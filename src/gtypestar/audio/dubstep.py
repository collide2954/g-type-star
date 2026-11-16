"""The bass sounds of the dubstep passage (the helium flash).

A dubstep bass has two layers:

- The sub: one clean sine tone in the lowest octave (41 to 82 Hz), in the
  centre. It gives the weight, and it does not change with the sound above it.
- The middle: a hard, bright sound with nothing below about 100 Hz. It
  "speaks": in each note, a filter or the depth of a modulation moves one
  time. Thus the rhythm of the notes is the rhythm of the move (eighth
  notes, triplets, sixteenth notes), and the score shows it.

The style changes the sound of the middle layer from note to note, as a
call and an answer. This module has six sounds. The player changes between
them with the command `\\switch`:

- "bass wobble": a low-pass filter opens and closes one time in each note.
- "bass growl": two sine pairs with frequency modulation; two resonances
  move from one vowel to a different vowel; a fast rattle.
- "bass yoi": two resonances go from the vowel "i" to "o" and back: the
  sound says "yoi".
- "bass screech": a high, narrow resonance that rises, two octaves above
  the note.
- "bass grind": sawtooth waves that are out of tune, with a notch that moves
  (the "Reese" bass of jungle), dark and wide.
- "bass gun": a very short stroke whose pitch falls fast, for fast repeats.

All middle sounds get the same end: distortion, a compressor for three
bands that makes loud parts softer and soft parts louder (the "OTT" sound
of the style), and width above 200 Hz. The values come from the rows
"Dubstep" and "Brostep" of `research/tables/electronics.csv`.
"""

from __future__ import annotations

import zlib

import numpy as np
from scipy import signal

from ..perform.feel import Event
from . import dsp, effects, kernels

RATE = float(dsp.RATE)
SOUNDS = ("bass wobble", "bass growl", "bass yoi", "bass screech", "bass grind", "bass gun")

SUB_LOW = 41.0  # hertz: the sub tone is between this value and one octave above it
SUB_GAIN = {"bass screech": 0.55, "bass gun": 0.75}  # the sub is softer under these sounds
SUB_LEVEL = 0.45  # the amplitude of the sub tone at full level
# The level (RMS) of the middle layer while it sounds. In this style the bass is the
# lead voice: its middle layer is as loud as the saxophone and the guitar in the mix.
MIDDLE_LEVEL = 0.45
# The compressor for three bands makes the high bands louder: the style is bright and hard.
BAND_GAINS_DB = (0.0, 5.0, 12.0)
FIZZ_DB = -9.0  # a hard-clipped copy of the band from 1.5 to 7 kHz, under the sound
CROSSOVER = 105.0  # hertz: the middle layer has nothing below, the sub nothing above
WIDTH_FROM = 200.0  # hertz: below this value the sound is in the centre
TOP = 9000.0  # hertz: the highest part of the distortion is cut
ATTACK, RELEASE = 0.004, 0.03  # seconds
GLIDE = 0.018  # seconds: the sub slides from one note to the next
RATTLE_HZ = 140.0 / 60.0 * 8.0  # thirty-second notes at 140 quarter notes in a minute

# The two lowest resonances of the vowels of a low voice, in hertz.
VOWELS = {"a": (850.0, 1610.0), "e": (390.0, 2300.0), "i": (240.0, 2400.0),
          "o": (360.0, 640.0), "u": (250.0, 595.0)}  # fmt: skip
# The growl goes from the first vowel to the second vowel. The notes take turns.
VOWEL_MOVES = (("u", "a"), ("o", "e"), ("a", "i"), ("e", "u"), ("a", "o"), ("i", "a"))


def _random(*keys: object) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(repr(keys).encode()))


def held(event: Event) -> float:
    """Return how long the note sounds, in seconds: the notes of the style are tight."""
    marks = event.note.articulations
    if "staccatissimo" in marks:
        return max(0.03, 0.3 * event.seconds)
    if "staccato" in marks:
        return max(0.04, 0.5 * event.seconds)
    return max(0.04, event.seconds - min(0.02, 0.1 * event.seconds))


def sub_hertz(hertz: float) -> float:
    """Return the frequency of the sub tone for a note: the same note in the lowest octave."""
    while hertz >= 2.0 * SUB_LOW:
        hertz /= 2.0
    while hertz < SUB_LOW:
        hertz *= 2.0
    return hertz


def _between(first: float, second: float, share: np.ndarray) -> np.ndarray:
    """Go from one frequency to a different frequency in equal ratios."""
    return first * (second / first) ** share


# ----------------------------------------------------------------------------
# The middle layer: one function for each sound. Each returns two channels.
# `frequency` is the pitch of each sample in hertz. `share` goes from 0 to 1
# in the time of the note.
# ----------------------------------------------------------------------------


def _wobble(frequency: np.ndarray, share: np.ndarray, level: float, random) -> np.ndarray:
    """Sawtooth waves through a low-pass filter that opens and closes one time."""
    total = len(frequency)
    top = 650.0 + 3600.0 * level
    move = np.sin(np.pi * share**0.8) ** 1.4
    cutoff = _between(130.0, top, move)
    out = np.empty((total, 2))
    for channel, cents in enumerate(((-13.0, 2.0, 9.0), (-8.0, -1.0, 14.0))):
        source = np.zeros(total)
        for value in cents:
            tuned = frequency * 2.0 ** (value / 1200.0)
            source += kernels.saw(tuned, RATE, float(random.uniform()))
        source += 0.7 * kernels.pulse(2.0 * frequency, np.full(total, 0.38), RATE,
                                      float(random.uniform()))  # fmt: skip
        out[:, channel] = kernels.ladder(source * 0.5, cutoff, 0.5, 2.5, RATE)
    return out


def _growl(frequency: np.ndarray, share: np.ndarray, level: float, number: int) -> np.ndarray:
    """Frequency modulation with a depth that moves, through two moving vowel resonances."""
    total = len(frequency)
    first, second = VOWEL_MOVES[number % len(VOWEL_MOVES)]
    move = np.clip(share / 0.75, 0.0, 1.0) ** 0.8
    low = _between(VOWELS[first][0], VOWELS[second][0], move)
    high = _between(VOWELS[first][1], VOWELS[second][1], move)
    depth = 1.5 + (4.0 + 3.0 * level) * np.sin(np.pi * share) ** 2
    time = np.arange(total) / RATE
    rattle = 1.0 + 0.3 * signal.sawtooth(2.0 * np.pi * RATTLE_HZ * time)
    quality = np.full(total, 6.0)
    out = np.empty((total, 2))
    for channel, cents in enumerate((0.0, 7.0)):
        tuned = frequency * 2.0 ** (cents / 1200.0)
        # The modulators are at the note and at three times the note: all partials are
        # partials of the note (ratios 0.5 : 1 and 3 : 1).
        source = kernels.fm_pair(2.0 * tuned, 0.5, depth * rattle, 0.55, RATE)
        source += 0.6 * kernels.fm_pair(tuned, 3.0, 0.6 * depth, 0.3, RATE)
        one = kernels.state_variable(source, low, quality, RATE, 1)
        two = kernels.state_variable(source, high, quality, RATE, 1)
        out[:, channel] = 2.0 * one + 1.8 * two + 0.55 * source
    return out


def _yoi(frequency: np.ndarray, share: np.ndarray, level: float, random) -> np.ndarray:
    """A bright source through resonances that go from "i" to "o" and back to "i"."""
    total = len(frequency)
    dip = np.sin(np.pi * share) ** 0.7
    low = _between(VOWELS["i"][0], VOWELS["o"][0], dip)
    high = _between(VOWELS["i"][1], VOWELS["o"][1], dip)
    third = np.full(total, 2900.0)
    out = np.empty((total, 2))
    for channel, cents in enumerate((-6.0, 6.0)):
        tuned = frequency * 2.0 ** (cents / 1200.0)
        source = kernels.pulse(2.0 * tuned, np.full(total, 0.3), RATE, float(random.uniform()))
        source += 0.8 * kernels.saw(tuned, RATE, float(random.uniform()))
        one = kernels.state_variable(source, low, np.full(total, 8.0), RATE, 1)
        two = kernels.state_variable(source, high, np.full(total, 9.0), RATE, 1)
        three = kernels.state_variable(source, third, np.full(total, 6.0), RATE, 1)
        mixed = 1.6 * one + 2.2 * two + 0.5 * three + 0.15 * source
        out[:, channel] = mixed * (0.7 + 0.3 * level)
    return out


def _screech(frequency: np.ndarray, share: np.ndarray, level: float, number: int) -> np.ndarray:
    """A high tone through a narrow resonance that rises: a scream."""
    total = len(frequency)
    # The pitch rises in the notes with an even number, and falls in the other notes.
    bend = 5.0 * share**1.5 if number % 2 == 0 else -7.0 * share**1.2
    tone = 4.0 * frequency * 2.0 ** (bend / 12.0)
    centre = _between(1100.0, 3400.0, share if number % 2 == 0 else 1.0 - share)
    out = np.empty((total, 2))
    for channel, cents in enumerate((-9.0, 9.0)):
        tuned = tone * 2.0 ** (cents / 1200.0)
        source = kernels.saw(tuned, RATE, 0.25 * channel)
        source += 0.8 * kernels.fm_pair(tuned, 2.0, np.full(total, 2.0 + 3.0 * level), 0.4, RATE)
        narrow = kernels.state_variable(source, centre, np.full(total, 9.0), RATE, 1)
        high = kernels.state_variable(source, np.full(total, 600.0), np.full(total, 0.7), RATE, 2)
        out[:, channel] = 2.5 * narrow + 0.3 * high
    return out


def _grind(frequency: np.ndarray, share: np.ndarray, level: float, random) -> np.ndarray:
    """Sawtooth waves that are out of tune, with a notch that moves down and up."""
    total = len(frequency)
    centre = _between(2300.0, 320.0, 0.5 - 0.5 * np.cos(2.0 * np.pi * share))
    cutoff = np.full(total, 900.0 + 2600.0 * level)
    out = np.empty((total, 2))
    for channel, cents in enumerate(((-27.0, 24.0), (-22.0, 29.0))):
        source = 0.6 * kernels.saw(frequency, RATE, float(random.uniform()))
        for value in cents:
            tuned = 2.0 * frequency * 2.0 ** (value / 1200.0)
            source += kernels.saw(tuned, RATE, float(random.uniform()))
        notched = kernels.state_variable(source, centre, np.full(total, 2.5), RATE, 3)
        out[:, channel] = kernels.ladder(notched * 0.5, cutoff, 0.25, 3.0, RATE)
    return out


def _gun(frequency: np.ndarray, level: float) -> np.ndarray:
    """A short stroke: the pitch and the depth of the modulation fall in a few milliseconds."""
    total = len(frequency)
    time = np.arange(total) / RATE
    tone = 2.0 * frequency * 2.0 ** (19.0 / 12.0 * np.exp(-time / 0.012))
    depth = 1.0 + (5.0 + 3.0 * level) * np.exp(-time / 0.03)
    out = np.empty((total, 2))
    for channel, cents in enumerate((0.0, 11.0)):
        tuned = tone * 2.0 ** (cents / 1200.0)
        # The ratio 1.41 gives partials that are not partials of the note: a metal sound.
        out[:, channel] = kernels.fm_pair(tuned, 1.41, depth, 0.5, RATE) * np.exp(-time / 0.05)
    return out


# The distortion of each sound, before the sounds come together.
def _character(name: str, sound: np.ndarray) -> np.ndarray:
    if name == "bass wobble":
        return effects.saturate(sound, 8.0, bias=0.2)
    if name == "bass growl":
        return effects.saturate(effects.fold(0.5 * sound, 5.0), 4.0)
    if name == "bass yoi":
        return effects.saturate(0.6 * sound, 10.0, bias=0.1)
    if name == "bass screech":
        return effects.saturate(0.6 * sound, 16.0)
    if name == "bass grind":
        return effects.saturate(sound, 9.0, bias=0.15)
    # "bass gun": a wave folder, then few level steps and a low sample rate.
    return effects.crush(effects.fold(0.7 * sound, 6.0), bits=6.0, hold=3)


# ----------------------------------------------------------------------------
# The end of the middle layer
# ----------------------------------------------------------------------------


def squash(
    sound: np.ndarray,
    amount: float = 0.75,
    edges: tuple[float, float] = (350.0, 2500.0),
    up_db: float = 14.0,
    down_db: float = 24.0,
    gains_db: tuple[float, float, float] = BAND_GAINS_DB,
) -> np.ndarray:
    """Compress three bands, down and up: each band comes near to its usual level.

    This is the "OTT" sound of the style. In each band, a part that is
    louder than the usual level becomes softer, and a part that is softer
    becomes louder (not more than `up_db`). Very soft sound (silence, the
    end of a note) gets no gain. `amount` is the share of the level
    difference that the compressor removes.
    """
    low = signal.sosfilt(dsp.lowpass(edges[0], 4), sound, axis=0)
    high = signal.sosfilt(dsp.highpass(edges[1], 4), sound, axis=0)
    middle = sound - low - high
    out = np.zeros_like(sound)
    for band, more in zip((low, middle, high), gains_db, strict=True):
        control = np.abs(band).max(axis=1).astype(np.float64)
        level = kernels.follow(control, 0.003, 0.07, RATE)
        loud = level[level > 1e-4]
        if len(loud) == 0:
            continue
        usual = float(np.percentile(loud, 75))
        below = 20.0 * np.log10(np.maximum(level, 1e-9) / usual)
        gain_db = np.clip(-amount * below, -down_db, up_db)
        # No gain for sound that is more than 55 dB below the usual level.
        gain_db *= np.clip((below + 55.0) / 15.0, 0.0, 1.0)
        out += band * (10.0 ** ((gain_db + more) / 20.0))[:, None]
    return out


def fizz(sound: np.ndarray) -> np.ndarray:
    """Add a hard-clipped copy of the upper middle band: the rough top of the sound."""
    band = signal.butter(2, [1500.0, 7000.0], "bandpass", fs=RATE, output="sos")
    part = signal.sosfilt(band, sound, axis=0)
    usual = float(np.percentile(np.abs(part), 99.0)) or 1.0
    hard = effects.saturate(part / usual, 18.0)
    hard = signal.sosfilt(band, hard, axis=0) * usual
    return sound + hard * dsp.db(FIZZ_DB)


def widen(sound: np.ndarray, side_gain: float = 0.5) -> np.ndarray:
    """Keep the low part in the centre, and set the width of the part above `WIDTH_FROM`.

    The two channels of the middle layer are two sounds that are a little out of
    tune: their difference is as loud as their sum. A bass must stay strong on
    one loudspeaker, thus the difference becomes softer.
    """
    mid = 0.5 * (sound[:, 0] + sound[:, 1])
    side = 0.5 * (sound[:, 0] - sound[:, 1])
    side = signal.sosfilt(dsp.highpass(WIDTH_FROM, 2), side) * side_gain
    return np.stack([mid + side, mid - side], axis=1)


def _middle(events: list[Event], total: int, player: str) -> np.ndarray:
    """Return the middle layer of all notes."""
    layers = {name: np.zeros((total, 2)) for name in SOUNDS}
    for number, event in enumerate(events):
        name = event.note.instrument
        begin = int(event.start * RATE)
        if begin >= total:
            continue
        length = held(event)
        count = min(total - begin, int((length + 4.0 * RELEASE) * RATE))
        time = np.arange(count) / RATE
        share = np.clip(time / length, 0.0, 1.0)
        level = float(np.clip(event.level + event.note.accent, 0.0, 1.0))
        hertz = 440.0 * 2.0 ** ((event.midi - 69.0) / 12.0)
        frequency = np.full(count, hertz)
        following = events[number + 1] if number + 1 < len(events) else None
        if event.note.glissando and following is not None:
            # A slide to the next note, in the second half of the note.
            span = following.midi - event.midi
            frequency = hertz * 2.0 ** (span * np.clip((share - 0.4) / 0.6, 0.0, 1.0) ** 1.5 / 12.0)
        random = _random(player, number, name)
        if name == "bass wobble":
            sound = _wobble(frequency, share, level, random)
        elif name == "bass growl":
            sound = _growl(frequency, share, level, number)
        elif name == "bass yoi":
            sound = _yoi(frequency, share, level, random)
        elif name == "bass screech":
            sound = _screech(frequency, share, level, number)
        elif name == "bass grind":
            sound = _grind(frequency, share, level, random)
        else:
            sound = _gun(frequency, level)
        gate = np.minimum(time / ATTACK, 1.0)
        gate *= np.where(time < length, 1.0, np.exp(-(time - length) / (RELEASE / 3.0)))
        layers[name][begin : begin + count] += sound * (gate * (0.35 + 0.65 * level))[:, None]
    out = np.zeros((total, 2))
    for name, layer in layers.items():
        if np.any(layer):
            # Each sound gets its own level before the distortion, then its distortion.
            peak = float(np.percentile(np.abs(layer[np.abs(layer).max(axis=1) > 1e-4]), 99.0))
            out += _character(name, layer / max(peak, 1e-6))
    out = signal.sosfilt(dsp.highpass(CROSSOVER, 4), out, axis=0)
    # More level above 1 kHz before the distortion: the distortion makes more high partials.
    out = signal.sosfilt(dsp.shelf(1000.0, 8.0, high=True), out, axis=0)
    usual = float(np.percentile(np.abs(out), 99.0)) or 1.0
    out = effects.saturate(out / usual, 10.0, bias=0.1)
    out = fizz(squash(out))
    out = signal.sosfilt(np.vstack([dsp.highpass(CROSSOVER, 2), dsp.lowpass(TOP, 2)]), out, axis=0)
    out = widen(out)
    sounding = np.abs(out).max(axis=1) > 1e-3
    if np.any(sounding):
        out *= MIDDLE_LEVEL / max(float(np.sqrt(np.mean(out[sounding] ** 2))), 1e-9)
    return effects.clip(out, -4.0, 0.3)


def _sub(events: list[Event], total: int) -> np.ndarray:
    """Return the sub layer: one sine tone that goes on from note to note (one channel)."""
    frequency = np.zeros(total)
    level = np.zeros(total)
    place = 0
    for number, event in enumerate(events):
        begin = int(event.start * RATE)
        if begin >= total:
            break
        length = held(event)
        end = min(total, begin + int(length * RATE))
        hertz = sub_hertz(440.0 * 2.0 ** ((event.midi - 69.0) / 12.0))
        frequency[place:end] = hertz  # the pitch is there before the note starts: no slide in
        following = events[number + 1] if number + 1 < len(events) else None
        if event.note.glissando and following is not None:
            target = sub_hertz(440.0 * 2.0 ** ((following.midi - 69.0) / 12.0))
            if abs(following.midi - event.midi) <= 12:
                place_in_note = np.arange(end - begin) / max(end - begin, 1)
                share = np.clip((place_in_note - 0.4) / 0.6, 0.0, 1.0)
                frequency[begin:end] = _between(hertz, target, share**1.5)
        loud = float(np.clip(event.level + 0.5 * event.note.accent, 0.0, 1.0)) ** 0.5
        level[begin:end] = loud * SUB_GAIN.get(event.note.instrument, 1.0)
        place = end
    frequency[place:] = frequency[place - 1] if place else SUB_LOW
    frequency = np.maximum(frequency, SUB_LOW / 2.0)
    # The slide between two notes. The filter starts at the pitch of the first note.
    cutoff = np.full(total, 1.0 / (2.0 * np.pi * GLIDE))
    smooth = frequency[0] + kernels.one_pole(frequency - frequency[0], cutoff, RATE)
    shape = kernels.follow(level, ATTACK, RELEASE, RATE)
    tone = kernels.sine(smooth, RATE, 0.0) * shape
    tone = np.tanh(1.4 * tone) / np.tanh(1.4)
    return signal.sosfilt(dsp.lowpass(160.0, 2), tone) * SUB_LEVEL


def render(events: list[Event], seconds: float, player: str) -> np.ndarray:
    """Play the dubstep bass notes of a player. Each event names its sound."""
    total = int(seconds * RATE) + int(RATE)
    ordered = sorted(events, key=lambda event: event.start)
    out = _middle(ordered, total, player)
    out += effects.stereo(_sub(ordered, total)) * np.sqrt(2.0)
    return out.astype(np.float32)
