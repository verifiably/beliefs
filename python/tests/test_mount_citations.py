"""Mount citations (mount-citations design, cut 44): the mount view, the writer's
refusal chain over read mounts, and the session's wiring. Roots W, M and M3 pin
`TYPED` (the testing contract and the fixture `biology`, so `typed_estimand()`'s
`testing/affects` decodes); M2 pins `TYPED_OTHER`, another `biology` identity
(decision 3's mismatch); M4 pins `TESTING_ONLY`, a namespace set without `biology`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import profile_with
from domain_facet_fixtures import testing_contract as _testing_contract
from fixtures_cut3 import report as acquisition_report
from fixtures_cut3 import typed_applicability, typed_estimand
from nodes.core.errors import RefError
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_corpus_write import OperationRecorder
from verification_fixtures import publish_corpus

from beliefs import stored
from beliefs.corpus import CorpusWriter, MountCitations, ReadView, _operation_lock_for, _root_state_for
from beliefs.errors import (
    AcquisitionBoundaryRefused,
    AddressMapConflict,
    BuildContended,
    CitationContractMismatch,
    EligibilityUnmet,
    FacetPayloadRefused,
    ImportRefused,
)
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.verify import decode_verification, publication_node

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


IMPORT: dict[str, Any] = {"observer": "o", "instrument": "i", "opened_at": "2026-10-01T00:00:00Z", "closed_at": "2026-10-01T00:00:01Z"}


def mounted_writer(roots, *names, profile=TYPED, port=False):
    root = roots["w"]
    operation_port = OperationRecorder(root, authority=FULL, profile=profile) if port else None
    return CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile, operation_port=operation_port,
                        read_mounts=[roots[name] for name in names])


def test_an_assessment_over_a_mount_dataset_and_proposition_is_written(roots):
    """J16-a's and J16-b's check."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = mounted_writer(roots, "m")
    run = w.add(run_over("r", d))
    held = w.add(assessment("a", run, p))
    assert ReadView.opened_at(roots["w"]).holds(held.id)
    assert not ReadView.opened_at(roots["m"]).holds(held.id)


def test_a_verification_of_a_mount_assessment_is_written(roots):
    """J16-c's check: a published, report-carrying verification reads its `verifies`
    target through the citation view (a report-less one never reads the view)."""
    published = publish_corpus(adopted(roots["m"]))
    w = mounted_writer(roots, "m")
    node = publication_node(published.derived, assessment_ref=published.assessment.id)
    assert decode_verification(node) is not None
    held = w.add(node)
    assert ReadView.opened_at(roots["w"]).holds(held.id)
    assert not ReadView.opened_at(roots["m"]).holds(held.id)


def test_a_citation_across_differing_identities_refuses(roots):
    """J16-d's check."""
    m2 = adopted(roots["m2"], TYPED_OTHER)
    p2 = m2.add(proposition("p2"))
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", "m2")
    run = w.add(run_over("r", d))
    with pytest.raises(CitationContractMismatch):
        w.add(assessment("a", run, p2))


def test_an_assessment_over_a_dataset_a_third_mount_produces_refuses(roots):
    """J16-f's check: producers are the session's."""
    d = adopted(roots["m"]).add(observed("d"))
    p = adopted(roots["m"]).add(proposition("p"))
    adopted(roots["m3"]).add(run_over("r3", produces=[d.id]))
    w = mounted_writer(roots, "m", "m3")
    run = w.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet, match="run:r3"):
        w.add(assessment("a", run, p))


def test_a_candidate_named_by_a_mount_runs_dangling_edge_refuses(roots):
    adopted(roots["m"]).add(run_over("rm", produces=[dataset_ref("future")]))
    w = mounted_writer(roots, "m")
    with pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w.add(observed("future"))


def test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses(roots):
    """J16-h's check."""
    w = mounted_writer(roots, "m")
    plain = w.add(stored.dataset_node(title="plain", resources=pinned("plain")))
    adopted(roots["m"]).add(run_over("rm", produces=[plain.id]))
    candidate = plain.model_copy(deep=True)
    candidate.facets["empirical-observation"] = {"locator": "instrument:fixture", "attested_by": ACTOR}
    with pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w.revise(candidate)


def test_an_acquired_dataset_a_mount_run_produces_refuses(roots):
    """J16-i's check, at the seam `holdings/acquire.py` calls."""
    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    dataset = observed("got", retrieval=report.id)
    adopted(roots["m"]).add(run_over("rm", produces=[dataset.id]))
    w = mounted_writer(roots, "m")
    with w._citing(), pytest.raises(AcquisitionBoundaryRefused, match="run:rm"):
        w._refuse_acquired_dataset(dataset, report)


def test_an_imported_run_producing_a_mount_observation_refuses(roots):
    """J16-j's check: the reverse direction."""
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", port=True)
    with pytest.raises(ImportRefused) as refused:
        w.import_bundle([run_over("ri", produces=[d.id])], **IMPORT)
    assert refused.value.member == "run:ri"
    assert isinstance(refused.value.__cause__, AcquisitionBoundaryRefused)
    with pytest.raises(AcquisitionBoundaryRefused):
        w.add(run_over("rw", produces=[d.id]))


def test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses(roots):
    """J16-k's check: retrieval reports stay with their dataset."""
    m = adopted(roots["m"], TYPED)
    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    m_port = CorpusWriter(roots["m"], DefaultExecutor, authority=FULL, profile=TYPED,
                          operation_port=OperationRecorder(roots["m"], authority=FULL, profile=TYPED))
    m_port.import_bundle([report], **IMPORT)
    w = mounted_writer(roots, "m")
    with pytest.raises(FacetPayloadRefused, match="facet-retrieval-unresolved"):
        w.add(observed("split", retrieval=report.id))
    assert m.read_view.holds(report.id)


def test_an_assessment_over_a_raw_split_dataset_refuses(roots):
    """J16-l's check: eligibility reads a dataset's report in its own corpus."""
    from fixtures_cut4 import raw_write

    report = stored.act_report_node(acquisition_report(operation="acquisition"))
    CorpusWriter(roots["m"], DefaultExecutor, authority=FULL, profile=TYPED,
                 operation_port=OperationRecorder(roots["m"], authority=FULL, profile=TYPED)).import_bundle([report], **IMPORT)
    split = observed("split", retrieval=report.id)
    raw_write(roots["w"], split)
    p = adopted(roots["m"]).add(proposition("p"))
    w = mounted_writer(roots, "m")
    w._reconstruct()
    run = w.add(run_over("r", split))
    with pytest.raises(EligibilityUnmet, match="facet-retrieval-unresolved"):
        w.add(assessment("a", run, p))


def test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses(roots):
    """J16-m's check: imports resolve locally and judge producers over the session."""
    w = mounted_writer(roots, "m", port=True)
    d = w.add(observed("d"))
    run = w.add(run_over("r", d))
    p = w.add(proposition("p"))
    adopted(roots["m"]).add(run_over("rm", produces=[d.id]))
    with pytest.raises(ImportRefused) as refused:
        w.import_bundle([assessment("a", run, p)], **IMPORT)
    assert refused.value.member == "assessment:a"
    assert isinstance(refused.value.__cause__, EligibilityUnmet) and "run:rm" in str(refused.value.__cause__)


def test_without_read_mounts_the_writes_refuse_as_today(roots):
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = adopted(roots["w"])
    run = w.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet, match="unresolved"):
        w.add(assessment("a", run, p))


def test_a_write_citing_nothing_opens_no_mount_while_a_mount_is_held(roots):
    """Review Focus 1, and J17's negative."""
    w = mounted_writer(roots, "m")
    with _root_state_for(roots["m"], DefaultExecutor).lock:
        w.add(proposition("q"))


def test_a_citing_write_while_a_mount_is_held_refuses_build_contended(roots):
    """A run's `observes` is not read at write time; the assessment through it cites."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    w = mounted_writer(roots, "m")
    run = w.add(run_over("r", d))
    with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p))
    assert not ReadView.opened_at(roots["w"]).holds("assessment:a")


def test_an_assessment_citing_only_write_root_records_still_contends(roots):
    """J17's negative: decision 5 opens every read mount to rule out a second holder."""
    w = mounted_writer(roots, "m")
    d, p = w.add(observed("d")), w.add(proposition("p"))
    run = w.add(run_over("r", d))
    with _root_state_for(roots["m"], DefaultExecutor).lock, pytest.raises(BuildContended):
        w.add(assessment("a", run, p))


def test_a_refused_citing_write_releases_every_mount_hold(roots):
    """Review Focus 2."""
    adopted(roots["m2"], TYPED_OTHER).add(proposition("p2"))
    d = adopted(roots["m"]).add(observed("d"))
    w = mounted_writer(roots, "m", "m2")
    run = w.add(run_over("r", d))
    with pytest.raises(CitationContractMismatch):
        w.add(assessment("a", run, "proposition:p2"))
    for name in ("m", "m2"):
        with _operation_lock_for(roots[name]).capture():
            pass


def test_a_library_writer_beside_a_mounted_writer_reads_its_own_root_only(roots):
    """Review Focus 3: writer state is shared per root; the read mounts are not."""
    m = adopted(roots["m"])
    d, p = m.add(observed("d")), m.add(proposition("p"))
    mounted = mounted_writer(roots, "m")
    run = mounted.add(run_over("r", d))
    with pytest.raises(EligibilityUnmet):
        adopted(roots["w"]).add(assessment("a", run, p))


def test_read_mounts_refuse_the_writers_own_root_and_repeats(roots, tmp_path):
    link = tmp_path / "alias"
    link.symlink_to(roots["w"])
    with pytest.raises(ValueError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[link])
    with pytest.raises(ValueError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[roots["m"], roots["m"]])
    with pytest.raises(TypeError):
        CorpusWriter(roots["w"], DefaultExecutor, authority=FULL, profile=TYPED, read_mounts=[str(roots["m"])])  # pyright: ignore[reportArgumentType]


def test_a_spec_targeting_a_mount_proposition_is_written(tmp_path):
    """J16's analysis-spec case: `test_corpus_write.py`'s spec-target admission, the target held in M.
    Every root pins `TESTING_PROFILE`, as `typed_writer` does, so decision 3 does not fire."""
    from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, spec_draft, spec_rules

    from beliefs.projection import project_claim
    from beliefs.spec import freeze

    w_root, m_root = (tmp_path / "w").resolve(), (tmp_path / "m").resolve()
    adopted(w_root, TESTING_PROFILE)
    target = adopted(m_root, TESTING_PROFILE).add(stored.proposition_node("p", title="p", claim=project_claim(TESTING_CLAIM)))
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    w = CorpusWriter(w_root, DefaultExecutor, authority=FULL, profile=TESTING_PROFILE, read_mounts=[m_root])
    held = w.add(stored.analysis_spec_node(spec))
    assert held.id == f"analysis-spec:{spec.identity}"
    assert ReadView.opened_at(w_root).holds(held.id) and not ReadView.opened_at(m_root).holds(held.id)


def test_a_composite_over_mount_propositions_is_written(tmp_path):
    """J16's composite case: `test_composite_boundary.py`'s first add, the members held in M.
    Every root pins `WITH_BIOLOGY`, as that module does, so decision 3 does not fire."""
    from profiles import WITH_BIOLOGY
    from test_composite_boundary import SNAPSHOT, A, B, C, _claim, _proposition

    from beliefs.composite import build_composite

    w_root, m_root = (tmp_path / "w").resolve(), (tmp_path / "m").resolve()
    adopted(w_root, WITH_BIOLOGY)
    m = adopted(m_root, WITH_BIOLOGY)
    _proposition(m, "ab", _claim("EX:a", "EX:b"))
    _proposition(m, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    value, _ = build_composite(WITH_BIOLOGY, m.read_view, shape="dag", nodes=[A, B, C],
                               members=["proposition:ab", "proposition:bc"], snapshot=SNAPSHOT, slug="g")
    w = CorpusWriter(w_root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, read_mounts=[m_root])
    minted = w.add(stored.composite_node(value, title="a→b⊣c"))
    node = ReadView.opened_at(w_root).get(minted.id)
    assert {r.target for r in node.relations} == {"proposition:ab", "proposition:bc"}
    assert not ReadView.opened_at(m_root).holds(minted.id)
