"""Cut 11's declared arms and citations: 13 selected + 13 labeled = 26 units.

L7u12's second-fulfilling-registration classification stays cut 8's —
cited here, never an arm of this cut.
"""

from n2_arms import Arm, Sabotage

CUT11_ARMS = (
    Arm(
        "L7u1",
        "no pointers reads the attempt finding, never a refutation",
        Sabotage(
            "intents/reduce.py",
            before='code="intent-attempt-without-recorded-outcome",',
            after='code="intent-attempt-withheld",',
        ),
        ("test_intent_reduce.py::test_no_pointers_reads_attempt_without_recorded_outcome",),
    ),
    Arm(
        "L7u2a",
        "a wrong-purpose committed transaction fails qualification",
        Sabotage(
            "intents/shapes.py",
            before='return "wrong-purpose"\n    if isinstance(value, OperationIntent):',
            after="return None\n    if isinstance(value, OperationIntent):",
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_purpose_member",
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "L7u2b",
        "a run publication under another spec fails qualification",
        Sabotage(
            "intents/shapes.py",
            before="if evidence.spec_identity != value.spec_identity:",
            after="if False:",
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_spec_member",
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "L7u2c",
        "a run publication under another event token fails qualification",
        Sabotage(
            "intents/shapes.py",
            before='return "wrong-spec"\n            return None if evidence.event_token == value.event_token else "wrong-token"',
            after='return "wrong-spec"\n            return None',
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_token_member",
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "L7u2d",
        "a publication creating no run fails qualification, named no-record",
        Sabotage(
            "intents/reduce.py",
            before=(
                'if not record_paths:\n'
                '            non_qualifying.append((registration.digest, "no-record"))\n'
                '            continue'
            ),
            after=(
                "return (\n                IntentQualification(intent.digest, intent.shape, "
                '"matched", registration.digest),\n                (),\n            )'
            ),
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u2_no_record_member",
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "L7u3",
        "decayed genuine bytes read unresolvable with no unmatched finding",
        Sabotage(
            "intents/reduce.py",
            before="except RecordUndecodable:\n            pointer_unresolved = True",
            after='except RecordUndecodable:\n            reasons.append("no-record")',
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u3_decayed_genuine_run_is_unresolvable_silently",
            "test_intent_reduce.py::test_undecodable_bytes_are_unresolvable",
        ),
    ),
    Arm(
        "L7u4",
        "the assessment intent is durably appended before any member act",
        Sabotage(
            "boundary.py",
            before=(
                "intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)\n"
                "    fulfills = port.append_intent(_intent_wire(intent))"
            ),
            after=(
                "intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)\n"
                '    fulfills = "0" * 64  # append deferred'
            ),
        ),
        ("test_run_persistence.py::test_kill_between_append_and_start_leaves_intent_only",),
    ),
    Arm(
        "L7u6",
        "publication through a root other than the intent's refuses",
        Sabotage("root.py", before="fulfills=self._fulfills,", after="fulfills=None,"),
        (
            "test_run_persistence.py::test_cross_root_publication_refuses",
            "test_run_persistence.py::test_assessment_sequence_appends_intent_then_publishes_fulfilling",
        ),
    ),
    Arm(
        "L7u7",
        "no caller-supplied fulfills path exists at the boundary",
        Sabotage(
            "boundary.py",
            before="def execute_assessment_run(\n    *,\n    spec: object,\n    port: OperationPort,",
            after=(
                "def execute_assessment_run(\n    *,\n    fulfills: str | None = None,\n"
                "    spec: object,\n    port: OperationPort,"
            ),
        ),
        ("test_run_persistence.py::test_no_caller_supplied_fulfills_path_exists",),
    ),
    Arm(
        "L7u8",
        "a wholly discarded attempt is indistinguishable by construction",
        Sabotage(
            "boundary.py",
            before=(
                'refused = _refused("no-frozen-spec", subject, actor, observer, started_at)\n'
                "        port.execute(_report_plan(refused.report))"
            ),
            after=(
                'refused = _refused("no-frozen-spec", subject, actor, observer, started_at)\n'
                '        port.append_intent(_intent_wire(AssessmentRunIntent("0" * 64, '
                "refused.report.event_token, actor)))\n"
                "        port.execute(_report_plan(refused.report))"
            ),
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u8_negative_discarded_attempt_is_indistinguishable",
        ),
    ),
    Arm(
        "L7u9",
        "a report carrying another operation's token fails qualification",
        Sabotage(
            "intents/shapes.py",
            before=(
                'if evidence.operation != value.kind:\n                return "wrong-kind"\n'
                '            return None if evidence.event_token == value.event_token else "wrong-token"'
            ),
            after=(
                'if evidence.operation != value.kind:\n                return "wrong-kind"\n'
                "            return None"
            ),
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u9_wrong_operation_token_fails_qualification",
        ),
    ),
    Arm(
        "L7u10",
        "a report of the wrong kind fails qualification",
        Sabotage(
            "intents/shapes.py",
            before='if evidence.operation != value.kind:\n                return "wrong-kind"',
            after='if False:\n                return "wrong-kind"',
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u10_wrong_kind_report_fails_qualification",
            "test_intent_gate.py::test_matching_requirements_per_shape",
        ),
    ),
    Arm(
        "L7u11",
        "a run publication never fulfills a non-run operation",
        Sabotage(
            "intents/shapes.py",
            before=(
                'if type(evidence) is ReportEvidence:\n'
                '            if evidence.operation != value.kind:\n'
                '                return "wrong-kind"\n'
                '            return None if evidence.event_token == value.event_token else "wrong-token"\n'
                '        return "wrong-purpose"'
            ),
            after=(
                'if type(evidence) is ReportEvidence:\n'
                '            if evidence.operation != value.kind:\n'
                '                return "wrong-kind"\n'
                '            return None if evidence.event_token == value.event_token else "wrong-token"\n'
                '        return (None if evidence.event_token == value.event_token else "wrong-token") '
                'if type(evidence) is RunEvidence else "wrong-purpose"'
            ),
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u11_run_for_non_run_operation_fails_qualification",
            "test_intent_gate.py::test_matching_requirements_per_shape",
        ),
    ),
    Arm(
        "L7u12",
        "a registration publishing no terminal record fails qualification",
        Sabotage(
            "intents/reduce.py",
            before=(
                'if not record_paths:\n'
                '            non_qualifying.append((registration.digest, "no-record"))\n'
                '            continue'
            ),
            after=(
                "return (\n                IntentQualification(intent.digest, intent.shape, "
                '"matched", registration.digest),\n                (),\n            )'
            ),
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_u12_no_terminal_record_fails_qualification",
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "L7u13",
        "the operation intent is durably appended before its first act",
        Sabotage(
            "boundary.py",
            before=(
                'intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)\n'
                "    fulfills = port.append_intent(_intent_wire(intent))"
            ),
            after=(
                'intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)\n'
                '    fulfills = "0" * 64  # append deferred'
            ),
        ),
        (
            "test_run_persistence.py::test_kill_between_append_and_start_leaves_intent_only_operation_kind",
        ),
    ),
    Arm(
        "J1",
        "an absent record path is unresolvable, never silently resolved",
        Sabotage(
            "intents/reduce.py",
            before=(
                "if payload is None:\n            pointer_unresolved = True\n            continue"
            ),
            after="if payload is None:\n            continue",
        ),
        ("test_intent_reduce.py::test_unresolvable_wins_over_non_qualifying_and_emits_nothing",),
    ),
    Arm(
        "J1b",
        "audit and restore capture records inside their shared held assembly",
        Sabotage(
            "world/verify.py",
            before="records = capture_records(root, kind)\n    return view, disk, records, presented",
            after="records = ()\n    return view, disk, records, presented",
        ),
        (
            "test_world_log_audit.py::TestTheAuditAct::test_it_holds_the_corpus_operation_lock_across_inspection_and_capture",
        ),
    ),
    Arm(
        "J1c",
        "arrival captures records inside its hold before admission",
        Sabotage(
            "world/verify.py",
            before='records = capture_records(root, "corpus")\n        report = evaluate_log(',
            after='records = ()\n        report = evaluate_log(',
        ),
        (
            "test_world_arrival.py::TestTheHold::test_it_holds_both_locks_across_inspection_capture_and_the_transaction",
            "test_world_arrival.py::TestTheHold::test_the_in_hold_order_is_inspection_then_the_claim_then_the_capture",
        ),
    ),
    Arm(
        "J1d",
        "the evaluator requires a typed records input with no empty fallback",
        Sabotage(
            "world/verify.py",
            before=(
                "if type(records) is not tuple:\n"
                "        raise TypeError(\n"
                '            "records is the captured published-record surface as a tuple of (path, payload) pairs"\n'
                "        )"
            ),
            after=(
                "if False:\n"
                "        raise TypeError(\n"
                '            "records is the captured published-record surface as a tuple of (path, payload) pairs"\n'
                "        )"
            ),
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_records_is_required_and_typed",
        ),
    ),
    Arm(
        "J1e",
        "capture returns every present record in sorted path order",
        Sabotage(
            "world/records.py",
            before="into.records.append((path, payload))",
            after="into.records[:] = [(path, payload)]",
        ),
        ("test_record_capture.py::test_captures_each_record_file_sorted",),
    ),
    Arm(
        "J1f",
        "the shared audit and restore assembly forwards captured records",
        Sabotage(
            "world/verify.py",
            before="return view, disk, records, presented",
            after="return view, disk, (), presented",
        ),
        (
            "test_world_log_audit.py::TestTheAuditAct::test_the_shared_assembly_forwards_the_captured_records",
        ),
    ),
    Arm(
        "J2a",
        "the leaf is classified before any readable open, never followed",
        Sabotage(
            "world/records.py",
            before=(
                "try:\n"
                "            if not stat.S_ISREG(os.fstat(path_fd).st_mode):\n"
                '                return "silent"\n'
                "        except OSError:\n"
                '            return "unreadable"\n'
                "        try:\n"
                '            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)\n'
                "        except OSError:\n"
                '            return "unreadable"'
            ),
            after="read_fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dir_fd)",
        ),
        (
            "test_record_capture.py::test_swap_race_is_lost_by_the_attacker",
            "test_record_capture.py::test_leaf_symlink_is_classified_and_withheld",
            "test_record_capture.py::test_fifo_is_classified_never_opened_readable",
        ),
    ),
    Arm(
        "J2b",
        "an intermediate namespace symlink is never followed",
        Sabotage(
            "world/records.py",
            before="os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd",
            after="os.O_DIRECTORY, dir_fd=parent_fd",
        ),
        ("test_record_capture.py::test_intermediate_symlink_directory_is_withheld",),
    ),
    Arm(
        "J3a",
        "the writer refuses an over-ceiling postimage before any write",
        Sabotage(
            "root.py",
            before="if isinstance(content, bytes) and len(content) > RECORD_CEILING:",
            after="if isinstance(content, bytes) and len(content) > RECORD_CEILING * 1024:",
        ),
        ("test_operation_port.py::test_oversized_postimage_refuses_before_any_write",),
    ),
    Arm(
        "J3b",
        "the reader withholds wholly, never hands a truncation to a decoder",
        Sabotage(
            "world/records.py",
            before="remaining = RECORD_CEILING + 1",
            after="remaining = RECORD_CEILING",
        ),
        ("test_record_capture.py::test_ceiling_boundary_exact_captures_one_over_withholds",),
    ),
    Arm(
        "J4a",
        "the operation discriminator is closed over OPERATION_KINDS",
        Sabotage(
            "intents/shapes.py",
            before=(
                'if set(value) == {"kind", "event_token", "actor"} '
                "and value.get(\"kind\") in OPERATION_KINDS:"
            ),
            after='if set(value) == {"kind", "event_token", "actor"}:',
        ),
        ("test_intent_gate.py::test_out_of_vocabulary_kind_is_domainless_unrecognized",),
    ),
    Arm(
        "J4b",
        "a discriminator-matched malformed payload is an error",
        Sabotage(
            "intents/shapes.py",
            before='return Unrecognized(digest, "intent-payload-malformed", "error", shape)',
            after='return Unrecognized(digest, "intent-payload-malformed", "warning", shape)',
        ),
        (
            "test_intent_gate.py::test_discriminator_matched_schema_invalid_is_payload_malformed_error",
            "test_intent_reduce.py::test_unrecognized_rows_carry_the_gate_finding_and_none_reduce",
        ),
    ),
    Arm(
        "J4c",
        "a foreign domain is an unrecognized warning",
        Sabotage(
            "intents/shapes.py",
            before=(
                "return Unrecognized(\n"
                "            digest,\n"
                '            "intent-domain-unrecognized",\n'
                '            "warning",\n'
                '            str(sniffed["domain"]),\n'
                "        )"
            ),
            after=(
                "return Unrecognized(\n"
                "            digest,\n"
                '            "intent-domain-unrecognized",\n'
                '            "error",\n'
                '            str(sniffed["domain"]),\n'
                "        )"
            ),
        ),
        (
            "test_intent_gate.py::test_foreign_domain_reads_unrecognized_warning",
            "test_intent_reduce.py::test_unrecognized_rows_carry_the_gate_finding_and_none_reduce",
        ),
    ),
    Arm(
        "J4d",
        "a parseable domainless object carries the domainless detail",
        Sabotage(
            "intents/shapes.py",
            before=(
                "except MalformedRecord:\n"
                '            return _malformed(digest, "assessment-run")\n'
                "    return Unrecognized(\n"
                "        digest,\n"
                '        "intent-domain-unrecognized",\n'
                '        "warning",\n'
                '        "domainless-unrecognized",\n'
                "    )"
            ),
            after=(
                "except MalformedRecord:\n"
                '            return _malformed(digest, "assessment-run")\n'
                "    return Unrecognized(\n"
                "        digest,\n"
                '        "intent-domain-unrecognized",\n'
                '        "warning",\n'
                '        "wrong-detail",\n'
                "    )"
            ),
        ),
        ("test_intent_gate.py::test_empty_object_reads_domainless_unrecognized",),
    ),
    Arm(
        "J4e",
        "non-JSON bytes are unrecognized as undecodable",
        Sabotage(
            "intents/shapes.py",
            before=(
                "except CanonicalTextRefused:\n"
                "        return Unrecognized(\n"
                "            digest,\n"
                '            "intent-domain-unrecognized",\n'
                '            "warning",\n'
                '            "undecodable",\n'
                "        )"
            ),
            after=(
                "except CanonicalTextRefused:\n"
                "        return Unrecognized(\n"
                "            digest,\n"
                '            "intent-domain-unrecognized",\n'
                '            "warning",\n'
                '            "wrong-detail",\n'
                "        )"
            ),
        ),
        ("test_intent_gate.py::test_undecodable_bytes_read_undecodable",),
    ),
    Arm(
        "J4f",
        "the holdings discriminator accepts the boundary's Unicode payload",
        Sabotage(
            "intents/shapes.py",
            before='return DecodedIntent(digest, "holdings", decoded)',
            after='return DecodedIntent(digest, "assessment-run", decoded)',
        ),
        (
            "test_intent_gate.py::test_the_three_discriminators_are_exact_and_disjoint",
            "test_intent_gate.py::test_the_built_holdings_boundary_payload_decodes_unicode_included",
        ),
    ),
    Arm(
        "J5a",
        "settlement is never inferred from disk",
        Sabotage(
            "intents/reduce.py",
            before="committed = settlement.get(registration.digest)",
            after="committed = settlement.get(registration.digest, True)",
        ),
        (
            "test_intent_reduce.py::test_unsettled_pointer_is_unresolvable_regardless_of_disk",
            "test_world_log_evaluator.py::TestQualification::test_pending_exit_carries_qualification",
        ),
    ),
    Arm(
        "J5b",
        "a rolled-back registration is resolved and never qualifying",
        Sabotage(
            "intents/reduce.py",
            before=(
                "if not committed:\n"
                '            non_qualifying.append((registration.digest, "no-record"))\n'
                "            continue"
            ),
            after="if not committed:\n            pass",
        ),
        (
            "test_intent_reduce.py::test_rolled_back_only_pointers_read_attempt_without_recorded_outcome",
        ),
    ),
    Arm(
        "J6a",
        "qualification findings are appended last, inventory order",
        Sabotage(
            "world/verify.py",
            before="findings + qual_findings",
            after="qual_findings + findings",
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_qualification_findings_are_appended_last",
        ),
    ),
    Arm(
        "J6b",
        "a genesis-form malformed exit still carries qualification",
        Sabotage(
            "world/verify.py",
            before=(
                "return _report(\n"
                '            "malformed",\n'
                "            qualification=qualification,\n"
                "            bound=labels,\n"
                "            findings=tuple(findings) + (defect,),"
            ),
            after=(
                "return _report(\n"
                '            "malformed",\n'
                "            qualification=(),\n"
                "            bound=labels,\n"
                "            findings=tuple(findings) + (defect,),"
            ),
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_genesis_malformed_exit_carries_qualification",
        ),
    ),
    Arm(
        "J6c",
        "a structural MalformedView carries empty qualification",
        Sabotage(
            "world/verify.py",
            before=(
                'return _report("malformed", bound=labels, '
                "findings=tuple(findings) + (_defect_finding(view.defect),))"
            ),
            after=(
                "from beliefs.intents.reduce import IntentQualification\n"
                "        return _report(\n"
                '            "malformed",\n'
                "            qualification=(IntentQualification(view.defect.digest, None, "
                '"unrecognized", None),),\n'
                "            bound=labels,\n"
                "            findings=tuple(findings) + (_defect_finding(view.defect),),\n"
                "        )"
            ),
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_malformed_view_exit_carries_empty_qualification",
        ),
    ),
    Arm(
        "J6d",
        "intents_unevaluated is retired with no alias",
        Sabotage(
            "world/verify.py",
            before=(
                "qualification: tuple[IntentQualification, ...]\n"
                "    observer_bound: tuple[str, ...]"
            ),
            after=(
                "qualification: tuple[IntentQualification, ...]\n\n"
                "    @property\n"
                "    def intents_unevaluated(self) -> tuple[str, ...]:\n"
                "        return ()\n\n"
                "    observer_bound: tuple[str, ...]"
            ),
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_intents_unevaluated_is_retired_with_no_alias",
        ),
    ),
    Arm(
        "J6e",
        "qualification is total and follows intent chain order",
        Sabotage(
            "intents/reduce.py",
            before="for entry in entries:\n        if type(entry) is not IntentEntryView:",
            after="for entry in entries[:1]:\n        if type(entry) is not IntentEntryView:",
        ),
        (
            "test_world_log_evaluator.py::TestQualification::test_qualification_is_total_and_in_chain_order",
        ),
    ),
    Arm(
        "J6f",
        "unrecognized qualification rows carry no shape",
        Sabotage(
            "intents/reduce.py",
            before=(
                'rows.append(IntentQualification(entry.digest, None, "unrecognized", None))'
            ),
            after=(
                'rows.append(IntentQualification(entry.digest, "operation", "unrecognized", None))'
            ),
        ),
        (
            "test_intent_reduce.py::test_unrecognized_rows_carry_the_gate_finding_and_none_reduce",
        ),
    ),
    Arm(
        "J6g",
        "an unrecognized row never names a fulfiller",
        Sabotage(
            "intents/reduce.py",
            before=(
                'rows.append(IntentQualification(entry.digest, None, "unrecognized", None))'
            ),
            after=(
                'rows.append(IntentQualification(entry.digest, None, "unrecognized", "fabricated"))'
            ),
        ),
        (
            "test_intent_reduce.py::test_unrecognized_rows_carry_the_gate_finding_and_none_reduce",
        ),
    ),
    Arm(
        "J6h",
        "an unresolvable row never names a fulfiller",
        Sabotage(
            "intents/reduce.py",
            before=(
                'IntentQualification(intent.digest, intent.shape, "unresolvable", None)'
            ),
            after=(
                'IntentQualification(intent.digest, intent.shape, "unresolvable", "fabricated")'
            ),
        ),
        (
            "test_intent_reduce.py::test_unresolvable_wins_over_non_qualifying_and_emits_nothing",
        ),
    ),
    Arm(
        "J6i",
        "an unmatched row never names a fulfiller",
        Sabotage(
            "intents/reduce.py",
            before=(
                '"attempt-without-recorded-outcome",\n'
                "        None,\n"
                "    )"
            ),
            after=(
                '"attempt-without-recorded-outcome",\n'
                '        "fabricated",\n'
                "    )"
            ),
        ),
        ("test_intent_reduce.py::test_no_pointers_reads_attempt_without_recorded_outcome",),
    ),
    Arm(
        "J6j",
        "the attempt-without-recorded-outcome finding is a warning",
        Sabotage(
            "intents/reduce.py",
            before=(
                'severity="warning",\n'
                '            code="intent-attempt-without-recorded-outcome",'
            ),
            after=(
                'severity="error",\n'
                '            code="intent-attempt-without-recorded-outcome",'
            ),
        ),
        ("test_intent_reduce.py::test_no_pointers_reads_attempt_without_recorded_outcome",),
    ),
    Arm(
        "J6k",
        "each non-qualifying fulfillment finding is a warning",
        Sabotage(
            "intents/reduce.py",
            before=(
                'severity="warning",\n'
                '            code="intent-fulfillment-non-qualifying",'
            ),
            after=(
                'severity="error",\n'
                '            code="intent-fulfillment-non-qualifying",'
            ),
        ),
        (
            "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason",
        ),
    ),
    Arm(
        "J7a",
        "the terminal publication fulfills the boundary's own appended intent",
        Sabotage(
            "boundary.py",
            before=(
                'result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)\n'
                "    if type(result) is RunMinted:\n"
                "        _, _, plan = publication_plan(result.run)\n"
                "        port.execute_fulfilling(plan, fulfills)"
            ),
            after=(
                'result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)\n'
                "    if type(result) is RunMinted:\n"
                "        _, _, plan = publication_plan(result.run)\n"
                "        port.execute(plan)"
            ),
        ),
        ("test_run_persistence.py::test_assessment_sequence_appends_intent_then_publishes_fulfilling",),
    ),
    Arm(
        "J7b",
        "the production terminal publication fulfills its own appended intent",
        Sabotage(
            "boundary.py",
            before=(
                'result = _refused("recipe-identity-mismatch", "absent", actor, observer, started_at, intent)\n'
                "    if type(result) is RunMinted:\n"
                "        _, _, plan = publication_plan(result.run)\n"
                "        port.execute_fulfilling(plan, fulfills)"
            ),
            after=(
                'result = _refused("recipe-identity-mismatch", "absent", actor, observer, started_at, intent)\n'
                "    if type(result) is RunMinted:\n"
                "        _, _, plan = publication_plan(result.run)\n"
                "        port.execute(plan)"
            ),
        ),
        (
            "test_run_persistence.py::test_production_sequence_publishes_fulfilling_with_one_produces_edge",
        ),
    ),
    Arm(
        "J7c",
        "execute refuses a malformed plan as PlanRefusedError before any write",
        Sabotage(
            "root.py",
            before="validate_plan(plan)",
            after='raise ExecutionError("sabotaged malformed-plan mapping")',
        ),
        ("test_operation_port.py::test_execute_refuses_a_malformed_plan_before_any_write",),
    ),
    Arm(
        "J7d",
        "execute surfaces an encoder-valid execution failure as ExecutionError",
        Sabotage(
            "root.py",
            before=(
                "fulfills=None,\n"
                "        ).execute(plan)"
            ),
            after=(
                "fulfills=None,\n"
                "        )\n"
                "        return"
            ),
        ),
        ("test_operation_port.py::test_execute_surfaces_an_execution_failure_as_execution_error",),
    ),
    Arm(
        "J8a",
        "the view requires canonical reprojection equality",
        Sabotage(
            "runrecord.py",
            before=(
                'if _reproject(parsed) != parsed:\n        _refuse("$", '
                '"an array the projection sorts is out of its canonical order")'
            ),
            after=(
                'if False:\n        _refuse("$", '
                '"an array the projection sorts is out of its canonical order")'
            ),
        ),
        ("test_runrecord.py::test_reversed_result_pairs_fail_canonical_reprojection",),
    ),
    Arm(
        "J8b",
        "decode verifies the recomputed address against the record id",
        Sabotage("runrecord.py", before="if node.id != run_ref(address):", after="if False:"),
        ("test_runrecord.py::test_closure_member_mutation_diverges_from_the_id",),
    ),
    Arm(
        "J8c",
        "an incomplete canonical self-addressed projection fails the typed view",
        Sabotage(
            "runrecord.py",
            before='_mapping(parsed, {"recipe", "result", "occurrence"}, "$")',
            after="return parsed",
        ),
        ("test_runrecord.py::test_incomplete_closure_fails_the_view_not_the_codec",),
    ),
    Arm(
        "J8d",
        "Decimal canonical text stays injective through durable publication",
        Sabotage(
            "identity/v1.py",
            before=(
                'text = format(value, "f")  # never exponent notation\n'
                '    if "." not in text:\n'
                '        return text + ".0"  # a decimal always retains a fractional part\n'
                '    integer, fraction = text.split(".")\n'
                '    return f"{integer}.{fraction.rstrip(\'0\') or \'0\'}"'
            ),
            after='return format(value.normalize(), "f")',
        ),
        (
            "test_runrecord.py::test_decimal_wire_arms_project_decode_recompute",
            "acceptance/test_intent_boundary_acceptance.py::test_decimal_round_trip_publishes_and_captures",
        ),
    ),
    Arm(
        "J8e",
        "an assessment-shaped run never qualifies a production intent",
        Sabotage(
            "intents/shapes.py",
            before=(
                'if evidence.shape != "dataset-production":\n'
                '                    return "wrong-shape"'
            ),
            after='if False:\n                    return "wrong-shape"',
        ),
        ("test_intent_reduce.py::test_wrong_shape_both_directions",),
    ),
    Arm(
        "J8f",
        "a production-shaped run never qualifies an assessment intent",
        Sabotage(
            "intents/shapes.py",
            before='if evidence.shape != "assessment":\n                return "wrong-shape"',
            after='if False:\n                return "wrong-shape"',
        ),
        ("test_intent_reduce.py::test_wrong_shape_both_directions",),
    ),
    Arm(
        "J8g",
        "run input relations preserve every input role predicate",
        Sabotage(
            "stored.py",
            before=(
                "relations = [\n"
                "        Relation(source=node_id, predicate=predicate, target=target)\n"
                "        for predicate, targets in (\n"
                "            (OBSERVES, observes),\n"
                "            (READS, reads),\n"
                "            (TRANSFORMS, transforms),\n"
                "            (PRODUCES, produces),\n"
                "        )\n"
                "        for target in targets\n"
                "    ]\n"
                "    run_facet: dict[str, Any]"
            ),
            after=(
                "relations = [\n"
                "        Relation(source=node_id, predicate=PRODUCES, target=target)\n"
                "        for target in produces\n"
                "    ]\n"
                "    run_facet: dict[str, Any]"
            ),
        ),
        ("test_runrecord.py::test_relations_are_role_preserving",),
    ),
    Arm(
        "J8h",
        "a production run emits its one mint-derived produces edge",
        Sabotage(
            "runrecord.py",
            before="produces=(produces,) if produces is not None else (),",
            after="produces=(),",
        ),
        ("test_runrecord.py::test_relations_are_role_preserving",),
    ),
    Arm(
        "J8i",
        "v1.decode preserves integer and Decimal types",
        Sabotage(
            "identity/v1.py",
            before="parse_int=int,\n            parse_float=Decimal,",
            after="parse_int=Decimal,\n            parse_float=Decimal,",
        ),
        ("test_identity_decode.py::test_decode_preserves_types_int_and_decimal_are_distinct",),
    ),
    Arm(
        "J8j",
        "v1.decode wraps re-encoding identity refusals with their cause",
        Sabotage(
            "identity/v1.py",
            before=(
                "except IdentityError as caught:\n"
                "        raise CanonicalTextRefused(\n"
                '            f"re-encoding refused ({type(caught).__name__}): {caught}"\n'
                "        ) from caught"
            ),
            after="except IdentityError:\n        raise",
        ),
        ("test_identity_decode.py::test_decode_wraps_reencoding_identity_errors_cause_preserved",),
    ),
    Arm(
        "J9a",
        "the closure facet is semantic-hash covered",
        Sabotage(
            "stored.py",
            before='"run": (RUN_FACET, RUN_CLOSURE_FACET),',
            after='"run": (RUN_FACET,),',
        ),
        ("test_runrecord.py::test_closure_facet_is_semantic_hash_covered",),
    ),
    Arm(
        "J9b",
        "the run-facet shapes are exact, never .get()-based",
        Sabotage(
            "runrecord.py",
            before='if run_facet != {"spec": spec_identity}:',
            after='if run_facet.get("spec") != spec_identity:',
        ),
        ("test_runrecord.py::test_run_facet_shapes_are_exact_not_get_based",),
    ),
    Arm(
        "J9c",
        "the reader enforces run-facet and closure-shape agreement both ways",
        Sabotage(
            "runrecord.py",
            before=(
                'if shape == "assessment":\n'
                '        if run_facet != {"spec": spec_identity}:\n'
                "            raise MalformedRecord(\n"
                '                f"{node.id}: the run facet is exactly "\n'
                '                "{\'spec\': <the closure\'s spec>}"\n'
                "            )\n"
                "    elif run_facet != {}:\n"
                '        raise MalformedRecord(f"{node.id}: a production run facet is exactly {{}}")'
            ),
            after='if False:\n        raise MalformedRecord("run-facet agreement disabled")',
        ),
        ("test_runrecord.py::test_shape_agreement_both_ways",),
    ),
    Arm(
        "J10",
        "both ref spellings resolve to exactly the published record",
        Sabotage(
            "runrecord.py",
            before='return f"run:{address}"',
            after='return f"run-closure:{address}"',
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_bridge_resolves_assessment_ref_and_stamped_basis",
        ),
    ),
    Arm(
        "J11",
        "a legacy record reads through the run facet with no schema rejection",
        Sabotage(
            "runrecord.py",
            before="if facet is None:\n        return None",
            after=(
                'if facet is None:\n        raise MalformedRecord(f"{node.id}: '
                'a run record carries the closure facet")'
            ),
        ),
        (
            "test_runrecord.py::test_legacy_run_node_reads_and_never_qualifies",
            "test_intent_evidence.py::test_legacy_run_is_inert_not_undecodable",
        ),
    ),
    Arm(
        "J12a",
        "completion's predicate is the shared shape predicates",
        Sabotage(
            "report.py",
            before="if shapes.mismatch(decoded, evidence) is None:",
            after='if getattr(evidence, "event_token", None) == intent.event_token:',
        ),
        (
            "test_report.py::test_wrong_spec_run_closure_reads_unfinished",
            "test_report.py::test_assessment_shaped_closure_never_closes_a_production_intent",
            "test_consumer_agreement.py::test_run_shapes_agree_between_verifier_and_completion",
        ),
    ),
    Arm(
        "J12b",
        "the regenerated rule interior keeps the certified matrix answers",
        Sabotage(
            "holdings/qualify.py",
            before=(
                'if observation["location"] == intent["location"] and '
                'observation["event_token"] == intent["event_token"]:'
            ),
            after='if observation["location"] == intent["location"]:',
        ),
        (
            "test_consumer_agreement.py::test_holdings_matrix_agrees_across_both_consumers",
        ),
    ),
    Arm(
        "J13",
        "the reducer can match — every alternative reads matched",
        Sabotage(
            "intents/shapes.py",
            before='if type(evidence) is InertRecord:\n        return "wrong-purpose"',
            after='if True:\n        return "wrong-purpose"',
        ),
        (
            "acceptance/test_intent_boundary_acceptance.py::test_positive_matched_per_alternative",
            "test_intent_reduce.py::test_matched_by_run_publication_sets_fulfilled_by",
        ),
    ),
)

ATOMS_CITATIONS_BY_UNIT = {
    "L7u5": "atoms root-lease serialization, remote main 038513f",
}

CO_PASSING_INDEPENDENCE = {
    "J3a": ("test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling",),
}

_UNIT_OF_LETTERED = {
    "L7u2a": "L7u2",
    "L7u2b": "L7u2",
    "L7u2c": "L7u2",
    "L7u2d": "L7u2",
    "J3a": "J3",
    "J3b": "J3",
    "J1b": "J1",
    "J1c": "J1",
    "J1d": "J1",
    "J1e": "J1",
    "J1f": "J1",
    "J2a": "J2",
    "J2b": "J2",
    "J4a": "J4",
    "J4b": "J4",
    "J4c": "J4",
    "J4d": "J4",
    "J4e": "J4",
    "J4f": "J4",
    "J5a": "J5",
    "J5b": "J5",
    "J6a": "J6",
    "J6b": "J6",
    "J6c": "J6",
    "J6d": "J6",
    "J6e": "J6",
    "J6f": "J6",
    "J6g": "J6",
    "J6h": "J6",
    "J6i": "J6",
    "J6j": "J6",
    "J6k": "J6",
    "J7a": "J7",
    "J7b": "J7",
    "J7c": "J7",
    "J7d": "J7",
    "J8a": "J8",
    "J8b": "J8",
    "J8c": "J8",
    "J8d": "J8",
    "J8e": "J8",
    "J8f": "J8",
    "J8g": "J8",
    "J8h": "J8",
    "J8i": "J8",
    "J8j": "J8",
    "J9a": "J9",
    "J9b": "J9",
    "J9c": "J9",
    "J12a": "J12",
    "J12b": "J12",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"L7": 13}
LABELED_UNITS: tuple[str, ...] = tuple(f"J{number}" for number in range(1, 14))
