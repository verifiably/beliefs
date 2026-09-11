"""Cut 24 over registered roots and the composition root's durable executors."""

from __future__ import annotations

import inspect
from dataclasses import replace
from hashlib import sha256

import pytest
from authority import FULL
from fixtures_cut4 import path_for, raw_write, reopen
from nodes.core.node import Node
from profiles import BASE
from test_closure import closure_kwargs
from test_coreference_attestation import LEFT, PINNED, RIGHT, attestation, endpoints_and
from test_deletion_acceptance import _audit_log
from test_durable_families import proposition
from test_facet_seams import IMPORT
from test_local_standing import raw_retraction, retracts
from test_world_receipts import document, hold_shipped, outcomes, publish, repackage
from test_world_view_acceptance import durable_world as durable_world  # noqa: PLC0414

from beliefs import corpus, relocation, stored
from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.corpus import CorpusWriter, OperationWrites, RelationAdjacency, lineage_snapshot
from beliefs.errors import (
    AddressMapConflict,
    CoreferenceEndpointRefused,
    EdgeIndeterminate,
    ImportRefused,
    MalformedRecord,
    WriteRefused,
)
from beliefs.root import open_corpus
from beliefs.traversal import closure
from beliefs.world import derive, epoch, read, rules
from beliefs.world.view import open_world_view

INVENTORY = (
    "add",
    "retract",
    "attest_coreference",
    "supersede",
    "revise",
    "delete",
    "mint_coordination",
    "revise_coordination",
)
RELOCATION = {"observer": "corpus", "instrument": "cut24", "opened_at": "T0", "closed_at": "T1"}


@pytest.fixture()
def pair(durable_world):
    return durable_world(endpoints_and(), ())


def writer_at(roots, corpus_id, actor=FULL.actor):
    return open_corpus(roots[corpus_id], authority=replace(FULL, actor=actor), profile=BASE)


def attest(writer, *, left=LEFT, right=RIGHT, stance=1, grounds="one work", token, view=None):
    return writer.attest_coreference(
        stored.coreference_attestation_node(
            title="coreference",
            endpoints=(left, right),
            stance=stance,
            actor=writer.authority.actor,
            grounds=grounds,
            event_token=token,
        ),
        view=view,
    )


def republish(world, coverage):
    return publish(world, coverage, hold_shipped(world))


def balance(published, left=LEFT, right=RIGHT):
    pairs = {
        tuple(p["endpoints"]): (p["balance"], p["distinct_key_count"])
        for p in document(published, "coreference-map.yaml")["pairs"]
    }
    return pairs.get(tuple(sorted((left, right))))


def weighted(pair):
    world, roots, published, a, b = pair
    attest(writer_at(roots, a, "human-a"), token="plus-1")
    attest(writer_at(roots, a, "agent-b"), token="plus-2")
    attest(writer_at(roots, b, "human-c"), stance=-1, token="minus", view=open_world_view(world, published))
    return world, roots, republish(world, (a, b)), a, b


def claimed_balance(world, published, value, count):
    wrong = {"pairs": [{"endpoints": [LEFT, RIGHT], "balance": value, "distinct_key_count": count}]}
    receipt = dict(
        document(published, "coreference-receipt.yaml"), subject=derive.subject_identity("coreference-reduction", wrong)
    )
    return repackage(world, published, {"coreference-map.yaml": wrong, "coreference-receipt.yaml": receipt})


def belief_closure(world, published):
    kwargs = closure_kwargs()
    kwargs["snapshot"] = lineage_snapshot(open_world_view(world, published), (LEFT,))
    kwargs["producer_snapshot_identity"] = derive.belief_input_identity(tuple(published.receipts.values()))
    enumeration = document(published, "retraction-receipt.yaml")["enumeration"]
    kwargs["retractions"] = RetractionEnumeration(
        found=tuple(tuple(row) for row in enumeration["found"]), coverage=tuple(enumeration["coverage"])
    )
    return build_closure(**kwargs)


def retract_route(writer, ref, token):
    node = writer.read_view.get(ref)
    identity = stored.stored_semantic_hash(node)
    assert identity is not None
    return writer.retract(
        stored.retraction_node(
            title=token,
            target=stored.RouteTarget(ref, ref, identity, "route:one"),
            reason="wrong-route",
            rationale="the route is invalid",
            grounds=("verification:v1",),
            actor=writer.authority.actor,
            event_token=token,
        )
    )


def test_the_four_endpoint_refusals_durably(pair):
    world, roots, published, a, b = pair
    writer = writer_at(roots, a)
    writer.add(Node(id="discussion:d", kind="discussion", title="d"))
    writer.add(Node(id="discussion:e", kind="discussion", title="e"))
    source = writer.add(stored.source_node(title="s", identifiers={"doi": "10.1234/x"}))
    for endpoints, reason in (
        (("discussion:d", "discussion:e"), "inadmissible-kind"),
        ((LEFT, "dataset:missing"), "unresolved"),
        ((LEFT, source.id), "kind-mismatch"),
        ((LEFT, LEFT), "self-pair"),
    ):
        node = attestation()
        node.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = list(endpoints)
        if reason != "self-pair":
            node = attestation(endpoints=endpoints)
        with pytest.raises(CoreferenceEndpointRefused) as refused:
            writer.attest_coreference(node)
        assert refused.value.reason == reason
    # A real mapped endpoint on the absent carrier, not an unknown address.
    remote = writer_at(roots, b).add(stored.dataset_node("remote", title="remote", resources=PINNED))
    published = republish(world, (a, b))
    manifest = roots[b] / "corpus.yaml"
    mounted = manifest.read_bytes()
    manifest.unlink()
    view = open_world_view(world, published)
    assert type(view.locate(remote.id)) is read.NotPresent
    with pytest.raises(CoreferenceEndpointRefused) as refused:
        attest(writer, right=remote.id, token="absent", view=view)
    assert (refused.value.reason, refused.value.endpoint, refused.value.corpus_id) == ("unresolved", remote.id, b)
    manifest.write_bytes(mounted)
    writer._corpus.rename(LEFT, "dataset:left-renamed")
    view = open_world_view(world, republish(world, (a, b)))
    assert view.resolve(LEFT) == "dataset:left-renamed"
    with pytest.raises(CoreferenceEndpointRefused) as refused:
        attest(writer, token="retired", view=view)
    assert (refused.value.reason, refused.value.endpoint) == ("unresolved", LEFT)


def test_the_balance_sequence_is_attester_symmetric_and_retains_every_record_durably(pair):
    world, roots, _published, a, b = pair
    first = attest(writer_at(roots, a, "human-a"), grounds="first reason", token="1")
    second = attest(writer_at(roots, a, "agent-b"), grounds="second reason", token="2")
    published = republish(world, (a, b))
    assert balance(published) == (2, 2)
    assert read.coreference_edge(world, published, LEFT, RIGHT).state == "active"
    writer = writer_at(roots, a)
    writer.delete(first.id)
    writer.delete(second.id)
    attest(writer_at(roots, a, "agent-b"), grounds="first reason", token="1")
    attest(writer_at(roots, a, "human-a"), grounds="second reason", token="2")
    swapped = republish(world, (a, b))
    assert swapped.members["coreference-map.yaml"] == published.members["coreference-map.yaml"]
    for actor, token, weight, state, count in (("human-a", "3", 1, "active", 3), ("human-c", "4", 0, "inactive", 4)):
        attest(writer_at(roots, a, actor), stance=-1, token=token)
        current = republish(world, (a, b))
        assert balance(current) == (weight, count)
        assert read.coreference_edge(world, current, LEFT, RIGHT).state == state
        assert len([n for n in writer.read_view.iter_stored() if n.kind == "coreference-attestation"]) == count


def test_exact_duplicates_add_no_weight_and_different_grounds_do_durably(pair):
    world, roots, published, a, b = pair
    writer = writer_at(roots, a)
    assert balance(published) is None
    assert read.coreference_edge(world, published, LEFT, RIGHT).state == "inactive"
    addresses = set()
    for i in range(10):
        addresses.add(attest(writer, token=str(i)).id)
        if i in (0, 9):
            assert balance(republish(world, (a, b))) == (1, 1)
    assert len(addresses) == 10
    assert addresses == {n.id for n in writer.read_view.iter_stored() if n.kind == "coreference-attestation"}
    attest(writer, grounds="different grounds", token="10")
    assert balance(republish(world, (a, b))) == (2, 2)


def test_closure_rewrites_nothing_durably(durable_world):
    left, right = endpoints_and()
    left.facets[stored.LINEAGE_BASIS_FACET] = {
        "tag": "single",
        "routes": [{"identity": "route:one", "run": "run:r", "ancestor": RIGHT, "transforms": [RIGHT]}],
    }
    stored.stamp_semantic_identity(left)
    claim = proposition("claim")
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[LEFT], transforms=[RIGHT])
    world, roots, _published, a, b = durable_world((left, claim), (right, run))
    writer = writer_at(roots, a)
    retraction = retract_route(writer, LEFT, "retract-left")
    published = republish(world, (a, b))
    before = {path: path.read_bytes() for root in roots.values() for path in root.glob("*/*.md")}
    view = open_world_view(world, published)
    projection = stored.semantic_projection(view.get(claim.id))
    traversals = (
        view.inbound(LEFT),
        view.inbound(RIGHT),
        closure(LEFT, RelationAdjacency(view, "cites", "inbound")),
        view.producers(LEFT),
        view.producers(RIGHT),
    )
    original_closure = belief_closure(world, published)
    assert lineage_snapshot(view, (LEFT,)).roots == (LEFT,)
    attest(writer, token="closure", view=view)
    current = republish(world, (a, b))
    assert read.coreference_edge(world, current, LEFT, RIGHT).state == "active"
    view = open_world_view(world, current)
    assert {path: path.read_bytes() for path in before} == before
    assert view.get(retraction.id).facets["retraction"]["target"]["dataset"] == LEFT
    assert stored.semantic_projection(view.get(claim.id)) == projection
    assert belief_closure(world, current).digest() == original_closure.digest()
    assert (
        view.inbound(LEFT),
        view.inbound(RIGHT),
        closure(LEFT, RelationAdjacency(view, "cites", "inbound")),
        view.producers(LEFT),
        view.producers(RIGHT),
    ) == traversals


def test_coverage_bounds_the_balance_and_no_epoch_is_unspellable_durably(pair):
    world, _roots, published, a, b = weighted(pair)
    assert balance(published) == (1, 3)
    assert read.coreference_edge(world, published, LEFT, RIGHT).state == "active"
    narrow = republish(world, (a,))
    assert balance(narrow) == (2, 2) and narrow.coverage != published.coverage
    answer = read.coreference_edge(world, narrow, LEFT, RIGHT)
    assert answer.state == "indeterminate" and answer.missing_coverage == (b,)
    with pytest.raises(EdgeIndeterminate, match=b) as refused:
        read.expand_coreference(world, narrow, LEFT)
    assert refused.value.missing_coverage == (b,)
    for method in (read.coreference_edge, read.expand_coreference):
        assert inspect.signature(method).parameters["published"].default is inspect.Parameter.empty
        assert "current" not in inspect.signature(method).parameters


def test_the_three_non_validated_outcomes_refuse_expansion_durably(pair):
    world, _roots, published, _a, _b = weighted(pair)
    wrong = claimed_balance(world, published, 99, 3)
    receipt = dict(document(published, "coreference-receipt.yaml"), implementation_identity="v1")
    malformed = repackage(world, published, {"coreference-receipt.yaml": receipt})
    for claimed, expected in ((wrong, "refuted"), (malformed, "malformed"), (published, "unresolvable")):
        if expected == "unresolvable":
            rules.remove_rule_binding(world, hold_shipped(world).coreference)
        answer = read.coreference_edge(world, claimed, LEFT, RIGHT)
        assert (answer.state, answer.receipt_outcome) == ("indeterminate", expected)
        with pytest.raises(EdgeIndeterminate) as refused:
            read.expand_coreference(world, claimed, LEFT)
        assert refused.value.receipt_outcome == expected


def test_an_unmounted_covered_corpus_still_contributes_to_the_published_balance_durably(pair):
    world, roots, published, _a, b = weighted(pair)
    manifest = roots[b] / "corpus.yaml"
    mounted = manifest.read_bytes()
    manifest.unlink()
    assert balance(published) == (1, 3)
    answer = read.coreference_edge(world, published, LEFT, RIGHT)
    assert (answer.state, answer.receipt_outcome) == ("indeterminate", "unresolvable")
    manifest.write_bytes(mounted)
    assert read.coreference_edge(world, published, LEFT, RIGHT).state == "active"


def test_coreference_between_retractions_closes_no_route_durably(durable_world, monkeypatch):
    nodes = []
    for ref in ("left", "right"):
        nodes.append(
            stored.dataset_node(
                ref, title=ref, resources=PINNED, basis={"tag": "single", "routes": [{"identity": "route:one"}]}
            )
        )
    world, roots, _published, a, b = durable_world((nodes[0],), (nodes[1],))
    writers = (writer_at(roots, a), writer_at(roots, b))
    targets = tuple(retract_route(w, n.id, str(i)) for i, (w, n) in enumerate(zip(writers, nodes, strict=True)))
    retractions = tuple(
        w.retract(retracts(n, f"counter-{i}")) for i, (w, n) in enumerate(zip(writers, targets, strict=True))
    )
    refs = tuple(n.id for n in retractions)
    before = {
        path_for(w.root, n.id): path_for(w.root, n.id).read_bytes() for w, n in zip(writers, retractions, strict=True)
    }
    standing = tuple(corpus.standing_in_local_view(w.read_view, n.id) for w, n in zip(writers, targets, strict=True))
    assert standing == (False, False)
    published = republish(world, (a, b))
    attest(writers[0], left=refs[0], right=refs[1], token="cycle", view=open_world_view(world, published))
    published = republish(world, (a, b))
    assert read.coreference_edge(world, published, *refs).state == "active"
    assert read.expand_coreference(world, published, refs[0]) == (refs[1],)
    assert {path: path.read_bytes() for path in before} == before
    assert (
        tuple(corpus.standing_in_local_view(w.read_view, n.id) for w, n in zip(writers, targets, strict=True))
        == standing
    )
    for writer in writers:
        assert writer._import_cycle_edges(()) == ()
        assert not [f for f in corpus.corpus_check(writer.read_view, BASE) if f.code.startswith("retraction-")]
        assert all(
            e.relation.source not in refs for ref in refs for e in open_world_view(world, published).inbound(ref)
        )
    witness = tuple(sorted(((refs[0], refs[1]), (refs[1], refs[0]))))
    assert corpus._cycle_edges({refs[0]: (refs[1],), refs[1]: (refs[0],)}) == witness
    before_records = {p: p.read_bytes() for p in writers[0].root.glob("*/*.md")}
    with monkeypatch.context() as patch:
        patch.setattr(CorpusWriter, "_import_cycle_edges", lambda _self, _records: (witness[0],))
        with pytest.raises(ImportRefused) as refused:
            writers[0].import_bundle((proposition("forced-cycle"),), **IMPORT)
        assert refused.value.cycle_edges == (witness[0],)
        assert not writers[0].read_view.holds("proposition:forced-cycle")
        assert {p: p.read_bytes() for p in before_records} == before_records
        assert {p.parent.name for p in writers[0].root.glob("*/*.md") if p not in before_records} <= {"act-report"}
    # Cut 18's raw shapes: malformed controlled identities, not a constructible controlled cycle.
    raw = (raw_retraction("retraction:r1", "retraction:r2"), raw_retraction("retraction:r2", "retraction:r1"))
    for writer, node in zip(writers, raw, strict=True):
        raw_write(writer.root, node)
        assert not stored.semantic_hash_disagrees(node)
    classified = tuple(
        tuple(f for f in corpus.corpus_check(w.read_view, BASE) if f.ref in {n.id for n in raw}) for w in writers
    )
    assert all(
        any(f.code == "retraction-target-invalid" and "controlled stored shape" in f.message for f in findings)
        for findings in classified
    )
    published = republish(world, (a, b))
    attest(writers[0], left=raw[0].id, right=raw[1].id, token="raw-cycle", view=open_world_view(world, published))
    published = republish(world, (a, b))
    assert read.coreference_edge(world, published, raw[0].id, raw[1].id).state == "active"
    assert (
        tuple(tuple(f for f in corpus.corpus_check(w.read_view, BASE) if f.ref in {n.id for n in raw}) for w in writers)
        == classified
    )
    for root in roots.values():
        with pytest.raises(MalformedRecord):
            corpus.standing_in_local_view(reopen(root), "assessment:unrelated")


def test_membership_follows_coverage_durably(pair):
    world, roots, _published, a, b = pair
    attest(writer_at(roots, a), token="membership")
    included, excluded = republish(world, (a,)), republish(world, (b,))
    assert balance(included) == (1, 1) and balance(excluded) is None
    assert tuple(dict(included.coverage)) == (a,) and tuple(dict(excluded.coverage)) == (b,)


def test_omission_and_a_wrong_balance_refute_and_move_no_digest_durably(pair):
    world, _roots, published, _a, _b = weighted(pair)
    for value, count in ((0, 2), (99, 3)):
        claimed = claimed_balance(world, published, value, count)
        assert outcomes(world, claimed) == {
            "producer": "validated",
            "retraction-enumeration": "validated",
            "certification-enumeration": "validated",
            "coreference-reduction": "refuted",
        }
        assert read.coreference_edge(world, claimed, LEFT, RIGHT).state == "indeterminate"
        assert belief_closure(world, claimed).digest() == belief_closure(world, published).digest()


def test_a_membership_only_rebuild_does_not_validate_a_wrong_balance_durably(pair):
    world, _roots, published, _a, _b = weighted(pair)
    claimed = claimed_balance(world, published, 99, 3)
    assert [p["endpoints"] for p in document(claimed, "coreference-map.yaml")["pairs"]] == [
        p["endpoints"] for p in document(published, "coreference-map.yaml")["pairs"]
    ]
    assert read.validate_receipt(world, claimed, "coreference-reduction").outcome == "refuted"


def test_unresolvable_for_an_unmounted_and_for_a_moved_named_state_durably(pair):
    world, roots, published, _a, b = weighted(pair)
    manifest = roots[b] / "corpus.yaml"
    mounted = manifest.read_bytes()
    manifest.unlink()
    assert read.validate_receipt(world, published, "coreference-reduction").outcome == "unresolvable"
    manifest.write_bytes(mounted)
    assert read.validate_receipt(world, published, "coreference-reduction").outcome == "validated"
    attest(writer_at(roots, b), token="later", view=open_world_view(world, published))
    assert read.validate_receipt(world, published, "coreference-reduction").outcome == "unresolvable"


def test_the_digest_boundary_holds_on_one_coverage_durably(pair):
    world, roots, published, a, b = weighted(pair)
    assert {n.kind for n in writer_at(roots, b).read_view.iter_stored()} == {"coreference-attestation"}
    narrow = republish(world, (a,))
    assert balance(published) == (1, 3) and balance(narrow) == (2, 2)
    assert published.coverage != narrow.coverage
    assert belief_closure(world, published).digest() != belief_closure(world, narrow).digest()
    before = belief_closure(world, published).digest()
    view = open_world_view(world, published)
    for token in ("extra-1", "extra-2"):
        attest(writer_at(roots, b), grounds=token, token=token, view=view)
    after = republish(world, (a, b))
    assert (
        after.receipts["producer-receipt.yaml"].subject_identity
        == published.receipts["producer-receipt.yaml"].subject_identity
    )
    assert after.members["coreference-map.yaml"] != published.members["coreference-map.yaml"]
    assert belief_closure(world, after).digest() == before


def test_no_operation_retires_an_address_on_coreference_grounds_durably(pair):
    world, roots, _published, a, b = pair
    writer = writer_at(roots, a)
    before = {ref: path_for(writer.root, ref).read_bytes() for ref in (LEFT, RIGHT)}
    attest(writer, token="no-merge")
    published = republish(world, (a, b))
    for ref in (LEFT, RIGHT):
        assert path_for(writer.root, ref).read_bytes() == before[ref]
        assert writer.read_view.resolve(ref) == ref and not writer.read_view.get(ref).deprecated_ids
        assert type(read.resolve_address(world, published, ref)) is read.Resolved
    assert not any(name == "merge" for name in dir(OperationWrites))
    assert not hasattr(CorpusWriter, "merge") and not hasattr(relocation, "merge")
    assert set(INVENTORY) <= {n for n in dir(OperationWrites) if not n.startswith("_")}
    for name in INVENTORY:
        assert "deprecated_ids" not in inspect.getsource(getattr(CorpusWriter, name))
    for method in (relocation.move, relocation.consolidate):
        assert "deprecated_ids" not in inspect.getsource(method)
    assert "{*survivor.deprecated_ids, *loser.deprecated_ids}" in inspect.getsource(relocation._reconcile)


def test_lifecycle_treats_an_attestation_as_a_retraction_s_peer_durably(pair):
    world, roots, _published, a, b = pair
    left, right = writer_at(roots, a), writer_at(roots, b)
    node = attest(left, token="move")
    initial = republish(world, (a, b))
    relocation.move(left, right, node.id, **RELOCATION)
    moved = republish(world, (a, b))
    assert balance(moved) == balance(initial) == (1, 1)
    payload = path_for(right.root, node.id).read_bytes()
    right.delete(node.id)
    assert balance(republish(world, (a, b))) is None
    audited = _audit_log(right, history={f"sha256:{sha256(payload).hexdigest()}": payload})
    assert audited.outcome == "validated"
    assert any(
        f.code == "record-removed" and f.ref == str(path_for(right.root, node.id).relative_to(right.root))
        for f in audited.findings
    )
    # The bundle can put the attestation first; endpoints arrive in the same act, actor retained.
    imported = attestation(
        endpoints=("dataset:import-left", "dataset:import-right"), actor="original-author", token="import"
    )
    endpoints = tuple(
        stored.dataset_node(slug, title=slug, resources=PINNED) for slug in ("import-left", "import-right")
    )
    left.import_bundle((imported, *endpoints), **IMPORT)
    assert stored.coreference_attestation_value(left.read_view.get(imported.id)).actor == "original-author"
    right.import_bundle(
        (
            imported.model_copy(deep=True, update={"uid": "c" * 32}),
            *[n.model_copy(deep=True, update={"uid": str(i) * 32}) for i, n in enumerate(endpoints, 1)],
        ),
        **IMPORT,
    )
    bindings = hold_shipped(world)
    draft = epoch._capture_build_inputs(world, coverage=frozenset((a, b)), bindings=bindings.by_kind())
    duplicated = derive.coreference_map(draft.run("coreference-reduction"))
    assert dict(duplicated.pairs) == {stored.coreference_attestation_value(imported).endpoints: (1, 1)}
    with pytest.raises(AddressMapConflict, match="duplicate-location"):
        publish(world, (a, b), bindings)
    relocation.consolidate((left, imported.id), (right, imported.id), rationale="one replica", **RELOCATION)
    # The imported endpoints are replicas too; settle their locations before publishing.
    for endpoint in endpoints:
        relocation.consolidate((left, endpoint.id), (right, endpoint.id), rationale="one endpoint", **RELOCATION)
    consolidated = republish(world, (a, b))
    assert sum(w.read_view.holds(imported.id) for w in (left, right)) == 1
    assert (
        balance(consolidated, *stored.coreference_attestation_value(imported).endpoints)
        == dict(duplicated.pairs)[stored.coreference_attestation_value(imported).endpoints]
    )
    with pytest.raises(WriteRefused, match="attest_coreference"):
        left.add(attestation(token="add"))
    malformed = attestation(token="malformed")
    malformed.facets[stored.COREFERENCE_ATTESTATION_FACET]["stance"] = 5
    with pytest.raises(ImportRefused) as refused:
        left.import_bundle((malformed,), **IMPORT)
    assert refused.value.member == malformed.id
    source = stored.source_node(title="s", identifiers={"doi": "10.1234/x"})
    for endpoints, reason in (
        ((LEFT, "dataset:missing"), "unresolved"),
        ((LEFT, source.id), "kind-mismatch"),
        (("discussion:d", "discussion:e"), "inadmissible-kind"),
        ((LEFT, LEFT), "self-pair"),
    ):
        bad = attestation(token=reason)
        bad.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = list(endpoints)
        if reason != "self-pair":
            bad = attestation(endpoints=endpoints, token=reason)
        extras = (source,) if reason == "kind-mismatch" else ()
        with pytest.raises(ImportRefused) as refused:
            left.import_bundle((bad, *extras), **IMPORT)
        assert refused.value.member == bad.id
