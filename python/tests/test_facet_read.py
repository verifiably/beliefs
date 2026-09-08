"""B3 and B4 (biology pack design §5.1–§5.2, §5.5): the corpus reader is the
only route to a `FacetRead`, the address is the fetched dataset's own, and
every read is validated. Every row here seeds a corpus by raw write and reads
it back through a fresh `ReadView`, because that is the only door."""

from __future__ import annotations

import pytest
from fixtures_cut4 import raw_write, reopen
from profiles import WITH_BIOLOGY

from beliefs import stored
from beliefs.dataset import dataset_address
from beliefs.errors import FacetPayloadRefused, FacetUndeclared, MalformedRecord
from beliefs.facet_read import FacetRead, read_observed_facets

RESOURCES = [{"name": "r-a", "digest": "sha256:" + "a" * 64}]


def _corpus(tmp_path, **domain_facets):
    node = stored.dataset_node("d-a", title="d-a", resources=RESOURCES, domain_facets=domain_facets)
    raw_write(tmp_path, node)
    return reopen(tmp_path), dataset_address(stored.dataset_declaration(node))


def test_facet_read_has_no_field_wise_constructor():
    with pytest.raises(MalformedRecord, match="minted by the reader"):
        FacetRead("dataset:sha256:" + "a" * 64, "biology/gene-axis", "0" * 64)  # type: ignore[call-arg]
    with pytest.raises(MalformedRecord):
        FacetRead(address="dataset:sha256:" + "a" * 64, key="biology/gene-axis", payload_digest="0" * 64)  # type: ignore[call-arg]


def _facet_node():
    return stored.dataset_node("d-a", title="d-a", resources=RESOURCES, domain_facets={"biology/gene-axis": {"axis": "rows"}})


def test_the_reader_refuses_anything_but_a_corpus_view():
    """The public bypass B3 closes: an in-memory node, or any object shaped
    like a view, mints nothing."""
    node = _facet_node()

    class Shaped:
        def holds(self, ref: str) -> bool:
            return True

        def get(self, ref: str):
            return node

    with pytest.raises(MalformedRecord, match="corpus ReadView"):
        read_observed_facets(WITH_BIOLOGY, Shaped(), "dataset:d-a")  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="corpus ReadView"):
        read_observed_facets(WITH_BIOLOGY, node, "dataset:d-a")  # type: ignore[arg-type]


def test_a_view_cannot_be_subclassed_to_override_its_reads():
    """The second bypass: a subclass whose `get` returns an in-memory node
    would satisfy `isinstance`. `ReadView` is sealed, so the class statement
    itself refuses."""
    from beliefs.corpus import ReadView
    from beliefs.errors import SubclassRefused

    with pytest.raises(SubclassRefused):

        class Overriding(ReadView):  # type: ignore[misc]
            def get(self, ref: str):
                return _facet_node()


def test_a_view_over_a_fabricated_corpus_is_refused():
    """The third bypass: an exact `ReadView` wrapping an object that is not
    `nodes.core.corpus.Corpus`. The constructor checks the exact type; a
    `Corpus` subclass from `nodes` is refused too, since only the exact class
    is known to read a directory."""
    from nodes.core.corpus import Corpus

    from beliefs.corpus import ReadView

    node = _facet_node()

    class FakeCorpus:
        def get(self, ref: str):
            return node

        def holds(self, ref: str) -> bool:
            return True

    class Derived(Corpus):
        pass

    with pytest.raises(MalformedRecord, match="exactly nodes.core.corpus.Corpus"):
        ReadView(FakeCorpus())  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="exactly nodes.core.corpus.Corpus"):
        ReadView(Derived.__new__(Derived))


def test_the_reader_mints_one_row_per_declared_domain_facet(tmp_path):
    view, address = _corpus(tmp_path, **{"biology/gene-axis": {"axis": "rows"}})
    rows = read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")
    assert len(rows) == 1
    assert rows[0].address == address and rows[0].key == "biology/gene-axis"
    assert len(rows[0].payload_digest) == 64 and int(rows[0].payload_digest, 16) >= 0
    assert rows[0].projection() == [address, "biology/gene-axis", rows[0].payload_digest]


def test_the_address_is_the_fetched_datasets_own(tmp_path):
    view, address = _corpus(tmp_path, **{"biology/gene-axis": {"axis": "rows"}})
    (row,) = read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")
    assert row.address == address == dataset_address(stored.dataset_declaration(view.get("dataset:d-a")))


def test_the_digest_follows_the_payload_bytes(tmp_path):
    one, _ = _corpus(tmp_path / "one", **{"biology/gene-axis": {"axis": "rows"}})
    other, _ = _corpus(tmp_path / "other", **{"biology/gene-axis": {"axis": "columns"}})
    assert read_observed_facets(WITH_BIOLOGY, one, "dataset:d-a")[0].payload_digest != read_observed_facets(WITH_BIOLOGY, other, "dataset:d-a")[0].payload_digest


def test_base_facets_are_not_this_readers(tmp_path):
    node = stored.dataset_node(
        "d-a", title="d-a", resources=RESOURCES,
        empirical_observation={"locator": "instrument:fixture", "attested_by": "actor:fixture"},
    )
    raw_write(tmp_path, node)
    assert read_observed_facets(WITH_BIOLOGY, reopen(tmp_path), "dataset:d-a") == ()


def test_an_unheld_target_is_malformed(tmp_path):
    view, _ = _corpus(tmp_path)
    with pytest.raises(MalformedRecord, match="not held"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-missing")


def test_a_malformed_payload_refuses_the_derivation(tmp_path):
    view, _ = _corpus(tmp_path, **{"biology/gene-axis": {}})
    with pytest.raises(FacetPayloadRefused, match="missing required field 'axis'"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")


def test_an_undeclared_namespaced_key_refuses(tmp_path):
    view, _ = _corpus(tmp_path, **{"other/thing": {"x": "y"}})
    with pytest.raises(FacetUndeclared, match="facet-undeclared: 'other/thing'"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")


def test_dataset_node_refuses_an_unnamespaced_domain_facet():
    with pytest.raises(MalformedRecord, match="namespaced"):
        stored.dataset_node("d-a", title="d-a", resources=[], domain_facets={"display": {"display_statement": "x"}})
