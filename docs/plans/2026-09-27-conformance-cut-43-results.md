# Conformance cut 43 — results

**Cut:** `../designs/2026-09-27-conformance-cut-43.md`
**Freeze:** `946657f`; SHA-256 `4ddc0883d9eadee9f16693101798737e0d7594724e819c93e01857ebdbd71596`
**Declaration:** `python/tests/n2_arms_cut43.py`; SHA-256 `6632623d9b9028172459e23885d3aa9651f05789cef62e95fb51776bb3cd7393`
**Subject:** one write root, manifest-pinned mounts, coordination across mounts and corpus-matched reconciliation
**Design:** `../superpowers/specs/2026-09-27-session-mounts-design.md`
**Plan:** `../superpowers/plans/2026-09-27-session-mounts.md`
**Discharged:** 2026-09-27 on `design/session-mounts`, implementation through `60f37ad`; reproduction at `0a864cf`
**Runner:** `python/tools/cut43_acceptance.py`

## 1. What ran

The final post-review fixed-tree runner ran from `.worktrees/session-mounts/python` through
`host-budget run -- uv run --frozen python tools/cut43_acceptance.py`, with
`SCIENCE_MM30_ROOT` on the main checkout's certified volume. Its tracked foreground
command exited 0; the retained log is main `.work/acceptance/cut43-runner-postreview.log`.
The runner chains cut 42 (`PREFIX_RUNNERS = ("cut42_acceptance.py",)`), retaining
the historical live prefix; cut 8 remains cited-not-run. All **70 pytest phases and
1106 passing invocations** passed, including inherited repetitions. Reported pytest
times total **3148.72 seconds**; elapsed time was approximately 54 minutes.
The final run had no failed phase, refusal, abort or retry.

```text
[cut43 phase 2/3] test_session_mounts_acceptance.py
13 passed in 12.99s
[cut43 phase 3/3] test_n2_cut43.py
10 passed in 11.95s
declared arms: 9 (= 9 declaration units; 4 guarantee rows)
guarantee rows exercised: 4 (4 newly closed: J12, J13, J14, J15)
```

The guard resolves every baseline and finds every mutation sound: no stale,
vacuous, unresolved or uncollected arm. Each unit homes one arm, with no co-citation.
Acceptance checks below live in `python/tests/acceptance/test_session_mounts_acceptance.py`;
the portable checks name their modules under `python/tests/` explicitly.

| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| J12-a | `test_j12_a_a_write_root_outside_the_configured_roots_refuses_durably` | `session/__init__.py` | resolved | sound | J12 closes |
| J12-b | `test_j12_b_a_mount_set_other_than_the_configured_roots_refuses_durably` | `session/__init__.py` | resolved | sound | J12 closes |
| J12-c | `test_j12_c_the_session_writes_the_named_root_and_only_it_durably` | `session/__init__.py` | resolved | sound | J12 closes |
| J13-a | `test_mount.py::test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin` | `mount.py` | resolved | sound | J13 closes |
| J13-b | `test_mount.py::test_an_available_unpinned_document_is_never_activated` | `mount.py` | resolved | sound | J13 closes |
| J14-a | `test_j14_a_coordination_resolves_over_every_mount_durably` | `session/__init__.py` | resolved | sound | J14 closes |
| J15-a | `test_j15_a_a_session_never_writes_a_read_mount_durably` | `session/__init__.py` | resolved | sound | J15 closes |
| J15-b | `test_session_reconcile.py::test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there` | `session/reconcile.py` | resolved | sound | J15 closes |
| J15-c | `test_session_reconcile.py::test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified` | `session/reconcile.py` | resolved | sound | J15 closes |

A certified pilot exercised durable setup, acceptance and all nine baseline/mutation
checks without the historical prefix before the unmodified full runner ran.
The recent-cut row is `(cut43, 43, (9, 9, 4))`, including the rows-exercised line;
that interface test mocks subprocesses, while the full chain supplies discharge evidence.

## 2. Accounting

**9 arms, 9 declaration units, 4 guarantee rows. J12–J15 close in full.**

- **J12:** the explicit write root belongs to the world; mounts cover exactly its
  roots without aliases; opening refusals leave no session directory.
- **J13:** manifest pins resolve by namespace and content identity; unpinned
  available documents never activate and unresolved pins refuse explicitly.
- **J14:** project selection, revision, standing and divergent tips resolve across
  every mount; a revision writes the selected write root.
- **J15:** read roots, chains and metadata siblings stay unchanged through the
  lifecycle and reconciliation, which matches corpus and registration digest.

The corpus is **214 of 241 guarantee rows closed, 27 open**, up four from the
merged pre-discharge tree's 210 of 241. No row reopens. The entry
`43: ("conformance-cut-43-results §2", "J12, J13, J14, J15", "")` in
`python/tools/roadmap_status.py` generates Appendix A with
`Closed 214 of 241; open 27.` The J table is closed across cuts 19 and 43.
`multi-corpus-session` closes, tier 1 **on the path**, the second-project milestone's
kernel prerequisite. Science's `sci-923d3a` launcher wiring and `beliefs-c08725`
relocation remain prerequisites of that measurement.

## 3. Evidence

The frozen cut body is byte-exact; this change edits only its status line.
The declaration retains the hash above. The thirteen acceptance cases match frozen
§3. `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and `CASES` in
`test_permit_entry_points.py` are unchanged and closed in both directions; no new
write primitive or entry point is introduced. `root.py` remains the one `atoms` importer.

**Only cut 19's J9a is retargeted**, in its guard's `_LIVE_SABOTAGES` table, to
`if write_root not in world_config.corpus_roots:` → `if False:`. Its zero-root
case supplies a real adopted write root with a well-formed chain, making membership
the only refusal. Removing it opens the session and fails the check. The old
two-root refusal is removed because J12 now requires two-root opening. All other
prior pins remain unchanged; the staleness probe is clean. The final chained run
passes both cut 19 phases and cut 42's unchanged frozen guard.

The spec's §13 planning notes are realized:

- A pins base, fixture `biology("fixture")` and coordination v2; B uses shipped
  biology and coordination v2; C uses fixture biology alone, the mm30 shape;
  D shares A's profile. Two biology documents cannot pin the same namespace.
- J15-a rebinds the writer and operation port to the first read mount whose
  profile equals the writer's, D. Binding B would refuse profile mismatch before
  isolation is checked. The mutant reaches and fails tree equality after
  reconciliation; the comparison includes read chains and metadata siblings.
- Malformed pin spelling remains `ManifestMalformed`; `MountPinUnresolved`
  names a well-formed unresolved pin, including an unshipped science identity.
- J12-c binds the whole session to `corpus_roots[0]`, the one-edit writer-factory
  sabotage; selecting the second root exposes it.
- J13's two units and J15-b/c live in the portable modules in §1; the latter use
  stand-in chain views to check both wrong-corpus directions and the right-corpus control.
- `mounts=None` disables coordination; an empty mapping omits configured roots
  and refuses. They are distinct configurations.

**Task 8 self-review correction:** the writes guide still described cut 42
remote publishing as frozen before implementation after its merge and discharge.
Its current-state list now records cuts 42 and 43 as built, and its guarantee
links name J1–J15 and Y1–Y16. A separate correction restores the original
guarantee table: a blank line introduced while banking J12–J15 had separated
J10 from it. All frozen J1–J11 row text remains byte-identical to main.

**Task 8 whole-branch review, J12-c:** the selected-root acceptance used A/B,
whose profiles differ. Its frozen wrong-root mutation bound A while selecting B,
so profile compatibility refused before the intended selected-root assertion.
The acceptance case now selects each of A/D, which already share a profile;
heterogeneous A/B resolution remains exercised by J14 and J15. No frozen
mutation, declaration, row, acceptance count or production code changed.

The direct corrected baseline exited 0; the frozen J12-c mutant exited 1 at
`assert session.corpus_root == write`, with no `ContractMismatch`. Full output is
main `.work/acceptance/cut43-j12-fix-pilot.log`. The certified prefix-free pilot
passed 13 acceptance cases and 10 guard checks. The final unmodified full chain
then ran on this corrected tree from 22:15 to 23:09 UTC, exited 0, and supplies
§1's replacement evidence in `cut43-runner-postreview.log`. The earlier
`cut43-runner-final.log` is retained as evidence before this correction.

## 4. The reproduction

`../designs/2026-09-05-mm30-reproduction.md` §22 records Task 6's certified preflight
(`ok`, exit 0) and re-derive (exit 0). The answer remains
`NoBelief(no-directional-outcome)` with equality true. Step 10b's scope, verdict,
report identity and restored spec identity agree; step 10c's restoration,
assessment, belief and prior pre-grammar checks agree. The before copy and rewritten
`state.json` are byte identical (`cmp` exit 0, empty full diff), both SHA-256
`1efbd06c433ba6546b9be92e45c91ad0ae5528f328b58f070311768e64861ae1`.
The driver opens one corpus through library readers and calls neither attended
sessions nor mounts. This is compatibility evidence; science's `sci-0d00d2` owns
the second-project measurement after wiring and relocation. Task 6's focused
reproduction and design tests passed all 50 cases.

## 5. Remaining boundary

None for `multi-corpus-session`: J12–J15 are discharged in full. Spec §10's
limitations remain:

1. Every mount pins the shipped base; base succession needs its own design.
2. Read chains are not verified at open. Coordination reads what `ReadView` sees;
   publish checks chains at step 0 and reconciliation reports them.
3. There is no cache.
4. Ordinary writes do not target another corpus; this remains with world resolution.

The second-project milestone has not been measured by the one-corpus reproduction.
The `write-path` lane closes again; `contract-cut` stays first off the path.

## 6. Main integration

Task 8's whole-branch review and scoped re-review approved the final tree.
`just gate` exited 0 on `4c80d2b`: 5847 Python tests passed with one skip,
standalone N2 passed 46, and TypeScript passed 155; static checks passed.
The closure commit was `1624a4c`, and `design/session-mounts` merged into `main`
at `9e3822c`. The merged Python and TypeScript trees are byte-identical to the
gate-tested tree. `just check` passed on merged `main`.

## 7. Execution rulings

- Cut 43 froze after cut 42's freeze. Main, including cut 42's discharge, merged
  at `7d529d8` before Task 5. The combined corpus has 82 designs; README and its
  spelling dictionary were corrected after the fast suite exposed the branches'
  count disagreement. The rerun passed 5847 cases with 1 skip.
- **J9 has five refusing configurations, not the plan's six:** four loop cases
  plus the separate chainless case after removing the two-root refusal. All specified
  cases remain; store-root refusal is separately covered. This corrects a count.
- Task 4 review added three observations: compare J15-a state after reconciliation,
  assert J12's complete serialized full-permit summary, and assert J14 revision
  refuses with `mounts=None`. The thirteen acceptance cases passed.
- Task 5 review found J15-a could fail on reconciliation findings before its
  designated tree assertion. The fix captures findings, compares every read tree
  and metadata sibling, then asserts no findings. Direct baseline exited 0; the
  mutant exited 1 at tree equality. Evidence is main
  `.work/acceptance/cut43-j15-fix-pilot.log`. Focused acceptance and guard checks
  passed 23 cases, followed by the earlier fixed-tree chain in
  `cut43-runner-final.log` (70 phases, 1106 passes, 3038.18 seconds summed pytest
  time). Task 8 then corrected J12-c and repeated the complete chain as §1 records. The earlier
  `.work/acceptance/cut43-runner.log` is retained, not substituted for the fixed-tree run.
- The guard resolves each `UNIT_CHECKS` module path because the approved units
  span three modules; cut 42's single-module guard assumption did not apply.
- The prefix-free certified pilot preceded the expensive full chain. The permanent
  runner still chains cut 42, and all nine arms and four rows remain frozen.
- Conflicting harness session variables produced task lifecycle provenance warnings,
  filed as `relay-c85a0f`; task checks stayed clean.
- The ledger and roadmap remove the closed boundary row together to preserve their
  tested equality, retaining discharge in prose. Frozen plan checkboxes and cut text
  remain historical; this record and the current ledger report delivery status.
