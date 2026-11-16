"""Part 3: the main sequence. The star burns hydrogen in a stable state.

This is the longest part. It has the theme, the bridge, the solos, a quiet
middle, and the return of the theme with a new division of the pulses.

Style profile: "Groove" (see research/tables/profiles.csv). Three speeds at
the same time: kick and snare far apart, a fast grid of sixteenth notes, and
a slow melody.
"""

from __future__ import annotations

from ..compose import chords, patterns, tools
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

    # ------------------------------------------------- the theme, second time
    s = Bars(work, 16)
    structure.mark(s.bar(1), "D")
    s.set("tsax", m.THEME_WIDE + m.THEME_CLOSE_WIDE, r"\f")
    s.set(
        "drums",
        m.drum_bars(m.MAIN_OPEN, 16, "theme 2", amount=1.2, crash=(1, 5, 9, 13),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "kicks 2"}),
        r"\f",
    )  # fmt: skip
    line = [tools.first(m.LINE_1[0], r"\leadtone\pmoff", note=True), m.LINE_1[1]]
    s.set("bass", _bass(symbols, "theme 2")[:14] + [tools.octave(b, -2) for b in m.LINE_1], r"\f")
    s.set("keys.rh", _keys(symbols, "theme 2"), r"\mf")
    s.set("gtr", _picks(symbols, "theme 2")[:14] + line, r"\mf\clean\pm")
    claps = drums.steps("ms  ------ c----- ---- ------ c-----", m.CLAVE)
    s.set("eperc", [claps] * 16, r"\mf")
    # The first line for all lead players: the last two bars.
    s.set("lead", [None] * 14 + [tools.octave(bar, 1) for bar in m.LINE_1], r"\f")
    s.set("chip", [None] * 14 + [tools.octave(bar, 2) for bar in m.LINE_1], r"\mf")
    s.close()

    # ------------------------------------------------- the bridge
    s = Bars(work, 16)
    structure.mark(s.bar(1), "E")
    symbols = m.LOOP_B * 3 + ["Ebmaj9", "Bbadd9/D", "Cm11", "D13b9"]
    s.set("gtr", m.BRIDGE + _picks(symbols[8:], "bridge"), r"\mf\clean\pmoff")
    s.set("tsax", [None] * 8 + [tools.octave(bar, -1) for bar in m.BRIDGE], r"\mf")
    s.set(
        "drums",
        m.drum_bars(m.HALF, 16, "bridge", amount=0.8, crash=(1, 9), fills={8: "linear 1",
                    16: "toms 2"}, grooves={n: m.MAIN_RIDE for n in range(9, 17)}),
        r"\mf",
    )  # fmt: skip
    s.set("bass", _bass(symbols, "bridge", BASS_SOFT), r"\mf")
    s.set("keys.rh", _keys(symbols, "bridge", patterns_=COMPS_SOFT), r"\mp")
    strings = m.layers(symbols, ["a_____ ______ ____ ______ ______"], m.STRINGS, "strings")
    for player, bars in strings.items():
        s.set(player, bars, r"\p\<")
    s.set("pad.rh", [None] * 8 + m.pad_bars(symbols[8:], low=60, high=84), r"\p",
          r'\switch "pad glass"')  # fmt: skip
    horns = m.layers([None] * 12 + symbols[12:], ["a_____ ______ ____ ______ ______"], m.HORNS,
                     "horns")  # fmt: skip
    for player, bars in horns.items():
        s.set(player, bars, r"\p\<")
    # The seams: the bridge starts with noise that falls and a low drop, and it ends
    # with noise that rises into the solo.
    s.set("eperc", r"<< { f,,1..\mp } \\ { es,,1..\mp } >> | R1*14/8*14 | e,,1..\mp\< |")
    s.close()

    # ------------------------------------------------- the solo of the saxophone
    s = Bars(work, 24)
    structure.mark(s.bar(1), "F")
    symbols = m.LOOP_A * 6
    s.set("tsax", m.SAX_SOLO + m.LINE_2, r"\mf")
    s.set(
        "drums",
        m.drum_bars(m.MAIN_RIDE, 24, "sax solo", amount=1.4, crash=(1, 9, 13, 17, 21),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "snare 2",
                           20: "kicks 2", 24: "toms 2"},
                    grooves={n: m.MAIN_OPEN for n in range(13, 25)}),
        r"\f",
    )  # fmt: skip
    line = [tools.first(m.LINE_2[0], r"\leadtone\pmoff", note=True), *m.LINE_2[1:]]
    s.set("bass", _bass(symbols, "sax solo")[:20] + [tools.octave(b, -2) for b in m.LINE_2], r"\f")
    s.set("keys.rh", _keys(symbols, "sax solo"), r"\mf")
    s.set("gtr", _picks(symbols, "sax solo")[:20] + line, r"\mf\clean\pm")
    s.set("pad.rh", [None] * 8 + m.pad_bars(symbols[8:]), r"\mp\<", r'\switch "pad warm"')
    stabs = ["------ ------ ---- A--a-- ------", "------ ---A-- ---- ------ A-----",
             "---A-- ------ a___ ------ ------", "------ ------ ---- ---A-a A_____"]  # fmt: skip
    horns = m.layers([None] * 12 + symbols[12:20] + [None] * 4, stabs, m.HORNS, "horns")
    for player, bars in horns.items():
        s.set(player, bars, r"\f")
    s.set("eperc", [r"ges,,1..\mf", *[None] * 11, *[claps] * 12])
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
