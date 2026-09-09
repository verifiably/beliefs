"""``ProfileSpec`` — compilation of claim schemas.

M7 is here in full. M8's merge-order arm is here in the half that does not need
``I_claim``; the other half — *"and `I_claim` unchanged"* — lands with the
projection, since asserting it before the projection exists would be asserting
nothing.
"""

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
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
from beliefs.profile import ProfileSpec, compile_profile


def test_coordination_compiles_into_immutable_authorization(base_contract):
    contract = coordination_contract()
    compiled = compile_profile(base_contract, [], coordination=contract)
    assert set(compiled.coordination_kinds) == set(contract.kinds)
    assert compiled.coordination_address_root == "project"
    assert compiled.coordination_query_kinds == frozenset(contract.query_kinds)
    assert compiled.coordination_query_relations == frozenset(contract.query_relations)
    assert compiled.activated_contracts["coordination"] == contract.content_identity


def test_no_coordination_contract_preserves_the_cut_20_compiled_identity(base_contract):
    before = compile_profile(base_contract, [])
    assert before.compiled_identity == "daebbdee1f95c0ebb61b06a0c202c53f981be98b27fb0a83c2dca42d89cdeefa"
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
def crossing_document():
    path = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "crossing.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestCrossContractSlots:
    """Biology pack design §4.3: namespaced references resolve at compile."""

    def test_a_foreign_sort_resolves_when_its_contract_is_compiled(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [crossing, testing])
        operator = profile.operator("crossing/affects-local-entity")
        assert operator.arg_sorts == ("crossing/local", "testing/entity")
        assert operator.contract == "crossing" and operator.dimensions == ()
        assert profile.dimensions["crossing/scope"].restriction_sort == "testing/cohort"
        assert profile.operator("crossing/scoped-local-local").dimensions == ("crossing/scope",)
        assert profile.sorts["testing/entity"].contract == "testing"

    def test_the_resolver_namespaces_a_bare_name_once(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [crossing, testing])
        assert profile.operator("crossing/same-local-local").arg_sorts == ("crossing/local", "crossing/local")

    def test_an_unresolved_reference_refuses_naming_the_namespace(self, base_contract, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        with pytest.raises(MalformedContract, match="no compiled contract declares sort 'testing/cohort'"):
            compile_profile(base_contract, [crossing])

    def test_an_unresolved_operator_sort_refuses_without_a_foreign_dimension(
        self, base_contract, testing, crossing_document
    ):
        crossing_document["dimensions"] = {}
        crossing_document["operators"] = {"affects-local-entity": crossing_document["operators"]["affects-local-entity"]}
        crossing_document["operators"]["affects-local-entity"]["arg_sorts"][1] = "testing/missing"
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        with pytest.raises(MalformedContract, match="no compiled contract declares sort 'testing/missing'"):
            compile_profile(base_contract, [crossing, testing])

    def test_compile_order_is_inert(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        one = compile_profile(base_contract, [crossing, testing])
        other = compile_profile(base_contract, [testing, crossing])
        assert one.operator("crossing/affects-local-entity") == other.operator("crossing/affects-local-entity")
        assert one.activated_contracts == other.activated_contracts


@pytest.fixture()
def other(parse, testing_document):
    """A second contract, in another namespace, declaring the same local names."""
    document = copy.deepcopy(testing_document)
    document["contract"] = "elsewhere"
    return parse(document)


class TestNoSecondAuthoredOperatorArtifact:
    """M7's first clause.

    The sabotage it names is *"add a hand-authored operator roster beside the
    contracts"*. The test below is what makes that unreachable rather than merely
    absent: if a roster existed anywhere in the package, a profile compiled from
    **no** domain contracts would still have operators in it.
    """

    def test_a_profile_with_no_domains_has_no_operators(self, base_contract):
        profile = compile_profile(base_contract, [])
        assert profile.operators == {}
        assert profile.dimensions == {}
        assert profile.sorts == {}

    def test_the_base_contract_contributes_no_operator(self, base_contract, testing):
        # §7.1: operators are domain-issued without exception.
        profile = compile_profile(base_contract, [testing])
        assert {decl.contract for decl in profile.operators.values()} == {"testing"}
        assert base_contract.name not in {decl.contract for decl in profile.operators.values()}

    def test_every_operator_traces_to_a_supplied_contract(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        local = {"affects", "subtype-of", "correlates-with", "measured-by"}
        assert set(profile.operators) == {
            f"{namespace}/{name}" for namespace in ["testing", "elsewhere"] for name in local
        }
        for decl in profile.operators.values():
            assert decl.contract in profile.activated_contracts

    def test_compile_profile_is_the_only_exported_route(self):
        public_functions = [name for name in profile_module.__all__ if name.islower()]
        assert public_functions == [
            "compile_profile",
            "shipped_base",
            "shipped_base_contract",
            "shipped_domain_contract",
        ]


class TestSemanticEditsRecompileAndEditorialOnesDoNot:
    """M7's second clause, stated as the pair of asymmetries it actually is."""

    def test_an_editorial_edit_moves_contract_identity_and_not_the_compiled_profile(
        self, base_contract, parse, testing_document, testing
    ):
        edited = copy.deepcopy(testing_document)
        edited["operators"]["affects"]["description"] = "Reworded."
        edited["lineage"] = {"successor": testing.content_identity}
        edited["version"] = 2
        successor = parse(edited, predecessor=testing)

        assert successor.content_identity != testing.content_identity
        assert compile_profile(base_contract, [successor]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_a_semantic_schema_edit_moves_the_compiled_profile(self, base_contract, parse, testing_document, testing):
        # Not reachable within a lineage — succession refuses it — so this is a
        # parallel genesis, which §8.3 records as the open escape hatch. The
        # recompilation property is asserted on the only path that can produce it.
        edited = copy.deepcopy(testing_document)
        edited["operators"]["affects"]["sign_apt"] = False
        assert compile_profile(base_contract, [parse(edited)]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_retiring_an_operator_recompiles(self, base_contract, parse, testing_document, testing):
        # Retirement changes what the authoring constructor may offer, so the
        # compiled runtime profile is genuinely different. It is not editorial.
        retired = copy.deepcopy(testing_document)
        retired["operators"]["affects"]["retired"] = True
        retired["lineage"] = {"successor": testing.content_identity}
        retired["version"] = 2
        successor = parse(retired, predecessor=testing)

        assert compile_profile(base_contract, [successor]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    def test_a_base_contract_edit_recompiles(self, base_contract, base_contract_path, parse, testing_document, testing):
        edited = copy.deepcopy(yaml.safe_load(base_contract_path.read_text(encoding="utf-8")))
        edited["claim_grammar"]["layers"] = [*edited["claim_grammar"]["layers"], "computational"]
        successor = base.parse_base_contract(edited, source="<test>")

        # The domain is re-parsed against the edited base, because that is what
        # loading under it means. Written first without the re-parse — compiling
        # one base's domain under another — which was the setup the mismatch
        # check now refuses, and refuses rightly: those layers were validated
        # against a document that is no longer the one in force.
        under_successor = domain.parse_domain_contract(
            testing_document, source="<test>", base=successor, predecessor=None
        )
        assert compile_profile(successor, [under_successor]).compiled_identity != (
            compile_profile(base_contract, [testing]).compiled_identity
        )


class TestMergeOrderIsInert:
    """M8's arm, in the half that does not need ``I_claim``.

    **The first two tests below cannot fail, and that is recorded rather than
    hidden.** `science.identity.v1` sorts object keys at encode time, so no
    iteration order inside `compile_profile` can reach the identity — sabotaging
    every sort in the compiler leaves both of them green. They are kept as
    regression guards and are not evidence of anything.

    The third test is the one with force. What *would* make merge order
    significant is a **shape** change — holding the declarations positionally
    instead of keyed by term — so that is what is asserted, and it is the arm
    that goes red when sabotaged.
    """

    def test_the_compiled_profile_is_a_function_of_the_contract_set(self, base_contract, testing, other):
        forward = compile_profile(base_contract, [testing, other])
        reverse = compile_profile(base_contract, [other, testing])
        assert forward.compiled_identity == reverse.compiled_identity
        assert forward.operators == reverse.operators
        assert forward.activated_contracts == reverse.activated_contracts

    def test_the_compiler_contributes_no_input(self, base_contract, testing):
        # No build, version or timestamp is an input to the identity.
        assert compile_profile(base_contract, [testing]).compiled_identity == (
            compile_profile(base_contract, [testing]).compiled_identity
        )

    @pytest.mark.parametrize("section", ["operators", "dimensions", "sorts"])
    def test_declarations_are_keyed_by_term_never_held_positionally(self, base_contract, testing, section):
        # A sequence here would make the merge order an identity input.
        projection = compile_profile(base_contract, [testing]).projection()
        assert isinstance(projection[section], dict)
        assert set(projection[section]) == {  # type: ignore[arg-type]  # narrowed by the assert above
            f"testing/{local}" for local in _locals(testing, section)
        }


def _locals(contract, section):
    return getattr(contract, section).keys()


class TestSetsAreSetsAndSlotsAreSlots:
    """§6.2 types `Dims(op)` and `Layers(op)` as **finite sets** and `ArgSort(op)`
    as a function on `Fin(arity(op))`. Holding a set positionally would make
    reordering one line of YAML a redefinition — refused at load, on a change
    that changed nothing.

    Found by a shape test failing for the right reason: `"dimensions":[` turned
    up nested inside every operator.
    """

    @staticmethod
    def _successor(document, predecessor, operators):
        successor = copy.deepcopy(document)
        successor["operators"] = operators
        successor["lineage"] = {"successor": predecessor.content_identity}
        successor["version"] = predecessor.version + 1
        return successor

    @pytest.mark.parametrize("declared_set", ["dimensions", "layers"])
    def test_reordering_a_declared_set_is_not_a_redefinition(
        self, parse, testing_document, base_contract, declared_set
    ):
        genesis = parse(testing_document)
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"][declared_set] = list(reversed(operators["affects"][declared_set]))
        # Must not raise: succession would otherwise report a redefinition.
        successor = parse(self._successor(testing_document, genesis, operators), predecessor=genesis)
        assert compile_profile(base_contract, [successor]).compiled_identity == (
            compile_profile(base_contract, [genesis]).compiled_identity
        )

    def test_reordering_arg_sorts_is_a_redefinition(self, parse, testing_document):
        # The converse, and the reason the two cannot be canonicalized alike:
        # swapping the slots of `affects` says something different about the world.
        genesis = parse(testing_document)
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["arg_sorts"] = list(reversed(operators["affects"]["arg_sorts"]))
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(self._successor(testing_document, genesis, operators), predecessor=genesis)


class TestResolution:
    """§7.5: ProfileSpec resolves, contracts authorize."""

    def test_local_names_are_resolved_to_term_identifiers(self, base_contract, testing):
        operator = compile_profile(base_contract, [testing]).operator("testing/affects")
        assert operator.arg_sorts == ("testing/entity", "testing/outcome")
        assert operator.dimensions == ("testing/population", "testing/setting")

    def test_a_dimensions_restriction_sort_is_resolved(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert profile.dimensions["testing/population"].restriction_sort == "testing/cohort"

    def test_same_local_names_in_different_namespaces_compose(self, base_contract, testing, other):
        # D §8's rule for facets, and the same one here.
        profile = compile_profile(base_contract, [testing, other])
        assert profile.operator("testing/affects").contract == "testing"
        assert profile.operator("elsewhere/affects").contract == "elsewhere"

    def test_two_contracts_in_one_namespace_are_refused(self, base_contract, testing, parse, testing_document):
        twin = parse(copy.deepcopy(testing_document))
        with pytest.raises(DuplicateContribution, match="never last-writer-wins"):
            compile_profile(base_contract, [testing, twin])

    def test_an_absent_operator_refuses_locally(self, base_contract, testing):
        # §7.4 row 4a: local and static, so it refuses here and nothing is minted.
        with pytest.raises(ProfileError, match="no operator"):
            compile_profile(base_contract, [testing]).operator("testing/nowhere")


class TestRetirementIsAnAuthoringProperty:
    """§7.3a: retirement lives in authoring, never in validation."""

    @pytest.fixture()
    def with_retired(self, parse, testing_document, testing):
        retired = copy.deepcopy(testing_document)
        retired["operators"]["affects"]["retired"] = True
        retired["lineage"] = {"successor": testing.content_identity}
        retired["version"] = 2
        return parse(retired, predecessor=testing)

    def test_a_retired_operator_stays_resolvable(self, base_contract, with_retired):
        # decode / import / restore type a historical claim against the frozen
        # retired declaration. Refusing here would corrupt exactly the history
        # retirement exists to preserve.
        profile = compile_profile(base_contract, [with_retired])
        assert profile.operator("testing/affects").retired is True

    def test_a_retired_operator_is_not_offered_for_authoring(self, base_contract, with_retired):
        profile = compile_profile(base_contract, [with_retired])
        assert "testing/affects" not in profile.authorable_operators()
        assert "testing/subtype-of" in profile.authorable_operators()


class TestTheProfileIsCompiledNeverAuthored:
    """M7's first clause has a second half the first pass missed.

    "No second authored operator artifact" is not only about a roster module. A
    `ProfileSpec` a caller can build field-wise, or mutate after the fact, *is* an
    authored profile — and a mutated one carries a `compiled_identity` describing
    a profile that no longer exists, which is `KIND_DESCRIPTORS`' drift with the
    two sources inside one object.
    """

    def test_the_field_wise_constructor_is_refused(self, base_contract, testing):
        compiled = compile_profile(base_contract, [testing])
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec(
                claim_grammar=compiled.claim_grammar,
                operators=dict(compiled.operators),
                dimensions=dict(compiled.dimensions),
                sorts=dict(compiled.sorts),
                base_contract_identity=compiled.base_contract_identity,
                activated_contracts=dict(compiled.activated_contracts),
                compiled_identity=compiled.compiled_identity,
            )

    def test_the_no_argument_constructor_is_refused_too(self):
        # Otherwise the field-wise route is closed and the empty one is not.
        with pytest.raises(ProfileError, match="compiled, never authored"):
            ProfileSpec()

    @pytest.mark.parametrize("section", ["operators", "dimensions", "sorts"])
    def test_the_mappings_are_read_only(self, base_contract, testing, other, section):
        profile = compile_profile(base_contract, [testing])
        mapping = getattr(profile, section)
        with pytest.raises(TypeError):
            mapping["forged"] = next(iter(getattr(compile_profile(base_contract, [other]), section).values()))
        with pytest.raises(TypeError):
            del mapping[next(iter(mapping))]

    def test_activated_contracts_is_read_only(self, base_contract, testing):
        with pytest.raises(TypeError):
            # Assigning into a Mapping is the point — the static type
            # forbids it and the test asks whether the run time does too.
            compile_profile(base_contract, [testing]).activated_contracts["forged"] = "f" * 64  # type: ignore[index]

    def test_the_profile_cannot_be_subclassed(self):
        # Same rule as `Claim`'s, for the same reason: a subclass could expose a
        # field-wise constructor and mint a spec whose `compiled_identity`
        # describes something else, while still passing isinstance().
        with pytest.raises(SubclassRefused):

            class Rogue(ProfileSpec):  # type: ignore[misc]  # the declaration is under test; see LaxReferent
                pass

    def test_the_fields_are_frozen(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        with pytest.raises(AttributeError):
            profile.compiled_identity = "forged"  # type: ignore[misc]


class TestActivationIsNotConsultation:
    """D6's conditional arm, guarded at the shape rather than in prose.

    The first pass carried one `contract_identities` mapping with the base
    contract folded in. Anything computing a digest from its values would have
    moved a belief because an unrelated domain was switched on — D6's negative
    arm, committed by the accessor rather than by the walk.
    """

    def test_the_unconditional_and_the_conditional_are_separate_fields(self, base_contract, testing, other):
        profile = compile_profile(base_contract, [testing, other])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {
            "testing": testing.content_identity,
            "elsewhere": other.content_identity,
        }

    def test_the_base_contract_is_not_among_the_activated(self, base_contract, testing):
        # Folding it in is what makes "take every value" look reasonable.
        profile = compile_profile(base_contract, [testing])
        assert base_contract.name not in profile.activated_contracts
        assert profile.base_contract_identity not in set(profile.activated_contracts.values())

    def test_the_base_contract_identity_survives_an_empty_profile(self, base_contract):
        # D §8: membership is unconditional, so no walk may be able to omit it.
        profile = compile_profile(base_contract, [])
        assert profile.base_contract_identity == base_contract.content_identity
        assert profile.activated_contracts == {}

    def test_no_member_offers_a_consulted_set(self, base_contract, testing):
        # Belief is outside cut 1. A member named for the consulted set would be
        # a placeholder that computes the activated one, which is the collapse.
        profile = compile_profile(base_contract, [testing])
        assert not [name for name in dir(profile) if "consult" in name.lower()]

    def test_the_compiled_identity_is_not_a_contract_identity(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert profile.compiled_identity != profile.base_contract_identity
        assert profile.compiled_identity not in set(profile.activated_contracts.values())


class TestRetirementReachesThroughSorts:
    """§7.3a's authoring boundary, applied to every route into it.

    Checking only the operator's own `retired` flag leaves an operator offered
    whose slots cannot be filled — the refusal then lands when the author tries
    to bind a referent, one step past the boundary §7.3a draws.
    """

    @pytest.fixture()
    def retire(self, parse, testing_document, base_contract):
        def _retire(section, name):
            genesis = parse(testing_document)
            document = copy.deepcopy(testing_document)
            document[section][name]["retired"] = True
            document["lineage"] = {"successor": genesis.content_identity}
            document["version"] = 2
            return compile_profile(base_contract, [parse(document, predecessor=genesis)])

        return _retire

    def test_retiring_an_argument_sort_withdraws_the_operator(self, retire):
        profile = retire("sorts", "outcome")  # affects : entity x outcome
        assert "testing/affects" not in profile.authorable_operators()
        assert "testing/subtype-of" in profile.authorable_operators()  # entity x entity

    def test_the_withdrawn_operator_stays_resolvable_for_decode(self, retire):
        # Historical claims are typed against the frozen declaration; refusing
        # here would corrupt the history retirement exists to preserve.
        profile = retire("sorts", "outcome")
        assert profile.operator("testing/affects").retired is False

    def test_retiring_the_operator_itself_still_withdraws_it(self, retire):
        assert "testing/affects" not in retire("operators", "affects").authorable_operators()

    def test_a_withdrawn_operator_offers_no_dimensions_at_all(self, retire):
        # Not an empty tuple: `subtype-of` legitimately returns one, so an empty
        # answer here would make "withdrawn" and "permits none" the same fact.
        for section, name, reason in [
            ("operators", "affects", "the operator is retired"),
            ("sorts", "outcome", "argument sorts"),
        ]:
            profile = retire(section, name)
            with pytest.raises(WithdrawnFromAuthoring, match=reason):
                profile.authorable_dimensions("testing/affects")

    def test_an_unresolvable_operator_is_not_a_withdrawn_one(self, base_contract, testing):
        # Two different facts, and the profile must not answer one with the other.
        profile = compile_profile(base_contract, [testing])
        with pytest.raises(ProfileError, match="no operator"):
            profile.authorable_dimensions("testing/absent")

    def test_retiring_a_permitted_dimension_withdraws_only_that_dimension(self, retire):
        # §6.2: Dims(op) is the set of dimensions *permitted*, not required, so
        # the operator remains authorable without it.
        profile = retire("dimensions", "setting")
        assert "testing/affects" in profile.authorable_operators()
        assert profile.authorable_dimensions("testing/affects") == ("testing/population",)

    def test_retiring_a_restriction_sort_withdraws_its_dimension(self, retire):
        # A restriction is sorted exactly as an argument is, so a retired
        # restriction sort leaves nothing selectable on that dimension.
        profile = retire("sorts", "cohort")  # population : restriction_sort cohort
        assert profile.authorable_dimensions("testing/affects") == ("testing/setting",)

    def test_nothing_is_withdrawn_when_nothing_is_retired(self, base_contract, testing):
        profile = compile_profile(base_contract, [testing])
        assert set(profile.authorable_operators()) == {
            f"testing/{name}" for name in ["affects", "subtype-of", "correlates-with", "measured-by"]
        }
        assert profile.authorable_dimensions("testing/affects") == ("testing/population", "testing/setting")
        assert profile.authorable_dimensions("testing/subtype-of") == ()


class TestTheTrustChainStartsAtTheDocument:
    """The link above the profile, and the one that decides whether the rest mean anything.

    ``ProfileSpec`` refuses to be authored, and that refusal certifies exactly one
    thing: ``compile_profile`` ran. It says nothing about what ``compile_profile``
    was handed. Before these checks a hand-built ``BaseContract`` and
    ``DomainContract`` compiled to an entirely genuine profile — resolving an
    operator, a sort and a layer that no document declares — and the claims typed
    against it were indistinguishable from real ones, agreeing byte-for-byte with
    the TypeScript implementation given the same forgery.

    Reported for TypeScript, found here by asking the same question of this
    language. The forgeries differ (there, an object literal; here, a dataclass
    constructor) and the hole is identical, which is the argument for asking every
    such question in both.
    """

    def test_an_authored_base_contract_cannot_be_constructed(self):
        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            base.BaseContract(
                name="science",
                version=1,
                claim_grammar=base.ClaimGrammar(1, ("generic",), ("positive",), "inapt", ("causal",)),
                content_identity="0" * 64,
            )

    def test_an_authored_domain_contract_cannot_be_constructed(self):
        with pytest.raises(UnparsedContract, match="parse_domain_contract"):
            domain.DomainContract(namespace="forged", version=1, predecessor=None)

    def test_neither_can_be_subclassed(self):
        # `_parsed` is reachable, so a subclass overriding nothing would still be
        # a route to an unparsed contract that passes isinstance().
        with pytest.raises(SubclassRefused):

            class RogueBase(base.BaseContract):  # type: ignore[misc]  # the declaration is under test
                pass

        with pytest.raises(SubclassRefused):

            class RogueDomain(domain.DomainContract):  # type: ignore[misc]
                pass

    def test_compilation_refuses_a_base_contract_no_parser_produced(self, testing):
        class Impostor:
            claim_grammar = base.ClaimGrammar(1, ("generic",), ("positive",), "inapt", ("causal",))
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            compile_profile(Impostor(), [testing])  # type: ignore[arg-type]

    def test_compilation_refuses_a_domain_contract_no_parser_produced(self, base_contract):
        class Impostor:
            namespace = "forged"
            sorts: ClassVar[dict] = {}
            dimensions: ClassVar[dict] = {}
            operators: ClassVar[dict] = {}
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_domain_contract"):
            compile_profile(base_contract, [Impostor()])  # type: ignore[list-item]

    def test_a_contract_cannot_be_edited_after_it_is_parsed(self, testing):
        # `content_identity` is derived from the document at parse time, so an
        # editable contract would carry an identity describing a document its own
        # contents no longer match — and recompile into a profile resolving
        # identifiers nobody declared.
        with pytest.raises(TypeError):
            testing.operators["smuggled"] = testing.operators["affects"]
        with pytest.raises(TypeError):
            del testing.sorts["entity"]
        with pytest.raises(FrozenInstanceError):
            testing.namespace = "forged"

    def test_the_parsed_contracts_are_the_ones_compilation_accepts(self, base_contract, testing):
        assert isinstance(base_contract, base.BaseContract)
        assert isinstance(testing, domain.DomainContract)
        assert compile_profile(base_contract, [testing]).activated_contracts == {"testing": testing.content_identity}


class TestTwoGenuineContractsThatDoNotBelongTogether:
    """Provenance is necessary and is not sufficient.

    Nothing in this class is forged. Every brand is intact, every parser ran on a
    real document, and the claim that came out stood on a layer the compiled base
    contract does not declare. A domain's layer selections are validated
    **once**, at parse time, against whatever base it was handed, and the
    compiled operator then carries them as facts that nothing revalidates.

    The general shape is worth more than the instance: authenticating each input
    separately says nothing about whether the inputs **belong together**. It
    applies to an artifact whose **validity is conditional** on a particular
    upstream artifact and which **may later be recombined independently** — both
    true of a domain contract, whose layers were checked against one base and
    which is handed to `compile_profile` separately from any base. Such a
    boundary must either verify a recorded dependency or revalidate the relation.
    A stage that rechecks its inputs owes neither, which is why this is not a
    demand that every transformation carry provenance.
    """

    @pytest.fixture()
    def wide_base(self, base_contract_path):
        document = copy.deepcopy(yaml.safe_load(base_contract_path.read_text(encoding="utf-8")))
        document["claim_grammar"]["layers"] = [*document["claim_grammar"]["layers"], "speculative"]
        return base.parse_base_contract(document, source="<wide>")

    @pytest.fixture()
    def speculative_document(self, testing_document):
        document = copy.deepcopy(testing_document)
        document["operators"]["affects"]["layers"] = ["causal", "speculative"]
        return document

    def test_a_domain_parsed_under_another_base_is_refused(self, base_contract, wide_base, speculative_document):
        under_wide = domain.parse_domain_contract(
            speculative_document, source="<testing>", base=wide_base, predecessor=None
        )
        assert "speculative" in under_wide.operators["affects"].layers
        with pytest.raises(ContractMismatch, match="typed against base contract"):
            compile_profile(base_contract, [under_wide])

    def test_it_compiles_under_the_base_it_was_parsed_against(self, wide_base, speculative_document):
        under_wide = domain.parse_domain_contract(
            speculative_document, source="<testing>", base=wide_base, predecessor=None
        )
        claim = build_claim(
            compile_profile(wide_base, [under_wide]),
            operator="testing/affects",
            args=(Referent(sort="testing/entity", term="EX:g"), Referent(sort="testing/outcome", term="EX:o")),
            layer="speculative",
            polarity="positive",
        )
        assert claim.layer == "speculative"

    def test_the_domain_records_the_base_it_was_typed_against(self, base_contract, testing):
        assert testing.base_identity == base_contract.content_identity

    def test_the_domain_parser_authenticates_its_base(self, testing_document):
        class Impostor:
            name = "science"
            claim_grammar = base.ClaimGrammar(1, ("generic",), ("positive",), "inapt", ("causal",))
            content_identity = "0" * 64

        with pytest.raises(UnparsedContract, match="parse_base_contract"):
            domain.parse_domain_contract(testing_document, source="<t>", base=Impostor(), predecessor=None)  # type: ignore[arg-type]

    def test_the_domain_parser_authenticates_its_predecessor(self, base_contract, testing_document):
        # Succession is the *never redefine* rule made checkable (§8.3). Checked
        # against an authored predecessor it certifies nothing, because the thing
        # it compares against was written to pass.
        successor = copy.deepcopy(testing_document)
        successor["version"] = 2
        successor["lineage"] = {"successor": "0" * 64}

        class Impostor:
            namespace = "testing"
            content_identity = "0" * 64

            def claim_vocabulary(self):
                return {}

            def retired_identifiers(self):
                return frozenset()

        with pytest.raises(UnparsedContract, match="predecessor"):
            domain.parse_domain_contract(
                successor,
                source="<t>",
                base=base_contract,
                predecessor=Impostor(),  # type: ignore[arg-type]
            )


class TestTheOrdinaryRouteToAnUnparsedArtifact:
    """``_parsed`` and ``_compiled`` are the parsers' own routes, not internal by convention.

    **What a token achieves here is less than the TypeScript brand achieves
    there, and the difference is a language's and not a design's.** A private
    field cannot be installed from outside its class body in JavaScript — the
    forgery is impossible. Python has no module privacy, and
    ``object.__new__`` plus ``object.__setattr__`` reproduces any of these
    methods in two lines. So these tests do not assert that provenance is
    unforgeable here; they assert that reaching an unparsed artifact requires
    reaching for the audit surface §6.3's third row already names, rather than
    calling a method that merely looked internal.
    """

    def test_a_base_contract_cannot_be_minted_without_the_parser_token(self):
        with pytest.raises(UnparsedContract, match="mint token"):
            base.BaseContract._parsed(
                object(),
                name="science",
                version=1,
                claim_grammar=base.ClaimGrammar(1, ("generic",), ("positive",), "inapt", ("causal",)),
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
                operators={},
                facets={},
                content_identity="0" * 64,
                base_identity="0" * 64,
            )

    def test_a_profile_cannot_be_minted_without_the_compiler_token(self):
        with pytest.raises(ProfileError, match="mint token"):
            ProfileSpec._compiled(object(), claim_grammar=None, operators={}, dimensions={}, sorts={})

    def test_the_raw_write_remains_and_is_the_audit_surface(self, base_contract):
        # Recorded rather than asserted away. This is §6.3's third row — the
        # boundary bypassed, not defeated — and it is the reason the tokens above
        # are described as removing an ordinary route rather than closing a hole.
        forged = object.__new__(base.BaseContract)
        object.__setattr__(forged, "content_identity", "0" * 64)
        assert isinstance(forged, base.BaseContract)


class TestTheClaimConstructorAuthenticatesItsProfile:
    """The Python twin of a hole reported against TypeScript and fixed there only.

    `ProfileSpec` is sealed and refuses to be authored, so this is not about a
    second `ProfileSpec` — it is about a **duck**. Every check a claim passes is
    read out of the profile object, so an impostor exposing `operator`,
    `claim_grammar` and `authorable_dimensions` types a claim against
    declarations of its own choosing, and the `Claim` that results is entirely
    genuine.
    """

    class Impostor:
        claim_grammar = base.ClaimGrammar(1, ("generic",), ("yes",), "no", ("made-up",))
        dimensions: ClassVar[dict] = {}

        def authorable_dimensions(self, term):
            return ()

        def operator(self, term):
            from beliefs.profile import CompiledOperator

            return CompiledOperator(
                term="forged/op",
                arity=1,
                arg_sorts=("forged/sort",),
                sign_apt=True,
                layers=("made-up",),
                dimensions=(),
                retired=False,
                contract="forged",
            )

    def test_build_claim_refuses_an_impostor(self):
        with pytest.raises(ProfileError, match="compile_profile"):
            build_claim(
                self.Impostor(),  # type: ignore[arg-type]
                operator="forged/op",
                args=(Referent(sort="forged/sort", term="X:1"),),
                layer="made-up",
                polarity="yes",
            )

    def test_the_decode_route_refuses_it_too(self):
        # `Claim._checked` is the other entry point, and decode will call it
        # directly. A check on one of two entry points is a check on neither.
        from beliefs.claim import Claim

        with pytest.raises(ProfileError, match="compile_profile"):
            Claim._checked(
                self.Impostor(),  # type: ignore[arg-type]
                operator="forged/op",
                args=(Referent(sort="forged/sort", term="X:1"),),
                qualifiers={},
                polarity="yes",
                layer="made-up",
            )
