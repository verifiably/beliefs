"""The one interior: generated from the shared holdings shape (spec §4)."""

from importlib import resources


def test_qualify_source_is_generated_from_the_shared_shape() -> None:
    shared = resources.files("beliefs.intents").joinpath("holdings.py").read_bytes()
    generated = resources.files("beliefs.holdings").joinpath("qualify.py").read_bytes()
    header, _, body = generated.partition(
        b"\n# Edit the source and regenerate; hand edits here are discarded.\n"
    )
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
