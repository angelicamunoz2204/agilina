"""Domain enumerations.

The values are the ones that travel through the API and are stored in the
database (they match the PostgreSQL enum types); the labels shown to the user
are resolved in the presentation layer, which is where the rule that the
Admin is displayed as Scrum Master when the team is in support mode lives.
"""

from agilina_shared.enums.ceremony_status import CeremonyStatus
from agilina_shared.enums.ceremony_type import CeremonyType
from agilina_shared.enums.language import Language
from agilina_shared.enums.operation_mode import OperationMode
from agilina_shared.enums.team_role import TeamRole

__all__ = [
    "CeremonyStatus",
    "CeremonyType",
    "Language",
    "OperationMode",
    "TeamRole",
]
