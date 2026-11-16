"""Shared code of the extraction scripts: paths, loading, and the pulse grid.

The extraction scripts run in the analysis environment (see `README.md` in
this directory). They read the recordings of the owner and write derived
data (times of drum strokes, notes, chroma) into `.cache/reference/derived`.
Derived data that can show the music of a recording stay in the cache. Only
numbers that describe the style go into the repository.
"""

from __future__ import annotations

import json
from pathlib import Path

import librosa
import numpy as np
import soundfile
from scipy.signal import find_peaks

AUDIO_DIR = Path(".cache/reference/audio")
STEMS_DIR = Path(".cache/reference/stems/htdemucs")
DERIVED_DIR = Path(".cache/reference/derived")
RATE = 44100
HOP = 256  # 5.8 ms: the frame of the onset curves


def names(arguments: list[str]) -> list[str]:
    """Return the names of the recordings to work on (default: all)."""
    found = [path.stem for path in sorted(AUDIO_DIR.glob("*.wav"))]
    return [name for name in found if name in arguments] if arguments else found


def load(name: str, stem: str | None = None, *, mono: bool = True) -> np.ndarray:
    """Load a recording, or one stem of it. Mono: shape (n,). Stereo: shape (n, 2)."""
    path = AUDIO_DIR / f"{name}.wav" if stem is None else STEMS_DIR / name / f"{stem}.flac"
    audio, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
    if rate != RATE:
        raise SystemExit(f"{path}: the rate is {rate}, not {RATE}")
    return audio.mean(axis=1) if mono else audio


def derived(name: str, file: str) -> Path:
    path = DERIVED_DIR / name / file
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(name: str, file: str, data: object) -> Path:
    path = derived(name, file)
    path.write_text(json.dumps(data, indent=1))
    return path


def read_json(name: str, file: str) -> dict:
    return json.loads(derived(name, file).read_text())


def onset_curve(audio: np.ndarray, *, fmin: float = 30.0, fmax: float = 16000.0) -> np.ndarray:
    """Return the onset strength of a signal in a frequency band, one value for each frame."""
    mel = librosa.feature.melspectrogram(
        y=audio, sr=RATE, n_fft=1024, hop_length=HOP, n_mels=64, fmin=fmin, fmax=fmax, power=1.0
    )
    return librosa.onset.onset_strength(
        S=librosa.amplitude_to_db(mel, ref=np.max, top_db=70.0), sr=RATE, hop_length=HOP,
        aggregate=np.median,
    )  # fmt: skip


def comb_period(curve: np.ndarray, low: float = 0.070, high: float = 0.260) -> list[tuple]:
    """Find the periods of the fastest regular pulse (the tatum) of an onset curve.

    For each candidate period, the score is the autocorrelation at the
    multiples of the period minus the autocorrelation between the multiples.
    Return the best candidates as (period in seconds, score), best first.
    """
    frame = HOP / RATE
    longest = int(8.0 / frame)
    correlation = librosa.autocorrelate(curve - curve.mean(), max_size=longest)
    correlation = correlation / max(correlation[0], 1e-12)
    lags = np.arange(longest) * frame
    scores = []
    periods = np.arange(low, high, 0.00025)
    for period in periods:
        count = int(6.0 / period)
        on = np.interp(np.arange(1, count + 1) * period, lags, correlation)
        off = np.interp((np.arange(1, count + 1) - 0.5) * period, lags, correlation)
        scores.append(float(on.mean() - off.mean()))
    scores = np.array(scores)
    peaks, _ = find_peaks(scores, distance=8)
    best = sorted(peaks, key=lambda index: -scores[index])[:6]
    return [(float(periods[index]), float(scores[index])) for index in best]


def track_pulse(curve: np.ndarray, period: float, tightness: float = 300.0) -> np.ndarray:
    """Follow a pulse of a known period through an onset curve. Return the pulse times."""
    _tempo, frames = librosa.beat.beat_track(
        onset_envelope=curve, sr=RATE, hop_length=HOP, bpm=60.0 / period, tightness=tightness,
        trim=False,
    )  # fmt: skip
    return librosa.frames_to_time(frames, sr=RATE, hop_length=HOP)


def smooth_grid(times: np.ndarray, span: int = 16) -> np.ndarray:
    """Return a pulse grid with no local jitter: a local straight line through the pulse times.

    The tracker puts each pulse on a frame of the onset curve. This
    function fits a straight line to the pulses in a window of `span`
    pulses on each side, and takes the value of the line. The result
    follows slow changes of the tempo, but not the timing of single strokes.
    """
    index = np.arange(len(times), dtype=float)
    result = np.empty_like(times)
    for number in range(len(times)):
        first, last = max(0, number - span), min(len(times), number + span + 1)
        slope, offset = np.polyfit(index[first:last], times[first:last], 1)
        result[number] = slope * number + offset
    return result
