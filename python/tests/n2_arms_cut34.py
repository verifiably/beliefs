"""Frozen cut-34 declaration: seventeen units, each homing one sabotage arm."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "C8-a",
    "C8-b",
    "C8-c",
    "C8-d",
    "C9-a",
    "C9-b",
    "C9-c",
    "C9-d",
    "BI-1",
    "BI-2",
    "BI-3",
    "BI-4",
    "BI-5",
    "BI-6",
    "BI-7",
    "BI-8",
    "BI-9",
)
_MODULE = "acceptance/test_snapshot_retraction_acceptance.py"
UNIT_CHECKS = {
    "C8-a": f"{_MODULE}::test_c8a_import_of_a_retracted_producer_subject_refuses_before_any_write",
    "C8-b": f"{_MODULE}::test_c8b_the_audit_reports_retracted_without_a_finding",
    "C8-c": f"{_MODULE}::test_c8c_the_query_reports_retracted_and_the_successor_unchecked",
    "C8-d": f"{_MODULE}::test_c8d_mounting_writes_nothing_and_validates_nothing",
    "C9-a": f"{_MODULE}::test_c9a_a_computation_bound_to_the_old_snapshot_refuses",
    "C9-b": f"{_MODULE}::test_c9b_bound_to_the_new_snapshot_proceeds_and_the_digest_moves",
    "C9-c": f"{_MODULE}::test_c9c_the_old_epoch_is_byte_unchanged",
    "C9-d": f"{_MODULE}::test_c9d_nothing_resolves_through_the_retraction_to_its_successor",
    "BI-1": f"{_MODULE}::test_bi1_a_snapshot_retraction_outside_the_targets_coverage_is_refused_at_authoring",
    "BI-2": f"{_MODULE}::test_bi2_a_writer_without_the_port_refuses_the_arm",
    "BI-3": f"{_MODULE}::test_bi3_retracted_precedes_availability",
    "BI-4": f"{_MODULE}::test_bi4_a_counter_retraction_restores_the_snapshot",
    "BI-5": f"{_MODULE}::test_bi5_an_older_snapshots_retraction_is_out_of_the_closure",
    "BI-6": f"{_MODULE}::test_bi6_a_raw_written_snapshot_retraction_is_reported_by_audit_world_from_captured_records",
    "BI-7": f"{_MODULE}::test_bi7_history_is_in_the_digest",
    "BI-8": f"{_MODULE}::test_bi8_an_unreadable_counter_retraction_refuses_rather_than_restores",
    "BI-9": f"{_MODULE}::test_bi9_a_rebuild_restores_nothing_and_duplicates_nothing",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Each row is exactly one declared unit, including its own suffix."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-34 row")
    return row


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT34_ARMS = (
    _arm(
        "C8-a",
        "Import of a carrier whose producer subject is retracted refuses before any write.",
        "world/importing.py",
        '("malformed-receipt", "malformed"), ("retracted-snapshot", "retracted"), ("refuted-receipt", "refuted"))',
        '("malformed-receipt", "malformed"), ("refuted-receipt", "refuted"))',
    ),
    _arm(
        "C8-b",
        "The epoch audit reduces a retracted producer receipt to the retracted state without a finding.",
        "world/audit.py",
        '    if any(outcome.outcome == "retracted" for outcome in outcomes):',
        "    if False:",
    ),
    _arm(
        "C8-c",
        "The snapshot-state query reports the retracted snapshot and its unchecked successor.",
        "world/read.py",
        "    if identity not in standing.retracted:\n        return None",
        "    if True:\n        return None",
    ),
    _arm(
        "C8-d",
        "Mounting a corpus writes nothing under epochs/ and validates nothing.",
        "world/registry.py",
        "        with self._state.lock:\n"
        "            return _locked_admit(\n"
        "                self._state,\n"
        "                self.config.world_root,\n"
        "                self._executor_factory,\n"
        "                lambda: load_manifest(corpus_root),\n"
        "                provenance,\n"
        "                self.authority,\n"
        "            )",
        "        with self._state.lock:\n"
        "            record = _locked_admit(\n"
        "                self._state,\n"
        "                self.config.world_root,\n"
        "                self._executor_factory,\n"
        "                lambda: load_manifest(corpus_root),\n"
        "                provenance,\n"
        "                self.authority,\n"
        "            )\n"
        "        from beliefs.errors import EpochUnknown as _Unknown\n"
        "        from beliefs.world import read as _read\n"
        "        try:\n"
        "            current = _read.current_epoch(self)\n"
        "        except _Unknown:\n"
        "            return record\n"
        '        _read.validate_receipt(self, current, "producer")\n'
        "        return record",
    ),
    _arm(
        "C9-a",
        "A world read bound to the retracted old snapshot refuses.",
        "evaluation.py",
        "            raise ProducerSnapshotRetracted(bound)",
        "            pass",
    ),
    _arm(
        "C9-b",
        "Bound to the successor the read proceeds and the digest moves with the producer snapshot member.",
        "closure.py",
        '        "producer_snapshot": producer_snapshot_identity,',
        '        "producer_snapshot": "",',
    ),
    _arm(
        "C9-c",
        "The old epoch's members and receipts are byte-unchanged across the retraction: standing is never stored on the target.",
        "world/epoch.py",
        "            retained[carrier.subject_identity] = coverage",
        "            retained[carrier.subject_identity] = coverage\n"
        '            (self._world.config.world_root / "epochs" / carrier.packaging_identity / member).open("ab").write(b"\\nretracted: true\\n")',
    ),
    _arm(
        "C9-d",
        "Nothing resolves through the retraction to its successor: the supplied identity must be the bound epoch's.",
        "evaluation.py",
        "        if context.producer_snapshot_identity != bound:\n"
        "            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)",
        "        successors = {\n"
        '            n.facets[stored.RETRACTION_FACET].get("successor")\n'
        "            for corpus_id, _state in view.stamp.coverage\n"
        "            for n in view.captured_records(corpus_id)\n"
        '            if n.kind == "retraction" and stored.RETRACTION_FACET in n.facets\n'
        "        }\n"
        "        if context.producer_snapshot_identity != bound and context.producer_snapshot_identity in successors:\n"
        "            bound = context.producer_snapshot_identity  # resolve through the retraction to its successor\n"
        "        if context.producer_snapshot_identity != bound:\n"
        "            raise ProducerSnapshotMismatch(context.producer_snapshot_identity, bound)",
    ),
    _arm(
        "BI-1",
        "A snapshot retraction written outside the target's coverage is refused at authoring.",
        "corpus.py",
        "        if corpus_id not in retained[identity]:",
        "        if False:",
    ),
    _arm(
        "BI-2",
        "A writer constructed without the snapshot resolver port refuses the arm.",
        "corpus.py",
        "        if self._snapshot_resolver is None:\n            raise RetractionTargetUnresolvable(",
        "        if self._snapshot_resolver is None:\n            return\n            raise RetractionTargetUnresolvable(",
    ),
    _arm(
        "BI-3",
        "Retracted is decided before availability: a moved covered corpus does not hide it.",
        "world/read.py",
        "    if kind == derive.BELIEF_INPUT_KIND:\n        standing = _snapshot_standing(world, receipt)",
        "    if False:\n        standing = _snapshot_standing(world, receipt)",
    ),
    _arm(
        "BI-4",
        "A counter-retraction restores the snapshot: only a standing retraction retracts.",
        "corpus.py",
        "            if standing[root]:\n                retracted.add(identity)",
        "            if True:\n                retracted.add(identity)",
    ),
    _arm(
        "BI-5",
        "An older snapshot's retraction is out of the closure: the scope loop never takes a snapshot arm.",
        "evaluation.py",
        '            key = None if target["arm"] == "snapshot" else target["resolved"]   # a snapshot arm is never in scope (decision 8)',
        '            key = f"producer-snapshot:{target[\'subject_identity\']}" if target["arm"] == "snapshot" else target["resolved"]\n'
        '            scope = scope | ({key} if target["arm"] == "snapshot" else set())',
    ),
    _arm(
        "BI-6",
        "The world audit resolves raw-written snapshot retractions from the captured records.",
        "audit.py",
        "        for node in view.captured_records(corpus_id):      # unmapped post-build records included (§7.4)",
        "        for node in ():",
    ),
    _arm(
        "BI-7",
        "The bound snapshot's retraction history is in the closure and the digest.",
        "evaluation.py",
        "        found=tuple(sorted({*((ref, recorded) for ref, recorded in enumeration.found if ref in taken), *history})),",
        "        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),",
    ),
    _arm(
        "BI-8",
        "A chain member is validated with the write boundary's checks before it is folded: an unreadable counter-retraction refuses rather than restores.",
        "corpus.py",
        "                CorpusWriter._resolve_retraction_target(nodes[ref], view)\n"
        "            except ScienceError as caught:\n"
        "                raise RetractionUnreadable(ref, str(caught)) from caught",
        "                pass\n"
        "            except ScienceError as caught:\n"
        "                raise RetractionUnreadable(ref, str(caught)) from caught",
    ),
    _arm(
        "BI-9",
        "A rebuild restores nothing and duplicates nothing: the history is the live fold, whatever the rebuilt epoch captured.",
        "evaluation.py",
        "        history = snapshot_standing.history.get(bound, ())",
        "        history = () if any(ref in {r for r, _ in snapshot_standing.history.get(bound, ())} for ref, _ in view.retraction_enumeration().found) else snapshot_standing.history.get(bound, ())",
    ),
)
