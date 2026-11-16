"""Find the notes of each reference recording: bass line, other notes, and chroma.

For each recording the script writes into `.cache/reference/derived/<name>`:

- `bass.csv`: the notes of the bass stem (one voice): start, end, MIDI pitch, level.
- `other.csv`: the notes of the stem "other" (guitar, keyboards, synthesizers, saxophone,
  strings), from the transcription model Basic Pitch (Spotify, 2022).
- `chroma.npz`: the strength of each of the 12 pitch classes at each pulse, for the
  stems "bass" and "other".

The results are approximations. The measurement code uses them for statistics
(ranges, intervals, note rates, pitch-class sets), not as a score.

The script needs the stems (`separate.py`) and the pulse grid (`rhythm.py`).

Usage:

    .cache/analysis-venv/bin/python tools/extract/notes.py [names]
"""

from __future__ import annotations

import csv
import sys

import common
import librosa
import numpy as np
from scipy.ndimage import median_filter

BASS_RATE = 5512
BASS_FRAME = 768  # 139 ms: four periods of the lowest note
BASS_HOP = 64  # 11.6 ms
BASS_LOW, BASS_HIGH = 29.0, 400.0  # hertz
SHORTEST_NOTE = 0.045  # seconds


def bass_notes(name: str) -> list[tuple[float, float, float, float]]:
    """Return the notes of the bass stem as (start, end, MIDI pitch, level in dB)."""
    audio = common.load(name, "bass")
    audio = librosa.resample(audio, orig_sr=common.RATE, target_sr=BASS_RATE)
    # The method YIN with no model of the note sequence: it is fast. A median filter
    # removes the single frames with an error of one octave.
    pitch = librosa.yin(
        audio, fmin=BASS_LOW, fmax=BASS_HIGH, sr=BASS_RATE, frame_length=BASS_FRAME,
        hop_length=BASS_HOP, trough_threshold=0.15,
    )  # fmt: skip
    pitch = median_filter(pitch, size=5)
    voiced = np.ones(len(pitch), dtype=bool)
    level = librosa.feature.rms(y=audio, frame_length=BASS_FRAME, hop_length=BASS_HOP)[0]
    level_db = 20.0 * np.log10(level + 1e-7)
    loud = np.percentile(level_db, 95)
    midi = librosa.hz_to_midi(np.where(voiced, pitch, np.nan))
    frame = BASS_HOP / BASS_RATE
    notes: list[tuple[float, float, float, float]] = []
    start = None
    for index in range(len(midi) + 1):
        value = midi[index] if index < len(midi) else np.nan
        active = not np.isnan(value) and level_db[min(index, len(level_db) - 1)] > loud - 30.0
        if start is not None:
            centre = float(np.median(midi[start:index]))
            if not active or abs(value - centre) > 0.7:
                if (index - start) * frame >= SHORTEST_NOTE:
                    notes.append(
                        (start * frame, index * frame, centre, float(level_db[start:index].max()))
                    )
                start = None
        if start is None and active:
            start = index
    return notes


def other_notes(name: str) -> list[tuple[float, float, int, float]]:
    """Return the notes of the stem "other" as (start, end, MIDI pitch, amplitude)."""
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict

    path = common.STEMS_DIR / name / "other.flac"
    _output, _midi, events = predict(
        str(path), ICASSP_2022_MODEL_PATH, onset_threshold=0.5, frame_threshold=0.3,
        minimum_note_length=58.0, minimum_frequency=60.0, maximum_frequency=4200.0,
    )  # fmt: skip
    return sorted(
        (float(a), float(b), int(pitch), float(level)) for a, b, pitch, level, _ in events
    )


def pulse_chroma(name: str, stem: str, pulses: np.ndarray) -> np.ndarray:
    """Return the strength of the 12 pitch classes in each pulse (pulses x 12)."""
    audio = common.load(name, stem)
    audio = librosa.effects.harmonic(audio, margin=3.0)
    chroma = librosa.feature.chroma_cqt(
        y=audio, sr=common.RATE, hop_length=512, fmin=librosa.note_to_hz("C1"), n_octaves=6,
        bins_per_octave=36,
    )  # fmt: skip
    frames = librosa.time_to_frames(pulses, sr=common.RATE, hop_length=512)
    frames = np.clip(frames, 0, chroma.shape[1] - 1)
    rows = []
    for first, last in zip(frames[:-1], frames[1:], strict=True):
        rows.append(np.median(chroma[:, first : max(last, first + 1)], axis=1))
    rows.append(chroma[:, frames[-1]])
    return np.array(rows)


def write_rows(name: str, file: str, header: list[str], rows: list[tuple]) -> None:
    with common.derived(name, file).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(
                [f"{value:.4f}" if isinstance(value, float) else value for value in row]
            )


def main() -> int:
    for name in common.names(sys.argv[1:]):
        if not (common.STEMS_DIR / name / "other.flac").exists():
            print(f"{name}: no stems", flush=True)
            continue
        if not common.derived(name, "grid.json").exists():
            print(f"{name}: no pulse grid", flush=True)
            continue
        pulses = np.array(common.read_json(name, "grid.json")["pulses"])
        if not common.derived(name, "bass.csv").exists():
            notes = bass_notes(name)
            write_rows(name, "bass.csv", ["start", "end", "midi", "level_db"], notes)
            print(f"{name}: {len(notes)} bass notes", flush=True)
        if not common.derived(name, "other.csv").exists():
            notes = other_notes(name)
            write_rows(name, "other.csv", ["start", "end", "midi", "amplitude"], notes)
            print(f"{name}: {len(notes)} other notes", flush=True)
        if not common.derived(name, "chroma.npz").exists():
            np.savez_compressed(
                common.derived(name, "chroma.npz"),
                bass=pulse_chroma(name, "bass", pulses),
                other=pulse_chroma(name, "other", pulses),
            )
            print(f"{name}: chroma for {len(pulses)} pulses", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
