"""The sounds of the synthesizers of the work.

Each patch has a name. The file `design/ensemble.toml` gives each
synthesizer player the names of its patches. The values come from known
instruments of the style (see `research/tables/electronics.csv`).
"""

from __future__ import annotations

from .synth import Envelope, FMPatch, Operators, Osc, Patch

# ------------------------------------------------------------------ leads

# A lead in the manner of a Minimoog: two sawtooth waves, a square wave one
# octave lower, a ladder filter, slides between the notes, and late vibrato.
LEAD_MOOG = Patch(
    "lead moog",
    (Osc("saw", voices=2, spread=12.0), Osc("pulse", semitones=-12, level=0.55, width=0.45)),
    cutoff=1500.0, tracking=0.6, resonance=0.32, drive=1.8, envelope_octaves=2.4,
    velocity_octaves=1.6, filter_envelope=Envelope(0.004, 0.4, 0.5, 0.2),
    amplitude=Envelope(0.004, 0.15, 0.9, 0.09), vibrato_hz=5.6, vibrato_cents=16.0,
    vibrato_delay=0.22, glide=0.045, stereo=0.25, gain_db=0.0,
)  # fmt: skip

# A hard lead: the square wave gives a hollow tone that cuts through guitars.
LEAD_SQUARE = Patch(
    "lead square",
    (Osc("pulse", width=0.5, pwm=0.08), Osc("saw", cents=7.0, level=0.6),
     Osc("pulse", semitones=12, level=0.25, width=0.3)),
    cutoff=2400.0, tracking=0.7, resonance=0.25, drive=1.4, envelope_octaves=1.6,
    velocity_octaves=1.4, filter_envelope=Envelope(0.003, 0.25, 0.6, 0.15),
    amplitude=Envelope(0.003, 0.1, 0.9, 0.07), vibrato_cents=14.0, glide=0.03, stereo=0.2,
)  # fmt: skip

# A soft lead in the manner of a wind controller: the loudness opens the filter.
LEAD_WIND = Patch(
    "lead wind",
    (Osc("saw", level=0.8), Osc("triangle", semitones=12, level=0.35), Osc("sine", level=0.5)),
    noise=0.015, filter="lowpass", cutoff=1100.0, tracking=0.8, resonance=0.12, drive=1.0,
    envelope_octaves=0.6, velocity_octaves=3.2, filter_envelope=Envelope(0.03, 0.3, 0.8, 0.12),
    amplitude=Envelope(0.025, 0.2, 0.92, 0.1), vibrato_hz=5.2, vibrato_cents=12.0,
    vibrato_delay=0.3, glide=0.035, stereo=0.1, range_db=30.0,
)  # fmt: skip

# ------------------------------------------------------------------ chords

# Seven detuned sawtooth waves: the wide chord sound of trance and future bass.
SUPERSAW = Patch(
    "supersaw",
    (Osc("saw", voices=7, spread=42.0),
     Osc("saw", semitones=12, voices=3, spread=24.0, level=0.4)),
    filter="lowpass", cutoff=3200.0, tracking=0.4, resonance=0.1, drive=0.9,
    envelope_octaves=1.4, velocity_octaves=1.2, filter_envelope=Envelope(0.004, 0.5, 0.55, 0.3),
    amplitude=Envelope(0.006, 0.3, 0.85, 0.22), stereo=1.0, drift_cents=5.0, gain_db=-3.0,
)  # fmt: skip

# A short pluck for arpeggios: the filter closes fast.
PLUCK = Patch(
    "pluck",
    (Osc("saw", voices=2, spread=9.0), Osc("pulse", semitones=12, level=0.3, width=0.3)),
    filter="lowpass", cutoff=700.0, tracking=0.6, resonance=0.3, drive=1.1,
    envelope_octaves=3.6, velocity_octaves=1.5, filter_envelope=Envelope(0.001, 0.22, 0.0, 0.18),
    amplitude=Envelope(0.001, 0.5, 0.0, 0.25), stereo=0.6, gain_db=-1.0,
)  # fmt: skip

# A warm pad in the manner of a string machine: slow start, slow changes.
PAD_WARM = Patch(
    "pad warm",
    (Osc("saw", voices=4, spread=22.0), Osc("pulse", semitones=-12, width=0.5, pwm=0.2, level=0.5,
                                            voices=2, spread=10.0)),
    filter="lowpass", cutoff=900.0, tracking=0.3, resonance=0.08, drive=0.8,
    envelope_octaves=1.2, velocity_octaves=0.8, filter_envelope=Envelope(0.9, 1.5, 0.7, 1.4),
    amplitude=Envelope(0.6, 1.0, 0.9, 1.6), stereo=1.0, drift_cents=6.0, gain_db=-4.0,
)  # fmt: skip

# A thin bright pad: the high part of a cloud of sound.
PAD_GLASS = Patch(
    "pad glass",
    (Osc("triangle", voices=3, spread=14.0), Osc("sine", semitones=12, voices=3, spread=18.0,
                                                 level=0.6),
     Osc("sine", semitones=19, level=0.25)),
    filter="highpass", cutoff=300.0, tracking=0.2, resonance=0.05, envelope_octaves=0.0,
    velocity_octaves=0.0, amplitude=Envelope(1.4, 2.0, 0.8, 2.6), stereo=1.0, drift_cents=8.0,
    gain_db=-6.0,
)  # fmt: skip

# Brass of an analog synthesizer: the filter opens at the start of each note.
SYNTH_BRASS = Patch(
    "synth brass",
    (Osc("saw", voices=3, spread=16.0), Osc("saw", semitones=-12, level=0.5)),
    cutoff=650.0, tracking=0.5, resonance=0.18, drive=1.3, envelope_octaves=2.8,
    velocity_octaves=1.8, filter_envelope=Envelope(0.05, 0.35, 0.6, 0.2),
    amplitude=Envelope(0.02, 0.2, 0.9, 0.14), stereo=0.7, gain_db=-2.0,
)  # fmt: skip

# ------------------------------------------------------------------ basses

# A bass in the manner of a Minimoog: fat, short, with a filter that closes.
BASS_MOOG = Patch(
    "bass moog",
    (Osc("saw"), Osc("pulse", semitones=-12, width=0.5, level=0.8),
     Osc("saw", cents=6.0, level=0.5)),
    cutoff=260.0, tracking=0.35, resonance=0.28, drive=2.2, envelope_octaves=3.2,
    velocity_octaves=1.6, filter_envelope=Envelope(0.002, 0.2, 0.25, 0.1),
    amplitude=Envelope(0.002, 0.3, 0.8, 0.07), glide=0.03, stereo=0.0, drift_cents=2.0,
    gain_db=2.0,
)  # fmt: skip

# The lowest octave only: a sine tone under a bass sound or under a kick drum.
BASS_SUB = Patch(
    "bass sub",
    (Osc("sine"), Osc("triangle", level=0.25)),
    filter="lowpass", cutoff=180.0, tracking=0.0, resonance=0.0, drive=1.5, envelope_octaves=0.0,
    velocity_octaves=0.0, amplitude=Envelope(0.004, 0.2, 1.0, 0.09), glide=0.05, stereo=0.0,
    drift_cents=0.0, range_db=18.0, gain_db=2.0,
)  # fmt: skip

# Two sawtooth waves that are a little out of tune: the bass moves by itself.
BASS_REESE = Patch(
    "bass reese",
    (Osc("saw", cents=-19.0), Osc("saw", cents=19.0), Osc("sine", semitones=-12, level=0.7)),
    cutoff=520.0, tracking=0.3, resonance=0.22, drive=2.6, envelope_octaves=1.0,
    velocity_octaves=1.2, filter_envelope=Envelope(0.01, 0.6, 0.6, 0.2),
    amplitude=Envelope(0.006, 0.2, 0.95, 0.1), glide=0.06, stereo=0.35, gain_db=1.0,
)  # fmt: skip

# The middle part of a dubstep bass: bright, hard, made for a filter that an LFO moves.
BASS_WOBBLE = Patch(
    "bass wobble",
    (Osc("saw", voices=3, spread=18.0), Osc("pulse", semitones=12, width=0.35, level=0.6),
     Osc("saw", semitones=-12, level=0.6)),
    filter="none", amplitude=Envelope(0.003, 0.1, 1.0, 0.05), glide=0.04, stereo=0.5,
    drift_cents=2.0, gain_db=0.0,
)  # fmt: skip

# ------------------------------------------------------------------ FM

# An electric piano with tines, in the manner of the Yamaha DX7.
EPIANO_FM = FMPatch(
    "epiano fm",
    (
        Operators(ratio=1.0, index=1.1, index_decay=0.7, index_sustain=0.15, level=1.0,
                  amplitude=Envelope(0.002, 3.2, 0.0, 0.3), pan=0.42),
        Operators(ratio=1.0, index=0.7, index_decay=0.9, index_sustain=0.2, level=0.7,
                  amplitude=Envelope(0.002, 2.6, 0.0, 0.3), cents=4.0, pan=0.58),
        Operators(ratio=14.0, index=0.8, index_decay=0.07, index_sustain=0.0, level=0.3,
                  amplitude=Envelope(0.001, 0.3, 0.0, 0.1), pan=0.5),
    ),
    velocity_index=2.2, tremolo_hz=4.6, tremolo_depth=0.22, gain_db=3.0,
)  # fmt: skip

# A bell: the frequencies of the operators are not multiples of the note.
BELL_FM = FMPatch(
    "bell fm",
    (
        Operators(ratio=3.5, index=2.4, index_decay=1.2, index_sustain=0.1, level=0.8,
                  amplitude=Envelope(0.001, 4.5, 0.0, 1.2), pan=0.35),
        Operators(ratio=1.41, carrier_ratio=2.0, index=1.6, index_decay=0.6, index_sustain=0.05,
                  level=0.45, amplitude=Envelope(0.001, 2.2, 0.0, 0.8), pan=0.65),
    ),
    velocity_index=1.2, gain_db=0.0,
)  # fmt: skip

# A hard bass with a voice-like growl: the modulator has feedback.
BASS_GROWL = FMPatch(
    "bass growl",
    (
        Operators(ratio=1.0, index=3.2, index_decay=0.5, index_sustain=0.8, feedback=0.55,
                  level=1.0, amplitude=Envelope(0.003, 0.2, 1.0, 0.05), pan=0.5),
        Operators(ratio=2.0, carrier_ratio=1.0, index=2.0, index_decay=0.3, index_sustain=0.7,
                  feedback=0.3, level=0.6, amplitude=Envelope(0.003, 0.2, 1.0, 0.05), cents=9.0,
                  pan=0.5),
    ),
    velocity_index=1.0, range_db=14.0, gain_db=0.0,
)  # fmt: skip

SUBTRACTIVE = {
    patch.name: patch
    for patch in (LEAD_MOOG, LEAD_SQUARE, LEAD_WIND, SUPERSAW, PLUCK, PAD_WARM, PAD_GLASS,
                  SYNTH_BRASS, BASS_MOOG, BASS_SUB, BASS_REESE, BASS_WOBBLE)
}  # fmt: skip
FM = {patch.name: patch for patch in (EPIANO_FM, BELL_FM, BASS_GROWL)}
