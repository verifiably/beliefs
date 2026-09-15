"""Cut 28: view evaluation and the W8/W8b conflicts over certified durable roots."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_coordination_node
from dataset_fixtures import dataset_ref
from durable_fixture import pinned
from fixtures_cut4 import path_for, raw_write
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.relations import Relation
from profiles import BASE
from test_evaluation import CLAIM_FACET, GENE, PHENO
from test_world_receipts import hold_shipped
from test_world_selection import PROJECT, REVISION, TOPIC, query, topic_nodes
from test_world_view import damage
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.
from beliefs import relocation, stored
from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CoordinationResolver, ReadView, corpus_check
from beliefs.errors import (
    AddressDisagreement,
    AddressMapConflict,
    DuplicateLocation,
    HistoryDisagreement,
    SelectionRefused,
    SemanticHashStale,
    SourceAddressDisagreement,
)
from beliefs.root import init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, epoch
from beliefs.world.selection import Unresolved, evaluate_query
from beliefs.world.view import open_world_view

MOVE_FIELDS = {"observer": "o", "instrument": "i", "opened_at": "2026-09-14T00:00:00Z", "closed_at": "2026-09-14T00:00:01Z"}
CONSOLIDATE_FIELDS = {**MOVE_FIELDS, "rationale": "keep holds the authored record"}
COORDINATION = coordination_profile(None)


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut28-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def topic_record(*clauses):
    return raw_coordination_node(
        "topic", PROJECT, REVISION, local=TOPIC,
        query={"version": "science.view-query.v1", "clauses": [{"all": clause} for clause in clauses]},
    )


@pytest.fixture()
def topic(durable_world, scratch):
    def make(*clauses, alpha_extra=(), beta_extra=(), alpha_raw=(), beta_raw=(), without=()):
        alpha_nodes, beta_nodes = topic_nodes()
        alpha_nodes = tuple(n for n in alpha_nodes if n.kind != "project" and n.id not in without)
        beta_nodes = tuple(n for n in beta_nodes if n.id not in without)
        project = next(n for n in topic_nodes()[0] if n.kind == "project")
        a, alpha, left = durable_world.corpus(COORDINATION)
        b, beta, right = durable_world.corpus(COORDINATION)
        for writer, nodes in ((left, (*alpha_nodes, *alpha_extra)), (right, (*beta_nodes, *beta_extra))):
            for node in nodes:
                writer.add(node)
        for node in (project, topic_record(*clauses), *alpha_raw):
            raw_write(alpha, node)
        for node in beta_raw:
            raw_write(beta, node)
        config = WorldConfig(scratch / f"topic-world-{a[:8]}", "e" * 32, (alpha, beta))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(alpha, provenance=Fresh())
        world.admit(beta, provenance=Fresh())
        published = epoch.build_epoch(world, coverage=frozenset((a, b)), bindings=hold_shipped(world))
        return world, {a: alpha, b: beta}, published, a, b
    return make


def resolved_query(roots, a):
    resolver = CoordinationResolver({roots[a]: COORDINATION})
    record = resolver.resolve(CoordinationAddress(PROJECT, TOPIC))
    assert isinstance(record, Node), record
    return stored_query(record)


def absent(roots, corpus_id):
    (roots[corpus_id] / "corpus.yaml").unlink()


def result(case):
    world, roots, published, a, b = case
    return evaluate_query(open_world_view(world, published), resolved_query(roots, a)), (world, roots, published, a, b)


def root_tree(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def durable_state(writer):
    return root_tree(writer.root), root_tree(metadata_root_for(writer.root))


def conflict_world(durable_world, scratch, alpha_nodes, beta_nodes, *, twin):
    a, alpha, left = durable_world.corpus()
    b, beta, right = durable_world.corpus()
    for node in alpha_nodes:
        left.add(node)
    for node in beta_nodes:
        right.add(node)
    config = WorldConfig(scratch / f"world-{a[:8]}", "e" * 32, (alpha, beta))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(alpha, provenance=Fresh())
    world.admit(beta, provenance=Fresh())
    raw_write(beta, twin)
    return world, {a: alpha, b: beta}, (a, b), (
        open_corpus(alpha, authority=FULL, profile=BASE),
        open_corpus(beta, authority=FULL, profile=BASE),
    ), hold_shipped(world)


def publish(world, coverage, bindings):
    return epoch.build_epoch(world, coverage=frozenset(coverage), bindings=bindings)


def test_w7_addresses_selects_the_other_corpus_record_and_contributes_its_corpus_durably(topic):
    first, case = result(topic([{"addresses": [dataset_ref("d-b")]}]))
    world, roots, published, _a, b = case
    second = evaluate_query(open_world_view(world, published), resolved_query(roots, _a))
    assert first.selected == (dataset_ref("d-b"),) and first.contributing == (b,) and first.complete
    assert first.identity() == second.identity()
    damaged_world, damaged_roots, damaged_published, damaged_a, damaged_b = topic([{"addresses": [dataset_ref("d-b")]}])
    damage(damaged_roots[damaged_b], "parse-error")
    with pytest.raises(SelectionRefused, match="corpus-damaged"):
        evaluate_query(
            open_world_view(damaged_world, damaged_published, on_damage="report"),
            resolved_query(damaged_roots, damaged_a),
        )


def test_w7_kinds_selects_and_contributes_both_corpora_durably(topic):
    selection, (_w, _r, _p, a, b) = result(topic([{"kinds": ["dataset"]}]))
    assert selection.selected == (dataset_ref("d-a"), dataset_ref("d-b"))
    assert selection.contributing == tuple(sorted((a, b)))


def test_w7_closure_out_selects_the_other_corpus_dataset_and_not_the_run_durably(topic):
    selection, (*_, b) = result(topic([{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]))
    assert selection.selected == (dataset_ref("d-b"),) and selection.contributing == (b,)


def test_w7_references_term_selects_the_proposition_and_never_a_dataset_durably(topic):
    selection, (*_, b) = result(topic([{"references-term": GENE}]))
    assert selection.selected == ("proposition:p-b",) and selection.contributing == (b,)


def test_w7_two_clauses_select_and_contribute_both_durably(topic):
    selection, (_w, _r, _p, a, b) = result(topic([{"addresses": [dataset_ref("d-a")]}], [{"references-term": GENE}]))
    assert selection.selected == (dataset_ref("d-a"), "proposition:p-b")
    assert selection.contributing == tuple(sorted((a, b)))


def test_w7_the_absent_corpus_refuses_reports_or_names_itself_by_form_durably(topic):
    for clause, reason in (([{"addresses": [dataset_ref("d-b")]}], "refuse"), ([{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}], "closure"), ([{"kinds": ["dataset"]}], "kinds")):
        complete, (world, roots, published, a, b) = result(topic(clause))
        absent(roots, b)
        if reason == "refuse":
            with pytest.raises(SelectionRefused) as caught:
                evaluate_query(open_world_view(world, published), resolved_query(roots, a))
            assert (caught.value.reason, caught.value.refs, caught.value.corpus_ids) == ("address-not-present", (dataset_ref("d-b"),), (b,))
        else:
            partial = evaluate_query(open_world_view(world, published), resolved_query(roots, a))
            assert not partial.complete and partial.identity() != complete.identity()
            if reason == "closure":
                assert partial.unresolved == (Unresolved("run:r-a", "produces", dataset_ref("d-b"), "not-present", b),)
            else:
                assert partial.absent == (b,)


def test_w7_a_closure_anchored_in_the_absent_corpus_refuses_durably(topic):
    selection, (world, roots, published, a, b) = result(topic([{"closure": {"anchor": dataset_ref("d-b"), "predicates": ["produces"], "direction": "in"}}]))
    assert selection.selected == ("run:r-a",)
    absent(roots, b)
    with pytest.raises(SelectionRefused) as caught:
        evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert caught.value.reason == "address-not-present" and caught.value.refs == (dataset_ref("d-b"),)


def test_w7_a_drifted_view_refuses_and_the_earlier_capture_evaluates_durably(topic):
    world, roots, published, a, b = topic([{"kinds": ["dataset"]}])
    before = open_world_view(world, published)
    node = before.get(dataset_ref("d-b")).model_copy(deep=True)
    node.relations.append(Relation(source=node.id, predicate="cites", target=dataset_ref("d-a")))
    path_for(roots[b], node.id).write_text(node_to_markdown(node))
    after = open_world_view(world, published)
    assert [r.corpus_id for r in after.drift() if r.captured_state != r.published_state] == [b]
    with pytest.raises(SelectionRefused, match="corpus-drifted"):
        evaluate_query(after, resolved_query(roots, a))
    assert evaluate_query(before, resolved_query(roots, a)).complete
    rebuilt = publish(world, (a, b), hold_shipped(world))
    clean = evaluate_query(open_world_view(world, rebuilt), resolved_query(roots, a))
    assert clean.complete and clean.identity() != evaluate_query(before, resolved_query(roots, a)).identity()


def test_w7_a_damaged_view_refuses_durably(topic):
    world, roots, published, a, b = topic([{"kinds": ["dataset"]}])
    damage(roots[b], "parse-error")
    with pytest.raises(SelectionRefused) as caught:
        evaluate_query(open_world_view(world, published, on_damage="report"), resolved_query(roots, a))
    assert caught.value.reason == "corpus-damaged" and caught.value.refs == (b,)


def test_w7_reordered_authoring_and_registration_give_one_projection_durably(topic):
    first, (world, roots, published, a, b) = result(topic([{"kinds": ["dataset"]}, {"addresses": [dataset_ref("d-b")]}], [{"kinds": ["run"]}]))
    reordered = query([{"kinds": ["run"]}], [{"addresses": [dataset_ref("d-b")]}, {"kinds": ["dataset"]}])
    assert first.projection() == evaluate_query(open_world_view(world, published), reordered).projection()
    projections = []
    for name, order in (("forward", (a, b)), ("backward", (b, a))):
        paths = tuple(roots[corpus_id] for corpus_id in order)
        config = WorldConfig(world.config.world_root.parent / name, "e" * 32, paths)
        init_world_root(config, authority=FULL)
        ordered = open_world(config, authority=FULL)
        for path in paths:
            ordered.admit(path, provenance=Fresh())
        capture = publish(ordered, (a, b), hold_shipped(ordered))
        projection = evaluate_query(open_world_view(ordered, capture), query([{"kinds": ["dataset"]}])).projection()
        assert projection["epoch"] == capture.packaging_identity
        projections.append(projection)
    assert [{key: value for key, value in projection.items() if key != "epoch"} for projection in projections] == [
        {key: value for key, value in projections[0].items() if key != "epoch"}
    ] * 2
    reversed_config = WorldConfig(world.config.world_root, world.config.world_id, tuple(reversed(world.config.corpus_roots)))
    reversed_world = open_world(reversed_config, authority=FULL)
    same_query = query([{"kinds": ["dataset"]}])
    assert evaluate_query(open_world_view(world, published), same_query).projection() == evaluate_query(
        open_world_view(reversed_world, published), same_query
    ).projection()


def test_w7_a_retired_anchor_over_a_cycle_selects_what_the_live_anchor_selects_durably(topic):
    one = stored.dataset_node(title="a", resources=pinned()); two = stored.dataset_node(title="b", resources=pinned())
    one.relations.append(Relation(source=one.id, predicate="cites", target=two.id)); two.relations.append(Relation(source=two.id, predicate="cites", target=one.id)); one.deprecated_ids = ["dataset:cyc-a-old"]
    world, _roots, published, _a, _b = topic(alpha_extra=(one, two))
    view = open_world_view(world, published)
    clause = lambda anchor: query([{"closure": {"anchor": anchor, "predicates": ["cites"], "direction": "out"}}])
    assert evaluate_query(view, clause(one.id)).selected == evaluate_query(view, clause("dataset:cyc-a-old")).selected == (two.id,)


def test_w7_dangling_and_absent_inbound_steps_are_reported_not_dropped_durably(topic):
    dangling = stored.dataset_node(title="d-x", resources=pinned()); dangling.relations.append(Relation(source=dangling.id, predicate="cites", target="dataset:never"))
    selection, _ = result(topic([{"closure": {"anchor": dangling.id, "predicates": ["cites"], "direction": "out"}}], alpha_extra=(dangling,)))
    assert selection.unresolved == (Unresolved(dangling.id, "cites", "dataset:never", "unknown", None),)
    selection, (world, roots, published, a, b) = result(topic([{"closure": {"anchor": dataset_ref("d-a"), "predicates": ["produces"], "direction": "in"}}]))
    assert selection.selected == ("run:r-b",); absent(roots, b)
    partial = evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert partial.unresolved == (Unresolved(dataset_ref("d-a"), "produces", "run:r-b", "not-present", b),)


def test_w7_a_retired_and_a_live_address_select_once_durably(topic):
    node = stored.dataset_node(title="new", resources=pinned()); node.deprecated_ids = ["dataset:d-old"]
    selection, _ = result(topic([{"addresses": ["dataset:d-old", node.id]}], alpha_extra=(node,)))
    assert selection.selected == (node.id,)


def test_w7_terms_in_arguments_and_restrictions_select_and_a_malformed_facet_refuses_durably(topic):
    qualified = stored.proposition_node("p-q", title="q", claim={**CLAIM_FACET, "qualifiers": {"tissue": {"quantifier": "some", "restriction": "EX:liver"}}})
    selection, _ = result(topic([{"references-term": "EX:liver"}], beta_extra=(qualified,)))
    assert selection.selected == ("proposition:p-q",)
    selection, _ = result(topic([{"references-term": GENE.upper()}]))
    assert selection.selected == ()
    selection, _ = result(topic([{"references-term": GENE.lower()}]))
    assert selection.selected == ()
    broken = stored.proposition_node("p-x", title="x", claim={**CLAIM_FACET, "args": "bad"})
    world, roots, published, a, _b = topic([{"references-term": GENE}], beta_extra=(broken,))
    with pytest.raises(SelectionRefused) as caught:
        evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert caught.value.reason == "record-malformed" and caught.value.refs == ("proposition:p-x",)


def test_w7_a_stale_edit_that_removed_the_term_refuses_durably(topic):
    stale = stored.proposition_node("p-s", title="s", claim=CLAIM_FACET); stale.facets["proposition"]["args"] = ["EX:other", PHENO]
    world, roots, published, a, _b = topic([{"references-term": GENE}], beta_raw=(stale,), without=("proposition:p-b",))
    with pytest.raises(SemanticHashStale):
        evaluate_query(open_world_view(world, published), resolved_query(roots, a))


def test_w7_a_stale_selected_record_refuses_durably(topic):
    stale = stored.dataset_node(title="s", resources=pinned()); stale.facets["dataset"]["resources"] = [{"digest": "f" * 64}]
    world, roots, published, a, _b = topic([{"kinds": ["dataset"]}], alpha_raw=(stale,))
    with pytest.raises(SemanticHashStale):
        evaluate_query(open_world_view(world, published), resolved_query(roots, a))


def test_w7_projection_members_are_asserted_directly_durably(topic):
    complete, (world, roots, published, a, b) = result(topic())
    absent(roots, b); partial = evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert partial.projection()["absent"] == [b] and partial.identity() != complete.identity()
    _selection, (world, roots, published, a, b) = result(topic([{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]))
    absent(roots, b); partial = evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert partial.projection()["unresolved"] == [{"source": "run:r-a", "predicate": "produces", "target": dataset_ref("d-b"), "state": "not-present", "corpus_id": [b]}]


def test_w7_empty_clauses_and_a_read_view_durably(topic):
    selection, (_w, roots, _p, a, _b) = result(topic())
    assert selection.selected == () and selection.complete
    with pytest.raises(TypeError, match="WorldReadView"):
        evaluate_query(ReadView.opened_at(roots[a]), query())  # type: ignore[arg-type]


def test_w7_an_unknown_address_refuses_naming_every_unknown_one_durably(topic):
    world, roots, published, a, b = topic([{"addresses": ["dataset:never", dataset_ref("d-b")]}], [{"addresses": ["run:never"]}])
    absent(roots, b)
    with pytest.raises(SelectionRefused) as caught:
        evaluate_query(open_world_view(world, published), resolved_query(roots, a))
    assert caught.value.reason == "address-unknown" and caught.value.refs == ("dataset:never", "run:never") and caught.value.corpus_ids == ()


def source_pair():
    record = stored.source_node(title="kept", identifiers={"doi": "10.1234/abc"})
    return record, record.model_copy(deep=True, update={"uid": "e" * 32})


def test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably(durable_world, scratch):
    original, twin = source_pair(); world, roots, coverage, _writers, bindings = conflict_world(durable_world, scratch, (original,), (), twin=twin)
    before = root_tree(world.config.world_root)
    with pytest.raises(AddressMapConflict) as caught: publish(world, coverage, bindings)
    assert caught.value.finding.detail == f"corpus/uid claims={tuple(sorted(zip(coverage, (original.uid, twin.uid))))!r}"
    assert root_tree(world.config.world_root) == before
    for reverse in (False, True):
        paths = tuple(roots[c] for c in (coverage[::-1] if reverse else coverage)); config = WorldConfig(scratch / f"order-{reverse}", "f" * 32, paths); init_world_root(config, authority=FULL); ordered = open_world(config, authority=FULL)
        for path in paths: ordered.admit(path, provenance=Fresh())
        with pytest.raises(AddressMapConflict) as second: publish(ordered, coverage, hold_shipped(ordered))
        assert (second.value.finding.code, second.value.finding.ref, second.value.finding.detail) == (caught.value.finding.code, caught.value.finding.ref, caught.value.finding.detail)
    for keep_index in (0, 1):
        original, twin = source_pair()
        _a, _alpha, left = durable_world.corpus(); _b, _beta, right = durable_world.corpus()
        left.add(original); right.add(twin); pair = (left, right); keep, other = pair[keep_index], pair[1-keep_index]
        survivor, _, _ = relocation.consolidate((keep, original.id), (other, original.id), **CONSOLIDATE_FIELDS)
        config = WorldConfig(scratch / f"fixed-{keep.corpus_id[:8]}", "a" * 32, (pair[0].root, pair[1].root)); init_world_root(config, authority=FULL); fixed = open_world(config, authority=FULL)
        for writer in pair: fixed.admit(writer.root, provenance=Fresh())
        view = open_world_view(fixed, publish(fixed, tuple(w.corpus_id for w in pair), hold_shipped(fixed)))
        assert view.get(original.id).uid == survivor.uid and [n.id for n in view.iter_stored()].count(original.id) == 1
    original, twin = source_pair()
    _a, _alpha, left = durable_world.corpus(); _b, _beta, right = durable_world.corpus()
    left.add(original); right.add(twin); pair = (left, right)
    state = [durable_state(w) for w in pair]
    with pytest.raises(DuplicateLocation): relocation.move(pair[0], pair[1], original.id, **MOVE_FIELDS)
    assert [durable_state(w) for w in pair] == state


def test_w8_address_conflict_refuses_the_build_and_consolidate_and_the_write_boundary_durably(durable_world, scratch):
    left = stored.source_node(title="p", identifiers={"doi": "10.1234/abc"}); right = stored.source_node(title="p", identifiers={"doi": "10.1234/abc", "isbn": "9780306406157"})
    world, _roots, coverage, writers, bindings = conflict_world(durable_world, scratch, (left,), (), twin=right)
    with pytest.raises(AddressMapConflict) as caught: publish(world, coverage, bindings)
    assert (caught.value.finding.code, caught.value.finding.ref) == ("duplicate-location", left.id)
    for keep_index in (0, 1):
        left = stored.source_node(title="p", identifiers={"doi": "10.1234/abc"}); right = stored.source_node(title="p", identifiers={"doi": "10.1234/abc", "isbn": "9780306406157"})
        _a, _alpha, first = durable_world.corpus(); _b, _beta, second = durable_world.corpus()
        first.add(left); second.add(right); pair = (first, second)
        keep, other = pair[keep_index], pair[1 - keep_index]
        state = [durable_state(writer) for writer in pair]
        with pytest.raises(HistoryDisagreement): relocation.consolidate((keep, left.id), (other, right.id), **CONSOLIDATE_FIELDS)
        assert [durable_state(writer) for writer in pair] == state
    forged = left.model_copy(update={"id": "source:forged"})
    with pytest.raises(SourceAddressDisagreement): writers[0].add(forged)


def test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably(durable_world, scratch):
    one = stored.dataset_node(title="one", resources=pinned()); two = stored.dataset_node(title="two", resources=pinned()).model_copy(update={"uid": one.uid})
    world, _roots, coverage, _writers, bindings = conflict_world(durable_world, scratch, (one,), (), twin=two)
    with pytest.raises(AddressMapConflict) as caught: publish(world, coverage, bindings)
    assert (caught.value.finding.code, caught.value.finding.ref) == ("uid-corruption", one.uid)
    assert "no repair is offered" in caught.value.finding.message and "consolidate" not in caught.value.finding.message
    _a, _alpha, left = durable_world.corpus(); _b, _beta, right = durable_world.corpus()
    left.add(one); right.add(two)
    with pytest.raises(AddressDisagreement): relocation.consolidate((left, one.id), (right, two.id), **CONSOLIDATE_FIELDS)


@pytest.mark.parametrize("same_uid", [True, False])
def test_w8b_duplicate_location_is_the_same_finding_with_shared_or_distinct_uids_durably(durable_world, scratch, same_uid):
    one = stored.dataset_node(title="one", resources=pinned()); two = one.model_copy(deep=True, update={"uid": one.uid if same_uid else "d" * 32})
    world, _roots, coverage, _writers, bindings = conflict_world(durable_world, scratch, (one,), (), twin=two)
    with pytest.raises(AddressMapConflict) as caught: publish(world, coverage, bindings)
    assert (caught.value.finding.code, caught.value.finding.ref) == ("duplicate-location", one.id)


def test_w8b_corruption_outranks_duplication_and_a_corpus_alone_reports_neither_durably(durable_world, scratch):
    one = stored.dataset_node(title="one", resources=pinned()); twin = one.model_copy(deep=True); third = one.model_copy(deep=True, update={"id": "dataset:third"})
    a, alpha, left = durable_world.corpus(); b, beta, right = durable_world.corpus(); c, gamma, last = durable_world.corpus()
    left.add(one); right.add(twin); last.add(third)
    coverage = (a, b, c); roots = {a: alpha, b: beta, c: gamma}; writers = (left, right, last)
    config = WorldConfig(scratch / "precedence", "b" * 32, (alpha, beta, gamma)); init_world_root(config, authority=FULL); world = open_world(config, authority=FULL)
    for writer in writers: world.admit(writer.root, provenance=Fresh())
    bindings = hold_shipped(world)
    with pytest.raises(AddressMapConflict) as caught: publish(world, coverage, bindings)
    assert caught.value.finding.code == "uid-corruption"
    for corpus_id, writer in zip(coverage, writers):
        findings = corpus_check(ReadView.opened_at(roots[corpus_id]), BASE)
        assert not [f for f in findings if f.code in ("uid-corruption", "duplicate-location")]
