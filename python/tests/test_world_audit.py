"""The world audit over a capture (slice 3 design §5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from dataset_fixtures import pinned
from fixtures_cut4 import raw_write
from profiles import BASE, WITH_BIOLOGY
from test_profile_agreement import foreign_profile  # noqa: F401
from test_world_build import ALPHA, BETA
from test_world_view import damage, make_absent, split_verification_world, two_corpus_world

from beliefs import stored
from beliefs.audit import NO_EVIDENCE, WORLD_AUDIT_CODES, WorldAudit, audit_corpus, audit_world
from beliefs.corpus import ReadView
from beliefs.errors import CorpusDamaged


def codes(findings) -> list[tuple[str, str]]:
    return sorted((finding.code, finding.detail) for finding in findings)


def attestation(left: str, right: str):
    return stored.coreference_attestation_node(
        title="coreference attestation",
        endpoints=(left, right),
        stance=1,
        actor="alice",
        grounds="same work",
        event_token="event-1",
    )


def stale(slug: str):
    node = stored.dataset_node(title=f"dataset {slug}", resources=pinned(slug))
    node.facets["semantic-identity"]["digest"] = "0" * 64
    return node


def inventory(*roots: Path) -> dict[str, bytes]:
    return {str(path): path.read_bytes() for root in roots for path in root.rglob("*") if path.is_file()}


def test_a_clean_world_audits_clean(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert isinstance(audit, WorldAudit) and audit.stamp.packaging_identity == published.packaging_identity
    assert dict(audit.corpora) == {ALPHA: (), BETA: ()}
    assert audit.world == ()


def test_a_raw_written_record_is_drift_and_judged_and_skipped_by_recomputation(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    late = stale("late")
    raw_write(roots[ALPHA], late)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert codes(audit.corpora[ALPHA]) == [
        ("drift", "state"),
        ("drift", f"unmapped:{late.uid}"),
        ("semantic-hash-stale", "mismatch"),
    ]
    local = audit_corpus(ReadView.opened_at(roots[ALPHA]), evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert [finding for finding in local if finding.code == "semantic-hash-stale"] == [
        finding for finding in audit.corpora[ALPHA] if finding.code == "semantic-hash-stale"
    ]
    assert not any(
        finding.code.endswith("-contradicted") or finding.code == "derivation-malformed"
        for finding in audit.corpora[ALPHA]
    )


def test_a_new_record_after_publication_is_state_and_unmapped_drift(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    moved = stale("moved")
    raw_write(roots[BETA], moved)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert codes(audit.corpora[BETA]) == [
        ("drift", "state"),
        ("drift", f"unmapped:{moved.uid}"),
        ("semantic-hash-stale", "mismatch"),
    ]


def test_an_absent_corpus_is_reported(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    make_absent(roots, BETA)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert codes(audit.corpora[BETA]) == [("corpus-absent", "")]


@pytest.mark.parametrize("kind", ["parse-error", "path-mismatch", "uid-collision", "id-collision"])
def test_a_damaged_corpus_is_judged_on_its_remainder_and_never_compared(tmp_path, kind):
    world, roots, published = two_corpus_world(tmp_path)
    damage(roots[BETA], kind)
    raw_write(roots[BETA], stale("remainder"))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    found = codes(audit.corpora[BETA])
    assert any(code == kind for code, _detail in found)
    assert ("semantic-hash-stale", "mismatch") in found
    assert any(code == "corpus-damaged" and detail.startswith("construction:") for code, detail in found)
    assert not any(code == "drift" for code, _detail in found)
    assert audit.corpora[ALPHA] == ()


def test_a_foreign_base_pin_is_reported_from_the_manifest_alone(tmp_path):
    from dataclasses import replace

    from fixtures_cut6 import PINS

    from beliefs.world import registry

    world, roots, published = two_corpus_world(tmp_path)
    pins = replace(PINS, science_contract="science:" + "0" * 64)
    (roots[BETA] / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, BETA, pins)))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert codes(audit.corpora[BETA]) == [("corpus-damaged", "base-pin"), ("profile-mismatch", "base")]


def test_a_recomputation_reaching_a_damaged_corpus_is_unreachable(tmp_path):
    published, _forged, roots, _view, world, epoch = split_verification_world(tmp_path)
    assert published.node is not None
    damage(roots[BETA], "parse-error")

    audit = audit_world(world, epoch, evidence=NO_EVIDENCE, profile=BASE)

    assert ("derivation-unreachable", BETA) in codes(audit.corpora[ALPHA])
    assert any(
        finding.code == "derivation-unreachable"
        and finding.ref == published.node.id
        and finding.detail == BETA
        for finding in audit.corpora[ALPHA]
    )


def test_the_audit_writes_nothing_and_every_code_is_declared(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    damage(roots[BETA], "parse-error")
    before = inventory(world.config.world_root, *roots.values())

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert inventory(world.config.world_root, *roots.values()) == before
    for finding in [*audit.world, *(finding for findings in audit.corpora.values() for finding in findings)]:
        assert finding.code in WORLD_AUDIT_CODES or finding.code in {"semantic-hash-stale", "profile-mismatch"}


def test_a_foreign_profile_stops_every_recomputation(tmp_path, monkeypatch, request):
    from beliefs import audit as audit_module

    world, _roots, published = two_corpus_world(tmp_path)
    profile = request.getfixturevalue("foreign_profile")
    assert profile.base_contract_identity != BASE.base_contract_identity

    def never(*_args, **_kwargs):
        raise AssertionError("a recomputation ran under a base mismatch")

    monkeypatch.setattr(audit_module, "_recompute", never)
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=profile)

    assert codes(audit.corpora[ALPHA]) == [("profile-mismatch", "base")] == codes(audit.corpora[BETA])


def test_corpus_damaged_never_escapes(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    damage(roots[BETA], "id-collision")
    try:
        audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    except CorpusDamaged:  # pragma: no cover - the assertion
        pytest.fail("CorpusDamaged escaped audit_world")


def test_an_attestation_over_a_deleted_endpoint_is_unknown_and_one_over_an_absent_endpoint_is_not(tmp_path):
    from authority import FULL
    from nodes.core.write_plan import DefaultExecutor
    from test_world_build import sample_nodes, slug_for
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    from beliefs.corpus import CorpusWriter

    coverage = (ALPHA, BETA)
    alpha_nodes = sample_nodes(slug_for(ALPHA, coverage))
    beta_nodes = sample_nodes(slug_for(BETA, coverage))
    gone = stored.proposition_node("gone", title="gone", claim={"operator": "affects"})
    kept = beta_nodes[0]
    over_gone = attestation(*sorted((gone.id, alpha_nodes[0].id)))
    over_beta = attestation(*sorted((alpha_nodes[1].id, kept.id)))
    roots = corpora(tmp_path, {ALPHA: (*alpha_nodes, gone, over_gone, over_beta), BETA: beta_nodes})
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    publish(world, coverage, bindings)

    CorpusWriter(roots[ALPHA], DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).delete(gone.id)
    rebuilt = publish(world, coverage, bindings)

    audit = audit_world(world, rebuilt, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert codes(audit.world) == [("attestation-endpoint-unknown", gone.id)]

    make_absent(roots, BETA)
    absent = audit_world(world, rebuilt, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert codes(f for f in absent.world if f.code.startswith("attestation-endpoint")) == [
        ("attestation-endpoint-unknown", gone.id)
    ]
    assert not any(f.ref == over_beta.id for f in absent.world)
    receipt_findings = [f for f in absent.world if f.code == "receipt-unresolvable"]
    assert len(receipt_findings) == 4
    assert {f.detail.partition(":")[0] for f in receipt_findings} == {
        "producer",
        "retraction-enumeration",
        "certification-enumeration",
        "coreference-reduction",
    }


def test_a_healthy_attestation_naming_a_damaged_endpoint_reports_and_the_audit_completes(tmp_path):
    from test_world_build import sample_nodes, slug_for
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    coverage = (ALPHA, BETA)
    alpha_nodes = sample_nodes(slug_for(ALPHA, coverage))
    beta_nodes = sample_nodes(slug_for(BETA, coverage))
    pair = sorted((alpha_nodes[0].id, beta_nodes[0].id))
    roots = corpora(tmp_path, {ALPHA: (*alpha_nodes, attestation(*pair)), BETA: beta_nodes})
    world = world_over(tmp_path, roots)
    published = publish(world, coverage, hold_shipped(world))
    damage(roots[BETA], "parse-error")

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert ("attestation-endpoint-unreachable", beta_nodes[0].id) in codes(audit.world)
    (roots[BETA] / "verification" / "bad.md").unlink()
    repaired = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert not any(f.code.startswith("attestation-endpoint") for f in repaired.world)
    assert repaired.corpora[BETA] == ()


def test_two_sources_sharing_a_secondary_identifier_are_reported(tmp_path):
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    doi_first = stored.source_node(title="paper", identifiers={"doi": "10.1234/abc", "pmid": "42"})
    pmid_only = stored.source_node(title="paper again", identifiers={"pmid": "42"})
    unrelated = stored.source_node(title="other", identifiers={"pmid": "43"})
    assert doi_first.id != pmid_only.id
    roots = corpora(tmp_path, {ALPHA: (doi_first, unrelated), BETA: (pmid_only,)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert codes(audit.world) == [("source-identifier-shared", "pmid:42")]
    (finding,) = audit.world
    assert finding.ref == min(doi_first.id, pmid_only.id) and finding.severity == "warning"


def test_the_audited_epochs_receipts_are_reported_on_the_world(tmp_path):
    from test_world_receipts import document, repackage

    world, _roots, published = two_corpus_world(tmp_path)
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    forged = repackage(world, published, {"producer-receipt.yaml": receipt})

    audit = audit_world(world, forged, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert ("receipt-malformed", "producer: ") in [
        (f.code, f.detail[: len("producer: ")]) for f in audit.world
    ]
    assert audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY).world == ()


def test_a_malformed_attestation_is_a_per_record_finding_and_the_audit_completes(tmp_path):
    from test_world_receipts import hold_shipped, publish
    from test_world_view import address_in

    from beliefs.world.view import open_world_view

    world, roots, published = two_corpus_world(tmp_path)
    broken = attestation(address_in(published, ALPHA), address_in(published, BETA))
    raw_write(roots[ALPHA], broken)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))

    broken.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [address_in(published, ALPHA)]
    raw_write(roots[ALPHA], broken)
    assert broken.id in {node.id for node in open_world_view(world, published).iter_stored()}

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert any(f.ref == broken.id and f.code == "semantic-hash-stale" for f in audit.corpora[ALPHA])
    assert not any(f.ref == broken.id for f in audit.world)



def test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues(tmp_path):
    """Decision 10, `audit_world`'s own seam (Task 8 review finding 3): a
    pre-grammar spec or assessment is named by its own code, never folded
    into `derivation-malformed`, and the exception that names it does not
    stop the loop from reaching a genuine finding for the record after it —
    `self_consistent_forgery`'s verdict-only forgery, part of the same
    published capture. Built inline rather than through
    `split_verification_world`: the pre-grammar records must be present
    **before** `publish`, the same way `split_verification_world`'s own
    forgery is, or `audit_world`'s per-node recomputation loop (over
    `view.iter_stored()`, which only sees what the epoch mapped) never
    reaches them at all — a raw write after `publish` only ever surfaces as
    drift, never as a recomputation finding."""
    from authority import FULL
    from fixtures_cut4 import reopen
    from nodes.core.write_plan import DefaultExecutor
    from profiles import pins_for
    from test_world_receipts import corpora, hold_shipped, publish, world_over
    from verification_fixtures import publish_corpus, self_consistent_forgery

    from beliefs.corpus import CorpusWriter
    from beliefs.identity import v1

    scratch = tmp_path / "scratch"
    writer = CorpusWriter(scratch, DefaultExecutor, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    published = publish_corpus(writer, publish=True)
    assert published.node is not None
    forged = self_consistent_forgery(
        writer, published.node, mutate=lambda facet: facet.__setitem__("verdict", "failed")
    )

    spec_node = stored.stamp_semantic_identity(
        stored._node(
            "analysis-spec", "old", "old",
            {stored.ANALYSIS_SPEC_FACET: {"identity": "old", "projection": v1.encode({
                "target": "proposition:p", "estimand": "prose", "method": "m", "assumptions": "a",
                "falsification": "f", "input_roles": [], "applicability": "prose",
                "interpretation_rule": "r", "equivalence_rule": "e", "parameters": {},
                "nondeterminism": {"variant": "deterministic"}, "rule_bindings": [],
            }).decode()}},
            (),
        )
    )
    assessment_node = stored.stamp_semantic_identity(
        stored._node(
            "assessment", "old", "old",
            {stored.ASSESSMENT_FACET: {
                "spec": "old", "run": "run:x", "proposition": "proposition:p",
                "outcome": "supported", "interpretation_rule": "r", "estimand": "prose",
            }},
            (),
        )
    )
    raw_write(scratch, spec_node)
    raw_write(scratch, assessment_node)

    nodes = tuple(reopen(scratch).iter_stored())
    runs = tuple(node for node in nodes if node.kind == "run")
    roots = corpora(tmp_path, {ALPHA: tuple(node for node in nodes if node.kind != "run"), BETA: runs})
    world = world_over(tmp_path, roots)
    epoch = publish(world, (ALPHA, BETA), hold_shipped(world))

    audit = audit_world(world, epoch, evidence=published.evidence, profile=BASE)

    found = {f.ref: f.code for f in audit.corpora[ALPHA]}
    assert found[spec_node.id] == "spec-pre-grammar"
    assert found[assessment_node.id] == "assessment-pre-grammar"
    assert "derivation-malformed" not in found.values()
    assert any(f.ref == forged.id and f.code == "verification-derivation-contradicted" for f in audit.corpora[ALPHA])


# --- composites and cross-kind succession reached through the world audit ----
# Both loops read a `supersedes` target and a composite's members through the
# world view, where a ref recorded in an absent corpus is `RecordNotPresent`
# rather than `RefError`. The audit reports and never raises (module docstring),
# so each of these arms asserts the whole world audit still completes.


def _composite_across(tmp_path, *, member_slugs=("ab", "bc")):
    """A composite and its two member propositions, built in a scratch corpus so
    the caller can place them in whichever world corpus the arm needs."""
    from test_composite_boundary import _build, _claim, _proposition
    from test_composite_boundary import _writer as _composite_writer

    scratch = _composite_writer(tmp_path / "scratch" / "corpus")
    ab = _proposition(scratch, "ab", _claim("EX:a", "EX:b"))
    bc = _proposition(scratch, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    minted = scratch.add(stored.composite_node(_build(scratch, [ab.id, bc.id]), title="g"))
    view = scratch.read_view
    return view.get(minted.id), {"ab": view.get(ab.id), "bc": view.get(bc.id)}


def _world_of(tmp_path, placement):
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    roots = corpora(tmp_path, placement)
    world = world_over(tmp_path, roots)
    return world, roots, publish(world, tuple(placement), hold_shipped(world))


def test_a_supersedes_edge_into_an_absent_corpus_does_not_discard_the_world_audit(tmp_path):
    """`check_supersedes_kinds` reads its target through the world view. A
    predecessor recorded in a corpus with no carrier answers `RecordNotPresent`,
    which is a `ScienceError` and not a `RecordError`: unguarded, it escapes the
    per-record loop and takes every finding already collected with it."""
    from nodes.core.relations import Relation

    predecessor = stored.proposition_node("beta-ab", title="beta ab", claim={"operator": "affects"})
    successor = stored.proposition_node("alpha-ab", title="alpha ab", claim={"operator": "affects"})
    successor.relations.append(Relation(source=successor.id, predicate=stored.SUPERSEDES, target=predecessor.id))
    world, roots, published = _world_of(tmp_path, {ALPHA: (successor,), BETA: (predecessor,)})
    make_absent(roots, BETA)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert ("corpus-absent", "") in codes(audit.corpora[BETA])
    assert ("supersession-target-missing", predecessor.id) in codes(audit.corpora[ALPHA])
    assert not any(f.code == "supersedes-cross-kind" for f in audit.corpora[ALPHA])


def test_a_composite_member_in_an_absent_corpus_is_unchecked_not_a_raise(tmp_path):
    """A member recorded elsewhere is not a member that is gone: the audit
    reports neither `composite-member-unresolvable` nor a raise, and the record's
    derivation is simply unchecked (module docstring, third case)."""
    from beliefs.audit import check_composite
    from beliefs.world.view import open_world_view

    composite, members = _composite_across(tmp_path)
    world, roots, published = _world_of(
        tmp_path, {ALPHA: (composite, members["ab"]), BETA: (members["bc"],)}
    )
    make_absent(roots, BETA)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert not any(f.code.startswith("composite-") for f in audit.corpora[ALPHA])
    view = open_world_view(world, published, on_damage="report")
    outcome = check_composite(view, view.get(composite.id), profile=WITH_BIOLOGY)
    assert outcome.checked is False and outcome.contradiction is None
    assert members["bc"].id in outcome.reason and BETA in outcome.reason


def test_an_absent_composite_member_does_not_hide_a_dangling_sibling(tmp_path):
    composite, members = _composite_across(tmp_path)
    first, second = (relation.target for relation in composite.relations if relation.predicate == stored.COMPOSES)
    by_id = {member.id: member for member in members.values()}
    world, roots, published = _world_of(tmp_path, {ALPHA: (composite,), BETA: (by_id[first],)})
    make_absent(roots, BETA)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert second != first
    assert [(finding.code, finding.ref) for finding in audit.corpora[ALPHA]] == [
        ("composite-member-unresolvable", composite.id)
    ]


def test_a_dangling_composite_is_reported_through_the_world_audits_recompute(tmp_path):
    """The U7 arm `beliefs-6776d3` names: `check_composite` reached through
    `audit_world`'s `_recompute` dispatch rather than through `audit_corpus`."""
    composite, members = _composite_across(tmp_path)
    world, _roots, published = _world_of(
        tmp_path, {ALPHA: (composite, members["ab"]), BETA: (stored.dataset_node(title="beta", resources=pinned("beta")),)}
    )

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert [(f.code, f.ref) for f in audit.corpora[ALPHA]] == [("composite-member-unresolvable", composite.id)]
    assert audit.corpora[BETA] == ()


def test_a_mismatching_spec_target_is_reported_through_the_world_audits_recompute(tmp_path):
    from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules
    from profiles import pins_for
    from test_audit import OTHER_CLAIM
    from test_world_receipts import hold_shipped, publish, world_over

    from beliefs.projection import project_claim
    from beliefs.spec import freeze
    from beliefs.world import registry

    root = tmp_path / "corpus"
    root.mkdir()
    (root / "corpus.yaml").write_bytes(
        registry.manifest_bytes(registry.CorpusManifest(2, ALPHA, pins_for(TESTING_PROFILE)))
    )
    target = stored.proposition_node("p-other", title="other", claim=project_claim(OTHER_CLAIM))
    spec = stored.analysis_spec_node(freeze(spec_draft(target=target.id), held_rules=spec_rules()))
    raw_write(root, target)
    raw_write(root, spec)
    world = world_over(tmp_path, {ALPHA: root})
    published = publish(world, (ALPHA,), hold_shipped(world))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=TESTING_PROFILE)

    assert [(finding.code, finding.ref) for finding in audit.corpora[ALPHA]] == [
        ("spec-target-contradicted", spec.id)
    ]


def test_a_raw_written_snapshot_retraction_naming_nothing_retained_is_reported_from_captured_records(tmp_path):
    """BI-6: the epoch predates the raw write, so the record is unmapped; iter_stored would miss it."""
    from fixtures_cut4 import raw_write
    from test_snapshot_retraction import S, snapshot_retraction
    from test_world_receipts import published_world

    from beliefs.audit import NO_EVIDENCE, audit_world
    from beliefs.corpus import ReadView, corpus_check

    world, _b, roots, published = published_world(tmp_path, (ALPHA,))
    node = snapshot_retraction(S)                       # S is retained nowhere
    raw_write(roots[ALPHA], node)
    report = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert ("retraction-target-invalid", node.id) in [(f.code, f.ref) for f in report.world]
    assert not [f for f in corpus_check(ReadView.opened_at(roots[ALPHA]), BASE) if f.ref == node.id]


def test_an_unreadable_retained_inventory_is_a_finding_and_the_audit_returns(tmp_path):
    from fixtures_cut4 import raw_write
    from test_snapshot_retraction import S, snapshot_retraction
    from test_world_receipts import published_world

    from beliefs.audit import NO_EVIDENCE, audit_world

    world, _b, roots, published = published_world(tmp_path, (ALPHA,))
    (world.config.world_root / "epochs" / "stray").write_text("not a carrier", encoding="utf-8")
    clean = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)      # no snapshot arm: no new finding
    assert "retained-epochs-unreadable" not in [f.code for f in clean.world]
    node = snapshot_retraction(S)
    raw_write(roots[ALPHA], node)
    report = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    codes_ = [f.code for f in report.world]
    assert "retained-epochs-unreadable" in codes_ and ("retraction-target-invalid", node.id) not in [(f.code, f.ref) for f in report.world]
