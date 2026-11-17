# The plan of the third version

The owner heard the second version and said (2026-11-16): the material and the ideas are
solid, but "the arrangement is sloppy and amateurish". Instruments are out of range, some
rhythms are "completely impossible to follow", the electronics "could be used better",
the dubstep passage "sounds corny", the motifs need more development, and the music must
"not just arrive at transitions but actually work to transitions". "Everything needs
basically reorganized and planned with purpose." The full words are in `brief.toml`.

This file is the plan. Each rule here has a check or a place in the code.

## What was wrong, in the code

| Fault | Cause |
| --- | --- |
| Notes with no sound | The tenor saxophone of the sound library stops at F5. The second version had 112 higher notes: the top of the theme, the solos, each climax. |
| Arrangement by chance | Bass, electric piano and guitar took a random figure from a short list in each bar. Horns and strings had one chord for each bar, or short chords from a list. No voice had a line of its own. |
| Rhythms that the ear cannot follow | Five notes in each long pulse (mark J), eleven cymbal notes in each half note (mark N), fills with seven notes, a cell of eleven steps across the bars. More than one such device at a time. |
| Transitions as noise | Most changes of part had rising noise, a held chord, or a filter. The music before the change did not move to the music after it. |
| Electronics as decoration | Chords, arpeggios and effects were on top of the band. Nothing in the electronics changed what the band played. |
| The dubstep passage | Six bass sounds that take turns from beat to beat and pieces of the word "fire": the manner of 2011. |

## Rules of the third version

1. **One idea in front.** In each passage one voice has the main idea, one layer answers
   or supports, and the rhythm section carries. The other players rest. The table of each
   part below names these layers.
2. **Composed parts.** Bass lines, chord rhythms and riffs are written for their passage.
   A figure changes when it comes again, but by a decision (a new end, a new register, a
   new player), not by chance.
3. **Section writing.** Horns and strings have lines: unison and octave lines, a melody
   in four parts under the trumpet, counter-melodies that move when the melody holds a
   note. Held chords are for passages where a held chord is the idea.
4. **Ranges.** Each note is inside the range that the instrument really has in the audio
   and that a first-class player uses with ease. The top fifth of a range is for a
   climax, and the line goes there by step or by a prepared leap. `gtypestar check`
   lists each note outside a range.
5. **Rhythm that the ear follows.** The pulse is always clear in one layer. A complex
   device comes alone, above a plain layer. Divisions of a pulse are 2, 3, 4, 6 and 8.
   Five in the time of four comes one time, as the link from the tempo 140 to the tempo
   175, with all players together. `gtypestar check` lists other divisions.
6. **Work to the transition.** The last bars before each change of part take the material
   of the old part to pieces and bring in the rhythm, the key or the sound of the new
   part. Rising noise alone is not a transition.
7. **Electronics that do something to the music.** Each part has one idea of live
   processing of the band, or one idea that makes the recorded sounds a part of the
   harmony or the rhythm.
8. **One sudden pause** (before the dubstep passage), one dubstep passage of 30 seconds
   or less, one sentence with a swear word. As before.

## The motifs

| Name | Notes | Where it comes from |
| --- | --- | --- |
| Motto | G, C, D, E: a fourth up, then two steps | The first intervals of the spectrum of hydrogen |
| Answer | A to G; and E, D, B, A going down | Bars 2 to 4 of the theme |
| Leap | E up to G, then F and D | Bar 6 of the theme: its one note outside the scale |
| Run | Sixteenth notes in the scale of G with five notes | The two fast lines |
| Thirds | The roots G, E-flat, C, A | The chords of the theme |
| Clave | Long, long, short, long, long (3 + 3 + 2 + 3 + 3 eighth notes) | The main metre |

How they change: the motto upside down (the bridge melody), the motto as a riff of the
bass, the motto as four chord roots, the motto in long notes (the chorale), the motto in
short notes (the runs), the answer as a sequence, the thirds as a line of the bass.

## The form

The eight parts and their order stay: they are the life of the star. The bar numbers of
the parts stay too, with two exceptions (marks H and J). What each part is for:

| Part | What the star does | What the music does | In front | Electronics | How it works to the next part |
| --- | --- | --- | --- | --- | --- |
| 1 Nebula | Gas falls together | Pitch comes out of noise: the recorded sounds go through filters that ring on the notes of the motto. Single events come closer and closer. | Recorded sounds, then the electric piano | Resonant filters and a vocoder give the recordings the notes of the motto | The events become the clave; the bass note G grows |
| 2 Ignition | Fusion starts | The clave as a groove. The motto as a riff of all players. | The riff | The first chord, backwards, leads to the start | The riff becomes thin; the saxophone starts the theme before the bar line |
| 3 Main sequence | A long stable state: gravity against pressure | C: the theme, plain. D: the theme against a riff. E: the bar of seven as a breakbeat, with the motto upside down. F: saxophone and guitar in turns. G: bass and drums. H: the motto as a canon of the saxophone with its own echoes. J: the theme at full force; a riff of four beats crosses the bar of seven. | Saxophone; then guitar; then bass | D: the ends of the riff repeat (the band samples itself). E: filter, repeats, a reverse. F: the last note of each turn echoes under the next turn. H: a delay makes the canon | The riff of four beats in J is the metre of part 4: the drums go over to it in the last bars |
| 4 Flares | Magnetic storms | A rock groove in 4/4 with double kick. Riffs of guitar, bass, trombone and baritone saxophone. The guitar solo. | Guitar | Low resolution and ring modulation on the drums in the breaks | The riff gets longer notes (sixteenth, eighth, quarter, half): the dotted quarter of the old tempo is the beat of part 5 |
| 5 Red giant | The star swells and cools | The motto in long notes: a chorale in four real voices. A solo of the lead synthesizer. Then the build-up on D. | Horns and strings; then the synthesizer | A reverb that adds the octave above (a "shimmer") on the chorale | The voice counts the force on the pilot; the low sounds go away; the one pause |
| 6 Helium flash | Helium burns all at once | Bass music in half time, 30 seconds: one riff from the motto for bass guitar, synthesizer bass and guitar together; the real drums play it. | The bass riff | The sound of the bass moves slowly inside each note; the band is cut and repeated at the ends of phrases | Five notes in four beats: the new tempo |
| 7 Last burning and fall | Pulses, then the outer layers go | The theme, the riff and the run at the same time. Then the gravity of the white dwarf pulls all of it down. | All players | The pitch and the tempo of the recording fall; echoes grow | The last chord stays as a frozen sound |
| 8 White dwarf | A small hot rest | The frozen chord gets darker. The motto as single bell notes. "Roger." | Recorded sounds | A frozen sound from the last chord of the band | - |

## Sounds to try

- Drums: the kit *Naked Drums* (Yamaha Recording Custom, ten strokes in each layer).
  The reader is in the code; the owner gets a comparison with the kit of version 2.
- Hand percussion (shaker, tambourine, congas) from a free library, for the grooves.
- A real grand piano for the chorale and the white dwarf.

## The sequence of the work

1. Ranges, the checks of rule 4 and rule 5, tools for section writing.
2. The main sequence (marks C to J). Render, measure, send.
3. The red giant, the helium flash and the build-up before it. Render, measure, send.
4. The flares, the last burning and the fall. Render, measure, send.
5. The nebula, the ignition and the white dwarf with the new electronics. Render, send.
6. The full render, the stems, the score and the parts, the documents.
