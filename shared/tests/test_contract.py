"""The contract is what keeps the worker and the API aligned: if these tests
fail, one deployable stopped understanding the other."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agilina_shared import (
    CeremonyContext,
    CeremonyResult,
    CeremonyStatus,
    Language,
    OperationMode,
    ParticipantContext,
    TeamRole,
    TranscriptSegment,
)


def _participant(order: int = 0) -> ParticipantContext:
    return ParticipantContext(
        user_id=uuid4(),
        name="Diego",
        room_identity="user-1",
        role=TeamRole.MEMBER,
        turn_order=order,
    )


def _context() -> CeremonyContext:
    return CeremonyContext(
        ceremony_id=uuid4(),
        team_id=uuid4(),
        room="ceremony-1",
        language=Language.ES,
        mode=OperationMode.SUPPORT,
        sprint_day=3,
        sprint_total_days=15,
        participants=[_participant(0), _participant(1)],
    )


def test_context_survives_a_json_round_trip():
    context = _context()
    restored = CeremonyContext.model_validate_json(context.model_dump_json())
    assert restored == context


def test_thresholds_have_the_agreed_starting_values():
    context = _context()
    assert context.silence_seconds == 10
    assert context.stuck_turn_seconds == 30


def test_an_unknown_field_breaks_immediately():
    """An incompatibility between versions must fail, not go unnoticed."""
    data = _context().model_dump(mode="json")
    data["field_that_does_not_exist"] = True
    with pytest.raises(ValidationError):
        CeremonyContext.model_validate(data)


def test_result_allows_a_degraded_ceremony_without_segments():
    result = CeremonyResult(
        ceremony_id=uuid4(),
        status=CeremonyStatus.DEGRADED,
        started_at=datetime.now(UTC),
        closed_at=datetime.now(UTC),
        present_participants=[uuid4()],
        segments=[],
        degraded=True,
        degradation_detail="The transcription service did not respond",
    )
    assert result.degraded is True


def test_segment_keeps_speaker_and_timestamps():
    segment = TranscriptSegment(
        user_id=uuid4(),
        room_identity="user-1",
        text="Yesterday I finished the migration",
        start_ms=0,
        end_ms=2400,
    )
    assert segment.end_ms > segment.start_ms


def test_enum_values_match_the_database_enum_types():
    """The values travel through the API and are stored as PostgreSQL enums."""
    assert {mode.value for mode in OperationMode} == {"support", "autonomous"}
    assert {role.value for role in TeamRole} == {"admin", "member"}
