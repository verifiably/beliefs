# Run confinement — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `clean-environment` reachable — a confined boundary policy that executes a run inside a fresh namespaced materialization of a digest-verified runtime closure, a receipt that observes that construction, `derive_scope`'s fourth row, the value-level join from a derived verification to admission, and conformance cut 13 with its discharge and banking.

**Architecture:** Documentation-first (the spec is amended with the spike's findings and cut 13 freezes before any implementation commit), then production changes in dependency order — the named refusals (`errors.py`), the values (`recipe.py`: closed capability vocabulary, the two exact policies, `science.environment.v2`, `science.boundary-receipt.v2`, `science.run.v2`, the instance attestation), the wire codec (`runrecord.py`), the per-file closure walk (`adapter.py`), the new `confinement.py` (snapshot, mount plan, probe-gated bubblewrap launch, boundary-side observation) with its in-sandbox `probe.py`, the boundary's confined path (`boundary.py`, `replay.py`), the scope row and admission join (`replay.py`, `verify.py`) — then the acceptance layer, discharge, and banking.

**Tech Stack:** Python 3.13 via `uv run` from `python/`; pytest; ruff; pyright; bubblewrap 0.12 (`bwrap`) with unprivileged user namespaces; glibc's dynamic loader (`ld.so --list`); Snakemake 8.11.4 (`--force-use-threads` executes `run:` rules in-process). No `atoms` or `nodes` change.

**Spec:** `docs/superpowers/specs/2026-08-30-run-confinement-design.md` — read it first; Task 1 amends it with what the spike established. Inherited authority: `docs/designs/2026-08-02-computation-reproducibility-design.md` §4.2c, §4.4b, §4.5, §7.3, §7.3a. Cut form: `docs/designs/2026-08-29-conformance-cut-12.md`.

## Global Constraints

- Work in this worktree on branch `design/run-confinement`; paths are relative to the worktree root unless a command says `cd python`. The sibling checkouts resolve through `.worktrees/design/{atoms,nodes}` symlinks already in place.
- **No atoms or nodes change.**
- **Prior cuts' sabotage anchors must still occur exactly once** in every module this plan edits. The ones at risk, and the rule each imposes:
  - `boundary.py`: `        config = _render_config(recipe, definition)\n` (8 spaces — the confined path spells it at 4), `        realized_seeds = read_realized_seeds(scratch)\n` (the confined path reads `output_root`), `    if type(spec) is not FrozenSpec:`, `    intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)`, `    intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)`, `    registration = Registration(token, report.identity()) if intent is not None else None`, `    spec: object,\n    port: OperationPort,`, `def execute_production_run(\n    *,\n    inputs: tuple[RecipeInput, ...],\n    port: OperationPort,`, `        result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)`, `refused = _refused("no-frozen-spec", subject, actor, observer, started_at)\n        port.execute(_report_plan(refused.report))`, `    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) for name in declared_outputs))`, `        if _digest(_output_path(scratch, name)) != expected:`, `    if any(_is_acquisition(address) for address in addresses):`. So: `boundary_policy` is inserted **after** `port` in both signatures; `_refused` keeps its positional parameters and gains `detail` as a trailing keyword; `_execute_confined` never repeats a minimal-path line at the same indentation.
  - `adapter.py`: `            rows.append((name, _file_digest(target)))` (only in `capture_bundle`), `        if target.startswith("-"):`.
  - `recipe.py`: `    receipt: BoundaryReceipt\n` (only `Occurrence`), `        "rendered_config": _pairs(receipt.rendered_config),\n` (once, in `_receipt_projection`), `                "occurrence": _occurrence_projection(self.occurrence),\n`, `        if type(self.environment) is not EnvironmentManifest:`, `    boundary_policy: BoundaryPolicy,\n) -> Recipe:`, `    declared_outputs: tuple[str, ...]\n\n    def __post_init__`, the `"boundary_policy": {…}` projection block.
  - `replay.py`: `        return "same-environment"` (8 spaces, once — the new row keeps that literal line), `        return "independent-implementation"\n    return "not-certified"`, `    recipe = run.recipe\n`, `            if actual != expected:`.
  - `verify.py`: `    "build_verification",\n]` (add `"admission_record"` **before** it in `__all__`), `    return _mint_verification(assessment=assessment, supersedes=None, **common)`.
  - `runrecord.py`: `if node.id != run_ref(address):`, `_mapping(parsed, {"recipe", "result", "occurrence"}, "$")`, `if _reproject(parsed) != parsed:\n        _refuse("$", "an array the projection sorts is out of its canonical order")`.
  - `errors.py`: `        self.reason = reason\n        self.ref = ref` (only `AdmissionEvidenceRefused` — the new errors carry `reason` as a class attribute).
  After every task: `cd python && set -o pipefail && uv run pytest tests/test_n2.py -k "stale" | tail -1` must pass (it audits cuts 1–3 live).
- **Byte-mutation primitives** (`tests/test_capability_boundary.py`): `confinement.py` may name exactly `copy2`, `write_text`, `symlink_to`, `rename`, `rmtree`; `probe.py` exactly `touch`, `unlink` — its one write check uses inventoried operations so the equality allowlist weighs it as the fourth surface, never a raw `os.open` the inventory cannot see. `adapter.py` stays at `{copy2}`, `boundary.py` at `{copy2, write_text}`.
- **Stable reasons**: `confinement-unavailable`, `boundary-policy-unsupported`, `closure-unsupported`, `snapshot-mismatch`, `closure-mutated`, `confinement-not-established`, plus the unchanged `execution-failed`.
- **Sandbox constants**: `/science/env`, `/science/env/python`, `/science/env/site`, `/science/env/path`, `/science/env/lib`, `/science/env/venv`, `/science/bundle`, `/science/out`, `/science/out/inputs`; hostname `science`; devices `/dev/null`, `/dev/urandom`.
- **Explicit sandbox environment**, exactly: `PATH=/science/env/venv/bin`, `LD_LIBRARY_PATH=/science/env/lib`, `HOME=/science/out/.home`, `PWD=/science/out`, `LC_CTYPE=C.UTF-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`, `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`, `SCIENCE_TRACE_FILE=/science/out/.trace/events.jsonl`.
- Pytest: `addopts` sets `-q`; run `cd python && set -o pipefail && uv run pytest tests/<file> | tail -3`. Lint: `uv run ruff check <paths> && uv run pyright <paths> | tail -1`. Acceptance modules are excluded from the ordinary run; run them by path.
- Conventional commits, no AI-attribution trailer. Every commit leaves the touched test files green.
- Curation rules bind: frozen cut bodies, plans, execution ledgers and results records are never edited after the fact; a design's `**Status:**` is corrected in the same change that lands its work.
- The **144 baseline failures** on this host are the ext4 durability allowlist refusing on kernel 7.1.11 (atoms `dd658ac` certified 7.1.10). They are not this slice's; nothing here touches them. The portable count to compare against is the cut-12 figure less those refusals, and Task 10 reports whatever the summary line says.

---

### Task 1: Amend the spec, freeze conformance cut 13, open the ledger

**Files:**
- Modify: `docs/superpowers/specs/2026-08-30-run-confinement-design.md` (§4.2, §4.3, §5.1, §5.4, §5.5, §6.1, §6.2, §9.3)
- Create: `docs/designs/2026-08-30-conformance-cut-13.md`
- Create: `docs/plans/2026-08-30-run-confinement-ledger.md`
- Modify: `README.md` (the design table, its count sentence)
- Modify: `python/tests/test_designs_corpus.py` (`_COUNT_WORDS`, only if 41 is missing)
- Modify: `docs/guide/contracts-and-adoption.md` (front matter `sources:`, `updated`)

**Interfaces:**
- Produces: the frozen unit ids Task 9 declares arms against (`R15u1`–`R15u6`, `R4u1`–`R4u4`, `R9u1`, `R13u1`, `R16u1`, `R21u1`–`R21u2`, `K1`–`K7`); the freeze commit hash Task 9 pins as `CUT13_FREEZE_COMMIT`.

- [ ] **Step 1: Amend the spec with the spike's findings**

The spike (bubblewrap 0.12, Snakemake 8.11.4, this host) established five facts the spec did not have. Edit the spec — it is not frozen — so the cut can cite it exactly:

1. In §4.2's `.pth` row, append: `A RECORD entry ending in .pth is skipped by the RECORD walk and handled here. For an import-only .pth, each imported top-level module must be a closure member; a site-packages module the file names that no RECORD lists (this host's _virtualenv.py, written by uv) is captured as /science/env/site/<name>.py; a named module absent from site-packages is ClosureUnsupported.`
2. In §4.3, after "creating exactly the manifested symlinks", append: `The snapshot also holds the rendered rows of §5.2 — pyvenv.cfg, the venv symlinks, the rewritten .pth files — because each is a pure function of the manifest, so the whole of /science/env is one read-only bind. Verification checks manifested rows by digest and rendered rows by expected content, and refuses any other file.`
3. In §5.1, replace the seven `/science/env/...` rows with two: `| <PT_INTERP> | the loader, at the path the interpreter's ELF header names, from the snapshot | ro-bind |` and `| /science/env/ | the snapshot: interpreter prefix, site-packages, .pth trees, native libraries under lib/, and the rendered venv | ro-bind |`. Add a sentence after the table: `PYTHONPATH is not part of the closure and is cleared; a module reachable on the host only through it is not reachable in the sandbox (a limitation, §9.3).`
4. In §5.4, add to the environment listing `HOME=/science/out/.home`, `PWD=/science/out`, `LC_CTYPE=C.UTF-8`, with: `bubblewrap sets PWD to the --chdir target and CPython's locale coercion sets LC_CTYPE=C.UTF-8 when it is unset, so both are declared explicitly and exact equality holds; HOME is declared because with it unset Snakemake expands ~ to a literal directory under the working directory.`
5. In §5.5, after `--cores <n>`, insert `--force-use-threads`, with: `Snakemake 8's local executor otherwise spawns every run: job as a fresh python -m snakemake through /bin/sh (shell=True); in-process execution keeps the closure shell-free. The minimal policy's argv is byte-unchanged.`
6. In §6.1 step 1, replace "with two inherited descriptors" by "with two inherited descriptors named on its own argv (`--report-fd`, `--go-fd`, never the environment)".
7. In §6.2's network row, replace the check text with: `an IPv4 connect to a non-loopback documentation address (192.0.2.1) fails with ENETUNREACH; an IPv6 socket either cannot be created (EAFNOSUPPORT) or its connect to 2001:db8::1 fails unreachable. Loopback is not evidence — the sandbox owns its own lo. DNS failure is not evidence and is not checked.`
8. In §9.3, add: `- An N2 sabotage of probe.py does not reach the sandbox, whose science tree is the closure's own copy; every cut-13 arm sabotages host-side code.` and `- PYTHONPATH is not captured (§5.1).`
9. In §4.2, after the sentence beginning "`PT_INTERP`, the Python version directory name", add: `Every symlink row's target is itself part of the closure — a file row, a symlink row, or a directory some row lies under — and is captured when the link is; a relative target that stays under the link's own root keeps its relative text, any other in-closure target is rewritten to the target's sandbox path, and a target outside every root is ClosureUnsupported. sys.executable is followed link by link (add_chain): each link a symlink row, the terminal binary the interpreter row. Every sandbox path is normalized — absolute, no ., .. or empty components — and the manifest refuses any other spelling, so a snapshot join can never leave the snapshot.` In §5.2's first bullet, replace "`/science/env/venv/bin/python` → the base interpreter;" with "`/science/env/venv/bin/python` → the base interpreter, rendered only when the interpreter's symlink chain did not already capture that path as a manifest row;".
10. In §5.3, append: `The host listing runs the loader under an empty environment — no ambient LD_LIBRARY_PATH or LD_PRELOAD — and the capture retains the expected map as rows (ELF sandbox path, SONAME, resolved sandbox path) over every loadable ELF (ET_EXEC or ET_DYN) under /science/env, closed to a fixpoint over the libraries it adds. The probe lists the same set in-layout and the boundary requires its report to equal the map exactly: the same ELFs, the same SONAMEs per ELF, the same resolved path, the manifest's digest; a nonzero loader exit, an unresolved or unparsable line, an omitted or extra entry each refuse.` Replace §6.2's loader row check text with: `the in-layout ld.so --list of every loadable ELF under /science/env reports, per ELF, its exit status and each SONAME's resolved path and digest; the boundary requires equality with the captured map (§5.3)`.
11. In §6.1 step 3, after "no `rw` where `ro` was planned", add: `Canonical rows preserve multiplicity — a stacked or duplicate mount is a row of its own and fails equality — and each observed mountpoint is classified into its planned role, an unplanned one taking the role unplanned; the receipt's instance carries these observed rows, never the plan's.` In §8, replace the `ConfinementUnavailable` row's stage text "pre-intent" with "pre-intent only", and append to the `ConfinementNotEstablished` row's "when" cell: `; any launch or protocol failure after intent — bubblewrap gone, an unstartable process, malformed info or report, a closed descriptor — with the child terminated and reaped and every descriptor closed on every failure path`.
12. In §10, add a bullet after the `RAW_WRITE_ALLOWLIST` one: `science/probe.py is the fourth raw-write surface, {touch, unlink}: its one write check touches and removes a file under the output root with inventoried operations, so the equality allowlist weighs it rather than a raw os.open escaping the inventory.` In §6.2's filesystem row, replace "succeeds and is removed" with "succeeds (Path.touch) and is removed (unlink)".
13. In §4.4's cost paragraph, replace the first sentence with: `A cache hit costs three full digest passes over the closure — the host capture, the snapshot verification materialize_snapshot performs (the pre-bind observation), and the post-exit check — against today's two (capture and require_executing_environment); the confined path does not call require_executing_environment, because the recipe's manifest is that single capture by construction, and no other pass over the snapshot exists.` In §5.6 step 3, replace "pre-bind integrity (§4.4)" with "pre-bind integrity (§4.4: the bundle's fold and the staged inputs' fingerprint; the snapshot's pass is the get-or-build verification)".
14. In §3, after the sentence stating the match is over the entire definition, add: `The capability member is compared as a set — frozenset(capabilities) — and the boundary carries on with the canonical known value, so a reordered spelling of a known set is recorded as the definition it names.`

```bash
git add docs/superpowers/specs/2026-08-30-run-confinement-design.md
git commit -m "docs(specs): amend the run-confinement design with the sandbox spike's findings"
```

- [ ] **Step 2: Write the cut document**

Write `docs/designs/2026-08-30-conformance-cut-13.md`. The six quoted rows are byte-exact copies of the R table at `4d29bc2`: before committing, re-copy each with `grep -E '^\| \*\*R(15|4|9|13|16|21)\*\* \|' docs/designs/2026-08-02-computation-reproducibility-design.md` and paste the grep output verbatim in place of the six `| … |` lines below.

````markdown
# Conformance cut 13 — run confinement, `clean-environment` reachable

**Status:** frozen 2026-08-30, before implementation. Source specification:
`docs/superpowers/specs/2026-08-30-run-confinement-design.md` (cited as
*spec*), promoted to `docs/designs/` at banking.

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

Inside: everything the spec builds — `science/confinement.py`,
`science/probe.py`, the confined path of `science/boundary.py`, the
closure walk in `science/adapter.py`, the values in `science/recipe.py`,
the receipt variants in `science/runrecord.py`, `qualifies` and the fourth
row in `science/replay.py`, `admission_record` in `science/verify.py`, the
named refusals in `science/errors.py`. The confined arms run under
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

| … |

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

| … |

**R4 — full**, four units, completing cut 3's walk. u1: the
`clean-environment` row is reached by a confined pair and only through a
qualifying receipt. u2 (negative d): a receipt missing one required
capability derives `same-environment`. u3: a policy providing every
capability qualifies whatever its identity string. u4: two receipts each
missing a different capability are both `same-environment` — containment,
never a ranking.

| … |

**R9 — full**, one unit: a confined pair whose evaluator cannot read an
output derives `inconclusive`, and `admit()` over `admission_record` of
that verification refuses — admission does not follow.

| … |

**R13 — full**, one unit: a workflow whose import resolves outside the
bundle and the held environment is refused under `confined-v1` and minted
under `minimal-v1` — a refusal, and nothing about its diagnostic (spec §8).

| … |

**R16 — partial**, one unit here: two confined runs with equal recipes and
two qualifying receipts, exactly one non-conforming (spec §7.3's `cores`
mechanism), derive `not-certified`; `admit()` refuses and `belief.evaluate`
returns the same `NoBelief` as without the verification. Every family,
multi-stream, definition-equality and execution-coverage arm stays with
`workflow-surface`.

| … |

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

1. **Host-side sabotage only**: the sandbox's `science` tree is the
   closure's own copy, so a sabotage of `probe.py` would not reach it;
   every arm mutates `boundary.py`, `confinement.py`, `adapter.py`,
   `recipe.py`, `replay.py`, `verify.py` or `runrecord.py`.
2. **The mutation arms** (R15u1, u2) interpose at named seams —
   `science.boundary.capture_bundle` and `science.boundary.launch_confined`
   — deterministically; u1 additionally asserts the launch seam was never
   entered.
3. **The fail-closed arms** (R15u3, u4, R21u1) assert the reason is
   exactly `execution-failed`, so a sabotage that widens the sandbox is
   caught by the gate's `confinement-not-established` rather than passing.
   R13u1 asserts a refusal only (spec §8); its sabotage makes the boundary
   mint a failed execution.
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
````

- [ ] **Step 3: Open the execution ledger**

`docs/plans/2026-08-30-run-confinement-ledger.md`:

```markdown
# Run-confinement slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-30-run-confinement.md`
Specification: `docs/superpowers/specs/2026-08-30-run-confinement-design.md`
Frozen cut: `docs/designs/2026-08-30-conformance-cut-13.md`
Freeze hash: <filled in Step 5>

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the host's confinement substrate is a prerequisite, not a
   dependency.** bubblewrap 0.12 with `--info-fd`, unprivileged user
   namespaces, and glibc's `ld.so --list` are checked before intent and
   refused pre-intent when absent; nothing under `/usr` is edited or
   vendored.
2. **R2 — the ext4 recertification on kernel 7.1.11 is a discharge
   prerequisite of the aggregate runner only.** The confined arms run under
   `tmp_path`; the cut-12 prefix needs the certified tuple. No atoms change
   ships in this branch.
```

- [ ] **Step 4: README, design count, guide sources**

Add to README's design table after the cut-12 row:

```markdown
| `2026-08-30-conformance-cut-13.md` | the thirteenth frozen conformance cut, selecting run confinement: 4 rows full, 2 part, with 15 selected and 7 labeled declarations; `clean-environment` reachable |
```

Change `Forty documents` to `Forty-one documents`. In `python/tests/test_designs_corpus.py`, if `_COUNT_WORDS` lacks `41`, add `    41: "Forty-one",`. Add `  - ../designs/2026-08-30-conformance-cut-13.md` to `docs/guide/contracts-and-adoption.md`'s `sources:` (after the cut-12 line) and set its `updated: 2026-08-30`.

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1 && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK
```

Expected: all passed; `CHECK_GUIDE_OK`.

- [ ] **Step 5: Commit the freeze and pin its hash**

```bash
git add docs/designs/2026-08-30-conformance-cut-13.md docs/plans/2026-08-30-run-confinement-ledger.md README.md python/tests/test_designs_corpus.py docs/guide/contracts-and-adoption.md
git commit -m "docs(designs): freeze conformance cut 13, run confinement"
git log --oneline -1
```

Then write the short hash into the ledger's `Freeze hash:` line and commit `docs(plans): pin cut 13's freeze hash`.

---

### Task 2: The named refusals and `RunRefused.detail`

**Files:**
- Modify: `python/src/science/errors.py` (append after `UnsafeInvocation`)
- Modify: `python/src/science/boundary.py:100-107` (`RunRefused`)
- Test: `python/tests/test_confinement_errors.py`

**Interfaces:**
- Produces: `ConfinementRefusal` (base, no `reason`), `ConfinementUnavailable`, `BoundaryPolicyUnsupported`, `ClosureUnsupported`, `SnapshotMismatch`, `ClosureMutated`, `ConfinementNotEstablished` (each with class attribute `reason: str`), `NotAnAssessmentVerification(RecordError)`; `RunRefused.detail: str = ""`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_confinement_errors.py`:

```python
"""The confined boundary's refusals carry stable reasons; the message is diagnostic."""

from science.boundary import RunRefused
from science.errors import (
    BoundaryPolicyUnsupported,
    ClosureMutated,
    ClosureUnsupported,
    ConfinementNotEstablished,
    ConfinementRefusal,
    ConfinementUnavailable,
    NotAnAssessmentVerification,
    RecordError,
    ScienceError,
    SnapshotMismatch,
)

REFUSALS = (
    ConfinementUnavailable,
    BoundaryPolicyUnsupported,
    ClosureUnsupported,
    SnapshotMismatch,
    ClosureMutated,
    ConfinementNotEstablished,
)


def test_every_confinement_refusal_carries_a_distinct_stable_reason():
    assert [cls.reason for cls in REFUSALS] == [
        "confinement-unavailable",
        "boundary-policy-unsupported",
        "closure-unsupported",
        "snapshot-mismatch",
        "closure-mutated",
        "confinement-not-established",
    ]
    assert all(issubclass(cls, ConfinementRefusal) for cls in REFUSALS)
    assert issubclass(ConfinementRefusal, ScienceError)
    assert "reason" not in vars(ConfinementRefusal)


def test_the_message_is_diagnostic_and_never_the_reason():
    error = ClosureMutated("bundle fingerprint moved between the bind and exit")
    assert error.reason == "closure-mutated"
    assert str(error) == "bundle fingerprint moved between the bind and exit"


def test_not_an_assessment_verification_is_a_record_error():
    assert issubclass(NotAnAssessmentVerification, RecordError)


def test_run_refused_carries_an_in_memory_detail_defaulting_to_empty():
    refused = RunRefused("closure-mutated", None, None, None)
    assert refused.detail == ""
    detailed = RunRefused("closure-mutated", None, None, None, detail="bundle moved")
    assert detailed.detail == "bundle moved"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_confinement_errors.py | tail -3`
Expected: FAIL — `ImportError: cannot import name 'ConfinementRefusal'`.

- [ ] **Step 3: Implement**

Append to `python/src/science/errors.py` directly after the `UnsafeInvocation` class:

```python
class ConfinementRefusal(ScienceError):
    """Base of the confined boundary's refusals (run-confinement design §8).

    Each subclass carries a stable ``reason`` as a class attribute; the run
    boundary maps it into ``RunRefused.reason`` and keeps the message as the
    in-memory diagnostic. The base carries no reason: a refusal without one is
    not a confinement refusal."""


class ConfinementUnavailable(ConfinementRefusal):
    """Pre-intent: bubblewrap absent or without ``--info-fd``, user namespaces
    disabled, or the loader's ``--list`` not callable on this host."""

    reason = "confinement-unavailable"


class BoundaryPolicyUnsupported(ConfinementRefusal):
    """Pre-intent: the supplied policy matches neither known definition on
    identity, scope rule and unique capability set together — a request
    failure, not an unavailable host."""

    reason = "boundary-policy-unsupported"


class ClosureUnsupported(ConfinementRefusal):
    """Post-intent: the runtime closure cannot be laid out — a SONAME
    collision, a symlink escaping the closure, an unfollowable or mixed
    ``.pth`` line, a non-ELF program interpreter, an unlistable artifact."""

    reason = "closure-unsupported"


class SnapshotMismatch(ConfinementRefusal):
    """Post-intent: an existing, freshly built, or concurrently published
    snapshot disagrees with the manifest. Never rebuilt — a corrupt shared
    snapshot is evidence, not a cache miss."""

    reason = "snapshot-mismatch"


class ClosureMutated(ConfinementRefusal):
    """Post-intent: the bundle, the snapshot or the staged inputs differ
    between the pre-bind and post-exit observations (design §4.4)."""

    reason = "closure-mutated"


class ConfinementNotEstablished(ConfinementRefusal):
    """Post-intent: a namespace equal to the parent's, a canonical mount
    table unequal to the plan, a probe check that failed, or a probe that
    never reported READY. The requested policy cannot be honestly executed."""

    reason = "confinement-not-established"


class NotAnAssessmentVerification(RecordError):
    """``admission_record`` was offered a dataset-production verification,
    which has no assessment to admit (design §7.2)."""
```

In `python/src/science/boundary.py`, change `RunRefused` to:

```python
@sealed
@final
@dataclass(frozen=True)
class RunRefused:
    reason: str
    report: ActReport | None
    intent: AssessmentRunIntent | OperationIntent | None
    registration: Registration | None
    detail: str = ""
    """In-memory only: the refusing error's message. The durable ``RunRefusal``
    and the act-report carry the stable reason alone (design §8)."""
```

- [ ] **Step 4: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_confinement_errors.py tests/test_boundary.py | tail -1 && uv run ruff check src/science/errors.py src/science/boundary.py && uv run pyright src/science/errors.py | tail -1`
Expected: all passed; clean; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/errors.py python/src/science/boundary.py python/tests/test_confinement_errors.py
git commit -m "feat(errors): name the confined boundary's refusals with stable reasons"
```

---

### Task 3: The values — vocabulary, policies, the instance attestation, receipt and run domains

**Files:**
- Modify: `python/src/science/recipe.py` (constants at 46–53; `BoundaryPolicy` 197–208; `BoundaryReceipt` 390–406; `_receipt_projection` 452–458; `RunClosure.address` 495–503; `__all__`). **Not** `EnvironmentManifest`: its v2 row shape lands with the capture that produces it, in Task 5, so every commit boundary stays green.
- Create: `python/tests/confinement_fixtures.py`
- Test: `python/tests/test_confinement_values.py`

**Interfaces:**
- Produces (all in `science.recipe`): `CAPABILITIES`, `REQUIRED_FOR_CLEAN_ENVIRONMENT`, `RENDERED_KINDS`, `NAMESPACES`, `MOUNT_ACCESS`, `CONFINED_RECEIPT_DOMAIN`, `CONFINED_RUN_DOMAIN`, `MOUNT_PLAN_DOMAIN`; `MINIMAL_POLICY`, `CONFINED_POLICY`, `SUPPORTED_POLICIES`, `supported_policy(policy) -> BoundaryPolicy` (the canonical known value, matched on identity, scope rule and capability *set*); `mount_plan_identity(mounts) -> str`; `InstanceAttestation(namespaces, mounts, mount_plan_identity, environment_identity)`; `BoundaryReceipt(..., instance=None, rendered_environment=None, mounts=None)` with `.confined`; `run_domain_for(confined: bool) -> str`; `_triples(rows)`.
- Consumes: `BoundaryPolicyUnsupported` (Task 2).

- [ ] **Step 1: Write the failing tests**

`python/tests/confinement_fixtures.py`:

```python
"""Confined-receipt value builders for the portable suite."""

from fixtures_cut3 import closure, occurrence

from science.recipe import (
    CAPABILITIES,
    NAMESPACES,
    BoundaryReceipt,
    InstanceAttestation,
    mount_plan_identity,
)

ENV_IDENTITY = "sha256:" + "ab" * 32

MOUNTS = (
    ("/", "root", "ro"),
    ("/lib64/ld-linux-x86-64.so.2", "loader", "ro"),
    ("/science/env", "env", "ro"),
    ("/science/bundle", "bundle", "ro"),
    ("/science/out", "output", "rw"),
    ("/science/out/inputs", "inputs", "ro"),
    ("/dev/null", "device", "rw"),
    ("/dev/urandom", "device", "rw"),
)


def instance(**overrides) -> InstanceAttestation:
    fields = {
        "namespaces": NAMESPACES,
        "mounts": MOUNTS,
        "mount_plan_identity": mount_plan_identity(MOUNTS),
        "environment_identity": ENV_IDENTITY,
    }
    fields.update(overrides)
    return InstanceAttestation(**fields)


def confined_receipt(**overrides) -> BoundaryReceipt:
    fields = {
        "scratch_mapping": "/host/scratch/run-1",
        "argv": ("/science/env/venv/bin/python", "-m", "snakemake"),
        "rendered_config": (("seed_model_initialization", "7"),),
        "capabilities": CAPABILITIES,
        "instance": instance(),
        "rendered_environment": (("env:PATH", "value", "/science/env/venv/bin"), ("hostname", "value", "science")),
        "mounts": (("/science/bundle", "/host/scratch/run-1/bundle"), ("/science/out", "/host/scratch/run-1/out")),
    }
    fields.update(overrides)
    return BoundaryReceipt(**fields)


def confined_closure(**overrides):
    return closure(occurrence=occurrence(receipt=confined_receipt(**overrides)))
```

`python/tests/test_confinement_values.py`:

```python
"""The run-confinement values: the closed vocabulary, the two exact policies,
science.environment.v2, the instance attestation, and the receipt and run
domains (design §3, §4.1, §6.3)."""

import dataclasses

import pytest
from confinement_fixtures import ENV_IDENTITY, MOUNTS, confined_closure, confined_receipt, instance
from fixtures_cut3 import closure, occurrence

from science.errors import BoundaryPolicyUnsupported, MalformedClosure
from science.identity import v1
from science.recipe import (
    BOUNDARY_RECEIPT_DOMAIN,
    CAPABILITIES,
    CONFINED_POLICY,
    CONFINED_RECEIPT_DOMAIN,
    CONFINED_RUN_DOMAIN,
    MINIMAL_POLICY,
    NAMESPACES,
    REQUIRED_FOR_CLEAN_ENVIRONMENT,
    RUN_DOMAIN,
    SUPPORTED_POLICIES,
    BoundaryPolicy,
    BoundaryReceipt,
    InstanceAttestation,
    _occurrence_projection,
    _receipt_projection,
    mount_plan_identity,
    run_domain_for,
    supported_policy,
)


# --- K1: the vocabulary and the two exact policies ----------------------------
def test_the_vocabulary_is_closed_and_the_requirement_is_its_own_explicit_tuple():
    assert CAPABILITIES == ("from-bundle", "closure-confined-filesystem", "network-denied")
    assert REQUIRED_FOR_CLEAN_ENVIRONMENT == CAPABILITIES
    assert REQUIRED_FOR_CLEAN_ENVIRONMENT is not CAPABILITIES
    with pytest.raises(MalformedClosure):
        BoundaryPolicy(identity="p", scope_rule="scope-derivation/v1", capabilities=("teleportation",))


def test_k1_a_duplicate_capability_is_unspellable():
    with pytest.raises(MalformedClosure):
        BoundaryPolicy(identity="p", scope_rule="scope-derivation/v1", capabilities=("from-bundle", "from-bundle"))


def test_k1_the_two_known_definitions_are_exact():
    assert MINIMAL_POLICY == BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")
    assert CONFINED_POLICY.capabilities == CAPABILITIES
    assert SUPPORTED_POLICIES == (MINIMAL_POLICY, CONFINED_POLICY)
    assert supported_policy(MINIMAL_POLICY) is MINIMAL_POLICY
    assert supported_policy(BoundaryPolicy(**dataclasses.asdict(CONFINED_POLICY))) == CONFINED_POLICY


def test_k1_a_known_identity_with_another_scope_rule_is_unsupported():
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(CONFINED_POLICY, scope_rule="scope-derivation/v2"))


def test_k1_a_reordered_spelling_of_a_known_capability_set_is_that_definition():
    reordered = BoundaryPolicy(
        identity=CONFINED_POLICY.identity,
        scope_rule=CONFINED_POLICY.scope_rule,
        capabilities=tuple(reversed(CAPABILITIES)),
    )
    assert reordered != CONFINED_POLICY
    assert supported_policy(reordered) is CONFINED_POLICY


def test_k1_a_known_identity_with_fewer_capabilities_is_unsupported():
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(CONFINED_POLICY, capabilities=CAPABILITIES[:2]))
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy(dataclasses.replace(MINIMAL_POLICY, capabilities=("network-denied",)))
    with pytest.raises(BoundaryPolicyUnsupported):
        supported_policy("boundary-policy/confined-v1")


# --- K3: the instance attestation ---------------------------------------------
def test_k3_a_mount_plan_identity_disagreeing_with_its_mounts_is_malformed():
    with pytest.raises(MalformedClosure):
        instance(mount_plan_identity="sha256:" + "00" * 32)
    fewer = MOUNTS[:-1]
    assert instance(mounts=fewer, mount_plan_identity=mount_plan_identity(fewer)).mounts == fewer


def test_k3_an_instance_attests_every_namespace_and_no_other():
    with pytest.raises(MalformedClosure):
        instance(namespaces=NAMESPACES[:-1])
    with pytest.raises(MalformedClosure):
        instance(namespaces=(*NAMESPACES, "time"))
    assert instance(namespaces=tuple(reversed(NAMESPACES))).namespaces == tuple(reversed(NAMESPACES))


def test_k3_the_confined_members_are_all_present_or_all_absent():
    with pytest.raises(MalformedClosure):
        confined_receipt(mounts=None)
    with pytest.raises(MalformedClosure):
        BoundaryReceipt(scratch_mapping="s", argv=("a",), rendered_config=(), instance=instance())
    minimal = BoundaryReceipt(scratch_mapping="s", argv=("a",), rendered_config=())
    assert not minimal.confined and confined_receipt().confined


def test_a_receipt_capability_outside_the_vocabulary_is_unspellable():
    with pytest.raises(MalformedClosure):
        BoundaryReceipt(scratch_mapping="s", argv=("a",), rendered_config=(), capabilities=("teleportation",))


# --- K4: the domains ----------------------------------------------------------
def test_k4_the_minimal_receipt_projection_is_byte_stable_under_v1():
    receipt = BoundaryReceipt(scratch_mapping="scratch-mount-a", argv=("snakemake",), rendered_config=(("alpha", "0.05"),))
    assert _receipt_projection(receipt) == {
        "scratch_mapping": "scratch-mount-a",
        "argv": ["snakemake"],
        "rendered_config": [["alpha", "0.05"]],
        "capabilities": [],
    }
    assert receipt.identity() == v1.digest(BOUNDARY_RECEIPT_DOMAIN, _receipt_projection(receipt))
    assert BOUNDARY_RECEIPT_DOMAIN == "science.boundary-receipt.v1"


def test_k4_a_confined_receipt_projects_its_three_members_under_v2():
    receipt = confined_receipt()
    projection = _receipt_projection(receipt)
    assert set(projection) == {"scratch_mapping", "argv", "rendered_config", "capabilities", "instance", "rendered_environment", "mounts"}
    assert projection["instance"]["environment_identity"] == ENV_IDENTITY
    assert receipt.identity() == v1.digest(CONFINED_RECEIPT_DOMAIN, projection)
    assert CONFINED_RECEIPT_DOMAIN == "science.boundary-receipt.v2"


def test_k4_a_confined_receipt_makes_a_v2_run():
    assert run_domain_for(False) == RUN_DOMAIN == "science.run.v1"
    assert run_domain_for(True) == CONFINED_RUN_DOMAIN == "science.run.v2"
    minimal = closure()
    confined = confined_closure()
    assert minimal.address() == v1.digest(
        RUN_DOMAIN,
        {"recipe": minimal.recipe._projection(), "result": [["outputs/result.txt", minimal.result.outputs[0][1]]],
         "occurrence": _occurrence_projection(minimal.occurrence)},
    )
    assert confined.address() != minimal.address()
    assert confined.address() == v1.digest(
        CONFINED_RUN_DOMAIN,
        {"recipe": confined.recipe._projection(), "result": [["outputs/result.txt", confined.result.outputs[0][1]]],
         "occurrence": _occurrence_projection(confined.occurrence)},
    )


def test_the_cut_3_occurrence_fixture_still_spells_a_minimal_receipt():
    assert not occurrence().receipt.confined
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_confinement_values.py | tail -3`
Expected: FAIL — `ImportError: cannot import name 'CAPABILITIES'`.

- [ ] **Step 3: Implement the values**

In `python/src/science/recipe.py`:

Replace the four domain constants (lines 46–49) with:

```python
RECIPE_DOMAIN = "science.recipe.v1"
RUN_DOMAIN = "science.run.v1"
CONFINED_RUN_DOMAIN = "science.run.v2"
ENVIRONMENT_DOMAIN = "science.environment.v1"
BOUNDARY_RECEIPT_DOMAIN = "science.boundary-receipt.v1"
CONFINED_RECEIPT_DOMAIN = "science.boundary-receipt.v2"
MOUNT_PLAN_DOMAIN = "science.mount-plan.v1"

#: §7.3a's three capabilities — the closed vocabulary a policy may name.
CAPABILITIES = ("from-bundle", "closure-confined-filesystem", "network-denied")
#: What `clean-environment` requires — spelled separately, never derived from
#: CAPABILITIES, so a capability added later does not become a requirement.
REQUIRED_FOR_CLEAN_ENVIRONMENT = ("from-bundle", "closure-confined-filesystem", "network-denied")
RENDERED_KINDS = ("file", "symlink", "value")
NAMESPACES = ("cgroup", "ipc", "mnt", "net", "pid", "user", "uts")
MOUNT_ACCESS = ("ro", "rw")
```

Add `BoundaryPolicyUnsupported` to the `from science.errors import` line. Add after `_require_pairs`:

```python
def _require_triples(value: object, where: str) -> None:
    _require_tuple(value, where)
    if not all(
        type(row) is tuple and len(row) == 3 and all(type(member) is str for member in row)
        for row in cast(tuple[object, ...], value)
    ):
        raise MalformedClosure(f"{where} must contain (string, string, string) triples only")


def _triples(rows: tuple[tuple[str, str, str], ...]) -> list[list[str]]:
    return [list(row) for row in sorted(rows)]
```

`EnvironmentManifest` is untouched here (Task 5 reshapes it together with the capture that produces the new rows).

Extend `BoundaryPolicy.__post_init__` with, after the existing three lines:

```python
        if any(capability not in CAPABILITIES for capability in self.capabilities):
            raise MalformedClosure(f"boundary policy capabilities are outside the closed vocabulary {CAPABILITIES}")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise MalformedClosure("boundary policy capabilities name each capability once")
```

Directly after the `BoundaryPolicy` class:

```python
MINIMAL_POLICY = BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")
CONFINED_POLICY = BoundaryPolicy(
    identity="boundary-policy/confined-v1",
    scope_rule="scope-derivation/v1",
    capabilities=CAPABILITIES,
)
SUPPORTED_POLICIES = (MINIMAL_POLICY, CONFINED_POLICY)


def supported_policy(policy: object) -> BoundaryPolicy:
    """The entire definition — identity, scope rule and capability *set* —
    must equal one of the two the boundary knows; the canonical known value is
    returned, so a reordered spelling of a known set carries on as the
    definition it names (design §3)."""
    if type(policy) is not BoundaryPolicy:
        raise BoundaryPolicyUnsupported("the boundary policy must be a BoundaryPolicy value")
    for known in SUPPORTED_POLICIES:
        if (policy.identity, policy.scope_rule, frozenset(policy.capabilities)) == (known.identity, known.scope_rule, frozenset(known.capabilities)):
            return known
    raise BoundaryPolicyUnsupported(
        f"{policy.identity!r} with scope rule {policy.scope_rule!r} and capabilities "
        f"{policy.capabilities} matches no known definition"
    )
```

Before the `BoundaryReceipt` class:

```python
def mount_plan_identity(mounts: tuple[tuple[str, str, str], ...]) -> str:
    """Digest of a canonical mount table: rows of (mountpoint, role, access)."""
    _require_triples(mounts, "mount plan rows")
    return v1.digest(MOUNT_PLAN_DOMAIN, {"mounts": _triples(mounts)})


@sealed
@final
@dataclass(frozen=True)
class InstanceAttestation:
    """What the boundary observed of the fresh instance from its own /proc:
    every namespace distinct from the parent's, the canonical mount table, its
    identity, and the verified snapshot's environment identity (design §6.3)."""

    namespaces: tuple[str, ...]
    mounts: tuple[tuple[str, str, str], ...]
    mount_plan_identity: str
    environment_identity: str

    def __post_init__(self) -> None:
        _require_strings(self.namespaces, "instance namespaces")
        if tuple(sorted(self.namespaces)) != NAMESPACES:
            raise MalformedClosure(f"an instance attests every namespace in {NAMESPACES} as distinct, and no other")
        _require_triples(self.mounts, "instance mounts")
        points = [point for point, _, _ in self.mounts]
        if len(set(points)) != len(points):
            raise MalformedClosure("instance mounts name each mountpoint once")
        if any(access not in MOUNT_ACCESS for _, _, access in self.mounts):
            raise MalformedClosure(f"instance mount access is one of {MOUNT_ACCESS}")
        _require_str(self.mount_plan_identity, "instance mount plan identity")
        if self.mount_plan_identity != mount_plan_identity(self.mounts):
            raise MalformedClosure("an instance's mount plan identity is the digest of its own canonical mounts")
        _require_component(self.environment_identity, "instance environment identity")
```

Replace `BoundaryReceipt` with:

```python
@sealed
@final
@dataclass(frozen=True)
class BoundaryReceipt:
    scratch_mapping: str
    argv: tuple[str, ...]
    rendered_config: tuple[tuple[str, str], ...]
    capabilities: tuple[str, ...] = ()
    instance: InstanceAttestation | None = None
    rendered_environment: tuple[tuple[str, str, str], ...] | None = None
    mounts: tuple[tuple[str, str], ...] | None = None

    def __post_init__(self) -> None:
        _require_str(self.scratch_mapping, "boundary receipt scratch mapping")
        _require_strings(self.argv, "boundary receipt argv")
        _require_pairs(self.rendered_config, "boundary receipt rendered config")
        _require_strings(self.capabilities, "boundary receipt capabilities")
        if any(capability not in CAPABILITIES for capability in self.capabilities):
            raise MalformedClosure(f"boundary receipt capabilities are outside the closed vocabulary {CAPABILITIES}")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise MalformedClosure("boundary receipt capabilities name each capability once")
        present = sum(member is not None for member in (self.instance, self.rendered_environment, self.mounts))
        if present not in (0, 3):
            raise MalformedClosure(
                "a confined receipt carries instance, rendered_environment and mounts together; a minimal receipt carries none"
            )
        if self.instance is None:
            return
        if type(self.instance) is not InstanceAttestation:
            raise MalformedClosure("a confined receipt's instance is an InstanceAttestation")
        _require_triples(self.rendered_environment, "boundary receipt rendered environment")
        if any(kind not in RENDERED_KINDS for _, kind, _ in cast(tuple[tuple[str, str, str], ...], self.rendered_environment)):
            raise MalformedClosure(f"a rendered environment row's kind is one of {RENDERED_KINDS}")
        _require_pairs(self.mounts, "boundary receipt mounts")

    @property
    def confined(self) -> bool:
        return self.instance is not None

    def identity(self) -> str:
        domain = CONFINED_RECEIPT_DOMAIN if self.confined else BOUNDARY_RECEIPT_DOMAIN
        return v1.digest(domain, _receipt_projection(self))
```

Replace `_receipt_projection` with:

```python
def _receipt_projection(receipt: BoundaryReceipt) -> dict[str, object]:
    projection: dict[str, object] = {
        "scratch_mapping": receipt.scratch_mapping,
        "argv": list(receipt.argv),
        "rendered_config": _pairs(receipt.rendered_config),
        "capabilities": sorted(receipt.capabilities),
    }
    if not receipt.confined:
        return projection
    instance = cast(InstanceAttestation, receipt.instance)
    projection["instance"] = {
        "namespaces": sorted(instance.namespaces),
        "mounts": _triples(instance.mounts),
        "mount_plan_identity": instance.mount_plan_identity,
        "environment_identity": instance.environment_identity,
    }
    projection["rendered_environment"] = _triples(cast(tuple[tuple[str, str, str], ...], receipt.rendered_environment))
    projection["mounts"] = _pairs(cast(tuple[tuple[str, str], ...], receipt.mounts))
    return projection
```

Before `RunClosure`:

```python
def run_domain_for(confined: bool) -> str:
    """A confined receipt reshapes the run projection, so it takes the
    successor run domain; the dispatch is by exact receipt shape (design §6.3)."""
    return CONFINED_RUN_DOMAIN if confined else RUN_DOMAIN
```

In `RunClosure.address`, change `RUN_DOMAIN,` to `run_domain_for(self.occurrence.receipt.confined),` — the `"occurrence": _occurrence_projection(self.occurrence),` line stays byte-identical.

Add to `__all__`: `"CAPABILITIES"`, `"CONFINED_POLICY"`, `"CONFINED_RECEIPT_DOMAIN"`, `"CONFINED_RUN_DOMAIN"`, `"InstanceAttestation"`, `"MINIMAL_POLICY"`, `"MOUNT_PLAN_DOMAIN"`, `"NAMESPACES"`, `"REQUIRED_FOR_CLEAN_ENVIRONMENT"`, `"SUPPORTED_POLICIES"`, `"mount_plan_identity"`, `"run_domain_for"`, `"supported_policy"` (keep the list sorted as it is).

- [ ] **Step 4: Run to verify pass, and the anchor audit**

Run: `cd python && set -o pipefail && uv run pytest tests/test_confinement_values.py tests/test_recipe.py tests/test_boundary.py tests/test_replay.py tests/test_verify.py tests/test_run_persistence.py tests/test_assess.py tests/test_production.py tests/test_decode.py | tail -1 && uv run pytest tests/test_n2.py -k stale | tail -1 && uv run ruff check src/science/recipe.py tests && uv run pyright src/science/recipe.py | tail -1`
Expected: all passed (the durable `test_run_persistence.py` tests fail only with the host's allowlist refusal — confirm every failure message is `CapabilityUnavailable: volume configuration is not on the supplied durability allowlist`, and nothing else); no stale anchors; clean; `0 errors`. Nothing in this task changes the environment manifest, so the boundary tests execute exactly as before.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/recipe.py python/tests
git commit -m "feat(recipe): close the capability vocabulary and attest the confined instance"
```

---

### Task 4: The wire codec — receipt variants and the run-domain dispatch

**Files:**
- Modify: `python/src/science/runrecord.py` (`_validate_occurrence` 318–371; `_reproject` 391–420; `decode_run_record` 458; imports 23–31)
- Test: `python/tests/test_runrecord_confined.py`

**Interfaces:**
- Consumes: `run_domain_for`, `mount_plan_identity`, `CAPABILITIES`, `NAMESPACES`, `MOUNT_ACCESS`, `RENDERED_KINDS` (Task 3).
- Produces: `decode_projection` accepting both receipt spellings and mirroring every value invariant (unique capabilities, unique mountpoints, closed access and rendered-kind sets); `decode_run_record` recomputing under the domain the receipt shape names.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_runrecord_confined.py`:

```python
"""K4: the wire codec accepts both receipt spellings and recomputes each run
under the domain its receipt shape names; K3: a mount plan identity that
disagrees with its mounts is refused on the wire too."""

import json

import pytest
from confinement_fixtures import confined_closure
from fixtures_cut3 import closure
from nodes.core.frontmatter import node_from_markdown

from science.errors import MalformedRecord
from science.identity import v1
from science.recipe import CONFINED_RUN_DOMAIN, RUN_DOMAIN
from science.runrecord import decode_projection, decode_run_record, projection_text, publication_plan
from science.stored import RUN_CLOSURE_FACET


def _node_of(run):
    _, _, (create,) = publication_plan(run)
    return node_from_markdown(create.content.decode("utf-8"))


def test_k4_a_minimal_projection_carries_exactly_the_v1_receipt_keys():
    parsed = decode_projection(projection_text(closure()))
    assert set(parsed["occurrence"]["receipt"]) == {"scratch_mapping", "argv", "rendered_config", "capabilities"}


def test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2():
    run = confined_closure()
    parsed = decode_projection(projection_text(run))
    assert set(parsed["occurrence"]["receipt"]) >= {"instance", "rendered_environment", "mounts"}
    assert v1.digest(CONFINED_RUN_DOMAIN, parsed) == run.address()
    assert v1.digest(RUN_DOMAIN, parsed) != run.address()
    published = decode_run_record(_node_of(run))
    assert published is not None and published.address == run.address()


def test_k4_a_minimal_run_still_recomputes_under_run_v1():
    run = closure()
    published = decode_run_record(_node_of(run))
    assert published is not None and published.address == run.address() == v1.digest(RUN_DOMAIN, decode_projection(projection_text(run)))


def test_k3_a_wire_mount_plan_identity_disagreeing_with_its_mounts_is_refused():
    run = confined_closure()
    text = json.loads(projection_text(run))
    text["occurrence"]["receipt"]["instance"]["mount_plan_identity"] = "sha256:" + "00" * 32
    with pytest.raises(MalformedRecord, match="mount_plan_identity"):
        decode_projection(v1.encode(text))


def test_a_partial_confined_receipt_is_refused_on_the_wire():
    run = confined_closure()
    text = json.loads(projection_text(run))
    del text["occurrence"]["receipt"]["mounts"]
    with pytest.raises(MalformedRecord):
        decode_projection(v1.encode(text))


def test_a_reordered_confined_list_is_out_of_canonical_order():
    run = confined_closure()
    text = json.loads(projection_text(run))
    text["occurrence"]["receipt"]["instance"]["namespaces"].reverse()
    with pytest.raises(MalformedRecord, match="canonical order"):
        decode_projection(v1.encode(text))


def test_the_run_closure_facet_survives_the_confined_shape():
    run = confined_closure()
    node = _node_of(run)
    assert set(node.facets[RUN_CLOSURE_FACET]) == {"projection"}


def _with_recomputed_mount_identity(receipt: dict) -> dict:
    instance = receipt["instance"]
    instance["mount_plan_identity"] = mount_plan_identity(tuple(tuple(row) for row in instance["mounts"]))
    return receipt


@pytest.mark.parametrize(
    "mutate, match",
    [
        (lambda r: r["capabilities"].insert(0, r["capabilities"][0]), "capabilities"),
        (lambda r: _with_recomputed_mount_identity(r)["instance"]["mounts"].insert(0, list(r["instance"]["mounts"][0])), "mounts"),
        (lambda r: _with_recomputed_mount_identity(r)["instance"]["mounts"][0].__setitem__(2, "rx"), "mounts"),
        (lambda r: r["rendered_environment"][0].__setitem__(1, "directory"), "rendered_environment"),
    ],
)
def test_the_wire_refuses_what_the_values_refuse(mutate, match):
    """Parity: a projection the value types could not construct is refused on
    the wire too — a duplicate capability, a duplicate mountpoint, an access
    outside MOUNT_ACCESS, a rendered kind outside RENDERED_KINDS."""
    run = confined_closure()
    text = json.loads(projection_text(run))
    receipt = text["occurrence"]["receipt"]
    mutate(receipt)
    if "mounts" in match:
        _with_recomputed_mount_identity(receipt)
    with pytest.raises(MalformedRecord, match=match):
        decode_projection(v1.encode(text))
```

(add `from science.recipe import CONFINED_RUN_DOMAIN, RUN_DOMAIN, mount_plan_identity` — the mutations that touch `mounts` recompute the identity so the parity check, not the identity check, is what refuses.)

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_runrecord_confined.py | tail -3`
Expected: FAIL — `MalformedRecord: run projection at $.occurrence.receipt: keys [...] != [...]`.

- [ ] **Step 3: Implement**

In `python/src/science/runrecord.py`, extend the `science.recipe` import with `CAPABILITIES`, `MOUNT_ACCESS`, `NAMESPACES`, `RENDERED_KINDS`, `mount_plan_identity`, `run_domain_for`, and drop `RUN_DOMAIN` from it. Add a helper after `_pair_list`:

```python
def _triple_list(value: object, path: str) -> list[list[str]]:
    if not isinstance(value, list) or any(
        not isinstance(row, list)
        or len(row) != 3
        or any(type(member) is not str for member in row)
        for row in value
    ):
        _refuse(path, "not a list of [string, string, string] triples")
    return value


_RECEIPT_KEYS = {"scratch_mapping", "argv", "rendered_config", "capabilities"}
_CONFINED_RECEIPT_KEYS = _RECEIPT_KEYS | {"instance", "rendered_environment", "mounts"}


def _is_confined_receipt(receipt: object) -> bool:
    return isinstance(receipt, dict) and "instance" in receipt
```

Replace the receipt block at the end of `_validate_occurrence` (from `receipt = _mapping(` to the `_str_list(receipt["capabilities"], ...)` line) with:

```python
    confined = _is_confined_receipt(occurrence["receipt"])
    receipt = _mapping(
        occurrence["receipt"],
        _CONFINED_RECEIPT_KEYS if confined else _RECEIPT_KEYS,
        "$.occurrence.receipt",
    )
    _str_at(receipt["scratch_mapping"], "$.occurrence.receipt.scratch_mapping")
    _str_list(receipt["argv"], "$.occurrence.receipt.argv")
    _pair_list(
        receipt["rendered_config"], "$.occurrence.receipt.rendered_config"
    )
    capabilities = _str_list(receipt["capabilities"], "$.occurrence.receipt.capabilities")
    if any(capability not in CAPABILITIES for capability in capabilities):
        _refuse("$.occurrence.receipt.capabilities", f"outside the closed vocabulary {CAPABILITIES}")
    if len(set(capabilities)) != len(capabilities):
        _refuse("$.occurrence.receipt.capabilities", "names a capability more than once")
    if confined:
        instance = _mapping(
            receipt["instance"],
            {"namespaces", "mounts", "mount_plan_identity", "environment_identity"},
            "$.occurrence.receipt.instance",
        )
        namespaces = _str_list(instance["namespaces"], "$.occurrence.receipt.instance.namespaces")
        if sorted(namespaces) != list(NAMESPACES):
            _refuse("$.occurrence.receipt.instance.namespaces", f"not exactly {NAMESPACES}")
        mounts = _triple_list(instance["mounts"], "$.occurrence.receipt.instance.mounts")
        points = [point for point, _, _ in mounts]
        if len(set(points)) != len(points):
            _refuse("$.occurrence.receipt.instance.mounts", "names a mountpoint more than once")
        if any(access not in MOUNT_ACCESS for _, _, access in mounts):
            _refuse("$.occurrence.receipt.instance.mounts", f"access is not one of {MOUNT_ACCESS}")
        recomputed = mount_plan_identity(tuple((point, role, access) for point, role, access in mounts))
        if _str_at(instance["mount_plan_identity"], "$.occurrence.receipt.instance.mount_plan_identity") != recomputed:
            _refuse("$.occurrence.receipt.instance.mount_plan_identity", "is not the digest of its own mounts")
        _component_at(instance["environment_identity"], "$.occurrence.receipt.instance.environment_identity")
        rendered = _triple_list(receipt["rendered_environment"], "$.occurrence.receipt.rendered_environment")
        if any(kind not in RENDERED_KINDS for _, kind, _ in rendered):
            _refuse("$.occurrence.receipt.rendered_environment", f"kind is not one of {RENDERED_KINDS}")
        _pair_list(receipt["mounts"], "$.occurrence.receipt.mounts")
```

In `_reproject`, after the `receipt["capabilities"] = sorted(...)` statement add:

```python
    if _is_confined_receipt(receipt):
        instance = cast(dict[str, object], receipt["instance"])
        instance["namespaces"] = sorted(cast("list[str]", instance["namespaces"]))
        instance["mounts"] = sorted(cast("list[list[str]]", instance["mounts"]))
        receipt["rendered_environment"] = sorted(cast("list[list[str]]", receipt["rendered_environment"]))
        receipt["mounts"] = sorted(cast("list[list[str]]", receipt["mounts"]))
```

In `decode_run_record`, replace `address = v1.digest(RUN_DOMAIN, parsed)` with:

```python
    occurrence_view = cast(dict[str, object], parsed["occurrence"])
    address = v1.digest(run_domain_for(_is_confined_receipt(occurrence_view["receipt"])), parsed)
```

(the later `occurrence = cast(...)` line stays as it is).

- [ ] **Step 4: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_runrecord_confined.py tests/test_decode.py tests/test_run_persistence.py | tail -1 && uv run pytest tests/test_n2.py -k stale | tail -1 && uv run ruff check src/science/runrecord.py && uv run pyright src/science/runrecord.py | tail -1`
Expected: the new tests pass; `test_run_persistence.py` fails only with the allowlist refusal; no stale anchors; clean; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/runrecord.py python/tests/test_runrecord_confined.py
git commit -m "feat(runrecord): accept both receipt spellings and recompute a confined run under run.v2"
```

---

### Task 5: The runtime artifact closure — the per-file walk and the policy-neutral argv

**Files:**
- Modify: `python/src/science/recipe.py` (`ENVIRONMENT_DOMAIN` at 48; `EnvironmentManifest` 187–195; new `ARTIFACT_KINDS`) — the v2 row shape lands **in this task**, atomically with the capture that produces it
- Modify: `python/src/science/adapter.py` (imports; `capture_environment` 157–165; `build_argv` 184–221; new closure walk)
- Modify: `python/src/science/boundary.py:357-364` (the one `build_argv` call — keyword renames only)
- Modify: `python/tests/fixtures_cut3.py:118` and every other `EnvironmentManifest(` construction under `python/tests/`
- Test: `python/tests/test_closure_capture.py`; `python/tests/test_adapter.py` (the existing `build_argv` tests take the new keywords)

**Interfaces:**
- Produces (`science.recipe`): `ENVIRONMENT_DOMAIN = "science.environment.v2"`, `ARTIFACT_KINDS`, `EnvironmentManifest(artifacts: tuple[tuple[str, str, str], ...])` rows `(normalized absolute sandbox path, kind, digest | link target)`.
- Produces (`science.adapter`): `SANDBOX_ENV`, `SANDBOX_PYTHON`, `SANDBOX_SITE`, `SANDBOX_PATH`, `SANDBOX_LIB`, `SANDBOX_VENV`; `CapturedEnvironment(manifest, plan, rendered, loader, interpreter, loader_map)` where `loader_map` rows are `(ELF sandbox path, SONAME, resolved sandbox path)`; `capture_closure() -> CapturedEnvironment`; `capture_environment() -> EnvironmentManifest` (unchanged name, `capture_closure().manifest`); `elf_interpreter(path) -> str`; `loader_listing(loader, path) -> dict[str, Path]` (run under an empty environment); `_is_loadable_elf(path) -> bool`; `_Closure` (the walker, test-visible: `register`, `root_of`, `sandbox_of`, `add`, `add_chain`, `add_tree`, `add_records`, `add_pth`, `add_native`, `elves`, `check_links`); `build_argv(*, interpreter, snakefile, directory, targets, config, log_handler, cores, in_process_jobs)`.
- Consumes: `_triples` (Task 3); `ClosureUnsupported` (Task 2).
- `distribution_digest`, `tree_digest` and `_stdlib_digest` stay as they are — the walk does not call them, and cut 3's tests may.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_closure_capture.py`:

```python
"""The runtime artifact closure (design §4.2): discovered from the executing
interpreter, one row per file, host paths ephemeral; K7's three refusals."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import science.adapter as adapter_module
from science.adapter import (
    SANDBOX_ENV,
    SANDBOX_LIB,
    SANDBOX_PATH,
    SANDBOX_PYTHON,
    SANDBOX_SITE,
    SANDBOX_VENV,
    CapturedEnvironment,
    _Closure,
    _parse_listing,
    build_argv,
    capture_closure,
    capture_environment,
    elf_interpreter,
    loader_listing,
    require_executing_environment,
)
from science.errors import ClosureUnsupported, MalformedClosure, UnsafeInvocation
from science.identity import v1
from science.recipe import ENVIRONMENT_DOMAIN, EnvironmentManifest

LOADABLE_ELF = b"\x7fELF" + bytes(12) + b"\x03\x00"  # ET_DYN, enough header for the type check


def _terminal(rows: dict[str, tuple[str, str]], path: str) -> str:
    while rows[path][0] == "symlink":
        target = rows[path][1]
        path = target if target.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(path), target))
    return path


# --- science.environment.v2 (moved here with the capture that produces it) ----
def test_the_manifest_is_per_file_under_the_v2_domain():
    manifest = EnvironmentManifest(
        artifacts=(
            ("/science/env/python/bin/python3.13", "file", "sha256:" + "dd" * 32),
            ("/science/env/python/lib/libpython3.13.so", "symlink", "libpython3.13.so.1.0"),
        )
    )
    assert ENVIRONMENT_DOMAIN == "science.environment.v2"
    assert manifest.identity() == v1.digest(
        ENVIRONMENT_DOMAIN,
        {
            "artifacts": [
                ["/science/env/python/bin/python3.13", "file", "sha256:" + "dd" * 32],
                ["/science/env/python/lib/libpython3.13.so", "symlink", "libpython3.13.so.1.0"],
            ]
        },
    )


@pytest.mark.parametrize(
    "rows",
    [
        (("python", "sha256:" + "dd" * 32),),  # the v1 pair shape
        (("science/env/x", "file", "sha256:" + "dd" * 32),),  # not absolute
        (("/science/env/../../outside", "file", "sha256:" + "dd" * 32),),  # not normalized: escapes a snapshot join
        (("/science/env//x", "file", "sha256:" + "dd" * 32),),  # empty component
        (("/science/env/./x", "file", "sha256:" + "dd" * 32),),  # dot component
        (("/science/env/x/", "file", "sha256:" + "dd" * 32),),  # trailing slash
        (("//science/env/x", "file", "sha256:" + "dd" * 32),),  # POSIX double root
        (("/science/env/x", "directory", "sha256:" + "dd" * 32),),  # kind outside the closed set
        (("/science/env/x", "file", "sha256:" + "dd" * 32), ("/science/env/x", "file", "sha256:" + "ee" * 32)),
        (("/science/env/x", "file", ""),),
    ],
)
def test_a_malformed_manifest_row_is_unspellable(rows):
    with pytest.raises(MalformedClosure):
        EnvironmentManifest(artifacts=rows)


@pytest.fixture(scope="module")
def captured() -> CapturedEnvironment:
    return capture_closure()


def test_every_row_is_a_sandbox_path_and_the_plan_covers_exactly_the_rows(captured):
    paths = {path for path, _, _ in captured.manifest.artifacts}
    assert paths == set(captured.plan)
    assert all(path.startswith("/science/env/") or path == captured.loader for path in paths)
    assert not any(str(Path.home()) in path for path in paths)


def test_the_interpreter_its_libraries_and_the_loader_are_rows(captured):
    rows = dict((path, (kind, content)) for path, kind, content in captured.manifest.artifacts)
    assert captured.interpreter.startswith(f"{SANDBOX_PYTHON}/bin/")
    assert rows[captured.interpreter][0] == "file"
    assert rows[captured.loader][0] == "file"
    assert captured.loader.startswith("/")
    assert any(path.startswith(f"{SANDBOX_LIB}/libc.so") for path in rows)
    assert any(path.startswith(f"{SANDBOX_SITE}/snakemake/") for path in rows)
    assert any(path.startswith(f"{SANDBOX_PATH}/") and path.endswith("/science/adapter.py") for path in rows)


def test_the_loader_map_covers_every_loadable_elf_and_names_rows_only(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    listed = {elf for elf, _, _ in captured.loader_map}
    assert captured.interpreter in listed
    assert all(elf.startswith(f"{SANDBOX_ENV}/") and rows[elf][0] == "file" for elf in listed)
    assert all(resolved in rows for _, _, resolved in captured.loader_map)
    assert all(rows[_terminal(rows, resolved)][0] == "file" for _, _, resolved in captured.loader_map)
    assert any(soname.startswith("libc.so") for _, soname, _ in captured.loader_map)


def test_the_interpreter_symlink_chain_is_captured_link_by_link(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    rendered = {path for path, _, _ in captured.rendered}
    venv_python = f"{SANDBOX_VENV}/bin/python"
    if Path(sys.executable).is_symlink() and sys.prefix != sys.base_prefix:
        assert rows[venv_python][0] == "symlink" and venv_python not in rendered
        assert _terminal(rows, venv_python) == captured.interpreter
    else:
        assert venv_python in rendered and venv_python not in rows
    assert rows[captured.interpreter][0] == "file"


def test_every_symlink_row_resolves_to_a_closure_row(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    for path, (kind, content) in rows.items():
        if kind != "symlink":
            continue
        resolved = content if content.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(path), content))
        assert resolved in rows or any(row.startswith(resolved + "/") for row in rows), (path, content)


def test_the_rendered_venv_and_pth_files_are_functions_of_the_layout(captured):
    rendered = {path: (kind, content) for path, kind, content in captured.rendered}
    assert rendered[f"{SANDBOX_VENV}/pyvenv.cfg"] == ("file", f"home = {SANDBOX_PYTHON}/bin\ninclude-system-site-packages = false\n")
    version_dir = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    assert rendered[f"{SANDBOX_VENV}/lib/{version_dir}/site-packages"] == ("symlink", SANDBOX_SITE)
    science_pth = next(path for path in rendered if path.endswith("_science.pth"))
    assert rendered[science_pth][1].startswith(f"{SANDBOX_PATH}/")
    assert not set(rendered) & {path for path, _, _ in captured.manifest.artifacts}


def test_the_manifest_is_the_executing_environment_under_v2(captured):
    assert ENVIRONMENT_DOMAIN == "science.environment.v2"
    assert capture_environment() == captured.manifest
    require_executing_environment(captured.manifest)


def test_elf_interpreter_reads_the_program_interpreter_from_the_header():
    loader = elf_interpreter(Path(os.path.realpath(sys.executable)))
    assert loader.startswith("/") and Path(loader).exists()
    with pytest.raises(ClosureUnsupported):
        elf_interpreter(Path(__file__))


def test_parse_listing_keeps_sonames_and_drops_the_vdso_and_the_loader():
    text = (
        "\tlinux-vdso.so.1 (0x00007f00)\n"
        "\tlibm.so.6 => /usr/lib/libm.so.6 (0x00007f01)\n"
        "\t/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f02)\n"
    )
    assert _parse_listing(text) == {"libm.so.6": Path("/usr/lib/libm.so.6")}
    with pytest.raises(ClosureUnsupported):
        _parse_listing("\tlibmissing.so.1 => not found\n")


def test_loader_listing_runs_the_loader_under_an_empty_environment(monkeypatch):
    seen: dict = {}

    def fake_run(argv, **kwargs):
        seen.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout="\tlibm.so.6 => /usr/lib/libm.so.6 (0x1)\n", stderr="")

    monkeypatch.setattr(adapter_module.subprocess, "run", fake_run)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/ambient")
    monkeypatch.setenv("LD_PRELOAD", "/ambient/libx.so")
    assert loader_listing("/lib64/ld.so", Path("/x")) == {"libm.so.6": Path("/usr/lib/libm.so.6")}
    assert seen["env"] == {}


def test_a_nonzero_loader_exit_is_closure_unsupported(monkeypatch):
    def failing_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 127, stdout="", stderr="cannot list")

    monkeypatch.setattr(adapter_module.subprocess, "run", failing_run)
    with pytest.raises(ClosureUnsupported, match="cannot list"):
        loader_listing("/lib64/ld.so", Path("/x"))


# --- K7: the three refusals, over synthetic closures --------------------------
def _site(tmp_path: Path) -> tuple[_Closure, Path]:
    purelib = tmp_path / "site"
    purelib.mkdir()
    walker = _Closure()
    walker.register(purelib, SANDBOX_SITE)
    return walker, purelib


def test_k7_a_mixed_pth_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    tree = tmp_path / "tree"
    tree.mkdir()
    (purelib / "mixed.pth").write_text(f"import os\n{tree}\n")
    with pytest.raises(ClosureUnsupported, match="mixes"):
        walker.add_pth(purelib)


def test_a_pth_path_line_is_followed_under_a_canonical_ordinal_key(tmp_path):
    walker, purelib = _site(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "mod.py").write_text("X = 1\n")
    (second / "other.py").write_text("Y = 2\n")
    (purelib / "_editable.pth").write_text(f"{first}\n{second}\n")
    walker.add_pth(purelib)
    assert f"{SANDBOX_PATH}/_editable.pth/0/mod.py" in walker.rows
    assert f"{SANDBOX_PATH}/_editable.pth/1/other.py" in walker.rows
    assert walker.rendered[f"{SANDBOX_SITE}/_editable.pth"] == (
        "file",
        f"{SANDBOX_PATH}/_editable.pth/0\n{SANDBOX_PATH}/_editable.pth/1\n",
    )


def test_a_pth_path_line_that_is_not_a_directory_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "bad.pth").write_text("relative/dir\n")
    with pytest.raises(ClosureUnsupported):
        walker.add_pth(purelib)


def test_an_import_only_pth_names_a_module_that_must_be_a_closure_member(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "_shim.pth").write_text("import _shim; _shim.install()\n")
    with pytest.raises(ClosureUnsupported, match="not a closure member"):
        walker.add_pth(purelib)
    (purelib / "_shim.py").write_text("def install(): pass\n")
    walker.add_pth(purelib)
    assert walker.rows[f"{SANDBOX_SITE}/_shim.pth"][0] == "file"
    assert walker.rows[f"{SANDBOX_SITE}/_shim.py"][0] == "file"


def test_k7_a_symlink_escaping_the_closure_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "escape").symlink_to("../../outside")
    with pytest.raises(ClosureUnsupported, match="escapes"):
        walker.add(purelib / "escape")
    (purelib / "absolute").symlink_to("/etc/hostname")
    with pytest.raises(ClosureUnsupported, match="escapes"):
        walker.add(purelib / "absolute")


def test_a_symlink_row_captures_its_target_and_a_dangling_link_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "real.so.1").write_bytes(b"x")
    (purelib / "real.so").symlink_to("real.so.1")
    walker.add(purelib / "real.so")
    assert walker.rows[f"{SANDBOX_SITE}/real.so"] == ("symlink", "real.so.1")
    assert walker.rows[f"{SANDBOX_SITE}/real.so.1"][0] == "file"
    walker.check_links()
    (purelib / "dangling").symlink_to("missing")
    with pytest.raises(ClosureUnsupported, match="names nothing"):
        walker.add(purelib / "dangling")


def test_check_links_refuses_a_symlink_row_whose_target_is_no_row(tmp_path):
    walker, _ = _site(tmp_path)
    walker.rows[f"{SANDBOX_SITE}/orphan"] = ("symlink", "../elsewhere")
    with pytest.raises(ClosureUnsupported, match="not a closure row"):
        walker.check_links()


def test_a_relative_link_into_another_root_is_rewritten_to_its_sandbox_path(tmp_path):
    walker, purelib = _site(tmp_path)
    base = tmp_path / "base"
    (base / "lib").mkdir(parents=True)
    (base / "lib" / "libq.so.1").write_bytes(b"q")
    walker.register(base, SANDBOX_PYTHON)
    (purelib / "libq.so").symlink_to("../base/lib/libq.so.1")
    walker.add(purelib / "libq.so")
    assert walker.rows[f"{SANDBOX_SITE}/libq.so"] == ("symlink", f"{SANDBOX_PYTHON}/lib/libq.so.1")
    assert walker.rows[f"{SANDBOX_PYTHON}/lib/libq.so.1"][0] == "file"
    walker.check_links()


def test_a_link_to_a_directory_inside_the_closure_is_a_symlink_row(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "pkg").mkdir()
    (purelib / "pkg" / "__init__.py").write_text("")
    (purelib / "alias").symlink_to("pkg")
    walker.add(purelib / "pkg" / "__init__.py")
    walker.add(purelib / "alias")
    assert walker.rows[f"{SANDBOX_SITE}/alias"] == ("symlink", "pkg")
    walker.check_links()


def test_add_chain_captures_every_link_and_returns_the_terminal(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "python3.13").write_bytes(b"bin")
    (purelib / "python3").symlink_to("python3.13")
    (purelib / "python").symlink_to("python3")
    assert walker.add_chain(purelib / "python") == f"{SANDBOX_SITE}/python3.13"
    assert walker.rows[f"{SANDBOX_SITE}/python"] == ("symlink", "python3")
    assert walker.rows[f"{SANDBOX_SITE}/python3"] == ("symlink", "python3.13")
    assert walker.rows[f"{SANDBOX_SITE}/python3.13"][0] == "file"


def test_k7_a_soname_collision_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "libz.so.1").write_bytes(b"a")
    (b / "libz.so.1").write_bytes(b"b")
    (purelib / "one.so").write_bytes(LOADABLE_ELF)
    (purelib / "two.so").write_bytes(LOADABLE_ELF)
    listings = {"one.so": {"libz.so.1": a / "libz.so.1"}, "two.so": {"libz.so.1": b / "libz.so.1"}}
    walker.add(purelib / "one.so")
    walker.add(purelib / "two.so")
    with pytest.raises(ClosureUnsupported, match="SONAME"):
        walker.add_native(listing=lambda elf: listings[elf.name])
    single = _Closure()
    single.register(purelib, SANDBOX_SITE)
    single.add(purelib / "one.so")
    single.add_native(listing=lambda elf: listings[elf.name])
    assert single.rows[f"{SANDBOX_LIB}/libz.so.1"][0] == "file"
    assert single.loader_map == [(f"{SANDBOX_SITE}/one.so", "libz.so.1", f"{SANDBOX_LIB}/libz.so.1")]


def test_add_native_closes_over_the_libraries_it_adds_and_maps_in_root_targets_to_their_rows(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "ext.so").write_bytes(LOADABLE_ELF)
    (purelib / "libinner.so.1").write_bytes(LOADABLE_ELF)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "libouter.so.1").write_bytes(LOADABLE_ELF)
    listings = {
        "ext.so": {"libinner.so.1": purelib / "libinner.so.1"},
        "libinner.so.1": {"libouter.so.1": outside / "libouter.so.1"},
        "libouter.so.1": {},
    }
    walker.add(purelib / "ext.so")
    walker.add_native(listing=lambda elf: listings[elf.name])
    assert sorted(walker.loader_map) == [
        (f"{SANDBOX_SITE}/ext.so", "libinner.so.1", f"{SANDBOX_SITE}/libinner.so.1"),
        (f"{SANDBOX_SITE}/libinner.so.1", "libouter.so.1", f"{SANDBOX_LIB}/libouter.so.1"),
    ]
    assert walker.rows[f"{SANDBOX_LIB}/libouter.so.1"][0] == "file"


# --- the policy-neutral argv --------------------------------------------------
def test_build_argv_is_policy_neutral_and_the_minimal_spelling_is_unchanged():
    minimal = build_argv(
        interpreter="/host/python",
        snakefile="/host/scratch/bundle/code/workflow/Snakefile",
        directory="/host/scratch",
        targets=("outputs/result.txt",),
        config={"alpha": "0.05"},
        log_handler="/host/trace/handler.py",
        cores=1,
        in_process_jobs=False,
    )
    assert minimal == (
        "/host/python", "-m", "snakemake",
        "--snakefile", "/host/scratch/bundle/code/workflow/Snakefile",
        "--cores", "1", "--directory", "/host/scratch", "--nolock",
        "--log-handler-script", "/host/trace/handler.py",
        "--config", "alpha=0.05", "--", "outputs/result.txt",
    )
    confined = build_argv(
        interpreter="/science/env/venv/bin/python",
        snakefile="/science/bundle/code/workflow/Snakefile",
        directory="/science/out",
        targets=("outputs/result.txt",),
        config={},
        log_handler="/science/out/.trace/handler.py",
        cores=2,
        in_process_jobs=True,
    )
    assert confined[:3] == ("/science/env/venv/bin/python", "-m", "snakemake")
    assert "--force-use-threads" in confined and confined.index("--force-use-threads") == confined.index("--nolock") + 1
    assert not any(part.startswith("/host") for part in confined)
    with pytest.raises(UnsafeInvocation):
        build_argv(interpreter="/p", snakefile="/s", directory="/d", targets=("--all",), config={}, log_handler="/h", cores=1, in_process_jobs=False)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_closure_capture.py | tail -3`
Expected: FAIL — `ImportError: cannot import name 'SANDBOX_LIB'`.

- [ ] **Step 3: Implement the manifest and the walk**

In `python/src/science/recipe.py`: change `ENVIRONMENT_DOMAIN = "science.environment.v1"` to `ENVIRONMENT_DOMAIN = "science.environment.v2"`; add `ARTIFACT_KINDS = ("file", "symlink")` directly after `REQUIRED_FOR_CLEAN_ENVIRONMENT`; add `import posixpath`; and replace `EnvironmentManifest` with:

```python
@sealed
@final
@dataclass(frozen=True)
class EnvironmentManifest:
    """The runtime artifact closure, one row per file: (sandbox path, kind,
    digest or link target). Host paths never enter it (design §4.1). Every
    path is normalized — absolute, no `.`, `..` or empty components — so a
    join under a snapshot root can never leave it."""

    artifacts: tuple[tuple[str, str, str], ...]

    def __post_init__(self) -> None:
        _require_triples(self.artifacts, "environment artifacts")
        paths = [path for path, _, _ in self.artifacts]
        if len(set(paths)) != len(paths):
            raise MalformedClosure("environment artifacts name each sandbox path once")
        for path, kind, content in self.artifacts:
            if not path.startswith("/") or path.startswith("//") or posixpath.normpath(path) != path:
                raise MalformedClosure(f"environment artifact {path!r} is not a normalized absolute sandbox path")
            if kind not in ARTIFACT_KINDS:
                raise MalformedClosure(f"environment artifact {path!r} has kind {kind!r}, outside {ARTIFACT_KINDS}")
            if not content:
                raise MalformedClosure(f"environment artifact {path!r} carries no content")

    def identity(self) -> str:
        return v1.digest(ENVIRONMENT_DOMAIN, {"artifacts": _triples(self.artifacts)})
```

Add `"ARTIFACT_KINDS"` to `__all__`. The `        if type(self.environment) is not EnvironmentManifest:` anchor in `Recipe.__post_init__` is untouched.

In `python/src/science/adapter.py`: add `import os`, `import posixpath`, `import struct`, `from collections.abc import Callable, Mapping`; import `ClosureUnsupported` from `science.errors`; import `sealed` is already there. Add the constants after `_PEP_503_RUN`:

```python
SANDBOX_ENV = "/science/env"
SANDBOX_PYTHON = "/science/env/python"
SANDBOX_SITE = "/science/env/site"
SANDBOX_PATH = "/science/env/path"
SANDBOX_LIB = "/science/env/lib"
SANDBOX_VENV = "/science/env/venv"
_ELF_MAGIC = b"\x7fELF"
_PT_INTERP = 3
```

Replace `capture_environment` (keep `require_executing_environment` as it is) with the walker, the ELF and loader helpers, and the two capture entry points:

```python
@sealed
@final
@dataclass(frozen=True)
class CapturedEnvironment:
    """The closure as captured: the manifest, the ephemeral host plan for
    materializing it, the rendered rows, the loader path, the interpreter's
    sandbox path, and the loader map — (ELF, SONAME, resolved sandbox path)
    for every loadable ELF under the environment root — which the probe's
    in-layout listing must reproduce exactly (design §4.1–§4.2, §5.2–§5.3)."""

    manifest: EnvironmentManifest
    plan: Mapping[str, Path]
    rendered: tuple[tuple[str, str, str], ...]
    loader: str
    interpreter: str
    loader_map: tuple[tuple[str, str, str], ...]

    def __post_init__(self) -> None:
        if type(self.manifest) is not EnvironmentManifest:
            raise MalformedClosure("a captured environment carries an EnvironmentManifest")
        paths = {path for path, _, _ in self.manifest.artifacts}
        if set(self.plan) != paths:
            raise MalformedClosure("the capture plan covers exactly the manifest's rows")
        if not self.loader.startswith("/") or self.loader not in paths:
            raise MalformedClosure("the loader is an absolute path and a manifest row")
        for path in paths:
            if not (path.startswith(f"{SANDBOX_ENV}/") or path == self.loader):
                raise MalformedClosure(f"manifest row {path!r} lies outside {SANDBOX_ENV} and is not the loader")
        if self.interpreter not in paths:
            raise MalformedClosure("the interpreter is a manifest row")
        if set(rendered for rendered, _, _ in self.rendered) & paths:
            raise MalformedClosure("a rendered row may not shadow a manifest row")
        for elf, _, resolved in self.loader_map:
            if elf not in paths or resolved not in paths:
                raise MalformedClosure("the loader map names manifest rows only")
        object.__setattr__(self, "plan", MappingProxyType(dict(self.plan)))


def _located(host: Path) -> Path:
    """The path's own location: its parent resolved, its name kept — so a
    symlink is captured as the link, not as its target."""
    return Path(os.path.realpath(host.parent)) / host.name


def _path_tree_excluded(parts: tuple[str, ...]) -> bool:
    return ".git" in parts or _distribution_cache(parts)


def _import_names(line: str) -> list[str]:
    body = line[len("import"):].split(";", 1)[0]
    return [part.strip().split(" as ")[0].strip().split(".")[0] for part in body.split(",") if part.strip()]


class _Closure:
    """The walker. `rows` and `plan` are keyed by sandbox path; `rendered`
    holds the rows the boundary renders from the layout."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, str]] = {}
        self.plan: dict[str, Path] = {}
        self.rendered: dict[str, tuple[str, str]] = {}
        self.loader_map: list[tuple[str, str, str]] = []
        self._roots: list[tuple[Path, str]] = []

    def register(self, host_root: Path, sandbox_root: str) -> None:
        self._roots.append((Path(os.path.realpath(host_root)), sandbox_root))
        self._roots.sort(key=lambda pair: len(str(pair[0])), reverse=True)

    def root_of(self, located: Path) -> tuple[Path, str] | None:
        for host_root, sandbox_root in self._roots:
            if located.is_relative_to(host_root):
                return host_root, sandbox_root
        return None

    def sandbox_of(self, located: Path) -> str:
        root = self.root_of(located)
        if root is None:
            raise ClosureUnsupported(f"{located} lies outside every closure root")
        host_root, sandbox_root = root
        return f"{sandbox_root}/{located.relative_to(host_root).as_posix()}"

    def add(self, host: Path) -> str:
        """One row. A symlink's target is captured with it: a relative target
        staying under the link's own root keeps its relative text, any other
        in-closure target is rewritten to its sandbox path, a target outside
        every root escapes, and a target that names nothing is dangling."""
        located = _located(host)
        sandbox = self.sandbox_of(located)
        if sandbox in self.rows:
            return sandbox
        if located.is_symlink():
            target = os.readlink(located)
            target_host = _located(Path(os.path.normpath(target if os.path.isabs(target) else located.parent / target)))
            root = self.root_of(located)
            target_root = self.root_of(target_host)
            if target_root is None:
                raise ClosureUnsupported(f"symlink {located} -> {target!r} escapes the closure")
            same_root = not os.path.isabs(target) and root == target_root
            self.rows[sandbox] = ("symlink", target if same_root else self.sandbox_of(target_host))
            self.plan[sandbox] = located
            if target_host.is_symlink() or target_host.is_file():
                self.add(target_host)
            elif not target_host.is_dir():
                raise ClosureUnsupported(f"symlink {located} -> {target!r} names nothing")
            return sandbox
        if located.is_file():
            self.rows[sandbox] = ("file", _file_digest(located))
            self.plan[sandbox] = located
            return sandbox
        raise ClosureUnsupported(f"{located} is neither a regular file nor a symlink")

    def add_chain(self, host: Path) -> str:
        """Every link of a symlink chain as a symlink row and its terminal file
        as a file row; returns the terminal's sandbox path (design §4.2)."""
        located = _located(host)
        seen: set[Path] = set()
        while located.is_symlink():
            if located in seen:
                raise ClosureUnsupported(f"{host} is a symlink cycle")
            seen.add(located)
            self.add(located)
            target = os.readlink(located)
            located = _located(Path(os.path.normpath(target if os.path.isabs(target) else located.parent / target)))
        return self.add(located)

    def check_links(self) -> None:
        """Every symlink row resolves, within the sandbox layout, to a row or
        to a directory some row lies under — never to nothing."""
        for sandbox, (kind, content) in sorted(self.rows.items()):
            if kind != "symlink":
                continue
            resolved = content if content.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(sandbox), content))
            if resolved in self.rows or any(row.startswith(resolved + "/") for row in self.rows):
                continue
            raise ClosureUnsupported(f"symlink {sandbox} -> {content!r} resolves to {resolved}, which is not a closure row")

    def add_tree(self, root: Path, *, excluded: Callable[[tuple[str, ...]], bool]) -> None:
        for path in sorted(root.rglob("*")):
            if excluded(path.relative_to(root).parts):
                continue
            if path.is_symlink() or path.is_file():
                self.add(path)

    def add_records(self) -> None:
        for dist in importlib.metadata.distributions():
            name = dist.metadata["Name"]
            record = dist.read_text("RECORD")
            if not record:
                raise MalformedClosure(f"distribution {name!r} has no readable RECORD — its inventory cannot be enumerated")
            for row in csv.reader(record.splitlines()):
                if not row or not row[0]:
                    raise MalformedClosure(f"distribution {name!r} has a malformed RECORD entry")
                entry = importlib.metadata.PackagePath(row[0])
                if _distribution_cache(entry.parts) or entry.suffix == ".pth":
                    continue
                located = Path(os.path.normpath(str(dist.locate_file(entry))))
                if not located.is_file() and not located.is_symlink():
                    raise MalformedClosure(f"distribution {name!r}: RECORD lists {entry} and no such file exists")
                self.add(located)

    def add_pth(self, purelib: Path) -> None:
        for pth in sorted(purelib.glob("*.pth")):
            lines = [line for line in pth.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
            imports = [line for line in lines if line.startswith(("import ", "import\t"))]
            paths = [line for line in lines if line not in imports]
            if imports and paths:
                raise ClosureUnsupported(f"{pth.name} mixes import lines and path lines")
            if paths:
                targets = []
                for ordinal, line in enumerate(paths):
                    tree = Path(line.strip())
                    if not tree.is_absolute() or not tree.is_dir():
                        raise ClosureUnsupported(f"{pth.name} line {ordinal} names {line!r}, not an absolute directory")
                    sandbox_root = f"{SANDBOX_PATH}/{pth.name}/{ordinal}"
                    self.register(tree, sandbox_root)
                    self.add_tree(tree, excluded=_path_tree_excluded)
                    targets.append(sandbox_root)
                self.rendered[f"{SANDBOX_SITE}/{pth.name}"] = ("file", "".join(f"{target}\n" for target in targets))
                continue
            self.add(pth)
            for line in imports:
                for module in _import_names(line):
                    if f"{SANDBOX_SITE}/{module}.py" in self.rows or f"{SANDBOX_SITE}/{module}/__init__.py" in self.rows:
                        continue
                    candidate = purelib / f"{module}.py"
                    if candidate.is_file():
                        self.add(candidate)
                        continue
                    raise ClosureUnsupported(f"{pth.name} imports {module!r}, which is not a closure member")

    def add_native(self, *, listing: Callable[[Path], Mapping[str, Path]]) -> None:
        """The loader's own resolution for every loadable ELF under the
        environment root, closed to a fixpoint over the libraries it adds, and
        the expected map row for each — what the probe must reproduce."""
        listed: set[str] = set()
        while pending := [(sandbox, host) for sandbox, host in self.elves() if sandbox not in listed]:
            for elf_sandbox, elf in pending:
                listed.add(elf_sandbox)
                for soname, host in sorted(listing(elf).items()):
                    located = _located(host)
                    if self.root_of(located) is not None:
                        resolved = self.add(located)
                    else:
                        resolved = f"{SANDBOX_LIB}/{soname}"
                        existing = self.plan.get(resolved)
                        if existing is not None and existing != located:
                            raise ClosureUnsupported(f"SONAME {soname!r} resolves to both {existing} and {located}")
                        self.rows[resolved] = ("file", _file_digest(located))
                        self.plan[resolved] = located
                    self.loader_map.append((elf_sandbox, soname, resolved))

    def elves(self) -> list[tuple[str, Path]]:
        """Every loadable ELF file row under the environment root, by sandbox
        path — the same set the probe enumerates in-layout."""
        return [
            (path, self.plan[path])
            for path, (kind, _) in sorted(self.rows.items())
            if kind == "file" and path.startswith(f"{SANDBOX_ENV}/") and _is_loadable_elf(self.plan[path])
        ]


def _is_loadable_elf(path: Path) -> bool:
    """ELF of type ET_EXEC or ET_DYN — what `ld.so --list` can list; a
    relocatable object is not."""
    with path.open("rb") as handle:
        header = handle.read(18)
    return len(header) == 18 and header[:4] == _ELF_MAGIC and struct.unpack_from("<H", header, 16)[0] in (2, 3)


def elf_interpreter(path: Path) -> str:
    """PT_INTERP, read from the ELF program headers; nothing is hardcoded."""
    with path.open("rb") as handle:
        header = handle.read(64)
        if header[:4] != _ELF_MAGIC:
            raise ClosureUnsupported(f"{path} is not an ELF file")
        if header[5] != 1:
            raise ClosureUnsupported(f"{path} is not little-endian")
        if header[4] == 2:
            (phoff,) = struct.unpack_from("<Q", header, 0x20)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x36)
        elif header[4] == 1:
            (phoff,) = struct.unpack_from("<I", header, 0x1C)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x2A)
        else:
            raise ClosureUnsupported(f"{path} has an unknown ELF class")
        for index in range(phnum):
            handle.seek(phoff + index * phentsize)
            phdr = handle.read(phentsize)
            if struct.unpack_from("<I", phdr, 0)[0] != _PT_INTERP:
                continue
            if header[4] == 2:
                (offset,) = struct.unpack_from("<Q", phdr, 8)
                (size,) = struct.unpack_from("<Q", phdr, 32)
            else:
                (offset,) = struct.unpack_from("<I", phdr, 4)
                (size,) = struct.unpack_from("<I", phdr, 16)
            handle.seek(offset)
            return handle.read(size).rstrip(b"\0").decode("ascii")
    raise ClosureUnsupported(f"{path} names no program interpreter")


def _parse_listing(text: str) -> dict[str, Path]:
    listing: dict[str, Path] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith(("linux-vdso", "linux-gate")) or parts[0].startswith("/"):
            continue
        if len(parts) < 3 or parts[1] != "=>":
            raise ClosureUnsupported(f"unparseable loader line {line!r}")
        if parts[2] == "not":
            raise ClosureUnsupported(f"{parts[0]} does not resolve on this host")
        listing[parts[0]] = Path(parts[2])
    return listing


def loader_listing(loader: str, path: Path) -> dict[str, Path]:
    """What `execve` will map for `path`, as the loader itself reports it —
    under an empty environment, so no ambient LD_LIBRARY_PATH or LD_PRELOAD
    shapes the capture (design §5.3)."""
    completed = subprocess.run([loader, "--list", str(path)], capture_output=True, text=True, check=False, env={})
    if completed.returncode != 0:
        raise ClosureUnsupported(f"the loader cannot list {path}: {completed.stderr.strip()}")
    return _parse_listing(completed.stdout)


def capture_closure() -> CapturedEnvironment:
    walker = _Closure()
    base = Path(os.path.realpath(sys.base_prefix))
    prefix = Path(os.path.realpath(sys.prefix))
    purelib = Path(os.path.realpath(sysconfig.get_path("purelib")))
    walker.register(base, SANDBOX_PYTHON)
    if prefix != base:
        walker.register(prefix, SANDBOX_VENV)
    walker.register(purelib, SANDBOX_SITE)
    interpreter = walker.add_chain(Path(sys.executable))
    interpreter_host = walker.plan[interpreter]
    if not interpreter_host.is_relative_to(base):
        raise ClosureUnsupported(f"the interpreter {interpreter_host} is outside its base prefix {base}")
    for name in ("stdlib", "platstdlib"):
        walker.add_tree(Path(os.path.realpath(sysconfig.get_path(name))), excluded=_stdlib_excluded)
    walker.add_records()
    walker.add_pth(purelib)
    loader = elf_interpreter(interpreter_host)
    walker.add_native(listing=lambda elf: loader_listing(loader, elf))
    walker.rows[loader] = ("file", _file_digest(Path(loader)))
    walker.plan[loader] = Path(loader)
    walker.check_links()
    version_dir = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    walker.rendered[f"{SANDBOX_VENV}/pyvenv.cfg"] = ("file", f"home = {SANDBOX_PYTHON}/bin\ninclude-system-site-packages = false\n")
    if f"{SANDBOX_VENV}/bin/python" not in walker.rows:
        walker.rendered[f"{SANDBOX_VENV}/bin/python"] = ("symlink", interpreter)
    walker.rendered[f"{SANDBOX_VENV}/lib/{version_dir}/site-packages"] = ("symlink", SANDBOX_SITE)
    return CapturedEnvironment(
        manifest=EnvironmentManifest(artifacts=tuple(sorted((path, kind, content) for path, (kind, content) in walker.rows.items()))),
        plan=walker.plan,
        rendered=tuple(sorted((path, kind, content) for path, (kind, content) in walker.rendered.items())),
        loader=loader,
        interpreter=interpreter,
        loader_map=tuple(sorted(walker.loader_map)),
    )


def capture_environment() -> EnvironmentManifest:
    return capture_closure().manifest
```

`_stdlib_excluded` and `_distribution_cache` stay. Add `from types import MappingProxyType` (already imported) — check the imports compile.

Replace `build_argv` with:

```python
def build_argv(
    *,
    interpreter: str,
    snakefile: str,
    directory: str,
    targets: tuple[str, ...],
    config: Mapping[str, str],
    log_handler: str,
    cores: int,
    in_process_jobs: bool,
) -> tuple[str, ...]:
    """Policy-neutral: the minimal policy supplies host paths, the confined
    policy sandbox paths. `in_process_jobs` adds `--force-use-threads`, under
    which Snakemake executes `run:` rules in-process instead of re-spawning
    itself through `/bin/sh` (design §5.5)."""
    for target in targets:
        if target.startswith("-"):
            raise UnsafeInvocation(
                f"target {target!r} is option-like; shell=False prevents shell injection, "
                "not option injection — targets are separated from options (cut 3 §3)"
            )
    for key in config:
        if not _CONFIG_KEY.fullmatch(key):
            raise UnsafeInvocation(f"config key {key!r} is not an identifier and could parse as an option")
    argv = [
        interpreter,
        "-m",
        "snakemake",
        "--snakefile",
        snakefile,
        "--cores",
        str(cores),
        "--directory",
        directory,
        "--nolock",
    ]
    if in_process_jobs:
        argv.append("--force-use-threads")
    argv.extend(["--log-handler-script", log_handler])
    if config:
        argv.append("--config")
        argv.extend(f"{key}={value}" for key, value in sorted(config.items()))
    argv.append("--")
    argv.extend(targets)
    return tuple(argv)
```

In `python/src/science/boundary.py` the minimal call becomes:

```python
        argv = build_argv(
            interpreter=sys.executable,
            snakefile=str(captured_entrypoint),
            directory=str(scratch),
            targets=targets,
            config=config,
            log_handler=str(handler),
            cores=cores,
            in_process_jobs=False,
        )
```

(add `import sys` to `boundary.py`). Update the `build_argv` calls in `python/tests/test_adapter.py` and any other test to the new keywords (`grep -rn "build_argv(" python/tests`), passing `interpreter=sys.executable`, `str(...)` paths, and `in_process_jobs=False`.

- [ ] **Step 4: Move every fixture manifest to the v2 row shape**

```bash
grep -rn "EnvironmentManifest(" python/tests python/src | grep -v "type(self.environment)"
```

For each construction that passes `(label, digest)` pairs, rewrite the row as `("/science/env/" + label, "file", digest)`. Known sites: `python/tests/fixtures_cut3.py:118` becomes `"environment": EnvironmentManifest(artifacts=(("/science/env/python/bin/python3", "file", "sha256:" + "dd" * 32),)),`; `python/tests/closure_fixtures.py` and `python/tests/test_recipe.py` carry the same shape — apply the same rewrite. A test that asserts the v1 domain string `science.environment.v1` or a pair row's refusal is rewritten to the v2 equivalent, not deleted. This step and Step 3 land in one commit: the production capture and every consumer of its shape move together.

- [ ] **Step 5: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_closure_capture.py tests/test_adapter.py tests/test_recipe.py tests/test_confinement_values.py tests/test_boundary.py tests/test_replay.py tests/test_verify.py tests/test_run_persistence.py tests/test_assess.py tests/test_production.py tests/test_decode.py | tail -1 && uv run pytest tests/test_n2.py -k stale | tail -1 && uv run ruff check src/science/recipe.py src/science/adapter.py src/science/boundary.py tests && uv run pyright src/science/recipe.py src/science/adapter.py | tail -1`
Expected: all passed (the durable `test_run_persistence.py` tests fail only with the host's allowlist refusal — confirm every failure message is `CapabilityUnavailable: volume configuration is not on the supplied durability allowlist`, and nothing else); no stale anchors; clean; `0 errors`. The closure walk digests the whole runtime, so the boundary tests get slower — a run is now roughly three digest passes (design §4.4); note the time in the ledger if it exceeds 2× cut 3's.

- [ ] **Step 6: Commit**

```bash
git add python/src/science/recipe.py python/src/science/adapter.py python/src/science/boundary.py python/tests
git commit -m "feat(adapter): capture the runtime artifact closure per file under environment.v2 and make the engine argv policy-neutral"
```

---

### Task 6: `confinement.py` and `probe.py` — snapshot, mount plan, the gated launch, the observation

**Files:**
- Create: `python/src/science/confinement.py`
- Create: `python/src/science/probe.py`
- Modify: `python/tests/test_capability_boundary.py:453-464` (`RAW_WRITE_ALLOWLIST`) and `:547` (its equality assertion)
- Test: `python/tests/test_confinement.py`

**Interfaces:**
- Produces (`science.confinement`): constants `HOSTNAME`, `BUNDLE_ROOT`, `OUTPUT_ROOT`, `INPUTS_ROOT`, `TRACE_DIR`, `HOME_DIR`, `DEVICES`, `UNPLANNED`; `sandbox_environment(trace_file) -> tuple[tuple[str, str], ...]`; `host_prerequisites() -> str | None`, `require_host()`; `materialize_snapshot(captured, environments) -> Path` (its verification of an existing or fresh snapshot **is** the pre-bind snapshot observation), `verify_snapshot(root, captured)`; `bundle_identity(bundle) -> str`, `fingerprint(root) -> str`, `check_bundle_intact(bundle, code_identity)`, `check_closure_intact(*, bundle, code_identity, snapshot, captured, inputs, inputs_fingerprint)` (the post-exit observation: one pass each); `MountPlan` (`binds`, `roles`, `loader`, `rows`, `expected` — the sorted rows —, `role_of(mountpoint)`, `identity()`, `host_mapping()`), `mount_plan(*, snapshot, loader, bundle, output_root)`; `bwrap_argv(...)`; `canonical_mounts(mountinfo, plan) -> tuple[tuple[str, str, str], ...]` (every row kept, classified by planned role); `InstanceFacts(distinct, mounts)`, `observe_instance(pid, plan)`; `judge_instance(facts, plan)`, `judge_report(report, *, environment, captured, inner_argv) -> tuple[str, ...]`; `Launch`, `launch_confined(*, plan, environment, inner_argv, captured) -> Launch` — every launch or protocol failure is `ConfinementNotEstablished`, with the child terminated and reaped and every descriptor closed.
- Produces (`science.probe`): `main(argv) -> int`, run as `python -m science.probe --report-fd R --go-fd G --loader L -- <engine argv>`; its report's `loader` member is `{elf: {"returncode": int, "resolved": {soname: [path, digest]}, "unresolved": [line, ...]}}` over every loadable ELF under `/science/env`.
- Consumes: Task 2's errors; Task 3's `CAPABILITIES`, `NAMESPACES`, `mount_plan_identity`; Task 5's `CapturedEnvironment` (with `loader_map`), sandbox constants, `elf_interpreter`, `loader_listing`, `_fold`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_confinement.py`:

```python
"""The confined boundary's machinery over synthetic inputs: the snapshot (K2),
the canonical mount comparison and the judgement (K6), fingerprints, the
declared environment, and the bwrap argv shape (design §4.3–§6)."""

import os
from hashlib import sha256
from pathlib import Path

import pytest

from science.adapter import SANDBOX_ENV, SANDBOX_LIB, SANDBOX_VENV, CapturedEnvironment, capture_bundle
import science.confinement as confinement_module
from science.confinement import (
    BUNDLE_ROOT,
    HOSTNAME,
    INPUTS_ROOT,
    OUTPUT_ROOT,
    UNPLANNED,
    InstanceFacts,
    MountPlan,
    bundle_identity,
    bwrap_argv,
    canonical_mounts,
    check_bundle_intact,
    check_closure_intact,
    fingerprint,
    judge_instance,
    judge_report,
    launch_confined,
    materialize_snapshot,
    mount_plan,
    sandbox_environment,
    verify_snapshot,
)
from science.errors import ClosureMutated, ConfinementNotEstablished, SnapshotMismatch
from science.recipe import CAPABILITIES, NAMESPACES, EnvironmentManifest, mount_plan_identity

LOADER = "/lib64/ld-linux-x86-64.so.2"


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def synthetic(tmp_path: Path) -> CapturedEnvironment:
    host = tmp_path / "host"
    host.mkdir()
    (host / "ld.so").write_bytes(b"loader")
    (host / "python3").write_bytes(b"interpreter")
    (host / "liba.so.1").write_bytes(b"liba")
    (host / "libc.so.6").write_bytes(b"libc")
    interpreter = "/science/env/python/bin/python3"
    manifest = EnvironmentManifest(
        artifacts=(
            (LOADER, "file", _digest(b"loader")),
            (interpreter, "file", _digest(b"interpreter")),
            ("/science/env/python/lib/liba.so", "symlink", "liba.so.1"),
            ("/science/env/python/lib/liba.so.1", "file", _digest(b"liba")),
            (f"{SANDBOX_LIB}/libc.so.6", "file", _digest(b"libc")),
        )
    )
    plan = {
        LOADER: host / "ld.so",
        interpreter: host / "python3",
        "/science/env/python/lib/liba.so": host / "liba.so.1",
        "/science/env/python/lib/liba.so.1": host / "liba.so.1",
        f"{SANDBOX_LIB}/libc.so.6": host / "libc.so.6",
    }
    rendered = (
        (f"{SANDBOX_VENV}/bin/python", "symlink", interpreter),
        (f"{SANDBOX_VENV}/pyvenv.cfg", "file", "home = /science/env/python/bin\ninclude-system-site-packages = false\n"),
    )
    loader_map = ((interpreter, "libc.so.6", f"{SANDBOX_LIB}/libc.so.6"),)
    return CapturedEnvironment(manifest=manifest, plan=plan, rendered=rendered, loader=LOADER, interpreter=interpreter, loader_map=loader_map)


# --- K2: the snapshot ---------------------------------------------------------
def test_a_snapshot_is_built_verified_and_published_under_its_environment_identity(tmp_path):
    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    snapshot = materialize_snapshot(captured, environments)
    assert snapshot == environments / captured.manifest.identity()
    assert (snapshot / "science/env/python/bin/python3").read_bytes() == b"interpreter"
    assert os.readlink(snapshot / "science/env/python/lib/liba.so") == "liba.so.1"
    assert (snapshot / "science/env/venv/pyvenv.cfg").read_text().startswith("home = ")
    assert os.readlink(snapshot / "science/env/venv/bin/python") == captured.interpreter
    verify_snapshot(snapshot, captured)
    assert materialize_snapshot(captured, environments) == snapshot
    assert not [entry for entry in environments.iterdir() if ".build-" in entry.name]


def test_k2_an_existing_mismatching_snapshot_refuses_and_is_never_rebuilt(tmp_path):
    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    snapshot = materialize_snapshot(captured, environments)
    corrupt = snapshot / "science/env/lib/libc.so.6"
    corrupt.write_bytes(b"CORRUPT")
    inode = corrupt.stat().st_ino
    with pytest.raises(SnapshotMismatch):
        materialize_snapshot(captured, environments)
    assert corrupt.read_bytes() == b"CORRUPT" and corrupt.stat().st_ino == inode


def test_a_snapshot_with_an_unmanifested_file_or_a_missing_row_refuses(tmp_path):
    captured = synthetic(tmp_path)
    snapshot = materialize_snapshot(captured, tmp_path / "environments")
    (snapshot / "science/env/extra").write_bytes(b"x")
    with pytest.raises(SnapshotMismatch, match="extra"):
        verify_snapshot(snapshot, captured)
    (snapshot / "science/env/extra").unlink()
    (snapshot / "science/env/lib/libc.so.6").unlink()
    with pytest.raises(SnapshotMismatch, match="missing"):
        verify_snapshot(snapshot, captured)


def test_k2_a_concurrent_winner_is_verified_and_reused_or_refused(tmp_path, monkeypatch):
    import shutil

    captured = synthetic(tmp_path)
    environments = tmp_path / "environments"
    target = environments / captured.manifest.identity()
    original_rename = Path.rename

    def lose_to_a_winner(self: Path, destination):
        if self.parent == environments and self.name.startswith(f"{target.name}.build-"):
            shutil.copytree(self, target, symlinks=True)
            raise OSError("a winner published first")
        return original_rename(self, destination)

    monkeypatch.setattr(Path, "rename", lose_to_a_winner)
    assert materialize_snapshot(captured, environments) == target
    assert not [entry for entry in environments.iterdir() if ".build-" in entry.name]

    shutil.rmtree(target)

    def lose_to_a_corrupt_winner(self: Path, destination):
        if self.parent == environments and self.name.startswith(f"{target.name}.build-"):
            shutil.copytree(self, target, symlinks=True)
            (target / "science/env/lib/libc.so.6").write_bytes(b"CORRUPT")
            raise OSError("a corrupt winner published first")
        return original_rename(self, destination)

    monkeypatch.setattr(Path, "rename", lose_to_a_corrupt_winner)
    with pytest.raises(SnapshotMismatch):
        materialize_snapshot(captured, environments)


# --- integrity ----------------------------------------------------------------
def test_bundle_identity_recomputes_capture_bundles_fold_and_moves_on_an_edit(tmp_path):
    root = tmp_path / "code"
    (root / "workflow").mkdir(parents=True)
    (root / "workflow" / "Snakefile").write_text("rule a: pass\n")
    (root / "helper.py").write_text("VALUE = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    assert bundle_identity(bundle) == code_identity
    (bundle / "code" / "helper.py").write_text("VALUE = 2\n")
    assert bundle_identity(bundle) != code_identity


def test_check_bundle_intact_refuses_an_edited_bundle(tmp_path):
    root = tmp_path / "code"
    root.mkdir()
    (root / "a.py").write_text("A = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    check_bundle_intact(bundle, code_identity)
    (bundle / "code" / "a.py").write_text("A = 2\n")
    with pytest.raises(ClosureMutated, match="bundle"):
        check_bundle_intact(bundle, code_identity)


def test_check_closure_intact_refuses_an_edited_bundle_a_moved_snapshot_and_changed_inputs(tmp_path):
    captured = synthetic(tmp_path)
    snapshot = materialize_snapshot(captured, tmp_path / "environments")
    root = tmp_path / "code"
    root.mkdir()
    (root / "a.py").write_text("A = 1\n")
    bundle = tmp_path / "bundle"
    code_identity = capture_bundle((root,), bundle)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "data.txt").write_text("x\n")
    before = fingerprint(inputs)

    def check() -> None:
        check_closure_intact(
            bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=inputs, inputs_fingerprint=before
        )

    check()
    (bundle / "code" / "a.py").write_text("A = 2\n")
    with pytest.raises(ClosureMutated, match="bundle"):
        check()
    (bundle / "code" / "a.py").write_text("A = 1\n")
    (snapshot / "science/env/lib/libc.so.6").write_bytes(b"MOVED")
    with pytest.raises(ClosureMutated, match="snapshot"):
        check()
    (snapshot / "science/env/lib/libc.so.6").write_bytes(b"libc")
    (inputs / "data.txt").write_text("y\n")
    with pytest.raises(ClosureMutated, match="inputs"):
        check()


def test_fingerprints_move_with_content_and_symlink_targets(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a").write_bytes(b"a")
    (tree / "link").symlink_to("a")
    before = fingerprint(tree)
    (tree / "a").write_bytes(b"b")
    assert fingerprint(tree) != before
    (tree / "a").write_bytes(b"a")
    assert fingerprint(tree) == before
    (tree / "link").unlink()
    (tree / "link").symlink_to("b")
    assert fingerprint(tree) != before


# --- the mount plan and the canonical comparison (K6) -------------------------
def _plan(tmp_path: Path) -> MountPlan:
    return mount_plan(snapshot=tmp_path / "snap", loader=LOADER, bundle=tmp_path / "bundle", output_root=tmp_path / "out")


def test_the_mount_plan_rows_are_canonical_and_identity_bearing(tmp_path):
    plan = _plan(tmp_path)
    assert plan.rows == (
        ("/", "root", "ro"),
        (LOADER, "loader", "ro"),
        (SANDBOX_ENV, "env", "ro"),
        (BUNDLE_ROOT, "bundle", "ro"),
        (OUTPUT_ROOT, "output", "rw"),
        (INPUTS_ROOT, "inputs", "ro"),
        ("/dev/null", "device", "rw"),
        ("/dev/urandom", "device", "rw"),
    )
    assert plan.identity() == mount_plan_identity(plan.rows)
    assert plan.expected == tuple(sorted(plan.rows))
    assert plan.role_of(BUNDLE_ROOT) == "bundle" and plan.role_of("/dev/null") == "device" and plan.role_of("/etc") == UNPLANNED
    assert dict(plan.host_mapping())[BUNDLE_ROOT] == str(tmp_path / "bundle")
    assert dict(plan.host_mapping())[SANDBOX_ENV] == str(tmp_path / "snap" / "science" / "env")
    assert dict(plan.host_mapping())[LOADER] == str(tmp_path / "snap" / LOADER.lstrip("/"))


def test_canonical_mounts_keeps_every_row_classifies_by_planned_role_and_unescapes(tmp_path):
    plan = _plan(tmp_path)
    text = (
        "1 0 0:1 / / ro,nosuid - tmpfs tmpfs rw\n"
        "2 1 8:1 /scratch/out /science/out rw,relatime - ext4 /dev/sda1 rw\n"
        "3 2 8:1 /scratch/out/in /science/out/inputs ro,relatime - ext4 /dev/sda1 rw\n"
        "4 2 8:1 /scratch/out/in /science/out/inputs ro,relatime - ext4 /dev/sda1 rw\n"
        "5 1 8:1 /x/with\\040space /science/with\\040space ro - ext4 /dev/sda1 rw\n"
    )
    assert canonical_mounts(text, plan) == (
        ("/", "root", "ro"),
        ("/science/out", "output", "rw"),
        ("/science/out/inputs", "inputs", "ro"),
        ("/science/out/inputs", "inputs", "ro"),
        ("/science/with space", UNPLANNED, "ro"),
    )


def test_k6_a_namespace_equal_to_the_parents_refuses(tmp_path):
    plan = _plan(tmp_path)
    facts = InstanceFacts(distinct=tuple(name for name in NAMESPACES if name != "net"), mounts=plan.expected)
    with pytest.raises(ConfinementNotEstablished, match="net"):
        judge_instance(facts, plan)
    judge_instance(InstanceFacts(distinct=NAMESPACES, mounts=plan.expected), plan)


def test_k6_a_mount_table_unequal_to_the_plan_refuses(tmp_path):
    plan = _plan(tmp_path)
    extra = InstanceFacts(distinct=NAMESPACES, mounts=tuple(sorted((*plan.expected, ("/etc", UNPLANNED, "ro")))))
    with pytest.raises(ConfinementNotEstablished, match="/etc"):
        judge_instance(extra, plan)
    stacked = InstanceFacts(distinct=NAMESPACES, mounts=tuple(sorted((*plan.expected, (INPUTS_ROOT, "inputs", "ro")))))
    with pytest.raises(ConfinementNotEstablished, match="observed rows"):
        judge_instance(stacked, plan)
    missing = InstanceFacts(distinct=NAMESPACES, mounts=tuple(row for row in plan.expected if row[0] != INPUTS_ROOT))
    with pytest.raises(ConfinementNotEstablished, match="inputs"):
        judge_instance(missing, plan)
    writable_root = InstanceFacts(
        distinct=NAMESPACES, mounts=tuple(sorted(("/", "root", "rw") if row[0] == "/" else row for row in plan.expected))
    )
    with pytest.raises(ConfinementNotEstablished):
        judge_instance(writable_root, plan)


def good_report(captured: CapturedEnvironment, environment) -> dict:
    return {
        "environ": dict(environment),
        "hostname": HOSTNAME,
        "cwd": OUTPUT_ROOT,
        "filesystem": {
            "read:/etc/passwd": "ENOENT",
            "read:/tmp": "ENOENT",
            "write:/": "EROFS",
            f"write:{BUNDLE_ROOT}": "EROFS",
            f"write:{SANDBOX_ENV}": "EROFS",
            f"write:{INPUTS_ROOT}": "EROFS",
            f"write:{OUTPUT_ROOT}": "OK",
        },
        "network": {"ipv4": "ENETUNREACH", "ipv6": "EAFNOSUPPORT"},
        "loader": {
            captured.interpreter: {
                "returncode": 0,
                "resolved": {"libc.so.6": [f"{SANDBOX_LIB}/libc.so.6", _digest(b"libc")]},
                "unresolved": [],
            }
        },
    }


def _entry(report: dict) -> dict:
    return report["loader"][next(iter(report["loader"]))]


INNER = ("/science/env/venv/bin/python", "-m", "snakemake", "--snakefile", f"{BUNDLE_ROOT}/code/workflow/Snakefile", "--", "outputs/result.txt")


def test_a_good_report_yields_every_capability(tmp_path):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    assert judge_report(good_report(captured, environment), environment=environment, captured=captured, inner_argv=INNER) == CAPABILITIES


@pytest.mark.parametrize(
    "mutate, match",
    [
        (lambda r: r["environ"].update({"HOSTTYPE": "x86_64"}), "environment"),
        (lambda r: r.update({"hostname": "laptop"}), "hostname"),
        (lambda r: r.update({"cwd": "/"}), "cwd"),
        (lambda r: r["filesystem"].update({"read:/etc/passwd": "READ"}), "filesystem"),
        (lambda r: r["filesystem"].update({f"write:{BUNDLE_ROOT}": "OK"}), "filesystem"),
        (lambda r: r["network"].update({"ipv4": "ECONNREFUSED"}), "network"),
        (lambda r: r["network"].update({"ipv6": "CONNECTED"}), "network"),
        (lambda r: _entry(r)["resolved"].update({"libc.so.6": [f"{SANDBOX_LIB}/libc.so.6", _digest(b"other")]}), "loader"),
        (lambda r: _entry(r)["resolved"].update({"libc.so.6": ["/science/env/python/lib/libc.so.6", _digest(b"libc")]}), "loader"),
        (lambda r: r["loader"].clear(), "loader"),  # an omitted ELF
        (lambda r: _entry(r)["resolved"].clear(), "loader"),  # an omitted SONAME
        (lambda r: _entry(r)["resolved"].update({"libm.so.6": [f"{SANDBOX_LIB}/libm.so.6", _digest(b"m")]}), "loader"),  # an extra SONAME
        (lambda r: _entry(r)["unresolved"].append("libm.so.6 => not found"), "loader"),  # not found
        (lambda r: _entry(r).update({"returncode": 127}), "loader"),  # a nonzero loader exit
        (lambda r: r["loader"].update({"/science/env/site/extra.so": dict(_entry(r))}), "loader"),  # an extra ELF
    ],
)
def test_k6_each_report_deviation_refuses(tmp_path, mutate, match):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    report = good_report(captured, environment)
    mutate(report)
    with pytest.raises(ConfinementNotEstablished, match=match):
        judge_report(report, environment=environment, captured=captured, inner_argv=INNER)


def test_an_engine_argv_whose_snakefile_is_outside_the_bundle_refuses(tmp_path):
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    outside = tuple("/science/out/Snakefile" if part.startswith(BUNDLE_ROOT) else part for part in INNER)
    with pytest.raises(ConfinementNotEstablished, match="bundle"):
        judge_report(good_report(captured, environment), environment=environment, captured=captured, inner_argv=outside)


@pytest.mark.parametrize("broken", [lambda r: r.pop("network"), lambda r: r.update({"environ": "not a mapping"}), lambda r: r.update({"loader": None})])
def test_a_malformed_report_shape_is_not_a_traceback_of_its_own(tmp_path, broken):
    """judge_report may raise KeyError or TypeError on a malformed shape; the
    launch wraps those (below). Here: it never returns capabilities for one."""
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    report = good_report(captured, environment)
    broken(report)
    with pytest.raises((ConfinementNotEstablished, KeyError, TypeError, AttributeError)):
        judge_report(report, environment=environment, captured=captured, inner_argv=INNER)


# --- the launch's failure boundary --------------------------------------------
def test_a_launch_protocol_failure_is_confinement_not_established_and_the_child_is_reaped(tmp_path, monkeypatch):
    """A stand-in bubblewrap that writes garbage on the info descriptor and then
    sleeps: the launch refuses with the stable reason, terminates and reaps the
    child, and leaves no descriptor open (design §8)."""
    import sys

    pid_file = tmp_path / "pid"
    fake = tmp_path / "bwrap"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import os, sys, time\n"
        "info = int(sys.argv[sys.argv.index('--info-fd') + 1])\n"
        "os.write(info, b'not json at all')\n"
        "os.close(info)\n"
        f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
        "time.sleep(60)\n"
    )
    fake.chmod(0o755)
    monkeypatch.setattr(confinement_module, "_BWRAP", str(fake))
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    open_before = set(os.listdir("/proc/self/fd"))
    with pytest.raises(ConfinementNotEstablished, match="info descriptor"):
        launch_confined(plan=_plan(tmp_path), environment=environment, inner_argv=INNER, captured=captured)
    assert set(os.listdir("/proc/self/fd")) <= open_before
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def test_bubblewrap_gone_after_intent_is_confinement_not_established_not_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(confinement_module, "_BWRAP", str(tmp_path / "no-such-bwrap"))
    captured = synthetic(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    with pytest.raises(ConfinementNotEstablished, match="PATH"):
        launch_confined(plan=_plan(tmp_path), environment=environment, inner_argv=INNER, captured=captured)


# --- the declared environment and the bwrap argv -----------------------------
def test_the_declared_environment_is_exactly_the_specs_set():
    assert sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl") == (
        ("HOME", "/science/out/.home"),
        ("LC_CTYPE", "C.UTF-8"),
        ("LD_LIBRARY_PATH", "/science/env/lib"),
        ("PATH", "/science/env/venv/bin"),
        ("PWD", "/science/out"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONHASHSEED", "0"),
        ("PYTHONNOUSERSITE", "1"),
        ("PYTHONSAFEPATH", "1"),
        ("SCIENCE_TRACE_FILE", "/science/out/.trace/events.jsonl"),
    )


def test_the_bwrap_argv_binds_then_remounts_the_root_read_only_and_gates_through_the_probe(tmp_path):
    plan = _plan(tmp_path)
    environment = sandbox_environment(f"{OUTPUT_ROOT}/.trace/events.jsonl")
    argv = bwrap_argv(plan, environment, INNER, bwrap="/usr/bin/bwrap", info_fd=7, report_fd=8, go_fd=9)
    assert argv[:2] == ("/usr/bin/bwrap", "--unshare-all")
    for flag in ("--die-with-parent", "--new-session", "--clearenv", "--hostname", "--info-fd"):
        assert flag in argv
    assert argv[argv.index("--hostname") + 1] == HOSTNAME
    remount = argv.index("--remount-ro")
    assert argv[remount + 1] == "/"
    assert max(index for index, part in enumerate(argv) if part in ("--ro-bind", "--bind", "--dev-bind")) < remount
    assert argv[argv.index("--chdir") + 1] == OUTPUT_ROOT
    assert ("--setenv", "PYTHONSAFEPATH", "1") == argv[argv.index("PYTHONSAFEPATH") - 1 : argv.index("PYTHONSAFEPATH") + 2]
    separator = argv.index("--")
    assert argv[separator + 1 : separator + 4] == (f"{SANDBOX_VENV}/bin/python", "-m", "science.probe")
    assert argv[-len(INNER):] == INNER
    assert ("--report-fd", "8") == argv[argv.index("--report-fd") : argv.index("--report-fd") + 2]
    assert ("--go-fd", "9") == argv[argv.index("--go-fd") : argv.index("--go-fd") + 2]
    assert "--proc" not in argv and "--dev" not in argv
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_confinement.py | tail -3`
Expected: FAIL — `ModuleNotFoundError: No module named 'science.confinement'`.

- [ ] **Step 3: Write `confinement.py`**

`python/src/science/confinement.py`:

```python
"""The confined boundary policy's machinery (run-confinement design §4.3–§6).

The snapshot and its verification, the mount plan, the bubblewrap launch gated
by the held probe, the boundary-side observation of the child's namespaces and
mounts from this process's own ``/proc``, and the judgement that turns the
probe's report and that observation into the capabilities the receipt attests.
Nothing here reads the requested policy's capabilities: what the receipt says
is what was observed.
"""

from __future__ import annotations

import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import cast, final

from science.adapter import (
    SANDBOX_ENV,
    SANDBOX_LIB,
    SANDBOX_VENV,
    CapturedEnvironment,
    _fold,
    elf_interpreter,
    loader_listing,
)
from science.errors import (
    ClosureMutated,
    ClosureUnsupported,
    ConfinementNotEstablished,
    ConfinementUnavailable,
    SnapshotMismatch,
)
from science.recipe import CAPABILITIES, NAMESPACES, mount_plan_identity
from science.sealed import sealed

__all__ = [
    "BUNDLE_ROOT",
    "DEVICES",
    "HOME_DIR",
    "HOSTNAME",
    "INPUTS_ROOT",
    "OUTPUT_ROOT",
    "TRACE_DIR",
    "UNPLANNED",
    "InstanceFacts",
    "Launch",
    "MountPlan",
    "bundle_identity",
    "bwrap_argv",
    "canonical_mounts",
    "check_bundle_intact",
    "check_closure_intact",
    "fingerprint",
    "host_prerequisites",
    "judge_instance",
    "judge_report",
    "launch_confined",
    "materialize_snapshot",
    "mount_plan",
    "observe_instance",
    "require_host",
    "sandbox_environment",
    "verify_snapshot",
]

HOSTNAME = "science"
BUNDLE_ROOT = "/science/bundle"
OUTPUT_ROOT = "/science/out"
INPUTS_ROOT = "/science/out/inputs"
TRACE_DIR = ".trace"
HOME_DIR = ".home"
DEVICES = ("/dev/null", "/dev/urandom")
UNPLANNED = "unplanned"
PROBE_MODULE = "science.probe"
_BWRAP = "bwrap"
_NETWORK_UNREACHABLE = ("EAFNOSUPPORT", "ENETUNREACH", "EADDRNOTAVAIL")


def sandbox_environment(trace_file: str) -> tuple[tuple[str, str], ...]:
    """The explicit environment, exactly (design §5.4). Sorted by name."""
    return (
        ("HOME", f"{OUTPUT_ROOT}/{HOME_DIR}"),
        ("LC_CTYPE", "C.UTF-8"),
        ("LD_LIBRARY_PATH", SANDBOX_LIB),
        ("PATH", f"{SANDBOX_VENV}/bin"),
        ("PWD", OUTPUT_ROOT),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONHASHSEED", "0"),
        ("PYTHONNOUSERSITE", "1"),
        ("PYTHONSAFEPATH", "1"),
        ("SCIENCE_TRACE_FILE", trace_file),
    )


# --- host prerequisites (pre-intent) -------------------------------------------
def host_prerequisites() -> str | None:
    """None when the confined policy can be provided here, else why not."""
    bwrap = shutil.which(_BWRAP)
    if bwrap is None:
        return "bubblewrap (bwrap) is not on PATH"
    usage = subprocess.run([bwrap, "--help"], capture_output=True, text=True, check=False)
    if "--info-fd" not in usage.stdout + usage.stderr:
        return "bubblewrap lacks --info-fd"
    namespaces = subprocess.run(
        [bwrap, "--unshare-all", "--ro-bind", "/", "/", "--", "/bin/true"],
        capture_output=True,
        text=True,
        check=False,
    )
    if namespaces.returncode != 0:
        return f"unprivileged user namespaces are unavailable: {namespaces.stderr.strip()}"
    interpreter = Path(os.path.realpath(sys.executable))
    try:
        loader_listing(elf_interpreter(interpreter), interpreter)
    except ClosureUnsupported as error:
        return f"the loader cannot list the interpreter: {error}"
    return None


def require_host() -> None:
    reason = host_prerequisites()
    if reason is not None:
        raise ConfinementUnavailable(reason)


# --- the snapshot -----------------------------------------------------------------
def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _within(root: Path, sandbox: str) -> Path:
    return root / sandbox.lstrip("/")


def verify_snapshot(root: Path, captured: CapturedEnvironment) -> None:
    """Every manifested row by digest, every rendered row by content, and
    nothing else (design §4.3)."""
    manifested = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    rendered = {path: (kind, content) for path, kind, content in captured.rendered if kind != "value"}
    seen: set[str] = set()
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        sandbox = "/" + path.relative_to(root).as_posix()
        if sandbox in manifested:
            kind, content = manifested[sandbox]
            actual = os.readlink(path) if path.is_symlink() else (_digest(path) if path.is_file() else "")
        elif sandbox in rendered:
            kind, content = rendered[sandbox]
            actual = os.readlink(path) if path.is_symlink() else (path.read_text(encoding="utf-8") if path.is_file() else "")
        else:
            raise SnapshotMismatch(f"{root.name}: {sandbox} is not a manifested or rendered row (extra)")
        if (kind == "symlink") != path.is_symlink() or actual != content:
            raise SnapshotMismatch(f"{root.name}: {sandbox} disagrees with its {kind} row")
        seen.add(sandbox)
    missing = sorted((set(manifested) | set(rendered)) - seen)
    if missing:
        raise SnapshotMismatch(f"{root.name}: missing rows {missing[:5]}")


def materialize_snapshot(captured: CapturedEnvironment, environments: Path) -> Path:
    """Get-or-build, keyed by environment identity; atomic publication with the
    loser rule; an existing mismatching snapshot refuses and is never rebuilt."""
    environments.mkdir(parents=True, exist_ok=True)
    target = environments / captured.manifest.identity()
    if target.exists():
        verify_snapshot(target, captured)
        return target
    build = Path(tempfile.mkdtemp(prefix=f"{target.name}.build-", dir=environments))
    for path, kind, content in captured.manifest.artifacts:
        destination = _within(build, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if kind == "symlink":
            destination.symlink_to(content)
        else:
            shutil.copy2(captured.plan[path], destination)
    for path, kind, content in captured.rendered:
        if kind == "value":
            continue
        destination = _within(build, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if kind == "symlink":
            destination.symlink_to(content)
        else:
            destination.write_text(content, encoding="utf-8")
    try:
        verify_snapshot(build, captured)
    except SnapshotMismatch:
        shutil.rmtree(build, ignore_errors=True)
        raise
    try:
        build.rename(target)
    except OSError:
        shutil.rmtree(build, ignore_errors=True)
        verify_snapshot(target, captured)
    return target


# --- integrity: two observations (design §4.4) ---------------------------------
def bundle_identity(bundle: Path) -> str:
    """`capture_bundle`'s fold, recomputed over the copied tree."""
    return _fold([(path.relative_to(bundle).as_posix(), _digest(path)) for path in sorted(bundle.rglob("*")) if path.is_file()])


def fingerprint(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append(f"{relative}\nsymlink\n{os.readlink(path)}\n")
        elif path.is_file():
            rows.append(f"{relative}\nfile\n{_digest(path)}\n")
    return "sha256:" + sha256("".join(rows).encode()).hexdigest()


def check_bundle_intact(bundle: Path, code_identity: str) -> None:
    """The bundle's pre-bind observation: its fold still equals the recorded
    code identity. The snapshot's pre-bind pass is `materialize_snapshot`'s
    verification; the staged inputs' is the fingerprint the caller keeps."""
    if bundle_identity(bundle) != code_identity:
        raise ClosureMutated("the captured bundle no longer folds to its code identity")


def check_closure_intact(
    *,
    bundle: Path,
    code_identity: str,
    snapshot: Path,
    captured: CapturedEnvironment,
    inputs: Path,
    inputs_fingerprint: str,
) -> None:
    """The post-exit observation: one pass each over the bundle, the snapshot
    and the staged inputs, against what was recorded before the bind
    (design §4.4). Runs before the trace, the seeds or any output is read."""
    check_bundle_intact(bundle, code_identity)
    try:
        verify_snapshot(snapshot, captured)
    except SnapshotMismatch as error:
        raise ClosureMutated(f"the snapshot no longer matches its manifest: {error}") from error
    if fingerprint(inputs) != inputs_fingerprint:
        raise ClosureMutated("the staged inputs changed between the bind and exit")


# --- the mount plan -----------------------------------------------------------------
_ROLES = {"ro": "ro", "rw": "rw", "dev": "rw"}


@sealed
@final
@dataclass(frozen=True)
class MountPlan:
    """`binds` are (sandbox path, host source, ro|rw|dev) in bwrap order;
    `rows` is the canonical table the receipt carries, the implicit root first."""

    binds: tuple[tuple[str, str, str], ...]
    roles: tuple[str, ...]
    loader: str

    @property
    def rows(self) -> tuple[tuple[str, str, str], ...]:
        return (("/", "root", "ro"), *((sandbox, role, _ROLES[access]) for (sandbox, _, access), role in zip(self.binds, self.roles)))

    @property
    def expected(self) -> tuple[tuple[str, str, str], ...]:
        """The canonical planned table: the rows, sorted, one per mount."""
        return tuple(sorted(self.rows))

    def role_of(self, mountpoint: str) -> str:
        for point, role, _ in self.rows:
            if point == mountpoint:
                return role
        return UNPLANNED

    def identity(self) -> str:
        return mount_plan_identity(self.rows)

    def host_mapping(self) -> tuple[tuple[str, str], ...]:
        return tuple((sandbox, host) for sandbox, host, _ in self.binds)


def mount_plan(*, snapshot: Path, loader: str, bundle: Path, output_root: Path) -> MountPlan:
    return MountPlan(
        binds=(
            (loader, str(_within(snapshot, loader)), "ro"),
            (SANDBOX_ENV, str(_within(snapshot, SANDBOX_ENV)), "ro"),
            (BUNDLE_ROOT, str(bundle), "ro"),
            (OUTPUT_ROOT, str(output_root), "rw"),
            (INPUTS_ROOT, str(output_root / "inputs"), "ro"),
            (DEVICES[0], DEVICES[0], "dev"),
            (DEVICES[1], DEVICES[1], "dev"),
        ),
        roles=("loader", "env", "bundle", "output", "inputs", "device", "device"),
        loader=loader,
    )


def bwrap_argv(
    plan: MountPlan,
    environment: tuple[tuple[str, str], ...],
    inner_argv: tuple[str, ...],
    *,
    bwrap: str,
    info_fd: int,
    report_fd: int,
    go_fd: int,
) -> tuple[str, ...]:
    argv = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--uid",
        str(os.getuid()),
        "--gid",
        str(os.getgid()),
        "--hostname",
        HOSTNAME,
        "--clearenv",
    ]
    flags = {"ro": "--ro-bind", "rw": "--bind", "dev": "--dev-bind"}
    for sandbox, host, access in plan.binds:
        argv.extend([flags[access], host, sandbox])
    argv.extend(["--remount-ro", "/", "--chdir", OUTPUT_ROOT])
    for name, value in environment:
        argv.extend(["--setenv", name, value])
    argv.extend(["--info-fd", str(info_fd), "--"])
    argv.extend([f"{SANDBOX_VENV}/bin/python", "-m", PROBE_MODULE, "--report-fd", str(report_fd), "--go-fd", str(go_fd), "--loader", plan.loader, "--"])
    argv.extend(inner_argv)
    return tuple(argv)


# --- the observation, from this process's own /proc --------------------------------
def _unescape(field: str) -> str:
    return field.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")


def canonical_mounts(mountinfo: str, plan: MountPlan) -> tuple[tuple[str, str, str], ...]:
    """Every mount, one row each — a stacked or duplicate mount stays a row of
    its own — as (mountpoint, planned role or UNPLANNED, ro|rw), sorted. This
    is what the receipt's instance carries (design §6.1 step 3)."""
    observed: list[tuple[str, str, str]] = []
    for line in mountinfo.splitlines():
        fields = line.split()
        if len(fields) < 6:
            raise ConfinementNotEstablished(f"unparseable mountinfo line {line!r}")
        point = _unescape(fields[4])
        observed.append((point, plan.role_of(point), "ro" if "ro" in fields[5].split(",") else "rw"))
    return tuple(sorted(observed))


@sealed
@final
@dataclass(frozen=True)
class InstanceFacts:
    distinct: tuple[str, ...]
    mounts: tuple[tuple[str, str, str], ...]


def observe_instance(pid: int, plan: MountPlan) -> InstanceFacts:
    distinct = tuple(name for name in NAMESPACES if os.readlink(f"/proc/{pid}/ns/{name}") != os.readlink(f"/proc/self/ns/{name}"))
    return InstanceFacts(distinct, canonical_mounts(Path(f"/proc/{pid}/mountinfo").read_text(encoding="utf-8"), plan))


def judge_instance(facts: InstanceFacts, plan: MountPlan) -> None:
    if missing := [name for name in NAMESPACES if name not in facts.distinct]:
        raise ConfinementNotEstablished(f"namespaces equal to the parent's: {missing}")
    if facts.mounts != plan.expected:
        differences = sorted(set(facts.mounts) ^ set(plan.expected)) or [
            f"{len(facts.mounts)} observed rows against {len(plan.expected)} planned"
        ]
        raise ConfinementNotEstablished(f"observed mounts differ from the plan: {differences}")


def _expected_filesystem() -> dict[str, str]:
    return {
        "read:/etc/passwd": "ENOENT",
        "read:/tmp": "ENOENT",
        "write:/": "EROFS",
        f"write:{BUNDLE_ROOT}": "EROFS",
        f"write:{SANDBOX_ENV}": "EROFS",
        f"write:{INPUTS_ROOT}": "EROFS",
        f"write:{OUTPUT_ROOT}": "OK",
    }


def _terminal_digest(captured: CapturedEnvironment, path: str) -> str | None:
    """The digest of the file row a sandbox path reaches through the manifest's
    own symlink rows; None when it reaches no file row."""
    rows = {row_path: (kind, content) for row_path, kind, content in captured.manifest.artifacts}
    for _ in range(len(rows) + 1):
        row = rows.get(path)
        if row is None:
            return None
        kind, content = row
        if kind == "file":
            return content
        path = content if content.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(path), content))
    return None


def judge_report(
    report: Mapping[str, object],
    *,
    environment: tuple[tuple[str, str], ...],
    captured: CapturedEnvironment,
    inner_argv: tuple[str, ...],
) -> tuple[str, ...]:
    """The probe's report against what was declared. Every failure is a refusal;
    the graded case is reached by selecting the minimal policy, not here. A
    malformed shape raises KeyError or TypeError, which the launch wraps."""
    environ = cast(Mapping[str, str], report["environ"])
    if dict(environ) != dict(environment):
        raise ConfinementNotEstablished(f"environment differs from the declared set: {sorted(set(environ.items()) ^ set(environment))}")
    if report["hostname"] != HOSTNAME:
        raise ConfinementNotEstablished(f"hostname {report['hostname']!r} is not {HOSTNAME!r}")
    if report["cwd"] != OUTPUT_ROOT:
        raise ConfinementNotEstablished(f"cwd {report['cwd']!r} is not {OUTPUT_ROOT!r}")
    filesystem = cast(Mapping[str, str], report["filesystem"])
    if dict(filesystem) != _expected_filesystem():
        raise ConfinementNotEstablished(f"filesystem probes differ: {sorted(set(filesystem.items()) ^ set(_expected_filesystem().items()))}")
    network = cast(Mapping[str, str], report["network"])
    if network["ipv4"] != "ENETUNREACH":
        raise ConfinementNotEstablished(f"network: IPv4 connect reported {network['ipv4']!r}, not ENETUNREACH")
    if network["ipv6"] not in _NETWORK_UNREACHABLE:
        raise ConfinementNotEstablished(f"network: IPv6 reported {network['ipv6']!r}, not one of {_NETWORK_UNREACHABLE}")
    expected: dict[str, dict[str, str]] = {}
    for elf, soname, resolved in captured.loader_map:
        expected.setdefault(elf, {})[soname] = resolved
    reported = cast(Mapping[str, Mapping[str, object]], report["loader"])
    if set(reported) != set(expected):
        raise ConfinementNotEstablished(f"loader: the listed ELFs differ from the captured set: {sorted(set(reported) ^ set(expected))}")
    for elf, entry in reported.items():
        if entry["returncode"] != 0 or entry["unresolved"]:
            raise ConfinementNotEstablished(f"loader: {elf} exited {entry['returncode']} with unresolved {entry['unresolved']}")
        resolved_map = cast(Mapping[str, list[str]], entry["resolved"])
        if set(resolved_map) != set(expected[elf]):
            raise ConfinementNotEstablished(f"loader: {elf} lists {sorted(set(resolved_map) ^ set(expected[elf]))} differently from the capture")
        for soname, (path, digest) in resolved_map.items():
            if path != expected[elf][soname] or _terminal_digest(captured, path) != digest:
                raise ConfinementNotEstablished(f"loader: {elf} maps {soname} to {path} ({digest}), not the manifested {expected[elf][soname]}")
    snakefile = inner_argv[inner_argv.index("--snakefile") + 1]
    if not snakefile.startswith(f"{BUNDLE_ROOT}/"):
        raise ConfinementNotEstablished(f"the engine's snakefile {snakefile!r} is not under the bundle")
    return CAPABILITIES


# --- the gated launch ---------------------------------------------------------------
@sealed
@final
@dataclass(frozen=True)
class Launch:
    returncode: int
    output: str
    capabilities: tuple[str, ...]
    facts: InstanceFacts
    report: Mapping[str, object]


def _read_info(fd: int) -> int:
    """bubblewrap's info JSON, read until it parses; the child pid, or a refusal."""
    buffer = b""
    while True:
        chunk = os.read(fd, 4096)
        if not chunk:
            raise ConfinementNotEstablished("bubblewrap closed its info descriptor without reporting the child")
        buffer += chunk
        try:
            info = json.loads(buffer)
        except json.JSONDecodeError:
            continue
        child = info.get("child-pid") if isinstance(info, dict) else None
        if type(child) is not int:
            raise ConfinementNotEstablished("bubblewrap's info report names no integer child-pid")
        return child


def _read_report(fd: int) -> Mapping[str, object]:
    """The probe's JSON report followed by the READY line, read raw so the
    descriptor's ownership stays with the caller."""
    terminator = b"\nREADY\n"
    buffer = b""
    while terminator not in buffer:
        chunk = os.read(fd, 65536)
        if not chunk:
            raise ConfinementNotEstablished("the probe exited before reporting READY")
        buffer += chunk
    body, _, _ = buffer.partition(terminator)
    report = json.loads(body)
    if not isinstance(report, dict):
        raise ConfinementNotEstablished("the probe's report is not a JSON object")
    return cast(Mapping[str, object], report)


def _close(open_fds: set[int], *fds: int) -> None:
    """Close each descriptor exactly once."""
    for fd in fds:
        if fd in open_fds:
            open_fds.remove(fd)
            os.close(fd)


def _reap(process: subprocess.Popen[str]) -> str:
    """Terminate and reap a child whose gate failed; its output, for the detail."""
    process.terminate()
    try:
        output, _ = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    return output or ""


_PROTOCOL_FAILURES = (ConfinementNotEstablished, OSError, ValueError, TypeError, KeyError, AttributeError)


def launch_confined(
    *,
    plan: MountPlan,
    environment: tuple[tuple[str, str], ...],
    inner_argv: tuple[str, ...],
    captured: CapturedEnvironment,
) -> Launch:
    """Start bubblewrap with the held probe as its command; read the child pid;
    wait for the probe's report and READY; inspect that child's namespaces and
    mounts from this process's /proc; judge; then GO or close (design §6.1).

    Every failure between the start and GO — a refusal, a closed pipe,
    malformed info or report, a missing key, an unstartable process — is
    `ConfinementNotEstablished` (design §8: post-intent, never the pre-intent
    `ConfinementUnavailable`); the child is terminated and reaped and every
    descriptor closed on every path."""
    bwrap = shutil.which(_BWRAP)
    if bwrap is None:
        raise ConfinementNotEstablished("bubblewrap (bwrap) left PATH after intent")
    info_r, info_w = os.pipe()
    report_r, report_w = os.pipe()
    go_r, go_w = os.pipe()
    open_fds = {info_r, info_w, report_r, report_w, go_r, go_w}
    argv = bwrap_argv(plan, environment, inner_argv, bwrap=bwrap, info_fd=info_w, report_fd=report_w, go_fd=go_r)
    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            pass_fds=(info_w, report_w, go_r),
            env={},
        )
    except OSError as failure:
        _close(open_fds, *tuple(open_fds))
        raise ConfinementNotEstablished(f"bubblewrap could not be started: {failure}") from failure
    try:
        _close(open_fds, info_w, report_w, go_r)
        child = _read_info(info_r)
        report = _read_report(report_r)
        facts = observe_instance(child, plan)
        judge_instance(facts, plan)
        capabilities = judge_report(report, environment=environment, captured=captured, inner_argv=inner_argv)
        os.write(go_w, b"GO\n")
    except _PROTOCOL_FAILURES as failure:
        _close(open_fds, *tuple(open_fds))  # closing GO tells the probe to exit
        output = _reap(process)
        raise ConfinementNotEstablished(f"{failure}; sandbox output: {output.strip()[-2000:]}") from failure
    finally:
        _close(open_fds, *tuple(open_fds))
    output, _ = process.communicate()
    return Launch(process.returncode, output, capabilities, facts, report)
```

`ConfinementUnavailable` is no longer imported by `confinement.py` except in `require_host` — the only pre-intent site.

- [ ] **Step 4: Write `probe.py`**

`python/src/science/probe.py`:

```python
"""The held probe that gates the confined engine (design §6.1–§6.2).

It runs inside the sandbox as the engine's own process: performs its checks,
writes the report and READY on the report descriptor, waits for GO on the go
descriptor, closes both, and ``execve``s the engine. It decides nothing — the
boundary judges the report from outside. Its one write check touches and
removes a file with inventoried operations (``Path.touch``, ``unlink``), so
``test_capability_boundary.py`` weighs this module as the fourth raw-write
surface rather than a raw ``os.open`` escaping the inventory.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import pathlib
import socket
import struct
import subprocess
import sys

_ELF_MAGIC = b"\x7fELF"
_ENV_ROOT = "/science/env"
_READ_PROBES = ("/etc/passwd", "/tmp")
_WRITE_PROBES = ("/", "/science/bundle", "/science/env", "/science/out/inputs", "/science/out")
_IPV4 = ("192.0.2.1", 9)
_IPV6 = ("2001:db8::1", 9)


def _errno_name(error: OSError) -> str:
    if error.errno is None:
        return type(error).__name__
    return errno.errorcode.get(error.errno, f"errno{error.errno}")


def _read_probe(path: str) -> str:
    try:
        with open(path, "rb"):
            return "READ"
    except OSError as error:
        return _errno_name(error)


def _write_probe(directory: str) -> str:
    probe = pathlib.Path(directory) / ".probe"
    try:
        probe.touch(mode=0o600, exist_ok=False)
    except OSError as error:
        return _errno_name(error)
    probe.unlink()
    return "OK"


def _connect(family: int, address: tuple[str, int]) -> str:
    try:
        sock = socket.socket(family, socket.SOCK_STREAM)
    except OSError as error:
        return _errno_name(error)
    try:
        sock.settimeout(2.0)
        sock.connect(address)
        return "CONNECTED"
    except OSError as error:
        return _errno_name(error)
    finally:
        sock.close()


def _digest(path: str) -> str:
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def _is_loadable_elf(path: str) -> bool:
    """The same predicate as adapter._is_loadable_elf: ELF of type ET_EXEC or ET_DYN."""
    with open(path, "rb") as handle:
        header = handle.read(18)
    return len(header) == 18 and header[:4] == _ELF_MAGIC and struct.unpack_from("<H", header, 16)[0] in (2, 3)


def _elves() -> list[str]:
    """Every loadable ELF regular file under the environment root — the set the
    boundary's loader map covers; symlinked directories are not followed."""
    found: list[str] = []
    for directory, _, names in os.walk(_ENV_ROOT):
        for name in names:
            path = os.path.join(directory, name)
            if os.path.isfile(path) and not os.path.islink(path) and _is_loadable_elf(path):
                found.append(path)
    return sorted(found)


def _listing(loader: str, path: str) -> dict[str, object]:
    """The loader's own in-layout resolution, reported whole: exit status, every
    resolved SONAME with the path as listed and its digest, every line that did
    not resolve. The boundary requires equality with its captured map."""
    completed = subprocess.run([loader, "--list", path], capture_output=True, text=True, check=False)
    resolved: dict[str, list[str]] = {}
    unresolved: list[str] = []
    for line in completed.stdout.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith(("linux-vdso", "linux-gate")) or parts[0].startswith("/"):
            continue
        if len(parts) >= 3 and parts[1] == "=>" and parts[2] != "not":
            resolved[parts[0]] = [parts[2], _digest(parts[2])]
        else:
            unresolved.append(line.strip())
    return {"returncode": completed.returncode, "resolved": resolved, "unresolved": unresolved}


def report(loader: str) -> dict[str, object]:
    return {
        "environ": dict(os.environ),
        "hostname": os.uname().nodename,
        "cwd": os.getcwd(),
        "filesystem": {
            **{f"read:{path}": _read_probe(path) for path in _READ_PROBES},
            **{f"write:{path}": _write_probe(path) for path in _WRITE_PROBES},
        },
        "network": {"ipv4": _connect(socket.AF_INET, _IPV4), "ipv6": _connect(socket.AF_INET6, _IPV6)},
        "loader": {elf: _listing(loader, elf) for elf in _elves()},
    }


def main(argv: list[str]) -> int:
    separator = argv.index("--")
    options = dict(zip(argv[:separator:2], argv[1:separator:2]))
    engine = argv[separator + 1 :]
    report_fd = int(options["--report-fd"])
    go_fd = int(options["--go-fd"])
    payload = report(options["--loader"])
    with os.fdopen(report_fd, "w", encoding="utf-8") as out:
        out.write(json.dumps(payload, sort_keys=True) + "\nREADY\n")
    with os.fdopen(go_fd, "r", encoding="utf-8") as go:
        line = go.readline()
    if line.rstrip("\n") != "GO":
        return 3
    os.execv(engine[0], engine)
    return 4  # pragma: no cover - execv does not return


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

Both `os.fdopen` blocks close their descriptors on exit, so the engine inherits no gate authority (design §6.1 step 4).

- [ ] **Step 5: Weigh the raw-write claim**

In `python/tests/test_capability_boundary.py`, extend `RAW_WRITE_ALLOWLIST`:

```python
    # The environment snapshot: manifested files copied, manifested and
    # rendered symlinks created, rendered files written, the build published
    # by rename, a losing build discarded — under a boundary-owned directory
    # registered by nothing (run-confinement design §4.3, §10).
    "confinement.py": {"copy2", "write_text", "symlink_to", "rename", "rmtree"},
    # The held probe's one write check: a file touched and removed under the
    # output root, with inventoried operations so this table weighs it
    # (run-confinement design §6.2, §10).
    "probe.py": {"touch", "unlink"},
```

change its docstring's "The two surfaces" to "The four surfaces", and the assertion to `assert set(RAW_WRITE_ALLOWLIST) == {"adapter.py", "boundary.py", "confinement.py", "probe.py"}`.

- [ ] **Step 6: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_confinement.py tests/test_capability_boundary.py | tail -1 && uv run ruff check src/science/confinement.py src/science/probe.py tests/test_confinement.py && uv run pyright src/science/confinement.py src/science/probe.py | tail -1`
Expected: all passed; clean; `0 errors`. If `test_capability_boundary` reports a primitive named in `confinement.py` beyond the five, or in `probe.py` beyond the two, rename the use — never widen the entry.

- [ ] **Step 7: A live smoke of the gate, recorded in the ledger**

Before wiring the boundary, exercise the launch once by hand from `python/` to learn what bubblewrap's mount table actually contains on this host:

```bash
cd python && uv run python - <<'EOF'
import tempfile, pathlib
from science.adapter import capture_closure
from science.confinement import *
captured = capture_closure()
work = pathlib.Path(tempfile.mkdtemp())
snapshot = materialize_snapshot(captured, work / "environments")
bundle = work / "bundle"; (bundle / "code").mkdir(parents=True); (bundle / "code" / "Snakefile").write_text("rule a:\n    output: 'outputs/x'\n    run:\n        open(output[0], 'w').write('x')\n")
out = work / "out"; (out / "inputs").mkdir(parents=True); (out / ".trace").mkdir(); (out / ".home").mkdir()
plan = mount_plan(snapshot=snapshot, loader=captured.loader, bundle=bundle, output_root=out)
env = sandbox_environment("/science/out/.trace/events.jsonl")
inner = (f"{SANDBOX_VENV}/bin/python", "-c", "print('engine ran')")
try:
    launch = launch_confined(plan=plan, environment=env, inner_argv=("/science/env/venv/bin/python", "-m", "snakemake", "--snakefile", "/science/bundle/code/Snakefile", "--directory", "/science/out", "--cores", "1", "--nolock", "--force-use-threads", "--", "outputs/x"), captured=captured)
    print("returncode", launch.returncode, "capabilities", launch.capabilities)
    print(sorted(launch.facts.mounts))
except Exception as error:
    print("REFUSED", error)
EOF
```

Expected: `returncode 0 capabilities ('from-bundle', 'closure-confined-filesystem', 'network-denied')` and a mount set equal to the plan's eight rows. If bubblewrap adds a mount the plan does not declare (a second root entry for its pivot, for example), **declare it in `mount_plan`'s rows with an explicit role** and adjust `test_the_mount_plan_rows_are_canonical_and_identity_bearing`; never loosen `judge_instance`. Record the observed table and any such declaration as ledger ruling R3. Delete the temporary directory.

- [ ] **Step 8: Commit**

```bash
git add python/src/science/confinement.py python/src/science/probe.py python/tests/test_confinement.py python/tests/test_capability_boundary.py docs/plans/2026-08-30-run-confinement-ledger.md
git commit -m "feat(confinement): materialize the closure snapshot and gate the bubblewrap launch through the held probe"
```

---

### Task 7: The boundary's confined path

**Files:**
- Modify: `python/src/science/boundary.py` (imports; `_refused` 144–164; `_execute_run` 281–392; `execute_assessment_run` 395–455; `execute_production_run` 458–519; new `_project`, `_policy_refusal`, `_execute_confined`)
- Modify: `python/src/science/replay.py:100-145` (`replay` passes the original's policy)
- Modify: `python/tests/fixtures_cut3.py` (`run_assessment`, `run_production` take `boundary_policy`); every direct `execute_*_run(` call under `python/tests/`
- Test: `python/tests/test_boundary.py` (appended tests)

**Interfaces:**
- Produces: `execute_assessment_run(*, spec, port, boundary_policy, ...)` and `execute_production_run(*, inputs, port, boundary_policy, ...)` — keyword-only, no default; `_execute_confined(...)`; `boundary.launch_confined` and `boundary.capture_bundle` as monkeypatchable names (the acceptance seams); `RunRefused.detail` populated for confinement refusals.
- Consumes: everything from Tasks 2–6.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_boundary.py`:

```python
# --- cut 13: the policy parameter, pre-intent refusals, stable reasons ---------
import dataclasses as _dc

from fixtures_cut3 import replay_of as _replay_of

import science.boundary as _boundary
from science.errors import ClosureUnsupported
from science.recipe import CONFINED_POLICY, MINIMAL_POLICY
from science.replay import replay as _replay


def test_the_boundary_policy_has_no_default_and_no_ambient_constant():
    for fn in (execute_assessment_run, execute_production_run):
        parameter = inspect.signature(fn).parameters["boundary_policy"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert not hasattr(_boundary, "_POLICY")


def test_k1_an_unsupported_policy_refuses_before_intent(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=_dc.replace(CONFINED_POLICY, scope_rule="scope-derivation/v2"))
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "boundary-policy-unsupported"
    assert outcome.intent is None and outcome.registration is None and outcome.report is not None
    assert "scope-derivation/v2" in outcome.detail


def test_a_minimal_run_carries_a_v1_receipt_and_no_instance(tmp_path):
    outcome = run_assessment(tmp_path, boundary_policy=MINIMAL_POLICY)
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    assert not receipt.confined and receipt.capabilities == () and receipt.instance is None
    assert outcome.run.recipe.boundary_policy == MINIMAL_POLICY


def test_replay_carries_the_originals_policy_and_takes_none_of_its_own(tmp_path):
    assert "boundary_policy" not in inspect.signature(_replay).parameters
    original = run_assessment(tmp_path / "a")
    replayed = _replay_of(original, tmp_path / "b", port=MEMORY_PORT)
    assert isinstance(replayed, RunMinted)
    assert replayed.run.recipe.boundary_policy == original.run.recipe.boundary_policy == MINIMAL_POLICY


def test_a_confinement_refusal_keeps_its_stable_reason_and_its_detail(tmp_path, monkeypatch):
    def unsupported():
        raise ClosureUnsupported("synthetic: SONAME collision")

    monkeypatch.setattr(_boundary, "capture_closure", unsupported)
    outcome = run_assessment(tmp_path)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "closure-unsupported"
    assert outcome.detail == "synthetic: SONAME collision"
    assert outcome.intent is not None  # post-intent: the intent was fulfilled by a refusal
    assert outcome.report is not None and outcome.report.entries[0].outcome.missing_member == "closure-unsupported"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_boundary.py -k "no_default or unsupported_policy or v1_receipt or originals_policy or stable_reason" | tail -3`
Expected: FAIL — `KeyError: 'boundary_policy'`.

- [ ] **Step 3: Implement**

In `python/src/science/boundary.py`:

Imports: replace `capture_environment` in the `science.adapter` import with `capture_closure`, and add `SANDBOX_VENV`, `BUNDLE_ROOT`-style names from `science.confinement`:

```python
from science.adapter import (
    LOG_HANDLER_SCRIPT,
    SANDBOX_VENV,
    CapturedEnvironment,
    WorkflowDefinition,
    build_argv,
    capture_bundle,
    capture_closure,
    create_scratch_root,
    read_realized_seeds,
    read_trace,
    require_executing_environment,
    run_engine,
    validate_entrypoint,
)
from science.confinement import (
    BUNDLE_ROOT,
    HOME_DIR,
    HOSTNAME,
    OUTPUT_ROOT,
    TRACE_DIR,
    check_bundle_intact,
    check_closure_intact,
    fingerprint,
    launch_confined,
    materialize_snapshot,
    mount_plan,
    require_host,
    sandbox_environment,
)
from science.errors import ConfinementRefusal, MalformedClosure, MalformedRecord, ScienceError
from science.recipe import (
    CONFINED_POLICY,
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentManifest,
    InstanceAttestation,
    Invocation,
    Occurrence,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    project_recipe,
    supported_policy,
)
```

and `import sys` (Task 5 added it). Delete the `_POLICY = BoundaryPolicy(...)` constant. Update the module docstring's first paragraph to: `"""Begin, execute, capture, and mint runs through the minimal adapter, or through the confined policy's snapshot-and-sandbox path (run-confinement design §5).\n\nThe scratch root is staging under the minimal policy and the host side of the output root under the confined one. ...` keeping the rest.

`_refused` gains a trailing keyword:

```python
def _refused(
    reason: str,
    subject: str,
    actor: str,
    observer: str,
    started_at: str,
    intent: AssessmentRunIntent | OperationIntent | None = None,
    *,
    detail: str = "",
) -> RunRefused:
```

and its last line becomes `return RunRefused(reason, report, intent, registration, detail)`. The `registration = Registration(token, report.identity()) if intent is not None else None` line stays byte-identical.

Add after `_render_config`:

```python
def _policy_refusal(policy: BoundaryPolicy) -> ConfinementRefusal | None:
    """Pre-intent: the whole definition must be known, and a confined request
    needs the host's substrate. Never a downgrade."""
    try:
        if supported_policy(policy) == CONFINED_POLICY:
            require_host()
    except ConfinementRefusal as refusal:
        return refusal
    return None


def _project(
    *,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    held: Mapping[str, str],
    code_identity: str,
    environment: EnvironmentManifest,
    definition: WorkflowDefinition,
    invocation: Invocation,
    boundary_policy: BoundaryPolicy,
) -> Recipe:
    if spec is not None:
        return project_recipe(
            spec,
            held=held,
            code_identity=code_identity,
            environment=environment,
            workflow_definition_identity=definition.identity(),
            invocation=invocation,
            boundary_policy=boundary_policy,
        )
    if nondeterminism is None:
        raise MalformedClosure("a production recipe requires a nondeterminism contract")
    if any(entry.content != held[entry.dataset] for entry in inputs):
        raise MalformedClosure("a production input content identity does not match held bytes")
    return Recipe(
        shape="dataset-production",
        spec_identity=None,
        code_identity=code_identity,
        environment=environment,
        workflow_definition_identity=definition.identity(),
        invocation=invocation,
        inputs=inputs,
        parameters=parameters,
        nondeterminism=nondeterminism,
        boundary_policy=boundary_policy,
        rule_bindings=((DATASET_EQUIVALENCE_RULE, "impl-dataset-eq-1"),),
    )
```

(import `EnvironmentManifest` from `science.recipe`). Replace `_execute_run` with:

```python
def _execute_run(
    *,
    intent: AssessmentRunIntent | OperationIntent,
    subject: str,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int,
    boundary_policy: BoundaryPolicy,
) -> RunMinted | RunRefused:
    try:
        scratch = create_scratch_root(scratch_base)
        bundle = scratch / "bundle"
        code_identity = capture_bundle(code_roots, bundle)
        captured = capture_closure()
        environment = captured.manifest
        captured_entrypoint = validate_entrypoint(bundle, entrypoint)
        if captured_entrypoint.read_bytes() != definition.snakefile:
            return _refused("definition-mismatch", subject, actor, observer, started_at, intent)

        addresses = (
            tuple(entry.dataset for entry in spec.input_roles)
            if spec is not None
            else tuple(entry.dataset for entry in inputs)
        )
        if boundary_policy == CONFINED_POLICY:
            return _execute_confined(
                intent=intent,
                subject=subject,
                spec=spec,
                inputs=inputs,
                parameters=parameters,
                nondeterminism=nondeterminism,
                definition=definition,
                addresses=addresses,
                held_inputs=held_inputs,
                captured=captured,
                scratch=scratch,
                bundle=bundle,
                code_identity=code_identity,
                captured_entrypoint=captured_entrypoint,
                entrypoint=entrypoint,
                targets=targets,
                declared_outputs=declared_outputs,
                actor=actor,
                observer=observer,
                started_at=started_at,
                host_realization=host_realization,
                scratch_base=scratch_base,
                cores=cores,
            )
        held = _stage_inputs(addresses, held_inputs, scratch)
        invocation = Invocation(
            entrypoint=entrypoint,
            targets=targets,
            bindings=("inputs", "parameters", "nondeterminism"),
            declared_outputs=declared_outputs,
        )
        recipe = _project(
            spec=spec,
            inputs=inputs,
            parameters=parameters,
            nondeterminism=nondeterminism,
            held=held,
            code_identity=code_identity,
            environment=environment,
            definition=definition,
            invocation=invocation,
            boundary_policy=boundary_policy,
        )

        config = _render_config(recipe, definition)
        trace_dir = Path(tempfile.mkdtemp(prefix="trace-", dir=scratch.parent))
        handler = trace_dir / "handler.py"
        events = trace_dir / "events.jsonl"
        handler.write_text(LOG_HANDLER_SCRIPT)
        argv = build_argv(
            interpreter=sys.executable,
            snakefile=str(captured_entrypoint),
            directory=str(scratch),
            targets=targets,
            config=config,
            log_handler=str(handler),
            cores=cores,
            in_process_jobs=False,
        )
        env = {**os.environ, "SCIENCE_TRACE_FILE": str(events)}
        require_executing_environment(recipe.environment)
        returncode, _ = run_engine(argv, cwd=scratch, env=env)
        if returncode != 0:
            return _refused("execution-failed", subject, actor, observer, started_at, intent)

        trace = read_trace(events)
        realized_seeds = read_realized_seeds(scratch)
        receipt = BoundaryReceipt(
            scratch_mapping=str(scratch),
            argv=argv,
            rendered_config=tuple(sorted(config.items())),
            capabilities=(),
        )
        occurrence = Occurrence(
            event_token=intent.event_token,
            started_at=started_at,
            actor=actor,
            host_realization=host_realization,
            trace=trace,
            realized_seeds=realized_seeds,
            receipt=receipt,
        )
        manifest = build_manifest(declared_outputs, scratch)
        run = mint_run(recipe, manifest, occurrence, scratch)
        return RunMinted(run, intent, Registration(intent.event_token, run.address()))
    except ConfinementRefusal as error:
        return _refused(error.reason, subject, actor, observer, started_at, intent, detail=str(error))
    except (ScienceError, OSError) as error:
        return _refused(str(error), subject, actor, observer, started_at, intent)


def _execute_confined(
    *,
    intent: AssessmentRunIntent | OperationIntent,
    subject: str,
    spec: FrozenSpec | None,
    inputs: tuple[RecipeInput, ...],
    parameters: Mapping[str, object],
    nondeterminism: NondeterminismContract | None,
    definition: WorkflowDefinition,
    addresses: tuple[str, ...],
    held_inputs: Mapping[str, Path],
    captured: CapturedEnvironment,
    scratch: Path,
    bundle: Path,
    code_identity: str,
    captured_entrypoint: Path,
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int,
) -> RunMinted | RunRefused:
    """Design §5.6 steps 3–5: the scratch root's ``out/`` is the host side of
    the output root; the closure is snapshotted, verified, bound and observed;
    the engine runs only after the gate; the post-exit check precedes every
    read. One capture (the caller's), one pre-bind observation (the bundle's
    fold, the snapshot verification ``materialize_snapshot`` performs, the
    inputs' fingerprint), one post-exit observation — no other pass over the
    closure. Raises ConfinementRefusal for the caller's except clause."""
    output_root = scratch / "out"
    output_root.mkdir()
    (output_root / TRACE_DIR).mkdir()
    (output_root / HOME_DIR).mkdir()
    held = _stage_inputs(addresses, held_inputs, output_root)
    invocation = Invocation(
        entrypoint=entrypoint,
        targets=targets,
        bindings=("inputs", "parameters", "nondeterminism"),
        declared_outputs=declared_outputs,
    )
    recipe = _project(
        spec=spec,
        inputs=inputs,
        parameters=parameters,
        nondeterminism=nondeterminism,
        held=held,
        code_identity=code_identity,
        environment=captured.manifest,
        definition=definition,
        invocation=invocation,
        boundary_policy=CONFINED_POLICY,
    )
    config = _render_config(recipe, definition)
    handler = output_root / TRACE_DIR / "handler.py"
    handler.write_text(LOG_HANDLER_SCRIPT)
    trace_file = f"{OUTPUT_ROOT}/{TRACE_DIR}/events.jsonl"
    relative_entrypoint = captured_entrypoint.relative_to(bundle.resolve()).as_posix()
    inner_argv = build_argv(
        interpreter=f"{SANDBOX_VENV}/bin/python",
        snakefile=f"{BUNDLE_ROOT}/{relative_entrypoint}",
        directory=OUTPUT_ROOT,
        targets=targets,
        config=config,
        log_handler=f"{OUTPUT_ROOT}/{TRACE_DIR}/handler.py",
        cores=cores,
        in_process_jobs=True,
    )
    environment = sandbox_environment(trace_file)
    snapshot = materialize_snapshot(captured, scratch_base / "environments")
    plan = mount_plan(snapshot=snapshot, loader=captured.loader, bundle=bundle, output_root=output_root)
    check_bundle_intact(bundle, code_identity)
    inputs_before = fingerprint(output_root / "inputs")
    launched = launch_confined(plan=plan, environment=environment, inner_argv=inner_argv, captured=captured)
    check_closure_intact(bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=output_root / "inputs", inputs_fingerprint=inputs_before)
    if launched.returncode != 0:
        return _refused("execution-failed", subject, actor, observer, started_at, intent, detail=launched.output[-2000:])
    trace = read_trace(output_root / TRACE_DIR / "events.jsonl")
    realized_seeds = read_realized_seeds(output_root)
    receipt = BoundaryReceipt(
        scratch_mapping=str(scratch),
        argv=inner_argv,
        rendered_config=tuple(sorted(config.items())),
        capabilities=launched.capabilities,
        instance=InstanceAttestation(
            namespaces=launched.facts.distinct,
            mounts=launched.facts.mounts,
            mount_plan_identity=plan.identity(),
            environment_identity=snapshot.name,
        ),
        rendered_environment=(
            *captured.rendered,
            *((f"env:{name}", "value", value) for name, value in environment),
            ("hostname", "value", HOSTNAME),
        ),
        mounts=plan.host_mapping(),
    )
    occurrence = Occurrence(
        event_token=intent.event_token,
        started_at=started_at,
        actor=actor,
        host_realization=host_realization,
        trace=trace,
        realized_seeds=realized_seeds,
        receipt=receipt,
    )
    manifest = build_manifest(declared_outputs, output_root)
    run = mint_run(recipe, manifest, occurrence, output_root)
    return RunMinted(run, intent, Registration(intent.event_token, run.address()))
```

`environment_identity=snapshot.name` is the verified snapshot's key — the directory `materialize_snapshot` published or verified — not the recipe's copy (design §6.3); `qualifies` compares the two in Task 8. `mounts=launched.facts.mounts` is the **observed** canonical table, which `judge_instance` has already found equal to the plan — the receipt records what was seen, never what was planned. The confined path does not call `require_executing_environment`: `recipe.environment` *is* `captured.manifest`, the single capture, and `materialize_snapshot`'s verification is the snapshot's only pre-bind pass.

In `execute_assessment_run`: add `boundary_policy: BoundaryPolicy,` directly after `port: OperationPort,`; after the `_preflight` block and before `intent = AssessmentRunIntent(...)` insert:

```python
    if refusal := _policy_refusal(boundary_policy):
        refused = _refused(refusal.reason, spec.identity, actor, observer, started_at, detail=str(refusal))
        port.execute(_report_plan(refused.report))
        return refused
```

and pass `boundary_policy=supported_policy(boundary_policy)` to `_execute_run` — the canonical known definition (it cannot raise after the refusal check), so a reordered spelling of a known capability set is recorded as the definition it names. Same in `execute_production_run` with subject `"absent"`.

In `python/src/science/replay.py`'s `replay`, add `"boundary_policy": original.run.recipe.boundary_policy,` to `common` (after `"port": port,`).

In `python/tests/fixtures_cut3.py`: `run_assessment` and `run_production` gain `boundary_policy=MINIMAL_POLICY` keyword parameters (import `MINIMAL_POLICY` from `science.recipe`) and pass `boundary_policy=boundary_policy` through. Then:

```bash
grep -rn "execute_assessment_run(\|execute_production_run(" python/tests | grep -v "def \|import"
```

and add `boundary_policy=MINIMAL_POLICY,` after `port=...` in every direct call (`test_boundary.py`, `test_run_persistence.py`, `test_production.py`, and any other hit).

- [ ] **Step 4: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_boundary.py tests/test_replay.py tests/test_verify.py tests/test_production.py tests/test_assess.py tests/test_adapter.py tests/test_capability_boundary.py | tail -1 && uv run pytest tests/test_n2.py -k stale | tail -1 && uv run ruff check src/science tests && uv run pyright src/science/boundary.py src/science/replay.py | tail -1`
Expected: all passed; no stale anchors; clean; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/boundary.py python/src/science/replay.py python/tests
git commit -m "feat(boundary): execute a run under the confined policy, gated, observed, and never downgraded"
```

---

### Task 8: The fourth scope row and the admission join

**Files:**
- Modify: `python/src/science/replay.py:202-234` (`derive_scope`, its docstring; new `qualifies`)
- Modify: `python/src/science/verify.py` (`__all__`; new `admission_record`)
- Modify: `python/tests/test_replay.py:386-388` (retire `test_clean_environment_has_no_reachable_branch`; new R4/R15 value-level arms)
- Test: `python/tests/test_verify.py` (appended K5 tests)

**Interfaces:**
- Produces: `replay.qualifies(receipt, environment_identity) -> bool`; `derive_scope` returning `"clean-environment"`; `verify.admission_record(derived: AssessmentVerification) -> Verification`.
- Consumes: `REQUIRED_FOR_CLEAN_ENVIRONMENT`, `BoundaryReceipt.instance` (Task 3); `NotAnAssessmentVerification` (Task 2).

- [ ] **Step 1: Write the failing tests**

In `python/tests/test_replay.py`, delete `test_clean_environment_has_no_reachable_branch` and, in its place, add (imports at the top: `from confinement_fixtures import confined_receipt, instance`; `from science.recipe import CAPABILITIES, BoundaryPolicy`; `from science.replay import qualifies`):

```python
def _confined(minted, *, capabilities=CAPABILITIES, environment_identity=None):
    run = minted.run
    identity = environment_identity if environment_identity is not None else run.recipe.environment.identity()
    receipt = confined_receipt(capabilities=capabilities, instance=instance(environment_identity=identity))
    return dataclasses.replace(run, occurrence=dataclasses.replace(run.occurrence, receipt=receipt))


def test_r4_the_clean_environment_row_is_reached_only_through_a_qualifying_receipt(pair):
    original, replayed = pair
    assert derive_scope(original.run, _confined(replayed), certification=None) == "clean-environment"
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"
    foreign = _confined(replayed, environment_identity="sha256:" + "00" * 32)
    assert derive_scope(original.run, foreign, certification=None) == "same-environment"


def test_r4_negative_d_a_receipt_missing_a_required_capability_derives_same_environment(pair):
    original, replayed = pair
    for missing in CAPABILITIES:
        fewer = tuple(capability for capability in CAPABILITIES if capability != missing)
        assert derive_scope(original.run, _confined(replayed, capabilities=fewer), certification=None) == "same-environment"


def test_r4_negative_d_a_policy_qualifies_whatever_its_version_string(pair):
    original, replayed = pair
    v99 = BoundaryPolicy(identity="boundary-policy/confined-v99", scope_rule="scope-derivation/v1", capabilities=CAPABILITIES)
    left = dataclasses.replace(original.run, recipe=dataclasses.replace(original.run.recipe, boundary_policy=v99))
    right = _confined(replayed)
    right = dataclasses.replace(right, recipe=dataclasses.replace(right.recipe, boundary_policy=v99))
    assert left.recipe.identity() == right.recipe.identity()
    assert derive_scope(left, right, certification=None) == "clean-environment"


def test_r4_negative_d_two_incomparable_policies_are_not_ranked(pair):
    original, replayed = pair
    one = _confined(replayed, capabilities=("from-bundle", "closure-confined-filesystem"))
    other = _confined(replayed, capabilities=("from-bundle", "network-denied"))
    assert derive_scope(original.run, one, certification=None) == "same-environment"
    assert derive_scope(original.run, other, certification=None) == "same-environment"
    identity = replayed.run.recipe.environment.identity()
    assert qualifies(confined_receipt(instance=instance(environment_identity=identity)), identity)
    assert not qualifies(one.occurrence.receipt, identity) and not qualifies(other.occurrence.receipt, identity)


def test_r15_negative_a_minimal_pair_never_derives_clean_environment(pair):
    original, replayed = pair
    assert replayed.run.occurrence.receipt.capabilities == () and replayed.run.occurrence.receipt.instance is None
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"
    assert not qualifies(replayed.run.occurrence.receipt, replayed.run.recipe.environment.identity())
```

Append to `python/tests/test_verify.py` (imports: `from science.errors import NotAnAssessmentVerification`; `from science.verification import Verification`; `from science.verify import _mint_verification, admission_record`):

```python
# --- K5: the admission join ---------------------------------------------------
def test_k5_admission_record_is_the_total_projection_of_a_derived_verification(pair):
    verification = verification_of(pair)
    record = admission_record(verification)
    assert record == Verification(
        ref=verification.identity(),
        assessment=verification.assessment,
        scope=verification.scope,
        verdict=verification.verdict,
        supersedes=None,
    )
    assert set(inspect.signature(admission_record).parameters) == {"derived"}


def test_k5_admission_record_carries_supersedes(pair):
    base = verification_of(pair)
    superseding = _mint_verification(
        original=base.original,
        replayed=base.replayed,
        assessment=base.assessment,
        rule=base.rule,
        report=base.report,
        scope_rule=base.scope_rule,
        scope=base.scope,
        verdict=base.verdict,
        supersedes=base.identity(),
    )
    assert admission_record(superseding).supersedes == base.identity()


def test_k5_a_production_verification_is_refused_by_the_join(production_pair):
    first, second = production_pair
    verification = build_verification(
        first.run,
        second.run,
        specs={},
        held_rules={"impl-dataset-eq-1": DATASET_CONTENT_EQUALITY},
        contract_identity="contract-1",
        epoch="epoch-1",
    )
    with pytest.raises(NotAnAssessmentVerification):
        admission_record(verification)
```

(`inspect`, `DATASET_CONTENT_EQUALITY` and `build_verification` are already imported in `test_verify.py`; confirm, add if not.)

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run pytest tests/test_replay.py tests/test_verify.py -k "r4 or r15 or k5" | tail -3`
Expected: FAIL — `ImportError: cannot import name 'qualifies'`.

- [ ] **Step 3: Implement**

In `python/src/science/replay.py`: extend the `science.recipe` import to `from science.recipe import REQUIRED_FOR_CLEAN_ENVIRONMENT, BoundaryReceipt, ResultManifest, RunClosure`. Add before `derive_scope`:

```python
def qualifies(receipt: BoundaryReceipt, environment_identity: str) -> bool:
    """§7.3a over the closed vocabulary — containment, never an ordering — plus
    the fresh-instance conjunct, bound to the replayed recipe's environment
    (design §7.1). Reads the receipt only; a policy's identity string is
    nothing here."""
    if type(receipt) is not BoundaryReceipt:
        raise MalformedRecord("qualification reads a BoundaryReceipt")
    if receipt.instance is None:
        return False
    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.capabilities):
        return False
    return receipt.instance.environment_identity == environment_identity
```

In `derive_scope`, replace the two lines

```python
    if original.recipe.identity() == replayed.recipe.identity():
        return "same-environment"
```

with

```python
    if original.recipe.identity() == replayed.recipe.identity():
        if qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):
            return "clean-environment"
        return "same-environment"
```

(the `        return "same-environment"` line — eight spaces — stays, once). Change `"""Walk only the scope rows this boundary can attest."""` to `"""Walk every row of §7.3."""` and replace the trailing `derive_scope.__doc__ = ...` assignment with:

```python
derive_scope.__doc__ = """Derive verification scope from two conforming closures — every row of
§7.3. The `clean-environment` row is reached only through the replay's
receipt qualifying under §7.3a (conformance cut 13); the original's receipt is
not read, because the requirement is that the replay ran through the boundary.
"""
```

In `python/src/science/verify.py`: import `NotAnAssessmentVerification` from `science.errors` and `Verification` from `science.verification`; add `"admission_record",` to `__all__` immediately before `"build_verification",`; add after `active_verifications`:

```python
def admission_record(derived: AssessmentVerification) -> Verification:
    """The total projection from a derived assessment verification to the
    record `admit()` and belief evaluation read (design §7.2). No
    caller-supplied field. A production verification has no assessment to
    admit and is refused early."""
    if type(derived) is not AssessmentVerification:
        raise NotAnAssessmentVerification(f"{type(derived).__name__} has no assessment to admit")
    return Verification(
        ref=derived.identity(),
        assessment=derived.assessment,
        scope=derived.scope,
        verdict=derived.verdict,
        supersedes=derived.supersedes,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `cd python && set -o pipefail && uv run pytest tests/test_replay.py tests/test_verify.py tests/test_assess.py | tail -1 && uv run pytest tests/test_n2.py -k stale | tail -1 && uv run ruff check src/science/replay.py src/science/verify.py tests && uv run pyright src/science/replay.py src/science/verify.py | tail -1`
Expected: all passed; no stale anchors (cut 3's R4 arm still finds `        return "same-environment"` once); clean; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/replay.py python/src/science/verify.py python/tests/test_replay.py python/tests/test_verify.py
git commit -m "feat(replay): derive clean-environment through a qualifying receipt and join a derived verification to admission"
```

---

### Task 9: The acceptance layer — the confinement gate, the confined arms, the N2 harness, the runner

**Files:**
- Modify: `python/tests/acceptance/conftest.py` (the confinement gate)
- Modify: `python/tests/conftest.py` (`certified_work` honours `SCIENCE_CUT13_ROOT`)
- Modify: `python/tests/fixtures_cut3.py` (`replay_of` gains `cores=1` and `snakefile` pass-through already exists)
- Create: `python/tests/acceptance/test_confinement_acceptance.py`
- Create: `python/tests/acceptance/n2_arms_cut13.py`
- Create: `python/tests/acceptance/test_n2_cut13.py`
- Create: `python/tools/cut13_acceptance.py`

**Interfaces:**
- Consumes: every unit id from the frozen cut (Task 1); the freeze hash (ledger); every sabotage anchor quoted below, byte-exact from Tasks 3–8.
- Produces: `CUT13_ARMS`, `ROW_UNITS`, `LABELED_UNITS`, `CO_CITED`, `unit_of`; the `confined_host` fixture; the runner Task 10 executes.

- [ ] **Step 1: The confinement gate and the root variable**

Append to `python/tests/acceptance/conftest.py`:

```python
class ConfinementUnavailableHost(Exception):
    """The confined arms' own error, raised rather than skipped."""


@pytest.fixture()
def confined_host() -> None:
    """The confinement gate: bubblewrap with --info-fd, unprivileged user
    namespaces, and the loader's --list. It errors and never skips — an
    environment that cannot exercise confinement must not be able to report
    cut-13 discharge. No durable root is involved."""
    from science.confinement import host_prerequisites

    reason = host_prerequisites()
    if reason is not None:
        raise ConfinementUnavailableHost(
            f"the confined acceptance arms need bubblewrap and user namespaces on this host; {reason}. "
            "This is an error and not a skip."
        )
```

In `python/tests/conftest.py`, change `certified_work`'s lookup to `configured = os.environ.get("SCIENCE_CUT10_ROOT") or os.environ.get("SCIENCE_CUT12_ROOT") or os.environ.get("SCIENCE_CUT13_ROOT")`.

In `python/tests/fixtures_cut3.py`, give `replay_of` a `cores=1` keyword parameter and pass `cores=cores` to `replay(...)`.

- [ ] **Step 2: Write the confined acceptance arms**

`python/tests/acceptance/test_confinement_acceptance.py`:

```python
"""Cut 13's confined arms: every check that executes under confined-v1.

They need the confinement gate and no durable root. One snapshot serves the
module (`shared_scratch`), so the closure is materialized once."""

from __future__ import annotations

import dataclasses
import socket
from pathlib import Path

import pytest
from fixtures_cut3 import (
    MEMORY_PORT,
    SNAKEFILE_DETERMINISTIC,
    interp,
    replay_of,
    run_assessment,
    spec_draft,
    spec_rules,
)
from test_assess import observations_for
from test_belief import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PROFILE
from test_verify import verification_of

import science.boundary as boundary_module
from science.admission import Admitted, AdmissionRefused, admit
from science.assess import build_assessment, run_record
from science.belief import Availability, Belief, NoBelief, Records, SuppliedContext, evaluate
from science.boundary import RunMinted, RunRefused
from science.closure import RetractionEnumeration
from science.consulted import CorpusPins
from science.dataset import dataset_address
from science.lineage import LineageSnapshot
from science.policy import PolicyBinding
from science.recipe import CAPABILITIES, CONFINED_POLICY, MINIMAL_POLICY, NAMESPACES
from science.replay import CONFORMING, EquivalenceImplementation, conformance, derive_scope
from science.spec import freeze
from science.verify import admission_record

pytestmark = pytest.mark.usefixtures("confined_host")

SNAKEFILE_UNDECLARED_READ = SNAKEFILE_DETERMINISTIC.replace(
    "        text = pathlib.Path(input[0]).read_text()",
    '        pathlib.Path("/etc/passwd").read_text()\n        text = pathlib.Path(input[0]).read_text()',
)
SNAKEFILE_WRITE_OUTSIDE = SNAKEFILE_DETERMINISTIC.replace(
    "        text = pathlib.Path(input[0]).read_text()",
    '        pathlib.Path("/escaped.txt").write_text("x")\n        text = pathlib.Path(input[0]).read_text()',
)
SNAKEFILE_CORES_SENSITIVE = """\
import json, pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        planned = int(config["seed_model_initialization"])
        seed = planned if workflow.cores == 1 else planned + 1
        pathlib.Path(".seeds").mkdir(exist_ok=True)
        pathlib.Path(".seeds/transform.json").write_text(
            json.dumps({"transform": {"model-initialization": seed}}))
        pathlib.Path(output[0]).write_text(pathlib.Path(input[0]).read_text().upper())
"""


def snakefile_connecting_to(port: int) -> str:
    return SNAKEFILE_DETERMINISTIC.replace(
        "        text = pathlib.Path(input[0]).read_text()",
        f'        __import__("socket").create_connection(("127.0.0.1", {port}), timeout=2).close()\n'
        "        text = pathlib.Path(input[0]).read_text()",
    )


def snakefile_importing_from(directory: Path) -> str:
    return SNAKEFILE_DETERMINISTIC.replace(
        "import json, pathlib, random",
        f'import sys; sys.path.insert(0, "{directory}"); import secret\nimport json, pathlib, random',
    )


@pytest.fixture(scope="module")
def shared_scratch(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("confined-scratch")


def confined(tmp_path: Path, shared_scratch: Path, **kwargs):
    return run_assessment(tmp_path, port=MEMORY_PORT, boundary_policy=CONFINED_POLICY, scratch_base=shared_scratch, **kwargs)


def minimal(tmp_path: Path, **kwargs):
    return run_assessment(tmp_path, port=MEMORY_PORT, boundary_policy=MINIMAL_POLICY, **kwargs)


def confined_pair(tmp_path: Path, shared_scratch: Path, *, snakefile=SNAKEFILE_DETERMINISTIC, replay_cores=1):
    original = confined(tmp_path / "original", shared_scratch, snakefile=snakefile)
    assert isinstance(original, RunMinted), original
    replayed = replay_of(original, tmp_path / "replayed", port=MEMORY_PORT, snakefile=snakefile, scratch_base=shared_scratch, cores=replay_cores)
    assert isinstance(replayed, RunMinted), replayed
    return original, replayed


def belief_over(minted: RunMinted, verification) -> Belief | NoBelief:
    spec = freeze(spec_draft(), held_rules=spec_rules())
    assessment = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    run_value = run_record(minted.run)
    observed = tuple(dataset_address(entry.dataset) for entry in run_value.inputs if entry.role == "observes")
    records = Records(
        claims={},
        assessments=(assessment,),
        runs={run_value.ref: run_value},
        source_assertions=(),
        verifications=(verification,) if verification is not None else (),
    )
    availability = Availability(
        observations=observations_for(run_value),
        implementations={BELIEF_V1.identity: BELIEF_V1},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )
    context = SuppliedContext(
        snapshot=LineageSnapshot(roots=tuple(root for root in observed if root is not None), bases={}, producers={}),
        producer_snapshot_identity="snap-1",
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        node_corpus={assessment.identity(): "c1"},
        pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
    )
    outcome = evaluate(
        proposition=assessment.proposition,
        records=records,
        availability=availability,
        context=context,
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        profile=PROFILE,
    )
    assert isinstance(outcome, (Belief, NoBelief)), outcome
    return outcome


def admission_of(minted: RunMinted, verification):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    assessment = build_assessment(minted.run, specs={spec.identity: spec}, implementations=interp())
    run_value = run_record(minted.run)
    return admit(assessment, run_value, observations_for(run_value), (verification,))


# --- R15 ------------------------------------------------------------------------
def test_r15u1_a_bundled_file_edited_after_capture_yields_no_run_and_the_engine_never_starts(tmp_path, shared_scratch, monkeypatch):
    real_capture = boundary_module.capture_bundle
    real_launch = boundary_module.launch_confined
    launched: list[bool] = []

    def capture_then_edit(code_roots, bundle_dir):
        identity = real_capture(code_roots, bundle_dir)
        (bundle_dir / "code" / "helper.py").write_text("VALUE = 2\n")
        return identity

    def spy(**kwargs):
        launched.append(True)
        return real_launch(**kwargs)

    monkeypatch.setattr(boundary_module, "capture_bundle", capture_then_edit)
    monkeypatch.setattr(boundary_module, "launch_confined", spy)
    outcome = confined(tmp_path, shared_scratch)
    assert isinstance(outcome, RunRefused) and outcome.reason == "closure-mutated", outcome
    assert outcome.intent is not None and outcome.report is not None
    assert launched == []


def test_r15u2_a_bundled_file_edited_after_exit_yields_no_run(tmp_path, shared_scratch, monkeypatch):
    real_launch = boundary_module.launch_confined

    def launch_then_edit(*, plan, environment, inner_argv, captured):
        result = real_launch(plan=plan, environment=environment, inner_argv=inner_argv, captured=captured)
        bundle = Path(dict(plan.host_mapping())["/science/bundle"])
        (bundle / "code" / "helper.py").write_text("VALUE = 3\n")
        return result

    monkeypatch.setattr(boundary_module, "launch_confined", launch_then_edit)
    outcome = confined(tmp_path, shared_scratch)
    assert isinstance(outcome, RunRefused) and outcome.reason == "closure-mutated", outcome


def test_r15u3_an_undeclared_file_read_fails_closed(tmp_path, shared_scratch):
    assert isinstance(minimal(tmp_path / "host", snakefile=SNAKEFILE_UNDECLARED_READ), RunMinted)
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=SNAKEFILE_UNDECLARED_READ)
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "FileNotFoundError" in outcome.detail or "No such file" in outcome.detail


def test_r15u4_an_undeclared_network_connection_fails_closed(tmp_path, shared_scratch):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(4)
    port = listener.getsockname()[1]
    try:
        assert isinstance(minimal(tmp_path / "host", snakefile=snakefile_connecting_to(port)), RunMinted)
        outcome = confined(tmp_path / "confined", shared_scratch, snakefile=snakefile_connecting_to(port))
    finally:
        listener.close()
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "ConnectionRefused" in outcome.detail or "Errno 111" in outcome.detail


def test_r15u5_the_receipt_names_the_capabilities_observed_in_force(tmp_path, shared_scratch):
    outcome = confined(tmp_path / "confined", shared_scratch)
    assert isinstance(outcome, RunMinted), outcome
    receipt = outcome.run.occurrence.receipt
    assert receipt.confined and receipt.capabilities == CAPABILITIES
    assert receipt.instance is not None
    assert tuple(sorted(receipt.instance.namespaces)) == NAMESPACES
    assert receipt.instance.environment_identity == outcome.run.recipe.environment.identity()
    assert all(part.startswith("/science/") or not part.startswith("/") for part in receipt.argv)
    assert dict(receipt.mounts)["/science/bundle"].startswith(str(shared_scratch))
    assert not any(str(shared_scratch) in value for _, _, value in receipt.rendered_environment)
    plain = minimal(tmp_path / "host")
    assert isinstance(plain, RunMinted) and plain.run.occurrence.receipt.capabilities == () and plain.run.occurrence.receipt.instance is None


def test_r15u6_a_minimal_run_is_valid_and_a_minimal_pair_stays_same_environment(tmp_path):
    original = minimal(tmp_path / "original")
    assert isinstance(original, RunMinted)
    replayed = replay_of(original, tmp_path / "replayed", port=MEMORY_PORT)
    assert isinstance(replayed, RunMinted)
    assert conformance(original.run) == CONFORMING and conformance(replayed.run) == CONFORMING
    assert derive_scope(original.run, replayed.run, certification=None) == "same-environment"


# --- R4 ---------------------------------------------------------------------------
def test_r4u1_a_confined_pair_derives_clean_environment(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert derive_scope(original.run, replayed.run, certification=None) == "clean-environment"


def test_end_to_end_a_passing_clean_environment_verification_admits_and_yields_belief(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    verification = verification_of((original, replayed))
    assert verification.scope == "clean-environment" and verification.verdict == "passed"
    record = admission_record(verification)
    assert isinstance(admission_of(original, record), Admitted)
    assert isinstance(belief_over(original, record), Belief)


# --- R9, R13, R16 ------------------------------------------------------------------
def test_r9u1_an_inconclusive_verification_admits_nothing(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch)
    unreadable = EquivalenceImplementation(identity="impl-eq-1", evaluate=lambda left, right: "inconclusive", fixtures=())
    verification = verification_of((original, replayed), held_rules={"impl-eq-1": unreadable})
    assert verification.verdict == "inconclusive" and verification.scope == "clean-environment"
    verdict = admission_of(original, admission_record(verification))
    assert isinstance(verdict, AdmissionRefused) and verdict.reason.startswith("not-admitted-verification-state")


def test_r13u1_an_import_outside_the_closure_is_refused_under_confinement_and_minted_under_minimal(tmp_path, shared_scratch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("VALUE = 42\n")
    snakefile = snakefile_importing_from(outside)
    assert isinstance(minimal(tmp_path / "host", snakefile=snakefile), RunMinted)
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=snakefile)
    assert isinstance(outcome, RunRefused), outcome  # a refusal, and nothing about its diagnostic (spec §8)


def test_r16u1_a_not_certified_pair_admits_nothing(tmp_path, shared_scratch):
    original, replayed = confined_pair(tmp_path, shared_scratch, snakefile=SNAKEFILE_CORES_SENSITIVE, replay_cores=2)
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert original.run.occurrence.receipt.confined and replayed.run.occurrence.receipt.confined
    assert original.run.result == replayed.run.result
    assert conformance(original.run) == CONFORMING and conformance(replayed.run) != CONFORMING
    verification = verification_of((original, replayed))
    assert verification.scope == "not-certified" and verification.verdict == "passed"
    record = admission_record(verification)
    assert isinstance(admission_of(original, record), AdmissionRefused)
    assert belief_over(original, record) == belief_over(original, None)
    assert isinstance(belief_over(original, record), NoBelief)


# --- R21 --------------------------------------------------------------------------
def test_r21u1_a_write_outside_the_output_root_fails_closed(tmp_path, shared_scratch):
    outcome = confined(tmp_path / "confined", shared_scratch, snakefile=SNAKEFILE_WRITE_OUTSIDE)
    assert isinstance(outcome, RunRefused), outcome
    assert outcome.reason == "execution-failed", (outcome.reason, outcome.detail)
    assert "Read-only file system" in outcome.detail or "EROFS" in outcome.detail


def test_r21u2_two_differently_mounted_scratch_roots_yield_equal_recipes_and_clean_environment(tmp_path, shared_scratch):
    other_scratch = tmp_path / "other-mount"
    original = confined(tmp_path / "original", shared_scratch)
    assert isinstance(original, RunMinted), original
    replayed = replay_of(original, tmp_path / "replayed", port=MEMORY_PORT, scratch_base=other_scratch)
    assert isinstance(replayed, RunMinted), replayed
    assert original.run.recipe.identity() == replayed.run.recipe.identity()
    assert original.run.occurrence.receipt.scratch_mapping != replayed.run.occurrence.receipt.scratch_mapping
    assert original.run.occurrence.receipt.argv == replayed.run.occurrence.receipt.argv
    assert derive_scope(original.run, replayed.run, certification=None) == "clean-environment"
    import json

    assert str(other_scratch) not in json.dumps(replayed.run.recipe._projection())
```

Run: `cd python && set -o pipefail && uv run pytest tests/acceptance/test_confinement_acceptance.py | tail -3`
Expected: all 13 passed on a host meeting the gate. Every assertion on `outcome.detail` reads the engine's captured output; if this Snakemake version phrases an error differently, match on what it actually prints (the `detail` is in the failure message) — never loosen the `reason` assertion.

- [ ] **Step 3: Declare the arms**

`python/tests/acceptance/n2_arms_cut13.py`:

```python
"""Cut 13's declared arms: 15 selected + 7 labeled = 22 units, 35 lettered arms.

Every sabotage is host-side (cut 13 §5 item 1): the sandbox's science tree is
the closure's own copy, so probe.py is never sabotaged."""

from n2_arms import Arm, Sabotage

_BOUNDARY = "boundary.py"
_CONFINEMENT = "confinement.py"
_ADAPTER = "adapter.py"
_RECIPE = "recipe.py"
_REPLAY = "replay.py"
_VERIFY = "verify.py"
_RUNRECORD = "runrecord.py"

_ACCEPT = "acceptance/test_confinement_acceptance.py"
_QUALIFY_LINE = '        if qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):'
_CONTAINMENT = '    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.capabilities):\n        return False'
_REMOUNT = '    argv.extend(["--remount-ro", "/", "--chdir", OUTPUT_ROOT])'

CUT13_ARMS = (
    # --- R15 ---
    Arm("R15u1", "a bundled file edited after capture yields no run and the engine never starts",
        Sabotage(_BOUNDARY,
            before='    check_bundle_intact(bundle, code_identity)\n    inputs_before = fingerprint(output_root / "inputs")',
            after='    inputs_before = fingerprint(output_root / "inputs")'),
        (f"{_ACCEPT}::test_r15u1_a_bundled_file_edited_after_capture_yields_no_run_and_the_engine_never_starts",)),
    Arm("R15u2", "a bundled file edited after exit yields no run",
        Sabotage(_BOUNDARY,
            before='    check_closure_intact(bundle=bundle, code_identity=code_identity, snapshot=snapshot, captured=captured, inputs=output_root / "inputs", inputs_fingerprint=inputs_before)',
            after='    pass'),
        (f"{_ACCEPT}::test_r15u2_a_bundled_file_edited_after_exit_yields_no_run",)),
    Arm("R15u3", "an undeclared file read fails closed",
        Sabotage(_CONFINEMENT,
            before=_REMOUNT,
            after='    argv.extend(["--ro-bind", "/etc", "/etc", "--remount-ro", "/", "--chdir", OUTPUT_ROOT])'),
        (f"{_ACCEPT}::test_r15u3_an_undeclared_file_read_fails_closed",)),
    Arm("R15u4", "an undeclared network connection fails closed",
        Sabotage(_CONFINEMENT,
            before='        "--unshare-all",',
            after='        "--unshare-user",\n        "--unshare-pid",\n        "--unshare-ipc",\n        "--unshare-uts",\n        "--unshare-cgroup",'),
        (f"{_ACCEPT}::test_r15u4_an_undeclared_network_connection_fails_closed",)),
    Arm("R15u5", "the receipt names the capabilities observed in force",
        Sabotage(_BOUNDARY,
            before='        capabilities=launched.capabilities,',
            after='        capabilities=(),'),
        (f"{_ACCEPT}::test_r15u5_the_receipt_names_the_capabilities_observed_in_force",)),
    Arm("R15u6", "a minimal run is valid and a minimal pair never derives clean-environment",
        Sabotage(_REPLAY, before=_QUALIFY_LINE, after='        if True:'),
        ("test_replay.py::test_r15_negative_a_minimal_pair_never_derives_clean_environment",
         f"{_ACCEPT}::test_r15u6_a_minimal_run_is_valid_and_a_minimal_pair_stays_same_environment")),
    # --- R4 ---
    Arm("R4u1", "the clean-environment row is reached by a confined pair through a qualifying receipt",
        Sabotage(_REPLAY,
            before='            return "clean-environment"',
            after='            return "not-certified"'),
        (f"{_ACCEPT}::test_r4u1_a_confined_pair_derives_clean_environment",
         f"{_ACCEPT}::test_end_to_end_a_passing_clean_environment_verification_admits_and_yields_belief",
         "test_replay.py::test_r4_the_clean_environment_row_is_reached_only_through_a_qualifying_receipt")),
    Arm("R4u2", "a receipt missing a required capability derives same-environment",
        Sabotage(_REPLAY, before=_CONTAINMENT, after='    if False:\n        return False'),
        ("test_replay.py::test_r4_negative_d_a_receipt_missing_a_required_capability_derives_same_environment",)),
    Arm("R4u3", "a policy providing every capability qualifies whatever its identity string",
        Sabotage(_REPLAY,
            before=_QUALIFY_LINE,
            after='        if replayed.recipe.boundary_policy.identity == "boundary-policy/confined-v1" and qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):'),
        ("test_replay.py::test_r4_negative_d_a_policy_qualifies_whatever_its_version_string",)),
    Arm("R4u4", "two incomparable policies are not ranked",
        Sabotage(_REPLAY, before=_CONTAINMENT, after='    if len(receipt.capabilities) < 2:\n        return False'),
        ("test_replay.py::test_r4_negative_d_two_incomparable_policies_are_not_ranked",)),
    # --- R9, R13, R16 ---
    Arm("R9u1", "admission does not follow an inconclusive verification",
        Sabotage(_VERIFY, before='        verdict=derived.verdict,', after='        verdict="passed",'),
        (f"{_ACCEPT}::test_r9u1_an_inconclusive_verification_admits_nothing",)),
    Arm("R13u1", "an import outside the bundle and the held environment is refused",
        # The boundary ceases refusing: a failed confined execution is minted.
        Sabotage(_BOUNDARY, before='    if launched.returncode != 0:', after='    if False:'),
        (f"{_ACCEPT}::test_r13u1_an_import_outside_the_closure_is_refused_under_confinement_and_minted_under_minimal",)),
    Arm("R16u1", "a not-certified pair with qualifying receipts admits nothing",
        Sabotage(_VERIFY, before='        scope=derived.scope,', after='        scope="clean-environment",'),
        (f"{_ACCEPT}::test_r16u1_a_not_certified_pair_admits_nothing",)),
    # --- R21 ---
    Arm("R21u1", "a write outside the output root fails closed",
        Sabotage(_CONFINEMENT, before=_REMOUNT, after='    argv.extend(["--chdir", OUTPUT_ROOT])'),
        (f"{_ACCEPT}::test_r21u1_a_write_outside_the_output_root_fails_closed",)),
    Arm("R21u2", "two differently mounted scratch roots yield equal recipes and clean-environment",
        Sabotage(_BOUNDARY,
            before='            environment_identity=snapshot.name,',
            after='            environment_identity=str(scratch),'),
        (f"{_ACCEPT}::test_r21u2_two_differently_mounted_scratch_roots_yield_equal_recipes_and_clean_environment",)),
    # --- K1: the policy match ---
    Arm("K1a", "the policy match is the entire definition",
        Sabotage(_RECIPE,
            before='        if (policy.identity, policy.scope_rule, frozenset(policy.capabilities)) == (known.identity, known.scope_rule, frozenset(known.capabilities)):',
            after='        if (policy.identity, frozenset(policy.capabilities)) == (known.identity, frozenset(known.capabilities)):'),
        ("test_confinement_values.py::test_k1_a_known_identity_with_another_scope_rule_is_unsupported",
         "test_boundary.py::test_k1_an_unsupported_policy_refuses_before_intent")),
    Arm("K1b", "a duplicate capability is unspellable",
        Sabotage(_RECIPE,
            before='        if len(set(self.capabilities)) != len(self.capabilities):\n            raise MalformedClosure("boundary policy capabilities name each capability once")',
            after='        if False:\n            raise MalformedClosure("boundary policy capabilities name each capability once")'),
        ("test_confinement_values.py::test_k1_a_duplicate_capability_is_unspellable",)),
    # --- K2: the snapshot ---
    Arm("K2a", "an existing mismatching snapshot refuses and is never rebuilt",
        Sabotage(_CONFINEMENT,
            before='    if target.exists():\n        verify_snapshot(target, captured)\n        return target',
            after='    if target.exists():\n        shutil.rmtree(target)'),
        ("test_confinement.py::test_k2_an_existing_mismatching_snapshot_refuses_and_is_never_rebuilt",)),
    Arm("K2b", "a concurrent winner is verified before it is reused",
        Sabotage(_CONFINEMENT,
            before='    except OSError:\n        shutil.rmtree(build, ignore_errors=True)\n        verify_snapshot(target, captured)',
            after='    except OSError:\n        shutil.rmtree(build, ignore_errors=True)'),
        ("test_confinement.py::test_k2_a_concurrent_winner_is_verified_and_reused_or_refused",)),
    # --- K3: receipt validation ---
    Arm("K3a", "a mount plan identity disagreeing with its mounts is malformed",
        Sabotage(_RECIPE,
            before='        if self.mount_plan_identity != mount_plan_identity(self.mounts):',
            after='        if False:'),
        ("test_confinement_values.py::test_k3_a_mount_plan_identity_disagreeing_with_its_mounts_is_malformed",)),
    Arm("K3b", "the confined members are all present or all absent",
        Sabotage(_RECIPE, before='        if present not in (0, 3):', after='        if False:'),
        ("test_confinement_values.py::test_k3_the_confined_members_are_all_present_or_all_absent",)),
    Arm("K3c", "the wire refuses a mount plan identity disagreeing with its mounts",
        Sabotage(_RUNRECORD,
            before='            _refuse("$.occurrence.receipt.instance.mount_plan_identity", "is not the digest of its own mounts")',
            after='            pass'),
        ("test_runrecord_confined.py::test_k3_a_wire_mount_plan_identity_disagreeing_with_its_mounts_is_refused",)),
    # --- K4: the domains ---
    Arm("K4a", "the minimal receipt projection is byte-stable under v1",
        Sabotage(_RECIPE,
            before='    if not receipt.confined:\n        return projection',
            after='    if False:\n        return projection'),
        ("test_confinement_values.py::test_k4_the_minimal_receipt_projection_is_byte_stable_under_v1",)),
    Arm("K4b", "a confined receipt makes a run.v2 run",
        Sabotage(_RECIPE,
            before='    return CONFINED_RUN_DOMAIN if confined else RUN_DOMAIN',
            after='    return RUN_DOMAIN'),
        ("test_confinement_values.py::test_k4_a_confined_receipt_makes_a_v2_run",
         "test_runrecord_confined.py::test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2")),
    Arm("K4c", "the wire recomputes under the domain the receipt shape names",
        Sabotage(_RUNRECORD,
            before='    address = v1.digest(run_domain_for(_is_confined_receipt(occurrence_view["receipt"])), parsed)',
            after='    address = v1.digest(run_domain_for(False), parsed)'),
        ("test_runrecord_confined.py::test_k4_a_confined_projection_round_trips_and_recomputes_under_run_v2",)),
    # --- K5: the join ---
    Arm("K5a", "admission_record carries supersedes",
        Sabotage(_VERIFY, before='        supersedes=derived.supersedes,', after='        supersedes=None,'),
        ("test_verify.py::test_k5_admission_record_carries_supersedes",)),
    Arm("K5b", "a production verification is refused by the join",
        Sabotage(_VERIFY,
            before='    if type(derived) is not AssessmentVerification:\n        raise NotAnAssessmentVerification(',
            after='    if False:\n        raise NotAnAssessmentVerification('),
        ("test_verify.py::test_k5_a_production_verification_is_refused_by_the_join",)),
    # --- K6: the gate ---
    Arm("K6a", "a namespace equal to the parent's refuses",
        Sabotage(_CONFINEMENT,
            before='    if missing := [name for name in NAMESPACES if name not in facts.distinct]:',
            after='    if False:'),
        ("test_confinement.py::test_k6_a_namespace_equal_to_the_parents_refuses",)),
    Arm("K6b", "a mount table unequal to the plan refuses",
        Sabotage(_CONFINEMENT, before='    if facts.mounts != plan.expected:', after='    if False:'),
        ("test_confinement.py::test_k6_a_mount_table_unequal_to_the_plan_refuses",)),
    Arm("K6c", "an environment unequal to the declared set refuses",
        Sabotage(_CONFINEMENT, before='    if dict(environ) != dict(environment):', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    Arm("K6d", "a routable network refuses",
        Sabotage(_CONFINEMENT, before='    if network["ipv4"] != "ENETUNREACH":', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    Arm("K6e", "a loader map unequal to the capture refuses",
        Sabotage(_CONFINEMENT, before='    if set(reported) != set(expected):', after='    if False:'),
        ("test_confinement.py::test_k6_each_report_deviation_refuses",)),
    # --- K7: closure refusals ---
    Arm("K7a", "a SONAME collision is refused",
        Sabotage(_ADAPTER,
            before='                if existing is not None and existing != located:',
            after='                if False:'),
        ("test_closure_capture.py::test_k7_a_soname_collision_is_refused",)),
    Arm("K7b", "a symlink escaping the closure is refused",
        Sabotage(_ADAPTER,
            before='            if target_root is None:\n                raise ClosureUnsupported(f"symlink {located} -> {target!r} escapes the closure")',
            after='            if target_root is None:\n                target_root = root'),
        ("test_closure_capture.py::test_k7_a_symlink_escaping_the_closure_is_refused",)),
    Arm("K7c", "a mixed .pth is refused",
        Sabotage(_ADAPTER, before='            if imports and paths:', after='            if False:'),
        ("test_closure_capture.py::test_k7_a_mixed_pth_is_refused",)),
)

_UNIT_OF_LETTERED = {
    "K1a": "K1", "K1b": "K1",
    "K2a": "K2", "K2b": "K2",
    "K3a": "K3", "K3b": "K3", "K3c": "K3",
    "K4a": "K4", "K4b": "K4", "K4c": "K4",
    "K5a": "K5", "K5b": "K5",
    "K6a": "K6", "K6b": "K6", "K6c": "K6", "K6d": "K6", "K6e": "K6",
    "K7a": "K7", "K7b": "K7", "K7c": "K7",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"R15": 6, "R4": 4, "R9": 1, "R13": 1, "R16": 1, "R21": 2}
LABELED_UNITS: tuple[str, ...] = tuple(f"K{number}" for number in range(1, 8))

#: No cut-13 arm cites a prior cut's check.
CO_CITED: dict[str, tuple[str, ...]] = {}
```

Before committing, verify every `before` occurs exactly once: `cd python && uv run python -c "import sys; sys.path[:0]=['tests','tests/acceptance']; from n2_arms_cut13 import CUT13_ARMS; from pathlib import Path; p=Path('src/science'); bad=[(a.row,(p/a.sabotage.module).read_text().count(a.sabotage.before)) for a in CUT13_ARMS if (p/a.sabotage.module).read_text().count(a.sabotage.before)!=1]; print('anchors ok' if not bad else bad)"` — expected `anchors ok`. A miscount means a Task 3–8 line was spelled differently from this plan; fix the **arm** to the code as written, never the code to the arm, and note it in the ledger.

- [ ] **Step 4: The N2 harness**

`python/tests/acceptance/test_n2_cut13.py` — copy `test_n2_cut12.py` and change: the docstring to `"""Cut 13's declaration accounting, N2 audit, and lettered-arm partition."""`; import `CUT12_ARMS` from `n2_arms_cut12` and `CO_CITED, CUT13_ARMS, LABELED_UNITS, ROW_UNITS, unit_of` from `n2_arms_cut13`; `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-30-conformance-cut-13.md"`; `CUT13_FREEZE_COMMIT = "<the Task 1 freeze hash>"`; add to `FROZEN_PRIOR_CUT_FILES` the line `"python/tests/acceptance/n2_arms_cut12.py": "<git log -1 --format=%h -- python/tests/acceptance/n2_arms_cut12.py>",`; `PRIOR_ARMS = (*CUT5_ARMS, …, *CUT11_ARMS, *CUT12_ARMS)`; every `CUT12_ARMS` in the audit and table tests becomes `CUT13_ARMS`, `cut-12` in messages becomes `cut-13`, the class names `TestEveryCut13ArmAssertsSomething`; `test_the_declared_arms_are_unique_and_number_fifty` becomes `..._number_thirty_five` asserting `== 35`; `test_the_frozen_cut_states_the_same_accounting` asserts `(15, 7, 22)` and `ROW_UNITS`; `test_every_check_lives_in_a_cut13_file` asserts the set

```python
{
    "acceptance/test_confinement_acceptance.py",
    "test_boundary.py",
    "test_closure_capture.py",
    "test_confinement.py",
    "test_confinement_values.py",
    "test_replay.py",
    "test_runrecord_confined.py",
    "test_verify.py",
}
```

`test_the_k_prefix_names_no_frozen_prior_guarantee_unit` stays; and the final partition test becomes:

```python
def test_the_partition_accounts_exactly_the_22_frozen_units() -> None:
    assert ROW_UNITS == {"R15": 6, "R4": 4, "R9": 1, "R13": 1, "R16": 1, "R21": 2}
    assert LABELED_UNITS == tuple(f"K{number}" for number in range(1, 8))
    expected = (
        {f"R15u{number}" for number in range(1, 7)}
        | {f"R4u{number}" for number in range(1, 5)}
        | {"R9u1", "R13u1", "R16u1", "R21u1", "R21u2"}
        | set(LABELED_UNITS)
    )
    assert {unit_of(arm.row) for arm in CUT13_ARMS} == expected
```

- [ ] **Step 5: The runner**

`python/tools/cut13_acceptance.py` — copy `cut12_acceptance.py` and change: the docstring to name cut 13 and its three phases (`the unedited cut-12 prefix, the confined cut-13 arms, then cut-13's N2 audit`) and add `The confined arms need no durable root; the prefix does — both prerequisites are probed first.`; `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut13-acceptance"`; `PREFIX_RUNNERS = ("cut12_acceptance.py",)`; `PHASE_MODULES = ("test_confinement_acceptance.py", "test_n2_cut13.py")`; `work_directory` reads `SCIENCE_CUT13_ROOT`; `declared_arm_count` imports `CUT13_ARMS`; `cut_environment` ranges `range(4, 14)`; `run_prefix` sets `SCIENCE_CUT12_ROOT`; every `cut-12`/`cut12` in messages becomes `cut-13`/`cut13`; the final print names `35`, `CUT13_ARMS`, `22 frozen units`, `test_the_partition_accounts_exactly_the_22_frozen_units`. Extend `probe` so that after the durable probe returns `None` it also checks confinement:

```python
    from science.confinement import host_prerequisites

    reason = host_prerequisites()
    if reason is not None:
        return f"ConfinementUnavailable: {reason}"
```

(inside the `try`, after `init_store_root(store_root)`, before `return None`), and extend the refusal message printed on `PROBE_REFUSED` with a second sentence: `A ConfinementUnavailable refusal means bubblewrap or user namespaces are missing; install bubblewrap or enable unprivileged user namespaces.`

- [ ] **Step 6: Run the new layers**

```bash
cd python && set -o pipefail && uv run pytest tests/acceptance/test_confinement_acceptance.py | tail -1 && uv run pytest tests/acceptance/test_n2_cut13.py | tail -1 && uv run ruff check tests tools && uv run pyright tools/cut13_acceptance.py | tail -1
```

Expected: `13 passed`; the N2 module all passed (every arm `sound`, the baseline `resolved`); clean; `0 errors`. The N2 audit runs each confined check in its own pytest against a sabotaged package copy, eight at a time — each materializes the snapshot under its own `tmp_path`, so this phase is slow (minutes); that is the cost of one copy per environment identity per process, and it is noted in the ledger.

- [ ] **Step 7: Commit**

```bash
git add python/tests/acceptance python/tests/conftest.py python/tests/fixtures_cut3.py python/tools/cut13_acceptance.py
git commit -m "test(cut13): declare the confinement arms, the gate, the N2 audit, and the acceptance runner"
```

---

### Task 10: Discharge

**Files:**
- Create: `docs/plans/<today>-conformance-cut-13-results.md`
- Modify: `docs/plans/2026-08-30-run-confinement-ledger.md`

- [ ] **Step 1: The portable gates on the whole tree**

```bash
cd python && set -o pipefail && uv run ruff check . && uv run pyright | tail -1 && uv run pytest | tail -1
```

Expected: clean; `0 errors`; the summary line. On this host the durable tests fail with the ext4 allowlist refusal until atoms is recertified on kernel 7.1.11 — if they do, record the summary line as measured **and** confirm with `uv run pytest 2>&1 | grep -c "durability allowlist"` that every failure is that refusal; the discharge of the confined arms does not depend on it, but the results record states the portable line honestly.

- [ ] **Step 2: The certified run**

```bash
cd python && set -o pipefail && uv run python tools/cut13_acceptance.py 2>&1 | tee ../.cut13-run.log | tail -20
```

Expected: `[cut13 phase 1/3] cut12_acceptance.py` … exit 0; `[cut13 phase 2/3] test_confinement_acceptance.py` `13 passed`; `[cut13 phase 3/3] test_n2_cut13.py` all passed; `declared arms: 35 …`; exit 0. A `PROBE_REFUSED` exit naming the durability allowlist is the recertification prerequisite (ledger R2), not a cut-13 failure: the confined arms can still be run alone with `uv run pytest tests/acceptance/test_confinement_acceptance.py tests/acceptance/test_n2_cut13.py`, and their summary lines recorded, but the cut is **not discharged** until the aggregate runner exits 0.

- [ ] **Step 3: Write the results record**

`docs/plans/<today>-conformance-cut-13-results.md`, every `<…>` a measured value:

```markdown
# Conformance cut 13 — discharge results

**Date:** <today>
**Subject:** run confinement, `clean-environment` reachable
(`../superpowers/specs/2026-08-30-run-confinement-design.md`, promoted to
`../designs/2026-08-30-run-confinement-design.md` at banking), measured
against conformance cut 13's frozen selection
(`../designs/2026-08-30-conformance-cut-13.md`).

The frozen cut remains byte-exact at `<freeze hash>`. Only its status header
changes at banking.

**Integration state.** Every implementation commit was made on
`design/run-confinement`. The reviewed pre-banking head is `<impl head>`.
The branch is not merged or pushed by this discharge; the human partner owns
the history-preserving `--no-ff` merge.

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

## 2. What ran

<as cut 12's record: host and tuple, the runner's three phase lines verbatim
with their pytest summary lines and exit, the portable and static gates with
their exits. State the bubblewrap version (`bwrap --version`) and the kernel.>

## 3. Review and implementation rulings

<the post-implementation review's finding count and closures, by ledger
ruling number; any anchor rewritten under Task 9 step 3's rule; the mount
table bubblewrap produced (ledger R3); the observed wall-clock cost of a
confined run against a minimal one.>

There is no frozen-cut deviation.

## 4. Commit identities

| commit | subject |
|---|---|
<one row per commit from `git log --oneline main..HEAD`, oldest first>

The banking commit following this record changes no runtime behavior.

## 5. Remaining boundary

Cut 13 closes R15, R4, R9 and R13 and reads R16 and R21 at their
confinement arms. Their workflow arms remain with `workflow-surface`, now
tier 1 row 1. Durable verification publication crosses the persistence seam
and is recorded as the `verification-publication` boundary at banking.
```

Then delete `.cut13-run.log`.

- [ ] **Step 4: Close the ledger and commit**

Append the discharge ruling (`R<n> — discharged at <HEAD short hash> on <host tuple>, bubblewrap <version>; the three phase summaries are in the results record`), then:

```bash
git add docs/plans/<today>-conformance-cut-13-results.md docs/plans/2026-08-30-run-confinement-ledger.md
git commit -m "docs(plans): record conformance cut 13's discharge"
```

---

### Task 11: Banking

**Files:**
- Move: `docs/superpowers/specs/2026-08-30-run-confinement-design.md` → `docs/designs/2026-08-30-run-confinement-design.md`
- Modify: `docs/designs/2026-08-30-conformance-cut-13.md:3-5` (the `**Status:**` line only)
- Modify: `docs/designs/2026-08-11-conformance-cut-3.md` (one dated correction under §3's confinement paragraph)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md`, `python/tools/roadmap_status.py`
- Modify: `README.md`, `docs/guide/README.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/computation-and-reproducibility.md`, `python/tests/test_designs_corpus.py` (`_COUNT_WORDS` for 42 if missing)

- [ ] **Step 1: Promote the spec and close both status lines**

```bash
git mv docs/superpowers/specs/2026-08-30-run-confinement-design.md docs/designs/2026-08-30-run-confinement-design.md
```

Set the promoted design's `**Status:**` to: `implemented and discharged <today> at `<impl head>`; conformance cut 13 froze before implementation at `<freeze hash>` and its 22 units passed through 35 lettered sabotage arms on a host meeting the confinement gate and carrying the certified tuple. Results: `../plans/<today>-conformance-cut-13-results.md`; execution rulings: `../plans/2026-08-30-run-confinement-ledger.md`. Promoted from `docs/superpowers/specs/` in this banking change.` Update its relative links (`../../designs/…` → `.`-relative, `../../plans/…` → `../plans/…`).

Set the cut's `**Status:**` to: `**Discharged <today> at `<impl head>`** — all 22 frozen units passed through 35 lettered sabotage arms; the confined arms ran under the confinement gate, the cut-12 prefix on the certified tuple; the portable suite reported <N> passing tests, Ruff and Pyright were clean. Results: `../plans/<today>-conformance-cut-13-results.md`. The cut remains frozen byte-exact at `<freeze hash>`; the specification was promoted to `2026-08-30-run-confinement-design.md` at banking.` Nothing below the status line changes.

Add the README design-table row after the cut-13 row:

```markdown
| `2026-08-30-run-confinement-design.md` | the run-confinement slice: the confined boundary policy, the per-file runtime closure and its snapshot, the probe-gated bubblewrap launch observed from the boundary's own `/proc`, the confined receipt and run domains, `derive_scope`'s `clean-environment` row, and the value-level admission join |
```

and change `Forty-one documents` to `Forty-two documents` (adding `42: "Forty-two"` to `_COUNT_WORDS` if absent).

- [ ] **Step 2: The dated correction in cut 3 §3**

Directly after the paragraph beginning `**A scratch root is staging, not confinement.**`, add:

```markdown
> **Confinement landed <today>, conformance cut 13**
> (`2026-08-30-run-confinement-design.md`; results
> `../plans/<today>-conformance-cut-13-results.md`). `boundary-policy/confined-v1`
> executes inside a fresh namespaced materialization of the digest-verified
> runtime closure, and `clean-environment` is reachable through its receipt.
> `boundary-policy/minimal-v1` is unchanged and remains the scratch root this
> paragraph describes.
```

- [ ] **Step 3: The adoption ledger**

Rename `## Current state (2026-08-29)` to `## Current state (<today>)` and update every anchor naming it (`grep -rn 'current-state-2026-08-29' docs README.md`); change `**Implemented through conformance cut 12.**` to `**Implemented through conformance cut 13.**`; add to the bullet list:

```markdown
- **Run confinement** — the confined boundary policy: a run executes inside
  a fresh namespaced materialization of the digest-verified runtime closure,
  the receipt attests the observed capabilities and the fresh instance,
  `derive_scope` reaches `clean-environment`, and a derived verification
  admits to belief through `admission_record` (cut 13).
```

Remove the `run-confinement` row from the boundaries table and add, after `persistence-cut`'s row:

```markdown
| `verification-publication` | durable publication of verification records — a derived verification written into a corpus through the operation port, with admission evaluated over records read back | the persistence seam; no design names it yet (cut 13 §2) | admission over stored verifications rather than in-memory records |
```

In the table's `workflow-surface` row and wherever R16/R21 are described, nothing changes — their remaining arms were already the workflow surface's.

- [ ] **Step 4: Re-rank the roadmap**

In `python/tools/roadmap_status.py` add `13: ("conformance-cut-13-results §1", "R4, R9, R13, R15", "R16, R21"),` to `ACCOUNTING`. Run `cd python && uv run python tools/roadmap_status.py` — expected last line `Closed 68 of 151; open 83.`

Rewrite `docs/plans/2026-08-29-implementation-roadmap.md` whole: `**Ranked at:** cut 13, against the ledger's Current state (<today>)`; remove `run-confinement` from the Boundary index and tier 1, renumbering so `workflow-surface` is row 1 and `contract-cut` row 7; add `verification-publication` to the index (tier 2) and to tier 2 with prerequisite `the persistence seam — a design for durable verification records behind the store's own gate; cut 13 §7.2 kept the join value-level` and unblocks `admission over stored verifications`; replace Appendix A with the script's output; in Appendix B drop the R15, R4, R9 and R13 rows, and reword R16's and R21's remainders to name only their `workflow-surface` arms; Appendix C unchanged. Then:

```bash
cd python && set -o pipefail && uv run pytest tests/test_designs_corpus.py | tail -1
```

Expected: all passed — the join guard sees the same ids on both sides.

- [ ] **Step 5: The guide**

Add `../designs/2026-08-30-run-confinement-design.md` to the `sources:` of `docs/guide/contracts-and-adoption.md` and `docs/guide/computation-and-reproducibility.md`; add the new results record beside cut 12's in `contracts-and-adoption.md`'s sources and point its "newest results record" link at it; set both pages' `updated: <today>`; grep `cut 12` across `docs/guide/*.md` and correct every "implemented through cut 12" style claim to cut 13, bumping `updated` on each page touched. In `computation-and-reproducibility.md`, where the guide describes the boundary as unconfined or `clean-environment` as unreachable, correct the sentence and cite the design.

- [ ] **Step 6: Full gates and diff review**

```bash
cd python && set -o pipefail && uv run python tools/check_guide.py && echo CHECK_GUIDE_OK && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py | tail -1
cd .. && git diff --check main && echo DIFF_CHECK_CLEAN && git diff main --name-status
```

Expected: `CHECK_GUIDE_OK`; all passed; `DIFF_CHECK_CLEAN`; the file list contains only: the promoted design (R), the cut, cut 3, the adoption ledger, the roadmap, `roadmap_status.py`, `README.md`, the guide pages touched, the results record and ledger under `docs/plans/`, this plan, and under `python/`: `src/science/{adapter,boundary,confinement,errors,probe,recipe,replay,runrecord,verify}.py`, `tests/{conftest,fixtures_cut3,closure_fixtures,confinement_fixtures,test_adapter,test_boundary,test_capability_boundary,test_closure_capture,test_confinement,test_confinement_errors,test_confinement_values,test_designs_corpus,test_recipe,test_replay,test_runrecord_confined,test_verify}.py` plus any test file Task 3 step 4 or Task 7 step 3 touched, `tests/acceptance/{conftest,n2_arms_cut13,test_n2_cut13,test_confinement_acceptance}.py`, `tools/cut13_acceptance.py`. Anything else is out of scope — revert it.

- [ ] **Step 7: Commit**

```bash
git add -A docs README.md python/tools/roadmap_status.py python/tests/test_designs_corpus.py
git commit -m "docs: bank the run-confinement slice, close R15, and re-rank the roadmap at cut 13"
git log --oneline main..HEAD
```

The branch is then ready for the human-owned `--no-ff` merge into `main`. The next cut — `workflow-surface` — is its own brainstorming session against computation §6.4.
