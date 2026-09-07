"""Shared builders for cut 21's arms (verification-publication design §8).

The run pair is synthetic and conforming — `fixtures_cut3.closure_with` with a
one-job plan — and the replay carries a qualifying confined receipt bound to
the recipe's environment identity, so `derive_scope` reaches
`clean-environment` with no engine (`test_replay.py`'s R4 arms do the same
over real runs). Every V arm that needs admission builds on it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from authority import ACTOR
from confinement_fixtures import confined_receipt, instance
from fixtures_cut3 import closure_with, planned, spec_draft, spec_rules, traced
from fixtures_cut4 import raw_write
from nodes.core.node import Node
from nodes.core.relations import Relation
from test_belief import PROFILE
from test_evaluation import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO

from beliefs import runrecord, stored
from beliefs.admission import admit
from beliefs.assess import build_assessment
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.corpus import lineage_snapshot
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.evaluation import evaluate_over, gather
from beliefs.evidence import DerivationEvidence
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.recipe import RunClosure, job_key
from beliefs.record import AssessmentValue
from beliefs.replay import CONTENT_EQUALITY, CodeLineageCertification
from beliefs.resolution import build_snapshot
from beliefs.runrecord import run_ref
from beliefs.spec import FrozenSpec, freeze
from beliefs.verify import AssessmentVerification, build_verification

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]
CONTRACT = "science:" + "c" * 64
EPOCH = "epoch:" + "e" * 64
BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)
DISAGREEING = (("out.txt", "sha256:" + "d" * 64),)
_PARTS = {
    "trace": (traced("fit", {"n": "a"}),),
    "planned": (planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),),
    "target_keys": (job_key("fit", (("n", "a"),)),),
    "targets": ("outputs/a.done",),
}
__all__ = ["CLAIM_FACET", "PROFILE", "EX", "GENE", "OTHER_GENE", "PHENO"]  # re-exported for the acceptance module  # noqa: RUF022


def frozen_for(target: str) -> FrozenSpec:
    """The spec's target is the proposition's corpus ref, as the reproduction
    set it: the stored assessment's `proposition` and the derived one then
    spell the same string (design §9 names the two namespaces)."""
    return freeze(spec_draft(target=target), held_rules=spec_rules())


def conforming_closure(frozen: FrozenSpec, *, token: str, confined: bool = False, outputs=None) -> RunClosure:
    base = closure_with(**_PARTS) if outputs is None else closure_with(**_PARTS, outputs=outputs)
    recipe = replace(base.recipe, spec_identity=frozen.identity, rule_bindings=frozen.rule_bindings)
    occurrence = replace(base.occurrence, event_token=token, actor=ACTOR)
    if confined:
        receipt = confined_receipt(instance=instance(environment_identity=recipe.environment.identity()))
        occurrence = replace(occurrence, receipt=receipt)
    return RunClosure(recipe=recipe, result=base.result, occurrence=occurrence)


def clean_pair(frozen: FrozenSpec, *, agreeing: bool = True, qualifying: bool = True) -> tuple[RunClosure, RunClosure]:
    """`qualifying=False` leaves the replay's receipt unconfined: the pair
    then derives `same-environment`, which is what a forged
    `clean-environment` over it must be caught against (V4)."""
    original = conforming_closure(frozen, token="tok-original")
    replayed = conforming_closure(frozen, token="tok-replayed", confined=qualifying, outputs=None if agreeing else DISAGREEING)
    return original, replayed


def evidence_for(frozen: FrozenSpec) -> DerivationEvidence:
    rules = spec_rules()
    interpretation = rules[frozen.interpretation_rule]
    return DerivationEvidence(
        specs={frozen.identity: frozen},
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        implementations={interpretation.identity: interpretation},
    )


def run_record(closure: RunClosure) -> Node:
    return stored.run_publication_node(
        closure.address(),
        title="assessment run",
        projection=runrecord.projection_text(closure).decode("utf-8"),
        spec=closure.recipe.spec_identity,
        observes=tuple(e.dataset for e in closure.recipe.inputs if e.role == "observes"),
        reads=tuple(e.dataset for e in closure.recipe.inputs if e.role == "reads"),
    )


def mint_datasets(writer, closure: RunClosure) -> None:
    for entry in closure.recipe.inputs:
        if not writer.read_view.holds(entry.dataset):
            writer.add(
                stored.dataset_node(
                    entry.dataset.removeprefix("dataset:"), title="raw", resources=PINNED,
                    empirical_observation={"locator": "instrument:fixture", "attested_by": writer.authority.actor},
                )
            )


@dataclass(frozen=True)
class Published:
    frozen: FrozenSpec
    original: RunClosure
    replayed: RunClosure
    proposition: Node
    assessment: Node
    derived_value: AssessmentValue
    derived: AssessmentVerification
    evidence: DerivationEvidence
    node: Node | None


def publish_corpus(
    writer, *, slug: str = "p", claim=None, certification: CodeLineageCertification | None = None,
    agreeing: bool = True, qualifying: bool = True, publish: bool = False,
) -> Published:
    """A proposition, the two runs and their datasets, the stored assessment
    over the original, the verification derived from the pair, and — with
    `publish` — its record through `writer.add`."""
    proposition = writer.add(stored.proposition_node(slug, title=slug, claim=claim or {"operator": "affects"}))
    frozen = frozen_for(proposition.id)
    original, replayed = clean_pair(frozen, agreeing=agreeing, qualifying=qualifying)
    mint_datasets(writer, original)
    writer.add(run_record(original))
    writer.add(run_record(replayed))
    evidence = evidence_for(frozen)
    derived_value = build_assessment(original, specs=evidence.specs, implementations=evidence.implementations)
    assert isinstance(derived_value, AssessmentValue), derived_value
    optional = {n: getattr(derived_value, n) for n in ("estimate", "uncertainty", "estimand", "applicability") if getattr(derived_value, n) is not None}
    assessment = writer.add(
        stored.assessment_node(
            f"a-{slug}", title=f"a-{slug}", spec=frozen.identity, run=run_ref(original.address()), proposition=proposition.id,
            outcome=derived_value.outcome, interpretation_rule=derived_value.interpretation_rule, **optional,
        )
    )
    derived = build_verification(
        original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
        contract_identity=CONTRACT, epoch=EPOCH, certification=certification,
    )
    assert isinstance(derived, AssessmentVerification)
    node = None
    if publish:
        from beliefs.verify import publication_node

        node = writer.add(publication_node(derived, assessment_ref=assessment.id))
    return Published(frozen, original, replayed, proposition, assessment, derived_value, derived, evidence, node)


def observations_for(view) -> dict[str, tuple[ByteObservation, ...]]:
    """One observation per held dataset at its declared digest, so `admit`
    reads every input as Held."""
    observations: dict[str, tuple[ByteObservation, ...]] = {}
    for node in view.iter_stored():
        if node.kind != "dataset":
            continue
        declaration = stored.dataset_declaration(node)
        address = dataset_address(declaration)
        if address is not None:
            observations[address] = tuple(
                ByteObservation(digest=r.digest, location="repo://data") for r in declaration.resources if r.digest
            )
    return observations


def evaluation_kwargs(view) -> dict:
    identities = {stored.assessment_value(n).identity() for n in view.iter_stored() if n.kind == "assessment"}
    observations = observations_for(view)
    return {
        "availability": Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES}),
        "context": SuppliedContext(
            snapshot=lineage_snapshot(view, [n.id for n in view.iter_stored() if n.kind == "dataset"]),  # corpus refs, not content addresses [R2, second round]
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={identity: "c1" for identity in identities},
            pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
        ),
        "profile": PROFILE,
        "resolution": build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        "binding": BINDING,
    }


def admission_over(writer, proposition_ref: str, original: RunClosure):
    """`gather` -> `admit` -> `evaluate_over` over the corpus as it stands. The
    assessment admitted is *an* assessment over `original`: two records may
    carry one identity (design decision 17) and the gate is over the identity. [R5]"""
    view = writer.read_view
    kwargs = evaluation_kwargs(view)
    gathered = {k: v for k, v in kwargs.items() if k != "availability"}
    inputs = gather(view, proposition_ref, **gathered)
    a = next(a for a in inputs.assessments if a.run == original.address())
    verdict = admit(a, inputs.runs[a.run], kwargs["availability"].observations, inputs.verifications)
    return verdict, evaluate_over(view, proposition_ref, **kwargs)


def self_consistent_forgery(writer, node: Node, *, mutate) -> Node:
    """V4's fixture (design decision 16): alter a member, then recompute the
    id, the relation source and the stamp from the altered members, so the
    record decodes and only the derivation recomputation can catch it. Written
    behind the boundary on purpose. The identity is computed through the
    reader's own basis helper — no constructor is opened for it."""
    from beliefs.verify import RUN_VERIFICATION_DOMAIN, _basis, _restore_report

    facet = {k: (dict(v) if isinstance(v, dict) else v) for k, v in node.facets[stored.VERIFICATION_FACET].items()}
    mutate(facet)
    members: dict[str, object] = {
        "original": stored.local_id("run", facet["derivation"]["original"]),
        "replayed": stored.local_id("run", facet["derivation"]["replayed"]),
        "rule": facet["rule"],
        "report": _restore_report(node.id, facet["report"]),
        "scope_rule": facet["scope_rule"],
        "scope": facet["scope"],
        "verdict": facet["verdict"],
        # facet's value type is Unknown here (raw dict payload); local_id's own
        # runtime check is what actually refuses a non-string, so this is a
        # type-checker note, not a coercion.
        "supersedes": None if "supersedes" not in facet else stored.local_id("verification", facet["supersedes"]),  # type: ignore[arg-type]
    }
    if "assessment" in facet:
        members["assessment"] = facet["assessment"]
    forged_id = f"verification:{v1.digest(RUN_VERIFICATION_DOMAIN, _basis(members))}"
    forged = stored.stamp_semantic_identity(
        Node(
            id=forged_id, kind="verification", title=node.title, facets={stored.VERIFICATION_FACET: facet},
            relations=[Relation(source=forged_id, predicate=r.predicate, target=r.target) for r in node.relations],
        )
    )
    raw_write(writer.root, forged)
    return forged


def forgeries(writer, published: Published) -> list[tuple[Node, type[Exception], str]]:
    """V5's five: a stale id, a forged report, a missing edge, a target that
    resolves nowhere, and a target carrying another identity — each with the
    refusal type and the substring its message carries. The helper records
    they need are minted through `writer` first, so a caller takes its
    baseline after this returns. [R8]"""
    from beliefs.errors import MalformedRecord, VerificationTargetMismatch
    from beliefs.verify import publication_node

    derived, assessment = published.derived, published.assessment
    good = publication_node(derived, assessment_ref=assessment.id)
    stale_id = good.model_copy(update={"id": "verification:" + "f" * 64})
    stale_id.relations = [Relation(source=stale_id.id, predicate=r.predicate, target=r.target) for r in good.relations]
    stored.stamp_semantic_identity(stale_id)
    bad_report = good.model_copy(deep=True)
    bad_report.facets[stored.VERIFICATION_FACET]["report"]["diagnostics"] = ["forged"]
    stored.stamp_semantic_identity(bad_report)
    no_edge = good.model_copy(deep=True, update={"relations": []})
    stored.stamp_semantic_identity(no_edge)
    wrong_target = publication_node(derived, assessment_ref="assessment:absent")
    other_proposition = writer.add(stored.proposition_node("p-other", title="p-other", claim={"operator": "affects"}))
    # Spelled from the same derived value as the real assessment, optionals included,
    # so it audits clean and imports; only its proposition differs, which the audit's
    # comparison excludes (cut 18 ruling R12). Its identity differs by that member.
    value = published.derived_value
    optional = {n: getattr(value, n) for n in ("estimate", "uncertainty", "estimand", "applicability") if getattr(value, n) is not None}
    other = writer.add(
        stored.assessment_node(
            "a-other", title="a-other", spec=published.frozen.identity, run=run_ref(published.original.address()),
            proposition=other_proposition.id, outcome=value.outcome, interpretation_rule=value.interpretation_rule, **optional,
        )
    )
    other_identity = publication_node(derived, assessment_ref=other.id)
    return [
        (stale_id, MalformedRecord, "recomputed identity"),
        (bad_report, MalformedRecord, "recomputed identity"),
        (no_edge, MalformedRecord, "present together"),
        (wrong_target, VerificationTargetMismatch, "resolves to no record"),
        (other_identity, VerificationTargetMismatch, "carries assessment identity"),
    ]
