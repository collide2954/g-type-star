# Style study

This document gives the style parameters for *G-Type Star*.
The parameters come from the music of the band Sungazer and of five circles of artists around it.
The composition code uses these parameters as its rules.

## Method

The study has three types of data. Each row of a table has a code for its type.

| Code | Type | Meaning |
| --- | --- | --- |
| M | Measured | Code measured audio recordings, score data, or performance data. |
| R | Read | The study team read the source. The column "Source" gives the key of the source. The list of sources is at the end of this document. |
| K | Reference knowledge | The row is standard knowledge, or an estimate. The study team did not read a source for the row. Check the row before you use it for a critical decision. |

The study measured six tracks of the album *Against the Fall of Night* (Sungazer, 2024), which the owner of the project has.
No open score data are available for this music.
Thus the study got its data from the audio:

1. A program divided each track into four stems: drums, bass, other instruments, and voice.
2. Code found the fastest regular pulse of each track, and the strokes of the kick drum, the snare drum, and the cymbals.
3. Code found the notes of the bass and of the other instruments.
4. Code measured the loudness, the tone balance, and the stereo width of each track.

The results are approximations. The study uses them for statistics, not as a score.
The recordings, the stems, and the notes are not in the repository. Only numbers that describe the style are in the repository.

The sourced tables come from seven research tasks (15 November 2026): Sungazer; large-ensemble fusion (Snarky Puppy); live-electronic fusion; progressive and djent fusion; cosmic jazz; the beat scene, IDM, and dubstep; and the science of human feel with the statistics of fast lines.
Two of these tasks also measured open data: the Groove MIDI Dataset (drummers) and the Weimar Jazz Database (solos).

## Main results

1. The reference tracks are loud and dense: -9.6 to -12.7 LUFS, and 53 to 77 percent of the time at the full level.
   The contrast comes from quiet parts and from short stops of the full band (0.6 to 2.3 stops in a minute).
2. The bars of the drums are almost never the same two times.
   In five of six tracks, a bar of kick and snare is the same as the bar before it in 0 to 15 percent of the bars.
3. The drummer is exact, but not a machine: the strokes of one drum have a spread of 8 to 12 ms against the pulse.
4. The metres are cycles of a fast pulse: 15 pulses (Whalefall), 12 (Skrontch), 10 (Whisky and Mes), 5 and 25 (Paydushko Horo).
   A track keeps its pulse and changes the grouping: Whalefall has 5 groups of 3 pulses, then 3 groups of 5.
   The sources give the same fact: a change of tempo by the ratio 5 to 3.
5. The bass is low and short: one third to one half of its notes are below A1, and the median note has 0.13 to 0.16 seconds.
6. The mix has the drums and the other instruments at the same loudness (4.2 LU below the mix), and the bass 2.7 LU below them.
7. The model track "Cool 7" has seven quarter notes in a bar, as four long pulses and one short pulse.
   Half way through its melody, each long pulse gets five notes and the short pulse gets three.
8. The melodies of the band are slow and in the scale, above chords that are complex: "Drunk" has 3.27 beats for each melody note.
9. Published measurements give the size of human timing: a soloist is behind the beat by about 9 percent of a beat on the beats and on the grid between them; a ghost note has 0.28 of the key velocity of a backbeat.
10. Fast lines of fusion players have 8.2 notes in a second (median) and 12.2 (90th percentile). Sixteenth notes at the main tempo of the work have 11.7.
