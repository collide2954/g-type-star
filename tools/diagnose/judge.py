"""Compare some sounds of one instrument: which one is nearest to a real recording?

The writer of the code cannot hear. This script is a substitute for a
comparison of two or more candidates for one sound (a guitar, a drum kit).
The model CLAP (the same model as in `tools/listen.py`) changes each file
into a list of numbers. The script shows, for each file:

- how well it agrees with each pair of descriptions, as the difference
  "good description - bad description" (larger is better);
- with `--real FOLDER`: how near it is to real recordings of the instrument
  (the mean of the largest similarities to the windows of the files in
  that folder).

The pairs of descriptions are for an electric guitar with distortion, or
for a drum kit (`--drums`). The numbers are a rough guide: the ears of the
owner of the project are the test.

Usage (the analysis environment has the model):

    .cache/analysis-venv/bin/python tools/diagnose/judge.py A.flac B.flac [--drums] [--real FOLDER]
"""

from __future__ import annotations

import sys
from pathlib import Path

import librosa
import numpy as np
import torch
from transformers import ClapModel, ClapProcessor

MODEL = "laion/clap-htsat-unfused"
RATE = 48000
WINDOW, HOP = 10.0, 5.0
GUITAR = [
    ("real", "a real electric guitar played by a guitarist", "a fake guitar from a keyboard"),
    ("album", "the guitar sound of a professional metal album", "a cheap MIDI guitar sound"),
    ("amp", "an electric guitar through a loud tube amplifier", "a synthesizer"),
    ("tight", "tight heavy palm muted metal riff", "thin and fizzy guitar"),
    ("full", "a full and warm guitar tone", "a harsh and tinny guitar tone"),
]
DRUMS = [
    ("real", "a real drum kit played by a drummer", "a drum machine"),
    ("album", "the drum sound of a professional metal album", "cheap MIDI drums"),
    ("punch", "punchy powerful drums", "weak and thin drums"),
    ("room", "drums recorded in a good room", "dry lifeless drum samples"),
    ("fusion", "a jazz fusion drummer", "a programmed drum beat"),
]


def windows(path: Path) -> np.ndarray:
    audio, _rate = librosa.load(path, sr=RATE, mono=True)
    size, step = int(WINDOW * RATE), int(HOP * RATE)
    if len(audio) < size:
        audio = np.pad(audio, (0, size - len(audio)))
    parts = [audio[start : start + size] for start in range(0, len(audio) - size + 1, step)]
    return np.array([part for part in parts if np.sqrt(np.mean(part**2)) > 1e-4])


def embed(model, processor, parts: np.ndarray) -> np.ndarray:
    result = []
    for start in range(0, len(parts), 8):
        batch = list(parts[start : start + 8])
        inputs = processor(audio=batch, sampling_rate=RATE, return_tensors="pt")
        with torch.no_grad():
            vectors = model.get_audio_features(**inputs)
        result.append(torch.nn.functional.normalize(vectors, dim=-1).numpy())
    return np.concatenate(result)


def main() -> int:
    arguments = sys.argv[1:]
    pairs = GUITAR
    if "--drums" in arguments:
        arguments.remove("--drums")
        pairs = DRUMS
    real = None
    if "--real" in arguments:
        place = arguments.index("--real")
        real = Path(arguments[place + 1])
        del arguments[place : place + 2]
    torch.set_num_threads(4)
    model = ClapModel.from_pretrained(MODEL).eval()
    processor = ClapProcessor.from_pretrained(MODEL)
    texts = [text for _name, good, bad in pairs for text in (good, bad)]
    inputs = processor(text=texts, return_tensors="pt", padding=True)
    with torch.no_grad():
        words = torch.nn.functional.normalize(model.get_text_features(**inputs), dim=-1).numpy()
    reference = None
    if real is not None:
        files = sorted(path for path in real.iterdir()
                       if path.suffix.lower() in (".wav", ".flac", ".mp3", ".ogg"))  # fmt: skip
        reference = np.concatenate([embed(model, processor, windows(path)) for path in files])
        print(f"real recordings: {len(files)} files, {len(reference)} windows")
    names = "".join(f"{name:>8s}" for name, _good, _bad in pairs)
    print(f"{'file':34s}{names}{'   sum':>8s}" + ("    near real" if reference is not None else ""))
    for name in arguments:
        vectors = embed(model, processor, windows(Path(name)))
        scores = vectors @ words.T
        values = [100.0 * float(np.mean(scores[:, 2 * index] - scores[:, 2 * index + 1]))
                  for index in range(len(pairs))]  # fmt: skip
        row = "".join(f"{value:+8.1f}" for value in values) + f"{sum(values):+8.1f}"
        if reference is not None:
            row += f"{float((vectors @ reference.T).max(axis=1).mean()):13.3f}"
        print(f"{Path(name).stem[:33]:34s}{row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
