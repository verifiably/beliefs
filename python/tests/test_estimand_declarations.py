"""The `estimands:` declaration class: keyed by typed target, `level_sorts` keyed by role."""

import copy

import pytest

from beliefs.contract import domain
from beliefs.errors import MalformedContract, ProfileError, SuccessionViolation


@pytest.fixture()
def parse(base_contract):
    def _parse(document, source="<test>", predecessor=None):
        return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=predecessor)

    return _parse


def test_the_fixture_declares_five_estimands(parse, testing_document):
    contract = parse(testing_document)
    assert set(contract.estimands) == {
        "instantiation:affects-entity-outcome",
        "instantiation:affects-entity-entity",
        "instantiation:correlates-event-product",
        "bridge:promotes",
        "instantiation:promotes",
    }
    decl = contract.estimands["instantiation:affects-entity-outcome"]
    assert decl.target == "instantiation:affects-entity-outcome"
    assert decl.level_sorts == {"cause": "level"}
    assert (decl.measure_sort, decl.identification_sort, decl.conditioning_sort) == (
        "measure",
        "identification",
        "entity",
    )


def test_level_sorts_are_keyed_by_role(parse, testing_document):
    contract = parse(testing_document)
    assert contract.estimands["instantiation:correlates-event-product"].level_sorts == {"parties": "level"}
    assert contract.estimands["instantiation:promotes"].level_sorts == {"subject": "level"}


@pytest.mark.parametrize("key", ["0", "Cause", "", "cause/0"])
def test_a_level_sorts_key_that_is_not_a_role_name_is_refused(parse, testing_document, key):
    testing_document["estimands"]["bridge:promotes"]["level_sorts"] = {key: "level"}
    with pytest.raises(MalformedContract, match="level_sorts"):
        parse(testing_document)


def test_an_unknown_field_is_refused(parse, testing_document):
    testing_document["estimands"]["bridge:promotes"]["retired"] = True
    with pytest.raises(MalformedContract, match="unknown field"):
        parse(testing_document)


@pytest.mark.parametrize("field", ["measure_sort", "identification_sort", "conditioning_sort"])
def test_an_undeclared_sort_is_refused_at_parse(parse, testing_document, field):
    testing_document["estimands"]["bridge:promotes"][field] = "assay"
    with pytest.raises(MalformedContract, match="assay"):
        parse(testing_document)


def test_an_undeclared_level_sort_is_refused_at_parse(parse, testing_document):
    testing_document["estimands"]["bridge:promotes"]["level_sorts"] = {"cause": "assay"}
    with pytest.raises(MalformedContract, match="assay"):
        parse(testing_document)


def test_the_projection_sorts_level_sort_keys(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["bridge:promotes"]["level_sorts"] = {"effect": "outcome", "cause": "level"}
    reordered = copy.deepcopy(document)
    reordered["estimands"]["bridge:promotes"]["level_sorts"] = {"cause": "level", "effect": "outcome"}
    assert (
        parse(document).estimands["bridge:promotes"].schema_projection()
        == parse(reordered).estimands["bridge:promotes"].schema_projection()
    )
    assert parse(document).content_identity == parse(reordered).content_identity


class TestSuccession:
    def _successor(self, document, predecessor):
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": predecessor.content_identity}
        successor["version"] = predecessor.version + 1
        return successor

    def test_adding_a_declaration_for_an_existing_instantiation_is_accepted(self, parse, testing_document):
        prior_document = copy.deepcopy(testing_document)
        del prior_document["estimands"]["instantiation:promotes"]
        prior = parse(prior_document)
        successor = self._successor(testing_document, prior)
        contract = parse(successor, predecessor=prior)
        assert "instantiation:promotes" in contract.estimands

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            ("level_sorts", {}),
            ("level_sorts", {"effect": "level"}),
            ("measure_sort", "entity"),
            ("identification_sort", "entity"),
            ("conditioning_sort", "outcome"),
        ],
    )
    def test_changing_any_member_is_a_redefinition(self, parse, testing_document, member, value):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["estimands"]["instantiation:affects-entity-outcome"][member] = value
        with pytest.raises(SuccessionViolation, match="estimand:instantiation:affects-entity-outcome"):
            parse(successor, predecessor=prior)

    def test_dropping_a_declaration_is_refused(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        del successor["estimands"]["bridge:promotes"]
        with pytest.raises(SuccessionViolation, match="estimand:bridge:promotes"):
            parse(successor, predecessor=prior)

    def test_retiring_the_instantiation_keeps_the_declaration_as_a_tombstone(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["instantiations"]["affects-entity-outcome"]["retired"] = True
        contract = parse(successor, predecessor=prior)
        assert "instantiation:affects-entity-outcome" in contract.estimands


class TestCompile:
    @pytest.fixture()
    def profile(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
        return compile_profile(base_contract, [testing])

    def test_sorts_compile_to_term_identifiers(self, profile):
        decl = profile.estimands["instantiation:testing/affects-entity-outcome"]
        assert decl.target == "instantiation:testing/affects-entity-outcome"
        assert decl.level_sorts == {"cause": "testing/level"}
        assert decl.measure_sort == "testing/measure"
        assert decl.identification_sort == "testing/identification"
        assert decl.conditioning_sort == "testing/entity"
        assert decl.contract == "testing"

    def test_the_table_is_keyed_by_compiled_typed_address(self, profile):
        assert set(profile.estimands) == {
            "instantiation:testing/affects-entity-outcome",
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/correlates-event-product",
            "bridge:testing/promotes",
            "instantiation:testing/promotes",
        }

    def test_a_level_sorts_key_naming_no_role_of_the_target_refuses(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        testing_document["estimands"]["instantiation:promotes"]["level_sorts"] = {"cause": "level"}
        contract = domain.parse_domain_contract(testing_document, source="<x>", base=base_contract, predecessor=None)
        with pytest.raises(ProfileError, match="cause"):
            compile_profile(base_contract, [contract])

    def test_the_declaration_enters_the_compiled_identity(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        changed = copy.deepcopy(testing_document)
        changed["estimands"]["bridge:promotes"]["conditioning_sort"] = "outcome"
        one = compile_profile(
            base_contract,
            [domain.parse_domain_contract(testing_document, source="<a>", base=base_contract, predecessor=None)],
        )
        two = compile_profile(
            base_contract, [domain.parse_domain_contract(changed, source="<b>", base=base_contract, predecessor=None)]
        )
        assert one.compiled_identity != two.compiled_identity

    def test_a_cross_contract_sort_resolves_or_refuses_by_namespace(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        testing_document["estimands"]["bridge:promotes"]["measure_sort"] = "biology/assay"
        contract = domain.parse_domain_contract(testing_document, source="<x>", base=base_contract, predecessor=None)
        with pytest.raises(MalformedContract, match="namespace 'biology'"):
            compile_profile(base_contract, [contract])

    def test_a_foreign_instantiations_declaration_resolves_into_its_own_namespace(
        self, base_contract, testing_document, crossing_document
    ):
        from beliefs.profile import compile_profile

        testing = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
        crossing = domain.parse_domain_contract(crossing_document, source="<c>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [testing, crossing])
        foreign = profile.estimands["instantiation:crossing/affects-local-entity"]
        local = profile.estimands["instantiation:testing/affects-entity-outcome"]
        assert foreign.contract == "crossing"
        assert foreign.schema_projection() == local.schema_projection()
