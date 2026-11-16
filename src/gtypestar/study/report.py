"""Check the study tables and write the style study report."""

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

RESEARCH_DIR = Path("research")
TABLES_DIR = RESEARCH_DIR / "tables"
MEASURED_DIR = RESEARCH_DIR / "measured"
TEXT_DIR = RESEARCH_DIR / "text"
REPORT_PATH = Path("docs/style-study.md")

EVIDENCE_CODES = {"R", "K", "M", "R, K"}

Row = dict[str, str]


def read_table(path: Path) -> tuple[list[str], list[Row]]:
    """Read a CSV table. Return its header and its rows."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------


def check() -> list[str]:
    """Check the sourced tables. Return a list of problems."""
    problems: list[str] = []
    _, sources = read_table(RESEARCH_DIR / "sources.csv")
    keys = {row["key"] for row in sources}
    if len(keys) != len(sources):
        problems.append("sources.csv: a key occurs more than one time")

    for path in sorted(TABLES_DIR.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            raw = list(csv.reader(handle))
        header = raw[0]
        for number, cells in enumerate(raw[1:], 2):
            if len(cells) != len(header):
                problems.append(
                    f"{path.name} line {number}: {len(cells)} cells, header has {len(header)}"
                )
        _, rows = read_table(path)
        for number, row in enumerate(rows, 2):
            if not (row[header[0]] or "").strip():
                problems.append(f"{path.name} line {number}: first cell is empty")
            if "evidence" in row and row["evidence"] not in EVIDENCE_CODES:
                problems.append(f"{path.name} line {number}: evidence code {row['evidence']!r}")
            if "source" in row:
                cited = [key.strip() for key in row["source"].split(";") if key.strip()]
                if not cited:
                    problems.append(f"{path.name} line {number}: no source")
                for key in cited:
                    if key not in keys:
                        problems.append(f"{path.name} line {number}: unknown source {key!r}")
                evidence = row.get("evidence", "")
                if evidence == "K" and cited != ["reference"]:
                    problems.append(f"{path.name} line {number}: code K must cite 'reference'")
                if evidence == "R" and "reference" in cited:
                    problems.append(f"{path.name} line {number}: code R cannot cite 'reference'")
    return problems


# ----------------------------------------------------------------------------
# Markdown output
# ----------------------------------------------------------------------------


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Return a Markdown table."""
    lines = [
        "| " + " | ".join(_cell(h) for h in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _label(column: str) -> str:
    text = column.replace("_", " ")
    return text[0].upper() + text[1:]


def percent(value: str) -> str:
    """Show a share (0 to 1) as a percentage."""
    try:
        return f"{100 * float(value):.1f} %"
    except ValueError:
        return value


def number(digits: int) -> Callable[[str], str]:
    """Return a function that rounds a number to the given number of decimal places."""

    def convert(value: str) -> str:
        try:
            amount = float(value)
        except ValueError:
            return value
        if amount == int(amount) and "." not in value:
            return str(int(amount))
        return f"{amount:.{digits}f}"

    return convert


@dataclass
class TableSpec:
    """How the report shows one table."""

    title: str
    path: Path
    intro: list[str]
    columns: list[str] | None = None  # columns to show; None = all
    formats: dict[str, Callable[[str], str]] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    keep: Callable[[Row], bool] | None = None

    def render(self) -> str:
        header, rows = read_table(self.path)
        columns = self.columns or header
        if self.keep:
            rows = [row for row in rows if self.keep(row)]
        body = [
            [self.formats.get(column, str)(row[column] or "") for column in columns] for row in rows
        ]
        shown = [self.labels.get(column, _label(column)) for column in columns]
        parts = [f"### {self.title}", *self.intro, markdown_table(shown, body)]
        parts.append(f"Data file: [`{self.path.as_posix()}`](../{self.path.as_posix()})")
        return "\n\n".join(parts)


MEASURED = [
    (
        "M1. Reference tracks: loudness and stereo width",
        "reference_recordings.csv",
        [
            "The loudness unit is the LUFS (ITU-R BS.1770). The loudness range is the difference "
            "between the loud and the soft passages (EBU Tech 3342). The short-term values are "
            "relative to the integrated loudness. The side level is the level of the difference "
            "of the two channels, relative to their sum.",
        ],
    ),
    (
        "M2. Reference tracks: tone balance",
        "reference_tone_balance.csv",
        [
            "The table gives the level of each third-octave band, relative to the total level. "
            "The master of the work gets the mean values.",
        ],
    ),
    (
        "M3. Reference tracks: pulse, cycles, strokes, and repetition",
        "reference_rhythm.csv",
        [
            "The pulse is the fastest regular note value of a track. A cycle is the number of "
            "pulses after which the pattern of the snare drum (or of the kick drum) comes again; "
            "the percentages are shares of the windows of 192 pulses. The last columns show how "
            "frequently a bar of kick and snare (a cycle of the main length) is the same as the "
            "bar before it, or as one of the 8 bars before it.",
        ],
    ),
    (
        "M4. Reference tracks: timing and loudness of the drum strokes",
        "reference_timing.csv",
        [
            "The spread is a robust standard deviation of the distance of the strokes from the "
            "pulse grid, with the error of the measurement. The levels are relative to the loud "
            "strokes of the drum (90th percentile). A soft stroke is 9 dB or more below them.",
        ],
    ),
    (
        "M5. Reference tracks: the bass",
        "reference_bass.csv",
        [
            "The notes of the bass stem. MIDI number 33 is A1; 23 is the low B string. "
            "The last columns are shares of the moves between two notes.",
        ],
    ),
    (
        "M6. Reference tracks: density of the notes",
        "reference_lines.csv",
        [
            "Note starts of the stem with the other instruments (guitar, keyboards, "
            "synthesizers, saxophone, strings), in windows of one second. Chords count as "
            "some starts at one time.",
        ],
    ),
    (
        "M7. Reference tracks: loudness of the stems",
        "reference_stems.csv",
        ["The integrated loudness of each stem, relative to the full track, in LU."],
    ),
    (
        "M8. Reference tracks: shape",
        "reference_form.csv",
        [
            "The full level is the range of 3 dB below the 90th percentile of the loudness "
            "(windows of 3 s). A short stop is a fall of 10 dB or more for 1.5 s or less.",
        ],
    ),
    (
        "M9. The new work",
        "work.csv",
        [
            "The same measurements for *G-Type Star*, from its score and from its master. "
            "The command `uv run gtypestar docs` makes this table again.",
        ],
    ),
]

SOURCED = [
    ("S1. Works and data", "works.csv"),
    ("S2. Forces: players, instruments, tunings", "forces.csv"),
    ("S3. Form", "form.csv"),
    ("S4. Tempo", "tempo.csv"),
    ("S5. Rhythm and metre", "rhythm.csv"),
    ("S6. Harmony", "harmony.csv"),
    ("S7. Melody and fast lines", "melody.csv"),
    ("S8. Texture and arranging", "texture.csv"),
    ("S9. Electronics", "electronics.csv"),
    ("S10. Production and mix", "production.csv"),
    ("S11. Variation: how an idea comes again", "variation.csv"),
    ("S12. Devices", "devices.csv"),
    ("S13. Feel: timing and loudness of real players", "feel.csv"),
]

PROFILES = {
    "All": 'P1. Profile "All": the full work',
    "Groove": 'P2. Profile "Groove": the main metre (parts 2, 3, 7)',
    "Feel": 'P3. Profile "Feel": the performance layer',
    "Lines": 'P4. Profile "Lines": the lines of the lead players',
    "Space": 'P5. Profile "Space": the nebula and the white dwarf (parts 1, 8)',
    "Heavy": 'P6. Profile "Heavy": the flares (part 4)',
    "Large": 'P7. Profile "Large": the red giant (part 5)',
    "Dubstep": 'P8. Profile "Dubstep": the helium flash (part 6)',
}


def render_measured() -> list[str]:
    parts = []
    for title, name, intro in MEASURED:
        path = MEASURED_DIR / name
        if not path.exists():
            continue
        header, rows = read_table(path)
        body = [[row[column] or "" for column in header] for row in rows]
        parts.append(f"### {title}")
        parts += intro
        parts.append(markdown_table([_label(column) for column in header], body))
        parts.append(f"Data file: [`{path.as_posix()}`](../{path.as_posix()})")
    return parts


def render_sourced() -> list[str]:
    parts = []
    for title, name in SOURCED:
        path = TABLES_DIR / name
        header, rows = read_table(path)
        columns = ["circle", "artist", "item", "content", "parameters", "where", "source",
                   "evidence"]  # fmt: skip
        labels = ["Circle", "Artist or study", "Item", "Content", "Values", "Where", "Source",
                  "Code"]  # fmt: skip
        body = [[row[column] or "" for column in columns] for row in rows]
        parts.append(f"### {title}")
        parts.append(markdown_table(labels, body))
        parts.append(f"Data file: [`{path.as_posix()}`](../{path.as_posix()})")
    return parts


def render_profiles() -> str:
    """Render the style profiles, one table for each profile."""
    _, rows = read_table(TABLES_DIR / "profiles.csv")
    parts = []
    for profile, title in PROFILES.items():
        chosen = [row for row in rows if row["profile"] == profile]
        parts.append(f"### {title}")
        parts.append(
            markdown_table(
                ["Group", "Parameter", "Low", "High", "Unit", "Basis", "Code"],
                [
                    [row["group"], row["parameter"], row["low"], row["high"], row["unit"],
                     row["basis"], row["evidence"]]
                    for row in chosen
                ],
            )
        )  # fmt: skip
    path = (TABLES_DIR / "profiles.csv").as_posix()
    parts.append(f"Data file: [`{path}`](../{path})")
    return "\n\n".join(parts)


def render_sources() -> str:
    """Render the list of sources."""
    _, rows = read_table(RESEARCH_DIR / "sources.csv")
    body = []
    for row in rows:
        citation = row["citation"]
        if row["url"]:
            citation += f" <{row['url']}>"
        body.append([f"`{row['key']}`", citation, row["access"]])
    return markdown_table(["Key", "Source", "Access"], body)


def build() -> str:
    """Return the full text of the report."""
    parts = [(TEXT_DIR / "introduction.md").read_text(encoding="utf-8").rstrip()]
    parts.append("## Part 1: Measured tables")
    parts.append(
        "Code made all tables of this part. The directory "
        "[`research/measured`](../research/measured) has the data files."
    )
    parts += render_measured()
    parts.append("## Part 2: Sourced tables")
    parts.append(
        'These tables come from the sources. The column "Circle" gives the research task. '
        "The directory [`research/tables`](../research/tables) has the data files."
    )
    parts += render_sourced()
    parts.append("## Part 3: Style profiles")
    parts.append(
        "A style profile is a set of target ranges for the new work. Each range has a low "
        "value and a high value, around a measured value or a sourced value. The column "
        '"Basis" gives that value. The design files and the code of the work use these ranges.'
    )
    parts.append(render_profiles())
    parts.append((TEXT_DIR / "limits.md").read_text(encoding="utf-8").rstrip())
    parts.append("## Sources")
    parts.append(render_sources())
    return "\n\n".join(parts) + "\n"


def write() -> Path:
    """Write the report file and return its path."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build(), encoding="utf-8")
    return REPORT_PATH
