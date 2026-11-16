"""Find the sudden pauses of a render: places where the level falls fast and stays low.

Usage:

    uv run python tools/diagnose/pauses.py build/audio/render.flac
"""

from __future__ import annotations

import sys

import numpy as np

from gtypestar.audio import reference
from gtypestar.work import build

RATE = 48000
STEP = 0.05  # seconds


def main() -> int:
    audio = reference.load_stereo(sys.argv[1])
    work = build()
    structure = work.structure
    marks = sorted((structure.seconds(structure.bar(bar).start), label)
                   for bar, label in structure.marks.items())  # fmt: skip
    size = int(STEP * RATE)
    count = len(audio) // size
    power = (audio[: count * size] ** 2).reshape(count, size, 2).mean(axis=(1, 2))
    level = 10.0 * np.log10(power + 1e-12)
    before = int(2.0 / STEP)
    found = []
    index = before
    while index < count - 4:
        usual = float(np.median(level[index - before : index]))
        if usual > -32.0 and level[index] < usual - 14.0:
            end = index
            while end < count and level[end] < usual - 10.0:
                end += 1
            seconds = (end - index) * STEP
            if seconds >= 0.2:
                depth = usual - float(level[index:end].min())
                found.append((index * STEP, seconds, depth, usual))
            index = end + int(1.0 / STEP)
        else:
            index += 1
    for start, seconds, depth, usual in found:
        label = [name for time, name in marks if time <= start]
        bar = structure.bar_at(_position(structure, start)).number
        mark = label[-1] if label else "-"
        print(
            f"{int(start // 60)}:{start % 60:05.2f}  mark {mark}  bar {bar:3d}"
            f"  {seconds:5.2f} s  {depth:5.1f} dB below the level before ({usual:.0f} dB)"
        )
    return 0


def _position(structure, seconds: float) -> float:
    low, high = 0.0, float(structure.length)
    for _ in range(40):
        middle = 0.5 * (low + high)
        if structure.seconds(middle) < seconds:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


if __name__ == "__main__":
    raise SystemExit(main())
