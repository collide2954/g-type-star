# G-Type Star

*G-Type Star* is a work of electronic jazz fusion: one piece of 13 minutes for a band with horns, strings, synthesizers, a drum machine, and recorded sounds of space.
Code makes all parts of the work: the style study, the music, the score, the audio, and the video.

The Sun is a star of the type G. The form of the work follows the life of such a star.

<!-- form table: start -->
| Part | Name | Marks | Bars | Start | Length | Metre | Quarter notes in a minute |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | The nebula | A | 1 to 22 | 0:00 | 1:13 | 4/4 | 70 to 85 |
| 2 | The ignition | B | 23 to 38 | 1:13 | 0:38 | 14/8 | 175 |
| 3 | The main sequence | C to J | 39 to 150 | 1:52 | 4:29 | 14/8 | 175 |
| 4 | The flares | K to M | 151 to 220 | 6:20 | 1:36 | 4/4 | 175 |
| 5 | The red giant | N to Q | 221 to 270 | 7:56 | 1:43 | 4/4 | 117 |
| 6 | The helium flash | R | 271 to 286 | 9:39 | 0:27 | 4/4 | 140 |
| 7 | The last burning and the fall | S to V | 287 to 328 | 10:07 | 1:55 | 14/8 | 72 to 175 |
| 8 | The white dwarf | W to X | 329 to 340 | 12:02 | 0:58 | 4/4 | 54 to 56 |
<!-- form table: end -->

## The model

The model of the style is the band Sungazer, with the instruments of its track "Cool 7", and related groups (Snarky Puppy, live-electronic fusion, progressive and djent fusion, cosmic jazz, the beat scene).
The project studies this style and writes it down as numbers:

- Measured values of six tracks of the album *Against the Fall of Night* (the owner of the project has the files; they are not in the repository): the pulse and the cycle of each bar, the timing of the drums, the bass, the fast lines, the loudness, the tone balance, and the balance of drums, bass, and music.
- 881 rows of sourced tables from 604 sources.
- Style profiles: target ranges that the music and the mix use.

The full report is [`docs/style-study.md`](docs/style-study.md). The work uses the sources; it does not copy a riff or a melody of them.

## Documents

| Document | Contents |
| --- | --- |
| [`docs/work.md`](docs/work.md) | The form, the material, and where each request of the owner is in the music |
| [`docs/audio.md`](docs/audio.md) | The sources of sound, the mix, the master, how the sound is checked, and the credits |
| [`docs/style-study.md`](docs/style-study.md) | The style study |
| [`research/README.md`](research/README.md) | The tables of the study and the measuring tools |
| [`design/brief.toml`](design/brief.toml) | The decisions of the owner |
| [`design/ensemble.toml`](design/ensemble.toml) | The players and their instruments |

## How the music is written

The music is text in a small part of the LilyPond language, inside Python code ([`src/gtypestar/work`](src/gtypestar/work)).
Code changes the written music into a performance (each player has small shifts of time and loudness), and the performance into audio, a score, and a video.

- A rhythm is a pattern of letters, one group for each pulse of the bar: `"a__x-b ---c-e b_a_ a__x-c ---e_c"`.
- A drum groove is data. A function makes the small changes of a drummer: no two bars are the same.
- A theme is written one time. Tools make its other forms: at a different pitch, upside down, or in a different register.

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.12 or later
- [LilyPond](https://lilypond.org/) 2.26 or later, for the score
- [FFmpeg](https://ffmpeg.org/), for the MP3 file and the video
- For the saxophone, the horns, and the strings of the master: MuseScore Studio 4 with Muse Sounds. Without them, synthesizer patches play these parts (`--no-muse`).

The audio needs about 14 GB of free sound files (a sampled drum kit, hand percussion, a recorded guitar and models of its amplifiers, a bass guitar, an electric piano, and recordings of NASA). This command downloads them into the directory `.cache` (the guitar library is a RAR archive: the package `libarchive-c` unpacks it with the libarchive library of the system):

```bash
uv run --with libarchive-c gtypestar fetch
```

## Commands

```bash
uv sync                           # install the Python environment
uv run gtypestar check            # find music that a player cannot play
uv run gtypestar parts            # the score and all parts (build/score, build/parts)
uv run gtypestar audio            # the audio master (build/audio)
uv run gtypestar audio --bars 151-220 --name flares   # an excerpt
uv run gtypestar audio --export-stems                 # the master and the stems (build/stems)
uv run gtypestar midi             # the performance as a MIDI file (build/midi)
uv run gtypestar video            # the score video; add --mobile for a telephone
uv run gtypestar compare FILE     # compare a render with the reference values
make study                        # check the tables of the style study and write the report
make test                         # run the tests
```

## Licence

- The code is under the MIT License. See [`LICENSE`](LICENSE).
- The music, the score, the parts, the audio, the video, and the documents are under the
  Creative Commons Attribution 4.0 International licence (CC BY 4.0).
  See [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0).
- The audio uses free sample libraries and public recordings. See the credits in [`docs/audio.md`](docs/audio.md).

This repository starts from the engine of
[*Night Music for Orchestra*](https://github.com/collide2954/night-music-for-orchestra).
