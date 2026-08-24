"""Cut 9's 30 frozen root-lifecycle arms and the sabotages they must not survive.

**19 selected + 11 labeled = 30**, one declaration unit per `Selected` unit and
§3.3 label of `docs/designs/2026-08-23-conformance-cut-9.md`, counted once at
its home. `test_n2_cut9.py` reconciles this table against §4's accounting and
audits every arm; nothing here restates a clause another row owns.

**Check nodes live under Science's `tests/` only.** The harness resolves every
check there and applies sabotage beneath `src/science`, so an atoms test can
never be a check node. Where a unit's producing half is atoms-certified, the
declaration carries an **atoms citation** in `ATOMS_CITATIONS_BY_UNIT` — a
parallel metadata map of fully qualified atoms pytest nodes that never enters
`Arm.checks` and is resolved by the harness against nothing: it is recorded
provenance, not a collected node.

**One sabotage, every check falsified.** The harness scores an arm `mixed` —
a defect — when any declared check survives its sabotage, so each arm's check
set is exactly the set one Science-side mutation falsifies. Two consequences
of that physics are declared rather than hidden: **W13 u2** carries the
fork-of admission integration node (its planned home, label 8, is falsified
by a `verify.py` mutation that cannot reach `World.admit`), and **label 10**
audits its three surface-borne checks while its payload-codec and
non-fork-baseline clauses stand un-sabotaged in the ordinary suite — both
recorded in the execution ledger with this task.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = [
    "ATOMS_CITATIONS_BY_UNIT",
    "CUT9_ARMS",
    "LABELED_UNITS",
    "ROW_UNITS",
]


ROW_UNITS: dict[str, int] = {
    "L2": 1,
    "L4": 2,
    "L6": 2,
    "L10": 12,
    "W13": 2,
}
"""Cut 9 §4's selected-unit partition, verbatim: 19 across five rows."""

LABELED_UNITS: tuple[str, ...] = (
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
    "V7",
    "V8",
    "V9",
    "V10",
    "V11",
)
"""§3.3's eleven labeled declarations, in the order the cut states them."""


ATOMS_CITATIONS_BY_UNIT: dict[str, tuple[str, ...]] = {
    "L10u4": (
        "tests/test_lifecycle_commands.py::test_replicate_interrupted_after_stamp_is_read_only_unserviceable",
    ),
    "L10u5": (
        "tests/test_lifecycle_commands.py::test_replicate_interrupted_before_stamp_is_metadata_less",
    ),
    "L10u7": (
        "tests/test_lifecycle_commands.py::test_fork_interrupted_before_grant_is_read_only",
    ),
    "V1": (
        "tests/test_lifecycle_commands.py::test_interrupted_registration_matching_retry_grants",
        "tests/test_lifecycle_commands.py::test_bare_reregistration_over_an_existing_genesis_never_grants",
    ),
    "V2": (
        "tests/test_lifecycle_commands.py::test_host_delta_reads_binding_mismatched",
        "tests/test_lifecycle_commands.py::test_path_delta_reads_binding_mismatched",
    ),
    "V3": (
        "tests/test_lifecycle_commands.py::test_migration_authorized_success_grants_with_a_fresh_binding",
    ),
    "V4": (
        "tests/test_lifecycle_commands.py::test_fork_pregrant_retry_completes_with_identical_inputs",
        "tests/test_lifecycle_commands.py::test_fork_pregrant_retry_refuses_different_bytes",
        "tests/test_lifecycle_commands.py::test_fork_postgrant_retry_returns_success_after_legitimate_writes",
    ),
    "V5": (
        "tests/test_lifecycle_commands.py::test_grant_refuses_a_writable_root",
        "tests/test_lifecycle_commands.py::test_grant_creates_bookkeeping_for_a_metadata_less_root",
        "tests/test_lifecycle_commands.py::test_grant_is_idempotent_on_read_only_serviceable",
    ),
    "V6": (
        "tests/test_lifecycle_commands.py::test_metadata_less_tree_reads_metadata_less",
    ),
}
"""The atoms-certified interiors, cited per the cut's §1 principle. Metadata
only: never passed to `baseline` or `audit`, never a check node."""


# --- shared sabotages ---------------------------------------------------------

_EXECUTOR_REFUSAL_VOICE = Sabotage(
    module="root.py",
    before=(
        "        except (ProjectApprovalRefused, SpecValidationError, PreconditionRefused, CapabilityUnavailable) as caught:\n"
        "            # Rooted proof, adapter-built spec, clean refusal, missing\n"
        "            # capability: each is raised before any project mutation, or refuses\n"
        "            # cleanly with restoration proven by the engine's own contract.\n"
        "            raise ExecutionError(str(caught), index=None, applied=0) from caught\n"
        "        except PendingUnresolved as caught:"
    ),
    after=(
        "        except (ProjectApprovalRefused, SpecValidationError, PreconditionRefused, CapabilityUnavailable) as caught:\n"
        '            raise ExecutionError("the engine refused", index=None, applied=0) from caught\n'
        "        except PendingUnresolved as caught:\n"
        '            raise ExecutionError("the engine refused", index=None, applied=0) from caught\n'
        "        except PendingUnresolved as caught:"
    ),
)
"""Both gate refusals lose their voice: the writability gate's state and the
pending gate's registrations stop reaching the caller's error, so precedence
and mechanism become indistinguishable."""

_METADATA_LESS_MISREAD = Sabotage(
    module="root.py",
    before=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""\n'
        "    target = Path(root)\n"
        "    return _read_lifecycle_state_callback("
    ),
    after=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""\n'
        "    target = Path(root)\n"
        "    state = _read_lifecycle_state_callback(\n"
        "        _PRODUCTION_BACKEND,\n"
        "        str(target),\n"
        "        str(metadata_root_for(target)),\n"
        "        PRODUCTION_STORAGE,\n"
        "    )\n"
        "    if state is LifecycleState.METADATA_LESS:\n"
        "        return LifecycleState.READ_ONLY_UNSERVICEABLE\n"
        "    return state\n"
        "\n"
        "\n"
        "def _read_lifecycle_state_unreached(target: Path) -> LifecycleState:\n"
        "    return _read_lifecycle_state_callback("
    ),
)
"""The cold-bootstrap state disappears: a metadata-less tree reads as if it
carried bookkeeping, which is exactly the misclassification the union's
metadata-less member exists to refuse."""

_UNSERVICEABLE_MISREAD = Sabotage(
    module="root.py",
    before=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""'
    ),
    after=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""\n'
        "    state = _read_lifecycle_state_unsabotaged(root)\n"
        "    if state is LifecycleState.READ_ONLY_UNSERVICEABLE:\n"
        "        return LifecycleState.WRITABLE\n"
        "    return state\n"
        "\n"
        "\n"
        "def _read_lifecycle_state_unsabotaged(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""'
    ),
)
"""A replica's read-only stamp reads as a grant: the exact confusion the
stamp-before-exposure ordering exists to make impossible."""

_MISMATCH_MISREAD = Sabotage(
    module="root.py",
    before=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""\n'
        "    target = Path(root)"
    ),
    after=(
        "def read_lifecycle_state(root: Path) -> LifecycleState:\n"
        '    """The closed five-value lifecycle union, validated while reading."""\n'
        "    state = _read_lifecycle_state_shadowed(root)\n"
        "    if state is LifecycleState.BINDING_MISMATCHED:\n"
        "        return LifecycleState.WRITABLE\n"
        "    return state\n"
        "\n"
        "\n"
        "def _read_lifecycle_state_shadowed(root: Path) -> LifecycleState:\n"
        "    target = Path(root)"
    ),
)
"""A mismatched binding reads as the state the bytes claim — the rebind the
binding rule refuses, performed by the reader instead."""

_METADATA_FOR_IDENTITY = Sabotage(
    module="root.py",
    before="    root = Path(corpus_root)\n    return root.with_name(root.name + METADATA_SUFFIX)",
    after="    root = Path(corpus_root)\n    return root",
)
"""The metadata sibling collapses onto the root itself: every derived carrier
path is wrong, and every act that rests on the one derivation rule fails."""

_UNANCHORED_VALIDATES = Sabotage(
    module="world/verify.py",
    before=(
        "    # Step 2 — anchors.\n"
        "    if not bound:\n"
        "        return _report(\n"
        '            "unresolvable",'
    ),
    after=(
        "    # Step 2 — anchors.\n"
        "    if not bound:\n"
        "        return _report(\n"
        '            "validated",'
    ),
)
"""An empty bound set stops being the honest non-answer: nothing anchors the
chain and the evaluator vouches for it anyway."""

_GRANT_SKIPPED = Sabotage(
    module="world/verify.py",
    before=(
        "        if report.outcome == \"validated\" and _restore_subject_agrees(\n"
        "            subject, kind, view, presented\n"
        "        ):\n"
        "            grant(root)"
    ),
    after=(
        "        if report.outcome == \"validated\" and _restore_subject_agrees(\n"
        "            subject, kind, view, presented\n"
        "        ):\n"
        "            pass"
    ),
)
"""Restore judges and never admits: the grant that separates evaluation from
admission is silently dropped."""


CUT9_ARMS: tuple[Arm, ...] = (
    # --- L2: settlement gates every absence test (the re-read unit) ----------
    Arm(
        row="L2u1",
        asserts=(
            "a metadata-less copied root refuses mutation at the writability gate first while its chain "
            "evaluation still reads unresolvable at step 3 with the pending entry named, and the certified "
            "PendingUnresolved class survives on the writable live-root construction — label 11's precedence "
            "ruling exercised over the copied-root construction (chain with a pending entry, no metadata)"
        ),
        sabotage=_EXECUTOR_REFUSAL_VOICE,
        checks=(
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_copy_refuses_mutation_at_the_writability_gate",
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_writable_pending_root_still_refuses_pending_unresolved",
        ),
    ),
    # --- L4: chain removal refutes against any surviving anchor --------------
    Arm(
        row="L4u1",
        asserts=(
            "delete a store's chain while its store-subject registry record is in the observer set → refuted, "
            "the subject binding associating the anchor by store_id, never by elimination"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before=(
                "        if bound:\n"
                '            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))'
            ),
            after=(
                "        if bound and False:\n"
                '            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))'
            ),
        ),
        checks=(
            "test_store_subjects.py::test_store_audit_refuted_on_chain_removal_under_registry_anchor",
        ),
    ),
    Arm(
        row="L4u2",
        asserts=(
            "replace an anchored fork's chain with a self-consistent chain under a different fork genesis, "
            "same child subject, original anchor supplied → refuted as replacement — the genesis-mismatch "
            "mechanism firing for a corpus, now constructible under the fork genesis"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before="    refutations = _anchor_refutations(bound, view.genesis.digest, positions)",
            after="    refutations = ()",
        ),
        checks=("test_fork_acts.py::TestTheL6Lift::test_two_fork_geneses_same_child_subject_refute",),
    ),
    # --- L6: the fork-baseline lift ------------------------------------------
    Arm(
        row="L6u1",
        asserts=(
            "fork, anchor the fork, delete one baseline-covered pre-log member (the only delta) → refuted at "
            "replay; the fixture asserts the member is in the fork genesis's baseline and in no post-genesis "
            "entry"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before="        for path in sorted(set(modeled) | set(scanned))",
            after="        for path in sorted(set(scanned))",
        ),
        checks=("test_fork_acts.py::TestTheL6Lift::test_l6_anchored_baseline_deletion_refutes",),
    ),
    Arm(
        row="L6u2",
        asserts=(
            "a consistent rewrite of genesis, baseline, and chain omitting the member, with no surviving "
            "anchor, is unresolvable — never validated and never refuted; the fixture asserts byte-difference "
            "and full omission"
        ),
        sabotage=_UNANCHORED_VALIDATES,
        checks=("test_fork_acts.py::TestTheL6Lift::test_l6_anchor_free_rewrite_is_unresolvable",),
    ),
    # --- L10: restore, replication, and the residue windows ------------------
    Arm(
        row="L10u1",
        asserts=(
            "the fork genesis's forked_from equals the parent's genesis and head digests at the bound "
            "snapshot, and its baseline equals the destination surface after overrides"
        ),
        sabotage=Sabotage(
            module="root.py",
            before='            "forked_from": {"genesis": forked_from[0], "head": forked_from[1]},',
            after='            "forked_from": {"genesis": forked_from[0], "head": forked_from[0]},',
        ),
        checks=(
            "test_fork_acts.py::TestForkCorpus::test_fork_genesis_carries_parent_digests_and_nonempty_baseline",
        ),
    ),
    Arm(
        row="L10u2",
        asserts=(
            "a parent anchor in a fork-subject observer set contributes to no genesis or ancestry judgment: "
            "the subject filter discards it before any comparison"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before=(
                "            if anchor.subject != subject:\n"
                "                continue"
            ),
            after=(
                "            if anchor.subject != subject and False:\n"
                "                continue"
            ),
        ),
        checks=(
            "test_fork_acts.py::TestTheL6Lift::test_parent_anchor_never_compared_in_fork_subject_evaluation",
        ),
    ),
    Arm(
        row="L10u3",
        asserts=(
            "a completed replica reads read-only unserviceable while its source stays writable, and the "
            "replica's chain arrives byte-identical"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=(
                "        str(dest),\n"
                "        str(metadata_root_for(dest)),\n"
                "        PRODUCTION_STORAGE,\n"
                "    )\n"
                "\n"
                "\n"
                "def read_lifecycle_state"
            ),
            after=(
                "        str(dest),\n"
                "        str(metadata_root_for(source)),\n"
                "        PRODUCTION_STORAGE,\n"
                "    )\n"
                "\n"
                "\n"
                "def read_lifecycle_state"
            ),
        ),
        checks=(
            "test_lifecycle_wrappers.py::TestReplication::test_completed_replica_reads_read_only_unserviceable",
            "test_lifecycle_wrappers.py::TestReplication::test_replica_chain_is_byte_identical",
        ),
    ),
    Arm(
        row="L10u4",
        asserts=(
            "the replica's read-only stamp is durable before any destination tree byte is exposable — the "
            "engine-interior order is atoms-certified (cited); the Science-observable residue is that a "
            "completed replica reads read-only unserviceable, never writable"
        ),
        sabotage=_UNSERVICEABLE_MISREAD,
        checks=(
            "test_lifecycle_wrappers.py::TestReplication::test_completed_replica_reads_read_only_unserviceable",
        ),
    ),
    Arm(
        row="L10u5",
        asserts=(
            "the pre-stamp window's residue classifies metadata-less — the claim-only destination is "
            "bookkeeping, not a stamped root; the window's construction is atoms-certified (cited), and the "
            "Science-observable residue is the metadata-less reading with mutation refused"
        ),
        sabotage=_METADATA_LESS_MISREAD,
        checks=(
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation",
        ),
    ),
    Arm(
        row="L10u6",
        asserts=(
            "a cold copied root — corpus and store alike — reads metadata-less and refuses cooperative "
            "mutation at the writability gate"
        ),
        sabotage=_METADATA_LESS_MISREAD,
        checks=(
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_copy_refuses_mutation_at_the_writability_gate",
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation",
        ),
    ),
    Arm(
        row="L10u7",
        asserts=(
            "an interrupted fork resumes with the original child identity, never a re-mint; the pre-grant "
            "read-only window is atoms-certified (cited), and the Science half is the resume-before-mint "
            "branch returning the same corpus_id"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=(
                "    pending = _fork_pending(dest)\n"
                "    if pending is not None:\n"
                "        _fork_resume(dest, pending)\n"
                "        return _registry.load_manifest(dest)\n"
                "\n"
                "    parent_manifest"
            ),
            after=(
                "    pending = None\n"
                "    if pending is not None:\n"
                "        _fork_resume(dest, pending)\n"
                "        return _registry.load_manifest(dest)\n"
                "\n"
                "    parent_manifest"
            ),
        ),
        checks=(
            "test_fork_acts.py::TestForkRetry::test_fork_retry_reuses_the_original_child_identity",
        ),
    ),
    Arm(
        row="L10u8",
        asserts=(
            "the store half of the cold bootstrap: a metadata-less store copy reads metadata-less and refuses "
            "mutation — the holdings-read clauses stay deferred by the cut"
        ),
        sabotage=_METADATA_LESS_MISREAD,
        checks=(
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation",
        ),
    ),
    Arm(
        row="L10u9",
        asserts=(
            "two metadata-less copies of one store_id both restore to read-only serviceable, cooperative "
            "writes refused on each; the fixture asserts both were metadata-less first"
        ),
        sabotage=_GRANT_SKIPPED,
        checks=("test_restore_root.py::TestStoreRestore::test_two_copies_both_admit_read_only",),
    ),
    Arm(
        row="L10u10",
        asserts=(
            "an incomplete copy — one payload file the chain's surface names omitted, never chain damage — "
            "never validates, and the root stays unserviceable"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before='        "refuted" if result.refuted else "validated",',
            after='        "validated",',
        ),
        checks=("test_restore_root.py::TestStoreRestore::test_incomplete_copy_never_validates",),
    ),
    Arm(
        row="L10u11",
        asserts=(
            "an empty observer set is unresolvable with replay not reached: the report's observer_bound is "
            "empty and the root stays unserviceable"
        ),
        sabotage=_UNANCHORED_VALIDATES,
        checks=(
            "test_restore_root.py::TestStoreRestore::test_empty_observer_set_unresolvable_replay_not_reached",
        ),
    ),
    Arm(
        row="L10u12",
        asserts=(
            "the divergence triple: two divergent copies assembled in one root are sibling-malformed; both "
            "divergent heads in one observer set refute; verified separately each validates — the pinned "
            "surviving-observer negative stated as the claim"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before="    return LogReport(outcome, anchored_through, unanchored_tail, pending, intents, bound, findings)",
            after='    return LogReport("unresolvable", anchored_through, unanchored_tail, pending, intents, bound, findings)',
        ),
        checks=(
            "test_restore_root.py::TestDivergentCopies::test_divergent_copies_assembled_in_one_root_are_sibling_malformed",
            "test_restore_root.py::TestDivergentCopies::test_both_divergent_heads_in_one_observer_set_refute",
            "test_restore_root.py::TestDivergentCopies::test_divergent_copies_verified_separately_each_validate",
        ),
    ),
    # --- W13: the fork constructor -------------------------------------------
    Arm(
        row="W13u1",
        asserts=(
            "fork_corpus mints a fresh opaque corpus_id independent of path and name: two forks of one parent "
            "mint distinct ids, each carrying the parent's id and corpus-state identity"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=(
                "    corpus_state = _registry.corpus_state_identity(source)\n"
                "    child_id = secrets.token_hex(16)"
            ),
            after=(
                "    corpus_state = _registry.corpus_state_identity(source)\n"
                '    child_id = "c" * 32'
            ),
        ),
        checks=(
            "test_fork_acts.py::TestForkCorpus::test_fork_corpus_mints_a_fresh_id_independent_of_path_and_name",
        ),
    ),
    Arm(
        row="W13u2",
        asserts=(
            "the fork constructor's completeness and binding: the destination manifest is complete the moment "
            "the root reads writable, a moved source refuses SourceSnapshotMoved with nothing minted, and the "
            "fork product admits through World.admit's ForkOf path with no fixture-authored manifest — the "
            "admission integration homed here because its falsification is the fork derivation's, which "
            "label 8's verify-side sabotage cannot reach"
        ),
        sabotage=_METADATA_FOR_IDENTITY,
        checks=(
            "test_fork_acts.py::TestForkCorpus::test_fork_manifest_is_complete_before_writability",
            "test_fork_acts.py::TestForkCorpus::test_source_moved_between_derivation_and_fork_refuses",
            "test_arrival_modes.py::test_fork_product_admits_through_the_fork_of_path",
        ),
    ),
    # --- §3.3's eleven labels -------------------------------------------------
    Arm(
        row="V1",
        asserts=(
            "the initialization-operation grant discipline: over the durable-genesis/no-grant state, the "
            "retry matching the recorded operation — and only it — completes the grant and returns the "
            "original id; a bare matching existing genesis never grants (order cited to atoms)"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=(
                "    store_root.mkdir(parents=True, exist_ok=True)\n"
                "    existing = _read_existing_store_genesis(store_root)"
            ),
            after=(
                "    store_root.mkdir(parents=True, exist_ok=True)\n"
                "    existing = None"
            ),
        ),
        checks=(
            "test_store_root.py::TestInitStoreRoot::test_interrupted_init_retry_returns_the_original_store_id",
            "test_store_root.py::TestInitStoreRoot::test_cold_existing_store_root_refuses_reinitialization",
        ),
    ),
    Arm(
        row="V2",
        asserts=(
            "no grant honored without a matching root/host binding: a single-delta edit — host, then path — "
            "reads binding-mismatched through the Science wrapper, never the state the bytes claim; the "
            "moved-root consequence is the path delta (atoms deltas cited)"
        ),
        sabotage=_MISMATCH_MISREAD,
        checks=(
            "test_lifecycle_wrappers.py::TestTheStateRead::test_binding_delta_reads_binding_mismatched",
        ),
    ),
    Arm(
        row="V3",
        asserts=(
            "the migration: the operator-authorized success grants with a fresh binding and reads writable; "
            "metadata-less roots and binding mismatches never migrate; provenance is attested, not proven"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=(
                "    target = Path(root)\n"
                "    _migrate_root_to_lifecycle_v3_callback(\n"
                "        _PRODUCTION_BACKEND,\n"
                "        str(target),\n"
                "        str(metadata_root_for(target)),"
            ),
            after=(
                "    target = Path(root)\n"
                "    _migrate_root_to_lifecycle_v3_callback(\n"
                "        _PRODUCTION_BACKEND,\n"
                "        str(target),\n"
                "        str(target),"
            ),
        ),
        checks=(
            "test_lifecycle_wrappers.py::TestMigration::test_migration_authorized_success_reads_writable",
            "test_lifecycle_wrappers.py::TestMigration::test_migration_refuses_metadata_less_and_mismatched",
        ),
    ),
    Arm(
        row="V4",
        asserts=(
            "no-clobber and the operation identity: both copy commands claim destination exclusivity durably "
            "at start, and fork retry splits at the grant (the split's interior cited to atoms) — falsified "
            "through the one metadata derivation every copy act's claim rests on"
        ),
        sabotage=_METADATA_FOR_IDENTITY,
        checks=(
            "test_lifecycle_wrappers.py::TestReplication::test_replicate_refuses_an_existing_destination",
            "test_fork_acts.py::TestForkRetry::test_fork_retry_reuses_the_original_child_identity",
        ),
    ),
    Arm(
        row="V5",
        asserts=(
            "the grant primitive is structural, idempotent, and out-of-band outside restore: restore's "
            "validated store copy admits read-only serviceable through the cold-root creation path, a second "
            "restore is a no-write success, and nothing ever grants writability; the out-of-band pinning is "
            "this declaration's stated negative — the grant beside raw bookkeeping edits and raw rm, the "
            "bound every detection claim's cooperative-write quantification carries (atoms grant arms cited)"
        ),
        sabotage=_GRANT_SKIPPED,
        checks=(
            "test_restore_root.py::TestStoreRestore::test_validated_store_copy_admits_read_only_serviceable",
            "test_restore_root.py::TestStoreRestore::test_re_restore_is_idempotent",
            "test_restore_root.py::TestStoreRestore::test_restore_never_grants_writability",
        ),
    ),
    Arm(
        row="V6",
        asserts=(
            "the lifecycle union is closed at five, and the mismatch is its own declared state, never the "
            "state the bookkeeping's bytes claim (the metadata-less member's atoms reading cited)"
        ),
        sabotage=Sabotage(
            module="root.py",
            before='STORE_GENESIS_DOMAIN = "science.store-root.v1"',
            after=(
                'STORE_GENESIS_DOMAIN = "science.store-root.v1"\n'
                "\n"
                "import enum as _shadow_enum\n"
                "\n"
                "\n"
                "class LifecycleState(_shadow_enum.StrEnum):  # noqa: F811\n"
                '    WRITABLE = "writable"\n'
                '    READ_ONLY_SERVICEABLE = "read-only-serviceable"\n'
                '    READ_ONLY_UNSERVICEABLE = "read-only-unserviceable"\n'
                '    METADATA_LESS = "metadata-less"\n'
                '    BINDING_MISMATCHED = "binding-mismatched"\n'
                '    LEGACY = "legacy"'
            ),
        ),
        checks=(
            "test_lifecycle_wrappers.py::TestTheStateRead::test_lifecycle_union_is_closed_at_five",
            "test_lifecycle_wrappers.py::TestTheStateRead::test_binding_delta_reads_binding_mismatched",
        ),
    ),
    Arm(
        row="V7",
        asserts=(
            "restore_root is one held boundary — inspect, capture the presented identity and surface, "
            "evaluate, gate on subject agreement, grant — malformed views flowing into the evaluator, a "
            "validated-with-mismatch report admitting nothing, and writability never granted"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before=(
                "    root = Path(dest_root).resolve()\n"
                "    with _subject_hold(seam, kind, root):\n"
                "        view, disk, presented = _assemble_evaluation_inputs(seam, kind, root, None)"
            ),
            after=(
                "    root = Path(dest_root).resolve()\n"
                "    if root:\n"
                '        return _report("unresolvable", findings=(_unanchored_finding(subject),))\n'
                "    with _subject_hold(seam, kind, root):\n"
                "        view, disk, presented = _assemble_evaluation_inputs(seam, kind, root, None)"
            ),
        ),
        checks=(
            "test_restore_root.py::TestStoreRestore::test_malformed_copy_returns_malformed_and_stays_unserviceable",
            "test_restore_root.py::TestStoreRestore::test_validated_with_store_subject_mismatch_does_not_admit",
            "test_restore_root.py::TestCorpusRestore::test_validated_with_corpus_manifest_mismatch_does_not_admit",
            "test_restore_root.py::TestStoreRestore::test_restore_never_grants_writability",
            "test_restore_root.py::TestTheHeldBoundary::test_restore_holds_one_boundary_across_evaluate_and_grant",
        ),
    ),
    Arm(
        row="V8",
        asserts=(
            "the arrival boundary is lifecycle-aware and corpus-only: registered inspection on read-only "
            "serviceable, detached on unserviceable, metadata-less, and mismatched, a typed refusal on "
            "writable, restore-then-arrive switching modes, and a store unspellable in the signature — the "
            "fork-of admission integration is W13 u2's check, homed with the derivation its falsification "
            "follows"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before=(
                "    if type(provenance) is not registry.ReplicaOf:\n"
                "        raise TypeError(\n"
                '            "admit_arrival is the verified route for a replica: fresh and fork provenance are World.admit\'s"\n'
                "        )\n"
                "    if history is not None:\n"
                "        validate_history(history)\n"
                "    subject = anchors.CorpusSubject(provenance.parent_corpus_id)\n"
                "    root = Path(corpus_root).resolve()\n"
                "    state = seam.lifecycle_state(root)\n"
                '    if state == "writable":\n'
                "        raise CorpusRootRefused(\n"
                '            f"{root}: a writable root is this host\'s own live root, not an "\n'
                '            "arrival; nothing arrives at the root it already is"\n'
                "        )\n"
                "    with seam.world_lock(world.config.world_root), seam.corpus_lock(root):\n"
                "        # The inspection mode follows the lifecycle state: a restored,\n"
                "        # read-only-serviceable copy earned the coherent registered read;\n"
                "        # every other non-writable state — unserviceable, metadata-less,\n"
                "        # binding-mismatched — is detached, its pending honestly unresolved.\n"
                "        inspect = (\n"
                "            seam.inspect_registered\n"
                '            if state == "read-only-serviceable"\n'
                "            else seam.inspect_detached\n"
                "        )"
            ),
            after=(
                "    if history is not None:\n"
                "        validate_history(history)\n"
                "    subject = anchors.CorpusSubject(provenance.parent_corpus_id)\n"
                "    root = Path(corpus_root).resolve()\n"
                "    state = seam.lifecycle_state(root)\n"
                "    with seam.world_lock(world.config.world_root), seam.corpus_lock(root):\n"
                "        inspect = (\n"
                "            seam.inspect_detached\n"
                '            if state == "read-only-serviceable"\n'
                "            else seam.inspect_registered\n"
                "        )"
            ),
        ),
        checks=(
            "test_arrival_modes.py::test_arrival_registered_mode_on_serviceable",
            "test_arrival_modes.py::test_arrival_detached_on_unserviceable_metadata_less_and_mismatched",
            "test_arrival_modes.py::test_arrival_refuses_a_writable_root",
            "test_arrival_modes.py::test_restored_arrival_requires_restore_first",
            "test_arrival_modes.py::test_store_subject_unspellable_at_arrival",
        ),
    ),
    Arm(
        row="V9",
        asserts=(
            "the store acts bind by genesis: anchor_heads and export_head_artifact alike verify the supplied "
            "root's genesis carries the named store_id before any head is accepted, exported, or recorded — "
            "the audited pair here is the shared binding refusal; the export round-trip and the store audit's "
            "one-boundary hold stand un-sabotaged in the ordinary suite "
            "(test_store_subjects' round-trip and hold nodes), because their mechanisms are the codec's and "
            "the lock's, not this binding's — the narrowing this declaration records"
        ),
        sabotage=Sabotage(
            module="world/anchors.py",
            before="    if named != store_id:",
            after="    if named != store_id and False:",
        ),
        checks=(
            "test_store_subjects.py::test_anchor_refuses_a_store_id_genesis_mismatch_before_registry_mutation",
            "test_store_subjects.py::test_export_refuses_a_store_genesis_mismatch",
        ),
    ),
    Arm(
        row="V10",
        asserts=(
            "store construction and the canonical projection: a populated root refuses initialization, and "
            "the store surface is the whole non-bookkeeping namespace with symlinks never followed; the "
            "payload codec round-trip and the non-fork empty-baseline rule stand un-sabotaged in the ordinary "
            "suite (test_store_root's round-trip node and test_fork_acts' non-fork baseline node), because no "
            "single projection mutation falsifies them with these checks — the narrowing this declaration "
            "records"
        ),
        sabotage=Sabotage(
            module="world/verify.py",
            before=(
                '    if kind == "store":\n'
                "        # The whole-namespace projection: a store's payload is opaque, so\n"
                "        # every non-bookkeeping root-relative entry is claimed. The walker's\n"
                "        # own dot-prefix rule already excludes exactly bookkeeping — the\n"
                "        # chain leaf, the root claim, engine metadata — and nothing else,\n"
                "        # and symlinks stay leaves here as everywhere.\n"
                '        return tuple(sorted(_files_beneath(root, "")))'
            ),
            after=(
                '    if kind == "store":\n'
                "        return ()"
            ),
        ),
        checks=(
            "test_store_root.py::TestInitStoreRoot::test_init_store_root_refuses_a_populated_payload_root",
            "test_store_root.py::TestStoreSurface::test_store_surface_excludes_bookkeeping",
            "test_store_root.py::TestStoreSurface::test_store_surface_does_not_follow_symlinks",
        ),
    ),
    Arm(
        row="V11",
        asserts=(
            "the writability-gate precedence: the coordinator's unconditional gate refuses a metadata-less "
            "copied root before the pending gate can speak, while a writable pending root still refuses "
            "through the pending gate — the ruling L2 u1 exercises, single-homed there and cited here"
        ),
        sabotage=_EXECUTOR_REFUSAL_VOICE,
        checks=(
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_metadata_less_copy_refuses_mutation_at_the_writability_gate",
            "test_lifecycle_wrappers.py::TestTheWritabilityGate::test_writable_pending_root_still_refuses_pending_unresolved",
        ),
    ),
)
