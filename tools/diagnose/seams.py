"""Show the level of a render near each rehearsal mark: before, after, and the lowest value.

Usage:

    uv run python tools/diagnose/seams.py build/audio/render.flac
"""

from __future__ import annotations

import sys

import numpy as np

from gtypestar.audio import reference
from gtypestar.work import build

RATE = 48000
STEP = 0.1


def main() -> int:
    audio = reference.load_stereo(sys.argv[1])
    structure = build().structure
    size = int(STEP * RATE)
    count = len(audio) // size
    power = (audio[: count * size] ** 2).reshape(count, size, 2).mean(axis=(1, 2))
    level = 10.0 * np.log10(power + 1e-12)

    def mean(start: float, end: float) -> float:
        part = power[max(0, int(start / STEP)) : max(1, int(end / STEP))]
        return 10.0 * np.log10(part.mean() + 1e-12)

    print("mark  time    4 s before  4 s after  change   lowest 0.1 s within 1.5 s of the mark")
    for bar, label in sorted(structure.marks.items()):
        time = structure.seconds(structure.bar(bar).start)
        before, after = mean(time - 4.0, time), mean(time, time + 4.0)
        near = level[max(0, int((time - 1.5) / STEP)) : int((time + 1.5) / STEP)]
        low = float(near.min())
        where = (int(np.argmin(near)) - 15) * STEP
        print(
            f"{label:4s} {int(time // 60)}:{time % 60:04.1f}   {before:7.1f}   {after:7.1f}   "
            f"{after - before:+6.1f}    {low:6.1f} dB at {where:+.1f} s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
