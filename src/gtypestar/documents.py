"""Keep the numbers in the documents the same as the numbers of the music.

The documents have a table of the form with bar numbers and times, and a
list of facts (the length of the dubstep passage, the place of the one
sudden pause). These values change when the music changes. This module
calculates them from the work and writes them between two marker lines:

    <!-- form table: start -->
    ...
    <!-- form table: end -->

The text of the documents outside the markers stays as the writer wrote
it. A test makes sure that the documents are up to date.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .notation.work import Work

ROOT = Path(__file__).resolve().parents[2]
FILES = (ROOT / "docs" / "work.md", ROOT / "README.md")

# The parts of the work: number, name, the first rehearsal mark ("" = the first bar),
# and what happens in the star.
PARTS = [
    ("1", "The nebula", "", "A cloud of gas and dust falls together."),
    ("2", "The ignition", "B", "The fusion of hydrogen starts."),
    ("3", "The main sequence", "C", "The star burns hydrogen in a stable state."),
    ("4", "The flares", "K", "The active Sun: spots, flares, and the cycle of 11 years."),
    ("5", "The red giant", "N", "The star swells and becomes cooler."),
    ("6", "The helium flash", "R", "Helium starts to burn in the core, all at one time."),
    (
        "7",
        "The last burning and the fall",
        "S",
        "Pulses of a shell; then gravity is the only force.",
    ),
    ("8", "The white dwarf", "W", "What stays: small, dense, and cold."),
]


def clock(seconds: float) -> str:
    """Return a time as minutes and seconds, for example "7:33"."""
    whole = int(seconds + 0.5)
    return f"{whole // 60}:{whole % 60:02d}"


def part_bars(work: Work) -> list[tuple[int, int]]:
    """Return the first and the last bar of each part."""
    marks = {label: bar for bar, label in work.structure.marks.items()}
    firsts = [marks[mark] if mark else 1 for _number, _name, mark, _text in PARTS]
    lasts = [first - 1 for first in firsts[1:]] + [len(work.structure.bars)]
    return list(zip(firsts, lasts, strict=True))


def form_table(work: Work) -> list[str]:
    """Return the table of the form as lines of Markdown."""
    structure = work.structure
    labels = sorted(structure.marks.items())
    lines = [
        "| Part | Name | Marks | Bars | Start | Length | Metre | Quarter notes in a minute |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for (number, name, _mark, _text), (first, last) in zip(PARTS, part_bars(work), strict=True):
        bars = structure.bars[first - 1 : last]
        start = structure.seconds(bars[0].start)
        end = structure.seconds(bars[-1].end)
        metres = Counter(f"{bar.numerator}/{bar.denominator}" for bar in bars)
        metre = ", ".join(name_ for name_, _count in metres.most_common(2))
        inside = [label for bar, label in labels if first <= bar <= last]
        marks = (
            "" if not inside else inside[0] if len(inside) == 1 else f"{inside[0]} to {inside[-1]}"
        )
        tempos = [structure.bpm_at(bar.start) for bar in bars]
        low, high = min(tempos), max(tempos)
        tempo = f"{low:.0f}" if high - low < 1.0 else f"{low:.0f} to {high:.0f}"
        lines.append(
            f"| {number} | {name} | {marks} | {first} to {last} | {clock(start)} | "
            f"{clock(end - start)} | {metre} | {tempo} |"
        )
    return lines


def pause(work: Work) -> tuple[int, float, float] | None:
    """Return the one sudden pause of the work: its bar, its beat, and its length in seconds."""
    structure = work.structure
    mutes = [edit for edit in work.extras.get("edits", []) if edit.kind == "mute"]
    if len(mutes) != 1:
        return None
    edit = mutes[0]
    start = structure.bar(edit.bar).start + float(edit.beat) - 1
    seconds = structure.seconds(start + float(edit.length)) - structure.seconds(start)
    return edit.bar, float(edit.beat), seconds


def facts(work: Work) -> list[str]:
    """Return the list of facts as lines of Markdown."""
    structure = work.structure
    bars = dict(zip([number for number, *_ in PARTS], part_bars(work), strict=True))
    first, last = bars["6"]
    flash = structure.seconds(structure.bar(last).end) - structure.seconds(
        structure.bar(first).start
    )
    lines = [
        f"- Length: {len(structure.bars)} bars, {clock(structure.duration_seconds)} minutes.",
        f"- The dubstep passage (part 6): bars {first} to {last}, {flash:.1f} seconds.",
    ]
    found = pause(work)
    if found:
        bar, beat, seconds = found
        lines.append(
            f"- The one sudden pause: bar {bar}, from beat {beat:g}, {seconds:.2f} seconds, "
            "before the first beat of part 6."
        )
    cues = work.extras.get("cues", [])
    voices = [cue for cue in cues if cue.text]
    lines.append(
        f"- Recorded sounds: {len(cues)} cues; {len(voices)} of them are voices of the flight "
        "Mercury-Redstone 3."
    )
    return lines


def _replace(text: str, name: str, lines: list[str]) -> str:
    """Replace the lines between the two markers of `name`. A text with no markers stays."""
    start, end = f"<!-- {name}: start -->", f"<!-- {name}: end -->"
    if start not in text or end not in text:
        return text
    before, rest = text.split(start, 1)
    _old, after = rest.split(end, 1)
    return before + start + "\n" + "\n".join(lines) + "\n" + end + after


def updated(text: str, work: Work) -> str:
    """Return the text of a document with the current values of the work."""
    text = _replace(text, "form table", form_table(work))
    return _replace(text, "facts", facts(work))


def update_files(work: Work) -> list[Path]:
    """Write the current values into the documents. Return the files that changed."""
    changed = []
    for path in FILES:
        if not path.exists():
            continue
        old = path.read_text(encoding="utf-8")
        new = updated(old, work)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    return changed
