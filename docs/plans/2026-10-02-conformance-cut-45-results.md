# Conformance cut 45 — results

**Cut:** `../designs/2026-10-02-conformance-cut-45.md`
**Freeze:** `4bec463`; SHA-256 `77632defceae5cddc6006151997774a173d13ff4861d4c099a7331e24a96ef16`
**Declaration:** `python/tests/n2_arms_cut45.py`; SHA-256 `e845aff4e54eb74e88b561e77aa9fd6be4afe6246851b87fd95ee78e95e4d94b`
**Subject:** caller-supplied acceptance inside evidence gathering and standing folds, with the opaque statement bound into the belief closure
**Design:** `../superpowers/specs/2026-10-02-belief-acceptance-design.md`; SHA-256 `e808237b587c9b535be9a1bec37945dd53238083afc0bc81c4e4c1d77043eca9`
**Plan:** `../superpowers/plans/2026-10-02-belief-acceptance.md`; SHA-256 `233261715a7f7728c17e8a5b2532096745dce79b4413f7c9880221df07ad3e5c`
**Implementation and declaration:** through `92c9ae7`, branch `feat/acceptance-filter`
**Discharged:** 2026-10-02 on `feat/acceptance-filter`; product/declaration through `92c9ae7`, final status documentation in this commit
**Reviewed document hashes:** design and plan hashes above are their reviewed bytes at `92c9ae7`; the final pass updates status metadata below
**Log SHA-256:** `be0fea9fc4e59ce9a06ede0083587fc4e0ebec07b61041de1b11757499326149`
**Runner:** `python/tools/cut45_acceptance.py`

## 1. What ran

The bounded pilot ran before the extended chain on the certified tuple:
kernel `7.2.2-arch1-1`, ext4 volume `/dev/nvme1n1p2` mounted with
`rw,noatime,data=ordered`. Eight durable cases passed in 63.75 seconds;
the four selected pilot arms G10-a/G11-d/G12-i/G13-d passed baseline and
mutation checks in 6.99 seconds. The stable declaration's complete guard
then passed 11 checks in 27.94 seconds, including all 34 mutation verdicts.
These runs used the main checkout's `.work/acceptance/cut45` durable root.

The successor invocation started 2026-10-02T11:28:44Z from the canonical
worktree directory at `92c9ae7`, through the recorded test front door:

```text
just --set one_cmd 'cd python && uv run --frozen python tools/cut45_acceptance.py' test-one -q
```

The recipe supplies `host-budget run`; an additional wrapper is unnecessary.
The runner uses the normal main-checkout durable root, chains cut 44, and
adds `test_belief_acceptance.py` and `test_n2_cut45.py`. The structural path
fix in `beliefs-fdc40f` makes a shortened `SCIENCE_CUT44_ROOT` unnecessary.
The retained log is main `.work/acceptance/cut45-runner.log`.

The invocation exited **0**. All **74 pytest phases and 1,145 passing
invocations** passed, with no failure, error, skip or capability refusal.
The 73 printed summaries report **3,320.08 seconds** of pytest time. The
forwarded `-q` suppresses the final guard summary: its eleven passing dots
and the successful runner return establish that phase; its duration is not
included in that subtotal. The final log write was 2026-10-02T12:25:58Z,
**3,434.13 seconds (about 57 minutes 14 seconds)** after invocation start.

```text
[cut45 phase 2/3] test_belief_acceptance.py
8 passed in 50.93s
[cut45 phase 3/3] test_n2_cut45.py
........... [100%]
declared arms: 34 (= 34 declaration units; 4 guarantee rows)
guarantee rows exercised: 4 (4 newly closed: G10, G11, G12, G13)
```

Each row below summarizes the completed phases for that cut, including
inherited repetitions. Cut 45's time cell excludes its quiet final guard.

| cut | phases | passing invocations | reported pytest seconds |
|---|---|---|---|
| 17 | 19 | 400 | 847.39 |
| 18 | 2 | 23 | 84.30 |
| 19 | 2 | 38 | 60.18 |
| 20 | 2 | 22 | 56.80 |
| 21 | 2 | 11 | 32.53 |
| 22 | 2 | 9 | 7.88 |
| 23 | 2 | 37 | 162.01 |
| 24 | 2 | 22 | 117.63 |
| 25 | 2 | 29 | 46.82 |
| 26 | 1 | 10 | 1.53 |
| 27 | 2 | 51 | 284.45 |
| 28 | 2 | 34 | 157.46 |
| 29 | 2 | 19 | 13.98 |
| 30 | 2 | 30 | 42.90 |
| 31 | 2 | 20 | 16.96 |
| 32 | 2 | 20 | 47.58 |
| 33 | 2 | 21 | 84.68 |
| 34 | 2 | 27 | 150.81 |
| 35 | 2 | 37 | 68.78 |
| 36 | 2 | 26 | 116.44 |
| 37 | 2 | 21 | 16.69 |
| 38 | 2 | 31 | 42.18 |
| 39 | 2 | 26 | 63.67 |
| 40 | 2 | 44 | 296.88 |
| 41 | 2 | 29 | 46.69 |
| 42 | 2 | 46 | 334.45 |
| 43 | 2 | 23 | 26.36 |
| 44 | 2 | 20 | 41.12 |
| 45 | 2 | 19 | 50.93 + unreported guard |


| declaration unit | check | sabotage site | baseline | mutation | guarantee-row effect |
|---|---|---|---|---|---|
| G10-a | `test_acceptance.py::test_g10_a_all_assessments_rejected` | `evaluation.py` | resolved | sound | G10 closes |
| G10-b | `test_acceptance.py::test_g10_b_contradictory_twin` | `evaluation.py` | resolved | sound | G10 closes |
| G10-c | `test_acceptance.py::test_g10_c_malformed_assessment` | `evaluation.py` | resolved | sound | G10 closes |
| G10-d | `test_acceptance.py::test_g10_d_canonical_holder` | `evaluation.py` | resolved | sound | G10 closes |
| G10-e | `test_acceptance.py::test_g10_e_manifest_preflight` | `evaluation.py` | resolved | sound | G10 closes |
| G10-f | `test_acceptance.py::test_g10_f_accepted_attribution` | `evaluation.py` | resolved | sound | G10 closes |
| G11-a | `test_acceptance.py::test_g11_a_rejected_failure` | `evaluation.py` | resolved | sound | G11 closes |
| G11-b | `test_acceptance.py::test_g11_b_rejected_pass` | `evaluation.py` | resolved | sound | G11 closes |
| G11-c | `test_acceptance.py::test_g11_c_rejected_superseder` | `evaluation.py` | resolved | sound | G11 closes |
| G11-d | `test_acceptance.py::test_g11_d_failure_names_rejected_twin` | `evaluation.py` | resolved | sound | G11 closes |
| G11-e | `test_acceptance.py::test_g11_e_pass_names_rejected_twin` | `evaluation.py` | resolved | sound | G11 closes |
| G11-f | `test_acceptance.py::test_g11_f_edge_scope` | `evaluation.py` | resolved | sound | G11 closes |
| G12-a | `test_acceptance.py::test_g12_a_node_retraction` | `evaluation.py` | resolved | sound | G12 closes |
| G12-b | `test_acceptance.py::test_g12_b_route_retraction` | `evaluation.py` | resolved | sound | G12 closes |
| G12-c | `test_acceptance.py::test_g12_c_counter_retraction` | `evaluation.py` | resolved | sound | G12 closes |
| G12-d | `test_acceptance.py::test_g12_d_changed_chain_receipt` | `evaluation.py` | resolved | sound | G12 closes |
| G12-e | `test_acceptance.py::test_g12_e_malformed_snapshot_candidate` | `corpus.py` | resolved | sound | G12 closes |
| G12-f | `test_acceptance.py::test_g12_f_accepted_snapshot_chain` | `corpus.py` | resolved | sound | G12 closes |
| G12-g | `test_acceptance.py::test_g12_g_mapped_oracle` | `evaluation.py` | resolved | sound | G12 closes |
| G12-h | `test_acceptance.py::test_g12_h_split_with_exclusion` | `evaluation.py` | resolved | sound | G12 closes |
| G12-i | `test_acceptance.py::test_g12_i_unchanged_receipt` | `evaluation.py` | resolved | sound | G12 closes |
| G12-j | `test_acceptance.py::test_g12_j_snapshot_root` | `evaluation.py` | resolved | sound | G12 closes |
| G12-k | `test_acceptance.py::test_g12_k_snapshot_history` | `evaluation.py` | resolved | sound | G12 closes |
| G12-l | `test_acceptance.py::test_g12_l_accept_all_refusal_parity` | `evaluation.py` | resolved | sound | G12 closes |
| G13-a | `test_acceptance.py::test_g13_a_policy_validation` | `evaluation.py` | resolved | sound | G13 closes |
| G13-b | `test_acceptance.py::test_g13_b_complete_report` | `evaluation.py` | resolved | sound | G13 closes |
| G13-c | `test_acceptance.py::test_g13_c_early_error` | `evaluation.py` | resolved | sound | G13 closes |
| G13-d | `test_acceptance.py::test_g13_d_late_error` | `evaluation.py` | resolved | sound | G13 closes |
| G13-e | `test_acceptance.py::test_g13_e_late_absence` | `evaluation.py` | resolved | sound | G13 closes |
| G13-f | `test_acceptance.py::test_g13_f_supplied_context` | `evaluation.py` | resolved | sound | G13 closes |
| G13-g | `test_acceptance.py::test_g13_g_pure_incomplete` | `belief.py` | resolved | sound | G13 closes |
| G13-h | `test_acceptance.py::test_g13_h_closure_statement` | `closure.py` | resolved | sound | G13 closes |
| G13-i | `test_acceptance.py::test_g13_i_two_policies` | `world/view.py` | resolved | sound | G13 closes |
| G13-j | `test_acceptance.py::test_g13_j_capture_integrity` | `evaluation.py` | resolved | sound | G13 closes |

## 2. Accounting

**34 arms, 34 declaration units, 4 guarantee rows.** The groups contain
6 G10 units, 6 G11 units, 12 G12 units and 10 G13 units. The recent-cut
inventory contains `(cut45, 45, (34, 34, 4))` and asserts the runner's exact
rows-exercised line. That interface check mocks subprocesses; it is not
discharge evidence.

**G10–G13 close; `belief-acceptance` is discharged.** The roadmap tool
computes **224 of 251 rows closed, 27 open**. No other partial or open row
changes status.

## 3. Checks and dispositions

The eight durable functions cover assessment twins, verification twin edges,
node and route corrections, counters and receipt fidelity, snapshot filtering
and history, completed and incomplete reports, statements and two policies,
and accept-all refusal parity. Honest cases use writers, publication and
registered roots; raw writes and coherent repackaging are confined to labelled
adversarial cases. Portable checks also cover rejected malformed verifications
and ordinary corrections, canonical aliases, once-per-key callback behavior,
raising and non-boolean callbacks, unfiltered closure bytes, and dependencies
in a holder whose evidence is excluded.

Accept-all parity is checked for nine cases: clean, a legitimate counter,
split-corpus disagreement, a coherently corrupt receipt, an accepted malformed
candidate, post-epoch alias drift, post-epoch snapshot root/counter history,
absence, and a bad binding. Values and admission agree; refusals and raised
exception type/message/ref agree. The supplied statement intentionally changes
the digest. An incomplete report has `excluded=()` in every early outcome;
a supplied lineage snapshot supplies the reachable late-absence case. The
wrapper's binding refusal and the pure evaluator's incomplete-context refusal
both carry the specified incomplete report.

Historical declarations and frozen cut bodies are unchanged. The live
sabotages have these explicit retargets:

| owner | retained obligation | live-text change |
|---|---|---|
| cut 18 M1 | verification edge containment | `visited` becomes `verification_targets` after acceptance |
| cut 33 C3-b | world correction coverage | the enumeration call includes `counts` |
| cut 33 BI-5 | receipt fidelity | the original mutation follows the relocated unfiltered branch |
| cut 23 R19e | absent-input answer | the original reason mutation retains the added acceptance report |
| portable G1 | authored assertion inertness | the signature mutation includes the optional statement parameter |

The initial pre-bank audit killed 33 of 34 mutations. G10-e originally omitted
only gather's preflight, while local correction discovery independently checked
the manifest. The declaration now omits selection setup, bypassing both checks;
its baseline resolves and its mutation fails the decisive assertion. This
strengthening occurred before banking `92c9ae7`; no frozen obligation changed.

G12-g uses a real post-epoch deprecated alias and a separate synthetic resolver
primitive for live-id precedence. Corpus admission rejects the direct
live/deprecated collision fixture described in the plan, so such a collision
is not smuggled past integrity admission. The ordinary fold is asserted to use
mapped records and the exact epoch address map; snapshot standing uses the full
capture. Counter-impact receipt waivers use reverse graph reachability, the
same transitive condition specified by C_c(r), without rebuilding that set for
every surviving ref.

## 4. Verification and review

Task 1's focused checks passed 52 tests. Tasks 2–4 passed their separate
94-, 120- and 127-test gates, and shared one implementation commit and fast
gate. Tasks 5–6 passed 47 portable acceptance cases, eight durable cases,
605 regression/inventory checks, the bounded pilot and the complete new guard.
The stable pre-bank fast gate passed **5,994 tests, one skip**, in 81.53 seconds.
The earlier guard-pin failure came from using cut 44's freeze commit instead of
its declaration commit; the pin now names its banked declaration `cac773c`.

One fresh read-only implementation review of `f5a8ac2..92c9ae7` by
`codex/gpt-6-astra` accepted with no Critical or Important findings. Its one
Minor finding was a blank line splitting G10–G13 from the formal-model table;
that formatting is corrected in the final documentation pass. The review did
not rerun tests or judge the pending successor verdict or final status docs.

Final document, roadmap and fast-gate verification is recorded on
`beliefs-c013b0`, followed by `tasks check` and the commit hook. The review
overlapped the fixed-source chain so a blocking repair could be found before
discharge. None was required; final changes are status/accounting documentation
and the one formatting repair. Source and declaration hashes remained unchanged
through the runner verdict.

| tested source at `92c9ae7` | SHA-256 |
|---|---|
| `python/src/beliefs/evaluation.py` | `058f6dd54305471e1c444fe447a2229309bed4c41f9ca43ab96029e98ddd2c1c` |
| `python/src/beliefs/corpus.py` | `e5f41102c73c41ceabd51c97a338a3614ed96edf59c495e982d2b8e7808b065f` |
| `python/src/beliefs/world/view.py` | `3b11438dab62b876868ccf05b85847af0c4d77c0192fc746014cac40bc8d51b2` |
| `python/src/beliefs/belief.py` | `ce65e2e73020ca756c41891e469ede0420031d5cfdf7fb8629a843848d559723` |
| `python/src/beliefs/closure.py` | `40172501bf2ec38002f22c532a067c09e082699dfbf66e9f1df756264ed0701c` |

## 5. Remaining boundary

None for `belief-acceptance`: G10–G13 are discharged. The cut's stated
singleton-holder and supplied-statement limits remain.

L1 remains partial on persistence under `persistence-cut`, and T7 remains partial
on its cross-root case under `cross-root-publication`. The full `contract-cut`,
authority labels, weighted belief and extraction boundaries remain open as the
ledger and roadmap state. This cut neither reads them in full nor re-ranks them.

## 6. Limitations and integration

This cut closes only belief acceptance and G10–G13. The singleton holder rule
remains milestone 1a's boundary; overlapping publications (`beliefs-81367e`)
must revisit the predicate contract. Attribution entries (`beliefs-f50596`)
are next, followed by the bounded N2 preflight pilot (`beliefs-aa9f88`). No
other open limitation is discharged by these checks.

The branch and `.worktrees/acceptance-filter` are retained. This record
establishes branch-local discharge, not main integration or remote publication.
