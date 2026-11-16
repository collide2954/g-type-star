"""Measure the reference recordings and write the measured tables as CSV files.

The data come from the extraction scripts (`tools/extract`): the pulse grid,
the drum strokes, the bass notes, the other notes, and the stems of each
recording. These data are in the cache of the owner of the project. The
tables that this module writes have only numbers that describe the style:
they are in the repository (`research/measured`).

The command `uv run gtypestar-study measure` runs this module. It needs the
cache. A computer that does not have the cache uses the tables as they are.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import soundfile
import soxr

from ..audio import dsp, loudness
from ..audio.reference import REFERENCES

OUTPUT_DIR = Path("research/measured")
DERIVED_DIR = Path(".cache/reference/derived")
STEMS_DIR = Path(".cache/reference/stems/htdemucs")
AUDIO_DIR = Path(".cache/reference/audio")
WINDOW = 192  # pulses in one window of the cycle search
DRUMS = ("kick", "snare", "hat", "cymbal", "tom")


def write_csv(name: str, header: Sequence[str], rows: Iterable[Sequence[object]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([_format(value) for value in row])
    return path


def _format(value: object) -> object:
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".") if abs(value) < 1000 else f"{value:.0f}"
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load(name: str) -> dict:
    """Read the extracted data of one recording."""
    folder = DERIVED_DIR / name
    grid = json.loads((folder / "grid.json").read_text())
    pulses = np.array(grid["pulses"])
    strokes = [
        (float(row["time"]), row["drum"], float(row["level_db"]), int(row["pulse"]),
         float(row["offset_ms"]))
        for row in _rows(folder / "strokes.csv")
    ]  # fmt: skip
    bass = [
        (float(r["start"]), float(r["end"]), float(r["midi"])) for r in _rows(folder / "bass.csv")
    ]
    other = [
        (float(r["start"]), float(r["end"]), int(r["midi"]), float(r["amplitude"]))
        for r in _rows(folder / "other.csv")
    ]
    return {"pulses": pulses, "period": float(np.median(np.diff(pulses))), "strokes": strokes,
            "bass": bass, "other": other}  # fmt: skip


def sequences(data: dict) -> dict[str, np.ndarray]:
    """Return, for each drum, a list with 1 for each pulse that has a stroke on it."""
    count = len(data["pulses"])
    result = {drum: np.zeros(count) for drum in DRUMS}
    limit = 0.3 * 1000.0 * data["period"]
    for _time, drum, _level, pulse, offset in data["strokes"]:
        if abs(offset) < limit and drum in result:
            result[drum][pulse] = 1.0
    return result


def cycle(sequence: np.ndarray, longest: int = 40) -> int:
    """Return the length of the cycle of a stroke sequence, in pulses (0 = no cycle)."""
    if sequence.sum() < 6:
        return 0
    centred = sequence - sequence.mean()
    energy = float(np.dot(centred, centred)) + 1e-9
    size = len(centred)
    values = np.array(
        [np.dot(centred[:-lag], centred[lag:]) / energy * size / (size - lag)
         for lag in range(1, longest + 1)]
    )  # fmt: skip
    best = float(values[3:].max())
    if best < 0.25:
        return 0
    # The shortest lag that is almost as good as the best lag: a longer lag is a multiple.
    for lag in range(4, longest + 1):
        if values[lag - 1] >= 0.9 * best:
            return lag
    return 0


def cycles(data: dict) -> Counter[int]:
    """Return how many windows of the recording have each cycle length of the snare drum."""
    found: Counter[int] = Counter()
    rows = sequences(data)
    for start in range(0, len(data["pulses"]) - WINDOW, WINDOW // 2):
        length = cycle(rows["snare"][start : start + WINDOW])
        if not length:
            length = cycle(rows["kick"][start : start + WINDOW])
        found[length] += 1
    return found


def repetition(data: dict, length: int) -> tuple[float, float, int]:
    """Return how frequently a bar of kick and snare comes again with no change.

    The bars have `length` pulses. The result has: the share of the bars
    that are the same as the bar before, the share that are the same as one
    of the 8 bars before, and the number of bars with strokes.
    """
    rows = sequences(data)
    count = len(data["pulses"]) // length
    bars = []
    for number in range(count):
        part = slice(number * length, (number + 1) * length)
        bars.append((tuple(rows["kick"][part]), tuple(rows["snare"][part])))
    same, near, total = 0, 0, 0
    for number, bar in enumerate(bars):
        if sum(bar[0]) + sum(bar[1]) < 2:
            continue
        total += 1
        same += number > 0 and bars[number - 1] == bar
        near += bar in bars[max(0, number - 8) : number]
    return same / max(total, 1), near / max(total, 1), total


def spread(data: dict, drum: str) -> tuple[float, float, int]:
    """Return the timing spread of one drum: robust standard deviation and median, in ms."""
    limit = 0.25 * 1000.0 * data["period"]
    offsets = np.array([o for _t, d, _l, _p, o in data["strokes"] if d == drum and abs(o) < limit])
    if len(offsets) < 20:
        return float("nan"), float("nan"), len(offsets)
    centre = float(np.median(offsets))
    return 1.4826 * float(np.median(np.abs(offsets - centre))), centre, len(offsets)


def rhythm_rows() -> tuple[list[list[object]], list[list[object]]]:
    """Measure the pulse, the cycles, the strokes, and the repetition of each recording."""
    rhythm, timing = [], []
    for reference in REFERENCES:
        if not (DERIVED_DIR / reference.name / "strokes.csv").exists():
            continue
        data = load(reference.name)
        seconds = float(data["pulses"][-1] - data["pulses"][0])
        found = cycles(data)
        windows = sum(found.values())
        common = [(length, share) for length, share in found.most_common(3) if length]
        main = common[0][0] if common else 0
        same, near, bars = repetition(data, main) if main else (float("nan"), float("nan"), 0)
        rate = {
            drum: sum(1 for stroke in data["strokes"] if stroke[1] == drum) / seconds
            for drum in DRUMS
        }
        kicks = np.array(sorted(t for t, d, *_ in data["strokes"] if d == "kick"))
        gaps = np.diff(kicks) / data["period"]
        double = float(np.mean((gaps > 0.35) & (gaps < 0.75))) if len(gaps) else 0.0
        rhythm.append(
            [
                reference.work,
                1000.0 * data["period"],
                1.0 / data["period"],
                "; ".join(f"{length} ({share / windows:.0%})" for length, share in common),
                main,
                main * data["period"],
                rate["kick"],
                rate["snare"],
                rate["hat"] + rate["cymbal"],
                double,
                same,
                near,
                bars,
            ]
        )
        for drum in ("kick", "snare", "hat", "cymbal"):
            deviation, centre, count = spread(data, drum)
            levels = np.array([level for _t, d, level, *_ in data["strokes"] if d == drum])
            if count < 20:
                continue
            timing.append(
                [
                    reference.work,
                    drum,
                    count,
                    deviation,
                    centre,
                    float(np.percentile(levels, 10)),
                    float(np.percentile(levels, 50)),
                    float(np.mean(levels < -9.0)),
                ]
            )
    return rhythm, timing


def interval_shares(pitches: Sequence[float]) -> dict[str, float]:
    """Return the share of each interval class in a line of pitches."""
    moves = [abs(round(b - a)) for a, b in zip(pitches, pitches[1:], strict=False)]
    total = max(len(moves), 1)
    bins = {
        "repeat": (0, 0),
        "semitone": (1, 1),
        "tone": (2, 2),
        "third": (3, 4),
        "fourth or fifth": (5, 7),
        "sixth or seventh": (8, 11),
        "octave or more": (12, 99),
    }
    return {
        name: sum(low <= move <= high for move in moves) / total
        for name, (low, high) in bins.items()
    }


def line_rows() -> tuple[list[list[object]], list[list[object]]]:
    """Measure the bass line and the fast lines of each recording."""
    bass_rows, line_rows_ = [], []
    for reference in REFERENCES:
        if not (DERIVED_DIR / reference.name / "bass.csv").exists():
            continue
        data = load(reference.name)
        seconds = float(data["pulses"][-1] - data["pulses"][0])
        notes = [n for n in data["bass"] if n[1] - n[0] >= 0.05]
        pitches = [n[2] for n in notes]
        shares = interval_shares(pitches)
        lengths = np.array([n[1] - n[0] for n in notes])
        bass_rows.append(
            [
                reference.work, len(notes) / seconds, float(np.percentile(pitches, 2)),
                float(np.median(pitches)), float(np.percentile(pitches, 98)),
                float(np.mean(np.array(pitches) < 33.5)), float(np.median(lengths)),
                *[shares[name] for name in shares],
            ]
        )  # fmt: skip
        # The fast lines: the number of note starts of the stem "other" in windows of 1 s.
        starts = np.array(sorted(n[0] for n in data["other"] if n[3] > 0.35))
        edges = np.arange(0.0, seconds, 0.5)
        rates = np.array([np.sum((starts >= e) & (starts < e + 1.0)) for e in edges], dtype=float)
        pitches = np.array([n[2] for n in data["other"]])
        line_rows_.append(
            [
                reference.work, float(np.median(rates)), float(np.percentile(rates, 90)),
                float(np.percentile(rates, 99)), float(np.mean(rates >= 8.0)),
                float(np.mean(rates >= 11.0)), float(np.percentile(pitches, 5)),
                float(np.percentile(pitches, 95)),
            ]
        )  # fmt: skip
    return bass_rows, line_rows_


def _lufs(path: Path) -> float:
    audio, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
    if rate != dsp.RATE:
        audio = soxr.resample(audio, rate, dsp.RATE, quality="MQ")
    return loudness.integrated(loudness.block_power(audio.astype(np.float32)))


def stem_rows() -> list[list[object]]:
    """Measure the loudness of each stem relative to the full recording."""
    rows = []
    for reference in REFERENCES:
        folder = STEMS_DIR / reference.name
        if not (folder / "other.flac").exists():
            continue
        full = _lufs(AUDIO_DIR / f"{reference.name}.wav")
        rows.append(
            [reference.work, *[_lufs(folder / f"{stem}.flac") - full for stem in
                               ("drums", "bass", "other", "vocals")]]
        )  # fmt: skip
    if rows:
        rows.append(["Mean", *[float(np.mean([row[i] for row in rows])) for i in range(1, 5)]])
    return rows


def section_rows() -> list[list[object]]:
    """Measure the shape of each recording from its loudness: full parts, quiet parts, stops."""
    rows = []
    for reference in REFERENCES:
        path = AUDIO_DIR / f"{reference.name}.wav"
        if not path.exists():
            continue
        audio, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
        if rate != dsp.RATE:
            audio = soxr.resample(audio, rate, dsp.RATE, quality="MQ")
        power = loudness.block_power(audio.astype(np.float32))
        momentary = 10.0 * np.log10(np.convolve(power, np.ones(4) / 4.0, mode="same") + 1e-12)
        slow = 10.0 * np.log10(np.convolve(power, np.ones(30) / 30.0, mode="same") + 1e-12)
        top = float(np.percentile(slow, 90))
        seconds = len(power) * 0.1
        full = slow > top - 3.0
        quiet = slow < top - 8.0
        # The first and the last time at the full level.
        places = np.flatnonzero(full)
        intro, outro = places[0] * 0.1, seconds - places[-1] * 0.1
        inner = np.arange(len(slow))
        inner_quiet = quiet & (inner > places[0]) & (inner < places[-1])
        # The longest quiet part between the first and the last full part.
        longest, start, run, best_start = 0, 0, 0, 0
        for index, value in enumerate(inner_quiet):
            if value:
                if run == 0:
                    start = index
                run += 1
                if run > longest:
                    longest, best_start = run, start
            else:
                run = 0
        # Stops: the sound goes down by 10 dB or more for less than 1.5 s, in a full part.
        dips = (momentary < top - 10.0) & (inner > places[0]) & (inner < places[-1])
        stops, run = 0, 0
        for value in list(dips) + [False]:
            if value:
                run += 1
            else:
                stops += 0 < run <= 15
                run = 0
        rows.append(
            [
                reference.work, seconds / 60.0, float(np.mean(full)), float(np.mean(quiet)),
                intro, outro, longest * 0.1, best_start * 0.1 / seconds if longest else "",
                stops, stops / (seconds / 60.0),
            ]
        )  # fmt: skip
    return rows


def measure_all() -> list[Path]:
    """Write all measured tables of the reference recordings. Return the paths."""
    from ..audio import reference

    paths = []
    if all((AUDIO_DIR / f"{item.name}.wav").exists() for item in REFERENCES):
        reference.measure_references()
        paths += [reference.SUMMARY_FILE, reference.TARGET_FILE]
    rhythm, timing = rhythm_rows()
    paths.append(
        write_csv(
            "reference_rhythm.csv",
            ["recording", "pulse_ms", "pulses_per_second", "cycle_lengths_in_pulses",
             "main_cycle_pulses", "main_cycle_seconds", "kick_strokes_per_second",
             "snare_strokes_per_second", "cymbal_strokes_per_second",
             "kick_share_at_half_a_pulse", "bars_same_as_the_bar_before",
             "bars_same_as_one_of_8_bars_before", "bars"],
            rhythm,
        )
    )  # fmt: skip
    paths.append(
        write_csv(
            "reference_timing.csv",
            ["recording", "drum", "strokes", "spread_ms", "centre_ms", "level_10th_percentile_db",
             "level_median_db", "share_of_soft_strokes"],
            timing,
        )
    )  # fmt: skip
    bass, lines = line_rows()
    paths.append(
        write_csv(
            "reference_bass.csv",
            ["recording", "notes_per_second", "lowest_midi", "median_midi", "highest_midi",
             "share_below_a1", "median_note_seconds", "repeat", "semitone", "tone", "third",
             "fourth_or_fifth", "sixth_or_seventh", "octave_or_more"],
            bass,
        )
    )  # fmt: skip
    paths.append(
        write_csv(
            "reference_lines.csv",
            ["recording", "note_starts_per_second_median", "note_starts_90th_percentile",
             "note_starts_99th_percentile", "share_of_time_8_or_more", "share_of_time_11_or_more",
             "pitch_5th_percentile_midi", "pitch_95th_percentile_midi"],
            lines,
        )
    )  # fmt: skip
    stems = stem_rows()
    if stems:
        paths.append(
            write_csv(
                "reference_stems.csv",
                ["recording", "drums_lu", "bass_lu", "other_lu", "vocals_lu"],
                stems,
            )
        )
    sections = section_rows()
    if sections:
        paths.append(
            write_csv(
                "reference_form.csv",
                ["recording", "minutes", "share_at_full_level", "share_8_db_below_full",
                 "seconds_before_first_full_level", "seconds_after_last_full_level",
                 "longest_quiet_part_seconds", "longest_quiet_part_position", "short_stops",
                 "short_stops_per_minute"],
                sections,
            )
        )  # fmt: skip
    return paths
