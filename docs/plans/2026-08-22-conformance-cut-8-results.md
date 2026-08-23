# Conformance cut 8 — discharge results

**Date:** 2026-08-23
**Subject:** log verification and anchoring, world-index slice 3
(`docs/designs/2026-08-22-log-verification-design.md`, promoted from the
implementation spec in this same change), measured against conformance cut 8's
frozen selection (`docs/designs/2026-08-22-conformance-cut-8.md`).

**The frozen cut's rows, selected bullets, labeled declarations, obligations
and accounting are not edited here.** Cut 8 froze on 2026-08-22 at `117f37e`;
only its status header changed — at banking, to record the discharge and
point at this document, and once more at the whole-branch review, to carry
§7.5's comparison basis for its own quoted rows. Results are recorded separately, which is what this is.

**Integration state.** Every commit named in §3 was made on the implementation
branch `design/log-verification`, whose base is `cd549aa` on `main`. **The
branch is not merged.** It is ready for the `--no-ff` merge, and the merge is
the human partner's act, as it was for slice 2. Nothing below claims otherwise:
where a banked document now says this slice landed, it says so about this
branch.

**Corrected 2026-08-23.** The merge landed later the same day: `--no-ff`
integration commit `10cc84b` on `main`, preserving branch history as §7's
constraint requires. The paragraph above is true of the discharge and false of
the present.

## 1. The accounting, re-derived

Recounted from the frozen cut's own §3 bullets rather than copied from its §4.

| state | rows | n |
|---|---|---:|
| full | L3, L5, L9, L11, L12 | 5 |
| part | L1, L2, L4, L7, L8, L10, L13 | 7 |
| unread | L6 (§3.2) | 1 |

**5 full + 7 partial = 12 rows read; L6 unread.**

Declaration units, counting each **Selected** and **Labeled** bullet once at its
home:

| row | L1 | L2 | L3 | L4 | L5 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | labeled |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| units | 1 | 5 | 4 | 7 | 2 | 2 | 2 | 5 | 1 | 4 | 5 | 5 | 10 |

The twelve rows sum to 43; the ten §3.3 labeled declarations sit outside the row
accounting. **43 selected + 10 labeled = 53 declaration units.** The landed
declaration module `python/tests/acceptance/n2_arms_cut8.py` carries exactly 53
arms with the same per-row distribution, ten of them `D1`–`D10`, and cut 8's own
§3.1 dispositions and §4 accounting are *parsed out of the frozen document* by
`test_the_selected_partition_is_the_frozen_cuts_own` rather than restated in the
suite — a table that agreed with a copy of the cut would be agreeing with
itself.

### 1.1 Unit dispositions: 51 full, 2 partial

The row dispositions above are the frozen cut's. This is the finer accounting
the landing owes, and it is the one the any-unrun-arm rule is measured against:
of the 53 declared units, **51 are certified in full and 2 are partial**
(execution ledger R37). Neither is argued into fullness. L2u5's declared
`asserts` text opens with the word **partial** and names the unrun command;
L7u1's does not use the word, and instead states only the two spellings it
covers, so the unrun third is visible as an omission from the claim rather than
as a caveat attached to it. Both readings are stated below, because an omission
is easier to miss than a caveat.

- **L7u1 — partial.** The frozen L7 clause names a `fulfills` pointing at an
  intent that is *missing*, *non-ancestor*, or *not an intent*. The missing and
  non-intent spellings run on disk against the engine's own validator. The
  **non-ancestor spelling is directory-unconstructible**: a linear
  content-addressed chain cannot present a referent that exists and is not an
  ancestor without a cycle, since a later entry's digest depends on the entry
  that references it. That spelling is certified in `atoms`'s typed validation
  core (an injected entry map), which is where the atoms chain-inspection design
  homes it, and nowhere in Science. The arm is declared and counted as covering
  the two constructible spellings only.
- **L2u5 — partial.** Cut 8's L2 bullet enumerates the pending gate's
  `PendingUnresolved` refusal from **all three** commands —
  `register_root`'s existing-chain arm, `append_intent`, and `run_transaction`.
  Two run. `register_root`'s existing-chain arm **has no Science mapping at
  all**: both Science root initializers call `register_root` bare, which the arm
  pins mechanically with a source assertion, so there is no Science behaviour to
  exercise and no mapping to falsify. The two that do run are asserted to agree
  on `(applied, index)` — the second production mapping, in
  `DurableOperationPort.append_intent`, was armed in the Task-10 fix round
  because its own comment said the two mappings must not drift, and the
  agreement assertion was verified to bite by mutating each site independently.

### 1.2 Obligation 1 is discharged two ways, and the split is stated

Cut 8 §5's obligation 1 — *every fabricated chain passes `inspect_chain` as
well-formed unless the arm's point is the defect, in which case exactly that one
defect class and no other* — is met literally by some units and by a narrower,
named substitute for others. The partition is mechanical, not editorial:
`FABRICATION_BY_UNIT`, `VIEW_LEVEL_UNITS` and a two-name static set are
reconciled against the declared units by
`test_every_declared_unit_states_its_fabrication_or_states_why_not`, so a unit
cannot fall out of all three and be excused by silence.

- **35 units** judge **real on-disk canonical envelopes**, read back through the
  engine's own `inspect_chain_detached`. Each names its builder; every builder
  is catalogued with the engine's verdict, in both directions (each catalogued
  fabrication is claimed by a unit, and each unit's fabrication is catalogued),
  and each of the **nine deliberate defects asserts exactly one engine defect
  kind**.
- **16 units** hand a chain **view** to a stubbed seam and **cannot** meet the
  obligation literally. They are admitted on a ground narrower than "no
  directory exists": **the arm's claim does not turn on the chain** — it turns
  on lock order, precedence, refusal placement, admission identity, or the count
  of evaluator calls. The ground is recorded per unit, drawn from two admissible
  spellings and no third. The obligation's *purpose* is then run over the nine
  stand-in units through a per-unit view-factory table: a structural
  well-formedness predicate reads the very views each arm hands its seam, pinned
  against the engine on the three defect classes a linearization can express.
  The other seven read no chain at all, so obligation 1 is inapplicable rather
  than substituted for.
- **2 units** (L1u1, L12u2) are source-surface assertions over the package —
  the unspellability of an unregistered cooperative mutation path, and the
  absence of a second summary model — and fabricate no chain.

**Three of the sixteen were convertible and were not converted.** L10u1, D3 and
D4 run over real roots with a real executor and could have been converted the
way L4u6, L11u3 and L11u4 were. They were not, because the conversion would
rewrite Task 9's reviewed arrival fixtures without changing what the arms
assert. That is a cost of this landing, recorded here and in the declaration
module rather than argued away (execution ledger R38).

**The residual cost of the substitute, named.** The view factories call the same
helpers the nodes call, but the *arguments* are still restated. If a node
changed which root it copies, which world id it mirrors, or how many shapes it
hands its seam, the table would go on checking a stale replica of the old one
and nothing would say so. Removing that would mean refactoring the arrival
fixtures to expose their own view construction — the same cost as above.

## 2. What ran, and where

Science resolves `atoms-core` and `nodes-core` as editable path dependencies
(`python/pyproject.toml` `[tool.uv.sources]`). All gates ran from this
repository's `python/` directory, sequentially — never concurrently, because the
cut-5, cut-6, cut-7 and cut-8 runners share `SCIENCE_CUT*_ROOT` work
directories.

**Evidence order.** Cut 8 §5's obligation 7 is homed here, and its discipline is
that a count claim quotes pytest's own summary line under `pipefail`, never a
collect-only count. Every command below was run **after the last edit to the
tree it measures** — after the banking amendment set of §8, after the spec's
promotion, after the stale-claim sweep, and after both Python edits the gates
forced (§3). **The set was collected three times**, because the tree moved twice
after the first collection and evidence recorded before the last edit is not
evidence of the final tree:

1. after the banking change's edits;
2. after §8.11's push-state correction, which edited
   `docs/designs/2026-08-03-redesign-adoption-ledger.md` (row 4) and
   `docs/plans/2026-08-20-conformance-cut-7-results.md` (§4) — the first of those
   is under `docs/designs/`, which the corpus guard reads, so a re-collection was
   owed and not optional;
3. after the one whole-branch-review correction a gate can see — §7.5's
   clause in cut 8's status header, a file the corpus guard reads. The
   review's other three corrections live in this file and were written
   after this collection.

**All three collections agree on every count and every exit code**; the run
pasted below is the third. Every tree change made after it is prose in this
file (§2.1, §2.3, §3, §6, §7.5, §8.12, §8.13 and §9's ruling count) or in the
execution ledger. None of those is read by any gate: the corpus guard reads
`docs/designs/`, `docs/guide/` and `README.md`, and `check_guide.py` reads
`docs/guide/`. Both resolve *links into* `docs/plans/` — this file's own path
among them, which is why it was created before the runs — but neither reads a
word of what is inside one.

### 2.1 Host and certified tuple

- backend `LinuxBackend`; storage profile
  `StorageProfile(profile_id='flush-honoring-disk.v1')`
- work directory: default, `.cut8-acceptance` beside the checkout —
  `SCIENCE_CUT8_ROOT` unset, so the certified volume is the repository's own.
  The runner makes one `run-` directory beneath it and points the cut-7 prefix
  at that same directory through `SCIENCE_CUT7_ROOT`, so the whole command
  occupies one certified volume and removes what it made.
- volume: ext4 on `/dev/nvme0n1p2`, mounted `rw,noatime,data=ordered`
- kernel `7.1.8-arch1-3`
- source commit `4389d2a`, plus the close-out commits' own edits (§3)

### 2.2 The four evidence items

**1 — the full portable suite.** Run bare: `pyproject.toml`'s `addopts` already
carries `-q`, so a second `-q` produces `-qq` and suppresses the very count the
claim rests on. The suite excludes `tests/acceptance` by configuration
(`--ignore=tests/acceptance`), so this is portable behaviour and **no**
durability claim.

```text
$ cd python && set -o pipefail && uv run --frozen pytest 2>&1 | tail -2
......................                                                   [100%]
2182 passed in 332.15s (0:05:32)
```

**2 — the cut-8 acceptance command.** This is the discharge. Four numbers, and
only three of them are pytest summary lines.

```text
$ cd python && set -o pipefail && uv run --frozen python tools/cut8_acceptance.py
[cut8 phase 1/2] cut7_acceptance.py
[cut7 phase 1/3] cut5_acceptance.py
.......................................                                  [100%]
39 passed in 14.52s
[cut7 phase 2/3] cut6_acceptance.py
.......................                                                  [100%]
23 passed in 11.18s
[cut7 phase 3/3] test_n2_cut7.py
..........................................                               [100%]
42 passed in 40.32s
[cut8 phase 2/2] test_n2_cut8.py
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 13.07s
declared units: 53 (pinned by test_the_declared_units_are_unique_and_number_fifty_three, among the tests above; not itself a pytest total)
### exit: 0
```

What each number counts:

| number | what it counts |
|---|---|
| `39 passed` | cut 5's own N2 arms, run by `cut5_acceptance.py` inside the cut-7 prefix — cut 5 unchanged under this branch |
| `23 passed` | cut 6's own N2 arms, likewise — cut 6 unchanged under this branch |
| `42 passed` | cut 7's acceptance module `test_n2_cut7.py`: its portable journey and its 48-arm declaration audit |
| `76 passed` | cut 8's phase: its **53-arm sabotage audit** *plus* the inventory reconciliation against the frozen document, obligations 1–6 and both freeze obligations, and the prior-cut freeze guard — pytest nodes, not declaration units |
| `53` | the **declared-unit count**, `len(CUT8_ARMS)`, pinned by `test_the_declared_units_are_unique_and_number_fifty_three` among the 76 above. **It is not a pytest total** and the runner prints it on its own line saying so. |

**Terminal result: exit 0.** The runner probes the certified tuple before any
collection and treats an uncertified volume as an error, never a skip: an
environment that cannot exercise durability must not be able to report cut-8
discharge.

**3 — the corpus guard.**

```text
$ cd python && set -o pipefail && uv run --frozen pytest tests/test_designs_corpus.py 2>&1 | tail -3
............                                                             [100%]
12 passed in 0.40s
```

Twelve guards, all mechanical and all over *documents*: the design corpus's
`atoms` adoption state, the completeness of every guarantee table against the
row inventory, the README's design count and its date range, the guide's
obligation to cite every design, and that every cross-reference resolves.
Promoting the specification is exactly the act that rots several of them at
once, which is why this is an evidence item and not an afterthought.

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
| typing | `uv run --frozen pyright` | 4 errors, 0 warnings, 0 informations | typing; the four the implementation plan fixes as the baseline present at merge `83744e7`, not re-measured there by this landing |
| whitespace | `git diff --check` | clean | no whitespace errors |

`pyright` takes no path argument here. A narrowed `pyright src` reports 0 and
hides the rest of the project; the whole-project form is the gate, and 4 is the
baseline, not a regression introduced by this slice. It returned **5** before
the suppression recorded in §3 and 4 after; that suppression is the last code
edit this tree received, and every number above was collected after it.

## 3. Commit identities

Base `cd549aa` on `main`. The commits this discharge measured, in order:

| commit | subject |
|---|---|
| `b481b61` | docs(log): draft conformance cut 8 for log verification and anchoring |
| `c5700ed` | docs(log): close the cut-8 second reader's five findings |
| `117f37e` | docs(log): freeze conformance cut 8 and record the reader discharge |
| `86d142e` | docs(log): commit the slice-3 spec, plan, and execution ledger |
| `65062e5` | docs(log): align the spec's §2 seam duty wording with ruling R1 |
| `5230da0` | docs(log): fold the atoms gate's rulings into the spec, plan, and ledger |
| `1319dd2` | docs(plans): test the TransactionHalted adapter arm at Task 4 |
| `8da0563` | docs(plans): record the task-2 atoms head in the ledger |
| `7d2f2a2` | feat(world): log-head record and head-artifact codecs |
| `aa84e01` | docs(plans): correct PendingUnresolved's import path to atoms.chain.errors |
| `b17a38d` | feat(root): the log seam, chain views, and the lock-only lookup |
| `d374bb2` | fix(root): catch every spelling of the composition-root import |
| `d6024e0` | docs(plans): ledger rulings R10-R12 from the task-4 review |
| `886a289` | feat(world): anchor act, head export, and build-origin records |
| `ed835fb` | fix(world): derive the build's anchors from the epoch member it publishes |
| `51725ba` | docs(plans): ledger rulings R13-R15 from the task-5 review |
| `6c0c5a8` | feat(world): registered-surface replay and the removal policy pass |
| `b72e717` | fix(world): complete the removal inventory and scope the classification to the held copy |
| `53be666` | docs(plans): ledger rulings R16-R20 from the task-6 review |
| `0d7a3f0` | feat(world): the four-outcome log evaluator |
| `68bd77a` | feat(world): state each bound anchor's custody in the report |
| `dfe603f` | fix(world): one statement of each genesis form, and one of each provenance |
| `3842804` | docs(plans): ledger rulings R21-R28 from the task-7 review |
| `7baba57` | feat(world): the audit act and the ordered-cuts predicate |
| `3731fdf` | fix(world): read the audited root's claim after recovery, not before |
| `d1ff306` | docs(plans): ledger rulings R29-R33 and the task-12 spec amendments |
| `5215bb1` | feat(world): verified arrival and the open-world agreement check |
| `21379ec` | fix(world): D10's four clauses, the arrival provenance arm, and the exact provenance test |
| `6b858ab` | fix(world): condition open_world's unregistered-root mapping on the engine's own wording |
| `97ba01b` | docs(plans): ledger rulings R34-R36 and the task-9 head |
| `6a8ccb2` | test(cut8): declare the 53 frozen arms |
| `cce804b` | fix(cut8): arm the second pending mapping and wire the view substitute per unit |
| `b42c709` | fix(cut8): correct the harness ground statement and complete the view factories |
| `0363077` | docs(plans): ledger rulings R37-R38 from the task-10 review |
| `232c409` | test(cut8): certified acceptance runner |
| `2bad282` | fix(cut8): self-describe the declared-unit count and correct a citation |
| `4389d2a` | docs(plans): state each acceptance count with what it counts |

The close-out commits that follow are documentation: the banking change that
carries this record and §8's amendments (`55b6de7`, the hash the execution
ledger's `## Heads` records), the finalized execution ledger, the correction
found while checking R1's precedent against the sibling repository rather than
against the sentence describing it (§8.11), and the whole-branch review's four
corrections — §9's ruling count, §7.5 together with the clause it added to
cut 8's status header, §2's evidence order, and §8.13. The branch history is the
exhaustive list; no count of close-out commits is given here, because such a
count goes stale on the commit that follows it. **None of them touches
`python/src` or any cut declaration.** The banking change makes two Python
edits,
both forced by a gate and neither behavioural: one entry added to the corpus
guard's design-count spelling table, since promoting the specification takes the
design corpus from 31 documents to 32 and the guard refuses a count it cannot
spell; and a `# pyright: ignore[reportMissingImports]` on the cut-8 runner's
deferred `n2_arms_cut8` import, whose `sys.path` entry is inserted three lines
above it at call time. The project-wide `pyright` gate returned five diagnostics
before that suppression and four after — the known baseline (execution ledger
R41, R43).

Cuts 5, 6 and 7 are prefixes, never edits. `test_n2_cut8.py`'s
`FROZEN_PRIOR_CUT_FILES` pins seven prior-cut surfaces — cut 5's and cut 6's
declaration modules and runners, cut 6's amended acceptance module, and **cut
7's declaration module and runner** — and shells out to `git diff --quiet <pin>
HEAD` for each. Cut 7's two surfaces are pinned at cut 8's own freeze commit
`117f37e`, because slice 3 begins with them exactly as the freeze left them.

**Cut 7's pinned audit module was amended under a ruling, and its declaration
module was not.** `python/tests/acceptance/test_n2_cut7.py` carries two
claim-preserving edits (execution ledger R13): the `ContentHeads` stub's
`genesis:<name>` label could not survive the log-head record form's 64-hex
validation, and X2's exact set equality could not survive a build-origin record
joining the epoch publication transaction. The tip claim stays
`corpus_state_identity`; set equality is retained and extended by an
exactly-one asserted record. `python/tests/n2_arms_cut7.py` and
`python/tools/cut7_acceptance.py` are byte-identical to `117f37e`, which is what
the freeze guard checks.

**Cut 7's history constraint is inherited unchanged.** Cut 7's results §7 binds
every future integration commit to keep `4a7dc19` and `c8c0b12` reachable;
cut 8's guard adds `117f37e` to the same class. A squash merge or a rebase that
orphans any of the three reds cuts 6, 7 and 8, and per the frozen-cut rule the
red cannot be repaired by editing a cut.

## 4. The cross-repository prerequisite

This slice required three new public commands in the sibling `atoms`
repository, behind their own design gate (spec §2, §8):

- `inspect_chain` / `inspect_chain_detached` — the never-raises structural
  inspection returning `WellFormedChain | MalformedChain | AbsentChain`, with
  one typed validation core shared by both modes and by the raising paths, so
  the fourteen-entry defect taxonomy cannot fork;
- the **batch path-state capture** command — `(backend, root, paths)` →
  `PathState`s in the engine's own vocabulary, which is what makes L12's "no
  second summary model" a mechanism rather than a promise; and
- the shared post-recovery **pending gate**, refusing `PendingUnresolved` from
  `register_root`'s existing-chain arm, `append_intent`, and `run_transaction`.

They were designed, reviewed, implemented, and **merged into the local `atoms`
`main` only — the merge has never been pushed to any remote.** The head is
`3aa5a766efb5275e444de193407992ce33e8edb7` (the `--no-ff` merge of
`design/chain-inspection`).

Science resolves `atoms-core` through an editable path dependency, so that local
merge is what makes this branch green. **Anyone reproducing this discharge needs
that `atoms` commit, and it exists only in a local clone.** Pushing it is a
prerequisite of any integration that expects a fresh checkout to build — exactly
the treatment `read_chain`'s `2c077ed` carries in adoption-ledger row 4, which
this head now joins (execution ledger R1).

**One correction to that row, found while writing this.** `2c077ed` itself is
**no longer unpushed**: it was pushed on 2026-08-22, after cut 7's results were
written, and the `atoms` remote `main` stands at it. Row 4 and cut 7's results
§4 both said the remote still stood at `7e97e09`, and both are corrected in this
change. So cut 7's reproduction prerequisite is satisfied, cut 8's is not, and
the local `atoms` `main` is nine commits ahead of the remote (execution ledger
R44).

**Corrected 2026-08-23.** `3aa5a76` was **pushed on 2026-08-23**, after this
record was written and after the branch merged; the `atoms` remote `main`
stands at it now. The paragraphs above are true of the discharge and false of
the present: reproducing this discharge no longer needs a local clone, and the
fresh-checkout prerequisite is closed. The treatment is `2c077ed`'s exactly —
the original sentences stand, and adoption-ledger row 4 is corrected in place
as the live authority.

The three commands' own behaviour is **not re-certified here**. Their tests live
in `atoms`; this cut consumes the seam contract and gates on the landed
commands. Cut 8 §2 says the same thing in its own words: the merged atoms seam
is *certified engine*, not this cut's mutation surface.

## 5. What the discharge establishes

**Artifact 5 — tamper-evident mutation log: carriage and verification both
land.** Slice 2 built the anchor carrier; this slice builds the Science half of
the verification the carrier exists for:

- the **registry log-head record** and its codec under the minted domain
  `science.log-head.v1`, with the `store` arm decodable and unreachable, and a
  `world` subject unconstructible;
- the **exported head artifact** and its codec under
  `science.head-artifact.v1`, and the locked producer `export_head_artifact`,
  which writes nothing, takes no actor, and refuses a subject that disagrees
  with configuration or genesis;
- the **explicit anchor act** `anchor_heads`, with `AnchorSubjectUnknown` and
  `AnchorTargetUnresolvable`, byte-identical re-anchoring as idempotent success
  submitting no transaction, and a same-name/different-bytes record refused as
  `LogHeadCollision`;
- the **one read-only log evaluator** with the four-step precedence
  (structure → anchors → pending → replay) over the closed outcome set
  `validated | refuted | unresolvable | malformed`, its report carrying
  `anchored_through`, the unanchored-tail extent, the pending set, the intent
  inventory *marked unevaluated*, and the observer bound with per-carrier
  provenance and custody;
- the **registered-surface projection and replay**, comparing in both
  directions over the union of replay-known and disk-discovered claimed paths,
  and the **removal policy pass** with its severity split — `record-removed` a
  warning, `failing-verification-removed` an error;
- the **audit act** `audit_log`, which takes the world *configuration* and an
  explicit target root, and stays callable on exactly the worlds `open_world`
  refuses;
- the **`ReplicaOf` arrival act** `admit_arrival`, with `World.admit`'s
  `ReplicaAdmissionRequiresVerification` refusal, the report-based cause
  ranking `malformed > refuted > pending > chainless`, and `SubjectMismatch`
  checked before the admission transaction and after the report-based refusals;
- the **world genesis↔mirror agreement check**, discharging the dated slice-1/2
  deferral — `open_world` refuses a mismatch, the world audit reports it; and
- **`epochs_ordered`**, the ordered-cuts predicate, over the world chain's own
  ancestry, with epoch sequence numbers read by nothing.

**Kernel §8.7 — three of the four recorded-mutation consequences close.**
Deleting a failing verification (G8), hand-editing a proposition's semantic
fields together with its stored hash (semantic identity), and deleting a
retraction record to restore its target's standing (5a's standing subtraction)
are all removals or rewrites *inside the registered surface*, and replay refutes
each against a surviving anchor. **G4 does not close**: discarding a failed
replay attempt is an intent-qualification question, and qualification is
unevaluated in every report this slice produces — it waits on the
intent-boundary slice. **G2a chronology is unchanged**: its strengthening stays
boundary-mediated-only, as banked, and the out-of-band negative stands.

**Artifact 4 — `atoms`: three more public commands land.** See §4. The
holdings-prerequisite commands of row 4 are untouched.

## 6. What this run does not claim

The frozen cut's own §8 limitations stand unchanged, and the design's dated
deferrals are preserved:

- **No persistence-cut harness.** Every kill-at-stage arm defers to `atoms`'s
  certification; Science-side observation of mid-transaction states remains
  unconstructible. This is the cut-7 X2 gap, fourth cut running, named rather
  than argued around.
- **The evaluator is certified over fabricated states** for engine-interior
  productions. The fabrication license is bounded by §5's well-formedness
  obligation and by §1.2 above, but a systematic divergence between fabricated
  and engine-produced chains would evade this cut; the `atoms` suite is the
  standing mitigation.
- **Intent qualification is entirely out.** The reduction, its findings, the
  boundary-side arms (placement freeze, no caller-supplied `fulfills`, kill
  windows) and both non-run intent shapes wait on the intent-boundary slice.
  L7's two units certify inspection taxonomy only.
- **L6 is unread entirely** (§3.2 there), and **L10's fork,
  replica-construction, restore and store arms have no certification here** —
  only its arrival-identity arm is read. Fork, replica and restore are row 4's.
- **Store subjects are shape-only.** The codecs round-trip the store arm; the
  anchor act's signature cannot spell a store; the evaluator refuses
  `StoreSubjectUnsupported` at the one API that can name one. Behaviour and the
  store-artifact writer are row 4's.
- **The L13 preimage-backed classification is deferred** on the named `atoms`
  blob-read seam, and the held-copy match is weaker than the spec first stated
  — see §7.1.
- **Event-level cross-chain order is deferred.** §7's predicate is the whole of
  L8 built here; spec-freeze/intent presence and exclusion reasoning across
  captured corpus heads is this design's own successor work.
- **Verification cost is measurement-gated.** No Merkle overlay is built
  speculatively.
- **The holder protocol remains open.** Nothing here learns which exported
  anchors survive; the surviving-observer bound is the whole detection claim.
- **The acceptance-node dependency** noted in cut 7's results §8 applies
  unchanged: explicit node ids beating `--ignore` is undocumented pytest
  behaviour the harness relies on.
- **Two of the frozen cut's quoted rows no longer match the live source
  table.** No disposition moves and no frozen text was edited, but the next
  second reader will hit a red running §7's byte-exactness charge unless they
  read §7.5 below first.

## 7. Known limitations of the landed implementation

Recorded honestly and not fixed in this landing.

### 7.1 The held-copy match is by path, not by digest — L13's second partiality

Spec §5.3 as first written said *a held copy resolves iff its digest matches the
recorded state*. **That is not implementable through the frozen Task-4 seam.**
Chain entries retain path *states*, states are opaque above the composition
root, and `LogSeam` exposes no state→digest accessor — verified against the
seam's surface, not assumed. The landed policy pass therefore decodes the held
bytes, derives the corpus path the copy's own identity claims, matches that
against the removed path, and names the digest the copy was **filed under**; two
copies claiming one path resolve nothing.

This is a **second, distinct departure**, beyond the §10.4 resolver deferral the
frozen cut already records: the deferral says the classification is absent
without a copy; this says the *match predicate itself* is weakened when there is
one. A single held copy of a different version of the same record can
misclassify a removal in either direction. Every finding message is therefore
scoped to what the evidence supports — it speaks about the held copy, never
about the removed bytes — and the risk the scoping exists to bound is a reader
taking `removal-classified` as proof the removed bytes were **not** a failing
verification, which is the understated immutability violation the pass exists to
catch. **L13 stays partial for this reason as well as for the resolver.** Spec
§5.3 carries the dated amendment; execution ledger R16 is the ruling.

### 7.2 Cut 6's X5 replica clause is superseded, not satisfied

Cut 6's declared arm X5 asserts that **a known id** refuses both `Fresh` and
`ReplicaOf` admission provenance
(`test_known_id_refuses_fresh_and_replica_provenance`). This slice makes a bare
`World.admit` of a `ReplicaOf` refuse `ReplicaAdmissionRequiresVerification`
**before the world lock and before any known-id consideration**, because a bare
admit holds no verdict to report. So the arm's **replica half no longer
demonstrates the row's claim**, even though its name, both refusals and its
green result all survive, and no frozen file was edited
(`test_world_registry.py` is not in `FROZEN_PRIOR_CUT_FILES`, and
`n2_arms_cut6.py` is untouched). Cut 6's sabotage direction is unaffected: its
harness mutates the tree materialized at its own source commit.

It is recorded here because cut 6's module docstring names exactly this case —
weakening a live check while leaving its name and green result in place — as
outside the harness's reach. **There is no way to preserve the claim:** a bare
admit can no longer reach the known-id check for a replica. The known-id refusal
for a replica is now `admit_arrival`'s, through the shared admission core.
Execution ledger R34 is the ruling; the world-registry design's
admission-algorithm section carries the amendment.

### 7.3 Departures from the spec, landed and stated

Each was ruled during execution, is recorded in the execution ledger, and is
stated in the code where it lands:

- **The world projection walks the three grammar namespaces**, not the exact
  registry/epoch/rules-store grammars (spec §5.1's words). Strictly broader: a
  raw-created foreign file *inside* a grammar directory becomes a head
  disagreement instead of vanishing. The departure runs toward more detection
  (R19).
- **The bookkeeping exclusion is a dot-prefix rule**, pinned to the grammars: a
  test pins that every grammar which can name a claimed path refuses a leading
  dot, so the equivalence is load-bearing rather than incidental. A future
  dot-prefixed claimable name would silently shrink the audited surface (R20).
- **`epochs_ordered`'s descent includes the settlement entry.** A publication
  linearizes registration → settlement, so the chain tip at the instant E1's
  publication commits *is* the settlement; strict descent would answer
  `unordered` for the archetypal sequential pair (R29).
- **The publication moment is the earliest committed settlement** of the
  registration creating `epochs/<e1>/anchors.yaml`. Accepted consequence: after
  a §9 deletion and republication the earliest settlement is retained, so a
  build started inside the deletion window answers `ordered` against an epoch
  whose members were absent at its preflight (R30).
- **An absent or malformed world chain answers `unordered`**, stated in the
  docstring rather than left as a fallback. A caller cannot distinguish "no
  order" from "unreadable chain"; the audit act is the named place a damaged
  chain gets named (R31).
- **`open_world` now reads the chain**, which §6.3 requires verbatim. Two
  disclosed consequences: opening a world now requires the certified volume,
  and it now takes the atoms project lock and resolves recovery, so opening can
  block on a concurrent build and is no longer a cheap read. Blast radius
  verified confined — no `tools/`, CLI or `src/` caller opens a world (R36).
- **An epoch carrier's identity revalidation is self-consistency, not
  provenance.** `from_export` recomputes the identity from the mapping the
  caller supplies, so a caller can fabricate all eleven members and pass a
  matching identity. That is the design's custody model — caller-attested and
  reported as such — not a defect (R23).
- **A future artifact arm reading a locally stored artifact** would be labeled
  `named-local` by the provenance discriminator and become ineligible for a
  world subject, diverging from §4.1's unqualified acceptance of artifacts
  there. Behaviourally inert today; stated in the carrier docstring (R21).
- **A `WorldUninitialized` reclassification.** One genesis-form predicate now
  owns the Science genesis grammar, and it is the strict one. An on-disk genesis
  naming an ungrammatical `world_id` refuses `WorldUninitialized` where it once
  refused `WorldIdMismatch` — within §3.2's documented refusal set, and
  unreachable for any world root Science can mint (R28).

### 7.4 Structure, coverage, and dependencies

- `python/src/science/world/verify.py` is now the largest module in the
  package. It carries the projection, replay, the policy pass, the evaluator and
  both boundary cores; the boundaries are the natural seam if it is split.
- The two helper duplications cut 7's results §8 recorded (`_require_lower_hex`
  defined twice, `_require_text` three times with divergent contracts) are
  **still unfixed**. This slice added no new spelling of either.
- `tools/cut7_acceptance.py`'s `PROBE_REFUSED` docstring defect is fixed in
  cut 8's runner, which states plainly that the code is *not* distinct from
  pytest's own `INTERRUPTED`. Cut 7's runner is frozen and still carries the
  wrong justification.
- `.gitignore` lists `.cut4-acceptance/` and `.cut8-acceptance/` and nothing for
  cuts 5, 6 or 7. Cut 8's runner works beneath its own ignored directory and
  points the cut-7 prefix at it, so the gap does not surface in this run.
- No lock file enforces the "never run two acceptance runners concurrently"
  rule; the shared `SCIENCE_CUT*_ROOT` work directories keep it a convention.
- **The cut-8 runner's prefix chaining is not the frozen cut's instruction.**
  No section of cut 8 mentions a prefix or a prior runner; the authority is the
  implementation plan's Task 11, and the runner says so in its own docstring
  rather than misattributing it.

### 7.5 Cut 8's quoted rows are a freeze snapshot: L4 and L10 have drifted

Cut 8 §7's standing second-reader charge opens with *verify every quoted row
byte-exact against the source table*. **Run against the live table today, that
check reds on two rows**, and it is meant to — but nothing in the frozen cut
could say so, so it is said here and in the cut's status header.

The banking change amended the source table, `2026-08-03-tamper-evident-log-design.md`
§10, in place: **L4** and **L10** each gained a dated `(amended 2026-08-23 …)`
marker carrying spec §1.2's genesis-subject consequence — for L4, that a
fabricated distinct corpus genesis is malformed before any anchor judgment so
replacement is refuted through anchored-head unreachability; for L10, that the
copy-under-a-fresh-manifest arm is demonstrated through `admit_arrival`'s
`SubjectMismatch` rather than a genesis-payload comparison. **L6** was amended
the same way with §1.3's empty-baseline consequence, but cut 8 does not quote
L6 — it is the unread row (§3.2 there) — so it is not part of the drift.

Measured, not asserted:

| comparison | result |
|---|---|
| cut 8 §3.1's twelve quoted rows vs. the source table **at `117f37e`** | all twelve byte-exact |
| the same twelve vs. the **live** source table | ten byte-exact; **L4 and L10 differ** |

**The comparison basis for cut 8 is `117f37e`, its own freeze commit.** That is
the whole of the remedy, and it is a documentary one: nothing in this repository
reads a cut's quotations against the design table it quotes — the corpus guard
checks row *inventories* and cross-references, never quoted text — so **no
mechanical guard enforces the pairing**. A reader who compares against `HEAD`
and stops there will conclude a frozen cut was tampered with.

Why it was done this way rather than avoided (execution ledger R39): amending
in place with a dated marker is this corpus's own convention for a frozen
table — L4, L7 and L10 already carried 2026-08-10 and 2026-08-11 markers before
this landing. Cut 8's §8 limitation 5 anticipated the inheritance and the
never-edit-here rule, though not this quotation drift: its conditional is
"if a future design lifts either", and nothing was lifted. The
alternative, keeping the amendments in section prose and out of the row cells,
would have left the guarantee table stating a mechanism the shipped code does
not implement, which is the failure this repository's design-doc rule exists to
prevent. Neither row's **disposition** changed: L4 and L10 are partial in the frozen
cut, which is the document that assigns dispositions, and the amendments to
the source table state mechanism, never verdict.

## 8. Corrections this landing made to the banked and frozen text

Per this repository's rule that a status header and a design sentence are claims
about the past, each of the following was checked against the tree and corrected
in the banking change.

1. **The slice-3 spec was promoted with two of its own claims corrected first.**
   A promoted design must not bank a claim the code contradicts.
   - **§5.3** — the held-copy digest match, replaced by the path match with a
     dated amendment (§7.1 above, ledger R16).
   - **§7** — `epochs_ordered(world, e1, e2)` was stale; the landed predicate
     takes a `WorldConfig`, which is forced by the act's own reason for
     existing: it must answer where `open_world` refuses (ledger R33).
   - **§9**'s expected dispositions carried L7 as wholly deferred. The frozen
     cut reads L7 as **partial**, with its two chain-structural units selected,
     and records that refinement itself. The section is labeled as an
     expectation "to be fixed at the cut's own freeze"; a dated pointer to the
     cut's actual dispositions now stands beside it.
2. **The log design's genesis-subject clauses (§3, §5, §6) and its L4/L10 arm
   mechanisms** are amended per spec §1.2: the corpus genesis is identity-free,
   so corpus anchor comparison is scoped by `(selected subject, genesis_digest)`
   and never by genesis alone; corpus-chain *replacement* is caught by
   anchored-head unreachability rather than genesis mismatch; the
   genesis-mismatch refutation fires for world subjects and future fork geneses;
   and subject mismatch is a lifecycle-boundary refusal even when the chain
   verdict is `validated`.
3. **The log design's L6 row and its baseline clause** are amended per spec
   §1.3: every genesis baseline is empty, genesis-form validation refuses a
   non-empty baseline as malformed, and both L6 arms are therefore presently
   unconstructible. L6 is wholly unread by cut 8.
4. **The world-registry design's admission algorithm** said "Known ids are
   refused uniformly … `replica-of` describes the first arrival." `World.admit`
   now contradicts that on the bare-admit path — see §7.2. The section carries
   the dated amendment and names cut 6's superseded X5 clause.
5. **Adoption-ledger row 5** said "Science anchor verification, the explicit
   anchor act, replay, genesis-to-mirror agreement, and L1–L13 remain
   outstanding." Carriage **and** verification have now landed, with the
   remainder named exactly: intent qualification and G4, the preimage resolver,
   event-level L8, and L10's row-4 arms.
6. **Adoption-ledger row 4** gains the three new `atoms` commands and the new
   **unpushed** head, disclosed exactly as `2c077ed` was.
7. **The kernel's §8.7 status line** said the four recorded-mutation
   consequences "close at implementation". Three close here; G4 does not, and
   chronology's strengthening stays boundary-mediated. The line now says which
   is which.
8. **The adoption ledger's dependency list** still read "L1–L13 await
   implementation after composition-root adoption" — false in two ways after
   this landing, and corrected.
9. **The README's cut-8 row was wrong before this landing.** It read "drafted
   2026-08-22, not yet frozen … L10 unread". Cut 8 froze on 2026-08-22 at
   `117f37e`, and the unread row is **L6**, not L10 — L10 moved from unread to
   partial when the second reader found its justification failed adversarial
   review. Both errors are corrected.
10. **Two guide pages said cut 7's work was on "a branch not yet merged".** It
    merged into `main` on 2026-08-22 at `83744e7`. Corrected in
    `docs/guide/contracts-and-adoption.md` and `docs/guide/foundations.md`,
    which is a stale claim this landing did not create but did surface.
11. **`read_chain`'s `2c077ed` is no longer unpushed.** Adoption-ledger row 4
    and cut 7's results §4 both said the `atoms` remote `main` "still stands at
    `7e97e09`". It was pushed on 2026-08-22 and the remote stands at `2c077ed`.
    Both are corrected; cut 7's record keeps its original sentence with a dated
    correction beneath it, because that record is a claim about its own
    discharge (§4 above; execution ledger R44).
12. **Cut 8's own frozen text cites the spec at its pre-promotion path**
    (`docs/superpowers/specs/…`). The frozen text is not edited; the cut's
    status header records the promotion and the new path, and — after the
    whole-branch review — the L4/L10 drift of §7.5 as well.
13. **Three further live design documents carried claims this landing makes
    false**, outside the plan's sweep, corrected on the rule that drift
    propagates outward (execution ledger R40):
    - `2026-08-03-world-index-packaging-design.md` **limitation 1** — "the
      registry is unanchored until §9 lands … deleting an admission record is
      undetectable today." Closed, with the two bounds that survive the closure
      named: detection is quantified over surviving observers, and the tail
      beyond the maximal anchor stays L5's residue.
    - `2026-08-20-world-registry-design.md` **§8.1** — "full replay/refutation
      and genesis-to-mirror agreement remain the deferred log reader's claim."
      That reader is no longer deferred; cut 6's own durability claim is
      explicitly not restated by the correction.
    - `2026-08-20-world-index-slice-2-design.md`'s **out-of-scope list** — its
      first two entries ("log verification, L1–L13, the explicit anchor act,
      and the replay reader"; "genesis-to-mirror verification, pending the
      configuration-mismatch audit") are no longer deferred anywhere. The
      slice's own boundary is unchanged and stays accurate as a statement about
      *that* slice.

    **The frozen conformance cuts were deliberately left alone.** Cuts 2, 3, 4,
    6 and 7 and the disposition record all carry L-row deferral tables this
    landing makes historically stale. A frozen cut's deferral table states the
    world at its freeze; editing one to track later work is what the freeze
    discipline forbids.

## 9. Execution record — the rulings ledger survived, at a tracked path

This slice was executed with a subagent-driven controller: a fresh implementer
per task, an independent review after each, and a bounded fix loop. Cut 7's
results §10 recorded that slice 2's rulings ledger was destroyed with its
worktree — a git-ignored file inside a disposable checkout — and named the fix:
keep the ledger at a tracked path and commit it at every task boundary.

That was done. **All 44 rulings are in
`docs/plans/2026-08-22-log-verification-ledger.md`**, with the atoms and Science
heads recorded beside them. **R1–R38 were written and committed at their task
boundaries** — the discipline cut 7's results asked for — and **R39–R44 are the
banking task's own**, committed with the close-out. Nothing in this execution
depends on a file that lives only in a worktree.

Rulings with obligations discharged in this document: R1 (§4), R13 (§3), R16
(§7.1), R33 (§8.1), R34 (§7.2), R37 (§1.1), R38 (§1.2), R39 (§7.5), R40
(§8.13), R44 (§4 and §8.11).
