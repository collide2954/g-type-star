"""Tests for the parts of the full render."""

from gtypestar.audio import render
from gtypestar.perform.feel import Event


def events(times: list[float]) -> list[Event]:
    return [Event(note=None, start=time, seconds=0.1, level=0.5, level_end=0.5) for time in times]  # type: ignore[arg-type]


def test_each_note_is_in_one_part_of_the_render():
    # Notes near the line between two parts (at 40 seconds): two of them are a little early.
    times = [0.0, 10.0, 39.9, 39.96, 39.99, 40.0, 40.02, 79.97, 80.0]
    first = render._inside(events(times), 0.0, 40.0, last=False)
    second = render._inside(events(times), 40.0, 80.0, last=False)
    third = render._inside(events(times), 80.0, 120.0, last=True)
    assert len(first) + len(second) + len(third) == len(times)
    # The early notes are in the part that starts at the line, inside its lead time.
    assert [round(event.start, 2) for event in first] == [0.0, 10.0, 39.9]
    lead = render.LEAD_SECONDS
    assert [round(event.start - lead, 2) for event in second] == [-0.04, -0.01, 0.0, 0.02]
    assert len(third) == 2


def test_an_excerpt_keeps_its_last_notes():
    times = [100.0, 139.98]
    assert len(render._inside(events(times), 100.0, 140.0)) == 2
