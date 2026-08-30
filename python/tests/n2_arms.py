"""Cut 1's selected arms, each paired with the sabotage it must not survive.

**N2: every oracle row can fail.** A row that passes under sabotage is itself
defective, and the doctrine is executable law rather than advice — so cut 1's own
rows are not exempt from it. N2's trigger is *the first executable suite*, which
is what this is; a cut whose rows were exempt from the discipline they encode
would be the first thing the corpus should refuse.

Each `Arm` below names three things and nothing else:

* the **row** it belongs to and what that arm asserts, in the banked wording;
* a **sabotage** — a source mutation that makes the asserted property false;
* the **checks** — the exact tests that must fail when it is applied.

Naming the checks is the part that distinguishes this from *"the suite went
red"*. An arm whose sabotage breaks some unrelated test while leaving its own
check green is exactly the defect N2 describes, and a suite-level assertion
cannot see it. Three sessions of hand-run sabotage matrices produced seven
vacuous tests and, twice, a sabotage that had gone stale against code it no
longer matched — which is why staleness is a reported finding here and not a
silent skip.

**Arms are declared, never derived.** A harness that generated sabotages from the
code would assert that the code does what the code does. What an arm asserts
comes from the design; the checks are the reading of it that this suite commits
to.

Cut 2's own selected arms live in `n2_arms_cut2.py`, imported and audited
alongside `ARMS` by `test_n2.py` — this module and its table are cut 1's, held
exactly as cut 1 left them.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ARMS",
    "CLASS_NODE_BY_CONSTRUCTION",
    "CLASS_NODE_DISAGREEMENT",
    "MIXED_BY_CONSTRUCTION",
    "STALE_BY_CONSTRUCTION",
    "UNCOLLECTED_BY_CONSTRUCTION",
    "VACUOUS_BY_CONSTRUCTION",
    "Arm",
    "Sabotage",
]


@dataclass(frozen=True)
class Sabotage:
    """A single source mutation, stated as an exact replacement.

    `before` must occur **exactly once** in the module. A pattern that matches
    nothing has gone stale against the code, and one that matches twice sabotages
    somewhere the arm did not mean to; both are reported rather than tolerated,
    because a sabotage that silently fails to apply reads as a passing arm.
    """

    module: str
    """Path under `src/beliefs`, e.g. `resolution.py` or `contract/domain.py`."""

    before: str
    after: str


@dataclass(frozen=True)
class Arm:
    row: str
    """The guarantee row this arm belongs to — M4, D3, and so on."""

    asserts: str
    """What the arm claims, in the banked wording where there is one."""

    sabotage: Sabotage
    checks: tuple[str, ...]
    """Test node ids, relative to `tests/`, that must **fail** under the sabotage
    and must **pass** without it. Both directions are checked: a node id that no
    longer resolves would make `pytest` exit non-zero for a usage error, which an
    exit-code-only harness would read as a healthy arm.

    Each must name **one test function** — a module or a class node is one
    invocation over many tests, where the one that fails hides the ones that pass.
    The harness refuses those rather than scoring them."""

    @property
    def label(self) -> str:
        return f"{self.row}: {self.asserts}"


# --- M4 --------------------------------------------------------------------
# Every argument and restriction is a typed referent; only `not-member` refuses;
# an unperformed check stays explicit; the receipt carries exactly one outcome
# per referent position plus the `ResolutionSnapshot` identity.

_M4 = [
    Arm(
        row="M4",
        asserts="a term absent from a readable vocabulary refuses, and nothing is minted",
        sabotage=Sabotage(
            module="resolution.py",
            before="        return self is TermOutcome.NOT_MEMBER",
            after="        return False",
        ),
        checks=(
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_term_absent_from_a_readable_vocabulary_refuses_and_mints_nothing",
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_bad_restriction_refuses_like_a_bad_argument",
        ),
    ),
    Arm(
        row="M4",
        asserts="availability is not membership — an unreadable vocabulary accepts the same bad term",
        sabotage=Sabotage(
            module="resolution.py",
            before="            return TermOutcome.NOT_AVAILABLE",
            after="            return TermOutcome.NOT_MEMBER",
        ),
        checks=("test_decode.py::TestM4TypedReferentsAndTheReceipt::test_availability_is_not_membership",),
    ),
    Arm(
        row="M4",
        asserts="an unperformed check stays explicit and cannot impersonate a finding",
        sabotage=Sabotage(
            module="resolution.py",
            before="        return self in (TermOutcome.MEMBER, TermOutcome.NOT_MEMBER)",
            after="        return self is not TermOutcome.NOT_MEMBER",
        ),
        checks=(
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_availability_is_not_membership",
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_the_two_accepting_receipts_are_distinguishable",
        ),
    ),
    Arm(
        row="M4",
        asserts="the receipt carries exactly one outcome per referent position",
        sabotage=Sabotage(
            module="decode.py",
            before="    for dimension, qualifier in claim.qualifiers.items():\n        outcomes[ReferentPosition.restriction(dimension).label()] = _resolve(profile, snapshot, qualifier.restriction)",
            after="    for dimension, qualifier in list(claim.qualifiers.items())[1:]:\n        outcomes[ReferentPosition.restriction(dimension).label()] = _resolve(profile, snapshot, qualifier.restriction)",
        ),
        checks=(
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_the_receipt_carries_exactly_one_outcome_per_referent_position",
        ),
    ),
    Arm(
        row="M4",
        asserts="the receipt names the snapshot it resolved against",
        sabotage=Sabotage(
            module="resolution.py",
            before="        snapshot_identity=snapshot.identity,",
            after='        snapshot_identity="",',
        ),
        checks=(
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_the_receipt_records_the_snapshot_it_resolved_against",
            "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_the_two_accepting_receipts_are_distinguishable",
        ),
    ),
    # Two arms, because *"a bare string cannot occupy a slot"* and *"the sort
    # travels with the value"* are two properties held at two places, and one
    # sabotage cannot make both false. Held as a single arm, the decode-side
    # check passed under the constructor-side mutation and the arm still scored
    # sound — the failing check covered for the passing one.
    Arm(
        row="M4",
        asserts="a bare string cannot occupy an argument slot — the constructor refuses one",
        sabotage=Sabotage(
            module="claim.py",
            before="        raise UntypedReferent(",
            after="        raise SystemExit(  # not a ClaimError, so a caller catching the declared arm sees a crash",
        ),
        checks=("test_claim.py::TestTheCheckIsAgainstTheProfile::test_a_bare_string_cannot_occupy_a_slot",),
    ),
    Arm(
        row="M4",
        asserts="the sort travels with the value — nothing bare survives the boundary",
        sabotage=Sabotage(
            module="decode.py",
            before="    args = tuple(Referent(sort=sort, term=term) for term, sort in zip(terms, declaration.arg_sorts, strict=True))",
            after="    args = tuple(terms)  # the wire's bare strings, straight into the slots",
        ),
        checks=("test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_bare_string_cannot_occupy_a_slot_inside",),
    ),
]

# --- M5 (arms in cut 1) ----------------------------------------------------
# Restriction identifier alone forks `I_claim`; quantifier tag alone forks; a
# present-versus-absent dimension forks; sabotage: drop the qualifier map and the
# founding pair collapses to one identity; negative: re-serialize map keys in
# another order and nothing moves.

_M5 = [
    Arm(
        row="M5",
        asserts="dropping the qualifier map collapses the founding pair to one identity",
        sabotage=Sabotage(
            module="projection.py",
            before='        "qualifiers": {\n            dimension: {"quantifier": qualifier.quantifier, "restriction": qualifier.restriction.term}\n            for dimension, qualifier in claim.qualifiers.items()\n        },',
            after='        "qualifiers": {},',
        ),
        checks=(
            "test_projection.py::TestQualificationParticipatesInIdentity::test_the_founding_case_forks",
            "test_projection.py::TestQualificationParticipatesInIdentity::test_the_restriction_alone_forks_it",
            "test_projection.py::TestQualificationParticipatesInIdentity::test_the_quantifier_alone_forks_it",
        ),
    ),
    Arm(
        row="M5",
        asserts="the quantifier tag alone forks the identity — it is never inferred",
        sabotage=Sabotage(
            module="projection.py",
            before='            dimension: {"quantifier": qualifier.quantifier, "restriction": qualifier.restriction.term}',
            after='            dimension: {"restriction": qualifier.restriction.term}',
        ),
        checks=("test_projection.py::TestQualificationParticipatesInIdentity::test_the_quantifier_alone_forks_it",),
    ),
    Arm(
        row="M5",
        asserts="a present-versus-absent dimension forks the identity",
        sabotage=Sabotage(
            module="projection.py",
            before="            for dimension, qualifier in claim.qualifiers.items()\n        },",
            after='            for dimension, qualifier in claim.qualifiers.items()\n            if qualifier.quantifier != "generic"\n        },',
        ),
        checks=(
            "test_projection.py::TestQualificationParticipatesInIdentity::test_an_omitted_dimension_forks_it",
            "test_projection.py::TestQualificationParticipatesInIdentity::test_the_dimension_key_participates",
        ),
    ),
    Arm(
        row="M5",
        asserts="negative — map-key order is inert, so a re-serialization moves nothing",
        sabotage=Sabotage(
            module="identity/v1.py",
            before='        _encode_string(key, path) + ":" + _encode_value(normalized[key], f"{path}.{key}") for key in sorted(normalized)',
            after='        _encode_string(key, path) + ":" + _encode_value(normalized[key], f"{path}.{key}") for key in normalized',
        ),
        checks=(
            "test_projection.py::TestQualificationParticipatesInIdentity::test_qualifier_key_order_is_inert",
            "test_identity_v1.py::TestObjects::test_key_order_is_inert",
        ),
    ),
]

# --- M6 (arms in cut 1) ----------------------------------------------------

_M6 = [
    Arm(
        row="M6",
        asserts="a successor redefining a declared schema under an existing id is refused at load",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="        if prior[identifier] != current[identifier]:",
            after="        if False:",
        ),
        checks=(
            "test_domain_contract.py::TestSuccession::test_redefining_a_declared_schema_is_refused",
            "test_domain_contract.py::TestSuccession::test_succession_covers_dimensions",
            "test_domain_contract.py::TestSuccession::test_succession_covers_sorts",
        ),
    ),
    Arm(
        row="M6",
        asserts="a successor that drops a declaration — retired or not — is refused",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="    dropped = sorted(set(prior) - set(current))",
            after="    dropped = []",
        ),
        checks=(
            "test_domain_contract.py::TestSuccession::test_dropping_a_declaration_is_refused",
            "test_domain_contract.py::TestRetirementIsOneWay::test_dropping_a_tombstone_is_refused",
        ),
    ),
    Arm(
        row="M6",
        asserts="the predecessor link is named and matched, not assumed",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="    if predecessor.content_identity != contract.predecessor:",
            after="    if False:",
        ),
        checks=("test_domain_contract.py::TestSuccession::test_a_mismatched_predecessor_identity_is_refused",),
    ),
    Arm(
        row="M6",
        asserts="retirement is one way — un-retiring is refused on both paths",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="    resurrected = sorted((predecessor.retired_identifiers() - contract.retired_identifiers()) & set(current))",
            after="    resurrected = []",
        ),
        checks=(
            "test_domain_contract.py::TestRetirementIsOneWay::test_un_retiring_is_refused",
            "test_domain_contract.py::TestRetirementIsOneWay::test_dropping_the_retired_field_entirely_is_also_un_retiring",
            "test_domain_contract.py::TestRetirementIsOneWay::test_it_covers_dimensions_and_sorts_too",
        ),
    ),
    Arm(
        row="M6",
        asserts="negative — an editorial change is accepted, and moves the contract identity",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="        content_identity=v1.digest(DOMAIN_CONTRACT_DOMAIN, root),",
            after='        content_identity=v1.digest(DOMAIN_CONTRACT_DOMAIN, {"contract": root["contract"]}),',
        ),
        checks=(
            "test_domain_contract.py::TestSuccession::test_an_editorial_change_is_accepted_and_moves_contract_identity",
        ),
    ),
]

# --- M7 --------------------------------------------------------------------

_M7 = [
    Arm(
        row="M7",
        asserts="no second authored operator artifact — every operator traces to a supplied contract",
        sabotage=Sabotage(
            module="profile.py",
            before="    operators: dict[str, CompiledOperator] = {}",
            after='    operators: dict[str, CompiledOperator] = {\n        "science/asserts": CompiledOperator(\n            term="science/asserts", arity=2, arg_sorts=("science/thing", "science/thing"),\n            sign_apt=True, layers=("causal",), dimensions=(), retired=False, namespace="science",\n        )\n    }',
        ),
        checks=(
            "test_profile.py::TestNoSecondAuthoredOperatorArtifact::test_every_operator_traces_to_a_supplied_contract",
            "test_profile.py::TestNoSecondAuthoredOperatorArtifact::test_a_profile_with_no_domains_has_no_operators",
            "test_profile.py::TestNoSecondAuthoredOperatorArtifact::test_the_base_contract_contributes_no_operator",
        ),
    ),
    Arm(
        row="M7",
        asserts="a semantic schema edit recompiles the profile; a description edit does not",
        sabotage=Sabotage(
            module="profile.py",
            before="        compiled_identity=v1.digest(PROFILE_DOMAIN, _projection(base.claim_grammar, operators, dimensions, sorts)),",
            after='        compiled_identity=v1.digest(\n            PROFILE_DOMAIN,\n            {\n                **_projection(base.claim_grammar, operators, dimensions, sorts),\n                "activated": {ns: c.content_identity for ns, c in seen.items()},\n            },\n        ),',
        ),
        # `test_the_compiler_contributes_no_input` is deliberately **not** named
        # here: its own docstring records that it cannot fail, since the encoder
        # sorts object keys and no iteration order in the compiler can reach the
        # identity. Naming an unfailable check is how an arm becomes decorative.
        checks=(
            "test_profile.py::TestSemanticEditsRecompileAndEditorialOnesDoNot::test_an_editorial_edit_moves_contract_identity_and_not_the_compiled_profile",
        ),
    ),
]

# --- M8 (arms in cut 1) ----------------------------------------------------

_M8 = [
    Arm(
        row="M8",
        asserts="folding a contract release into π_claim would fork every claim on an ontology release",
        # The fold has to widen the signature to reach a contract at all, which
        # is why the signature is the arm with force and this sabotage performs
        # both halves. `test_no_contract_identity_reaches_the_bytes` is
        # deliberately **not** named: it looks for the profile's own digests,
        # computed at run time, and no source mutation confined to this module
        # can put one of those in the bytes. It guards the same prohibition from
        # the value side and no arm here can make it fail.
        sabotage=Sabotage(
            module="projection.py",
            before="def project_claim(claim: Claim) -> dict[str, object]:",
            after=(
                "def project_claim(claim: Claim, profile: object = None) -> dict[str, object]:\n"
                '    """An ontology release, folded into the projection."""\n'
                '    return {**_project(claim), "contract": "science.testing.v2"}\n\n\n'
                "def _project(claim: Claim) -> dict[str, object]:"
            ),
        ),
        checks=(
            "test_projection.py::TestTheProjectionIsAFunctionOfTheClaimAlone::test_the_projection_takes_a_claim_and_nothing_else",
            "test_parity_fixture.py::TestEveryRowRoundTrips::test_the_row_reproduces",
        ),
    ),
    Arm(
        row="M8",
        asserts="`ProfileSpec`'s identity is absent from π_claim, and merge order is inert",
        sabotage=Sabotage(
            module="profile.py",
            before='        "operators": {term: decl.schema_projection() for term, decl in operators.items()},',
            after='        "operators": [[term, decl.schema_projection()] for term, decl in operators.items()],',
        ),
        # Pointed at the third test in that class, not the first. The first two
        # are recorded in their own docstring as unable to fail — the encoder's
        # key sort already makes iteration order unreachable — so the arm with
        # force is the **shape** one: holding declarations positionally is what
        # would make merge order an identity input.
        checks=("test_profile.py::TestMergeOrderIsInert::test_declarations_are_keyed_by_term_never_held_positionally",),
    ),
]

# --- M9 --------------------------------------------------------------------

_M9 = [
    Arm(
        row="M9",
        asserts="the polarity position is present at a sign-inapt operator — the shape never reads a contract field",
        sabotage=Sabotage(
            module="projection.py",
            before='        "polarity": claim.polarity,',
            after='        **({} if claim.polarity == "inapt" else {"polarity": claim.polarity}),',
        ),
        checks=(
            "test_projection.py::TestTheShapeDependsOnTheClaimNeverOnAContractField::test_the_polarity_position_is_present_at_a_sign_inapt_operator",
            "test_projection.py::TestTheShapeDependsOnTheClaimNeverOnAContractField::test_the_position_set_is_the_same_at_both_kinds_of_operator",
        ),
    ),
    Arm(
        row="M9",
        asserts="`inapt` and `unsigned` are distinct bytes, asserted against the base contract",
        sabotage=Sabotage(
            module="contract/base.py",
            before="    if sign_inapt_tag in polarities:",
            after="    if False:",
        ),
        checks=(
            "test_base_contract.py::TestTagsThatMustNotCollapse::test_an_inapt_tag_that_is_also_a_polarity_is_refused",
            "test_projection.py::TestTheBaseContractPinsTheTags::test_a_grammar_that_collides_inapt_with_a_polarity_is_refused",
        ),
    ),
]

# --- M10 -------------------------------------------------------------------
# Two implementations hash a claim identically over every closed tag, with vector
# coverage asserted complete. The design names three sabotages by hand: map-key
# sort, slot order, and a single tag's bytes.

_M10 = [
    Arm(
        row="M10",
        asserts="changing one implementation's map-key sort fails the fixture",
        sabotage=Sabotage(
            module="identity/v1.py",
            before="for key in sorted(normalized)",
            after="for key in sorted(normalized, reverse=True)",
        ),
        checks=("test_parity_fixture.py::TestEveryRowRoundTrips::test_the_row_reproduces",),
    ),
    Arm(
        row="M10",
        asserts="changing slot order fails the fixture — arguments are held by slot",
        sabotage=Sabotage(
            module="projection.py",
            before='        "args": [referent.term for referent in claim.args],',
            after='        "args": sorted(referent.term for referent in claim.args),',
        ),
        checks=(
            "test_parity_fixture.py::TestEveryRowRoundTrips::test_the_row_reproduces",
            "test_projection.py::TestArgumentsAreHeldBySlot::test_swapping_two_arguments_forks_the_identity",
        ),
    ),
    Arm(
        row="M10",
        asserts="changing a single tag's bytes fails the fixture",
        # A closed-vocabulary tag, written differently on one side. The arm below
        # is what makes this one land: the fixture can only see a tag it carries,
        # and coverage of the closed sets is asserted rather than hoped for.
        sabotage=Sabotage(
            module="projection.py",
            before='        "polarity": claim.polarity,',
            after='        "polarity": ("negated" if claim.polarity == "negative" else claim.polarity),',
        ),
        checks=("test_parity_fixture.py::TestEveryRowRoundTrips::test_the_row_reproduces",),
    ),
    Arm(
        row="M10",
        asserts="the escape rules are held by each implementation's own unit tests, which the fixture does not compare",
        # Stated as what it is. This sabotage changes how a backslash is written
        # and the **fixture does not see it**: no row's values carry a backslash
        # or a quote, so the vector compares the two implementations over tags,
        # slots and keys, and over escaping compares nothing. Each side tests its
        # own escaping and neither is checked against the other — which is the
        # values-level parity fixture recorded as owed and outside cut 1. Named
        # here rather than dropped, so the gap has a row that states it.
        sabotage=Sabotage(
            module="identity/v1.py",
            before='            out.append("\\\\\\\\")',
            after='            out.append("\\\\u005c")',
        ),
        checks=("test_identity_v1.py::TestStrings::test_quote_and_backslash_are_escaped",),
    ),
    Arm(
        row="M10",
        asserts="the vector's coverage of the closed tag sets is asserted complete, not assumed",
        sabotage=Sabotage(
            module="contract/base.py",
            before='    polarities = _closed_set(grammar["polarities"], f"{grammar_where}: polarities")',
            after='    polarities = (*_closed_set(grammar["polarities"], f"{grammar_where}: polarities"), "conjectural")',
        ),
        checks=(
            "test_parity_fixture.py::TestTagCoverageIsCompleteAgainstTheBaseContract::test_every_polarity_tag_appears",
        ),
    ),
]

# --- M11 -------------------------------------------------------------------

_M11 = [
    Arm(
        row="M11",
        asserts="availability is a parameter — a decoder that supplied its own would decide by ambient state",
        sabotage=Sabotage(
            module="decode.py",
            before="    wire: WireClaim, *, profile: ProfileSpec, snapshot: ResolutionSnapshot",
            after="    wire: WireClaim, *, profile: ProfileSpec, snapshot: ResolutionSnapshot | None = None",
        ),
        checks=(
            "test_decode.py::TestM11DecodeIsAFunctionOfItsArguments::test_availability_is_a_parameter_and_has_no_default",
        ),
    ),
    Arm(
        row="M11",
        asserts="decode refuses rather than repairs — arity is not clamped to fit",
        sabotage=Sabotage(
            module="decode.py",
            before="    if len(terms) != declaration.arity:",
            after="    if terms and len(terms) < declaration.arity:\n        terms = terms + terms[-1:] * (declaration.arity - len(terms))\n    terms = terms[: declaration.arity]\n    if len(terms) != declaration.arity:",
        ),
        checks=(
            "test_decode.py::TestM11DecodeIsAFunctionOfItsArguments::test_each_ill_formed_input_is_refused_and_mints_nothing",
        ),
    ),
    Arm(
        row="M11",
        asserts="the wire value's own shape is settled before any contract is consulted",
        sabotage=Sabotage(
            module="decode.py",
            before="    operator, terms, qualifier_bodies, polarity, layer = _wire_parts(wire)\n    declaration = profile.operator(operator)",
            after="    declaration = profile.operator(wire.operator)\n    operator, terms, qualifier_bodies, polarity, layer = _wire_parts(wire)",
        ),
        checks=(
            "test_decode.py::TestM11DecodeIsAFunctionOfItsArguments::test_a_malformed_wire_value_refuses_before_any_contract_is_consulted",
        ),
    ),
    Arm(
        row="M11",
        asserts="the snapshot is authenticated, so an ambient stand-in cannot be passed instead",
        sabotage=Sabotage(
            module="decode.py",
            before="    if not isinstance(snapshot, ResolutionSnapshot):",
            after="    if False:",
        ),
        checks=("test_decode.py::TestM11DecodeIsAFunctionOfItsArguments::test_the_snapshot_is_authenticated",),
    ),
    Arm(
        row="M11",
        asserts="the same three inputs decode identically in another process",
        sabotage=Sabotage(
            module="projection.py",
            before="    return v1.digest(CLAIM_DOMAIN, project_claim(claim))",
            after='    import os\n\n    return v1.digest(CLAIM_DOMAIN, {**project_claim(claim), "pid": str(os.getpid())})',
        ),
        checks=(
            "test_decode.py::TestM11DecodeIsAFunctionOfItsArguments::test_the_same_three_inputs_decode_identically_in_another_process",
        ),
    ),
]

# --- M13 -------------------------------------------------------------------

_M13 = [
    Arm(
        row="M13",
        asserts="`Claim` is opaque — exporting a raw constructor must fail",
        sabotage=Sabotage(
            module="claim.py",
            before='        raise ClaimError(\n            "Claim is validated at construction',
            after='        for _name, _value in kwargs.items():\n            object.__setattr__(self, _name, _value)\n        return\n        raise ClaimError(  # noqa: B012\n            "Claim is validated at construction',
        ),
        checks=(
            "test_claim.py::TestTheOnlyRouteIsTheValidatedConstructor::test_the_field_wise_constructor_is_refused",
            "test_claim.py::TestTheOnlyRouteIsTheValidatedConstructor::test_the_no_argument_constructor_is_refused_too",
        ),
    ),
    Arm(
        row="M13",
        asserts="no signature downstream of the boundary accepts a `WireClaim`",
        sabotage=Sabotage(
            module="projection.py",
            before="def project_claim(claim: Claim) -> dict[str, object]:",
            after="def project_claim(claim: Claim | WireClaim) -> dict[str, object]:  # type: ignore[name-defined]  # noqa: F821",
        ),
        checks=(
            "test_decode.py::TestM13TheWireTypeIsConfinedToTheDecodeModule::test_no_signature_outside_decode_mentions_the_wire_type",
        ),
    ),
    Arm(
        row="M13",
        asserts="the chain reaches the document — compilation refuses a contract no parser produced",
        sabotage=Sabotage(
            module="profile.py",
            before="    if not isinstance(base, BaseContract):",
            after='    if not hasattr(base, "claim_grammar"):',
        ),
        checks=(
            "test_profile.py::TestTheTrustChainStartsAtTheDocument::test_compilation_refuses_a_base_contract_no_parser_produced",
        ),
    ),
    Arm(
        row="M13",
        asserts="two genuine contracts that were never typed against each other are refused where they meet",
        sabotage=Sabotage(
            module="profile.py",
            before="        if contract.base_identity != base.content_identity:",
            after="        if False:",
        ),
        checks=(
            "test_profile.py::TestTwoGenuineContractsThatDoNotBelongTogether::test_a_domain_parsed_under_another_base_is_refused",
        ),
    ),
    Arm(
        row="M13",
        asserts="a compiled profile and its source contracts are immutable to the leaves",
        sabotage=Sabotage(
            module="profile.py",
            before="        operators=MappingProxyType(dict(operators)),",
            after="        operators=operators,",
        ),
        checks=("test_profile.py::TestTheProfileIsCompiledNeverAuthored::test_the_mappings_are_read_only",),
    ),
    Arm(
        row="M13",
        asserts="the closed types stay closed — a subclass could mint an unchecked value that still passes `isinstance`",
        sabotage=Sabotage(
            module="sealed.py",
            before="    cls.__init_subclass__ = classmethod(__init_subclass__)  # type: ignore[assignment]",
            after="    pass",
        ),
        checks=(
            "test_claim.py::TestTheValueTypesOwnTheirInvariants::test_the_claim_types_cannot_be_subclassed",
            "test_profile.py::TestTheProfileIsCompiledNeverAuthored::test_the_profile_cannot_be_subclassed",
            "test_domain_contract.py::TestTheBindingIsASumAndNotAProduct::test_the_binding_is_sealed",
        ),
    ),
]

# --- D3 (arms in cut 1) ----------------------------------------------------

_D3 = [
    Arm(
        row="D3",
        asserts="a `vocabulary` with no release is refused at contract load",
        sabotage=Sabotage(
            module="contract/domain.py",
            before="    if not isinstance(namespace, str) or not namespace or not isinstance(release, str) or not release:",
            after="    if not isinstance(namespace, str) or not namespace:",
        ),
        checks=("test_domain_contract.py::TestVocabularyBindings::test_a_bare_namespace_is_refused",),
    ),
    Arm(
        row="D3",
        asserts="an unconsulted namespace yields `not-consulted`, never a membership finding",
        sabotage=Sabotage(
            module="resolution.py",
            before="            return TermOutcome.NOT_CONSULTED",
            after="            return TermOutcome.NOT_MEMBER",
        ),
        checks=(
            "test_decode.py::TestD3TheFiveOutcomesStayDistinct::test_an_unconsulted_namespace_yields_not_consulted",
            "test_decode.py::TestD3TheFiveOutcomesStayDistinct::test_an_empty_readable_vocabulary_is_not_an_unconsulted_one",
        ),
    ),
    Arm(
        row="D3",
        asserts="the five outcomes do not collapse into one another",
        sabotage=Sabotage(
            module="resolution.py",
            before='    NOT_PRESENT = "not-present"',
            after='    NOT_PRESENT = "not-consulted"',
        ),
        checks=("test_decode.py::TestD3TheFiveOutcomesStayDistinct::test_no_outcome_collapses_into_another",),
    ),
    Arm(
        row="D3",
        asserts="the binding stays well formed — there is no fallback to another release",
        sabotage=Sabotage(
            module="resolution.py",
            before="        state = self.bindings.get(binding)",
            after="        state = self.bindings.get(binding) or next(\n            (s for b, s in self.bindings.items() if b.namespace == binding.namespace), None\n        )",
        ),
        checks=("test_decode.py::TestD3TheFiveOutcomesStayDistinct::test_there_is_no_fallback_to_another_release",),
    ),
]

ARMS: tuple[Arm, ...] = tuple(_M4 + _M5 + _M6 + _M7 + _M8 + _M9 + _M10 + _M11 + _M13 + _D3)


CLASS_NODE_BY_CONSTRUCTION = Arm(
    row="N2",
    asserts="a check names one test function — a class node is a whole invocation wearing a node id",
    # M4's first sabotage, checked by the **class** that holds the test which
    # catches it. `pytest` runs every method under that class and reports one
    # exit code, so the one that fails hides the ones that pass and the arm reads
    # as sound. It is the aggregation defect a check-at-a-time verdict was meant
    # to close, one level further down, and having a `::` in it is not enough to
    # tell the two apart.
    sabotage=_M4[0].sabotage,
    checks=("test_decode.py::TestM4TypedReferentsAndTheReceipt",),
)
"""The two methods below are what make that concrete: under the same sabotage the
first fails and the second passes, and a class-level exit code cannot say so."""

CLASS_NODE_DISAGREEMENT = (
    "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_term_absent_from_a_readable_vocabulary_refuses_and_mints_nothing",
    "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_member_term_is_accepted_with_the_check_performed",
)


VACUOUS_BY_CONSTRUCTION = Arm(
    row="N2",
    asserts=(
        "an arm whose check does not cover its own sabotage is reported as malformed contract content, "
        "not as a passing arm"
    ),
    # A real defect: the receipt stops naming the claim it was taken for.
    sabotage=Sabotage(
        module="resolution.py",
        before="        claim_identity=claim_identity,",
        after='        claim_identity="",',
    ),
    # ...checked by a test that never looks at `claim_identity`. This is the
    # shape of every vacuous test found by hand in this build: the check is real
    # and the sabotage is real, and they are about different things.
    checks=(
        "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_member_term_is_accepted_with_the_check_performed",
    ),
)


MIXED_BY_CONSTRUCTION = Arm(
    row="N2",
    asserts="a check that fails cannot cover for one that passes — every named check must fail on its own",
    # The same real defect as above, named by **two** checks: the first sees it,
    # the second does not. Run together in one `pytest` invocation the pair exits
    # non-zero and the arm scores sound, while half of what it claims to assert
    # asserts nothing. This is the shape of the three real arms that were carrying
    # a passing check when the harness began scoring them one at a time.
    sabotage=VACUOUS_BY_CONSTRUCTION.sabotage,
    checks=(
        "test_decode.py::TestDecodeInvertsTheProjection::test_every_frozen_row_decodes_back_to_its_own_identity",
        "test_decode.py::TestM4TypedReferentsAndTheReceipt::test_a_member_term_is_accepted_with_the_check_performed",
    ),
)


UNCOLLECTED_BY_CONSTRUCTION = Arm(
    row="N2",
    asserts="a sabotage that stops the check from running has not shown the check can fail",
    # A mutation coarse enough to break the module's syntax. Every check named
    # under it exits 4 — `pytest` cannot collect the node id — which is non-zero
    # and reads as a failing check to anything watching the exit code alone. What
    # such an arm demonstrates is that unimportable code does not import, which is
    # true of every check in the suite and specific to none of them.
    sabotage=Sabotage(
        module="projection.py",
        before='    return {\n        "operator": claim.operator,',
        after='    return {{{\n        "operator": claim.operator,',
    ),
    checks=("test_projection.py::TestArgumentsAreHeldBySlot::test_swapping_two_arguments_forks_the_identity",),
)


STALE_BY_CONSTRUCTION = Arm(
    row="N2",
    asserts="an arm whose sabotage no longer matches the code is reported, not silently skipped",
    # This mutation matched real code once. A stale sabotage applies nothing, so
    # the arm's checks pass and it scores healthy — the same false report as a
    # vacuous arm, reached by a different route, and the one that will actually
    # happen as the code moves under a table nobody re-reads.
    sabotage=Sabotage(
        module="resolution.py",
        before="    if not isinstance(term, str) or not term:",
        after="    if False:",
    ),
    checks=(
        "test_decode.py::TestTheSnapshotAuthenticatesWhatItIsBuiltFrom::test_a_member_that_is_not_a_term_identifier_is_refused",
    ),
)
