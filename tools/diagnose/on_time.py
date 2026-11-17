"""Show how late the notes of the stems are against their written times.

A sampler plays a recording of a note from its start. But a recording does
not start with the note: first the pick or the finger is on the string. In
all versions to 3.4 the guitar was 15 to 26 milliseconds late for this
reason, and the bass guitar 26 milliseconds. A band is tight when the
strokes of its players come at the same moment.

The script reads the stems of a full render (`build/stems`, made by
`gtypestar audio --export-stems`) and the notes of the work as the players
play them. For each row (a stem, and the notes of some of its players) it
takes the notes that start after a quiet moment, finds the moment at which
each note sounds in the stem (the first value of half of the largest value
near the note), and shows the middle value of "sound minus written time" in
milliseconds, with the range of the middle half of the notes.

The rows are for instruments with a sharp start. (A saxophone or a string
section has a slow start: this measurement says nothing about them.)

Usage:

    uv run python tools/diagnose/on_time.py [DIRECTORY ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.audio import render
from gtypestar.work import build

BEFORE, AFTER = 0.06, 0.08  # seconds: the part of the stem around a written time
QUIET_PART = 0.02  # seconds: the start of that part must be quiet
QUIET = 0.25  # "quiet": under this part of the largest value
SILENT = 1e-3  # a note under this value is not in the stem
CHORD = 0.03  # seconds: notes that start nearer than this are one chord
# The rows: a name, the stem, the players, the keys of the notes (None: all), and the
# frequency band of the measurement in hertz.
ROWS = [
    ("kick drums", "drums", ["drums"], (35, 36), (30.0, 8000.0)),
    ("snare drum", "drums", ["drums"], (38, 40), (150.0, 8000.0)),
    ("bass guitar", "bass", ["bass"], None, (30.0, 4000.0)),
    ("guitar", "guitar", ["gtr"], None, (60.0, 8000.0)),
    ("electric piano", "keys", ["keys.rh", "keys.lh"], None, (60.0, 8000.0)),
]


def lateness(sound: np.ndarray, rate: int, starts: list[float]) -> np.ndarray:
    """Return "sound minus written time" in seconds for the notes with a quiet start."""
    size = np.abs(sound)
    result = []
    for start in starts:
        first = int((start - BEFORE) * rate)
        if first < 0 or first + int((BEFORE + AFTER) * rate) > len(size):
            continue
        part = size[first : first + int((BEFORE + AFTER) * rate)]
        top = float(part.max())
        if top < SILENT or float(part[: int(QUIET_PART * rate)].max()) > QUIET * top:
            continue
        result.append(float(np.flatnonzero(part >= 0.5 * top)[0]) / rate - BEFORE)
    return np.array(result)


def main() -> int:
    directories = [Path(word) for word in sys.argv[1:]] or [Path("build/stems")]
    work = build()
    events = {}
    for _name, _stem, players, _keys, _band in ROWS:
        for player in players:
            if player not in events:
                events[player] = render.player_events(work, player)
    for directory in directories:
        print(f"{directory}: sound minus written time in milliseconds")
        print(f"{'notes of':16s}{'notes':>7s}{'middle value':>14s}{'middle half of them':>28s}")
        for name, stem, players, keys, band in ROWS:
            path = directory / f"{stem}.flac"
            if not path.exists():
                continue
            sound, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
            sos = signal.butter(2, band, "bandpass", fs=rate, output="sos")
            mono = signal.sosfilt(sos, sound.mean(axis=1))
            starts = []
            for start in sorted(event.start for player in players for event in events[player]
                                if keys is None or int(event.midi) in keys):  # fmt: skip
                # The notes of a chord are one stroke: its time is the time of its first note.
                if not starts or start - starts[-1] > CHORD:
                    starts.append(start)
            values = 1000.0 * lateness(mono, rate, starts)
            if len(values) < 5:
                print(f"{name:16s}{len(values):7d}")
                continue
            low, middle, high = np.percentile(values, [25, 50, 75])
            print(f"{name:16s}{len(values):7d}{middle:+14.1f}{f'{low:+.1f} to {high:+.1f}':>28s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
