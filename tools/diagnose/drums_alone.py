"""Write the drums of some bars alone, as the mix has them, with one of the drum kits.

The file has the drum group only: the strokes of the drummer with the
microphones of the kit, after the channel strips and the group processing
of the mix (`work/mix.py`), with no other player and no master. It is for a
comparison of drum kits on the same bars.

Usage:

    uv run python tools/diagnose/drums_alone.py FIRST-LAST NAME [KIT]

KIT is the short name of a kit in `kit.KITS` (default: the kit of the work).
The result is build/audio/NAME.flac and build/audio/NAME.mp3.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import console, dsp, kit, render
from gtypestar.work import build


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    name = sys.argv[2]
    spec = kit.KITS[sys.argv[3]] if len(sys.argv) > 3 else kit.kit()
    work = build()
    begin, end = render.window(work, (int(first), int(last)))
    events = render._inside(render.player_events(work, "drums"), begin, end)
    seconds = end - begin + render.LEAD_SECONDS + 3.0
    stems = {f"drums.{group}": sound for group, sound in kit.render(events, seconds, spec).items()}
    kicks = np.array(sorted(event.start for event in events if int(event.midi) in (35, 36)))
    settings = work.extras.get("mix") or console.Mix()
    groups, _sends = console.group_buses(stems, settings, kicks)
    drums = groups["drums"]
    levels = {group: 10.0 * np.log10(float(np.mean(sound**2)) + 1e-12)
              for group, sound in stems.items()}  # fmt: skip
    values = ", ".join(f"{group.split('.')[1]} {value:.1f}" for group, value in levels.items())
    print(f"{spec.name}, bars {first} to {last}: {len(events)} strokes; group levels: {values}")
    drums = drums * (dsp.db(-1.0) / max(float(np.max(np.abs(drums))), 1e-9))
    target = Path("build/audio") / f"{name}.flac"
    target.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(str(target), drums, dsp.RATE, subtype="PCM_24")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(target), "-codec:a", "libmp3lame",
         "-q:a", "1", str(target.with_suffix(".mp3"))],
        check=True,
    )  # fmt: skip
    print(f"wrote {target.with_suffix('.mp3')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
