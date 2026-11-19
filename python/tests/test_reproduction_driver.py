"""Unit tests for the mm30 reproduction driver under `tools/reproduction/`.

The driver is throwaway by declaration; these tests guard the bridges it
crosses between kernel spellings and the pure functions its steps rely on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fixtures_cut3 import freeze_context
from reproduction import answers, findings

from beliefs.belief import Belief, NoBelief
from beliefs.policy import PolicyBinding


def test_a_finding_class_outside_the_closed_set_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(findings.paths, "FINDINGS", tmp_path / "f.jsonl")
    with pytest.raises(ValueError):
        findings.record(1, "oops", "reason")


def test_answer_payload_distinguishes_beliefs_by_value_and_digest():
    binding = PolicyBinding(rule="science.belief.v1", implementation="impl-1")
    one = answers.payload(Belief(1, "sha256:" + "a" * 64, binding))
    other = answers.payload(Belief(99, "sha256:" + "b" * 64, binding))
    assert one != other and one["value"] == 1 and other["belief_input_digest"].endswith("b" * 64)
    assert answers.payload(NoBelief("no-eligible-assessment")) == {
        "kind": "NoBelief",
        "reason": "no-eligible-assessment",
        "detail": "",
    }


def test_rank_prefers_empirical_locally_held_small_targets():
    from reproduction.select_target import rank

    a = {"proposition_id": "p:a", "claim_layer": "causal_effect", "dataset_bytes": 2_000_000, "empirical_lines": 3}
    b = {"proposition_id": "p:b", "claim_layer": "structural_claim", "dataset_bytes": 1_000, "empirical_lines": 5}
    c = {"proposition_id": "p:c", "claim_layer": "empirical_regularity", "dataset_bytes": 50_000, "empirical_lines": 1}
    ordered = [r["proposition_id"] for r in rank([a, b, c])]
    assert ordered == ["p:c", "p:a", "p:b"]


def test_dataset_record_id_equals_its_content_address():
    from hashlib import sha256

    from reproduction.hold import dataset_record

    node, address = dataset_record(name="expr.tsv", digest="sha256:" + "c" * 64, title="t", accession="GSE179929")
    assert node.id == address == "dataset:sha256:" + sha256(("sha256:" + "c" * 64 + "\n").encode()).hexdigest()


def test_the_hold_step_declares_a_locator_and_the_bound_actor():
    from reproduction.authority import ACTOR
    from reproduction.hold import dataset_record

    node, _ = dataset_record(name="f.gz", digest="sha256:" + "c" * 64, title="dataset:gse179929", accession="GSE179929")
    assert node.facets["empirical-observation"] == {"locator": "accession:GSE179929", "attested_by": ACTOR}


def test_outcome_digests_cover_exactly_the_three_outcomes():
    from hashlib import sha256

    from reproduction.spec import OUTCOME_DIGESTS

    assert set(OUTCOME_DIGESTS.values()) == {"supported", "refuted", "inconclusive"}
    assert OUTCOME_DIGESTS["sha256:" + sha256(b"supported\n").hexdigest()] == "supported"


def _assoc():
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "tools" / "reproduction" / "analysis" / "assoc.py"
    spec = importlib.util.spec_from_file_location("assoc", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


def _matrix(tmp_path, samples, rows, *, gz=False):
    """A wide matrix: header of sample ids, one row per feature."""
    import gzip

    text = "\t".join(["id", *samples]) + "\n" + "".join("\t".join(r) + "\n" for r in rows)
    p = tmp_path / ("m.tsv.gz" if gz else "m.tsv")
    if gz:
        with gzip.open(p, "wt") as out:
            out.write(text)
    else:
        p.write_text(text)
    return p


def test_assoc_refuses_a_missing_row(tmp_path):
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="row"):
        assoc.load(_matrix(tmp_path, ["s1_NDMM", "s2_PD"], [["g1", "1", "2"]]), value_row="g9")


def test_assoc_refuses_non_finite_values(tmp_path):
    assoc = _assoc()
    samples = [f"s{i}_{'NDMM' if i % 2 else 'PD'}" for i in range(6)]
    with pytest.raises(assoc.MalformedInput, match="finite"):
        assoc.load(_matrix(tmp_path, samples, [["g1", "nan", "2", "3", "4", "5", "6"]]), value_row="g1")


def test_assoc_refuses_a_sample_without_a_group_token(tmp_path):
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="group token"):
        assoc.load(_matrix(tmp_path, ["s1_NDMM", "s2"], [["g1", "1", "2"]]), value_row="g1")


def test_assoc_refuses_a_group_below_the_floor(tmp_path):
    assoc = _assoc()
    samples = ["s1_NDMM", "s2_NDMM", "s3_NDMM", "s4_PD"]
    groups = assoc.load(_matrix(tmp_path, samples, [["g1", "1", "2", "3", "4"]]), value_row="g1")
    with pytest.raises(assoc.MalformedInput, match="at least"):
        assoc.decide(groups, positive_level="NDMM")


def test_assoc_refuses_a_positive_level_that_is_absent(tmp_path):
    assoc = _assoc()
    samples = [f"s{i}_{'NDMM' if i % 2 else 'PD'}" for i in range(1, 11)]
    groups = assoc.load(_matrix(tmp_path, samples, [["g1", *[str(i) for i in range(1, 11)]]]), value_row="g1")
    with pytest.raises(assoc.MalformedInput, match="positive level"):
        assoc.decide(groups, positive_level="zzz")


def test_assoc_refuses_more_than_two_levels(tmp_path):
    assoc = _assoc()
    groups = {"NDMM": [1, 2, 3], "PD": [4, 5, 6], "other": [7, 8, 9]}
    with pytest.raises(assoc.MalformedInput, match="two levels"):
        assoc.decide(groups, positive_level="NDMM")


def test_assoc_supported_when_positive_level_is_PDgher_reading_gzip(tmp_path):
    assoc = _assoc()
    samples = [f"h{i}_PD" for i in range(8)] + [f"l{i}_NDMM" for i in range(8)]
    values = [str(10 + i) for i in range(8)] + [str(i) for i in range(8)]
    groups = assoc.load(_matrix(tmp_path, samples, [["other", *["0"] * 16], ["g1", *values]], gz=True), value_row="g1")
    outcome, _effect, z, p, n = assoc.decide(groups, positive_level="PD")
    assert outcome == "supported" and z > 0 and p < 0.05 and n == 16


def test_spec_record_carries_a_fresh_semantic_stamp():
    from decimal import Decimal

    from fixtures_cut3 import typed_applicability, typed_estimand
    from reproduction import spec as spec_module

    from beliefs import stored
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    draft = SpecDraft(
        target="proposition:p",
        estimand=typed_estimand(),
        method="m",
        assumptions="a",
        falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64, mode="observation"),),
        applicability=typed_applicability(),
        interpretation_rule=spec_module.INTERPRETATION_RULE,
        equivalence_rule=spec_module.EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
        registers=(),
        standing="empirical",
        model=None,
    )
    node = spec_module.spec_record(
        freeze(draft, held_rules=spec_module.held_rules(), **freeze_context(spec_module.INTERPRETATION_RULE))
    )
    assert node.kind == "analysis-spec"
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)


def test_classify_scope_attributes_only_same_environment_to_the_host():
    from reproduction.run import classify_scope

    assert classify_scope("clean-environment", conforming=(True, True), recipes_agree=True) == "none"
    assert classify_scope("same-environment", conforming=(True, True), recipes_agree=True) == "host"
    assert classify_scope("not-certified", conforming=(True, False), recipes_agree=True) == "defect"
    assert classify_scope("not-certified", conforming=(True, True), recipes_agree=False) == "corpus-work"


def test_10b_reads_the_report_from_the_corpus_with_no_in_process_spec(tmp_path, monkeypatch):
    """The 10b checks: the report, scope and verdict are read; the only
    in-process input is the rule implementations; `spec.frozen()` is not
    reachable. The negative: a report-less record reports false."""
    from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, spec_rules
    from reproduction import close, rederive, spec
    from test_stored import _testing_writer
    from verification_fixtures import publish_corpus

    from beliefs import stored
    from beliefs.projection import project_claim
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.verify import publication_node

    writer = _testing_writer(tmp_path / "corpus")
    # The stored spec's estimand is `spec_draft`'s default, against
    # `TESTING_CLAIM` (`frozen_for`, via `typed_estimand`); the boundary now
    # requires the target proposition's own claim to agree, so
    # the proposition carries that same claim rather than
    # `publish_corpus`'s bare `{"operator": "affects"}` default.
    published = publish_corpus(writer, claim=project_claim(TESTING_CLAIM))
    spec_node = writer.read_view.get(stored.analysis_spec_node(published.frozen).id)
    node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))

    def unavailable():
        raise RuntimeError("the in-process spec is unavailable")

    monkeypatch.setattr(spec, "frozen", unavailable)
    monkeypatch.setattr(rederive, "profile", lambda: TESTING_PROFILE)
    interpretation = spec_rules()[published.frozen.interpretation_rule]
    monkeypatch.setattr(spec, "EQUIVALENCE", CONTENT_EQUALITY)
    monkeypatch.setattr(spec, "INTERPRETATION", interpretation)
    st = {"verification_ref": node.id, "spec_ref": spec_node.id}
    view = writer.read_view
    from dataclasses import replace

    from beliefs.series.evidence import SeriesEvidence

    supplied = SeriesEvidence({}, {})
    actual_verification = rederive.build_verification
    forwarded = []

    def verification(*args, **kwargs):
        assert kwargs["profile"] is TESTING_PROFILE
        assert kwargs["records"].holds(published.assessment.id)
        forwarded.append(kwargs["series_evidence"])
        return actual_verification(*args, **kwargs)

    monkeypatch.setattr(rederive, "build_verification", verification)
    report = rederive.reconstruct(
        view, st, replace(close.evidence_for(view, TESTING_PROFILE), series_evidence=supplied)
    )
    assert forwarded == [supplied]
    assert report["comparison_report_stored"] is True
    assert report["scope_equal"] is True and report["verdict_equal"] is True and report["report_identity_equal"] is True
    assert report["inputs"]["in_process"] == ["interpretation and equivalence RuleImplementations"]
    assert report["spec_restored_identity_matches_run"] is True
    assert report["audit_check"] == {"checked": True, "reason": "", "contradiction": None}
    legacy = writer.add(
        stored.verification_node(
            "legacy",
            title="legacy",
            assessment=published.derived.assessment,
            assessment_ref=published.assessment.id,
            scope=published.derived.scope,
            verdict=published.derived.verdict,
            derivation=(
                stored.typed_ref("run", published.derived.original),
                stored.typed_ref("run", published.derived.replayed),
            ),
        )
    )
    negative = rederive.reconstruct(
        writer.read_view, {**st, "verification_ref": legacy.id}, close.evidence_for(writer.read_view, TESTING_PROFILE)
    )
    assert negative["comparison_report_stored"] is False and "scope_read" not in negative


def test_close_evidence_for_raises_on_a_stored_spec_that_does_not_restore(tmp_path):
    """`evidence_for` fails loud rather than silently narrowing the specs a
    recomputation sees : a raw-written analysis-spec
    record whose text disagrees with its own identity must stop 10b cold,
    never drop out of `stored_specs`' mapping unnoticed."""
    from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules
    from fixtures_cut4 import raw_write, reopen
    from reproduction import close
    from test_relocation import _writer

    from beliefs import stored
    from beliefs.spec import freeze

    writer = _writer(tmp_path / "corpus")
    frozen = freeze(spec_draft(), held_rules=spec_rules(), **freeze_context())
    forged = stored.analysis_spec_node(frozen).model_copy(update={"id": "analysis-spec:forged"})
    forged.facets[stored.ANALYSIS_SPEC_FACET]["identity"] = "forged"
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET][
        "projection"
    ].replace("fit the model", "fit another model")
    raw_write(writer.root, stored.stamp_semantic_identity(forged))
    with pytest.raises(RuntimeError, match="analysis-spec:forged"):
        close.evidence_for(reopen(writer.root), TESTING_PROFILE)


# Retired with the driver's contract layer (beliefs-d64969, ruling P11): the
# row plan, the mm30 contract's held-list bindings and succession chain, and the
# two held-list snapshot checks read the v1 mm30 documents or the v1
# `VocabularyBinding`, neither of which exists under base v2. beliefs-709bd9's
# recreate restores them against the biology v2 genesis and the mm30
# corpus-local v2 contract.


def test_concept_lines_are_canonical_sorted_and_terminated(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    (root / "b.md").write_text("---\nid: concept:b-thing\nkind: concept\n---\n")
    (root / "a.md").write_text("---\nid: concept:a-thing\nkind: concept\n---\n")
    assert concept_lines(tmp_path) == b"concept:a-thing\nconcept:b-thing\n"


def test_a_held_list_is_written_sorted_canonical_and_newline_terminated(tmp_path, monkeypatch):
    from hashlib import sha256

    from reproduction import lists, paths

    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

    monkeypatch.setattr(paths, "WORK", tmp_path)
    address, path = lists.hold_list("levels", ["level:pd", "level:ndmm"])
    assert path == tmp_path / "mm30-stage-levels.txt"
    assert path.read_bytes() == b"level:ndmm\nlevel:pd\n"
    # The address the contract's `stage-level` sort binds is the content
    # address of exactly those bytes under that resource name.
    declared = DatasetDeclaration(
        resources=(
            ResourceDeclaration(name="mm30-stage-levels.txt", digest="sha256:" + sha256(path.read_bytes()).hexdigest()),
        )
    )
    assert address == dataset_address(declared)


def test_a_non_canonical_list_term_refuses_and_writes_nothing(tmp_path, monkeypatch):
    from reproduction import lists, paths

    monkeypatch.setattr(paths, "WORK", tmp_path)
    with pytest.raises(ValueError, match="canonical"):
        lists.hold_list("levels", ["level:ndmm", "level:cafe\u0301"])
    assert not (tmp_path / "mm30-stage-levels.txt").exists()


def test_a_non_canonical_concept_id_refuses(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    (root / "x.md").write_text("---\nid: 'concept:café-thing'\nkind: concept\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canonical"):
        concept_lines(tmp_path)


# Re-pinned 2026-09-15: `estimand` and `applicability`
# moved from prose to typed members, so the digest they enter into moved too.
# Re-pinned 2026-11-09 (beliefs-d64969): the spec is `science.spec.v2` with a
# canonical `registers` field, and its estimand names a role of a
# `science.claim.v2` claim. The rule bindings this test actually guards are
# unchanged both times, per the assertion above.
PINNED_IDENTITY = "e58bebf472ba4ee89e83d895e5c0fce1b4be34faaf05c2f96de5041c83812e0a"


def test_the_driver_binds_the_kernel_rules_under_its_own_identities():
    from decimal import Decimal

    from fixtures_cut3 import typed_applicability, typed_estimand
    from reproduction import spec as spec_module

    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.rules import OUTCOME_FILE_V1
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    held = spec_module.held_rules()
    assert held[spec_module.INTERPRETATION_RULE] is OUTCOME_FILE_V1
    assert held[spec_module.EQUIVALENCE_RULE] is CONTENT_EQUALITY
    draft = SpecDraft(
        target="proposition:p",
        estimand=typed_estimand(),
        method="m",
        assumptions="a",
        falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64, mode="observation"),),
        applicability=typed_applicability(),
        interpretation_rule=spec_module.INTERPRETATION_RULE,
        equivalence_rule=spec_module.EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
        registers=(),
        standing="empirical",
        model=None,
    )
    frozen = freeze(draft, held_rules=held, **freeze_context(spec_module.INTERPRETATION_RULE))
    # The pairs the 2026-09-05 record digests, unchanged: identity-neutral by construction.
    assert tuple((b.rule, b.implementation) for b in frozen.rule_bindings) == (
        ("content-identity-equality/v1", "impl-eq-1"),
        ("mm30-reproduction/outcome-file/v1", "impl-outcome-file-1"),
    )
    assert frozen.identity != PINNED_IDENTITY  # evidence mode, target and estimator procedure change the spec identity


def _phf19_inputs_case():
    target = {
        "subject": "concept:disease-stage",
        "predicate": "affects",
        "object": "protein:PHF19",
        "polarity": "positive",
        "dataset_id": "dataset:gse179929",
        "dataset_path": "/held/GSE179929_gene_tpm.txt.gz",
    }
    declaration = {
        "crosswalks": {"dataset:gene-crosswalk-hgnc": {"key": "ensgene", "symbol": "symbol"}},
        "groups": {"concept:disease-stage": {"separator": "_", "level_order": ["NDMM", "PD"]}},
    }
    dataset_front = {
        "id": "dataset:gse179929",
        "identity_context": {
            "molecular_ids": {"gene": {"namespace": "ensembl", "registry": "dataset:gene-crosswalk-hgnc"}}
        },
    }
    header = ["Sample_ID", "P4_S1_NDMM", "P4_S2_PD", "P8_S1_PD"]
    crosswalk = [
        {"ensgene": "ENSG00000000003", "symbol": "TSPAN6"},
        {"ensgene": "ENSG00000119403", "symbol": "PHF19"},
    ]
    return target, declaration, dataset_front, header, crosswalk


def test_analysis_inputs_are_derived_from_the_selection_the_record_the_header_and_the_declaration():
    from reproduction.analysis_inputs import analysis_inputs

    assert analysis_inputs(*_phf19_inputs_case()) == {
        "held_file": "GSE179929_gene_tpm.txt.gz",
        "value_row": "ENSG00000119403",
        "value_row_symbol": "PHF19",
        "group_separator": "_",
        "positive_level": "PD",
    }


def test_positive_level_follows_polarity_over_the_declared_level_order():
    from reproduction.analysis_inputs import InputsRefused, positive_level_for

    assert positive_level_for("positive", ["NDMM", "PD"]) == "PD"
    assert positive_level_for("negative", ["NDMM", "PD"]) == "NDMM"
    with pytest.raises(InputsRefused, match="unsigned"):
        positive_level_for("unsigned", ["NDMM", "PD"])


def test_header_levels_must_equal_the_declared_order_and_every_sample_must_carry_a_token():
    from reproduction.analysis_inputs import InputsRefused, levels_in

    assert levels_in(["Sample_ID", "P4_S1_NDMM", "P4_S2_PD"], "_") == ["NDMM", "PD"]
    with pytest.raises(InputsRefused, match="P4S1NDMM"):
        levels_in(["Sample_ID", "P4S1NDMM"], "_")
    target, declaration, front, _header, crosswalk = _phf19_inputs_case()
    from reproduction.analysis_inputs import analysis_inputs

    with pytest.raises(InputsRefused, match="MGUS"):
        analysis_inputs(target, declaration, front, ["Sample_ID", "P1_S1_NDMM", "P1_S2_MGUS"], crosswalk)


def test_the_crosswalk_must_name_the_symbol_exactly_once():
    from reproduction.analysis_inputs import InputsRefused, row_for_symbol

    rows = [{"ensgene": "ENSG1", "symbol": "PHF19"}, {"ensgene": "ENSG2", "symbol": "PHF19"}]
    with pytest.raises(InputsRefused, match="2 rows"):
        row_for_symbol(rows, "PHF19", key="ensgene", symbol_column="symbol")
    with pytest.raises(InputsRefused, match="no row"):
        row_for_symbol(rows[:1], "EZH2", key="ensgene", symbol_column="symbol")


def test_analysis_inputs_refuse_a_dataset_whose_registry_is_not_declared():
    from reproduction.analysis_inputs import InputsRefused, analysis_inputs

    target, declaration, front, header, crosswalk = _phf19_inputs_case()
    undeclared = {**declaration, "crosswalks": {}}
    with pytest.raises(InputsRefused, match="dataset:gene-crosswalk-hgnc"):
        analysis_inputs(target, undeclared, front, header, crosswalk)
    unkeyed = {**front, "identity_context": {}}
    with pytest.raises(InputsRefused, match="molecular_ids"):
        analysis_inputs(target, declaration, unkeyed, header, crosswalk)


def test_analysis_inputs_refuse_a_target_that_is_not_one_concept_and_one_protein():
    from reproduction.analysis_inputs import InputsRefused, analysis_inputs

    target, declaration, front, header, crosswalk = _phf19_inputs_case()
    with pytest.raises(InputsRefused, match="concept:ratchet-strength"):
        analysis_inputs({**target, "object": "concept:ratchet-strength"}, declaration, front, header, crosswalk)


def test_select_target_refuses_an_eligible_evidence_line_without_a_target(tmp_path):
    from reproduction.select_target import evidence_lines

    lines = tmp_path / "entities" / "evidence-lines"
    lines.mkdir(parents=True)
    (lines / "ok.md").write_text(
        "---\nid: evidence-line:ok\ntarget: proposition:p\nevidence_type: empirical_data\nbelief_eligible: true\n---\n"
    )
    assert list(evidence_lines(tmp_path)) == ["proposition:p"]
    (lines / "orphan.md").write_text(
        "---\nid: evidence-line:orphan\nevidence_type: empirical_data\nbelief_eligible: true\n---\n"
    )
    with pytest.raises(ValueError, match="orphan"):
        evidence_lines(tmp_path)


def test_the_reading_projection_round_trips_through_identity_v1(tmp_path):
    """Step 12 compares two processes' encoded readings byte for byte, so the
    encoding must be a fixed point of decode-then-encode: an encoding that did
    not round-trip would make `reading_equal` a measurement of the encoder
    rather than of the corpus. Read through `read_composite`, which is the
    reading's one mint, over a memberless composite — the rows are
    exercised in `test_composite_reading.py`; what is measured here is the
    encoding the driver's two files hold."""
    from test_composite_boundary import GENE, _writer

    from beliefs import stored
    from beliefs.belief import Availability, SuppliedContext
    from beliefs.composite import CompositeNode, build_composite, read_composite
    from beliefs.corpus import lineage_snapshot
    from beliefs.identity import v1
    from beliefs.policy import BELIEF_V1, BELIEF_V1_RULE
    from beliefs.resolution import build_snapshot

    writer = _writer(tmp_path / "corpus")
    value, _ = build_composite(
        writer.profile,
        writer.read_view,
        shape="dag",
        nodes=[CompositeNode(GENE, "EX:a")],
        members=[],
        snapshot=build_snapshot(),
        slug="m",
    )
    minted = writer.add(stored.composite_node(value, title="m"))
    reading = read_composite(
        writer.read_view,
        minted.id,
        context=SuppliedContext(
            snapshot=lineage_snapshot(writer.read_view, ()),
            producer_snapshot_identity="no-epoch-published",
            node_corpus={},
            pins={},
        ),
        availability=Availability(observations={}, implementations={}, fixtures={}),
        resolution=build_snapshot(),
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        profile=writer.profile,
    )
    encoded = v1.encode(reading.projection())
    assert encoded == v1.encode(json.loads(encoded))


@pytest.mark.parametrize("multiple", [False, True])
def test_step8_evaluates_after_mint_and_reopen_before_diagnostics(tmp_path, monkeypatch, multiple):
    from dataclasses import replace

    from fixtures_cut3 import TESTING_PROFILE, typed_estimand
    from fixtures_cut4 import raw_write
    from reproduction import belief as driver
    from test_stored import _testing_writer
    from verification_fixtures import evaluation_kwargs, publish_corpus

    from beliefs import stored
    from beliefs.identity import v1
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.runrecord import run_ref
    from beliefs.target import target_projection

    writer = _testing_writer(tmp_path / "corpus")
    published = publish_corpus(writer)
    if multiple:
        node = published.assessment.model_copy(deep=True)
        import uuid

        node.uid = uuid.uuid4().hex
        node.id = "assessment:second-key"
        node.relations = [r.model_copy(update={"source": node.id}) for r in node.relations]
        value = stored.assessment_value(node, profile=TESTING_PROFILE)
        target = replace(value.target, estimand=typed_estimand(uncertainty="standard-error"))
        node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(target_projection(target)).decode()
        # Give the second key its own identity and verification target.
        node.facets[stored.ASSESSMENT_FACET]["spec"] = "other-spec"
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        from authority import FULL
        from nodes.core.write_plan import DefaultExecutor

        from beliefs.corpus import CorpusWriter

        writer = CorpusWriter(writer.root, DefaultExecutor, authority=FULL, profile=TESTING_PROFILE)
    st = {
        "proposition_ref": published.proposition.id,
        "assessment_ref": published.assessment.id,
        "original_run_ref": run_ref(published.original.address()),
        "replayed_run_ref": run_ref(published.replayed.address()),
        "assessment_identity_derived": published.derived.assessment,
        "assessment_identity_stored": published.derived_value.identity(),
    }
    saved, findings_seen, events = {}, [], []

    def opened():
        events.append("open")
        return writer

    monkeypatch.setattr(driver.world, "open_writer", opened)
    monkeypatch.setattr(driver.state, "load", lambda: st)
    monkeypatch.setattr(driver.state, "save", lambda **values: saved.update(values))
    from beliefs.series.evidence import SeriesEvidence

    supplied = SeriesEvidence({}, {})

    def frozen(**kwargs):
        assert kwargs["series_evidence"] is supplied
        return published.frozen

    monkeypatch.setattr(driver.spec, "frozen", frozen)
    actual_verification = driver.build_verification

    def verification(*args, **kwargs):
        assert kwargs["series_evidence"] is supplied
        assert kwargs["profile"] is TESTING_PROFILE
        assert kwargs["records"].holds(published.assessment.id)
        return actual_verification(*args, **kwargs)

    monkeypatch.setattr(driver, "build_verification", verification)
    monkeypatch.setattr(driver.spec, "EQUIVALENCE", CONTENT_EQUALITY)
    monkeypatch.setattr(driver.vocabulary, "profile", lambda: TESTING_PROFILE)
    kwargs = evaluation_kwargs(writer.read_view)
    monkeypatch.setattr(driver.vocabulary, "snapshot", lambda: kwargs["resolution"])
    monkeypatch.setattr(driver, "availability", lambda view: kwargs["availability"])
    monkeypatch.setattr(driver, "context", lambda view: evaluation_kwargs(view)["context"])
    monkeypatch.setattr(driver, "observations_from_corpus", lambda view: kwargs["availability"].observations)
    monkeypatch.setattr(driver.findings, "record", lambda *a, **kw: findings_seen.append(a))
    actual_evaluate = driver.evaluate_here

    def evaluate_after_mint(view):
        assert events.count("open") >= 2
        assert any(n.kind == "verification" for n in view.iter_stored())
        events.append("evaluate")
        return actual_evaluate(view)

    monkeypatch.setattr(driver, "evaluate_here", evaluate_after_mint)
    actual_gather = driver.gather

    def diagnostic(*args, **kwargs):
        assert "evaluate" in events
        events.append("gather")
        return actual_gather(*args, **kwargs)

    monkeypatch.setattr(driver, "gather", diagnostic)
    monkeypatch.setattr(driver, "pins_negative", lambda view, key: events.append(("pins", key)))
    code = driver.main(series_evidence=supplied)
    assert events.index("evaluate") > events.index("open")
    if multiple:
        assert code == 2
        assert saved["belief_answer"] == {"kind": "Refused", "reason": "multiple-assessed-propositions: use claim_view"}
        assert saved["admission"] == "not-evaluated: multiple-assessed-propositions"
        assert any(
            row[0:2] == (8, "design-gap") and "multiple-assessed-propositions" in row[2] for row in findings_seen
        )
        assert "gather" not in events
    else:
        assert code == 0 and saved["admission"] == "Admitted"
        assert saved["belief_answer"]["kind"] == "Belief" and saved["belief_answer"]["value"] == 1
        assert events.index("evaluate") < events.index("gather")
        assert ("pins", published.derived_value.key()) in events


def test_mann_whitney_normalized_u_counts_half_ties():
    from math import sqrt

    a, baseline = [1, 2], [2, 3]
    u_reported, z, _p = _assoc().mann_whitney(a, baseline)
    n_a, n_b = len(a), len(baseline)
    sigma = sqrt(n_a * n_b * (n_a + n_b + 1) / 12)
    u = z * sigma + n_a * n_b / 2
    pairwise = sum((x > y) + 0.5 * (x == y) for x in a for y in baseline) / (n_a * n_b)
    assert u_reported == pytest.approx(u)
    assert pairwise == 0.125
    assert u / (n_a * n_b) == pytest.approx(pairwise, abs=1e-15)


@pytest.mark.parametrize(
    "pd,ndmm,effect",
    [
        ([4, 5, 6], [1, 2, 3], 1.0),
        ([1, 2, 3], [4, 5, 6], 0.0),
        ([2, 2, 2], [2, 2, 2], 0.5),
        ([1, 2, 3], [2, 3, 4], 2 / 9),
    ],
)
def test_exported_probability_of_superiority(pd, ndmm, effect):
    _outcome, actual, _z, _p, n = _assoc().decide({"PD": pd, "NDMM": ndmm}, positive_level="PD")
    assert actual == pytest.approx(effect)
    assert n == 6
    _, reversed_effect, *_ = _assoc().decide({"PD": ndmm, "NDMM": pd}, positive_level="PD")
    assert reversed_effect == pytest.approx(1 - effect)


def test_assoc_refuses_the_wrong_pair_of_two_levels():
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="NDMM and PD"):
        assoc.decide({"PD": [1, 2, 3], "other": [4, 5, 6]}, positive_level="PD")


def test_assoc_rejects_duplicate_features_and_unknown_label_tokens(tmp_path):
    assoc = _assoc()
    matrix = _matrix(tmp_path, ["a_NDMM", "b_PD"], [["g1", "1", "2"], ["g1", "3", "4"]])
    with pytest.raises(assoc.MalformedInput, match="more than once"):
        assoc.load(matrix, value_row="g1")
    matrix = _matrix(tmp_path, ["a_NDMM", "b_unknown"], [["g1", "1", "2"]])
    with pytest.raises(assoc.MalformedInput, match="unknown group token"):
        assoc.load(matrix, value_row="g1")


def test_reproduction_callers_forward_series_context(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from fixtures_cut3 import MEMORY_PORT, TESTING_CLAIM, TESTING_PROFILE, spec_rules
    from reproduction import run as driver
    from test_stored import _testing_writer
    from verification_fixtures import publish_corpus

    from beliefs.projection import project_claim
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.series.evidence import SeriesEvidence

    writer = _testing_writer(tmp_path / "corpus")
    published = publish_corpus(writer, claim=project_claim(TESTING_CLAIM))
    supplied = SeriesEvidence({}, {})
    states = {
        "dataset_address": published.frozen.input_roles[0].dataset,
        "held_file": str(tmp_path / "held"),
        "proposition_ref": published.proposition.id,
    }
    monkeypatch.setattr(driver.state, "load", lambda: states)
    monkeypatch.setattr(driver.state, "save", lambda **kw: None)
    monkeypatch.setattr(
        driver.world,
        "open_writer",
        lambda: SimpleNamespace(
            read_view=writer.read_view,
            add=lambda node: published.assessment,
            manifest_pins=writer.manifest_pins,
        ),
    )
    monkeypatch.setattr(driver, "port", lambda: MEMORY_PORT)
    monkeypatch.setattr(driver, "profile", lambda: TESTING_PROFILE)

    def frozen(**kwargs):
        assert kwargs["series_evidence"] is supplied
        return published.frozen

    monkeypatch.setattr(driver.spec, "frozen", frozen)
    monkeypatch.setattr(driver.spec, "definition", lambda: None)
    monkeypatch.setattr(driver.spec, "code_root", lambda: tmp_path)
    monkeypatch.setattr(driver.spec, "EQUIVALENCE", CONTENT_EQUALITY)
    monkeypatch.setattr(driver.spec, "INTERPRETATION", spec_rules()[published.frozen.interpretation_rule])
    monkeypatch.setattr(driver.findings, "record", lambda *a, **kw: None)
    calls = []

    def context(kwargs):
        assert kwargs["series_evidence"] is supplied
        assert kwargs["profile"] is TESTING_PROFILE
        assert kwargs["records"].holds(published.assessment.id)

    def execute(**kwargs):
        context(kwargs)
        calls.append("execute")
        return SimpleNamespace(run=published.original)

    def replay(*args, **kwargs):
        context(kwargs)
        calls.append("replay")
        return SimpleNamespace(run=published.replayed)

    actual = driver.build_verification

    def verify(*args, **kwargs):
        context(kwargs)
        calls.append("verify")
        return actual(*args, **kwargs)

    monkeypatch.setattr(driver, "execute_assessment_run", execute)
    monkeypatch.setattr(driver, "replay", replay)
    monkeypatch.setattr(driver, "build_verification", verify)
    assert driver.main(series_evidence=supplied) == 0
    assert calls == ["execute", "replay", "verify"]
