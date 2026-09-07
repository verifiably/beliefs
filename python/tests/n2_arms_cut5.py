"""Cut 5's 28 selected family-adapter arms and their exact sabotages."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT5_ARMS"]


_PROPOSITION_IDENTITY_DROPPED = Sabotage(
    module="stored.py",
    before='    "proposition": (PROPOSITION_FACET,),',
    after='    "proposition": (),',
)

_STANDING_DISABLED = Sabotage(
    module="corpus.py",
    before="    return standing.get(view.resolve(ref) or ref, True)",
    after="    return True",
)

_CYCLE_WITNESS_DROPPED = Sabotage(
    module="corpus.py",
    before="                return tuple(sorted((*pairwise(path), (node, child))))",
    after="                return ()",
)


_SUPERSEDE_AND_REVISE = (
    Arm(
        row="S2",
        asserts=(
            "through `supersede`, changing proposition semantic scope mints a fresh proposition, "
            "one adapter-authored `supersedes` edge, and leaves the predecessor untouched"
        ),
        sabotage=Sabotage(
            module="corpus.py",
            before="                        Relation(source=successor.id, predicate=stored.SUPERSEDES, target=predecessor_id),\n",
            after="",
        ),
        checks=("acceptance/test_n2_cut5.py::test_scope_supersession_preserves_predecessor_evidence",),
    ),
    Arm(
        row="S4",
        asserts="the semantic-change branch reaches no `nodes.rename` path",
        sabotage=Sabotage(
            module="corpus.py",
            before="            return self._corpus.add(candidate)\n\n    def revise(",
            after="            return self._corpus.rename(candidate)\n\n    def revise(",
        ),
        checks=("acceptance/test_n2_cut5.py::test_semantic_change_branch_names_no_rename_path",),
    ),
    Arm(
        row="G7",
        asserts=(
            "editing proposition scope mints a new semantic identity while prior evidence remains "
            "bound to the predecessor and belief on that predecessor remains unchanged"
        ),
        sabotage=_PROPOSITION_IDENTITY_DROPPED,
        checks=("acceptance/test_n2_cut5.py::test_scope_supersession_preserves_predecessor_evidence",),
    ),
    Arm(
        row="G7",
        asserts="revising title alone mints nothing and leaves the semantic digest unchanged",
        sabotage=Sabotage(
            module="stored.py",
            before='        "kind": node.kind,\n        "present": present,',
            after='        "kind": node.kind,\n        "title": node.title,\n        "present": present,',
        ),
        checks=("test_revise.py::test_revise_prose_in_place_no_mint",),
    ),
    Arm(
        row="G7",
        asserts="revising `display_statement` mints nothing and leaves the semantic digest unchanged",
        sabotage=Sabotage(
            module="stored.py",
            before='    "proposition": (PROPOSITION_FACET,),',
            after='    "proposition": (PROPOSITION_FACET, DISPLAY_FACET),',
        ),
        checks=("test_revise.py::test_revise_display_statement_add_change_remove",),
    ),
    Arm(
        row="M5",
        asserts=(
            "the founding `in adults` to `in all humans` change mints a new identity and leaves "
            "the prior assessment bound to the predecessor"
        ),
        sabotage=_PROPOSITION_IDENTITY_DROPPED,
        checks=("acceptance/test_n2_cut5.py::test_scope_supersession_preserves_predecessor_evidence",),
    ),
)


_EXPLICIT_IMPORT = (
    Arm(
        row="S3",
        asserts="a semantic-field edit with a stale stored stamp refuses before any payload write",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):\n"
                '                raise ValidationRefused(f"{node.id}: semantic-identity stamp is missing or stale")'
            ),
            after="            if False:\n                pass",
        ),
        checks=("test_import_bundle.py::test_stale_stamp_member_refuses",),
    ),
    Arm(
        row="S3",
        asserts="a semantic-field edit restamped consistently is admitted undetected",
        sabotage=Sabotage(
            module="corpus.py",
            before="                covered = stored.COVERED_FACETS.get(record.kind)",
            after=(
                '                if record.kind == "proposition":\n'
                '                    raise ValidationRefused(f"{record.id}: propositions are not importable")\n'
                "                covered = stored.COVERED_FACETS.get(record.kind)"
            ),
        ),
        checks=("acceptance/test_n2_cut5.py::test_restamped_semantic_edit_is_imported",),
    ),
    Arm(
        row="T1",
        asserts=(
            "an explicitly imported foreign act-report enters structurally validated, not "
            "operation-authenticated, attributed, and inert without stored validation state"
        ),
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                '                if record.kind == "act-report":\n'
                "                    self._refuse_malformed_act_report(record)"
            ),
            after=(
                '                if record.kind == "act-report":\n'
                "                    pass"
            ),
        ),
        checks=(
            "acceptance/test_n2_cut5.py::test_foreign_act_report_is_attributed_inert_and_structurally_validated",
        ),
    ),
    Arm(
        row="T2",
        asserts=(
            "a successful import records one intent and exactly one qualifying terminal report, "
            "with no payload act before the intent"
        ),
        sabotage=Sabotage(
            module="root.py",
            before="            fulfills=fulfills,",
            after="            fulfills=None,",
        ),
        checks=("acceptance/test_durable_families.py::test_import_bundle_records_the_exact_durable_chain",),
    ),
    Arm(
        row="T2",
        asserts="a post-intent refusal writes one fulfilling refusal report and no payload",
        sabotage=Sabotage(
            module="corpus.py",
            before="                self._operation_port.execute_fulfilling([self._create_op(report_node)], intent_digest)",
            after="                pass",
        ),
        checks=(
            "acceptance/test_n2_cut5.py::test_post_intent_refusal_writes_one_fulfilling_report_and_no_payload",
        ),
    ),
    Arm(
        row="T2",
        asserts="intent-append failure begins no payload or report act and mints no record",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            intent_digest = self._operation_port.append_intent(\n"
                '                v1.encode({"kind": intent.kind, "event_token": intent.event_token, "actor": intent.actor})\n'
                "            )"
            ),
            after=f'            intent_digest = {"0" * 64!r}',
        ),
        checks=("acceptance/test_n2_cut5.py::test_intent_append_failure_begins_no_act",),
    ),
    Arm(
        row="M3",
        asserts=(
            "`standing_in_local_view` terminates stably over increasing chains, counters, and siblings"
        ),
        sabotage=Sabotage(
            module="corpus.py",
            before="    return tuple(ordered)\n\n\ndef _cycle_edges(",
            after="    return tuple(reversed(ordered))\n\n\ndef _cycle_edges(",
        ),
        checks=(
            "test_local_standing.py::test_standing_is_subtracted_by_one_standing_retraction",
            "test_local_standing.py::test_counter_retraction_restores_iff_no_standing_sibling_remains",
            "test_local_standing.py::test_counter_counter_retraction_retracts_the_restoration",
        ),
    ),
    Arm(
        row="M3",
        asserts="the cycle validator returns a cycle-specific offending-edge witness",
        sabotage=_CYCLE_WITNESS_DROPPED,
        checks=("acceptance/test_n2_cut5.py::test_cycle_validator_returns_the_offending_edges",),
    ),
    Arm(
        row="M3",
        asserts="import consumes a forced cycle verdict, refuses, and writes no payload",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if cycle_edges:\n            raise ImportRefused(",
            after="        if False and cycle_edges:\n            raise ImportRefused(",
        ),
        checks=("acceptance/test_n2_cut5.py::test_import_consumes_a_forced_cycle_verdict",),
    ),
    Arm(
        row="M3",
        asserts="an ordinary retraction whose target does not resolve is refused",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                '            resolved = view.resolve(target["ref"])\n'
                '            if resolved is None or resolved != target["resolved"]:\n'
                '                raise RetractionTargetUnresolvable(f"{record.id}: node target does not resolve exactly")'
            ),
            after=(
                '            resolved = view.resolve(target["ref"])\n'
                "            if False:\n"
                '                raise RetractionTargetUnresolvable(f"{record.id}: node target does not resolve exactly")'
            ),
        ),
        checks=("test_retract.py::test_retract_refuses_an_unresolvable_node_target",),
    ),
    Arm(
        row="R20",
        asserts="import refuses a stochastic-unseeded analysis spec paired with a bitwise equivalence rule",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "        except UnfreezableSpec as caught:\n"
                '            raise ValidationRefused(f"{record.id}: {caught}") from caught'
            ),
            after="        except UnfreezableSpec:\n            pass",
        ),
        checks=("test_import_bundle.py::test_contradictory_nondeterminism_contract_refused",),
    ),
)


_RETRACTION = (
    Arm(
        row="C1",
        asserts="retraction is additive: the target remains byte-identical and resolvable",
        sabotage=Sabotage(
            module="corpus.py",
            before="            return self._corpus.add(record)\n\n    def supersede(",
            after=(
                '            return self._corpus.add(resolved_target.model_copy(update={"title": record.title}))\n\n'
                "    def supersede("
            ),
        ),
        checks=("test_retract.py::test_retract_is_create_only_and_target_untouched",),
    ),
    Arm(
        row="C2",
        asserts="actor, event attribution, typed reason, rationale, and grounds are required",
        sabotage=Sabotage(
            module="stored.py",
            before=(
                '    if type(reason) is not str:\n'
                '        raise MalformedRecord("a retraction reason is a string")\n'
                "    if reason not in RETRACTION_REASONS:\n"
                '        raise MalformedRecord(f"retraction reason {reason!r} is outside the closed set {RETRACTION_REASONS}")\n'
                "    if type(rationale) is not str or not rationale:\n"
                '        raise MalformedRecord("a retraction rationale is a non-empty string")\n'
                "    if isinstance(grounds, (str, bytes)) or not isinstance(grounds, Sequence):\n"
                '        raise MalformedRecord("a retraction\'s grounds are a sequence of references")\n'
                "    grounds_list = list(grounds)\n"
                "    if not grounds_list or not all(type(ground) is str and ground for ground in grounds_list):\n"
                '        raise MalformedRecord("a retraction names at least one string ground reference")\n'
                "    if type(actor) is not str or not actor or type(event_token) is not str or not event_token:\n"
                '        raise MalformedRecord("a retraction carries actor and event attribution")'
            ),
            after=(
                '    reason = reason or "authored-error"\n'
                '    rationale = rationale or "missing"\n'
                '    grounds = grounds or ("source:missing",)\n'
                '    actor = actor or "missing"\n'
                '    event_token = event_token or "missing"\n'
                "    grounds_list = list(grounds)"
            ),
        ),
        checks=("acceptance/test_n2_cut5.py::test_retraction_required_fields_refuse_when_empty",),
    ),
    Arm(
        row="C3",
        asserts="an in-closure standing retraction moves the digest while an outside retraction does not",
        sabotage=Sabotage(
            module="closure.py",
            before='            "found": [list(pair) for pair in retractions.found],',
            after='            "found": [],',
        ),
        checks=("acceptance/test_n2_cut5.py::test_retraction_enumeration_moves_only_when_in_closure",),
    ),
    Arm(
        row="C4",
        asserts="subtracting support lowers belief and subtracting refutation raises it through the same rule",
        sabotage=_STANDING_DISABLED,
        checks=("acceptance/test_n2_cut5.py::test_retraction_subtraction_is_direction_free",),
    ),
    Arm(
        row="C5",
        asserts="retract then counter-retract restores admission while all three digest states differ",
        sabotage=_STANDING_DISABLED,
        checks=("acceptance/test_n2_cut5.py::test_retraction_chain_restores_admission_with_distinct_digests",),
    ),
    Arm(
        row="C5",
        asserts="counter-retracting one sibling leaves the target subtracted until the other is countered",
        sabotage=_STANDING_DISABLED,
        checks=("test_local_standing.py::test_counter_retraction_restores_iff_no_standing_sibling_remains",),
    ),
    Arm(
        row="C6",
        asserts=(
            "retracting a false failure admits only while a standing pass remains; retracting the pass de-admits"
        ),
        sabotage=_STANDING_DISABLED,
        checks=("acceptance/test_n2_cut5.py::test_verification_retractions_recompute_admission_and_belief",),
    ),
    Arm(
        row="C10",
        asserts="node-arm targets of kind note, proposition, and run are refused",
        sabotage=Sabotage(
            module="corpus.py",
            before='ELIGIBLE_RETRACTION_TARGET_KINDS = ("assessment", "retraction", "verification")',
            after=(
                'ELIGIBLE_RETRACTION_TARGET_KINDS = ("assessment", "note", "proposition", "retraction", "run", '
                '"verification")'
            ),
        ),
        checks=("acceptance/test_n2_cut5.py::test_ineligible_node_target_kinds_refuse",),
    ),
    Arm(
        row="C10",
        asserts="a route target absent from the locally resolved dataset's stamped basis is refused",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "        if not any(route.get(\"identity\") == target[\"route_identity\"] for route in stored.basis_routes(dataset)):\n"
                "            raise RetractionTargetUnresolvable("
            ),
            after=(
                "        if False:\n"
                "            raise RetractionTargetUnresolvable("
            ),
        ),
        checks=("test_retract.py::test_retract_refuses_a_route_absent_from_the_stamped_basis",),
    ),
    Arm(
        row="G2c",
        asserts=(
            "after retraction, only a standing clean-environment pass admits; a passing sibling clears no failure"
        ),
        sabotage=Sabotage(
            module="verification.py",
            before='    if any(v.scope == "clean-environment" and v.verdict == "passed" for v in live):',
            after="    if False:",
        ),
        checks=("acceptance/test_n2_cut5.py::test_verification_retractions_recompute_admission_and_belief",),
    ),
    Arm(
        row="G8",
        asserts="a standing retraction of an active failure clears it and forces belief-input recomputation",
        sabotage=Sabotage(
            module="closure.py",
            before='        "verifications": [list(row) for row in verification_rows],',
            after='        "verifications": [],',
        ),
        checks=("acceptance/test_n2_cut5.py::test_verification_retractions_recompute_admission_and_belief",),
    ),
)


CUT5_ARMS = (*_SUPERSEDE_AND_REVISE, *_EXPLICIT_IMPORT, *_RETRACTION)
