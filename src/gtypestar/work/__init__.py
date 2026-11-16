"""The work: G-Type Star, written as code."""

from __future__ import annotations

from ..notation.work import Work, load_orchestra
from . import agb, dwarf, flares, flash, giant, ignition, mainseq, mix, nebula

TITLE = "G-Type Star"
COMPOSER = "Brett Gilio"


def build() -> Work:
    """Build the full work from its parts."""
    work = Work(TITLE, load_orchestra(), composer=COMPOSER)
    nebula.write(work)
    ignition.write(work)
    mainseq.write(work)
    flares.write(work)
    giant.write(work)
    flash.write(work)
    agb.write(work)
    dwarf.write(work)
    work.extras["mix"] = mix.settings()
    work.check_complete()
    return work
