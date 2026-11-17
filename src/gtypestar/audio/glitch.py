"""Changes of the recording itself: repeats, stops, reversed sound, and filters.

The style edits its own sound: a short part repeats many times (stutter), the
"tape" slows down and stops, a part plays backwards, the sound goes silent
for a moment, or a filter closes over the full band. These changes are not
notes of a player. The work gives them as a list of edits. Each edit names
the stems that it changes.

Three kinds are long changes (`LONG_KINDS`): they can go through many bars.
They make the end of the work, where the gravity of the white dwarf pulls
the music down: the pitch of the recording falls with no change of the
time ("sink"), the sound moves to the centre ("narrow"), and a low-pass
filter closes slowly ("darken").
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
from numba import njit

from ..notation.work import Work
from . import dsp, effects

RATE = dsp.RATE
# The long kinds of edit. Their values are functions of the time of the work: the render
# makes the work in parts (see `render.chunks`), and each part gets the correct values.
LONG_KINDS = ("sink", "narrow", "darken")


@dataclass(frozen=True)
class Edit:
    """One change of the recording.

    `kind` is one of: stutter, tapestop, reverse, mute, gate, crush, lowpass,
    highpass, echo, shimmer, freeze, and the long kinds sink, narrow, darken. `bar` and `beat` give
    the start (the beat is in quarter notes, 1 = start of the bar). `length`
    is the length of the changed part in quarter notes. `stems` are the first
    parts of the names of the stems that change ("" = all stems).

    "echo" is a delay on the changed part, as a player does it with a pedal: the sound
    of the part comes again after `slice` quarter notes, some times, each time softer
    (`fade` is the level of each echo relative to the one before; `share` is the level
    of the first echo). The echoes go on after the end of the part.

    "shimmer" is a long reverb whose sound is one octave higher than the sound that
    goes in: a bright cloud above held chords (`share` is its level).

    "freeze" holds one moment of the sound: the first `slice` quarter notes of the part
    go on as a sound that does not move, for the full length of the part, and fade
    (`share` is the level, `fade` the share of the length with full level).

    The long kinds: "sink" moves the pitch from `pitch_start` to `pitch`
    (semitones; the time does not change). "narrow" moves the stereo width
    from `width_start` to `width`. "darken" moves the cutoff of a low-pass
    filter from `start` to `end`. `curve` gives the shape of the change.
    """

    kind: str
    bar: int
    beat: Fraction | float = 1
    length: Fraction | float = 1
    stems: tuple[str, ...] = ("",)
    slice: Fraction | float = Fraction(1, 4)  # stutter and gate: the length of one piece
    pitch: float = 0.0  # stutter: change of pitch from the first to the last piece (semitones)
    fade: float = 1.0  # stutter: level of the last piece relative to the first
    start: float = 18000.0  # filters: cutoff at the start of the edit (hertz)
    end: float = 300.0  # filters: cutoff at the end of the edit
    bits: float = 6.0  # crush: number of bits
    hold: int = 6  # crush: each sample is held for this number of samples
    share: float = 0.5  # gate: the open share of each piece
    curve: float = 1.0  # long kinds: 1 = a straight line; 2 = slow at first, then faster
    pitch_start: float = 0.0  # sink: the change of pitch at the start of the edit (semitones)
    width_start: float = 1.0  # narrow: the stereo width at the start (1 = no change)
    width: float = 0.0  # narrow: the stereo width at the end (0 = all sound in the centre)

    @property
    def label(self) -> str:
        """Return the text of the edit in the score."""
        values = {4.0: "whole", 2.0: "half", 1.0: "quarter", 0.5: "eighth", 0.25: "sixteenth",
                  0.125: "thirty-second"}  # fmt: skip
        piece = values.get(float(self.slice), f"{float(self.slice):g} quarter")
        if self.kind == "shimmer":
            text = "Reverb with the octave above"
        elif self.kind == "freeze":
            text = "The sound of this moment is held"
        elif self.kind == "echo":
            text = f"Echoes, one {piece} note apart"
        elif self.kind == "stutter":
            text = f"Repeat one {piece} note"
            if self.pitch:
                text += f", the pitch goes {'up' if self.pitch > 0 else 'down'}"
        elif self.kind == "gate":
            text = f"Cut the sound in {piece} notes"
        elif self.kind == "crush":
            text = f"Low resolution ({self.bits:g} bits)"
        elif self.kind in ("lowpass", "highpass"):
            name = "Low-pass" if self.kind == "lowpass" else "High-pass"
            text = f"{name} filter, {self.start:.0f} Hz to {self.end:.0f} Hz"
        elif self.kind == "sink":
            text = f"The pitch of the recording falls, {self.pitch_start:g} to {self.pitch:g}"
            text += " semitones"
            if self.pitch_start == self.pitch:
                text = f"The pitch of the recording stays {abs(self.pitch):g} semitones lower"
        elif self.kind == "narrow":
            text = f"The sound moves to the centre, width {self.width_start:g} to {self.width:g}"
            if self.width_start == self.width:
                text = f"The sound stays near the centre, width {self.width:g}"
        elif self.kind == "darken":
            move = "closes" if self.end < self.start else "opens"
            text = f"A low-pass filter {move} slowly, {self.start:.0f} Hz to {self.end:.0f} Hz"
            if self.start == self.end:
                text = f"The low-pass filter stays at {self.end:.0f} Hz"
        else:
            text = {"tapestop": "Tape stop", "reverse": "Reverse", "mute": "Silence"}[self.kind]
        if self.kind in LONG_KINDS and len(self.stems) > 8:
            text += " (the band)"
        elif self.stems != ("",):
            text += " (" + ", ".join(self.stems) + ")"
        return f"{text}, {float(self.length):g} quarter notes"


def _matches(name: str, edit: Edit) -> bool:
    return any(name.startswith(prefix) for prefix in edit.stems)


def _resample(piece: np.ndarray, speed: np.ndarray) -> np.ndarray:
    """Play a piece with a speed for each output sample (1 = normal)."""
    position = np.concatenate([[0.0], np.cumsum(speed)[:-1]])
    position = position[position < len(piece) - 1]
    index = position.astype(int)
    share = (position - index)[:, None]
    return piece[index] * (1.0 - share) + piece[index + 1] * share


def stutter(part: np.ndarray, piece: int, pitch: float, fade: float) -> np.ndarray:
    """Fill the part with repeats of its first piece."""
    out = np.zeros_like(part)
    count = int(np.ceil(len(part) / piece))
    source = part[:piece].copy()
    edge = min(64, piece // 4)
    for number in range(count):
        share = number / max(count - 1, 1)
        speed = 2.0 ** (pitch * share / 12.0)
        played = _resample(source, np.full(piece, speed)) if pitch else source
        played = played.copy()
        played[:edge] *= np.linspace(0.0, 1.0, edge)[:, None]
        played[-edge:] *= np.linspace(1.0, 0.0, edge)[:, None]
        first = number * piece
        last = min(len(part), first + len(played))
        out[first:last] = played[: last - first] * (1.0 + (fade - 1.0) * share)
    return out


def tapestop(part: np.ndarray) -> np.ndarray:
    """Slow the sound down to a stop, as a tape machine that loses its power."""
    out = np.zeros_like(part)
    count = len(part)
    speed = np.clip(1.0 - np.arange(count) / (0.8 * count), 0.0, 1.0) ** 0.7
    played = _resample(part, speed)
    out[: len(played)] = played
    gain = np.clip(speed * 4.0, 0.0, 1.0)[:, None]
    return out * gain


@njit(cache=True, fastmath=True)
def _agreement(
    mono: np.ndarray, first: float, second: float, rate: float, size: int, step: int
) -> float:
    """Return how well two parts of a sound agree (a larger value = a better agreement).

    The parts start at `first` and at `second`. Each `step`-th sample of
    `size` samples is compared, with the read speed `rate`.
    """
    count = len(mono)
    together, own = 0.0, 1e-9
    index = 0
    while index < size:
        place_1 = int(first + rate * index)
        place_2 = int(second + rate * index)
        if 0 <= place_1 < count and 0 <= place_2 < count:
            together += mono[place_1] * mono[place_2]
            own += mono[place_2] * mono[place_2]
        index += step
    return together / np.sqrt(own)


@njit(cache=True, fastmath=True)
def shift_pitch(sound: np.ndarray, ratio: np.ndarray, grain: int, search: int) -> np.ndarray:
    """Change the pitch of a sound with two channels. Its length does not change.

    `ratio` gives the pitch ratio for each sample (0.5 = one octave lower).
    The sound is cut into short pieces (`grain` samples) that overlap by one
    half. Each piece is played slower or faster, from the place in the sound
    that has the same time. The start of each piece moves a little (not more
    than `search` samples) to the place where it agrees best with the end of
    the piece before it: thus a held tone gets no beats, and a stroke of a
    drum is not heard two times.
    """
    count = len(sound)
    out = np.zeros((count, 2))
    hop = grain // 2
    mono = sound[:, 0] + sound[:, 1]
    before_start = 0.0
    before_rate = 1.0
    for start in range(0, count, hop):
        rate = ratio[start]
        best = 0
        if start > 0 and abs(rate - 1.0) > 1e-4:
            expected = before_start + before_rate * hop
            # A coarse search first, then a fine search near its best place.
            best_score = _agreement(mono, expected, float(start), rate, hop, 8)
            coarse = 0
            for move in range(-search, search + 1, 12):
                score = _agreement(mono, expected, float(start + move), rate, hop, 8)
                if score > best_score * 1.02 + 1e-9:
                    best_score, coarse = score, move
            best = coarse
            best_score = _agreement(mono, expected, float(start + coarse), rate, hop, 4)
            for move in range(coarse - 11, coarse + 12):
                score = _agreement(mono, expected, float(start + move), rate, hop, 4)
                if score > best_score + 1e-9:
                    best_score, best = score, move
        read = float(start + best)
        for index in range(grain):
            target = start + index
            if target >= count:
                break
            weight = 0.5 - 0.5 * np.cos(2.0 * np.pi * (index + 0.5) / grain)
            if start == 0 and index < hop:
                # The first half of the first piece has no piece before it.
                out[target, 0] += (1.0 - weight) * sound[target, 0]
                out[target, 1] += (1.0 - weight) * sound[target, 1]
            position = read + rate * index
            place = int(np.floor(position))
            if place < 0 or place + 1 >= count:
                continue
            share = position - place
            out[target, 0] += weight * (
                sound[place, 0] * (1.0 - share) + sound[place + 1, 0] * share
            )
            out[target, 1] += weight * (
                sound[place, 1] * (1.0 - share) + sound[place + 1, 1] * share
            )
        before_start, before_rate = read, rate
    return out


def shimmer(part: np.ndarray) -> np.ndarray:
    """Return a reverb of the part whose sound is one octave higher (no direct sound).

    The sound goes into a long room; the sound of the room is moved up one
    octave; the result goes into a second room, which makes it smooth.
    """
    first = effects.reverb(part, effects.room(3.2, brightness=0.7, predelay=0.03, seed=31))
    # The sound of a room has no clear phase: the pieces need no search for a good place.
    high = shift_pitch(first, np.full(len(first), 2.0), 3072, 0)
    second = effects.reverb(high, effects.room(2.6, brightness=0.55, seed=32))
    second = effects.each(second, lambda channel: dsp.apply(channel, dsp.highpass(500.0, 2)))
    return second * 0.5


def freeze(moment: np.ndarray, total: int, hold: float = 0.6, seed: int = 9) -> np.ndarray:
    """Return a sound of `total` samples that holds the sound of a short moment.

    Short pieces of the moment (0.2 seconds, from places at random) follow
    each other and overlap: the result has the tone of the moment and no
    rhythm. It has full level for the share `hold` of its length, then it fades.
    """
    random = np.random.default_rng(seed)
    grain = min(int(0.2 * RATE), max(64, len(moment) // 2))
    hop = max(1, grain // 6)
    window = np.hanning(grain)[:, None]
    out = np.zeros((total + grain, 2))
    for start in range(0, total, hop):
        place = int(random.integers(0, max(1, len(moment) - grain)))
        piece = moment[place : place + grain]
        if random.uniform() < 0.5:
            piece = piece[:, ::-1]  # the two channels change places: the sound is wide
        out[start : start + len(piece)] += piece * window[: len(piece)]
    out = out[:total]
    # The pieces have no common phase: their sum is softer than the moment. The held
    # sound gets the level of the moment.
    level_in = float(np.sqrt(np.mean(moment.astype(np.float64) ** 2)))
    level_out = float(np.sqrt(np.mean(out**2))) + 1e-12
    out = out * (level_in / level_out)
    level = np.ones(total)
    rise = min(total, int(0.08 * RATE))
    level[:rise] = np.linspace(0.0, 1.0, rise)
    fall = int(total * (1.0 - hold))
    if fall > 0:
        level[total - fall :] = np.linspace(1.0, 0.0, fall) ** 1.5
    return out * level[:, None]


def _apply_long(structure, edit: Edit, stems: dict[str, np.ndarray], offset: float) -> None:
    """Apply a long edit to the part of each stem that is inside the time of the edit.

    The values of the edit are functions of the time of the work. A stem of
    one part of the render (with the end of its sounds after the part) gets
    the same values as the stems of the other parts at the same time.
    """
    position = structure.bar(edit.bar).start + Fraction(edit.beat) - 1
    first = int((structure.seconds(position) + offset) * RATE)
    last = int((structure.seconds(position + Fraction(edit.length)) + offset) * RATE)
    for name, stem in stems.items():
        if not _matches(name, edit):
            continue
        low, high = max(first, 0), min(last, len(stem))
        if high - low < 64 or not np.any(stem[low:high]):
            continue
        part = stem[low:high].astype(np.float64)
        share = (np.arange(low, high) - first) / max(last - first, 1)
        progress = np.clip(share, 0.0, 1.0) ** edit.curve
        if edit.kind == "sink":
            semitones = edit.pitch_start + (edit.pitch - edit.pitch_start) * progress
            if float(np.max(np.abs(semitones))) < 0.02:
                continue
            # Short pieces for the drums: a stroke stays sharp. Long pieces for held tones.
            drum = name.startswith(("drums", "eperc"))
            changed = shift_pitch(
                part, 2.0 ** (semitones / 12.0), 1536 if drum else 4096, 384 if drum else 768
            )
        elif edit.kind == "narrow":
            amount = edit.width_start + (edit.width - edit.width_start) * progress
            mid = 0.5 * (part[:, 0] + part[:, 1])
            side = 0.5 * (part[:, 0] - part[:, 1]) * amount
            changed = np.stack([mid + side, mid - side], axis=1)
        else:
            cutoff = edit.start * (edit.end / edit.start) ** progress
            changed = effects.sweep(part, cutoff, "lowpass", 0.7)
        stem[low:high] = changed.astype(np.float32)


def apply(
    work: Work, stems: dict[str, np.ndarray], offset: float, begin: float, end: float
) -> dict[str, np.ndarray]:
    """Apply the edits of the work to the stems. `offset` is added to the time of the work."""
    edits: list[Edit] = work.extras.get("edits", [])  # type: ignore[assignment]
    if not edits:
        return stems
    structure = work.structure
    result = {name: stem.copy() for name, stem in stems.items()}
    for edit in sorted(edits, key=lambda item: (item.bar, float(item.beat))):
        if edit.kind in LONG_KINDS:
            _apply_long(structure, edit, result, offset)
            continue
        position = structure.bar(edit.bar).start + Fraction(edit.beat) - 1
        start_seconds = structure.seconds(position)
        if not begin - 0.01 <= start_seconds < end:
            continue
        stop_seconds = structure.seconds(position + Fraction(edit.length))
        first = int((start_seconds + offset) * RATE)
        for name, stem in result.items():
            if not _matches(name, edit):
                continue
            last = min(len(stem), int((stop_seconds + offset) * RATE))
            if last - first < 32:
                continue
            part = stem[first:last].astype(np.float64)
            piece_seconds = structure.seconds(position + Fraction(edit.slice)) - start_seconds
            piece = max(32, int(piece_seconds * RATE))
            if edit.kind in ("shimmer", "freeze"):
                if not np.any(part):
                    continue
                if edit.kind == "shimmer":
                    added = shimmer(part) * edit.share
                else:
                    added = freeze(part[:piece], len(part), edit.fade) * edit.share
                added = added[: len(stem) - first]
                stem[first : first + len(added)] += added.astype(np.float32)
                continue
            if edit.kind == "echo":
                echoes = effects.delay(part, piece / RATE, edit.fade, 0.55, repeats=7)
                echoes = echoes[: len(stem) - first] * (edit.share / max(edit.fade, 1e-6))
                stem[first : first + len(echoes)] += echoes.astype(np.float32)
                continue
            if edit.kind == "stutter":
                changed = stutter(part, piece, edit.pitch, edit.fade)
            elif edit.kind == "tapestop":
                changed = tapestop(part)
            elif edit.kind == "reverse":
                changed = part[::-1].copy()
            elif edit.kind == "mute":
                changed = np.zeros_like(part)
            elif edit.kind == "gate":
                phase = (np.arange(len(part)) % piece) / piece
                changed = part * np.clip((edit.share - phase) * 40.0, 0.0, 1.0)[:, None]
            elif edit.kind == "crush":
                changed = effects.crush(part, edit.bits, edit.hold)
            elif edit.kind in ("lowpass", "highpass"):
                share = np.linspace(0.0, 1.0, len(part))
                cutoff = edit.start * (edit.end / edit.start) ** share
                changed = effects.sweep(part, cutoff, edit.kind, 0.9)
            else:
                raise ValueError(f"unknown edit {edit.kind!r}")
            # A short fade at the two ends of the changed part: no click.
            edge = min(96, len(part) // 8)
            ramp = np.linspace(0.0, 1.0, edge)[:, None]
            changed[:edge] = changed[:edge] * ramp + part[:edge] * (1.0 - ramp)
            if edit.kind not in ("tapestop", "mute"):
                changed[-edge:] = changed[-edge:] * ramp[::-1] + part[-edge:] * (1.0 - ramp[::-1])
            stem[first:last] = changed.astype(np.float32)
    return result
