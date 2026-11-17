"""Find notes of the solo saxophone that have no sound in the render of MuseScore.

MuseScore gives no sound for a note outside the range of its samples (see
`muse_ranges.py`). The checker of the work finds such notes from the table
of ranges. This script is the test of the audio itself: it reads the stem
of the tenor saxophone that MuseScore made for the full work, and it looks
at the level of the stem in the time of each written note.

Usage:

    uv run python tools/diagnose/silent_notes.py

The stem is `build/musescore/tsax/score.wav`: run a full render first. The
script looks at the stem as it goes into the mix: after `musestems.even`
made its weak notes louder.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from gtypestar.audio import musescore, musestems
from gtypestar.notation.pitch import from_midi
from gtypestar.perform.events import perform
from gtypestar.work import build

STEM = Path("build/musescore/tsax/score.wav")
SILENT_DB = -62.0  # in the file of MuseScore (before the level of its master control)


def main() -> int:
    if not STEM.exists():
        print(f"{STEM} is not there: run `gtypestar audio` first")
        return 1
    work = build()
    structure = work.structure
    # The stem as it goes into the mix: at the sample rate of the project, and with its
    # weak notes made louder.
    audio = musestems.even(work, None, "tsax", musescore._load(STEM))
    rate = musestems.RATE
    mono = audio.mean(axis=1)
    notes = [note for note in perform(work, "tsax") if not note.grace]
    silent = []
    for note in notes:
        start = structure.seconds(note.start)
        end = structure.seconds(note.start + note.duration)
        first = int((start + 0.02) * rate)
        last = int(min(end, start + 0.4) * rate)
        part = mono[first:last]
        if len(part) < 64:
            continue
        level = 10.0 * np.log10(float(np.mean(part**2)) + 1e-12)
        if level < SILENT_DB - musescore.MASTER_VOLUME_DB:
            silent.append((structure.bar_at(note.start).number, from_midi(note.midi).name, level))
    print(f"{len(notes)} notes of the tenor saxophone, {len(silent)} with no sound")
    for bar, name, level in silent[:60]:
        print(f"  bar {bar}: {name} ({level:.0f} dB)")
    return 1 if silent else 0


if __name__ == "__main__":
    sys.exit(main())
