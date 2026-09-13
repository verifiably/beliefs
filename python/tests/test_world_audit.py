"""The world audit over a capture (slice 3 design §5)."""

from __future__ import annotations

from pathlib import Path

import pytest
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
    node = stored.dataset_node(slug, title=f"dataset {slug}")
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
    raw_write(roots[BETA], stale("remainder"))
    damage(roots[BETA], kind)

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
    published, _forged, roots, _view, world, epoch = split_verification_world(tmp_path, include_world=True)
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
