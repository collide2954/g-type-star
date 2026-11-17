"""Compare the two players of the guitar on some bars, before the amplifier.

The player of `guitar.py` and the program of the library in a sampler
(`sfzguitar.py`) get the same notes. For each player and each of the two
guitars, the script shows for the direct signal of the pickup:

- the level and the largest value (the amplifier models need the same
  level from the two players);
- the level in frequency bands;
- the times of the strokes against the written times: the mean and the
  spread in milliseconds. (The stroke is where the level of the high
  frequencies goes up fastest, near the written time.)

Usage:

    uv run python tools/diagnose/guitar_players.py FIRST-LAST TONE

TONE is the tone of the notes that are played ("high gain", "crunch",
"lead", "clean").
"""

from __future__ import annotations

import sys

import numpy as np
from scipy import signal

from gtypestar.audio import band, dsp, guitar, render, sfzguitar
from gtypestar.work import build

BANDS = [(60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000),
         (4000, 6000), (6000, 9000), (9000, 14000)]  # fmt: skip
FRAME = 0.001  # seconds


def spectrum(sound: np.ndarray) -> list[float]:
    spec = np.abs(np.fft.rfft(sound * np.hanning(len(sound)))) ** 2
    freqs = np.fft.rfftfreq(len(sound), 1 / dsp.RATE)
    total = spec[(freqs >= 60) & (freqs < 14000)].sum()
    return [10 * np.log10(spec[(freqs >= low) & (freqs < high)].sum() / total + 1e-12)
            for low, high in BANDS]  # fmt: skip


def stroke_times(sound: np.ndarray, starts: list[float]) -> np.ndarray:
    """Return, for each written start, the time of the stroke minus the written time."""
    high = signal.sosfilt(dsp.highpass(1500.0, 2), sound.astype(np.float64))
    size = int(FRAME * dsp.RATE)
    frames = np.abs(high[: len(high) // size * size]).reshape(-1, size).mean(axis=1)
    level = np.convolve(frames, np.ones(3) / 3.0, mode="same")
    rise = np.diff(level, prepend=level[0])
    result = []
    for start in starts:
        first = int((start - 0.04) / FRAME)
        last = int((start + 0.06) / FRAME)
        if first < 0 or last >= len(rise):
            continue
        result.append((first + int(np.argmax(rise[first:last]))) * FRAME - start)
    return np.array(result)


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    tone = sys.argv[2]
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = [event for event in render._inside(render.player_events(work, "gtr"), begin, end)
              if (event.note.get("tone") or "clean") == tone]  # fmt: skip
    seconds = end - begin + render.LEAD_SECONDS + 3.0
    print(f"bars {first} to {last}: {len(events)} notes with the tone {tone!r}")
    names = "".join(f"{low:>7d}" for low, _high in BANDS)
    print(f"{'player, guitar':22s}{'level':>8s}{'largest':>9s}{names}   stroke time: mean, spread")
    players = [("plain", guitar)]
    if sfzguitar.available():
        players.append(("program", sfzguitar))
    for name, player in players:
        for side, seed in ((0, 11), (1, 23)):
            strokes = band._strokes(events, seed if player is guitar else 0)
            dry = player.direct(strokes, seconds, side, seed)
            played = dry[np.abs(dry) > 1e-5]
            level = 10 * np.log10(float(np.mean(played**2)) + 1e-12)
            largest = 20 * np.log10(float(np.max(np.abs(dry))) + 1e-12)
            starts = sorted({round(stroke.start, 3) for stroke in strokes})
            times = 1000.0 * stroke_times(dry, starts)
            bands = "".join(f"{value:7.1f}" for value in spectrum(dry))
            print(f"{name + ', ' + str(side):22s}{level:8.1f}{largest:9.1f}{bands}"
                  f"   {times.mean():+6.1f} ms, {times.std():4.1f} ms")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
