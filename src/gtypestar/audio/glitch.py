"""Changes of the recording itself: repeats, stops, reversed sound, and filters.

The style edits its own sound: a short part repeats many times (stutter), the
"tape" slows down and stops, a part plays backwards, the sound goes silent
for a moment, or a filter closes over the full band. These changes are not
notes of a player. The work gives them as a list of edits. Each edit names
the stems that it changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from ..notation.work import Work
from . import dsp, effects

RATE = dsp.RATE


@dataclass(frozen=True)
class Edit:
    """One change of the recording.

    `kind` is one of: stutter, tapestop, reverse, mute, gate, crush, lowpass,
    highpass. `bar` and `beat` give the start (the beat is in quarter notes,
    1 = start of the bar). `length` is the length of the changed part in
    quarter notes. `stems` are the first parts of the names of the stems
    that change ("" = all stems).
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

    @property
    def label(self) -> str:
        """Return the text of the edit in the score."""
        values = {4.0: "whole", 2.0: "half", 1.0: "quarter", 0.5: "eighth", 0.25: "sixteenth",
                  0.125: "thirty-second"}  # fmt: skip
        piece = values.get(float(self.slice), f"{float(self.slice):g} quarter")
        if self.kind == "stutter":
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
        else:
            text = {"tapestop": "Tape stop", "reverse": "Reverse", "mute": "Silence"}[self.kind]
        if self.stems != ("",):
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
