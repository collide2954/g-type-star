"""Find the notes that Muse Sounds play for each wind and string instrument of the work.

MuseScore gives no sound for a note outside the range of the samples of an
instrument, and it gives no warning. The first two masters of the work had
such notes: all notes of the tenor saxophone above E5 were silent.

This script writes a test piece: each instrument plays all notes from below
its range to above its range, one after the other, each note one second
long with one second of rest. MuseScore renders it, and the script
measures which notes have sound.

Usage:

    uv run python tools/diagnose/muse_ranges.py

The result goes into `HIGHEST_NOTE` and `LOWEST_NOTE` of
`src/gtypestar/audio/musescore.py`.
"""

from __future__ import annotations

import numpy as np

from gtypestar.audio import dsp, musestems
from gtypestar.notation.pitch import from_midi
from gtypestar.notation.work import Work, load_orchestra

MORE = 8  # semitones below and above the range of the orchestra file
PLAYERS = ("tsax", "tpt", "asax", "tbn", "bsax", "vn1", "va", "vc")


def main() -> int:
    orchestra = load_orchestra()
    work = Work("Range test", orchestra, composer="test")
    ranges = {}
    plan = []  # (player, first bar, MIDI numbers)
    place = {"tsax": 1, "horns": 1, "strings": 1}
    for player_id in PLAYERS:
        player = next(p for p in orchestra.players if p.id == player_id)
        instrument = orchestra.instruments[player.instruments[0]]
        low, high = instrument.low, instrument.high
        ranges[player_id] = (low, high)
        group = next(name for name, members in musestems.GROUPS.items() if player_id in members)
        notes = list(range(low - MORE, high + MORE + 1))
        plan.append((player_id, place[group], notes))
        place[group] += len(notes)
    count = max(place.values()) - 1
    section = work.section(count, 4, 4, ())
    work.structure.tempo(1, 1, 120.0, "Test")
    for player_id, first, notes in plan:
        bars = ["R1"] * count
        for index, midi in enumerate(notes):
            bars[first - 1 + index] = f"{from_midi(midi).name}2 r2"
        bars[first - 1] = bars[first - 1].replace("2 r2", "2\\mf r2")
        section.write(player_id, " | ".join(bars) + " |")
    section.close()
    seconds = count * 2.0 + 4.0
    stems = musestems.render(work, None, list(PLAYERS), seconds, 0.0)
    rate = dsp.RATE
    print(f"{'player':8s} {'file range':>12s} {'notes with sound':>20s}   silent in the range")
    for player_id, first, notes in plan:
        group = next(name for name, members in musestems.GROUPS.items() if player_id in members)
        audio = stems[group].mean(axis=1)
        sounding = []
        for index, midi in enumerate(notes):
            start = int(((first - 1 + index) * 2.0 + 0.15) * rate)
            part = audio[start : start + int(0.7 * rate)]
            level = 10.0 * np.log10(float(np.mean(part**2)) + 1e-12)
            if level > -55.0:
                sounding.append(midi)
        low, high = ranges[player_id]
        silent = [midi for midi in range(low, high + 1) if midi not in sounding]
        found = f"{min(sounding)} to {max(sounding)}" if sounding else "none"
        names = ", ".join(f"{midi} ({from_midi(midi).name})" for midi in silent)
        print(f"{player_id:8s} {low:5d} to {high:3d} {found:>20s}   {names or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
