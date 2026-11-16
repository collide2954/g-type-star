"""Tests for the numbers in the documents."""

from gtypestar import documents
from gtypestar.work import build


def test_the_documents_are_up_to_date():
    work = build()
    for path in documents.FILES:
        text = path.read_text(encoding="utf-8")
        assert documents.updated(text, work) == text, (
            f"{path.name} is not up to date: run `uv run gtypestar docs`"
        )


def test_the_work_follows_the_brief():
    work = build()
    structure = work.structure
    assert abs(structure.duration_seconds - 780.0) < 0.05  # 13 minutes
    # The dubstep passage: one time, 30 seconds or less.
    bars = dict(zip([number for number, *_ in documents.PARTS], documents.part_bars(work),
                    strict=True))  # fmt: skip
    first, last = bars["6"]
    seconds = structure.seconds(structure.bar(last).end) - structure.seconds(
        structure.bar(first).start
    )
    assert seconds <= 30.0
    # One sudden pause in the work.
    assert documents.pause(work) is not None


def test_clock():
    assert documents.clock(453.2) == "7:33"
    assert documents.clock(59.6) == "1:00"
