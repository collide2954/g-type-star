# The audio

This document says where each sound of *G-Type Star* comes from, how the mix and the master work, and how the sound is checked against the reference recordings.

## The sources of sound

| Player | Source | Where it runs |
| --- | --- | --- |
| Drums | Samples of a real kit with all its microphones: CrocellKit (DrumGizmo). Under each stroke of the kick drums and of the snare drum, a processed sample plays at about the level of the microphones: *The Metal Kick Drum* (see "The drums"). If the kit is not there: DRSKit. The code plays the hits ([`audio/kit.py`](../src/gtypestar/audio/kit.py)). For a comparison, the code can also play other kits: set the environment variable `GTYPESTAR_KIT` to `crocell` (no layers), `naked`, `muldjord` or `aasimonster`. | Each computer (the code downloads the kit and the layers) |
| Percussion (shaker, tambourine, congas) | Samples of real instruments: the *Versilian Community Sample Library*. The code plays the strokes ([`audio/perc.py`](../src/gtypestar/audio/perc.py)); the shaker takes the move away and the move back in turn. | Each computer (the code downloads the samples) |
| Bass guitar | Samples of a five-string bass, the direct signal of the pickup: Karoryfer *Black And Blue Basses*. An amplifier model of the project comes after them. | Each computer |
| Electric piano | Samples of a 1977 Rhodes Mark I: *jRhodes3d* by Jeff Learman | Each computer |
| Guitar (8 strings) | Recordings of a real guitar, note by note (the direct signal of the pickup): the library *METAL-GTX* of Unreal Instruments. Then a model of a real amplifier with its cabinet and microphone, from the Neural Amp Modeler project ([`audio/guitar.py`](../src/gtypestar/audio/guitar.py), [`audio/nam.py`](../src/gtypestar/audio/nam.py)). The two rhythm guitars, left and right, are two different recordings of each note. If the library is not there: a model of a plucked string and of an amplifier ([`audio/amp.py`](../src/gtypestar/audio/amp.py)). | Each computer (the code downloads the library and the models) |
| Synthesizers, chip synthesizer, synthesizer bass, drum machine | Code: oscillators, filters, frequency modulation ([`audio/synth.py`](../src/gtypestar/audio/synth.py), [`audio/drumsynth.py`](../src/gtypestar/audio/drumsynth.py), [`audio/dubstep.py`](../src/gtypestar/audio/dubstep.py)) | Each computer |
| Tenor saxophone, horns, strings | MuseScore Studio with Muse Sounds ([`audio/musestems.py`](../src/gtypestar/audio/musestems.py)). On a computer with no Muse Sounds, synthesizer patches play these parts (`--no-muse`). | A computer with MuseScore Studio and Muse Sounds |
| Recorded sounds | Public recordings of space and of space flight, and sounds that code makes from physical values ([`audio/tape.py`](../src/gtypestar/audio/tape.py)) | Each computer |

Muse Sounds are free sample libraries of Muse Group, but they are not open: only MuseScore Studio can play them, and a build server cannot install them.

## The guitar

The first guitar of the project was all code: a model of a plucked string and a simple model of an amplifier. An audio model that compares sound with descriptions in words gave it these values, and the new guitar these (the same riff, the guitar alone; larger is nearer to the description):

| Description | String model | Recorded guitar and amplifier model |
| --- | --- | --- |
| "heavy metal rhythm guitar with palm muted riff" | 28 | 66 |
| "a real electric guitar through a tube amplifier" | 9 | 38 |
| "cheap MIDI guitar sound" | 21 | 2 |

How the new guitar works:

1. Each note is a recording from the library: an open note or a note with the palm of the hand on the strings. Fast notes get down strokes and up strokes of the pick in turn. A note does not get the same take two times one after the other. The notes of a chord start a little one after the other.
2. The sum of the notes is the signal of the pickup. A filter cuts its low end and makes its middle louder, as an overdrive pedal in front of a heavy amplifier.
3. A neural network that was trained with recordings of a real amplifier does to this signal what that amplifier did ([`audio/nam.py`](../src/gtypestar/audio/nam.py)). The tool `tools/diagnose/nam_check.py` compares this code with the reference code of the Neural Amp Modeler project: the largest difference is 0.000001.
4. Filters after the amplifier bring the middle forward: the captured cabinet has less level there than the instruments of the reference tracks.

| Tone in the score | Amplifier |
| --- | --- |
| clean | Bugera 333, clean channel, with cabinet |
| crunch | Bugera 6262, crunch channel, with cabinet |
| high gain | Bugera 6262, lead channel, with cabinet |
| lead | Marshall JVM, channel OD2, with cabinet |

The lead tone is for the solo lines. The owner heard the first version and said that it was "unconvincing and tinny": the solo was in the highest octave of the guitar, each note had a stroke of the pick, and the amplifier gave much level from 2.8 to 5.6 kHz. The changes:

- The notes of a fast run under a slur join: only the first note has a stroke of the pick. The other notes start inside the recording, after its attack, and the pitch goes from the note before in 30 ms (hammer-on and pull-off).
- A low-pass filter before the amplifier (as the tone control of the guitar) and filters after it give a darker sound with more body.
- Soft echoes, left and right. A wider vibrato on long notes.
- The solo of part 4 is one octave lower.

The script `tools/diagnose/guitar_alone.py` writes the guitar part of some bars with no other player.

### After the third version: "This one sounds bad"

The owner heard version 3.3 and asked for a better, more real metal guitar. Two searches gave the same answer: no free library is better than METAL-GTX for a guitar with eight strings. What was wrong was the way the project used it, and the tone. Real recordings were the measure: public examples of real distorted guitars (Wikimedia Commons; they stay in `.cache/reference/guitar`). `tools/diagnose/guitar_lab.py` shows the tone of a rig next to them, and `tools/diagnose/judge.py` shows how near a sound is to them for an audio model.

| What was wrong | Measured | Change |
| --- | --- | --- |
| The gaps between the notes of a riff were silent: no player sounds like that. | Between two palm-muted notes the level fell by 30 to 55 dB. | The player uses what the library has for this: the noise of the pick a little before each stroke, the sound of the hand that stops a string ("release"), and nine recordings for each key (the three takes of the key and of the two keys next to it), with a random loudness. The numbers are from the SFZ program of the library. |
| "Fizz": too much level in the high range. | 6 dB more from 4 to 6 kHz and 12 dB more from 6 to 9 kHz than a real double-tracked metal guitar. A real cabinet has almost no sound above 6 kHz. | A low-pass filter at 5 kHz and a cut at 4 kHz after the amplifier. |
| Too little weight of the low string. | 7 dB less below 120 Hz. | The filter before the amplifier is at 80 Hz (before: 110 Hz); a low shelf after it. |
| Too much low middle. | 3 dB more from 250 Hz to 1 kHz. | No boost at 800 Hz; a cut at 450 Hz. |

The same riff, the two rhythm guitars alone (the last column: the mean of the largest similarities to the real recordings; a real recording against the others has 1.0 by definition):

| Version | "real - fake", sum of five pairs | Near the real recordings |
| --- | --- | --- |
| Version 3.3 | 54 | 0.81 |
| With the pick noise, the releases, nine recordings | 60 | 0.89 |
| With the new tone | 71 | 0.91 |
| Real recordings | 56 to 105 | 1.0 |

A model of an amplifier with no cabinet can have the response of a real cabinet (`Rig.cabinet`, a file in `.cache/models/ir`). The comparison had a Peavey 5150 with a boost pedal (capture: Helga B) and "God's Cab", the responses of a Mesa cabinet of 4 x 12 inches with a Shure SM57. For the audio model this rig is as near to the real recordings as the retuned rig (0.91 against 0.93 on the amplifier test), so the choice is for the ears of the owner. The retuned rig is the rig of the work; the environment variable `GTYPESTAR_GUITAR=5150` selects the second set (the same level in the mix).

A complete SFZ player would play all of the library as its makers planned it (real hammer-on and slide samples, key switches). The package `pysfizz` is such a player; the session could not install it without the permission of the owner.

The distortion of an amplifier is a compressor: after it, a soft stroke is almost as loud as a hard stroke. In the third version, a held chord with the mark *mezzo forte* and a hairpin to *pianissimo* stayed at full level for six seconds, above the first notes of the horn chorale (mark N). Now a fader after the amplifier follows the written loudness (`band.fader`), as the volume control of the player or the hand of the engineer does: 24 dB between the loudness values 0 and 1 for the high gain tone, 10 dB for the crunch tone. The build-up before the helium flash and the fall at the end of part 7 have a real change of the loudness of the guitar because of this.

## The drums

The owner: "The drums are acceptable" (second version), then "Look for better drums". The measure here is the drum stem of each reference track (separated by a model), and the same audio model as for the guitar. The drums alone, as the mix has them, on two passages (the groove of mark D and the fast kick drums of the flares; `tools/diagnose/drums_alone.py`):

| Kit | Near the reference drums: groove | Fast kick drums |
| --- | --- | --- |
| A: CrocellKit (versions 1 to 3.3) | 0.86 | 0.88 |
| B: Naked Drums | 0.89 | 0.91 |
| C: MuldjordKit | 0.87 | 0.92 |
| D: Aasimonster | 0.89 | 0.93 |
| E: CrocellKit with layers | 0.90 | 0.91 |

- **C and D** are kits of DrumGizmo that were recorded for metal. Each kick drum has a microphone and a trigger: the MuldjordKit has the click of the trigger as a channel, the Aasimonster has a drum module that plays a kick sample (the code moves it 10 ms earlier, in time with the microphone). The Aasimonster has the most recordings (93 strokes of the snare drum, rim shots, three closed hi-hats). It has no cross-stick and no hi-hat pedal: the CrocellKit plays these two (`KitSpec.borrowed`).
- **E** is what a metal production does: a clean, short, processed sample under each stroke of the kick drum and of the snare drum ("sample reinforcement"). The samples are from *The Metal Kick Drum*: the kick "Fate" (0.2 seconds, little level below 60 Hz) and a snare drum of 14 x 6 inches with eight layers of loudness. A layer is about as loud as the microphones of its drum; a ghost note has no layer. E is the kit of the work now: it keeps all sounds of the kit that the mix was made for.
- In the full mix (the flares), the new guitar with E is nearer to the reference tracks than version 3.3 (0.93 against 0.89), and so is the new guitar with D (0.92).

## The steps of a render

1. The performance layer changes the written music into events with times in seconds. Each player gets small shifts of time and loudness (the "feel"): the measured timing spread of the reference drums is 8 to 12 ms.
2. Each player gets its sound. The result is one file for each instrument group (a stem).
3. The changes of the recording itself (a repeated slice, a filter that opens, the fall of pitch at the end) are applied to the stems ([`audio/glitch.py`](../src/gtypestar/audio/glitch.py)).
4. The mixer makes the mix ([`audio/console.py`](../src/gtypestar/audio/console.py), settings in [`work/mix.py`](../src/gtypestar/work/mix.py)).
5. The master gives the mix the tone balance and the loudness of the reference recordings.

The full work is rendered in parts of about 40 seconds, two at the same time.
The levels of the groups come from one passage with all players (the second statement of the theme): all parts use the same levels.

## Live processing

These are the changes of step 3: what a player or an engineer does to the sound of the band with a pedal or with the recording. The score shows each of them on the staff "Recorded Sounds".

| Kind | What it does | Where |
| --- | --- | --- |
| Echo | The sound of a passage comes again after one long pulse, some times, each time softer. | The canon of the motto (mark H): the notes of the saxophone sound together as a chord. The last note of each solo turn (mark F). |
| Repeat ("stutter") | A short piece of the band comes again, two or more times. | The ends of the riff passages (marks D and E), and three places of the dubstep passage. |
| Reverse | One beat plays backwards. | The end of the bridge melody (mark E), bar 12 of the dubstep passage. |
| Filter that opens | The sound starts dull and becomes bright. | The riff of the ignition, the drums at the start of mark E, the chords of the build-up. |
| Gate | Chords are cut into eighth notes. | The last two bars of mark E. |
| Low resolution | The sound has few bits and a low sample rate, as a digital radio link with errors. | The flares, three times: the last two beats of the drums before the gallop, before the turns, and before the climb. Each time the resolution is lower. |
| Reverb with the octave above ("shimmer") | A long room whose sound is one octave higher than the horns and strings that go in. | The chorale (mark N). |
| Held sound ("freeze") | One moment of a chord goes on as a sound that does not move. | The electric piano in the white dwarf. |
| Ringing filters | Noise goes through narrow filters at the notes of the motto: the noise gets pitch. | The solar wind in the nebula. |
| Fall of pitch, narrow, dark | The pitch of the recording falls with no change of the time, the sound moves to the centre, a filter closes. | The fall (mark V) and the white dwarf. |
| Silence | All players stop; the recorded voice goes on. | One time: before the dubstep passage. |

## The mix

- Each stem has a channel strip: filters, saturation, compression, width, place between left and right, and the share that goes to each space (room, plate, hall, echo).
- The strips go into four groups: drums, bass, music, and space.
- The mixer sets the loudness of the groups to the mean of the separated stems of the reference tracks: drums -4.2 LU, bass -6.9 LU, music -4.2 LU relative to the full mix.
- The drum group has a copy with strong compression under it. That copy has no high frequencies, and the microphones of the cymbals do not go through it.
- The kick drum makes the bass and the chords softer for a short time at each stroke.
- A recorded voice with words brings all other sounds down by 3 or 4 dB while it speaks (`Cue.duck_db`). A voice on a radio has a narrow band of frequencies (300 to 3400 Hz), and a guitar covers it: in the third version, 10 of the 13 voices were under the level of the band in that range, some of them by 12 dB. `tools/diagnose/voices.py` shows the level of each voice against the band.

## The master

1. Tone: a filter moves the long-term tone balance of the mix to that of the six reference masters, from 30 Hz to 16 kHz, not more than 6 dB in one band.
2. Glue: a slow compressor with a small ratio.
3. Loudness: a soft clip and a limiter bring the master to -10.5 LUFS (the references: -9.6 to -12.7 LUFS).

## How the sound is checked

The writer of the code cannot hear. Each render is measured against the reference recordings (see [`research/README.md`](../research/README.md) for the tools).

- `uv run gtypestar compare FILE`: loudness, loudness range, crest factor, stereo width, and the tone balance in third-octave bands.
- `tools/tone.py`: the tone balance of each part of the work, and the separated stems of the render against the separated stems of the references.
- `tools/diagnose/mixlab.py`: each group of the mix against the reference stems, for some bars.
- `tools/listen.py`: an audio model (CLAP) says how near each ten seconds are to the references.
- `tools/diagnose/pauses.py` and `seams.py`: the pauses and the level at each change of part.
- `tools/diagnose/front.py`: the stems that are in front after each rehearsal mark (the level between 250 Hz and 6 kHz). `tools/diagnose/part_stems.py` makes the stems of some parts for this, with no full render.
- `tools/diagnose/voices.py`: the level of each recorded voice against the band.
- `tools/diagnose/silent_notes.py`: the notes of the saxophone that have no sound, or almost no sound, in the stem of MuseScore. In version 3.2 it found four notes in the canon of the motto (mark H): a G4 after another note under a slur, at a soft dynamic, is 10 to 13 dB under its level in the sound library. The stem of a solo player now gets its weak notes at the level of the others (`musestems.even`), as an engineer does by hand.
- `tools/diagnose/pulse.py`: how clear the pulse of each part is (the autocorrelation of the onset curve), against the reference recordings.
- `tools/diagnose/judge.py`: a comparison of candidates for one sound (a guitar, a drum kit): pairs of descriptions ("a real electric guitar played by a guitarist" against "a fake guitar from a keyboard"), and the similarity to real recordings of the instrument.
- `tools/diagnose/guitar_lab.py`: settings of the guitar amplifier on one passage, with the tone of real recordings next to them. `tools/diagnose/drums_alone.py`: one drum kit on some bars, as the mix has it.

The owner of the project is the last judge: the tools only find what a number can show.

### What the first master got wrong

The owner heard the first full render and said: "The EQ is also a problem".
The long-term tone balance of that master was correct from 40 Hz to 8 kHz, because the master filter makes it so.
The measurements in more detail found these faults, which one mean curve does not show:

| Fault of the first master | Measured value | Change |
| --- | --- | --- |
| Too much level above 11 kHz | 9 dB more than the references; 61% of all windows of three seconds were above their range | The strong compression of the drum group made the cymbals louder. The cymbal microphones now have their own group with no such compression, and a low-pass filter at 11.5 kHz. The master filter now works to 16 kHz. |
| The electric piano was almost not there | 19 dB under the saxophone | 9.5 dB more level, some saturation |
| The music group had no body | 10 dB less level from 180 to 355 Hz than the stem "other" of the references | Lower high-pass filters; no cuts near 350 Hz |
| The guitar tone was thin and sharp | With high gain, the bands from 90 to 700 Hz were 17 to 23 dB under the band from 1.4 to 5.6 kHz | First: a new cabinet model. Then the owner heard it and said: "the guitar is really bad. Look for samples or VST or something." The guitar is now a recorded guitar through a model of a real amplifier (see "The guitar"). |
| The bass had too much middle | 5 to 9 dB more level from 180 Hz to 2.8 kHz than the bass stems of the references, 4 dB less below 45 Hz | More level below 95 Hz, less from 240 Hz up |
| The kick drum was too low | 2.7 dB more level from 20 to 45 Hz than the drum stems of the references | High-pass filter at 40 Hz; more level at 80 and 130 Hz |
| The drums had too much low middle | 3.4 dB more from 180 to 355 Hz | Less level of the snare drum near 210 and 550 Hz |

The first master also had three faults at the places where two parts of the render meet (each 40 seconds or less, at the rehearsal marks):

| Fault of the first master | Change |
| --- | --- |
| The saxophone, the horns and the strings were two times as loud for about six seconds after each such place: their sound was in two parts of the render. | Each part gets the piece of these stems from its first bar to its last bar only. |
| A note that a player started a little before such a place (within 0.05 seconds) sounded two times. | Such a note is in the next part only. |
| A long recorded sound (the sound of the Sun: 66 seconds) stopped at the end of the part in which it started. | A long sound goes through all parts that it overlaps. |

The tests in `tests/test_render.py` and `tests/test_tape.py` check these three items.

## Credits

| Sound | Source | Licence |
| --- | --- | --- |
| Drums | CrocellKit and DRSKit. Drum samples: DrumGizmo.org | CC BY 4.0 |
| Layers under kick and snare | *The Metal Kick Drum* (TMKD), Rafa Prieto, https://www.themetalkickdrum.com | Free; the maker keeps the copyright; "You are allowed to use these samples for any artistic application"; no copy of the collection in a different place |
| Drums, for a comparison | MuldjordKit and Aasimonster. Drum samples: DrumGizmo.org | CC BY 4.0 |
| Guitar cabinet, for a comparison | "God's Cab 1.4", Signals Audio / Wilkinson Audio (a copy in the Internet Archive; the site of the maker is gone) | Free ("It's free"); no licence text |
| Drums, for a comparison | *Naked Drums*, Wilkinson Audio (SFZ version: kinwie), https://github.com/sfzinstruments/WilkinsonAudio.NakedDrums | CC BY 4.0 |
| Percussion | Versilian Studios, *Versilian Community Sample Library* (https://github.com/sgossner/VCSL) | CC0 1.0 |
| Bass guitar | Karoryfer Samples, *Black And Blue Basses* | CC0 1.0 |
| Guitar | Unreal Instruments, *METAL-GTX* (https://unreal-instruments.wixsite.com/unreal-instruments/metal-gtx) | "License free. No credit notation required." (its manual) |
| Guitar amplifiers | Captures by Phillipe P of a Bugera 6262, a Bugera 333 and a Marshall JVM with cabinet, from the collection of the Neural Amp Modeler community (https://github.com/pelennor2170/NAM_models) | GPL 3.0 (the model files; they are not in this repository) |
| Electric piano | *jRhodes3d* by Jeff Learman | Free for use in music; the samples themselves are CC BY-NC and are not in this repository |
| Saxophone, horns, strings | Muse Sounds (Muse Group), played by MuseScore Studio | Free to use in music; not open |
| The sound of the Sun | NASA, "Sounds of the Sun": data of the Solar and Heliospheric Observatory (ESA and NASA), sonification by A. Kosovichev, Stanford Experimental Physics Lab | NASA media guidelines |
| Voices | Radio traffic of the flight Mercury-Redstone 3 (NASA, 1961), from the Internet Archive | Public Domain Mark 1.0 |
| One voice | The voice recorder of the lunar module of Apollo 10 (NASA, 1969), from the Apollo Flight Journal (https://apollojournals.org/afj/ap10fj/); clip: John Stoll, NASA Johnson | Public domain (NASA) |
| Plasma waves of Voyager 1, of Cassini, and of the Earth | Original space audio recordings provided courtesy of NASA and The University of Iowa. https://space-audio.org/ | CC BY 4.0 |

No sample file and no recording is in this repository. The code downloads the free files into the directory `.cache`.
