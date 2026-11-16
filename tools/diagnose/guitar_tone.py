"""Show the level of each band group for a heavy riff of the guitar model, for each amplifier.

The riff: sixteenth notes on the lowest string (F-sharp 1) with a muted
palm, and an open power chord on each fourth beat.

Usage:

    uv run python tools/diagnose/guitar_tone.py
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from gtypestar.audio import amp, dsp

GROUPS = [("45-90", 45, 90), ("90-180", 90, 180), ("180-355", 180, 355), ("355-710", 355, 710),
          ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800), ("2.8-5.6k", 2800, 5600),
          ("5.6-11k", 5600, 11200)]  # fmt: skip


def riff() -> list[amp.StringNote]:
    step = 60.0 / 175.0 / 4.0
    notes = []
    for bar in range(4):
        for index in range(16):
            start = (bar * 16 + index) * step
            if index % 16 == 12:
                for midi in (30, 37, 42):
                    notes.append(amp.StringNote(start, 4 * step, midi, 0.9))
            elif index % 16 < 12 and index % 4 != 3:
                notes.append(amp.StringNote(start, step, 30, 0.85, mute=0.8))
    return notes


def main() -> int:
    seconds = 4 * 16 * 60.0 / 175.0 / 4.0 + 1.0
    dry = amp.play(amp.GUITAR, riff(), seconds, seed=1)
    print(f"{'':12s}" + "".join(f"{name:>9s}" for name, _l, _h in GROUPS) + "    level")
    for name, settings in (("clean", amp.CLEAN), ("crunch", amp.CRUNCH),
                           ("high gain", amp.HIGH_GAIN), ("lead", amp.LEAD)):  # fmt: skip
        wet = amp.amplify(dry, settings)
        frequencies, power = signal.welch(wet, fs=dsp.RATE, nperseg=8192)
        step = frequencies[1] - frequencies[0]
        levels = np.array([
            10.0 * np.log10(power[(frequencies >= low) & (frequencies < high)].sum() * step + 1e-20)
            for _n, low, high in GROUPS
        ])  # fmt: skip
        total = 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))
        shown = "".join(f"{value:9.1f}" for value in levels - total)
        print(f"{name:12s}{shown}{total:9.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
