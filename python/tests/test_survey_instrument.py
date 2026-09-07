"""Regression tests for the corpus survey instrument's pure classifiers.

The survey itself is never run by the suite — it reads corpora outside this
repository, so any test asserting a *finding* would be asserting something CI
cannot see. What is testable here is the part that decided the finding: the
predicates. Every case below is a defect that was actually shipped and caught in
review, which is the only reason to keep the file — a survey defect costs a
ruling, and three of them did.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# `tools/` is not a package and deliberately is not on the import path — nothing
# in `src/` may depend on it. Load it by file instead, registering it in
# `sys.modules` first because `@dataclass` resolves annotations through there.
_SPEC = importlib.util.spec_from_file_location(
    "survey_corpora", Path(__file__).parents[1] / "tools" / "survey_corpora.py"
)
assert _SPEC is not None and _SPEC.loader is not None
survey = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = survey
_SPEC.loader.exec_module(survey)


class TestAgreement:
    def test_identical_sets_agree(self) -> None:
        assert survey.agreement([{"a", "b"}, {"a", "b"}]) == "identical"

    def test_a_chain_is_nested(self) -> None:
        assert survey.agreement([{"a"}, {"a", "b"}, {"a", "b", "c"}]) == "nested"

    def test_incomparable_pair_is_divergent_even_when_one_set_equals_the_union(self) -> None:
        # The shipped defect: the verdict asked whether *some* set equalled the
        # union. Here `{a,b,c}` does, while `{a,b}` and `{a,c}` each carry a term
        # the other lacks. `evidence_type` is this shape across the real corpora.
        assert survey.agreement([{"a", "b", "c"}, {"a", "b"}, {"a", "c"}]) == "divergent"

    def test_disjoint_sets_are_divergent(self) -> None:
        assert survey.agreement([{"high", "low"}, {"p1", "p2"}]) == "divergent"


class TestReferenceShape:
    @pytest.mark.parametrize(
        "value",
        [
            "proposition:0001-myc-drives-progression",
            "hypothesis:h1",
            "evidence-line:el_0042",
            "dataset:gse4581/v2",
        ],
    )
    def test_entity_references_are_links(self, value: str) -> None:
        assert survey._looks_like_reference(value)

    @pytest.mark.parametrize(
        "value",
        [
            "2026-08-07T10:49:59.595Z",  # an ISO timestamp partitions to an alphanumeric head
            "https://example.com/x",  # so does every URL
            "doi:10.1038/s41586-024-00001-2",  # an identifier authority, not an entity kind
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # a content address
            "mm30: a myeloma survival atlas",  # prose holding a colon — this is what titles do
            "Background: the cohort was recruited in 2019",
            "notacolon",
            "kind:",  # empty tail
            "Proposition:0001",  # a kind is lowercase; this is prose
        ],
    )
    def test_reference_shaped_non_edges_are_not_links(self, value: str) -> None:
        assert not survey._looks_like_reference(value)


def _corpus(tmp_path: Path, name: str, records: dict[str, str]):  # -> survey.Corpus, loaded dynamically
    root = tmp_path / name / "entities" / "discussion"
    root.mkdir(parents=True)
    for stem, front in records.items():
        (root / f"{stem}.md").write_text(f"---\n{front}\n---\n\nbody\n")
    return survey.read_corpus(tmp_path / name)


class TestLinkAccounting:
    def test_identity_and_display_fields_are_not_edges(self, tmp_path: Path) -> None:
        c = _corpus(
            tmp_path,
            "identity",
            {
                "a": "id: discussion:a\ntitle: discussion:a\ncontent_hash: sha256:abc123\nrelated:\n  - question:q1",
            },
        )
        assert dict(c.links) == {"related": 1}

    def test_a_mixed_list_counts_only_its_references(self, tmp_path: Path) -> None:
        c = _corpus(tmp_path, "mixed", {"a": "tags:\n  - question:q1\n  - some free text\n  - https://example.com"})
        assert c.links["tags"] == 1

    def test_a_field_holding_no_reference_is_absent_from_the_tally(self, tmp_path: Path) -> None:
        # `Counter[key] += 0` inserts the key, which reported fields that never
        # held a link as link-bearing and inflated the distinct-field count.
        c = _corpus(tmp_path, "empty", {"a": "tags:\n  - some free text"})
        assert "tags" not in c.links

    def test_a_triple_is_counted_per_record_not_per_field(self, tmp_path: Path) -> None:
        c = _corpus(
            tmp_path,
            "triples",
            {
                "whole": "subject: gene:myc\npredicate: affects\nobject: phenotype:survival",
                "partial": "predicate: affects",
            },
        )
        assert c.triples == 1

    def test_an_unparsed_record_is_named_not_dropped(self, tmp_path: Path) -> None:
        c = _corpus(tmp_path, "broken", {"a": "kind: discussion\n  bad: [indent"})
        assert c.records == 0
        assert len(c.unparsed) == 1


class TestClassify:
    def test_distinct_values_above_half_the_occurrences_are_free_text(self) -> None:
        values = survey.Counter({f"v{i}": 1 for i in range(11)} | {"repeated": 9})
        assert survey.classify(values) == "free-text"

    def test_a_dominant_value_collapses(self) -> None:
        assert survey.classify(survey.Counter({"supports": 95, "disputes": 5})) == "collapsed"

    def test_quoting_is_not_a_second_value(self) -> None:
        # Agreement is computed over normalized values because `literature` and
        # `"literature"` are one term. A regex pass that missed this reported
        # encoding drift that does not exist.
        assert survey.classify(survey.Counter({"literature": 50, '"literature"': 50})) == "collapsed"
