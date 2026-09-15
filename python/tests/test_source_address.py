"""Slice 2b §3: the source basis projection — normalization, precedence, address."""

from __future__ import annotations

from itertools import combinations
from types import MappingProxyType
from typing import Any, cast

import pytest
from nodes.core.node import Node

from beliefs import source, stored
from beliefs.errors import BasisMissing, HistoryDisagreement, IdentifierMalformed, MalformedRecord
from beliefs.identity import v1

CANONICAL_DOI = "10.1234/abc.def"


class TestNormalizeDoi:
    @pytest.mark.parametrize("spelling", ["10.1234/abc.DEF", "  10.1234/abc.def  ", "doi:10.1234/abc.def", "DOI:10.1234/ABC.DEF", "https://doi.org/10.1234/abc.def", "http://dx.doi.org/10.1234/abc.def", "HTTPS://DOI.ORG/10.1234/abc.def"])
    def test_every_spelling_folds_to_one_canonical_form(self, spelling):
        assert source.normalize("doi", spelling) == CANONICAL_DOI

    def test_nfc_is_applied(self):
        assert source.normalize("doi", "10.1234/café") == "10.1234/café"

    @pytest.mark.parametrize("bad", ["10.1/abc", "11.1234/abc", "10.1234/", "10.1234", "10.1234/a b"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("doi", bad)
        assert caught.value.reason == "malformed"


class TestNormalizePmid:
    @pytest.mark.parametrize("spelling", ["12345", " 12345 ", "pmid:12345", "PMID:12345"])
    def test_folds(self, spelling):
        assert source.normalize("pmid", spelling) == "12345"

    @pytest.mark.parametrize("bad", ["0", "012345", "12a45", "-5"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("pmid", bad)
        assert caught.value.reason == "malformed"


class TestNormalizeIsbn:
    def test_isbn13_with_hyphens_and_prefix(self):
        assert source.normalize("isbn", "isbn: 978-0-306-40615-7") == "9780306406157"

    def test_isbn10_is_converted_to_isbn13(self):
        assert source.normalize("isbn", "0-306-40615-2") == "9780306406157"

    def test_isbn10_with_x_check_digit(self):
        assert source.normalize("isbn", "0-8044-2957-X") == "9780804429573"

    def test_isbn13_with_979_prefix(self):
        assert source.normalize("isbn", "979-0-306-40615-6") == "9790306406156"

    @pytest.mark.parametrize("bad", ["978-0-306-40615-8", "0-306-40615-3", "0000000000000", "1234567890123", "12345"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("isbn", bad)
        assert caught.value.reason == "malformed"


class TestNormalizeAccession:
    @pytest.mark.parametrize("spelling", ["gse12345", " GSE12345 ", "nc_000913.3"])
    def test_folds(self, spelling):
        assert source.normalize("accession", spelling) == spelling.strip().upper()

    def test_versioned_and_unversioned_stay_distinct(self):
        assert source.normalize("accession", "NC_000913.3") != source.normalize("accession", "NC_000913")

    @pytest.mark.parametrize("bad", ["12345", "GSE 123", "gse-123", "_GSE"])
    def test_malformed(self, bad):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("accession", bad)
        assert caught.value.reason == "malformed"


class TestRefusalOrder:
    def test_not_a_string_precedes_every_value_rule(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize("doi", 5)
        assert caught.value.reason == "not-a-string"

    @pytest.mark.parametrize("scheme,value", [("doi", ""), ("doi", "   "), ("doi", "doi:"), ("pmid", "PMID:"), ("isbn", "isbn:--"), ("accession", " ")])
    def test_empty_after_trim_and_prefix_strip(self, scheme, value):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalize(scheme, value)
        assert caught.value.reason == "empty"

    def test_unknown_scheme_wins_over_its_own_value(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"unknown": 1})
        assert (caught.value.reason, caught.value.scheme) == ("unknown-scheme", "unknown")

    def test_non_string_scheme_is_a_named_unknown_scheme_refusal(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"pmid": "1", 1: "x"})
        assert (caught.value.reason, caught.value.scheme) == ("unknown-scheme", 1)

    def test_sorted_key_order_first_refusal_wins(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"pmid": 5, "doi": ""})
        assert (caught.value.reason, caught.value.scheme) == ("empty", "doi")

    def test_every_entry_is_validated_before_selection(self):
        with pytest.raises(IdentifierMalformed) as caught:
            source.normalized_identifiers({"doi": CANONICAL_DOI, "pmid": "0"})
        assert (caught.value.reason, caught.value.scheme) == ("malformed", "pmid")

    def test_one_tuple_in_precedence_order(self):
        assert source.SCHEMES == ("doi", "pmid", "isbn", "accession")
        assert stored.ACCEPTED_EXTERNAL_IDENTIFIERS is source.SCHEMES
        assert set(source._RULES) == set(source.SCHEMES)


class TestBasisAndAddress:
    def test_precedence_over_every_non_empty_subset(self):
        full = {"doi": CANONICAL_DOI, "pmid": "1", "isbn": "9780306406157", "accession": "GSE1"}
        precedence = ("doi", "pmid", "isbn", "accession")
        for size in range(1, 5):
            for schemes in combinations(precedence, size):
                subset = {k: full[k] for k in schemes}
                expected = min(schemes, key=precedence.index)
                assert source.basis(subset) == (expected, full[expected])

    def test_no_basis_is_none(self):
        assert source.basis({}) is None
        assert source.source_address({}) is None

    def test_the_address_is_the_domain_digest_over_scheme_and_value(self):
        expected = v1.digest(source.SOURCE_ADDRESS_DOMAIN, {"scheme": "doi", "value": CANONICAL_DOI})
        assert source.source_address({"doi": CANONICAL_DOI, "pmid": "1"}) == f"source:{expected}"

    def test_pinned_digest(self):
        assert source.source_address({"pmid": "12345"}) == "source:8e2aa77202899912130944e03f698206f93ec6faaf4d8c1e6847b9eec5e65db9"
        assert source.SOURCE_ADDRESS_DOMAIN == "science.source-address.v1"

    def test_two_records_with_different_selected_bases_are_two_addresses(self):
        assert source.source_address({"pmid": "1"}) != source.source_address({"doi": CANONICAL_DOI, "pmid": "1"})


class TestTheBuilder:
    def test_it_stores_the_canonical_form_and_derives_the_id(self):
        node = stored.source_node(
            title="A paper",
            identifiers={"doi": "https://doi.org/10.1234/ABC.def", "pmid": "pmid:7"},
        )
        assert node.facets[stored.SOURCE_FACET] == {
            "identifiers": {"doi": CANONICAL_DOI, "pmid": "7"}
        }
        assert (
            node.id
            == source.source_address({"doi": CANONICAL_DOI})
            == stored.source_address_of(node)
        )
        assert stored.IDENTIFIER_CORRECTION_FACET not in node.facets

    def test_two_spellings_are_one_facet_one_stamp_one_address(self):
        one = stored.source_node(title="x", identifiers={"doi": "10.1234/ABC"})
        two = stored.source_node(title="y", identifiers={"doi": "doi:10.1234/abc"})
        assert one.id == two.id and one.facets == two.facets

    def test_an_empty_basis_refuses_at_the_builder(self):
        with pytest.raises(BasisMissing):
            stored.source_node(title="A paper", identifiers={})

    def test_an_unaccepted_scheme_refuses_at_the_builder(self):
        with pytest.raises(IdentifierMalformed) as caught:
            stored.source_node(title="A paper", identifiers={"url": "https://example.org"})
        assert caught.value.reason == "unknown-scheme"


def raw_source(identifiers, *, history=None, deprecated=(), node_id=None):
    """A hand-built source, stamped, at the derived address unless `node_id` overrides it."""
    facets: dict[str, Any] = {stored.SOURCE_FACET: {"identifiers": dict(identifiers)}}
    if history is not None:
        facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [dict(e) for e in history]}
    address = node_id or source.source_address(identifiers)
    assert address is not None
    node = Node(
        id=address,
        kind="source",
        title="paper",
        facets=facets,
        deprecated_ids=list(deprecated),
    )
    return stored.stamp_semantic_identity(node)


def entry(frm, to, *, actor="curator", grounds="checked the PDF", token="t1"):
    return {"from": dict(frm), "to": dict(to), "actor": actor, "grounds": grounds, "event_token": token}


def consolidation(frm, absorbed, *, actor="consolidator", grounds="one paper", token="c1"):
    """A consolidation entry (slice 6 §3.1): `from == to`, plus the absorbed chain."""
    return {
        "from": dict(frm),
        "to": dict(frm),
        "actor": actor,
        "grounds": grounds,
        "event_token": token,
        "absorbed": [dict(e) for e in absorbed],
    }


C = {"doi": "10.1234/xyz", "pmid": "1"}
ADDR_C = cast(str, source.source_address(C))


A = {"pmid": "1"}
B = {"doi": CANONICAL_DOI, "pmid": "1"}
ADDR_A = cast(str, source.source_address(A))
ADDR_B = cast(str, source.source_address(B))


class TestReaders:
    def test_source_basis_and_address_of(self):
        node = raw_source(B)
        assert stored.source_basis(node) == ("doi", CANONICAL_DOI)
        assert stored.source_address_of(node) == node.id == ADDR_B

    def test_no_history_reads_empty(self):
        assert stored.identifier_corrections(raw_source(A)) == ()

    def test_a_well_formed_history_reads_back(self):
        node = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        (correction,) = stored.identifier_corrections(node)
        assert correction.from_identifiers == A and correction.to_identifiers == B
        assert isinstance(correction.from_identifiers, MappingProxyType)
        assert isinstance(correction.to_identifiers, MappingProxyType)
        assert (correction.actor, correction.grounds, correction.event_token) == (
            "curator",
            "checked the PDF",
            "t1",
        )

    def test_held_addresses(self):
        assert stored.held_source_addresses(
            stored.identifier_corrections(raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A]))
        ) == {ADDR_A, ADDR_B}

    # --- slice 6 §3: the consolidation entry and the nested chain ---

    def test_a_consolidation_entry_reads_with_its_absorbed_chain(self):
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        node = raw_source(B, history=history, deprecated=sorted([ADDR_A, ADDR_C]))
        first, merged = stored.identifier_corrections(node)
        assert first.absorbed == ()
        assert merged.from_identifiers == B and merged.to_identifiers == B
        assert (merged.actor, merged.grounds, merged.event_token) == ("consolidator", "one paper", "c1")
        assert [c.event_token for c in merged.absorbed] == ["o1", "o2"]
        assert merged.absorbed[0].from_identifiers == A and merged.absorbed[1].to_identifiers == B
        assert stored.validate_source_history(node) == (first, merged)

    def test_a_nested_consolidation_entry_reads(self):
        inner = consolidation(B, [entry(A, B, token="o1")], token="c1")
        outer = consolidation(B, [entry(C, B, token="p1"), inner], token="c2")
        node = raw_source(B, history=[entry(A, B, token="t1"), outer], deprecated=sorted([ADDR_A, ADDR_C]))
        _, merged = stored.identifier_corrections(node)
        assert merged.absorbed[1].absorbed[0].event_token == "o1"

    def test_held_addresses_reach_into_absorbed_chains_once(self):
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        node = raw_source(B, history=history, deprecated=sorted([ADDR_A, ADDR_C]))
        assert stored.held_source_addresses(stored.identifier_corrections(node)) == {ADDR_A, ADDR_B, ADDR_C}

    @pytest.mark.parametrize(
        "deprecated",
        [sorted([ADDR_A]), sorted([ADDR_A, ADDR_C, "source:" + "f" * 64])],
        ids=["omits-an-absorbed-address", "adds-an-underived-address"],
    )
    def test_validate_source_history_holds_the_redirect_set_to_the_absorbed_chain(self, deprecated):
        history = [entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])]
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(raw_source(B, history=history, deprecated=deprecated))

    def test_an_identical_event_may_recur_across_chains(self):
        b = entry(A, B, token="b")
        history = [
            entry(A, B, token="a"),
            consolidation(B, [b], token="m1"),
            consolidation(B, [entry(A, B, token="c"), consolidation(B, [dict(b)], token="m2")], token="m3"),
        ]
        node = raw_source(B, history=history, deprecated=[ADDR_A])
        assert len(stored.identifier_corrections(node)) == 3

    @pytest.mark.parametrize(
        "history, match",
        [
            ([dict(entry(A, B, token="t1"), absorbed=[entry(B, A, token="o1")])], "changes nothing"),
            ([entry(A, B, token="t1"), consolidation(B, [])], "non-empty list"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry({"pmid": "9"}, B, token="o2")])], "continue"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1")])], "does not end at the entry"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="t1", grounds="other")])], "two different events"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o1")])], "repeats"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1", grounds="\udcff")])], "encodable"),
            ([entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1")], token="t1")], "repeats"),
        ],
        ids=["six-keys-unequal", "empty-absorbed", "absorbed-discontinuous", "absorbed-ends-elsewhere", "conflicting-reuse", "repeat-inside-absorbed", "unencodable-inside-absorbed", "entry-token-repeats-spine"],
    )
    def test_malformed_consolidation_shapes_refuse(self, history, match):
        node = raw_source(B, history=history, deprecated=[ADDR_A])
        with pytest.raises(MalformedRecord, match=match):
            stored.identifier_corrections(node)

    def test_validate_source_history_accepts_the_agreeing_redirect(self):
        node = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        assert len(stored.validate_source_history(node)) == 1
        assert stored.validate_source_history(raw_source(A)) == ()

    @pytest.mark.parametrize(
        "deprecated",
        [
            [],  # the retired address missing
            [ADDR_A, ADDR_A],  # a duplicate
            [ADDR_A, ADDR_B],  # the live address deprecated too
            [ADDR_A, "source:" + "f" * 64],  # a retired address the history does not derive
        ],
        ids=["missing", "duplicate", "live-and-deprecated", "underived"],
    )
    def test_validate_source_history_refuses_a_disagreeing_redirect(self, deprecated):
        node = raw_source(B, history=[entry(A, B)], deprecated=deprecated)
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(node)

    def test_an_unsorted_redirect_refuses(self):
        two = {"pmid": "2"}
        history = [entry(A, B, token="t1"), entry(B, two, token="t2")]
        node = raw_source(two, history=history, deprecated=sorted([ADDR_A, ADDR_B], reverse=True))
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(node)
        assert (
            len(
                stored.validate_source_history(
                    raw_source(two, history=history, deprecated=sorted([ADDR_A, ADDR_B]))
                )
            )
            == 2
        )

    def test_a_history_free_source_with_a_deprecated_id_refuses(self):
        with pytest.raises(MalformedRecord):
            stored.validate_source_history(raw_source(B, deprecated=[ADDR_A]))

    @pytest.mark.parametrize(
        "history",
        [
            [],  # empty entries
            [dict(entry(A, B), extra=1)],  # an extra key
            [dict(entry(A, B), absorbed=[entry(B, A, token="o1")])],  # six keys with from != to
            [{k: v for k, v in entry(A, B).items() if k != "grounds"}],  # a missing key
            [entry({}, B)],  # empty from
            [entry(A, {})],  # empty to
            [entry(A, {"doi": "10.1234/ABC.DEF", "pmid": "1"})],  # non-canonical value in a map
            [entry(A, {"url": "x"})],  # unknown scheme in a map
            [entry(A, B, actor="")],
            [entry(A, B, grounds="")],
            [entry(A, B, token="")],
            [entry(A, B, grounds="\udcff")],  # a lone surrogate is not canonically encodable
            [dict(entry(A, B), **{"from": None})],  # a null map: this reader's refusal, never NullRefused
            [entry(A, B, token="t"), entry(B, {"pmid": "2"}, token="t")],  # duplicate token
            [entry(A, B), entry({"pmid": "9"}, {"pmid": "2"}, token="t2")],  # continuity broken
        ],
    )
    def test_malformed_shapes_refuse(self, history):
        node = raw_source(
            B if history and history[-1]["to"] == B else {"pmid": "2"},
            history=history,
            deprecated=[ADDR_A],
        )
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)

    def test_from_equal_to_refuses_and_nothing_else_does(self):
        # The one fixture that violates only the from != to clause: continuity holds,
        # the entry ends at the current identifiers, and the redirect set is empty.
        node = raw_source(A, history=[entry(A, A)], deprecated=[])
        with pytest.raises(MalformedRecord, match="from and to are equal"):
            stored.identifier_corrections(node)

    def test_the_last_entry_must_end_at_the_current_identifiers(self):
        node = raw_source({"pmid": "7"}, history=[entry(A, B)], deprecated=[ADDR_A])
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)

    def test_the_facet_must_be_a_mapping_with_entries_only(self):
        node = raw_source(B)
        node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [entry(A, B)], "note": 1}
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(node)

    def test_a_mixed_key_identifier_map_is_a_malformed_record(self):
        mixed = entry(A, B)
        mixed["from"] = {"pmid": "1", 1: "x"}
        with pytest.raises(MalformedRecord):
            stored.identifier_corrections(raw_source(B, history=[mixed], deprecated=[ADDR_A]))


class TestReconcile:
    """Slice 6 §4: keep's chain is the spine; other's unheld tail is absorbed; idempotent."""

    A_B = entry(A, B, token="a")
    B_ = entry(A, B, token="b")
    E = entry(B, C, token="e1")
    E_BACK = entry(C, B, token="e2")

    def merge(self, keep, other, token="op"):
        return stored.reconcile_correction_histories(keep, other, actor="me", grounds="one paper", event_token=token)

    def test_equal_chains_are_the_identity(self):
        assert self.merge([self.A_B], [self.A_B]) == [self.A_B]
        assert self.merge([], []) == []

    def test_a_proper_prefix_fast_forwards_either_way(self):
        longer = [self.A_B, self.E, self.E_BACK]
        assert self.merge([self.A_B], longer) == longer
        assert self.merge(longer, [self.A_B]) == longer
        assert self.merge([], longer) == longer
        assert self.merge(longer, []) == longer

    def test_divergent_chains_absorb_the_tail_after_the_common_prefix(self):
        keep = [self.A_B, self.E, self.E_BACK]
        other = [self.A_B, entry(B, C, token="o1"), entry(C, B, token="o2")]
        merged = self.merge(keep, other)
        assert merged[:3] == keep
        assert merged[3] == {
            "from": B, "to": B, "actor": "me", "grounds": "one paper", "event_token": "op",
            "absorbed": other[1:],
        }

    def test_divergent_chains_with_no_common_prefix_absorb_all_of_other(self):
        merged = self.merge([self.A_B], [self.B_])
        assert merged == [self.A_B, {**consolidation(B, [self.B_], actor="me", grounds="one paper", token="op")}]

    def test_an_already_absorbed_chain_is_not_absorbed_again(self):
        once = self.merge([self.A_B], [self.B_])
        assert self.merge(once, [self.B_]) == once

    def test_a_chain_corrected_after_absorption_absorbs_only_the_new_tail(self):
        once = self.merge([self.A_B], [self.B_])
        other = [self.B_, entry(B, C, token="o1"), entry(C, B, token="o2")]
        merged = self.merge(once, other, token="op2")
        assert merged[:2] == once and merged[2]["absorbed"] == other[1:] and merged[2]["event_token"] == "op2"

    def test_the_diamond_absorbs_an_identical_event_twice(self):
        once = self.merge([self.A_B], [self.B_])
        other = [entry(A, B, token="c"), consolidation(B, [self.B_], token="m2")]
        merged = self.merge(once, other, token="op2")
        assert merged[2]["absorbed"] == other

    def test_conflicting_token_reuse_refuses(self):
        with pytest.raises(HistoryDisagreement, match="two different events"):
            self.merge([self.A_B], [entry(A, B, token="a", grounds="other grounds")])

    def test_held_events_interleaving_unheld_ones_refuse(self):
        once = self.merge([self.A_B], [self.B_])
        other = [entry(B, A, token="x"), self.B_, consolidation(B, [entry(A, B, token="z")], token="y")]
        with pytest.raises(HistoryDisagreement, match="interleave"):
            self.merge(once, other, token="op2")

    @pytest.mark.parametrize(
        "keep, other",
        [
            ([entry(A, B, token="a")], [entry(A, B, token="b")]),
            ([entry(A, B, token="a"), entry(B, C, token="e1"), entry(C, B, token="e2")], [entry(A, B, token="a"), entry(B, C, token="o1"), entry(C, B, token="o2")]),
            ([entry(A, B, token="a")], [entry(A, B, token="a"), entry(B, C, token="e1"), entry(C, B, token="e2")]),
        ],
        ids=["no-prefix", "common-prefix", "fast-forward"],
    )
    def test_reconciliation_is_idempotent(self, keep, other):
        once = self.merge(keep, other)
        assert self.merge(once, other, token="op2") == once

    def test_the_result_aliases_no_input(self):
        keep, other = [entry(A, B, token="a")], [entry(A, B, token="b")]
        merged = self.merge(keep, other)
        merged[1]["absorbed"][0]["grounds"] = "mutated"
        assert other[0]["grounds"] == "checked the PDF"
