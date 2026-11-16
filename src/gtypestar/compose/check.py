"""Find music that a player cannot play.

The checks are:

- Each note must be in the range of the instrument.
- A wind instrument plays one note at a time.
- A wind player must have a rest to breathe.
- The drummer has two hands and two feet.
- Each note of the drums and of the drum machine must be a sound that exists.

The synthesizers, the drum machine, and the recorded sounds have no limits:
a sequencer or the studio plays them.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..notation import drums
from ..notation.pitch import from_midi
from ..notation.work import Work
from ..perform.events import PerfNote, perform

ONE_NOTE_FAMILIES = ("horns",)
BREATH_SECONDS = 0.35  # a rest of this length or more is time to breathe
LONGEST_BREATH = 18.0  # the longest time with no such rest, in seconds
FEET = {35, 36, 44}  # the drums that the feet play
HANDS = 2
DRUM_TABLES = {"drums": drums.BY_MIDI, "eperc": drums.MACHINE_BY_MIDI}


@dataclass(frozen=True)
class Problem:
    """One problem in the music of a player."""

    player: str
    bar: int
    text: str

    def __str__(self) -> str:
        return f"{self.player}, bar {self.bar}: {self.text}"


def _breath_problems(work: Work, player: str, notes: list[PerfNote]) -> list[Problem]:
    """Find the passages of a wind player that are too long with no rest."""
    problems: list[Problem] = []
    structure = work.structure
    start = end = None
    for note in notes:
        begin = structure.seconds(note.start)
        finish = structure.seconds(note.start + note.duration)
        if end is None or begin - end >= BREATH_SECONDS:
            start = begin
            flagged = False
        end = max(end or 0.0, finish)
        if end - start > LONGEST_BREATH and not flagged:
            flagged = True
            text = f"more than {LONGEST_BREATH:.0f} s with no rest to breathe"
            problems.append(Problem(player, structure.bar_at(note.start).number, text))
    return problems


def _limb_problems(work: Work, player: str, notes: list[PerfNote]) -> list[Problem]:
    """Find the moments at which the drummer needs more than two hands or two feet."""
    problems: list[Problem] = []
    moments: dict[Fraction, list[int]] = {}
    for note in notes:
        if note.grace == 0:
            moments.setdefault(note.start, []).append(int(note.midi))
    for start, strokes in sorted(moments.items()):
        hands = [midi for midi in strokes if midi not in FEET]
        feet = [midi for midi in strokes if midi in FEET]
        if len(hands) > HANDS or len(feet) > 2:
            text = f"{len(hands)} strokes of the hands and {len(feet)} of the feet at one time"
            problems.append(Problem(player, work.structure.bar_at(start).number, text))
    return problems


def check(work: Work) -> list[Problem]:
    """Return the problems in the work, in the sequence of the score."""
    problems: list[Problem] = []
    structure = work.structure
    for player in work.orchestra.players:
        seen: set[tuple[int, str]] = set()
        notes = sorted(perform(work, player.id), key=lambda item: item.start)
        if player.family in ONE_NOTE_FAMILIES:
            problems.extend(_breath_problems(work, player.id, notes))
        if player.id == "drums":
            problems.extend(_limb_problems(work, player.id, notes))
        for note in notes:
            bar = structure.bar_at(note.start).number
            if player.id in DRUM_TABLES and int(note.midi) not in DRUM_TABLES[player.id]:
                text = f"the note {from_midi(note.midi).name} is not a sound of the {player.name}"
                if (bar, text) not in seen:
                    seen.add((bar, text))
                    problems.append(Problem(player.id, bar, text))
            instrument = work.orchestra.instruments.get(note.instrument)
            if instrument is not None and not note.harmonic:
                name = from_midi(note.midi).name
                if note.midi < instrument.low:
                    text = f"{name} is below the range of the {note.instrument}"
                elif note.midi > instrument.high:
                    text = f"{name} is above the range of the {note.instrument}"
                else:
                    text = ""
                if text and (bar, text) not in seen:
                    seen.add((bar, text))
                    problems.append(Problem(player.id, bar, text))
            if player.family in ONE_NOTE_FAMILIES and note.chord_size > 1:
                text = f"a chord for the {note.instrument}"
                if (bar, text) not in seen:
                    seen.add((bar, text))
                    problems.append(Problem(player.id, bar, text))
    return problems
