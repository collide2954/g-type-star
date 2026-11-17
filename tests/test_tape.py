"""Tests for the recorded sounds."""

import numpy as np

from gtypestar.audio import tape
from gtypestar.work import build

RATE = tape.RATE


def test_a_long_sound_goes_through_two_parts_of_the_render():
    work = build()
    # The first 40 seconds have the long sound of the Sun. One part, and two parts.
    whole = tape.render(work, 0.0, 40.0, 45.0, 0.0)
    first = tape.render(work, 0.0, 20.0, 25.0, 0.0)
    second = tape.render(work, 20.0, 40.0, 25.5, 0.5)
    assert whole is not None and first is not None and second is not None
    joined = np.zeros_like(whole)
    joined[: len(first)] += first[: len(joined)]
    place = int(round((20.0 - 0.5) * RATE))
    count = min(len(second), len(joined) - place)
    joined[place : place + count] += second[:count]
    span = slice(0, int(39.9 * RATE))
    assert float(np.sqrt(np.mean(whole[span] ** 2))) > 1e-4  # there is a sound
    error = float(np.max(np.abs(joined[span] - whole[span])))
    assert error < 0.02 * float(np.max(np.abs(whole[span])))


def test_a_part_has_no_sound_after_its_end():
    work = build()
    part = tape.render(work, 0.0, 20.0, 25.0, 0.0)
    assert part is not None
    assert not np.any(part[int((20.0 + 2 * tape.CROSS_SECONDS) * RATE) :])
