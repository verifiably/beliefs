---
id: beliefs-d0ca64
title: Cut 19's J8f arm is timing-dependent under its sabotage
status: todo
priority: 2
size: s
created: 2026-09-06T11:44:14Z
updated: 2026-09-06T11:44:14Z
depends: []
tags: [conformance, write-path]
---

Running tools/cut19_acceptance.py twice on 2026-09-06 over main (74a5938, after the cut 17/18 re-pin) gave two verdicts for arm J8f (n2_arms_cut19.py: replace stack.enter_context(_operation_lock_for(root)) with a bare _operation_lock_for(root) in session/__init__.py). First run: mixed — tests/acceptance/test_session_acceptance.py::test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold passed with the sabotage applied, so test_n2_cut19.py failed on that one arm. Second run: all 43 arms sound, exit 0. The check observes the lock from another thread, so its detection of an unheld lock depends on scheduling. An N2 arm must fail deterministically under its sabotage (N2). Fix: make the interleaving check block inside the read under the lock (a barrier or an event the reconciliation read must reach while the writer holds the lock) so an unheld lock is observed on every run, then record the correction as a dated note in the cut 19 results record. The cut 19 record's 43-arms-sound claim was true on its run and is not retracted; the arm's check is what changes.
