"""``Claim`` — opacity, the validated constructor, and the authoring boundary.

The profile-dependent refusals below are shared by the authoring route
(`build_claim`) and by decode (`Claim._checked`); they are exercised through the
authoring route, and the retirement tests assert that `_checked` without
`authoring` admits what `build_claim` refuses. One test per step of the typing
rule, each refused **distinctly**: a single collapsed error would let one check
cover for another's absence.
"""

import copy
import dataclasses
import unicodedata

import pytest

import beliefs.claim as claim_module
from beliefs.claim import Claim, Member, Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.errors import (
    ClaimError,
    CoefficientRefused,
    DimensionNotClaimSide,
    DuplicateMember,
    FormRefused,
    IdentifierClassMismatch,
    InadmissibleLayer,
    MalformedReferent,
    PolarityRefused,
    ProfileError,
    RestrictionSortMismatch,
    RoleRefused,
    SubclassRefused,
    UndeclaredDimension,
    UndeclaredSort,
    UninstantiatedTemplate,
    UnknownQuantifier,
    UntypedQualifier,
    UntypedReferent,
    WithdrawnFromAuthoring,
    WithinModelRefused,
)
from beliefs.profile import compile_profile

AFFECTS = "testing/affects"
CORRELATES = "testing/correlates-with"
TRANSFORMS = "testing/transforms"
MEASURED_BY = "testing/measured-by"
PROMOTES = "testing/promotes"
POPULATION = "testing/population"
SETTING = "testing/setting"
FOLLOW_UP = "testing/follow-up"
MODEL = Referent(sort="testing/procedure-spec", term="procedure:" + "a" * 64)


@pytest.fixture()
def parse(base_contract):
    def _parse(document, predecessor=None):
        return domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=predecessor)

    return _parse


@pytest.fixture()
def profile(base_contract, parse, testing_document):
    return compile_profile(base_contract, [parse(testing_document)])


@pytest.fixture()
def retire(base_contract, parse, testing_document):
    """A profile compiled from a successor that retires one declaration."""

    def _retire(section, name):
        genesis = parse(testing_document)
        document = copy.deepcopy(testing_document)
        document[section][name]["retired"] = True
        document["lineage"] = {"successor": genesis.content_identity}
        document["version"] = 2
        return compile_profile(base_contract, [parse(document, predecessor=genesis)])

    return _retire


@pytest.fixture()
def gene():
    return Referent(sort="testing/entity", term="EX:gene-x")


@pytest.fixture()
def other_gene():
    return Referent(sort="testing/entity", term="EX:gene-z")


@pytest.fixture()
def outcome():
    return Referent(sort="testing/outcome", term="EX:outcome-y")


@pytest.fixture()
def method():
    return Referent(sort="testing/method", term="EX:assay")


@pytest.fixture()
def adults():
    return Referent(sort="testing/cohort", term="EX:adults")


@pytest.fixture()
def cause_effect(gene, outcome):
    return {"cause": gene, "effect": outcome}


@pytest.fixture()
def affects(profile, cause_effect):
    return build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="positive", layer="causal")


@pytest.fixture()
def measured(gene, method):
    """The roles of a sign-inapt `measured-by` claim."""
    return {"subject": gene, "instrument": method}


class TestTheOnlyRouteIsTheValidatedConstructor:
    """The first clause: `Claim` cannot be built from ambient data."""

    def test_the_field_wise_constructor_is_refused(self, cause_effect):
        with pytest.raises(ClaimError, match="use build_claim"):
            Claim(AFFECTS, cause_effect, {}, "polar", "positive", "causal")  # type: ignore[call-arg]

    def test_the_no_argument_constructor_is_refused_too(self):
        # Closing one arity and leaving the other open moves the door, it does
        # not shut it.
        with pytest.raises(ClaimError):
            Claim()  # type: ignore[call-arg]

    def test_there_is_no_mapping_route(self, affects):
        fields = {field.name: getattr(affects, field.name) for field in dataclasses.fields(affects)}
        with pytest.raises(ClaimError):
            Claim(**fields)  # type: ignore[arg-type]

    def test_replace_is_refused(self, affects):
        # `dataclasses.replace` re-enters `__init__`, so a claim cannot be
        # rebuilt with one field swapped and no re-check.
        with pytest.raises(ClaimError):
            dataclasses.replace(affects, polarity="negative")

    def test_no_alternate_constructor_is_exported(self):
        builders = [name for name in claim_module.__all__ if name.islower()]
        # `canonical_members` and `member_key` build no Claim: they order and key a role's members.
        assert builders == ["build_claim", "canonical_members", "member_key"]

    def test_the_type_offers_no_coercion(self):
        # A `from_*` classmethod is how the wire type gets a second route in.
        assert not [name for name in dir(Claim) if name.startswith("from_")]

    def test_the_fields_are_frozen(self, affects):
        with pytest.raises(dataclasses.FrozenInstanceError):
            affects.polarity = "negative"  # type: ignore[misc]

    def test_the_roles_and_qualifiers_are_read_only(self, profile, cause_effect, gene, adults):
        claim = build_claim(
            profile,
            operator=AFFECTS,
            roles=cause_effect,
            qualifiers={POPULATION: Qualifier("generic", adults)},
            polarity="positive",
            layer="causal",
        )
        with pytest.raises(TypeError):
            claim.qualifiers[SETTING] = Qualifier("generic", gene)  # type: ignore[index]
        with pytest.raises(TypeError):
            claim.roles["cause"] = gene  # type: ignore[index]

    def test_the_caller_cannot_reach_what_it_passed_in(self, profile, gene, other_gene, adults):
        # The mutable handles a caller genuinely holds: the dicts and the member list it supplied.
        authored = {POPULATION: Qualifier("generic", adults)}
        inputs = [Member(gene)]
        roles = {"inputs": inputs, "outputs": [Member(other_gene)], "facilitators": []}
        claim = build_claim(profile, operator=TRANSFORMS, roles=roles, qualifiers={}, layer="structural")
        roles["facilitators"] = [Member(gene)]
        inputs.append(Member(other_gene))
        assert claim.roles["facilitators"] == ()
        assert claim.roles["inputs"] == (Member(gene),)
        restricted = build_claim(
            profile,
            operator=AFFECTS,
            roles={"cause": gene, "effect": other_gene},
            qualifiers=authored,
            polarity="positive",
            layer="causal",
        )
        authored[SETTING] = Qualifier("generic", gene)
        assert set(restricted.qualifiers) == {POPULATION}


class TestTheValueTypesOwnTheirInvariants:
    """What `isinstance` has to be worth for the opacity above to mean anything.

    Each gap here produces a **trusted** `Claim` — one that came through the
    boundary — holding something that is not a claim's content. Refusing at the
    boundary is not enough if the values it admits can be malformed or faked.
    """

    @pytest.mark.parametrize("term", [123, None, b"EX:gene-x", "", ("EX:gene-x",)])
    def test_a_referent_term_must_be_an_identifier(self, term):
        with pytest.raises(MalformedReferent):
            Referent(sort="testing/entity", term=term)

    @pytest.mark.parametrize("sort", [123, None, ""])
    def test_a_referent_sort_must_be_an_identifier(self, sort):
        with pytest.raises(MalformedReferent):
            Referent(sort=sort, term="EX:gene-x")

    def test_a_qualifier_restriction_must_be_a_referent(self):
        with pytest.raises(UntypedReferent):
            Qualifier("generic", "EX:adults")  # type: ignore[arg-type]

    def test_a_qualifier_impostor_is_refused(self, profile, cause_effect, adults):
        # Structural typing would admit this: it has both attributes, and both
        # hold the right types. It is refused because it is not a `Qualifier`.
        @dataclasses.dataclass(frozen=True)
        class Impostor:
            quantifier: str
            restriction: Referent

        with pytest.raises(UntypedQualifier):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Impostor("generic", adults)},  # type: ignore[dict-item]
                polarity="positive",
                layer="causal",
            )

    @pytest.mark.parametrize("closed", [Claim, Referent, Member, Qualifier])
    def test_the_claim_types_cannot_be_subclassed(self, closed):
        # A subclass could expose a raw constructor and mint an unchecked object
        # that still satisfies isinstance(x, Claim) — at which point every reader
        # trusting a Claim unconditionally is wrong, with nothing here edited.
        with pytest.raises(SubclassRefused):

            class Rogue(closed):
                pass

    def test_a_subclass_cannot_be_smuggled_in_through_a_value(self):
        # The transitive case: `Claim`'s contents are identifiers only because
        # `Referent` says so, so sealing `Claim` alone would leave the invariant
        # reachable one level down.
        with pytest.raises(SubclassRefused):

            class LaxReferent(Referent):  # type: ignore[misc]
                def __post_init__(self) -> None:
                    return None


class TestTheChecksFollowTheTypingRule:
    """§5.6, one test per step, in order."""

    def test_an_unresolvable_operator_refuses(self, profile, cause_effect):
        # Step 1. A local, static failure — and *not* a ClaimError: nothing is
        # wrong with the claim as written; the profile cannot resolve what it names.
        with pytest.raises(ProfileError, match="no operator"):
            build_claim(profile, operator="testing/absent", roles=cause_effect, polarity="positive", layer="causal")

    def test_missing_role_refuses(self, profile, gene):
        with pytest.raises(RoleRefused, match="effect"):
            build_claim(profile, operator=AFFECTS, roles={"cause": gene}, polarity="positive", layer="causal")

    def test_undeclared_role_refuses(self, profile, cause_effect, gene):
        with pytest.raises(RoleRefused, match="bystander"):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={**cause_effect, "bystander": gene},
                polarity="positive",
                layer="causal",
            )

    def test_roles_are_a_mapping_never_a_sequence(self, profile, gene, outcome):
        with pytest.raises(RoleRefused, match="mapping"):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=(gene, outcome),  # type: ignore[arg-type]
                polarity="positive",
                layer="causal",
            )

    def test_a_bare_string_cannot_fill_a_one_role(self, profile, outcome):
        # A string has no sort, so there is nothing to check against the role's.
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": "EX:gene-x", "effect": outcome},  # type: ignore[dict-item]
                polarity="positive",
                layer="causal",
            )

    def test_members_cannot_fill_a_one_role(self, profile, gene, outcome):
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": [Member(gene)], "effect": outcome},
                polarity="positive",
                layer="causal",
            )

    @pytest.mark.parametrize("filling", ["referent", "string", "referents"])
    def test_a_many_role_holds_members(self, profile, gene, outcome, filling):
        value = {"referent": gene, "string": "EX:gene-x", "referents": [gene, outcome]}[filling]
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=CORRELATES,
                roles={"parties": value},  # type: ignore[dict-item]
                polarity="positive",
                layer="statistical",
            )

    @pytest.mark.parametrize("count", [1, 3])
    def test_member_count_outside_bounds_refuses(self, profile, count):
        members = [Member(Referent("testing/entity", f"EX:gene-{i}")) for i in range(count)]
        with pytest.raises(RoleRefused, match=r"\[2, 2\]"):
            build_claim(
                profile, operator=CORRELATES, roles={"parties": members}, polarity="positive", layer="statistical"
            )

    def test_min_one_role_refuses_empty(self, profile, gene):
        with pytest.raises(RoleRefused, match="inputs"):
            build_claim(
                profile,
                operator=TRANSFORMS,
                roles={"inputs": [], "outputs": [Member(gene)], "facilitators": []},
                layer="structural",
            )

    def test_coefficient_on_role_without_coefficients_refuses(self, profile, gene, other_gene, outcome):
        with pytest.raises(CoefficientRefused):
            build_claim(
                profile,
                operator=CORRELATES,
                roles={"parties": [Member(gene, 2), Member(outcome)]},
                polarity="positive",
                layer="statistical",
            )
        with pytest.raises(CoefficientRefused):
            build_claim(
                profile,
                operator=TRANSFORMS,
                roles={"inputs": [Member(gene)], "outputs": [Member(other_gene)], "facilitators": [Member(gene, 2)]},
                layer="structural",
            )
        admitted = build_claim(
            profile,
            operator=TRANSFORMS,
            roles={"inputs": [Member(gene, 2)], "outputs": [Member(other_gene, 3)], "facilitators": []},
            layer="structural",
        )
        assert admitted.roles["inputs"] == (Member(gene, 2),)

    def test_duplicate_member_by_nfc_key_refuses(self, profile):
        composed = Referent("testing/event", unicodedata.normalize("NFC", "EX:café"))
        decomposed = Referent("testing/event", unicodedata.normalize("NFD", "EX:café"))
        assert composed.term != decomposed.term
        with pytest.raises(DuplicateMember):
            build_claim(
                profile,
                operator=CORRELATES,
                roles={"parties": [Member(composed), Member(decomposed)]},
                polarity="positive",
                layer="statistical",
            )

    def test_undeclared_sort_refuses(self, profile, outcome):
        with pytest.raises(UndeclaredSort):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": Referent("testing/absent", "EX:gene-x"), "effect": outcome},
                polarity="positive",
                layer="causal",
            )

    def test_an_undeclared_restriction_sort_refuses_too(self, profile, cause_effect):
        with pytest.raises(UndeclaredSort):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Qualifier("generic", Referent("testing/absent", "EX:adults"))},
                polarity="positive",
                layer="causal",
            )

    def test_identifier_class_mismatch_refuses(self, profile, gene, outcome):
        # Case 5: `EX:ABC` is outside entity's narrow class and inside cohort's
        # wide one, and step 4 covers every referent, restrictions included.
        with pytest.raises(IdentifierClassMismatch, match="EX:ABC"):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": Referent("testing/entity", "EX:ABC"), "effect": outcome},
                polarity="positive",
                layer="causal",
            )
        accepted = build_claim(
            profile,
            operator=AFFECTS,
            roles={"cause": gene, "effect": outcome},
            qualifiers={POPULATION: Qualifier("generic", Referent("testing/cohort", "EX:ABC"))},
            polarity="positive",
            layer="causal",
        )
        assert accepted.qualifiers[POPULATION].restriction.term == "EX:ABC"
        with pytest.raises(IdentifierClassMismatch):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": gene, "effect": outcome},
                qualifiers={POPULATION: Qualifier("generic", Referent("testing/cohort", "OTHER:ABC"))},
                polarity="positive",
                layer="causal",
            )

    def test_a_world_kind_sort_takes_the_record_id_grammar(self, profile, cause_effect):
        for term in ["procedure:" + "A" * 64, "procedure:" + "a" * 63, "run:" + "a" * 64]:
            with pytest.raises(IdentifierClassMismatch):
                build_claim(
                    profile,
                    operator=AFFECTS,
                    roles={**cause_effect, "within-model": Referent("testing/procedure-spec", term)},
                    polarity="positive",
                    layer="causal",
                )

    def test_uninstantiated_assignment_refuses(self, profile, outcome):
        with pytest.raises(UninstantiatedTemplate):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={"cause": outcome, "effect": outcome},
                polarity="positive",
                layer="causal",
            )

    def test_a_bridge_admits_by_its_own_role_sorts(self, profile, gene):
        # `affects-entity-entity` admits `effect: entity` on the template; the
        # bridge lists only `outcome`, so the same assignment refuses on it.
        build_claim(
            profile, operator=AFFECTS, roles={"cause": gene, "effect": gene}, polarity="positive", layer="causal"
        )
        with pytest.raises(UninstantiatedTemplate, match="^bridge"):
            build_claim(
                profile, operator=PROMOTES, roles={"cause": gene, "effect": gene}, polarity="positive", layer="causal"
            )

    def test_two_instantiations_admit(self, profile, affects):
        # Case 4 / R7: both instantiations of `affects` list entity → outcome.
        assert profile.admitting(AFFECTS, affects.assignment(), authoring=True) == (
            "instantiation:testing/affects-entity-entity",
            "instantiation:testing/affects-entity-outcome",
        )
        assert affects.assignment() == {
            "cause": frozenset({"testing/entity"}),
            "effect": frozenset({"testing/outcome"}),
        }

    def test_a_many_role_admits_by_every_members_sort(self, profile, gene, outcome):
        claim = build_claim(
            profile,
            operator=CORRELATES,
            roles={"parties": [Member(outcome), Member(gene)]},
            polarity="positive",
            layer="statistical",
        )
        assert claim.assignment() == {"parties": frozenset({"testing/entity", "testing/outcome"})}
        mixed = [Member(gene), Member(Referent("testing/event", "EX:event-1"))]
        with pytest.raises(UninstantiatedTemplate):
            build_claim(
                profile, operator=CORRELATES, roles={"parties": mixed}, polarity="positive", layer="statistical"
            )

    def test_applicability_dimension_in_qualifiers_refuses(self, profile, cause_effect):
        with pytest.raises(DimensionNotClaimSide):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={FOLLOW_UP: Qualifier("generic", Referent("testing/level", "EX:week-12"))},
                polarity="positive",
                layer="causal",
            )

    def test_dimension_not_applying_to_operator_refuses(self, profile, gene, outcome):
        with pytest.raises(UndeclaredDimension, match="does not apply"):
            build_claim(
                profile,
                operator=CORRELATES,
                roles={"parties": [Member(gene), Member(outcome)]},
                qualifiers={SETTING: Qualifier("generic", gene)},
                polarity="positive",
                layer="statistical",
            )

    def test_an_undeclared_dimension_refuses(self, profile, cause_effect, adults):
        with pytest.raises(UndeclaredDimension, match="no dimension"):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={"testing/absent": Qualifier("generic", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_a_foreign_dimension_applying_to_the_operator_is_admitted(
        self, base_contract, parse, testing_document, crossing_document, gene
    ):
        # Review Focus 4: `crossing/scope` is declared in another contract than
        # `testing/affects` and names it in `applies_to`.
        profile = compile_profile(base_contract, [parse(testing_document), parse(crossing_document)])
        local = Referent("crossing/local-entity", "EX:local-1")
        claim = build_claim(
            profile,
            operator=AFFECTS,
            roles={"cause": gene, "effect": local},
            qualifiers={"crossing/scope": Qualifier("generic", Referent("testing/cohort", "EX:adults"))},
            polarity="positive",
            layer="causal",
        )
        assert set(claim.qualifiers) == {"crossing/scope"}
        assert profile.admitting(AFFECTS, claim.assignment(), authoring=True) == (
            "instantiation:crossing/affects-local-entity",
        )

    def test_a_wrongly_sorted_restriction_refuses(self, profile, cause_effect, gene):
        with pytest.raises(RestrictionSortMismatch):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Qualifier("generic", gene)},  # population restricts to cohort
                polarity="positive",
                layer="causal",
            )

    def test_a_quantifier_outside_the_closed_set_refuses(self, profile, cause_effect, adults):
        with pytest.raises(UnknownQuantifier):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Qualifier("mostly", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_null_form_requires_declaration_and_sign_aptness(self, profile, base_contract, cause_effect, measured):
        # Case 6. `measured-by` is sign-inapt and declares only `polar`.
        with pytest.raises(FormRefused):
            build_claim(profile, operator=MEASURED_BY, roles=measured, form="null", layer="methodological")
        with pytest.raises(FormRefused):
            build_claim(profile, operator=AFFECTS, roles=cause_effect, form="absent", layer="causal")
        null = build_claim(profile, operator=AFFECTS, roles=cause_effect, form="null", layer="causal")
        assert null.form == "null"
        assert null.polarity == base_contract.claim_grammar.sign_inapt_tag
        for supplied in ["positive", "unsigned", base_contract.claim_grammar.sign_inapt_tag]:
            with pytest.raises(PolarityRefused):
                build_claim(
                    profile, operator=AFFECTS, roles=cause_effect, form="null", polarity=supplied, layer="causal"
                )

    def test_an_inadmissible_layer_refuses(self, profile, cause_effect, gene, outcome):
        with pytest.raises(InadmissibleLayer):
            build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="positive", layer="structural")
        # A bridge's layers are its own narrowing of its template's.
        with pytest.raises(InadmissibleLayer):
            build_claim(
                profile,
                operator=PROMOTES,
                roles={"cause": gene, "effect": outcome},
                polarity="positive",
                layer="statistical",
            )

    def test_within_model_on_template_and_on_bridge(self, profile, cause_effect, gene):
        # Review Focus 5: the kernel admits the reserved role on every operator,
        # on a template whose roles are all filled and on a bridge alike.
        on_template = build_claim(
            profile,
            operator=AFFECTS,
            roles={**cause_effect, "within-model": MODEL},
            polarity="positive",
            layer="causal",
        )
        on_bridge = build_claim(
            profile,
            operator=PROMOTES,
            roles={**cause_effect, "within-model": MODEL},
            polarity="positive",
            layer="causal",
        )
        assert on_template.roles["within-model"] == MODEL
        assert on_bridge.roles["within-model"] == MODEL
        assert "within-model" not in on_template.assignment()
        with pytest.raises(WithinModelRefused):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={**cause_effect, "within-model": Referent("testing/entity", "EX:model-x")},
                polarity="positive",
                layer="causal",
            )
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=AFFECTS,
                roles={**cause_effect, "within-model": [Member(MODEL)]},
                polarity="positive",
                layer="causal",
            )

    def test_min_zero_role_builds_empty(self, profile, gene, other_gene):
        claim = build_claim(
            profile,
            operator=TRANSFORMS,
            roles={"inputs": [Member(gene)], "outputs": [Member(other_gene)], "facilitators": []},
            layer="structural",
        )
        assert claim.roles["facilitators"] == ()
        assert claim.assignment()["facilitators"] == frozenset()

    def test_a_many_role_is_held_in_canonical_order(self, profile, gene, outcome):
        forward = build_claim(
            profile,
            operator=CORRELATES,
            roles={"parties": [Member(gene), Member(outcome)]},
            polarity="positive",
            layer="statistical",
        )
        reverse = build_claim(
            profile,
            operator=CORRELATES,
            roles={"parties": (Member(outcome), Member(gene))},
            polarity="positive",
            layer="statistical",
        )
        assert forward.roles == reverse.roles
        assert forward.roles["parties"] == (Member(gene), Member(outcome))

    def test_a_well_formed_claim_is_accepted_whole(self, profile, cause_effect, gene, outcome, adults):
        claim = build_claim(
            profile,
            operator=AFFECTS,
            roles=cause_effect,
            qualifiers={POPULATION: Qualifier("universal", adults)},
            polarity="negative",
            layer="causal",
        )
        assert claim.operator == AFFECTS
        assert claim.roles == {"cause": gene, "effect": outcome}
        assert claim.qualifiers == {POPULATION: Qualifier("universal", adults)}
        assert claim.form == "polar"
        assert claim.polarity == "negative"
        assert claim.layer == "causal"


class TestPolarityIsTheUnitInhabitantWhenTheOperatorHasNoSign:
    """`inapt` and `unsigned` are different facts."""

    def test_a_sign_inapt_operator_carries_the_inapt_tag(self, profile, base_contract, measured):
        claim = build_claim(profile, operator=MEASURED_BY, roles=measured, layer="methodological")
        assert claim.polarity == base_contract.claim_grammar.sign_inapt_tag
        assert claim.polarity not in base_contract.claim_grammar.polarities

    def test_a_sign_on_a_sign_inapt_operator_refuses(self, profile, measured):
        with pytest.raises(PolarityRefused, match="unit type"):
            build_claim(profile, operator=MEASURED_BY, roles=measured, polarity="positive", layer="methodological")

    def test_unsigned_is_not_a_way_to_say_inapt(self, profile, measured):
        # The collapse refused: `unsigned` says the operator has a sign and
        # this claim asserts none.
        with pytest.raises(PolarityRefused):
            build_claim(profile, operator=MEASURED_BY, roles=measured, polarity="unsigned", layer="methodological")

    def test_the_inapt_tag_cannot_be_supplied_by_hand_either(self, profile, base_contract, measured):
        inapt = base_contract.claim_grammar.sign_inapt_tag
        with pytest.raises(PolarityRefused):
            build_claim(profile, operator=MEASURED_BY, roles=measured, polarity=inapt, layer="methodological")

    def test_a_sign_apt_operator_requires_one(self, profile, cause_effect):
        with pytest.raises(PolarityRefused, match="sign-apt"):
            build_claim(profile, operator=AFFECTS, roles=cause_effect, layer="causal")

    def test_unsigned_is_available_where_the_operator_has_a_sign(self, profile, cause_effect):
        claim = build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="unsigned", layer="causal")
        assert claim.polarity == "unsigned"


class TestTheAuthoringBoundaryRefusesRetiredVocabulary:
    """The per-claim half. Every route by which retirement reaches an
    author is closed here; **none** of them reaches decode."""

    def test_a_retired_operator_cannot_be_authored(self, retire, cause_effect):
        profile = retire("templates", "affects")
        with pytest.raises(WithdrawnFromAuthoring, match="the operator is retired"):
            build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="positive", layer="causal")

    def test_a_retired_referent_sort_cannot_be_authored(self, retire, cause_effect):
        profile = retire("sorts", "outcome")
        with pytest.raises(WithdrawnFromAuthoring, match="testing/outcome"):
            build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="positive", layer="causal")

    def test_retired_instantiation_not_authorable_but_checked(self, retire, measured):
        # `measured-by-entity-method` is the only declaration admitting entity → method.
        profile = retire("instantiations", "measured-by-entity-method")
        with pytest.raises(WithdrawnFromAuthoring, match="only by retired"):
            build_claim(profile, operator=MEASURED_BY, roles=measured, layer="methodological")
        claim = Claim._checked(
            profile,
            operator=MEASURED_BY,
            roles=measured,
            qualifiers={},
            form="polar",
            polarity=None,
            layer="methodological",
        )
        assert claim.operator == MEASURED_BY

    def test_a_retired_dimension_cannot_be_selected(self, retire, cause_effect, adults):
        profile = retire("dimensions", "population")
        with pytest.raises(WithdrawnFromAuthoring, match=POPULATION):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Qualifier("generic", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_a_retired_restriction_sort_withdraws_its_dimension(self, retire, cause_effect, adults):
        profile = retire("sorts", "cohort")  # population restricts to cohort
        with pytest.raises(WithdrawnFromAuthoring):
            build_claim(
                profile,
                operator=AFFECTS,
                roles=cause_effect,
                qualifiers={POPULATION: Qualifier("generic", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_the_operator_stays_authorable_without_the_retired_dimension(self, retire, cause_effect):
        # A dimension's `applies_to` permits, it does not require, so retiring
        # one withdraws only itself.
        profile = retire("dimensions", "population")
        claim = build_claim(profile, operator=AFFECTS, roles=cause_effect, polarity="positive", layer="causal")
        assert claim.qualifiers == {}

    def test_an_undeclared_dimension_does_not_collapse_into_a_retired_one(self, retire, measured, adults):
        # Two different facts: never permitted, versus permitted and withdrawn.
        profile = retire("dimensions", "population")
        with pytest.raises(UndeclaredDimension):
            build_claim(
                profile,
                operator=MEASURED_BY,
                roles=measured,
                qualifiers={POPULATION: Qualifier("generic", adults)},
                layer="methodological",
            )

    def test_retirement_does_not_reach_the_seam_decode_will_use(self, retire, cause_effect, adults):
        # The rule above must not narrow the decode rule. Asserted against
        # `_checked` because that is the route `decodeClaim` takes, and
        # asserting it only through `build_claim` would assert the opposite.
        profile = retire("templates", "affects")
        claim = Claim._checked(
            profile,
            operator=AFFECTS,
            roles=cause_effect,
            qualifiers={POPULATION: Qualifier("generic", adults)},
            form="polar",
            polarity="positive",
            layer="causal",
        )
        assert claim.operator == AFFECTS

    def test_a_retired_restriction_sort_is_still_typed_at_that_seam(self, retire, cause_effect, adults):
        profile = retire("sorts", "cohort")
        claim = Claim._checked(
            profile,
            operator=AFFECTS,
            roles=cause_effect,
            qualifiers={POPULATION: Qualifier("generic", adults)},
            form="polar",
            polarity="positive",
            layer="causal",
        )
        assert claim.qualifiers[POPULATION].restriction == adults
