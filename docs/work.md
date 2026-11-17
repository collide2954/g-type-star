# The work: form and material

This document describes the music of *G-Type Star*.
The style study ([`style-study.md`](style-study.md)) gives the measured values that the music uses.
The audio is in [`audio.md`](audio.md).

## Summary

| Item | Value |
| --- | --- |
| Form | One piece in eight linked parts: the life of a star like the Sun |
| Ensemble | A band (tenor saxophone, guitar with eight strings, electric piano, bass guitar, drums, percussion), four more horns, synthesizers, strings, a drum machine, and recorded sounds (see [`design/ensemble.toml`](../design/ensemble.toml)) |
| Main metre | 14/8 with five pulses: 3 + 3 + 2 + 3 + 3 eighth notes |
| Tempos | 175, 140, and 116.67 quarter notes in a minute: the ratios 15 : 12 : 10 |
| Key centre | G |
| Score | In C. Guitar, bass guitar, and synthesizer bass are written one octave higher than they sound. |

<!-- facts: start -->
- Length: 340 bars, 13:00 minutes.
- The dubstep passage (part 6): bars 271 to 286, 27.4 seconds.
- The one sudden pause: bar 270, from beat 3.5, 0.77 seconds, before the first beat of part 6.
- Recorded sounds: 33 cues; 12 of them are voices of the flight Mercury-Redstone 3.
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
| 1 | A cloud of gas and dust falls together. | No steady groove: the sound of the Sun, radio noise, chords of fourths, single high notes. The noise of the solar wind goes through narrow filters at the notes of the motto: pitch comes out of the noise. The drums go faster by division (1, 2, 3, 4, 6, 8 notes in a beat). One dense chord of all players. |
| 2 | The fusion of hydrogen starts. | The riff of the work comes in behind a filter that opens. A voice counts: "two, one, fire". On "fire", all players start. The riff has no major third yet. |
| 3 | The star burns hydrogen in a stable state. | C: the theme, plain, with a line of the violins. D: the theme again, with a riff of bass guitar and guitar against it; the chords go up. E: a drum-and-bass beat in the same bar of seven, with the motto upside down above it. F: the saxophone and the guitar take turns (four bars each, two, one). G: bass and drums in turns. H: the motto as a canon of the saxophone with a delay. J: the theme at full force (trumpet, alto saxophone, violins); the riff of part 4 crosses the bars of seven, the motto goes up by whole tones in four parts, and the drums go over to four beats. |
| 4 | Spots and flares. | A heavy rock groove in plain 4/4: double pedal kick drum, the low string of the guitar, a guitar solo, a line of all lead players. The key goes up by minor thirds. |
| 5 | The star swells and becomes cooler. | The long pulse becomes the beat of a slow bar. The theme is a chorale in four real voices (trumpet, alto saxophone, trombone, baritone saxophone; then the strings with them), under a reverb that adds the octave above. A solo of the lead synthesizer. The chorale again in G. Then ten bars of build-up on the note D. |
| 6 | Helium starts to burn, all at one time. | The one dubstep passage of the work, as a band plays it: one riff from the motto in a minor key (G, C, D, E-flat) for bass guitar, bass synthesizer and guitar, with the snare drum in half time. The kick drum plays the notes of the riff in its first eight bars and keeps those strokes when the riff gets sixteenth notes: the groove of the drums stays. |
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
| C, bars 9 to 16 | `THEME_LOW_RISE` | Starts low, goes to the high octave (to F5) at its highest phrase, falls two octaves |
| D | `THEME_WIDE`, `THEME_CLOSE_WIDE` | A start from the low D, a leap of an eleventh, an answer two octaves lower, the highest phrase to F5, a fall to the low B |
| H | The motto alone, as a canon with a delay | Low, then one octave higher, then from A, C and D |
| J | `THEME` | Trumpet, alto saxophone and violins; the tenor saxophone one octave lower |
| N, P (part 5) | The chorale, in E-flat and in G | Four voices of the horns and the strings |
| S (part 7) | `THEME_FORCE` (in [`work/agb.py`](../src/gtypestar/work/agb.py)) | Accented low notes, leaps of two octaves, the highest note F5; the trumpet above, to B-flat 5 |
| W (part 8) | The first three notes of the motto | Low and soft |

The tenor saxophone of the audio has no note above F5 (the sound library stops there; a player has notes to C6). No line of the saxophone goes higher: where the music needs higher notes, the trumpet or the alto saxophone has them.

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
| "the arrangement is sloppy and amateurish" | The third version has a plan ([`design/plan.md`](../design/plan.md)). One idea is in front in each passage; bass, chords and riffs are written for their passage; the kick drum plays the low notes of the bass; horns and strings have lines (the violin line of mark C, the four voices of the chorale, the motto in four parts in mark J). A search finds held notes that clash with the bass (`tools/diagnose/clashes.py`). A table shows which stem is in front after each mark (`tools/diagnose/front.py`): it found a held guitar chord that covered the first notes of the chorale. |
| "range issues with instruments … impossible to follow rhythms" | `gtypestar check` now knows the ranges that the instruments really have in the audio (the saxophone had 112 notes with no sound) and the divisions of a pulse that the ear can follow. It had 265 problems; it has none. Where the saxophone cannot play the top of a fast line of all lead players, a whole bar of its line is one octave lower (before: single notes, and the line went up and down in sevenths and ninths). The fast line of mark T has slurs (the tongue started 12 notes in one second for eight bars). A chord of the electric piano that is wider than a tenth is for two hands. `tools/diagnose/playing.py` shows the range, the speed and the leaps of each player. |
| "the electronics could be used better" | Live processing of the band, one idea in each part: see "Live processing" in [`audio.md`](audio.md). The recorded voices are above the band now: 10 of the 13 voices were under the level of the band, and the listener could not get the words. Each voice in a loud passage has more level, and the band goes down a little while it speaks. A voice in the first bar of the flares was under the riff and said a number of the count that comes later: it is gone. |
| "the dubstep section sounds corny" | Part 6 is now one riff from the motto that the band plays; see its row in the table of the parts. |
| "not just arrive at transitions but actually work to transitions" | The riff of D starts in the last bar of C. The riff of part 4 starts four bars before J and crosses its bars; the drums go over to its four beats; the motto goes up to the chord before the new key. The theme starts in the last bar of the ignition. |
| "Explore other samples too for sounds" | A percussion player (shaker, tambourine, congas). A second drum kit for a comparison. |
| "a nice full bodied sound from the guitar that shreds in a jazz metal way" | The solo of the guitar in part 4 (mark L): joined notes, a darker amplifier sound, one octave lower. See [`audio.md`](audio.md), "The guitar". |
| "Can we find better more realistic metal guitar samples or vst or something? This one sounds bad." | No free library is better than the one in use; the player now uses all of it that a real performance needs (pick noise, the sound of a stopped string, nine recordings for each key), and the tone is near real recordings (less "fizz", more of the low string). A second rig (a Peavey 5150 with a real cabinet response) is there for a comparison. See [`audio.md`](audio.md), "The guitar". |
| "Look for better drums while you're at it" | Two more kits that were recorded for metal, and processed samples under the kick drums and the snare drum of the kit. The kit with these layers is the kit of the work; the owner has all five sounds. See [`audio.md`](audio.md), "The drums". |
| "an audio sample of an astronaut swearing over the radio … both funny and tasteful" | The first bar of part 5 (mark N), after the flares: "That son of a bitch was wild." (Eugene Cernan, Apollo 10), then a radio tone. One time. The sentence is in the half bar of rest before the first note of the trumpet, and the last chord of the guitar goes down under it. |

## The recorded sounds

- The oscillations of the Sun, 42 000 times faster (a recording of NASA, and a sound that code makes from the measured frequencies of the modes).
- The radio traffic of the first American flight into space, Mercury-Redstone 3 (1961): "Trajectory okay", the numbers of the force on the pilot ("two G", "five G"), and two countdowns ("two, one, fire").
- One sentence from the lunar module of Apollo 10 (1969). At the separation of its two stages, the module turned over and over for some seconds. Twelve minutes later, Eugene Cernan said: "That son of a bitch was wild." The sentence comes after the flares.
- Plasma waves that Voyager 1 recorded at the edge of the Solar System, and radio waves of Saturn and of the Earth.
- Radio noise, radio tones, and a data signal that code makes.

The staff "Recorded Sounds" of the score has one note for each sound that starts.
See [`audio.md`](audio.md) for the sources and the licences.
