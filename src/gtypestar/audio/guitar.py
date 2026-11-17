"""The guitar: recordings of a real guitar, through models of real amplifiers.

The first versions of the work had a guitar that code made: a model of a
plucked string and a simple model of an amplifier. The owner of the project
heard it and said: "the guitar is really bad. Look for samples or VST or
something." This module is the answer. It has two parts:

1. The direct signal of the pickup of a real guitar, note by note. The
   library METAL-GTX (Unreal Instruments) has each note from F-sharp 1 (the
   lowest string of a guitar with eight strings) to E6: open notes and notes
   with the palm of the hand on the strings, each with a down stroke and an
   up stroke of the pick, each in three takes, and each take two times (the
   left and the right channel of a file are two different recordings). Thus
   the two rhythm guitars, left and right, are two real performances.
2. Models of real amplifiers with their loudspeaker cabinets, from the
   Neural Amp Modeler project (see `nam.py`).

If the library or the models are not on the computer, the string model of
`amp.py` plays (see `band.render_guitar`).

Credits: METAL-GTX by Unreal Instruments ("License free", from its manual).
Amplifier models: the collection https://github.com/pelennor2170/NAM_models
(GPL 3.0), captures by Phillipe P.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import soundfile
import soxr
from scipy import signal

from . import dsp, nam

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples/metal-gtx/UI_METAL-GTX/Samples")
MODELS_DIR = Path(".cache/models/nam")
LOWEST, HIGHEST = 30, 88  # F-sharp 1 to E6
HIGHEST_MUTE = 76
NOTE_NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
TAKES = 3
CACHE_BYTES = 400_000_000
LONGEST = 7.0  # seconds: the length of the longest recording


# The amplifier of each tone of the guitar: the model file, the level of the guitar
# signal at the input (dB), a filter before the amplifier (low cut in hertz, and a boost
# of the middle in dB: an overdrive pedal in front of the amplifier makes a heavy sound
# tight), the output level (dB), and the filters of the mix engineer after the
# microphone, as rows for `console.filters`.
@dataclass(frozen=True)
class Rig:
    model: str
    input_db: float
    low_cut: float
    push_db: float
    output_db: float
    post: tuple[tuple, ...] = ()
    tone_hz: float = 0.0  # the tone control of the guitar: a low-pass filter before the amplifier


# The captured cabinet has much level near 130 Hz and from 3 to 5 kHz, and less in the
# middle. Against the stem "other" of the reference tracks, a heavy riff had 7 dB too
# much from 90 to 180 Hz and from 2.8 to 5.6 kHz, and 4 to 6 dB too little from 355 Hz
# to 1.4 kHz. These filters bring the middle forward.
HEAVY_POST = (
    ("bell", 130.0, -6.0, 1.0),
    ("bell", 800.0, 5.0, 0.6),
    ("bell", 4000.0, -6.0, 1.0),
    ("high shelf", 6000.0, -2.0),
)
LEAD_POST = (
    ("bell", 500.0, 4.0, 0.6),
    ("bell", 3500.0, -8.0, 0.9),
    ("lowpass", 4800.0, 4),
)
RIGS = {
    "high gain": Rig("Phillipe_P_Bugera6262-Lead-NoDrive-Cab-ESR0.009.nam", -8.0, 110.0, 6.0,
                     9.5, HEAVY_POST),
    "crunch": Rig("Phillipe_P_Bug6262-Crunch-NoDrive-Cab-ESR0.004.nam", -8.0, 90.0, 3.0, 4.6,
                  HEAVY_POST),
    "clean": Rig("Phillipe_P_Bug333-Clean-Cab-ESR0.007.nam", -12.0, 70.0, 0.0, 2.5,
                 (("bell", 3600.0, -4.0, 1.0),)),
    # The lead tone: full in the middle, with no sharp top. The owner: "I really just
    # want a nice full bodied sound from the guitar that shreds in a jazz metal way."
    # The tone control of the guitar is turned down before the amplifier (less
    # distortion of the high partials), and the filters after it cut near 3.5 kHz.
    "lead": Rig("Phillipe_P_JVM-OD2-RD-NoDrive-Cab-ESR0.006.nam", -8.0, 90.0, 4.0, 11.5,
                LEAD_POST, tone_hz=2200.0),
}  # fmt: skip

FAST = 0.22  # seconds: notes that follow faster than this get up and down strokes in turn
STRUM = 0.006  # seconds between the strings of a chord
CUT = 0.02  # seconds: the end of a note that the hand stops
# A note that the left hand starts (hammer-on, pull-off) has no stroke of the pick. As in
# the hammer-on patch of the library, it starts inside the recording, where the string
# rings with no sound of the pick, and its pitch comes from the note before it.
LEGATO_START = 0.55  # seconds into the recording
LEGATO_RISE = 0.007
LEGATO_GLIDE = 0.03
LEGATO_LEVEL = 0.85  # the level of such a note against a note with a stroke
OVERLAP = 0.012  # seconds: a note of a line rings on into the start of the next note
JOIN = 0.05  # seconds: a gap shorter than this between two notes of a line is closed


def available() -> bool:
    """Return True if the guitar library and all amplifier models are on the computer."""
    return (SAMPLES_DIR / "Sus_Down").exists() and all(
        (MODELS_DIR / rig.model).exists() for rig in RIGS.values()
    )


@dataclass(frozen=True)
class Stroke:
    """One note of the guitar."""

    start: float
    seconds: float
    midi: float
    level: float
    mute: bool = False  # the palm of the hand is on the strings
    hammer: bool = False  # the left hand starts the note: no stroke of the pick
    dead: bool = False  # a note with no pitch
    slide_from: float | None = None  # the pitch at the start, if the player slides to the note
    bend: tuple[float, ...] = ()  # pitch curve in semitones for the time of the note
    vibrato: float = 0.0  # depth in cents


class _Bank:
    """The recordings of the library, at the rate of the project, each from its first sound."""

    def __init__(self) -> None:
        self.items: OrderedDict[tuple, np.ndarray] = OrderedDict()
        self.size = 0

    def get(self, kind: str, midi: int, down: bool, take: int, side: int) -> np.ndarray:
        key = (kind, midi, down, take, side)
        if key in self.items:
            self.items.move_to_end(key)
            return self.items[key]
        name = f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"
        stroke = "Down" if down else "Up"
        path = SAMPLES_DIR / f"{kind}_{stroke}" / f"{name}_{kind}_{stroke}{take}.flac"
        data, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
        # The two channels of a file are two recordings: one for each of the two guitars.
        sound = data[:, side % data.shape[1]]
        if rate != RATE:
            sound = soxr.resample(sound, rate, RATE, quality="HQ").astype(np.float32)
        # Each recording starts at its first sound, with one millisecond before it.
        loud = np.flatnonzero(np.abs(sound) > 0.02 * float(np.max(np.abs(sound))))
        first = max(0, int(loud[0]) - RATE // 1000) if len(loud) else 0
        sound = np.ascontiguousarray(sound[first:])
        self.items[key] = sound
        self.size += sound.nbytes
        while self.size > CACHE_BYTES and len(self.items) > 1:
            _old, removed = self.items.popitem(last=False)
            self.size -= removed.nbytes
        return sound


BANK = _Bank()


def _bent(sound: np.ndarray, cents: np.ndarray) -> np.ndarray:
    """Play a recording with a pitch that changes: `cents` gives the change for each sample."""
    speed = 2.0 ** (cents / 1200.0)
    position = np.concatenate([[0.0], np.cumsum(speed)[:-1]])
    position = position[position < len(sound) - 1]
    return np.interp(position, np.arange(len(sound)), sound).astype(np.float32)


def _one(stroke: Stroke, down: bool, take: int, side: int) -> np.ndarray:
    """Return the direct signal of one note."""
    midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
    kind = "Mute" if (stroke.mute or stroke.dead) and midi <= HIGHEST_MUTE else "Sus"
    sound = BANK.get(kind, midi, down, take, side)
    length = int(min(max(stroke.seconds, 0.03), LONGEST) * RATE)
    if stroke.dead:
        length = min(length, int(0.07 * RATE))
    begin = 0
    level = 1.0
    if stroke.hammer and kind == "Sus" and len(sound) > int((LEGATO_START + 0.3) * RATE):
        begin = int(LEGATO_START * RATE)
        # The string is softer there than at its start: bring it to the level of a stroke.
        window = RATE // 10
        early = float(np.sqrt(np.mean(sound[RATE // 30 : RATE // 30 + window] ** 2)))
        late = float(np.sqrt(np.mean(sound[begin : begin + window] ** 2)))
        level = LEGATO_LEVEL * min(6.0, early / max(late, 1e-6))
    piece = sound[begin : begin + length + RATE // 4].copy()
    # The pitch: a slide into the note, a bend, a vibrato, and the part of a semitone.
    cents = np.full(len(piece), 100.0 * (stroke.midi - midi))
    time = np.arange(len(piece)) / RATE
    if stroke.slide_from is not None:
        glide = LEGATO_GLIDE if stroke.hammer else 0.07
        cents += 100.0 * (stroke.slide_from - stroke.midi) * np.clip(1.0 - time / glide, 0.0, 1.0)
    if stroke.bend:
        knots = np.linspace(0.0, max(stroke.seconds, 0.05), len(stroke.bend))
        cents += 100.0 * np.interp(time, knots, stroke.bend)
    if stroke.vibrato:
        depth = stroke.vibrato * np.clip((time - 0.22) / 0.3, 0.0, 1.0)
        cents += depth * np.sin(2.0 * np.pi * 5.6 * time)
    if np.any(np.abs(cents) > 0.5):
        piece = _bent(piece, cents)
    piece = piece[:length]
    if stroke.hammer:
        rise = min(len(piece), int(LEGATO_RISE * RATE))
        piece[:rise] *= np.linspace(0.0, 1.0, rise, dtype=np.float32)
    fade = min(len(piece), int(CUT * RATE))
    piece[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
    # A soft stroke is 14 dB under a hard stroke. (The library has one loudness.)
    gain = 10.0 ** ((float(np.clip(stroke.level, 0.0, 1.0)) - 1.0) * 14.0 / 20.0)
    return piece * np.float32(gain * level)


def direct(strokes: list[Stroke], seconds: float, side: int, seed: int = 0) -> np.ndarray:
    """Return the direct signal of the pickup for all notes of one performance.

    `side` selects one of the two recordings of each note (0 or 1). Fast
    notes get down strokes and up strokes in turn. A note does not get the
    same take two times one after the other. The notes of a chord start a
    little one after the other, from the lowest string.
    """
    random = np.random.default_rng((seed, side))
    out = np.zeros(int(seconds * RATE) + RATE // 2, dtype=np.float32)
    ordered = sorted(strokes, key=lambda item: (round(item.start, 3), item.midi))
    # The notes that start at the same moment are one stroke of the pick (a chord).
    chords: list[list[Stroke]] = []
    for stroke in ordered:
        if chords and abs(stroke.start - chords[-1][0].start) < 0.012:
            chords[-1].append(stroke)
        else:
            chords.append([stroke])
    # A line of single notes: a note rings to the start of the next note (no gap between
    # the notes of a line), and a note that the left hand starts gets its pitch from the
    # note before it.
    for index in range(len(chords) - 1):
        now, later = chords[index], chords[index + 1]
        if len(now) != 1 or len(later) != 1 or now[0].mute or now[0].dead:
            continue
        gap = later[0].start - (now[0].start + now[0].seconds)
        if later[0].hammer or gap < JOIN:
            now[0] = replace(now[0], seconds=later[0].start - now[0].start + OVERLAP)
        if later[0].hammer and later[0].slide_from is None:
            step = float(np.clip(now[0].midi - later[0].midi, -3.0, 3.0))
            later[0] = replace(later[0], slide_from=later[0].midi + step)
    last_take: dict[tuple[int, bool], int] = {}
    previous_start = -10.0
    down = False
    for chord in chords:
        down = not down if chord[0].start - previous_start < FAST else True
        previous_start = chord[0].start
        # A down stroke goes from the lowest string to the highest, an up stroke back.
        strings = chord if down else chord[::-1]
        for place, stroke in enumerate(strings):
            midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
            take = int(random.integers(1, TAKES + 1))
            if take == last_take.get((midi, stroke.mute)):
                take = take % TAKES + 1
            last_take[(midi, stroke.mute)] = take
            piece = _one(stroke, down, take, side)
            first = int(round((stroke.start + place * STRUM) * RATE))
            if first < 0 or first >= len(out):
                continue
            count = min(len(piece), len(out) - first)
            out[first : first + count] += piece[:count]
    return out


PAUSE_SECONDS = 0.5  # the amplifier model does not run in a silence that is longer
RING_SECONDS = 0.15  # the time of the amplifier sound after the last sample of a note


def _playing(dry: np.ndarray) -> list[tuple[int, int]]:
    """Return the parts of the direct signal that are not silent: (first, last) samples."""
    loud = np.flatnonzero(np.abs(dry) > 1e-6)
    if len(loud) == 0:
        return []
    breaks = np.flatnonzero(np.diff(loud) > int(PAUSE_SECONDS * RATE))
    firsts = [int(loud[0]), *(int(loud[index + 1]) for index in breaks)]
    lasts = [*(int(loud[index]) for index in breaks), int(loud[-1])]
    ring = int(RING_SECONDS * RATE)
    return [
        (max(0, first - 256), min(len(dry), last + ring))
        for first, last in zip(firsts, lasts, strict=True)
    ]


def amplify(dry: np.ndarray, tone: str) -> np.ndarray:
    """Send the direct signal through the amplifier of a tone. Return one channel."""
    rig = RIGS[tone]
    filters = [dsp.highpass(rig.low_cut, 2)]
    if rig.push_db:
        filters.append(dsp.peaking(800.0, rig.push_db, 0.7))
    if rig.tone_hz:
        filters.append(dsp.lowpass(rig.tone_hz, 2))
    shaped = signal.sosfilt(np.vstack(filters), dry.astype(np.float64)) * dsp.db(rig.input_db)
    shaped = shaped.astype(np.float32)
    # The model of the amplifier needs much time. It runs only where the guitar plays:
    # in a long excerpt, a tone often has notes in some bars only.
    model = nam.load(str(MODELS_DIR / rig.model))
    wet = np.zeros(len(shaped), dtype=np.float32)
    edge = int(0.005 * RATE)
    for first, last in _playing(dry):
        part = model.play(shaped[first:last])
        size = min(edge, len(part) // 2)
        ramp = np.linspace(0.0, 1.0, size, dtype=np.float32)
        part[:size] *= ramp
        part[len(part) - size :] *= ramp[::-1]
        wet[first:last] = part
    if rig.post:
        from .console import filters as rows

        wet = signal.sosfilt(np.vstack(rows(rig.post)), wet.astype(np.float64))
    return (wet * dsp.db(rig.output_db)).astype(np.float32)
