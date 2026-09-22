"""Frozen cut-38 declaration: twelve units, fourteen sabotage arms (T2-g homes three)."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "T2-e",
    "T2-f",
    "T2-g",
    "T2-h",
    "T2-i",
    "T2-j",
    "T5-d",
    "T6-d",
    "T6-e",
    "BI-1",
    "BI-2",
    "BI-3",
)
_MODULE = "acceptance/test_act_report_remainder_acceptance.py"
UNIT_CHECKS = {
    "T2-e": f"{_MODULE}::test_t2e_an_audit_closes_through_exactly_one_report_after_its_intent_and_the_evaluator_ran_between_durably",
    "T2-f": f"{_MODULE}::test_t2f_a_recheck_closes_through_one_report_and_its_operation_intent_precedes_every_holdings_intent_durably",
    "T2-g": f"{_MODULE}::test_t2g_root_selection_no_port_a_refused_append_and_a_foreign_store_begin_no_act_for_both_kinds_durably",
    "T2-h": f"{_MODULE}::test_t2h_each_kind_submits_exactly_one_fulfilling_execution_and_a_second_is_refused_durably",
    "T2-i": f"{_MODULE}::test_t2i_a_port_bound_to_another_root_is_refused_by_both_kinds_before_any_intent_durably",
    "T2-j": f"{_MODULE}::test_t2j_late_inputs_refuse_the_recheck_before_the_operation_intent_with_no_holdings_intent_and_no_read_durably",
    "T5-d": f"{_MODULE}::test_t5d_an_inconclusive_recheck_location_spells_untested_or_failed_by_whether_the_read_began_durably",
    "T6-d": f"{_MODULE}::test_t6d_cite_resolves_each_finding_in_evaluator_order_and_a_permutation_moves_the_identity_durably",
    "T6-e": f"{_MODULE}::test_t6e_findings_differing_only_in_message_mint_equal_entries_and_one_identity_under_a_fixed_envelope_durably",
    "BI-1": f"{_MODULE}::test_bi1_the_evaluator_modules_define_no_write_entry_point_and_reach_no_primitive_durably",
    "BI-2": f"{_MODULE}::test_bi2_the_evaluators_read_runs_under_the_root_lock_after_the_intent_so_a_raced_write_lands_after_the_report_durably",
    "BI-3": f"{_MODULE}::test_bi3_the_session_routes_write_one_act_line_per_committed_transaction_and_name_the_session_actor_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Numbered T2-g arms share their declaration unit."""
    unit = row[:-1] if row in ("T2-g1", "T2-g2", "T2-g3") else row
    if unit not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-38 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT38_ARMS = (
    _arm(
        'T2-e',
        "The audit's evaluator read happens after the operation intent, never before it.",
        'audit_operation.py',
        '        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '        # 4. Act: the read after the intent, so the chain position names the state judged.\n'
        '        writer._reconstruct()\n'
        '        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)',
        '        writer._reconstruct()\n'
        '        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)\n'
        '        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '        # 4. Act: the read after the intent, so the chain position names the state judged.',
    ),
    _arm(
        'T2-f',
        "The re-check's operation intent precedes every holdings intent its acts append.",
        'holdings/recheck.py',
        '    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '    # 3. Acts, in request order, nothing held across them.\n'
        '    entries: list[LocatorEntry] = []\n'
        '    results: list[ActResult] = []\n'
        '    published: list[str] = []\n'
        '    for location, canonical in zip(locations, canonicals, strict=True):\n'
        '        result = recheck(ctx, location, standing=heads.get(canonical, ()))\n'
        '        results.append(result)',
        '    intent_digest = None  # appended after the first act\n'
        '    # 3. Acts, in request order, nothing held across them.\n'
        '    entries: list[LocatorEntry] = []\n'
        '    results: list[ActResult] = []\n'
        '    published: list[str] = []\n'
        '    for location, canonical in zip(locations, canonicals, strict=True):\n'
        '        result = recheck(ctx, location, standing=heads.get(canonical, ()))\n'
        '        if intent_digest is None:\n'
        '            intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '        results.append(result)',
    ),
    _arm(
        'T2-g1',
        "A re-check whose writer is not the act context's observer root begins no act.",
        'holdings/recheck.py',
        '    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():\n'
        '        raise RecheckRefused("the writer\'s root is not the act context\'s observer root; a re-check publishes in one root")',
        "    pass  # the one-root check dropped: the intent lands in the writer's root while the acts publish in the observer's",
    ),
    _arm(
        'T2-g2',
        'An operation intent the port refuses ends the audit; no act follows it.',
        'audit_operation.py',
        '        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)',
        '        try:\n'
        '            intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '        except Exception:\n'
        '            intent_digest = "0" * 64  # the append failure swallowed; the acts proceed',
    ),
    _arm(
        'T2-g3',
        'A location naming a foreign store refuses the re-check before its intent.',
        'holdings/recheck.py',
        '    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))\n'
        '    for location in locations:\n'
        '        if location.store_id != store_id:\n'
        '            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")\n'
        '    # 2. Open.\n'
        '    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)\n'
        '    opened_at = _now()\n'
        '    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)',
        '    # 2. Open.\n'
        '    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)\n'
        '    opened_at = _now()\n'
        '    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))\n'
        '    for location in locations:\n'
        '        if location.store_id != store_id:\n'
        '            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")',
    ),
    _arm(
        'T2-h',
        'Each kind submits exactly one fulfilling execution under its intent.',
        'audit_operation.py',
        '        writer._publish_operation_report(report, intent_digest, port=port)\n'
        '    return AuditOutcome(',
        '        writer._publish_operation_report(report, intent_digest, port=port)\n'
        '        try:\n'
        '            writer._publish_operation_report(report, intent_digest, port=port)\n'
        '        except Exception:\n'
        '            pass  # a second close, its refusal swallowed\n'
        '    return AuditOutcome(',
    ),
    _arm(
        'T2-i',
        'A port bound to another root is refused by both kinds before any intent.',
        'corpus.py',
        '        if Path(port.root).resolve() != Path(self.root).resolve():\n'
        '            raise PortMismatch(',
        '        if False:\n'
        '            raise PortMismatch(',
    ),
    _arm(
        'T2-j',
        'Every late re-check input is checked before the operation intent.',
        'holdings/recheck.py',
        '    heads: dict[str, tuple[HoldingsObservation, ...]] = {} if standing is None else dict(standing)\n'
        '    for key, predecessors in heads.items():\n'
        '        if key not in canonicals:\n'
        '            raise RecheckRefused(f"{key}: standing names a location this re-check does not request")\n'
        '        if type(predecessors) is not tuple or any(\n'
        '            type(predecessor) is not HoldingsObservation or predecessor.location.canonical() != key for predecessor in predecessors\n'
        '        ):\n'
        '            raise RecheckRefused(f"{key}: standing holds only HoldingsObservation values at that canonical location")\n'
        '    ctx.authority.require("holdings", ("holdings-observation",))\n'
        '    ctx.authority.require("corpus-write", ("act-report",))\n'
        '    _require_identity_text(ctx.observer, "observer")\n'
        '    _require_identity_text(ctx.instrument, "instrument")\n'
        '    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():\n'
        '        raise RecheckRefused("the writer\'s root is not the act context\'s observer root; a re-check publishes in one root")\n'
        '    if port is None and writer._operation_port is None:\n'
        '        raise RecheckRefused("this corpus has no operation port; re-check is a boundary operation")\n'
        '    writer._require_bound_port(port)\n'
        '    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))\n'
        '    for location in locations:\n'
        '        if location.store_id != store_id:\n'
        '            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")\n'
        '    # 2. Open.\n'
        '    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)\n'
        '    opened_at = _now()\n'
        '    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)',
        '    heads: dict[str, tuple[HoldingsObservation, ...]] = {} if standing is None else dict(standing)\n'
        '    ctx.authority.require("holdings", ("holdings-observation",))\n'
        '    ctx.authority.require("corpus-write", ("act-report",))\n'
        '    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():\n'
        '        raise RecheckRefused("the writer\'s root is not the act context\'s observer root; a re-check publishes in one root")\n'
        '    if port is None and writer._operation_port is None:\n'
        '        raise RecheckRefused("this corpus has no operation port; re-check is a boundary operation")\n'
        '    writer._require_bound_port(port)\n'
        '    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))\n'
        '    for location in locations:\n'
        '        if location.store_id != store_id:\n'
        '            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")\n'
        '    # 2. Open.\n'
        '    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)\n'
        '    opened_at = _now()\n'
        '    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n'
        '    _require_identity_text(ctx.observer, "observer")\n'
        '    _require_identity_text(ctx.instrument, "instrument")\n'
        '    for key, predecessors in heads.items():\n'
        '        if key not in canonicals:\n'
        '            raise RecheckRefused(f"{key}: standing names a location this re-check does not request")\n'
        '        if type(predecessors) is not tuple or any(\n'
        '            type(predecessor) is not HoldingsObservation or predecessor.location.canonical() != key for predecessor in predecessors\n'
        '        ):\n'
        '            raise RecheckRefused(f"{key}: standing holds only HoldingsObservation values at that canonical location")',
    ),
    _arm(
        'T5-d',
        'An inconclusive re-check location carries its own locator entry.',
        'holdings/recheck.py',
        '            entries.append(LocatorEntry(canonical, outcome))\n'
        '            continue',
        '            continue  # the inconclusive location dropped from the entries',
    ),
    _arm(
        'T6-d',
        "The report carries one entry per finding in the evaluator's order.",
        'audit_operation.py',
        '        entries = tuple(_entry(finding) for finding in findings)',
        '        entries = tuple(_entry(finding) for finding in reversed(findings))',
    ),
    _arm(
        'T6-e',
        "A finding's `message` is normative for nothing the entry payload carries.",
        'audit_operation.py',
        '    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail}).decode("utf-8")',
        '    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail, "message": finding.message}).decode("utf-8")',
    ),
    _arm(
        'BI-1',
        'The evaluator reaches no write primitive.',
        'audit.py',
        '    findings = list(corpus_check(view, profile))\n'
        '    if any(f.code == "profile-mismatch" and f.detail in ("base", "malformed") for f in findings):',
        '    findings = list(corpus_check(view, profile))\n'
        '    view.executor.execute(())  # a write primitive reached from the evaluator\n'
        '    if any(f.code == "profile-mismatch" and f.detail in ("base", "malformed") for f in findings):',
    ),
    _arm(
        'BI-2',
        "The evaluator's read runs under the root lock the intent was appended in.",
        'audit_operation.py',
        '    outer = nullcontext() if hold is None else hold()\n'
        '    with outer, writer._operation:\n'
        '        # 3. Open.',
        '    outer = nullcontext() if hold is None else hold()\n'
        '    with outer, writer._operation:\n'
        '        pass  # the lock released before the evaluator call\n'
        '    if True:\n'
        '        # 3. Open.',
    ),
    _arm(
        'BI-3',
        "The session's audit route writes its act line through the ledgered port.",
        'session/writer.py',
        '            port=self.operation_port(), hold=self._closing_hold,\n'
        '        )\n'
        '\n'
        '    def recheck(',
        '            port=self._writer._operation_port, hold=self._closing_hold,\n'
        '        )\n'
        '\n'
        '    def recheck(',
    ),
)
