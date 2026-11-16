# The audio

This document says where each sound of *G-Type Star* comes from, how the mix and the master work, and how the sound is checked against the reference recordings.

## The sources of sound

| Player | Source | Where it runs |
| --- | --- | --- |
| Drums | Samples of a real kit with all its microphones: CrocellKit (DrumGizmo). If it is not there: DRSKit. The code plays the hits ([`audio/kit.py`](../src/gtypestar/audio/kit.py)). | Each computer (the code downloads the kit) |
| Bass guitar | Samples of a five-string bass, the direct signal of the pickup: Karoryfer *Black And Blue Basses*. An amplifier model of the project comes after them. | Each computer |
| Electric piano | Samples of a 1977 Rhodes Mark I: *jRhodes3d* by Jeff Learman | Each computer |
| Guitar (8 strings) | A model of a plucked string and a model of an amplifier with its loudspeaker cabinet ([`audio/amp.py`](../src/gtypestar/audio/amp.py)). The rhythm tones are played two times, left and right. | Each computer |
| Synthesizers, chip synthesizer, synthesizer bass, drum machine | Code: oscillators, filters, frequency modulation ([`audio/synth.py`](../src/gtypestar/audio/synth.py), [`audio/drumsynth.py`](../src/gtypestar/audio/drumsynth.py), [`audio/dubstep.py`](../src/gtypestar/audio/dubstep.py)) | Each computer |
| Tenor saxophone, horns, strings | MuseScore Studio with Muse Sounds ([`audio/musestems.py`](../src/gtypestar/audio/musestems.py)). On a computer with no Muse Sounds, synthesizer patches play these parts (`--no-muse`). | A computer with MuseScore Studio and Muse Sounds |
| Recorded sounds | Public recordings of space and of space flight, and sounds that code makes from physical values ([`audio/tape.py`](../src/gtypestar/audio/tape.py)) | Each computer |

Muse Sounds are free sample libraries of Muse Group, but they are not open: only MuseScore Studio can play them, and a build server cannot install them.

## The steps of a render

1. The performance layer changes the written music into events with times in seconds. Each player gets small shifts of time and loudness (the "feel"): the measured timing spread of the reference drums is 8 to 12 ms.
2. Each player gets its sound. The result is one file for each instrument group (a stem).
3. The changes of the recording itself (a repeated slice, a filter that opens, the fall of pitch at the end) are applied to the stems ([`audio/glitch.py`](../src/gtypestar/audio/glitch.py)).
4. The mixer makes the mix ([`audio/console.py`](../src/gtypestar/audio/console.py), settings in [`work/mix.py`](../src/gtypestar/work/mix.py)).
5. The master gives the mix the tone balance and the loudness of the reference recordings.

The full work is rendered in parts of about 40 seconds, three at the same time.
The levels of the groups come from one passage with all players (the second statement of the theme): all parts use the same levels.

## The mix

- Each stem has a channel strip: filters, saturation, compression, width, place between left and right, and the share that goes to each space (room, plate, hall, echo).
- The strips go into four groups: drums, bass, music, and space.
- The mixer sets the loudness of the groups to the mean of the separated stems of the reference tracks: drums -4.2 LU, bass -6.9 LU, music -4.2 LU relative to the full mix.
- The drum group has a copy with strong compression under it. That copy has no high frequencies, and the microphones of the cymbals do not go through it.
- The kick drum makes the bass and the chords softer for a short time at each stroke.

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
| The guitar tone was thin and sharp | With high gain, the bands from 90 to 700 Hz were 17 to 23 dB under the band from 1.4 to 5.6 kHz | The cabinet model has a resonance at 140 Hz and a falling slope above 450 Hz; the amplifier has no cut of the middle |
| The bass had too much middle | 5 to 9 dB more level from 180 Hz to 2.8 kHz than the bass stems of the references, 4 dB less below 45 Hz | More level below 95 Hz, less from 240 Hz up |
| The kick drum was too low | 2.7 dB more level from 20 to 45 Hz than the drum stems of the references | High-pass filter at 40 Hz; more level at 80 and 130 Hz |
| The drums had too much low middle | 3.4 dB more from 180 to 355 Hz | Less level of the snare drum near 210 and 550 Hz |

## Credits

| Sound | Source | Licence |
| --- | --- | --- |
| Drums | CrocellKit and DRSKit. Drum samples: DrumGizmo.org | CC BY 4.0 |
| Bass guitar | Karoryfer Samples, *Black And Blue Basses* | CC0 1.0 |
| Electric piano | *jRhodes3d* by Jeff Learman | Free for use in music; the samples themselves are CC BY-NC and are not in this repository |
| Saxophone, horns, strings | Muse Sounds (Muse Group), played by MuseScore Studio | Free to use in music; not open |
| The sound of the Sun | NASA, "Sounds of the Sun": data of the Solar and Heliospheric Observatory (ESA and NASA), sonification by A. Kosovichev, Stanford Experimental Physics Lab | NASA media guidelines |
| Voices | Radio traffic of the flight Mercury-Redstone 3 (NASA, 1961), from the Internet Archive | Public Domain Mark 1.0 |
| Plasma waves of Voyager 1, of Cassini, and of the Earth | Original space audio recordings provided courtesy of NASA and The University of Iowa. https://space-audio.org/ | CC BY 4.0 |

No sample file and no recording is in this repository. The code downloads the free files into the directory `.cache`.
