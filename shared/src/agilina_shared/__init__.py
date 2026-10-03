"""Domain models and contract shared by the Agilina deployables.

This package is the reason Agilina lives in a single repository: the contract
between the worker and the API is expressed as shared types instead of
documentation that goes stale (architecture document, section 5.2).
"""

from agilina_shared.contract import (
    CeremonyContext,
    CeremonyResult,
    ParticipantContext,
    TranscriptSegment,
)
from agilina_shared.enums import (
    CeremonyStatus,
    CeremonyType,
    Language,
    OperationMode,
    TeamRole,
)

__all__ = [
    "CONTRACT_VERSION",
    "CeremonyContext",
    "CeremonyResult",
    "CeremonyStatus",
    "CeremonyType",
    "Language",
    "OperationMode",
    "ParticipantContext",
    "TeamRole",
    "TranscriptSegment",
]

CONTRACT_VERSION = "2.0"
"""Worker ↔ API contract version.

Changing it is a BREAKING CHANGE and must be declared in the commit footer
(Avance 1 document, section 7.3). 2.0: field names and enum values moved to
English; nothing was deployed with 1.0.
"""
