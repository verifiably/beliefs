"""Slice 2b §3: the source basis projection — normalization, precedence, address."""

from __future__ import annotations

from itertools import combinations

import pytest

from beliefs import source
from beliefs.errors import IdentifierMalformed
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
        assert set(source._RULES) == set(source.SCHEMES)


class TestBasisAndAddress:
    def test_precedence_over_every_non_empty_subset(self):
        full = {"doi": CANONICAL_DOI, "pmid": "1", "isbn": "9780306406157", "accession": "GSE1"}
        for size in range(1, 5):
            for schemes in combinations(source.SCHEMES, size):
                subset = {k: full[k] for k in schemes}
                expected = min(schemes, key=source.SCHEMES.index)
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
