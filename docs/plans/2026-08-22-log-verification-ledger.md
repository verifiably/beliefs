# Log Verification and Anchoring Execution Ledger

**Plan:** `docs/superpowers/plans/2026-08-22-log-verification.md`  
**Spec:** `docs/superpowers/specs/2026-08-22-log-verification-design.md`  
**Cut:** `docs/designs/2026-08-22-conformance-cut-8.md`

## Rulings

**R1: Spec clarification — merge and push obligation (§8, §11)**

The spec's original wording in §8 ("and the merge-then-push obligation extending row 4's existing unpushed-`atoms` disclosure") and §11 step 4 ("the push obligation extending row 4's disclosure") implied the atoms head is pushed as part of this plan. This is clarified to match row 4's actual practice: the new atoms head joins row 4's recorded **unpushed** disclosure, and pushing remains a prerequisite of any integration expecting a fresh checkout to build (identical to `read_chain`'s `2c077ed` treatment).

Cost if wrong: A reader assumes the atoms head was pushed during this execution, creating ambiguity about which pushed state a fresh checkout integrates against. Follow-up: aligned the same duty terminology in §2's seam introduction ("merge-and-disclosure" duty).

**R2: Staging-leaf carve-out ratified with a tightening (atoms gate, 2026-08-22)**

The atoms design's reading — a `.#~stage` occupied by anything other than a
staging envelope is a foreign leaf — is ratified, tightened to: the
exemption covers **readable, no-follow regular staging files only**. Spec
§2.1's sentence amended accordingly. Cost if wrong: tamper at the reserved
name would be reclassified as bookkeeping, exactly what an arrival verdict
exists to catch.

**R3: Detached `pending` weakening ratified (atoms gate, 2026-08-22)**

Staged registration evidence stays in `pending`; detached pending digests
need not occur in `entries`. Spec §2.1 amended to state the weaker
invariant. Cost if wrong: a consumer resolving pending digests against
`entries` misses the staged pair — the spec now says not to.

**R4: Engine refusals get a boundary contract (atoms gate, 2026-08-22)**

`ChainStateInvalid` (chain-vs-record contradiction), `TransactionHalted`,
and capture's `PreconditionRefused` are translated by the root-owned seam
adapters into `LogEvidenceRefused(phase, engine_error, detail)` with
`__cause__` preserved — no `LogReport`, not `ArrivalRefused`, outside every
precedence. Spec gains §6.4; the plan's Task 4 seam, Task 8 and Task 9
tests amended. Cost if wrong: an audit of a contradicted or halted root
surfaces a bare engine exception instead of a contracted refusal.

**R5: The `fulfills` submission gate approved (atoms gate, 2026-08-22)**

Including the `test_coordinator_run.py:363` edit, with atoms ledger row
27's carriage assertion preserved verbatim — after the shared-helper claim
was corrected to cover only the referent checks, with the duplicate check
split to submission-time and settlement-time (the defect exists only at
the second committed settlement). Cost if wrong: either the engine can
mint chains its own validator condemns, or a discharged atoms ledger row
loses its verification.

**R6: Defect subjects and `AbsentChain` aligned across both documents
(atoms gate, 2026-08-22)**

`ORPHAN_HISTORY`'s subject is the lowest unvisited digest;
`DUPLICATE_FULFILLMENT`'s subject is the second committed settlement
digest; `AbsentChain` means **no durable chain claim** — directory absent,
or empty without contradictory live metadata — and arrival treats either
as chainless. Spec §2.1 and the plan's Task 4 `DefectView` mapping
amended; the atoms design already carried the ratified behavior. Cost if
wrong: the two repositories' inspection contracts drift at exactly the
member the evaluator's findings name.

**R7: Plan defect — no `science/world/errors.py` exists**

Tasks 5, 7, and 9 pointed error definitions at a nonexistent module; the
existing central `python/src/science/errors.py` is the home, including for
`LogEvidenceRefused`. Cost if wrong: an executor mints a parallel errors
module against house convention.

**R8: The `TransactionHalted` adapter arm is tested at Task 4 (gate closure, 2026-08-22)**

Task 4's file list gains `python/src/science/errors.py` (where the seam
defines `LogEvidenceRefused`), and Task 4's tests cover the
`TransactionHalted` arm of the §6.4 translation; Tasks 8 and 9 cover the
`ChainStateInvalid` and `PreconditionRefused` arms in context. Cost if
wrong: one of the three contracted arms ships untested until an audit or
arrival happens to exercise it.

**R9: `PendingUnresolved` lives in `atoms.chain.errors` (Task 3 boundary, 2026-08-22)**

The plan's Task 2 lines pointed it at `atoms.core.errors`; the gate-approved
atoms design and the landed implementation put it in a new
`atoms/chain/errors.py`. The design wins; the plan's two lines are
corrected, and Task 4's seam imports it from `atoms.chain.errors`. Cost if
wrong: Task 4's implementer chases a nonexistent import path.

**R10: The well-formed view's genesis is `entries[0]`, by identity (Task 4
review, 2026-08-22)**

`WellFormedView.entries` includes the genesis at index 0 with
`genesis is entries[0]` — the engine's own linearization sets
`genesis_digest = entries[0][0]`, and the seam re-types rather than
reshapes. Tasks 5–8's replay and evaluator indexing build on this. Cost if
wrong: an off-by-one over the registered surface, caught by cut 8's replay
units.

**R11: Every seam adapter translates, including `read_head` (Task 4 review,
2026-08-22)**

`read_head` translates the inspect-phase escapes exactly as
`inspect_registered` does — §6.4's contract binds the root-owned seam
adapters as a class, and the phase vocabulary has no third member. The
`World`'s injected `_chain_head` reader is not a seam member and does not
translate. Cost if wrong: audit and the anchor/export acts would see two
different error contracts over the same engine state.

**R12: An act holding `world_lock` must not call `World` methods (Task 4
review, 2026-08-22)**

The seam's `world_lock` returns the identical non-reentrant lock an opened
`World` takes in `registry()`/`status()` — that identity is the contract,
and its consequence is that Tasks 5–9's act cores read registry state
through their own parameters, never through a `World` method call made
under the lock. Cost if wrong: a self-deadlock, not an error.

**R13: Cut 7's pinned audit moves under a ruling; its declaration file does
not move at all (Task 5 review, 2026-08-22)**

Spec §3.3 (build-origin records join the epoch publication transaction)
cannot land under any implementation without two edits to cut 7's pinned
audit `python/tests/acceptance/test_n2_cut7.py`: the `ContentHeads` stub's
`genesis:<name>` label cannot survive the record form's 64-hex validation,
and X2's exact set equality cannot survive a record joining the
transaction. Both edits are claim-preserving (the tip stays
`corpus_state_identity`; set equality is retained, extended by an
exactly-one asserted record) and are authorized here, following the cut-6
precedent of editing the analogous audit only under a recorded ruling. The
declaration file `python/tests/n2_arms_cut7.py` is frozen ever — the
Task 5 fix round restores it byte-identical and derives the anchors inside
`_locked_publication_plan` from the `anchors.yaml` member it already
receives. Cost if wrong: either a frozen surface drifts silently, or the
build's record half is derived from a re-parse the ruling did not weigh.

**R14: `LogHeadCollision` is a distinct named error (Task 5 review,
2026-08-22)**

The spec names the collision refusal without a type; the plan's minting
constraint covers domain strings only. `RuleCollision` is documented as
rule-path-specific, so the record path gets its structural twin in the
central errors module. Cost if wrong: one superfluous error name.

**R15: Corpus-subject export can refuse `BuildHold` (Task 5 review,
2026-08-22)**

`export_head_artifact` takes the carrier's operation lock in writer mode,
so an export during a build capture refuses `BuildHold` — a documented
refusal, added to the export core's docstring and armed. No deadlock
arises: builds capture before taking the world lock, so the world→corpus
order is consistent. Cost if wrong: an undocumented refusal surfaces
mid-export and reads as a defect.

## Heads

Atoms commit hash (Task 2): `3aa5a766efb5275e444de193407992ce33e8edb7` (local atoms `main`, merge of `design/chain-inspection`; unpushed, joining row 4's disclosure per R1)  
Science commit hash (Task 9): *(recorded at Task 9)*
