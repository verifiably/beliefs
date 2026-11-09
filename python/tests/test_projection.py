"""``π_claim`` and ``I_claim``.

The claim identity in full; qualification in the checks that do not need an assessment record — the
founding case is minted and forked here, but *"the prior assessment still bound
to the old claim, and a `supersedes` link"* needs kinds not built here.
The in-scope half of merge-order inertness: `I_claim` unchanged across recompilation and across an
editorial contract bump; the *"and `belief_input_digest` moves"* arm is belief's,
which this module stops before.

One thing this file is careful about. Several of those assertions **cannot fail
given the signature** — `project_claim` takes a `Claim` and nothing else, so no
merge order, compiler build or contract release can reach it. Those are marked
where they appear and kept as regression guards. The arm that can fail is the
signature itself, and the absence of any contract-declared value — a binding, a
release, a contract identity — from the bytes.
"""

import copy
import inspect

import pytest

from beliefs.claim import Member, Qualifier, Referent, build_claim
from beliefs.contract import base, domain
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

AFFECTS = "testing/affects"
CORRELATES = "testing/correlates-with"
TRANSFORMS = "testing/transforms"
MEASURED_BY = "testing/measured-by"
PROMOTES = "testing/promotes"
POPULATION = "testing/population"
SETTING = "testing/setting"
MODEL = Referent(sort="testing/procedure-spec", term="procedure:" + "a" * 64)


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
def method():
    return Referent(sort="testing/method", term="EX:assay")


@pytest.fixture()
def adults():
    return Referent(sort="testing/cohort", term="EX:adults")


@pytest.fixture()
def humans():
    return Referent(sort="testing/cohort", term="EX:humans")


@pytest.fixture()
def affects(profile, gene, outcome):
    """`⟨affects, {cause: gene, effect: outcome}, {}, polar, positive, causal⟩`."""

    def _affects(qualifiers=None, polarity="positive", roles=None, operator=AFFECTS, form="polar"):
        return build_claim(
            profile,
            operator=operator,
            roles=roles or {"cause": gene, "effect": outcome},
            qualifiers=qualifiers or {},
            form=form,
            polarity=polarity,
            layer="causal",
        )

    return _affects


@pytest.fixture()
def measured(profile, gene, method):
    """A sign-inapt `measured-by` claim."""
    return build_claim(
        profile, operator=MEASURED_BY, roles={"subject": gene, "instrument": method}, layer="methodological"
    )


@pytest.fixture()
def correlates(profile):
    def _correlates(*parties, qualifiers=None):
        return build_claim(
            profile,
            operator=CORRELATES,
            roles={"parties": parties},
            qualifiers=qualifiers or {},
            polarity="positive",
            layer="statistical",
        )

    return _correlates


class TestTheProjectionIsAFunctionOfTheClaimAlone:
    """The signature is the guarantee; the rest follows from it."""

    def test_the_projection_takes_a_claim_and_nothing_else(self):
        # This is the check with force. Folding a contract release into π_claim —
        # the named failure — is unreachable without widening this signature,
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

    def test_the_sort_identifier_reaches_the_bytes_and_its_binding_never_does(self, profile, affects, adults):
        # The sort *identifier* enters; its binding is contract-declared, so
        # carrying it would let a re-declaration re-project stored claims.
        claim = affects({POPULATION: Qualifier("generic", adults)})
        encoded = v1.encode(project_claim(claim)).decode("utf-8")
        for sort in ["testing/entity", "testing/outcome", "testing/cohort"]:
            assert f'"{sort}"' in encoded
        entity_binding = profile.sorts["testing/entity"].binding.projection()
        cohort_binding = profile.sorts["testing/cohort"].binding.projection()
        for value in [
            entity_binding["kind"],
            entity_binding["release"],
            cohort_binding["kind"],
            cohort_binding["dataset"],
        ]:
            assert value not in encoded

    def test_an_editorial_contract_bump_leaves_the_identity_still(
        self, base_contract, parse, testing_document, testing, gene, outcome
    ):
        # The contract identity moves and `I_claim` does not.
        edited = copy.deepcopy(testing_document)
        edited["templates"]["affects"]["description"] = "Reworded."
        edited["lineage"] = {"successor": testing.content_identity}
        edited["version"] = 2
        successor = parse(edited, predecessor=testing)
        assert successor.content_identity != testing.content_identity

        def mint(contract):
            spec = compile_profile(base_contract, [contract])
            return claim_identity(
                build_claim(
                    spec,
                    operator=AFFECTS,
                    roles={"cause": gene, "effect": outcome},
                    polarity="positive",
                    layer="causal",
                )
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
                build_claim(
                    spec,
                    operator=AFFECTS,
                    roles={"cause": gene, "effect": outcome},
                    polarity="positive",
                    layer="causal",
                )
            )

        assert mint([testing, second]) == mint([second, testing])

    def test_domain_is_v2(self, affects):
        # A shape change takes a new domain, so a v2 projection can never be
        # mistaken for a v1 one.
        claim = affects()
        assert CLAIM_DOMAIN == "science.claim.v2"
        assert claim_identity(claim) == v1.digest(CLAIM_DOMAIN, project_claim(claim))
        assert claim_identity(claim) != v1.digest("science.claim.v1", project_claim(claim))


class TestTheShapeIsTheDesigns:
    """§5.3: roles by name, every referent carrying its sort, the form and
    polarity always present."""

    def test_projection_shape_v2(self, correlates, gene, outcome, adults):
        # The §5.3 example's shape, over the fixture contract.
        claim = correlates(Member(outcome), Member(gene), qualifiers={POPULATION: Qualifier("generic", adults)})
        assert project_claim(claim) == {
            "operator": "testing/correlates-with",
            "roles": {
                "parties": [
                    {"sort": "testing/entity", "term": "EX:gene-x", "coefficient": 1},
                    {"sort": "testing/outcome", "term": "EX:outcome-y", "coefficient": 1},
                ]
            },
            "qualifiers": {
                "testing/population": {
                    "quantifier": "generic",
                    "restriction": {"sort": "testing/cohort", "term": "EX:adults"},
                }
            },
            "form": "polar",
            "polarity": "positive",
            "layer": "statistical",
        }

    def test_a_one_role_projects_as_a_referent_object(self, affects):
        assert project_claim(affects())["roles"] == {
            "cause": {"sort": "testing/entity", "term": "EX:gene-x"},
            "effect": {"sort": "testing/outcome", "term": "EX:outcome-y"},
        }

    def test_a_coefficient_projects_as_an_integer(self, profile, gene, other_gene):
        claim = build_claim(
            profile,
            operator=TRANSFORMS,
            roles={"inputs": [Member(gene, 2)], "outputs": [Member(other_gene)], "facilitators": []},
            layer="structural",
        )
        roles = project_claim(claim)["roles"]
        assert isinstance(roles, dict)
        assert roles["inputs"] == [{"sort": "testing/entity", "term": "EX:gene-x", "coefficient": 2}]
        assert type(roles["inputs"][0]["coefficient"]) is int
        assert roles["outputs"][0]["coefficient"] == 1

    def test_many_role_order_is_canonical(self, correlates, gene, outcome):
        # Case 3: a size-2 `parties` role written in both orders has one identity.
        forward = correlates(Member(gene), Member(outcome))
        reverse = correlates(Member(outcome), Member(gene))
        assert project_claim(forward) == project_claim(reverse)
        assert claim_identity(forward) == claim_identity(reverse)

    def test_empty_many_role_projects_as_list(self, profile, gene, other_gene):
        # Case 4a.
        claim = build_claim(
            profile,
            operator=TRANSFORMS,
            roles={"inputs": [Member(gene)], "outputs": [Member(other_gene)], "facilitators": []},
            layer="structural",
        )
        assert project_claim(claim)["roles"]["facilitators"] == []  # type: ignore[index]

    def test_the_polarity_position_is_present_at_a_sign_inapt_operator(self, measured, base_contract):
        projection = project_claim(measured)
        assert projection["polarity"] == base_contract.claim_grammar.sign_inapt_tag

    def test_the_position_set_is_the_same_at_every_kind_of_claim(self, affects, measured, base_contract):
        positions = {"operator", "roles", "qualifiers", "form", "polarity", "layer"}
        assert set(project_claim(measured)) == positions
        assert set(project_claim(affects())) == positions
        null = affects(form="null", polarity=None)
        assert set(project_claim(null)) == positions
        assert project_claim(null)["polarity"] == base_contract.claim_grammar.sign_inapt_tag

    def test_inapt_and_unsigned_are_distinct_bytes_in_the_encoding(self, base_contract):
        # Asserted **directly against the base contract**, never inferred from
        # two claim digests: the two tags necessarily occur under different
        # operators, so differing digests would prove only that the operators
        # differ.
        grammar = base_contract.claim_grammar
        assert v1.encode(grammar.sign_inapt_tag) != v1.encode("unsigned")
        assert grammar.sign_inapt_tag not in grammar.polarities
        assert len({v1.encode(tag) for tag in grammar.polarity_tags}) == len(grammar.polarity_tags)

    def test_every_polarity_tag_projects_distinctly(self, affects, measured):
        projected = [project_claim(affects(polarity=tag))["polarity"] for tag in ["positive", "negative", "unsigned"]]
        projected.append(project_claim(measured)["polarity"])
        assert len(set(projected)) == 4

    def test_the_claim_carries_the_tag_so_no_contract_is_consulted(self, measured):
        # The projection reads `claim.polarity`, which is already a tag, so
        # flipping `sign_apt` cannot re-project a stored claim.
        assert project_claim(measured)["polarity"] == measured.polarity


class TestEachPositionParticipatesInIdentity:
    """The acceptance cases this design owns, in their projection half."""

    def test_sort_identifier_changes_identity(self, affects, gene):
        # Case 1: one term under two sorts is two referents.
        as_outcome = affects(roles={"cause": gene, "effect": Referent("testing/outcome", "EX:x-1")})
        as_entity = affects(roles={"cause": gene, "effect": Referent("testing/entity", "EX:x-1")})
        assert claim_identity(as_outcome) != claim_identity(as_entity)

    def test_form_changes_identity(self, affects):
        # Case 6.
        polar = affects(polarity="unsigned")
        null = affects(form="null", polarity=None)
        assert project_claim(null)["form"] == "null"
        assert claim_identity(polar) != claim_identity(null)

    def test_within_model_changes_identity(self, affects, gene, outcome):
        # Case 7: "in model M" never shares an identity with the world claim.
        world = affects()
        modelled = affects(roles={"cause": gene, "effect": outcome, "within-model": MODEL})
        assert project_claim(modelled)["roles"]["within-model"] == {  # type: ignore[index]
            "sort": MODEL.sort,
            "term": MODEL.term,
        }
        assert claim_identity(world) != claim_identity(modelled)

    def test_bridge_and_template_differ(self, affects):
        # Case 9: a bridge is an operator of its own.
        assert claim_identity(affects(operator=PROMOTES)) != claim_identity(affects())

    def test_swapping_two_roles_forks_the_identity(self, affects, gene, other_gene):
        forward = affects(roles={"cause": gene, "effect": other_gene})
        reverse = affects(roles={"cause": other_gene, "effect": gene})
        assert claim_identity(forward) != claim_identity(reverse)

    def test_the_roles_are_keyed_by_name_never_held_positionally(self, affects):
        roles = project_claim(affects())["roles"]
        assert isinstance(roles, dict)
        assert set(roles) == {"cause", "effect"}

    def test_the_operator_and_layer_are_identifiers(self, affects):
        projection = project_claim(affects())
        assert projection["operator"] == AFFECTS
        assert projection["layer"] == "causal"


class TestQualificationParticipatesInIdentity:
    """Qualification, in the checks that do not need an assessment record."""

    def test_the_founding_case_forks(self, affects, adults, humans):
        # "X affects Y in adults" edited to "X affects Y in all
        # humans" must not be a revision.
        c_adults = affects({POPULATION: Qualifier("generic", adults)})
        c_humans = affects({POPULATION: Qualifier("universal", humans)})
        assert claim_identity(c_adults) != claim_identity(c_humans)

    def test_the_restriction_alone_forks_it(self, affects, adults, humans):
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

    def test_the_dimension_key_participates(self, affects):
        # Two qualifiers whose quantifier and term agree and whose dimensions
        # differ. Without the key in the projection these would differ only in
        # the restriction's sort.
        by_population = affects({POPULATION: Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
        by_setting = affects({SETTING: Qualifier("generic", Referent("testing/entity", "EX:adults"))})
        assert claim_identity(by_population) != claim_identity(by_setting)

    def test_qualifier_key_order_is_inert(self, affects, adults, gene):
        # `science.identity.v1` sorts object keys at encode time, so this is
        # delivered by the encoder rather than re-implemented.
        forward = affects({POPULATION: Qualifier("generic", adults), SETTING: Qualifier("generic", gene)})
        reverse = affects({SETTING: Qualifier("generic", gene), POPULATION: Qualifier("generic", adults)})
        assert claim_identity(forward) == claim_identity(reverse)
        assert list(forward.qualifiers) != list(reverse.qualifiers)

    def test_the_qualifiers_are_keyed_by_dimension_never_held_positionally(self, affects, adults):
        projection = project_claim(affects({POPULATION: Qualifier("generic", adults)}))
        assert isinstance(projection["qualifiers"], dict)
        assert set(projection["qualifiers"]) == {POPULATION}


def _leaves(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from _leaves(item)
    else:
        yield value


class TestNoProseReachesIdentity:
    def test_the_projection_holds_nothing_but_identifiers_tags_and_coefficients(
        self, correlates, gene, outcome, adults
    ):
        claim = correlates(Member(gene), Member(outcome), qualifiers={POPULATION: Qualifier("generic", adults)})
        leaves = list(_leaves(project_claim(claim)))
        assert all((isinstance(value, str) and value and " " not in value) or type(value) is int for value in leaves)
        assert [value for value in leaves if not isinstance(value, str)] == [1, 1]

    def test_a_claim_has_no_statement_to_project(self, affects):
        # `statement` is in exactly the position `title` was: a
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
