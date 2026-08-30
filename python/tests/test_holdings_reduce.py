"""The fixture-bound holdings active-set reducer."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib import resources
from typing import Any

import pytest
import yaml
from nodes.core.node import Node
from nodes.core.projection import to_canonical_json
from test_world_log_codecs import Chain, inspected
from test_world_rules import make_world

from beliefs import stored
from beliefs.holdings.qualify import qualify_intent
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.identity import v1
from beliefs.world import logmodel, rules

REF_A = "a" * 64
REF_B = "b" * 64
REF_C = "c" * 64
STORE = "d" * 32
LOCATION = f"store:{STORE}:artifact.bin"
OTHER_LOCATION = f"store:{STORE}:other.bin"


def observation(
    ref: str,
    *,
    location: str = LOCATION,
    finding: str = "found",
    digest: str = "sha256:" + "1" * 64,
    expected: str | None = None,
    token: str = "token",
    observed_at: str = "2026-01-01T00:00:00Z",
    supersedes: tuple[str, ...] = (),
) -> dict[str, Any]:
    store, store_id, relative_path = location.split(":", 2)
    outcome: dict[str, Any] = {"finding": finding}
    if finding == "found":
        outcome["digest"] = digest
    facet: dict[str, Any] = {
        "kind": "holdings-observation",
        "location": {"type": store, "store_id": store_id, "relative_path": relative_path},
        "outcome": outcome,
        "observer": "observer",
        "instrument": "instrument",
        "event_token": token,
        "observed_at": observed_at,
        "supersedes": list(supersedes),
    }
    if expected is not None:
        facet["expected"] = expected
    canonical = json.dumps(
        {
            "id": f"holdings-observation:{ref}",
            "uid": ref[:32],
            "kind": "holdings-observation",
            "title": "Fabricated holdings observation",
            "facets": {"holdings-observation": facet},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert stored.holdings_observation_value(Node.model_validate(json.loads(canonical))).facet() == facet
    return {"uid": ref[:32], "canonical": canonical}


def intent(
    digest: str,
    *,
    kind: str = "write",
    location: str = LOCATION,
    token: str = "token",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store, store_id, relative_path = location.split(":", 2)
    value = payload if payload is not None else {
        "actor": "actor",
        "domain": "science.holdings-intent.v1",
        "event_token": token,
        "kind": kind,
        "location": {"relative_path": relative_path, "store_id": store_id, "type": store},
    }
    return {
        "digest": digest,
        "entry": {
            "kind": "intent",
            "payload": json.dumps(value, sort_keys=True, separators=(",", ":")).encode().hex(),
        },
    }


def registration(
    digest: str,
    intent_digest: str,
    *,
    final: list[list[object]] | None = None,
) -> dict[str, Any]:
    return {
        "digest": digest,
        "entry": {
            "kind": "registered",
            "txid": "tx-" + digest[0],
            "intent_digest": "sha256:" + "e" * 64,
            "consumer_tag": "science-corpus-write-v1",
            "fulfills": intent_digest,
            "initial": [],
            "final": [] if final is None else final,
        },
    }


def settlement(digest: str, registration_digest: str, *, outcome: str = "committed") -> dict[str, Any]:
    return {
        "digest": digest,
        "entry": {
            "kind": "settled",
            "txid": "tx-" + registration_digest[0],
            "registration": registration_digest,
            "outcome": outcome,
        },
    }


def file_row(path: str) -> list[Any]:
    return [path, [["content_hash", "sha256:" + "9" * 64], ["kind", "file"], ["mode", "0o100644"]]]


def corpus(
    *,
    records: list[dict[str, Any]] | None = None,
    chain: list[dict[str, Any]] | None = None,
    corpus_id: str = "corpus-a",
) -> dict[str, Any]:
    return {
        "corpus_id": corpus_id,
        "corpus_state": "sha256:" + "1" * 64,
        "chain_head": (chain or [{"digest": "0" * 64}])[-1]["digest"],
        "records": records or [],
        "chain": chain or [],
    }


def capture(*corpora: dict[str, Any]) -> dict[str, Any]:
    return {"corpora": list(corpora)}


def invoke(value: dict[str, Any]) -> dict[str, Any]:
    result = rules._load_entry_point("reduce_holdings", holdings_rule_bundle().implementation)(value)
    assert isinstance(result, dict)
    return result


def member(ref: str, *, location: str = LOCATION, finding: str = "found", digest: str = "sha256:" + "1" * 64,
           expected: str | None = None, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    outcome: dict[str, Any] = {"finding": finding}
    if finding == "found":
        outcome["digest"] = digest
    value: dict[str, Any] = {
        "head": ref,
        "location": location,
        "outcome": outcome,
        "history": history or [],
    }
    if expected is not None:
        value["expected"] = expected
    return value


def matched_chain(intent_ref: str = "1" * 64, registration_ref: str = "2" * 64) -> list[dict[str, Any]]:
    return [
        intent(intent_ref),
        registration(registration_ref, intent_ref, final=[file_row(f"holdings-observation/{REF_A}.md")]),
        settlement("3" * 64, registration_ref),
    ]


def test_the_bundle_installs_through_the_fixture_bound_admission(tmp_path):
    bundle = holdings_rule_bundle()
    binding = rules.install_rule_binding(make_world(tmp_path), bundle)

    assert rules.binding_for(bundle) == binding
    assert [name for name, _content in bundle.fixtures] == [
        "holdings.basic.yaml",
        "holdings.blocked.yaml",
        "holdings.empty.yaml",
        "holdings.unresolved.yaml",
    ]


def test_no_timestamp_ordering():
    first = capture(corpus(records=[observation(REF_A), observation(REF_B, observed_at="2026-12-31T00:00:00Z")]))
    swapped = deepcopy(first)
    first_facets = [json.loads(row["canonical"])["facets"]["holdings-observation"] for row in first["corpora"][0]["records"]]
    swapped_facets = [
        json.loads(row["canonical"])["facets"]["holdings-observation"]
        for row in swapped["corpora"][0]["records"]
    ]
    swapped_facets[0]["observed_at"], swapped_facets[1]["observed_at"] = (
        swapped_facets[1]["observed_at"], swapped_facets[0]["observed_at"]
    )
    for row, facet in zip(swapped["corpora"][0]["records"], swapped_facets, strict=True):
        document = json.loads(row["canonical"])
        document["facets"]["holdings-observation"] = facet
        row["canonical"] = json.dumps(document, sort_keys=True, separators=(",", ":"))

    assert first_facets[0]["observed_at"] != first_facets[1]["observed_at"]
    assert all(not facet["supersedes"] for facet in (*first_facets, *swapped_facets))
    normalized_first = deepcopy(first)
    normalized_swapped = deepcopy(swapped)
    for value in (normalized_first, normalized_swapped):
        for row in value["corpora"][0]["records"]:
            document = json.loads(row["canonical"])
            document["facets"]["holdings-observation"]["observed_at"] = "<ignored>"
            row["canonical"] = json.dumps(document, sort_keys=True, separators=(",", ":"))
    assert normalized_first == normalized_swapped
    assert invoke(first) == invoke(swapped) == {"active": [member(REF_A), member(REF_B)], "blocked": []}


def test_disagreeing_heads_block_as_contested():
    result = invoke(capture(corpus(records=[observation(REF_A), observation(REF_B, finding="absent")])))

    assert result == {
        "active": [],
        "blocked": [{
            "location": LOCATION,
            "reasons": ["contested"],
            "heads": [member(REF_A), member(REF_B, finding="absent")],
        }],
    }


def test_a_cycle_refuses_the_whole_projection():
    value = capture(corpus(records=[
        observation(REF_A, supersedes=(REF_B,)),
        observation(REF_B, supersedes=(REF_A,)),
        observation(REF_C, location=OTHER_LOCATION),
    ]))

    with pytest.raises(ValueError, match=f"^supersession cycle at {LOCATION}$"):
        invoke(value)


def test_unmatched_and_unresolved_intents_block_distinctly_and_a_later_recheck_lifts():
    unmatched = intent("1" * 64)
    pending = intent("2" * 64, location=OTHER_LOCATION)
    pending_registration = registration("3" * 64, "2" * 64)
    value = capture(corpus(chain=[unmatched, pending, pending_registration]))

    assert invoke(value) == {
        "active": [],
        "blocked": [
            {"location": LOCATION, "reasons": ["unsettled"], "heads": []},
            {"location": OTHER_LOCATION, "reasons": ["unsettled"], "heads": []},
        ],
    }

    repaired = deepcopy(value)
    repaired["corpora"][0]["records"] = [observation(REF_A, location=LOCATION, token="repair")]
    repaired["corpora"][0]["chain"].extend([
        intent("4" * 64, kind="re-check", token="repair"),
        registration("5" * 64, "4" * 64, final=[file_row(f"holdings-observation/{REF_A}.md")]),
        settlement("6" * 64, "5" * 64),
    ])

    assert invoke(repaired)["blocked"] == [
        {"location": OTHER_LOCATION, "reasons": ["unsettled"], "heads": []}
    ]


def test_agreeing_heads_all_stay_active_with_their_expectations():
    first_expected = "sha256:" + "2" * 64
    second_expected = "sha256:" + "3" * 64
    result = invoke(capture(corpus(records=[
        observation(REF_A, expected=first_expected),
        observation(REF_B, expected=second_expected),
    ])))

    assert result == {
        "active": [member(REF_A, expected=first_expected), member(REF_B, expected=second_expected)],
        "blocked": [],
    }


def test_algorithm_mixed_found_pair_is_incommensurable():
    result = invoke(capture(corpus(records=[
        observation(REF_A),
        observation(REF_B, digest="sha512:" + "4" * 128),
    ])))

    assert result["active"] == []
    assert result["blocked"][0]["reasons"] == ["incommensurable"]


def test_same_algorithm_disagreement_and_mixed_algorithms_carry_both_reasons():
    result = invoke(capture(corpus(records=[
        observation(REF_A, digest="sha256:" + "1" * 64),
        observation(REF_B, digest="sha256:" + "2" * 64),
        observation(REF_C, digest="sha512:" + "3" * 128),
    ])))

    assert result["blocked"][0]["reasons"] == ["contested", "incommensurable"]


def test_the_walk_carries_deduplicated_sorted_history():
    result = invoke(capture(corpus(records=[
        observation(REF_A),
        observation(REF_B, supersedes=(REF_A,)),
        observation(REF_C, supersedes=(REF_A, REF_B)),
    ])))

    assert result == {
        "active": [member(REF_C, history=[
            {"ref": REF_A, "outcome": {"finding": "found", "digest": "sha256:" + "1" * 64}},
            {"ref": REF_B, "outcome": {"finding": "found", "digest": "sha256:" + "1" * 64}},
        ])],
        "blocked": [],
    }


def test_a_dangling_predecessor_keeps_the_record_as_a_head_with_an_unseen_tail():
    result = invoke(capture(corpus(records=[observation(REF_A, supersedes=("f" * 64,))])))

    assert result == {"active": [member(REF_A)], "blocked": []}


def test_a_cross_location_predecessor_refuses_the_whole_projection():
    value = capture(corpus(records=[
        observation(REF_A, supersedes=(REF_B,)),
        observation(REF_B, location=OTHER_LOCATION),
    ]))

    with pytest.raises(ValueError, match=f"^supersession crosses locations at {LOCATION}$"):
        invoke(value)


def test_qualification_matched_by_derived_path_and_token():
    result = invoke(capture(corpus(records=[observation(REF_A)], chain=matched_chain())))

    assert result == {"active": [member(REF_A)], "blocked": []}


def test_an_intent_cannot_qualify_against_another_corpus_record():
    intent_corpus = corpus(chain=matched_chain(), corpus_id="corpus-a")
    record_corpus = corpus(records=[observation(REF_A)], corpus_id="corpus-b")

    assert invoke(capture(intent_corpus, record_corpus)) == {
        "active": [],
        "blocked": [{"location": LOCATION, "reasons": ["unsettled"], "heads": [member(REF_A)]}],
    }


def test_an_identical_record_in_two_corpora_is_one_active_head():
    record = observation(REF_A)

    assert invoke(capture(
        corpus(records=[record], corpus_id="corpus-a"),
        corpus(records=[deepcopy(record)], corpus_id="corpus-b"),
    )) == {"active": [member(REF_A)], "blocked": []}


@pytest.mark.parametrize(
    "changed",
    [
        observation(REF_A, location=OTHER_LOCATION),
        observation(REF_A, observed_at="2026-01-02T00:00:00Z"),
    ],
)
def test_the_same_reference_with_different_canonical_content_refuses(changed):
    with pytest.raises(ValueError, match=f"^holdings observation reference collision at {REF_A}$"):
        invoke(capture(
            corpus(records=[observation(REF_A)], corpus_id="corpus-a"),
            corpus(records=[changed], corpus_id="corpus-b"),
        ))


@pytest.mark.parametrize(
    "records, final",
    [
        ([observation(REF_A, location=OTHER_LOCATION)], [file_row(f"holdings-observation/{REF_A}.md")]),
        ([observation(REF_A, token="wrong-token")], [file_row(f"holdings-observation/{REF_A}.md")]),
        ([], [["deleted", [["kind", "absent"]]]]),
        ([], [["directory", [["kind", "directory"]]]]),
        ([], [["outside.md", [["kind", "file"]]]]),
    ],
)
def test_wrong_location_wrong_token_and_no_observation_fail_qualification(records, final):
    chain = [intent("1" * 64), registration("2" * 64, "1" * 64, final=final), settlement("3" * 64, "2" * 64)]

    assert invoke(capture(corpus(records=records, chain=chain)))["blocked"][0]["reasons"] == ["unsettled"]


def test_a_missing_record_at_a_holdings_layout_row_is_unresolved():
    registration_value = {"settlement": "committed", "final": [file_row(f"holdings-observation/{REF_A}.md")]}
    assert qualify_intent({"location": LOCATION, "event_token": "token"}, [registration_value], {}) == "unresolved"


@pytest.mark.parametrize("path", [
    f"holdings-observation/x/{REF_A}.md",
    "holdings-observation/readme.md",
    f"holdings-observation/{REF_A.upper()}.md",
    f"holdings-observation/{'a' * 63}.md",
])
def test_the_layout_grammar_is_exact(path):
    registration_value = {"settlement": "committed", "final": [file_row(path)]}
    assert qualify_intent({"location": LOCATION, "event_token": "token"}, [registration_value], {}) == "unmatched"


def test_qualify_intent_never_collapses_unresolved():
    intent_value = {"location": LOCATION, "event_token": "token"}
    deriving = {f"holdings-observation/{REF_A}.md": {"location": LOCATION, "event_token": "token"}}
    assert qualify_intent(intent_value, [{"settlement": None, "final": []}], {}) == "unresolved"
    assert qualify_intent(
        intent_value,
        [{"settlement": "committed", "final": [file_row(f"holdings-observation/{REF_A}.md")]}],
        {},
    ) == "unresolved"
    assert qualify_intent(intent_value, [{"settlement": "rolled-back", "final": object()}], {}) == "unmatched"
    assert qualify_intent(
        intent_value,
        [{"settlement": "committed", "final": [file_row("outside.md")]}],
        {},
    ) == "unmatched"
    assert qualify_intent(
        intent_value,
        [{"settlement": "committed", "final": [file_row(f"holdings-observation/{REF_A}.md")]}],
        deriving,
    ) == "matched"


def test_a_settlement_less_registration_is_an_inspected_well_formed_chain(tmp_path):
    root = tmp_path / "pending-chain"
    root.mkdir()
    chain = Chain(root)
    chain.genesis()
    intent_ref = chain.intent(b"holdings intent")
    registration_ref = chain.registration("tx-pending", (), (), fulfills=intent_ref)

    view = inspected(root)

    assert isinstance(view, logmodel.WellFormedView)
    assert view.pending == (("tx-pending", registration_ref),)
    assert any(
        isinstance(entry, logmodel.RegisteredEntryView) and entry.fulfills == intent_ref
        for entry in view.entries
    )


def test_a_rolled_back_registration_is_resolved_with_rows_unconsulted():
    assert qualify_intent(
        {"location": LOCATION, "event_token": "token"},
        [{"settlement": "rolled-back", "final": object()}],
        {},
    ) == "unmatched"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.pop("location"),
        lambda value: value.__setitem__("location", "not-an-object"),
        lambda value: value["location"].__setitem__("store_id", "A" * 32),
        lambda value: value["location"].__setitem__("relative_path", "../escape"),
        lambda value: value["location"].__setitem__("type", "url"),
        lambda value: value.pop("kind"),
        lambda value: value.__setitem__("kind", "inspect"),
        lambda value: value.pop("event_token"),
        lambda value: value.__setitem__("event_token", ""),
        lambda value: value.pop("actor"),
        lambda value: value.__setitem__("extra", True),
        lambda value: value["location"].__setitem__("extra", True),
    ],
)
def test_a_malformed_holdings_intent_refuses_the_whole_reduction(mutate):
    payload = json.loads(bytes.fromhex(intent("1" * 64)["entry"]["payload"]).decode())
    mutate(payload)
    value = capture(corpus(records=[observation(REF_A)], chain=[intent("1" * 64, payload=payload)]))

    with pytest.raises(ValueError, match="^malformed holdings intent at " + "1" * 64 + "$"):
        invoke(value)


@pytest.mark.parametrize(
    "payload",
    [
        "not-hex",
        b"\xff".hex(),
        b"not-json".hex(),
        json.dumps(["not", "an", "object"]).encode().hex(),
        json.dumps({"domain": "science.some-other-intent.v1"}).encode().hex(),
        json.dumps({"actor": "no-domain"}).encode().hex(),
    ],
)
def test_payloads_that_do_not_select_the_holdings_domain_are_ignored(payload):
    row = {"digest": "1" * 64, "entry": {"kind": "intent", "payload": payload}}

    assert invoke(capture(corpus(chain=[row]))) == {"active": [], "blocked": []}


def test_the_bundle_concatenates_the_helper_source():
    qualify = resources.files("beliefs.holdings").joinpath("qualify.py").read_bytes()
    holdings = resources.files("beliefs.holdings.rules_v1").joinpath("holdings.py").read_bytes()

    assert holdings_rule_bundle().implementation == qualify + b"\n\n" + holdings


def test_fixture_records_are_exact_production_canonical_projections():
    for _name, content in holdings_rule_bundle().fixtures:
        supplied = yaml.safe_load(content)["input"]
        for corpus_value in supplied["corpora"]:
            state = corpus_value["corpus_state"]
            assert len(state) == 64 and all(character in "0123456789abcdef" for character in state)
            for record in corpus_value["records"]:
                node = Node.model_validate(json.loads(record["canonical"]))
                rebuilt = stored.holdings_observation_node(stored.holdings_observation_value(node)).model_copy(
                    update={"uid": node.uid}
                )
                assert record == {"uid": node.uid, "canonical": to_canonical_json(rebuilt)}


def test_the_outputs_are_byte_deterministic():
    first = capture(
        corpus(records=[observation(REF_B), observation(REF_A)], corpus_id="corpus-b"),
        corpus(records=[observation(REF_C, location=OTHER_LOCATION)], corpus_id="corpus-a"),
    )
    shuffled = capture(*reversed(deepcopy(first["corpora"])))
    for item in shuffled["corpora"]:
        item["records"].reverse()

    assert v1.encode(invoke(first)) == v1.encode(invoke(first)) == v1.encode(invoke(shuffled))
