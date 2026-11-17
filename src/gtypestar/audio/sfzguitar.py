"""The guitar library, played by the program of its makers in a sampler.

The library METAL-GTX is more than its recordings. Its makers wrote a
program for it (a text in the format SFZ, 14 000 regions): which recording
plays for which key, how hard, how bright, with which small sounds around
it. The player of `guitar.py` reads the recordings and copies a part of that
program by hand. This module plays the program itself, with the sampler
sfizz (the package `pysfizz`). The owner of the project heard the guitar of
the third version, said "This one sounds bad", and then: "Install pysfizz".

What the program does, and the player of `guitar.py` does not:

- A real down stroke and a real up stroke for each note, with or without
  the palm of the hand on the strings, and real notes with no pitch (the
  left hand stops the string).
- Each recording starts before the pick leaves the string: the sound of the
  pick on the string is there. (`guitar.py` cuts each recording at its
  first loud sample.)
- A soft stroke is duller, not only softer.
- Notes that the left hand starts (hammer-on, pull-off) with the settings of
  the makers, and recorded slides into a note.
- A sound when a note stops, for each way of playing, and the next stroke
  stops it. The noise of the pick, and a soft sound of the other strings.
- A vibrato that only goes up from the note, as a finger on a string does.

The sampler gets the notes as MIDI messages: `messages` writes them from
the same `guitar.Stroke` list that `guitar.direct` gets. The result of
`direct` here has the same form: the signal of the pickup, for the
amplifier models of `guitar.py`.

A note of the program does not sound at the moment of its key: the
recording has the time of the pick on the string first (30 to 45
milliseconds). Each key goes to the sampler earlier by that time, from a
table that `latency` measures one time (some minutes) and keeps.

The sampler has its own random numbers (the loudness of each stroke, the
start of a small sound): two renders of the same notes are not equal
sample for sample.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import dsp, guitar
from .guitar import Stroke

RATE = dsp.RATE
PROGRAM = guitar.SAMPLES_DIR.parent / "Programs" / "01-METAL-GTX Full.sfz"
BLOCK = 256  # samples: the sampler makes the sound in blocks of this size
VOICES = 256  # the largest number of recordings that sound at the same time

# The keys of the program that select the way of playing (its "key switches").
DEAD_DOWN, DEAD_UP = 14, 15  # the left hand stops the string: a note with no pitch
SUS_DOWN, SUS_UP = 17, 18  # an open note
MUTE_DOWN, MUTE_UP = 20, 21  # the palm of the hand is on the strings
PULL_OFF, HAMMER_ON = 25, 26  # the left hand starts the note
SLIDE_IN = 27  # the finger slides up into the note
# The lowest and the highest key with a sound, for each way of playing.
RANGES = {
    DEAD_DOWN: (31, 88),
    DEAD_UP: (31, 88),
    SUS_DOWN: (30, 88),
    SUS_UP: (30, 88),
    MUTE_DOWN: (30, 76),
    MUTE_UP: (30, 76),
    PULL_OFF: (30, 87),
    HAMMER_ON: (31, 88),
    SLIDE_IN: (32, 88),
}
UP = {SUS_DOWN: SUS_UP, MUTE_DOWN: MUTE_UP, DEAD_DOWN: DEAD_UP}

# The controllers of the program (the numbers are from its manual).
VIBRATO_DEPTH, VIBRATO_SPEED = 20, 21
RELEASE_SHAPE, RELEASE_LEVEL = 24, 25
SLIDE_IN_INTERVAL = 27
MAGNET = 48
# The values of the controllers for the work. All other controllers have the values
# of the program.
# - Magnet: a tone filter that makes the pickup sound like an active pickup. The
#   manual: set it to 0 if the tone comes from your own amplifier.
# - Vibrato speed: 118 is 5.6 cycles in a second.
SETTINGS = {MAGNET: 0, VIBRATO_SPEED: 118}

FULL = 0.83  # the loudness (fortissimo) from which a stroke has the full velocity
SOFT_DB = 14.0  # a stroke with the loudness 0 is this much softer than a full stroke
DIRECT_DB = 9.5  # the level of the sampler signal at the input of the amplifier
FAST = 0.22  # seconds: notes that follow faster than this get up and down strokes in turn
STRUM = 0.006  # seconds between the strings of a chord
JOIN = 0.05  # seconds: a note that ends this near to the next stroke goes on to it
VIBRATO_START, VIBRATO_RISE = 0.22, 0.3  # seconds into a note
STEP = 0.005  # seconds between two values of a controller that changes
BEND_RANGE = 2.0  # semitones: the range of the pitch wheel in the program

# The measurement of the time from a key to its sound.
REPEATS = 9  # the program has nine recordings for a key
SPACING, HOLD = 0.25, 0.15  # seconds from a note to the next, and the length of a note
WINDOW = 0.12  # seconds: the part of a note that has its start
THRESHOLD = 0.25  # the note "sounds" when its level is this part of its largest level
SETTLE = 0.3  # seconds of sound that the sampler makes and the code drops, between renders


@dataclass(frozen=True)
class Message:
    """One MIDI message for the sampler."""

    sample: int  # the moment, in samples from the start
    order: int  # the sequence of messages at the same moment
    kind: str  # "note_on", "note_off", "cc" or "pitch_wheel"
    first: int  # the key, the controller, or the value of the pitch wheel
    second: int = 0  # the velocity, or the value of the controller


def _module():
    """Return the module of the sampler, or None if it is not on the computer."""
    try:
        from pysfizz import _sfizz
    except ImportError:
        return None
    return _sfizz


def available() -> bool:
    """Return True if the sampler and the program of the library are on the computer."""
    return PROGRAM.exists() and _module() is not None


def selected() -> bool:
    """Return True if the sampler plays the guitar of the work.

    The environment variable GTYPESTAR_PLAYER selects the player: "program"
    (this module, if the sampler is on the computer) or "plain" (the player
    of `guitar.py`).
    """
    return os.environ.get("GTYPESTAR_PLAYER", "program") == "program" and available()


PLAYER = 1  # a change of the code that writes the messages: a new number here


def signature() -> str:
    """Return a short word for the name of the kept guitar stems.

    It is empty if the sampler does not play. If not, it changes with the
    settings of this module: then the kept stems of the guitar are invalid.
    """
    if not selected():
        return ""
    text = repr((PLAYER, sorted(SETTINGS.items()), FULL, SOFT_DB, DIRECT_DB, FAST, STRUM, JOIN))
    return "-program-" + hashlib.sha1(text.encode()).hexdigest()[:6]  # noqa: S324


def _new():
    """Return a new sampler with the program of the library."""
    sampler = _module().Synth(RATE, BLOCK)
    # With "freewheeling", the sampler waits for each recording from the disk. Without
    # it, a render faster than the clock loses the starts of notes.
    sampler.enable_freewheeling()
    sampler.set_num_voices(VOICES)
    if not sampler.load_sfz_file(str(PROGRAM)):
        raise RuntimeError(f"the sampler cannot read {PROGRAM}")
    return sampler


_SAMPLER: tuple[int, object] | None = None


def _sampler():
    """Return the sampler of this process.

    A sampler has threads of its own. A process that starts as a copy of
    another process (a worker of the full render) does not get them: each
    process makes its own sampler.
    """
    global _SAMPLER
    if _SAMPLER is None or _SAMPLER[0] != os.getpid():
        _SAMPLER = (os.getpid(), _new())
    return _SAMPLER[1]


def play(sampler, messages: list[Message], seconds: float) -> np.ndarray:
    """Send messages to a sampler. Return its sound: two channels, `seconds` long.

    The two channels are two recordings of each note (two guitars).
    """
    for number, value in SETTINGS.items():
        sampler.cc(0, number, value)
    total = int(seconds * RATE)
    out = np.zeros((total + BLOCK, 2), dtype=np.float32)
    ordered = sorted(messages, key=lambda item: (item.sample, item.order))
    index = 0
    for position in range(0, total, BLOCK):
        while index < len(ordered) and ordered[index].sample < position + BLOCK:
            message = ordered[index]
            delay = max(0, message.sample - position)
            if message.kind == "pitch_wheel":
                sampler.pitch_wheel(delay, message.first)
            else:
                getattr(sampler, message.kind)(delay, message.first, message.second)
            index += 1
        left, right = sampler.render_block()
        out[position : position + BLOCK, 0] = left
        out[position : position + BLOCK, 1] = right
    return out[:total]


def _quiet(sampler) -> None:
    """Stop all sounds of a sampler, and bring its controllers back."""
    sampler.all_sound_off()
    sampler.cc(0, VIBRATO_DEPTH, 0)
    sampler.pitch_wheel(0, 0)
    for _ in range(int(SETTLE * RATE) // BLOCK):
        sampler.render_block()


def velocity(level: float) -> int:
    """Return the MIDI velocity of a stroke with a loudness from 0 to 1.

    The program plays a full stroke at the velocity 127 (the examples of its
    makers have 127 for almost all notes, and 96 for softer strokes). A
    softer stroke is softer and duller.
    """
    drop = SOFT_DB * max(0.0, FULL - float(level))
    return int(np.clip(round(127.0 * 10.0 ** (-drop / 40.0)), 1, 127))


# ----------------------------------------------------------------------------
# The time from a key to its sound
# ----------------------------------------------------------------------------


def _signature() -> str:
    """Return a short word that changes with the program and the measurement."""
    state = PROGRAM.stat()
    text = repr((state.st_size, int(state.st_mtime), RATE, REPEATS, THRESHOLD, sorted(RANGES)))
    return hashlib.sha1(text.encode()).hexdigest()[:10]  # noqa: S324


def _table_path() -> Path:
    return PROGRAM.parent.parent / f"latency-{_signature()}.json"


def onset(sound: np.ndarray) -> float:
    """Return the time in seconds at which a note "sounds".

    It is the first moment at which the level is `THRESHOLD` of the largest
    level of the first part of the note. (The noise of the pick before the
    note is under this level.)
    """
    level = np.convolve(np.abs(sound), np.ones(24) / 24.0, mode="same")
    top = float(np.max(level[: int(WINDOW * RATE)]))
    if top <= 0.0:
        return 0.0
    return float(np.flatnonzero(level >= THRESHOLD * top)[0]) / RATE


def _measure(switch: int) -> np.ndarray:
    """Return the time from a key to its sound for one way of playing.

    The result has one row for each of the two channels and one number for
    each key: the mean of `REPEATS` strokes.
    """
    low, high = RANGES[switch]
    sampler = _new()
    messages = [Message(0, 0, "note_on", switch, 100), Message(1, 1, "note_off", switch)]
    starts = []
    for key in range(low, high + 1):
        for _ in range(REPEATS):
            start = int((0.05 + SPACING * len(starts)) * RATE)
            starts.append(start)
            messages.append(Message(start, 2, "note_on", key, 127))
            messages.append(Message(start + int(HOLD * RATE), 3, "note_off", key))
    sound = play(sampler, messages, 0.05 + SPACING * len(starts) + 0.2)
    table = np.zeros((2, 128))
    size = int((SPACING - 0.01) * RATE)
    for side in range(2):
        times = [onset(sound[start : start + size, side]) for start in starts]
        means = np.array(times).reshape(-1, REPEATS).mean(axis=1)
        table[side, low : high + 1] = means
        table[side, :low], table[side, high + 1 :] = means[0], means[-1]
    return table


def latency() -> dict[tuple[int, int], np.ndarray]:
    """Return the time in seconds from each key to its sound.

    The keys of the result are (way of playing, channel); each value has one
    number for each MIDI key. The first call measures the program (some
    minutes) and writes the table next to the library.
    """
    global _LATENCY
    if _LATENCY is None:
        path = _table_path()
        if path.exists():
            rows = json.loads(path.read_text(encoding="utf-8"))
        else:
            rows = {}
            for switch in RANGES:
                table = _measure(switch)
                for side in range(2):
                    rows[f"{switch} {side}"] = [round(float(value), 5) for value in table[side]]
            part = path.with_suffix(f".{os.getpid()}.part")
            part.write_text(json.dumps(rows), encoding="utf-8")
            part.replace(path)
        _LATENCY = {
            (int(name.split()[0]), int(name.split()[1])): np.array(values)
            for name, values in rows.items()
        }
    return _LATENCY


_LATENCY: dict[tuple[int, int], np.ndarray] | None = None


# ----------------------------------------------------------------------------
# From the notes to the messages
# ----------------------------------------------------------------------------


@dataclass
class _Note:
    """One note for the sampler: the key, its way of playing, and its times in seconds."""

    key: int
    switch: int
    velocity: int
    send: float  # the moment of the message "note on"
    start: float  # the moment at which the note sounds
    end: float  # the moment of the message "note off"
    chord: int  # the number of the stroke of the pick
    slide: int = 0  # semitones of a slide into the note


def _switch(stroke: Stroke, down: bool, before: Stroke | None) -> int:
    """Return the way of playing of a stroke, as a key switch of the program."""
    key = int(round(stroke.midi))
    if stroke.dead:
        kind = DEAD_DOWN
    elif stroke.mute and key <= RANGES[MUTE_DOWN][1]:
        kind = MUTE_DOWN
    elif stroke.hammer:
        # The left hand starts the note: a finger falls on the string (the pitch goes
        # up), or a finger leaves it (the pitch goes down).
        return PULL_OFF if before is not None and before.midi > stroke.midi else HAMMER_ON
    elif stroke.slide_from is not None and 0.5 <= stroke.midi - stroke.slide_from <= 7.5:
        return SLIDE_IN
    else:
        kind = SUS_DOWN
    return kind if down else UP[kind]


def notes(
    strokes: list[Stroke], side: int, table: dict[tuple[int, int], np.ndarray]
) -> list[_Note]:
    """Return the notes for the sampler, with the moments of their messages.

    Fast notes get down strokes and up strokes in turn. The strings of a
    chord start a little one after the other. Each key goes to the sampler
    earlier by the time from that key to its sound (`table`). A note that
    ends near the next stroke (nearer than `JOIN`), or before a note that
    the left hand starts, stops when the pick comes down for that stroke:
    its message "note off" is immediately before the next "note on", as in
    the examples of the makers. Then the sound of the stop does not play.
    A note with a gap after it stops at its end, with the sound of the hand
    that stops the string. A note that is longer rings on.
    """
    ordered = sorted(strokes, key=lambda item: (round(item.start, 3), item.midi))
    chords = guitar.chords_of(ordered)
    result: list[_Note] = []
    previous_start = -10.0
    down = False
    before: Stroke | None = None
    for number, chord in enumerate(chords):
        down = not down if chord[0].start - previous_start < FAST else True
        previous_start = chord[0].start
        strings = chord if down else chord[::-1]
        for place, stroke in enumerate(strings):
            switch = _switch(stroke, down, before if len(chord) == 1 else None)
            low, high = RANGES[switch]
            key = int(np.clip(round(stroke.midi), low, high))
            start = stroke.start + place * STRUM
            slide = int(round(stroke.midi - stroke.slide_from)) if switch == SLIDE_IN else 0
            result.append(
                _Note(
                    key=key,
                    switch=switch,
                    velocity=velocity(stroke.level),
                    send=max(0.0, start - float(table[(switch, side)][key])),
                    start=start,
                    end=stroke.start + stroke.seconds,
                    chord=number,
                    slide=slide,
                )
            )
        before = chord[0] if len(chord) == 1 else None
    # The ends of the notes.
    moment = 1.0 / RATE
    first_send: dict[int, float] = {}
    first_start: dict[int, float] = {}
    for note in result:
        first_send[note.chord] = min(first_send.get(note.chord, np.inf), note.send)
        first_start[note.chord] = min(first_start.get(note.chord, np.inf), note.start)
    legato = {number for number, chord in enumerate(chords) if len(chord) == 1 and chord[0].hammer}
    later_same: dict[int, float] = {}  # for each key: the next "note on" of the same key
    for note in sorted(result, key=lambda item: -item.send):
        same = later_same.get(note.key)
        following = note.chord + 1
        if same is not None and same - moment < note.end:
            # The same string again: the note stops before its key goes down again.
            note.end = same - moment
        elif following in first_send:
            gap = first_start[following] - note.end
            if abs(gap) < JOIN or (gap > 0.0 and following in legato):
                note.end = first_send[following] - moment
        note.end = max(note.end, note.send + 0.005)
        later_same[note.key] = note.send
    return result


def messages(
    strokes: list[Stroke], side: int, table: dict[tuple[int, int], np.ndarray]
) -> list[Message]:
    """Return the MIDI messages for the notes of one performance."""
    result: list[Message] = []

    def at(seconds: float, phase: int, kind: str, first: int, second: int = 0) -> None:
        # At one moment: first the ends of notes, then the controllers, then the starts
        # of notes. In each of these, the messages keep the sequence of this code.
        order = phase * 10_000_000 + len(result)
        result.append(Message(max(0, int(round(seconds * RATE))), order, kind, first, second))

    for note in notes(strokes, side, table):
        # The key switch comes before the two messages of a note: the sound of the stop
        # of a note is also different for each way of playing.
        if note.slide:
            at(note.send, 2, "cc", SLIDE_IN_INTERVAL, min(127, 8 + 16 * (note.slide - 1)))
        at(note.send, 2, "note_on", note.switch, 100)
        at(note.send, 2, "note_off", note.switch)
        at(note.send, 2, "note_on", note.key, note.velocity)
        at(note.end, 0, "note_on", note.switch, 100)
        at(note.end, 0, "note_off", note.switch)
        at(note.end, 0, "note_off", note.key)
    # A vibrato on long notes, and the pitch of a note that slides: one curve of values
    # for each, with a value each `STEP` seconds.
    if strokes:
        length = int((max(item.start + item.seconds for item in strokes) + 1.0) / STEP) + 2
        time = np.arange(length) * STEP
        depth = np.zeros(length)
        bend = np.zeros(length)
        for stroke in strokes:
            inside = (time >= stroke.start) & (time < stroke.start + stroke.seconds)
            if stroke.vibrato:
                rise = np.clip((time - stroke.start - VIBRATO_START) / VIBRATO_RISE, 0.0, 1.0)
                depth = np.maximum(depth, np.where(inside, stroke.vibrato * rise, 0.0))
            if stroke.bend:
                knots = np.linspace(0.0, max(stroke.seconds, 0.05), len(stroke.bend))
                curve = np.interp(time - stroke.start, knots, stroke.bend)
                bend = np.where(inside, curve, bend)
        # The vibrato of the program goes from the note up to two times its depth (a
        # finger on a string can only make the pitch higher). The depth of a stroke is
        # in cents to each side of the note: the same distance from the lowest to the
        # highest pitch.
        for name, values in (
            ("cc", np.clip(np.round(127.0 * depth / 100.0), 0, 127).astype(int)),
            ("pitch_wheel", np.round(8191.0 * np.clip(bend / BEND_RANGE, -1.0, 1.0)).astype(int)),
        ):
            changes = np.flatnonzero(np.diff(values, prepend=0))
            for place in changes:
                if name == "cc":
                    at(float(time[place]), 1, "cc", VIBRATO_DEPTH, int(values[place]))
                else:
                    at(float(time[place]), 1, "pitch_wheel", int(values[place]))
    return result


def direct(strokes: list[Stroke], seconds: float, side: int, seed: int = 0) -> np.ndarray:
    """Return the direct signal of the pickup for all notes of one performance.

    `side` selects one of the two recordings of each note (0 or 1). `seed`
    is not used: the sampler has its own random numbers.
    """
    del seed
    sampler = _sampler()
    _quiet(sampler)
    sound = play(sampler, messages(strokes, side, latency()), seconds + 0.5)
    return sound[:, side] * np.float32(dsp.db(DIRECT_DB))


if __name__ == "__main__":
    # Measure the program, if the table is not there.
    for (way, channel), values in sorted(latency().items()):
        low, high = RANGES[way]
        part = 1000.0 * values[low : high + 1]
        print(f"way of playing {way:3d}, channel {channel}: {part.mean():5.1f} ms "
              f"(from {part.min():5.1f} to {part.max():5.1f})")  # fmt: skip
