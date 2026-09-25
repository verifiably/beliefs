"""Cut 41: live view-query evaluation over certified durable roots (live-query design §6.2)."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_coordination_node
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut4 import raw_write
from test_evaluation import GENE
from test_world_receipts import hold_shipped
from test_world_selection import PROJECT, query, topic_nodes
from test_world_view import damage
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.
from beliefs import stored
from beliefs.corpus import ReadView, _operation_lock_for
from beliefs.errors import AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused, SelectionRefused
from beliefs.root import init_world_root, metadata_root_for, open_world
from beliefs.world import Fresh, WorldConfig, epoch, registry
from beliefs.world import live as live_module
from beliefs.world.live import evaluate_live_query
from beliefs.world.registry import load_manifest
from beliefs.world.selection import evaluate_query
from beliefs.world.view import open_world_view

COORDINATION = coordination_profile(None)
DATASETS = query([{"kinds": ["dataset"]}])


def datasets(*slugs):
    return tuple(stored.dataset_node(title=slug, resources=pinned(slug)) for slug in slugs)


def topic_records():
    """Slice 4's topic records without its coordination project: ALPHA d_a, r_a; BETA d_b, r_b, p_b."""
    alpha, beta = topic_nodes()
    return tuple(node for node in alpha if node.kind != "project"), beta


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut41-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def live_world(durable_world, scratch):
    """Two admitted durable corpora and a world that has never published.

    `records` replaces the topic records; `gamma` adds a third configured,
    admitted corpus; `admit_beta=False` leaves BETA configured but unadmitted;
    `also_configured` adds roots the world sees and never admits."""

    def make(*, records=None, alpha_raw=(), beta_raw=(), gamma=None, admit_beta=True, also_configured=()):
        alpha_nodes, beta_nodes = topic_records() if records is None else records
        a, alpha, left = durable_world.corpus(COORDINATION)
        b, beta, right = durable_world.corpus(COORDINATION)
        for writer, nodes in ((left, alpha_nodes), (right, beta_nodes)):
            for node in nodes:
                writer.add(node)
        for node in alpha_raw:
            raw_write(alpha, node)
        for node in beta_raw:
            raw_write(beta, node)
        roots = {a: alpha, b: beta}
        if gamma is not None:
            g, gamma_root, third = durable_world.corpus(COORDINATION)
            for node in gamma:
                third.add(node)
            roots[g] = gamma_root
        config = WorldConfig(scratch / f"live-world-{a[:8]}", "e" * 32, (*roots.values(), *also_configured))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        for corpus_id, root in roots.items():
            if corpus_id != b or admit_beta:
                world.admit(root, provenance=Fresh())
        return world, roots, a, b

    return make


def tree(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


# --- Z1: coverage is the world's live admitted set ------------------------------------------------


def test_z1_a_every_present_admitted_corpus_is_captured_and_stamped_durably(live_world):
    world, roots, a, b = live_world()
    live = evaluate_live_query(world, DATASETS)
    assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
    assert live.contributing == tuple(sorted((a, b)))
    assert live.stamp.coverage == tuple(sorted((c, registry.corpus_state_identity(r)) for c, r in roots.items()))
    assert live.absent == () and live.complete


def test_z1_b_a_terminal_corpus_is_never_covered_durably(live_world):
    world, roots, a, b = live_world(gamma=datasets("d-g"))
    (g,) = set(roots) - {a, b}
    world.retire(g)
    live = evaluate_live_query(world, DATASETS)
    assert dataset_ref("d-g") not in live.selected
    assert set(dict(live.stamp.coverage)) == {a, b}
    assert g not in live.contributing and g not in live.absent


def test_z1_c_an_absent_corpus_is_listed_and_its_addresses_are_unknown_durably(live_world):
    world, roots, a, b = live_world()
    (roots[b] / "corpus.yaml").unlink()
    live = evaluate_live_query(world, DATASETS)
    assert live.absent == (b,) and not live.complete
    assert live.selected == (dataset_ref("d-a"),) and set(dict(live.stamp.coverage)) == {a}
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, query([{"addresses": [dataset_ref("d-b")]}]))
    assert refused.value.reason == "address-unknown" and refused.value.refs == (dataset_ref("d-b"),)


def test_z1_d_coverage_is_the_registry_not_an_epoch_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")), admit_beta=False)
    never_published = evaluate_live_query(world, DATASETS)
    assert never_published.selected == (dataset_ref("d-a"),)
    epoch.build_epoch(world, coverage=frozenset({a}), bindings=hold_shipped(world))
    world.admit(roots[b], provenance=Fresh())
    live = evaluate_live_query(world, DATASETS)
    assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
    assert set(dict(live.stamp.coverage)) == {a, b}


# --- Z2: each corpus is captured inside its own hold -----------------------------------------------


def test_z2_a_a_state_moving_inside_the_hold_discards_the_evaluation_durably(live_world, monkeypatch):
    world, roots, a, b = live_world()
    first = min(a, b)
    original = registry.corpus_state_identity
    calls = {"n": 0}

    def moving(root):
        calls["n"] += 1
        if calls["n"] == 2:  # the first corpus's second read, inside its hold
            raw_write(roots[first], datasets("d-late")[0])
        return original(root)

    monkeypatch.setattr(registry, "corpus_state_identity", moving)
    with pytest.raises(CaptureDrift):
        evaluate_live_query(world, DATASETS)


def test_z2_b_state_reads_and_enumeration_run_inside_the_corpus_hold_durably(live_world, monkeypatch):
    world, roots, a, _b = live_world()
    carriers = {root.resolve() for root in roots.values()}
    seen: list[tuple[str, Path, object]] = []
    original_state = registry.corpus_state_identity
    original_open = ReadView.opened_at.__func__
    original_iter = ReadView.iter_stored

    def state(root):
        seen.append(("state", Path(root).resolve(), _operation_lock_for(root)._holder))
        return original_state(root)

    def opened(cls, root):
        seen.append(("open", Path(root).resolve(), _operation_lock_for(root)._holder))
        return original_open(cls, root)

    def enumerated(self):
        # `iter_stored` reads the store lazily, so the holder is read at each record
        # as the evaluation consumes it, not when the iterator is made: a
        # generator created inside the hold and drained after it must fail here.
        root = self._corpus.store.root
        for node in original_iter(self):
            seen.append(("enumerate", Path(root).resolve(), _operation_lock_for(root)._holder))
            yield node

    monkeypatch.setattr(registry, "corpus_state_identity", state)
    monkeypatch.setattr(ReadView, "opened_at", classmethod(opened))
    monkeypatch.setattr(ReadView, "iter_stored", enumerated)
    evaluate_live_query(world, DATASETS)
    monkeypatch.undo()

    calls = [call for call in seen if call[1] in carriers]
    # every carrier holds records, so each is seen stating, opening and enumerating
    assert {carrier: {kind for kind, path, _ in calls if path == carrier} for carrier in carriers} == {
        carrier: {"state", "open", "enumerate"} for carrier in carriers
    }
    assert all(holder == "capture" for _, _, holder in calls), calls
    with _operation_lock_for(roots[a]), pytest.raises(BuildContended):
        evaluate_live_query(world, DATASETS)


# --- Z3: the stamp names what was denoted ------------------------------------------------------------


def test_z3_a_the_stamp_names_the_states_the_selection_was_denoted_over_durably(live_world, monkeypatch):
    world, roots, a, b = live_world()
    first, second = sorted((a, b))
    (late,) = datasets("d-late")
    original = registry.corpus_state_identity
    in_hold: dict[str, str] = {}

    def recording(root):
        resolved = Path(root).resolve()
        if resolved == roots[second].resolve() and "written" not in in_hold:
            in_hold["written"] = "yes"  # the first corpus's hold is released; the evaluation has not returned
            raw_write(roots[first], late)
        value = original(root)
        if resolved == roots[first].resolve():
            in_hold.setdefault(first, value)
        return value

    monkeypatch.setattr(registry, "corpus_state_identity", recording)
    live = evaluate_live_query(world, DATASETS)
    monkeypatch.undo()
    assert late.id not in live.selected
    assert dict(live.stamp.coverage)[first] == in_hold[first]
    assert registry.corpus_state_identity(roots[first]) != in_hold[first]


# --- Z4: damage refuses and is never omitted -----------------------------------------------------------


def test_z4_a_a_malformed_corpus_refuses_and_is_never_omitted_durably(live_world):
    world, roots, _a, b = live_world()
    damage(roots[b], "parse-error")
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == (b,)


def test_z4_b_a_disagreeing_base_pin_refuses_durably(live_world):
    world, roots, _a, b = live_world()
    manifest = roots[b] / "corpus.yaml"
    science = load_manifest(roots[b]).profile.science_contract
    text = manifest.read_text(encoding="utf-8")
    assert f"science_contract: {science}" in text
    manifest.write_text(
        text.replace(f"science_contract: {science}", "science_contract: science:" + "0" * 64), encoding="utf-8"
    )
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == (b,)


# --- Z5: conflicts keep publish's classification -------------------------------------------------------


def test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably(live_world):
    world, roots, a, b = live_world()
    copy = ReadView.opened_at(roots[a]).get(dataset_ref("d-a"))  # same address, same uid
    raw_write(roots[b], copy)
    with pytest.raises(AddressMapConflict) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.finding.code == "duplicate-location" and refused.value.finding.ref == copy.id


def test_z5_b_uid_corruption_outranks_duplicate_location_durably(live_world):
    world, roots, a, b = live_world()
    read = ReadView.opened_at(roots[a])
    run = read.get("run:r-a")
    twin = run.model_copy(deep=True)
    twin.id = "run:r-a-twin"  # same uid, another canonical address
    raw_write(roots[b], twin)
    raw_write(roots[b], read.get(dataset_ref("d-a")))  # and a duplicate location beside it
    with pytest.raises(AddressMapConflict) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.finding.code == "uid-corruption" and refused.value.finding.ref == run.uid


def test_z5_c_a_uid_shared_with_a_record_outside_the_map_refuses_after_the_map_durably(live_world):
    world, roots, a, b = live_world()
    shared = ReadView.opened_at(roots[b]).get("run:r-b").uid
    raw_write(roots[a], raw_coordination_node("project", PROJECT, shared))
    with pytest.raises(ResolutionRefused, match="W8b"):
        evaluate_live_query(world, DATASETS)


# --- the module's other tests (spec §6.2) --------------------------------------------------------------


def test_live_after_a_write_selects_what_the_old_epoch_refuses_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")))
    published = epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
    (late,) = datasets("d-late")
    raw_write(roots[a], late)
    with pytest.raises(SelectionRefused) as refused:
        evaluate_query(open_world_view(world, published), DATASETS)
    assert refused.value.reason == "corpus-drifted"
    live = evaluate_live_query(world, DATASETS)
    assert late.id in live.selected
    assert dict(live.stamp.coverage)[a] == registry.corpus_state_identity(roots[a])


AGREEMENT_QUERIES = (
    # Slice 4's acceptance queries over its default topic records
    # (`test_world_selection_acceptance.py`), then two of this plan's own.
    query([{"kinds": ["dataset"]}]),
    query([{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]),
    query([{"references-term": GENE}]),
    query([{"references-term": GENE.upper()}]),
    query([{"references-term": GENE.lower()}]),
    query([{"addresses": [dataset_ref("d-a")]}], [{"references-term": GENE}]),
    query([{"addresses": [dataset_ref("d-b")]}]),
    query([{"closure": {"anchor": dataset_ref("d-b"), "predicates": ["produces"], "direction": "in"}}]),
    query([{"closure": {"anchor": dataset_ref("d-a"), "predicates": ["produces"], "direction": "in"}}]),
    query([{"kinds": ["dataset"]}, {"addresses": [dataset_ref("d-b")]}], [{"kinds": ["run"]}]),
    query([{"kinds": ["dataset", "run"]}]),
    query(
        [{"closure": {"anchor": dataset_ref("d-b"), "predicates": ["produces"], "direction": "both"}}],
        [{"kinds": ["proposition"]}],
    ),
)


def test_live_and_epoch_agree_over_identical_coverage_every_corpus_present_and_equal_states_durably(live_world):
    world, roots, a, b = live_world()
    published = epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
    live_set = {a, b}
    assert {corpus_id for corpus_id, _ in published.coverage} == live_set  # identical coverage
    assert all(root.joinpath("corpus.yaml").exists() for root in roots.values())  # every corpus present
    assert dict(published.coverage) == {c: registry.corpus_state_identity(r) for c, r in roots.items()}  # equal states
    view = open_world_view(world, published)
    for each in AGREEMENT_QUERIES:
        bound, live = evaluate_query(view, each), evaluate_live_query(world, each)
        assert (live.selected, live.contributing, live.absent, live.unresolved) == (
            bound.selected,
            bound.contributing,
            bound.absent,
            bound.unresolved,
        ), each.projection()
        live_projection, bound_projection = live.projection(), bound.projection()
        assert set(live_projection) - set(bound_projection) == {"capture"}
        assert set(bound_projection) - set(live_projection) == {"epoch"}
        assert {k: v for k, v in live_projection.items() if k not in ("version", "capture")} == {
            k: v for k, v in bound_projection.items() if k not in ("version", "epoch")
        }


def test_equal_states_alone_do_not_make_the_two_agree_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")), admit_beta=False)
    published = epoch.build_epoch(world, coverage=frozenset({a}), bindings=hold_shipped(world))
    world.admit(roots[b], provenance=Fresh())
    assert dict(published.coverage)[a] == registry.corpus_state_identity(roots[a])
    bound = evaluate_query(open_world_view(world, published), DATASETS)
    live = evaluate_live_query(world, DATASETS)
    assert dataset_ref("d-b") in live.selected and dataset_ref("d-b") not in bound.selected


def test_damage_names_every_damaged_corpus_durably(live_world):
    world, roots, a, b = live_world()
    damage(roots[a], "parse-error")
    damage(roots[b], "parse-error")
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == tuple(sorted((a, b)))


def test_coordination_records_are_never_selected_durably(live_world):
    project = raw_coordination_node("project", PROJECT, "4" * 32)
    world, roots, a, _b = live_world(alpha_raw=(project,))
    every = evaluate_live_query(world, query([{"kinds": sorted(stored.WORLD_KINDS)}]))
    assert project.id not in every.selected
    world_records = {node.id for records in topic_records() for node in records}
    assert set(every.selected) == world_records
    # the address map the evaluation derives holds no coordination address
    captured, states, damaged = live_module._capture(roots)
    assert not damaged and project.id in {node.id for node in captured[a]}
    assert project.id not in live_module._address_map(captured, states)


def test_two_carriers_of_one_corpus_refuse_durably(live_world, scratch):
    twin = scratch / "twin-carrier"
    twin.mkdir()
    world, roots, a, _b = live_world(also_configured=(twin,))
    shutil.copyfile(roots[a] / "corpus.yaml", twin / "corpus.yaml")
    with pytest.raises(ResolutionRefused, match="more than one configured carrier"):
        evaluate_live_query(world, DATASETS)


def test_an_evaluation_writes_nothing_durably(live_world):
    world, roots, _a, _b = live_world()
    watched = [world.config.world_root, *roots.values(), *(metadata_root_for(root) for root in roots.values())]
    before = {str(path): tree(path) for path in watched}
    states = {c: registry.corpus_state_identity(r) for c, r in roots.items()}
    evaluate_live_query(world, DATASETS)
    assert {str(path): tree(path) for path in watched} == before
    assert {c: registry.corpus_state_identity(r) for c, r in roots.items()} == states
