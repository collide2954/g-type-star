"""Part 3: the main sequence. The star burns hydrogen in a stable state.

This is the longest part: seven passages, each with one idea in front
(see design/plan.md).

- C: the theme, plain. The saxophone, the rhythm section, and from the
  ninth bar a line of the violins that moves when the theme holds a note.
- D: the theme against a riff of bass guitar and guitar. The horns answer.
  The chords of the second half go up, and the violins go up with them.
- E: the bar of seven quarter notes as a drum-and-bass beat (the tempo of
  the work, 175, is the tempo of that style). The melody above it is the
  motto upside down. A short solo of the electric piano, then a snare roll.
- F: the saxophone and the guitar take turns: four bars each, two bars
  each, one bar each. The last note of each turn echoes under the next
  turn. Then all lead players have the second fast line.
- G: the bass guitar and the drums take turns.
- H: the motto as a canon. The saxophone plays it in long notes, and a
  delay brings each note again: the notes of the motto sound together as a
  chord. Then the motto on the note D, the fifth of the key, leads on.
- J: the theme at full force: trumpet, alto saxophone, and violins, with
  the tenor saxophone one octave lower. The guitar and the bass play a
  riff of four beats that crosses the bars of seven beats: it is the riff
  of part 4. In the second half the motto goes up by whole tones (G, A, B,
  C-sharp) in four parts, the drums go over to the four beats of the riff,
  and the last chord is the chord before F-sharp, the key of part 4.

The bass guitar and the kick drum play as one: the kick drum has the low
notes of the bass figure of its bar (`material.drum_bars`).

Style profile: "Groove" (see research/tables/profiles.csv). Three speeds at
the same time: kick and snare far apart, a fast grid of sixteenth notes, and
a slow melody.
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..compose import chords, patterns, tools
from ..compose.patterns import Groove
from ..notation import drums
from ..notation.work import Work
from . import flares
from . import material as m
from .material import Bars

SAX_TOP = 77  # F5: the highest note of the tenor saxophone in the audio

# ----------------------------------------------------------------------------
# The rhythm section of the theme passages (C and F)
# ----------------------------------------------------------------------------

# Bass figures for one bar. The letters are the notes of `material.bass_table`.
BASS = [
    "a__x-b ---c-e b_a_ a__x-c ---e_c",
    "a__x-b -x-c_e b_a_ a_-x-c b__c_e",
    "a__-xb ---c_e b_a_ a__x-c -x-e_c",
    "a__x-b ---c-e b-a_ a__c_e b_-c_h",
    "a__x-a -x-b_c b_a_ a__x-e ---c_b",
    "a_-a-b ---c_e g_b_ a__x-c -e_c_a",
    "a__x-b --xc-e b_a_ a_xa-c ---b_c",
    "a_____ -x-c_e b_a_ a__x-c b_g_e_",
    "a__xab ---c-e b_-a a__-xc -x-e_c",
]
# The figure of each bar of C (bar 16 has the riff of D) and of the first 20 bars of F.
# A figure does not come back within three bars; the last bar of four has more motion.
C_FIGURES = [0, 3, 1, 7, 4, 0, 5, 6, 0, 3, 2, 7, 8, 1, 5]
F_FIGURES = [0, 3, 1, 7, 4, 2, 5, 6, 8, 3, 0, 7, 1, 4, 5, 2, 6, 0, 8, 3]
# The chords of the electric piano: a figure of two bars, and a third bar for the end of
# each eight bars. The letter `a` is the chord.
C_KEYS = ["---a__ ------ a___ ---a__ ______", "a_____ ---a__ ---- a__-a_ ______"]
F_KEYS = ["a__--- ---a__ a_-- ---a__ ---a__", "---a__ ___--- -a__ ------ a_____"]
KEYS_END = "a__--- ---a__ a_-- ---a__ ---a__"
# The guitar in the second half of C: three notes of the chord, in eighth notes.
PICK = "a-b-c- a-b-c- a-b- c-a-b- c-a-b-"
# The line of the violins in bars 9 to 16 of C. It moves when the theme holds a note.
C_VIOLINS = [
    r"b''4.\p( ~ b''4. ~ b''4 a''4. ~ a''4.",
    r"g''4. ~ g''4. f''4 ~ f''4. g''4.)",
    r"r4. g''4.( ~ g''4 fis''4. ~ fis''4. ~",
    r"fis''4. e''4. ~ e''4 d''4. ~ d''4.)",
    r"d''4.( ~ d''4. e''4 fis''4. g''4. ~",
    r"g''4. ~ g''4.) bes''4( a''4. g''4.)",
    r"g''4.( ~ g''4. fis''4 e''4. d''4.",
    r"b'4. ~ b'4. ~ b'4 ~ b'4.) r4.",
]

# ----------------------------------------------------------------------------
# D: a riff against the theme
# ----------------------------------------------------------------------------

# The riff of the bass guitar and the guitar, in unison. The first two pulses are the
# same in most forms: that is the part that the ear knows again. The end changes.
RIFFS = [
    "a-aa-c -a-b-- a_-x a-aa-e c-b-a-",
    "a-aa-c -a-b-- a_-x a--a-b c-e-g-",
    "a-aa-c -a-b-- a_a- -a-c-d b_____",
    "a-aa-c -a-b-c d-e- g-e-d- c-b-h-",
    "a-aa-c -a-b-- a_-x a-a-ab c-e-c-",
    "a--a-a -c-b-- a_ab -a-a-e c-b-a-",
]
# The drums of the riff. The kick drum of the first, third and fourth pulse comes from
# the riff of the bar.
RIFF_GROOVE = Groove(
    """
    hh  x-x-x- x-x-o- x-x- x-x-x- x-x-o-
    sn  ------ o--g-- ---g ------ o--g--
    bd  x-xx-- ------ x--- x-xx-- ---x--
    """,
    m.CLAVE,
)
# The four bars between the two riff passages: the bass has long notes.
BASS_OPEN = [
    "a_____ ______ ---- a__x-b c_____",
    "a_____ ---a__ ---- ------ a_-b-c",
    "a_____ ______ --a_ a__x-c ---e_c",
    "a_____ ---x-a b___ ------ a_-c-h",
]
# The form of the riff or of the long notes in each of the first 14 bars of D.
D_FIGURES = [RIFFS[0], RIFFS[1], RIFFS[2], RIFFS[3], *BASS_OPEN, RIFFS[4], RIFFS[0], RIFFS[5],
             RIFFS[2], RIFFS[1], RIFFS[3]]  # fmt: skip
# The horns answer the theme with short chords.
SHOUTS = [
    "------ ---A-- ---- ------ A--a--",
    "A----- ------ ---- ---A-a ------",
    "------ A--a-- ---- ------ ---A--",
    "A--a-- ------ a___ ------ A_____",
]
# The chords of the last eight bars of D: the bass note goes up from E to B-flat. The
# melody has the notes of the theme: each chord gives them a new colour.
CLIMB = ["Em11", "Cmaj9", "Am11", "D13sus", "Gmaj9/B", "Bbmaj7#11", "Cmaj9#11", "Am11"]
# The violins go up with the chords: from B4 to D6 in six bars.
D_VIOLINS = [
    r"b'4.\mp\<( ~ b'4. ~ b'4 d''4. ~ d''4.",
    r"e''4. ~ e''4. ~ e''4 g''4. ~ g''4.",
    r"a''4. ~ a''4. ~ a''4 b''4. ~ b''4.",
    r"c'''4. ~ c'''4. ~ c'''4 b''4. a''4.)",
    r"b''4.\f( ~ b''4. ~ b''4 d'''4. ~ d'''4.",
    r"d'''4. ~ d'''4. ~ d'''4 c'''4. bes''4.)",
]
# The short chords of the band: with the riff of D, and in the last turns of F.
HITS = [
    "A--a-- ------ ---- A--a-- ------",
    "A----- ---a-- ---- A--a-- ------",
    "A--a-- ------ ---- A----- ---a--",
    "A--a-- ------ a___ A--a-- A_____",
]

# ----------------------------------------------------------------------------
# E: the breakbeat
# ----------------------------------------------------------------------------

# The bar of seven quarter notes as a drum-and-bass beat: the snare drum is on the
# second, the fourth, and the sixth quarter note (not on the pulses of the main
# metre), with soft notes between. The second form has the kick drum between the beats.
BREAK_A = Groove(
    """
    hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ----o- -g---g o-g- --g-o- ---go-
    bd  x----- ----x- ---- x----- -x----
    """,
    m.CLAVE,
)
BREAK_B = Groove(
    """
    hh  x-x-x- x-x-x- x-o- x-x-x- x-x-x-
    sn  ----o- -g-g-- o--g -g--o- -g-g-o
    bd  x-x--- ----xx ---- --x--- ----x-
    """,
    m.CLAVE,
)
# Under the solo of the electric piano: kick drum and cross-stick only.
BREAK_THIN = Groove(
    """
    hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ------ ------ x--- ------ ----x-
    bd  x----- ------ ---- x----- ------
    """,
    m.CLAVE,
)
m.FILLS.update({
    "roll 1": {"sn": ["oooooo"], "bd": ["x-----"]},
    "roll 2": {"sn": ["o-oo-o", "oooooooooooo"], "bd": ["------", "x-----"]},
})  # fmt: skip
# The last two bars of E: the snare drum goes from eighth notes to thirty-second notes.
BUILD = [
    "sn  o-o-o- o-o-o- o-o- oooooo oooooo\nbd  x----- x----- x--- x----- x-----",
    "sn  oooooo oooooo oooo oooooooooooo OOOOOO\nbd  x----- x----- x-x- x-x-x- xxxxxx",
]
# The bass of the breakbeat: long low notes, and short notes that lead to the next bar.
BASS_BREAK = [
    "a_____ ______ --a_ ______ --c-e-",
    "a_____ --b-a_ ____ ---c__ a_-h--",
    "a___-a ______ c___ a_____ -b-c-e",
    "a_____ ____-a -x-b a_____ --e-c-",
]
BREAK_FIGURES = [0, 1, 2, 3, 1, 0, 3, 2, 0, 3, 1, 2, 0, 1]
COMPS_BREAK = [
    "---a-- ------ ---- ---a-- ------",
    "------ ---a-- ---- ------ ---a--",
    "---a-- ------ a___ ------ ---a--",
]
# The chip synthesizer: four notes of the chord, up and down.
CHIPS_BREAK = ["abcdab cdabcd abcd dcbadc badcba", "a-c-b- d-b-c- adcb d-b-c- a-c-d-"]
# The drum machine with the breakbeat: claps on the beats of the snare drum, fast hats.
MACHINE_BREAK = [
    "ms  ----c- ------ c--- ----c- ----c-\nmh  xxxxxx xxxxxx xxxx xxxxxx xxxxxx",
    "ms  ----c- ------ c--- ----c- ------\nmh  x-xxx- xxxxxx x-xx xxxxxx xxx-xx",
]
# The solo of the electric piano (two bars), in the scale of B-flat with five notes.
KEYS_SOLO = [
    r"r8 g'16( bes' c'' d'' f'' g'' f'' d'' c'' bes' g'8 f'16 g' bes' c'' d''8 f''16 d'' c'' "
    r"bes' g' f' d'8)",
    r"f'16( g' bes' c'' d'' f'' g''8 f''16 d'' c''8 bes'16 c'' d'' f'' g'' bes'' c'''8 bes''16 "
    r"g'' f'' d'' c'' bes' g'8)",
]

# ----------------------------------------------------------------------------
# F: the saxophone and the guitar take turns
# ----------------------------------------------------------------------------

# The number of the bar in F, and the music of that bar. The turns become shorter: four
# bars each, then two bars each (two times), then one bar each (two times). The
# saxophone stays under F5 and uses its low notes: honks on the low A, runs through
# two octaves and a half.
SAX_TURNS = {
    # The motto as a fast start (G, C, D, E), then lines in the middle of the instrument.
    1: r"g16( c' d' e' g' a' b'8->) a'16( g' e' d' b a g8) a16( b d' e' g'8 e'16 d' b8 d')",
    2: r"r8 f'16( g' bes' c'' d''8->) c''16( bes' g' f' d'8) f'16( g' bes'8 a' g'16 f' d'8 "
    r"c' bes)",
    3: r"c'16( e' g' a' b' d'' e''8->) d''16( b' g' fis' e'8) d'16( e' g' a' b'8 d''16 b' a'8 "
    r"g' e')",
    # Two low notes, then one run to the high E.
    4: r"a,8-> a,-> r8 c16( e g a c' d' e' g' a' c'' d''8 e''4.-> ~ e''4)",
    # A figure of three notes with accents: a rhythm, not a line.
    9: r"d''8->( b' a' d''8-> b' a' d''8-> b' d''8-> b' a' g'8 a' b')",
    10: r"d''8->( c'' bes' d''8-> c'' bes' d''8-> c'' f''4.-> ~ f''8) r4",
    # A long high E, a fall of two octaves and a half, and the start of a rise.
    13: r"e''4.->( ~ e''4 d''16 b' a'8 g'16 e' d'8 b16 a g d b,8) d16( e g a)",
    # The rise goes on to the highest note.
    14: r"bes16( c' d' f' g' bes' c'' d'' f''8->) d''16( c'' bes' g' f'8) g'16( bes' c'' d'' "
    r"f''4.->) r8",
    17: r"g16( b d' e' g' b' d''8->) b'16( a' g' e' d' b g8) a16( b d' e' g'8 a'16 b' d''8 e'')",
    19: r"e''16( d'' b' a' g' e' d' e' g' a' b' d'' e''8) d''( b'16 a' g' e' d'8) c'16( d' e' "
    r"g' a'8)",
}
GUITAR_TURNS = {
    # A long note, then a line down and up.
    5: r"d''4.->( ~ d''8 e''16 fis'' g'' fis'' e'' d'' b' a') g'( a' b' d'' e'' fis'' a'' g'' "
    r"e'' d'' b' a')",
    # Groups of four notes that go down (the scale of G minor with five notes).
    6: r"bes''16( g'' f'' d'') g''( f'' d'' c'') f''( d'' c'' bes') d''( c'' bes' g') c''( bes' "
    r"g' f') bes'( g' f' d') g'( f' d' c')",
    # Wide chords, note by note, up to the high B.
    7: r"c'16( e' g' b' d'' fis'') a''( g'' e'' d'' b' a') g'( b' d'' fis'') a''( b'' a'' fis'' "
    r"d'' b') a'( b' d'' e'' fis'' a'')",
    8: r"b''4.->( ~ b''4. a''16 g'' e'' d'' c''8) a'16( g' e'8) d'16( e' g' a' c''8)",
    # Chords of three notes with the two hands on the fingerboard: E minor, B minor, C, D.
    11: r"e''16(\tap b' g') e''( b' g') fis''( d'' b') fis''( d'' b') g''( e'' c'') g''( e'' c'') "
    r"a''( fis'' d'') a''( fis'' d'') b''8->\pick a''16( g'')",
    12: r"c'''16( b'' a'' g'' e'' d'') c''( b' a' g' e' d') c'8 e'16( g' a' c'') d''8 e'' "
    r"c'''4.->",
    # Groups of three notes that go down by step.
    15: r"b''16( a'' g'') a''( g'' fis'') g''( fis'' e'') fis''( e'' d'') e''( d'' c'') d''( c'' "
    r"b') c''( b' a') b'( a' g') a'( g' fis' g')",
    16: r"e'16( g' a' b' c'' d'') e''( g'' a'' b'' c''' b'') a''8 g''16( e'') d''8 e''16( g'') "
    r"a''4.-> ~ a''8",
    # Two and a half octaves up in one pulse, then down.
    18: r"g16( bes c' d' f' g') bes'( c'' d'' f'' g'' bes'') c'''8-> bes''16( g'' f'' d'' c'' "
    r"bes') g'8 f'16( g' bes' c'') d''8",
    # The last bar before the line: the chords of A minor and G, note by note, up and down.
    20: r"a16( c' e' g' b' c'' e'' g'') a''( g'' e'' c'' b' g' e' c') d'( g' b' d'' g'' b'') "
    r"c'''8-> b''16( a'' g'' e'')",
}
# The short chords of the horns behind the turns of two bars.
ANSWERS = ["------ ------ ---- A--a-- ------", "------ ---A-- ---- ------ A-----",
           "---A-- ------ a___ ------ ------", "------ ------ ---- ---A-a A_____"]  # fmt: skip

# ----------------------------------------------------------------------------
# H: the canon of the motto
# ----------------------------------------------------------------------------

# The saxophone: the motto in long notes, with one bar of rest after each of the first
# two forms (there the echoes play). Bars 9 to 16: the motto from A, from C, and from D
# (the fifth of the key), each time higher.
H_SAX = [
    r"g4.\p\subtone( c'4. d'4 e'4. ~ e'4.)",
    None,
    r"e'4.( d'4. c'4 g4. ~ g4.)",
    None,
    r"g'4.( c''4. d''4 e''4. ~ e''4.)",
    r"r4. bes'4.( g'4 f'4. ~ f'4.)",
    r"e'4.( g'4. a'4 b'4. ~ b'4.)",
    r"a'4.( g'4. e'4 d'4. ~ d'4.)",
    r"a4.\mp\normaltone( c'4. d'4 e'4. ~ e'4.)",
    r"r4. e'4.( g'4 a'4. ~ a'4.)",
    r"c'4.( e'4. fis'4 g'4. ~ g'4.)",
    r"r4. g'4.( b'4 d''4. ~ d''4.)",
    r"d'4.\mf\<( g'4. a'4 b'4. ~ b'4.)",
    r"r4. b'4.( d''4 e''4. ~ e''4.)",
    r"d''4.( e''4. d''4 e''4. ~ e''4. ~",
    r"e''4. ~ e''4. es''4 d''4.)\f r4.",
]
H_CHORDS = ["Gmaj9", "Ebmaj7#11", "Cmaj9#11", "Am11", "Gmaj9", "Ebmaj7#11", "Cmaj9#11", "Am11",
            "Am11", "Am11", "Cmaj9#11", "Cmaj9#11", "D13sus", "D13sus", "D13sus", "D13b9"]  # fmt: skip
# The drums of H: cross-stick and kick drum, then the half-time groove.
H_GROOVE = Groove(
    """
    hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ------ ------ ---- x----- ------
    bd  x----- ------ x--- ------ ---x--
    """,
    m.CLAVE,
)

# ----------------------------------------------------------------------------
# J: the theme at full force, and the riff of four beats
# ----------------------------------------------------------------------------

# The riff of part 4 (`flares.RIFF_HALF`, its first bar): 16 sixteenth notes. It starts
# again after each four beats; a bar has seven beats. After four bars the riff and the
# bar start together again.
CROSS = "P-aa-a-aa-b-a-aa"
# The roots of the riff: the note of the guitar and of the bass guitar.
ROOTS = {"G": ("g,,", "g,,"), "Eb": ("es,", "es,,"), "C": ("c,", "c,"), "A": ("a,,", "a,,"),
         "B": ("b,,", "b,,"), "C#": ("cis,", "cis,"), "D": ("d,", "d,")}  # fmt: skip
# Bars 9 to 16: the motto in four parts, with the same form of chord under each note
# (from below: root, fourth, fifth, root). Two bars at each level: G, A, B, C-sharp.
# Each player: the bar with the motto, the bar with the answer, and the last bar of J.
SOLI = {
    "tpt": (r"r4. g'4.->( c''4 d''4. e''4. ~", r"e''4. ~ e''4.) r4 d''4.->( e''4.)",
            r"e''4. ~ e''4. ~ e''4 ~ e''4.) r4."),
    "asax": (r"r4. d'4.->( g'4 a'4. c''4. ~", r"c''4. ~ c''4.) r4 a'4.->( c''4.)",
             r"c''4. ~ c''4. ~ c''4 ~ c''4.) r4."),
    "tsax": (r"r4. c'4.->( f'4 g'4. a'4. ~", r"a'4. ~ a'4.) r4 g'4.->( a'4.)",
             r"a'4. ~ a'4. ~ a'4 ~ a'4.) r4."),
    "tbn": (r"r4. g4.->( c'4 d'4. f'4. ~", r"f'4. ~ f'4.) r4 d'4.->( f'4.)",
            r"f'4. ~ f'4. ~ f'4 ~ f'4.) r4."),
}  # fmt: skip
LEVELS = [(0, 0), (2, 1), (4, 2), (6, 3)]  # semitones and scale steps above G
J_CHORDS = [*m.LOOP_A, *m.LOOP_A, "G9sus", "G9sus", "A9sus", "A9sus", "B9sus", "B9sus",
            "C#9sus", "C#9sus"]  # fmt: skip
J_ROOTS = ["G", "Eb", "C", "A", "G", "Eb", "C", "A", "G", "G", "A", "A", "B", "B", "C#", "C#"]
# The drums of bars 9 to 16: the groove of part 4, in the four beats of the riff.
FOUR_HATS, FOUR_STACK = "x-x-x-x-x-x-x-x-", "k---k---k---k---"
FOUR_SNARE, FOUR_KICK = "--------O-------", "x-xx-x-xx-x-x-xx"


def _figures(order: list[int], symbols: list[str]) -> tuple[list[str], list[str]]:
    """Return the bass figure of each bar, and its music."""
    figures = [BASS[number] for number in order]
    music = [
        patterns.pitched(figure, m.CLAVE, m.bass_table(symbol))
        for figure, symbol in zip(figures, symbols, strict=False)
    ]
    return figures, music


def _comp(
    symbols: list[str], rhythms: list[str], low: int = 55, high: int = 77, end: str = KEYS_END
) -> list[str]:
    """Return one bar of the electric piano for each chord.

    The rhythm is a figure of some bars that comes again; each eighth bar has
    the rhythm `end`. Each chord takes the nearest notes to the chord before.
    """
    bars = []
    before = None
    for number, symbol in enumerate(symbols):
        before = chords.voice(symbol, 4, low=low, high=high, before=before)
        rhythm = end if number % 8 == 7 else rhythms[number % len(rhythms)]
        bars.append(patterns.pitched(rhythm, m.CLAVE, {"a": chords.names(before, symbol)}))
    return bars


def _picks(symbols: list[str]) -> list[str]:
    """Return one bar of the guitar for each chord: three notes, in eighth notes."""
    bars = []
    for symbol in symbols:
        notes = chords.voice(symbol, 3, low=62, high=81)
        table = {
            letter: chords.names((midi,), symbol) for letter, midi in zip("abc", notes, strict=True)
        }
        bars.append(patterns.pitched(PICK, m.CLAVE, table))
    return bars


def _cross(first: int, roots: list[str], player: int) -> list[str]:
    """Return the riff of four beats for some bars. `player`: 0 = guitar, 1 = bass guitar.

    `first` is the number of sixteenth notes of the riff that came before the
    first of these bars.
    """
    size = sum(m.STEPS)
    flat = CROSS * (first // len(CROSS) + len(roots) * 2 + 2)
    flat = flat[first % len(CROSS) :]
    bars = []
    for number, root in enumerate(roots):
        part = flat[number * size : (number + 1) * size]
        groups, place = [], 0
        for length in m.STEPS:
            groups.append(part[place : place + length])
            place += length
        note = ROOTS[root][player]
        table = flares.guitar_table(note) if player == 0 else flares.bass_table(note)
        bars.append(patterns.pitched(flares.ring(" ".join(groups)), m.CLAVE, table))
    return bars


def _four(rows: dict[str, str], bars: int) -> list[str]:
    """Return drum bars from rows of 16 sixteenth notes that start again after four beats."""
    laid = {name: m.cycle_bars(cell, bars) for name, cell in rows.items()}
    return ["\n".join(f"{name}  {laid[name][number]}" for name in rows) for number in range(bars)]


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]
    whole = ["a_____ ______ ____ ______ ______"]

    # ------------------------------------------------- C: the theme, plain
    s = Bars(work, 16)
    structure.mark(s.bar(1), "C")
    symbols = m.LOOP_A * 4
    # The first note of the theme comes on the first beat here: the saxophone started
    # the phrase in the last bar of the ignition.
    s.set("tsax", [r"g4.) ~ g4. c'4( d'4. ~ d'4.", *m.THEME_LOW[1:], *m.THEME_LOW_RISE])
    figures, bass = _figures(C_FIGURES, symbols)
    # The last bar has the riff of D, soft and growing: the riff starts before the mark.
    figures.append(RIFFS[0])
    bass.append(tools.first(patterns.pitched(RIFFS[0], m.CLAVE, m.bass_table(symbols[15])),
                            r"\mp\<", note=True))  # fmt: skip
    s.set("bass", bass, r"\f\fingers")
    s.set(
        "drums",
        m.drum_bars(m.MAIN, 16, "theme 1", crash=(1, 9), fills={8: "snare 1", 16: "toms 2"},
                    kicks=figures),
        r"\f",
    )  # fmt: skip
    s.set("keys.rh", _comp(symbols, C_KEYS), r"\mf")
    s.set("gtr", [None] * 8 + _picks(symbols[8:]), r"\mp\clean\pmoff")
    s.set("vn1", [None] * 8 + C_VIOLINS)
    s.set("vn2", [None] * 8 + [tools.octave(bar, -1) for bar in C_VIOLINS])
    s.set("perc", [None] * 8 + m.percussion(m.SHAKER, 8), r"\mp")
    low_strings = m.layers([None] * 8 + symbols[8:], whole, ("vc", "va"), "strings")
    for player, bars in low_strings.items():
        s.set(player, bars, r"\p")
    # The trombone and the baritone saxophone hold the fifth of the key under the last
    # two bars: the chord of D grows out of the theme.
    s.set("tbn", [None] * 14 + [r"d1..\pp\< ~", r"d1.."])
    s.set("bsax", [None] * 14 + [r"d,1..\pp\< ~", r"d,1.."])
    # The seam with the ignition: its arpeggios and its low tone go on and become soft.
    table = {"a": "g''", "b": "b''", "c": "d'''", "d": "e'''", "e": "g'''"}
    tail = [
        patterns.pitched("abcdec abcdec abcd ecabcd ecabcd", m.CLAVE, table),
        tools.first(patterns.pitched("a-c-e- --b-d- a--- ---c-- e-----", m.CLAVE, table), r"\p",
                    note=True),
    ]  # fmt: skip
    s.set("chip", tail + [None] * 14, r"\mp", r'\switch "chip pulse"')
    s.set("sbass", r'\switch "bass sub" g,,1..\mf\> | R1*14/8\! | R1*14/8*14 |')
    s.close()

    # ------------------------------------------------- D: the theme against a riff
    s = Bars(work, 16)
    structure.mark(s.bar(1), "D")
    climb = [*m.LOOP_A, *m.LOOP_A, *CLIMB]  # the chords of the 16 bars
    s.set("tsax", m.THEME_WIDE + m.THEME_CLOSE_WIDE, r"\f")
    s.set(
        "drums",
        m.drum_bars(RIFF_GROOVE, 16, "riff", amount=0.9, crash=(1, 3, 9, 11, 13),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "kicks 2"},
                    grooves={n: m.MAIN_RIDE for n in range(5, 9)},
                    kicks=[*D_FIGURES, None, None]),
        r"\f",
    )  # fmt: skip
    # Bars 1 to 4 and 9 to 14: the riff. Bars 5 to 8: long notes. Bars 15 and 16: the line.
    riff = [
        patterns.pitched(figure, m.CLAVE, m.bass_table(symbol))
        for figure, symbol in zip(D_FIGURES, climb, strict=False)
    ]
    s.set("bass", riff + [tools.octave(b, -2) for b in m.LINE_1], r"\f")
    # The guitar: the riff one octave above the bass, then high notes of the chords
    # with a clean sound, then the riff, then the line with the lead sound.
    heavy = [tools.octave(bar, 1) for bar in riff]
    picks = _picks(m.LOOP_A)
    line = [tools.first(m.LINE_1[0], r"\leadtone\pmoff", note=True), m.LINE_1[1]]
    guitar = [tools.first(bar, r"\crunch\pm", note=True) if n in (0, 8) else bar
              for n, bar in enumerate(heavy)]  # fmt: skip
    guitar[4:8] = [tools.first(picks[0], r"\clean\pmoff\mp", note=True), *picks[1:]]
    guitar[8] = tools.first(guitar[8], r"\f", note=True)
    s.set("gtr", guitar + line, r"\f")
    # The electric piano plays chords on the accents of the riff, and its figure of C in
    # the four bars between.
    keys = [m.comp(symbol, HITS[n % 4], low=55, high=77)[0] for n, symbol in enumerate(climb)]
    keys[4:8] = _comp(m.LOOP_A, C_KEYS)
    s.set("keys.rh", keys, r"\mf")
    shouts = m.layers([None] * 4 + m.LOOP_A + [None] * 8, SHOUTS, m.HORNS, "horns")
    swell = m.layers([None] * 10 + CLIMB[2:6] + [None] * 2, whole, m.HORNS, "horns")
    for player in m.HORNS:
        bars = [a or b for a, b in zip(shouts[player], swell[player], strict=True)]
        bars[10] = tools.first(bars[10] or "", r"\mp\<", note=True)
        s.set(player, bars, r"\f")
    s.set("vn1", [None] * 8 + D_VIOLINS + [None] * 2)
    s.set("vn2", [None] * 8 + [tools.octave(bar, -1) for bar in D_VIOLINS] + [None] * 2)
    low_strings = m.layers([None] * 8 + CLIMB[:6] + [None] * 2, whole, ("vc", "va"), "strings")
    for player, bars in low_strings.items():
        s.set(player, bars, r"\mp\<")
    s.set("perc", m.percussion(m.TAMBOURINE, 4) + m.percussion(m.SHAKER, 4)
          + m.percussion(m.TAMBOURINE, 6) + [None, None], r"\mf")  # fmt: skip
    # The first line for all lead players: the last two bars.
    s.set("lead", [None] * 14 + [tools.octave(bar, 1) for bar in m.LINE_1], r"\f")
    s.set("chip", [None] * 14 + [tools.octave(bar, 2) for bar in m.LINE_1], r"\mf")
    # The band samples itself: the last beat of the first riff passage comes two times.
    edits.append(Edit("stutter", s.bar(4), 7, length=1.0, stems=("drums", "bass", "gtr"),
                      slice=0.5))  # fmt: skip
    s.close()

    # ------------------------------------------------- E: the breakbeat
    s = Bars(work, 16)
    structure.mark(s.bar(1), "E")
    symbols = m.LOOP_B * 3 + ["Ebmaj9", "Bbadd9/D", "Cm11", "D13b9"]
    # Bars 1 to 4: the drums alone, dull at first; the bass comes in bar 3.
    # Bars 5 to 12: the melody of the bridge. Bars 13 and 14: the electric piano.
    # Bars 15 and 16: the snare roll.
    break_drums = m.drum_bars(BREAK_A, 14, "break", amount=0.8, crash=(1, 5, 9),
                              fills={4: "roll 1", 8: "snare 2", 12: "roll 2"},
                              grooves={**{n: BREAK_B for n in (3, 6, 7, 10, 11)},
                                       13: BREAK_THIN, 14: BREAK_THIN})  # fmt: skip
    build = [drums.steps(bar, m.CLAVE) for bar in BUILD]
    build[0] = tools.first(build[0], r"\mf\<", note=True)
    s.set("drums", break_drums + build, r"\f")
    low: list[str | None] = [
        patterns.pitched(BASS_BREAK[number], m.CLAVE, m.bass_table(symbol))
        for number, symbol in zip(BREAK_FIGURES, symbols, strict=False)
    ]
    low[:2] = [None, None]
    climb_bass = [
        patterns.pitched("a-a-a- a-a-a- a-a- b-b-b- b-b-b-", m.CLAVE, m.bass_table("Cm11")),
        patterns.pitched("a-a-a- a-a-a- aaaa aaaaaa aaaaaa", m.CLAVE, m.bass_table("D13b9")),
    ]
    s.set("bass", low + climb_bass, r"\f")
    s.set("sbass", m.roots(symbols[:14], "a_____ ______ ____ a_____ ______") + [None, None],
          r"\mf", r'\switch "bass reese"')  # fmt: skip
    stabs: list[str | None] = [*_comp(symbols[:12], COMPS_BREAK, end=COMPS_BREAK[2])]
    stabs[:2] = [None, None]
    tremolo = [m.comp(symbol, "aaaaaa aaaaaa aaaa aaaaaa aaaaaa", low=58, high=80)[0]
               for symbol in symbols[14:]]  # fmt: skip
    s.set("keys.rh", stabs + KEYS_SOLO + tremolo, r"\mf")
    sparkle: list[str | None] = [None]
    for number, symbol in enumerate(symbols[1:12]):
        notes = chords.voice(symbol, 4, low=74, high=96, rootless=False)
        table = {
            letter: chords.names((midi,), symbol)
            for letter, midi in zip("abcd", notes, strict=True)
        }
        sparkle.append(patterns.pitched(CHIPS_BREAK[number % 2], m.CLAVE, table))
    s.set("chip", sparkle + [None] * 4, r"\mp", r'\switch "chip pulse 25"')
    s.set("lead", [None] * 4 + m.BRIDGE + [None] * 4, r"\f", r'\switch "lead moog"')
    # The saxophone has the second half of the melody with the synthesizer, one octave lower.
    s.set("tsax", [None] * 8 + [tools.octave(bar, -1) for bar in m.BRIDGE[4:]] + [None] * 4,
          r"\mf")  # fmt: skip
    s.set("pad.rh", [None] * 12 + m.pad_bars(symbols[12:], low=60, high=84), r"\mp\<",
          r'\switch "supersaw"')  # fmt: skip
    for kind, players in (("horns", m.HORNS), ("strings", m.STRINGS)):
        swell = m.layers([None] * 14 + symbols[14:], whole, players, kind)
        for player, bars in swell.items():
            s.set(player, bars, r"\mp\<")
    chug = {"a": r"d, \pm"}
    s.set("gtr", [None] * 15 + [patterns.pitched("a-a-a- a-a-a- aaaa aaaaaa aaaaaa", m.CLAVE,
                                                 chug)], r"\mf\<\crunch")  # fmt: skip
    machine = [drums.steps(MACHINE_BREAK[n % 2], m.CLAVE) for n in range(8)]
    # The start: noise that falls and a low drop, as the last note of the line ends.
    s.set("eperc", [r"<< { f,,1..\mp } \\ { es,,1..\mp } >>", None, None, None, *machine,
                    None, None, None, None])  # fmt: skip
    edits += [
        # The drums start dull: a filter opens in two bars.
        Edit("lowpass", s.bar(1), 1, length=14.0, stems=("drums",), start=380.0, end=17000.0),
        # The end of the first half of the melody: the last two beats repeat in pieces.
        Edit("stutter", s.bar(8), 6, length=1.0, stems=("drums", "bass", "sbass"), slice=0.5),
        Edit("stutter", s.bar(8), 7, length=1.0, stems=("drums", "bass", "sbass"), slice=0.25),
        # The end of the melody: the last beat plays backwards.
        Edit("reverse", s.bar(12), 7, length=1.0, stems=("drums", "keys", "chip")),
        # The chords of the last two bars are cut into eighth notes.
        Edit("gate", s.bar(15), 1, length=14.0, stems=("pad", "keys"), slice=0.5, share=0.55),
    ]
    s.close()

    # ------------------------------------------------- F: the saxophone and the guitar
    s = Bars(work, 24)
    structure.mark(s.bar(1), "F")
    symbols = m.LOOP_A * 6
    sax: list[str | None] = [None] * 20
    guitar_solo: list[str | None] = [None] * 20
    for bar, music in SAX_TURNS.items():
        sax[bar - 1] = music
    for bar, music in GUITAR_TURNS.items():
        guitar_solo[bar - 1] = music
    guitar_solo[4] = tools.first(guitar_solo[4] or "", r"\leadtone\pmoff", note=True)
    s.set("tsax", sax + [tools.within(bar, 44, SAX_TOP) for bar in m.LINE_2], r"\f")
    s.set("gtr", guitar_solo + m.LINE_2, r"\f")
    figures, walk = _figures(F_FIGURES, symbols)
    s.set(
        "drums",
        m.drum_bars(m.MAIN_RIDE, 24, "sax solo", amount=1.2,
                    crash=(1, 5, 9, 13, 17, 18, 19, 20, 21, 23),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "snare 2",
                           17: "snare 1", 18: "toms 1", 19: "snare 1", 20: "kicks 2",
                           24: "toms 2"},
                    grooves={n: m.MAIN_OPEN for n in range(9, 25)},
                    kicks=[*figures, None, None, None, None]),
        r"\f",
    )  # fmt: skip
    s.set("bass", walk + [tools.octave(b, -2) for b in m.LINE_2], r"\f")
    keys = _comp(symbols, F_KEYS)
    keys[16:20] = [m.comp(symbol, HITS[n], low=55, high=77)[0]
                   for n, symbol in enumerate(symbols[16:20])]  # fmt: skip
    s.set("keys.rh", keys, r"\mf")
    s.set("pad.rh", [None] * 8 + m.pad_bars(symbols[8:]), r"\mp\<", r'\switch "pad warm"')
    answers = m.layers([None] * 8 + symbols[8:16] + [None] * 8, ANSWERS, m.HORNS, "horns")
    hits = m.layers([None] * 16 + symbols[16:20] + [None] * 4, HITS, m.HORNS, "horns")
    for player in m.HORNS:
        bars = [a or b for a, b in zip(answers[player], hits[player], strict=True)]
        bars[16] = tools.first(bars[16] or "", r"\ff", note=True)
        s.set(player, bars, r"\f")
    s.set("eperc", [r"ges,,1..\mf", *[None] * 23])
    s.set("perc", m.percussion(m.CONGAS, 16) + m.percussion(m.TAMBOURINE, 4) + [None] * 4,
          r"\mf")  # fmt: skip
    # The second line: the last four bars.
    s.set("lead", [None] * 20 + [tools.octave(bar, 1) for bar in m.LINE_2], r"\f")
    s.set("chip", [None] * 20 + [tools.octave(bar, 2) for bar in m.LINE_2], r"\mf")
    # The last pulse of each turn echoes under the next turn (a delay pedal).
    for bar, stem in ((4, "tsax"), (8, "gtr"), (10, "tsax"), (12, "gtr"), (14, "tsax"),
                      (16, "gtr")):  # fmt: skip
        edits.append(Edit("echo", s.bar(bar), 6.5, length=1.5, stems=(stem,), slice=1.5,
                          fade=0.5, share=0.4))  # fmt: skip
    s.close()

    # ------------------------------------------------- G: bass and drums take turns
    s = Bars(work, 8)
    structure.mark(s.bar(1), "G")
    solo_1 = m.Groove(
        """
        sn  o-oo-o o-g-oo ---- O--o-o g-O---
        tm  ------ ------ h-m- ------ ---f-f
        bd  -x--x- -x-x-- -x-x -xx-x- -x--x-
        """,
        m.CLAVE,
    )
    solo_2 = m.Groove(
        """
        cy  c----- ------ ---- ------ ------
        sn  ---o-- O--o-o ---- o-o-o- O-O-OO
        tm  -h--m- ------ f-f- ------ ------
        bd  x-x--x -xx-x- -x-x -x-x-x -x-x--
        """,
        m.CLAVE,
    )
    solo_3 = m.Groove(
        """
        sn  O-o-g- o-O--- oo-- O--O-- ------
        tm  ------ ---h-m --ff ------ h-m-f-
        bd  -x-x-x -x---- ---- -xx-xx -x-x-x
        """,
        m.CLAVE,
    )
    solo_4 = m.Groove(
        """
        cy  c----- ------ ---- k----- ------
        sn  ---ooo O-g-g- O--- ---O-- g-g-g-
        tm  ------ ------ -hmf ------ ------
        bd  x-x--- -x-x-x ---- x-x--- x-----
        """,
        m.CLAVE,
    )
    time = m.drum_bars(m.HALF, 8, "trade", amount=0.6, crash=(1, 5))
    s.set(
        "drums",
        [time[0], time[1], solo_1.text(), solo_2.text(), time[4], time[5], solo_3.text(),
         solo_4.text()],
        r"\f",
    )  # fmt: skip
    # In the last bar the bass leads down by step to the root of H.
    s.set("bass", [m.BASS_SOLO[0], m.BASS_SOLO[1], None, None, m.BASS_SOLO[2], m.BASS_SOLO[3],
                   None, r"r4. r4. r4 e8\mp( d b, a,4.)"], r"\f")  # fmt: skip
    hits_g = ["A_____ ------ ---- ------ ------", None, None, None] * 2
    chord_hits = ["Gmaj9", None, None, None, "Cmaj9#11", None, None, None]
    stabs_g = [None if symbol is None else m.comp(symbol, hit, low=55, high=77)[0]
               for symbol, hit in zip(chord_hits, hits_g, strict=True)]  # fmt: skip
    # The chord of H starts before the bar line and grows from nothing.
    stabs_g[7] = r"r4. r4. r4 <b d' fis' a'>4.\pp\< ~ <b d' fis' a'>4."
    s.set("keys.rh", stabs_g, r"\f")
    s.close()

    # ------------------------------------------------- H: the canon of the motto
    s = Bars(work, 16)
    structure.mark(s.bar(1), "H")
    s.set("tsax", H_SAX)
    s.set("keys.rh", m.pad_bars(H_CHORDS, low=55, high=77), r"\p")
    s.set("bass", m.roots(H_CHORDS[:14], "a_____ ______ ____ ______ ___c__", octave=1)
          + _cross(2 * 28, ["D", "D"], 1), r"\p")  # fmt: skip
    shimmer: list[str | None] = [None] * 4
    for symbol in H_CHORDS[4:12]:
        notes = chords.voice(symbol, 4, low=74, high=96, rootless=False)
        table = {
            letter: chords.names((midi,), symbol)
            for letter, midi in zip("abcd", notes, strict=True)
        }
        shimmer.append(patterns.pitched("a-b-c- d-c-b- a-b- c-d-c- b-a-b-", m.CLAVE, table))
    s.set("chip", shimmer + [None] * 4, r"\pp", r'\switch "chip pulse 25"')
    s.set(
        "drums",
        [None] * 4
        + m.drum_bars(H_GROOVE, 12, "canon", amount=0.5, crash=(), fills={12: "toms 2"},
                      grooves={n: m.HALF for n in range(5, 13)}),
        r"\p\<",
    )  # fmt: skip
    strings = m.layers([None] * 8 + H_CHORDS[8:], whole, m.STRINGS, "strings")
    for player, bars in strings.items():
        s.set(player, bars, r"\pp\<")
    s.set("perc", [None] * 4 + m.percussion(m.SHAKER_SOFT, 12), r"\p")
    # The riff of part 4 starts here, very soft, on the note D: four bars before J.
    s.set("gtr", [None] * 12 + _cross(0, ["D"] * 4, 0), r"\pp\<\crunch")
    # A delay of one long pulse on the saxophone: each note of the motto comes again
    # under the next notes.
    edits.append(Edit("echo", s.bar(1), 1, length=84.0, stems=("tsax",), slice=1.5, fade=0.55,
                      share=0.5))  # fmt: skip
    s.close()

    # ------------------------------------------------- J: the theme at full force
    s = Bars(work, 16)
    structure.mark(s.bar(1), "J")
    theme = m.THEME
    parts: dict[str, list[str | None]] = {
        "tpt": [*theme], "asax": [*theme], "tsax": [*m.THEME_LOW], "tbn": [None] * 8,
    }  # fmt: skip
    for player, (motto, answer, last) in SOLI.items():
        for number, (semitones, steps) in enumerate(LEVELS):
            parts[player].append(tools.tr(motto, semitones, steps))
            parts[player].append(tools.tr(last if number == 3 else answer, semitones, steps))
    for player, bars in parts.items():
        bars[8] = tools.first(bars[8] or "", r"\ff", note=True)
        s.set(player, bars, r"\f" if bars[0] else "")
    top = parts["tpt"]
    s.set("vn1", [tools.octave(bar or "", 1) for bar in top], r"\f")
    s.set("vn2", top, r"\f")
    s.set("lead", [None] * 8 + top[8:], r"\ff", r'\switch "lead moog"')
    low_strings = m.layers(J_CHORDS, whole, ("vc", "va"), "strings")
    for player, bars in low_strings.items():
        s.set(player, bars, r"\f")
    # The baritone saxophone has the root of each level, with a rest to breathe.
    roots = ["g,", "a,", "b,", "cis"]
    s.set("bsax", [None] * 8 + [bar for root in roots
                                for bar in (f"{root}1..-> ~", f"{root}1 ~ {root}4. r4.")],
          r"\ff")  # fmt: skip
    s.set("gtr", _cross(4 * 28, J_ROOTS, 0), r"\mf")
    s.set("bass", _cross(4 * 28, J_ROOTS, 1), r"\f")
    s.set("keys.rh", _comp(J_CHORDS, C_KEYS), r"\mf")
    s.set("pad.rh", m.pad_bars(J_CHORDS), r"\mf\<", r'\switch "supersaw"')
    both = [f"{shaker}\n{m.TAMBOURINE}" for shaker in m.SHAKER]
    s.set("perc", m.percussion(both, 8) + [None] * 8, r"\mf")
    # The drums: the groove of the theme for eight bars. Then the four beats of the riff:
    # hi-hat, snare drum on the third beat, kick drum with the riff; then the stack
    # cymbal of part 4 on each beat.
    first = m.drum_bars(m.MAIN_OPEN, 8, "full", amount=1.0, crash=(1, 5),
                        fills={4: "snare 1", 8: "toms 2"})  # fmt: skip
    four = _four({"hh": FOUR_HATS, "sn": FOUR_SNARE, "bd": FOUR_KICK}, 8)
    stack = _four({"cy": FOUR_STACK, "sn": FOUR_SNARE, "bd": FOUR_KICK}, 8)
    second = [drums.steps(bar, m.CLAVE) for bar in four[:4] + stack[4:]]
    s.set("drums", first + second, r"\f")
    s.close()
    structure.double_bar(s.section.last_bar)
