"""§2 items 1 and 14: the predicate and the invariant, over an in-memory view."""

from typing import Any, cast

from nodes.core.relations import Relation
from profiles import BASE
from test_read_side import seed  # the module's raw-write seeding helper (Task 11 gives it manifest arguments)

from beliefs import stored
from beliefs.acquisition import bearer_refusal, validity_refusal

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
GOOD = {"locator": "accession:GSE1", "attested_by": "test-actor"}


def acquired(slug="d", **facet):
    return stored.dataset_node(slug, title=slug, resources=PINNED, empirical_observation={**GOOD, **facet})


def test_a_valid_declaration_on_an_unproduced_dataset_passes(tmp_path):
    node = acquired()
    assert validity_refusal(seed(tmp_path, node), node, BASE) is None


def test_absence_and_invalidity_are_distinct_reasons(tmp_path):
    plain = stored.dataset_node("p", title="p", resources=PINNED)
    assert validity_refusal(seed(tmp_path, plain), plain, BASE) == "no-empirical-observation-facet"
    bad = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
    assert str(validity_refusal(seed(tmp_path / "b", bad), bad, BASE)).startswith("facet-payload-malformed:")


def test_a_lineage_basis_disqualifies_even_with_a_valid_facet(tmp_path):
    node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation=GOOD, basis={"tag": "single", "routes": []})
    assert validity_refusal(seed(tmp_path, node), node, BASE) == "facet-bearer-produced: the dataset carries a lineage basis"


def test_a_producer_disqualifies(tmp_path):
    node = acquired()
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[node.id])
    assert validity_refusal(seed(tmp_path, node, run), node, BASE) == f"facet-bearer-produced: produced by {run.id}"


def test_a_dangling_producer_edge_counts_before_the_dataset_exists(tmp_path):
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=["dataset:d"])
    view = seed(tmp_path, run)
    assert view.producers("dataset:d") == (run.id,)
    assert bearer_refusal(view, acquired()) == f"dataset:d: carries the empirical-observation facet and is produced by {run.id}"


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
    assert bearer_refusal(view, source) == f"{source.id}: produces {node.id}, which carries the empirical-observation facet"


def test_a_new_dataset_producing_itself_is_refused_by_id_and_by_alias(tmp_path):
    view = seed(tmp_path)  # an empty corpus: nothing resolves, so only the candidate can answer
    for target in ("dataset:d", "dataset:old"):
        node = acquired()
        node.deprecated_ids = ["dataset:old"]
        node.relations.append(Relation(source=node.id, predicate="produces", target=target))
        assert bearer_refusal(view, node) == "dataset:d: carries the empirical-observation facet and produces itself"


def test_a_non_acquisition_report_disqualifies(tmp_path):
    from fixtures_cut3 import report

    report_node = stored.act_report_node(report(operation="audit"))
    node = acquired(retrieval=report_node.id)
    assert validity_refusal(seed(tmp_path, report_node), node, BASE) == (
        f"facet-retrieval-unresolved: {report_node.id} is not an acquisition report"
    )


def test_a_lineage_basis_breaks_the_bearer_invariant(tmp_path):
    node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation=GOOD, basis={"tag": "single", "routes": []})
    assert bearer_refusal(seed(tmp_path), node) == "dataset:d: carries the empirical-observation facet and a lineage basis"


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
        "a", title="a", spec="analysis-spec:s", run="run:r", proposition="proposition:p",
        outcome="supported", interpretation_rule="rule:threshold",
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
    assert bearer_refusal(view, node) == "dataset:d: carries the empirical-observation facet and a lineage basis"


def test_a_present_null_payload_is_malformed_not_absent(tmp_path):
    node = acquired()
    node.facets[stored.EMPIRICAL_OBSERVATION_FACET] = cast(Any, None)
    reason = validity_refusal(seed(tmp_path), node, BASE)
    assert reason is not None and reason.startswith("facet-payload-malformed:")
