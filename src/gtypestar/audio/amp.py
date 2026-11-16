"""Guitar and bass amplifiers, and the string model for the guitar and the bass.

The signal of an electric guitar goes through an amplifier with much gain
and through a loudspeaker cabinet. The amplifier makes new partials from all
strings together: thus a chord through the amplifier is not the sum of its
notes through the amplifier. The code plays all strings into one signal and
then uses the amplifier one time.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

import numpy as np
import soxr
from scipy import signal

from . import dsp, kernels

RATE = float(dsp.RATE)


@dataclass(frozen=True)
class Amp:
    """The settings of an amplifier."""

    tight_hz: float = 110.0  # low cut before the gain: a tight low end
    push_hz: float = 900.0  # middle boost before the gain (an overdrive pedal)
    push_db: float = 8.0
    gain_db: float = 34.0
    stages: int = 3
    bias: float = 0.12  # makes the two halves of the wave different (even partials)
    low_db: float = 3.0  # tone controls after the gain
    mid_hz: float = 650.0
    mid_db: float = -4.0
    presence_db: float = 3.0
    cabinet: bool = True
    gate_db: float = -62.0  # the noise gate closes below this level
    level_db: float = -19.0


CLEAN = Amp(tight_hz=70.0, push_db=0.0, gain_db=6.0, stages=1, bias=0.05, low_db=1.0, mid_db=-2.0,
            presence_db=2.0, gate_db=-80.0, level_db=-8.0)  # fmt: skip
CRUNCH = Amp(tight_hz=90.0, push_db=5.0, gain_db=20.0, stages=2, mid_db=-1.0, level_db=-19.0)
HIGH_GAIN = Amp()
LEAD = Amp(tight_hz=140.0, push_hz=1100.0, push_db=10.0, gain_db=38.0, mid_db=1.0, presence_db=1.0,
           level_db=-17.0)  # fmt: skip
BASS_GRIT = Amp(tight_hz=45.0, push_hz=700.0, push_db=4.0, gain_db=16.0, stages=2, bias=0.2,
                low_db=2.0, mid_hz=400.0, mid_db=-2.0, presence_db=1.0, cabinet=False,
                gate_db=-80.0, level_db=-8.0)  # fmt: skip


def cabinet(samples: np.ndarray) -> np.ndarray:
    """The tone of a closed cabinet with four 12-inch loudspeakers and a near microphone."""
    sections = np.vstack(
        [
            dsp.highpass(75.0, 2),
            dsp.peaking(120.0, 3.0, 1.2),
            dsp.peaking(400.0, -3.0, 1.0),
            dsp.peaking(2600.0, 4.0, 1.4),
            dsp.peaking(4200.0, 2.0, 2.5),
            dsp.lowpass(5200.0, 4),
            dsp.lowpass(7500.0, 2),
        ]
    )
    return signal.sosfilt(sections, samples)


def amplify(samples: np.ndarray, amp: Amp = HIGH_GAIN) -> np.ndarray:
    """Send a signal with one channel through an amplifier and its cabinet."""
    dry = samples.astype(np.float64)
    # The gate uses the level of the input: the amplifier makes soft noise loud.
    level = kernels.follow(dry, 0.002, 0.06, RATE)
    gate = np.clip((20.0 * np.log10(level + 1e-9) - amp.gate_db) / 6.0, 0.0, 1.0)
    before = [dsp.highpass(amp.tight_hz, 2)]
    if amp.push_db:
        before.append(dsp.peaking(amp.push_hz, amp.push_db, 0.7))
    shaped = signal.sosfilt(np.vstack(before), dry)
    high = soxr.resample(shaped, RATE, RATE * 4, quality="HQ")
    gain = dsp.db(amp.gain_db / amp.stages)
    for stage in range(amp.stages):
        bias = amp.bias * (1.0 if stage % 2 == 0 else -0.6)
        high = np.tanh(gain * high + bias) - np.tanh(bias)
        # Between two stages the low end gets smaller: the sound stays clear.
        high = signal.sosfilt(dsp.highpass(60.0 + 40.0 * stage, 1, rate=int(RATE * 4)), high)
    out = soxr.resample(high, RATE * 4, RATE, quality="HQ")[: len(dry)]
    tone = [
        dsp.shelf(120.0, amp.low_db, high=False),
        dsp.peaking(amp.mid_hz, amp.mid_db, 0.8),
        dsp.peaking(3200.0, amp.presence_db, 1.0),
    ]
    out = signal.sosfilt(np.vstack(tone), out)
    if amp.cabinet:
        out = cabinet(out)
    gate = gate[: len(out)]
    return out * gate * dsp.db(amp.level_db)


# ----------------------------------------------------------------------------
# The strings
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class StringNote:
    """One note of a guitar or a bass: times in seconds."""

    start: float
    seconds: float
    midi: float
    level: float
    mute: float = 0.0  # 0 = open string; 1 = fully palm-muted
    slide_from: float | None = None  # the pitch at the start, if the player slides to the note
    bend: tuple[float, ...] = ()  # pitch curve in semitones for the time of the note
    vibrato: float = 0.0  # depth in cents
    hammer: bool = False  # the left hand starts the note: no pick attack
    harmonic: bool = False
    dead: bool = False  # a note with no pitch: the left hand stops the string


@dataclass(frozen=True)
class StringModel:
    """The body of an electric string instrument and its pickup."""

    name: str = "guitar"
    sustain: float = 6.0  # seconds for a decay of 60 dB of an open middle note
    brightness: float = 0.72
    stiffness: float = 0.12
    pick: float = 0.13  # place of the pick as a share of the string length
    pickup: float = 0.08  # place of the pickup as a share of the string length
    pick_noise: float = 0.6
    pickup_tone_hz: float = 4200.0  # the coil of the pickup is a low-pass filter


GUITAR = StringModel()
BASS = StringModel("bass", sustain=9.0, brightness=0.55, stiffness=0.3, pick=0.17, pickup=0.12,
                   pick_noise=0.35, pickup_tone_hz=2600.0)  # fmt: skip


def pluck(model: StringModel, note: StringNote, seed: object = 0) -> np.ndarray:
    """Return the direct signal of one note of a string (one channel, before the amplifier)."""
    random = np.random.default_rng(zlib.crc32(repr((model.name, seed, note.start)).encode()))
    release = 0.03 if note.mute > 0.5 or note.dead else 0.05
    total = int((note.seconds + release + 0.02) * RATE)
    time = np.arange(total) / RATE
    pitch = np.full(total, float(note.midi))
    if note.slide_from is not None:
        pitch += (note.slide_from - note.midi) * np.exp(-time / 0.035)
    if note.bend:
        held = max(1, int(note.seconds * RATE))
        curve = np.interp(np.linspace(0, len(note.bend) - 1, held), np.arange(len(note.bend)),
                          np.array(note.bend))  # fmt: skip
        pitch[:held] += curve[: min(held, total)]
        pitch[held:] += curve[-1]
    if note.vibrato:
        depth = np.clip((time - 0.18) / 0.3, 0.0, 1.0) * note.vibrato / 100.0
        pitch += depth * np.sin(2 * np.pi * (5.6 + 0.3 * random.normal()) * time)
    # A hard stroke makes the pitch sharp for a moment.
    pitch += 0.12 * note.level * np.exp(-time / 0.025)
    frequency = 440.0 * 2.0 ** ((pitch - 69.0) / 12.0)
    if note.harmonic:
        frequency = frequency  # the written pitch is the sounding pitch of the harmonic
    period = RATE / frequency[0]

    # The pluck: a short burst of noise. The place of the pick removes some partials.
    burst = int(max(period, 32))
    excitation = np.zeros(total)
    shape = random.uniform(-1.0, 1.0, burst)
    softness = 0.25 + 0.75 * (1.0 - note.level)  # a soft stroke has a dark start
    shape = signal.lfilter([1.0 - softness * 0.85], [1.0, -softness * 0.85], shape)
    if note.hammer:
        shape = signal.lfilter([0.15], [1.0, -0.85], shape)
    excitation[:burst] = shape
    lag = max(1, int(round(model.pick * period)))
    comb = np.zeros(total)
    comb[lag:] = excitation[:-lag]
    excitation = excitation - comb
    if not note.hammer:
        click = random.normal(0.0, 1.0, total) * np.exp(-time / 0.0025)
        excitation += (
            model.pick_noise
            * (0.3 + 0.7 * note.level)
            * signal.sosfilt(dsp.highpass(1800.0, 1), click)
        )

    # The decay: low notes ring longer; a palm mute stops the string fast.
    register = 2.0 ** (-(note.midi - 52.0) / 24.0)
    ring = model.sustain * register
    ring = ring * (1.0 - note.mute) + (0.045 + 0.1 * (1.0 - note.mute)) * note.mute
    brightness = model.brightness * (1.0 - 0.45 * note.mute)
    if note.dead:
        ring, brightness = 0.03, 0.3
    decay = np.full(total, ring)
    held = int(note.seconds * RATE)
    decay[held:] = 0.03  # the hand stops the string at the end of the note
    bright = np.full(total, brightness)
    out = kernels.plucked_string(excitation, frequency, decay, bright, model.stiffness, RATE)

    # The pickup hears the string at one place: this removes some partials.
    lag = max(1, int(round(model.pickup * period)))
    heard = out.copy()
    heard[lag:] -= 0.6 * out[:-lag]
    heard = signal.sosfilt(dsp.lowpass(model.pickup_tone_hz, 2), heard)
    return heard * (0.2 + 0.8 * note.level**1.3) * 0.5


def play(model: StringModel, notes: list[StringNote], seconds: float, seed: object = 0):
    """Return the direct signal of all notes of one player (one channel)."""
    out = np.zeros(int(seconds * RATE) + int(0.5 * RATE))
    for number, note in enumerate(notes):
        sound = pluck(model, note, (seed, number))
        start = int(note.start * RATE)
        if start >= len(out):
            continue
        end = min(len(out), start + len(sound))
        out[start:end] += sound[: end - start]
    return out
