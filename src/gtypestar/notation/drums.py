"""The drums: the note of each drum, its name in the score, and a short pattern language.

A drum has no pitch. In the music text, each drum is a note with a fixed
MIDI number. The numbers are those of the General MIDI drum map: thus the
MIDI file of the work plays the correct drums in other programs.

The composer does not write these notes by hand. The function `steps`
changes a pattern of letters into music text: one row for each drum, one
group of letters for each pulse of the bar.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .pitch import from_midi


@dataclass(frozen=True)
class Drum:
    """One drum or one way to hit it."""

    midi: int
    name: str
    lilypond: str  # the name in the drum mode of LilyPond
    voice: int  # 0 = the hands (stems up), 1 = the feet (stems down)
    ghost: bool = False  # a very soft stroke; the score shows it in brackets
    text: str = ""  # a text above the note in the score, for the sounds with no usual sign


KIT = [
    Drum(36, "kick", "bd", 1),
    Drum(35, "kick (left foot)", "bda", 1),
    Drum(44, "hi-hat pedal", "hhp", 1),
    Drum(38, "snare", "sn", 0),
    Drum(40, "snare ghost", "sn", 0, ghost=True),
    Drum(37, "cross-stick", "ss", 0),
    Drum(42, "hi-hat closed", "hh", 0),
    Drum(46, "hi-hat open", "hho", 0),
    Drum(51, "ride", "cymr", 0),
    Drum(53, "ride bell", "rb", 0),
    Drum(49, "crash", "cymc", 0),
    Drum(57, "crash 2", "cymca", 0),
    Drum(52, "stack", "cymch", 0),
    Drum(55, "splash", "cyms", 0),
    Drum(50, "tom high", "tomh", 0),
    Drum(47, "tom middle", "tommh", 0),
    Drum(43, "tom floor", "tomfh", 0),
    Drum(41, "tom floor low", "tomfl", 0),
]
BY_MIDI = {drum.midi: drum for drum in KIT}
BY_NAME = {drum.name: drum for drum in KIT}

# The drum machine: electronic sounds that code makes.
MACHINE = [
    Drum(36, "machine kick", "bd", 1),
    Drum(38, "machine snare", "sn", 0),
    Drum(39, "clap", "hc", 0),
    Drum(37, "rim", "ss", 0),
    Drum(42, "machine hat", "hh", 0),
    Drum(46, "machine hat open", "hho", 0),
    Drum(45, "machine tom", "tomml", 0),
    Drum(56, "zap", "cb", 0, text="zap"),
    Drum(27, "sub drop", "bda", 1, text="sub drop"),
    Drum(28, "riser", "cuim", 0, text="noise rises"),
    Drum(29, "downlifter", "cuio", 0, text="noise falls"),
    Drum(30, "impact", "tamb", 0, text="impact"),
    Drum(31, "noise burst", "mar", 0, text="noise"),
    # The heavy sounds of the dubstep passage.
    Drum(35, "hard kick", "toml", 1),
    Drum(40, "heavy snare", "sne", 0),
    Drum(41, "roll snare", "sna", 0),
    Drum(32, "reverse cymbal", "cymr", 0, text="reverse cymbal"),
]
MACHINE_BY_MIDI = {drum.midi: drum for drum in MACHINE}

# The rows of a pattern: the name of the row, and the drum of each letter.
# A capital letter is a stroke with an accent.
ROWS: dict[str, dict[str, int]] = {
    "hh": {"x": 42, "o": 46, "p": 44},  # closed, open, pedal
    "rd": {"x": 51, "b": 53},  # ride, bell
    "cy": {"c": 49, "d": 57, "k": 52, "s": 55},  # crash, crash 2, stack, splash
    "sn": {"o": 38, "g": 40, "x": 37},  # stroke, ghost note, cross-stick
    "tm": {"h": 50, "m": 47, "f": 43, "l": 41},  # high, middle, floor, low floor
    "bd": {"x": 36, "y": 35},  # right foot, left foot
    # The drum machine.
    "mk": {"x": 36, "d": 27, "h": 35},  # kick, sub drop, hard kick
    "ms": {"o": 38, "c": 39, "x": 37, "s": 40, "r": 41},  # snare, clap, rim, heavy, roll
    "mh": {"x": 42, "o": 46},
    "mt": {"t": 45, "z": 56, "n": 31},  # tom, zap, noise burst
}
FEET_ROWS = {"bd", "mk"}
CYMBAL_ROWS = {"hh", "rd", "cy", "mh"}
REST = "-."


def _note_name(midi: int) -> str:
    return from_midi(midi).name


def _length_text(steps: int, unit: Fraction) -> list[str] | None:
    """Return the note value for a number of steps, or None if no single value fits."""
    names = {
        Fraction(4): "1", Fraction(3): "2.", Fraction(2): "2", Fraction(3, 2): "4.",
        Fraction(1): "4", Fraction(3, 4): "8.", Fraction(1, 2): "8", Fraction(3, 8): "16.",
        Fraction(1, 4): "16", Fraction(1, 8): "32", Fraction(1, 16): "64",
    }  # fmt: skip
    value = names.get(steps * unit)
    return [value] if value else None


POWERS = [Fraction(4), Fraction(2), Fraction(1), Fraction(1, 2), Fraction(1, 4), Fraction(1, 8),
          Fraction(1, 16), Fraction(1, 32)]  # fmt: skip


def division(pulse: Fraction, count: int) -> tuple[Fraction, int]:
    """Return how to write `count` equal notes in a pulse: the note value and the tuplet.

    The second value is 0 for a plain division. For a tuplet it is the
    number of plain notes that the `count` notes replace: five notes in a
    pulse of three eighth notes are a tuplet of 5 in the time of 3.
    """
    step = pulse / count
    if step in POWERS or step * Fraction(2, 3) in POWERS:
        return step, 0  # a plain note value, or a plain note value with a dot
    for value in POWERS:
        normal = pulse / value
        if normal.denominator == 1 and count / 2 < normal < count:
            return value, int(normal)
    raise ValueError(f"no way to write {count} equal notes in {pulse} quarter notes")


def _pulse_text(columns: list[list[tuple[int, bool]]], pulse: Fraction) -> str:
    """Write one pulse of one voice. Each column has the strokes of one step."""
    count = len(columns)
    written, normal = division(pulse, count)
    parts: list[str] = []
    index = 0
    while index < count:
        strokes = columns[index]
        run = 1
        # A stroke or a rest takes the empty steps after it, if a note value has that
        # length: in a group of 11 notes, the strokes 2 + 2 + 3 + 2 + 2 are four eighth
        # notes and one eighth note with a dot.
        while index + run < count and not columns[index + run]:
            if _length_text(run + 1, written) is None:
                break
            run += 1
        value = _length_text(run, written)
        assert value is not None
        if strokes:
            names = " ".join(_note_name(midi) for midi, _accent in strokes)
            text = f"<{names}>" if len(strokes) > 1 else names
            accent = "->" if any(accent for _midi, accent in strokes) else ""
            parts.append(f"{text}{value[0]}{accent}")
        else:
            parts.append(f"r{value[0]}")
        index += run
    body = " ".join(parts)
    return f"\\tuplet {count}/{normal} {{ {body} }}" if normal else body


def steps(pattern: str, pulses: tuple[int, ...] | list[int], unit: int = 8) -> str:
    """Change a drum pattern into music text for one bar.

    `pulses` are the lengths of the pulses of the bar, in notes of the value
    `unit` (8 = eighth notes): for example (3, 3, 2, 3, 3) for a bar of 7/4.

    The pattern has one row for each drum. A row starts with its name and
    has one group of letters for each pulse. The number of letters in a
    group gives the division of that pulse: six letters in a pulse of three
    eighth notes are sixteenth notes; five letters are a quintuplet.

        hh  x-x-x- x-x-x- x-x- x-x-x- x-x-o-
        sn  ------ o--g-- ---- o----g ------
        bd  x--x-- ------ x-x- ------ x-----

    Letters: see `ROWS`. A capital letter is an accent. `-` or `.` is a rest.
    A `|` between groups is ignored. The result has two voices: hands and feet.
    """
    rows: dict[str, list[str]] = {}
    for line in pattern.strip().splitlines():
        words = line.replace("|", " ").split()
        if not words:
            continue
        name, groups = words[0], words[1:]
        if name not in ROWS:
            raise ValueError(f"unknown drum row {name!r}")
        if len(groups) != len(pulses):
            raise ValueError(f"row {name}: {len(groups)} groups for {len(pulses)} pulses")
        rows[name] = groups
    # The voices of the bar. Usually: the hands, and the feet. The rows of one voice
    # must agree in each pulse: the division of one row is a multiple of the others.
    # If the cymbals and the drums of the hands do not agree (11 cymbal notes against 4
    # snare notes), the cymbals get their own voice and the snare drum goes to the feet.
    cymbals = [name for name in rows if name in CYMBAL_ROWS]
    hands = [name for name in rows if name not in CYMBAL_ROWS and name not in FEET_ROWS]
    feet = [name for name in rows if name in FEET_ROWS]
    if _agree(rows, cymbals + hands):
        layout = [cymbals + hands, feet]
    elif _agree(rows, hands + feet):
        layout = [cymbals, hands + feet]
    else:
        layout = [cymbals, hands, feet]
    texts = [_voice_text(rows, names, pulses, unit) for names in layout]
    used = [text for text in texts if text is not None]
    if not used:
        return _voice_text(rows, list(rows), pulses, unit, keep_empty=True) or ""
    if len(used) == 1:
        return used[0]
    return "<< " + " \\\\ ".join(f"{{ {text} }}" for text in used) + " >>"


def _sizes(rows: dict[str, list[str]], names: list[str], number: int) -> set[int]:
    """Return the divisions of one pulse in the rows that have a stroke there."""
    return {
        len(rows[name][number])
        for name in names
        if any(letter not in REST for letter in rows[name][number])
    }


def _agree(rows: dict[str, list[str]], names: list[str]) -> bool:
    """Return True if the rows fit in one voice: in each pulse one grid has all strokes."""
    if not names:
        return True
    for number in range(len(rows[names[0]])):
        sizes = _sizes(rows, names, number)
        if sizes and any(max(sizes) % size for size in sizes):
            return False
    return True


def _voice_text(
    rows: dict[str, list[str]], names: list[str], pulses, unit: int, keep_empty: bool = False
) -> str | None:
    """Return the music text of one voice for one bar, or None if the voice has no stroke."""
    texts = []
    used = False
    for number, length in enumerate(pulses):
        pulse = Fraction(4 * length, unit)
        count = 1
        # A row with no stroke in this pulse does not change the grid of the pulse.
        for size in _sizes(rows, names, number):
            count = count * size // _gcd(count, size)
        columns: list[list[tuple[int, bool]]] = [[] for _ in range(count)]
        for name in names:
            group = rows[name][number]
            for place, letter in enumerate(group):
                if letter in REST:
                    continue
                midi = ROWS[name].get(letter.lower())
                if midi is None:
                    raise ValueError(f"row {name}: unknown letter {letter!r}")
                columns[place * count // len(group)].append((midi, letter.isupper()))
                used = True
        texts.append(_pulse_text(columns, pulse))
    return " ".join(texts) if used or keep_empty else None


def _gcd(first: int, second: int) -> int:
    while second:
        first, second = second, first % second
    return first
