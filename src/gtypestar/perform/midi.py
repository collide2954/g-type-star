"""Write the performance of the work as a MIDI file.

The file has one track for each player, the tempo plan, and the metres.
Each note has the time and the loudness of the performance layer: the small
shifts of the players are in the file. Another program (a digital audio
workstation) can open the file and play it with its own sounds.

The drums use the numbers of the General MIDI drum map.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import mido

from ..notation.work import Work

TICKS = 960  # ticks in a quarter note
# General MIDI programs (0 = the first program), as a start for the other program.
PROGRAMS = {
    "tpt": 56, "asax": 65, "tsax": 66, "tbn": 57, "bsax": 67, "lead": 81, "pad.rh": 89,
    "pad.lh": 89, "chip": 80, "keys.rh": 4, "keys.lh": 4, "gtr": 30, "bass": 33, "sbass": 38,
    "vn1": 48, "vn2": 48, "va": 48, "vc": 48,
}  # fmt: skip
DRUM_PLAYERS = ("drums", "eperc", "perc")


def position_at(work: Work, seconds: float) -> float:
    """Return the position (quarter notes) of a time in seconds."""
    structure = work.structure
    low, high = 0.0, float(structure.length)
    for _ in range(40):
        middle = 0.5 * (low + high)
        if structure.seconds(middle) < seconds:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def write(work: Work, path: Path) -> Path:
    """Write the MIDI file. Return its path."""
    from ..audio.render import player_events

    structure = work.structure
    file = mido.MidiFile(type=1, ticks_per_beat=TICKS)
    plan = mido.MidiTrack()
    plan.append(mido.MetaMessage("track_name", name=work.title, time=0))
    events: list[tuple[int, mido.MetaMessage]] = []
    previous = None
    for bar in structure.bars:
        metre = (bar.numerator, bar.denominator)
        if metre != previous:
            events.append(
                (
                    int(bar.start * TICKS),
                    mido.MetaMessage("time_signature", numerator=metre[0], denominator=metre[1]),
                )
            )
            previous = metre
    # The tempo at each quarter note: a gradual change of tempo becomes small steps.
    last = None
    position = Fraction(0)
    while position < structure.length:
        tempo = round(structure.bpm_at(position), 3)
        if tempo != last:
            events.append(
                (int(position * TICKS), mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo)))
            )
            last = tempo
        position += Fraction(1, 2)
    for bar_number, label in sorted(structure.marks.items()):
        start = int(structure.bar(bar_number).start * TICKS)
        events.append((start, mido.MetaMessage("marker", text=label)))
    now = 0
    for tick, message in sorted(events, key=lambda item: item[0]):
        plan.append(message.copy(time=tick - now))
        now = tick
    file.tracks.append(plan)

    channel = 0
    for player in work.orchestra.players:
        if player.id == "tape":
            continue
        notes = player_events(work, player.id)
        if not notes:
            continue
        track = mido.MidiTrack()
        track.append(mido.MetaMessage("track_name", name=player.name, time=0))
        if player.id in DRUM_PLAYERS:
            number = 9
        else:
            number = channel
            channel = channel + 1 if channel + 1 != 9 else channel + 2
            channel %= 16
            track.append(
                mido.Message("program_change", channel=number, program=PROGRAMS.get(player.id, 0))
            )
        messages: list[tuple[int, int, mido.Message]] = []
        for event in notes:
            start = int(round(position_at(work, event.start) * TICKS))
            end = int(round(position_at(work, event.start + event.seconds) * TICKS))
            velocity = max(1, min(127, round(127 * min(1.0, event.level + event.note.accent))))
            pitch = int(round(event.midi))
            messages.append(
                (start, 1, mido.Message("note_on", channel=number, note=pitch, velocity=velocity))
            )
            messages.append(
                (max(end, start + 1), 0, mido.Message("note_off", channel=number, note=pitch))
            )
        now = 0
        for tick, _order, message in sorted(messages, key=lambda item: (item[0], item[1])):
            track.append(message.copy(time=max(0, tick - now)))
            now = max(now, tick)
        file.tracks.append(track)
    path.parent.mkdir(parents=True, exist_ok=True)
    file.save(str(path))
    return path
