"""Find the words of a public-domain speech recording, with their times.

The recorded sounds of the work use short parts of the radio traffic of
space missions. This script writes the text of a recording with the time of
each phrase: thus the composer can select phrases without listening.

The script needs the analysis environment and the package `faster-whisper`.

Usage:

    .cache/analysis-venv/bin/python tools/extract/speech.py .cache/media/mercury3-548.mp3
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def main() -> int:
    path = Path(sys.argv[1])
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(path), vad_filter=True, word_timestamps=True)
    rows = [
        {
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": [[word.word.strip(), round(word.start, 2), round(word.end, 2)]
                      for word in segment.words or []],
        }
        for segment in segments
    ]
    target = path.with_suffix(".json")
    target.write_text(json.dumps(rows, indent=1))
    print(f"{path.name}: {len(rows)} phrases -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
