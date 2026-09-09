"""`decode_claim` — M4, M11, and D3's in-cut arms.

The boundary every import, deserialization and restore comes through. Three
guarantee rows meet here, and they are kept apart deliberately: **M4** is about
referent typing and the receipt, **M11** about the function being a function of
its arguments, and **D3** about the five outcomes staying distinct.

One scope note that a reader will otherwise have to reconstruct. `not-available`
appears in both M4 and D3 and they are **not the same test**. M4's is local — the
vocabulary could not be read. D3's world-level `not-present` means the dataset's
covered corpus is absent. The cut keeps the two distinct.
"""

import subprocess
import sys
import textwrap
from typing import ClassVar

import pytest

from beliefs import resolution
from beliefs.claim import Claim, Referent, build_claim
from beliefs.contract.domain import VocabularyBinding
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import (
    ArityMismatch,
    ClaimError,
    DecodeError,
    InadmissibleLayer,
    MalformedContract,
    MalformedReferent,
    MalformedWireClaim,
    PolarityRefused,
    ProfileError,
    ResolutionError,
    UnboundReferent,
    UndeclaredDimension,
)
from beliefs.identifiers import canonical
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity
from beliefs.resolution import BindingCheckReceipt, ReferentPosition, ResolutionSnapshot, TermOutcome, build_snapshot

EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
COHORT_DATASET = VocabularyBinding(namespace=None, release=None, dataset_identity="0" * 64)

GENE = "EX:gene-x"
OTHER_GENE = "EX:gene-z"
OUTCOME = "EX:outcome-y"
ADULTS = "EX:adults"
ABSENT = "EX:not-in-the-vocabulary"


@pytest.fixture()
def profile(base_contract, testing_contract_path):
    from beliefs.contract import load_domain_contract

    testing = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def readable():
    """Both vocabularies read, holding every term these tests bind."""
    return build_snapshot(readable={EX: [GENE, OTHER_GENE, OUTCOME], COHORT_DATASET: [ADULTS]})


def affects(*, args=(GENE, OUTCOME), qualifiers=None, polarity="positive", layer="causal"):
    return WireClaim(
        operator="testing/affects",
        args=list(args),
        qualifiers=qualifiers or {},
        polarity=polarity,
        layer=layer,
    )


class TestM4TypedReferentsAndTheReceipt:
    def test_a_member_term_is_accepted_with_the_check_performed(self, profile, readable):
        claim, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert claim.args[0] == claim.args[0].__class__(sort="testing/entity", term=GENE)
        assert set(receipt.outcomes.values()) == {TermOutcome.MEMBER}
        assert receipt.performed

    def test_a_term_absent_from_a_readable_vocabulary_refuses_and_mints_nothing(self, profile, readable):
        # The sabotage arm of M4's row, and the only one of the five that refuses.
        with pytest.raises(UnboundReferent) as raised:
            decode_claim(affects(args=(ABSENT, OUTCOME)), profile=profile, snapshot=readable)
        assert "argument:0" in str(raised.value)
        assert "Nothing was minted" in str(raised.value)

    def test_availability_is_not_membership(self, profile, readable):
        """M4's negative arm: the same bad term, accepted when nothing was read.

        This is the pair the design exists to keep apart. Refusing here would
        report *"not in the vocabulary"* on the evidence that nobody looked —
        the same error §7.2 was written to avoid, committed by the decoder.
        """
        bad = affects(args=(ABSENT, OUTCOME))
        with pytest.raises(UnboundReferent):
            decode_claim(bad, profile=profile, snapshot=readable)

        unreadable = build_snapshot(unreadable=[EX])
        claim, receipt = decode_claim(bad, profile=profile, snapshot=unreadable)
        assert receipt.outcomes["argument:0"] is TermOutcome.NOT_AVAILABLE
        assert not receipt.performed
        assert claim.args[0].term == ABSENT

    def test_the_two_accepting_receipts_are_distinguishable(self, profile):
        """Also M4's negative arm: accepted-and-checked must not look like accepted-and-unchecked."""
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
        wire = affects(qualifiers={"testing/population": {"quantifier": "generic", "restriction": ADULTS}})
        claim, receipt = decode_claim(wire, profile=profile, snapshot=readable)

        expected = {ReferentPosition.argument(0).label(), ReferentPosition.argument(1).label()} | {
            ReferentPosition.restriction("testing/population").label()
        }
        assert set(receipt.outcomes) == expected
        assert len(receipt.outcomes) == len(claim.args) + len(claim.qualifiers)

    def test_a_restriction_is_resolved_exactly_as_an_argument_is(self, profile):
        # §6.4: a restriction is sorted as an argument is, so it resolves as one.
        # `cohort` binds a dataset, not the EX namespace, so a snapshot holding
        # only EX leaves the restriction unconsulted while the arguments are read.
        wire = affects(qualifiers={"testing/population": {"quantifier": "generic", "restriction": ADULTS}})
        _, receipt = decode_claim(wire, profile=profile, snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}))
        assert receipt.outcomes["argument:0"] is TermOutcome.MEMBER
        assert receipt.outcomes["restriction:testing/population"] is TermOutcome.NOT_CONSULTED

    def test_a_bad_restriction_refuses_like_a_bad_argument(self, profile, readable):
        wire = affects(qualifiers={"testing/population": {"quantifier": "generic", "restriction": "EX:nobody"}})
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
            ResolutionSnapshot(bindings={}, identity="x")

    def test_a_bare_string_cannot_occupy_a_slot_inside(self, profile, readable):
        """M4's static arm, at this boundary.

        The wire carries bare strings — that is what a wire is. What the boundary
        guarantees is that nothing bare survives it: every slot of the decoded
        claim holds a `Referent` carrying the sort its declaration names.
        """
        claim, _ = decode_claim(affects(), profile=profile, snapshot=readable)
        assert [referent.sort for referent in claim.args] == ["testing/entity", "testing/outcome"]
        assert all(not isinstance(slot, str) for slot in claim.args)


class TestM11DecodeIsAFunctionOfItsArguments:
    def test_the_same_three_inputs_decode_identically_in_another_process(
        self, profile, readable, base_contract_path, testing_contract_path
    ):
        """M11's first arm, run as it is written: *in different processes*.

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
            from beliefs.contract.domain import VocabularyBinding
            from beliefs.profile import compile_profile
            from beliefs.decode import WireClaim, decode_claim
            from beliefs.projection import claim_identity
            from beliefs.resolution import build_snapshot

            base = load_base_contract(Path({str(base_contract_path)!r}))
            testing = load_domain_contract(Path({str(testing_contract_path)!r}), base=base, predecessor=None)
            profile = compile_profile(base, [testing])
            EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
            COHORT = VocabularyBinding(namespace=None, release=None, dataset_identity="0" * 64)
            snapshot = build_snapshot(readable={{EX: [{GENE!r}, {OTHER_GENE!r}, {OUTCOME!r}], COHORT: [{ADULTS!r}]}})
            wire = WireClaim(
                operator="testing/affects",
                args=[{GENE!r}, {OUTCOME!r}],
                qualifiers={{}},
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
        """M11's sabotage arm, closed by construction rather than by a check.

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
        bad = affects(args=(ABSENT, OUTCOME))
        with pytest.raises(UnboundReferent):
            decode_claim(bad, profile=profile, snapshot=build_snapshot(readable={EX: [GENE, OUTCOME]}))
        _, receipt = decode_claim(bad, profile=profile, snapshot=build_snapshot())
        assert receipt.outcomes["argument:0"] is TermOutcome.NOT_CONSULTED

    @pytest.mark.parametrize(
        ("wire", "error"),
        [
            pytest.param(
                WireClaim(
                    operator="testing/subtype-of",
                    args=[GENE, OTHER_GENE],
                    qualifiers={},
                    polarity="positive",
                    layer="structural",
                ),
                PolarityRefused,
                id="a-sign-on-a-sign-inapt-operator",
            ),
            pytest.param(affects(args=(GENE,)), ArityMismatch, id="wrong-arity"),
            pytest.param(
                affects(qualifiers={"testing/absent": {"quantifier": "generic", "restriction": ADULTS}}),
                UndeclaredDimension,
                id="an-undeclared-dimension",
            ),
            pytest.param(affects(layer="statistical"), InadmissibleLayer, id="an-inadmissible-layer"),
            pytest.param(
                WireClaim(operator="absent/operator", args=[GENE], qualifiers={}, polarity="positive", layer="causal"),
                ProfileError,
                id="a-missing-required-contract",
            ),
            pytest.param(
                affects(qualifiers={"testing/population": {"quantifier": "invented", "restriction": ADULTS}}),
                ClaimError,
                id="a-quantifier-outside-the-closed-set",
            ),
        ],
    )
    def test_each_ill_formed_input_is_refused_and_mints_nothing(self, profile, readable, wire, error):
        with pytest.raises(error):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_a_malformed_wire_value_refuses_before_any_contract_is_consulted(self, profile, readable):
        # `WireClaim`'s annotations are a wish, not a guarantee — it models
        # untrusted input, so the values below are exactly what arrives when the
        # writer disagreed with them. The type checker is told to allow what the
        # run time is being asked to refuse.
        for wire in [
            WireClaim(operator="", args=[GENE, OUTCOME], qualifiers={}, polarity="positive", layer="causal"),
            WireClaim(operator="testing/affects", args=GENE, qualifiers={}, polarity="positive", layer="causal"),
            WireClaim(
                operator="testing/affects",
                args=[GENE, 7],  # type: ignore[list-item]
                qualifiers={},
                polarity="positive",
                layer="causal",
            ),
            WireClaim(
                operator="testing/affects",
                args=[GENE, OUTCOME],
                qualifiers=[],  # type: ignore[arg-type]
                polarity="positive",
                layer="causal",
            ),
            WireClaim(
                operator="testing/affects",
                args=[GENE, OUTCOME],
                qualifiers={"testing/population": {"quantifier": "generic"}},
                polarity="positive",
                layer="causal",
            ),
        ]:
            with pytest.raises(MalformedWireClaim):
                decode_claim(wire, profile=profile, snapshot=readable)

    def test_a_value_merely_shaped_like_a_wire_claim_is_refused(self, profile, readable):
        class Impostor:
            operator = "testing/affects"
            args = (GENE, OUTCOME)
            qualifiers: ClassVar[dict] = {}
            polarity = "positive"
            layer = "causal"

        with pytest.raises(MalformedWireClaim, match="WireClaim"):
            decode_claim(Impostor(), profile=profile, snapshot=readable)  # type: ignore[arg-type]

    def test_the_snapshot_is_authenticated(self, profile):
        class Impostor:
            identity = "0" * 64

            def resolve(self, binding, term):
                return TermOutcome.MEMBER

        with pytest.raises(MalformedWireClaim, match="ResolutionSnapshot"):
            decode_claim(affects(), profile=profile, snapshot=Impostor())  # type: ignore[arg-type]

    def test_a_raw_written_claim_is_an_audit_finding_not_a_decode_failure(self, profile):
        """M11's negative arm.

        `object.__new__` reaches past the constructor, and past this boundary
        with it — the same act as a hand-edited file on disk. The distinction
        the row draws is that this is neither a silent accept nor a decode
        failure: decode was never involved. It is §6.3's third row, and it
        belongs to the audit surface rather than to a refusal.
        """
        forged = object.__new__(Claim)
        object.__setattr__(forged, "operator", "testing/affects")
        object.__setattr__(forged, "args", ())
        assert isinstance(forged, Claim)
        assert forged.operator == "testing/affects"

    def test_retirement_is_not_enforced_at_decode(self, base_contract, testing_document):
        """§7.3a, and the reason the two routes differ at all.

        Decode sees wire bytes and cannot tell a claim being authored now from
        one being restored from a backup. Refusing a retired identifier here
        would make every corpus holding a prior claim un-restorable — corrupting
        the history retirement exists to preserve.
        """
        import copy

        from beliefs.contract import domain
        from beliefs.errors import WithdrawnFromAuthoring

        document = copy.deepcopy(testing_document)
        document["operators"]["affects"]["retired"] = True
        retired = domain.parse_domain_contract(document, source="<t>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [retired])
        snapshot = build_snapshot(readable={EX: [GENE, OUTCOME]})

        claim, receipt = decode_claim(affects(), profile=profile, snapshot=snapshot)
        assert claim.operator == "testing/affects"
        assert receipt.performed

        with pytest.raises(WithdrawnFromAuthoring):
            build_claim(
                profile,
                operator="testing/affects",
                args=claim.args,
                layer="causal",
                polarity="positive",
            )


class TestD3TheFiveOutcomesStayDistinct:
    """D3's in-cut arms. `not-present` and `not-available`'s world-level arm are deferred."""

    def test_a_readable_vocabulary_yields_member_and_not_member(self, profile, readable):
        _, receipt = decode_claim(affects(), profile=profile, snapshot=readable)
        assert set(receipt.outcomes.values()) == {TermOutcome.MEMBER}
        assert readable.resolve(EX, ABSENT) is TermOutcome.NOT_MEMBER

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
        """D3's in-cut arm, and the one a plausible convenience would break.

        A binding is a namespace **with** a release (D §5). A snapshot holding
        `EX@2025-01-01` says nothing about `EX@2026-01-01`, and resolving the
        second through the first would be answering a question about one dataset
        with evidence from another. The honest outcome is that nobody consulted
        the binding the contract actually names.
        """
        other_release = VocabularyBinding(namespace="EX", release="2025-01-01", dataset_identity=None)
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

    def test_not_present_is_unreachable_in_this_cut_and_that_is_recorded(self, profile):
        """Stated as a test rather than left as a silence.

        `not-present` needs the world index and holding machinery — D3's
        deferred arm. Nothing in cut 1 can construct it, and the outcome is
        defined anyway: implementing four of five would be a different closed
        set than §7.2 rules, and the gap would be invisible.
        """
        reachable = set()
        for snapshot in [
            build_snapshot(readable={EX: [GENE, OUTCOME]}),
            build_snapshot(readable={EX: []}),
            build_snapshot(unreadable=[EX]),
            build_snapshot(),
        ]:
            reachable.add(snapshot.resolve(EX, GENE))
        assert reachable == {
            TermOutcome.MEMBER,
            TermOutcome.NOT_MEMBER,
            TermOutcome.NOT_AVAILABLE,
            TermOutcome.NOT_CONSULTED,
        }
        assert TermOutcome.NOT_PRESENT not in reachable

    def test_a_binding_cannot_be_both_readable_and_unreadable(self):
        with pytest.raises(ResolutionError, match="both readable and unreadable"):
            build_snapshot(readable={EX: [GENE]}, unreadable=[EX])


class TestM13TheWireTypeIsConfinedToTheDecodeModule:
    """M13's second clause, testable for the first time now that `WireClaim` exists.

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
            decode_claim(affects(args=(ABSENT, OUTCOME)), profile=profile, snapshot=readable)
        assert not hasattr(raised.value, "receipt")


class TestDecodeInvertsTheProjection:
    """decode ∘ π_claim = identity, over M10's frozen corpus.

    The completeness check the arm-by-arm tests above cannot give. Each of those
    fixes one behaviour; this one asserts that the boundary as a whole puts back
    exactly the claim the projection took apart — for every closed kernel tag,
    since the vector's coverage is asserted complete against the base contract.

    It reuses M10's fixture rather than inventing claims, which is the point: the
    `projection` field **is** a wire claim's shape, because a serialized claim is
    a projection. Nothing here re-derives the expected digests; they are the
    frozen ones.

    Written after sabotage found the gap — passing the wire polarity through
    unmapped left every arm green, because no test decoded a **successful**
    sign-inapt claim. §7.5 always emits the polarity position, so `inapt` is on
    the wire for an operator whose `Polarity(op)` is the unit type, and the
    boundary has to map it back to *there is nothing to supply* rather than
    forward it as an asserted sign.
    """

    @pytest.fixture()
    def fixture(self, parity_fixture_path):
        import json

        return json.loads(parity_fixture_path.read_text(encoding="utf-8"))

    @pytest.fixture()
    def every_term_readable(self, profile, fixture):
        """A snapshot holding every term the vector mentions, grouped by the binding its sort names.

        The terms are **canonicalized on the way in**, and one row makes that
        load-bearing: `affects-decomposed-referent` holds its restriction in NFD
        deliberately, so that an implementation normalizing at parse time fails
        the fixture. A vocabulary stores canonical members and `resolve`
        normalizes what it is asked about, which is how a legitimately decomposed
        claim term resolves `member` against the composed one it names.
        """
        held: dict[VocabularyBinding, set[str]] = {}
        for row in fixture["vector"]:
            referents = list(row["claim"]["args"])
            referents += [qualifier["restriction"] for qualifier in row["claim"]["qualifiers"].values()]
            for referent in referents:
                binding = profile.sorts[referent["sort"]].vocabulary
                held.setdefault(binding, set()).add(canonical(referent["term"]))
        return build_snapshot(readable=held)

    def test_every_frozen_row_decodes_back_to_its_own_identity(self, profile, fixture, every_term_readable):
        for row in fixture["vector"]:
            projection = row["projection"]
            wire = WireClaim(
                operator=projection["operator"],
                args=projection["args"],
                qualifiers=projection["qualifiers"],
                polarity=projection["polarity"],
                layer=projection["layer"],
            )
            claim, receipt = decode_claim(wire, profile=profile, snapshot=every_term_readable)
            assert claim_identity(claim) == row["digest"], row["name"]
            assert receipt.claim_identity == row["digest"], row["name"]
            assert receipt.performed, row["name"]

    def test_the_sign_inapt_row_round_trips_without_an_asserted_sign(self, profile, fixture, every_term_readable):
        # Called out separately because it is the row whose absence made an
        # earlier sabotage pass: on the wire the position carries `inapt`, and
        # inside there is no polarity to supply at all (§6.3, §7.5).
        row = next(r for r in fixture["vector"] if r["name"] == "subtype-of-inapt-structural")
        wire = WireClaim(**{k: row["projection"][k] for k in ("operator", "args", "qualifiers", "polarity", "layer")})
        claim, _ = decode_claim(wire, profile=profile, snapshot=every_term_readable)
        assert claim.polarity == profile.claim_grammar.sign_inapt_tag
        assert claim_identity(claim) == row["digest"]

    def test_a_hand_supplied_inapt_tag_is_still_refused_on_the_authoring_route(self, profile):
        # The wire may carry it; an author may not. Decode maps the tag back to
        # the unit inhabitant, which is a different act from accepting it as a
        # sign — and `build_claim` still refuses it.
        from beliefs.errors import PolarityRefused

        with pytest.raises(PolarityRefused):
            build_claim(
                profile,
                operator="testing/subtype-of",
                args=(
                    Referent(sort="testing/entity", term=GENE),
                    Referent(sort="testing/entity", term=OTHER_GENE),
                ),
                layer="structural",
                polarity=profile.claim_grammar.sign_inapt_tag,
            )


class TestTheWireValueIsCheckedFieldByField:
    @pytest.mark.parametrize(
        "body",
        [
            {1: "x", "quantifier": "generic", "restriction": ADULTS},
            {"quantifier": "generic", "restriction": ADULTS, 1: "x"},
            {1: "x"},
            {"quantifier": "generic", "restriction": ADULTS, (): "x"},
            # Two unknown names of different types: this one crashes in `sorted`
            # rather than in `join`, which is why the guard has to precede the
            # whole field arithmetic and not merely its message.
            {"quantifier": "generic", "restriction": ADULTS, 1: "x", "extra": "y"},
        ],
    )
    def test_a_field_name_that_is_not_a_name_refuses_rather_than_crashes(self, profile, readable, body):
        # The field arithmetic below sorts the unknown names and joins them into
        # a message, and a non-string key raises `TypeError` in one or the other
        # — which is not a `DecodeError`, so a caller holding this boundary's
        # refusing arm gets a crash instead of a refusal, on input this function
        # exists to refuse. The contract loaders check mapping keys before their
        # own field arithmetic for the same reason; this is that guard at the
        # boundary that had skipped it.
        wire = affects(qualifiers={"testing/population": body})
        with pytest.raises(MalformedWireClaim):
            decode_claim(wire, profile=profile, snapshot=readable)

    def test_the_refusal_is_the_declared_arm_and_not_an_incidental_type_error(self, profile, readable):
        wire = affects(qualifiers={"testing/population": {1: "x", "quantifier": "generic", "restriction": ADULTS}})
        try:
            decode_claim(wire, profile=profile, snapshot=readable)
        except DecodeError:
            pass
        except TypeError as exc:  # pragma: no cover - the defect this pins
            pytest.fail(f"a raw TypeError escaped decodeClaim's refusing arm: {exc}")

    def test_an_unknown_qualifier_field_is_refused_never_ignored(self, profile, readable):
        # D5's rule at this boundary: an unrecognized field is refused at load.
        # A wire value carrying one has been written by something that disagrees
        # with this reader about what a claim is, and guessing which of the two
        # is right is not a decision a decoder may take.
        wire = affects(
            qualifiers={"testing/population": {"quantifier": "generic", "restriction": ADULTS, "confidence": "high"}}
        )
        with pytest.raises(MalformedWireClaim, match="confidence"):
            decode_claim(wire, profile=profile, snapshot=readable)


class TestMembershipIsDecidedUnderTheSameEquivalenceAsIdentity:
    """`science.identity.v1` normalizes to NFC **at encode time**, so `"é"` and
    `"é"` are one identifier to every digest here and two strings to
    Python. Membership is decided by string comparison, so without care the two
    relations disagree — and a vocabulary reports `not-member` for a term it
    holds.

    The resolution is **not** to canonicalize claims. The claim layer preserves
    what the author wrote, and the `affects-decomposed-referent` fixture row
    exists to catch an implementation that normalizes at parse time; refusing or
    folding a decomposed referent would make this implementation the one that row
    is aimed at. So the snapshot stores canonically and `resolve` normalizes what
    it is asked about.
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
        assert Referent(sort="testing/cohort", term=self.DECOMPOSED).term == self.DECOMPOSED

    def test_a_decomposed_term_resolves_against_a_composed_member(self):
        snapshot = build_snapshot(readable={EX: [self.COMPOSED]})
        assert snapshot.resolve(EX, self.DECOMPOSED) is TermOutcome.MEMBER
        assert snapshot.resolve(EX, self.COMPOSED) is TermOutcome.MEMBER

    def test_a_noncanonical_member_is_refused_rather_than_stored(self):
        # The other half. Stored non-canonically, this member encodes identically
        # to its canonical spelling — so a vocabulary could hold two members the
        # projection cannot tell apart, and `resolve` would decide by whichever
        # spelling happened to be written down.
        with pytest.raises(ResolutionError, match="not in NFC"):
            build_snapshot(readable={EX: [self.DECOMPOSED]})

    def test_a_binding_field_that_is_not_canonical_is_refused(self):
        # `VocabularyBinding` is the other collision: two bindings differing only
        # in normalization are two dictionary keys and one encoded binding, which
        # is the sum-versus-product collision arriving through the text.
        with pytest.raises(MalformedContract, match="not in NFC"):
            VocabularyBinding(namespace="cafe\u0301", release="2026-01-01", dataset_identity=None)
        assert VocabularyBinding(namespace="caf\u00e9", release="2026-01-01", dataset_identity=None).namespace

    def test_the_two_would_have_encoded_alike(self):
        # What that refusal prevents, reached through §6.3's raw route since the
        # ordinary one is now closed: two unequal bindings, one encoding.
        one = VocabularyBinding(namespace="caf\u00e9", release="2026-01-01", dataset_identity=None)
        other = object.__new__(VocabularyBinding)
        for field, value in (("namespace", "cafe\u0301"), ("release", "2026-01-01"), ("dataset_identity", None)):
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
            wire = affects(qualifiers={"testing/population": {"quantifier": "generic", "restriction": spelling}})
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
        one = build_snapshot(readable={EX: [GENE, OUTCOME], COHORT_DATASET: [ADULTS]})
        two = build_snapshot(readable={COHORT_DATASET: [ADULTS], EX: [OUTCOME, GENE]})
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
        # Keys are matched by value against `profile.sorts[...].vocabulary`, so a
        # lookalike matches nothing and every term under it resolves
        # `not-consulted` — a snapshot that was handed a vocabulary reporting
        # that nobody looked at it.
        with pytest.raises(ResolutionError, match="keyed by VocabularyBinding"):
            build_snapshot(readable={"EX": [GENE]})  # type: ignore[arg-type]

    def test_a_lookalike_binding_is_refused_before_it_can_be_asked_to_project(self):
        class Lookalike:
            def projection(self) -> dict[str, object]:
                return {"namespace": "EX", "release": "2026-01-01"}

        with pytest.raises(ResolutionError, match="keyed by VocabularyBinding"):
            build_snapshot(unreadable=[Lookalike()])  # type: ignore[arg-type]

    @pytest.mark.parametrize("term", [1, "", None, ("EX", "gene-x")])
    def test_a_member_that_is_not_a_term_identifier_is_refused(self, term):
        with pytest.raises(ResolutionError):
            build_snapshot(readable={EX: [term]})

    def test_a_single_string_is_not_a_vocabulary(self):
        # `str` satisfies `Iterable[str]`, so this type-checks and builds a
        # vocabulary of six characters — none of them the term it was written to
        # declare present, which then resolves `not-member`. The wire decoder
        # already refuses a bare string where it wants a sequence of terms; this
        # is the same guard, at the boundary that had not carried it over.
        snapshot = None
        with pytest.raises(ResolutionError, match="single string"):
            snapshot = build_snapshot(readable={EX: GENE})
        assert snapshot is None

    @pytest.mark.parametrize("terms", [None, 7])
    def test_a_vocabulary_that_is_not_a_collection_is_refused(self, terms):
        with pytest.raises(ResolutionError, match="collection of terms"):
            build_snapshot(readable={EX: terms})  # type: ignore[dict-item]

    def test_that_predicate_is_the_one_a_referent_applies(self, profile, readable):
        # The two have to agree, and this is the sharper direction: a `Referent`
        # cannot carry a non-identifier term, so a snapshot holding one holds a
        # member no claim can ever name. `resolve` would then answer
        # `not-member` — the single *refusing* outcome, positive evidence that a
        # vocabulary was read and lacks the term — about a vocabulary that was
        # told it has it. §7.2 keeps an absence of evidence from being reported
        # as evidence of absence; this is the same confusion from the other side,
        # and its victim is a well-formed claim.
        for admitted in [GENE, "1"]:
            assert Referent(sort="testing/entity", term=admitted).term == admitted
            build_snapshot(readable={EX: [admitted]})
        for refused in [1, ""]:
            with pytest.raises(MalformedReferent):
                Referent(sort="testing/entity", term=refused)
            with pytest.raises(ResolutionError):
                build_snapshot(readable={EX: [refused]})

    def test_the_integer_member_case_end_to_end(self, profile):
        # What the refusal above prevents, spelled out: the snapshot is told the
        # vocabulary holds 1, the claim names "1", and the receipt reports
        # `not-member` — a finding of absence about a term that was supplied.
        # Built through §6.3's raw route, which stands in for the one now closed.
        snapshot = ResolutionSnapshot._built(
            resolution._MINT,
            bindings={EX: resolution._BoundVocabulary(
                state="readable",
                terms=frozenset([1]),  # type: ignore[arg-type]
                absent=(),
            )},
            identity="unchecked",
        )
        assert snapshot.resolve(EX, "1") is TermOutcome.NOT_MEMBER
        with pytest.raises(ResolutionError):
            build_snapshot(readable={EX: [1]})  # type: ignore[list-item]
