# Conformance cut 15 — discharge results

**Date:** 2026-09-02
**Subject:** the full workflow surface
(`../superpowers/specs/2026-09-01-workflow-surface-design.md`), measured
against its frozen §11 at `e2f9d71`.

Frozen §11 remains byte-exact. The design status changes at banking; the
frozen selection does not.

## 1. Accounting and disposition

Cut 15 selects **17 units**: R2 2, R16 10, R20 2, R21 2, and R23 1.
Labels K1–K8 add **8 labeled units**, for **17 selected + 8 labeled = 25
units**. The executable declaration table expands them into 30 unique
one-mutation arms.

This discharge closes R2, R16, R20, and R21. It reads R23's local
basis/composition disagreement from cut 5 §3.2; R23 stays partial on its
separately assigned world-resolution, mutation, and rules-store clauses. Its
replay-cardinality arm was already discharged by cut 3 and was neither
reopened nor selected here.

The implementation establishes:

- content-addressed workflow-definition snapshots carried by recipe v2,
  with semantic job keys over wildcard instances;
- a planning launch that records non-checkpoint jobs and resolved target
  keys before execution, including the declared checkpoint expansion rule;
- per-family seed obligations checked against per-job claims and against
  execution coverage, for both assessment and dataset-production recipes;
- comparison diagnostics for legitimate job-set differences, without making
  those differences a verdict or scope input;
- definition-equality and job-diagnostic queries over closure values; and
- composed planning/execution launch attestations, with qualification reading
  execution evidence and the four-row recipe/receipt run-domain matrix.

## 2. What ran

All Python commands ran from `python/`. The runner used its default durable
work root at `../.cut15-acceptance`, probed both durable and confinement
prerequisites, and removed each per-run directory afterward.
`PREFIX_RUNNERS = ("cut14_acceptance.py",)`: cut 14 was the newest discharged
cut when cut 15 ran, and its complete runner executed before cut 15's three
phase modules.

### 2.1 Certified cut-15 runner

`uv run --frozen python tools/cut15_acceptance.py`

```text
[cut15 phase 1/4] cut14_acceptance.py
[cut14 phase 1/12] test_n2_cut6.py
23 passed in 12.42s
[cut14 phase 2/12] test_n2_cut7.py
42 passed in 43.90s
[cut14 phase 3/12] test_n2_cut9.py
23 passed in 18.75s
[cut14 phase 4/12] test_n2_cut10.py
36 passed in 11.03s
[cut14 phase 5/12] test_intent_boundary_acceptance.py
18 passed in 5.70s
[cut14 phase 6/12] test_n2_cut11.py
17 passed in 29.87s
[cut14 phase 7/12] test_successor_admission_acceptance.py
4 passed in 2.07s
[cut14 phase 8/12] test_n2_cut12.py
16 passed in 16.24s
[cut14 phase 9/12] test_confinement_acceptance.py
15 passed in 310.84s (0:05:10)
[cut14 phase 10/12] test_n2_cut13.py
16 passed in 150.06s (0:02:30)
[cut14 phase 11/12] test_coordination_acceptance.py
22 passed in 12.39s
[cut14 phase 12/12] test_n2_cut14.py
7 passed in 14.41s
declared arms: 29 (= 29 selected units)
[cut15 phase 2/4] test_cut15_lineage.py
5 passed in 71.15s (0:01:11)
[cut15 phase 3/4] test_confinement_acceptance.py
15 passed in 318.96s (0:05:18)
[cut15 phase 4/4] test_n2_cut15.py
8 passed in 47.01s
declared arms: 30 (= 17 selected + 8 labeled units)
```

The fifteen pytest summaries total **267 passed, 0 failed**. The runner
exited 0 at workflow head `b8c00d4`.

### 2.2 Certified host facts

- backend `linux`, revision `linux-4`; storage profile
  `flush-honoring-disk.v1`;
- kernel `7.1.11-arch1-1`;
- ext4 source `/dev/nvme1n1p2`, mounted at `/mnt/ssd` with
  `rw,noatime,data=ordered`;
- normalized barrier options `async`, `barrier=1`, `commit=5`,
  `data=ordered`, and durability features `compat=0x3c`, `incompat=0x246`,
  `ro_compat=0x46b`;
- certification record
  `atoms/docs/certification/2026-08-30-ext4-linux-7.1.11-arch1-1.json` at
  Atoms commit `2a25de8`: 9 scenarios, 920 marks, 3,286 crash prefixes, zero
  violations; and
- bubblewrap `0.12.0`, unprivileged user namespaces enabled, and the loader
  listing probe available. `host_prerequisites()` returned `None`; refusal
  would have ended the runner with exit 2 rather than skipping a phase.

The editable Atoms dependency loaded checkout `a563ee6`; the certification
commit is its ancestor, and the commit after cut 14's recorded `569d5c4` is
documentation-only.

### 2.3 Repository gates

Post-banking gates:

- `uv run --frozen pytest` — **3074 passed in 1004.34s (0:16:44)**;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**;
- `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py`
  — **22 passed in 0.66s**;
- `npm ci` — completed; npm reported 6 dependency vulnerabilities (3
  moderate, 2 high, 1 critical) and 2 install scripts awaiting approval;
- `npm test` — **101 passed across 5 files**;
- `npm run typecheck` and `npm run check` — passed; Biome checked 13 files;
- `git diff --check` — silent; and
- `tasks check` — zero errors and zero warnings before banking.

Every command above exited 0. The npm audit and allow-scripts notices are
pre-existing dependency advisories, not gate failures.

## 3. Frozen prior evidence

Cut 15 names `cut14_acceptance.py` as its sole prefix runner. That runner
executes cut 14's twelve frozen phases, including the live cut-13 audit; cut
15 additionally pins every prior declaration file from cuts 5–14 and verifies
that the cut-15 design freeze `e2f9d71` is an ancestor of the executing head.

The merge with cut 14 exposed five source anchors whose guarantees remained
live after launch-attestation composition, plus two confinement-tamper arms
made vacuous by the new planning launch. Commits `77dd0b6` and `b8c00d4`
preserved those historical mutation seams without changing frozen declaration
bodies. The complete cut-13 and cut-15 audits above establish that every arm
is sound on the banked tree.

## 4. Implementation commits

The workflow implementation begins at `ae0c8a9`; the cut-14 merge and its two
integration corrections precede the certified head `b8c00d4`:

| commit | subject |
|---|---|
| `ae0c8a9` | feat(recipe): add the canonical semantic job key |
| `d32b051` | feat(recipe): carry the workflow-definition snapshot at v2 |
| `4fd3317` | feat(recipe): carry the workflow-definition snapshot at recipe v2 |
| `09ed484` | feat(recipe): compose planning and execution launch attestations |
| `5119b20` | feat(recipe): dispatch the run domain on recipe and receipt shape |
| `e2a1956` | feat(runrecord): decode typed run closures |
| `de29d22` | feat(replay): state definition plan agreement |
| `1448dbb` | feat(seeds): derive and claim job seeds |
| `26a4578` | feat(boundary): render seed roots as one mapping |
| `a59fa62` | feat(adapter): read digest-named seed claims |
| `c6ab77c` | feat(replay): check seed conformance at both levels |
| `4c01dfe` | feat(boundary): derive the planned job set |
| `e4c9cdc` | feat(boundary): cross-check checkpoint declarations |
| `dd1b468` | feat(boundary): resolve targets to planned jobs |
| `7188216` | feat(replay): check job sets and targets |
| `237d0c2` | feat(boundary): plan in a confined instance |
| `af5f7ec` | test(cut15): exercise full workflow fixtures |
| `37d4b2d` | feat(workflows): query definition equality and job diagnostics |
| `4635f52` | test(cut15): vary one recipe job set through scratch |
| `237ddde` | test(cut15): pin local lineage disagreement |
| `8a4d43b` | test(n2): declare cut 15 arms and acceptance command |
| `6383a71` | fix(workflows): close cut 15 integration gaps |
| `77dd0b6` | chore: merge main into workflow surface |
| `fd873d3` | fix(tests): preserve malformed spec boundary ordering |
| `b8c00d4` | fix(boundary): preserve confinement tamper checks |

The design and plan commits precede this range. This results record is
committed with the discharge change and therefore does not embed its own
commit id.

## 5. Remaining boundary

`workflow-surface` leaves the live ledger. R23 remains partial only on its
producer-snapshot and receipt clauses, its move/consolidate/deletion clauses,
and its rules-store clauses; its local basis/composition disagreement is
closed here and its replay-cardinality arm remains closed at cut 3. No new
boundary is created by this discharge.
