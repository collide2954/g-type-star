"""Part 2: the ignition. The fusion of hydrogen starts.

The riff of the work comes in softly, with a filter that opens (eight bars).
A voice counts: "two, one, fire". The band does not stop for the voice: the
snare drum rolls and the noise rises to the first beat (the work has only
one sudden pause, before the helium flash). On "fire", all players start
(eight bars).
The riff has the notes G, B-flat, C, D, F: there is no major third yet. The
major third comes with the theme, at the start of the main sequence.

The voice is the radio traffic of the Mercury-Redstone 3 flight (NASA, 1961).
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..compose import patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from . import nebula
from .material import Bars

# The riff, in sixteenth notes. a = G, b = B-flat, c = C, d = D, f = F, g = G one octave higher.
RIFF = [
    "a__a-x -bc_d_ f_g_ --a__b c_df--",
    "a__a-x -bc_d_ g_f_ d_c_b_ a_____",
    "a__a-x -bc_d_ f_g_ --g__f d_c_bc",
    "a_xa-b c_d_f_ g_f_ d_c_b_ a_bc_d",
]
BASS_NOTES = {"a": "g,,", "b": "bes,,", "c": "c,", "d": "d,", "f": "f,", "g": "g,", "x": "g,, -+"}
GUITAR_NOTES = {"a": "g,", "b": "bes,", "c": "c", "d": "d", "f": "f", "g": "g", "x": "g, -!"}
STABS = ["---A__ ------ ---- a__--- ------", "------ ---A__ a___ ------ ---a__",
         "A_____ ------ ---- ---a__ ------", "---a__ ------ --A_ ------ a_____"]  # fmt: skip


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    # ------------------------------------------------- the riff behind a filter
    s = Bars(work, 8)
    structure.mark(s.bar(1), "B")
    structure.tempo(s.bar(1), 1, m.FAST, "Bright, with drive")
    order = [0, 1, 0, 1, 0, 2, 0]
    s.set(
        "bass",
        [patterns.pitched(RIFF[n], m.CLAVE, BASS_NOTES) for n in [*order, 3]],
        r"\mf\fingers",
    )
    s.set(
        "gtr",
        [None, None] + [patterns.pitched(RIFF[n], m.CLAVE, GUITAR_NOTES) for n in [*order[2:], 3]],
        r"\mf\clean\pm",
    )
    build = [
        None,
        None,
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nbd  x----- x----- x--- x----- x-----",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-o-\nbd  x----- x----- x--- x----- x--x--",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nsn  ---g-- ---g-- ---g ---g-- ---g-g\n"
        "bd  x----- x----- x--- x----- x-----",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-o-\nsn  ---g-- o--g-- ---g ---g-- o--g-g\n"
        "bd  x----x x----- x--- x--x-- x-----",
        "hh  x-x-x- x-x-x- x-x- x-x-x- ------\nsn  --g-g- o-g-g- g-g- o-o-o- oooooo\n"
        "bd  x----x x----- x--- x--x-- x--x--",
        "sn  o-o-oo o-oooo oooo oOoOoO OOOOOO\nbd  x--x-- x--x-- x-x- x-x-x- x-x-x-",
    ]
    s.set(
        "drums", [None if rows is None else drums.steps(rows, m.CLAVE) for rows in build], r"\mp\<"
    )
    s.set(
        "keys.rh",
        [None] * 4 + [m.comp("G9sus", STABS[n % 4], low=53, high=74)[0] for n in range(3)]
        + [m.comp("G9sus", "A_____ ---A__ A___ A__A__ A__A__", low=53, high=74)[0]],
        r"\mf\<",
    )  # fmt: skip
    # The drum machine: a kick on each pulse (bars 1 to 4), then noise that rises (bars 7 and 8).
    four = drums.steps("mk  x----- x----- x--- x----- x-----", m.CLAVE)
    riser = r"e,,1.. ~ | e,,1.."
    # The first beat has an impact and a low tone that falls: the cloud is now a star.
    first = r"<< { " + four + r" } \\ { <es,, ges,,>1..\f } >>"
    second = tools.first(four, r"\mp", note=True)
    s.set("eperc", patterns.join([first, second] + [four] * 4) + " " + riser + " |", r"\mp")
    edits.append(
        Edit("lowpass", s.bar(1), 1, length=7 * 8, stems=("drums", "bass", "gtr", "keys"),
             start=240.0, end=17000.0)
    )  # fmt: skip
    # The seam with the nebula: its last chord rings on above the riff and becomes soft.
    for player, note in nebula.SPACE.items():
        tremolo = ":32" if player.startswith("v") else ""
        s.set(player, rf"{note}1..{tremolo}\ff\> ~ | {note}1..{tremolo} | R1*14/8*6\! |")
    s.set(
        "pad.rh",
        r"""\switch "supersaw" <g c' d' f' g'>1..\f\> ~ | <g c' d' f' g'>1.. | R1*14/8*6\! |""",
    )
    # "Two, one, fire. Lift off." The word "fire" is on the first beat of the next bar.
    fire = 2.43 - 0.7  # seconds from the start of the part of the recording to the word
    beat = 1 + 7 - fire * m.FAST / 60.0
    cues.append(Cue("mercury3-548", s.bar(8), beat, offset=0.7, text="Two, one, fire. Lift off.", seconds=3.7, gain_db=-4.0,
                    radio=True))  # fmt: skip
    s.close()

    # ------------------------------------------------- all players
    s = Bars(work, 8)
    order = [0, 1, 0, 2, 0, 1, 2, 3]
    s.set("bass", [patterns.pitched(RIFF[n], m.CLAVE, BASS_NOTES) for n in order], r"\ff")
    s.set("gtr", [patterns.pitched(RIFF[n], m.CLAVE, GUITAR_NOTES) for n in order],
          r"\ff\crunch\pm")  # fmt: skip
    s.set(
        "drums",
        m.drum_bars(m.MAIN_OPEN, 8, "ignition", amount=1.0, crash=(1, 3, 5, 7),
                    fills={4: "snare 1", 8: "toms 2"}),
        r"\ff",
    )  # fmt: skip
    s.set("keys.rh", [m.comp("G9sus", STABS[n % 4], low=53, high=74)[0] for n in range(8)], r"\f")
    s.set("sbass", m.roots(["G5"] * 8, "a_____ ______ ____ a_____ ______"), r"\f",
          r'\switch "bass sub"')  # fmt: skip
    horn_hits = ["------ ------ ---- A--a-- A_____", "---A__ ------ A___ ------ ------",
                 "------ ---A-a ____ ------ A--A__", "A_____ ---A__ A___ A__A__ A_____"]  # fmt: skip
    horns = m.layers([None] * 4 + ["G9sus"] * 4, horn_hits, m.HORNS, "horns")
    for player, bars in horns.items():
        s.set(player, bars, r"\f")
    s.set("tsax", horns_line(), r"\f")
    arps = []
    for number in range(8):
        table = {"a": "g''", "b": "c'''", "c": "d'''", "d": "f'''", "e": "g'''"}
        shape = ["abcdec abcdec abcd ecabcd ecabcd", "edcbae dcbaed cbae dcbaed cbaedc"][number % 2]
        arps.append(patterns.pitched(shape, m.CLAVE, table))
    s.set("chip", arps, r"\mf", r'\switch "chip pulse"')
    impact = r"<< { r4. es,4.\mf r4 r4. es,4. } \\ { ges,,1..\f } >>"
    claps = drums.steps("ms  ------ c----- ---- ------ c-----", m.CLAVE)
    s.set("eperc", patterns.join([impact] + [claps] * 7))
    s.close()
    structure.double_bar(s.section.last_bar)


def horns_line() -> list[str | None]:
    """Return the part of the tenor saxophone in the last bars of the ignition."""
    return [
        None, None, None, None,
        r"r4. r4. r4 d''4.->\f r4.",
        r"r4. f''4.-> ~ f''4 r4. r4.",
        r"r4. r4. f''4-> ~ f''4. r4.",
        r"d''4.-> f''4.-> d''4-> f''4.-> d''4.->",
    ]  # fmt: skip
