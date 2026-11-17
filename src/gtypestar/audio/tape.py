"""Recorded sounds: voices of space missions, radio noise, and the sound of the Sun.

The part "Recorded Sounds" of the work is a list of cues. A cue starts a
sound at a place in the music. There are two kinds of sound:

- A file in the directory `.cache/media`: a public-domain recording, for
  example the radio traffic of a space mission. If the file is not there,
  the cue is silent and the render shows a message.
- A sound that code makes from physical values: the tones that start and
  stop a radio message of the Apollo missions, radio noise, a data signal,
  and the oscillations of the Sun at a speed that the ear can hear.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import soxr
from scipy import signal

from ..notation.work import Work
from . import dsp, effects, kernels

RATE = dsp.RATE
MEDIA_DIR = Path(".cache/media")


@dataclass(frozen=True)
class Cue:
    """One recorded sound at a place in the music."""

    sound: str  # the name of a file in the media directory, or of a sound that code makes
    bar: int
    beat: Fraction | float = 1  # in quarter notes; 1 = start of the bar
    length: Fraction | float | None = None  # quarter notes; None = the length of the sound
    seconds: float | None = None  # the length in seconds, for the sounds that code makes
    gain_db: float = -14.0
    offset: float = 0.0  # start in the file, in seconds
    speed: float = 1.0  # 2 = one octave higher and two times as fast
    reverse: bool = False
    pan: float = 0.0
    radio: bool = False  # the narrow band of a radio message (300 to 3400 Hz), with distortion
    fade: float = 0.05  # seconds at the start and at the end
    seed: int = 0
    text: str = ""  # the words of a voice, for the score
    # Notes (MIDI numbers) on which the sound rings: narrow filters at these notes and at
    # the octaves above them. With these, noise gets the pitch of the music.
    ring: tuple[int, ...] = ()
    ring_mix: float = 0.8  # the share of the filtered sound (the rest is the plain sound)

    @property
    def label(self) -> str:
        """Return the text of the cue in the score."""
        name = LABELS.get(self.sound, self.sound)
        if self.text:
            name = f"{name}: \u201c{self.text}\u201d"
        if self.seconds is not None and self.seconds >= 8.0:
            name += f" ({self.seconds:.0f} seconds)"
        return name


# The names of the sounds in the score.
LABELS = {
    "sun": "The Sun: its oscillations, 42 000 times faster",
    "sun-sonification": "The Sun: recording of the Solar and Heliospheric Observatory",
    "wind": "Noise: wind of particles",
    "quindar on": "Radio tone: start of a message",
    "quindar off": "Radio tone: end of a message",
    "static": "Radio noise",
    "telemetry": "Data signal",
    "mercury3-548": "Voice (Mercury 3, 1961)",
    "apollo10-onboard": "Voice (Apollo 10, 1969)",
    "voyager-heliosphere": "Voyager 1: plasma waves outside the heliosphere",
    "voyager-termination-shock": "Voyager 1: the termination shock",
    "earth-chorus": "Earth: radio waves of the radiation belts",
    "cassini-saturn-radio": "Cassini: radio emissions of Saturn",
}


# ----------------------------------------------------------------------------
# Sounds that code makes
# ----------------------------------------------------------------------------

# The Sun oscillates with a period near five minutes. The modes with the most power
# have frequencies near 3090 microhertz, 135 microhertz apart (the "large separation").
# Played 42 000 times faster, they are near 130 Hz, 5.7 Hz apart: a low hum with beats.
SUN_PEAK_MICROHERTZ = 3090.0
SUN_SEPARATION_MICROHERTZ = 135.0
SUN_WIDTH_MICROHERTZ = 1000.0  # full width at half maximum of the power
SUN_SPEED = 42000.0


def sun(seconds: float, seed: int = 0, speed: float = SUN_SPEED) -> np.ndarray:
    """The oscillations of the Sun, faster: a sum of its strongest modes. Two channels."""
    random = np.random.default_rng(seed)
    time = np.arange(int(seconds * RATE)) / RATE
    out = np.zeros((len(time), 2))
    sigma = SUN_WIDTH_MICROHERTZ / 2.355
    for order in range(-9, 10):
        for degree, share in ((0, 1.0), (1, 0.85), (2, 0.5)):
            # Modes of degree 1 are half a separation from the modes of degree 0.
            micro = SUN_PEAK_MICROHERTZ + (order + degree / 2.0) * SUN_SEPARATION_MICROHERTZ
            micro -= 9.0 * (degree == 2)  # the small separation
            power = np.exp(-0.5 * ((micro - SUN_PEAK_MICROHERTZ) / sigma) ** 2)
            frequency = micro * 1e-6 * speed
            # Each mode lives some days: its level changes slowly and at random.
            knots = random.rayleigh(1.0, int(seconds / 1.3) + 3)
            level = np.interp(time / 1.3, np.arange(len(knots)), knots)
            phase = random.uniform(0.0, 2 * np.pi)
            wave = np.sin(2 * np.pi * frequency * time + phase) * level * np.sqrt(power) * share
            side = random.uniform(0.2, 0.8)
            out[:, 0] += wave * np.cos(side * np.pi / 2)
            out[:, 1] += wave * np.sin(side * np.pi / 2)
    return out / 14.0


def quindar(start: bool = True) -> np.ndarray:
    """The tone at the start (2525 Hz) or at the end (2475 Hz) of an Apollo radio message."""
    time = np.arange(int(0.25 * RATE)) / RATE
    tone = np.sin(2 * np.pi * (2525.0 if start else 2475.0) * time)
    tone *= np.minimum(1.0, np.minimum(time, 0.25 - time) / 0.004)
    return effects.stereo(tone * 0.5)


def static(seconds: float, seed: int = 0) -> np.ndarray:
    """Radio noise: hiss in a narrow band, with crackle and a slow change of level."""
    random = np.random.default_rng(seed)
    total = int(seconds * RATE)
    hiss = random.normal(0.0, 1.0, total)
    band = signal.butter(2, [400.0, 3200.0], "bandpass", fs=RATE, output="sos")
    hiss = signal.sosfilt(band, hiss)
    knots = random.uniform(0.4, 1.0, int(seconds / 0.4) + 3)
    hiss *= np.interp(np.arange(total) / (0.4 * RATE), np.arange(len(knots)), knots)
    crackle = (random.uniform(0.0, 1.0, total) < 0.0006) * random.normal(0.0, 6.0, total)
    crackle = signal.sosfilt(dsp.highpass(1500.0, 1), crackle)
    return effects.stereo((hiss + crackle) * 0.12)


def telemetry(seconds: float, seed: int = 0) -> np.ndarray:
    """A data signal: fast changes between two tones, as a modem."""
    random = np.random.default_rng(seed)
    total = int(seconds * RATE)
    bits = random.integers(0, 2, int(seconds * 300) + 2)
    index = np.minimum((np.arange(total) / RATE * 300).astype(int), len(bits) - 1)
    frequency = np.where(bits[index] == 1, 2225.0, 2025.0).astype(np.float64)
    tone = kernels.sine(frequency, float(RATE), 0.0)
    return effects.stereo(tone * 0.2)


def wind(seconds: float, seed: int = 0) -> np.ndarray:
    """Noise that a slow filter moves: the solar wind."""
    random = np.random.default_rng(seed)
    total = int(seconds * RATE)
    time = np.arange(total) / RATE
    out = np.zeros((total, 2))
    for channel in range(2):
        noise = random.normal(0.0, 1.0, total)
        knots = random.uniform(0.0, 1.0, int(seconds / 2.5) + 3)
        move = np.interp(time / 2.5, np.arange(len(knots)), knots)
        cutoff = 250.0 * 2.0 ** (4.0 * move)
        out[:, channel] = kernels.state_variable(noise, cutoff, np.full(total, 3.0), float(RATE), 1)
    return out * 0.12


MADE = {"sun", "quindar on", "quindar off", "static", "telemetry", "wind"}


def make(cue: Cue, seconds: float) -> np.ndarray:
    """Return a sound that code makes (two channels)."""
    if cue.sound == "sun":
        return sun(seconds, cue.seed)
    if cue.sound == "quindar on":
        return quindar(True)
    if cue.sound == "quindar off":
        return quindar(False)
    if cue.sound == "static":
        return static(seconds, cue.seed)
    if cue.sound == "telemetry":
        return telemetry(seconds, cue.seed)
    return wind(seconds, cue.seed)


@functools.lru_cache(maxsize=4)
def load(name: str) -> np.ndarray | None:
    """Read a file of the media directory (one or two channels), or return None.

    The result stays in memory: many cues use the same long recording. Do not
    change the returned signal.
    """
    import soundfile

    for suffix in (".flac", ".wav", ".mp3", ".ogg"):
        path = MEDIA_DIR / f"{name}{suffix}"
        if path.exists():
            data, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
            if rate != RATE:
                data = soxr.resample(data, rate, RATE, quality="HQ")
            # A recording with one channel stays so: it needs half of the memory. Some
            # files have the same signal in two channels: one of them is sufficient.
            if data.shape[1] > 1 and np.array_equal(data[:, 0], data[:, 1]):
                data = data[:, :1]
            return np.ascontiguousarray(data[:, :2], dtype=np.float32)
    return None


def radio(sound: np.ndarray) -> np.ndarray:
    """Give a sound the narrow band and the distortion of a radio message."""
    band = signal.butter(3, [320.0, 3300.0], "bandpass", fs=RATE, output="sos")
    out = signal.sosfilt(band, sound.mean(axis=1))
    out = np.tanh(6.0 * out / max(float(np.percentile(np.abs(out), 99.5)), 1e-6)) * 0.3
    return effects.stereo(out) * 1.41


def ring(sound: np.ndarray, notes: tuple[int, ...], mix: float = 0.8) -> np.ndarray:
    """Make a sound ring on some notes: narrow band filters at each note and its octaves.

    The level of the result is the level of the sound that goes in.
    """
    out = np.zeros_like(sound, dtype=np.float64)
    for note in notes:
        for octave in range(4):
            frequency = 440.0 * 2.0 ** ((note + 12 * octave - 69) / 12.0)
            if frequency > 0.4 * RATE:
                break
            width = frequency / 90.0
            band = signal.butter(1, [frequency - width, frequency + width], "bandpass",
                                 fs=RATE, output="sos")  # fmt: skip
            out += signal.sosfilt(band, sound, axis=0) / (1.0 + 0.6 * octave)
    before = float(np.sqrt(np.mean(np.asarray(sound, dtype=np.float64) ** 2))) + 1e-12
    after = float(np.sqrt(np.mean(out**2))) + 1e-12
    return mix * out * (before / after) + (1.0 - mix) * sound


CROSS_SECONDS = 0.02  # two parts of the render change over in this time


def render(work: Work, begin: float, end: float, seconds: float, lead: float) -> np.ndarray | None:
    """Return the stem of the recorded sounds, or None if the work has no cues.

    The full work is rendered in parts (see `render.chunks`). A long sound
    goes through some parts: each part has the piece of the sound that is
    inside its own time, from `begin` to `end`. At the two ends, the piece
    changes over to the piece of the adjacent part in a short time.
    """
    cues: list[Cue] = work.extras.get("cues", [])  # type: ignore[assignment]
    if not cues:
        return None
    structure = work.structure
    out = np.zeros((int(seconds * RATE) + RATE, 2), dtype=np.float32)
    window_first = int(round(lead * RATE))
    window_last = int(round((end - begin + lead) * RATE))
    cross = int(CROSS_SECONDS * RATE)
    missing = set()
    for cue in cues:
        position = structure.bar(cue.bar).start + Fraction(cue.beat) - 1
        start = structure.seconds(position)
        if start >= end:
            continue
        wanted = cue.seconds
        if cue.length is not None:
            wanted = structure.seconds(position + Fraction(cue.length)) - start
        # A sound that ended before this part has nothing here. (A file with no given
        # length is not longer than some minutes.)
        if start + (wanted if wanted is not None else 600.0) <= begin:
            continue
        if cue.sound in MADE:
            sound = make(cue, wanted or 4.0)
        else:
            loaded = load(cue.sound)
            if loaded is None:
                missing.add(cue.sound)
                continue
            sound = loaded[int(cue.offset * RATE) :]
            if wanted is not None:
                sound = sound[: int((wanted * max(cue.speed, 1.0) + 1.0) * RATE)]
            if sound.shape[1] == 1:
                sound = np.repeat(sound, 2, axis=1)
        if cue.speed != 1.0:
            sound = soxr.resample(sound, RATE * cue.speed, RATE, quality="HQ")
        if wanted is not None:
            sound = sound[: int(wanted * RATE)]
        if cue.reverse:
            sound = sound[::-1]
        if cue.radio:
            sound = radio(sound)
        if cue.ring:
            sound = ring(sound, cue.ring, cue.ring_mix)
        sound = sound.astype(np.float64).copy()
        edge = max(8, min(int(cue.fade * RATE), len(sound) // 2))
        sound[:edge] *= np.linspace(0.0, 1.0, edge)[:, None]
        sound[-edge:] *= np.linspace(1.0, 0.0, edge)[:, None]
        if cue.pan:
            sound = sound * np.array([min(1.0, 1.0 - cue.pan), min(1.0, 1.0 + cue.pan)])
        first = int(round((start - begin + lead) * RATE))
        if first + len(sound) <= window_first:
            continue
        piece = np.zeros((len(out), 2))
        skip = max(0, -first)
        place = max(0, first)
        count = min(len(sound) - skip, len(out) - place)
        if count <= 0:
            continue
        piece[place : place + count] = sound[skip : skip + count]
        # The piece of this part: from the start of the part to its end, with a short
        # change-over at each end where the sound goes on in the adjacent part.
        if first < window_first:
            piece[:window_first] = 0.0
            ramp = np.linspace(0.0, 1.0, cross)[:, None]
            piece[window_first : window_first + cross] *= ramp[: len(piece) - window_first]
        if window_last < len(piece):
            stop = min(len(piece), window_last + cross)
            piece[window_last:stop] *= np.linspace(1.0, 0.0, cross)[: stop - window_last, None]
            piece[stop:] = 0.0
        out += (piece * dsp.db(cue.gain_db)).astype(np.float32)
    for name in sorted(missing):
        print(f"tape: the recorded sound {name!r} is not in {MEDIA_DIR}; the cue is silent")
    return out
