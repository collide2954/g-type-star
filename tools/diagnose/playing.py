"""Show what each player has to do: the range, the speed, the leaps, the hands.

`gtypestar check` finds the notes that a player cannot play at all. This
script shows the numbers behind the harder question: is a passage good
writing for the instrument? For each player it shows:

- the lowest and the highest note, with the bar of the highest note;
- the fastest passage: the largest number of notes in one second, and the
  bar where it is;
- for wind players: the fastest passage of notes that are not under a slur
  (the tongue has to start each note);
- the large leaps between two fast notes (an octave or more, with less
  than `FAST_SECONDS` for the first note);
- for the electric piano: the chords of one hand that are wider than a
  tenth.

Usage:

    uv run python tools/diagnose/playing.py [PLAYER ...]
"""

from __future__ import annotations

import sys
from collections import defaultdict

from gtypestar.notation.pitch import from_midi
from gtypestar.perform.events import perform
from gtypestar.work import build

FAST_SECONDS = 0.16  # a note shorter than this is a fast note
LEAP = 12  # semitones
HAND = 16  # semitones: a tenth
WINDOW = 1.0  # seconds
NO_LIMITS = ("lead", "pad.rh", "pad.lh", "chip", "sbass", "eperc", "drums", "perc")


def main() -> int:
    work = build()
    structure = work.structure
    wanted = sys.argv[1:]
    for player in work.orchestra.players:
        if wanted and player.id not in wanted:
            continue
        if not wanted and player.id in NO_LIMITS:
            continue
        notes = sorted(
            (note for note in perform(work, player.id) if note.grace == 0 and note.midi > 0),
            key=lambda item: (item.start, item.midi),
        )
        if not notes:
            continue
        times = [(structure.seconds(note.start), note) for note in notes]
        low = min(notes, key=lambda item: item.midi)
        high = max(notes, key=lambda item: item.midi)
        print(f"\n{player.id}: {len(notes)} notes")
        print(f"  range   {from_midi(low.midi).name} to {from_midi(high.midi).name} "
              f"(bar {structure.bar_at(high.start).number})")  # fmt: skip
        # The fastest second: the starts of the notes (a chord is one start).
        starts = sorted({(seconds, note.start) for seconds, note in times})
        best, where = 0, None
        first = 0
        for last in range(len(starts)):
            while starts[last][0] - starts[first][0] > WINDOW:
                first += 1
            if last - first + 1 > best:
                best, where = last - first + 1, starts[first][1]
        print(f"  speed   {best} notes in one second (bar {structure.bar_at(where).number})")
        if player.family == "horns":
            tongued = [(seconds, note) for seconds, note in times if not note.legato]
            best, where = 0, None
            first = 0
            for last in range(len(tongued)):
                while tongued[last][0] - tongued[first][0] > WINDOW:
                    first += 1
                if last - first + 1 > best:
                    best, where = last - first + 1, tongued[first][1].start
            print(f"  tongue  {best} starts with the tongue in one second "
                  f"(bar {structure.bar_at(where).number})")  # fmt: skip
        # Leaps between fast notes, for the players of one line.
        if player.family in ("horns", "strings") or player.id in ("gtr", "bass"):
            leaps: dict[int, list[str]] = defaultdict(list)
            for (seconds, note), (after, following) in zip(times, times[1:], strict=False):
                if note.chord_size > 1 or following.chord_size > 1:
                    continue
                gap = after - seconds
                size = abs(following.midi - note.midi)
                if 0 < gap < FAST_SECONDS and size >= LEAP:
                    bar = structure.bar_at(note.start).number
                    leaps[bar].append(
                        f"{from_midi(note.midi).name}-{from_midi(following.midi).name}"
                    )
            total = sum(len(found) for found in leaps.values())
            print(f"  leaps   {total} leaps of an octave or more between fast notes")
            for bar, found in sorted(leaps.items()):
                print(f"          bar {bar}: {', '.join(found)}")
        if player.id.startswith("keys"):
            wide: dict[int, int] = {}
            chords: dict[tuple, list[float]] = defaultdict(list)  # one hand at one time
            for note in notes:
                chords[(note.start, note.voice)].append(note.midi)
            for (start, _voice), pitches in chords.items():
                span = max(pitches) - min(pitches)
                if span > HAND:
                    bar = structure.bar_at(start).number
                    wide[bar] = max(wide.get(bar, 0), int(span))
            places = ", ".join(f"bar {bar} ({span})" for bar, span in sorted(wide.items()))
            print(f"  hands   {len(wide)} bars with a chord wider than a tenth: {places}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
