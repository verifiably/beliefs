# Conformance cut 13 — run confinement, `clean-environment` reachable

**Status:** **Discharged 2026-09-01 at `2f0cedb`** — all 22 frozen units
passed through 35 lettered sabotage arms; the confined arms ran under the
confinement gate, the cut-12 prefix on the certified tuple; the portable
suite reported 2850 passing tests, Ruff was clean and Pyright reported 31
errors confined to test files, disclosed and not corrected (results §2.3).
Results: `../plans/2026-09-01-conformance-cut-13-results.md`. The cut
remains frozen byte-exact at `fa89241`; the specification was promoted to
`2026-08-30-run-confinement-design.md` at banking.

**Sources:** `2026-08-11-conformance-cut-3.md` (§3's "a scratch root is
staging, not confinement"; §4.2's arm split naming every arm deferred to
the confinement-capable boundary policy; its `n2_arms_cut3.py` anchors in
`boundary.py`, `adapter.py`, `recipe.py`, `replay.py` and `verify.py`, all
of which stay in force); `2026-08-29-conformance-cut-12.md` (the acceptance
form this cut inherits: a prefix runner, declared arms, an N2 audit that
errors and never skips); `2026-08-02-computation-reproducibility-design.md`
§4.2c, §4.4b, §4.5, §7.3, §7.3a (the rule text implemented without
amendment); the live **R15**, **R4**, **R9**, **R13**, **R16** and **R21**
rows quoted verbatim below.

## 1. What this cut is

Cut 13 is the frozen acceptance boundary for the run-confinement slice:
the confined boundary policy `boundary-policy/confined-v1` under a closed
capability vocabulary; the per-file runtime artifact closure
(`science.environment.v2`) and its digest-verified snapshot; the
bubblewrap launch gated by a held probe, observed by the boundary from its
own `/proc`; the confined receipt (`science.boundary-receipt.v2`) and run
(`science.run.v2`); `derive_scope`'s `clean-environment` row over a
qualifying receipt; and the total projection `admission_record` from a
derived assessment verification to the record `admit()` reads. **No store
change, no `atoms` or `nodes` change, no workflow surface beyond cut 3's
single-rule adapter, no durable verification publication** (spec §2, §7.2).

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any
unrun arm is **partial**. Cut 12's three practice inheritances stand:
labeled declarations for the design's own rules, one exact once-matching
sabotage per arm, checks naming one test function each.

## 2. The boundary

Inside: everything the spec builds — `beliefs/confinement.py`,
`beliefs/probe.py`, the confined path of `beliefs/boundary.py`, the
closure walk in `beliefs/adapter.py`, the values in `beliefs/recipe.py`,
the receipt variants in `beliefs/runrecord.py`, `qualifies` and the fourth
row in `beliefs/replay.py`, `admission_record` in `beliefs/verify.py`, the
named refusals in `beliefs/errors.py`. The confined arms run under
`tests/acceptance/` behind a **confinement gate** — bubblewrap with
`--info-fd`, user namespaces, the loader's `--list` — that errors and never
skips, and need no durable root. The aggregate runner
`tools/cut13_acceptance.py` runs the cut-12 prefix first and therefore does
need the recertified durable prefix (spec §9.2).

Outside: the workflow surface (R16 and R21's remaining arms), durable
verification publication (a roadmap finding), `shell:` rules under
confinement, immutable materialization (spec §4.4's threat model),
`PYTHONPATH` capture.

## 3. The rows

### 3.1 Rows read, quoted verbatim, with dispositions

| **R15** | Execution is confined to the closure it declared (§4.4b) | Capture the bundle, then **edit a bundled file before execution reads it**; assert the run fails rather than executing modified code under an unchanged `code_identity`. Attempt an **undeclared file read** and an **undeclared network fetch**; assert both fail closed. Assert the receipt names the capabilities actually in force. **Negative:** run under a policy providing fewer capabilities and assert the run is still valid but **cannot reach `clean-environment`** — confinement is graded, not pretended |

**R15 — full**, six units. u1: a bundled file edited after capture and
before the bind yields no run, refusal `closure-mutated`, and the engine
never starts. u2: a bundled file edited after the process exits and before
the post-exit check yields no run, `closure-mutated`. u3: a workflow reading
an undeclared host file fails closed — `execution-failed` under
`confined-v1`, minted under `minimal-v1`. u4: a workflow connecting to a
host listener fails closed the same way. u5: the confined receipt's
`capabilities` are exactly §7.3a's three, observed, with an `instance`;
the minimal receipt's are `()` with none. u6 (the negative): a
`minimal-v1` run is valid and a minimal pair derives `same-environment`,
never `clean-environment`.

| **R4** | Verification scope is derived, and rests on evidence rather than difference | Attempt to author a `scope`; assert refusal. Walk every row of §7.3 including `not-certified`. **Negative (a):** change only the **hostname** between two runs of one recipe and assert the scope stays `same-environment` — no receipt, no `clean-environment`, so a machine name cannot buy admission. **Negative (b):** change only a **comment** in the code and assert `not-certified`, never `independent-implementation`. **Negative (c):** two runs sharing a proposition target but with **different `spec_identity`** assert `not-certified`. **Negative (d):** replay under a `boundary_policy` **missing a required capability** (§7.3a) and assert `same-environment`, never `clean-environment`; assert a policy providing every capability qualifies **whatever its version string**, and that two incomparable policies are not ranked |

**R4 — full**, four units, completing cut 3's walk. u1: the
`clean-environment` row is reached by a confined pair and only through a
qualifying receipt. u2 (negative d): a receipt missing one required
capability derives `same-environment`. u3: a policy providing every
capability qualifies whatever its identity string. u4: two receipts each
missing a different capability are both `same-environment` — containment,
never a ranking.

| **R9** | `inconclusive` never collapses into `passed` or `failed` | Make an output unreadable; assert `inconclusive`, and assert admission does **not** follow. Assert the same for a missing output and a reader error |

**R9 — full**, one unit: a confined pair whose evaluator cannot read an
output derives `inconclusive`, and `admit()` over `admission_record` of
that verification refuses — admission does not follow.

| **R13** | `code_identity` captures what actually ran, not what was committed | Modify an **untracked** file inside `code_roots` and assert `code_identity` changes. Modify a tracked-but-uncommitted file and assert the same. **Negative:** attempt a run whose local import resolves **outside** the bundle and the held environment; assert refusal, not a silently absent member. This tests the capture, which mutating a stored digest does not |

**R13 — full**, one unit: a workflow whose import resolves outside the
bundle and the held environment is refused under `confined-v1` and minted
under `minimal-v1` — a refusal, and nothing about its diagnostic (spec §8).

| **R16** | Non-conformance blocks scope, not just reporting (§4.2, §7.3, §6.2) | Execute two runs with equal recipes, qualifying receipts and **equivalent outputs**, but force one execution's **realized seeds to violate its seed plan**; assert the derived scope is **`not-certified`** and that **nothing is admitted**. Repeat with a job that is **not in the engine-derived trace** for the requested targets, and with a **requested target left unsatisfied** — the two things single-run job-set conformance actually asserts (§6.2). **Negative — no phantom enumeration:** assert a data-dependent replay that legitimately runs a **different job set** over different held inputs is **conforming**, that the difference appears in the **comparison report as a diagnostic**, and that it contributes to **no verdict and no scope**. Assert **no equivalence rule can read an occurrence** — the evaluator's signature is `(result, result)` (§7.2) and admits no job-set argument. **Multi-stream:** run a job whose **family declares two streams**, assert both seeds are recorded under `[job_key][stream_key]`, then omit one and assert **`not-certified`** — not a pass on the strength of the job key being present. Repeat with a realized stream that family does **not** declare. **Per-family:** run a workflow where family A declares `model-initialization` and family B declares `resample-draws`; assert the honest record `{A: [model-initialization], B: [resample-draws]}` **conforms**, and that a record claiming every stream for every job does **not** — pinning that conformance is evaluated against each job's own family and cannot be satisfied by over-claiming. Assert a wildcard instance is judged against its family's declaration. Assert the family declarations are read from the **workflow-definition snapshot**, not the spec, and that the boundary enforces **set equality against `recipe.seed_plan.logical_streams`** in both directions: a family stream with no matching logical stream is refused, **and** a declared logical stream that **no family claims** is refused. Assert this holds for a **`dataset-production`** run, which has no spec — pinning that the rule reads the recipe rather than a member that shape does not carry. **Execution coverage, not just definition coverage:** build a workflow that satisfies the definition equality but whose `resample-draws` family produces **zero jobs** — filtered out, or off the path to the requested target — and assert the run is **non-conforming** and the derived scope is **`not-certified`**, even though every executed job matched its own family vacuously. Assert the conformance result for **both** runs appears in the comparison report, and therefore in the verification's identity |

**R16 — partial**, one unit here: two confined runs with equal recipes and
two qualifying receipts, exactly one non-conforming (spec §7.3's `cores`
mechanism), derive `not-certified`; `admit()` refuses and `belief.evaluate`
returns the same `NoBelief` as without the verification. Every family,
multi-stream, definition-equality and execution-coverage arm stays with
`workflow-surface`.

| **R21** | A recipe says what to execute, and says it portably (§4.2b, §4.2c) | Take one workflow definition with two targets, `analysis` and `report`, and execute each; assert the two runs have **different recipe identities** — pinning that a shared bundle, environment, definition snapshot, inputs, parameters and contract do **not** make them executions of one recipe, and that §7.3 cannot read them as such. Assert a replay boundary given only the recipe **can invoke it**: the entrypoint, the targets and the bindings are all present, the boundary **renders** the engine's configuration from `inputs`, `parameters` and the seed plan, and no caller supplies any of it. **Result manifest (§4.2d):** assert the manifest is **constructed by the boundary** by content-addressing every declared final output, and that there is **no supplied-manifest path**; then assert each of a **missing** declared output, a **duplicate** logical name, an **undeclared** entry, and a digest disagreeing with the bytes on disk mints **no run at all** — not a run marked non-conforming. Assert **intermediates beneath the output root are excluded**, and that a replay leaving different scratch files therefore produces an **equal manifest**. **Negative (a):** vary a scheduling-only option (`-j 8` → `-j 2`) and assert the recipe identity is **unchanged** — the member records what runs, not how fast. **Negative (b) — outputs cannot grant their own authority (§4.2c):** attempt to declare an **absolute** output path, and a boundary-relative one containing traversal that escapes the output root; assert both are **refused**, so a caller cannot place a host location inside the confinement allowlist by naming it. Attempt a write outside the boundary-owned output root and assert it fails closed. **Negative (c) — the host mapping is not identity:** execute one recipe on two hosts whose output roots mount at **different absolute paths**; assert the **recipe identities are equal** and `clean-environment` stays reachable, and that each host's mapping appears only in its **receipt**. **Negative (d) — targets are not a job set:** assert `invocation` does **not** claim to enumerate the jobs a target implies, and that R16's single-run job-set conformance asserts only target satisfaction and trace membership (§6.2). **Negative (e) — the two failure states are distinct:** assert a **complete** closure whose realized seeds violate the plan **does** mint a run and is **non-conforming**, pinning that refusal is for closures that cannot be completed and non-conformance for executions that disobeyed a complete one. |

**R21 — partial**, two units here: u1, negative (b)'s write outside the
output root fails closed (`execution-failed`); u2, negative (c)'s two
differently mounted scratch roots yield equal recipe identities, a
`clean-environment` derivation, and each host mapping only in its receipt.
The two-target arm and negative (d) stay with `workflow-surface`.

### 3.2 Rows not read

Every other row. R2, R20 and R23's workflow arms are `workflow-surface`'s;
no R row's store, audit or import arm is touched.

### 3.3 Labeled declarations

Seven, for the spec's own rules, none a guarantee row:

- **K1** — the policy match is the entire definition: identity, scope
  rule, and unique capability set; a duplicate capability is unspellable.
- **K2** — an existing mismatching snapshot refuses and is never rebuilt;
  a concurrent winner is verified, reused when it matches, refused when
  not.
- **K3** — a confined receipt whose `mount_plan_identity` disagrees with
  its own canonical mounts is malformed; the three confined members are
  all present or all absent.
- **K4** — the minimal receipt projection is byte-stable under
  `science.boundary-receipt.v1`; a confined receipt makes a
  `science.run.v2` run, in both `RunClosure.address()` and the wire
  recomputation.
- **K5** — `admission_record` is total over `AssessmentVerification`,
  carries `supersedes`, and refuses a `DatasetProductionVerification`.
- **K6** — the gate refuses a namespace equal to the parent's, a canonical
  mount table unequal to the plan, an environment unequal to the declared
  set, a routable network, and a loader map unequal to the capture.
- **K7** — a SONAME collision, a symlink escaping the closure, and a mixed
  `.pth` are each `ClosureUnsupported`.

## 4. Accounting

Six rows read: **4 full** (R15, R4, R9, R13), **2 partial** (R16, R21,
their `workflow-surface` arms restated). Selected units: R15 6, R4 4, R9 1,
R13 1, R16 1, R21 2 — **15 selected + 7 labeled = 22 declaration units**.

## 5. N2 obligations

1. **Host-side sabotage only**: the sandbox's `beliefs` tree is the
   closure's own copy, so a sabotage of `probe.py` would not reach it;
   every arm mutates `boundary.py`, `confinement.py`, `adapter.py`,
   `recipe.py`, `replay.py`, `verify.py` or `runrecord.py`.
2. **The mutation arms** (R15u1, u2) interpose at named seams —
   `beliefs.boundary.capture_bundle` and `beliefs.boundary.launch_confined`
   — deterministically; u1 additionally asserts the launch seam was never
   entered.
3. **The fail-closed arms** (R15u3, u4, R21u1) assert the reason is
   exactly `execution-failed`, so a sabotage that widens the sandbox is
   caught by the gate's `confinement-not-established` rather than passing.
   R13u1 asserts a refusal only (spec §8); its sabotage routes the confined
   request through the minimal path, where the outside module is reachable
   and the run mints.
4. **The network arm** (R15u4) listens on the host's loopback in the test
   process; the workflow connects to that port.
5. **R16u1** executes at `cores=1` and replays at `cores=2`; the fixture
   workflow records the planned seed plus one when `workflow.cores != 1`.
6. **The confined arms need no durable root** and run under `tmp_path`;
   the gate fixture errors, never skips.

## 6. Freeze obligations

Five: **the minimal path is byte-unchanged** except for the `boundary_policy`
parameter, the v2 environment manifest, and the closure walk replacing
`capture_environment`'s body — every cut-3 anchor listed in the plan's
Global Constraints still matches exactly once; **receipt capabilities are
never copied from the requested policy** — they are the set the launch
observed; **the probe gates the engine's own process**; **snapshots are
never deleted by the boundary**; **`science.run.v1` records decode
unchanged** — the wire validator accepts both receipt shapes and recomputes
each under the domain its shape names.

## 7. Second reader

The charge, unchanged from cut 12 §7: verify every quoted row byte-exact
against its source table as of the freeze commit; audit each selection
against §2's boundary; audit each disposition against the selection rule,
with any unrun arm forcing partial; record findings for amendment before
the freeze.

## 8. Limitations

1. **Host-side mutation between the two observations is not detected**
   (spec §4.4): the host and boundary owner are trusted.
2. **`shell:` rules fail closed** under `confined-v1`; no shell is in the
   closure.
3. **Snapshot races** are covered by atomic publication and the loser rule,
   not by a test that races two runs.
4. **`PYTHONPATH` is not captured.**
5. **The probe's descriptor closing** (spec §6.1 step 4) is not
   sabotage-checked, for §5 item 1's reason, and cannot be observed from
   inside a sandbox without `/proc`; it stands on the probe's code, which
   closes both descriptors through `os.fdopen` context managers before
   `execve`.
