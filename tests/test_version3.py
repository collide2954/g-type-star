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


def test_a_line_moves_bar_by_bar_with_the_smallest_leaps_at_the_bar_lines():
    # Bar 2 has a G5, above the range: the whole bar goes one octave lower, and its
    # shape stays. Bar 1 has a low A-flat: it cannot go lower, and stays. Bar 3 has two
    # possible octaves: it takes the octave next to the end of bar 2.
    line = ["as,8 d'' e'' f''", "g''8 f'' e'' d''", "c''8 b' a' g'"]
    assert tools.fit_bars(line, 44, 77) == ["as,8 d'' e'' f''", "g'8 f' e' d'", "c'8 b a g"]
    # A line that is in the range stays as it is.
    assert tools.fit_bars(line[2:], 44, 77) == line[2:]
    # With no low note in bar 1, the three bars go down together: no leap at a bar line.
    line[0] = "c''8 d'' e'' f''"
    assert tools.fit_bars(line, 44, 77) == ["c'8 d' e' f'", "g'8 f' e' d'", "c'8 b a g"]


def test_a_bar_of_the_last_line_has_one_slur_on_each_pulse():
    from gtypestar.work import agb

    bar = agb.slurred(" ".join(["c'16"] + ["d'"] * 27))
    words = bar.split()
    starts = [index for index, word in enumerate(words) if word.endswith("(")]
    ends = [index for index, word in enumerate(words) if word.endswith(")")]
    assert starts == [0, 6, 12, 16, 22] and ends == [5, 11, 15, 21, 27]


def test_the_work_has_no_fast_line_without_slurs_and_no_chord_too_wide_for_a_hand():
    from gtypestar.work import build

    work = build()
    problems = [str(problem) for problem in check.check(work)]
    assert problems == []
    # The checks find the faults: a fast line with no slur (the first bars of the work
    # have 70 quarter notes in a minute: 16 notes in a quarter note are 18 in a second),
    # and a chord of two octaves in one hand.

    def notes(legato: bool) -> list[PerfNote]:
        return [
            PerfNote("tsax", "tenor saxophone", Fraction(number, 16), Fraction(1, 16), 60, 0.7,
                     0.7, legato=legato and number > 0)
            for number in range(40)
        ]  # fmt: skip

    assert len(check._tongue_problems(work, "tsax", notes(legato=False))) == 1
    assert check._tongue_problems(work, "tsax", notes(legato=True)) == []
    wide = [PerfNote("keys.rh", "electric piano", Fraction(0), Fraction(1), midi, 0.7, 0.7)
            for midi in (60, 84)]  # fmt: skip
    assert len(check._hand_problems(work, "keys.rh", wide)) == 1
    assert check._hand_problems(work, "keys.rh", wide[:1]) == []


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
