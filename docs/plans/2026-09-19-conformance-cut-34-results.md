# Conformance cut 34 — results

**Cut:** `../designs/2026-09-19-conformance-cut-34.md`
**Freeze:** `5eda3fa45b64bf716f44ae1de7adc5fd65a2b296`; SHA-256 `97ba92153bd2866a09711c25d2fd3e1ee3ad0cc00591c41fa6f61dfb11588c3e`
**Declaration:** `python/tests/n2_arms_cut34.py`; SHA-256 `76e8e3b438a9468682d93900983407df4e6ee66120d99b6669ba7edd296ff1f8`
**Subject:** correction-remainder slice 2 — the snapshot target
**Design:** `../superpowers/specs/2026-09-19-correction-remainder-slice-2-design.md`
**Plan:** `../superpowers/plans/2026-09-19-correction-remainder-slice-2.md`
**Discharged:** 2026-09-19 on `design/correction-remainder`, through `c77b2aa`
**Runner:** `python/tools/cut34_acceptance.py`

## 1. What ran

The certified runner exported cut roots 4–34 to the certified cut-34 root and
the reproduction root to the retained mm30 corpus, then ran the complete
prefix through cut 33 (the cut 17 runner's nineteen phases through cut 33, 69
phases in all) followed by cut 34. It exited **0**. Its final declaration
line, verbatim, was:

```text
declared arms: 17 (= 17 declaration units; 2 guarantee rows)
guarantee rows exercised: 2 (2 newly closed: C8, C9; the mutation lane has no open boundary)
```

Cut 34's own phases passed:

```text
[cut34 phase 2/3] test_snapshot_retraction_acceptance.py
17 passed in 113.28s (0:01:53)
[cut34 phase 3/3] test_n2_cut34.py
10 passed in 35.69s
```

The whole chain ran in roughly 41 minutes. The first launch of the runner
failed at cut 23's live acceptance phase — `test_world_view_acceptance.py`,
five failures over two absence-shape assertions the frozen cut-23 module had
carried since before decision 7 — and is recorded as a plan deviation below
(§3.2); the module was edited to decision 7's successor contract and the
second launch, quoted above, is the one that discharges the cut.

All seventeen baselines reported **resolved**, and every corresponding
mutation reported **sound**. No unit was stale, vacuous, mixed or
uncollected; the sabotage suite passed **10 passed in 37.09s** with
`test_every_arm_fails_under_its_own_sabotage` sound on every finding and
`test_every_live_check_resolves_and_passes_without_sabotage` resolved.

| declaration unit | baseline | mutation | guarantee-row effect |
|---|---|---|---|
| C8-a | resolved | sound | C8 closes |
| C8-b | resolved | sound | C8 closes |
| C8-c | resolved | sound | C8 closes |
| C8-d | resolved | sound | C8 closes (mount negative) |
| C9-a | resolved | sound | C9 closes |
| C9-b | resolved | sound | C9 closes |
| C9-c | resolved | sound | C9 closes |
| C9-d | resolved | sound | C9 closes |
| BI-1 | resolved | sound | boundary invariant |
| BI-2 | resolved | sound | boundary invariant |
| BI-3 | resolved | sound | boundary invariant |
| BI-4 | resolved | sound | boundary invariant |
| BI-5 | resolved | sound | boundary invariant |
| BI-6 | resolved | sound | boundary invariant |
| BI-7 | resolved | sound | boundary invariant |
| BI-8 | resolved | sound | boundary invariant |
| BI-9 | resolved | sound | boundary invariant |

**Staleness evidence.** Refactoring in Task 2 (the write-boundary resolver
port), Task 4 (the recomputation sites) and Task 5 (the evaluator's world
read) moved **six** pinned `before` strings out from under four earlier
live guards (all six land in `test_n2_cut16.py`, `test_n2_cut18.py`,
`test_n2_cut27.py`, or `test_n2_cut33.py`; `test_n2_cut33.py` carries two
of the six, `C7-c` and `BI-3`). Task 2's and Task 4's rewrites moved five,
none with a plan
step naming the re-target: cut 16's `boundary-reresolution-a` and cut 18's
`boundary-reresolution-after-delete-a` (both `corpus.py`'s `retract`, moved
by Task 2's rewrite), cut 33's `C7-c` (the same rewrite), and cut 27's
`W8a-a` and `R23-a` (`world/read.py` and `world/importing.py`, moved by
Task 4); Task 4b re-targeted these five in the live `_LIVE_SABOTAGES`
tables (`test_n2_cut16.py`, `test_n2_cut18.py`, `test_n2_cut27.py` — which,
with `test_n2_cut33.py`, gained the table for the first time — and
`test_n2_cut33.py`), commit `e85f703`. Separately, Task 5's history union
in `gather`'s scope loop (`evaluation.py`'s
`found=tuple(sorted({*(...), *history}))`) moved cut 33's own `BI-3` arm
("the epoch enumeration is scoped to the proposition inputs"); Task 5
re-targeted it in the same commit that moved it, `81104e1`, in
`test_n2_cut33.py`'s `_LIVE_SABOTAGES`, dropping exactly the same
`if ref in taken` filter the frozen sabotage drops and leaving the history
union (and everything else on the line) intact. A separate AST effect
check, `test_pin_recheck_inventory`, also began reading
`snapshot_standing`'s `retracted.add`/`members.add`/`nxt.add` calls as
unlisted effects; Task 4b added the three set-receiver names to
`test_pin_recheck_inventory.py`'s `READ_ONLY` list. Every re-target across
both commits was verified against the frozen declaration's own property
before and after the move: no frozen `n2_arms_cut*.py` file changed, and
each retargeted `after` still fails the same check the frozen arm requires.
The final staleness/freeze set and the retargeted guards passed alongside
the full suite reported in §1's pre-push gate.

The full repository gate ran on the discharge commit with the certified
exports:

```text
5052 passed, 1 skipped in 1182.96s (0:19:42)
      Tests  155 passed (155)
```

`just check` passed standalone (Ruff, Pyright zero errors, `tsc --noEmit`,
Biome); `tasks check` reported zero errors and zero warnings throughout. The
one Python skip is the same intentional causal-only fixture arm cut 33's
record named (`tests/test_composite.py:119`). No capability refusal or
waiver occurred.

## 2. Accounting

The cut carries **17 declaration units**: eight against C8 and C9 (four
each) and nine boundary invariants holding the write, fold, recomputation
and read seams the new arm touches. C8 closes in full and C9 closes in
full. `correction-remainder` — the mutation lane's only open boundary —
closes with them; the correction lifecycle carries no further open row.

The global corpus is **177 of 216 guarantee rows closed, 39 open**. This is
a two-row increase from cut 33's 175: C8 and C9 close. C10 does not add a
closed row and stays partial, owned by `contract-cut`'s
`instrument-certification` eligibility arm.
`python/tools/roadmap_status.py` carries the cut-34 accounting (added as
`34: ("conformance-cut-34-results §2", "C8, C9", "")` in `ACCOUNTING`, the
plan's own place to record a new cut) and produces the roadmap's
Appendix A with C8 and C9 selected and closed and C10 unmoved.

The cut changes no grammar and no kind. `derive.RECEIPT_OUTCOMES` and
`audit.SNAPSHOT_STATES` each gain `"retracted"` last; `ReceiptOutcome`'s
`validated` outcome is unchanged; no derivation rule or implementation
identity moves (verified by running `validate_receipt` over a pre-slice
epoch — Task 1's requirement). `contract-cut` gains no dependency from this
slice: the target union's third arm is projected into the existing
`retraction` kind's identity basis exactly as the `node` and `route` arms
are, with no relation edge emitted for it (decision 9).

## 3. Evidence

No prior frozen declaration or cut body changed. Cut 34's §§2–7 remain
byte-exact to the freeze object; only its status line changes at discharge.
The cut-34 declaration remains byte-exact at its pinned SHA-256. Historical
evidence in prior results records and the reproduction record is unchanged
except by the addendum this cut adds to the reproduction record (§4) and one
sentence correction in that same addendum (§3.2).

### 3.1 Corrections carried by the cut document

The frozen cut required no post-freeze supplement. A review round found two
findings in the draft before the freeze commit (§7 had dropped two of spec
§14's seven limitation clauses; §5 named its phase modules by path rather
than the exact `PHASE_MODULES` tuple); both were fixed in the same freeze
sequence, so the pinned commit (`5eda3fa`) already carries the corrected
text and the cut's selected units, homing, second-reader challenge and
limitations stand as frozen.

### 3.2 Deviations from the plan, all reviewed and taken

- **`open_session` names no function; the session opener is
  `open_attended_session`.** The plan's Task 2 step named a function that
  does not exist in `session/writer.py`; the spec asks for the session to
  carry the resolver port, and `open_attended_session` is the one opener
  that constructs a `writer_factory`. Substituted with no behavior change.
- **`retracted_world`'s fixture profile is the sample corpora's pinned
  profile, not `BASE`.** `BASE` refuses at `_require_pins_agree`; Task 4's
  fixture uses the same `WITH_BIOLOGY`-shaped profile the existing sample
  corpora already carry, changing no assertion's target.
- **Five pre-existing tests in `test_world_standing.py`/`test_world_view.py`
  and two absence assertions in cut 23's live acceptance module were
  re-asserted to decision 7's contract.** Decision 7 makes an absent
  covered corpus answer absence for the *whole* world read, before the
  per-ref walk that used to name each absent target individually; a
  reviewer confirmed the re-assertion against decision 7's text before it
  landed, and no contract fixture changed. `test_world_view_acceptance.py`
  is a durable module carrying the pre-decision-7 contract exactly as its
  portable twin (`test_world_view.py`) had before Task 5; it was edited to
  the successor contract following the precedent spec §11.5 names (cuts
  31–33 edited frozen-adjacent modules the same way, most recently
  `63b3eb5` in slice 1) — the frozen cut-23 *document* is untouched, only
  its live acceptance module.
- **Six pins the plan named no re-target step for were moved by Tasks 2, 4
  and 5's refactors and re-targeted in the live guards** (§1's staleness
  evidence): cut 16's `boundary-reresolution-a`, cut 18's
  `boundary-reresolution-after-delete-a`, cut 33's `C7-c`, and cut 27's
  `W8a-a` and `R23-a`, moved by Tasks 2 and 4 and re-targeted together by
  Task 4b (`e85f703`) — the last two giving `test_n2_cut27.py` a
  `_LIVE_SABOTAGES` table for the first time, alongside `test_n2_cut33.py`.
  Separately, cut 33's `BI-3` (`evaluation.py`'s `scoped.found` line) was
  moved by Task 5's history union in `gather`'s scope loop and re-targeted
  by Task 5 in the same commit, `81104e1`, dropping exactly the frozen
  sabotage's `if ref in taken` filter and nothing else. Frozen
  `n2_arms_cut*.py` declarations stay untouched.
- **`test_pin_recheck_inventory.READ_ONLY` gained `snapshot_standing`'s
  three set-receiver names** (`retracted.add`, `members.add`, `nxt.add`),
  the check's own "keep receiver names explicit" convention, so the AST
  effect check does not flag `snapshot_standing`'s own bookkeeping as an
  unlisted mutation.
- **Three spec §11.1 unit cases the plan dropped were added in Task 5's fix
  round**: absence-wins precedence against a standing retraction, the
  damaged-corpus pair, and a raw-written retraction outside coverage
  leaving the read unchanged. All three are spec-binding, not new scope.
- **Four arm `after`s follow the plan's forms rather than the frozen cut
  document §5's exact wording.** BI-5's `after` is spelled as
  `scope = scope | ({key} if target["arm"] == "snapshot" else set())`
  beside the re-keyed `key` line, since the view holds no world handle and
  cannot reach the retained inventory `gather` would otherwise consult; the
  restricted set the view *can* see still breaks the check the cut names
  (the older snapshot's retraction enters `found`). C9-d's `after` accepts
  the successor a standing snapshot retraction's facet names through
  `view.captured_records` and re-binds to it, because the alternative form
  (testing membership in `history`'s refs) cannot accept an identity.
  BI-9's `after` prefers the captured enumeration over the live fold rather
  than the cut's own "duplicates the pair" wording, because a
  set-assembled `found` cannot carry one ref twice; BI-3's `after` is
  `if False:` (the retracted phase never runs, so availability answers
  `unresolvable`) rather than "called after the availability phase" — the
  literal ordering swap is unspellable against the actual control flow.
  Each `after` was verified at review to still break its unit's declared
  property under the sabotage suite.
- **`tests/test_recent_cut_acceptance.py` gained the cut-34 row** (a plan
  gap, not named by any task step): `(cut34, 34, (17, 17, 2))` appended
  beside the existing cut 23/24/33 rows, with the matching
  `if cut == 34:` closing-line assertion. No older row rotated out,
  following the shape `f4c2cef` used to add cut 33's row.
- **The reproduction re-run reused the existing corpus in place.** Spec §13
  said cut 33's reproduction state moves aside to
  `.work/reproduction/mm30.cut33` before this slice's re-run; no contract
  succeeded (the same `NoBelief` shape as cut 33's own re-run), so nothing
  under `.work/reproduction/mm30` was recreated or moved aside, and the
  addendum records that directly rather than the plan's expectation. Spec
  §17 carries this as a planning correction (§4 below). A second sentence
  in the addendum, giving the working `MM30_PREDECESSOR` value as "one path
  segment further in" than the declared default, undercounted by one: the
  real predecessor carries `proto/projects` ahead of
  `cancer/cancer-types/multiple-myeloma`, two segments, not one; corrected
  in the same file.

### 3.3 Limitations found at review

1. **A retraction's corpus can depart.** Decision 7 fails the read closed
   (`NoBelief`), and audit answers `unresolvable`. A departed corpus that
   held the only retraction of a snapshot therefore neither restores nor
   confirms it; the design's "detected at audit" holds and nothing here
   re-admits the snapshot. Filed as an idea, `beliefs-7d3463` (§5 below), and
   banked as a dated limitation on the correction design (§8 item 7).
2. **`move` of a snapshot retraction away from its counter-retraction** is
   slice 1 §11's split, unchanged; it now covers three arms.
3. **A raw computation that ignores retraction records** can still bind to
   a retracted epoch's bytes (`read.open_epoch` does not refuse). The
   design bounds "unusable" to boundaries and audit; the kernel has no
   process-level enforcement and this slice adds none.
4. **Retracting the current epoch's snapshot with no successor** makes
   every world read bound to `current_epoch` refuse until a new epoch is
   built — intended, per C9's negative; recorded in the guide
   (`docs/guide/identity-world-and-change.md`).
5. **A snapshot retraction makes every receipt covering the writing corpus
   `unresolvable` until a fresh epoch is built** — the successor's
   included; recorded in the guide beside item 4.
6. **Other receipt subjects are not retractable** (decision 2); banked as a
   dated limitation on the correction design (§8 item 8).
7. **`build_epoch` republishes a retracted identity.** A rebuild under the
   retracted snapshot's coverage yields the same identity, is retained, and
   may become `current`; every read bound to it refuses and import of the
   same carrier elsewhere is refused, so the state is coherent but
   asymmetric. Whether build should refuse is filed as an idea,
   `beliefs-05dd2a` (§5 below), not decided here.

Three review findings found no place to become work: `gather`'s per-ref
`_absence_of` branches are unreachable for a world read after decision 7's
early return (still live for a corpus-local read) — filed as an idea,
`beliefs-179099`. The import call site's double call to
`_validated_retraction` (once to validate, once more to read the arm) is
plan-mandated, not a defect — filed as a hygiene idea, `beliefs-b22a0c`. One
`test_world_view_acceptance.py` run failed transiently for 3 seconds during
Task 7 right after its decision-7 edit and was not reproduced in three later
runs (two standalone, one in the full chain) — filed as a testing idea with
what was observed, `beliefs-15946f`, so a recurrence is not read as new.

## 4. Reproduction measurement

The reproduction record's §13 addendum
(`../designs/2026-09-05-mm30-reproduction.md`) re-ran
`reproduction.rederive` on 2026-09-19 in a fresh process against the
existing cut-32/33 corpus. No contract succeeded, so the corpus was neither
recreated nor moved aside — read in place, exactly as at §12.

The slice adds one retraction target arm, `snapshot`, and its live standing,
none of it reached by the mm30 driver: `context()` still supplies
`producer_snapshot_identity` as the literal `"no-epoch-published"`
(`python/tools/reproduction/belief.py`, unchanged), no epoch is ever built
by this driver, and the scope loop's snapshot key is never populated. The
one new arm is exercised only by
`test_snapshot_retraction_acceptance.py`, `n2_arms_cut34.py`,
`test_n2_cut34.py` and `cut34_acceptance.py`, not by this corpus.

The fresh answer was `NoBelief(reason="no-directional-outcome")`, equal to
the recorded answer (`rederived_equal: true`). The corpus holds no
retraction of any arm, so the derived enumeration is still `found=()`,
coverage unchanged (`8b5d0c802677ee445e2b9d91ebf5d6a7`). `state.json` was
rewritten with byte-identical content; only `findings.jsonl` gained the
run's own log lines. No pinned digest moved: decision 11 holds, and this
re-run is the transition it predicted — a slice that adds a new retraction
arm and its standing fold without touching any derivation rule or
implementation identity the mm30 corpus's answer depends on.

## 5. Remaining boundary

`correction-remainder` closes in full at this cut: C8 and C9 close, joining
C7 and C3 (cut 33), and the correction lifecycle's mutation lane has no
further open boundary.

**C10** remains partial on the `instrument-certification` eligibility arm,
owned by `contract-cut`. Its raw-written audit arm was completed at cut 33.

Five ideas are filed rather than left as hidden limitations, none of which
reopens C8, C9 or any other guarantee row: `beliefs-7d3463`, whether a
departed corpus's snapshot retraction should be a registry-visible event
(§3.3 item 1); `beliefs-05dd2a`, whether `build_epoch` should refuse to
publish a retracted producer identity (§3.3 item 7); `beliefs-179099`,
`gather`'s dead per-ref absence branches after decision 7; `beliefs-b22a0c`,
the import boundary's double `_validated_retraction` call; and
`beliefs-15946f`, the one transient `test_world_view_acceptance.py`
failure. `beliefs-2d5ada` ("should the audit report a certification that
retirement would change?") was read at this cut and found unchanged by the
slice — retirement remains a belief-input fact only — and stays open,
unrelated to any row this cut closes.

## 6. Main integration

The controller completed the final whole-branch review, took the final fix
wave at `d6cb814` (the reproduction addendum's C9 sentence) and `a25305c`
(ten seam tests pinning `RetainedSnapshots`'s skip and two-coverage refusal,
`audit_world`'s outside-coverage and successor faults, the session's port
pass-through, C8-b's discriminating "not a finding" form and the second
raw-write counter-retraction variant; no source change), and completed a
scoped re-review with every finding addressed. The reviewed branch was merged
locally into `main` with `--no-ff` on 2026-09-19 at
`bef38b971eb79e277a610510acf496945f39948c`. Nothing was pushed.

`just gate` on the merged commit exited **0**. Ruff, Pyright, TypeScript
typecheck and Biome passed; task validation reported zero errors and zero
warnings. The serial Python suite reported:

```text
5062 passed, 1 skipped in 1241.01s (0:20:41)
```

The skip is the intentional `tests/test_composite.py` causal-only fixture arm
documented at cut 33. TypeScript passed all seven files and 155 tests:

```text
 Test Files  7 passed (7)
      Tests  155 passed (155)
```

The merged-main gate transcript had SHA-256 `fb76ac6668a3d76510108d306ecf067fde5208405a46873c94e7cf95f4481cf5`; the durable summaries
are recorded above because the plan's scratch workspace is removed at
completion. No capability refusal or waiver occurred. This integration record
changes only documentation after the successful gate.

## 7. Execution rulings

Every `Ruling:` entry from the execution ledger, in chronological order:

- **De-indent the `faults` block in Task 4's audit.py addition, as the plan
  itself flags.** A transcription note in the plan, not a design choice.
  Cost if wrong: none.
- **Use whatever `WorldReadView` defines for `stamp`** (the plan cites it as
  a property at one line; the spec calls it `view.stamp()`). Cost if wrong:
  an `AttributeError` the tests catch.
- **Import both `RETRACTION_UPHELD` and `RETRACTION_OVERTURNED`** where a
  Task 5 test used the former but the plan's import line named only the
  latter. Cost if wrong: none.
- **Accept `open_session` → `open_attended_session`.** The plan named a
  function that does not exist; the spec asks for the session to carry the
  resolver port, and `open_attended_session` is the one opener that
  constructs it. Cost if wrong: none.
- **Fix Task 0's dropped spec §14 clauses and imprecise `PHASE_MODULES`
  wording before freeze, and let the fix commit supersede the draft as the
  freeze pin.** Nothing had pinned the draft commit yet; a cut freezes
  after review clears, so `5eda3fa` — not `f1334c6` — is the pin every
  later task reads. Cost if wrong: none, the guard pins whichever commit
  Task 7 actually reads.
- **Re-target the five pins Tasks 2 and 4 moved, and whitelist
  `snapshot_standing`'s three set receivers, as a separate commit rather
  than folding it into Task 4 or 5.** No task step named this re-target; it
  surfaced as `test_arm_staleness` and `test_pin_recheck_inventory`
  failures after Task 4 landed. Live `_LIVE_SABOTAGES` tables move; frozen
  `n2_arms_cut*.py` files do not. Cost if wrong: a re-target that asserts a
  weaker check than the frozen arm — closed by verifying each `after` still
  fails the same check post-move.
- **Re-target cut 33's sixth moved pin, `BI-3`, in the same commit as the
  Task 5 change that moves it (`81104e1`), rather than deferring it to
  Task 4b's separate re-target pass.** Task 5's history union in `gather`'s
  scope loop moves the same `scoped.found` line the frozen `BI-3` sabotage
  pins; the drop-`if-ref-in-taken`-only shape of the frozen sabotage is
  preserved exactly, only its position in the line moves. Cost if wrong: a
  re-target that asserts a weaker check than the frozen arm — closed the
  same way as the five-pin re-target, by verifying the `after` still fails
  the check the frozen arm requires. Found at Task 8's review and recorded
  here rather than reopening Task 5's commit.
- **Accept the five re-assertions in `test_world_standing.py` /
  `test_world_view.py` as decision 7's mandated consequence.** A reviewer
  confirmed the re-assertion against decision 7's own text; no contract
  fixture changed. Cost if wrong: world reads over a partially absent world
  would answer absence where they used to proceed per-ref, which the spec
  states explicitly.
- **Add the three spec §11.1 cases the plan dropped in Task 5's fix
  round**, rather than treat their absence as an accepted gap: absence-wins
  precedence, the damaged-corpus pair, and a raw-written retraction outside
  coverage. Spec-binding. Cost if wrong: none against decided scope.
- **Accept `test_world_view_acceptance.py`'s edit to decision 7's successor
  contract, following the precedent named in spec §11.5 and landed at
  `63b3eb5` in slice 1.** A live acceptance check follows the current
  contract; the frozen cut-23 document is untouched. Cost if wrong: cut
  23's acceptance would no longer pin the per-ref absence granularity that
  decision 7 deliberately removes.
- **Add the cut-34 row to `test_recent_cut_acceptance.py`** in a fix round
  after Task 7's review, following the shape `f4c2cef` used for cut 33's
  row — no older row rotates out. Cost if wrong: none, an additive test
  fixture.
- **Record that the reproduction re-run reused the existing corpus in
  place, and correct the addendum's path-segment count, in Task 8** rather
  than editing the plan or the addendum during Task 6. Spec §13 predicted a
  move-aside that a `NoBelief` answer never triggers, the same shape cut
  33's own re-run hit; the correction belongs in spec §17 and the
  addendum's own sentence, not in a new re-run. Cost if wrong: reproduction
  evidence would need re-reading against the corrected sentence.
