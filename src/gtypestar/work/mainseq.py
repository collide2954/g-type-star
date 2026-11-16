"""Part 3: the main sequence. The star burns hydrogen in a stable state.

This is the longest part. It has the theme, the bridge, the solos, a quiet
middle, and the return of the theme with a new division of the pulses.

Style profile: "Groove" (see research/tables/profiles.csv). Three speeds at
the same time: kick and snare far apart, a fast grid of sixteenth notes, and
a slow melody.
"""

from __future__ import annotations

from ..compose import chords, patterns
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

# Rhythms of the electric piano for one bar: the letter `a` is the chord.
COMPS = [
    "---a__ ------ a___ ---a__ ______",
    "a_____ ---a__ ---- a__-a_ ______",
    "---a__ ___--- -a__ ------ a_____",
    "a__--- ---a__ a_-- ---a__ ---a__",
    "---a__ ------ a___ ------ -a____",
    "a_____ ______ ---- ---a__ a__---",
]
# Bass figures for one bar. The letters are the notes of `material.bass_table`.
BASS = [
    "a__x-b ---c-e b_a_ a__x-c ---e_c",
    "a__x-b -x-c_e b_a_ a_-x-c b__c_e",
    "a__-xb ---c_e b_a_ a__x-c -x-e_c",
    "a__x-b ---c-e b-a_ a__c_e b_-c_h",
    "a__x-a -x-b_c b_a_ a__x-e ---c_b",
]
# Figures of the guitar: three notes of the chord (a, b, c) in sixteenth notes.
PICKS = [
    "abcabc abcabc abca bcabca bcabca",
    "a-ca-c abcabc a-c- bcabca b-ab--",
    "abc-bc a-cabc abca -cab-a bcabca",
    "ab-ab- abcabc -bca bcabca bca---",
]


def _bass(symbols: list[str], key: str, shapes: list[str] = BASS) -> list[str]:
    """Return one bar of bass for each chord. The figure changes from bar to bar."""
    source = m.random("bass", key)
    bars = []
    last = -1
    for symbol in symbols:
        choice = int(source.integers(0, len(shapes)))
        if choice == last:
            choice = (choice + 1) % len(shapes)
        last = choice
        bars.append(patterns.pitched(shapes[choice], m.CLAVE, m.bass_table(symbol)))
    return bars


def _keys(symbols: list[str], key: str, low: int = 55, high: int = 77) -> list[str]:
    """Return one bar of the electric piano for each chord."""
    source = m.random("keys", key)
    bars = []
    before = None
    for symbol in symbols:
        voicing = chords.voice(symbol, 4, low=low, high=high, before=before)
        before = voicing
        pattern = COMPS[int(source.integers(0, len(COMPS)))]
        bars.append(patterns.pitched(pattern, m.CLAVE, {"a": chords.names(voicing, symbol)}))
    return bars


def _picks(symbols: list[str], key: str) -> list[str]:
    """Return one bar of the guitar figure for each chord."""
    source = m.random("guitar", key)
    bars = []
    for symbol in symbols:
        notes = chords.voice(symbol, 3, low=62, high=81)
        table = {
            letter: chords.names((midi,), symbol) for letter, midi in zip("abc", notes, strict=True)
        }
        bars.append(patterns.pitched(PICKS[int(source.integers(0, len(PICKS)))], m.CLAVE, table))
    return bars


def write(work: Work) -> None:
    structure = work.structure

    # ------------------------------------------------- the theme, first time
    s = Bars(work, 16)
    structure.mark(s.bar(1), "C")
    symbols = m.LOOP_A * 4
    s.set("tsax", m.THEME + m.THEME_SECOND, r"\mf")
    s.set(
        "drums",
        m.drum_bars(m.MAIN, 16, "theme 1", crash=(1, 9), fills={8: "snare 1", 16: "toms 2"}),
        r"\f",
    )
    s.set("bass", _bass(symbols, "theme 1"), r"\f\fingers")
    s.set("keys.rh", _keys(symbols, "theme 1"), r"\mf")
    s.set("gtr", [None] * 8 + _picks(symbols[8:], "theme 1"), r"\mp\clean\pm")
    s.close()

    # ------------------------------------------------- the theme, second time
    s = Bars(work, 16)
    structure.mark(s.bar(1), "D")
    s.set("tsax", m.THEME_HIGH + m.THEME_CLOSE, r"\f")
    s.set(
        "drums",
        m.drum_bars(m.MAIN_OPEN, 16, "theme 2", amount=1.2, crash=(1, 5, 9, 13),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "kicks 2"}),
        r"\f",
    )  # fmt: skip
    s.set("bass", _bass(symbols, "theme 2"), r"\f")
    s.set("keys.rh", _keys(symbols, "theme 2"), r"\mf")
    s.set("gtr", _picks(symbols, "theme 2"), r"\mf\clean\pm")
    claps = drums.steps("ms  ------ c----- ---- ------ c-----", m.CLAVE)
    s.set("eperc", [claps] * 16, r"\mf")
    s.close()
