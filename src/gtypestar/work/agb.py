"""Part 7: the last burning. Helium burns in the core, then in a shell with pulses.

The main metre and the main tempo come back. The drums play in the manner of
drum and bass. All lead players have the theme, then the longest line of the
work (eight bars of sixteenth notes). Three "thermal pulses" follow: the key
goes up by major thirds (G, B, E-flat), and in each pulse the division of the
bar changes from sixteenth notes to five notes in a pulse. The part ends with
strokes on each pulse and one chord of all players.

Style profile: "Groove", with the largest density of the work.
"""

from __future__ import annotations

from ..audio.glitch import Edit
from ..compose import chords, patterns, tools
from ..notation import drums
from ..notation.work import Work
from . import mainseq
from . import material as m
from .material import Bars

# The groove in the manner of drum and bass: ride cymbal, many ghost notes, a busy kick.
BREAK = m.Groove(
    """
    rd  x-x-x- x-x-x- x-x- x-x-x- x-x-x-
    sn  ---g-g o--g-g -g-g --g-g- o-gg-g
    bd  x--x-- ---x-- x--x x--x-x ---x--
    """,
    m.CLAVE,
)
# Two new bars for the end of the last line: fourths that go up, then triads that go up.
LINE_END = [
    r"g16 c' f' e' a d' g' fis' b e' a' g' c' fis' b' a' d' g' c'' b' e' a' d'' c'' fis' b' e'' d''",
    r"g'16 b' d'' g'' fis'' d'' b' g' a' c'' e'' a'' g'' e'' c'' a' b' d'' fis'' b'' a'' fis'' d'' b' c'' e'' g'' g'')",
]
CHORDS = ["a_____ ---a__ ---- a__-a_ ______", "---a__ ------ a___ ---a__ ---a__",
          "a__a__ ---a__ a___ ------ a_____", "---a__ a__--- -a__ a__a__ ------"]  # fmt: skip


def line_4() -> list[str]:
    """Return the fourth line for all lead players: eight bars."""
    bars = [*m.LINE_1, *m.LINE_2, *LINE_END]
    return [bar.replace("(", "").replace(")", "") for bar in bars]


def write(work: Work) -> None:
    structure = work.structure
    edits: list[Edit] = work.extras.setdefault("edits", [])  # type: ignore[assignment]

    # ------------------------------------------------- the theme, by all lead players
    s = Bars(work, 16)
    structure.mark(s.bar(1), "S")
    structure.tempo(s.bar(1), 1, m.FAST, "Bright, with all force")
    symbols = m.LOOP_A * 4
    theme = m.THEME_HIGH + m.THEME_SECOND
    s.set("tsax", theme, r"\ff\normaltone")
    s.set("tpt", theme, r"\ff")
    second = [tools.tr(bar, -3) if n % 4 != 1 else tools.tr(bar, -4)
              for n, bar in enumerate(theme)]  # fmt: skip
    s.set("asax", tools.true_ties(second), r"\f")
    s.set("vn1", [tools.octave(bar, 1) for bar in theme], r"\f")
    low_horns = m.layers(symbols, ["a_____ ______ ____ ______ ______"], ("bsax", "tbn"), "horns2")
    for player, bars in low_horns.items():
        s.set(player, bars, r"\f")
    low_strings = m.layers(symbols, ["a_____ ______ ____ ______ ______"], ("vc", "va", "vn2"),
                           "strings3")  # fmt: skip
    for player, bars in low_strings.items():
        s.set(player, bars, r"\f")
    s.set(
        "drums",
        m.drum_bars(BREAK, 16, "last theme", amount=1.3, crash=(1, 5, 9, 13),
                    fills={4: "snare 1", 8: "linear 2", 12: "toms 1", 16: "kicks 2"}),
        r"\ff",
    )  # fmt: skip
    s.set("bass", mainseq._bass(symbols, "last theme"), r"\ff")
    s.set("keys.rh", mainseq._keys(symbols, "last theme"), r"\f")
    guitar = []
    for number, symbol in enumerate(symbols):
        notes = chords.voice(symbol, 4, low=50, high=74, rootless=False)
        guitar.append(
            patterns.pitched(CHORDS[number % 4], m.CLAVE, {"a": chords.names(notes, symbol)})
        )
    s.set("gtr", guitar, r"\ff\crunch\pmoff")
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
    s.set("eperc", [machine] * 16, r"\mf")
    s.close()

    # ------------------------------------------------- the fourth line: eight bars
    s = Bars(work, 8)
    structure.mark(s.bar(1), "T")
    line = line_4()
    # The saxophone player has one bar of rest to breathe.
    s.set("tsax", [*line[:3], None, *line[4:]], r"\ff")
    s.set("gtr", line, r"\ff\leadtone")
    s.set("lead", [tools.octave(bar, 1) for bar in line], r"\ff", r'\switch "lead moog"')
    s.set("chip", [tools.octave(bar, 2) for bar in line], r"\f")
    s.set("bass", [tools.octave(bar, -2) for bar in line], r"\ff")
    s.set("keys.rh", line, r"\f")
    accents = m.Groove(
        """
        cy  c----- k----- k--- k----- k-----
        sn  ------ o--g-- ---g ------ o--g-g
        bd  x--x-x ---x-- x-x- x--x-- ---x-x
        """,
        m.CLAVE,
    )
    s.set("drums", m.drum_bars(accents, 8, "line 4", amount=1.4, crash=(1, 3, 5, 7),
                               fills={4: "linear 2", 8: "toms 2"}), r"\ff")  # fmt: skip
    hits = m.layers(m.LOOP_A * 2, ["A_____ ------ ---- ------ ------", "------ ------ ---- A_____ ------"],
                    m.HORNS, "horns")  # fmt: skip
    for player, bars in hits.items():
        s.set(player, bars, r"\ff")
    s.close()

    # ------------------------------------------------- three thermal pulses
    s = Bars(work, 12)
    structure.mark(s.bar(1), "U")
    keys = ["Gmaj9", "Bmaj9", "Ebmaj9"]
    mottos = [r"g'4.(\f\< c''4. ~ c''4 d''4. e''4. ~", r"e''1..\ff)", None, None]
    sax, trumpet, drum_bars, bass_bars, key_bars, guitar_bars, pad_bars, sub_bars = (
        [], [], [], [], [], [], [], []
    )  # fmt: skip
    for number, name in enumerate(keys):
        step = [0, 4, 8][number]
        sax += [None if bar is None else tools.tr(bar, step if step < 8 else step - 12)
                for bar in mottos]  # fmt: skip
        trumpet += [None if bar is None else tools.tr(bar, step if step < 8 else step - 12)
                    for bar in mottos]  # fmt: skip
        drum_bars += m.drum_bars(m.MAIN_OPEN, 2, f"pulse {number}", amount=1.2, crash=(1,))
        drum_bars += m.drum_bars(m.MORPH, 2, f"pulse five {number}", amount=1.0, crash=(1,),
                                 fills={2: "five 2"})  # fmt: skip
        symbols = [name] * 4
        bass_bars += mainseq._bass(symbols[:2], f"pulse {number}")
        bass_bars += mainseq._bass(symbols[2:], f"pulse five {number}", mainseq.BASS_FIVE)
        key_bars += mainseq._keys(symbols[:2], f"pulse {number}")
        key_bars += mainseq._keys(symbols[2:], f"pulse five {number}", patterns_=mainseq.COMPS_FIVE)
        # The lowest string of the guitar is F-sharp: the riff on E-flat is one octave higher.
        shift = step if step < 8 else step
        root = {"a": tools.tr("g,,", shift) + r" \pm", "b": tools.tr("g,", shift)}
        guitar_bars += [patterns.pitched(p, m.CLAVE, root) for p in
                        ("aaaaaa a-aa-a aaaa aaaaaa a-ab--", "aaaaaa aa-aab aaaa a-aaaa aab---",
                         "aaaaa a-a-a aaa aaaaa a-ab-", "aaaaa aa-aa a-a aaaaa aaaab")]  # fmt: skip
        pad_bars += m.pad_bars(symbols, low=60, high=84)
        sub_bars += m.roots(symbols, "a_____ ______ a___ ______ ______")
    s.set("tsax", sax)
    s.set("tpt", trumpet)
    s.set("drums", drum_bars, r"\ff")
    s.set("bass", bass_bars, r"\ff")
    s.set("keys.rh", key_bars, r"\f")
    s.set("gtr", guitar_bars, r"\ff\highgain")
    s.set("pad.rh", pad_bars, r"\f\<")
    s.set("sbass", sub_bars, r"\f")
    wide = m.layers([k for k in keys for _ in range(4)], ["a_____ ______ ____ ______ ______"],
                    m.STRINGS, "strings")  # fmt: skip
    for player, bars in wide.items():
        s.set(player, tools.first(patterns.join(bars), r"\f\<", note=True))
    s.set(
        "eperc",
        r"R1*14/8*2 | e,,1..\mf\< ~ | e,,1.. | R1*14/8*2 | e,,1..\mf\< ~ | e,,1.. | R1*14/8*2 | e,,1..\f\< ~ | e,,1..\ff |",
    )
    s.close()

    # ------------------------------------------------- the last strokes and the last chord
    s = Bars(work, 4)
    structure.mark(s.bar(1), "V")
    strokes = "A_____ A_____ A___ A_____ A_____"
    faster = "A__A__ A__A__ A_A_ A_A_A_ AAAAAA"
    final = "Gmaj13#11"
    rows = [
        "cy C----- C----- C--- C----- C-----\nsn O----- O----- O--- O----- O-----\nbd x----- x----- x--- x----- x-----",
        "cy C----- C----- C--- C----- C-----\nsn O--O-- O--O-- O-O- O-O-O- OOOOOO\nbd x--x-- x--x-- x-x- x-x-x- xxxxxx",
        "cy C----- ------ ---- ------ ------\nsn OOOOOO OOOOOO OOOO OOOOOO OOOOOO\nbd x----- ------ x--- ------ ------",
        "cy C----- ------ ---- ------ ------\nsn O----- ------ ---- ------ ------\nbd x----- ------ ---- ------ ------",
    ]
    s.set("drums", [drums.steps(row, m.CLAVE) for row in rows], r"\ff")
    for kind, players in (("horns", m.HORNS), ("strings", m.STRINGS)):
        parts = m.layers(["D13sus", "D13sus", final, final],
                         [strokes, faster, "a_____ ______ ____ ______ ______", "A_____ ------ ---- ------ ------"],
                         players, kind)  # fmt: skip
        for player, bars in parts.items():
            s.set(player, bars, r"\ff")
    s.set("tsax", [r"a'4.->\ff a'4.-> a'4-> c''4.-> c''4.->", r"d''4.-> d''4.-> e''4-> fis''8-> fis''-> fis''-> fis''-> fis''-> fis''->",
                   r"g''1..->", r"g''4.-> r4. r4 r4. r4."])  # fmt: skip
    for player, low in (("gtr", "<d, a, d>"), ("bass", "d,")):
        end = "<g,, d, g, b,>" if player == "gtr" else "g,,"
        s.set(player, [patterns.pitched(strokes, m.CLAVE, {"a": low}),
                       patterns.pitched(faster, m.CLAVE, {"a": low}),
                       f"{end}1..->", f"{end}4.-> r4. r4 r4. r4."], r"\ff")  # fmt: skip
    chord = chords.names(chords.voice(final, 5, low=55, high=84), final)
    sus = chords.names(chords.voice("D13sus", 4, low=55, high=79), "D13sus")
    for player in ("keys.rh", "pad.rh"):
        s.set(player, [patterns.pitched(strokes, m.CLAVE, {"a": sus}),
                       patterns.pitched(faster, m.CLAVE, {"a": sus}),
                       f"{chord}1..", f"{chord}4.-> r4. r4 r4. r4."], r"\ff")  # fmt: skip
    s.set("sbass", [None, None, r"g,,1..\ff", r"g,,4. r4. r4 r4. r4."])
    s.set(
        "chip",
        [
            None,
            None,
            r"\repeat unfold 7 { g'''16\f b''' d'''' fis'''' }",
            r"g''''4.-> r4. r4 r4. r4.",
        ],
    )
    s.set(
        "eperc",
        r"R1*14/8*2 | << { R1*14/8 } \\ { ges,,1..\ff } >> | << { r4. r4. r4 r4. r4. } \\ { ges,,4.\ff r4. r4 r4. r4. } >> |",
    )
    # After the first pulse of the last bar, the sound stops at once.
    edits.append(Edit("mute", s.bar(4), 2.5, length=5.5, stems=("drums", "gtr", "bass", "keys",
                                                               "pad", "horns", "strings", "tsax",
                                                               "sbass", "chip", "eperc")))  # fmt: skip
    s.close()
    structure.double_bar(s.section.last_bar)
