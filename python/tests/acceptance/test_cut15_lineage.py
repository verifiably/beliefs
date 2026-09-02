from hashlib import sha256

import pytest
from durable_fixture import basis, pinned, route, slug
from fixtures_cut4 import reopen
from fixtures_cut15 import SNAKEFILE_CONSTANT_PRODUCTION, run_workflow
from test_operation_port import durable_port

from beliefs import stored
from beliefs.boundary import RunMinted
from beliefs.corpus import derived_from, lineage_snapshot
from beliefs.lineage import certify, divergence_state
from beliefs.production import mint_dataset
from beliefs.recipe import RecipeInput
from beliefs.runrecord import run_ref

INPUT_A = "dataset:in-a"
INPUT_B = "dataset:in-b"


def _held(tmp_path, name: str, text: str):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _produce(durable_root, tmp_path, *, address: str, name: str, text: str):
    held = _held(tmp_path / name, "data.txt", text)
    digest = "sha256:" + sha256(held.read_bytes()).hexdigest()
    return run_workflow(
        tmp_path / name,
        port=durable_port(durable_root),
        snakefile=SNAKEFILE_CONSTANT_PRODUCTION,
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        inputs=(RecipeInput(role="transforms", dataset=address, content=digest),),
        held_inputs={address: held},
    )


def two_producers(durable_root, durable_writer, tmp_path, *, second_input=INPUT_B):
    for address in (INPUT_A, INPUT_B):
        durable_writer.add(stored.dataset_node(slug(address), title=slug(address), resources=pinned()))
    first = _produce(durable_root, tmp_path, address=INPUT_A, name="first", text="alpha")
    second = _produce(durable_root, tmp_path, address=second_input, name="second", text="beta")
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    minted = mint_dataset(first.run, existing_bases={})
    again = mint_dataset(second.run, existing_bases={minted.address: minted.basis})
    durable_writer.add(
        stored.dataset_node(
            slug(minted.address),
            title="produced",
            resources=[{"name": name, "digest": digest} for name, digest in first.run.result.outputs],
            basis=basis(route(run_ref(first.run.address()), INPUT_A, [INPUT_A])),
        )
    )
    return first, second, minted, again, reopen(durable_root)


def test_two_runs_produce_one_address_by_different_routes(durable_root, durable_writer, tmp_path):
    first, second, minted, again, _view = two_producers(durable_root, durable_writer, tmp_path)
    assert first.run.recipe.identity() != second.run.recipe.identity()
    assert again.address == minted.address
    assert again.stamped is False


def test_the_composition_sees_both_producers_while_the_basis_names_the_first(
    durable_root, durable_writer, tmp_path
):
    first, second, minted, again, view = two_producers(durable_root, durable_writer, tmp_path)
    snapshot = lineage_snapshot(view, (minted.address,))
    assert {producer.stored_run for producer in snapshot.producers[minted.address]} == {
        run_ref(first.run.address()),
        run_ref(second.run.address()),
    }
    assert {route.stored_run for route in snapshot.bases[minted.address].routes} == {
        run_ref(first.run.address())
    }
    assert set(derived_from(view, minted.address).reached) == {INPUT_A, INPUT_B}
    assert again.basis.run == first.run.address()


def test_independence_walks_the_basis_and_not_the_composition(durable_root, durable_writer, tmp_path):
    _first, _second, minted, _again, view = two_producers(durable_root, durable_writer, tmp_path)
    snapshot = lineage_snapshot(view, (minted.address,))
    assert divergence_state(snapshot, minted.address) == "divergent"
    verdict = certify(snapshot, (minted.address,), (INPUT_B,))
    assert verdict.state == "not-certified"
    assert verdict.findings == ("lineage-divergent",)


def test_the_replay_case_is_not_divergence_and_still_certifies(durable_root, durable_writer, tmp_path):
    _first, _second, minted, _again, view = two_producers(
        durable_root, durable_writer, tmp_path, second_input=INPUT_A
    )
    snapshot = lineage_snapshot(view, (minted.address,))
    assert len(snapshot.producers[minted.address]) == 2
    assert divergence_state(snapshot, minted.address) == "undiverged"
    assert certify(snapshot, (minted.address,), (INPUT_B,)).state == "independent"


def test_the_view_is_stored_nowhere_and_no_ancestry_is_authored(durable_root, durable_writer, tmp_path):
    first, _second, minted, _again, view = two_producers(durable_root, durable_writer, tmp_path)
    assert derived_from(view, minted.address).reached
    assert not [node for node in view.iter_stored() if node.kind == "dataset" and "derived-from" in node.facets]
    with pytest.raises(TypeError):
        mint_dataset(
            first.run,
            existing_bases={},
            ancestry=("dataset:whatever",),  # pyright: ignore[reportCallIssue]
        )
