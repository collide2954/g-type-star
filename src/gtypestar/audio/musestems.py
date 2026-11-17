"""Render the wind and string players with MuseScore and Muse Sounds.

MuseScore renders three groups, each as one file (a stem): the solo tenor
saxophone, the horn section, and the strings. Three
MuseScore programs run at the same time. A stem stays in the cache if its
music did not change.

Muse Sounds are free sample libraries of Muse Group. Only MuseScore Studio
can play them, and a build server cannot install them. On a computer with
no Muse Sounds, synthesizer patches play these parts (`band.render_substitute`).
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from ..notation import musicxml
from ..notation.work import Work
from ..perform.events import perform
from . import dsp, musescore

RATE = dsp.RATE
DIRECTORY = Path("build/musescore")
VERSION = 1  # a change of this number makes all kept stems invalid
PARALLEL_RENDERS = 3

# The groups: the name of the stem and its players.
GROUPS = {
    "tsax": ("tsax",),
    "horns": ("tpt", "asax", "tbn", "bsax"),
    "strings": ("vn1", "vn2", "va", "vc"),
}


def available() -> bool:
    return musescore.available()


def played_key(work: Work, bars: tuple[int, int] | None, members: set[str]) -> str:
    """Return a key of the music of some players as they play it, not as it is written.

    Two ways to write the same sound (a whole note, or two half notes with a
    tie) have the same key: a change of the notation alone does not make
    MuseScore render the stem again. The key has each note with its time in
    seconds: a change of a tempo changes it.
    """
    structure = work.structure
    digest = hashlib.sha256(
        f"{VERSION}|{musescore.PROFILE}|{musescore.MASTER_VOLUME_DB}|{bars}".encode()
    )
    for player in sorted(members):
        notes = sorted(perform(work, player), key=lambda n: (n.start, n.midi, n.duration))
        for note in notes:
            if bars is not None and not bars[0] <= structure.bar_at(note.start).number <= bars[1]:
                continue
            digest.update(
                repr((player, note.instrument, round(structure.seconds(note.start), 5),
                      round(structure.seconds(note.start + note.duration), 5), note.midi,
                      round(note.level, 4), round(note.level_end, 4), note.accent,
                      sorted(note.articulations), note.legato, note.tremolo, note.trill,
                      note.harmonic, note.glissando, note.fermata, note.grace, note.state)).encode()
            )  # fmt: skip
    return digest.hexdigest()


def stamp(work: Work) -> list[str]:
    """Write the key of the played music into the record of each kept stem of the full work.

    This is for stems that an older version of the code made (their record
    has the key of the written music only). Call it only when the stems are
    the stems of the music as it is now. Return the names of the stems.
    """
    done = []
    for name, members in GROUPS.items():
        record = DIRECTORY / name / "stem.json"
        if record.exists() and (DIRECTORY / name / "score.wav").exists():
            kept = json.loads(record.read_text(encoding="utf-8"))
            kept["played"] = played_key(work, None, set(members))
            record.write_text(json.dumps(kept), encoding="utf-8")
            done.append(name)
    return done


def render(
    work: Work,
    bars: tuple[int, int] | None,
    players: list[str],
    seconds: float,
    begin: float,
) -> dict[str, np.ndarray]:
    """Render the groups that have one or more of the given players.

    Return one stem for each group, with two channels and the length
    `seconds`. The sound of the first bar starts after the lead time of an
    excerpt (see `render.LEAD_SECONDS`).
    """
    from .render import LEAD_SECONDS

    lead = int((LEAD_SECONDS if begin > 0 else 0.0) * RATE)
    total = int(seconds * RATE) + RATE

    def one(name: str) -> tuple[str, np.ndarray | None]:
        members = {player for player in GROUPS[name] if player in players}
        if not members:
            return name, None
        text, names = musicxml.score(work, bars, players=members)
        if not names:
            return name, None
        folder = DIRECTORY / (name if bars is None else f"{name}-{bars[0]}-{bars[1]}")
        record = folder / "stem.json"
        sound = folder / "score.wav"
        key = hashlib.sha256(
            f"{VERSION}|{musescore.PROFILE}|{musescore.MASTER_VOLUME_DB}|{text}".encode()
        ).hexdigest()
        played = played_key(work, bars, members)
        kept = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {}
        # The stem stays if the music is written the same way, or if it sounds the same.
        if sound.exists() and (kept.get("key") == key or kept.get("played") == played):
            audio = musescore._load(sound)
        else:
            audio, _names = musescore.render(work, folder, bars, players=members)
        if kept.get("key") != key or kept.get("played") != played:
            data = {"key": key, "played": played, "parts": names}
            record.write_text(json.dumps(data), encoding="utf-8")
        out = np.zeros((total, 2), dtype=np.float32)
        length = min(total - lead, len(audio))
        out[lead : lead + length] = audio[:length]
        return name, out

    with ThreadPoolExecutor(max_workers=PARALLEL_RENDERS) as pool:
        results = list(pool.map(one, GROUPS))
    return {name: audio for name, audio in results if audio is not None}
