"""Lineage-inherited standing fixtures: an acquired ancestor, the production
run that transforms it, the derived dataset it produces, and the analysis run
and assessment that observe the derived dataset.

A derived dataset's basis is stamped here as `publication_plan` stamps it — one
route naming the producing run, the ancestor and `[ancestor]` as its
transforms — unless a test hands its own routes. A route carries an `identity`
only when a test asks for one, as boundary-minted routes never do.
"""

from __future__ import annotations

from typing import Any

from authority import ACTOR
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut3 import typed_applicability, typed_estimand, typed_target
from nodes.core.node import Node

from beliefs import stored
from beliefs.identity import v1

__all__ = [
    "OBSERVATION",
    "acquired",
    "analysis",
    "assessment_over",
    "derived",
    "node_retraction",
    "plain",
    "production",
    "ref",
    "route",
    "route_retraction",
]

OBSERVATION = {"locator": "instrument:fixture", "attested_by": ACTOR}


def acquired(seed: str, *, retrieval: str | None = None) -> Node:
    """A dataset carrying a valid `empirical-observation` facet."""
    payload: dict[str, Any] = dict(OBSERVATION)
    if retrieval is not None:
        payload["retrieval"] = retrieval
    return stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation=payload)


def plain(seed: str) -> Node:
    """A dataset carrying neither `empirical-observation` nor a basis."""
    return stored.dataset_node(title=seed, resources=pinned(seed))


def route(run: str, ancestor: str, *, identity: str | None = None, transforms: Any = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "run": run,
        "ancestor": ancestor,
        "transforms": [ancestor] if transforms is None else transforms,
    }
    if identity is not None:
        value["identity"] = identity
    return value


def derived(seed: str, *routes: dict[str, Any]) -> Node:
    """A dataset carrying a tagged basis over `routes`: `single` for one,
    `conflict` (canonically sorted) for several."""
    ordered = sorted(routes, key=v1.encode)
    basis = {"tag": "single" if len(ordered) == 1 else "conflict", "routes": ordered}
    return stored.dataset_node(title=seed, resources=pinned(seed), basis=basis)


def production(slug: str, ancestor: str, produced: str, *, transforms: tuple[str, ...] | None = None) -> Node:
    """A dataset-production run: it transforms `ancestor` and produces `produced`."""
    return stored.run_node(
        slug,
        title=slug,
        spec="analysis-spec:s1",
        transforms=list((ancestor,) if transforms is None else transforms),
        produces=[produced],
    )


def analysis(slug: str, *observes: str) -> Node:
    return stored.run_node(slug, title=slug, spec="analysis-spec:s1", observes=list(observes))


def assessment_over(slug: str, run: str, proposition: str = "proposition:p1") -> Node:
    return stored.assessment_node(
        slug,
        title=slug,
        spec="analysis-spec:s1",
        run=run,
        proposition=proposition,
        outcome="supported",
        interpretation_rule="rule:threshold",
        target=typed_target(estimand=typed_estimand(), applicability=typed_applicability()),
    )


def route_retraction(dataset: Node, identity: str, token: str) -> Node:
    content_identity = stored.stored_semantic_hash(dataset)
    assert content_identity is not None
    return stored.retraction_node(
        title=token,
        target=stored.RouteTarget(dataset.id, dataset.id, content_identity, identity),
        reason="wrong-route",
        rationale="the route is invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
    )


def node_retraction(target: Node, token: str) -> Node:
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    return stored.retraction_node(
        title=token,
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the record is invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token=token,
    )


def ref(seed: str) -> str:
    return dataset_ref(seed)
