"""The predicate and the invariant, over an in-memory view."""

from typing import Any, cast

import lineage_fixtures as lineage
import pytest
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut3 import typed_applicability, typed_estimand
from nodes.core.relations import Relation
from profiles import BASE
from test_read_side import seed  # the module's raw-write seeding helper

from beliefs import stored
from beliefs.acquisition import bearer_refusal, validity_refusal
from beliefs.errors import MalformedRecord

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
GOOD = {"locator": "accession:GSE1", "attested_by": "test-actor"}


def acquired(seed="d", **facet):
    return stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation={**GOOD, **facet})


def test_a_valid_declaration_on_an_unproduced_dataset_passes(tmp_path):
    node = acquired()
    assert validity_refusal(seed(tmp_path, node), node, BASE) is None


def test_absence_and_invalidity_are_distinct_reasons(tmp_path):
    plain = stored.dataset_node(title="p", resources=PINNED)
    assert validity_refusal(seed(tmp_path, plain), plain, BASE) == "no-empirical-observation-facet"
    bad = stored.dataset_node(title="b", resources=PINNED, empirical_observation={"boundary": "x"})
    assert str(validity_refusal(seed(tmp_path / "b", bad), bad, BASE)).startswith("facet-payload-malformed:")


def test_a_lineage_basis_disqualifies_even_with_a_valid_facet(tmp_path):
    node = stored.dataset_node(
        title="d", resources=PINNED, empirical_observation=GOOD, basis={"tag": "single", "routes": []}
    )
    assert (
        validity_refusal(seed(tmp_path, node), node, BASE)
        == "facet-bearer-produced: the dataset carries a lineage basis"
    )


def test_a_producer_disqualifies(tmp_path):
    node = acquired()
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[node.id])
    assert validity_refusal(seed(tmp_path, node, run), node, BASE) == f"facet-bearer-produced: produced by {run.id}"


def test_a_dangling_producer_edge_counts_before_the_dataset_exists(tmp_path):
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[dataset_ref("d")])
    view = seed(tmp_path, run)
    assert view.producers(dataset_ref("d")) == (run.id,)
    assert (
        bearer_refusal(view, acquired())
        == f"{dataset_ref('d')}: carries the empirical-observation facet and is produced by {run.id}"
    )


def test_an_alias_reaches_the_producer(tmp_path):
    node = acquired()
    node.deprecated_ids = ["dataset:old"]
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=["dataset:old"])
    view = seed(tmp_path, stored.stamp_semantic_identity(node), run)
    assert view.producers(node.id, aliases=("dataset:old",)) == (run.id,)


def test_an_unresolved_retrieval_disqualifies(tmp_path):
    node = acquired(retrieval="act-report:" + "0" * 64)
    assert validity_refusal(seed(tmp_path, node), node, BASE) == "facet-retrieval-unresolved: act-report:" + "0" * 64


def test_the_bearer_invariant_reads_the_edge_whatever_its_carrier(tmp_path):
    node = acquired()
    view = seed(tmp_path, node)
    source = stored.source_node(title="s", identifiers={"doi": "10.1234/x"})
    source.relations.append(Relation(source=source.id, predicate="produces", target=node.id))
    assert (
        bearer_refusal(view, source)
        == f"{source.id}: produces {node.id}, which carries the empirical-observation facet"
    )


def test_a_new_dataset_producing_itself_is_refused_by_id_and_by_alias(tmp_path):
    view = seed(tmp_path)  # an empty corpus: nothing resolves, so only the candidate can answer
    for target in (dataset_ref("d"), "dataset:old"):
        node = acquired()
        node.deprecated_ids = ["dataset:old"]
        node.relations.append(Relation(source=node.id, predicate="produces", target=target))
        assert (
            bearer_refusal(view, node)
            == f"{dataset_ref('d')}: carries the empirical-observation facet and produces itself"
        )


def test_a_non_acquisition_report_disqualifies(tmp_path):
    from fixtures_cut3 import report

    report_node = stored.act_report_node(report(operation="audit"))
    node = acquired(retrieval=report_node.id)
    assert validity_refusal(seed(tmp_path, report_node), node, BASE) == (
        f"facet-retrieval-unresolved: {report_node.id} is not an acquisition report"
    )


def test_a_lineage_basis_breaks_the_bearer_invariant(tmp_path):
    node = stored.dataset_node(
        title="d", resources=PINNED, empirical_observation=GOOD, basis={"tag": "single", "routes": []}
    )
    assert (
        bearer_refusal(seed(tmp_path), node)
        == f"{node.id}: carries the empirical-observation facet and a lineage basis"
    )


def test_producers_are_unique_sorted_and_ignore_other_edges(tmp_path):
    node = acquired()
    node.deprecated_ids = ["dataset:old"]
    first = stored.run_node("a", title="a", spec="analysis-spec:s", produces=[node.id, "dataset:old"])
    last = stored.run_node("z", title="z", spec="analysis-spec:s", produces=["dataset:old"])
    reader = stored.run_node("reader", title="reader", spec="analysis-spec:s", observes=[node.id])
    view = seed(tmp_path, stored.stamp_semantic_identity(node), last, first, reader)
    assert view.producers(node.id) == (first.id, last.id)


def test_eligibility_is_existential_and_reports_invalidity(tmp_path):
    from beliefs.corpus import eligibility_refusal

    good = acquired("good")
    bad = acquired("bad", retrieval="act-report:" + "0" * 64)
    assessment = stored.assessment_node(
        "a",
        title="a",
        spec="analysis-spec:s",
        run="run:r",
        proposition="proposition:p",
        outcome="supported",
        interpretation_rule="rule:threshold",
        estimand=typed_estimand(),
        applicability=typed_applicability(),
    )
    run = stored.run_node("r", title="r", spec="analysis-spec:s", observes=["dataset:missing", bad.id])
    view = seed(tmp_path / "bad", bad, run)
    reason = eligibility_refusal(view, assessment, BASE)
    assert reason is not None and "dataset:missing: unresolved" in reason and "facet-retrieval-unresolved" in reason
    run = stored.run_node("r", title="r", spec="analysis-spec:s", observes=[bad.id, good.id])
    assert eligibility_refusal(seed(tmp_path / "good", bad, good, run), assessment, BASE) is None


def test_even_a_malformed_lineage_basis_is_not_absent(tmp_path):
    node = acquired()
    node.facets[stored.LINEAGE_BASIS_FACET] = cast(Any, "malformed")
    view = seed(tmp_path)
    assert validity_refusal(view, node, BASE) == "facet-bearer-produced: the dataset carries a lineage basis"
    assert bearer_refusal(view, node) == f"{node.id}: carries the empirical-observation facet and a lineage basis"


def test_a_present_null_payload_is_malformed_not_absent(tmp_path):
    node = acquired()
    node.facets[stored.EMPIRICAL_OBSERVATION_FACET] = cast(Any, None)
    reason = validity_refusal(seed(tmp_path), node, BASE)
    assert reason is not None and reason.startswith("facet-payload-malformed:")


def test_validate_lineage_basis_checks_route_fields():
    good = stored.dataset_node(
        title="d1",
        resources=PINNED,
        basis={"tag": "single", "routes": [{"run": "run:r1", "ancestor": "dataset:d0", "transforms": ["dataset:d0"]}]},
    )
    stored.validate_lineage_basis(good)
    stored.validate_lineage_basis(stored.dataset_node(title="plain", resources=PINNED))
    identitied = good.model_copy(
        update={
            "facets": {
                **good.facets,
                "lineage-basis": {
                    "tag": "single",
                    "routes": [
                        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": ["dataset:d0"], "identity": "route:1"}
                    ],
                },
            }
        }
    )
    stored.validate_lineage_basis(identitied)
    for bad_route in (
        {"run": "", "ancestor": "dataset:d0", "transforms": ["dataset:d0"]},
        {"run": "run:r1", "ancestor": "", "transforms": ["dataset:d0"]},
        {"run": "run:r1", "transforms": ["dataset:d0"]},
        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": []},
        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": 123},
        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": [""]},
        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": ["dataset:d0"], "extra": "x"},
        {"run": "run:r1", "ancestor": "dataset:d0", "transforms": ["dataset:d0"], "identity": ""},
    ):
        node = good.model_copy(
            update={"facets": {**good.facets, "lineage-basis": {"tag": "single", "routes": [bad_route]}}}
        )
        with pytest.raises(MalformedRecord):
            stored.validate_lineage_basis(node)
    malformed_tag = good.model_copy(update={"facets": {**good.facets, "lineage-basis": "malformed"}})
    with pytest.raises(MalformedRecord):
        stored.validate_lineage_basis(malformed_tag)


# --- empirical standing inherited through lineage (beliefs-8ecbb5) ------------


def _chain(*, ancestor=None):
    """d2 -> d1 -> d0, each hop a production run stamped as the boundary stamps it."""
    d0 = lineage.acquired("d0") if ancestor is None else ancestor
    d1 = lineage.derived("d1", lineage.route("run:p1", d0.id))
    d2 = lineage.derived("d2", lineage.route("run:p2", d1.id))
    return d0, d1, d2, lineage.production("p1", d0.id, d1.id), lineage.production("p2", d1.id, d2.id)


def _outcome(tmp_path, observed, *nodes):
    from beliefs.corpus import eligibility_outcome

    run = lineage.analysis("r", observed)
    view = seed(tmp_path, run, *nodes)
    return eligibility_outcome(view, lineage.assessment_over("a", run.id), BASE)


def test_derived_dataset_inherits_standing_from_acquired_ancestor(tmp_path):
    d0, d1, d2, p1, p2 = _chain()
    assert _outcome(tmp_path / "one", d1.id, d0, d1, p1) is None
    assert _outcome(tmp_path / "two", d2.id, d0, d1, d2, p1, p2) is None
    view = seed(tmp_path / "direct", d0, d1, d2, p1, p2)
    assert validity_refusal(view, d1, BASE) == "no-empirical-observation-facet"
    assert validity_refusal(view, d2, BASE) == "no-empirical-observation-facet"
    assert validity_refusal(view, d0, BASE) is None


def test_derived_dataset_standing_fails_on_unobserving_ancestor_or_divergent_producer_or_missing_link_or_malformed_ancestor(
    tmp_path,
):
    d0, d1, d2, p1, p2 = _chain(ancestor=lineage.plain("d0"))
    outcome = _outcome(tmp_path / "plain", d1.id, d0, d1, p1)
    assert outcome is not None and outcome.unresolved == ()
    assert f"{d1.id}: {d0.id}: no-empirical-observation-facet" in outcome.reason
    assert outcome.reason.startswith("no observes input of 'run:r' has empirical standing (")

    d0, d1, _d2, p1, _p2 = _chain()
    other = lineage.production("other", lineage.ref("elsewhere"), d1.id)
    outcome = _outcome(tmp_path / "divergent", d1.id, d0, d1, p1, other)
    assert outcome is not None and outcome.unresolved == ()
    assert f"{d1.id}: lineage-divergent" in outcome.reason

    no_run = lineage.derived("d1", lineage.route("run:missing", d0.id))
    outcome = _outcome(tmp_path / "no-run", no_run.id, d0, no_run)
    assert outcome is not None and outcome.unresolved == ("run:missing",)
    assert f"{no_run.id}: lineage-incomplete" in outcome.reason

    no_ancestor = lineage.derived("d1", lineage.route("run:p1", "dataset:missing"))
    outcome = _outcome(
        tmp_path / "no-ancestor",
        no_ancestor.id,
        no_ancestor,
        lineage.production("p1", "dataset:missing", no_ancestor.id),
    )
    assert outcome is not None and outcome.unresolved == ("dataset:missing",)
    assert f"{no_ancestor.id}: lineage-incomplete" in outcome.reason

    d0, d1, d2, p1, p2 = _chain()
    d1.facets[stored.LINEAGE_BASIS_FACET]["routes"][0]["transforms"] = 123
    stored.stamp_semantic_identity(d1)
    outcome = _outcome(tmp_path / "malformed", d2.id, d0, d1, d2, p1, p2)
    assert outcome is not None and outcome.unresolved == ()
    assert f"{d2.id}: lineage-basis-malformed:" in outcome.reason


def test_a_cycle_refuses_as_incomplete_with_nothing_unresolved(tmp_path):
    a_ref, b_ref = lineage.ref("a"), lineage.ref("b")
    a = lineage.derived("a", lineage.route("run:pa", b_ref))
    b = lineage.derived("b", lineage.route("run:pb", a_ref))
    outcome = _outcome(
        tmp_path, a.id, a, b, lineage.production("pa", b_ref, a_ref), lineage.production("pb", a_ref, b_ref)
    )
    assert outcome is not None and outcome.unresolved == ()
    assert f"{a.id}: lineage-incomplete" in outcome.reason


def test_a_terminal_with_an_unresolved_retrieval_report_refuses(tmp_path):
    d0, d1, _d2, p1, _p2 = _chain(ancestor=lineage.acquired("d0", retrieval="act-report:" + "0" * 64))
    outcome = _outcome(tmp_path, d1.id, d0, d1, p1)
    assert outcome is not None
    assert f"{d1.id}: {d0.id}: facet-retrieval-unresolved: act-report:" + "0" * 64 in outcome.reason


def test_a_derived_dataset_carrying_the_facet_stays_refused_by_the_bearer_rule(tmp_path):
    d0 = lineage.acquired("d0")
    both = stored.dataset_node(
        title="d1",
        resources=pinned("d1"),
        empirical_observation=lineage.OBSERVATION,
        basis={"tag": "single", "routes": [lineage.route("run:p1", d0.id)]},
    )
    p1 = lineage.production("p1", d0.id, both.id)
    outcome = _outcome(tmp_path, both.id, d0, both, p1)
    assert outcome is not None
    assert f"{both.id}: facet-bearer-produced: the dataset carries a lineage basis" in outcome.reason
    assert bearer_refusal(seed(tmp_path / "b", d0, p1), both) is not None


def _identitied(d0, *identities_runs):
    return lineage.derived("d1", *(lineage.route(run, d0.id, identity=identity) for identity, run in identities_runs))


def test_route_retraction_and_fail_closed_unreadable_retraction_on_identitied_basis(tmp_path):
    d0 = lineage.acquired("d0")
    conflict = _identitied(d0, ("route:1", "run:p1"), ("route:2", "run:p2"))
    producers = (lineage.production("p1", d0.id, conflict.id), lineage.production("p2", d0.id, conflict.id))
    outcome = _outcome(tmp_path / "conflict", conflict.id, d0, conflict, *producers)
    assert outcome is not None and f"{conflict.id}: lineage-divergent" in outcome.reason
    retired_one = lineage.route_retraction(conflict, "route:2", "rr2")
    assert _outcome(tmp_path / "retired-one", conflict.id, d0, conflict, *producers, retired_one) is None

    single = _identitied(d0, ("route:1", "run:p1"))
    p1 = lineage.production("p1", d0.id, single.id)
    assert _outcome(tmp_path / "single", single.id, d0, single, p1) is None
    retired = lineage.route_retraction(single, "route:1", "rr1")
    outcome = _outcome(tmp_path / "retired-all", single.id, d0, single, p1, retired)
    assert outcome is not None and outcome.unresolved == ()
    assert f"{single.id}: lineage-incomplete" in outcome.reason
    counter = lineage.node_retraction(retired, "c1")
    assert _outcome(tmp_path / "countered", single.id, d0, single, p1, retired, counter) is None

    stale = lineage.node_retraction(lineage.assessment_over("other", "run:other"), "s1")
    stale.facets[stored.RETRACTION_FACET]["rationale"] = "changed after stamping"
    outcome = _outcome(tmp_path / "stale", single.id, d0, single, p1, stale)
    assert outcome is not None and outcome.unresolved == ()
    assert f"{single.id}: retraction-unreadable:" in outcome.reason

    from test_local_standing import raw_retraction

    cycle = (raw_retraction("retraction:r1", "retraction:r2"), raw_retraction("retraction:r2", "retraction:r1"))
    outcome = _outcome(tmp_path / "cycle", single.id, d0, single, p1, *cycle)
    assert outcome is not None and f"{single.id}: retraction-unreadable:" in outcome.reason
    # an identity-free basis never folds retractions, so the same broken corpus still confers standing
    boundary = lineage.derived("d1", lineage.route("run:p1", d0.id))
    assert _outcome(tmp_path / "boundary", boundary.id, d0, boundary, p1, *cycle) is None


def test_aliased_producer_and_ancestor_resolve_through_deprecated_ids(tmp_path):
    d0 = lineage.acquired("d0")
    d0.deprecated_ids = ["dataset:old-d0"]
    d1 = lineage.derived("d1", lineage.route("run:old-p1", "dataset:old-d0"))
    p1 = lineage.production("p1", "dataset:old-d0", d1.id)
    p1.deprecated_ids = ["run:old-p1"]
    nodes = (stored.stamp_semantic_identity(d0), d1, stored.stamp_semantic_identity(p1))
    assert _outcome(tmp_path, d1.id, *nodes) is None
