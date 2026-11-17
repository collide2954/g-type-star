"""Render some parts of the full work and write their stems, for a test of the balance.

The stems of the full render (`gtypestar audio --export-stems`) need a full
render. This script makes the same stems for the parts of the work inside
some bars only: the other parts are silent. It writes them into
`.cache/stems-part`, not into `build/stems`.

Usage:

    uv run python tools/diagnose/part_stems.py FIRST-LAST

Then, for example:

    uv run python tools/diagnose/front.py 16 .cache/stems-part
"""

from __future__ import annotations

import sys
from pathlib import Path

from gtypestar.audio import render
from gtypestar.work import build

TARGET = Path(".cache/stems-part")


def main() -> int:
    first, _, last = sys.argv[1].partition("-")
    _audio, report = render.render(build(), None, export_to=TARGET, only=(int(first), int(last)))
    print(f"stems: {TARGET} ({report.loudness_lufs:.1f} LUFS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
