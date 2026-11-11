"""Every read that crosses the instrumented resolver is inside the
declared closure.

One corpus, seeded by the raw-write fixture act and read back through a fresh
facade, exercises **every** corpus-read kind the resolver has: two assessments
on the proposition over two runs, each run observing its own pinned dataset,
one clean-environment passing verification each, and the proposition node
carrying a full claim facet. Beside them sits an **unrelated** proposition
with its own assessment, run and verification — the pool the resolver must not
read, and the material a deliberately wrong read reaches for.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from authority import ACTOR
from domain_facet_fixtures import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO
from fixtures_cut3 import MEASUREMENT_RECORDS, frozen_fixture_spec, only_assessed_key, typed_estimand
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation
from profiles import pins_for
from test_belief import CLAIM as EXPECTED_CLAIM
from test_belief import PROFILE

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, Refused, SuppliedContext, evaluate
from beliefs.corpus import CorpusWriter, ReadView, lineage_snapshot
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.estimand import Estimand
from beliefs.evaluation import READ_KINDS, EvaluationInputs, evaluate_over, gather
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding, PolicyImplementation
from beliefs.projection import claim_identity, project_claim
from beliefs.record import AssessmentValue
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from beliefs.spec import SpecInput
from beliefs.target import target_projection

# --- the claim the proposition node carries --------------------------------
#
# `EX`, `GENE`, `PHENO`, `OTHER_GENE` and `CLAIM_FACET` are
# `domain_facet_fixtures`'; `CLAIM_FACET` is `test_belief.CLAIM`'s wire shape,
# so the restored claim is that claim and `PROFILE` types it.

OTHER_CLAIM_FACET: dict[str, Any] = {
    **CLAIM_FACET,
    "roles": {**CLAIM_FACET["roles"], "cause": {"sort": "testing/entity", "term": OTHER_GENE}},
}

EMPIRICAL: dict[str, str] = {"locator": "instrument:fixture", "attested_by": ACTOR}
"""The empirical-observation facet every fixture dataset carries; the writer's
boundary requires `attested_by` to be the writer's own actor."""

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


def _seed(
    corpus: Path | CorpusWriter,
    proposition_ref: str,
    *,
    reads: bool = False,
    assesses_target: str | None = None,
    estimand: Estimand | None = None,
) -> tuple[ReadView, dict[str, AssessmentValue]]:
    """Seed the corpus and hand back a **fresh** view over what is on disk.

    A path takes the raw-write fixture act, which is what the divergent
    `assesses` edge needs and what these portable rows have always used. An
    open `CorpusWriter` — the acceptance module, bound to a registered
    root — mints the same records through `add` instead, so the durable test
    reads bytes the certified engine committed. The two paths must stay
    interchangeable, so the writer path is offered only where the fixture asks
    for nothing a raw write alone can build.

    `estimand` replaces the two matched assessments' estimand (default
    `typed_estimand()`, built for `CLAIM_FACET`'s claim)."""
    matched_estimand = typed_estimand()
    nodes: list[Node] = [
        stored.proposition_node("p", title="p", claim=CLAIM_FACET),
        stored.proposition_node("q", title="q", claim=OTHER_CLAIM_FACET),
    ]
    if reads:
        nodes.append(
            stored.dataset_node(
                title="d-e",
                resources=_resources("e"),
                empirical_observation=EMPIRICAL,
            )
        )
    specs = {}
    from domain_facet_fixtures import _claim_of

    for letter in ("a", "b", "c"):
        claim = _claim_of(OTHER_CLAIM_FACET if letter == "c" else CLAIM_FACET)
        e = typed_estimand(claim=claim) if letter == "c" else matched_estimand
        inputs = (SpecInput("observes", _address(letter), "observation"),)
        if reads and letter == "a":
            inputs += (SpecInput("reads", _address("e"), "literature-extraction"),)
        spec = frozen_fixture_spec(
            OTHER_PROPOSITION_REF if letter == "c" else proposition_ref,
            inputs,
            estimand=e,
            claim=claim,
            profile=PROFILE,
        )
        specs[letter] = spec
        held_ids = {n.id for n in nodes}
        nodes.extend(MEASUREMENT_RECORDS.read(d.id) for d in spec.assessed_target.dependencies if d.id not in held_ids)
        nodes.append(stored.analysis_spec_node(spec))
        nodes.append(
            stored.dataset_node(
                title=f"d-{letter}",
                resources=_resources(letter),
                empirical_observation=EMPIRICAL,
            )
        )
        nodes.append(
            stored.run_node(
                f"run-{letter}",
                title=f"run-{letter}",
                spec=spec.identity,
                observes=[_address(letter)],
                # A `reads` input on `run-a` only: `run_value` hands out its
                # declaration for every role, and the resolver traces none but
                # `observes`.
                reads=[_address("e")] if reads and letter == "a" else [],
            )
        )

    assessments = [
        stored.assessment_node(
            "a-1",
            title="a-1",
            spec=specs["a"].identity,
            run="run:run-a",
            proposition=proposition_ref,
            outcome="supported",
            interpretation_rule=specs["a"].interpretation_rule,
            target=specs["a"].assessed_target,
        ),
        stored.assessment_node(
            "a-2",
            title="a-2",
            spec=specs["b"].identity,
            run="run:run-b",
            proposition=proposition_ref,
            outcome="supported",
            interpretation_rule=specs["b"].interpretation_rule,
            target=specs["b"].assessed_target,
        ),
        # The unrelated one: its own proposition, run, dataset and verification.
        stored.assessment_node(
            "a-3",
            title="a-3",
            spec=specs["c"].identity,
            run="run:run-c",
            proposition=OTHER_PROPOSITION_REF,
            outcome="refuted",
            interpretation_rule=specs["c"].interpretation_rule,
            target=specs["c"].assessed_target,
        ),
    ]
    if estimand is not None:
        if isinstance(corpus, CorpusWriter):
            raise AssertionError("an estimand naming another claim is raw corruption")
        for index, letter in enumerate(("a", "b")):
            assessments[index].facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(
                {**target_projection(replace(specs[letter].assessed_target, estimand=estimand))}
            ).decode()
            stored.stamp_semantic_identity(assessments[index])
    if assesses_target is not None:
        # A raw write nothing downstream checks: the facet still says
        # `proposition_ref`, so `assessment_value` matches, but the `assesses`
        # edge points somewhere else entirely.
        assessments[:2] = [
            stored.stamp_semantic_identity(
                node.model_copy(
                    update={
                        "relations": [
                            Relation(source=node.id, predicate=stored.ASSESSES, target=assesses_target),
                            *(r for r in node.relations if r.predicate != stored.ASSESSES),
                        ]
                    }
                )
            )
            for node in assessments[:2]
        ]

    if assesses_target is not None and isinstance(corpus, CorpusWriter):
        raise AssertionError("the divergent `assesses` edge is a raw write; it has no add path")
    values = {node.id: stored.assessment_value(node, profile=PROFILE) for node in assessments}
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

    root = corpus.root if isinstance(corpus, CorpusWriter) else corpus
    for node in nodes:
        if isinstance(corpus, CorpusWriter):
            corpus.add(node)
        else:
            raw_write(root, node)
    return reopen(root), values


def seed_assessed_proposition(writer, proposition_ref: str, *, slug: str, outcome: str = "supported", **typed) -> str:
    """Mint one admissible assessment of `proposition_ref` through the writer:
    dataset `d-a` (address `_address("a")`, resources `_resources("a")`), an
    observing run, the assessment, and a passed clean-environment
    verification. Returns the dataset address. `typed` carries the estimand
    lane's `estimand=` and `applicability=` values."""
    from fixtures_cut3 import MEASUREMENT_RECORDS, typed_applicability, typed_target

    if "target" not in typed:
        typed = {
            "target": typed_target(
                estimand=typed["estimand"], applicability=typed_applicability(typed.get("applicability", {}))
            )
        }
    for dependency in typed["target"].dependencies:
        if not writer.read_view.holds(dependency.id):
            writer.add(MEASUREMENT_RECORDS.read(dependency.id))
    address = _address("a")
    if not writer.read_view.holds(address):
        writer.add(stored.dataset_node(title="d-a", resources=_resources("a"), empirical_observation=EMPIRICAL))
    from fixtures_cut3 import ESTIMATOR_PROCEDURE, spec_draft, spec_rules

    from beliefs.decode import claim_from_stored
    from beliefs.spec import freeze

    claim, _ = claim_from_stored(
        writer.read_view.get(proposition_ref), profile=writer.profile, snapshot=build_snapshot(readable={})
    )
    from beliefs.procedure import procedure_from_stored

    estimator = ESTIMATOR_PROCEDURE
    if "testing/estimator" not in writer.profile.procedure_kinds:
        declaration = procedure_from_stored(MEASUREMENT_RECORDS.read(ESTIMATOR_PROCEDURE))
        estimator = MEASUREMENT_RECORDS.put_procedure(
            replace(
                declaration, kind=next(k for k, v in writer.profile.procedure_kinds.items() if not v.fills_within_model)
            )
        )
    frozen = freeze(
        spec_draft(
            target=proposition_ref,
            estimand=typed["target"].estimand,
            applicability=typed["target"].applicability,
            input_roles=(SpecInput("observes", address, "observation"),),
        ),
        held_rules=spec_rules(),
        profile=writer.profile,
        claim=claim,
        records=MEASUREMENT_RECORDS,
        rule_procedures={"median-difference/v1": estimator},
    )
    for dependency in frozen.assessed_target.dependencies:
        if not writer.read_view.holds(dependency.id):
            writer.add(MEASUREMENT_RECORDS.read(dependency.id))
    spec_node = stored.analysis_spec_node(frozen)
    if not writer.read_view.holds(spec_node.id):
        writer.add(spec_node)
    typed = {"target": frozen.assessed_target}
    run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=frozen.identity, observes=[address]))
    assessment = writer.add(
        stored.assessment_node(
            slug,
            title=slug,
            spec=frozen.identity,
            run=run.id,
            proposition=proposition_ref,
            outcome=outcome,
            interpretation_rule=frozen.interpretation_rule,
            target=frozen.assessed_target,
        )
    )
    value = stored.assessment_value(writer.read_view.get(assessment.id), profile=writer.profile)
    writer.add(
        stored.verification_node(
            f"v-{slug}",
            title=slug,
            assessment=value.identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        )
    )
    return address


def _fixture(
    corpus: Path | CorpusWriter,
    proposition_ref: str,
    *,
    reads: bool = False,
    assesses_target: str | None = None,
    estimand: Estimand | None = None,
) -> CorpusFixture:
    if isinstance(corpus, Path):
        corpus.mkdir(parents=True, exist_ok=True)
        from domain_facet_fixtures import LOCAL_CORPUS_ID

        from beliefs.world import registry

        (corpus / "corpus.yaml").write_bytes(
            registry.manifest_bytes(registry.CorpusManifest(2, LOCAL_CORPUS_ID, pins_for(PROFILE)))
        )
    view, values = _seed(corpus, proposition_ref, reads=reads, assesses_target=assesses_target, estimand=estimand)
    matched = (values["assessment:a-1"], values["assessment:a-2"])
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, (_address("a"), _address("b"))),
        producer_snapshot_identity="producer-snapshot-1",
        node_corpus={value.identity(): ("c1",) for value in values.values()},
        pins={"c1": pins_for(PROFILE)},
    )
    return CorpusFixture(
        view=view,
        proposition=proposition_ref,
        availability=Availability(
            # A `reads` input must be held too: `admit` quantifies heldness
            # over every input role, not just the eligibility-conferring one.
            observations=_observations("a", "b", "e") if reads else _observations("a", "b"),
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


@pytest.fixture()
def divergent_fixture(tmp_path) -> CorpusFixture:
    """The corpus with the matched assessments' `assesses` edges pointing at
    `proposition:q` while their facets still say `proposition:p` — a raw write
    nothing in the read path reconciles."""
    return _fixture(tmp_path, PROPOSITION_REF, assesses_target=OTHER_PROPOSITION_REF)


# --- the rows --------------------------------------------------------------


def test_evaluate_over_is_the_corpus_backed_path_and_yields_a_belief(corpus_fixture):
    from domain_facet_fixtures import over_kwargs

    result = evaluate_over(corpus_fixture.view, corpus_fixture.proposition, **over_kwargs(corpus_fixture.kwargs))
    assert isinstance(result, Belief)
    assert result.value == 2  # two independent supports, as test_belief's scenario publishes


def test_evaluate_over_maps_a_profile_pin_mismatch_to_refused(corpus_fixture):
    from domain_facet_fixtures import over_kwargs

    context = replace(
        corpus_fixture.context,
        pins={"c1": replace(pins_for(PROFILE), science_contract="science:" + "0" * 64)},
    )
    result = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **over_kwargs({**corpus_fixture.kwargs, "context": context}),
    )
    assert isinstance(result, Refused)
    assert result.reason.startswith("profile-pin-mismatch: science")


def test_the_restored_claim_is_the_one_the_proposition_node_carries(corpus_fixture):
    from domain_facet_fixtures import over_kwargs

    inputs = gather(
        corpus_fixture.view,
        corpus_fixture.proposition,
        key=only_assessed_key(
            corpus_fixture.view,
            corpus_fixture.proposition,
            profile=(over_kwargs(corpus_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(corpus_fixture.gather_kwargs),
    )
    assert inputs.claim is not None
    # π_claim accepts it — the brand chain survived the restore — and it
    # projects back to exactly the facet the stored proposition carries.
    assert project_claim(inputs.claim) == CLAIM_FACET
    # And it is the *same* claim `test_belief` builds through `build_claim`,
    # restored from stored bytes rather than constructed.
    assert claim_identity(inputs.claim) == claim_identity(EXPECTED_CLAIM)
    assert inputs.consulted == tuple(
        sorted((("science", pins_for(PROFILE).science_contract), ("testing", pins_for(PROFILE).domains["testing"])))
    )


def test_every_read_through_the_resolver_is_inside_the_declared_closure(corpus_fixture):
    from domain_facet_fixtures import over_kwargs

    inputs = gather(
        corpus_fixture.view,
        corpus_fixture.proposition,
        key=only_assessed_key(
            corpus_fixture.view,
            corpus_fixture.proposition,
            profile=(over_kwargs(corpus_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(corpus_fixture.gather_kwargs),
    )
    assert set(inputs.read_trace) <= inputs.declared_refs()
    assert {kind for kind, _ in inputs.read_trace} == {
        "assessment",
        "proposition",
        "run",
        "verification",
        "dataset",
        "procedure",
    }
    assert {kind for kind, _ in inputs.read_trace} <= set(READ_KINDS)
    answer = evaluate(
        key=inputs.key,
        dependencies=inputs.dependencies,
        proposition=corpus_fixture.proposition,
        records=inputs.records(),
        availability=corpus_fixture.availability,
        context=corpus_fixture.context,
        retractions=inputs.retractions,
        binding=corpus_fixture.binding,
        profile=PROFILE,
    )
    assert isinstance(answer, Belief)
    assert inputs.closure().digest() == answer.belief_input_digest


def test_the_records_are_already_proposition_scoped(corpus_fixture):
    from domain_facet_fixtures import over_kwargs

    inputs = gather(
        corpus_fixture.view,
        corpus_fixture.proposition,
        key=only_assessed_key(
            corpus_fixture.view,
            corpus_fixture.proposition,
            profile=(over_kwargs(corpus_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(corpus_fixture.gather_kwargs),
    )
    assert all(a.proposition == corpus_fixture.proposition for a in inputs.assessments)
    assert {a.identity() for a in inputs.assessments} == {a.identity() for a in corpus_fixture.assessments}
    assert set(inputs.runs) == {a.run for a in inputs.assessments}
    assert all(v.assessment in {a.identity() for a in inputs.assessments} for v in inputs.verifications)
    records = inputs.records()
    assert records.assessments == inputs.assessments
    assert set(records.claims) == {corpus_fixture.proposition}
    assert records.source_assertions == ()


def test_an_unrelated_verification_read_fails_containment(corpus_fixture, monkeypatch):
    from domain_facet_fixtures import over_kwargs

    """A deliberately wrong read: `gather` reads one verification belonging to a
    different proposition; the digest is unchanged and the check fails."""
    from beliefs import evaluation

    corpus_fixture = replace(corpus_fixture, view=corpus_fixture.view.captured())
    honest = gather(
        corpus_fixture.view,
        corpus_fixture.proposition,
        key=only_assessed_key(
            corpus_fixture.view,
            corpus_fixture.proposition,
            profile=(over_kwargs(corpus_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(corpus_fixture.gather_kwargs),
    )
    monkeypatch.setattr(evaluation, "_verification_selected", lambda value, ids: True)
    resolve = corpus_fixture.view.resolve
    monkeypatch.setattr(
        corpus_fixture.view, "resolve", lambda ref: "assessment:a-1" if ref == "assessment:a-3" else resolve(ref)
    )
    leaky = gather(
        corpus_fixture.view,
        corpus_fixture.proposition,
        key=only_assessed_key(
            corpus_fixture.view,
            corpus_fixture.proposition,
            profile=(over_kwargs(corpus_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(corpus_fixture.gather_kwargs),
    )

    assert {v.ref for v in leaky.verifications} > {v.ref for v in honest.verifications}
    assert leaky.closure().digest() == honest.closure().digest()
    assert set(honest.read_trace) <= honest.declared_refs()
    assert not set(leaky.read_trace) <= leaky.declared_refs()


def test_the_binding_is_guarded_before_any_read(corpus_fixture, monkeypatch):
    from domain_facet_fixtures import over_kwargs

    from beliefs import evaluation

    monkeypatch.setattr(evaluation, "_gather", lambda *a, **k: pytest.fail("read before the binding was refused"))
    result = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **over_kwargs({**corpus_fixture.kwargs, "binding": ("rule", "impl")}),
    )
    assert isinstance(result, Refused) and result.reason.startswith("binding-not-exact")


def test_a_proposition_with_no_claim_record_still_reaches_its_assessments_estimand(claimless_fixture):
    # The claim schema contributes nothing here (no claim resolves), but the
    # estimand walk is unconditional on that: each matched assessment still
    # carries a typed estimand under `testing/affects`, so `testing` is
    # consulted through it alone.
    from domain_facet_fixtures import over_kwargs

    inputs = gather(
        claimless_fixture.view,
        claimless_fixture.proposition,
        key=only_assessed_key(
            claimless_fixture.view,
            claimless_fixture.proposition,
            profile=(over_kwargs(claimless_fixture.gather_kwargs))["profile"],
        ),
        observations={},
        **over_kwargs(claimless_fixture.gather_kwargs),
    )
    assert inputs.claim is None
    assert dict(inputs.records().claims) == {}
    assert inputs.consulted == (
        ("science", pins_for(PROFILE).science_contract),
        ("testing", pins_for(PROFILE).domains["testing"]),
    )
    assert "proposition" not in {kind for kind, _ in inputs.read_trace}
    assert set(inputs.read_trace) <= inputs.declared_refs()


def test_assessment_estimand_naming_another_claim_is_malformed(tmp_path):
    """Round-9 review (ruling P5). Proposition `P` holds typed claim `C`; its
    two matched assessments name `P` by their `assesses` edge and their
    `proposition` field, and carry a shape-valid estimand built for another
    claim, so its claimed identity is `D`, not `I(C)`. `gather` pairs each
    estimand with the claim of its assessment's target itself, and admission
    judges `D` against that claim: the read refuses with `MalformedRecord`,
    never answering with a consulted set reduced to what `D` could reach."""

    from domain_facet_fixtures import over_kwargs

    from beliefs.claim import Referent, build_claim
    from beliefs.errors import MalformedRecord

    other_claim = build_claim(
        PROFILE,
        operator="testing/affects",
        roles={"cause": Referent("testing/entity", OTHER_GENE), "effect": Referent("testing/outcome", PHENO)},
        layer="causal",
        polarity="positive",
    )
    foreign = typed_estimand(profile=PROFILE, claim=other_claim)
    held_claim = claim_identity(EXPECTED_CLAIM)
    assert project_claim(EXPECTED_CLAIM) == CLAIM_FACET
    assert foreign.claim == claim_identity(other_claim) != held_claim

    fixture = _fixture(tmp_path, PROPOSITION_REF, estimand=foreign)
    # The stored records carry the pairing, and the test supplies none: each
    # matched assessment names `P` both ways and holds the foreign estimand.
    for value in fixture.assessments:
        assert value.proposition == PROPOSITION_REF and value.estimand.claim == foreign.claim
    for ref in ("assessment:a-1", "assessment:a-2"):
        assert [r.target for r in fixture.view.get(ref).relations if r.predicate == stored.ASSESSES] == [
            PROPOSITION_REF
        ]

    with pytest.raises(MalformedRecord, match="not admitted for the claim of the proposition it targets") as caught:
        gather(
            fixture.view,
            fixture.proposition,
            key=only_assessed_key(
                fixture.view, fixture.proposition, profile=(over_kwargs(fixture.gather_kwargs))["profile"]
            ),
            observations={},
            **over_kwargs(fixture.gather_kwargs),
        )
    assert "different claim" in str(caught.value)


def test_a_divergent_assesses_edge_is_selected_before_decode(divergent_fixture):
    from beliefs.errors import MalformedRecord

    inputs = gather(
        divergent_fixture.view,
        divergent_fixture.proposition,
        key=only_assessed_key(
            divergent_fixture.view, divergent_fixture.proposition, profile=(divergent_fixture.gather_kwargs)["profile"]
        ),
        observations={},
        **divergent_fixture.gather_kwargs,
    )
    assert inputs.assessments == () and inputs.claim is None
    assert not any(kind == "assessment" for kind, _ in inputs.read_trace)
    with pytest.raises(MalformedRecord, match="assesses edge"):
        gather(
            divergent_fixture.view,
            OTHER_PROPOSITION_REF,
            key=divergent_fixture.assessments[0].key(),
            observations={},
            **divergent_fixture.gather_kwargs,
        )


def test_a_reads_input_declaration_crosses_gather_untraced(tmp_path):
    from domain_facet_fixtures import over_kwargs

    """The second bound, pinned rather than hidden: `run_value` hands out the
    declaration of every input role, and the resolver traces only `observes` —
    because the closure declares dataset refs only under `observes` and
    consumes no other role's declaration. Tracing one would record a read the
    digest cannot move for."""
    fixture = _fixture(tmp_path, PROPOSITION_REF, reads=True)
    inputs = gather(
        fixture.view,
        fixture.proposition,
        key=only_assessed_key(
            fixture.view, fixture.proposition, profile=(over_kwargs(fixture.gather_kwargs))["profile"]
        ),
        observations={},
        **over_kwargs(fixture.gather_kwargs),
    )
    run_a = inputs.runs["run-a"]
    assert {i.role for i in run_a.inputs} == {"observes", "reads"}
    assert ("dataset", _address("e")) not in inputs.read_trace
    assert set(inputs.read_trace) <= inputs.declared_refs()
    # Change only a reads declaration's resource name. Its content address and
    # the frozen input/mode stay fixed; authoring another spec would change identity.
    node = fixture.view.get(_address("e"))
    node.facets[stored.DATASET_FACET]["resources"][0]["name"] = "renamed auxiliary"
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    changed = gather(
        reopen(tmp_path),
        fixture.proposition,
        key=only_assessed_key(
            reopen(tmp_path), fixture.proposition, profile=(over_kwargs(fixture.gather_kwargs))["profile"]
        ),
        observations={},
        **over_kwargs(fixture.gather_kwargs),
    )
    assert inputs.runs["run-a"] != changed.runs["run-a"]
    assert inputs.closure().digest() == changed.closure().digest()


def test_the_no_belief_and_refused_arms_still_gather_and_assert_no_containment(corpus_fixture, monkeypatch):
    from domain_facet_fixtures import over_kwargs

    """The closure exists whenever a belief is produced; `NoBelief` and
    `Refused` commit no input closure, so there is nothing on those arms for a
    read to be contained in. `gather` still runs — the only guard before it is
    the binding's."""
    from beliefs import evaluation

    calls: list[str] = []
    real = evaluation._gather
    monkeypatch.setattr(evaluation, "_gather", lambda *a, **k: (calls.append("gathered"), real(*a, **k))[1])

    no_belief = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **over_kwargs({**corpus_fixture.kwargs, "availability": replace(corpus_fixture.availability, fixtures={})}),
    )
    assert isinstance(no_belief, NoBelief) and no_belief.reason == "unavailable-fixtures-unheld"

    broken = PolicyImplementation(identity=BELIEF_V1.identity, aggregate=lambda problem: 999)
    refused = evaluate_over(
        corpus_fixture.view,
        corpus_fixture.proposition,
        **over_kwargs(
            {
                **corpus_fixture.kwargs,
                "availability": replace(corpus_fixture.availability, implementations={BELIEF_V1.identity: broken}),
            }
        ),
    )
    assert isinstance(refused, Refused) and refused.reason.startswith("implementation-fails-fixtures")

    assert calls == ["gathered", "gathered"], "the guard is on the Belief arm only; gather ran on both"


def test_the_closure_fields_are_build_closure_s_keywords_in_order():
    import inspect

    from beliefs.closure import build_closure

    parameters = inspect.signature(build_closure).parameters
    required = [name for name, parameter in parameters.items() if parameter.default is inspect.Parameter.empty]
    expected = [
        "proposition",
        "key",
        "dependencies",
        "assessments",
        "runs",
        "verifications",
        "snapshot",
        "producer_snapshot_identity",
        "retractions",
        "consulted",
        "binding",
        "observed_facets",
    ]
    assert required == expected
    assert [f.name for f in dataclasses.fields(EvaluationInputs) if f.name in required] == expected
    assert set(parameters) - set(required) == {"acceptance_statement"}
    assert "acceptance" in {f.name for f in dataclasses.fields(EvaluationInputs)}


from test_verify import production_pair  # noqa: F401 - the module-scoped fixture the test resolves


def test_gather_never_selects_a_production_verification(production_pair, request, tmp_path):  # noqa: F811
    from authority import FULL
    from domain_facet_fixtures import over_kwargs
    from nodes.core.write_plan import DefaultExecutor
    from test_verify import _production_verification

    from beliefs.corpus import CorpusWriter
    from beliefs.verify import publication_node

    mark = request.node.get_closest_marker("xdist_group")
    assert mark is not None and mark.args == ("tests/test_evaluation.py",)
    production = _production_verification(production_pair)
    writer = CorpusWriter(tmp_path / "corpus", DefaultExecutor, authority=FULL, profile=PROFILE)
    writer.adopt_manifest(profile=pins_for(PROFILE))
    node = writer.add(publication_node(production))
    fixture = _fixture(writer, PROPOSITION_REF)
    inputs = gather(
        fixture.view,
        PROPOSITION_REF,
        key=only_assessed_key(fixture.view, PROPOSITION_REF, profile=(over_kwargs(fixture.gather_kwargs))["profile"]),
        observations={},
        **over_kwargs(fixture.gather_kwargs),
    )
    assert node.id not in {v.ref for v in inputs.verifications}


def test_evaluate_over_is_the_first_projection_of_evaluate_over_traced(corpus_fixture, claimless_fixture):
    from domain_facet_fixtures import over_kwargs

    from beliefs.belief import Reached
    from beliefs.evaluation import evaluate_over_traced

    # The other tests carry the proof that the first projection is the answer; this pins only that the tuple's first member is what `evaluate` returns.
    for fixture in (corpus_fixture, claimless_fixture):
        answer, admission = evaluate_over_traced(fixture.view, fixture.proposition, **over_kwargs(fixture.kwargs))
        assert evaluate_over(fixture.view, fixture.proposition, **over_kwargs(fixture.kwargs)) == answer
        if isinstance(answer, Belief):
            assert isinstance(admission, Reached) and admission.admitted == {a.identity() for a in fixture.assessments}
