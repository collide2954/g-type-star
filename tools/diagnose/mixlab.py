"""Try the settings of the mix on some bars, fast.

The first run renders the stems of the bars and keeps them in
`.cache/mixlab`. Later runs read them: a change of `work/mix.py` or of
`audio/console.py` shows its result in some seconds. Delete the kept stems
when the music of the bars changes.

The script shows the level of each band group for each group of the mix
(drums, bass, music) against the separated stems of the reference tracks,
and for the mix before and after the master against the reference masters.

Usage:

    uv run python tools/diagnose/mixlab.py FIRST-LAST [--stems] [--fixed] [--write NAME]

`--fixed`: use the levels of the groups of the full render (from the reference
passage), not the levels that give these bars the balance of the references.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

from gtypestar.audio import console, dsp, glitch, render
from gtypestar.work import build

KEEP = Path(".cache/mixlab")
GROUPS = [("20-45", 20, 45), ("45-90", 45, 90), ("90-180", 90, 180), ("180-355", 180, 355),
          ("355-710", 355, 710), ("0.7-1.4k", 710, 1400), ("1.4-2.8k", 1400, 2800),
          ("2.8-5.6k", 2800, 5600), ("5.6-11k", 5600, 11200), ("11-20k", 11200, 20000)]  # fmt: skip
# The separated stems of the six reference tracks (mean; "music" is the stem "other"),
# and their masters: the level of each band group relative to the total (dB).
REFERENCE = {
    "drums": [-9.2, -3.3, -5.7, -10.9, -18.6, -22.4, -19.6, -18.0, -19.2, -30.6],
    "bass": [-10.2, -2.7, -6.0, -11.5, -18.6, -25.6, -30.8, -42.1, -59.6, -67.7],
    "music": [-33.8, -28.8, -14.2, -6.2, -5.1, -6.7, -9.0, -13.0, -24.0, -35.2],
    "master": [-10.8, -4.5, -6.8, -9.1, -10.5, -12.5, -14.2, -16.4, -21.1, -32.2],
}
# The side signal of the reference masters relative to their mid signal, in each band (dB).
REFERENCE_SIDE = [-30.4, -20.5, -17.5, -6.9, -3.6, -3.1, -3.4, -3.6, -2.0, -0.6]


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


def side_bands(sound: np.ndarray) -> np.ndarray:
    """Return the level of the side signal relative to the mid signal in each band group (dB)."""
    mid = 0.5 * (sound[:, 0] + sound[:, 1]).astype(np.float64)
    side = 0.5 * (sound[:, 0] - sound[:, 1]).astype(np.float64)
    frequencies, mid_power = signal.welch(mid, fs=dsp.RATE, nperseg=8192)
    _f, side_power = signal.welch(side, fs=dsp.RATE, nperseg=8192)
    result = []
    for _name, low, high in GROUPS:
        inside = (frequencies >= low) & (frequencies < high)
        result.append(10.0 * np.log10((side_power[inside].sum() + 1e-20) /
                                      (mid_power[inside].sum() + 1e-20)))  # fmt: skip
    return np.array(result)


def row(name: str, levels: np.ndarray, side: float | None = None) -> str:
    text = f"{name:16s}" + "".join(f"{value:9.1f}" for value in levels)
    return text if side is None else text + f"{side:9.1f}"


def relative(levels: np.ndarray) -> np.ndarray:
    return levels - 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))


def load(work, bars: tuple[int, int]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Return the stems and the kick times of the bars, from the kept file if there is one."""
    path = KEEP / f"stems-{bars[0]}-{bars[1]}.npz"
    if path.exists():
        kept = np.load(path)
        stems = {name: kept[name] for name in kept.files if name != "__kicks"}
        return stems, kept["__kicks"]
    stems, kicks, _seconds = render.render_stems(work, bars)
    begin, end = render.window(work, bars)
    offset = render.LEAD_SECONDS - begin if begin > 0 else 0.0
    stems = glitch.apply(work, stems, offset, begin, end)
    KEEP.mkdir(parents=True, exist_ok=True)
    np.savez(path, __kicks=kicks, **stems)
    return stems, kicks


def main() -> int:
    arguments = sys.argv[1:]
    first, _, last = arguments[0].partition("-")
    bars = (int(first), int(last))
    work = build()
    stems, kicks = load(work, bars)
    settings = work.extras.get("mix") or console.Mix()
    print(f"{'':16s}" + "".join(f"{name:>9s}" for name, _l, _h in GROUPS) + "     side")
    if "--stems" in arguments:
        rows = []
        for name, stem in stems.items():
            out = console.channel(stem, settings.strips.get(name, console.Strip()), kicks)
            rows.append((name, *bands(out)))
        for name, levels, side in sorted(rows, key=lambda item: -item[1].max()):
            print(row(name, levels, side))
    groups, _sends = console.group_buses(stems, settings, kicks)
    for name in ("drums", "bass", "music"):
        if not np.any(groups[name]):
            continue
        levels, side = bands(groups[name])
        print(row(name, relative(levels), side))
        print(row("  - reference", relative(levels) - np.array(REFERENCE[name])))
    fixed = render.reference_gains(work, True) if "--fixed" in arguments else None
    mixed, gains = console.mix(stems, settings, kicks, fixed)
    levels, side = bands(mixed)
    print(row("mix", relative(levels), side))
    print(row("  - reference", relative(levels) - np.array(REFERENCE["master"])))
    final, report = console.master(mixed.copy(), tone=True)
    levels, side = bands(final)
    print(row("master", relative(levels), side))
    print(row("  - reference", relative(levels) - np.array(REFERENCE["master"])))
    width = side_bands(final)
    print(row("side - mid", width))
    print(row("  - reference", width - np.array(REFERENCE_SIDE)))
    print(
        f"tone change {report.tone_change_db[0]:.1f} to {report.tone_change_db[1]:.1f} dB, "
        f"limiter drive {report.limiter_drive_db:.1f} dB, group gains "
        + ", ".join(f"{name} {value:+.1f}" for name, value in gains.items())
    )
    if "--write" in arguments:
        name = arguments[arguments.index("--write") + 1]
        target = Path("build/audio")
        target.mkdir(parents=True, exist_ok=True)
        soundfile.write(str(target / f"{name}.flac"), final, dsp.RATE, subtype="PCM_24")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(target / f"{name}.flac"),
             "-codec:a", "libmp3lame", "-q:a", "1", str(target / f"{name}.mp3")],
            check=True,
        )  # fmt: skip
        print(f"audio: {target / name}.mp3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
