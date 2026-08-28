"""R23's in-cell arms only. Deferred: the `derived_from` view, the
independence-multiplier and omission arms, every deletion, divergence,
coverage, receipt, snapshot, merge, and conflict arm, negatives (e)–(g), and
the raw-written-basis audit — the store, the world index, and the audit
(cut 3 §4.2)."""

import dataclasses
import inspect

import pytest
from fixtures_cut3 import D_IN, SNAKEFILE_TWO_NAMES, closure, recipe
from fixtures_cut3 import memory_production as run_production

from science.boundary import RunMinted
from science.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from science.errors import MalformedClosure
from science.production import ProducesEdge, StampedBasis, mint_dataset
from science.recipe import RecipeInput
from science.spec import ExclusionCertification


@pytest.fixture(scope="module")
def produced(tmp_path_factory):
    outcome = run_production(tmp_path_factory.mktemp("prod"))
    assert isinstance(outcome, RunMinted)
    return outcome


def test_r23_the_address_is_the_basis_projection_over_the_manifest(produced):
    declaration = DatasetDeclaration(
        resources=tuple(ResourceDeclaration(name=name, digest=digest) for name, digest in produced.run.result.outputs)
    )
    expected = dataset_address(declaration)
    minted = mint_dataset(produced.run, existing_bases={})
    assert minted.address == expected  # §6.2: dedupe, sort, fold — reused from cut 2, not rebuilt


def test_r23_the_produces_edge_is_emitted_with_the_run(produced):
    minted = mint_dataset(produced.run, existing_bases={})
    assert minted.edge == ProducesEdge(run=produced.run.address(), dataset=minted.address)
    # No path attaches an edge naming an output absent from the manifest:
    signature = inspect.signature(mint_dataset)
    assert list(signature.parameters) == ["run", "existing_bases"]
    assert signature.parameters["existing_bases"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["existing_bases"].default is inspect.Parameter.empty


def test_r23_no_edge_can_name_output_absent_from_the_manifest(produced):
    minted = mint_dataset(produced.run, existing_bases={})
    manifest_address = dataset_address(
        DatasetDeclaration(
            resources=tuple(
                ResourceDeclaration(name=name, digest=digest) for name, digest in produced.run.result.outputs
            )
        )
    )
    assert minted.edge.dataset == manifest_address


def test_r23_refuses_a_non_production_closure():
    with pytest.raises(MalformedClosure):
        mint_dataset(closure(), existing_bases={})


def test_r23_production_values_are_strict_and_immutable(produced):
    minted = mint_dataset(produced.run, existing_bases={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        minted.stamped = False  # type: ignore[misc]
    with pytest.raises(MalformedClosure):
        StampedBasis(run=produced.run.address(), transforms=[D_IN])  # type: ignore[arg-type]


def test_r23_no_produced_by_edge_is_reachable_in_either_direction(produced):
    import science.production as production_module

    assert not any("produced_by" in name for name in production_module.__all__)
    minted = mint_dataset(produced.run, existing_bases={})
    for value in (minted, minted.edge, minted.basis):
        assert "produced_by" not in {f.name for f in dataclasses.fields(value)}


def test_r23_negative_a_byte_identical_output_under_two_logical_names_yields_one_address(tmp_path):
    outcome = run_production(
        tmp_path,
        snakefile=SNAKEFILE_TWO_NAMES,
        targets=("outputs/a.txt", "outputs/b.txt"),
        declared_outputs=("outputs/a.txt", "outputs/b.txt"),
    )
    assert isinstance(outcome, RunMinted)
    minted = mint_dataset(outcome.run, existing_bases={})
    digests = {digest for _, digest in outcome.run.result.outputs}
    assert len(outcome.run.result.outputs) == 2 and len(digests) == 1
    single = dataset_address(
        DatasetDeclaration(resources=(ResourceDeclaration(name="only", digest=next(iter(digests))),))
    )
    assert minted.address == single  # the name never entered; the projection deduplicated


def test_r23_replay_cardinality_one_address_two_edges_nothing_mutated(tmp_path):
    first = run_production(tmp_path / "a")
    second = run_production(tmp_path / "b")
    assert isinstance(first, RunMinted) and isinstance(second, RunMinted)
    assert first.run.recipe.identity() == second.run.recipe.identity()
    first_minted = mint_dataset(first.run, existing_bases={})
    bases = {first_minted.address: first_minted.basis}
    second_minted = mint_dataset(second.run, existing_bases=bases)
    assert second_minted.address == first_minted.address  # one address
    assert second_minted.edge != first_minted.edge  # two produces edges from two runs
    assert second_minted.basis == first_minted.basis  # the prior lineage basis unchanged
    assert second_minted.stamped is False
    assert bases == {first_minted.address: first_minted.basis}  # no existing node mutated


def test_r23_the_certified_exclusion_is_inline_and_mints_a_recipe_not_a_run():
    certified = recipe(
        shape="dataset-production",
        spec_identity=None,
        inputs=(
            RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),
            RecipeInput(
                role="reads",
                dataset="dataset:y",
                content="sha256:" + "34" * 32,
                exclusion=ExclusionCertification(rationale="gene-name lookup", attribution="tester"),
            ),
        ),
    )
    uncertified = recipe(
        shape="dataset-production",
        spec_identity=None,
        inputs=(
            RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),
            RecipeInput(role="reads", dataset="dataset:y", content="sha256:" + "34" * 32),
        ),
    )
    assert certified.identity() != uncertified.identity()  # adding it mints a different recipe
    withdrawn = uncertified
    assert withdrawn.identity() != certified.identity()  # withdrawing it likewise
    # …and no run until executed: a Recipe is a description, not a run —
    # nothing here has an address() until a RunClosure exists.
    assert not hasattr(certified, "address")


def test_r23_negative_h_reclassifying_an_inputs_role_mints_a_different_recipe():
    as_transforms = recipe(
        shape="dataset-production",
        spec_identity=None,
        inputs=(RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),),
    )
    as_reads = recipe(
        shape="dataset-production",
        spec_identity=None,
        inputs=(
            RecipeInput(role="transforms", dataset="dataset:x", content=D_IN),
            RecipeInput(role="reads", dataset="dataset:y", content="sha256:" + "34" * 32),
        ),
    )
    reclassified = recipe(
        shape="dataset-production",
        spec_identity=None,
        inputs=(
            RecipeInput(role="reads", dataset="dataset:x", content=D_IN),
            RecipeInput(role="transforms", dataset="dataset:y", content="sha256:" + "34" * 32),
        ),
    )
    assert len({as_transforms.identity(), as_reads.identity(), reclassified.identity()}) == 3
