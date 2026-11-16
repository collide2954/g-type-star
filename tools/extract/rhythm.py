"""Find the pulse grid and the drum strokes of each reference recording.

For each recording the script writes into `.cache/reference/derived/<name>`:

- `grid.json`: the period of the fastest regular pulse (the tatum), and the
  time of each pulse.
- `strokes.csv`: one row for each drum stroke: time, drum (kick, snare, hat),
  strength, the number of the nearest pulse, and the distance from it.
- `fold.png`: the strokes folded at different cycle lengths, to find the bar.
- `check-<second>.png`: a spectrogram of the drum stem with the strokes, to
  make sure that the detection is correct.

The script needs the drum stem (`separate.py`).

Usage:

    .cache/analysis-venv/bin/python tools/extract/rhythm.py [names] [--check 60,120]
"""

from __future__ import annotations

import argparse
import csv

import common
import librosa
import matplotlib
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks
from sklearn.cluster import KMeans

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FINE_HOP = 64  # 1.45 ms: the frame of the stroke detection
# Edges of the frequency bands of a stroke (Hz).
EDGES = [35, 70, 110, 180, 300, 600, 1200, 2500, 5000, 8000, 12000, 16000]
SUB = slice(0, 2)  # 35 to 110 Hz: the kick drum
BODY = slice(2, 4)  # 110 to 300 Hz: the shell of the snare drum and of the tom-toms
MID = slice(5, 8)  # 600 to 5000 Hz: the wires of the snare drum
AIR = slice(9, 11)  # 8 to 16 kHz: hi-hat and cymbals
SHORTEST_GAP = 0.028  # two sudden changes are not nearer than this (seconds)
SAME_DRUM_GAP = 0.045  # two strokes of one drum are not nearer than this
CLUSTERS = 14
PERIOD_HINTS: dict[str, float] = {}  # name of a recording -> tatum period, if the search fails


def _frames(seconds: float) -> int:
    return int(round(seconds * common.RATE / FINE_HOP))


def band_levels(audio: np.ndarray) -> np.ndarray:
    """Return the level of each band (amplitude) at the fine frame: bands x frames."""
    spectrum = np.abs(librosa.stft(audio, n_fft=2048, hop_length=FINE_HOP, window="hann"))
    frequencies = librosa.fft_frequencies(sr=common.RATE, n_fft=2048)
    rows = []
    for low, high in zip(EDGES[:-1], EDGES[1:], strict=True):
        selected = (frequencies >= low) & (frequencies < high)
        rows.append(np.sqrt((spectrum[selected] ** 2).sum(axis=0)) + 1e-7)
    return np.stack(rows)


def onsets(audio: np.ndarray, share: float = 0.08) -> np.ndarray:
    """Return the frames where the sound of the drum stem changes suddenly."""
    short = np.abs(librosa.stft(audio, n_fft=256, hop_length=FINE_HOP, window="hann"))
    flux = np.maximum(0.0, np.diff(np.log1p(100.0 * short), axis=1)).sum(axis=0)
    flux = np.concatenate([[0.0], flux])
    base = median_filter(flux, size=_frames(0.25))
    peaks, _ = find_peaks(
        flux - base, height=share * np.percentile(flux, 99.9), distance=_frames(SHORTEST_GAP)
    )
    return peaks


def shapes(levels: np.ndarray, frames: np.ndarray) -> tuple[np.ndarray, ...]:
    """Describe each sudden change: how each band comes up, and how it stays.

    Return four tables (changes x bands), in dB:

    - rise: the peak in the first 45 ms, relative to the level before.
    - tail: the mean from 45 to 100 ms, relative to the level before.
    - late: the mean from 200 to 300 ms, relative to the level before.
    - peak: the peak level.
    """
    length = levels.shape[1]

    def window(frame: int, first: float, last: float, how) -> np.ndarray:
        begin = min(max(0, frame + _frames(first)), length - 1)
        stop = min(max(begin + 1, frame + _frames(last)), length)
        return how(levels[:, begin:stop], axis=1)

    rise, tail, late, peak = [], [], [], []
    for frame in frames:
        before = window(frame, -0.060, -0.028, np.mean)
        top = window(frame, -0.005, 0.045, np.max)
        rise.append(20.0 * np.log10(top / before))
        tail.append(20.0 * np.log10(window(frame, 0.045, 0.100, np.mean) / before))
        late.append(20.0 * np.log10(window(frame, 0.200, 0.300, np.mean) / before))
        peak.append(20.0 * np.log10(top))
    return tuple(np.array(table) for table in (rise, tail, late, peak))


def cluster_labels(centre_rise: np.ndarray, centre_tail: np.ndarray, centre_late: np.ndarray):
    """Give each cluster of strokes its drums, from the shape of its centre.

    The centre of a cluster is the mean of many strokes: thus it is clear,
    also if a single stroke is not. The rules:

    - kick: the band below 110 Hz comes up.
    - snare: the band of the shell comes up, and the band from 600 to 5000 Hz
      stays loud for 50 to 100 ms.
    - cymbal: the bands above 2.5 kHz stay loud for 250 ms.
    - hat: the band above 8 kHz comes up, and the stroke is not a snare or a ringing cymbal.
    - tom: the band of the shell comes up, and the stroke is not a snare or a kick.
    """
    sub = centre_rise[:, SUB].mean(axis=1)
    body = centre_rise[:, BODY].max(axis=1)
    mid_tail = centre_tail[:, MID].mean(axis=1)
    air = centre_rise[:, AIR].mean(axis=1)
    high_late = centre_late[:, 7:11].mean(axis=1)
    kick_limit = max(8.0, 0.3 * sub.max())
    tail_limit = max(6.0, 0.45 * mid_tail.max())
    labels = []
    for index in range(len(sub)):
        found = []
        if sub[index] >= kick_limit:
            found.append("kick")
        ringing = high_late[index] >= 9.0
        # A cymbal alone has almost no sound in the band of the shell.
        if body[index] >= 15.0 and mid_tail[index] >= tail_limit:
            found.append("snare")
        if ringing:
            found.append("cymbal")
        if air[index] >= 6.0 and "snare" not in found and not ringing:
            found.append("hat")
        if not found and body[index] >= 8.0:
            found.append("tom")
        labels.append(found)
    return labels


def detect(audio: np.ndarray, report: list[str] | None = None) -> list[tuple[float, str, float]]:
    """Return the drum strokes as (time, drum, level in dB relative to the loud strokes).

    One sudden change of the sound can be more than one drum (for example
    kick and hi-hat together). The function puts all sudden changes into
    clusters of the same shape, and gives each cluster its drums.
    """
    levels = band_levels(audio)
    frames = onsets(audio)
    rise, tail, late, peak = shapes(levels, frames)
    features = np.clip(np.concatenate([rise, tail, 0.5 * late], axis=1), 0.0, 40.0) / 40.0
    model = KMeans(n_clusters=CLUSTERS, n_init=4, random_state=0).fit(features)
    centre = lambda table: np.stack(  # noqa: E731
        [table[model.labels_ == number].mean(axis=0) for number in range(CLUSTERS)]
    )
    labels = cluster_labels(centre(rise), centre(tail), centre(late))
    if report is not None:
        centre_rise, centre_tail = centre(rise), centre(tail)
        for number in np.argsort(-np.bincount(model.labels_, minlength=CLUSTERS)):
            count = int((model.labels_ == number).sum())
            report.append(
                f"  cluster {number:2d} n={count:4d}"
                f" sub {centre_rise[number, SUB].mean():5.1f}"
                f" body {centre_rise[number, BODY].max():5.1f}"
                f" midtail {centre_tail[number, MID].mean():5.1f}"
                f" air {centre_rise[number, AIR].mean():5.1f}"
                f" -> {'+'.join(labels[number]) or '-'}"
            )

    measure = {
        "kick": peak[:, SUB].max(axis=1),
        "snare": 0.5 * (peak[:, BODY].max(axis=1) + peak[:, MID].max(axis=1)),
        "cymbal": peak[:, AIR].max(axis=1),
        "hat": peak[:, AIR].max(axis=1),
        "tom": peak[:, BODY].max(axis=1),
    }
    strokes: list[tuple[float, str, float]] = []
    for index, frame in enumerate(frames):
        for drum in labels[model.labels_[index]]:
            strokes.append((frame * FINE_HOP / common.RATE, drum, float(measure[drum][index])))

    # Soft hi-hat strokes are not sudden changes of the full sound: find them in their band.
    air = 20.0 * np.log10(np.sqrt((levels[AIR] ** 2).sum(axis=0)))
    ahead = np.concatenate([air[_frames(0.012) :], np.full(_frames(0.012), air[-1])])
    behind = np.concatenate([np.full(_frames(0.012), air[0]), air[: -_frames(0.012)]])
    lift = np.maximum(0.0, ahead - np.minimum(air, behind))
    ticks, _ = find_peaks(lift, height=6.0, distance=_frames(SHORTEST_GAP))
    ticks = ticks[air[ticks] > np.percentile(air, 99.5) - 40.0]
    known = np.array(sorted(frames))
    for tick in ticks:
        place = np.searchsorted(known, tick)
        gaps = [abs(known[i] - tick) for i in (place - 1, place) if 0 <= i < len(known)]
        if not gaps or min(gaps) > _frames(0.025):
            top = float(air[tick : tick + _frames(0.03)].max())
            strokes.append(((tick + _frames(0.006)) * FINE_HOP / common.RATE, "hat", top))

    # One drum does not sound two times in a very short time: keep the first stroke.
    strokes.sort()
    kept: list[tuple[float, str, float]] = []
    last: dict[str, float] = {}
    for time, drum, level in strokes:
        if time - last.get(drum, -1.0) >= SAME_DRUM_GAP:
            kept.append((time, drum, level))
            last[drum] = time
    # Give the level of each stroke relative to the loud strokes of its drum.
    result = []
    for drum in ("kick", "snare", "hat", "tom", "cymbal"):
        values = np.array([level for _time, name, level in kept if name == drum])
        if len(values) == 0:
            continue
        top = float(np.percentile(values, 90))
        result.extend((time, name, level - top) for time, name, level in kept if name == drum)
    result.sort()
    return result


def nearest_pulse(grid: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Return the number of the pulse nearest to each time."""
    after = np.clip(np.searchsorted(grid, times), 1, len(grid) - 1)
    return np.where(times - grid[after - 1] < grid[after] - times, after - 1, after)


def fold_plot(name: str, strokes: list, grid: np.ndarray, lengths: list[int], path) -> None:
    """Draw the strokes folded at some cycle lengths: one row for each cycle."""
    figure, axes = plt.subplots(1, len(lengths), figsize=(4.2 * len(lengths), 9), squeeze=False)
    colours = {"kick": "tab:red", "snare": "tab:blue", "hat": "tab:green", "tom": "tab:orange",
               "cymbal": "tab:purple"}  # fmt: skip
    times = np.array([stroke[0] for stroke in strokes])
    pulses = np.searchsorted(grid, times) - 1
    pulses = np.clip(pulses, 0, len(grid) - 2)
    span = grid[pulses + 1] - grid[pulses]
    position = pulses + (times - grid[pulses]) / np.maximum(span, 1e-6)
    for axis, length in zip(axes[0], lengths, strict=True):
        for drum, colour in colours.items():
            rows = np.array([stroke[1] == drum for stroke in strokes])
            axis.scatter(
                np.mod(position[rows], length),
                position[rows] // length,
                s=3, c=colour, marker="s", linewidths=0,
            )  # fmt: skip
        axis.set_title(f"{name}: cycle of {length} pulses", fontsize=9)
        axis.invert_yaxis()
        axis.set_xlim(-0.5, length - 0.5)
        axis.set_xticks(range(0, length, 1 if length <= 20 else 2))
        axis.tick_params(labelsize=6)
        axis.grid(alpha=0.25, axis="x")
    figure.tight_layout()
    figure.savefig(path, dpi=80)
    plt.close(figure)


def check_plot(name: str, audio: np.ndarray, strokes: list, grid: np.ndarray, start: float) -> None:
    """Draw 8 seconds of the drum stem with the strokes and the pulse grid."""
    length = 8.0
    first, last = int(start * common.RATE), int((start + length) * common.RATE)
    spectrum = np.abs(librosa.stft(audio[first:last], n_fft=1024, hop_length=128))
    figure, axis = plt.subplots(figsize=(18, 6))
    librosa.display.specshow(
        librosa.amplitude_to_db(spectrum, ref=np.max, top_db=70), sr=common.RATE, hop_length=128,
        x_axis="time", y_axis="log", ax=axis, cmap="magma",
    )  # fmt: skip
    heights = {"kick": 45, "snare": 900, "hat": 12000, "tom": 300, "cymbal": 6000}
    colours = {"kick": "cyan", "snare": "lime", "hat": "white", "tom": "orange", "cymbal": "yellow"}
    for time, drum, strength in strokes:
        if start <= time < start + length:
            axis.plot(time - start, heights[drum], "v", color=colours[drum], markersize=7)
            axis.text(time - start, heights[drum] * 1.25, f"{strength:.0f}", color=colours[drum],
                      fontsize=6, ha="center")  # fmt: skip
    for number, pulse in enumerate(grid):
        if start <= pulse < start + length:
            axis.axvline(pulse - start, color="white", alpha=0.25, linewidth=0.6)
            axis.text(pulse - start, 20500, str(number), color="white", fontsize=5, ha="center")
    axis.set_ylim(25, 21000)
    axis.set_title(f"{name}: drum stem from {start:.0f} s (kick cyan, snare green, hat white)")
    figure.tight_layout()
    figure.savefig(common.derived(name, f"check-{int(start):03d}.png"), dpi=80)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*")
    parser.add_argument("--check", default="", help="start times of check pictures, in seconds")
    parser.add_argument("--fold", default="", help="cycle lengths for the fold picture")
    parser.add_argument("--verbose", action="store_true", help="show the clusters of strokes")
    args = parser.parse_args()
    for name in common.names(args.names):
        if not (common.STEMS_DIR / name / "drums.flac").exists():
            print(f"{name}: no drum stem", flush=True)
            continue
        drums = common.load(name, "drums")
        curve = common.onset_curve(drums)
        candidates = common.comb_period(curve)
        period = PERIOD_HINTS.get(name, candidates[0][0])
        tracked = common.track_pulse(curve, period)
        grid = common.smooth_grid(tracked)
        report: list[str] = []
        strokes = detect(drums, report)

        times = np.array([stroke[0] for stroke in strokes])
        nearest = nearest_pulse(grid, times)
        # The pulse tracker is late by a constant time (the window of its onset curve).
        # Move the grid to the centre of the strokes that are on a pulse.
        distance = times - grid[nearest]
        near = np.abs(distance) < 0.25 * period
        grid = grid + float(np.median(distance[near]))
        nearest = nearest_pulse(grid, times)
        with common.derived(name, "strokes.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time", "drum", "level_db", "pulse", "offset_ms"])
            for (time, drum, strength), pulse in zip(strokes, nearest, strict=True):
                offset = 1000.0 * (time - grid[pulse])
                writer.writerow(
                    [f"{time:.4f}", drum, f"{strength:.1f}", int(pulse), f"{offset:.1f}"]
                )
        common.write_json(
            name,
            "grid.json",
            {
                "period": float(np.median(np.diff(grid))),
                "candidates": candidates,
                "pulses": [round(float(time), 4) for time in grid],
            },
        )
        counts = {drum: sum(1 for stroke in strokes if stroke[1] == drum) for drum in
                  ("kick", "snare", "hat", "tom", "cymbal")}  # fmt: skip
        print(
            f"{name}: pulse {1000 * np.median(np.diff(grid)):.2f} ms, {len(grid)} pulses, "
            f"strokes {counts}",
            flush=True,
        )
        if args.verbose:
            print("\n".join(report), flush=True)
        lengths = [int(value) for value in args.fold.split(",") if value] or [12, 14, 15, 16, 20]
        fold_plot(name, strokes, grid, lengths, common.derived(name, "fold.png"))
        for value in args.check.split(","):
            if value:
                check_plot(name, drums, strokes, grid, float(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
