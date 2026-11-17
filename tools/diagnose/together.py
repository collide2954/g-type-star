"""Show how well the strokes of two stems are together in time, part by part.

A band is tight when the strokes of its players come at the same moment.
The script reads two stems of a full render (for example the drums and
the guitar). For each part of the work (from one rehearsal mark to the
next) it finds the delay of the second stem against the first stem: the
delay at which the starts of the sounds of the two stems agree best.

A positive delay: the second stem is late. The "agreement" is a number
from 0 to 1; a small number says that the two stems do not have their
strokes at the same places in this part (the delay then says nothing).

In all versions to 3.4, the guitar was 15 to 26 milliseconds behind its
written time. This script shows such a fault in the stems of a render.

Usage:

    uv run python tools/diagnose/together.py FIRST.flac SECOND.flac [SECOND.flac ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.work import build

FRAME = 0.001  # seconds: the step of the stroke curve
REACH = 0.06  # seconds: the largest delay that the script looks for
QUIET = 1e-4  # a part with a stem under this level has no row
AGREE = 0.15  # an agreement under this number has no clear delay


def strokes(path: Path, start: float, seconds: float) -> np.ndarray:
    """Return the stroke curve of a part of a stem: where the level of the high
    frequencies goes up, in steps of `FRAME`."""
    with soundfile.SoundFile(str(path)) as handle:
        rate = handle.samplerate
        handle.seek(int(start * rate))
        sound = handle.read(int(seconds * rate), dtype="float32", always_2d=True).mean(axis=1)
    if len(sound) < rate or float(np.sqrt(np.mean(sound**2))) < QUIET:
        return np.zeros(0)
    high = signal.sosfilt(signal.butter(2, 1500.0, "highpass", fs=rate, output="sos"), sound)
    size = int(FRAME * rate)
    frames = np.abs(high[: len(high) // size * size]).reshape(-1, size).mean(axis=1)
    level = np.convolve(frames, np.ones(3) / 3.0, mode="same")
    return np.maximum(np.diff(level, prepend=level[0]), 0.0)


def delay(first: np.ndarray, second: np.ndarray) -> tuple[float, float]:
    """Return the delay of the second curve against the first curve in seconds, and
    the agreement of the two curves at that delay."""
    size = min(len(first), len(second))
    if size < 1000:
        return 0.0, 0.0
    first, second = first[:size], second[:size]
    norm = float(np.sqrt(np.sum(first**2) * np.sum(second**2)))
    if norm <= 0.0:
        return 0.0, 0.0
    reach = int(REACH / FRAME)
    inner = first[reach : size - reach]
    values = [float(np.dot(inner, second[reach + lag : size - reach + lag]))
              for lag in range(-reach, reach + 1)]  # fmt: skip
    best = int(np.argmax(values))
    return (best - reach) * FRAME, values[best] / norm


def main() -> int:
    first, *others = [Path(word) for word in sys.argv[1:]]
    structure = build().structure
    marks = sorted((structure.seconds(structure.bar(bar).start), label)
                   for bar, label in structure.marks.items())  # fmt: skip
    marks = [(0.0, "start"), *marks]
    ends = [start for start, _label in marks[1:]] + [structure.seconds(structure.length)]
    names = "".join(f"{path.parent.name[:12] + '/' + path.stem[:8]:>24s}" for path in others)
    print(f"the delay against {first} in milliseconds (the agreement)\n{'mark':12s}{names}")
    for (start, label), end in zip(marks, ends, strict=True):
        base = strokes(first, start, end - start)
        row = ""
        for path in others:
            seconds, agreement = delay(base, strokes(path, start, end - start))
            text = f"{1000.0 * seconds:+.0f} ({agreement:.2f})" if agreement >= AGREE else "-"
            row += f"{text:>24s}"
        if row.strip("- "):
            print(f"{label + f' {int(start // 60)}:{start % 60:04.1f}':12s}{row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
