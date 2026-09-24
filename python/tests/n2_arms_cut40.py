"""Frozen cut-40 declaration: fifteen units, fifteen sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Y5-a",
    "Y5-b",
    "Y6-a",
    "Y6-b",
    "Y7-a",
    "Y7-b",
    "Y8-a",
    "Y8-b",
    "Y9-a",
    "Y9-b",
    "Y9-c",
    "Y9-d",
    "Y9-e",
    "Y10-a",
    "Y10-b",
)
_MODULE = "acceptance/test_publish_act_acceptance.py"
UNIT_CHECKS = {
    "Y5-a": f"{_MODULE}::test_y5_a_every_step_0_refusal_writes_nothing_durably",
    "Y5-b": f"{_MODULE}::test_y5_b_a_view_revised_between_evaluation_and_lock_refuses_durably",
    "Y6-a": f"{_MODULE}::test_y6_a_the_selection_is_fixed_before_the_intent_and_a_drift_after_it_strands_nothing_durably",
    "Y6-b": f"{_MODULE}::test_y6_b_a_rewritten_snapshot_is_request_corrupt_durably",
    "Y7-a": f"{_MODULE}::test_y7_a_a_crash_after_k_staged_records_resumes_at_k_plus_one_durably",
    "Y7-b": f"{_MODULE}::test_y7_b_an_extra_staged_record_is_staging_corrupt_and_staging_is_retained_durably",
    "Y8-a": f"{_MODULE}::test_y8_a_a_publication_lands_at_its_corpus_id_and_a_second_lands_beside_it_durably",
    "Y8-b": f"{_MODULE}::test_y8_b_a_colliding_sibling_is_export_collision_and_binds_nothing_durably",
    "Y9-a": f"{_MODULE}::test_y9_a_a_crash_at_every_local_step_resumes_to_one_binding_and_one_report_durably",
    "Y9-b": f"{_MODULE}::test_y9_b_a_binding_beside_an_unfinished_intent_is_unresolved_durably",
    "Y9-c": f"{_MODULE}::test_y9_c_pending_lists_crashed_attempts_only_durably",
    "Y9-d": f"{_MODULE}::test_y9_d_a_crash_inside_step_9_is_finished_by_the_resume_durably",
    "Y9-e": f"{_MODULE}::test_y9_e_the_next_publish_reads_success_and_pre_binding_reports_durably",
    "Y10-a": f"{_MODULE}::test_y10_a_a_second_world_admits_a_publication_and_nothing_without_a_marker_durably",
    "Y10-b": f"{_MODULE}::test_y10_b_a_verified_root_with_records_beyond_its_selection_is_refused_before_admission_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-40 row")
    return row


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT40_ARMS = (
    _arm(
        "Y5-a",
        "Every step-0 refusal writes nothing, so the closure reads both endpoints of a relation and a missing source refuses before any intent.",
        "publish_request.py",
        "            for endpoint in (relation.source, relation.target):",
        "            for endpoint in (relation.target,):",
    ),
    _arm(
        "Y5-b",
        "A view revised between evaluation and lock refuses `view-revised` and appends nothing, because `_open_publication` re-checks `expected_view`.",
        "publication_doors.py",
        "        if expected_view is not None and view.unpinned().pinned(resolved.uid) != expected_view:",
        "        if False:",
    ),
    _arm(
        "Y6-a",
        "A retry never selects differently: the snapshot holds the step-0 evaluation, so a corpus that drifts after the intent does not strand the retry.",
        "publish.py",
        "    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)\n"
        "    _require_snapshot_records(read, records)\n"
        "    opened = _open_publication(\n"
        "        writer, resolver, view=view.unpinned(), destination=destination, clock=clock, seam=seam, port=port, expected_view=pinned,\n"
        "    )",
        "    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)\n"
        "    _require_snapshot_records(read, records)\n"
        "    opened = _open_publication(\n"
        "        writer, resolver, view=view.unpinned(), destination=destination, clock=clock, seam=seam, port=port, expected_view=pinned,\n"
        "    )\n"
        "    records = tuple((address, node_to_markdown(open_world_view(world, current_epoch(world)).get(address))) for address in evaluate_query(open_world_view(world, current_epoch(world)), query).selected)",
    ),
    _arm(
        "Y6-b",
        "A snapshot that disagrees with its request or intent is `request-corrupt`, reported and terminal, because the retry checks the snapshot's identity.",
        "publish.py",
        "    if snapshot.identity() != request.selection or snapshot.event_token != intent.event_token:",
        "    if False:",
    ),
    _arm(
        "Y7-a",
        "Staging resumes from its true prefix, so a crash after k staged records resumes at record k + 1 rather than record 1.",
        "publish.py",
        "    return _Population(n, complete=False)",
        "    return _Population(0, complete=False)",
    ),
    _arm(
        "Y7-b",
        "A record in staging outside the snapshot is `staging-corrupt`, reported alone with staging retained.",
        "publish.py",
        "    if extras:",
        "    if False:",
    ),
    _arm(
        "Y8-a",
        "The local reveal lands at `<destination>/<corpus_id>`, so a second publication to the same destination lands beside the first.",
        "publish.py",
        "    return Path(a.request.destination.locator) / corpus_id",
        "    return Path(a.request.destination.locator)",
    ),
    _arm(
        "Y8-b",
        "The head-artifact sibling is written create-only, so a colliding sibling is `export-collision` and binds nothing.",
        "publish.py",
        "        write_create_only(sibling, artifact)",
        "        sibling.write_bytes(artifact)",
    ),
    _arm(
        "Y9-a",
        "The terminal report carries the attempt's lifecycle entries in step order.",
        "publish.py",
        "        lifecycle=entries,",
        "        lifecycle=(),",
    ),
    _arm(
        "Y9-b",
        "A binding beside an unfinished intent is `binding-without-report` and fails closed with nothing written, never read as done.",
        "publish.py",
        '        return PublishUnresolved(event_token, "binding-without-report")',
        "        pass",
    ),
    _arm(
        "Y9-c",
        "`pending_publishes` lists only unfinished attempts, omitting a done one.",
        "publish.py",
        '        if reading is not None and reading.reading == "unfinished":',
        "        if reading is not None:",
    ),
    _arm(
        "Y9-d",
        "A done attempt's resume finishes step 9 by discarding staging before answering `Published`.",
        "publish.py",
        "        _discard(op)",
        "        pass",
    ),
    _arm(
        "Y9-e",
        "The next publish's step-0 fold reads every terminal report, successful or refused, not only a single-entry binding report.",
        "publication_doors.py",
        "        if type(entries[-1]) is not PublicationBindingEntry:\n            yield intent, PreBinding(",
        "        if len(entries) != 1:\n"
        '            yield intent, PositionRefused("revision-malformed", "not a publish report")\n'
        "            continue\n"
        "        if type(entries[-1]) is not PublicationBindingEntry:\n"
        "            yield intent, PreBinding(",
    ),
    _arm(
        "Y10-a",
        "`admit_publication` refuses a root with no marker `marker-absent` before any write.",
        "publication_arrival.py",
        '    if not markers:\n        raise PublicationArrivalRefused("marker-absent")',
        '    if False:\n        raise PublicationArrivalRefused("marker-absent")',
    ),
    _arm(
        "Y10-b",
        "`admit_publication` refuses records other than the marker's selection, in both directions, before any write.",
        "publication_arrival.py",
        "    if held != selection:",
        "    if not set(selection) <= set(held):",
    ),
)
