"""Load the fixture-bound holdings reducer."""

from __future__ import annotations

from importlib import resources

from science.world.rules import RuleBundle

__all__ = ["holdings_rule_bundle"]


def holdings_rule_bundle() -> RuleBundle:
    package = resources.files("science.holdings.rules_v1")
    fixtures = tuple(
        sorted(
            (path.name, path.read_bytes())
            for path in (package / "fixtures").iterdir()
            if path.name.startswith("holdings.") and path.name.endswith(".yaml")
        )
    )
    qualify = resources.files("science.holdings").joinpath("qualify.py").read_bytes()
    return RuleBundle(
        symbol="reduce_holdings",
        fixtures=fixtures,
        implementation=qualify + b"\n\n" + (package / "holdings.py").read_bytes(),
    )
