# Conformance cut 11 — discharge results

**Date:** 2026-08-28
**Subject:** general intent qualification, world-index slice 6
(`../designs/2026-08-26-world-index-intent-boundary-design.md`), measured
against conformance cut 11's frozen selection
(`../designs/2026-08-27-conformance-cut-11.md`).

The frozen cut remains byte-exact at `9711886`. Only its status header changes
at banking. The implementation specification is promoted from
`docs/superpowers/specs/` to `docs/designs/` in the same change.

**Integration state.** Every implementation commit was made on
`design/intent-boundary`. The reviewed pre-banking head is `806444e`. The
branch is not merged or pushed by this discharge; the human partner owns the
history-preserving `--no-ff` merge. G4 and successor admission remain outside
this slice under their named successor-admission owner.

**Integration correction, 2026-08-28.** The human-authorized `--no-ff` merge
subsequently landed on local `main` in the integration commit carrying this
correction. It has not been pushed. The paragraph above records the
discharge-time state.

## 1. Accounting

Cut 11 reads one row, L7, in part. Its 13 selected units and labels J1–J13 give
**13 selected + 13 labeled = 26 declaration units**. Event-level L8, the L13
preimage resolver, and G4 remain unread, so no row is relabeled full.

The executable declaration table expands compound requirements into **66
lettered sabotage arms** normalized back to those 26 frozen units. L7u5 is the
sole citation-only unit for the engine's concurrent append serialization; its
Science corroborating check runs in the ordinary pass but is never mutated.
Every armed claim has one exact once-matching source mutation and at least one
check that fails under it.

### 1.1 What the discharge establishes

- The three intent shapes decode through one total gate and qualify through one
  precedence reducer: matched first, unresolved suppression second, unmatched
  findings last.
- Reports carry one total, chain-ordered qualification inventory. Audit,
  restore, and arrival assemble the same captured-record evidence and append
  qualification findings after phase findings.
- Capture is descriptor-bound, no-follow, regular-file-only, and bounded by the
  shared record ceiling. The publication port refuses an oversized qualifying
  record before executor construction while non-port writes remain unaffected.
- Assessment and dataset-production boundaries append their intent before any
  member act and durably publish the returned terminal outcome. Run records
  preserve the closure preimage, typed identity bridge, role relations, semantic
  coverage, token, and shape.
- The maintained holdings predicate regenerates the shipped rule byte-for-byte
  after its provenance header, and both holdings consumers agree with the
  general reducer.
- `completion()` retains its exported vocabulary while projecting the shared
  matching predicates; a wrong-spec run now reads `UNFINISHED`.

## 2. What ran

All commands ran sequentially from `python/`. Durable work ran on the
repository's ext4 volume through the certified runner root.

### 2.1 Host and certified tuple

- backend `linux`, revision `linux-4`; storage profile
  `flush-honoring-disk.v1`
- kernel `7.1.10-arch1-1`
- ext4 source `/dev/nvme1n1p2`, mounted `rw,nosuid,nodev,noatime,data=ordered`
- the exact host tuple independently passed 3,281 crash prefixes with zero
  violations before this Science slice ran; that atoms-local certification is
  recorded in execution-ledger R3 and no atoms change ships here
- measured Science source: `806444e`, followed only by this banking change's
  documentation and count-guard edits

### 2.2 Certified cut-11 runner

```text
$ uv run --frozen python tools/cut11_acceptance.py
[unchanged cut 5 prefix]
39 passed in 15.11s
[unchanged cut 6 prefix]
23 passed in 11.36s
[unchanged cut 7 N2 prefix]
42 passed in 42.03s
[unchanged cut 9 N2 prefix]
23 passed in 17.52s
[unchanged cut 10 N2 prefix]
36 passed in 10.41s
[cut 11 durable acceptance]
18 passed in 5.19s
[cut 11 N2]
17 passed in 21.60s
declared arms: 66 (= len(CUT11_ARMS), normalizing to the 26 frozen units)
### exit: 0
```

The seven pytest totals are the chained current-tree prefix, cut 11's durable
acceptance checks, and cut 11's N2 module. The printed 66 is a declaration-arm
count, not a pytest count. Cut 8 remains a historical byte pin because cut 9
deliberately succeeded its retired store-refusal label.

### 2.3 Portable and static gates

```text
$ uv run --frozen pytest
2635 passed in 406.90s (0:06:46)
### exit: 0

$ uv run --frozen ruff check .
All checks passed!
### exit: 0

$ uv run --frozen pyright
0 errors, 0 warnings, 0 informations
### exit: 0

$ git diff --check
### exit: 0
```

The portable suite excludes `tests/acceptance` by configuration and therefore
makes no durability claim. The certified runner above owns that claim.

The final documentation-only banking gate is recorded after the status and
guide edits:

```text
$ uv run --frozen python tools/check_guide.py
### exit: 0

$ uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py
....................                                                     [100%]
20 passed in 0.58s
### exit: 0
```

## 3. Review and implementation rulings

The post-implementation review reported no findings. During declaration review,
compound frozen requirements were expanded from 32 to 66 lettered arms; the
frozen 26-unit partition never changed. Signature-anchored prior-cut sabotages
moved with the production boundary or verifier lift while preserving their
checks and guarantees. The exact rationale, task heads, TDD disclosures, and
definitive runner summaries live in
`2026-08-27-intent-boundary-ledger.md`.

There is no frozen-cut deviation. The one specification amendment after the
cut froze was approved before implementation began: the replay check became
the specific `expected_recipe_identity` comparison rather than a general
callback. It narrowed the planned boundary surface without changing the cut's
selection or accounting.

## 4. Commit identities

The implementation heads measured here are:

| commit | subject |
|---|---|
| `76e76d8` | docs(plans): open the intent-boundary execution ledger |
| `fac2c80` | feat(identity): export v1.decode with CanonicalTextRefused |
| `1d25baf` | feat(runrecord): closure-to-stored codec with typed projection view |
| `e05c60c` | feat(port): add non-fulfilling execute and record ceiling |
| `4b7e1df` | feat(boundary): persist run intents and terminal outcomes |
| `6ed0c8f` | feat(intents): single-home the holdings qualification shape |
| `e7338a3` | feat(intents): add total decode gate and shape matching |
| `2a8ed87` | feat(records): add descriptor-bound record capture |
| `3d267e0` | feat(intents): decode captured records into qualification evidence |
| `aefcbb0` | feat(intents): add qualification precedence reducer |
| `c7817ba` | feat(verify): evaluated qualification replaces intents_unevaluated |
| `3c77a5b` | feat(report): re-base completion onto the shared shape predicates |
| `8472939` | test(intents): three-site consumer agreement and the label-12 matrix |
| `806444e` | test(cut11): declare intent-boundary arms and acceptance runner |

The banking commit following this record changes no runtime behavior.

## 5. Remaining boundary

Cut 11 does not close G4. The successor-admission slice inherits the transferred
design obligations recorded in the promoted design's §5. Event-level L8 and the
L13 preimage resolver also remain with their named owners. URL retrieval,
acquisition orchestration, typed grants, recency, and the belief-input status of
the holdings receipt are unchanged.
