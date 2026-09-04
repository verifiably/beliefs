"""E1 at value level, E4 and E5 (design §3, §7)."""
from __future__ import annotations

import pytest

from beliefs.coordination import COORDINATION_KINDS
from beliefs.errors import ActorMismatch, PermitExceeded, PermitFact, PermitSummary, WriteRefused
from beliefs.permit import (
    ACT_FAMILIES,
    COMMAND_REACHABLE_FAMILIES,
    KIND_ACTS,
    Authority,
    WritePermit,
    require_actor,
)
from beliefs.stored import WORLD_KINDS


class TestE4KindActsIsClosedAndComplete:
    def test_the_key_set_is_exactly_the_world_and_coordination_kinds(self):
        assert set(KIND_ACTS) == set(WORLD_KINDS) | set(COORDINATION_KINDS)

    def test_every_route_is_an_act_family(self):
        for kind, routes in KIND_ACTS.items():
            assert routes and routes <= ACT_FAMILIES, kind

    def test_the_routes_are_the_banked_ones(self):
        assert KIND_ACTS["run"] == {"run", "corpus-write"}
        assert KIND_ACTS["dataset"] == {"corpus-write"}
        assert KIND_ACTS["act-report"] == {"corpus-write", "run"}
        assert KIND_ACTS["holdings-observation"] == {"holdings"}
        for kind in COORDINATION_KINDS:
            assert KIND_ACTS[kind] == {"corpus-write"}

    def test_the_mapping_is_read_only(self):
        with pytest.raises(TypeError):
            KIND_ACTS["proposition"] = frozenset()  # type: ignore[index]

    def test_the_families_are_the_six_and_three_are_command_reachable(self):
        assert ACT_FAMILIES == {"corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"}
        assert COMMAND_REACHABLE_FAMILIES == {"corpus-write", "run", "holdings"}


class TestWritePermitConstruction:
    def test_full_holds_every_kind_and_family_and_the_ungoverned_kinds(self):
        full = WritePermit.full()
        assert full.kinds == frozenset(KIND_ACTS)
        assert full.act_families == ACT_FAMILIES
        assert full.ungoverned is True
        assert WritePermit(frozenset(), frozenset()).ungoverned is False

    def test_an_unknown_kind_or_family_is_refused(self):
        with pytest.raises(ValueError, match="kind"):
            WritePermit(frozenset({"unicorn"}), frozenset())
        with pytest.raises(ValueError, match="family"):
            WritePermit(frozenset(), frozenset({"publish"}))

    def test_only_exact_frozensets_of_strings_construct(self):
        with pytest.raises(TypeError):
            WritePermit({"proposition"}, frozenset())  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            WritePermit(frozenset({1}), frozenset())  # type: ignore[arg-type]

    def test_summary_is_sorted_plain_data(self):
        permit = WritePermit(frozenset({"source", "proposition"}), frozenset({"run", "corpus-write"}))
        assert permit.summary() == PermitSummary(("proposition", "source"), ("corpus-write", "run"), False)


class TestRequireActor:
    def test_an_exact_encodable_string_passes(self):
        assert require_actor("alice") == "alice"

    def test_non_strings_and_empty_strings_refuse(self):
        with pytest.raises(TypeError):
            require_actor(b"alice")
        with pytest.raises(ValueError):
            require_actor("")


class TestE1AuthorityRequire:
    def test_a_missing_family_is_refused_on_the_family_before_any_kind(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        with pytest.raises(PermitExceeded) as caught:
            authority.require("run", ("proposition",))
        assert caught.value.requirement == PermitFact("family", "run")
        assert caught.value.capability == PermitSummary(("proposition",), ("corpus-write",), False)
        assert str(caught.value).startswith("permit exceeded: family run is not permitted")

    def test_the_first_missing_kind_in_the_callers_order_is_named(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        with pytest.raises(PermitExceeded) as caught:
            authority.require("corpus-write", ("proposition", "source", "dataset"))
        assert caught.value.requirement == PermitFact("kind", "source")

    def test_an_exact_requirement_passes_and_returns_nothing(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        assert authority.require("corpus-write", ("proposition",)) is None
        assert authority.require("corpus-write") is None

    def test_an_unknown_family_is_a_caller_error_not_a_refusal(self):
        with pytest.raises(ValueError):
            Authority(WritePermit.full(), "a").require("publish")

    def test_an_ungoverned_kind_needs_the_flag_and_the_corpus_write_family(self):
        governed_only = Authority(WritePermit(frozenset(), frozenset({"corpus-write", "run"})), "a")
        with pytest.raises(PermitExceeded) as caught:
            governed_only.require("corpus-write", ("memo",))
        assert caught.value.requirement == PermitFact("kind", "memo")
        full = Authority(WritePermit.full(), "a")
        assert full.require("corpus-write", ("memo",)) is None
        with pytest.raises(PermitExceeded) as caught:
            full.require("run", ("memo",))
        assert caught.value.requirement == PermitFact("kind", "memo")

    def test_permit_exceeded_is_a_write_refusal_and_actor_mismatch_too(self):
        assert issubclass(PermitExceeded, WriteRefused)
        assert issubclass(ActorMismatch, WriteRefused)

    def test_authority_fixes_the_actor_by_the_one_rule(self):
        with pytest.raises(TypeError):
            Authority(WritePermit.full(), 7)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            Authority(WritePermit.full(), "")
        with pytest.raises(TypeError):
            Authority("full", "a")  # type: ignore[arg-type]
