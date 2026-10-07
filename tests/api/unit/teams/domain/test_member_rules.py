"""Why a member's role cannot change or why they cannot be removed (HU-06): the pure rules
the aggregate enforces and the members list explains."""

import pytest

from agilina_api.teams.domain.member_rules import (
    MemberChangeBlocker,
    is_last_admin,
    removal_blocker,
    role_change_blocker,
)
from agilina_shared.enums import TeamRole


@pytest.mark.parametrize(
    ("role", "admin_count", "expected"),
    [
        (TeamRole.ADMIN, 1, True),
        (TeamRole.ADMIN, 2, False),
        (TeamRole.MEMBER, 1, False),
        (TeamRole.MEMBER, 0, False),
    ],
)
def test_only_the_single_active_admin_is_the_last_admin(role, admin_count, expected):
    assert is_last_admin(role, admin_count) is expected


def test_a_sprint_in_progress_blocks_any_role_change_and_comes_before_the_last_admin():
    assert (
        role_change_blocker(role=TeamRole.ADMIN, admin_count=1, sprint_in_progress=True)
        is MemberChangeBlocker.SPRINT_IN_PROGRESS
    )
    assert (
        role_change_blocker(role=TeamRole.MEMBER, admin_count=2, sprint_in_progress=True)
        is MemberChangeBlocker.SPRINT_IN_PROGRESS
    )


def test_without_a_sprint_only_the_last_admin_cannot_have_their_role_changed():
    assert (
        role_change_blocker(role=TeamRole.ADMIN, admin_count=1, sprint_in_progress=False)
        is MemberChangeBlocker.LAST_ADMIN
    )
    assert role_change_blocker(role=TeamRole.ADMIN, admin_count=2, sprint_in_progress=False) is None
    assert (
        role_change_blocker(role=TeamRole.MEMBER, admin_count=1, sprint_in_progress=False) is None
    )


def test_only_the_last_admin_cannot_be_removed():
    assert removal_blocker(role=TeamRole.ADMIN, admin_count=1) is MemberChangeBlocker.LAST_ADMIN
    assert removal_blocker(role=TeamRole.ADMIN, admin_count=2) is None
    assert removal_blocker(role=TeamRole.MEMBER, admin_count=1) is None


def test_the_codes_are_the_stable_strings_the_interface_translates():
    assert [blocker.value for blocker in MemberChangeBlocker] == [
        "last_admin",
        "sprint_in_progress",
    ]
