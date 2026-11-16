"""The work: G-Type Star, written as code."""

from __future__ import annotations

from ..notation.work import Work, load_orchestra
from . import mainseq, mix
from . import material as m

TITLE = "G-Type Star"
COMPOSER = "Brett Gilio"


def build() -> Work:
    """Build the full work from its parts."""
    work = Work(TITLE, load_orchestra(), composer=COMPOSER)
    mainseq.write(work)
    work.structure.tempo(1, 1, m.FAST, "Bright, with drive")
    work.extras["mix"] = mix.settings()
    work.check_complete()
    return work
