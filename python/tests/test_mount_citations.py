"""Mount citations (mount-citations design, cut 44): the mount view, the writer's
refusal chain over read mounts, and the session's wiring. Roots W, M and M3 pin
`TYPED` (the testing contract and the fixture `biology`, so `typed_estimand()`'s
`testing/affects` decodes); M2 pins `TYPED_OTHER`, another `biology` identity
(decision 3's mismatch); M4 pins `TESTING_ONLY`, a namespace set without `biology`."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import profile_with
from domain_facet_fixtures import testing_contract as _testing_contract
from fixtures_cut3 import typed_applicability, typed_estimand
from nodes.core.errors import RefError
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for

from beliefs import stored
from beliefs.corpus import CorpusWriter, MountCitations, ReadView, _operation_lock_for, _root_state_for
from beliefs.errors import AddressMapConflict, BuildContended, CitationContractMismatch
from beliefs.profile import compile_profile, shipped_base_contract

TYPED = profile_with()
TYPED_OTHER = profile_with("other")
TESTING_ONLY = compile_profile(shipped_base_contract(), [_testing_contract(None)])


def adopted(root: Path, profile=TYPED) -> CorpusWriter:
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile)
    if not (root / "corpus.yaml").exists():
        writer.adopt_manifest(profile=pins_for(profile))
    return writer


def observed(seed: str, *, actor: str = ACTOR, retrieval: str | None = None):
    payload = {"locator": "instrument:fixture", "attested_by": actor}
    if retrieval is not None:
        payload["retrieval"] = retrieval
    return stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation=payload)


def run_over(slug: str, *datasets, produces=()):
    return stored.run_node(slug, title=slug, spec="analysis-spec:s1", observes=[d if isinstance(d, str) else d.id for d in datasets], produces=list(produces))


def proposition(slug: str):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


def assessment(slug: str, run, prop):
    return stored.assessment_node(
        slug, title=slug, spec="analysis-spec:s1", run=run.id, proposition=prop.id if not isinstance(prop, str) else prop,
        outcome="supported", interpretation_rule="rule:threshold",
        estimand=typed_estimand(), applicability=typed_applicability(),
    )


@pytest.fixture()
def roots(tmp_path):
    made = {name: tmp_path / name for name in ("w", "m", "m2", "m3", "m4")}
    for name, root in made.items():
        adopted(root, {"m2": TYPED_OTHER, "m4": TESTING_ONLY}.get(name, TYPED))
    return {name: root.resolve() for name, root in made.items()}


def citations(roots, *names):
    own = ReadView.opened_at(roots["w"])
    return MountCitations(own, TYPED, [roots[name] for name in names])


def test_holder_is_the_one_corpus_holding_a_ref(roots):
    d = adopted(roots["m"]).add(observed("d"))
    view = citations(roots, "m", "m3")
    try:
        holder = view.holder(d.id)
        assert holder is not None and holder.corpus_id == ReadView.opened_at(roots["m"]).corpus_id
        assert view.holds(d.id) and view.get(d.id).id == d.id
        assert view.holder("proposition:nowhere") is None
        with pytest.raises(RefError):
            view.get("proposition:nowhere")
    finally:
        view.close()


def test_a_ref_held_twice_refuses_duplicate_location_naming_both(roots):
    """J17-a's check."""
    d = adopted(roots["m"]).add(observed("d"))
    adopted(roots["m3"]).add(observed("d"))
    view = citations(roots, "m", "m3")
    try:
        with pytest.raises(AddressMapConflict) as refused:
            view.holder(d.id)
    finally:
        view.close()
    ids = sorted(ReadView.opened_at(roots[name]).corpus_id for name in ("m", "m3"))
    assert refused.value.finding.code == "duplicate-location"
    assert refused.value.finding.detail == ", ".join(ids)


def test_a_held_read_mount_lock_refuses_build_contended(roots):
    """J17-b's check: another holder owns M's operation lock."""
    d = adopted(roots["m"]).add(observed("d"))
    view = citations(roots, "m")
    try:
        with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
            view.holder(d.id)
    finally:
        view.close()


def test_read_mounts_open_lazily_and_close_releases_their_holds(roots):
    view = citations(roots, "m")
    with _operation_lock_for(roots["m"]):  # nothing opened yet, so nothing contends
        pass
    view.holder("proposition:anything")
    with pytest.raises(BuildContended), _operation_lock_for(roots["m"]).capture():  # held until close
        pass
    view.close()
    with _operation_lock_for(roots["m"]).capture():
        pass


def test_a_citation_into_a_differing_namespace_identity_refuses(roots):
    """J16-d's unit: M2 pins another `biology` identity than W's."""
    p = adopted(roots["m2"], TYPED_OTHER).add(proposition("p2"))
    view = citations(roots, "m2")
    try:
        with pytest.raises(CitationContractMismatch) as refused:
            view.holder(p.id)
    finally:
        view.close()
    assert refused.value.namespace == "biology" and refused.value.root == roots["m2"]


def test_a_namespace_only_the_writer_pins_does_not_refuse(roots):
    p = adopted(roots["m4"], TESTING_ONLY).add(proposition("p4"))
    view = citations(roots, "m4")
    try:
        assert view.holder(p.id) is not None
    finally:
        view.close()


def test_producers_are_the_union_over_the_session_dangling_edges_included(roots):
    target = dataset_ref("future")
    adopted(roots["w"]).add(run_over("rw", produces=[target]))
    adopted(roots["m"]).add(run_over("rm", produces=[target]))
    view = citations(roots, "m")
    try:
        assert view.producers(target) == ("run:rm", "run:rw")
    finally:
        view.close()


def test_the_session_overlay_resolves_into_mounts_and_unions_producers(roots):
    d = adopted(roots["m"]).add(observed("d"))
    adopted(roots["m3"]).add(run_over("r3", produces=[d.id]))
    view = citations(roots, "m", "m3")
    try:
        overlay = view.overlay(ReadView.opened_at(roots["w"]))
        assert overlay.resolve(d.id) == d.id and overlay.get(d.id).id == d.id
        assert overlay.producers(d.id) == ("run:r3",)
    finally:
        view.close()
