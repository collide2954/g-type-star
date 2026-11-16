"""Tests for the mixer."""

import numpy as np

from gtypestar.audio import console, dsp
from gtypestar.work import mix as work_mix


def stems() -> dict[str, np.ndarray]:
    random = np.random.default_rng(5)
    length = dsp.RATE
    names = ["drums.kick", "drums.cymbals", "bass", "gtr", "keys", "tsax", "lead", "tape"]
    return {name: random.normal(0.0, 0.05, (length, 2)).astype(np.float32) for name in names}


def test_the_exported_stems_add_up_to_the_mix():
    parts: dict[str, np.ndarray] = {}
    gains = {"drums": -3.0, "bass": 1.0}
    total, _gains = console.mix(stems(), work_mix.settings(), None, gains, parts)
    assert set(parts) == {"drums", "bass", "guitar", "keys", "saxophone", "synthesizers",
                          "recorded-sounds", "reverb"}  # fmt: skip
    assert np.allclose(sum(parts.values()), total, atol=1e-4)


def test_the_cymbal_microphones_are_in_the_drum_group():
    groups, _sends = console.group_buses(stems(), work_mix.settings(), None)
    assert set(groups) == {"drums", "bass", "music", "space"}
    only_cymbals = {"drums.cymbals": stems()["drums.cymbals"]}
    groups, _sends = console.group_buses(only_cymbals, work_mix.settings(), None)
    assert np.any(groups["drums"])


def test_export_names():
    assert console.export_name("gtr") == "guitar"
    assert console.export_name("pad.rh") == "synthesizers"
    assert console.export_name("chip") == "synthesizers"
