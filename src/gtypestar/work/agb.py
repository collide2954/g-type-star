"""Part 7: the last burning, and the fall.

Helium burns in a shell with pulses, and the star gives its last and largest
light. Then the outer layers leave, the burning stops, and gravity is the
only force: the core falls to the size of the Earth.

The music has two halves.

The last burning (marks S, T, U; 28 bars at the main tempo). This is the
part of the work with the most drive. The kick drum never stops (eighth
notes, then sixteenth notes of two pedals), the snare drum is on the second
and the fifth pulse, and the guitar and the bass guitar play one riff of
sixteenth notes: muted low notes, open chords with the snare drum.

- S: the theme with all force. The saxophone uses its full range: accented
  low notes, leaps of more than one octave, and the highest note of the
  instrument (C6).
- T: the longest line of the work (eight bars of sixteenth notes), by all
  lead players, above the two pedals.
- U: three "thermal pulses". The key goes up by major thirds (G, B, E-flat).
  Each pulse has the motto, a run up, and five strokes of all players. Each
  pulse is higher and has more strokes of the drums than the pulse before.

The fall (mark V; 14 bars). The fourth pulse does not come. From its first
beat, all parts go down:

- The tempo falls from 175 to 56, slowly at first, then faster and faster
  (the square of the time, as the speed of an object that falls).
- All written music moves down one semitone in each bar: the guitar ends
  on its lowest string. The pitch of the recording itself falls by six
  semitones more (see "sink" in `audio/glitch.py`), a low-pass filter
  closes, and the sound moves to the centre. The last sounding root is C;
  the white dwarf starts on G.
- The division of the pulses becomes coarse: six notes in a pulse, then
  five, four, three, two, one. The players do not change at the same bar:
  they go out of step.
- The strings hold the notes of the last chord. One group after the other
  starts to fall in semitones, from the highest group down. Each group ends
  on its lowest open string.
- The saxophone goes down through its full range and ends on its lowest note.
- The chords become narrow: a wide major chord, then fourths, then three
  notes, then two. The kick drum stays last.

Style profile: "Groove", with the largest density of the work; then no profile.
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..compose import chords, patterns, tools
from ..notation import drums
from ..notation.pitch import from_midi
from ..notation.work import Work
from . import mainseq
from . import material as m
from .material import Bars

# ----------------------------------------------------------------------------
# The theme with all force
# ----------------------------------------------------------------------------

# The theme for the tenor saxophone, with a new shape that uses the range of the
# instrument: accented low notes (D3, G3), leaps of a ninth and of two octaves, and the
# notes above the usual range, to C6 in bar 6.
THEME_FORCE = [
    r"d8-> g-> r g'4.( c''4 d''4. g''4. ~",
    r"g''4.) r4. r4 a'4.->( g4.->)",
    r"e'4.->( e''4. ~ e''4 b''4.-> a''4. ~",
    r"a''4. g''4. ~ g''4) r4. r8 d8->( e",
    r"g4.->) g'4.( c''4 d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 c'''4.-> ~ c'''4.",
    r"b''4. a''4. g''4 e''4. d''4.)",
    r"b'4.( a'4. g'4 ~ g'4.) r4.",
]
# The same shape for the trumpet, with no low notes.
THEME_FORCE_TRUMPET = [
    r"r4. g'4.( c''4 d''4. g''4. ~",
    r"g''4.) r4. r4 a'4.->( g'4.)",
    r"e''4.->( ~ e''4. ~ e''4 b''4.-> a''4. ~",
    r"a''4. g''4. ~ g''4) r4. r4.",
    r"r4. g'4.( c''4 d''4. e''4. ~",
    r"e''4.) g''4.( ~ g''4 c'''4.-> ~ c'''4.",
    r"b''4. a''4. g''4 e''4. d''4.)",
    r"b'4.( a'4. g'4 ~ g'4.) r4.",
]

# Two new bars for the end of the last line: fourths that go up, then triads that go up.
LINE_END = [
    r"g16 c' f' e' a d' g' fis' b e' a' g' c' fis' b' a' d' g' c'' b' e' a' d'' c'' fis' b' e'' d''",
    r"g'16 b' d'' g'' fis'' d'' b' g' a' c'' e'' a'' g'' e'' c'' a' b' d'' fis'' b'' a'' fis'' d'' b' c'' e'' g'' g'')",
]

# ----------------------------------------------------------------------------
# The riff and the drums of the last burning
# ----------------------------------------------------------------------------

# The riff of the guitar and the bass guitar, in sixteenth notes. a = the low note with
# the palm on the strings; b = the open chord (root, fifth, octave). The open chords are
# on the second and the fifth pulse, with the snare drum.
RIFFS = [
    "Aaaaaa B__aaa Aaaa Aaaaaa B__a-a",
    "Aaaaaa B_aaB_ Aaaa aaAaaa B_____",
    "A-aaaa B__aaa A-aa Aaaaaa B_aB__",
    "Aaaaaa B__aaa AaAa B__aaa B_B_B_",
]
RIFF_RUN = "Aaaaaa Aaaaaa Aaaa Aaaaaa Aaaaaa"  # the bar of the run up
STROKES = "B_____ B_____ B___ B_____ B_____"  # the bar of the five strokes
# Strokes of the low horns with the riff.
LOW_HORNS = [
    "A__--- A__--- ---- ------ A__---",
    "A__--- ------ A_-- ------ A__A__",
    "A__--- A__--- ---- A__--- ------",
    "A__--- ---A__ ---- A__--- A__A__",
]

# The kick drum. The feet never stop: eighth notes with short runs of sixteenth notes,
# or sixteenth notes through the bar.
KICK_16 = "xxxxxx xxxxxx xxxx xxxxxx xxxxxx"
KICKS_8 = [
    "x-x-x- x-xxxx x-x- x-x-x- x-xxxx",
    "x-xxx- x-x-x- xxxx x-x-xx x-x-x-",
    "x-x-xx x-x-x- x-x- xxxxxx x-x-x-",
    "x-x-x- xxx-x- x-xx x-x-x- xxxxxx",
]
# The hands for the theme: open hi-hat between the beats, the cymbals on some pulses.
HANDS_OPEN = [
    {"cy": "c----- ------ k--- ------ ------", "hh": "--o-x- x-o-x- --x- x-o-x- x-o-x-",
     "sn": "------ O--g-- ---- ---g-- O-----"},
    {"cy": "------ ------ k--- ------ ------", "hh": "x-o-x- x-o-x- --x- x-o-x- x-x-o-",
     "sn": "------ O----g ---- ------ O--g--"},
    {"cy": "d----- ------ ---- k----- ------", "hh": "--o-x- x-o-x- x-o- --o-x- x-o-x-",
     "sn": "---g-- O----- ---g ------ O-----"},
    {"cy": "------ ------ k--- ------ ------", "hh": "x-o-x- x-x-o- --x- x-o-x- x-o-x-",
     "sn": "------ O--g-- ---- -----g O--g-g"},
]  # fmt: skip
# The hands for the line and the first two pulses: the bell of the ride cymbal on each pulse.
HANDS_BELL = [
    {"cy": "c----- ------ ---- ------ ------", "rd": "--x-x- b-x-x- b-x- b-x-x- b-x-x-",
     "sn": "------ O--g-- ---g ------ O--g--"},
    {"cy": "------ ------ k--- ------ ------", "rd": "b-x-x- b-x-x- --x- b-x-x- b-x-x-",
     "sn": "---g-- O----- ---- ---g-- O----g"},
    {"cy": "d----- ------ ---- ------ ------", "rd": "--x-x- b-x-x- b-x- b-x-x- b-x-b-",
     "sn": "------ O--g-g ---- ------ O--g--"},
    {"cy": "------ ------ ---- k----- ------", "rd": "b-x-x- b-x-x- b-x- --x-x- b-x-x-",
     "sn": "------ O----- ---g ---g-- O-g--g"},
]  # fmt: skip
# The hands for the third pulse: the stack cymbal and the snare drum on each pulse.
HANDS_ALL = [
    {"cy": "c----- k----- k--- k----- k-----", "sn": "---g-- O--g-- O-g- O--g-- O--g-g"},
    {"cy": "k----- k----- k--- k----- k-----", "sn": "O--g-- O--g-g O--- O-g-g- O--g--"},
]
# Fills for the hands in the last pulse, or in the last two pulses, of a bar. The feet
# go on below the fill.
END_FILLS = {
    "roll": {"sn": "OoOoOo"},
    "toms": {"sn": "Oo----", "tm": "--hmff"},
    "roll 2": {"sn": "o-oOoo OoOOOO"},
    "toms 2": {"sn": "OoO--- ------", "tm": "---hhm mmffll"},
    "down 2": {"sn": "O-o--- ------", "tm": "--hh-m m-ffll"},
}
ROLL = {"sn": "oooooo oooooo oooo OoOoOo OOOOOO"}  # the bar of the run up
HITS = {"cy": "C----- C----- C--- C----- C-----", "sn": "O----- O----- O--- O----- O-OOOO"}

ROOTS_LOW = 30  # the lowest string of the guitar is F-sharp 1


def drum_bar(hands: dict[str, str], kick: str, fill: str = "") -> str:
    """Return one bar of the drums: the rows of the hands, a fill at its end, and the kick."""
    rows = dict(hands)
    if fill:
        new = {name: groups.split() for name, groups in END_FILLS[fill].items()}
        size = len(next(iter(new.values())))
        empty = ["-" * steps for steps in m.STEPS]
        for name in {*rows, *new}:
            groups = rows.get(name, " ".join(empty)).split()
            groups[-size:] = new.get(name, empty[-size:])
            rows[name] = " ".join(groups)
    rows["bd"] = kick
    return drums.steps("\n".join(f"{name} {groups}" for name, groups in rows.items()), m.CLAVE)


def note_name(midi: int, flats: bool = False) -> str:
    return from_midi(midi, prefer_sharps=not flats).name


def flat_root(root: int) -> bool:
    """Return True if the chords on a root are written with flats (D-flat, E-flat, F, ...)."""
    return root % 12 in (0, 1, 3, 5, 8, 10)


def bass_root(symbol: str) -> int:
    """Return the root of a chord in the low octave of the bass guitar (MIDI number)."""
    root = chords.parse(symbol).bass
    while root < m.BASS_LOW:
        root += 12
    while root > m.BASS_HIGH:
        root -= 12
    return root


def riff_tables(root: int, flats: bool = False) -> tuple[dict[str, str], dict[str, str]]:
    """Return the notes of the riff on a root: for the guitar and for the bass guitar.

    `root` is the MIDI number of the low note of the bass guitar. The low
    note of the guitar is the same note, or one octave higher if that note
    is below the lowest string.
    """
    low = root if root >= ROOTS_LOW else root + 12
    chord = " ".join(note_name(low + step, flats) for step in (0, 7, 12))
    guitar = {"a": note_name(low, flats) + r" \pm", "b": f"<{chord}> \\pmoff"}
    bass = {"a": note_name(root, flats), "b": note_name(root, flats)}
    return guitar, bass


def scale_up(start: int, count: int, key: int) -> list[int]:
    """Return `count` notes of the Lydian scale of a key that go up from `start`."""
    steps = {(key + step) % 12 for step in (0, 2, 4, 6, 7, 9, 11)}
    notes = []
    midi = start
    while len(notes) < count:
        if midi % 12 in steps:
            notes.append(midi)
        midi += 1
    return notes


def sixteenths(notes: list[int], flats: bool, slur: bool = True) -> str:
    """Return the notes as sixteenth notes under one slur."""
    words = [note_name(midi, flats) for midi in notes]
    words[0] += "16(" if slur else "16"
    if slur:
        words[-1] += ")"
    return " ".join(words)


# ----------------------------------------------------------------------------
# The fall
# ----------------------------------------------------------------------------

FALL_BARS = 14
FALL_CUT = 9  # the render makes a new part after this bar of the fall
FALL_END = 56.0  # the tempo at the end of the fall (quarter notes in a minute)
SINK = -6.0  # the fall of the pitch of the recording, in semitones
# The stems that the long edits change (see `audio/glitch.py`). The recorded sounds do
# not change: the sound of the Sun stays where it is.
BAND = ("drums", "eperc", "bass", "sbass", "gtr", "keys", "tsax", "horns", "tpt", "asax", "tbn",
        "bsax", "strings", "vn1", "vn2", "va", "vc", "pad", "lead", "chip")  # fmt: skip
# The division of the pulses in each bar of the fall: the kick drum, the guitar (one
# stage later), and the bass guitar (one stage earlier). They go out of step.
FALL_KICK = [
    KICK_16, KICK_16, KICK_16, KICK_16, KICK_16, KICK_16,
    "xxxxx xxxxx xxx xxxxx xxxxx",
    "xxxx xxxx xx xxxx xxxx",
    "xxx xxx xx xxx xxx",
    "xx xx x xx xx",
    "x x x x x",
    "x - x x -",
    "x - - x -",
    "x - - - -",
]  # fmt: skip
FALL_HANDS = [
    {"cy": "C----- ------ k--- k----- ------", "hh": "--o-x- x-o-x- --x- --o-x- x-o-x-",
     "sn": "------ O--g-- ---- ------ O-----"},
    {"cy": "------ ------ k--- ------ ------", "hh": "x-o-x- x-o-x- --x- x-o-x- x-x-o-",
     "sn": "------ O----- ---- ---g-- O-----"},
    {"cy": "k----- ------ ---- ------ ------", "hh": "--x-x- x-o-x- x-x- x-x-x- x-x-o-",
     "sn": "------ O----- ---g ------ O-----"},
    {"cy": "------ ------ ---- k----- ------", "hh": "x-x-x- x-x-x- x-x- --x-x- x-x---",
     "sn": "------ O----- ---- ------ O--g--"},
    {"rd": "b-x-x- b-x-x- b-x- b-x-x- b-x---", "sn": "------ O----- ---- ------ O-----"},
    {"rd": "b-x--- b-x-x- b--- b-x--- b-----", "sn": "------ O----- ---- ------ O--g--"},
    {"cy": "k k k k -", "sn": "- O - - O"},
    {"cy": "k - k - -", "sn": "- O - - O"},
    {"cy": "k-- --- -- --- ---", "tm": "--- h-m f- l-- ---", "sn": "--- --- -- --- O--"},
    {"tm": "h - m - f", "sn": "- - - O -"},
    {"tm": "- f - l -"},
    {"tm": "- - - - l"},
    {},
    {},
]  # fmt: skip
FALL_GUITAR = [
    "B__aaa B__aaa B_aa B__aaa B__aaa",
    "B__aaa aaaaaa B_aa aaaaaa B__aaa",
    "B__aaa aaaaaa aaaa B__aaa aaaaaa",
    "B__aaa aaaaaa aaaa aaaaaa B__aa-",
    "B__aaa aa-aaa aaaa aaaaaa aa-aa-",
    "B__aaa a-aaaa aa-a aaa-aa a-aa--",
    "B__aaa a-aa-a aa-a aaa-aa a--a--",
    "B_aaa a-aa- aaa a-a-a aa---",
    "B_aa a-a- aa a-a- a---",
    "B_a a-a a- a-- a--",
    "B_ a- a a- --",
]
FALL_BASS = [
    "Aaaaaa A__aaa Aaaa Aaaaaa A__aaa",
    "Aaaaaa aaaaaa A_aa aaaaaa A__aaa",
    "Aaaaaa aaaaaa aaaa A__aaa aaaaaa",
    "Aaaaaa aaaaaa aaaa A__aaa aaaa--",
    "Aaaaaa aa-aaa aaaa A__aa- aaa---",
    "Aaaaa A_aaa Aaa Aaaaa A_aa-",
    "Aaaa A_aa Aa Aaaa A_a-",
    "Aaa A_a Aa Aaa A--",
    "Aa A_ A Aa A_",
    "A A A A A",
]
# The chords of the electric piano and the synthesizer: semitones above the root of the
# bar. A wide chord, then fourths, then three notes, then two.
FALL_CHORDS = [
    (0, 7, 11, 16, 21), (0, 5, 10, 15, 19), (0, 5, 10, 15, 19), (0, 5, 10, 15, 19),
    (0, 5, 10, 15), (0, 5, 10, 15), (0, 5, 10, 15), (0, 5, 10), (0, 5, 10), (0, 5, 10),
    (0, 2, 5), (0, 2, 5), (0, 2, 5), (0, 5),
]  # fmt: skip
FALL_CHORD_RHYTHM = ["A A A A A", "A A A A A", "A A - A -", "A A - A -", "A A - A -",
                     "A - - A -", "A - - A -", "A - - A -", "A - - A -", "A _ _ _ _",
                     "A _ _ _ _", "A _ _ _ _", "A _ _ _ _", "A _ _ _ _"]  # fmt: skip
# The saxophone: the motto goes down (three steps and a fourth), each time lower, through
# the full range. From bar 5 it holds its three lowest notes.
FALL_SAX = [
    r"b''4.->( a''4. g''4 d''4.) r4.",
    r"f''4.->( es''4. des''4 as'4.) r4.",
    r"d'4.->( c'4. bes4 f4.) r4.",
    r"gis4.->( fis4. e4 b,4.) r4.",
    r"bes,1..->",
    r"a,1..",
    r"as,1..",
]
FALL_TRUMPET = [
    r"b''4.->( a''4. g''4 d''4.) r4.",
    r"f''4.->( es''4. des''4 as'4.) r4.",
    r"d''4.->( c''4. bes'4 f'4.) r4.",
    r"gis'4.->( fis'4. e'4 b4.) r4.",
]
# The strings: the note that each group holds, the bar in which it starts to fall, and
# its lowest open string.
FALL_STRINGS = {"vn1": (95, 1, 55), "vn2": (91, 3, 55), "va": (86, 5, 48), "vc": (69, 6, 36)}
# The low horns hold a chord of two fifths (root, fifth, ninth). It moves down with the
# bars, and each player stops at the lowest note of the instrument, or before it.
FALL_HORNS = {"bsax": (43, 8), "tbn": (50, 11), "asax": (69, 10)}  # the first note, the last bar
# The loudness of the fall: the bar and the mark.
FALL_LEVELS = {1: r"\ff", 5: r"\f", 8: r"\mf", 10: r"\mp", 12: r"\p", 14: r"\pp"}


def fall_tempo(structure, first: int) -> None:
    """Write the tempo plan of the fall: slowly at first, then faster and faster."""
    structure.change(first, 1, "the tempo falls: slowly, then faster and faster")
    for number in range(1, FALL_BARS):
        bpm = m.FAST - (m.FAST - FALL_END) * (number / FALL_BARS) ** 2
        structure.arrive(first + number, 1, bpm)
        structure.change(first + number, 1, "")  # the tempo goes on to the next value
    # The end of the last bar (the "beat 15" of a bar of 14 eighth notes).
    structure.arrive(first + FALL_BARS - 1, 15, FALL_END)


def falling_line(start: int, first_bar: int, floor: int) -> list[str]:
    """Return the bars of one string group in the fall.

    The group holds `start`. From the bar `first_bar` it goes down one
    semitone on each pulse, to its lowest open string `floor`. Then it holds
    that string to the end.
    """
    values = ["4.", "4.", "4", "4.", "4."]
    pitch = start
    bars = []
    for number in range(1, FALL_BARS + 1):
        notes = []
        for _pulse in values:
            notes.append(pitch)
            if number >= first_bar and pitch > floor:
                pitch -= 1
        if len(set(notes)) == 1:
            # A held note: with a tie if the bar after it has the same note. No tie goes
            # through the cut of the render.
            held = pitch == notes[0] and number < FALL_BARS and number != FALL_CUT
            tie = " ~" if held else ""
            bars.append(f"{note_name(notes[0], True)}1..{tie}")
        else:
            words = [
                note_name(midi, True) + value for midi, value in zip(notes, values, strict=True)
            ]
            words[0] += "("
            words[-1] += ")"
            bars.append(" ".join(words))
    return bars


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]

    # ------------------------------------------------- S: the theme with all force
    s = Bars(work, 8)
    structure.mark(s.bar(1), "S")
    structure.tempo(s.bar(1), 1, m.FAST, "With all force: the feet never stop")
    symbols = m.LOOP_A * 2
    s.set("tsax", THEME_FORCE, r"\ff\normaltone")
    s.set("tpt", THEME_FORCE_TRUMPET, r"\ff")
    second = [tools.tr(bar, -3) if n % 4 != 1 else tools.tr(bar, -4)
              for n, bar in enumerate(THEME_FORCE_TRUMPET)]  # fmt: skip
    s.set("asax", tools.true_ties(second), r"\f")
    guitar, bass = [], []
    for number, symbol in enumerate(symbols):
        guitar_notes, bass_notes = riff_tables(bass_root(symbol), symbol[1:2] == "b")
        guitar.append(patterns.pitched(RIFFS[number % 4], m.CLAVE, guitar_notes))
        bass.append(patterns.pitched(RIFFS[number % 4].replace("B", "A"), m.CLAVE, bass_notes))
    s.set("gtr", guitar, r"\ff\highgain")
    s.set("bass", bass, r"\ff\pick")
    low_horns = m.layers(symbols, LOW_HORNS, ("bsax", "tbn"), "horns2")
    for player, bars in low_horns.items():
        s.set(player, bars, r"\ff")
    # The strings go up through the eight bars: B4, D5, E5, G5, A5, B-flat 5, B5, D6.
    strings = m.layers(symbols, ["a_____ ______ ____ ______ ______"], m.STRINGS, "strings",
                       tops=[71, 74, 76, 79, 81, 82, 83, 86])  # fmt: skip
    for player, bars in strings.items():
        s.set(player, tools.first(patterns.join(bars), r"\f\<", note=True))
    fills = {4: "toms", 8: "roll 2"}
    s.set(
        "drums",
        [drum_bar(HANDS_OPEN[n % 4], KICKS_8[n % 4], fills.get(n + 1, "")) for n in range(8)],
        r"\ff",
    )
    s.set("keys.rh", mainseq._comp(symbols, mainseq.C_KEYS), r"\f")
    s.set("pad.rh", m.pad_bars(symbols, low=60, high=84), r"\f", r'\switch "supersaw"')
    s.set("sbass", m.roots(symbols, "a_____ ______ a___ ______ ______"), r"\f",
          r'\switch "bass sub"')  # fmt: skip
    arps = []
    for number, symbol in enumerate(symbols):
        notes = chords.voice(symbol, 4, low=79, high=98)
        table = {k: chords.names((n,), symbol) for k, n in zip("abcd", notes, strict=True)}
        shape = ["abcdab cdabcd abcd abcdab cdabcd", "dcbadc badcba dcba dcbadc badcba"][number % 2]
        arps.append(patterns.pitched(shape, m.CLAVE, table))
    s.set("chip", arps, r"\mf", r'\switch "chip pulse"')
    machine = drums.steps("ms  ------ c----- ---- ------ c-----\nmh  xxxxxx xxxxxx xxxx xxxxxx xxxxxx",
                          m.CLAVE)  # fmt: skip
    # A low stroke and a falling low tone on the first beat: the start after the helium flash.
    arrival = r"<< { " + machine + r" } \\ { <es,, ges,,>1.. } >>"
    s.set("eperc", [arrival] + [machine] * 7, r"\mf")
    s.close()

    # ------------------------------------------------- T: the longest line
    s = Bars(work, 8)
    structure.mark(s.bar(1), "T")
    line = [bar.replace("(", "").replace(")", "") for bar in [*m.LINE_1, *m.LINE_2, *LINE_END]]
    # The saxophone player has one bar of rest to breathe.
    s.set("tsax", [*line[:3], None, *line[4:]], r"\ff")
    s.set("gtr", line, r"\ff\leadtone\pmoff")
    s.set("lead", [tools.octave(bar, 1) for bar in line], r"\ff", r'\switch "lead moog"')
    s.set("chip", [tools.octave(bar, 2) for bar in line], r"\f")
    s.set("bass", [tools.octave(bar, -2) for bar in line], r"\ff")
    s.set("keys.rh", line, r"\f")
    fills = {4: "down 2", 8: "roll 2"}
    s.set(
        "drums",
        [drum_bar(HANDS_BELL[n % 4], KICK_16, fills.get(n + 1, "")) for n in range(8)],
        r"\ff",
    )
    hits = m.layers(symbols, ["A_____ ------ ---- ------ ------", "------ ------ ---- A_____ ------"],
                    m.HORNS, "horns")  # fmt: skip
    for player, bars in hits.items():
        s.set(player, bars, r"\ff")
    strings = m.layers(symbols, ["a_____ ______ ____ ______ ______"], m.STRINGS, "strings",
                       tops=[79, 79, 79, 81, 83, 82, 83, 86])  # fmt: skip
    for player, bars in strings.items():
        s.set(player, bars, r"\f")
    s.set("sbass", m.roots(symbols, "a_____ ______ a___ ______ ______"), r"\f")
    s.set("eperc", [machine] * 8, r"\mf")
    s.close()

    # ------------------------------------------------- U: three thermal pulses
    s = Bars(work, 12)
    structure.mark(s.bar(1), "U")
    # Each pulse: the name of the chord, semitones above G, flats, the chord of the five
    # strokes (the chord before the next key), and the note of the strokes of the lead
    # players.
    pulses = [
        ("Gmaj9", 0, False, "F#13sus", 78),
        ("Bmaj9", 4, False, "Bb13sus", 82),
        ("Ebmaj9", 8, True, "D13sus", 84),
    ]
    parts: dict[str, list[str | None]] = {name: [] for name in (
        "tsax", "tpt", "asax", "gtr", "bass", "drums", "keys.rh", "pad.rh", "sbass", "lead", "chip",
        "vn1", "vn2", "va", "vc", "bsax", "tbn", "eperc")}  # fmt: skip
    for number, (name, step, flats, turn, top) in enumerate(pulses):
        key = 7 + step  # the pitch class of the key
        # The motto goes up; the saxophone starts it with an accented low note.
        low = note_name(55 + step - (12 if step else 0), flats)
        motto = [tools.tr(r"c''4.( ~ c''4 d''4. e''4. ~", step), tools.tr(r"e''1..)", step)]
        run_start = 55 + step if step < 8 else 51
        run = sixteenths(scale_up(run_start, 12, key), flats)
        turn_flats = turn[1:2] == "b" or flats
        stroke = note_name(top, turn_flats)
        strokes = f"{stroke}4.-> {stroke}4.-> {stroke}4-> {stroke}4.-> {stroke}4.->"
        parts["tsax"] += [f"{low}4.-> {motto[0]}", motto[1], f"r4. r4. r4 {run}", strokes]
        trumpet = [tools.tr(r"g'4.( c''4. ~ c''4 d''4. e''4. ~", step), motto[1]]
        trumpet_run = run if run_start >= 54 else sixteenths(scale_up(63, 12, key), flats)
        parts["tpt"] += [*trumpet, f"r4. r4. r4 {trumpet_run}", strokes]
        alto = [tools.tr(r"e'4.( a'4. ~ a'4 b'4. c''4. ~", step), tools.tr(r"c''1..)", step)]
        # The second voice of the strokes: the note of the chord a fourth below.
        under = note_name(top - 5, turn_flats)
        parts["asax"] += [*alto, None,
                          f"{under}4.-> {under}4.-> {under}4-> {under}4.-> {under}4.->"]  # fmt: skip
        # The riff, the run, and the five strokes of the guitar and the bass guitar.
        root = 31 + step if step < 8 else 27
        guitar_notes, bass_notes = riff_tables(root, flats)
        turn_guitar, turn_bass = riff_tables(bass_root(turn), turn[1:2] == "b")
        for pattern, table_g, table_b in (
            (RIFFS[number % 4], guitar_notes, bass_notes),
            (RIFFS[(number + 2) % 4], guitar_notes, bass_notes),
            (RIFF_RUN, guitar_notes, bass_notes),
            (STROKES, turn_guitar, turn_bass),
        ):
            parts["gtr"].append(patterns.pitched(pattern, m.CLAVE, table_g))
            parts["bass"].append(patterns.pitched(pattern.replace("B", "A"), m.CLAVE, table_b))
        # The drums: each pulse has more strokes than the pulse before.
        if number == 0:
            grooves = [drum_bar(HANDS_BELL[0], KICKS_8[0]), drum_bar(HANDS_BELL[1], KICKS_8[2])]
        elif number == 1:
            grooves = [drum_bar(HANDS_BELL[2], KICK_16), drum_bar(HANDS_BELL[3], KICK_16, "toms")]
        else:
            grooves = [drum_bar(HANDS_ALL[0], KICK_16), drum_bar(HANDS_ALL[1], KICK_16, "roll")]
        parts["drums"] += [*grooves, drum_bar(ROLL, KICK_16), drum_bar(HITS, KICK_16)]
        # The chords: two bars of the key, the run, the five strokes.
        chord = chords.voice(name, 4, low=58, high=82)
        chord_text = chords.names(chord, name)
        turn_text = chords.names(chords.voice(turn, 4, low=58, high=82), turn)
        hold = patterns.pitched("a_____ ______ ____ ______ ______", m.CLAVE, {"a": chord_text})
        five = patterns.pitched("A_____ A_____ A___ A_____ A_____", m.CLAVE, {"a": turn_text})
        run_keys = sixteenths(scale_up(55 + step, 16, key), flats)
        parts["keys.rh"] += [*mainseq._comp([name] * 2, mainseq.F_KEYS),
                             f"{chord_text}2.-> {run_keys}", five]  # fmt: skip
        parts["pad.rh"] += [hold, hold, hold, five]
        sub = m.roots([name] * 3, "a_____ ______ a___ ______ ______")
        parts["sbass"] += [*sub, m.roots([turn], "a_____ ______ ____ ______ ______")[0]]
        # The run up of the strings, the lead synthesizer, and the chip synthesizer: 16
        # notes in the last three pulses of the third bar.
        first = 67 + step if step < 8 else 63
        high_run = scale_up(first, 16, key)
        top_note = note_name(high_run[0], flats)
        parts["vn1"] += [None, None, f"{top_note}2.\\< {sixteenths(high_run, flats)}", None]
        low_run = [midi - 12 for midi in high_run] if high_run[0] - 12 >= 55 else high_run
        parts["vn2"] += [None, None,
                         f"{note_name(low_run[0], flats)}2.\\< {sixteenths(low_run, flats)}", None]  # fmt: skip
        parts["lead"] += [None, None, f"r2. {sixteenths(high_run, flats)}", None]
        chip_run = [midi + 12 for midi in high_run] if high_run[-1] + 12 <= 108 else high_run
        parts["chip"] += [None, None, f"r2. {sixteenths(chip_run, flats, slur=False)}", None]
        for player in ("va", "vc", "bsax", "tbn"):
            parts[player] += [None, None, None, None]
        rise = r"R1*14/8*2 | e,,1..\mf\< ~ | e,,1..\f"
        parts["eperc"].append(rise)
    # The held chords and the strokes of the strings and the low horns, from the chords.
    chord_names = [name for name, *_rest in pulses for _ in range(3)]
    turn_names = [turn for _name, _step, _flats, turn, _top in pulses]
    for kind, players in (("strings", m.STRINGS), ("horns2", ("bsax", "tbn"))):
        shapes = ["a_____ ______ ____ ______ ______"]
        if kind == "horns2":
            shapes = [LOW_HORNS[0], LOW_HORNS[2], "a_____ ______ ____ ______ ------"]
        held = m.layers(chord_names, shapes, players, kind)
        five = m.layers(turn_names, ["A_____ A_____ A___ A_____ A_____"], players, kind)
        for player in players:
            for number in range(3):
                bars = [*held[player][3 * number : 3 * number + 3], five[player][number]]
                for place, bar in enumerate(bars):
                    if parts[player][4 * number + place] is None:
                        parts[player][4 * number + place] = bar
    for player in ("tsax", "tpt", "asax", "gtr", "bass", "drums", "keys.rh", "pad.rh", "sbass",
                   "lead", "chip", "vn1", "vn2", "va", "vc", "bsax", "tbn"):  # fmt: skip
        mark = r"\ff" if player in ("tsax", "tpt", "gtr", "bass", "drums", "lead") else r"\f"
        prefix = r'\switch "lead moog"' if player == "lead" else ""
        if player == "gtr":
            mark += r"\highgain"
        s.set(player, parts[player], mark, prefix)
    s.set("eperc", " | ".join(parts["eperc"]) + " |")
    s.close()

    # ------------------------------------------------- V: the fall
    s = Bars(work, FALL_BARS)
    structure.mark(s.bar(1), "V")
    fall_tempo(structure, s.bar(1))
    levels = FALL_LEVELS

    def marked(bars: list[str | None], shift: int = 0) -> list[str | None]:
        """Return the bars with the loudness of the fall on the first note of some bars."""
        result: list[str | None] = []
        for number, bar in enumerate(bars, start=1):
            mark = levels.get(number + shift)
            result.append(tools.first(bar, mark, note=True) if bar and mark else bar)
        return result

    # The drums.
    drum_bars = []
    for number in range(FALL_BARS):
        rows = dict(FALL_HANDS[number])
        rows["bd"] = FALL_KICK[number]
        text = "\n".join(f"{name} {groups}" for name, groups in rows.items())
        drum_bars.append(drums.steps(text, m.CLAVE))
    s.set("drums", marked(drum_bars))
    # Guitar and bass guitar: each bar one semitone lower (the root of the first bar is G2).
    guitar_bars: list[str | None] = []
    bass_bars: list[str | None] = []
    for number in range(FALL_BARS):
        root = 43 - number
        flats = flat_root(root)
        chord = " ".join(note_name(root + step, flats) for step in (0, 7, 12))
        if number == 0:
            chord = note_name(root - 12, flats) + " " + note_name(root - 5, flats) + " " + chord
        table = {"a": note_name(root, flats) + r" \pm", "b": f"<{chord}> \\pmoff"}
        if number < len(FALL_GUITAR):
            guitar_bars.append(patterns.pitched(FALL_GUITAR[number], m.CLAVE, table))
        else:
            # One long note that bends down to the note of the next bar.
            bend = r"\glissando" if number < FALL_BARS - 1 else ""
            guitar_bars.append(f"{note_name(root, flats)}1..\\pmoff{bend}")
        if number < len(FALL_BASS):
            notes = {"a": note_name(root, flats)}
            bass_bars.append(patterns.pitched(FALL_BASS[number], m.CLAVE, notes))
        else:
            bass_bars.append(f"{note_name(root, flats)}1..")
    s.set("gtr", marked(guitar_bars))
    s.set("bass", marked(bass_bars))
    s.set("sbass", marked([f"{note_name(31 - n, flat_root(31 - n))}1.." for n in range(4)]
                          + [None] * (FALL_BARS - 4)))  # fmt: skip
    # The chords become narrow and go to the low register.
    key_bars: list[str | None] = []
    pad_bars: list[str | None] = []
    for number in range(FALL_BARS):
        root = (67 if number < 7 else 55) - number
        flats = flat_root(root)
        notes = " ".join(note_name(root + step, flats) for step in FALL_CHORDS[number])
        key_bars.append(patterns.pitched(FALL_CHORD_RHYTHM[number], m.CLAVE, {"a": f"<{notes}>"}))
        high = " ".join(note_name(root + 12 + step, flats) for step in FALL_CHORDS[number])
        pad_bars.append(f"<{high}>1.." if number < 9 else None)
    s.set("keys.rh", marked(key_bars))
    s.set("pad.rh", marked(pad_bars))
    # The lead players.
    s.set("tsax", marked([*FALL_SAX, *[None] * (FALL_BARS - len(FALL_SAX))]))
    s.set("tpt", marked([*FALL_TRUMPET, *[None] * (FALL_BARS - len(FALL_TRUMPET))]))
    for player, (start, last) in FALL_HORNS.items():
        bars = []
        for number in range(FALL_BARS):
            if number >= last:
                bars.append(None)
            elif number % 2 == 1:
                # A wind player must breathe: each second bar ends with a rest.
                name = note_name(start - number, flat_root(43 - number))
                bars.append(f"{name}1-> ~ {name}4. r4.")
            else:
                bars.append(f"{note_name(start - number, flat_root(43 - number))}1..->")
        s.set(player, marked(bars))
    for player, (start, first_bar, floor) in FALL_STRINGS.items():
        s.set(player, marked(falling_line(start, first_bar, floor)))
    # One high tone of the synthesizer bends down through the fall: the fourth note of
    # the motto (E), which stays at the end of the work.
    lead = [f"{note_name(88 - n, True)}1..\\glissando" for n in range(FALL_BARS - 1)]
    lead.append(f"{note_name(88 - FALL_BARS + 1, True)}1..\\pp")
    s.set("lead", lead, r"\mp\>", r'\switch "lead moog"')
    # The chip synthesizer: a figure that goes down, with fewer and fewer notes.
    figures = ["abcdab cdabcd abcd abcdab cdabcd", "abcdab cdabcd abcd abcd-b cdab-d",
               "abcd-b cdab-d abcd a-cdab cd--cd", "abc--b cd-b-d a-cd a--dab c---c-",
               "abcda bcd-b cda b-dab cd---", "abcd a-cd ab cd-- a---", "abc d-- a- --- b--",
               "a- -- c -- --", "- - - a -", "- - - - d"]  # fmt: skip
    chip_bars: list[str | None] = []
    for number, figure in enumerate(figures):
        table = {letter: note_name(midi - number, True)
                 for letter, midi in zip("abcd", (91, 88, 86, 83), strict=True)}  # fmt: skip
        chip_bars.append(patterns.pitched(figure, m.CLAVE, table))
    s.set("chip", marked(chip_bars + [None] * (FALL_BARS - len(chip_bars))),
          prefix=r'\switch "chip pulse 12"')  # fmt: skip
    # The drum machine: a low stroke on the first beat, then noise that falls, then low
    # tones that fall.
    s.set(
        "eperc",
        r"<es,, ges,,>1..\f | R1*14/8*2 | f,,1..\mf ~ | f,,1.. ~ | f,,1.. ~ | f,,1.. ~ | "
        r"f,,1.. | R1*14/8*2 | es,,1..\mf | R1*14/8*2 | es,,1..\mp |",
    )
    # The recording itself: the pitch falls, a filter closes, the sound goes to the centre.
    quarters = 7 * FALL_BARS
    edits += [
        Edit("sink", s.bar(1), 1, length=quarters, stems=BAND, pitch=SINK, curve=2.0),
        Edit("darken", s.bar(5), 1, length=quarters - 28, stems=BAND, start=18000.0, end=900.0,
             curve=1.5),
        Edit("narrow", s.bar(5), 1, length=quarters - 28, stems=BAND, width=0.2, curve=1.5),
    ]  # fmt: skip
    # The sound of the Sun comes in below the last bars. (A cue stays inside one part of
    # the render and some seconds more: the next part of the work has the next cue.)
    start = structure.seconds(structure.bar(s.bar(FALL_CUT + 1)).start)
    end = structure.seconds(structure.bar(s.bar(FALL_BARS)).end)
    cues.append(Cue("sun", s.bar(FALL_CUT + 1), 1, seconds=end - start + 4.5, gain_db=-15.0,
                    fade=4.0, seed=11))  # fmt: skip
    s.close()
    # The render makes a new part after a double bar line: no long note goes through it.
    structure.double_bar(s.bar(FALL_CUT))
    structure.double_bar(s.section.last_bar)
