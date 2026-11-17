"""Compare the drum kits: the level of each group of microphones on bars of the work.

The mixer has fixed settings for the groups of the drum kit (kick, snare,
toms, cymbals, overheads, room). A different kit must give these groups
almost the same levels. The script plays the drum part of some bars with
each kit and shows the level and the peak of each group.

Usage:

    uv run python tools/diagnose/kit_levels.py FIRST-LAST [kit ...]

With `--write`, the script also writes the sum of the groups of each kit
(no mixer) to build/checks/kit-NAME.flac.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import dsp, kit, render
from gtypestar.work import build


def main() -> int:
    arguments = [value for value in sys.argv[1:] if value != "--write"]
    write = "--write" in sys.argv
    first, _, last = arguments[0].partition("-")
    names = arguments[1:] or list(kit.KITS)
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = render._inside(render.player_events(work, "drums"), begin, end)
    seconds = end - begin + render.LEAD_SECONDS + 3.0
    print(f"bars {first} to {last}: {len(events)} strokes, {end - begin:.1f} s")
    groups = list(kit.CROCELL.groups)
    print(f"{'kit':12s}" + "".join(f"{group:>18s}" for group in groups))
    for name in names:
        spec = kit.KITS[name]
        stems = kit.render(events, seconds, spec)
        line = f"{name:12s}"
        for group in groups:
            data = stems[group]
            level = 10.0 * np.log10(float(np.mean(data**2)) + 1e-12)
            peak = 20.0 * np.log10(float(np.max(np.abs(data))) + 1e-9)
            line += f"{level:9.1f} /{peak:6.1f}"
        print(line + "   (level / peak, dB)")
        if write:
            total = sum(stems.values())
            total = total * (dsp.db(-1.0) / max(float(np.max(np.abs(total))), 1e-9))
            target = Path("build/checks")
            target.mkdir(parents=True, exist_ok=True)
            soundfile.write(str(target / f"kit-{name}.flac"), total, dsp.RATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
