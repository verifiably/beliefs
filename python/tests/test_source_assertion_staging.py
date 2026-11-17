"""Publication staging checks for `source-assertion` records."""

from __future__ import annotations

from typing import cast

import pytest
from authority import ACTOR, FULL
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import SourceAssertionRefused
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span

SOURCE_ID = "source:" + "1" * 64
PROPOSITION_ID = "proposition:ab"


@pytest.fixture()
def writer(tmp_path):
    root = tmp_path / "staging"
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return w


def _assertion(*, quote: str = "PHF19 is overexpressed") -> SourceAssertion:
    return SourceAssertion(
        source=SOURCE_ID,
        read=Reading(
            representation=Representation(sha256="a" * 64, media_type="application/pdf", extent="full"),
            span=Span(quote=quote, locator="Results, para 2"),
            extracted_by=ACTOR,
        ),
        bears_on=Bearing(sign="asserts", proposition=PROPOSITION_ID),
        recorded_by=ACTOR,
    )


def test_staging_admits_a_well_formed_assertion_byte_for_byte(writer):
    value = _assertion(quote="caf\u00e9")
    node = stored.source_assertion_node(value, title="t")
    text = node_to_markdown(node)

    staged = writer._stage_record(text)

    assert staged == node
    assert (writer.root / writer._relative_path(node)).read_text(encoding="utf-8") == text
    assert stored.source_assertion_value(writer.read_view.get(node.id)).read.span.quote == "caf\u00e9"


def test_staging_refuses_an_extra_edge(writer):
    value = _assertion()
    node = stored.source_assertion_node(value, title="t")
    with_extra = stored.stamp_semantic_identity(
        node.model_copy(
            update={
                "relations": [*node.relations, Relation(source=value.id, predicate="assesses", target=PROPOSITION_ID)]
            }
        )
    )

    with pytest.raises(SourceAssertionRefused) as caught:
        writer._stage_record(node_to_markdown(with_extra))

    assert caught.value.code == "source-assertion-edge-mismatch"
    assert not (writer.root / writer._relative_path(with_extra)).exists()


def test_staging_refuses_a_malformed_assertion(writer):
    value = _assertion()
    node = stored.source_assertion_node(value, title="t").model_copy(deep=True)
    facet = cast(dict[str, object], node.facets[stored.SOURCE_ASSERTION_FACET])
    del facet["bears_on"]
    damaged = stored.stamp_semantic_identity(node)

    with pytest.raises(SourceAssertionRefused) as caught:
        writer._stage_record(node_to_markdown(damaged))

    assert caught.value.code == "source-assertion-malformed"
    assert not (writer.root / writer._relative_path(damaged)).exists()
