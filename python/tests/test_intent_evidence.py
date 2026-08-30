"""Captured bytes to qualification evidence (spec §3.1)."""

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_to_markdown

from beliefs import stored
from beliefs.errors import RecordUndecodable
from beliefs.holdings.records import Found, StoreLocator, holdings_observation
from beliefs.intents import evidence, shapes
from beliefs.intents.evidence import decode_node
from beliefs.intents.holdings import decode_holdings_intent


@pytest.fixture
def assessment_closure():
    return make_closure()


@pytest.fixture
def sample_act_report():
    return sample_report()


@pytest.fixture
def sample_observation_node():
    value = holdings_observation(
        location=StoreLocator("a" * 32, "payload/data.csv"),
        outcome=Found("sha256:" + "ab" * 32),
        observer="observer-1",
        instrument="instrument-1",
        event_token="event-1",
        observed_at="2026-08-24T12:00:00Z",
    )
    return stored.holdings_observation_node(value)


def test_run_publication_decodes_to_run_evidence(assessment_closure) -> None:
    from beliefs.runrecord import publication_plan

    _, path, (op,) = publication_plan(assessment_closure)
    decoded = evidence.decode_record(path, op.content)
    assert decoded == shapes.RunEvidence(
        "assessment",
        assessment_closure.recipe.spec_identity,
        assessment_closure.occurrence.event_token,
    )


def test_legacy_run_is_inert_not_undecodable() -> None:
    node = stored.run_node("legacy", title="legacy", spec="s" * 64)
    payload = node_to_markdown(node).encode("utf-8")
    assert evidence.decode_record("run/legacy.md", payload) == shapes.InertRecord()


def test_stale_stamp_is_undecodable(assessment_closure) -> None:
    from nodes.core.frontmatter import node_from_markdown

    from beliefs.runrecord import publication_plan

    _, path, (op,) = publication_plan(assessment_closure)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run-closure"]["projection"] += " "
    with pytest.raises(RecordUndecodable):
        evidence.decode_record(path, node_to_markdown(node).encode("utf-8"))


def test_act_report_decodes_operation_and_token(sample_act_report) -> None:
    payload = node_to_markdown(stored.act_report_node(sample_act_report)).encode(
        "utf-8"
    )
    decoded = evidence.decode_record(
        f"act-report/{sample_act_report.identity()}.md",
        payload,
    )
    assert decoded == shapes.ReportEvidence(
        sample_act_report.operation,
        sample_act_report.event_token,
    )


def test_holdings_observation_decodes_location_and_token(
    sample_observation_node,
) -> None:
    payload = node_to_markdown(sample_observation_node).encode("utf-8")
    slug = sample_observation_node.id.split(":", 1)[1]
    decoded = evidence.decode_record(f"holdings-observation/{slug}.md", payload)
    facet = sample_observation_node.facets["holdings-observation"]
    location = facet["location"]
    expected = f"store:{location['store_id']}:{location['relative_path']}"
    intent = decode_holdings_intent(
        {
            "digest": "i",
            "entry": {
                "payload": (
                    b'{"actor":"a","domain":"science.holdings-intent.v1",'
                    b'"event_token":"event-1","kind":"re-check","location":'
                    b'{"relative_path":"payload/data.csv","store_id":"'
                    + b"a" * 32
                    + b'","type":"store"}}'
                ).hex()
            },
        }
    )
    assert intent is not None and intent["location"] == expected
    assert decoded == shapes.ObservationEvidence(expected, facet["event_token"])


def test_a_record_under_the_wrong_path_or_name_is_undecodable(
    sample_act_report,
) -> None:
    payload = node_to_markdown(stored.act_report_node(sample_act_report)).encode(
        "utf-8"
    )
    identity = sample_act_report.identity()
    with pytest.raises(RecordUndecodable):
        evidence.decode_record(f"run/{identity}.md", payload)
    with pytest.raises(RecordUndecodable):
        evidence.decode_record("act-report/" + "0" * 64 + ".md", payload)


def test_a_malformed_act_report_entry_is_undecodable(sample_act_report) -> None:
    node = stored.act_report_node(sample_act_report)
    node.facets["act-report"]["entries"].append({"kind": "not-an-entry"})
    node.facets["semantic-identity"] = {
        "digest": stored.recompute_semantic_hash(node)
    }
    payload = node_to_markdown(node).encode("utf-8")
    with pytest.raises(RecordUndecodable):
        evidence.decode_record(
            f"act-report/{node.id.split(':', 1)[1]}.md",
            payload,
        )


def test_garbage_bytes_are_undecodable() -> None:
    with pytest.raises(RecordUndecodable):
        evidence.decode_record("run/x.md", b"\xff not markdown")


def test_record_layout_path_matches_exactly_the_three_namespaces() -> None:
    assert evidence.record_layout_path("run/" + "a" * 64 + ".md")
    assert evidence.record_layout_path("act-report/x.md")
    assert evidence.record_layout_path("holdings-observation/x.md")
    assert not evidence.record_layout_path("corpus.yaml")
    assert not evidence.record_layout_path("proposition/x.md")
    assert not evidence.record_layout_path("run/x.txt")


def _verification_bytes(slug: str = "v1") -> bytes:
    node = stored.verification_node(
        slug,
        title=slug,
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    return node_to_markdown(node).encode("utf-8")


def test_decode_node_returns_the_stamped_node_for_its_own_path() -> None:
    node = decode_node("verification/v1.md", _verification_bytes())
    assert node.id == "verification:v1"
    assert node.kind == "verification"


def test_decode_node_refuses_an_id_that_names_another_path() -> None:
    with pytest.raises(RecordUndecodable, match="does not name this path"):
        decode_node("verification/other.md", _verification_bytes())


def test_decode_node_refuses_a_stale_stamp() -> None:
    node = stored.verification_node(
        "v1",
        title="v1",
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    node.facets["verification"]["verdict"] = "passed"  # after the stamp
    with pytest.raises(RecordUndecodable, match="semantic stamp"):
        decode_node("verification/v1.md", node_to_markdown(node).encode("utf-8"))


def test_decode_node_refuses_a_missing_stamp() -> None:
    node = stored.verification_node(
        "v1",
        title="v1",
        assessment="sha256:" + "a" * 64,
        assessment_ref="assessment:a1",
        scope="clean-environment",
        verdict="failed",
    )
    del node.facets[stored.SEMANTIC_IDENTITY_FACET]
    with pytest.raises(RecordUndecodable, match="semantic stamp"):
        decode_node("verification/v1.md", node_to_markdown(node).encode("utf-8"))


def test_decode_node_refuses_bytes_that_are_not_a_record() -> None:
    with pytest.raises(RecordUndecodable):
        decode_node("verification/v1.md", b"---\nnot: [a record\n---\n")


@pytest.mark.parametrize(
    "payload",
    [
        b"---\nid: verification:v1\nuid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nkind: verification\ntitle: v1\nrelated: 1\n---\n",
        b"---\nid: verification:v1\nuid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nkind: verification\ntitle: v1\nrelations: [nope]\n---\n",
    ],
)
def test_decode_node_translates_yaml_valid_malformed_relation_shapes(
    payload: bytes,
) -> None:
    with pytest.raises(RecordUndecodable):
        decode_node("verification/v1.md", payload)
