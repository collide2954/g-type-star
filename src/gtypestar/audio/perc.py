"""Hand percussion: shaker, tambourine, cabasa, cowbell, congas, and bongos.

The samples are recordings of real instruments from the Versilian Community
Sample Library (VCSL, Versilian Studios, CC0 1.0). Each instrument has some
strokes of different force and two takes of most of them: the same take
does not come two times one after the other.

The shaker has two kinds of stroke, away from the player and back. Fast
notes take them in turn, as the hand of a player does.

The result is one stem with two channels. Each instrument has its place
between left and right.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile
import soxr

from ..perform.feel import Event
from . import dsp

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples/vcsl")
STRUCK = "Idiophones/Struck Idiophones"
SKINS = "Membranophones/Struck Membranophones"
URL = "https://raw.githubusercontent.com/sgossner/VCSL/master/"
SHAKER_TURN = 0.3  # seconds: two shaker notes that are nearer are two halves of one move


@dataclass(frozen=True)
class Sound:
    """One instrument: its strokes from soft to loud, each with its takes."""

    folder: str
    layers: tuple[tuple[str, ...], ...]
    gain_db: float = 0.0
    place: float = 0.0  # -1 = left, 1 = right
    back: tuple[str, ...] = ()  # the shaker: the takes of the move back


SOUNDS: dict[int, Sound] = {
    82: Sound(
        f"{STRUCK}/Shaker, Small",
        (("Mid_ShakerHighFaster_Down_rr1", "Mid_ShakerHighFaster_Down_rr2"),),
        gain_db=12.0, place=0.4,
        back=("Mid_ShakerHighFaster_Up_rr1", "Mid_ShakerHighFaster_Up_rr2"),
    ),
    54: Sound(
        f"{STRUCK}/Tambourine 1",
        (("Tamb1_Hit_v1_rr1_Mid",), ("Tamb1_Hit_v2_rr1_Mid",)),
        gain_db=2.0, place=-0.4,
    ),
    69: Sound(f"{STRUCK}/Cabasa", (("Cabasa1_Hit_rr1_Mid", "Cabasa1_Hit_rr2_Mid"),),
              gain_db=6.0, place=0.5),
    56: Sound(
        f"{STRUCK}/Cowbells",
        (("Cowbell1_Hit_v2_rr1_Mid",), ("Cowbell1_Hit_v3_rr1_Mid",), ("Cowbell1_Hit_v4_rr1_Mid",)),
        gain_db=-4.0, place=-0.2,
    ),
    63: Sound(
        f"{SKINS}/Conga",
        (("Quinto_HitN_v1_rr1_Sum", "Quinto_HitN_v1_rr2_Sum"),
         ("Quinto_HitN_v2_rr1_Sum", "Quinto_HitN_v2_rr2_Sum"),
         ("Quinto_HitN_v3_rr1_Sum", "Quinto_HitN_v3_rr2_Sum")),
        gain_db=0.0, place=-0.3,
    ),
    62: Sound(
        f"{SKINS}/Conga",
        (("Quinto_HitFM1_v1_rr1_Sum", "Quinto_HitFM1_v1_rr2_Sum"),
         ("Quinto_HitFM1_v2_rr1_Sum", "Quinto_HitFM1_v2_rr2_Sum")),
        gain_db=2.0, place=-0.3,
    ),
    64: Sound(
        f"{SKINS}/Conga",
        (("Conga_HitN_v1_rr1_Sum", "Conga_HitN_v1_rr2_Sum"),
         ("Conga_HitN_v2_rr1_Sum", "Conga_HitN_v2_rr2_Sum"),
         ("Conga_HitN_v3_rr1_Sum", "Conga_HitN_v3_rr2_Sum")),
        gain_db=2.0, place=-0.1,
    ),
    60: Sound(
        f"{SKINS}/Bongos",
        (("BongoH_Hit1_v1_rr1_Mid", "BongoH_Hit1_v1_rr2_Mid"),
         ("BongoH_Hit1_v2_rr1_Mid", "BongoH_Hit1_v2_rr2_Mid"),
         ("BongoH_Hit1_v3_rr1_Mid", "BongoH_Hit1_v3_rr2_Mid")),
        gain_db=2.0, place=0.25,
    ),
    61: Sound(
        f"{SKINS}/Bongos",
        (("BongoL_Hit1_v1_rr1_Mid", "BongoL_Hit1_v1_rr2_Mid"),
         ("BongoL_Hit1_v2_rr1_Mid", "BongoL_Hit1_v2_rr2_Mid"),
         ("BongoL_Hit1_v3_rr1_Mid", "BongoL_Hit1_v3_rr2_Mid")),
        gain_db=2.0, place=0.15,
    ),
}  # fmt: skip


def files() -> list[str]:
    """Return the paths of all sample files, from the top directory of the library."""
    names = []
    for sound in SOUNDS.values():
        for take in (*[name for layer in sound.layers for name in layer], *sound.back):
            names.append(f"{sound.folder}/{take}.wav")
    return sorted(set(names))


def available() -> bool:
    return all((SAMPLES_DIR / name).exists() for name in files())


@lru_cache(maxsize=128)
def _load(path: str) -> np.ndarray:
    data, rate = soundfile.read(path, dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    if rate != RATE:
        data = soxr.resample(data, rate, RATE, quality="HQ").astype(np.float32)
    # The recordings start a little before the stroke: the sound starts at the stroke.
    level = np.max(np.abs(data), axis=1)
    loud = np.flatnonzero(level > 0.1 * float(level.max()))
    first = max(0, int(loud[0]) - int(0.004 * RATE)) if len(loud) else 0
    data = data[first:].copy()
    fade = min(len(data), int(0.05 * RATE))
    data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
    return data


def render(events: list[Event], seconds: float) -> np.ndarray:
    """Play the events of the percussion player. Return a stem with two channels."""
    total = int(seconds * RATE) + RATE
    out = np.zeros((total, 2), dtype=np.float32)
    ordered = sorted(events, key=lambda event: event.start)
    last_take: dict[int, str] = {}
    shaker_time, shaker_back = -10.0, False
    for number, event in enumerate(ordered):
        midi = int(event.midi)
        sound = SOUNDS.get(midi)
        if sound is None:
            continue
        level = float(np.clip(event.level + event.note.accent, 0.02, 1.0))
        seed = zlib.crc32(repr((midi, number, round(event.start, 4))).encode())
        random = np.random.default_rng(seed)
        takes = sound.layers[min(len(sound.layers) - 1, int(level * len(sound.layers)))]
        if sound.back:
            # The move back comes after a move away, if the two notes are near in time.
            shaker_back = event.start - shaker_time < SHAKER_TURN and not shaker_back
            shaker_time = event.start
            if shaker_back:
                takes = sound.back
        choice = [take for take in takes if take != last_take.get(midi)] or list(takes)
        take = choice[int(random.integers(len(choice)))]
        last_take[midi] = take
        data = _load(str(SAMPLES_DIR / sound.folder / f"{take}.wav"))
        first = int(round(event.start * RATE))
        if first < 0 or first >= total:
            continue
        length = min(len(data), total - first)
        gain = dsp.db(sound.gain_db) * level**1.1
        angle = (sound.place + 1.0) * np.pi / 4.0
        out[first : first + length, 0] += data[:length, 0] * np.float32(gain * np.cos(angle) * 1.41)
        out[first : first + length, 1] += data[:length, 1] * np.float32(gain * np.sin(angle) * 1.41)
    return out


def fetch() -> Path:
    """Download the sample files that are not in the cache. Return their directory."""
    import subprocess
    from urllib.parse import quote

    for name in files():
        path = SAMPLES_DIR / name
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(".part")
        subprocess.run(
            ["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3",
             "--user-agent", "g-type-star-build", "-o", str(part), URL + quote(name)],
            check=True,
        )  # fmt: skip
        part.replace(path)
    return SAMPLES_DIR
