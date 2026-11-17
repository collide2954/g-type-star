"""Read a drum kit in the SFZ format that has one file for each microphone.

The kit "Naked Drums" (Wilkinson Audio, the SFZ version by kinwie) is such a
kit: each stroke of a drum is some files, one for each group of microphones
(direct microphones, overheads, room). The kit has one SFZ program for each
microphone. The programs are short: they include many small text files, and
they use variables (`#define $NAME value`).

This module reads the programs and returns a table of the strokes:

    microphone -> key (MIDI number of the kit piece) -> list of `Region`

It reads only the parts of the format that this kit uses.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from pathlib import Path

HEADER = re.compile(r"<(\w+)>")
OPCODE = re.compile(r"([A-Za-z_]\w*)=")


@dataclass(frozen=True)
class Region:
    """One recorded stroke of one microphone."""

    key: int
    low: int  # the lowest and the highest velocity (1 to 127) that plays this stroke
    high: int
    position: int  # the number of the stroke in its series (1 = first)
    sample: str  # the name of the file
    volume: float  # in decibels: the sum of the trims of the program
    switch: int | None  # the key switch that the stroke needs, or None
    release: bool  # the sound of a cymbal that a hand stops: it plays at the end of a note


def _substitute(text: str, defines: dict[str, str]) -> str:
    """Replace the variables of a line. A name is the longest defined name at a `$`."""
    for _ in range(8):  # a value can have a variable
        if "$" not in text:
            break
        out = []
        place = 0
        changed = False
        while place < len(text):
            if text[place] == "$":
                rest = text[place:]
                name = max((key for key in defines if rest.startswith(key)), key=len, default=None)
                if name is not None:
                    out.append(defines[name])
                    place += len(name)
                    changed = True
                    continue
            out.append(text[place])
            place += 1
        text = "".join(out)
        if not changed:
            break
    return text


def _lines(path: Path, base: Path, defines: dict[str, str], depth: int = 0):
    """Yield the lines of a program, with its included files and with values for variables."""
    if depth > 12:
        raise ValueError(f"{path}: too many levels of included files")
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        if line.startswith("#include"):
            match = re.search(r'"([^"]+)"', line)
            if match:
                target = (base / _substitute(match.group(1), defines)).resolve()
                yield from _lines(target, base, defines, depth + 1)
        elif line.startswith("#define"):
            # One line can have more than one definition.
            for piece in line.split("#define")[1:]:
                parts = piece.split(None, 1)
                if parts:
                    defines[parts[0]] = parts[1].strip() if len(parts) > 1 else ""
        else:
            yield _substitute(line, defines)


def _number(text: str | None, default: float = 0.0) -> float:
    try:
        return float(text) if text is not None else default
    except ValueError:
        return default


def read_program(path: Path) -> list[Region]:
    """Return the strokes of one SFZ program."""
    levels: dict[str, dict[str, str]] = {"global": {}, "master": {}, "group": {}, "region": {}}
    order = ["global", "master", "group", "region"]
    regions: list[Region] = []
    current = "global"

    def close() -> None:
        values: dict[str, str] = {}
        for level in order:
            values.update(levels[level])
        sample = values.get("sample")
        key = values.get("key")
        if not sample or key is None or sample.startswith("*"):
            return  # "*silence" is a stroke with no sound: it only stops other strokes
        trims = (("master", "master_volume"), ("group", "group_volume"), ("region", "volume"))
        volume = sum(_number(levels[level].get(name)) for level, name in trims)
        switch = values.get("sw_last")
        regions.append(
            Region(
                key=int(_number(key)),
                low=int(_number(values.get("lovel"), 1)),
                high=int(_number(values.get("hivel"), 127)),
                position=int(_number(values.get("seq_position"), 1)),
                sample=sample.replace("\\", "/").split("/")[-1],
                volume=volume,
                switch=None if switch is None else int(_number(switch)),
                release=values.get("trigger", "attack") != "attack",
            )
        )

    defines: dict[str, str] = {}
    for line in _lines(path, path.parent, defines):
        pieces = HEADER.split(line)
        # pieces: text before the first header, then (header name, text) pairs.
        chunks = [(current, pieces[0])] + [
            (pieces[index], pieces[index + 1]) for index in range(1, len(pieces) - 1, 2)
        ]
        for number, (header, text) in enumerate(chunks):
            if number > 0:
                if current == "region":
                    close()
                current = header if header in levels else "global"
                for level in order[order.index(current) :] if current in order else []:
                    levels[level] = {}
            marks = list(OPCODE.finditer(text))
            for index, mark in enumerate(marks):
                end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
                levels[current][mark.group(1)] = text[mark.end() : end].strip()
    if current == "region":
        close()
    return regions


@functools.lru_cache(maxsize=4)
def read(root: str, programs: tuple[tuple[str, str], ...]) -> dict[str, dict[int, list[Region]]]:
    """Read the programs of a kit: (microphone, file) pairs. Return microphone -> key -> strokes."""
    table: dict[str, dict[int, list[Region]]] = {}
    for microphone, name in programs:
        by_key: dict[int, list[Region]] = {}
        for region in read_program(Path(root) / name):
            by_key.setdefault(region.key, []).append(region)
        table[microphone] = by_key
    return table
