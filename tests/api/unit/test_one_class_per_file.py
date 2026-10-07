"""A file declares one class: the file's name says which (code-conventions.md)."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
FILES = sorted([*(ROOT / "api/src").rglob("*.py"), *(ROOT / "shared/src").rglob("*.py")])


def _classes(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def test_the_sources_are_found():
    assert len(FILES) > 100


@pytest.mark.parametrize("path", FILES, ids=lambda path: str(path.relative_to(ROOT)))
def test_a_file_declares_at_most_one_class(path: Path):
    assert len(_classes(path)) <= 1
