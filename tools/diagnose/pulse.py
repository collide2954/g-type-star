"""Show how clear the pulse of a render is, part by part, against the reference recordings.

"Pulse clarity" is a number from 0 to 1: the height of the highest peak of
the autocorrelation of the onset curve, for a delay between 0.2 and 2.5
seconds. A groove that the ear can follow has strokes that come again
after the same time: the number is high. Free music, and music in which no
pattern comes again, has a low number.

The script shows the number for each part of the work (from one rehearsal
mark to the next), and the range of the same number in windows of the
reference recordings (`.cache/reference/audio`). A part of the work below
the range of the references is a part whose rhythm is harder to follow
than any passage of the references. (The nebula, the fall and the white
dwarf have no steady pulse: that is their plan.)

The script needs the analysis environment (librosa):

    .cache/analysis-venv/bin/python tools/diagnose/pulse.py build/audio/g-type-star.flac
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np

RATE = 22050
HOP = 256
WINDOW = 12.0  # seconds, for the reference recordings
REFERENCES = Path(".cache/reference/audio")


def clarity(envelope: np.ndarray) -> float:
    """Return the pulse clarity of an onset curve."""
    if len(envelope) < 200 or float(envelope.std()) < 1e-9:
        return 0.0
    curve = envelope - envelope.mean()
    auto = np.correlate(curve, curve, mode="full")[len(curve) - 1 :]
    auto = auto / max(auto[0], 1e-12)
    low = int(0.2 * RATE / HOP)
    high = min(len(auto) - 1, int(2.5 * RATE / HOP))
    return float(auto[low:high].max())


def onsets(path: Path) -> np.ndarray:
    sound, _rate = librosa.load(str(path), sr=RATE, mono=True)
    return librosa.onset.onset_strength(y=sound, sr=RATE, hop_length=HOP)


def marks() -> list[tuple[float, str]]:
    """Return the times of the rehearsal marks, from the main environment of the project."""
    code = (
        "import json; from gtypestar.work import build; s = build().structure; "
        "print(json.dumps(sorted((s.seconds(s.bar(b).start), l) for b, l in s.marks.items())))"
    )
    result = subprocess.run(["uv", "run", "python", "-c", code], capture_output=True, text=True,
                            check=True)  # fmt: skip
    return [(float(start), label) for start, label in json.loads(result.stdout.strip())]


def main() -> int:
    values = []
    for path in sorted(REFERENCES.glob("*.wav")):
        envelope = onsets(path)
        size = int(WINDOW * RATE / HOP)
        found = [clarity(envelope[start : start + size])
                 for start in range(0, len(envelope) - size, size)]  # fmt: skip
        values += found
        print(f"reference {path.stem[:28]:28s} median {np.median(found):.2f}  "
              f"lowest tenth {np.percentile(found, 10):.2f}")  # fmt: skip
    floor = float(np.percentile(values, 10))
    print(f"all references: median {np.median(values):.2f}, lowest tenth {floor:.2f}\n")
    envelope = onsets(Path(sys.argv[1]))
    places = marks()
    total = len(envelope) * HOP / RATE
    for index, (start, label) in enumerate([(0.0, "start"), *places]):
        end = places[index][0] if index < len(places) else total
        part = envelope[int(start * RATE / HOP) : int(end * RATE / HOP)]
        # A long part: the median of its windows.
        size = int(WINDOW * RATE / HOP)
        pieces = [part[first : first + size] for first in range(0, max(1, len(part) - size // 2), size)]
        found = [clarity(piece) for piece in pieces if len(piece) > size // 2] or [clarity(part)]
        value = float(np.median(found))
        flag = "  below the references" if value < floor else ""
        print(f"{label:6s}{int(start // 60)}:{start % 60:04.1f}  {value:.2f}  "
              f"(windows: {' '.join(f'{item:.2f}' for item in found)}){flag}")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
