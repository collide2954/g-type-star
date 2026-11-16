"""Chord symbols and voicings.

The composer writes the harmony of a passage as chord symbols, for example
`Gmaj9#11` or `Ebmaj7#11/G`. The functions of this module give the notes of
a symbol and make voicings for the keyboard, the guitar, the horns, and the
strings: close, rootless, in fourths, or spread. A voicing moves as little
as possible from the voicing before it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..notation.pitch import from_midi

LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SYMBOL = re.compile(r"^([A-G])([#b]?)([^/]*)(?:/([A-G])([#b]?))?$")

# The notes of each chord quality, in semitones above the root. The sequence is
# the importance of the notes: a voicing with few notes takes the first ones.
QUALITIES: dict[str, tuple[int, ...]] = {
    "": (4, 7),
    "m": (3, 7),
    "5": (7,),
    "sus": (5, 7),
    "sus2": (2, 7),
    "6": (4, 9, 7),
    "m6": (3, 9, 7),
    "69": (4, 9, 14, 7),
    "m69": (3, 9, 14, 7),
    "add9": (4, 14, 7),
    "madd9": (3, 14, 7),
    "maj7": (4, 11, 7),
    "maj9": (4, 11, 14, 7),
    "maj7#11": (4, 11, 18, 7),
    "maj9#11": (4, 11, 14, 18, 7),
    "maj13": (4, 11, 14, 21, 7),
    "maj13#11": (4, 11, 14, 18, 21),
    "m7": (3, 10, 7),
    "m9": (3, 10, 14, 7),
    "m11": (3, 10, 17, 14, 7),
    "m13": (3, 10, 14, 21, 7),
    "m7b5": (3, 10, 6),
    "mmaj7": (3, 11, 7),
    "mmaj9": (3, 11, 14, 7),
    "7": (4, 10, 7),
    "9": (4, 10, 14, 7),
    "13": (4, 10, 21, 14),
    "7sus": (5, 10, 7),
    "9sus": (5, 10, 14, 7),
    "13sus": (5, 10, 21, 14),
    "7#9": (4, 10, 15, 7),
    "7b9": (4, 10, 13, 7),
    "7#11": (4, 10, 18, 14),
    "7alt": (4, 10, 15, 20),
    "13b9": (4, 10, 21, 13),
    "7b13": (4, 10, 20, 14),
    "dim7": (3, 6, 9),
    "aug": (4, 8),
    "q": (5, 10, 15),  # three fourths above the root
    "q4": (5, 10, 15, 20),
}


@dataclass(frozen=True)
class Chord:
    """A chord: the root, the notes above the root, and the bass note (pitch classes)."""

    symbol: str
    root: int
    intervals: tuple[int, ...]
    bass: int
    letter: int = 0  # the letter of the root: 0 = C, 1 = D, ... 6 = B

    @property
    def classes(self) -> tuple[int, ...]:
        """The pitch classes of the chord, the most important first, the root last."""
        return tuple((self.root + interval) % 12 for interval in self.intervals) + (self.root,)


def parse(symbol: str) -> Chord:
    """Read a chord symbol, for example "Ebmaj7#11/G"."""
    match = SYMBOL.match(symbol)
    if not match:
        raise ValueError(f"cannot read the chord symbol {symbol!r}")
    letter, accidental, quality, bass_letter, bass_accidental = match.groups()
    if quality not in QUALITIES:
        raise ValueError(f"unknown chord quality {quality!r} in {symbol!r}")
    root = (LETTERS[letter] + {"#": 1, "b": -1, "": 0}[accidental]) % 12
    bass = root
    if bass_letter:
        bass = (LETTERS[bass_letter] + {"#": 1, "b": -1, "": 0}[bass_accidental or ""]) % 12
    return Chord(symbol, root, QUALITIES[quality], bass, "CDEFGAB".index(letter))


def _candidates(chord: Chord, count: int, low: int, high: int, rootless: bool) -> list[tuple]:
    """Return all voicings of `count` notes between `low` and `high` (MIDI numbers)."""
    classes = list(chord.classes[:-1] if rootless else chord.classes)
    if not rootless:
        classes = [classes[-1], *classes[:-1]]  # the root, then the notes by importance
    classes = list(dict.fromkeys(classes))[:count] if len(classes) > count else classes
    wanted = set(classes)
    result: list[tuple[int, ...]] = []

    def extend(notes: tuple[int, ...], rest: frozenset[int]) -> None:
        if not rest:
            result.append(notes)
            return
        start = notes[-1] + 1 if notes else low
        for midi in range(start, high + 1):
            if midi % 12 in rest:
                if notes and midi - notes[-1] > 10:
                    break
                extend((*notes, midi), rest - {midi % 12})

    extend((), frozenset(wanted))
    if not rootless:
        rooted = [notes for notes in result if notes[0] % 12 == chord.bass]
        result = rooted or result
    return result


def voice(
    symbol: str | Chord,
    count: int = 4,
    *,
    low: int = 52,
    high: int = 76,
    before: tuple[int, ...] | None = None,
    top: int | None = None,
    rootless: bool = True,
    spread: bool = False,
) -> tuple[int, ...]:
    """Return a voicing of a chord as MIDI numbers, from the lowest note up.

    `before` is the voicing before this one: the new voicing is the nearest
    one. `top` asks for a given highest note (a melody note). `rootless`
    leaves the root to the bass player. `spread` prefers wide voicings
    (for strings and pads); if not, close voicings with no semitone at the
    top are preferred.
    """
    chord = parse(symbol) if isinstance(symbol, str) else symbol
    options = _candidates(chord, count, low, high, rootless)
    if not options:
        options = _candidates(chord, min(count, 3), low - 5, high + 5, rootless)
    if not options:
        raise ValueError(f"no voicing for {chord.symbol} between {low} and {high}")
    centre = (low + high) / 2.0

    def cost(notes: tuple[int, ...]) -> float:
        value = 0.0
        if before:
            pairs = zip(sorted(before)[-len(notes) :], notes[-len(before) :], strict=False)
            value += sum(abs(a - b) for a, b in pairs) * 1.0
        else:
            value += abs(sum(notes) / len(notes) - centre) * 0.6
        if top is not None:
            value += 40.0 if notes[-1] % 12 != top % 12 else abs(notes[-1] - top) * 2.0
        gaps = [b - a for a, b in zip(notes, notes[1:], strict=False)]
        if gaps:
            value += 6.0 if gaps[-1] == 1 else 0.0  # no semitone under the highest note
            value += 2.5 * sum(1 for gap in gaps if gap == 1)
            width = notes[-1] - notes[0]
            value += 0.25 * abs(width - 19) if spread else 0.35 * abs(width - 10)
            if notes[0] < 48 and gaps[0] < 5:
                value += 5.0  # low notes that are near together sound unclear
        return value

    return min(options, key=cost)


# The scale degree (0 = the root) of each chord note, from its distance to the root.
DEGREES = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6,
           13: 1, 14: 1, 15: 1, 17: 3, 18: 3, 20: 5, 21: 5}  # fmt: skip
NATURAL = (0, 2, 4, 5, 7, 9, 11)
SUFFIX = {-2: "eses", -1: "es", 0: "", 1: "is", 2: "isis"}


def names(notes: tuple[int, ...] | list[int], chord: str | Chord | None = None) -> str:
    """Return a voicing as the pitch names of the music language: "<g b d' fis'>".

    With a chord, each note gets the spelling of its place in the chord: the
    sharp eleventh of G is C-sharp, not D-flat. With no chord, flats are used.
    """
    spelled = parse(chord) if isinstance(chord, str) else chord
    words = []
    for midi in notes:
        word = from_midi(midi).name
        if spelled is not None:
            distance = (midi - spelled.root) % 12
            options = [
                interval for interval in (0, *spelled.intervals) if interval % 12 == distance
            ]
            if options:
                letter = (spelled.letter + DEGREES[options[0]]) % 7
                alter = (midi - NATURAL[letter] + 6) % 12 - 6
                if alter in SUFFIX:
                    octave = (midi - NATURAL[letter] - alter) // 12 - 1
                    marks = "'" * (octave - 3) if octave >= 3 else "," * (3 - octave)
                    name = "cdefgab"[letter] + SUFFIX[alter]
                    name = {"ees": "es", "aes": "as", "eeses": "eses", "aeses": "ases"}.get(
                        name, name
                    )
                    word = name + marks
        words.append(word)
    text = " ".join(words)
    return f"<{text}>" if len(notes) > 1 else text


def progression(symbols: list[str], count: int = 4, **options) -> list[tuple[int, ...]]:
    """Return a voicing for each chord of a progression, each near the voicing before it."""
    result: list[tuple[int, ...]] = []
    before = None
    for symbol in symbols:
        before = voice(symbol, count, before=before, **options)
        result.append(before)
    return result
