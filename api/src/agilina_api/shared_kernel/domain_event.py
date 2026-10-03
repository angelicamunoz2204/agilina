"""Domain events.

Named in the past tense (``InvitationAccepted``) and produced by an aggregate
when something relevant to the business happened. The instant is always passed
in (taken from a ``Clock``), never read from the system inside the domain.

Every concrete event is declared with ``@dataclass(frozen=True, kw_only=True)`` so it
can add its own fields and stays immutable.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
