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
TAIL_SECONDS = 5.0
SUBSTITUTE_GAIN = 3.5  # a patch in place of a real instrument, relative to Muse Sounds
LEAD_SECONDS = 0.5  # time before the first bar of an excerpt

# The feel of each player, if the work does not give one.
FEELS = {
    "drums": feel.DRUMS, "bass": feel.BASS, "gtr": feel.GUITAR, "keys.rh": feel.KEYS,
    "keys.lh": feel.KEYS, "tsax": feel.LEAD, "lead": feel.KEYS,
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


def _inside(events: list[feel.Event], begin: float, end: float) -> list[feel.Event]:
    """Return the events of a time window, with times from the start of the render."""
    from dataclasses import replace

    shift = LEAD_SECONDS - begin if begin > 0 else 0.0
    return [
        replace(event, start=event.start + shift)
        for event in events
        if begin - 0.05 <= event.start < end
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
    from . import kit, musestems, tape

    begin, end = window(work, bars)
    lead = LEAD_SECONDS if begin > 0 else 0.0
    seconds = end - begin + TAIL_SECONDS + lead
    if muse is None:
        muse = musestems.available()
    stems: dict[str, np.ndarray] = {}
    kicks: list[float] = []
    muse_events: dict[str, list[feel.Event]] = {}
    keys_events: list[feel.Event] = []
    for player in work.orchestra.players:
        events = _inside(player_events(work, player.id), begin, end)
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
        elif first == "guitar":
            stems["gtr"] = band.cached(
                "gtr", events, seconds, lambda e=events: band.render_guitar(e, seconds)
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
        for name, full in muse_full.items():
            part = full[max(0, first_sample) : first_sample + total]
            if np.any(part):
                piece = np.zeros((total, 2), dtype=np.float32)
                piece[: len(part)] = part
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
) -> tuple[np.ndarray, dict[str, float]]:
    """Render and mix the work or some bars. Return the mix before the master, and the gains."""
    from . import glitch

    stems, kicks, _seconds = render_stems(work, bars, muse=muse, muse_full=muse_full)
    settings = work.extras.get("mix") or console.Mix()
    begin, end = window(work, bars)
    offset = LEAD_SECONDS - begin if begin > 0 else 0.0
    stems = glitch.apply(work, stems, offset, begin, end)
    if stems_to is not None:
        stems_to.mkdir(parents=True, exist_ok=True)
        for name, sound in stems.items():
            soundfile.write(str(stems_to / f"{name}.flac"), sound, RATE, subtype="PCM_24")
    return console.mix(stems, settings, kicks, gains)


CHUNK_SECONDS = 40.0  # the full work is rendered in parts of about this length
WORKERS = 3
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


def _chunk(bars: tuple[int, int]) -> tuple[int, np.ndarray]:
    """Render one part of the work. Return its first sample in the work, and its mix."""
    work = _JOB["work"]
    mixed, _gains = mix_bars(
        work, bars, muse=_JOB["muse"], muse_full=_JOB["muse_full"], gains=_JOB["gains"]
    )
    begin, _end = window(work, bars)
    lead = LEAD_SECONDS if begin > 0 else 0.0
    return int(round((begin - lead) * RATE)), mixed


def reference_bars(work: Work) -> tuple[int, int]:
    """Return the bars that give the balance of the groups: a passage with all players."""
    marks = {label: bar for bar, label in work.structure.marks.items()}
    if "D" in marks and "E" in marks:
        return marks["D"], marks["E"] - 1
    return 1, min(len(work.structure.bars), 24)


def render(
    work: Work,
    bars: tuple[int, int] | None = None,
    *,
    muse: bool | None = None,
    stems_to: Path | None = None,
    workers: int = WORKERS,
) -> tuple[np.ndarray, console.MasterReport]:
    """Render the work or an excerpt. Return the master and its report.

    The full work is rendered in parts, some at the same time. The levels of
    the groups (drums, bass, music) come from one passage with all players:
    all parts use the same levels.
    """
    import multiprocessing

    from . import musestems

    if muse is None:
        muse = musestems.available()
    _mix, gains = mix_bars(work, reference_bars(work), muse=muse)
    begin, end = window(work, bars)
    if bars is not None:
        mixed, _gains = mix_bars(work, bars, muse=muse, gains=gains, stems_to=stems_to)
        return console.master(mixed, tone=(end - begin) > 20.0)

    muse_full = None
    if muse:
        seconds = work.structure.duration_seconds + TAIL_SECONDS
        muse_full = musestems.render(work, None, list(MUSE_PLAYERS), seconds, 0.0)
    total = int((work.structure.duration_seconds + TAIL_SECONDS) * RATE) + RATE
    full = np.zeros((total, 2), dtype=np.float32)
    _JOB.update(work=work, muse=muse, muse_full=muse_full, gains=gains)
    try:
        parts = chunks(work)
        if workers <= 1:
            results = map(_chunk, parts)
        else:
            pool = multiprocessing.get_context("fork").Pool(workers)
            results = pool.imap_unordered(_chunk, parts)
        for first, mixed in results:
            if first < 0:
                mixed, first = mixed[-first:], 0
            last = min(total, first + len(mixed))
            full[first:last] += mixed[: last - first]
        if workers > 1:
            pool.close()
            pool.join()
    finally:
        _JOB.clear()
    return console.master(full)


def position_seconds(work: Work, bar: int, beat: Fraction | float = 1) -> float:
    return work.structure.seconds(work.structure.position(bar, beat))
