"""Queries over workflow runs."""

from collections.abc import Iterable

from beliefs.recipe import RunClosure


def same_definition(runs: Iterable[RunClosure]) -> dict[str, tuple[str, ...]]:
    """Group run addresses by workflow definition identity."""
    grouped: dict[str, list[str]] = {}
    for run in runs:
        grouped.setdefault(run.recipe.workflow_definition.identity(), []).append(run.address())
    return {identity: tuple(sorted(addresses)) for identity, addresses in grouped.items()}
