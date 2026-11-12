"""``ProfileSpec`` — compilation of claim schemas.

The no-second-roster check is here in full. The merge-order check is here in the half that does not need
``I_claim``; the other half — *"and `I_claim` unchanged"* — lands with the
projection, since asserting it before the projection exists would be asserting
nothing.
"""

import copy
from dataclasses import FrozenInstanceError
from types import MappingProxyType
from typing import ClassVar

import pytest
import yaml
from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract

import beliefs.profile as profile_module
from beliefs.claim import Referent, build_claim
from beliefs.contract import base, domain
from beliefs.errors import (
    ContractMismatch,
    DuplicateContribution,
    MalformedContract,
    ProfileError,
    SubclassRefused,
    SuccessionViolation,
    UnparsedContract,
    WithdrawnFromAuthoring,
)
from beliefs.patterns import IdentifierClass
from beliefs.profile import ProfileSpec, compile_profile, shipped_domain_contract


def forged_grammar(polarities: tuple[str, ...], inapt: str, layers: tuple[str, ...]) -> base.ClaimGrammar:
    """A hand-built claim grammar, the forgery these tests prove is refused."""
    return base.ClaimGrammar(
        version=2,
        quantifiers=("generic",),
        polarities=polarities,
        sign_inapt_tag=inapt,
        layers=layers,
        forms=base.SUPPORTED_FORMS,
        role_categories=base.SUPPORTED_ROLE_CATEGORIES,
        binding_kinds=base.SUPPORTED_BINDING_KINDS,
        mapping_types=base.SUPPORTED_MAPPING_TYPES,
        placements=base.SUPPORTED_PLACEMENTS,
        reserved_roles={"within-model": base.ReservedRole("procedure")},
    )


def test_coordination_compiles_into_immutable_authorization(base_contract):
    contract = coordination_contract()
    compiled = compile_profile(base_contract, [], coordination=contract)
    assert set(compiled.coordination_kinds) == set(contract.kinds)
    assert compiled.coordination_address_root == "project"
    assert compiled.coordination_query_kinds == frozenset(contract.query_kinds)
    assert compiled.coordination_query_relations == frozenset(contract.query_relations)
    assert compiled.activated_contracts["coordination"] == contract.content_identity


def test_no_coordination_contract_preserves_the_compiled_identity(base_contract):
    """The identity moved when source history became a declared facet,
    again when the estimand grammar entered the projection,
    again when the (here empty) `estimands` table entered it too, again
    when the composite grammar entered the projection,
    and again when the (here empty) `edges` table entered it too,
    and again when the exposure and reservation kinds entered it,
    and again when base v2's claim tables (templates, instantiations, bridges,
    duration conventions) replaced the operator and edge tables,
    and again when the measurement grammar and its five declaration tables entered the projection,
    and again when the vocabulary, pack and typed dimension tables entered it,
    and again when the four measurement kinds gained their governed facets,
    when functional and control declarations entered the schema,
    and when assumptions-register moved to science.assumptions-register.v2."""
    before = compile_profile(base_contract, [])
    assert before.compiled_identity == "306f8efeb19ba837e7e002fd38b528212b7bf63adb46100436e54733a3debdf8"
    assert compile_profile(base_contract, [], coordination=None).compiled_identity == before.compiled_identity
    assert before.coordination_kinds == {}


def test_coordination_editorial_edits_do_not_recompile(base_contract):
    genesis = coordination_contract()
    editorial_document = copy.deepcopy(COORDINATION_DOCUMENT)
    editorial_document.update(
        version=2,
        lineage={"successor": genesis.content_identity},
        description="new words",
    )
    editorial = coordination_contract(editorial_document, genesis)
    assert editorial.content_identity != genesis.content_identity
    assert (
        compile_profile(base_contract, [], coordination=editorial).compiled_identity
        == compile_profile(base_contract, [], coordination=genesis).compiled_identity
    )


def test_coordination_schema_edits_recompile(base_contract):
    genesis = coordination_contract()
    schema_document = copy.deepcopy(COORDINATION_DOCUMENT)
    schema_document["version"] = 2
    schema_document["kinds"]["publication"] = {
        "fields": ["name", "body", "author", "at"],
        "query_versions": [],
    }
    schema = coordination_contract(schema_document)
    assert (
        compile_profile(base_contract, [], coordination=schema).compiled_identity
        != compile_profile(base_contract, [], coordination=genesis).compiled_identity
    )

    field_document = copy.deepcopy(COORDINATION_DOCUMENT)
    field_document["kinds"]["decision"]["fields"].append("about")
    field_schema = coordination_contract(field_document)
    original = compile_profile(base_contract, [], coordination=genesis)
    changed = compile_profile(base_contract, [], coordination=field_schema)
    assert {name: kind.projection() for name, kind in original.kinds.items()} == {
        name: kind.projection() for name, kind in changed.kinds.items()
    }
    assert changed.compiled_identity != original.compiled_identity


@pytest.mark.parametrize("kind", ["not-world", "discussion"])
def test_coordination_compile_refuses_unknown_query_kind(base_contract, kind):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["kinds"].append(kind)
    with pytest.raises(ProfileError, match="query vocabulary"):
        compile_profile(base_contract, [], coordination=coordination_contract(document))


@pytest.mark.parametrize("relation", ["not-a-relation", "supersedes"])
def test_coordination_compile_refuses_unknown_query_relation(base_contract, relation):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["relations"].append(relation)
    with pytest.raises(ProfileError, match="query vocabulary"):
        compile_profile(base_contract, [], coordination=coordination_contract(document))


@pytest.fixture()
def parse(base_contract):
    def _parse(document, predecessor=None):
        return domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=predecessor)

    return _parse


@pytest.fixture()
def testing(parse, testing_document):
    return parse(testing_document)


@pytest.fixture()
def crossing(parse, crossing_document):
    return parse(crossing_document)


@pytest.fixture()
def compiled(base_contract, testing):
    return compile_profile(base_contract, [testing])


def successor(document, predecessor):
    document = copy.deepcopy(document)
    document["lineage"] = {"successor": predecessor.content_identity}
    document["version"] = predecessor.version + 1
    return document


ENTITY, OUTCOME = frozenset({"testing/entity"}), frozenset({"testing/outcome"})


class TestCrossContractReferences:
    """Namespaced references resolve at compile."""

    def test_foreign_declarations_resolve_when_their_contract_is_compiled(self, base_contract, testing, crossing):
        profile = compile_profile(base_contract, [crossing, testing])
        instantiation = profile.instantiations["crossing/affects-local-entity"]
        assert instantiation.template == "testing/affects"
        # A bare name is namespaced once, into its own contract.
        assert instantiation.roles == {
            "cause": frozenset({"testing/entity"}),
            "effect": frozenset({"crossing/local-entity"}),
        }
        assert instantiation.contract == "crossing"
        scope = profile.dimensions["crossing/scope"]
        assert scope.restriction_sort == "testing/cohort"
        assert scope.applies_to == frozenset({"testing/affects"})
        assert profile.sorts["testing/entity"].contract == "testing"

    def test_an_unresolved_sort_refuses_naming_the_namespace(self, base_contract, crossing):
        with pytest.raises(MalformedContract, match="no compiled contract declares sort 'testing/cohort'"):
            compile_profile(base_contract, [crossing])

    def test_an_unresolved_instantiation_sort_refuses_without_a_foreign_dimension(
        self, base_contract, parse, testing, crossing_document
    ):
        crossing_document["dimensions"] = {}
        crossing_document["instantiations"]["affects-local-entity"]["roles"]["cause"] = ["testing/missing"]
        crossing_document["estimands"] = {}
        with pytest.raises(MalformedContract, match="no compiled contract declares sort 'testing/missing'"):
            compile_profile(base_contract, [parse(crossing_document), testing])

    def test_compile_order_is_inert(self, base_contract, testing, crossing):
        one = compile_profile(base_contract, [crossing, testing])
        other = compile_profile(base_contract, [testing, crossing])
        assert one.instantiations == other.instantiations
        assert one.admission == other.admission
        assert one.activated_contracts == other.activated_contracts
        assert one.compiled_identity == other.compiled_identity


@pytest.fixture()
def other(parse, testing_document):
    """A second contract, in another namespace, declaring the same local names."""
    document = copy.deepcopy(testing_document)
    document["contract"] = "elsewhere"
    return parse(document)


class TestNoSecondAuthoredOperatorArtifact:
    """No second authored operator artifact.

    The failure it names is *"add a hand-authored operator roster beside the
    contracts"*. The test below is what makes that unreachable rather than merely
    absent: if a roster existed anywhere in the package, a profile compiled from
    **no** domain contracts would still have operators in it.
    """

    def test_a_profile_with_no_domains_has_no_operators(self, base_contract):
        profile = compile_profile(base_contract, [])
        for table in ("templates", "instantiations", "bridges", "estimands", "dimensions", "sorts", "admission"):
            assert getattr(profile, table) == {}, table
        assert profile.authorable_operators() == ()

    def test_the_base_contract_contributes_no_operator(self, compiled, base_contract):
        contracts = {decl.contract for decl in [*compiled.templates.values(), *compiled.bridges.values()]}
        assert contracts == {"testing"}
        assert base_contract.name not in contracts

    def test_every_operator_traces_to_a_supplied_contract(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        local = {"affects", "correlates-with", "transforms", "measured-by"}
        assert set(profile.templates) == {
            f"{namespace}/{name}" for namespace in ["testing", "elsewhere"] for name in local
        }
        assert set(profile.bridges) == {"testing/promotes", "elsewhere/promotes"}
        for decl in [*profile.templates.values(), *profile.bridges.values()]:
            assert decl.contract in profile.activated_contracts

    def test_compile_profile_is_the_only_exported_route(self):
        public_functions = [name for name in profile_module.__all__ if name.islower()]
        assert public_functions == [
            "compile_profile",
            "shipped_assumptions_register",
            "shipped_base",
            "shipped_base_contract",
            "shipped_coordination",
            "shipped_domain_contract",
        ]


def test_shipped_domain_contract_ships_general_and_refuses_other_namespaces():
    assert shipped_domain_contract("general").namespace == "general"
    for namespace in ("testing", "chemistry", "biology/../biology", "biology.bad", "../general"):
        with pytest.raises(ProfileError, match="ships no domain contract"):
            shipped_domain_contract(namespace)


class TestSemanticEditsRecompileAndEditorialOnesDoNot:
    """Stated as the pair of asymmetries it actually is."""

    def test_an_editorial_edit_moves_contract_identity_and_not_the_compiled_profile(
        self, base_contract, parse, testing_document, testing
    ):
        edited = successor(testing_document, testing)
        edited["templates"]["affects"]["description"] = "Reworded."
        edited["templates"]["affects"]["definition"] = "Its cause changes its effect."
        later = parse(edited, predecessor=testing)

        assert later.content_identity != testing.content_identity
        assert compile_profile(base_contract, [later]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    @pytest.mark.parametrize(
        ("section", "name", "field", "value"),
        [
            ("templates", "measured-by", "sign_apt", True),
            ("templates", "affects", "edge", {"cause": "effect", "effect": "cause"}),
            ("instantiations", "affects-entity-entity", "roles", {"cause": ["entity"], "effect": ["entity"]}),
            ("bridges", "promotes", "mapping", "contextual"),
            ("dimensions", "population", "placement", "applicability"),
            ("sorts", "entity", "categories", []),
            ("duration_conventions", "mean-month", "conversion", "mean-month-to-hour"),
        ],
    )
    def test_a_semantic_schema_edit_moves_the_compiled_profile(
        self, base_contract, parse, testing_document, compiled, section, name, field, value
    ):
        # Not reachable within a lineage — succession refuses it — so this is a
        # parallel genesis, which is the open escape hatch.
        testing_document[section][name][field] = value
        if section == "duration_conventions":
            testing_document["conversions"]["mean-month-to-hour"] = {
                "from": "calendar-month",
                "to": "hour",
                "kind": "multiplicative",
                "factor": "730.5",
                "exact": True,
            }
        if section == "dimensions" and field == "placement" and value == "applicability":
            testing_document[section][name]["restriction"] = {"form": "term", "sort": "cohort"}
        assert compile_profile(base_contract, [parse(testing_document)]).compiled_identity != compiled.compiled_identity

    @pytest.mark.parametrize(
        ("section", "name"),
        [("templates", "affects"), ("instantiations", "affects-entity-entity"), ("bridges", "promotes")],
    )
    def test_retiring_a_declaration_recompiles(self, base_contract, parse, testing_document, testing, section, name):
        # Retirement changes what the authoring constructor may offer, so the
        # compiled runtime profile is genuinely different. It is not editorial.
        retired = successor(testing_document, testing)
        retired[section][name]["retired"] = True
        later = parse(retired, predecessor=testing)
        assert compile_profile(base_contract, [later]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_a_base_contract_edit_recompiles(self, base_contract, base_contract_path, testing_document, testing):
        edited = copy.deepcopy(yaml.safe_load(base_contract_path.read_text(encoding="utf-8")))
        edited["claim_grammar"]["layers"] = [*edited["claim_grammar"]["layers"], "computational"]
        later = base.parse_base_contract(edited, source="<test>")

        # The domain is re-parsed against the edited base, because that is what
        # loading under it means.
        under_later = domain.parse_domain_contract(testing_document, source="<test>", base=later, predecessor=None)
        assert compile_profile(later, [under_later]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )


class TestMergeOrderIsInert:
    """The merge-order check, in the half that does not need ``I_claim``.

    **The first two tests below cannot fail, and that is recorded rather than
    hidden.** `science.identity.v1` sorts object keys at encode time, so no
    iteration order inside `compile_profile` can reach the identity. They are
    kept as regression guards and are not evidence of anything.

    The third test is the one with force. What *would* make merge order
    significant is a **shape** change — holding the declarations positionally
    instead of keyed by term — so that is what is asserted.
    """

    def test_the_compiled_profile_is_a_function_of_the_contract_set(self, base_contract, testing, other):
        forward = compile_profile(base_contract, [testing, other])
        reverse = compile_profile(base_contract, [other, testing])
        assert forward.compiled_identity == reverse.compiled_identity
        assert forward.templates == reverse.templates
        assert forward.activated_contracts == reverse.activated_contracts

    def test_the_compiler_contributes_no_input(self, base_contract, testing):
        assert compile_profile(base_contract, [testing]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    @pytest.mark.parametrize(
        ("section", "table"),
        [
            ("templates", "templates"),
            ("instantiations", "instantiations"),
            ("bridges", "bridges"),
            ("dimensions", "dimensions"),
            ("sorts", "sorts"),
            ("duration_conventions", "duration_conventions"),
        ],
    )
    def test_compiled_identity_keys_by_term(self, compiled, testing, section, table):
        # A sequence here would make the activation order an identity input.
        projection = compiled.projection()
        assert isinstance(projection[section], dict)
        assert set(projection[section]) == {f"testing/{local}" for local in getattr(testing, table)}  # type: ignore[arg-type]

    def test_estimands_key_by_compiled_typed_address(self, compiled, testing):
        projection = compiled.projection()
        assert isinstance(projection["estimands"], dict)
        assert set(projection["estimands"]) == {target.replace(":", ":testing/", 1) for target in testing.estimands}

    def test_activation_order_is_inert_across_contracts(self, base_contract, testing, crossing, other):
        orders = ([testing, crossing, other], [other, crossing, testing], [crossing, other, testing])
        identities = {compile_profile(base_contract, order).compiled_identity for order in orders}
        assert len(identities) == 1


class TestSetsAreSets:
    """Role sets, layers, forms, categories and `applies_to` are **finite sets**.
    Holding one positionally would make reordering one line of YAML a
    redefinition — refused at load, on a change that changed nothing."""

    @pytest.mark.parametrize(
        ("section", "name", "field"),
        [
            ("templates", "affects", "layers"),
            ("templates", "affects", "forms"),
            ("dimensions", "population", "applies_to"),
        ],
    )
    def test_reordering_a_declared_set_is_not_a_redefinition(
        self, parse, testing_document, base_contract, section, name, field
    ):
        genesis = parse(testing_document)
        document = successor(testing_document, genesis)
        document[section][name][field] = list(reversed(document[section][name][field]))
        later = parse(document, predecessor=genesis)
        assert compile_profile(base_contract, [later]).compiled_identity == (
            compile_profile(base_contract, [genesis]).compiled_identity
        )

    def test_reordering_an_instantiations_sorts_is_not_a_redefinition(self, parse, testing_document, base_contract):
        genesis = parse(testing_document)
        document = successor(testing_document, genesis)
        document["instantiations"]["affects-entity-entity"]["roles"]["effect"] = ["outcome", "entity"]
        later = parse(document, predecessor=genesis)
        assert compile_profile(base_contract, [later]).compiled_identity == (
            compile_profile(base_contract, [genesis]).compiled_identity
        )

    def test_swapping_the_edge_roles_is_a_redefinition(self, parse, testing_document):
        # The converse: which role is the cause says something about the world.
        genesis = parse(testing_document)
        document = successor(testing_document, genesis)
        document["templates"]["affects"]["edge"] = {"cause": "effect", "effect": "cause"}
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(document, predecessor=genesis)


class TestResolution:
    """ProfileSpec resolves, contracts authorize."""

    def test_local_names_are_resolved_to_term_identifiers(self, compiled):
        instantiation = compiled.instantiations["testing/affects-entity-entity"]
        assert instantiation.template == "testing/affects"
        assert instantiation.roles == {"cause": ENTITY, "effect": ENTITY | OUTCOME}
        bridge = compiled.bridges["testing/promotes"]
        assert (bridge.template, bridge.mapping, bridge.layers) == ("testing/affects", "narrower", ("causal",))
        assert bridge.roles == {"cause": ENTITY, "effect": OUTCOME}

    def test_a_dimensions_restriction_sort_and_operators_are_resolved(self, compiled):
        population = compiled.dimensions["testing/population"]
        assert population.restriction_sort == "testing/cohort"
        assert population.placement == "claim"
        assert population.applies_to == frozenset({"testing/affects", "testing/correlates-with", "testing/promotes"})

    def test_a_template_compiles_with_its_roles(self, compiled):
        transforms = compiled.templates["testing/transforms"]
        assert transforms.roles["inputs"] == profile_module.CompiledRole(
            name="inputs", arity="many", min=1, max=None, coefficients=True, constraint=frozenset()
        )
        assert transforms.edge == ("inputs", "outputs")
        assert (transforms.sign_apt, transforms.layers, transforms.forms) == (
            False,
            ("structural", "causal"),
            ("polar",),
        )

    def test_a_sort_compiles_with_its_binding_class_and_categories(self, compiled):
        entity = compiled.sorts["testing/entity"]
        assert entity.binding == domain.ReleaseBinding(namespace="EX", release="2026-01-01")
        assert entity.identifier_class is not None and entity.identifier_class.pattern == "EX:[a-z0-9\\-]+"
        assert entity.categories == frozenset({"set"})
        assert compiled.sorts["testing/procedure-spec"].identifier_class is None

    def test_duration_conventions_compile_under_their_terms(self, compiled):
        convention = compiled.duration_conventions["testing/mean-month"]
        assert (convention.term, convention.conversion, convention.contract) == (
            "testing/mean-month",
            "testing/mean-month-to-second",
            "testing",
        )

    def test_same_local_names_in_different_namespaces_compose(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        assert profile.operator("testing/affects").contract == "testing"
        assert profile.operator("elsewhere/affects").contract == "elsewhere"

    def test_two_contracts_in_one_namespace_are_refused(self, base_contract, testing, parse, testing_document):
        twin = parse(copy.deepcopy(testing_document))
        with pytest.raises(DuplicateContribution, match="never last-writer-wins"):
            compile_profile(base_contract, [testing, twin])

    def test_an_absent_operator_refuses_locally(self, compiled):
        with pytest.raises(ProfileError, match="no operator"):
            compiled.operator("testing/nowhere")
        # An instantiation is not an operator.
        with pytest.raises(ProfileError, match="no operator"):
            compiled.operator("testing/affects-entity-outcome")

    def test_an_operator_is_a_template_or_a_bridge(self, compiled):
        template = compiled.operator("testing/affects")
        bridge = compiled.operator("testing/promotes")
        assert isinstance(template, profile_module.CompiledTemplate)
        assert isinstance(bridge, profile_module.CompiledBridge)
        assert compiled.template_of(template) is template
        # A bridge inherits its template's roles, sign aptness, forms and edge.
        assert compiled.template_of(bridge) is template
        assert compiled.template_of(bridge).edge == ("cause", "effect")
        assert compiled.templates["testing/correlates-with"].edge is None


class TestAdmission:
    def test_admission_index_lists_overlapping_instantiations(self, compiled):
        assert compiled.admission["testing/affects"] == (
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/affects-entity-outcome",
        )
        assert compiled.admission["testing/measured-by"] == (
            "instantiation:testing/measured-by-entity-method",
            "instantiation:testing/promotes",
        )

    def test_the_index_spans_contracts(self, base_contract, testing, crossing):
        profile = compile_profile(base_contract, [testing, crossing])
        assert profile.admission["testing/affects"] == (
            "instantiation:crossing/affects-local-entity",
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/affects-entity-outcome",
        )

    def test_admitting_is_order_independent(self, base_contract, testing, crossing):
        assignment = {"cause": ENTITY, "effect": OUTCOME}
        one = compile_profile(base_contract, [testing, crossing])
        other = compile_profile(base_contract, [crossing, testing])
        expected = (
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/affects-entity-outcome",
        )
        assert one.admitting("testing/affects", assignment, authoring=True) == expected
        assert other.admitting("testing/affects", assignment, authoring=True) == expected

    def test_admitting_reads_every_role(self, base_contract, testing, crossing):
        profile = compile_profile(base_contract, [testing, crossing])
        assert profile.admitting("testing/affects", {"cause": ENTITY, "effect": ENTITY}, authoring=True) == (
            "instantiation:testing/affects-entity-entity",
        )
        local = frozenset({"crossing/local-entity"})
        assert profile.admitting("testing/affects", {"cause": ENTITY, "effect": local}, authoring=True) == (
            "instantiation:crossing/affects-local-entity",
        )
        assert profile.admitting("testing/affects", {"cause": OUTCOME, "effect": OUTCOME}, authoring=True) == ()

    def test_a_many_roles_member_sorts_are_each_admitted(self, compiled):
        event, product = frozenset({"testing/event"}), frozenset({"testing/product"})
        assert compiled.admitting("testing/correlates-with", {"parties": ENTITY | OUTCOME}, authoring=True) == (
            "instantiation:testing/correlates-entity-outcome",
        )
        assert compiled.admitting("testing/correlates-with", {"parties": event | product}, authoring=True) == (
            "instantiation:testing/correlates-event-product",
        )
        assert compiled.admitting("testing/correlates-with", {"parties": ENTITY | product}, authoring=True) == ()

    def test_a_reserved_role_does_not_reach_admission(self, compiled):
        assignment = {"cause": ENTITY, "effect": OUTCOME, "within-model": frozenset({"testing/procedure-spec"})}
        assert len(compiled.admitting("testing/affects", assignment, authoring=True)) == 2

    def test_an_undeclared_role_refuses(self, compiled):
        with pytest.raises(ProfileError, match="agent"):
            compiled.admitting("testing/affects", {"cause": ENTITY, "agent": ENTITY}, authoring=True)

    def test_admitting_excludes_retired_at_authoring(self, base_contract, parse, testing_document, testing):
        document = successor(testing_document, testing)
        document["instantiations"]["affects-entity-entity"]["retired"] = True
        document["bridges"]["promotes"]["retired"] = True
        profile = compile_profile(base_contract, [parse(document, predecessor=testing)])
        assignment = {"cause": ENTITY, "effect": OUTCOME}
        assert profile.admitting("testing/affects", assignment, authoring=True) == (
            "instantiation:testing/affects-entity-outcome",
        )
        # Decode admits through a retired declaration: retirement is an authoring property.
        assert profile.admitting("testing/affects", assignment, authoring=False) == (
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/affects-entity-outcome",
        )
        assert profile.admitting("testing/promotes", assignment, authoring=True) == ()
        assert profile.admitting("testing/promotes", assignment, authoring=False) == ("bridge:testing/promotes",)

    def test_estimand_declarations_by_admitting_set(self, base_contract, testing, crossing):
        profile = compile_profile(base_contract, [testing, crossing])
        admitting = profile.admitting("testing/affects", {"cause": ENTITY, "effect": OUTCOME}, authoring=True)
        declarations = profile.estimand_declarations("testing/affects", admitting)
        assert [decl.target for decl in declarations] == list(admitting)
        assert [decl.conditioning_sorts for decl in declarations] == [
            frozenset({"testing/outcome"}),
            frozenset({"testing/entity"}),
        ]
        # In the order given, never re-sorted.
        reversed_ = profile.estimand_declarations("testing/affects", tuple(reversed(admitting)))
        assert [decl.target for decl in reversed_] == list(reversed(admitting))
        # The crossing declaration whose fields match is reached only through its own admission.
        assert "instantiation:crossing/affects-local-entity" not in admitting
        local = frozenset({"crossing/local-entity"})
        foreign = profile.admitting("testing/affects", {"cause": ENTITY, "effect": local}, authoring=True)
        assert [decl.contract for decl in profile.estimand_declarations("testing/affects", foreign)] == ["crossing"]

    def test_an_admitting_instantiation_without_a_declaration_contributes_none(self, compiled):
        admitting = compiled.admitting("testing/correlates-with", {"parties": ENTITY | OUTCOME}, authoring=True)
        assert admitting == ("instantiation:testing/correlates-entity-outcome",)
        assert compiled.estimand_declarations("testing/correlates-with", admitting) == ()

    def test_estimand_declarations_refuse_an_address_of_another_operator(self, compiled):
        with pytest.raises(ProfileError, match="testing/measured-by"):
            compiled.estimand_declarations("testing/affects", ("instantiation:testing/promotes",))
        with pytest.raises(ProfileError):
            compiled.estimand_declarations("testing/affects", ("bridge:testing/promotes",))

    def test_estimand_declarations_distinguish_instantiation_from_bridge(self, compiled):
        bridge_admitting = compiled.admitting("testing/promotes", {"cause": ENTITY, "effect": OUTCOME}, authoring=True)
        assert bridge_admitting == ("bridge:testing/promotes",)
        (bridge_decl,) = compiled.estimand_declarations("testing/promotes", bridge_admitting)
        assert bridge_decl.target == "bridge:testing/promotes"
        assert bridge_decl.kind == "bridge"
        assert bridge_decl.conditioning_sorts == {"testing/entity"}
        assert "contrast" in bridge_decl.forms

        method, product = frozenset({"testing/method"}), frozenset({"testing/product"})
        inst_admitting = compiled.admitting(
            "testing/measured-by", {"subject": product, "instrument": method}, authoring=True
        )
        assert inst_admitting == ("instantiation:testing/promotes",)
        (inst_decl,) = compiled.estimand_declarations("testing/measured-by", inst_admitting)
        assert inst_decl.target == "instantiation:testing/promotes"
        assert inst_decl.kind == "instantiation"
        assert inst_decl.conditioning_sorts == {"testing/entity"}
        assert inst_decl.forms == ("quantity",)

    def test_declaration_at_dereferences_typed_addresses(self, compiled):
        instantiation = compiled.declaration_at("instantiation:testing/promotes")
        bridge = compiled.declaration_at("bridge:testing/promotes")
        assert isinstance(instantiation, profile_module.CompiledInstantiation)
        assert instantiation.template == "testing/measured-by"
        assert isinstance(bridge, profile_module.CompiledBridge)
        assert bridge.template == "testing/affects"
        for address in ("template:testing/affects", "instantiation:testing/nowhere", "testing/promotes", "bridge:"):
            with pytest.raises(ProfileError):
                compiled.declaration_at(address)


class TestDimensions:
    def test_claim_dimensions_by_applies_to(self, compiled):
        assert compiled.claim_dimensions("testing/affects") == ("testing/population", "testing/setting")
        assert compiled.claim_dimensions("testing/correlates-with") == ("testing/population",)
        assert compiled.claim_dimensions("testing/promotes") == ("testing/population",)
        assert compiled.claim_dimensions("testing/measured-by") == ()
        # `follow-up` applies to `affects` on the applicability side, so it is no claim dimension.
        assert compiled.dimensions["testing/follow-up"].applies_to == frozenset(
            {"testing/affects", "testing/correlates-with"}
        )
        with pytest.raises(ProfileError, match="no operator"):
            compiled.claim_dimensions("testing/nowhere")

    def test_applies_to_resolves_local_then_qualified(self, base_contract, testing, other, crossing):
        # A local name resolves against its own contract only, even when another
        # contract declares the same local name; a qualified one names that contract.
        profile = compile_profile(base_contract, [testing, other, crossing])
        assert profile.dimensions["testing/population"].applies_to == frozenset(
            {"testing/affects", "testing/correlates-with", "testing/promotes"}
        )
        assert profile.dimensions["elsewhere/population"].applies_to == frozenset(
            {"elsewhere/affects", "elsewhere/correlates-with", "elsewhere/promotes"}
        )
        # A dimension declared in a contract other than the operator's reaches it.
        assert profile.claim_dimensions("testing/affects") == (
            "crossing/scope",
            "testing/population",
            "testing/setting",
        )
        assert profile.claim_dimensions("elsewhere/affects") == ("elsewhere/population", "elsewhere/setting")


class TestCompileRefusals:
    def _compile(self, base_contract, parse, document, *also):
        return compile_profile(base_contract, [parse(document), *also])

    @pytest.mark.parametrize("template", ["nowhere", "other/affects", "affects-entity-entity", "promotes"])
    def test_an_instantiation_of_an_undeclared_template_refuses(self, base_contract, parse, testing_document, template):
        # A bridge is an operator and not a template, so an instantiation of one refuses too.
        testing_document["instantiations"]["affects-entity-outcome"]["template"] = template
        with pytest.raises(ProfileError, match="template"):
            self._compile(base_contract, parse, testing_document)

    def test_a_bridge_of_an_undeclared_template_refuses(self, base_contract, parse, testing_document):
        testing_document["bridges"]["promotes"]["template"] = "other/affects"
        with pytest.raises(ProfileError, match="template"):
            self._compile(base_contract, parse, testing_document)

    def test_a_listed_sort_missing_a_constraint_category_refuses(self, base_contract, parse, testing_document):
        testing_document["templates"]["affects"]["roles"]["effect"]["constraint"] = ["set"]
        with pytest.raises(ProfileError, match="testing/outcome"):
            self._compile(base_contract, parse, testing_document)

    def test_a_constraint_every_listed_sort_satisfies_compiles(self, base_contract, parse, testing_document):
        testing_document["templates"]["transforms"]["roles"]["inputs"]["constraint"] = ["set"]
        profile = self._compile(base_contract, parse, testing_document)
        assert profile.templates["testing/transforms"].roles["inputs"].constraint == frozenset({"set"})

    @pytest.mark.parametrize("table", ["instantiations", "bridges"])
    def test_a_role_the_template_lacks_refuses(self, base_contract, parse, testing_document, table):
        name = "promotes" if table == "bridges" else "affects-entity-outcome"
        testing_document[table][name]["roles"]["agent"] = ["entity"]
        with pytest.raises(ProfileError, match="agent"):
            self._compile(base_contract, parse, testing_document)

    @pytest.mark.parametrize("table", ["instantiations", "bridges"])
    def test_an_omitted_role_refuses(self, base_contract, parse, testing_document, table):
        name = "promotes" if table == "bridges" else "affects-entity-outcome"
        del testing_document[table][name]["roles"]["effect"]
        with pytest.raises(ProfileError, match="effect"):
            self._compile(base_contract, parse, testing_document)

    def test_a_within_model_role_on_an_instantiation_refuses(self, base_contract, parse, testing_document):
        testing_document["instantiations"]["affects-entity-outcome"]["roles"]["within-model"] = ["procedure-spec"]
        with pytest.raises(ProfileError, match="within-model"):
            self._compile(base_contract, parse, testing_document)

    @pytest.mark.parametrize("operator", ["nowhere", "other/affects", "affects-entity-outcome", "day"])
    def test_applies_to_naming_no_active_operator_refuses(self, base_contract, parse, testing_document, operator):
        testing_document["dimensions"]["setting"]["applies_to"] = ["affects", operator]
        with pytest.raises(ProfileError, match="applies_to"):
            self._compile(base_contract, parse, testing_document)

    def test_a_bridges_layers_outside_its_templates_refuse(self, base_contract, parse, testing_document):
        testing_document["bridges"]["promotes"]["layers"] = ["causal", "methodological"]
        with pytest.raises(ProfileError, match="methodological"):
            self._compile(base_contract, parse, testing_document)

    def test_a_bridge_without_layers_inherits_its_templates(self, base_contract, parse, testing_document):
        del testing_document["bridges"]["promotes"]["layers"]
        profile = self._compile(base_contract, parse, testing_document)
        assert profile.bridges["testing/promotes"].layers == ("causal", "statistical")

    def test_an_old_estimand_field_refuses(self, base_contract, parse, testing_document):
        testing_document["estimands"]["bridge:promotes"]["level_sorts"] = {"subject": "level"}
        with pytest.raises(MalformedContract, match="level_sorts"):
            self._compile(base_contract, parse, testing_document)


class TestRetirementIsAnAuthoringProperty:
    """Retirement lives in authoring, never in validation."""

    @pytest.fixture()
    def with_retired(self, parse, testing_document, testing):
        retired = successor(testing_document, testing)
        retired["templates"]["affects"]["retired"] = True
        return parse(retired, predecessor=testing)

    def test_a_retired_template_stays_resolvable(self, base_contract, with_retired):
        # decode / import / restore type a historical claim against the frozen
        # retired declaration.
        profile = compile_profile(base_contract, [with_retired])
        assert profile.operator("testing/affects").retired is True

    def test_a_retired_template_is_not_offered_for_authoring(self, base_contract, with_retired):
        profile = compile_profile(base_contract, [with_retired])
        assert "testing/affects" not in profile.authorable_operators()
        assert "testing/correlates-with" in profile.authorable_operators()


class TestTheProfileIsCompiledNeverAuthored:
    """A `ProfileSpec` a caller can build field-wise, or mutate after the fact, *is*
    an authored profile — and a mutated one carries a `compiled_identity`
    describing a profile that no longer exists."""

    def test_the_field_wise_constructor_is_refused(self, compiled):
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec(
                claim_grammar=compiled.claim_grammar,
                templates=dict(compiled.templates),
                dimensions=dict(compiled.dimensions),
                sorts=dict(compiled.sorts),
                base_contract_identity=compiled.base_contract_identity,
                activated_contracts=dict(compiled.activated_contracts),
                compiled_identity=compiled.compiled_identity,
            )

    def test_the_no_argument_constructor_is_refused_too(self):
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec()

    @pytest.mark.parametrize(
        "section",
        [
            "templates",
            "instantiations",
            "bridges",
            "dimensions",
            "sorts",
            "estimands",
            "duration_conventions",
            "admission",
        ],
    )
    def test_the_mappings_are_read_only(self, compiled, section):
        mapping = getattr(compiled, section)
        with pytest.raises(TypeError):
            mapping["forged"] = next(iter(mapping.values()))
        with pytest.raises(TypeError):
            del mapping[next(iter(mapping))]

    def test_the_nested_role_tables_are_read_only(self, compiled):
        with pytest.raises(TypeError):
            compiled.templates["testing/affects"].roles["forged"] = compiled.templates["testing/affects"].roles["cause"]
        with pytest.raises(TypeError):
            compiled.instantiations["testing/promotes"].roles["forged"] = frozenset()

    def test_activated_contracts_is_read_only(self, compiled):
        with pytest.raises(TypeError):
            compiled.activated_contracts["forged"] = "f" * 64  # type: ignore[index]

    def test_the_profile_cannot_be_subclassed(self):
        with pytest.raises(SubclassRefused):

            class Rogue(ProfileSpec):  # type: ignore[misc]  # the declaration is under test; see LaxReferent
                pass

    def test_the_fields_are_frozen(self, compiled):
        with pytest.raises(AttributeError):
            compiled.compiled_identity = "forged"  # type: ignore[misc]


class TestActivationIsNotConsultation:
    """The conditional case, guarded at the shape rather than in prose."""

    def test_the_unconditional_and_the_conditional_are_separate_fields(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {
            "testing": testing.content_identity,
            "elsewhere": other.content_identity,
        }

    def test_the_base_contract_is_not_among_the_activated(self, base_contract, compiled):
        assert base_contract.name not in compiled.activated_contracts
        assert compiled.base_contract_identity not in set(compiled.activated_contracts.values())

    def test_the_base_contract_identity_survives_an_empty_profile(self, base_contract):
        profile = compile_profile(base_contract, [])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {}

    def test_no_member_offers_a_consulted_set(self, compiled):
        assert not [name for name in dir(compiled) if "consult" in name.lower()]

    def test_the_compiled_identity_is_not_a_contract_identity(self, compiled):
        assert compiled.compiled_identity != compiled.base_contract_identity
        assert compiled.compiled_identity not in set(compiled.activated_contracts.values())


class TestRetirementReachesThroughSorts:
    """The authoring boundary, applied to every route into it.

    Checking only the operator's own `retired` flag leaves an operator offered
    whose roles cannot be filled — the refusal then lands when the author tries
    to bind a referent, one step past the boundary. An operator is authorable
    when it is live and some live route (an instantiation, or the bridge itself)
    lists a live sort for every role.
    """

    @pytest.fixture()
    def retire(self, parse, testing_document, base_contract):
        def _retire(*declarations):
            genesis = parse(testing_document)
            document = successor(testing_document, genesis)
            for section, name in declarations:
                document[section][name]["retired"] = True
            return compile_profile(base_contract, [parse(document, predecessor=genesis)])

        return _retire

    def test_retiring_a_sort_withdraws_the_operators_it_alone_fills(self, retire):
        profile = retire(("sorts", "entity"))
        authorable = profile.authorable_operators()
        # Every route into these lists only `entity` for some role.
        for withdrawn in ("testing/affects", "testing/transforms", "testing/promotes"):
            assert withdrawn not in authorable
        # `correlates-with` keeps `outcome` and the event/product route; `measured-by` keeps its `promotes` route.
        assert {"testing/correlates-with", "testing/measured-by"} <= set(authorable)

    def test_a_sort_another_route_still_fills_withdraws_nothing(self, retire):
        # `affects-entity-entity` lists `entity` beside `outcome` for its effect.
        assert "testing/affects" in retire(("sorts", "outcome")).authorable_operators()

    def test_retiring_every_instantiation_withdraws_the_template(self, retire):
        profile = retire(("instantiations", "affects-entity-outcome"), ("instantiations", "affects-entity-entity"))
        assert "testing/affects" not in profile.authorable_operators()
        # The bridge is its own route and stays.
        assert "testing/promotes" in profile.authorable_operators()

    def test_the_withdrawn_operator_stays_resolvable_for_decode(self, retire):
        profile = retire(("sorts", "entity"))
        assert profile.operator("testing/affects").retired is False

    def test_retiring_the_template_itself_still_withdraws_it(self, retire):
        assert "testing/affects" not in retire(("templates", "affects")).authorable_operators()

    def test_retiring_a_template_withdraws_its_bridges(self, retire):
        profile = retire(("templates", "affects"))
        assert "testing/promotes" not in profile.authorable_operators()
        with pytest.raises(WithdrawnFromAuthoring, match="template 'testing/affects' is retired"):
            profile.authorable_dimensions("testing/promotes")
        # Withdrawn, not removed: the bridge stays resolvable for decode.
        assert profile.operator("testing/promotes").retired is False

    def test_a_withdrawn_operator_offers_no_dimensions_at_all(self, retire):
        # Not an empty tuple: `measured-by` legitimately returns one, so an empty
        # answer here would make "withdrawn" and "permits none" the same fact.
        for declarations, reason in [
            ((("templates", "affects"),), "the operator is retired"),
            ((("sorts", "entity"),), "no live route"),
        ]:
            profile = retire(*declarations)
            with pytest.raises(WithdrawnFromAuthoring, match=reason):
                profile.authorable_dimensions("testing/affects")

    def test_an_unresolvable_operator_is_not_a_withdrawn_one(self, compiled):
        with pytest.raises(ProfileError, match="no operator"):
            compiled.authorable_dimensions("testing/absent")

    def test_retiring_a_dimension_withdraws_only_that_dimension(self, retire):
        profile = retire(("dimensions", "setting"))
        assert "testing/affects" in profile.authorable_operators()
        assert profile.authorable_dimensions("testing/affects") == ("testing/population",)

    def test_retiring_a_restriction_sort_withdraws_its_dimension(self, retire):
        profile = retire(("sorts", "cohort"))  # population : restriction_sort cohort
        assert profile.authorable_dimensions("testing/affects") == ("testing/setting",)

    def test_nothing_is_withdrawn_when_nothing_is_retired(self, compiled):
        assert set(compiled.authorable_operators()) == {
            "testing/affects",
            "testing/correlates-with",
            "testing/transforms",
            "testing/measured-by",
            "testing/promotes",
        }
        assert compiled.authorable_dimensions("testing/affects") == ("testing/population", "testing/setting")
        assert compiled.authorable_dimensions("testing/promotes") == ("testing/population",)
        assert compiled.authorable_dimensions("testing/measured-by") == ()


class TestTheTrustChainStartsAtTheDocument:
    """``ProfileSpec`` refuses to be authored, and that refusal certifies exactly one
    thing: ``compile_profile`` ran. It says nothing about what ``compile_profile``
    was handed, so the contracts it compiles must have come from a parser."""

    def test_an_authored_base_contract_cannot_be_constructed(self):
        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            base.BaseContract(
                name="science",
                version=1,
                claim_grammar=forged_grammar(("positive",), "inapt", ("causal",)),
                content_identity="0" * 64,
            )

    def test_an_authored_domain_contract_cannot_be_constructed(self):
        with pytest.raises(UnparsedContract, match="parse_domain_contract"):
            domain.DomainContract(namespace="forged", version=1, predecessor=None)

    def test_neither_can_be_subclassed(self):
        with pytest.raises(SubclassRefused):

            class RogueBase(base.BaseContract):  # type: ignore[misc]  # the declaration is under test
                pass

        with pytest.raises(SubclassRefused):

            class RogueDomain(domain.DomainContract):  # type: ignore[misc]
                pass

    def test_compilation_refuses_a_base_contract_no_parser_produced(self, testing):
        class Impostor:
            claim_grammar = forged_grammar(("positive",), "inapt", ("causal",))
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            compile_profile(Impostor(), [testing])  # type: ignore[arg-type]

    def test_compilation_refuses_a_domain_contract_no_parser_produced(self, base_contract):
        class Impostor:
            namespace = "forged"
            sorts: ClassVar[dict] = {}
            dimensions: ClassVar[dict] = {}
            templates: ClassVar[dict] = {}
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_domain_contract"):
            compile_profile(base_contract, [Impostor()])  # type: ignore[list-item]

    def test_a_contract_cannot_be_edited_after_it_is_parsed(self, testing):
        with pytest.raises(TypeError):
            testing.templates["smuggled"] = testing.templates["affects"]  # type: ignore[index]
        with pytest.raises(TypeError):
            del testing.sorts["entity"]  # type: ignore[attr-defined]
        with pytest.raises(TypeError):
            testing.templates["affects"].roles["smuggled"] = testing.templates["affects"].roles["cause"]  # type: ignore[index]
        with pytest.raises(FrozenInstanceError):
            testing.namespace = "forged"  # type: ignore[misc]

    def test_the_parsed_contracts_are_the_ones_compilation_accepts(self, base_contract, testing):
        assert isinstance(base_contract, base.BaseContract)
        assert isinstance(testing, domain.DomainContract)
        assert compile_profile(base_contract, [testing]).activated_contracts == {"testing": testing.content_identity}


class TestTwoGenuineContractsThatDoNotBelongTogether:
    """Provenance is necessary and is not sufficient.

    Nothing in this class is forged. A domain's layer selections are validated
    **once**, at parse time, against whatever base it was handed, and the
    compiled template then carries them as facts that nothing revalidates. So
    authenticating each input separately says nothing about whether the inputs
    **belong together**, and compile checks the recorded dependency.
    """

    @pytest.fixture()
    def wide_base(self, base_contract_path):
        document = copy.deepcopy(yaml.safe_load(base_contract_path.read_text(encoding="utf-8")))
        document["claim_grammar"]["layers"] = [*document["claim_grammar"]["layers"], "speculative"]
        return base.parse_base_contract(document, source="<wide>")

    @pytest.fixture()
    def speculative_document(self, testing_document):
        document = copy.deepcopy(testing_document)
        document["templates"]["affects"]["layers"] = ["causal", "speculative"]
        return document

    def test_a_domain_parsed_under_another_base_is_refused(self, base_contract, wide_base, speculative_document):
        under_wide = domain.parse_domain_contract(
            speculative_document, source="<testing>", base=wide_base, predecessor=None
        )
        assert "speculative" in under_wide.templates["affects"].layers
        with pytest.raises(ContractMismatch, match="typed against base contract"):
            compile_profile(base_contract, [under_wide])

    def test_it_compiles_under_the_base_it_was_parsed_against(self, wide_base, speculative_document):
        under_wide = domain.parse_domain_contract(
            speculative_document, source="<testing>", base=wide_base, predecessor=None
        )
        claim = build_claim(
            compile_profile(wide_base, [under_wide]),
            operator="testing/affects",
            roles={
                "cause": Referent(sort="testing/entity", term="EX:g"),
                "effect": Referent(sort="testing/outcome", term="EX:o"),
            },
            layer="speculative",
            polarity="positive",
        )
        assert claim.layer == "speculative"

    def test_the_domain_records_the_base_it_was_typed_against(self, base_contract, testing):
        assert testing.base_identity == base_contract.content_identity

    def test_the_domain_parser_authenticates_its_base(self, testing_document):
        class Impostor:
            name = "science"
            claim_grammar = forged_grammar(("positive",), "inapt", ("causal",))
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            domain.parse_domain_contract(testing_document, source="<t>", base=Impostor(), predecessor=None)  # type: ignore[arg-type]

    def test_the_domain_parser_authenticates_its_predecessor(self, base_contract, testing_document):
        later = copy.deepcopy(testing_document)
        later["version"] = 2
        later["lineage"] = {"successor": "0" * 64}

        class Impostor:
            namespace = "testing"
            content_identity = "0" * 64

            def claim_vocabulary(self):
                return {}

            def retired_identifiers(self):
                return frozenset()

        with pytest.raises(UnparsedContract, match="predecessor"):
            domain.parse_domain_contract(
                later,
                source="<t>",
                base=base_contract,
                predecessor=Impostor(),  # type: ignore[arg-type]
            )


class TestTheOrdinaryRouteToAnUnparsedArtifact:
    """``_parsed`` and ``_compiled`` are the parsers' own routes, not internal by
    convention. Python has no module privacy, so these tests assert that
    reaching an unparsed artifact requires reaching for the audit surface that
    already exists, rather than calling a method that merely looked internal."""

    def test_a_base_contract_cannot_be_minted_without_the_parser_token(self):
        with pytest.raises(UnparsedContract, match="mint token"):
            base.BaseContract._parsed(
                object(),
                name="science",
                version=1,
                claim_grammar=forged_grammar(("positive",), "inapt", ("causal",)),
                content_identity="0" * 64,
            )

    def test_a_domain_contract_cannot_be_minted_without_the_parser_token(self):
        with pytest.raises(UnparsedContract, match="mint token"):
            domain.DomainContract._parsed(
                object(),
                namespace="forged",
                version=1,
                predecessor=None,
                sorts={},
                dimensions={},
                templates={},
                instantiations={},
                bridges={},
                estimands={},
                duration_conventions={},
                functionals={},
                identification_classes={},
                designs={},
                selection_mechanisms={},
                procedure_kinds={},
                aggregation_rules={},
                assumption_kinds={},
                measurements={},
                aspects={},
                quantity_kinds={},
                units={},
                constants={},
                conversions={},
                transformations={},
                facets={},
                content_identity="0" * 64,
                base_identity="0" * 64,
            )

    def test_a_profile_cannot_be_minted_without_the_compiler_token(self):
        with pytest.raises(ProfileError, match="mint token"):
            ProfileSpec._compiled(object(), claim_grammar=None, templates={}, dimensions={}, sorts={})

    def test_the_raw_write_remains_and_is_the_audit_surface(self, base_contract):
        forged = object.__new__(base.BaseContract)
        object.__setattr__(forged, "content_identity", "0" * 64)
        assert isinstance(forged, base.BaseContract)


class TestTheClaimConstructorAuthenticatesItsProfile:
    """Every check a claim passes is read out of the profile object, so an
    impostor exposing `operator`, `template_of`, `admitting`, `claim_dimensions`,
    `sorts`, `dimensions` and `claim_grammar` would type a claim against
    declarations of its own choosing. The constructor's first check is that the
    profile is a compiled one.
    """

    class Impostor:
        claim_grammar = forged_grammar(("yes",), "no", ("made-up",))
        dimensions: ClassVar[dict] = {}
        sorts: ClassVar[dict] = {
            "forged/sort": profile_module.CompiledSort(
                term="forged/sort",
                binding=domain.SchemeBinding(scheme="X", version="1"),
                identifier_class=IdentifierClass(prefix="X", pattern="X:[0-9]+"),
                categories=frozenset(),
                retired=False,
                contract="forged",
            )
        }
        template = profile_module.CompiledTemplate(
            term="forged/op",
            roles=MappingProxyType(
                {
                    "subject": profile_module.CompiledRole(
                        name="subject", arity="one", min=1, max=1, coefficients=False, constraint=frozenset()
                    )
                }
            ),
            sign_apt=True,
            layers=("made-up",),
            forms=("polar",),
            edge=None,
            retired=False,
            contract="forged",
        )

        def operator(self, term):
            return self.template

        def template_of(self, operator):
            return self.template

        def admitting(self, operator, assignment, *, authoring):
            return ("instantiation:forged/anything",)

        def claim_dimensions(self, operator):
            return ()

    def test_the_impostor_is_a_complete_duck(self, monkeypatch):
        # Without the authentication it would type a claim: the refusal below is
        # the profile check's, not a gap in the forgery.
        import beliefs.claim as claim_module

        monkeypatch.setattr(claim_module, "_require_profile", lambda value: None)
        claim = build_claim(
            self.Impostor(),  # type: ignore[arg-type]
            operator="forged/op",
            roles={"subject": Referent(sort="forged/sort", term="X:1")},
            layer="made-up",
            polarity="yes",
        )
        assert claim.layer == "made-up"

    def test_build_claim_refuses_an_impostor(self):
        with pytest.raises(ProfileError, match="compile_profile"):
            build_claim(
                self.Impostor(),  # type: ignore[arg-type]
                operator="forged/op",
                roles={"subject": Referent(sort="forged/sort", term="X:1")},
                layer="made-up",
                polarity="yes",
            )

    def test_the_decode_route_refuses_it_too(self):
        # `Claim._checked` is the other entry point, and decode calls it
        # directly. A check on one of two entry points is a check on neither.
        from beliefs.claim import Claim

        with pytest.raises(ProfileError, match="compile_profile"):
            Claim._checked(
                self.Impostor(),  # type: ignore[arg-type]
                operator="forged/op",
                roles={"subject": Referent(sort="forged/sort", term="X:1")},
                qualifiers={},
                form="polar",
                polarity="yes",
                layer="made-up",
            )


class TestEdges:
    """A template's `edge` role pair replaces the v1 `edges:` table."""

    def test_the_edge_compiles_on_the_template(self, compiled):
        assert compiled.templates["testing/affects"].edge == ("cause", "effect")
        assert compiled.templates["testing/transforms"].edge == ("inputs", "outputs")
        assert compiled.templates["testing/correlates-with"].edge is None

    def test_the_edge_enters_the_compiled_identity(self, base_contract, parse, testing_document, compiled):
        del testing_document["templates"]["affects"]["edge"]
        assert compile_profile(base_contract, [parse(testing_document)]).compiled_identity != compiled.compiled_identity

    def test_the_v1_edges_table_is_gone(self, compiled):
        assert not hasattr(compiled, "edges")
        assert not hasattr(compiled, "estimand")
