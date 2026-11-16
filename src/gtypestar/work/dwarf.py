"""Part 8: the planetary nebula and the white dwarf. The star loses its outer layers.

After the last chord, the groove comes back very softly and becomes thinner:
the players stop one after the other, and the drums play fewer and fewer
notes in each pulse. The sound of the Sun comes back. At the end there are
only chords of fourths (three fourths: the carbon that the star made from
helium), a slow low pulse that becomes softer, and one last high note: the
fourth note of the motto, with no chord under it.
"""

from __future__ import annotations

from ..audio.tape import Cue
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
END_SECONDS = 780.0  # the work has 13 minutes


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]

    # ------------------------------------------------- the layers go away
    s = Bars(work, 12)
    structure.mark(s.bar(1), "W")
    structure.tempo(s.bar(1), 1, m.FAST, "The same tempo, very soft", show_number=False)
    symbols = m.LOOP_A * 3
    thin = [
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nsn  ------ ------ ---- x----- ------\nbd  x----- ------ x--- ------ ------",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nsn  ------ ---g-- ---- x----- ------\nbd  x----- ------ ---- ------ ---x--",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nsn  ------ ------ ---- x----- ---g--\nbd  x----- ------ x--- ------ ------",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-----\nsn  ------ ------ ---- x----- ------\nbd  x----- ------ ---- ------ ------",
        "hh  x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nbd  x----- ------ ---- ------ ------",
        "hh  x--x-- x--x-- x-x- x--x-- x--x--",
        "hh  x--x-- x--x-- x-x- x--x-- x-----\nbd  x----- ------ ---- ------ ------",
        "hh  x----- x----- x--- x----- x-----",
        "rd  b----- ------ x--- ------ ------\nhh  ------ p----- ---- p----- ------",
        "rd  b----- ------ ---- ------ ------\nhh  ------ ------ ---- p----- ------",
        "rd  b----- ------ ---- ------ ------",
        None,
    ]
    s.set("drums", [None if rows is None else drums.steps(rows, m.CLAVE) for rows in thin], r"\p\>")
    s.set("keys.rh", m.pad_bars(symbols, low=55, high=77), r"\p")
    s.set("bass", m.roots(symbols[:8], "a_____ ______ ____ ______ ______", octave=1) + [None] * 4,
          r"\p\>")  # fmt: skip
    s.set(
        "tsax",
        m.THEME[:4] + [r"r4. g'4.( c''4 d''4. ~ d''4.", r"d''4. ~ d''4.) r4 r4. r4."] + [None] * 6,
        r"\p\subtone",
    )
    s.set(
        "chip",
        [None, None, None, None, None, r"r4. r4. r4 r4. e''''16 r16 r4", None,
         r"r4. r4. r4 d''''16 r16 r4 r4.", None, r"r4. c''''16 r16 r4 r4 r4. r4.", None,
         r"g'''16 r16 r4 r4. r4 r4. r4."],
        r"\pp",
        r'\switch "chip pulse 12"',
    )  # fmt: skip
    s.set(
        "vn1",
        r"d''''1..\pp\sultasto ~ | d''''1.. ~ | d''''1.. ~ | d''''1.. ~ | d''''1.. ~ | d''''1.. ~ | d''''1.. ~ | d''''1..\> ~ | d''''1.. ~ | d''''1.. ~ | d''''1.. ~ | d''''1..\ppp |",
    )
    s.set(
        "vn2",
        r"g'''1..\pp\sultasto ~ | g'''1.. ~ | g'''1.. ~ | g'''1.. ~ | g'''1.. ~ | g'''1.. ~ | g'''1.. ~ | g'''1..\> ~ | g'''1.. ~ | g'''1.. ~ | g'''1.. ~ | g'''1..\ppp |",
    )
    s.set("pad.rh", m.pad_bars(symbols, low=67, high=91), r"\pp", r'\switch "pad glass"')
    cues += [
        Cue("sun", s.bar(5), 1, seconds=62.0, gain_db=-18.0, fade=8.0, seed=11),
        Cue("wind", s.bar(7), 1, seconds=40.0, gain_db=-22.0, fade=8.0, seed=12),
        Cue("sun-sonification", s.bar(9), 1, gain_db=-16.0, fade=4.0),
    ]
    s.close()

    # ------------------------------------------------- the white dwarf
    s = Bars(work, 12, COMMON)
    structure.mark(s.bar(1), "X")
    structure.tempo(s.bar(1), 1, 87.5, "Slow (one bar of the old tempo is two beats)")
    structure.change(s.bar(5), 1, "rit. poco a poco")
    structure.arrive(s.bar(12), 4, 50.0)
    s.set(
        "keys.rh",
        r"""<g c' f' bes'>1\pp ~ | <g c' f' bes'>1 | <a d' g' c''>1 | <g c' f'>1 |
        <d g c' f'>1 ~ | <d g c' f'>1 | <g c' f' bes'>1\> ~ | <g c' f' bes'>1 |
        <g c' d'>1\ppp ~ | <g c' d'>1 | R1*2 |""",
    )
    s.set("keys.lh", r"<g,, g,>1\pp ~ | <g,, g,>1 | R1*2 | <g,, g,>1 ~ | <g,, g,>1 | R1*6 |")
    s.set("tsax", r"R1 | g'2\pp\subtone( c''2 ~ | c''2 d''2 ~ | d''1\>) | R1*8\! |")
    s.set(
        "sbass",
        r"""\switch "bass sub" R1*4 | g,,2\mp r2 | g,,2 r2 | g,,2\p r2 | g,,2 r2 |
        g,,2\pp r2 | g,,2 r2 | g,,2\ppp r2 | R1 |""",
    )
    s.set("bass", r"R1*2 | g1\pp\flageolet ~ | g1 | d'1\flageolet ~ | d'1 | R1*6 |")
    s.set("chip", r"R1*10 | r2 e''''8\pp r8 r4 | R1\fermata |")
    s.set("vn1", r"d''''1\ppp ~ | d''''1 ~ | d''''1 ~ | d''''1 | R1*8 |")
    cues += [
        Cue("static", s.bar(6), 1, seconds=14.0, gain_db=-27.0, fade=4.0, seed=13),
        Cue("quindar on", s.bar(9), 1, gain_db=-22.0),
        Cue(
            "mercury3-548",
            s.bar(9),
            1.6,
            offset=20.55,
            text="Roger.",
            seconds=0.5,
            gain_db=-12.0,
            radio=True,
        ),
        Cue("quindar off", s.bar(9), 3, gain_db=-22.0),
    ]
    s.close()
    # The last bar is held: the work ends at 13 minutes.
    hold = END_SECONDS - structure.duration_seconds
    if hold > 0.5:
        structure.fermata(len(structure.bars), hold)
