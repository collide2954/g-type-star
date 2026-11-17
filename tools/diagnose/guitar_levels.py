"""Show the level of the guitar stem of each tone, for each of the two players.

The mix has one fader for the guitar. If the program of the library in the
sampler (`sfzguitar.py`) makes a tone louder or softer than the player of
`guitar.py`, the balance of the mix changes. The script plays some bars of
each tone with the two players and shows the level of the stem from 250 Hz
to 6 kHz (the band of `front.py`) and its largest value.

Usage:

    uv run python tools/diagnose/guitar_levels.py [FIRST-LAST ...]

With no bars, the script takes eight bars from the first passage of each tone.
"""

from __future__ import annotations

import os
import sys

import numpy as np
from scipy import signal

from gtypestar.audio import band, dsp, render, sfzguitar
from gtypestar.work import build


def level(sound: np.ndarray) -> tuple[float, float]:
    mono = sound.mean(axis=1)
    sos = np.vstack([dsp.highpass(250.0, 2), dsp.lowpass(6000.0, 2)])
    middle = signal.sosfilt(sos, mono)
    loud = middle[np.abs(mono) > 1e-4]
    if len(loud) == 0:
        return -120.0, -120.0
    return (10 * np.log10(float(np.mean(loud**2)) + 1e-12),
            20 * np.log10(float(np.max(np.abs(sound))) + 1e-12))  # fmt: skip


def main() -> int:
    work = build()
    events = render.player_events(work, "gtr")
    spans = [tuple(int(word) for word in text.split("-")) for text in sys.argv[1:]]
    if not spans:
        seen: dict[str, int] = {}
        for event in sorted(events, key=lambda item: item.start):
            tone = event.note.get("tone") or "clean"
            if tone not in seen:
                seen[tone] = max(bar.number for bar in work.structure.bars
                                 if work.structure.seconds(bar.start) <= event.start)  # fmt: skip
        spans = [(bar, bar + 7) for bar in seen.values()]
    print(f"{'bars':>10s} {'tone':10s} {'notes':>6s}   plain: level, largest"
          "   program: level, largest   difference")  # fmt: skip
    for first, last in spans:
        begin, end = render.window(work, (first, last))
        inside = render._inside(events, begin, end)
        seconds = end - begin + render.LEAD_SECONDS + 3.0
        tones: dict[str, list] = {}
        for event in inside:
            tones.setdefault(event.note.get("tone") or "clean", []).append(event)
        for tone, group in tones.items():
            row = []
            for player in ("plain", "program"):
                os.environ["GTYPESTAR_PLAYER"] = player
                if player == "program" and not sfzguitar.available():
                    row.append((float("nan"), float("nan")))
                    continue
                row.append(level(band.render_guitar(group, seconds)))
            plain, program = row
            print(f"{first:>4d}-{last:<5d} {tone:10s} {len(group):6d}"
                  f"   {plain[0]:12.1f} {plain[1]:8.1f}   {program[0]:14.1f} {program[1]:8.1f}"
                  f"   {program[0] - plain[0]:+10.1f}")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
