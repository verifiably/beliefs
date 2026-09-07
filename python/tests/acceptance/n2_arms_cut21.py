"""Cut 21's eight frozen declaration units and their source sabotages
(docs/designs/2026-09-06-conformance-cut-21.md §3, §5 item 4), one arm per
frozen sabotage. `V5a` keeps the refusal and appends an intent before it,
inside `_refuse_verification` — the after-intent ordering as one replacement."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

_VERIFY, _STORED, _AUDIT, _CORPUS, _SPEC, _ADMISSION, _EVALUATION = (
    "verify.py", "stored.py", "audit.py", "corpus.py", "spec.py", "admission.py", "evaluation.py",
)
_TV, _TS, _TAD, _TA, _TI, _TO, _TSP, _TID, _TVP, _TCW, _ACC = (
    "test_verify.py", "test_stored.py", "test_admission.py", "test_audit.py", "test_import_derivation.py",
    "test_operation_writes.py", "test_spec.py", "test_verification_identity.py",
    "test_verification_publication.py", "test_corpus_write.py", "acceptance/test_verification_acceptance.py",
)

DECLARATION_UNITS = tuple(f"V{n}" for n in range(1, 9))
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


CUT21_ARMS = (
    # --- verify.py -----------------------------------------------------------
    Arm("V1a", "drop report from the projection",
        Sabotage(_VERIFY, '        "report": derived.report.projection(),\n', '        "report": {},\n'),
        (f"{_TV}::test_v1_publication_node_round_trips_through_the_reader", f"{_ACC}::test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone")),
    Arm("V1b", "skip the identity recomputation in decode_verification",
        Sabotage(_VERIFY, '    if decoded.identity() != stored.local_id("verification", node.id):\n', "    if False:\n"),
        (f"{_TV}::test_v5_a_record_id_that_does_not_recompute_is_malformed",)),
    Arm("V6a", "accept a projection with a missing key",
        Sabotage(_VERIFY, "    if not isinstance(member, Mapping) or not _REPORT_REQUIRED <= set(member) <= _REPORT_REQUIRED | _REPORT_OPTIONAL:\n", "    if not isinstance(member, Mapping):\n"),
        (f"{_TV}::test_v6_a_present_but_malformed_report_or_member_is_refused[<lambda>0]",)),
    Arm("V7a", "write assessment for the production shape",
        Sabotage(_VERIFY, '    if type(derived) is AssessmentVerification:\n        facet["assessment"] = derived.assessment\n', '    facet["assessment"] = getattr(derived, "assessment", "")\n'),
        (f"{_TV}::test_v7_the_production_shape_publishes_edge_less_and_admits_nothing",)),
    Arm("V2e", "compute the assessment digest over the typed ref",
        Sabotage(_VERIFY, '            {"spec": spec.identity, "run": original.address(), "proposition": spec.target},\n', '            {"spec": spec.identity, "run": stored.typed_ref("run", original.address()), "proposition": spec.target},\n'),
        (f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean",)),
    Arm("V3a", "publish a superseding verification without its predecessor",
        Sabotage(_VERIFY, '        facet["supersedes"] = stored.typed_ref("verification", derived.supersedes)\n', "        pass\n"),
        (f"{_TV}::test_v3_a_superseding_verification_publishes_its_typed_predecessor", f"{_TVP}::test_v3_a_superseding_failed_verification_invalidates_and_retires_its_predecessor")),
    # --- stored.py -----------------------------------------------------------
    Arm("V2a", "return the typed ref from assessment_value",
        Sabotage(_STORED, '        run=local_id("run", facet.get("run")),  # type: ignore[arg-type]\n', '        run=str(facet.get("run", "")),\n'),
        (f"{_TS}::test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one", f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean")),
    Arm("V2f", "strip nothing in local_id",
        Sabotage(_STORED, "    return ref[len(prefix):]\n", "    return ref\n"),
        (f"{_TS}::test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref",)),
    Arm("V8d", "skip the identity check in analysis_spec_value",
        Sabotage(_STORED, '    if node.id != typed_ref("analysis-spec", spec.identity):\n', "    if False:\n"),
        (f"{_TS}::test_v8_a_renamed_or_falsely_identified_record_is_malformed",)),
    # --- admission.py / evaluation.py ----------------------------------------
    Arm("V2b", "compare run.ref to the bare address",
        Sabotage(_ADMISSION, '    if run.ref != typed_ref("run", assessment.run):\n', "    if run.ref != assessment.run:\n"),
        (f"{_TAD}::test_v2_admit_matches_a_typed_run_ref_to_the_bare_member",)),
    Arm("V2c", "resolve a.run untyped",
        Sabotage(_EVALUATION, '        ref = stored.typed_ref("run", a.run)\n', "        ref = a.run\n"),
        (f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean",)),
    # --- audit.py ------------------------------------------------------------
    Arm("V4a", "skip the scope comparison",
        Sabotage(_AUDIT, "        if decoded.scope != derived.scope:\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[scope]",)),
    Arm("V4b", "skip the report comparison",
        Sabotage(_AUDIT, "        if decoded.report.identity() != derived.report.identity():\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[report-receipt]",)),
    Arm("V4c", "take certification=None for a decoded report",
        Sabotage(_AUDIT, "    certification = None if decoded is None else decoded.report.certification\n", "    certification = None\n"),
        (f"{_TA}::test_v4_a_certified_verification_audits_clean_through_its_stored_certification",)),
    Arm("V2g", "compare stored_value.run through run_ref again",
        Sabotage(_AUDIT, "    if stored_value.run != derived.run:\n", '    if stored_value.run != "run:" + derived.run:\n'),
        (f"{_TA}::test_v4_a_published_verification_audits_checked_with_no_contradiction",)),
    Arm("V2d", "resolve the assessment's run bare",
        Sabotage(_AUDIT, '    closure, why = _closure(view, stored.typed_ref("run", stored_value.run))\n', "    closure, why = _closure(view, stored_value.run)\n"),
        (f"{_TA}::test_v2_a_contradicted_assessment_still_contradicts",)),
    Arm("V8e", "drop the analysis-spec branch",
        Sabotage(_AUDIT, '            elif node.kind == "analysis-spec":\n                outcome = check_analysis_spec(node)\n', "            elif False:\n                continue\n"),
        (f"{_TA}::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it",)),
    Arm("V8c", "let stored_specs return the mapping alone",
        Sabotage(_AUDIT, "            spec = stored.analysis_spec_value(node)\n        except RecordError as refused:\n", "            spec = stored.analysis_spec_value(node)\n        except RecordError:\n            continue\n"),
        (f"{_TA}::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it",)),
    # --- corpus.py -----------------------------------------------------------
    Arm("V5a", "the verification refusal lands after an intent is appended",
        Sabotage(_CORPUS, "        decoded = decode_verification(node)  # MalformedRecord propagates: refuse, never repair\n",
                 '        port = self._operation_port\n        assert port is not None\n        port.append_intent(_encode_operation_intent("corpus-write", "sabotage", self.authority.actor))\n        decoded = decode_verification(node)  # MalformedRecord propagates: refuse, never repair\n'),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent", f"{_ACC}::test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent")),
    Arm("V5b", "return before the target check",
        Sabotage(_CORPUS, "        if identity != decoded.assessment:\n", "        if False:\n"),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent",)),
    Arm("V5c", "resolve the target in self._view instead of the union for import",
        Sabotage(_CORPUS, "            self._refuse_verification(node, view=self._view if view is None else view)\n", "            self._refuse_verification(node, view=self._view)\n"),
        (f"{_TI}::test_v5_every_forgery_refuses_the_bundle_and_the_well_formed_record_imports",)),
    Arm("V8f", "skip _refuse's spec restoration",
        Sabotage(_CORPUS, '        if node.kind == "analysis-spec":\n            self._refuse_r20_contradiction(node)\n', "        pass\n"),
        (f"{_TCW}::test_v8_a_spec_record_whose_identity_is_false_is_refused_at_add", f"{_TI}::test_v8_a_spec_record_whose_identity_is_false_refuses_the_bundle")),
    # --- spec.py -------------------------------------------------------------
    Arm("V8a", "skip restore's identity check",
        Sabotage(_SPEC, "    if v1.digest(SPEC_DOMAIN, mapping) != identity:\n", "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_a_projection_that_does_not_digest_to_the_identity[<lambda>0]", f"{_TS}::test_v8_a_renamed_or_falsely_identified_record_is_malformed")),
    Arm("V8b", "skip the unfreezable check in restore",
        Sabotage(_SPEC, '    if isinstance(nondeterminism, StochasticUnseeded) and text["equivalence_rule"] in BITWISE_EQUIVALENCE_RULES:\n', "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair",)),
    Arm("V8g", "decode with a float parser",
        Sabotage(_SPEC, "        mapping = v1.decode(projection)\n", '        mapping = __import__("json").loads(projection)\n'),
        (f"{_TSP}::test_v8_restore_round_trips_every_member_and_the_decimal_by_type",)),
)
