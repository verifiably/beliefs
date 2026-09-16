# Conformance cut 32 — results

**Cut:** `../designs/2026-09-16-conformance-cut-32.md`
**Freeze:** `ff03b00f7f6297f3277da4ab40e1dbfc0b9a39e0`; SHA-256 `598222cbac1ac04e43e503b05287524dc6a3049b760063721482dc844ca43ac2`
**Declaration:** `python/tests/n2_arms_cut32.py`, committed at `44343da`; SHA-256 `a02c1618915f4bc7a9f5dd11deb176346d392e4f35888b05612536d014add796`
**Subject:** the `composite` world kind — a declared node set, members read as signed directed edges, and a belief-inert derived reading
**Design:** `../designs/2026-09-12-composite-claims-design.md`
**Discharged:** 2026-09-16, on `design/composite-claim`, at `44343da` with the fix round `caa4adb`
**Runner:** `python/tools/cut32_acceptance.py`

## 1. What ran

```sh
MAIN_CHECKOUT="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
for v in 4 7 10 29 30 31 32; do export SCIENCE_CUT${v}_ROOT="$MAIN_CHECKOUT/.work/acceptance/cut32/composite-claims"; done
export SCIENCE_MM30_ROOT="$MAIN_CHECKOUT/.work/reproduction/mm30"
export MM30_PREDECESSOR="$MAIN_CHECKOUT/.work/reproduction/mm30.cut22"
(cd python && uv run --frozen python tools/cut32_acceptance.py)
just hook-pre-push
```

The certified aggregate exited **0**. Its declaration line, verbatim:

```
declared arms: 26 (= 10 declaration units; 10 guarantee rows)
```

`just hook-pre-push` — the full gate (`ops-check`, ruff, pyright, tsc, biome,
`tasks check`, then `just test`) — exited **0**. Its two summary lines,
verbatim:

```
4934 passed, 2 skipped in 1128.01s (0:18:48)
```

```
      Tests  154 passed (154)
```

Both were taken on the fixed tree at `caa4adb`. The discharge at `44343da`
reported the same declaration line and `4931 passed, 2 skipped in 1195.17s
(0:19:55)` / `Tests 153 passed (153)`; the three added Python tests are the
parametrized `composes`-signature rows in `test_base_contract.py` and the one
added TypeScript test is its mirror (§3.2). The two skips are both in
`test_composite.py` and both conditional on the testing fixture's `affects`
admitting the `causal` layer only: the non-causal-layer row and the cycle row,
each named in its own skip message as exercised in `test_composite_boundary.py`
under the biology fixture, and each held again by the acceptance module's U3.
No capability refusal, no waiver. The run transcripts are scratch — this cut
retains no log artifact — and both summary lines are recorded verbatim in the
bodies of `44343da` and `caa4adb`.

The prefix chain is cut 32 → cut 31 → cut 30 → cut 29 → cut 28 → cut 27 →
cut 26 → cut 25 → cut 24 → cut 23 → cut 22 → cut 21 → cut 20 → cut 19 →
cut 18 → cut 17 (`PREFIX_RUNNERS = ("cut31_acceptance.py",)`). Cut 32's own
phases are `test_composite_acceptance.py` (10 passed in 23.46s; one test per
table-U row) and `test_n2_cut32.py` (10 passed in 18.38s; the twenty-six arms
audited both ways). The runner's default work root is the main checkout's
`.work/acceptance/cut32`, never a new dotted root at the project root.

**The arms and their verdicts.** 26 arms, homed exactly as the cut document's
§5 homes them (U1 1, U2 2, U3 4, U4 4, U5 1, U6 2, U7 2, U8 7, U9 3). **U10
homes none**: §5 lists none, and the guard names the absence by name
(`UNAUDITED_UNIT = "U10"`), asserts the arms cover exactly the other nine, and
asserts that the one unit check no arm names is U10's, rather than passing
silently on it. The two audit tests are the verdict:
`test_every_live_check_resolves_and_passes_without_sabotage` reports
**resolved** — every one of the ten distinct checks the arms name passes
against the real package — and `test_every_arm_fails_under_its_own_sabotage`
reports no unsound finding, i.e. every arm's named check *failed* under its own
sabotage, with `pytest` exiting 1 rather than 4.

| arm | module | baseline | audit |
|---|---|---|---|
| U1-a | `contract/base.py` | sound | caught |
| U2-a | `contract/domain.py` | sound | caught |
| U2-b | `contract/domain.py` | sound | caught |
| U3-a | `composite.py` | sound | caught |
| U3-b | `composite.py` | sound | caught |
| U3-c | `composite.py` | sound | caught |
| U3-d | `composite.py` | sound | caught |
| U4-a | `evaluation.py` | sound | caught |
| U4-b | `contracts/science/CONTRACT.yaml` (packaged) | sound | caught |
| U4-c | `corpus.py` | sound | caught |
| U4-d | `corpus.py` | sound | caught |
| U5-a | `composite.py` | sound | caught |
| U6-a | `corpus.py` | sound | caught |
| U6-b | `corpus.py` | sound | caught |
| U7-a | `audit.py` | sound | caught |
| U7-b | `audit.py` | sound | caught |
| U8-a | `composite.py` | sound | caught |
| U8-b | `composite.py` | sound | caught |
| U8-c | `composite.py` | sound | caught |
| U8-d | `composite.py` | sound | caught |
| U8-e | `composite.py` | sound | caught |
| U8-f | `belief.py` | sound | caught |
| U8-g | `composite.py` | sound | caught |
| U9-a | `corpus.py` | sound | caught |
| U9-b | `contract/base.py` | sound | caught |
| U9-c | `audit.py` | sound | caught |

**Two arms were measured `vacuous` before either was declared sound, and both
were moved** (§3.1): **U4-a** written in `closure.py`, where the plan homes it —
`build_closure` holds no read view, so every mutation available inside it moves
the digest identically before and after a composite is minted — re-homed to
`evaluation.gather`, the one function that resolves a proposition's belief
inputs from a corpus; and **U1-a** written as `root.get("composite_grammar",
{...})`, which `_exact_fields` makes unreachable — re-sited to a `setdefault`
ahead of that call, inside the same module and on the same mechanism. A vacuous
arm is a measurement and not a verdict; both are recorded in the cut document's
§8 rather than quietly re-sited, and the arm count is unchanged at 26.

## 2. Accounting

Ten guarantee rows are read, **10 full/closed**: U1–U10, every clause of every
row, with nothing deferred. The frozen inventory is **10 declaration units**
expanding to **26 one-mutation sabotage arms**, homed per unit exactly as the
cut's §5 homes them. Task 8's review and its re-review read every row's clauses
one by one; the four clauses the first discharge did not hold were built and
re-run in the fix round, not reported partial (§3.2).

The global corpus is **173 of 216 rows closed, 43 open**, in twenty tables
(`python/tools/roadmap_status.py`, which gains this cut's entry in this
commit). No P row's verdict changes: minting, superseding and deleting a
composite leaves every proposition's belief input digest byte-identical, and
`evaluate` equals the first projection of `evaluate_traced` over every scenario
in `test_belief.py`. `assesses` keeps its one target kind. `WORLD_KINDS` gains
exactly one kind — **fourteen** in both implementations. M1–M13 are untouched,
M6 governs the new `edges:` declaration class unamended, and claim identities do
not move (M8): the reproduction's target claim `780ace5964c8ab83…` is the
identity cut 31 recorded.

`composite-claims` enters the ledger's `Current state` and the roadmap's
boundary index at this discharge and closes in this same commit, so neither
table carries an open row for it; the roadmap's lane table carries the closed
`composite-claims` lane. Kernel §4.4's *open, unplaced deliberately* row loses
three of its four entries — `inquiry`, `patch-definition` and `structural-chain`
are placed, `search` stays — and kernel §11's first bullet closes by citation.
`contract-cut` (`beliefs-eacbe2`) gained this lane as a dependency at the
lane's opening and does not gain it again here.

## 3. Evidence

No allowlist, no frozen declaration, no frozen cut body — cut 32's own §§2–7,
the slice the guard pins, included — and no cited-not-run guard was changed. No `n2_arms_cut*.py` body through cut 31
was edited, and no prior cut document was edited.

### 3.1 Corrections carried by the cut document

Five corrections are recorded as dated supplements in
`../designs/2026-09-16-conformance-cut-32.md` §8, outside the frozen body and
outside the guard's `_frozen_body` slice, so the freeze pin is unchanged and is
not re-taken. None adds, removes or moves a declaration unit, a row or an arm:
§4's **10 declaration units** and **26 one-mutation sabotage arms** and §5's
homing stand exactly as frozen. Each was measured before it was written.

- **§8.1 — U4-a's mutation lands in `evaluation.py`, not `closure.py`.**
  Measured: `build_closure` is a pure function of the arguments it is handed and
  holds no read view, so it cannot see a composite at all, and every mutation
  available inside it moves the digest identically before and after a composite
  is minted — which is exactly the comparison U4 makes. An arm written there
  scores `vacuous`. The one function that resolves a proposition's belief inputs
  *from a corpus* is `evaluation.gather`, and the arm is homed on its
  `absent.extend(context.snapshot.not_present.items())` line. The property
  falsified and the check that fails (`test_u4_belief_inert`) are unchanged.
- **§8.2 — U1-a's site inside `contract/base.py`.** Measured: written as the
  plan spells it (`root.get("composite_grammar", {...})`) the arm scores
  `vacuous`, because `parse_base_contract` calls
  `_exact_fields(root, _CONTRACT_FIELDS, source)` before it reads any grammar
  and `_CONTRACT_FIELDS` carries `composite_grammar`, so the `root[...]` read is
  never reached. The arm is re-sited to a `setdefault` ahead of that call —
  the same module and the same mechanism, at the site where optionality is
  actually decided.
- **§8.3 — U8-a's sabotage drops the unresolvable member rather than reading
  it.** A row cannot be minted for a member that does not resolve without
  forging its `claim` and its `role`, which would sabotage the row's
  construction rather than the refusal. The arm is written as the other half of
  the same disjunction: `read_composite` filters the unresolvable refs out
  before `restore_members` and does not refuse. The asserted property and the
  check are unchanged, and the arm scores `sound`.
- **§8.4 — where U3's "at construction and at `add` alike" rows land at the
  boundary.** Measured per row: a duplicate node, a duplicate member and an
  empty node set are defects *of the facet*, so §4.2's step 1 — the facet decode
  in `CompositeFacet.__post_init__` — refuses each with `MalformedRecord` and
  its own message, and no `composite-*` code is reached. The other five rows
  carry the same code at `add` as at construction. §8.4's table states both
  columns, and `test_u3_form_classification_and_vocabulary_arms` asserts both.
- **§8.5 — U4-b mutates the packaged contract copy only.** An N2 arm is one
  byte-exact mutation of one module inside one package tree, and `test_n2.py`'s
  harness copies and mutates `python/src/beliefs` alone, so the repo-root
  `contracts/science/CONTRACT.yaml` is unreachable from an arm. `test_u1` and
  `test_u4` therefore read the **packaged** contract through
  `importlib.resources` — the copy the sabotage moves — and the two copies are
  held byte-equal by the existing parity machinery. One arm, homed on U4, as §5
  counts it.

### 3.2 Deviations from the plan, all reviewed and taken

Every deviation below was ruled while the plan ran; §7 reproduces the rulings
themselves, with what each costs if wrong.

- **A `composes` signature rule was built, not reported partial.** U1's clause
  *"a `composes` signature outside `composite → proposition` refuses at parse"*
  had no rule behind it at the discharge: `composite → dataset` and
  `proposition → proposition` both parsed, and the acceptance check was reading
  a kind-existence refusal, which is a different rule. `contract/base.py` gained
  `COMPOSES_SIGNATURE` and a refusal in the same shape as the `same_kind` one
  beside it, and `ts/src/contract.ts` mirrors it with the same message. No arm
  was added, moved or renamed, and the declaration's pinned SHA-256 is
  unchanged.
- **`belief.admitted`'s signature is the plan's, not the design's prose.** It is
  `(distinct, *, runs, observations, verifications)`; the design's §6.2 named
  two arguments step 5 never reads. Recorded as a dated note on that section,
  together with the reader name: the identification term is read through
  `stored.assessment_value(...).estimand.control.identification`, not
  `analysis_spec_value`.
- **`CompositeReading` has no public constructor.** The plan's Global
  Constraints outrank its own verbatim construction code: the reading's identity
  is a content hash it computes, so a hand-built instance could pair any
  identity with any rows. It carries the `_MINT`/`_checked` gate `Composite`
  has.
- **`composite` is a coreference endpoint kind.** The constant's rule — every
  world kind less the attestation itself and the two boundary-minted occurrence
  records — admits it, so the endpoint set and its test formula include it.
- **`require_identifier` is public by name and not in `claim.py`'s `__all__`.**
  M13 pins that `__all__` to a single lowercase name, and a frozen guarantee
  outranks the plan's wording; the finding's substance — no cross-module private
  import — is met.
- **The reproduction's spine proposition is minted NEGATIVE.** Higher PHF19
  expression, shorter overall survival, as the inquiry states it and as the
  fragment's title and the plan's code say. The design's §9 calls it "positive"
  in one clause; that is a drafting slip against its own two neighbours, and the
  correction is a dated note on §9 rather than an adjustment of what was
  measured.
- **`check_composite` is wired into both audit dispatches** — `audit_corpus`'s
  loop and `audit_world`'s `_recompute` — with code registration, as the
  pre-freeze review required, rather than into `audit_corpus` alone.
- **One live guard was re-targeted.** Cut 20's `D8a` in
  `test_n2_cut20.py`: only its `after` moved, by one list member, because Task 2
  added `edges` to `_CONTRACT_OPTIONAL` and the stale `after` made the arm score
  `uncollected`. The frozen declaration is untouched, and a dated comment
  beside the existing 2026-09-14 and 2026-09-15 migrations says so.
- **Four more live arms were re-targeted by the implementing tasks**, under the
  same, already-established mechanism and with a dated comment on each: the
  portable harness's own **M7** (`python/tests/n2_arms.py`, twice — Task 1, when
  `compile_profile`'s `_projection(...)` call gained `base.composite_grammar`,
  and Task 2, when the same call gained `edges=edges`); cut 2's **P9**
  (`test_n2.py`'s `_LIVE_SABOTAGES`, Task 6, when `evaluate` became the first
  projection of `evaluate_traced`); cut 23's **R19e** (`test_n2_cut23.py`,
  Task 6, the same factoring on `evaluate_over`); and cut 24's **W15n**
  (`test_n2_cut24.py`, Task 1). `n2_arms.py` is the **live** harness's arm
  table, not a frozen declaration, so M7 is edited in place there by the same
  rule that governs a live guard; no `n2_arms_cut*.py` body was touched.
- **Two acceptance modules outside this lane were repaired**, both red on this
  branch before Task 8 and visible only to the chain, since the portable suite
  cannot see `tests/acceptance`:
  `test_relocation_acceptance.py`'s destination now holds the assessment's
  `assesses` target (Task 4's refusal applies on every write path, relocation
  included — U4's own clause), and `test_facet_acceptance.py`'s F8 builder
  enumeration gains `composite_node`.
- **U3-a's fixture is a layers-widened `affects` contract.** The plan named
  `correlates-with` for the non-causal-layer row, which cannot reach `classify`'s
  layer refusal: it declares no `edges:` row, so it refuses as
  `composite-member-undeclared` first. `correlates-with` is used for the
  undeclared-operator row instead.
- **The shipped `biology` pack gains no `edges:` row.** A shipped pack has no
  succession route (`shipped_domain_contract` parses it with no predecessor and
  `check_succession` refuses a successor lineage without one), found at the
  pre-freeze review and banked as the design's limitation 18. The mm30 successor
  contract carries the seven-row table and both of the fragment's operators are
  mm30's.

### 3.3 Limitations found at review

Filed as ideas, each sourced to this record:

- **`beliefs-89542c`** — `arm_staleness` measures only an arm's `before` block.
  A stale `after` therefore surfaces as an *uncollected* arm in a later chain
  run — `pytest` exiting 4, which is not a failing check — rather than as
  staleness. That is exactly how cut 20's `D8a` was found here (§3.2), and the
  shared probe could not see it.
- **`beliefs-51ffdf`** — `python/tools/reproduction/paths.py` and
  `python/tools/cut32_acceptance.py` resolve the main checkout from the
  repository root's *real* path. Where the worktree directory is a symlink onto
  a separate volume, the derived default roots land beside that volume rather
  than beside the main checkout, so every run of this lane needed the
  `SCIENCE_*_ROOT` variables exported by hand and the reproduction's `preflight`
  refused once before they were.
- **`beliefs-0c1cc9`** — the reproduction record's §11.5 measurement
  (`state.cut31_corpus_state`) was taken by a one-shot script that is not in the
  tree, and no committed check reads the key. Decision 11's transition arm is
  recorded and not re-runnable.
- **`beliefs-6776d3`** — `check_composite` is reached by `audit_world`'s
  `_recompute`, but no U7 arm exercises that dispatch; every arm goes through
  `audit_corpus` or calls the check directly.
- **`beliefs-7ab5c4`** — `test_n2.py`'s `_LIVE_SABOTAGES` table keys by
  `arm.row`, which is unique within a cut's declaration and not across the
  unioned tuples. A count assert would catch a silent multi-arm overwrite.

Also carried forward, not new here: **`beliefs-1b0827`** — the shared staleness
probe checks that a pinned before-string still occurs, not that the sabotaged
file still parses; cut 32's own guard adds that check per-cut, as cut 31's did,
but the shared harness does not.

Six minor findings were deferred with reasons in the execution ledger rather
than filed: `restore_members` duplicating `build_composite`'s member loop, the
shape check running twice, the reading walking the corpus three times per
member, `MemberRow.projection` unasserted, the four enumerated `NotReached`
arms without a direct assertion, and the "first projection" tests being
tautological as implemented (P1–P9's banked expectations carry the factoring
proof). None changes a row's verdict.

## 4. Reproduction measurement

The mm30 reproduction re-ran under the successor contracts, recorded as a dated
addendum at `../designs/2026-09-05-mm30-reproduction.md` §11. It **recreates**
the corpus rather than migrating it (design decision 11), with the cut-31
corpus state moved aside — never deleted — to `.work/reproduction/mm30.cut31`;
`.work/reproduction/mm30.cut22` is untouched, since `rederive` still reads it.
The driver ran `preflight` through `close` and then the two new steps,
`compose` (11) and `read` (12). Both of its root variables were supplied rather
than defaulted, for the reason §3.3's second entry gives.

- **The successor contracts** (§11.1): the `mm30` document declares a lineage
  successor to the cut-31 document, committed beside it as a byte copy, and
  `vocabulary.contract()` walks the whole chain document by document. What the
  successor adds is one `edges:` table of seven rows over the operators whose
  direction is not in doubt; `associates-with-*` and `binds-*` get none
  (symmetric), and `is-proxy-for-*` gets none (§11.6). The consulted set is
  unchanged in membership, `{science, mm30, biology}`.
- **The spine, minted NEGATIVE** (§11.3):
  `proposition:protein-phf19-affects-concept-overall-survival`, claim
  `376450b154a29a9b…`, operator `mm30/affects-molecular-entity-concept`, layer
  `causal`, **polarity negative** — higher PHF19 expression, shorter overall
  survival, as the inquiry states it. This is the polarity as *measured*; the
  design's §9 clause is a drafting slip and is corrected there by a dated note.
- **The composite** (§11.3): `composite:h1-prognosis-fragment`, identity
  `ef546cde73edf91b…`, shape `dag`, three nodes, two signed edges —
  `disease-stage → PHF19` positive and `PHF19 → overall-survival` negative.
- **The node receipt**, measured: `node:0` (`protein:PHF19`,
  `biology/molecular-entity`) `not-consulted`; `node:1`
  (`concept:disease-stage`) and `node:2` (`concept:overall-survival`) both
  `member`, resolved on the first call against the held 285-term concept list.
  `not-consulted` is the honest answer, not a gap: the reproduction's snapshot
  reads no HGNC release, and a check not performed is not a finding.
- **The two rows** (§11.4), read under the four arguments the `belief` step
  handed the evaluator plus the compiled profile:

  | member | edge | belief | identification |
  |---|---|---|---|
  | `780ace59…` | `disease-stage → PHF19`, positive | `NoBelief("no-directional-outcome")` | `{identification:observational}` |
  | `376450b1…` | `PHF19 → overall-survival`, negative | `NoBelief("no-eligible-assessment")` | `()` |

  The target's row carries the answer the `belief` step computed over this same
  corpus, reached through the traced evaluator rather than re-derived, with its
  identification column read from the same traced admission. The spine's row is
  `no-eligible-assessment` because nothing assesses it: it was minted with no
  evidence and none is claimed.
- **The readings are equal** (§11.4): the reading was taken twice from persisted
  records in fresh processes and the two canonical encodings are **byte-equal**
  (`state.reading_equal` true).
- **The moved-aside corpus** (§11.5): `.work/reproduction/mm30.cut31`, opened
  read-only under the successor profile, audits to exactly **`profile-mismatch:
  base`** and reads no record — its pinned base contract predates
  `composite_grammar`, and the profile-disagreement rule returns before
  `iter_stored` is reached. Decision 11's transition arm, measured rather than
  assumed; the same shape §10.8 measured for the cut-22 state.

This cut adds **no new mm30 measurement of the on-path question**: the
reproduction reached the same evaluator answer it reached before, over the same
data, and a composite's reading is never a belief. Tier 1's on-path state is not
re-ranked.

## 5. Remaining boundary

`composite-claims` retains nothing: U1–U10 close in full, the design's eighteen
limitations are banked as limitations rather than work, and the boundary leaves
the ledger in the commit that entered it.

What the lane's surfaces leave standing elsewhere:

- **The coordination-contract amendment is sub-project 5's road, not this
  lane's.** The coordination contract's version 1 carries two literal lists —
  the world-kind names a `kinds` predicate may use and the relation names a
  `closure` predicate may traverse — and neither `composite` nor `composes` is
  in them. Until the versioned amendment lands, `closure` from a composite
  anchor and a `kinds: [composite]` view predicate are both unspellable, and a
  view names a composite's members by `addresses` instead (design limitation
  12). The lane files the row and does not wait on it.
- **`correction-remainder` retains C7, C8, C9**, and the composite reading's
  identification column waits on them: the column follows admission as it is,
  and `verification.py` defers the correction-lifecycle clause that excludes the
  target of a standing retraction with the C group (design limitation 16). Until
  that remainder lands, an assessment a standing retraction names contributes a
  term exactly as it contributes to belief; the column and the belief share one
  admission function, so they move together and never disagree.
- **`contract-cut` retains N1–N10** and carries this lane as a dependency, added
  at the lane's opening: the base contract gains a grammar, a kind and a
  relation signature here, and N1 mints a successor contract identity for every
  oracle amended after the freeze.
- **`publish` retains the closure sentence, not a check.** "A composite's
  closure is its members" lands in the user and autonomy layer spec's §6.1,
  where the publish act is specified; the act itself is unbuilt.

## 6. Main integration

To be filled at merge. `design/composite-claim` has not been merged into `main`
at the time this record lands; when it is, this section records the merge
revision, the whole-branch review, the gate re-run on the merged tree with §1's
exports, and any difference between the discharge's counts and the merged
tree's.

## 7. Execution rulings

Every ruling made while the plan ran, in the execution ledger's order. The
ledger itself is not tracked; this is its durable copy.

- **Pre-flight: no ruling needed.** The cross-task scan — produced against
  consumed, for every pair the plan couples — found every interface consistent
  after the drift review, so nothing had to be decided before Task 1 was
  dispatched. Cost if wrong: an interface mismatch discovered mid-lane, which
  is what the scan exists to pay for up front.
- **Task 1 — `composite` is a coreference endpoint kind.** The constant's rule
  (world-index slice 2 design §2 item 4) admits every world kind that is not one
  of its two named exceptions — the attestation itself and the two
  boundary-minted occurrence records — and a composite is neither, so the plan's
  expectation stands and the test formula reverts to it. Cost if wrong: an
  attestation may name a composite endpoint, which is belief-inert either way;
  reversal is one constant plus a design note.
- **Task 1 — the edit to `test_n2_cut24.py` is a sanctioned live-guard
  re-target, and a Critical review finding against it is overruled.** The change
  is a `_LIVE_SABOTAGES` entry for `W15n` — the pattern seventeen guards already
  carry — and `n2_arms_cut24.py` is untouched; the re-review prompt had listed
  `test_n2_cut*.py` as frozen in error. Cost if wrong: a guard arm that no
  longer sabotages the live line, which `test_arm_staleness` would report stale.
- **Task 3 — `require_identifier` is public by name and not added to
  `claim.py`'s `__all__`.** `test_no_alternate_constructor_is_exported` (M13,
  one construction authority) pins that `__all__` to a single lowercase name,
  and a frozen guarantee outranks the plan's "add to `__all__`" wording; the
  finding's substance, that no module imports another's private helper, is met.
  Cost if wrong: a helper importable by name but unlisted — a documentation
  smell only.
- **Task 6 — `belief.admitted`'s signature is the plan's verbatim code,
  `(distinct, *, runs, observations, verifications)`.** The plan is the reviewed
  argument, and the design's §6.2 prose named two arguments step 5 never reads
  (the pre-freeze review's own finding 10). Task 9 records the correction as a
  dated note on §6.2 together with the reader name. Cost if wrong: one signature
  line and one arm string.
- **Task 6 — the plan's Global Constraint outranks its own verbatim
  construction: `CompositeReading` gets the `_MINT`/`_checked` gate `Composite`
  has.** The reading's identity is a content hash it computes, so a public
  constructor would let a hand-built instance pair any identity with any rows.
  Cost if wrong: twelve lines of ceremony on a derived value.
- **Task 7 — the spine proposition
  `affects-molecular-entity-concept(PHF19, overall-survival)` is minted
  NEGATIVE.** The plan's code, the fragment's title and the inquiry's own
  reading all say negative — higher PHF19 predicts lower survival — and the
  design's §9 "positive" is a drafting slip against its two neighbours. Task 9
  records the correction as a dated note on §9. Cost if wrong: one polarity tag
  in a row that is reported as measured, not asserted.
- **Task 8 — U1's `composes`-signature clause is held by building the rule, not
  by reporting the row partial.** `parse_base_contract` and `parseBaseContract`
  refuse a `composes` relation whose sources are not exactly `[composite]` or
  whose targets are not exactly `[proposition]` — a closed signature, the same
  shape as the `same_kind` refusal beside it — and the arm count stays 26, with
  no arm added or moved. Cost if wrong: a parse rule the contract cut would have
  to carry forward; reversible by a successor contract.
- **Task 8 — U3's three form rows refuse at `add` under §4.2 step 1's facet
  decode, not under a `composite-*` code.** A facet whose nodes repeat, whose
  members repeat, or whose node set is empty is not a composite facet at all, so
  the row's "named code" at `add` is the decode's; the constructor keeps its own
  codes, and the undeclared operator asserts `composite-member-undeclared` at
  `add`. Cost if wrong: one §8 line.
