"""The event domain of the event-level relation (spec §3): moments and placements
over fabricated well-formed views. Nothing here reads a root."""

from __future__ import annotations

import pytest
from test_world_log_audit import chain, digest, genesis_entry, registration, settlement

from beliefs.errors import EventUnknown
from beliefs.world import events, logmodel


def intent(label: str) -> logmodel.IntentEntryView:
    return logmodel.IntentEntryView(digest=digest(label), payload=b"{}")


GENESIS = genesis_entry(b"g", label="events-genesis")
INTENT = intent("events-intent")
REGISTRATION = registration(digest("events-reg"), "tx-1", (("a.md", None),), (("a.md", "s"),))
COMMITTED = settlement(digest("events-settled"), REGISTRATION.digest, "tx-1", committed=True)
OTHER_REGISTRATION = registration(digest("events-reg-2"), "tx-2", (("b.md", None),), (("b.md", "s"),))
ROLLED_BACK = settlement(digest("events-rolled"), OTHER_REGISTRATION.digest, "tx-2", committed=False)
PENDING = registration(digest("events-reg-3"), "tx-3", (("c.md", None),), (("c.md", "s"),))
VIEW = chain(GENESIS, INTENT, REGISTRATION, COMMITTED, OTHER_REGISTRATION, ROLLED_BACK, PENDING)


class TestMoment:
    def test_genesis_intent_and_committed_settlement_are_their_own_position(self):
        assert events.moment(VIEW, GENESIS.digest) == 0
        assert events.moment(VIEW, INTENT.digest) == 1
        assert events.moment(VIEW, COMMITTED.digest) == 3

    def test_a_registration_normalizes_to_its_committed_settlement(self):
        assert events.moment(VIEW, REGISTRATION.digest) == 3

    def test_a_rolled_back_settlement_and_its_registration_have_no_moment(self):
        assert events.moment(VIEW, ROLLED_BACK.digest) is None
        assert events.moment(VIEW, OTHER_REGISTRATION.digest) is None

    def test_a_pending_registration_has_no_moment(self):
        assert events.moment(VIEW, PENDING.digest) is None

    def test_an_absent_digest_refuses(self):
        with pytest.raises(EventUnknown):
            events.moment(VIEW, digest("not-an-entry"))

    def test_the_settlement_is_found_by_registration_digest_not_by_adjacency(self):
        # The committed settlement sits two entries after its registration here;
        # a lookup by "the next settlement" would find the rolled-back one.
        view = chain(GENESIS, REGISTRATION, OTHER_REGISTRATION, ROLLED_BACK, COMMITTED)
        assert events.moment(view, REGISTRATION.digest) == 4


class TestPlace:
    def test_a_reachable_head_under_the_live_genesis_places(self):
        placement = events.place(VIEW, genesis_digest=GENESIS.digest, head_digest=COMMITTED.digest)
        assert placement == events.Placement(head=3)

    def test_a_genesis_mismatch_places_nothing_even_with_a_reachable_head(self):
        assert events.place(VIEW, genesis_digest=digest("other-genesis"), head_digest=COMMITTED.digest) is None

    def test_an_unplaceable_head_places_nothing(self):
        assert events.place(VIEW, genesis_digest=GENESIS.digest, head_digest=digest("beyond-the-tip")) is None

    def test_contains_is_inclusive_at_the_head_and_excludes_is_its_negation(self):
        placement = events.Placement(head=3)
        assert events.contains(placement, 3) and events.contains(placement, 0)
        assert not events.contains(placement, 4)
        assert events.excludes(placement, 4) and not events.excludes(placement, 3)


def test_the_module_imports_no_engine_and_no_world_sibling():
    import ast
    from pathlib import Path

    source = Path(events.__file__).read_text(encoding="utf-8")
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imported <= {"__future__", "dataclasses", "typing", "beliefs.errors", "beliefs.world.logmodel"}
