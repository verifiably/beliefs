# Root lifecycle — execution ledger, world-index slice 4

Plan: `docs/superpowers/plans/2026-08-23-root-lifecycle.md`
Specification: `docs/superpowers/specs/2026-08-23-world-index-root-lifecycle-design.md`
Frozen cut: `docs/designs/2026-08-23-conformance-cut-9.md`
Freeze hash: `0977bde`

## Rulings

1. **R1 — reviewed authority.** Atoms-side human review closed on 2026-08-23.
   Findings landed through `6555e46`; the approved status head is `b1469f4`.
   That document's DDL, public signatures, serialization, durability order,
   and retry/error dispositions are Task 2's binding contract.
2. **R2 — carrier and transition.** Lifecycle/binding and retained
   root-creation operation evidence live in the existing `atoms.db`. Store
   schema v3 is exact v2 plus `root_lifecycle`, `root_operation`, and the ten
   reviewed triggers; exact v2 is read-only unserviceable until the explicit
   `migrate_root_to_lifecycle_v3` operator transition.
3. **R3 — closed state and binding.** `LifecycleState` is the closed five-value
   enum writable / read-only serviceable / read-only unserviceable /
   metadata-less / binding-mismatched. Every stored grant binds the stable
   machine identity and canonical root path; mismatch conveys no grant and no
   writable rebind exists.
4. **R4 — claim-only pre-stamp refinement.** A mode-`0o700` destination
   directory containing only the mode-`0o600` reserved `.#~root-claim` may be
   published before the lifecycle stamp. Its no-clobber rename is the
   filesystem-level cross-metadata-carrier ownership point. The claim is
   excluded from surfaces and snapshots; no payload, chain, override,
   lifecycle stamp or grant, or serviceability exists before the stamp.
5. **R5 — public API.** Task 2 exports `LifecycleState`, `RootOperationId`,
   `DestinationOverride`, `replicate_root`, `fork_root`,
   `read_pending_fork_operation`, `resume_fork_root`,
   `grant_read_serviceability`, `read_lifecycle_state`, and
   `migrate_root_to_lifecycle_v3` with the exact Task 1 signatures.
   `SourceSnapshotMoved` and `RootOperationMismatch` subclass
   `PreconditionRefused`; `RootOperationInvalid` subclasses `AtomsError`.
6. **R6 — identity and exact retry.** Canonical request bytes, not a hash
   alone, bind the retained 32-hex operation ID. Fork request bytes include
   the expected source head, opaque genesis, surfaces, and overrides. Science
   queries pending destination evidence before minting and resumes by retained
   ID, so a retry never re-mints the child; changed input is
   `RootOperationMismatch` and a required moved source is
   `SourceSnapshotMoved`.
7. **R7 — path and lock order.** Source root, source metadata root,
   destination root, and destination metadata root are pairwise
   non-overlapping. Fresh copies acquire source blocking then destination
   nonblocking; busy destination is
   `PreconditionRefused("copy destination lock is busy")`. Retry begins at
   the destination and opens the source only for bytes destination proof says
   are missing.
8. **R8 — writability and read coherence.** `_existing_read_only_lease`
   performs no recovery-capable or sidecar-creating write. Cooperative
   mutation of existing roots requires a validated writable grant before
   recovery, reclamation, probing, or chain append. Recorded root-creation
   operations are the sole pre-grant write exception.
9. **R9 — serviceability.** The serviceability grant is structural and has no
   verdict/attestation parameter. It refuses writable, binding-mismatched,
   exact-v2, incomplete-operation, `.#~root-claim`, and chain-staging residue;
   repeated success on an already-serviceable root uses the no-write path.
10. **R10 — Science initialization refusal.** Task 3 preserves `b3a965c`'s
    reviewed boundary: an atoms `PreconditionRefused` on the existing-genesis
    retry maps to Science's established `CorpusRootRefused`; it is not exposed
    as a new initialization error or treated as permission to re-mint.
11. **R11 — Task 2 discharged.** The atoms implementation landed on
    `design/root-lifecycle` (`23019b0` writer state/binding/query, `24b15ce`
    copy commands/grant/migration) and merged `--no-ff` to atoms `main` at
    `ff144e7`, pushed. Gates from the atoms worktree's `python/` under
    `pipefail`: pytest's own summary line read
    `6205 passed, 7 skipped in 494.23s (0:08:14)`; `ruff check .` reported
    "All checks passed!"; `pyright` reported "0 errors, 0 warnings,
    0 informations".
12. **R12 — completed-retry precedence.** Under the reviewed §8, a completed
    `register_root` retry answers from its retained operation record without
    touching the chain, so the pending-registration gate now binds exactly
    the two chain mutators; the atoms pending-gate test was re-pinned to
    that reading.
13. **R13 — carrier-less reads are the detached mode's.** `read_chain` and
    `inspect_chain` are lifecycle-gated: a metadata-less or binding-mismatched
    root refuses (a live transaction record without a grant stays
    `ChainStateInvalid`), non-writable v3 roots are served through the
    quiescent read-only entry, and the structural taxonomy over carrier-less
    trees is `inspect_chain_detached`'s alone. Three atoms chain-inspection
    tests were re-pinned accordingly.
14. **R14 — Task 3 discharged.** `init_store_root` mints the opaque
    32-lowercase-hex `store_id`, refuses a populated root, returns the
    original id over an interrupted init through `register_root`'s own
    recorded-operation retry, and maps the engine's `PreconditionRefused`
    on every other existing-genesis carrier to `CorpusRootRefused` (R10's
    boundary). `registered_surface_paths` gained the `"store"` arm — the
    whole-namespace projection through the one existing walker. The
    boundary roster gained the seven lifecycle command names, and
    `register_root`'s call-site registry records `init_store_root`'s two
    sites. `test_world_log_replay.py::test_an_unclaimed_kind_refuses`
    re-pinned to "holdings", the next unclaimed kind. Gates under
    `pipefail`: `3 failed, 2187 passed in 438.74s (0:07:18)` — the three
    known pre-banking documentation failures assigned to Task 11 — with
    ruff "All checks passed!", pyright at its four known baseline
    diagnostics, and `tools/cut7_acceptance.py` exit 0.
15. **R15 — cut 8's store-refusal declarations are deliberately stale from
    Task 4 on.** This task deletes `_refuse_store_subject` and
    `StoreSubjectUnsupported`: the shape-only refusal cut 8's label 6 and its
    store-refusal arms certify no longer exists on the current tree, so those
    declarations fail from this commit forward **by design**. Cut 8's
    discharge stands as its frozen results record
    (`docs/plans/2026-08-22-conformance-cut-8-results.md`), not as a
    current-tree invariant; `tools/cut7_acceptance.py` is the standing
    current-tree prefix (exit 0 after this task), and cut 9's store units are
    the successor certification.
16. **R16 — Task 4 discharged.** Store subjects act: `anchor_heads` takes
    `store_roots` pairs and verifies the genesis carries the named
    `store_id` before head acceptance or registry mutation;
    `export_head_artifact` takes a supplied `store_root` under the same
    binding; the audit path judges a store root through the four-outcome
    evaluator over the supplied root (a store is configured nowhere), with
    the corpus/store-shared per-root operation lock as its one hold. The
    store genesis form lives in `anchors.parse_store_genesis` — the L6
    fork-baseline lift admits a populated baseline exactly when the payload
    states `forked_from`. One addition beyond the plan's file list:
    `StoreIdMismatch` in `science/errors.py`, the store analog of
    `WorldIdMismatch`, because the acts' binding refusal fits no existing
    error and `LogEvidenceRefused`'s closed constructor is the engine
    seam's. Gates: `3 failed, 2200 passed in 394.69s (0:06:34)` (the three
    known Task-11 documentation failures), ruff clean, pyright at its four
    baseline diagnostics, cut-7 acceptance exit 0.
17. **R17 — carrier-less registered inspection serves the detached
    classification.** R13's inspect claim is corrected: refusing
    `inspect_chain` over a metadata-less root made a cold copy's chain
    unjudgeable through the audit act, which cut 9 L2 u1 requires
    (`unresolvable at step 3` over the copied root). Atoms `fb95e1a`
    (merged/pushed at `bf559c2`) answers a carrier-less registered
    inspection with the detached classification — non-coherent,
    non-mutating, staging as evidence — while a live record without a
    grant stays `ChainStateInvalid`, `read_chain` still refuses without a
    grant, and binding-mismatched roots refuse both.
18. **R18 — Task 5 discharged.** The Science wrappers `replicate_root`,
    `read_lifecycle_state`, and `migrate_root_to_lifecycle_v3` land as
    thin Path-taking passthroughs over the callback aliases; the engine
    command names arrive as aliased imports (the boundary roster now
    counts import sources on both sides of the confinement), and the
    unused fork/restore callbacks are held with the boundary until their
    tasks. The gate-precedence pair is pinned live: a metadata-less copy
    refuses mutation at the writability gate while its chain evaluation
    reads unresolvable with the pending entry named, and a writable
    pending root still refuses through the pending gate. Real-engine
    tests run under `certified_work`, a per-test directory on the
    repository's own certified volume. Gates: `3 failed, 2212 passed in
    344.87s (0:05:44)` (the three known Task-11 documentation failures),
    ruff clean, pyright at its four baseline diagnostics, cut-7
    acceptance exit 0.
19. **R19 — Task 6 discharged.** `restore_root(dest_root, subject,
    observers) -> LogReport` lands: one held per-root boundary spanning
    inspection, the presented claim, capture, evaluation, the subject gate,
    and the grant, with `_assemble_evaluation_inputs` factored out of
    `_audit_log` as the exact shared boundary (no third assembly). The
    subject gate is a separate lifecycle precondition: `validated` with a
    disagreeing store genesis id or corpus manifest id returns the report
    and admits nothing. A grant refusal over creation residue (root claim,
    staging survivor) propagates loudly out of the restore — fail-closed,
    the report forfeited to the refusal. Two slice facts pinned by the
    fixtures: an empty initialized store validates while raw payload
    replays as a disagreement (holdings are the next slice's row), and a
    raw-authored fork-form genesis (payload with `forked_from`, baseline
    naming the surface) is how a chain names payload before the fork acts
    land. The divergence triple reads: assembled-in-one-root is sibling
    malformed, both heads in one observer set refute, and separately each
    validates — the pinned surviving-observer negative stated as the
    claim. Gates: `3 failed, 2228 passed in 346.35s (0:05:46)` (the three
    known Task-11 documentation failures), ruff clean, pyright at its four
    baseline diagnostics, cut-7 acceptance exit 0.

## Heads

| Task | Atoms head | Science head |
| --- | --- | --- |
| 0 — tracking setup | — | `7db3e38` |
| 1 — reviewed atoms design and Science contract amendment | `b1469f4` | this amendment commit |
| 2 — atoms lifecycle implementation | `ff144e7` (merge of `24b15ce`) | this ledger commit |
| 3 — store roots and the store projection | `ff144e7` | `560c859` |
| 4 — store subjects through the verification surface | `ff144e7` | `8e14f8a` |
| 5 — lifecycle wrappers and gate precedence | `bf559c2` (merge of `fb95e1a`) | `ee590d2` |
| 6 — restore_root | `bf559c2` | this task's commit |
