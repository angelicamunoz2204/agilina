"""State machine of the daily stand-up.

What Agilina says always comes from per-language templates, never from the
language model (AD-19): interventions depend on the state of the ceremony,
which the worker knows, and not on the content of what was said.

Room controls arrive through the LiveKit data channel, not through the API,
and their sender is provided by LiveKit signed in the token. That is why the
permission check lives here, against the roster of the context, and never
trusts the content of the message.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from agilina_shared.contract import CeremonyContext, ParticipantContext
from agilina_shared.enums import TeamRole
from agilina_shared.i18n import render_text


class FacilitationState(StrEnum):
    WAITING = "waiting"
    GREETING = "greeting"
    TURN = "turn"
    CLOSED = "closed"
    DEGRADED = "degraded"


class ActionNotAllowedError(Exception):
    """The sender is not allowed to perform that action according to the roster."""


@dataclass
class FacilitationMachine:
    """Conducts one ceremony. One instance per room.

    In the WAITING state Agilina is in the room but sends no audio to the
    transcription service: that is why the daily starts with a button and not
    with a wake word.
    """

    context: CeremonyContext
    state: FacilitationState = FacilitationState.WAITING
    turn_index: int = -1
    degradation_reason: str | None = None
    _order: list[ParticipantContext] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._order = sorted(self.context.participants, key=lambda p: p.turn_order)

    # --------------------------------------------------------------- queries --
    @property
    def current_turn(self) -> ParticipantContext | None:
        if self.state is not FacilitationState.TURN:
            return None
        return self._order[self.turn_index]

    def participant(self, room_identity: str) -> ParticipantContext:
        for participant in self._order:
            if participant.room_identity == room_identity:
                return participant
        raise ActionNotAllowedError(f"'{room_identity}' is not in the ceremony roster")

    def is_admin(self, room_identity: str) -> bool:
        return self.participant(room_identity).role is TeamRole.ADMIN

    # ------------------------------------------------------------ transitions --
    def start(self, room_identity: str) -> str:
        """Start the ceremony. Only the Admin or Scrum Master can."""
        if not self.is_admin(room_identity):
            raise ActionNotAllowedError("Only the Admin or Scrum Master starts the ceremony")
        if self.state is not FacilitationState.WAITING:
            raise ActionNotAllowedError("The ceremony was already started")

        self.state = FacilitationState.GREETING
        return render_text(
            "greeting",
            self.context.language,
            day=self.context.sprint_day,
            total=self.context.sprint_total_days,
        )

    def hand_over_turn(self) -> str | None:
        """Move on to the next participant. Returns None when none are left."""
        if self.state not in (FacilitationState.GREETING, FacilitationState.TURN):
            raise ActionNotAllowedError("The ceremony is not in progress")

        if self.turn_index + 1 >= len(self._order):
            return None

        self.turn_index += 1
        self.state = FacilitationState.TURN
        next_participant = self._order[self.turn_index]
        return render_text("hand_over_turn", self.context.language, name=next_participant.name)

    def end_turn(self, room_identity: str) -> str | None:
        """Close the turn in progress.

        Everyone can end their own; the Admin or Scrum Master can end anyone's.
        """
        current = self.current_turn
        if current is None:
            raise ActionNotAllowedError("There is no turn in progress")

        sender = self.participant(room_identity)
        is_own_turn = sender.user_id == current.user_id
        if not is_own_turn and sender.role is not TeamRole.ADMIN:
            raise ActionNotAllowedError("Only the Admin can end someone else's turn")

        return self.hand_over_turn()

    def ask_about_silence(self) -> str:
        current = self.current_turn
        if current is None:
            raise ActionNotAllowedError("There is no turn in progress")
        return render_text("silence", self.context.language, name=current.name)

    def ask_about_stuck_turn(self) -> str:
        current = self.current_turn
        if current is None:
            raise ActionNotAllowedError("There is no turn in progress")
        return render_text("stuck_turn", self.context.language, name=current.name)

    def close(self, room_identity: str | None = None) -> str:
        """Close the ceremony.

        With a sender, it checks that they are the Admin or Scrum Master;
        without one, it is the automatic close when the turns run out.
        """
        if room_identity is not None and not self.is_admin(room_identity):
            raise ActionNotAllowedError("Only the Admin or Scrum Master closes the ceremony")

        self.state = FacilitationState.CLOSED
        return render_text("farewell", self.context.language)

    def degrade(self, reason: str) -> str:
        """The transcription service does not respond.

        Agilina announces it out loud and the ceremony goes on without automatic
        facilitation, instead of leaving the room silent waiting.
        """
        self.state = FacilitationState.DEGRADED
        self.degradation_reason = reason
        return render_text("degraded", self.context.language)
