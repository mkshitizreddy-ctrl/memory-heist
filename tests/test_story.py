"""Story text: every part of the run has a beat, and every beat fits a card."""

import pytest

from core.level_manager import LEVEL_ORDER
from core.story import ANTAGONIST, HERO, PARTNER, STORY, beat_for


def test_cast_names():
    assert (HERO, PARTNER, ANTAGONIST) == ("Ghost", "Echo", "WARDEN")


def test_there_is_a_beat_for_the_intro_every_level_and_the_ending():
    assert set(STORY) == {"intro", "outro", *LEVEL_ORDER}


@pytest.mark.parametrize("key", ["intro", "outro", *LEVEL_ORDER])
def test_every_beat_has_a_title_and_a_few_short_lines(key):
    beat = STORY[key]

    assert isinstance(beat["title"], str) and beat["title"].strip()
    assert 1 <= len(beat["lines"]) <= 4
    for line in beat["lines"]:
        assert isinstance(line, str) and line.strip()
        assert len(line) <= 80, f"{key}: line too long for a card: {line!r}"


@pytest.mark.parametrize("level", LEVEL_ORDER)
def test_every_level_beat_names_the_concept_it_teaches(level):
    assert STORY[level]["concept"].strip()


def test_beat_for_returns_the_beat_or_none():
    assert beat_for("level3") is STORY["level3"]
    assert beat_for("no_such_level") is None
