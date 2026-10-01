"""Conformance cut 44 — mount citations (spec §8.2): J16–J21 over real roots on the
certified volume. W (write root) pins testing, the fixture `biology` and
coordination v2; M and M3 pin testing and the fixture `biology`; M2 pins another
`biology` identity; O holds J20's one-corpus baseline."""

from __future__ import annotations

import secrets
import shutil
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace

import pytest
from authority import FULL
from coordination_fixtures import pins_for
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import kwargs_for, over_kwargs, profile_with, seed_nodes
from domain_facet_fixtures import testing_contract as _testing_contract
from fixtures_cut3 import typed_applicability, typed_estimand
from profiles import biology
from test_session_acceptance import fresh
from test_session_mounts_acceptance import library_on, state
from test_world_receipts import hold_shipped, publish
from test_world_view import make_absent

from beliefs import stored
from beliefs.audit import NO_EVIDENCE, audit_world
from beliefs.belief import Belief, NoBelief, Refused
from beliefs.corpus import ReadView, corpus_check, lineage_snapshot
from beliefs.errors import (
    AddressMapConflict,
    BuildContended,
    CitationContractMismatch,
    EligibilityUnmet,
    InputOutsideCorpus,
)
from beliefs.evaluation import evaluate_over, evaluate_over_traced, gather
from beliefs.mount import compile_mount_profile
from beliefs.permit import RequiredCapabilities
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination
from beliefs.root import init_corpus_root, init_world_root, open_corpus, open_world
from beliefs.session import open_attended_session
from beliefs.world import Fresh, WorldConfig, load_manifest
from beliefs.world.view import open_world_view

TYPED = profile_with()
TYPED_OTHER = profile_with("other")
W_PROFILE = compile_profile(
    shipped_base_contract(), [_testing_contract(None), biology("fixture")], coordination=shipped_coordination(2)
)
AVAILABLE = (_testing_contract(None), biology("fixture"), biology("other"))
CITING = RequiredCapabilities.for_kinds({"run", "assessment", "proposition", "verification"}, {"run": "run"})


def _adopt(base: Path, name: str, profile) -> Path:
    root = base / name
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
    return root.resolve()


@pytest.fixture()
def corpora(work_directory):
    """Every case owns one directory under the certified work directory: its
    roots, their `.metadata` siblings, its worlds and operations roots.
    Teardown removes it whole."""
    base = Path(mkdtemp(prefix="cut44-", dir=work_directory)).resolve()
    try:
        yield SimpleNamespace(
            base=base,
            w=_adopt(base, "w", W_PROFILE),
            m=_adopt(base, "m", TYPED),
            m2=_adopt(base, "m2", TYPED_OTHER),
            m3=_adopt(base, "m3", TYPED),
            o=_adopt(base, "o", TYPED),
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)


def open_session(s, roots):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    mounts = {root: compile_mount_profile(root, available=AVAILABLE) for root in roots}
    return open_attended_session(
        config, s.base / f"ops-{secrets.token_hex(4)}", write_root=s.w, profile=W_PROFILE, mounts=mounts
    )


def observed(seed):
    return stored.dataset_node(title=seed, resources=pinned(seed),
                               empirical_observation={"locator": "instrument:fixture", "attested_by": "test-actor"})


def assessment(slug, run, prop_id):
    return stored.assessment_node(slug, title=slug, spec="analysis-spec:s1", run=run.id, proposition=prop_id,
                                  outcome="supported", interpretation_rule="rule:threshold",
                                  estimand=typed_estimand(), applicability=typed_applicability())


def seeded(s):
    m = library_on(s.m, TYPED)
    return m.add(observed("d")), m.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))


def run_then(w, d):
    return w.add(stored.run_node("r", title="r", spec="analysis-spec:s1", observes=[d.id]))  # observes is not read at write time


# --- J16 ------------------------------------------------------------------------


def test_j16_a_session_cites_a_mount_dataset_and_proposition_durably(corpora):
    s = corpora
    d, p = seeded(s)
    before = state(s.m)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    held = w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert ReadView.opened_at(s.w).holds(held.id) and state(s.m) == before


def test_j16_a_citation_across_differing_identities_refuses_durably(corpora):
    s = corpora
    d, _p = seeded(s)
    p2 = library_on(s.m2, TYPED_OTHER).add(stored.proposition_node("p2", title="p2", claim={"operator": "affects"}))
    session = open_session(s, (s.w, s.m, s.m2))
    w = fresh(session, "A", CITING)
    run = run_then(w, d)
    unchanged = state(s.w)
    with pytest.raises(CitationContractMismatch) as refused:
        w.add(assessment("a", run, p2.id))
    assert state(s.w) == unchanged  # refused before any effect: W's tree and its chain
    session.close_invocation("A", {"done": []})
    session.close()
    assert (refused.value.root, refused.value.namespace) == (s.m2, "biology")
    assert refused.value.held == f"biology:{biology('other').content_identity}"
    assert refused.value.writer == f"biology:{biology('fixture').content_identity}"


def test_j16_producers_held_in_a_third_mount_refuse_durably(corpora):
    s = corpora
    d, p = seeded(s)
    library_on(s.m3, TYPED).add(stored.run_node("r3", title="r3", spec="analysis-spec:s1", produces=[d.id]))
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    with pytest.raises(EligibilityUnmet, match="run:r3"):
        w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()


def test_j16_no_mount_is_written_durably(corpora):
    s = corpora
    d, p = seeded(s)
    before = {root: state(root) for root in (s.m, s.m3)}
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert {root: state(root) for root in (s.m, s.m3)} == before


# --- J17 ------------------------------------------------------------------------


def test_j17_a_duplicate_citation_refuses_naming_both_durably(corpora):
    s = corpora
    d, p = seeded(s)
    library_on(s.m3, TYPED).add(observed("d"))
    session = open_session(s, (s.w, s.m, s.m3))
    w = fresh(session, "A", CITING)
    run = run_then(w, d)
    unchanged = state(s.w)
    with pytest.raises(AddressMapConflict) as refused:
        w.add(assessment("a", run, p.id))
    assert state(s.w) == unchanged  # refused before any effect: W's tree and its chain
    session.close_invocation("A", {"done": []})
    session.close()
    ids = sorted(ReadView.opened_at(root).corpus_id for root in (s.m, s.m3))
    assert (refused.value.finding.code, refused.value.finding.detail) == ("duplicate-location", ", ".join(ids))


def test_j17_a_held_mount_refuses_build_contended_durably(corpora):
    s = corpora
    d, p = seeded(s)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    run = run_then(w, d)
    held = library_on(s.m, TYPED)  # a second holder: a library writer on M, not the session
    unchanged = state(s.w)
    with held._state.lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p.id))
    assert state(s.w) == unchanged  # refused before any effect: W's tree and its chain
    session.close_invocation("A", {"done": []})
    session.close()


# --- J18 ------------------------------------------------------------------------


def test_j18_the_session_corpus_check_warns_not_errs_durably(corpora):
    s = corpora
    d, p = seeded(s)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    w.add(assessment("a", run_then(w, d), p.id))
    session.close_invocation("A", {"done": []})
    session.close()
    assert [(f.severity, f.code) for f in corpus_check(ReadView.opened_at(s.w), W_PROFILE)] == [
        ("warning", "eligibility-unresolved")
    ]


# --- J19 / J20: the two-installation split ------------------------------------------


def _split_seed(s):
    """J20's fixture: `seed_nodes()`'s proposition and datasets in M, its runs,
    assessments and verifications written in a session on W; the same nodes in O."""
    nodes = seed_nodes()
    in_m = {"proposition:p", dataset_ref("d-a"), dataset_ref("d-b")}
    m, o = library_on(s.m, TYPED), library_on(s.o, TYPED)
    for node in nodes:
        o.add(node)
        if node.id in in_m:
            m.add(node)
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    for node in nodes:
        if node.id not in in_m:
            w.add(node)
    session.close_invocation("A", {"done": []})
    session.close()
    roots = {ReadView.opened_at(root).corpus_id: root for root in (s.w, s.m)}
    # a durable world: the roots are open under the certified executor factory, one factory per root
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots.values()))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    for root in roots.values():
        world.admit(root, provenance=Fresh())
    return world, roots, publish(world, tuple(sorted(roots)), hold_shipped(world))


def _world_context(view, pins, kwargs):
    """`pins` are read once, while every manifest is present (plan review 2, P2)."""
    return replace(
        kwargs["context"],
        snapshot=lineage_snapshot(view, (dataset_ref("d-a"), dataset_ref("d-b"))),
        producer_snapshot_identity=view.producer_snapshot_identity(),
        node_corpus={},
        pins=pins,
    )


def _assessment_ids(nodes) -> set[str]:
    return {stored.assessment_reference(n).identity() for n in nodes if n.kind == "assessment"}


def _eligibility(audit, corpus_id):
    return [(f.severity, f.code, f.ref, f.detail) for f in audit.corpora[corpus_id] if f.code.startswith("eligibility")]


def test_j19_the_world_audit_supports_the_split_durably(corpora):
    s = corpora
    world, roots, published = _split_seed(s)
    w_id, m_id = ReadView.opened_at(s.w).corpus_id, ReadView.opened_at(s.m).corpus_id
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=TYPED)
    assert not [f for findings in audit.corpora.values() for f in findings if f.code.startswith("eligibility")]
    # M absent: each of W's assessments is judged on its own, unresolved and naming M, and the
    # audit continues over W's other records (world-audit seams need an absent-corpus test).
    make_absent(roots, m_id)
    absent = audit_world(world, published, evidence=NO_EVIDENCE, profile=TYPED)
    findings = _eligibility(absent, w_id)
    w_assessments = sorted(n.id for n in seed_nodes() if n.kind == "assessment")
    assert sorted(ref for _severity, _code, ref, _detail in findings) == w_assessments
    assert all(
        severity == "warning" and code == "eligibility-unresolved" and m_id in detail and "absent" in detail
        for severity, code, _ref, detail in findings
    )
    assert "corpus-absent" in {f.code for f in absent.corpora[m_id]}
    # W's own findings stand with M absent: its manifest's domain-scope `profile-mismatch` (W pins
    # coordination v2; the audit runs under TYPED), which does not stop W's records being judged
    others = {(f.code, f.ref) for f in audit.corpora[w_id]}
    assert others == {("profile-mismatch", "corpus.yaml")}
    assert others <= {(f.code, f.ref) for f in absent.corpora[w_id]}


def test_j20_belief_over_the_world_matches_one_corpus_durably(corpora):
    s = corpora
    world, roots, published = _split_seed(s)
    w_id, m_id = ReadView.opened_at(s.w).corpus_id, ReadView.opened_at(s.m).corpus_id
    view = open_world_view(world, published)
    kwargs = kwargs_for(view, TYPED)
    pins = {corpus_id: load_manifest(root).profile for corpus_id, root in roots.items()}
    context = _world_context(view, pins, kwargs)
    split_answer, split_admission = evaluate_over_traced(view, "proposition:p", **over_kwargs({**kwargs, "context": context}))
    local = ReadView.opened_at(s.o)
    local_kwargs = kwargs_for(local, TYPED)
    local_answer, local_admission = evaluate_over_traced(local, "proposition:p", **over_kwargs(local_kwargs))
    # `belief_input_digest` differs by construction: the closure names the producer snapshot and the
    # retraction coverage, the world's epoch and corpus ids (mount-citations spec §13). The verdict,
    # the evidence set (every other closure member) and the admission are compared instead.
    assert isinstance(split_answer, Belief) and isinstance(local_answer, Belief)
    assert split_answer.value == local_answer.value and split_answer.policy_binding == local_answer.policy_binding
    assert split_admission == local_admission
    inputs = gather(view, "proposition:p", context=context, profile=TYPED,
                    resolution=kwargs["resolution"], binding=kwargs["binding"])
    local_inputs = gather(local, "proposition:p", context=local_kwargs["context"], profile=TYPED,
                          resolution=local_kwargs["resolution"], binding=local_kwargs["binding"])
    split_closure = inputs.closure().projection
    assert _without_corpus_names(split_closure) == _without_corpus_names(local_inputs.closure().projection)
    # and the two members left out are exactly the world's names: its epoch and its corpora
    assert split_closure["producer_snapshot"] == view.producer_snapshot_identity()
    assert split_closure["retractions"] == {"found": [], "coverage": sorted((w_id, m_id))}
    # attribution: the assessments and runs to W, the observed datasets to M; the proposition is
    # read through the world view from M (gather attributes closure nodes only, not the proposition)
    assert dict(inputs.node_corpus) == {
        **{identity: (w_id,) for identity in _assessment_ids(seed_nodes())},
        "run:run-a": (w_id,),
        "run:run-b": (w_id,),
        dataset_ref("d-a"): (m_id,),
        dataset_ref("d-b"): (m_id,),
    }
    assert view.corpus_of("proposition:p") == m_id
    # the walk inspected M's dataset through the world view: held, its (empty) producer set captured
    assert context.snapshot.producers[dataset_ref("d-a")] == ()
    assert dataset_ref("d-a") not in context.snapshot.not_present
    make_absent(roots, m_id)
    absent_view = open_world_view(world, published)
    absent_context = _world_context(absent_view, pins, kwargs)
    assert dataset_ref("d-a") not in absent_context.snapshot.producers
    assert absent_context.snapshot.not_present[dataset_ref("d-a")] == m_id
    answer, _admission = evaluate_over_traced(absent_view, "proposition:p", **over_kwargs({**kwargs, "context": absent_context}))
    assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"
    assert m_id in answer.detail and w_id not in answer.detail


def _without_corpus_names(projection: Mapping[str, object]) -> dict[str, object]:
    """The closure projection less exactly the two members that name a corpus or an epoch."""
    kept = {key: value for key, value in projection.items() if key != "producer_snapshot"}
    retractions = projection["retractions"]
    assert isinstance(retractions, Mapping) and set(retractions) == {"found", "coverage"}
    kept["retractions"] = {"found": retractions["found"]}
    return kept


# --- J21 ------------------------------------------------------------------------


def test_j21_a_local_read_of_the_split_refuses_durably(corpora):
    s = corpora
    d, _p = seeded(s)
    own = library_on(s.w, W_PROFILE)  # W's own d-a and d-b: the roots `kwargs_for`'s lineage snapshot walks
    for seed in ("d-a", "d-b"):
        own.add(observed(seed))
    session = open_session(s, (s.w, s.m))
    w = fresh(session, "A", CITING)
    q = w.add(stored.proposition_node("q", title="q", claim={"operator": "affects"}))
    run = run_then(w, d)
    a = w.add(assessment("a", run, q.id))
    session.close_invocation("A", {"done": []})
    session.close()
    view = ReadView.opened_at(s.w)
    kwargs = kwargs_for(view, W_PROFILE)
    with pytest.raises(InputOutsideCorpus) as refused:
        gather(view, q.id, context=kwargs["context"], profile=W_PROFILE,
               resolution=kwargs["resolution"], binding=kwargs["binding"])
    assert refused.value.assessment == stored.assessment_reference(a).identity()
    assert (refused.value.run, refused.value.inputs) == (run.id, (d.id,))
    answer = evaluate_over(view, q.id, **over_kwargs(kwargs))
    assert isinstance(answer, Refused) and answer.reason.startswith("input-outside-corpus: ")
