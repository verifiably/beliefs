from dataclasses import replace
from typing import Any, cast

import pytest
from atoms.core.errors import SpecValidationError
from atoms.core.paths import require_rel_path

from beliefs.errors import MalformedRecord
from beliefs.holdings.records import (
    Absent,
    Found,
    HoldingsObservation,
    StoreLocator,
    UrlLocator,
    holdings_observation,
    require_store_relative_path,
    url_locator,
)

STORE_ID = "a" * 32
DIGEST = "sha256:" + "ab" * 32
OTHER_DIGEST = "sha256:" + "cd" * 32


def observation(**changes: object):
    fields: dict[str, object] = {
        "location": StoreLocator(STORE_ID, "payload/data.csv"),
        "outcome": Found(DIGEST),
        "expected": None,
        "observer": "observer-1",
        "instrument": "instrument-1",
        "event_token": "event-1",
        "observed_at": "2026-08-24T12:00:00Z",
    }
    fields.update(changes)
    return holdings_observation(**fields)  # type: ignore[arg-type]


def test_store_locator_accepts_a_32_hex_identity_and_grammar_valid_path():
    locator = StoreLocator(STORE_ID, "a/b-c_1.txt")
    assert locator.canonical() == f"store:{STORE_ID}:a/b-c_1.txt"


def test_store_locator_refuses_a_non_32_hex_store_identity():
    with pytest.raises(MalformedRecord):
        StoreLocator("A" * 32, "payload")


@pytest.mark.parametrize("path", ["a/../b", "a//b", "./a", "a/", "/a", "", "a\x00b"])
def test_store_locator_refuses_rather_than_normalizes_the_path(path: str):
    with pytest.raises(MalformedRecord):
        StoreLocator(STORE_ID, path)


@pytest.mark.parametrize(
    "path",
    ["a", "a/b", "a-b_c.1", "unicode/é", " space ", "a/.hidden", ".#~reserved", "a/.#~reserved", "", "/a", "a/", "a//b", "./a", "a/./b", "../a", "a/../b", "a\x00b", ".#~", "a/.#~", "a/.#~b/c"],
)
def test_the_path_grammar_agrees_with_the_engine(path: str):
    def accepted(requirement) -> bool:
        try:
            requirement()
        except (MalformedRecord, SpecValidationError):
            return False
        return True

    assert accepted(lambda: require_store_relative_path(path)) == accepted(lambda: require_rel_path("path", path))


CANONICAL = [
    # (spelling, canonical): one row per profile clause of decision 1
    ("HTTPS://Example.ORG/data", "https://example.org/data"),
    ("https://example.org:443/data", "https://example.org/data"),
    ("http://example.org:80/data", "http://example.org/data"),
    ("https://example.org:8443/data", "https://example.org:8443/data"),
    ("https://example.org", "https://example.org/"),
    ("https://example.org/a/./b/../c", "https://example.org/a/c"),
    ("https://example.org/a/%7e/%2f/%41", "https://example.org/a/~/%2F/A"),
    ("https://example.org/p?b=%2f&a", "https://example.org/p?b=%2f&a"),
    ("https://example.org/p?", "https://example.org/p?"),
    ("https://example.org/p?B=1", "https://example.org/p?B=1"),
    ("https://example.org/a/.", "https://example.org/a/"),
    ("https://example.org/a/b/..", "https://example.org/a/"),
    ("https://example.org/a/b/", "https://example.org/a/b/"),
    ("https://example.org/..", "https://example.org/"),
    ("https://example.org/a/..", "https://example.org/"),
    ("https://example.org/a//.", "https://example.org/a//"),
    ("https://example.org/a///..", "https://example.org/a//"),
    ("https://example.org/a//..", "https://example.org/a/"),
    ("https://[2001:DB8::1]:8443/x", "https://[2001:db8::1]:8443/x"),
    ("https://[2001:db8::1]:443/x", "https://[2001:db8::1]/x"),
]


@pytest.mark.parametrize("spelling,canonical", CANONICAL)
def test_url_locator_canonicalizes_under_the_banked_profile(spelling: str, canonical: str):
    locator = url_locator(spelling)
    assert locator.url == canonical
    assert locator.canonical() == "url:" + canonical
    assert url_locator(canonical) == locator


@pytest.mark.parametrize(
    "spelling",
    [
        "https://example.org/p#frag",
        "https://example.org/p#",
        "https://user@example.org/p",
        "https://user:pw@example.org/p",
        "ftp://example.org/p",
        "https:///p",
        "https://exämple.org/p",
        "https://example.org/a b",
        "https://example.org/a\tb",
        "https://example.org/%zz",
        "https://example.org/%4",
        "https://example.org:0/p",
        "https://[2001:db8::1/p",
        "https://[example.org]/p",
        "",
        "example.org/p",
    ],
)
def test_url_locator_refuses_rather_than_repairs(spelling: str):
    with pytest.raises(MalformedRecord):
        url_locator(spelling)


def test_a_trailing_dot_segment_names_the_directory_and_not_its_parent():
    assert url_locator("https://example.org/a/.") == url_locator("https://example.org/a/")
    assert url_locator("https://example.org/a/.") != url_locator("https://example.org/a")
    assert url_locator("https://example.org/a/b/..") != url_locator("https://example.org/a")


def test_a_url_locator_is_constructed_canonical_or_refused():
    assert UrlLocator("https://example.org/") == url_locator("https://EXAMPLE.org")
    with pytest.raises(MalformedRecord):
        UrlLocator("https://EXAMPLE.org/")


def test_a_url_observation_carries_the_url_arm_in_its_facet_and_identity():
    record = observation(location=url_locator("https://example.org/data"))
    assert record.facet()["location"] == {"type": "url", "url": "https://example.org/data"}
    other = observation(location=url_locator("https://example.org/other"))
    assert record.identity() != other.identity()


def test_a_url_observation_never_spells_absent():
    with pytest.raises(MalformedRecord):
        observation(location=url_locator("https://example.org/data"), outcome=Absent())


def test_supersession_never_crosses_the_url_and_store_arms():
    store = observation()
    with pytest.raises(MalformedRecord):
        observation(location=url_locator("https://example.org/data"), supersedes=(store,))


@pytest.mark.parametrize("digest", ["sha256:" + "AB" * 32, "sha256", "ab" * 32, "SHA256:" + "ab" * 32])
def test_found_requires_an_algorithm_qualified_canonical_digest(digest: str):
    with pytest.raises(MalformedRecord):
        Found(digest)


def test_sha256_width_is_exact_and_unknown_algorithms_are_generic():
    with pytest.raises(MalformedRecord):
        Found("sha256:" + "a" * 63)
    assert Found("sha512:" + "a" * 40).digest == "sha512:" + "a" * 40


def test_expected_must_share_the_found_algorithm():
    with pytest.raises(MalformedRecord):
        observation(expected="sha512:" + "a" * 40)
    assert observation(outcome=Absent(), expected="sha512:" + "a" * 40).expected == "sha512:" + "a" * 40


@pytest.mark.parametrize("observed_at", ["2026-08-24T12:00:00+00:00", "2026-08-24T12:00:00.000Z", "2026-13-40T12:00:00Z"])
def test_observed_at_is_the_one_canonical_utc_encoding(observed_at: str):
    assert observation().observed_at == "2026-08-24T12:00:00Z"
    with pytest.raises(MalformedRecord):
        observation(observed_at=observed_at)


def test_supersedes_predecessors_must_share_the_canonical_location():
    predecessor = observation(location=StoreLocator(STORE_ID, "other"))
    with pytest.raises(MalformedRecord):
        observation(supersedes=(predecessor,))


def test_supersedes_references_are_deduplicated_and_sorted_by_bytes():
    first = observation(event_token="first")
    second = observation(event_token="second")
    record = observation(event_token="third", supersedes=(second, first, first))
    assert record.supersedes == tuple(sorted({first.identity(), second.identity()}))


def test_two_identical_findings_differ_by_event_token_alone():
    first = observation(event_token="first")
    second = observation(event_token="second")
    assert first.identity() != second.identity()
    assert first.identity() == observation(event_token="first").identity()


def test_every_field_participates_in_the_identity():
    base = observation()
    predecessor = observation(event_token="predecessor")
    changed = (
        observation(location=StoreLocator(STORE_ID, "other")),
        observation(outcome=Absent()),
        observation(expected=OTHER_DIGEST),
        observation(observer="other"),
        observation(instrument="other"),
        observation(event_token="other"),
        observation(observed_at="2026-08-24T12:00:01Z"),
        observation(supersedes=(predecessor,)),
    )
    assert all(record.identity() != base.identity() for record in changed)


def test_absent_expected_is_omitted_from_the_facet_never_null():
    assert "expected" not in observation(outcome=Absent()).facet()


def test_the_found_facet_is_exact():
    assert observation(expected=OTHER_DIGEST).facet() == {
        "kind": "holdings-observation",
        "location": {"type": "store", "store_id": STORE_ID, "relative_path": "payload/data.csv"},
        "outcome": {"finding": "found", "digest": DIGEST},
        "expected": OTHER_DIGEST,
        "observer": "observer-1",
        "instrument": "instrument-1",
        "event_token": "event-1",
        "observed_at": "2026-08-24T12:00:00Z",
        "supersedes": [],
    }


def test_the_absent_facet_is_exact_and_omits_an_unset_expected():
    assert observation(outcome=Absent()).facet() == {
        "kind": "holdings-observation",
        "location": {"type": "store", "store_id": STORE_ID, "relative_path": "payload/data.csv"},
        "outcome": {"finding": "absent"},
        "observer": "observer-1",
        "instrument": "instrument-1",
        "event_token": "event-1",
        "observed_at": "2026-08-24T12:00:00Z",
        "supersedes": [],
    }


@pytest.mark.parametrize("field", ["observer", "instrument", "event_token"])
def test_identity_bearing_strings_refuse_lone_surrogates_at_construction(field: str):
    with pytest.raises(MalformedRecord):
        observation(**{field: "\ud800"})


@pytest.mark.parametrize(
    "changes",
    [
        {"location": None},
        {"outcome": None},
        {"expected": True},
        {"observer": True},
        {"instrument": True},
        {"event_token": True},
        {"observed_at": True},
        {"supersedes": []},
        {"supersedes": ("z" * 64,)},
        {"supersedes": ("a" * 64, "a" * 64)},
        {"supersedes": ("b" * 64, "a" * 64)},
    ],
)
def test_direct_observation_construction_refuses_malformed_fields(changes: dict[str, object]):
    record = observation()
    with pytest.raises(MalformedRecord):
        replace(cast(HoldingsObservation, record), **cast(Any, changes))
