"""Compare a render of the work with the reference recordings, with a model that "hears".

The composer of the code cannot hear audio. This script is a substitute: the
model CLAP (LAION) changes each 10 seconds of sound into a list of numbers
that describes how it sounds. The script reports:

- How near each part of the render is to the reference recordings (the
  largest cosine similarity to a window of a reference recording).
- A distance between the render and the references for the full length
  (the Fréchet distance of the two sets of windows; smaller is nearer).
- How well each part agrees with some descriptions in words, for example
  "a professional studio recording" against "a cheap MIDI demo".

The values are a rough guide. The judgement of the owner of the project is
the real test.

Usage:

    .cache/analysis-venv/bin/python tools/listen.py build/audio/g-type-star.flac [more files]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import librosa
import numpy as np
import torch
from scipy import linalg
from transformers import ClapModel, ClapProcessor

MODEL = "laion/larger_clap_music"
RATE = 48000
WINDOW, HOP = 10.0, 5.0
REFERENCE_DIR = Path(".cache/reference/audio")
CACHE = Path(".cache/reference/derived/clap-reference.npz")
PAIRS = [
    (
        "a professional studio recording of a jazz fusion band",
        "a cheap MIDI demo with fake instruments",
    ),
    ("a real drum kit played by a drummer", "a programmed drum machine with stiff timing"),
    ("a clear, punchy, well balanced mix", "a muddy, harsh, badly balanced mix"),
    ("real instruments", "synthetic computer-generated sounds"),
    ("an exciting groove with energy", "boring repetitive music"),
]
TAGS = ["tenor saxophone", "electric guitar with distortion", "electric bass guitar", "synthesizer lead",
        "electric piano", "string section", "brass section", "dubstep wobble bass", "8-bit chiptune",
        "radio voice", "ambient space sounds", "drum solo"]  # fmt: skip


def windows(path: Path) -> tuple[np.ndarray, list[float]]:
    audio, _rate = librosa.load(path, sr=RATE, mono=True)
    size, step = int(WINDOW * RATE), int(HOP * RATE)
    parts, times = [], []
    for start in range(0, max(1, len(audio) - size + 1), step):
        part = audio[start : start + size]
        if np.sqrt(np.mean(part**2)) > 1e-4:
            parts.append(part)
            times.append(start / RATE)
    return np.array(parts), times


def embed(model, processor, parts: np.ndarray) -> np.ndarray:
    result = []
    for start in range(0, len(parts), 8):
        batch = [part for part in parts[start : start + 8]]
        inputs = processor(audios=batch, sampling_rate=RATE, return_tensors="pt")
        with torch.no_grad():
            vectors = model.get_audio_features(**inputs)
        result.append(torch.nn.functional.normalize(vectors, dim=-1).numpy())
    return np.concatenate(result)


def frechet(first: np.ndarray, second: np.ndarray) -> float:
    mean_1, mean_2 = first.mean(axis=0), second.mean(axis=0)
    cov_1, cov_2 = np.cov(first, rowvar=False), np.cov(second, rowvar=False)
    root, _ = linalg.sqrtm(cov_1 @ cov_2, disp=False)
    return float(np.sum((mean_1 - mean_2) ** 2) + np.trace(cov_1 + cov_2 - 2.0 * root.real))


def main() -> int:
    torch.set_num_threads(4)
    model = ClapModel.from_pretrained(MODEL).eval()
    processor = ClapProcessor.from_pretrained(MODEL)
    if CACHE.exists():
        reference = np.load(CACHE)["vectors"]
    else:
        reference = np.concatenate(
            [
                embed(model, processor, windows(path)[0])
                for path in sorted(REFERENCE_DIR.glob("*.wav"))
            ]
        )
        np.savez_compressed(CACHE, vectors=reference)
    texts = [text for pair in PAIRS for text in pair] + TAGS
    inputs = processor(text=texts, return_tensors="pt", padding=True)
    with torch.no_grad():
        words = torch.nn.functional.normalize(model.get_text_features(**inputs), dim=-1).numpy()
    # The reference tracks against the descriptions: the values that a good render must reach.
    ref_scores = reference @ words.T
    print(
        "reference tracks: "
        + "  ".join(
            f"{PAIRS[i][0].split(' ')[1][:5]}:{100 * float(np.mean(ref_scores[:, 2 * i] - ref_scores[:, 2 * i + 1])):+.1f}"
            for i in range(len(PAIRS))
        )
    )
    for name in sys.argv[1:]:
        path = Path(name)
        parts, times = windows(path)
        vectors = embed(model, processor, parts)
        nearest = (vectors @ reference.T).max(axis=1)
        scores = vectors @ words.T
        report = {
            "file": name,
            "windows": len(times),
            "nearest_mean": round(float(nearest.mean()), 4),
            "frechet": round(frechet(vectors, reference), 4),
            "pairs": {
                PAIRS[i][0]: round(100 * float(np.mean(scores[:, 2 * i] - scores[:, 2 * i + 1])), 2)
                for i in range(len(PAIRS))
            },
        }
        print(json.dumps(report))
        print("time    near  " + " ".join(f"p{i}" for i in range(len(PAIRS))) + "   strongest tags")
        offset = 2 * len(PAIRS)
        for index in range(0, len(times), 3):
            chunk = slice(index, index + 3)
            pair_values = " ".join(
                f"{100 * float(np.mean(scores[chunk, 2 * i] - scores[chunk, 2 * i + 1])):+3.0f}"
                for i in range(len(PAIRS))
            )
            tag_scores = scores[chunk, offset:].mean(axis=0)
            top = np.argsort(-tag_scores)[:3]
            tags = ", ".join(f"{TAGS[t]} {100 * tag_scores[t]:.0f}" for t in top)
            minutes = int(times[index] // 60)
            print(
                f"{minutes}:{times[index] % 60:04.1f}  {float(nearest[chunk].mean()):.3f} {pair_values}   {tags}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
