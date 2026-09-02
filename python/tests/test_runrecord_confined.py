"""K4: the wire codec accepts both receipt spellings and recomputes each run
under the domain its receipt shape names; K3: a mount plan identity that
disagrees with its mounts is refused on the wire too."""

from typing import Any, cast

import pytest
from confinement_fixtures import confined_closure
from fixtures_cut3 import closure
from nodes.core.frontmatter import node_from_markdown

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.recipe import job_key, mount_plan_identity, run_domain_for
from beliefs.runrecord import decode_projection, decode_run_record, projection_text, publication_plan
from beliefs.stored import RUN_CLOSURE_FACET


def _node_of(run):
    _, _, (create,) = publication_plan(run)
    return node_from_markdown(create.content.decode("utf-8"))


def test_k4_a_minimal_projection_carries_exactly_the_v1_receipt_keys():
    parsed = cast(Any, decode_projection(projection_text(closure())))
    receipt = parsed["occurrence"]["receipt"]
    assert set(receipt) == {"planning", "execution"}
    assert all(
        set(receipt[launch]) == {"scratch_mapping", "argv", "rendered_config", "capabilities"}
        for launch in ("planning", "execution")
    )


def test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2():
    run = confined_closure()
    parsed = cast(Any, decode_projection(projection_text(run)))
    receipt = parsed["occurrence"]["receipt"]
    assert all(
        set(receipt[launch]) >= {"instance", "rendered_environment", "mounts"}
        for launch in ("planning", "execution")
    )
    assert v1.digest(run_domain_for(recipe_v2=True, confined=True), parsed) == run.address()
    assert v1.digest(run_domain_for(recipe_v2=True, confined=False), parsed) != run.address()
    published = decode_run_record(_node_of(run))
    assert published is not None and published.address == run.address()


def test_k4_a_minimal_run_still_recomputes_under_run_v1():
    run = closure()
    published = decode_run_record(_node_of(run))
    assert published is not None and published.address == run.address() == v1.digest(
        run_domain_for(recipe_v2=True, confined=False),
        decode_projection(projection_text(run)),
    )


def test_k3_a_wire_mount_plan_identity_disagreeing_with_its_mounts_is_refused():
    run = confined_closure()
    text = cast(Any, v1.decode(projection_text(run)))
    text["recipe"]["workflow_definition_identity"] = run.recipe.workflow_definition.identity()
    del text["recipe"]["workflow_definition"]
    text["occurrence"].pop("planned")
    text["occurrence"].pop("target_keys")
    text["occurrence"]["receipt"] = text["occurrence"]["receipt"]["execution"]
    text["occurrence"]["receipt"]["instance"]["mount_plan_identity"] = "sha256:" + "00" * 32
    with pytest.raises(MalformedRecord, match="mount_plan_identity"):
        decode_projection(v1.encode(text))


def test_a_partial_confined_receipt_is_refused_on_the_wire():
    run = confined_closure()
    text = cast(Any, v1.decode(projection_text(run)))
    del text["occurrence"]["receipt"]["execution"]["mounts"]
    with pytest.raises(MalformedRecord):
        decode_projection(v1.encode(text))


def test_a_reordered_confined_list_is_out_of_canonical_order():
    run = confined_closure()
    text = cast(Any, v1.decode(projection_text(run)))
    text["occurrence"]["receipt"]["execution"]["instance"]["namespaces"].reverse()
    with pytest.raises(MalformedRecord, match="canonical order"):
        decode_projection(v1.encode(text))


def test_wire_jobs_refuse_inconsistent_semantic_keys_and_duplicate_wildcards():
    planned = cast(Any, v1.decode(projection_text(closure())))
    planned["occurrence"]["planned"][0]["job_key"] = job_key("other", ())
    with pytest.raises(MalformedRecord, match="disagrees with its family"):
        decode_projection(v1.encode(planned))

    traced = cast(Any, v1.decode(projection_text(closure())))
    traced["occurrence"]["trace"][0]["wildcards"] = [["sample", "a"], ["sample", "b"]]
    with pytest.raises(MalformedRecord, match="name each binding once"):
        decode_projection(v1.encode(traced))


def test_the_run_closure_facet_survives_the_confined_shape():
    run = confined_closure()
    node = _node_of(run)
    assert set(node.facets[RUN_CLOSURE_FACET]) == {"projection"}


def _with_recomputed_mount_identity(receipt: dict) -> dict:
    instance = receipt["instance"]
    instance["mount_plan_identity"] = mount_plan_identity(tuple(tuple(row) for row in instance["mounts"]))
    return receipt


@pytest.mark.parametrize(
    "mutate, match",
    [
        (lambda r: r["capabilities"].insert(0, r["capabilities"][0]), "capabilities"),
        (lambda r: _with_recomputed_mount_identity(r)["instance"]["mounts"].insert(0, list(r["instance"]["mounts"][0])), "mounts"),
        (lambda r: _with_recomputed_mount_identity(r)["instance"]["mounts"][0].__setitem__(2, "rx"), "mounts"),
        (lambda r: r["rendered_environment"][0].__setitem__(1, "directory"), "rendered_environment"),
    ],
)
def test_the_wire_refuses_what_the_values_refuse(mutate, match):
    """Parity: a projection the value types could not construct is refused on
    the wire too — a duplicate capability, a duplicate mountpoint, an access
    outside MOUNT_ACCESS, a rendered kind outside RENDERED_KINDS."""
    run = confined_closure()
    text = cast(Any, v1.decode(projection_text(run)))
    launch = text["occurrence"]["receipt"]["execution"]
    mutate(launch)
    if "mounts" in match:
        _with_recomputed_mount_identity(launch)
    with pytest.raises(MalformedRecord, match=match):
        decode_projection(v1.encode(text))
