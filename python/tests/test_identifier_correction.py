"""Slice 2b §5–§8: the source write boundary, the correction seam, its layers,
relocation and the read side."""

from __future__ import annotations

from typing import TypedDict

import pytest
from authority import FULL
from profiles import BASE
from test_corpus_write import Recorder
from test_source_address import ADDR_A, ADDR_B, CANONICAL_DOI, A, B, entry, raw_source

from beliefs import source, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    BasisMissing,
    IdentifierMalformed,
    SourceAddressDisagreement,
    ValidationRefused,
)


class _ImportFields(TypedDict):
    observer: str
    instrument: str
    opened_at: str
    closed_at: str


@pytest.fixture()
def writer(request, tmp_path) -> CorpusWriter:
    Recorder.plans.clear()
    callspec = getattr(request.node, "callspec", None)
    root = tmp_path / callspec.id if callspec is not None else tmp_path
    return CorpusWriter(root / "corpus", Recorder, authority=FULL, profile=BASE)


class TestTheBoundary:
    def test_a_builder_source_is_admitted(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        assert writer.read_view.get(minted.id).id == ADDR_B

    def test_an_empty_basis_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(raw_source({}, node_id="source:handle"))

    def test_a_non_canonical_stored_value_refuses(self, writer):
        node = raw_source({"doi": "10.1234/ABC"}, node_id=source.source_address({"doi": "10.1234/ABC"}))
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "non-canonical"

    def test_non_canonical_refusal_is_independent_of_insertion_order(self, writer):
        for identifiers in (
            {"pmid": "pmid:1", "doi": "10.1234/ABC"},
            {"doi": "10.1234/ABC", "pmid": "pmid:1"},
        ):
            with pytest.raises(IdentifierMalformed) as caught:
                writer.add(raw_source(identifiers, node_id=ADDR_B))
            assert (caught.value.scheme, caught.value.reason) == ("doi", "non-canonical")

    def test_an_unknown_scheme_beside_a_valid_doi_refuses(self, writer):
        node = raw_source({"doi": CANONICAL_DOI, "url": "x"}, node_id=ADDR_B)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "unknown-scheme"

    def test_a_handle_address_refuses(self, writer):
        with pytest.raises(SourceAddressDisagreement):
            writer.add(raw_source(B, node_id="source:Chen2023"))

    def test_add_refuses_a_history(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A]))

    def test_a_history_free_source_with_a_deprecated_id_refuses(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, deprecated=[ADDR_A]))

    def test_import_admits_a_well_formed_history_and_refuses_a_malformed_one(self, tmp_path):
        # `import_bundle` is a boundary operation: it needs an operation port, which this
        # module's `writer` fixture lacks. test_relocation._writer builds one with a recording port.
        from test_relocation import _writer

        from beliefs.errors import ImportRefused

        importer = _writer(tmp_path / "importer")
        report: _ImportFields = {
            "observer": "o",
            "instrument": "i",
            "opened_at": "2026-09-10T00:00:00Z",
            "closed_at": "2026-09-10T00:00:01Z",
        }
        good = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        importer.import_bundle([good], **report)
        assert importer.read_view.get(ADDR_B).deprecated_ids == [ADDR_A]
        # The malformed member claims addresses nothing else holds, so the only refusal it can
        # meet is history validation — a BundleMemberHeld on a colliding deprecated id would
        # subclass ImportRefused and satisfy a looser assertion with the validation removed.
        eight, nine = {"pmid": "8"}, {"pmid": "9"}
        bad = raw_source(
            nine,
            history=[entry(eight, nine, grounds="")],
            deprecated=[source.source_address(eight)],
        )
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle([bad], **report)
        assert type(caught.value) is ImportRefused and caught.value.member == bad.id
        assert "grounds" in str(caught.value)

    def test_a_dataset_without_content_identity_still_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(stored.dataset_node("d1", title="d", resources=[]))
