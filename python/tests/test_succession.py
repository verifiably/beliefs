"""`admit_spec_successor` over fabricated roots (successor-admission design §4)."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from nodes.core.write_plan import CreateOp
from succession_fixtures import (
    admit,
    append_assessment_intent,
    assessment,
    corpus,
    publish,
    seam,
    specs,
    verification,
)

from science import stored, succession
from science.errors import AdmissionEvidenceRefused
from science.intents import reduce as intent_reduce
from science.runrecord import publication_plan
from science.spec import SuccessorAdmitted, SuccessorRefused
from science.succession import REASONS, admit_spec_successor
from science.world.records import RECORD_CEILING


def _refuses(root, candidate, superseded, reason: str) -> AdmissionEvidenceRefused:
    with pytest.raises(AdmissionEvidenceRefused) as caught:
        admit(root, candidate, superseded)
    assert caught.value.reason == reason
    return caught.value


def _report_plan(report):
    node = stored.act_report_node(report)
    return (CreateOp(f"act-report/{report.identity()}.md", node_to_markdown(node).encode("utf-8")),)


def _raw(port, path: str, payload: bytes) -> None:
    port.execute((CreateOp(path, payload),))


def _oversized(root, path: str) -> None:
    (root / path).parent.mkdir(exist_ok=True)
    (root / path).write_bytes(b"x" * (RECORD_CEILING + 1))


def _failing_pair(port, spec_identity: str, slug: str = "v1"):
    target = assessment(spec_identity)
    failing = verification(slug, target, "failed")
    publish(port, target, failing)
    return target, failing


# --- G4u13, K4: before the derivation ---------------------------------------------


def test_the_reason_set_is_exactly_the_specs_eleven() -> None:
    assert REASONS == (
        "root unreadable",
        "chain not well-formed",
        "namespace uninspectable",
        "verification unreadable",
        "assessment unreadable",
        "verification oversized",
        "verification edge cardinality",
        "verification target unreadable",
        "verification target mismatch",
        "record collision",
        "qualification unresolved for the superseded spec",
    )


def test_an_absent_root_refuses_before_any_lock(certified_work) -> None:
    original, unreferenced, _ = specs()
    refused = _refuses(certified_work / "nowhere", unreferenced, original, "root unreadable")
    assert refused.ref == str((certified_work / "nowhere").resolve())


@pytest.mark.parametrize("failure_type", [RuntimeError, ValueError])
def test_a_resolution_failure_refuses_before_any_lock(
    certified_work,
    monkeypatch,
    failure_type: type[Exception],
) -> None:
    root = certified_work / "loop"
    original, unreferenced, _ = specs()

    def fail_resolution(*_args, **_kwargs):
        raise failure_type("injected resolution failure")

    def fail_lock(_root):
        pytest.fail("a root-resolution refusal must happen before the operation lock")

    guarded_seam = replace(seam(), corpus_lock=fail_lock)
    monkeypatch.setattr(succession.Path, "resolve", fail_resolution)
    with pytest.raises(AdmissionEvidenceRefused) as caught:
        admit_spec_successor(unreferenced, original, seam=guarded_seam, root=root)
    assert (caught.value.reason, caught.value.ref) == ("root unreadable", str(root))


def test_a_file_where_the_root_should_be_refuses_as_unreadable(certified_work) -> None:
    # `root` is resolved before the `O_DIRECTORY | O_NOFOLLOW` open (design
    # §4.1), so a symlink to a real corpus admits through its target; what
    # the open refuses is a path that is not a directory at all.
    not_a_directory = certified_work / "file"
    not_a_directory.write_bytes(b"")
    original, unreferenced, _ = specs()
    assert _refuses(not_a_directory, unreferenced, original, "root unreadable").ref == str(not_a_directory.resolve())


def test_a_close_only_root_probe_failure_does_not_change_admission(certified_work, monkeypatch) -> None:
    root, _ = corpus(certified_work, "close-failure")
    original, unreferenced, _ = specs()
    real_close = os.close
    injected = False

    def fail_once(fd: int) -> None:
        nonlocal injected
        real_close(fd)
        if not injected:
            injected = True
            raise OSError("injected close failure")

    monkeypatch.setattr(succession.os, "close", fail_once)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_an_unregistered_directory_is_an_absent_chain_and_refuses(certified_work) -> None:
    root = certified_work / "bare"
    root.mkdir()
    original, unreferenced, _ = specs()
    _refuses(root, unreferenced, original, "chain not well-formed")


def test_an_unenumerable_namespace_refuses_for_verification_and_for_run(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user"
    original, unreferenced, _ = specs()
    for namespace in ("verification", "run"):
        root, _ = corpus(certified_work, f"locked-{namespace}")
        locked = root / namespace
        locked.mkdir()
        locked.chmod(0)
        try:
            refused = _refuses(root, unreferenced, original, "namespace uninspectable")
        finally:
            locked.chmod(0o755)
        assert refused.ref == namespace


def test_an_absent_verification_namespace_admits(certified_work) -> None:
    root, _ = corpus(certified_work, "empty")
    original, unreferenced, _ = specs()
    assert not (root / "verification").exists()
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


# --- G4u2, G4u12, G4u10, L7u15, L7u16: class 2 from the chain -------------------------


def test_an_unfinished_attempt_blocks_an_unreferenced_successor(certified_work) -> None:
    root, port = corpus(certified_work, "unfinished")
    original, unreferenced, referencing = specs()
    append_assessment_intent(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_an_unfinished_attempt_for_another_spec_blocks_nothing(certified_work) -> None:
    root, port = corpus(certified_work, "other-spec")
    original, unreferenced, _ = specs()
    append_assessment_intent(port, "f" * 64)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_the_negative_nothing_durable_admits(certified_work) -> None:
    # G4u12: the attempt and its intent discarded before any append — no class
    # holds a trace, and the successor is admitted. Crash, cancellation and
    # discarded failure are indistinguishable by construction.
    root, _ = corpus(certified_work, "negative")
    original, unreferenced, _ = specs()
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_decayed_run_under_the_superseded_spec_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "decayed")
    original, unreferenced, _ = specs()
    _, path, plan = publication_plan(make_closure(spec=original.identity))
    intent = append_assessment_intent(port, original.identity)
    port.execute_fulfilling(plan, intent)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])
    refused = _refuses(root, unreferenced, original, "qualification unresolved for the superseded spec")
    assert refused.ref == intent


def test_a_decayed_run_under_another_spec_does_not_block(certified_work) -> None:
    root, port = corpus(certified_work, "decayed-other")
    original, unreferenced, _ = specs()
    other = "e" * 64
    _, path, plan = publication_plan(make_closure(spec=other))
    port.execute_fulfilling(plan, append_assessment_intent(port, other))
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_qualifying_run_lifts_the_block(certified_work) -> None:
    # L7u16
    root, port = corpus(certified_work, "qualified")
    original, unreferenced, _ = specs()
    _, _, plan = publication_plan(make_closure(spec=original.identity))
    port.execute_fulfilling(plan, append_assessment_intent(port, original.identity))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_wrong_spec_publication_fails_qualification_and_the_intent_still_blocks(certified_work) -> None:
    # L7u15
    root, port = corpus(certified_work, "wrong-spec")
    original, unreferenced, _ = specs()
    _, _, plan = publication_plan(make_closure(spec="x" * 64))
    port.execute_fulfilling(plan, append_assessment_intent(port, original.identity))
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to an unfinished recorded attempt"


# --- G4u3, G4u14: class 1b from run-attempt reports ------------------------------------


def test_a_run_attempt_report_is_a_recorded_failure(certified_work) -> None:
    root, port = corpus(certified_work, "run-attempt")
    original, unreferenced, referencing = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    port.execute_fulfilling(_report_plan(sample_report(operation="run-attempt", token="tok")), intent)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_a_matched_registration_is_decoded_once_for_qualification_and_admission(
    certified_work,
    monkeypatch,
) -> None:
    root, port = corpus(certified_work, "single-pass")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    port.execute_fulfilling(
        _report_plan(sample_report(operation="run-attempt", token="tok")),
        intent,
    )
    decoded: set[str] = set()
    real_decode = intent_reduce.evidence_module.decode_record

    def decode_once(path: str, payload: bytes):
        if path in decoded:
            raise AssertionError(f"{path} was decoded twice")
        decoded.add(path)
        return real_decode(path, payload)

    monkeypatch.setattr(intent_reduce.evidence_module, "decode_record", decode_once)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_an_undecodable_sibling_before_the_qualifying_report_still_joins(certified_work) -> None:
    # G4u14: the registration carries `act-report/aaa.md` (undecodable, sorts
    # first) and the qualifying run-attempt report; `matched` is the reducer's
    # verdict and the report is the match.
    root, port = corpus(certified_work, "sibling")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    report = sample_report(operation="run-attempt", token="tok")
    port.execute_fulfilling(
        (CreateOp("act-report/aaa.md", b"not a record"), *_report_plan(report)),
        intent,
    )
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_a_qualifying_run_beside_a_report_joins_nothing(certified_work) -> None:
    # G4u14, the other half: one registration carries both a qualifying run and
    # a qualifying run-attempt report. `final` is path-ordered and
    # `act-report/` sorts before `run/`, so the report would match first — the
    # arm therefore publishes the report under a token that does not qualify,
    # leaving the run the first (and only) qualifying record, and asserts a
    # `RunEvidence` match is a minted run, not a failure.
    root, port = corpus(certified_work, "run-and-report")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    _, _, run_plan = publication_plan(make_closure(spec=original.identity, token="tok"))
    stray = _report_plan(sample_report(operation="run-attempt", token="other"))
    port.execute_fulfilling((*stray, *run_plan), intent)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_qualifying_report_before_a_qualifying_run_is_the_match(certified_work) -> None:
    # G4u14, the mixed registration proper: both records qualify; the report
    # sorts first in `final`, so the reducer's first match is the report and
    # the spec joins class 1 — the act reads the record that matched, in the
    # reducer's order, never "whichever is a run".
    root, port = corpus(certified_work, "report-then-run")
    original, unreferenced, _ = specs()
    intent = append_assessment_intent(port, original.identity, token="tok")
    _, _, run_plan = publication_plan(make_closure(spec=original.identity, token="tok"))
    report = _report_plan(sample_report(operation="run-attempt", token="tok"))
    port.execute_fulfilling((*report, *run_plan), intent)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


# --- G4u1, G4u4, G4u5, G4u6: class 1a ---------------------------------------------------


def test_a_live_failing_verification_blocks_an_unreferenced_successor(certified_work) -> None:
    root, port = corpus(certified_work, "failing")
    original, unreferenced, referencing = specs()
    _failing_pair(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"
    assert isinstance(admit(root, referencing, original), SuccessorAdmitted)


def test_a_failing_verification_for_another_spec_blocks_nothing(certified_work) -> None:
    root, port = corpus(certified_work, "failing-other")
    original, unreferenced, _ = specs()
    _failing_pair(port, "d" * 64)
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_passing_verification_is_not_blocker_evidence(certified_work) -> None:
    root, port = corpus(certified_work, "passing")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target, verification("v1", target, "passed"))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_overlap_refuses_with_the_recorded_failure_reason(certified_work) -> None:
    # G4u5: the same spec is in both classes.
    root, port = corpus(certified_work, "overlap")
    original, unreferenced, _ = specs()
    _failing_pair(port, original.identity)
    append_assessment_intent(port, original.identity)
    verdict = admit(root, unreferenced, original)
    assert isinstance(verdict, SuccessorRefused)
    assert verdict.reason == "an unreferenced successor to a recorded failed replay"


def test_a_coherent_passing_superseder_lifts_the_block(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-pass")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    publish(port, verification("v2", target, "passed", supersedes=failing.id))
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_failing_superseder_keeps_the_block_through_the_active_member(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-fail")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    publish(port, verification("v2", target, "failed", supersedes=failing.id))
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_an_incoherent_passing_superseder_refuses_naming_itself(certified_work) -> None:
    root, port = corpus(certified_work, "superseded-incoherent")
    original, unreferenced, _ = specs()
    target, failing = _failing_pair(port, original.identity)
    superseder = verification("v2", target, "passed", supersedes=failing.id)
    superseder.relations = []  # zero `verifies` edges; the stamp covers the facet, not relations
    publish(port, superseder)
    refused = _refuses(root, unreferenced, original, "verification edge cardinality")
    assert refused.ref == "verification/v2.md"


# --- G4u7: the evidence gate -------------------------------------------------------------


def test_a_stale_stamp_refuses_naming_the_path(certified_work) -> None:
    root, port = corpus(certified_work, "stale")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    stale = verification("v1", target, "failed")
    stale.facets["verification"]["verdict"] = "passed"
    publish(port, target, stale)
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/v1.md"


def test_a_missing_stamp_refuses_naming_the_path(certified_work) -> None:
    root, port = corpus(certified_work, "unstamped")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    bare = verification("v1", target, "failed")
    del bare.facets[stored.SEMANTIC_IDENTITY_FACET]
    publish(port, target, bare)
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/v1.md"


def test_an_id_naming_another_path_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "misnamed")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target)
    _raw(port, "verification/other.md", node_to_markdown(verification("v1", target, "failed")).encode("utf-8"))
    assert _refuses(root, unreferenced, original, "verification unreadable").ref == "verification/other.md"


def test_an_undecodable_verification_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "undecodable")
    original, unreferenced, _ = specs()
    _raw(port, "verification/v1.md", b"---\nnot: [a record\n---\n")
    _refuses(root, unreferenced, original, "verification unreadable")


def test_an_undecodable_untargeted_assessment_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "bad-assessment")
    original, unreferenced, _ = specs()
    _raw(port, "assessment/a9.md", b"---\nnot: [a record\n---\n")
    assert _refuses(root, unreferenced, original, "assessment unreadable").ref == "assessment/a9.md"


@pytest.mark.parametrize(
    ("path", "node_id", "kind", "relation_shape", "reason"),
    [
        (
            "verification/v1.md",
            "verification:v1",
            "verification",
            "related: 1",
            "verification unreadable",
        ),
        (
            "assessment/a1.md",
            "assessment:a1",
            "assessment",
            "relations: [nope]",
            "assessment unreadable",
        ),
    ],
)
def test_yaml_valid_malformed_relation_shapes_refuse_in_either_namespace(
    certified_work,
    path: str,
    node_id: str,
    kind: str,
    relation_shape: str,
    reason: str,
) -> None:
    root, port = corpus(certified_work, "malformed-" + kind)
    original, unreferenced, _ = specs()
    payload = (
        "---\n"
        f"id: {node_id}\n"
        "uid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        f"kind: {kind}\n"
        "title: malformed\n"
        f"{relation_shape}\n"
        "---\n"
    ).encode()
    _raw(port, path, payload)
    assert _refuses(root, unreferenced, original, reason).ref == path


def test_an_unreadable_regular_file_refuses_in_either_namespace(certified_work) -> None:
    assert os.geteuid() != 0, "this arm needs a non-root user"
    original, unreferenced, _ = specs()
    for namespace, reason in (
        ("verification", "verification unreadable"),
        ("assessment", "assessment unreadable"),
    ):
        root, port = corpus(certified_work, f"locked-file-{namespace}")
        target = assessment(original.identity)
        publish(port, target, verification("v1", target, "failed"))
        locked = root / namespace / ("v1.md" if namespace == "verification" else "a1.md")
        locked.chmod(0)
        try:
            refused = _refuses(root, unreferenced, original, reason)
        finally:
            locked.chmod(0o644)
        assert refused.ref == f"{namespace}/{locked.name}"


# --- G4u8: the coherence gate -------------------------------------------------------------


def test_two_verifies_edges_refuse(certified_work) -> None:
    root, port = corpus(certified_work, "two-edges")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    other = assessment(original.identity, slug="a2")
    doubled = verification("v1", target, "failed")
    doubled.relations.append(Relation(source=doubled.id, predicate=stored.VERIFIES, target=other.id))
    publish(port, target, other, doubled)
    _refuses(root, unreferenced, original, "verification edge cardinality")


def test_a_relation_sourced_elsewhere_is_not_this_verifications_edge(certified_work) -> None:
    # The gate counts outbound edges, not stored relations: the one `verifies`
    # relation this record stores runs from the assessment *to* the
    # verification, so it is an inbound edge of v1 and an outbound edge of a1
    # — and v1 has no outbound edge at all.
    root, port = corpus(certified_work, "foreign-source")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    mislabeled = verification("v1", target, "failed")
    mislabeled.relations = [Relation(source=target.id, predicate=stored.VERIFIES, target=mislabeled.id)]
    publish(port, target, mislabeled)
    assert _refuses(root, unreferenced, original, "verification edge cardinality").ref == "verification/v1.md"


def test_a_target_that_is_not_an_assessment_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "wrong-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    astray = verification("v1", target, "failed")
    astray.relations[0].target = "verification:v1"
    publish(port, target, astray)
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_missing_target_refuses(certified_work) -> None:
    # An unrelated assessment is present so that "some assessment" is never an
    # acceptable stand-in for the one the edge names: the refusal must be the
    # target's absence, not a mismatch against whatever happened to be there.
    root, port = corpus(certified_work, "missing-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    bystander = assessment("b" * 64, slug="a9")
    publish(port, bystander, verification("v1", target, "failed"))  # `target` is never published
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_deprecated_id_target_resolves_and_blocks(certified_work) -> None:
    root, port = corpus(certified_work, "deprecated")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    target.deprecated_ids = ["assessment:old"]
    stored.stamp_semantic_identity(target)
    pointing = verification("v1", target, "failed")
    pointing.relations[0].target = "assessment:old"
    publish(port, target, pointing)
    assert isinstance(admit(root, unreferenced, original), SuccessorRefused)


def test_a_uid_collision_refuses_naming_the_colliding_id(certified_work) -> None:
    root, port = corpus(certified_work, "collision")
    original, unreferenced, _ = specs()
    first = assessment(original.identity, slug="a1")
    second = assessment(original.identity, slug="a2")
    second.uid = first.uid
    stored.stamp_semantic_identity(second)
    publish(port, first, second)
    # Paths are read in sorted order, so `assessment/a2.md` is the node whose
    # admission to the index collides; its id is the ref.
    assert _refuses(root, unreferenced, original, "record collision").ref == "assessment:a2"


def test_an_identity_mismatch_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "mismatch")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    other = assessment("c" * 64, slug="a2")
    swapped = verification("v1", other, "failed")  # facet identity is `other`'s
    swapped.relations[0].target = target.id  # edge points at `target`
    stored.stamp_semantic_identity(swapped)
    publish(port, target, other, swapped)
    assert _refuses(root, unreferenced, original, "verification target mismatch").ref == "verification/v1.md"


# --- G4u9: oversized records ------------------------------------------------------------------


def test_a_withheld_verification_without_a_superseder_refuses(certified_work) -> None:
    root, _ = corpus(certified_work, "big-alone")
    original, unreferenced, _ = specs()
    _oversized(root, "verification/big.md")
    assert _refuses(root, unreferenced, original, "verification oversized").ref == "verification/big.md"


def test_a_withheld_verification_with_a_coherent_superseder_is_skipped(certified_work) -> None:
    root, port = corpus(certified_work, "big-superseded")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    publish(port, target, verification("v2", target, "passed", supersedes="verification:big"))
    _oversized(root, "verification/big.md")
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_withheld_verification_with_an_incoherent_superseder_refuses_the_superseder(certified_work) -> None:
    root, port = corpus(certified_work, "big-incoherent")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    superseder = verification("v2", target, "passed", supersedes="verification:big")
    superseder.relations = []
    publish(port, target, superseder)
    _oversized(root, "verification/big.md")
    assert _refuses(root, unreferenced, original, "verification edge cardinality").ref == "verification/v2.md"


def test_a_withheld_assessment_targeted_by_a_failing_verification_refuses(certified_work) -> None:
    root, port = corpus(certified_work, "big-target")
    original, unreferenced, _ = specs()
    target = assessment(original.identity, slug="big")
    publish(port, verification("v1", target, "failed"))
    _oversized(root, "assessment/big.md")
    assert _refuses(root, unreferenced, original, "verification target unreadable").ref == "verification/v1.md"


def test_a_withheld_untargeted_assessment_is_ignored(certified_work) -> None:
    root, _ = corpus(certified_work, "big-untargeted")
    original, unreferenced, _ = specs()
    _oversized(root, "assessment/big.md")
    assert isinstance(admit(root, unreferenced, original), SuccessorAdmitted)


def test_a_decoded_node_claiming_a_withheld_paths_id_is_a_collision(certified_work) -> None:
    root, port = corpus(certified_work, "big-claimed")
    original, unreferenced, _ = specs()
    target = assessment(original.identity)
    target.deprecated_ids = ["assessment:big"]
    stored.stamp_semantic_identity(target)
    publish(port, target)
    _oversized(root, "assessment/big.md")
    assert _refuses(root, unreferenced, original, "record collision").ref == "assessment:big"
