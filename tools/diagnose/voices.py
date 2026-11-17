"""Show if each recorded voice is above the band: the level of the voice and of the rest.

The script reads the stems of the full render (`build/stems`, or the
directory that is given). For the time of each cue with words, it shows the
level of the stem of the recorded sounds and the level of the sum of all
other stems, between 300 Hz and 3400 Hz (the band of a radio voice). A
voice that is some dB under the band cannot be understood.

Usage:

    uv run python tools/diagnose/voices.py [DIRECTORY]
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.work import build

BAND = (300.0, 3400.0)


def level(sound: np.ndarray) -> float:
    return 10.0 * np.log10(float(np.mean(sound.astype(np.float64) ** 2)) + 1e-12)


def main() -> int:
    stems = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/stems")
    paths = sorted(stems.glob("*.flac"))
    if not paths:
        print(f"no stems in {stems}")
        return 1
    work = build()
    structure = work.structure
    low = 0
    print(f"{'time':8s}{'voice':>8s}{'band':>8s}{'voice - band':>14s}   words")
    for cue in work.extras.get("cues", []):
        if not cue.text:
            continue
        start = structure.seconds(structure.bar(cue.bar).start + Fraction(cue.beat) - 1)
        seconds = cue.seconds or 1.0
        voice, rest = None, None
        for path in paths:
            with soundfile.SoundFile(str(path)) as handle:
                rate = handle.samplerate
                handle.seek(int(start * rate))
                sound = handle.read(int(seconds * rate), dtype="float32", always_2d=True)
            if len(sound) < 1000:
                continue
            sos = signal.butter(2, BAND, "bandpass", fs=rate, output="sos")
            sound = signal.sosfilt(sos, sound, axis=0)
            if path.stem.startswith("recorded"):
                voice = sound
            else:
                rest = sound if rest is None else rest[: len(sound)] + sound[: len(rest)]
        if voice is None or rest is None or level(voice) < -90.0:
            continue
        difference = level(voice) - level(rest)
        low += difference < 0.0
        print(f"{int(start // 60)}:{start % 60:04.1f}  {level(voice):8.1f}{level(rest):8.1f}"
              f"{difference:14.1f}   {cue.text}")  # fmt: skip
    print(f"{low} voices under the level of the band")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
