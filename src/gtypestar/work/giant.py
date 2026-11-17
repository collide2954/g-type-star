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

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..compose import chords, patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
HALVES = (4, 4)  # two half notes, in eighth notes
BEATS = (2, 2, 2, 2)

# The countdown in the recording of Mercury 3: the start of the words "fire three, two,
# one", and the start of the last word "fire", in seconds.
COUNT_START, COUNT_FIRE = 356.78, 359.08
# The sentence "That son of a bitch was wild." in the recording of Apollo 10, in seconds.
WILD = 590.0
# The stems of the players, for the changes of the recording before the helium flash.
# (Without MuseScore, each horn and each string group has its own stem.)
LOW_STEMS = ("drums", "eperc", "bass", "sbass", "gtr", "keys")
ALL_PLAYERS = (*LOW_STEMS, "tsax", "lead", "pad", "chip", "horns", "strings", "tpt", "asax",
               "tbn", "bsax", "vn", "va", "vc")  # fmt: skip

# The theme as a chorale in E-flat, in bars of four beats (16 bars): the motto in long
# notes (E-flat, A-flat, B-flat, C). No note of the melody is held into a chord in
# which it is the minor ninth.
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
    r"as'4 bes'4 c''2)",
    r"r2 es''2( ~",
    r"es''2 des''4 bes'4)",
    r"c''1( ~",
    r"c''4 bes'4 g'4 f'4 ~",
    r"f'2 es'2 ~",
    r"es'2.) r4",
]
# The other three voices of the chorale: the alto saxophone, the trombone, and the
# baritone saxophone. Each voice moves by small steps; an inner voice moves when the
# melody holds a note (bars 5 and 13: E-flat to D, the raised fourth of the chord).
CHORALE_ALTO = [
    r"r2 bes2(",
    r"f'2 g'2",
    r"dis'2.) r4",
    r"cis'2( b2)",
    r"g'1( ~",
    r"g'2 g'4 es'4 ~",
    r"es'2 c'2 ~",
    r"c'2 d'4) r4",
    r"r2 bes2(",
    r"f'4 g'4 g'2)",
    r"dis'2( ais'2 ~",
    r"ais'2 gis'4 fis'4)",
    r"g'1( ~",
    r"g'4 g'4 es'4 d'4",
    r"c'2 bes2",
    r"c'2.) r4",
]
CHORALE_TROMBONE = [
    r"r2 g2(",
    r"c'2 d'2",
    r"fis2.) r4",
    r"ais2( fis2)",
    r"es'2( d'2",
    r"es'2 es'4 c'4",
    r"as2 bes2",
    r"as2 as4) r4",
    r"r2 g2(",
    r"c'4 d'4 d'2)",
    r"fis2( fis'2 ~",
    r"fis'2 dis'4 cis'4)",
    r"es'2( d'2",
    r"es'4 d'4 c'4 bes4",
    r"as2 g2",
    r"as2.) r4",
]
CHORALE_BARITONE = [
    r"r2 es2(",
    r"es1",
    r"b,2.) r4",
    r"b,1",
    r"as,1( ~",
    r"as,1)",
    r"f,1(",
    r"bes,2.) r4",
    r"r2 es2(",
    r"es2 es2)",
    r"b,1( ~",
    r"b,1)",
    r"as,1( ~",
    r"as,1)",
    r"f,1(",
    r"bes,2.) r4",
]
CHORALE_VOICES = [CHORALE, CHORALE_ALTO, CHORALE_TROMBONE, CHORALE_BARITONE]
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
# The first eight bars of the chorale: the ride cymbal on each beat, a cross-stick on
# the third beat, the kick drum on the first.
BROAD = m.Groove(
    """
    rd  x--- x--- x--- x---
    sn  ---- ---- x--- ----
    bd  x--- ---- ---- ----
    """,
    BEATS,
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

    # ------------------------------------------------- N: the chorale
    s = Bars(work, 16, COMMON)
    structure.mark(s.bar(1), "N")
    structure.tempo(s.bar(1), 1, m.GIANT, "Broad and heavy (the long pulse is the new beat)")
    loop = ["Ebmaj9", "Ebmaj9", "Bmaj7#11", "Bmaj7#11", "Abmaj9#11", "Abmaj9#11", "Fm11", "Bb13sus"]
    symbols = loop * 2
    # Four real voices: the trumpet has the motto in long notes, and the alto saxophone,
    # the trombone and the baritone saxophone each have a line of their own. The strings
    # play the same four voices from the ninth bar.
    for player, voice in zip(("tpt", "asax", "tbn", "bsax"), CHORALE_VOICES, strict=True):
        s.set(player, voice, r"\mf\dolce" if player == "tpt" else r"\mp")
    s.set("vn1", [None] * 8 + [tools.octave(bar, 1) for bar in CHORALE[8:]], r"\mp")
    for player, voice in zip(("vn2", "va", "vc"), CHORALE_VOICES[1:], strict=True):
        s.set(player, [None] * 8 + voice[8:], r"\mp")
    s.set("keys.rh", chord_bars(symbols, "a___ ____"), r"\p")
    s.set("bass", m.roots(symbols, "a___ __c_", HALVES), r"\mf")
    s.set("sbass", m.roots(symbols, "a___ ____", HALVES), r"\mf", r'\switch "bass sub"')
    s.set(
        "drums",
        slow_bars(BROAD, 8, "chorale 1", amount=0.0, crash=(1,), fills={})
        + slow_bars(SLOW, 8, "chorale 2", amount=0.3, crash=(1,), fills={8: "slow 2"}),
        r"\mp",
    )
    # The seam with the flares: their last strokes become softer (to mezzo forte). The
    # guitar holds the new root at that level and its sound dies away under the chorale;
    # noise falls from the first beat.
    s.set(
        "gtr",
        r"<es, bes, es>1\mf\>\highgain\pmoff ~ | <es, bes, es>1 ~ | <es, bes, es>1\! | R1*13 |",
    )
    s.set("eperc", r"<< { f,,1\mp } \\ { es,,1\mp } >> | R1*15 |")
    # One sentence of an astronaut, after the flares (the owner asked for an astronaut who
    # swears on the radio, one time). Eugene Cernan said it in the lunar module of Apollo 10,
    # 12 minutes after the module turned over and over at the separation of its two stages.
    cues += [
        Cue("apollo10-onboard", s.bar(1), 2, offset=WILD, seconds=0.97, gain_db=-7.0,
            text="That son of a bitch was wild.", radio=True, fade=0.012, pan=0.2),
        Cue("quindar off", s.bar(1), 4.25, gain_db=-22.0),
    ]  # fmt: skip
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
    # The second half of the chorale, in G: the four voices of the horns, the tenor
    # saxophone one octave under the trumpet, and the strings with the same voices.
    voices = [[tools.tr(bar, 4) for bar in voice[8:]] for voice in CHORALE_VOICES]
    theme = voices[0]
    s.set("tpt", theme, r"\f")
    s.set("tsax", [tools.octave(bar, -1) for bar in theme], r"\f\normaltone")
    s.set("lead", [tools.octave(bar, 1) for bar in theme], r"\f")
    s.set("vn1", [tools.octave(bar, 1) for bar in theme], r"\f")
    for horn, string, voice in zip(
        ("asax", "tbn", "bsax"), ("vn2", "va", "vc"), voices[1:], strict=True
    ):
        s.set(horn, voice, r"\f")
        s.set(string, voice, r"\f")
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

    # ------------------------------------------------- the tension rises on D: the build-up
    # Ten bars lead to the helium flash (`flash.py`). All sounds become faster, higher and
    # brighter: the snare drum goes from quarter notes to thirty-second notes, noise rises,
    # the chords of the synthesizer open, the lines climb, and in the last bars the low
    # sounds go away. On the third beat of the last bar all players stop. In the silence
    # (one and a half beats: the only sudden pause of the work) the voice of the recording
    # says "one"; the word "fire" is on the first beat of the next part.
    s = Bars(work, 10, COMMON)
    structure.mark(s.bar(1), "Q")
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]
    symbols = ["D13sus", "D13sus", "D13b9", "D13b9"] + ["D7alt"] * 6
    stop = "A_------"  # the last stroke: an eighth note on the third beat, then silence
    rolls = [
        "sn ---- ---- o--- ----\nbd x--- ---- ---- ----\nhh x-x- x-x- x-x- x-x-",
        "sn ---- o--- ---- o---\nbd x--- ---- x--- ----\nhh x-x- x-x- x-x- x-x-",
        "sn ---- o--- ---- o---\nbd x--- x--- x--- x---\nhh x-x- x-x- x-x- x-x-",
        "sn o--- o--- o--- o---\nbd x--- x--- x--- x---\nhh x-x- x-x- x-x- x-x-",
        "sn o-o- o-o- o-o- o-o-\nbd x--- x--- x--- x---",
        "sn o-o- o-o- o-o- o-oo\nbd x--- x--- x--- x---",
        "sn o-o- o-o- oooo oooo\nbd x--- x--- x--- x---",
        "sn oooo oooo oooo oooo\nbd x--- x--- x-x- x-x-",
        "cy c----- ------ ------ ------\nsn oooooo oooooo oooooo OOOOOO\nbd x----- x----- x--x-- x--x--",
        "sn OOOOOOOO OOOOOOOO O--- ----\nbd x---x--- x---x--- x--- ----\ncy -------- -------- C--- ----",
    ]
    kit = [drums.steps(rows, BEATS) for rows in rolls]
    kit[9] = tools.first(kit[9], r"\fff", note=True)
    s.set("drums", kit, r"\mf\<")
    # The drum machine: the kick on each beat, a roll whose pitch rises with the loudness,
    # and noise that rises for five and a half bars.
    roll = ["r-r- r-r- r-r- r-r-", "r-r- r-r- r-r- r-rr", "r-r- r-r- rrrr rrrr",
            "rrrr rrrr rrrr rrrr", "rrrrrr rrrrrr rrrrrr RRRRRR", "RRRRRRRR RRRRRRRR s--- ----"]  # fmt: skip
    feet = ["h--- h--- h--- h---"] * 6 + ["h-h- h-h- h-h- h-h-", "h-h- h-h- h--- ----"]
    hands = ["R1"] * 4 + [drums.steps(f"ms {row}", BEATS) for row in roll]
    hands[4] = tools.first(hands[4], r"\mp\<", note=True)
    hands[9] = tools.first(hands[9], r"\fff", note=True)
    lower = ["R1"] * 2 + [drums.steps(f"mk {row}", BEATS) for row in feet]
    lower[2] = tools.first(lower[2], r"\mf\<", note=True)
    lower[9] = tools.first(lower[9], r"\fff", note=True)
    noise = r"R1*4 | e,,1\mf\< ~ | e,,1 ~ | e,,1 ~ | e,,1 ~ | e,,1 ~ | e,,2\fff r2"
    s.set("eperc", "<< { " + " | ".join(hands) + r" } \\ { " + " | ".join(lower) + r" } \\ { "
          + noise + " } >> |")  # fmt: skip

    low = m.roots(symbols[:4], "a_a_ a_a_", HALVES) + m.roots(symbols[4:8], "aaaa aaaa", HALVES)
    low += m.roots(symbols[8:9], "aaaaaaaa aaaaaaaa", HALVES)
    low += m.roots(symbols[9:], "aaaaaaaa " + stop, HALVES)
    s.set("bass", low, r"\f\<")
    s.set("sbass", m.roots(symbols[:9], "a___ ____", HALVES) + [r"d,2 d,8-> r8 r4"], r"\f")
    keys = chord_bars(symbols[:8], "a_a_ a_a_") + chord_bars(symbols[8:9], "aaaa aaaa")
    keys += chord_bars(symbols[9:], "a_a_a_a_ " + stop)
    s.set("keys.rh", keys, r"\mf\<")
    chug = {"a": r"d, \pm", "b": r"<d, a, d> \pmoff"}
    guitar = [patterns.pitched("aaaa aaaa", HALVES, chug)] * 6
    guitar += [patterns.pitched("aaaaaaaa aaaaaaaa", HALVES, chug)] * 3
    guitar.append(patterns.pitched("aaaaaaaa B_------", HALVES, chug))
    s.set("gtr", guitar, r"\f\<\highgain")
    held = ["a___ ____"] * 9 + ["a___ A---"]
    strings = m.layers(symbols, held, m.STRINGS, "strings", HALVES)
    for player, bars in strings.items():
        bars[9] = tools.first(bars[9], r"\fff", note=True)
        s.set(player, tools.first(patterns.join(bars), r"\mf\<", note=True))
    horns = m.layers([None] * 4 + symbols[4:], held, m.HORNS, "horns", HALVES)
    # The trumpet takes the line of the saxophone on from its highest note (F5).
    horns["tpt"][7:] = [r"r2 f''2(", r"fis''2 a''2 ~", r"a''2 a''8->) r8 r4"]
    for player, bars in horns.items():
        bars[9] = tools.first(bars[9], r"\fff", note=True)
        s.set(player, bars, r"\mf\<")
    # The saxophone climbs through the notes of the chord to its highest note.
    s.set("tsax", [None] * 4 + [r"a'1\mf\<( ~", r"a'2 c''2 ~", r"c''2 es''2 ~", r"es''2 f''2 ~",
                                r"f''1 ~", r"f''2 f''8->\fff) r8 r4"])  # fmt: skip
    # Chords of the synthesizer in eighth notes: a filter opens from bar 5 to the stop.
    pulse = chord_bars(symbols[4:9], "aaaa aaaa", low=60, high=84)
    pulse += chord_bars(symbols[9:], "a_a_a_a_ " + stop, low=60, high=84)
    s.set("pad.rh", [None] * 4 + pulse, r"\mf\<", r'\switch "supersaw"')
    # The lead synthesizer rises by a semitone on each beat of the last two bars.
    climb = " ".join(f"{name}16 {name} {name} {name}" for name in ("d''", "es''", "e''", "f''"))
    last = r"fis''16 fis'' fis'' fis'' g'' g'' g'' g'' a''8->\fff r8 r4"
    s.set("lead", [None] * 8 + [climb, last], r"\f\<", r'\switch "lead square"')

    # The force on the pilot goes up: "one and a half G", "two G", "two and a half G", "five G".
    cues += [
        Cue(
            "mercury3-548",
            s.bar(1),
            2,
            offset=33.7,
            text="One and a half G.",
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
            text="Two G.",
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
            text="Two and a half G.",
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
            text="Five G.",
            seconds=1.1,
            gain_db=-6.0,
            radio=True,
            pan=0.4,
        ),
    ]
    # The countdown: "Fire three, two, one, fire". The recording has the last word 2.30
    # seconds after the start of this part of it: that word is on the first beat of the
    # next part of the work.
    fire = COUNT_FIRE - COUNT_START
    beat = 1 + 8 - fire * m.GIANT / 60.0
    cues.append(Cue("mercury3-548", s.bar(9), beat, offset=COUNT_START, seconds=fire + 0.34,
                    text="Fire three, two, one, fire.", gain_db=3.0, radio=True, fade=0.01))  # fmt: skip
    edits += [
        # The filter of the synthesizer chords opens.
        Edit("lowpass", s.bar(5), 1, length=22.0, stems=("pad",), start=220.0, end=15000.0),
        # In the last six beats before the stop, the low sounds go away.
        Edit("highpass", s.bar(9), 1, length=6.0, stems=LOW_STEMS, start=30.0, end=420.0),
        # The silence before the helium flash: all players, but not the recorded voice.
        Edit("mute", s.bar(10), 3.5, length=1.5, stems=ALL_PLAYERS),
    ]
    s.close()
    structure.double_bar(s.section.last_bar)
