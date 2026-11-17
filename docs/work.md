# The work: form and material

This document describes the music of *G-Type Star*.
The style study ([`style-study.md`](style-study.md)) gives the measured values that the music uses.
The audio is in [`audio.md`](audio.md).

## Summary

| Item | Value |
| --- | --- |
| Form | One piece in eight linked parts: the life of a star like the Sun |
| Ensemble | A band (tenor saxophone, guitar with eight strings, electric piano, bass guitar, drums), four more horns, synthesizers, strings, a drum machine, and recorded sounds (see [`design/ensemble.toml`](../design/ensemble.toml)) |
| Main metre | 14/8 with five pulses: 3 + 3 + 2 + 3 + 3 eighth notes |
| Tempos | 175, 140, and 116.67 quarter notes in a minute: the ratios 15 : 12 : 10 |
| Key centre | G |
| Score | In C. Guitar, bass guitar, and synthesizer bass are written one octave higher than they sound. |

<!-- facts: start -->
- Length: 340 bars, 13:00 minutes.
- The dubstep passage (part 6): bars 271 to 286, 27.4 seconds.
- The one sudden pause: bar 270, from beat 3.5, 0.77 seconds, before the first beat of part 6.
- Recorded sounds: 41 cues; 20 of them are voices of the flight Mercury-Redstone 3.
<!-- facts: end -->

## The form

The Sun is a star of the type G. The form follows the life of such a star.

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

| Part | In the star | In the music |
| --- | --- | --- |
| 1 | A cloud of gas and dust falls together. | No steady groove: the sound of the Sun, radio noise, chords of fourths, single high notes. The drums go faster by division, from one to eight notes in a beat. One dense chord of all players. |
| 2 | The fusion of hydrogen starts. | The riff of the work comes in behind a filter that opens. A voice counts: "two, one, fire". On "fire", all players start. The riff has no major third yet. |
| 3 | The star burns hydrogen in a stable state. | The theme; the theme again with a riff of the band against it; a drum-and-bass beat in the same bar of seven, with the bridge melody above it; the saxophone and the guitar take turns (four bars each, two, one); bass and drums in turns; a quiet middle; and the theme with five notes in each long pulse. |
| 4 | Spots and flares. | A heavy rock groove in plain 4/4: double pedal kick drum, the low string of the guitar, a guitar solo, a line of all lead players. The key goes up by minor thirds. |
| 5 | The star swells and becomes cooler. | The long pulse becomes the beat of a slow bar. The theme is a chorale of horns and strings. A solo of the lead synthesizer. Then ten bars of build-up on the note D. |
| 6 | Helium starts to burn, all at one time. | The one dubstep passage of the work. |
| 7 | Pulses of a burning shell; then the burning stops. | The most driving music of the work: the kick drum never stops. Then the fall: tempo, pitch, and register go down, faster and faster. |
| 8 | A white dwarf. | A low held tone, the sound of the Sun, a chord of three fourths, and one last high note. |

## The material

### The clave

The main metre has seven quarter notes in a bar. It is written as 14/8, with five pulses: long, long, short, long, long.
The snare drum is on the second and on the fifth pulse: the bar sounds as a bar of four beats with a short extra beat in its middle.
The model is the track "Cool 7" of Sungazer, which has the short pulse at the end.

### The motto

Four notes: G, C, D, E (a fourth up, then two steps).
The theme starts with them, the lines contain them, the three "thermal pulses" of part 7 play them in three keys, and the last note of the work is the fourth note alone.

### The loop

The theme stays in the scale of G major; the chords under it change colour:
G major 9, E-flat major 7 (sharp 11), C major 9 (sharp 11), A minor 11.
The roots go down by thirds.

### The theme and its forms

The theme has eight bars with few, long notes. Each time it comes back, the tenor saxophone uses a different part of its range, and the contour changes:

| Place | Form (in [`work/material.py`](../src/gtypestar/work/material.py)) | Range |
| --- | --- | --- |
| C, bars 1 to 8 | `THEME_LOW` | The middle and low register, G3 to G4 |
| C, bars 9 to 16 | `THEME_LOW_RISE` | Starts low, breaks into the high octave at its highest phrase, falls two octaves |
| D | `THEME_WIDE`, `THEME_CLOSE_WIDE` | A start from the low D, a leap of an eleventh, up to B-flat 5, a fall to the low B |
| H (the quiet middle) | `THEME_DEEP` | The low register with much air; the last note is A2 |
| J | `THEME_LEAPS` | The motto low, each answer high; the highest note is B5 |
| N, P (part 5) | The chorale, in E-flat and in G | Trumpet and strings; the saxophone has the second voice |
| S (part 7) | `THEME_FORCE` (in [`work/agb.py`](../src/gtypestar/work/agb.py)) | Accented low notes, leaps of two octaves, the highest note C6 |
| W (part 8) | The first three notes of the motto | Low and soft |

### The lines

Four fast lines of sixteenth notes for all lead players (saxophone, guitar, lead synthesizer, chip synthesizer, bass guitar):
two bars at the end of D, four bars at the end of F, the first line a semitone lower with its mirror form in part 4, and eight bars in part 7.

## What the owner asked for, and where it is

| Request | Where |
| --- | --- |
| "NEVER the same thing twice" | No two bars of a drum groove are the same (`Groove.vary`): ghost notes, a kick that moves, open hi-hats. The bass figure changes in each bar and does not come back within three bars. The theme has a new form each time. |
| "It feels dirty. It should not feel square and computational." | Each player has its own small shifts of time and loudness, with the measured spread of the reference drums. The bass has a band with grit, the electric piano has saturation, the guitar has a model of an amplifier. |
| Dubstep, one time, 30 seconds or less | Part 6: 16 bars at 140 quarter notes in a minute. Six bass sounds take turns. |
| "A sudden pause is fine, but only once in the piece." | The silence before the first beat of part 6. No other part stops: where the voice counts in part 2, the snare drum rolls. |
| "The transitions between sections could be better developed." | Each change of part has a link: chords and noise that start before the bar line, a bass that leads to the next root, a chord that rings on, the beat of the next tempo in the last bars. |
| "lean into a rock groove … double pedal kick drum" (the flares) | Part 4 is in plain 4/4 with a steady backbeat. |
| "heavy guitar" | Parts 4 and 7. |
| "a really blood pumping section … that like falls apart, strong gravity from the dwarf star" | Part 7. |
| "the saxophone would explore more of its range" | The table of the forms of the theme, above. |
| "Everything from 2:30-4:30 is pretty boring." | These two minutes (marks D, E, F) had the theme a second time above the same chords, a soft bridge of long notes, and a solo that started slowly. Now: D has a riff of bass and guitar against the theme, answers of the horns, and new chords that go up. E is a drum-and-bass beat (the tempo of the work, 175, is the tempo of that style) with the bridge melody, a short solo of the electric piano, and a snare roll. F has the saxophone and the guitar in turns that become shorter, then the fast line of all lead players. |
| "a nice full bodied sound from the guitar that shreds in a jazz metal way" | The solo of the guitar in part 4 (mark L): joined notes, a darker amplifier sound, one octave lower. See [`audio.md`](audio.md), "The guitar". |
| "an audio sample of an astronaut swearing over the radio … both funny and tasteful" | The first bar of part 5 (mark N), after the flares: "That son of a bitch was wild." (Eugene Cernan, Apollo 10), then a radio tone. One time. |

## The recorded sounds

- The oscillations of the Sun, 42 000 times faster (a recording of NASA, and a sound that code makes from the measured frequencies of the modes).
- The radio traffic of the first American flight into space, Mercury-Redstone 3 (1961): "Trajectory okay", the numbers of the force on the pilot ("two G", "five G"), and two countdowns ("two, one, fire").
- One sentence from the lunar module of Apollo 10 (1969). At the separation of its two stages, the module turned over and over for some seconds. Twelve minutes later, Eugene Cernan said: "That son of a bitch was wild." The sentence comes after the flares.
- Plasma waves that Voyager 1 recorded at the edge of the Solar System, and radio waves of Saturn and of the Earth.
- Radio noise, radio tones, and a data signal that code makes.

The staff "Recorded Sounds" of the score has one note for each sound that starts.
See [`audio.md`](audio.md) for the sources and the licences.
