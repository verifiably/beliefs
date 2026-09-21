"""Frozen cut-36 declaration: sixteen units, eighteen sabotage arms (L8-a and L8-j home two each)."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "L8-a",
    "L8-b",
    "L8-c",
    "L8-d",
    "L8-e",
    "L8-f",
    "L8-g",
    "L8-h",
    "L8-i",
    "L8-j",
    "L8-k",
    "L4-a",
    "L10-a",
    "BI-1",
    "BI-2",
    "BI-3",
)
_MODULE = "acceptance/test_event_order_acceptance.py"
UNIT_CHECKS = {
    "L8-a": f"{_MODULE}::test_l8a_a_freeze_before_a_run_intent_across_ordered_cuts_orders_and_is_antisymmetric_durably",
    "L8-b": f"{_MODULE}::test_l8b_co_appearance_is_unordered_and_later_cuts_holding_both_do_not_reverse_a_witness_durably",
    "L8-c": f"{_MODULE}::test_l8c_epoch_sequence_numbers_are_read_by_nothing_durably",
    "L8-d": f"{_MODULE}::test_l8d_a_cut_covering_one_corpus_establishes_nothing_durably",
    "L8-e": f"{_MODULE}::test_l8e_a_chain_replaced_under_another_fork_genesis_establishes_nothing_durably",
    "L8-f": f"{_MODULE}::test_l8f_the_double_witness_is_unordered_durably",
    "L8-g": f"{_MODULE}::test_l8g_valid_prefix_truncation_invalidates_every_witness_and_unknowns_the_removed_event_durably",
    "L8-h": f"{_MODULE}::test_l8h_same_chain_orders_by_ancestry_and_equal_moments_are_unordered_durably",
    "L8-i": f"{_MODULE}::test_l8i_a_pending_or_rolled_back_registration_has_no_moment_durably",
    "L8-j": f"{_MODULE}::test_l8j_same_chain_independence_from_a_malformed_carrier_and_world_chain_durably",
    "L8-k": f"{_MODULE}::test_l8k_the_refusals_and_a_terminal_corpus_durably",
    "L4-a": f"{_MODULE}::test_l4a_a_deleted_chain_refutes_against_its_registry_anchor_bound_by_corpus_id_durably",
    "L10-a": f"{_MODULE}::test_l10a_a_replica_under_a_fresh_manifest_refuses_subject_mismatch_at_arrival_durably",
    "BI-1": f"{_MODULE}::test_bi1_recovery_precedes_resolution_on_both_paths_durably",
    "BI-2": f"{_MODULE}::test_bi2_one_world_inspection_and_the_world_lock_released_before_sorted_unnested_corpus_locks_durably",
    "BI-3": f"{_MODULE}::test_bi3_the_genesis_clause_alone_decides_a_placement_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Each row is one declared unit; L8-a's and L8-j's two numbered arms share their unit."""
    unit = row[:-1] if row[-1:] in ("1", "2") and row[:-1] in ("L8-a", "L8-j") else row
    if unit not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-36 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT36_ARMS = (
    _arm(
        "L8-a1",
        "A freeze before a run intent across ordered cuts orders: E2 orders after E1 by E2's own world anchor, never E1's.",
        "world/verify.py",
        "            built_from = e2.world_anchor.head_digest",
        "            built_from = e1.world_anchor.head_digest",
    ),
    _arm(
        "L8-a2",
        "Descent includes the settlement itself: a cut built from the settling head is ordered after the epoch it settled.",
        "world/verify.py",
        '    return "ordered" if positions[built_from] >= positions[settlement] else "unordered"',
        '    return "ordered" if positions[built_from] > positions[settlement] else "unordered"',
    ),
    _arm(
        "L8-b",
        "A witness requires the first cut to exclude the second event: later cuts holding both never reverse a witness.",
        "world/verify.py",
        "        if not (contains(on_first, first.moment) and excludes(on_second, second.moment)):",
        "        if not contains(on_first, first.moment):",
    ),
    _arm(
        "L8-e",
        "A chain replaced under another fork genesis places nowhere: an unplaceable anchor establishes nothing.",
        "world/verify.py",
        "            return place(view, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest)",
        "            return place(view, genesis_digest=anchor.genesis_digest, head_digest=anchor.head_digest) or Placement(head=len(view.entries) - 1)",
    ),
    _arm(
        "L8-c",
        "Epoch sequence numbers are read by nothing: the relation consults no sequence.",
        "world/verify.py",
        "    cross_chain = a.corpus_id != b.corpus_id",
        "    sequence = 0  # an epoch sequence number, consulted\n    cross_chain = a.corpus_id != b.corpus_id",
    ),
    _arm(
        "L8-d",
        "A cut covering one corpus establishes nothing: both witness cuts cover both corpora.",
        "world/verify.py",
        "        if on_first is None or on_second is None:\n            continue",
        "        if on_first is None:\n            continue\n        if on_second is None:\n            on_second = Placement(head=-1)",
    ),
    _arm(
        "L8-f",
        "The double witness is unordered: a-precedes-b iff W(a,b) and not W(b,a).",
        "world/verify.py",
        "    if w_ab and not w_ba:",
        "    if w_ab:",
    ),
    _arm(
        "L8-g",
        "A head that is no entry of the live chain places nowhere: valid-prefix truncation invalidates every witness.",
        "world/events.py",
        "    return None\n\n\ndef contains(",
        "    return Placement(head=len(view.entries) - 1)\n\n\ndef contains(",
    ),
    _arm(
        "L8-h",
        "A registration's moment is its committed settlement's position, never its own.",
        "world/events.py",
        "    assert type(entry) is RegisteredEntryView\n    for index, candidate",
        "    assert type(entry) is RegisteredEntryView\n    return positions[digest]\n    for index, candidate",
    ),
    _arm(
        "L8-i",
        "A pending or rolled-back registration has no moment.",
        "world/events.py",
        "            return index if candidate.committed else None",
        "            return index",
    ),
    _arm(
        "L8-j1",
        "A same-chain question opens no epoch: a malformed world chain or epoch layout is never read for it.",
        "world/verify.py",
        "        if cross_chain:\n            epochs = tuple(",
        "        if True:\n            epochs = tuple(",
    ),
    _arm(
        "L8-j2",
        "EpochMalformed propagates untranslated from a cross-chain question: the relation refused to judge.",
        "world/verify.py",
        "        epochs: tuple[Epoch, ...] = ()\n        if cross_chain:",
        "        epochs: tuple[Epoch, ...] = ()\n"
        "        if cross_chain:\n"
        "          try:\n"
        "            epochs = tuple(\n"
        "                epoch._locked_open_epoch(config.world_root, identity)\n"
        "                for identity in epoch._retained_identities_locked(config.world_root)\n"
        "            )\n"
        "          except EpochMalformed:\n"
        "            epochs = ()\n"
        "        if False:",
    ),
    _arm(
        "L8-k",
        "Exactly one configured carrier root resolves a corpus: two carriers refuse EventCorpusUnresolvable.",
        "world/verify.py",
        "    if len(roots) != 1:",
        "    if len(roots) == 0:",
    ),
    _arm(
        "L4-a",
        "A deleted chain refutes against its registry anchor, bound by corpus id.",
        "world/verify.py",
        "        if bound:\n"
        '            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))',
        "        if False:\n"
        '            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))',
    ),
    _arm(
        "L10-a",
        "A replica under a fresh manifest refuses SubjectMismatch at arrival.",
        "world/verify.py",
        "        if manifest.corpus_id != provenance.parent_corpus_id:\n            raise SubjectMismatch(",
        "        if False:\n            raise SubjectMismatch(",
    ),
    _arm(
        "BI-1",
        "Recovery precedes resolution: the world root is inspected before the registry is scanned.",
        "world/verify.py",
        "        world_view = seam.inspect_registered(config.world_root)\n"
        "        registry_view = registry._scan_registry(config.world_root)",
        "        registry_view = registry._scan_registry(config.world_root)\n"
        "        world_view = seam.inspect_registered(config.world_root)",
    ),
    _arm(
        "BI-2",
        "The world chain is inspected exactly once per call.",
        "world/verify.py",
        "        world_view = seam.inspect_registered(config.world_root)\n",
        "        world_view = seam.inspect_registered(config.world_root)\n"
        "        world_view = seam.inspect_registered(config.world_root)\n",
    ),
    _arm(
        "BI-3",
        "The genesis clause alone decides a placement: a differing genesis places nowhere even where the head is an entry.",
        "world/events.py",
        "    if genesis_digest != view.genesis.digest:\n        return None",
        "    if False:\n        return None",
    ),
)
