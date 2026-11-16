"""Compare the tone of a render with the reference recordings, in detail.

The master of the work gets the long-term tone balance of the references.
That one curve does not show all problems of tone. This script looks at:

- The tone balance of each part of the work (between the rehearsal marks):
  a bright part and a dull part can give a correct mean.
- The spread of each band in time (the 10th, 50th and 90th percentile of
  the level in windows of three seconds).
- Narrow peaks: the level in bands of 1/12 octave against a smooth curve.
- The side signal (left minus right) against the mid signal, for each band.
- The stems (drums, bass, other) after the same separation as the
  references, if the stems of the render are in `.cache/analysis/stems`.

Usage:

    uv run python tools/tone.py build/audio/render.flac
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.audio import dsp, reference

RATE = dsp.RATE
SEGMENT = 8192
WINDOW_FRAMES = 32  # frames of the spectrum in one window: about three seconds
THIRDS = 1000.0 * 2.0 ** (np.arange(-17, 14) / 3.0)  # 20 Hz to 20 kHz
GROUPS = [
    ("sub 20-45", 20, 45), ("bass 45-90", 45, 90), ("90-180", 90, 180), ("180-355", 180, 355),
    ("355-710", 355, 710), ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800),
    ("2.8-5.6k", 2800, 5600), ("5.6-11k", 5600, 11200), ("air 11-20k", 11200, 20000),
]  # fmt: skip
REFERENCE_STEMS = Path(".cache/reference/stems/htdemucs")
RENDER_STEMS = Path(".cache/analysis/stems/htdemucs")


def spectrum_frames(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the frequencies, and the power of the mid and the side signal in each frame."""
    mid = 0.5 * (audio[:, 0] + audio[:, 1])
    side = 0.5 * (audio[:, 0] - audio[:, 1])
    frequencies, _times, mid_power = signal.spectrogram(
        mid, fs=RATE, nperseg=SEGMENT, noverlap=SEGMENT // 2, mode="psd"
    )
    _f, _t, side_power = signal.spectrogram(
        side, fs=RATE, nperseg=SEGMENT, noverlap=SEGMENT // 2, mode="psd"
    )
    return frequencies, mid_power, side_power


def band_matrix(frequencies: np.ndarray, edges: list[tuple[float, float]]) -> np.ndarray:
    """Return a matrix that sums the bins of the spectrum into bands."""
    matrix = np.zeros((len(edges), len(frequencies)))
    for index, (low, high) in enumerate(edges):
        matrix[index, (frequencies >= low) & (frequencies < high)] = 1.0
    return matrix


def third_edges() -> list[tuple[float, float]]:
    return [(centre / 2 ** (1 / 6), centre * 2 ** (1 / 6)) for centre in THIRDS]


def windows(power: np.ndarray) -> np.ndarray:
    """Return the mean power of each window of frames (bands x windows)."""
    count = power.shape[1] // WINDOW_FRAMES
    trimmed = power[:, : count * WINDOW_FRAMES]
    return trimmed.reshape(power.shape[0], count, WINDOW_FRAMES).mean(axis=2)


def loud(total: np.ndarray, below_db: float = 12.0) -> np.ndarray:
    """Return the windows that are not more than `below_db` under the loud windows."""
    level = 10.0 * np.log10(total + 1e-20)
    return level > np.percentile(level, 95) - below_db


class Track:
    """The band levels of one recording, in windows of three seconds."""

    def __init__(self, audio: np.ndarray) -> None:
        frequencies, mid, side = spectrum_frames(audio)
        self.frequencies = frequencies
        self.mid = mid
        thirds = band_matrix(frequencies, third_edges())
        self.band_power = windows(thirds @ mid)  # bands x windows
        self.side_power = windows(thirds @ side)
        self.total = self.band_power.sum(axis=0)
        self.keep = loud(self.total)
        self.seconds = WINDOW_FRAMES * SEGMENT / 2 / RATE

    def relative(self) -> np.ndarray:
        """Return the level of each band relative to the total of its window (dB), loud windows."""
        power = self.band_power[:, self.keep]
        return 10.0 * np.log10(power / power.sum(axis=0) + 1e-20)

    def long_term(self) -> np.ndarray:
        power = self.band_power[:, self.keep].sum(axis=1)
        return 10.0 * np.log10(power / power.sum() + 1e-20)

    def fine(self) -> tuple[np.ndarray, np.ndarray]:
        """Return centres of 1/12-octave bands and the level of each against a smooth curve."""
        # From 200 Hz: below it, a band is narrower than one line of the spectrum.
        centres = 200.0 * 2.0 ** (np.arange(0, 12 * 6 + 5) / 12.0)
        edges = [(centre / 2 ** (1 / 24), centre * 2 ** (1 / 24)) for centre in centres]
        frames = windows(self.mid)[:, self.keep] if self.mid.shape[1] else self.mid
        power = band_matrix(self.frequencies, edges) @ frames.sum(axis=1)
        level = 10.0 * np.log10(power + 1e-20)
        kernel = np.hanning(13)
        smooth = np.convolve(np.pad(level, 6, mode="edge"), kernel / kernel.sum(), mode="valid")
        return centres, level - smooth


def group_levels(centres: np.ndarray, levels: np.ndarray) -> np.ndarray:
    """Sum third-octave levels (dB, bands x n) into the wide groups (dB)."""
    power = 10.0 ** (levels / 10.0)
    rows = []
    for _name, low, high in GROUPS:
        inside = (centres >= low) & (centres < high)
        rows.append(10.0 * np.log10(power[inside].sum(axis=0) + 1e-20))
    return np.array(rows)


def marks() -> list[tuple[str, float, float]]:
    """Return the parts of the work: the label, the start and the end in seconds."""
    from gtypestar.work import build

    structure = build().structure
    numbers = sorted(structure.marks)
    starts = [(structure.marks[n], structure.seconds(structure.bar(n).start)) for n in numbers]
    starts.insert(0, ("start", 0.0))
    ends = [start for _label, start in starts[1:]] + [structure.duration_seconds]
    return [(label, start, end) for (label, start), end in zip(starts, ends, strict=True)]


def load(path: Path) -> np.ndarray:
    return reference.load_stereo(path)


def print_table(title: str, names: list[str], rows: dict[str, np.ndarray]) -> None:
    print(f"\n{title}")
    print(f"{'':22s}" + "".join(f"{name:>11s}" for name in names))
    for label, values in rows.items():
        print(f"{label:22s}" + "".join(f"{value:11.1f}" for value in values))


def stems_report(render_name: str) -> None:
    """Compare the separated stems of the render with those of the references."""
    render_dir = RENDER_STEMS / render_name
    if not render_dir.exists():
        print(f"\n(no stems of the render in {render_dir})")
        return
    names = [name for name, _low, _high in GROUPS]
    for stem in ("drums", "bass", "other"):
        rows: dict[str, np.ndarray] = {}
        shares = {}
        collected = []
        for directory in sorted(REFERENCE_STEMS.iterdir()):
            track = Track(load(directory / f"{stem}.flac"))
            level = group_levels(THIRDS, track.long_term()[:, None])[:, 0]
            collected.append(level)
            everything = sum(
                float(np.mean(soundfile.read(str(file), dtype="float32")[0] ** 2))
                for file in directory.glob("*.flac")
            )
            own = float(np.mean(soundfile.read(str(directory / f"{stem}.flac"))[0] ** 2))
            shares[directory.name] = 10.0 * np.log10(own / everything)
        collected = np.array(collected)
        rows["references lowest"] = collected.min(axis=0)
        rows["references mean"] = collected.mean(axis=0)
        rows["references highest"] = collected.max(axis=0)
        track = Track(load(render_dir / f"{stem}.flac"))
        mine = group_levels(THIRDS, track.long_term()[:, None])[:, 0]
        rows["render"] = mine
        rows["render - mean"] = mine - collected.mean(axis=0)
        everything = sum(
            float(np.mean(soundfile.read(str(file), dtype="float32")[0] ** 2))
            for file in render_dir.glob("*.flac")
        )
        own = float(np.mean(soundfile.read(str(render_dir / f"{stem}.flac"))[0] ** 2))
        share = 10.0 * np.log10(own / everything)
        spread = f"{min(shares.values()):.1f} to {max(shares.values()):.1f}"
        print_table(
            f"Stem '{stem}': level of each band group relative to the stem (dB). Power of the "
            f"stem relative to all stems: references {spread} dB, render {share:.1f} dB",
            names,
            rows,
        )


def main() -> int:
    path = Path(sys.argv[1])
    names = [name for name, _low, _high in GROUPS]
    references = [Track(load(reference.fetch(item))) for item in reference.REFERENCES]
    mine = Track(load(path))

    # 1. Long-term balance in the wide groups.
    ref_long = np.array([group_levels(THIRDS, t.long_term()[:, None])[:, 0] for t in references])
    own_long = group_levels(THIRDS, mine.long_term()[:, None])[:, 0]
    print_table(
        "Long-term balance of the loud windows (dB relative to the total)",
        names,
        {
            "references lowest": ref_long.min(axis=0),
            "references mean": ref_long.mean(axis=0),
            "references highest": ref_long.max(axis=0),
            "render": own_long,
            "render - mean": own_long - ref_long.mean(axis=0),
        },
    )

    # 2. The spread in time: percentiles of the windows.
    ref_windows = np.concatenate([group_levels(THIRDS, t.relative()) for t in references], axis=1)
    own_windows = group_levels(THIRDS, mine.relative())
    rows = {}
    for percent in (10, 50, 90):
        rows[f"references p{percent}"] = np.percentile(ref_windows, percent, axis=1)
        rows[f"render p{percent}"] = np.percentile(own_windows, percent, axis=1)
    low, high = np.percentile(ref_windows, 5, axis=1), np.percentile(ref_windows, 95, axis=1)
    rows["render % above p95"] = 100.0 * np.mean(own_windows > high[:, None], axis=1)
    rows["render % below p5"] = 100.0 * np.mean(own_windows < low[:, None], axis=1)
    print_table("Windows of three seconds (dB relative to the total of the window)", names, rows)

    # 3. Each part of the work against the median of the references.
    median = np.percentile(ref_windows, 50, axis=1)
    rows = {}
    relative = 10.0 * np.log10(mine.band_power / (mine.band_power.sum(axis=0) + 1e-30) + 1e-20)
    all_groups = group_levels(THIRDS, relative)
    level = 10.0 * np.log10(mine.total + 1e-20)
    top = np.percentile(level, 95)
    for label, start, end in marks():
        first, last = int(start / mine.seconds), max(int(end / mine.seconds), 1)
        part = all_groups[:, first:last]
        if part.shape[1] == 0:
            continue
        loudness = float(np.mean(level[first:last]) - top)
        rows[f"{label} {start / 60:4.1f} min {loudness:+5.1f}dB"] = part.mean(axis=1) - median
    print_table(
        "Each part: band groups relative to the median of the references (dB); the label "
        "has the start and the level relative to the loud parts",
        names,
        rows,
    )

    # 4. The side signal.
    def side_groups(track: Track) -> np.ndarray:
        result = []
        for _name, low_edge, high_edge in GROUPS:
            inside = (low_edge <= THIRDS) & (high_edge > THIRDS)
            side = track.side_power[inside][:, track.keep].sum()
            mid = track.band_power[inside][:, track.keep].sum()
            result.append(10.0 * np.log10((side + 1e-20) / (mid + 1e-20)))
        return np.array(result)

    ref_side = np.array([side_groups(t) for t in references])
    print_table(
        "Side signal relative to the mid signal (dB)",
        names,
        {
            "references lowest": ref_side.min(axis=0),
            "references mean": ref_side.mean(axis=0),
            "references highest": ref_side.max(axis=0),
            "render": side_groups(mine),
        },
    )

    # 5. Narrow peaks.
    centres, own_fine = mine.fine()
    ref_fine = np.array([t.fine()[1] for t in references])
    limit = np.abs(ref_fine).max(axis=0)
    print("\nNarrow bands (1/12 octave) against a smooth curve: the largest values of the render")
    order = np.argsort(-np.abs(own_fine))[:14]
    for index in sorted(order):
        print(
            f"  {centres[index]:8.0f} Hz  render {own_fine[index]:+5.1f} dB   "
            f"references at most {limit[index]:4.1f} dB"
        )
    print(
        f"  mean size: render {np.abs(own_fine).mean():.2f} dB, references "
        f"{np.abs(ref_fine).mean():.2f} dB"
    )

    stems_report(path.stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
