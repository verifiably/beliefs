"""M1 — every read that crosses the instrumented resolver is inside the
declared closure (world-changing families §6.3).

One corpus, seeded by the raw-write fixture act and read back through a fresh
facade, exercises **every** corpus-read kind the resolver has: two assessments
on the proposition over two runs, each run observing its own pinned dataset,
one clean-environment passing verification each, and the proposition node
carrying a full claim facet. Beside them sits an **unrelated** proposition
with its own assessment, run and verification — the pool the resolver must not
read, and the material the sabotage arm reaches for.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from test_belief import PROFILE

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, Refused, SuppliedContext, evaluate
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.contract.domain import VocabularyBinding
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.evaluation import READ_KINDS, EvaluationInputs, evaluate_over, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.projection import claim_identity
from beliefs.record import AssessmentValue
from beliefs.resolution import ResolutionSnapshot, build_snapshot

# --- the claim the proposition node carries --------------------------------

EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
GENE = "EX:gene-x"
PHENO = "EX:pheno-y"
OTHER_GENE = "EX:gene-z"

CLAIM_FACET: dict[str, Any] = {
    "operator": "testing/affects",
    "args": [GENE, PHENO],
    "qualifiers": {},
    "polarity": "positive",
    "layer": "causal",
}
"""`test_belief.CLAIM`'s wire shape — the same operator, args, polarity and
layer, so the restored claim is that claim and `PROFILE` types it."""

OTHER_CLAIM_FACET: dict[str, Any] = {**CLAIM_FACET, "args": [OTHER_GENE, PHENO]}

PROPOSITION_REF = "proposition:p"
OTHER_PROPOSITION_REF = "proposition:q"
ABSENT_PROPOSITION_REF = "proposition:never-stored"


def _resources(letter: str) -> list[dict[str, str]]:
    return [{"name": f"r-{letter}", "digest": f"sha256:{letter * 64}"}]


def _declaration(letter: str) -> DatasetDeclaration:
    return DatasetDeclaration(resources=(ResourceDeclaration(name=f"r-{letter}", digest=f"sha256:{letter * 64}"),))


def _address(letter: str) -> str:
    address = dataset_address(_declaration(letter))
    assert address is not None
    return address


def _observations(*letters: str) -> dict[str, tuple[ByteObservation, ...]]:
    return {
        _address(letter): (ByteObservation(digest=f"sha256:{letter * 64}", location="repo://data"),)
        for letter in letters
    }


# --- the fixture -----------------------------------------------------------


@dataclass(frozen=True)
class CorpusFixture:
    view: ReadView
    proposition: str
    availability: Availability
    context: SuppliedContext
    resolution: ResolutionSnapshot
    binding: PolicyBinding
    assessments: tuple[AssessmentValue, ...]
    """The two matched assessment values, as the seeded nodes read back."""

    @property
    def gather_kwargs(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "profile": PROFILE,
            "resolution": self.resolution,
            "binding": self.binding,
        }

    @property
    def kwargs(self) -> dict[str, Any]:
        return {"availability": self.availability, **self.gather_kwargs}


def _seed(root: Path, proposition_ref: str) -> tuple[ReadView, dict[str, AssessmentValue]]:
    nodes: list[Node] = [
        stored.proposition_node("p", title="p", claim=CLAIM_FACET),
        stored.proposition_node("q", title="q", claim=OTHER_CLAIM_FACET),
    ]
    for letter in ("a", "b", "c"):
        nodes.append(
            stored.dataset_node(
                f"d-{letter}",
                title=f"d-{letter}",
                resources=_resources(letter),
                empirical_observation={"boundary": "instrument"},
            )
        )
        nodes.append(
            stored.run_node(f"run-{letter}", title=f"run-{letter}", spec=f"spec-{letter}", observes=[f"dataset:d-{letter}"])
        )

    assessments = [
        stored.assessment_node(
            "a-1",
            title="a-1",
            spec="spec-a",
            run="run:run-a",
            proposition=proposition_ref,
            outcome="supported",
            interpretation_rule="rule-1",
        ),
        stored.assessment_node(
            "a-2",
            title="a-2",
            spec="spec-b",
            run="run:run-b",
            proposition=proposition_ref,
            outcome="supported",
            interpretation_rule="rule-1",
        ),
        # The unrelated one: its own proposition, run, dataset and verification.
        stored.assessment_node(
            "a-3",
            title="a-3",
            spec="spec-c",
            run="run:run-c",
            proposition=OTHER_PROPOSITION_REF,
            outcome="refuted",
            interpretation_rule="rule-1",
        ),
    ]
    values = {node.id: stored.assessment_value(node) for node in assessments}
    nodes.extend(assessments)
    for index, node in enumerate(assessments, start=1):
        nodes.append(
            stored.verification_node(
                f"v-{index}",
                title=f"v-{index}",
                assessment=values[node.id].identity(),
                assessment_ref=node.id,
                scope="clean-environment",
                verdict="passed",
            )
        )

    for node in nodes:
        raw_write(root, node)
    return reopen(root), values


def _fixture(tmp_path: Path, proposition_ref: str) -> CorpusFixture:
    view, values = _seed(tmp_path, proposition_ref)
    matched = (values["assessment:a-1"], values["assessment:a-2"])
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, ("dataset:d-a", "dataset:d-b")),
        producer_snapshot_identity="producer-snapshot-1",
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        node_corpus={value.identity(): "c1" for value in values.values()},
        pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
    )
    return CorpusFixture(
        view=view,
        proposition=proposition_ref,
        availability=Availability(
            observations=_observations("a", "b"),
            implementations={BELIEF_V1.identity: BELIEF_V1},
            fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
        ),
        context=context,
        resolution=build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        assessments=matched,
    )


@pytest.fixture()
def corpus_fixture(tmp_path) -> CorpusFixture:
    return _fixture(tmp_path, PROPOSITION_REF)


@pytest.fixture()
def claimless_fixture(tmp_path) -> CorpusFixture:
    """The same corpus, with the assessments naming a proposition the corpus
    does not hold: the `assesses` target does not resolve, so no claim is
    handed out and none is traced."""
    return _fixture(tmp_path, ABSENT_PROPOSITION_REF)


# --- the rows --------------------------------------------------------------


def test_evaluate_over_is_the_corpus_backed_path_and_yields_a_belief(corpus_fixture):
    result = evaluate_over(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.kwargs)
    assert isinstance(result, Belief)
    assert result.value == 2  # two independent supports, as test_belief's scenario publishes


def test_the_restored_claim_is_the_one_the_proposition_node_carries(corpus_fixture):
    inputs = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)
    assert inputs.claim is not None
    assert claim_identity(inputs.claim)  # π_claim accepts it: the brand chain survived the restore
    assert inputs.consulted == (("science", "sci-1"), ("testing", "testing-1"))


def test_m1_every_read_through_the_resolver_is_inside_the_declared_closure(corpus_fixture):
    inputs = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)
    assert set(inputs.read_trace) <= inputs.declared_refs()
    assert {kind for kind, _ in inputs.read_trace} == set(READ_KINDS) - {
        "retraction",
        "contract",
        "producer-snapshot",
    }, "every corpus-read kind is exercised"
    answer = evaluate(
        proposition=corpus_fixture.proposition,
        records=inputs.records(),
        availability=corpus_fixture.availability,
        context=corpus_fixture.context,
        binding=corpus_fixture.binding,
        profile=PROFILE,
    )
    assert isinstance(answer, Belief)
    assert inputs.closure().digest() == answer.belief_input_digest


def test_the_records_are_already_proposition_scoped(corpus_fixture):
    inputs = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)
    assert all(a.proposition == corpus_fixture.proposition for a in inputs.assessments)
    assert {a.identity() for a in inputs.assessments} == {a.identity() for a in corpus_fixture.assessments}
    assert set(inputs.runs) == {a.run for a in inputs.assessments}
    assert all(v.assessment in {a.identity() for a in inputs.assessments} for v in inputs.verifications)
    records = inputs.records()
    assert records.assessments == inputs.assessments
    assert set(records.claims) == {corpus_fixture.proposition}
    assert records.source_assertions == ()


def test_m1_sabotage_shape_an_unrelated_verification_read_fails_containment(corpus_fixture, monkeypatch):
    """The sabotage N2 declares: `gather` reads one verification belonging to a
    different proposition; the digest is unchanged and the check fails."""
    from beliefs import evaluation

    honest = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)
    monkeypatch.setattr(evaluation, "_verification_selected", lambda value, ids: True)
    leaky = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)

    assert {v.ref for v in leaky.verifications} > {v.ref for v in honest.verifications}
    assert leaky.closure().digest() == honest.closure().digest()
    assert set(honest.read_trace) <= honest.declared_refs()
    assert not set(leaky.read_trace) <= leaky.declared_refs()


def test_the_binding_is_guarded_before_any_read(corpus_fixture, monkeypatch):
    from beliefs import evaluation

    monkeypatch.setattr(evaluation, "gather", lambda *a, **k: pytest.fail("read before the binding was refused"))
    result = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **{**corpus_fixture.kwargs, "binding": ("rule", "impl")},
    )
    assert isinstance(result, Refused) and result.reason.startswith("binding-not-exact")


def test_a_proposition_with_no_claim_record_consults_only_the_base_contract(claimless_fixture):
    inputs = gather(claimless_fixture.view, claimless_fixture.proposition, **claimless_fixture.gather_kwargs)
    assert inputs.claim is None
    assert dict(inputs.records().claims) == {}
    assert inputs.consulted == (("science", "sci-1"),)
    assert "proposition" not in {kind for kind, _ in inputs.read_trace}
    assert set(inputs.read_trace) <= inputs.declared_refs()


def test_no_belief_and_refused_arms_assert_no_containment(corpus_fixture, monkeypatch):
    from beliefs import evaluation

    calls: list[str] = []
    real = evaluation.gather
    monkeypatch.setattr(
        evaluation, "gather", lambda *a, **k: (calls.append("gathered"), real(*a, **k))[1]
    )
    result = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **{**corpus_fixture.kwargs, "availability": replace(corpus_fixture.availability, fixtures={})},
    )
    assert isinstance(result, NoBelief) and result.reason == "unavailable-fixtures-unheld"
    assert calls == ["gathered"], "the guard is on the Belief arm only; gather still ran once"


def test_the_nine_fields_are_build_closure_s_keywords_in_order():
    import inspect

    from beliefs.closure import build_closure

    params = [p for p in inspect.signature(build_closure).parameters if p != "self"]
    fields = [f.name for f in dataclasses.fields(EvaluationInputs)][:9]
    assert fields == params
