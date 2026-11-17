"""The drum kit: play the strokes of the drummer with samples of a real kit.

The samples are a recorded drum kit. Each sample is one stroke on one drum,
recorded with all microphones of the kit at the same time: the near
microphones, the overhead microphones, and the room microphones. Thus each
stroke also has the sound that the other microphones get from that drum, as
in a studio recording.

The module reads two kinds of kit:

- A kit of the DrumGizmo project. Each stroke is one file with a channel for
  each microphone. Each drum has many strokes of different force, and each
  stroke has a measured power in the description file of the kit. For the
  loudness of an event, the code selects a stroke of the nearest power, with
  a small random choice.
- A kit in the SFZ format with one file for each microphone (`sfzkit.py`).
  Each drum has some layers of force, and ten strokes in each layer. The
  recordings of all layers have the same level: the code makes a soft stroke
  softer.

The same stroke does not come two times one after the other.

The result is one stem for each group of microphones: kick, snare, toms,
hi-hat and ride (the near microphones), overheads, and room.
"""

from __future__ import annotations

import functools
import os
import xml.etree.ElementTree as ElementTree
import zlib
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile
import soxr
from scipy import signal

from ..perform.feel import Event
from . import dsp, sfzkit

RATE = dsp.RATE
SAMPLES_DIR = Path(".cache/samples")
FAST_KICK = 0.8  # the loudness of a kick stroke less than 0.16 seconds after the stroke before
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
    # A kit in the SFZ format: the program of each microphone, and the key of each instrument.
    programs: tuple[tuple[str, str], ...] = ()
    keys: dict[str, int] = field(default_factory=dict)
    channels_db: dict[str, float] = field(default_factory=dict)  # the level of one microphone
    # The recordings of such a kit have one level for all forces of a stroke:
    # the amplitude of a stroke is its loudness (0 to 1) to this power.
    power_curve: float = 0.0
    # Filters for a group of microphones (the rows of `console.filters`): they bring the
    # tone of the group near the tone of the same group of the CrocellKit, because the
    # channel strips of the mixer are made for that kit.
    tone: dict[str, tuple] = field(default_factory=dict)
    # Microphones with the opposite polarity (a microphone under a drum, against the
    # microphone above it): the code turns their signal over.
    inverted: tuple[str, ...] = ()
    # Microphones (or trigger channels) whose signal comes late: the time in seconds by
    # which the code plays them earlier, so that they are in time with the others.
    advance: dict[str, float] = field(default_factory=dict)


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
    # The open hi-hat stops when the hi-hat closes. The kick drum is one drum with two
    # pedals: a new stroke stops the ring of the stroke before it. Without this, fast
    # strokes of the two feet add up to a low rumble.
    chokes={"HihatOpen": (42, 44, 46), "KDrumR": (35, 36), "KDrumL": (35, 36)},
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
    chokes={"Hihat_open": (42, 44, 46), "Hihat_semi_open": (42, 44, 46),
            "Kdrum_with_contact": (35, 36), "Kdrum_without_contact": (35, 36)},  # fmt: skip
    accent={},
    gains_db={},
    mics_db={},
)  # fmt: skip


# Naked Drums: a Yamaha Recording Custom kit in a small room, with ten strokes in each
# layer of force. The files of the direct microphones have one channel; the overheads
# and the far room have two.
NAKED = KitSpec(
    name="Naked Drums",
    folder="naked-drums/WilkinsonAudio.NakedDrums-master/Wilkinson Audio/Naked Drums",
    url="https://github.com/sfzinstruments/WilkinsonAudio.NakedDrums/archive/refs/heads/master.tar.gz",
    licence="CC BY 4.0",
    credit="Drum samples: Naked Drums, Wilkinson Audio (SFZ version: kinwie)",
    drums={
        36: "kick", 35: "kick", 38: "snare", 40: "snare", 37: "sidestick",
        42: "hat closed", 46: "hat open", 44: "hat pedal",
        51: "ride", 53: "ride bell", 49: "crash 1", 57: "crash 2", 52: "china", 55: "splash",
        50: "tom 1", 47: "tom 2", 43: "tom 4", 41: "tom 5",
    },
    groups={
        "kick": {"Kick In": 0.0, "Kick Sub": 0.0},
        "snare": {"Snare Tops": 0.0, "Snare Bottom": 0.0},
        "toms": {"Tom 1": -0.4, "Tom 2": -0.15, "Tom 3": 0.1, "Tom 4": 0.35, "Tom 5": 0.55},
        "cymbals": {"Hats": -0.45, "Ride": 0.45},
        "overheads": {"Overheads L": -1.0, "Overheads R": 1.0},
        "room": {"Close Room": 0.0, "Far Rooms L": -1.0, "Far Rooms R": 1.0},
    },
    longest={"ride": 5.0, "ride bell": 4.0, "crash 1": 5.0, "crash 2": 5.0, "china": 3.5,
             "splash": 2.5, "hat open": 2.5, "hat half": 2.0, "kick": 1.2},
    chokes={"hat open": (42, 44, 46), "hat half": (42, 44, 46), "kick": (35, 36)},
    accent={},
    gains_db={},
    # These levels give each group almost the level that it has with the CrocellKit
    # (tools/diagnose/kit_levels.py): the mixer has fixed settings for the groups.
    mics_db={"kick": 7.0, "snare": -4.0, "toms": 8.5, "cymbals": 11.0, "overheads": 4.5,
             "room": -2.5},
    programs=tuple(
        (name, f"Multi/{name}.sfz")
        for name in ("Kick In", "Kick Sub", "Snare Tops", "Snare Bottom", "Tom 1", "Tom 2",
                     "Tom 3", "Tom 4", "Tom 5", "Hats", "Ride", "Overheads", "Close Room",
                     "Far Rooms")
    ),
    # The kit has two snare drums: the key 38 is the drum with the higher tone.
    keys={"kick": 36, "snare": 38, "snare low": 40, "sidestick": 37, "hat tight": 39,
          "hat closed": 42, "hat half": 46, "hat open": 49, "hat pedal": 44, "ride": 51,
          "ride bell": 53, "crash 1": 55, "crash 2": 57, "splash": 54, "splash 2": 56,
          "china": 50, "china 2": 52, "tom 1": 48, "tom 2": 47, "tom 3": 45, "tom 4": 43,
          "tom 5": 41},
    channels_db={"Far Rooms L": -6.0, "Far Rooms R": -6.0},
    power_curve=1.1,
    # Measured against the CrocellKit on bars 87 to 102 (the same strokes): this kit has
    # 7 to 9 dB more level from 180 Hz to 1.4 kHz in the kick drum, 6 to 9 dB less below
    # 180 Hz in the snare drum, and 5 to 9 dB more above 5.6 kHz in all cymbal microphones.
    tone={
        "kick": (("low shelf", 55.0, 6.0), ("bell", 500.0, -7.0, 0.6),
                 ("high shelf", 5000.0, -6.0)),
        "snare": (("low shelf", 180.0, 5.0),),
        "cymbals": (("high shelf", 2000.0, -7.0),),
        "overheads": (("bell", 250.0, -6.0, 0.9), ("high shelf", 6000.0, -6.0)),
        "room": (("high shelf", 6000.0, -4.0),),
    },
)  # fmt: skip
# The MuldjordKit: a Tama Superstar kit with two kick drums, recorded for a death metal
# band ("a metal or rock kit"). Each kick drum has a microphone inside and a trigger:
# the channel of the triggers has the click of the beater (most of its level is from
# 2.5 to 6 kHz). With it, fast strokes of the two feet stay clear. The kit has no
# hi-hat pedal sound and no splash cymbal: the closed hi-hat and the left crash play them.
MULDJORD = KitSpec(
    name="MuldjordKit",
    folder="muldjordkit/MuldjordKit3",
    url="https://drumgizmo.org/kits/MuldjordKit/MuldjordKit3.zip",
    licence="CC BY 4.0",
    credit="Drum samples: MuldjordKit, DrumGizmo.org",
    drums={
        36: "KdrumR", 35: "KdrumL", 38: "Snare", 40: "Snare", 37: "SnareRest",
        42: "HihatClosed", 46: "HihatOpen", 44: "HihatClosed",
        51: "RideR", 53: "RideRBell", 49: "CrashL", 57: "CrashR", 52: "China", 55: "CrashL",
        50: "Tom1", 47: "Tom2", 43: "Tom3", 41: "Tom4",
    },
    groups={
        "kick": {"KdrumL": 0.0, "KdrumR": 0.0, "Trigger": 0.0},
        "snare": {"Snare_top": 0.0, "Snare_bottom": 0.0},
        "toms": {"Tom1": -0.4, "Tom2": -0.15, "Tom3": 0.15, "Tom4": 0.5},
        "cymbals": {"Hihat": -0.45, "RideL": -0.3, "RideR": 0.45},
        "overheads": {"OHL": -1.0, "OHR": 1.0},
        "room": {"AmbL": -1.0, "AmbR": 1.0},
    },
    longest={"RideR": 5.0, "RideRBell": 4.0, "CrashL": 5.0, "CrashR": 5.0, "China": 3.5,
             "HihatOpen": 2.5, "KdrumR": 1.2, "KdrumL": 1.2},
    chokes={"HihatOpen": (42, 44, 46), "KdrumR": (35, 36), "KdrumL": (35, 36)},
    accent={},
    gains_db={},
    # These levels give each group almost the level that it has with the CrocellKit on
    # bars 163 to 174 (tools/diagnose/kit_levels.py). The room of this kit is loud.
    mics_db={"kick": 4.8, "snare": -4.8, "toms": -0.7, "cymbals": -2.1, "overheads": -0.6,
             "room": -12.0},
    # The microphone under the snare drum has the opposite polarity (the notes of the kit
    # say this; with the two signals as they are, the drum has 3.7 dB less low sound).
    inverted=("Snare_bottom",),
)  # fmt: skip
# The Aasimonster: the kit of a death metal record (DIE, "Rise of the Rotten"). It has
# the most recordings of the kits here (93 strokes of the snare drum, rim shots, three
# closed hi-hats, china cymbals of 8, 10 and 18 inches), and trigger channels: a drum
# module that plays a kick sample at each stroke of a kick drum (it comes 12 ms after
# the microphone), and a trigger on the snare drum. The kit has no cross-stick sound:
# soft strokes away from the centre of the snare drum play it.
AASIMONSTER = KitSpec(
    name="Aasimonster",
    folder="aasimonster/aasimonster2",
    url="https://drumgizmo.org/kits/Aasimonster/aasimonster2_1.zip",
    licence="CC BY 4.0",
    credit="Drum samples: Aasimonster, DrumGizmo.org",
    drums={
        36: "kick_r", 35: "kick_l", 38: "snare_on_center", 40: "snare_on_center",
        37: "snare_off_center", 42: "hihat_closed2", 46: "hihat_open", 44: "hihat_closed1",
        51: "ride", 53: "ride_bell1", 49: "crash1", 57: "crash2", 52: "china_18_inch",
        55: "china_10_inch", 50: "tom_1", 47: "tom_2", 43: "tom_3", 41: "tom_4",
    },
    groups={
        "kick": {"Kick L": 0.0, "Kick R": 0.0, "Alesis": 0.0},
        "snare": {"Snare top": 0.0, "Snare bottom": 0.0, "Snare trigger": 0.0},
        "toms": {"Tom1": -0.4, "Tom2": -0.15, "Tom3": 0.15, "Tom4": 0.5},
        "cymbals": {"Hihat": -0.45, "Ride": 0.45},
        "overheads": {"OH L": -1.0, "OH R": 1.0},
        "room": {"Amb L": -1.0, "Amb R": 1.0},
    },
    longest={"ride": 5.0, "ride_bell1": 4.0, "crash1": 5.0, "crash2": 5.0,
             "china_18_inch": 3.5, "china_10_inch": 2.5, "hihat_open": 1.6, "kick_r": 1.2,
             "kick_l": 1.2},
    chokes={"hihat_open": (42, 44, 46), "kick_r": (35, 36), "kick_l": (35, 36)},
    accent={38: "snare_rim_shot"},
    gains_db={},
    # These levels give each group almost the level that it has with the CrocellKit on
    # bars 55 to 62 and 163 to 174 (tools/diagnose/kit_levels.py).
    mics_db={"kick": 7.2, "snare": 3.5, "toms": 6.5, "cymbals": 6.5, "overheads": 1.8,
             "room": -4.8},
    channels_db={"Snare trigger": -8.0},
    advance={"Alesis": 0.012},
)  # fmt: skip
SFZ_SWITCH = 12  # the key switch of the kit for hi-hat strokes with a fixed opening
KITS = {"crocell": CROCELL, "drs": DRS, "naked": NAKED, "muldjord": MULDJORD,
        "aasimonster": AASIMONSTER}  # fmt: skip


def kit() -> KitSpec:
    """Return the kit of the work: the first kit of the list that is in the cache.

    For a comparison of kits, the environment variable GTYPESTAR_KIT selects
    a kit by its short name (crocell, drs, naked).
    """
    wanted = os.environ.get("GTYPESTAR_KIT", "")
    if wanted:
        return KITS[wanted]
    for spec in (CROCELL, DRS):
        if (SAMPLES_DIR / spec.folder).exists():
            return spec
    raise FileNotFoundError(
        "No drum kit in .cache/samples. See README.md, 'Requirements', for the download."
    )


@dataclass(frozen=True)
class Source:
    """The sound of one stroke in one microphone."""

    channel: str  # the name of the microphone in the groups of the kit
    path: Path
    column: int  # the number of the channel in the file (0 = first)
    gain: float = 1.0


@dataclass
class Hit:
    """One recorded stroke."""

    power: float
    sources: tuple[Source, ...]
    # A kit with layers: the lowest and the highest velocity (1 to 127) of this stroke.
    span: tuple[int, int] | None = None


class _Cache:
    """Keep loaded strokes in memory, up to a size limit."""

    def __init__(self, limit: int = CACHE_BYTES) -> None:
        self.limit = limit
        self.size = 0
        self.items: OrderedDict[Path, np.ndarray] = OrderedDict()

    def get(self, path: Path, seconds: float) -> np.ndarray:
        if path in self.items:
            self.items.move_to_end(path)
            return self.items[path]
        with soundfile.SoundFile(str(path)) as handle:
            frames = min(len(handle), int(seconds * handle.samplerate))
            data = handle.read(frames, dtype="float32", always_2d=True)
            rate = handle.samplerate
        if rate != RATE:
            data = soxr.resample(data, rate, RATE, quality="HQ").astype(np.float32)
        # A soft end, if the stroke is cut.
        fade = min(len(data), int(0.25 * RATE))
        data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        self.items[path] = data
        self.size += data.nbytes
        while self.size > self.limit and len(self.items) > 1:
            _, removed = self.items.popitem(last=False)
            self.size -= removed.nbytes
        return data


CACHE = _Cache()


@functools.lru_cache(maxsize=8192)
def _file_channels(path: Path) -> int:
    return soundfile.info(str(path)).channels


def _read_sfz(spec: KitSpec, name: str) -> list[Hit]:
    """Return the strokes of one instrument of a kit in the SFZ format."""
    root = SAMPLES_DIR / spec.folder
    table = sfzkit.read(str(root), spec.programs)
    key = spec.keys[name]
    strokes: dict[tuple[int, int, int], list[Source]] = {}
    for microphone, by_key in table.items():
        for region in by_key.get(key, []):
            if region.release or region.switch not in (None, SFZ_SWITCH):
                continue
            file = root / "Samples" / region.sample
            sources = strokes.setdefault((region.low, region.high, region.position), [])
            if _file_channels(file) == 1:
                names = [microphone]
            else:
                names = [f"{microphone} L", f"{microphone} R"]
            for column, channel in enumerate(names):
                gain = dsp.db(region.volume + spec.channels_db.get(channel, 0.0))
                sources.append(Source(channel, file, column, float(gain)))
    hits = [
        Hit(float(low), tuple(sources), (low, high))
        for (low, high, _position), sources in sorted(strokes.items())
    ]
    return hits


def read_instrument(spec: KitSpec, name: str) -> list[Hit]:
    """Read the description of one instrument of the kit. Return its strokes by power."""
    if spec.programs:
        return _read_sfz(spec, name)
    folder = SAMPLES_DIR / spec.folder / name
    tree = ElementTree.parse(folder / f"{name}.xml")
    hits = []
    for sample in tree.getroot().iter("sample"):
        files = sample.findall("audiofile")
        if not files:
            continue
        path = folder / files[0].get("file", "")
        if path.exists():
            sources = tuple(
                Source(
                    entry.get("channel", ""),
                    path,
                    int(entry.get("filechannel", "1")) - 1,
                    (-1.0 if entry.get("channel") in spec.inverted else 1.0)
                    * dsp.db(spec.channels_db.get(entry.get("channel", ""), 0.0)),
                )
                for entry in files
            )
            hits.append(Hit(float(sample.get("power", "1")), sources))
    hits.sort(key=lambda hit: hit.power)
    return hits


def available() -> bool:
    return any((SAMPLES_DIR / spec.folder).exists() for spec in KITS.values())


def choose(hits: list[Hit], level: float, random: np.random.Generator, last: int) -> int:
    """Return the number of the stroke for a loudness from 0 to 1."""
    if hits[0].span is not None:
        # A kit with layers: a random stroke of the layer of this loudness.
        velocity = int(np.clip(round(level * 127.0), 1, 127))
        layer = [index for index, hit in enumerate(hits)
                 if hit.span is not None and hit.span[0] <= velocity <= hit.span[1]]  # fmt: skip
        layer = layer or list(range(len(hits)))
        other = [index for index in layer if index != last] or layer
        return other[int(random.integers(len(other)))]
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
    # The place of each microphone: its group, and its weights for the left and the right.
    places = {
        channel: (group, np.float32(np.cos((position + 1.0) * np.pi / 4.0)),
                  np.float32(np.sin((position + 1.0) * np.pi / 4.0)))
        for group, channels in spec.groups.items()
        for channel, position in channels.items()
    }  # fmt: skip
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
            fast = start - previous_kick < 0.16
            if fast and last_index.get("foot") == 36:
                name, foot = spec.drums.get(35, name), 35
            else:
                foot = 36
            if fast:
                # A stroke in a fast run has less force than a single stroke.
                level *= FAST_KICK
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
        longest = spec.longest.get(name, 4.0)
        gain = dsp.db(spec.gains_db.get(name, 0.0))
        if spec.power_curve:
            gain *= float(max(level, 0.02) ** spec.power_curve)
        # The softest recorded stroke is not as soft as a ghost note: make it softer.
        if level < 0.25:
            gain *= float(0.35 + 0.65 * level / 0.25)
        first = int(round(start * RATE))
        if first < 0 or first >= total:
            continue
        limit = total - first
        if name in spec.chokes:
            # The ring stops at the next stroke of the same group (the hi-hat closes).
            later = np.flatnonzero((starts > event.start + 0.02)
                                   & np.isin(midis, spec.chokes[name]))  # fmt: skip
            if len(later):
                limit = min(limit, int((starts[later[0]] - event.start + 0.03) * RATE))
        for source in hit.sources:
            place = places.get(source.channel)
            if place is None:
                continue
            data = CACHE.get(source.path, longest)
            length = min(len(data), limit)
            if source.column >= data.shape[1] or length <= 0:
                continue
            part = data[:length, source.column] * np.float32(gain * source.gain)
            if length < len(data):
                fade = min(length, int(0.045 * RATE))
                part[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
            group, left, right = place
            # A channel that comes late (a drum module after a trigger) plays earlier.
            early = min(first, int(spec.advance.get(source.channel, 0.0) * RATE))
            begin = first - early
            stems[group][begin : begin + length, 0] += part * left
            stems[group][begin : begin + length, 1] += part * right
    for group, level in spec.mics_db.items():
        stems[group] *= np.float32(dsp.db(level))
    if spec.tone:
        from .console import filters

        for group, rows in spec.tone.items():
            if group in stems:
                shaped = signal.sosfilt(np.vstack(filters(rows)), stems[group], axis=0)
                stems[group] = shaped.astype(np.float32)
    return stems
