"""Cut 2's selected arms, paired with the sabotage each must not survive.

Same doctrine as `n2_arms.py` (N2: every oracle row can fail), extended over
cut 2's selected rows. The deferred rows' doctrine stays exactly as cut 1 left
it — nothing here touches `ARMS`, and nothing here claims a row cut 2 defers.

Every `before` string below was reconciled against the merged tree at
declaration time, not against the planning brief's sketch of the code (the
brief itself warns the two drift). Where the brief's table names a sabotage
that turned out to be inert against the real code and its real tests — every
candidate anchor and every candidate check tried — the row is still covered
here through an adjacent sabotage with the same semantic effect, and the swap
is recorded in the arm's `asserts` text or the task's report, never silently.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT2_ARMS"]


# --- G9 ----------------------------------------------------------------
# Held is derived, never stored, and quantified over the whole declaration; an
# observation matches by digest alone, never by location (kernel §2.2).

_G9 = [
    Arm(
        row="G9",
        asserts="a proper subset of the declared digests does not promote to Held",
        sabotage=Sabotage(
            module="dataset.py",
            before="    if set(pinned) <= observed:",
            after="    if set(pinned) & observed:",
        ),
        checks=(
            "test_dataset_state.py::TestAProperSubsetDoesNotPromote::test_two_of_three_is_still_declared",
            "test_dataset_state.py::TestAProperSubsetDoesNotPromote::test_removing_one_returns_it_to_declared",
        ),
    ),
    Arm(
        row="G9",
        asserts="presence alone does not promote a finding to matched — a mismatch stays a mismatch",
        sabotage=Sabotage(
            module="dataset.py",
            before='            outcome="matched" if digest in observed else "no-matching-observation-in-coverage",',
            after='            outcome="matched" if True else "no-matching-observation-in-coverage",',
        ),
        checks=("test_dataset_state.py::TestPresenceDoesNotPromote::test_the_mismatch_is_reported_as_a_mismatch",),
    ),
    Arm(
        row="G9",
        asserts="location is reporting material and never the discriminator for Held",
        sabotage=Sabotage(
            module="dataset.py",
            before="    if set(pinned) <= observed:",
            after=("    if set(pinned) <= observed and all(o.location.startswith('repo://') for o in observations):"),
        ),
        checks=(
            "test_dataset_state.py::TestLocationIsNotTheDiscriminator::test_matching_bytes_outside_the_repository_read_held",
            "test_dataset_state.py::TestLocationIsNotTheDiscriminator::test_unreachable_here_with_a_controlled_copy_leaves_both_halves_unchanged",
        ),
    ),
]

# --- G2b -----------------------------------------------------------------
# Every input must be held under the observations supplied to the call — not
# only the observes ones.

_G2b = [
    Arm(
        row="G2b",
        asserts="an input that is not Held refuses admission, whatever its role",
        sabotage=Sabotage(
            module="admission.py",
            before="        if not isinstance(state, Held):",
            after="        if False:",
        ),
        checks=(
            "test_admission.py::TestG2b::test_a_declared_input_is_refused",
            "test_admission.py::TestG2b::test_a_curation_note_input_is_refused",
            "test_admission.py::TestG2b::test_every_input_must_be_held_not_only_observes",
        ),
    ),
]

# --- G6 --------------------------------------------------------------------
# `reads` inputs never confer eligibility, in any quantity.

_G6 = [
    Arm(
        row="G6",
        asserts="an assessment with no observes input is refused, regardless of verification state",
        sabotage=Sabotage(
            module="admission.py",
            before='    if not any(i.role == "observes" for i in run.inputs):',
            after="    if False:",
        ),
        checks=(
            "test_admission.py::TestG6::test_reads_only_inputs_admit_nothing",
            "test_admission.py::TestG6::test_qa_state_does_not_rescue_it",
        ),
    ),
]

# --- G2c -------------------------------------------------------------------
# Kernel §3.3's table is fail-closed and total by construction.

_G2c = [
    Arm(
        row="G2c",
        asserts="an active failing verification invalidates, and no sibling or later pass clears it",
        sabotage=Sabotage(
            module="verification.py",
            before='    if any(v.verdict == "failed" for v in live):',
            after="    if False:",
        ),
        checks=(
            "test_verification_lifecycle.py::TestFailClosed::test_a_passing_sibling_does_not_clear_an_active_failure",
            "test_verification_lifecycle.py::TestFailClosed::test_recency_does_not_clear_either",
        ),
    ),
    Arm(
        row="G2c",
        asserts="the table's final row is a complement, so every other cell is not-admitted",
        sabotage=Sabotage(
            module="verification.py",
            before=(
                '    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):\n'
                "        return ADMITTED\n"
                "    return NOT_ADMITTED"
            ),
            after=(
                '    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):\n'
                "        return ADMITTED\n"
                "    return ADMITTED"
            ),
        ),
        checks=("test_verification_lifecycle.py::TestTheTableIsTotal::test_every_single_verification_lands_in_a_row",),
    ),
]

# --- G1 --------------------------------------------------------------------
# A source-assertion can assert, deny or hypothesize — never assess — and
# moves no belief output byte, value or digest. Four arms: the constructor
# refusal, the value half, the digest half's closed signature (the parameter
# does not exist to be threaded), and the digest half live (folding a source
# assertion into what closure.py digests, at the one call site that could).

_G1 = [
    Arm(
        row="G1",
        asserts="the constructor refuses an assesses edge from a source-assertion — the only authoring surface",
        sabotage=Sabotage(
            module="record.py",
            before="        if self.relation not in SOURCE_ASSERTION_RELATIONS:",
            after="        if False:",
        ),
        checks=("test_records.py::TestClosedSignatures::test_an_assesses_edge_from_a_source_assertion_is_refused",),
    ),
    Arm(
        row="G1",
        asserts="the value half: widening the vertex build to read source-assertion signs moves belief's value",
        sabotage=Sabotage(
            module="belief.py",
            before=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs)"
            ),
            after=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs) + tuple(\n"
                "        DirectionalInput(assessment=sa.ref, sign=1 if sa.relation == "
                '"asserts" else -1)\n'
                "        for sa in records.source_assertions\n"
                '        if sa.relation != "hypothesizes"\n'
                "    )"
            ),
        ),
        checks=(
            "test_belief.py::TestG1ASourceAssertionMovesNothing::test_every_field_maximal_moves_no_belief_output_byte",
        ),
    ),
    Arm(
        row="G1",
        asserts="the digest half: source assertions have no parameter here at all — closure's signature stays closed",
        sabotage=Sabotage(
            module="closure.py",
            before="    binding: tuple[str, str],\n) -> Closure:",
            after="    binding: tuple[str, str],\n    source_assertions: tuple[object, ...] = (),\n) -> Closure:",
        ),
        checks=("test_closure.py::test_the_same_binding_resolves_identically_elsewhere",),
    ),
    Arm(
        row="G1",
        asserts=(
            "the digest half, live: source assertions are failable only because closure membership is "
            "computed — folding them into the consulted member at the build_closure call site moves the digest"
        ),
        sabotage=Sabotage(
            module="belief.py",
            before="        consulted=consulted,\n        binding=(binding.rule, binding.implementation),",
            after=(
                "        consulted=consulted + tuple((sa.ref, sa.relation) for sa in "
                "records.source_assertions),\n"
                "        binding=(binding.rule, binding.implementation),"
            ),
        ),
        checks=(
            "test_belief.py::TestG1ASourceAssertionMovesNothing::test_every_field_maximal_moves_no_belief_output_byte",
        ),
    ),
]

# --- G3 --------------------------------------------------------------------
# "A member is in the closure because something reads it" — the projection is
# exactly what `evaluate` reads, keyed pairs and all.

_G3 = [
    Arm(
        row="G3",
        asserts="dropping producer_snapshot from the projection is a member-mutation and a narrower-coverage arm at once",
        sabotage=Sabotage(
            module="closure.py",
            before='        "producer_snapshot": producer_snapshot_identity,\n',
            after="",
        ),
        checks=(
            "test_closure.py::test_each_member_moves_the_digest[producer_snapshot]",
            "test_closure.py::test_a_narrower_coverage_snapshot_moves_it",
        ),
    ),
    Arm(
        row="G3",
        asserts="the assessment-facet pairing is the member, not the bag of either half on its own",
        sabotage=Sabotage(
            module="closure.py",
            before="    assessment_facets = sorted((a.identity(), a.facet_digest()) for a in ours)",
            after="    assessment_facets = sorted(a.facet_digest() for a in ours)",
        ),
        checks=("test_closure.py::test_the_keyed_facet_permutation_moves_it",),
    ),
    Arm(
        row="G3",
        asserts="stored ref and resolution are recorded separately, or a producing-run deletion is invisible to the digest",
        sabotage=Sabotage(
            module="lineage.py",
            before='    return {"stored": stored, "resolved": [] if resolved is None else [resolved]}',
            after='    return {"stored": stored}',
        ),
        checks=("test_closure.py::test_a_producing_run_deletion_moves_it",),
    ),
    Arm(
        row="G3",
        asserts="the producer set is a projected member — a second producer must move the digest",
        sabotage=Sabotage(
            module="lineage.py",
            before='        "producers": producers,\n',
            after="",
        ),
        checks=("test_closure.py::test_a_second_producer_moves_it",),
    ),
]

# --- G8 --------------------------------------------------------------------
# `lifecycle_state` is a pure function of its argument — no cross-call memory.

_G8 = [
    Arm(
        row="G8",
        asserts="statefulness — a module-level memo of past failures — breaks the deletion negative",
        sabotage=Sabotage(
            module="verification.py",
            before=(
                "def lifecycle_state(verifications: tuple[Verification, ...]) -> str:\n"
                '    """Kernel §3.3\'s table, over the verifications for one assessment.\n'
                "\n"
                "    A pure function of its argument: a cross-call memory here would make a\n"
                "    deleted failure keep invalidating, contradicting the deletion negative G8\n"
                '    pins (§3.2\'s undetectable-history limit)."""\n'
                "    if not verifications:\n"
                "        return NOT_ADMITTED\n"
                "    live = active(verifications)\n"
                '    if any(v.verdict == "failed" for v in live):\n'
                "        return INVALIDATED\n"
                '    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):\n'
                "        return ADMITTED\n"
                "    return NOT_ADMITTED"
            ),
            after=(
                "_seen_failures: set[str] = set()\n"
                "\n"
                "\n"
                "def lifecycle_state(verifications: tuple[Verification, ...]) -> str:\n"
                '    """Kernel §3.3\'s table, over the verifications for one assessment.\n'
                "\n"
                "    A pure function of its argument: a cross-call memory here would make a\n"
                "    deleted failure keep invalidating, contradicting the deletion negative G8\n"
                '    pins (§3.2\'s undetectable-history limit)."""\n'
                "    if not verifications:\n"
                "        return NOT_ADMITTED\n"
                "    for v in verifications:\n"
                '        if v.verdict == "failed":\n'
                "            _seen_failures.add(v.assessment)\n"
                "    live = active(verifications)\n"
                "    if any(v.assessment in _seen_failures for v in live):\n"
                "        return INVALIDATED\n"
                '    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):\n'
                "        return ADMITTED\n"
                "    return NOT_ADMITTED"
            ),
        ),
        checks=("test_verification_lifecycle.py::TestFailClosed::test_the_state_is_a_function_of_its_argument",),
    ),
]

# --- S5 --------------------------------------------------------------------
# An unresolved basis entry — either resolution None — is lineage-incomplete;
# a supplied snapshot never certifies over one.

_S5 = [
    Arm(
        row="S5",
        asserts="treating an unresolved route as resolved lets an incomplete closure certify",
        sabotage=Sabotage(
            module="lineage.py",
            before="            if r.resolved_run is None or r.resolved_ancestor is None:",
            after="            if False:",
        ),
        checks=(
            "test_lineage.py::TestIncompleteNeverCertifies::test_an_unresolved_basis_entry_yields_lineage_incomplete",
            "test_lineage.py::TestIncompleteNeverCertifies::test_the_roots_own_parent_counts",
        ),
    ),
]

# --- S6 --------------------------------------------------------------------
# Only certified independence confers multiplicity; contestation reduces
# toward the prior and is clamped there; the algorithm is exact, not greedy.
#
# S6(f)'s literal sabotage — replacing the `chosen = min(candidates, key=...)`
# tie-break with a corroboration-only key — was tried against every existing
# S6 test and the fixture-conformance check (see the task report): every
# candidate of the same maximum cardinality that this suite's fixtures ever
# produce already agrees in `abs(final(...))`, by the same symmetry the tests
# are asserting, so no tie-break substitution at that line moves any check.
# S6's row is covered here through its other three sabotages instead.

_S6 = [
    Arm(
        row="S6",
        asserts="a multiplicity of two is a maximum independent set, not a partition into connected components",
        sabotage=Sabotage(
            module="policy.py",
            before=(
                "def _maximum_selections(ids: tuple[str, ...], edges: frozenset[frozenset[str]]) -> "
                "list[tuple[str, ...]]:\n"
                '    """Every maximum-cardinality independent set. Exact, always — no bound, no\n'
                "    greedy fallback: a lower bound on cardinality is not a lower bound on\n"
                '    belief (kernel §4.2.1)."""\n'
                "    for size in range(len(ids), 0, -1):\n"
                "        found = [c for c in itertools.combinations(ids, size) if _independent(c, edges)]\n"
                "        if found:\n"
                "            return found\n"
                "    return [()]"
            ),
            after=(
                "def _maximum_selections(ids: tuple[str, ...], edges: frozenset[frozenset[str]]) -> "
                "list[tuple[str, ...]]:\n"
                '    """Sabotaged: every edge-linked vertex unions into one selectable unit."""\n'
                "    return [tuple(sorted(ids))]"
            ),
        ),
        checks=(
            "test_aggregation.py::TestS6TheDependencyGraph::test_a_multiplicity_is_two_not_a_partition_and_not_components",
        ),
    ),
    Arm(
        row="S6",
        asserts="a maximum selection's non-independent contrary vertices still contest it",
        sabotage=Sabotage(
            module="policy.py",
            before=(
                "        direction = 1 if value > 0 else -1\n"
                "        contrary = tuple(a for a in ids if a not in candidate and signs[a] == -direction)"
            ),
            after=(
                "        direction = 1 if value > 0 else -1\n"
                "        return value\n"
                "        contrary = tuple(a for a in ids if a not in candidate and signs[a] == -direction)"
            ),
        ),
        checks=(
            "test_aggregation.py::TestS6TheDependencyGraph::test_b_non_selection_is_not_exclusion",
            "test_aggregation.py::TestS6TheDependencyGraph::test_g_contestation_clamps_at_the_prior",
        ),
    ),
    Arm(
        row="S6",
        asserts="contestation is clamped at the prior — without the clamp it can cross and flip the sign",
        sabotage=Sabotage(
            module="policy.py",
            before="        return value - direction * min(magnitude, abs(value))  # clamped at the prior",
            after="        return value - direction * magnitude  # clamp removed",
        ),
        checks=("test_aggregation.py::TestS6TheDependencyGraph::test_g_contestation_clamps_at_the_prior",),
    ),
]

# --- P1 --------------------------------------------------------------------

_P1 = [
    Arm(
        row="P1",
        asserts="the binding must be an exact PolicyBinding — nothing else computes",
        sabotage=Sabotage(
            module="belief.py",
            before="    if not isinstance(binding, PolicyBinding):",
            after="    if False:",
        ),
        checks=(
            "test_belief.py::TestP1TheBindingIsExact::test_nothing_refuses",
            "test_belief.py::TestP1TheBindingIsExact::test_the_rule_identity_alone_refuses",
        ),
    ),
]

# --- P2 --------------------------------------------------------------------

_P2 = [
    Arm(
        row="P2",
        asserts="a named implementation that fails its own fixtures is refused, not merely unavailable",
        sabotage=Sabotage(
            module="belief.py",
            before="    if not conforms(implementation, fixtures):",
            after="    if False:",
        ),
        checks=(
            "test_belief.py::TestP2FixtureFailureRefuses::test_a_failing_implementation_refuses_not_unavailable",
            "test_belief.py::TestP2FixtureFailureRefuses::test_installing_a_conforming_one_beside_it_still_refuses",
        ),
    ),
]

# --- P3 --------------------------------------------------------------------

_P3 = [
    Arm(
        row="P3",
        asserts="the policy binding is a projected member — the belief digest is a function of it",
        sabotage=Sabotage(
            module="closure.py",
            before='        "policy_binding": list(binding),',
            after='        "policy_binding": [],',
        ),
        checks=("test_closure.py::test_each_member_moves_the_digest[policy_binding]",),
    ),
]

# --- P4 --------------------------------------------------------------------

_P4 = [
    Arm(
        row="P4",
        asserts="an eligible set with nothing directional is distinguishable from no eligible assessment at all",
        sabotage=Sabotage(
            module="belief.py",
            before='        return NoBelief("no-directional-outcome")',
            after='        return NoBelief("no-eligible-assessment")',
        ),
        checks=(
            "test_belief.py::TestP4TheAbsencesAreDistinguishable::test_fifty_inconclusive_are_not_an_absence_of_assessment",
        ),
    ),
]

# --- P5 --------------------------------------------------------------------

_P5 = [
    Arm(
        row="P5",
        asserts="an implementation that smuggles in a per-assessment weight fails the reference fixture set",
        sabotage=Sabotage(
            module="policy.py",
            before="    signs = {v.assessment: v.sign for v in problem.vertices}\n    ids = tuple(sorted(signs))",
            after=(
                "    signs = {v.assessment: v.sign for v in problem.vertices}\n"
                "    ids = tuple(sorted(signs))\n"
                "    if ids:\n"
                "        signs[ids[0]] = signs[ids[0]] * 2"
            ),
        ),
        checks=("test_aggregation.py::TestTheFixtureSetBindsTheReference::test_the_reference_conforms",),
    ),
]

# --- P6 --------------------------------------------------------------------

_P6 = [
    Arm(
        row="P6",
        asserts="no facet field beyond outcome bears magnitude — reading estimate into the vertex build moves the value",
        sabotage=Sabotage(
            module="belief.py",
            before=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs)"
            ),
            after=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs) + tuple(\n"
                '        DirectionalInput(assessment=a.identity() + ":estimate", sign=OUTCOME_SIGNS[a.outcome])\n'
                "        for a in graph_inputs\n"
                "        if a.estimate is not None\n"
                "    )"
            ),
        ),
        checks=("test_belief.py::TestP6NoMagnitudeBearingRead::test_each_field_moves_the_digest_and_not_the_value",),
    ),
]

# --- P7 --------------------------------------------------------------------

_P7 = [
    Arm(
        row="P7",
        asserts="the evaluator accepts no prior value and no prior digest — belief is a computed view, not accumulated",
        sabotage=Sabotage(
            module="belief.py",
            before="    profile: ProfileSpec,\n) -> Belief | NoBelief | Refused:",
            after="    profile: ProfileSpec,\n    prior_digest: str | None = None,\n) -> Belief | NoBelief | Refused:",
        ),
        checks=(
            "test_belief.py::TestP7BeliefIsAComputedView::test_the_evaluator_accepts_no_prior_value_and_no_prior_digest",
        ),
    ),
]

# --- P8 --------------------------------------------------------------------

_P8 = [
    Arm(
        row="P8",
        asserts="inconclusive is not a vertex — admitting it as one is not a cardinality gift, it is a refused construction",
        sabotage=Sabotage(
            module="belief.py",
            before=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in graph_inputs)"
            ),
            after=(
                "    vertices = tuple(DirectionalInput(assessment=a.identity(), "
                "sign=OUTCOME_SIGNS[a.outcome]) for a in eligible)"
            ),
        ),
        checks=(
            "test_belief.py::TestP8InconclusiveIsValueInertAndDigestCommitted::test_the_exclusion_is_not_a_cardinality_gift",
        ),
    ),
]

# --- P9 --------------------------------------------------------------------

_P9 = [
    Arm(
        row="P9",
        asserts="unavailable-input-unheld fires only when the withheld input was the last directional one",
        sabotage=Sabotage(
            module="belief.py",
            before=(
                "    directional = [a for a in eligible if OUTCOME_SIGNS[a.outcome] != 0]\n"
                "    if not directional:\n"
                "        if unheld_only and any(OUTCOME_SIGNS[a.outcome] != 0 for a in unheld_only):\n"
                '            return NoBelief("unavailable-input-unheld")\n'
                "        if not eligible:\n"
                '            return NoBelief("no-eligible-assessment")\n'
                '        return NoBelief("no-directional-outcome")'
            ),
            after=(
                "    directional = [a for a in eligible if OUTCOME_SIGNS[a.outcome] != 0]\n"
                "    if unheld_only and any(OUTCOME_SIGNS[a.outcome] != 0 for a in unheld_only):\n"
                '        return NoBelief("unavailable-input-unheld")\n'
                "    if not directional:\n"
                "        if not eligible:\n"
                '            return NoBelief("no-eligible-assessment")\n'
                '        return NoBelief("no-directional-outcome")'
            ),
        ),
        checks=("test_belief.py::TestP9UnholdingPrecedence::test_partial_unholding_recomputes_from_the_survivors",),
    ),
]

# --- M6 ----------------------------------------------------------------
# The completion tied to the consulted walk: cut 1's own M6 arms (successor
# refusal over `contract/domain.py`) stand unchanged in `ARMS`. What is new
# here is the real succession path reaching the belief digest through the
# `consulted` closure member.

_M6 = [
    Arm(
        row="M6",
        asserts="the real succession path moves the consulted digest, and hence the belief digest",
        sabotage=Sabotage(
            module="closure.py",
            before='        "consulted": [list(pair) for pair in consulted],',
            after='        "consulted": [],',
        ),
        checks=("test_closure.py::test_an_additive_successor_moves_consulted_digests",),
    ),
]

# --- M8 ----------------------------------------------------------------
# The completion tied to the consulted walk: cut 1's own M8 arms (profile
# projection) stand unchanged in `ARMS`. What is new here is that an
# activated-but-unread namespace bump must stay absent from the walk's output.

_M8 = [
    Arm(
        row="M8",
        asserts="an activated-but-unread namespace bump is absent from the walk's output and the belief digest",
        sabotage=Sabotage(
            module="consulted.py",
            before=(
                "    read: set[str] = set()\n"
                "    for claim in claims.values():\n"
                "        read.add(profile.operator(claim.operator).contract)"
            ),
            after=("    read: set[str] = set()\n    for corpus in corpora:\n        read.update(pins[corpus].domains)"),
        ),
        checks=("test_closure.py::test_an_activated_but_unconsulted_bump_is_absent",),
    ),
]

# --- D3 ----------------------------------------------------------------

_D3 = [
    Arm(
        row="D3",
        asserts="an unheld vocabulary dataset reads not-available — derived from admission state, not assumed",
        sabotage=Sabotage(
            module="admission.py",
            before="    if isinstance(state, Held):",
            after="    if True:",
        ),
        checks=(
            "test_admission.py::TestD3NotAvailableIsDerived::test_an_unheld_vocabulary_dataset_reads_not_available",
        ),
    ),
]

# --- D6 ----------------------------------------------------------------
# The base contract is consulted unconditionally; a domain contract only if
# actually read. Two independent ways for that boundary to fail.

_D6 = [
    Arm(
        row="D6",
        asserts="consulting every pinned namespace — not only the read ones — leaves an unread namespace's bump visible",
        sabotage=Sabotage(
            module="consulted.py",
            before=(
                "    read: set[str] = set()\n"
                "    for claim in claims.values():\n"
                "        read.add(profile.operator(claim.operator).contract)"
            ),
            after=("    read: set[str] = set()\n    for corpus in corpora:\n        read.update(pins[corpus].domains)"),
        ),
        checks=("test_consulted.py::TestTheWalk::test_an_activated_but_unread_namespace_stays_out",),
    ),
    Arm(
        row="D6",
        asserts="the base contract's consultation is unconditional — not gated on whether any claim reads a base facet",
        sabotage=Sabotage(
            module="consulted.py",
            before="        consulted[namespace] = identities.pop()\n    return tuple(sorted(consulted.items()))",
            after=(
                "        consulted[namespace] = identities.pop()\n"
                "    if not read:\n"
                "        consulted.pop(BASE_NAMESPACE, None)\n"
                "    return tuple(sorted(consulted.items()))"
            ),
        ),
        checks=(
            "test_consulted.py::TestTheWalk::test_the_base_contract_is_unconditional",
            "test_closure.py::test_the_base_contract_arm_at_the_eligibility_hinge",
        ),
    ),
]

# --- D7 ----------------------------------------------------------------
# §8.1's agreement rule refuses a closure whose corpora disagree — at both
# sites: the always-consulted base contract, and each read domain namespace.

_D7 = [
    Arm(
        row="D7",
        asserts="the base contract's agreement is unconditional — corpora pinning different science_contracts refuse",
        sabotage=Sabotage(
            module="consulted.py",
            before="    if len(base_identities) != 1:",
            after="    if False:",
        ),
        checks=("test_consulted.py::TestAgreement::test_science_contract_agreement_is_unconditional",),
    ),
    Arm(
        row="D7",
        asserts="a domain namespace resolving to more than one identity across corpora refuses, all the way to the evaluator",
        sabotage=Sabotage(
            module="consulted.py",
            before="        if len(identities) != 1:",
            after="        if False:",
        ),
        checks=(
            "test_consulted.py::TestAgreement::test_two_corpora_pinning_different_identities_for_one_namespace_refuse",
            "test_belief.py::TestD7AtTheEvaluator::test_disagreeing_corpora_refuse_the_derivation",
        ),
    ),
]


CUT2_ARMS: tuple[Arm, ...] = tuple(
    _G9
    + _G2b
    + _G6
    + _G2c
    + _G1
    + _G3
    + _G8
    + _S5
    + _S6
    + _P1
    + _P2
    + _P3
    + _P4
    + _P5
    + _P6
    + _P7
    + _P8
    + _P9
    + _M6
    + _M8
    + _D3
    + _D6
    + _D7
)
