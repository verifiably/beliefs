# Conformance cut 34 — correction-remainder, slice 2

**Status:** discharged 2026-09-19 on the certified volume; results: `../plans/2026-09-19-conformance-cut-34-results.md`.
**Design:** `../superpowers/specs/2026-09-19-correction-remainder-slice-2-design.md`, approved for implementation planning 2026-09-19 at `435e254` after three reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-19-correction-remainder-slice-2.md`.
**Numbered after** cut 33 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 34–39 at freeze; cut 33 is the highest discharged runner.

## 1. What this cut is

The baseline below describes `main` at `1958ec5`; `main` moved to `4605a2e`
by freeze with no commit touching `python/src/beliefs/`, so the baseline is
unchanged.

Slice 1 (cut 33) made standing a property of the read for the node and
route arms: the enumeration is derived, a standing retraction's node target
leaves the read set before decoding, and a route target retires its route.
What no cut has built is the fourth instantiation the correction design
names — the **semantic snapshot** — and the narrowing route that rests on
it.

This cut gives the retraction a third target arm, **`snapshot`**, naming a
producer subject by kind and identity; reads that subject's standing
**live** from the corpora its own coverage names; and reports or refuses it
at exactly the sites the correction design lists — import refuses before
any write, audit and the diagnostic query report `retracted`, and a world
read whose supplied snapshot is retracted refuses. Narrowing is then the
design's own composition: build the successor under the narrower coverage,
retract the old snapshot with `successor` naming the new one. Mounting
stays inert.

It reads C8 and C9 in full. The boundary closes with this cut and the
mutation lane has no further open boundary.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/errors.py`, `stored.py`, `corpus.py`, `audit.py`,
  `closure.py`, `evaluation.py`, `world/derive.py`, `world/epoch.py`,
  `world/read.py`, `world/view.py`, `world/audit.py`, `world/importing.py`,
  `world/registry.py`, and `session/writer.py`;
- `python/tests/test_snapshot_retraction.py`, `test_world_audit.py`, and
  `test_world_standing.py`;
- `python/tests/acceptance/test_snapshot_retraction_acceptance.py`,
  `python/tests/acceptance/n2_arms_cut34.py`,
  `python/tests/acceptance/test_n2_cut34.py`, and
  `python/tools/cut34_acceptance.py`;
- this cut, its results record, the adoption ledger, roadmap, guide, README,
  and the correction-lifecycle and world-index slice-2 amendments.

Frozen declarations and cut bodies through cut 33 remain byte-exact.

## 3. Selection

Seventeen declaration units are selected and single-homed here. The quoted
row text is byte-exact from correction lifecycle §7 at freeze.

```markdown
| C8 | A retracted snapshot is refused where recomputation already happens | import naming it refuses before any write; audit and diagnostic query report `retracted`; **negative:** mounting the corpus writes nothing and validates nothing |
| C9 | Narrowing is snapshot succession plus retraction, never mutation behind an identity | derive the narrowed successor snapshot, retract the old naming it as `successor`; assert the old snapshot's identity and its receipts are byte-unchanged, a computation naming the old hits C8's refusal, one naming the new proceeds, and the digest moves. **Negative:** nothing resolves through the retraction to the successor implicitly |
```

| unit | row | what it reads |
|---|---|---|
| C8-a | C8 | `import_epoch` of a carrier whose producer subject is retracted → `retracted-snapshot`, no directory |
| C8-b | C8 | `audit_epochs`: the producer receipt `retracted`, the verdict `retracted`, no finding names it |
| C8-c | C8 | `snapshot_state(S)` `retracted`; `snapshot_state(S')` `unchecked` (receipt `unresolvable`); `checked` for `S'` only between build and retraction |
| C8-d | C8 | mount negative: `World.admit` writes nothing under `epochs/`, validates nothing |
| C9-a | C9 | narrowing: `gather` bound to the old epoch refuses `ProducerSnapshotRetracted` |
| C9-b | C9 | bound to the new: proceeds, digest moves, `closure()["producer_snapshot"] == S'` |
| C9-c | C9 | old members and receipts byte-identical across the retraction |
| C9-d | C9 | nothing resolves through the retraction to its successor (two mismatch negatives) |
| BI-1 | — | a snapshot retraction outside the target's coverage is refused at authoring; inside is admitted |
| BI-2 | — | a writer without the port refuses the arm |
| BI-3 | — | `retracted` precedes availability (the moved state does not hide it) |
| BI-4 | — | a counter-retraction restores: not retracted, `gather` proceeds, nothing stored on the target |
| BI-5 | — | an older snapshot's retraction is out of the closure |
| BI-6 | — | the raw-write disposition: `audit_world` reports `retraction-target-invalid` from `captured_records`; `corpus_check` reports nothing |
| BI-7 | — | history is in the digest: counter-retracted ≠ never-retracted; `found` carries the pair |
| BI-8 | — | an unreadable counter-retraction refuses rather than restores, at `gather`, import and the reports (which still return) |
| BI-9 | — | a rebuild restores nothing and duplicates nothing |

## 4. Accounting

**17 declaration units**, eight against rows and nine boundary invariants;
C8 closes, C9 closes; the boundary closes.

## 5. N2 and acceptance obligations

Acceptance has one arm per declaration unit. Each N2 sabotage has a
byte-exact `before` block copied from the tree at freeze and parsed after
mutation.

| arm | module | sabotage | check |
|---|---|---|---|
| C8-a | `world/importing.py` | the `("retracted-snapshot", "retracted")` decision is removed | acceptance C8-a |
| C8-b | `world/audit.py` | `_reduce`'s `retracted` test → `if False:` | acceptance C8-b |
| C8-c | `world/read.py` | `_snapshot_standing` returns `None` unconditionally | acceptance C8-c (C8-a and C8-b fail with it; the arm's check is C8-c) |
| C8-d | `world/registry.py` | `_locked_admit` calls `read.validate_receipt` on the world's current epoch after the append | acceptance C8-d (the counting stub records one call) |
| C9-a | `evaluation.py` | `raise ProducerSnapshotRetracted(bound)` → `pass` | acceptance C9-a |
| C9-b | `closure.py` | `"producer_snapshot": producer_snapshot_identity` → `"producer_snapshot": ""` | acceptance C9-b (the digest no longer moves) |
| C9-c | `world/epoch.py` | `RetainedSnapshots.retained`, under the barrier it already holds, appends a `retracted: true` line to the named subject's `producer-receipt.yaml` in its retained carrier — standing stored on the target, the shape §4 of the design forbids | acceptance C9-c (the receipt is no longer byte-identical) |
| C9-d | `evaluation.py` | the mismatch check consults `view.snapshot_standing()` and accepts the successor named by a standing retraction | acceptance C9-d |
| BI-1 | `corpus.py` | the coverage clause of `_resolve_retraction_target`'s snapshot branch is removed | acceptance BI-1 |
| BI-2 | `corpus.py` | `snapshot_resolver is None` → returns instead of raising | acceptance BI-2 |
| BI-3 | `world/read.py` | `_snapshot_standing` is called after the availability phase | acceptance BI-3 |
| BI-4 | `corpus.py` | `snapshot_standing` puts every snapshot-arm retraction's identity in `retracted` regardless of `standing[r]` | acceptance BI-4 (`gather` still refuses after the counter-retraction) |
| BI-5 | `evaluation.py` | the scope loop's snapshot key is `f"producer-snapshot:{target['subject_identity']}"` and `scope` gains every retained identity | acceptance BI-5 (the older snapshot's retraction enters `found`) |
| BI-6 | `audit.py` | `audit_world`'s snapshot resolution is removed | acceptance BI-6 |
| BI-7 | `evaluation.py` | `history` is dropped from `scoped.found` | acceptance BI-7 (the digest equals the never-retracted one) |
| BI-8 | `corpus.py` | `snapshot_standing` skips `_resolve_retraction_target` for chain members | acceptance BI-8 (the broken counter-retraction overturns; `gather` proceeds) |
| BI-9 | `evaluation.py` | the scope loop's snapshot key is `f"producer-snapshot:{target['subject_identity']}"` and `scope` gains `f"producer-snapshot:{bound}"` | acceptance BI-9 (the rebuilt epoch's `found` carries the pair twice) |

Both directions are required: the check passes on the real tree and fails
under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut33_acceptance.py",)` and carries
`PHASE_MODULES = ("test_snapshot_retraction_acceptance.py",
"test_n2_cut34.py")`.

## 6. Second reader

Challenge the implicit-resolution attack C9's negative names. Verify that
C9-a and C9-b read the bound identity through `gather` exactly as the
caller supplies it, with no test-side selection of the epoch, and that
BI-7's two digests are compared over the *same* epoch.

## 7. Limitations

1. **A retraction's corpus can depart.** Decision 7 fails the read closed
   (`NoBelief`), and audit answers `unresolvable`. A departed corpus that
   held the only retraction of a snapshot therefore neither restores nor
   confirms it; the design's "detected at audit" holds and nothing here
   re-admits the snapshot. Filed as a limitation on the correction design.
2. **`move` of a snapshot retraction away from its counter-retraction** is
   slice 1 §11's split, unchanged; it now covers three arms.
3. **A raw computation that ignores retraction records** can still bind to
   a retracted epoch's bytes (`read.open_epoch` does not refuse). The
   design bounds "unusable" to boundaries and audit; the kernel has no
   process-level enforcement and this slice adds none. Recorded, not filed.
4. **Retracting the current epoch's snapshot with no successor** makes every
   world read bound to `current_epoch` refuse until a new epoch is built.
   Intended: the alternative — `current_epoch` skipping retracted epochs —
   is the implicit resolution C9's negative forbids. Recorded in the guide.
5. **A snapshot retraction makes every receipt covering the writing corpus
   `unresolvable` until a fresh epoch is built** — the successor's included
   (decision 1's consequence, §9 step 3). World-index §7.5's availability
   rule, unchanged; stated here because the narrowing route meets it on its
   first step. Recorded in the guide beside item 4.
6. **Other receipt subjects are not retractable** (decision 2).
7. **`build_epoch` republishes a retracted identity.** A rebuild under the
   retracted snapshot's coverage yields the same identity, is retained, and
   may become `current`; every read bound to it refuses and import of the
   same carrier elsewhere is refused, so the state is coherent but
   asymmetric. Whether build should refuse — a change to world-index §5.3's
   closed refusal surface — is filed as an idea at the cut, not decided
   here. A certification inventory or a coreference reduction is corrected
   by retracting the records it derives from. Recorded in the correction
   design's note.
