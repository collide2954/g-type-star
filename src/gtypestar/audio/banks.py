"""Sample banks of the bass guitar and of the electric piano.

A bank is a set of recorded notes of one instrument: for each pitch some
loudness layers, and for each layer some different takes (round robins).

- Bass guitar: Karoryfer "Black And Blue Basses" (CC0). The black bass is a
  five-string bass, played with the fingers. The files are the direct signal
  of the pickup: the amplifier of the project comes after them.
- Electric piano: "jRhodes3d" by Jeff Learman, a 1977 Rhodes Mark I (free for
  use in music; the samples themselves are CC BY-NC).

The code downloads the two libraries into the cache. If a library is not
there, the string model or a synthesizer patch plays the part.
"""

from __future__ import annotations

import re
import subprocess
import zipfile
from collections import OrderedDict
from pathlib import Path

import numpy as np
import soundfile
import soxr

from . import dsp

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples")
BASS_URL = (
    "https://github.com/sfzinstruments/karoryfer.black-and-blue-basses/releases/download/"
    "v1.002/Black_And_Blue_Basses_1002.zip"
)
RHODES_URL = "https://github.com/sfzinstruments/jlearman.jRhodes3d.git"
PITCH_CLASS = {"c": 0, "db": 1, "d": 2, "eb": 3, "e": 4, "f": 5, "gb": 6, "g": 7, "ab": 8,
               "a": 9, "bb": 10, "b": 11}  # fmt: skip
CACHE_BYTES = 900_000_000


class _Cache:
    def __init__(self) -> None:
        self.size = 0
        self.items: OrderedDict[tuple[Path, int], np.ndarray] = OrderedDict()
        self.leads: dict[tuple[Path, int], float] = {}

    def lead(self, path: Path, cents: int = 0) -> float:
        """Return the time in seconds from the start of a sample to its sound."""
        key = (path, cents)
        if key not in self.leads:
            self.leads[key] = dsp.onset(self.get(path, cents))
        return self.leads[key]

    def get(self, path: Path, cents: int = 0) -> np.ndarray:
        """Return one sample (one channel) at the project rate, moved by `cents`."""
        key = (path, cents)
        if key in self.items:
            self.items.move_to_end(key)
            return self.items[key]
        if cents:
            base = self.get(path, 0)
            ratio = 2.0 ** (cents / 1200.0)
            data = soxr.resample(base, RATE * ratio, RATE, quality="HQ").astype(np.float32)
        else:
            raw, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
            data = raw.mean(axis=1)
            if rate != RATE:
                data = soxr.resample(data, rate, RATE, quality="HQ").astype(np.float32)
        self.items[key] = data
        self.size += data.nbytes
        while self.size > CACHE_BYTES and len(self.items) > 1:
            _, removed = self.items.popitem(last=False)
            self.size -= removed.nbytes
        return data


CACHE = _Cache()


def fetch_bass() -> Path | None:
    """Return the sample directory of the bass. Download the library if it is not there."""
    folder = SAMPLES_DIR / "basses"
    if not (folder / "Samples" / "darkblack").exists():
        archive = folder / "Black_And_Blue_Basses_1002.zip"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                subprocess.run(["curl", "-sL", "-o", str(archive), BASS_URL], check=True)
            with zipfile.ZipFile(archive) as packed:
                packed.extractall(folder)
        except (OSError, subprocess.CalledProcessError, zipfile.BadZipFile):
            return None
    return folder / "Samples" / "darkblack"


def fetch_rhodes() -> Path | None:
    """Return the sample directory of the electric piano. Download it if it is not there."""
    folder = SAMPLES_DIR / "jrhodes3d"
    if not (folder / "jRhodes3d-mono").exists():
        try:
            SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", RHODES_URL, str(folder)], check=True
            )
        except (OSError, subprocess.CalledProcessError):
            return None
    return folder / "jRhodes3d-mono"


class BassBank:
    """The fingered five-string bass: each semitone, four loudness layers, four takes."""

    LAYERS = ("p", "mp", "mf", "f")
    NAME = re.compile(r"darkblack_([a-g]b?)(\d)_(?:(p|mp|mf|f)|ghost_(p|f)|stac|rel)_rr(\d)\.wav")

    def __init__(self, folder: Path) -> None:
        self.notes: dict[tuple[str, int, str], list[Path]] = {}
        for kind in ("reg", "ghost", "stac", "rel"):
            for path in sorted((folder / kind).glob("*.wav")):
                match = self.NAME.fullmatch(path.name)
                if not match:
                    continue
                letter, octave, layer, ghost, _take = match.groups()
                # The names of the files are one octave above the sounding pitch.
                midi = 12 * int(octave) + PITCH_CLASS[letter]
                key = (kind, midi, layer or ghost or "")
                self.notes.setdefault(key, []).append(path)
        self.lowest = min(midi for kind, midi, _ in self.notes if kind == "reg")
        self.highest = max(midi for kind, midi, _ in self.notes if kind == "reg")

    def sample(
        self, kind: str, midi: float, level: float, take: int
    ) -> tuple[np.ndarray, float, float]:
        """Return a sample for a note, the gain that gives it the wanted loudness, and
        the time in seconds from the start of the sample to its sound (`dsp.onset`)."""
        nearest = int(np.clip(round(midi), self.lowest, self.highest))
        cents = int(round((midi - nearest) * 100.0))
        if kind == "reg":
            position = float(np.clip(level, 0.0, 1.0)) ** 1.1 * (len(self.LAYERS) - 1)
            layer = self.LAYERS[int(round(position))]
            # Between two layers, the level of the sample moves a little.
            gain = dsp.db(4.0 * (position - round(position)))
            if level < 0.2:
                gain *= 0.4 + 3.0 * level
        elif kind == "ghost":
            layer, gain = ("f" if level > 0.5 else "p"), 1.0
        else:
            layer, gain = "", 0.3 + 0.9 * level
        takes = self.notes.get((kind, nearest, layer)) or self.notes.get(("reg", nearest, "mf"))
        if not takes:
            return np.zeros(1, dtype=np.float32), 0.0, 0.0
        path = takes[take % len(takes)]
        return CACHE.get(path, cents), float(gain), CACHE.lead(path, cents)


class RhodesBank:
    """The electric piano: 15 sampled pitches, five loudness layers."""

    NAME = re.compile(r"A_(\d{3})__\w+?_(\d)\.flac")

    def __init__(self, folder: Path) -> None:
        self.notes: dict[tuple[int, int], Path] = {}
        for path in sorted(folder.glob("*.flac")):
            match = self.NAME.fullmatch(path.name)
            if match:
                self.notes[(int(match.group(1)), int(match.group(2)))] = path
        self.pitches = sorted({midi for midi, _layer in self.notes})
        self.layers = sorted({layer for _midi, layer in self.notes})

    def sample(self, midi: float, level: float) -> list[tuple[np.ndarray, float]]:
        """Return one or two samples (loudness layers) with their gains."""
        nearest = min(self.pitches, key=lambda pitch: abs(pitch - midi))
        cents = int(round((midi - nearest) * 100.0 / 10.0)) * 10
        # The high notes of the library have fewer layers than the low notes.
        layers = sorted(layer for pitch, layer in self.notes if pitch == nearest)
        wanted = 1.0 + float(np.clip(level, 0.0, 1.0)) ** 1.3 * (self.layers[-1] - 1)
        below = [layer for layer in layers if layer <= wanted] or layers[:1]
        above = [layer for layer in layers if layer >= wanted] or layers[-1:]
        low, high = below[-1], above[0]
        share = 0.0 if high == low else (wanted - low) / (high - low)
        # A soft note is softer than the softest layer.
        trim = dsp.db(-14.0 * (1.0 - min(1.0, level / 0.35))) if level < 0.35 else 1.0
        result = []
        for layer, weight in ((low, np.cos(share * np.pi / 2)), (high, np.sin(share * np.pi / 2))):
            if weight > 0.02:
                path = self.notes[(nearest, layer)]
                result.append((CACHE.get(path, cents), float(weight * trim)))
        return result
