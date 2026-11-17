"""Play the sound of a real amplifier: models of the Neural Amp Modeler project (NAM).

A NAM model is a small neural network (a "WaveNet") that someone trained
with recordings of a real guitar amplifier: the test signal that went into
the amplifier, and the sound that came out of it (with or without the
loudspeaker cabinet and the microphone). The network then does to any
guitar signal what that amplifier did. A model file (`.nam`) is a text file
with numbers; it has no program code.

This module reads the standard WaveNet models and runs them with NumPy. It
does the same calculation as the reference code of the project
(https://github.com/sdatkinson/neural-amp-modeler, `nam/models/wavenet.py`):

- The network has some groups of layers. Each layer is a convolution with
  three taps that are `dilation` samples apart, then the function tanh.
- The input signal goes into each layer again (the "condition").
- The sum of the outputs of all layers, through one last small layer, is
  the output signal.

The models work at 48 000 samples in a second: the rate of the project.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

RATE = 48000
BLOCK = 96000  # samples that one step calculates (memory: about 30 MB for each step)


@dataclass
class _Layer:
    dilation: int
    taps: np.ndarray  # (kernel, channels out, channels in)
    bias: np.ndarray
    mixer: np.ndarray  # (channels, condition size)
    one: np.ndarray  # (channels, channels)
    one_bias: np.ndarray


@dataclass
class _Group:
    rechannel: np.ndarray  # (channels, input size)
    layers: list[_Layer]
    head: np.ndarray  # (head size, channels)
    head_bias: np.ndarray | None
    reach: int  # samples of the past that the group needs


class Model:
    """One amplifier model."""

    def __init__(self, path: Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("architecture") != "WaveNet":
            raise ValueError(f"{path}: only WaveNet models are supported")
        rate = data.get("sample_rate") or RATE
        if int(rate) != RATE:
            raise ValueError(f"{path}: the model is for {rate} samples in a second")
        weights = np.asarray(data["weights"], dtype=np.float32)
        place = 0

        def take(*shape: int) -> np.ndarray:
            nonlocal place
            size = int(np.prod(shape))
            block = weights[place : place + size].reshape(shape)
            place += size
            return block

        config = data["config"]
        if config.get("head") is not None:
            raise ValueError(f"{path}: a model with a head network is not supported")
        self.groups: list[_Group] = []
        for group in config["layers"]:
            channels, kernel = group["channels"], group["kernel_size"]
            if group["activation"] != "Tanh" or group["gated"]:
                raise ValueError(f"{path}: only layers with tanh and no gate are supported")
            rechannel = take(channels, group["input_size"], 1)[:, :, 0]
            layers = []
            for dilation in group["dilations"]:
                # The file has each convolution as (out, in, tap), then its bias.
                taps = np.ascontiguousarray(take(channels, channels, kernel).transpose(2, 0, 1))
                bias = take(channels)
                mixer = take(channels, group["condition_size"], 1)[:, :, 0]
                one = take(channels, channels, 1)[:, :, 0]
                one_bias = take(channels)
                layers.append(_Layer(int(dilation), taps, bias, mixer, one, one_bias))
            head = take(group["head_size"], channels, 1)[:, :, 0]
            head_bias = take(group["head_size"]) if group["head_bias"] else None
            reach = sum(layer.dilation * (kernel - 1) for layer in layers)
            self.groups.append(_Group(rechannel, layers, head, head_bias, reach))
        self.head_scale = float(take(1)[0])
        if place != len(weights):
            raise ValueError(f"{path}: {len(weights) - place} numbers of the file are not used")
        self.reach = sum(group.reach for group in self.groups)

    def _forward(self, signal: np.ndarray) -> np.ndarray:
        """Return the output for a piece of signal. The result is `reach` samples shorter."""
        condition = signal[None, :]
        layer_input = condition
        head: np.ndarray | None = None
        for group in self.groups:
            length = layer_input.shape[1] - group.reach
            state = group.rechannel @ layer_input
            for layer in group.layers:
                step = layer.dilation
                count = state.shape[1] - (len(layer.taps) - 1) * step
                total = layer.mixer @ condition[:, -count:] + layer.bias[:, None]
                for index, tap in enumerate(layer.taps):
                    total += tap @ state[:, index * step : index * step + count]
                active = np.tanh(total)
                state = state[:, -count:] + layer.one @ active + layer.one_bias[:, None]
                term = active[:, -length:]
                head = term if head is None else head[:, -length:] + term
            assert head is not None
            head = group.head @ head
            if group.head_bias is not None:
                head = head + group.head_bias[:, None]
            layer_input = state
        assert head is not None
        return self.head_scale * head[0]

    def play(self, signal: np.ndarray) -> np.ndarray:
        """Send a signal with one channel through the amplifier. The length stays."""
        dry = np.concatenate([np.zeros(self.reach, dtype=np.float32), signal.astype(np.float32)])
        out = np.empty(len(signal), dtype=np.float32)
        for start in range(0, len(signal), BLOCK):
            piece = dry[start : start + BLOCK + self.reach]
            result = self._forward(piece)
            out[start : start + len(result)] = result
        return out


@functools.lru_cache(maxsize=8)
def load(path: str) -> Model:
    """Return a model. A model that was read stays in memory."""
    return Model(Path(path))
