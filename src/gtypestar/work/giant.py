"""Part 5: the red giant. The star swells and becomes cooler.

The long pulse of the main metre becomes the beat of a slow bar of four
beats (116.67 quarter notes in a minute, felt as 58 half notes). The theme
comes back as a chorale of the horns and the strings, one major third
lower, in E-flat. The cymbals play 11 notes in each half note, grouped
2 + 2 + 3 + 2 + 2: this is the method of the title track of the reference
album. Then the harmony goes up by whole tones (E-flat, F, G) under a solo
of the lead synthesizer. At the end, the tension rises on the note D.

Style profile: "Large" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.tape import Cue
from ..compose import chords, patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
HALVES = (4, 4)  # two half notes, in eighth notes
BEATS = (2, 2, 2, 2)

# The theme as a chorale in E-flat, in bars of four beats (16 bars).
CHORALE = [
    r"r2 es'2(",
    r"as'2 bes'2 ~",
    r"bes'2.) r4",
    r"f'2( es'2)",
    r"c''1( ~",
    r"c''2 bes'4 g'4 ~",
    r"g'2 f'2 ~",
    r"f'2) r2",
    r"r2 es'2(",
    r"as'4 bes'4 c''2 ~",
    r"c''2) es''2( ~",
    r"es''2 des''4 bes'4)",
    r"c''1( ~",
    r"c''4 bes'4 g'4 f'4 ~",
    r"f'2 es'2 ~",
    r"es'2.) r4",
]
# The solo of the lead synthesizer: eight bars in F, then eight bars in G.
SOLO_F = [
    r"r4 c''8( d'' f''4 g''4 ~",
    r"g''2) a''8( g'' f'' d''",
    r"es''4 f''8 as'' ~ as''4 g''8 f''",
    r"es''2) r8 c''( es'' f''",
    r"g''8. a''16 ~ a''4 ~ a''8 g'' f'' d''",
    r"e''4 d''8 c'' a'4) c''8( d''",
    r"f''8 g'' bes''4 ~ bes''8 a'' g'' f''",
    r"g''4. e''8 d''4 c''4)",
]
SOLO_G = [
    r"g''16( a'' b'' d''' e''' d''' b'' a'' g''8 e'' d''16 e'' g'' a''",
    r"b''4 ~ b''16) a''( g'' e'' d''8 b' \tuplet 3/2 { d''8 e'' g'' }",
    r"\tuplet 6/4 { bes''16 a'' g'' f'' d'' bes' } \tuplet 6/4 { a'16 bes' d'' f'' g'' a'' } bes''4 ~ bes''8) g''8(",
    r"f''16 g'' a'' bes'' d'''8 bes'' a''16 g'' f'' d'' es''4)",
    r"e''16( fis'' g'' b'' e'''8. d'''16 b''8 g'' fis''16 e'' d'' b'",
    r"c''16 e'' g'' b'' d''' b'' g'' e'' \tuplet 6/4 { fis''16 g'' a'' b'' d''' e''' } fis'''4)",
    r"e'''8( d''' c'''16 a'' g'' e'' d''8 c'' a'4)",
    r"r8 d''16( e'' fis'' a'' b'' d''' e'''4 ~ e'''4)",
]
SHIMMER = m.Groove(
    """
    hh  x-x-x--x-x- x-x-x--x-x-
    sn  ----------- x----------
    bd  x---------- -----------
    """,
    HALVES,
)
SHIMMER_FULL = m.Groove(
    """
    hh  x-x-x--x-x- x-x-x--x-x-
    sn  ----------- o----------
    bd  x---------- ---------x-
    """,
    HALVES,
)
SLOW = m.Groove(
    """
    hh  x-x- x-x- x-x- x-x-
    sn  ---- ---- o--g ----
    bd  x--- --x- ---- -x--
    """,
    BEATS,
)
SLOW_OPEN = m.Groove(
    """
    hh  x-x- x-o- x-x- x-o-
    sn  ---g ---- o--g -g--
    bd  x--x --x- ---- -x-x
    """,
    BEATS,
)
SLOW_FILLS = {
    "slow 1": {"sn": ["o-oo"], "tm": ["----"]},
    "slow 2": {"sn": ["o-g-", "----"], "tm": ["--h-", "mmff"], "bd": ["----", "x-x-"]},
    "slow 3": {"sn": ["oooo", "OOOO"], "bd": ["x---", "x-x-"]},
}
m.FILLS.update(SLOW_FILLS)


def slow_bars(base: m.Groove, count: int, key: str, *, amount: float, crash: tuple, fills: dict):
    """Return bars of a slow groove in four beats. No two bars are the same."""
    source = m.random("giant", key)
    result, seen = [], set()
    for number in range(1, count + 1):
        for _attempt in range(8):
            bar = base.vary(source, amount)
            if number in crash:
                bar.put("cy", 0, 0, "c")
                bar.put("hh", 0, 0, "-")
            if number in fills:
                rows = m.FILLS[fills[number]]
                size = len(next(iter(rows.values())))
                bar.fill(len(base.pulses) - size, rows)
            text = bar.text()
            if text not in seen:
                break
        seen.add(text)
        result.append(text)
    return result


def chord_bars(symbols: list[str], pattern: str, low: int = 55, high: int = 79) -> list[str]:
    return [
        patterns.pitched(pattern, HALVES, {"a": chords.names(voicing, symbol)})
        for symbol, voicing in zip(symbols, chords.progression(symbols, 4, low=low, high=high),
                                   strict=True)
    ]  # fmt: skip


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]

    # ------------------------------------------------- the chorale
    s = Bars(work, 16, COMMON)
    structure.mark(s.bar(1), "N")
    structure.tempo(s.bar(1), 1, m.GIANT, "Broad and heavy (the long pulse is the new beat)")
    loop = ["Ebmaj9", "Ebmaj9", "Bmaj7#11", "Bmaj7#11", "Abmaj9#11", "Abmaj9#11", "Fm11", "Bb13sus"]
    symbols = loop * 2
    s.set("tpt", CHORALE, r"\mf\dolce")
    s.set("vn1", [tools.octave(bar, 1) for bar in CHORALE], r"\mp")
    s.set("tsax", [None] * 8 + [tools.tr(bar, -3) if i not in (2, 3) else tools.tr(bar, -4)
                                for i, bar in enumerate(CHORALE[8:])], r"\mp\subtone")  # fmt: skip
    low_horns = m.layers(symbols, ["a___ ____"], ("bsax", "tbn", "asax"), "horns3", HALVES)
    for player, bars in low_horns.items():
        s.set(player, bars, r"\p")
    low_strings = m.layers(symbols, ["a___ ____"], ("vc", "va", "vn2"), "strings3", HALVES)
    for player, bars in low_strings.items():
        s.set(player, bars, r"\p")
    s.set("keys.rh", chord_bars(symbols, "a___ ____"), r"\p")
    s.set("bass", m.roots(symbols, "a___ __c_", HALVES), r"\mf")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\mf", r'\switch "bass sub"')
    s.set(
        "drums",
        slow_bars(SHIMMER, 8, "chorale 1", amount=0.0, crash=(1,), fills={})
        + slow_bars(SHIMMER_FULL, 8, "chorale 2", amount=0.3, crash=(1,), fills={8: "slow 2"}),
        r"\mp",
    )
    eleven = []
    for symbol in symbols:
        notes = chords.voice(symbol, 4, low=79, high=98)
        table = {k: chords.names((n,), symbol) for k, n in zip("abcd", notes, strict=True)}
        eleven.append(patterns.pitched("ab-cd--ab-c d-ab-c--d-a", HALVES, table))
    s.set("chip", eleven, r"\pp", r'\switch "chip pulse 25"')
    s.close()

    # ------------------------------------------------- the solo of the synthesizer, in F
    s = Bars(work, 8, COMMON)
    structure.mark(s.bar(1), "O")
    symbols = [
        "Fmaj9",
        "Fmaj9",
        "Dbmaj7#11",
        "Dbmaj7#11",
        "Bbmaj9#11",
        "Bbmaj9#11",
        "Gm11",
        "C13sus",
    ]
    s.set("lead", SOLO_F, r"\mf", r'\switch "lead moog"')
    s.set("keys.rh", chord_bars(symbols, "a___ --a_"), r"\mp")
    s.set("bass", m.roots(symbols, "a__c b_a_", HALVES), r"\mf")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\mf")
    s.set("drums", slow_bars(SLOW, 8, "solo f", amount=1.0, crash=(1,), fills={4: "slow 1",
                             8: "slow 2"}), r"\mf")  # fmt: skip
    strings = m.layers(symbols, ["a___ ____"], m.STRINGS, "strings", HALVES)
    for player, bars in strings.items():
        s.set(player, bars, r"\mp")
    s.set("gtr", chord_bars(symbols, "--a_ ____", low=57, high=79), r"\mp\clean\pmoff")
    s.close()

    # ------------------------------------------------- the solo goes on, in G
    s = Bars(work, 8, COMMON)
    symbols = ["Gmaj9", "Gmaj9", "Ebmaj7#11", "Ebmaj7#11", "Cmaj9#11", "Cmaj9#11", "Am11", "D13sus"]
    s.set("lead", SOLO_G, r"\f")
    s.set("keys.rh", chord_bars(symbols, "a_a_ --a_"), r"\mf")
    s.set("bass", m.roots(symbols, "a_xc b_ac", HALVES), r"\f")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\f")
    s.set("drums", slow_bars(SLOW_OPEN, 8, "solo g", amount=1.3, crash=(1, 5), fills={4: "slow 1",
                             8: "slow 3"}), r"\f")  # fmt: skip
    strings = m.layers(symbols, ["a___ ____"], m.STRINGS, "strings", HALVES)
    for player, bars in strings.items():
        s.set(player, bars, r"\mf")
    horns = m.layers(symbols, ["a___ ____", "--a_ a___"], m.HORNS, "horns", HALVES)
    for player, bars in horns.items():
        s.set(player, bars, r"\mf")
    s.set("gtr", chord_bars(symbols, "a___ --a_", low=57, high=79), r"\mf\crunch")
    s.set("pad.rh", chord_bars(symbols, "a___ ____", low=60, high=84), r"\mf",
          r'\switch "supersaw"')  # fmt: skip
    s.close()

    # ------------------------------------------------- the theme, in G, by all players
    s = Bars(work, 8, COMMON)
    structure.mark(s.bar(1), "P")
    theme = [tools.tr(bar, 4) for bar in CHORALE[8:]]
    s.set("tpt", [tools.octave(bar, 1) for bar in theme], r"\f")
    s.set("tsax", theme, r"\f\normaltone")
    s.set("asax", [tools.tr(bar, -3) if i not in (2, 3) else tools.tr(bar, -4)
                   for i, bar in enumerate(theme)], r"\f")  # fmt: skip
    s.set("lead", [tools.octave(bar, 1) for bar in theme], r"\f")
    s.set("vn1", [tools.octave(bar, 1) for bar in theme], r"\f")
    low_horns = m.layers(symbols, ["a___ ____"], ("bsax", "tbn"), "horns2", HALVES)
    for player, bars in low_horns.items():
        s.set(player, bars, r"\f")
    low_strings = m.layers(symbols, ["a___ ____"], ("vc", "va", "vn2"), "strings3", HALVES)
    for player, bars in low_strings.items():
        s.set(player, bars, r"\f")
    s.set("keys.rh", chord_bars(symbols, "a_a_ --a_"), r"\f")
    s.set("bass", m.roots(symbols, "a_xc b_ac", HALVES), r"\f")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\f")
    s.set("gtr", chord_bars(symbols, "a___ a___", low=50, high=74), r"\f\crunch")
    s.set("pad.rh", chord_bars(symbols, "a___ ____", low=60, high=84), r"\f")
    s.set("drums", slow_bars(SLOW_OPEN, 8, "theme g", amount=1.5, crash=(1, 3, 5, 7),
                             fills={4: "slow 2", 8: "slow 3"}), r"\ff")  # fmt: skip
    claps = drums.steps("ms ---- ---- c--- ----", BEATS)
    s.set("eperc", [claps] * 8, r"\mf")
    s.close()

    # ------------------------------------------------- the tension rises on D
    s = Bars(work, 8, COMMON)
    structure.mark(s.bar(1), "Q")
    symbols = ["D13sus", "D13sus", "D13b9", "D13b9", "D7alt", "D7alt", "D7alt", "D7alt"]
    rolls = [
        "sn ---- ---- o--- ----\nbd x--- ---- ---- ----\nhh x-x- x-x- x-x- x-x-",
        "sn ---- o--- ---- o---\nbd x--- ---- x--- ----\nhh x-x- x-x- x-x- x-x-",
        "sn o--- o--- o--- o---\nbd x--- x--- x--- x---",
        "sn o-o- o-o- o-o- o-o-\nbd x--- x--- x--- x---",
        "sn o-o- o-o- oooo oooo\nbd x--- x--- x--- x---",
        "sn oooo oooo oooo oooo\nbd x--- x--- x-x- x-x-",
        "sn oooooo oooooo oooooo OOOOOO\nbd x----- x----- x--x-- x--x--",
        "sn OOOOOOOO OOOOOOOO O--- ----\nbd x---x--- x---x--- x--- ----\ncy -------- -------- c--- ----",
    ]
    s.set("drums", [drums.steps(rows, BEATS) for rows in rolls], r"\mf\<")
    s.set("bass", m.roots(symbols, "a_a_ a_a_", HALVES), r"\f\<")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\f")
    s.set("keys.rh", chord_bars(symbols, "a_a_ a_a_"), r"\mf\<")
    s.set("gtr", [patterns.pitched("aaaa aaaa", HALVES, {"a": r"d, \pm"})] * 7
          + [r"<d, a, d>2\ff\pmoff r2"], r"\f\<\highgain")  # fmt: skip
    strings = m.layers(symbols, ["a___ ____"], m.STRINGS, "strings", HALVES)
    for player, bars in strings.items():
        s.set(player, tools.first(patterns.join(bars), r"\mf\<", note=True))
    horns = m.layers([None] * 4 + symbols[4:], ["a___ ____"], m.HORNS, "horns", HALVES)
    for player, bars in horns.items():
        s.set(player, bars, r"\mf\<")
    s.set("tsax", [None] * 4 + [r"a'1\mf\<( ~", r"a'2 c''2 ~", r"c''2 es''2 ~", r"es''2\ff) r2"])
    s.set("eperc", r"R1*4 | e,,1\mf\< ~ | e,,1 ~ | e,,1 ~ | e,,2\ff r2 |")
    # The force on the pilot goes up: "one and a half G", "two G", "two and a half G", "five G".
    cues += [
        Cue(
            "mercury3-548",
            s.bar(1),
            2,
            offset=33.7,
            seconds=0.9,
            gain_db=-9.0,
            radio=True,
            pan=-0.4,
        ),
        Cue(
            "mercury3-548",
            s.bar(3),
            2,
            offset=50.25,
            seconds=0.7,
            gain_db=-8.0,
            radio=True,
            pan=0.4,
        ),
        Cue(
            "mercury3-548",
            s.bar(5),
            2,
            offset=73.3,
            seconds=0.85,
            gain_db=-7.0,
            radio=True,
            pan=-0.4,
        ),
        Cue(
            "mercury3-548",
            s.bar(7),
            2,
            offset=120.85,
            seconds=1.1,
            gain_db=-6.0,
            radio=True,
            pan=0.4,
        ),
    ]
    s.close()

    # ------------------------------------------------- the countdown
    s = Bars(work, 2, COMMON)
    # "Three, two, one, fire": the word "fire" is on the first beat of the next part.
    fire = 2.15  # seconds from the start of the part of the recording to the word "fire"
    beat = 1 + 8 - fire * m.GIANT / 60.0
    cues.append(Cue("mercury3-548", s.bar(1), beat, offset=356.6, seconds=2.6, gain_db=-3.0,
                    radio=True))  # fmt: skip
    cues.append(Cue("static", s.bar(1), 1, seconds=3.6, gain_db=-22.0, seed=9))
    s.set("eperc", r"<< { e,,\breve\p\< } \\ { es,,1\mf r1 } >> |")
    s.set("sbass", r"d,,1\mp\> ~ | d,,2 r2\! |")
    s.close()
    structure.double_bar(s.section.last_bar)
