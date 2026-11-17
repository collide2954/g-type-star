"""Part 1: the nebula. A cloud of hydrogen comes together.

No steady groove. The real sound of the Sun (its oscillations, made faster),
radio noise, an electric piano with chords of fourths, and single high notes
of the chip synthesizer: the lines of the spectrum of hydrogen. A slow pulse
starts (35 beats in a minute). Then the drums go faster by division: one,
two, three, four, six, and eight notes in a beat. The part ends on one loud,
dense chord of all players (a "space chord").

Style profile: "Space" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.tape import Cue
from ..notation import drums
from ..notation.work import Work
from .material import Bars

SLOW = 70.0  # quarter notes in a minute; the pulse is the half note: 35 in a minute
COMMON = (4, 4, ())
# The notes of the horns and the strings in the last chord of the part. The chord rings
# on into the next part (see ignition.py).
SPACE = {"tpt": "d''", "asax": "f'", "tbn": "c'", "bsax": "g,", "vn1": "f'''", "vn2": "c'''",
         "va": "d''", "vc": "g"}  # fmt: skip
BEATS = (2, 2, 2, 2)  # the four beats of a bar, in eighth notes


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]

    # ------------------------------------------------- bars 1 to 16: the cloud
    s = Bars(work, 16, COMMON)
    structure.tempo(s.bar(1), 1, SLOW, "Free, as in space")
    cues += [
        Cue("sun", s.bar(1), 1, seconds=66.0, gain_db=-17.0, fade=6.0, seed=1),
        Cue("sun-sonification", s.bar(1), 3, gain_db=-15.0, fade=3.0),
        # The noise of the solar wind goes through narrow filters at the notes of the
        # motto (G, C, D, E): pitch comes out of the noise before a player has a note.
        Cue("wind", s.bar(2), 1, seconds=50.0, gain_db=-17.0, fade=8.0, seed=2,
            ring=(55, 60, 62, 64), ring_mix=0.75),
        Cue("quindar on", s.bar(3), 1, gain_db=-20.0),
        Cue(
            "mercury3-548",
            s.bar(3),
            1.5,
            offset=30.5,
            text="Trajectory okay.",
            seconds=1.0,
            gain_db=-13.0,
            radio=True,
        ),
        Cue("quindar off", s.bar(3), 3.5, gain_db=-20.0),
        Cue("static", s.bar(4), 1, seconds=2.5, gain_db=-24.0, seed=3, pan=-0.5),
        Cue("voyager-heliosphere", s.bar(7), 1, gain_db=-17.0, fade=1.5, pan=0.4,
            ring=(55, 62), ring_mix=0.35),
        Cue("quindar on", s.bar(11), 2, gain_db=-21.0),
        Cue(
            "mercury3-548",
            s.bar(11),
            2.5,
            offset=20.5,
            text="Roger.",
            seconds=0.5,
            gain_db=-14.0,
            radio=True,
        ),
        Cue("quindar off", s.bar(11), 3.5, gain_db=-21.0),
        Cue("earth-chorus", s.bar(13), 1, gain_db=-19.0, fade=1.0, pan=-0.4),
        Cue("telemetry", s.bar(15), 3, seconds=1.2, gain_db=-27.0, pan=0.6),
    ]
    s.set(
        "keys.rh",
        r"""R1*4 |
        r2 <g c' f'>2\pp ~ | <g c' f'>1 | r4 <a d' g'>2.\< ~ | <a d' g'>2\p r2 |
        <d' g' c''>1\pp ~ | <d' g' c''>2 <c' f' bes'>2 ~ | <c' f' bes'>1 | r2 <g c' f' bes'>2\< ~ |
        <g c' f' bes'>1\p | <a d' g' c''>1 | <bes es' as'>2\mp <a d' g'>2 | <g c' d' f'>1\> |""",
    )
    s.set(
        "keys.lh", r"R1*8 | <g,, g,>1\pp ~ | <g,, g,>1 | R1*2 | <g,, g,>1\p ~ | <g,, g,>1 | R1*2 |"
    )
    s.set(
        "chip",
        r"""\switch "chip pulse 12" R1*2 |
        r2 r4 d''''16\pp r8. | R1 | r4 es''''16 r8. r2 | r2 c''''16 r8. r4 |
        R1 | f''''16 r8. r4 r2 | r2 r4 d''''16 r8. | c''''16 r8. r2. |
        r4 r8 es''''16 r16 r2 | R1 |
        g'''16\pp( c'''' d'''' c'''' g''' d''' g''' c'''') r2 |
        r2 d''''16( c'''' g''' f''' g''' c'''' d'''' f'''') |
        g'''16( c'''' d'''' c'''' g''' d''' g''' c'''')
        c''''16( g''' f''' d''' f''' g''' c'''' d'''') |
        g'''16\<( c'''' d'''' f'''' d'''' c'''' g''' c'''')
        g''''16( f'''' d'''' c'''' d'''' f'''' g'''' g'''\mp) |""",
    )
    s.set(
        "pad.rh",
        r"""\switch "pad glass" R1*2 |
        <g'' c''' d'''>1\pp ~ | <g'' c''' d'''>1 ~ | <g'' c''' d'''>1 ~ | <g'' c''' d'''>1 |
        <a'' d''' g'''>1 ~ | <a'' d''' g'''>1 | <g'' c''' f'''>1 ~ | <g'' c''' f'''>1 |
        <g'' c''' d'''>1\< ~ | <g'' c''' d'''>1 | <a'' d''' f'''>1\p ~ | <a'' d''' f'''>1 |
        <bes'' es''' g'''>1 | <g'' c''' d''' f'''>1 |""",
    )
    s.set(
        "bass",
        r"""R1*6 |
        g1\pp\flageolet ~ | g2 d'2\flageolet ~ | d'1 | R1 | g1\flageolet ~ | g1 |
        g,,1\p ~ | g,,1 | g,,1\< ~ | g,,2 f,,2\mp |""",
    )
    s.set(
        "tsax",
        r"""R1*12 |
        r2 g'2\pp\subtone( ~ | g'4 c''2. ~ | c''4 d''2.\< ~ | d''2.\p\>) r4\! |""",
    )
    s.set(
        "vn1",
        r"R1*8 | d''''1\ppp\sultasto ~ | d''''1 ~ | d''''1 ~ | d''''1 | c''''1\< ~ | c''''1 | d''''1\p ~ | d''''1\> |",
    )
    s.set(
        "vn2",
        r"R1*8 | g'''1\ppp\sultasto ~ | g'''1 ~ | g'''1 ~ | g'''1 | g'''1\< ~ | g'''1 | f'''1\p ~ | f'''1\> |",
    )
    s.set("va", r"R1*10 | c''1\ppp\sultasto ~ | c''1 | d''1\< ~ | d''1 | c''1\p ~ | c''1\> |")
    s.set("vc", r"R1*10 | g1\ppp\sultasto ~ | g1 | g1\< ~ | g1 | g1\p ~ | g1\> |")
    pulse = drums.steps("bd x--- ---- x--- ----", BEATS)
    soft_crash = drums.steps("cy c--- ---- ---- ----", BEATS)
    s.set(
        "drums",
        [None] * 8 + [soft_crash, None, None, None, pulse, pulse, pulse, pulse],
        r"\pp",
    )
    s.close()

    # ------------------------------------------------- bars 17 to 22: the cloud falls together
    s = Bars(work, 6, COMMON)
    structure.mark(s.bar(1), "A")
    structure.change(s.bar(1), 1, "accel. poco a poco")
    structure.arrive(s.bar(6), 4, 87.5)
    cues += [
        Cue(
            "mercury3-548",
            s.bar(2),
            1,
            offset=33.6,
            text="One and a half G.",
            seconds=1.0,
            gain_db=-13.0,
            radio=True,
        ),
        Cue(
            "mercury3-548",
            s.bar(4),
            1,
            offset=50.2,
            text="Two G.",
            seconds=0.75,
            gain_db=-12.0,
            radio=True,
        ),
        Cue("static", s.bar(5), 1, seconds=6.0, gain_db=-22.0, seed=5),
    ]
    ladder = [
        "tm f f f f\nbd x - x -",
        "tm f- f- f- f-\nbd x- -- x- --",
        "tm ff- mf- ff- mf-\nbd x-- --- x-- ---",
        "tm ffm- ffm- hmf- hmff\nbd x--- x--- x--- x---",
        "sn o-o--- o-o--- --o--- o-----\ntm --h-m- --h-f- hm-mff -hmfff\nbd x----- x----- x----- x-----",
        "sn oooooooo oooooooo oooooooo OOOOOOOO\nbd x------- x------- x---x--- x-x-x-x-",
    ]
    s.set("drums", [drums.steps(rows, BEATS) for rows in ladder], r"\mp\<")
    # The drum machine: a low tone that falls (bars 1 and 2), and noise that rises (bars 5 and 6).
    s.set("eperc", r"""<< { R1*4 | e,,1\mp\< ~ | e,,1 } \\ { es,,1\mf ~ | es,,1 | R1*4 } >> |""")
    s.set(
        "bass",
        r"g,,1\mp\< ~ | g,,1 | g,,2 g,,2 | g,,4 g,,4 g,,4 g,,4 | g,,8\f g,, g,, g,, g,, g,, g,, g,, | <g,, d,>1\ff\fermata |",
    )
    s.set(
        "keys.rh",
        r"""<g c' f'>1\p\< ~ | <g c' f'>1 | <a d' g'>2 <bes es' as'>2 | <c' f' bes'>2\mf <d' g' c''>2 |
        <es' as' des''>2 <f' bes' es''>2 | <g' c'' d'' es'' f''>1\ff |""",
    )
    s.set(
        "keys.lh",
        r"<g,, g,>1\p\< ~ | <g,, g,>1 | <g,, g,>1 ~ | <g,, g,>1\mf | <g,, g,>1 | <g,, d, g,>1\ff |",
    )
    s.set(
        "tsax",
        r"""r2 g'2\p\<( ~ | g'4 c''2. ~ | c''4 d''2. | es''2\mf f''2 ~ | f''1\< ~ | f''1\ff) |""",
    )
    s.set("pad.rh", r"""\switch "supersaw" R1*4 | <g c' d' f'>1\p\< ~ | <g c' d' f' g'>1\ff |""")
    s.set("gtr", r"R1*4 | <g,, d, g,>1\mf\<\highgain ~ | <g,, d, g, c>1\ff |")
    s.set(
        "chip",
        r"""R1*4 | \repeat unfold 4 { g'''16\mf\< c'''' d'''' f'''' } | \repeat unfold 4 { g''''16\f f'''' d'''' c'''' } |""",
    )
    for player, note in SPACE.items():
        tremolo = ":32" if player.startswith("v") else ""
        s.set(player, rf"R1*4 | {note}1{tremolo}\p\< ~ | {note}1{tremolo}\ff |")
    s.close()
    structure.double_bar(s.section.last_bar)
