"""Shared corpus shape for domain-facet reader tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from authority import ACTOR
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from profiles import biology, pins_for
from test_evaluation import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO, _observations, _resources

from beliefs import stored
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.contract import domain
from beliefs.corpus import CorpusWriter, ReadView, lineage_snapshot
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract
from beliefs.resolution import build_snapshot

PROPOSITION_REF = "proposition:p"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _fixture_document(name: str) -> dict:
    import yaml

    return yaml.safe_load((REPO_ROOT / "fixtures" / "contracts" / f"{name}.yaml").read_text(encoding="utf-8"))


def testing_contract(description: str | None = None):
    document = _fixture_document("testing")
    if description is not None:
        document["description"] = description
    return domain.parse_domain_contract(document, source="<test>", base=shipped_base_contract(), predecessor=None)


def crossing_contract():
    return domain.parse_domain_contract(
        _fixture_document("crossing"), source="<crossing>", base=shipped_base_contract(), predecessor=None
    )


def unrelated_contract(description: str):
    document = _fixture_document("testing")
    document["contract"] = "unrelated"
    document["description"] = description
    return domain.parse_domain_contract(
        document, source="<unrelated>", base=shipped_base_contract(), predecessor=None
    )


def profile_with(
    biology_description: str = "fixture",
    *,
    unrelated: str | None = None,
    testing_description: str | None = None,
    crossing: bool = False,
) -> ProfileSpec:
    contracts = [testing_contract(testing_description), biology(biology_description)]
    if unrelated is not None:
        contracts.append(unrelated_contract(unrelated))
    if crossing:
        contracts.append(crossing_contract())
    return compile_profile(shipped_base_contract(), contracts)


CROSSING_CLAIM: dict[str, Any] = {
    "operator": "crossing/affects-local-entity",
    "args": [OTHER_GENE, GENE],
    "qualifiers": {},
    "polarity": "positive",
    "layer": "causal",
}


def seed(
    corpus: Path | CorpusWriter,
    *,
    axis: str | None = "rows",
    observes_missing: bool = False,
    claim: dict[str, Any] | None = None,
    proposition: str = PROPOSITION_REF,
) -> ReadView:
    domain_facets: dict[str, Any] = {"biology/gene-axis": {"axis": axis}} if axis is not None else {}
    nodes: list[Node] = [stored.proposition_node("p", title="p", claim=claim or CLAIM_FACET)]
    nodes.append(
        stored.dataset_node(
            "d-a",
            title="d-a",
            resources=_resources("a"),
            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
            domain_facets=domain_facets,
        )
    )
    nodes.append(
        stored.dataset_node(
            "d-b",
            title="d-b",
            resources=_resources("b"),
            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
        )
    )
    nodes.append(
        stored.run_node(
            "run-a",
            title="run-a",
            spec="spec-a",
            observes=["dataset:d-missing" if observes_missing else "dataset:d-a"],
        )
    )
    nodes.append(stored.run_node("run-b", title="run-b", spec="spec-b", observes=["dataset:d-b"]))
    assessments = [
        stored.assessment_node(
            "a-1", title="a-1", spec="spec-a", run="run:run-a", proposition=proposition,
            outcome="supported", interpretation_rule="rule-1"
        ),
        stored.assessment_node(
            "a-2", title="a-2", spec="spec-b", run="run:run-b", proposition=proposition,
            outcome="supported", interpretation_rule="rule-1"
        ),
    ]
    nodes.extend(assessments)
    for index, node in enumerate(assessments, start=1):
        value = stored.assessment_value(node)
        nodes.append(
            stored.verification_node(
                f"v-{index}", title=f"v-{index}", assessment=value.identity(), assessment_ref=node.id,
                scope="clean-environment", verdict="passed"
            )
        )
    if isinstance(corpus, CorpusWriter):
        for node in nodes:
            corpus.add(node)
        return corpus.read_view
    corpus.mkdir(parents=True, exist_ok=True)
    for node in nodes:
        raw_write(corpus, node)
    return reopen(corpus)


def kwargs_for(view: ReadView, profile: ProfileSpec) -> dict[str, Any]:
    identities = {stored.assessment_value(n).identity() for n in view.iter_stored() if n.kind == "assessment"}
    return {
        "availability": Availability(
            observations=_observations("a", "b"),
            implementations={BELIEF_V1.identity: BELIEF_V1},
            fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
        ),
        "context": SuppliedContext(
            snapshot=lineage_snapshot(view, ("dataset:d-a", "dataset:d-b")),
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={identity: ("c1",) for identity in identities},
            pins={"c1": pins_for(profile)},
        ),
        "profile": profile,
        "resolution": build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        "binding": PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
    }
