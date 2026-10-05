"""TeamName: a team's name is trimmed, never blank and at most 80 characters (HU-05)."""

import pytest

from agilina_api.teams.domain.errors import InvalidTeamNameError
from agilina_api.teams.domain.team_name import MAX_LENGTH, TeamName


def test_a_name_is_stored_trimmed():
    name = TeamName("  Atlas \n")

    assert name.value == "Atlas"
    assert str(name) == "Atlas"


def test_a_blank_name_is_rejected():
    with pytest.raises(InvalidTeamNameError):
        TeamName("")


@pytest.mark.parametrize("raw", [" ", "     ", "\t\n "])
def test_a_name_of_only_spaces_is_rejected(raw):
    with pytest.raises(InvalidTeamNameError):
        TeamName(raw)


def test_the_limit_is_80_characters():
    assert MAX_LENGTH == 80


def test_a_name_of_80_characters_after_trimming_is_accepted():
    assert TeamName("x" * 80).value == "x" * 80


def test_a_name_longer_than_80_characters_is_rejected():
    with pytest.raises(InvalidTeamNameError):
        TeamName("x" * 81)


def test_surrounding_spaces_do_not_count_towards_the_limit():
    assert TeamName("   " + "x" * 80 + "   ").value == "x" * 80


def test_characters_are_counted_as_code_points_like_postgresql():
    """An emoji is one character for Python's ``len`` and for ``char_length``."""
    assert TeamName("🚀" * 80).value == "🚀" * 80
    with pytest.raises(InvalidTeamNameError):
        TeamName("🚀" * 81)
