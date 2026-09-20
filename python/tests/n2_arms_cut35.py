"""Frozen cut-35 declaration: twenty-seven units, twenty-eight sabotage arms (BI-11 homes two)."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "H4-a",
    "H4-b",
    "G9-a",
    "R10-a",
    "T5-a",
    "T5-b",
    "T5-c",
    "T7-a",
    "T7-b",
    "T1-a",
    "T2-a",
    "T2-b",
    "T2-c",
    "T2-d",
    "T4-a",
    "T4-b",
    "BI-1",
    "BI-2",
    "BI-3",
    "BI-4",
    "BI-5",
    "BI-6",
    "BI-7",
    "BI-8",
    "BI-9",
    "BI-10",
    "BI-11",
)
_MODULE = "acceptance/test_url_retrieval_acceptance.py"
UNIT_CHECKS = {
    "H4-a": f"{_MODULE}::test_h4a_an_established_remote_found_publishes_or_the_look_raises",
    "H4-b": f"{_MODULE}::test_h4b_an_inconclusive_remote_attempt_mints_nothing_and_never_absent",
    "G9-a": f"{_MODULE}::test_g9a_a_url_location_holds_without_a_store_copy",
    "R10-a": f"{_MODULE}::test_r10a_the_acquisition_records_dataset_provenance",
    "T5-a": f"{_MODULE}::test_t5a_a_began_request_never_spells_untested",
    "T5-b": f"{_MODULE}::test_t5b_a_preflight_refusal_and_a_post_stop_skip_spell_distinct_reasons",
    "T5-c": f"{_MODULE}::test_t5c_no_entry_outcome_constructs_an_observation",
    "T7-a": f"{_MODULE}::test_t7a_the_dataset_and_its_report_publish_in_one_transaction_in_one_root",
    "T7-b": f"{_MODULE}::test_t7b_the_address_is_unchanged_while_the_record_bytes_move",
    "T1-a": f"{_MODULE}::test_t1a_a_raw_written_report_is_undetected_on_read_and_refuted_under_anchors",
    "T2-a": f"{_MODULE}::test_t2a_an_acquisition_closes_through_exactly_one_report_after_its_intent",
    "T2-b": f"{_MODULE}::test_t2b_root_selection_failure_begins_no_act",
    "T2-c": f"{_MODULE}::test_t2c_intent_append_failure_begins_no_act",
    "T2-d": f"{_MODULE}::test_t2d_a_second_fulfillment_is_refused_and_a_raw_one_is_malformed",
    "T4-a": f"{_MODULE}::test_t4a_reports_leave_the_projection_unchanged_and_an_unfinished_operation_blocks_nothing",
    "T4-b": f"{_MODULE}::test_t4b_deleting_a_referenced_observation_moves_the_active_set_and_not_the_report",
    "BI-1": f"{_MODULE}::test_bi1_two_spellings_of_one_url_are_one_location",
    "BI-2": f"{_MODULE}::test_bi2_no_hop_bytes_enter_any_record_or_reason",
    "BI-3": f"{_MODULE}::test_bi3_the_pinned_connection_dials_the_validated_address",
    "BI-4": f"{_MODULE}::test_bi4_the_ceiling_finalizes_no_digest",
    "BI-5": f"{_MODULE}::test_bi5_an_expectation_mismatch_mints_no_dataset_and_reports_mismatch",
    "BI-6": f"{_MODULE}::test_bi6_an_already_held_address_mints_no_second_dataset",
    "BI-7": f"{_MODULE}::test_bi7_the_url_looks_intent_blocks_nothing",
    "BI-8": f"{_MODULE}::test_bi8_no_lock_is_held_across_the_request",
    "BI-9": f"{_MODULE}::test_bi9_the_successor_rule_keeps_old_receipts_validatable",
    "BI-10": f"{_MODULE}::test_bi10_url_intents_and_observations_decode_and_reconcile",
    "BI-11": f"{_MODULE}::test_bi11_the_materialization_classification",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Each row is one declared unit; BI-11's two lettered arms share its unit."""
    unit = row[:-1] if row[-1:] in ("a", "b") and row[:-1] == "BI-11" else row
    if unit not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-35 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


_OBSERVED_AT = 'datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")'

CUT35_ARMS = (
    _arm(
        "H4-a",
        "An established remote found publishes; a publication failure after Retrieved raises and leaves the re-check intent unmatched, never a transient report.",
        "holdings/boundary.py",
        "    except BaseException:\n"
        "        result.path.unlink(missing_ok=True)  # ownership never reached the caller\n"
        "        raise",
        "    except BaseException as caught:\n"
        "        result.path.unlink(missing_ok=True)  # ownership never reached the caller\n"
        "        if isinstance(caught, ExecutionError):\n"
        '            return InconclusiveLook("retrieval-failed", str(caught))\n'
        "        raise",
    ),
    _arm(
        "H4-b",
        "An inconclusive remote attempt mints nothing and never absent; the standing observation's identity is unchanged.",
        "holdings/boundary.py",
        "    if isinstance(result, NotAttempted):\n"
        '        return InconclusiveLook("byte-locator-untested", result.reason)',
        "    if isinstance(result, NotAttempted):\n"
        "        _publish_record(ctx, holdings_observation(location=location, outcome=Found(\"sha256:\" + \"0\" * 64), expected=expected, observer=ctx.observer, instrument=ctx.instrument, event_token=token, observed_at="
        + _OBSERVED_AT
        + ", supersedes=standing), intent)\n"
        '        return InconclusiveLook("byte-locator-untested", result.reason)',
    ),
    _arm(
        "G9-a",
        "A URL location with a found observation and no store copy holds.",
        "holdings/adapter.py",
        "        if (found := _joined(member, declared)) is not None",
        '        if not cast(str, member["location"]).startswith("url:") and (found := _joined(member, declared)) is not None',
    ),
    _arm(
        "R10-a",
        "The minted dataset's facet names the acquisition report through retrieval.",
        "holdings/acquire.py",
        '                empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": report_node.id},',
        '                empirical_observation={"locator": request.locator, "attested_by": ctx.actor},',
    ),
    _arm(
        "T5-a",
        "A failed retrieval after the request began spells retrieval-failed, never byte-locator-untested.",
        "holdings/boundary.py",
        '        return InconclusiveLook("retrieval-failed", result.reason)',
        '        return InconclusiveLook("byte-locator-untested", result.reason)',
    ),
    _arm(
        "T5-b",
        "A preflight refusal and a post-stop skip spell byte-locator-untested with distinct reasons.",
        "holdings/acquire.py",
        "            entries.append(LocatorEntry(subject, ByteLocatorUntested(SKIPPED_AFTER_STOP), inputs))",
        "            entries.append(LocatorEntry(subject, ByteLocatorUntested(stop.reason), inputs))",
    ),
    _arm(
        "T5-c",
        "The close refuses a report whose published-observation ref resolves to no observation an act published.",
        "holdings/acquire.py",
        "        for ref in sorted(published):\n"
        "            if writer.read_view.resolve(ref) is None:",
        "        for ref in ():\n"
        "            if writer.read_view.resolve(ref) is None:",
    ),
    _arm(
        "T7-a",
        "The dataset and its report publish in one registered transaction in one root.",
        "holdings/acquire.py",
        "            writer._refuse_acquired_dataset(dataset, report_node)\n"
        "            operations.append(writer._create_op(dataset))",
        "            writer._refuse_acquired_dataset(dataset, report_node)\n"
        "            (writer._operation_port if port is None else port).execute([writer._create_op(dataset)])",
    ),
    _arm(
        "T7-b",
        "The dataset address excludes provenance: two acquisitions of one byte set share an id while their record bytes differ.",
        "stored.py",
        '    return _node("dataset", address.partition(":")[2], title, facets, ())',
        '    return _node("dataset", address.partition(":")[2] + ("-" + str(empirical_observation.get("retrieval"))[-8:] if empirical_observation is not None and "retrieval" in empirical_observation else ""), title, facets, ())',
    ),
    _arm(
        "T1-a",
        "A raw-written self-consistent report is inside the corpus surface: log verification under an anchored observer set refutes it.",
        "world/verify.py",
        "def _claimed_by_the_corpus_layout(path: str) -> bool:\n"
        "    return path == CORPUS_MANIFEST or path.endswith(RECORD_SUFFIX)",
        "def _claimed_by_the_corpus_layout(path: str) -> bool:\n"
        '    return (path == CORPUS_MANIFEST or path.endswith(RECORD_SUFFIX)) and not path.startswith("act-report/")',
    ),
    _arm(
        "T2-a",
        "No act precedes the operation intent: the intent's chain position is below every look and registration.",
        "holdings/acquire.py",
        "    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)",
        "    look(ctx, request.resources[0].url, bounds=request.bounds, seam=seam, scratch=scratch)\n"
        "    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)",
    ),
    _arm(
        "T2-b",
        "A port-less writer refuses before the intent: no request, no intent, no record.",
        "holdings/acquire.py",
        "    if port is None and writer._operation_port is None:\n"
        '        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")',
        "    if False:\n"
        '        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")',
    ),
    _arm(
        "T2-c",
        "An intent append the port refuses begins no act: no request issued.",
        "corpus.py",
        "        digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))",
        "        try:\n"
        "            digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))\n"
        "        except ExecutionError:\n"
        '            digest = "0" * 64',
    ),
    _arm(
        "T2-d",
        "A raw second fulfillment of the operation intent reads malformed with kind duplicate-fulfillment.",
        "root.py",
        '    DefectKind.DUPLICATE_FULFILLMENT: "duplicate-fulfillment",',
        '    DefectKind.DUPLICATE_FULFILLMENT: "fulfills-invalid",',
    ),
    _arm(
        "T4-a",
        "An unmatched acquisition operation intent blocks nothing in the reduction.",
        "holdings/qualify.py",
        '    if not isinstance(value, dict) or value.get("domain") != HOLDINGS_INTENT_DOMAIN:\n'
        "        return None",
        '    if not isinstance(value, dict) or value.get("domain") != HOLDINGS_INTENT_DOMAIN:\n'
        '        return {"digest": row["digest"], "actor": "x", "event_token": str((value or {}).get("event_token", "")) if isinstance(value, dict) else "", "kind": "write", "location": "url:https://sabotage.example/"}',
    ),
    _arm(
        "T4-b",
        "A report confers no protection on the observation it references: after the removal the active set moves and the rule reads no report.",
        "holdings/rules_v1/holdings.py",
        "    _check_walks(by_location, observations)",
        '    for corpus in capture["corpora"]:\n'
        '        for row in corpus["records"]:\n'
        '            document = json.loads(row["canonical"])\n'
        '            if document.get("kind") != "act-report":\n'
        "                continue\n"
        '            for entry in document["facets"]["act-report"]["entries"]:\n'
        '                outcome = entry.get("outcome") or {}\n'
        '                ref = str(outcome.get("ref", "")).split(":", 1)[-1]\n'
        '                if "ref" in outcome and ref and ref not in observations:\n'
        '                    value = {"ref": ref, "path": "holdings-observation/" + ref + ".md", "location": entry["subject"], "outcome": {"finding": "found", "digest": "sha256:" + "0" * 64}, "expected": None, "event_token": "", "supersedes": ()}\n'
        "                    observations[ref] = value\n"
        '                    canonical_by_ref[ref] = row["canonical"]\n'
        '                    by_location.setdefault(value["location"], []).append(value)\n'
        "    _check_walks(by_location, observations)",
    ),
    _arm(
        "BI-1",
        "Two spellings of one URL are one location: the default port is elided.",
        "holdings/records.py",
        '    authority = host if port in (None, _DEFAULT_PORTS[scheme]) else f"{host}:{port}"',
        '    authority = host if port is None else f"{host}:{port}"',
    ),
    _arm(
        "BI-2",
        "A refused hop is named by ordinal and category, never by its host.",
        "holdings/transport.py",
        '            return Failed(f"redirect hop {hop} refused: {decision.category}")',
        '            return Failed(f"redirect hop {hop} to {urlsplit(current).hostname} refused: {decision.category}")',
    ),
    _arm(
        "BI-3",
        "The pinned connection dials the validated address, not the host name.",
        "holdings/transport.py",
        "        sock = socket.create_connection((self._address, self.port), self.timeout)",
        "        sock = socket.create_connection((self.host, self.port), self.timeout)",
    ),
    _arm(
        "BI-4",
        "The ceiling ends the stream and finalizes no digest.",
        "holdings/transport.py",
        "            if size > bounds.max_bytes:\n"
        '                return Failed(f"exceeded the {bounds.max_bytes}-byte streaming ceiling")',
        "            if size > bounds.max_bytes:\n"
        '                return Retrieved(digest=f"sha256:{hasher.hexdigest()}", size=size, path=target)',
    ),
    _arm(
        "BI-5",
        "An expectation mismatch mints no dataset.",
        "holdings/acquire.py",
        "    expectations_hold = all(r.expected is None or digests.get(r.name) == r.expected for r in request.resources)",
        "    expectations_hold = True",
    ),
    _arm(
        "BI-6",
        "An already-held address mints no second dataset and keeps its retrieval.",
        "holdings/acquire.py",
        "        held = address is not None and writer.read_view.resolve(address) is not None",
        "        held = False",
    ),
    _arm(
        "BI-7",
        "The URL look's intent is a re-check: unmatched, it blocks nothing.",
        "holdings/boundary.py",
        '    token, intent = _append(ctx, location, "re-check")\n'
        "    result = retrieve(location, bounds, seam, scratch)",
        '    token, intent = _append(ctx, location, "write")\n'
        "    result = retrieve(location, bounds, seam, scratch)",
    ),
    _arm(
        "BI-8",
        "No lock is held across the request.",
        "holdings/acquire.py",
        "        result = look(\n"
        "            ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch,\n"
        "            expected=resource.expected, standing=heads.get(subject) or (),\n"
        "        )",
        "        with writer._operation:\n"
        "            result = look(ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch, expected=resource.expected, standing=heads.get(subject) or ())",
    ),
    _arm(
        "BI-9",
        "The successor rule decodes the url arm; the generated copy is what the bundle reads.",
        "holdings/qualify.py",
        '    if value["type"] == "url":\n'
        '        if set(value) != {"type", "url"} or not _url(value["url"]):\n'
        "            return None\n"
        '        return "url:" + value["url"]',
        '    if value["type"] == "url":\n'
        "        return None",
    ),
    _arm(
        "BI-10",
        "A URL observation decodes to evidence at its canonical location key.",
        "intents/evidence.py",
        "        return ObservationEvidence(\n"
        "            value.location.canonical(),\n"
        "            value.event_token,\n"
        "        )",
        "        return ObservationEvidence(\n"
        '            f"store:{value.location.store_id}:{value.location.relative_path}",\n'
        "            value.event_token,\n"
        "        )",
    ),
    _arm(
        "BI-11a",
        "The store-refusal wrap covers the store write's phase only: a publication failure after a committed materialization propagates.",
        "holdings/boundary.py",
        "    try:\n"
        "        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content)\n"
        "    except ExecutionError as caught:\n"
        "        if ctx.seam.store_refusal(caught):\n"
        "            raise StoreWriteRefused(location.canonical(), str(caught)) from caught\n"
        "        raise\n"
        "    state = _final(outcome, location.relative_path)",
        "    try:\n"
        "        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content)\n"
        "        state = _final(outcome, location.relative_path)\n"
        "        if isinstance(state, FileStateView):\n"
        "            return _publish_record(ctx, holdings_observation(location=location, outcome=Found(state.content_hash), expected=expected, observer=ctx.observer, instrument=ctx.instrument, event_token=token, observed_at="
        + _OBSERVED_AT
        + ", supersedes=standing), intent)\n"
        "    except ExecutionError as caught:\n"
        "        if ctx.seam.store_refusal(caught):\n"
        "            raise StoreWriteRefused(location.canonical(), str(caught)) from caught\n"
        "        raise",
    ),
    _arm(
        "BI-11b",
        "The store-refusal predicate is true for exactly the routine causes: an unexpected engine failure propagates and is never a stop.",
        "root.py",
        "    return isinstance(caught, ExecutionError) and caught.applied == 0 and type(caught.__cause__) in _STORE_ROUTINE_REFUSALS",
        "    return True",
    ),
)
