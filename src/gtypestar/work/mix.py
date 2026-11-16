"""The mix of the work: the settings of each stem.

The levels of the three groups (drums, bass, music) come from the reference
tracks: the mixer sets them (see `audio/console.py`). The levels inside a
group, the tone, and the space of each stem are in this file.

The sound of the model: dry drums with a bright, short kick drum; a bass
with weight below 60 Hz and grit above 250 Hz; a synthesizer background and
a bright top; a lead voice in front.
"""

from __future__ import annotations

from ..audio.console import Mix, Strip

STRIPS = {
    # ------------------------------------------------------------ drums
    "drums.kick": Strip(
        gain_db=1.0, bus="drums",
        eq=(("highpass", 32.0), ("bell", 62.0, 3.0, 1.0), ("bell", 380.0, -6.0, 1.0),
            ("bell", 3800.0, 6.0, 0.9), ("high shelf", 9000.0, 2.0)),
        compress=(-16.0, 4.0, 0.012, 0.09), makeup_db=2.0, transient_db=3.0,
    ),
    "drums.snare": Strip(
        gain_db=8.0, bus="drums",
        eq=(("highpass", 95.0), ("bell", 205.0, 3.0, 1.0), ("bell", 800.0, -3.0, 1.0),
            ("bell", 5000.0, 4.0, 0.8)),
        compress=(-18.0, 4.0, 0.004, 0.11), makeup_db=2.0, transient_db=2.0,
        room=0.18, plate=0.07,
    ),
    "drums.toms": Strip(
        gain_db=3.0, bus="drums",
        eq=(("highpass", 55.0), ("bell", 420.0, -5.0, 1.0), ("bell", 4200.0, 4.0, 0.9)),
        room=0.15,
    ),
    "drums.cymbals": Strip(
        gain_db=-4.0, bus="drums", eq=(("highpass", 450.0), ("high shelf", 9000.0, 1.5)),
    ),
    "drums.overheads": Strip(
        gain_db=0.0, bus="drums", eq=(("highpass", 280.0), ("bell", 3500.0, -1.5, 0.8)),
        width=1.35,
    ),
    "drums.room": Strip(
        gain_db=-3.0, bus="drums", eq=(("highpass", 110.0), ("lowpass", 9000.0)),
        compress=(-34.0, 6.0, 0.006, 0.14), makeup_db=8.0, width=1.4,
    ),
    "eperc": Strip(
        gain_db=-9.0, bus="drums", eq=(("highpass", 35.0),), plate=0.1, room=0.1,
    ),
    # ------------------------------------------------------------ bass
    "bass": Strip(
        gain_db=0.0, bus="bass",
        eq=(("highpass", 30.0), ("bell", 75.0, 2.0, 1.0), ("bell", 260.0, -3.0, 1.0),
            ("bell", 900.0, 2.5, 0.8), ("lowpass", 6500.0)),
        compress=(-20.0, 5.0, 0.02, 0.14), makeup_db=3.0, duck_db=3.5, duck_release=0.11,
    ),
    "sbass": Strip(
        gain_db=-4.0, bus="bass", eq=(("highpass", 28.0), ("lowpass", 5000.0)),
        compress=(-18.0, 4.0, 0.01, 0.12), duck_db=5.0, duck_release=0.12,
    ),
    # ------------------------------------------------------------ rhythm section
    "gtr": Strip(
        gain_db=-3.0, eq=(("highpass", 110.0), ("bell", 400.0, -2.0, 1.0), ("lowpass", 9500.0)),
        compress=(-20.0, 3.0, 0.015, 0.12), duck_db=1.0, room=0.08, echo=0.07,
    ),
    "keys": Strip(
        gain_db=-19.0, eq=(("highpass", 130.0), ("bell", 320.0, -3.0, 1.0),
                           ("bell", 2500.0, 2.0, 0.8)),
        compress=(-22.0, 3.0, 0.02, 0.15), chorus=0.3, width=1.5, duck_db=1.5, plate=0.1,
        echo=0.08,
    ),
    # ------------------------------------------------------------ lead voices
    "tsax": Strip(
        gain_db=4.0, eq=(("highpass", 120.0), ("bell", 350.0, -2.0, 1.0),
                         ("bell", 3000.0, 2.5, 0.8)),
        drive_db=3.0, compress=(-22.0, 3.5, 0.01, 0.16), makeup_db=3.0, plate=0.2, echo=0.14,
    ),
    "lead": Strip(
        gain_db=9.0, eq=(("highpass", 150.0), ("bell", 3000.0, 1.5, 0.8)),
        compress=(-20.0, 3.0, 0.01, 0.15), plate=0.14, echo=0.2,
    ),
    "horns": Strip(
        gain_db=0.0, eq=(("highpass", 110.0), ("bell", 2500.0, 2.0, 0.8),
                         ("high shelf", 7000.0, -2.0)),
        compress=(-22.0, 3.0, 0.01, 0.15), plate=0.16, room=0.12,
    ),
    "strings": Strip(
        gain_db=0.0, eq=(("highpass", 110.0), ("high shelf", 7000.0, -2.0)), hall=0.3,
        duck_db=1.0,
    ),
    # ------------------------------------------------------------ synthesizers
    "pad.rh": Strip(
        gain_db=0.0, eq=(("highpass", 180.0), ("high shelf", 8000.0, -1.0)), width=1.3,
        duck_db=4.5, duck_release=0.2, hall=0.2,
    ),
    "pad.lh": Strip(gain_db=0.0, eq=(("highpass", 120.0),), duck_db=4.5, hall=0.15),
    "chip": Strip(gain_db=-2.0, eq=(("highpass", 300.0),), echo=0.25, plate=0.1),
    # ------------------------------------------------------------ recorded sounds
    "tape": Strip(gain_db=0.0, bus="space", eq=(("highpass", 60.0),), hall=0.25),
}  # fmt: skip


def settings() -> Mix:
    """Return the settings of the mix."""
    return Mix(strips=dict(STRIPS))
