"""Find held notes that clash with the bass: a note one semitone above the root.

A melody note that is held for a long time one semitone (or a minor ninth)
above the bass note of its bar is the hardest clash in this style: the
minor ninth of the chord. The second version of the work had this in each
statement of the theme (an E, held from the bar before, above the chord of
E-flat).

The script takes the first note of the bass guitar in each bar as the root
of the bar (or of the synthesizer bass, if the bass guitar has a rest). It
shows each note of a melody player that sounds one semitone above that
root for one quarter note or longer.

Usage:

    uv run python tools/diagnose/clashes.py
"""

from __future__ import annotations

from fractions import Fraction

from gtypestar.notation.pitch import from_midi
from gtypestar.perform.events import perform
from gtypestar.work import build

MELODY = ("tsax", "tpt", "asax", "tbn", "bsax", "lead", "gtr", "vn1", "vn2", "va", "vc")
LONGEST_FREE = Fraction(1)  # quarter notes: a shorter clash is a passing note


def main() -> int:
    work = build()
    structure = work.structure
    roots: dict[int, float] = {}
    for player in ("sbass", "bass"):
        for note in sorted(perform(work, player), key=lambda item: item.start, reverse=True):
            if note.grace or note.midi <= 0:
                continue
            roots[structure.bar_at(note.start).number] = note.midi
    found = 0
    for player in MELODY:
        for note in perform(work, player):
            if note.grace:
                continue
            end = note.start + note.duration
            position = note.start
            while position < end:
                bar = structure.bar_at(position)
                stop = min(end, bar.end)
                root = roots.get(bar.number)
                long = root is not None and stop - position >= LONGEST_FREE
                if long and round(note.midi - root) % 12 == 1 and note.instrument != "guitar":
                    found += 1
                    print(
                        f"bar {bar.number}: {player} holds {from_midi(note.midi).name} for "
                        f"{float(stop - position):g} quarter notes above the bass note "
                        f"{from_midi(root).name}"
                    )
                position = stop
    print(f"{found} held notes one semitone above the bass note")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
