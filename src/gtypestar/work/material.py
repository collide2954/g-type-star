"""The material that all parts of the work share.

The clave
    The main metre has seven quarter notes in a bar. It is written as 14/8,
    with five pulses: long, long, short, long, long (3 + 3 + 2 + 3 + 3 eighth
    notes). The snare drum is on the second and on the fifth pulse: thus the
    bar sounds as a bar of four beats with a short extra beat in its middle.
    The model is the track "Cool 7" of Sungazer, which has the short pulse at
    the end (3 + 3 + 3 + 3 + 2). See research/tables/rhythm.csv.

The motto
    Four notes: G, C, D, E (a fourth up, then two steps). The fourth and the
    fifth above the root are the first two intervals of the spectrum of
    hydrogen (see design/pitch.toml).

The tempos
    175, 140, and 116.67 quarter notes in a minute: the ratios 15 : 12 : 10.
"""

from __future__ import annotations

import numpy as np

from ..compose import chords, patterns, tools
from ..compose.patterns import Groove
from ..notation.work import Section, Work

CLAVE = (3, 3, 2, 3, 3)  # eighth notes in each pulse of the main metre
METRE = (14, 8, CLAVE)
STEPS = (6, 6, 4, 6, 6)  # sixteenth notes in each pulse
FAST = 175.0  # quarter notes in a minute: the main tempo
FLASH = 140.0  # the tempo of the helium flash: 4/5 of the main tempo
GIANT = 350.0 / 3.0  # the tempo of the red giant: the long pulse becomes the beat
REST_BAR = "R1*14/8"
SEED = 2026


def random(*keys: object) -> np.random.Generator:
    """Return a random source for one passage. The same keys give the same values."""
    import zlib

    return np.random.default_rng(zlib.crc32(repr((SEED, *keys)).encode()))


class Bars:
    """Write the music of a section bar by bar.

    Each player gets a list with the music of each bar, or one text for all
    bars. A player with no music gets rests.
    """

    def __init__(self, work: Work, count: int, metre: tuple = METRE) -> None:
        self.work = work
        self.count = count
        self.metre = metre
        self.section: Section = work.section(count, *metre)
        self.first = self.section.first_bar

    def bar(self, number: int) -> int:
        """Return the bar number in the work of a bar of this section (1 = the first bar)."""
        return self.section.bar(number)

    @property
    def rest(self) -> str:
        return f"R1*{self.metre[0]}/{self.metre[1]}"

    def set(self, player: str, bars: list[str | None] | str, marks: str = "", prefix: str = ""):
        """Give the music of one player. `marks` go on the first note; `prefix` comes first."""
        if isinstance(bars, list):
            if len(bars) != self.count:
                raise ValueError(f"{player}: {len(bars)} bars for a section of {self.count} bars")
            text = patterns.join([bar if bar else self.rest for bar in bars])
        else:
            text = bars
        if marks:
            text = tools.first(text, marks, note=True)
        if prefix:
            text = f"{prefix} {text}"
        self.section.write(player, text)

    def same(self, players: str, bars: list[str | None] | str, marks: str = "") -> None:
        """Give the same music to some players: "tsax:-1 gtr lead" (a number moves octaves)."""
        text = (
            patterns.join([b if b else self.rest for b in bars]) if isinstance(bars, list) else bars
        )
        tools.put(self.section, players, text, marks)

    def close(self) -> None:
        self.section.close()


# ----------------------------------------------------------------------------
# Harmony
# ----------------------------------------------------------------------------

# The loop of the main sequence: roots that go down by thirds, then a 2-5 to G.
# The melody stays in the scale of G major; the chords under it change colour.
LOOP_A = ["Gmaj9", "Ebmaj7#11", "Cmaj9#11", "Am11"]
TURN_A = "D13sus"  # on the last two pulses of the fourth bar
# The loop of the bridge: the flat side, with B-flat and F held as pedal notes.
LOOP_B = ["Ebmaj9", "Bbadd9/D", "Cm11", "F9sus"]

BASS_LOW, BASS_HIGH = 27, 38  # the root of a bass figure is between E-flat 1 and D2


def bass_table(symbol: str, octave: int = 0) -> dict[str, str]:
    """Return the notes of a bass figure for one chord.

    a = root, b = root one octave higher, c = fifth, d = seventh (below the
    high root), e = third, f = fourth, g = ninth, h = the tone below the
    root, i = the semitone below the root, x = a note with no pitch.
    """
    chord = chords.parse(symbol)
    root = chord.bass
    while root < BASS_LOW:
        root += 12
    while root > BASS_HIGH:
        root -= 12
    root += 12 * octave
    third = 3 if 3 in chord.intervals else 4
    if 4 not in chord.intervals and 3 not in chord.intervals and 5 in chord.intervals:
        third = 5  # a chord with a fourth in place of the third ("D13sus")
    seventh = 11 if 11 in chord.intervals else 10
    names = {
        "a": root, "b": root + 12, "c": root + 7, "d": root + seventh, "e": root + third,
        "f": root + 5, "g": root + 14, "h": root - 2, "i": root - 1,
    }  # fmt: skip
    if chord.bass != chord.root:
        # A chord above a different bass note ("Bbadd9/D"): the fifth, the seventh, the
        # third, the fourth and the ninth are notes of the chord, in the octave above
        # the bass note.
        base = root + (chord.root - chord.bass) % 12
        for letter, interval in (("c", 7), ("d", seventh), ("e", third), ("f", 5), ("g", 14)):
            note = base + interval
            while note > root + 12:
                note -= 12
            names[letter] = note
    flats = chord.symbol[1:2] == "b" or chord.symbol[0] in "FC" or third == 3
    table = {
        letter: chords.from_midi(midi, prefer_sharps=not flats).name
        for letter, midi in names.items()
    }
    table["x"] = table["a"] + " -+"
    return table


def comp(symbol: str, pattern: str, pulses: tuple = CLAVE, **options) -> tuple[str, tuple]:
    """Return one bar of chords in a rhythm pattern, and the voicing.

    The letter `a` of the pattern is the voicing of the chord.
    """
    voicing = chords.voice(symbol, options.pop("count", 4), **options)
    text = patterns.pitched(pattern, pulses, {"a": chords.names(voicing, symbol)})
    return text, voicing


# ----------------------------------------------------------------------------
# Drum grooves of the main metre
# ----------------------------------------------------------------------------

# The groove of the main sequence. Kick on the first, third, and fourth pulse; snare
# on the second and the fifth pulse; hi-hat in eighth notes; ghost notes between.
MAIN = Groove(
    """
    hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ------ o--g-- ---g ------ o----g
    bd  x----x ------ x--- x--x-- ------
    """,
    CLAVE,
)
# The same groove with the hi-hat open between the beats ("barks"), for the loud passages.
MAIN_OPEN = Groove(
    """
    hh  x-x-o- x-x-x- x-o- x-x-o- x-x-x-
    sn  ---g-- o--g-- ---g ---g-- o--g--
    bd  x--x-x ------ x-x- x--x-- ---x--
    """,
    CLAVE,
)
# The ride cymbal in place of the hi-hat: a wider sound for the solos.
MAIN_RIDE = Groove(
    """
    rd  x-x-x- x-x-b- x-x- x-x-x- x-b-x-
    hh  ---p-- ---p-- --p- ---p-- ---p--
    sn  ------ o--g-- -g-g ---g-- o--g-g
    bd  x----x ------ x--- x--x-- ---x--
    """,
    CLAVE,
)
# A half-time form: one snare stroke in a bar, on the fourth pulse.
HALF = Groove(
    """
    hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ------ ---g-- ---- o----- ---g--
    bd  x----- -----x x--- ------ ---x--
    """,
    CLAVE,
)

# Fills: the rows that replace the last pulses of a bar.
FILLS: dict[str, dict[str, list[str]]] = {
    "snare 1": {"sn": ["o-oOgo"]},
    "snare toms 1": {"sn": ["o-o---"], "tm": ["---h-f"], "bd": ["-----x"]},
    "toms 1": {"tm": ["h-hm-f"], "bd": ["-x---x"]},
    "linear 1": {"sn": ["o--o--"], "tm": ["-h--f-"], "bd": ["--x--x"]},
    "snare 2": {"sn": ["o-gO-g", "O-oOoo"], "bd": ["------", "-x----"]},
    "toms 2": {"sn": ["o-o-g-", "------"], "tm": ["-----h", "-hm-ff"], "bd": ["------", "x--x--"]},
    "linear 2": {"sn": ["o--o-g", "o--o--"], "tm": ["-h----", "-m--f-"],
                 "bd": ["--x-x-", "--x--x"]},
    "stops 2": {"sn": ["O-----", "O--O--"], "bd": ["x-----", "x--x--"], "cy": ["k-----", "------"]},
    "kicks 2": {"sn": ["o-----", "o---oo"], "bd": ["-xx-xx", "-xx---"]},
}  # fmt: skip


def drum_bars(
    base: Groove, count: int, key: str, *, amount: float = 1.0, crash: tuple[int, ...] = (1,),
    fills: dict[int, str] | None = None, grooves: dict[int, Groove] | None = None,
) -> list[str]:  # fmt: skip
    """Return `count` bars of a groove. No two bars are fully the same.

    `crash` are the bars that start with a crash cymbal. `fills` gives the
    name of a fill for a bar number (the first bar is 1). `grooves` gives a
    different base groove for some bars.
    """
    source = random("drums", key)
    result = []
    seen: set[str] = set()
    for number in range(1, count + 1):
        groove = (grooves or {}).get(number, base)
        for _attempt in range(8):
            bar = groove.vary(source, amount)
            if number in crash:
                bar.put("cy", 0, 0, "c")
                bar.put("hh", 0, 0, "-")
                bar.put("rd", 0, 0, "-") if "rd" in bar.rows else None
            if fills and number in fills:
                rows = FILLS[fills[number]]
                size = len(next(iter(rows.values())))
                bar.fill(len(CLAVE) - size, rows)
            text = bar.text()
            if text not in seen:
                break
        seen.add(text)
        result.append(text)
    return result


# ----------------------------------------------------------------------------
# The theme
# ----------------------------------------------------------------------------

# The theme of the main sequence, at the sounding pitch of the tenor saxophone.
# Eight bars above the loop of four chords, two times. Few notes, long notes, all
# in the scale of G major except one F (the ninth of the chord of E-flat).
THEME = [
    r"r4. g'4.( c''4 d''4. ~ d''4.",  # the motto: G, C, D
    r"d''4. ~ d''4.) r4 a'4.( g'4.)",
    r"e''4.( ~ e''4. ~ e''4 d''4. b'4. ~",  # the fourth note of the motto: E
    r"b'4. a'4. ~ a'4) r4. r4.",
    r"r4. g'4.( c''4 d''4. e''4. ~",  # the motto in one bar: G, C, D, E
    r"e''4.) g''4.( ~ g''4 f''4. d''4.)",
    r"e''4.( ~ e''4. d''4 b'4. a'4. ~",
    r"a'4. g'4. ~ g'4 ~ g'4.) r4.",
]

# The second eight bars of the first statement: the same theme with a turn at the end
# of the second bar and a start before the bar line into the fifth bar.
THEME_SECOND = [
    r"r4. g'4.( c''4 d''4. ~ d''4.",
    r"d''4. ~ d''4.) r8 b'16( a' g'4. ~ g'4.)",
    r"e''4.( ~ e''4. ~ e''4 d''4. b'4. ~",
    r"b'4. a'4. ~ a'4) r4. r8 d'8( e'",
    r"g'4.) ~ g'4. c''4( d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 f''4. d''4.)",
    r"e''4.( ~ e''4. d''4 b'4. a'4. ~",
    r"a'4. g'4. ~ g'4 ~ g'4.) r4.",
]
# The second statement: runs of two sixteenth notes lead into the long notes, and the
# answer of the second bar goes up, not down.
THEME_HIGH = [
    r"r4 d'16( e' g'4. c''4 d''4. ~ d''4.",
    r"d''4.) r4. r4 a'8( b' d'' e''4. ~",
    r"e''4. ~ e''4.) g''4( fis''4. d''4. ~",
    r"d''4. b'4. a'4) r4. r4.",
    r"r4 d'16( e' g'4. c''4 d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 f''4. d''8 c'' d''",
    r"e''4. ~ e''4. d''4 b'4. a'4. ~",
    r"a'4. g'4.) r4 r4. r4.",
]
# The first line that all lead players play together (two bars of sixteenth notes), at
# the pitch of the tenor saxophone and the guitar. It is made from the scale of G with
# five notes, the motto (C, D, E, G), and notes that go round a goal note.
LINE_1 = [
    r"g16( a b d' e' g' fis' e' d' b a g c' d' e' g' a' g' e' d' cis' d' b d' e' fis' a' b'",
    r"c''16 b' a' g' fis' e' dis' e' g' fis' d' b c' e' d' b bes a g a b d' e' g' a' b' d'' e'')",
]
# The last eight bars of the second statement: six bars of the theme, then the line.
THEME_CLOSE = [
    r"r4. g'4.( c''4 d''4. ~ d''4.",
    r"d''4. ~ d''4.) r4 a'4.( g'4.)",
    r"e''4.( ~ e''4. ~ e''4 d''4. b'4. ~",
    r"b'4. a'4. ~ a'4) r4. r4.",
    r"r4. g'4.( c''4 d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 f''4. d''4.)",
    *LINE_1,
]


# The forms of the theme for the range of the tenor saxophone. Each time the theme comes
# back, the saxophone uses a different part of its range (sounding A-flat 2 to E5, and
# to C6 with the altissimo register): the contour of the theme changes, not only its octave.

# The first statement: the middle and low register (G3 to G4).
THEME_LOW = [
    r"r4. g4.( c'4 d'4. ~ d'4.",
    r"d'4. ~ d'4.) r4 a4.( g4.)",
    r"e'4.( ~ e'4. ~ e'4 d'4. b4. ~",
    r"b4. a4. ~ a4) r4. r4.",
    r"r4. g4.( c'4 d'4. e'4. ~",
    r"e'4.) g'4.( ~ g'4 f'4. d'4.)",
    r"e'4.( ~ e'4. d'4 b4. a4. ~",
    r"a4. g4. ~ g4 ~ g4.) r4.",
]
# Its second half: the theme starts low, breaks into the high octave at its highest
# phrase, and falls through two octaves to the low G.
THEME_LOW_RISE = [
    r"r4. g4.( c'4 d'4. ~ d'4.",
    r"d'4. ~ d'4.) r8 b16( a g4. ~ g4.)",
    r"e'4.( ~ e'4. ~ e'4 d'4. b4. ~",
    r"b4. a4. ~ a4) r4. r8 d'8( e'",
    r"g'4.) ~ g'4. c''4( d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 f''4. d''4.)",
    r"e''4.( ~ e''4. d''4 b'4. a'4.",
    r"g'4. e'4. d'4 b4. g4.)",
]
# The second statement: a start from the low D, a leap of an eleventh to the high C,
# the answer up to A5 and B-flat 5, and a fall to the low B at the end of the phrase.
THEME_WIDE = [
    r"r4 d16( e g4. c''4 d''4. ~ d''4.",
    r"d''4.) r4. r4 a'8( b' d'' e''4. ~",
    r"e''4. ~ e''4.) g''4( a''4. fis''4. ~",
    r"fis''4. d''4. b'4) r4. g8( d b,)",
    r"r4 d16( e g4. c''4 d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 a''4. bes''4.)",
    r"a''4.( ~ a''4. g''4 e''4. d''4. ~",
    r"d''4. b'4. a'4 g'4.) r4.",
]
# The last eight bars of the second statement: the answer of the second bar is one
# octave lower, the motto of the fifth bar is low, and a leap of a tenth goes to the
# highest phrase. Then the first line.
THEME_CLOSE_WIDE = [
    r"r4. g'4.( c''4 d''4. ~ d''4.",
    r"d''4. ~ d''4.) r4 a4.( g4.)",
    r"e''4.( ~ e''4. ~ e''4 d''4. b'4. ~",
    r"b'4. a'4. ~ a'4) r4. r4.",
    r"r4. g4.( c'4 d'4. e'4. ~",
    r"e'4.) g''4.( ~ g''4 f''4. d''4.)",
    *LINE_1,
]
# The quiet middle: the low register with much air in the tone. The second phrase is a
# fourth lower (the motto from D), and the last note is the low A, near the lowest note.
THEME_DEEP = [
    r"r4. g4.( c'4 d'4. ~ d'4.",
    r"d'4. ~ d'4.) r4 a4.( d4.)",
    r"e'4.( ~ e'4. ~ e'4 d'4. b4. ~",
    r"b4. a4. ~ a4) r4. r4.",
    r"r4. d4.( g4 a4. b4. ~",
    r"b4.) d'4.( ~ d'4 c'4. a4.)",
    r"b4.( ~ b4. a4 fis4. e4. ~",
    r"e4. d4. ~ d4 a,4. ~ a,4.)",
]
# The theme with the new division of the pulses: leaps between the registers. The motto
# is low, each answer is high, the highest note is B5, and the end falls two octaves.
THEME_LEAPS = [
    r"r4 d16( e g4. c'4 d'4. ~ d'4.",
    r"d'4.) r4. r4 a'8( b' d'' e''4. ~",
    r"e''4. ~ e''4.) g''4( fis''4. d''4. ~",
    r"d''4. b'4. a'4) r4. r4.",
    r"r4 d16( e g4. c'4 d'4. e'4. ~",
    r"e'4.) g''4.( ~ g''4 a''4. bes''4.)",
    r"b''4.( ~ b''4. a''4 g''4. e''4. ~",
    r"e''4. d''4. ~ d''4 b'4.) r4.",
    r"r4. g'4.( c''4 d''4. ~ d''4.",
    r"d''4. ~ d''4.) r8 b'16( a' g'4. ~ g'4.)",
    r"e''4.( ~ e''4. ~ e''4 d''4. b'4. ~",
    r"b'4. a'4. ~ a'4) r4. r8 d8( e",
    r"g4.) ~ g4. c''4( d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 f''4. d''4.)",
    r"e''4.( ~ e''4. d''4 b'4. a'4.",
    r"g'4. e'4. d'4 b4. g4.)",
]


# ----------------------------------------------------------------------------
# Sections of players: horns, strings, and the chords of the synthesizer
# ----------------------------------------------------------------------------

HORNS = ("bsax", "tbn", "asax", "tpt")  # from the lowest to the highest voice
STRINGS = ("vc", "va", "vn2", "vn1")


def horn_notes(symbol: str, top: int | None = None, before: tuple | None = None) -> tuple:
    """Return a voicing for the four horns: the root in the baritone, three notes above."""
    chord = chords.parse(symbol)
    root = chord.bass
    while root < 41:
        root += 12
    upper = chords.voice(chord, 3, low=55, high=80, top=top, before=before[1:] if before else None)
    return (root, *upper)


def string_notes(symbol: str, top: int | None = None, before: tuple | None = None) -> tuple:
    """Return a wide voicing for the four string groups."""
    return chords.voice(
        symbol, 4, low=45, high=86, spread=True, rootless=False, top=top, before=before
    )


def layer(
    symbol: str, pattern: str, players: tuple[str, ...], notes: tuple[int, ...],
    pulses: tuple = CLAVE,
) -> dict[str, str]:  # fmt: skip
    """Return one bar for each player of a section: one note of the chord, the same rhythm."""
    return {
        player: patterns.pitched(pattern, pulses, {"a": chords.names((midi,), symbol)})
        for player, midi in zip(players, notes, strict=True)
    }


def layers(
    symbols: list[str | None], patterns_: list[str], players: tuple[str, ...], kind: str,
    pulses: tuple = CLAVE, tops: list[int | None] | None = None,
) -> dict[str, list[str | None]]:  # fmt: skip
    """Return the bars of a section of players for a list of chords (None = a bar of rest).

    `kind` starts with "horns" or "strings". `tops` gives the highest note of some bars.
    """
    result: dict[str, list[str | None]] = {player: [] for player in players}
    before = None
    for number, symbol in enumerate(symbols):
        if symbol is None:
            for player in players:
                result[player].append(None)
            continue
        top = tops[number] if tops else None
        make = horn_notes if kind.startswith("horns") else string_notes
        before = make(symbol, top, before)
        # With fewer than four players, the lowest notes of the voicing are used.
        notes = before[: len(players)]
        pattern = patterns_[number % len(patterns_)]
        if kind.startswith("horns") and number % 2 == 1:
            # A wind player must breathe: each second bar of a held chord ends with a rest.
            groups = pattern.split()
            if set(groups[-1]) == {"_"}:
                pattern = " ".join([*groups[:-1], "-" * len(groups[-1])])
        bar = layer(symbol, pattern, players, notes, pulses)
        for player in players:
            result[player].append(bar[player])
    return result


def pad_bars(
    symbols: list[str | None], pattern: str = "a_____ ______ ____ ______ ______",
    pulses: tuple = CLAVE, low: int = 55, high: int = 79,
) -> list[str | None]:  # fmt: skip
    """Return the bars of the synthesizer chords (right hand) for a list of chords."""
    result: list[str | None] = []
    before = None
    for symbol in symbols:
        if symbol is None:
            result.append(None)
            continue
        before = chords.voice(symbol, 4, low=low, high=high, before=before)
        result.append(patterns.pitched(pattern, pulses, {"a": chords.names(before, symbol)}))
    return result


def roots(symbols: list[str | None], pattern: str, pulses: tuple = CLAVE, octave: int = 0):
    """Return bars with the root of each chord in a rhythm pattern (for the synthesizer bass)."""
    return [
        None if symbol is None else patterns.pitched(pattern, pulses, bass_table(symbol, octave))
        for symbol in symbols
    ]


# ----------------------------------------------------------------------------
# More lines
# ----------------------------------------------------------------------------

# The melody of the bridge: the motto upside down (G, D, C, B-flat), then a rise.
BRIDGE = [
    r"r4. g''4.( d''4 c''4. bes'4. ~",
    r"bes'4. ~ bes'4.) r4 f''4.( d''4.)",
    r"es''4.( ~ es''4. f''4 g''4. bes''4. ~",
    r"bes''4. a''4. ~ a''4) g''4.( f''4.)",
    r"r4. g''4.( d''4 c''4. bes'4.)",
    r"d''4.( f''4. ~ f''4 bes''4. ~ bes''4.)",
    r"c'''4.( ~ c'''4. bes''4 g''4. f''4. ~",
    r"f''4. es''4. d''4 c''4.) r4.",
]

# The solo of the tenor saxophone in the main sequence: 20 bars above the loop.
# It starts with the motto and with few notes, goes to lines of sixteenth notes,
# has its highest note in bar 14, and ends on a long G before the second line.
SAX_SOLO = [
    r"r4. r4. r4 d'8( e' g' a'4. ~",
    r"a'4.) r4. g'8( a' bes'4. d''4.)",
    r"r4 e''8( d''4. b'4 g'4. fis'4.)",
    r"e'4.( g'4. ~ g'4) r4. r8 a'16( b' c'' d''",
    r"e''4.) d''8( b' a' g'4) r8 b'16( d'' e''8 fis''8. e''16 d''8)",
    r"r8 d''8( bes' g'8 a' bes' d''4 f''4.) r4.",
    r"e''16( fis'' g'' fis'' e'' d'' b'8 d'' e'' g''4 ~ g''4. ~ g''8) r4",
    r"r4. e''8( d'' c'' a'4 g'8 a' c'' d''8. c''16 a'8)",
    r"g'16( a' b' d'' e'' fis'' g'' fis'' e'' d'' b' a' g'8 b' d''16 e'' fis'' a'' g''8) r4.",
    r"r8 g''16( f'' d'' bes' a'8 g'16 a' bes' d'' f''4 ~ f''8 d''16 bes' g'8) r4.",
    r"e'16( g' b' d'' e'' g'' fis'' e'' d'' b' g' e' fis'8 a' b'16 d'' e'' fis'' g''8 a''16 g'' "
    r"e''8 d''8)",
    r"c''8( e'' g'' a''4. g''8 e'' d''16 c'' a' g' a'8 c''16 d'' e'' g'' a''8)",
    r"g''8->( e'' d'' g''8-> e'' d'' g''8-> e'' g''8-> e'' d'' b'8 d'' e'')",
    r"g''8->( f'' d'' g''8-> f'' d'' g''8-> f'' a''4. ~ a''8) r4",
    r"g''16( fis'' e'' d'' b' a' g' a' b' d'' e'' fis'' g''8 e'' d''16 b' a' g' fis'8 "
    r"e'16 fis' g' a' b'8)",
    r"c''8( e'' a' c''16 d'' e'' g'' a''8 g''8 e'' d''4.) r4.",
    r"r4. d''8( e'' g'' a''4 g''8 e'' d'' b'4.)",
    r"r4. bes'8( d'' f'' g''4 f''8 d'' bes' a'4.)",
    r"r4. e''8( fis'' g'' a''4 g''8 fis'' e'' d''4.)",
    r"c''8( d'' e'' g''4. ~ g''4 ~ g''4. ~ g''8) r4",
]

# The second line for all lead players: four bars. The motto goes up through the scale
# (bar 1), a line falls through the scale of B-flat (bar 2), the triads of C and D take
# turns (bar 3), and notes go round the notes of the chord of A minor (bar 4).
LINE_2 = [
    r"g16( c' d' e' a d' e' fis' b e' fis' g' c' fis' g' a' d' g' a' b' e' a' b' c'' "
    r"fis' b' c'' d''",
    r"es''16 d'' bes' g' a' bes' d'' c'' bes' g' f' g' a' bes' g' f' d' es' f' g' bes' a' "
    r"g' f' d' bes a g",
    r"c'16 e' g' d' fis' a' e' g' c'' fis' a' d'' g' c'' e'' a' d'' fis'' c'' e'' g'' "
    r"fis'' d'' a' g'' e'' c'' d''",
    r"e''16 dis'' e'' c'' b' c'' a' gis' a' e' g' a' c'' b' a' g' fis' a' c'' e'' d'' c'' "
    r"a' fis' d' fis' a' c'')",
]

# The bass alone, between the solos of the drums: lines in the high register.
BASS_SOLO = [
    r"g,16( d g a d' g a d' e' a d' e' g'8 e' d'16 b g a b d' e'8 d'16 b a g)",
    r"e16( g a b d' e' g'8 fis' e' d'4 b8 a g e4.)",
    r"c16( g c' d' g c' d' e' g' e' d' c' b8 d' e'16 fis' g' e' d' b g8 a b)",
    r"c'8( e' g' fis'4. e'8 d' b16 a g e fis8 a16 b d' e' fis'8)",
]

# The grooves with the new division of the pulses: five notes in each long pulse and
# three in the short pulse. The pulses keep their lengths (see research/tables/rhythm.csv,
# "Pulse morph").
MORPH = Groove(
    """
    hh  xxxxx xxxxx xxx xxxxx xxxxx
    sn  ----- o---g --- ----- o--g-
    bd  x--x- ----- x-- x-x-- -----
    """,
    CLAVE,
)
MORPH_HALF = Groove(
    """
    hh  x-x-x x-x-x x-x x-x-x x-x-x
    sn  ----- ----- --- x---- -----
    bd  x---- ----- x-- ----- ---x-
    """,
    CLAVE,
)
MORPH_FILLS: dict[str, dict[str, list[str]]] = {
    "five 1": {"sn": ["oogoo"], "bd": ["-----"]},
    "five toms 1": {"sn": ["oo---"], "tm": ["--hmf"]},
    "five 2": {"sn": ["o-ogo", "ooOoo"], "bd": ["-x---", "-----"]},
    "five toms 2": {"sn": ["oog--", "-----"], "tm": ["---hh", "mmfff"], "bd": ["-----", "x-x--"]},
}
FILLS.update(MORPH_FILLS)


# ----------------------------------------------------------------------------
# A figure whose length is not the length of the bar
# ----------------------------------------------------------------------------


def cycle_bars(cell: str, bars: int, close: str = "", steps: tuple[int, ...] = STEPS) -> list[str]:
    """Lay a short figure again and again across some bars. Return a pattern for each bar.

    `cell` is a figure in sixteenth notes whose length is not a part of the
    bar (for example 11). It repeats with no gap. The last notes of the
    last bar are `close`: there the figure and the bars come together again.
    This is the method of the band Meshuggah (see research/tables/rhythm.csv).
    """
    size = sum(steps)
    total = size * bars
    flat = (cell * (total // len(cell) + 1))[: total - len(close)] + close
    result = []
    for bar in range(bars):
        part = flat[bar * size : (bar + 1) * size]
        groups, place = [], 0
        for length in steps:
            groups.append(part[place : place + length])
            place += length
        result.append(" ".join(groups))
    return result


def only(pattern: str, letters: str, new: str = "x") -> str:
    """Return a pattern with `new` at each place that has one of `letters`, and rests elsewhere."""
    return "".join(char if char == " " else (new if char in letters else "-") for char in pattern)
