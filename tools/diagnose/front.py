"""Show which stems are in front in each part of the work.

The script reads the stems of the full render (`build/stems`, made by
`gtypestar audio --export-stems`). For the first seconds after each
rehearsal mark, it shows the level of each stem relative to the level of
the mix. A passage has a clear plan if the stem with its main idea is near
the top of its row.

The levels are the levels between 250 Hz and 6000 Hz: this is where the
ear finds the instrument that leads. (The low notes of the bass and the
kick drum have the most energy of a mix, but they are not "in front".)
With the word `full` the script shows the levels of all frequencies.

Usage:

    uv run python tools/diagnose/front.py [SECONDS] [full] [DIRECTORY]

SECONDS is the length of the part after each mark (default 16). DIRECTORY is
the directory of the stems (default `build/stems`; see also
`tools/diagnose/part_stems.py`).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.work import build

STEMS = Path("build/stems")


BAND = (250.0, 6000.0)  # Hz


def part(path: Path, start: float, seconds: float, full: bool) -> np.ndarray:
    with soundfile.SoundFile(str(path)) as handle:
        handle.seek(int(start * handle.samplerate))
        sound = handle.read(int(seconds * handle.samplerate), dtype="float32", always_2d=True)
        if full or len(sound) < 1000:
            return sound
        sos = signal.butter(2, BAND, "bandpass", fs=handle.samplerate, output="sos")
        return signal.sosfilt(sos, sound, axis=0)


def level(sound: np.ndarray) -> float:
    return 10.0 * np.log10(float(np.mean(sound.astype(np.float64) ** 2)) + 1e-12)


def main() -> int:
    words = [word for word in sys.argv[1:] if word != "full"]
    full = "full" in sys.argv[1:]
    numbers = [word for word in words if word.replace(".", "").isdigit()]
    directories = [word for word in words if word not in numbers]
    seconds = float(numbers[0]) if numbers else 16.0
    stems = Path(directories[0]) if directories else STEMS
    paths = sorted(stems.glob("*.flac"))
    if not paths:
        print(f"no stems in {stems}: run `gtypestar audio --export-stems` first")
        return 1
    structure = build().structure
    marks = sorted((structure.seconds(structure.bar(bar).start), label)
                   for bar, label in structure.marks.items())  # fmt: skip
    print(f"{'mark':12s}" + "".join(f"{path.stem[:9]:>10s}" for path in paths) + "   in front")
    for start, label in [(0.0, "start"), *marks]:
        sounds = [part(path, start + 1.0, seconds, full) for path in paths]
        size = min(len(sound) for sound in sounds)
        if size < 1000:
            continue
        total = level(sum(sound[:size] for sound in sounds))
        if total < -80.0:
            continue  # a part that is not in these stems
        levels = [level(sound[:size]) - total for sound in sounds]
        first = sorted(zip(levels, paths, strict=True), reverse=True)[:2]
        names = ", ".join(path.stem for _value, path in first)
        row = "".join(f"{max(value, -99.0):10.1f}" for value in levels)
        print(f"{label + f' {int(start // 60)}:{start % 60:04.1f}':12s}{row}   {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
