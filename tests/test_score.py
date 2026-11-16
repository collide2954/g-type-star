"""Tests for the drum staves and the staff of the recorded sounds in the score."""

from fractions import Fraction

from gtypestar.notation import drums, lilypond, music
from gtypestar.notation.structure import Bar


def parse(text: str) -> list[music.Element]:
    return music.parse(text).children


def total(elements: list[music.Element]) -> Fraction:
    return sum((music.length(element) for element in elements), Fraction(0))


def test_drum_voices_continue_through_all_bars():
    text = (
        "<< { g,4\\mp\\< g,4 g,4 g,4 } \\\\ { c,4 r4 c,4 r4 } >> | "  # hands and feet
        "c,4 r4 c,4 r4 | "  # the feet only
        "d,4\\f d,4 d,4 d,4 | "  # the hands only
        "R1 |"
    )
    voices, marks = lilypond.drum_voices(parse(text), feet={35, 36, 44})
    hands, feet, long_sounds = voices
    assert total(hands) == total(feet) == total(long_sounds) == 16
    # The bar of the feet is in the voice of the feet; the hands have a spacer rest there.
    spacers = [e for e in hands if isinstance(e, music.Rest) and e.kind == "s"]
    assert sum(spacer.duration for spacer in spacers) == 4
    # The dynamic marks left the notes: they have their own voice.
    assert [position for position, _posts in marks] == [0, 8]
    for element in hands:
        if isinstance(element, music.Note):
            assert all(post.kind not in ("dynamic", "hairpin") for post in element.posts)


def test_drum_voices_three_voices():
    text = "<< { << { g,4 g,4 g,4 g,4 } \\\\ { c,4 r4 r4 r4 } >> } \\\\ { es,,1 } >> |"
    voices, _marks = lilypond.drum_voices(parse(text), feet={36, 27})
    assert [bool(lilypond._pitches(voice)) for voice in voices] == [True, True, True]


def test_marks_voice_ends_an_open_crescendo():
    posts = [music.Post("dynamic", "\\mp", "mp"), music.Post("hairpin", "\\<", "<")]
    text = lilypond._marks_voice([(Fraction(0), posts)], Fraction(8))
    assert text.endswith("\\!")
    assert "\\mp\\<" in text


def test_drum_note_names():
    emitter = lilypond._Emitter(None, for_part=False)  # type: ignore[arg-type]
    emitter.drums = {drum.midi: drum for drum in drums.KIT}
    snare_and_hat = parse("<d, ges,>8->")[0]
    assert emitter.drum_note(snare_and_hat) == "<sn hh>8->"
    ghost = parse("e,16")[0]
    assert emitter.drum_note(ghost) == "\\parenthesize sn16"


def test_values_show_the_pulse():
    # Five sixteenth notes from the second sixteenth note of a pulse of six.
    assert lilypond._values(1, 5, 6) == [1, 2, 2]
    assert lilypond._values(0, 6, 6) == [6]
    assert lilypond._values(0, 3, 6) == [2, 1]


def test_pulse_sizes():
    assert lilypond._pulse_sizes(Bar(1, Fraction(0), 14, 8, (3, 3, 2, 3, 3))) == [6, 6, 4, 6, 6]
    assert lilypond._pulse_sizes(Bar(1, Fraction(0), 4, 4)) == [4, 4, 4, 4]
    assert lilypond._pulse_sizes(Bar(1, Fraction(0), 6, 8)) == [6, 6]
