"""F1–F3, F7 at the write seams: add, import, relocation. Revision is Task 9's."""

from typing import Any

import pytest
from authority import ACTOR, FULL
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import AcquisitionBoundaryRefused, ActorMismatch, FacetPayloadRefused, ImportRefused
from beliefs.permit import Authority, WritePermit

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
ALICE = Authority(WritePermit.full(), "alice")
IMPORT: dict[str, Any] = {"observer": "o", "instrument": "i", "opened_at": "2026-09-05T00:00:00Z", "closed_at": "2026-09-05T00:00:01Z"}


def writer(root, authority=FULL):
    port = OperationRecorder(root, authority=authority, profile=BASE)
    w = CorpusWriter(root, DefaultExecutor, authority=authority, profile=BASE, operation_port=port)
    if not (root / "corpus.yaml").exists():
        w.adopt_manifest(profile=pins_for(BASE))
    return w


def acquired(slug, attester, **extra):
    return stored.dataset_node(slug, title=slug, resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": attester, **extra})


def producing(slug, target):
    return stored.run_node(slug, title=slug, spec="analysis-spec:s", produces=[target])


class TestF1:
    def test_the_reproductions_authored_payload_is_refused(self, tmp_path):
        node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"boundary": "acquisition", "source": "dataset:gse", "asserted_by": "driver"})
        with pytest.raises(FacetPayloadRefused, match="unknown key"):
            writer(tmp_path).add(node)

    def test_import_wraps_the_refusal_naming_the_member(self, tmp_path):
        node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "ftp:x", "attested_by": "k"})
        with pytest.raises(ImportRefused) as caught:
            writer(tmp_path).import_bundle([node], **IMPORT)
        assert caught.value.member == node.id
        assert isinstance(caught.value.__cause__, FacetPayloadRefused)


class TestF2:
    def test_facet_dataset_then_producing_run_refuses_the_run(self, tmp_path):
        w = writer(tmp_path)
        d = w.add(acquired("d", ACTOR))
        with pytest.raises(AcquisitionBoundaryRefused, match="carries the empirical-observation facet"):
            w.add(producing("r", d.id))

    def test_producing_run_then_facet_dataset_refuses_the_dataset(self, tmp_path):
        w = writer(tmp_path)
        w.add(producing("r", "dataset:d"))
        with pytest.raises(AcquisitionBoundaryRefused, match="is produced by run:r"):
            w.add(acquired("d", ACTOR))

    def test_a_non_run_carrier_of_produces_is_refused_on_the_edge(self, tmp_path):
        w = writer(tmp_path)
        d = w.add(acquired("d", ACTOR))
        source = stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})
        source.relations.append(Relation(source=source.id, predicate="produces", target=d.id))
        with pytest.raises(AcquisitionBoundaryRefused):
            w.add(stored.stamp_semantic_identity(source))

    @pytest.mark.parametrize("order", ["dataset-first", "run-first"])
    def test_a_bundle_holding_both_is_refused_in_either_order(self, tmp_path, order):
        d, r = acquired("d", "importer"), producing("r", "dataset:d")
        members = [d, r] if order == "dataset-first" else [r, d]
        with pytest.raises(ImportRefused) as caught:
            writer(tmp_path).import_bundle(members, **IMPORT)
        assert isinstance(caught.value.__cause__, AcquisitionBoundaryRefused)
        assert not (tmp_path / "dataset").exists() and not (tmp_path / "run").exists()


class TestF3:
    def test_add_binds_the_attester_to_the_authority(self, tmp_path):
        with pytest.raises(ActorMismatch):
            writer(tmp_path, ALICE).add(acquired("d", "bob"))
        writer(tmp_path, ALICE).add(acquired("e", "alice"))

    def test_import_keeps_a_foreign_attester(self, tmp_path):
        w = writer(tmp_path, ALICE)
        w.import_bundle([acquired("d", "carol")], **IMPORT)
        assert w.read_view.get("dataset:d").facets["empirical-observation"]["attested_by"] == "carol"

    def test_relocation_keeps_a_foreign_attester(self, tmp_path):
        from test_relocation import _writer as relocation_writer

        from beliefs import relocation

        source = relocation_writer(tmp_path / "s")
        destination = relocation_writer(tmp_path / "d")
        source.import_bundle([acquired("d", "carol")], **IMPORT)
        relocation.move(source, destination, "dataset:d", **IMPORT)
        assert destination.read_view.get("dataset:d").facets["empirical-observation"]["attested_by"] == "carol"


class TestF7:
    def test_present_and_unresolved_is_refused(self, tmp_path):
        with pytest.raises(FacetPayloadRefused, match="retrieval-unresolved"):
            writer(tmp_path).add(acquired("d", ACTOR, retrieval="act-report:" + "0" * 64))

    def test_resolving_to_a_non_acquisition_report_is_refused(self, tmp_path):
        w = writer(tmp_path)
        report = w.import_bundle([stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})], **IMPORT)
        with pytest.raises(FacetPayloadRefused, match="not an acquisition"):
            w.add(acquired("d", ACTOR, retrieval=f"act-report:{report.identity()}"))

    def test_resolving_to_an_imported_acquisition_report_is_accepted(self, tmp_path, acquisition_report):
        w = writer(tmp_path)
        node = stored.act_report_node(acquisition_report)
        w.import_bundle([node], **IMPORT)
        w.add(acquired("d", ACTOR, retrieval=node.id))


@pytest.mark.parametrize("order", ["dataset-first", "run-first"])
def test_bundle_producers_follow_an_arriving_alias(tmp_path, order):
    d = acquired("d", "foreign")
    d.deprecated_ids = ["dataset:old"]
    d = stored.stamp_semantic_identity(d)
    r = producing("r", "dataset:old")
    with pytest.raises(ImportRefused) as caught:
        writer(tmp_path).import_bundle([d, r] if order == "dataset-first" else [r, d], **IMPORT)
    assert isinstance(caught.value.__cause__, AcquisitionBoundaryRefused)


@pytest.mark.parametrize("target", ["dataset:d", "dataset:old"])
def test_add_refuses_a_candidate_producing_itself(tmp_path, target):
    d = acquired("d", ACTOR)
    d.deprecated_ids = ["dataset:old"]
    d.relations.append(Relation(source=d.id, predicate="produces", target=target))
    with pytest.raises(AcquisitionBoundaryRefused, match="produces itself"):
        writer(tmp_path).add(stored.stamp_semantic_identity(d))


def test_import_sees_existing_dangling_producers(tmp_path):
    w = writer(tmp_path)
    w.add(producing("r", "dataset:d"))
    with pytest.raises(ImportRefused) as caught:
        w.import_bundle([acquired("d", "foreign")], **IMPORT)
    assert isinstance(caught.value.__cause__, AcquisitionBoundaryRefused)


def test_import_resolves_retrieval_in_the_arriving_bundle(tmp_path, acquisition_report):
    report = stored.act_report_node(acquisition_report)
    w = writer(tmp_path)
    w.import_bundle([acquired("d", "foreign", retrieval=report.id), report], **IMPORT)
    assert w.read_view.get("dataset:d").facets["empirical-observation"]["retrieval"] == report.id


def test_relocation_checks_retrieval_at_destination(tmp_path, acquisition_report):
    from test_relocation import _writer as relocation_writer

    from beliefs import relocation

    source = relocation_writer(tmp_path / "source")
    destination = relocation_writer(tmp_path / "destination")
    report = stored.act_report_node(acquisition_report)
    source.import_bundle([report, acquired("d", "foreign", retrieval=report.id)], **IMPORT)
    with pytest.raises(FacetPayloadRefused, match="retrieval-unresolved"):
        relocation.move(source, destination, "dataset:d", **IMPORT)
    assert source.read_view.holds("dataset:d")
    assert not destination.read_view.holds("dataset:d")
