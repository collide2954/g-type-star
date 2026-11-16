"""Give the performance notes the timing and the loudness of real players.

The written music is exact: each note is on the grid. A player is not
exact, and the small differences are a part of the style. This module
changes each performance note into an event with a time in seconds:

- A constant shift: a player is before or behind the beat.
- A random part for each note, and a slow drift over some seconds.
- Swing: the second half of a note value comes late.
- Lay-back: a lead player puts the notes on the beat late and the notes
  between the beats on the grid.
- Chords: the notes of a chord do not start at the same moment.
- Loudness: accents from the place in the pulse, soft ghost notes, and a
  random part.

The values come from published measurements and from the reference
recordings (see `research/tables/profiles.csv`, profile "Feel"). All random
values come from the name of the player and the position of the note: the
result is the same for each build.

The parts that a machine plays (synthesizers with a sequencer, the drum
machine) get no changes. The difference between the exact machine parts and
the human parts is a part of the sound of the style.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field, replace
from fractions import Fraction

import numpy as np

from ..notation.structure import Structure
from .events import PerfNote


@dataclass(frozen=True)
class Feel:
    """How one player places the notes in time, and how loud each note is."""

    late_ms: float = 0.0  # constant shift; a positive value is behind the beat
    spread_ms: float = 0.0  # standard deviation of the random part of each note
    drift_ms: float = 0.0  # size of the slow random change
    swing: float = 0.5  # place of the second half of the swing unit (0.5 = even)
    swing_unit: Fraction = Fraction(1, 2)  # the note value that the swing divides
    layback: float = 0.0  # notes on the beat are late by this share of a beat
    strum_ms: float = 0.0  # time between two notes of a chord, from the lowest note up
    level_spread: float = 0.0  # standard deviation of the random part of the loudness
    accents: tuple[float, float, float] = (1.0, 1.0, 1.0)  # pulse start, eighth, between
    shifts: dict[int, float] = field(default_factory=dict)  # drums: shift of each drum in ms
    backbeat_ms: float = 0.0  # drums: more shift for the snare on the backbeat
    ghost: float = 0.28  # drums: loudness of a ghost note relative to a normal stroke
    # A soloist and a drummer play fills a little early and louder.
    rush_ms: float = 0.0


EXACT = Feel()

# A drummer in the style: tight, a little before the beat, the snare a little behind.
# Spread of the reference recordings: about 10 ms for each drum, with the error of the
# measurement. Published: hi-hat 10 ms, kick 10 ms, snare 16 ms against a click.
DRUMS = Feel(
    late_ms=-2.0, spread_ms=5.5, drift_ms=3.0, level_spread=0.045,
    accents=(1.0, 0.79, 0.62), shifts={36: -2.0, 35: -2.0, 38: 3.0, 40: 4.0, 42: -1.0, 46: -1.0},
    backbeat_ms=5.0,
)  # fmt: skip
BASS = Feel(late_ms=4.0, spread_ms=7.0, drift_ms=3.0, level_spread=0.05)
GUITAR = Feel(late_ms=1.0, spread_ms=6.0, drift_ms=3.0, strum_ms=4.0, level_spread=0.05)
KEYS = Feel(late_ms=3.0, spread_ms=7.0, drift_ms=3.0, strum_ms=5.0, level_spread=0.06)
LEAD = Feel(late_ms=6.0, spread_ms=9.0, drift_ms=5.0, layback=0.05, level_spread=0.05)
SECTION = Feel(late_ms=5.0, spread_ms=8.0, drift_ms=4.0, level_spread=0.04)


@dataclass(frozen=True)
class Event:
    """One note for the sound engine. Times are in seconds from the start of the work."""

    note: PerfNote
    start: float
    seconds: float  # the time from the start of the note to the written end
    level: float
    level_end: float

    @property
    def midi(self) -> float:
        return self.note.midi


def _seed(*keys: object) -> int:
    return zlib.crc32(repr(keys).encode())


def _drift(player: str, seconds: np.ndarray, size_ms: float) -> np.ndarray:
    """Return a slow random curve in ms: it changes in 4 to 10 seconds."""
    if not size_ms or len(seconds) == 0:
        return np.zeros(len(seconds))
    random = np.random.default_rng(_seed(player, "drift"))
    span = float(seconds.max()) + 20.0
    out = np.zeros(len(seconds))
    for period in (4.0, 7.0, 13.0):
        knots = random.normal(0.0, 1.0, int(span / period) + 3)
        out += np.interp(seconds / period, np.arange(len(knots)), knots)
    return out * size_ms / np.sqrt(3.0)


def place(structure: Structure, position: Fraction) -> tuple[int, Fraction, Fraction]:
    """Return where a position is in its pulse.

    The result has: the kind of the place (0 = start of a pulse, 1 = on an
    eighth note or a larger value, 2 = between), the position in the bar,
    and the length of the pulse (quarter notes).
    """
    bar = structure.bar_at(position)
    inside = position - bar.start
    unit = Fraction(4, bar.denominator)
    groups = bar.grouping or (1,) * bar.numerator
    start = Fraction(0)
    pulse = unit
    for group in groups:
        pulse = group * unit
        if inside < start + pulse:
            break
        start += pulse
    offset = inside - start
    if offset == 0:
        return 0, inside, pulse
    if (offset / Fraction(1, 2)).denominator == 1:
        return 1, inside, pulse
    return 2, inside, pulse


def events(
    structure: Structure,
    notes: list[PerfNote],
    feel: Feel | list[tuple[Fraction, Feel]],
    *,
    drums: bool = False,
    backbeats: set[tuple[int, Fraction]] | None = None,
) -> list[Event]:
    """Change the performance notes of one player into events.

    `feel` is one feel for the full work, or a list of (position, feel):
    each feel is in effect from its position (quarter notes) to the next.
    `backbeats` are the places (bar number, position in the bar) of the
    backbeat, for the shift of the snare drum.
    """
    if not notes:
        return []
    plan = [(Fraction(0), feel)] if isinstance(feel, Feel) else sorted(feel, key=lambda p: p[0])
    player = notes[0].player
    starts = np.array([structure.seconds(note.start) for note in notes])
    widest = max(item.drift_ms for _position, item in plan)
    drift = _drift(player, starts, 1.0) if widest else np.zeros(len(notes))
    result: list[Event] = []
    chord_rank: dict[tuple[Fraction, int], int] = {}
    for index, note in enumerate(notes):
        current = plan[0][1]
        for position, item in plan:
            if position <= note.start:
                current = item
        random = np.random.default_rng(_seed(player, float(note.start), note.midi, note.voice))
        kind, inside, pulse = place(structure, note.start)
        quarter_seconds = 60.0 / structure.bpm_at(note.start)
        shift = current.late_ms + current.drift_ms * drift[index]
        if current.spread_ms:
            shift += float(np.clip(random.normal(0.0, current.spread_ms), -3 * current.spread_ms,
                                   3 * current.spread_ms))  # fmt: skip
        # Swing: a note on the second half of the swing unit comes late.
        if current.swing != 0.5:
            unit = current.swing_unit
            share = (note.start % unit) / unit
            if share == Fraction(1, 2):
                shift += (current.swing - 0.5) * float(unit) * quarter_seconds * 1000.0
        if current.layback and kind == 0:
            shift += current.layback * float(pulse) * quarter_seconds * 1000.0
        level, level_end = note.level, note.level_end
        if drums:
            shift += current.shifts.get(int(note.midi), 0.0)
            bar = structure.bar_at(note.start).number
            if backbeats and int(note.midi) == 38 and (bar, inside) in backbeats:
                shift += current.backbeat_ms
            if int(note.midi) == 40:
                level = level_end = level * current.ghost
            elif int(note.midi) in (42, 44, 51) and not note.accent:
                level = level_end = level * current.accents[kind]
        elif current.strum_ms and note.chord_size > 1:
            key = (note.start, note.voice)
            rank = chord_rank.get(key, 0)
            chord_rank[key] = rank + 1
            shift += rank * current.strum_ms * (0.7 + 0.6 * random.uniform())
        if current.level_spread:
            change = float(random.normal(0.0, current.level_spread))
            level = float(np.clip(level + change, 0.02, 1.0))
            level_end = float(np.clip(level_end + change, 0.02, 1.0))
        start = float(starts[index]) + shift / 1000.0
        end = structure.seconds(note.start + note.duration)
        result.append(Event(note, max(0.0, start), max(0.02, end - float(starts[index])), level,
                            level_end))  # fmt: skip
    result.sort(key=lambda event: event.start)
    return result


def tight(feel: Feel, share: float) -> Feel:
    """Return a feel with less random timing: `share` 1 = no change, 0 = exact."""
    return replace(
        feel,
        spread_ms=feel.spread_ms * share,
        drift_ms=feel.drift_ms * share,
        late_ms=feel.late_ms * share,
        layback=feel.layback * share,
    )
