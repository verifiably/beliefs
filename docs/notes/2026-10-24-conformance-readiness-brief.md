# Conformance contract and audit readiness

## Problem

Keep the eventual full contract cut grounded in live evidence: identify its
remaining prerequisites, retain the historical cuts honestly, and catch a live
sabotage becoming vacuous before another cut discovers it. Tracking goal:
`beliefs-199aeb`. This is a scope handoff, not a contract design or gate rollout.

## Current behaviour and evidence

Inspected main at `a7ce8ff` on 2026-10-24; no runtime certification was run.

- `beliefs-eacbe2` has twelve recorded dependencies; eleven are done and only
  `beliefs-3ea822` remains open. The roadmap still places `contract-cut` at the
  join after the operation set settles. Successor identities, normative artifact
  shape, certification cadence and legacy-check disposition remain design work
  (`docs/designs/2026-08-03-normative-contract-design.md`, §§3–8, 11).
- X2 is **epoch publication**, not merely the corpus publish act:
  `python/src/beliefs/world/epoch.py::build_epoch` crosses the locked recovery
  barrier and submits `_locked_publication_plan`, combining epoch members,
  `epochs/current` and log-head records in one plan. Cut 7 §3.2 leaves the
  power-fail arm open. Cut 36 re-homes L1's persistence arms to `beliefs-3ea822`;
  this re-scope adds them to its previously incomplete body. `atoms-f5779f` remains planned and open; its
  2026-10-14 assessment establishes synthetic A8 machinery, not consumer or
  physical certification evidence.
- `beliefs-1b6534` reports fifteen historical cut-5 failures, but `8b7fbc3`
  explicitly restored that frozen guard. The doctrine §§2, 5 and 8, the
  `CITED_NOT_RUN` entry, and acceptance conftest preserve it and refuse its
  collection. `c153ac2` likewise rules old runner signatures historical.
  An older runner naming cut 5 does not make it live.
- `70ff54e` made live cut-19 arm J2i vacuous; `567edbf` repaired it after
  cut 40's chained run found it (cut-40 results §3.1). The portable N2 inventory
  in `python/tests/test_n2.py` covers cuts 1–3 and 26, not every live acceptance
  guard. The 2026-10-02 preflight pilot catches collection failures, not runtime
  vacuity; its evidence remains in
  `docs/notes/2026-09-29-testing-backlog-brief.md`.

## Constraints

Keep cited guards, declarations and historical results under the frozen guard
doctrine, including its formatting amendment. Audit live guards selected by the
newest runner, never all historical guards indiscriminately. Preserve every
baseline and sabotage verdict, and run copied packages through the timed test
front door. Keep `root.py` the sole Atoms importer and Atoms the transaction
authority. X2 must distinguish prior-epoch recovery before the durable commit
decision from complete-new-epoch recovery after it. L1 includes committing and
rolling-back settlement paths and durable settlement before return or lease
release. No acceptance chain or hardware matrix was verified in this pass.

The project declares no shared-resource vocabulary. If a later measurement needs
an exclusive idle-host window, propose a `quiet` need with that meaning before
using it; this pass adds no undeclared need. Existing oracle-changing work,
including the session envelope and empirical-boundary designs, must be checked
again before the contract freezes; the old dependency list alone is insufficient.

## Alternatives

1. Repair old cut-5 checks to run on today's API. Reject: this changes evidence
   deliberately retained by `8b7fbc3` and cannot certify the historical discharge.
2. Add the newest full acceptance chain to every source change. It supplies
   stronger runtime evidence, but its incremental cost has not been measured.
3. Pilot the **live N2 phases only**, compare cost and detection with that chain,
   then recommend placement. Lean here: reuse `beliefs-e35dee` for the detection
   question and `beliefs-f64cf1` for shared cost attribution. No new research task
   or unconditional gate is needed at scoping time.

## Unanswered questions

- Which live-N2 net detects a J2i-style loss of sensitivity at acceptable cost?
  `beliefs-e35dee` answers with a bounded pilot, using `beliefs-f64cf1`'s existing
  cost work rather than duplicating an inventory sweep.
- What consumer-stage mapping and certification matrix close X2 and L1?
  `atoms-f5779f` and `beliefs-3ea822` own preparation and review of that design.
- Which successor identities, artifact shape, certification cadence and
  legacy-check dispositions enter the first full contract? `beliefs-eacbe2`'s
  design review answers after a fresh join/prerequisite inventory.

## Proposed decomposition

- `beliefs-e35dee`: rescoped, P2/s/mid/direct; measure and recommend a live-N2 net,
  with a healthy control and reproduced vacuity; no implementation rollout.
- `beliefs-3ea822`: rescoped, P3/l/high/planned; make X2's epoch path and all
  inherited L1 arms explicit; retain its wait on `atoms-f5779f`.
- `beliefs-eacbe2`: rescoped, P2/xl/high/planned; replace stale blocker claims
  with the observed eleven closures and remaining persistence prerequisite;
  refresh the join before freezing, then review the design and plan.
- `beliefs-1b6534`: proposed drop, supported by `8b7fbc3` and `c153ac2`; retain
  the original report and status pending disposition. Its dependent
  `beliefs-5aad8c` needs a later re-scope of the frozen-runner premise; it was
  related context, not processed here.

These are existing tasks, now grouped under `beliefs-199aeb`; no new research or
design task and no new idea wait edge is required. Existing testing goal
`beliefs-287026`, cost task `beliefs-f64cf1`, and idea `beliefs-89542c` retain
their ownership and dependencies. No member was claimed.
