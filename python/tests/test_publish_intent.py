"""The publish intent (publication-records design §5, decisions 3, 9 and 10; row Y3)."""

from typing import Any

import pytest

from beliefs.coordination import Anchor, CoordinationAddress
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination, PublishIntent, decode_publish_intent, encode_publish_intent
from beliefs.intents.shapes import DecodedIntent, ReportEvidence, Unrecognized, decode_intent, mismatch
from beliefs.report import CLOSED, UNFINISHED, Registration, completion

VIEW = CoordinationAddress("a" * 32, "b" * 32, "c" * 32)


def intent(**changes) -> PublishIntent:
    values: dict[str, Any] = {
        "kind": "publish",
        "event_token": "d" * 32,
        "actor": "actor",
        "at": "2026-09-22T00:00:00Z",
        "view": VIEW,
        "destination": Destination.local("/srv/published/mm30"),
        "binding_tips": ("1" * 32,),
        "marker_tips": (("e" * 32, "f" * 32),),
        "anchors": (Anchor("0" * 32, "9" * 64, "8" * 64),),
    }
    values.update(changes)
    return PublishIntent(**values)


def decoded_payload() -> dict[str, Any]:
    payload = v1.decode(encode_publish_intent(intent()))
    assert isinstance(payload, dict)
    return payload


def test_the_intent_round_trips_byte_exactly():
    value = intent()
    payload = encode_publish_intent(value)
    assert decode_publish_intent(payload) == value
    assert encode_publish_intent(decode_publish_intent(payload)) == payload


@pytest.mark.parametrize(
    "changes",
    [
        {"binding_tips": ("2" * 32, "1" * 32)},
        {"binding_tips": ("1" * 32, "1" * 32)},
        {"marker_tips": (("e" * 32, "f" * 32), ("a" * 32, "f" * 32))},
        {"anchors": (Anchor("1" * 32, "9" * 64, "8" * 64), Anchor("0" * 32, "9" * 64, "8" * 64))},
        {"view": CoordinationAddress("a" * 32, "b" * 32)},
        {"at": "yesterday"},
        {"kind": "audit"},
        {"event_token": "short"},
        {"actor": ""},
        {"actor": 1},
    ],
    ids=[
        "tips-order",
        "tips-duplicate",
        "markers-order",
        "anchors-order",
        "view-unpinned",
        "at",
        "kind",
        "token",
        "actor-empty",
        "actor-int",
    ],
)
def test_every_malformed_field_is_refused(changes):
    with pytest.raises(MalformedRecord):
        intent(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"binding_tips": ({},)},
        {"binding_tips": ("1" * 32, 1)},
        {"binding_tips": ["1" * 32]},
        {"marker_tips": (({}, "f" * 32),)},
        {"marker_tips": (("e" * 32, "f" * 32), ("a" * 32, 1))},
        {"marker_tips": ({},)},
        {"anchors": (Anchor("0" * 32, "9" * 64, "8" * 64), {})},
        {"anchors": [Anchor("0" * 32, "9" * 64, "8" * 64)]},
    ],
    ids=[
        "binding-mapping",
        "binding-mixed",
        "binding-list",
        "marker-mapping",
        "marker-mixed",
        "marker-member-mapping",
        "anchor-mapping",
        "anchors-list",
    ],
)
def test_malformed_collection_members_raise_malformed_record_not_type_error(changes):
    """User review 2: every caller-supplied collection is validated member by member before ordering."""
    with pytest.raises(MalformedRecord):
        intent(**changes)


@pytest.mark.parametrize(
    "fields",
    [
        (1, "9" * 64, "8" * 64),
        ("0" * 32, {}, "8" * 64),
        ("0" * 32, "9" * 64, None),
        ("0" * 31, "9" * 64, "8" * 64),
        ("0" * 32, "9" * 63, "8" * 64),
        ("0" * 32, "9" * 64, "A" * 64),
    ],
    ids=["corpus-int", "genesis-mapping", "head-none", "corpus-short", "genesis-short", "head-upper"],
)
def test_an_anchor_refuses_malformed_fields_with_malformed_record(fields):
    """Types are checked before `re.fullmatch`, which raises TypeError on a non-string."""
    with pytest.raises(MalformedRecord):
        Anchor(*fields)


@pytest.mark.parametrize(
    "field, member",
    [
        ("anchors", 1),
        ("anchors", {"corpus_id": 1, "genesis": "9" * 64, "head": "8" * 64}),
        ("anchors", {"corpus_id": "0" * 32, "genesis": "9" * 64, "head": "8" * 64, "extra": "x"}),
        ("binding_tips", {}),
        ("marker_tips", "e" * 32),
        ("marker_tips", ["e" * 32, 1]),
    ],
)
def test_the_decoder_refuses_malformed_members_with_malformed_record(field, member):
    payload = decoded_payload()
    payload[field] = [member]
    with pytest.raises(MalformedRecord):
        decode_publish_intent(v1.encode(payload))


@pytest.mark.parametrize("field", ["binding_tips", "marker_tips", "anchors"])
def test_the_decoder_refuses_a_non_list_collection_before_converting_it(field):
    payload = decoded_payload()
    payload[field] = "1" * 32
    with pytest.raises(MalformedRecord, match=f"{field} is a list"):
        decode_publish_intent(v1.encode(payload))


def test_the_decoder_refuses_a_non_canonical_or_foreign_payload():
    with pytest.raises(MalformedRecord):
        decode_publish_intent(b"\xff")
    payload = decoded_payload()
    payload["domain"] = "science.holdings-intent.v1"
    with pytest.raises(MalformedRecord):
        decode_publish_intent(v1.encode(payload))


def test_destinations_are_canonical():
    assert Destination.local("/srv/published/../published/mm30/") == Destination.local("/srv/published/mm30")
    with pytest.raises(MalformedRecord):
        Destination("local", "relative/path")
    with pytest.raises(MalformedRecord):
        Destination("local", "//host/share")
    assert Destination.remote("HTTPS://Example.org/a").locator == Destination.remote("https://example.org/a").locator


@pytest.mark.parametrize(
    "value",
    [
        {"type": "ftp", "locator": "/x"},
        {"type": "local"},
        {"type": "local", "locator": 1},
        ["local", "/x"],
        {"type": "remote", "locator": "HTTPS://Example.org/a"},
    ],
    ids=["type", "missing-locator", "locator-int", "list", "remote-not-canonical"],
)
def test_a_malformed_destination_projection_is_refused(value):
    with pytest.raises(MalformedRecord):
        Destination.from_projection(value)


def test_decode_intent_dispatches_the_domain_and_mismatch_qualifies_by_a_publish_report():
    payload = encode_publish_intent(intent())
    decoded = decode_intent("0" * 64, payload)
    assert type(decoded) is DecodedIntent and decoded.shape == "publish"
    assert mismatch(decoded, ReportEvidence("publish", "d" * 32)) is None
    assert mismatch(decoded, ReportEvidence("audit", "d" * 32)) == "wrong-kind"
    assert mismatch(decoded, ReportEvidence("publish", "e" * 32)) == "wrong-token"


def test_a_malformed_payload_under_the_domain_is_malformed():
    payload = v1.encode({"domain": "science.publish-intent.v1", "kind": "publish"})
    decoded = decode_intent("0" * 64, payload)
    assert type(decoded) is Unrecognized and decoded.code == "intent-payload-malformed" and decoded.detail == "publish"


def test_completion_reads_a_publish_intent():
    from test_report import publish_report  # Task 2's helper

    from beliefs.report import BindingBound

    report = publish_report(BindingBound("d" * 32, "e" * 32, "f" * 32))
    value = intent(event_token=report.event_token)
    assert completion(value, (Registration(value.event_token, "r"),), {"r": report}) == CLOSED
    assert completion(value, (), {}) == UNFINISHED


def test_a_session_actor_on_a_publish_intent_names_its_session():
    """The session reconciler reads the actor of every decoded shape, publish included."""
    from beliefs.session.reconcile import _session_of

    decoded = decode_intent("0" * 64, encode_publish_intent(intent(actor="session:" + "7" * 32)))
    assert _session_of(decoded) == "7" * 32
