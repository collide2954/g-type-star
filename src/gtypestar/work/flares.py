"""Part 4: the flares. The active Sun: spots, flares, and the cycle of 11 years.

The key centre goes down one semitone to F-sharp, the lowest string of the
8-string guitar. A riff of 11 sixteenth notes repeats against the bars of
28 sixteenth notes: riff and bars come together again after four bars. The
kick drum plays each stroke of the riff. The recording itself is cut: a part
repeats, the sound goes backwards, the "tape" stops.

Style profile: "Heavy" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..compose import patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

CELL = "A-aa-a-aa-b"  # 11 sixteenth notes: the cycle of the sunspots has 11 years
CELL_2 = "Aa-a-ab-a-a"
GUITAR = {"a": r"fis,, \pm", "b": r"fis, \pmoff"}
BASS = {"a": "fis,,", "b": "fis,"}
# The solo of the guitar: eight bars above the riff.
SOLO = [
    r"r4. cis''4.( ~ cis''4 e''8 fis'' a'' fis''4.)",
    r"e''8( cis'' b' cis''4. ~ cis''4) r8 b'16( cis'' e''8 fis''8. e''16 cis''8)",
    r"a''4.( ~ a''4. g''4 fis''8 e'' cis'' b'4.)",
    r"cis''16( e'' fis'' a'' b'' cis''' b'' a'' fis'' e'' cis'' b' a'8 b' cis''16 e'' fis'' a'' b''8 cis'''4.)",
    r"cis'''8( b'' a'' g''4. fis''8 e'' cis''16 e'' fis'' g'' a''8 b''4.)",
    r"a''16( g'' fis'' e'' cis'' c'' b' c'' cis'' e'' fis'' g'' a''8 cis''' e'''4. ~ e'''4.)",
    r"e'''16( cis''' b'' a'' fis'' e'' cis''' b'' a'' fis'' e'' cis'' b''16 a'' fis'' e'' cis''16 e'' fis'' a'' b'' cis''' e'''8 cis''' b''",
    r"a''4. fis''4. ~ fis''4 ~ fis''4.) r4.",
]


def riff(cell: str, bars: int, table: dict[str, str], close: str = "--") -> list[str]:
    return [patterns.pitched(bar, m.CLAVE, table) for bar in m.cycle_bars(cell, bars, close)]


def riff_drums(
    cell: str, bars: int, key: str, close: str = "--", double: bool = False
) -> list[str]:
    """Return the drums for the riff: a cymbal on each pulse, one snare, the kick with the riff."""
    result = []
    source = m.random("flares", key)
    for number, bar in enumerate(m.cycle_bars(cell, bars, close)):
        kick = m.only(bar, "Aa")
        if double:
            kick = m.only(bar, "Aab-").replace("x", "x")  # the feet play all sixteenth notes
        cymbal = (
            "k----- k----- k--- k----- k-----"
            if number % 2 == 0
            else "c----- k----- k--- k----- k-----"
        )
        snare = ["------ ------ ---- o----- ------", "------ ------ ---- o----- ---g-g",
                 "------ ---g-- ---- o----- ------"][int(source.integers(0, 3))]  # fmt: skip
        if number == bars - 1:
            snare = "------ ------ ---- o----- ----OO"
        result.append(drums.steps(f"cy {cymbal}\nsn {snare}\nbd {kick}", m.CLAVE))
    return result


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]
    heavy = ("drums", "bass", "gtr", "sbass", "keys")

    # ------------------------------------------------- the riff
    s = Bars(work, 8)
    structure.mark(s.bar(1), "K")
    structure.tempo(s.bar(1), 1, m.FAST, "Heavy", show_number=False)
    s.set("gtr", riff(CELL, 4, GUITAR) + riff(CELL, 4, GUITAR), r"\ff\highgain")
    s.set("bass", riff(CELL, 4, BASS) + riff(CELL, 4, BASS), r"\ff")
    s.set("drums", riff_drums(CELL, 4, "a1") + riff_drums(CELL, 4, "a2"), r"\ff")
    s.set("sbass", m.roots(["F#5"] * 8, "a_____ ______ ____ a_____ ______"), r"\f",
          r'\switch "bass sub"')  # fmt: skip
    s.set("eperc", r"<< { R1*14/8 } \\ { ges,,1*7/4\f } >> | R1*14/8*7 |")
    cues.append(Cue("mercury3-548", s.bar(1), 1, offset=72.1, seconds=1.9, gain_db=-11.0,
                    radio=True, pan=-0.3))  # fmt: skip
    s.close()

    # ------------------------------------------------- the riff with cuts in the recording
    s = Bars(work, 8)
    s.set("gtr", riff(CELL_2, 4, GUITAR) + riff(CELL, 4, GUITAR), r"\ff")
    s.set("bass", riff(CELL_2, 4, BASS) + riff(CELL, 4, BASS), r"\ff")
    s.set("drums", riff_drums(CELL_2, 4, "b1") + riff_drums(CELL, 4, "b2"), r"\ff")
    s.set("sbass", m.roots(["F#5"] * 8, "a_____ ______ ____ a_____ ______"), r"\f")
    stabs = ["A_____ ------ ---- ------ ------", "------ ---A__ ---- A__--- ------",
             "A_____ ------ A___ ------ ---A__", "------ ------ ---- A__A__ A_____"]  # fmt: skip
    symbols = ["F#m11", "Gmaj7#11", "F#m11", "C7#11", "F#m11", "Gmaj7#11", "Amaj7#11", "C7#11"]
    horns = m.layers(symbols, stabs, m.HORNS, "horns")
    for player, bars in horns.items():
        s.set(player, bars, r"\ff")
    s.set(
        "tsax",
        [r"cis''4.->\ff\growl ~ cis''4. ~ cis''4 r4. r4.", None,
         r"r4. r4. r4 e''4.-> ~ e''4.", r"g''4.-> ~ g''4. fis''4-> ~ fis''4. r4.",
         r"cis''4.-> ~ cis''4. ~ cis''4 r4. r4.", None,
         r"r4. e''4.-> ~ e''4 g''4.-> ~ g''4.", r"a''4.-> ~ a''4. g''4-> fis''4.-> r4."],
    )  # fmt: skip
    s.set(
        "lead",
        [None, r"r4. r4. r4 <c'' fis''>4.->\f r4.", None, r"r4. r4. r4 r4. <c'' fis''>8-. <c'' fis''>-. r",
         None, r"r4. <c'' fis''>4.-> r4 r4. r4.", None, r"<c'' fis''>4.-> r4. r4 <cis'' g''>4.-> r4."],
        prefix=r'\switch "lead square"',
    )  # fmt: skip
    # Cuts: the last pulse of bars 4 and 8 repeats in pieces of a sixteenth note, and
    # the sound of bar 6 goes backwards for one pulse.
    edits += [
        Edit("stutter", s.bar(4), 6.5, length=1.5, stems=heavy, slice=0.25, pitch=5.0),
        Edit("reverse", s.bar(6), 4, length=1.0, stems=("gtr", "keys", "horns", "tsax")),
        Edit("stutter", s.bar(8), 5, length=3.0, stems=heavy, slice=0.5, pitch=-7.0, fade=0.6),
        Edit("crush", s.bar(8), 5, length=3.0, stems=("drums",), bits=5.0, hold=8),
    ]
    s.close()

    # ------------------------------------------------- the solo of the guitar
    s = Bars(work, 8)
    structure.mark(s.bar(1), "L")
    s.set("gtr", SOLO, r"\f\leadtone\pmoff")
    s.set("bass", riff(CELL, 4, BASS) + riff(CELL_2, 4, BASS), r"\ff")
    s.set("drums", riff_drums(CELL, 4, "c1") + riff_drums(CELL_2, 4, "c2"), r"\ff")
    low = {"a": "<fis,, fis,>", "b": "<fis, cis>"}
    s.set("keys.lh", riff(CELL, 4, low) + riff(CELL_2, 4, low), r"\f")
    s.set("sbass", m.roots(["F#5"] * 8, "a_____ ______ ____ a_____ ______"), r"\f")
    s.set("pad.rh", m.pad_bars(["F#m11", "F#m11", "Gmaj7#11", "Gmaj7#11", "F#m11", "F#m11",
                                "Amaj7#11", "C7#11"]), r"\mf", r'\switch "supersaw"')  # fmt: skip
    s.close()

    # ------------------------------------------------- the third line for all lead players
    s = Bars(work, 4)
    line = [tools.tr(bar, -1) for bar in m.LINE_1]
    mirror = [tools.invert(bar, "fis'") for bar in line]
    full = line + mirror
    s.set("gtr", full, r"\ff")
    s.set("tsax", full, r"\ff\normaltone")
    s.set("lead", [tools.octave(bar, 1) for bar in full], r"\f", r'\switch "lead moog"')
    s.set("chip", [tools.octave(bar, 2) for bar in full], r"\mf", r'\switch "chip pulse"')
    s.set("bass", [tools.octave(bar, -2) for bar in full], r"\ff")
    hits = m.Groove(
        """
        cy  c----- k----- k--- k----- k-----
        sn  ------ o----- ---- ------ o-----
        bd  x--x-x ---x-- x-x- x--x-x ---x-x
        """,
        m.CLAVE,
    )
    s.set("drums", m.drum_bars(hits, 4, "line 3", amount=1.3, crash=(1, 3), fills={4: "kicks 2"}),
          r"\ff")  # fmt: skip
    s.close()

    # ------------------------------------------------- the riff goes up by semitones
    s = Bars(work, 8)
    structure.mark(s.bar(1), "M")
    climb_guitar, climb_bass, sub = [], [], []
    for step, name in enumerate(["F#5", "G5", "Ab5", "A5"]):
        guitar = {"a": tools.tr("fis,,", step) + r" \pm", "b": tools.tr("fis,", step) + r" \pmoff"}
        bass = {"a": tools.tr("fis,,", step), "b": tools.tr("fis,", step)}
        bars = m.cycle_bars(CELL if step % 2 == 0 else CELL_2, 2, "aa")
        climb_guitar += [patterns.pitched(bar, m.CLAVE, guitar) for bar in bars]
        climb_bass += [patterns.pitched(bar, m.CLAVE, bass) for bar in bars]
        sub += m.roots([name] * 2, "a_____ ______ a___ ______ a_____")
    s.set("gtr", climb_guitar, r"\ff\highgain")
    s.set("bass", climb_bass, r"\ff")
    s.set("sbass", sub, r"\ff")
    fast = m.Groove(
        """
        cy  c----- k----- k--- k----- k-----
        sn  ------ o----- ---- ------ o-----
        bd  xxxxxx -xxxxx xxxx xxxxxx -xxxxx
        """,
        m.CLAVE,
    )
    s.set("drums", m.drum_bars(fast, 8, "climb", amount=0.3, crash=(1, 3, 5, 7),
                               fills={8: "snare 2"}), r"\ff")  # fmt: skip
    rising = ["F#m11", "F#m11", "Gm11", "Gm11", "Abm11", "Abm11", "Am11", "Am11"]
    horns = m.layers(rising, ["a_____ ______ ____ ______ ______"], m.HORNS, "horns")
    for player, bars in horns.items():
        s.set(player, bars, r"\f\<")
    strings = m.layers(rising, ["a_____ ______ ____ ______ ______"], m.STRINGS, "strings")
    for player, bars in strings.items():
        s.set(player, tools.first(patterns.join(bars), r"\f\<", note=True))
    s.set(
        "tsax",
        [r"fis'4.(\f\< b'4. ~ b'4 cis''4. dis''4.)", r"dis''1*7/4",
         r"g'4.( c''4. ~ c''4 d''4. e''4.)", r"e''1*7/4",
         r"as'4.( des''4. ~ des''4 es''4. f''4.)", r"f''1*7/4",
         r"a'4.( d''4. ~ d''4 e''4. fis''4.)", r"fis''4. ~ fis''4. ~ fis''4 g''4.\ff ~ g''4."],
    )  # fmt: skip
    s.set("eperc", r"R1*14/8*6 | e,,1*7/4\mf\< ~ | e,,1*7/4\f |")
    s.close()

    # ------------------------------------------------- the mass leaves the Sun
    s = Bars(work, 4)
    pulses = {"a": "<g,, d, g,>"}
    s.set(
        "gtr",
        [patterns.pitched("A_____ A_____ A___ A_____ A_____", m.CLAVE, {"a": "<bes,, f, bes,>"}),
         patterns.pitched("A__A__ A__A__ A_A_ AAAAAA AAAAAA", m.CLAVE, {"a": "<bes,, f, bes,>"}),
         r"<bes,, f, bes, d>1*7/4\ff ~", r"<bes,, f, bes, d>1*7/4"],
        r"\ff",
    )  # fmt: skip
    del pulses
    s.set(
        "bass",
        [patterns.pitched("A_____ A_____ A___ A_____ A_____", m.CLAVE, {"a": "bes,,"}),
         patterns.pitched("A__A__ A__A__ A_A_ AAAAAA AAAAAA", m.CLAVE, {"a": "bes,,"}),
         r"bes,,1*7/4\ff ~", r"bes,,1*7/4"],
    )  # fmt: skip
    s.set(
        "drums",
        [drums.steps("cy C----- C----- C--- C----- C-----\nsn O----- O----- O--- O----- O-----\n"
                     "bd x----- x----- x--- x----- x-----", m.CLAVE),
         drums.steps("sn O--O-- O--O-- O-O- OOOOOO OOOOOO\nbd x--x-- x--x-- x-x- x-x-x- xxxxxx",
                     m.CLAVE),
         drums.steps("cy C----- ------ ---- ------ ------\nbd x----- ------ ---- ------ ------",
                     m.CLAVE),
         None],
        r"\ff",
    )  # fmt: skip
    chord = ["Bb13sus"] * 4
    hit_patterns = ["A_____ A_____ A___ A_____ A_____", "A__A__ A__A__ A_A_ A_____ ______",
                    "a_____ ______ ____ ______ ______", "a_____ ______ ____ ______ ______"]  # fmt: skip
    horns = m.layers(chord, hit_patterns, m.HORNS, "horns")
    for player, bars in horns.items():
        s.set(player, bars, r"\ff")
    strings = m.layers(chord, hit_patterns, m.STRINGS, "strings")
    for player, bars in strings.items():
        s.set(player, bars, r"\ff")
    s.set("tsax", [r"f''4.->\ff f''4.-> f''4-> f''4.-> f''4.->", r"f''4.-> f''4.-> f''4-> g''4. ~ g''4.",
                   r"as''1*7/4 ~", r"as''1*7/4"])  # fmt: skip
    s.set("pad.rh", m.pad_bars(chord, low=58, high=82), r"\ff")
    s.set("keys.rh", m.pad_bars(chord), r"\ff")
    s.set("sbass", [None, None, r"bes,,1*7/4\ff ~", r"bes,,1*7/4"])
    s.set("eperc", r"R1*14/8*2 | << { R1*14/8 } \\ { ges,,1*7/4\ff } >> | R1*14/8 |")
    # The "tape" stops: all sound slows down in the last bar.
    edits.append(Edit("tapestop", s.bar(4), 1, length=7.0, stems=("",)))
    s.close()
    structure.double_bar(s.section.last_bar)
