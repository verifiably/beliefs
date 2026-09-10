"""Unit tests for the mm30 reproduction driver under `tools/reproduction/`.

The driver is throwaway by declaration; these tests guard the bridges it
crosses between kernel spellings and the pure functions its steps rely on.
"""

from __future__ import annotations

from pathlib import Path

import pytest
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

    node, address = dataset_record(
        name="expr.tsv", digest="sha256:" + "c" * 64, title="t", accession="GSE179929"
    )
    assert node.id == address == "dataset:sha256:" + sha256(("sha256:" + "c" * 64 + "\n").encode()).hexdigest()


def test_the_hold_step_declares_a_locator_and_the_bound_actor():
    from reproduction.authority import ACTOR
    from reproduction.hold import dataset_record

    node, _ = dataset_record(
        name="f.gz", digest="sha256:" + "c" * 64, title="dataset:gse179929", accession="GSE179929"
    )
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
    spec.loader.exec_module(module)
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
        assoc.load(_matrix(tmp_path, ["s1_a", "s2_b"], [["g1", "1", "2"]]), value_row="g9")


def test_assoc_refuses_non_finite_values(tmp_path):
    assoc = _assoc()
    samples = [f"s{i}_{'a' if i % 2 else 'b'}" for i in range(6)]
    with pytest.raises(assoc.MalformedInput, match="finite"):
        assoc.load(_matrix(tmp_path, samples, [["g1", "nan", "2", "3", "4", "5", "6"]]), value_row="g1")


def test_assoc_refuses_a_sample_without_a_group_token(tmp_path):
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="group token"):
        assoc.load(_matrix(tmp_path, ["s1_a", "s2"], [["g1", "1", "2"]]), value_row="g1")


def test_assoc_refuses_a_group_below_the_floor(tmp_path):
    assoc = _assoc()
    samples = ["s1_a", "s2_a", "s3_a", "s4_b"]
    groups = assoc.load(_matrix(tmp_path, samples, [["g1", "1", "2", "3", "4"]]), value_row="g1")
    with pytest.raises(assoc.MalformedInput, match="at least"):
        assoc.decide(groups, positive_level="a")


def test_assoc_refuses_a_positive_level_that_is_absent(tmp_path):
    assoc = _assoc()
    samples = [f"s{i}_{'a' if i % 2 else 'b'}" for i in range(1, 11)]
    groups = assoc.load(_matrix(tmp_path, samples, [["g1", *[str(i) for i in range(1, 11)]]]), value_row="g1")
    with pytest.raises(assoc.MalformedInput, match="positive level"):
        assoc.decide(groups, positive_level="zzz")


def test_assoc_refuses_more_than_two_levels(tmp_path):
    assoc = _assoc()
    samples = ["s1_a", "s2_b", "s3_c"]
    groups = assoc.load(_matrix(tmp_path, samples, [["g1", "1", "2", "3"]]), value_row="g1")
    with pytest.raises(assoc.MalformedInput, match="two levels"):
        assoc.decide(groups, positive_level="a")


def test_assoc_supported_when_positive_level_is_higher_reading_gzip(tmp_path):
    assoc = _assoc()
    samples = [f"h{i}_hi" for i in range(8)] + [f"l{i}_lo" for i in range(8)]
    values = [str(10 + i) for i in range(8)] + [str(i) for i in range(8)]
    groups = assoc.load(_matrix(tmp_path, samples, [["other", *["0"] * 16], ["g1", *values]], gz=True), value_row="g1")
    outcome, z, p, n = assoc.decide(groups, positive_level="hi")
    assert outcome == "supported" and z > 0 and p < 0.05 and n == 16


def test_spec_record_carries_a_fresh_semantic_stamp():
    from decimal import Decimal

    from reproduction import spec as spec_module

    from beliefs import stored
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    draft = SpecDraft(
        target="proposition:p", estimand="e", method="m", assumptions="a", falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),), applicability="x",
        interpretation_rule=spec_module.INTERPRETATION_RULE, equivalence_rule=spec_module.EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")}, nondeterminism=Deterministic(),
    )
    node = spec_module.spec_record(freeze(draft, held_rules=spec_module.held_rules()))
    assert node.kind == "analysis-spec"
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)


def test_classify_scope_attributes_only_same_environment_to_the_host():
    from reproduction.run import classify_scope

    assert classify_scope("clean-environment", conforming=(True, True), recipes_agree=True) == "none"
    assert classify_scope("same-environment", conforming=(True, True), recipes_agree=True) == "host"
    assert classify_scope("not-certified", conforming=(True, False), recipes_agree=True) == "defect"
    assert classify_scope("not-certified", conforming=(True, True), recipes_agree=False) == "corpus-work"


def test_10b_reads_the_report_from_the_corpus_with_no_in_process_spec(tmp_path, monkeypatch):
    """V1 and V8's 10b arms: the report, scope and verdict are read; the only
    in-process input is the rule implementations; `spec.frozen()` is not
    reachable. The negative: a report-less record reports false."""
    from fixtures_cut3 import spec_rules
    from reproduction import close, rederive, spec
    from test_relocation import _writer
    from verification_fixtures import publish_corpus

    from beliefs import stored
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.verify import publication_node

    writer = _writer(tmp_path / "corpus")
    published = publish_corpus(writer)
    spec_node = writer.add(stored.analysis_spec_node(published.frozen))
    node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))

    def unavailable():
        raise RuntimeError("the in-process spec is unavailable")

    monkeypatch.setattr(spec, "frozen", unavailable)
    interpretation = spec_rules()[published.frozen.interpretation_rule]
    monkeypatch.setattr(spec, "EQUIVALENCE", CONTENT_EQUALITY)
    monkeypatch.setattr(spec, "INTERPRETATION", interpretation)
    st = {"verification_ref": node.id, "spec_ref": spec_node.id}
    view = writer.read_view
    report = rederive.reconstruct(view, st, close.evidence_for(view))
    assert report["comparison_report_stored"] is True
    assert report["scope_equal"] is True and report["verdict_equal"] is True and report["report_identity_equal"] is True
    assert report["inputs"]["in_process"] == ["interpretation and equivalence RuleImplementations"]
    assert report["spec_restored_identity_matches_run"] is True
    assert report["audit_check"] == {"checked": True, "reason": "", "contradiction": None}
    legacy = writer.add(
        stored.verification_node(
            "legacy", title="legacy", assessment=published.derived.assessment, assessment_ref=published.assessment.id,
            scope=published.derived.scope, verdict=published.derived.verdict,
            derivation=(stored.typed_ref("run", published.derived.original), stored.typed_ref("run", published.derived.replayed)),
        )
    )
    negative = rederive.reconstruct(writer.read_view, {**st, "verification_ref": legacy.id}, close.evidence_for(writer.read_view))
    assert negative["comparison_report_stored"] is False and "scope_read" not in negative


def test_10b_names_no_in_process_spec():
    from pathlib import Path

    from reproduction import rederive

    source = Path(rederive.__file__).read_text(encoding="utf-8")
    assert "spec.frozen" not in source and "from reproduction import" in source


def test_close_evidence_for_raises_on_a_stored_spec_that_does_not_restore(tmp_path):
    """`evidence_for` fails loud rather than silently narrowing the specs a
    recomputation sees (design decision 15): a raw-written analysis-spec
    record whose text disagrees with its own identity must stop 10b cold,
    never drop out of `stored_specs`' mapping unnoticed."""
    from fixtures_cut3 import spec_draft, spec_rules
    from fixtures_cut4 import raw_write, reopen
    from reproduction import close
    from test_relocation import _writer

    from beliefs import stored
    from beliefs.spec import freeze

    writer = _writer(tmp_path / "corpus")
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    forged = stored.analysis_spec_node(frozen).model_copy(update={"id": "analysis-spec:forged"})
    forged.facets[stored.ANALYSIS_SPEC_FACET]["identity"] = "forged"
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace(
        "fit the model", "fit another model"
    )
    raw_write(writer.root, stored.stamp_semantic_identity(forged))
    with pytest.raises(RuntimeError, match="analysis-spec:forged"):
        close.evidence_for(reopen(writer.root))


def test_the_row_plan_maps_a_predicate_and_kind_pair(tmp_path, monkeypatch):
    from reproduction import vocabulary

    monkeypatch.setattr(vocabulary.state, "load", lambda: {"concepts_address": "dataset:sha256:" + "c" * 64})
    plan = vocabulary.plan()
    assert plan["operators"][("affects", "concept", "protein")] == "mm30/affects-concept-molecular-entity"
    assert plan["operators"][("affects", "protein", "protein")] == "biology/affects-molecular-entity-molecular-entity"
    assert plan["sorts"] == {"concept": "mm30/concept", "protein": "biology/molecular-entity"}
    assert len(plan["operators"]) == 17


def test_the_mm30_contract_binds_concept_to_the_held_list(monkeypatch):
    from reproduction import vocabulary

    monkeypatch.setattr(vocabulary.state, "load", lambda: {"concepts_address": "dataset:sha256:" + "c" * 64})
    vocabulary._document.cache_clear()
    contract = vocabulary.contract()
    assert contract.sorts["concept"].vocabulary.dataset_identity == "sha256:" + "c" * 64
    assert contract.operators["affects-concept-molecular-entity"].arg_sorts == ("concept", "biology/molecular-entity")


def test_concept_lines_are_canonical_sorted_and_terminated(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    (root / "b.md").write_text("---\nid: concept:b-thing\nkind: concept\n---\n")
    (root / "a.md").write_text("---\nid: concept:a-thing\nkind: concept\n---\n")
    assert concept_lines(tmp_path) == b"concept:a-thing\nconcept:b-thing\n"


def test_the_snapshot_refuses_a_dataset_the_binding_does_not_name():
    from hashlib import sha256

    from reproduction.vocabulary import snapshot_over

    from beliefs.contract.domain import VocabularyBinding
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

    content = b"concept:a-thing\nconcept:b-thing\n"
    digest = "sha256:" + sha256(content).hexdigest()
    declared = DatasetDeclaration(resources=(ResourceDeclaration(name="mm30-concepts.txt", digest=digest),))
    right = dataset_address(declared)
    assert right is not None
    bound_to_this = VocabularyBinding(namespace=None, release=None, dataset_identity=right.removeprefix("dataset:"))
    bound_elsewhere = VocabularyBinding(namespace=None, release=None, dataset_identity="sha256:" + "f" * 64)
    assert snapshot_over(declared, content, bound_to_this).resolve(bound_to_this, "concept:a-thing").value == "member"
    with pytest.raises(RuntimeError, match="binds dataset:sha256:f"):
        snapshot_over(declared, content, bound_elsewhere)


def test_the_snapshot_refuses_a_copy_that_is_not_the_dataset():
    from hashlib import sha256

    from reproduction.vocabulary import snapshot_over

    from beliefs.contract.domain import VocabularyBinding
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

    content = b"concept:a-thing\n"
    declared = DatasetDeclaration(
        resources=(ResourceDeclaration(name="mm30-concepts.txt", digest="sha256:" + sha256(content).hexdigest()),)
    )
    address = dataset_address(declared)
    assert address is not None
    binding = VocabularyBinding(namespace=None, release=None, dataset_identity=address.removeprefix("dataset:"))
    with pytest.raises(RuntimeError, match="does not hash"):
        snapshot_over(declared, b"concept:a-thing\nconcept:smuggled\n", binding)


def test_a_non_canonical_concept_id_refuses(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    (root / "x.md").write_text("---\nid: 'concept:café-thing'\nkind: concept\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canonical"):
        concept_lines(tmp_path)


PINNED_IDENTITY = "fadc127ba6efd8a901015a029df99178c346889a39afb98200ba7c9914c5da6a"


def test_the_driver_binds_the_kernel_rules_under_its_own_identities():
    from decimal import Decimal

    from reproduction import spec as spec_module

    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.rules import OUTCOME_FILE_V1
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    held = spec_module.held_rules()
    assert held[spec_module.INTERPRETATION_RULE] is OUTCOME_FILE_V1
    assert held[spec_module.EQUIVALENCE_RULE] is CONTENT_EQUALITY
    draft = SpecDraft(
        target="proposition:p",
        estimand="e",
        method="m",
        assumptions="a",
        falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),),
        applicability="x",
        interpretation_rule=spec_module.INTERPRETATION_RULE,
        equivalence_rule=spec_module.EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
    )
    frozen = freeze(draft, held_rules=held)
    # The pairs the 2026-09-05 record digests, unchanged: identity-neutral by construction.
    assert frozen.rule_bindings == (
        ("content-identity-equality/v1", "impl-eq-1"),
        ("mm30-reproduction/outcome-file/v1", "impl-outcome-file-1"),
    )
    assert frozen.identity == PINNED_IDENTITY
