# Conformance cut 14 — discharge results

**Date:** 2026-09-02
**Subject:** coordination and view kinds
(`../designs/2026-08-31-coordination-and-view-kinds-design.md`), measured
against its frozen §9 at `c07bf72` and approved implementation amendment §11
at `09b0b58`.

Frozen §9 remains byte-exact. The design status and paths outside §9 change at
banking; the frozen selection does not.

## 1. Accounting and disposition

Cut 14 selects **29 units**: W11 2, W12 1, W13 1, W17 14, and W18 11.
There are zero labeled units and no intent-position arm. W17's whole-revision
clause is its own unit; missing and divergent projects are separate units.
The declaration table contains 29 unique, one-mutation arms normalized
one-to-one to those units.

This discharge closes W11, W12, and W18. It closes W17's ordinary coordination
revision family and leaves that row partial only on intent-position, owned by
`publish`. It reads W13's two-project negative; W13 remains partial on its other
world-resolution clauses.

The implementation establishes:

- a closed, canonical `science.view-query.v1` grammar whose address-bearing
  forms accept only world-tier addresses;
- an independently versioned coordination contract compiled into
  `ProfileSpec`, with authorization read from the destination's pinned profile;
- opaque project and local identities, immutable whole revisions, exact
  predecessor continuity, one standing tip or a refusal naming every tip, and
  all-tip repair across explicitly mounted corpora;
- a dedicated coordination family door, with ordinary family doors and import
  refusing coordination records and the coordination door refusing world
  kinds; and
- coordination bytes moving corpus/epoch packaging identity while entering no
  world map and no belief-input digest.

## 2. What ran

All Python commands ran from `python/`. The runner used its default durable
work root at `../.cut14-acceptance`, created one probed environment, forwarded a
writable per-run cache to N2 children, and removed the individual run directory
afterward. `PREFIX_RUNNERS` is empty: the twelve frozen phase modules ran
directly in this exact order.

### 2.1 Certified cut-14 runner

`uv run --frozen python tools/cut14_acceptance.py`

```text
[cut14 phase 1/12] test_n2_cut6.py
23 passed in 12.53s
[cut14 phase 2/12] test_n2_cut7.py
42 passed in 44.79s
[cut14 phase 3/12] test_n2_cut9.py
23 passed in 18.92s
[cut14 phase 4/12] test_n2_cut10.py
36 passed in 15.05s
[cut14 phase 5/12] test_intent_boundary_acceptance.py
18 passed in 5.79s
[cut14 phase 6/12] test_n2_cut11.py
17 passed in 34.49s
[cut14 phase 7/12] test_successor_admission_acceptance.py
4 passed in 2.49s
[cut14 phase 8/12] test_n2_cut12.py
16 passed in 16.09s
[cut14 phase 9/12] test_confinement_acceptance.py
13 passed in 213.70s (0:03:33)
[cut14 phase 10/12] test_n2_cut13.py
16 passed in 125.12s (0:02:05)
[cut14 phase 11/12] test_coordination_acceptance.py
22 passed in 12.84s
[cut14 phase 12/12] test_n2_cut14.py
7 passed in 14.68s
declared arms: 29 (= 29 selected units)
```

The twelve pytest summaries total **237 passed, 0 failed**. The runner exited
0.

### 2.2 Certified host facts

- backend `linux`, revision `linux-4`; storage profile
  `flush-honoring-disk.v1`;
- kernel `7.1.11-arch1-1`;
- ext4 source `/dev/nvme1n1p2`, mounted `rw,nosuid,nodev,noatime,data=ordered`;
- normalized barrier options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`, `ro_compat=0x46b`;
- certification record
  `atoms/docs/certification/2026-08-30-ext4-linux-7.1.11-arch1-1.json` at
  Atoms commit `2a25de8`: 9 scenarios, 920 marks, 3,286 crash prefixes, zero
  violations; and
- bubblewrap `0.12.0`, unprivileged user namespaces enabled, and the loader
  listing probe available. `host_prerequisites()` returned `None`; any refusal
  would have ended the runner with exit 2 rather than skipping a phase.

### 2.3 Repository gates

The first full-suite attempt exposed three shared integration defects. Commit
`5b1b251` corrected them at their common boundaries: the controlled retraction
door admits its own record kind after the coordination checks, coordination
validation no longer uses the capability-audited `remove` name, and M7's
sabotage follows the coordination-aware profile projection. The 22 directly
affected checks and the stale-sabotage audit passed before the final run.

Post-fix gates:

- `uv run --frozen pytest` — **2968 passed in 935.88s (0:15:35)**;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**;
- `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py`
  — **22 passed in 0.66s**;
- `git diff --check` — silent; and
- `tasks check` — zero errors and zero warnings before banking.

Every command above exited 0.

## 3. Frozen prior evidence

Cut 14 cites cut 5 from
`2026-08-19-conformance-cut-5-results.md`; it does not invoke cut 5 or an
aggregate runner. The four cut-5 SHA-256 pins remained unchanged:

| path | SHA-256 |
|---|---|
| `python/tests/n2_arms_cut5.py` | `29a778a617627a697787ea62b578034e2407d45c2d9adb4e85816598af3f0f19` |
| `python/tests/acceptance/test_n2_cut5.py` | `df589285dd377709c322a2a3958196f3e8a8c65032af8d79863b548584e41798` |
| `docs/designs/2026-08-19-conformance-cut-5.md` | `683dc249b1898179beaac9c9a550bca5b43f5fe3af9a107f0fc7ee47d58cbdd0` |
| `docs/plans/2026-08-19-conformance-cut-5-results.md` | `3a24efe3678b99d977a6ddd4f464e600479fb689dedd6df3f5647cb58f6f32de` |

The cut-14 audit also verified that every frozen prior declaration file from
cuts 5–13 matches its pinned commit and that `c07bf72` and `09b0b58` are
ancestors of the executing head.

## 4. Implementation commits

The implementation range is `48f2ac5..5b1b251` (inclusive):

| commit | subject |
|---|---|
| `48f2ac5` | feat(coordination): add address and refusal values |
| `e5ea10e` | feat(coordination): parse view query v1 |
| `6f3f8ca` | feat(coordination): parse coordination contracts |
| `cb1a964` | feat(coordination): compile coordination profiles |
| `a055de6` | feat(coordination): resolve live revision tips |
| `e2d2288` | feat(coordination): mint coordination genesis |
| `ae9558d` | feat(coordination): revise and repair tips |
| `40d5582` | feat(coordination): close coordination family doors |
| `df997b7` | feat(coordination): exclude coordination from world inputs |
| `0650434` | test(coordination): add cut 14 durable acceptance |
| `f982778` | test(coordination): declare cut 14 arms |
| `5b1b251` | fix(coordination): preserve controlled family entries |

The plan and execution corrections at `aa6e4d4` and `34107bb` precede that
implementation range. This results record is committed with the discharge
change and therefore does not embed its own commit id.

## 5. Remaining boundary

`coordination-addressing` leaves the live ledger. W17 intent-position remains
with `publish`; view-query evaluation remains with `world-read`; neither is
silently reassigned to a new coordination boundary. W13's remaining
coverage/digest, restore, forgery, and fork clauses stay with
`world-resolution` as the roadmap records.

> **Amended 2026-09-08 (biology pack design §5.3a, §10).** The live cut-14
> guard adapts W18j's matcher to the landed base-profile agreement line while
> preserving its injection, check, row, and arm count. The canonical
> `n2_arms_cut14.py` declaration remains frozen at `f982778`.
