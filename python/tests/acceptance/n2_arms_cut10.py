"""Cut 10's 31 frozen holdings declarations and their sabotages.

**20 selected + 11 labeled = 31 declaration units**, counted once at the
single home recorded here.  Check nodes are Science pytest functions; atoms
productions are citations in ``ATOMS_CITATIONS_BY_UNIT``, never collected.

Unit-to-check map:

* H1u1/u2/u3: payload back-fill / detached capture / delete return
* H2u1..u6: timestamp / disagreement / cycle / unresolved / coalescence / algorithms
* H3u1/u2/u3: coverage / receipt reproduction / committed heads
* H4u1/u2/u3: publish-or-fail / mint nothing / intent before mutation
* G9u1: presence never promotes; L7u1/u2: qualification / append first
* L10u1/u2: metadata-less / unserviceable dereference
* J1..J11: the eleven labels in frozen §3.3 order

Every sabotage matches exactly once below ``src/science`` and every declared
check fails under that mutation while passing on the real tree.  G9's three
co-passing independence nodes are deliberately not checks of its arm; the
audit module runs all four against one sabotaged package and requires G9 to
fail while G2b, R5, and R10 pass.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = [
    "ATOMS_CITATIONS_BY_UNIT",
    "CUT10_ARMS",
    "LABELED_UNITS",
    "ROW_UNITS",
]


ROW_UNITS: dict[str, int] = {
    "H1": 3,
    "H2": 6,
    "H3": 3,
    "H4": 3,
    "G9": 1,
    "L7": 2,
    "L10": 2,
}

LABELED_UNITS: tuple[str, ...] = tuple(f"J{number}" for number in range(1, 12))

ATOMS_CITATIONS_BY_UNIT: dict[str, tuple[str, ...]] = {
    "H1u1": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §5, §8",
        "python/tests/test_final_states.py::test_run_transaction_returns_the_complete_final_surface_typed",
    ),
    "H1u3": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §5, §8",
        "python/tests/test_final_states.py::test_final_states_carries_the_delete_rows_verified_absence",
    ),
    "H4u2": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §3, §4, §8",
        "python/tests/test_read_path_state.py::test_read_path_state_refuses_a_metadata_less_root",
        "python/tests/test_read_path_state.py::test_read_path_state_refuses_an_unserviceable_replica",
    ),
    "L10u1": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §3, §4, §8",
        "python/tests/test_read_path_state.py::test_read_path_state_refuses_a_metadata_less_root",
    ),
    "L10u2": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §3, §4, §8",
        "python/tests/test_read_path_state.py::test_read_path_state_refuses_an_unserviceable_replica",
    ),
    "J1": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §3, §4, §6, §8",
        "python/tests/test_read_path_state.py::test_a_routine_failure_after_the_observation_begins_is_unestablished",
    ),
    "J2": (
        "docs/2026-08-24-holdings-read-and-evidence-commands-design.md §5, §6, §8",
        "python/tests/test_final_states.py::test_final_states_is_complete_while_the_chain_carries_the_registered_subset",
    ),
}


_MINT_ABSENT_FROM_NOT_ATTEMPTED = Sabotage(
    module="holdings/boundary.py",
    before=(
        "    if isinstance(view, ReadNotAttemptedView):\n"
        "        return InconclusiveAttempt(\"byte-locator-untested\", view.reason, view.detail)"
    ),
    after=(
        "    if isinstance(view, ReadNotAttemptedView):\n"
        "        return _publish(ctx, location, Absent(), token, intent, standing)"
    ),
)


CUT10_ARMS: tuple[Arm, ...] = (
    Arm(
        row="H1u1",
        asserts="a managed write records the engine's verified final row, never a payload-derived digest; label J2 owns the evidence rule",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before="    record = holdings_observation(location=location, outcome=Found(state.content_hash), expected=expected,",
            after=(
                "    record = holdings_observation(location=location, "
                "outcome=Found(\"sha256:\" + __import__(\"hashlib\").sha256(content).hexdigest()), expected=expected,"
            ),
        ),
        checks=("test_holdings_boundary.py::test_write_records_the_engine_final_row_not_the_payload_digest",),
    ),
    Arm(
        row="H1u2",
        asserts="a detached capture over an undamaged store establishes nothing for the act; raw concurrent mutation remains out of band",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before="    view = ctx.seam.read_path(ctx.store_root, location.relative_path)",
            after=(
                "    detached = __import__(\"science.root\", fromlist=[\"_log_seam\", \"_path_state_view\"])\n"
                "    captured = detached._log_seam().capture(ctx.store_root, (location.relative_path,))\n"
                "    view = type(\"DetachedView\", (), {\"state\": detached._path_state_view(captured[0][1])})()"
            ),
        ),
        checks=("test_holdings_boundary.py::test_recheck_refuses_to_mint_from_a_detached_capture",),
    ),
    Arm(
        row="H1u3",
        asserts="delete absence comes from the verified final AbsentState row, never transaction return alone; label J2 owns the evidence rule",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "    state = _final(ctx.seam.store_delete(ctx.store_root, location.relative_path), location.relative_path)\n"
                "    if not isinstance(state, AbsentStateView):\n"
                "        raise TypeError(f\"store delete did not establish absence at {location.relative_path!r}\")\n"
                "    return _publish(ctx, location, Absent(), token, intent, standing)"
            ),
            after=(
                "    ctx.seam.store_delete(ctx.store_root, location.relative_path)\n"
                "    return _publish(ctx, location, Absent(), token, intent, standing)"
            ),
        ),
        checks=("test_holdings_boundary.py::test_delete_refuses_a_wrong_or_missing_final_row",),
    ),
    Arm(
        row="H2u1",
        asserts="active heads follow explicit supersession only; the paired fixture asserts only timestamps differ",
        sabotage=Sabotage(
            module="holdings/rules_v1/holdings.py",
            before=(
                "        heads[location] = sorted((member for member in members if member[\"ref\"] not in superseded), key=lambda item: item[\"ref\"])"
            ),
            after=(
                "        heads[location] = sorted((member for member in members if member[\"ref\"] not in superseded), "
                "key=lambda item: json.loads(canonical_by_ref[item[\"ref\"]])[\"facets\"][\"holdings-observation\"][\"observed_at\"])[-1:]"
            ),
        ),
        checks=("test_holdings_reduce.py::test_no_timestamp_ordering",),
    ),
    Arm(
        row="H2u2",
        asserts="found beside absent blocks as contested; the found never remains active",
        sabotage=Sabotage(
            module="holdings/rules_v1/holdings.py",
            before="    if len(findings) > 1:\n        reasons.add(\"contested\")",
            after="    if False:\n        reasons.add(\"contested\")",
        ),
        checks=("test_holdings_reduce.py::test_disagreeing_heads_block_as_contested",),
    ),
    Arm(
        row="H2u3",
        asserts="an individually decodable raw-authored supersession cycle refuses the whole projection at the walk",
        sabotage=Sabotage(
            module="holdings/rules_v1/holdings.py",
            before="    if ref in visiting:\n        raise ValueError(\"supersession cycle at \" + location)",
            after="    if ref in visiting:\n        return",
        ),
        checks=("test_holdings_reduce.py::test_a_cycle_refuses_the_whole_projection",),
    ),
    Arm(
        row="H2u4",
        asserts="qualification-unresolved remains explicit and is never collapsed into a resolved state; crash-window readings stand in the ordinary suite",
        sabotage=Sabotage(
            module="holdings/qualify.py",
            before='    return "unresolved" if unresolved else "unmatched"',
            after='    return "unmatched"',
        ),
        checks=("test_holdings_reduce.py::test_qualify_intent_never_collapses_unresolved",),
    ),
    Arm(
        row="H2u5",
        asserts="all agreeing heads remain active with their distinct expectations; classification coalesces without dropping evidence",
        sabotage=Sabotage(
            module="holdings/rules_v1/holdings.py",
            before="            active.extend(projections)",
            after="            active.extend(projections[:1])",
        ),
        checks=("test_holdings_reduce.py::test_agreeing_heads_all_stay_active_with_their_expectations",),
    ),
    Arm(
        row="H2u6",
        asserts="found heads under different algorithms block as incommensurable",
        sabotage=Sabotage(
            module="holdings/rules_v1/holdings.py",
            before="    if len(by_algorithm) > 1:\n        reasons.add(\"incommensurable\")",
            after="    if False:\n        reasons.add(\"incommensurable\")",
        ),
        checks=("test_holdings_reduce.py::test_algorithm_mixed_found_pair_is_incommensurable",),
    ),
    Arm(
        row="H3u1",
        asserts="empty or unproducible declared coverage refuses the whole projection, never silently shrinking",
        sabotage=Sabotage(
            module="holdings/project.py",
            before=(
                "    if not coverage:\n"
                "        raise CoverageUnknown(\"a projection with no declared coverage is refused\")\n"
                "    carriers = epoch.resolve_coverage(world, coverage)"
            ),
            after=(
                "    carriers = {}\n"
                "    for corpus_id in coverage:\n"
                "        try:\n"
                "            carriers.update(epoch.resolve_coverage(world, frozenset({corpus_id})))\n"
                "        except CoverageUnknown:\n"
                "            pass"
            ),
        ),
        checks=(
            "test_holdings_capture.py::test_no_declared_coverage_refuses",
            "test_holdings_capture.py::test_an_unresolvable_corpus_refuses_the_whole_projection",
        ),
    ),
    Arm(
        row="H3u2",
        asserts="receipt validation re-runs the exact named coverage; signing only half cannot validate as the full receipt",
        sabotage=Sabotage(
            module="holdings/receipt.py",
            before=(
                "        current = capture_coverage(\n"
                "            world,\n"
                "            frozenset(corpus_id for corpus_id, _state, _head in checked.coverage),\n"
                "            chain_view=chain_view,\n"
                "            state_facts=state_facts,\n"
                "        )\n"
                "    except (\n"
                "        BuildContended,\n"
                "        CaptureDrift,\n"
                "        CorpusStateMalformed,\n"
                "        CoverageNotLive,\n"
                "        CoverageUnknown,\n"
                "        CoverageUnresolvable,\n"
                "        LogEvidenceRefused,\n"
                "    ) as caught:\n"
                "        return HoldingsReceiptOutcome(\"unresolvable\", f\"the named coverage cannot be produced here: {caught}\")\n"
                "    selected = _named_capture(current, checked.coverage)"
            ),
            after=(
                "        named = checked.coverage[:1]\n"
                "        current = capture_coverage(\n"
                "            world,\n"
                "            frozenset(corpus_id for corpus_id, _state, _head in named),\n"
                "            chain_view=chain_view,\n"
                "            state_facts=state_facts,\n"
                "        )\n"
                "    except (\n"
                "        BuildContended,\n"
                "        CaptureDrift,\n"
                "        CorpusStateMalformed,\n"
                "        CoverageNotLive,\n"
                "        CoverageUnknown,\n"
                "        CoverageUnresolvable,\n"
                "        LogEvidenceRefused,\n"
                "    ) as caught:\n"
                "        return HoldingsReceiptOutcome(\"unresolvable\", f\"the named coverage cannot be produced here: {caught}\")\n"
                "    selected = _named_capture(current, named)"
            ),
        ),
        checks=("test_holdings_receipt.py::test_signing_half_the_coverage_fails",),
    ),
    Arm(
        row="H3u3",
        asserts="coherently captured chain heads are committed receipt inputs; the same states under different heads have different identities",
        sabotage=Sabotage(
            module="holdings/receipt.py",
            before="                [[corpus_id, state, head] for corpus_id, state, head in self.coverage],",
            after="                [[corpus_id, state] for corpus_id, state, _head in self.coverage],",
        ),
        checks=("test_holdings_receipt.py::test_chain_head_alone_participates_in_receipt_identity",),
    ),
    Arm(
        row="H4u1",
        asserts="an established finding is published or the act fails loudly; no transient result survives a dropped record",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "def _publish(ctx: ActContext, location: StoreLocator, outcome: Found | Absent, token: str, intent: str,\n"
                "             standing: tuple[HoldingsObservation, ...]) -> PublishedObservation:\n"
                "    record = holdings_observation(location=location, outcome=outcome, observer=ctx.observer, instrument=ctx.instrument,\n"
                "                                  event_token=token, observed_at=datetime.now(UTC).strftime(\"%Y-%m-%dT%H:%M:%SZ\"),\n"
                "                                  supersedes=standing)\n"
                "    node = stored.holdings_observation_node(record)\n"
                "    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f\"holdings-observation/{record.identity()}.md\",\n"
                "                                                             node_to_markdown(node).encode(\"utf-8\")),), intent)\n"
                "    return PublishedObservation(record)"
            ),
            after=(
                "def _publish(ctx: ActContext, location: StoreLocator, outcome: Found | Absent, token: str, intent: str,\n"
                "             standing: tuple[HoldingsObservation, ...]) -> PublishedObservation:\n"
                "    record = holdings_observation(location=location, outcome=outcome, observer=ctx.observer, instrument=ctx.instrument,\n"
                "                                  event_token=token, observed_at=datetime.now(UTC).strftime(\"%Y-%m-%dT%H:%M:%SZ\"),\n"
                "                                  supersedes=standing)\n"
                "    node = stored.holdings_observation_node(record)\n"
                "    return PublishedObservation(record)"
            ),
        ),
        checks=("test_holdings_boundary.py::test_publication_failure_after_an_established_outcome_raises",),
    ),
    Arm(
        row="H4u2",
        asserts="an inconclusive store attempt uses J1's report channel, leaves the standing observation unchanged, and mints nothing",
        sabotage=_MINT_ABSENT_FROM_NOT_ATTEMPTED,
        checks=(
            "test_holdings_boundary.py::test_recheck_on_a_metadata_less_store_reports_byte_locator_untested_and_mints_nothing",
            "test_holdings_boundary.py::test_recheck_of_an_unserviceable_restored_root_mints_nothing_never_absent",
        ),
    ),
    Arm(
        row="H4u3",
        asserts="a managed move appends its intents before mutation; append failure leaves both paths unchanged",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "    source_token, source_intent = _append(ctx, source, \"move-source\")\n"
                "    destination_token, destination_intent = _append(ctx, destination, \"move-destination\")\n"
                "    _bind(ctx, source)\n"
                "    _bind(ctx, destination)\n"
                "    outcome = ctx.seam.store_move(ctx.store_root, source.relative_path, destination.relative_path)"
            ),
            after=(
                "    source_token, source_intent = \"sabotaged-source\", \"0\" * 64\n"
                "    destination_token, destination_intent = \"sabotaged-destination\", \"1\" * 64\n"
                "    _bind(ctx, source)\n"
                "    _bind(ctx, destination)\n"
                "    outcome = ctx.seam.store_move(ctx.store_root, source.relative_path, destination.relative_path)"
            ),
        ),
        checks=("test_holdings_boundary.py::test_a_move_never_mutates_when_its_intent_append_fails",),
    ),
    Arm(
        row="G9u1",
        asserts="presence never substitutes the declaration's digest; the G2b admission gate, R5, and R10 co-pass against this same sabotage",
        sabotage=Sabotage(
            module="holdings/adapter.py",
            before=(
                "    for digest in declared:\n"
                "        if _matches(member, digest) or (\n"
                "            _algorithm(found) == _algorithm(digest) and any(_matches(row, digest) for row in history)\n"
                "        ):\n"
                "            return found"
            ),
            after=(
                "    for digest in declared:\n"
                "        if found is not None:\n"
                "            return digest"
            ),
        ),
        checks=("test_holdings_adapter.py::test_a_different_digest_never_promotes_on_presence",),
    ),
    Arm(
        row="L7u1",
        asserts="genuine committed wrong-location, wrong-token, and resolved no-observation fulfillments fail qualification; unresolved stays H2u4's territory",
        sabotage=Sabotage(
            module="holdings/qualify.py",
            before=(
                "            if observation is not None:\n"
                "                if observation[\"location\"] == intent[\"location\"] and observation[\"event_token\"] == intent[\"event_token\"]:\n"
                "                    return \"matched\""
            ),
            after=(
                "            if observation is not None:\n"
                "                return \"matched\""
            ),
        ),
        checks=(
            "test_holdings_windows.py::test_nonqualifying_fulfillments_are_committed_and_leave_the_intent_unsettled",
        ),
    ),
    Arm(
        row="L7u2",
        asserts="the holdings write appends its intent before mutation; the real kill window reads unsettled until a fulfilled recheck",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "    token, intent = _append(ctx, location, \"write\")\n"
                "    _bind(ctx, location)\n"
                "    state = _final(ctx.seam.store_write(ctx.store_root, location.relative_path, content), location.relative_path)"
            ),
            after=(
                "    _bind(ctx, location)\n"
                "    state = _final(ctx.seam.store_write(ctx.store_root, location.relative_path, content), location.relative_path)\n"
                "    token, intent = _append(ctx, location, \"write\")"
            ),
        ),
        checks=(
            "test_holdings_boundary.py::test_a_kill_between_intent_and_mutation_leaves_the_intent_unmatched",
            "test_holdings_windows.py::test_the_kill_window_reads_unsettled_until_a_fulfilled_recheck_lifts_it",
        ),
    ),
    Arm(
        row="L10u1",
        asserts="a metadata-less store dereference goes through the act and never launders an uncopied path into absent; J1 maps the report",
        sabotage=_MINT_ABSENT_FROM_NOT_ATTEMPTED,
        checks=(
            "test_holdings_boundary.py::test_recheck_on_a_metadata_less_store_reports_byte_locator_untested_and_mints_nothing",
        ),
    ),
    Arm(
        row="L10u2",
        asserts="an unserviceable failed-restore dereference goes through the act and never launders the omitted payload into absent; J1 maps the report",
        sabotage=_MINT_ABSENT_FROM_NOT_ATTEMPTED,
        checks=(
            "test_holdings_boundary.py::test_recheck_of_an_unserviceable_restored_root_mints_nothing_never_absent",
        ),
    ),
    Arm(
        row="J1",
        asserts="the structured read variants map to the exact two report vocabularies; engine raises remain raises",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "    if isinstance(view, ReadNotAttemptedView):\n"
                "        return InconclusiveAttempt(\"byte-locator-untested\", view.reason, view.detail)\n"
                "    if isinstance(view, ReadUnestablishedView):\n"
                "        return InconclusiveAttempt(\"retrieval-failed\", view.reason, view.detail)"
            ),
            after=(
                "    if isinstance(view, ReadNotAttemptedView):\n"
                "        return InconclusiveAttempt(\"retrieval-failed\", view.reason, view.detail)\n"
                "    if isinstance(view, ReadUnestablishedView):\n"
                "        return InconclusiveAttempt(\"byte-locator-untested\", view.reason, view.detail)"
            ),
        ),
        checks=(
            "test_holdings_boundary.py::test_recheck_on_a_metadata_less_store_reports_byte_locator_untested_and_mints_nothing",
            "test_holdings_boundary.py::test_read_unestablished_reports_retrieval_failed_verbatim_and_mints_nothing",
        ),
    ),
    Arm(
        row="J2",
        asserts="post-state evidence selects the final_states row for the exact path, including both locations of a move",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before="        if final_path == path:\n            return state",
            after="        if True:\n            return state",
        ),
        checks=("test_holdings_boundary.py::test_move_publishes_two_observations_fulfilling_two_intents",),
    ),
    Arm(
        row="J3",
        asserts="the locator union ships store-only and URL construction refuses with the named deferral",
        sabotage=Sabotage(
            module="holdings/records.py",
            before="    raise UrlLocatorDeferred(f\"url locator {url!r} is deferred until the URL slice exists\")",
            after="    return None  # type: ignore[return-value]",
        ),
        checks=("test_holdings_records.py::test_url_locator_refuses_with_the_named_deferral",),
    ),
    Arm(
        row="J4",
        asserts="algorithm-qualified digests use canonical lowercase spelling and exact known widths, never repair",
        sabotage=Sabotage(
            module="holdings/records.py",
            before='_DIGEST = re.compile(r"^(?P<algorithm>[a-z0-9-]+):(?P<hex>[0-9a-f]+)$")',
            after='_DIGEST = re.compile(r"^(?P<algorithm>[a-z0-9-]+):(?P<hex>[0-9A-Fa-f]+)$")',
        ),
        checks=("test_holdings_records.py::test_found_requires_an_algorithm_qualified_canonical_digest",),
    ),
    Arm(
        row="J5",
        asserts="supersession is constructible only between records at one canonical location",
        sabotage=Sabotage(
            module="holdings/records.py",
            before="    if any(predecessor.location.canonical() != location.canonical() for predecessor in supersedes):",
            after="    if False and any(predecessor.location.canonical() != location.canonical() for predecessor in supersedes):",
        ),
        checks=("test_holdings_records.py::test_supersedes_predecessors_must_share_the_canonical_location",),
    ),
    Arm(
        row="J6",
        asserts="science.holdings-observation.v1 digests the whole facet; event-token distinctness is never clock-derived",
        sabotage=Sabotage(
            module="holdings/records.py",
            before="        return v1.digest(HOLDINGS_OBSERVATION_DOMAIN, self.facet())",
            after=(
                "        facet = self.facet()\n"
                "        del facet[\"event_token\"]\n"
                "        return v1.digest(HOLDINGS_OBSERVATION_DOMAIN, facet)"
            ),
        ),
        checks=(
            "test_holdings_records.py::test_two_identical_findings_differ_by_event_token_alone",
            "test_holdings_records.py::test_every_field_participates_in_the_identity",
        ),
    ),
    Arm(
        row="J7",
        asserts="the governed stored kind is boundary-authored and joins no epoch map",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "holdings-observation":\n            raise WriteRefused("a holdings observation is minted only by the acts boundary")',
            after='        if node.kind == "holdings-observation" and False:\n            raise WriteRefused("a holdings observation is minted only by the acts boundary")',
        ),
        checks=("test_holdings_stored.py::test_direct_authoring_through_the_writer_is_refused",),
    ),
    Arm(
        row="J8",
        asserts="the canonical holdings intent travels with the registered stored observation path",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "def _publish(ctx: ActContext, location: StoreLocator, outcome: Found | Absent, token: str, intent: str,\n"
                "             standing: tuple[HoldingsObservation, ...]) -> PublishedObservation:\n"
                "    record = holdings_observation(location=location, outcome=outcome, observer=ctx.observer, instrument=ctx.instrument,\n"
                "                                  event_token=token, observed_at=datetime.now(UTC).strftime(\"%Y-%m-%dT%H:%M:%SZ\"),\n"
                "                                  supersedes=standing)\n"
                "    node = stored.holdings_observation_node(record)\n"
                "    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f\"holdings-observation/{record.identity()}.md\","
            ),
            after=(
                "def _publish(ctx: ActContext, location: StoreLocator, outcome: Found | Absent, token: str, intent: str,\n"
                "             standing: tuple[HoldingsObservation, ...]) -> PublishedObservation:\n"
                "    record = holdings_observation(location=location, outcome=outcome, observer=ctx.observer, instrument=ctx.instrument,\n"
                "                                  event_token=token, observed_at=datetime.now(UTC).strftime(\"%Y-%m-%dT%H:%M:%SZ\"),\n"
                "                                  supersedes=standing)\n"
                "    node = stored.holdings_observation_node(record)\n"
                "    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f\"misplaced/{record.identity()}.md\","
            ),
        ),
        checks=("test_holdings_boundary.py::test_the_published_transaction_registers_the_stored_path",),
    ),
    Arm(
        row="J9",
        asserts="move mints and appends two distinct intents one at a time before mutation; its crash-window readings cite L7u2 and H2u4",
        sabotage=Sabotage(
            module="holdings/boundary.py",
            before=(
                "    source_token, source_intent = _append(ctx, source, \"move-source\")\n"
                "    destination_token, destination_intent = _append(ctx, destination, \"move-destination\")"
            ),
            after=(
                "    source_token, source_intent = _append(ctx, source, \"move-source\")\n"
                "    destination_token = source_token\n"
                "    destination_intent = ctx.seam.append_intent(\n"
                "        ctx.observer_root, intent_payload(location=destination, act_kind=\"move-destination\",\n"
                "                                          event_token=destination_token, actor=ctx.actor)\n"
                "    )"
            ),
        ),
        checks=("test_holdings_boundary.py::test_move_publishes_two_observations_fulfilling_two_intents",),
    ),
    Arm(
        row="J10",
        asserts="mechanical capture carries the exact closed record and whole-chain schema with no kind filter",
        sabotage=Sabotage(
            module="holdings/project.py",
            before='            "intent_digest": entry.intent_digest,',
            after="            # intent_digest silently omitted",
        ),
        checks=("test_holdings_capture.py::test_each_entry_variant_has_the_exact_closed_serialization",),
    ),
    Arm(
        row="J11",
        asserts="the holdings-receipt facet's identity digests every closed member and names the fixture-admitted binding",
        sabotage=Sabotage(
            module="holdings/receipt.py",
            before="                self.blocked_set_digest,",
            after="                # blocked_set_digest silently omitted",
        ),
        checks=("test_holdings_receipt.py::test_identity_digests_every_member",),
    ),
)
