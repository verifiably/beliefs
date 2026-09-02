# Workflow surface implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full workflow surface — multi-rule, wildcard, family and
multi-target workflows with two-level seed conformance and engine-derived
job-set conformance — and discharge conformance cut 15.

**Architecture:** The recipe carries the workflow-definition *snapshot* rather
than its digest, so conformance can read family declarations from a closure.
Seeds are derived inside each job by a helper shipped in the environment
closure and keyed by a canonical semantic job key. Every run launches the
engine twice — a planning launch in a disposable directory that derives the
job set, then the execution launch — and the receipt composes one attestation
per launch. Records that gain members step their domain version, and the run
domain dispatches on recipe and receipt shape together.

**Tech Stack:** Python 3.13, Snakemake 8.11.4, `uv`, pytest, ruff, pyright;
`beliefs` (this package), `atoms-core` and `nodes-core` as editable path
dependencies.

**Spec:** `../superpowers/specs/2026-09-01-workflow-surface-design.md`

## Global Constraints

- **Gates, from `python/`:** `uv run --frozen pytest`,
  `uv run --frozen ruff check .`, `uv run --frozen pyright`. From `ts/`:
  `npm ci`, `npm test`, `npm run typecheck`, `npm run check`.
- **`CapabilityUnavailable` is a fail-closed result, not a waiver.** Run the
  Python suite on the certified kernel and volume tuple or report the exact
  mismatch.
- **A family is exactly `TraceJob.rule`** for this adapter — in the
  declaration, the trace, the plan and the job key.
- **Domain versions are fixed by the spec** and must be spelled exactly:
  `science.workflow-definition.v2`, `science.recipe.v2`,
  `science.boundary-receipt.v3` (minimal) and `.v4` (confined),
  `science.run.v1`–`.v4` per §3.5's matrix. Every cross-pair is malformed.
- **`seed-derivation/v1` keeps its identity string.** The rule is unchanged;
  only its `semantic_job_key` argument was wrong at the call site.
- **No compatibility layer.** v1 records stay readable; nothing translates
  them into the new shape.
- **Never edit `tasks/*.md`.** Use the `tasks` CLI. Run `tasks check` before
  every commit and require zero errors.
- **Cut 15 discharges after cut 14** and names `cut14_acceptance.py` as its
  prefix. The lane's code may merge earlier; the discharge may not.
- **Conventional commits, no AI attribution trailer.**

## File structure

| file | responsibility | tasks |
|---|---|---|
| `python/src/beliefs/recipe.py` | `job_key()` beside `TraceJob`; the snapshot-bearing `Recipe`; read-side `EnvironmentReference`; `LaunchAttestation`; the receipt; the run-domain matrix | 1, 3, 4, 5, 6 |
| `python/src/beliefs/adapter.py` | `WorkflowDefinition` → snapshot; manifest-only execution check; the planning launch's plan reader; claim-file reading | 2, 6, 10, 12 |
| `python/src/beliefs/seeds.py` (new) | `bind`/`seed`: derivation and claim writing, imported by the workflow | 8 |
| `python/src/beliefs/boundary.py` | config rendering; the planning launch; checkpoint cross-checks; target resolution; both launches into one receipt | 9, 12, 13, 14, 16 |
| `python/src/beliefs/replay.py` | `definition_agrees_with_plan`; two-level seed conformance; job-set conformance | 7, 11, 15 |
| `python/src/beliefs/runrecord.py` | `decode_run_closure` and the decode matrix | 5, 6 |
| `python/src/beliefs/verify.py` | `_job_diagnostics` respelled to `job_key()` | 18 |
| `python/src/beliefs/errors.py` | the seven new refusals | 6, 12, 13, 14 |
| `python/tests/fixtures_cut15.py` (new) | multi-rule, wildcard, checkpoint and fan-out Snakefiles and run helpers | 17 |
| `python/tests/acceptance/n2_arms_cut15.py`, `test_n2_cut15.py`, `python/tools/cut15_acceptance.py` (new) | the cut's declared arms and its aggregate runner | 21 |

---

### Task 1: The canonical semantic job key

**Files:**
- Modify: `python/src/beliefs/recipe.py` (beside `TraceJob`, near line 460)
- Test: `python/tests/test_recipe.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `job_key(rule: str, wildcards: tuple[tuple[str, str], ...]) -> str`
  and `TraceJob.job_key() -> str`, both returning RFC 8785 canonical text.
  Tasks 8, 10, 11, 12, 15 and 18 all call one of these.

The helper lives in `recipe.py`, not `adapter.py`: the adapter already imports
`TraceJob` from `recipe.py`, so putting the shared spelling in the adapter
creates a back-edge.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_recipe.py
from beliefs.recipe import TraceJob, job_key


def test_the_job_key_is_canonical_text_over_rule_and_wildcards():
    key = job_key("fit", (("sample", "a"),))
    assert key == '{"rule":"fit","wildcards":{"sample":"a"}}'


def test_the_job_key_orders_wildcards_canonically_whatever_the_input_order():
    assert job_key("fit", (("b", "2"), ("a", "1"))) == job_key("fit", (("a", "1"), ("b", "2")))


def test_a_wildcard_value_containing_a_separator_cannot_collide():
    # a hand-rolled "rule|k=v" join would map these two to one string
    left = job_key("fit", (("a", "1|b=2"),))
    right = job_key("fit", (("a", "1"), ("b", "2")))
    assert left != right


def test_a_trace_job_reports_its_own_key():
    job = TraceJob(job_id="1", rule="fit", wildcards=(("sample", "a"),), inputs=(), outputs=())
    assert job.job_key() == job_key("fit", (("sample", "a"),))
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py -k job_key -v`
Expected: FAIL — `ImportError: cannot import name 'job_key' from 'beliefs.recipe'`.

- [ ] **Step 3: Implement it**

```python
# python/src/beliefs/recipe.py — beside TraceJob
def job_key(rule: str, wildcards: tuple[tuple[str, str], ...]) -> str:
    """The semantic job key of computation §6.2: the rule name and its
    canonicalized wildcard binding, as RFC 8785 canonical text. One
    implementation — the trace, the plan, the seed helper and conformance all
    call it, so no two of them can spell a job differently."""
    _require_str(rule, "job key rule")
    _require_pairs(wildcards, "job key wildcards")
    return v1.encode({"rule": rule, "wildcards": {name: value for name, value in wildcards}}).decode("utf-8")
```

and, on `TraceJob`:

```python
    def job_key(self) -> str:
        return job_key(self.rule, self.wildcards)
```

Add `"job_key"` to `__all__`. `v1.encode` (`identity/v1.py:157`) is the
existing RFC 8785 encoder and returns `bytes`; there is no second encoder to
add and no domain constant to mint — a job key is canonical text, not a
digest.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py -k job_key -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/recipe.py python/tests/test_recipe.py
git commit -m "feat(recipe): add the canonical semantic job key"
```

---

### Task 2: The workflow-definition snapshot, `science.workflow-definition.v2`

**Files:**
- Modify: `python/src/beliefs/recipe.py` (the snapshot value, beside `TraceJob`)
- Modify: `python/src/beliefs/adapter.py:30,64-85` (re-export, `snapshot()`)
- Modify: `python/tests/fixtures_cut3.py`
- Test: `python/tests/test_adapter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `WorkflowDefinitionSnapshot(snakefile_digest: str,
  family_streams: Mapping[str, tuple[str, ...]], checkpoint_expanded_families:
  tuple[str, ...])` with `.identity() -> str` and `.projection() -> dict`;
  `WorkflowDefinition.snapshot() -> WorkflowDefinitionSnapshot`.
  `WORKFLOW_DEFINITION_DOMAIN` becomes `"science.workflow-definition.v2"`.
  Tasks 3, 7, 12 and 13 consume the snapshot.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_adapter.py
import pytest

from beliefs.adapter import WORKFLOW_DEFINITION_DOMAIN, WorkflowDefinition
from beliefs.errors import MalformedClosure


def _definition(**overrides):
    fields = {
        "snakefile": b"rule fit:\n    output: 'out.txt'\n",
        "family_streams": {"fit": ("model-initialization",)},
        "checkpoint_expanded_families": (),
    }
    return WorkflowDefinition(**{**fields, **overrides})


def test_the_domain_is_v2_because_the_projection_gained_a_member():
    assert WORKFLOW_DEFINITION_DOMAIN == "science.workflow-definition.v2"


def test_the_snapshot_carries_the_declaration_not_the_bytes():
    snapshot = _definition().snapshot()
    assert snapshot.family_streams == {"fit": ("model-initialization",)}
    assert snapshot.snakefile_digest.startswith("sha256:")
    assert snapshot.checkpoint_expanded_families == ()


def test_declaring_a_checkpoint_expanded_family_moves_the_identity():
    plain = _definition().snapshot().identity()
    declared = _definition(checkpoint_expanded_families=("fit",)).snapshot().identity()
    assert plain != declared


def test_the_snapshot_identity_is_the_definition_identity():
    definition = _definition()
    assert definition.identity() == definition.snapshot().identity()


def test_a_malformed_checkpoint_declaration_is_refused():
    with pytest.raises(MalformedClosure):
        _definition(checkpoint_expanded_families=("fit", 3))
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `cd python && uv run --frozen pytest tests/test_adapter.py -k "snapshot or domain_is_v2 or checkpoint" -v`
Expected: FAIL — `WorkflowDefinition.__init__() got an unexpected keyword argument 'checkpoint_expanded_families'`.

- [ ] **Step 3: Implement it**

The value class is defined in **`recipe.py`**, beside `TraceJob`, and
re-exported from `adapter.py` (`from beliefs.recipe import
WORKFLOW_DEFINITION_DOMAIN, WorkflowDefinitionSnapshot`). Defining it in the
adapter and moving it later would invert the existing `adapter → recipe`
dependency in Task 3 and rewrite the same class twice.

```python
# python/src/beliefs/recipe.py — beside TraceJob
WORKFLOW_DEFINITION_DOMAIN = "science.workflow-definition.v2"


@sealed
@final
@dataclass(frozen=True)
class WorkflowDefinitionSnapshot:
    """The recipe's workflow member (computation §6.2): the declaration a
    closure can read, not a digest it cannot."""

    snakefile_digest: str
    family_streams: Mapping[str, tuple[str, ...]]
    checkpoint_expanded_families: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.snakefile_digest) is not str or not self.snakefile_digest.startswith("sha256:"):
            raise MalformedClosure("a workflow definition snapshot carries a sha256 snakefile digest")
        if not isinstance(self.family_streams, Mapping) or not all(
            type(family) is str and type(streams) is tuple and all(type(stream) is str for stream in streams)
            for family, streams in self.family_streams.items()
        ):
            raise MalformedClosure("workflow family streams must map strings to tuples of strings")
        if type(self.checkpoint_expanded_families) is not tuple or any(
            type(family) is not str for family in self.checkpoint_expanded_families
        ):
            raise MalformedClosure("checkpoint-expanded families are a tuple of strings")
        object.__setattr__(self, "family_streams", MappingProxyType(dict(self.family_streams)))

    def projection(self) -> dict[str, object]:
        return {
            "snakefile": self.snakefile_digest,
            "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},
            "checkpoint_expanded_families": sorted(self.checkpoint_expanded_families),
        }

    def identity(self) -> str:
        return v1.digest(WORKFLOW_DEFINITION_DOMAIN, self.projection())
```

`WorkflowDefinition` stays in `adapter.py`, gains
`checkpoint_expanded_families: tuple[str, ...] = ()`, and its `identity()`
becomes `return self.snapshot().identity()`:

```python
    def snapshot(self) -> WorkflowDefinitionSnapshot:
        return WorkflowDefinitionSnapshot(
            snakefile_digest="sha256:" + sha256(self.snakefile).hexdigest(),
            family_streams=self.family_streams,
            checkpoint_expanded_families=self.checkpoint_expanded_families,
        )
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest -x -q`
Expected: the whole suite is green. The domain change moves every workflow
definition identity, so update `fixtures_cut3.py` in this task by rebuilding
the values it constructs; if any test pins a digest literal, rebuild the value
rather than editing the literal. This task ends with a green suite, not a
handover of red tests.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/recipe.py python/src/beliefs/adapter.py \
        python/tests/test_adapter.py python/tests/fixtures_cut3.py
git commit -m "feat(recipe): carry the workflow-definition snapshot at v2"
```

---

### Task 3: The recipe carries the snapshot, `science.recipe.v2`

**Files:**
- Modify: `python/src/beliefs/recipe.py:304,342,378,401,405-434`
- Modify: `python/src/beliefs/boundary.py:318-356` (`_project`)
- Test: `python/tests/test_recipe.py`, `python/tests/fixtures_cut3.py`

**Interfaces:**
- Consumes: Task 2's `WorkflowDefinitionSnapshot`.
- Produces: `Recipe.workflow_definition: WorkflowDefinitionSnapshot` replacing
  `workflow_definition_identity: str`; `RECIPE_DOMAIN == "science.recipe.v2"`;
  `project_recipe(..., workflow_definition=<snapshot>, ...)`. Tasks 5, 6, 7,
  11 and 15 read `recipe.workflow_definition`.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_recipe.py
from beliefs.recipe import RECIPE_DOMAIN
from fixtures_cut3 import recipe


def test_the_recipe_domain_is_v2():
    assert RECIPE_DOMAIN == "science.recipe.v2"


def test_the_recipe_carries_the_declaration_a_closure_can_read():
    value = recipe()
    assert value.workflow_definition.family_streams == {"transform": ("model-initialization",)}


def test_the_projection_emits_the_snapshot_not_only_its_digest():
    projected = recipe()._projection()
    assert projected["workflow_definition"]["family_streams"] == {"transform": ["model-initialization"]}
    assert "workflow_definition_identity" not in projected


def test_changing_a_family_declaration_moves_the_recipe_identity():
    from beliefs.adapter import WorkflowDefinitionSnapshot

    left = recipe()
    right = recipe(
        workflow_definition=WorkflowDefinitionSnapshot(
            snakefile_digest=left.workflow_definition.snakefile_digest,
            family_streams={"transform": ("model-initialization", "resample-draws")},
            checkpoint_expanded_families=(),
        )
    )
    assert left.identity() != right.identity()
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py -k "domain_is_v2 or declaration or projection_emits" -v`
Expected: FAIL — `RECIPE_DOMAIN` is `science.recipe.v1` and `Recipe` has no
`workflow_definition`.

- [ ] **Step 3: Implement it**

In `recipe.py`: `RECIPE_DOMAIN = "science.recipe.v2"`; the field becomes
`workflow_definition: WorkflowDefinitionSnapshot`; `__post_init__` validates
its type rather than a component string; `_projection()` emits
`"workflow_definition": self.workflow_definition.projection()`; and
`project_recipe`'s keyword becomes `workflow_definition`.

In `boundary.py:318-356`, `_project` passes `definition.snapshot()` in both
branches, replacing `workflow_definition_identity=definition.identity()`.

In `fixtures_cut3.py`, `recipe()`'s defaults carry a snapshot built from
`definition().snapshot()`.

Importing `WorkflowDefinitionSnapshot` into `recipe.py` would invert the
existing `adapter → recipe` dependency. Move the snapshot value class into
`recipe.py` beside `TraceJob` and re-export it from `adapter.py`
(`from beliefs.recipe import WorkflowDefinitionSnapshot`), keeping
`WORKFLOW_DEFINITION_DOMAIN` with it. Task 2's tests import from
`beliefs.adapter` and must keep passing unchanged.

- [ ] **Step 4: Run the suite**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py tests/test_adapter.py tests/test_boundary.py -v`
Expected: PASS. Address every stale-digest failure by rebuilding the value,
never by pinning a literal.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/recipe.py python/src/beliefs/adapter.py python/src/beliefs/boundary.py python/tests/
git commit -m "feat(recipe): carry the workflow-definition snapshot at recipe v2"
```

---

### Task 4: Two launch attestations, receipt v3 and v4

**Files:**
- Modify: `python/src/beliefs/recipe.py:512-552`
- Modify: `python/src/beliefs/replay.py:203-215` (`qualifies`)
- Test: `python/tests/test_recipe.py`, `python/tests/test_confinement_values.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `LaunchAttestation(scratch_mapping, argv, rendered_config,
  capabilities, instance=None, rendered_environment=None, mounts=None)` and
  `BoundaryReceipt(planning: LaunchAttestation, execution: LaunchAttestation)`
  with `.confined` derived from `execution.instance is not None`;
  `BOUNDARY_RECEIPT_DOMAIN == "science.boundary-receipt.v3"`,
  `CONFINED_RECEIPT_DOMAIN == "science.boundary-receipt.v4"`. Tasks 5, 12 and
  16 build receipts; Task 15 reads `execution`.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_recipe.py
import pytest

from beliefs.errors import MalformedClosure
from beliefs.recipe import BOUNDARY_RECEIPT_DOMAIN, BoundaryReceipt, LaunchAttestation


def _launch(**overrides):
    fields = {"scratch_mapping": "/scratch/x", "argv": ("snakemake",), "rendered_config": (), "capabilities": ()}
    return LaunchAttestation(**{**fields, **overrides})


def test_the_minimal_receipt_domain_is_v3():
    assert BOUNDARY_RECEIPT_DOMAIN == "science.boundary-receipt.v3"


def test_a_receipt_composes_one_attestation_per_launch():
    receipt = BoundaryReceipt(planning=_launch(), execution=_launch(scratch_mapping="/scratch/y"))
    assert receipt.planning.scratch_mapping != receipt.execution.scratch_mapping
    assert receipt.confined is False


def test_two_launches_must_agree_about_confinement(confined_launch):
    # a MINIMAL planning launch beside a CONFINED execution launch: each
    # attestation is individually well formed, and the receipt still refuses
    with pytest.raises(MalformedClosure):
        BoundaryReceipt(planning=_launch(), execution=confined_launch())
```

`confined_launch` is a fixture building a `LaunchAttestation` with all three
confined members present, so this arm fails the receipt's agreement rule and
not the attestation's own 0-or-3 rule — an attestation carrying `instance`
without `mounts` is refused one level down and would prove the wrong thing.

and, for `qualifies`:

```python
# python/tests/test_confinement_values.py
def test_qualification_reads_the_execution_launch_and_not_the_planning_one(confined_launch):
    # BOTH launches confined — a mixed receipt is malformed — and they differ
    # in the evidence qualification actually reads
    qualifying = confined_launch(capabilities=REQUIRED_FOR_CLEAN_ENVIRONMENT)
    short = confined_launch(capabilities=("from-bundle",))
    assert qualifies(BoundaryReceipt(planning=short, execution=qualifying), ENVIRONMENT) is True
    assert qualifies(BoundaryReceipt(planning=qualifying, execution=short), ENVIRONMENT) is False


def test_a_planning_launch_cannot_supply_the_execution_s_environment_agreement(confined_launch):
    qualifying = confined_launch(environment_identity=ENVIRONMENT)
    other = confined_launch(environment_identity=OTHER_ENVIRONMENT)
    assert qualifies(BoundaryReceipt(planning=qualifying, execution=other), ENVIRONMENT) is False
```

`confined_launch` is used by **two modules** (`test_recipe.py` and
`test_confinement_values.py`), so it goes in `python/tests/conftest.py`, not
in either module — a module-local fixture does not cross that boundary. It is
a factory fixture returning a fully confined `LaunchAttestation` with
overridable `capabilities` and `environment_identity`, built from the existing
confined-receipt fixture values with `instance`, `rendered_environment` and
`mounts` moved onto the attestation:

```python
# python/tests/conftest.py
@pytest.fixture()
def confined_launch():
    def build(*, capabilities=REQUIRED_FOR_CLEAN_ENVIRONMENT, environment_identity=ENVIRONMENT,
              scratch_mapping="/science/out", argv=("snakemake",)):
        instance = InstanceAttestation(
            namespaces=CONFINED_NAMESPACES, mounts=CONFINED_MOUNTS,
            mount_plan_identity=mount_plan_identity(CONFINED_MOUNTS),
            environment_identity=environment_identity,
        )
        return LaunchAttestation(
            scratch_mapping=scratch_mapping, argv=argv, rendered_config=(),
            capabilities=tuple(capabilities), instance=instance,
            rendered_environment=RENDERED_ENVIRONMENT, mounts=SANDBOX_MOUNTS,
        )
    return build
```

`CONFINED_NAMESPACES`, `CONFINED_MOUNTS`, `RENDERED_ENVIRONMENT` and
`SANDBOX_MOUNTS` are the values `test_confinement_values.py` already builds
its confined receipt from — move them into `conftest.py` beside the fixture
rather than duplicating them. `ENVIRONMENT` and `OTHER_ENVIRONMENT` are two
distinct environment identity strings defined there too.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py tests/test_confinement_values.py -k "launch or receipt_domain or qualification" -v`
Expected: FAIL — no `LaunchAttestation`.

- [ ] **Step 3: Implement it**

Move the existing member set and its 0-or-3 rule from `BoundaryReceipt` onto
`LaunchAttestation` verbatim, with `confined` a property of the attestation.
`BoundaryReceipt` keeps two fields, refuses launches that disagree about
confinement, and its `identity()` selects `CONFINED_RECEIPT_DOMAIN` when
`execution.confined`. `_receipt_projection` emits
`{"planning": ..., "execution": ...}`. `qualifies` reads `receipt.execution` throughout, and its containment line is
spelled exactly so, because Task 21's K8 arm quotes it:

```python
    if receipt.execution.instance is None:
        return False
    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.execution.capabilities):
        return False
    return receipt.execution.instance.environment_identity == environment_identity
```

- [ ] **Step 4: Run the suite**

Run: `cd python && uv run --frozen pytest tests/test_recipe.py tests/test_confinement_values.py tests/test_confinement.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/recipe.py python/src/beliefs/replay.py python/tests/
git commit -m "feat(recipe): compose planning and execution launch attestations"
```

---

### Task 5: The run-domain matrix

**Files:**
- Modify: `python/src/beliefs/recipe.py:630` (`run_domain_for`)
- Modify: `python/src/beliefs/runrecord.py:500-520` (`decode_run_record`)
- Test: `python/tests/test_recipe.py`, `python/tests/test_runrecord.py`

**Interfaces:**
- Consumes: Tasks 3 and 4.
- Produces: `run_domain_for(recipe_v2: bool, confined: bool) -> str` and
  `run_domain_for_projection(parsed: Mapping[str, object]) -> str`, which
  reads both shapes out of a decoded projection and raises `MalformedRecord`
  on a cross-pair. Task 6 calls the projection form.

| recipe | receipt | run domain |
|---|---|---|
| v1, identity only | receipt v1 | `science.run.v1` |
| v1, identity only | confined receipt v2 | `science.run.v2` |
| v2, snapshot | planning receipt v3 | `science.run.v3` |
| v2, snapshot | confined planning receipt v4 | `science.run.v4` |

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_runrecord.py
import pytest

from beliefs.errors import MalformedRecord
from beliefs.recipe import run_domain_for, run_domain_for_projection


def _projection(*, recipe_key, receipt):
    return {"recipe": {recipe_key: "x"}, "occurrence": {"receipt": receipt}}


_V1_RECEIPT = {"scratch_mapping": "/s", "argv": [], "rendered_config": [], "capabilities": []}
_V2_RECEIPT = {**_V1_RECEIPT, "instance": {}, "rendered_environment": [], "mounts": []}
_V3_RECEIPT = {"planning": _V1_RECEIPT, "execution": _V1_RECEIPT}
# both launches confined: a receipt whose launches disagree is malformed, so a
# v4 fixture that mixed one of each would not be a v4 receipt at all
_V4_RECEIPT = {"planning": _V2_RECEIPT, "execution": _V2_RECEIPT}


def test_each_of_the_four_pairs_mints_its_own_domain():
    assert run_domain_for(recipe_v2=False, confined=False) == "science.run.v1"
    assert run_domain_for(recipe_v2=False, confined=True) == "science.run.v2"
    assert run_domain_for(recipe_v2=True, confined=False) == "science.run.v3"
    assert run_domain_for(recipe_v2=True, confined=True) == "science.run.v4"


@pytest.mark.parametrize(
    "recipe_key,receipt",
    [
        ("workflow_definition", _V1_RECEIPT),   # v2 recipe, v1 receipt
        ("workflow_definition", _V2_RECEIPT),   # v2 recipe, v2 receipt
        ("workflow_definition_identity", _V3_RECEIPT),  # v1 recipe, v3 receipt
        ("workflow_definition_identity", _V4_RECEIPT),  # v1 recipe, v4 receipt
    ],
)
def test_every_cross_pair_is_malformed(recipe_key, receipt):
    with pytest.raises(MalformedRecord):
        run_domain_for_projection(_projection(recipe_key=recipe_key, receipt=receipt))


def test_the_recipe_shape_is_read_from_its_own_key_never_inferred_from_the_receipt():
    assert run_domain_for_projection(_projection(recipe_key="workflow_definition", receipt=_V3_RECEIPT)) == "science.run.v3"
    assert run_domain_for_projection(_projection(recipe_key="workflow_definition_identity", receipt=_V1_RECEIPT)) == "science.run.v1"
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_runrecord.py -k domain -v`
Expected: FAIL — `run_domain_for() got an unexpected keyword argument 'recipe_v2'`.

- [ ] **Step 3: Implement it**

```python
# python/src/beliefs/recipe.py
RUN_DOMAINS = {
    (False, False): "science.run.v1",
    (False, True): "science.run.v2",
    (True, False): "science.run.v3",
    (True, True): "science.run.v4",
}


def run_domain_for(*, recipe_v2: bool, confined: bool) -> str:
    """The §3.5 matrix: the run domain is a function of the recipe's shape and
    the receipt's, never of one alone."""
    return RUN_DOMAINS[(recipe_v2, confined)]


def run_domain_for_projection(parsed: Mapping[str, object]) -> str:
    recipe = cast(Mapping[str, object], parsed["recipe"])
    receipt = cast(Mapping[str, object], cast(Mapping[str, object], parsed["occurrence"])["receipt"])
    composed = set(receipt) == {"planning", "execution"}
    recipe_v2 = "workflow_definition" in recipe
    if recipe_v2 == ("workflow_definition_identity" in recipe):
        raise MalformedRecord("a recipe projection carries exactly one workflow member")
    if recipe_v2 != composed:
        raise MalformedRecord(
            f"recipe shape v{2 if recipe_v2 else 1} does not pair with this receipt shape (§3.5)"
        )
    confined = _is_confined_receipt(cast(Mapping[str, object], receipt["execution"]) if composed else receipt)
    return run_domain_for(recipe_v2=recipe_v2, confined=confined)
```

`RunClosure.address()` calls `run_domain_for(recipe_v2=True, confined=...)` —
a constructed closure is always v2 — and `decode_run_record` calls
`run_domain_for_projection(parsed)`.

`composed` is computed **before** `recipe_v2`, deliberately: Task 21's K2 arm
mutates `recipe_v2` to read `composed`, and a mutation that references a name
not yet bound raises `UnboundLocalError` instead of demonstrating the
receipt-inference defect it claims.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_runrecord.py tests/test_recipe.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/recipe.py python/src/beliefs/runrecord.py python/tests/test_runrecord.py
git commit -m "feat(recipe): dispatch the run domain on recipe and receipt shape"
```

---

### Task 6: `decode_run_closure` and `RecipeVersionUnsupported`

**Files:**
- Modify: `python/src/beliefs/runrecord.py` (after `decode_run_record`)
- Modify: `python/src/beliefs/errors.py`
- Modify: `python/src/beliefs/recipe.py`
- Modify: `python/src/beliefs/adapter.py`
- Test: `python/tests/test_runrecord.py`

**Interfaces:**
- Consumes: Tasks 3, 4, 5.
- Produces: `decode_run_closure(node: Node) -> RunClosure`, raising
  `RecipeVersionUnsupported` for a v1 recipe. Tasks 11 and 15 test
  conformance over its output; and
  `EnvironmentReference(identity_value: str)`, a read-side recipe environment
  exposing `identity() -> str`. Execution continues to require an
  `EnvironmentManifest` and refuses a reference before launching the engine.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_runrecord.py
import pytest
from nodes.core.frontmatter import node_from_markdown

from beliefs.errors import RecipeVersionUnsupported
from beliefs.recipe import EnvironmentReference
from beliefs.replay import conformance
from beliefs.runrecord import decode_run_closure, publication_plan
from fixtures_cut3 import closure


def _node_for(run):
    _, _, (op,) = publication_plan(run)
    return node_from_markdown(op.content.decode("utf-8"))


def test_a_minted_closure_round_trips_through_the_typed_decode():
    run = closure()
    decoded = decode_run_closure(_node_for(run))
    assert decoded.address() == run.address()
    assert type(decoded.recipe.environment) is EnvironmentReference
    assert decoded.recipe.environment.identity() == run.recipe.environment.identity()
    assert decoded.recipe.workflow_definition.family_streams == run.recipe.workflow_definition.family_streams


def test_conformance_over_a_decoded_closure_equals_conformance_over_the_minted_one():
    run = closure()
    assert conformance(decode_run_closure(_node_for(run))) == conformance(run)


def test_a_v1_identity_only_recipe_is_refused_rather_than_given_an_invented_declaration(v1_run_node):
    with pytest.raises(RecipeVersionUnsupported):
        decode_run_closure(v1_run_node)
```

`v1_run_node` is a module fixture holding an explicit v1 projection. Keep its
members literal rather than manufacturing a v1 closure through the v2
constructors; its point is that old records still decode while typed decode
refuses to invent the missing declaration.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_runrecord.py -k decode_run_closure -v`
Expected: FAIL — no `decode_run_closure`.

- [ ] **Step 3: Implement it**

Add to `errors.py`, beside the other `RecordError` subclasses:

```python
class RecipeVersionUnsupported(RecordError):
    """A v1, identity-only recipe cannot be reconstructed as a RunClosure: the
    snapshot's members are not in the record, and inventing an empty
    family_streams would manufacture a declaration nobody made (design §3.6)."""
```

`decode_run_closure` validates through `decode_run_record`'s existing
projection checks, then refuses a v1 recipe on its own guard line — spelled
exactly so, because Task 21's K3 arm quotes it:

```python
    if "workflow_definition_identity" in recipe:
        raise RecipeVersionUnsupported(
            "a v1 recipe carries an identity where the snapshot's members belong"
        )
```

and otherwise rebuilds `Recipe`,
`ResultManifest` and `Occurrence` — including `LaunchAttestation` values,
`TraceJob`s and `RealizedSeeds` — from the projection. `decode_run_record`
itself is unchanged and keeps returning `RunPublication | None`.

The recipe projection contains only `environment.identity()`. Add the minimal
read-side carrier beside `EnvironmentManifest`:

```python
@dataclass(frozen=True)
class EnvironmentReference:
    identity_value: str

    def __post_init__(self) -> None:
        _require_component(self.identity_value, "environment identity")

    def identity(self) -> str:
        return self.identity_value
```

`Recipe.environment` accepts `EnvironmentManifest | EnvironmentReference`.
Typed decode constructs the reference from the stored identity, preserving the
recipe projection and closure address without inventing artifacts. Widen
`require_executing_environment` to the same union and fail early unless the
value is exactly an `EnvironmentManifest`; decoded evidence is inspectable but
cannot be executed.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_runrecord.py -v`
Expected: PASS, including the untouched v1 decode tests.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-09-01-workflow-surface-design.md docs/plans/2026-09-01-workflow-surface.md python/src/beliefs/recipe.py python/src/beliefs/adapter.py python/src/beliefs/runrecord.py python/src/beliefs/errors.py python/tests/test_runrecord.py
git commit -m "feat(runrecord): decode a typed run closure and refuse v1 recipes"
```

---

### Task 7: `definition_agrees_with_plan` over `SeedPlan | None`

**Files:**
- Modify: `python/src/beliefs/replay.py`
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_replay.py`

**Interfaces:**
- Consumes: Tasks 2, 3.
- Produces: `definition_agrees_with_plan(snapshot: WorkflowDefinitionSnapshot,
  plan: SeedPlan | None) -> str | None` — `None` when they agree, a reason
  string otherwise — and `DefinitionPlanMismatch` in `errors.py`. Tasks 11
  and 12 call it.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_replay.py
from beliefs.recipe import WorkflowDefinitionSnapshot
from beliefs.replay import definition_agrees_with_plan
from fixtures_cut3 import seed_plan

DIGEST = "sha256:" + "11" * 32


def _snapshot(family_streams):
    return WorkflowDefinitionSnapshot(
        snakefile_digest=DIGEST, family_streams=family_streams, checkpoint_expanded_families=()
    )


def test_agreement_is_none():
    assert definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), seed_plan()) is None


def test_a_family_stream_no_logical_stream_matches_disagrees():
    reason = definition_agrees_with_plan(_snapshot({"fit": ("resample-draws",)}), seed_plan())
    assert reason is not None and "resample-draws" in reason


def test_a_logical_stream_no_family_claims_disagrees():
    plan = seed_plan(streams=("model-initialization", "resample-draws"))
    reason = definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), plan)
    assert reason is not None and "resample-draws" in reason


def test_a_deterministic_recipe_expects_no_streams_at_all():
    assert definition_agrees_with_plan(_snapshot({}), None) is None
    reason = definition_agrees_with_plan(_snapshot({"fit": ("model-initialization",)}), None)
    assert reason is not None
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -k agrees -v`
Expected: FAIL — no `definition_agrees_with_plan`.

- [ ] **Step 3: Implement it**

```python
# python/src/beliefs/replay.py
def definition_agrees_with_plan(snapshot: WorkflowDefinitionSnapshot, plan: SeedPlan | None) -> str | None:
    """R16's both-directions equality as one pure predicate (design §5). The
    plan is optional: `Deterministic` and `StochasticUnseeded` expect the
    empty stream set, so a family claiming a stream under either contract
    disagrees exactly as an unmatched stream does under `Seeded`."""
    declared = {stream for streams in snapshot.family_streams.values() for stream in streams}
    expected = set(plan.streams) if plan is not None else set()
    if unmatched := sorted(declared - expected):
        return f"family streams no logical stream matches: {unmatched}"
    if unclaimed := sorted(expected - declared):
        return f"logical streams no family claims: {unclaimed}"
    return None
```

Add `DefinitionPlanMismatch(RecordError)` to `errors.py`; Task 12 raises it at
the boundary.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -k agrees -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/replay.py python/src/beliefs/errors.py python/tests/test_replay.py
git commit -m "feat(replay): state definition/plan agreement as one predicate"
```

---

### Task 8: `beliefs.seeds` — derivation and claim writing inside the job

**Files:**
- Create: `python/src/beliefs/seeds.py`
- Create: `python/tests/test_seeds.py`

**Interfaces:**
- Consumes: Task 1's `job_key`, `spec.derive_seed`, `SEED_DERIVATION_V1`.
- Produces: `bind(config: Mapping[str, object]) -> Callable[[object, object,
  str], int]`. The returned `seed(rule, wildcards, stream)` derives the seed,
  writes its claim, and returns the integer. Task 9 renders the config it
  reads; Task 10 reads the claims it writes.

`rule` and `wildcards` are Snakemake's own in-job objects: `rule` is a string
and `wildcards` supports `dict(wildcards)`. Accept both those and plain
values, so the helper is testable without the engine.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_seeds.py
import json
import pathlib

import pytest

from beliefs.errors import MalformedClosure, SeedClaimMalformed
from beliefs.recipe import job_key
from beliefs.seeds import bind
from beliefs.spec import derive_seed

CONFIG = {"seed_roots": {"model-initialization": "11"}, "seed_derivation_rule": "seed-derivation/v1"}


def test_the_seed_is_the_v1_derivation_over_this_job_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)("fit", {"sample": "a"}, "model-initialization")
    assert seed == derive_seed(11, job_key("fit", (("sample", "a"),)), "model-initialization")


def test_two_instances_of_one_family_draw_different_seeds(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)
    assert seed("fit", {"sample": "a"}, "model-initialization") != seed("fit", {"sample": "b"}, "model-initialization")


def test_the_claim_is_written_under_a_digest_name_carrying_its_own_tuple(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    value = bind(CONFIG)("fit", {"sample": "a"}, "model-initialization")
    claims = sorted((tmp_path / ".seeds").glob("*.json"))
    assert len(claims) == 1
    record = json.loads(claims[0].read_text())
    assert record == {
        "rule": "fit",
        "wildcards": {"sample": "a"},
        "job_key": job_key("fit", (("sample", "a"),)),
        "stream": "model-initialization",
        "seed": value,
    }
    assert claims[0].stem == record_digest_of(record)  # defined in Step 3's helper


def test_two_streams_in_one_job_write_two_claims(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {"seed_roots": {"a": "11", "b": "12"}, "seed_derivation_rule": "seed-derivation/v1"}
    seed = bind(config)
    seed("fit", {}, "a")
    seed("fit", {}, "b")
    assert len(list((tmp_path / ".seeds").glob("*.json"))) == 2


def test_a_repeated_claim_fails_inside_the_job_rather_than_overwriting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)
    seed("fit", {"sample": "a"}, "model-initialization")
    with pytest.raises(SeedClaimMalformed):
        seed("fit", {"sample": "a"}, "model-initialization")


def test_a_deterministic_config_has_no_roots_so_binding_refuses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(MalformedClosure):
        bind({})


def test_a_non_integral_root_is_refused_rather_than_coerced(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(MalformedClosure):
        bind({"seed_roots": {"model-initialization": "eleven"}, "seed_derivation_rule": "seed-derivation/v1"})
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_seeds.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.seeds'`.

- [ ] **Step 3: Implement it**

```python
# python/src/beliefs/seeds.py
"""The seed helper the workflow imports (design §4).

It ships in the environment closure — run confinement §4.2 captures this
checkout through its `.pth` line — so it is pinned by `environment_identity`
and never enters `code_identity`. It derives the seed AND writes the claim, so
the job key in the claim and the job key in the check are one call."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path

from beliefs.errors import MalformedClosure, SeedClaimMalformed
from beliefs.recipe import job_key
from beliefs.spec import SEED_DERIVATION_V1, derive_seed

CLAIM_DIRECTORY = ".seeds"


def _roots(config: Mapping[str, object]) -> dict[str, int]:
    if config.get("seed_derivation_rule") != SEED_DERIVATION_V1:
        raise MalformedClosure(f"the rendered config names no {SEED_DERIVATION_V1} seed plan")
    rendered = config.get("seed_roots")
    if not isinstance(rendered, Mapping) or not rendered:
        raise MalformedClosure("the rendered config carries no seed roots")
    roots: dict[str, int] = {}
    for stream, value in rendered.items():
        # the engine hands back strings for a structured config value, and an
        # int for a bare scalar; parse explicitly rather than trusting either
        text = value if type(value) is str else str(value)
        if not text.lstrip("-").isdigit():
            raise MalformedClosure(f"seed root for stream {stream!r} is not an integer: {text!r}")
        roots[str(stream)] = int(text)
    return roots


def record_digest_of(record: Mapping[str, object]) -> str:
    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def bind(config: Mapping[str, object]) -> Callable[[object, object, str], int]:
    """Bound once at Snakefile load, where `config` is in scope; an imported
    module cannot see the engine's injected global."""
    roots = _roots(config)

    def seed(rule: object, wildcards: object, stream: str) -> int:
        if stream not in roots:
            raise MalformedClosure(f"stream {stream!r} has no rendered root")
        pairs = tuple(sorted((str(k), str(v)) for k, v in dict(wildcards).items()))
        key = job_key(str(rule), pairs)
        value = derive_seed(roots[stream], key, stream)
        record = {
            "rule": str(rule),
            "wildcards": {name: value_ for name, value_ in pairs},
            "job_key": key,
            "stream": stream,
            "seed": value,
        }
        directory = Path(CLAIM_DIRECTORY)
        directory.mkdir(exist_ok=True)
        path = directory / f"{record_digest_of(record)}.json"
        try:
            handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise SeedClaimMalformed(f"a claim for {key}/{stream} was already written") from error
        with os.fdopen(handle, "w", encoding="utf-8") as claim:
            claim.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
        return value

    return seed
```

Add `SeedClaimMalformed(RecordError)` to `errors.py`. Import
`record_digest_of` in the test module.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_seeds.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/seeds.py python/src/beliefs/errors.py python/tests/test_seeds.py
git commit -m "feat(seeds): derive and claim a job's seed inside the job"
```

---

### Task 9: Render `seed_roots`, and pin the engine's coercion

**Files:**
- Modify: `python/src/beliefs/boundary.py:280-304` (`_render_config`)
- Test: `python/tests/test_boundary.py`

**Interfaces:**
- Consumes: Tasks 3, 7.
- Produces: a rendered config carrying `seed_roots` (a JSON object of stream →
  decimal string) and `seed_derivation_rule`, and no `seed_<stream>` key.
  Task 12 renders it for both launches.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_boundary.py
import json

from beliefs.boundary import _render_config
from fixtures_cut3 import definition, recipe, seeded


def test_the_roots_are_rendered_as_one_mapping_never_per_stream_keys():
    config = _render_config(recipe(nondeterminism=seeded()), definition().snapshot())
    assert json.loads(config["seed_roots"]) == {"model-initialization": "11"}
    assert config["seed_derivation_rule"] == "seed-derivation/v1"
    assert not any(key.startswith("seed_model") for key in config)


def test_two_streams_differing_only_in_punctuation_do_not_collide():
    plan = seed_plan(streams=("a-b", "a_b"), roots={"r": 11}, stream_roots={"a-b": "r", "a_b": "r"})
    snapshot = definition(family_streams={"transform": ("a-b", "a_b")}).snapshot()
    config = _render_config(recipe(nondeterminism=Seeded(plan=plan)), snapshot)
    assert json.loads(config["seed_roots"]) == {"a-b": "11", "a_b": "11"}


def test_a_deterministic_recipe_renders_no_seed_material():
    config = _render_config(recipe(), definition(family_streams={}).snapshot())
    assert "seed_roots" not in config and "seed_derivation_rule" not in config
```

and the engine-coercion pin, which is an execution test:

```python
def test_the_engine_coerces_a_structured_config_value_to_strings(tmp_path):
    # pins spike 5: `seed_roots={...}` arrives as a dict of STRINGS, a bare
    # scalar as an int. beliefs.seeds parses accordingly; if an engine upgrade
    # changes this, fail here rather than in a job.
    observed = run_config_probe(tmp_path, {"seed_roots": '{"a": 11}', "plain": "11"})
    assert observed["seed_roots"] == ["dict", {"a": "11"}]
    assert observed["plain"] == ["int", 11]
```

`run_config_probe` is written **in this task**, in
`python/tests/config_probe.py`, so Task 9 passes on its own:

```python
# python/tests/config_probe.py
"""What the engine actually delivers for a rendered config value."""

import json
import os
import subprocess
import sys

PROBE = """\
import json, pathlib

rule probe:
    output: "out.json"
    run:
        rows = {k: [type(v).__name__, v] for k, v in config.items()}
        pathlib.Path(output[0]).write_text(json.dumps(rows, sort_keys=True))
"""


def run_config_probe(tmp_path, config):
    """Return `{key: [type name, value]}` as the engine handed it to the job."""
    work = tmp_path / "probe"
    work.mkdir()
    (work / "Snakefile").write_text(PROBE)
    argv = [
        sys.executable, "-m", "snakemake", "--snakefile", str(work / "Snakefile"),
        "--cores", "1", "--directory", str(work), "--nolock",
        "--config", *[f"{key}={value}" for key, value in config.items()],
        "--", "out.json",
    ]
    result = subprocess.run(argv, cwd=work, env={**os.environ, "PYTHONHASHSEED": "0"},
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]
    return json.loads((work / "out.json").read_text())
```

Task 17 imports it from here rather than redefining it.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k "render or coerce" -v`
Expected: FAIL — `_render_config` still emits `seed_<stream>` keys and takes a
`WorkflowDefinition`.

- [ ] **Step 3: Implement it**

`_render_config(recipe, snapshot)` takes the snapshot; the definition/plan
check moves out (Task 12 calls the predicate before launching); and for a
`Seeded` recipe it renders exactly two keys:

```python
    config["seed_roots"] = json.dumps(
        {stream: str(plan.roots[plan.stream_roots[stream]]) for stream in sorted(plan.streams)},
        sort_keys=True,
        separators=(",", ":"),
    )
    config["seed_derivation_rule"] = plan.derivation_rule
```

Per-instance seed values are never rendered.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k "render or coerce" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/boundary.py python/tests/test_boundary.py python/tests/config_probe.py
git commit -m "feat(boundary): render seed roots as one mapping"
```

---

### Task 10: Read digest-named claims

**Files:**
- Modify: `python/src/beliefs/adapter.py:785-823` (`read_realized_seeds`)
- Test: `python/tests/test_adapter.py`

**Interfaces:**
- Consumes: Task 8's claim format.
- Produces: `read_realized_seeds(scratch) -> RealizedSeeds` keyed
  `[job_key][stream]`, refusing a claim whose filename disagrees with its
  content. Task 11's conformance reads the result.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_adapter.py
import json

import pytest

from beliefs.adapter import read_realized_seeds
from beliefs.errors import MalformedClosure, SeedClaimMalformed
from beliefs.recipe import job_key
from beliefs.seeds import record_digest_of


def _write(directory, record):
    directory.mkdir(exist_ok=True)
    (directory / f"{record_digest_of(record)}.json").write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"))
    )


def _record(stream="model-initialization", seed=7):
    key = job_key("fit", (("sample", "a"),))
    return {"rule": "fit", "wildcards": {"sample": "a"}, "job_key": key, "stream": stream, "seed": seed}


def test_claims_are_read_into_the_two_level_map(tmp_path):
    _write(tmp_path / ".seeds", _record())
    _write(tmp_path / ".seeds", _record(stream="resample-draws", seed=9))
    seeds = read_realized_seeds(tmp_path).seeds
    key = job_key("fit", (("sample", "a"),))
    assert seeds == {key: {"model-initialization": 7, "resample-draws": 9}}


def test_a_claim_whose_name_disagrees_with_its_content_is_refused(tmp_path):
    directory = tmp_path / ".seeds"
    directory.mkdir()
    (directory / ("00" * 32 + ".json")).write_text(json.dumps(_record(), sort_keys=True, separators=(",", ":")))
    with pytest.raises(SeedClaimMalformed):
        read_realized_seeds(tmp_path)


def test_the_key_is_never_reconstructed_from_the_path(tmp_path):
    record = _record()
    record["job_key"] = job_key("fit", (("sample", "b"),))  # content disagrees with itself
    _write(tmp_path / ".seeds", record)
    with pytest.raises(SeedClaimMalformed):
        read_realized_seeds(tmp_path)


def test_a_symlinked_claim_directory_is_still_refused(tmp_path):
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / ".seeds").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(MalformedClosure):
        read_realized_seeds(tmp_path)
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_adapter.py -k claim -v`
Expected: FAIL — the reader still merges by the record's top-level job keys.

- [ ] **Step 3: Implement it**

Keep the existing symlink and directory refusals verbatim. For each `*.json`:
parse with the duplicate-key hook already there, require exactly the five
members, recompute `record_digest_of(record)` and compare it to the filename
stem, recompute `job_key(record["rule"], sorted wildcards)` and compare it to
`record["job_key"]`, then merge into `merged[job_key][stream] = seed`,
refusing a repeated `(job, stream)` pair as `SeedClaimMalformed`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_adapter.py -k claim -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/adapter.py python/tests/test_adapter.py
git commit -m "feat(adapter): read digest-named seed claims"
```

---

### Task 11: Two-level seed conformance

**Files:**
- Modify: `python/src/beliefs/replay.py:175-201` (`conformance`)
- Test: `python/tests/test_replay.py`

**Interfaces:**
- Consumes: Tasks 1, 3, 7, 10.
- Produces: `conformance(run) -> str` checking, in order, definition/plan
  agreement, the per-job level and the over-occurrence level. Task 15 appends
  the job-set levels to the same function.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_replay.py
from beliefs.recipe import job_key
from beliefs.replay import CONFORMING, conformance
from fixtures_cut3 import closure, seed_plan, seeded

FIT_A = job_key("fit", (("sample", "a"),))
FIT_B = job_key("fit", (("sample", "b"),))


def _run(*, families, plan, seeds):
    return closure_with(
        nondeterminism=seeded(plan=plan),
        family_streams=families,
        realized={key: dict(streams) for key, streams in seeds.items()},
        trace=tuple(traced_from_key(key) for key in seeds),
    )


def test_a_job_realizing_a_stream_its_family_does_not_declare_is_non_conforming():
    run = _run(
        families={"fit": ("model-initialization",)},
        plan=seed_plan(streams=("model-initialization",)),
        seeds={FIT_A: {"model-initialization": 1, "resample-draws": 2}},
    )
    assert conformance(run).startswith("non-conforming")


def test_a_job_omitting_a_stream_its_family_declares_is_non_conforming():
    # a SECOND job realizes the stream the first omitted, so the occurrence
    # union is complete and only the per-job level can catch this — otherwise
    # the union check would pass the test whatever the per-job level did
    plan = seed_plan(streams=("model-initialization", "resample-draws"), roots={"r": 11},
                     stream_roots={"model-initialization": "r", "resample-draws": "r"})
    other = job_key("other", ())
    seeds = {
        FIT_A: {"model-initialization": correct_seed(11, FIT_A, "model-initialization")},
        other: {"resample-draws": correct_seed(11, other, "resample-draws")},
    }
    families = {"fit": ("model-initialization", "resample-draws"), "other": ("resample-draws",)}
    run = _run(families=families, plan=plan, seeds=seeds)
    assert {stream for claims in seeds.values() for stream in claims} == set(plan.streams)  # union complete
    assert conformance(run).startswith("non-conforming")


def test_a_wildcard_instance_is_judged_against_its_family():
    plan = seed_plan(streams=("model-initialization",))
    seeds = {
        key: {"model-initialization": correct_seed(11, key, "model-initialization")}
        for key in (FIT_A, FIT_B)
    }
    assert conformance(_run(families={"fit": ("model-initialization",)}, plan=plan, seeds=seeds)) == CONFORMING


def test_different_families_realizing_different_streams_conforms():
    plan = seed_plan(streams=("model-initialization", "resample-draws"), roots={"r": 11},
                     stream_roots={"model-initialization": "r", "resample-draws": "r"})
    a, b = job_key("a", ()), job_key("b", ())
    seeds = {
        a: {"model-initialization": correct_seed(11, a, "model-initialization")},
        b: {"resample-draws": correct_seed(11, b, "resample-draws")},
    }
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    assert conformance(_run(families=families, plan=plan, seeds=seeds)) == CONFORMING


def test_an_over_claiming_record_does_not_conform():
    plan = seed_plan(streams=("model-initialization", "resample-draws"), roots={"r": 11},
                     stream_roots={"model-initialization": "r", "resample-draws": "r"})
    a, b = job_key("a", ()), job_key("b", ())
    seeds = {
        key: {stream: correct_seed(11, key, stream) for stream in ("model-initialization", "resample-draws")}
        for key in (a, b)
    }
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    assert conformance(_run(families=families, plan=plan, seeds=seeds)).startswith("non-conforming")


def test_two_streams_in_one_job_are_both_checked():
    # the nesting: one job key, two stream keys, both derived and both read
    plan = seed_plan(streams=("model-initialization", "resample-draws"), roots={"r": 11},
                     stream_roots={"model-initialization": "r", "resample-draws": "r"})
    seeds = {FIT_A: {stream: correct_seed(11, FIT_A, stream)
                     for stream in ("model-initialization", "resample-draws")}}
    run = _run(families={"fit": ("model-initialization", "resample-draws")}, plan=plan, seeds=seeds)
    assert conformance(run) == CONFORMING


def test_a_constructed_closure_whose_definition_disagrees_is_non_conforming():
    # design §5's SECOND disposition: no boundary refused this one, because no
    # boundary ever saw it — it was constructed, as a decoded record is
    run = closure_with(family_streams={"fit": ("model-initialization",)}, nondeterminism=Deterministic(),
                       trace=(traced("fit", {}),))
    assert conformance(run).startswith("non-conforming")


def test_a_declared_stream_no_executed_job_realized_is_non_conforming():
    # every per-job check passes vacuously; the occurrence level is what fails
    plan = seed_plan(streams=("model-initialization", "resample-draws"), roots={"r": 11},
                     stream_roots={"model-initialization": "r", "resample-draws": "r"})
    a = job_key("a", ())
    seeds = {a: {"model-initialization": correct_seed(11, a, "model-initialization")}}
    families = {"a": ("model-initialization",), "b": ("resample-draws",)}
    run = _run(families=families, plan=plan, seeds=seeds)  # family b produced zero jobs
    assert conformance(run).startswith("non-conforming")
```

`correct_seed` is `beliefs.spec.derive_seed`, imported under that name in the
test module. Add **one** builder to `fixtures_cut3.py` and use it for every
value-width closure in Tasks 11, 15 and 18 — do not grow a second one:

```python
def traced(family, wildcards, job_id=None):
    pairs = tuple(sorted(wildcards.items()))
    return TraceJob(job_id=job_id or f"{family}-{len(pairs)}", rule=family, wildcards=pairs,
                    inputs=(), outputs=())


def traced_from_key(key):
    parsed = json.loads(key)
    return traced(parsed["rule"], parsed["wildcards"])


def closure_with(*, nondeterminism=None, family_streams=None, realized=None, trace=None,
                 outputs=(("out.txt", D_OUT),)):
    """A closure built from parts, for arms that need no engine."""
    families = family_streams if family_streams is not None else {}
    jobs = trace if trace is not None else (traced("transform", {}),)
    snapshot = WorkflowDefinitionSnapshot(
        snakefile_digest=D_IN, family_streams=families, checkpoint_expanded_families=()
    )
    built = recipe(nondeterminism=nondeterminism or Deterministic(), workflow_definition=snapshot,
                   invocation=invocation(declared_outputs=tuple(name for name, _ in outputs)))
    return RunClosure(
        recipe=built,
        result=ResultManifest(outputs=tuple(outputs)),
        occurrence=occurrence(trace=jobs, realized_seeds=RealizedSeeds(seeds=realized or {})),
    )
```

**This builder takes only what the record carries today.** `PlannedJob`,
`Occurrence.planned`, `checkpoint_expanded_families` on a constructed closure
and `Occurrence.target_keys` do not exist until Tasks 12 and 14, and a Task-11
builder naming them would not import. Tasks 12 and 14 each extend this one
builder when they add their member — and each **defaults the new member from
the trace**, so every closure built before them stays conforming once Task 15
lands: `planned` defaults to one `PlannedJob` per traced job, and
`target_keys` defaults to the last traced job's key. Without those defaults,
Task 11's conforming arms would start failing trace membership at Task 15.

Tasks 15 and 18 use these helpers, so their test bodies need no builders of
their own. `recipe`, `invocation` and `occurrence` are `fixtures_cut3.py`'s
existing builders.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -k "family or wildcard or over_claiming or declared_stream" -v`
Expected: FAIL — the current `conformance` validates claims only.

- [ ] **Step 3: Implement it**

```python
def conformance(run: RunClosure) -> str:
    """Design §6.5. Every level runs for every contract variant: an unseeded
    recipe still has a trace, a plan and targets, so there is no early return
    here and Task 15's levels are always reached."""
    contract = run.recipe.nondeterminism
    snapshot = run.recipe.workflow_definition
    plan = contract.plan if type(contract) is Seeded else None
    if reason := definition_agrees_with_plan(snapshot, plan):
        return f"non-conforming: {reason}"
    if plan is not None and plan.derivation_rule != SEED_DERIVATION_V1:
        return f"non-conforming: unsupported seed derivation rule {plan.derivation_rule!r}"

    realized = run.occurrence.realized_seeds.seeds
    # iterate the TRACE, not the claims: a claim-driven loop lets a traced job
    # that reported nothing evade its family's obligation entirely
    for job in run.occurrence.trace:
        key = job.job_key()
        declared = set(snapshot.family_streams.get(job.rule, ()))
        claims = realized.get(key, {})
        if set(claims) != declared:
            return (
                f"non-conforming: job {key!r} realized {sorted(claims)} against "
                f"its family's declaration {sorted(declared)}"
            )
        if plan is None:
            continue
        for stream, actual in sorted(claims.items()):
            expected = derive_seed(plan.roots[plan.stream_roots[stream]], key, stream)
            if actual != expected:
                return f"non-conforming: job {key!r} stream {stream!r} realized {actual}, expected {expected}"

    executed_keys = {job.job_key() for job in run.occurrence.trace}
    if orphans := sorted(set(realized) - executed_keys):
        return f"non-conforming: seed claims for jobs absent from the trace: {orphans}"

    union = {stream for claims in realized.values() for stream in claims}
    expected_streams = set(plan.streams) if plan is not None else set()
    if union != expected_streams:
        return f"non-conforming: realized streams {sorted(union)} against plan {sorted(expected_streams)}"
    return CONFORMING
```

An unseeded recipe reaches every level: its expected stream set is empty, so
a job reporting a seed fails the per-job level and an unexpected claim fails
the union level, without the deterministic early return the previous revision
had — which would have made Task 15's job-set checks unreachable for exactly
the runs most likely to have a multi-rule trace.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -v`
Expected: PASS. Update `replay.py`'s module docstring — its "Family coverage
is deferred" paragraph is now false.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/replay.py python/tests/test_replay.py python/tests/fixtures_cut3.py
git commit -m "feat(replay): check seed conformance at both levels"
```

---

### Task 12: The planning launch and the planned job set

**Files:**
- Modify: `python/src/beliefs/adapter.py` (plan reading, beside `read_trace`)
- Modify: `python/src/beliefs/boundary.py:360-490` (`_execute_run`)
- Modify: `python/src/beliefs/recipe.py` (`PlannedJob`, `Occurrence`)
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_adapter.py`, `python/tests/test_boundary.py`

**Interfaces:**
- Consumes: Tasks 1, 7, 9.
- Produces: `PlannedJob(job_key: str, family: str, outputs: tuple[str, ...],
  is_checkpoint: bool)`; `Occurrence.planned: tuple[PlannedJob, ...]`;
  `read_plan(events_file: Path) -> tuple[PlannedJob, ...]`;
  `PlanUnavailable` in `errors.py`. Tasks 13, 14 and 15 read the plan.

The planning launch runs in a **disposable planning directory**, staged with
the same inputs and discarded once the plan is read, so parse-time Snakefile
Python cannot touch the execution scratch.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_adapter.py
import json

import pytest

from beliefs.adapter import read_plan
from beliefs.errors import PlanUnavailable
from beliefs.recipe import PlannedJob, job_key


def _event(jobid, name, wildcards, output, is_checkpoint=False):
    return json.dumps({
        "level": "job_info", "jobid": jobid, "name": name, "wildcards": wildcards,
        "input": [], "output": output, "is_checkpoint": is_checkpoint,
    })


def test_a_job_emitted_twice_yields_one_planned_job(tmp_path):
    events = tmp_path / "dry.jsonl"
    events.write_text("\n".join([
        _event(1, "fit", {"sample": "a"}, ["outputs/a.txt"]),
        _event(1, "fit", {"sample": "a"}, ["outputs/a.txt"]),
    ]) + "\n")
    assert read_plan(events) == (
        PlannedJob(job_key=job_key("fit", (("sample", "a"),)), family="fit",
                   outputs=("outputs/a.txt",), is_checkpoint=False),
    )


def test_two_records_for_one_key_that_disagree_are_a_planning_refusal(tmp_path):
    events = tmp_path / "dry.jsonl"
    events.write_text("\n".join([
        _event(1, "split", {}, ["splits"], is_checkpoint=True),
        _event(1, "split", {}, ["splits"], is_checkpoint=False),
    ]) + "\n")
    with pytest.raises(PlanUnavailable):
        read_plan(events)


def test_a_plan_with_no_job_is_a_planning_refusal(tmp_path):
    events = tmp_path / "dry.jsonl"
    events.write_text("")
    with pytest.raises(PlanUnavailable):
        read_plan(events)


def test_the_job_id_is_not_a_member_because_dry_run_numbering_is_not_the_executions(tmp_path):
    events = tmp_path / "dry.jsonl"
    events.write_text(_event(7, "fit", {"sample": "a"}, ["outputs/a.txt"]) + "\n")
    assert not hasattr(read_plan(events)[0], "job_id")
```

and, at the boundary:

```python
# python/tests/test_boundary.py
def test_the_planning_launch_writes_nothing_into_the_execution_scratch(tmp_path):
    outcome = memory_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert isinstance(outcome, RunMinted)
    scratch = pathlib.Path(outcome.run.occurrence.receipt.execution.scratch_mapping)
    planning = pathlib.Path(outcome.run.occurrence.receipt.planning.scratch_mapping)
    assert scratch.exists() and planning != scratch and not planning.exists()  # planning discarded


def test_the_plan_is_carried_by_the_occurrence(tmp_path):
    outcome = memory_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION)
    assert {job.family for job in outcome.run.occurrence.planned} == {"transform"}


def test_an_unknown_target_is_a_planning_refusal_and_not_a_resolution_one(tmp_path):
    # spike 6: the engine refuses to plan at all for an unknown target — exit
    # 1, zero jobs — so this surfaces as PlanUnavailable. TargetUnresolvable
    # covers a plan that succeeded without naming the target (Task 14).
    outcome = memory_production(tmp_path, snakefile=SNAKEFILE_PRODUCTION, targets=("outputs/zzz.txt",))
    assert isinstance(outcome, RunRefused)
    assert "plan" in outcome.report.reason and "target" not in outcome.report.reason


def test_a_definition_disagreeing_with_its_plan_refuses_before_any_workflow_effect(tmp_path):
    # design §5: the predicate's FIRST disposition. A deterministic recipe
    # expects no streams, so a family declaring one disagrees.
    outcome = memory_production(
        tmp_path,
        snakefile=SNAKEFILE_PRODUCTION,
        definition_override=definition(snakefile=SNAKEFILE_PRODUCTION,
                                       family_streams={"transform": ("model-initialization",)}),
    )
    assert isinstance(outcome, RunRefused)
    assert "definition" in outcome.report.reason
    assert not list((tmp_path / "scratch").glob("planning-*"))  # refused before the planning launch
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_adapter.py -k plan tests/test_boundary.py -k planning -v`
Expected: FAIL — no `read_plan`, no `Occurrence.planned`.

- [ ] **Step 3: Implement it**

`PlannedJob` is a sealed frozen dataclass in `recipe.py` with a `projection()`
emitting its four members; `Occurrence` gains `planned: tuple[PlannedJob, ...]`
and its projection emits `[job.projection() for job in ...]` sorted by
`job_key`.

Extend Task 11's `closure_with` in the same commit, adding
`planned=None, expanded=()` and **defaulting `planned` from the trace** —
`tuple(PlannedJob(job_key=job.job_key(), family=job.rule, outputs=(),
is_checkpoint=False) for job in jobs)` — plus a `planned(family, outputs=(),
is_checkpoint=False, wildcards=())` helper for arms that need a plan differing
from the trace. Every closure built before this task stays conforming, which
is what keeps Task 11's arms green once Task 15 lands.

`read_plan` parses the events file exactly as `read_trace` does, groups by
`job_key(name, sorted wildcards)`, and refuses through `PlanUnavailable` when
two records under one key disagree in family, outputs or `is_checkpoint`, or
when no job is present.

In `_execute_run`, **before** anything is launched, spell the check exactly
so — Task 21's R16f arm quotes this line:

```python
    if reason := definition_agrees_with_plan(definition.snapshot(), plan):
        raise DefinitionPlanMismatch(reason)
```

which raises `DefinitionPlanMismatch` on a non-`None` result — this is design §5's first
disposition, and it is why `_render_config` no longer carries the check.

Then, before the execution launch: create
`planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))`,
stage the same inputs into it, run `build_argv(..., dry_run=True)` through
`run_engine`, and `read_plan` the events. Dispose of the directory in a
`try/finally`, so a refusal on a non-zero exit or a malformed plan cannot
leave planning state behind:

```python
    planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))
    try:
        returncode, _ = run_engine(planning_argv, cwd=planning_dir, env=planning_env)
        if returncode != 0:
            raise PlanUnavailable(f"the planning launch exited {returncode}")
        planned = read_plan(planning_events)
    finally:
        shutil.rmtree(planning_dir, ignore_errors=True)
```

`build_argv` gains a `dry_run: bool = False` parameter appending `--dryrun`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_adapter.py tests/test_boundary.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/adapter.py python/src/beliefs/boundary.py python/src/beliefs/recipe.py python/src/beliefs/errors.py python/tests/
git commit -m "feat(boundary): derive the planned job set in a planning launch"
```

---

### Task 13: Checkpoint declaration cross-checks

**Files:**
- Modify: `python/src/beliefs/boundary.py` (after the plan is read)
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_boundary.py`

**Interfaces:**
- Consumes: Tasks 2, 12.
- Produces: `check_checkpoint_declaration(snapshot, planned) -> None`, raising
  `CheckpointDeclarationUnmet`. Task 15 relies on the declaration being
  trustworthy.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_boundary.py
import pytest

from beliefs.boundary import check_checkpoint_declaration
from beliefs.errors import CheckpointDeclarationUnmet
from beliefs.recipe import PlannedJob, WorkflowDefinitionSnapshot, job_key

DIGEST = "sha256:" + "22" * 32


def _snapshot(families, expanded):
    return WorkflowDefinitionSnapshot(
        snakefile_digest=DIGEST, family_streams=families, checkpoint_expanded_families=expanded
    )


def _planned(family, is_checkpoint=False):
    return PlannedJob(job_key=job_key(family, ()), family=family, outputs=(), is_checkpoint=is_checkpoint)


def test_a_declaration_with_no_checkpoint_in_the_plan_is_refused():
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(_snapshot({"fit": ()}, ("fit",)), (_planned("fit"),))


def test_a_declared_family_the_definition_does_not_contain_is_refused():
    with pytest.raises(CheckpointDeclarationUnmet):
        check_checkpoint_declaration(
            _snapshot({"fit": ()}, ("absent",)), (_planned("split", is_checkpoint=True),)
        )


def test_an_empty_declaration_against_a_planned_checkpoint_is_permitted():
    check_checkpoint_declaration(_snapshot({"split": ()}, ()), (_planned("split", is_checkpoint=True),))


def test_a_declaration_with_a_planned_checkpoint_is_permitted():
    snapshot = _snapshot({"split": (), "fit": ()}, ("fit",))
    check_checkpoint_declaration(snapshot, (_planned("split", is_checkpoint=True), _planned("fit")))
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k checkpoint_declaration -v`
Expected: FAIL — no `check_checkpoint_declaration`.

- [ ] **Step 3: Implement it**

```python
def check_checkpoint_declaration(
    snapshot: WorkflowDefinitionSnapshot, planned: tuple[PlannedJob, ...]
) -> None:
    """The declaration is not an unfalsifiable escape hatch (design §6.3):
    the engine reports `is_checkpoint`, and the declaration must agree with
    it and name families the definition actually contains."""
    declared = set(snapshot.checkpoint_expanded_families)
    if unknown := sorted(declared - set(snapshot.family_streams)):
        raise CheckpointDeclarationUnmet(f"checkpoint-expanded families the definition does not contain: {unknown}")
    if declared and not any(job.is_checkpoint for job in planned):
        raise CheckpointDeclarationUnmet(
            f"checkpoint-expanded families {sorted(declared)} declared, but the plan contains no checkpoint"
        )
```

Call it in `_execute_run` immediately after `read_plan`. Add
`CheckpointDeclarationUnmet(RecordError)` to `errors.py`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k checkpoint_declaration -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/boundary.py python/src/beliefs/errors.py python/tests/test_boundary.py
git commit -m "feat(boundary): cross-check the checkpoint-expanded declaration"
```

---

### Task 14: Target resolution

**Files:**
- Modify: `python/src/beliefs/boundary.py`
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_boundary.py`

**Interfaces:**
- Consumes: Task 12.
- Produces: `resolve_targets(targets: tuple[str, ...], planned:
  tuple[PlannedJob, ...]) -> tuple[str, ...]` returning one target job key per
  requested target, raising `TargetUnresolvable` or `TargetAmbiguous`.
  Task 15 checks the returned keys against the trace.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_boundary.py
import pytest

from beliefs.boundary import resolve_targets
from beliefs.errors import TargetAmbiguous, TargetUnresolvable
from beliefs.recipe import PlannedJob, job_key

ALL = PlannedJob(job_key=job_key("all", ()), family="all", outputs=(), is_checkpoint=False)
FIT_A = PlannedJob(job_key=job_key("fit", (("s", "a"),)), family="fit", outputs=("outputs/a.done",), is_checkpoint=False)
FIT_B = PlannedJob(job_key=job_key("fit", (("s", "b"),)), family="fit", outputs=("outputs/b.done",), is_checkpoint=False)


def test_a_rule_target_resolves_to_the_job_with_that_family_and_no_wildcards():
    assert resolve_targets(("all",), (ALL, FIT_A)) == (ALL.job_key,)


def test_a_file_target_resolves_to_the_job_that_produces_it():
    assert resolve_targets(("outputs/a.done",), (ALL, FIT_A, FIT_B)) == (FIT_A.job_key,)


def test_two_targets_resolve_to_two_keys_in_request_order():
    assert resolve_targets(("outputs/b.done", "outputs/a.done"), (FIT_A, FIT_B)) == (FIT_B.job_key, FIT_A.job_key)


def test_a_target_the_plan_does_not_name_is_unresolvable():
    with pytest.raises(TargetUnresolvable):
        resolve_targets(("outputs/zzz.done",), (ALL, FIT_A))


def test_a_target_matching_two_planned_jobs_is_ambiguous():
    twin = PlannedJob(job_key=job_key("copy", ()), family="copy", outputs=("outputs/a.done",), is_checkpoint=False)
    with pytest.raises(TargetAmbiguous):
        resolve_targets(("outputs/a.done",), (FIT_A, twin))
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k resolve_targets -v`
Expected: FAIL — no `resolve_targets`.

- [ ] **Step 3: Implement it**

```python
def resolve_targets(targets: tuple[str, ...], planned: tuple[PlannedJob, ...]) -> tuple[str, ...]:
    """Each requested target resolves to exactly one planned job (design §6.4).
    Ordered after the plan is obtained, so an engine that refuses to plan at
    all is `PlanUnavailable` and never reaches here."""
    resolved: list[str] = []
    for target in targets:
        matches = [
            job for job in planned
            if job.job_key == job_key(target, ()) or target in job.outputs
        ]
        if not matches:
            raise TargetUnresolvable(f"the plan names no job for target {target!r}")
        if len(matches) > 1:
            raise TargetAmbiguous(f"target {target!r} matches {len(matches)} planned jobs")
        resolved.append(matches[0].job_key)
    return tuple(resolved)
```

A rule target is the planned job whose key is `job_key(target, ())`: the empty
wildcard binding is part of that equality, so no separate emptiness test is
needed.

Extend `closure_with` again here, adding `target_keys=None` and **defaulting
it to the last traced job's key**, for the same reason Task 12 defaulted
`planned` from the trace: closures built by earlier arms must keep satisfying
target satisfaction when Task 15 lands. Add `TargetUnresolvable(RecordError)` and `TargetAmbiguous(RecordError)`
to `errors.py`, and store the resolved keys on the occurrence beside the plan
as `Occurrence.target_keys: tuple[str, ...]`.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_boundary.py -k resolve_targets -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/boundary.py python/src/beliefs/errors.py python/tests/test_boundary.py
git commit -m "feat(boundary): resolve each target to exactly one planned job"
```

---

### Task 15: Job-set conformance

**Files:**
- Modify: `python/src/beliefs/replay.py` (`conformance`)
- Test: `python/tests/test_replay.py`

**Interfaces:**
- Consumes: Tasks 11, 12, 13, 14.
- Produces: `conformance` extended with §6.5's levels 4 and 5. Task 18's
  diagnostics and Task 21's N2 arms depend on the messages being distinct.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_replay.py
def test_an_executed_job_outside_the_plan_is_non_conforming():
    run = closure_with(
        planned=(planned("fit", ("outputs/a.done",)),),
        trace=(traced("fit", {"s": "a"}), traced("stowaway", {})),
        target_keys=(job_key("fit", (("s", "a"),)),),
    )
    assert "not in the plan" in conformance(run)


def test_a_checkpoint_expanded_family_is_admitted_though_it_was_unplannable():
    run = closure_with(
        planned=(planned("split", ("splits",), is_checkpoint=True),),
        trace=(traced("split", {}), traced("fit", {"n": "a"})),
        expanded=("fit",),
        target_keys=(job_key("split", ()),),
    )
    assert conformance(run) == CONFORMING


def test_an_unexpanded_family_gets_no_such_admission():
    run = closure_with(
        planned=(planned("split", ("splits",), is_checkpoint=True),),
        trace=(traced("split", {}), traced("fit", {"n": "a"})),
        expanded=(),
        target_keys=(job_key("split", ()),),
    )
    assert "not in the plan" in conformance(run)


def test_a_resolved_target_missing_from_the_trace_is_non_conforming():
    run = closure_with(
        planned=(planned("fit", ("outputs/a.done",)), planned("report", ("outputs/r.txt",))),
        trace=(traced("fit", {}),),
        target_keys=(job_key("report", ()),),
    )
    assert "target" in conformance(run)
```

`closure_with`, `planned` and `traced` are helpers added to
`fixtures_cut3.py`: they build a deterministic closure with the given plan,
trace, expanded-family declaration and target keys, so these arms need no
engine.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -k "outside_the_plan or expanded or target_missing" -v`
Expected: FAIL — `conformance` returns `CONFORMING` for all four.

- [ ] **Step 3: Implement it**

**Replace** Task 11's final `return CONFORMING` — appending after it would
leave this block unreachable. The union check keeps its early return on
failure; only the terminal success return is replaced:

```python
    if union != expected_streams:
        return f"non-conforming: realized streams {sorted(union)} against plan {sorted(expected_streams)}"
    # ↓ everything below replaces Task 11's terminal `return CONFORMING`
```

The replacement runs for every contract variant, since Task 11 removed the
deterministic early return precisely so it would:

```python
    planned_keys = {job.job_key for job in run.occurrence.planned}
    expanded = set(run.recipe.workflow_definition.checkpoint_expanded_families)
    for job in run.occurrence.trace:
        if job.job_key() not in planned_keys and job.rule not in expanded:
            return f"non-conforming: executed job {job.job_key()!r} is not in the plan"
    executed = {job.job_key() for job in run.occurrence.trace}
    if missing := sorted(set(run.occurrence.target_keys) - executed):
        return f"non-conforming: resolved target {missing[0]!r} was not executed"
    return CONFORMING
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_replay.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/replay.py python/tests/
git commit -m "feat(replay): check trace membership and target satisfaction"
```

---

### Task 16: The confined planning instance

**Files:**
- Modify: `python/src/beliefs/boundary.py:490-604` (`_execute_confined`)
- Test: `python/tests/acceptance/test_confinement_acceptance.py`

**Interfaces:**
- Consumes: Tasks 4, 12.
- Produces: a confined run whose receipt carries two confined
  `LaunchAttestation`s over one verified snapshot.

Each instance still executes exactly one snakemake argv, so cut 13's
derivation of `from-bundle` from the observed inner argv is untouched.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/acceptance/test_confinement_acceptance.py
def test_a_confined_run_attests_both_launches_over_one_snapshot(tmp_path, confinement_gate):
    outcome = run_production(tmp_path, port=MEMORY_PORT, boundary_policy=CONFINED_POLICY)
    assert isinstance(outcome, RunMinted)
    receipt = outcome.run.occurrence.receipt
    assert receipt.planning.instance is not None and receipt.execution.instance is not None
    assert receipt.planning.instance.environment_identity == receipt.execution.instance.environment_identity
    assert receipt.planning.instance.mount_plan_identity == receipt.execution.instance.mount_plan_identity
    assert receipt.planning.mounts != receipt.execution.mounts
    assert receipt.confined is True


def test_each_confined_instance_executes_exactly_one_engine_argv(tmp_path, confinement_gate):
    outcome = run_production(tmp_path, port=MEMORY_PORT, boundary_policy=CONFINED_POLICY)
    for launch in (outcome.run.occurrence.receipt.planning, outcome.run.occurrence.receipt.execution):
        assert launch.argv.count("-m") == 1 and "snakemake" in launch.argv
    assert "--dryrun" in outcome.run.occurrence.receipt.planning.argv
    assert "--dryrun" not in outcome.run.occurrence.receipt.execution.argv
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_confinement_acceptance.py -k launches -v`
Expected: FAIL — the confined path builds a single-launch receipt.

- [ ] **Step 3: Implement it**

In `_execute_confined`, materialize the verified snapshot once, then run the
existing gated-launch sequence twice: once against the planning directory with
`dry_run=True`, reading the plan from the events file; once against the
execution output root as today. Each launch produces its own
`LaunchAttestation` from the existing probe, and the two are composed into one
`BoundaryReceipt`. Their canonical sandbox mount-plan identity is the same;
their attested host mappings differ because they name distinct directories.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_confinement_acceptance.py -v`
Expected: PASS on a host meeting the confinement gate; the gate errors and
never skips.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/boundary.py python/tests/acceptance/test_confinement_acceptance.py
git commit -m "feat(boundary): plan in its own confined instance"
```

---

### Task 17: Multi-rule, wildcard and checkpoint fixtures, and R21's arms

**Files:**
- Create: `python/tests/fixtures_cut15.py`
- Test: `python/tests/test_cut15_workflows.py`

**Interfaces:**
- Consumes: Tasks 8, 9, 12, 14.
- Produces: `SNAKEFILE_WILDCARD`, `SNAKEFILE_TWO_FAMILIES`,
  `SNAKEFILE_TWO_TARGETS`, `SNAKEFILE_CHECKPOINT`, `SNAKEFILE_ZERO_JOB_FAMILY`,
  `SNAKEFILE_ONE_RULE_PIPELINE`, `SNAKEFILE_INPUT_DEPENDENT_DAG`,
  `SNAKEFILE_CONSTANT_PRODUCTION`, and a **standalone**
  `run_workflow(work_dir, **kwargs)` calling `execute_production_run` directly
  — not a wrapper over `run_production`, which has no `scratch_base` and
  stages into a fixed directory. It takes `family_streams`,
  `checkpoint_expanded_families`, `nondeterminism`, `inputs`, `held_inputs`,
  `scratch_base` and `data`. `run_config_probe` is imported from Task 9's
  `config_probe.py`, not redefined. Tasks 18-20 use these.

- [ ] **Step 1: Write the fixtures and the failing test**

```python
# python/tests/fixtures_cut15.py
SNAKEFILE_WILDCARD = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)
SAMPLES = ["a", "b"]

rule all:
    input: expand("outputs/{s}.txt", s=SAMPLES)

rule fit:
    input: "inputs/data.txt"
    output: "outputs/{s}.txt"
    run:
        value = seed(rule, wildcards, "model-initialization")
        pathlib.Path(output[0]).write_text(f"{wildcards.s}:{value}")
"""

SNAKEFILE_TWO_TARGETS = """\
import pathlib

rule analysis:
    input: "inputs/data.txt"
    output: "outputs/analysis.txt"
    run:
        pathlib.Path(output[0]).write_text(pathlib.Path(input[0]).read_text().upper())

rule report:
    input: "outputs/analysis.txt"
    output: "outputs/report.txt"
    run:
        pathlib.Path(output[0]).write_text("report:" + pathlib.Path(input[0]).read_text())
"""
```

```python
SNAKEFILE_TWO_FAMILIES = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)

rule all:
    input: "outputs/a.txt", "outputs/b.txt"

rule a:
    input: "inputs/data.txt"
    output: "outputs/a.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "model-initialization")))

rule b:
    input: "inputs/data.txt"
    output: "outputs/b.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "resample-draws")))
"""

SNAKEFILE_CHECKPOINT = """\
import pathlib

checkpoint split:
    input: "inputs/data.txt"
    output: directory("splits")
    run:
        target = pathlib.Path(output[0]); target.mkdir(parents=True, exist_ok=True)
        for name in ("a", "b"):
            (target / (name + ".txt")).write_text(name)

def parts(wildcards):
    directory = checkpoints.split.get(**wildcards).output[0]
    names = sorted(q.stem for q in pathlib.Path(directory).glob("*.txt"))
    return expand("outputs/{n}.done", n=names)

rule fit:
    input: "splits/{n}.txt"
    output: "outputs/{n}.done"
    run:
        pathlib.Path(output[0]).write_text(wildcards.n)

rule all:
    input: parts
"""

# family `unused` is declared and never runs: it is off the path to the
# requested target, so every per-job check passes vacuously (R16's
# execution-coverage arm)
SNAKEFILE_ZERO_JOB_FAMILY = """\
import pathlib
from beliefs.seeds import bind

seed = bind(config)

rule used:
    input: "inputs/data.txt"
    output: "outputs/used.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "model-initialization")))

rule unused:
    input: "inputs/data.txt"
    output: "outputs/unused.txt"
    run:
        pathlib.Path(output[0]).write_text(str(seed(rule, wildcards, "resample-draws")))
"""

# the DAG is read FROM THE INPUT at parse time, so two held inputs give two
# different job sets. SNAKEFILE_WILDCARD cannot do this: its SAMPLES list is
# hardcoded, so every execution of it plans the same jobs (Task 18)
SNAKEFILE_INPUT_DEPENDENT_DAG = """\
import pathlib

SAMPLES = pathlib.Path("inputs/data.txt").read_text().split()

rule all:
    input: expand("outputs/{s}.txt", s=SAMPLES)

rule fit:
    input: "inputs/data.txt"
    output: "outputs/{s}.txt"
    run:
        pathlib.Path(output[0]).write_text(wildcards.s)
"""

# two runs, different transforms inputs, ONE output digest: the second
# producer gives the composition a route the stamped basis does not have
# (Task 20)
SNAKEFILE_CONSTANT_PRODUCTION = """\
import pathlib

rule transform:
    input: "inputs/data.txt"
    output: "outputs/result.txt"
    run:
        pathlib.Path(output[0]).write_text("constant")
"""
```

```python
# python/tests/test_cut15_workflows.py
def test_two_targets_over_one_definition_are_two_recipes(tmp_path):
    analysis = run_workflow(tmp_path / "a", snakefile=SNAKEFILE_TWO_TARGETS,
                            targets=("outputs/analysis.txt",), declared_outputs=("outputs/analysis.txt",))
    report = run_workflow(tmp_path / "b", snakefile=SNAKEFILE_TWO_TARGETS,
                          targets=("outputs/report.txt",), declared_outputs=("outputs/report.txt",))
    assert isinstance(analysis, RunMinted) and isinstance(report, RunMinted)
    assert analysis.run.recipe.workflow_definition == report.run.recipe.workflow_definition
    assert analysis.run.recipe.identity() != report.run.recipe.identity()


def test_a_manifest_is_built_across_the_outputs_of_several_rules(tmp_path):
    outcome = run_workflow(tmp_path, snakefile=SNAKEFILE_TWO_TARGETS,
                           targets=("outputs/report.txt",),
                           declared_outputs=("outputs/analysis.txt", "outputs/report.txt"))
    assert {name for name, _ in outcome.run.result.outputs} == {"outputs/analysis.txt", "outputs/report.txt"}


def test_a_wildcard_run_records_one_seed_per_instance(tmp_path):
    outcome = run_workflow(tmp_path, snakefile=SNAKEFILE_WILDCARD, targets=("all",),
                           declared_outputs=("outputs/a.txt", "outputs/b.txt"),
                           family_streams={"fit": ("model-initialization",), "all": ()},
                           nondeterminism=seeded())
    assert isinstance(outcome, RunMinted)
    assert len(outcome.run.occurrence.realized_seeds.seeds) == 2
    assert conformance(outcome.run) == CONFORMING


def test_the_family_rule_binds_for_a_production_recipe_with_no_spec(tmp_path):
    # the family declarations are read from the RECIPE's snapshot, so the rule
    # binds for a shape that carries no spec at all
    outcome = run_workflow(tmp_path, snakefile=SNAKEFILE_TWO_FAMILIES, targets=("all",),
                           declared_outputs=("outputs/a.txt", "outputs/b.txt"),
                           family_streams={"a": ("model-initialization",), "b": ("resample-draws",), "all": ()},
                           nondeterminism=seeded(plan=seed_plan(
                               streams=("model-initialization", "resample-draws"), roots={"r": 11},
                               stream_roots={"model-initialization": "r", "resample-draws": "r"})))
    assert isinstance(outcome, RunMinted)
    assert outcome.run.recipe.spec_identity is None
    assert conformance(outcome.run) == CONFORMING


def test_a_declared_family_producing_zero_jobs_is_non_conforming(tmp_path):
    # execution coverage: `unused` is off the path to the requested target, so
    # every per-job check passes vacuously and the occurrence level is what
    # catches it
    outcome = run_workflow(tmp_path, snakefile=SNAKEFILE_ZERO_JOB_FAMILY,
                           targets=("outputs/used.txt",), declared_outputs=("outputs/used.txt",),
                           family_streams={"used": ("model-initialization",), "unused": ("resample-draws",)},
                           nondeterminism=seeded(plan=seed_plan(
                               streams=("model-initialization", "resample-draws"), roots={"r": 11},
                               stream_roots={"model-initialization": "r", "resample-draws": "r"})))
    assert isinstance(outcome, RunMinted)
    assert conformance(outcome.run).startswith("non-conforming")


def test_the_invocation_does_not_enumerate_the_jobs_a_target_implies(tmp_path):
    outcome = run_workflow(tmp_path, snakefile=SNAKEFILE_WILDCARD, targets=("all",),
                           declared_outputs=("outputs/a.txt", "outputs/b.txt"),
                           family_streams={"fit": ("model-initialization",), "all": ()},
                           nondeterminism=seeded())
    assert outcome.run.recipe.invocation.targets == ("all",)
    assert not hasattr(outcome.run.recipe.invocation, "jobs")
    assert len(outcome.run.occurrence.planned) > len(outcome.run.recipe.invocation.targets)
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py -v`
Expected: FAIL — `fixtures_cut15` does not exist.

- [ ] **Step 3: Make them pass**

`run_workflow` is **standalone**, not a wrapper over
`fixtures_cut3.run_production`: that helper has no `scratch_base` parameter
(`fixtures_cut3.py:396`) and stages into a fixed `tmp_path/"code"`, so calling
it twice under one `tmp_path` fails on `stage()`'s second `mkdir`
(`fixtures_cut3.py:337`). Each call therefore takes its **own work
directory**:

```python
def run_workflow(work_dir, *, port=MEMORY_PORT, snakefile, targets, declared_outputs,
                 family_streams=None, checkpoint_expanded_families=(), nondeterminism=None,
                 inputs=None, held_inputs=None, parameters=None, data="hello", scratch_base=None,
                 boundary_policy=MINIMAL_POLICY, started_at="2026-09-01T00:00:00Z",
                 host_realization="host-a", cores=1):
    work_dir.mkdir(parents=True, exist_ok=True)
    code, held = stage(work_dir, snakefile=snakefile, data=data)
    contract = nondeterminism if nondeterminism is not None else Deterministic()
    definition = WorkflowDefinition(
        snakefile=snakefile.encode("utf-8"),
        family_streams=family_streams if family_streams is not None else {},
        checkpoint_expanded_families=tuple(checkpoint_expanded_families),
    )
    supplied = held_inputs if held_inputs is not None else {
        DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"
    }
    authored = inputs if inputs is not None else (
        RecipeInput(role="transforms", dataset=DATA_ADDRESS,
                    content="sha256:" + sha256(supplied[DATA_ADDRESS].read_bytes()).hexdigest()),
    )
    return execute_production_run(
        inputs=authored, parameters=parameters or {}, nondeterminism=contract, port=port,
        boundary_policy=boundary_policy, definition=definition, code_roots=(code,),
        held_inputs=supplied, entrypoint="code/workflow/Snakefile", targets=tuple(targets),
        declared_outputs=tuple(declared_outputs), actor="tester", observer="observer-1",
        started_at=started_at, host_realization=host_realization,
        scratch_base=scratch_base if scratch_base is not None else work_dir / "scratch",
        cores=cores,
    )
```

`stage` is `fixtures_cut3.stage`, which takes the directory to stage into. No
production-code change should be needed in this task; if one is, it belongs to
the task that owns that file.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/tests/fixtures_cut15.py python/tests/test_cut15_workflows.py
git commit -m "test(cut15): exercise multi-rule, wildcard and two-target workflows"
```

---

### Task 18: Definition equality and job-set diagnostics

**Files:**
- Modify: `python/src/beliefs/verify.py:321-327` (`_job_diagnostics`)
- Create: `python/src/beliefs/workflows.py`
- Test: `python/tests/test_verify.py`, `python/tests/test_cut15_workflows.py`

**Interfaces:**
- Consumes: Tasks 1, 3.
- Produces: `same_definition(runs: Iterable[RunClosure]) -> dict[str,
  tuple[str, ...]]`, mapping a definition identity to the addresses of the
  runs that executed it. No view record and no `workflow` kind — view records
  are cut 14's and the query evaluator is `world-read`'s.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_cut15_workflows.py
from beliefs.workflows import same_definition


def test_runs_sharing_a_definition_are_the_same_pipeline(tmp_path):
    first = run_workflow(tmp_path / "1", snakefile=SNAKEFILE_TWO_TARGETS,
                         targets=("outputs/analysis.txt",), declared_outputs=("outputs/analysis.txt",))
    second = run_workflow(tmp_path / "2", snakefile=SNAKEFILE_TWO_TARGETS,
                          targets=("outputs/report.txt",), declared_outputs=("outputs/report.txt",))
    grouped = same_definition([first.run, second.run])
    assert list(grouped) == [first.run.recipe.workflow_definition.identity()]
    assert set(grouped[first.run.recipe.workflow_definition.identity()]) == {
        first.run.address(), second.run.address()
    }


def test_two_decompositions_of_one_computation_are_different_definitions(tmp_path):
    one_rule = run_workflow(tmp_path / "one", snakefile=SNAKEFILE_ONE_RULE_PIPELINE,
                            targets=("outputs/report.txt",), declared_outputs=("outputs/report.txt",))
    two_rules = run_workflow(tmp_path / "two", snakefile=SNAKEFILE_TWO_TARGETS,
                             targets=("outputs/report.txt",), declared_outputs=("outputs/report.txt",))
    assert one_rule.run.result.outputs == two_rules.run.result.outputs  # same computation
    assert len(same_definition([one_rule.run, two_rules.run])) == 2  # different definitions
```

```python
# python/tests/test_verify.py
from beliefs.recipe import job_key
from beliefs.verify import _job_diagnostics


def test_a_differing_job_set_is_reported_by_job_key():
    original = closure_with(trace=(traced("fit", {"s": "a"}),))
    replayed = closure_with(trace=(traced("fit", {"s": "a"}), traced("fit", {"s": "b"})))
    (message,) = _job_diagnostics(original, replayed)
    assert job_key("fit", (("s", "b"),)) in message


def test_a_data_dependent_replay_over_different_inputs_is_conforming(tmp_path):
    # R16's negative: a legitimately different job set is CONFORMING, and the
    # difference is reported as a diagnostic
    original, replayed = data_dependent_pair(tmp_path)  # different held inputs
    assert conformance(original) == CONFORMING and conformance(replayed) == CONFORMING
    assert _job_diagnostics(original, replayed) != ()


def test_a_differing_job_set_alone_costs_no_scope():
    # the "no verdict and no scope" half, stated where it is provable: ONE
    # recipe whose two executions ran different job sets still derives a
    # positive scope. Over different held INPUTS the recipe differs, so scope
    # would be not-certified for that reason and would prove nothing here.
    # Constructed closures, so this task depends on no later fixture.
    # the plan must name the jobs that ran, wildcards included, or both
    # closures are non-conforming on trace membership rather than conforming
    narrow = closure_with(
        trace=(traced("fit", {"n": "a"}),),
        planned=(planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),),
        target_keys=(job_key("fit", (("n", "a"),)),),
    )
    wide = closure_with(
        trace=(traced("fit", {"n": "a"}), traced("fit", {"n": "b"})),
        planned=(planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),
                 planned("fit", ("outputs/b.done",), wildcards=(("n", "b"),))),
        target_keys=(job_key("fit", (("n", "a"),)),),
    )
    assert narrow.recipe.identity() == wide.recipe.identity()   # the trace is not a recipe member
    assert conformance(narrow) == CONFORMING and conformance(wide) == CONFORMING
    # scope ALONE, so the assertion cannot pass or fail on the diagnostic:
    # that is the other test's subject
    assert derive_scope(narrow, wide, certification=None) == "same-environment"
```

Both closures come from Task 11's `closure_with`, so Task 18 needs nothing
Task 19 builds. Task 19's engine-level fan-out proves the same property
against the real engine and is that task's own arm.

Add `SNAKEFILE_ONE_RULE_PIPELINE` to `fixtures_cut15.py` — one rule producing
`outputs/report.txt` with the same bytes the two-rule pipeline produces — and
`data_dependent_pair`, which runs **`SNAKEFILE_INPUT_DEPENDENT_DAG`** (Task
17) over two held inputs, `"a b"` and `"a b c"`, so the two executions plan
and run different job sets:

```python
def data_dependent_pair(tmp_path):
    narrow = run_workflow(tmp_path / "narrow", snakefile=SNAKEFILE_INPUT_DEPENDENT_DAG,
                          data="a b", targets=("all",),
                          declared_outputs=("outputs/a.txt", "outputs/b.txt"))
    wide = run_workflow(tmp_path / "wide", snakefile=SNAKEFILE_INPUT_DEPENDENT_DAG,
                        data="a b c", targets=("all",),
                        declared_outputs=("outputs/a.txt", "outputs/b.txt", "outputs/c.txt"))
    return narrow.run, wide.run
```

`SNAKEFILE_WILDCARD` cannot serve here — its `SAMPLES` list is hardcoded, so
every execution of it plans the same jobs whatever the input holds.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py tests/test_verify.py -k "definition or job_set or data_dependent" -v`
Expected: FAIL — no `beliefs.workflows`; `_job_diagnostics` still spells keys
as `(rule, wildcards)`.

- [ ] **Step 3: Implement it**

```python
# python/src/beliefs/workflows.py
"""§6.3's "which runs executed the same pipeline" — a query, not an entity."""

from __future__ import annotations

from collections.abc import Iterable

from beliefs.recipe import RunClosure


def same_definition(runs: Iterable[RunClosure]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for run in runs:
        grouped.setdefault(run.recipe.workflow_definition.identity(), []).append(run.address())
    return {identity: tuple(sorted(addresses)) for identity, addresses in grouped.items()}
```

and in `verify.py`, replace the two set comprehensions with
`{job.job_key() for job in ...occurrence.trace}`, leaving the message shape
and the "no verdict, no scope" behaviour exactly as they are.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py tests/test_verify.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/workflows.py python/src/beliefs/verify.py python/tests/
git commit -m "feat(workflows): compute definition equality and report job-set diagnostics by job key"
```

---

### Task 19: R2's fan-out fixture under `minimal-v1`

**Files:**
- Modify: `python/tests/fixtures_cut15.py`
- Test: `python/tests/test_cut15_workflows.py`

**Interfaces:**
- Consumes: Task 17.
- Produces: `SNAKEFILE_SCRATCH_KEYED_FANOUT` and `fanout_width(base_name: str)
  -> int`, the pure function the Snakefile and the test both use.

Job ids are **stable** across identical runs, so a multi-job DAG proves
nothing (spike 3). The job **set** must vary, and it varies here on the
scratch base directory name — a receipt member, never a recipe member, which
is what R21 negative (c) pins. This fixture runs under `minimal-v1` only: a
confined workflow's working directory is `/science/out`, constant across
instances, so the same fixture under `confined-v1` would produce one job set.

- [ ] **Step 1: Write the failing test**

```python
# python/tests/test_cut15_workflows.py
from fixtures_cut15 import SNAKEFILE_SCRATCH_KEYED_FANOUT, fanout_width


def test_the_fixtures_determinism_is_pinned_not_folklore():
    assert fanout_width("base-a") == 1      # len 6, 6 % 3 == 0
    assert fanout_width("base-one") == 3    # len 8, 8 % 3 == 2
    assert fanout_width("base-a") == fanout_width("base-a")


def test_two_executions_of_one_recipe_differ_in_trace_and_job_ids(tmp_path):
    narrow = run_workflow(tmp_path / "narrow", scratch_base=tmp_path / "base-a",
                          snakefile=SNAKEFILE_SCRATCH_KEYED_FANOUT, targets=("all",),
                          declared_outputs=("outputs/a.done",),
                          family_streams={"split": (), "fit": ("model-initialization",), "all": ()},
                          checkpoint_expanded_families=("fit",), nondeterminism=seeded())
    wide = run_workflow(tmp_path / "wide", scratch_base=tmp_path / "base-one",
                        snakefile=SNAKEFILE_SCRATCH_KEYED_FANOUT, targets=("all",),
                        declared_outputs=("outputs/a.done",),
                        family_streams={"split": (), "fit": ("model-initialization",), "all": ()},
                        checkpoint_expanded_families=("fit",), nondeterminism=seeded())
    assert narrow.run.recipe.identity() == wide.run.recipe.identity()          # one recipe
    narrow_ids = {job.job_id for job in narrow.run.occurrence.trace}
    wide_ids = {job.job_id for job in wide.run.occurrence.trace}
    assert narrow_ids != wide_ids                                              # differing job ids
    assert len(narrow.run.occurrence.trace) < len(wide.run.occurrence.trace)   # differing job sets
    narrow_seeds = narrow.run.occurrence.realized_seeds.seeds
    wide_seeds = wide.run.occurrence.realized_seeds.seeds
    assert narrow_seeds != wide_seeds                                          # differing realized seeds
    assert set(narrow_seeds) < set(wide_seeds)
    assert narrow.run.address() != wide.run.address()


def test_the_scratch_mapping_is_the_receipt_s_and_not_the_recipe_s(tmp_path):
    narrow = run_workflow(tmp_path / "narrow", scratch_base=tmp_path / "base-a", snakefile=SNAKEFILE_SCRATCH_KEYED_FANOUT,
                          targets=("all",), declared_outputs=("outputs/a.done",),
                          family_streams={"split": (), "fit": (), "all": ()},
                          checkpoint_expanded_families=("fit",))
    assert "base-a" in narrow.run.occurrence.receipt.execution.scratch_mapping
    assert "base-a" not in json.dumps(narrow.run.recipe._projection())
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py -k fanout -v`
Expected: FAIL — the fixture does not exist.

- [ ] **Step 3: Write the fixture**

```python
# python/tests/fixtures_cut15.py
def fanout_width(base_name: str) -> int:
    """Deterministic in the scratch BASE name, which the test chooses. The
    Snakefile computes the same function from its own working directory."""
    return 1 + (len(base_name) % 3)


SNAKEFILE_SCRATCH_KEYED_FANOUT = """\
import os, pathlib
from beliefs.seeds import bind

seed = bind(config)

def _width(base_name):
    return 1 + (len(base_name) % 3)

checkpoint split:
    input: "inputs/data.txt"
    output: directory("splits")
    run:
        target = pathlib.Path(output[0]); target.mkdir(parents=True, exist_ok=True)
        base = pathlib.Path(os.getcwd()).parent.name
        for index in range(_width(base)):
            (target / (chr(97 + index) + ".txt")).write_text(str(index))

def parts(wildcards):
    directory = checkpoints.split.get(**wildcards).output[0]
    names = sorted(p.stem for p in pathlib.Path(directory).glob("*.txt"))
    return expand("outputs/{n}.done", n=names)

rule fit:
    input: "splits/{n}.txt"
    output: "outputs/{n}.done"
    run:
        value = seed(rule, wildcards, "model-initialization")
        pathlib.Path(output[0]).write_text(f"{wildcards.n}:{value}")

rule all:
    input: parts
"""
```

The fan-out family is **seeded**, and the Snakefile binds the helper at load
(`from beliefs.seeds import bind` / `seed = bind(config)`, as
`SNAKEFILE_WILDCARD` does). R2's negative names three differing occurrence
components — trace, job ids and **realized seeds** — and a deterministic
fixture would supply only the first two: each expanded instance has its own
job key, so a wider fan-out realizes strictly more seeds under the same
recipe.

`"base-a"` is 6 characters, so its width is `1 + (6 % 3) = 1`; `"base-one"` is
8, so its width is `1 + (8 % 3) = 3`. The test states both literally. If a
later change breaks those equalities, change the base names, never the
function — the point of the pure helper is that the fixture's determinism is
checkable without running the engine.

- [ ] **Step 4: Run the tests and watch them pass**

Run: `cd python && uv run --frozen pytest tests/test_cut15_workflows.py -k fanout -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/tests/fixtures_cut15.py python/tests/test_cut15_workflows.py
git commit -m "test(cut15): vary one recipe's job set through the scratch base"
```

---

### Task 20: R23's local basis/composition disagreement

**Files:**
- Create: `python/tests/acceptance/test_cut15_lineage.py`
- Test: the same file

**Interfaces:**
- Consumes: Tasks 12, 17; `production.mint_dataset`; `corpus.derived_from`,
  `corpus.lineage_snapshot`; `lineage.certify`, `lineage.divergence_state`;
  `stored.dataset_node`; `runrecord.run_ref`; `fixtures_cut4.reopen`; the
  `durable_root` and `durable_writer` fixtures (`tests/acceptance/conftest.py`)
  and `basis`/`route`/`slug`/`pinned` (`tests/acceptance/durable_fixture.py`).
  `run_workflow` must accept `inputs` and `held_inputs` (Task 17).
- Produces: no production code. If this task needs a source change, the design
  is wrong and the change must be raised rather than written here.

This is R23's **local basis/composition disagreement**, not its
replay-cardinality arm — that discharged at cut 3
(`test_production.py::test_r23_replay_cardinality_one_address_two_edges_nothing_mutated`)
and is not re-selected. A second dataset-production run makes the composition
and the stamped basis disagree with no fixture write anywhere.

- [ ] **Step 1: Write the arm**

The real API, every name checked against the source:

| need | the actual spelling |
|---|---|
| a certified root, and a writer on it | `durable_root`, `durable_writer` (`tests/acceptance/conftest.py:55,79`) |
| an operation port | `durable_port(root)` — takes a **root path**, from `test_operation_port` |
| the read surface | `writer.read_view` — a **property**, not a method (`corpus.py:982`); it has `get`, `resolve`, `iter_stored`, `outbound`, `inbound`, and no `nodes_of_kind` |
| a view of what the port wrote | `fixtures_cut4.reopen(root)` — `ReadView.opened_at`, a fresh facade off disk. `open_corpus` reuses the cached root state (`root.py:1640`) and would not show the port's records |
| a run's record id | `run_ref(run.address())` (`runrecord.py:55`) — lineage stores `run:<digest>`, not the bare address |
| the dataset record | `stored.dataset_node(slug, *, title, resources=(), basis=None)` (`stored.py:573`) |
| basis and route facets | `basis(*routes, tag="single")` and `route(run, ancestor, transforms=())` in `durable_fixture.py:74,78` — both take **dataset and run references**, never content digests |
| the view | `derived_from(view, dataset) -> Reach` (`corpus.py:535`); `.reached` holds the **transformed dataset refs** |
| the producer set | `lineage_snapshot(view, roots).producers[dataset]` — `Producer(stored_run, resolved_run, transforms)` |
| the stamped basis | `MintedDataset.basis` is `StampedBasis(run, transforms)` — one run, and `transforms` are **content digests** |
| the certification | `certify(snapshot, roots_a, roots_b) -> Certification(state, findings)` (`lineage.py:279`) |

Three fixture facts decide the arm:

- **One address needs constant output.** With `SNAKEFILE_PRODUCTION` the output
  depends on the input bytes, so two runs over different inputs mint two
  addresses and no disagreement exists. `SNAKEFILE_CONSTANT_PRODUCTION` writes
  constant bytes.
- **Two routes need two input datasets**, each its own `transforms` reference,
  each stored — otherwise `derived_from(...).reached` is empty and the
  composition names nothing.
- **The port writes through its own writer**, so a view taken before it is
  stale. Reopen the corpus after the runs publish.

```python
# python/tests/acceptance/test_cut15_lineage.py
import pytest
from durable_fixture import basis, pinned, route, slug
from test_operation_port import durable_port

from beliefs import stored
from beliefs.corpus import derived_from, lineage_snapshot
from beliefs.lineage import certify, divergence_state
from beliefs.production import mint_dataset
from beliefs.recipe import RecipeInput
from beliefs.runrecord import run_ref
from fixtures_cut4 import reopen
from fixtures_cut15 import SNAKEFILE_CONSTANT_PRODUCTION, run_workflow

INPUT_A = "dataset:in-a"
INPUT_B = "dataset:in-b"


def _held(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _produce(durable_root, tmp_path, *, address, name, text):
    """One production run whose single `transforms` input is `address`."""
    held = _held(tmp_path / "held", f"{name}.txt", text)
    digest = "sha256:" + __import__("hashlib").sha256(held.read_bytes()).hexdigest()
    return run_workflow(
        tmp_path / name,
        port=durable_port(durable_root),
        snakefile=SNAKEFILE_CONSTANT_PRODUCTION,
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        inputs=(RecipeInput(role="transforms", dataset=address, content=digest),),
        held_inputs={address: held},
    )


def two_producers(durable_root, durable_writer, tmp_path, *, second_input=INPUT_B):
    """Two runs, one output digest, different transforms — unless the caller
    asks for the replay case, where the second run transforms INPUT_A too."""
    for address in (INPUT_A, INPUT_B):
        durable_writer.add(stored.dataset_node(slug(address), title=slug(address), resources=pinned()))
    first = _produce(durable_root, tmp_path, address=INPUT_A, name="first", text="alpha")
    second = _produce(durable_root, tmp_path, address=second_input, name="second", text="beta")
    minted = mint_dataset(first.run, existing_bases={})
    again = mint_dataset(second.run, existing_bases={minted.address: minted.basis})
    # `open_corpus` reuses the cached root state and would not show the
    # port's records; write through the fixture's own writer and take a fresh
    # facade off disk with `fixtures_cut4.reopen`
    durable_writer.add(
        stored.dataset_node(
            slug(minted.address),
            title="produced",
            resources=[{"name": name, "digest": digest} for name, digest in first.run.result.outputs],
            # the stored route names REFERENCES; StampedBasis.transforms holds
            # content digests, and the two vocabularies are not interchangeable
            basis=basis(route(run_ref(first.run.address()), INPUT_A, [INPUT_A])),
        )
    )
    return first, second, minted, again, reopen(durable_root)


def test_two_runs_produce_one_address_by_different_routes(durable_root, durable_writer, tmp_path):
    first, second, minted, again, _view = two_producers(durable_root, durable_writer, tmp_path)
    assert first.run.recipe.identity() != second.run.recipe.identity()
    assert again.address == minted.address
    assert again.stamped is False


def test_the_composition_sees_both_producers_while_the_basis_names_the_first(durable_root, durable_writer, tmp_path):
    first, second, minted, again, view = two_producers(durable_root, durable_writer, tmp_path)
    snapshot = lineage_snapshot(view, (minted.address,))
    assert {p.stored_run for p in snapshot.producers[minted.address]} == {
        run_ref(first.run.address()), run_ref(second.run.address())
    }
    assert {r.stored_run for r in snapshot.bases[minted.address].routes} == {run_ref(first.run.address())}
    assert set(derived_from(view, minted.address).reached) == {INPUT_A, INPUT_B}  # the view sees both
    assert again.basis.run == first.run.address()


def test_independence_walks_the_basis_and_not_the_composition(durable_root, durable_writer, tmp_path):
    _first, _second, minted, _again, view = two_producers(durable_root, durable_writer, tmp_path)
    snapshot = lineage_snapshot(view, (minted.address,))
    assert divergence_state(snapshot, minted.address) == "divergent"
    verdict = certify(snapshot, (minted.address,), (INPUT_B,))
    # a build whose walk followed the COMPOSITION would reach INPUT_B through
    # the second producer and return `shared-source` with NO findings; walking
    # the basis, the second route is not ancestry at all — it is divergence
    assert verdict.state == "not-certified"
    assert verdict.findings == ("lineage-divergent",)


def test_the_replay_case_is_not_divergence_and_still_certifies(durable_root, durable_writer, tmp_path):
    # the control that makes the arm failable in both directions: same producer
    # cardinality, transforms EQUAL to the basis route, and the verdict flips
    _first, _second, minted, _again, view = two_producers(
        durable_root, durable_writer, tmp_path, second_input=INPUT_A
    )
    snapshot = lineage_snapshot(view, (minted.address,))
    assert len(snapshot.producers[minted.address]) == 2
    assert divergence_state(snapshot, minted.address) == "undiverged"
    assert certify(snapshot, (minted.address,), (INPUT_B,)).state == "independent"


def test_the_view_is_stored_nowhere_and_no_ancestry_is_authored(durable_root, durable_writer, tmp_path):
    first, _second, minted, _again, view = two_producers(durable_root, durable_writer, tmp_path)
    assert derived_from(view, minted.address).reached
    assert not [node for node in view.iter_stored()
                if node.kind == "dataset" and "derived-from" in node.facets]
    with pytest.raises(TypeError):
        mint_dataset(first.run, existing_bases={}, ancestry=("dataset:whatever",))
```

`certify`'s two verdicts are the whole arm: `not-certified` with
`lineage-divergent` when the second route disagrees with the basis, and
`independent` when it is a replay of it — the same producer set both times,
so nothing but the basis can be deciding.

- [ ] **Step 2: Run the tests**

```bash
cd python && SCIENCE_CUT4_ROOT=<a directory on the certified volume> \
    uv run --frozen pytest tests/acceptance/test_cut15_lineage.py -v
```

`SCIENCE_CUT4_ROOT` is the variable the acceptance `work_directory` fixture
reads (`tests/acceptance/conftest.py:48`) — every per-cut root hangs off it,
which is why `cut13_acceptance.py` sets `SCIENCE_CUT{4..13}_ROOT` to one
directory. Setting `SCIENCE_CUT15_ROOT` alone would leave the fixture on its
default work directory.

Expected: **PASS**, once Task 17's fixtures exist. This task is deliberately
not a red-green cycle, and saying otherwise would be a lie about what it
does: R23's clause is satisfied by machinery that already exists —
`mint_dataset` preserves an existing basis (`production.py:92`),
`derived_from` stores nothing (`corpus.py:535`), and `_closure` folds
divergence into `certify`'s findings (`lineage.py:260`). The arm's value is
that it **pins** that behaviour against a state no previous test constructed.

Before this task's fixtures exist the tests fail on the import, which is not
a red-green cycle either. Its failability is proven where failability is
actually demonstrated in this repository: Task 21's N2 sabotage, which
mutates `lineage.py`'s divergence fold and requires these checks to go red.

- [ ] **Step 3: Change no production code**

No production change should be required. If an assertion fails for a reason
other than a missing test helper, **stop and report it** — that is a design
defect, not a test to adjust.

- [ ] **Step 4: Run the whole acceptance file once more**

```bash
cd python && SCIENCE_CUT4_ROOT=<certified volume directory> \
    uv run --frozen pytest tests/acceptance/test_cut15_lineage.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add python/tests/acceptance/test_cut15_lineage.py
git commit -m "test(cut15): make the basis and the composition disagree by a second production run"
```

---

### Task 21: N2 arms and the cut-15 acceptance command

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut15.py`
- Create: `python/tests/acceptance/test_n2_cut15.py`
- Create: `python/tools/cut15_acceptance.py`
- Test: `python/tests/acceptance/test_n2_cut15.py`

**Interfaces:**
- Consumes: every prior task.
- Produces: `CUT15_ARMS`, 17 selected + 8 labeled = 25 declaration units, each
  with its row, its assertion, its source mutation and its exact named checks.

`PREFIX_RUNNERS = ("cut14_acceptance.py",)` — cut 14 froze "cuts after 14 name
`cut14_acceptance.py` and inherit the bypass", and cut 15's discharge is
serialized after cut 14's.

- [ ] **Step 1: Write `n2_arms_cut15.py`**

The harness, read from the source, is not what a first draft assumes:
`Arm(row, asserts, sabotage, checks)` has **no `selected` field**; selection
lives in the module's own tables; `audit`/`baseline` come from **`test_n2`**,
not `n2_arms`; and a `Sabotage.before` must occur **exactly once** in its
module, so quote a whole distinctive line including its indentation.

```python
# python/tests/acceptance/n2_arms_cut15.py
"""Cut 15's declared arms: 17 selected + 8 labeled = 25 units, 30 lettered arms.

Each `before` is quoted from the implementation the named task writes, and must
occur exactly once in its module."""

from n2_arms import Arm, Sabotage

_RECIPE, _ADAPTER, _BOUNDARY = "recipe.py", "adapter.py", "boundary.py"
_REPLAY, _RUNRECORD, _SEEDS = "replay.py", "runrecord.py", "seeds.py"
_VERIFY, _LINEAGE = "verify.py", "lineage.py"

_W = "test_cut15_workflows.py"
_R = "test_replay.py"
_B = "test_boundary.py"
_REC = "test_recipe.py"
_RUN = "test_runrecord.py"

CUT15_ARMS = (
    # --- R2 ---------------------------------------------------------------
    Arm(row="R2a", asserts="two executions of one recipe keep equal recipe identities and distinct addresses",
        sabotage=Sabotage(module=_RECIPE,
            before='                "occurrence": _occurrence_projection(self.occurrence),\n', after=""),
        checks=(f"{_W}::test_two_executions_of_one_recipe_differ_in_trace_and_job_ids",)),
    Arm(row="R2b", asserts="the family-stream declaration is a definition and recipe identity member",
        sabotage=Sabotage(module=_RECIPE,
            before='            "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},\n',
            after=""),
        checks=(f"{_REC}::test_changing_a_family_declaration_moves_the_recipe_identity",)),
    Arm(row="R2c", asserts="the checkpoint-expanded declaration is a definition identity member",
        # one mutation per member: deleting the checkpoint line leaves the
        # family-stream check green, so a single mixed arm would report `sound`
        # while proving only half of what it claims
        sabotage=Sabotage(module=_RECIPE,
            before='            "checkpoint_expanded_families": sorted(self.checkpoint_expanded_families),\n',
            after=""),
        checks=("test_adapter.py::test_declaring_a_checkpoint_expanded_family_moves_the_identity",)),

    # --- R16 --------------------------------------------------------------
    Arm(row="R16a", asserts="a job realizing a stream its family does not declare is non-conforming",
        sabotage=Sabotage(module=_REPLAY,
            before="        if set(claims) != declared:", after="        if False:"),
        checks=(f"{_R}::test_a_job_realizing_a_stream_its_family_does_not_declare_is_non_conforming",)),
    Arm(row="R16b", asserts="a job omitting a stream its family declares is non-conforming",
        # over-claiming still refused, omission admitted: the arm that a
        # one-directional check would miss
        sabotage=Sabotage(module=_REPLAY,
            before="        if set(claims) != declared:", after="        if set(claims) - declared:"),
        checks=(f"{_R}::test_a_job_omitting_a_stream_its_family_declares_is_non_conforming",)),
    Arm(row="R16c", asserts="two streams in one job are both keyed and both checked",
        # only the first stream of a job survives: the flat-map failure §6.2
        # describes, reintroduced
        sabotage=Sabotage(module=_REPLAY,
            before="        claims = realized.get(key, {})",
            after="        claims = dict(list(realized.get(key, {}).items())[:1])"),
        checks=(f"{_R}::test_two_streams_in_one_job_are_both_checked",)),
    Arm(row="R16d", asserts="conformance reads each job's own family, so over-claiming does not satisfy it",
        sabotage=Sabotage(module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after="        declared = {s for streams in snapshot.family_streams.values() for s in streams}"),
        checks=(f"{_R}::test_an_over_claiming_record_does_not_conform",)),
    Arm(row="R16e", asserts="a wildcard instance is judged against its family",
        sabotage=Sabotage(module=_RECIPE,
            before="        return job_key(self.rule, self.wildcards)",
            after="        return job_key(self.rule, ())"),
        checks=(f"{_R}::test_a_wildcard_instance_is_judged_against_its_family",)),
    Arm(row="R16f", asserts="the both-directions equality is refused at the boundary, before any effect",
        sabotage=Sabotage(module=_BOUNDARY,
            before="    if reason := definition_agrees_with_plan(definition.snapshot(), plan):",
            after="    if False:"),
        checks=(f"{_B}::test_a_definition_disagreeing_with_its_plan_refuses_before_any_workflow_effect",)),
    Arm(row="R16g", asserts="the same predicate states the disagreement about a constructed closure",
        sabotage=Sabotage(module=_REPLAY,
            before="    if reason := definition_agrees_with_plan(snapshot, plan):", after="    if False:"),
        checks=(f"{_R}::test_a_constructed_closure_whose_definition_disagrees_is_non_conforming",)),
    Arm(row="R16h", asserts="the family rule reads the recipe, so it binds for a production shape with no spec",
        # the plausible defect is an assessment-only reading, spelled with
        # names that exist — an undefined one would fail at import and prove
        # nothing about the property
        sabotage=Sabotage(module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after="        declared = set(snapshot.family_streams.get(job.rule, ())) if run.recipe.spec_identity else set()"),
        checks=(f"{_W}::test_the_family_rule_binds_for_a_production_recipe_with_no_spec",)),
    Arm(row="R16i", asserts="execution coverage: a declared stream no executed job realized",
        sabotage=Sabotage(module=_REPLAY,
            before="    if union != expected_streams:", after="    if union - expected_streams:"),
        checks=(f"{_W}::test_a_declared_family_producing_zero_jobs_is_non_conforming",)),
    Arm(row="R16j", asserts="trace membership, with the checkpoint-expanded admission",
        sabotage=Sabotage(module=_REPLAY,
            before="        if job.job_key() not in planned_keys and job.rule not in expanded:",
            after="        if False:"),
        checks=(f"{_R}::test_an_executed_job_outside_the_plan_is_non_conforming",
                f"{_R}::test_an_unexpanded_family_gets_no_such_admission")),
    Arm(row="R16k", asserts="target satisfaction over the resolved target job keys",
        sabotage=Sabotage(module=_REPLAY,
            before="    if missing := sorted(set(run.occurrence.target_keys) - executed):",
            after="    if False:"),
        checks=(f"{_R}::test_a_resolved_target_missing_from_the_trace_is_non_conforming",)),
    Arm(row="R16l", asserts="a legitimately different job set is conforming, and its difference is reported",
        sabotage=Sabotage(module=_VERIFY, before="    if left == right:\n        return ()\n", after="    return ()\n"),
        checks=("test_verify.py::test_a_data_dependent_replay_over_different_inputs_is_conforming",)),
    Arm(row="R16m", asserts="a job-set difference contributes to no scope",
        # scope needs its OWN mutation: emptying the diagnostics makes the
        # no-scope test fail on the diagnostic assertion before scope is
        # decided, which would prove nothing about scope
        sabotage=Sabotage(module=_REPLAY,
            before="    if original.recipe.identity() == replayed.recipe.identity():",
            after=("    if original.recipe.identity() == replayed.recipe.identity() and "
                   "{j.job_key() for j in original.occurrence.trace} == "
                   "{j.job_key() for j in replayed.occurrence.trace}:")),
        checks=("test_verify.py::test_a_differing_job_set_alone_costs_no_scope",)),

    # --- R20 --------------------------------------------------------------
    Arm(row="R20a", asserts="the obligation is per family, and no global per-job obligation is spellable",
        sabotage=Sabotage(module=_REPLAY,
            before="        declared = set(snapshot.family_streams.get(job.rule, ()))",
            after="        declared = set()"),
        checks=(f"{_R}::test_different_families_realizing_different_streams_conforms",)),
    Arm(row="R20b", asserts="two decompositions of one computation are two definitions",
        sabotage=Sabotage(module=_RECIPE, before='            "snakefile": self.snakefile_digest,\n', after=""),
        checks=(f"{_W}::test_two_decompositions_of_one_computation_are_different_definitions",)),

    # --- R21 --------------------------------------------------------------
    Arm(row="R21a", asserts="two targets over one definition are two recipes",
        sabotage=Sabotage(module=_RECIPE,
            before='                "invocation": _invocation_projection(self.invocation),\n', after=""),
        checks=(f"{_W}::test_two_targets_over_one_definition_are_two_recipes",)),
    Arm(row="R21b", asserts="the manifest is constructed across the outputs of several rules",
        # `build_manifest` is a comprehension, not a loop, and no task in this
        # plan rewrites it — the anchor is the line that is actually there
        sabotage=Sabotage(module=_BOUNDARY,
            before="    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) for name in declared_outputs))",
            after="    return ResultManifest(outputs=tuple((name, _digest(_output_path(scratch, name))) for name in declared_outputs[:1]))"),
        checks=(f"{_W}::test_a_manifest_is_built_across_the_outputs_of_several_rules",)),
    Arm(row="R21c", asserts="`invocation` enumerates no jobs a target implies",
        sabotage=Sabotage(module=_RECIPE,
            before="    declared_outputs: tuple[str, ...]\n",
            after="    declared_outputs: tuple[str, ...]\n    jobs: tuple[str, ...] = ()\n"),
        checks=(f"{_W}::test_the_invocation_does_not_enumerate_the_jobs_a_target_implies",)),

    # --- R23 --------------------------------------------------------------
    Arm(row="R23", asserts="independence walks the stamped basis, not the composition",
        sabotage=Sabotage(module=_LINEAGE,
            before='        if divergence_state(snapshot, dataset) == "divergent":', after="        if False:"),
        checks=("acceptance/test_cut15_lineage.py::test_independence_walks_the_basis_and_not_the_composition",)),

    # --- labeled ----------------------------------------------------------
    Arm(row="K1", asserts="every cross-pair of the run-domain matrix is malformed",
        sabotage=Sabotage(module=_RECIPE, before="    if recipe_v2 != composed:", after="    if False:"),
        checks=(f"{_RUN}::test_every_cross_pair_is_malformed",)),
    Arm(row="K2", asserts="the recipe's shape is read from its own key, never inferred from the receipt",
        # shares K1's check deliberately: inference is observable only on a
        # cross-pair, and the two arms prove two independent mechanisms — K1
        # that the pairing is checked at all, K2 that the shapes are read
        # separately. `composed` is bound first (Task 5) so this mutation runs
        sabotage=Sabotage(module=_RECIPE,
            before='    recipe_v2 = "workflow_definition" in recipe', after="    recipe_v2 = composed"),
        checks=(f"{_RUN}::test_every_cross_pair_is_malformed",
                f"{_RUN}::test_the_recipe_shape_is_read_from_its_own_key_never_inferred_from_the_receipt")),
    Arm(row="K3", asserts="a v1 recipe is refused rather than given an invented declaration",
        # the GUARD, not the raise: deleting a `raise X(` line orphans its
        # arguments and the module stops importing, which proves nothing
        sabotage=Sabotage(module=_RUNRECORD,
            before='    if "workflow_definition_identity" in recipe:', after="    if False:"),
        checks=(f"{_RUN}::test_a_v1_identity_only_recipe_is_refused_rather_than_given_an_invented_declaration",)),
    Arm(row="K4", asserts="the job key is canonical text, so no wildcard value can collide",
        sabotage=Sabotage(module=_RECIPE,
            before='    return v1.encode({"rule": rule, "wildcards": {name: value for name, value in wildcards}}).decode("utf-8")',
            after='    return rule + "|" + ",".join(f"{name}={value}" for name, value in wildcards)'),
        checks=(f"{_REC}::test_a_wildcard_value_containing_a_separator_cannot_collide",)),
    Arm(row="K5", asserts="a repeated (job, stream) claim fails inside the job",
        sabotage=Sabotage(module=_SEEDS,
            before="            handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)",
            after="            handle = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)"),
        checks=("test_seeds.py::test_a_repeated_claim_fails_inside_the_job_rather_than_overwriting",)),
    Arm(row="K6", asserts="seed roots are parsed explicitly, whatever the engine coerced them to",
        sabotage=Sabotage(module=_SEEDS,
            before='        if not text.lstrip("-").isdigit():', after="        if False:"),
        checks=("test_seeds.py::test_a_non_integral_root_is_refused_rather_than_coerced",)),
    Arm(row="K7", asserts="the planning launch touches no execution scratch",
        sabotage=Sabotage(module=_BOUNDARY,
            before='    planning_dir = Path(tempfile.mkdtemp(prefix="planning-", dir=scratch_base))',
            after="    planning_dir = scratch"),
        checks=(f"{_B}::test_the_planning_launch_writes_nothing_into_the_execution_scratch",)),
    Arm(row="K8", asserts="qualification reads the execution launch's evidence, never the planning launch's",
        # the containment check is where the two launches actually differ in
        # the fixture; flipping only the `instance is None` guard changes
        # nothing when both launches are confined
        sabotage=Sabotage(module=_REPLAY,
            before="    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.execution.capabilities):",
            after="    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.planning.capabilities):"),
        checks=("test_confinement_values.py::test_qualification_reads_the_execution_launch_and_not_the_planning_one",)),
)

_UNIT_OF_LETTERED = {
    "R2a": "R2", "R2b": "R2", "R2c": "R2",
    **{f"R16{letter}": "R16" for letter in "abcdefghijklm"},
    "R20a": "R20", "R20b": "R20",
    "R21a": "R21", "R21b": "R21", "R21c": "R21",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"R2": 2, "R16": 10, "R20": 2, "R21": 2, "R23": 1}
LABELED_UNITS: tuple[str, ...] = tuple(f"K{number}" for number in range(1, 9))

#: No cut-15 arm cites a prior cut's check.
CO_CITED: dict[str, tuple[str, ...]] = {}
```

**Thirty arms carry seventeen units** — R2 3, R16 13, R20 2, R21 3, R23 1,
K 8 — which is the normal shape: a unit needs a second arm whenever one
mutation cannot falsify both halves of its claim. R16's ten units take
thirteen arms for that reason, and R2's two take three. `ROW_UNITS` states the
inventory; the arm count is whatever it takes to make every claim failable,
and the count assertion below keeps the two from drifting apart.

Three of these were vacuous in an earlier draft, and the reasons are worth
keeping: an `or dict.fromkeys(...)` fallback leaves a truthy partial claim
untouched, so the omission still refuses; a seed-value mutation is unreachable
behind the `set(claims) != declared` return; and flipping only `instance is
None` changes nothing when both launches are confined, because capabilities
and environment identity are still read from `execution`.

- [ ] **Step 2: Write the audit test and run it**

```python
# python/tests/acceptance/test_n2_cut15.py
import pytest
from n2_arms_cut15 import CUT15_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

SELECTED_UNITS = {"R2": 2, "R16": 10, "R20": 2, "R21": 2, "R23": 1}


def test_the_inventory_is_seventeen_selected_and_eight_labeled():
    assert ROW_UNITS == SELECTED_UNITS
    assert sum(ROW_UNITS.values()) == 17
    assert len(LABELED_UNITS) == 8


def test_the_arm_rows_are_unique_and_counted():
    # the arm count drifts every time a mixed arm is split; assert it, so a
    # split that forgets the docstring fails here rather than in review
    rows = [arm.row for arm in CUT15_ARMS]
    assert len(rows) == len(set(rows)) == 30


def test_every_declared_unit_is_carried_by_at_least_one_arm():
    carried = {unit_of(arm.row) for arm in CUT15_ARMS}
    assert set(ROW_UNITS) | set(LABELED_UNITS) <= carried


@pytest.mark.parametrize("arm", CUT15_ARMS, ids=lambda arm: arm.row)
def test_each_arm_passes_unsabotaged_and_fails_under_its_sabotage(arm, tmp_path):
    # the two directions have DIFFERENT verdict vocabularies: baseline reports
    # "resolved" when every check passes against the real package
    # (test_n2.py:195), audit reports "sound" when every check fails under the
    # sabotage (test_n2.py:236)
    assert baseline(arm).verdict == "resolved"
    assert audit(arm, tmp_path).verdict == "sound"
```

Cut 15's frozen authority is
`docs/superpowers/specs/2026-09-01-workflow-surface-design.md`, frozen at
commit **`e2f9d71`** — not a `docs/designs/2026-09-01-conformance-cut-15.md`,
which does not exist and is not created before banking. Pin that path and
that commit literally, as `test_n2_cut13.py` pins `FROZEN_CUT` and
`CUT13_FREEZE_COMMIT`, and pin prior cuts' declaration files by digest the
same way.

Run: `cd python && SCIENCE_CUT4_ROOT=<certified volume directory> uv run --frozen pytest tests/acceptance/test_n2_cut15.py -v`
Expected: every arm reports `resolved` then `sound`. An arm whose `before`
matches zero or two places is reported rather than tolerated — fix the quote,
never the harness.

- [ ] **Step 3: Write the runner**

`python/tools/cut15_acceptance.py`, on `cut13_acceptance.py`'s shape — two
constants plus the environment propagation, which is what actually makes the
roots resolve:

```python
PREFIX_RUNNERS = ("cut14_acceptance.py",)
PHASE_MODULES = ("test_cut15_lineage.py", "test_confinement_acceptance.py", "test_n2_cut15.py")


def cut_environment(run: Path) -> dict[str, str]:
    # every acceptance fixture hangs off the work directory the conftest reads
    # from SCIENCE_CUT4_ROOT, and each prior cut's modules read their own
    # variable — cut 13 sets range(4, 14); cut 15 extends it
    return {**os.environ, **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 16)}}
```

The prefix invocation passes `env={**os.environ, "SCIENCE_CUT14_ROOT": str(run)}`,
exactly as `cut13_acceptance.py:97` passes `SCIENCE_CUT12_ROOT`, and every
phase module runs under `cut_environment(run)`.

It probes **both** prerequisites before running anything and errors off either,
never skipping: the confinement gate (`bwrap` with `--info-fd`, user
namespaces, `ld.so --list`) for the confined arms, and the certified durable
work root — read from `SCIENCE_CUT15_ROOT`, defaulting as cut 13 does — for
the prefix and for Task 20's lineage arms.

- [ ] **Step 4: Run the whole cut**

Run: `cd python && uv run --frozen python tools/cut15_acceptance.py`
Expected: every phase passes, prefix first.

- [ ] **Step 5: Commit**

```bash
git add python/tests/acceptance/n2_arms_cut15.py python/tests/acceptance/test_n2_cut15.py python/tools/cut15_acceptance.py
git commit -m "test(n2): declare cut 15's arms and its acceptance command"
```

---

### Task 22: Bank the slice — results record, ledger, roadmap, guide

**Files:**
- Create: `docs/plans/2026-09-01-conformance-cut-15-results.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md`
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md`
- Modify: `docs/superpowers/specs/2026-09-01-workflow-surface-design.md` (status header)
- Modify: the guide pages describing the boundary as rendering single invocations
- Test: `python/tests/test_designs_corpus.py`, `python/tests/test_check_guide.py`

**Interfaces:**
- Consumes: Task 21's discharge.
- Produces: the banked slice. Nothing consumes it.

- [ ] **Step 1: Write the results record**

On `2026-09-01-conformance-cut-13-results.md`'s shape: the selection as
discharged, the unit inventory (17 + 8 = 25), the commit table, the host and
volume tuple, the prefix chain naming `cut14_acceptance.py`, and §5's
remaining boundary. State which cut was newest-discharged when cut 15 ran.

- [ ] **Step 2: Correct the ledger and the roadmap**

The ledger's `Current state` table drops the `workflow-surface` row and gains
a summary bullet. In **both** the ledger and the roadmap, the R23 assignment
is **reworded, not reassigned**: `workflow-surface` carries *R23's local
basis/composition disagreement (cut 5 §3.2)*, never "the second
dataset-production run", in the ledger's boundary row, the roadmap's boundary
index, its tier-1 table and its Appendix B R23 row. Do not restate the
discharged replay-cardinality arm as open anywhere, Appendix A included.

Add roadmap concurrency rule 5: *a cut names the acceptance runner of the
highest-numbered cut, and a cut frozen while a lower-numbered cut is
undischarged serializes its discharge after that cut's.*

Re-rank the roadmap whole, at cut 15, per its own header.

- [ ] **Step 3: Apply the dated amendments to the banked designs**

Design §13 owes four, and they land here, each dated and in the banked
document itself:

1. **Computation §6.2's "no prior enumeration exists" ruling is narrowed** —
   a planning enumeration now exists for every non-checkpoint job, and
   job-set conformance reads it; checkpoint-expanded jobs stay unenumerable
   and are admitted by declaration. Leave the surrounding rule — that job-set
   differences between two runs contribute to no verdict — untouched.
2. **R16's definition/plan check gains a second disposition** — the oracle's
   "refused" stays primary at the boundary, and the same predicate is
   additionally statable about a constructed or decoded closure. Record it as
   a widening, not a substitution.
3. **The record shapes and the decode matrix** — the workflow-definition,
   recipe, receipt and run domains of design §3.5, with every cross-pair
   malformed and v1/v2 records decoding untranslated.
4. **Run confinement's receipt** becomes two composed launch attestations,
   with `qualifies()` reading `execution`; its §6.3 contents are preserved
   per launch and its `from-bundle` derivation is unchanged.

Amendments 5 and 6 of §13 are accounting statements, not text changes: no
amendment to R23, and none to cut 14.

- [ ] **Step 4: Correct the guide and the design's status header**

Grep the guide for the boundary "rendering single invocations" and for
single-rule claims; correct them in this change, since this is the change that
makes them stale. Update the design's status header from "designed" to
implemented and discharged, naming the results record and the discharge
commit.

- [ ] **Step 5: Run every gate**

```bash
cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright
cd ../ts && npm ci && npm test && npm run typecheck && npm run check
cd .. && tasks check
```
Expected: all green, `tasks check` zero errors and zero warnings.

- [ ] **Step 6: Commit and close the task**

```bash
# close this task first: the parent depends on it, and `tasks done` on a task
# with an open dependency is what --force exists to override — don't
tasks done beliefs-a8b85e "Banked the slice: cut 15 results record, ledger, roadmap and guide"
tasks done beliefs-73be28 "Workflow surface delivered; cut 15 discharged at 17 selected + 8 labeled units"
tasks check
git add docs python/tests tasks   # stage AFTER both CLI mutations, so their file writes are included
git commit -m "docs: bank the workflow surface, discharge cut 15, and re-rank the roadmap"
```

Then merge the lane with `--no-ff`, as every prior integration has.
