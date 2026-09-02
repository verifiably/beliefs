# The full workflow surface — design (the `workflow-surface` slice)

**Date:** 2026-09-01
**Status:** implemented and discharged 2026-09-02 at `b8c00d4`; conformance
cut 15 froze before implementation at `e2f9d71`, and its 17 selected + 8
labeled units passed through 30 sabotage arms after the complete cut-14
prefix. Results: `../../plans/2026-09-01-conformance-cut-15-results.md`.
**Scope:** computation §6.2's two-level seed conformance and job-set
conformance, §6.3's definition-equality query, and §6.4's adapter beyond cut
3's single-rule minimum: the workflow-definition **snapshot** as a recipe
member, semantic job keys over wildcard instances, the planning launch that
derives the job set the execution is judged against, multi-rule and
multi-target invocations. Closes R2, R16, R20 and R21 in full and reads
R23's **local basis/composition disagreement** — not its replay-cardinality
arm, which discharged at cut 3 (§9). No store
change, no `atoms` or `nodes` change, no view kind — §6.3's set is a
value-level query here, and view *records* stay with cut 14 and
`world-read`.

**Inherits:** computation
(`../../designs/2026-08-02-computation-reproducibility-design.md`)
§3.1a, §4.2, §4.2a, §4.2b, §4.2d, §6.2, §6.3, §6.4, §7.2 and §7.3 — the rule
text this document implements. It amends §6.2 in one place (§13 item 1).
Cut 3 (`../../designs/2026-08-11-conformance-cut-3.md`) §3 and §4.2 name every
arm deferred here; cut 5 (`../../designs/2026-08-19-conformance-cut-5.md`) took
R20 negative (a)'s import half, so R20's only outstanding deferrals are negatives (c) and (d).
Run confinement (`../../designs/2026-08-30-run-confinement-design.md`) §4.2,
§4.3, §5.1, §6.1 and §6.3 own the instance and the receipt this design extends. The
implementation roadmap (`../../plans/2026-08-29-implementation-roadmap.md`)
ranks this boundary first in tier 1 and heads the `execution` lane; the
adoption ledger (`../../designs/2026-08-03-redesign-adoption-ledger.md`)
carries it as `workflow-surface`.

**Sources, read at design time:** the R2, R16, R20, R21 and R23 rows of
computation §10; `python/src/beliefs/adapter.py`, `boundary.py`, `recipe.py`,
`replay.py`, `verify.py`, `runrecord.py`, `spec.py`, `confinement.py`,
`production.py`; `python/tests/test_production.py`;
`python/tests/fixtures_cut3.py`; and the engine spikes on this host
(Snakemake 8.11.4, uv-managed CPython 3.13), recorded in §2.1 as seven
numbered measurements because five design decisions rest on what they
measured.

---

## 1. Problem

Cut 3 built "the minimal adapter only". The consequence is not that the
surface is small — it is that four oracles have **no failable arm** on it,
and one record shape cannot express what conformance is defined to check.

1. **Conformance cannot see a family.** `replay.py`'s own module docstring
   says it: "Family coverage is deferred: RunClosure retains the
   workflow-definition identity, not its family-to-stream mapping, so missing
   family/job/stream claims cannot be derived from this value alone."
   `conformance()` (`replay.py:175`) therefore validates recorded seed claims
   against the global `SeedPlan` and nothing else. Neither of §6.2's two
   levels exists: not the per-job check against **its own family's**
   declaration, and not `union(realized stream keys) ==
   recipe.seed_plan.logical_streams` over the occurrence.

2. **The seed key is a family, not a job.** `_render_config`
   (`boundary.py:280`) derives one seed per `(family, stream)` and passes it
   as `config["seed_<stream>"]`. A family is a rule name, so every wildcard
   instance of one rule would draw one seed. The **semantic job key** §6.2
   makes the seed's key — the rule name plus its canonicalized wildcard
   binding — is spelled nowhere in the tree, and `derive_seed`
   (`spec.py:61`) is called with the family name in the argument named
   `semantic_job_key`.

3. **Job-set conformance has no left-hand side.** §6.2 asserts two things
   for a single run: the requested targets were satisfied, and every executed
   job belongs to the engine-derived trace for those targets. Nothing in the
   boundary asks the engine what that trace is. Cut 3 was right to defer it —
   a one-rule execution *is* its derived trace by construction — and it stays
   underivable until something plans the run.

4. **The definition/plan equality is a render-time accident.**
   `_render_config` raises `MalformedClosure` when `union(family streams) !=
   set(plan.streams)`, which is R16's "both directions" clause, but it is
   reachable only while rendering a `Seeded` config: a `Deterministic` recipe
   returns at `boundary.py:283` before the check, and no closure — minted or
   decoded — can state the predicate at all.

5. **Every fixture is one rule, no wildcards, one target.**
   `fixtures_cut3.py:228-300` holds five Snakefiles, each a single `transform`
   rule. R21's two-target arm, R20's two-decomposition comparison, R16's
   per-family and execution-coverage arms and R2's trace components have no
   fixture that could fail.

6. **A decoded record is not checkable.** `decode_run_record`
   (`runrecord.py:500`) returns `RunPublication | None` and reconstructs no
   `RunClosure`, so conformance is defined only over closures the boundary
   just minted. Whatever §6.2 asserts about a run is unavailable to anyone
   reading that run back out of a corpus.

## 2. Decision

1. The recipe's workflow member becomes the **snapshot**, not its digest, so
   conformance can read family declarations from the closure (§3.1, §3.3).
2. The **semantic job key** is canonical text over `{rule, wildcards}`, with
   one implementation serving the trace, the seed helper and the planned set
   (§3.2).
3. Seeds are derived **inside the job** by a helper shipped in the
   environment closure, never rendered per instance and never reimplemented
   by a project (§4).
4. Definition/plan agreement is **one pure predicate with two dispositions**:
   a preflight refusal before any effect, and a closure predicate conformance
   can state (§5).
5. The job set the execution is judged against is derived by a **planning
   launch** — its own instance, its own disposable directory — and stored as
   an occurrence member (§6).
6. Checkpoint-expanded families are **declared** in the definition snapshot,
   because the engine's records carry no dependency edges (§6.3).
7. Requested targets are **resolved to target job keys** at planning time;
   conformance checks those keys against the executed trace, never the
   manifest (§6.4).
8. Record shapes that gain members **step their domain version**, and the run
   domain dispatches on the recipe and receipt shapes together (§3.5).

### 2.1 What the spikes measured

Five of those decisions rest on engine behaviour rather than argument. The
spikes ran on this host against Snakemake 8.11.4 through the boundary's own
`--log-handler-script` channel.

| # | question | measurement | what it decided |
|---|---|---|---|
| 1 | does `--dryrun` emit `job_info`? | yes, through the same handler; every job emitted **twice**, and dry-run `jobid`s are not comparable to the execution's | the planned set needs no new engine interface, but must be **deduplicated** and keyed by job key, never by `jobid` (§6.2) |
| 2 | can a checkpoint's expanded jobs be planned? | no: the plan for the checkpoint fixture holds `split` and `all` only; both `fit` instances appear solely in the execution trace. The record's keys are `benchmark, indent, input, is_checkpoint, is_handover, jobid, level, local, log, msg, name, output, printshellcmd, priority, reason, resources, threads, timestamp, wildcards` — `is_checkpoint` marks the checkpoint **rule**, and there are **no dependency edges** | "downstream of a checkpoint" is underivable; it is declared instead (§6.3) |
| 3 | are `jobid`s unstable across identical runs? | **no.** Two identical static runs both gave `fit{s=a}→1, b→2, c→3`; two identical checkpoint runs both gave `4` and `5` | a multi-job DAG does **not** make R2's job-ID component failable; the fixture must vary the *job set* (§8.2) |
| 4 | is a differing trace under one recipe constructible? | yes: with the fan-out width drawn per execution, six runs produced three distinct job sets — `{a}`, `{a,b}`, `{a,b,c}` — with job ids 4/5/6 appearing and vanishing under one recipe | R2's arm exists, and is a fan-out fixture (§8.2) |
| 5 | how does `--config` type a structured value? | `seed_roots={"model-initialization": 11}` arrives as a **dict with string values** (`{'model-initialization': '11'}`); a bare `plain_int=11` arrives as an `int` | the mapping survives, the value types do not: the helper parses integers explicitly, and a test pins the coercion (§4.2) |
| 6 | dry-run side effects, and an unknown target | the engine wrote nothing into the working directory, not even `.snakemake`; an unknown target exits 1 with zero planned jobs | isolation is still **structural**, not observed (§6.1); an unresolvable target is a refusal (§6.6) |
| 7 | how does a target appear in the plan? | a rule target is a planned job with empty wildcards and no outputs (`all {} output=[]`); a file target is the planned job whose outputs contain it (`fit {s: a} output=['outputs/a.done']`) | targets resolve to **target job keys** at planning time, against the plan rather than the manifest (§6.4) |

## 3. Records and identity

### 3.1 The workflow-definition snapshot (`science.workflow-definition.v2`)

```
WorkflowDefinitionSnapshot:
    snakefile_digest: str
    family_streams: Mapping[str, tuple[str, ...]]
    checkpoint_expanded_families: tuple[str, ...]
```

The third member is new, and it is what makes §6.3 decidable. Adding it
changes the projection shape, so new definitions mint under
`science.workflow-definition.v2`; **v1 remains the historical two-member
shape** and is never written again. A definition that declares a
checkpoint-expanded family therefore has a different identity from one that
does not, which is the point: the declaration binds through the recipe, and
cannot be edited after the fact to excuse a job that ran.

For this adapter — and this is stated, not implied — **a family is exactly
`TraceJob.rule`**. Snakemake's rule name is the family name in the
declaration, in the trace, in the plan and in the job key.

`WorkflowDefinition` (`adapter.py:65`) keeps its `snakefile: bytes` and gains
the third member; it is the boundary's input value, and `snapshot()` projects
it to the record above, digesting the Snakefile once.

### 3.2 The semantic job key

The job key is **canonical text**, produced by the RFC 8785 encoder already
behind `identity/v1`, over:

```
{"rule": "<family>", "wildcards": {"<name>": "<value>", ...}}
```

One implementation, in `recipe.py` **beside `TraceJob`**, is called by
`TraceJob.job_key()`, by the planned set's reader, and by the seed helper.
It does not live in `adapter.py`: the adapter already imports `TraceJob`
from `recipe.py`, and putting the shared spelling there would create a
back-edge between the two modules. "Rule plus sorted
wildcards" is not a spelling — a wildcard value containing `=`, `|` or a
newline would make a hand-rolled join ambiguous, and the encoder already
answers escaping, ordering and unicode for every other identity in the
system.

`derive_seed(stream_root, semantic_job_key, stream_key)` (`spec.py:61`) is
unchanged in signature and rule identity; what changes is that it is finally
called with a job key. `seed-derivation/v1` keeps its name because the
function is the same function — the argument was wrong at the call site, not
in the rule.

### 3.3 The recipe (`science.recipe.v2`)

`Recipe.workflow_definition` carries the snapshot; the projection emits its
members rather than only its digest. This is the change that makes a decoded
closure checkable, and it is why the recipe steps to v2. The wire shape of
every other recipe member stays fixed: `invocation`, inputs, parameters, the
nondeterminism contract, the policy and the rule bindings keep their shapes.
The environment member remains its identity string; §3.6 defines the
read-side value used to reconstruct that deliberately identity-only member.

### 3.4 The receipt: two composed launch attestations (v3, v4)

A run now launches the engine twice — once to plan, once to execute — and the
receipt must carry complete evidence for both, not an argv bolted onto the
side of one. The receipt composes two attestations of one type:

```
LaunchAttestation:
    scratch_mapping: str
    argv: tuple[str, ...]
    rendered_config: tuple[tuple[str, str], ...]
    capabilities: tuple[str, ...]
    instance: InstanceAttestation | None
    rendered_environment: tuple[tuple[str, str, str], ...] | None
    mounts: tuple[tuple[str, str], ...] | None

BoundaryReceipt:
    planning: LaunchAttestation
    execution: LaunchAttestation
```

Each attestation keeps the existing 0-or-3 rule over `instance`,
`rendered_environment` and `mounts` (`recipe.py:534`), so "confined" stays a
property of a launch. A receipt whose two launches disagree about confinement
is malformed. The two launches share one captured bundle, one environment
snapshot and one staged held-input content set — they differ in their
directory and their argv, and in nothing else.

`qualifies()` (`replay.py:203`) reads **`execution`** and only `execution`.
The planning launch attests how the plan was obtained; it says nothing about
whether the run reached `clean-environment`, and cut 13's §7.3a containment
check is unchanged in meaning.

Receipts step to `science.boundary-receipt.v3` (minimal) and `.v4`
(confined). The v1 and v2 shapes stay readable and are never written again.

### 3.5 The run-domain matrix

`run_domain_for(confined)` (`recipe.py:630`) dispatches on receipt shape
alone. It becomes a dispatch on both shapes:

| recipe | receipt | run domain |
|---|---|---|
| v1, identity only | boundary receipt v1 | `science.run.v1` |
| v1, identity only | confined receipt v2 | `science.run.v2` |
| v2, snapshot | planning receipt v3 | `science.run.v3` |
| v2, snapshot | confined planning receipt v4 | `science.run.v4` |

**Every cross-pair is malformed** — a v2 recipe with a v1 receipt, a v1
recipe with a v4 receipt, and the other two combinations — a v1 recipe with
a v3 receipt, and a v2 recipe with a v2 receipt — are refused as
malformed records rather than digested under some nearest domain. Recipe
shape is detected by which key the projection carries (`workflow_definition`
against `workflow_definition_identity`), receipt shape by its own members;
neither is inferred from the other. Records minted before this cut decode
untranslated and recompute their v1 or v2 addresses, which is cut 13's
promise and this cut keeps it.

### 3.6 The typed decode seam

`decode_run_closure(node) -> RunClosure` joins `decode_run_record`,
reconstructing `Recipe`, `Occurrence` and `ResultManifest` from a validated
projection. It is feasible because the recipe's rule bindings are identity
strings rather than callables; it refuses any projection whose recipe and
receipt shapes fall outside the matrix above.

The environment projection is likewise an identity string, but unlike a rule
binding it normally corresponds to an in-memory `EnvironmentManifest` whose
artifact rows are not stored in the recipe. Typed decode therefore uses an
explicit read-side value, `EnvironmentReference(identity)`. `Recipe.environment`
accepts `EnvironmentManifest | EnvironmentReference`, both exposing
`identity()`, so reprojection and the run address are preserved without
inventing artifact rows. An execution boundary still requires the full
`EnvironmentManifest` and refuses an `EnvironmentReference` before launching
the engine. The reference is evidence sufficient to inspect a decoded closure,
not an executable environment. This changes no record member and steps no
domain version.

**`decode_run_closure` requires a v2 recipe.** A v1 record carries an
identity where the snapshot's members belong, so it can neither instantiate
the `Recipe` this design defines nor satisfy a family-level conformance
check — and inventing an empty `family_streams` for it would manufacture a
declaration nobody made. A v1 record therefore stays readable through
`decode_run_record`, which is unchanged and keeps returning
`RunPublication | None`, and `decode_run_closure` refuses it as
`RecipeVersionUnsupported`. This is a stated limit of what conformance can
be asked about a record, not a defect of the record: runs minted before this
cut were checked by the conformance their own cut defined.

Conformance is then defined over a `RunClosure` from either source, and the
cut tests both: `conformance(minted) == conformance(decode_run_closure(node))`
for the same run.

## 4. Seeds

### 4.1 Where the helper lives

The derivation ships as `beliefs.seeds`, a module of the `beliefs`
distribution — **not** a file injected into the captured bundle. Run
confinement §4.2 captures this checkout's editable `science` through its
`.pth` line into the environment closure, so the helper is present in the
confined instance and pinned by `environment_identity`. Injecting it into the
bundle instead would put boundary-owned bytes inside `code_identity`, which
R2 and `independent-implementation` both read as *the project's* code.

The Snakefile binds it once, at load, where `config` is in scope:

```python
from beliefs.seeds import bind
seed = bind(config)

rule fit:
    output: "outputs/{sample}.txt"
    run:
        s = seed(rule, wildcards, "model-initialization")
```

An imported module cannot see the Snakefile's injected `config` global, so
binding is what makes the three-argument call site possible. `bind` refuses a
config carrying no seed plan, which is how a `Deterministic` recipe fails
early rather than inventing a root.

### 4.2 The rendered config

`_render_config` renders **one mapping**:

```
seed_roots            = {"<stream>": "<decimal>"}      (JSON object)
seed_derivation_rule  = "seed-derivation/v1"
```

never `seed_root_<stream>`, under which the streams `a-b` and `a_b` collide
into one key. Spike 5 measured what the engine hands back: the mapping
survives as a `dict`, its values arrive as **strings** (`'11'`), and a bare
scalar arrives as an `int`. The helper therefore parses integers explicitly
and refuses a non-integral root, and a test pins the coercion itself so that
an engine upgrade which changes it fails loudly here rather than quietly
somewhere else.

Per-instance seed values are never rendered. There is nothing to render for a
fan-out whose instances do not exist yet, which is §6.2's reason for having a
derivation rule at all.

### 4.3 The claim files

The helper derives the seed, and also **writes the claim**, so the job key in
the claim and the job key in the check are produced by one call:

- one file per `(job key, stream key)`, never per job;
- named by the digest of its own canonical content, so no job key is ever a
  filename and no wildcard value reaches the filesystem;
- created `O_EXCL`, so a repeated claim for one `(job, stream)` fails inside
  the job rather than silently overwriting;
- carrying the full canonical tuple — rule, wildcards, job key, stream, seed
  — so `read_realized_seeds` validates the name against the content and never
  reconstructs a key from a path.

This replaces `fixtures_cut3.py`'s convention of a job writing
`.seeds/transform.json` by hand, which held one slot per job and could not
express two streams in one job — the "one key per job was one dimension
short" failure §6.2 describes, in the fixture rather than in the record.

### 4.4 What conformance checks

Unchanged in doctrine: conformance is a precondition on scope derivation, it
never rewrites the recipe, and a non-conforming execution derives
`not-certified`.

## 5. Definition/plan agreement — one predicate, two dispositions

R16's oracle says the boundary **refuses** a definition whose family streams
and the recipe's logical streams disagree, in both directions. That refusal
is kept: it is decidable before execution, and executing a recipe already
known to disagree with its definition would violate the repository's
fail-early rule for no gain.

What is added is that the same fact is **statable about a closure**. One pure
predicate:

```
definition_agrees_with_plan(snapshot, plan: SeedPlan | None) -> str | None
```

The plan is optional because two of the three contract variants carry none,
and §1 item 4's defect is exactly that the current check is unreachable for
them. The expected stream set is **empty** for `Deterministic` and
`StochasticUnseeded`, so a definition declaring family streams under either
contract **disagrees** — a family that claims a stream its recipe does not
plan is the same error whichever variant the recipe carries.

is called at two sites:

- **before the planning launch**, where a non-`None` result is a refusal,
  before any workflow effect;
- **inside `conformance()`**, where a non-`None` result is non-conformance,
  for a closure that was constructed or decoded rather than just minted.

The second site is not a second policy. A minted run can never reach it — the
first site refused. It exists because a decoded record, or a record raw-written
into a corpus, can carry a disagreement no boundary ever saw, and conformance
must be able to say so. This is a widening of R16's reading, recorded as such
in §13.

## 6. Planning and job-set conformance

### 6.1 The planning launch

Before the execution launch, the boundary invokes the engine `--dryrun` over
the same Snakefile, the same rendered config and the same staged inputs, in a
**disposable planning directory** — staged identically, read once, discarded.
The execution scratch is never the planning directory.

Spike 6 measured that the engine wrote nothing into the working directory,
not even `.snakemake`. That is one workflow, not a guarantee: a Snakefile's
top-level Python executes at parse time under `--dryrun` exactly as it does
under execution, and may write. Isolation here is therefore **structural** —
a separate directory — rather than a property observed of the engine.

Under `confined-v1` the planning launch is **its own confined instance** of
the same verified snapshot. Each instance still executes exactly one
snakemake argv, so cut 13's derivation of `from-bundle` from the observed
inner argv is untouched, and each launch's attestation is produced by the
existing probe. The rejected alternative is a trusted runner wrapping both
invocations inside one instance (§14 item 1).

### 6.2 The planned job set

The planning launch's `job_info` records are read through the same channel as
the trace and **grouped by semantic job key** — spike 1 measured each job
emitted twice. Repeated observations of one key must **agree on every other
field**; a disagreement, `is_checkpoint` included, is a **planning refusal**
(`PlanUnavailable`), never a silent pick of the first or last record.
Grouping on `(job key, outputs)` would have been wrong twice over: it admits
two planned records for one semantic job, and it ignores disagreement in the
very field §6.3 reads. One key yields exactly one `PlannedJob`:

```
PlannedJob:
    job_key: str
    family: str
    outputs: tuple[str, ...]
    is_checkpoint: bool
```

`jobid` is deliberately absent: spike 1 measured that dry-run numbering is
not comparable to the execution's, and §6.2's identity for a job is the
semantic key.

### 6.3 Checkpoint-expanded families

Spike 2 measured that the engine's records carry `is_checkpoint` and **no
dependency edges**, so "an instance of a family downstream of a checkpoint"
cannot be derived from the plan. It is declared, in the snapshot, inside the
definition identity.

The declaration is cross-checked at planning time, so it cannot be an
unfalsifiable escape hatch:

- a non-empty `checkpoint_expanded_families` whose plan contains no
  `is_checkpoint` job is **refused**;
- a declared family the definition does not contain as a rule is **refused**;
- an empty declaration against a plan containing a checkpoint job is
  permitted — a checkpoint whose downstream is fully planned is an ordinary
  definition.

Strengthening this later with input-containment evidence — a job whose inputs
lie under a checkpoint's declared output directory — is possible and is **not
in this cut**; it is named in §11.3 as banked.

### 6.4 Target resolution

Each requested target resolves, at planning time, to exactly one **target job
key**:

- a *rule* target matches a planned job whose family is that name and whose
  wildcards are empty — spike 1 measured `all {} output=[]` as a planned job;
- a *file* target matches a planned job whose outputs contain it — spike 7
  measured `fit {s: a} output=['outputs/a.done']`.

**Exactly one match is required.** Zero matches is `TargetUnresolvable`;
two or more is `TargetAmbiguous`. Neither is a diagnostic, and neither is
non-conformance: both are refusals, before execution.

The two refusals are **ordered and disjoint by construction**, which is what
separates them from `PlanUnavailable`: resolution runs only against a plan
that was successfully obtained. A planning launch that exits non-zero or
emits no job is `PlanUnavailable` and never reaches resolution; a plan in
hand that does not name a requested target is `TargetUnresolvable`. Spike 6
measured that the engine refuses to plan at all for an unknown target — exit
1, zero jobs — so **that case surfaces as `PlanUnavailable`**, and cut 15's
arm asserts exactly that rather than the name it superficially resembles.
`TargetUnresolvable` covers a successful plan that does not name the target,
which the disposable planning directory makes reachable because no output
pre-exists there.

Conformance then checks the resolved **target job keys against the executed
trace**. It does not check that targets appear in the result manifest: a rule
target names no file, and §4.2d's manifest is built from declared outputs,
which is a different claim about a different record.

### 6.5 Conformance, in full

For a completed closure, in order:

1. **Definition/plan agreement** (§5).
2. **Per job** — each executed job's realized streams equal its own family's
   declared set; a wildcard instance inherits its family's declaration.
3. **Over the occurrence** — `union(realized stream keys) ==
   plan.logical_streams`, so a declared stream no executed job realized is
   non-conforming however well each job matched.
4. **Trace membership** — every executed job's key is in the planned set, or
   its family is a declared checkpoint-expanded family.
5. **Target satisfaction** — every resolved target job key appears in the
   executed trace.

Every failure derives `not-certified`. No equivalence rule reads any of it:
the evaluator's signature is `(result, result)` and this cut does not widen
it.

### 6.6 The failure taxonomy

Three states, and the boundary between them is what R21 negative (e) pins:

- **Planning failure** — an unparseable definition, a definition/plan
  disagreement, an unresolvable or ambiguous target, a declaration
  contradicting the plan, or an engine failure while planning: a **refusal**,
  after contained disposable-planning effects and **before any
  execution-instance effect**. No run is minted.
- **Execution failure** — the engine fails, an output is missing, a manifest
  entry is undeclared or disagrees with its bytes: a **refusal**, after
  attempted execution effects. No run is minted.
- **A completed execution contradicting its recorded plan** — a job outside
  the plan, an unsatisfied target, a seed claim violating the plan:
  **non-conformance**. A run is minted, and it derives `not-certified`.

## 7. Multi-rule, multi-target, and the manifest

`Invocation` already carries `targets` and `declared_outputs`, and
`build_manifest` (`boundary.py:146`) already content-addresses declared
outputs and excludes everything else beneath the output root. The extension
is the fixture and the arms, not new machinery: a definition with two targets
executed twice yields two runs with **different recipe identities** despite
sharing bundle, environment, snapshot, inputs, parameters and contract; a
manifest is constructed across the outputs of several rules; intermediates
beneath the output root stay excluded, so a replay leaving different scratch
files produces an equal manifest.

## 8. Definition equality and job-set diagnostics

### 8.1 Definition equality

§6.3's "which runs executed the same pipeline" ships as a value-level query
over runs sharing a `workflow_definition` identity. No view record, no
`workflow` kind, no entity: view *records* are cut 14's and the query
evaluator is `world-read`'s, and the `execution` lane takes no dependency on
either. R20 negative (d)'s two-decomposition comparison is read against this
query: two decompositions of one computation — one rule versus two — produce
**different definition identities**, and no spec can spell either, because a
frozen spec names logical streams only.

### 8.2 Job-set diagnostics

`_job_diagnostics` already exists at `verify.py:321` and already reports a
differing job set as a comparison-report diagnostic contributing to no
verdict and no scope. It keeps its home; its `(job.rule, job.wildcards)`
spelling becomes `job_key()`, so the diagnostic and the conformance check
name jobs identically.

R2's job-ID component needs a fixture, and spike 3 measured that the obvious
one does not work: job ids are **stable** across identical runs, statically
and under checkpoints alike, so a multi-job DAG produces no difference. What
does is a **varying job set**: spike 4's fan-out produced three distinct job
sets in six runs under one recipe, with job ids appearing and vanishing. The
cut's fixture makes that deterministic by keying the fan-out width on the
**scratch base directory name**, which the test chooses — a receipt member,
not a recipe member, which is exactly what R21 negative (c) pins — and the
width function itself is pinned by a unit test so the fixture's determinism
is not folklore.

That fixture runs under **`minimal-v1`**, and the design says so explicitly:
a confined workflow's working directory is `/science/out`
(`confinement.py:77`), constant across instances by construction, so the same
fixture under `confined-v1` would produce one job set and contradict R21(c)
rather than exercise R2.

## 9. R23: replay cardinality is discharged, the local disagreement is not

An earlier revision of this design selected R23's "second dataset-production
run" as a cut-15 unit, reading the roadmap's words as the replay-cardinality
arm. **That arm is discharged**; a different R23 clause belongs here, and
§9.1 separates them.

Cut 3 selected it by name — "**replay cardinality**: one address, two
`produces` edges from two runs, no existing node mutated and the prior
lineage basis unchanged" (`../../designs/2026-08-11-conformance-cut-3.md`
§4.2, "Selected in part — the arm split, stated exactly"). The test exists and executes two production runs rather than
constructing them:
`test_production.py::test_r23_replay_cardinality_one_address_two_edges_nothing_mutated`
runs `run_production` twice, asserts equal recipe identities, one address,
distinct edges, an unchanged prior basis and an unmutated basis map. N2
declares it with a sabotage in `production.py` (`n2_arms_cut3.py`, the R23
arm "a replay adds an edge while preserving the first stamped basis
unchanged"). Cut 5 files it under "**Prior, not selected again**"
(`../../designs/2026-08-19-conformance-cut-5.md` §3.2).

What cut 5 actually deferred is a different clause — the **local
basis/composition disagreement** — and the roadmap compressed it into "the
second dataset-production run → `workflow-surface`", which reads as the
discharged arm and is not it.

### 9.1 What the clause actually is, and who owns it

Cut 4 selected the `derived_from` view "**not read by independence**, which
walks the **stamped basis**: with a basis and a composition made to
disagree, **by the §3 item 2 fixture write** rather than by any deletion,
independence follows the basis"
(`../../designs/2026-08-17-conformance-cut-4.md` §3, R23). The §3 item 2
fixture write is the raw filesystem write, and cut 5's review removed it:
"the frozen local basis/composition disagreement is triggered by a second
dataset-production run… **Disposition:** remove the invented import mutation
and defer R23" (`../../designs/2026-08-19-conformance-cut-5.md` §6.1 item 2).
Cut 5 §3.2 then states the deferral in full — the source mutation "is a
second dataset-production run, **not explicit import**; it waits on that
**operation-family boundary** rather than being respelled as import
behavior."

A second dataset-production run produces the disagreement **honestly and by
construction**: the second run adds a `produces` edge while `mint_dataset`
leaves the first stamped basis untouched, so the composition
(`produces ∘ transforms`, which the view composes over both producers) and
the basis (which still names the first run alone) diverge with no fixture
write anywhere. That is why cut 5 refused to respell it as import behavior,
and an earlier revision of this section made exactly that mistake, assigning
the clause to `run-boundary-remainder` as an explicit-import validation.
**R23's actual explicit-import clauses are different work** — producer
snapshots, receipts, world corpus states and rule resolution — and they wait
on the world index and the rules store, which is to say `world-resolution`
and `contract-cut`.

Cut 5 names the operation families: "their respective **run**, acquisition,
audit, and other operation-family cuts" (§3.2 there). The mutation here is a
dataset-production **run**, so the owner is the **run**-family boundary —
`workflow-surface`, this one. The roadmap's assignment of an R23 arm to this
boundary is therefore right in its destination and wrong in its words: what
belongs here is the local basis/composition disagreement, never the
discharged replay cardinality.

### 9.2 Cut 15 selects it

The clause is executable on this surface with no new machinery: two
dataset-production runs minted through the add path into one durable corpus
root, `derived_from` walked back out as a view, and independence asserted to
follow the **stamped basis** rather than the composition — failable in both
directions, as cut 4's selected half is. Cut 15 therefore selects **one R23
unit**, distinct from replay cardinality, and R23 stays `part` on the
producer-snapshot, receipt, coverage, divergence, move, consolidate,
deletion and rules-store clauses that other boundaries carry.

The replay-cardinality assertions still run over the new surface as
**ordinary regression coverage** — the multi-rule production fixture
executes twice and cut 3's assertions hold — declaring no N2 arm and
changing no row's accounting.

## 10. Refusals

New names in `errors.py`, all `RecordError` subclasses on the existing
pattern:

| name | raised when |
|---|---|
| `PlanUnavailable` | the planning launch exits non-zero, emits no job, or emits two records for one job key that disagree in any other field |
| `TargetUnresolvable` | a **successfully obtained** plan names no job matching a requested target |
| `TargetAmbiguous` | a requested target matches more than one planned job |
| `CheckpointDeclarationUnmet` | a declared expanded family is not a rule of the definition, or the declaration is non-empty and the plan contains no checkpoint job |
| `DefinitionPlanMismatch` | family streams and the recipe's expected stream set disagree, in either direction, under any contract variant |
| `SeedClaimMalformed` | a claim file's name disagrees with its content, or a `(job, stream)` claim repeats |
| `RecipeVersionUnsupported` | `decode_run_closure` is given a v1, identity-only recipe (§3.6) |

`errors.py` is a lane-shared file under the roadmap's concurrency rule 3;
§12 names it.

## 11. Conformance cut 15

Cut 15 is frozen here, before its code exists, and claims the number at
freeze: cut 14 (`2026-08-31-coordination-and-view-kinds-design.md`) froze
first in the `mutation` lane, and cut 15 **discharges after it** (§11.2).
The two lanes' code merges independently; their discharges do not.

### 11.1 Selection

| row | arms in cut 15 | banked |
|---|---|---|
| **R2** | two executions of one recipe with **differing job sets, job ids and realized seeds** have equal recipe identities; mutating `family_streams`, and separately `checkpoint_expanded_families`, moves the definition identity, the recipe identity and the run address | **closes** |
| **R16** | a job realizing a stream its family does not declare; a job omitting one it declares; the two-stream nesting under `[job_key][stream_key]` and the omission of one; the honest per-family record conforming while an over-claiming record does not; a wildcard instance judged against its family; the declarations read from the snapshot and the both-directions equality refused; the same rule over a `dataset-production` recipe with no spec; execution coverage — a declared stream whose family produces zero jobs is non-conforming though every per-job check passed vacuously; trace membership and target satisfaction; the data-dependent negative — a replay running a different job set over different held inputs is conforming, its difference a diagnostic contributing to no verdict and no scope | **closes** |
| **R20** | negative (c): different families realizing different streams conforms, and no global per-job obligation is spellable; negative (d): two decompositions of one computation yield different definition identities | **closes** |
| **R21** | the two-target arm — `analysis` and `report` over one definition yield different recipe identities, with the manifest constructed across rules and intermediates excluded; negative (d): `invocation` does not enumerate the jobs a target implies, and job-set conformance asserts only target satisfaction and trace membership | **closes** |
| **R23** | the **local basis/composition disagreement**: two dataset-production runs minted through the add path into one durable corpus root make the composition and the stamped basis disagree with no fixture write; independence follows the **basis**, `derived_from` composes over both producers and is stored nowhere — failable in both directions | remains **part** — the producer-snapshot, receipt, coverage, divergence, move, consolidate, deletion and rules-store clauses are `world-resolution`'s, `consolidate-family`'s and `contract-cut`'s |

R23's **replay-cardinality** arm is not selected and is not re-run as a unit:
it discharged at cut 3 (§9). The unit above is the clause cut 5 deferred to
the run-family boundary, and the two must not be confused in the accounting.

**Selected units, by row: R2 = 2, R16 = 10, R20 = 2, R21 = 2, R23 = 1 — 17
in all.** This is the same total an earlier revision claimed, reached by a
different route: that revision's R23 unit was the discharged replay
cardinality, and this one's is the local disagreement.

| row | units |
|---|---|
| R2 | the equal-recipe/differing-trace negative; the two new snapshot members moving the address |
| R16 | (1) undeclared stream; (2) omitted stream; (3) the two-stream nesting with the omission of one of two; (4) the honest per-family record against the over-claiming one; (5) the wildcard instance judged against its family; (6) the snapshot-sourced both-directions equality; (7) the `dataset-production` recipe with no spec; (8) execution coverage over a zero-job family; (9) trace membership with target satisfaction; (10) the data-dependent negative |
| R20 | negative (c); negative (d) |
| R21 | the two-target arm; negative (d) |
| R23 | the local basis/composition disagreement over a durable corpus root |

Eight further units are **labeled** — machinery this
cut builds that no guarantee row names: the four-row run-domain matrix and
the malformedness of every cross-pair; an old v1-recipe record decoding
untranslated with its address recomputed; `decode_run_closure` round-tripping
a minted closure with equal conformance; the canonical job key shared by
trace, plan and helper; two streams in one job writing two claim files, and
an `O_EXCL` collision on a repeated claim; the engine's config coercion;
the planning launch writing nothing into the execution scratch; and the
receipt's two launch attestations, with `qualifies()` reading `execution`
only and a receipt carrying planning evidence without execution evidence
refused as malformed. **17 selected + 8 labeled = 25 units.**

### 11.2 Where the arms live

**Portable suite:** the record shapes and the domain matrix; the job key over
constructed values; `definition_agrees_with_plan` as a pure predicate;
`conformance()` over constructed and decoded closures, which is where most of
R16 and R20 lives; the definition-equality query; `_job_diagnostics`; and
`decode_run_closure`'s refusals. These need no engine.

**Real-engine suite,** under `minimal-v1`, on cut 3's pattern in
`test_boundary.py`: the multi-rule and wildcard executions, the planning
launch and its plan, the two-target arm, the checkpoint fixtures, and R2's
fan-out fixture. Cut 3's replay-cardinality assertions run here too, as
regression coverage over the new surface rather than as a selected unit
(§9.2); R23's selected arm is durable and lives in the acceptance tier.

**Acceptance tier** (`tests/acceptance/`), behind the confinement gate that
errors and never skips: the planning launch as its own confined instance, the
two-launch receipt under `confined-v1`, and `qualifies()` reading `execution`
across a confined pair. R23's local-disagreement arm also lives here, on cut
4's pattern rather than the gate's: it mints two production runs through the
add path into a **durable corpus root** on the certified volume and walks
`derived_from` back out after reload, so `tools/cut15_acceptance.py` probes
the durable root as well as the confinement gate — both prerequisites, as cut
13's runner already probes them for its prefix.

**N2:** `n2_arms_cut15.py` declares every selected and labeled arm with its
sabotage in `boundary.py`, `adapter.py`, `recipe.py`, `replay.py`,
`verify.py` or `runrecord.py`; `test_n2_cut15.py` and
`tools/cut15_acceptance.py` follow cut 13's pattern, with
`PREFIX_RUNNERS = ("cut14_acceptance.py",)` — and **cut 15's discharge is
serialized after cut 14's**, a discharge prerequisite on the pattern of cut
13's ext4 recertification, not an implementation dependency of anything in
this slice.

An earlier revision proposed chaining by **discharge order** instead — the
newest discharged cut, whichever lane it came from. That rule loses a cut.
If cut 15 discharged first it would chain cut 13; cut 14 would then discharge
with its own frozen inventory ending at cut 13's phase modules; and no chain
would contain both, so any later runner naming only the newest discharge
necessarily omits one. It also contradicts cut 14's frozen text, which says
**"Cuts after 14 name `cut14_acceptance.py` and inherit the bypass"**.

Serializing is additionally **forced** rather than merely tidy. Cut 14 turns
on the ordinary path's `note` refusal, which makes cut 5's ineligible-kind
arm fail on the post-cut-14 tree by design — which is why cut 14 names no
aggregate runner and freezes a current-tree module inventory instead. A cut
15 that discharged on `cut13_acceptance.py` would chain
`cut12 → cut11 → cut10 → cut9 → cut7 → cut5` and break the moment cut 14's
code landed. Naming `cut14_acceptance.py` inherits the bypass, exactly as
cut 14 froze.

The `execution` lane's **code** still merges independently of the `mutation`
lane; only the discharge serializes.

### 11.3 Limitations, banked as unrun by design

- **Input-containment evidence for checkpoint ancestry** (§6.3): a job whose
  inputs lie under a checkpoint's declared output directory could be admitted
  on engine-derived evidence rather than declaration. Not built; the
  declaration is what this cut claims.
- **A second engine adapter.** §6.4's ruling stands: one adapter, no plugin
  framework, a second when a second engine exists in a project.
- **Job-set equality between two runs contributes to no verdict**, by §6.2's
  rule. The diagnostic is tested; an occurrence-aware pairwise rule is not
  designed and is not owed here.
- **`shell:` rules under `confined-v1`** remain unrun, inherited from cut 13:
  no shell is in the closure.
- **The planning launch's own trace is not a run.** It mints nothing, and no
  arm asserts a property of the plan beyond what conformance reads.

## 12. What changes elsewhere

- **`errors.py`**, `python/tests/test_designs_corpus.py`, the adoption
  ledger, the roadmap and the guide index are rewritten by every lane; this
  design names them under concurrency rule 3.
- **`adapter.py`** is listed in the shared surface of both the `execution`
  and the `mutation` lanes in the roadmap's lane table. This cut rewrites it.
  The mutation families in fact live in `corpus.py`
  (`CorpusWriter.retract/supersede/revise/import_bundle`), so the real
  overlap may be nil, but rule 3 asks for the name rather than the analysis:
  the later merge resolves toward the earlier.
- **Files this cut rewrites**, beyond the lane's declared surface:
  `replay.py`, `runrecord.py`, `spec.py` (documentation of
  `semantic_job_key` at its call site), and a new `seeds.py`.
- **The roadmap** gains concurrency rule 5 in the banking change, since cut
  15 is the first cut frozen against an undischarged concurrent cut: *a cut
  names the acceptance runner of the highest-numbered cut, and a cut frozen
  while a lower-numbered cut is undischarged serializes its discharge after
  that cut's.* Discharge order and cut number then agree, and no chain can
  omit a cut (§11.2).
- **The ledger and the roadmap carry a stale R23 assignment.** Both give
  `workflow-surface` "R23's second-production arm"
  (ledger `Current state`; roadmap boundary index, tier-1 table, and
  Appendix B's R23 row), and that arm discharged at cut 3 (§9). The
  correction lands in the banking change, and it is a **rewording, not a
  reassignment**: the destination stays `workflow-surface`, and the words
  become the clause cut 5 deferred — *R23's local basis/composition
  disagreement (cut 5 §3.2)* — in the ledger's boundary row, the roadmap's
  boundary index, its tier-1 table and its Appendix B R23 row. No open clause
  is dropped, nothing moves to another lane, and the correction must not
  restate the discharged replay-cardinality arm as open anywhere, including
  Appendix A's row accounting.
- **The ledger's `Current state`** drops the `workflow-surface` row at
  discharge and gains a summary bullet; the roadmap is re-ranked by the
  commit that adds cut 15's results record, one lane at a time under
  concurrency rule 2.
- **The guide** describes the boundary as rendering single invocations; that
  claim goes stale the moment this lands and is corrected in the same change.

## 13. Amendments to the banked designs

1. **Computation §6.2's "no prior enumeration exists" ruling is narrowed.**
   It reads: "a target names an outcome and the engine decides which jobs
   reach it… Comparing an executed job set against a 'requested' one that was
   never enumerable is a check with no left-hand side." That stays true of
   **checkpoint-expanded** jobs, and is now false of every other job: the
   planning launch enumerates them, and job-set conformance reads that
   enumeration. The amendment states the narrowed form — no prior enumeration
   of checkpoint-expanded jobs exists, and those are admitted by declaration —
   and leaves the surrounding rule, that job-set differences between two runs
   contribute to no verdict, untouched.
2. **R16's definition/plan check gains a second disposition.** The oracle's
   "refused" is preserved as the primary disposition at the boundary; the
   same predicate is additionally statable about a constructed or decoded
   closure, where it is non-conformance. Recorded as a widening, not a
   substitution (§5).
3. **Record shapes and the decode matrix**: `science.workflow-definition.v2`,
   `science.recipe.v2`, `science.boundary-receipt.v3`/`.v4`, and
   `science.run.v3`/`.v4`, with the four-row dispatch of §3.5 and every
   cross-pair malformed. v1 and v2 records decode untranslated.
4. **Run confinement's receipt** becomes two composed launch attestations
   (§3.4); `qualifies()` reads `execution`. Cut 13's §6.3 receipt contents are
   preserved per launch, and its `from-bundle` derivation from the observed
   inner argv is unchanged because each instance still executes one argv.
5. **No amendment to R23, and a correction to its accounting.** Cut 3's
   replay-cardinality selection stands as discharged; nothing here reopens,
   respells or re-runs it as a cut-15 unit. Cut 5's deferral of the local
   basis/composition disagreement to the run-family boundary is honoured as
   written — the source mutation is a second dataset-production run, and it
   is **not** respelled as import behavior. What changes is the wording of
   the ledger's and the roadmap's R23 assignment to this boundary (§9, §12),
   a current-facing accounting error rather than an amendment to any banked
   design.
6. **No amendment to cut 14.** Serializing cut 15's discharge behind cut 14
   satisfies cut 14's frozen "cuts after 14 name `cut14_acceptance.py`" as
   written; the multi-head prefix frontier that would have required a dated
   amendment to cut 14 is rejected (§14 item 7).
7. **Typed decode carries an opaque environment reference.** The stored recipe
   has always projected only `environment.identity()`, so reconstructing a full
   `EnvironmentManifest` would invent evidence. `EnvironmentReference` is the
   read-side value described in §3.6; execution remains manifest-only and all
   record shapes and identities stay unchanged.

## 14. Alternatives rejected

1. **A trusted runner wrapping both invocations in one instance.** It changes
   the argv the confined instance executes, and cut 13 derives `from-bundle`
   from exactly that observation. Two instances keep the attestation model
   intact at the cost of a second materialization of a snapshot that is
   already cached by environment identity.
2. **Injecting the seed helper into the captured bundle.** It would place
   boundary-owned bytes inside `code_identity`, which R2 and
   `independent-implementation` read as the project's own code. The
   environment closure already carries the helper (run confinement §4.2).
3. **Structural membership instead of a planning launch** — every executed
   job's rule must be a declared family and its outputs must match that
   rule's pattern. It never asks the engine what the DAG for those targets
   was, so it proves a job was *spellable* rather than *derived*, which is
   weaker than §6.2's wording.
4. **Refusing checkpoints outright.** It would make executed and planned sets
   equal with no admitted exception, and would refuse precisely the dynamic
   workflows §6.2 built the derivation rule to serve.
5. **Rendering per-instance seeds.** Impossible for a fan-out whose instances
   do not exist before execution, and §6.2's derivation rule exists so that
   nobody has to enumerate them.
6. **A `workflow` view record for definition equality.** View records are cut
   14's and the query evaluator is `world-read`'s; §6.3 says the set is a
   query, and the `execution` lane takes no cross-lane dependency for it.
7. **A multi-head prefix frontier.** Letting a cut name several prefix heads
   would allow the two lanes to discharge in either order, but it needs a
   dated amendment to cut 14's frozen inventory statement and a rule for
   reconciling two heads that disagree about a shared module. Serializing
   one discharge behind the other costs one ordering constraint and needs
   neither (§11.2).
8. **Selecting R23's replay cardinality again.** It is discharged, its test
   and N2 arm exist, and cut 5 records it as prior; re-selecting a discharged
   arm would inflate this cut's coverage claim while proving nothing new
   (§9).
9. **Respelling the local disagreement as import validation.** Cut 5
   considered and refused exactly that — "not explicit import… rather than
   being respelled as import behavior" — and R23's real explicit-import
   clauses are the producer-snapshot and receipt work waiting on the world
   index and rules store. An earlier revision of §9 made this mistake and it
   is recorded here so the reasoning is not repeated.
10. **Synthesizing an empty environment manifest during decode.** It would
    claim the recorded identity was derived from artifact rows the record does
    not contain. Adding those rows to the recipe projection would instead
    change the frozen recipe and run identities. The opaque reference preserves
    the existing evidence and execution refuses it (§3.6).

## 15. Verification

The repository gates, from `python/`: `uv run --frozen pytest`,
`uv run --frozen ruff check .`, `uv run --frozen pyright`; from `ts/`:
`npm ci`, `npm test`, `npm run typecheck`, `npm run check`. The cut is
discharged by `tools/cut15_acceptance.py` on the certified volume beside the
checkout, with the confinement gate satisfied, and its results record lands
with the ledger and roadmap re-rank in one commit under concurrency rule 2.
