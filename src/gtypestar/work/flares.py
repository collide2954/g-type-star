"""Part 4: the flares. The active Sun: spots, flares, and the cycle of 11 years.

A heavy rock groove. The guitar with eight strings is in front: its lowest
string (F-sharp) with the palm of the hand on it, and open chords of root,
fifth, and octave on the accents. The bass guitar plays the riff with the
guitar. The drummer plays the kick drum with two feet.

The metre is plain 4/4, at the tempo of the main sequence (the quarter note
stays). The reasons:

- The first version had a riff of 11 sixteenth notes against bars of 14/8,
  with the kick drum on the riff and one snare stroke in a bar. The owner
  of the project could not follow it. Here the snare drum is on beat 3
  (half time) or on beats 2 and 4, and each riff has the length of one or
  two bars.
- After four and a half minutes of 14/8, plain time is a release.
- Part 5 is in 4/4. Its beat is the dotted quarter note of this part: the
  last three bars have a stroke of all players on each dotted quarter
  note, and the kick drum plays the eighth notes of the new tempo.

The riff of 11 sixteenth notes of the first version is the start of each
bar of the first riff (`CELL`): it has a tail of five sixteenth notes, and
thus it starts again at each bar line. The accents of the second bar are
the motto from F-sharp: B, C-sharp, D-sharp.

The form (70 bars, 96 seconds):

    K  bars  1 to  8   the riff; half time (snare drum on beat 3)
       bars  9 to 16   gallop; snare drum on beats 2 and 4; the saxophone has a melody
       bars 17 to 24   sixteenth notes of the two feet; accents of 3 + 3 + 2
    L  bars 25 to 32   solo of the guitar, in F-sharp
       bars 33 to 40   the solo goes on, in A
       bars 41 to 48   saxophone and guitar take turns (two bars each), in C
    M  bars 49 to 56   the third line of all lead players, in E-flat
       bars 57 to 64   the riff goes up by semitones: F-sharp, G, A-flat, A
       bars 65 to 70   B-flat: the chord before E-flat, and the new beat

Each key is a minor third above the key before it (F-sharp, A, C, E-flat),
and the bass goes up by two semitones in the last bar before each new key.
The last eight bars before B-flat do the same thing more slowly.

No sound stops in this part, and the recording has no cuts.

Style profile: "Heavy" (see research/tables/profiles.csv). The sources for
the plain metre and the half-time groove under a saxophone melody are in
research/tables/form.csv (Tigran Hamasyan; the longest track of Sungazer).
"""

from __future__ import annotations

import numpy as np

from ..audio.tape import Cue
from ..compose import chords, patterns, tools
from ..compose.patterns import Groove
from ..notation import music
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
BEATS = (2, 2, 2, 2)  # four beats: four letters in a group are sixteenth notes
HALVES = (4, 4)  # two half notes: four letters in a group are eighth notes
CELL = "A-aa-a-aa-b"  # 11 sixteenth notes: the cycle of the sunspots has 11 years

# ----------------------------------------------------------------------------
# The riffs
# ----------------------------------------------------------------------------

# The letters of a riff. `a` is the root on the lowest string, with the palm on it.
# `b` is the root one octave higher. All other letters are open chords of root,
# fifth, and octave: `p` on the root, and the others at this number of semitones above
# the root. `m`, `n`, `o` are the notes of the motto (a fourth, a fifth, a sixth).
CHORD_STEPS = {"p": 0, "m": 5, "n": 7, "o": 9, "g": 1, "h": 2, "e": 10, "c": 6}

# Bars 1 to 8. The first 11 sixteenth notes of bars 1, 3, 5, 7 are `CELL`.
RIFF_HALF = [
    "P-aa -a-a a-b- a-aa",
    "P-aa -a-a M___ N_O_",
    "P-aa -a-a a-b- aaaa",
    "P-aa -a-a O___ N_M_",
    "P-aa -a-a a-b- -aab",
    "P-aa -aaa M__N __O_",
    "P-aa -a-a aab- aaaa",
    "G_G_ -aaa E___ C_C_",
]
# Bars 9 to 16: a gallop (one eighth note and two sixteenth notes).
RIFF_GALLOP = [
    "P-aa a-aa P-aa a-aa",
    "M-aa a-aa N-aa O-O-",
    "P-aa a-aa P-aa a-ab",
    "O-aa a-aa N-aa M-M-",
    "P-aa a-aa P-aa aaaa",
    "M-aa a-aa N-aa O_OO",
    "P-aa aaaa P-aa a-aa",
    "G-G- -G-G E-E- CCCC",
]
# Bars 17 to 24: sixteenth notes with accents of 3 + 3 + 2 (long, long, short: the
# clave of the work in small). The last two bars are the motto in eighth notes.
RIFF_FAST = [
    "PaaP aaPa PaaP aaPa",
    "MaaM aaMa NaaN aaOa",
    "PaaP aaPa PaaP aabb",
    "OaaO aaOa NaaN aaMa",
    "PaaP aaPa PaaP aaPa",
    "GaaG aaGa EaaE aaCa",
    "P_P_ P_P_ M_M_ M_M_",
    "N_N_ N_N_ O_O_ OOOO",
]
# Under the solos. The last bar of each list goes up to the next key: the chords one
# and two semitones above the root.
RIFF_SOLO_1 = [
    "P-aa -a-a a-b- a-aa",
    "P-aa -a-a a-b- aaaa",
    "P-aa -a-a a-b- a-aa",
    "P-aa -a-a M___ N_O_",
    "P-aa -a-a a-b- -aab",
    "P-aa -aaa a-b- aaaa",
    "P-aa -a-a aab- a-aa",
    "P-aa -a-a G_G_ H_H_",
]
RIFF_SOLO_2 = [
    "P-aa a-aa P-aa a-aa",
    "P-aa -a-a a-b- aaaa",
    "P-aa a-aa P-aa a-ab",
    "P-aa -a-a O___ N_M_",
    "P-aa a-aa P-aa aaaa",
    "P-aa -aaa a-b- aaaa",
    "P-aa a-aa P-aa a-aa",
    "P-aa -a-a G_G_ H_H_",
]
RIFF_SOLO_3 = [
    "P-aa a-aa P-aa a-aa",
    "M-aa a-aa N-aa O-O-",
    "PaaP aaPa PaaP aaPa",
    "PaaP aaPa PaaP aabb",
    "P-aa a-aa P-aa a-aa",
    "O-aa a-aa N-aa M-M-",
    "PaaP aaPa PaaP aaPa",
    "PaaP aaPa G_G_ H_H_",
]
# Bars 57 to 64: two bars on each root. The last beat is the chord of the next root.
RIFF_CLIMB = [
    ["PaaP aaPa PaaP aaPa", "PaaP aaPa P_P_ GGGG"],
    ["PaaP aaPa PaaP aabb", "PaaP aaPa PaaP GGGG"],
    ["PaaP aaPa PaaP aaPa", "P_P_ P_P_ P_P_ GGGG"],
    ["PaaP aaPa PaaP aaPa", "PaaP aaPa G_G_ GGGG"],
]
# Bars 65 to 67, on B-flat.
RIFF_LAST = ["P_P_ P_P_ P_P_ P_P_", "PPPP PPPP PPPP PPPP", "P--P --P- P--P --P-"]


def power(root: str) -> str:
    """Return a chord of root, fifth, and octave."""
    return "<" + " ".join(tools.tr(root, step) for step in (0, 7, 12)) + ">"


def guitar_table(root: str = "fis,,") -> dict[str, str]:
    """Return the notes of the riff letters for the guitar."""
    table = {"a": root + r" \pm", "b": tools.tr(root, 12) + r" \pmoff"}
    for letter, step in CHORD_STEPS.items():
        table[letter] = power(tools.tr(root, step)) + r" \pmoff"
    return table


def bass_table(root: str = "fis,,") -> dict[str, str]:
    """Return the notes of the riff letters for the bass guitar: the roots of the chords."""
    table = {"a": root, "b": tools.tr(root, 12)}
    for letter, step in CHORD_STEPS.items():
        # The chord one tone below the root is below the root if the bass has that note.
        low = step == 10 and music.parse(root).children[0].pitches[0].pitch.midi - 2 >= 23
        table[letter] = tools.tr(root, step - 12 if low else step)
    return table


def keys_table(root: str = "fis,,") -> dict[str, str]:
    """Return the notes of the riff letters for the left hand of the electric piano: octaves."""
    return {
        letter: "<" + note + " " + tools.tr(note, 12) + ">"
        for letter, note in bass_table(root).items()
    }


def ring(pattern: str) -> str:
    """Return a riff in which each chord sounds through the rest after it."""
    chars = list(pattern)
    for place in range(len(chars) - 1):
        if chars[place].isupper() and chars[place + 1] == "-":
            chars[place + 1] = "_"
    return "".join(chars)


def riff(bars: list[str], table: dict[str, str]) -> list[str]:
    """Return the bars of a riff for one player."""
    return [patterns.pitched(ring(bar), BEATS, table) for bar in bars]


def low_notes(roots: list[str | None], pattern: str = "a___ ____") -> list[str | None]:
    """Return bars of the low synthesizer: one root for each bar (None = a bar of rest)."""
    return [
        None if root is None else patterns.pitched(pattern, HALVES, {"a": root}) for root in roots
    ]


def strokes(pattern: str) -> str:
    """Return a drum row with one stroke for each note of a riff."""
    return "".join(char if char == " " else ("x" if char.isalpha() else "-") for char in pattern)


def burst(row: str, *beats: int) -> str:
    """Return a kick drum row with sixteenth notes of the two feet in some beats (0 to 3)."""
    groups = row.split()
    for beat in beats:
        groups[beat] = "xxxx"
    return " ".join(groups)


def accents(pattern: str) -> str:
    """Return the chords of a riff for the horns: each chord is an eighth note or longer."""
    groups = []
    for group in pattern.split():
        chars, sounding = [], False
        for char in group:
            if char.isalpha():
                sounding = char.lower() in CHORD_STEPS
                chars.append(char if sounding else "-")
            else:
                chars.append("_" if char == "_" and sounding else "-")
                sounding = sounding and char == "_"
        for place in range(len(chars) - 1):
            if chars[place].isalpha() and chars[place + 1] == "-":
                chars[place + 1] = "_"
        groups.append("".join(chars))
    return " ".join(groups)


def horn_tables(root: int, sharps: bool = True) -> dict[str, dict[str, str]]:
    """Return the note of each riff chord for each horn: root, fifth, fifth, root.

    The horns play the chords of the guitar with no third. The baritone
    saxophone has the root (from E2 to E-flat 3), the trombone the fifth, the
    alto saxophone the fifth one octave higher, and the trumpet the root two
    octaves above the baritone saxophone.
    """
    tables: dict[str, dict[str, str]] = {player: {} for player in m.HORNS}
    for letter, step in CHORD_STEPS.items():
        low = root + step
        while low < 40:
            low += 12
        while low > 51:
            low -= 12
        for player, more in zip(m.HORNS, (0, 7, 19, 24), strict=True):
            tables[player][letter] = chords.from_midi(low + more, prefer_sharps=sharps).name
    return tables


# ----------------------------------------------------------------------------
# The drums
# ----------------------------------------------------------------------------

CHINA = "k--- k--- k--- k---"  # the stack cymbal on each beat
OPEN_HATS = "o-o- o-o- o-o- o-o-"  # the open hi-hat in eighth notes
BELL = "b-x- b-x- b-x- b-x-"  # the bell of the ride cymbal on each beat
CRASHES = "d--- d--- d--- d---"  # the second crash cymbal on each beat
HALF = "---- ---- O--- ----"  # half time: the snare drum on beat 3
BACK = "---- O--- ---- O---"  # the snare drum on beats 2 and 4
FOUR = "O--- O--- O--- O---"  # the snare drum on each beat
EIGHTHS = "O-o- O-o- O-o- O-o-"
GALLOP = "x-xx x-xx x-xx x-xx"
FEET = "xxxx xxxx xxxx xxxx"  # sixteenth notes: the two feet take turns

# Fills for the last beat or the last two beats of a bar. Six letters in a beat are
# sextuplets.
FILLS: dict[str, dict[str, list[str]]] = {
    "one snare": {"sn": ["o-oo"], "bd": ["-x--"]},
    "one toms": {"sn": ["oo--"], "tm": ["--hf"], "bd": ["x---"]},
    "one feet": {"sn": ["O---"], "bd": ["-xxx"]},
    "one six": {"sn": ["ooooOO"], "bd": ["x-----"]},
    "two snare": {"sn": ["o-oo", "OoOO"], "bd": ["-x--", "x---"]},
    "two toms": {"sn": ["oo--", "----"], "tm": ["--hh", "mmff"], "bd": ["x---", "x-x-"]},
    "two feet": {"sn": ["O--O", "--O-"], "bd": ["-xx-", "xx-x"]},
    "two six": {"sn": ["oooooo", "------"], "tm": ["------", "hhmmff"], "bd": ["x-----", "x-----"]},
    "two build": {"sn": ["O-O-", "OOOO"], "bd": ["xxxx", "x-x-"]},
}  # fmt: skip


def kit_bar(
    cymbal: tuple[str, str],
    snare: str,
    kick: str,
    *,
    crash: str = "",
    fill: str = "",
    ghosts: float = 0.0,
    source: np.random.Generator | None = None,
) -> str:
    """Return one bar of the drums in four beats.

    `cymbal` is the name of the row ("cy", "hh" or "rd") and its strokes.
    `crash` is a cymbal for the first beat ("c" or "d"). `fill` is the name
    of a fill for the end of the bar. `ghosts` is the probability of a ghost
    note on each free sixteenth note between two eighth notes.
    """
    rows = {cymbal[0]: cymbal[1], "sn": snare, "bd": kick}
    groove = Groove("\n".join(f"{name} {row}" for name, row in rows.items()), BEATS)
    if crash:
        groove.put("cy", 0, 0, crash)
        if cymbal[0] != "cy":
            groove.put(cymbal[0], 0, 0, "-")
    if ghosts and source is not None:
        for beat in range(len(BEATS)):
            for step in (1, 3):
                free = all(groove.empty("sn", beat, place) for place in (step - 1, step, step + 1))
                if free and source.uniform() < ghosts:
                    groove.put("sn", beat, step, "g")
    if fill:
        parts = FILLS[fill]
        size = len(next(iter(parts.values())))
        first = len(BEATS) - size
        groove.fill(first, parts)
        # A beat with sextuplets: the rows with no stroke get the same division.
        for beat in range(first, len(BEATS)):
            places = max(len(row[beat]) for row in groove.rows.values())
            for row in groove.rows.values():
                if len(row[beat]) != places and set(row[beat]) <= set("-."):
                    row[beat] = "-" * places
    return groove.text()


def kit_bars(
    cymbal: tuple[str, str],
    snare: str,
    kicks: list[str],
    key: str,
    *,
    crash: dict[int, str] | None = None,
    fills: dict[int, str] | None = None,
    ghosts: float = 0.0,
) -> list[str]:
    """Return one bar of the drums for each kick drum row. Bar numbers start at 1."""
    source = m.random("flares", key)
    return [
        kit_bar(cymbal, snare, kick, crash=(crash or {}).get(number, ""),
                fill=(fills or {}).get(number, ""), ghosts=ghosts, source=source)
        for number, kick in enumerate(kicks, start=1)
    ]  # fmt: skip


# ----------------------------------------------------------------------------
# The lines
# ----------------------------------------------------------------------------

# The melody of the saxophone above the gallop (bars 9 to 16): the motto from F-sharp
# (F-sharp, B, C-sharp, D-sharp) in long notes, then a rise to a high A.
SAX_MELODY = [
    r"r4 fis'4( b'4 cis''4 ~",
    r"cis''2.) r8 gis'8(",
    r"fis'4.) dis''8( ~ dis''2 ~",
    r"dis''4 cis''4 a'4.) r8",
    r"r8 cis''8( e''4 fis''2 ~",
    r"fis''4 e''8 cis'' e''4 fis''8 a''8 ~",
    r"a''1 ~",
    r"a''4) r4 r2",
]
# The solo of the guitar: eight bars in F-sharp, then eight bars in A. It starts with
# the motto; the start of the second half is the start of the first half in the new key.
SOLO_1 = [
    r"r4 fis'8( b' cis''4 dis''4 ~",
    r"dis''8) cis''16( dis'' e''8 fis'' ~ fis''4 a''8 gis''16 fis''",
    r"e''4.) cis''8( b'16 cis'' e'' fis'' gis'' a'' b'' cis'''",
    r"dis'''4.) b''8( a''16 fis'' e'' cis'' b'8 a')",
    r"r8 fis'16( a' b' cis'' e'' fis'' e'' cis'' b' a' b' cis'' e'' fis''",
    r"a''16 fis'' e'' cis'' e'' fis'' a'' b'' cis'''8) b''16( a'' fis'' e'' cis'' b'",
    r"a'4.) fis'8( a'16 b' cis'' dis'' e'' fis'' gis'' a''",
    r"b''4.) a''8( gis''16 fis'' e'' dis'' cis'' b' a' gis'",
]
SOLO_2 = [
    r"a'4) r8 a'8( d''8 e''4 fis''8 ~",
    r"fis''8) e''16( fis'' g''8 a'' ~ a''4 c'''8 b''16 a''",
    r"\tuplet 6/4 { g''16 a'' g'' e'' d'' e'' } \tuplet 6/4 { g'' a'' g'' e'' d'' e'' } "
    r"\tuplet 6/4 { a'' b'' a'' fis'' e'' fis'' } \tuplet 6/4 { a'' b'' a'' fis'' e'' fis'' }",
    r"c'''2) b''16( a'' g'' e'' d'' c'' a'8)",
    r"r8 e'16( g' a' c'' d'' e'' g'' a'' c''' d''' e'''4)",
    r"e'''8-> r e'''8->( d'''16 c''' a''8) c'''8->( a''16 g'' e''8)",
    r"d''16( e'' g'' a'' c''' a'' g'' e'' d'' e'' g'' a'' b'' c''' d''' e'''",
    r"e'''4) d'''16( c''' a'' g'' e'' d'' c'' a' g'8) r8",
]
# Bars 41 to 48, in C: two bars of the saxophone, two bars of the guitar, two times.
# The saxophone uses its lowest and its highest notes.
SAX_TURN_1 = [
    r"bes,8-> bes,-> r8 c16( es f g bes c' es' f' g' bes'",
    r"c''16 es'' f'' es'' c'' bes' g'8->) ~ g'8 f'16( es' c'8 bes)",
]
GUITAR_TURN_1 = [
    r"\tuplet 6/4 { c''16( es'' f'' g'' f'' es'' } \tuplet 6/4 { c'' es'' f'' g'' bes'' g'' } "
    r"\tuplet 6/4 { f'' g'' bes'' c''' bes'' g'' } \tuplet 6/4 { f'' g'' bes'' c''' d''' c''' }",
    r"es'''4->) d'''16( c''' bes'' g'' f''8 es''16 c'' bes'8 c'')",
]
SAX_TURN_2 = [
    r"f''4->( ~ f''16 es'' c'' bes' g'8) c8-> r c->",
    r"r16 c( es g c' es' g' bes' c'' es'' f''8 ~ f''4)",
]
# The last two bars of the guitar go down to the first note of the third line (E-flat).
GUITAR_TURN_2 = [
    r"c'''16( bes'' g'' f'' es'' f'' g'' bes'' c''' d''' es''' d''' c''' bes'' g'' f''",
    r"es''16 c'' bes' g' f' es' c' bes g f es f g f es d)",
]


def third_line() -> list[str]:
    """Return the third line for all lead players: seven bars of sixteenth notes in E-flat.

    The line is the first line of the work (two bars of 14/8), a major third
    lower, and then its mirror. It is written again in bars of four beats.
    The last note of the mirror is F-sharp: the root of the next riff.
    """
    line = [tools.tr(bar, -4) for bar in m.LINE_1]
    both = line + [tools.invert(bar, "es'") for bar in line]
    names = [
        element.pitches[0].pitch.name
        for bar in both
        for element in music.parse(bar).children
        if isinstance(element, music.Note)
    ]
    size = 16
    return [
        f"{names[start]}16( " + " ".join(names[start + 1 : start + size]) + ")"
        for start in range(0, len(names), size)
    ]


def hit_bars(note: str) -> list[str]:
    """Return the last three bars: a stroke on each dotted quarter note (eight strokes).

    The dotted quarter note is the beat of the next part. The strokes become
    softer: the next part starts mezzo forte, with no drop of the loudness
    at the bar line.
    """
    return [
        f"{note}4.->\\ff\\> {note}4.-> {note}4-> ~",
        f"{note}8 {note}4.-> {note}4.-> {note}8-> ~",
        f"{note}4 {note}4.-> {note}4.->\\mf",
    ]


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]
    guitar, bass = guitar_table(), bass_table()
    whole = "a___ ____"

    # ------------------------------------------------- K: the riff
    s = Bars(work, 24, COMMON)
    structure.mark(s.bar(1), "K")
    structure.tempo(s.bar(1), 1, m.FAST, "Heavy, in four")
    bars = RIFF_HALF + RIFF_GALLOP + RIFF_FAST
    s.set("gtr", riff(bars, guitar), r"\ff\highgain")
    s.set("bass", riff(bars, bass), r"\ff")
    drums = (
        # Half time. The kick drum plays the riff, with runs of the two feet.
        kit_bars(
            ("cy", CHINA), HALF,
            [strokes(RIFF_HALF[0]), burst(strokes(RIFF_HALF[1]), 2), strokes(RIFF_HALF[2]),
             strokes(RIFF_HALF[3]), strokes(RIFF_HALF[4]), burst(strokes(RIFF_HALF[5]), 2),
             burst(strokes(RIFF_HALF[6]), 3), strokes(RIFF_HALF[7])],
            "half", crash={1: "c", 5: "d"}, fills={4: "one feet", 8: "two toms"}, ghosts=0.08,
        )
        # The gallop: open hi-hat, then the bell of the ride cymbal.
        + kit_bars(("hh", OPEN_HATS), BACK, [strokes(bar) for bar in RIFF_GALLOP[:4]], "gallop 1",
                   crash={1: "c"}, fills={4: "one snare"}, ghosts=0.12)
        + kit_bars(("rd", BELL), BACK, [strokes(bar) for bar in RIFF_GALLOP[4:]], "gallop 2",
                   crash={1: "d"}, fills={4: "two feet"}, ghosts=0.12)
        # Sixteenth notes of the two feet.
        + kit_bars(("cy", CHINA), BACK, [FEET, FEET, "xxxx xxxx xxxx xxx-", FEET, FEET, FEET],
                   "fast", crash={1: "c", 3: "d", 5: "c"}, fills={2: "one snare", 4: "one six",
                                                                  6: "one toms"})
        + [kit_bar(("cy", CHINA), "o-o- o-o- o-o- o-o-", FEET, crash="c"),
           kit_bar(("cy", "---- ---- ---- ----"), "oooo oooo OOOO OOOO", "x-x- x-x- xxxx xxxx")]
    )  # fmt: skip
    s.set("drums", drums, r"\ff")
    # The low synthesizer makes the first beat of each second bar larger.
    sub = low_notes(["fis,,", None] * 11, "a___ ----") + [r"fis,,2 b,,2", r"cis,2 dis,2"]
    s.set("sbass", sub, r"\mf", r'\switch "bass sub"')
    s.set("eperc", r"ges,,1\f | R1*21 | e,,1\mf\< ~ | e,,1\f |")
    # The saxophone: low strokes with the chords of the riff, a melody above the gallop,
    # low strokes again, and one run through three octaves into the solo of the guitar.
    s.set(
        "tsax",
        [None, None, None, None, None, r"r2 b,8.->\ff cis8.-> dis8->", None,
         r"g8-> g-> r4 e4-> c8-> c->",
         tools.first(SAX_MELODY[0], r"\f\normaltone", note=True), *SAX_MELODY[1:4],
         *[tools.octave(bar, -1) for bar in SAX_MELODY[4:]],
         None, None, r"fis8.->\ff\growl fis8.-> fis8-> r2",
         r"dis8.-> dis8.-> dis8-> cis8.-> cis8.-> b,8->",
         None, r"g8.-> g8.-> g8-> e8.-> e8.-> c8->", None,
         r"a,16(\< b, cis e fis a b cis' e' fis' a' b' cis'' dis'' e'' eis''\ff)"],
        r"\growl",
    )  # fmt: skip
    # The horns: the chords of the riff, with no third.
    horn_bars = [None] * 8
    horn_bars += ["P_-- ---- ---- ----", accents(RIFF_GALLOP[1]), None, accents(RIFF_GALLOP[3]),
                  "P_-- ---- ---- ----", accents(RIFF_GALLOP[5]), None, accents(RIFF_GALLOP[7])]  # fmt: skip
    horn_bars += ["P_-P _-P_ ---- ----", accents(RIFF_FAST[1]), "P_-P _-P_ ---- ----",
                  accents(RIFF_FAST[3]), "P_-P _-P_ ---- ----", accents(RIFF_FAST[5]),
                  RIFF_FAST[6], "N_N_ N_N_ O_O_ O_O_"]  # fmt: skip
    for player, table in horn_tables(30).items():
        bars = [None if bar is None else patterns.pitched(bar, BEATS, table) for bar in horn_bars]
        if player == "tpt":
            # The trumpet has the rise of the melody to the high A: the saxophone of the
            # audio stops at F5, and plays these four bars one octave lower.
            bars[12:16] = SAX_MELODY[4:]
        s.set(player, bars, r"\ff")
    cues.append(Cue("mercury3-548", s.bar(1), 1, offset=72.1, text="Roger. Two and a half G.",
                    seconds=1.9, gain_db=-11.0, radio=True, pan=-0.3))  # fmt: skip
    s.close()

    # ------------------------------------------------- L: the solo of the guitar
    s = Bars(work, 24, COMMON)
    structure.mark(s.bar(1), "L")
    roots = ["fis,,", "a,,", "c,"]
    under = [RIFF_SOLO_1, RIFF_SOLO_2, RIFF_SOLO_3]
    # The band is one step softer under the solo. It comes back to full force when the
    # heavy guitar comes back (bar 17 of the section).
    low = [bar for root, part in zip(roots, under, strict=True)
           for bar in riff(part, bass_table(root))]  # fmt: skip
    low[16] = tools.first(low[16], r"\ff", note=True)
    s.set("bass", low, r"\f")
    octaves = [bar for root, part in zip(roots, under, strict=True)
               for bar in riff(part, keys_table(root))]  # fmt: skip
    octaves[16] = tools.first(octaves[16], r"\f", note=True)
    s.set("keys.lh", octaves, r"\mf")
    heavy = riff(RIFF_SOLO_3, guitar_table("c,"))
    # The solo and the first turn sound one octave lower than they were written at
    # first: the highest octave of the guitar is thin, and the owner wants a full sound.
    turn_1 = [tools.octave(bar, -1) for bar in GUITAR_TURN_1]
    turns = [
        tools.first(heavy[0], r"\ff\highgain", note=True), heavy[1],
        tools.first(turn_1[0], r"\leadtone\pmoff", note=True), turn_1[1],
        tools.first(heavy[4], r"\highgain", note=True), heavy[5],
        tools.first(GUITAR_TURN_2[0], r"\leadtone\pmoff", note=True), GUITAR_TURN_2[1],
    ]  # fmt: skip
    solo = [tools.octave(bar, -1) for bar in SOLO_1 + SOLO_2]
    s.set("gtr", solo + turns, r"\f\leadtone\pmoff")
    s.set("tsax", [None] * 11 + [r"r2 r8 e8->\f e-> r", None, None, None,
                                 r"r2 bes,8->\ff bes,-> b,-> b,->",
                                 tools.first(SAX_TURN_1[0], r"\ff", note=True), SAX_TURN_1[1],
                                 None, None, *SAX_TURN_2, None, None])  # fmt: skip
    drums = (
        kit_bars(("rd", BELL), BACK,
                 [strokes(RIFF_SOLO_1[0]), strokes(RIFF_SOLO_1[1]), strokes(RIFF_SOLO_1[2]),
                  burst(strokes(RIFF_SOLO_1[3]), 2), strokes(RIFF_SOLO_1[4]),
                  strokes(RIFF_SOLO_1[5]), burst(strokes(RIFF_SOLO_1[6]), 3),
                  strokes(RIFF_SOLO_1[7])],
                 "solo 1", crash={1: "c", 5: "d"}, fills={4: "one toms", 8: "two toms"},
                 ghosts=0.2)
        + kit_bars(("cy", CRASHES), BACK,
                   [strokes(RIFF_SOLO_2[0]), burst(strokes(RIFF_SOLO_2[1]), 3),
                    strokes(RIFF_SOLO_2[2]), burst(strokes(RIFF_SOLO_2[3]), 2),
                    burst(strokes(RIFF_SOLO_2[4]), 1), burst(strokes(RIFF_SOLO_2[5]), 3),
                    burst(strokes(RIFF_SOLO_2[6]), 1, 3), strokes(RIFF_SOLO_2[7])],
                   "solo 2", crash={1: "c", 5: "c"}, fills={4: "one feet", 8: "two feet"},
                   ghosts=0.1)
        + kit_bars(("cy", CHINA), BACK, [FEET] * 8, "turns",
                   crash={1: "c", 3: "d", 5: "c", 7: "d"},
                   fills={2: "one snare", 4: "one six", 6: "one toms", 8: "two six"})
    )  # fmt: skip
    drums[16] = tools.first(drums[16], r"\ff", note=True)
    s.set("drums", drums, r"\f")
    colours = ["F#m11", "F#m11", "Gmaj7#11", "Gmaj7#11", "F#m11", "F#m11", "Amaj7#11", "C7#11",
               "Am11", "Am11", "Bbmaj7#11", "Bbmaj7#11", "Am11", "Am11", "Cmaj7#11", "Eb7#11",
               "Cm11", "Cm11", "Dbmaj7#11", "Dbmaj7#11", "Cm11", "Cm11", "Ebmaj7#11", "D7#11"]  # fmt: skip
    pad = m.pad_bars(colours, whole, HALVES)
    pad[8] = tools.first(pad[8], r"\mf\<", note=True)
    pad[16] = tools.first(pad[16], r"\f", note=True)
    s.set("pad.rh", pad, r"\mp", r'\switch "supersaw"')
    s.set("sbass", low_notes(["fis,,"] * 8 + ["a,,"] * 8 + ["c,"] * 8), r"\mf")
    # The horns: long chords under the second half of the solo, then strokes with the turns.
    long_horns = m.layers([None] * 8 + colours[8:15] + [None] * 9, [whole], m.HORNS, "horns",
                          HALVES)  # fmt: skip
    hits = horn_tables(36, sharps=False)
    for player in m.HORNS:
        stroke = patterns.pitched("P___ ---- ---- ----", BEATS, hits[player])
        parts = long_horns[player][:16] + [stroke, None] * 4
        parts[8] = tools.first(parts[8], r"\mp\<", note=True)
        parts[16] = tools.first(parts[16], r"\ff", note=True)
        s.set(player, parts)
    s.set("eperc", r"R1*22 | e,,1\mf\< ~ | e,,1\f |")
    s.close()

    # ------------------------------------------------- M: the third line, the climb, the end
    s = Bars(work, 22, COMMON)
    structure.mark(s.bar(1), "M")
    line = third_line()
    climb_roots = ["fis,,", "g,,", "as,,", "a,,"]
    climb_guitar, climb_bass = [], []
    for root, pair in zip(climb_roots, RIFF_CLIMB, strict=True):
        climb_guitar += riff(pair, guitar_table(root))
        climb_bass += riff(pair, bass_table(root))
    last = "<bes,, f, bes,>"
    s.set(
        "gtr",
        [*line, r"<fis,, cis, fis,>1\ff\highgain\pmoff", *climb_guitar,
         *riff(RIFF_LAST, guitar_table("bes,,")), *hit_bars(last)],
    )  # fmt: skip
    s.set(
        "bass",
        [*[tools.octave(bar, -2) for bar in line], r"fis,,1", *climb_bass,
         *riff(RIFF_LAST, bass_table("bes,,")), *hit_bars("bes,,")],
        r"\ff",
    )  # fmt: skip
    motto = [
        r"r4. fis'8(\f\< b'4 cis''4 ~", r"cis''4 dis''2.)",
        r"r4. g'8( c''4 d''4 ~", r"d''4 e''2.)",
        r"r4. as'8( des''4 es''4 ~", r"es''4 f''2.)",
        r"r4. a'8( d''4 e''4 ~", r"e''4 fis''4 g''2\ff)",
    ]  # fmt: skip
    s.set("lead", [*[tools.octave(bar, 1) for bar in line], r"fis''1",
                   *[tools.octave(bar, 1) for bar in motto]] + [None] * 6, r"\f",
          r'\switch "lead moog"')  # fmt: skip
    s.set("chip", [*[tools.octave(bar, 2) for bar in line], r"fis'''1"] + [None] * 14, r"\mf",
          r'\switch "chip pulse"')  # fmt: skip
    # The saxophone: the line, then the motto on each root of the climb (the second
    # time it is the motto of the work: G, C, D, E), then the top of the last chord.
    s.set(
        "tsax",
        [*[tools.within(bar, 44, 77) for bar in line], r"fis2 r2", *motto[:6],
         *[tools.octave(bar, -1) for bar in motto[6:]],
         r"f''1 ~", r"f''2 r2", r"g'8.-> g'8.-> g'8-> g'8.-> g'8.-> g'8->",
         *hit_bars("as'")],
        r"\ff\normaltone",
    )  # fmt: skip
    drums = (
        kit_bars(("cy", CHINA), BACK, [FEET, FEET, "xxxx xxxx xxxx xxx-", FEET, FEET,
                                       "xxxx xxx- xxxx xxxx", FEET, FEET], "line",
                 crash={1: "c", 3: "d", 5: "c", 7: "d"}, fills={4: "one snare", 8: "two build"})
        # The climb: the snare drum on each beat.
        + kit_bars(("cy", CHINA), FOUR, [FEET] * 8, "climb",
                   crash={number: "cd"[number % 2] for number in range(1, 9)},
                   fills={4: "one six", 8: "two build"})
        + [kit_bar(("cy", CHINA), EIGHTHS, FEET, crash="c"),
           kit_bar(("cy", "---- ---- ---- ----"), "oooo oooo OOOO OOOO", "x-x- x-x- x-x- x-x-"),
           # The strokes of all players, and the snare drum between them.
           Groove("cy C--C --C- C--C --C-\nsn -oo- oo-o -oo- oo-o\nbd x--x --x- x--x --x-",
                  BEATS).text(),
           # A stroke on each dotted quarter note. The kick drum plays each dotted eighth
           # note: these are the eighth notes of the next part.
           tools.first(
               Groove("cy C--- --C- ---- C---\nsn O--- --O- ---- O---\nbd x--x --x- -x-- x--x",
                      BEATS).text(), r"\ff\>", note=True),
           Groove("cy --C- ---- C--- --C-\nsn --O- ---- O--- --O-\nbd --x- -x-- x--x --x-",
                  BEATS).text(),
           tools.first(
               Groove("cy ---- C--- --C- ----\nsn ---- O--- --O- ----\nbd -x-- x--x --x- -x--",
                      BEATS).text(), r"\mf", note=True)]
    )  # fmt: skip
    s.set("drums", drums, r"\ff")
    rising = ["F#m11", "F#m11", "Gm11", "Gm11", "Abm11", "Abm11", "Am11", "Am11"]
    final = "Bb13sus"
    figure = "A__A __A_ A__A __A_"
    for kind, players, make in (("horns", m.HORNS, m.horn_notes),
                                ("strings", m.STRINGS, m.string_notes)):  # fmt: skip
        parts = m.layers([None] * 8 + rising, [whole], players, kind, HALVES)
        for player, midi in zip(players, make(final), strict=True):
            note = chords.names((midi,), final)
            rows = parts[player]
            rows += [f"{note}1\\ff ~", f"{note}1", patterns.pitched(figure, BEATS, {"a": note}),
                     *hit_bars(note)]  # fmt: skip
            rows[8] = tools.first(rows[8], r"\f\<", note=True)
            s.set(player, rows)
    chord = chords.names(chords.voice(final, 4, low=58, high=82), final)
    # The line has no chords under it: the low synthesizer holds E-flat.
    pad = [None] * 8 + m.pad_bars(rising, whole, HALVES, low=60, high=84)
    pad[8] = tools.first(pad[8], r"\mf\<", note=True)
    close = [f"{chord}1\\ff ~", f"{chord}1", patterns.pitched(figure, BEATS, {"a": chord}),
             *hit_bars(chord)]  # fmt: skip
    s.set("pad.rh", pad + close)
    s.set("keys.rh", [None] * 16 + close)
    sub = low_notes(["es,,"] * 7 + ["fis,,"] + [root for root in climb_roots for _ in range(2)]
                    + ["bes,,"] * 2)  # fmt: skip
    sub += [patterns.pitched(figure, BEATS, {"a": "bes,,"}), *hit_bars("bes,,")]
    s.set("sbass", sub, r"\f")
    s.set("eperc", r"ges,,1\f | R1*13 | e,,1\mf\< ~ | e,,1\f | ges,,1\ff | R1*5 |")
    s.close()
    structure.double_bar(s.section.last_bar)
