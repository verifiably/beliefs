"""Standing at the read (correction-remainder slice 1): the fold, the local
enumeration, and — from Task 4 on — `gather`'s subtraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import FULL
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_local_standing import assessment, retracts

from beliefs import corpus, stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, RetractionEnumeration
from beliefs.corpus import CorpusWriter, ReadView, local_retraction_enumeration, retraction_standing
from beliefs.errors import ManifestMissing, RetractionUnreadable


def adopted(tmp_path: Path, name: str = "corpus") -> CorpusWriter:
    """A corpus with a manifest: `ReadView.corpus_id` reads one, and
    `test_local_standing.seed` writes none (spec §8.1)."""
    writer = CorpusWriter(tmp_path / name, DefaultExecutor, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return writer


def add_assessment(writer: CorpusWriter):
    """Supply the real write boundary's prerequisites for `assessment()`."""
    dataset = writer.add(
        stored.dataset_node(
            title="raw",
            resources=[{"name": "matrix", "digest": "sha256:" + "ab" * 32}],
            empirical_observation={"locator": "instrument:fixture", "attested_by": writer.authority.actor},
        )
    )
    writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
    writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    return writer.add(assessment())


def test_the_local_enumeration_is_empty_with_the_manifest_coverage(tmp_path):
    writer = adopted(tmp_path)
    view = writer.read_view
    assert view.corpus_id == writer.corpus_id
    assert local_retraction_enumeration(view) == RetractionEnumeration(found=(), coverage=(writer.corpus_id,))


def test_the_local_enumeration_folds_standing_and_keys_by_id(tmp_path):
    writer = adopted(tmp_path)
    target = add_assessment(writer)
    first = writer.retract(retracts(target, "t1"))
    counter = writer.retract(retracts(first, "t2"))
    view = writer.read_view
    found = dict(local_retraction_enumeration(view).found)
    assert found == {first.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
    facets = {n.id: corpus._validated_retraction_facet(n) for n in view.iter_stored() if n.kind == "retraction"}
    standing = retraction_standing(view, facets)
    assert standing[first.id] is False and standing[counter.id] is True and standing[target.id] is True
    assert corpus.standing_in_local_view(view, target.id) is True


def test_a_manifest_less_corpus_cannot_declare_coverage(tmp_path):
    from fixtures_cut4 import raw_write, reopen

    raw_write(tmp_path / "bare", assessment())
    with pytest.raises(ManifestMissing):
        _coverage = local_retraction_enumeration(reopen(tmp_path / "bare")).coverage


def test_a_raw_retraction_the_capture_validator_refuses_is_unreadable_at_the_enumeration(tmp_path):
    from fixtures_cut4 import raw_write

    writer = adopted(tmp_path)
    target = add_assessment(writer)
    node = retracts(target, "t1")
    node.facets[stored.RETRACTION_FACET].pop("grounds")
    raw_write(writer.root, stored.stamp_semantic_identity(node))
    with pytest.raises(RetractionUnreadable) as refused:
        local_retraction_enumeration(ReadView.opened_at(writer.root))
    assert refused.value.ref == node.id and "grounds" in refused.value.cause
