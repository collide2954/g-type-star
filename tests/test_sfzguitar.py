"""Tests for the guitar library in a sampler: the messages, and the sound of the sampler."""

from __future__ import annotations

import numpy as np
import pytest

from gtypestar.audio import sfzguitar
from gtypestar.audio.guitar import Stroke
from gtypestar.audio.sfzguitar import (
    DEAD_DOWN,
    HAMMER_ON,
    MUTE_DOWN,
    MUTE_UP,
    PULL_OFF,
    RATE,
    SLIDE_IN,
    SLIDE_IN_INTERVAL,
    SUS_DOWN,
    SUS_UP,
    VIBRATO_DEPTH,
)

# A table for the tests: each key sounds 35 milliseconds after its message.
LATE = 0.035
TABLE = {(switch, side): np.full(128, LATE) for switch in sfzguitar.RANGES for side in (0, 1)}
needs_sampler = pytest.mark.skipif(
    not sfzguitar.available(), reason="the sampler or the guitar library is not on this computer"
)


def test_a_full_stroke_has_the_full_velocity_and_a_soft_stroke_less() -> None:
    assert sfzguitar.velocity(1.0) == 127
    assert sfzguitar.velocity(sfzguitar.FULL) == 127
    values = [sfzguitar.velocity(level) for level in (0.0, 0.2, 0.4, 0.6, 0.8)]
    assert values == sorted(values)
    assert len(set(values)) == len(values)
    # The softest stroke is not softer than the softest strokes of the makers' examples.
    assert 60 <= values[0] <= 80


def test_fast_muted_notes_go_down_and_up_and_stop_before_the_same_key_again() -> None:
    strokes = [Stroke(1.0 + 0.1 * number, 0.09, 30.0, 0.9, mute=True) for number in range(6)]
    notes = sfzguitar.notes(strokes, 0, TABLE)
    assert [note.switch for note in notes] == [MUTE_DOWN, MUTE_UP] * 3
    for note, stroke in zip(notes, strokes, strict=True):
        # Each key goes down earlier by the time from the key to its sound.
        assert note.send == pytest.approx(stroke.start - LATE)
    for now, later in zip(notes, notes[1:], strict=False):
        assert now.send < now.end < later.send


def test_slow_notes_are_down_strokes_and_a_note_before_a_gap_keeps_its_end() -> None:
    strokes = [Stroke(1.0 + 0.5 * number, 0.2, 40.0 + number, 0.9) for number in range(3)]
    notes = sfzguitar.notes(strokes, 1, TABLE)
    assert [note.switch for note in notes] == [SUS_DOWN] * 3
    assert [note.end for note in notes] == pytest.approx([1.2, 1.7, 2.2])


def test_a_note_that_ends_at_the_next_stroke_stops_when_the_pick_comes_down() -> None:
    # Three notes with no gap, and a fourth note after a rest.
    strokes = [
        Stroke(1.0, 0.3, 52.0, 0.9),
        Stroke(1.3, 0.28, 55.0, 0.9),  # ends 20 ms before the next note: it goes on to it
        Stroke(1.6, 0.3, 57.0, 0.9),
        Stroke(2.5, 0.3, 59.0, 0.9),
    ]
    notes = sfzguitar.notes(strokes, 0, TABLE)
    moment = 1.0 / RATE
    assert notes[0].end == pytest.approx(notes[1].send - moment)
    assert notes[1].end == pytest.approx(notes[2].send - moment)
    assert notes[2].end == pytest.approx(1.9)
    assert notes[3].end == pytest.approx(2.8)


def test_a_long_note_rings_on_over_the_next_note() -> None:
    strokes = [Stroke(1.0, 2.0, 52.0, 0.7), Stroke(1.5, 0.4, 59.0, 0.7)]
    notes = sfzguitar.notes(strokes, 0, TABLE)
    assert notes[0].end == pytest.approx(3.0)


def test_the_strings_of_a_chord_start_one_after_the_other() -> None:
    chord = [Stroke(1.0, 0.5, pitch, 0.9) for pitch in (30.0, 37.0, 42.0)]
    again = [Stroke(1.1, 0.5, pitch, 0.9) for pitch in (30.0, 37.0, 42.0)]
    notes = sfzguitar.notes(chord + again, 0, TABLE)
    down, up = notes[:3], notes[3:]
    # A down stroke goes from the lowest string to the highest, an up stroke back.
    assert [note.key for note in down] == [30, 37, 42]
    assert [note.key for note in up] == [42, 37, 30]
    assert {note.switch for note in down} == {SUS_DOWN}
    assert {note.switch for note in up} == {SUS_UP}
    assert np.diff([note.start for note in down]) == pytest.approx([sfzguitar.STRUM] * 2)
    # Each string stops before its key goes down again.
    for note in down:
        same = next(later for later in up if later.key == note.key)
        assert note.end < same.send


def test_the_ways_of_playing() -> None:
    strokes = [
        Stroke(1.0, 0.2, 64.0, 0.9),
        Stroke(1.2, 0.2, 66.0, 0.9, hammer=True),  # the pitch goes up: a hammer-on
        Stroke(1.4, 0.2, 62.0, 0.9, hammer=True),  # the pitch goes down: a pull-off
        Stroke(2.0, 0.05, 40.0, 0.9, mute=True, dead=True),
        Stroke(2.5, 0.2, 80.0, 0.9, mute=True),  # no muted recording so high: an open note
        Stroke(3.0, 0.4, 60.0, 0.9, slide_from=58.0),
    ]
    notes = sfzguitar.notes(strokes, 0, TABLE)
    assert [note.switch for note in notes] == [
        SUS_DOWN,
        HAMMER_ON,
        PULL_OFF,
        DEAD_DOWN,
        SUS_DOWN,
        SLIDE_IN,
    ]
    assert notes[5].slide == 2
    # A note before a note that the left hand starts goes on to it.
    assert notes[0].end == pytest.approx(notes[1].send - 1.0 / RATE)


def test_the_messages_of_a_note() -> None:
    strokes = [Stroke(1.0, 0.1, 30.0, 0.9, mute=True), Stroke(1.1, 0.1, 30.0, 0.9, mute=True)]
    messages = sorted(
        sfzguitar.messages(strokes, 0, TABLE), key=lambda item: (item.sample, item.order)
    )
    words = [(message.kind, message.first) for message in messages]
    # The key switch is before each message of a note, and the first note stops before
    # the key goes down again.
    assert words == [
        ("note_on", MUTE_DOWN), ("note_off", MUTE_DOWN), ("note_on", 30),
        ("note_on", MUTE_DOWN), ("note_off", MUTE_DOWN), ("note_off", 30),
        ("note_on", MUTE_UP), ("note_off", MUTE_UP), ("note_on", 30),
        ("note_on", MUTE_UP), ("note_off", MUTE_UP), ("note_off", 30),
    ]  # fmt: skip
    assert messages[2].sample == int(round((1.0 - LATE) * RATE))
    assert messages[2].second == 127


def test_two_notes_that_stop_at_the_same_moment_keep_their_key_switches() -> None:
    strokes = [Stroke(1.0, 0.5, 40.0, 0.9, mute=True), Stroke(1.3, 0.2, 64.0, 0.9)]
    messages = sorted(
        sfzguitar.messages(strokes, 0, TABLE), key=lambda item: (item.sample, item.order)
    )
    ends = [index for index, message in enumerate(messages) if message.kind == "note_off"
            and message.first in (40, 64)]  # fmt: skip
    for index in ends:
        switch = MUTE_DOWN if messages[index].first == 40 else SUS_DOWN
        assert (messages[index - 2].kind, messages[index - 2].first) == ("note_on", switch)
        assert (messages[index - 1].kind, messages[index - 1].first) == ("note_off", switch)


def test_a_long_note_gets_a_vibrato_and_a_slide_gets_its_distance() -> None:
    strokes = [
        Stroke(1.0, 1.5, 64.0, 0.9, vibrato=30.0),
        Stroke(3.0, 0.5, 60.0, 0.9, slide_from=57.0),
    ]
    messages = sfzguitar.messages(strokes, 0, TABLE)
    depths = [(message.sample / RATE, message.second) for message in messages
              if message.kind == "cc" and message.first == VIBRATO_DEPTH]  # fmt: skip
    depths.sort()
    # The vibrato starts after the start of the note, grows, and stops with the note.
    assert depths[0][0] > 1.0 + sfzguitar.VIBRATO_START
    assert max(value for _time, value in depths) == round(127 * 30.0 / 100.0)
    assert depths[-1][1] == 0
    assert depths[-1][0] == pytest.approx(2.5, abs=0.01)
    slides = [message.second for message in messages
              if message.kind == "cc" and message.first == SLIDE_IN_INTERVAL]  # fmt: skip
    # Three semitones: the third range of the controller (from 32 to 47).
    assert len(slides) == 1 and 32 <= slides[0] <= 47


def test_the_pitch_wheel_follows_a_slide_between_notes_and_comes_back() -> None:
    strokes = [
        Stroke(1.0, 1.0, 50.0, 0.9, bend=(0.0, 0.0, -0.8, -2.0)),
        Stroke(2.5, 0.3, 48.0, 0.9),
    ]
    messages = sfzguitar.messages(strokes, 0, TABLE)
    wheel = sorted((message.sample, message.first) for message in messages
                   if message.kind == "pitch_wheel")  # fmt: skip
    values = [value for _sample, value in wheel]
    assert min(values) < -7000
    assert values[-1] == 0
    assert wheel[-1][0] == pytest.approx(2.0 * RATE, abs=0.01 * RATE)


@needs_sampler
def test_the_sampler_plays_a_note_near_its_written_time_and_two_different_guitars() -> None:
    strokes = [Stroke(0.5 + 0.5 * number, 0.3, 45.0 + number, 0.9) for number in range(4)]
    sound = sfzguitar.play(sfzguitar._new(), sfzguitar.messages(strokes, 0, TABLE), 3.0)
    assert sound.shape == (3 * RATE, 2)
    for stroke in strokes:
        first = int((stroke.start - 0.1) * RATE)
        part = sound[first : first + int(0.3 * RATE), 0]
        # With the table of the test (35 ms for each key) the note is not exactly at
        # its time: the real time from a key to its sound is from 29 to 36 ms here.
        assert sfzguitar.onset(part[int(0.05 * RATE) :]) + 0.05 == pytest.approx(0.1, abs=0.02)
    # The two channels are two recordings.
    left, right = sound[:, 0], sound[:, 1]
    assert float(np.sqrt(np.mean(left**2))) > 1e-3
    assert abs(float(np.corrcoef(left, right)[0, 1])) < 0.6


@needs_sampler
def test_a_soft_stroke_is_softer_and_duller_and_a_muted_note_is_shorter() -> None:
    def note(level: float, mute: bool = False) -> np.ndarray:
        strokes = [Stroke(0.3, 0.8, 47.0, level, mute=mute)]
        sampler = sfzguitar._new()
        return sfzguitar.play(sampler, sfzguitar.messages(strokes, 0, TABLE), 1.5)[:, 0]

    def bright(sound: np.ndarray) -> float:
        spectrum = np.abs(np.fft.rfft(sound)) ** 2
        frequencies = np.fft.rfftfreq(len(sound), 1.0 / RATE)
        return float(spectrum[frequencies > 2000.0].sum() / spectrum.sum())

    full, soft, muted = note(1.0), note(0.2), note(1.0, mute=True)
    assert float(np.sqrt(np.mean(soft**2))) < 0.6 * float(np.sqrt(np.mean(full**2)))
    assert bright(soft) < bright(full)
    late = slice(int(0.8 * RATE), int(1.0 * RATE))
    assert float(np.sqrt(np.mean(muted[late] ** 2))) < 0.3 * float(
        np.sqrt(np.mean(full[late] ** 2))
    )
