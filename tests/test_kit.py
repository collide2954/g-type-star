"""Tests for the drum engine: kits in the SFZ format, and the choice of a stroke."""

from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile

from gtypestar.audio import kit, sfzkit
from gtypestar.perform.events import PerfNote
from gtypestar.perform.feel import Event

RATE = 48000


def small_kit(root: Path) -> kit.KitSpec:
    """Write a kit with one drum: two layers of force, two strokes in each, two microphones."""
    (root / "Samples").mkdir(parents=True)
    (root / "Data").mkdir()
    (root / "Multi").mkdir()
    time = np.arange(RATE // 10) / RATE
    for layer, tone in (("soft", 200.0), ("hard", 400.0)):
        for stroke in ("one", "two"):
            near = 0.5 * np.sin(2 * np.pi * tone * time) * np.exp(-30 * time)
            soundfile.write(str(root / "Samples" / f"near_{layer}_{stroke}.flac"), near, RATE)
            far = np.stack([0.25 * near, 0.125 * near], axis=1)
            soundfile.write(str(root / "Samples" / f"far_{layer}_{stroke}.flac"), far, RATE)
    (root / "Data" / "macro.txt").write_text(
        "#define $KEY 36\n#define $LOW 1    #define $SPLIT 64\n#define $ext flac\n"
    )
    (root / "Data" / "strokes.txt").write_text(
        "<region> lovel=$LOW hivel=$SPLIT seq_position=1 sample=$MIC_soft_one.$ext\n"
        "<region> lovel=$LOW hivel=$SPLIT seq_position=2 sample=$MIC_soft_two.$ext\n"
        "<region> lovel=65 hivel=127 seq_position=1 sample=$MIC_hard_one.$ext volume=-6\n"
        "<region> lovel=65 hivel=127 seq_position=2 sample=$MIC_hard_two.$ext volume=-6\n"
        "<region> key=60 sample=*silence\n"
    )
    for name, microphone, trim in (("Near", "near", 0), ("Far", "far", 6)):
        (root / "Multi" / f"{name}.sfz").write_text(
            '// one microphone\n#include "../Data/macro.txt"\n<global> loop_mode=one_shot\n'
            f"<master>\nmaster_volume={trim}\n<group>\nkey=$KEY\n#define $MIC {microphone}\n"
            '#include "../Data/strokes.txt"\n'
        )
    return replace(
        kit.NAKED,
        name="small",
        folder=str(root),
        drums={36: "kick"},
        keys={"kick": 36},
        groups={"kick": {"Near": 0.0}, "room": {"Far L": -1.0, "Far R": 1.0}},
        programs=(("Near", "Multi/Near.sfz"), ("Far", "Multi/Far.sfz")),
        longest={},
        chokes={},
        mics_db={},
        channels_db={},
        power_curve=1.0,
    )


def stroke(start: float, level: float) -> Event:
    note = PerfNote("drums", "drum kit", Fraction(0), Fraction(1), 36, level, level)
    return Event(note, start, 0.1, level, level)


def test_the_program_reader_follows_included_files_and_variables(tmp_path):
    spec = small_kit(tmp_path / "kit")
    regions = sfzkit.read_program(tmp_path / "kit" / "Multi" / "Far.sfz")
    assert [region.sample for region in regions] == [
        "far_soft_one.flac", "far_soft_two.flac", "far_hard_one.flac", "far_hard_two.flac",
    ]  # fmt: skip
    assert [(region.low, region.high) for region in regions] == [(1, 64)] * 2 + [(65, 127)] * 2
    assert [region.volume for region in regions] == [6.0, 6.0, 0.0, 0.0]
    assert all(region.key == 36 for region in regions)
    hits = kit.read_instrument(spec, "kick")
    assert len(hits) == 4
    assert sorted(source.channel for source in hits[0].sources) == ["Far L", "Far R", "Near"]


def test_a_kit_with_layers_plays_the_layer_of_the_loudness(tmp_path):
    spec = small_kit(tmp_path / "kit")
    stems = kit.render([stroke(0.1, 0.3), stroke(0.5, 0.9)], 1.0, spec)
    near = stems["kick"][:, 0]

    def tone(start: float) -> float:
        part = near[int(start * RATE) : int((start + 0.05) * RATE)]
        spectrum = np.abs(np.fft.rfft(part * np.hanning(len(part))))
        return float(np.fft.rfftfreq(len(part), 1 / RATE)[np.argmax(spectrum)])

    assert abs(tone(0.1) - 200.0) < 30.0  # the soft layer
    assert abs(tone(0.5) - 400.0) < 30.0  # the hard layer
    # The microphone with two channels is in the room group, left and right.
    room = stems["room"]
    assert float(np.max(np.abs(room[:, 0]))) > 1.5 * float(np.max(np.abs(room[:, 1])))


def test_the_same_stroke_does_not_come_two_times(tmp_path):
    spec = small_kit(tmp_path / "kit")
    hits = kit.read_instrument(spec, "kick")
    random = np.random.default_rng(1)
    last = -1
    for _ in range(20):
        index = kit.choose(hits, 0.9, random, last)
        assert index != last
        assert hits[index].span == (65, 127)
        last = index
