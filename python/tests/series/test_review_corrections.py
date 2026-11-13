"""Corrupt neighbours and missing bytes cannot erase established audit facts."""

from dataclasses import replace

import pytest
from fixtures_cut4 import path_for, raw_write
from test_world_receipts import hold_shipped, publish, world_over

from beliefs import audit, stored
from beliefs.errors import SemanticHashMissing, SemanticHashStale
from beliefs.estimand import MeasuredBinding
from beliefs.replay import CONTENT_EQUALITY
from beliefs.verify import AssessmentVerification, build_verification, publication_node
from beliefs.world.view import open_world_view

from .test_chains import chain_profile as chain_profile  # noqa: PLC0414
from .test_chains import native_verification_case
from .test_portability import portable as portable  # noqa: PLC0414
from .test_portability import run_publication, writer_at


def verification(original, replayed, evidence, profile, records):
    value = build_verification(
        original,
        replayed,
        specs=evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + profile.base_contract_identity,
        epoch="fixture",
        series_evidence=evidence.series_evidence,
        profile=profile,
        records=records,
    )
    assert isinstance(value, AssessmentVerification)
    return value


@pytest.mark.parametrize("neighbour", ["ancestor", "producer", "retraction"])
@pytest.mark.parametrize("holder", ["same", "other"])
@pytest.mark.parametrize("stamp", ["missing", "stale"])
def test_native_world_standing_cannot_consume_malformed_neighbours(chain_profile, tmp_path, neighbour, holder, stamp):
    import lineage_fixtures as lineage

    _case, writer, records, dataset, original, replayed, evidence = native_verification_case(chain_profile, tmp_path)
    derived = verification(original, replayed, evidence, chain_profile, records)
    assert derived.verdict == "passed"
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    table = writer.read_view.get(dataset)
    ancestor = table.facets[stored.LINEAGE_BASIS_FACET]["routes"][0]["ancestor"]
    primary = tmp_path / "corpus"
    if neighbour == "retraction":
        target = stored.stamp_semantic_identity(
            lineage.route_retraction(table, "route:series-producer", "retire-series")
        )
        raw_write(primary, target)
    else:
        target = writer.read_view.get(ancestor if neighbour == "ancestor" else "run:series-producer")
    roots = {writer.read_view.corpus_id: primary}
    if holder == "other":
        foreign_root = tmp_path / "foreign"
        foreign = writer_at(foreign_root, chain_profile)
        if neighbour == "retraction":
            raw_write(foreign_root, target)
        else:
            foreign.add(target)
        path_for(primary, target.id).unlink()
        roots[foreign.read_view.corpus_id] = foreign_root
        target_root = foreign_root
    else:
        target_root = primary
    world = world_over(tmp_path / "world", roots)
    epoch = publish(world, tuple(roots), hold_shipped(world))
    damaged = target.model_copy(deep=True)
    if stamp == "missing":
        del damaged.facets["semantic-identity"]
    else:
        damaged.facets["semantic-identity"]["digest"] = "f" * 64
    raw_write(target_root, damaged)
    captured = open_world_view(world, epoch)
    with pytest.raises((SemanticHashMissing, SemanticHashStale)):
        captured.get(target.id)
    result = audit.check_verification(
        captured,
        publication_node(derived, assessment_ref="assessment:native"),
        evidence=evidence,
        profile=chain_profile,
    )
    assert not result.checked
    assert result.contradiction is None
    assert target.id in result.reason


def test_valid_retired_native_route_is_still_a_known_contradiction(chain_profile, tmp_path):
    import lineage_fixtures as lineage

    _case, writer, records, dataset, original, replayed, evidence = native_verification_case(chain_profile, tmp_path)
    derived = verification(original, replayed, evidence, chain_profile, records)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    raw_write(
        tmp_path / "corpus",
        stored.stamp_semantic_identity(
            lineage.route_retraction(writer.read_view.get(dataset), "route:series-producer", "retire-series")
        ),
    )
    world = world_over(tmp_path / "world", {writer.read_view.corpus_id: tmp_path / "corpus"})
    epoch = publish(world, (writer.read_view.corpus_id,), hold_shipped(world))
    result = audit.check_verification(
        open_world_view(world, epoch),
        publication_node(derived, assessment_ref="assessment:native"),
        evidence=evidence,
        profile=chain_profile,
    )
    assert result.checked and result.contradiction is not None


@pytest.mark.parametrize("availability", ["absent", "unreadable"])
def test_missing_series_bytes_do_not_hide_a_known_assessment_mismatch(portable, availability, tmp_path):
    p = portable
    changed = p.assessment.model_copy(deep=True)
    changed.facets[stored.ASSESSMENT_FACET]["outcome"] = "refuted"
    changed = stored.stamp_semantic_identity(changed)
    supplied = p.case.evidence() if availability == "unreadable" else None
    if availability == "unreadable":
        p.case.buffers.clear()
    result = audit.check_assessment(
        p.writer.read_view, changed, evidence=replace(p.evidence, series_evidence=supplied), profile=p.profile
    )
    assert result.checked and result.contradiction is not None
    assert "outcome" in result.contradiction.detail

    from beliefs.errors import ImportRefused

    target = writer_at(tmp_path / "contradicted-import", p.profile)
    members = [changed if node.id == changed.id else node for node in p.writer.read_view.iter_stored()]
    with pytest.raises(ImportRefused):
        target.import_bundle(
            members,
            evidence=replace(p.evidence, series_evidence=supplied),
            observer="fixture",
            instrument="fixture",
            opened_at="2026-11-13T00:00:00Z",
            closed_at="2026-11-13T00:00:01Z",
        )
    assert not target.read_view.holds(changed.id)


@pytest.mark.parametrize("mismatch", ["result", "assessment-identity"])
def test_missing_series_bytes_do_not_hide_a_definite_verification_mismatch(portable, mismatch):
    p = portable
    replayed = replace(p.closure, occurrence=replace(p.closure.occurrence, event_token="mixed-evidence-replay"))
    complete = replace(
        p.evidence, held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}, series_evidence=p.case.evidence()
    )
    passed = verification(p.closure, replayed, complete, p.profile, p.case.records)
    if mismatch == "result":
        outputs = replayed.result.outputs
        replayed = replace(
            replayed, result=replace(replayed.result, outputs=((outputs[0][0], "sha256:" + "f" * 64), *outputs[1:]))
        )
    # An imported legacy verdict need not carry the comparison report.
    node = stored.verification_node(
        "mixed-evidence",
        title="Claimed agreement",
        assessment=passed.assessment if mismatch == "result" else "f" * 64,
        assessment_ref=p.assessment.id,
        scope=passed.scope,
        verdict="passed",
        derivation=(stored.typed_ref("run", p.closure.address()), stored.typed_ref("run", replayed.address())),
    )
    p.writer.add(run_publication(replayed))
    result = audit.check_verification(
        p.writer.read_view, node, evidence=replace(complete, series_evidence=None), profile=p.profile
    )
    assert result.checked and result.contradiction is not None
    assert ("verdict" if mismatch == "result" else "assessment identity") in result.contradiction.detail


def test_known_series_contradiction_survives_other_target_unavailability(portable, tmp_path):
    from fixtures_cut3 import typed_estimand

    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.evidence import SeriesEvidence

    from .fixtures import raw_object
    from .test_authoring import author_case
    from .test_portability import persist_case

    p = portable
    case, initial = author_case(p.profile)
    response = initial.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    descriptor = raw_object(case.buffers[response.series.resource.split(":")[1]])
    selected = case.view(descriptor["table"], [0, 2], selection_procedure=case.procedure())
    value = typed_estimand(
        profile=p.profile,
        records=case.records,
        functional=initial.functional,
        bindings={**initial.bindings, "response": replace(response, series=series_ref_from_projection(selected))},
        series_evidence=case.evidence(),
    )
    other = persist_case(case, value, p.profile, tmp_path / "other-target")
    p.case.records.nodes.update(case.records.nodes)
    for row in case.records.nodes.values():
        if not p.writer.read_view.holds(row.id):
            p.writer.add(row)
    p.writer.add(run_publication(other.closure))
    buffers = {**p.case.buffers, **case.buffers}
    stores = p.case.evidence().stores
    supplied = SeriesEvidence(
        {store: lambda path, limit: buffers[path] for store in stores},
        {**p.case.evidence().locations, **case.evidence().locations},
    )
    specs = {**p.evidence.specs, **other.evidence.specs}
    evidence = replace(
        p.evidence, specs=specs, held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}, series_evidence=supplied
    )
    passed = verification(p.closure, other.closure, evidence, p.profile, p.case.records)
    assert passed.verdict == "passed"
    response_a = p.value.bindings["response"]
    assert isinstance(response_a, MeasuredBinding) and response_a.series is not None
    buffers[response_a.series.resource.split(":")[1]] = b"contradicting descriptor"
    del buffers[selected["resource"].split(":")[1]]
    result = audit.check_verification(
        p.writer.read_view,
        publication_node(passed, assessment_ref=p.assessment.id),
        evidence=evidence,
        profile=p.profile,
    )
    assert result.checked and result.contradiction is not None
    assert "verdict" in result.contradiction.detail


def test_unrelated_bad_stamp_does_not_invalidate_native_standing(chain_profile, tmp_path):
    import lineage_fixtures as lineage

    _case, writer, records, _dataset, original, replayed, evidence = native_verification_case(chain_profile, tmp_path)
    derived = verification(original, replayed, evidence, chain_profile, records)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    unrelated = writer.add(lineage.acquired("unrelated-record"))
    world = world_over(tmp_path / "world", {writer.read_view.corpus_id: tmp_path / "corpus"})
    epoch = publish(world, (writer.read_view.corpus_id,), hold_shipped(world))
    del unrelated.facets["semantic-identity"]
    raw_write(tmp_path / "corpus", unrelated)
    result = audit.check_verification(
        open_world_view(world, epoch),
        publication_node(derived, assessment_ref="assessment:native"),
        evidence=evidence,
        profile=chain_profile,
    )
    assert result.checked and result.contradiction is None


@pytest.mark.parametrize("mismatch", ["scope", "report"])
def test_missing_series_bytes_preserve_independent_full_report_checks(portable, mismatch):
    from beliefs.identity import v1
    from beliefs.verify import COMPARISON_REPORT_DOMAIN, RUN_VERIFICATION_DOMAIN, decode_verification

    p = portable
    replayed = replace(p.closure, occurrence=replace(p.closure.occurrence, event_token="full-report-replay"))
    evidence = replace(
        p.evidence, held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}, series_evidence=p.case.evidence()
    )
    passed = verification(p.closure, replayed, evidence, p.profile, p.case.records)
    node = publication_node(passed, assessment_ref=p.assessment.id)
    decoded = decode_verification(node)
    assert decoded is not None
    basis = decoded.basis()
    facet = node.facets[stored.VERIFICATION_FACET]
    if mismatch == "scope":
        facet["scope"] = "clean-environment" if passed.scope != "clean-environment" else "same-environment"
        basis["scope"] = facet["scope"]
    else:
        facet["report"]["receipts"][0] = "f" * 64
        basis["report"] = v1.digest(COMPARISON_REPORT_DOMAIN, facet["report"])
    # This is coherent imported wire data, rather than a malformed identity.
    identity = stored.typed_ref("verification", v1.digest(RUN_VERIFICATION_DOMAIN, basis))
    node = node.model_copy(
        update={"id": identity, "relations": [r.model_copy(update={"source": identity}) for r in node.relations]}
    )
    assert decode_verification(node) is not None
    p.writer.add(run_publication(replayed))
    result = audit.check_verification(
        p.writer.read_view, node, evidence=replace(evidence, series_evidence=None), profile=p.profile
    )
    assert result.checked and result.contradiction is not None
    assert mismatch in result.contradiction.detail
