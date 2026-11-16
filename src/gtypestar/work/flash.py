"""Part 6: the helium flash. Helium starts to burn in the core, all at one time.

This is the only dubstep passage of the work: 16 bars at 140 quarter notes
in a minute, 27.4 seconds (decision of the owner: one time, 30 seconds or
less). The part before it ends with a build-up and one short silence (see
`giant.py`). The first beat of this part is the "drop".

The drums play in half time: kick on beat 1, snare on beat 3. The drum
machine has the hard kick and the heavy snare of the style. The bass
synthesizer has a low sine tone and, above it, six hard sounds that take
turns from beat to beat, as a call and an answer (`audio/dubstep.py`): in
each note a filter moves one time, thus the rhythm of the notes is the
rhythm of the sound. The first eight bars state the figure; the second
eight bars are harder: faster notes, the guitar plays the figure with the
bass, the strings rise. Saxophone and guitar answer in the gaps, and the word
"fire" of the recording comes back in small pieces.

The last bar has five equal notes in the time of four beats: these notes
have the speed of the beat of the next part (175 quarter notes in a minute).

Style profile: "Dubstep" (see research/tables/profiles.csv).
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..audio.tape import Cue
from ..compose import patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import material as m
from .material import Bars

COMMON = (4, 4, ())
BEATS = (2, 2, 2, 2)
BAR = (8,)  # the full bar as one pulse: five letters are five notes in the time of four beats
NOTES = {"a": "g,,", "b": "bes,,", "c": "c,", "d": "d,", "e": "es,,", "f": "f,,", "g": "g,",
         "h": "as,,"}  # fmt: skip
# The sounds of the bass: one letter for each beat of a bar ("." = the sound stays).
SOUND = {"w": "bass wobble", "g": "bass growl", "y": "bass yoi", "s": "bass screech",
         "r": "bass grind", "m": "bass gun"}  # fmt: skip
# The figure of the bass: the rhythm, and the sound of each beat. A long group is a slow
# move of the sound; three letters in a beat are triplets; four are sixteenth notes. The
# third beat starts with a rest: there the snare drum is alone.
RIFF = [
    # The first eight bars: the figure.
    ("A___ ____ --a_ a_a_", "g . y ."),
    ("a_a_ a_a_ --b_ aaaa", "w . g m"),
    ("A___ a_a_ --a_ G___", "g . y s"),
    ("aaa aaa --c_ d_e_", "w . g r"),
    ("A___ ____ --a_ h_a_", "g . y ."),
    ("a___ ____ --a_ aaaaaa", "r . w m"),
    ("a_a_ b_b_ --c_ D___", "g . y s"),
    ("aaa aaa ---- ----", "w . . ."),
    # The second eight bars: harder.
    ("A___ ____ --aa aaaa", "g . m ."),
    ("a_aa a_aa --b_ G_G_", "w . g s"),
    ("A_a_ a_a_ --a_ aaaaaa", "y . g m"),
    ("c___ b___ --a_ ----", "r . g ."),
    ("A___ aaaa --aa G_g_", "g m . s"),
    ("aaa aaa --h_ a_a_", "w . y ."),
    ("aaaa aaaa aaaaaa aaaaaaaa", "m . . ."),
]
# The last bar: five notes that go up to the leading note of the next part (G major).
LAST_NOTES = ("g,,", "bes,,", "c,", "d,", "fis,")
# The guitar plays the figure of the second eight bars with the bass (low strings, muted).
GUITAR = {"a": "g,,", "b": "bes,,", "c": "c,", "d": "d,", "e": "es,", "f": "f,", "g": "g,",
          "h": "as,,"}  # fmt: skip
# The answers of the saxophone, in the gaps of the bass. Bar 8 has the motto (G, C, D, E).
ANSWERS = [
    None,
    r"r2 r8 d''16( f'' g''8-.) r8",
    None,
    r"r4 r8 g'16( bes' c''8 d'' f''16 g'' bes''8-.)",
    None,
    r"r2 r8 bes''16( g'' f''8-.) r8",
    r"r2 r4 d''8->( f''->)",
    r"r2 g16( c' d' e' g' c'' d'' e'')",
    r"g''2.-> r4",
    None,
    r"r2 r8 f''16( g'' bes''8-.) r8",
    r"r2 r4 d''16( f'' g'' bes'')",
    r"c'''4-> r4 r2",
    r"r2 r8 bes''16( g'' f''8 d''-.)",
    r"g''4-> a''4-> bes''4-> b''4->",
    r"\tuplet 5/4 { g'4-> bes'4-> c''4-> d''4-> fis''4-> }",
]
# The acoustic drums: one bar in each entry. Bars 4, 8, and 12 end with a fill.
KIT = [
    "cy C--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- O--- ----\nbd x--- ---- ---- ---x",
    "hh x-x- x-x- x-x- x-o-\nsn ---- ---- o--- -g--\nbd x--- --x- ---- ----",
    "hh x-x- x-x- x-x- x-x-\nsn ---- ---g o--- ----\nbd x--x ---- ---- --x-",
    "hh x-x- x-x- x-x- ----\nsn ---- ---- o--- o-oo\nbd x--- --x- ---- -x--",
    "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- o--- ----\nbd x--- ---x ---- --xx",
    "hh x-x- x-o- x-x- x-x-\nsn ---- ---- o--g ----\nbd x--- --x- ---- -x--",
    "hh x-x- x-x- x-x- x-x-\nsn ---g ---- o--- --g-\nbd x-x- ---- ---x ----",
    "sn ---- ---- o--- ooooooo\ntm ---- hhmm ---- -------\nbd x--- ---- -x-x x------",
    "cy C--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- O--- ----\nbd xx-- ---- ---- ---x",
    "hh x-x- x-x- x-x- x-o-\nsn ---- ---- o--- -g-g\nbd x-xx --xx ---- ----",
    "hh x-x- x-x- x-x- x-x-\nsn ---- --g- o--- ----\nbd x--x --xx --x- --xx",
    "hh x-x- x-x- x-x- ----\nsn ---- ---- o--- oo-o\ntm ---- ---- ---- --f-\nbd x-xx --x- ---- ----",
    "cy c--- ---- ---- ----\nhh --x- x-x- x-x- x-x-\nsn ---- ---- O--- ----\nbd xxxx ---- -x-x --xx",
    "hh x-x- x-o- x-x- x-x-\nsn ---g ---- o--g ----\nbd x-xx --xx ---- -xxx",
    "cy c--- c--- c--- c---\nsn o--- o--- o-o- oooo\nbd xxxx xxxx xxxx xxxx",
]
# The drum machine: the hats, and the strokes of the snare sounds (s = the heavy snare,
# r = the short snare of a roll). The kick of the machine plays with the kick of the kit.
HATS = [
    "--x- x-x- --x- x-xx", "xxx- x-x- --x- x-x-", "--x- x-xx --x- xxxxxx", "x-x- x-x- --x- ----",
    "--x- x-x- --x- x-xx", "x-x- xxx --x- x-x-", "--x- x-xx --x- xxxxxx", "x-x- x-x- ---- ----",
    "--xx xxxx --xx xxxx", "xxxx xxox --xx xxxxxx", "--xx xxxx --xx xxox", "xxxx xxxx --xx ----",
    "--xx xxxx --xx xxxx", "xxxx xxox --xx xxxxxx", "xxxx xxxx xxxx xxxx",
]  # fmt: skip
SNARES = {8: "---- ---- s--- rrrr", 12: "---- ---- s--- r-rr", 15: "s--- s--- r-r- rrrr"}
# The long sounds of the machine: the bar, and the notes of one more voice.
# es,, = sub drop; ges,, = impact; as,, = cymbal that plays backwards; e,, = noise that rises.
LONG = {
    1: r"<es,, ges,,>2\ff r2",
    4: r"r2 as,,2\f",
    8: r"r2 <e,, as,,>2\f",
    9: r"<es,, ges,,>2\ff r2",
    12: r"r2 as,,2\f",
    15: r"e,,1\f",
    16: r"as,,1\ff",
}
# The chords of the horns: the bar, the chord, and the rhythm of the strokes.
STABS = {
    1: ("Gm11", "A___ ---- ---- ----"),
    3: ("Gm11", "---- --A_ ---- ----"),
    5: ("Gm11", "A___ ---- ---- ----"),
    7: ("Gm11", "---- --A_ ---- ----"),
    9: ("Gm11", "A___ ---- ---- ----"),
    10: ("Gm11", "---- --A_ ---- --A_"),
    11: ("Gm11", "A___ ---- ---- ----"),
    12: ("Abmaj7#11", "---- --A_ ---- ----"),
    13: ("Gm11", "A___ ---- --A_ ----"),
    14: ("Abmaj7#11", "---- --A_ ---- --A_"),
    15: ("Gm11", "A___ A___ A___ A___"),
}
# The last bar of each horn and each string group: five notes with the bass.
LAST_HORNS = {"bsax": "g, bes, c d fis", "tbn": "d f g a c'", "asax": "bes d' es' fis' a'",
              "tpt": "g' bes' c'' d'' fis''"}  # fmt: skip
# The strings rise in the second eight bars: two bars on each note, then the last bar.
RISE = ["g''", "g''", "as''", "as''", "bes''", "bes''"]
FIRE = 359.08  # the place of the word "fire" in the recording of Mercury 3, in seconds


def five(notes: str | tuple[str, ...], marks: str = "->") -> str:
    """Return a bar with five equal notes in the time of four beats."""
    names = notes.split() if isinstance(notes, str) else notes
    return r"\tuplet 5/4 { " + " ".join(f"{name}4{marks}" for name in names) + " }"


def bass_bar(pattern: str, sounds: str) -> str:
    """Return one bar of the bass. `sounds` has one letter for each beat (see `SOUND`).

    Beats with the same sound are one phrase: a note can go on from one beat
    to the next beat of the phrase.
    """
    groups, letters = pattern.split(), sounds.split()
    if len(groups) != len(BEATS) or len(letters) != len(BEATS):
        raise ValueError(f"a bar of the bass needs four beats: {pattern!r}, {sounds!r}")
    runs: list[tuple[str, list[str]]] = []
    for group, letter in zip(groups, letters, strict=True):
        if runs and letter in (".", runs[-1][0]):
            runs[-1][1].append(group)
        else:
            runs.append((letter, [group]))
    texts = []
    for letter, part in runs:
        text = patterns.pitched(" ".join(part), (2,) * len(part), NOTES)
        texts.append(text if letter == "." else f'\\switch "{SOUND[letter]}" {text}')
    return " ".join(texts)


def machine_bar(number: int) -> str:
    """Return bar `number` (1 to 16) of the drum machine."""
    if number == 16:
        text = drums.steps("ms sssss\nmk hhhhh", BAR)
    else:
        kick = next(row for row in KIT[number - 1].splitlines() if row.startswith("bd"))
        rows = [
            "mk" + kick[2:].replace("x", "h"),
            "ms " + SNARES.get(number, "---- ---- s--- ----"),
            "mh " + HATS[number - 1],
        ]
        text = drums.steps("\n".join(rows), BEATS)
    if number in LONG:
        text = r"<< { " + text + r" } \\ { " + LONG[number] + " } >>"
    return text


def write(work: Work) -> None:
    structure = work.structure
    cues: list[Cue] = work.extras.setdefault("cues", [])  # type: ignore[assignment]
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    s = Bars(work, 16, COMMON)
    structure.mark(s.bar(1), "R")
    structure.tempo(s.bar(1), 1, m.FLASH, "Half time, heavy")

    # ------------------------------------------------- the bass synthesizer
    bass = [bass_bar(pattern, sounds) for pattern, sounds in RIFF]
    bass[8] = tools.first(bass[8], r"\fff", note=True)
    bass.append(r'\switch "bass growl" ' + five(LAST_NOTES))
    s.set("sbass", bass, r"\ff")

    # ------------------------------------------------- drums and drum machine
    kit = [drums.steps(rows, BEATS) for rows in KIT]
    kit.append(drums.steps("cy CCCCC\nsn OOOOO\nbd xxxxx", BAR))
    s.set("drums", kit, r"\ff")
    s.set("eperc", [machine_bar(number) for number in range(1, 17)], r"\ff")

    # ------------------------------------------------- saxophone and guitar
    s.set("tsax", ANSWERS, r"\ff\growl")
    # The guitar: one chord at the drop, the answers with the saxophone, then the figure
    # of the bass on the low strings, and the last bar in chords of fifths.
    guitar: list[str | None] = [r"<g,, d, g,>1->\highgain\pmoff", *ANSWERS[1:8]]
    guitar[1] = tools.first(ANSWERS[1], r"\leadtone", note=True)
    chugs = [patterns.pitched(pattern, BEATS, GUITAR) for pattern, _sounds in RIFF[8:14]]
    chugs.append(patterns.pitched("aaaa aaaa aaaa aaaa", BEATS, GUITAR))
    chugs[0] = tools.first(chugs[0], r"\highgain\pm", note=True)
    guitar += chugs
    guitar.append(
        r"\tuplet 5/4 { <g,, d, g,>4->\pmoff <bes,, f, bes,>4-> <c, g, c>4-> <d, a, d>4-> "
        r"<fis,, d, a,>4-> }"
    )
    s.set("gtr", guitar, r"\ff")
    s.set("bass", [None] * 15 + [five(LAST_NOTES)], r"\ff")

    # ------------------------------------------------- horns, strings, synthesizers
    symbols = [STABS[number][0] if number in STABS else None for number in range(1, 16)]
    rhythms = [STABS[number][1] if number in STABS else "---- ---- ---- ----"
               for number in range(1, 16)]  # fmt: skip
    horns = m.layers(symbols, rhythms, m.HORNS, "horns", BEATS)
    for player, bars in horns.items():
        s.set(player, [*bars, five(LAST_HORNS[player])], r"\ff")
    for player, shift in (("vn1", 0), ("vn2", -1), ("va", -2), ("vc", -2)):
        line = [f"{name}1 ~" if number % 2 == 0 else f"{name}1" for number, name in enumerate(RISE)]
        line += [r"c'''2 d'''2", five("g'' bes'' c''' d''' fis'''")]
        moved = [tools.octave(bar, shift) for bar in line]
        s.set(player, [None] * 8 + moved, r"\mf\<")
    # Chords of the synthesizer: one long chord at the two drops, then short chords
    # between the beats (the manner of dub).
    chords_a = m.pad_bars(["Gm11" if number in (0, 4) else None for number in range(8)],
                          "A___ ____ ---- ----", BEATS, low=58, high=82)  # fmt: skip
    names = ["Gm9", "Gm9", "Gm9", "Abmaj7#11", "Gm9", "Abmaj7#11", "Gm9"]
    chords_b = m.pad_bars(names, "--a- --a- --a- --a-", BEATS, low=58, high=82)
    last = r"<g' bes' d''>4-> <bes' d'' f''>4-> <c'' es'' g''>4-> <d'' fis'' a''>4-> <d'' fis'' c'''>4->"
    s.set("pad.rh", [*chords_a, *chords_b, r"\tuplet 5/4 { " + last + " }"], r"\ff",
          r'\switch "supersaw"')  # fmt: skip
    table = {"a": "g''", "b": "bes''", "c": "d'''", "d": "f'''"}
    shapes = ["---- abcd ---- dcba", "abcd ---- dcba ----"]
    arps = [patterns.pitched(shapes[number % 2], BEATS, table) for number in range(6)]
    arps.append(patterns.pitched("abcd abcd abcd abcd", BEATS, table))
    chip: list[str | None] = [None] * 16
    chip[3] = patterns.pitched("---- ---- ---- dcba", BEATS, table)
    chip[7] = tools.octave(ANSWERS[7], 2)  # the motto, with the saxophone
    chip[8:15] = arps
    chip[15] = five("g''' bes''' c'''' d'''' fis''''", "")
    s.set("chip", chip, r"\mf", r'\switch "chip pulse 25"')

    # ------------------------------------------------- the word "fire" in pieces
    def word(bar: int, beat: float, seconds: float = 0.3, **options) -> Cue:
        return Cue("mercury3-548", s.bar(bar), beat, offset=FIRE, seconds=seconds, radio=True,
                   fade=0.004, text="Fire.", **options)  # fmt: skip

    cues += [
        word(4, 4.5, gain_db=-7.0, pan=0.4),
        # Bar 8: the start of the word three times, then the full word (a stutter).
        word(8, 3.0, 0.09, gain_db=-6.0, pan=-0.5),
        word(8, 3.25, 0.09, gain_db=-6.0, pan=0.5),
        word(8, 3.5, 0.09, gain_db=-5.0, pan=-0.5),
        word(8, 3.75, gain_db=-4.0),
        word(12, 3.5, gain_db=-6.0, pan=-0.4, reverse=True),
        word(14, 4.5, gain_db=-7.0, pan=0.4, speed=0.8),
    ]
    # The last beat of bar 8 repeats in very short pieces that go up one octave.
    edits.append(Edit("stutter", s.bar(8), 4, length=1.0, stems=("drums", "eperc"), slice=0.125,
                      pitch=12.0))  # fmt: skip
    s.close()
    structure.double_bar(s.section.last_bar)
