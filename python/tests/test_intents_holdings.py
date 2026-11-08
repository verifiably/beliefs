"""The one interior: generated from the shared holdings shape."""

import json
from importlib import resources

import pytest

from beliefs.intents.holdings import ACT_KINDS, MUTATING_KINDS, decode_holdings_intent

TREE = "e" * 64
STORE = "d" * 32
STORE_LOCATION = {"relative_path": "held.bin", "store_id": STORE, "type": "store"}
TREE_LOCATION = {"store_id": STORE, "tree": TREE, "type": "store-tree"}
URL_LOCATION = {"type": "url", "url": "https://example.org/data"}


def _row(kind: str, location: dict[str, str]) -> dict[str, object]:
    payload = {
        "actor": "actor",
        "domain": "science.holdings-intent.v1",
        "event_token": "token",
        "kind": kind,
        "location": location,
    }
    return {"digest": "1" * 64, "entry": {"payload": json.dumps(payload, sort_keys=True).encode().hex()}}


def test_qualify_source_is_generated_from_the_shared_shape() -> None:
    shared = resources.files("beliefs.intents").joinpath("holdings.py").read_bytes()
    generated = resources.files("beliefs.holdings").joinpath("qualify.py").read_bytes()
    header, _, body = generated.partition(b"\n# Edit the source and regenerate; hand edits here are discarded.\n")
    assert header.startswith(b"# GENERATED from beliefs/intents/holdings.py")
    assert body == shared


def test_shared_shape_stays_in_the_dialect() -> None:
    source = resources.files("beliefs.intents").joinpath("holdings.py").read_text()
    imports = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert imports == ["import json"]


def test_the_rule_digest_moved_with_the_regeneration() -> None:
    from beliefs.holdings.reduce import holdings_rule_bundle
    from beliefs.world.rules import implementation_identity

    bundle = holdings_rule_bundle()
    shared = resources.files("beliefs.intents").joinpath("holdings.py").read_bytes()
    assert shared in bundle.implementation
    assert len(implementation_identity(bundle.implementation)) == 64


def test_tree_write_is_a_mutating_kind() -> None:
    assert "tree-write" in ACT_KINDS
    assert "tree-write" in MUTATING_KINDS


@pytest.mark.parametrize("kind", ["tree-write", "re-check"])
def test_decode_keys_a_store_tree_intent_by_its_canonical_form(kind: str) -> None:
    decoded = decode_holdings_intent(_row(kind, TREE_LOCATION))

    assert decoded is not None
    assert decoded["location"] == f"store-tree:{STORE}:{TREE}"
    assert decoded["kind"] == kind


@pytest.mark.parametrize(
    ("kind", "location"),
    [
        ("write", TREE_LOCATION),
        ("delete", TREE_LOCATION),
        ("move-source", TREE_LOCATION),
        ("move-destination", TREE_LOCATION),
        ("tree-write", STORE_LOCATION),
        ("tree-write", URL_LOCATION),
        ("re-check", {**TREE_LOCATION, "tree": "E" * 64}),
        ("re-check", {**TREE_LOCATION, "tree": "e" * 63}),
        ("re-check", {**TREE_LOCATION, "relative_path": "x"}),
    ],
)
def test_decode_refuses_mismatched_kind_and_location(kind: str, location: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="^malformed holdings intent at "):
        decode_holdings_intent(_row(kind, location))
