from __future__ import annotations

import pytest
from dataset_fixtures import dataset_ref, pinned

from beliefs import stored
from beliefs.dataset import dataset_address
from beliefs.errors import BasisMissing, MalformedRecord

PINNED = [{"name": "data", "digest": "sha256:" + "ab" * 32}]


class TestTheDatasetBuilder:
    def test_it_derives_the_id_from_the_declaration(self):
        node = stored.dataset_node(title="DepMap 24Q2", resources=pinned("depmap"))
        assert node.id == dataset_ref("depmap") == stored.dataset_address_of(node)
        assert node.facets[stored.DATASET_FACET] == {"resources": pinned("depmap")}

    def test_one_byte_set_is_one_id_whatever_the_title_order_repetition_or_names(self):
        a = pinned("a")[0]
        b = pinned("b")[0]
        one = stored.dataset_node(title="first", resources=[a, b])
        two = stored.dataset_node(title="second", resources=[b, a, {"name": "copy", "digest": a["digest"]}])
        assert one.id == two.id
        assert stored.dataset_node(title="x", resources=[a]).id != one.id

    def test_an_unpinned_or_empty_declaration_refuses_at_the_builder(self):
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="DepMap", resources=[])
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="DepMap", resources=[*pinned("p"), {"name": "unpinned"}])
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="md5", resources=[{"name": "m", "digest": "md5:" + "0" * 32}])

    def test_the_slug_parameter_is_gone(self):
        with pytest.raises(TypeError):
            stored.dataset_node("slug", title="t", resources=pinned("s"))  # type: ignore[misc]


def _dataset(seed: str, basis=None):
    return stored.dataset_node(title=seed, resources=pinned(seed), basis=basis)


def test_dataset_address_of_reads_the_stored_declaration_not_the_id():
    handle = stored.governed_node("dataset", "handle", "handle", {stored.DATASET_FACET: {"resources": PINNED}}, ())
    assert stored.dataset_address_of(handle) == dataset_address(stored.dataset_declaration(handle))
    assert stored.dataset_address_of(handle) != handle.id


def test_dataset_address_of_is_none_for_an_unpinned_record():
    unpinned = stored.governed_node("dataset", "u", "u", {stored.DATASET_FACET: {"resources": [{"name": "x"}]}}, ())
    assert stored.dataset_address_of(unpinned) is None


def _route(identity: str) -> dict[str, object]:
    return {
        "identity": identity,
        "run": f"run:{identity}",
        "ancestor": dataset_ref(identity),
        "transforms": [dataset_ref(identity)],
    }


def test_union_lineage_bases_keeps_a_single_tag_for_equal_bases():
    basis = {"tag": "single", "routes": [_route("a")]}

    facets = stored.union_lineage_bases(_dataset("kept", basis), _dataset("other", basis))

    assert facets[stored.LINEAGE_BASIS_FACET] == basis


def test_union_lineage_bases_makes_a_sorted_conflict_for_differing_routes():
    facets = stored.union_lineage_bases(
        _dataset("kept", {"tag": "single", "routes": [_route("z")]}),
        _dataset("other", {"tag": "single", "routes": [_route("a")]}),
    )

    assert facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_route("z"), _route("a")],
    }


def test_union_lineage_bases_unions_two_conflicts():
    facets = stored.union_lineage_bases(
        _dataset(
            "kept",
            {"tag": "conflict", "routes": [_route("a"), _route("c")]},
        ),
        _dataset(
            "other",
            {"tag": "conflict", "routes": [_route("c"), _route("b")]},
        ),
    )

    assert facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_route("a"), _route("c"), _route("b")],
    }


def test_a_conflict_with_fewer_than_two_routes_is_unconstructible():
    malformed = _dataset(
        "other", {"tag": "conflict", "routes": [_route("only")]}
    )

    with pytest.raises(MalformedRecord, match="conflict"):
        stored.union_lineage_bases(_dataset("kept"), malformed)


def test_equal_routes_retain_one_canonical_mapping_independent_of_operand_order():
    composed = {
        "identity": "route:cafe\u0301",
        "run": "run:cafe\u0301",
        "ancestor": "dataset:cafe\u0301",
        "transforms": ["dataset:cafe\u0301"],
    }
    canonical = {
        "ancestor": "dataset:café",
        "identity": "route:café",
        "run": "run:café",
        "transforms": ["dataset:café"],
    }
    first = _dataset("same", {"tag": "single", "routes": [composed]})
    second = _dataset("same", {"routes": [canonical], "tag": "single"})

    forward = stored.union_lineage_bases(first, second)
    reverse = stored.union_lineage_bases(second, first)

    assert forward == reverse
    assert forward[stored.LINEAGE_BASIS_FACET] == {
        "tag": "single",
        "routes": [canonical],
    }
    assert list(forward[stored.LINEAGE_BASIS_FACET]["routes"][0]) == [
        "ancestor",
        "identity",
        "run",
        "transforms",
    ]


# --- V2: the one place a kind prefix is added or removed (design §3.1) --------
from beliefs.runrecord import run_ref
from beliefs.stored import local_id, typed_ref


def test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref():
    address = "a" * 64
    assert typed_ref("run", address) == run_ref(address) == f"run:{address}"
    assert local_id("run", f"run:{address}") == address
    assert typed_ref("assessment", "a1") == "assessment:a1"
    assert local_id("verification", "verification:v-1") == "v-1"


@pytest.mark.parametrize(
    "call",
    [
        lambda: typed_ref("run", "run:abc"),
        lambda: typed_ref("run", ""),
        lambda: typed_ref("not-a-kind", "abc"),
        lambda: local_id("run", "abc"),
        lambda: local_id("run", "run:"),
        lambda: local_id("run", "assessment:abc"),
        lambda: local_id("run", None),  # type: ignore[arg-type]
    ],
)
def test_v2_the_helper_pair_refuses_the_wrong_shape(call):
    with pytest.raises(MalformedRecord):
        call()


def test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one():
    from fixtures_cut3 import typed_applicability, typed_estimand

    from beliefs import stored

    node = stored.assessment_node(
        "a1", title="a1", spec="s", run="run:r1", proposition="proposition:p", outcome="supported",
        interpretation_rule="rule-1", estimand=typed_estimand(), applicability=typed_applicability(),
    )
    # `AssessmentRef` reads only the three world-identity members — no
    # profile is needed to hand back the bare run (estimand-typing §9).
    assert stored.assessment_reference(node).run == "r1"
    node.facets[stored.ASSESSMENT_FACET]["run"] = "r1"
    with pytest.raises(MalformedRecord):
        stored.assessment_reference(node)
    del node.facets[stored.ASSESSMENT_FACET]["run"]
    with pytest.raises(MalformedRecord):
        stored.assessment_reference(node)


# --- V8: the analysis-spec record (design §7) --------------------------------
from decimal import Decimal

from authority import FULL
from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, spec_draft, spec_rules
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_corpus_write import OperationRecorder

from beliefs.corpus import CorpusWriter
from beliefs.spec import freeze


def _testing_writer(root):
    """A writer whose own profile activates the domain `spec_draft`'s typed
    estimand is built against — `_writer`'s BASE profile does not declare
    `testing/affects`, and a stored spec must restore under the profile that
    writes it (design §7.2)."""
    port = OperationRecorder(root, authority=FULL, profile=TESTING_PROFILE)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=TESTING_PROFILE, operation_port=port)
    writer.adopt_manifest(profile=pins_for(TESTING_PROFILE))
    return writer


def test_v8_analysis_spec_node_round_trips_through_the_writer_and_the_reader(tmp_path):
    from beliefs.projection import project_claim

    writer = _testing_writer(tmp_path / "corpus")
    # The boundary now refuses a spec whose target does not resolve to a
    # proposition its own estimand answers (estimand-typing §7.2, Task 8), so
    # `spec_draft`'s default `target` must name a real, matching proposition.
    target = writer.add(stored.proposition_node("p", title="p", claim=project_claim(TESTING_CLAIM)))
    spec = freeze(spec_draft(target=target.id, parameters={"alpha": Decimal("0.05")}), held_rules=spec_rules())
    node = writer.add(stored.analysis_spec_node(spec))
    assert node.id == f"analysis-spec:{spec.identity}"
    assert set(node.facets[stored.ANALYSIS_SPEC_FACET]) == {"identity", "projection"}
    restored = stored.analysis_spec_value(writer.read_view.get(node.id), profile=TESTING_PROFILE)
    assert restored == spec and type(restored.parameters["alpha"]) is Decimal


def test_v8_a_renamed_or_falsely_identified_record_is_malformed(tmp_path):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    node = stored.analysis_spec_node(spec)
    renamed = node.model_copy(update={"id": "analysis-spec:elsewhere"})
    with pytest.raises(MalformedRecord, match="not the spec identity"):
        stored.analysis_spec_value(renamed, profile=TESTING_PROFILE)
    node.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = node.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    stored.stamp_semantic_identity(node)  # the stamp passes; restoration is what detects the mismatch
    with pytest.raises(MalformedRecord):
        stored.analysis_spec_value(node, profile=TESTING_PROFILE)
    with pytest.raises(MalformedRecord):
        stored.analysis_spec_value(stored.proposition_node("p", title="p", claim={"operator": "affects"}), profile=TESTING_PROFILE)
