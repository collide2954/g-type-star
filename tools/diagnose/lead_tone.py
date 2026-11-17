"""Try amplifier settings for the lead tone of the guitar on bars of the work.

The script takes the notes of the guitar in some bars (for example the first
bars of the guitar solo), plays them with the recorded guitar through some
amplifier settings, shows the level of each band group, and writes the
sounds to build/checks/lead-*.flac.

Usage:

    uv run python tools/diagnose/lead_tone.py FIRST-LAST [SEMITONES]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.audio import band, dsp, guitar, render
from gtypestar.work import build

GROUPS = [("90-180", 90, 180), ("180-355", 180, 355), ("355-710", 355, 710),
          ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800), ("2.8-5.6k", 2800, 5600),
          ("5.6-11k", 5600, 11200)]  # fmt: skip
P = "Phillipe_P_"
CREAM = (("bell", 500.0, 4.0, 0.6), ("bell", 3500.0, -8.0, 0.9), ("lowpass", 4800.0, 4))
RIGS = {
    "now": guitar.RIGS["lead"],
    "333 cream": guitar.Rig(P + "Bug333-Lead-NoDrive-Cab-ESR0.007.nam", -8.0, 90.0, 4.0, 9.0,
                            CREAM, tone_hz=2200.0),
    "jvm cream": guitar.Rig(P + "JVM-OD2-RD-NoDrive-Cab-ESR0.006.nam", -8.0, 90.0, 4.0, 9.0,
                            CREAM, tone_hz=2200.0),
    "6262 cream": guitar.Rig(P + "Bugera6262-Lead-NoDrive-Cab-ESR0.009.nam", -8.0, 90.0, 4.0,
                             9.0, CREAM, tone_hz=2200.0),
    "crunch cream": guitar.Rig(P + "Bug333-Crunch-DT-Cab-ESR0.014.nam", -6.0, 90.0, 4.0, 9.0,
                               CREAM, tone_hz=2200.0),
}  # fmt: skip


def show(name: str, wet: np.ndarray) -> None:
    frequencies, power = signal.welch(wet, fs=dsp.RATE, nperseg=8192)
    step = frequencies[1] - frequencies[0]
    levels = np.array([
        10.0 * np.log10(power[(frequencies >= low) & (frequencies < high)].sum() * step + 1e-20)
        for _n, low, high in GROUPS
    ])  # fmt: skip
    total = 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))
    print(f"{name:14s}" + "".join(f"{value:9.1f}" for value in levels - total) + f"{total:9.1f}")


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    bars = (int(first), int(last))
    work = build()
    begin, end = render.window(work, bars)
    events = render._inside(render.player_events(work, "gtr"), begin, end)
    events = [event for event in events if event.note.get("tone") == "lead"]
    seconds = end - begin + 2.0
    strokes = band._strokes(events)
    shift = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0  # semitones, for a trial
    if shift:
        from dataclasses import replace

        strokes = [
            replace(stroke, midi=stroke.midi + shift,
                    slide_from=None if stroke.slide_from is None else stroke.slide_from + shift)
            for stroke in strokes
        ]  # fmt: skip
    dry = guitar.direct(strokes, seconds, 0, 5)
    target = Path("build/checks")
    target.mkdir(parents=True, exist_ok=True)
    print(f"{len(strokes)} notes of the lead tone, {sum(s.hammer for s in strokes)} with no stroke")
    print(f"{'':14s}" + "".join(f"{name:>9s}" for name, _l, _h in GROUPS) + "    level")
    show("direct", dry)
    for name, rig in RIGS.items():
        guitar.RIGS["trial"] = rig
        wet = guitar.amplify(dry, "trial")
        show(name, wet)
        label = name.replace(" ", "-") + (f"{shift:+.0f}" if shift else "")
        soundfile.write(str(target / f"lead-{label}.flac"), wet, dsp.RATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
