# Conformance cut 36 — results

**Cut:** `../designs/2026-09-21-conformance-cut-36.md`
**Freeze:** `635345697562f71f23763b72bbd129fc8c19007b`; SHA-256 `c4dea1fc153ecb2a0c5f90fc647ed9f67d3f891498c7e87f1d445366a4f4d6bb`
**Declaration:** `python/tests/n2_arms_cut36.py`; SHA-256 `1b66b97223ca6f4a2fc5117cebe21234e979f9e3ef14575838e5195e73e793b9`
**Subject:** Event-level L8 — the presence/exclusion relation across captured corpus heads; L4 and L10 as relabels; L1 re-homed
**Design:** `../superpowers/specs/2026-09-21-event-level-l8-design.md`
**Plan:** `../superpowers/plans/2026-09-21-event-level-l8.md`
**Discharged:** 2026-09-21 on `event-level-l8`, through `810ab3d`
**Runner:** `python/tools/cut36_acceptance.py`

## 1. What ran

The certified runner ran from the lane's worktree with every cut root
(`SCIENCE_CUT4_ROOT` … `SCIENCE_CUT36_ROOT`) exported to the certified
cut-36 root (`.work/acceptance/cut36`, beside the main checkout on the
repository's own volume — the worktree's own volume is uncertified) and the
reproduction root to the retained mm30 corpus. It ran the complete prefix
through cut 35 (the cut 35 runner and its own prefix chain back through cut
17's nineteen phases) followed by cut 36. Cut 36 chains **cut 35's** runner
(`PREFIX_RUNNERS = ("cut35_acceptance.py",)`): cut 8's guard is cited-not-run
(`python/tests/cited_not_run.py`, R15), so cut 8's two L8 units — the
ordered-cuts predicate and the sequence-number negative — are **cited** to
`2026-08-22-conformance-cut-8-results.md` by L8-a and never re-run or
re-targeted here (the frozen §3 L8-a row carries the citation; the frozen §5
does not restate it, and this record does). The runner exited **0**. Its
final declaration lines, verbatim, were:

```text
declared arms: 18 (= 16 declaration units; 3 guarantee rows)
guarantee rows exercised: 3 (3 newly closed: L8, L4, L10; L1 re-homed to persistence-cut, partial)
```

Cut 36's own phases passed:

```text
[cut36 phase 2/3] test_event_order_acceptance.py
16 passed in 92.79s (0:01:32)
[cut36 phase 3/3] test_n2_cut36.py
10 passed in 32.85s
```

The whole chain ran in roughly 45 minutes of wall clock (12:53–13:38 UTC,
launched detached from the worktree's `python/`; its log is the main
checkout's `.work/acceptance/cut36-runner.log`); every earlier cut's phases
passed (56 `passed` lines in the runner log, no `failed`, `error`, `stale`
or `unsound`). The prefix's last lines were cut 35's own
(`declared arms: 28 (= 27 declaration units; 8 guarantee rows)` /
`guarantee rows exercised: 8 (6 newly closed: H4, G9, R10, T5, T1, T4; T2
and T7 partial)`). No test reaches the network.

All sixteen baselines reported **resolved**, and every one of the eighteen
mutations reported **sound**
(`test_every_live_check_resolves_and_passes_without_sabotage` and
`test_every_arm_fails_under_its_own_sabotage`, both in the `10 passed`
above). No unit was stale, vacuous, mixed or uncollected. `L8-a` and `L8-j`
are the two units homed to two arms each (`L8-a1`/`L8-a2`, `L8-j1`/`L8-j2`),
as the frozen §5 declares; every other unit is homed to exactly one. Each
unit's check is one function of
`python/tests/acceptance/test_event_order_acceptance.py`:

| declaration unit | check | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|
| L8-a (arms a1, a2) | `test_l8a_a_freeze_before_a_run_intent_across_ordered_cuts_orders_and_is_antisymmetric_durably` | resolved | sound, sound | L8 closes |
| L8-b | `test_l8b_co_appearance_is_unordered_and_later_cuts_holding_both_do_not_reverse_a_witness_durably` | resolved | sound | L8 closes |
| L8-c | `test_l8c_epoch_sequence_numbers_are_read_by_nothing_durably` | resolved | sound | L8 closes |
| L8-d | `test_l8d_a_cut_covering_one_corpus_establishes_nothing_durably` | resolved | sound | L8 closes |
| L8-e | `test_l8e_a_chain_replaced_under_another_fork_genesis_establishes_nothing_durably` | resolved | sound | L8 closes |
| L8-f | `test_l8f_the_double_witness_is_unordered_durably` | resolved | sound | L8 closes |
| L8-g | `test_l8g_valid_prefix_truncation_invalidates_every_witness_and_unknowns_the_removed_event_durably` | resolved | sound | L8 closes |
| L8-h | `test_l8h_same_chain_orders_by_ancestry_and_equal_moments_are_unordered_durably` | resolved | sound | L8 closes |
| L8-i | `test_l8i_a_pending_or_rolled_back_registration_has_no_moment_durably` | resolved | sound | L8 closes |
| L8-j (arms j1, j2) | `test_l8j_same_chain_independence_from_a_malformed_carrier_and_world_chain_durably` | resolved | sound, sound | L8 closes |
| L8-k | `test_l8k_the_refusals_and_a_terminal_corpus_durably` | resolved | sound | L8 closes |
| L4-a | `test_l4a_a_deleted_chain_refutes_against_its_registry_anchor_bound_by_corpus_id_durably` | resolved | sound | L4 closes (relabel) |
| L10-a | `test_l10a_a_replica_under_a_fresh_manifest_refuses_subject_mismatch_at_arrival_durably` | resolved | sound | L10 closes (relabel) |
| BI-1 | `test_bi1_recovery_precedes_resolution_on_both_paths_durably` | resolved | sound | boundary invariant |
| BI-2 | `test_bi2_one_world_inspection_and_the_world_lock_released_before_sorted_unnested_corpus_locks_durably` | resolved | sound | boundary invariant |
| BI-3 | `test_bi3_the_genesis_clause_alone_decides_a_placement_durably` | resolved | sound | boundary invariant |

**Staleness evidence.** The slice moved **no** pinned `before` string. Task
2's refactor, which factored `_epochs_ordered`'s descent into the pure
`_ordered_by_descent`, left cut 8's two L8 pins untouched and verified it
by count: `_publication_settlement`'s
`if type(entry) is SettledEntryView and entry.committed and entry.registration in publications:`
line and `_epochs_ordered`'s
`first = _packaging_identity(e1)` / `second = _packaging_identity(e2)`
lines each still occur exactly once (`grep -c` = 1 for both, `2fc2232`).
Neither `cited_not_run.py`'s `stale_arms` register nor any live guard's
`_LIVE_SABOTAGES` table changed on the branch; no frozen `n2_arms_cut*.py`
file changed. `tests/test_arm_staleness.py` and `tests/test_frozen_guards.py`
were green at every commit from Task 2 on, and with
`tests/test_recent_cut_acceptance.py` (which mocks `subprocess.run`, so the
cut-36 row never executes the runner) reported `25 passed` after Task 5
landed the declaration, guard, runner and row.

Before the run of record, Task 5 audited all eighteen arms through
`test_n2.audit` directly, each `sound`, and ran the guard with its sabotage
test deselected (`9 passed, 1 deselected`); Task 4's acceptance module had
passed on the certified volume on its first run (`16 passed in 77.86s`).
Task 3's seven gate modules (the composition-root, permit-boundary and
permit-entry-point inventories among them) reported `611 passed`, and
`just test-fast` on the tree after Task 3 reported `5208 passed, 1 skipped`;
the one Python skip is the intentional causal-only fixture arm cut 33's
record named (`tests/test_composite.py:119`). `just check` passed on every
commit of the lane through the pre-commit hook; `tasks check` reported zero
errors throughout. No capability refusal or waiver occurred. The full
repository gate (`just hook-pre-push`) is the merge's (§6).

## 2. Accounting

The cut carries **16 declaration units**: thirteen against rows — L8 (11),
L4 (1), L10 (1) — and three boundary invariants holding recovery before
resolution, the one world inspection with the audit's lock order, and the
isolated genesis clause of placement. **L8 closes in full**: the event
domain (an event is `(corpus_id, entry_digest)`; a registration's moment is
its committed settlement, a pending or rolled-back one has none; equal
moments are unordered), the witness predicate with coverage and
placeability explicit, and the witness-asymmetric relation answering
`a-precedes-b`, `b-precedes-a` or `unordered` over the world's retained
epochs, with the refusals `EventCorpusUnknown`, `EventCorpusUnresolvable`
and `EventUnknown` and the reads' own `EpochMalformed`, `BuildHold` and
`LogEvidenceRefused` propagating untranslated. **L4 and L10 close as
relabels** on cut 27's X5 shape: every clause cuts 8 (seven L4 units; L10's
arrival-identity arm), 9 (L4's store subject and distinct fork genesis;
L10's fork, replica, restore and store arms) and 10 (L10's two holdings-read
clauses) read is cited, and each row carries one durable check of its own
(L4-a, L10-a). **L1 is not read and stays partial**: its remaining arms —
kill the executor between entry durability and apply at every stage; crash
after entry durability but before the transaction record stores the entry
digest; cut persistence at every stage of the settlement sequence for both
terminal arms — are re-homed from `log-remainder` to `persistence-cut`
(`beliefs-3ea822`), the persistence-cut harness's arms behind
`atoms-f5779f` (spec decision 12; cut 8 §3.1's "no persistence-cut harness"
gap, named, not argued around). The unspellability arm stands certified at
cut 8.

`event-level-l8` — the `world-read` lane's head — closes with this cut, and
`log-remainder`, its ride-along, closes with it: both leave the ledger's
table and the roadmap's boundary index in the same commit, L4 and L10
closed and L1 carried by `persistence-cut`'s row. `act-report-remainder`
becomes the `world-read` lane's head.

The global corpus is **186 of 216 guarantee rows closed, 30 open**, a
three-row increase from cut 35's 183. `python/tools/roadmap_status.py`
carries the cut-36 accounting (added as
`36: ("conformance-cut-36-results §2", "L8, L4, L10", "")` in `ACCOUNTING`,
the plan's own place to record a new cut) and produces the roadmap's
Appendix A with the three rows closed, no row partial at cut 36, and no row
reopened; L1's last partial read stays cut 8's.

The cut changes no grammar, no kind and no contract: both `CONTRACT.yaml`
copies are byte-identical before and after the lane, `science.belief.v1`'s
answers are unchanged, and the TypeScript tree is untouched. `root.py` is
still the one `atoms` importer (`world/events.py` imports `beliefs.errors`
and `beliefs.world.logmodel` only; `world/verify.py`'s additions import
`epoch` and `registry` lazily); the relation calls no write primitive, so
`WRITE_ENTRY_POINTS` and `test_permit_entry_points.py`'s `CASES` are
unchanged. `_epochs_ordered` keeps its signature and contract and calls the
factored `_ordered_by_descent`; `root.event_order(config, a, b)` wraps
`verify._event_order` exactly as `epochs_ordered` wraps `_epochs_ordered`.

## 3. Evidence

No prior frozen declaration or cut body changed. Cut 36's §§2–7 remain
byte-exact to the freeze object; only its status line changes at discharge.
The cut-36 declaration remains byte-exact at its pinned SHA-256. Historical
evidence in prior results records and the reproduction record is unchanged
except by the addendum this cut adds to the reproduction record (§4).

### 3.1 Corrections carried by the cut document

The frozen cut required no post-freeze supplement, and no claim in its
frozen body is superseded by what the tree established. One omission is
restated here rather than edited there: **§5 does not restate that cut 8's
guard is cited-not-run** — the frozen §3's L8-a row carries the citation
("cut 8's two units … cited to `../plans/2026-08-22-conformance-cut-8-results.md`,
never re-run"), and §1 above states it for the runner: cut 36 chains cut
35's runner and neither runs nor re-targets `test_n2_cut8.py`.

### 3.2 Deviations from the plan, all reviewed and taken

**Frozen §5 versus the declaration.** No arm's module or sabotage claim
differs from the frozen §5 row; the declaration is the table, with each
`before` the tree's bytes. The staleness guard's site test
(`test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable`)
holds every `before` to exactly one occurrence in its named module, so a
mis-sited arm would have read `stale`; none did.

**Read at freeze.** The cut froze before its code existed, so the `before`
blocks §5 describes as "copied from the tree at freeze" were copied from
the tree once Tasks 1–3 had landed the surfaces (`ff6cb0c`; the eighteen
sites are tabled in Task 5's report), each occurring exactly once and each
mutation parsing. Two choices the tree's layout forced: L8-j2's `after`
keeps `if cross_chain:`, wraps a copy of the four-line retained-epochs
tuple in `try:` / `except EpochMalformed: epochs = ()`, and closes with
`if False:` so the original lines that follow the `before` remain a
parseable dead body; and BI-1's and BI-2's `before` blocks both begin at
the same line of `_event_order`'s world-lock block — BI-1's the two-line
inspect-then-scan sequence, which its `after` reverses, and BI-2's the
inspection line alone, which its `after` doubles — so the two arms mutate
one site with distinct `before` strings.

**Code and test deviations, by task.**

- **Task 0 (the freeze).** The guide's "Cut 35 is frozen and not yet
  discharged" paragraph no longer existed — cut 35's discharge had replaced
  it — so the cut-36 paragraph was added in that position rather than
  replacing anything; the worktree list at freeze had no `audio-baseline`
  entry; two literal quotation marks in the brief's closing sentences were
  dropped to match cut 35's frozen style; and the cut carries a
  `### 3.2 Rows not read` heading on cut 9's precedent.
- **Task 3 (the relation).** Three lint-only edits to the plan's test text:
  two unused `# noqa: E402` removed and one nested `with` merged (SIM117).
  The relation code is the plan's verbatim.
- **Task 4 (the acceptance module).** Three lint-only edits: RUF015
  (`[…][0]` → `next(…)` in `rewrite_an_interior_entry`); `# noqa: BLE001` on
  the overlapping-build thread's `except BaseException`, surfaced by the
  join below it; and L8-k's nested `with` merged (SIM117), the capture hold
  still entered before `pytest.raises(BuildHold)`. `run_assessment`
  returned normally in L8-a, so nothing on that path deviated. The plan's
  Step 4 command carried `-q` twice, which hides pytest's count line; this
  record quotes the runner log's lines instead. **L8-j checks the
  carrier-malformed and the world-malformed states separately** — the
  carrier is moved out of `epochs/` before the world chain is rewritten —
  not simultaneously as spec §8.2 case 6's "and" reads; both L8-j
  sabotages are caught either way (§3.3).
- **Task 5 (declarations, guard, runner, row).** Split at the long run: the
  implementer landed the four files and the `test_recent_cut_acceptance.py`
  row `(cut36, 36, (18, 16, 3))` with the fast gates, and the controller
  launched the chained runner detached and read its log (§1). The guard's
  row-parser reject list uses cut-36-shaped rows rather than cut 35's,
  since `unit_of` strips a trailing `1`/`2` only from `L8-a` and `L8-j`.
- **Task 6 (the reproduction).** `MM30_PREDECESSOR` had to be set
  explicitly, the same declared-default defect §13 and §14 of the
  reproduction record recorded.

**Reviews.** Every task review (0–6) approved with no Critical or Important
findings; no fix rounds were needed. The minor findings are §3.3's.

**Final review, following cut 35's pattern** (2026-09-21). Two Important
findings, both taken, landed after the final whole-branch review rather
than in the task that touched the code:

- **`root.py`'s `epochs_ordered` docstring named `event_order`.** The
  stale sentence §3.3 recorded as a Task 3 limitation — "the event-level
  relation is deferred and L8 is partial" — is now "the event-level
  relation is `event_order` (cut 36)".
- **`TestTheEventLevelRelation` gained
  `test_a_refused_inspection_propagates_untranslated`.** Spec §8.1
  decision D9's `LogEvidenceRefused` propagation was untested:
  `test_the_reads_own_refusals_propagate` covered only `EpochMalformed`
  and `BuildHold`. The new arm drives the `Inspections` double's `probe`
  hook to raise `LogEvidenceRefused` for the world root's inspection (the
  cross-chain question `l8_pair` asks) and for a corpus root's, and
  asserts the relation re-raises the same instance.

Both landed at `fff26ec`, alongside the two test-prose nits §3.3
also recorded (the double-witness docstring's "e2 and e4 follow each" and
the `A = Event` alias comment's non-existent `B`); the spec's §12 gained
the matching review-log entry in this same pass.

### 3.3 Limitations found at review

Review findings the lane deferred rather than fixed, by task, each a
limitation of the code or its tests as they stand; none reopens a row.

- **Task 0**: the cut document's §5 does not restate that cut 8's guard is
  cited-not-run (§3.1 and §1 restate it).
- **Task 3**: `root.py`'s `epochs_ordered` docstring still says the
  event-level relation is deferred and L8 is partial — to be amended
  before merge; the double-witness unit test's docstring says "e2 and e4
  follow each" while e4 follows e2's settlement; an `A = Event` alias
  comment mentions a non-existent `B` alias. Fixed after the final
  review: all three (§3.2).
- **Task 4**: L8-j checks the carrier-malformed and world-malformed states
  separately (carrier moved out before the world chain is rewritten), not
  simultaneously as spec §8.2 case 6 reads — both L8-j sabotages are still
  caught; L8-j's `aside` `mkdtemp` is not removed in a `finally`; the
  fixture's `built = Built()` sits outside its `try`; BI-2 compares a
  resolved path against the unresolved `world_root`, so a symlinked
  `SCIENCE_CUT4_ROOT` would fail it.
- **Task 5**: `test_n2_cut36.py`'s trailing "Export the live tuple" comment
  (inherited from cut 35) has nothing after it; L8-c's `after` is a dead
  binding, its bite resting on L8-c's source inspection.
- **Task 6**: none.

The frozen §7's four limitations stand as banked: the build window remains
the residual uncertainty, now visible as the double witness answering
`unordered`; capture-order sharpening is filed, not built (§5); the
relation has no consumer — comp §3.3's chronology claim has no finding
that consults it; L1's persistence arms are `persistence-cut`'s.

## 4. Reproduction measurement

The reproduction record's §15 addendum
(`../designs/2026-09-05-mm30-reproduction.md`) re-ran
`reproduction.rederive` on 2026-09-21 in a fresh process at `7cb5151`
against the existing corpus. No contract succeeded, so the corpus was
neither recreated nor moved aside — read in place, as at §13 and §14.
`MM30_PREDECESSOR` again had to be set explicitly, the same declared-default
defect §13 recorded.

The slice adds `beliefs.world.events`, factors `_ordered_by_descent` out of
`_epochs_ordered`, and adds `_event_order`, `_witnessed`, `_placement`,
`_event_carrier`, `root.event_order` and the three caller-input refusals,
none of it reached by the mm30 driver: `grep -n 'event_order\|_epochs_ordered'
python/tools/reproduction/*.py` is empty. mm30's world has one corpus chain
and its epochs order no cross-chain pair, so the relation is exercised by
the acceptance module alone.

The fresh answer was `NoBelief(reason="no-directional-outcome")`, equal to
the recorded answer (`rederived_equal: true`). `state.json` was rewritten
with byte-identical content (a full-file diff against the pre-run copy is
empty); only `findings.jsonl` gained the run's own log lines. No pinned
digest moved. Task 6 waited for the chained runner to exit before running
(§7).

## 5. Remaining boundary

`event-level-l8` closes in full at this cut, and `log-remainder` with it:
L8 closes, L4 and L10 close as relabels, and the `world-read` lane's head
is now `act-report-remainder`.

**L1** remains partial on its persistence arms — kill the executor between
entry durability and apply at every stage; crash after entry durability but
before the transaction record stores the entry digest; cut persistence at
every stage of the settlement sequence for both terminal arms — re-homed
here from `log-remainder` to `persistence-cut` (tier 2, `beliefs-3ea822`),
whose harness they are, behind `atoms-f5779f`. The unspellability arm
stands certified at cut 8. No cut argues the arms full by citing the
`atoms` suite.

**T2** remains partial on the `audit` and `re-check` operation kinds, owned
by `act-report-remainder` (`beliefs-86b150`), unchanged by this cut.

**T7** remains partial on its cross-root case, owned by
`cross-root-publication` (tier 3, `beliefs-256f17`), unchanged by this cut.

One open question is filed rather than left as a hidden limitation, and it
reopens no row this cut closes: **capture-order sharpening of the
event-level relation** (`../guide/open-questions.md`, spec §11.2) — the
build captures serially in sorted `corpus_id` order, so E1's A-head
containing `a` and B-head excluding `b` implies `a` before `b` in real time
exactly when `A < B`; using it would order the double witness. Not built;
a design amendment to the log design §7 when a consumer needs it.

## 6. Main integration

Filled at merge.

## 7. Execution rulings

Every `Ruling:` entry from the execution so far, in chronological order:

- **Leave the frozen §5's cited-not-run omission as frozen and restate it
  in this record** (Task 0's review). A frozen body is not edited after its
  commit; the frozen §3 L8-a row carries the citation and §1 and §3.1 here
  restate it for the runner. Cost if wrong: a reader of the frozen §5 alone
  would not see that cut 8's guard is never run.
- **Task 6 waited for the chained runner to exit before re-running the
  reproduction.** `reproduction/state.py` rewrites `state.json` with a
  non-atomic `write_text`, and cut 32's guard plus the composite and
  estimand acceptance modules in the prefix chain read mm30's `state.json`;
  a racing read could have failed the run of record. Cost if wrong: about
  45 minutes of serialization on a run that would otherwise have raced.
