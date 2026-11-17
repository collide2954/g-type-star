"""Render the work: events, stems, mix, and master.

The steps are:

1. The performance layer changes the written music of each player into
   events with times in seconds (`perform/feel.py`).
2. Each player gets the sound of its instrument (`band.py`, `kit.py`).
3. The mixer makes the mix from the stems (`console.py`).
4. The changes of the recording itself (repeats, stops, reversed sound) are
   applied to the groups of stems (`glitch.py`).
5. The master step gives the loudness and the tone balance of the reference
   recordings.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile

from ..notation.work import Work
from ..perform import feel
from ..perform.events import perform
from . import band, console, dsp

RATE = dsp.RATE
TAIL_SECONDS = 5.0  # the time after the last bar of a render, for the sound that rings on
RING_SECONDS = 3.0  # the time after the end of the longest note
SUBSTITUTE_GAIN = 3.5  # a patch in place of a real instrument, relative to Muse Sounds
LEAD_SECONDS = 0.5  # time before the first bar of an excerpt

# The feel of each player, if the work does not give one.
FEELS = {
    "drums": feel.DRUMS, "perc": feel.DRUMS, "bass": feel.BASS, "gtr": feel.GUITAR,
    "keys.rh": feel.KEYS, "keys.lh": feel.KEYS, "tsax": feel.LEAD, "lead": feel.KEYS,
    "tpt": feel.SECTION, "asax": feel.SECTION, "tbn": feel.SECTION, "bsax": feel.SECTION,
    "vn1": feel.SECTION, "vn2": feel.SECTION, "va": feel.SECTION, "vc": feel.SECTION,
}  # fmt: skip
MUSE_PLAYERS = ("tpt", "asax", "tsax", "tbn", "bsax", "vn1", "vn2", "va", "vc")


def window(work: Work, bars: tuple[int, int] | None) -> tuple[float, float]:
    """Return the first and the last second of the work or of an excerpt."""
    structure = work.structure
    if bars is None:
        return 0.0, structure.duration_seconds
    return (
        structure.seconds(structure.bar(bars[0]).start),
        structure.seconds(structure.bar(bars[1]).end),
    )


def player_events(work: Work, player: str) -> list[feel.Event]:
    """Return the events of one player for the full work."""
    notes = perform(work, player)
    plans = work.extras.get("feels", {})
    plan = plans.get(player) or plans.get(player.split(".")[0]) or FEELS.get(player, feel.EXACT)
    backbeats = work.extras.get("backbeats")
    return feel.events(work.structure, notes, plan, drums=player == "drums", backbeats=backbeats)


EARLY = 0.05  # a note that a player starts this much before a bar line is in the next part


def _inside(
    events: list[feel.Event], begin: float, end: float, last: bool = True
) -> list[feel.Event]:
    """Return the events of a time window, with times from the start of the render.

    A player can start a note a little before the bar line. Such a note is
    in the part of the render that starts at that bar line, and only there:
    `last` says that no part comes after this window.
    """
    from dataclasses import replace

    shift = LEAD_SECONDS - begin if begin > 0 else 0.0
    lower = begin - EARLY if begin > 0 else -1e9
    upper = end if last else end - EARLY
    return [
        replace(event, start=event.start + shift)
        for event in events
        if lower <= event.start < upper
    ]


def render_stems(
    work: Work,
    bars: tuple[int, int] | None = None,
    *,
    muse: bool | None = None,
    muse_full: dict[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray, float]:
    """Render the stems of the work or of some bars. Return the stems, the kick times, the length.

    `muse`: use MuseScore with Muse Sounds for the wind and string players
    (default: yes, if the computer has them). `muse_full` are the stems of
    MuseScore for the full work: the function takes the part for the bars.
    """
    from . import guitar, kit, musestems, perc, sfzguitar, tape

    begin, end = window(work, bars)
    lead = LEAD_SECONDS if begin > 0 else 0.0
    seconds = end - begin + TAIL_SECONDS + lead
    # A part of the full render (`muse_full` is given) that is not the last part: the
    # next part has the notes that start just before its first bar line.
    last = muse_full is None or end >= work.structure.duration_seconds - 1e-6
    if _JOB.get("work") is work:
        last = end >= work.structure.duration_seconds - 1e-6
    if muse is None:
        muse = musestems.available()
    stems: dict[str, np.ndarray] = {}
    kicks: list[float] = []
    muse_events: dict[str, list[feel.Event]] = {}
    keys_events: list[feel.Event] = []
    gathered = {
        player.id: _inside(player_events(work, player.id), begin, end, last)
        for player in work.orchestra.players
    }
    # A long note that starts in these bars must sound to its end: the render has more
    # time after the last bar, if a note needs it.
    longest = max(
        (event.start + event.seconds for events in gathered.values() for event in events),
        default=0.0,
    )
    seconds = max(seconds, longest + RING_SECONDS)
    for player in work.orchestra.players:
        events = gathered[player.id]
        if not events:
            continue
        first = events[0].note.instrument
        if player.id == "drums":
            for name, sound in kit.render(events, seconds).items():
                stems[f"drums.{name}"] = sound
            kicks += [event.start for event in events if int(event.midi) in (35, 36)]
        elif player.id == "eperc":
            stems["eperc"] = band.cached(
                "eperc", events, seconds, lambda e=events: band.render_machine(e, seconds)
            )
            kicks += [event.start for event in events if int(event.midi) == 36]
        elif player.id == "perc":
            if perc.available():
                stems["perc"] = band.cached(
                    "perc", events, seconds, lambda e=events: perc.render(e, seconds)
                )
        elif first == "guitar":
            # The recorded guitar and the string model are two different sounds. (The
            # name of the kept stems has a word that changes with the settings of the
            # guitar: see `guitar.signature`.)
            name = "gtr"
            if guitar.available():
                name = f"gtr-recorded-{guitar.signature()}{sfzguitar.signature()}"
            stems["gtr"] = band.cached(
                name, events, seconds, lambda e=events: band.render_guitar(e, seconds)
            )
        elif first == "bass guitar":
            stems["bass"] = band.cached(
                "bass", events, seconds, lambda e=events: band.render_bass(e, seconds)
            )
        elif first in ("electric piano", "wurlitzer"):
            keys_events.extend(events)
        elif first in band.SUBSTITUTES:
            if muse and player.id in MUSE_PLAYERS:
                muse_events[player.id] = events
            else:
                # A synthesizer patch plays the part: its level is near that of Muse Sounds.
                stems[player.id] = band.cached(
                    player.id + "-substitute",
                    events,
                    seconds,
                    lambda e=events, p=player.id: (
                        band.render_substitute(e, seconds, p) * SUBSTITUTE_GAIN
                    ),
                )
        elif first != "tape":
            stems[player.id] = band.cached(
                player.id,
                events,
                seconds,
                lambda e=events, p=player.id: band.render_patch(e, seconds, p),
            )
    if keys_events:
        keys_events.sort(key=lambda event: event.start)
        stems["keys"] = band.cached(
            "keys", keys_events, seconds, lambda: band.render_keys(keys_events, seconds)
        )
    if muse_events and muse_full is not None:
        total = int(seconds * RATE) + RATE
        first_sample = int((begin - lead) * RATE)
        # The stems of MuseScore are recordings of the full work. This part of the
        # render gets the piece from its first bar to its last bar, with a short
        # change-over to the pieces of the adjacent parts. (Without this, the sound
        # after a part was in two parts of the render, and two times as loud.)
        cross = int(CROSS_SECONDS * RATE)
        window_first = int(round(lead * RATE))
        window_last = int(round((end - begin + lead) * RATE))
        for name, full in muse_full.items():
            part = full[max(0, first_sample) : first_sample + total]
            if np.any(part):
                piece = np.zeros((total, 2), dtype=np.float32)
                piece[: len(part)] = part
                if begin > 0:
                    piece[:window_first] = 0.0
                    ramp = np.linspace(0.0, 1.0, cross, dtype=np.float32)[:, None]
                    piece[window_first : window_first + cross] *= ramp
                if not last:
                    ramp = np.linspace(1.0, 0.0, cross, dtype=np.float32)[:, None]
                    piece[window_last : window_last + cross] *= ramp
                    piece[window_last + cross :] = 0.0
                if np.any(piece):
                    stems[name] = piece
    elif muse_events:
        stems.update(musestems.render(work, bars, list(muse_events), seconds, begin))
    recorded = tape.render(work, begin, end, seconds, lead)
    if recorded is not None and np.any(recorded):
        stems["tape"] = recorded
    return stems, np.array(sorted(kicks)), seconds


def mix_bars(
    work: Work,
    bars: tuple[int, int] | None,
    *,
    muse: bool | None = None,
    muse_full: dict[str, np.ndarray] | None = None,
    gains: dict[str, float] | None = None,
    stems_to: Path | None = None,
    parts: dict[str, np.ndarray] | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Render and mix the work or some bars. Return the mix before the master, and the gains.

    `parts`: a dictionary that gets the stems for export (see `console.mix`).
    """
    from . import glitch, tape

    stems, kicks, seconds = render_stems(work, bars, muse=muse, muse_full=muse_full)
    if not stems:
        # A passage with no sound.
        return np.zeros((int(seconds * RATE), 2), dtype=np.float32), dict(gains or {})
    settings = work.extras.get("mix") or console.Mix()
    begin, end = window(work, bars)
    offset = LEAD_SECONDS - begin if begin > 0 else 0.0
    stems = glitch.apply(work, stems, offset, begin, end)
    # A recorded voice over the band: the band goes down a little while the voice speaks.
    under = tape.ducking(work, offset, max(len(stem) for stem in stems.values()))
    if under is not None:
        stems = {
            name: stem if name == "tape" else stem * under[: len(stem), None]
            for name, stem in stems.items()
        }
    if stems_to is not None:
        stems_to.mkdir(parents=True, exist_ok=True)
        for name, sound in stems.items():
            soundfile.write(str(stems_to / f"{name}.flac"), sound, RATE, subtype="PCM_24")
    return console.mix(stems, settings, kicks, gains, parts)


CHUNK_SECONDS = 40.0  # the full work is rendered in parts of about this length
CROSS_SECONDS = 0.02  # two parts change over in this time (the stems of MuseScore)
# Each worker needs 2 to 3 GB of memory. With three workers, a computer with 12 GB killed
# one of them, and the render did not end.
WORKERS = 2
_JOB: dict = {}


def chunks(work: Work) -> list[tuple[int, int]]:
    """Divide the work into parts for the render: (first bar, last bar).

    A part starts at a rehearsal mark or after a double bar line, if that
    is possible: there the sound changes, and a cut is not audible.
    """
    structure = work.structure
    cuts = sorted({1, *structure.marks, *(bar + 1 for bar in structure.double_bars)})
    cuts = [bar for bar in cuts if bar <= len(structure.bars)]
    result = []
    for index, first in enumerate(cuts):
        last = cuts[index + 1] - 1 if index + 1 < len(cuts) else len(structure.bars)
        start = first
        while start <= last:
            stop = start
            begin = structure.seconds(structure.bar(start).start)
            while stop < last and structure.seconds(structure.bar(stop + 1).end) - begin <= (
                CHUNK_SECONDS
            ):
                stop += 1
            result.append((start, stop))
            start = stop + 1
    return result


def _chunk(bars: tuple[int, int]) -> tuple[int, np.ndarray, dict[str, np.ndarray] | None]:
    """Render one part of the work.

    Return its first sample in the work, its mix, and its stems for export
    (if the job asks for them).
    """
    work = _JOB["work"]
    parts: dict[str, np.ndarray] | None = {} if _JOB.get("export") else None
    mixed, _gains = mix_bars(
        work, bars, muse=_JOB["muse"], muse_full=_JOB["muse_full"], gains=_JOB["gains"],
        parts=parts,
    )  # fmt: skip
    begin, _end = window(work, bars)
    lead = LEAD_SECONDS if begin > 0 else 0.0
    return int(round((begin - lead) * RATE)), mixed, parts


def _results(parts: list[tuple[int, int]], workers: int):
    """Render the parts, some at the same time. Give the result of each part.

    If the system stops a worker (not enough memory), the parts that are
    not ready are rendered one after the other in this process.
    """
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from concurrent.futures.process import BrokenProcessPool

    if workers <= 1:
        yield from map(_chunk, parts)
        return
    ready: set[tuple[int, int]] = set()
    try:
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            jobs = {pool.submit(_chunk, part): part for part in parts}
            for job in as_completed(jobs):
                result = job.result()
                ready.add(jobs[job])
                yield result
    except BrokenProcessPool:
        left = [part for part in parts if part not in ready]
        print(f"render: a worker stopped; {len(left)} parts are rendered one after the other")
        yield from map(_chunk, left)


def reference_bars(work: Work) -> tuple[int, int]:
    """Return the bars that give the balance of the groups: a passage with all players."""
    marks = {label: bar for bar, label in work.structure.marks.items()}
    if "D" in marks and "E" in marks:
        return marks["D"], marks["E"] - 1
    return 1, min(len(work.structure.bars), 24)


def reference_gains(work: Work, muse: bool) -> dict[str, float]:
    """Return the gains of the groups (drums, bass, music) from the reference passage.

    The gains stay in the cache: they change only if the music of the
    passage or the settings of the mix change. Thus an excerpt renders fast.
    """
    import hashlib
    import json

    bars = reference_bars(work)
    begin, end = window(work, bars)
    from . import kit

    digest = hashlib.sha1(repr((band.VERSION, bars, muse)).encode())  # noqa: S324
    digest.update(repr(work.extras.get("mix")).encode())
    if kit.kit() is not kit.CROCELL:
        digest.update(repr(kit.kit()).encode())  # a different drum kit has different levels
    for player in work.orchestra.players:
        for event in _inside(player_events(work, player.id), begin, end):
            digest.update(
                repr((player.id, round(event.start, 4), round(event.seconds, 4), event.midi,
                      round(event.level, 3), event.note.instrument, event.note.state)).encode()
            )  # fmt: skip
    path = band.CACHE_DIR / f"gains-{digest.hexdigest()[:16]}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    _mix, gains = mix_bars(work, bars, muse=muse)
    band.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(gains), encoding="utf-8")
    return gains


def render(
    work: Work,
    bars: tuple[int, int] | None = None,
    *,
    muse: bool | None = None,
    stems_to: Path | None = None,
    workers: int = WORKERS,
    export_to: Path | None = None,
    only: tuple[int, int] | None = None,
) -> tuple[np.ndarray, console.MasterReport]:
    """Render the work or an excerpt. Return the master and its report.

    The full work is rendered in parts, some at the same time. The levels of
    the groups (drums, bass, music) come from one passage with all players:
    all parts use the same levels.

    `export_to`: a directory for the stems of the full work (drums, bass,
    guitar, keys, saxophone, horns, strings, synthesizers, recorded sounds,
    reverberation). The sum of the stems is the mix before the master. All
    stems get the same gain: the gain of the master, or less if a stem
    would be too loud for the file.

    `only`: render only the parts of the full work inside these bars (a test
    of the full render; the rest of the result is silent).
    """
    from . import banks, guitar, kit, musestems

    if muse is None:
        muse = musestems.available()
    if bars is None and workers > 1:
        # Each worker keeps recordings in memory: with some workers, each keeps fewer.
        kit.CACHE.limit = 600_000_000
        banks.CACHE_BYTES = 300_000_000
        guitar.CACHE_BYTES = 250_000_000
    gains = reference_gains(work, muse)
    begin, end = window(work, bars)
    if bars is not None and only is None:
        mixed, _gains = mix_bars(work, bars, muse=muse, gains=gains, stems_to=stems_to)
        return console.master(mixed, tone=(end - begin) > 20.0)

    muse_full = None
    if muse:
        seconds = work.structure.duration_seconds + TAIL_SECONDS
        muse_full = musestems.render(work, None, list(MUSE_PLAYERS), seconds, 0.0)
    total = int((work.structure.duration_seconds + TAIL_SECONDS) * RATE) + RATE
    full = np.zeros((total, 2), dtype=np.float32)
    _JOB.update(work=work, muse=muse, muse_full=muse_full, gains=gains,
                export=export_to is not None)  # fmt: skip
    exports: dict[str, np.memmap] = {}
    try:
        parts = chunks(work)
        if only is not None:
            parts = [part for part in parts if only[0] <= part[0] and part[1] <= only[1]]
        for first, mixed, stems in _results(parts, workers):
            cut = -first if first < 0 else 0
            first = max(first, 0)
            last = min(total, first + len(mixed) - cut)
            full[first:last] += mixed[cut : cut + last - first]
            for name, sound in (stems or {}).items():
                if name not in exports:
                    # A stem of the full work is large: it stays in a file, not in memory.
                    export_to.mkdir(parents=True, exist_ok=True)
                    exports[name] = np.memmap(export_to / f".{name}.f32", dtype=np.float32,
                                              mode="w+", shape=(total, 2))  # fmt: skip
                exports[name][first:last] += sound[cut : cut + last - first]
    finally:
        _JOB.clear()
    final, report = console.master(full)
    if exports:
        _write_exports(exports, export_to, report.limiter_drive_db)
    return final, report


def _write_exports(exports: dict[str, np.memmap], directory: Path, drive_db: float) -> None:
    """Write the stems of the full work as FLAC files, all with the same gain."""
    block = 1 << 20
    peak = 0.0
    for sound in exports.values():
        for start in range(0, len(sound), block):
            peak = max(peak, float(np.max(np.abs(sound[start : start + block]))))
    gain = min(dsp.db(drive_db), 0.94 / max(peak, 1e-9))
    for name, sound in exports.items():
        with soundfile.SoundFile(str(directory / f"{name}.flac"), "w", RATE, 2, "PCM_24") as file:
            for start in range(0, len(sound), block):
                file.write(np.asarray(sound[start : start + block]) * np.float32(gain))
        path = Path(sound.filename)
        del sound
        path.unlink()
    exports.clear()
    (directory / "README.txt").write_text(
        "The stems of G-Type Star before the master. Their sum is the mix. All stems have\n"
        f"the same gain ({dsp.to_db(gain):+.1f} dB). The master has, after this sum, a filter for\n"
        "the tone balance, a compressor, and a limiter (see docs/audio.md).\n",
        encoding="utf-8",
    )


def position_seconds(work: Work, bar: int, beat: Fraction | float = 1) -> float:
    return work.structure.seconds(work.structure.position(bar, beat))
