"""Unit tests for the mm30 reproduction driver under `tools/reproduction/`.

The driver is throwaway by declaration; these tests guard the bridges it
crosses between kernel spellings and the pure functions its steps rely on.
"""

from __future__ import annotations

import json
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

    from fixtures_cut3 import typed_applicability, typed_estimand
    from reproduction import spec as spec_module

    from beliefs import stored
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    draft = SpecDraft(
        target="proposition:p", estimand=typed_estimand(), method="m", assumptions="a", falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),), applicability=typed_applicability(),
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
    # requires the target proposition's own claim to agree (estimand-typing
    # §7.2, Task 8), so the proposition carries that same claim rather than
    # `publish_corpus`'s bare `{"operator": "affects"}` default.
    published = publish_corpus(writer, claim=project_claim(TESTING_CLAIM))
    spec_node = writer.add(stored.analysis_spec_node(published.frozen))
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
    report = rederive.reconstruct(view, st, close.evidence_for(view, TESTING_PROFILE))
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
    negative = rederive.reconstruct(writer.read_view, {**st, "verification_ref": legacy.id}, close.evidence_for(writer.read_view, TESTING_PROFILE))
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
    from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules
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
        close.evidence_for(reopen(writer.root), TESTING_PROFILE)


# The held concept list's content address, measured 2026-09-15 over the
# predecessor's 285 concept records. The cut-22 document's content identity is
# taken over it, so the successor's declared predecessor moves with it; a
# changed predecessor corpus fails this loudly rather than silently.
HELD_CONCEPTS = "dataset:sha256:be3bf183a830c31d4f8acf46a309e01bd0476580d2d6db4079af3e3c7bd738d8"


@pytest.fixture
def held_vocabulary(monkeypatch):
    """`state.json` as the driver leaves it after steps 1b and 1c: the four
    addresses every sort of the successor contract binds. The three list
    addresses are derived from the driver's own declaration, so only the
    concept list — which lives in the predecessor corpus — is pinned."""
    from hashlib import sha256

    from reproduction import lists, vocabulary

    cached = (vocabulary._document, vocabulary.contract, vocabulary.profile)
    st = {"concepts_address": HELD_CONCEPTS}
    for name, (_resource, terms) in lists.LISTS.items():
        st[f"{name}_address"] = lists.list_node(name, "sha256:" + sha256(lists.list_lines(terms)).hexdigest()).id
    monkeypatch.setattr(vocabulary.state, "load", lambda: st)
    for entry in cached:
        entry.cache_clear()
    yield st
    for entry in cached:
        entry.cache_clear()


def test_the_row_plan_maps_a_predicate_and_kind_pair(held_vocabulary):
    from reproduction import vocabulary

    plan = vocabulary.plan()
    assert plan["operators"][("affects", "concept", "protein")] == "mm30/affects-concept-molecular-entity"
    assert plan["operators"][("affects", "protein", "protein")] == "biology/affects-molecular-entity-molecular-entity"
    assert plan["sorts"] == {"concept": "mm30/concept", "protein": "biology/molecular-entity"}
    assert len(plan["operators"]) == 17


def test_the_mm30_contract_binds_every_sort_to_its_held_list_and_succeeds_the_cut_31_document(held_vocabulary):
    from reproduction import vocabulary

    contract = vocabulary.contract()
    for sort, key in (
        ("concept", "concepts"),
        ("stage-level", "levels"),
        ("measure", "measures"),
        ("identification", "identifications"),
    ):
        assert contract.sorts[sort].vocabulary.dataset_identity == held_vocabulary[f"{key}_address"].removeprefix(
            "dataset:"
        )
    assert contract.operators["affects-concept-molecular-entity"].arg_sorts == ("concept", "biology/molecular-entity")
    # Succession ran against the real predecessors, not authored stand-ins, and
    # the whole chain is walked: cut 22 → cut 31 → current.
    cut31 = vocabulary.contract(vocabulary.CUT31_DOCUMENT)
    assert contract.predecessor == cut31.content_identity
    assert cut31.predecessor == vocabulary.contract(vocabulary.CUT22_DOCUMENT).content_identity
    assert vocabulary.contract(vocabulary.CUT22_DOCUMENT).predecessor is None
    # The `edges:` table the composite-claims lane adds, and the operators it
    # leaves without a row (composite-claims design §3.3, §3.4).
    assert {name: (e.cause, e.effect) for name, e in contract.edges.items()} == {
        "affects-concept-concept": (0, 1),
        "affects-concept-molecular-entity": (0, 1),
        "affects-molecular-entity-concept": (0, 1),
        "regulates-concept-concept": (0, 1),
        "regulates-concept-molecular-entity": (0, 1),
        "regulates-molecular-entity-concept": (0, 1),
        "induces-state-concept-concept": (0, 1),
    }
    assert not cut31.edges
    declared = contract.estimands["affects-concept-molecular-entity"]
    assert dict(declared.level_sorts) == {"0": "stage-level"}
    assert (declared.measure_sort, declared.identification_sort, declared.conditioning_sort) == (
        "measure",
        "identification",
        "concept",
    )
    compiled = vocabulary.profile().estimand("mm30/affects-concept-molecular-entity")
    assert dict(compiled.level_sorts) == {"0": "mm30/stage-level"}
    assert (compiled.measure_sort, compiled.identification_sort, compiled.conditioning_sort) == (
        "mm30/measure",
        "mm30/identification",
        "mm30/concept",
    )


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
            ResourceDeclaration(
                name="mm30-stage-levels.txt", digest="sha256:" + sha256(path.read_bytes()).hexdigest()
            ),
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


# Re-pinned 2026-09-15 (estimand-typing Task 6): `estimand` and `applicability`
# moved from prose to typed members, so the digest they enter into moved too —
# the rule bindings this test actually guards are unchanged, per the assertion
# above.
PINNED_IDENTITY = "abb23abf21d3674428606df058bafc983be845d9b4e2fa918bf08bff7aae87d8"


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
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),),
        applicability=typed_applicability(),
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
        "identity_context": {"molecular_ids": {"gene": {"namespace": "ensembl", "registry": "dataset:gene-crosswalk-hgnc"}}},
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
    (lines / "orphan.md").write_text("---\nid: evidence-line:orphan\nevidence_type: empirical_data\nbelief_eligible: true\n---\n")
    with pytest.raises(ValueError, match="orphan"):
        evidence_lines(tmp_path)


def test_the_reading_projection_round_trips_through_identity_v1(tmp_path):
    """Step 12 compares two processes' encoded readings byte for byte, so the
    encoding must be a fixed point of decode-then-encode: an encoding that did
    not round-trip would make `reading_equal` a measurement of the encoder
    rather than of the corpus. Read through `read_composite`, which is the
    reading's one mint (U8), over a memberless composite — the rows are
    exercised in `test_composite_reading.py`; what is measured here is the
    encoding the driver's two files hold."""
    from test_composite_boundary import GENE, _writer

    from beliefs import stored
    from beliefs.belief import Availability, SuppliedContext
    from beliefs.closure import RetractionEnumeration
    from beliefs.composite import CompositeNode, build_composite, read_composite
    from beliefs.corpus import lineage_snapshot
    from beliefs.identity import v1
    from beliefs.policy import BELIEF_V1, BELIEF_V1_RULE
    from beliefs.resolution import build_snapshot

    writer = _writer(tmp_path / "corpus")
    value, _ = build_composite(
        writer.profile, writer.read_view, shape="dag", nodes=[CompositeNode(GENE, "EX:a")],
        members=[], snapshot=build_snapshot(), slug="m",
    )
    minted = writer.add(stored.composite_node(value, title="m"))
    reading = read_composite(
        writer.read_view,
        minted.id,
        context=SuppliedContext(
            snapshot=lineage_snapshot(writer.read_view, ()),
            producer_snapshot_identity="no-epoch-published",
            retractions=RetractionEnumeration(found=(), coverage=()),
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
