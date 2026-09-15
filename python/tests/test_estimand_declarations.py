"""The `estimands:` declaration class (estimand-typing design §5, Q2)."""

import copy

import pytest

from beliefs.contract import domain
from beliefs.errors import MalformedContract, SuccessionViolation


@pytest.fixture()
def parse(base_contract):
    def _parse(document, source="<test>", predecessor=None):
        return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=predecessor)

    return _parse


def test_the_fixture_declares_two_estimands(parse, testing_document):
    contract = parse(testing_document)
    assert set(contract.estimands) == {"affects", "correlates-with"}
    decl = contract.estimands["affects"]
    assert decl.level_sorts == {"0": "level"}
    assert (decl.measure_sort, decl.identification_sort, decl.conditioning_sort) == ("measure", "identification", "entity")


def test_a_key_naming_an_undeclared_operator_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["regulates"] = document["estimands"]["affects"]
    with pytest.raises(MalformedContract, match="regulates"):
        parse(document)


def test_a_level_sort_index_outside_the_arity_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["level_sorts"] = {"2": "level"}
    with pytest.raises(MalformedContract, match="Fin"):
        parse(document)


def test_a_non_decimal_level_sort_key_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["level_sorts"] = {"first": "level"}
    with pytest.raises(MalformedContract, match="slot index"):
        parse(document)


def test_an_arity_zero_operator_admits_no_declaration(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["operators"]["holds"] = {"arity": 0, "arg_sorts": [], "sign_apt": False, "layers": ["structural"], "dimensions": []}
    document["estimands"]["holds"] = {"level_sorts": {}, "measure_sort": "measure", "identification_sort": "identification", "conditioning_sort": "entity"}
    with pytest.raises(MalformedContract, match="arity 0"):
        parse(document)


def test_an_unknown_field_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["retired"] = True
    with pytest.raises(MalformedContract, match="unknown field"):
        parse(document)


def test_an_undeclared_sort_is_refused_at_parse(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["measure_sort"] = "assay"
    with pytest.raises(MalformedContract, match="assay"):
        parse(document)


def test_the_projection_sorts_level_sort_keys(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["operators"]["affects"]["arity"] = 2
    document["estimands"]["affects"]["level_sorts"] = {"1": "level", "0": "level"}
    reordered = copy.deepcopy(document)
    reordered["estimands"]["affects"]["level_sorts"] = {"0": "level", "1": "level"}
    assert parse(document).estimands["affects"].schema_projection() == parse(reordered).estimands["affects"].schema_projection()
    assert parse(document).content_identity == parse(reordered).content_identity


class TestSuccession:
    def _successor(self, document, predecessor):
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": predecessor.content_identity}
        return successor

    def test_adding_a_declaration_for_an_existing_operator_is_accepted(self, parse, testing_document):
        prior_document = copy.deepcopy(testing_document)
        del prior_document["estimands"]["correlates-with"]
        prior = parse(prior_document)
        successor = self._successor(testing_document, prior)
        contract = parse(successor, predecessor=prior)
        assert "correlates-with" in contract.estimands
        assert contract.operators["correlates-with"].schema_projection() == prior.operators["correlates-with"].schema_projection()

    @pytest.mark.parametrize("member,value", [
        ("level_sorts", {}),
        ("measure_sort", "entity"),
        ("identification_sort", "entity"),
        ("conditioning_sort", "outcome"),
    ])
    def test_changing_any_member_is_a_redefinition(self, parse, testing_document, member, value):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["estimands"]["affects"][member] = value
        with pytest.raises(SuccessionViolation, match="estimand:affects"):
            parse(successor, predecessor=prior)

    def test_dropping_a_declaration_is_refused(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        del successor["estimands"]["affects"]
        with pytest.raises(SuccessionViolation, match="estimand:affects"):
            parse(successor, predecessor=prior)

    def test_retiring_the_operator_keeps_the_declaration_as_a_tombstone(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["operators"]["affects"]["retired"] = True
        contract = parse(successor, predecessor=prior)
        assert "affects" in contract.estimands
