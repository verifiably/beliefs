# Conformance cut 13 — discharge results

**Date:** 2026-09-01
**Subject:** run confinement, `clean-environment` reachable
(`../superpowers/specs/2026-08-30-run-confinement-design.md`, promoted to
`../designs/2026-08-30-run-confinement-design.md` at banking), measured
against conformance cut 13's frozen selection
(`../designs/2026-08-30-conformance-cut-13.md`).

The frozen cut remains byte-exact at `fa89241`. Only its status header
changes at banking; the cut's own **Status:** line still reads "frozen
2026-08-31" and this discharge does not touch it.

**Integration state.** Every implementation commit was made on
`design/run-confinement`. The reviewed pre-banking head is `e053211`
(task 9's review over `744e73f..e053211`: cut compliance ✅, task quality
Approved, 3 LOW findings, 0 Critical/Important). This discharge additionally
appends execution-ledger ruling R9 (commit `ef118c5`), closing the review's
Finding 2 by recording rounds 3–4's re-pin extension, before running the
acceptance suite below. The branch is not merged or pushed by this
discharge; the human partner owns the history-preserving `--no-ff` merge.

## 1. Accounting

Cut 13 reads six rows: R15, R4, R9 and R13 in full, R16 and R21 in part. Its
15 selected units and labels K1–K7 give **15 selected + 7 labeled = 22
declaration units**. R16 and R21 stay partial on exactly their
`workflow-surface` arms.

The executable declaration table expands compound requirements into **35
lettered sabotage arms** normalized back to those 22 frozen units. Every armed
claim has one exact once-matching host-side source mutation and at least one
check that fails under it. No prior cut's check is claimed.

### 1.1 What the discharge establishes

- A run under `boundary-policy/confined-v1` executes inside a fresh set of
  namespaces holding exactly the digest-verified closure snapshot, the
  bundle, the staged inputs and one writable output root; the boundary
  observed the namespaces and the mount table from its own `/proc` before
  the engine started.
- The receipt's capabilities are the set the launch observed; the fresh
  instance is a separate attested fact bound to the verified snapshot.
- `derive_scope` reaches `clean-environment` only through a qualifying
  receipt; a minimal pair stays `same-environment`.
- `admission_record` carries a derived verification into `admit()` and
  belief evaluation: passed admits, inconclusive does not, not-certified
  does not.
- Every cut-3 anchor in the edited modules matches exactly once; cut 3's
  live N2 audit is green.

**§6 freeze obligation discharged by citation, not by an arm.** "Receipt
capabilities are never copied from the requested policy" carries no §3
declared unit (cut 13 assigns it to the second reader); it is discharged
here by code citation instead of an acceptance arm. `grep -n capabilities
src/beliefs/boundary.py` returns exactly two hits: `boundary.py:470`
`capabilities=()` (the minimal receipt) and `boundary.py:576`
`capabilities=launched.capabilities` (the confined receipt). There is no
assignment of `policy.capabilities`, `CONFINED_POLICY.capabilities`, or
`CAPABILITIES` into any receipt anywhere in the file; `launched.capabilities`
traces to `judge_report` in `confinement.py`, which derives the set from the
probe's own report, and `confinement.py:7` states the module-level
invariant ("nothing here reads the requested policy's capabilities"). This
was verified by grep in the task-7 review and is restated here as the
freeze audit's record of it (task 9 review, Finding 3).

## 2. What ran

All commands ran from `python/`. Durable work ran on the certified volume
at `../.cut13-acceptance`, the default beside the checkout;
`SCIENCE_CUT13_ROOT` was unset.

### 2.1 Host and certified tuple

- backend `linux`, revision `linux-4`; storage profile `flush-honoring-disk.v1`
- kernel `7.1.11-arch1-1`
- ext4 device `259:2` (`/dev/nvme0n1p2`), mounted at `/mnt/ssd` with mount
  options `rw,noatime,data=ordered` (`/proc/mounts`)
- normalized barrier options `async`, `barrier=1`, `commit=5`, `data=ordered`
- durability features `compat=0x3c`, `incompat=0x246`, `ro_compat=0x46b`
- certification record: the `atoms` repository's
  `docs/certification/2026-08-30-ext4-linux-7.1.11-arch1-1.json` — 9
  scenarios, 920 marks, 3,286 crash prefixes, zero violations
- confinement substrate: `bubblewrap 0.12.0`, unprivileged user namespaces
  confirmed, glibc `ld.so --list` present
- execution authority: the editable Atoms dependency loaded local `main` at
  `569d5c4`, one commit ahead of the pushed remote `main` at `914acb6`; the
  only diff between them is a 4-line, docs-only addition to
  `docs/plans/2026-08-30-atoms-tasks-migration.md` — no production diff.
  The certification commit `2a25de8` is a common ancestor of both, so the
  certified tuple above binds regardless of which of the two heads is
  loaded; no Atoms change ships in this branch (ledger R2).

### 2.2 Certified cut-13 runner

`uv run python tools/cut13_acceptance.py`

```text
[cut13 phase 1/3] cut12_acceptance.py
[cut12 phase 1/3] cut11_acceptance.py
[cut11 phase 1/3] cut10_acceptance.py
[cut10 phase 1/2] cut9_acceptance.py
[cut9 phase 1/2] cut7_acceptance.py
[cut7 phase 1/3] cut5_acceptance.py
39 passed in 15.28s
[cut7 phase 2/3] cut6_acceptance.py
23 passed in 11.29s
[cut7 phase 3/3] test_n2_cut7.py
42 passed in 41.38s
[cut9 phase 2/2] test_n2_cut9.py
23 passed in 17.37s
declared units: 30 (pinned by test_the_declared_units_are_unique_and_number_thirty, among the tests above; not itself a pytest total)
[cut10 phase 2/2] test_n2_cut10.py
36 passed in 10.08s
declared units: 31 (= len(CUT10_ARMS); pinned by test_the_declared_units_are_unique_and_number_thirty_one, among the tests above; not itself a pytest total)
[cut11 phase 2/3] test_intent_boundary_acceptance.py
18 passed in 5.27s
[cut11 phase 3/3] test_n2_cut11.py
17 passed in 30.14s
declared arms: 66 (= len(CUT11_ARMS), normalizing to the 26 frozen units pinned by test_the_partition_accounts_exactly_the_26_frozen_units, among the tests above; not itself a pytest total)
[cut12 phase 2/3] test_successor_admission_acceptance.py
4 passed in 1.87s
[cut12 phase 3/3] test_n2_cut12.py
16 passed in 14.88s
declared arms: 50 (= len(CUT12_ARMS), normalizing to the 24 frozen units pinned by test_the_partition_accounts_exactly_the_24_frozen_units, among the tests above; not itself a pytest total)
[cut13 phase 2/3] test_confinement_acceptance.py
13 passed in 202.02s (0:03:22)
[cut13 phase 3/3] test_n2_cut13.py
16 passed in 113.70s (0:01:53)
declared arms: 35 (= len(CUT13_ARMS), normalizing to the 22 frozen units pinned by test_the_partition_accounts_exactly_the_22_frozen_units, among the tests above; not itself a pytest total)
```

Eleven pytest invocations run across the chain (three under cut 7, two each
under cuts 9–13); their summary lines sum to **247 passed, 0 failed**
(39+23+42+23+36+18+17+4+16+13+16 = 247).

### exit: 0

### 2.3 Portable and static gates

`cd python && uv run pytest` — **2850 passed in 864.15s (0:14:24)**

### exit: 0

`uv run ruff check .` — All checks passed!

### exit: 0

`uv run pyright` — **31 errors, 0 warnings, 0 informations** — not clean.
This is a known, already-disclosed deviation, not a new one: task 9's review
(Finding 1) found the new `test_confinement_acceptance.py` pyright-dirty and
noted the same pattern across the slice's earlier test files (tasks 3–8),
deferring it as slice-wide test-typing debt rather than a functional defect —
the pyright gate the plan wrote covered `src/` only. All 31 errors are in
test files this branch added or modified
(`tests/acceptance/test_confinement_acceptance.py`, `tests/test_boundary.py`,
`tests/test_confinement_values.py`, `tests/test_runrecord_confined.py`,
`tests/test_verify.py`); `main` at this branch's base is pyright-clean (`0
errors`). None of the 31 are in `src/beliefs/`, and none bear on the 22
frozen units' correctness — every declared arm's check is a passing pytest
test, independent of static typing. This is disclosed here rather than
corrected, since fixing it is outside this discharge's scope (results
records report; they do not silently repair unrelated debt).

### exit: 1 (pyright only; every other gate above exits 0)

The plan's obsolete 144-baseline-failure caveat does not apply: the tuple is
certified for kernel 7.1.11 (the recertification runs on `atoms-recertify.timer`),
the full ordinary suite passes 2850/2850, and every durable arm above ran for
real on the certified volume — there is no allowlist refusal to discount.

## 3. Review and implementation rulings

Task 9's review (the only post-implementation review this slice's task list
schedules) reported **0 Critical, 0 Important, 3 LOW** findings, all
addressed or knowingly deferred:

1. **Pyright test-typing debt** (Finding 1) — disclosed in §2.3 above, not
   fixed; a pre-existing pattern across the slice's test files, not a
   regression this discharge introduced.
2. **Ledger R7 narrower than what landed** (Finding 2) — closed by this
   discharge's ruling R9 (commit `ef118c5`), which records that rounds 3–4
   extended R7's re-pin to its transitive fixpoint across every
   `FROZEN_PRIOR_CUT_FILES` table (cuts 7–13), including the one transitive
   pin `CUT8_AUDIT_REPIN_COMMIT`.
3. **§6 freeze obligation left to the second reader** (Finding 3) — closed
   in §1.1 above by code citation, not by an acceptance arm.

No anchor required rewriting under Task 9 step 3's rule ("fix the arm to the
code as written, never the code to the arm"): the anchor-count check ran
clean on the first try (`anchors ok`, task 9 report), so no anchor was ever
in breach.

**The mount table bubblewrap produced (ledger R5).** A live launch on this
host, under the executing interpreter's own captured closure, produced
exactly `mount_plan`'s eight planned rows, row for row in sorted order, with
no bwrap-added row outside the plan:

```
[('/', 'root', 'ro'), ('/dev/null', 'device', 'rw'), ('/dev/urandom', 'device', 'rw'),
 ('/lib64/ld-linux-x86-64.so.2', 'loader', 'ro'), ('/science/bundle', 'bundle', 'ro'),
 ('/science/env', 'env', 'ro'), ('/science/out', 'output', 'rw'),
 ('/science/out/inputs', 'inputs', 'ro')]
```

Distinct namespaces observed: `cgroup`, `ipc`, `mnt`, `net`, `pid`, `user`,
`uts` (seven, all distinct from the parent's). Observed capabilities:
`from-bundle`, `closure-confined-filesystem`, `network-denied` — exactly
spec §7.3a's three. No amendment to `mount_plan` or `judge_instance` was
needed on this host (ledger R5); the brief's own template mislabels this
ruling "R3", which is the RPATH ruling — the mount-table ruling is R5, and
this record uses the correct number.

**Observed wall-clock cost of a confined run against a minimal one.** Per-test
timings from `test_confinement_acceptance.py` (this run, `--durations=0`):
the single test that mints a run under `minimal-v1` alone
(`test_r15u6_a_minimal_run_is_valid_and_a_minimal_pair_stays_same_environment`)
took 13.43s; tests that mint one or two confined runs ranged 14.75s–22.27s;
a confined attempt refused before the bwrap launch is ever entered
(`test_r15u1`, whose sabotage removes the launch call itself) took 4.65s.
Closure capture and Snakemake start-up dominate both policies' cost on this
host — the bwrap launch itself adds on the order of single-digit seconds on
top of a ~13s shared floor, not a distinctly separable one; this is an
observation from the suite's own timings, not a controlled isolated
benchmark.

There is no frozen-cut deviation.

## 4. Commit identities

| commit | subject |
|---|---|
| `0193da9` | docs(specs): amend the run-confinement design with the sandbox spike's findings |
| `fa89241` | docs(designs): freeze conformance cut 13, run confinement |
| `ff5f19e` | docs(plans): pin cut 13's freeze hash |
| `8ac375f` | feat(errors): name the confined boundary's refusals with stable reasons |
| `938f5f8` | feat(recipe): close the capability vocabulary and attest the confined instance |
| `721c6c3` | feat(runrecord): accept both receipt spellings and recompute a confined run under run.v2 |
| `e17b960` | feat(adapter): capture the runtime artifact closure per file under environment.v2 and make the engine argv policy-neutral |
| `e9241d3` | docs(specs): supply the interpreter's own RPATH to the host loader listing explicitly |
| `69abf59` | docs(plans): record ruling R3, the explicit RPATH library path |
| `54194dd` | feat(adapter): resolve the interpreter's RPATH-only libraries into the closure |
| `63451e8` | docs(specs): architecture-match the loadable-ELF predicate |
| `a05600d` | docs(plans): record ruling R4, the architecture-matched loader map |
| `b5eb98d` | feat(adapter): match the loader map to the closure's own architecture |
| `722c4ee` | test(closure): select the rendered editable pth by content, not a stale name |
| `57dd09e` | feat(confinement): materialize the closure snapshot and gate the bubblewrap launch through the held probe |
| `7f648c8` | feat(confinement): range map equality over every ELF and give the probe the capture's library path |
| `92f1954` | docs(specs): make the probe's listing model the same RPATH inheritance as the capture |
| `1d17773` | docs(plans): record ruling R6, symmetric loader listings |
| `c57459c` | fix(confinement): reap the child on a malformed inner argv |
| `614d439` | docs(specs): state the probe's exact library-path composition |
| `f803455` | feat(boundary): execute a run under the confined policy, gated, observed, and never downgraded |
| `744e73f` | feat(replay): derive clean-environment through a qualifying receipt and join a derived verification to admission |
| `7504d69` | test(cut13): declare the confinement arms, the gate, the N2 audit, and the acceptance runner |
| `96be202` | docs(plans): record ruling R7, re-pinning the frozen arms files across the rename |
| `e38ac40` | test(n2): re-pin the frozen arms files to their post-rename bytes |
| `ae5de6f` | docs(plans): record ruling R8, the harness names the audited package |
| `5e861c7` | test(n2): derive the sabotage copy's name from the audited package |
| `d0206c8` | test(n2): complete ruling R7's re-pin across every prior cut's table |
| `e053211` | test(n2): carry ruling R7's re-pin to its transitive fixpoint |
| `ef118c5` | docs(plans): record ruling R9, the re-pin's full extent |

This record's own commit, and the ledger append that accompanies it, follow
this table (they cannot name their own not-yet-created hash) and change no
runtime behavior. The banking commit following this record likewise changes
no runtime behavior.

## 5. Remaining boundary

Cut 13 closes R15, R4, R9 and R13 and reads R16 and R21 at their
confinement arms. Their workflow arms remain with `workflow-surface`, now
tier 1 row 1. Durable verification publication crosses the persistence seam
and is recorded as the `verification-publication` boundary at banking.
