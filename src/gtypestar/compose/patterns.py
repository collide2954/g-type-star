"""Rhythm patterns for the parts with pitch, and the changes of a drum groove.

The metres of the work have pulses of different lengths. A pattern has one
group of letters for each pulse of the bar, as in the drum patterns
(`notation/drums.py`):

- A letter starts a note. A table gives the pitch (or the chord) of each letter.
- `_` holds the note before it. `-` or `.` is a rest.
- A capital letter is a note with an accent.
- The number of letters in a group gives the division of the pulse.

    pitched("a__a-- ---b__ a_c_ ---a__ b_____", (3, 3, 2, 3, 3), {"a": "g,,", ...})

The class `Groove` holds a drum pattern as data. Its functions make the
small changes that a drummer makes from bar to bar: a ghost note more, an
open hi-hat, a kick drum on a different place, a fill at the end of a phrase.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ..notation import drums

REST = "-."
HOLD = "_"
VALUES = {
    Fraction(4): "1", Fraction(3): "2.", Fraction(2): "2", Fraction(3, 2): "4.",
    Fraction(1): "4", Fraction(3, 4): "8.", Fraction(1, 2): "8", Fraction(3, 8): "16.",
    Fraction(1, 4): "16", Fraction(1, 8): "32", Fraction(1, 16): "64",
}  # fmt: skip


def _split(steps: int, written: Fraction) -> list[int]:
    """Divide a number of steps into parts that each have a note value, the largest first."""
    parts = []
    rest = steps
    while rest > 0:
        for size in range(rest, 0, -1):
            if size * written in VALUES:
                parts.append(size)
                rest -= size
                break
    return parts


def _note(table: dict[str, str], letter: str) -> tuple[str, str]:
    """Return the pitch text and the marks of a letter."""
    if letter.lower() not in table:
        raise ValueError(f"the pattern has the letter {letter!r}, but the table has no such note")
    value = table[letter.lower()]
    if value.startswith("<"):
        end = value.index(">") + 1  # a chord: the marks come after the ">"
        pitch, marks = value[:end], value[end:].strip()
    else:
        pitch, _, marks = value.partition(" ")
    if letter.isupper():
        marks += "->"
    return pitch, marks


def pitched(
    pattern: str, pulses: tuple[int, ...] | list[int], table: dict[str, str], unit: int = 8
) -> str:
    """Change a pattern of one voice into music text for one bar.

    `table` gives the pitch of each letter in the music language, for
    example {"a": "g,,", "b": "<d' g' a'>"}. Marks can follow the pitch after
    a space: {"a": "g,, -."} is a staccato note.
    """
    groups = pattern.replace("|", " ").split()
    if len(groups) != len(pulses):
        raise ValueError(f"{len(groups)} groups for {len(pulses)} pulses: {pattern!r}")
    texts: list[str] = []
    sounding: tuple[str, str] | None = None  # the note that a hold continues
    for number, (group, length) in enumerate(zip(groups, pulses, strict=True)):
        pulse = Fraction(4 * length, unit)
        count = len(group)
        written, normal = drums.division(pulse, count)
        parts: list[str] = []
        index = 0
        while index < count:
            letter = group[index]
            run = 1
            if letter in REST:
                while index + run < count and group[index + run] in REST:
                    run += 1
                sounding = None
                for size in _split(run, written):
                    parts.append(f"r{VALUES[size * written]}")
            else:
                if letter == HOLD:
                    if sounding is None:
                        raise ValueError(f"a hold with no note before it: {pattern!r}")
                    pitch, marks = sounding[0], ""
                else:
                    pitch, marks = _note(table, letter)
                    sounding = (pitch, marks)
                while index + run < count and group[index + run] == HOLD:
                    run += 1
                # The note continues into the next pulse if that pulse starts with a hold.
                later = groups[number + 1] if number + 1 < len(groups) else ""
                tied_out = index + run == count and later.startswith(HOLD)
                sizes = _split(run, written)
                for place, size in enumerate(sizes):
                    tie = "~" if place + 1 < len(sizes) or tied_out else ""
                    first = place == 0 and letter != HOLD
                    parts.append(f"{pitch}{VALUES[size * written]}{marks if first else ''}{tie}")
            index += run
        body = " ".join(parts)
        texts.append(f"\\tuplet {count}/{normal} {{ {body} }}" if normal else body)
    return " ".join(texts)


class Groove:
    """A drum pattern for one bar, as data that code can change.

    `rows` gives the groups of each row: {"hh": ["x-x-x-", ...], "sn": [...], "bd": [...]}.
    """

    def __init__(self, pattern: str, pulses: tuple[int, ...]) -> None:
        self.pulses = tuple(pulses)
        self.rows: dict[str, list[str]] = {}
        for line in pattern.strip().splitlines():
            words = line.replace("|", " ").split()
            if not words:
                continue
            if len(words) - 1 != len(self.pulses):
                raise ValueError(
                    f"row {words[0]}: {len(words) - 1} groups for {len(pulses)} pulses"
                )
            self.rows[words[0]] = words[1:]

    def copy(self) -> Groove:
        new = Groove("", self.pulses)
        new.rows = {name: list(groups) for name, groups in self.rows.items()}
        return new

    def text(self) -> str:
        """Return the pattern as music text for one bar."""
        lines = [f"{name} {' '.join(groups)}" for name, groups in self.rows.items()]
        return drums.steps("\n".join(lines), self.pulses)

    def _row(self, name: str) -> list[str]:
        if name not in self.rows:
            sizes = [len(group) for group in next(iter(self.rows.values()))]
            self.rows[name] = ["-" * size for size in sizes]
        return self.rows[name]

    def put(self, name: str, pulse: int, step: int, letter: str) -> Groove:
        """Put a letter at a step of a pulse (the first pulse and the first step are 0)."""
        row = self._row(name)
        group = row[pulse]
        if step < len(group):
            row[pulse] = group[:step] + letter + group[step + 1 :]
        return self

    def set(self, name: str, pulse: int, group: str) -> Groove:
        """Give one pulse of a row a new group of letters."""
        self._row(name)[pulse] = group
        return self

    def clear(self, pulse: int, names: tuple[str, ...] | None = None) -> Groove:
        """Remove all strokes of one pulse (for a fill or a rest)."""
        for name, row in self.rows.items():
            if names is None or name in names:
                row[pulse] = "-" * len(row[pulse])
        return self

    def fill(self, start: int, rows: dict[str, list[str]]) -> Groove:
        """Put a fill into the pulses from `start`: the rows of the fill replace all strokes."""
        size = len(next(iter(rows.values())))
        for pulse in range(start, start + size):
            for row in self.rows.values():
                row[pulse] = "-" * len(row[pulse])
        for name, groups in rows.items():
            row = self._row(name)
            for offset, group in enumerate(groups):
                row[start + offset] = group
        return self

    def empty(self, name: str, pulse: int, step: int) -> bool:
        group = self.rows.get(name, [""] * len(self.pulses))[pulse]
        return step >= len(group) or group[step] in REST

    def vary(self, random: np.random.Generator, amount: float = 1.0) -> Groove:
        """Make the small changes of a drummer. Return a new groove.

        Each change has a probability. `amount` makes all changes more or
        less frequent (0 = no change). The rules:

        - A ghost note on an empty step of the snare row that is not next to a stroke.
        - A stroke of the kick drum moves by one step, or a soft kick comes before a stroke.
        - A closed hi-hat stroke before the end of a pulse opens.
        - One hi-hat stroke is left out (the hand goes to a different drum).
        """
        new = self.copy()
        pulses = range(len(self.pulses))
        snare = new.rows.get("sn")
        if snare is not None:
            for pulse in pulses:
                for step in range(len(snare[pulse])):
                    near = [
                        not new.empty("sn", pulse, other)
                        for other in (step - 1, step + 1)
                        if 0 <= other < len(snare[pulse])
                    ]
                    if new.empty("sn", pulse, step) and not any(near) and step % 2 == 1:
                        if random.uniform() < 0.07 * amount:
                            new.put("sn", pulse, step, "g")
                    elif snare[pulse][step] == "g" and random.uniform() < 0.25 * amount:
                        new.put("sn", pulse, step, "-")
        kick = new.rows.get("bd")
        if kick is not None:
            for pulse in pulses:
                for step in range(len(kick[pulse])):
                    if kick[pulse][step] != "x" or (pulse == 0 and step == 0):
                        continue
                    chance = random.uniform()
                    target = step + (1 if random.uniform() < 0.5 else -1)
                    free = 0 <= target < len(kick[pulse]) and new.empty("bd", pulse, target)
                    if chance < 0.06 * amount and free and new.empty("sn", pulse, target):
                        new.put("bd", pulse, step, "-").put("bd", pulse, target, "x")
                    elif chance < 0.12 * amount and free and target < step:
                        new.put("bd", pulse, target, "x")
        hat = new.rows.get("hh")
        if hat is not None:
            for pulse in pulses:
                group = hat[pulse]
                last = len(group) - 2 if len(group) >= 4 else -1
                if last >= 0 and group[last] == "x" and random.uniform() < 0.08 * amount:
                    new.put("hh", pulse, last, "o")
                for step in range(1, len(group)):
                    if group[step] == "x" and random.uniform() < 0.03 * amount:
                        new.put("hh", pulse, step, "-")
        return new


def join(bars: list[str]) -> str:
    """Return the bars as music text with a bar check after each bar."""
    return " | ".join(bars) + " |"
