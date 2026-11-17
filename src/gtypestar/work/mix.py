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
        eq=(("highpass", 40.0), ("bell", 80.0, 3.0, 1.0), ("bell", 130.0, 2.5, 1.0),
            ("bell", 380.0, -6.0, 1.0), ("bell", 3800.0, 6.0, 0.9)),
        compress=(-16.0, 4.0, 0.012, 0.09), makeup_db=2.0, transient_db=3.0,
    ),
    "drums.snare": Strip(
        gain_db=8.0, bus="drums",
        eq=(("highpass", 110.0), ("bell", 210.0, -3.0, 1.0), ("bell", 550.0, -4.0, 0.8),
            ("bell", 5000.0, 4.0, 0.8), ("high shelf", 7000.0, 2.0)),
        compress=(-18.0, 4.0, 0.004, 0.11), makeup_db=2.0, transient_db=2.0,
        room=0.18, plate=0.07,
    ),
    "drums.toms": Strip(
        gain_db=3.0, bus="drums",
        eq=(("highpass", 55.0), ("bell", 420.0, -5.0, 1.0), ("bell", 4200.0, 4.0, 0.9)),
        room=0.15,
    ),
    # The microphones of the cymbals go to the group "cymbals": no strong compression,
    # and less level above 9 kHz (the first master had 9 dB too much above 11 kHz).
    "drums.cymbals": Strip(
        gain_db=-8.5, bus="cymbals",
        eq=(("highpass", 450.0), ("bell", 7000.0, 3.0, 0.7), ("lowpass", 11500.0, 4)),
        width=1.8,
    ),
    "drums.overheads": Strip(
        gain_db=4.0, bus="cymbals",
        eq=(("highpass", 550.0), ("bell", 3500.0, -1.5, 0.8), ("bell", 7000.0, 3.0, 0.7),
            ("lowpass", 15000.0, 2)),
        width=2.0,
    ),
    "drums.room": Strip(
        gain_db=-3.0, bus="drums", eq=(("highpass", 200.0), ("lowpass", 9000.0)),
        compress=(-34.0, 6.0, 0.006, 0.14), makeup_db=8.0, width=1.8,
    ),
    "eperc": Strip(
        gain_db=-9.0, bus="drums", eq=(("highpass", 35.0),), plate=0.1, room=0.1,
    ),
    # ------------------------------------------------------------ bass
    "bass": Strip(
        gain_db=0.0, bus="bass",
        eq=(("highpass", 30.0), ("low shelf", 95.0, 4.0), ("bell", 240.0, -6.0, 0.8),
            ("bell", 1000.0, -3.0, 0.7), ("high shelf", 600.0, -3.0), ("lowpass", 4500.0)),
        compress=(-20.0, 5.0, 0.02, 0.14), makeup_db=3.0, duck_db=3.5, duck_release=0.11,
    ),
    "sbass": Strip(
        # The bass sounds of the dubstep passage have their rough part up to 9 kHz. No
        # compressor: the sounds of the synthesizer have an even level by themselves, and
        # a compressor here made the bass of the dubstep passage 10 dB too soft.
        gain_db=-4.0, bus="bass", eq=(("highpass", 28.0), ("lowpass", 9000.0)),
        duck_db=5.0, duck_release=0.12,
    ),
    # ------------------------------------------------------------ rhythm section
    # No compressor: the clean tone has its own in the guitar sound (`band.render_guitar`),
    # and the distortion of the heavy tones is a compressor by itself.
    "gtr": Strip(
        gain_db=-1.5, eq=(("highpass", 100.0), ("lowpass", 8000.0)),
        duck_db=1.0, room=0.08, echo=0.07,
    ),
    "keys": Strip(
        gain_db=-10.5, eq=(("highpass", 110.0), ("bell", 1000.0, 2.0, 0.7)), drive_db=5.0,
        compress=(-22.0, 3.0, 0.02, 0.15), chorus=0.3, width=1.5, duck_db=1.5, plate=0.1,
        echo=0.08,
    ),
    # ------------------------------------------------------------ lead voices
    "tsax": Strip(
        gain_db=4.0, eq=(("highpass", 100.0), ("bell", 250.0, 1.5, 1.0),
                         ("bell", 520.0, -2.5, 0.9), ("bell", 1100.0, 3.0, 0.7),
                         ("bell", 3200.0, -2.0, 0.8)),
        drive_db=2.0, compress=(-22.0, 3.5, 0.01, 0.16), makeup_db=3.0, plate=0.2, echo=0.14,
    ),
    "lead": Strip(
        gain_db=12.0, eq=(("highpass", 150.0), ("bell", 3000.0, 1.5, 0.8)),
        compress=(-20.0, 3.0, 0.01, 0.15), chorus=0.25, plate=0.14, echo=0.2,
    ),
    "horns": Strip(
        gain_db=3.0, eq=(("highpass", 110.0), ("bell", 2500.0, 2.0, 0.8),
                         ("high shelf", 7000.0, -2.0)),
        compress=(-22.0, 3.0, 0.01, 0.15), plate=0.16, room=0.12,
    ),
    "strings": Strip(
        gain_db=2.0, eq=(("highpass", 110.0), ("high shelf", 7000.0, -2.0)), hall=0.3,
        duck_db=1.0,
    ),
    # ------------------------------------------------------------ synthesizers
    "pad.rh": Strip(
        gain_db=0.0, eq=(("highpass", 130.0), ("high shelf", 8000.0, -1.0)), width=1.3,
        duck_db=4.5, duck_release=0.2, hall=0.2,
    ),
    "pad.lh": Strip(gain_db=0.0, eq=(("highpass", 120.0),), duck_db=4.5, hall=0.15),
    "chip": Strip(gain_db=-2.0, eq=(("highpass", 300.0), ("lowpass", 9000.0)), echo=0.25,
                  plate=0.1),
    # ------------------------------------------------------------ recorded sounds
    "tape": Strip(gain_db=0.0, bus="space", eq=(("highpass", 60.0),), hall=0.25),
}  # fmt: skip


def settings() -> Mix:
    """Return the settings of the mix."""
    return Mix(strips=dict(STRIPS))
