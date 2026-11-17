"""Try settings of the guitar program in the sampler on some bars.

The program of the guitar library has controllers (the tone filter
"Magnet", the kind of sound when a note stops, stronger recordings, the
level of the pick noise), and the player of `sfzguitar.py` has numbers of
its own (how fast notes must be for up strokes). The script writes the
guitar of some bars, as the full render plays it, one time for each row of
settings.

Usage:

    uv run python tools/diagnose/program_lab.py FIRST-LAST NAME=SETTINGS [NAME=SETTINGS ...]

SETTINGS is a list with commas. `48:64` sets the controller 48 to 64.
`fast:0.15` sets `sfzguitar.FAST`, `full:0.9` sets `sfzguitar.FULL`,
`level:6` sets `sfzguitar.DIRECT_DB`. `now` is the settings of the work.
The files are build/audio/lab-NAME.flac. Then:

    .cache/analysis-venv/bin/python tools/diagnose/judge.py build/audio/lab-*.flac \\
        --real .cache/reference/guitar
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import band, dsp, render, sfzguitar
from gtypestar.work import build

NUMBERS = {"fast": "FAST", "full": "FULL", "level": "DIRECT_DB", "join": "JOIN"}


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = render._inside(render.player_events(work, "gtr"), begin, end)
    seconds = end - begin + render.LEAD_SECONDS + 3.0
    settings = dict(sfzguitar.SETTINGS)
    numbers = {name: getattr(sfzguitar, name) for name in NUMBERS.values()}
    for job in sys.argv[2:]:
        name, _, text = job.partition("=")
        sfzguitar.SETTINGS.clear()
        sfzguitar.SETTINGS.update(settings)
        for word, value in numbers.items():
            setattr(sfzguitar, word, value)
        for part in text.split(","):
            key, _, value = part.partition(":")
            if key in NUMBERS:
                setattr(sfzguitar, NUMBERS[key], float(value))
            elif key != "now":
                sfzguitar.SETTINGS[int(key)] = int(value)
        audio = band.render_guitar(events, seconds)
        audio = audio * (dsp.db(-1.0) / max(float(np.max(np.abs(audio))), 1e-9))
        path = Path("build/audio") / f"lab-{name}.flac"
        soundfile.write(str(path), audio, dsp.RATE, subtype="PCM_24")
        print(f"wrote {path}: {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
