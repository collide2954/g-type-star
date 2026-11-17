"""Tests for the rules and the tools of the third version (see design/plan.md)."""

from fractions import Fraction

import numpy as np
import pytest

from gtypestar.audio import glitch, perc, tape
from gtypestar.compose import check, tools
from gtypestar.perform.events import PerfNote
from gtypestar.perform.feel import Event
from gtypestar.work import material as m

RATE = 48000


def test_a_line_stays_inside_a_range_note_by_note():
    # F-sharp 5 and G5 are above F5 (77): they go one octave lower; E5 stays.
    assert tools.within("e''8 fis'' g''", 44, 77) == "e''8 fis' g'"


def test_a_phrase_moves_as_one_piece_if_its_highest_note_is_too_high():
    assert tools.fit("c''4 g''4", 77) == "c'4 g'4"
    assert tools.fit("c''4 e''4", 77) == "c''4 e''4"
    # The second bar of a phrase moves with the first bar.
    assert tools.fit("c''4", 77, more=("c''4", "g''4")) == "c'4"


def test_the_kick_drum_has_the_low_notes_of_the_bass():
    figure = "a__x-b ---c-e b_a_ a__x-c ---e_c"
    bars = m.drum_bars(m.MAIN, 1, "test", amount=0.0, crash=(), kicks=[figure])
    kick = next(row for row in _rows(bars[0], m.MAIN) if row[0] == "bd")[1]
    # The first, third and fourth pulse come from the bass figure (letters a and b).
    assert kick[0] == "x----x" and kick[2] == "x-x-" and kick[3] == "x-----"
    # The second and the fifth pulse stay as in the groove.
    assert kick[1] == m.MAIN.rows["bd"][1] and kick[4] == m.MAIN.rows["bd"][4]


def _rows(text: str, groove) -> list[tuple[str, list[str]]]:
    """Make the same bar again as rows: the function under test returns music text."""
    source = m.random("drums", "test")
    bar = groove.vary(source, 0.0)
    figure = "a__x-b ---c-e b_a_ a__x-c ---e_c"
    for pulse, group in enumerate(figure.split()):
        if pulse in m.KICK_PULSES:
            bar.rows["bd"][pulse] = "".join("x" if char in "ab" else "-" for char in group)
    assert bar.text() == text
    return list(bar.rows.items())


def test_a_division_in_five_seven_or_eleven_is_found():
    assert check._division(Fraction(1, 4)) == 0
    assert check._division(Fraction(1, 6)) == 0
    assert check._division(Fraction(3, 20)) == 5
    assert check._division(Fraction(1, 7)) == 7
    assert check._division(Fraction(4, 11)) == 11


def test_noise_rings_on_the_given_notes():
    noise = np.random.default_rng(1).normal(0.0, 0.1, (2 * RATE, 2))
    rung = tape.ring(noise, (57,), mix=1.0)  # A3 = 220 Hz
    spectrum = np.abs(np.fft.rfft(rung[:, 0]))
    frequencies = np.fft.rfftfreq(len(rung), 1 / RATE)
    peak = float(frequencies[np.argmax(spectrum)])
    assert min(abs(peak - value) for value in (220.0, 440.0, 880.0, 1760.0)) < 6.0
    # The level stays.
    assert abs(float(np.std(rung)) / float(np.std(noise)) - 1.0) < 0.05


def test_a_held_moment_has_the_length_that_is_asked_for_and_fades():
    time = np.arange(RATE // 2) / RATE
    tone = 0.2 * np.sin(2 * np.pi * 330.0 * time)
    moment = np.stack([tone, tone], axis=1)
    held = glitch.freeze(moment, 3 * RATE, hold=0.5)
    assert held.shape == (3 * RATE, 2)
    middle = float(np.sqrt(np.mean(held[RATE : RATE + 4800] ** 2)))
    end = float(np.sqrt(np.mean(held[-2400:] ** 2)))
    assert middle > 0.05 and end < 0.1 * middle


@pytest.mark.skipif(not perc.available(), reason="the percussion samples are not on this computer")
def test_the_shaker_takes_two_kinds_of_stroke_in_turn():
    def stroke(start: float) -> Event:
        note = PerfNote("perc", "hand percussion", Fraction(0), Fraction(1), 82, 0.7, 0.7)
        return Event(note, start, 0.1, 0.7, 0.7)

    sound = perc.render([stroke(0.1), stroke(0.27), stroke(0.44), stroke(0.61)], 1.0)
    pieces = [sound[int(start * RATE) : int((start + 0.12) * RATE)] for start in (0.1, 0.27)]
    assert all(float(np.max(np.abs(piece))) > 0.01 for piece in pieces)
    # The move away and the move back are two different recordings.
    same = float(np.corrcoef(pieces[0][:, 0], pieces[1][:, 0])[0, 1])
    assert abs(same) < 0.9
