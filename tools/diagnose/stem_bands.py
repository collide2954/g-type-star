"""Show the level of each stem in each band group, for some bars, after its channel strip.

The table shows which stems give the energy of a band, for example the band
above 11 kHz. The last rows are the mix and the master of the same bars.

Usage:

    uv run python tools/diagnose/stem_bands.py FIRST-LAST
"""

from __future__ import annotations

import sys

import numpy as np
from scipy import signal

from gtypestar.audio import console, dsp, render
from gtypestar.work import build

GROUPS = [("20-45", 20, 45), ("45-90", 45, 90), ("90-180", 90, 180), ("180-355", 180, 355),
          ("355-710", 355, 710), ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800),
          ("2.8-5.6k", 2800, 5600), ("5.6-11k", 5600, 11200), ("11-20k", 11200, 20000)]  # fmt: skip


# The separated stems of the reference tracks: the level of each band group relative to
# the stem (dB), mean of six tracks. "music" is the stem "other" of the separation.
REFERENCE = {
    "drums": [-9.2, -3.3, -5.7, -10.9, -18.6, -22.4, -19.6, -18.0, -19.2, -30.6],
    "bass": [-10.2, -2.7, -6.0, -11.5, -18.6, -25.6, -30.8, -42.1, -59.6, -67.7],
    "music": [-33.8, -28.8, -14.2, -6.2, -5.1, -6.7, -9.0, -13.0, -24.0, -35.2],
}


def bands(sound: np.ndarray) -> tuple[np.ndarray, float]:
    """Return the power of the mid signal in each band group (dB), and the side level (dB)."""
    mid = 0.5 * (sound[:, 0] + sound[:, 1]).astype(np.float64)
    side = 0.5 * (sound[:, 0] - sound[:, 1]).astype(np.float64)
    frequencies, power = signal.welch(mid, fs=dsp.RATE, nperseg=8192)
    step = frequencies[1] - frequencies[0]
    levels = [
        10.0 * np.log10(power[(frequencies >= low) & (frequencies < high)].sum() * step + 1e-20)
        for _name, low, high in GROUPS
    ]
    ratio = 10.0 * np.log10((np.mean(side**2) + 1e-20) / (np.mean(mid**2) + 1e-20))
    return np.array(levels), float(ratio)


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    bars = (int(first), int(last))
    work = build()
    stems, kicks, _seconds = render.render_stems(work, bars)
    settings = work.extras.get("mix") or console.Mix()
    print(f"{'stem':16s}" + "".join(f"{name:>9s}" for name, _l, _h in GROUPS) + "     side")
    rows = []
    for name, stem in stems.items():
        strip = settings.strips.get(name, console.Strip())
        out = console.channel(stem, strip, kicks)
        levels, side = bands(out)
        rows.append((name, levels, side))
    for name, levels, side in sorted(rows, key=lambda row: -row[1][-1]):
        print(f"{name:16s}" + "".join(f"{value:9.1f}" for value in levels) + f"{side:9.1f}")
    groups, _sends = console.group_buses(stems, settings, kicks)
    print("groups, each band relative to the total of the group; below: the separated stems")
    print("of the six reference tracks (mean), from tools/tone.py")
    for name in ("drums", "bass", "music"):
        levels, side = bands(groups[name])
        total = 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))
        print(f"{name:16s}" + "".join(f"{value:9.1f}" for value in levels - total) + f"{side:9.1f}")
        print(f"{'  reference':16s}" + "".join(f"{value:9.1f}" for value in REFERENCE[name]))
    mixed, gains = console.mix(stems, settings, kicks)
    levels, side = bands(mixed)
    print(f"{'mix':16s}" + "".join(f"{value:9.1f}" for value in levels) + f"{side:9.1f}")
    for tone in (False, True):
        final, report = console.master(mixed.copy(), tone=tone)
        levels, side = bands(final)
        name = "master+tone" if tone else "master"
        print(f"{name:16s}" + "".join(f"{value:9.1f}" for value in levels) + f"{side:9.1f}")
        print(f"   limiter drive {report.limiter_drive_db:.1f} dB, tone change "
              f"{report.tone_change_db[0]:.1f} to {report.tone_change_db[1]:.1f} dB")  # fmt: skip
    print("group gains:", {name: round(value, 1) for name, value in gains.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
