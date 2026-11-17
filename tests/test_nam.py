"""Tests for the code that runs the amplifier models."""

import json

import numpy as np
import pytest

from gtypestar.audio import guitar, nam

RATE = guitar.RATE


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


@pytest.mark.skipif(not guitar.available(), reason="the guitar library is not on this computer")
def test_the_gap_between_two_muted_notes_has_the_sound_of_the_hand():
    # Two short muted notes with a rest of 0.4 seconds between them.
    strokes = [guitar.Stroke(start, 0.1, 35, 0.9, mute=True) for start in (0.1, 0.6)]
    dry = guitar.direct(strokes, 1.5, 0, seed=1)

    def level(start: float, end: float) -> float:
        part = dry[int(start * RATE) : int(end * RATE)]
        return 10.0 * np.log10(float(np.mean(part.astype(np.float64) ** 2)) + 1e-12)

    note, gap = level(0.1, 0.2), level(0.24, 0.34)
    # The release sound is there, and it is much softer than the note.
    assert note - 45.0 < gap < note - 8.0
    # The noise of the pick comes before the string.
    assert level(0.09, 0.1) > -80.0


@pytest.mark.skipif(not guitar.available(), reason="the guitar library is not on this computer")
def test_a_row_of_strokes_on_one_note_has_many_different_recordings():
    strokes = [guitar.Stroke(0.1 + 0.3 * n, 0.25, 40, 0.9, mute=True) for n in range(12)]
    dry = guitar.direct(strokes, 4.5, 0, seed=3)
    # Each second stroke (the down strokes): the first 30 ms after the pick noise.
    starts = [dry[int((0.1 + 0.3 * n + 0.004) * RATE) :][: int(0.03 * RATE)] for n in range(12)]
    different = set()
    for piece in starts:
        different.add(tuple(np.round(piece[::48] / (np.max(np.abs(piece)) + 1e-9), 1)))
    assert len(different) >= 8
    # No recording comes two times one after the other.
    for first, second in zip(starts, starts[1:], strict=False):
        assert abs(float(np.corrcoef(first, second)[0, 1])) < 0.999


def test_a_cabinet_response_keeps_the_level_of_the_middle(tmp_path, monkeypatch):
    import soundfile

    # A response with a loud impulse and a soft echo: a comb filter.
    response = np.zeros(4800, dtype=np.float32)
    response[100] = 0.25
    response[148] = 0.1
    soundfile.write(str(tmp_path / "cab.wav"), response, RATE, subtype="FLOAT")
    monkeypatch.setattr(guitar, "CABINETS_DIR", tmp_path)
    guitar.cabinet.cache_clear()
    loaded = guitar.cabinet("cab.wav")
    # The response starts at its first sound, and the middle band has the level 0 dB.
    assert int(np.argmax(np.abs(loaded))) == 0
    spectrum = np.abs(np.fft.rfft(loaded, 1 << 15)) ** 2
    frequencies = np.fft.rfftfreq(1 << 15, 1.0 / RATE)
    middle = float(np.mean(spectrum[(frequencies >= 300.0) & (frequencies <= 3000.0)]))
    assert abs(10.0 * np.log10(middle)) < 0.01
    guitar.cabinet.cache_clear()
