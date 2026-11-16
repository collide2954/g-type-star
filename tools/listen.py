"""Compare a render of the work with the reference recordings, with a model that "hears".

The writer of the code cannot hear audio. This script is a substitute: the
model CLAP (LAION) changes each 10 seconds of sound into a list of numbers
that describes how it sounds. The script reports:

- How near each part of the render is to the reference recordings: the
  largest cosine similarity to a window of a reference recording. For
  comparison, the same value for each reference recording against the
  other reference recordings (how near real tracks of this style are to
  each other).
- A distance between the render and the references for the full length
  (the Fréchet distance of the two sets of windows; smaller is nearer).
- How well each part agrees with some descriptions in words, for example
  "a professional studio recording" against "a cheap MIDI demo".

The values are a rough guide. The judgement of the owner of the project is
the real test.

The first version of this script used the checkpoint `laion/larger_clap_music`.
With the installed version of the library, that checkpoint gives almost the
same numbers for all sounds (white noise and a sine tone: similarity 0.95).
The checkpoint `laion/clap-htsat-unfused` separates them (0.35).

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

MODEL = "laion/clap-htsat-unfused"
RATE = 48000
WINDOW, HOP = 10.0, 5.0
REFERENCE_DIR = Path(".cache/reference/audio")
CACHE = Path(".cache/reference/derived/clap-unfused-reference.npz")
PAIRS = [
    ("studio", "a professional studio recording of a band", "a cheap MIDI demo"),
    ("drummer", "a real drum kit played by a drummer", "a drum machine"),
    ("mix", "a clear and punchy mix", "a muddy and harsh mix"),
    ("real", "real instruments played by musicians", "computer-generated music"),
    ("energy", "an exciting groove with energy", "boring repetitive music"),
    ("fusion", "jazz fusion", "electronic dance music"),
]
TAGS = ["tenor saxophone", "distorted electric guitar", "electric bass guitar", "synthesizer",
        "electric piano", "string section", "brass section", "dubstep bass", "chiptune",
        "a voice on the radio", "ambient noise", "drums"]  # fmt: skip


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
        inputs = processor(audio=batch, sampling_rate=RATE, return_tensors="pt")
        with torch.no_grad():
            vectors = model.get_audio_features(**inputs)
        result.append(torch.nn.functional.normalize(vectors, dim=-1).numpy())
    return np.concatenate(result)


def frechet(first: np.ndarray, second: np.ndarray) -> float:
    mean_1, mean_2 = first.mean(axis=0), second.mean(axis=0)
    cov_1, cov_2 = np.cov(first, rowvar=False), np.cov(second, rowvar=False)
    root, _ = linalg.sqrtm(cov_1 @ cov_2, disp=False)
    return float(np.sum((mean_1 - mean_2) ** 2) + np.trace(cov_1 + cov_2 - 2.0 * root.real))


def pair_scores(scores: np.ndarray) -> list[float]:
    """Return, for each pair of descriptions, the mean of (good description - bad description)."""
    return [
        100.0 * float(np.mean(scores[:, 2 * index] - scores[:, 2 * index + 1]))
        for index in range(len(PAIRS))
    ]


def summary(nearest: np.ndarray) -> str:
    return f"mean {nearest.mean():.3f}, lowest tenth {np.percentile(nearest, 10):.3f}"


def main() -> int:
    torch.set_num_threads(4)
    model = ClapModel.from_pretrained(MODEL).eval()
    processor = ClapProcessor.from_pretrained(MODEL)
    paths = sorted(REFERENCE_DIR.glob("*.wav"))
    if CACHE.exists():
        stored = np.load(CACHE)
        tracks = {name: stored[name] for name in stored.files}
    else:
        tracks = {path.stem: embed(model, processor, windows(path)[0]) for path in paths}
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(CACHE, **tracks)
    reference = np.concatenate(list(tracks.values()))
    texts = [text for _name, good, bad in PAIRS for text in (good, bad)] + TAGS
    inputs = processor(text=texts, return_tensors="pt", padding=True)
    with torch.no_grad():
        words = torch.nn.functional.normalize(model.get_text_features(**inputs), dim=-1).numpy()

    names = "  ".join(f"{name:>7s}" for name, _good, _bad in PAIRS)
    print(f"{'':28s} nearest (mean, lowest tenth)   Fréchet   {names}")
    for name, vectors in tracks.items():
        others = np.concatenate([other for key, other in tracks.items() if key != name])
        nearest = (vectors @ others.T).max(axis=1)
        values = "  ".join(f"{value:+7.1f}" for value in pair_scores(vectors @ words.T))
        print(
            f"reference {name:18s} {nearest.mean():.3f}  {np.percentile(nearest, 10):.3f}"
            f"            {frechet(vectors, others):7.3f}   {values}"
        )
    for name in sys.argv[1:]:
        path = Path(name)
        parts, times = windows(path)
        vectors = embed(model, processor, parts)
        nearest = (vectors @ reference.T).max(axis=1)
        scores = vectors @ words.T
        values = "  ".join(f"{value:+7.1f}" for value in pair_scores(scores))
        print(
            f"render    {path.stem:18s} {nearest.mean():.3f}  {np.percentile(nearest, 10):.3f}"
            f"            {frechet(vectors, reference):7.3f}   {values}"
        )
        report = {
            "file": name,
            "windows": len(times),
            "nearest_mean": round(float(nearest.mean()), 4),
            "nearest_low_tenth": round(float(np.percentile(nearest, 10)), 4),
            "frechet": round(frechet(vectors, reference), 4),
            "pairs": dict(
                zip([pair[0] for pair in PAIRS], np.round(pair_scores(scores), 2), strict=True)
            ),
        }
        print(json.dumps(report))
        print(f"time    near  {names}   strongest tags")
        offset = 2 * len(PAIRS)
        for index in range(0, len(times), 3):
            chunk = slice(index, index + 3)
            pair_values = "  ".join(f"{value:+7.1f}" for value in pair_scores(scores[chunk]))
            tag_scores = scores[chunk, offset:].mean(axis=0)
            top = np.argsort(-tag_scores)[:3]
            tags = ", ".join(f"{TAGS[t]} {100 * tag_scores[t]:.0f}" for t in top)
            minutes = int(times[index] // 60)
            print(
                f"{minutes}:{times[index] % 60:04.1f}  {float(nearest[chunk].mean()):.3f} "
                f"{pair_values}   {tags}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
