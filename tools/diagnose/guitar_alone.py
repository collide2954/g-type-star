"""Write the guitar part of some bars alone, as the full render plays it.

The file has the guitar only (the two rhythm guitars on the sides, the lead
guitar in the centre with its echoes), with no mix and no master. It is for
a fast check of the guitar sound.

Usage:

    uv run python tools/diagnose/guitar_alone.py FIRST-LAST NAME

The result is build/audio/NAME.flac and build/audio/NAME.mp3.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import band, dsp, render
from gtypestar.work import build


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    name = sys.argv[2]
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = render._inside(render.player_events(work, "gtr"), begin, end)
    tones: dict[str, int] = {}
    for event in events:
        tone = event.note.get("tone") or "clean"
        tones[tone] = tones.get(tone, 0) + 1
    print(f"bars {first} to {last}: {end - begin:.1f} s, notes of each tone: {tones}")
    audio = band.render_guitar(events, end - begin + render.LEAD_SECONDS + 3.0)
    audio = audio * (dsp.db(-1.0) / max(float(np.max(np.abs(audio))), 1e-9))
    directory = Path("build/audio")
    directory.mkdir(parents=True, exist_ok=True)
    flac = directory / f"{name}.flac"
    soundfile.write(str(flac), audio, dsp.RATE, subtype="PCM_24")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(flac), "-codec:a", "libmp3lame",
         "-q:a", "1", str(flac.with_suffix(".mp3"))],
        check=True,
    )  # fmt: skip
    print(f"wrote {flac.with_suffix('.mp3')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
