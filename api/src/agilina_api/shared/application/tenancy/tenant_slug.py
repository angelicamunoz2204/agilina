import re

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9]{1,30}$")


RESERVED_SLUGS = frozenset({"platform", "admin", "api"})


"""Names the platform keeps for itself (the catalog's database is ``agilina_platform``)."""


def is_valid_slug(slug: str) -> bool:
    """A slug is lowercase letters and digits, starts with a letter and has 2 to 31
    characters: it becomes a database name and a realm name, so it cannot be anything else."""
    return SLUG_PATTERN.fullmatch(slug) is not None and slug not in RESERVED_SLUGS
