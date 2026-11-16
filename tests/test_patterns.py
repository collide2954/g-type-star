"""Tests for the rhythm patterns, the drum language, and the tools that change music text."""

from fractions import Fraction

import numpy as np
import pytest

from gtypestar.compose import patterns, tools
from gtypestar.notation import drums, music

CLAVE = (3, 3, 2, 3, 3)


def length(text: str) -> Fraction:
    return sum((music.length(element) for element in music.parse(text).children), Fraction(0))


def test_pitched_fills_the_bar():
    text = patterns.pitched(
        "a__a-- ---b__ a_c_ ---a__ b_____", CLAVE, {"a": "g,,", "b": "d,", "c": "f,"}
    )
    assert length(text) == 7  # 14 eighth notes


def test_pitched_tuplet_and_accent():
    text = patterns.pitched("Aaaaa a-a-a aaa aaaaa a-a--", CLAVE, {"a": "g,,"})
    assert length(text) == 7
    assert "\\tuplet 5/3" in text
    assert "->" in text


def test_pitched_hold_over_a_pulse_is_a_tie():
    text = patterns.pitched("a_____ ______ ____ ------ ------", CLAVE, {"a": "<g c' f'>"})
    assert "~" in text
    assert length(text) == 7


def test_pitched_needs_one_group_for_each_pulse():
    with pytest.raises(ValueError):
        patterns.pitched("a_____ ______", CLAVE, {"a": "g"})


def test_drum_steps_two_voices():
    text = drums.steps(
        "hh x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nbd x----- ------ x--- ------ ------", CLAVE
    )
    group = music.parse(text).children[0]
    assert isinstance(group, music.Group) and group.kind == "parallel"
    assert length(text) == 7


def test_drum_steps_unknown_row():
    with pytest.raises(ValueError):
        drums.steps("zz x-x-x- x-x-x- x-x- x-x-x- x-x-x-", CLAVE)


def test_division():
    assert drums.division(Fraction(3, 2), 6) == (Fraction(1, 4), 0)  # sixteenth notes
    assert drums.division(Fraction(3, 2), 5)[1] != 0  # five notes in a long pulse: a tuplet
    assert drums.division(Fraction(1), 3)[1] == 2  # a triplet


def test_groove_vary_is_the_same_for_the_same_seed():
    groove = patterns.Groove(
        "hh x-x-x- x-x-x- x-x- x-x-x- x-x-x-\nsn ------ o--g-- ---g ------ o----g\n"
        "bd x----x ------ x--- x--x-- ------",
        CLAVE,
    )
    first = groove.vary(np.random.default_rng(7)).text()
    second = groove.vary(np.random.default_rng(7)).text()
    assert first == second
    assert length(first) == 7
    # The first stroke of the kick drum stays: the bar keeps its start.
    assert groove.vary(np.random.default_rng(3), 3.0).rows["bd"][0][0] == "x"


def test_groove_fill_replaces_the_last_pulses():
    groove = patterns.Groove("hh x-x-x- x-x-x- x-x- x-x-x- x-x-x-", CLAVE)
    groove.fill(4, {"sn": ["oooooo"]})
    assert groove.rows["hh"][4] == "------"
    assert groove.rows["sn"][4] == "oooooo"


def test_transpose_and_octave():
    assert tools.tr("g'4 c''4", 2) == "a'4 d''4"
    assert tools.octave("g'4", -1) == "g4"


def test_true_ties_removes_a_tie_to_a_different_pitch():
    bars = ["c''2 d''2 ~", "des''2 r2"]
    assert tools.true_ties(bars) == ["c''2 d''2", "des''2 r2"]


def test_true_ties_keeps_a_real_tie():
    bars = ["c''2 d''2 ~", "d''2 r2", None]
    assert tools.true_ties(bars) == bars
