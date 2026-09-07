"""F6 and F3's revision cases (design §5.3)."""

import pytest
from authority import lacking
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    PermitExceeded,
    ReviseOutsideAllowlist,
    RevisionTargetMissing,
    ValidationRefused,
)
from beliefs.permit import Authority, WritePermit

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
ALICE = Authority(WritePermit.full(), "alice")
BOB = Authority(WritePermit.full(), "bob")
DATASET_ONLY = lacking(kinds=("proposition",), actor="alice")


def writer(root, authority):
    port = OperationRecorder(root, authority=authority, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=authority, profile=WITH_BIOLOGY, operation_port=port)
    if not (root / "corpus.yaml").exists():
        w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return w


def revised(node, **facets):
    candidate = node.model_copy(deep=True)
    for key, value in facets.items():
        if value is None:
            candidate.facets.pop(key, None)
        else:
            candidate.facets[key] = value
    return candidate


@pytest.fixture()
def minted(request, tmp_path):
    callspec = getattr(request.node, "callspec", None)
    root = tmp_path / callspec.id if callspec is not None else tmp_path
    w = writer(root, ALICE)
    node = w.add(stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": "alice"}))
    return w, node


def test_dataset_only_authority_may_revise_a_dataset_and_the_writer_restamps(tmp_path):
    w = writer(tmp_path, ALICE)
    node = w.add(stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": "alice"}))
    narrow = writer(tmp_path, DATASET_ONLY)
    candidate = revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}})
    del candidate.facets[stored.SEMANTIC_IDENTITY_FACET]
    stored_node = narrow.revise(candidate)
    assert stored_node.facets["empirical-observation"]["locator"] == "url:y"
    assert not stored.semantic_hash_disagrees(narrow.read_view.get(node.id))
    proposition = w.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    with pytest.raises(PermitExceeded):
        narrow.revise(proposition.model_copy(update={"title": "renamed"}))


def test_alice_revises_her_own_locator_keeping_herself(minted):
    w, node = minted
    w.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    assert w.read_view.get(node.id).facets["empirical-observation"]["locator"] == "url:y"


def test_bob_revising_the_locator_must_name_himself(minted, tmp_path):
    _, node = minted
    bob = writer(tmp_path, BOB)
    with pytest.raises(ActorMismatch):
        bob.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    bob.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "bob"}}))


def test_an_unchanged_declaration_keeps_its_attester(minted, tmp_path):
    _, node = minted
    bob = writer(tmp_path, BOB)
    with pytest.raises(ActorMismatch):
        bob.revise(revised(node, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    bob.revise(revised(node, **{"biology/gene-axis": {"axis": "rows"}}))


def test_removing_the_facet_is_refused_and_removing_a_domain_facet_is_not(minted):
    w, node = minted
    with_axis = w.revise(revised(node, **{"biology/gene-axis": {"axis": "rows"}}))
    w.revise(revised(with_axis, **{"biology/gene-axis": None}))
    with pytest.raises(ReviseOutsideAllowlist, match="empirical-observation"):
        w.revise(revised(node, **{"empirical-observation": None}))


@pytest.mark.parametrize(
    "field, refusal",
    [("id", RevisionTargetMissing), ("uid", RevisionTargetMissing), ("kind", ReviseOutsideAllowlist),
     ("coordination-kind", ReviseOutsideAllowlist),
     ("relations", ReviseOutsideAllowlist),
     ("deprecated_ids", ReviseOutsideAllowlist), ("metadata", ReviseOutsideAllowlist),
     ("dataset", ReviseOutsideAllowlist), ("lineage-basis", ReviseOutsideAllowlist)],
)
def test_every_preserved_field_is_refused_when_moved(minted, field, refusal):
    w, node = minted
    candidate = node.model_copy(deep=True)
    if field == "id":
        candidate.id = "dataset:other"
    elif field == "uid":
        candidate.uid = "0" * 32
    elif field == "kind":
        candidate.kind = "proposition"
    elif field == "coordination-kind":
        candidate.kind = "note"
    elif field == "relations":
        candidate.relations.append(Relation(source=node.id, predicate="reads", target="dataset:z"))
    elif field == "deprecated_ids":
        candidate.deprecated_ids = ["dataset:old"]
    elif field == "metadata":
        candidate.metadata = candidate.metadata.model_copy(update={"version": candidate.metadata.version + 1})
    elif field == "dataset":
        candidate.facets["dataset"] = {"resources": [{"name": "n", "digest": "sha256:" + "2" * 64}]}
    else:
        candidate.facets["lineage-basis"] = {"tag": "single", "routes": []}
    with pytest.raises(refusal):
        w.revise(candidate)
    assert w.read_view.get(node.id).facets == node.facets


def test_adding_the_facet_to_an_unmarked_dataset_mints_the_declaration(tmp_path):
    w = writer(tmp_path, ALICE)
    plain = w.add(stored.dataset_node("p", title="p", resources=PINNED))
    with pytest.raises(ActorMismatch):
        w.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    w.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "alice"}}))
    assert stored.dataset_declaration(w.read_view.get(plain.id)) == stored.dataset_declaration(plain)


def test_a_malformed_payload_in_a_revision_is_refused_as_a_payload_fault(minted):
    from beliefs.errors import FacetPayloadRefused

    w, node = minted
    with pytest.raises(FacetPayloadRefused, match="null"):
        w.revise(revised(node, **{"empirical-observation": {"locator": None, "attested_by": "alice"}}))


def test_display_and_prose_may_change(minted):
    w, node = minted
    candidate = node.model_copy(deep=True, update={"title": "new title"})
    candidate.facets["display"] = {"display_statement": "shown"}
    w.revise(candidate)
    assert w.read_view.get(node.id).title == "new title"


@pytest.mark.parametrize(
    "update",
    [
        {"body": "\ud800"},
        {"facets": {stored.DISPLAY_FACET: {"extra": "field"}}},
    ],
)
def test_malformed_dataset_prose_is_refused(minted, update):
    w, node = minted
    if "facets" in update:
        update["facets"] = {**node.facets, **update["facets"]}
    with pytest.raises(ValidationRefused):
        w.revise(node.model_copy(deep=True, update=update))
