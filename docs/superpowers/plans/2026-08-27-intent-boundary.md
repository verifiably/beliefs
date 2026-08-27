# General Intent Qualification (World-Index Slice 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** Draft — awaiting the human partner's review before execution
(spec §8 step 4 begins only after this plan is approved).
**Revised 2026-08-27**, closing the plan review's six findings: executable
assertions replace comment-body tests (Tasks 3, 4, 9, 10, 12); the
projection view mirrors the built closure invariants exactly — type-only
string checks where the constructors check type only, the constructor
constraints the first draft omitted, exact facet shapes — and the codec
tests construct real mutations (Task 2); evidence decoding binds
path↔kind↔id and reuses the tree's full validators (Task 8, extraction
in Task 8a); the reducer consults only file-state final rows through the
seam's `state_facts` (Tasks 9, 10); the decode gate lets the holdings
dialect own holdings parsing so the built boundary's `ensure_ascii`
payloads stay decodable, with a Unicode arm (Task 6); and Task 13 carries
the concrete arm/citation partition with a named sabotage per check and
explicit citation accounting for L7u5. The `OperationPort` protocol is
single-homed in `science/runrecord.py` (Task 2), re-exported by
`corpus.py`, and every structural fake gains `execute` (Task 3).
**Revised again 2026-08-27** (second plan review, seven blockers):
`replay()` and `replay_of` thread the required port with their callers
listed and committed (Task 4); every durable builder registers its root
explicitly (`init_corpus_root`/`init_store_root` — unregistered roots
refuse every write); Task 13's partition is restated in the harness's
own `Arm`/`Sabotage` shape — exact once-matching before/after strings,
exact node ids, one sabotage per arm with J3/J8/J9/J12 split into
lettered arms, L7u5 as a citation with explicit accounting, and the
non-port regression as a co-passing independence node under J3a; J2's
sabotage is a single fail-fast mutation (`O_RDONLY | O_NONBLOCK`, no
blocking open); label 8 gains the durable
publish→capture→decode→recompute arm and the relation test pins both
shapes' `reads` edges; the literal code is pyright-clean (typed
`DecodedIntent.value` union with isinstance narrowing, `NoReturn`
imported, validator-established casts, exclusion members non-empty);
the findings-order test constructs a guaranteed non-qualification
finding and pins the exact outcome, Task 11's vocabulary test is
executable, and the Task 3/4/8 commit lists name every modified file.
**Revised a third time 2026-08-27** (third plan review, seven
blockers): the entrypoints gain the `conformance` gate so replay's
recipe check runs before the terminal publication — the durable record
always states the returned result, with a durable test; Task 13's
harness additions and every durable acceptance arm are supplied as
code, with the lettered-arm-to-unit normalization asserted by the
harness; L7u2 splits into four member arms with their own sabotages,
J2's sabotage is one by-name `O_RDONLY | O_NONBLOCK` open (the /proc
reopen of a symlink's `O_PATH` fd is `ELOOP`, so mutating the reopen
alone leaves the symlink arms green), and J5's evaluator check holds
genuinely matching bytes; L7u8's port raises a cancellation before
writing, honoring the port contract; Task 10's calls follow the
wrapper's real positional convention with `verify.PresentedManifest`;
the gate tests narrow through `decoded`/`unrecognized` helpers, the
validator returns typed lists and a cast token; and
`tests/closure_fixtures.py` (Task 2) homes the shared
`make_closure`/`sample_report` builders while
`_REPORT_ENTRY_OUTCOMES` moves with the extracted act-report
validator.
**Revised a fourth time 2026-08-27** (fourth plan review): the replay
gate narrows to the frozen `expected_recipe_identity: str | None`
value — one comparison, no caller-supplied code inside the boundary —
recorded as the spec's twenty-first amendment (§2.6 item 6) before any
implementation; J10 ships and sabotages the actual bridge
(`runrecord.run_ref`/`bare_address`, the one spelling authority the
encoder's record id also mints through), with the arm resolving a raw
`StampedBasis.run` and a stored assessment `run` field; the u5 race
uses futures whose `result()` propagates append failures, asserting
exactly two digests and two intent entries; the partition test asserts
the frozen unit identities (`L7u1…L7u13` ∪ `J1…J13`), never counts;
and the speculative `sample_report` and `CreateOp` contingency notes
are removed.

**Goal:** Land the general qualification reduction over the closed
three-shape intent union, the verifier's `qualification` report contract,
the captured-record evidence input, the run boundary's persistence
contract with the closure-to-stored codec, the regenerated holdings
interior, and the `science.report.completion` re-base — then discharge
conformance cut 11's 26 frozen declaration units.

**Architecture:** A new `science/intents/` package holds the one
precedence reducer, the total decode gate, the evidence projection, and
the shared pure holdings shape (the dialect source the rules-store
concatenation consumes). A new `science/runrecord.py` owns the
closure-to-stored codec: `run:<RunClosure.address()>` identity, the
`run-closure` facet carrying the projection as v1-canonical text, the
typed projection view with canonical reprojection equality, and the
`WritePlan` the port executes. `science/world/records.py` owns the
fd-anchored, classified, bounded record capture and `RECORD_CEILING`.
The verifier (`science/world/verify.py`) lifts `intents_unevaluated`
into `LogReport.qualification`; `science/root.py` (the one atoms
importer) gains the port's non-fulfilling `execute` and the writer-side
ceiling; `science/boundary.py` gains the required destination port and
the append–act–publish sequence.

**Tech Stack:** Python 3 (`uv run --frozen`, cwd `python/`), pytest, the
certified `atoms` engine at remote `main` `038513f` (no atoms change
ships with this slice), the N2 declaration harness
(`tests/acceptance/n2_arms_cut10.py` + `tests/acceptance/test_n2_cut10.py`
are the pattern), `tools/cutN_acceptance.py` runners.

**Spec:** `docs/superpowers/specs/2026-08-26-world-index-intent-boundary-design.md`
(promoted to `docs/designs/` by the banking task).
**Frozen cut:** `docs/designs/2026-08-27-conformance-cut-11.md` (frozen at
`9711886`; its §3 declarations are the acceptance criteria — read the
spec and the cut before any task).
**Inherited authority:** log design §6 as amended (the precedence),
`2026-08-11-act-report-design.md` §3 (operation intent, T2),
`2026-08-24-world-index-holdings-design.md` §4.3 (the interior this
slice replaces).

## Global Constraints

- The frozen cut is never edited except its status header at discharge.
  The spec is edited only by a dated amendment (a mid-task gap upgrade,
  spec §8's closing rule) or by the banking task (Task 14).
- **G4 and the successor-admission boundary are out of scope.** Spec §5
  is transferred authority for a future slice; no task here implements
  `admit_spec_successor`, the two-class blocker, or any admission read.
- No `atoms` change. `science/root.py` stays the **only** module
  importing `atoms`, enforced by `python/tests/test_capability_boundary.py`.
- Frozen names, verbatim: `RECORD_CEILING = 8 * 1024 * 1024` (2^23);
  facet key `run-closure`, inner field `projection`; identity domain
  `science.run.v1`; `SHAPES = ("assessment", "dataset-production")`;
  `OPERATION_KINDS` closed as built, the production run's wire kind is
  exactly `run-attempt`; finding codes
  `intent-attempt-without-recorded-outcome`,
  `intent-fulfillment-non-qualifying`, `intent-domain-unrecognized`,
  `intent-payload-malformed`; reason classes `wrong-purpose`,
  `wrong-spec`, `wrong-token`, `wrong-kind`, `wrong-shape`,
  `wrong-location`, `no-record`.
- Qualification is report-field status, **never** the chain verdict: no
  task changes `outcome`, and no outcome suppresses qualification's
  findings.
- No compatibility alias: `intents_unevaluated` retires, and every
  caller and test naming it updates in the same task (Task 10).
- The rules-store dialect constraints hold for
  `science/intents/holdings.py` and the regenerated
  `science/holdings/qualify.py`: pure source, exactly one top-level
  import (`json`), no science imports.
- `python/tools/cut8_acceptance.py`, `cut9_acceptance.py`, and
  `cut10_acceptance.py` stay exit 0. Run them on the certified volume
  before claiming done any task that touched `science/root.py`,
  `science/world/verify.py`, `science/world/logmodel.py`,
  `science/corpus.py`, `science/report.py`, or `science/holdings/`;
  for tasks touching only new files the full-suite gate suffices.
- Durable arms live on the repository's own volume — never `/tmp`, the
  scratch volume, or `/dev/shm`. Reuse the `certified_work` fixture
  (`python/tests/conftest.py`) for unit-level durable tests and
  `tests/acceptance/durable_fixture.py` for acceptance arms.
- Every count claim quotes pytest's own summary line under `pipefail` —
  never a collect-only count (addopts already sets `-q`; do not double
  it, and never `| tail` without `set -o pipefail`).
- The Science gate block, run from `python/` after every green step
  (addopts supplies `-q` and `--ignore=tests/acceptance`; acceptance
  files run only by explicit node id):
  `uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`
- The three corpus-guard tests
  (`test_the_readme_lists_every_design_document`,
  `test_the_readme_states_how_many_designs_there_are`,
  `test_the_guide_cites_every_design`) are green at the branch head and
  stay green through every task: Task 14 promotes the spec **and**
  updates README, guide, and `_COUNT_WORDS` in the same commit, so no
  commit boundary is red. "Full suite green" means literally green
  throughout.
- Conventional commits; no AI-attribution trailers. After every task:
  append the execution ledger
  (`docs/plans/2026-08-27-intent-boundary-ledger.md` — rulings + the
  task's head commit) and commit it with the task.
- TDD throughout: every new behavior gets a failing test first, watched
  to fail for the right reason. Where a cohesive green step makes a
  later declared test pass on first run, record it in the ledger as a
  contract pin, not silently.
- No clock enters any derivation; tests assert timestamp **form**,
  never value. `Decimal` values on the wire keep their mandatory
  fractional part; binary floats are refused everywhere.

---

### Task 0: Tracking setup — the execution ledger

**Files:**
- Create: `docs/plans/2026-08-27-intent-boundary-ledger.md`
- Modify: `.gitignore` (append `.cut11-acceptance/`)
- Modify: `docs/superpowers/plans/2026-08-27-intent-boundary.md` (Status
  → approved, once the human partner approves)

**Interfaces:**
- Produces: the tracked ledger every later task appends to. Slice 2
  lost R1–R15 to an untracked path; never relocate it.

- [ ] **Step 1: Write the ledger skeleton**

```markdown
# Intent-boundary slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-27-intent-boundary.md`
Specification: `docs/superpowers/specs/2026-08-26-world-index-intent-boundary-design.md`
Frozen cut: `docs/designs/2026-08-27-conformance-cut-11.md`
Freeze hash: `9711886`

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the certified engine is standing authority.** Atoms remote
   `main` `038513f` is the binding engine contract (cut 11 §2: no atoms
   change ships with this slice); no task edits atoms.

## Heads

| Task | Science head |
|---|---|

(Appended at every task boundary.)
```

- [ ] **Step 2: Append `.cut11-acceptance/` to `.gitignore`**

- [ ] **Step 3: Record the plan's approval** — edit this plan's
  **Status** line to name the approval (the reviewer's message and the
  reviewed commit).

- [ ] **Step 4: Commit**

```bash
git add docs/plans/2026-08-27-intent-boundary-ledger.md .gitignore \
        docs/superpowers/plans/2026-08-27-intent-boundary.md
git commit -m "docs(plans): open the intent-boundary execution ledger"
```

---

### Task 1: `v1.decode` and `CanonicalTextRefused`

**Files:**
- Modify: `python/src/science/errors.py` (beside the `IdentityError`
  family, `errors.py:408`)
- Modify: `python/src/science/identity/v1.py` (`__all__` at line 45)
- Test: `python/tests/test_identity_decode.py` (new)

**Interfaces:**
- Produces: `science.identity.v1.decode(data: bytes) -> object` —
  parse rules: UTF-8 decode, `json.loads` with `parse_int=int`,
  `parse_float=Decimal`, `parse_constant` refusing; validity is
  canonical re-encoding equality (`v1.encode(parsed) == data`). Every
  failure raises `CanonicalTextRefused` (an `IdentityError` subclass in
  `science.errors`), wrapping any re-encoding `IdentityError` with the
  cause preserved and the failure class named in the message. Never
  returns a partial or coerced value.
- Produces: `science.errors.CanonicalTextRefused`.

- [ ] **Step 1: Write the failing tests**

```python
"""`v1.decode` — the exported inverse of the canonical codec (spec §2.6 item 5)."""

from decimal import Decimal

import pytest

from science.errors import CanonicalTextRefused, IdentityError
from science.identity import v1


def test_decode_round_trips_a_canonical_object() -> None:
    value = {"a": 1, "b": Decimal("0.5"), "c": ["x", True]}
    data = v1.encode(value)
    parsed = v1.decode(data)
    assert parsed == value
    assert v1.encode(parsed) == data


def test_decode_preserves_types_int_and_decimal_are_distinct() -> None:
    assert v1.decode(b"1") == 1 and type(v1.decode(b"1")) is int
    assert v1.decode(b"1.0") == Decimal("1.0") and type(v1.decode(b"1.0")) is Decimal
    assert v1.decode(b'"0.5"') == "0.5"
    assert v1.decode(b"0.5") == Decimal("0.5")


def test_decode_refuses_the_constants() -> None:
    for payload in (b"NaN", b"Infinity", b"-Infinity", b"[NaN]"):
        with pytest.raises(CanonicalTextRefused):
            v1.decode(payload)


def test_decode_refuses_malformed_utf8_and_malformed_json() -> None:
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"\xff\xfe")
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"{not json")


def test_decode_refuses_non_canonical_ordering_and_duplicate_keys() -> None:
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b'{"b":1,"a":2}')  # canonical order is a first
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b'{"a":1,"a":2}')  # collapsed duplicate re-encodes shorter


def test_decode_wraps_reencoding_identity_errors_cause_preserved() -> None:
    with pytest.raises(CanonicalTextRefused) as caught:
        v1.decode(b"null")  # NullRefused inside encode
    assert isinstance(caught.value, IdentityError)
    assert isinstance(caught.value.__cause__, IdentityError)
    assert "NullRefused" in str(caught.value)


def test_decode_refuses_a_float_producing_spelling() -> None:
    # 1e2 parses as Decimal under parse_float and re-encodes as "100" != b"1e2".
    with pytest.raises(CanonicalTextRefused):
        v1.decode(b"1e2")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run --frozen pytest tests/test_identity_decode.py -x`
Expected: FAIL — `ImportError: cannot import name 'CanonicalTextRefused'`.

- [ ] **Step 3: Implement**

In `errors.py`, directly after `MalformedDomain` (line 446):

```python
class CanonicalTextRefused(IdentityError):
    """Bytes presented as v1-canonical text are not: malformed UTF-8 or
    JSON, a refused constant, a re-encoding refusal (wrapped, cause
    preserved), or re-encoded bytes that differ from the input."""
```

In `identity/v1.py`: `__all__ = ["check_domain", "decode", "digest", "encode"]`,
add `import json` and `from science.errors import CanonicalTextRefused`
(extend the existing import), and:

```python
def _refuse_constant(token: str) -> object:
    raise CanonicalTextRefused(f"refused constant {token!r}: NaN and Infinity never parse")


def decode(data: bytes) -> object:
    """The exported inverse: parse canonical bytes back to the typed value.

    Validity is canonical re-encoding equality — `encode(parsed)` must equal
    `data` byte-for-byte — which also refuses non-canonical ordering and
    collapsed duplicate keys. Every failure is `CanonicalTextRefused`; a
    re-encoding `IdentityError` is wrapped with its cause preserved."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as caught:
        raise CanonicalTextRefused(f"malformed UTF-8: {caught}") from caught
    try:
        parsed: object = json.loads(
            text, parse_int=int, parse_float=Decimal, parse_constant=_refuse_constant
        )
    except CanonicalTextRefused:
        raise
    except ValueError as caught:
        raise CanonicalTextRefused(f"malformed JSON: {caught}") from caught
    try:
        reencoded = encode(parsed)
    except CanonicalTextRefused:
        raise
    except IdentityError as caught:
        raise CanonicalTextRefused(
            f"re-encoding refused ({type(caught).__name__}): {caught}"
        ) from caught
    if reencoded != data:
        raise CanonicalTextRefused("bytes are not canonical: re-encoding differs from the input")
    return parsed
```

- [ ] **Step 4: Run to verify pass, then the gate block**

Run: `uv run --frozen pytest tests/test_identity_decode.py tests/test_identity_v1.py`
then the gate block. Expected: PASS.

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/errors.py python/src/science/identity/v1.py \
        python/tests/test_identity_decode.py docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(identity): export v1.decode with CanonicalTextRefused"
```

---

### Task 2: The run publication codec (`science/runrecord.py`)

**Files:**
- Create: `python/src/science/runrecord.py`
- Create: `python/tests/closure_fixtures.py` — the shared plain-module
  builders every later test file imports (fixtures in one test module
  are invisible to another; a helper module is not):

  ```python
  """Shared closure and report builders for the intent-boundary tests."""

  from decimal import Decimal
  from pathlib import PurePosixPath  # noqa: F401 — builders below

  from science.recipe import (
      BoundaryPolicy, BoundaryReceipt, EnvironmentManifest, Invocation,
      Occurrence, Recipe, RecipeInput, ResultManifest, RunClosure,
  )
  from science.report import ActReport, Entry, RunAttemptEntry, RunRefusal, _mint_report
  from science.spec import Deterministic, RealizedSeeds


  def make_closure(*, shape: str = "assessment", parameters=None,
                   spec: str | None = "s" * 64, token: str = "tok") -> RunClosure:
      """One closure per call: two declared outputs (so pair reversal is a
      real mutation), a `reads` input beside the shape's eligible role, a
      Decimal parameter unless overridden — mirror tests/test_closure.py's
      member values for the receipt/occurrence details."""
      eligible = "observes" if shape == "assessment" else "transforms"
      inputs = (
          RecipeInput(role=eligible, dataset="dataset:" + "1" * 64, content="sha256:" + "2" * 64),
          RecipeInput(role="reads", dataset="dataset:" + "3" * 64, content="sha256:" + "4" * 64),
      )
      recipe = Recipe(
          shape=shape,
          spec_identity=spec if shape == "assessment" else None,
          code_identity="sha256:" + "5" * 64,
          environment=EnvironmentManifest(artifacts=(("python", "sha256:" + "6" * 64),)),
          workflow_definition_identity="sha256:" + "7" * 64,
          invocation=Invocation(entrypoint="code/workflow/Snakefile",
                                targets=("out-a", "out-b"), bindings=("inputs",),
                                declared_outputs=("out-a", "out-b")),
          inputs=inputs,
          parameters=parameters if parameters is not None else {"threshold": Decimal("0.5")},
          nondeterminism=Deterministic(),
          boundary_policy=BoundaryPolicy(identity="boundary-policy/minimal-v1",
                                         scope_rule="scope-derivation/v1"),
          rule_bindings=(("rule:eq", "impl-1"),),
      )
      result = ResultManifest(outputs=(("out-a", "sha256:" + "8" * 64), ("out-b", "sha256:" + "9" * 64)))
      occurrence = Occurrence(
          event_token=token, started_at="2026-08-27T00:00:00Z", actor="tester",
          host_realization="host-a", trace=(), realized_seeds=RealizedSeeds({}),
          receipt=BoundaryReceipt(scratch_mapping="/scratch", argv=("snakemake",),
                                  rendered_config=(("threshold", "0.5"),)),
      )
      return RunClosure(recipe=recipe, result=result, occurrence=occurrence)


  def sample_report(*, operation: str = "run-attempt", token: str = "tok") -> ActReport:
      entries: tuple[Entry, ...] = (RunAttemptEntry("subject", RunRefusal("execution-failed")),)
      return _mint_report(operation=operation, event_token=token, actor="tester",
                          observer="observer-1", instrument="science.boundary/v1",
                          opened_at="2026-08-27T00:00:00Z", closed_at="2026-08-27T00:00:00Z",
                          entries=entries)
  ```

- Modify: `python/src/science/stored.py` — `RUN_CLOSURE_FACET` constant,
  `COVERED_FACETS["run"]` gains it (line 187), new constructor
  `run_publication_node` beside `run_node` (line 492); `run_node` itself
  unchanged.
- Test: `python/tests/test_runrecord.py` (new; its `assessment_closure`
  / `production_closure` / `make_closure` fixtures are thin pytest
  wrappers over `closure_fixtures.make_closure`)

**Interfaces:**
- Consumes: `RunClosure.address()` (`recipe.py:495`),
  `Recipe._projection()`, `recipe._occurrence_projection`,
  `recipe._pairs`, `v1.decode`/`v1.encode`/`v1.digest`,
  `stored.stamp_semantic_identity` via `stored._node`.
- Produces (later tasks rely on these exact names):
  - `stored.RUN_CLOSURE_FACET = "run-closure"`
  - `stored.run_publication_node(slug, *, title, projection, spec,
    observes=(), reads=(), transforms=(), produces=()) -> Node` —
    facets `{"run": {"spec": spec} | {}, "run-closure": {"projection": projection}}`,
    role-preserving relations.
  - `runrecord.projection_text(closure: RunClosure) -> bytes` — the
    v1-canonical bytes of the `{recipe, result, occurrence}` mapping
    `RunClosure.address()` digests.
  - `runrecord.RunPublication` — frozen dataclass
    `(address: str, shape: str, spec_identity: str | None, event_token: str)`.
  - `runrecord.decode_projection(data: bytes) -> dict[str, object]` —
    `v1.decode`, then the typed projection view (exact schema at every
    depth), then canonical reprojection equality; raises
    `CanonicalTextRefused` or `MalformedRecord`.
  - `runrecord.decode_run_record(node: Node) -> RunPublication | None` —
    `None` for a legacy record (no `run-closure` facet: readable, never
    qualifying); raises `MalformedRecord`/`CanonicalTextRefused` when
    the bytes are not the named publication (schema, reprojection,
    address mismatch, `run`-facet shape disagreement either way).
  - `runrecord.publication_plan(closure, *, produces: str | None) ->
    tuple[str, str, tuple[CreateOp, ...]]` — `(record_id, path, plan)`,
    id `run:<address>` minted through `run_ref`, path
    `run/<address>.md`, one `CreateOp` of the markdown bytes;
    `produces` required exactly for shape `dataset-production`.
  - `runrecord.run_ref(address: str) -> str` and
    `runrecord.bare_address(ref: str) -> str` — the frozen
    bare-address/typed-ref bridge, one implementation for every
    consumer (label 10's arm resolves a raw `StampedBasis.run` through
    it).
  - `runrecord.OperationPort` — the protocol's **single home**:
    `append_intent(payload: bytes) -> str`, `execute(plan) -> None`,
    `execute_fulfilling(plan, fulfills: str) -> None`. It cannot live
    in `science.corpus` (which imports `science.boundary`, which needs
    the type); Task 3 deletes the corpus copy and re-exports this one.

- [ ] **Step 1: Write the failing round-trip and refusal tests**

Build one real closure per shape with a helper (no engine, no scratch —
construct `Recipe`/`ResultManifest`/`Occurrence` values directly, the
way `tests/test_closure.py` does; copy its fixture idiom):

```python
"""The closure-to-stored codec (spec §2.6 items 4–5)."""

from decimal import Decimal

import pytest

from nodes.core.frontmatter import node_from_markdown
from science import runrecord, stored
from science.errors import CanonicalTextRefused, MalformedRecord
from science.identity import v1


def test_projection_text_digests_to_the_address(assessment_closure) -> None:
    data = runrecord.projection_text(assessment_closure)
    assert v1.digest("science.run.v1", v1.decode(data)) == assessment_closure.address()


def test_decode_round_trip_reads_shape_spec_and_token(assessment_closure) -> None:
    _, path, (op,) = runrecord.publication_plan(assessment_closure, produces=None)
    node = node_from_markdown(op.content.decode("utf-8"))
    publication = runrecord.decode_run_record(node)
    assert publication == runrecord.RunPublication(
        address=assessment_closure.address(),
        shape="assessment",
        spec_identity=assessment_closure.recipe.spec_identity,
        event_token=assessment_closure.occurrence.event_token,
    )


def test_closure_member_mutation_diverges_from_the_id(assessment_closure) -> None:
    # Mutate one occurrence field inside the canonical text; the recomputed
    # address no longer matches the record id: not the named publication.
    _, _, (op,) = runrecord.publication_plan(assessment_closure, produces=None)
    text = op.content.decode("utf-8")
    mutated = text.replace(assessment_closure.occurrence.actor, "someone-else", 1)
    node = node_from_markdown(mutated)
    node.facets["semantic-identity"] = {"digest": stored.recompute_semantic_hash(node)}
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)


def test_incomplete_closure_fails_the_view_not_the_codec() -> None:
    # Canonical, self-addressed, not a projection: v1.decode and the digest
    # both succeed (freeze obligation 3 — the refusal exercised must be the
    # view's, never an earlier layer's); the typed projection view refuses.
    preimage = {"shape": "assessment", "spec_identity": "s" * 64, "event_token": "t" * 32}
    data = v1.encode(preimage)
    assert v1.decode(data) == preimage  # the decode layer passes
    assert len(v1.digest("science.run.v1", preimage)) == 64  # the digest layer passes
    with pytest.raises(MalformedRecord):
        runrecord.decode_projection(data)


def test_reversed_result_pairs_fail_canonical_reprojection(production_closure) -> None:
    data = runrecord.projection_text(production_closure)
    parsed = v1.decode(data)
    assert len(parsed["result"]) == 2  # the two-pair fixture: reversal is a real mutation
    parsed["result"] = list(reversed(parsed["result"]))
    assert parsed["result"] != sorted(parsed["result"])  # actually out of order now
    reversed_bytes = v1.encode(parsed)
    assert v1.decode(reversed_bytes) == parsed  # canonical (freeze obligation 3)
    assert len(v1.digest("science.run.v1", parsed)) == 64  # self-addressable
    with pytest.raises(MalformedRecord):
        runrecord.decode_projection(reversed_bytes)


def test_decimal_wire_arms_project_decode_recompute(make_closure) -> None:
    # Four closures identical except one parameter carrying each of the four
    # values. N2 obligation 3: pairwise distinctness at the canonical-text
    # layer is asserted BEFORE address agreement — a colliding encoding
    # would make the round trip vacuous. This is the codec half; the frozen
    # publish→capture→decode→recompute round trip runs durably as
    # test_intent_boundary_acceptance.py::test_decimal_round_trip_publishes_and_captures
    # (Task 13), where the four closures go through the port and
    # capture_records.
    values = [Decimal("0.5"), "0.5", 1, Decimal("1.0")]
    closures = [make_closure(parameters={"threshold": value}) for value in values]
    texts = [runrecord.projection_text(closure) for closure in closures]
    assert len(set(texts)) == 4  # distinct wires
    addresses = [closure.address() for closure in closures]
    assert len(set(addresses)) == 4  # the four never collide
    for closure, data, address in zip(closures, texts, addresses):
        parsed = runrecord.decode_projection(data)  # capture -> decode
        assert v1.digest("science.run.v1", parsed) == address  # recompute agrees
        threshold = parsed["recipe"]["parameters"]["threshold"]
        original = closure.recipe.parameters["threshold"]
        assert threshold == original and type(threshold) is type(original)


def test_shape_agreement_both_ways(assessment_closure, production_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure, produces=None)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run"]["spec"] = "not-the-closure-spec"
    node.facets["semantic-identity"] = {"digest": stored.recompute_semantic_hash(node)}
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)

    _, _, (op,) = runrecord.publication_plan(production_closure, produces="dataset:" + "d" * 64)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run"]["spec"] = "s" * 64  # a production run facet carries no spec key
    node.facets["semantic-identity"] = {"digest": stored.recompute_semantic_hash(node)}
    with pytest.raises(MalformedRecord):
        runrecord.decode_run_record(node)


def test_run_facet_shapes_are_exact_not_get_based(assessment_closure, production_closure) -> None:
    # The frozen shapes are exactly {"spec": <spec>} and exactly {} — an
    # extra key refuses in both directions, never slides past a .get().
    for closure, produces in ((assessment_closure, None), (production_closure, "dataset:" + "d" * 64)):
        _, _, (op,) = runrecord.publication_plan(closure, produces=produces)
        node = node_from_markdown(op.content.decode("utf-8"))
        node.facets["run"]["extra"] = "key"
        node.facets["semantic-identity"] = {"digest": stored.recompute_semantic_hash(node)}
        with pytest.raises(MalformedRecord):
            runrecord.decode_run_record(node)


def test_legacy_run_node_reads_and_never_qualifies() -> None:
    node = stored.run_node("legacy-slug", title="legacy", spec="s" * 64)
    assert stored.run_spec(node) == "s" * 64
    assert runrecord.decode_run_record(node) is None  # readable, no schema rejection


def test_production_facet_is_exactly_empty_and_run_spec_reads_none(production_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(production_closure, produces="dataset:" + "d" * 64)
    node = node_from_markdown(op.content.decode("utf-8"))
    assert node.facets["run"] == {}
    assert stored.run_spec(node) is None


def test_relations_are_role_preserving(assessment_closure, production_closure) -> None:
    # Both fixture recipes carry a `reads` input beside their eligible role,
    # so every member of both closed role vocabularies is pinned — a codec
    # collapsing roles to `reads` (or dropping `reads`) fails here.
    def edges(node, role, closure):
        expected = tuple(e.dataset for e in closure.recipe.inputs if e.role == role)
        assert expected, f"the fixture must carry a {role} input"
        assert stored.inputs_of(node, role) == expected

    _, _, (op,) = runrecord.publication_plan(assessment_closure, produces=None)
    node = node_from_markdown(op.content.decode("utf-8"))
    edges(node, "observes", assessment_closure)
    edges(node, "reads", assessment_closure)
    assert stored.inputs_of(node, "transforms") == ()
    assert stored.inputs_of(node, "produces") == ()

    dataset = "dataset:" + "d" * 64
    _, _, (op,) = runrecord.publication_plan(production_closure, produces=dataset)
    node = node_from_markdown(op.content.decode("utf-8"))
    edges(node, "transforms", production_closure)
    edges(node, "reads", production_closure)
    assert stored.inputs_of(node, "observes") == ()
    assert stored.inputs_of(node, "produces") == (dataset,)


def test_closure_facet_is_semantic_hash_covered(assessment_closure) -> None:
    _, _, (op,) = runrecord.publication_plan(assessment_closure, produces=None)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run-closure"]["projection"] += " "
    assert stored.semantic_hash_disagrees(node)  # stale stamp: the read refuses
    legacy = stored.run_node("legacy", title="legacy", spec="s" * 64)
    assert not stored.semantic_hash_disagrees(legacy)  # absent facet never enters
```

Fixtures `assessment_closure` / `production_closure` are thin pytest
wrappers over `closure_fixtures.make_closure` (the shared module in
this task's Files) — two declared outputs so pair reversal is a real
mutation, a `reads` input beside each shape's eligible role so the
relation round-trip pins every member of both closed role
vocabularies, and a `Decimal("0.5")` parameter so every round-trip
crosses the type-preserving wire. `make_closure` is importable by
`test_report.py`, `test_intent_reduce.py`, `test_consumer_agreement.py`
and the acceptance file — module-level fixtures do not cross test
files; this module does.

- [ ] **Step 2: Run to verify failure**

Run: `uv run --frozen pytest tests/test_runrecord.py -x`
Expected: FAIL — `ModuleNotFoundError: science.runrecord`.

- [ ] **Step 3: Implement `stored.py` additions**

```python
RUN_CLOSURE_FACET = "run-closure"
```

`COVERED_FACETS["run"]` becomes `(RUN_FACET, RUN_CLOSURE_FACET)` (the
dataset entry is the multi-facet precedent; an absent facet never
enters `semantic_projection`, so legacy stamps stay valid). Then:

```python
def run_publication_node(
    slug: str,
    *,
    title: str,
    projection: str,
    spec: str | None,
    observes: Sequence[str] = (),
    reads: Sequence[str] = (),
    transforms: Sequence[str] = (),
    produces: Sequence[str] = (),
) -> Node:
    """A boundary-published run: the readers' `run` facet — `{"spec": spec}`
    for an assessment run, exactly `{}` for a production run — beside the
    `run-closure` facet carrying the address preimage as v1-canonical text.
    `run_node` stays the legacy constructor, unchanged for its callers."""
    node_id = f"run:{slug}"
    relations = [
        Relation(source=node_id, predicate=predicate, target=target)
        for predicate, targets in (
            (OBSERVES, observes),
            (READS, reads),
            (TRANSFORMS, transforms),
            (PRODUCES, produces),
        )
        for target in targets
    ]
    run_facet: dict[str, Any] = {} if spec is None else {"spec": spec}
    facets = {RUN_FACET: run_facet, RUN_CLOSURE_FACET: {"projection": projection}}
    return _node("run", slug, title, facets, relations)
```

- [ ] **Step 4: Implement `runrecord.py`**

```python
"""The closure-to-stored run publication codec (spec §2.6 items 4–5).

Identity is the closure's address: `run:<RunClosure.address()>`. The
`run-closure` facet carries the `{recipe, result, occurrence}` projection
as v1-canonical text — the type-preserving wire the address digests.
Decode validates through the typed projection view (exact schema at every
depth) plus canonical reprojection equality, recomputes the address, and
checks the readers' `run` facet for both-ways shape agreement. A record
with no closure facet is legacy: readable, resolvable, never qualifying.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn, Protocol, cast, final

from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, WritePlan

from science import stored
from science.errors import MalformedClosure, MalformedRecord
from science.identity import v1
from science.recipe import (
    ASSESSMENT_ROLES,
    PRODUCTION_ROLES,
    RUN_DOMAIN,
    SHAPES,
    RunClosure,
    _occurrence_projection,
    _pairs,
)
from science.sealed import sealed

__all__ = [
    "OperationPort",
    "RunPublication",
    "bare_address",
    "decode_projection",
    "decode_run_record",
    "projection_text",
    "publication_plan",
    "run_ref",
]


def run_ref(address: str) -> str:
    """The bare-address/typed-ref bridge, bare -> typed: prepend the kind
    (spec §2.6 item 5). Bare spellings: `RunClosure.address()`,
    `Registration.pointer`, `StampedBasis.run`. Typed spellings: the
    stored record id, an assessment facet's `run` field, relation
    endpoints. One injective bridge, one implementation."""
    if type(address) is not str or not address or ":" in address:
        raise MalformedRecord(f"{address!r} is not a bare closure address")
    return f"run:{address}"


def bare_address(ref: str) -> str:
    """The bridge's inverse, typed -> bare: strip the kind."""
    if type(ref) is not str or not ref.startswith("run:"):
        raise MalformedRecord(f"{ref!r} is not a typed run reference")
    return ref.removeprefix("run:")


class OperationPort(Protocol):
    def append_intent(self, payload: bytes) -> str: ...

    def execute(self, plan: WritePlan) -> None: ...

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None: ...


@sealed
@final
@dataclass(frozen=True)
class RunPublication:
    address: str
    shape: str
    spec_identity: str | None
    event_token: str


def projection_text(closure: RunClosure) -> bytes:
    if type(closure) is not RunClosure:
        raise MalformedClosure("projection_text requires a RunClosure")
    return v1.encode(
        {
            "recipe": closure.recipe._projection(),
            "result": _pairs(closure.result.outputs),
            "occurrence": _occurrence_projection(closure.occurrence),
        }
    )
```

The typed projection view — the exact-schema validator plus the
reprojection. Every helper refuses with `MalformedRecord`:

```python
def _refuse(path: str, why: str) -> NoReturn:
    raise MalformedRecord(f"run projection at {path}: {why}")


def _mapping(value: object, keys: set[str], path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _refuse(path, "not an object")
    if set(value) != keys:
        _refuse(path, f"keys {sorted(value)} != {sorted(keys)}")
    return value


def _str_at(value: object, path: str) -> str:
    # Exact string TYPE only — the closure's own `_require_str`
    # (recipe.py:56) admits the empty string, and the view must accept
    # every value the official encoder can publish. Non-emptiness is
    # checked only where a constructor checks it (`_component_at`, the
    # stochastic rationale).
    if type(value) is not str:
        _refuse(path, "not a string")
    return value


def _component_at(value: object, path: str) -> str:
    # Mirrors `_require_component` (recipe.py:61): a held component
    # identity, never "", "unknown", or "attested".
    _str_at(value, path)
    if value in ("", "unknown", "attested"):
        _refuse(path, f"{value!r} is not a held component identity")
    return value


def _str_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or any(type(member) is not str for member in value):
        _refuse(path, "not a list of strings")
    return value


def _pair_list(value: object, path: str) -> list[list[str]]:
    if not isinstance(value, list) or any(
        not isinstance(row, list) or len(row) != 2 or any(type(m) is not str for m in row)
        for row in value
    ):
        _refuse(path, "not a list of [string, string] pairs")
    return value


_RECIPE_KEYS = {
    "shape", "code_identity", "environment", "workflow_definition_identity",
    "invocation", "inputs", "parameters", "nondeterminism", "boundary_policy",
    "rule_bindings",
}


def _validate_recipe(recipe: object) -> str:
    """Returns the shape. Mirrors the closure invariants at the projection's
    own level — every check below is a constructor's check restated
    (`Recipe`, `RecipeInput`, `Invocation` in recipe.py), never a stricter
    invention and never a reconstruction (the environment is a digest)."""
    if not isinstance(recipe, dict):
        _refuse("$.recipe", "not an object")
    shape = _str_at(recipe.get("shape"), "$.recipe.shape")
    if shape not in SHAPES:
        _refuse("$.recipe.shape", f"{shape!r} is outside {SHAPES}")
    expected = _RECIPE_KEYS | ({"spec_identity"} if shape == "assessment" else set())
    _mapping(recipe, expected, "$.recipe")
    if shape == "assessment":
        _str_at(recipe["spec_identity"], "$.recipe.spec_identity")
    _component_at(recipe["code_identity"], "$.recipe.code_identity")
    _str_at(recipe["environment"], "$.recipe.environment")
    _component_at(recipe["workflow_definition_identity"], "$.recipe.workflow_definition_identity")
    invocation = _mapping(
        recipe["invocation"],
        {"entrypoint", "targets", "bindings", "declared_outputs"},
        "$.recipe.invocation",
    )
    _str_at(invocation["entrypoint"], "$.recipe.invocation.entrypoint")
    lists = {
        field: _str_list(invocation[field], f"$.recipe.invocation.{field}")
        for field in ("targets", "bindings", "declared_outputs")
    }
    # Invocation.__post_init__, restated (over the typed lists):
    if any(target.startswith("-") for target in lists["targets"]):
        _refuse("$.recipe.invocation.targets", "an option-like target is not a workflow target")
    declared = lists["declared_outputs"]
    for output in declared:
        depth = 0
        if output.startswith("/"):
            _refuse("$.recipe.invocation.declared_outputs", f"{output!r} is absolute")
        for segment in output.split("/"):
            if segment == "..":
                depth -= 1
            elif segment not in ("", "."):
                depth += 1
            if depth < 0:
                _refuse("$.recipe.invocation.declared_outputs", f"{output!r} escapes the run root")
    if len(set(declared)) != len(declared):
        _refuse("$.recipe.invocation.declared_outputs", "duplicate logical names")
    roles = ASSESSMENT_ROLES if shape == "assessment" else PRODUCTION_ROLES
    inputs = recipe["inputs"]
    if not isinstance(inputs, list):
        _refuse("$.recipe.inputs", "not a list")
    for index, row in enumerate(inputs):
        path = f"$.recipe.inputs[{index}]"
        if not isinstance(row, dict):
            _refuse(path, "not an object")
        keys = {"role", "dataset", "content"} | ({"exclusion"} if "exclusion" in row else set())
        _mapping(row, keys, path)
        role = _str_at(row["role"], f"{path}.role")
        if role not in roles:
            _refuse(f"{path}.role", f"{role!r} is outside the {shape} partition {roles}")
        _str_at(row["dataset"], f"{path}.dataset")
        _component_at(row["content"], f"{path}.content")
        if "exclusion" in row:
            if role != "reads":
                _refuse(f"{path}.exclusion", "an exclusion certification is carried by a `reads` input only")
            exclusion = _mapping(row["exclusion"], {"rationale", "attribution"}, f"{path}.exclusion")
            # ExclusionCertification.__post_init__ refuses empty members.
            for member in ("rationale", "attribution"):
                if not _str_at(exclusion[member], f"{path}.exclusion.{member}"):
                    _refuse(f"{path}.exclusion.{member}", "an exclusion member is never empty")
    if not isinstance(recipe["parameters"], dict):
        _refuse("$.recipe.parameters", "not an object")
    _validate_nondeterminism(recipe["nondeterminism"])
    policy = _mapping(
        recipe["boundary_policy"], {"identity", "scope_rule", "capabilities"},
        "$.recipe.boundary_policy",
    )
    _str_at(policy["identity"], "$.recipe.boundary_policy.identity")
    _str_at(policy["scope_rule"], "$.recipe.boundary_policy.scope_rule")
    _str_list(policy["capabilities"], "$.recipe.boundary_policy.capabilities")
    bindings = _pair_list(recipe["rule_bindings"], "$.recipe.rule_bindings")
    rules = [rule for rule, _ in bindings]
    if len(rules) != len(set(rules)):
        _refuse("$.recipe.rule_bindings", "each logical rule is named once")
    return shape


def _validate_nondeterminism(value: object) -> None:
    if not isinstance(value, dict) or "variant" not in value:
        _refuse("$.recipe.nondeterminism", "not a variant object")
    variant = value["variant"]
    if variant == "deterministic":
        _mapping(value, {"variant"}, "$.recipe.nondeterminism")
    elif variant == "stochastic-unseeded":
        _mapping(value, {"variant", "rationale"}, "$.recipe.nondeterminism")
        _str_at(value["rationale"], "$.recipe.nondeterminism.rationale")
        if not value["rationale"]:
            # StochasticUnseeded.__post_init__ refuses the empty rationale.
            _refuse("$.recipe.nondeterminism.rationale", "an empty rationale declares nothing")
    elif variant == "seeded":
        _mapping(value, {"variant", "plan"}, "$.recipe.nondeterminism")
        plan = _mapping(
            value["plan"], {"derivation_rule", "streams", "roots", "stream_roots"},
            "$.recipe.nondeterminism.plan",
        )
        _str_at(plan["derivation_rule"], "$.recipe.nondeterminism.plan.derivation_rule")
        streams = _str_list(plan["streams"], "$.recipe.nondeterminism.plan.streams")
        roots = plan["roots"]
        if not isinstance(roots, dict) or any(
            type(k) is not str or type(v) is not int for k, v in roots.items()
        ):
            _refuse("$.recipe.nondeterminism.plan.roots", "not a string-to-int object")
        stream_roots = plan["stream_roots"]
        if not isinstance(stream_roots, dict) or any(
            type(k) is not str or type(v) is not str for k, v in stream_roots.items()
        ):
            _refuse("$.recipe.nondeterminism.plan.stream_roots", "not a string-to-string object")
        # SeedPlan.__post_init__'s totality, restated:
        if set(streams) - set(stream_roots):
            _refuse("$.recipe.nondeterminism.plan", "streams with no root")
        if set(stream_roots) - set(streams):
            _refuse("$.recipe.nondeterminism.plan", "a mapping entry for an undeclared stream")
        if set(stream_roots.values()) - set(roots):
            _refuse("$.recipe.nondeterminism.plan", "mapped roots nobody declared")
    else:
        _refuse("$.recipe.nondeterminism.variant", f"unknown variant {variant!r}")


def _validate_occurrence(value: object) -> str:
    """Returns the event token."""
    occurrence = _mapping(
        value,
        {"event_token", "started_at", "actor", "host_realization", "trace",
         "realized_seeds", "receipt"},
        "$.occurrence",
    )
    for field in ("event_token", "started_at", "actor", "host_realization"):
        _str_at(occurrence[field], f"$.occurrence.{field}")
    trace = occurrence["trace"]
    if not isinstance(trace, list):
        _refuse("$.occurrence.trace", "not a list")
    for index, job in enumerate(trace):
        path = f"$.occurrence.trace[{index}]"
        row = _mapping(job, {"job_id", "rule", "wildcards", "inputs", "outputs"}, path)
        _str_at(row["job_id"], f"{path}.job_id")
        _str_at(row["rule"], f"{path}.rule")
        _pair_list(row["wildcards"], f"{path}.wildcards")
        _str_list(row["inputs"], f"{path}.inputs")
        _str_list(row["outputs"], f"{path}.outputs")
    seeds = occurrence["realized_seeds"]
    if not isinstance(seeds, dict) or any(
        type(job) is not str
        or not isinstance(per_stream, dict)
        or any(type(s) is not str or type(seed) is not int for s, seed in per_stream.items())
        for job, per_stream in seeds.items()
    ):
        _refuse("$.occurrence.realized_seeds", "not a [job][stream] -> int object")
    receipt = _mapping(
        occurrence["receipt"],
        {"scratch_mapping", "argv", "rendered_config", "capabilities"},
        "$.occurrence.receipt",
    )
    _str_at(receipt["scratch_mapping"], "$.occurrence.receipt.scratch_mapping")
    _str_list(receipt["argv"], "$.occurrence.receipt.argv")
    _pair_list(receipt["rendered_config"], "$.occurrence.receipt.rendered_config")
    _str_list(receipt["capabilities"], "$.occurrence.receipt.capabilities")
    return cast(str, occurrence["event_token"])


def _input_sort_key(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    exclusion = row.get("exclusion")
    rationale = cast(str, exclusion["rationale"]) if isinstance(exclusion, dict) else ""
    attribution = cast(str, exclusion["attribution"]) if isinstance(exclusion, dict) else ""
    return (cast(str, row["role"]), cast(str, row["dataset"]), cast(str, row["content"]),
            rationale, attribution)


def _reproject(parsed: dict[str, object]) -> dict[str, object]:
    """Rebuild the mapping under the projection's ordering rules — every
    array the projection sorts, re-sorted; everything else carried whole.
    Canonical JSON preserves array order, so equality with the parsed
    mapping is what enforces the orderings, current and future."""
    import copy

    # Validation already proved every shape below; the casts restate what
    # the validator established, for pyright — never a runtime assumption.
    rebuilt = cast(dict[str, object], copy.deepcopy(parsed))
    recipe = cast(dict[str, object], rebuilt["recipe"])
    recipe["inputs"] = sorted(cast("list[dict[str, object]]", recipe["inputs"]), key=_input_sort_key)
    recipe["rule_bindings"] = sorted(cast("list[list[str]]", recipe["rule_bindings"]))
    policy = cast(dict[str, object], recipe["boundary_policy"])
    policy["capabilities"] = sorted(cast("list[str]", policy["capabilities"]))
    nondeterminism = cast(dict[str, object], recipe["nondeterminism"])
    if nondeterminism.get("variant") == "seeded":
        plan = cast(dict[str, object], nondeterminism["plan"])
        plan["streams"] = sorted(cast("list[str]", plan["streams"]))
    rebuilt["result"] = sorted(cast("list[list[str]]", rebuilt["result"]))
    occurrence = cast(dict[str, object], rebuilt["occurrence"])
    for job in cast("list[dict[str, object]]", occurrence["trace"]):
        job["wildcards"] = sorted(cast("list[list[str]]", job["wildcards"]))
    receipt = cast(dict[str, object], occurrence["receipt"])
    receipt["rendered_config"] = sorted(cast("list[list[str]]", receipt["rendered_config"]))
    receipt["capabilities"] = sorted(cast("list[str]", receipt["capabilities"]))
    return rebuilt


def decode_projection(data: bytes) -> dict[str, object]:
    parsed = v1.decode(data)
    if not isinstance(parsed, dict):
        _refuse("$", "not an object")
    _mapping(parsed, {"recipe", "result", "occurrence"}, "$")
    _validate_recipe(parsed["recipe"])
    result = _pair_list(parsed["result"], "$.result")
    # ResultManifest + RunClosure.__post_init__, restated: unique logical
    # names, and the result names are exactly the declared outputs.
    names = [name for name, _ in result]
    if len(set(names)) != len(names):
        _refuse("$.result", "duplicate logical names")
    recipe = cast(dict[str, object], parsed["recipe"])
    invocation = cast(dict[str, object], recipe["invocation"])
    if set(names) != set(cast("list[str]", invocation["declared_outputs"])):
        _refuse("$.result", "result names disagree with the declared outputs")
    _validate_occurrence(parsed["occurrence"])
    if _reproject(parsed) != parsed:
        _refuse("$", "an array the projection sorts is out of its canonical order")
    return parsed


def decode_run_record(node: Node) -> RunPublication | None:
    if node.kind != "run":
        raise MalformedRecord(f"{node.id}: not a run record")
    facet = node.facets.get(stored.RUN_CLOSURE_FACET)
    if facet is None:
        return None  # legacy: readable, resolvable, never qualifying
    if not isinstance(facet, dict) or set(facet) != {"projection"} or type(facet["projection"]) is not str:
        raise MalformedRecord(f"{node.id}: the run-closure facet is exactly {{'projection': <text>}}")
    data = facet["projection"].encode("utf-8")
    parsed = decode_projection(data)
    address = v1.digest(RUN_DOMAIN, parsed)
    if node.id != f"run:{address}":
        raise MalformedRecord(f"{node.id}: the recomputed address {address} is not the record id")
    recipe = cast(dict[str, object], parsed["recipe"])
    shape = cast(str, recipe["shape"])
    spec_identity = cast("str | None", recipe.get("spec_identity"))
    run_facet = node.facets.get(stored.RUN_FACET)
    if not isinstance(run_facet, dict):
        raise MalformedRecord(f"{node.id}: a boundary-published run carries the run facet")
    # The frozen shapes are exact: {"spec": <spec>} and {} — never a
    # .get() that an extra key slides past.
    if shape == "assessment":
        if run_facet != {"spec": spec_identity}:
            raise MalformedRecord(f"{node.id}: the run facet is exactly {{'spec': <the closure's spec>}}")
    elif run_facet != {}:
        raise MalformedRecord(f"{node.id}: a production run facet is exactly {{}}")
    occurrence = cast(dict[str, object], parsed["occurrence"])
    return RunPublication(
        address=address,
        shape=shape,
        spec_identity=spec_identity,
        event_token=cast(str, occurrence["event_token"]),
    )


def publication_plan(
    closure: RunClosure, *, produces: str | None
) -> tuple[str, str, tuple[CreateOp, ...]]:
    shape = closure.recipe.shape
    if (shape == "dataset-production") != (produces is not None):
        raise MalformedClosure(
            "a dataset-production run publishes exactly one produces edge; an assessment run none"
        )
    address = closure.address()
    inputs = closure.recipe.inputs
    node = stored.run_publication_node(
        address,
        title=f"{shape} run",
        projection=projection_text(closure).decode("utf-8"),
        spec=closure.recipe.spec_identity,
        observes=tuple(e.dataset for e in inputs if e.role == "observes"),
        reads=tuple(e.dataset for e in inputs if e.role == "reads"),
        transforms=tuple(e.dataset for e in inputs if e.role == "transforms"),
        produces=(produces,) if produces is not None else (),
    )
    path = f"run/{address}.md"
    # The returned id goes through the bridge — the one spelling authority.
    return run_ref(address), path, (CreateOp(path, node_to_markdown(node).encode("utf-8")),)
```

- [ ] **Step 5: Run to verify pass, then the gate block**

Run: `uv run --frozen pytest tests/test_runrecord.py tests/test_holdings_stored.py tests/test_corpus_write.py`
then the gate block. Expected: PASS (the `COVERED_FACETS` change must
not disturb existing run-kind tests — legacy records carry no closure
facet).

- [ ] **Step 6: Ledger + commit**

```bash
git add python/src/science/runrecord.py python/src/science/stored.py \
        python/tests/test_runrecord.py docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(runrecord): closure-to-stored codec with typed projection view"
```

---

### Task 3: The port — `execute` and the record ceiling

**Files:**
- Create: `python/src/science/world/records.py` (constants only in this
  task; capture lands in Task 7)
- Modify: `python/src/science/root.py` (`DurableOperationPort`, line 929)
- Modify: `python/src/science/corpus.py` (`OperationPort` protocol at
  line 121 is **deleted** and re-exported from its single home,
  `science.runrecord`)
- Modify: every structural port fake the grep in Step 3 surfaces
  (`tests/test_operation_port.py::FakePort` first among them)
- Test: `python/tests/test_operation_port.py` (extend)

**Interfaces:**
- Produces: `science.world.records.RECORD_CEILING = 8 * 1024 * 1024` —
  the one shared constant, imported by both enforcement points.
- Produces: `DurableOperationPort.execute(plan) -> None` — the
  non-fulfilling publication on the existing `fulfills=None` executor
  path, preserving the two-error contract (`PlanRefusedError` pre-write,
  `ExecutionError` on execution failure).
- Produces: both `execute` and `execute_fulfilling` refuse any planned
  postimage over the ceiling as `PlanRefusedError` **before the
  executor is constructed** — the qualifying-publication boundary, not
  the shared plan validation (`_refuse_malformed` runs inside every
  executor, including the non-port corpus/world/store writers).

- [ ] **Step 1: Write the failing tests** (extend
  `tests/test_operation_port.py`; its `durable_port(tmp_path)` helper
  builds the real port, and `science_root._log_seam()` reads the chain
  back — the idiom `tests/test_holdings_boundary.py:140` uses)

```python
from science import root as science_root
from science.root import init_corpus_root, init_store_root
from science.world.logmodel import RegisteredEntryView, WellFormedView
from science.world.records import RECORD_CEILING


def _registered_port(root):
    # Every write against an unregistered root refuses (root.py:308's
    # explicit act) — registration is part of every durable builder.
    init_corpus_root(root)
    return durable_port(root)


def _registrations(root):
    chain = science_root._log_seam().inspect_registered(root)
    assert type(chain) is WellFormedView
    return [entry for entry in chain.entries if type(entry) is RegisteredEntryView]


def test_execute_publishes_fulfilling_nothing(tmp_path) -> None:
    port = _registered_port(tmp_path)
    port.execute([CreateOp(path="act-report/" + "a" * 64 + ".md", content=b"content")])
    (registration,) = _registrations(tmp_path)
    assert registration.fulfills is None
    assert (tmp_path / "act-report" / ("a" * 64 + ".md")).read_bytes() == b"content"


def test_execute_refuses_a_malformed_plan_before_any_write(tmp_path) -> None:
    port = _registered_port(tmp_path)
    with pytest.raises(PlanRefusedError):
        port.execute([CreateOp(path="../escape.md", content=b"x")])  # lexical, pre-write
    assert _registrations(tmp_path) == []  # nothing reached the chain


def test_execute_surfaces_an_execution_failure_as_execution_error(tmp_path) -> None:
    port = _registered_port(tmp_path)
    plan = [CreateOp(path="act-report/" + "b" * 64 + ".md", content=b"x")]
    port.execute(plan)
    with pytest.raises(ExecutionError):
        port.execute(plan)  # create over an existing file cannot be satisfied


def test_oversized_postimage_refuses_before_any_write(tmp_path) -> None:
    port = _registered_port(tmp_path)
    boundary = b"x" * RECORD_CEILING
    port.execute([CreateOp(path="act-report/" + "c" * 64 + ".md", content=boundary)])  # exactly the ceiling publishes
    with pytest.raises(PlanRefusedError):
        port.execute([CreateOp(path="act-report/" + "d" * 64 + ".md", content=boundary + b"x")])
    with pytest.raises(PlanRefusedError):
        port.execute_fulfilling([CreateOp(path="run/" + "e" * 64 + ".md", content=boundary + b"x")], "f" * 64)
    assert not (tmp_path / "act-report" / ("d" * 64 + ".md")).exists()  # no partial record
    assert not (tmp_path / "run").exists()
    assert len(_registrations(tmp_path)) == 1  # only the at-ceiling publication registered


def test_non_port_writes_are_unaffected_by_the_ceiling(tmp_path) -> None:
    # Cut label 3's non-port regression, freeze obligation 5: a genuine
    # non-port effect path an existing writer uses — the store writer —
    # never a synthetic executor call constructed only for the arm.
    init_store_root(tmp_path)  # the store writer's own explicit registration act
    big = b"x" * (RECORD_CEILING + 1)
    outcome = science_root._store_write(tmp_path, "payload.bin", big)
    assert (tmp_path / "payload.bin").read_bytes() == big
    assert outcome.txid  # the effect landed through its own executor
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run --frozen pytest tests/test_operation_port.py -x`
Expected: FAIL — `AttributeError: 'DurableOperationPort' object has no attribute 'execute'`.

- [ ] **Step 3: Implement**

`python/src/science/world/records.py` (this task's slice of it):

```python
"""The published-record evidence surface: the shared ceiling, and (Task 7)
the fd-anchored, classified, bounded capture."""

from __future__ import annotations

RECORD_CEILING = 8 * 1024 * 1024
"""2^23 bytes — one constant, two enforcement points: the reader's
ceiling-plus-one bounded capture and the port's pre-construction check
(spec §3.1). A payload of exactly the ceiling passes both."""
```

`root.py` — import `RECORD_CEILING` from `science.world.records`, then
inside `DurableOperationPort`:

```python
    def execute(self, plan: WritePlan) -> None:
        """The non-fulfilling publication (spec §2.6 item 2a): a pre-intent
        refusal report lands through this, fulfilling nothing."""
        _refuse_over_ceiling(plan)
        DurableExecutor(
            self.root,
            backend=self._backend,
            storage=self._storage,
            metadata_root=self._metadata_root,
            consumer_tag=CONSUMER_TAG,
            intent_domain=INTENT_DOMAIN,
            fulfills=None,
        ).execute(plan)
```

`execute_fulfilling` gains `_refuse_over_ceiling(plan)` as its first
statement, before the executor is constructed. Module-level, beside
`_refuse_malformed`:

```python
def _refuse_over_ceiling(plan: WritePlan) -> None:
    """The writer half of the shared record ceiling. Lives at the port —
    the qualifying-publication boundary — never in `_refuse_malformed`,
    which runs inside every executor including the non-port corpus,
    world, and store writers the ceiling must not bind."""
    for op in plan:
        content = getattr(op, "content", None)
        if isinstance(content, bytes) and len(content) > RECORD_CEILING:
            raise PlanRefusedError(
                f"planned postimage at {op.path!r} is {len(content)} bytes, "
                f"over the {RECORD_CEILING}-byte record ceiling"
            )
```

**Single-home the protocol.** `runrecord.OperationPort` (Task 2) is the
one authority — it already carries all three methods. `corpus.py`
deletes its local `class OperationPort(Protocol)` (line 121) and
re-exports the single home so every existing importer keeps working:

```python
from science.runrecord import OperationPort
```

(`OperationPort` stays in `corpus.__all__`; no import cycle — `corpus`
already imports `boundary`, which imports `runrecord`, and `runrecord`
imports only `stored`/`recipe`/`nodes`.)

**Update every structural fake.** Grep and list before editing:

```bash
grep -rn "OperationPort\|def execute_fulfilling" python/src python/tests | grep -v runrecord
```

Every fake implementing the port shape gains the third method —
`tests/test_operation_port.py`'s `FakePort` (add
`executed: ClassVar[list[WritePlan]]` and
`def execute(self, plan): self.executed.append(plan)`), and any other
fake the grep surfaces (`tests/test_import_bundle.py` and the corpus
write tests construct ports for the import boundary — same one-method
addition at each).

- [ ] **Step 4: Run to verify pass; run cut8–cut10 acceptance on the
  certified volume** (root.py and corpus.py were touched), then the
  gate block.

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/world/records.py python/src/science/root.py \
        python/src/science/corpus.py python/tests/test_operation_port.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
# plus every test file whose structural port fake gained `execute`
# (the Step 3 grep's list) — commit exactly what changed.
git commit -m "feat(port): non-fulfilling execute and the writer-side record ceiling"
```

---

### Task 4: The run boundary's persistence sequence

**Files:**
- Modify: `python/src/science/boundary.py` (`execute_assessment_run`
  line 359, `execute_production_run` line 403, `_refused` line 138)
- Modify: `python/src/science/replay.py` — `replay()` (line 99) calls
  both entrypoints and breaks the moment the port is required:
  `replay(original, *, port: OperationPort, spec, ...)` gains the
  required parameter and adds `"port": port` to its `common` dict.
- Modify: `python/tests/fixtures_cut3.py` — `run_assessment`,
  `run_production` (gain `port` + `definition_override`), and
  `replay_of` (line 416, gains `port`, passed through to `replay`).
- Modify: `python/tests/test_replay.py` and every other
  `replay_of`/`replay(` caller the grep
  `grep -rln "replay_of(\|replay(" python/tests` surfaces — each
  passes a port (the shared fake where the assertion is not about
  persistence).
- Test: `python/tests/test_boundary.py` (extend), plus a durable test
  file `python/tests/test_run_persistence.py` (new) using the
  `certified_work` fixture and a real `DurableOperationPort`.

**Interfaces:**
- Consumes: `runrecord.publication_plan`, `runrecord.OperationPort`,
  `mint_dataset` (`production.py:72`), `v1.encode`,
  `stored.act_report_node`, `node_to_markdown`.
- Produces: both entrypoints gain the **required** keyword parameter
  `port: OperationPort` — no defaulted in-memory mode. The sequence is
  fixed: freeze root (the port is root-bound at construction), durably
  append the intent, member acts, terminal publication through the same
  port with boundary-constructed `fulfills`. Wire shapes:
  - assessment-run append payload:
    `v1.encode({"spec_identity": ..., "event_token": ..., "actor": ...})`
  - operation append payload (production run, kind frozen `run-attempt`):
    `v1.encode({"kind": ..., "event_token": ..., "actor": ...})` — the
    import boundary's existing encoding (`corpus.py:1106`), reused.
- Produces: a pre-intent refusal publishes its report through
  `port.execute` (unfulfilling); a post-intent refusal publishes the
  report through `port.execute_fulfilling`; a minted run publishes the
  closure record through `port.execute_fulfilling`, with `produces` set
  to the `mint_dataset`-derived address for a production run.
- Produces: both entrypoints gain
  `expected_recipe_identity: str | None = None` — the frozen replay
  gate (spec §2.6 item 6, the twenty-first amendment): when set, the
  boundary compares the minted run's `recipe.identity()` against it
  exactly once, **after the mint and before the terminal publication**;
  on mismatch the outcome is the standard post-intent refusal (reason
  `recipe-identity-mismatch`) whose report is what publishes fulfilling
  the intent — the durable terminal record always states the returned
  result, and the mismatched run is never published. Deliberately a
  value, not a callback: `replay()` is the sole consumer, and no
  caller-supplied code runs inside the boundary between mint and
  publication (so there is no undefined exception or return-value
  surface to specify).

- [ ] **Step 1: Write the failing tests**

The executable helpers are `fixtures_cut3.run_assessment(tmp_path, ...)`
and `run_production(...)` — they call the entrypoints with a real staged
workflow. This task threads a required `port` parameter through both
helpers (Step 3), so the durable tests below drive real executions
through a real `DurableOperationPort` (`durable_port` from
`tests/test_operation_port.py`), and the chain is read back through
`science_root._log_seam().inspect_registered(root)` — the
`tests/test_holdings_boundary.py:140` idiom.

In `test_run_persistence.py`:

```python
from fixtures_cut3 import run_assessment, run_production
from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_from_markdown
from science import root as science_root
from science import runrecord, stored
from science.boundary import RunMinted, RunRefused
from science.production import mint_dataset
from science.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView
from test_operation_port import durable_port
from science.root import init_corpus_root


def _observer_port(tmp_path):
    root = tmp_path / "observer"
    init_corpus_root(root)  # unregistered roots refuse every write (root.py:308)
    return root, durable_port(root)


def _entries(root):
    chain = science_root._log_seam().inspect_registered(root)
    assert type(chain) is WellFormedView
    return chain.entries


def test_assessment_sequence_appends_intent_then_publishes_fulfilling(tmp_path) -> None:
    root, port = _observer_port(tmp_path)
    result = run_assessment(tmp_path, port=port)
    assert type(result) is RunMinted
    entries = _entries(root)
    intents = [e for e in entries if type(e) is IntentEntryView]
    registrations = [e for e in entries if type(e) is RegisteredEntryView]
    assert len(intents) == 1 and len(registrations) == 1
    assert entries.index(intents[0]) < entries.index(registrations[0])  # append first
    assert registrations[0].fulfills == intents[0].digest  # boundary-constructed
    address = result.run.address()
    record = (root / "run" / f"{address}.md").read_bytes()
    publication = runrecord.decode_run_record(node_from_markdown(record.decode("utf-8")))
    assert publication.address == address
    assert publication.spec_identity == result.run.recipe.spec_identity
    assert publication.event_token == result.intent.event_token


def test_pre_intent_refusal_publishes_unfulfilling_report(tmp_path) -> None:
    root, port = _observer_port(tmp_path)
    result = run_assessment(tmp_path, port=port, spec="not-a-spec")
    assert type(result) is RunRefused and result.registration is None
    entries = _entries(root)
    assert [type(e) for e in entries if type(e) is IntentEntryView] == []  # no intent
    (registration,) = [e for e in entries if type(e) is RegisteredEntryView]
    assert registration.fulfills is None  # unfulfilling, through execute
    assert (root / "act-report" / f"{result.report.identity()}.md").exists()


def test_post_intent_refusal_publishes_fulfilling_report(tmp_path) -> None:
    # definition-mismatch fires inside _execute_run, after the append: hand
    # run_assessment a snakefile whose bytes differ from the definition's.
    from fixtures_cut3 import SNAKEFILE_DETERMINISTIC, SNAKEFILE_SCRATCHY, definition, stage

    root, port = _observer_port(tmp_path)
    result = run_assessment(
        tmp_path, port=port, snakefile=SNAKEFILE_DETERMINISTIC,
        # override inside the helper: pass definition(snakefile=SNAKEFILE_SCRATCHY)
        # via the helper's new `definition_override` parameter (Step 3 adds it
        # beside `port` for exactly this arm).
        definition_override=definition(snakefile=SNAKEFILE_SCRATCHY),
    )
    assert type(result) is RunRefused and result.reason == "definition-mismatch"
    entries = _entries(root)
    (intent_entry,) = [e for e in entries if type(e) is IntentEntryView]
    (registration,) = [e for e in entries if type(e) is RegisteredEntryView]
    assert registration.fulfills == intent_entry.digest  # the report fulfills the intent


class _Killed(BaseException):
    pass


def test_kill_between_append_and_start_leaves_intent_only(tmp_path, monkeypatch) -> None:
    # N2 obligation 2: deterministic interposition at the port seam — the
    # kill lands after the durable append and before any member act.
    root, inner = _observer_port(tmp_path)

    class KilledAfterAppend:
        def append_intent(self, payload):
            digest = inner.append_intent(payload)
            raise _Killed()  # the process dies with the intent durable

        def execute(self, plan):
            raise AssertionError("no publication may run")

        def execute_fulfilling(self, plan, fulfills):
            raise AssertionError("no publication may run")

    engine_calls: list[object] = []
    monkeypatch.setattr("science.boundary.run_engine", lambda *a, **k: engine_calls.append(a))
    with pytest.raises(_Killed):
        run_assessment(tmp_path, port=KilledAfterAppend())
    entries = _entries(root)
    assert all(type(e) is not RegisteredEntryView for e in entries)  # nothing published
    assert len([e for e in entries if type(e) is IntentEntryView]) == 1  # durably present
    assert engine_calls == []  # no member act began
    assert not (root / "run").exists() and not (root / "act-report").exists()


def test_cross_root_publication_refuses(tmp_path) -> None:
    # u6, freeze obligation 4: both roots writable and serviceable — the
    # refusal is placement's (the fulfills binding), not a lifecycle gate's.
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    init_corpus_root(root_a); init_corpus_root(root_b)  # both writable and serviceable
    port_a, port_b = durable_port(root_a), durable_port(root_b)
    port_b.execute([CreateOp(path="act-report/" + "0" * 64 + ".md", content=b"serviceable")])
    digest_on_a = port_a.append_intent(b'{"actor":"a","event_token":"t","kind":"import"}')
    with pytest.raises(ExecutionError):
        port_b.execute_fulfilling(
            [CreateOp(path="run/" + "1" * 64 + ".md", content=b"record")], digest_on_a
        )
    assert not (root_a / "run").exists() and not (root_b / "run").exists()


def test_production_run_publishes_exactly_one_produces_edge(tmp_path) -> None:
    root, port = _observer_port(tmp_path)
    result = run_production(tmp_path, port=port)
    assert type(result) is RunMinted
    address = result.run.address()
    node = node_from_markdown((root / "run" / f"{address}.md").read_text())
    minted = mint_dataset(result.run, existing_bases={})
    assert stored.inputs_of(node, "produces") == (minted.address,)
    assert node.facets["run"] == {}  # the frozen production facet


def test_replay_recipe_mismatch_publishes_refusal_not_run(tmp_path) -> None:
    # The frozen replay gate (spec §2.6 item 6): the recipe comparison runs
    # BEFORE the terminal publication, so a mismatch publishes the refusal
    # report — never a durable run beside an in-memory refusal.
    from fixtures_cut3 import SNAKEFILE_SCRATCHY, replay_of

    root, port = _observer_port(tmp_path)
    original = run_assessment(tmp_path, port=port)
    assert type(original) is RunMinted
    replay_root = tmp_path / "replay-observer"
    init_corpus_root(replay_root)
    replayed_dir = tmp_path / "replayed"
    replayed_dir.mkdir()
    outcome = replay_of(original, replayed_dir, port=durable_port(replay_root),
                        snakefile=SNAKEFILE_SCRATCHY)  # a different recipe identity
    assert type(outcome) is RunRefused
    assert outcome.reason == "recipe-identity-mismatch"  # the frozen gate's reason
    entries = _entries(replay_root)
    (intent_entry,) = [e for e in entries if type(e) is IntentEntryView]
    (registration,) = [e for e in entries if type(e) is RegisteredEntryView]
    assert registration.fulfills == intent_entry.digest  # the REPORT fulfills the intent
    assert not (replay_root / "run").exists()  # the mismatched run was never published
    assert (replay_root / "act-report" / f"{outcome.report.identity()}.md").exists()


def test_no_caller_supplied_fulfills_path_exists() -> None:
    # u7, asserted structurally over both signatures.
    import inspect

    from science.boundary import execute_assessment_run, execute_production_run

    for entrypoint in (execute_assessment_run, execute_production_run):
        assert "fulfills" not in inspect.signature(entrypoint).parameters
```

In `test_boundary.py` and `fixtures_cut3.py`: `run_assessment` and
`run_production` gain the required `port` parameter (plus the
`definition_override` keyword defaulting to `None`) and pass both
through; every direct `execute_assessment_run`/`execute_production_run`
call site passes a port. For call sites asserting refusal reasons only,
use one shared in-memory fake implementing all three methods (extend
`FakePort` from `tests/test_operation_port.py` after Task 3 gave it
`execute`) — there is no portless mode left.

- [ ] **Step 2: Run to verify failure**

Run: `uv run --frozen pytest tests/test_run_persistence.py -x`
Expected: FAIL — `TypeError: execute_assessment_run() got an unexpected
keyword argument 'port'`.

- [ ] **Step 3: Implement**

In `boundary.py` — import `from science.production import mint_dataset`,
`from science.runrecord import OperationPort, publication_plan`,
`from science.identity import v1`, `from science.stored import act_report_node`,
`from nodes.core.frontmatter import node_to_markdown`,
`from nodes.core.write_plan import CreateOp`. Add helpers:

```python
def _report_plan(report: ActReport) -> tuple[CreateOp, ...]:
    from science import stored

    node = stored.act_report_node(report)
    return (CreateOp(f"act-report/{report.identity()}.md", node_to_markdown(node).encode("utf-8")),)


def _intent_wire(intent: AssessmentRunIntent | OperationIntent) -> bytes:
    if type(intent) is AssessmentRunIntent:
        return v1.encode(
            {"spec_identity": intent.spec_identity, "event_token": intent.event_token, "actor": intent.actor}
        )
    return v1.encode({"kind": intent.kind, "event_token": intent.event_token, "actor": intent.actor})
```

`execute_assessment_run` becomes (production mirrors it, with
`OperationIntent("run-attempt", ...)` and the `produces` address):

```python
def execute_assessment_run(*, spec: object, port: OperationPort,
                           expected_recipe_identity: str | None = None,
                           definition, ...) -> RunMinted | RunRefused:
    if type(spec) is not FrozenSpec:
        subject = spec if type(spec) is str else "absent"
        refused = _refused("no-frozen-spec", subject, actor, observer, started_at)
        port.execute(_report_plan(refused.report))  # unfulfilling, pre-intent
        return refused
    if reason := _preflight(tuple(entry.dataset for entry in spec.input_roles), held_inputs):
        refused = _refused(reason, spec.identity, actor, observer, started_at)
        port.execute(_report_plan(refused.report))
        return refused
    intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)
    fulfills = port.append_intent(_intent_wire(intent))
    result = _execute_run(intent=intent, subject=spec.identity, spec=spec, inputs=(), parameters={},
                          nondeterminism=None, definition=definition, code_roots=code_roots,
                          held_inputs=held_inputs, entrypoint=entrypoint, targets=targets,
                          declared_outputs=declared_outputs, actor=actor, observer=observer,
                          started_at=started_at, host_realization=host_realization,
                          scratch_base=scratch_base, cores=cores)  # the existing call, verbatim
    if (
        type(result) is RunMinted
        and expected_recipe_identity is not None
        and result.run.recipe.identity() != expected_recipe_identity
    ):
        # The frozen replay gate (spec §2.6 item 6): the mismatched run is
        # never published; the terminal record is the refusal report.
        result = _refused("recipe-identity-mismatch", spec.identity, actor, observer, started_at, intent)
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run, produces=None)
        port.execute_fulfilling(plan, fulfills)
    else:
        port.execute_fulfilling(_report_plan(result.report), fulfills)
    return result
```

The production entrypoint applies the same comparison (subject
`"absent"`) before its minted branch.

For the production entrypoint the minted branch is:

```python
    if type(result) is RunMinted:
        minted = mint_dataset(result.run, existing_bases={})
        _, _, plan = publication_plan(result.run, produces=minted.address)
        port.execute_fulfilling(plan, fulfills)
```

The boundary constructs `fulfills` from its own `append_intent` return
value; neither entrypoint accepts a `fulfills` argument (u7 is asserted
structurally by inspecting both signatures in a test).

In `fixtures_cut3.py`: `run_assessment` and `run_production` gain
`port` (required) and `definition_override=None` (when set, passed as
`definition=` in place of `definition(snakefile=snakefile)` — the
post-intent definition-mismatch arm's hook), threading both to the
entrypoints unchanged; `replay_of` gains `port` and passes it to
`replay`.

In `replay.py`: `replay()` gains the required `port: OperationPort`
keyword (import the protocol from `science.runrecord`), adds
`"port": port` to the `common` mapping both entrypoint calls unpack —
a replay is a run and persists like one; no portless mode survives
here either — and its post-hoc recipe check **becomes the frozen
gate**: delete the
`if outcome.run.recipe.identity() != recipe.identity():` branch
(replay.py:142) and add
`"expected_recipe_identity": recipe.identity()` to `common`, so the
refusal is decided before the terminal publication and the durable
record agrees with the returned value.

- [ ] **Step 4: Run to verify pass; run cut8–cut10 acceptance (boundary
  feeds corpus paths), then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/boundary.py python/src/science/replay.py \
        python/tests/fixtures_cut3.py python/tests/test_boundary.py \
        python/tests/test_replay.py python/tests/test_run_persistence.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(boundary): destination port, append-first sequence, durable terminal publication"
```

(Any further test file the `replay_of` grep touched joins the `git add`
list — commit exactly what changed.)

---

### Task 5: The shared holdings shape and the regenerated interior

**Files:**
- Create: `python/src/science/intents/__init__.py`
- Create: `python/src/science/intents/holdings.py`
- Create: `python/tools/regen_holdings_interior.py`
- Modify: `python/src/science/holdings/qualify.py` (regenerated output)
- Test: `python/tests/test_intents_holdings.py` (new)

**Interfaces:**
- Produces: `science/intents/holdings.py` — the maintained source of
  the holdings qualification section: exactly the current
  `qualify.py` content (the interior relocated, not rewritten —
  `decode_holdings_intent`, `holdings_layout_path`, `qualify_intent`,
  the constants). Dialect rules hold: one top-level import (`json`),
  no science imports.
- Produces: `science/holdings/qualify.py` regenerated as
  `_HEADER + <shared source bytes>`, where the header is the two lines:

  ```python
  # GENERATED from science/intents/holdings.py by tools/regen_holdings_interior.py.
  # Edit the source and regenerate; hand edits here are discarded.
  ```

  The header changes the rule's implementation bytes → new content
  digest → a new receipt is minted by the existing receipt machinery
  (`implementation_identity` is derived, nothing is hand-pinned).
- Produces: `intents/__init__.py` exporting the package (fills up over
  Tasks 6–9).

- [ ] **Step 1: Write the failing guard test**

```python
"""The one interior: the rule source is generated from the shared shape (spec §4)."""

from importlib import resources


def test_qualify_source_is_generated_from_the_shared_shape() -> None:
    shared = resources.files("science.intents").joinpath("holdings.py").read_bytes()
    generated = resources.files("science.holdings").joinpath("qualify.py").read_bytes()
    header, _, body = generated.partition(b"\n# Edit the source and regenerate; hand edits here are discarded.\n")
    assert header.startswith(b"# GENERATED from science/intents/holdings.py")
    assert body == shared


def test_shared_shape_stays_in_the_dialect() -> None:
    source = resources.files("science.intents").joinpath("holdings.py").read_text()
    imports = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert imports == ["import json"]


def test_the_rule_digest_moved_with_the_regeneration() -> None:
    # The regenerated source differs from the cut-10 interior byte-for-byte
    # (the generation header), so the bundle's implementation identity is
    # new — assert holdings_rule_bundle() still builds and its
    # implementation contains the shared bytes.
    from science.holdings.reduce import holdings_rule_bundle
    from science.world.rules import implementation_identity

    bundle = holdings_rule_bundle()
    shared = resources.files("science.intents").joinpath("holdings.py").read_bytes()
    assert shared in bundle.implementation
    assert len(implementation_identity(bundle.implementation)) == 64
```

- [ ] **Step 2: Run to verify failure** (`ModuleNotFoundError: science.intents`).

- [ ] **Step 3: Implement**

- `science/intents/__init__.py`:

```python
"""The general intent-qualification surface (spec §2): one reducer, one
precedence, three shapes as data. `holdings.py` is the rules-dialect
source the holdings rule regenerates from — pure, one import, servable
to every consumer."""
```

- `science/intents/holdings.py`: copy the current
  `science/holdings/qualify.py` bytes verbatim (keep the `ruff: noqa`
  line and docstring; this file is now the maintained source).
- `tools/regen_holdings_interior.py`:

```python
"""Regenerate science/holdings/qualify.py from the shared holdings shape."""

from pathlib import Path

HEADER = (
    b"# GENERATED from science/intents/holdings.py by tools/regen_holdings_interior.py.\n"
    b"# Edit the source and regenerate; hand edits here are discarded.\n"
)

def main() -> None:
    src = Path(__file__).resolve().parents[1] / "src" / "science"
    shared = (src / "intents" / "holdings.py").read_bytes()
    (src / "holdings" / "qualify.py").write_bytes(HEADER + shared)

if __name__ == "__main__":
    main()
```

- Run it: `uv run --frozen python tools/regen_holdings_interior.py`.

- [ ] **Step 4: Run the guard tests plus the whole holdings family**

Run: `uv run --frozen pytest tests/test_intents_holdings.py tests/test_holdings_reduce.py tests/test_holdings_receipt.py tests/test_holdings_capture.py tests/test_holdings_boundary.py`
then cut10 acceptance on the certified volume (the holdings interior
moved), then the gate block. Expected: PASS — blocking semantics and
precedence are byte-identical concerns of the regeneration.

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/intents/ python/tools/regen_holdings_interior.py \
        python/src/science/holdings/qualify.py python/tests/test_intents_holdings.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(intents): shared holdings shape; regenerate the rule interior"
```

---

### Task 6: The decode gate (`science/intents/shapes.py`)

**Files:**
- Create: `python/src/science/intents/shapes.py`
- Test: `python/tests/test_intent_gate.py` (new)

**Interfaces:**
- Consumes: `v1.decode`, `CanonicalTextRefused`,
  `report.OPERATION_KINDS`, `report.OperationIntent`,
  `report.AssessmentRunIntent`, `intents.holdings.decode_holdings_intent`
  (one interior, wrapped — never a second holdings schema).
- Produces (Tasks 9–11 rely on these exact names):
  - `DecodedIntent` — frozen dataclass
    `(digest: str, shape: Literal["assessment-run", "operation", "holdings"], value: object)`
    where `value` is `AssessmentRunIntent` / `OperationIntent` / the
    holdings dict the dialect decoder returns.
  - `Unrecognized` — frozen dataclass
    `(digest: str, code: str, severity: str, detail: str)` with `code`
    in `("intent-domain-unrecognized", "intent-payload-malformed")`,
    severities `warning` / `error` respectively.
  - `decode_intent(digest: str, payload: bytes) -> DecodedIntent | Unrecognized`
    — the total gate: every payload lands in exactly one bullet of
    spec §3.2.
  - Evidence values: `RunEvidence(shape, spec_identity, event_token)`,
    `ReportEvidence(operation, event_token)`,
    `ObservationEvidence(location, event_token)`, `InertRecord()` —
    frozen dataclasses (defined here; Task 8's decoder and Task 11's
    `completion` both produce them).
  - `mismatch(intent: DecodedIntent, evidence) -> str | None` — `None`
    when the evidence qualifies the intent, else the reason class.
  - `REASON_PRIORITY = ("wrong-spec", "wrong-token", "wrong-kind",
    "wrong-shape", "wrong-location", "wrong-purpose", "no-record")` —
    the deterministic per-pointer reason selection order.

- [ ] **Step 1: Write the failing tests**

```python
"""The total decode gate and the per-shape matching requirements (spec §2.2, §3.2)."""

from science.identity import v1
from science.intents import shapes


def decoded(digest: str, payload: bytes) -> shapes.DecodedIntent:
    gate = shapes.decode_intent(digest, payload)
    assert type(gate) is shapes.DecodedIntent, gate
    return gate


def unrecognized(digest: str, payload: bytes) -> shapes.Unrecognized:
    gate = shapes.decode_intent(digest, payload)
    assert type(gate) is shapes.Unrecognized, gate
    return gate


def _holdings_payload(**overrides) -> bytes:
    value = {
        "actor": "someone",
        "domain": "science.holdings-intent.v1",
        "event_token": "t" * 32,
        "kind": "re-check",
        "location": {"relative_path": "a/b", "store_id": "0" * 32, "type": "store"},
    }
    value.update(overrides)
    return v1.encode(value)


def test_the_three_discriminators_are_exact_and_disjoint() -> None:
    assert decoded("d1", v1.encode({"kind": "import", "event_token": "t", "actor": "a"})).shape == "operation"
    assert decoded("d2", v1.encode({"spec_identity": "s", "event_token": "t", "actor": "a"})).shape == "assessment-run"
    assert decoded("d3", _holdings_payload()).shape == "holdings"


def test_the_built_holdings_boundary_payload_decodes_unicode_included() -> None:
    # The official writer emits json.dumps(..., ensure_ascii=True): actor
    # "é" arrives as é — valid holdings intent, not v1-canonical text.
    # The dialect owns holdings parsing, so it decodes (never "undecodable").
    from science.holdings.boundary import intent_payload
    from science.holdings.records import StoreLocator

    from collections.abc import Mapping

    payload = intent_payload(
        location=StoreLocator(store_id="0" * 32, relative_path="a/b"),
        act_kind="re-check", event_token="t" * 32, actor="renée",
    )
    gate = decoded("d", payload)
    assert gate.shape == "holdings"
    assert isinstance(gate.value, Mapping) and gate.value["event_token"] == "t" * 32


def test_foreign_domain_reads_unrecognized_warning() -> None:
    gate = unrecognized("d", v1.encode({"domain": "science.other.v1", "x": "y"}))
    assert gate == shapes.Unrecognized("d", "intent-domain-unrecognized", "warning", "science.other.v1")


def test_empty_object_reads_domainless_unrecognized() -> None:
    gate = unrecognized("d", b"{}")
    assert gate.code == "intent-domain-unrecognized" and gate.detail == "domainless-unrecognized"


def test_out_of_vocabulary_kind_is_domainless_unrecognized() -> None:
    gate = unrecognized("d", v1.encode({"kind": "dataset-production", "event_token": "t", "actor": "a"}))
    assert gate.code == "intent-domain-unrecognized"  # OPERATION_KINDS is closed


def test_undecodable_bytes_read_undecodable() -> None:
    gate = unrecognized("d", b"not json")
    assert gate.code == "intent-domain-unrecognized" and gate.detail == "undecodable"


def test_discriminator_matched_schema_invalid_is_payload_malformed_error() -> None:
    gate = unrecognized("d", v1.encode({"kind": "import", "event_token": "", "actor": "a"}))
    assert gate == shapes.Unrecognized("d", "intent-payload-malformed", "error", "operation")
    gate = unrecognized("d", _holdings_payload(location={"relative_path": "/abs", "store_id": "0" * 32, "type": "store"}))
    assert gate.code == "intent-payload-malformed"


def test_matching_requirements_per_shape() -> None:
    run = shapes.RunEvidence("assessment", "s" * 64, "tok")
    intent = decoded("d", v1.encode({"spec_identity": "s" * 64, "event_token": "tok", "actor": "a"}))
    assert shapes.mismatch(intent, run) is None
    assert shapes.mismatch(intent, shapes.RunEvidence("assessment", "x" * 64, "tok")) == "wrong-spec"
    assert shapes.mismatch(intent, shapes.RunEvidence("assessment", "s" * 64, "other")) == "wrong-token"
    assert shapes.mismatch(intent, shapes.RunEvidence("dataset-production", None, "tok")) == "wrong-shape"
    assert shapes.mismatch(intent, shapes.ReportEvidence("run-attempt", "tok")) is None
    assert shapes.mismatch(intent, shapes.ReportEvidence("import", "tok")) == "wrong-kind"
    assert shapes.mismatch(intent, shapes.ObservationEvidence("store:x:y", "tok")) == "wrong-purpose"

    production = decoded("d", v1.encode({"kind": "run-attempt", "event_token": "tok", "actor": "a"}))
    assert shapes.mismatch(production, shapes.RunEvidence("dataset-production", None, "tok")) is None
    assert shapes.mismatch(production, shapes.RunEvidence("assessment", "s" * 64, "tok")) == "wrong-shape"
    assert shapes.mismatch(production, shapes.ReportEvidence("run-attempt", "tok")) is None

    non_run = decoded("d", v1.encode({"kind": "import", "event_token": "tok", "actor": "a"}))
    assert shapes.mismatch(non_run, shapes.ReportEvidence("import", "tok")) is None
    assert shapes.mismatch(non_run, shapes.ReportEvidence("audit", "tok")) == "wrong-kind"
    assert shapes.mismatch(non_run, shapes.RunEvidence("dataset-production", None, "tok")) == "wrong-purpose"

    held = decoded("d", _holdings_payload(kind="write"))
    location = "store:" + "0" * 32 + ":a/b"
    assert shapes.mismatch(held, shapes.ObservationEvidence(location, "t" * 32)) is None
    assert shapes.mismatch(held, shapes.ObservationEvidence("store:" + "0" * 32 + ":other", "t" * 32)) == "wrong-location"
    assert shapes.mismatch(held, shapes.ObservationEvidence(location, "other")) == "wrong-token"
    assert shapes.mismatch(held, shapes.InertRecord()) == "wrong-purpose"
```

- [ ] **Step 2: Run to verify failure** (`ImportError`).

- [ ] **Step 3: Implement `shapes.py`**

```python
"""The closed shape union: the total decode gate and the matching
requirements (spec §2.2, §3.2). Three shapes as data to one reducer,
never forks of it; the holdings schema is the dialect's, wrapped."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, final

from science.errors import CanonicalTextRefused, MalformedRecord
from science.identity import v1
from science.intents import holdings as holdings_shape
from science.report import OPERATION_KINDS, AssessmentRunIntent, OperationIntent
from science.sealed import sealed

__all__ = [
    "REASON_PRIORITY",
    "DecodedIntent",
    "InertRecord",
    "ObservationEvidence",
    "ReportEvidence",
    "RunEvidence",
    "Unrecognized",
    "decode_intent",
    "mismatch",
]

REASON_PRIORITY = (
    "wrong-spec", "wrong-token", "wrong-kind", "wrong-shape",
    "wrong-location", "wrong-purpose", "no-record",
)


@sealed
@final
@dataclass(frozen=True)
class DecodedIntent:
    digest: str
    shape: Literal["assessment-run", "operation", "holdings"]
    value: AssessmentRunIntent | OperationIntent | Mapping[str, str]
    """The typed union pyright narrows on: the two report values, or the
    holdings dialect's decoded mapping (string-valued)."""


@sealed
@final
@dataclass(frozen=True)
class Unrecognized:
    digest: str
    code: str
    severity: str
    detail: str


@sealed
@final
@dataclass(frozen=True)
class RunEvidence:
    shape: str
    spec_identity: str | None
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class ReportEvidence:
    operation: str
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class ObservationEvidence:
    location: str
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class InertRecord:
    """A readable published record that qualifies nothing: a legacy run,
    an unrelated kind. Fully resolved, never unresolvable."""


def _malformed(digest: str, shape: str) -> Unrecognized:
    return Unrecognized(digest, "intent-payload-malformed", "error", shape)


def decode_intent(digest: str, payload: bytes) -> DecodedIntent | Unrecognized:
    """The total gate (spec §3.2): every payload lands in exactly one bullet.

    The domain-bearing branch parses with the DIALECT's own tolerant parse —
    spec §2.2 makes the holdings decoder's contract the union's, and the
    built boundary appends `json.dumps(..., ensure_ascii=True)` payloads
    (holdings/boundary.py:39) that are valid holdings intents without being
    v1-canonical text on non-ASCII fields. v1 canonicality governs the two
    domainless shapes, whose only writers (§2.6, corpus.py:1106) emit
    `v1.encode`. Recorded as a ledger ruling at this task."""
    try:
        sniffed: object = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        sniffed = None
    if isinstance(sniffed, dict) and "domain" in sniffed:
        if sniffed["domain"] == holdings_shape.HOLDINGS_INTENT_DOMAIN:
            row = {"digest": digest, "entry": {"payload": payload.hex()}}
            try:
                decoded = holdings_shape.decode_holdings_intent(row)
            except ValueError:
                return _malformed(digest, "holdings")
            assert decoded is not None  # the domain matched above
            return DecodedIntent(digest, "holdings", decoded)
        return Unrecognized(digest, "intent-domain-unrecognized", "warning", str(sniffed["domain"]))
    try:
        value = v1.decode(payload)
    except CanonicalTextRefused:
        return Unrecognized(digest, "intent-domain-unrecognized", "warning", "undecodable")
    if not isinstance(value, dict):
        return Unrecognized(digest, "intent-domain-unrecognized", "warning", "domainless-unrecognized")
    if set(value) == {"kind", "event_token", "actor"} and value.get("kind") in OPERATION_KINDS:
        try:
            _require_fields(value, ("kind", "event_token", "actor"))
            return DecodedIntent(digest, "operation", OperationIntent(value["kind"], value["event_token"], value["actor"]))
        except MalformedRecord:
            return _malformed(digest, "operation")
    if set(value) == {"spec_identity", "event_token", "actor"}:
        try:
            _require_fields(value, ("spec_identity", "event_token", "actor"))
            return DecodedIntent(
                digest, "assessment-run",
                AssessmentRunIntent(value["spec_identity"], value["event_token"], value["actor"]),
            )
        except MalformedRecord:
            return _malformed(digest, "assessment-run")
    return Unrecognized(digest, "intent-domain-unrecognized", "warning", "domainless-unrecognized")


def _require_fields(value: dict[str, object], names: tuple[str, ...]) -> None:
    for name in names:
        member = value[name]
        if type(member) is not str or not member:
            raise MalformedRecord(f"intent field {name} must be a non-empty string")


def mismatch(intent: DecodedIntent, evidence: object) -> str | None:
    """`None` when the evidence qualifies the intent, else the reason class —
    the frozen §2.2 matching requirements, one implementation for every
    consumer. Branches narrow on the VALUE's type (pyright-clean), which
    the gate made equivalent to branching on `shape`."""
    if type(evidence) is InertRecord:
        return "wrong-purpose"
    value = intent.value
    if isinstance(value, AssessmentRunIntent):
        if type(evidence) is RunEvidence:
            if evidence.shape != "assessment":
                return "wrong-shape"
            if evidence.spec_identity != value.spec_identity:
                return "wrong-spec"
            return None if evidence.event_token == value.event_token else "wrong-token"
        if type(evidence) is ReportEvidence:
            if evidence.operation != "run-attempt":
                return "wrong-kind"
            return None if evidence.event_token == value.event_token else "wrong-token"
        return "wrong-purpose"
    if isinstance(value, OperationIntent):
        if value.kind == "run-attempt":
            if type(evidence) is RunEvidence:
                if evidence.shape != "dataset-production":
                    return "wrong-shape"
                return None if evidence.event_token == value.event_token else "wrong-token"
            if type(evidence) is ReportEvidence:
                if evidence.operation != "run-attempt":
                    return "wrong-kind"
                return None if evidence.event_token == value.event_token else "wrong-token"
            return "wrong-purpose"
        if type(evidence) is ReportEvidence:
            if evidence.operation != value.kind:
                return "wrong-kind"
            return None if evidence.event_token == value.event_token else "wrong-token"
        return "wrong-purpose"  # a run publication never fulfills a non-run operation
    # holdings: the dialect's mapping, string-valued by construction
    if type(evidence) is ObservationEvidence:
        if evidence.location != value["location"]:
            return "wrong-location"
        return None if evidence.event_token == value["event_token"] else "wrong-token"
    return "wrong-purpose"
```

- [ ] **Step 4: Run to verify pass, then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/intents/shapes.py python/tests/test_intent_gate.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(intents): total decode gate and per-shape matching requirements"
```

---

### Task 7: The bounded record capture (`science/world/records.py`)

**Files:**
- Modify: `python/src/science/world/records.py` (Task 3 created it)
- Test: `python/tests/test_record_capture.py` (new; durable — uses the
  `certified_work` fixture, the classification behaviors are Linux
  facts about real fds)

**Interfaces:**
- Produces:
  - `RECORD_NAMESPACES = ("run", "act-report", "holdings-observation")`
  - `capture_records(root: Path, kind: RootKind) -> tuple[tuple[str, bytes], ...]`
    — `()` for `world`/`store` kinds; for a corpus root, one
    `(root-relative POSIX path, payload)` pair per record file
    successfully captured beneath the three namespaces, sorted by path.
    Fd-anchored no-follow descent (`O_DIRECTORY | O_NOFOLLOW` per
    component), leaf classified via `O_PATH | O_NOFOLLOW` + `fstat`
    before any readable open, reopened only through
    `/proc/self/fd/<fd>`; ceiling-plus-one bounded read. Every failure
    (symlink either position, non-regular leaf, oversize, permission,
    disappearance) **withholds** the pair — nothing raises out of
    capture.
  - `_leaf_seam(path: str) -> None` — module-level no-op called per
    leaf between enumeration and the `O_PATH` open; the deterministic
    interposition point the swap-race arm monkeypatches (N2
    obligation 4).

- [ ] **Step 1: Write the failing tests**

```python
"""The captured-record evidence surface (spec §3.1): no-follow by
construction, classified before any readable open, bounded."""

import os
from pathlib import Path

from science.world import records


def _corpus(tmp: Path) -> Path:
    for namespace in records.RECORD_NAMESPACES:
        (tmp / namespace).mkdir(parents=True)
    return tmp


def test_captures_each_record_file_sorted(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "a.md").write_bytes(b"run-bytes")
    (root / "act-report" / "b.md").write_bytes(b"report-bytes")
    assert records.capture_records(root, "corpus") == (
        ("act-report/b.md", b"report-bytes"),
        ("run/a.md", b"run-bytes"),
    )


def test_world_and_store_kinds_capture_nothing(certified_work) -> None:
    assert records.capture_records(certified_work, "world") == ()
    assert records.capture_records(certified_work, "store") == ()


def test_leaf_symlink_is_classified_and_withheld(certified_work) -> None:
    root = _corpus(certified_work / "root")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    (root / "run" / "a.md").symlink_to(outside)
    assert records.capture_records(root, "corpus") == ()  # never followed


def test_intermediate_symlink_directory_is_withheld(certified_work) -> None:
    root = _corpus(certified_work / "root")
    elsewhere = certified_work / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "x.md").write_bytes(b"OUTSIDE")
    (root / "run").rmdir()
    (root / "run").symlink_to(elsewhere)
    assert records.capture_records(root, "corpus") == ()


def test_fifo_is_classified_never_opened_readable(certified_work) -> None:
    root = _corpus(certified_work / "root")
    os.mkfifo(root / "run" / "a.md")  # an open for reading would block
    assert records.capture_records(root, "corpus") == ()  # completes, withheld


def test_swap_race_is_lost_by_the_attacker(certified_work, monkeypatch) -> None:
    root = _corpus(certified_work / "root")
    target = root / "run" / "a.md"
    target.write_bytes(b"genuine")
    outside = certified_work / "outside.md"
    outside.write_bytes(b"OUTSIDE")
    orderings: list[str] = []

    real_seam = records._leaf_seam

    def swap(path: str) -> None:
        orderings.append(f"enumerated:{path}")
        target.unlink()
        target.symlink_to(outside)
        orderings.append(f"swapped:{path}")
        real_seam(path)

    monkeypatch.setattr(records, "_leaf_seam", swap)
    captured = records.capture_records(root, "corpus")
    assert captured == ()  # classified as a symlink on the opened descriptor
    assert orderings == ["enumerated:run/a.md", "swapped:run/a.md"]
    assert b"OUTSIDE" not in b"".join(payload for _, payload in captured)


def test_ceiling_boundary_exact_captures_one_over_withholds(certified_work) -> None:
    root = _corpus(certified_work / "root")
    (root / "run" / "exact.md").write_bytes(b"x" * records.RECORD_CEILING)
    (root / "run" / "over.md").write_bytes(b"x" * (records.RECORD_CEILING + 1))
    captured = dict(records.capture_records(root, "corpus"))
    assert set(captured) == {"run/exact.md"}
    assert len(captured["run/exact.md"]) == records.RECORD_CEILING
```

- [ ] **Step 2: Run to verify failure** (`AttributeError: capture_records`).

- [ ] **Step 3: Implement**

```python
import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from science.world.verify import RootKind

RECORD_NAMESPACES = ("run", "act-report", "holdings-observation")
"""The published-record namespaces the shapes read (spec §3.1): run
publications, act-reports, holdings observations."""


def _leaf_seam(path: str) -> None:
    """Called per leaf between enumeration and the O_PATH open — the
    deterministic interposition point the swap-race arm drives. A no-op
    in production; never remove the call sites."""


def capture_records(root: Path, kind: "RootKind") -> tuple[tuple[str, bytes], ...]:
    if kind != "corpus":
        return ()
    captured: list[tuple[str, bytes]] = []
    try:
        root_fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return ()
    try:
        for namespace in RECORD_NAMESPACES:
            _capture_directory(root_fd, namespace, namespace, captured)
    finally:
        os.close(root_fd)
    return tuple(sorted(captured))


def _capture_directory(parent_fd: int, name: str, prefix: str, captured: list[tuple[str, bytes]]) -> None:
    try:
        dir_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError:
        return  # symlink (ELOOP), non-directory (ENOTDIR), absent: withheld
    try:
        try:
            with os.scandir(dir_fd) as scan:
                children = sorted(scan, key=lambda child: child.name)
        except OSError:
            return
        for child in children:
            if child.name.startswith("."):
                continue
            path = f"{prefix}/{child.name}"
            if child.is_dir(follow_symlinks=False):
                _capture_directory(dir_fd, child.name, path, captured)
                continue
            _leaf_seam(path)
            payload = _read_leaf(dir_fd, child.name)
            if payload is not None:
                captured.append((path, payload))
    finally:
        os.close(dir_fd)


def _read_leaf(dir_fd: int, name: str) -> bytes | None:
    """Classify through O_PATH before any readable open exists; reopen only
    through the descriptor's own re-open route; read ceiling + 1. Every
    failure withholds — capture never raises and never truncates."""
    try:
        path_fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=dir_fd)
    except OSError:
        return None
    try:
        try:
            if not stat.S_ISREG(os.fstat(path_fd).st_mode):
                return None  # a symlink or fifo at the leaf: opened as itself, never read
            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)
        except OSError:
            return None
        try:
            chunks: list[bytes] = []
            remaining = RECORD_CEILING + 1
            while remaining > 0:
                chunk = os.read(read_fd, min(remaining, 1 << 20))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            return None if len(data) > RECORD_CEILING else data
        except OSError:
            return None
        finally:
            os.close(read_fd)
    finally:
        os.close(path_fd)
```

- [ ] **Step 4: Run to verify pass, then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/world/records.py python/tests/test_record_capture.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(records): fd-anchored classified bounded record capture"
```

---

### Task 8: Evidence decoding (`science/intents/evidence.py`)

**Files:**
- Create: `python/src/science/intents/evidence.py`
- Modify: `python/src/science/stored.py` — the act-report validator
  extracted from `corpus.py:1399` as `act_report_facet(node)`;
  `_valid_report_entry` (`corpus.py:637`) **and its
  `_REPORT_ENTRY_OUTCOMES` table (`corpus.py:623`)** move with it —
  the validator is nothing without its per-kind outcome-field table.
- Modify: `python/src/science/corpus.py` —
  `_refuse_malformed_act_report` delegates to the extracted validator
  (converting `MalformedRecord` to `ValidationRefused`), so one
  authority validates act-report records for writer and reader alike.
- Test: `python/tests/test_intent_evidence.py` (new)

**Interfaces:**
- Consumes: `node_from_markdown` (`nodes.core.frontmatter`),
  `stored.semantic_hash_disagrees` / `semantic_hash_missing`,
  `stored.holdings_observation_value` (`stored.py:390` — the exact
  typed reader with its facet round-trip equality),
  `runrecord.decode_run_record`, the evidence values from Task 6.
- Produces:
  - `stored.act_report_facet(node: Node) -> Mapping[str, object]` —
    the full validator relocated: exact facet key set, operation in
    `OPERATION_KINDS`, string fields, entries validated member by
    member, **no relations**, and the record id equal to
    `act-report:<v1.digest(ACT_REPORT_DOMAIN, facet)>`; raises
    `MalformedRecord`.
  - `RecordUndecodable(ScienceError)` — added to `science/errors.py`
    beside the record errors: the captured bytes are not a readable
    publication (qualification `unresolvable` for the pointer, never a
    refusal — the evaluator maps, it never propagates).
  - `decode_record(path: str, payload: bytes) ->
    RunEvidence | ReportEvidence | ObservationEvidence | InertRecord` —
    raises `RecordUndecodable` on: markdown/YAML failure; a stale or
    missing semantic stamp (`IdentityError` from the recomputation
    mapped too — a stamp that cannot even recompute is unreadable); a
    **path↔kind↔id binding failure** (the record's id must be
    `<kind>:<slug>` for the captured path `<kind>/<slug>.md`, so a
    valid record stored under another namespace or name never
    qualifies as the named publication); a run record whose closure
    facet refuses (`MalformedRecord`/`CanonicalTextRefused` mapped); a
    malformed act-report (the extracted full validator, not a
    two-field read); a malformed holdings observation (the typed
    reader, not a three-field read), or a holdings id disagreeing with
    the value's own identity. Returns `InertRecord()` for a legacy run
    (no closure facet) and for any kind the shapes do not read.
  - `record_layout_path(path: str) -> bool` — `True` exactly for
    `<namespace>/<...>.md` under `RECORD_NAMESPACES` — the paths whose
    absence from `records` makes a pointer unresolvable.

- [ ] **Step 1: Write the failing tests**

```python
"""Captured bytes -> qualification evidence (spec §3.1)."""

import pytest

from nodes.core.frontmatter import node_to_markdown
from science import stored
from science.errors import RecordUndecodable
from science.intents import evidence, shapes


def test_run_publication_decodes_to_run_evidence(assessment_closure) -> None:
    from science.runrecord import publication_plan

    _, path, (op,) = publication_plan(assessment_closure, produces=None)
    decoded = evidence.decode_record(path, op.content)
    assert decoded == shapes.RunEvidence(
        "assessment", assessment_closure.recipe.spec_identity,
        assessment_closure.occurrence.event_token,
    )


def test_legacy_run_is_inert_not_undecodable() -> None:
    node = stored.run_node("legacy", title="legacy", spec="s" * 64)
    payload = node_to_markdown(node).encode("utf-8")
    assert evidence.decode_record("run/legacy.md", payload) == shapes.InertRecord()


def test_stale_stamp_is_undecodable(assessment_closure) -> None:
    from nodes.core.frontmatter import node_from_markdown
    from science.runrecord import publication_plan

    _, path, (op,) = publication_plan(assessment_closure, produces=None)
    node = node_from_markdown(op.content.decode("utf-8"))
    node.facets["run-closure"]["projection"] += " "  # stamp now stale
    with pytest.raises(RecordUndecodable):
        evidence.decode_record(path, node_to_markdown(node).encode("utf-8"))


def test_act_report_decodes_operation_and_token(sample_act_report) -> None:
    payload = node_to_markdown(stored.act_report_node(sample_act_report)).encode("utf-8")
    decoded = evidence.decode_record(f"act-report/{sample_act_report.identity()}.md", payload)
    assert decoded == shapes.ReportEvidence(sample_act_report.operation, sample_act_report.event_token)


def test_holdings_observation_decodes_location_and_token(sample_observation_node) -> None:
    payload = node_to_markdown(sample_observation_node).encode("utf-8")
    slug = sample_observation_node.id.split(":", 1)[1]
    decoded = evidence.decode_record(f"holdings-observation/{slug}.md", payload)
    facet = sample_observation_node.facets["holdings-observation"]
    location = facet["location"]
    # The canonical spelling is qualify.py's `_location` spelling exactly:
    assert decoded == shapes.ObservationEvidence(
        f"store:{location['store_id']}:{location['relative_path']}", facet["event_token"]
    )


def test_a_record_under_the_wrong_path_or_name_is_undecodable(sample_act_report) -> None:
    payload = node_to_markdown(stored.act_report_node(sample_act_report)).encode("utf-8")
    identity = sample_act_report.identity()
    with pytest.raises(RecordUndecodable):
        evidence.decode_record(f"run/{identity}.md", payload)  # wrong namespace
    with pytest.raises(RecordUndecodable):
        evidence.decode_record("act-report/" + "0" * 64 + ".md", payload)  # wrong name


def test_a_malformed_act_report_entry_is_undecodable(sample_act_report) -> None:
    from nodes.core.frontmatter import node_from_markdown

    node = stored.act_report_node(sample_act_report)
    node.facets["act-report"]["entries"].append({"kind": "not-an-entry"})
    node.facets["semantic-identity"] = {"digest": stored.recompute_semantic_hash(node)}
    payload = node_to_markdown(node).encode("utf-8")
    with pytest.raises(RecordUndecodable):  # the full validator, not a two-field read
        evidence.decode_record(f"act-report/{node.id.split(':', 1)[1]}.md", payload)


def test_garbage_bytes_are_undecodable() -> None:
    with pytest.raises(RecordUndecodable):
        evidence.decode_record("run/x.md", b"\xff not markdown")


def test_record_layout_path_matches_exactly_the_three_namespaces() -> None:
    assert evidence.record_layout_path("run/" + "a" * 64 + ".md")
    assert evidence.record_layout_path("act-report/x.md")
    assert evidence.record_layout_path("holdings-observation/x.md")
    assert not evidence.record_layout_path("corpus.yaml")
    assert not evidence.record_layout_path("proposition/x.md")
    assert not evidence.record_layout_path("run/x.txt")
```

(`sample_act_report` is a pytest wrapper over
`closure_fixtures.sample_report()`; `assessment_closure` over
`closure_fixtures.make_closure()`; the observation node builds through
`stored.holdings_observation_node` with a
`records.holdings_observation` value — reuse the value builders in
`tests/test_holdings_stored.py`.)

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement**

`errors.py`, beside `MalformedRecord`:

```python
class RecordUndecodable(RecordError):
    """Captured published-record bytes that cannot be read as the named
    publication. A qualification state (the pointer is unresolvable),
    never a chain verdict and never propagated out of the evaluator."""
```

`evidence.py`:

```python
"""Captured record bytes -> the evidence values the shapes match on."""

from __future__ import annotations

from nodes.core.errors import NodesError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.node import Node
from yaml import YAMLError

from science import runrecord, stored
from science.errors import CanonicalTextRefused, MalformedRecord, RecordUndecodable
from science.intents.shapes import (
    InertRecord,
    ObservationEvidence,
    ReportEvidence,
    RunEvidence,
)
from science.world.records import RECORD_NAMESPACES

__all__ = ["decode_record", "record_layout_path"]


def record_layout_path(path: str) -> bool:
    return path.endswith(".md") and any(
        path.startswith(namespace + "/") for namespace in RECORD_NAMESPACES
    )


def decode_record(path: str, payload: bytes) -> RunEvidence | ReportEvidence | ObservationEvidence | InertRecord:
    try:
        node = node_from_markdown(payload.decode("utf-8"))
    except (UnicodeDecodeError, NodesError, YAMLError, ValueError) as caught:
        raise RecordUndecodable(f"{path}: {caught}") from caught
    try:
        if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):
            raise RecordUndecodable(f"{path}: the semantic stamp does not agree with the stored fields")
    except IdentityError as caught:
        # A stamp whose recomputation cannot even encode is unreadable.
        raise RecordUndecodable(f"{path}: the semantic projection is not encodable: {caught}") from caught
    # The path↔kind↔id binding: the captured path names the publication, so
    # a valid record stored under another namespace or name is not the
    # named publication (§2.6's decode-verifies-identity rule, generalized).
    kind, _, slug = node.id.partition(":")
    if not slug or path != f"{kind}/{slug}.md":
        raise RecordUndecodable(f"{path}: the record id {node.id!r} does not name this path")
    if node.kind != kind:
        raise RecordUndecodable(f"{path}: the record kind {node.kind!r} disagrees with its id")
    if node.kind == "run":
        try:
            publication = runrecord.decode_run_record(node)
        except (MalformedRecord, CanonicalTextRefused) as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if publication is None:
            return InertRecord()  # legacy: readable, never qualifying
        return RunEvidence(publication.shape, publication.spec_identity, publication.event_token)
    if node.kind == "act-report":
        # The FULL validator — extracted from the writer (corpus.py:1399),
        # never a two-field read: exact facet keys, operation vocabulary,
        # entries member by member, no relations, id == identity digest.
        try:
            facet = stored.act_report_facet(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        return ReportEvidence(str(facet["operation"]), str(facet["event_token"]))
    if node.kind == "holdings-observation":
        # The exact typed reader (stored.py:390) with its facet round-trip
        # equality, plus the id↔identity binding the reader leaves to us.
        try:
            value = stored.holdings_observation_value(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if node.id != f"holdings-observation:{value.identity()}":
            raise RecordUndecodable(f"{path}: the observation id disagrees with its identity")
        return ObservationEvidence(
            f"store:{value.location.store_id}:{value.location.relative_path}",
            value.event_token,
        )
    return InertRecord()
```

(The `store:<id>:<path>` spelling must match `qualify.py`'s
`_location`; assert equality against
`decode_holdings_intent`'s output in a test. Check `StoreLocator`'s
field names against `science/holdings/records.py` before writing the
last block. `IdentityError` joins the imports from `science.errors`.)

The `stored.py` extraction: move `_REPORT_ENTRY_OUTCOMES`,
`_valid_report_entry`, and the body of
`_refuse_malformed_act_report` into

```python
def act_report_facet(node: Node) -> Mapping[str, Any]:
    """The one act-report record validator — the writer's checks
    (formerly CorpusWriter._refuse_malformed_act_report), raised as
    MalformedRecord, returning the validated facet."""
```

with `corpus.py`'s method becoming a delegation that wraps
`MalformedRecord` in `ValidationRefused` — assertions and message
content unchanged, so the corpus writer tests keep passing byte-for-byte
on their match patterns (adjust only if a test matches the exception
class name).

- [ ] **Step 4: Run to verify pass, then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/intents/evidence.py python/src/science/errors.py \
        python/src/science/stored.py python/src/science/corpus.py \
        python/tests/test_intent_evidence.py docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(intents): captured-record evidence decoding and the extracted act-report validator"
```

---

### Task 9: The qualification reducer (`science/intents/reduce.py`)

**Files:**
- Create: `python/src/science/intents/reduce.py`
- Modify: `python/src/science/intents/__init__.py` (exports)
- Test: `python/tests/test_intent_reduce.py` (new)

**Interfaces:**
- Consumes: `logmodel` entry views (`IntentEntryView`,
  `RegisteredEntryView`, `SettledEntryView`), `shapes.decode_intent`,
  `shapes.mismatch`, `shapes.REASON_PRIORITY`,
  `evidence.decode_record`, `evidence.record_layout_path`,
  `corpus.Finding`.
- Produces (Task 10 relies on these exact names):

```python
@sealed
@final
@dataclass(frozen=True, slots=True)
class IntentQualification:
    digest: str
    shape: Literal["assessment-run", "operation", "holdings"] | None
    status: Literal["matched", "unresolvable", "attempt-without-recorded-outcome", "unrecognized"]
    fulfilled_by: str | None
```

  and `qualify_chain(entries: tuple[EntryView, ...],
  records: Mapping[str, bytes], *,
  state_facts: Callable[[object], tuple[tuple[str, str], ...]]) ->
  tuple[tuple[IntentQualification, ...], tuple[Finding, ...]]` — one
  row per `IntentEntryView` in chain order (total accounting), findings
  in the pinned §3.3 order: per intent, the gate finding, or the
  attempt finding followed by that intent's non-qualifying findings in
  registration chain order; `matched` and `unresolvable` emit nothing.
  `state_facts` is the seam's engine-owned state codec
  (`LogSeam.state_facts`, wired at `root.py:1493`): only a final row
  whose facts say `("kind", "file")` names published bytes — the
  holdings interior's `_file` rule (`qualify.py:72`), now general — so
  an absent or deleted final row is the resolved `no-record` case and
  never reads whatever bytes a later write left at that path.

- [ ] **Step 1: Write the failing tests** — drive the precedence with
  fabricated entry views and real record bytes (the Task 2 closure
  fixtures produce run payloads; `stored.act_report_node` /
  `holdings_observation_node` the other two kinds). The builders, in
  full, at the top of `test_intent_reduce.py`:

```python
from dataclasses import dataclass

from science.identity import v1
from science.intents.reduce import IntentQualification, qualify_chain
from science.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView


@dataclass(frozen=True)
class FakeFile:
    tag: str


ABSENT_ROW = object()


def _facts(state: object) -> tuple[tuple[str, str], ...]:
    return (("kind", "file"),) if type(state) is FakeFile else (("kind", "absent"),)


def _assessment_payload(spec: str = "s" * 64, token: str = "tok") -> bytes:
    return v1.encode({"spec_identity": spec, "event_token": token, "actor": "a"})


def _production_payload(token: str = "tok") -> bytes:
    return v1.encode({"kind": "run-attempt", "event_token": token, "actor": "a"})


def _intent(digest: str, payload: bytes) -> IntentEntryView:
    return IntentEntryView(digest=digest, payload=payload)


def _registration(digest: str, fulfills: str, *files: str, absent: tuple[str, ...] = ()) -> RegisteredEntryView:
    final = tuple((path, FakeFile(path)) for path in files) + tuple((path, ABSENT_ROW) for path in absent)
    return RegisteredEntryView(digest=digest, txid="tx-" + digest, initial=(), final=final, fulfills=fulfills)


def _settled(registration: str, committed: bool = True) -> SettledEntryView:
    return SettledEntryView(digest="s-" + registration, txid="tx-" + registration,
                            registration=registration, committed=committed)


def _qualify(entries, records):
    return qualify_chain(tuple(entries), records, state_facts=_facts)
```

and the bodies (`run_path`/`run_bytes` come from a Task 2 closure
fixture whose intent token is `"tok"` and spec is `"s" * 64` — i.e.
`_, run_path, (op,) = runrecord.publication_plan(closure, produces=None)`
with `run_bytes = op.content`):

```python
def test_no_pointers_reads_attempt_without_recorded_outcome() -> None:
    rows, findings = _qualify([_intent("i1", _assessment_payload())], {})
    assert rows == (IntentQualification("i1", "assessment-run", "attempt-without-recorded-outcome", None),)
    assert [f.code for f in findings] == ["intent-attempt-without-recorded-outcome"]
    assert findings[0].ref == "i1"


def test_matched_by_run_publication_sets_fulfilled_by(run_path, run_bytes) -> None:
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", run_path), _settled("r1")]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows == (IntentQualification("i1", "assessment-run", "matched", "r1"),)
    assert findings == ()


def test_every_resolved_non_qualifying_pointer_is_named_with_its_reason(
    run_path, run_bytes, observation_path, observation_bytes, wrong_spec_run_path, wrong_spec_run_bytes
) -> None:
    # u2's family: wrong-purpose (an observation for a run intent),
    # wrong-spec, wrong-token, and a committed publication creating no
    # record. Findings after the attempt finding, registration chain order.
    entries = [
        _intent("i1", _assessment_payload(token="other")),   # nothing carries "other"
        _registration("r1", "i1", observation_path), _settled("r1"),
        _registration("r2", "i1", wrong_spec_run_path), _settled("r2"),
        _registration("r3", "i1", run_path), _settled("r3"),
        _registration("r4", "i1"), _settled("r4"),
    ]
    records = {observation_path: observation_bytes,
               wrong_spec_run_path: wrong_spec_run_bytes, run_path: run_bytes}
    rows, findings = _qualify(entries, records)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert [(f.code, f.ref) for f in findings] == [
        ("intent-attempt-without-recorded-outcome", "i1"),
        ("intent-fulfillment-non-qualifying", "r1"),
        ("intent-fulfillment-non-qualifying", "r2"),
        ("intent-fulfillment-non-qualifying", "r3"),
        ("intent-fulfillment-non-qualifying", "r4"),
    ]
    assert "reason=wrong-purpose" in findings[1].detail
    assert "reason=wrong-spec" in findings[2].detail
    assert "reason=wrong-token" in findings[3].detail
    assert "reason=no-record" in findings[4].detail
    assert all(f"intent=i1" in f.detail for f in findings[1:])


def test_unresolvable_wins_over_non_qualifying_and_emits_nothing(run_path) -> None:
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", run_path), _settled("r1"),      # bytes absent
               _registration("r2", "i1"), _settled("r2")]                # resolved, no record
    rows, findings = _qualify(entries, {})
    assert rows == (IntentQualification("i1", "assessment-run", "unresolvable", None),)
    assert findings == ()  # §6: no unmatched finding on the unresolvable branch


def test_undecodable_bytes_are_unresolvable(run_path) -> None:
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", run_path), _settled("r1")]
    rows, findings = _qualify(entries, {run_path: b"\xffgarbage"})
    assert rows[0].status == "unresolvable" and findings == ()


def test_unsettled_pointer_is_unresolvable_regardless_of_disk(run_path, run_bytes) -> None:
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", run_path)]  # no settlement entry
    rows, _ = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "unresolvable"  # never matched from disk state


def test_rolled_back_only_pointers_read_attempt_without_recorded_outcome(run_path, run_bytes) -> None:
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", run_path), _settled("r1", committed=False)]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "attempt-without-recorded-outcome"  # nothing toward unresolvable
    assert [f.code for f in findings] == [
        "intent-attempt-without-recorded-outcome", "intent-fulfillment-non-qualifying",
    ]


def test_an_absent_final_row_never_reads_present_bytes(run_path, run_bytes) -> None:
    # The holdings interior's _file rule at the general width: the final
    # row's state is absent (a delete), yet bytes exist at that path in the
    # capture (a later transaction's record). The pointer published no
    # record — resolved no-record, never a match on another write's bytes.
    entries = [_intent("i1", _assessment_payload()),
               _registration("r1", "i1", absent=(run_path,)), _settled("r1")]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in findings[1].detail


def test_unrecognized_rows_carry_the_gate_finding_and_none_reduce() -> None:
    entries = [
        _intent("i1", v1.encode({"domain": "science.other.v1"})),
        _intent("i2", b"{}"),
        _intent("i3", v1.encode({"kind": "import", "event_token": "", "actor": "a"})),
    ]
    rows, findings = _qualify(entries, {})
    assert [row.status for row in rows] == ["unrecognized"] * 3  # total, chain order
    assert [row.shape for row in rows] == [None] * 3
    assert [(f.code, f.severity) for f in findings] == [
        ("intent-domain-unrecognized", "warning"),
        ("intent-domain-unrecognized", "warning"),
        ("intent-payload-malformed", "error"),
    ]


def test_wrong_shape_both_directions(run_path, run_bytes, production_run_path, production_run_bytes) -> None:
    # label 8 at the reducer's level: shapes share one token space, so a
    # token match alone never qualifies.
    entries = [_intent("i1", _production_payload()),                       # wants dataset-production
               _registration("r1", "i1", run_path), _settled("r1")]       # assessment-shaped run
    _, findings = _qualify(entries, {run_path: run_bytes})
    assert "reason=wrong-shape" in findings[1].detail
    entries = [_intent("i2", _assessment_payload()),                      # wants assessment
               _registration("r2", "i2", production_run_path), _settled("r2")]
    _, findings = _qualify(entries, {production_run_path: production_run_bytes})
    assert "reason=wrong-shape" in findings[1].detail
```

The fixtures `run_path`/`run_bytes`, `wrong_spec_run_path`/…,
`production_run_path`/…, `observation_path`/`observation_bytes` are
module fixtures built once from `closure_fixtures.make_closure` (spec
`"s"*64` vs `"x"*64`, token `"tok"`, shape per name) and from
`stored.holdings_observation_node` over a `holdings_observation` value
with token `"tok"` — each returning
`(path, op.content)` from `publication_plan` /
`(f"holdings-observation/{identity}.md", node_to_markdown(node).encode())`.

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement**

```python
"""Log §6's one qualification reduction (spec §2.1, §3.3)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, final

from science.corpus import Finding
from science.errors import RecordUndecodable
from science.intents import evidence as evidence_module
from science.intents import shapes
from science.sealed import sealed
from science.world.logmodel import (
    EntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
)

__all__ = ["IntentQualification", "qualify_chain"]


@sealed
@final
@dataclass(frozen=True, slots=True)
class IntentQualification:
    digest: str
    shape: Literal["assessment-run", "operation", "holdings"] | None
    status: Literal["matched", "unresolvable", "attempt-without-recorded-outcome", "unrecognized"]
    fulfilled_by: str | None


StateFacts = Callable[[object], tuple[tuple[str, str], ...]]


def _is_file(facts: tuple[tuple[str, str], ...]) -> bool:
    # The holdings interior's `_file` rule (qualify.py:72), verbatim at the
    # general width: only a final row whose state is a file names published
    # bytes. An absent or deleted final row never reads whatever bytes a
    # later transaction left at that path.
    return any(pair[0] == "kind" and pair[1] == "file" for pair in facts)


def qualify_chain(
    entries: tuple[EntryView, ...],
    records: Mapping[str, bytes],
    *,
    state_facts: StateFacts,
) -> tuple[tuple[IntentQualification, ...], tuple[Finding, ...]]:
    settlement = {
        entry.registration: entry.committed
        for entry in entries
        if type(entry) is SettledEntryView
    }
    pointers: dict[str, list[RegisteredEntryView]] = {}
    for entry in entries:
        if type(entry) is RegisteredEntryView and entry.fulfills is not None:
            pointers.setdefault(entry.fulfills, []).append(entry)

    rows: list[IntentQualification] = []
    findings: list[Finding] = []
    for entry in entries:
        if type(entry) is not IntentEntryView:
            continue
        gate = shapes.decode_intent(entry.digest, entry.payload)
        if type(gate) is shapes.Unrecognized:
            rows.append(IntentQualification(entry.digest, None, "unrecognized", None))
            findings.append(
                Finding(
                    severity=gate.severity,
                    code=gate.code,
                    ref=entry.digest,
                    detail=gate.detail,
                    message="the intent payload fits no shape of the closed union"
                    if gate.code == "intent-domain-unrecognized"
                    else "a discriminator-matched payload fails its shape's schema",
                )
            )
            continue
        row, intent_findings = _qualify_one(
            gate, pointers.get(entry.digest, []), settlement, records, state_facts
        )
        rows.append(row)
        findings.extend(intent_findings)
    return tuple(rows), tuple(findings)


def _qualify_one(
    intent: shapes.DecodedIntent,
    registrations: list[RegisteredEntryView],
    settlement: Mapping[str, bool],
    records: Mapping[str, bytes],
    state_facts: StateFacts,
) -> tuple[IntentQualification, tuple[Finding, ...]]:
    unresolved = False
    non_qualifying: list[tuple[str, str]] = []  # (registration digest, reason class)
    for registration in registrations:
        committed = settlement.get(registration.digest)
        if committed is None:
            unresolved = True  # §2.1: settlement is never inferred from disk
            continue
        if not committed:
            non_qualifying.append((registration.digest, "no-record"))  # rolled back: resolved, publishes nothing
            continue
        record_paths = [
            path
            for path, state in registration.final
            if evidence_module.record_layout_path(path) and _is_file(state_facts(state))
        ]
        if not record_paths:
            # No file-state record row: the registration published no record
            # (a non-file or deleted final row names no published bytes).
            non_qualifying.append((registration.digest, "no-record"))
            continue
        reasons: list[str] = []
        pointer_unresolved = False
        for path in record_paths:
            payload = records.get(path)
            if payload is None:
                pointer_unresolved = True  # absent — including withheld by capture
                continue
            try:
                record_evidence = evidence_module.decode_record(path, payload)
            except RecordUndecodable:
                pointer_unresolved = True
                continue
            reason = shapes.mismatch(intent, record_evidence)
            if reason is None:
                return (
                    IntentQualification(intent.digest, intent.shape, "matched", registration.digest),
                    (),
                )
            reasons.append(reason)
        if pointer_unresolved:
            unresolved = True  # decayed bytes are not evidence of no outcome
            continue
        chosen = min(reasons, key=shapes.REASON_PRIORITY.index) if reasons else "no-record"
        non_qualifying.append((registration.digest, chosen))
    if unresolved:
        return IntentQualification(intent.digest, intent.shape, "unresolvable", None), ()
    row = IntentQualification(intent.digest, intent.shape, "attempt-without-recorded-outcome", None)
    findings = [
        Finding(
            severity="warning",
            code="intent-attempt-without-recorded-outcome",
            ref=intent.digest,
            detail="",
            message="a durable intent whose every pointer fully resolves and none qualifies",
        )
    ]
    findings.extend(
        Finding(
            severity="warning",
            code="intent-fulfillment-non-qualifying",
            ref=registration_digest,
            detail=f"intent={intent.digest} reason={reason}",
            message="a committed fulfillment that does not qualify its intent",
        )
        for registration_digest, reason in non_qualifying
    )
    return row, tuple(findings)
```

**Precedence note (test it, don't re-derive it):** matched wins
immediately; else any unresolvable pointer (unsettled, absent record
path, undecodable bytes) makes the intent `unresolvable` with **no**
findings; only when every pointer fully resolves and none qualifies do
the attempt finding and the per-pointer findings emit. A registration
whose record path was **withheld** by capture is indistinguishable from
absent here — that is §3.1's rule, by construction.

- [ ] **Step 4: Run to verify pass, then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/intents/ python/tests/test_intent_reduce.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(intents): the one qualification reduction with pinned findings"
```

---

### Task 10: The verifier lift (`science/world/verify.py`)

**Files:**
- Modify: `python/src/science/world/verify.py` — `LogReport` (line 871),
  `_report` (line 893), `evaluate_log` (line 909),
  `_assemble_evaluation_inputs` (line 1509), the arrival assembly
  (line ~1773), `_restore_root` (line 1578)
- Modify: `python/tests/test_world_log_evaluator.py`,
  `python/tests/test_world_arrival.py`, and every test constructing
  `LogReport` or calling `evaluate_log` (grep
  `intents_unevaluated\|evaluate_log(`)
- Test: extend `python/tests/test_world_log_evaluator.py`

**Interfaces:**
- Produces: `LogReport.qualification: tuple[IntentQualification, ...]`
  replacing `intents_unevaluated` (no alias); `evaluate_log(subject,
  view, observers, disk, records, presented, absent_state, state_facts,
  history=None)` — `records: tuple[tuple[str, bytes], ...]`, required,
  no defaulted-empty overload; `state_facts` the seam's engine-owned
  state codec, required for the same reason (every caller passes
  `seam.state_facts`; the production seam wires it at `root.py:1493`,
  and a test seam that fabricates states supplies its own);
  `_assemble_evaluation_inputs` returns `(view, disk, records,
  presented)` and captures records **under the caller's hold**, after
  `seam.capture`.
- Carriage: populated on every well-formed exit **including** the
  genesis-form `malformed` exit and the pending exit; empty on
  `MalformedView` and `AbsentView` (no entries to inventory).
  Placement: qualification findings appended **last** on every exit
  that carries `qualification`.

- [ ] **Step 1: Write the failing tests** — extend
  `tests/test_world_log_evaluator.py`, whose builders are `genesis()`,
  `registration(digest, txid)`, `settlement(...)`, `chain(*entries,
  pending=...)`, `corpus_chain()`, `record_carrier(head)`,
  `observers(*carriers)`, and the `evaluate(...)` wrapper (line 248).
  Extend two builders in place: `registration` gains
  `fulfills: str | None = None` and `final: tuple = ()` pass-throughs,
  and `evaluate` gains keyword-only `records: tuple = ()` and
  `state_facts=_facts` (the same `FakeFile`/`_facts` pair Task 9's
  test file defines — import them from `test_intent_reduce`). The
  wrapper's calling convention is the file's own: positional
  `(subject, view, observer_set)` with everything else keyword —
  every call below passes `CorpusSubject(CORPUS_ID)` first, and
  presented identities are the module's `verify.PresentedManifest`.
  New tests, in a `TestQualification` class:

```python
from test_intent_reduce import FakeFile, _assessment_payload, _facts

INTENT = IntentEntryView(digest="i1", payload=_assessment_payload())
FOREIGN = IntentEntryView(digest="i2", payload=v1.encode({"domain": "science.other.v1"}))


class TestQualification:
    def test_qualification_is_total_and_in_chain_order(self) -> None:
        view = chain(genesis(), INTENT, FOREIGN)
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(view.tip)))
        assert [row.digest for row in report.qualification] == ["i1", "i2"]
        assert report.qualification[0].status == "attempt-without-recorded-outcome"
        assert report.qualification[1].status == "unrecognized"
        assert report.outcome == "validated"  # never moved by qualification

    def test_qualification_findings_are_appended_last(self) -> None:
        # A presented manifest naming another corpus id yields a
        # subject-mismatch finding on the validated exit (the file's
        # TestSubjectMismatch construction) — a guaranteed non-qualification
        # finding, so the ordering claim is never vacuous.
        view = chain(genesis(), INTENT, FOREIGN)
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(view.tip)),
                          presented=verify.PresentedManifest(corpus_id="someone-else"))
        assert report.outcome == "validated"  # qualification moved nothing
        qual_codes = {"intent-attempt-without-recorded-outcome", "intent-domain-unrecognized",
                      "intent-fulfillment-non-qualifying", "intent-payload-malformed"}
        positions = [index for index, f in enumerate(report.findings) if f.code in qual_codes]
        others = [index for index, f in enumerate(report.findings) if f.code not in qual_codes]
        assert positions, "the two intents must produce qualification findings"
        assert others, "the presented mismatch must produce a non-qualification finding"
        assert all(p > o for p in positions for o in others)
        assert positions == sorted(positions)  # inventory order within the block

    def test_pending_exit_carries_qualification(self) -> None:
        # §2.1 / label 5: the registration is unsettled and its published
        # bytes are a GENUINELY MATCHING run publication — so a reducer that
        # inferred settlement from disk would read "matched", and the arm is
        # falsifiable. Outcome is unresolvable at step 3 either way.
        from closure_fixtures import make_closure
        from science.runrecord import publication_plan

        _, run_path, (op,) = publication_plan(make_closure(), produces=None)
        pointer = registration("r1", "tx-1", fulfills="i1",
                               final=((run_path, FakeFile("x")),))
        view = chain(genesis(), INTENT, pointer, pending=(("tx-1", "r1"),))
        report = evaluate(CorpusSubject(CORPUS_ID), view,
                          observers(record_carrier(view.tip)),
                          records=((run_path, op.content),))
        assert report.outcome == "unresolvable"
        assert report.qualification[0].status == "unresolvable"  # never matched from disk
        assert not [f for f in report.findings if f.code.startswith("intent-fulfillment")]

    def test_genesis_malformed_exit_carries_qualification(self) -> None:
        view = chain(genesis(payload=b"not the corpus genesis payload"), INTENT)
        report = evaluate(CorpusSubject(CORPUS_ID), view, observers(record_carrier(view.tip)))
        assert report.outcome == "malformed"
        assert [row.digest for row in report.qualification] == ["i1"]  # carried even here

    def test_malformed_view_exit_carries_empty_qualification(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID),
                          MalformedView(DefectView("cycle", "d1", "detail")), observers())
        assert report.outcome == "malformed"
        assert report.qualification == ()  # no entries to inventory

    def test_records_is_required_and_typed(self) -> None:
        with pytest.raises(TypeError):
            evaluate_log(CorpusSubject(CORPUS_ID), corpus_chain(), observers(), (),
                         "not-a-tuple", None, ABSENT, _facts)

    def test_intents_unevaluated_is_retired_with_no_alias(self) -> None:
        report = evaluate(CorpusSubject(CORPUS_ID), corpus_chain(), observers())
        assert not hasattr(report, "intents_unevaluated")
```

(If the malformed-genesis payload literal above does not produce the
genesis-form defect, reuse the file's existing genesis-defect
construction from `TestStructure` — the assertion stays as written.)

- [ ] **Step 2: Run to verify failure** (TypeError on arity — the new
  parameter).

- [ ] **Step 3: Implement**

- `LogReport`: replace the `intents_unevaluated` field with
  `qualification: tuple[IntentQualification, ...]` (import from
  `science.intents.reduce`); rewrite the docstring sentence: the
  qualification **is** made, one row per intent, total.
- `_report`: parameter `intents` becomes
  `qualification: tuple[IntentQualification, ...] = ()`, and gains
  `qual_findings: tuple[Finding, ...] = ()`; the constructed report's
  findings member is spelled exactly `findings + qual_findings` (once —
  it is J6's sabotage anchor), so qualification findings land last on
  every exit that carries them.
- `evaluate_log`: signature gains `records` after `disk` and
  `state_facts` after `absent_state`, with

```python
    if type(records) is not tuple:
        raise TypeError("records is the captured published-record surface as a tuple of (path, payload) pairs")
    if not callable(state_facts):
        raise TypeError("state_facts is the seam's engine-owned state codec")
```

  After the `WellFormedView` check, replace the `intents = ...` line:

```python
    qualification, qual_findings = qualify_chain(view.entries, dict(records), state_facts=state_facts)
```

  Every `_report(...)` call on a well-formed view passes
  `qualification=qualification, qual_findings=qual_findings` (the
  genesis-defect exit included); the `MalformedView` and `AbsentView`
  exits pass neither (empty defaults). No other phase's findings move.
- `_assemble_evaluation_inputs`:

```python
    view = seam.inspect_registered(root)
    presented = _presented_identity(config, kind, root)
    disk = seam.capture(root, registered_surface_paths(root, kind))
    records = capture_records(root, kind)  # same hold: the caller's
    return view, disk, records, presented
```

- `_audit_log`, `_restore_root`, and the arrival assembly at ~1773
  thread `records` and `seam.state_facts` through to `evaluate_log`.
  The arrival site captures with `capture_records(root, "corpus")`
  inside its existing hold. Any test-constructed `LogSeam` that leaves
  `state_facts` unwired and reaches qualification over a committed
  registration will hit `_unwired_state_facts`'s loud refusal — wire a
  fake at those sites, never a default.
- Update every test naming the retired field or calling `evaluate_log`
  (the grep list from the Files section) in this same task — for tests
  with no record surface, pass `records=()` **explicitly** at each
  call site (the parameter stays required), and a `state_facts` fake
  where the test fabricates states.

- [ ] **Step 4: Run the evaluator/audit/arrival/replay/restore test
  files, then cut8–cut10 acceptance on the certified volume, then the
  gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/world/verify.py python/tests/ \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(verify): evaluated qualification replaces intents_unevaluated"
```

---

### Task 11: The completion re-base (`science/report.py`)

**Files:**
- Modify: `python/src/science/report.py` (`completion`, line 405)
- Test: `python/tests/test_report.py` or wherever `completion` is
  covered (grep `completion(`), plus new cases

**Interfaces:**
- Produces: `completion(intent, registrations, held) -> str` — signature
  and vocabulary unchanged (`CLOSED`/`INDETERMINATE`/`UNFINISHED`); the
  per-pointer judgment is now `shapes.mismatch` over held-value
  evidence. The vocabulary is a projection: `CLOSED` is matched,
  `INDETERMINATE` is unresolvable (a pointer whose held value is
  absent), `UNFINISHED` is every-pointer-resolved-none-qualifying.
- Pinned tightening (cut label 12): a wrong-spec run closure that read
  `CLOSED` before reads `UNFINISHED` after; an assessment-shaped
  closure fulfilling a `run-attempt` operation intent likewise.

- [ ] **Step 1: Write the failing tests**

```python
from closure_fixtures import make_closure, sample_report  # Task 2's shared module


def test_wrong_spec_run_closure_reads_unfinished() -> None:
    # The closure's spec_identity ("s" * 64) differs from the intent's;
    # token matches — the §2.5 pin: CLOSED before the re-base, UNFINISHED after.
    closure = make_closure()
    intent = AssessmentRunIntent("b" * 64, closure.occurrence.event_token, "actor")
    registrations = (Registration(intent.event_token, closure.address()),)
    assert completion(intent, registrations, {closure.address(): closure}) == UNFINISHED


def test_assessment_shaped_closure_never_closes_a_production_intent() -> None:
    closure = make_closure()
    intent = OperationIntent("run-attempt", closure.occurrence.event_token, "actor")
    registrations = (Registration(intent.event_token, closure.address()),)
    assert completion(intent, registrations, {closure.address(): closure}) == UNFINISHED


def test_existing_vocabulary_is_preserved() -> None:
    # The projection: CLOSED is matched, INDETERMINATE is a pointer whose
    # held value is absent, UNFINISHED is every-pointer-resolved-none-qualifying.
    report = sample_report(operation="run-attempt", token="tok")
    intent = OperationIntent("run-attempt", "tok", "actor")
    registrations = (Registration("tok", "pointer"),)
    assert completion(intent, registrations, {"pointer": report}) == CLOSED
    assert completion(intent, registrations, {}) == INDETERMINATE
    other = OperationIntent("audit", "tok", "actor")
    assert completion(other, registrations, {"pointer": report}) == UNFINISHED
```

- [ ] **Step 2: Run to verify failure** (the wrong-spec case currently
  returns `CLOSED`).

- [ ] **Step 3: Implement** — replace the matching body of `completion`:

```python
    from science.intents import shapes  # local: intents imports report

    decoded = shapes.DecodedIntent(
        "held",
        "assessment-run" if type(intent) is AssessmentRunIntent else "operation",
        intent,
    )
    unresolved = False
    for registration in registrations:
        if registration.intent_token != intent.event_token:
            continue
        if registration.pointer not in held:
            unresolved = True
            continue
        value = held[registration.pointer]
        if type(value) is ActReport:
            held_evidence: object = shapes.ReportEvidence(value.operation, value.event_token)
        elif type(value) is RunClosure:
            held_evidence = shapes.RunEvidence(
                value.recipe.shape, value.recipe.spec_identity, value.occurrence.event_token
            )
        else:
            held_evidence = shapes.InertRecord()
        if shapes.mismatch(decoded, held_evidence) is None:
            return CLOSED
    return INDETERMINATE if unresolved else UNFINISHED
```

After this task the shape predicates are the only implementation of
qualification anywhere in Science; the verifier, the holdings rule, and
`completion` are callers.

- [ ] **Step 4: Run to verify pass; run cut8–cut10 acceptance
  (report.py is act-report authority), then the gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/src/science/report.py python/tests/ \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "feat(report): re-base completion onto the shared shape predicates"
```

---

### Task 12: Three-site consumer agreement and the label-12 matrix

**Files:**
- Test: `python/tests/test_consumer_agreement.py` (new; durable where
  the verifier consumer needs a real chain — reuse the holdings
  capture/reduce fixtures from `tests/test_holdings_reduce.py` and
  `tests/test_holdings_capture.py`)

**Interfaces:**
- Consumes: everything landed above; produces no new API. This is cut
  label 12's executable half: the verifier, the regenerated holdings
  rule, and `completion` answer identically over the same evidence for
  every shape each consumer reads.

- [ ] **Step 1: Write the failing (or first-run-green, ledger-pinned)
  matrix tests**

Re-run cut 10's holdings qualification matrix through **both** holdings
consumers over the regenerated interior. The rule side reuses
`tests/test_holdings_reduce.py`'s builders verbatim (`observation`,
`intent`, `registration`, `settlement`, `file_row`, `corpus`,
`capture`, `invoke`, and its `LOCATION`/`OTHER_LOCATION`/`REF_A`
constants — import them); its blocked projection reports a
non-qualified intent's location with reason `"unsettled"` (the
certified `test_unmatched_and_unresolved_intents_block_distinctly`
behavior). The verifier side runs `qualify_chain` over entry views and
records built to state the same facts:

```python
import pytest
from test_holdings_reduce import (
    LOCATION, OTHER_LOCATION, REF_A,
    capture, corpus, file_row, intent, invoke, observation, registration, settlement,
)
from test_intent_reduce import FakeFile, _facts
from science.identity import v1
from science.intents.reduce import qualify_chain
from science.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView

OBSERVATION_PATH = f"holdings-observation/{REF_A}.md"

# case -> (observation kwargs | None, registration/settlement shape, verifier status, rule blocks the location?)
MATRIX = {
    "matched": (dict(location=LOCATION, token="tok"), "settled-file", "matched", False),
    "unresolved-unsettled-registration": (dict(location=LOCATION, token="tok"), "unsettled", "unresolvable", True),
    "unresolved-settled-file-row-no-captured-record": (None, "settled-file", "unresolvable", True),
    "rolled-back": (dict(location=LOCATION, token="tok"), "rolled-back", "attempt-without-recorded-outcome", True),
    "wrong-location": (dict(location=OTHER_LOCATION, token="tok"), "settled-file", "attempt-without-recorded-outcome", True),
    "wrong-token": (dict(location=LOCATION, token="other"), "settled-file", "attempt-without-recorded-outcome", True),
    "no-observation": (None, "settled-no-record", "attempt-without-recorded-outcome", True),
}


@pytest.mark.parametrize("case", sorted(MATRIX))
def test_holdings_matrix_agrees_across_both_consumers(case, holdings_intent_payload) -> None:
    observation_kwargs, shape, verifier_status, rule_blocks = MATRIX[case]

    # --- the rule, over the regenerated interior -------------------------
    rows = [observation(REF_A, **observation_kwargs)] if observation_kwargs else []
    chain = [intent("1" * 64, location=LOCATION, token="tok")]
    final = [file_row(OBSERVATION_PATH)] if shape.startswith("settled-file") else []
    chain.append(registration("2" * 64, "1" * 64, final=final))
    if shape != "unsettled":
        outcome = "rolled-back" if shape == "rolled-back" else "committed"
        chain.append(settlement("3" * 64, "2" * 64, outcome=outcome))
    result = invoke(capture(corpus(chain=chain, records=rows)))
    blocked_locations = {row["location"] for row in result["blocked"]}
    assert (LOCATION in blocked_locations) is rule_blocks

    # --- the verifier, over the same facts -------------------------------
    entries = [IntentEntryView(digest="i1", payload=holdings_intent_payload(location=LOCATION, token="tok"))]
    records = {}
    if observation_kwargs:
        records[OBSERVATION_PATH] = observation_record_bytes(REF_A, **observation_kwargs)
    final = ((OBSERVATION_PATH, FakeFile("f")),) if shape.startswith("settled-file") else ()
    entries.append(RegisteredEntryView(digest="r1", txid="t1", initial=(), final=final, fulfills="i1"))
    if shape != "unsettled":
        entries.append(SettledEntryView(digest="s1", txid="t1", registration="r1",
                                        committed=shape != "rolled-back"))
    verifier_rows, _ = qualify_chain(tuple(entries), records, state_facts=_facts)
    assert verifier_rows[0].status == verifier_status
```

`holdings_intent_payload` builds the wire payload through
`science.holdings.boundary.intent_payload` (the real writer);
`observation_record_bytes` builds the stored record through
`science.holdings.records.holdings_observation` +
`stored.holdings_observation_node` + `node_to_markdown` with the same
location/token — both small fixtures written in this file, mapping
`LOCATION`'s `store:<id>:<path>` spelling back to its
store-id/relative-path parts with `LOCATION.split(":", 2)`. A
regenerated rule mishandling missing-record evidence fails the
`unresolved-settled-file-row-no-captured-record` row on the rule side;
a verifier diverging on any row fails the same test on its side.

And the run/operation agreement between verifier and `completion` — one
table, every §2.2 alternative and every sabotage:

```python
from science.report import (
    CLOSED, UNFINISHED, AssessmentRunIntent, OperationIntent, Registration, completion,
)


def _verifier_status(intent_payload, record_path, record_bytes):
    entries = (
        IntentEntryView(digest="i1", payload=intent_payload),
        RegisteredEntryView(digest="r1", txid="t1", initial=(),
                            final=((record_path, FakeFile("f")),), fulfills="i1"),
        SettledEntryView(digest="s1", txid="t1", registration="r1", committed=True),
    )
    rows, _ = qualify_chain(entries, {record_path: record_bytes}, state_facts=_facts)
    return rows[0].status


@pytest.mark.parametrize("held_intent,closure_fixture,expected", [
    # (the in-memory intent, which published closure/report fulfills it, CLOSED?)
    ("matching-assessment", "assessment", CLOSED),
    ("wrong-spec-assessment", "assessment", UNFINISHED),          # the §2.5 pin
    ("wrong-token-assessment", "assessment", UNFINISHED),
    ("production-run-attempt", "production", CLOSED),
    ("production-run-attempt", "assessment", UNFINISHED),          # wrong-shape
    ("matching-assessment", "run-attempt-report", CLOSED),
    ("non-run-import", "import-report", CLOSED),
    ("non-run-import", "audit-report", UNFINISHED),                # wrong-kind
])
def test_run_shapes_agree_between_verifier_and_completion(
    held_intent, closure_fixture, expected, agreement_case
) -> None:
    intent_value, wire_payload, held_value, record_path, record_bytes = agreement_case(
        held_intent, closure_fixture
    )
    held_answer = completion(
        intent_value, (Registration(intent_value.event_token, "pointer"),), {"pointer": held_value}
    )
    assert held_answer == expected
    status = _verifier_status(wire_payload, record_path, record_bytes)
    assert (status == "matched") is (expected == CLOSED)  # the two consumers agree
```

`agreement_case` is one fixture returning the five aligned values per
pair: the in-memory intent (`AssessmentRunIntent`/`OperationIntent`
with token `"tok"`, spec `"s" * 64` or `"x" * 64` per the sabotage),
its wire payload (`v1.encode` of its fields), the held value
(`closure_fixtures.make_closure` / `closure_fixtures.sample_report`
with the named operation), and the published bytes
(`runrecord.publication_plan` / `stored.act_report_node` +
`node_to_markdown`).

- [ ] **Step 2–4: Run, implement any divergence surfaced (a divergence
  is a bug in Tasks 5–11 — fix it there, never by widening the test),
  gate block.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/tests/test_consumer_agreement.py docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "test(intents): three-site consumer agreement and the label-12 matrix"
```

---

### Task 13: The 26 N2 declarations and the acceptance runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut11.py`
- Create: `python/tests/acceptance/test_n2_cut11.py` (copy the cut-10
  harness's structure)
- Create: `python/tests/acceptance/test_intent_boundary_acceptance.py`
  (the durable end-to-end arms that need the certified volume)
- Create: `python/tools/cut11_acceptance.py` (copy `cut10_acceptance.py`,
  point it at the cut-11 node ids)

**Interfaces:**
- Consumes: the whole slice. Every declared check must fail under its
  declared sabotage and pass on the real tree (the N2 discipline);
  fabrication well-formedness is asserted at declaration time (cut §5
  item 1).

- [ ] **Step 1: Author the declarations** — `13 selected + 13 labeled
  = 26 declaration units`, single-homed, in the harness's own shape
  (`n2_arms.py:50`): each `Arm(row, asserts, Sabotage(module, before,
  after), checks)` names exact test-function node ids that **all fail**
  under its one sabotage and pass without it; `before` must match its
  module **exactly once** (the strings below quote this plan's own
  implementation blocks — adjust only if the landed code differs, and
  record the adjustment in the ledger). A unit whose claim is an atoms
  production is a **citation**, not an arm; a check that must KEEP
  passing under a sabotage is a **co-passing independence node**, run
  by the harness audit, never listed in `checks`. The complete
  partition:

```python
CUT11_ARMS = (
    Arm("L7u1", "no pointers reads the attempt finding, never a refutation",
        Sabotage("intents/reduce.py",
                 before='code="intent-attempt-without-recorded-outcome",',
                 after='code="intent-attempt-withheld",'),
        ("test_intent_reduce.py::test_no_pointers_reads_attempt_without_recorded_outcome",)),
    # L7u2 — one arm per frozen family member, each with its own sabotage:
    Arm("L7u2a", "a wrong-purpose committed transaction fails qualification",
        Sabotage("intents/shapes.py",
                 before='return "wrong-purpose"\n    if isinstance(value, OperationIntent):',
                 after="return None\n    if isinstance(value, OperationIntent):"),
        ("acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_purpose_member",
         "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason")),
    Arm("L7u2b", "a run publication under another spec fails qualification",
        Sabotage("intents/shapes.py",
                 before="if evidence.spec_identity != value.spec_identity:",
                 after="if False:"),
        ("acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_spec_member",
         "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason")),
    Arm("L7u2c", "a run publication under another event token fails qualification",
        Sabotage("intents/shapes.py",
                 before='return "wrong-spec"\n            return None if evidence.event_token == value.event_token else "wrong-token"',
                 after='return "wrong-spec"\n            return None'),
        ("acceptance/test_intent_boundary_acceptance.py::test_u2_wrong_token_member",
         "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason")),
    Arm("L7u2d", "a publication creating no run fails qualification, named no-record",
        Sabotage("intents/reduce.py",
                 before='non_qualifying.append((registration.digest, "no-record"))\n            continue',
                 after="return (\n                IntentQualification(intent.digest, intent.shape, "
                       '"matched", registration.digest),\n                (),\n            )'),
        ("acceptance/test_intent_boundary_acceptance.py::test_u2_no_record_member",
         "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason")),
    Arm("L7u3", "decayed genuine bytes read unresolvable with no unmatched finding",
        Sabotage("intents/reduce.py",
                 before="except RecordUndecodable:\n                pointer_unresolved = True",
                 after='except RecordUndecodable:\n                reasons.append("no-record")'),
        ("acceptance/test_intent_boundary_acceptance.py::test_u3_decayed_genuine_run_is_unresolvable_silently",
         "test_intent_reduce.py::test_undecodable_bytes_are_unresolvable")),
    Arm("L7u4", "the assessment intent is durably appended before any member act",
        Sabotage("boundary.py",
                 before="intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)\n"
                        "    fulfills = port.append_intent(_intent_wire(intent))",
                 after="intent = AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)\n"
                       '    fulfills = "0" * 64  # append deferred'),
        ("test_run_persistence.py::test_kill_between_append_and_start_leaves_intent_only",)),
    Arm("L7u6", "publication through a root other than the intent's refuses",
        Sabotage("root.py", before="fulfills=self._fulfills,", after="fulfills=None,"),
        ("test_run_persistence.py::test_cross_root_publication_refuses",
         "test_run_persistence.py::test_assessment_sequence_appends_intent_then_publishes_fulfilling")),
    Arm("L7u7", "no caller-supplied fulfills path exists at the boundary",
        Sabotage("boundary.py",
                 before="def execute_assessment_run(\n    *,\n    spec: object,\n    port: OperationPort,",
                 after="def execute_assessment_run(\n    *,\n    fulfills: str | None = None,\n"
                       "    spec: object,\n    port: OperationPort,"),
        ("test_run_persistence.py::test_no_caller_supplied_fulfills_path_exists",)),
    Arm("L7u8", "a wholly discarded attempt is indistinguishable by construction",
        # The check's port RAISES a cancellation before any write (the port
        # contract is honored — nothing silently succeeds); untouched, the
        # pre-intent path leaves no durable trace at all. The sabotage's
        # premature append plants the intent the negative must not find.
        Sabotage("boundary.py",
                 before='refused = _refused("no-frozen-spec", subject, actor, observer, started_at)\n'
                        "        port.execute(_report_plan(refused.report))",
                 after='refused = _refused("no-frozen-spec", subject, actor, observer, started_at)\n'
                       '        port.append_intent(_intent_wire(AssessmentRunIntent("0" * 64, '
                       "refused.report.event_token, actor)))\n"
                       "        port.execute(_report_plan(refused.report))"),
        ("acceptance/test_intent_boundary_acceptance.py::test_u8_negative_discarded_attempt_is_indistinguishable",)),
    Arm("L7u9", "a report carrying another operation's token fails qualification",
        Sabotage("intents/shapes.py",
                 before='if evidence.operation != value.kind:\n                return "wrong-kind"\n'
                        '            return None if evidence.event_token == value.event_token else "wrong-token"',
                 after='if evidence.operation != value.kind:\n                return "wrong-kind"\n'
                       "            return None"),
        ("acceptance/test_intent_boundary_acceptance.py::test_u9_wrong_operation_token_fails_qualification",)),
    Arm("L7u10", "a report of the wrong kind fails qualification",
        Sabotage("intents/shapes.py",
                 before='if evidence.operation != value.kind:\n                return "wrong-kind"',
                 after='if False:\n                return "wrong-kind"'),
        ("acceptance/test_intent_boundary_acceptance.py::test_u10_wrong_kind_report_fails_qualification",
         "test_intent_gate.py::test_matching_requirements_per_shape")),
    Arm("L7u11", "a run publication never fulfills a non-run operation",
        Sabotage("intents/shapes.py",
                 before='return "wrong-purpose"  # a run publication never fulfills a non-run operation',
                 after="return (None if evidence.event_token == value.event_token else \"wrong-token\") "
                       "if type(evidence) is RunEvidence else \"wrong-purpose\""),
        ("acceptance/test_intent_boundary_acceptance.py::test_u11_run_for_non_run_operation_fails_qualification",
         "test_intent_gate.py::test_matching_requirements_per_shape")),
    Arm("L7u12", "a registration publishing no terminal record fails qualification",
        Sabotage("intents/reduce.py",
                 before='non_qualifying.append((registration.digest, "no-record"))\n            continue',
                 after="return (\n                IntentQualification(intent.digest, intent.shape, "
                       '"matched", registration.digest),\n                (),\n            )'),
        ("acceptance/test_intent_boundary_acceptance.py::test_u12_no_terminal_record_fails_qualification",
         "test_intent_reduce.py::test_every_resolved_non_qualifying_pointer_is_named_with_its_reason")),
    Arm("L7u13", "the operation intent is durably appended before its first act",
        Sabotage("boundary.py",
                 before='intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)\n'
                        "    fulfills = port.append_intent(_intent_wire(intent))",
                 after='intent = OperationIntent("run-attempt", secrets.token_hex(16), actor)\n'
                       '    fulfills = "0" * 64  # append deferred'),
        ("test_run_persistence.py::test_kill_between_append_and_start_leaves_intent_only_operation_kind",)),
    Arm("J1", "an absent record path is unresolvable, never silently resolved",
        Sabotage("intents/reduce.py",
                 before="if payload is None:\n                pointer_unresolved = True  "
                        "# absent — including withheld by capture\n                continue",
                 after="if payload is None:\n                continue"),
        ("test_intent_reduce.py::test_unresolvable_wins_over_non_qualifying_and_emits_nothing",)),
    Arm("J2", "the leaf is classified before any readable open, never followed",
        # One replacement deletes the classification AND opens by name with
        # follow semantics, O_NONBLOCK so the FIFO open cannot block: the
        # symlink arms capture outside bytes (path traversal follows), and
        # the FIFO arm captures b"" (EOF, no writers) — all three fail,
        # nothing hangs. (A /proc reopen of a symlink's O_PATH fd is ELOOP,
        # so mutating only the reopen would leave the symlink arms green.)
        Sabotage("world/records.py",
                 before='if not stat.S_ISREG(os.fstat(path_fd).st_mode):\n'
                        "                return None  # a symlink or fifo at the leaf: opened as itself, never read\n"
                        '            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)',
                 after='read_fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dir_fd)'),
        ("test_record_capture.py::test_swap_race_is_lost_by_the_attacker",
         "test_record_capture.py::test_leaf_symlink_is_classified_and_withheld",
         "test_record_capture.py::test_fifo_is_classified_never_opened_readable")),
    Arm("J3a", "the writer refuses an over-ceiling postimage before any write",
        Sabotage("root.py",
                 before="if isinstance(content, bytes) and len(content) > RECORD_CEILING:",
                 after="if isinstance(content, bytes) and len(content) > RECORD_CEILING * 1024:"),
        ("test_operation_port.py::test_oversized_postimage_refuses_before_any_write",)),
    Arm("J3b", "the reader withholds wholly, never hands a truncation to a decoder",
        Sabotage("world/records.py",
                 before="remaining = RECORD_CEILING + 1",
                 after="remaining = RECORD_CEILING"),
        ("test_record_capture.py::test_ceiling_boundary_exact_captures_one_over_withholds",)),
    Arm("J4", "the operation discriminator is closed over OPERATION_KINDS",
        Sabotage("intents/shapes.py",
                 before='if set(value) == {"kind", "event_token", "actor"} and value.get("kind") in OPERATION_KINDS:',
                 after='if set(value) == {"kind", "event_token", "actor"}:'),
        ("test_intent_gate.py::test_out_of_vocabulary_kind_is_domainless_unrecognized",)),
    Arm("J5", "settlement is never inferred from disk",
        Sabotage("intents/reduce.py",
                 before="committed = settlement.get(registration.digest)",
                 after="committed = settlement.get(registration.digest, True)"),
        # Both checks hold genuinely MATCHING published bytes, so treating
        # the unsettled pointer as committed flips them to "matched".
        ("test_intent_reduce.py::test_unsettled_pointer_is_unresolvable_regardless_of_disk",
         "test_world_log_evaluator.py::TestQualification::test_pending_exit_carries_qualification")),
    Arm("J6", "qualification findings are appended last, inventory order",
        Sabotage("world/verify.py",
                 before="findings + qual_findings",
                 after="qual_findings + findings"),
        ("test_world_log_evaluator.py::TestQualification::test_qualification_findings_are_appended_last",)),
    Arm("J7", "the terminal publication fulfills the boundary's own appended intent",
        Sabotage("boundary.py",
                 before="_, _, plan = publication_plan(result.run, produces=None)\n"
                        "        port.execute_fulfilling(plan, fulfills)",
                 after="_, _, plan = publication_plan(result.run, produces=None)\n"
                       "        port.execute(plan)"),
        ("test_run_persistence.py::test_assessment_sequence_appends_intent_then_publishes_fulfilling",)),
    Arm("J8a", "the view requires canonical reprojection equality",
        Sabotage("runrecord.py",
                 before='if _reproject(parsed) != parsed:\n        _refuse("$", "an array the projection sorts is out of its canonical order")',
                 after='if False:\n        _refuse("$", "an array the projection sorts is out of its canonical order")'),
        ("test_runrecord.py::test_reversed_result_pairs_fail_canonical_reprojection",)),
    Arm("J8b", "decode verifies the recomputed address against the record id",
        Sabotage("runrecord.py",
                 before='if node.id != f"run:{address}":',
                 after="if False:"),
        ("test_runrecord.py::test_closure_member_mutation_diverges_from_the_id",)),
    Arm("J9a", "the closure facet is semantic-hash covered",
        Sabotage("stored.py",
                 before='"run": (RUN_FACET, RUN_CLOSURE_FACET),',
                 after='"run": (RUN_FACET,),'),
        ("test_runrecord.py::test_closure_facet_is_semantic_hash_covered",)),
    Arm("J9b", "the run-facet shapes are exact, never .get()-based",
        Sabotage("runrecord.py",
                 before='if run_facet != {"spec": spec_identity}:',
                 after='if run_facet.get("spec") != spec_identity:'),
        ("test_runrecord.py::test_run_facet_shapes_are_exact_not_get_based",)),
    Arm("J10", "both ref spellings resolve to exactly the published record",
        # The sabotage hits the BRIDGE, not the run node's slug: run_ref
        # minting a foreign kind breaks the bare->typed crossing (and the
        # id the encoder mints through it), which is label 10's claim.
        Sabotage("runrecord.py",
                 before='return f"run:{address}"',
                 after='return f"run-closure:{address}"'),
        ("acceptance/test_intent_boundary_acceptance.py::test_bridge_resolves_assessment_ref_and_stamped_basis",)),
    Arm("J11", "a legacy record reads through the run facet with no schema rejection",
        Sabotage("runrecord.py",
                 before="if facet is None:\n        return None  # legacy: readable, resolvable, never qualifying",
                 after='if facet is None:\n        raise MalformedRecord(f"{node.id}: a run record carries the closure facet")'),
        ("test_runrecord.py::test_legacy_run_node_reads_and_never_qualifies",
         "test_intent_evidence.py::test_legacy_run_is_inert_not_undecodable")),
    Arm("J12a", "completion's predicate is the shared shape predicates",
        Sabotage("report.py",
                 before="if shapes.mismatch(decoded, held_evidence) is None:",
                 after='if getattr(held_evidence, "event_token", None) == intent.event_token:'),
        ("test_report.py::test_wrong_spec_run_closure_reads_unfinished",
         "test_report.py::test_assessment_shaped_closure_never_closes_a_production_intent")),
    Arm("J12b", "the regenerated rule interior keeps the certified matrix answers",
        Sabotage("holdings/qualify.py",
                 before='if observation["location"] == intent["location"] and '
                        'observation["event_token"] == intent["event_token"]:',
                 after='if observation["location"] == intent["location"]:'),
        ("test_consumer_agreement.py::test_holdings_matrix_agrees_across_both_consumers[wrong-token]",)),
    Arm("J13", "the reducer can match — every alternative reads matched",
        Sabotage("intents/shapes.py",
                 before='if type(evidence) is InertRecord:\n        return "wrong-purpose"',
                 after='if True:\n        return "wrong-purpose"'),
        ("acceptance/test_intent_boundary_acceptance.py::test_positive_matched_per_alternative",
         "test_intent_reduce.py::test_matched_by_run_publication_sets_fulfilled_by")),
)

ATOMS_CITATIONS_BY_UNIT = {
    # L7u5's serialization claim is the root lease's — an atoms production
    # (suite at 038513f), cited, never mutated from Science. The
    # corroborating Science check runs in the ordinary acceptance pass
    # (never as an Arm): test_u5_raced_appends_serialize_into_one_chain.
    "L7u5": "atoms root-lease serialization, remote main 038513f",
}

CO_PASSING_INDEPENDENCE = {
    # Under J3a's writer sabotage the non-port path must KEEP passing —
    # the ceiling binds only the qualifying-publication boundary (cut-10's
    # G9 audit pattern: the harness applies the sabotage once and requires
    # the arm's checks to fail while this node passes).
    "J3a": ("test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling",),
}
```

  The normalization from lettered arms to the 26 frozen units is data
  in the same file, asserted by the harness — never prose:

```python
_UNIT_OF_LETTERED = {
    "L7u2a": "L7u2", "L7u2b": "L7u2", "L7u2c": "L7u2", "L7u2d": "L7u2",
    "J3a": "J3", "J3b": "J3", "J8a": "J8", "J8b": "J8",
    "J9a": "J9", "J9b": "J9", "J12a": "J12", "J12b": "J12",
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {"L7": 13}
LABELED_UNITS: tuple[str, ...] = tuple(f"J{n}" for n in range(1, 14))
```

  L7u12's T2 second-fulfilling-registration classification stays
  cut 8's — cited in the module docstring, no arm.

- [ ] **Step 1a: The harness** — `test_n2_cut11.py` mirrors
  `test_n2_cut10.py`: the same imports (`from test_n2 import FAILED,
  PASSED, MalformedArm, _run_check, _sabotage, audit, baseline`), the
  same session-scoped `findings` fixture applying every arm through
  `audit`/`baseline` on an isolated copy, the same
  `TestEveryCutArmAssertsSomething` loop. Its cut-11 additions, in
  full:

```python
def test_the_partition_accounts_exactly_the_26_frozen_units() -> None:
    from n2_arms_cut11 import ATOMS_CITATIONS_BY_UNIT, CUT11_ARMS, LABELED_UNITS, ROW_UNITS, unit_of

    arm_units = {unit_of(arm.row) for arm in CUT11_ARMS}
    citation_units = set(ATOMS_CITATIONS_BY_UNIT)
    assert not arm_units & citation_units  # a unit is an arm XOR a citation
    # The frozen IDENTITIES, never a count: cut 11 §3.1's thirteen selected
    # units and §3.3's thirteen labels, exactly.
    selected = {f"L7u{n}" for n in range(1, ROW_UNITS["L7"] + 1)}
    assert arm_units | citation_units == selected | set(LABELED_UNITS)
    assert set(LABELED_UNITS) == {f"J{n}" for n in range(1, 14)}
    assert citation_units == {"L7u5"}


def test_the_citation_units_corroborating_checks_are_collected() -> None:
    # A citation is metadata with a living check — collected in the ordinary
    # pass, never mutated (the atoms production is the authority).
    collected = subprocess.run(
        ["uv", "run", "--frozen", "pytest", "--collect-only", "-q",
         "tests/acceptance/test_intent_boundary_acceptance.py::test_u5_raced_appends_serialize_into_one_chain"],
        cwd=REPO_ROOT / "python", capture_output=True, text=True, check=False,
    )
    assert collected.returncode == 0


def _j3a_independence(arm: Arm, workspace: Path) -> tuple[int, int]:
    # The cut-10 G9 audit pattern (`_g9_independence`): one sabotaged
    # installation, the arm's check must fail while the independence node
    # passes — the ceiling binds only the qualifying-publication boundary.
    package = _sabotage(arm, workspace)
    assert package is not None
    failing = _run_check(
        "test_operation_port.py::test_oversized_postimage_refuses_before_any_write", package
    ).returncode
    passing = _run_check(
        "test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling", package
    ).returncode
    return failing, passing


def test_j3a_writer_ceiling_fails_while_the_non_port_write_passes(tmp_path):
    from n2_arms_cut11 import CO_PASSING_INDEPENDENCE, CUT11_ARMS

    arm = next(arm for arm in CUT11_ARMS if arm.row == "J3a")
    assert CO_PASSING_INDEPENDENCE["J3a"] == (
        "test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling",
    )
    failing, passing = _j3a_independence(arm, tmp_path / "j3a")
    assert failing == FAILED
    assert passing == PASSED
```

- [ ] **Step 2: Write the durable acceptance arms** — the complete
  `tests/acceptance/test_intent_boundary_acceptance.py`, on the
  certified volume (`certified_work` from `tests/conftest.py`), every
  root registered, every fulfillment a genuine committed transaction:

```python
"""Cut 11's durable acceptance arms: genuine boundaries, real chains."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.write_plan import CreateOp

from science import root as science_root
from science import stored
from science.corpus import ReadView
from science.identity import v1
from science.intents.reduce import qualify_chain
from science.production import mint_dataset
from science.root import init_corpus_root
from science.runrecord import bare_address, decode_run_record, publication_plan, run_ref
from science.world.logmodel import IntentEntryView, WellFormedView
from science.world.records import capture_records
from test_operation_port import durable_port


def _port(base, name):
    root = base / name
    init_corpus_root(root)
    return root, durable_port(root)


def _qualification(root):
    seam = science_root._log_seam()
    view = seam.inspect_registered(root)
    assert type(view) is WellFormedView
    return qualify_chain(view.entries, dict(capture_records(root, "corpus")),
                         state_facts=seam.state_facts)


def _append_assessment(port, *, spec="s" * 64, token="tok"):
    return port.append_intent(v1.encode({"spec_identity": spec, "event_token": token, "actor": "a"}))


def _append_operation(port, *, kind, token="tok"):
    return port.append_intent(v1.encode({"kind": kind, "event_token": token, "actor": "a"}))


def _report_plan(report):
    node = stored.act_report_node(report)
    return (CreateOp(f"act-report/{report.identity()}.md", node_to_markdown(node).encode("utf-8")),)


def _observation_plan(token="tok"):
    from science.holdings.records import Found, StoreLocator, holdings_observation

    value = holdings_observation(location=StoreLocator(store_id="0" * 32, relative_path="a/b"),
                                 outcome=Found("sha256:" + "1" * 64), observer="observer-1",
                                 instrument="instrument-1", event_token=token,
                                 observed_at="2026-08-27T00:00:00Z", supersedes=())
    node = stored.holdings_observation_node(value)
    return (CreateOp(f"holdings-observation/{value.identity()}.md",
                     node_to_markdown(node).encode("utf-8")),)


def _non_qualifying_reason(findings):
    details = [f.detail for f in findings if f.code == "intent-fulfillment-non-qualifying"]
    assert len(details) == 1, findings
    return details[0]


# --- L7u2: the mutated-fulfillment family, one genuine member each ------

def test_u2_wrong_purpose_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-purpose")
    port.execute_fulfilling(_observation_plan(), _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-purpose" in _non_qualifying_reason(findings)


def test_u2_wrong_spec_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-spec")
    _, _, plan = publication_plan(make_closure(spec="x" * 64), produces=None)
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-spec" in _non_qualifying_reason(findings)


def test_u2_wrong_token_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-token")
    _, _, plan = publication_plan(make_closure(token="other"), produces=None)
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-token" in _non_qualifying_reason(findings)


def test_u2_no_record_member(certified_work):
    root, port = _port(certified_work, "u2-no-record")
    port.execute_fulfilling((CreateOp("notes/memo.md", b"no record here"),),
                            _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in _non_qualifying_reason(findings)


# --- L7u3: decay a GENUINE boundary-published run (freeze obligation 2) --

def test_u3_decayed_genuine_run_is_unresolvable_silently(certified_work):
    root, port = _port(certified_work, "u3")
    closure = make_closure()
    _, path, plan = publication_plan(closure, produces=None)
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, _ = _qualification(root)
    assert rows[0].status == "matched"  # genuine before the decay
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])  # decay in place
    rows, findings = _qualification(root)
    assert rows[0].status == "unresolvable"
    assert findings == ()  # §6: no unmatched finding


# --- L7u5: the citation's corroborating check ---------------------------

def test_u5_raced_appends_serialize_into_one_chain(certified_work):
    root, port = _port(certified_work, "u5")
    barrier = threading.Barrier(2)

    def append(token: str) -> str:
        barrier.wait()
        return _append_operation(port, kind="audit", token=token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(append, token) for token in ("t1", "t2")]
        digests = [future.result() for future in futures]  # an append failure raises HERE
    assert len(digests) == 2 and len(set(digests)) == 2  # both appends actually landed
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView  # one linear chain, never a sibling branch
    chained = sorted(e.digest for e in view.entries if type(e) is IntentEntryView)
    assert len(chained) == 2 and chained == sorted(digests)


# --- L7u8: the negative --------------------------------------------------

class _Cancelled(BaseException):
    pass


def test_u8_negative_discarded_attempt_is_indistinguishable(certified_work, tmp_path):
    from fixtures_cut3 import run_assessment

    root, inner = _port(certified_work, "u8")

    class CancelledBeforePublication:
        # The port contract is honored: execute RAISES before writing —
        # a cancellation, not a silent success over a discarded plan.
        def append_intent(self, payload: bytes) -> str:
            return inner.append_intent(payload)

        def execute(self, plan) -> None:
            raise _Cancelled()

        def execute_fulfilling(self, plan, fulfills: str) -> None:
            raise _Cancelled()

    with pytest.raises(_Cancelled):
        run_assessment(tmp_path, port=CancelledBeforePublication(), spec="not-a-spec")
    view = science_root._log_seam().inspect_registered(root)
    assert [e for e in view.entries if type(e) is IntentEntryView] == []  # nothing durable
    rows, findings = _qualification(root)
    assert rows == () and findings == ()  # indistinguishable from never-attempted


# --- L7u9–u12: the operation family --------------------------------------

def test_u9_wrong_operation_token_fails_qualification(certified_work):
    root, port = _port(certified_work, "u9")
    port.execute_fulfilling(_report_plan(sample_report(operation="import", token="other")),
                            _append_operation(port, kind="import"))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-token" in _non_qualifying_reason(findings)


def test_u10_wrong_kind_report_fails_qualification(certified_work):
    root, port = _port(certified_work, "u10")
    port.execute_fulfilling(_report_plan(sample_report(operation="audit", token="tok")),
                            _append_operation(port, kind="import"))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-kind" in _non_qualifying_reason(findings)


def test_u11_run_for_non_run_operation_fails_qualification(certified_work):
    root, port = _port(certified_work, "u11")
    _, _, plan = publication_plan(make_closure(), produces=None)
    port.execute_fulfilling(plan, _append_operation(port, kind="import"))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-purpose" in _non_qualifying_reason(findings)


def test_u12_no_terminal_record_fails_qualification(certified_work):
    root, port = _port(certified_work, "u12")
    port.execute_fulfilling((CreateOp("notes/no-terminal.md", b"nothing"),),
                            _append_operation(port, kind="import"))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in _non_qualifying_reason(findings)


# --- J10: the bare-address/typed-ref bridge ------------------------------

def test_bridge_resolves_assessment_ref_and_stamped_basis(certified_work):
    root, port = _port(certified_work, "bridge")
    closure = make_closure(shape="dataset-production")
    minted = mint_dataset(closure, existing_bases={})
    record_id, _, plan = publication_plan(closure, produces=minted.address)
    port.execute(plan)
    # StampedBasis.run is a BARE closure address — no kind, no colon:
    assert minted.basis.run == closure.address() and ":" not in minted.basis.run
    # bare -> typed through the bridge, then resolution to the one record:
    assert run_ref(minted.basis.run) == record_id
    view = ReadView.opened_at(root)
    assert view.resolve(run_ref(minted.basis.run)) == record_id
    # an assessment's stored `run` field is the typed spelling, and resolves:
    assessment = stored.assessment_node(
        "a" * 64, title="assessment", spec="s" * 64, run=record_id,
        proposition="proposition:" + "p" * 64, outcome="supports",
        interpretation_rule="rule:interpretation",
    )
    port.execute((CreateOp(f"assessment/{'a' * 64}.md",
                           node_to_markdown(assessment).encode("utf-8")),))
    view = ReadView.opened_at(root)
    stored_run_field = stored.assessment_value(view.get("assessment:" + "a" * 64)).run
    assert view.resolve(stored_run_field) == record_id
    # and the inverse round-trips, field-by-field as frozen:
    assert bare_address(record_id) == minted.basis.run


# --- J13: positive qualification, every §2.2 alternative -----------------

@pytest.mark.parametrize("case", [
    "assessment-run-publication", "assessment-report",
    "operation-report", "production-run", "production-report",
])
def test_positive_matched_per_alternative(case, certified_work):
    root, port = _port(certified_work, f"positive-{case}")
    if case.startswith("assessment"):
        fulfills = _append_assessment(port)
    else:
        kind = "import" if case == "operation-report" else "run-attempt"
        fulfills = _append_operation(port, kind=kind)
    if case == "assessment-run-publication":
        _, _, plan = publication_plan(make_closure(), produces=None)
    elif case == "production-run":
        closure = make_closure(shape="dataset-production")
        _, _, plan = publication_plan(closure,
                                      produces=mint_dataset(closure, existing_bases={}).address)
    else:
        operation = "import" if case == "operation-report" else "run-attempt"
        plan = _report_plan(sample_report(operation=operation, token="tok"))
    port.execute_fulfilling(plan, fulfills)
    rows, findings = _qualification(root)
    assert rows[0].status == "matched" and rows[0].fulfilled_by is not None
    assert findings == ()


# --- label 8's frozen round trip -----------------------------------------

def test_decimal_round_trip_publishes_and_captures(certified_work):
    values = [Decimal("0.5"), "0.5", 1, Decimal("1.0")]
    root, port = _port(certified_work, "decimal")
    published = []
    for value in values:
        closure = make_closure(parameters={"threshold": value})
        _, path, plan = publication_plan(closure, produces=None)
        port.execute(plan)
        published.append((closure, path))
    records = dict(capture_records(root, "corpus"))
    addresses = set()
    for closure, path in published:
        publication = decode_run_record(node_from_markdown(records[path].decode("utf-8")))
        assert publication is not None and publication.address == closure.address()
        addresses.add(publication.address)
    assert len(addresses) == 4  # the four never collide
```

  Also added, to `python/tests/test_run_persistence.py`:
  `test_kill_between_append_and_start_leaves_intent_only_operation_kind`
  — u13's twin of Task 4's kill arm, identical body with
  `run_production` in place of `run_assessment`.

- [ ] **Step 3: Run the N2 harness**

Run: `uv run --frozen pytest "tests/acceptance/test_n2_cut11.py" -p no:cacheprovider`
Every arm must be sound — no `vacuous`, `stale`, or `uncollected` —
and every fabricated construction must pass its declared-layer
assertion (cut §5 item 1).

- [ ] **Step 4: Write and run `tools/cut11_acceptance.py` on the
  certified volume; quote its pytest summary lines into the ledger.**

- [ ] **Step 5: Ledger + commit**

```bash
git add python/tests/acceptance/ python/tools/cut11_acceptance.py \
        docs/plans/2026-08-27-intent-boundary-ledger.md
git commit -m "test(cut11): the 26 N2 declarations and the acceptance runner"
```

---

### Task 14: Discharge, results record, banking

**Files:**
- Create: `docs/plans/2026-08-27-conformance-cut-11-results.md`
- Modify: `docs/designs/2026-08-27-conformance-cut-11.md` (status
  header only: discharged, with the head commit and summary lines)
- Move: `docs/superpowers/specs/2026-08-26-world-index-intent-boundary-design.md`
  → `docs/designs/2026-08-26-world-index-intent-boundary-design.md`
  (promotion at banking; status header → implemented)
- Modify (spec §7's list, each a dated note, frozen bodies untouched):
  - `docs/designs/2026-08-02-epistemic-kernel-design.md` §8.7 status
    paragraph (dated ownership note only — G4 stays open, owner the
    successor-admission slice)
  - `docs/designs/2026-08-03-redesign-adoption-ledger.md` row 5 +
    design-track item 6 (remainder shrinks to event-level L8, the L13
    preimage resolver, and G4 with its named owner)
  - `docs/designs/2026-08-22-log-verification-design.md` §10 item 1
    (closed, dated) and its deferral texts
  - `docs/designs/2026-08-24-world-index-holdings-design.md` deferral 5
    (closed, dated)
- Modify: `README.md` (design table row for the promoted spec;
  count → "Thirty-eight documents", date range end unchanged at
  2026-08-27), `python/tests/test_designs_corpus.py` (`_COUNT_WORDS`
  gains `38: "Thirty-eight"`), guide pages per the stale-claim grep.

- [ ] **Step 1: Discharge** — run the full suite, cut8–cut11 acceptance
  runners, and the N2 harness on the certified volume; quote every
  pytest summary line in the results record; commit the execution
  ledger's final rulings **before any worktree removal** (the ledger is
  already on a tracked path).

- [ ] **Step 2: Write the results record** — mirror
  `docs/plans/2026-08-24-conformance-cut-10-results.md`: the discharged
  units, the quoted summary lines, deviations (none, or listed), the
  ledger pointer.

- [ ] **Step 3: The stale-claim grep** (spec §7):

```bash
grep -rn "intent qualification\|intents_unevaluated\|G4" README.md docs/guide/ docs/designs/ | grep -v conformance-cut
```

Live text saying qualification is unevaluated updates with dated notes;
frozen cut bodies and quoted rows stay byte-exact.

- [ ] **Step 4: Promote the spec, update README/guide/corpus tests**,
  run `python tools/check_guide.py` and
  `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py`
  — the three mid-branch red tests turn green here.

- [ ] **Step 5: Final gate + ledger close + commit**

```bash
git add -A
git commit -m "docs(cut11): discharge the intent-boundary slice and bank the design"
```

The `--no-ff` merge into `main` is the human partner's act; the branch
stays unpushed.

---

## Self-Review (run before handing the plan over)

1. **Spec coverage:** §2.1/§2.2 → Tasks 6, 9; §2.3 (T2 stays the
   chain's) → cited, never re-implemented; §2.4/§4 → Task 5; §2.5 →
   Task 11; §2.6 items 1–3 → Task 4, item 2a → Task 3, items 4–5 →
   Task 2; §3.1 → Tasks 3, 7; §3.2 → Task 6; §3.3 → Tasks 9, 10; §5 →
   deliberately no task (transferred); §6's arm inventory → Tasks 12,
   13; §7/§8 → Task 14.
2. **Placeholder scan:** every Step-1 test carries executable
   assertions; repo-local builders are named exactly
   (`fixtures_cut3.run_assessment`, `test_operation_port.durable_port`,
   `test_holdings_reduce.invoke`, the evaluator file's `chain`/
   `evaluate`), and where a builder gains a parameter, the gaining
   task's Step 3 spells the change. No comment-body tests, no TBDs.
3. **Type consistency:** `IntentQualification` (Task 9) is what
   `LogReport.qualification` (Task 10) carries; `shapes.mismatch`
   (Task 6) is what Tasks 9 and 11 call; `qualify_chain(entries,
   records, *, state_facts)` reads the same in Tasks 9, 10, and 12;
   `RECORD_CEILING` (Task 3, `science/world/records.py`) is what
   Task 7's reader and `root.py`'s writer import;
   `runrecord.publication_plan` returns `(id, path, plan)` in Tasks 2,
   4, and 8 alike; `capture_records(root, kind)` in Tasks 7 and 10
   alike; `OperationPort` has exactly one home (`runrecord`, Task 2),
   one re-export (`corpus`, Task 3), and three methods everywhere.
