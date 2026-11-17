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


EVEN_LOW = 6.0  # dB: a note this far under its level is a weak note
EVEN_MOST = 10.0  # dB: the largest change of one note
EVEN_EDGE = 0.025  # seconds: the time of the change at the two ends of a note
EVEN_NOTES = 40  # with fewer notes than this, the stem has no safe level to compare with


def even(work: Work, bars: tuple[int, int] | None, player: str, audio: np.ndarray) -> np.ndarray:
    """Return the stem of one solo player with its weak notes at the level of the others.

    The sound library has notes that are much softer than the notes next to
    them. In the tenor saxophone, a G4 that follows a different note under a
    slur at a soft dynamic is 10 to 13 dB under its level: in the canon of
    the motto, where the saxophone is alone, the line had holes. An
    engineer makes such a note louder by hand. Here: the level of each note
    in the stem, against the level that its written loudness and its pitch
    give (a fit through all notes). A note more than `EVEN_LOW` dB under the
    fit comes up to half of that distance.
    """
    structure = work.structure
    origin = 0.0 if bars is None else structure.seconds(structure.bar(bars[0]).start)
    mono = audio.mean(axis=1) if audio.ndim == 2 else audio
    rows = []
    for note in perform(work, player):
        if note.grace or note.midi <= 0:
            continue
        if bars is not None and not bars[0] <= structure.bar_at(note.start).number <= bars[1]:
            continue
        start = structure.seconds(note.start) - origin
        end = structure.seconds(note.start + note.duration) - origin
        first, last = int((start + 0.03) * RATE), int(min(end, start + 1.0) * RATE)
        if last - first < int(0.04 * RATE) or last > len(mono):
            continue
        power = float(np.mean(mono[first:last].astype(np.float64) ** 2))
        if power < 1e-11:
            continue  # no sound at all: a note outside the range of the library
        rows.append((start, end, note.level, note.midi, 10.0 * np.log10(power)))
    if len(rows) < EVEN_NOTES:
        return audio
    level = np.array([row[2] for row in rows])
    midi = np.array([row[3] for row in rows])
    measured = np.array([row[4] for row in rows])
    terms = np.stack([np.ones_like(level), level, level**2, midi, midi**2], axis=1)
    keep = np.ones(len(rows), dtype=bool)
    for _turn in range(2):  # the second fit is without the weak notes
        factors, *_rest = np.linalg.lstsq(terms[keep], measured[keep], rcond=None)
        missing = terms @ factors - measured
        keep = missing < EVEN_LOW
    gain_db = np.zeros(len(mono))
    edge = int(EVEN_EDGE * RATE)
    for (start, end, *_values), less in zip(rows, missing, strict=True):
        if less <= EVEN_LOW:
            continue
        more = min(EVEN_MOST, less - EVEN_LOW / 2.0)
        first, last = max(0, int(start * RATE) - edge), min(len(mono), int(end * RATE))
        if last - first < 4 * edge:
            continue
        shape = np.ones(last - first)
        shape[:edge] = np.linspace(0.0, 1.0, edge)
        shape[-edge:] = np.linspace(1.0, 0.0, edge)
        gain_db[first:last] = np.maximum(gain_db[first:last], more * shape)
    gain = (10.0 ** (gain_db / 20.0)).astype(np.float32)
    return audio * (gain[:, None] if audio.ndim == 2 else gain)


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
        if len(members) == 1:
            audio = even(work, bars, next(iter(members)), audio)
        out = np.zeros((total, 2), dtype=np.float32)
        length = min(total - lead, len(audio))
        out[lead : lead + length] = audio[:length]
        return name, out

    with ThreadPoolExecutor(max_workers=PARALLEL_RENDERS) as pool:
        results = list(pool.map(one, GROUPS))
    return {name: audio for name, audio in results if audio is not None}
