# Conformance cut 26 — results

Frozen at `16926adfa33cae63f8bc33c65106a20de95df8ef`; discharged
2026-09-12 against installed `nodes` `c36c98931aa04f8da0865b85ae15699019e4394b`.
That checkout is a task-metadata-only descendant of the required design gate
`d8ecf664c85b7d17488de9f8884e5ba5b302c821`.

## 1. What ran

`just hook-pre-push` on the certified tuple: **4,487 passed in 1,032.29s** in
Python and **142 passed** in TypeScript, including `test_n2.py`'s portable audit
of `PORTABLE_ARMS` (cuts 1–3 and 26). `python/tools/cut26_acceptance.py` after
cut 25's complete chain: `test_n2_cut26.py` **10 passed in 1.32s**; D1-a and
D1-b both `sound`; the baseline `resolved`.
Pyright also printed its informational notice that 1.1.414 is available while
the environment runs 1.1.411; its analysis reported zero errors, warnings, or
information diagnostics.

A post-discharge review strengthened clause 4 after that full gate: `Corpus.all`
now compares complete, ordered nodes under both renamings rather than only their
IDs. An in-memory `Corpus.all` that dropped `biology/` facets failed the amended
check; the installed package passed both cases, and the focused portable N2 and
staleness audit passed all 48 tests. These focused results, rather than the
earlier full gate, are the evidence for the stronger assertion.

The installed `nodes` source tree was byte-identical before and after. A SHA-256
over each sorted relative path and file byte sequence under `python/src/nodes`,
excluding `.git`, `__pycache__`, `.pyc`, and `.pyo`, covered 19 files and
108,224 bytes and produced
`5e7859b0e2614dc487d2b7f915743b6f295401a6ce3dc0e79a7f0b710ed8341b` both times.

## 2. Accounting and disposition

Cut 26 reads one guarantee row: **1 full/closed** (D1). One declaration unit,
two arms. The global corpus has **148 of 195 rows closed, 47 open**.
`domain-boundary` closes.

- **D1 closes.** Cut 20's inspection arm is re-cited; the invariance check is
  selected; the negative is discharged as two `nodes`-package sabotages that
  the check refuses.

## 3. Corrections and deviations from the frozen cut

The frozen cut's selection, declarations, and body did not change. The
following corrections were required during discharge:

- the README/guide design inventory and its count guard gained cut 26;
- cut 6's historical replay now resolves the package-aware Beliefs source map
  and replays against `nodes` `5a00bba51df8bb2a06ec8a2fdc3c56ac8959e619`,
  the post-discharge source recorded by cut 6's results. Its live baseline still
  reads the currently installed `nodes` package. Cut 7's live guard now pins
  that intentional amendment at `46667b25c1afed966c3b831b6aef44ebb23e4616`;
- `domain-boundary` was removed from the ledger's open-boundary table, instead
  of retained as a closed row, to preserve the ledger/roadmap open-set contract.

The first gate exposed the three inventory omissions (4,484 passed, 3 failed).
The first acceptance-chain run exposed cut 6's stale package-root mapping and
historical dependency drift (18 passed, 5 failed). Neither failure was waived;
the corrected full gate and complete acceptance chain both passed.

## 4. Remaining boundary

`domain-boundary` has no open row. The next on-path boundary is
`world-resolution` slice 3, beginning with W7.
