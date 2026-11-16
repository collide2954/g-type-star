"""Part 8: the white dwarf. What stays after the fall: small, dense, and cold.

The fall of part 7 ends on the first beat of this part: one stroke of the
kick drum and a low tone that falls. Then there is no band. A low G of the
synthesizer is the mass of the star, and the sound of the Sun goes on below
all other sounds. The kick drum has three more strokes, each softer than
the stroke before. The electric piano holds a chord of fourths (three
fourths: the carbon that the star made from helium). The saxophone plays
the first three notes of the motto, low and soft. The last sound is the
fourth note of the motto, very high, with no chord under it.

The sound of the recording stays low, dark, and near the centre (the long
edits of `audio/glitch.py`): the star has the size of the Earth now.

The last bar is held: the work ends at 13 minutes.
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..notation.work import Work
from . import agb
from .material import Bars

COMMON = (4, 4, ())
END_SECONDS = 780.0  # the work has 13 minutes
LAST_HOLD = 6.0  # the wanted length of the hold of the last bar, in seconds
LAST_BARS = 6  # the bars after the mark X
SLOWEST, FASTEST = 40.0, 72.0  # limits of the tempo of the last bars
# A cue of a recorded sound stays inside one part of the render and some seconds more
# (see `audio/tape.py`). Thus the sound of the Sun is a chain of cues: each cue starts
# with a new part of the work, and goes into the next cue.
OVERLAP = 4.5


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    # ------------------------------------------------- W: the mass
    s = Bars(work, 6, COMMON)
    first = s.bar(1)
    structure.mark(first, "W")
    structure.tempo(first, 1, agb.FALL_END, "Very slow: small, dense, cold")
    # The last strokes of the kick drum (the first one with the low floor tom).
    s.set("drums", r"<c, f,>4\mf r4 r2 | c,4\p r4 r2 | R1 | c,4\pp r4 r2 | R1*2 |")
    s.set("eperc", r"es,,1\mf | R1*5 |")  # a low tone that falls
    s.set("sbass", r"g,,1\mf ~ | g,,1 | g,,1\mp ~ | g,,1 | g,,1\p ~ | g,,1 |",
          prefix=r'\switch "bass sub"')  # fmt: skip
    s.set("bass", r"g,,1\mf\fingers ~ | g,,1 | R1*4 |")
    s.set(
        "keys.rh",
        r"R1*2 | <g c' f' bes'>1\pp ~ | <g c' f' bes'>1 | <g c' f' bes'>1 ~ | <g c' f' bes'>1 |",
    )
    s.set("keys.lh", r"R1*2 | <g,, g,>1\pp ~ | <g,, g,>1 | R1*2 |")
    s.set("tsax", r"R1*3 | r2 g2\pp\subtone( | c'2 d'2 ~ | d'2.\>) r4\! |")
    s.set("pad.rh", r"R1*2 | <d''' g'''>1\ppp ~ | <d''' g'''>1 ~ | <d''' g'''>1 ~ | <d''' g'''>1 |",
          prefix=r'\switch "pad glass"')  # fmt: skip
    start = structure.seconds(structure.bar(first).start)
    end = structure.seconds(structure.bar(s.bar(6)).end)
    cues.append(Cue("sun", first, 1, seconds=end - start + OVERLAP, gain_db=-14.0, fade=4.0,
                    seed=12))  # fmt: skip
    cues.append(Cue("static", s.bar(5), 1, seconds=6.0, gain_db=-30.0, fade=2.5, seed=13))
    # The sounds of the fall end at their low pitch. The drums stay low for their last
    # strokes.
    ringing = tuple(name for name in agb.BAND if name not in ("drums", "bass", "sbass"))
    edits += [
        Edit("sink", first, 1, length=7, stems=ringing, pitch_start=agb.SINK, pitch=agb.SINK),
        Edit("sink", first, 1, length=24, stems=("drums",), pitch_start=agb.SINK, pitch=agb.SINK),
    ]
    s.close()

    # ------------------------------------------------- X: the last note
    s = Bars(work, LAST_BARS, COMMON)
    structure.mark(s.bar(1), "X")
    # The tempo of the last bars comes from the time that is left: the hold of the last
    # bar has about six seconds.
    left = END_SECONDS - structure.seconds(structure.bar(s.bar(1)).start) - LAST_HOLD
    bpm = min(FASTEST, max(SLOWEST, 60.0 * 4 * LAST_BARS / max(left, 1.0)))
    structure.tempo(s.bar(1), 1, bpm, "The last light")
    s.set("keys.rh", r"<g c' d'>1\ppp ~ | <g c' d'>1 | R1*4 |")
    s.set("keys.lh", r"g,,1\ppp ~ | g,,1 | R1*4 |")
    # A slow low pulse that becomes softer.
    s.set("sbass", r"R1*2 | g,,2\pp r2 | g,,2\ppp r2 | R1*2 |")
    # The fourth note of the motto.
    s.set("chip", r"R1*4 | r2 e''''8\pp r8 r4 | R1\fermata |",
          prefix=r'\switch "chip pulse 12"')  # fmt: skip
    cues += [
        # The recording of the real Sun, as at the start of the work.
        Cue("sun-sonification", s.bar(1), 3, seconds=20.0, gain_db=-17.0, fade=5.0),
        Cue("quindar on", s.bar(2), 1, gain_db=-22.0),
        Cue("mercury3-548", s.bar(2), 1.6, offset=20.55, text="Roger.", seconds=0.5,
            gain_db=-12.0, radio=True),
        Cue("quindar off", s.bar(2), 3, gain_db=-22.0),
    ]  # fmt: skip
    # The sound stays dark and near the centre to the end. The high sounds (the chip
    # synthesizer, the glass sound) are not in the filter: they are the cold light.
    quarters = 4 * (6 + LAST_BARS)
    dark = tuple(name for name in agb.BAND if name not in ("chip", "pad", "lead"))
    edits += [
        Edit("narrow", first, 1, length=quarters, stems=agb.BAND, width_start=0.2, width=0.2),
        Edit("darken", first, 1, length=quarters, stems=dark, start=900.0, end=1400.0),
    ]
    s.close()

    # The last bar is held: the work ends at 13 minutes. The hold changes the last
    # quarter note only; two more steps make the time exact.
    last = len(structure.bars)
    hold = END_SECONDS - structure.duration_seconds
    for _step in range(3):
        if hold <= 0.5:
            break
        structure.tempo_points = [point for point in structure.tempo_points if not point.hold]
        structure.fermata(last, hold)
        error = END_SECONDS - structure.duration_seconds
        if abs(error) < 1e-6:
            break
        hold += error
    # The sound of the Sun to the end of the work: two more cues of the chain.
    start = structure.seconds(structure.bar(s.bar(1)).start)
    final = structure.seconds(structure.bar(last).start)
    cues += [
        Cue("sun", s.bar(1), 1, seconds=final - start + OVERLAP, gain_db=-14.0, fade=4.0, seed=14),
        Cue("sun", last, 1, seconds=END_SECONDS - final - 0.3, gain_db=-14.0, fade=4.0, seed=15),
    ]
