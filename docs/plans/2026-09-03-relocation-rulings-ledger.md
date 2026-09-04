# Relocation implementation rulings ledger

**Date:** 2026-09-04
**Scope:** implementation and discharge of
`../designs/2026-09-03-conformance-cut-16.md`.

This file preserves the rulings made while the relocation plan was executed.
The frozen cut remains the authority for selection and accounting; this ledger
records how implementation ambiguities were resolved.

## R1 — Task state travels with implementation

The task record entered `doing` with the banking commit and remains tracked
with the implementation evidence. Managed deletion is not delivered, so the
task is not closed by the relocation discharge.

## R2 — Both operation ports are preflighted

Public `move` and `consolidate` require both writers to expose operation ports
before either root-local intent is appended. Internal helper assertions are
not a public refusal and may not strand one root's intent.

## R3 — Destination occupancy is exact and canonical

A move destination is already occupied only when
`destination.read_view.resolve(node.id) == node.id`. A deprecated-alias claim or a
same-uid/different-id claim is not a duplicate location; ordinary add
preflight classifies it as `CollisionRefused` before either intent.

## R4 — Local absence has one observable taxonomy

After a target has moved away, local state cannot distinguish that history
from a target that never existed. The final under-lock re-resolution in
`retract` and `supersede` therefore uses `RelocationTargetMissing` for either
case. No provenance scan or compatibility hierarchy was added.

## R5 — Replacement is preflighted without writing

`consolidate` runs `_replace_locked`'s deterministic admission checks before
either intent. It omits the create-only `_refuse_already_minted` check and
passes the carried kind through the family guard; the already-resolved losing
input is sufficient delete preflight.

## R6 — Collision checking is replacement-safe

`Index.assert_addable` permits the existing same `(uid, id)` pair and rejects
an identity claim owned by another uid. `_refuse_collision` therefore belongs
in replacement preflight, preventing a contributed deprecated-id collision
from stranding intents.

## R7 — Equal routes retain canonical decoded values

Lineage-basis union compares canonical v1 encodings and decodes the sorted
keys for retained values. Unicode-normalization and mapping-key-order variants
therefore produce one operand-order-independent result instead of preserving
either input's raw spelling.

## R8 — Carried retractions are admitted only at relocation seams

The lock-held add and replace seams pass `admitted_kind=node.kind` for a record
they relocate but did not author. This makes the M3 retraction-replica arm
reachable without opening a general retraction minting route. Coordination,
holdings-observation, and act-report refusals do not consult that argument and
remain absolute.

## R9 — Recovery repairs data, not operations

Every invocation mints a fresh `event_token`. A retry or a compensating
`consolidate` can repair the data state but cannot adopt or close the
interrupted invocation's intents. An interruption at or after the first intent
append permanently leaves one or two original intents unfinished.

## R10 — The certified runner owns disposable cache state

The ambient XDG cache proved read-only to the planning subprocess. The cut-16
runner scopes child-process cache state to its disposable certified run
directory, preserving the prefix environment and removing the cache with the
run.

## R11 — Six vacuous evidence gaps required stronger assertions

Second-reader sabotage established six gaps before correction: W5's constant
producer subject, T2 data before intent, M3's identity-preserving counter
rewrite, T8's destructive refusal, W16's omitted coreference-balance check,
and R23's false first-stamp mutation. Each acceptance assertion was tightened
at the actual guarantee boundary.

## R12 — Extra sabotages do not create frozen units

Eight additional source sabotages cover the strengthened clauses. The
executable inventory therefore contains 27 concrete arms while `unit_of`
normalizes them to the frozen 11 units. No prior-cut check is reclaimed and no
unit is silently split.

## R13 — Conflict fixtures use public production and movement

Boundary-minted conflict routes are built through public import and move setup
so every route resolves fully. The R23 conflict evidence does not depend on a
fixture-authored shortcut or an unresolved synthetic producer.

## R14 — Discharge corrects current-facing status only

The world-changing-families design, frozen cut status, adoption ledger,
roadmap, README, and contributor guide advance together. Frozen §§2–7 and
historical results remain unchanged; current-facing claims that cut 16 awaits
implementation are corrected.

## R15 — Integration requires fresh approval

The discharge commit stops on the clean feature branch. It does not merge to
`main`, push, create a pull request, or remove the worktree without fresh
explicit approval at that boundary.

## R16 — Deletion planning starts after integration

The deletion cut is not drafted in this worktree. Brainstorming and planning
begin only after relocation integrates, in a fresh worktree as repository
guidance requires.
