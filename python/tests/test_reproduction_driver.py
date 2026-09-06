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


def test_a_finding_class_outside_the_four_is_refused(tmp_path, monkeypatch):
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
        name="expr.tsv", digest="sha256:" + "c" * 64, title="t", facet={"boundary": "acquisition"}
    )
    assert node.id == address == "dataset:sha256:" + sha256(("sha256:" + "c" * 64 + "\n").encode()).hexdigest()


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
