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
        kept = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {}
        if sound.exists() and kept.get("key") == key:
            audio = musescore._load(sound)
        else:
            audio, _names = musescore.render(work, folder, bars, players=members)
            record.write_text(json.dumps({"key": key, "parts": names}), encoding="utf-8")
        out = np.zeros((total, 2), dtype=np.float32)
        length = min(total - lead, len(audio))
        out[lead : lead + length] = audio[:length]
        return name, out

    with ThreadPoolExecutor(max_workers=PARALLEL_RENDERS) as pool:
        results = list(pool.map(one, GROUPS))
    return {name: audio for name, audio in results if audio is not None}
