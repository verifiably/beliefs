"""`decode_claim`: referent typing, determinism and the five outcomes.

The boundary every import, deserialization and restore comes through. Three
guarantees meet here, and they are kept apart deliberately: **referent typing** is about
the receipt, **determinism** about the function being a function of
its arguments, and the **outcomes** about the five outcomes staying distinct.

One scope note that a reader will otherwise have to reconstruct. `not-available`
appears in both referent typing and the outcomes and they are **not the same test**. The first is local — the
vocabulary could not be read. The world-level `not-present` means the dataset's
covered corpus is absent. The cut keeps the two distinct.
"""

import subprocess
import sys
import textwrap
from typing import Any, ClassVar, cast

import pytest
import yaml
from domain_facet_fixtures import EX, GENE, OTHER_GENE

from beliefs import resolution, stored
from beliefs.claim import Claim, Member, Qualifier, Referent, build_claim
from beliefs.contract.base import parse_base_contract
from beliefs.contract.domain import DatasetBinding, ReleaseBinding
from beliefs.decode import WireClaim, decode_claim, stored_claim_terms
from beliefs.errors import (
    ClaimError,
    CoefficientRefused,
    DecodeError,
    FormRefused,
    InadmissibleLayer,
    MalformedContract,
    MalformedReferent,
    MalformedWireClaim,
    PolarityRefused,
    ProfileError,
    ResolutionError,
    RestrictionSortMismatch,
    RoleRefused,
    UnboundReferent,
    UndeclaredDimension,
)
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import BindingCheckReceipt, ReferentPosition, ResolutionSnapshot, TermOutcome, build_snapshot

COHORT_DATASET = DatasetBinding(dataset="dataset:sha256:" + "0" * 64)
"""The binding `testing`'s `cohort` sort declares."""
SELECTED = DatasetBinding(dataset="dataset:sha256:" + "3" * 64)
"""The `selected` dataset of `testing/event`'s selection binding."""
PRODUCED = DatasetBinding(dataset="dataset:sha256:" + "5" * 64)
"""The produced dataset of `testing/product`'s run-output binding."""

ENTITY = "testing/entity"
OUTCOME_SORT = "testing/outcome"
COHORT = "testing/cohort"
METHOD = "testing/method"
EVENT = "testing/event"
PRODUCT = "testing/product"
PROCEDURE_SPEC = "testing/procedure-spec"

OUTCOME = "EX:outcome-y"
ADULTS = "EX:adults"
ABSENT = "EX:not-in-the-vocabulary"
PROCEDURE = "procedure:" + "a" * 64


def test_a_wire_target_form_without_an_operable_decoder_cannot_enter_the_grammar(base_contract_path):
    document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
    document["estimand_grammar"]["forms"].append("ordinal")

    with pytest.raises(MalformedContract, match="ordinal"):
        parse_base_contract(document, source="<ordinal>")


@pytest.fixture()
def profile(base_contract, testing_contract_path):
    from beliefs.contract import load_domain_contract

    testing = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def readable():
    """Both vocabularies read, holding every term these tests bind."""
    return build_snapshot(readable={EX: [GENE, OTHER_GENE, OUTCOME], COHORT_DATASET: [ADULTS]})


def ref(sort: str, term: str) -> dict[str, object]:
    return {"sort": sort, "term": term}


def member(sort: str, term: str, coefficient: object = 1) -> dict[str, object]:
    return {"sort": sort, "term": term, "coefficient": coefficient}


def population(restriction: object = None, *, quantifier: str = "generic") -> dict[str, Any]:
    return {
        "testing/population": {
            "quantifier": quantifier,
            "restriction": ref(COHORT, ADULTS) if restriction is None else restriction,
        }
    }


def affects(
    *,
    cause: str = GENE,
    effect: str = OUTCOME,
    roles: object = None,
    qualifiers: object = None,
    form: str = "polar",
    polarity: str = "positive",
    layer: str = "causal",
    operator: str = "testing/affects",
) -> WireClaim:
    return WireClaim(
        operator=operator,
        roles={"cause": ref(ENTITY, cause), "effect": ref(OUTCOME_SORT, effect)} if roles is None else roles,  # type: ignore[arg-type]
        qualifiers={} if qualifiers is None else qualifiers,  # type: ignore[arg-type]
        form=form,
        polarity=polarity,
        layer=layer,
    )


def correlates(*parties: object, qualifiers: object = None) -> WireClaim:
    return WireClaim(
        operator="testing/correlates-with",
        roles={"parties": list(parties)},
        qualifiers={} if qualifiers is None else qualifiers,  # type: ignore[arg-type]
        form="polar",
        polarity="positive",
        layer="statistical",
    )


def wire_of(claim: Claim) -> WireClaim:
    """A serialized claim is its projection: the wire value a stored facet holds."""
    return WireClaim(**project_claim(claim))  # type: ignore[arg-type]


class TestTypedReferentsAndTheReceipt:
    def test_a_member_term_is_accepted_with_the_check_performed(self, profile, readable):
        claim, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert claim.roles["cause"] == Referent(sort=ENTITY, term=GENE)
        assert set(receipt.outcomes.values()) == {TermOutcome.MEMBER}
        assert receipt.performed

    def test_a_term_absent_from_a_readable_vocabulary_refuses_and_mints_nothing(self, profile, readable):
        # The only one of the five that refuses.
        with pytest.raises(UnboundReferent) as raised:
            decode_claim(affects(cause=ABSENT), profile=profile, snapshot=readable)
        assert "role:cause" in str(raised.value)
        assert "Nothing was minted" in str(raised.value)

    def test_availability_is_not_membership(self, profile, readable):
        """The negative case: the same bad term, accepted when nothing was read.

        This is the pair this boundary exists to keep apart. Refusing here would
        report *"not in the vocabulary"* on the evidence that nobody looked —
        the same error the outcome vocabulary exists to avoid, committed by the decoder.
        """
        bad = affects(cause=ABSENT)
        with pytest.raises(UnboundReferent):
            decode_claim(bad, profile=profile, snapshot=readable)

        unreadable = build_snapshot(unreadable=[EX])
        claim, receipt = decode_claim(bad, profile=profile, snapshot=unreadable)
        assert receipt.outcomes["role:cause"] is TermOutcome.NOT_AVAILABLE
        assert not receipt.performed
        assert claim.roles["cause"] == Referent(sort=ENTITY, term=ABSENT)

    def test_the_two_accepting_receipts_are_distinguishable(self, profile):
        """Also a negative case: accepted-and-checked must not look like accepted-and-unchecked."""
        good = affects()
        checked = decode_claim(good, profile=profile, snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}))[1]
        unchecked = decode_claim(good, profile=profile, snapshot=build_snapshot(unreadable=[EX]))[1]

        assert checked.outcomes != unchecked.outcomes
        assert checked.performed and not unchecked.performed
        assert checked.snapshot_identity != unchecked.snapshot_identity
        assert checked.identity() != unchecked.identity()
        # The claim is the same claim either way: availability must not reach identity.
        assert checked.claim_identity == unchecked.claim_identity

    def test_the_receipt_carries_exactly_one_outcome_per_referent_position(self, profile, readable):
        claim, receipt = decode_claim(affects(qualifiers=population()), profile=profile, snapshot=readable)

        expected = {
            ReferentPosition.role("cause").label(),
            ReferentPosition.role("effect").label(),
            ReferentPosition.restriction("testing/population").label(),
        }
        assert set(receipt.outcomes) == expected
        assert len(receipt.outcomes) == len(claim.roles) + len(claim.qualifiers)

    def test_a_restriction_is_resolved_exactly_as_a_role_is(self, profile):
        # A restriction is sorted as a role's referent is, so it resolves as one.
        # `cohort` binds a dataset, not the EX namespace, so a snapshot holding
        # only EX leaves the restriction unconsulted while the roles are read.
        wire = affects(qualifiers=population())
        _, receipt = decode_claim(wire, profile=profile, snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}))
        assert receipt.outcomes["role:cause"] is TermOutcome.MEMBER
        assert receipt.outcomes["restriction:testing/population"] is TermOutcome.NOT_CONSULTED

    def test_a_bad_restriction_refuses_like_a_bad_role(self, profile, readable):
        wire = affects(qualifiers=population(ref(COHORT, "EX:nobody")))
        with pytest.raises(UnboundReferent, match="restriction:testing/population"):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_the_receipt_records_the_snapshot_it_resolved_against(self, profile, readable):
        _, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert receipt.snapshot_identity == readable.identity

    def test_a_receipt_cannot_be_authored(self):
        with pytest.raises(ResolutionError, match="never authored"):
            BindingCheckReceipt(claim_identity="x", snapshot_identity="y", outcomes={})

    def test_a_snapshot_cannot_be_authored(self):
        with pytest.raises(ResolutionError, match="never authored"):
            ResolutionSnapshot(bindings={}, kinds={}, identity="x")

    def test_a_bare_string_cannot_occupy_a_role_inside(self, profile, readable):
        """The static check, at this boundary.

        The wire carries strings — that is what a wire is. What the boundary
        guarantees is that nothing bare survives it: every role of the decoded
        claim holds a `Referent` carrying a sort the profile admitted there.
        """
        claim, _ = decode_claim(affects(), profile=profile, snapshot=readable)
        assert all(isinstance(value, Referent) for value in claim.roles.values())
        assert claim.roles == {
            "cause": Referent(sort=ENTITY, term=GENE),
            "effect": Referent(sort=OUTCOME_SORT, term=OUTCOME),
        }


class TestRolePositions:
    def test_receipt_positions_are_roles(self, profile):
        """`role:<name>` for a `one` role, `role:<name>[<i>]` for the i-th member of a
        `many` role in canonical member-key order, `restriction:<dimension>` unchanged;
        `argument:<i>` is gone.

        The members are written product-first and resolve differently (the
        event's selected dataset is read, the product's dataset is not held), so
        the outcome at each index says which member the index names: the
        canonical first (`testing/event` sorts before `testing/product`), not the
        first written."""
        snapshot = build_snapshot(
            readable={EX: [GENE, OUTCOME], COHORT_DATASET: [ADULTS], SELECTED: ["EX:event-1"]},
            unreadable=[PRODUCED],
        )
        _, one = decode_claim(affects(qualifiers=population()), profile=profile, snapshot=snapshot)
        _, many = decode_claim(
            correlates(member(PRODUCT, "EX:product-1"), member(EVENT, "EX:event-1"), qualifiers=population()),
            profile=profile,
            snapshot=snapshot,
        )
        assert set(one.outcomes) == {"role:cause", "role:effect", "restriction:testing/population"}
        assert set(many.outcomes) == {"role:parties[0]", "role:parties[1]", "restriction:testing/population"}
        assert many.outcomes["role:parties[0]"] is TermOutcome.MEMBER
        assert many.outcomes["role:parties[1]"] is TermOutcome.NOT_AVAILABLE
        assert not any(label.startswith("argument:") for label in (*one.outcomes, *many.outcomes))
        assert not hasattr(ReferentPosition, "argument")

    def test_the_reserved_role_is_a_one_role_position(self, profile, readable):
        wire = affects(
            roles={
                "cause": ref(ENTITY, GENE),
                "effect": ref(OUTCOME_SORT, OUTCOME),
                "within-model": ref(PROCEDURE_SPEC, PROCEDURE),
            }
        )
        _, receipt = decode_claim(wire, profile=profile, snapshot=readable)
        assert receipt.outcomes["role:within-model"] is TermOutcome.NOT_CONSULTED
        _, held = decode_claim(
            wire,
            profile=profile,
            snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}, kinds={"procedure": [PROCEDURE]}),
        )
        assert held.outcomes["role:within-model"] is TermOutcome.MEMBER

    def test_an_empty_many_role_has_no_position(self, profile):
        wire = WireClaim(
            operator="testing/transforms",
            roles={
                "inputs": [member(ENTITY, GENE, 2)],
                "outputs": [member(ENTITY, OTHER_GENE)],
                "facilitators": [],
            },
            qualifiers={},
            form="polar",
            polarity="inapt",
            layer="structural",
        )
        _, receipt = decode_claim(wire, profile=profile, snapshot=build_snapshot())
        assert set(receipt.outcomes) == {"role:inputs[0]", "role:outputs[0]"}

    def test_a_member_index_is_a_non_negative_integer(self):
        assert ReferentPosition.member("parties", 1).label() == "role:parties[1]"
        for index in (-1, True, "0"):
            with pytest.raises(ResolutionError):
                ReferentPosition.member("parties", index)  # type: ignore[arg-type]

    def test_receipt_domain_v2(self, profile, readable):
        _, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert resolution.RECEIPT_DOMAIN == "science.receipt.v2"
        assert receipt.identity() == v1.digest("science.receipt.v2", receipt.projection())
        assert receipt.identity() != v1.digest("science.receipt.v1", receipt.projection())


class TestDecodeIsAFunctionOfItsArguments:
    def test_the_same_three_inputs_decode_identically_in_another_process(
        self, profile, readable, base_contract_path, testing_contract_path
    ):
        """The first determinism check, run as it is written: *in different processes*.

        Asserting determinism twice inside one interpreter would be asserting
        that a pure function is pure, which it is by construction there. The
        property at issue is that nothing ambient — a cache, a working
        directory, an environment variable, an import-time singleton — reaches
        the result, and only a second process can say so.
        """
        claim, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        script = textwrap.dedent(f"""
            from pathlib import Path
            from beliefs.contract import load_base_contract, load_domain_contract
            from beliefs.contract.domain import DatasetBinding, ReleaseBinding
            from beliefs.profile import compile_profile
            from beliefs.decode import WireClaim, decode_claim
            from beliefs.projection import claim_identity
            from beliefs.resolution import build_snapshot

            base = load_base_contract(Path({str(base_contract_path)!r}))
            testing = load_domain_contract(Path({str(testing_contract_path)!r}), base=base, predecessor=None)
            profile = compile_profile(base, [testing])
            EX = ReleaseBinding(namespace="EX", release="2026-01-01")
            COHORT = DatasetBinding(dataset="dataset:sha256:" + "0" * 64)
            snapshot = build_snapshot(readable={{EX: [{GENE!r}, {OTHER_GENE!r}, {OUTCOME!r}], COHORT: [{ADULTS!r}]}})
            wire = WireClaim(
                operator="testing/affects",
                roles={{
                    "cause": {{"sort": {ENTITY!r}, "term": {GENE!r}}},
                    "effect": {{"sort": {OUTCOME_SORT!r}, "term": {OUTCOME!r}}},
                }},
                qualifiers={{}},
                form="polar",
                polarity="positive",
                layer="causal",
            )
            decoded, emitted = decode_claim(wire, profile=profile, snapshot=snapshot)
            print(claim_identity(decoded))
            print(emitted.identity())
        """)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(base_contract_path.parent),
        )
        elsewhere_claim, elsewhere_receipt = result.stdout.split()
        assert elsewhere_claim == claim_identity(claim)
        assert elsewhere_receipt == receipt.identity()

    def test_availability_is_a_parameter_and_has_no_default(self):
        """The ambient-availability check, closed by construction rather than by a check.

        *"Make availability ambient rather than a parameter and assert two
        holders now decode the same bytes differently."* There is no way to make
        it ambient without editing the signature, which is the strongest form
        this can take: `snapshot` is keyword-only and has no default, so a decode
        that did not state what it resolved against does not compile.
        """
        import inspect

        parameter = inspect.signature(decode_claim).parameters["snapshot"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY

    def test_two_holders_with_different_availability_decode_differently(self, profile):
        """And the observable half: the parameter is not decorative.

        Same bytes, same profile, two holders — one refuses and one accepts. That
        is not a defect; it is the fact that made `ResolutionSnapshot` a
        parameter, now visible in the result instead of hidden in the ambient.
        """
        bad = affects(cause=ABSENT)
        with pytest.raises(UnboundReferent):
            decode_claim(bad, profile=profile, snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}))
        _, receipt = decode_claim(bad, profile=profile, snapshot=build_snapshot())
        assert receipt.outcomes["role:cause"] is TermOutcome.NOT_CONSULTED

    @pytest.mark.parametrize(
        ("wire", "error"),
        [
            pytest.param(
                WireClaim(
                    operator="testing/measured-by",
                    roles={"subject": ref(ENTITY, GENE), "instrument": ref(METHOD, "EX:assay")},
                    qualifiers={},
                    form="polar",
                    polarity="positive",
                    layer="methodological",
                ),
                PolarityRefused,
                id="a-sign-on-a-sign-inapt-operator",
            ),
            pytest.param(affects(roles={"cause": ref(ENTITY, GENE)}), RoleRefused, id="a-missing-role"),
            pytest.param(
                affects(
                    roles={"cause": ref(ENTITY, GENE), "effect": ref(OUTCOME_SORT, OUTCOME), "extra": ref(ENTITY, GENE)}
                ),
                RoleRefused,
                id="an-undeclared-role",
            ),
            pytest.param(
                affects(qualifiers={"testing/absent": {"quantifier": "generic", "restriction": ref(COHORT, ADULTS)}}),
                UndeclaredDimension,
                id="an-undeclared-dimension",
            ),
            pytest.param(
                affects(qualifiers=population(ref(ENTITY, GENE))), RestrictionSortMismatch, id="a-restriction-sort"
            ),
            pytest.param(affects(layer="structural"), InadmissibleLayer, id="an-inadmissible-layer"),
            pytest.param(
                WireClaim(
                    operator="testing/measured-by",
                    roles={"subject": ref(ENTITY, GENE), "instrument": ref(METHOD, "EX:assay")},
                    qualifiers={},
                    form="null",
                    polarity="inapt",
                    layer="methodological",
                ),
                FormRefused,
                id="a-form-the-template-does-not-declare",
            ),
            pytest.param(
                affects(operator="absent/operator", roles={"cause": ref(ENTITY, GENE)}),
                ProfileError,
                id="a-missing-required-contract",
            ),
            pytest.param(affects(qualifiers=population(quantifier="invented")), ClaimError, id="a-quantifier"),
            pytest.param(
                correlates(member(ENTITY, GENE, 0), member(OUTCOME_SORT, OUTCOME)),
                CoefficientRefused,
                id="a-coefficient-below-one",
            ),
        ],
    )
    def test_each_ill_formed_input_is_refused_and_mints_nothing(self, profile, readable, wire, error):
        with pytest.raises(error):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_a_malformed_wire_value_refuses_before_any_contract_is_consulted(self, profile, readable):
        # `WireClaim`'s annotations are a wish, not a guarantee — it models
        # untrusted input, so the values below are exactly what arrives when the
        # writer disagreed with them. Each is given an operator no profile
        # declares, so a refusal that came from the profile would be a
        # `ProfileError`, not this one.
        for wire in [
            affects(operator=""),
            affects(roles="cause"),
            affects(roles={"cause": ref(ENTITY, GENE), "effect": ref(OUTCOME_SORT, 7)}),  # type: ignore[arg-type]
            affects(roles={"cause": ref(ENTITY, GENE), "effect": OUTCOME}),
            affects(qualifiers=[]),
            affects(qualifiers={"testing/population": {"quantifier": "generic"}}),
            # The v1 shape: a bare restriction term carries no sort.
            affects(qualifiers={"testing/population": {"quantifier": "generic", "restriction": ADULTS}}),
            affects(form=""),
        ]:
            absent = WireClaim(**{**vars(wire), "operator": wire.operator and "absent/operator"})
            for candidate in (wire, absent):
                with pytest.raises(MalformedWireClaim):
                    decode_claim(candidate, profile=profile, snapshot=readable)

    @pytest.mark.parametrize(
        "roles",
        [
            pytest.param([ref(ENTITY, GENE), ref(OUTCOME_SORT, OUTCOME)], id="a-list-roles"),
            pytest.param({"cause": [GENE], "effect": ref(OUTCOME_SORT, OUTCOME)}, id="a-list-of-terms-in-a-one-role"),
            pytest.param(
                {"cause": [member(ENTITY, GENE)], "effect": ref(OUTCOME_SORT, OUTCOME)},
                id="a-list-of-members-in-a-one-role",
            ),
            pytest.param(
                {"cause": {**ref(ENTITY, GENE), "extra": "x"}, "effect": ref(OUTCOME_SORT, OUTCOME)},
                id="a-stray-key-on-a-referent",
            ),
            pytest.param(
                {"cause": {"sort": ENTITY}, "effect": ref(OUTCOME_SORT, OUTCOME)}, id="a-referent-without-term"
            ),
            pytest.param({1: ref(ENTITY, GENE), "effect": ref(OUTCOME_SORT, OUTCOME)}, id="a-role-name-not-a-string"),
            pytest.param({"cause": None, "effect": ref(OUTCOME_SORT, OUTCOME)}, id="a-null-role"),
        ],
    )
    def test_wire_roles_shapes_refuse(self, profile, readable, roles):
        """Review Focus 1: a malformed `roles` value is `MalformedWireClaim`, never a
        `TypeError` and never a typing error that read the shape as something else."""
        with pytest.raises(MalformedWireClaim):
            decode_claim(affects(roles=roles), profile=profile, snapshot=readable)

    @pytest.mark.parametrize(
        "parties",
        [
            pytest.param([ref(ENTITY, GENE), ref(OUTCOME_SORT, OUTCOME)], id="members-without-coefficient"),
            pytest.param([member(ENTITY, GENE), {**member(OUTCOME_SORT, OUTCOME), "extra": 1}], id="a-stray-key"),
            pytest.param([member(ENTITY, GENE, True), member(OUTCOME_SORT, OUTCOME)], id="a-bool-coefficient"),
            pytest.param([member(ENTITY, GENE, 1.0), member(OUTCOME_SORT, OUTCOME)], id="a-float-coefficient"),
            pytest.param([member(ENTITY, GENE, "1"), member(OUTCOME_SORT, OUTCOME)], id="a-string-coefficient"),
            pytest.param([member(ENTITY, GENE), GENE], id="a-bare-term-member"),
        ],
    )
    def test_wire_many_members_shapes_refuse(self, profile, readable, parties):
        with pytest.raises(MalformedWireClaim):
            decode_claim(correlates(*parties), profile=profile, snapshot=readable)

    def test_a_referent_in_a_many_role_refuses(self, profile, readable):
        wire = WireClaim(
            operator="testing/correlates-with",
            roles={"parties": ref(ENTITY, GENE)},
            qualifiers={},
            form="polar",
            polarity="positive",
            layer="statistical",
        )
        with pytest.raises(MalformedWireClaim, match="`many` role"):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_a_value_merely_shaped_like_a_wire_claim_is_refused(self, profile, readable):
        class Impostor:
            operator = "testing/affects"
            roles: ClassVar[dict] = {"cause": ref(ENTITY, GENE), "effect": ref(OUTCOME_SORT, OUTCOME)}
            qualifiers: ClassVar[dict] = {}
            form = "polar"
            polarity = "positive"
            layer = "causal"

        with pytest.raises(MalformedWireClaim, match="WireClaim"):
            decode_claim(Impostor(), profile=profile, snapshot=readable)  # type: ignore[arg-type]

    def test_the_snapshot_is_authenticated(self, profile):
        class Impostor:
            identity = "0" * 64

            def resolve(self, sort, term):
                return TermOutcome.MEMBER

        with pytest.raises(MalformedWireClaim, match="ResolutionSnapshot"):
            decode_claim(affects(), profile=profile, snapshot=Impostor())  # type: ignore[arg-type]

    def test_a_raw_written_claim_is_an_audit_finding_not_a_decode_failure(self, profile):
        """The negative case.

        `object.__new__` reaches past the constructor, and past this boundary
        with it — the same act as a hand-edited file on disk. The distinction
        the row draws is that this is neither a silent accept nor a decode
        failure: decode was never involved. It is the third case, and it
        belongs to the audit surface rather than to a refusal.
        """
        forged = object.__new__(Claim)
        object.__setattr__(forged, "operator", "testing/affects")
        object.__setattr__(forged, "roles", {})
        assert isinstance(forged, Claim)
        assert forged.operator == "testing/affects"

    def test_retirement_is_not_enforced_at_decode(self, base_contract, testing_document):
        """The reason the two routes differ at all.

        Decode sees wire bytes and cannot tell a claim being authored now from
        one being restored from a backup. Refusing a retired identifier here
        would make every corpus holding a prior claim un-restorable — corrupting
        the history retirement exists to preserve.
        """
        from beliefs.contract import domain
        from beliefs.errors import WithdrawnFromAuthoring

        testing_document["templates"]["affects"]["retired"] = True
        retired = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [retired])
        snapshot = build_snapshot(readable={EX: [GENE, OUTCOME]})

        claim, receipt = decode_claim(affects(), profile=profile, snapshot=snapshot)
        assert claim.operator == "testing/affects"
        assert receipt.performed

        with pytest.raises(WithdrawnFromAuthoring):
            build_claim(profile, operator="testing/affects", roles=claim.roles, layer="causal", polarity="positive")


class TestTheFiveOutcomesStayDistinct:
    """The in-scope cases. `not-present` and `not-available`'s world-level arm are deferred."""

    def test_a_readable_vocabulary_yields_member_and_not_member(self, profile, readable):
        _, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert set(receipt.outcomes.values()) == {TermOutcome.MEMBER}
        assert readable.resolve(profile.sorts[ENTITY], ABSENT) is TermOutcome.NOT_MEMBER

    def test_an_unconsulted_namespace_yields_not_consulted(self, profile):
        _, receipt = decode_claim(affects(), profile=profile, snapshot=build_snapshot())
        assert set(receipt.outcomes.values()) == {TermOutcome.NOT_CONSULTED}

    def test_only_not_member_refuses(self):
        assert [outcome for outcome in TermOutcome if outcome.refuses] == [TermOutcome.NOT_MEMBER]

    def test_the_two_groups_do_not_mix(self):
        performed = {outcome for outcome in TermOutcome if outcome.performed}
        assert performed == {TermOutcome.MEMBER, TermOutcome.NOT_MEMBER}
        assert {outcome for outcome in TermOutcome} - performed == {
            TermOutcome.NOT_CONSULTED,
            TermOutcome.NOT_PRESENT,
            TermOutcome.NOT_AVAILABLE,
        }

    def test_no_outcome_collapses_into_another(self):
        values = [outcome.value for outcome in TermOutcome]
        assert len(set(values)) == len(values) == 5
        assert set(values) == {"member", "not-member", "not-consulted", "not-present", "not-available"}

    def test_there_is_no_fallback_to_another_release(self, profile):
        """An in-scope case, and the one a plausible convenience would break.

        A binding is a namespace **with** a release. A snapshot holding
        `EX@2025-01-01` says nothing about `EX@2026-01-01`, and resolving the
        second through the first would be answering a question about one dataset
        with evidence from another. The honest outcome is that nobody consulted
        the binding the contract actually names.
        """
        other_release = ReleaseBinding(namespace="EX", release="2025-01-01")
        snapshot = build_snapshot(readable={other_release: [GENE, OUTCOME]})
        _, receipt = decode_claim(affects(), profile=profile, snapshot=snapshot)
        assert set(receipt.outcomes.values()) == {TermOutcome.NOT_CONSULTED}

    def test_an_empty_readable_vocabulary_is_not_an_unconsulted_one(self, profile):
        """The other half of the same distinction, from the snapshot's side.

        *"Read it and it contains nothing"* is a finding; *"nobody looked"* is
        not. A snapshot that represented the first as the second would lose the
        evidence that makes `not-member` refuse.
        """
        with pytest.raises(UnboundReferent):
            decode_claim(affects(), profile=profile, snapshot=build_snapshot(readable={EX: []}))
        _, receipt = decode_claim(affects(), profile=profile, snapshot=build_snapshot())
        assert set(receipt.outcomes.values()) == {TermOutcome.NOT_CONSULTED}

    def test_not_present_is_reached_only_through_its_own_argument(self, profile):
        """`not-present` needs the world's word that the binding's corpus is absent,
        and only `build_snapshot(not_present=...)` carries it: none of the other
        availability states reaches it."""
        entity = profile.sorts[ENTITY]
        reachable = set()
        for snapshot in [
            build_snapshot(readable={EX: [GENE, OUTCOME]}),
            build_snapshot(readable={EX: []}),
            build_snapshot(unreadable=[EX]),
            build_snapshot(),
        ]:
            reachable.add(snapshot.resolve(entity, GENE))
        assert reachable == {
            TermOutcome.MEMBER,
            TermOutcome.NOT_MEMBER,
            TermOutcome.NOT_AVAILABLE,
            TermOutcome.NOT_CONSULTED,
        }
        assert TermOutcome.NOT_PRESENT not in reachable

    def test_a_binding_cannot_be_both_readable_and_unreadable(self):
        with pytest.raises(ResolutionError, match=r"more than one availability state \(readable and not-available\)"):
            build_snapshot(readable={EX: [GENE]}, unreadable=[EX])


class TestTheWireTypeIsConfinedToTheDecodeModule:
    """The second clause, testable for the first time now that `WireClaim` exists.

    Deferred twice as untestable, correctly: a test that a type does not appear
    where it should not cannot be written before the type does. It is asserted by
    walking the package's own signatures rather than by grepping the source,
    because a grep neither proves a signature accepts one nor survives a mention
    in a comment.
    """

    @staticmethod
    def _public_callables():
        import importlib
        import pkgutil

        import beliefs

        for info in pkgutil.walk_packages(beliefs.__path__, prefix="beliefs."):
            module = importlib.import_module(info.name)
            for name, value in vars(module).items():
                if name.startswith("_") or not callable(value):
                    continue
                if getattr(value, "__module__", None) != info.name:
                    continue
                yield info.name, name, value

    def test_no_signature_outside_decode_mentions_the_wire_type(self):
        import inspect

        offenders = []
        for module_name, name, value in self._public_callables():
            if module_name == "beliefs.decode":
                continue
            try:
                signature = inspect.signature(value)
            except (TypeError, ValueError):
                continue
            annotations = [str(p.annotation) for p in signature.parameters.values()]
            annotations.append(str(signature.return_annotation))
            if any("WireClaim" in annotation for annotation in annotations):
                offenders.append(f"{module_name}.{name}")
        assert offenders == []

    def test_the_decode_module_does_mention_it(self):
        """The other half, so the walk above cannot pass by finding nothing at all."""
        import inspect

        signature = inspect.signature(decode_claim)
        assert "WireClaim" in str(signature.parameters["wire"].annotation)

    def test_the_boundary_returns_a_claim_and_a_receipt(self, profile, readable):
        decoded = decode_claim(affects(), profile=profile, snapshot=readable)
        assert isinstance(decoded, tuple) and len(decoded) == 2
        claim, receipt = decoded
        assert isinstance(claim, Claim)
        assert isinstance(receipt, BindingCheckReceipt)

    def test_the_refusing_arm_produces_no_receipt(self, profile, readable):
        """`+ Refused` carries no second component, and the receipt is emitted on the accepting arm only."""
        with pytest.raises(DecodeError) as raised:
            decode_claim(affects(cause=ABSENT), profile=profile, snapshot=readable)
        assert not hasattr(raised.value, "receipt")


class TestDecodeInvertsTheProjection:
    """decode ∘ π_claim = identity, over the frozen parity vector and a hand-built set.

    The completeness check the arm-by-arm tests above cannot give. Each of those
    fixes one behaviour; this one asserts that the boundary as a whole puts back
    exactly the claim the projection took apart, for claims covering each role
    arity, both forms, both polarity regimes, the reserved role and every
    binding arm a role can reach. The `projection` **is** a wire claim's shape,
    because a serialized claim is a projection.

    The sign-inapt case is the one an earlier patched implementation slipped
    through: on the wire the polarity position carries `inapt`, and inside there
    is no polarity to supply, so the boundary has to map it back rather than
    forward it as an asserted sign.
    """

    @staticmethod
    def claims(profile) -> list[Claim]:
        cause = Referent(sort=ENTITY, term=GENE)
        effect = Referent(sort=OUTCOME_SORT, term=OUTCOME)
        adults = {"testing/population": Qualifier(quantifier="generic", restriction=Referent(sort=COHORT, term=ADULTS))}
        return [
            build_claim(
                profile,
                operator="testing/affects",
                roles={"cause": cause, "effect": effect},
                layer="causal",
                polarity="negative",
                qualifiers=adults,
            ),
            build_claim(
                profile,
                operator="testing/affects",
                roles={"cause": cause, "effect": effect},
                layer="statistical",
                form="null",
            ),
            build_claim(
                profile,
                operator="testing/affects",
                roles={"cause": cause, "effect": effect, "within-model": Referent(sort=PROCEDURE_SPEC, term=PROCEDURE)},
                layer="causal",
                polarity="unsigned",
            ),
            build_claim(
                profile,
                operator="testing/correlates-with",
                roles={
                    "parties": [
                        Member(Referent(sort=PRODUCT, term="EX:product-1")),
                        Member(Referent(sort=EVENT, term="EX:event-1")),
                    ]
                },
                layer="statistical",
                polarity="positive",
                qualifiers=adults,
            ),
            build_claim(
                profile,
                operator="testing/transforms",
                roles={
                    "inputs": [Member(Referent(sort=ENTITY, term=OTHER_GENE), 3), Member(cause, 2)],
                    "outputs": [Member(Referent(sort=ENTITY, term="EX:gene-w"))],
                    "facilitators": [],
                },
                layer="structural",
            ),
            build_claim(
                profile,
                operator="testing/measured-by",
                roles={"subject": cause, "instrument": Referent(sort=METHOD, term="EX:assay")},
                layer="methodological",
            ),
            build_claim(
                profile,
                operator="testing/promotes",
                roles={"cause": cause, "effect": effect},
                layer="causal",
                polarity="positive",
            ),
        ]

    @pytest.fixture()
    def fixture(self, parity_fixture_path):
        import json

        return json.loads(parity_fixture_path.read_text(encoding="utf-8"))

    @pytest.fixture()
    def every_term_readable(self, profile, fixture):
        """A snapshot holding every term the frozen vector mentions, under the
        binding its sort resolves through: a `selection` sort through its
        `selected` dataset, a `run-output` sort through its dataset, a
        `world-kind` sort through the kind inventory, and a `scheme` sort through
        its identifier class (always performed, so nothing is held for it).

        The terms are **canonicalized on the way in**, and one row makes that
        load-bearing: `affects-decomposed-restriction` holds its restriction in
        NFD deliberately, so that an implementation normalizing at parse time
        fails the fixture. A vocabulary stores canonical members and `resolve`
        normalizes what it is asked about.
        """
        from beliefs.contract.domain import RunOutputBinding, SchemeBinding, SelectionBinding, WorldKindBinding
        from beliefs.identifiers import canonical

        held: dict[Any, set[str]] = {}
        kinds: dict[str, set[str]] = {}
        for row in fixture["vector"]:
            referents: list[dict[str, str]] = []
            for value in row["projection"]["roles"].values():
                referents.extend([value] if isinstance(value, dict) else value)
            referents += [qualifier["restriction"] for qualifier in row["projection"]["qualifiers"].values()]
            for referent in referents:
                binding = profile.sorts[referent["sort"]].binding
                term = canonical(referent["term"])
                if isinstance(binding, SchemeBinding):
                    continue
                if isinstance(binding, WorldKindBinding):
                    kinds.setdefault(binding.world_kind, set()).add(term)
                    continue
                if isinstance(binding, SelectionBinding):
                    binding = DatasetBinding(dataset=binding.selected)
                elif isinstance(binding, RunOutputBinding):
                    binding = DatasetBinding(dataset=binding.dataset)
                held.setdefault(binding, set()).add(term)
        return build_snapshot(readable=held, kinds=kinds)

    def test_every_frozen_row_decodes_back_to_its_own_identity(self, profile, fixture, every_term_readable):
        """decode ∘ π_claim = identity over the frozen parity vector
        (`fixtures/claim-identity-v2.json`), whose coverage of every closed
        kernel tag and binding kind `test_parity_fixture.py` asserts. Nothing
        here re-derives the expected digests; they are the frozen ones."""
        assert fixture["claim_domain"] == "science.claim.v2"
        for row in fixture["vector"]:
            wire = WireClaim(**row["projection"])
            claim, receipt = decode_claim(wire, profile=profile, snapshot=every_term_readable)
            assert claim_identity(claim) == row["digest"], row["name"]
            assert receipt.claim_identity == row["digest"], row["name"]
            assert receipt.performed, row["name"]

    def test_the_frozen_sign_inapt_rows_round_trip_without_an_asserted_sign(
        self, profile, fixture, every_term_readable
    ):
        # Both routes to `inapt` on the wire: a sign-inapt template, and the
        # `null` form on a sign-apt one. Inside, there is no polarity to supply.
        rows = {row["name"]: row for row in fixture["vector"]}
        for name in ("transforms-structural", "affects-null-statistical"):
            row = rows[name]
            assert row["projection"]["polarity"] == profile.claim_grammar.sign_inapt_tag
            claim, _ = decode_claim(WireClaim(**row["projection"]), profile=profile, snapshot=every_term_readable)
            assert claim.polarity == profile.claim_grammar.sign_inapt_tag
            assert claim_identity(claim) == row["digest"]

    def test_decode_round_trips_projection(self, profile):
        for claim in self.claims(profile):
            decoded, receipt = decode_claim(wire_of(claim), profile=profile, snapshot=build_snapshot())
            assert project_claim(decoded) == project_claim(claim)
            assert claim_identity(decoded) == claim_identity(claim)
            assert receipt.claim_identity == claim_identity(claim)

    def test_the_sign_inapt_claim_round_trips_without_an_asserted_sign(self, profile):
        claim = self.claims(profile)[5]
        assert project_claim(claim)["polarity"] == profile.claim_grammar.sign_inapt_tag
        decoded, _ = decode_claim(wire_of(claim), profile=profile, snapshot=build_snapshot())
        assert decoded.polarity == profile.claim_grammar.sign_inapt_tag
        assert claim_identity(decoded) == claim_identity(claim)

    def test_members_written_out_of_order_decode_to_the_canonical_claim(self, profile):
        claim = self.claims(profile)[3]
        projection = project_claim(claim)
        parties = cast(dict[str, list[object]], projection["roles"])["parties"]
        reversed_wire = WireClaim(**{**projection, "roles": {"parties": list(reversed(parties))}})  # type: ignore[arg-type]
        decoded, _ = decode_claim(reversed_wire, profile=profile, snapshot=build_snapshot())
        assert claim_identity(decoded) == claim_identity(claim)

    def test_a_hand_supplied_inapt_tag_is_still_refused_on_the_authoring_route(self, profile):
        # The wire may carry it; an author may not. Decode maps the tag back to
        # the unit inhabitant, which is a different act from accepting it as a
        # sign — and `build_claim` still refuses it.
        with pytest.raises(PolarityRefused):
            build_claim(
                profile,
                operator="testing/measured-by",
                roles={
                    "subject": Referent(sort=ENTITY, term=GENE),
                    "instrument": Referent(sort=METHOD, term="EX:assay"),
                },
                layer="methodological",
                polarity=profile.claim_grammar.sign_inapt_tag,
            )


class TestStoredClaimTerms:
    def test_stored_claim_terms_lists_members_in_canonical_order(self):
        facet = {
            "operator": "testing/correlates-with",
            "roles": {
                "parties": [member(PRODUCT, "EX:product-1"), member(EVENT, "EX:event-1")],
                "within-model": ref(PROCEDURE_SPEC, PROCEDURE),
            },
            "qualifiers": {
                "testing/setting": {"quantifier": "generic", "restriction": ref(ENTITY, OTHER_GENE)},
                "testing/population": {"quantifier": "generic", "restriction": ref(COHORT, ADULTS)},
            },
            "form": "polar",
            "polarity": "positive",
            "layer": "statistical",
        }
        node = stored.proposition_node("p", title="p", claim=facet)
        roles, restrictions = stored_claim_terms(node)
        # Roles by name, members by canonical member key; restrictions by dimension.
        assert roles == (
            Referent(sort=EVENT, term="EX:event-1"),
            Referent(sort=PRODUCT, term="EX:product-1"),
            Referent(sort=PROCEDURE_SPEC, term=PROCEDURE),
        )
        assert restrictions == (Referent(sort=COHORT, term=ADULTS), Referent(sort=ENTITY, term=OTHER_GENE))

    def test_a_non_identifier_term_is_a_malformed_stored_value(self):
        facet = {
            **project_claim_facet(),
            "roles": {"cause": ref(ENTITY, GENE), "effect": {"sort": OUTCOME_SORT, "term": 7}},
        }
        with pytest.raises(MalformedWireClaim):
            stored_claim_terms(stored.proposition_node("p", title="p", claim=facet))


def project_claim_facet() -> dict[str, Any]:
    return {
        "operator": "testing/affects",
        "roles": {"cause": ref(ENTITY, GENE), "effect": ref(OUTCOME_SORT, OUTCOME)},
        "qualifiers": {},
        "form": "polar",
        "polarity": "positive",
        "layer": "causal",
    }


class TestTheWireValueIsCheckedFieldByField:
    @pytest.mark.parametrize(
        "body",
        [
            {1: "x", "quantifier": "generic", "restriction": ref(COHORT, ADULTS)},
            {"quantifier": "generic", "restriction": ref(COHORT, ADULTS), 1: "x"},
            {1: "x"},
            {"quantifier": "generic", "restriction": ref(COHORT, ADULTS), (): "x"},
            # Two unknown names of different types: this one crashes in `sorted`
            # rather than in `join`, which is why the guard has to precede the
            # whole field arithmetic and not merely its message.
            {"quantifier": "generic", "restriction": ref(COHORT, ADULTS), 1: "x", "extra": "y"},
            {"quantifier": "generic", "restriction": {**ref(COHORT, ADULTS), 1: "x", "extra": "y"}},
        ],
    )
    def test_a_field_name_that_is_not_a_name_refuses_rather_than_crashes(self, profile, readable, body):
        # The field arithmetic sorts the unknown names and joins them into a
        # message, and a non-string key raises `TypeError` in one or the other —
        # which is not a `DecodeError`, so a caller holding this boundary's
        # refusing arm gets a crash instead of a refusal, on input this function
        # exists to refuse.
        wire = affects(qualifiers={"testing/population": body})
        with pytest.raises(MalformedWireClaim):
            decode_claim(wire, profile=profile, snapshot=readable)

    @pytest.mark.parametrize(
        "wire",
        [
            pytest.param(
                affects(
                    roles={"cause": {**ref(ENTITY, GENE), 1: "x", "extra": "y"}, "effect": ref(OUTCOME_SORT, OUTCOME)}
                ),
                id="a-referent",
            ),
            pytest.param(
                correlates({**member(ENTITY, GENE), 1: "x", "extra": "y"}, member(OUTCOME_SORT, OUTCOME)), id="a-member"
            ),
        ],
    )
    def test_the_same_guard_covers_role_referents_and_members(self, profile, readable, wire):
        with pytest.raises(MalformedWireClaim):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_the_refusal_is_the_declared_arm_and_not_an_incidental_type_error(self, profile, readable):
        wire = affects(
            qualifiers={"testing/population": {1: "x", "quantifier": "generic", "restriction": ref(COHORT, ADULTS)}}
        )
        try:
            decode_claim(wire, profile=profile, snapshot=readable)
        except DecodeError:
            pass
        except TypeError as exc:  # pragma: no cover - the defect this pins
            pytest.fail(f"a raw TypeError escaped decodeClaim's refusing arm: {exc}")

    def test_an_unknown_qualifier_field_is_refused_never_ignored(self, profile, readable):
        # The same rule at this boundary: an unrecognized field is refused at load.
        # A wire value carrying one has been written by something that disagrees
        # with this reader about what a claim is, and guessing which of the two
        # is right is not a decision a decoder may take.
        wire = affects(
            qualifiers={
                "testing/population": {
                    "quantifier": "generic",
                    "restriction": ref(COHORT, ADULTS),
                    "confidence": "high",
                }
            }
        )
        with pytest.raises(MalformedWireClaim, match="confidence"):
            decode_claim(wire, profile=profile, snapshot=readable)


class TestMembershipIsDecidedUnderTheSameEquivalenceAsIdentity:
    """`science.identity.v1` normalizes to NFC **at encode time**, so `"é"` and
    `"é"` are one identifier to every digest here and two strings to
    Python. Membership is decided by string comparison, so without care the two
    relations disagree — and a vocabulary reports `not-member` for a term it
    holds.

    The resolution is **not** to canonicalize claims. The claim layer preserves
    what the author wrote; refusing or folding a decomposed referent would lose
    the author's bytes. So the snapshot stores canonically and `resolve`
    normalizes what it is asked about.
    """

    # The two spellings are written as escapes for the same reason the fixture
    # artifact holds its non-ASCII referents escaped: written literally, an
    # editor, merge tool or transfer that normalized this file would silently
    # delete the assertion, leaving a green test of nothing.
    COMPOSED: ClassVar[str] = "EX:caf\u00e9-cohort"
    DECOMPOSED: ClassVar[str] = "EX:cafe\u0301-cohort"

    def test_the_two_spellings_are_one_identifier_to_the_digest(self):
        assert self.COMPOSED != self.DECOMPOSED
        assert v1.encode(self.COMPOSED) == v1.encode(self.DECOMPOSED)

    def test_a_referent_may_still_hold_the_decomposed_form(self):
        # The rule this whole class is arranged around: canonicity is required
        # where identities are taken over projections, and *not* where an
        # author's bytes are being recorded.
        assert Referent(sort=COHORT, term=self.DECOMPOSED).term == self.DECOMPOSED

    def test_a_decomposed_term_resolves_against_a_composed_member(self, profile):
        snapshot = build_snapshot(readable={COHORT_DATASET: [self.COMPOSED]})
        cohort = profile.sorts[COHORT]
        assert snapshot.resolve(cohort, self.DECOMPOSED) is TermOutcome.MEMBER
        assert snapshot.resolve(cohort, self.COMPOSED) is TermOutcome.MEMBER

    def test_a_noncanonical_member_is_refused_rather_than_stored(self):
        # The other half. Stored non-canonically, this member encodes identically
        # to its canonical spelling — so a vocabulary could hold two members the
        # projection cannot tell apart, and `resolve` would decide by whichever
        # spelling happened to be written down.
        with pytest.raises(ResolutionError, match="not in NFC"):
            build_snapshot(readable={COHORT_DATASET: [self.DECOMPOSED]})

    def test_a_binding_field_that_is_not_canonical_is_refused(self):
        # Two bindings differing only in normalization are two dictionary keys and
        # one encoded binding, which is the collision arriving through the text.
        with pytest.raises(MalformedContract, match="not in NFC"):
            ReleaseBinding(namespace="cafe\u0301", release="2026-01-01")
        assert ReleaseBinding(namespace="caf\u00e9", release="2026-01-01").namespace

    def test_the_two_would_have_encoded_alike(self):
        # What that refusal prevents, reached through the raw route since the
        # ordinary one is now closed: two unequal bindings, one encoding.
        one = ReleaseBinding(namespace="caf\u00e9", release="2026-01-01")
        other = object.__new__(ReleaseBinding)
        for field, value in (("namespace", "cafe\u0301"), ("release", "2026-01-01")):
            object.__setattr__(other, field, value)
        assert one != other
        assert v1.encode(one.projection()) == v1.encode(other.projection())

    def test_the_whole_thing_end_to_end(self, profile):
        # A claim whose restriction is decomposed, against a vocabulary holding
        # the composed form: accepted, checked, and identical in identity to the
        # composed spelling of the same claim.
        held = build_snapshot(readable={EX: [GENE, OUTCOME], COHORT_DATASET: [self.COMPOSED]})
        claims = []
        for spelling in (self.DECOMPOSED, self.COMPOSED):
            wire = affects(qualifiers=population(ref(COHORT, spelling)))
            claim, receipt = decode_claim(wire, profile=profile, snapshot=held)
            assert receipt.outcomes["restriction:testing/population"] is TermOutcome.MEMBER
            assert receipt.performed
            claims.append(claim)
        assert claims[0].qualifiers["testing/population"].restriction.term == self.DECOMPOSED
        assert claim_identity(claims[0]) == claim_identity(claims[1])


class TestTheSnapshotIdentityIsContentDerived:
    def test_two_snapshots_differing_only_in_terms_have_different_identities(self):
        # Otherwise the receipt's snapshot identity would not pin what was read,
        # and two decodes resolving different vocabularies would be indistinguishable.
        one = build_snapshot(readable={EX: [GENE]})
        two = build_snapshot(readable={EX: [GENE, OUTCOME]})
        assert one.identity != two.identity

    def test_the_same_contents_give_the_same_identity_whatever_the_order(self):
        one = build_snapshot(readable={EX: [GENE, OUTCOME], COHORT_DATASET: [ADULTS]}, kinds={"procedure": [PROCEDURE]})
        two = build_snapshot(
            kinds={"procedure": (PROCEDURE,)}, readable={COHORT_DATASET: [ADULTS], EX: [OUTCOME, GENE]}
        )
        assert one.identity == two.identity

    def test_readable_and_unreadable_differ(self):
        assert build_snapshot(readable={EX: []}).identity != build_snapshot(unreadable=[EX]).identity


class TestTheSnapshotAuthenticatesWhatItIsBuiltFrom:
    """A snapshot is the third parameter that makes decode a function, and its
    contents come from the caller — so *it* is where the caller's values are
    checked. Everything else in this file resolves against a snapshot already
    built; these are the arms that decide what one may be built from.
    """

    def test_a_key_that_is_not_a_binding_is_refused(self):
        # Keys are matched by value against `profile.sorts[...].binding`, so a
        # lookalike matches nothing and every term under it resolves
        # `not-consulted` — a snapshot that was handed a vocabulary reporting
        # that nobody looked at it.
        with pytest.raises(ResolutionError, match="keyed by SortBinding"):
            build_snapshot(readable={"EX": [GENE]})  # type: ignore[arg-type]

    def test_a_lookalike_binding_is_refused_before_it_can_be_asked_to_project(self):
        class Lookalike:
            def projection(self) -> dict[str, object]:
                return {"namespace": "EX", "release": "2026-01-01"}

        with pytest.raises(ResolutionError, match="keyed by SortBinding"):
            build_snapshot(unreadable=[Lookalike()])  # type: ignore[arg-type]

    @pytest.mark.parametrize("term", [1, "", None, ("EX", "gene-x")])
    def test_a_member_that_is_not_a_term_identifier_is_refused(self, term):
        with pytest.raises(ResolutionError):
            build_snapshot(readable={EX: [term]})

    def test_a_single_string_is_not_a_vocabulary(self):
        # `str` satisfies `Iterable[str]`, so this type-checks and builds a
        # vocabulary of six characters — none of them the term it was written to
        # declare present, which then resolves `not-member`. The wire decoder
        # already refuses a bare string where it wants members; this is the same
        # guard, at the boundary that had not carried it over.
        snapshot = None
        with pytest.raises(ResolutionError, match="single string"):
            snapshot = build_snapshot(readable={EX: GENE})
        assert snapshot is None

    @pytest.mark.parametrize("terms", [None, 7])
    def test_a_vocabulary_that_is_not_a_collection_is_refused(self, terms):
        with pytest.raises(ResolutionError, match="collection of terms"):
            build_snapshot(readable={EX: terms})  # type: ignore[dict-item]

    def test_that_predicate_is_the_one_a_referent_applies(self):
        # The two have to agree, and this is the sharper direction: a `Referent`
        # cannot carry a non-identifier term, so a snapshot holding one holds a
        # member no claim can ever name. `resolve` would then answer
        # `not-member` — the single *refusing* outcome, positive evidence that a
        # vocabulary was read and lacks the term — about a vocabulary that was
        # told it has it.
        for admitted in [GENE, "1"]:
            assert Referent(sort=ENTITY, term=admitted).term == admitted
            build_snapshot(readable={EX: [admitted]})
        for refused in [1, ""]:
            with pytest.raises(MalformedReferent):
                Referent(sort=ENTITY, term=refused)  # type: ignore[arg-type]
            with pytest.raises(ResolutionError):
                build_snapshot(readable={EX: [refused]})  # type: ignore[list-item]

    def test_the_integer_member_case_end_to_end(self, profile):
        # What the refusal above prevents, spelled out: the snapshot is told the
        # vocabulary holds 1, the claim names "1", and the receipt reports
        # `not-member` — a finding of absence about a term that was supplied.
        # Built through the raw route, which stands in for the one now closed.
        snapshot = ResolutionSnapshot._built(
            resolution._MINT,
            bindings={
                EX: resolution._BoundVocabulary(
                    state="readable",
                    terms=frozenset([1]),  # type: ignore[arg-type]
                    absent=(),
                )
            },
            kinds={},
            identity="unchecked",
        )
        assert snapshot.resolve(profile.sorts[ENTITY], "1") is TermOutcome.NOT_MEMBER
        with pytest.raises(ResolutionError):
            build_snapshot(readable={EX: [1]})  # type: ignore[list-item]
