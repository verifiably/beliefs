from __future__ import annotations

from copy import deepcopy

import pytest
from authority import FULL
from nodes.core.store import Store
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import MalformedRecord, WriteRefused
from beliefs.holdings.records import (
    HOLDINGS_OBSERVATION_DOMAIN,
    Found,
    StoreLocator,
    holdings_observation,
)
from beliefs.world import epoch


def observation(**changes: object):
    fields: dict[str, object] = {
        "location": StoreLocator("a" * 32, "payload/data.csv"),
        "outcome": Found("sha256:" + "ab" * 32),
        "observer": "observer-1",
        "instrument": "instrument-1",
        "event_token": "event-1",
        "observed_at": "2026-08-24T12:00:00Z",
    }
    fields.update(changes)
    return holdings_observation(**fields)  # type: ignore[arg-type]


def test_the_kind_is_governed():
    assert stored.SEMANTIC_DOMAINS["holdings-observation"] == HOLDINGS_OBSERVATION_DOMAIN
    assert stored.COVERED_FACETS["holdings-observation"] == (stored.HOLDINGS_OBSERVATION_FACET,)


def test_node_round_trips_the_value():
    value = observation()

    assert stored.holdings_observation_value(stored.holdings_observation_node(value)) == value


def test_the_node_is_stamped_and_recompute_agrees():
    node = stored.holdings_observation_node(observation())

    assert not stored.semantic_hash_missing(node)
    assert stored.recompute_semantic_hash(node) == stored.stored_semantic_hash(node)


def test_the_slug_is_the_facet_identity():
    value = observation()

    assert stored.holdings_observation_node(value).id == f"holdings-observation:{value.identity()}"


def test_the_stored_path_is_kind_first(tmp_path):
    value = observation()
    node = stored.holdings_observation_node(value)

    assert Store(tmp_path).path_for(node.id).relative_to(tmp_path).as_posix() == f"holdings-observation/{value.identity()}.md"


def test_direct_authoring_through_the_writer_is_refused(tmp_path):
    with pytest.raises(WriteRefused, match="a holdings observation is minted only by the acts boundary"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE).add(stored.holdings_observation_node(observation()))


def test_the_kind_joins_no_epoch_map():
    assert "holdings-observation" not in epoch.ENUMERATED_SOURCE_KINDS
    assert "holdings-observation" not in epoch.RECEIPT_KINDS
    assert epoch.ENUMERATED_SOURCE_KINDS == (
        "coreference-attestation",
        "instrument-certification",
        "retraction",
        "run",
    )
    assert epoch.EPOCH_MEMBERS == (
        "address-map.yaml",
        "producers-map.yaml",
        "retraction-discovery-map.yaml",
        "coreference-map.yaml",
        "producer-snapshot.yaml",
        "producer-receipt.yaml",
        "retraction-receipt.yaml",
        "certification-receipt.yaml",
        "coreference-receipt.yaml",
        "anchors.yaml",
        "coverage.yaml",
    )


def test_a_decoded_malformed_facet_refuses():
    node = stored.holdings_observation_node(observation())
    facets = deepcopy(node.facets)
    del facets[stored.HOLDINGS_OBSERVATION_FACET]["event_token"]
    malformed = node.model_copy(update={"facets": facets})

    with pytest.raises(MalformedRecord):
        stored.holdings_observation_value(malformed)
