# Conformance cut 22 — results

**Cut:** `../designs/2026-09-08-conformance-cut-22.md`, frozen 2026-09-08 at
`99d5757`, digest
`49a3cbdd843afa0d090c9dbe685bbf136ed9d0d62da12a25d0739691409323a0`
**Subject:** the biology pack, cross-contract slots, consulted-profile pin
agreement, and the first derivation-side domain-facet read
**Discharged:** 2026-09-08, on `feat/domain-boundary-slice2`
**Runner:** `python/tools/cut22_acceptance.py`

## 1. What ran

From `python/`, on the certified host and volume:

```text
XDG_CACHE_HOME=/mnt/ssd3/tmp/beliefs-biology-cache uv run --frozen python tools/cut22_acceptance.py
```

**Exit code 0.** The chain was cut 22 → cut 21 → cut 20 → cut 19 → cut 18 →
cut 17. Its 29 phase summaries reported **474 passed**. Cut 22's own accounting
was:

```text
[cut22 phase 2/3] test_biology_acceptance.py
2 passed in 2.97s
[cut22 phase 3/3] test_n2_cut22.py
7 passed in 5.12s
declared arms: 17 (= 9 declaration units; 9 guarantee rows)
```

The certified transcript is retained as
[`2026-09-08-conformance-cut-22-run/certified.log`](2026-09-08-conformance-cut-22-run/certified.log).
No capability waiver or refusal occurred. The M6 namespaced-slot reread was run
separately by Task 7's full domain-contract module test and is also selected by
the repository Python suite; the cut-22 runner does not count it as a new
sabotage arm.

The final repository gates tested commit `68a4b38d12f5a14fc4d92c13fdf792b95f0e0c12`:

- `just check` exited 0; Ruff, Pyright, TypeScript typecheck, Biome, and
  `tasks check` passed. Its transcript is
  [`check.log`](2026-09-08-conformance-cut-22-run/check.log).
- `just test` exited 0 with **4,125 Python tests passed in 1207.86 seconds**
  and **142 TypeScript tests passed**, with no skips or failures. Its transcript
  is [`test.log`](2026-09-08-conformance-cut-22-run/test.log).

## 2. Accounting and disposition

Cut 22 reads nine guarantee rows: **9 full/closed** (B1–B7, D6, M8), **1
partial unchanged** (D1), and the unchanged M6 reread. The frozen inventory is
9 declaration units expanding to 17 one-mutation sabotage arms. B1–B7 are the
new biology-pack table; D6 moves from partial to closed; M8 was already closed
and gains the sort-contract arm. The global corpus now has **195 rows across 18
tables, 135 closed and 60 open**: 127 previously closed + 7 new closed B rows +
1 newly full D6. M8 does not increase the closed-row count.

- **B1–B7 close.** Python and TypeScript parse and compile cross-contract
  slots; the consulted walk reaches every sort contract and checks pins; the
  authenticated reader mints immutable facet receipts; observed facet rows
  enter the belief-input closure; and the biology pack ships byte-identically.
- **D6 closes.** The isolated case proves the domain-facet namespace is
  collected from the read, and the dogfood case measures the same reader over
  `biology/gene-axis`.
- **M8 gains an arm.** An editorial biology-contract bump preserves claim
  identity and moves the belief-input digest through the foreign slot's sort
  contract.
- **M6 re-runs unchanged.** A successor cannot rewrite a namespaced slot.
- **D1 stays partial.** Its cross-repository negative requires adding a
  domain-aware path to `nodes`; this cut does not claim it.

## 3. Corrections and deviations from the frozen cut

- **2026-09-08 — exact reader authentication.** Public profile-shaped and
  spec-shaped mocks exposed spoofing seams. The implementation checks the exact
  compiled `ProfileSpec` and exact read-view/receipt types, binds a private
  validating-contract identity, and carries facet receipts immutably. These
  checks add no projection member or sabotage arm; the frozen three-field
  projection and 17-arm count remain unchanged.
- **2026-09-08 — missing-read sabotage.** B4b removes the held-target guard so
  the sabotage reaches the actual missing `view.get` rather than failing at a
  neighbouring condition.
- **2026-09-08 — durable dogfood seam.** A mismatched manifest may be opened
  and read; the writer rechecks pins under its operation lock and refuses the
  attempted `add` before effects. The durable fixture exercises that seam and
  preserves B7's low-level original-pin check.
- **2026-09-08 — fixture and live matcher corrections.** The certified chain
  exposed two synthetic-pin fixtures and W18j's stale source anchor. The
  fixtures now derive real profile pins. Only cut 14's live, unpinned guard
  machinery adapts W18j with `dataclasses.replace`; its canonical table, check
  ids, guarantees, frozen cut bodies, and prior pins are preserved.
- **2026-09-08 — typing classifier.** An unknown predicate remains
  `unmapped-predicate`; `unmapped-shape` is reserved for a known predicate with
  a missing kind pair.
- **2026-09-08 — final-review evidence.** The dogfood fixture now records real
  `Belief` digest comparisons for a biology editorial bump, an unrelated-domain
  bump, and a facet-payload change. The resolver refusal now names the missing
  sort truthfully whether its namespace is absent or already compiled, and the
  Python coverage reaches an unresolved operator slot with no foreign dimension.

## 4. Reproduction measurement

The durable measurement is recorded in
`2026-09-08-mm30-reproduction-slice2-run/` and interpreted in
`../designs/2026-09-05-mm30-reproduction.md`. The rerun typed **307 of 334**
claims, with **27 `no-claim-recorded`**, over **285 concepts**. Admission was
`Admitted`; both the original and rederived answers were equal
`NoBelief(no-directional-outcome)`.

Neither answer has a `belief_input_digest`: `NoBelief` carries none, and the
historical artifacts record none. The run therefore makes no old/new digest
comparison and no isolated causal claim. What changed and is recorded is the
claim projection, operator vocabulary, compiled profile, and consulted
contract set.

## 5. Remaining boundary

The biology pack, corpus-local mm30 contract, cross-contract slot rule, and
D6 reader arm are discharged. `domain-boundary` retains only **D1**, partial on
the cross-repository negative that adds a domain-aware code path to `nodes`.
GO, HP, EFO and MONDO remain unmeasured limitations rather than promised
contents of the shipped pack. The next on-path implementation boundary is
`world-resolution`.
