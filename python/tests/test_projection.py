"""``π_claim`` and ``I_claim``.

**M9** in full. **M5** in the arms that do not need an assessment record — the
founding case is minted and forked here, but *"the prior assessment still bound
to the old claim, and a `supersedes` link"* needs kinds cut 1 does not build.
**M8**'s in-cut half: `I_claim` unchanged across recompilation and across an
editorial contract bump; the *"and `belief_input_digest` moves"* arm is belief's,
which cut 1 stops before.

One thing this file is careful about. Several of M8's assertions **cannot fail
given the signature** — `project_claim` takes a `Claim` and nothing else, so no
merge order, compiler build or contract release can reach it. Those are marked
where they appear and kept as regression guards. The arm that can fail is the
signature itself, and the absence of any contract-derived value from the bytes.
"""

import copy
import inspect

import pytest

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import base, domain
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

AFFECTS = "testing/affects"
SUBTYPE_OF = "testing/subtype-of"
POPULATION = "testing/population"
SETTING = "testing/setting"


@pytest.fixture()
def parse(base_contract):
    def _parse(document, predecessor=None):
        return domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=predecessor)

    return _parse


@pytest.fixture()
def testing(parse, testing_document):
    return parse(testing_document)


@pytest.fixture()
def profile(base_contract, testing):
    return compile_profile(base_contract, [testing])


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
def adults():
    return Referent(sort="testing/cohort", term="EX:adults")


@pytest.fixture()
def humans():
    return Referent(sort="testing/cohort", term="EX:humans")


@pytest.fixture()
def affects(profile, gene, outcome):
    """`⟨affects, [gene, outcome], {}, positive, causal⟩`."""

    def _affects(qualifiers=None, polarity="positive"):
        return build_claim(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers=qualifiers or {},
            polarity=polarity,
            layer="causal",
        )

    return _affects


class TestTheProjectionIsAFunctionOfTheClaimAlone:
    """M8. The signature is the guarantee; the rest follows from it."""

    def test_the_projection_takes_a_claim_and_nothing_else(self):
        # This is the arm with force. Folding a contract release into π_claim —
        # M8's named sabotage — is unreachable without widening this signature,
        # so the signature is what a test can watch.
        parameters = inspect.signature(project_claim).parameters
        assert list(parameters) == ["claim"]
        assert parameters["claim"].annotation == "Claim"
        assert list(inspect.signature(claim_identity).parameters) == ["claim"]

    def test_no_contract_identity_reaches_the_bytes(self, profile, affects, adults):
        claim = affects({POPULATION: Qualifier("generic", adults)})
        encoded = v1.encode(project_claim(claim)).decode("utf-8")
        for identity in [
            profile.base_contract_identity,
            profile.compiled_identity,
            *profile.activated_contracts.values(),
        ]:
            assert identity not in encoded

    def test_no_sort_identifier_reaches_the_bytes(self, affects, adults):
        # §6.5 admits the referent identifier, not the sort that admitted it. A
        # sort is contract-declared, so carrying it would let a re-declaration
        # re-project stored claims.
        claim = affects({POPULATION: Qualifier("generic", adults)})
        encoded = v1.encode(project_claim(claim)).decode("utf-8")
        for sort in ["testing/entity", "testing/outcome", "testing/cohort"]:
            assert sort not in encoded
        assert '"EX:gene-x"' in encoded

    def test_an_editorial_contract_bump_leaves_the_identity_still(
        self, base_contract, parse, testing_document, testing, gene, outcome
    ):
        # §7.4 row 1. The contract identity moves and `I_claim` does not.
        edited = copy.deepcopy(testing_document)
        edited["operators"]["affects"]["description"] = "Reworded."
        edited["lineage"] = {"successor": testing.content_identity}
        edited["version"] = 2
        successor = parse(edited, predecessor=testing)
        assert successor.content_identity != testing.content_identity

        def mint(contract):
            spec = compile_profile(base_contract, [contract])
            return claim_identity(
                build_claim(spec, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")
            )

        assert mint(successor) == mint(testing)

    def test_recompiling_leaves_the_identity_still(
        self, base_contract, parse, testing_document, testing, gene, outcome
    ):
        # **Cannot fail given the signature** — no profile reaches the
        # projection, so no merge order can. Kept as a regression guard against a
        # future signature change, and not evidence of anything on its own.
        elsewhere = copy.deepcopy(testing_document)
        elsewhere["contract"] = "elsewhere"
        second = parse(elsewhere)

        def mint(domains):
            spec = compile_profile(base_contract, domains)
            return claim_identity(
                build_claim(spec, operator=AFFECTS, args=(gene, outcome), polarity="positive", layer="causal")
            )

        assert mint([testing, second]) == mint([second, testing])

    def test_the_domain_is_the_projections_own(self, affects):
        # A shape change takes a new domain, so a v2 projection can never be
        # mistaken for a v1 one.
        claim = affects()
        assert claim_identity(claim) == v1.digest(CLAIM_DOMAIN, project_claim(claim))
        assert CLAIM_DOMAIN == "science.claim.v1"


class TestTheShapeDependsOnTheClaimNeverOnAContractField:
    """M9."""

    def test_the_polarity_position_is_present_at_a_sign_inapt_operator(self, profile, base_contract, gene, other_gene):
        claim = build_claim(profile, operator=SUBTYPE_OF, args=(gene, other_gene), layer="structural")
        projection = project_claim(claim)
        assert "polarity" in projection
        assert projection["polarity"] == base_contract.claim_grammar.sign_inapt_tag

    def test_the_position_set_is_the_same_at_both_kinds_of_operator(self, profile, affects, gene, other_gene):
        inapt = build_claim(profile, operator=SUBTYPE_OF, args=(gene, other_gene), layer="structural")
        assert set(project_claim(inapt)) == set(project_claim(affects()))
        assert set(project_claim(inapt)) == {"operator", "args", "qualifiers", "polarity", "layer"}

    def test_inapt_and_unsigned_are_distinct_bytes_in_the_encoding(self, base_contract):
        # Asserted **directly against the base contract**, never inferred from
        # two claim digests: the two tags necessarily occur under different
        # operators, so differing digests would prove only that the operators
        # differ.
        grammar = base_contract.claim_grammar
        assert v1.encode(grammar.sign_inapt_tag) != v1.encode("unsigned")
        assert grammar.sign_inapt_tag not in grammar.polarities
        assert len({v1.encode(tag) for tag in grammar.polarity_tags}) == len(grammar.polarity_tags)

    def test_every_polarity_tag_projects_distinctly(self, profile, affects, gene, other_gene):
        inapt = build_claim(profile, operator=SUBTYPE_OF, args=(gene, other_gene), layer="structural")
        projected = [project_claim(affects(polarity=tag))["polarity"] for tag in ["positive", "negative", "unsigned"]]
        projected.append(project_claim(inapt)["polarity"])
        assert len(set(projected)) == 4

    def test_the_claim_carries_the_tag_so_no_contract_is_consulted(self, profile, gene, other_gene):
        # The point of §7.5: the projection reads `claim.polarity`, which is
        # already a tag, so flipping `sign_apt` cannot re-project a stored claim
        # — there is no path from the contract to this shape.
        claim = build_claim(profile, operator=SUBTYPE_OF, args=(gene, other_gene), layer="structural")
        assert project_claim(claim)["polarity"] == claim.polarity


class TestQualificationParticipatesInIdentity:
    """M5, in the arms that do not need an assessment record."""

    def test_the_founding_case_forks(self, affects, adults, humans):
        # Kernel §4.1: "X affects Y in adults" edited to "X affects Y in all
        # humans" must not be a revision.
        c_adults = affects({POPULATION: Qualifier("generic", adults)})
        c_humans = affects({POPULATION: Qualifier("universal", humans)})
        assert claim_identity(c_adults) != claim_identity(c_humans)

    def test_the_restriction_alone_forks_it(self, affects, adults, humans):
        # The case that matters: the widening a reviewer would miss is usually a
        # restriction swap, not a visible "all".
        held = affects({POPULATION: Qualifier("generic", adults)})
        swapped = affects({POPULATION: Qualifier("generic", humans)})
        assert claim_identity(held) != claim_identity(swapped)

    def test_the_quantifier_alone_forks_it(self, affects, adults):
        generic = affects({POPULATION: Qualifier("generic", adults)})
        universal = affects({POPULATION: Qualifier("universal", adults)})
        assert claim_identity(generic) != claim_identity(universal)

    def test_an_omitted_dimension_forks_it(self, affects, adults, gene):
        restricted = affects({POPULATION: Qualifier("generic", adults)})
        both = affects({POPULATION: Qualifier("generic", adults), SETTING: Qualifier("generic", gene)})
        assert claim_identity(restricted) != claim_identity(both)
        assert claim_identity(affects()) != claim_identity(restricted)

    def test_the_dimension_key_participates(self, profile, gene, outcome):
        # Two claims whose qualifier *values* are identical and whose dimensions
        # differ. Without the key in the projection these would collide.
        entity_restriction = Referent(sort="testing/entity", term="EX:adults")
        cohort_restriction = Referent(sort="testing/cohort", term="EX:adults")
        by_population = build_claim(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={POPULATION: Qualifier("generic", cohort_restriction)},
            polarity="positive",
            layer="causal",
        )
        by_setting = build_claim(
            profile,
            operator=AFFECTS,
            args=(gene, outcome),
            qualifiers={SETTING: Qualifier("generic", entity_restriction)},
            polarity="positive",
            layer="causal",
        )
        assert claim_identity(by_population) != claim_identity(by_setting)

    def test_qualifier_key_order_is_inert(self, affects, adults, gene):
        # M5's negative arm. `science.identity.v1` sorts object keys at encode
        # time, so this is delivered by the encoder rather than re-implemented.
        forward = affects({POPULATION: Qualifier("generic", adults), SETTING: Qualifier("generic", gene)})
        reverse = affects({SETTING: Qualifier("generic", gene), POPULATION: Qualifier("generic", adults)})
        assert claim_identity(forward) == claim_identity(reverse)
        assert list(forward.qualifiers) != list(reverse.qualifiers)

    def test_the_qualifiers_are_keyed_by_dimension_never_held_positionally(self, affects, adults):
        # A sequence here would make the authoring order an identity input, and
        # the negative arm above would then be enforcing nothing.
        projection = project_claim(affects({POPULATION: Qualifier("generic", adults)}))
        assert isinstance(projection["qualifiers"], dict)
        assert set(projection["qualifiers"]) == {POPULATION}


class TestArgumentsAreHeldBySlot:
    """§6.2: `ArgSort(op)` is positional, so the sequence is the meaning."""

    def test_swapping_two_arguments_forks_the_identity(self, profile, gene, other_gene):
        forward = build_claim(profile, operator=SUBTYPE_OF, args=(gene, other_gene), layer="structural")
        reverse = build_claim(profile, operator=SUBTYPE_OF, args=(other_gene, gene), layer="structural")
        assert claim_identity(forward) != claim_identity(reverse)

    def test_the_arguments_are_a_sequence(self, affects):
        projection = project_claim(affects())
        assert projection["args"] == ["EX:gene-x", "EX:outcome-y"]

    def test_the_operator_and_layer_are_identifiers(self, affects):
        projection = project_claim(affects())
        assert projection["operator"] == AFFECTS
        assert projection["layer"] == "causal"


class TestNoProseReachesIdentity:
    def test_the_projection_holds_nothing_but_identifiers_and_tags(self, affects, adults):
        claim = affects({POPULATION: Qualifier("generic", adults)})
        projection = project_claim(claim)
        flat = [
            projection["operator"],
            *projection["args"],  # type: ignore[misc]  # π_claim's shape is what the assert below checks
            projection["polarity"],
            projection["layer"],
            *[value for entry in projection["qualifiers"].values() for value in entry.values()],  # type: ignore[attr-defined]
        ]
        assert all(isinstance(value, str) and value and " " not in value for value in flat)

    def test_a_claim_has_no_statement_to_project(self, affects):
        # `statement` is in exactly the position `title` was (kernel §4.1): a
        # field cannot be both hand-editable prose and an identity input. There
        # is no such field to exclude, which is stronger than excluding it.
        assert not hasattr(affects(), "statement")
        assert not hasattr(affects(), "display_statement")


class TestIdentityIsStableAndDomainSeparated:
    def test_the_same_claim_hashes_the_same_way_twice(self, affects, adults):
        first = affects({POPULATION: Qualifier("generic", adults)})
        second = affects({POPULATION: Qualifier("generic", adults)})
        assert first is not second
        assert claim_identity(first) == claim_identity(second)

    def test_the_claim_domain_separates_it_from_the_profile_domain(self, affects):
        # The same bytes under a different domain must not collide.
        projection = project_claim(affects())
        assert v1.digest(CLAIM_DOMAIN, projection) != v1.digest("science.profile.v1", projection)

    def test_the_domain_is_well_formed(self):
        v1.check_domain(CLAIM_DOMAIN)


class TestTheBaseContractPinsTheTags:
    def test_a_grammar_that_collides_inapt_with_a_polarity_is_refused(self, base_contract_path):
        import yaml

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        document["claim_grammar"]["sign_inapt_tag"] = "unsigned"
        with pytest.raises(Exception, match="sign_inapt_tag"):
            base.parse_base_contract(document, source="<test>")
