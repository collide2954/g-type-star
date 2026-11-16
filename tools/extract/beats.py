"""Find the beats and the downbeats of each reference recording.

This script needs the analysis environment (see `tools/extract/README.md`).
It uses the beat tracker "Beat This!" (Foscarin, Schlüter, Widmer, 2024). It
writes one JSON file for each recording into `.cache/reference/derived`.

The tracker has no fixed metre. In music with uneven metres its downbeats
are not always correct: the measurement code makes sure of the bar length
with the patterns of the drums.

Usage:

    .cache/analysis-venv/bin/python -I tools/extract/beats.py [names of recordings]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from beat_this.inference import File2Beats

AUDIO_DIR = Path(".cache/reference/audio")
DERIVED_DIR = Path(".cache/reference/derived")


def main() -> int:
    names = sys.argv[1:]
    paths = sorted(AUDIO_DIR.glob("*.wav"))
    if names:
        paths = [path for path in paths if path.stem in names]
    if not paths:
        print(f"no recordings in {AUDIO_DIR}", file=sys.stderr)
        return 1
    tracker = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    for path in paths:
        target = DERIVED_DIR / path.stem / "beats.json"
        if target.exists():
            print(f"{path.stem}: the beats are there", flush=True)
            continue
        beats, downbeats = tracker(str(path))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "beats": [round(float(time), 4) for time in beats],
                    "downbeats": [round(float(time), 4) for time in downbeats],
                }
            )
        )
        print(f"{path.stem}: {len(beats)} beats, {len(downbeats)} downbeats", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
