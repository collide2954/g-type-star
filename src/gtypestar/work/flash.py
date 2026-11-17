"""Part 6: the helium flash. Helium starts to burn in the core, all at one time.

This is the only dubstep passage of the work: 16 bars at 140 quarter notes
in a minute, 27.4 seconds (decision of the owner: one time, 30 seconds or
less). The part before it ends with a build-up and one short silence (see
`giant.py`). The first beat of this part is the "drop".

The owner heard the second version and said that the passage "sounds
corny". That version had six bass sounds that took turns from beat to beat,
a drum machine on top of the drums, and pieces of the word "fire". This
version is bass music that a band plays:

- One riff, made from the motto in a minor key (G, C, D, E-flat). The bass
  guitar, the bass synthesizer and the guitar play it together. The kick
  drum plays its notes in the first eight bars, and keeps these strokes
  when the riff gets sixteenth notes.
- The drums play in half time: the snare drum on beat 3. The third beat of
  the riff starts with a rest: there the snare drum is alone.
- One bass sound for the first twelve bars (out-of-tune sawtooth waves with
  a notch that moves slowly: the "Reese" bass), and a harder sound for the
  three bars with the motto in quarter notes.
- The first eight bars state the riff, and the saxophone answers in its
  gaps. In the second eight bars the riff has sixteenth notes, the horns
  play its first note with the bass, and then all players have the motto
  one note to a beat: up (G, C, D, E-flat) and down (F, E-flat, D, C).
- The band is cut and repeated at the ends of three phrases (bars 4, 8, 12).

The last bar has five equal notes in the time of four beats: these notes
have the speed of the beat of the next part (175 quarter notes in a minute).
It is the only division in five of the work.

Style profile: "Dubstep" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..compose import patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
BEATS = (2, 2, 2, 2)
BAR = (8,)  # the full bar as one pulse: five letters are five notes in the time of four beats
# The riff: one bar in each entry, four beats of sixteenth notes. The letters are the
# notes of `NOTES`. A capital letter has an accent.
RIFF = [
    # The first eight bars: the motto goes up through two bars (G ... C, D | E-flat).
    "A___ ____ --a- c-d-",
    "E___ __d- -c-a ----",
    "A___ ____ --a- c-d-",
    "F___ __e- -d-c b-a-",
    "A___ __a- -a-c --d-",
    "E___ e-d- -c-a --ag",
    "A_a- -a-a --a- c-d-",
    "F___ ____ ---- ----",
    # The second eight bars: the same riff with sixteenth notes.
    "A_aa -aa- -aaa c-d-",
    "E_ee -ee- -d-c a-ag",
    "A_aa -aa- -aaa c-d-",
    "F_ff -ff- -e-d c-b-",
    # The motto, one note to a beat, up and down. Then the low G.
    "A_aa C_cc D_dd E_ee",
    "F_ff E_ee D_dd C_cc",
    "AAaa AAaa AAAA AAAA",
]
NOTES = {"a": "g,,", "b": "bes,,", "c": "c,", "d": "d,", "e": "es,", "f": "f,", "g": "g,"}
# The last bar: five notes that go up to the leading note of the next part (G major).
LAST_NOTES = ("g,,", "bes,,", "c,", "d,", "fis,")
# The guitar plays the riff one octave above the bass. A short note is one note with
# the palm of the hand on the strings; a note that is held is an open chord of root,
# fifth and octave (the letters p to t).
GUITAR = {
    "a": r"g, \pm", "b": r"bes, \pm", "c": r"c \pm", "d": r"d \pm", "e": r"es \pm",
    "f": r"f \pm", "g": r"g \pm",
    "p": r"<g, d g> \pmoff", "q": r"<c g c'> \pmoff", "r": r"<d a d'> \pmoff",
    "s": r"<es bes es'> \pmoff", "t": r"<f c' f'> \pmoff",
}  # fmt: skip
HELD = {"a": "p", "c": "q", "d": "r", "e": "s", "f": "t"}
# The hands of the drummer: one bar in each entry. The kick drum has the notes of the
# riff. Bars 4, 8 and 12 end with a fill; bar 15 is a roll that grows.
HANDS = [
    "cy C--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- O--- ----",
    "hh x-x- x-x- x-x- x-o-\nsn ---- ---- O--- -g--",
    "hh x-x- x-x- x-x- x-x-\nsn ---- ---g O--- ----",
    "hh x-x- x-x- x-x- ----\nsn ---- ---- O--- o-oo",
    "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- O--- ----",
    "hh x-x- x-o- x-x- x-x-\nsn ---- ---- O--g ----",
    "hh x-x- x-x- x-x- x-x-\nsn ---g ---- O--- --g-",
    "hh x-x- x-x- ---- ------\nsn ---- ---- O-oo oooooo",
    "cy C--- k--- k--- k---\nsn ---- ---- O--- ----",
    "cy k--- k--- k--- k---\nsn ---- ---- O--- -g-g",
    "cy k--- k--- k--- k---\nsn ---- --g- O--- ----",
    "cy k--- k--- k--- ----\nsn ---- ---- O--- oo-o\ntm ---- ---- ---- --f-",
    "cy c--- c--- c--- c---\nsn ---- ---- O--- ----",
    "cy c--- c--- c--- c---\nsn ---- ---- O--- ----",
    "cy c--- c--- c--- c---\nsn o--- o--- o-o- oooo",
]
# The kick drum of bar 8: the riff has one long note there, and the feet end the fill.
KICK_8 = "x--- ---- ---- x-----"
# Bars 9 to 12: the riff has sixteenth notes, but the kick drum keeps its strokes of
# bars 1 to 4, with one more stroke before the second beat. The groove of the drums
# comes again each two bars: the ear has the half time, and the fast notes are for the
# bass and the guitar. (In the third version the kick drum had each note of the riff:
# ten strokes in a bar, and no bar like the bar before. The pulse was less clear there
# than in any passage of the reference recordings: `tools/diagnose/pulse.py`.)
KICK_SECOND = "x--x"
# The long sounds of the drum machine: the bar, and its notes.
# es,, = sub drop; ges,, = impact; as,, = cymbal that plays backwards; e,, = noise that rises.
LONG = {
    1: r"<es,, ges,,>2\ff r2",
    8: r"r2 as,,2\f",
    9: r"<es,, ges,,>2\ff r2",
    15: r"e,,1\f",
    16: r"as,,1\ff",
}
# The saxophone in the first nine bars: a stroke with the horns, then answers in the
# gaps of the riff. Each answer starts on the fourth beat and ends on the next first beat.
SAX = [
    r"g4->\growl r4 r2",
    r"r2 r4 d'16( f' g' bes'",
    r"c''8-.) r8 r4 r2",
    r"r2 r4 g'16( bes' c'' d''",
    r"f''8-.) r8 r4 r2",
    r"r2 r4 f''16( d'' c'' bes'",
    r"g'8-.) r8 r4 r2",
    r"r2 g16( bes c' d' f' g' bes' c''",
    r"d''8->) r8 r4 r2",
]
# The horns play notes of the riff, in three octaves: the baritone saxophone; the
# trombone and the tenor saxophone; the alto saxophone and the trumpet.
HORN_NOTES = {
    "bsax": {"a": "g,", "c": "c", "d": "d", "e": "es", "f": "f"},
    "tbn": {"a": "g", "c": "c'", "d": "d'", "e": "es'", "f": "f'"},
    "tsax": {"a": "g", "c": "c'", "d": "d'", "e": "es'", "f": "f'"},
    "asax": {"a": "g'", "c": "c''", "d": "d''", "e": "es''", "f": "f''"},
    "tpt": {"a": "g'", "c": "c''", "d": "d''", "e": "es''", "f": "f''"},
}
# The bar, and the rhythm of the horns in it.
HORN_BARS = {
    1: "A___ ---- ---- ----",
    5: "A___ ---- ---- ----",
    9: "A_-- ---- ---- ----",
    10: "E_-- ---- ---- ----",
    11: "A_-- ---- ---- ----",
    12: "F_-- ---- ---- ----",
    13: "A_-- C_-- D_-- E_--",
    14: "F_-- E_-- D_-- C_--",
    15: "A___ ____ ____ ____",
}
# The last bar of each horn and each string group: five notes with the bass.
LAST_HORNS = {"bsax": "g, bes, c d fis", "tbn": "d f g a c'", "tsax": "g bes c' d' fis'",
              "asax": "bes d' es' fis' a'", "tpt": "g' bes' c'' d'' fis''"}  # fmt: skip
# The strings rise in the second eight bars: two bars on each note, then the last bar.
RISE = ["g''", "g''", "bes''", "bes''", "d'''", "d'''"]


def five(notes: str | tuple[str, ...], marks: str = "->") -> str:
    """Return a bar with five equal notes in the time of four beats."""
    names = notes.split() if isinstance(notes, str) else notes
    return r"\tuplet 5/4 { " + " ".join(f"{name}4{marks}" for name in names) + " }"


def strokes(pattern: str) -> str:
    """Return a drum row with one stroke for each note of a riff."""
    return "".join(char if char == " " else ("x" if char.isalpha() else "-") for char in pattern)


def guitar_bar(pattern: str) -> str:
    """Return one bar of the riff for the guitar: a held note is an open chord."""
    chars = list(pattern)
    for place, char in enumerate(chars):
        later = "".join(chars[place + 1 :]).replace(" ", "")
        if char.isalpha() and later.startswith("_") and char.lower() in HELD:
            chord = HELD[char.lower()]
            chars[place] = chord.upper() if char.isupper() else chord
    return patterns.pitched("".join(chars), BEATS, GUITAR)


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]
    free: set[int] = work.extras.setdefault("free_divisions", set())  # type: ignore[assignment]

    s = Bars(work, 16, COMMON)
    structure.mark(s.bar(1), "R")
    structure.tempo(s.bar(1), 1, m.FLASH, "Half time, heavy")
    free.add(s.bar(16))  # the five notes in four beats: the link to the next tempo

    # ------------------------------------------------- the riff: three players as one
    riff = [patterns.pitched(bar, BEATS, NOTES) for bar in RIFF]
    synth = [*riff, five(LAST_NOTES)]
    synth[0] = r'\switch "bass grind" ' + synth[0]
    synth[12] = r'\switch "bass growl" ' + tools.first(synth[12], r"\fff", note=True)
    s.set("sbass", synth, r"\ff")
    s.set("bass", [*riff, five(LAST_NOTES)], r"\ff")
    guitar = [guitar_bar(bar) for bar in RIFF]
    guitar.append(
        r"\tuplet 5/4 { <g,, d, g,>4->\pmoff <bes,, f, bes,>4-> <c, g, c>4-> <d, a, d>4-> "
        r"<fis,, d, a,>4-> }"
    )
    s.set("gtr", guitar, r"\ff\highgain")

    # ------------------------------------------------- the drums
    kit = []
    for number, (hands, bar) in enumerate(zip(HANDS, RIFF, strict=True), start=1):
        kick = KICK_8 if number == 8 else strokes(bar)
        if 9 <= number <= 12:
            kick = " ".join([KICK_SECOND, *strokes(RIFF[number - 9]).split()[1:]])
        kit.append(drums.steps(f"{hands}\nbd {kick}", BEATS))
    kit[14] = tools.first(kit[14], r"\<", note=True)
    kit.append(tools.first(drums.steps("cy CCCCC\nsn OOOOO\nbd xxxxx", BAR), r"\fff", note=True))
    s.set("drums", kit, r"\ff")
    # The drum machine has no beat here: only the low drop and the stroke at the two
    # starts, a cymbal that plays backwards, and noise that rises in the last bars.
    machine: list[str | None] = [LONG.get(number) for number in range(1, 16)]
    last = drums.steps("ms sssss\nmk hhhhh", BAR)
    machine.append(r"<< { " + last + r" } \\ { " + LONG[16] + " } >>")
    s.set("eperc", machine, r"\ff")

    # ------------------------------------------------- saxophone and horns
    for player, notes in HORN_NOTES.items():
        bars: list[str | None] = [
            patterns.pitched(HORN_BARS[number], BEATS, notes) if number in HORN_BARS else None
            for number in range(1, 16)
        ]
        if player == "tsax":
            bars[:9] = SAX
        bars.append(five(LAST_HORNS[player]))
        s.set(player, bars, r"\ff")

    # ------------------------------------------------- strings and synthesizers
    for player, shift in (("vn1", 0), ("vn2", -1), ("va", -2), ("vc", -2)):
        line = [f"{name}1 ~" if number % 2 == 0 else f"{name}1" for number, name in enumerate(RISE)]
        line += [r"es'''2 d'''2", five("g'' bes'' c''' d''' fis'''")]
        moved = [tools.octave(bar, shift) for bar in line]
        s.set(player, [None] * 8 + moved, r"\mf\<")
    # Chords of the synthesizer: one long chord at each start, and under the motto.
    names = ["Gm11", None, None, None, "Gm11", None, None, None, "Gm9", None, "Gm9", None,
             "Gm9", "Ebmaj7#11", "Gm9"]  # fmt: skip
    held = m.pad_bars(names, "A___ ____ ____ ____", BEATS, low=58, high=82)
    last = r"<g' bes' d''>4-> <bes' d'' f''>4-> <c'' es'' g''>4-> <d'' fis'' a''>4-> <d'' fis'' c'''>4->"
    s.set("pad.rh", [*held, r"\tuplet 5/4 { " + last + " }"], r"\ff", r'\switch "supersaw"')
    s.set("chip", [None] * 15 + [five("g''' bes''' c'''' d'''' fis''''", "")], r"\mf",
          r'\switch "chip pulse 25"')  # fmt: skip

    # ------------------------------------------------- the band is cut and repeated
    edits += [
        # Bar 4: the first half of the last beat comes two times.
        Edit(
            "stutter", s.bar(4), 4, length=1.0, stems=("drums", "bass", "sbass", "gtr"), slice=0.5
        ),
        # Bar 8: the fill of the drums comes again in sixteenth notes.
        Edit("stutter", s.bar(8), 4, length=1.0, stems=("drums",), slice=0.25),
        # Bar 12: the last beat plays backwards.
        Edit("reverse", s.bar(12), 4, length=1.0, stems=("drums", "bass", "sbass", "gtr")),
    ]
    s.close()
    structure.double_bar(s.section.last_bar)
