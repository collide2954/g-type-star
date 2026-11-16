"""The drum kit: play the strokes of the drummer with samples of a real kit.

The samples are a drum kit of the DrumGizmo project. Each sample is one
stroke on one drum, recorded with all microphones of the kit at the same
time: the near microphones, the overhead microphones, and the room
microphones. Thus each stroke also has the sound that the other microphones
get from that drum, as in a studio recording.

Each drum has many strokes of different force. Each stroke has a measured
power in the description file of the kit. For the loudness of an event, the
code selects a stroke of the nearest power, with a small random choice: the
same stroke does not come two times one after the other.

The result is one stem for each group of microphones: kick, snare, toms,
hi-hat and ride (the near microphones), overheads, and room.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
import zlib
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile
import soxr

from ..perform.feel import Event
from . import dsp

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples")
CACHE_BYTES = 1_800_000_000
GRACE_SECONDS = 0.032  # a grace note (flam) comes this much before the main stroke


@dataclass(frozen=True)
class KitSpec:
    """One kit: where its files are, and which sample group plays each drum of the work."""

    name: str
    folder: str  # in the sample directory
    url: str
    licence: str
    credit: str
    # The note of the work (MIDI number) -> the instrument of the kit.
    drums: dict[int, str]
    # The group of microphones -> the channels of the kit and the place of each (left to right).
    groups: dict[str, dict[str, float]]
    # Longest part of a stroke that the code uses, in seconds, for each instrument (default 4).
    longest: dict[str, float]
    # Instruments whose ring stops when a later stroke of these notes comes (the hi-hat).
    chokes: dict[str, tuple[int, ...]]
    accent: dict[int, str]  # the instrument for a note with an accent (for example a rimshot)
    gains_db: dict[str, float]
    mics_db: dict[str, float]  # the level of each group of microphones, to agree with the mixer


CROCELL = KitSpec(
    name="CrocellKit",
    folder="crocellkit/CrocellKit",
    url="https://drumgizmo.org/kits/CrocellKit/CrocellKit1_1.zip",
    licence="CC BY 4.0",
    credit="Drum samples: CrocellKit, DrumGizmo.org",
    drums={
        36: "KDrumR", 35: "KDrumL", 38: "Snare", 40: "Snare", 37: "SnareRim",
        42: "HihatClosed", 46: "HihatOpen", 44: "HihatPedal",
        51: "RideR", 53: "RideRBell", 49: "CrashL", 57: "CrashR", 52: "ChinaR", 55: "SplashL",
        50: "Tom1", 47: "Tom2", 43: "FTom1", 41: "FTom2",
    },
    groups={
        "kick": {"KDrumInside": 0.0, "KDrumOutside": 0.0},
        "snare": {"SnareTop": 0.0, "SnareBottom": 0.0},
        "toms": {"Tom1": -0.35, "Tom2": -0.1, "FTom1": 0.3, "FTom2": 0.5},
        "cymbals": {"Hihat": -0.45, "Ride": 0.45},
        "overheads": {"OHLeft": -1.0, "OHRight": 1.0, "OHCenter": 0.0},
        "room": {"AmbLeft": -1.0, "AmbRight": 1.0},
    },
    longest={"RideR": 5.0, "RideRBell": 4.0, "CrashL": 5.0, "CrashR": 5.0, "ChinaR": 3.5,
             "SplashL": 2.5, "HihatOpen": 2.5, "KDrumR": 1.2, "KDrumL": 1.2},
    chokes={"HihatOpen": (42, 44, 46)},
    accent={38: "SnareRimShot"},
    gains_db={},
    # The recordings of this kit are softer than those of the DRSKit, and its room is louder.
    mics_db={"kick": 11.0, "snare": 10.0, "toms": 12.0, "cymbals": 10.0, "overheads": 8.5,
             "room": -1.0},
)  # fmt: skip

DRS = KitSpec(
    name="DRSKit",
    folder="drskit/DRSKit",
    url="https://drumgizmo.org/kits/DRSKit/DRSKit2_1.zip",
    licence="CC BY 4.0",
    credit="Drum samples: DRSKit, DrumGizmo.org",
    drums={
        36: "Kdrum_with_contact", 35: "Kdrum_without_contact", 38: "Snare", 40: "Snare",
        37: "Snare_rim", 42: "Hihat_closed", 46: "Hihat_open", 44: "Hihat_foot",
        51: "Ride_tip", 53: "Ride_tip_bell", 49: "Crash_left_shank", 57: "Crash_right_shank",
        52: "Crash_left_tip", 55: "Crash_right_tip",
        50: "Tom1", 47: "Tom2", 43: "Tom2", 41: "Tom3",
    },
    groups={
        "kick": {"Kdrum_back": 0.0, "Kdrum_front": 0.0},
        "snare": {"Snare_top": 0.0, "Snare_bottom": 0.0},
        "toms": {"Tom1": -0.3, "Tom2": 0.25, "Tom3": 0.5},
        "cymbals": {"Hihat": -0.45, "Ride": 0.45},
        "overheads": {"OHL": -1.0, "OHR": 1.0},
        "room": {"AmbL": -1.0, "AmbR": 1.0},
    },
    longest={"Ride_tip": 5.0, "Ride_tip_bell": 4.0, "Crash_left_shank": 5.0,
             "Crash_right_shank": 5.0, "Crash_left_tip": 1.2, "Crash_right_tip": 1.5,
             "Hihat_open": 2.5, "Kdrum_with_contact": 1.2, "Kdrum_without_contact": 1.2},
    chokes={"Hihat_open": (42, 44, 46), "Hihat_semi_open": (42, 44, 46)},
    accent={},
    gains_db={},
    mics_db={},
)  # fmt: skip


def kit() -> KitSpec:
    """Return the kit of the work: the first kit of the list that is in the cache."""
    for spec in (CROCELL, DRS):
        if (SAMPLES_DIR / spec.folder).exists():
            return spec
    raise FileNotFoundError(
        "No drum kit in .cache/samples. See README.md, 'Requirements', for the download."
    )


@dataclass
class Hit:
    """One recorded stroke."""

    path: Path
    power: float
    channels: dict[str, int]  # channel name -> number of the channel in the file (0 = first)


class _Cache:
    """Keep loaded strokes in memory, up to a size limit."""

    def __init__(self, limit: int = CACHE_BYTES) -> None:
        self.limit = limit
        self.size = 0
        self.items: OrderedDict[Path, np.ndarray] = OrderedDict()

    def get(self, hit: Hit, seconds: float) -> np.ndarray:
        if hit.path in self.items:
            self.items.move_to_end(hit.path)
            return self.items[hit.path]
        with soundfile.SoundFile(str(hit.path)) as handle:
            frames = min(len(handle), int(seconds * handle.samplerate))
            data = handle.read(frames, dtype="float32", always_2d=True)
            rate = handle.samplerate
        if rate != RATE:
            data = soxr.resample(data, rate, RATE, quality="HQ").astype(np.float32)
        # A soft end, if the stroke is cut.
        fade = min(len(data), int(0.25 * RATE))
        data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        self.items[hit.path] = data
        self.size += data.nbytes
        while self.size > self.limit and len(self.items) > 1:
            _, removed = self.items.popitem(last=False)
            self.size -= removed.nbytes
        return data


CACHE = _Cache()


def read_instrument(spec: KitSpec, name: str) -> list[Hit]:
    """Read the description file of one instrument of the kit. Return its strokes by power."""
    folder = SAMPLES_DIR / spec.folder / name
    tree = ElementTree.parse(folder / f"{name}.xml")
    hits = []
    for sample in tree.getroot().iter("sample"):
        files = sample.findall("audiofile")
        if not files:
            continue
        channels = {
            entry.get("channel", ""): int(entry.get("filechannel", "1")) - 1 for entry in files
        }
        path = folder / files[0].get("file", "")
        if path.exists():
            hits.append(Hit(path, float(sample.get("power", "1")), channels))
    hits.sort(key=lambda hit: hit.power)
    return hits


def available() -> bool:
    return any((SAMPLES_DIR / spec.folder).exists() for spec in (CROCELL, DRS))


def choose(hits: list[Hit], level: float, random: np.random.Generator, last: int) -> int:
    """Return the number of the stroke for a loudness from 0 to 1."""
    count = len(hits)
    centre = float(np.clip(level, 0.0, 1.0)) ** 1.15 * (count - 1)
    reach = max(1.0, 0.045 * count)
    for _ in range(4):
        index = int(np.clip(round(centre + random.uniform(-reach, reach)), 0, count - 1))
        if index != last or count == 1:
            return index
    return int(np.clip(round(centre), 0, count - 1))


def render(
    events: list[Event], seconds: float, spec: KitSpec | None = None
) -> dict[str, np.ndarray]:
    """Play the events of the drummer. Return one stem (two channels) for each group."""
    spec = spec or kit()
    total = int(seconds * RATE) + RATE
    stems = {group: np.zeros((total, 2), dtype=np.float32) for group in spec.groups}
    instruments: dict[str, list[Hit]] = {}
    last_index: dict[str, int] = {}
    ordered = sorted(events, key=lambda event: event.start)
    starts = np.array([event.start for event in ordered])
    midis = np.array([int(event.midi) for event in ordered])
    previous_kick = -10.0
    for number, event in enumerate(ordered):
        midi = int(event.midi)
        name = spec.drums.get(midi)
        if name is None:
            continue
        level = min(1.0, event.level + event.note.accent)
        if event.note.accent >= 0.1 and midi in spec.accent and level > 0.55:
            name = spec.accent[midi]
        start = event.start
        if event.note.grace:
            start -= event.note.grace * GRACE_SECONDS
            level *= 0.55
        # Fast strokes of one foot are not possible: the feet take turns.
        if midi == 36 and name == spec.drums[36]:
            if start - previous_kick < 0.16 and last_index.get("foot") == 36:
                name, foot = spec.drums.get(35, name), 35
            else:
                foot = 36
            last_index["foot"] = foot
            previous_kick = start
        if name not in instruments:
            instruments[name] = read_instrument(spec, name)
        hits = instruments[name]
        if not hits:
            continue
        random = np.random.default_rng(zlib.crc32(repr((name, number, round(start, 4))).encode()))
        index = choose(hits, level, random, last_index.get(name, -1))
        last_index[name] = index
        hit = hits[index]
        data = CACHE.get(hit, spec.longest.get(name, 4.0))
        # The softest recorded stroke is not as soft as a ghost note: make it softer.
        gain = dsp.db(spec.gains_db.get(name, 0.0))
        if level < 0.25:
            gain *= float(0.35 + 0.65 * level / 0.25)
        length = len(data)
        if name in spec.chokes:
            # The ring stops at the next stroke of the same group (the hi-hat closes).
            later = np.flatnonzero((starts > event.start + 0.02)
                                   & np.isin(midis, spec.chokes[name]))  # fmt: skip
            if len(later):
                length = min(length, int((starts[later[0]] - event.start + 0.03) * RATE))
        first = int(round(start * RATE))
        if first < 0 or first >= total:
            continue
        length = min(length, total - first)
        if length <= 0:
            continue
        shape = None
        if length < len(data):
            fade = min(length, int(0.045 * RATE))
            shape = np.ones(length, dtype=np.float32)
            shape[-fade:] = np.linspace(1.0, 0.0, fade, dtype=np.float32)
        for group, channels in spec.groups.items():
            for channel, position in channels.items():
                column = hit.channels.get(channel)
                if column is None or column >= data.shape[1]:
                    continue
                part = data[:length, column] * np.float32(gain)
                if shape is not None:
                    part = part * shape
                angle = (position + 1.0) * np.pi / 4.0
                stems[group][first : first + length, 0] += part * np.float32(np.cos(angle))
                stems[group][first : first + length, 1] += part * np.float32(np.sin(angle))
    for group, level in spec.mics_db.items():
        stems[group] *= np.float32(dsp.db(level))
    return stems
