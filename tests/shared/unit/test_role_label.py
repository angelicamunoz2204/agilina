"""The visible label of a role: derived from the role and the team's mode, never stored."""

import pytest

from agilina_shared import OperationMode, RoleLabel, TeamRole, role_label


@pytest.mark.parametrize(
    ("role", "mode", "label"),
    [
        (TeamRole.ADMIN, OperationMode.SUPPORT, RoleLabel.SCRUM_MASTER),
        (TeamRole.ADMIN, OperationMode.AUTONOMOUS, RoleLabel.ADMIN),
        (TeamRole.MEMBER, OperationMode.SUPPORT, RoleLabel.MEMBER),
        (TeamRole.MEMBER, OperationMode.AUTONOMOUS, RoleLabel.MEMBER),
    ],
)
def test_the_label_follows_the_role_and_the_mode(role, mode, label):
    assert role_label(role, mode) is label


def test_there_is_a_label_for_every_role_and_mode():
    labels = {role_label(role, mode) for role in TeamRole for mode in OperationMode}

    assert labels == set(RoleLabel)


def test_the_codes_are_stable():
    assert [label.value for label in RoleLabel] == ["member", "scrum_master", "admin"]
