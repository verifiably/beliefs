"""Every `shape: reader` facet label in the shipped base contract names a live attribute."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL = REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"
PACKAGED = REPO_ROOT / "python" / "src" / "beliefs" / "contracts" / "science" / "CONTRACT.yaml"

KNOWN_DANGLING = {"runrecord.projection_of"}  # beliefs-af903c


def _resolves(dotted: str) -> bool:
    """Import the longest importable module prefix and walk remaining dotted attributes without calling them."""
    parts = dotted.split(".")
    target: object | None = None
    rest: list[str] = []
    for end in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:end])
        try:
            target = importlib.import_module(prefix)
            rest = parts[end:]
            break
        except ModuleNotFoundError as exc:
            if exc.name is not None and prefix != exc.name and not prefix.startswith(exc.name + "."):
                raise
    if target is None or not rest:
        return False
    for attr in rest:
        try:
            target = getattr(target, attr)
        except AttributeError:
            return False
    return True


@pytest.mark.parametrize("path", [CANONICAL, PACKAGED])
def test_every_reader_label_names_an_attribute(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    readers = {
        facet["reader"]
        for facet in document["facets"].values()
        if isinstance(facet, dict) and facet.get("shape") == "reader"
    }
    unresolved = {label for label in readers if not _resolves("beliefs." + label)}
    resolved = readers - unresolved
    assert {"stored.source_assertion_value", "corpus.CorpusWriter._validated_retraction"} <= resolved
    assert unresolved == KNOWN_DANGLING


def test_resolver_rejects_missing_module_and_missing_attribute() -> None:
    assert not _resolves("beliefs.nonexistent_module_for_test.reader")
    assert not _resolves("beliefs.stored.nonexistent_reader_for_test")
