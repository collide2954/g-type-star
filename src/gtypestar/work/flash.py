"""Part 6: the helium flash. Helium starts to burn in the core, all at one time.

This is the only dubstep passage of the work: 16 bars at 140 quarter notes
in a minute, 27.4 seconds (decision of the owner: one time, 30 seconds or
less). The drums play in half time: kick on beat 1, snare on beat 3. The bass
synthesizer has a low sine tone and, above it, a sound whose filter moves one
time in each note ("wobble"), then a sound with moving vowels ("growl"). The
rhythm of the notes is the rhythm of the filter. Saxophone and guitar answer
in the gaps.

Style profile: "Dubstep" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..compose import patterns
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
BEATS = (2, 2, 2, 2)
NOTES = {"a": "g,,", "b": "bes,,", "c": "c,", "d": "d,", "e": "es,,", "f": "f,,", "g": "g,"}
# The bass: one group of letters for each beat. A long group is a slow move of the
# filter; three letters in a beat are triplets; four are sixteenth notes.
WOBBLE = [
    "a___ a_a_ a___ aaaa",
    "a___ ____ b_b_ c___",
    "a_a_ a_a_ aaa d___",
    "a___ aaa aaa f_e_",
    "a___ a_a_ ---- aaaa",
    "c___ ____ b_b_ a___",
    "aaa aaa a_a_ gggg",
    "a___ ____ ---- ----",
]
GROWL = [
    "a_-a --a_ a___ ----",
    "a___ --b_ c_-c ----",
    "a_-a --a_ aaa ----",
    "d___ c_b_ a___ ----",
    "a_-a --a_ a___ gg--",
    "e___ --f_ g_-g ----",
    "a_a_ aaa aaaa aaaaaa",
    "a___ ____ ____ ____",
]
# The answers of the saxophone and the guitar, in the gaps of the bass.
ANSWERS = [
    None,
    None,
    None,
    r"r2 r4 r8 d''16( f''",
    r"g''8-.) r r4 r2",
    None,
    None,
    r"r4 g'8->( bes' d''8. f''16 ~ f''8 g''8->)",
    r"r2 r4 d''16( f'' g''8-.)",
    r"r2 r4 bes'16( d'' f''8-.)",
    r"r2 r4 r8 g''16( f''",
    r"d''8-.) r r2 f''16( g'' bes''8-.)",
    r"r2 r4 d''16( f'' g''8-.)",
    r"r2 r4 bes'16( c'' d''8-.)",
    None,
    r"r4 g''4->( ~ g''2)",
]


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    s = Bars(work, 16, COMMON)
    structure.mark(s.bar(1), "R")
    structure.tempo(s.bar(1), 1, m.FLASH, "Half time, heavy")
    bass = [patterns.pitched(bar, BEATS, NOTES) for bar in WOBBLE]
    growl = [patterns.pitched(bar, BEATS, NOTES) for bar in GROWL]
    growl[0] = r'\switch "bass growl" ' + growl[0]
    s.set("sbass", bass + growl, r"\ff", r'\switch "bass wobble"')
    half = [
        "hh x-x- x-x- x-x- x-x-\nsn ---- ---- o--- ----\nbd x--- ---- ---- ---x",
        "hh x-x- x-x- x-x- x-o-\nsn ---- ---- o--- -g--\nbd x--- --x- ---- ----",
        "hh x-x- x-x- x-x- x-x-\nsn ---- ---g o--- ----\nbd x--x ---- ---- --x-",
        "hh x-x- x-x- x-x- ----\nsn ---- ---- o--- o-oo\nbd x--- --x- ---- -x--",
        "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- o--- ----\nbd x--- ---x ---- --xx",
        "hh x-x- x-o- x-x- x-x-\nsn ---- ---- o--g ----\nbd x--- --x- ---- -x--",
        "hh x-x- x-x- x-x- x-x-\nsn ---g ---- o--- --g-\nbd x-x- ---- ---x ----",
        "sn ---- ---- o--- ooooooo\ntm ---- hhmm ---- -------\nbd x--- ---- -x-x x------",
        "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- o--- ----\nbd xx-- ---- ---- ---x",
        "hh x-x- x-x- x-x- x-o-\nsn ---- ---- o--- -g-g\nbd x--- --xx ---- ----",
        "hh x-x- x-x- x-x- x-x-\nsn ---- --g- o--- ----\nbd x--x ---- --x- --x-",
        "hh x-x- x-x- x-x- ----\nsn ---- ---- o--- oo-o\ntm ---- ---- ---- --f-\nbd x--- --x- ---- ----",
        "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- o--- ----\nbd x--- -x-x ---- --xx",
        "hh x-x- x-o- x-x- x-x-\nsn ---g ---- o--g ----\nbd x-x- --x- ---- -x--",
        "sn ---- o--- o-o- oooooo\nbd xxxx ---- -x-x x-----\ncy c--- ---- ---- ------",
        "cy c--- ---- ---- ----\nsn ---- ---- O--- ----\nbd x--- ---- ---- ----",
    ]
    s.set("drums", [drums.steps(rows, BEATS) for rows in half], r"\ff")
    machine = [
        "mk x--- ---- ---- ----\nms ---- ---- c--- ----\nmh --x- x-x- --x- x-xx",
        "mk x--- ---- ---- ----\nms ---- ---- c--- ----\nmh xxx- x-x- --x- x-x-",
    ]
    layer = [drums.steps(machine[n % 2], BEATS) for n in range(16)]
    layer[0] = r"<< { " + layer[0] + r" } \\ { <es,, ges,,>1 } >>"
    layer[8] = r"<< { " + layer[8] + r" } \\ { ges,,1 } >>"
    s.set("eperc", layer, r"\ff")
    s.set("tsax", ANSWERS, r"\ff\growl")
    s.set("gtr", ANSWERS, r"\ff\leadtone\pmoff")
    stabs = ["A___ ---- ---- ----", None, None, None] * 4
    horns = m.layers(["Gm11" if stab else None for stab in stabs], ["A___ ---- ---- ----"],
                     m.HORNS, "horns", BEATS)  # fmt: skip
    for player, bars in horns.items():
        s.set(player, bars, r"\ff")
    arps = []
    for number in range(8):
        table = {"a": "g''", "b": "bes''", "c": "d'''", "d": "f'''"}
        shape = ["---- abcd ---- dcba", "abcd ---- dcba ----"][number % 2]
        arps.append(patterns.pitched(shape, BEATS, table))
    s.set("chip", [None] * 8 + arps, r"\mf", r'\switch "chip pulse 25"')
    # In the last bar, the "tape" stops.
    edits.append(Edit("stutter", s.bar(8), 4, length=1.0, stems=("drums", "sbass", "eperc"),
                      slice=0.125, pitch=12.0))  # fmt: skip
    edits.append(Edit("tapestop", s.bar(16), 2, length=3.0, stems=("",)))
    s.close()
    structure.double_bar(s.section.last_bar)
