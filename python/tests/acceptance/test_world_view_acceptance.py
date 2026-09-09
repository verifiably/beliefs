"""Cut 23 over registered roots and the composition root's durable executors."""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, cast

import pytest
from authority import FULL
from domain_facet_fixtures import kwargs_for, profile_with, seed
from durable_fixture import pinned
from fixtures_cut4 import raw_write
from nodes.core.errors import RefError
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from profiles import BASE, pins_for
from test_evaluation import EX, GENE
from test_world_receipts import hold_shipped, publish
from test_world_view import chain_nodes
from verification_fixtures import publish_corpus, self_consistent_forgery

from beliefs import stored
from beliefs.audit import check_verification
from beliefs.belief import Belief, NoBelief, Refused
from beliefs.corpus import LineageAdjacency, ReadView, RelationAdjacency, _absence_of, lineage_snapshot
from beliefs.errors import (
    BuildContended,
    CaptureDrift,
    EpochUnknown,
    MalformedRecord,
    RecordNotPresent,
    ResolutionError,
    ResolutionRefused,
    SemanticHashStale,
)
from beliefs.evaluation import evaluate_over, gather
from beliefs.lineage import Absence, certify, divergence_state, snapshot_projection
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.root import init_corpus_root, init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.traversal import closure
from beliefs.world import Fresh, WorldConfig, read
from beliefs.world.view import open_world_view


@pytest.fixture()
def durable_world(work_directory):
    """Own only this test's roots: N2's subprocesses share work_directory."""
    roots = []

    def corpus(profile=BASE):
        path = Path(mkdtemp(prefix="cut23-corpus-", dir=work_directory))
        roots.append(path)
        init_corpus_root(path, authority=FULL)
        writer = open_corpus(path, authority=FULL, profile=profile)
        manifest = writer.adopt_manifest(profile=pins_for(profile))
        return manifest.corpus_id, path, writer

    def make(alpha_nodes, beta_nodes, *, profile=BASE, raw=()):
        a, alpha, left = corpus(profile)
        b, beta, right = corpus(profile)
        for writer, nodes, other in ((left, alpha_nodes, beta_nodes), (right, beta_nodes, alpha_nodes)):
            # S7 admits assessments only with local prerequisites. Stage those
            # through the durable writer, then remove the copies before publication.
            staging = (
                tuple(n for n in other if n.kind in ("dataset", "run", "proposition"))
                if any(n.kind == "assessment" for n in nodes)
                else ()
            )
            for node in sorted(
                (*staging, *nodes), key=lambda n: (n.kind in ("assessment", "verification"), n.kind == "verification")
            ):
                node = node.model_copy(deep=True)
                if node.kind == "dataset" and not node.facets["dataset"]["resources"]:
                    node.facets["dataset"]["resources"] = pinned()
                    stored.stamp_semantic_identity(node)
                writer.add(node)
            for node in staging:
                writer.delete(node.id)
            assert {n.id for n in writer.read_view.iter_stored()} == {n.id for n in nodes}
        for node in raw:
            raw_write(alpha, node)  # A deliberately forged record, never an admitted write.
        path = Path(mkdtemp(prefix="cut23-world-", dir=work_directory))
        roots.append(path)
        config = WorldConfig(path, "e" * 32, (alpha, beta))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(alpha, provenance=Fresh())
        world.admit(beta, provenance=Fresh())
        published = publish(world, (a, b), hold_shipped(world))
        return world, {a: alpha, b: beta}, published, a, b

    make.corpus = corpus
    try:
        yield make
    finally:
        for path in roots:
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)


@pytest.fixture()
def chain(durable_world):
    d0, r1, d1, r2, d2 = chain_nodes()
    # A real relation chain as well as the lineage facet chain; one dangling edge.
    d2.relations.extend(
        [
            Relation(source=d2.id, predicate="cites", target=d1.id),
            Relation(source=d2.id, predicate="cites", target="dataset:unknown"),
        ]
    )
    d1.relations.append(Relation(source=d1.id, predicate="cites", target=d0.id))
    return durable_world((d0, r2, d2), (r1, d1))


def absent(roots, corpus_id):
    (roots[corpus_id] / "corpus.yaml").unlink()


def test_the_world_closure_is_complete_and_the_local_one_truncates_durably(chain):
    world, roots, published, a, _b = chain
    view = open_world_view(world, published)
    reached = closure("dataset:d2", LineageAdjacency(view))
    assert set(reached.reached) == {"dataset:d1", "dataset:d0"} and not reached.unresolved
    local = ReadView.opened_at(roots[a])
    truncated = closure("dataset:d2", LineageAdjacency(local))
    assert not truncated.reached and truncated.unresolved
    assert "lineage-incomplete" in certify(lineage_snapshot(local, ["dataset:d2"]), ("dataset:d2",), ()).findings
    assert certify(lineage_snapshot(view, ["dataset:d2"]), ("dataset:d2",), ()).state == "independent"
    assert {e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "transforms"} == {"run:r2"}


def test_the_relation_and_lineage_chains_cross_the_edge_durably(chain):
    world, roots, published, a, b = chain
    view = open_world_view(world, published)
    relation = closure("dataset:d2", RelationAdjacency(view, "cites", "outbound"))
    assert set(relation.reached) == {"dataset:d1", "dataset:d0"}
    assert len(relation.unresolved) == 1
    assert set(closure("dataset:d0", RelationAdjacency(view, "cites", "inbound")).reached) == {
        "dataset:d1",
        "dataset:d2",
    }
    assert set(closure("dataset:d2", LineageAdjacency(view)).reached) == {"dataset:d1", "dataset:d0"}
    assert not closure("dataset:d2", RelationAdjacency(ReadView.opened_at(roots[a]), "cites", "outbound")).reached
    late = stored.run_node("late", title="late", spec="s", produces=["dataset:d2"])
    raw_write(roots[a], late)
    raw_write(roots[a], stored.dataset_node("d1", title="drift copy of B's mapped target", resources=pinned()))
    drift = open_world_view(world, published)
    assert "run:late" not in {e.relation.source for e in drift.inbound("dataset:d2")}
    assert drift.producers("dataset:d2") == ("run:r2",)
    assert drift.corpus_of("dataset:d1") == b
    assert {e.relation.source for e in drift.inbound("dataset:d1") if e.relation.predicate == "transforms"} == {
        "run:r2"
    }


def test_an_absent_corpus_is_lineage_incomplete_naming_it_durably(chain):
    world, roots, published, a, b = chain
    complete = lineage_snapshot(open_world_view(world, published), ["dataset:d2"])
    absent(roots, b)
    view = open_world_view(world, published)
    assert type(view.locate("dataset:d1")) is read.NotPresent
    partial = lineage_snapshot(view, ["dataset:d2"])
    assert partial.not_present == {"dataset:d1": b}
    result = certify(partial, ("dataset:d2",), ())
    assert result.state == "not-certified" and "lineage-incomplete" in result.findings
    assert result.absent == (Absence("dataset:d1", b),)
    assert snapshot_projection(partial) != snapshot_projection(complete)
    # Identical topology, only the coverage evidence differs: this kills omission
    # of not_present without letting other projection differences mask it.
    unknown = replace(partial, not_present={})
    assert snapshot_projection(partial) != snapshot_projection(unknown)
    assert snapshot_projection(partial)["not_present"] == [{"ref": "dataset:d1", "corpus_id": b}]
    local = lineage_snapshot(ReadView.opened_at(roots[a]), ["dataset:d2"])
    assert not local.not_present
    both = lineage_snapshot(view, ["dataset:d2", "dataset:d1"])
    assert both.not_present == {"dataset:d1": b}  # R1 is behind the unreadable basis.


def split_producer(durable_world):
    d0 = stored.dataset_node("d0", title="d0")
    r3 = stored.run_node("r3", title="r3", spec="s", transforms=[d0.id], produces=["dataset:d3"])
    d3 = stored.dataset_node(
        "d3", title="d3", basis={"tag": "single", "routes": [{"run": r3.id, "ancestor": d0.id, "transforms": [d0.id]}]}
    )
    return durable_world((d0, d3), (r3,))


def test_a_published_producer_survives_its_absent_carrier_durably(durable_world):
    world, roots, published, a, b = split_producer(durable_world)
    present = lineage_snapshot(open_world_view(world, published), ["dataset:d3"])
    assert divergence_state(present, "dataset:d3") == "undiverged"
    absent(roots, b)
    gone = lineage_snapshot(open_world_view(world, published), ["dataset:d3"])
    (producer,) = gone.producers["dataset:d3"]
    assert producer.stored_run == "run:r3" and producer.resolved_run is None and producer.absent == (b,)
    assert gone.not_present == {"run:r3": b}
    assert divergence_state(gone, "dataset:d3") == "incomplete"
    assert snapshot_projection(gone)["divergence"] == {"dataset:d3": "incomplete"}
    result = certify(gone, ("dataset:d3",), ())
    assert result.absent == (Absence("run:r3", b),)
    assert "lineage-incomplete" in result.findings and "lineage-divergent" not in result.findings
    fabricated = replace(gone, not_present={}, producers={"dataset:d3": (replace(producer, absent=()),)})
    assert divergence_state(fabricated, "dataset:d3") == "divergent"
    assert not lineage_snapshot(ReadView.opened_at(roots[a]), ["dataset:d3"]).producers["dataset:d3"]


def test_an_absent_dataset_is_incomplete_without_a_comparison_durably(chain):
    world, roots, published, _a, b = chain
    absent(roots, b)
    snapshot = lineage_snapshot(open_world_view(world, published), ["dataset:d1"])
    assert "dataset:d1" not in snapshot.bases and "dataset:d1" not in snapshot.producers
    assert snapshot.not_present == {"dataset:d1": b}
    result = certify(snapshot, ("dataset:d1",), ())
    assert result.state == "not-certified" and "lineage-incomplete" in result.findings
    assert "lineage-divergent" not in result.findings


def test_an_absent_root_is_recorded_before_any_walk_durably(chain):
    world, roots, published, a, b = chain
    absent(roots, b)
    view = open_world_view(world, published)
    snapshot = lineage_snapshot(view, ["dataset:d1"])
    assert snapshot.roots == ("dataset:d1",) and snapshot.not_present == {"dataset:d1": b}
    assert certify(snapshot, ("dataset:d1",), ()).absent == (Absence("dataset:d1", b),)
    for reader in (view, ReadView.opened_at(roots[a])):
        with pytest.raises(RefError):
            lineage_snapshot(reader, ["dataset:unknown"])


def test_absence_names_what_each_root_can_discover_durably(chain, durable_world):
    world, roots, published, _a, b = chain
    absent(roots, b)
    snapshot = lineage_snapshot(open_world_view(world, published), ["dataset:d2"])
    result = certify(snapshot, ("dataset:d2",), ())
    assert result.absent == (Absence("dataset:d1", b),)
    assert all(item.ref != "run:r1" for item in result.absent)
    world, roots, published, _a, b = split_producer(durable_world)
    absent(roots, b)
    snapshot = lineage_snapshot(open_world_view(world, published), ["dataset:d3"])
    assert certify(snapshot, ("dataset:d3",), ()).absent == (Absence("run:r3", b),)


def test_a_refusal_is_not_absence_durably(chain):
    world, roots, published, a, _b = chain
    node = ReadView.opened_at(roots[a]).get("dataset:d2")
    node.facets["dataset"]["resources"] = [{"digest": "sha256:" + "f" * 64}]
    (roots[a] / "dataset" / "d2.md").write_text(node_to_markdown(node))  # deliberately stale stamp
    view = open_world_view(world, published)
    assert type(view.locate(node.id)) is read.Resolved and view.absent() == ()
    assert _absence_of(view, node.id) is None
    with pytest.raises(SemanticHashStale):
        lineage_snapshot(view, [node.id])
    with pytest.raises(SemanticHashStale):
        lineage_snapshot(ReadView.opened_at(roots[a]), [node.id])


def test_the_capture_is_coherent_and_drift_is_the_next_opens_durably(chain):
    world, roots, published, a, _b = chain
    first = open_world_view(world, published)
    before = first.get("dataset:d2")
    stored_before = tuple(first.iter_stored())
    inbound_before = first.inbound("dataset:d1")
    late = stored.run_node("late", title="late", spec="s", produces=["dataset:d2"])
    raw_write(roots[a], late)
    changed = before.model_copy(deep=True)
    changed.title = "edited after capture"
    changed.relations.append(Relation(source=changed.id, predicate="cites", target="dataset:d0"))
    raw_write(roots[a], changed)
    assert first.get(before.id) == before
    assert tuple(first.iter_stored()) == stored_before and first.inbound("dataset:d1") == inbound_before
    assert first.drift() == () and type(first.locate(late.id)) is read.Unknown
    second = open_world_view(world, published)
    assert type(second.locate(late.id)) is read.Unknown  # its live carrier has indexed the new id
    (drift,) = second.drift()
    assert drift.corpus_id == a and drift.unmapped == (late.uid,)
    assert drift.published_state == dict(published.coverage)[a] and drift.captured_state != drift.published_state
    assert second.get(before.id).title == changed.title
    assert late.id not in {n.id for n in second.iter_stored()}
    local = ReadView.opened_at(roots[a])
    assert local.holds(late.id) and local.get(before.id).title == changed.title
    writer = open_corpus(roots[a], authority=FULL, profile=BASE)
    with writer._state.lock, pytest.raises(BuildContended):
        open_world_view(world, published)


def test_a_returned_object_is_detached_durably(chain):
    world, _roots, published, _a, _b = chain
    view = open_world_view(world, published)
    before = view.get("dataset:d2")
    returned = view.get(before.id)
    assert returned is not before
    returned.title = "mutated"
    returned.facets["dataset"]["resources"].append({"digest": "x"})
    assert view.get(before.id) == before
    yielded = next(n for n in view.iter_stored() if n.id == before.id)
    yielded.deprecated_ids.append("dataset:fake")
    assert "dataset:fake" not in next(n for n in view.iter_stored() if n.id == before.id).deprecated_ids
    edges = view.inbound("dataset:d1")
    edge_before = edges[0].relation.model_copy(deep=True)
    edges[0].relation.predicate = "mutated"
    assert view.inbound("dataset:d1")[0].relation == edge_before


def evaluation_world(durable_world, beta_refs=("dataset:d-a",), *, extra=(), role=None):
    profile = profile_with()
    _cid, _root, writer = durable_world.corpus(profile)
    nodes = list(seed(writer).iter_stored())
    nodes.extend(extra)
    if role is not None:
        run = next(n for n in nodes if n.id == "run:run-b")
        run.relations.append(Relation(source=run.id, predicate=role, target="dataset:d-t"))
        stored.stamp_semantic_identity(run)
    return (
        *durable_world(
            tuple(n for n in nodes if n.id not in beta_refs),
            tuple(n for n in nodes if n.id in beta_refs),
            profile=profile,
        ),
        profile,
    )


def world_kwargs(view, profile, a, b):
    kwargs = kwargs_for(view, profile)
    context = replace(
        kwargs["context"],
        retractions=replace(kwargs["context"].retractions, coverage=tuple(sorted((a, b)))),
        node_corpus={},
        pins={a: pins_for(profile), b: pins_for(profile)},
    )
    return {**kwargs, "context": context}


def gathered(view, kwargs):
    return gather(view, "proposition:p", **{k: v for k, v in kwargs.items() if k != "availability"})


def test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably(durable_world):
    world, roots, published, a, b, profile = evaluation_world(durable_world)
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile, a, b)
    inputs = gathered(view, kwargs)
    assert inputs.absent == () and len(inputs.observed_facets) == 1
    assert inputs.node_corpus[inputs.observed_facets[0].address] == (b,)
    assert inputs.node_corpus["run:run-a"] == (a,)
    assert all(inputs.node_corpus[value.identity()] == (a,) for value in inputs.assessments)
    assert ("biology", pins_for(profile).domains["biology"]) in inputs.consulted
    assert set(inputs.read_trace) <= inputs.declared_refs()
    complete_belief = evaluate_over(view, "proposition:p", **kwargs)
    assert isinstance(complete_belief, Belief)
    supplied = replace(kwargs["context"], node_corpus={"anything": (a,)})
    with pytest.raises(MalformedRecord, match="node_corpus.*derived"):
        evaluate_over(view, "proposition:p", **{**kwargs, "context": supplied})
    with pytest.raises(MalformedRecord, match="node_corpus.*derived"):
        gathered(view, {**kwargs, "context": supplied})
    absent(roots, b)
    view = open_world_view(world, published)
    result = evaluate_over(view, "proposition:p", **world_kwargs(view, profile, a, b))
    assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent" and b in result.detail
    local = ReadView.opened_at(roots[a])
    local_context = replace(
        kwargs["context"],
        snapshot=lineage_snapshot(local, ["dataset:d-b"]),
        node_corpus={value.identity(): (a,) for value in inputs.assessments},
    )
    local_kwargs = {**kwargs, "context": local_context}
    local_inputs = gathered(local, local_kwargs)
    assert local_inputs.absent == () and local_inputs.observed_facets == ()
    local_result = evaluate_over(local, "proposition:p", **local_kwargs)
    # Run-b's local evidence still admits a belief; the foreign evidence is gone.
    assert isinstance(local_result, Belief)
    assert local_result.belief_input_digest != complete_belief.belief_input_digest


@pytest.mark.parametrize("role", [stored.READS, stored.TRANSFORMS, stored.OBSERVES])
def test_absent_runs_and_all_input_roles_are_named_durably(durable_world, role):
    extra = stored.dataset_node("d-t", title="d-t", resources=pinned())
    world, roots, published, a, b, profile = evaluation_world(
        durable_world, ("run:run-a", extra.id), extra=(extra,), role=role
    )
    absent(roots, b)
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile, a, b)
    inputs = gathered(view, kwargs)
    assert ("run:run-a", b) in inputs.absent and (extra.id, b) in inputs.absent
    result = evaluate_over(view, "proposition:p", **kwargs)
    assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent"


@pytest.mark.parametrize("target", ["proposition:p", "dataset:extra"])
def test_proposition_and_snapshot_absence_are_named_durably(durable_world, target):
    extra = stored.dataset_node("extra", title="extra", resources=pinned())
    world, roots, published, a, b, profile = evaluation_world(durable_world, (target,), extra=(extra,))
    absent(roots, b)
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile, a, b)
    if target == extra.id:
        kwargs["context"] = replace(
            kwargs["context"], snapshot=lineage_snapshot(view, ["dataset:d-a", "dataset:d-b", target])
        )
    assert gathered(view, kwargs).absent == ((target, b),)
    result = evaluate_over(view, "proposition:p", **kwargs)
    assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent" and b in result.detail


def test_identical_assessments_consult_both_carriers_durably(durable_world):
    twin = stored.assessment_node(
        "a-twin",
        title="twin",
        spec="spec-a",
        run="run:run-a",
        proposition="proposition:p",
        outcome="supported",
        interpretation_rule="rule-1",
    )
    world, _roots, published, a, b, profile = evaluation_world(durable_world, (twin.id,), extra=(twin,))
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile, a, b)
    inputs = gathered(view, kwargs)
    identity = stored.assessment_value(twin).identity()
    assert inputs.node_corpus[identity] == tuple(sorted((a, b)))
    with pytest.raises(TypeError):
        cast(Any, inputs.node_corpus)[identity] = (a,)
    assert isinstance(evaluate_over(view, "proposition:p", **kwargs), Belief)
    disagreeing = replace(pins_for(profile), science_contract="science:" + "0" * 64)
    context = replace(kwargs["context"], pins={a: pins_for(profile), b: disagreeing})
    result = evaluate_over(view, "proposition:p", **{**kwargs, "context": context})
    assert isinstance(result, Refused) and "consulted-contracts-disagree" in result.reason


@pytest.mark.parametrize("change", ["content", "addition", "removal"])
def test_a_facet_read_is_held_to_the_capture_durably(durable_world, change):
    world, roots, published, a, b, profile = evaluation_world(durable_world)
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile, a, b)
    path = roots[b] / "dataset" / "d-a.md"
    path.write_text(path.read_text() + "\n")
    gathered(view, kwargs)
    node = ReadView.opened_at(roots[b]).get("dataset:d-a")
    if change == "content":
        node.facets["biology/gene-axis"]["axis"] = "columns"
    elif change == "removal":
        del node.facets["biology/gene-axis"]
    else:
        node.facets["testing/annotation"] = {"note": "added"}
    raw_write(roots[b], node)
    assert view.get(node.id).facets["biology/gene-axis"]["axis"] == "rows"
    with pytest.raises(CaptureDrift):
        gathered(view, kwargs)


def test_check_verification_reports_a_cross_corpus_forgery_durably(durable_world):
    _cid, _root, writer = durable_world.corpus()
    original = publish_corpus(writer, publish=True)
    assert original.node is not None
    forged = self_consistent_forgery(writer, original.node, mutate=lambda facet: facet.__setitem__("verdict", "failed"))
    nodes = tuple(n for n in writer.read_view.iter_stored() if n.id != forged.id)
    world, roots, published, a, b = durable_world(
        tuple(n for n in nodes if n.kind != "run"), tuple(n for n in nodes if n.kind == "run"), raw=(forged,)
    )
    view = open_world_view(world, published)
    assert view.corpus_of(original.node.id) == a
    assert all(view.corpus_of(n.id) == b for n in nodes if n.kind == "run")
    genuine = check_verification(view, view.get(original.node.id), evidence=original.evidence)
    assert genuine.checked and genuine.contradiction is None
    outcome = check_verification(view, view.get(forged.id), evidence=original.evidence)
    assert outcome.checked and outcome.contradiction is not None
    assert outcome.contradiction.code == "verification-derivation-contradicted"
    malformed = view.get(original.node.id)
    malformed.facets["verification"]["report"] = {"forged": True}
    with pytest.raises(MalformedRecord):
        check_verification(view, malformed, evidence=original.evidence)
    local = ReadView.opened_at(roots[a])
    unchecked = check_verification(local, local.get(original.node.id), evidence=original.evidence)
    assert (
        not unchecked.checked and unchecked.contradiction is None and unchecked.reason.endswith("does not resolve here")
    )


def test_the_three_states_never_collapse_and_removal_is_not_unknown(chain):
    world, roots, published, a, b = chain
    present = read.resolve_address(world, published, "dataset:d1")
    assert type(present) is read.Resolved
    absent(roots, b)
    missing = read.resolve_address(world, published, "dataset:d1")
    unknown = read.resolve_address(world, published, "dataset:unknown")
    assert type(missing) is read.NotPresent and type(unknown) is read.Unknown
    assert len({type(present), type(missing), type(unknown)}) == 3
    assert present.stamp == missing.stamp == unknown.stamp
    assert type(read.resolve_address(world, published, "dataset:d2")) is read.Resolved
    world.depart(b)
    assert type(read.resolve_address(world, published, "dataset:d1")) is read.NotPresent
    assert not ReadView.opened_at(roots[a]).holds("dataset:d1")


def test_one_uid_under_two_corpora_refuses_at_open_durably(chain):
    world, roots, published, a, b = chain
    assert open_world_view(world, published).absent() == ()
    twin = ReadView.opened_at(roots[a]).get("dataset:d0").model_copy(deep=True, update={"id": "dataset:twin"})
    raw_write(roots[b], twin)
    with pytest.raises(ResolutionRefused, match="uid uniqueness"):
        open_world_view(world, published)


def test_the_five_outcomes_are_produced_and_kept_apart_durably(chain):
    world, roots, published, _a, b = chain
    absent(roots, b)
    view = open_world_view(world, published)
    assert type(view.locate("dataset:d1")) is read.NotPresent
    corpus_id = view.corpus_of("dataset:d1")
    assert corpus_id is not None and corpus_id == b
    readable = build_snapshot(readable={EX: [GENE]})
    assert {
        readable.resolve(EX, GENE),
        readable.resolve(EX, "EX:other"),
        build_snapshot().resolve(EX, GENE),
        build_snapshot(unreadable=[EX]).resolve(EX, GENE),
        build_snapshot(not_present={EX: corpus_id}).resolve(EX, GENE),
    } == set(TermOutcome)
    assert (
        len(
            {
                build_snapshot(readable={EX: []}).identity,
                build_snapshot(unreadable=[EX]).identity,
                build_snapshot(not_present={EX: corpus_id}).identity,
            }
        )
        == 3
    )
    for kwargs in (
        {"readable": {EX: []}, "unreadable": [EX]},
        {"readable": {EX: []}, "not_present": {EX: corpus_id}},
        {"unreadable": [EX], "not_present": {EX: corpus_id}},
    ):
        with pytest.raises(ResolutionError):
            build_snapshot(**kwargs)


@pytest.mark.parametrize("fault", ["duplicate-carrier", "manifest", "mapped-uid", "foreign-epoch", "capture-moves"])
def test_open_refusals_never_become_absence_durably(chain, durable_world, monkeypatch, fault):
    from beliefs.world import registry

    world, roots, published, a, _b = chain
    assert open_world_view(world, published).absent() == ()
    expected: type[Exception] = ResolutionRefused
    if fault == "duplicate-carrier":
        _cid, duplicate, _writer = durable_world.corpus()
        # This is a corrupt carrier claim, deliberately outside the writer.
        (duplicate / "corpus.yaml").write_bytes((roots[a] / "corpus.yaml").read_bytes())
        world = open_world(replace(world.config, corpus_roots=(*roots.values(), duplicate)), authority=FULL)
    elif fault == "manifest":
        (roots[a] / "corpus.yaml").write_text("not: [a readable manifest")
    elif fault == "mapped-uid":
        node = ReadView.opened_at(roots[a]).get("dataset:d0")
        raw_write(roots[a], node.model_copy(deep=True, update={"uid": "f" * 32}))
    elif fault == "foreign-epoch":
        # Nested scratch and its metadata are owned by this fixture's corpus root.
        foreign = WorldConfig(roots[a] / "foreign-world", "f" * 32, tuple(roots.values()))
        init_world_root(foreign, authority=FULL)
        world = open_world(foreign, authority=FULL)
        expected = EpochUnknown
    else:
        state_identity = registry.corpus_state_identity
        changed = False

        def move_during_capture(path):
            nonlocal changed
            state = state_identity(path)
            if not changed:
                changed = True
                raw_write(path, stored.dataset_node("racing", title="racing", resources=pinned()))
            return state

        monkeypatch.setattr(registry, "corpus_state_identity", move_during_capture)
        expected = CaptureDrift
    with pytest.raises(expected):
        open_world_view(world, published)


def test_unheld_reads_keep_unknown_and_absent_apart_durably(chain):
    world, roots, published, _a, b = chain
    absent(roots, b)
    view = open_world_view(world, published)
    assert view.absent() == (b,)
    assert view.resolve("dataset:d1") is None and not view.holds("dataset:d1")
    for fetch in (view.get, view.corpus_view):
        with pytest.raises(RecordNotPresent) as caught:
            fetch("dataset:d1")
        assert (caught.value.ref, caught.value.corpus_id, caught.value.stamp) == ("dataset:d1", b, view.stamp)
        with pytest.raises(RefError):
            fetch("dataset:unknown")
    assert view.corpus_of("dataset:unknown") is None and view.inbound("dataset:unknown") == []
