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
    seventh = 11 if 11 in chord.intervals else 10
    names = {
        "a": root, "b": root + 12, "c": root + 7, "d": root + seventh, "e": root + third,
        "f": root + 5, "g": root + 14, "h": root - 2, "i": root - 1,
    }  # fmt: skip
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
