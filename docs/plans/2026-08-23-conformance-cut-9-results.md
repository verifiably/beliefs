# Conformance cut 9 — discharge results

**Date:** 2026-08-23
**Subject:** the root lifecycle and store substrate, world-index slice 4
(`docs/designs/2026-08-23-world-index-root-lifecycle-design.md`, promoted from
the implementation spec in this same change), measured against conformance
cut 9's frozen selection (`docs/designs/2026-08-23-conformance-cut-9.md`).

**The frozen cut's rows, selected bullets, labeled declarations, obligations
and accounting are not edited here.** Cut 9 froze on 2026-08-23 at `0977bde`;
only its status header changed — at banking, to record the discharge, point at
this document, and name the promoted path of the spec its frozen text cites at
the pre-banking `docs/superpowers/specs/` home. Results are recorded
separately, which is what this is.

**Integration state.** Every commit named in §3 was made on the implementation
branch `design/world-index-root-lifecycle`, whose base is `6bbe855` on `main`.
**The branch is not merged.** It is ready for the `--no-ff` merge, and the
merge is the human partner's act, as it was for slices 2 and 3, inheriting the
prior cuts' reachability constraints (`4a7dc19`, `c8c0b12`, `117f37e`) plus
cut 9's own freeze pin `0977bde`. Nothing below claims otherwise: where a
banked document now says this slice landed, it says so about this branch.

**Corrected 2026-08-24.** The merge landed the next day: `--no-ff`
integration commit `7a9fec8` on `main`, preserving branch history and the four
reachability constraints named above. The paragraph above is true of the
discharge and false of the present.

## 1. The accounting, re-derived

Recounted from the frozen cut's own §3 bullets rather than copied from its §4.

| state | rows | n |
|---|---|---:|
| full | L6 | 1 |
| part | L2, L4, L10, W13 | 4 |

**1 full + 4 partial = 5 rows read.** Every other row stands at its prior
cut's certification (cut 9 §3.2); the fork-baseline lift landed before the
cut's draft precisely so L6 would not fail construction.

Declaration units, counting each **Selected** and **Labeled** bullet once at
its home:

| row | L2 | L4 | L6 | L10 | W13 | labeled |
|---|--:|--:|--:|--:|--:|--:|
| units | 1 | 2 | 2 | 12 | 2 | 11 |

The five rows sum to 19; the eleven §3.3 labeled declarations sit outside the
row accounting. **19 selected + 11 labeled = 30 declaration units.** The
landed declaration module `python/tests/acceptance/n2_arms_cut9.py` carries
exactly 30 arms with the same per-row distribution, eleven of them
`V1`–`V11` — the **V prefix, not cut 8's `D`**: `D1`–`D10` are cut 8's
declared labels and a shared prefix would collide in any cross-cut listing
(execution ledger R22). Cut 9's own §3.1 dispositions and §4 accounting are
*parsed out of the frozen document* by
`test_the_selected_partition_is_the_frozen_cuts_own` rather than restated in
the suite, exactly as for cut 8.

**Atoms citations are metadata, never checks.** Eight units and one shared
clause cite the atoms certification for engine-interior durability orders
(the replica stamp order, the fork genesis-before-grant order, the
operation-before-genesis order — the cut's §1 principle). The declaration
module carries them in `ATOMS_CITATIONS_BY_UNIT` (keys `L10u4`, `L10u5`,
`L10u7`, `V1`–`V6`), reconciled by the audit so a citation cannot silently
stand in for a check node: every declared check is a Science pytest node, and
the citations name what is *not* checked here and where it is.

### 1.1 Unit dispositions: 28 full, 2 partial

The row dispositions above are the frozen cut's. This is the finer accounting
the landing owes under the any-unrun-arm rule: of the 30 declared units,
**28 are certified in full and 2 are partial**, and both partialities are the
frozen cut's own, not this landing's — cut 9 §8 limitation 2 names them at
declaration:

- **L10u8 — partial.** The cold-bootstrap arm certifies that a metadata-less
  store copy reads `metadata-less` and refuses mutation, the stamp's loss
  failing closed. The frozen row's *unresolvable-for-holdings-reads and
  dereference-minting* clauses defer to the holdings slice — no holdings read
  exists to refuse — and the unit's declared `asserts` text says so.
- **L10u10 — partial.** The incomplete-copy arm certifies that a copy missing
  a payload file the chain's surface names never returns `validated` and the
  root stays unserviceable, the incompleteness constructed by omission and
  never by chain damage (§6's first freeze obligation). Its *dereference*
  behavior is again the holdings slice's.

All three §6 freeze obligations are discharged as source-borne checks in
`test_n2_cut9.py`: the L10u10 construction is scanned for surface-named
omission rather than chain damage, the L6u1 fixture interposes no mutation
between the anchor and the deletion, and the label-8 writable-refusal arm
builds its granted root through `register_root`'s own path, never fabricated
bookkeeping.

### 1.2 Three harness refinements, forced by the all-checks-fail physics

The N2 harness inherits cut 5's physics: each arm is one unit under one
sabotage, and **every** declared check must fail under it — a mixed arm is a
defect. Three declarations could not carry their first-drafted check lists
under that rule, and each was refined rather than argued around (execution
ledger R22):

- **W13u2 homes the fork-of admission integration node.** Label 8's
  verify-side sabotage cannot reach `World.admit`'s `ForkOf` validation, so
  the end-to-end admission node (no fixture-authored manifest) is declared on
  W13u2, whose act-authored-manifest sabotage it genuinely fails under.
- **V9 audits the shared genesis-binding refusal pair** (`anchor_heads` and
  `export_head_artifact` refusing a `store_id` the supplied root's genesis
  does not carry); the export round-trip and audit-one-boundary nodes stand
  un-sabotaged in the ordinary suite, where they run green on every push.
- **V10 audits its three surface-borne nodes** (the store-mint refusal of a
  populated root, the fork-baseline admission rule, the canonical projection);
  the payload-codec and non-fork-empty-baseline clauses are suite-enforced.

One fixture correction closed a vacuous first sabotage: the fork parent's
chain now moves past its genesis (`head ≠ genesis` asserted), so L10u1's
fresh-genesis claim is tested against a parent whose head genuinely differs
from the digests the fork genesis must carry.

## 2. What ran, and where

Science resolves `atoms-core` and `nodes-core` as editable path dependencies
(`python/pyproject.toml` `[tool.uv.sources]`). All gates ran from this
repository's `python/` directory, sequentially — never concurrently, because
the cut-5, cut-6, cut-7 and cut-9 runners share `SCIENCE_CUT*_ROOT` work
directories.

**Evidence order.** Cut 9 §5's obligation 9 is homed here, and its discipline
is cut 8's: a count claim quotes pytest's own summary line under `pipefail`,
never a collect-only count. Every command below was run **after the last edit
to the tree it measures** — after the banking amendment set of §8 (the spec's
promotion, the adoption-ledger rows, the limitation closures, the README and
guide corrections, cut 9's status header, and the corpus guard's one forced
Python edit) and after this file was created, which it had to be before the
runs because the corpus guard resolves the guide's link to it. Every tree
change made after the collection is prose in this file or in the execution
ledger — `docs/plans/` content no gate reads: the corpus guard reads
`docs/designs/`, `docs/guide/` and `README.md` (resolving *links into*
`docs/plans/`, never content), and `check_guide.py` reads `docs/guide/`.

### 2.1 Host and certified tuple

- backend `LinuxBackend`; storage profile
  `StorageProfile(profile_id='flush-honoring-disk.v1')`
- work directory: default, `.cut9-acceptance` beside the checkout —
  `SCIENCE_CUT9_ROOT` unset, so the certified volume is the repository's own.
  The runner probes it by registering and dropping one throwaway root of
  **each kind the projection instantiates — world, corpus, and store** — and
  treats a refusal as an error, never a skip. It makes one `run-` directory
  beneath the work directory and points the cut-7 prefix at that same
  directory through `SCIENCE_CUT7_ROOT`, so the whole command occupies one
  certified volume and removes what it made.
- volume: ext4 on `/dev/nvme0n1p2`, mounted `rw,noatime,data=ordered`
- kernel `7.1.8-arch1-3`
- source commit `d29a98f`, plus the banking change's own edits (§3)

### 2.2 The four evidence items

**1 — the full portable suite.** Run bare: `pyproject.toml`'s `addopts`
already carries `-q`, so a second `-q` produces `-qq` and suppresses the very
count the claim rests on. The suite excludes `tests/acceptance` by
configuration (`--ignore=tests/acceptance`), so this is portable behaviour and
**no** durability claim. Through Tasks 3–10 this suite read `3 failed` on the
same three documentation guards — the README design count and table and the
guide's citation completeness, assigned to this task by the plan — and the
banking amendment set is what turns them green; the ledger quotes each
intermediate line (R14, R16, R18–R23).

```text
$ cd python && set -o pipefail && uv run --frozen pytest 2>&1 | tail -2
....................                                                     [100%]
2252 passed in 352.28s (0:05:52)
```

**2 — the cut-9 acceptance command.** This is the discharge. Five numbers, and
only four of them are pytest summary lines.

```text
$ cd python && set -o pipefail && uv run --frozen python tools/cut9_acceptance.py
[cut9 phase 1/2] cut7_acceptance.py
[cut7 phase 1/3] cut5_acceptance.py
.......................................                                  [100%]
39 passed in 14.56s
[cut7 phase 2/3] cut6_acceptance.py
.......................                                                  [100%]
23 passed in 10.84s
[cut7 phase 3/3] test_n2_cut7.py
..........................................                               [100%]
42 passed in 40.52s
[cut9 phase 2/2] test_n2_cut9.py
.......................                                                  [100%]
23 passed in 16.43s
declared units: 30 (pinned by test_the_declared_units_are_unique_and_number_thirty, among the tests above; not itself a pytest total)
### exit: 0
```

What each number counts:

| number | what it counts |
|---|---|
| cut 5's line | cut 5's own N2 arms, run by `cut5_acceptance.py` inside the cut-7 prefix — cut 5 unchanged under this branch |
| cut 6's line | cut 6's own N2 arms, likewise — cut 6 unchanged under this branch |
| cut 7's line | cut 7's acceptance module `test_n2_cut7.py`: its portable journey and its 48-arm declaration audit — cut 7 unchanged under this branch |
| phase 2's line | cut 9's phase: its **30-arm sabotage audit** *plus* the inventory reconciliation against the frozen document, the §5/§6 obligations as source-borne checks, the citation-metadata reconciliation, and the prior-cut freeze guard — pytest nodes, not declaration units |
| `30` | the **declared-unit count**, `len(CUT9_ARMS)`, pinned by `test_the_declared_units_are_unique_and_number_thirty` among phase 2's tests. **It is not a pytest total** and the runner prints it on its own line saying so. |

**Cut 8 is cited, not run — and running it would red by design.** Task 4
deleted `_refuse_store_subject` and `StoreSubjectUnsupported`, the shape-only
refusal cut 8's label 6 and store-refusal arms certify, so those declarations
fail on this tree deliberately (execution ledger R15). Cut 8's discharge
stands as its frozen results record
(`2026-08-22-conformance-cut-8-results.md`), its declaration files are pinned
byte-identical by phase 2's freeze guard — **at `55b6de7`, its banking
commit, a deliberately stale pin** — and cut 9's store units are the
successor certification. The runner's docstring states this ruling as its
chaining authority, exactly as cut 8's docstring states its own.

**3 — the corpus guard.**

```text
$ cd python && set -o pipefail && uv run --frozen pytest tests/test_designs_corpus.py 2>&1 | tail -3
............                                                             [100%]
12 passed in 0.43s
```

Promoting the specification is exactly the act that rots several of these at
once — the design count, its spelled-out word, the date range, the citation
obligation — which is why this is an evidence item and not an afterthought.

**4 — the contributor-guide check.** It prints nothing on success and has no
`N passed` line to quote, so the evidence is its exit code.

```text
$ cd python && set -o pipefail && uv run --frozen python tools/check_guide.py; echo "### exit: $?"
### exit: 0
```

### 2.3 The other gates, at the same tree

| gate | command | result | claim |
|---|---|---|---|
| lint | `uv run --frozen ruff check` | All checks passed! | code quality |
| typing | `uv run --frozen pyright` | 4 errors, 0 warnings, 0 informations | typing; the four known baseline diagnostics carried since the slice-3 merge, not re-measured by this landing |
| whitespace | `git diff --check` | clean | no whitespace errors |

`pyright` takes no path argument here: the whole-project form is the gate, and
four is the baseline this branch inherited at its base — no task of this slice
added or removed a diagnostic (the ledger quotes the count at every task).

## 3. Commit identities

Base `6bbe855` on `main`. The commits this discharge measured, in order:

| commit | subject |
|---|---|
| `b29c814` | docs(specs): draft the world-index slice-4 root-lifecycle spec |
| `c55dcb2` | docs(specs): close the slice-4 spec review's six findings |
| `26a4721` | docs(specs): close the second review's five findings on the slice-4 spec |
| `56db3f3` | docs(specs): align the binding-mismatch paragraph with the five-value union |
| `84bb4e4` | docs(log): lift the empty-baseline amendment for fork geneses (L6) |
| `552561b` | docs(designs): draft conformance cut 9 (root lifecycle and store substrate) |
| `0977bde` | docs(designs): close the cut-9 second reader's sixteen findings |
| `868cddd` | docs(designs): freeze conformance cut 9 at 0977bde |
| `ce1cddb` | docs(plans): root-lifecycle (slice 4) implementation plan against frozen cut 9 |
| `579aaeb` | docs(plans): revise the slice-4 plan on the pre-execution review's six findings |
| `237007b` | docs(plans): close the second pre-execution review's six blockers |
| `fe57798` | docs(plans): close the third pre-execution review's four blockers |
| `cf09504` | docs(plans): close final root-lifecycle review blockers |
| `b3a965c` | docs(plans): let register_root discriminate the store-init retry |
| `71d7033` | docs(plans): root-lifecycle execution ledger |
| `7db3e38` | docs(plans): remove ledger trailing whitespace |
| `b31c855` | docs(plans): pin Task 2 to the reviewed atoms lifecycle design |
| `cdd80c9` | docs(plans): distinguish root claim choreography |
| `6c3af86` | docs(plans): record the Task 2 atoms implementation in the ledger |
| `560c859` | feat(root): store roots and the canonical store projection |
| `8e14f8a` | feat(world): store subjects through anchor, export, and audit |
| `ee590d2` | feat(root): lifecycle wrappers and the writability-gate precedence |
| `588fc9e` | feat(root): restore_root under one held boundary |
| `d0d632d` | feat(root): fork acts, fork geneses, and the L6 lift in code |
| `d28d5ce` | feat(world): act-minted fork admission and lifecycle-aware arrival |
| `c047be4` | test(cut9): declare the 30 frozen arms |
| `d29a98f` | test(cut9): certified acceptance runner |

The banking commit that follows carries this record, §8's amendment set, the
finalized execution ledger, and **two Python edits, both forced by a gate and
neither behavioural**: two entries added to the corpus guard's design-count
spelling table (`_COUNT_WORDS` gains 33 and 34 — promoting the specification
takes the design corpus from 32 documents to 34 counting cut 9's own frozen
document, committed earlier on this branch, and the guard refuses a count it
cannot spell), and one line added to `.gitignore` (`.cut9-acceptance/`,
closing for this cut the gap cut 8's results §7.4 recorded for cuts 5–7).
The ledger appends beside each task's commit, so the plan-execution history
above already contains its intermediate states.

Cuts 5, 6, 7 and 8 are prefixes or pins, never edits. `test_n2_cut9.py`'s
`FROZEN_PRIOR_CUT_FILES` pins the prior-cut surfaces byte-identical via
`git diff --quiet <pin> HEAD`: cuts 5–7's declaration modules, runners, and
amended acceptance modules at the pins cut 8 recorded, and **cut 8's own
declaration module, audit module, and runner at `55b6de7`**, its banking
commit — a pin that is *deliberately stale* as a current-tree claim (R15,
§2.2 above): the files are unedited, and the refusal they certify is gone.

**The history constraint is inherited and extended.** Cut 7's results §7
binds every future integration commit to keep `4a7dc19` and `c8c0b12`
reachable; cut 8 added `117f37e`; cut 9 adds its freeze pin `0977bde` to the
same class. A squash merge or a rebase that orphans any of the four reds the
frozen-cut guards, and per the frozen-cut rule the red cannot be repaired by
editing a cut.

## 4. The cross-repository prerequisite

This slice required the fail-closed writer state and five new public commands
in the sibling `atoms` repository, behind their own design gate (spec §2–§4;
the atoms-local design `docs/2026-08-23-root-lifecycle-commands-design.md`
there, approved at `b1469f4`):

- the **schema-v3 host bookkeeping** — the singleton `root_lifecycle` row
  binding machine identity and canonical root path, the retained
  `root_operation` row, and the ten reviewed triggers, with exact v2
  read-only unserviceable until the operator migration;
- `replicate_root` and `fork_root` — the copy pipeline with the claim-only
  no-clobber destination, canonical request/snapshot proofs, the recorded
  phase machine, and the fork retry split at the grant, with
  `read_pending_fork_operation` and `resume_fork_root` as the
  resume-before-mint seam;
- `grant_read_serviceability` — structural, idempotent, refusing writable,
  binding-mismatched, exact-v2, incomplete-operation, and residue-bearing
  roots;
- `read_lifecycle_state` — the closed five-value union; and
- `migrate_root_to_lifecycle_v3` — the operator-authorized transition.

They were designed, reviewed, implemented, **merged into the local `atoms`
`main` and pushed the same day**: the first merge `ff144e7` (Task 2), and the
amendment merge `bf559c2` (`fb95e1a` — carrier-less registered inspection
answers the detached classification, the correction R17 records against R13's
first reading, forced by cut 9 L2u1's requirement that a cold copy's chain
stay judgeable through the audit act). **The `atoms` remote `main` stands at
`bf559c2`**, so — unlike cut 8's discharge, which recorded an unpushed-head
disclosure and corrected it only after the fact — cut 9's reproduction
prerequisite is satisfied from the remote at discharge, and there is no
unpushed disclosure to record. Adoption-ledger row 4 names the pushed head.

The commands' own behaviour is **not re-certified here**. Their tests live in
`atoms` (the atoms worktree's suite read `6205 passed, 7 skipped` at the
Task 2 merge, quoted in ledger R11); this cut consumes the seam contract and
gates on the landed commands. Cut 9 §2 says the same thing in its own words:
the merged atoms lifecycle seam is *certified engine*, not this cut's
mutation surface.

## 5. What the discharge establishes

**The root lifecycle closes fail-open copy semantics.** Before this slice, a
copied root was indistinguishable from its original and a second cooperative
writer was one `cp -r` away. Now:

- every root carries **engine bookkeeping binding machine identity and
  canonical path**, and `read_lifecycle_state` reads the closed five-value
  union — writable, read-only serviceable, read-only unserviceable,
  metadata-less, binding-mismatched — with the mismatch its own declared
  state, never the state the bytes claim;
- **cooperative mutation requires a validated writable grant**, the refusal
  unconditional and first (label 11's precedence: a metadata-less copy
  refuses by lifecycle state; `PendingUnresolved` remains the pending gate's
  refusal of a *writable* root), so a copy, an interrupted copy, and a
  cold-bootstrapped tree all fail closed;
- **`replicate_root`** produces a same-chain read-only copy whose stamp is
  durable before exposure, and **`restore_root`** is the one held Science
  boundary from inspection through capture, evaluation, the subject-agreement
  gate, and the read-serviceability grant — `validated` with a disagreeing
  subject admits nothing, and a residue refusal propagates loudly;
- **two metadata-less copies of one `store_id` restore on two hosts into
  read-only service**, writes refused on both — the sole writable exit is a
  fork under a fresh id, so two cooperative writers of one store stay
  unconstructible (L10u9).

**The store becomes a first-class root kind.** `init_store_root` mints the
opaque 32-hex `store_id` into a `store(store_id)` genesis and refuses a
populated root; the registered surface is the canonical whole-namespace
projection; `anchor_heads`, `export_head_artifact`, and the audit act take
store subjects resolved by supplied root under the genesis-binding rule
(`StoreIdMismatch` before head acceptance or registry mutation); and the
evaluator judges store chains through the same four-outcome core — cut 8's
shape-only store boundary is retired, cut 9's V-labeled store units its
successor certification.

**The fork acts land, and L6 is read at last.** `fork_corpus` and
`fork_store` mint the child on the engine's fork seam, resume-before-mint, the
two `forked_from` facts distinct: the fork genesis carries the parent's
genesis and head digests, the child manifest the parent `corpus_id` and
corpus-state identity — act-derived under the source's held lease, never
caller-supplied (W13u2). The fork genesis registers its copied destination
surface as a **populated baseline** — the one minting path — so both L6 arms
are constructible for the first time: delete a baseline-covered pre-log
member under an anchor → refuted at replay; the anchor-free consistent
omission → unresolvable at best, the baseline's own claim (L6 full, the row's
first certification since it was written). The distinct-fork-genesis
refutation (L4u2) fires the genesis-mismatch mechanism for a corpus for the
first time. The fork product admits end-to-end through `World.admit`'s
`ForkOf` validation with no fixture-authored manifest, and `admit_arrival`
branches its inspection mode over the full lifecycle union — registered on
serviceable, detached on unserviceable/metadata-less/binding-mismatched,
**writable refuses**: this host's own live root is not an arrival.

## 6. What this run does not claim

The frozen cut's own §8 limitations stand unchanged:

- **No persistence-cut harness** (fourth cut running): every kill-at-stage
  and durability-order interior defers to the atoms certification; this cut
  reads the resulting states, with the citations declared as metadata (§1.2).
- **Holdings-read consequences defer**: L10u8 and L10u10 certify lifecycle
  state and mutation/validation refusals; unresolvable-for-holdings-reads and
  dereference-minting behavior wait on the holdings slice (§1.1).
- **Intent qualification remains entirely out.** The lifecycle acts append no
  intents; the store-dereferencing holdings intents arrive with the holdings
  slice.
- **The evaluator is certified over fabricated states** for engine-interior
  productions, bounded by the well-formedness obligation (every fabricated
  chain passes `inspect_chain`; every fabricated bookkeeping state reads back
  through `read_lifecycle_state`); the atoms suite is the standing
  mitigation.
- **Migration provenance is attested, not proven**: the refusals and the
  authorized path's mechanics are certified, never an operator's attestation.
- **W13's standing deferrals stay cut 6's**, named there and in cut 9 §3.1:
  coverage-declaration invariance, the coordinated forgery and its variants,
  two-corpora uniqueness, the two-projects negative, and the rest stand
  exactly where cut 6 §3.2 left them.
- **The acceptance-node dependency** noted in cut 7's results §8 applies
  unchanged: explicit node ids beating `--ignore` is undocumented pytest
  behaviour the harness relies on.
- **No quotation drift this time.** Cut 9's four quoted rows were checked
  byte-exact against their live source tables at this banking: the banking
  amendment set touches no guarantee-table row (the L6/L4/L10 amendments it
  relies on landed *before* the freeze, so the frozen quotations carry them).
  Cut 8's §7.5 drift remains cut 8's own, unchanged.

## 7. Known limitations and departures of the landed implementation

Recorded honestly and not fixed in this landing. Each ruled departure is in
the execution ledger and stated where it lands.

- **R12 — completed-retry precedence.** Under the reviewed §8, a completed
  `register_root` retry answers from its retained operation record without
  touching the chain; the pending-registration gate binds exactly the two
  chain mutators. One atoms pending-gate test was re-pinned to that reading.
- **R13 corrected by R17 — the inspect-gating amendment, mid-slice.** The
  first reading refused `inspect_chain` over metadata-less roots; that made a
  cold copy's chain unjudgeable through the audit act, which cut 9 L2u1
  requires (`unresolvable at step 3` over the copied root). Atoms `fb95e1a`
  answers a carrier-less registered inspection with the detached
  classification; a live transaction record without a grant stays
  `ChainStateInvalid`; `read_chain` still refuses without a grant;
  binding-mismatched roots refuse both. The amendment is the one mid-slice
  atoms correction this execution needed.
- **R16 — one error class beyond the plan's file list.** `StoreIdMismatch`
  in `science/errors.py`, the store analog of `WorldIdMismatch`: the acts'
  genesis-binding refusal fits no existing error, and `LogEvidenceRefused`'s
  closed constructor is the engine seam's.
- **R21 — one TDD sequencing deviation, recorded as the plan invites.** The
  arrival-mode selection was implemented before its failing-test run, so the
  mode tests' first execution passed; their assertions were verified against
  the recording seam rather than a red run.
- **Store validation is deliberately narrow this slice.** A store validates
  empty or with a fork-form genesis; raw-authored payload replays as a
  disagreement (R19's pinned fixture fact). Holdings — the records that make
  store payload registered surface — are the next slice's row.
- **`science/world/verify.py` remains the package's largest module**, now
  carrying the store-subject evaluation and the restore core as well; the
  boundaries remain the natural seam if it is split. The two helper
  duplications cut 7's results §8 recorded are still unfixed; this slice
  added no new spelling of either.
- **No lock file enforces the "never run two acceptance runners
  concurrently" rule**; the shared `SCIENCE_CUT*_ROOT` work directories keep
  it a convention, one more runner wide than before.

## 8. Corrections this landing made to the banked and frozen text

Per this repository's rule that a status header and a design sentence are
claims about the past, each of the following was checked against the tree and
corrected in the banking change.

1. **The slice-4 spec was promoted** to
   `docs/designs/2026-08-23-world-index-root-lifecycle-design.md` (spec §8
   step 7), its status header rewritten from "promotes at banking" to banked,
   naming this record, the ledger, and the pushed atoms head.
2. **Cut 9's status header** gained the discharge note — and the promoted
   path of the spec its frozen Sources block cites at the pre-banking
   `docs/superpowers/specs/` home, which is not edited (the cut-8 §8.12
   treatment, repeated).
3. **The cut-8 successor ruling, recorded rather than hidden** (execution
   ledger **R15**): Task 4 deleted the shape-only store refusal cut 8's
   label 6 and store-refusal arms certify, so those declarations are
   deliberately stale on this tree. Cut 8's discharge stands as its frozen
   results record; its declaration files stay pinned byte-identical at
   `55b6de7`; cut 9's store units are the successor certification; and the
   cut-9 runner's docstring carries the ruling as its chaining authority.
   **Cut 8's own frozen documents — including its results record's §6 store
   sentences — are untouched**, on the standing rule that a frozen record
   states the world at its own discharge.
4. **Adoption-ledger row 4** gains the root-lifecycle prerequisite as landed
   — the writer state, the five commands, the atoms-local design gate, and
   the **pushed** remote head `bf559c2` — discharging the holdings-
   prerequisite clause for the lifecycle commands, with the coordinator
   dereference-and-hash read and mutator post-state capture named as that
   clause's outstanding remainder.
5. **Adoption-ledger row 2** — "fork construction remains outstanding …
   `fork-of` admission still uses fixture-authored manifests" — closes:
   `fork_corpus` act-authors the manifest and admission is proven end-to-end
   (cut 9 W13u2).
6. **Adoption-ledger row 5's remainder shrinks** to exactly intent
   qualification, event-level L8, and the L13 preimage resolver — L10's
   fork, replica-construction, restore and store arms landed, L6 read at
   last.
7. **Log-verification design limitations 2, 3 and 6 close** with dated
   markers (store subjects spelled through the acts; fork/replica/restore
   built and read; L6 lifted by the fork-baseline rule), and its §3.2
   store-writer sentence gains the landed pointer.
8. **Packaging limitation 5 narrows**: act-minted forks' `forked_from` is
   act-derived under the held lease; the limitation holds in full for
   hand-authored manifests.
9. **The README's design table gains cut 9 and the promoted design**, and its
   count sentence moves from "Thirty-two … through 2026-08-22" to
   "Thirty-four … through 2026-08-23".
10. **Two guide pages are corrected**:
    `docs/guide/identity-world-and-change.md` gains the root-lifecycle
    current state and cites both new documents and this record;
    `docs/guide/contracts-and-adoption.md`'s current state moves from
    "Cuts 1–8" to "Cuts 1–9" and removes the fork/replica/restore arms from
    the open remainder.
11. **The stale-claim grep** (`fork construction remains|store subjects are
    shape-only|row 4's|wait on row 4`) was run over `docs/` and `README.md`;
    every live hit is corrected by the items above. The remaining hits are
    frozen records (cut 8's results, the log-verification ledger and plan)
    and cut 8's frozen §8 — deliberately left alone, as the freeze
    discipline requires.

    **The frozen conformance cuts were deliberately left alone** beyond
    cut 9's own status header: cuts 2–8 and the disposition record carry
    deferral language this landing makes historically stale; a frozen cut's
    deferral table states the world at its freeze.

## 9. Execution record — the ledger, at a tracked path, every task boundary

This slice was executed inline with the same ledger discipline slices 2 and 3
converged on: **all rulings are in
`docs/plans/2026-08-23-root-lifecycle-ledger.md`** at a tracked path, with
the atoms and Science heads recorded beside them, appended and committed at
every task boundary — R1–R10 with the reviewed plan and atoms design gate,
R11–R23 each at its task's commit, R24 the banking task's own. Nothing in
this execution depends on a file that lives only in a worktree.

Rulings with obligations discharged in this document: R11 (§4), R15 (§2.2,
§3, §8.3), R16 (§7), R17 (§4, §7), R21 (§7), R22 (§1.2), R23 (§2.2).
