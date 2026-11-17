"""Tests for the rules and the tools of the third version (see design/plan.md)."""

from fractions import Fraction

import numpy as np
import pytest

from gtypestar.audio import band, banks, dsp, glitch, perc, tape
from gtypestar.compose import check, patterns, tools
from gtypestar.perform.events import PerfNote
from gtypestar.perform.feel import Event
from gtypestar.work import material as m

RATE = 48000


def test_a_line_stays_inside_a_range_note_by_note():
    # F-sharp 5 and G5 are above F5 (77): they go one octave lower; E5 stays.
    assert tools.within("e''8 fis'' g''", 44, 77) == "e''8 fis' g'"


def test_a_phrase_moves_as_one_piece_if_its_highest_note_is_too_high():
    assert tools.fit("c''4 g''4", 77) == "c'4 g'4"
    assert tools.fit("c''4 e''4", 77) == "c''4 e''4"
    # The second bar of a phrase moves with the first bar.
    assert tools.fit("c''4", 77, more=("c''4", "g''4")) == "c'4"


def test_a_line_moves_bar_by_bar_with_the_smallest_leaps_at_the_bar_lines():
    # Bar 2 has a G5, above the range: the whole bar goes one octave lower, and its
    # shape stays. Bar 1 has a low A-flat: it cannot go lower, and stays. Bar 3 has two
    # possible octaves: it takes the octave next to the end of bar 2.
    line = ["as,8 d'' e'' f''", "g''8 f'' e'' d''", "c''8 b' a' g'"]
    assert tools.fit_bars(line, 44, 77) == ["as,8 d'' e'' f''", "g'8 f' e' d'", "c'8 b a g"]
    # A line that is in the range stays as it is.
    assert tools.fit_bars(line[2:], 44, 77) == line[2:]
    # With no low note in bar 1, the three bars go down together: no leap at a bar line.
    line[0] = "c''8 d'' e'' f''"
    assert tools.fit_bars(line, 44, 77) == ["c'8 d' e' f'", "g'8 f' e' d'", "c'8 b a g"]


def test_a_bar_of_the_last_line_has_one_slur_on_each_pulse():
    from gtypestar.work import agb

    bar = agb.slurred(" ".join(["c'16"] + ["d'"] * 27))
    words = bar.split()
    starts = [index for index, word in enumerate(words) if word.endswith("(")]
    ends = [index for index, word in enumerate(words) if word.endswith(")")]
    assert starts == [0, 6, 12, 16, 22] and ends == [5, 11, 15, 21, 27]


def test_the_work_has_no_fast_line_without_slurs_and_no_chord_too_wide_for_a_hand():
    from gtypestar.work import build

    work = build()
    problems = [str(problem) for problem in check.check(work)]
    assert problems == []
    # The checks find the faults: a fast line with no slur (the first bars of the work
    # have 70 quarter notes in a minute: 16 notes in a quarter note are 18 in a second),
    # and a chord of two octaves in one hand.

    def notes(legato: bool) -> list[PerfNote]:
        return [
            PerfNote("tsax", "tenor saxophone", Fraction(number, 16), Fraction(1, 16), 60, 0.7,
                     0.7, legato=legato and number > 0)
            for number in range(40)
        ]  # fmt: skip

    assert len(check._tongue_problems(work, "tsax", notes(legato=False))) == 1
    assert check._tongue_problems(work, "tsax", notes(legato=True)) == []
    wide = [PerfNote("keys.rh", "electric piano", Fraction(0), Fraction(1), midi, 0.7, 0.7)
            for midi in (60, 84)]  # fmt: skip
    assert len(check._hand_problems(work, "keys.rh", wide)) == 1
    assert check._hand_problems(work, "keys.rh", wide[:1]) == []


def test_the_kick_drum_has_the_low_notes_of_the_bass():
    figure = "a__x-b ---c-e b_a_ a__x-c ---e_c"
    bars = m.drum_bars(m.MAIN, 1, "test", amount=0.0, crash=(), kicks=[figure])
    kick = next(row for row in _rows(bars[0], m.MAIN) if row[0] == "bd")[1]
    # The first, third and fourth pulse come from the bass figure (letters a and b).
    assert kick[0] == "x----x" and kick[2] == "x-x-" and kick[3] == "x-----"
    # The second and the fifth pulse stay as in the groove.
    assert kick[1] == m.MAIN.rows["bd"][1] and kick[4] == m.MAIN.rows["bd"][4]


def _rows(text: str, groove) -> list[tuple[str, list[str]]]:
    """Make the same bar again as rows: the function under test returns music text."""
    source = m.random("drums", "test")
    bar = groove.vary(source, 0.0)
    figure = "a__x-b ---c-e b_a_ a__x-c ---e_c"
    for pulse, group in enumerate(figure.split()):
        if pulse in m.KICK_PULSES:
            bar.rows["bd"][pulse] = "".join("x" if char in "ab" else "-" for char in group)
    assert bar.text() == text
    return list(bar.rows.items())


def test_a_division_in_five_seven_or_eleven_is_found():
    assert check._division(Fraction(1, 4)) == 0
    assert check._division(Fraction(1, 6)) == 0
    assert check._division(Fraction(3, 20)) == 5
    assert check._division(Fraction(1, 7)) == 7
    assert check._division(Fraction(4, 11)) == 11


def test_noise_rings_on_the_given_notes():
    noise = np.random.default_rng(1).normal(0.0, 0.1, (2 * RATE, 2))
    rung = tape.ring(noise, (57,), mix=1.0)  # A3 = 220 Hz
    spectrum = np.abs(np.fft.rfft(rung[:, 0]))
    frequencies = np.fft.rfftfreq(len(rung), 1 / RATE)
    peak = float(frequencies[np.argmax(spectrum)])
    assert min(abs(peak - value) for value in (220.0, 440.0, 880.0, 1760.0)) < 6.0
    # The level stays.
    assert abs(float(np.std(rung)) / float(np.std(noise)) - 1.0) < 0.05


def test_a_held_moment_has_the_length_that_is_asked_for_and_fades():
    time = np.arange(RATE // 2) / RATE
    tone = 0.2 * np.sin(2 * np.pi * 330.0 * time)
    moment = np.stack([tone, tone], axis=1)
    held = glitch.freeze(moment, 3 * RATE, hold=0.5)
    assert held.shape == (3 * RATE, 2)
    middle = float(np.sqrt(np.mean(held[RATE : RATE + 4800] ** 2)))
    end = float(np.sqrt(np.mean(held[-2400:] ** 2)))
    assert middle > 0.05 and end < 0.1 * middle


@pytest.mark.skipif(not perc.available(), reason="the percussion samples are not on this computer")
def test_the_shaker_takes_two_kinds_of_stroke_in_turn():
    def stroke(start: float) -> Event:
        note = PerfNote("perc", "hand percussion", Fraction(0), Fraction(1), 82, 0.7, 0.7)
        return Event(note, start, 0.1, 0.7, 0.7)

    sound = perc.render([stroke(0.1), stroke(0.27), stroke(0.44), stroke(0.61)], 1.0)
    pieces = [sound[int(start * RATE) : int((start + 0.12) * RATE)] for start in (0.1, 0.27)]
    assert all(float(np.max(np.abs(piece))) > 0.01 for piece in pieces)
    # The move away and the move back are two different recordings.
    same = float(np.corrcoef(pieces[0][:, 0], pieces[1][:, 0])[0, 1])
    assert abs(same) < 0.9


def test_the_fader_after_the_amplifier_follows_the_written_loudness():
    def chord(start: float, seconds: float, level: float, level_end: float) -> Event:
        note = PerfNote("gtr", "guitar", Fraction(0), Fraction(1), 40, level, level_end)
        return Event(note, start, seconds, level, level_end)

    # A fortissimo stroke, then a chord of four seconds from mezzo forte to pianissimo.
    events = [chord(0.0, 0.5, 0.83, 0.83), chord(1.0, 4.0, 0.59, 0.27)]
    gain = 20.0 * np.log10(band.fader(events, 6 * RATE, 24.0))
    assert abs(gain[RATE // 4]) < 0.1  # full level at fortissimo
    assert abs(gain[int(1.2 * RATE)] - 24.0 * (0.59 - 0.83)) < 1.0
    assert abs(gain[int(4.9 * RATE)] - 24.0 * (0.27 - 0.83)) < 1.0
    assert abs(gain[-1] - gain[int(4.9 * RATE)]) < 0.5  # the fader stays after the chord
    # A tone with no range of the fader (the lead tone) has no change.
    assert np.all(band.fader(events, RATE, 0.0) == 1.0)


def test_the_band_goes_down_under_a_voice_and_comes_back():
    from gtypestar.work import build

    work = build()
    structure = work.structure
    cue = next(cue for cue in work.extras["cues"] if "wild" in cue.text)
    start = structure.seconds(structure.bar(cue.bar).start + Fraction(cue.beat) - 1)
    # A part of the work that starts 5 seconds before the voice.
    offset = 5.0 - start
    curve = tape.ducking(work, offset, 12 * RATE)
    assert curve is not None
    middle = 20.0 * np.log10(curve[int((5.0 + cue.seconds / 2) * RATE)])
    assert abs(middle + cue.duck_db) < 0.01
    assert curve[int(4.5 * RATE)] == 1.0 and curve[int(7.5 * RATE)] == 1.0
    # Each voice with words inside the loud parts of the work brings the band down.
    loud = [cue for cue in work.extras["cues"] if cue.text and cue.gain_db > -11.0]
    assert all(cue.duck_db > 0 or "Fire three" in cue.text for cue in loud), [
        cue.text for cue in loud if not cue.duck_db
    ]


def test_a_held_note_is_one_note_value_where_the_metre_allows_it():
    table = {"a": "g"}
    clave, beats = (3, 3, 2, 3, 3), (2, 2, 2, 2)
    # A full bar of 14 eighth notes: 6 + 2 + 6, not five values with ties.
    assert patterns.pitched("a_____ ______ ____ ______ ______", clave, table) == "g2.~ g4~ g2."
    # A full bar of four beats is a whole note; three beats are a half note and a quarter.
    assert patterns.pitched("a___ ____ ____ ____", beats, table) == "g1"
    assert patterns.pitched("a___ ____ ____ ----", beats, table) == "g2~ g4 r4"
    # A note from the second beat does not hide the middle of the bar.
    assert patterns.pitched("---- a___ ____ ____", beats, table) == "r4 g4~ g2"
    # Two notes are two notes.
    assert patterns.pitched("a_____ a_____ ---- ------ ------", clave, table) == (
        "g4. g4. r4 r4. r4."
    )


def test_the_key_of_a_muse_stem_is_the_music_as_it_sounds():
    from gtypestar.audio import musestems
    from gtypestar.work import build

    work = build()
    first = musestems.played_key(work, None, {"tsax"})
    assert first == musestems.played_key(work, None, {"tsax"})
    assert first != musestems.played_key(work, None, {"tpt"})
    assert first != musestems.played_key(work, (39, 54), {"tsax"})


def test_a_weak_note_of_a_solo_stem_comes_up_to_the_level_of_the_others():
    from gtypestar.audio import musestems
    from gtypestar.perform.events import perform
    from gtypestar.work import build

    work = build()
    structure = work.structure
    bars = (39, 70)
    origin = structure.seconds(structure.bar(bars[0]).start)
    end = structure.seconds(structure.bar(bars[1]).end)
    audio = np.zeros((int((end - origin) * RATE) + RATE, 2), dtype=np.float32)
    notes = [note for note in perform(work, "tsax")
             if not note.grace and bars[0] <= structure.bar_at(note.start).number <= bars[1]
             and note.duration >= 1]  # fmt: skip
    weak, normal = notes[10], notes[20]

    def place(note) -> tuple[int, int]:
        first = int((structure.seconds(note.start) - origin) * RATE)
        last = int((structure.seconds(note.start + note.duration) - origin) * RATE)
        return first, last

    # A stem in which each note has the level of its written loudness; one note is
    # 12 dB too soft.
    for note in notes:
        first, last = place(note)
        level_db = -40.0 + 20.0 * note.level - (12.0 if note is weak else 0.0)
        time = np.arange(last - first) / RATE
        audio[first:last] = (10.0 ** (level_db / 20.0) * np.sin(2 * np.pi * 440.0 * time))[:, None]
    fixed = musestems.even(work, bars, "tsax", audio)

    def gain(note) -> float:
        first, last = place(note)
        middle = slice(first + (last - first) // 4, last - (last - first) // 4)
        before = float(np.sqrt(np.mean(audio[middle] ** 2)))
        return 20.0 * np.log10(float(np.sqrt(np.mean(fixed[middle] ** 2))) / before)

    # The weak note comes up to 3 dB under its level; a normal note does not change.
    assert abs(gain(weak) - 9.0) < 1.0
    assert abs(gain(normal)) < 0.01


def test_a_video_page_with_given_starts_has_line_breaks_at_these_bars_only():
    from gtypestar.notation import lilypond
    from gtypestar.work import build

    work = build()
    first, last = lilypond.chunk_bars(work, 0)
    assert last - first >= 10
    given = lilypond.video_file(work, 0, 10.0, mobile=True, starts=[first + 4, first + 9])
    assert "line-break-permission = ##f" in given
    assert given.count("\\break") == 2
    # With no given starts, LilyPond can make one more break on a full screen.
    assert "line-break-permission" not in lilypond.video_file(work, 0, 10.0, mobile=True)
    # The name of a clef with an octave is in quotes (with no quotes, LilyPond reads the
    # octave as a number under the first note).
    index = next(number for number in range(lilypond.chunk_count(work))
                 if "treble_8" in lilypond.video_file(work, number, 10.0))  # fmt: skip
    page = lilypond.video_file(work, index, 10.0)
    assert '\\clef "treble_8"' in page and "\\clef treble_8" not in page


BASS_FOLDER = banks.SAMPLES_DIR / "basses" / "Samples" / "darkblack"


@pytest.mark.skipif(not BASS_FOLDER.exists(), reason="the bass library is not on this computer")
def test_a_note_of_the_bass_guitar_sounds_at_its_written_time():
    # A recording of the bass starts 26 ms before its note sounds: the finger is on the
    # string. To version 3.5 each note was late by this time.
    def event(start: float, midi: int, legato: bool = False) -> Event:
        note = PerfNote("bass", "bass guitar", Fraction(0), Fraction(1), midi, 0.8, 0.8,
                        legato=legato)  # fmt: skip
        return Event(note, start, 0.4, 0.8, 0.8)

    events = [event(0.5 + 0.6 * number, 28 + 5 * number) for number in range(5)]
    events.append(event(4.0, 40, legato=True))
    dry = band._bass_samples(banks.BassBank(BASS_FOLDER), events, 6 * RATE)
    for item in events:
        first = int((item.start - 0.06) * RATE)
        part = dry[first : first + int(0.2 * RATE)].astype(np.float32)
        late = dsp.onset(part) - 0.06
        # A note under a slur starts inside its recording, with a short rise.
        assert late == pytest.approx(0.0, abs=0.012 if item.note.legato else 0.002)
    # The finger is on the string before the first note.
    assert float(np.max(np.abs(dry[int(0.48 * RATE) : int(0.5 * RATE)]))) > 0.0
