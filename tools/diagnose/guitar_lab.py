"""Try settings of the guitar amplifier on one passage, and compare them with real recordings.

The script makes the direct signal of the two rhythm guitars (or of the lead
guitar) of some bars one time, sends it through each rig of a table, and
writes one file for each rig. For each file it shows the level in nine
frequency bands, next to the same numbers of the real recordings in
`.cache/reference/guitar` (public examples of real distorted guitars, for
analysis only).

A rig of the table is a `guitar.Rig`: the model of the amplifier, the level
at its input, the filters before it, the cabinet (an impulse response), and
the filters after it.

Usage:

    uv run python tools/diagnose/guitar_lab.py FIRST-LAST TONE NAME=RIG [NAME=RIG ...]

TONE is the tone of the notes that are played ("high gain", "crunch",
"lead", "clean"). RIG is the name of a rig in `guitar.RIGS` or in `LAB`
below. The files are build/audio/lab-NAME.flac. Then:

    .cache/analysis-venv/bin/python tools/diagnose/judge.py build/audio/lab-*.flac \\
        --real .cache/reference/guitar
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import band, dsp, effects, guitar, render
from gtypestar.audio.guitar import Rig
from gtypestar.work import build

REAL = Path(".cache/reference/guitar")
BANDS = [(60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000),
         (4000, 6000), (6000, 9000), (9000, 14000)]  # fmt: skip

# Rigs to try. (The rigs of the work are in `guitar.RIGS`.)
BUGERA = "Phillipe_P_Bugera6262-Lead-NoDrive-Cab-ESR0.009.nam"
GODS = "Gods_Cab_1.4/48/"
ORBIT = "orbit-metal/darwinscat-guitar-cab-irs-metal-v1.1/48k/"
EDGE = GODS + "SM57/NO-TS/57_1_inch_edge_pres_3.wav"
CONE = GODS + "SM57/NO-TS/57_1_inch_cone_near_pres_3.wav"
MD421 = GODS + "MD421/NO-TS/MD421_1_inch_edge_pres_3.wav"
LAB: dict[str, Rig] = {
    # The amplifier of the third version, with no boost of the middle and no sound
    # above 5.5 kHz, and more of the low string.
    "dark": Rig(BUGERA, -8.0, 80.0, 6.0, 12.5,
                (("bell", 130.0, -2.0, 1.0), ("bell", 4000.0, -6.0, 1.0),
                 ("lowpass", 5500.0, 4))),
    "dark2": Rig(BUGERA, -8.0, 80.0, 6.0, 12.5,
                 (("low shelf", 110.0, 3.0), ("bell", 450.0, -3.0, 1.0),
                  ("bell", 4000.0, -7.0, 1.0), ("lowpass", 5000.0, 4))),
    "dark3": Rig(BUGERA, -8.0, 70.0, 6.0, 12.5,
                 (("low shelf", 110.0, 3.0), ("bell", 450.0, -3.0, 1.0),
                  ("bell", 4000.0, -8.0, 1.0), ("lowpass", 4600.0, 4))),
    "bug333": Rig("Phillipe_P_Bug333-Lead-NoDrive-Cab-ESR0.007.nam", -8.0, 75.0, 6.0, 12.5,
                  (("low shelf", 110.0, 3.0), ("bell", 450.0, -3.0, 1.0),
                   ("bell", 4000.0, -7.0, 1.0), ("lowpass", 5000.0, 4))),
    # An amplifier with no cabinet, and filters in the place of the cabinet (a test only).
    "5150-filters": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -10.0, 75.0, 0.0, 6.0,
                        (("highpass", 85.0, 2), ("bell", 120.0, 3.0, 1.2),
                         ("bell", 400.0, -4.0, 1.0), ("bell", 2600.0, 3.0, 1.2),
                         ("lowpass", 4800.0, 6))),
    # Amplifiers with no cabinet (captures of the open collection of the NAM community),
    # with the response of a real cabinet: "God's Cab" (a Mesa cabinet of 4 x 12 inches
    # with a Shure SM57 or a Sennheiser MD421), or a response of the Orbit set.
    "6505-57": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -8.0, 80.0, 0.0, 0.0,
                   (("lowpass", 7000.0, 2),), cabinet=EDGE),
    "5152-57": Rig("Tim_R_5152_Lead_+_TS9.nam", -8.0, 80.0, 0.0, 0.0,
                   (("lowpass", 7000.0, 2),), cabinet=EDGE),
    "5150-57": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -8.0, 80.0, 0.0, 0.0,
                   (("lowpass", 7000.0, 2),), cabinet=EDGE),
    "III-57": Rig("Helga_B_III_Red_-_805_Boost.nam", -8.0, 80.0, 0.0, 0.0,
                  (("lowpass", 7000.0, 2),), cabinet=EDGE),
    "6505-421": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -8.0, 80.0, 0.0, 0.0,
                    (("lowpass", 7000.0, 2),), cabinet=MD421),
    "6505-cone": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -8.0, 80.0, 0.0, 0.0,
                     (("lowpass", 7000.0, 2),),
                     cabinet=CONE),
    "6505-orbit2": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -8.0, 80.0, 0.0, 0.0,
                       (("lowpass", 7000.0, 2),), cabinet=ORBIT + "metal-02-4x12-venom.wav"),
    "6505-orbit3": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -8.0, 80.0, 0.0, 0.0,
                       (("lowpass", 7000.0, 2),), cabinet=ORBIT + "metal-03-4x12-anvil.wav"),
    # The same with less level at the input of the amplifier (less distortion), and
    # with the filters of the retuned rig after the cabinet.
    "5150-b": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -14.0, 80.0, 0.0, 0.0,
                  (("bell", 4000.0, -4.0, 1.0), ("lowpass", 5200.0, 4)),
                  cabinet=EDGE),
    "5150-c": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -14.0, 80.0, 0.0, 0.0,
                  (("bell", 900.0, 3.0, 0.7), ("bell", 4000.0, -4.0, 1.0),
                   ("lowpass", 5200.0, 4)),
                  cabinet=CONE),
    "6505-b": Rig("Helga_B_6505+_Red_ch_-_MXR_Drive_V2.nam", -14.0, 80.0, 0.0, 0.0,
                  (("bell", 4000.0, -4.0, 1.0), ("lowpass", 5200.0, 4)),
                  cabinet=CONE),
    "5152-b": Rig("Tim_R_5152_Lead_+_TS9.nam", -14.0, 80.0, 0.0, 0.0,
                  (("bell", 4000.0, -4.0, 1.0), ("lowpass", 5200.0, 4)),
                  cabinet=EDGE),
    "5150-d": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -20.0, 80.0, 0.0, 0.0,
                  (("bell", 4000.0, -4.0, 1.0), ("lowpass", 5200.0, 4)),
                  cabinet=EDGE),
}  # fmt: skip


def spectrum(sound: np.ndarray) -> list[float]:
    spec = np.abs(np.fft.rfft(sound * np.hanning(len(sound)))) ** 2
    freqs = np.fft.rfftfreq(len(sound), 1 / dsp.RATE)
    total = spec[(freqs >= 60) & (freqs < 14000)].sum()
    return [10 * np.log10(spec[(freqs >= low) & (freqs < high)].sum() / total + 1e-12)
            for low, high in BANDS]  # fmt: skip


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar",
         str(dsp.RATE), "-"], capture_output=True, check=True,
    ).stdout  # fmt: skip
    return np.frombuffer(raw, dtype=np.float32)


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    tone = sys.argv[2]
    jobs = [word.partition("=")[::2] for word in sys.argv[3:]]
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = [event for event in render._inside(render.player_events(work, "gtr"), begin, end)
              if (event.note.get("tone") or "clean") == tone]  # fmt: skip
    seconds = end - begin + render.LEAD_SECONDS + 3.0
    print(f"bars {first} to {last}: {len(events)} notes with the tone {tone!r}")
    print(f"{'':30s}" + "".join(f"{low:>7d}" for low, _high in BANDS))
    for path in sorted(REAL.iterdir()) if REAL.exists() else []:
        print(
            f"{'real ' + path.stem[:24]:30s}" + "".join(f"{v:7.1f}" for v in spectrum(load(path)))
        )
    # The direct signal of the two performances (or of the one lead guitar).
    takes = [(0, 11), (1, 23)] if tone != "lead" else [(0, 5)]
    dry = [guitar.direct(band._strokes(events, seed), seconds, side, seed) for side, seed in takes]
    canvas_size = int(seconds * dsp.RATE)
    for name, rig_name in jobs:
        rig = LAB.get(rig_name) or guitar.RIGS[rig_name]
        guitar.RIGS["lab"] = rig
        out = np.zeros((canvas_size, 2), dtype=np.float32)
        for (side, _seed), signal_dry in zip(takes, dry, strict=True):
            wet = guitar.amplify(signal_dry, "lab")[:canvas_size]
            place = 0.0 if tone == "lead" else 0.92 * (2 * side - 1)
            out[: len(wet)] += effects.pan(wet, place)
        out *= dsp.db(-1.0) / max(float(np.max(np.abs(out))), 1e-9)
        path = Path("build/audio") / f"lab-{name}.flac"
        soundfile.write(str(path), out, dsp.RATE, subtype="PCM_24")
        mono = out.mean(axis=1)[int(render.LEAD_SECONDS * dsp.RATE) :]
        print(f"{'lab-' + name[:26]:30s}" + "".join(f"{v:7.1f}" for v in spectrum(mono)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
