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

import os
from collections import OrderedDict
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile
import soxr
from scipy import signal

from . import dsp, nam

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples/metal-gtx/UI_METAL-GTX/Samples")
MODELS_DIR = Path(".cache/models/nam")
CABINETS_DIR = Path(".cache/models/ir")
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
    # The loudspeaker cabinet and its microphone, for a model of an amplifier alone: the
    # name of an impulse response in `CABINETS_DIR`. ("" = the model has its cabinet.)
    cabinet: str = ""


# The tone of the heavy guitar against real recordings (public examples of real
# distorted guitars through loudspeaker cabinets, `tools/diagnose/guitar_lab.py`): the
# third version had 6 dB more level from 4 to 6 kHz and 12 dB more from 6 to 9 kHz than
# a real double-tracked metal guitar ("fizz": a real cabinet has almost no sound
# there), 3 dB more from 250 Hz to 1 kHz, and 7 dB less below 120 Hz (the weight of the
# low string). These filters, and a lower filter before the amplifier, bring the tone
# near the real recordings.
HEAVY_POST = (
    ("low shelf", 110.0, 3.0),
    ("bell", 450.0, -3.0, 1.0),
    ("bell", 4000.0, -7.0, 1.0),
    ("lowpass", 5000.0, 4),
)
CRUNCH_POST = (
    ("low shelf", 110.0, 2.0),
    ("bell", 450.0, -2.0, 1.0),
    ("bell", 4000.0, -6.0, 1.0),
    ("lowpass", 5500.0, 4),
)
LEAD_POST = (
    ("bell", 500.0, 4.0, 0.6),
    ("bell", 3500.0, -8.0, 0.9),
    ("lowpass", 4800.0, 4),
)
RIGS = {
    "high gain": Rig("Phillipe_P_Bugera6262-Lead-NoDrive-Cab-ESR0.009.nam", -8.0, 80.0, 6.0,
                     14.5, HEAVY_POST),
    "crunch": Rig("Phillipe_P_Bug6262-Crunch-NoDrive-Cab-ESR0.004.nam", -8.0, 80.0, 3.0, 8.0,
                  CRUNCH_POST),
    "clean": Rig("Phillipe_P_Bug333-Clean-Cab-ESR0.007.nam", -12.0, 70.0, 0.0, 2.5,
                 (("bell", 3600.0, -4.0, 1.0),)),
    # The lead tone: full in the middle, with no sharp top. The owner: "I really just
    # want a nice full bodied sound from the guitar that shreds in a jazz metal way."
    # The tone control of the guitar is turned down before the amplifier (less
    # distortion of the high partials), and the filters after it cut near 3.5 kHz.
    "lead": Rig("Phillipe_P_JVM-OD2-RD-NoDrive-Cab-ESR0.006.nam", -8.0, 90.0, 4.0, 11.5,
                LEAD_POST, tone_hz=2200.0),
}  # fmt: skip

# A second set of rigs, for a comparison by ear: a Peavey 5150 ("block letter") with a
# boost pedal for the heavy tone and an EVH 5150 III with a Tube Screamer for the crunch
# tone (captures with no cabinet), into the response of a real cabinet: "God's Cab", a
# Mesa cabinet of 4 x 12 inches with a Shure SM57 one inch from the edge of the cone.
# The output levels give each tone the level of the first set from 250 Hz to 6 kHz.
GODS_CAB = "Gods_Cab_1.4/48/SM57/NO-TS/57_1_inch_edge_pres_3.wav"
RIGS_5150 = {
    **RIGS,
    "high gain": Rig("Helga_B_5150_BlockLetter_-_Boosted.nam", -14.0, 80.0, 0.0, 15.3,
                     (("bell", 4000.0, -4.0, 1.0), ("lowpass", 5200.0, 4)), cabinet=GODS_CAB),
    "crunch": Rig("Tim_R_5152_Crunch_+_TS9.nam", -12.0, 80.0, 0.0, -1.1,
                  (("bell", 4000.0, -3.0, 1.0), ("lowpass", 5500.0, 4)), cabinet=GODS_CAB),
}  # fmt: skip
RIG_SETS = {"retuned": RIGS, "5150": RIGS_5150}


def rigs() -> dict[str, Rig]:
    """Return the rigs of the work.

    The environment variable GTYPESTAR_GUITAR selects a set by its name
    ("retuned": the set of the work; "5150": the second set).
    """
    return RIG_SETS[os.environ.get("GTYPESTAR_GUITAR", "retuned")]


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

# The small sounds of a real player, as the program of the library plays them (its SFZ
# files give the numbers). Without them the guitar is a row of clean notes: a machine.
# - Each key has nine recordings, not three: the three takes of its own note, and the
#   takes of the notes one semitone below and above it, at the pitch of the key.
# - The noise of the pick comes a little before the string.
# - When the hand stops a string, the string makes a short sound (a "release"). It is
#   softer after a long note.
# - No two strokes have the same loudness.
NEIGHBOURS = (-1, 0, 1)
PICK_DB = -20.5  # the level of the pick noise against a full stroke
PICK_LEAD = 0.012  # seconds from the pick noise to the note
PICK_FILES = 18
PICK_CUTOFF = 2560.0  # hertz: the pick noise of a full stroke has no sound above this
RELEASE_DB = -16.5  # the level of the release sound against a full stroke
RELEASE_DECAY = {False: 10.0, True: 30.0}  # dB less for each second of an open, a muted note
RELEASE_MUTE_KEY_DB = 1.0  # a muted note: the release is this much softer for each semitone
RELEASE_ZONES = (32, 35, 40, 45, 50, 55, 60, 63, 67, 72, 77, 81, 84, 88)  # recorded pitches
RELEASE_FILES = 8
RELEASE_FLOOR_DB = -55.0  # a release sound under this level is left out
RELEASE_OFF = 0.1  # seconds: the next stroke stops a release sound in this time
LEVEL_RANDOM_DB = 3.0  # each stroke is softer by a random amount up to this


PLAYER = 4  # a change of the code that plays the recordings: a new number here


def signature() -> str:
    """Return a short word that changes with the player and the settings of the rigs.

    It is part of the name of the kept guitar stems: a change of an amplifier,
    a filter or a level makes the kept stems of the guitar invalid, and no
    other stems.
    """
    import hashlib

    text = repr((PLAYER, sorted(rigs().items()), PICK_DB, RELEASE_DB, LEVEL_RANDOM_DB))
    return hashlib.sha1(text.encode()).hexdigest()[:8]  # noqa: S324


def available() -> bool:
    """Return True if the guitar library and all amplifier models are on the computer."""
    return (SAMPLES_DIR / "Sus_Down").exists() and all(
        (MODELS_DIR / rig.model).exists()
        and (not rig.cabinet or (CABINETS_DIR / rig.cabinet).exists())
        for rig in rigs().values()
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


ONSET_LEVEL = dsp.ONSET_LEVEL
ONSET = dsp.ONSET
onset = dsp.onset


class _Bank:
    """The recordings of the library, at the rate of the project, each from its first sound."""

    def __init__(self) -> None:
        self.items: OrderedDict[tuple, np.ndarray] = OrderedDict()
        self.size = 0
        self.leads: dict[tuple, float] = {}

    def get(
        self, kind: str, midi: int, down: bool, take: int, side: int, shift: int = 0
    ) -> tuple[np.ndarray, float]:
        """Return one recording of a note, and the time in seconds from its start to
        its sound (see `onset`). `shift` selects the recording of a note this number of
        semitones away, played at the pitch of `midi`."""
        name = f"{NOTE_NAMES[(midi + shift) % 12]}{(midi + shift) // 12 - 1}"
        stroke = "Down" if down else "Up"
        path = f"{kind}_{stroke}/{name}_{kind}_{stroke}{take}.flac"
        sound = self.file(path, side, semitones=-float(shift))
        key = (path, side, round(-float(shift), 3))
        if key not in self.leads:
            self.leads[key] = onset(sound)
        return sound, self.leads[key]

    def file(self, path: str, side: int, semitones: float = 0.0, trim: bool = True) -> np.ndarray:
        """Return one channel of a file of the library at the rate of the project.

        `semitones` moves the pitch (the length changes with it). With `trim`, the
        recording starts at its first sound.
        """
        key = (path, side, round(semitones, 3), trim)
        if key in self.items:
            self.items.move_to_end(key)
            return self.items[key]
        data, rate = soundfile.read(str(SAMPLES_DIR / path), dtype="float32", always_2d=True)
        # The two channels of a file are two recordings: one for each of the two guitars.
        sound = data[:, side % data.shape[1]]
        # A recording that is played slower is lower.
        target = RATE * 2.0 ** (-semitones / 12.0)
        if abs(rate - target) > 1e-6:
            sound = soxr.resample(sound, rate, target, quality="HQ").astype(np.float32)
        if trim:
            # Each recording starts at its first sound, with one millisecond before it.
            loud = np.flatnonzero(np.abs(sound) > 0.02 * float(np.max(np.abs(sound))))
            first = max(0, int(loud[0]) - RATE // 1000) if len(loud) else 0
            sound = sound[first:]
        sound = np.ascontiguousarray(sound)
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


def _muted(stroke: Stroke) -> bool:
    """Return True if the note has a recording with the palm of the hand on the strings."""
    midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
    return (stroke.mute or stroke.dead) and midi <= HIGHEST_MUTE


def _one(
    stroke: Stroke, down: bool, take: int, side: int, shift: int = 0
) -> tuple[np.ndarray, float]:
    """Return the direct signal of one note, and the time from its start to its sound.

    The player puts the note earlier by that time: then the note sounds at
    its written time. (Before the fourth version of this player, each note
    was late by 15 to 26 milliseconds.)
    """
    midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
    kind = "Mute" if _muted(stroke) else "Sus"
    sound, lead = BANK.get(kind, midi, down, take, side, shift)
    length = int(min(max(stroke.seconds, 0.03), LONGEST) * RATE)
    if stroke.dead:
        length = min(length, int(0.07 * RATE))
    begin = 0
    level = 1.0
    if stroke.hammer and kind == "Sus" and len(sound) > int((LEGATO_START + 0.3) * RATE):
        begin = int(LEGATO_START * RATE)
        lead = 0.0  # the note starts inside the recording: its sound is there at once
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
    return piece * np.float32(_gain(stroke) * level), lead


def _gain(stroke: Stroke) -> float:
    """Return the gain of a stroke: a soft stroke is 14 dB under a hard stroke.

    (The library has one loudness for each note.)
    """
    return 10.0 ** ((float(np.clip(stroke.level, 0.0, 1.0)) - 1.0) * 14.0 / 20.0)


def _pick_noise(level: float, number: int, side: int) -> np.ndarray:
    """Return the noise of the pick for one stroke: a short dull click."""
    sound = BANK.file(f"Noise/Picking_Noise/Picking_Noise{number}_Stereo.flac", side, trim=False)
    # A soft stroke has a duller noise (two octaves lower for half of the loudness).
    cutoff = PICK_CUTOFF * 4.0 ** (float(np.clip(level, 0.0, 1.0)) - 1.0)
    sos = signal.butter(2, cutoff, "lowpass", fs=RATE, output="sos")
    return (signal.sosfilt(sos, sound) * dsp.db(PICK_DB)).astype(np.float32)


def _release(stroke: Stroke, number: int, side: int) -> np.ndarray | None:
    """Return the sound of the hand that stops the string of a note, or None.

    The sound is softer after a long note: the string has less energy then.
    """
    midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
    muted = _muted(stroke)
    level_db = RELEASE_DB - RELEASE_DECAY[muted] * stroke.seconds
    if muted:
        level_db -= RELEASE_MUTE_KEY_DB * (midi - LOWEST)
    if level_db < RELEASE_FLOOR_DB:
        return None
    zone = min(RELEASE_ZONES, key=lambda pitch: abs(pitch - midi))
    name = f"{NOTE_NAMES[zone % 12]}{zone // 12 - 1}"
    sound = BANK.file(f"Release1/{name}_Rel1_{number}.flac", side, semitones=float(midi - zone))
    return sound * np.float32(dsp.db(level_db))


def chords_of(ordered: list[Stroke]) -> list[list[Stroke]]:
    """Return notes in groups. The notes in sequence of time that start at the same
    moment are one group: one stroke of the pick (a chord)."""
    groups: list[list[Stroke]] = []
    for stroke in ordered:
        if groups and abs(stroke.start - groups[-1][0].start) < 0.012:
            groups[-1].append(stroke)
        else:
            groups.append([stroke])
    return groups


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
    chords = chords_of(ordered)
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
    # A note of a line that goes on into the next note has no release sound.
    joined = set()
    for index in range(len(chords) - 1):
        now, later = chords[index], chords[index + 1]
        line = len(now) == 1 and len(later) == 1 and not now[0].mute and not now[0].dead
        if line and later[0].start - (now[0].start + now[0].seconds) < JOIN:
            joined.add(index)

    def add(piece: np.ndarray, start: float) -> None:
        first = int(round(start * RATE))
        if first < 0:
            piece, first = piece[-first:], 0
        count = min(len(piece), len(out) - first)
        if count > 0:
            out[first : first + count] += piece[:count]

    last_used: dict[tuple[int, bool], list[tuple[int, int]]] = {}
    previous_start = -10.0
    down = False
    for index, chord in enumerate(chords):
        down = not down if chord[0].start - previous_start < FAST else True
        previous_start = chord[0].start
        # A down stroke goes from the lowest string to the highest, an up stroke back.
        strings = chord if down else chord[::-1]
        picked = not all(stroke.hammer for stroke in chord)
        for place, stroke in enumerate(strings):
            midi = int(np.clip(round(stroke.midi), LOWEST, HIGHEST))
            muted = _muted(stroke)
            top = HIGHEST_MUTE if muted else HIGHEST
            choices = [(shift, take) for shift in NEIGHBOURS if LOWEST <= midi + shift <= top
                       for take in range(1, TAKES + 1)]  # fmt: skip
            used = last_used.setdefault((midi, muted), [])
            fresh = [choice for choice in choices if choice not in used] or choices
            shift, take = fresh[int(random.integers(len(fresh)))]
            used.append((shift, take))
            del used[:-4]  # a recording does not come back within the next four strokes
            softer = dsp.db(-LEVEL_RANDOM_DB * float(random.uniform()))
            piece, lead = _one(stroke, down, take, side, shift)
            add(piece * np.float32(softer), stroke.start + place * STRUM - lead)
            if picked and place == 0:
                # One stroke of the pick: its noise, a little before the first recording.
                loudest = max(item.level for item in chord)
                noise = _pick_noise(loudest, int(random.integers(1, PICK_FILES + 1)), side)
                add(noise * np.float32(_gain(replace(chord[0], level=loudest))),
                    stroke.start - lead - PICK_LEAD)  # fmt: skip
            if index not in joined and not stroke.dead:
                sound = _release(stroke, int(random.integers(1, RELEASE_FILES + 1)), side)
                if sound is not None:
                    begin = stroke.start + stroke.seconds - CUT
                    # The next stroke stops the release sound: the hand is on the strings
                    # again. (In a fast row of muted notes, the release sounds would
                    # add up to a noise that never stops.)
                    if index + 1 < len(chords):
                        left = chords[index + 1][0].start - begin + RELEASE_OFF
                        size = int(max(left, 0.0) * RATE)
                        if size < len(sound):
                            fade = min(size, int(RELEASE_OFF * RATE))
                            sound = sound[:size].copy()
                            if fade:
                                sound[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
                    add(sound * np.float32(_gain(stroke) * softer), begin)
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


CABINET_SECONDS = 0.2  # the part of an impulse response that the code uses


@lru_cache(maxsize=16)
def cabinet(name: str) -> np.ndarray:
    """Return the impulse response of a loudspeaker cabinet, at the rate of the project.

    The response starts at its first sound. Its level is set so that the
    band from 300 Hz to 3 kHz goes through with no change of the level: a
    change of the cabinet changes the tone, not the loudness.
    """
    data, rate = soundfile.read(str(CABINETS_DIR / name), dtype="float32", always_2d=True)
    sound = data[:, 0].astype(np.float64)
    if rate != RATE:
        sound = soxr.resample(sound, rate, RATE, quality="HQ")
    loud = np.flatnonzero(np.abs(sound) > 1e-3 * float(np.max(np.abs(sound))))
    sound = sound[int(loud[0]) : int(loud[0]) + int(CABINET_SECONDS * RATE)].copy()
    fade = min(len(sound), RATE // 100)
    sound[-fade:] *= np.linspace(1.0, 0.0, fade)
    spectrum = np.abs(np.fft.rfft(sound, 1 << 15)) ** 2
    frequencies = np.fft.rfftfreq(1 << 15, 1.0 / RATE)
    middle = float(np.mean(spectrum[(frequencies >= 300.0) & (frequencies <= 3000.0)]))
    return (sound / np.sqrt(max(middle, 1e-20))).astype(np.float32)


def amplify(dry: np.ndarray, tone: str) -> np.ndarray:
    """Send the direct signal through the amplifier of a tone. Return one channel."""
    rig = rigs()[tone]
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
    if rig.cabinet:
        wet = signal.fftconvolve(wet, cabinet(rig.cabinet))[: len(wet)].astype(np.float32)
    if rig.post:
        from .console import filters as rows

        wet = signal.sosfilt(np.vstack(rows(rig.post)), wet.astype(np.float64))
    return (wet * dsp.db(rig.output_db)).astype(np.float32)
