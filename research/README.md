# Style study

This directory contains the style study for *G-Type Star*.
The study gives the style of Sungazer and of related groups as numbers and tables.
The composition code and the mix use these tables as their rules.

The full report is [`docs/style-study.md`](../docs/style-study.md).

## Contents

| Path | Contents | How it is made |
| --- | --- | --- |
| [`tables/`](tables) | Sourced tables: works, forces, form, tempo, rhythm, feel, harmony, melody, texture, electronics, production, variation, more devices | Written by the study team from the sources |
| [`tables/profiles.csv`](tables/profiles.csv) | Style profiles: target ranges for the new work (All, Groove, Feel, Lines, Space, Heavy, Large, Dubstep) | Written by the study team from the measured and sourced values |
| [`measured/`](measured) | Measured tables of the reference recordings: loudness, tone balance, pulse and cycle, timing, bass, lines, stems, form | Made by the tools in [`tools/extract`](../tools/extract) and the command `uv run gtypestar-study measure` |
| [`sources.csv`](sources.csv) | List of all sources | Written by the study team |
| [`text/`](text) | Text sections of the report | Written by the study team |

## Evidence codes

Each row of a sourced table has an evidence code.

| Code | Meaning |
| --- | --- |
| M | The study code measured the value. |
| R | The study team read the source. The row gives the key of the source. |
| K | The row is standard reference knowledge. The study team did not read a source for the row. |

## Reference recordings

The measured reference is the album *Against the Fall of Night* of Sungazer (2024).
The owner of the project has the files of six of its nine tracks (tracks 1, 7 and 9 were not in the folder).

- The recordings are not in the repository, and the code cannot download them.
- Copies for the measurement are in the directory `.cache/reference`, which Git ignores: the recordings, their separated stems (drums, bass, other, vocals), and the note lists.
- Only measured numbers are in the repository. They are facts about the recordings; they contain no audio and no melody.

To measure the recordings again, put the files into `.cache/reference/audio` with the names in [`src/gtypestar/audio/reference.py`](../src/gtypestar/audio/reference.py), make the analysis environment (Python 3.10 with PyTorch, Demucs, librosa and basic-pitch), and run the tools:

| Tool | What it measures |
| --- | --- |
| [`tools/extract/separate.py`](../tools/extract/separate.py) | Divides each recording into stems |
| [`tools/extract/rhythm.py`](../tools/extract/rhythm.py) | The pulse, the cycle of the bar, and the strokes of the drums |
| [`tools/extract/notes.py`](../tools/extract/notes.py) | The notes of the bass and of the other instruments |
| [`tools/extract/speech.py`](../tools/extract/speech.py) | The words and their times in the public-domain voice recordings |

## Tools that compare a render with the references

The writer of the code cannot hear. These tools give numbers for the sound of a render.

| Tool | What it shows |
| --- | --- |
| `uv run gtypestar compare FILE` | Loudness, stereo width, and tone balance against the six masters |
| [`tools/tone.py`](../tools/tone.py) | The tone balance of each part of the work, the spread in time, the side signal, and the separated stems against those of the references |
| [`tools/listen.py`](../tools/listen.py) | How near each ten seconds of a render are to the references for an audio model (CLAP), and how well they agree with descriptions in words |
| [`tools/diagnose/mixlab.py`](../tools/diagnose/mixlab.py) | The level of each band for each stem and each group of the mix, for some bars; fast after the first run |
| [`tools/diagnose/pauses.py`](../tools/diagnose/pauses.py) | The sudden pauses of a render (the work must have one) |
| [`tools/diagnose/seams.py`](../tools/diagnose/seams.py) | The level before and after each rehearsal mark |
| [`tools/diagnose/guitar_tone.py`](../tools/diagnose/guitar_tone.py) | The band balance of the guitar model for each amplifier |

## How to build the study

```bash
uv sync
make study
```

The command checks the sourced tables for errors and writes the report `docs/style-study.md`.

## Rules for the tables

- Each value must have a source or a measurement.
- A row with the code K must cite the key `reference`.
- A row with the code R must not cite the key `reference`.
- Do not copy music notation or audio from sources that have a copyright.
  Facts, numbers, and short descriptions are permitted.
