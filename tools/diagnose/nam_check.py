"""Compare the amplifier-model code of the project with the reference code of the NAM project.

Run it in the analysis environment (it needs the package `neural-amp-modeler`):

    .cache/analysis-venv/bin/python tools/diagnose/nam_check.py MODEL.nam
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch
from nam.models import init_from_nam


def own_module():
    path = Path(__file__).resolve().parents[2] / "src" / "gtypestar" / "audio" / "nam.py"
    spec = importlib.util.spec_from_file_location("own_nam", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["own_nam"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    path = Path(sys.argv[1])
    random = np.random.default_rng(1)
    time = np.arange(48000) / 48000.0
    signal = 0.3 * np.sin(2 * np.pi * 82.4 * time) * np.exp(-3.0 * time)
    signal += 0.1 * np.sin(2 * np.pi * 246.9 * time) + random.normal(0.0, 0.02, len(time))
    signal = signal.astype(np.float32)

    data = json.loads(path.read_text(encoding="utf-8"))
    # The new version of the reference code wants the last small layer of each group
    # as an object "head"; the model files of version 0.5 have two values for it.
    for group in data["config"]["layers"]:
        group.setdefault(
            "head",
            {"out_channels": group["head_size"], "kernel_size": 1, "bias": group["head_bias"]},
        )
    reference = init_from_nam(data)
    reference.eval()
    with torch.no_grad():
        wanted = reference(torch.from_numpy(signal)[None, :], pad_start=True)[0].numpy()
    found = own_module().Model(path).play(signal)
    count = min(len(wanted), len(found))
    error = float(np.max(np.abs(wanted[-count:] - found[-count:])))
    level = float(np.max(np.abs(wanted)))
    print(f"{path.name}: reference {len(wanted)} samples, own {len(found)} samples, "
          f"peak {level:.3f}, largest difference {error:.2e}")  # fmt: skip
    return 0 if error < 1e-3 * max(level, 1e-6) + 1e-5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
