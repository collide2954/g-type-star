"""Show which stems are in front in each part of the work.

The script reads the stems of the full render (`build/stems`, made by
`gtypestar audio --export-stems`). For the first seconds after each
rehearsal mark, it shows the level of each stem relative to the level of
the mix. A passage has a clear plan if the stem with its main idea is near
the top of its row.

Usage:

    uv run python tools/diagnose/front.py [SECONDS]

SECONDS is the length of the part after each mark (default 16).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.work import build

STEMS = Path("build/stems")


def part(path: Path, start: float, seconds: float) -> np.ndarray:
    with soundfile.SoundFile(str(path)) as handle:
        handle.seek(int(start * handle.samplerate))
        return handle.read(int(seconds * handle.samplerate), dtype="float32", always_2d=True)


def level(sound: np.ndarray) -> float:
    return 10.0 * np.log10(float(np.mean(sound.astype(np.float64) ** 2)) + 1e-12)


def main() -> int:
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    paths = sorted(STEMS.glob("*.flac"))
    if not paths:
        print(f"no stems in {STEMS}: run `gtypestar audio --export-stems` first")
        return 1
    structure = build().structure
    marks = sorted((structure.seconds(structure.bar(bar).start), label)
                   for bar, label in structure.marks.items())  # fmt: skip
    print(f"{'mark':12s}" + "".join(f"{path.stem[:9]:>10s}" for path in paths) + "   in front")
    for start, label in [(0.0, "start"), *marks]:
        sounds = [part(path, start + 1.0, seconds) for path in paths]
        size = min(len(sound) for sound in sounds)
        if size < 1000:
            continue
        total = level(sum(sound[:size] for sound in sounds))
        levels = [level(sound[:size]) - total for sound in sounds]
        first = sorted(zip(levels, paths, strict=True), reverse=True)[:2]
        names = ", ".join(path.stem for _value, path in first)
        row = "".join(f"{max(value, -99.0):10.1f}" for value in levels)
        print(f"{label + f' {int(start // 60)}:{start % 60:04.1f}':12s}{row}   {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
