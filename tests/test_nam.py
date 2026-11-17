"""Tests for the code that runs the amplifier models."""

import json

import numpy as np
import pytest

from gtypestar.audio import guitar, nam


def model_file(path, channels=(4, 2), dilations=(1, 2, 4)):
    """Write a small model with random numbers, in the format of the NAM project."""
    random = np.random.default_rng(3)
    layers = []
    count = 0
    inputs = 1
    for index, size in enumerate(channels):
        last = index == len(channels) - 1
        head = 1 if last else channels[index + 1]
        layers.append({
            "input_size": inputs, "condition_size": 1, "head_size": head, "channels": size,
            "kernel_size": 3, "dilations": list(dilations), "activation": "Tanh", "gated": False,
            "head_bias": last,
        })  # fmt: skip
        count += size * inputs  # the first small layer
        count += len(dilations) * (size * size * 3 + size + size + size * size + size)
        count += head * size + (head if last else 0)
        inputs = size
    weights = random.normal(0.0, 0.3, count).tolist() + [0.5]
    config = {"layers": layers, "head": None, "head_scale": 0.5}
    data = {"version": "0.5.0", "architecture": "WaveNet", "config": config, "weights": weights}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_the_model_uses_all_numbers_of_the_file(tmp_path):
    model = nam.Model(model_file(tmp_path / "small.nam"))
    assert model.reach == 2 * 2 * (1 + 2 + 4)
    signal = np.random.default_rng(1).normal(0.0, 0.1, 5000).astype(np.float32)
    out = model.play(signal)
    assert out.shape == signal.shape
    assert np.all(np.isfinite(out))


def test_the_result_does_not_change_with_the_size_of_the_steps(tmp_path, monkeypatch):
    model = nam.Model(model_file(tmp_path / "small.nam"))
    signal = np.random.default_rng(2).normal(0.0, 0.1, 3000).astype(np.float32)
    whole = model.play(signal)
    monkeypatch.setattr(nam, "BLOCK", 700)
    pieces = model.play(signal)
    assert np.allclose(whole, pieces, atol=1e-6)


def test_a_file_with_too_many_numbers_is_an_error(tmp_path):
    path = model_file(tmp_path / "small.nam")
    data = json.loads(path.read_text())
    data["weights"].append(1.0)
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        nam.Model(path)


@pytest.mark.skipif(not guitar.available(), reason="the guitar library is not on this computer")
def test_the_two_guitars_are_two_different_recordings():
    strokes = [guitar.Stroke(0.1 * n, 0.09, 30, 0.9, mute=True) for n in range(8)]
    left = guitar.direct(strokes, 1.5, 0, seed=1)
    right = guitar.direct(strokes, 1.5, 1, seed=1)
    assert float(np.max(np.abs(left))) > 0.1
    same = float(np.corrcoef(left, right)[0, 1])
    assert abs(same) < 0.9
    wet = guitar.amplify(left, "high gain")
    assert len(wet) == len(left) and np.all(np.isfinite(wet))
