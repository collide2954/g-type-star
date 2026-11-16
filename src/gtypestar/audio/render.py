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
from . import band, console, dsp, patches

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
    work: Work, bars: tuple[int, int] | None = None, *, muse: bool | None = None
) -> tuple[dict[str, np.ndarray], np.ndarray, float]:
    """Render the stems of the work. Return the stems, the kick times, and the length.

    `muse`: use MuseScore with Muse Sounds for the wind, string, and keyboard
    players (default: yes, if the computer has them).
    """
    from . import kit, musestems

    begin, end = window(work, bars)
    seconds = end - begin + TAIL_SECONDS + (LEAD_SECONDS if begin > 0 else 0.0)
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
        elif first in patches.SUBTRACTIVE or first in patches.FM or first.startswith("chip") \
                or first == "voice pad":  # fmt: skip
            stems[player.id] = band.cached(
                player.id, events, seconds,
                lambda e=events, p=player.id: band.render_patch(e, seconds, p),
            )  # fmt: skip
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
        elif first == "tape":
            continue  # the recorded sounds come from the cue list of the work
    if keys_events:
        keys_events.sort(key=lambda event: event.start)
        stems["keys"] = band.cached(
            "keys", keys_events, seconds, lambda: band.render_keys(keys_events, seconds)
        )
    if muse_events:
        stems.update(musestems.render(work, bars, list(muse_events), seconds, begin))
    from . import tape

    recorded = tape.render(work, begin, end, seconds, LEAD_SECONDS if begin > 0 else 0.0)
    if recorded is not None:
        stems["tape"] = recorded
    return stems, np.array(sorted(kicks)), seconds


def render(
    work: Work, bars: tuple[int, int] | None = None, *, muse: bool | None = None,
    stems_to: Path | None = None,
) -> tuple[np.ndarray, console.MasterReport]:  # fmt: skip
    """Render the work or an excerpt. Return the master and its report."""
    from . import glitch

    stems, kicks, _seconds = render_stems(work, bars, muse=muse)
    settings = work.extras.get("mix") or console.Mix()
    begin, end = window(work, bars)
    offset = LEAD_SECONDS - begin if begin > 0 else 0.0
    stems = glitch.apply(work, stems, offset, begin, end)
    moves = work.extras.get("moves")
    if moves is not None:
        stems = moves(work, stems, offset)
    if stems_to is not None:
        stems_to.mkdir(parents=True, exist_ok=True)
        for name, sound in stems.items():
            soundfile.write(str(stems_to / f"{name}.flac"), sound, RATE, subtype="PCM_24")
    mixed = console.mix(stems, settings, kicks)
    return console.master(mixed, tone=bars is None or (end - begin) > 20.0)


def position_seconds(work: Work, bar: int, beat: Fraction | float = 1) -> float:
    return work.structure.seconds(work.structure.position(bar, beat))
