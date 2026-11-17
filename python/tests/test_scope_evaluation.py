"""Key-local scope validity in captured belief evaluation and its pure replay.

Scope containment design §§7.3–7.4; acceptance cases C10–C14 and C17 for keyed
and nested evaluation. Pair comparison context is test_scope_pairs.py's.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from domain_facet_fixtures import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO, _claim_of
from fixtures_cut3 import spec_draft, spec_rules
from fixtures_cut4 import raw_write, reopen
from profiles import pins_for
from scope_fixtures import endpoint_document, relation, relations_document
from test_evaluation import EMPIRICAL, _address, _observations, _resources
from test_scope_validity import World, _procedure

from beliefs import errors, stored
from beliefs.belief import Availability, Belief, NoBelief, Reached, SuppliedContext, evaluate_traced
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.corpus import lineage_snapshot, run_value
from beliefs.eligibility import (
    AssessmentEligibilityReader,
    ClosureEligibility,
    Eligible,
    Ineligible,
    merge_scope_eligibility,
)
from beliefs.evaluation import _evaluate_claim
from beliefs.evidence import DependencyEvidence
from beliefs.measurement import Observable
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.projection import claim_identity
from beliefs.resolution import build_snapshot
from beliefs.scope_checks import author_scope_reader
from beliefs.spec import SpecInput, freeze
from beliefs.target_comparison import TargetUnknown
from beliefs.target_validity import scope_eligibility

BASE = shipped_base_contract()
PROPOSITION = "proposition:p"
BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)
TERMS_DOCUMENT = {
    "contract": "scope-terms",
    "version": 1,
    "lineage": "genesis",
    "sorts": {},
    "dimensions": {},
    "quantity_kinds": {"abundance": {"dimension": "construct"}},
}
TERM_OBSERVABLE = Observable("scope-terms/abundance", "testing/entity")


def _parse(document, source):
    return parse_domain_contract(document, source=source, base=BASE, predecessor=None)


class Scene:
    """One proposition with a stale-able key (the World's rule-scoped estimand,
    whose waiver rests on R{a} < T{m} < S{x}) and an unaffected key (an
    unrestricted target over a universally validated procedure). Rule T reads an
    observable of a third namespace, so its body terms need their own pin."""

    def __init__(
        self,
        root: Path,
        *,
        shared_key: bool = False,
        failing: str = "",
        t_held: bool = True,
        rows=None,
        tamper: str = "",
    ):
        t_rule = ClassificationRule("testing/level", (TERM_OBSERVABLE,), "Rule T: intermediate.", None, None, None)
        self.world = world = World(t_rule=t_rule)
        self.universal = world.records.put(_procedure("Universal assay", {}))
        original = self.profile()
        self.claim = _claim_of(CLAIM_FACET)
        assert claim_identity(self.claim) == claim_identity(world_claim())
        stale = world.estimand(original)
        assert stale.assumptions == ()
        unaffected = world.estimand(original, procedure=self.universal, scope={})
        if rows is None:
            rows = [("a", stale, world.scope_values), ("c", unaffected, {})]
            if shared_key:
                rows.insert(1, ("b", stale, world.scope_values))
        else:
            rows = rows(self, original)
        root.mkdir(parents=True)
        from domain_facet_fixtures import LOCAL_CORPUS_ID

        from beliefs.world import registry

        (root / "corpus.yaml").write_bytes(
            registry.manifest_bytes(registry.CorpusManifest(2, LOCAL_CORPUS_ID, pins_for(original)))
        )
        nodes = [stored.proposition_node("p", title="p", claim=CLAIM_FACET)]
        nodes.extend(node for id, node in world.records.nodes.items() if t_held or id != world.t)
        self.values: dict[str, object] = {}
        self.letters = [letter for letter, _, _ in rows]
        for letter, estimand, scope in rows:
            applicability = world.applicability(original, values=scope)
            spec = freeze(
                spec_draft(
                    target=PROPOSITION,
                    estimand=estimand,
                    applicability=applicability,
                    input_roles=(SpecInput("observes", _address(letter), "observation"),),
                ),
                held_rules=spec_rules(),
                rule_procedures={"median-difference/v1": world.estimator},
                profile=original,
                claim=self.claim,
                records=world.records,
            )
            nodes.append(stored.analysis_spec_node(spec))
            target = spec.assessed_target
            if letter == tamper:
                # The stored target's entry for operand rule R disagrees with the held body:
                # a frozen-dependency mismatch on a rule that is also a selected scope root.
                target = replace(
                    target,
                    dependencies=tuple(
                        replace(entry, terms=tuple(sorted({*entry.terms, "testing/stage"})))
                        if entry.id == world.r
                        else entry
                        for entry in target.dependencies
                    ),
                )
            nodes.append(
                stored.dataset_node(title=f"d-{letter}", resources=_resources(letter), empirical_observation=EMPIRICAL)
            )
            nodes.append(
                stored.run_node(f"run-{letter}", title=letter, spec=spec.identity, observes=[_address(letter)])
            )
            node = stored.assessment_node(
                f"a-{letter}",
                title=letter,
                spec=spec.identity,
                run=f"run:run-{letter}",
                proposition=PROPOSITION,
                outcome="supported",
                interpretation_rule=spec.interpretation_rule,
                target=target,
            )
            value = stored.assessment_value(node, profile=original)
            self.values[letter] = value
            nodes.append(node)
            nodes.append(
                stored.verification_node(
                    f"v-{letter}",
                    title=letter,
                    assessment=value.identity(),
                    assessment_ref=node.id,
                    scope="clean-environment",
                    verdict="failed" if letter == failing else "passed",
                )
            )
        for node in nodes:
            raw_write(root, node)
        self.root = root

    def profile(self, *, retire: bool = False, editorial: bool = False, extra: dict | None = None):
        first, second = self.world.tables(retire_second=retire)
        documents = [
            relations_document(first, namespace="scope-relations"),
            relations_document(second, namespace="scope-relations-b"),
        ]
        if editorial:
            documents[1]["description"] = "Edited prose; no relation changes."
        if extra is not None:
            documents.append(relations_document(extra, namespace="scope-relations-c"))
        contracts = [_parse(endpoint_document(), "testing"), _parse(dict(TERMS_DOCUMENT), "scope-terms")]
        if retire:
            # A real lineage successor of the relation owner that retires its relation.
            genesis = _parse(relations_document(self.world.tables()[1], namespace="scope-relations-b"), "genesis")
            documents[1].update(version=2, lineage={"successor": genesis.content_identity})
            successor = parse_domain_contract(documents[1], source="successor", base=BASE, predecessor=genesis)
            contracts.extend([_parse(documents[0], "scope-relations"), successor])
            contracts.extend(_parse(document, document["contract"]) for document in documents[2:])
        else:
            contracts.extend(_parse(document, document["contract"]) for document in documents)
        return compile_profile(BASE, contracts)

    def key(self, letter: str) -> str:
        return self.values[letter].key()  # type: ignore[attr-defined]

    def identity(self, letter: str) -> str:
        return self.values[letter].identity()  # type: ignore[attr-defined]

    def context(self, profile, view):
        return SuppliedContext(
            snapshot=lineage_snapshot(view, tuple(_address(letter) for letter in self.letters)),
            producer_snapshot_identity="producer-snapshot-1",
            node_corpus={},
            pins={"c1": pins_for(profile)},
        )

    def availability(self):
        return Availability(
            observations=_observations(*self.letters),
            implementations={BELIEF_V1.identity: BELIEF_V1},
            fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
        )

    def evaluate(self, profile):
        view = reopen(self.root)
        return _evaluate_claim(
            view,
            PROPOSITION,
            availability=self.availability(),
            context=self.context(profile, view),
            profile=profile,
            resolution=build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
            binding=BINDING,
        )

    def replay(self, profile, key, *, dependencies=None, pins=None):
        """The pure evaluator over one key's captured inputs, optionally altered."""
        evaluation = self.evaluate(profile)
        inputs = evaluation.traces[key][2]
        assert inputs is not None
        context = replace(
            self.context(profile, reopen(self.root)),
            node_corpus=inputs.node_corpus,
            snapshot=inputs.snapshot,
            acceptance=inputs.acceptance,
        )
        if pins is not None:
            context = replace(context, pins=pins)
        return evaluate_traced(
            proposition=PROPOSITION,
            key=key,
            dependencies=inputs.dependencies if dependencies is None else dependencies,
            records=inputs.records(),
            availability=self.availability(),
            context=context,
            retractions=inputs.retractions,
            binding=BINDING,
            profile=profile,
        )[0]


def world_claim():
    from fixtures_cut3 import TESTING_CLAIM

    return TESTING_CLAIM


def _digest(answer) -> str:
    assert isinstance(answer, Belief), answer
    return answer.belief_input_digest


def test_retired_waiver_is_key_local(tmp_path):
    scene = Scene(tmp_path / "corpus")
    stale_key, unaffected_key = scene.key("a"), scene.key("c")
    before = scene.evaluate(scene.profile())
    assert isinstance(before.view.beliefs[stale_key], Belief)
    unaffected_digest_before = _digest(before.view.beliefs[unaffected_key])
    stale_inputs = before.traces[stale_key][2]
    assert stale_inputs is not None
    assert stale_inputs.dependencies.closure.verdicts[scene.identity("a")] == Eligible()
    # The selected rules join the closure reads, retraction scope and pin agreement.
    assert scene.world.t in stale_inputs.dependencies.closure.reads
    assert ("classification-rule", scene.world.t) in stale_inputs.declared_refs()
    consulted = dict(stale_inputs.consulted)
    assert {"scope-relations", "scope-relations-b", "scope-terms"} <= consulted.keys()
    unaffected_inputs = before.traces[unaffected_key][2]
    assert unaffected_inputs is not None
    assert "scope-relations" not in dict(unaffected_inputs.consulted)

    after = scene.evaluate(scene.profile(retire=True))
    inputs = after.traces[stale_key][2]
    assert inputs is not None
    stale_state = inputs.dependencies.closure.verdicts[scene.identity("a")]
    assert isinstance(stale_state, Ineligible)
    assert stale_state.reason == "scope-validity-incompatible"
    view = after.view
    stale_answer = view.beliefs[stale_key]
    assert isinstance(stale_answer, NoBelief)
    assert stale_answer.reason == "no-eligible-assessment"
    assert isinstance(view.beliefs[unaffected_key], Belief)
    unaffected_digest_after = _digest(view.beliefs[unaffected_key])
    assert unaffected_digest_after == unaffected_digest_before
    affected_pairs = [p for p in view.pairs if stale_key in (p.left, p.right)]
    assert affected_pairs and all(isinstance(p.synthesis, TargetUnknown) for p in affected_pairs)
    # The stored target bytes and key are unchanged; only current use differs.
    assert scene.key("a") == stale_key
    # The pure evaluator over the captured inputs reaches the same answer.
    assert scene.replay(scene.profile(retire=True), stale_key) == view.beliefs[stale_key]


def test_scope_eligibility_merge_precedence():
    nested_ref = "assessment:nested"
    intrinsic = Ineligible("not-admitted-verification-state", (nested_ref,))
    scope = Ineligible("scope-validity-incompatible", ('{"co_scope":"unknown"}',))
    assert merge_scope_eligibility(Eligible(), Eligible()) == Eligible()
    assert merge_scope_eligibility(intrinsic, Eligible()) == intrinsic
    assert merge_scope_eligibility(Eligible(), scope) == scope
    assert merge_scope_eligibility(intrinsic, scope) == intrinsic
    merged = merge_scope_eligibility(intrinsic, scope)
    assert merge_scope_eligibility(merged, Eligible()) == intrinsic
    assert merge_scope_eligibility(merge_scope_eligibility(Eligible(), scope), Eligible()) == scope


class _HeldView:
    def __init__(self, view, digests):
        self.view, self.digests = view, digests

    def holds(self, id):
        return self.view.holds(id)

    def read(self, id):
        return self.view.get(id)

    def retraction_in_force(self, id):
        return False

    def observation_held(self, digest):
        return digest in self.digests

    def crosswalks(self, a, b):
        return ()


@pytest.mark.parametrize("inputs_held", [True, False])
def test_nested_waiver_is_rechecked(tmp_path, inputs_held):
    scene = Scene(tmp_path / "corpus")
    view = reopen(scene.root)
    digests = {o.digest for values in _observations(*scene.letters).values() for o in values}
    records = _HeldView(view, digests if inputs_held else set())

    def verifications_of(identity):
        values = (stored.verification_value(n) for n in view.iter_stored() if n.kind == "verification")
        return tuple(v for v in values if v.assessment == identity)

    for profile, retired in ((scene.profile(), False), (scene.profile(retire=True), True)):
        readers = []

        def scope(value, profile=profile, readers=readers):
            reader = author_scope_reader(profile, records)
            readers.append(reader)
            return scope_eligibility(value.target, reader)

        nested = AssessmentEligibilityReader(
            records, profile, lambda id: run_value(view, stored.typed_ref("run", id)), verifications_of, scope=scope
        )
        verdict = nested("assessment:a-a")
        state = nested.states[scene.identity("a")]
        assert state == verdict
        # Scope evidence is collected whether or not the intrinsic check failed.
        assert readers and readers[0].comparisons and scene.world.t in readers[0].reads
        if not inputs_held:
            assert verdict == Ineligible("input-not-held")  # the intrinsic reason wins
        elif retired:
            assert isinstance(verdict, Ineligible) and verdict.reason == "scope-validity-incompatible"
        else:
            assert verdict == Eligible()


def test_two_assessments_filter_independently(tmp_path):
    scene = Scene(tmp_path / "corpus", shared_key=True, failing="a")
    assert scene.key("a") == scene.key("b") and scene.identity("a") != scene.identity("b")
    evaluation = scene.evaluate(scene.profile())
    admission = evaluation.traces[scene.key("a")][1]
    assert isinstance(admission, Reached)
    assert scene.identity("b") in admission.admitted and scene.identity("a") not in admission.admitted
    assert isinstance(evaluation.view.beliefs[scene.key("a")], Belief)
    assert isinstance(evaluation.view.beliefs[scene.key("c")], Belief)


def test_shared_key_waiver_retirement_filters_both(tmp_path):
    scene = Scene(tmp_path / "corpus", shared_key=True)
    evaluation = scene.evaluate(scene.profile(retire=True))
    inputs = evaluation.traces[scene.key("a")][2]
    assert inputs is not None
    for letter in ("a", "b"):
        state = inputs.dependencies.closure.verdicts[scene.identity(letter)]
        assert isinstance(state, Ineligible) and state.reason == "scope-validity-incompatible"
    assert isinstance(evaluation.view.beliefs[scene.key("a")], NoBelief)
    assert isinstance(evaluation.view.beliefs[scene.key("c")], Belief)


def _without(evidence: DependencyEvidence, *, record=None, state=None, read=None) -> DependencyEvidence:
    verdicts = {k: v for k, v in evidence.closure.verdicts.items() if k != state}
    reads = tuple(r for r in evidence.closure.reads if r != read)
    records = {k: v for k, v in evidence.records.items() if k != record}
    return DependencyEvidence(ClosureEligibility(verdicts, reads), records, evidence.assessments, evidence.runs)


def test_scope_evidence_omissions_refuse(tmp_path):
    scene = Scene(tmp_path / "corpus")
    profile, key, t = scene.profile(), scene.key("a"), scene.world.t
    evaluation = scene.evaluate(profile)
    inputs = evaluation.traces[key][2]
    assert inputs is not None
    evidence = inputs.dependencies
    assert scene.replay(profile, key, dependencies=evidence) == evaluation.view.beliefs[key]
    for omission in (
        {"record": t},
        {"state": t},
        {"read": t},
        {"state": scene.identity("a")},
        {"record": scene.world.r},
    ):
        with pytest.raises(errors.MalformedRecord, match="scope-evidence-incomplete"):
            scene.replay(profile, key, dependencies=_without(evidence, **omission))
    # Copying the comparisons is not recomputation: a state that disagrees with the
    # recomputed scope result is refused too.
    forged = dict(evidence.closure.verdicts)
    forged[scene.identity("a")] = Ineligible("scope-validity-incompatible", ("forged",))
    with pytest.raises(errors.MalformedRecord, match="scope-evidence-incomplete"):
        scene.replay(
            profile,
            key,
            dependencies=DependencyEvidence(
                ClosureEligibility(forged, evidence.closure.reads),
                evidence.records,
                evidence.assessments,
                evidence.runs,
            ),
        )
    # Withholding a selected owner's pin refuses rather than passing with the same digest.
    pins = pins_for(profile)
    reduced = replace(pins, domains={ns: pin for ns, pin in pins.domains.items() if ns != "scope-terms"})
    answer = scene.replay(profile, key, pins={"c1": reduced})
    assert not isinstance(answer, Belief)


def test_failed_scope_reads_replay_as_ineligible(tmp_path):
    scene = Scene(tmp_path / "corpus", t_held=False)
    profile, key = scene.profile(), scene.key("a")
    evaluation = scene.evaluate(profile)
    inputs = evaluation.traces[key][2]
    assert inputs is not None
    evidence = inputs.dependencies
    assert evidence.closure.verdicts[scene.world.t] == Ineligible("not-held")
    assert scene.world.t in evidence.closure.reads and scene.world.t not in evidence.records
    state = evidence.closure.verdicts[scene.identity("a")]
    assert isinstance(state, Ineligible) and state.reason == "scope-dependency-ineligible"
    assert scene.world.t in state.concerns
    assert isinstance(evaluation.view.beliefs[key], NoBelief)
    assert isinstance(evaluation.view.beliefs[scene.key("c")], Belief)
    # Complete recorded failed-read evidence replays as key-local ineligibility.
    assert scene.replay(profile, key) == evaluation.view.beliefs[key]


def test_disconnected_activation_preserves_digest(tmp_path):
    scene = Scene(tmp_path / "corpus")
    key = scene.key("a")
    baseline = _digest(scene.evaluate(scene.profile()).view.beliefs[key])
    disconnected = scene.profile(extra={"x-y": relation("x", "narrower", "y")})
    assert _digest(scene.evaluate(disconnected).view.beliefs[key]) == baseline
    # A selected owner's content change is visible in the digest.
    edited = scene.profile(editorial=True)
    assert _digest(scene.evaluate(edited).view.beliefs[key]) != baseline


def test_retracted_selected_rule_is_scope_ineligible(tmp_path):
    from lineage_fixtures import node_retraction
    from test_scope_validity import _rule

    scene = Scene(tmp_path / "corpus")
    unrelated = scene.world.records.put(_rule("Unrelated rule U."))
    raw_write(scene.root, scene.world.records.nodes[unrelated])
    raw_write(scene.root, node_retraction(scene.world.records.nodes[unrelated], "retract-u"))
    profile, key = scene.profile(), scene.key("a")
    assert isinstance(scene.evaluate(profile).view.beliefs[key], Belief)  # an unrelated retraction has no effect
    raw_write(scene.root, node_retraction(scene.world.records.nodes[scene.world.t], "retract-t"))
    evaluation = scene.evaluate(profile)
    inputs = evaluation.traces[key][2]
    assert inputs is not None
    # The root's closure state names the retracted member in the existing aggregate form.
    assert inputs.dependencies.closure.verdicts[scene.world.t] == Ineligible(f"dependency-ineligible: {scene.world.t}")
    state = inputs.dependencies.closure.verdicts[scene.identity("a")]
    assert isinstance(state, Ineligible) and state.reason == "scope-dependency-ineligible"
    assert isinstance(evaluation.view.beliefs[key], NoBelief)
    assert isinstance(evaluation.view.beliefs[scene.key("c")], Belief)
    assert scene.replay(profile, key) == evaluation.view.beliefs[key]


def test_frozen_mismatch_on_a_selected_root_stays_key_local(tmp_path):
    scene = Scene(tmp_path / "corpus", tamper="a")
    profile, r = scene.profile(), scene.world.r
    evaluation = scene.evaluate(profile)
    stale, unaffected = scene.key("a"), scene.key("c")
    inputs = evaluation.traces[stale][2]
    assert inputs is not None
    verdicts = inputs.dependencies.closure.verdicts
    assert verdicts[r] == Ineligible("frozen-dependency-mismatch")
    # One source of truth: the selected root's recorded row is what its scope state used.
    state = verdicts[scene.identity("a")]
    assert isinstance(state, Ineligible) and state.reason == "scope-dependency-ineligible" and r in state.concerns
    assert isinstance(evaluation.view.beliefs[stale], NoBelief)
    assert isinstance(evaluation.view.beliefs[unaffected], Belief)
    assert scene.replay(profile, stale) == evaluation.view.beliefs[stale]


def test_nested_targets_are_rechecked_in_pure_replay(tmp_path):
    """C14 nested: the stale assessment supplied only as a captured nested dependency."""
    from beliefs.evidence import scope_evidence

    scene = Scene(tmp_path / "corpus")
    retired, nested = scene.profile(retire=True), scene.identity("a")
    inputs = scene.evaluate(retired).traces[scene.key("a")][2]
    assert inputs is not None
    captured = inputs.dependencies
    stale = captured.closure.verdicts[nested]
    assert isinstance(stale, Ineligible) and stale.reason == "scope-validity-incompatible"

    def as_nested(**rows):
        verdicts = {**captured.closure.verdicts, **rows}
        verdicts = {k: v for k, v in verdicts.items() if v is not None}
        return DependencyEvidence(
            ClosureEligibility(verdicts, captured.closure.reads),
            captured.records,
            {"assessment:a-a": scene.values["a"]},  # type: ignore[dict-item]
            captured.runs,
        )

    # An accurate stale state, or an intrinsic failure that wins over it, is valid input.
    assert scope_evidence((), as_nested(), profile=retired)
    assert scope_evidence((), as_nested(**{nested: Ineligible("input-not-held")}), profile=retired)
    # A missing or Eligible state, or a different scope reason, is incomplete evidence.
    for row in (None, Eligible(), Ineligible("scope-dependency-ineligible", ("forged",))):
        with pytest.raises(errors.ScopeEvidenceIncomplete):
            scope_evidence((), as_nested(**{nested: row}), profile=retired)
    # Omitting a selected rule's state for the nested target refuses too.
    with pytest.raises(errors.ScopeEvidenceIncomplete):
        scope_evidence((), as_nested(**{scene.world.t: None}), profile=retired)
