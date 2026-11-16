"""Divide each reference recording into stems (drums, bass, other, vocals).

This script needs the analysis environment (see `tools/extract/README.md`):
PyTorch and Demucs. It reads the recordings of the owner in
`.cache/reference/audio` and writes the stems into `.cache/reference/stems`.
The stems are for measurement only. They do not go into the repository.

Usage:

    .cache/analysis-venv/bin/python -I tools/extract/separate.py [--model htdemucs] [--threads 6]
    .cache/analysis-venv/bin/python -I tools/extract/separate.py --file build/audio/render.flac
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import soundfile
import torch
from demucs.apply import apply_model
from demucs.pretrained import get_model

AUDIO_DIR = Path(".cache/reference/audio")
STEMS_DIR = Path(".cache/reference/stems")


def separate(path: Path, model, name: str, output: Path) -> None:
    """Write one file for each source of the model."""
    target = output / name / path.stem
    if all((target / f"{source}.flac").exists() for source in model.sources):
        print(f"{path.stem}: the stems are there", flush=True)
        return
    audio, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
    if rate != model.samplerate:
        import librosa

        audio = librosa.resample(audio.T, orig_sr=rate, target_sr=model.samplerate).T
        rate = model.samplerate
    wave = torch.from_numpy(np.ascontiguousarray(audio.T))
    reference = wave.mean(0)
    mean, deviation = reference.mean(), reference.std()
    wave = (wave - mean) / deviation
    started = time.time()
    with torch.no_grad():
        sources = apply_model(model, wave[None], shifts=1, split=True, overlap=0.25)[0]
    sources = sources * deviation + mean
    target.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(model.sources):
        data = sources[index].numpy().T
        soundfile.write(str(target / f"{source}.flac"), np.clip(data, -1.0, 1.0), rate, "PCM_24")
    minutes = len(audio) / rate / 60.0
    print(
        f"{path.stem}: {minutes:.1f} minutes of music in {time.time() - started:.0f} s",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="htdemucs")
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("files", nargs="*", help="names of recordings (default: all)")
    parser.add_argument("--file", type=Path, help="one audio file, for example a render")
    parser.add_argument("--output", type=Path, default=Path(".cache/analysis/stems"),
                        help="the directory for the stems of --file")  # fmt: skip
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    model = get_model(args.model)
    model.eval()
    if args.file:
        # A render of the work: the same separation as the references, for a fair comparison.
        separate(args.file, model, args.model, args.output)
        return 0
    paths = sorted(AUDIO_DIR.glob("*.wav"))
    if args.files:
        paths = [path for path in paths if path.stem in args.files]
    if not paths:
        print(f"no recordings in {AUDIO_DIR}", file=sys.stderr)
        return 1
    for path in paths:
        separate(path, model, args.model, STEMS_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
