from __future__ import annotations

import pytest
from authority import FULL
from nodes.core.write_plan import DefaultExecutor

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import ValidationRefused


def test_display_statement_stored_uncovered():
    node = stored.proposition_node(
        "p1", title="t", claim={"op": "affects"}, display_statement="In adults, X affects Y."
    )

    assert stored.display_statement(node) == "In adults, X affects Y."
    assert stored.DISPLAY_FACET not in stored.COVERED_FACETS["proposition"]

    bare = stored.proposition_node("p1", title="t", claim={"op": "affects"})
    assert stored.DISPLAY_FACET not in bare.facets
    assert stored.stored_semantic_hash(node) == stored.stored_semantic_hash(bare)


@pytest.mark.parametrize(
    "facet", [{"extra": 1}, {}, {"display_statement": 1}, {"display_statement": "x", "extra": 1}]
)
def test_display_facet_shape_is_validated(facet):
    node = stored.proposition_node("p1", title="t", claim={"op": "affects"})
    raw = node.model_copy(update={"facets": {**node.facets, "display": facet}})

    assert stored.display_facet_malformed(raw)


def test_writer_refuses_a_malformed_display_facet(tmp_path):
    node = stored.proposition_node("p1", title="t", claim={"op": "affects"})
    raw = node.model_copy(update={"facets": {**node.facets, "display": {"extra": 1}}})

    with pytest.raises(ValidationRefused, match="display"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL).add(raw)
