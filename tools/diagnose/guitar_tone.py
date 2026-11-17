"""Show the level of each band group for a heavy riff of the guitar, for each amplifier.

The riff: sixteenth notes on the lowest string (F-sharp 1) with a muted
palm, and an open power chord on each fourth beat. The script plays it with
the string model and with the recorded guitar (if the library is there).

Usage:

    uv run python tools/diagnose/guitar_tone.py [--write]

With `--write`, the script writes the sounds to build/checks/guitar-*.flac.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.audio import amp, dsp, guitar

GROUPS = [("45-90", 45, 90), ("90-180", 90, 180), ("180-355", 180, 355), ("355-710", 355, 710),
          ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800), ("2.8-5.6k", 2800, 5600),
          ("5.6-11k", 5600, 11200)]  # fmt: skip
STEP = 60.0 / 175.0 / 4.0  # one sixteenth note at 175 quarter notes in a minute
BARS = 4


def riff() -> list[tuple[float, float, int, float, bool]]:
    """Return the notes: start, length, MIDI number, loudness, and "muted"."""
    notes = []
    for bar in range(BARS):
        for index in range(16):
            start = (bar * 16 + index) * STEP
            if index == 12:
                notes += [(start, 4 * STEP, midi, 0.9, False) for midi in (30, 37, 42)]
            elif index < 12 and index % 4 != 3:
                notes.append((start, STEP, 30, 0.85, True))
    return notes


def show(name: str, wet: np.ndarray) -> None:
    frequencies, power = signal.welch(wet, fs=dsp.RATE, nperseg=8192)
    step = frequencies[1] - frequencies[0]
    levels = np.array([
        10.0 * np.log10(power[(frequencies >= low) & (frequencies < high)].sum() * step + 1e-20)
        for _n, low, high in GROUPS
    ])  # fmt: skip
    total = 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))
    shown = "".join(f"{value:9.1f}" for value in levels - total)
    print(f"{name:22s}{shown}{total:9.1f}")


def main() -> int:
    seconds = BARS * 16 * STEP + 1.0
    write = "--write" in sys.argv
    target = Path("build/checks")
    target.mkdir(parents=True, exist_ok=True)
    print(f"{'':22s}" + "".join(f"{name:>9s}" for name, _l, _h in GROUPS) + "    level")
    notes = [amp.StringNote(s, length, midi, level, mute=0.8 if muted else 0.0)
             for s, length, midi, level, muted in riff()]  # fmt: skip
    dry = amp.play(amp.GUITAR, notes, seconds, seed=1)
    for name, settings in (("clean", amp.CLEAN), ("crunch", amp.CRUNCH),
                           ("high gain", amp.HIGH_GAIN), ("lead", amp.LEAD)):  # fmt: skip
        wet = amp.amplify(dry, settings)
        show(f"model: {name}", wet)
        if write:
            soundfile.write(str(target / f"guitar-model-{name.replace(' ', '-')}.flac"), wet,
                            dsp.RATE)  # fmt: skip
    if not guitar.available():
        print("(the recorded guitar is not on this computer)")
        return 0
    strokes = [guitar.Stroke(s, length, midi, level, mute=muted)
               for s, length, midi, level, muted in riff()]  # fmt: skip
    sides = [guitar.direct(strokes, seconds, side, seed=1) for side in (0, 1)]
    show("recorded: direct", sides[0])
    for name in guitar.RIGS:
        both = [guitar.amplify(side, name) for side in sides]
        show(f"recorded: {name}", both[0])
        if write:
            stereo = np.stack(both, axis=1)
            soundfile.write(str(target / f"guitar-recorded-{name.replace(' ', '-')}.flac"),
                            stereo, dsp.RATE)  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
