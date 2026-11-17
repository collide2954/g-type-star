"""Write the conductor score and the parts as LilyPond files."""

from __future__ import annotations

import bisect
from collections import Counter
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path

from . import drums, music, techniques
from .pitch import Interval
from .structure import Bar, global_to_lilypond
from .work import Instrument, Player, Work

LILYPOND_VERSION = "2.26.0"

FAMILY_ORDER = ["horns", "synths", "rhythm", "strings", "media"]

# The players with no pitch. The name of the first "instrument" of the player gives
# the kind of staff: a drum staff with its table of drums, or the staff of the
# recorded sounds.
DRUM_STAVES: dict[str, tuple[list[drums.Drum], str]] = {
    "drum kit": (drums.KIT, "gts-kit-style"),
    "drum machine": (drums.MACHINE, "gts-machine-style"),
    "hand percussion": (drums.PERCUSSION, "gts-percussion-style"),
}
TAPE = "tape"

STYLE = r"""
% Style of G-Type Star. The build code writes this file.

#(define-markup-command (rehearsal layout props text) (markup?)
   "A rehearsal mark: a bold letter in a box."
   (interpret-markup layout props
     (markup #:box #:pad-markup 0.4 #:bold #:fontsize 2 text)))

#(define-markup-command (tempochange layout props text) (markup?)
   "A gradual change of tempo, for example rit."
   (interpret-markup layout props
     (markup #:normal-text #:italic #:fontsize 1 text)))

#(define-markup-command (instrumentchange layout props text) (markup?)
   "A change of instrument for one player."
   (interpret-markup layout props
     (markup #:box #:pad-markup 0.3 #:fontsize -1 text)))

% The drum kit: the head and the place of each drum on the staff.
% (0 = the middle line; 1 = one place higher.)
#(define gts-kit-style
   '((bassdrum () #f -3)
     (acousticbassdrum () #f -4)
     (pedalhihat cross #f -5)
     (snare () #f 1)
     (sidestick cross #f 1)
     (hihat cross #f 5)
     (openhihat cross open 5)
     (ridecymbal cross #f 4)
     (ridebell diamond #f 4)
     (crashcymbal cross #f 6)
     (crashcymbala cross #f 7)
     (chinesecymbal xcircle #f 6)
     (splashcymbal diamond #f 6)
     (hightom () #f 3)
     (himidtom () #f 2)
     (highfloortom () #f -1)
     (lowfloortom () #f -2)))

% The drum machine. The long sounds (riser, fall, impact) have a text in the music.
#(define gts-machine-style
   '((bassdrum () #f -3)
     (acousticbassdrum diamond #f -5)
     (snare () #f 1)
     (handclap triangle #f 1)
     (sidestick cross #f 1)
     (hihat cross #f 5)
     (openhihat cross open 5)
     (lowmidtom () #f -1)
     (cowbell triangle #f 3)
     (mutecuica slash #f 0)
     (opencuica slash #f 0)
     (tambourine xcircle #f 0)
     (maracas cross #f 3)
     (lowtom () #f -4)
     (electricsnare diamond #f 1)
     (acousticsnare () #f 2)
     (ridecymbal xcircle #f 6)))

% Hand percussion.
#(define gts-percussion-style
   '((maracas cross #f 5)
     (tambourine xcircle #f 3)
     (cabasa cross #f 4)
     (cowbell triangle #f 2)
     (openhiconga () #f 0)
     (mutehiconga cross #f 0)
     (loconga () #f -2)
     (hibongo () #f 2)
     (lobongo () #f 1)))

% Dynamic marks that LilyPond does not have.
sffz = #(make-dynamic-script "sffz")
sfpp = #(make-dynamic-script "sfpp")
ffp = #(make-dynamic-script "ffp")
pf = #(make-dynamic-script "pf")
"""

SCORE_LAYOUT = r"""
\layout {
  \context {
    \Score
    \override BarNumber.font-size = #0
    \override BarNumber.padding = #1.5
    \override MetronomeMark.font-size = #2
    \override MetronomeMark.padding = #2.5
    \override RehearsalMark.padding = #3
    \override InstrumentName.self-alignment-X = #RIGHT
    \override InstrumentName.padding = #0.8
    \override Hairpin.minimum-length = #5
    \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/16)
    skipBars = ##f
  }
  \context {
    \Staff
    \RemoveEmptyStaves
    \override VerticalAxisGroup.remove-first = ##f
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
  \context {
    \DrumStaff
    \RemoveEmptyStaves
    \consists Merge_rests_engraver
    \override VerticalAxisGroup.remove-first = ##f
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
  \context {
    \RhythmicStaff
    \RemoveEmptyStaves
    \override VerticalAxisGroup.remove-first = ##f
    \override TextScript.font-size = #-1
    \override NoteHead.style = #'cross
  }
  \context {
    \PianoStaff
    \override InstrumentName.self-alignment-X = #RIGHT
  }
}
"""

PART_LAYOUT = r"""
\layout {
  \context {
    \Score
    \override BarNumber.font-size = #-1
    \override MetronomeMark.font-size = #1.5
    \override MetronomeMark.padding = #2.5
    \override RehearsalMark.padding = #2.5
    \override MultiMeasureRest.expand-limit = #1
    \override Hairpin.minimum-length = #5
    \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/16)
    skipBars = ##t
  }
  \context {
    \Staff
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
    % A page turn is permitted where the player has a rest of two bars or more.
    \consists Page_turn_engraver
    pageTurnMinimumRestLength = #2
  }
  \context {
    \DrumStaff
    \consists Merge_rests_engraver
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
    \consists Page_turn_engraver
    pageTurnMinimumRestLength = #2
  }
  \context {
    \RhythmicStaff
    \override TextScript.font-size = #-0.5
    \override NoteHead.style = #'cross
    \consists Page_turn_engraver
    pageTurnMinimumRestLength = #2
  }
}
"""

SCORE_PAPER = r"""
\paper {
  #(set-paper-size "11x17")
  top-margin = 12\mm
  bottom-margin = 12\mm
  left-margin = 14\mm
  right-margin = 12\mm
  indent = 28\mm
  short-indent = 14\mm
  system-separator-markup = \slashSeparator
  ragged-last-bottom = ##f
  print-page-number = ##t
}
"""

PART_PAPER = r"""
\paper {
  #(set-paper-size "arch a")
  top-margin = 12\mm
  bottom-margin = 14\mm
  left-margin = 14\mm
  right-margin = 14\mm
  indent = 0\mm
  ragged-last-bottom = ##t
  print-page-number = ##t
  page-breaking = #ly:page-turn-breaking
}
"""


def identifier(player_id: str) -> str:
    """Return a LilyPond variable name for a player (letters only)."""
    letters = "".join(
        chr(ord("A") + int(char) - 1) if char.isdigit() else char for char in player_id
    )
    return "music" + letters[0].upper() + letters[1:].replace(".", "")


@dataclass
class _Emitter:
    """Write the music of one player. The interval changes when the player changes instrument."""

    work: Work
    for_part: bool
    left_hand: bool = False
    interval: Interval | None = None
    # A drum staff: the drum of each note number. The notes become names of drums.
    drums: dict[int, drums.Drum] = field(default_factory=dict)
    labelled: str = ""  # the last drum that got a text
    tied: bool = False  # the note before has a tie

    def drum_note(self, element: music.Note) -> str:
        """Write a note of a drum staff: the names of the drums in place of the pitches."""
        names = []
        label = ""
        for note_pitch in element.pitches:
            drum = self.drums.get(round(note_pitch.pitch.midi))
            if drum is None:
                raise ValueError(f"the note {note_pitch.pitch.name} is not a drum of this staff")
            ghost = "\\parenthesize " if drum.ghost else ""
            names.append(ghost + drum.lilypond + music._posts_text(note_pitch.posts))
            label = label or drum.text
        core = "<" + " ".join(names) + ">" if element.chord else names[0]
        posts = music._posts_text(element.posts)
        if label and label != self.labelled and not self.tied:
            posts += f'^"{label}"'
        if not self.tied:
            self.labelled = label
        self.tied = any(post.kind == "tie" for post in element.posts)
        return core + element.duration_text + posts

    def set_instrument(self, instrument: Instrument | None) -> None:
        if instrument is None:
            self.interval = None
        else:
            self.interval = instrument.part_interval if self.for_part else instrument.score_interval

    def clef_of(self, instrument: Instrument | None) -> str:
        if instrument is None:
            return "percussion"
        clef = instrument.clef if self.for_part else instrument.score_clef
        if clef == "grand":
            return "bass" if self.left_hand else "treble"
        return clef

    def emit(self, elements: list[music.Element]) -> str:
        parts = []
        for element in _merge_full_bar_rests(elements):
            if isinstance(element, music.Command) and element.name == "switch":
                name = element.arguments[0].strip('"')
                instrument = self.work.orchestra.instruments.get(name)
                self.set_instrument(instrument)
                label = name[0].upper() + name[1:]
                parts.append(
                    f'\\clef {self.clef_of(instrument)} <>^\\markup \\instrumentchange "{label}"'
                )
            elif isinstance(element, music.Group) and element.kind == "parallel":
                voices = [f"{{ {self.emit(child.children)} }}" for child in element.children]
                parts.append("<< " + " \\\\ ".join(voices) + " >>")
            elif isinstance(element, music.Group):
                inner = self.emit(element.children)
                prefix = f"{element.header} " if element.kind != "sequence" else ""
                parts.append(f"{prefix}{{ {inner} }}")
            elif self.drums and isinstance(element, music.Note):
                parts.append(self.drum_note(element))
            else:
                parts.append(music.to_lilypond(element, self.interval))
        return " ".join(parts).replace("\n ", "\n")


def _merge_full_bar_rests(elements: list[music.Element]) -> list[music.Element]:
    """Join adjacent full-bar rests into one rest.

    LilyPond shows one long rest as a rest with a number in the parts. It does
    not join rests that are written one bar at a time.
    """
    merged: list[music.Element] = []
    run: music.Rest | None = None
    for element in elements:
        plain_rest = isinstance(element, music.Rest) and element.kind == "R" and not element.posts
        if plain_rest:
            if run is None:
                run = music.Rest("R", element.duration, "")
                merged.append(run)
            else:
                run.duration += element.duration
            whole = run.duration / 4
            run.duration_text = (
                f"1*{whole.numerator}"
                if whole.denominator == 1
                else f"1*{whole.numerator}/{whole.denominator}"
            )
        elif isinstance(element, music.BarCheck) and run is not None:
            continue
        else:
            if run is not None:
                merged.append(music.BarCheck())
                run = None
            merged.append(element)
    if run is not None:
        merged.append(music.BarCheck())
    return merged


def _pitches(elements: list[music.Element]) -> list[float]:
    """Return the MIDI numbers of all notes in the elements."""
    found: list[float] = []
    for element in elements:
        if isinstance(element, music.Note):
            found.extend(note_pitch.pitch.midi for note_pitch in element.pitches)
        elif isinstance(element, music.Group):
            found.extend(_pitches(element.children))
    return found


def best_clef(base: str, instrument: Instrument | None, written: list[float]) -> str:
    """Return the clef for a passage: the usual clef, or a better clef for its range."""
    if not written or instrument is None or base in ("percussion", "grand"):
        return base
    ordered = sorted(written)
    median, lowest = ordered[len(ordered) // 2], ordered[0]
    # The low strings of a guitar with eight strings are far below the treble staff.
    if base == "treble" and instrument.name == "guitar" and median < 55:
        return "bass"
    if base == "bass" and instrument.name == "violoncello" and median > 66 and lowest >= 55:
        return "tenor"
    if base == "alto" and median > 81 and lowest > 67:
        return "treble"
    return base


def best_ottava(clef: str, instrument: Instrument | None, written: list[float]) -> int:
    """Return the octave sign for a passage: 1 = one octave higher, -1 = lower, 0 = none.

    A passage that is all very high is easier to read with an octave sign.
    The low octaves of a keyboard instrument get the sign for the lower octave.
    """
    if not written or instrument is None:
        return 0
    ordered = sorted(written)
    low_part = ordered[len(ordered) // 10]
    if clef == "treble" and ordered[-1] >= 93 and low_part >= 81:
        return 1
    if clef == "bass" and instrument.clef == "grand" and ordered[0] < 31 and ordered[-1] <= 55:
        return -1
    return 0


def _with_clefs(
    work: Work, player: Player, chunks: list[music.Group], emitter: _Emitter, instrument
) -> list[music.Element]:
    """Return the music of the chunks with a clef command where the best clef changes."""
    elements: list[music.Element] = []
    current = ""
    ottava = 0
    for chunk in chunks:
        shift = emitter.interval.semitones if emitter.interval else 0
        written = [midi + shift for midi in _pitches(chunk.children)]
        clef = best_clef(emitter.clef_of(instrument), instrument, written)
        if clef != current:
            elements.append(music.Command("clef", [clef]))
            current = clef
        octave = best_ottava(clef, instrument, written)
        if octave != ottava:
            elements.append(music.Command("ottava", [f"#{octave}"]))
            ottava = octave
        elements.extend(chunk.children)
        # A change of instrument in the chunk changes the usual clef.
        for command in _walk_commands(chunk.children):
            if command.name == "switch":
                instrument = work.orchestra.instruments.get(command.arguments[0].strip('"'))
                emitter.set_instrument(instrument)
                current = emitter.clef_of(instrument)
    emitter.set_instrument(work.orchestra.first_instrument(player.id))
    return elements


# A crescendo or a decrescendo with no written end goes on to the next dynamic mark. If
# the player has a rest of this length (in quarter notes) or more before that mark, the
# sign ends at the rest: a crescendo through bars of rest has no meaning.
HAIRPIN_REST = Fraction(2)


def end_hairpins(elements: list[music.Element], is_open: bool = False) -> list[music.Element]:
    """Return the music with an end for each crescendo that would go through a long rest."""
    result, _state = _end_hairpins(elements, is_open)
    return result


def _end_hairpins(elements: list[music.Element], is_open: bool) -> tuple[list[music.Element], bool]:
    result: list[music.Element] = []
    for index, element in enumerate(elements):
        marked = isinstance(element, music.Note | music.Rest) and any(
            post.kind in _DYNAMIC_KINDS for post in element.posts
        )
        if is_open and not marked and isinstance(element, music.Rest) and element.kind != "s":
            # The rests that follow with no note between them count as one rest.
            total = Fraction(0)
            full_bar = False
            for later in elements[index:]:
                if isinstance(later, music.Rest) and later.kind != "s":
                    total += later.duration
                    full_bar = full_bar or later.kind == "R"
                elif not isinstance(later, music.BarCheck | music.Command):
                    break
            if full_bar or total >= HAIRPIN_REST:
                end = music.Post("hairpin", "\\!", "!")
                element = replace(element, posts=[*element.posts, end])
                is_open = False
        if isinstance(element, music.Note | music.Rest):
            for post in element.posts:
                if post.kind == "hairpin":
                    is_open = post.value in "<>"
                elif post.kind == "dynamic":
                    is_open = False
        elif isinstance(element, music.Group):
            if element.kind == "parallel":
                # Each voice has its own signs. The first voice goes on after the group.
                voices = []
                after = is_open
                for number, child in enumerate(element.children):
                    children, state = _end_hairpins(child.children, is_open)
                    voices.append(replace(child, children=children))
                    if number == 0:
                        after = state
                element, is_open = replace(element, children=voices), after
            else:
                children, is_open = _end_hairpins(element.children, is_open)
                element = replace(element, children=children)
        result.append(element)
    return result, is_open


def _emitter(work: Work, player: Player, *, for_part: bool) -> _Emitter:
    """Return the writer for the music of a player."""
    emitter = _Emitter(work, for_part, left_hand=player.id.endswith(".lh"))
    table = DRUM_STAVES.get(player.instruments[0])
    if table:
        emitter.drums = {drum.midi: drum for drum in table[0]}
    return emitter


def _player_music(work: Work, player: Player, *, for_part: bool) -> str:
    if player.instruments[0] == TAPE:
        return tape_music(work, 1, len(work.structure.bars))
    emitter = _emitter(work, player, for_part=for_part)
    instrument = work.orchestra.first_instrument(player.id)
    emitter.set_instrument(instrument)
    chunks = [chunk for _first_bar, chunk in work.chunks.get(player.id, [])]
    if emitter.drums:
        elements = [element for chunk in chunks for element in chunk.children]
        return drum_music(emitter, end_hairpins(elements))
    return emitter.emit(end_hairpins(_with_clefs(work, player, chunks, emitter, instrument)))


# ----------------------------------------------------------------------------
# The drum staves
# ----------------------------------------------------------------------------

_DYNAMIC_KINDS = ("dynamic", "hairpin")
_Marks = list[tuple[Fraction, list[music.Post]]]


def _skip(duration: Fraction) -> music.Rest:
    """Return a spacer rest with a duration in quarter notes."""
    whole = duration / 4
    return music.Rest("s", duration, f"1*{whole.numerator}/{whole.denominator}")


def _is_parallel(element: music.Element) -> bool:
    return isinstance(element, music.Group) and element.kind == "parallel"


def _flat_voices(group: music.Group) -> list[list[music.Element]]:
    """Return the voices of a group. A voice that is a group of voices gives its own voices."""
    voices: list[list[music.Element]] = []
    for child in group.children:
        if len(child.children) == 1 and _is_parallel(child.children[0]):
            voices.extend(_flat_voices(child.children[0]))
        else:
            voices.append(child.children)
    return voices


DRUM_VOICES = 3  # the hands, the feet, and one more voice for the long sounds of the machine


def drum_voices(
    elements: list[music.Element], feet: set[int]
) -> tuple[list[list[music.Element]], _Marks]:
    """Divide the music of a drum staff into its voices and the dynamic marks.

    The music text has two voices only in the bars in which hands and feet
    play together. The score needs voices that continue through the part: a
    crescendo cannot go from a voice of one bar to a voice of the next bar.
    Thus each voice gets a spacer rest where it has no music, and the
    dynamic marks go to a list with the position of each mark (in quarter
    notes from the start of the music).
    """
    marks: _Marks = []

    def strip(items: list[music.Element], start: Fraction, scale: Fraction) -> list[music.Element]:
        """Return the items with no dynamic marks. The marks go to the list."""
        result: list[music.Element] = []
        place = start
        for item in items:
            if isinstance(item, music.Note | music.Rest):
                moved = [post for post in item.posts if post.kind in _DYNAMIC_KINDS]
                if moved:
                    marks.append((place, moved))
                    kept = [post for post in item.posts if post.kind not in _DYNAMIC_KINDS]
                    item = replace(item, posts=kept)
            elif _is_parallel(item):
                voices = [
                    replace(child, children=strip(child.children, place, scale))
                    for child in item.children
                ]
                item = replace(item, children=voices)
            elif isinstance(item, music.Group) and item.kind != "grace":
                item = replace(item, children=strip(item.children, place, scale * item.ratio))
            result.append(item)
            place += music.length(item) * scale
        return result

    voices: list[list[music.Element]] = [[] for _ in range(DRUM_VOICES)]
    position = Fraction(0)
    bar: list[music.Element] = []

    def close_bar() -> None:
        nonlocal position
        # A bar with strokes of the feet only goes to the voice of the feet.
        pitches = _pitches([item for item in bar if not _is_parallel(item)])
        target = 1 if pitches and all(round(midi) in feet for midi in pitches) else 0
        for item in strip(bar, position, Fraction(1)):
            duration = music.length(item)
            if duration == 0:
                voices[0].append(item)  # a command
                continue
            parts = _flat_voices(item) if _is_parallel(item) else []
            if len(parts) > DRUM_VOICES:
                raise ValueError(f"a drum staff has {DRUM_VOICES} voices or fewer")
            for number, voice in enumerate(voices):
                if parts:
                    voice.extend(parts[number] if number < len(parts) else [_skip(duration)])
                else:
                    voice.append(item if number == target else _skip(duration))
            position += duration
        bar.clear()

    for element in elements:
        if isinstance(element, music.BarCheck):
            close_bar()
            for voice in voices:
                voice.append(element)
        else:
            bar.append(element)
    close_bar()
    return voices, marks


def _marks_voice(marks: _Marks, total: Fraction) -> str:
    """Write the dynamic marks as a voice of spacer rests."""
    places: dict[Fraction, list[music.Post]] = {}
    for position, posts in sorted(marks, key=lambda mark: mark[0]):
        own = places.setdefault(position, [])
        for post in posts:
            # Two voices can have a dynamic mark at the same time: the staff shows one.
            if post.kind == "dynamic" and any(other.kind == "dynamic" for other in own):
                continue
            if post.text not in [other.text for other in own]:
                own.append(post)
    parts = []
    ordered = sorted(places)
    if not ordered or ordered[0] > 0:
        parts.append(music.to_lilypond(_skip(ordered[0] if ordered else total)))
    is_open = False
    for index, position in enumerate(ordered):
        end = ordered[index + 1] if index + 1 < len(ordered) else total
        for post in places[position]:
            is_open = post.kind == "hairpin" and post.value in "<>"
        if end <= position:
            continue
        if is_open and end == total and end - position > Fraction(1, 4):
            # The last crescendo or decrescendo ends just before the end of the music.
            end -= Fraction(1, 4)
            parts.append(music.to_lilypond(replace(_skip(end - position), posts=places[position])))
            parts.append(music.to_lilypond(_skip(Fraction(1, 4))) + "\\!")
        else:
            parts.append(music.to_lilypond(replace(_skip(end - position), posts=places[position])))
    return " ".join(parts)


def _without_rests(elements: list[music.Element]) -> list[music.Element]:
    """Return the elements with spacer rests in place of all rests."""
    result: list[music.Element] = []
    for element in elements:
        if isinstance(element, music.Rest) and element.kind != "s":
            element = replace(element, kind="s", posts=[])
        elif isinstance(element, music.Group):
            element = replace(element, children=_without_rests(element.children))
        result.append(element)
    return result


def drum_music(emitter: _Emitter, elements: list[music.Element]) -> str:
    """Return the music of a drum staff: three voices that continue through the part."""
    feet = {midi for midi, drum in emitter.drums.items() if drum.voice == 1}
    voices, marks = drum_voices(elements, feet)
    total = sum((music.length(element) for element in elements), Fraction(0))
    lines = ["<<"]
    # The third voice shows no rests: three rests at the same place are hard to read.
    voices[2] = _without_rests(voices[2])
    for voice, setting in zip(voices, ("\\voiceOne", "\\voiceTwo", "\\voiceFour"), strict=True):
        if not _pitches(voice):
            continue
        emitter.tied = False
        lines.append(f"\\new DrumVoice {{ {setting} \\drummode {{\n{emitter.emit(voice)}\n}} }}")
    emitter.tied = False
    lines.append(f"\\new DrumVoice {{ {_marks_voice(marks, total)} }}")
    lines.append(">>")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# The staff of the recorded sounds
# ----------------------------------------------------------------------------

# Note values in sixteenth notes.
_VALUES = {1: "16", 2: "8", 3: "8.", 4: "4", 6: "4.", 8: "2", 12: "2.", 16: "1"}


def _pulse_sizes(bar: Bar) -> list[int]:
    """Return the lengths of the pulses of a bar, in sixteenth notes."""
    unit = 16 // bar.denominator
    if bar.grouping:
        return [group * unit for group in bar.grouping]
    if bar.denominator == 8 and bar.numerator % 3 == 0:
        return [3 * unit] * (bar.numerator // 3)
    return [unit] * bar.numerator


def _values(place: int, run: int, size: int) -> list[int]:
    """Divide `run` sixteenth notes at `place` of a pulse into note values.

    A value starts at a place that its length divides: thus the rests show
    the pulse.
    """
    if place == 0 and run == size and size in _VALUES:
        return [size]
    values = []
    while run > 0:
        value = 16
        while value > run or place % value:
            value //= 2
        values.append(value)
        place += value
        run -= value
    return values


def tape_events(work: Work) -> dict[int, dict[int, list[str]]]:
    """Return the texts of the recorded sounds: for each bar, for each sixteenth note."""
    structure = work.structure
    found: dict[int, dict[int, list[str]]] = {}
    for item in [*work.extras.get("cues", []), *work.extras.get("edits", [])]:
        beat = Fraction(item.beat).limit_denominator(64)
        position = structure.bar(item.bar).start + beat - 1
        position = min(max(position, Fraction(0)), structure.length - Fraction(1, 4))
        bar = structure.bar_at(position)
        step = min(int((position - bar.start) * 4 + Fraction(1, 2)), int(bar.length * 4) - 1)
        found.setdefault(bar.number, {}).setdefault(step, []).append(item.label)
    return found


def tape_music(work: Work, first: int, last: int) -> str:
    """Return the music of the staff of the recorded sounds, from bar `first` to bar `last`.

    The staff has one note for each sound that starts and for each change of
    the recording, at the nearest sixteenth note. A text gives the name.
    """

    def quoted(label: str) -> str:
        return '"' + label.replace("\\", "").replace('"', "'") + '"'

    events = tape_events(work)
    bars: list[str] = []
    empty: tuple[int, int] | None = None  # the metre of the run of empty bars
    count = 0

    def close_run() -> None:
        nonlocal empty, count
        if empty is not None:
            bars.append(f"R1*{empty[0]}/{empty[1]}*{count}")
        empty, count = None, 0

    for bar in work.structure.bars[first - 1 : last]:
        own = events.get(bar.number)
        if not own:
            if empty != (bar.numerator, bar.denominator):
                close_run()
            empty = (bar.numerator, bar.denominator)
            count += 1
            continue
        close_run()
        parts = []
        offset = 0
        for size in _pulse_sizes(bar):
            place = 0
            while place < size:
                labels = own.get(offset + place)
                run = 1
                while place + run < size and offset + place + run not in own:
                    run += 1
                values = _values(place, run, size)
                if labels:
                    lines = " ".join(quoted(label) for label in labels)
                    markup = lines if len(labels) == 1 else f"\\markup \\column {{ {lines} }}"
                    parts.append(f"c'{_VALUES[values[0]]}^{markup}")
                    values = values[1:]
                parts.extend(f"r{_VALUES[value]}" for value in values)
                place += run
            offset += size
        bars.append(" ".join(parts))
    close_run()
    return " |\n".join(bars) + " |"


def _header(work: Work, instrument_line: str = "") -> str:
    lines = [
        "\\header {",
        f'  title = "{work.title}"',
        f'  subtitle = "{work.subtitle}"' if work.subtitle else "",
        f'  composer = "{work.composer}"' if work.composer else "",
        f'  instrument = "{instrument_line}"' if instrument_line else "",
        "  tagline = ##f",
        "}",
    ]
    return "\n".join(line for line in lines if line)


def _definitions(
    work: Work, players: list[Player], *, for_part: bool, breaks: set[int] | None = None
) -> str:
    structure = work.structure if breaks is None else replace(work.structure, breaks=breaks)
    blocks = [
        "global = {\n\\accidentalStyle Score.modern\n\\numericTimeSignature\n"
        + global_to_lilypond(structure)
        + "\n}"
    ]
    for player in players:
        text = _player_music(work, player, for_part=for_part)
        blocks.append(f"{identifier(player.id)} = {{\n{text}\n}}")
    return "\n\n".join(blocks)


def staff_kind(player: Player) -> tuple[str, str]:
    """Return the kind of staff of a player, and the settings of that kind."""
    first = player.instruments[0]
    if first in DRUM_STAVES:
        return "DrumStaff", f"drumStyleTable = #(alist->hash-table {DRUM_STAVES[first][1]})"
    if first == TAPE:
        return "RhythmicStaff", ""
    return "Staff", ""


def _staff(player: Player, *, names: bool = True, settings: str = "") -> str:
    kind, own = staff_kind(player)
    name = f'instrumentName = "{player.name}" shortInstrumentName = "{player.short}"'
    inner = " ".join(word for word in (name if names else "", own, settings) if word)
    with_block = f"\\with {{ {inner} }} " if inner else ""
    return f'\\new {kind} = "{player.id}" {with_block}<< \\global \\{identifier(player.id)} >>'


def _groups(work: Work) -> list[tuple[str, list[Player]]]:
    """Return the players in families, in the sequence of the score."""
    groups: dict[str, list[Player]] = {family: [] for family in FAMILY_ORDER}
    for player in work.orchestra.players:
        groups[player.family].append(player)
    return [(family, members) for family, members in groups.items() if members]


def _score_staves(work: Work) -> str:
    blocks = []
    for family, members in _groups(work):
        staves = []
        index = 0
        while index < len(members):
            player = members[index]
            if player.id.endswith(".rh"):
                lower = members[index + 1]
                base = player.id[: -len(".rh")]
                staves.append(
                    f'\\new PianoStaff = "{base}" \\with {{ instrumentName = "{player.name}" '
                    f'shortInstrumentName = "{player.short}" }} <<\n'
                    f"    {_staff(player, names=False)}\n    {_staff(lower, names=False)}\n  >>"
                )
                index += 2
            else:
                staves.append(_staff(player))
                index += 1
        joined = "\n  ".join(staves)
        blocks.append(f'\\new StaffGroup = "{family}" <<\n  {joined}\n>>')
    return "\n".join(blocks)


FAMILY_TITLES = {
    "horns": "Horns",
    "synths": "Synthesizers",
    "rhythm": "Rhythm section",
    "strings": "Strings",
    "media": "Recorded sounds",
}
LEFT_COLUMN = ("horns", "synths")
# The players of these families play with few rests: their parts have no place for a
# page turn at a rest.
CONTINUOUS_FAMILIES = ("rhythm", "media")


def _metre_note(work: Work) -> str:
    """Return the note about the most frequent uneven metre of the work."""
    metres = Counter(
        (bar.numerator, bar.denominator, bar.grouping)
        for bar in work.structure.bars
        if bar.grouping
    )
    if not metres:
        return ""
    (numerator, denominator, grouping), _count = metres.most_common(1)[0]
    unit = {4: "quarter", 8: "eighth", 16: "sixteenth"}.get(denominator, f"1/{denominator}")
    groups = " + ".join(str(group) for group in grouping)
    return (
        f"The metre {numerator}/{denominator} has {len(grouping)} pulses of different "
        f"lengths: {groups} {unit} notes. The beams and the rests show the pulses."
    )


def score_notes(work: Work) -> list[str]:
    """Return the notes for the performance on the first page of the score.

    The texts come from the music. Thus they stay correct when the music changes.
    """
    from ..perform.events import perform  # at call time: that module imports this package

    structure = work.structure
    transposed = []
    octave = []
    for player in work.orchestra.players:
        instrument = work.orchestra.first_instrument(player.id)
        if instrument is None or player.id.endswith(".lh") or not perform(work, player.id):
            continue
        if instrument.transposition % 12:
            transposed.append(player.name.lower())
        elif instrument.transposition == 12:
            octave.append(player.name.lower().split(" (")[0])

    def listed(names: list[str]) -> str:
        if len(names) <= 2:
            return " and ".join(names)
        return ", ".join(names[:-1]) + ", and " + names[-1]

    notes = ["The score is in C."]
    if transposed:
        notes[0] += f" These parts are transposed: {listed(transposed)}."
    if octave:
        verb = "sounds" if len(octave) == 1 else "sound"
        notes.append(f"The {listed(octave)} {verb} one octave lower than written.")
    notes.append("An accidental is for one bar and one octave only.")
    metre = _metre_note(work)
    if metre:
        notes.append(metre)
    players = {player.instruments[0]: player for player in work.orchestra.players}
    if "drum kit" in players:
        notes.append(
            "Drums: a note in brackets is a ghost note (very soft). The page shows the "
            "note of each drum."
        )
    studio = [players[name].name.lower() for name in ("drum machine", TAPE) if name in players]
    if studio:
        notes.append(
            f"A sequencer plays the {listed(studio)}. The staff of the recorded sounds has "
            "one note at each place where a sound starts or where the recording changes."
        )
    used = {post for player in work.orchestra.players for post in _technique_names(work, player)}
    marks = [
        f"{technique.text} = {technique.meaning}"
        for technique in techniques.TECHNIQUES.values()
        if technique.name in used and technique.meaning
    ]
    if marks:
        notes.append("Signs: " + "; ".join(marks) + ".")
    minutes = round(structure.duration_seconds / 60)
    if minutes >= 1:
        notes.append(f"Duration: {minutes} minutes.")
    return notes


def _technique_names(work: Work, player: Player) -> set[str]:
    """Return the names of the technique commands in the music of a player."""
    found: set[str] = set()

    def walk(elements: list[music.Element]) -> None:
        for element in elements:
            if isinstance(element, music.Group):
                walk(element.children)
            elif isinstance(element, music.Command):
                found.add(element.name)
            elif isinstance(element, (music.Note, music.Rest)):
                for post in element.posts:
                    found.add(post.text.lstrip("\\^_-"))

    for _first_bar, chunk in work.chunks.get(player.id, []):
        walk(chunk.children)
    return found


def _instrument_lines(work: Work) -> dict[str, list[str]]:
    """Return the list of the players for the first page: one line for each player."""
    from ..perform.events import perform

    lines: dict[str, list[str]] = {family: [] for family in FAMILY_ORDER}
    for player in work.orchestra.players:
        if player.id.endswith(".lh"):
            continue
        hands = [player.id]
        if player.id.endswith(".rh"):
            hands.append(player.id[: -len(".rh")] + ".lh")
        used: list[str] = []
        for hand in hands:
            for note in perform(work, hand):
                if note.instrument not in used:
                    used.append(note.instrument)
        if player.instruments[0] == TAPE:
            if not tape_events(work):
                continue
        elif not used:
            continue
        line = player.name
        if len(player.instruments) > 1 and [name.lower() for name in used] != [line.lower()]:
            # A synthesizer player: the sounds in the sequence of the music.
            line += ": " + ", ".join(used)
        if player.count > 1:
            line += f" ({player.count} players)"
        lines[player.family].append(line)
    return lines


def drum_key(table: list[drums.Drum], style: str, width: float) -> str:
    """Return a small staff that shows the note of each drum, as LilyPond markup."""
    notes = []
    words = []
    for drum in table:
        ghost = "\\parenthesize " if drum.ghost else ""
        notes.append(f'{ghost}{drum.lilypond}4 \\bar ""')
        words.append('"' + drum.name + '"')
    return (
        "\\score {\n"
        f"  \\new DrumStaff \\with {{ drumStyleTable = #(alist->hash-table {style}) }} <<\n"
        '    \\new DrumVoice = "key" \\drummode { \\cadenzaOn \\stemUp ' + " ".join(notes) + " }\n"
        '    \\new Lyrics \\lyricsto "key" { ' + " ".join(words) + " }\n"
        "  >>\n"
        "  \\layout {\n"
        f"    indent = 0 line-width = {width}\\mm ragged-right = ##t ragged-last = ##t\n"
        "    \\context { \\Score \\omit BarNumber }\n"
        "    \\context { \\DrumStaff \\omit TimeSignature }\n"
        "    \\context { \\Lyrics \\override LyricText.font-size = #-2 }\n"
        "  }\n"
        "}"
    )


def _used_drums(work: Work, player: Player) -> list[drums.Drum]:
    """Return the drums that a player has in the work, in the sequence of the table."""
    from ..perform.events import perform

    table = DRUM_STAVES[player.instruments[0]][0]
    used = {round(note.midi) for note in perform(work, player.id)}
    return [drum for drum in table if drum.midi in used]


def drum_keys(work: Work, players: list[Player], width: float) -> list[str]:
    """Return the markup lines with the drum key of each drum staff among the players."""
    lines = []
    for player in players:
        if player.instruments[0] not in DRUM_STAVES:
            continue
        table = _used_drums(work, player)
        if not table:
            continue
        style = DRUM_STAVES[player.instruments[0]][1]
        lines.append(f'\\vspace #1 \\line {{ \\bold "{player.name}" }}')
        lines.append(drum_key(table, style, width))
    return lines


def _front_page(work: Work) -> str:
    """Return the first page of the score: the list of the players and the notes."""

    def text(value: str) -> str:
        return '"' + value.replace("\\", "").replace('"', "'") + '"'

    def wrapped(value: str) -> str:
        words = " ".join(text(word) for word in value.split())
        return f"\\wordwrap {{ {words} }}"

    families = _instrument_lines(work)
    columns: list[list[str]] = [[], []]
    for family in FAMILY_ORDER:
        if not families[family]:
            continue
        target = columns[0] if family in LEFT_COLUMN else columns[1]
        target.append(f"\\vspace #1 \\line {{ \\bold {text(FAMILY_TITLES[family])} }}")
        target.extend(f"\\line {{ {text(line)} }}" for line in families[family])
    left = "\n      ".join(columns[0])
    right = "\n      ".join(columns[1])
    notes = "\n    ".join(f"\\vspace #0.4 {wrapped(note)}" for note in score_notes(work))
    keys = "\n    ".join(drum_keys(work, work.orchestra.players, 150.0))
    return (
        "\\markup \\fontsize #3 \\column {\n"
        '  \\vspace #2 \\line { \\bold \\fontsize #2 "Ensemble" }\n'
        "  \\line {\n"
        f"    \\column {{\n      {left}\n    }}\n"
        "    \\hspace #10\n"
        f"    \\column {{\n      {right}\n    }}\n"
        "  }\n"
        '  \\vspace #2 \\line { \\bold \\fontsize #2 "Notes for the performance" }\n'
        f"  \\override #'(line-width . 110) \\column {{\n    {notes}\n  }}\n"
        + (
            '  \\vspace #2 \\line { \\bold \\fontsize #2 "The notes of the drums" }\n'
            f"  \\column {{\n    {keys}\n  }}\n"
            if keys
            else ""
        )
        + "}\n\n\\pageBreak"
    )


def score_breaks(work: Work, capacity: float = 62.0, most_bars: int = 10) -> set[int]:
    """Return the bars after which the conductor score starts a new system.

    The width of a bar depends on the number of different moments at which
    a note starts. A system gets bars until it is full.
    """
    from ..perform.events import perform

    structure = work.structure
    starts = [float(bar.start) for bar in structure.bars]
    moments: list[set[float]] = [set() for _ in structure.bars]
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            position = float(note.start)
            moments[bisect.bisect_right(starts, position) - 1].add(position)
    breaks: set[int] = set()
    load, count = 0.0, 0
    for bar, columns in zip(structure.bars, moments, strict=True):
        width = max(len(columns), 2) + 1.5
        if count and (load + width > capacity or count >= most_bars):
            breaks.add(bar.number - 1)
            load, count = 0.0, 0
        load += width
        count += 1
    return breaks


def score_file(work: Work) -> str:
    """Return the LilyPond text of the conductor score."""
    breaks = score_breaks(work)
    return (
        "\n\n".join(
            [
                f'\\version "{LILYPOND_VERSION}"',
                STYLE.strip(),
                techniques.lilypond_definitions(),
                "#(set-global-staff-size 13)",
                SCORE_PAPER.strip(),
                _header(work, "Score in C"),
                _front_page(work),
                _definitions(work, work.orchestra.players, for_part=False, breaks=breaks),
                "\\score {\n<<\n" + _score_staves(work) + "\n>>\n" + SCORE_LAYOUT.strip() + "\n}",
            ]
        )
        + "\n"
    )


def part_players(work: Work) -> dict[str, list[Player]]:
    """Return the staves of each part. A keyboard part has two staves."""
    parts: dict[str, list[Player]] = {}
    for player in work.orchestra.players:
        base = player.id.split(".")[0]
        parts.setdefault(base, []).append(player)
    return parts


def part_file(work: Work, part_id: str) -> str:
    """Return the LilyPond text of one part."""
    players = part_players(work)[part_id]
    first = players[0]
    name = first.name
    instrument = work.orchestra.first_instrument(first.id)
    line = name
    if instrument and instrument.transposition % 12 and " in " in instrument.name:
        line = f"{name} in {instrument.name.split(' in ')[1]}"
    if len(players) == 1:
        staves = _staff(first, names=False)
    else:
        inner = "\n  ".join(_staff(player, names=False) for player in players)
        staves = f"\\new PianoStaff <<\n  {inner}\n>>"
    paper = PART_PAPER
    if first.family in CONTINUOUS_FAMILIES:
        paper = paper.replace("#ly:page-turn-breaking", "#ly:optimal-breaking")
    keys = drum_keys(work, players, 170.0)
    key_page = ""
    if keys:
        key_page = "\\markup \\column {\n  " + "\n  ".join(keys[1::2]) + "\n  \\vspace #1\n}"
    return (
        "\n\n".join(
            block
            for block in [
                f'\\version "{LILYPOND_VERSION}"',
                STYLE.strip(),
                techniques.lilypond_definitions(),
                "#(set-global-staff-size 19)",
                paper.strip(),
                _header(work, line),
                key_page,
                _definitions(work, players, for_part=True),
                "\\score {\n" + staves + "\n" + PART_LAYOUT.strip() + "\n}",
            ]
            if block
        )
        + "\n"
    )


# ----------------------------------------------------------------------------
# Score pages for the video: one file for each section of the work
# ----------------------------------------------------------------------------

VIDEO_PAGE_MM = (480.0, 270.0)
VIDEO_SECONDS_PER_SCREEN = 15.0
# The video for a telephone: the screen is tall and narrow. A screen shows less
# time, and the notes are larger.
MOBILE_PAGE_MM = (270.0, 480.0)
MOBILE_SECONDS_PER_SCREEN = 7.0

VIDEO_SCHEME = r"""
#(define (tag-when class)
   (lambda (grob)
     (let* ((column (ly:item-get-column grob))
            (when (ly:grob-property column 'when)))
       (list (cons 'class class)
             (cons 'data-when
                   (number->string (exact->inexact (ly:moment-main when))))))))
"""

VIDEO_LAYOUT = r"""
\layout {
  \context {
    \Score
    \override NoteHead.output-attributes = #(tag-when "nh")
    \override Rest.output-attributes = #(tag-when "rest")
    \override BarLine.output-attributes = #(tag-when "bar")
    \override BarNumber.font-size = #0
    \override MetronomeMark.font-size = #2
    \override MetronomeMark.padding = #2.5
    \override RehearsalMark.padding = #3
    \override InstrumentName.self-alignment-X = #RIGHT
    \override Hairpin.minimum-length = #5
  }
  \context {
    \Staff
    \RemoveAllEmptyStaves
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
  \context {
    \DrumStaff
    \RemoveAllEmptyStaves
    \consists Merge_rests_engraver
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
  \context {
    \RhythmicStaff
    \RemoveAllEmptyStaves
    \override TextScript.font-size = #-1
    \override NoteHead.style = #'cross
  }
}
""".replace("\\\\", "\\")


# The names of the instruments are smaller on the narrow page: the staves are large.
MOBILE_LAYOUT = VIDEO_LAYOUT.replace(
    "\\override InstrumentName.self-alignment-X = #RIGHT",
    "\\override InstrumentName.self-alignment-X = #RIGHT\n"
    "    \\override InstrumentName.font-size = #-3",
)


def chunk_count(work: Work) -> int:
    """Return the number of sections of the work."""
    return max(len(chunks) for chunks in work.chunks.values())


def chunk_bars(work: Work, index: int) -> tuple[int, int]:
    """Return the first bar and the last bar of a section."""
    some_player = next(iter(work.chunks.values()))
    first = some_player[index][0]
    last = (
        some_player[index + 1][0] - 1 if index + 1 < len(some_player) else len(work.structure.bars)
    )
    return first, last


def _instrument_at(work: Work, player: Player, index: int) -> Instrument | None:
    """Return the instrument that a player has at the start of a section."""
    name = player.instruments[0]
    for _first_bar, chunk in work.chunks[player.id][:index]:
        for element in _walk_commands(chunk.children):
            if element.name == "switch":
                name = element.arguments[0].strip('"')
    return work.orchestra.instruments.get(name)


def _walk_commands(elements: list[music.Element]):
    for element in elements:
        if isinstance(element, music.Command):
            yield element
        elif isinstance(element, music.Group):
            yield from _walk_commands(element.children)


def _is_silent(elements: list[music.Element]) -> bool:
    """Return True if the music has no notes."""
    for element in elements:
        if isinstance(element, music.Note):
            return False
        if isinstance(element, music.Group) and not _is_silent(element.children):
            return False
    return True


def active_players(work: Work, index: int) -> list[Player]:
    """Return the players that have notes in a section."""
    first, last = chunk_bars(work, index)
    tape = any(first <= bar <= last for bar in tape_events(work))
    return [
        player
        for player in work.orchestra.players
        if (tape if player.instruments[0] == TAPE else
            not _is_silent(work.chunks[player.id][index][1].children))
    ]  # fmt: skip


def video_file(work: Work, index: int, staff_size: float, *, mobile: bool = False) -> str:
    """Return the LilyPond text of one section, as a page for the video.

    If `mobile` is true, the page is for the video for a telephone.
    """
    from .structure import Structure, global_to_lilypond

    first, last = chunk_bars(work, index)
    source = work.structure
    part = Structure(final_bar=last == len(source.bars))
    for bar in source.bars[first - 1 : last]:
        part.add_bars(1, bar.numerator, bar.denominator, bar.grouping)
    start = source.bar(first).start
    end = source.bar(last).end
    for point in source.tempo_points:
        if start <= point.position < end:
            shifted = type(point)(**{**point.__dict__, "position": point.position - start})
            part.tempo_points.append(shifted)
    part.marks = {
        bar - first + 1: label for bar, label in source.marks.items() if first <= bar <= last
    }
    part.double_bars = {bar - first + 1 for bar in source.double_bars if first <= bar <= last}
    # A screen of the video shows about 15 seconds of music.
    shown_from = start
    for bar in source.bars[first - 1 : last - 1]:
        seconds = source.seconds(bar.end) - source.seconds(shown_from)
        if seconds >= (MOBILE_SECONDS_PER_SCREEN if mobile else VIDEO_SECONDS_PER_SCREEN):
            part.breaks.add(bar.number - first + 1)
            shown_from = bar.end

    blocks = [
        "global = {\n\\accidentalStyle Score.modern\n\\numericTimeSignature\n"
        f"\\set Score.currentBarNumber = #{first}\n" + global_to_lilypond(part) + "\n}"
    ]
    staves: dict[str, list[str]] = {family: [] for family in FAMILY_ORDER}
    players = work.orchestra.players
    shown = {player.id for player in active_players(work, index)}
    # A keyboard instrument shows its two staves if one of them has notes.
    for player in players:
        base = player.id.split(".")[0]
        if "." in player.id and any(other.split(".")[0] == base for other in shown):
            shown.add(player.id)
    position = 0
    while position < len(players):
        player = players[position]
        position += 1
        if player.id not in shown:
            continue
        emitter = _emitter(work, player, for_part=False)
        instrument = _instrument_at(work, player, index)
        emitter.set_instrument(instrument)
        children = end_hairpins(work.chunks[player.id][index][1].children)
        if player.instruments[0] == TAPE:
            body = tape_music(work, first, last)
        elif emitter.drums:
            body = drum_music(emitter, children)
        else:
            shift = emitter.interval.semitones if emitter.interval else 0
            written = [midi + shift for midi in _pitches(children)]
            clef = best_clef(emitter.clef_of(instrument), instrument, written)
            body = f"\\clef {clef}\n" + emitter.emit(children)
        blocks.append(f"{identifier(player.id)} = {{\n{body}\n}}")
        tag = (
            f"\\override StaffSymbol.output-attributes = "
            f'#\'((class . "staff") (data-staff . "{player.id}"))'
        )
        names = f'instrumentName = "{player.short}" shortInstrumentName = "{player.short}"'
        kind, own = staff_kind(player)
        settings = " ".join(word for word in ("" if "." in player.id else names, own, tag) if word)
        staff = (
            f'\\new {kind} = "{player.id}" \\with {{ {settings} }} '
            f"<< \\global \\{identifier(player.id)} >>"
        )
        if player.id.endswith(".rh"):
            staves[player.family].append(f"\\new PianoStaff \\with {{ {names} }} <<\n    {staff}")
        elif player.id.endswith(".lh"):
            staves[player.family].append(f"    {staff}\n  >>")
        else:
            staves[player.family].append(staff)
    groups = [
        f'\\new StaffGroup = "{family}" <<\n  ' + "\n  ".join(members) + "\n>>"
        for family, members in staves.items()
        if members
    ]
    width, height = MOBILE_PAGE_MM if mobile else VIDEO_PAGE_MM
    side = 6 if mobile else 10
    paper = (
        "\\paper {\n"
        f"  #(set-paper-size '(cons (* {width} mm) (* {height} mm)))\n"
        f"  top-margin = 8\\mm\n  bottom-margin = 8\\mm\n  left-margin = {side}\\mm\n"
        f"  right-margin = {side}\\mm\n  indent = 20\\mm\n  short-indent = 20\\mm\n"
        "  max-systems-per-page = 1\n  ragged-last = ##f\n  ragged-bottom = ##t\n"
        "  print-page-number = ##f\n  oddHeaderMarkup = ##f\n  evenHeaderMarkup = ##f\n"
        "  oddFooterMarkup = ##f\n  evenFooterMarkup = ##f\n}"
    )
    return (
        "\n\n".join(
            [
                f'\\version "{LILYPOND_VERSION}"',
                STYLE.strip(),
                VIDEO_SCHEME.strip(),
                techniques.lilypond_definitions(),
                f"#(set-global-staff-size {staff_size:.2f})",
                paper,
                "\n\n".join(blocks),
                "\\score {\n<<\n"
                + "\n".join(groups)
                + "\n>>\n"
                + (MOBILE_LAYOUT if mobile else VIDEO_LAYOUT).strip()
                + "\n}",
            ]
        )
        + "\n"
    )


def write_all(work: Work, directory: Path) -> list[Path]:
    """Write the score file and all part files. Return the paths."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / "score.ly"]
    paths[0].write_text(score_file(work), encoding="utf-8")
    for part_id in part_players(work):
        path = directory / f"part-{part_id}.ly"
        path.write_text(part_file(work, part_id), encoding="utf-8")
        paths.append(path)
    return paths
