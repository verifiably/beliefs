---
id: beliefs-d0ca64
title: Cut 19's J8f arm is timing-dependent under its sabotage
status: done
priority: 2
size: s
owner: hygiene/n2-arms
created: 2026-09-06T11:44:14Z
updated: 2026-09-09T09:15:40Z
depends: []
tags: [conformance, write-path]
---

Running tools/cut19_acceptance.py twice on 2026-09-06 over main (74a5938, after the cut 17/18 re-pin) gave two verdicts for arm J8f (n2_arms_cut19.py: replace stack.enter_context(_operation_lock_for(root)) with a bare _operation_lock_for(root) in session/__init__.py). First run: mixed — tests/acceptance/test_session_acceptance.py::test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold passed with the sabotage applied, so test_n2_cut19.py failed on that one arm. Second run: all 43 arms sound, exit 0. The check observes the lock from another thread, so its detection of an unheld lock depends on scheduling. An N2 arm must fail deterministically under its sabotage (N2). Fix: make the interleaving check block inside the read under the lock (a barrier or an event the reconciliation read must reach while the writer holds the lock) so an unheld lock is observed on every run, then record the correction as a dated note in the cut 19 results record. The cut 19 record's 43-arms-sound claim was true on its run and is not retracted; the arm's check is what changes.

## Notes

- 2026-09-09T09:15:40Z (hygiene/n2-arms): Root cause: the check observed the writer's durable commit landing within a fixed 0.5 s wait, so a commit slower than the wait read as a held lock. Rewritten to observe the lock's holder state at the two read points (inspect_detached and read_ledger_evidence patched) - no writer, no timer. Verified 2026-09-09: J8f sound on five concurrent audits, baseline resolved, and a dedent-the-ledger-read variant (the residue cut 19 §3 named) now audits sound as well. Declaration file untouched, still pinned at 8723fac. Sibling J8I still uses reader.join(0.5)/is_alive to show reconciliation waits; it failed correctly under sabotage on both recorded runs and is left as is.
- 2026-09-09T09:15:40Z (hygiene/n2-arms): test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold observes the hold at both read points via the lock's holder state; dated note 3.1 in the cut 19 results record
