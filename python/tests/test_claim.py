"""``Claim`` — opacity, the validated constructor, and the authoring boundary.

**M13 in the half that exists.** Its second clause — *"no function downstream of
the boundary accepts a `WireClaim`"* — is **not** tested here, because
`WireClaim` does not exist yet: a scan for it today would pass by finding
nothing, which is a test that cannot fail. It lands with `decodeClaim`.

The profile-dependent refusals below are **M11's**, exercised through the
authoring route because it is the one that exists. M13's scope note is explicit
that sign-aptness, arity, argument sorts, permitted dimensions and admissible
layers are runtime and belong to M11; what is asserted *here* is that they
happen at construction and cannot be bypassed.
"""

import copy
import dataclasses

import pytest

import beliefs.claim as claim_module
from beliefs.claim import Claim, Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.errors import (
    ArgumentSortMismatch,
    ArityMismatch,
    ClaimError,
    InadmissibleLayer,
    MalformedReferent,
    PolarityRefused,
    ProfileError,
    RestrictionSortMismatch,
    SubclassRefused,
    UndeclaredDimension,
    UnknownQuantifier,
    UntypedQualifier,
    UntypedReferent,
    WithdrawnFromAuthoring,
)
from beliefs.profile import compile_profile

AFFECTS = "testing/affects"
SUBTYPE_OF = "testing/subtype-of"


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
def outcome():
    return Referent(sort="testing/outcome", term="EX:outcome-y")


@pytest.fixture()
def adults():
    return Referent(sort="testing/cohort", term="EX:adults")


@pytest.fixture()
def affects(profile, gene, outcome):
    return build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")


class TestTheOnlyRouteIsTheValidatedConstructor:
    """M13's first clause: `Claim` cannot be built from ambient data."""

    def test_the_field_wise_constructor_is_refused(self, gene, outcome):
        with pytest.raises(ClaimError, match="use build_claim"):
            Claim(AFFECTS, (gene, outcome), {}, "positive", "causal")  # type: ignore[call-arg]

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
        assert builders == ["build_claim"]

    def test_the_type_offers_no_coercion(self):
        # A `from_*` classmethod is how the wire type gets a second route in.
        assert not [name for name in dir(Claim) if name.startswith("from_")]

    def test_the_fields_are_frozen(self, affects):
        with pytest.raises(dataclasses.FrozenInstanceError):
            affects.polarity = "negative"  # type: ignore[misc]

    def test_the_qualifiers_are_read_only(self, profile, gene, outcome, adults):
        claim = build_claim(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={"testing/population": Qualifier("generic", adults)},
            polarity="positive",
            layer="causal",
        )
        with pytest.raises(TypeError):
            claim.qualifiers["testing/setting"] = Qualifier("generic", gene)  # type: ignore[index]

    def test_the_caller_cannot_reach_the_qualifiers_it_passed_in(self, profile, gene, outcome, adults):
        # The one mutable handle a caller genuinely holds: the dict it supplied.
        authored = {"testing/population": Qualifier("generic", adults)}
        claim = build_claim(
            profile, operator=AFFECTS, args=(gene, outcome), qualifiers=authored, polarity="positive", layer="causal"
        )
        authored["testing/setting"] = Qualifier("generic", gene)
        assert set(claim.qualifiers) == {"testing/population"}


class TestTheValueTypesOwnTheirInvariants:
    """What `isinstance` has to be worth for the opacity above to mean anything.

    Each gap here produces a **trusted** `Claim` — one that came through the
    boundary — holding something that is not a claim's content. Refusing at the
    boundary is not enough if the values it admits can be malformed or faked.
    """

    @pytest.mark.parametrize("term", [123, None, b"EX:gene-x", "", ("EX:gene-x",)])
    def test_a_referent_term_must_be_an_identifier(self, term):
        # §6.5: every position in the projection is an identifier. `term` is the
        # only one nothing downstream checks — membership is decode's, against a
        # snapshot — so an unchecked non-string reaches a minted claim.
        with pytest.raises(MalformedReferent):
            Referent(sort="testing/entity", term=term)

    @pytest.mark.parametrize("sort", [123, None, ""])
    def test_a_referent_sort_must_be_an_identifier(self, sort):
        with pytest.raises(MalformedReferent):
            Referent(sort=sort, term="EX:gene-x")

    def test_a_qualifier_restriction_must_be_a_referent(self):
        with pytest.raises(UntypedReferent):
            Qualifier("generic", "EX:adults")  # type: ignore[arg-type]

    def test_a_qualifier_impostor_is_refused(self, profile, gene, outcome, adults):
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
                args=(gene, outcome),
                qualifiers={"testing/population": Impostor("generic", adults)},  # type: ignore[dict-item]
                polarity="positive",
                layer="causal",
            )

    @pytest.mark.parametrize("closed", [Claim, Referent, Qualifier])
    def test_the_claim_types_cannot_be_subclassed(self, closed):
        # A subclass could expose a raw constructor and mint an unchecked object
        # that still satisfies isinstance(x, Claim) — at which point every reader
        # trusting a Claim unconditionally is wrong, with nothing here edited.
        with pytest.raises(SubclassRefused):

            class Rogue(closed):
                pass

    def test_a_subclass_cannot_be_smuggled_in_through_a_value(self, profile, outcome):
        # The transitive case: `Claim`'s contents are identifiers only because
        # `Referent` says so, so sealing `Claim` alone would leave the invariant
        # reachable one level down.
        with pytest.raises(SubclassRefused):
            # The declaration is what is under test — `@final` states the
            # rule and `@sealed` enforces it at run time, and only one of the two
            # survives into a running program.
            class LaxReferent(Referent):  # type: ignore[misc]
                def __post_init__(self) -> None:
                    return None


class TestTheCheckIsAgainstTheProfile:
    """M11's checks, at the route that exists. Each is refused **distinctly**:
    M11 decodes each ill-formed input in turn, and a single collapsed error
    would let one check cover for another's absence."""

    def test_an_unresolvable_operator_refuses(self, profile, gene, outcome):
        # §7.4 row 4a: a local, static failure — and *not* a ClaimError, because
        # nothing is wrong with the claim as written; the profile cannot resolve
        # what it names.
        with pytest.raises(ProfileError, match="no operator"):
            build_claim(profile, operator="testing/absent", args=(gene, outcome), polarity="positive", layer="causal")

    def test_wrong_arity_refuses(self, profile, gene):
        with pytest.raises(ArityMismatch):
            build_claim(profile, operator=AFFECTS, args=(gene,), polarity="positive", layer="causal")

    def test_a_wrongly_sorted_argument_refuses(self, profile, gene, outcome):
        with pytest.raises(ArgumentSortMismatch):
            build_claim(profile, operator=AFFECTS, args=(outcome, gene), polarity="positive", layer="causal")

    def test_a_bare_string_cannot_occupy_a_slot(self, profile, outcome):
        # M4's static arm, as far as a runtime carries it: a string has no sort,
        # so there is nothing to check against the slot's.
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=AFFECTS,
                args=("EX:gene-x", outcome),  # type: ignore[arg-type]
                polarity="positive",
                layer="causal",
            )

    def test_an_undeclared_dimension_refuses(self, profile, gene, adults):
        with pytest.raises(UndeclaredDimension):
            build_claim(
                profile,
                operator=SUBTYPE_OF,
                args=(gene, gene),
                qualifiers={"testing/population": Qualifier("generic", adults)},
                layer="structural",
            )

    def test_a_wrongly_sorted_restriction_refuses(self, profile, gene, outcome):
        with pytest.raises(RestrictionSortMismatch):
            build_claim(
                profile,
                operator=AFFECTS,
                args=(gene, outcome),
                qualifiers={"testing/population": Qualifier("generic", gene)},  # population restricts to cohort
                polarity="positive",
                layer="causal",
            )

    def test_a_bare_string_cannot_be_a_restriction(self, profile, gene, outcome):
        with pytest.raises(UntypedReferent):
            build_claim(
                profile,
                operator=AFFECTS,
                args=(gene, outcome),
                qualifiers={"testing/population": Qualifier("generic", "EX:adults")},  # type: ignore[arg-type]
                polarity="positive",
                layer="causal",
            )

    def test_a_quantifier_outside_the_closed_set_refuses(self, profile, gene, outcome, adults):
        with pytest.raises(UnknownQuantifier):
            build_claim(
                profile,
                operator=AFFECTS,
                args=(gene, outcome),
                qualifiers={"testing/population": Qualifier("mostly", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_an_inadmissible_layer_refuses(self, profile, gene, outcome):
        with pytest.raises(InadmissibleLayer):
            build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="structural")

    def test_a_well_formed_claim_is_accepted_whole(self, profile, gene, outcome, adults):
        claim = build_claim(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={"testing/population": Qualifier("universal", adults)},
            polarity="negative",
            layer="causal",
        )
        assert claim.operator == AFFECTS
        assert claim.args == (gene, outcome)
        assert claim.qualifiers == {"testing/population": Qualifier("universal", adults)}
        assert claim.polarity == "negative"
        assert claim.layer == "causal"


class TestPolarityIsTheUnitInhabitantWhenTheOperatorHasNoSign:
    """§6.3 and §7.5. `inapt` and `unsigned` are different facts."""

    def test_a_sign_inapt_operator_carries_the_inapt_tag(self, profile, base_contract, gene):
        claim = build_claim(profile, operator=SUBTYPE_OF, args=(gene, gene), layer="structural")
        assert claim.polarity == base_contract.claim_grammar.sign_inapt_tag
        assert claim.polarity not in base_contract.claim_grammar.polarities

    def test_a_sign_on_a_sign_inapt_operator_refuses(self, profile, gene):
        with pytest.raises(PolarityRefused, match="unit type"):
            build_claim(profile, operator=SUBTYPE_OF, args=(gene, gene), polarity="positive", layer="structural")

    def test_unsigned_is_not_a_way_to_say_inapt(self, profile, gene):
        # The collapse §7.5 refuses: `unsigned` says the operator has a sign and
        # this claim asserts none.
        with pytest.raises(PolarityRefused):
            build_claim(profile, operator=SUBTYPE_OF, args=(gene, gene), polarity="unsigned", layer="structural")

    def test_the_inapt_tag_cannot_be_supplied_by_hand_either(self, profile, base_contract, gene):
        # There is one inhabitant, so it is not a choice — accepting it here
        # would make the author an authority on a contract-derived fact.
        inapt = base_contract.claim_grammar.sign_inapt_tag
        with pytest.raises(PolarityRefused):
            build_claim(profile, operator=SUBTYPE_OF, args=(gene, gene), polarity=inapt, layer="structural")

    def test_a_sign_apt_operator_requires_one(self, profile, gene, outcome):
        with pytest.raises(PolarityRefused, match="sign-apt"):
            build_claim(profile, operator=AFFECTS, args=(gene, outcome), layer="causal")

    def test_unsigned_is_available_where_the_operator_has_a_sign(self, profile, gene, outcome):
        claim = build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="unsigned", layer="causal")
        assert claim.polarity == "unsigned"


class TestTheAuthoringBoundaryRefusesRetiredVocabulary:
    """§7.3a's per-claim half. Every route by which retirement reaches an
    author is closed here; **none** of them reaches decode."""

    def test_a_retired_operator_cannot_be_authored(self, retire, gene, outcome):
        profile = retire("operators", "affects")
        with pytest.raises(WithdrawnFromAuthoring, match="the operator is retired"):
            build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")

    def test_a_retired_argument_sort_withdraws_the_operator(self, retire, gene, outcome):
        profile = retire("sorts", "outcome")
        with pytest.raises(WithdrawnFromAuthoring, match="argument sorts"):
            build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")

    def test_a_retired_dimension_cannot_be_selected(self, retire, gene, outcome, adults):
        profile = retire("dimensions", "population")
        with pytest.raises(WithdrawnFromAuthoring, match="testing/population"):
            build_claim(
                profile,
                operator=AFFECTS,
                args=(gene, outcome),
                qualifiers={"testing/population": Qualifier("generic", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_a_retired_restriction_sort_withdraws_its_dimension(self, retire, gene, outcome, adults):
        profile = retire("sorts", "cohort")  # population restricts to cohort
        with pytest.raises(WithdrawnFromAuthoring):
            build_claim(
                profile,
                operator=AFFECTS,
                args=(gene, outcome),
                qualifiers={"testing/population": Qualifier("generic", adults)},
                polarity="positive",
                layer="causal",
            )

    def test_the_operator_stays_authorable_without_the_retired_dimension(self, retire, gene, outcome):
        # §6.2: Dims(op) is *permitted*, not required, so retiring one withdraws
        # only itself. Widening the operator rule to match would be the wrong
        # correction.
        profile = retire("dimensions", "population")
        claim = build_claim(profile, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")
        assert claim.qualifiers == {}

    def test_an_undeclared_dimension_does_not_collapse_into_a_retired_one(self, retire, gene, adults):
        # Two different facts: never permitted, versus permitted and withdrawn.
        profile = retire("dimensions", "population")
        with pytest.raises(UndeclaredDimension):
            build_claim(
                profile,
                operator=SUBTYPE_OF,
                args=(gene, gene),
                qualifiers={"testing/population": Qualifier("generic", adults)},
                layer="structural",
            )

    def test_retirement_does_not_reach_the_seam_decode_will_use(self, retire, gene, outcome, adults):
        # The rule above must not narrow the decode rule. Asserted against
        # `_checked` because that is the route `decodeClaim` will take, and
        # asserting it only through `build_claim` would assert the opposite.
        profile = retire("operators", "affects")
        claim = Claim._checked(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={"testing/population": Qualifier("generic", adults)},
            polarity="positive",
            layer="causal",
        )
        assert claim.operator == AFFECTS

    def test_a_retired_restriction_sort_is_still_typed_at_that_seam(self, retire, gene, outcome, adults):
        profile = retire("sorts", "cohort")
        claim = Claim._checked(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={"testing/population": Qualifier("generic", adults)},
            polarity="positive",
            layer="causal",
        )
        assert claim.qualifiers["testing/population"].restriction == adults
