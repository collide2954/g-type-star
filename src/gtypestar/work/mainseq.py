"""Part 3: the main sequence. The star burns hydrogen in a stable state.

This is the longest part. It has the theme, a breakbeat with the bridge
melody, the solos, a quiet middle, and the return of the theme with a new
division of the pulses.

The owner heard the first two versions and said: "Everything from 2:30-4:30
is pretty boring." These two minutes (the marks D, E, and F) had the theme
a second time above the same chords, a soft bridge with long notes, and a
solo that started slowly. Now each of them has an idea of its own:

- D: the band plays a riff against the theme, the horns answer, and the
  chords of the second half go up.
- E: the bar of seven quarter notes becomes a drum-and-bass beat (the tempo
  of the work, 175, is the tempo of that style). The melody of the bridge is
  above it, the electric piano has a short solo, and a snare roll leads on.
- F: the saxophone and the guitar take turns: four bars each, two bars
  each, one bar each. Then all lead players have the second fast line.

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
from . import material as m
from .material import Bars

# Rhythms of the electric piano for one bar: the letter `a` is the chord.
COMPS = [
    "---a__ ------ a___ ---a__ ______",
    "a_____ ---a__ ---- a__-a_ ______",
    "---a__ ___--- -a__ ------ a_____",
    "a__--- ---a__ a_-- ---a__ ---a__",
    "---a__ ------ a___ ------ -a____",
    "a_____ ______ ---- ---a__ a__---",
]
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
# Soft forms for the bridge: long notes.
COMPS_SOFT = [
    "a_____ ______ ____ a_____ ______",
    "---a__ ______ ____ ---a__ ______",
    "a_____ ______ a___ ______ ---a__",
]
BASS_SOFT = [
    "a_____ ______ c___ a_____ ___e_c",
    "a_____ ___c__ b___ ______ a__c_e",
    "a_____ ______ a_c_ b_____ ___c__",
]
# Forms with five notes in each long pulse and three in the short pulse.
COMPS_FIVE = [
    "--a__ _____ a__ --a__ _____",
    "a____ --a__ --- a__a_ _____",
    "--a__ __--- a__ ----- a____",
]
BASS_FIVE = [
    "a__xb --c_e b_a a_x_c -e_c_",
    "a__xb -xc_e b_a a__xc b_c_e",
    "a_x_b --c_e b-a a_c_e b_c_h",
]
# Figures of the guitar: three notes of the chord (a, b, c) in sixteenth notes.
PICKS = [
    "abcabc abcabc abca bcabca bcabca",
    "a-ca-c abcabc a-c- bcabca b-ab--",
    "abc-bc a-cabc abca -cab-a bcabca",
    "ab-ab- abcabc -bca bcabca bca---",
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
# The drums of the riff: the kick drum plays the notes of the first and the fourth pulse.
RIFF_GROOVE = Groove(
    """
    hh  x-x-x- x-x-o- x-x- x-x-x- x-x-o-
    sn  ------ o--g-- ---g ------ o--g--
    bd  x-xx-x ------ x--- x-xx-- ---x--
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
# bars each, then two bars each (two times), then one bar each (two times).
SAX_TURNS = {
    1: m.SAX_SOLO[8],
    2: m.SAX_SOLO[9],
    3: m.SAX_SOLO[10],
    4: m.SAX_SOLO[11],
    9: m.SAX_SOLO[12],
    10: m.SAX_SOLO[13],
    # A long high B, a fall of two octaves, and the start of a rise.
    13: r"b''4.->( ~ b''4 a''16 g'' e''8 d''16 b' a'8 g'16 e' d' b a8) b16( d' e' g')",
    # The rise goes on to the highest note of the saxophone.
    14: r"bes'16( c'' d'' f'' g'' bes'' a'' g'' f'' d'' c'' bes' g'8) bes'16( d'' f''8 g''16 "
    r"bes'' c'''4.->) r8",
    17: r"g'16( b' d'' e'' g'' a'' b''8->) a''16( g'' e'' d'' b' a' g'8) a'16( b' d'' e'' g''8 "
    r"e''16 d'' b'8 d'')",
    19: m.SAX_SOLO[14],
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
    # The last bar before the line: chords of A minor and G, six notes in each beat.
    20: r"\tuplet 6/4 { a16( c' e' a' e' c' } \tuplet 6/4 { b d' g' b' g' d' } "
    r"\tuplet 6/4 { c' e' a' c'' a' e' } \tuplet 6/4 { d' g' b' d'' b' g' } "
    r"\tuplet 6/4 { e' a' c'' e'' c'' a' } \tuplet 6/4 { g' b' d'' g'' d'' b' } "
    r"\tuplet 6/4 { a' c'' e'' a'' e'' c'') }",
}
# The short chords of the band in the bars with turns of one bar.
HITS = [
    "A--a-- ------ ---- A--a-- ------",
    "A----- ---a-- ---- A--a-- ------",
    "A--a-- ------ ---- A----- ---a--",
    "A--a-- ------ a___ A--a-- A_____",
]


def _bass(symbols: list[str], key: str, shapes: list[str] = BASS) -> list[str]:
    """Return one bar of bass for each chord. The figure changes from bar to bar."""
    source = m.random("bass", key)
    bars = []
    recent: list[int] = []
    for symbol in symbols:
        choice = int(source.integers(0, len(shapes)))
        while choice in recent[-min(3, len(shapes) - 1) :]:
            choice = (choice + 1) % len(shapes)
        recent.append(choice)
        bars.append(patterns.pitched(shapes[choice], m.CLAVE, m.bass_table(symbol)))
    return bars


def _keys(
    symbols: list[str], key: str, low: int = 55, high: int = 77, patterns_: list[str] = COMPS
) -> list[str]:
    """Return one bar of the electric piano for each chord."""
    source = m.random("keys", key)
    bars = []
    before = None
    for symbol in symbols:
        voicing = chords.voice(symbol, 4, low=low, high=high, before=before)
        before = voicing
        pattern = patterns_[int(source.integers(0, len(patterns_)))]
        bars.append(patterns.pitched(pattern, m.CLAVE, {"a": chords.names(voicing, symbol)}))
    return bars


def _picks(symbols: list[str], key: str) -> list[str]:
    """Return one bar of the guitar figure for each chord."""
    source = m.random("guitar", key)
    bars = []
    for symbol in symbols:
        notes = chords.voice(symbol, 3, low=62, high=81)
        table = {
            letter: chords.names((midi,), symbol) for letter, midi in zip("abc", notes, strict=True)
        }
        bars.append(patterns.pitched(PICKS[int(source.integers(0, len(PICKS)))], m.CLAVE, table))
    return bars


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    # ------------------------------------------------- the theme, first time
    s = Bars(work, 16)
    structure.mark(s.bar(1), "C")
    symbols = m.LOOP_A * 4
    s.set("tsax", m.THEME_LOW + m.THEME_LOW_RISE, r"\mf")
    s.set(
        "drums",
        m.drum_bars(m.MAIN, 16, "theme 1", crash=(1, 9), fills={8: "snare 1", 16: "toms 2"}),
        r"\f",
    )
    s.set("bass", _bass(symbols, "theme 1"), r"\f\fingers")
    s.set("keys.rh", _keys(symbols, "theme 1"), r"\mf")
    picks = _picks(symbols[8:], "theme 1")
    picks[6] = tools.first(picks[6], r"\<", note=True)  # a crescendo into the second statement
    s.set("gtr", [None] * 8 + picks, r"\mp\clean\pm")
    # The seam with the ignition: its arpeggios and its low tone go on and become soft.
    table = {"a": "g''", "b": "b''", "c": "d'''", "d": "e'''", "e": "g'''"}
    tail = [
        patterns.pitched("abcdec abcdec abcd ecabcd ecabcd", m.CLAVE, table),
        tools.first(patterns.pitched("a-c-e- --b-d- a--- ---c-- e-----", m.CLAVE, table), r"\p",
                    note=True),
    ]  # fmt: skip
    s.set("chip", tail + [None] * 14, r"\mp", r'\switch "chip pulse"')
    s.set("sbass", r'\switch "bass sub" g,,1..\mf\> | R1*14/8\! | R1*14/8*14 |')
    # The seam with the second statement: noise that rises in the last bar.
    s.set("eperc", r"R1*14/8*15 | e,,1..\mp\< |")
    s.close()

    # ------------------------------------------------- D: the theme against a riff
    s = Bars(work, 16)
    structure.mark(s.bar(1), "D")
    climb = [*m.LOOP_A, *m.LOOP_A, *CLIMB]  # the chords of the 16 bars
    s.set("tsax", m.THEME_WIDE + m.THEME_CLOSE_WIDE, r"\f")
    riff_drums = m.drum_bars(RIFF_GROOVE, 16, "riff", amount=0.9, crash=(1, 3, 9, 11, 13),
                             fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "kicks 2"},
                             grooves={n: m.MAIN_RIDE for n in range(5, 9)})  # fmt: skip
    s.set("drums", riff_drums, r"\f")
    # Bars 1 to 4 and 9 to 14: the riff. Bars 5 to 8: long notes. Bars 15 and 16: the line.
    order = [0, 1, 2, 3, None, None, None, None, 4, 0, 5, 2, 1, 3]
    riff = [
        patterns.pitched(BASS_OPEN[bar - 4] if form is None else RIFFS[form], m.CLAVE,
                         m.bass_table(climb[bar]))
        for bar, form in enumerate(order)
    ]  # fmt: skip
    s.set("bass", riff + [tools.octave(b, -2) for b in m.LINE_1], r"\f")
    # The guitar: the riff one octave above the bass, then high notes of the chords
    # with a clean sound, then the riff, then the line with the lead sound.
    heavy = [tools.octave(bar, 1) for bar in riff]
    picks = _picks(m.LOOP_A, "theme 2")
    line = [tools.first(m.LINE_1[0], r"\leadtone\pmoff", note=True), m.LINE_1[1]]
    guitar = [tools.first(bar, r"\crunch\pm", note=True) if n in (0, 8) else bar
              for n, bar in enumerate(heavy)]  # fmt: skip
    guitar[4:8] = [tools.first(picks[0], r"\clean\mp", note=True), *picks[1:]]
    guitar[8] = tools.first(guitar[8], r"\f", note=True)
    s.set("gtr", guitar + line, r"\f")
    # The electric piano plays chords on the accents of the riff, and its usual figures
    # in the four bars between.
    keys = [m.comp(symbol, HITS[n % 4], low=55, high=77)[0] for n, symbol in enumerate(climb)]
    keys[4:8] = _keys(m.LOOP_A, "theme 2")
    s.set("keys.rh", keys, r"\mf")
    shouts = m.layers([None] * 4 + m.LOOP_A + [None] * 8, SHOUTS, m.HORNS, "horns")
    swell = m.layers([None] * 10 + CLIMB[2:6] + [None] * 2,
                     ["a_____ ______ ____ ______ ______"], m.HORNS, "horns")  # fmt: skip
    for player in m.HORNS:
        bars = [a or b for a, b in zip(shouts[player], swell[player], strict=True)]
        bars[10] = tools.first(bars[10], r"\mp\<", note=True)
        s.set(player, bars, r"\f")
    strings = m.layers([None] * 8 + CLIMB[:6] + [None] * 2,
                       ["a_____ ______ ____ ______ ______"], m.STRINGS, "strings")  # fmt: skip
    for player, bars in strings.items():
        s.set(player, bars, r"\mp\<")
    claps = drums.steps("ms  ------ c----- ---- ------ c-----", m.CLAVE)
    s.set("eperc", [claps] * 16, r"\mf")
    # The first line for all lead players: the last two bars.
    s.set("lead", [None] * 14 + [tools.octave(bar, 1) for bar in m.LINE_1], r"\f")
    s.set("chip", [None] * 14 + [tools.octave(bar, 2) for bar in m.LINE_1], r"\mf")
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
    low: list[str | None] = [*_bass(symbols[:14], "break", BASS_BREAK)]
    low[:2] = [None, None]
    climb_bass = [
        patterns.pitched("a-a-a- a-a-a- a-a- b-b-b- b-b-b-", m.CLAVE, m.bass_table("Cm11")),
        patterns.pitched("a-a-a- a-a-a- aaaa aaaaaa aaaaaa", m.CLAVE, m.bass_table("D13b9")),
    ]
    s.set("bass", low + climb_bass, r"\f")
    s.set("sbass", m.roots(symbols[:14], "a_____ ______ ____ a_____ ______") + [None, None],
          r"\mf", r'\switch "bass reese"')  # fmt: skip
    stabs: list[str | None] = [*_keys(symbols[:12], "break", patterns_=COMPS_BREAK)]
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
        swell = m.layers([None] * 14 + symbols[14:], ["a_____ ______ ____ ______ ______"],
                         players, kind)  # fmt: skip
        for player, bars in swell.items():
            s.set(player, bars, r"\mp\<")
    chug = {"a": r"d, \pm"}
    s.set("gtr", [None] * 15 + [patterns.pitched("a-a-a- a-a-a- aaaa aaaaaa aaaaaa", m.CLAVE,
                                                 chug)], r"\mf\<\crunch")  # fmt: skip
    machine = [drums.steps(MACHINE_BREAK[n % 2], m.CLAVE) for n in range(8)]
    # The seams: noise that falls and a low drop at the start; noise that rises at the end.
    s.set("eperc", [r"<< { f,,1..\mp } \\ { es,,1..\mp } >>", None, None, None, *machine,
                    None, None, None, r"e,,1..\mf\<"])  # fmt: skip
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
    s.set("tsax", sax + m.LINE_2, r"\f")
    s.set("gtr", guitar_solo + m.LINE_2, r"\f")
    s.set(
        "drums",
        m.drum_bars(m.MAIN_RIDE, 24, "sax solo", amount=1.4,
                    crash=(1, 5, 9, 13, 17, 18, 19, 20, 21, 23),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "snare 2",
                           17: "snare 1", 18: "toms 1", 19: "snare 1", 20: "kicks 2",
                           24: "toms 2"},
                    grooves={n: m.MAIN_OPEN for n in range(9, 25)}),
        r"\f",
    )  # fmt: skip
    walk = _bass(symbols, "sax solo")[:20]
    s.set("bass", walk + [tools.octave(b, -2) for b in m.LINE_2], r"\f")
    keys = _keys(symbols, "sax solo")
    keys[16:20] = [m.comp(symbol, HITS[n], low=55, high=77)[0]
                   for n, symbol in enumerate(symbols[16:20])]  # fmt: skip
    s.set("keys.rh", keys, r"\mf")
    s.set("pad.rh", [None] * 8 + m.pad_bars(symbols[8:]), r"\mp\<", r'\switch "pad warm"')
    stabs = ["------ ------ ---- A--a-- ------", "------ ---A-- ---- ------ A-----",
             "---A-- ------ a___ ------ ------", "------ ------ ---- ---A-a A_____"]  # fmt: skip
    answers = m.layers([None] * 8 + symbols[8:16] + [None] * 8, stabs, m.HORNS, "horns")
    hits = m.layers([None] * 16 + symbols[16:20] + [None] * 4, HITS, m.HORNS, "horns")
    for player in m.HORNS:
        bars = [a or b for a, b in zip(answers[player], hits[player], strict=True)]
        bars[16] = tools.first(bars[16] or "", r"\ff", note=True)
        s.set(player, bars, r"\f")
    s.set("eperc", [r"ges,,1..\mf", *[None] * 7, *[claps] * 16])
    # The second line: the last four bars.
    s.set("lead", [None] * 20 + [tools.octave(bar, 1) for bar in m.LINE_2], r"\f")
    s.set("chip", [None] * 20 + [tools.octave(bar, 2) for bar in m.LINE_2], r"\mf")
    s.close()

    # ------------------------------------------------- bass and drums take turns
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
    # In the last bar the bass leads down by step to the root of the quiet middle.
    s.set("bass", [m.BASS_SOLO[0], m.BASS_SOLO[1], None, None, m.BASS_SOLO[2], m.BASS_SOLO[3],
                   None, r"r4. r4. r4 e8\mp( d b, a,4.)"], r"\f")  # fmt: skip
    hits = ["A_____ ------ ---- ------ ------", None, None, None] * 2
    chord_hits = ["Gmaj9", None, None, None, "Cmaj9#11", None, None, None]
    stabs = [None if symbol is None else m.comp(symbol, hit, low=55, high=77)[0]
             for symbol, hit in zip(chord_hits, hits, strict=True)]  # fmt: skip
    # The chord of the quiet middle starts before the bar line and grows from nothing.
    stabs[7] = r"r4. r4. r4 <c' e' g' b'>4.\pp\< ~ <c' e' g' b'>4."
    s.set("keys.rh", stabs, r"\f")
    s.close()

    # ------------------------------------------------- the quiet middle
    s = Bars(work, 16)
    structure.mark(s.bar(1), "H")
    symbols = m.LOOP_A * 4
    s.set("keys.rh", m.pad_bars(symbols, low=55, high=77), r"\p")
    shimmer = []
    for symbol in symbols:
        notes = chords.voice(symbol, 5, low=74, high=96, rootless=False)
        table = {
            letter: chords.names((midi,), symbol)
            for letter, midi in zip("abcde", notes, strict=True)
        }
        shimmer.append(patterns.pitched("abcde abcde abc edcba edcba", m.CLAVE, table))
    s.set("chip", shimmer, r"\pp", r'\switch "chip pulse 25"')
    s.set("bass", m.roots(symbols, "a_____ ______ ____ ______ ___c__", octave=1), r"\p")
    s.set(
        "drums",
        [None] * 4 + m.drum_bars(m.MORPH_HALF, 12, "middle", amount=0.5, crash=(),
                                 fills={12: "five toms 2"}),
        r"\p\<",
    )  # fmt: skip
    s.set("tsax", [None] * 8 + m.THEME_DEEP, r"\p\subtone")
    strings = m.layers([None] * 8 + symbols[8:], ["a_____ ______ ____ ______ ______"], m.STRINGS,
                       "strings")  # fmt: skip
    for player, bars in strings.items():
        s.set(player, bars, r"\pp\<")
    # The seam: the low guitar notes, the chords and the noise of the next part start in
    # the last bars and grow.
    early = {"a": r"g,, \pm"}
    s.set("gtr", [None] * 15 + [patterns.pitched("a-a-a a-a-a aaa aaaaa aaaaa", m.CLAVE, early)],
          r"\p\<\crunch")  # fmt: skip
    s.set("pad.rh", [None] * 14 + m.pad_bars(symbols[14:]), r"\pp\<", r'\switch "supersaw"')
    s.set("eperc", r"R1*14/8*15 | e,,1..\p\< |")
    s.close()

    # ------------------------------------------------- the theme with the new division
    s = Bars(work, 16)
    structure.mark(s.bar(1), "J")
    s.set("tsax", m.THEME_LEAPS, r"\f\normaltone")
    s.set(
        "drums",
        m.drum_bars(m.MORPH, 16, "morph", amount=1.0, crash=(1, 5, 9, 13),
                    fills={4: "five 1", 8: "five toms 2", 12: "five 1", 16: "five 2"}),
        r"\f",
    )  # fmt: skip
    bass = _bass(symbols, "morph", BASS_FIVE)
    # The seam with the flares: the last bar goes down by step (A, G) to the F-sharp of
    # the next part, the guitar plays all notes of the bar and grows, and noise rises.
    bass[15] = patterns.pitched("a__xb --c_e b_a a_x_c h_h__", m.CLAVE, m.bass_table(symbols[15]))
    s.set("bass", bass, r"\f")
    s.set("keys.rh", _keys(symbols, "morph", patterns_=COMPS_FIVE), r"\mf")
    chug = {"a": r"g,, \pm", "b": "g,"}
    chugs = ["aaaaa a-a-a aaa aaaaa a-ab-", "aaaaa aa-aa a-a aaaaa aab--",
             "a-aaa aaaaa aaa a-a-a aaaaa", "aaaaa a-a-a aab aaaaa a-a--"]  # fmt: skip
    guitar = [patterns.pitched(chugs[n % 4], m.CLAVE, chug) for n in range(15)]
    guitar.append(tools.first(patterns.pitched("aaaaa aaaaa aaa aaaaa aaaaa", m.CLAVE, chug),
                              r"\<", note=True))  # fmt: skip
    s.set("gtr", guitar, r"\f\crunch")
    s.set("pad.rh", m.pad_bars(symbols), r"\mf", r'\switch "supersaw"')
    horns = m.layers([None] * 8 + symbols[8:], ["a_____ ______ ____ ______ ______"], m.HORNS,
                     "horns")  # fmt: skip
    for player, bars in horns.items():
        s.set(player, bars, r"\mf\<")
    s.set("eperc", [claps] * 15 + [r"<< { " + claps + r" } \\ { e,,1..\mf\< } >>"], r"\mf")
    s.close()
    structure.double_bar(s.section.last_bar)
