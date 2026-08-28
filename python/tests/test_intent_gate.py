"""The total decode gate and per-shape matching requirements (spec §2.2, §3.2)."""

from science.identity import v1
from science.intents import shapes


def decoded(digest: str, payload: bytes) -> shapes.DecodedIntent:
    gate = shapes.decode_intent(digest, payload)
    assert type(gate) is shapes.DecodedIntent, gate
    return gate


def unrecognized(digest: str, payload: bytes) -> shapes.Unrecognized:
    gate = shapes.decode_intent(digest, payload)
    assert type(gate) is shapes.Unrecognized, gate
    return gate


def _holdings_payload(**overrides) -> bytes:
    value = {
        "actor": "someone",
        "domain": "science.holdings-intent.v1",
        "event_token": "t" * 32,
        "kind": "re-check",
        "location": {
            "relative_path": "a/b",
            "store_id": "0" * 32,
            "type": "store",
        },
    }
    value.update(overrides)
    return v1.encode(value)


def test_the_three_discriminators_are_exact_and_disjoint() -> None:
    assert decoded(
        "d1",
        v1.encode({"kind": "import", "event_token": "t", "actor": "a"}),
    ).shape == "operation"
    assert decoded(
        "d2",
        v1.encode({"spec_identity": "s", "event_token": "t", "actor": "a"}),
    ).shape == "assessment-run"
    assert decoded("d3", _holdings_payload()).shape == "holdings"


def test_the_built_holdings_boundary_payload_decodes_unicode_included() -> None:
    from collections.abc import Mapping

    from science.holdings.boundary import intent_payload
    from science.holdings.records import StoreLocator

    payload = intent_payload(
        location=StoreLocator(store_id="0" * 32, relative_path="a/b"),
        act_kind="re-check",
        event_token="t" * 32,
        actor="renée",
    )
    gate = decoded("d", payload)
    assert gate.shape == "holdings"
    assert isinstance(gate.value, Mapping) and gate.value["event_token"] == "t" * 32


def test_foreign_domain_reads_unrecognized_warning() -> None:
    gate = unrecognized("d", v1.encode({"domain": "science.other.v1", "x": "y"}))
    assert gate == shapes.Unrecognized(
        "d",
        "intent-domain-unrecognized",
        "warning",
        "science.other.v1",
    )


def test_empty_object_reads_domainless_unrecognized() -> None:
    gate = unrecognized("d", b"{}")
    assert gate.code == "intent-domain-unrecognized"
    assert gate.detail == "domainless-unrecognized"


def test_out_of_vocabulary_kind_is_domainless_unrecognized() -> None:
    gate = unrecognized(
        "d",
        v1.encode(
            {"kind": "dataset-production", "event_token": "t", "actor": "a"}
        ),
    )
    assert gate.code == "intent-domain-unrecognized"


def test_undecodable_bytes_read_undecodable() -> None:
    gate = unrecognized("d", b"not json")
    assert gate.code == "intent-domain-unrecognized"
    assert gate.detail == "undecodable"


def test_discriminator_matched_schema_invalid_is_payload_malformed_error() -> None:
    gate = unrecognized(
        "d",
        v1.encode({"kind": "import", "event_token": "", "actor": "a"}),
    )
    assert gate == shapes.Unrecognized(
        "d",
        "intent-payload-malformed",
        "error",
        "operation",
    )
    gate = unrecognized(
        "d",
        _holdings_payload(
            location={
                "relative_path": "/abs",
                "store_id": "0" * 32,
                "type": "store",
            }
        ),
    )
    assert gate.code == "intent-payload-malformed"


def test_matching_requirements_per_shape() -> None:
    run = shapes.RunEvidence("assessment", "s" * 64, "tok")
    intent = decoded(
        "d",
        v1.encode(
            {"spec_identity": "s" * 64, "event_token": "tok", "actor": "a"}
        ),
    )
    assert shapes.mismatch(intent, run) is None
    assert (
        shapes.mismatch(
            intent,
            shapes.RunEvidence("assessment", "x" * 64, "tok"),
        )
        == "wrong-spec"
    )
    assert (
        shapes.mismatch(
            intent,
            shapes.RunEvidence("assessment", "s" * 64, "other"),
        )
        == "wrong-token"
    )
    assert (
        shapes.mismatch(
            intent,
            shapes.RunEvidence("dataset-production", None, "tok"),
        )
        == "wrong-shape"
    )
    assert shapes.mismatch(intent, shapes.ReportEvidence("run-attempt", "tok")) is None
    assert (
        shapes.mismatch(intent, shapes.ReportEvidence("import", "tok"))
        == "wrong-kind"
    )
    assert (
        shapes.mismatch(intent, shapes.ObservationEvidence("store:x:y", "tok"))
        == "wrong-purpose"
    )

    production = decoded(
        "d",
        v1.encode({"kind": "run-attempt", "event_token": "tok", "actor": "a"}),
    )
    assert (
        shapes.mismatch(
            production,
            shapes.RunEvidence("dataset-production", None, "tok"),
        )
        is None
    )
    assert (
        shapes.mismatch(
            production,
            shapes.RunEvidence("assessment", "s" * 64, "tok"),
        )
        == "wrong-shape"
    )
    assert (
        shapes.mismatch(production, shapes.ReportEvidence("run-attempt", "tok"))
        is None
    )

    non_run = decoded(
        "d",
        v1.encode({"kind": "import", "event_token": "tok", "actor": "a"}),
    )
    assert shapes.mismatch(non_run, shapes.ReportEvidence("import", "tok")) is None
    assert (
        shapes.mismatch(non_run, shapes.ReportEvidence("audit", "tok"))
        == "wrong-kind"
    )
    assert (
        shapes.mismatch(
            non_run,
            shapes.RunEvidence("dataset-production", None, "tok"),
        )
        == "wrong-purpose"
    )

    held = decoded("d", _holdings_payload(kind="write"))
    location = "store:" + "0" * 32 + ":a/b"
    assert (
        shapes.mismatch(held, shapes.ObservationEvidence(location, "t" * 32))
        is None
    )
    assert (
        shapes.mismatch(
            held,
            shapes.ObservationEvidence(
                "store:" + "0" * 32 + ":other",
                "t" * 32,
            ),
        )
        == "wrong-location"
    )
    assert (
        shapes.mismatch(held, shapes.ObservationEvidence(location, "other"))
        == "wrong-token"
    )
    assert shapes.mismatch(held, shapes.InertRecord()) == "wrong-purpose"
