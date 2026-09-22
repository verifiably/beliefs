# Act-Report Remainder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open the `audit` and `re-check` operation kinds through boundary wrappers that append one operation intent before any act and close through exactly one act-report, bind every supplied operation port to its writer, and discharge T2 in full as conformance cut 38.

**Architecture:** Two new modules — `beliefs/audit_operation.py` (the audit: checks, intent, `audit_corpus` over the writer's own view, one subject-evaluation entry per finding, one closing transaction, all under the caller's hold and the root lock) and `beliefs/holdings/recheck.py` (the re-check: checks, intent, the per-location `recheck` act as built with nothing held across the acts, one locator entry per location, the close under the hold and the root lock). `OperationPort` gains `root`, and `CorpusWriter._require_bound_port` — called by both primitives and both wrappers' preflights — refuses a port not bound to the writer's root, authority and profile. Two session routes mirror `acquire`. The evaluator and the per-act boundary do not change.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, `nodes` records, the acceptance harness under `python/tests/acceptance/` and the N2 audit (`n2_arms.py`, `test_n2.py`).

**Spec:** `docs/superpowers/specs/2026-09-22-act-report-remainder-design.md` (reviewed 2026-09-22, two rounds; §14 there). Read it first; every task cites its sections and decisions.

## Global Constraints

- **Baseline is `main` at `a71a3f4`.** Work in the worktree `.worktrees/act-report-remainder` (branch `design/act-report-remainder`, locked "on WORK_ROOT storage"); every path below is relative to the repository root, and paths shown to the user carry the worktree prefix. The main checkout is `~/d/beliefs`. Exports for a worktree on `WORK_ROOT`: `SCIENCE_MM30_ROOT` and every `SCIENCE_CUT*_ROOT` name the **main checkout's** `.work/…` (memory `worktree-on-work-root-needs-cut-root-exports`; ~190 `CapabilityUnavailable` failures are a missing export, not a regression). For the fast loop: `export SCIENCE_CUT4_ROOT=~/d/beliefs/.cut4-acceptance SCIENCE_CUT10_ROOT=~/d/beliefs/.lifecycle-wrappers-test`.
- **The worktree's sibling dependencies resolve under `.worktrees/`.** `python/pyproject.toml` pins `verifiably-atoms` and `verifiably-nodes` as editable paths `../../atoms/python` and `../../nodes/python`; `cd python && uv run --frozen python -c "import atoms, nodes, beliefs"` prints nothing on success. `just setup` has run.
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions. — For this lane (spec decision 11): neither new module imports `atoms` or names an engine type; both reach the log only through `CorpusWriter._append_operation_intent`, `CorpusWriter._publish_operation_report` and `holdings/boundary.py`'s `recheck`, all inventoried callers. Neither wrapper calls a write primitive directly (the primitive set is `test_permit_boundary.py`'s `PRIMITIVE_ATTRIBUTES` and `PRIMITIVE_NAMES`), so the inventory is unchanged — the standing `holdings/acquire.py:acquire` has. Tasks 2, 3 and 4 each assert `test_permit_boundary.py`, `test_permit_entry_points.py` and `test_capability_boundary.py` green; the results record states the inventories were checked in both directions.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. — Here that is Task 6, Step 4, with `(cut38, 38, (14, 12, 3))`.
- **Frozen declarations and frozen cut bodies stay byte-exact.** Cut 38 chains **cut 37's** runner (`PREFIX_RUNNERS = ("cut37_acceptance.py",)`) and re-targets nothing: no line this lane edits is pinned by a live prior arm (Task 1 Step 8 and Task 6 Step 5 run `tests/test_arm_staleness.py` to prove it; a stale prior arm means a `before` this lane moved — restore the line's spelling, never edit the prior declaration).
- **Decisions the code must honour verbatim** (spec §2): two new modules, `audit.py` and `holdings/boundary.py` untouched (1); the audit's subject is the writer's own corpus through `audit_corpus` (2); one `SubjectEvaluationEntry` per finding in the evaluator's order, payload `v1.encode({"severity", "code", "detail"})` decoded UTF-8, `message` excluded, a clean audit closes with empty entries (3); the audit runs under the caller's hold then `writer._operation` from before the intent to after the report (4); the re-check is independent store re-checks with no stop, `instrument_inputs=()`, the attempt's `reason` only (5); the re-check's acts run outside the root lock and its close under the hold then the lock, view rebuilt before any ref resolves (6); every check before the intent, no catch on the operation's behalf (7); session routes through `operation_port()` and `_closing_hold`, observer = session actor (8); kind-checked `_mint_audit_report` / `_mint_recheck_report` (9); `AuditRefused`, `RecheckRefused`, `PortMismatch` under `WriteRefused` (10, 13); `OperationPort.root`, `_require_bound_port` in both primitives and both preflights, comparing `Path(port.root).resolve()` to the writer's resolved root, `port.authority == writer.authority`, `port.profile.compiled_identity == writer.profile.compiled_identity`, applied to a **supplied** port only (13); the re-check validates observer, instrument and every `standing` set pre-intent (14).
- **Detached runs go through a reaping wrapper** (Processes rule): the cut runner and the gate outlive a turn, so each is launched by `~/d/beliefs/.work/acceptance/detached.sh` (already written by cut 37's plan; `test -x` it, and if missing recreate it from `docs/superpowers/plans/2026-09-21-l13-preimage.md`'s Global Constraints). Launch: `setsid nohup ~/d/beliefs/.work/acceptance/detached.sh <log> <cmd…> > /dev/null 2>&1 &`. The end-of-turn report that leaves it running names the process-group id (`cat <log>.pid`) and the stop command (`kill -TERM -- "-$(cat <log>.pid)"`), after `host-load --section session` has listed what the session's scope left. After exit, check that the process group is gone before reporting nothing left.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row or invariant it serves. Run every `pytest` from `python/` with `uv run --frozen`. No `TypeScript` changes; both `CONTRACT.yaml` copies unchanged.

---

## File map

| File | Responsibility |
| --- | --- |
| `python/src/beliefs/runrecord.py` | `OperationPort.root` (Task 1) |
| `python/src/beliefs/session/routes.py` | `LedgeredPort.root` (Task 1) |
| `python/src/beliefs/corpus.py` | `_require_bound_port`; both primitives call it (Task 1) |
| `python/src/beliefs/errors.py` | `PortMismatch` (Task 1); `AuditRefused` (Task 2); `RecheckRefused` (Task 3) |
| `python/tests/fixtures_cut3.py`, `test_import_bundle.py`, `test_operation_port.py`, `test_relocation_recovery.py`, `acceptance/test_url_retrieval_acceptance.py` | the port fakes gain `root` (Task 1) |
| `python/tests/test_operation_port_binding.py` (new) | the binding check over real roots (Task 1) |
| `python/src/beliefs/audit_operation.py` (new) | `AuditOutcome`, `audit`, `_finding_payload` (Task 2) |
| `python/src/beliefs/boundary.py` | `_mint_audit_report` (Task 2), `_mint_recheck_report` (Task 3) |
| `python/tests/test_audit_operation.py` (new) | the audit operation over a durable root (Task 2) |
| `python/src/beliefs/holdings/recheck.py` (new) | `RecheckOutcome`, `recheck_locations` (Task 3) |
| `python/tests/test_holdings_recheck.py` (new) | the re-check operation over a durable root and store (Task 3) |
| `python/src/beliefs/session/writer.py` | `ScopedWriter.audit`, `ScopedWriter.recheck` (Task 4) |
| `python/tests/test_session_routes.py` | the two routes (Task 4) |
| `python/tests/acceptance/test_act_report_remainder_acceptance.py` (new) | the twelve declaration units and two plain tests over real roots (Task 5) |
| `python/tests/n2_arms_cut38.py` (new), `python/tests/acceptance/n2_arms_cut38.py` (new shim), `python/tests/acceptance/test_n2_cut38.py` (new), `python/tools/cut38_acceptance.py` (new), `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, the recent-cut row (Task 6) |
| `docs/designs/2026-09-22-conformance-cut-38.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py` | the freeze (Task 0) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | §17 (Task 7) |
| `docs/plans/2026-09-22-conformance-cut-38-results.md` (new), the ledger, the roadmap, `python/tools/roadmap_status.py`, `docs/designs/2026-08-11-act-report-design.md`, `docs/guide/open-questions.md`, `docs/guide/contracts-and-adoption.md`, `README.md`, tasks | discharge and amendments (Task 8) |

---

### Task 0: Freeze cut 38 and file the tasks

**Files:**
- Create: `docs/designs/2026-09-22-conformance-cut-38.md`
- Modify: `README.md` (the designs count and table row), `docs/guide/contracts-and-adoption.md` (a "frozen and not yet discharged" paragraph and the cut list), `python/tests/test_designs_corpus.py` (the number-word table, one entry), `tasks/beliefs-86b150.md` through the CLI

**Interfaces:**
- Produces: the frozen §§2–7 the guard pins (Task 6 reads its freeze commit and body digest); the unit inventory every later task builds against.

- [ ] **Step 1: Confirm cut 38 is unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -q "conformance-cut-3[8-9]" && echo "claimed on $b"; done; echo scan done
git worktree list
```
Expected: `scan done` alone; the only worktrees are `main` and `.worktrees/act-report-remainder`.

- [ ] **Step 2: Write the cut document** on cut 37's shape (`docs/designs/2026-09-21-conformance-cut-37.md`; `sed -n 1,120p` it first). Header:

```markdown
# Conformance cut 38 — the act-report remainder

**Status:** frozen 2026-09-22, before implementation; T2 is open
**Design:** `../superpowers/specs/2026-09-22-act-report-remainder-design.md`, approved for implementation planning 2026-09-22 at `f43e236` after two reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-22-act-report-remainder.md`.
**Numbered after** cut 37 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 38–39 at freeze; cut 37 is the highest discharged runner.
```

§1 states what the cut is (spec §1, condensed: six of the eight operation kinds open through a boundary; `audit` and `re-check` have none; this cut builds the two wrappers — the audit over the writer's own corpus under the root lock, the re-check over independent store re-checks — binds every supplied operation port to its writer, and closes T2; the T table is then full but for T7's cross-root case under `cross-root-publication`).

§2 the boundary: `python/src/beliefs/audit_operation.py` (new), `python/src/beliefs/holdings/recheck.py` (new), `boundary.py`, `corpus.py`, `runrecord.py`, `session/routes.py`, `session/writer.py`, `errors.py`; the test modules whose port fakes gain `root`; `python/tests/test_operation_port_binding.py`, `test_audit_operation.py`, `test_holdings_recheck.py`, `test_session_routes.py`; `python/tests/acceptance/test_act_report_remainder_acceptance.py`, `python/tests/n2_arms_cut38.py`, `python/tests/acceptance/n2_arms_cut38.py`, `python/tests/acceptance/test_n2_cut38.py`, `python/tools/cut38_acceptance.py`; this cut, the ledger, roadmap, guide, README, the act-report design's §3.1 amendment note. "`audit.py`, `world/audit.py` and `holdings/boundary.py` are consumed and not edited. Frozen declarations and cut bodies through cut 37 remain byte-exact; no prior live arm pins a line this cut moves."

§3 selection: quote the T2 row byte-exact from `docs/designs/2026-08-11-act-report-design.md` §5 (`grep -n "^| \*\*T2\*\*" docs/designs/2026-08-11-act-report-design.md` and copy the whole line), then the unit table, copied from spec §9.2 (twelve rows, T2-e through BI-3, the assertion column verbatim).

§3.2 rows not read: "**T7** is not read; its cross-root case is `cross-root-publication`'s (`beliefs-256f17`, tier 3). **T3** and **T4** are already closed and are exercised by two plain acceptance tests that declare no unit and claim no row. **T1** and **T8** are not read. T2, T5 and T6 are read: T2 in full, T5 and T6 for the instance the new kinds give them."

§4 accounting: "**12 declaration units**, nine against T2, T5 and T6 and three boundary invariants; T2 closes; the T table stays partial on T7 alone. 187 of 216 → 188 of 216."

§5 N2 and acceptance obligations, the sabotage table exactly as Task 6 declares it (fourteen rows, copied from spec §9.3's table with the `module` column added: `audit_operation.py` for T2-e, T2-g2 (the audit's), T2-h, T6-d, T6-e, BI-2; `holdings/recheck.py` for T2-f, T2-g1, T2-g3, T2-j, T5-d; `corpus.py` for T2-i; `audit.py` for BI-1; `session/writer.py` for BI-3). "That makes **14 arms over 12 units** (T2-g homes three; every other unit one). Both directions are required: the check passes on the real tree and fails under sabotage. The runner uses `PREFIX_RUNNERS = ("cut37_acceptance.py",)` and carries `PHASE_MODULES = ("test_act_report_remainder_acceptance.py", "test_n2_cut38.py")`."

§6 second reader: check that T2-e's ordering proof reads the evaluator's invocation from a recording seam and the intent's position from the chain, not from timestamps; that T2-i's foreign port carries the writer's own authority and profile so only the root differs; that T2-j's "zero reads" is read from the store seam's `read_path` counter and not inferred from the chain; that T6-e's two entry tuples come from two evaluator returns that differ in `message` alone, and that the fixed envelope is one `OperationIntent` value reused for both mints; that BI-2's racing write is a real `writer.add` on another thread that blocks on the root lock (its registration lands after the report's); that BI-1's static assertion uses `test_permit_boundary.py`'s own `primitive_callers` over the two evaluator modules.

§7 limitations: spec §12 items 1–5.

- [ ] **Step 3: README, guide, the number word**

`README.md`: "Seventy-four documents" → "Seventy-five documents"; add the table row after the cut-37 row:

```markdown
| `2026-09-22-conformance-cut-38.md` | the frozen act-report-remainder cut: the `audit` and `re-check` operations through the boundary, every supplied port bound to its writer; T2 read in full, 12 declaration units, three boundary invariants, the cut 37 runner as prefix |
```

`docs/guide/contracts-and-adoption.md`: after the cut-37 discharge paragraph (the one beginning "Cut 37 discharges the L13 preimage resolver"), add:

```markdown
Cut 38 is frozen and not yet discharged: the act-report remainder — the
`audit` and `re-check` operations open through the boundary and close
through one act-report each; a supplied operation port is bound to its
writer (`../designs/2026-09-22-conformance-cut-38.md`).
```
and add `  - ../designs/2026-09-22-conformance-cut-38.md` to the cut list where cut 37's line is.

`python/tests/test_designs_corpus.py`: add `75: "Seventy-five",` to the number-word table beside `74: "Seventy-four",`.

- [ ] **Step 4: Verify**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```
Expected: all pass (the newest results record is still cut 37's, so the "discharged" guards read cut 37).

- [ ] **Step 5: Tasks**

```bash
tasks note beliefs-86b150 "Cut 38 frozen (docs/designs/2026-09-22-conformance-cut-38.md): 12 units, 14 arms; chains cut 37; no prior live arm re-targeted."
```
The plan's step children exist (filed with the plan: `beliefs-b3a977` Task 0, `beliefs-223c02` Task 1, `beliefs-3b5200` Task 2, `beliefs-17f790` Task 3, `beliefs-97f8b4` Task 4, `beliefs-bbacaf` Task 5, `beliefs-1e1731` Task 6, `beliefs-26d2da` Task 7, `beliefs-d1bfbd` Task 8, `beliefs-b4a631` Task 9, each depending on its predecessor). `tasks start` each before its task and `tasks done` it in the task's commit. `tasks check` — zero errors.

- [ ] **Step 6: Commit the freeze**

```bash
tasks check && git add docs/designs/2026-09-22-conformance-cut-38.md README.md docs/guide/contracts-and-adoption.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut): freeze conformance cut 38, the act-report remainder"
git rev-parse HEAD
```
Record the full commit hash: Task 6's guard pins it as `CUT38_FREEZE_COMMIT`, and `sha256sum docs/designs/2026-09-22-conformance-cut-38.md` as `CUT38_FROZEN_SHA256`.

---

### Task 1: The port binding — `OperationPort.root`, `_require_bound_port`, `PortMismatch`

**Files:**
- Modify: `python/src/beliefs/runrecord.py` (the `OperationPort` protocol), `python/src/beliefs/session/routes.py` (`LedgeredPort`), `python/src/beliefs/corpus.py` (`_append_operation_intent`, `_publish_operation_report`, the new helper), `python/src/beliefs/errors.py`
- Modify (fakes): `python/tests/fixtures_cut3.py` (`MemoryPort`), `python/tests/test_import_bundle.py` (`FakePort`), `python/tests/test_operation_port.py` (`FakePort`), `python/tests/test_relocation_recovery.py` (`_HashingOperationPort`), `python/tests/acceptance/test_url_retrieval_acceptance.py` (`RefusingPort`)
- Create: `python/tests/test_operation_port_binding.py`
- Test: `python/tests/test_session_routes.py`

**Interfaces:**
- Produces: `OperationPort.root: Path` (a property on the protocol); `CorpusWriter._require_bound_port(port: OperationPort | None) -> OperationPort` — returns the writer's own port for `None`, the supplied port when bound, raises `PortMismatch` otherwise; `PortMismatch(WriteRefused)`. Tasks 2 and 3 call `writer._require_bound_port(port)` in their preflights.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_operation_port_binding.py`, portable (spec §9.1): the recording port of `tests/test_operation_writes.py` over `tmp_path`, no engine:

```python
"""A supplied operation port is bound to its writer (act-report-remainder design decision 13)."""

from __future__ import annotations

import secrets

import pytest
from authority import FULL, narrowed
from profiles import WITH_BIOLOGY
from test_operation_writes import RecordingPort, writer_over

from beliefs import boundary as boundary_values
from beliefs.errors import PortMismatch
from beliefs.report import LocatorEntry, OperationIntent, RetrievalFailed


def _report(writer, token: str):
    now = "2026-09-22T00:00:00Z"
    return boundary_values._mint_acquisition_report(
        OperationIntent("acquisition", token, writer.authority.actor), observer="o", instrument="i",
        opened_at=now, closed_at=now,
        entries=(LocatorEntry("url:https://example.org/a", RetrievalFailed("status 500"), ()),),
    )


class BiologyPort(RecordingPort):
    def __init__(self, authority, root) -> None:
        super().__init__(authority, root)
        self.profile = WITH_BIOLOGY


def test_none_returns_the_writers_own_port(tmp_path):
    writer, port = writer_over(tmp_path)
    assert writer._require_bound_port(None) is port


def test_a_fresh_port_on_the_same_root_authority_and_profile_is_bound(tmp_path):
    writer, port = writer_over(tmp_path)
    fresh = RecordingPort(FULL, tmp_path)
    assert writer._require_bound_port(port) is port
    assert writer._require_bound_port(fresh) is fresh


@pytest.mark.parametrize("spoil", ["root", "authority", "profile"])
def test_a_port_bound_elsewhere_refuses_before_either_primitive_touches_a_port(tmp_path, spoil):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    writer, own = writer_over(tmp_path / "a")
    if spoil == "root":
        port = RecordingPort(FULL, tmp_path / "b")
    elif spoil == "authority":
        port = RecordingPort(narrowed(kinds=("act-report",), families=("corpus-write",)), tmp_path / "a")
    else:
        port = BiologyPort(FULL, tmp_path / "a")
    token = secrets.token_hex(16)
    with pytest.raises(PortMismatch):
        writer._append_operation_intent("acquisition", token, writer.authority.actor, port=port)
    with pytest.raises(PortMismatch):
        writer._publish_operation_report(_report(writer, token), "0" * 64, port=port)
    assert own.calls == [] and port.calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
```

And in `python/tests/test_session_routes.py`, beside the portable `_holdings` helper (it uses `make_session`, which builds `RecordingPort`s):

```python
def test_the_ledgered_port_forwards_its_inner_ports_root(tmp_path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(BOTH, "A")
    assert scoped.operation_port().root == ports[-1].root
    session.close_invocation("A", {"done": []})
    session.close()
```

- [ ] **Step 2: Run them to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_operation_port_binding.py tests/test_session_routes.py::test_the_ledgered_port_forwards_its_inner_ports_root -q -p no:cacheprovider
```
Expected: FAIL — `ImportError: cannot import name 'PortMismatch'`, then `AttributeError: 'CorpusWriter' object has no attribute '_require_bound_port'` and `'LedgeredPort' object has no attribute 'root'`. No `SCIENCE_CUT*` export is needed: these run on `tmp_path`.

- [ ] **Step 3: The protocol and the ledgered port**

`python/src/beliefs/runrecord.py`: add `from pathlib import Path` beside `import re` (the module has no `pathlib` import today; `grep -n "^from pathlib" src/beliefs/runrecord.py` is empty), and at the top of `class OperationPort(Protocol):`

```python
class OperationPort(Protocol):
    @property
    def root(self) -> Path:
        """The corpus root this port appends to and commits in. A writer
        refuses a supplied port whose root is not its own
        (`CorpusWriter._require_bound_port`)."""
        ...

    @property
    def profile(self) -> ProfileSpec: ...
```

`python/src/beliefs/session/routes.py`, in `LedgeredPort` after `__init__`:

```python
    @property
    def root(self) -> Path:
        return self._inner.root
```
(`Path` is already imported there.)

- [ ] **Step 4: The error and the helper**

`python/src/beliefs/errors.py`, directly after `class ActorMismatch(WriteRefused):` and its docstring:

```python
class PortMismatch(WriteRefused):
    """A supplied operation port is bound to another root, authority or
    profile than the writer's (act-report-remainder design decision 13). A
    foreign root's port would carry the intent and the report into another
    chain while this writer's corpus is what the operation reads."""
```

`python/src/beliefs/corpus.py`: add `PortMismatch` to the `from beliefs.errors import (…)` block (alphabetical, beside `PlanRefused`). Then, directly above `def _append_operation_intent(`:

```python
    def _require_bound_port(self, port: OperationPort | None) -> OperationPort:
        """The port an operation runs on: this writer's own for `None`, or a
        supplied one bound to the same root, authority and profile
        (act-report-remainder design decision 13). The writer's own port is
        bound at construction (`root.py`'s `open_corpus` hands both one root,
        authority and profile), so only a supplied port is compared."""
        if port is None:
            assert self._operation_port is not None
            return self._operation_port
        if Path(port.root).resolve() != Path(self.root).resolve():
            raise PortMismatch(f"the operation port is bound to {port.root}, not this writer's root {self.root}")
        if port.authority != self.authority:
            raise PortMismatch("the operation port binds another authority than this writer's")
        if port.profile.compiled_identity != self.profile.compiled_identity:
            raise PortMismatch("the operation port binds another profile than this writer's")
        return port
```

In `_append_operation_intent`, replace

```python
        operation_port = self._operation_port if port is None else port
        assert operation_port is not None
```
with

```python
        operation_port = self._require_bound_port(port)
```
and make the identical replacement in `_publish_operation_report`. Both keep `self._require_pins_agree()` and `self.authority.require("corpus-write", ("act-report",))` ahead of it, so `test_every_entry_point_requires_before_it_writes` still sees the authority check first.

- [ ] **Step 5: The fakes gain `root`** — one line each; a placeholder root on a value-width fake is never compared (the helper compares a supplied port only, and these fakes are the writers' own). `test_operation_writes.py`'s `RecordingPort` already carries `root` and needs nothing:

- `python/tests/fixtures_cut3.py`, `class MemoryPort`: after `authority = FULL`, add `root = Path("memory-port")` (`Path` is imported at line 6).
- `python/tests/test_import_bundle.py`, `class FakePort.__init__`: after `self.authority = authority`, add `self.root = Path(root)`; add `from pathlib import Path` to the imports if absent.
- `python/tests/test_operation_port.py`, `class FakePort`: after `authority = FULL`, add `root = Path("fake-port")`; add `from pathlib import Path`.
- `python/tests/test_relocation_recovery.py`, `class _HashingOperationPort.__init__`: after `self.authority = authority`, add `self.root = Path(root)` (`Path` is imported at line 7).
- `python/tests/acceptance/test_url_retrieval_acceptance.py`, `class RefusingPort`: add

```python
    @property
    def root(self):
        return self._inner.root
```

- [ ] **Step 6: Run the tests**

```bash
cd python && uv run --frozen pytest tests/test_operation_port_binding.py tests/test_session_routes.py tests/test_operation_port.py tests/test_import_bundle.py tests/test_relocation_recovery.py tests/test_boundary.py tests/test_holdings_acquire.py -q -p no:cacheprovider
uv run --frozen pyright
uv run --frozen ruff check .
```
Expected: all pass; pyright `0 errors` (the spike on 2026-09-22 counted 21 `"root" is not present` errors before this step — every one is a fake above or `LedgeredPort`); ruff clean.

- [ ] **Step 7: The inventories are unchanged**

```bash
cd python && uv run --frozen pytest tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py -q
```
Expected: green — `_require_bound_port` calls no primitive, so it joins nothing.

- [ ] **Step 8: No prior live arm moved**

```bash
cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py -q
```
Expected: green. (Cut 35's arms pin `holdings/acquire.py` lines, not the two primitive lines edited here; if a `before` here reports stale, restore the exact spelling of the pinned line and re-run.)

- [ ] **Step 9: Commit**

```bash
tasks check && git add python/src/beliefs/runrecord.py python/src/beliefs/session/routes.py python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests/fixtures_cut3.py python/tests/test_import_bundle.py python/tests/test_operation_port.py python/tests/test_relocation_recovery.py python/tests/acceptance/test_url_retrieval_acceptance.py python/tests/test_operation_port_binding.py python/tests/test_session_routes.py tasks
git commit -m "feat(report): bind a supplied operation port to its writer — T2, decision 13"
```

---

### Task 2: The audit operation — `beliefs/audit_operation.py`

**Files:**
- Create: `python/src/beliefs/audit_operation.py`, `python/tests/test_audit_operation.py`
- Modify: `python/src/beliefs/boundary.py` (`_mint_audit_report`, the import block), `python/src/beliefs/errors.py` (`AuditRefused`)

**Interfaces:**
- Consumes: `CorpusWriter._require_bound_port` (Task 1); `audit_corpus(view, *, evidence, profile) -> tuple[Finding, ...]`; `CorpusWriter._append_operation_intent(kind, token, actor, *, port=None) -> str`; `CorpusWriter._publish_operation_report(report, intent_digest, *, port=None) -> ActReport`; `writer._operation` (the settling hold); `writer._reconstruct()`; `writer.read_view`; `writer.profile`; `writer.authority`.
- Produces: `audit(writer, *, observer, instrument, evidence, port=None, hold=None) -> AuditOutcome`; `AuditOutcome(report, report_ref, findings, entries)`; `_finding_payload(finding) -> str`; `boundary._mint_audit_report(intent, *, observer, instrument, opened_at, closed_at, entries) -> ActReport`; `AuditRefused(WriteRefused)`. Task 4's session route and Task 5's acceptance call `audit`; Task 6's sabotages pin its lines.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_audit_operation.py`, portable (spec §9.1): `writer_over(tmp_path)` gives a writer whose `RecordingPort` records every port call in order and applies fulfilling plans through `DefaultExecutor`, so the report lands on disk and the writer's rebuilt view sees it; the chain is the port's call list.

```python
"""The audit operation (act-report-remainder design §3) — portable, over the recording port."""

from __future__ import annotations

import json
import threading
from dataclasses import replace

import pytest
from authority import FULL, narrowed
from fixtures_cut4 import raw_write
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE
from test_operation_writes import RecordingPort, intents_of, writer_over
from test_read_side import observed_dataset

from beliefs import audit_operation, boundary as boundary_values, stored
from beliefs.audit import NO_EVIDENCE
from beliefs.audit_operation import AuditOutcome, _finding_payload, audit
from beliefs.corpus import CorpusWriter, Finding, _operation_lock_for
from beliefs.errors import AuditRefused, BuildContended, MalformedRecord, PermitExceeded, PortMismatch
from beliefs.report import CLOSED, UNFINISHED, EvaluationFinding, OperationIntent, Registration, SubjectEvaluationEntry, completion


def stale_dataset(writer) -> str:
    """One `semantic-hash-stale` finding: a dataset raw-written with a body its stamp does not cover."""
    node = observed_dataset()
    node.facets[stored.DATASET_FACET]["resources"] = []
    raw_write(writer.root, node)
    writer._reconstruct()
    return node.id


class Ordered(RecordingPort):
    """The recording port with each call's *completion* logged to a shared list."""

    def __init__(self, authority, root, events: list[str]) -> None:
        super().__init__(authority, root)
        self.events = events

    def append_intent(self, payload):
        digest = super().append_intent(payload)
        self.events.append("appended")
        return digest

    def execute_fulfilling(self, plan, fulfills):
        digest = super().execute_fulfilling(plan, fulfills)
        self.events.append("closed")
        return digest


def run(writer, **kwargs) -> AuditOutcome:
    return audit(writer, observer="observer", instrument="instrument", evidence=NO_EVIDENCE, **kwargs)


def fulfilling(port: RecordingPort) -> list[tuple[tuple, str]]:
    return [payload for kind, payload in port.calls if kind == "execute_fulfilling"]


def test_a_clean_corpus_closes_through_one_report_with_no_entries(tmp_path):
    writer, port = writer_over(tmp_path)
    outcome = run(writer)
    assert outcome.findings == () and outcome.entries == ()
    assert outcome.report.operation == "audit" and outcome.report.entries == ()
    assert writer.read_view.holds(outcome.report_ref)
    (intent,) = intents_of(port)
    assert intent == OperationIntent("audit", outcome.report.event_token, FULL.actor)
    assert [kind for kind, _ in port.calls] == ["append_intent", "execute_fulfilling"]
    ((plan, fulfills),) = fulfilling(port)
    assert fulfills == "1" * 60 + "0001"  # the digest the append returned
    assert len(plan) == 1 and plan[0].path == f"act-report/{outcome.report.identity()}.md"
    assert completion(intent, (Registration(intent.event_token, outcome.report_ref),), {outcome.report_ref: outcome.report}) == CLOSED
    assert stored.act_report_facet(writer.read_view.get(outcome.report_ref))["event_token"] == intent.event_token


def test_findings_become_entries_in_the_evaluators_order_with_no_message(tmp_path):
    writer, _ = writer_over(tmp_path)
    ref = stale_dataset(writer)
    outcome = run(writer)
    assert [f.code for f in outcome.findings] == ["semantic-hash-stale"]
    (entry,) = outcome.entries
    assert entry == SubjectEvaluationEntry(ref, EvaluationFinding(_finding_payload(outcome.findings[0])))
    payload = json.loads(entry.outcome.payload)
    assert payload == {"severity": "error", "code": "semantic-hash-stale", "detail": "mismatch"}
    assert "message" not in payload
    assert outcome.report.entries == outcome.entries


def test_the_payload_is_invariant_under_a_reworded_message_and_moves_with_detail():
    finding = Finding("error", "c", "ref", "d", "one wording")
    assert _finding_payload(finding) == _finding_payload(replace(finding, message="another wording"))
    assert _finding_payload(finding) != _finding_payload(replace(finding, detail="e"))


def test_the_evaluator_runs_after_the_append_completes_and_before_the_close(tmp_path, monkeypatch):
    writer, _ = writer_over(tmp_path)
    events: list[str] = []
    real = audit_operation.audit_corpus

    def evaluator(view, *, evidence, profile):
        events.append("evaluated")
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    run(writer, port=Ordered(FULL, tmp_path, events))
    assert events == ["appended", "evaluated", "closed"]


@pytest.mark.parametrize(
    ("spoil", "refusal"),
    [
        ("no-port", AuditRefused),
        ("foreign-root-port", PortMismatch),
        ("empty-instrument", AuditRefused),
        ("unencodable-observer", AuditRefused),
        ("no-act-report-permit", PermitExceeded),
        ("evidence-type", MalformedRecord),
    ],
)
def test_every_pre_intent_refusal_appends_nothing_and_runs_the_evaluator_zero_times(tmp_path, spoil, refusal, monkeypatch):
    calls: list[object] = []
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda *a, **k: calls.append(a) or ())
    writer, port = writer_over(tmp_path)
    ports = [port]
    kwargs = {"observer": "observer", "instrument": "instrument", "evidence": NO_EVIDENCE}
    if spoil == "no-port":
        writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE)
    elif spoil == "foreign-root-port":
        (tmp_path / "other").mkdir()
        kwargs["port"] = RecordingPort(FULL, tmp_path / "other")
        ports.append(kwargs["port"])
    elif spoil == "empty-instrument":
        kwargs["instrument"] = ""
    elif spoil == "unencodable-observer":
        kwargs["observer"] = "\udcff"
    elif spoil == "no-act-report-permit":
        writer, port = writer_over(tmp_path, narrowed(kinds=("proposition",), families=("corpus-write",)))
        ports = [port]
    elif spoil == "evidence-type":
        kwargs["evidence"] = {}
    with pytest.raises(refusal):
        audit(writer, **kwargs)
    assert all(p.calls == [] for p in ports)
    assert calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_an_evaluator_failure_after_the_intent_propagates_and_reads_unfinished(tmp_path, monkeypatch):
    writer, port = writer_over(tmp_path)

    def failing(view, *, evidence, profile):
        raise RuntimeError("carrier failure")

    monkeypatch.setattr(audit_operation, "audit_corpus", failing)
    with pytest.raises(RuntimeError, match="carrier failure"):
        run(writer)
    assert [kind for kind, _ in port.calls] == ["append_intent"]
    (intent,) = intents_of(port)
    assert completion(intent, (), {}) == UNFINISHED
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def _held(lock) -> bool:
    seen: list[bool] = []

    def probe() -> None:
        try:
            with lock.capture():
                seen.append(False)
        except BuildContended:
            seen.append(True)

    thread = threading.Thread(target=probe)
    thread.start()
    thread.join(5)
    return seen == [True]


def test_the_hold_enters_before_the_root_lock_and_spans_the_evaluator(tmp_path, monkeypatch):
    writer, _ = writer_over(tmp_path)
    events: list[str] = []
    lock = _operation_lock_for(tmp_path)

    class Hold:
        def __enter__(self):
            events.append("hold-enter:" + ("held" if _held(lock) else "free"))
            return self

        def __exit__(self, *_exc):
            events.append("hold-exit:" + ("held" if _held(lock) else "free"))

    real = audit_operation.audit_corpus

    def evaluator(view, *, evidence, profile):
        events.append("evaluate:" + ("held" if _held(lock) else "free"))
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    run(writer, hold=Hold)
    assert events == ["hold-enter:free", "evaluate:held", "hold-exit:free"]


def test_the_mint_helper_refuses_the_wrong_intent_kind_and_the_wrong_entry_kind():
    from beliefs.report import LocatorEntry, RetrievalFailed

    now = "2026-09-22T00:00:00Z"
    entry = SubjectEvaluationEntry("proposition:" + "a" * 64, EvaluationFinding("{}"))
    with pytest.raises(MalformedRecord, match="audit operation intent"):
        boundary_values._mint_audit_report(OperationIntent("re-check", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    with pytest.raises(MalformedRecord, match="subject-evaluation entries only"):
        boundary_values._mint_audit_report(
            OperationIntent("audit", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now,
            entries=(LocatorEntry("url:https://example.org/a", RetrievalFailed("x")),),
        )
    report = boundary_values._mint_audit_report(OperationIntent("audit", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    assert report.operation == "audit" and report.entries == (entry,)
```

`writer_over(tmp_path, authority)` takes the authority as its second positional argument (`test_operation_writes.py` line 87); `RecordingPort._digest("1")` returns `"1" * 60 + "0001"` for the first append. `stale_dataset`, `Ordered` and `_held` are imported by Task 3's and Task 5's modules, so keep them module-level.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_audit_operation.py -q -p no:cacheprovider
```
Expected: FAIL at collection — `ModuleNotFoundError: No module named 'beliefs.audit_operation'`.

- [ ] **Step 3: The error and the minting helper**

`python/src/beliefs/errors.py`, directly after `class AcquisitionRefused(WriteRefused):` and its docstring:

```python
class AuditRefused(WriteRefused):
    """An audit operation refused before its intent — no operation port, an
    observer or instrument that is empty or not canonically encodable
    (act-report-remainder design §3 step 1)."""
```

`python/src/beliefs/boundary.py`: add `LocatorEntry` and `SubjectEvaluationEntry` to the `from beliefs.report import (…)` block (alphabetical). Directly after `_mint_acquisition_report`:

```python
def _mint_audit_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The audit operation's terminal record (act-report-remainder design §3):
    one subject-evaluation entry per finding, in the evaluator's order; a
    clean audit's entries are empty."""
    if type(intent) is not OperationIntent or intent.kind != "audit":
        raise MalformedRecord("an audit report requires an audit operation intent")
    if type(entries) is not tuple or any(type(entry) is not SubjectEvaluationEntry for entry in entries):
        raise MalformedRecord("an audit report carries subject-evaluation entries only")
    return _mint_report(
        operation="audit",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )
```

- [ ] **Step 4: The module** — `python/src/beliefs/audit_operation.py`:

```python
"""The audit operation (act-report-remainder design §3).

One operation intent, then `audit_corpus` over the writer's own view, then
one act-report carrying one subject-evaluation entry per finding — every
step under the caller's hold and the root lock, so the state the evaluator
judged is the state at the intent's chain position (decision 4). The
evaluator stays read-only (`audit.py` is not imported by anything that
writes); this wrapper reports.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import final

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.audit import audit_corpus
from beliefs.corpus import CorpusWriter, Finding
from beliefs.errors import AuditRefused, LoneSurrogate, MalformedRecord
from beliefs.evidence import DerivationEvidence
from beliefs.identity import v1
from beliefs.report import ActReport, EvaluationFinding, OperationIntent, SubjectEvaluationEntry
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed

__all__ = ["AuditOutcome", "audit"]


@sealed
@final
@dataclass(frozen=True)
class AuditOutcome:
    report: ActReport
    report_ref: str
    findings: tuple[Finding, ...]
    entries: tuple[SubjectEvaluationEntry, ...]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finding_payload(finding: Finding) -> str:
    """`severity`, `code` and `detail` — never `message`, which `Finding`
    makes normative for nothing (decision 3): a reworded message moves no
    report identity. A detail the canonical encoder refuses propagates."""
    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail}).decode("utf-8")


def _entry(finding: Finding) -> SubjectEvaluationEntry:
    return SubjectEvaluationEntry(finding.ref, EvaluationFinding(_finding_payload(finding)))


def audit(
    writer: CorpusWriter,
    *,
    observer: str,
    instrument: str,
    evidence: DerivationEvidence,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> AuditOutcome:
    """`hold` is the caller's outer lock — the session route passes the one
    `ScopedWriter._act` takes first — entered before the root lock and held,
    with it, across the evaluator's read (decision 4)."""
    # 1. Checks, before any effect (§3 step 1).
    if type(evidence) is not DerivationEvidence:
        raise MalformedRecord("audit takes a DerivationEvidence")
    writer.authority.require("corpus-write", ("act-report",))
    for name, value in (("observer", observer), ("instrument", instrument)):
        if type(value) is not str or not value:
            raise AuditRefused(f"audit {name} must be a non-empty string")
    try:
        v1.encode({"actor": writer.authority.actor, "observer": observer, "instrument": instrument})
    except LoneSurrogate as caught:
        raise AuditRefused(f"audit report fields are not canonically encodable: {caught}") from caught
    if port is None and writer._operation_port is None:
        raise AuditRefused("this corpus has no operation port; audit is a boundary operation")
    writer._require_bound_port(port)
    # 2. The hold: the caller's, then the root's (decision 4).
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:
        # 3. Open.
        intent = OperationIntent("audit", secrets.token_hex(16), writer.authority.actor)
        opened_at = _now()
        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
        # 4. Act: the read after the intent, so the chain position names the state judged.
        writer._reconstruct()
        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)
        # 5. Close.
        entries = tuple(_entry(finding) for finding in findings)
        closed_at = _now()
        report = boundary_values._mint_audit_report(
            intent, observer=observer, instrument=instrument, opened_at=opened_at, closed_at=closed_at, entries=entries,
        )
        report_ref = stored.act_report_node(report).id
        writer._publish_operation_report(report, intent_digest, port=port)
    return AuditOutcome(report, report_ref, findings, entries)
```

- [ ] **Step 5: Run the tests**

```bash
cd python && uv run --frozen pytest tests/test_audit_operation.py -q -p no:cacheprovider
```
Expected: all pass, with no `SCIENCE_CUT*` export — every test runs on `tmp_path`. If `test_the_hold_enters_before_the_root_lock_and_spans_the_evaluator` reports `evaluate:free`, the root lock the probe captures is not the one `writer._operation` takes — `_root_state_for(root, …)` and `_operation_lock_for(root)` are both keyed by the root, so check that the writer was opened on exactly `tmp_path` before touching the wrapper.

- [ ] **Step 6: The inventories and the evaluator's read-only standing**

```bash
cd python && uv run --frozen pytest tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py tests/test_audit.py tests/test_report.py tests/test_stored_act_report.py -q
uv run --frozen pyright && uv run --frozen ruff check .
```
Expected: green. `audit_operation.py` calls no primitive (`_append_operation_intent` and `_publish_operation_report` are method calls on the writer, not primitive attributes), so `test_the_inventory_is_closed_in_both_directions` (or its current name — `grep -n "uninventoried primitive callers" tests/test_permit_boundary.py`) still passes.

- [ ] **Step 7: Commit**

```bash
tasks check && git add python/src/beliefs/audit_operation.py python/src/beliefs/boundary.py python/src/beliefs/errors.py python/tests/test_audit_operation.py tasks
git commit -m "feat(report): the audit operation — one intent, the evaluator under the hold, one report; T2"
```

---

### Task 3: The re-check operation — `beliefs/holdings/recheck.py`

**Files:**
- Create: `python/src/beliefs/holdings/recheck.py`, `python/tests/test_holdings_recheck.py`
- Modify: `python/src/beliefs/boundary.py` (`_mint_recheck_report`), `python/src/beliefs/errors.py` (`RecheckRefused`)

**Interfaces:**
- Consumes: `holdings/boundary.py`'s `recheck(ctx, location, *, standing=()) -> PublishedObservation | InconclusiveAttempt` (the act; `PublishedObservation.record: HoldingsObservation`, `InconclusiveAttempt.report: str, reason: str, detail: str`), `ActContext` (`observer_root`, `store_root`, `observer`, `instrument`, `authority`, `seam`, `profile`, `.actor`); `parse_store_genesis(ctx.seam.store_genesis(root)) -> (store_id, …)`; Task 1's `_require_bound_port`; the writer primitives as in Task 2.
- Produces: `recheck_locations(ctx, writer, locations, *, standing=None, port=None, hold=None) -> RecheckOutcome`; `RecheckOutcome(report, report_ref, entries, results)`; `boundary._mint_recheck_report(intent, *, observer, instrument, opened_at, closed_at, entries) -> ActReport`; `RecheckRefused(WriteRefused)`.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_holdings_recheck.py`, portable (spec §9.1): the writer and its recording port, and a store seam whose publications land on disk through `DefaultExecutor`, whose reads are scripted per path, and whose every call joins one event list with the port's:

```python
"""The re-check operation (act-report-remainder design §4) — portable, over a recording port and a scripted store seam."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path

import pytest
from authority import FULL, narrowed
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE
from test_audit_operation import Ordered, _held
from test_operation_writes import RecordingPort, intents_of, writer_over

from beliefs import boundary as boundary_values, stored
from beliefs.corpus import CorpusWriter, _operation_lock_for
from beliefs.errors import MalformedRecord, PermitExceeded, PortMismatch, RecheckRefused
from beliefs.holdings.boundary import ActContext, InconclusiveAttempt
from beliefs.holdings.records import Found, StoreLocator, holdings_observation
from beliefs.holdings.recheck import RecheckOutcome, recheck_locations
from beliefs.holdings.seam import FileStateView, PathObservedView, ReadNotAttemptedView, ReadUnestablishedView, StoreActSeam
from beliefs.report import CLOSED, ByteLocatorUntested, LocatorEntry, OperationIntent, PublishedObservation, Registration, RetrievalFailed, completion

STORE_ID = "1" * 32
GENESIS = b'{"domain":"science.store-root.v1","store_id":"' + STORE_ID.encode() + b'"}'
FOUND = PathObservedView(FileStateView("sha256:" + "a" * 64))


@dataclass
class ScriptedStore:
    """A store seam over the observer root's plain executor: holdings intents counted, publications on disk, reads scripted per path."""

    root: Path
    views: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    intents: list[bytes] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)

    def build(self) -> StoreActSeam:
        executor = DefaultExecutor(self.root)

        @contextmanager
        def corpus_lock(root):
            with _operation_lock_for(root):
                yield

        def append_intent(_root, payload):
            self.intents.append(payload)
            self.events.append("holdings-intent")
            return sha256(payload).hexdigest()

        def publish_fulfilling(_root, plan, _intent):
            executor.execute(list(plan))
            self.events.append("published")
            return "2" * 64

        def read_path(_root, path):
            self.reads.append(path)
            self.events.append("read")
            return self.views.get(path, FOUND)

        def unused(*_):
            raise AssertionError("not reached")

        return StoreActSeam(corpus_lock, append_intent, publish_fulfilling, read_path, unused, unused, unused, lambda _root: GENESIS, lambda _caught: False)


def portable(tmp_path, views=None):
    observer_root, store_root = tmp_path / "observer", tmp_path / "store"
    observer_root.mkdir()
    store_root.mkdir()
    seam = ScriptedStore(observer_root, {} if views is None else views)
    ctx = ActContext(observer_root, store_root, "observer", "instrument", FULL, seam.build(), profile=BASE)
    port = Ordered(FULL, observer_root, seam.events)
    writer = CorpusWriter(observer_root, DefaultExecutor, authority=FULL, operation_port=port, profile=BASE)
    return ctx, seam, writer, port


def location(name: str) -> StoreLocator:
    return StoreLocator(STORE_ID, name)


def test_two_locations_close_through_one_report_after_one_operation_intent(tmp_path):
    ctx, seam, writer, port = portable(tmp_path)
    a, b = location("a.bin"), location("b.bin")
    outcome = recheck_locations(ctx, writer, (a, b))
    assert isinstance(outcome, RecheckOutcome)
    assert seam.events == ["appended", "holdings-intent", "read", "published", "holdings-intent", "read", "published", "closed"]
    (intent,) = intents_of(port)
    assert intent == OperationIntent("re-check", outcome.report.event_token, FULL.actor)
    assert len(seam.intents) == 2 and all(json.loads(i)["kind"] == "re-check" for i in seam.intents)
    assert [e.subject for e in outcome.entries] == [a.canonical(), b.canonical()]
    assert all(type(e) is LocatorEntry and type(e.outcome) is PublishedObservation and e.instrument_inputs == () for e in outcome.entries)
    for entry in outcome.entries:
        assert writer.read_view.holds(entry.outcome.ref)
    assert writer.read_view.holds(outcome.report_ref)
    ((plan, fulfills),) = [payload for kind, payload in port.calls if kind == "execute_fulfilling"]
    assert fulfills == "1" * 60 + "0001"
    assert completion(intent, (Registration(intent.event_token, outcome.report_ref),), {outcome.report_ref: outcome.report}) == CLOSED
    assert outcome.report.entries == outcome.entries


def test_an_inconclusive_location_is_an_entry_with_the_reason_only_and_the_operation_still_closes(tmp_path):
    views = {"b.bin": ReadNotAttemptedView(reason="lease-refused", lifecycle_state=None, detail="/secret/path must not enter the record")}
    ctx, seam, writer, _ = portable(tmp_path, views)
    a, b = location("a.bin"), location("b.bin")
    outcome = recheck_locations(ctx, writer, (a, b))
    assert type(outcome.entries[0].outcome) is PublishedObservation
    assert outcome.entries[1] == LocatorEntry(b.canonical(), ByteLocatorUntested("lease-refused"))
    assert isinstance(outcome.results[1], InconclusiveAttempt)
    assert "/secret/path" not in json.dumps(stored.act_report_facet(writer.read_view.get(outcome.report_ref)))
    assert seam.events[-1] == "closed"


def test_an_unestablished_read_spells_retrieval_failed(tmp_path):
    ctx, _, writer, _ = portable(tmp_path, {"a.bin": ReadUnestablishedView(reason="io-error", detail="d")})
    a = location("a.bin")
    outcome = recheck_locations(ctx, writer, (a,))
    assert outcome.entries == (LocatorEntry(a.canonical(), RetrievalFailed("io-error")),)


def test_a_standing_head_is_superseded_by_the_new_observation(tmp_path):
    ctx, _, writer, _ = portable(tmp_path)
    a = location("a.bin")
    first = recheck_locations(ctx, writer, (a,))
    head = stored.holdings_observation_value(writer.read_view.get(first.entries[0].outcome.ref))
    second = recheck_locations(ctx, writer, (a,), standing={a.canonical(): (head,)})
    new = stored.holdings_observation_value(writer.read_view.get(second.entries[0].outcome.ref))
    assert new.supersedes == (head.identity(),)


@pytest.mark.parametrize(
    ("spoil", "refusal"),
    [
        ("not-a-tuple", MalformedRecord),
        ("empty", MalformedRecord),
        ("duplicate", RecheckRefused),
        ("foreign-store", RecheckRefused),
        ("wrong-root", RecheckRefused),
        ("no-port", RecheckRefused),
        ("foreign-root-port", PortMismatch),
        ("empty-instrument", RecheckRefused),
        ("unencodable-observer", RecheckRefused),
        ("standing-elsewhere", RecheckRefused),
        ("standing-unrequested", RecheckRefused),
        ("no-holdings-permit", PermitExceeded),
    ],
)
def test_every_pre_intent_refusal_appends_no_intent_of_either_grain_and_reads_nothing(tmp_path, spoil, refusal):
    ctx, seam, writer, port = portable(tmp_path)
    a = location("a.bin")
    locations: object = (a,)
    kwargs: dict = {}
    ports = [port]
    if spoil == "not-a-tuple":
        locations = [a]
    elif spoil == "empty":
        locations = ()
    elif spoil == "duplicate":
        locations = (a, StoreLocator(STORE_ID, "a.bin"))
    elif spoil == "foreign-store":
        locations = (a, StoreLocator("f" * 32, "x.bin"))
    elif spoil == "wrong-root":
        (tmp_path / "other").mkdir()
        writer, other_port = writer_over(tmp_path / "other")
        ports.append(other_port)
    elif spoil == "no-port":
        writer = CorpusWriter(ctx.observer_root, DefaultExecutor, authority=FULL, profile=BASE)
    elif spoil == "foreign-root-port":
        (tmp_path / "other").mkdir()
        kwargs["port"] = RecordingPort(FULL, tmp_path / "other")
        ports.append(kwargs["port"])
    elif spoil == "empty-instrument":
        ctx = replace(ctx, instrument="")
    elif spoil == "unencodable-observer":
        ctx = replace(ctx, observer="\udcff")
    elif spoil == "standing-elsewhere":
        elsewhere = holdings_observation(
            location=location("b.bin"), outcome=Found("sha256:" + "0" * 64), observer="o", instrument="i",
            event_token="t", observed_at="2026-09-22T00:00:00Z",
        )
        kwargs["standing"] = {a.canonical(): (elsewhere,)}
    elif spoil == "standing-unrequested":
        kwargs["standing"] = {location("b.bin").canonical(): ()}
    elif spoil == "no-holdings-permit":
        ctx = replace(ctx, authority=narrowed(kinds=("act-report",), families=("corpus-write",)))
    with pytest.raises(refusal):
        recheck_locations(ctx, writer, locations, **kwargs)  # type: ignore[arg-type]
    assert all(p.calls == [] for p in ports)
    assert seam.intents == [] and seam.reads == [] and seam.events == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_no_lock_is_held_across_the_acts_and_the_hold_enters_before_the_root_lock_at_the_close(tmp_path):
    ctx, seam, writer, _ = portable(tmp_path)
    a = location("a.bin")
    events: list[str] = []
    lock = _operation_lock_for(ctx.observer_root)
    inner = ctx.seam.read_path

    def reading(root, path):
        events.append("read:" + ("held" if _held(lock) else "free"))
        return inner(root, path)

    class Hold:
        def __enter__(self):
            events.append("hold-enter:" + ("held" if _held(lock) else "free"))
            return self

        def __exit__(self, *_exc):
            events.append("hold-exit:" + ("held" if _held(lock) else "free"))

    ctx = replace(ctx, seam=replace(ctx.seam, read_path=reading))
    recheck_locations(ctx, writer, (a,), hold=Hold)
    assert events == ["read:free", "hold-enter:free", "hold-exit:free"]


def test_the_close_rebuilds_the_view_and_refuses_a_ref_no_act_published(tmp_path, monkeypatch):
    ctx, _, writer, port = portable(tmp_path)
    monkeypatch.setattr(writer, "_reconstruct", lambda: None)  # the act published past this writer's cached index
    with pytest.raises(RecheckRefused, match="no act published"):
        recheck_locations(ctx, writer, (location("a.bin"),))
    assert [kind for kind, _ in port.calls] == ["append_intent"]  # the intent stands; nothing fulfilled it


def test_the_mint_helper_refuses_the_wrong_intent_kind_and_the_wrong_entry_kind():
    from beliefs.report import EvaluationFinding, SubjectEvaluationEntry

    now = "2026-09-22T00:00:00Z"
    entry = LocatorEntry(location("x.bin").canonical(), RetrievalFailed("x"))
    with pytest.raises(MalformedRecord, match="re-check operation intent"):
        boundary_values._mint_recheck_report(OperationIntent("audit", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    with pytest.raises(MalformedRecord, match="locator entries only"):
        boundary_values._mint_recheck_report(
            OperationIntent("re-check", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now,
            entries=(SubjectEvaluationEntry("proposition:" + "a" * 64, EvaluationFinding("{}")),),
        )
    report = boundary_values._mint_recheck_report(OperationIntent("re-check", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    assert report.operation == "re-check" and report.entries == (entry,)
```

Fixture facts, verified 2026-09-22: `ReadNotAttemptedView(reason, lifecycle_state, detail)` and `ReadUnestablishedView(reason, detail)` (`holdings/seam.py` lines 38–47); `stored.holdings_observation_value(node)` decodes a stored observation (`stored.py` line 826) and `HoldingsObservation.supersedes` is the sorted tuple of predecessor identities (`records.py` line 325); `StoreActSeam`'s nine positional fields are `corpus_lock, append_intent, publish_fulfilling, read_path, store_write, store_delete, store_move, store_genesis, store_refusal` (`seam.py` line 60), and `parse_store_genesis` reads the `GENESIS` bytes above (`test_session_routes.py`'s `FakeSeam` supplies the same); `require_pins_agree` returns on a manifest-less root (`corpus.py` line 1719), so no `adopt_manifest` is needed; `_operation_lock_for(root)` is process-local and keyed by root, so the scripted seam's `corpus_lock` and the writer's `_operation` are one lock on `tmp_path` exactly as on a durable root.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_holdings_recheck.py -q -p no:cacheprovider
```
Expected: FAIL at collection — `ModuleNotFoundError: No module named 'beliefs.holdings.recheck'`.

- [ ] **Step 3: The error and the minting helper**

`python/src/beliefs/errors.py`, directly after `AuditRefused`:

```python
class RecheckRefused(WriteRefused):
    """A re-check operation refused before its intent — duplicate locations, a
    foreign store, the wrong root, no operation port, an observer or
    instrument the observation would refuse, a `standing` set at another
    location or for an unrequested one (act-report-remainder design §4 step 1,
    decision 14) — or at its close, when the report would name an observation
    no act published."""
```

`python/src/beliefs/boundary.py`, directly after `_mint_audit_report`:

```python
def _mint_recheck_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The re-check operation's terminal record (act-report-remainder design
    §4): one locator entry per requested location, in request order."""
    if type(intent) is not OperationIntent or intent.kind != "re-check":
        raise MalformedRecord("a re-check report requires a re-check operation intent")
    if type(entries) is not tuple or any(type(entry) is not LocatorEntry for entry in entries):
        raise MalformedRecord("a re-check report carries locator entries only")
    return _mint_report(
        operation="re-check",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )
```

- [ ] **Step 4: The module** — `python/src/beliefs/holdings/recheck.py`:

```python
"""The re-check operation (act-report-remainder design §4).

One operation intent, then per location the `recheck` act as built — its own
holdings intent, its own observation — then one closing transaction carrying
the act-report: one locator entry per location, in request order. No
cooperative stop: the close mints nothing that depends on any location
(decision 5). Nothing is held across the acts; the close takes the caller's
hold and then the root lock, the view rebuilt before any ref resolves
(decision 6). Every check the acts would make late is made before the
intent (decision 14).
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import final

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import LoneSurrogate, MalformedRecord, RecheckRefused
from beliefs.holdings.boundary import ActContext, ActResult, InconclusiveAttempt, recheck
from beliefs.holdings.records import HoldingsObservation, StoreLocator
from beliefs.identity import v1
from beliefs.report import ActReport, ByteLocatorUntested, LocatorEntry, OperationIntent, PublishedObservation, RetrievalFailed
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.world.anchors import parse_store_genesis

__all__ = ["RecheckOutcome", "recheck_locations"]


@sealed
@final
@dataclass(frozen=True)
class RecheckOutcome:
    report: ActReport
    report_ref: str
    entries: tuple[LocatorEntry, ...]
    results: tuple[ActResult, ...]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_identity_text(value: object, name: str) -> None:
    """`holdings_observation`'s rule for observer and instrument, made before
    the intent rather than after the read (decision 14)."""
    if type(value) is not str or not value:
        raise RecheckRefused(f"a re-check's {name} must be a non-empty string")
    try:
        v1.encode(value)
    except LoneSurrogate as caught:
        raise RecheckRefused(f"a re-check's {name} must encode as identity text") from caught


def recheck_locations(
    ctx: ActContext,
    writer: CorpusWriter,
    locations: tuple[StoreLocator, ...],
    *,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> RecheckOutcome:
    """`hold` is the caller's outer lock for the close — the session route
    passes the one `ScopedWriter._act` takes first — entered before the root
    lock and never around an act (decision 6)."""
    # 1. Checks, before any effect (§4 step 1).
    if type(locations) is not tuple or not locations or any(type(location) is not StoreLocator for location in locations):
        raise MalformedRecord("recheck_locations takes a non-empty tuple of StoreLocator values")
    canonicals = [location.canonical() for location in locations]
    if len(set(canonicals)) != len(canonicals):
        raise RecheckRefused("re-check locations are unique by canonical spelling")
    heads: dict[str, tuple[HoldingsObservation, ...]] = {} if standing is None else dict(standing)
    for key, predecessors in heads.items():
        if key not in canonicals:
            raise RecheckRefused(f"{key}: standing names a location this re-check does not request")
        if type(predecessors) is not tuple or any(
            type(predecessor) is not HoldingsObservation or predecessor.location.canonical() != key for predecessor in predecessors
        ):
            raise RecheckRefused(f"{key}: standing holds only HoldingsObservation values at that canonical location")
    ctx.authority.require("holdings", ("holdings-observation",))
    ctx.authority.require("corpus-write", ("act-report",))
    _require_identity_text(ctx.observer, "observer")
    _require_identity_text(ctx.instrument, "instrument")
    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():
        raise RecheckRefused("the writer's root is not the act context's observer root; a re-check publishes in one root")
    if port is None and writer._operation_port is None:
        raise RecheckRefused("this corpus has no operation port; re-check is a boundary operation")
    writer._require_bound_port(port)
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    for location in locations:
        if location.store_id != store_id:
            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")
    # 2. Open.
    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)
    opened_at = _now()
    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
    # 3. Acts, in request order, nothing held across them.
    entries: list[LocatorEntry] = []
    results: list[ActResult] = []
    published: list[str] = []
    for location, canonical in zip(locations, canonicals, strict=True):
        result = recheck(ctx, location, standing=heads.get(canonical, ()))
        results.append(result)
        if isinstance(result, InconclusiveAttempt):
            outcome = ByteLocatorUntested(result.reason) if result.report == "byte-locator-untested" else RetrievalFailed(result.reason)
            entries.append(LocatorEntry(canonical, outcome))
            continue
        ref = f"holdings-observation:{result.record.identity()}"
        published.append(ref)
        entries.append(LocatorEntry(canonical, PublishedObservation(ref)))
    # 4. Close.
    closed_at = _now()
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:  # the caller's hold, then the root: `_act`'s order
        writer._reconstruct()  # the acts published through the holdings seam, past this writer's cached index
        for ref in published:
            if writer.read_view.resolve(ref) is None:
                raise RecheckRefused(f"{ref}: the report would reference an observation no act published")
        report = boundary_values._mint_recheck_report(
            intent, observer=ctx.observer, instrument=ctx.instrument, opened_at=opened_at, closed_at=closed_at,
            entries=tuple(entries),
        )
        report_ref = stored.act_report_node(report).id
        writer._publish_operation_report(report, intent_digest, port=port)
    return RecheckOutcome(report, report_ref, tuple(entries), tuple(results))
```

`ActResult` is `PublishedObservation | InconclusiveAttempt` in `holdings/boundary.py`; if it is not exported by name, import `PublishedObservation as PublishedAct` from there and spell the union locally. The `PublishedObservation` imported above is `report.py`'s outcome value, not the boundary's act result — do not conflate them.

- [ ] **Step 5: Run the tests**

```bash
cd python && uv run --frozen pytest tests/test_holdings_recheck.py tests/test_holdings_boundary.py tests/test_holdings_acquire.py -q -p no:cacheprovider
```
Expected: `test_holdings_recheck.py` all pass with no `SCIENCE_CUT*` export; the other two modules unchanged (they need the certified exports as before).

- [ ] **Step 6: The inventories**

```bash
cd python && uv run --frozen pytest tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py -q
uv run --frozen pyright && uv run --frozen ruff check .
```
Expected: green.

- [ ] **Step 7: Commit**

```bash
tasks check && git add python/src/beliefs/holdings/recheck.py python/src/beliefs/boundary.py python/src/beliefs/errors.py python/tests/test_holdings_recheck.py tasks
git commit -m "feat(holdings): the re-check operation — one intent, independent store re-checks, one report; T2"
```

---

### Task 4: The session routes — `ScopedWriter.audit` and `ScopedWriter.recheck`

**Files:**
- Modify: `python/src/beliefs/session/writer.py` (two methods after `acquire`), `python/tests/test_session_routes.py`

**Interfaces:**
- Consumes: Task 2's `audit`, Task 3's `recheck_locations`; `ScopedWriter.operation_port()`, `holdings_context(instrument=…)`, `_closing_hold`, `self._session.actor`, `self._writer`.
- Produces: `ScopedWriter.audit(*, instrument, evidence) -> AuditOutcome`; `ScopedWriter.recheck(locations, *, instrument, standing=None) -> RecheckOutcome`. Task 5's BI-3 calls both.

- [ ] **Step 1: Write the failing tests** — `python/tests/test_session_routes.py`, after `test_acquire_through_a_session_ledgers_every_commit`:

```python
AUDITS = RequiredCapabilities.for_kinds({"act-report"}, {"act-report": "corpus-write"})
RECHECKS = RequiredCapabilities.for_kinds({"holdings-observation", "act-report"}, {"act-report": "corpus-write"})


def test_audit_through_a_session_ledgers_its_one_commit_and_names_the_session_actor(certified_work):
    from beliefs.audit import NO_EVIDENCE

    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(AUDITS, "A")
    outcome = scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    assert outcome.report.observer == session.actor and outcome.report.actor == session.actor
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 1
    assert {pair[1] for act in acts for pair in act.record_ids} == {outcome.report_ref}


def test_recheck_through_a_session_ledgers_every_commit(certified_work):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "recheck", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    ctx = scoped.holdings_context(instrument="inst")
    location = StoreLocator(scoped.store_id, "a.bin")
    write(ctx, location, b"alpha")
    outcome = scoped.recheck((location,), instrument="inst")
    assert outcome.report.observer == session.actor
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 3  # the write's publication, the re-check's publication, the closing transaction
    assert {pair[1] for act in acts for pair in act.record_ids} >= {outcome.report_ref, outcome.entries[0].outcome.ref}


def test_a_store_less_session_audits_and_cannot_recheck(certified_work):
    from beliefs.audit import NO_EVIDENCE

    corpus_root = certified_work / "corpus"
    init_corpus_root(corpus_root, authority=FULL)
    open_corpus(corpus_root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    config = WorldConfig(certified_work / "world", "a" * 32, (corpus_root,))
    session = open_attended_session(config, certified_work / "ops", profile=BASE)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    assert scoped.audit(instrument="inst", evidence=NO_EVIDENCE).entries == ()
    with pytest.raises(SessionProtocolError, match="no store root"):
        scoped.recheck((StoreLocator("a" * 32, "a.bin"),), instrument="inst")
    session.close_invocation("A", {"done": []})
    session.close()


def test_the_routes_refuse_after_the_invocation_closes(certified_work):
    from beliefs.audit import NO_EVIDENCE

    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    with pytest.raises(SessionProtocolError):
        scoped.recheck((StoreLocator(scoped.store_id, "a.bin"),), instrument="inst")
    session.close()
```

If `session.scoped(RECHECKS, "A")` refuses in the store-less session (a capability the session cannot supply), scope with `AUDITS` for the audit there and assert the refusal at `scoped(RECHECKS, …)` instead of at `recheck`. Check the ledger-act count in the re-check test against `test_acquire_through_a_session_ledgers_every_commit` (two acts for one look and one close): a managed `write` through the ledgered seam publishes one fulfilling transaction, the re-check act another, the close a third. If the count reads differently, print `acts` and correct the number — the assertion that matters is the report and the observation both appearing.

- [ ] **Step 2: Run to verify they fail**

```bash
cd python && uv run --frozen pytest tests/test_session_routes.py -q -p no:cacheprovider -k "audit or recheck or store_less or routes_refuse"
```
Expected: FAIL — `AttributeError: 'ScopedWriter' object has no attribute 'audit'`.

- [ ] **Step 3: The routes** — `python/src/beliefs/session/writer.py`, after `acquire` and before `_closing_hold`:

```python
    def audit(self, *, instrument: str, evidence: DerivationEvidence) -> AuditOutcome:
        """This invocation's audit route (act-report-remainder design §5): the
        ledgered operation port, and this session's lock taken before the root
        lock across the whole operation — the evaluator reads the writer's own
        index and does no I/O outside the root (decision 4)."""
        from beliefs.audit_operation import audit as run_audit

        return run_audit(
            self._writer, observer=self._session.actor, instrument=instrument, evidence=evidence,
            port=self.operation_port(), hold=self._closing_hold,
        )

    def recheck(
        self,
        locations: tuple[StoreLocator, ...],
        *,
        instrument: str,
        standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    ) -> RecheckOutcome:
        """This invocation's re-check route (act-report-remainder design §5):
        the holdings context supplies the ledgered store seam, `operation_port()`
        the ledgered operation port, and no lock of this facade is held across
        an act (decision 6)."""
        from beliefs.holdings.recheck import recheck_locations

        ctx = self.holdings_context(instrument=instrument)
        return recheck_locations(
            ctx, self._writer, locations, standing=standing, port=self.operation_port(), hold=self._closing_hold,
        )
```

Add the type-only imports beside the existing ones (`grep -n "AcquisitionOutcome" src/beliefs/session/writer.py` shows how `acquire`'s are brought in — under `TYPE_CHECKING` or at module level; follow that): `AuditOutcome` from `beliefs.audit_operation`, `RecheckOutcome` from `beliefs.holdings.recheck`, `DerivationEvidence` from `beliefs.evidence`, `StoreLocator` and `HoldingsObservation` from `beliefs.holdings.records`.

- [ ] **Step 4: Run the tests**

```bash
cd python && uv run --frozen pytest tests/test_session_routes.py tests/test_session_writer.py tests/test_session_ledger.py -q -p no:cacheprovider
uv run --frozen pytest tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py -q
uv run --frozen pyright && uv run --frozen ruff check .
```
Expected: green.

- [ ] **Step 5: Commit**

```bash
tasks check && git add python/src/beliefs/session/writer.py python/tests/test_session_routes.py tasks
git commit -m "feat(session): audit and re-check routes through the ledgered port — T2, decision 8"
```

---

### Task 5: The acceptance module — real roots on the certified volume

**Files:**
- Create: `python/tests/acceptance/test_act_report_remainder_acceptance.py`

**Interfaces:**
- Consumes: Tasks 1–4. Fixtures reused from `tests/acceptance/test_url_retrieval_acceptance.py` (`observer`, `intents`, `kinds`, `registrations`, `world_over`, `reduce`), `tests/test_holdings_acquire.py` (`chain`, `registrations_of`), `tests/test_session_routes.py` (`_durable_session`, `DIGEST`, and Task 4's `AUDITS`, `RECHECKS`), `tests/test_audit_operation.py` (`stale_dataset`), `tests/test_permit_boundary.py` (`modules`, `relative`, `parsed`, `primitive_callers`, `WRITE_ENTRY_POINTS`), `tests/test_world_log_codecs.py` (`Chain`, `ChainOutcome`, `state_at`) and `atoms.chain.model.SettledEntry` — the raw-chain forgery helpers cut 35's T2-d imports (`sed -n 25,50p tests/acceptance/test_url_retrieval_acceptance.py`); `beliefs.holdings.receipt.output_digest`.
- Produces: twelve test functions whose names Task 6's `UNIT_CHECKS` cites, plus two plain tests.

- [ ] **Step 1: Write the module.** Header and helpers:

```python
"""Conformance cut 38 — the act-report remainder: `audit` and `re-check` open
through the boundary (act-report-remainder design §9.2). Twelve declaration
units over real roots on the certified volume, and two plain tests."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import threading
from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from profiles import BASE
from test_audit_operation import stale_dataset
from test_holdings_acquire import chain, registrations_of
from test_operation_writes import proposition
from test_permit_boundary import WRITE_ENTRY_POINTS, modules, parsed, primitive_callers, relative
from test_session_routes import _durable_session, DIGEST, AUDITS, RECHECKS
from test_url_retrieval_acceptance import intents, kinds, observer, reduce, registrations, world_over
from test_world_log_codecs import Chain, ChainOutcome, state_at
from atoms.chain.model import SettledEntry  # the raw-chain forgery, as cut 35's T2-d spells it; a test, not a boundary module
from nodes.core.errors import ExecutionError

from beliefs import audit_operation, boundary as boundary_values, root as science_root, stored
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.audit_operation import audit
from beliefs.corpus import CorpusWriter, Finding
from beliefs.errors import AuditRefused, PortMismatch, RecheckRefused
from beliefs.holdings.boundary import write
from beliefs.holdings.receipt import output_digest
from beliefs.holdings.records import StoreLocator
from beliefs.holdings.recheck import recheck_locations
from beliefs.holdings.seam import ReadNotAttemptedView, ReadUnestablishedView
from beliefs.report import CLOSED, INDETERMINATE, ByteLocatorUntested, LocatorEntry, OperationIntent, Registration, RetrievalFailed, cite, completion
from beliefs.root import durable_executor_factory, init_corpus_root, open_corpus
from beliefs.session import open_ledger_reader
from beliefs.world.logmodel import IntentEntryView, MalformedView, RegisteredEntryView

__all__ = ["observer"]  # the fixture is re-exported for pytest's collection


def operation_intent(root: Path, kind: str) -> IntentEntryView:
    """The one operation intent of `kind` — the holdings intents of the same kind carry a `location`."""
    (entry,) = [e for e in intents(root) if json.loads(e.payload).get("kind") == kind and "location" not in json.loads(e.payload)]
    return entry


def closed(root: Path, kind: str, report_ref: str, report) -> bool:
    entry = operation_intent(root, kind)
    value = OperationIntent(kind, json.loads(entry.payload)["event_token"], report.actor)
    return completion(value, registrations_of(chain(root), entry.digest, report_ref), {report_ref: report}) == CLOSED


def held(ctx, store_id: str, name: str, body: bytes) -> StoreLocator:
    location = StoreLocator(store_id, name)
    write(ctx, location, body)
    return location


def run_audit(writer: CorpusWriter, **kwargs):
    return audit(writer, observer="observer", instrument="instrument", evidence=NO_EVIDENCE, **kwargs)


class CountingPort:
    """The durable port with every fulfilling submission counted (T2-h)."""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.submissions = 0

    @property
    def root(self):
        return self._inner.root

    @property
    def profile(self):
        return self._inner.profile

    @property
    def authority(self):
        return self._inner.authority

    def append_intent(self, payload):
        return self._inner.append_intent(payload)

    def preflight(self, plan):
        self._inner.preflight(plan)

    def execute(self, plan):
        self._inner.execute(plan)

    def execute_fulfilling(self, plan, fulfills):
        self.submissions += 1
        return self._inner.execute_fulfilling(plan, fulfills)

    def execute_fulfilling_guarded(self, plan, fulfills, *, guard, fallback):
        return self._inner.execute_fulfilling_guarded(plan, fulfills, guard=guard, fallback=fallback)


class RefusingPort(CountingPort):
    def append_intent(self, payload):
        raise ExecutionError("refused", index=None, applied=0)
```

The twelve units and two plain tests:

```python
# --- T2 ----------------------------------------------------------------------------


def test_t2e_an_audit_closes_through_exactly_one_report_after_its_intent_and_the_evaluator_ran_between_durably(observer, monkeypatch):
    ctx, writer = observer.ctx, observer.writer
    events: list[str] = []
    inner = writer._operation_port

    class Recording(CountingPort):
        """Each call's *completion* is logged after the durable port returns."""

        def append_intent(self, payload):
            digest = super().append_intent(payload)
            events.append("appended")
            return digest

        def execute_fulfilling(self, plan, fulfills):
            digest = super().execute_fulfilling(plan, fulfills)
            events.append("closed")
            return digest

    real = audit_operation.audit_corpus
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: events.append("evaluated") or real(view, evidence=evidence, profile=profile))
    outcome = run_audit(writer, port=Recording(inner))
    assert events == ["appended", "evaluated", "closed"]
    entry = operation_intent(ctx.observer_root, "audit")
    entries = chain(ctx.observer_root)  # one captured read; every read constructs fresh entry objects, so compare digests
    positions = [
        i for i, e in enumerate(entries)
        if (isinstance(e, IntentEntryView) and e.digest == entry.digest) or (isinstance(e, RegisteredEntryView) and e.fulfills == entry.digest)
    ]
    assert len(positions) == 2 and positions[0] < positions[1]
    assert len(registrations_of(chain(ctx.observer_root), entry.digest, outcome.report_ref)) == 1
    assert closed(ctx.observer_root, "audit", outcome.report_ref, outcome.report)


def test_t2f_a_recheck_closes_through_one_report_and_its_operation_intent_precedes_every_holdings_intent_durably(observer):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a, b = held(ctx, store_id, "a.bin", b"alpha"), held(ctx, store_id, "b.bin", b"beta")
    before = len(intents(ctx.observer_root))
    outcome = recheck_locations(ctx, writer, (a, b))
    later = intents(ctx.observer_root)[before:]
    assert [json.loads(e.payload).get("kind") for e in later] == ["re-check", "re-check", "re-check"]
    assert "location" not in json.loads(later[0].payload) and all("location" in json.loads(e.payload) for e in later[1:])
    fulfilled = {e.fulfills for e in registrations(ctx.observer_root)}
    assert {e.digest for e in later} <= fulfilled  # every holdings intent fulfilled by its observation, the operation's by the report
    assert len(registrations_of(chain(ctx.observer_root), later[0].digest, outcome.report_ref)) == 1
    assert closed(ctx.observer_root, "re-check", outcome.report_ref, outcome.report)


@pytest.mark.parametrize("spoil", ["wrong-root", "no-port", "refusing-port", "foreign-store"])
def test_t2g_root_selection_no_port_a_refused_append_and_a_foreign_store_begin_no_act_for_both_kinds_durably(observer, certified_work, spoil, monkeypatch):
    """The audit has no root-selection or store arm (one writer, no store), so under
    `wrong-root` and `foreign-store` its half reads the port-less writer; the
    assertion is the same for every arm — no read, no intent, no record."""
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    reads: list[str] = []
    calls: list[object] = []
    inner_read = ctx.seam.read_path
    ctx = replace(ctx, seam=replace(ctx.seam, read_path=lambda root, path: reads.append(path) or inner_read(root, path)))
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda *a, **k: calls.append(a) or ())
    portless = CorpusWriter(ctx.observer_root, durable_executor_factory(), authority=FULL, profile=BASE)
    audit_writer, audit_kwargs = portless, {}
    recheck_writer, recheck_kwargs, locations = writer, {}, (a,)
    if spoil == "wrong-root":
        other = certified_work / "other"
        init_corpus_root(other, authority=FULL)
        recheck_writer = open_corpus(other, authority=FULL, profile=BASE)
    elif spoil == "no-port":
        recheck_writer = portless
    elif spoil == "refusing-port":
        audit_writer, audit_kwargs = writer, {"port": RefusingPort(writer._operation_port)}
        recheck_kwargs = {"port": RefusingPort(writer._operation_port)}
    else:
        locations = (a, StoreLocator("f" * 32, "x.bin"))
    before = chain(ctx.observer_root)
    with pytest.raises((AuditRefused, ExecutionError)):
        run_audit(audit_writer, **audit_kwargs)
    with pytest.raises((RecheckRefused, ExecutionError)):
        recheck_locations(ctx, recheck_writer, locations, **recheck_kwargs)
    assert chain(ctx.observer_root) == before
    assert reads == [] and calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
    if spoil == "wrong-root":
        assert not any(node.kind == "act-report" for node in recheck_writer.read_view.iter_stored())


def test_t2h_each_kind_submits_exactly_one_fulfilling_execution_and_a_second_is_refused_durably(observer, certified_work):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    counting = CountingPort(writer._operation_port)
    outcome = run_audit(writer, port=counting)
    assert counting.submissions == 1
    a = held(ctx, store_id, "a.bin", b"alpha")
    recheck_counting = CountingPort(writer._operation_port)
    recheck_locations(ctx, writer, (a,), port=recheck_counting)
    assert recheck_counting.submissions == 1
    intent_digest = operation_intent(ctx.observer_root, "audit").digest
    with pytest.raises(ExecutionError, match="already fulfills"):
        writer._publish_operation_report(outcome.report, intent_digest, operations=(writer._create_op(proposition("p")),))
    assert len([e for e in registrations(ctx.observer_root) if e.fulfills == intent_digest]) == 1
    copy = certified_work / "copy"
    shutil.copytree(ctx.observer_root, copy, symlinks=True)
    forged = Chain(copy)
    forged.digests = [entry.digest for entry in chain(ctx.observer_root)]
    report_path = writer._relative_path(writer.read_view.get(outcome.report_ref))
    state = state_at(copy, report_path)
    registration = forged.registration("tx-raw", ((report_path, state),), ((report_path, state),), fulfills=intent_digest)
    forged.append(SettledEntry(txid="tx-raw", registration=registration, outcome=ChainOutcome.COMMITTED))
    view = science_root._log_seam().inspect_registered(copy)
    assert isinstance(view, MalformedView), view
    assert view.defect.kind == "duplicate-fulfillment"


def test_t2i_a_port_bound_to_another_root_is_refused_by_both_kinds_before_any_intent_durably(observer, certified_work):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    other = certified_work / "other"
    init_corpus_root(other, authority=FULL)
    foreign = science_root.durable_operation_port(other, writer.authority, profile=writer.profile)  # the writer's authority and profile; only the root differs
    before = (chain(ctx.observer_root), chain(other))
    with pytest.raises(PortMismatch):
        run_audit(writer, port=foreign)
    with pytest.raises(PortMismatch):
        recheck_locations(ctx, writer, (a,), port=foreign)
    assert (chain(ctx.observer_root), chain(other)) == before


@pytest.mark.parametrize("spoil", ["empty-instrument", "unencodable-observer", "standing-elsewhere", "standing-unrequested"])
def test_t2j_late_inputs_refuse_the_recheck_before_the_operation_intent_with_no_holdings_intent_and_no_read_durably(observer, spoil):
    from beliefs.holdings.records import Found, holdings_observation

    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    reads: list[str] = []
    inner_read = ctx.seam.read_path
    ctx = replace(ctx, seam=replace(ctx.seam, read_path=lambda root, path: reads.append(path) or inner_read(root, path)))
    kwargs: dict = {}
    if spoil == "empty-instrument":
        ctx = replace(ctx, instrument="")
    elif spoil == "unencodable-observer":
        ctx = replace(ctx, observer="\udcff")
    elif spoil == "standing-elsewhere":
        elsewhere = holdings_observation(
            location=StoreLocator(store_id, "b.bin"), outcome=Found("sha256:" + "0" * 64), observer="o", instrument="i",
            event_token="t", observed_at="2026-09-22T00:00:00Z",
        )
        kwargs["standing"] = {a.canonical(): (elsewhere,)}
    else:
        kwargs["standing"] = {StoreLocator(store_id, "b.bin").canonical(): ()}
    before = chain(ctx.observer_root)
    with pytest.raises(RecheckRefused):
        recheck_locations(ctx, writer, (a,), **kwargs)
    assert chain(ctx.observer_root) == before and reads == []


# --- T5, T6 ------------------------------------------------------------------------


def test_t5d_an_inconclusive_recheck_location_spells_untested_or_failed_by_whether_the_read_began_durably(observer):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a, b, c = held(ctx, store_id, "a.bin", b"alpha"), StoreLocator(store_id, "b.bin"), StoreLocator(store_id, "c.bin")
    inner = ctx.seam.read_path

    def reading(root, path):
        if path == b.relative_path:
            return ReadNotAttemptedView(reason="lease-refused", lifecycle_state=None, detail="x")
        if path == c.relative_path:
            return ReadUnestablishedView(reason="io-error", detail="y")
        return inner(root, path)

    ctx = replace(ctx, seam=replace(ctx.seam, read_path=reading))
    files_before = sorted((ctx.observer_root / "holdings-observation").iterdir())
    outcome = recheck_locations(ctx, writer, (a, b, c))
    assert outcome.entries[1] == LocatorEntry(b.canonical(), ByteLocatorUntested("lease-refused"))
    assert outcome.entries[2] == LocatorEntry(c.canonical(), RetrievalFailed("io-error"))
    assert outcome.entries[1].outcome != outcome.entries[2].outcome
    assert len(sorted((ctx.observer_root / "holdings-observation").iterdir())) == len(files_before) + 1  # a's re-check only
    assert closed(ctx.observer_root, "re-check", outcome.report_ref, outcome.report)


def test_t6d_cite_resolves_each_finding_in_evaluator_order_and_a_permutation_moves_the_identity_durably(observer, monkeypatch):
    writer = observer.writer
    first = stale_dataset(writer)
    real = audit_operation.audit_corpus
    second = Finding("warning", "zz-second", "proposition:" + "b" * 64, "d2", "m2")
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: real(view, evidence=evidence, profile=profile) + (second,))
    outcome = run_audit(writer)
    assert [f.ref for f in outcome.findings] == [first, second.ref]
    assert cite(outcome.report, 0).subject == first and cite(outcome.report, 1).subject == second.ref
    with pytest.raises(Exception):
        cite(outcome.report, 2)
    permuted = boundary_values._mint_audit_report(
        OperationIntent("audit", outcome.report.event_token, outcome.report.actor), observer=outcome.report.observer,
        instrument=outcome.report.instrument, opened_at=outcome.report.opened_at, closed_at=outcome.report.closed_at,
        entries=(outcome.entries[1], outcome.entries[0]),
    )
    assert permuted.identity() != outcome.report.identity()


def test_t6e_findings_differing_only_in_message_mint_equal_entries_and_one_identity_under_a_fixed_envelope_durably(observer, monkeypatch):
    writer = observer.writer
    stale_dataset(writer)
    real = audit_operation.audit_corpus
    base = run_audit(writer)
    (finding,) = base.findings
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: (replace(finding, message="reworded"),))
    reworded = run_audit(writer)
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: (replace(finding, detail="other-detail"),))
    detailed = run_audit(writer)
    assert reworded.entries == base.entries and detailed.entries != base.entries
    assert reworded.report.identity() != base.report.identity()  # T8: distinct tokens; not the comparison that matters
    envelope = dict(observer="o", instrument="i", opened_at="2026-09-22T00:00:00Z", closed_at="2026-09-22T00:00:00Z")
    intent = OperationIntent("audit", "f" * 32, writer.authority.actor)
    fixed = lambda entries: boundary_values._mint_audit_report(intent, entries=entries, **envelope).identity()  # noqa: E731
    assert fixed(base.entries) == fixed(reworded.entries)
    assert fixed(base.entries) != fixed(detailed.entries)


# --- BI ------------------------------------------------------------------------------


def test_bi1_the_evaluator_modules_define_no_write_entry_point_and_reach_no_primitive_durably():
    evaluators = {"audit.py", "world/audit.py"}
    assert not {key for key in WRITE_ENTRY_POINTS if key.split(":", 1)[0] in evaluators}
    for module in modules():
        name = relative(module)
        if name in evaluators:
            assert primitive_callers(parsed(module), name) == set(), name
    wrappers = {"audit_operation.py", "holdings/recheck.py"}
    seen = set()
    for module in modules():
        name = relative(module)
        if name in wrappers:
            seen.add(name)
            assert primitive_callers(parsed(module), name) == set(), name
    assert seen == wrappers


def test_bi2_the_evaluators_read_runs_under_the_root_lock_after_the_intent_so_a_raced_write_lands_after_the_report_durably(observer, monkeypatch):
    ctx, writer = observer.ctx, observer.writer
    started = threading.Event()
    real = audit_operation.audit_corpus
    racer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    added: list[str] = []

    def race() -> None:
        started.wait(5)
        added.append(racer.add(proposition("raced")).id)

    thread = threading.Thread(target=race)

    def evaluator(view, *, evidence, profile):
        thread.start()
        started.set()
        thread.join(0.5)  # blocked on the root lock the audit holds
        assert thread.is_alive() and added == []
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    outcome = run_audit(writer)
    thread.join(10)
    assert len(added) == 1
    committed = [e for e in chain(ctx.observer_root) if isinstance(e, RegisteredEntryView)]
    report_position = next(i for i, e in enumerate(committed) if e.fulfills == operation_intent(ctx.observer_root, "audit").digest)
    raced_position = next(i for i, e in enumerate(committed) if any(path == racer._relative_path(racer.read_view.get(added[0])) for path, _ in e.final))
    assert report_position < raced_position
    assert outcome.entries == ()  # the raced record was not in the judged state


def test_bi3_the_session_routes_write_one_act_line_per_committed_transaction_and_name_the_session_actor_durably(certified_work):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    audited = scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    ctx = scoped.holdings_context(instrument="inst")
    location = StoreLocator(scoped.store_id, "a.bin")
    write(ctx, location, b"alpha")
    rechecked = scoped.recheck((location,), instrument="inst")
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 4  # the audit's close, the write, the re-check act, the re-check's close
    assert {pair[1] for act in acts for pair in act.record_ids} >= {audited.report_ref, rechecked.report_ref, rechecked.entries[0].outcome.ref}
    assert audited.report.observer == session.actor and rechecked.report.observer == session.actor


# --- plain tests: T3 and T4, already closed, exercised by the new kinds ----------------


def test_deleting_the_published_audit_report_moves_the_operation_closed_to_indeterminate(observer):
    ctx, writer = observer.ctx, observer.writer
    outcome = run_audit(writer)
    entry = operation_intent(ctx.observer_root, "audit")
    value = OperationIntent("audit", json.loads(entry.payload)["event_token"], writer.authority.actor)
    registrations_ = registrations_of(chain(ctx.observer_root), entry.digest, outcome.report_ref)
    assert completion(value, registrations_, {outcome.report_ref: outcome.report}) == CLOSED
    os.unlink(writer.root / writer._relative_path(writer.read_view.get(outcome.report_ref)))
    writer._reconstruct()
    assert completion(value, registrations_, {}) == INDETERMINATE


def test_the_two_reports_leave_the_projection_unchanged_and_an_unfinished_audit_blocks_nothing(observer, certified_work):
    """T4's rule for the new kinds: over a fixed set of observations, adding and
    removing the two reports moves neither reducer output nor the corpus's
    audit findings; an unmatched audit intent blocks nothing. The re-check's
    own observation is part of the fixed set — it is taken before the
    baseline, never compared across."""
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    rechecked = recheck_locations(ctx, writer, (a,))  # the observation set is now fixed
    world, binding = world_over(certified_work, ctx.observer_root)

    def snapshot():
        active, blocked, _ = reduce(world, writer.corpus_id, binding)
        findings = tuple((f.code, f.ref) for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile))
        return output_digest(active), output_digest(blocked), blocked == [], findings

    os.unlink(writer.root / writer._relative_path(writer.read_view.get(rechecked.report_ref)))
    writer._reconstruct()
    baseline = snapshot()  # observations fixed, no report present
    audited = run_audit(writer)
    with_audit_report = snapshot()
    os.unlink(writer.root / writer._relative_path(writer.read_view.get(audited.report_ref)))
    writer._reconstruct()
    reports_removed = snapshot()
    writer._append_operation_intent("audit", secrets.token_hex(16), ctx.actor)  # an unfinished audit
    with_unmatched_intent = snapshot()
    assert with_audit_report == baseline == reports_removed == with_unmatched_intent
    assert baseline[2]  # nothing blocked, before and after
```

Import facts, verified 2026-09-22: `output_digest` lives in `beliefs.holdings.receipt` (`test_url_retrieval_acceptance.py` line 66); `Chain`, `ChainOutcome`, `state_at` come from `tests/test_world_log_codecs.py` and `SettledEntry` from `atoms.chain.model` (lines 46 and 31 there) — the module above imports them the same way. The T4 plain test unlinks the re-check's report with `os.unlink` because no ordinary API deletes a report (`DeletionKindExcluded`, families design §3.0 — cut 35's T4-a does the same); the re-check's observation stays, as part of the fixed set.

- [ ] **Step 2: Run on the certified volume**

```bash
cd python && export SCIENCE_CUT4_ROOT=~/d/beliefs/.cut4-acceptance SCIENCE_CUT10_ROOT=~/d/beliefs/.lifecycle-wrappers-test
uv run --frozen pytest tests/acceptance/test_act_report_remainder_acceptance.py -q -p no:cacheprovider
```
Expected: 12 unit functions (two parametrized: T2-g ×4, T2-j ×4) and the two plain tests green. BI-2 is the one to watch: if the evaluator's `thread.join(0.5)` returns with the racer already done, the root lock was not held across the read — that is a wrapper defect (decision 4), not a test to loosen.

- [ ] **Step 3: Commit**

```bash
tasks check && git add python/tests/acceptance/test_act_report_remainder_acceptance.py tasks
git commit -m "test(cut38): acceptance module — twelve units over real roots; T2, T5, T6"
```

---

### Task 6: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut38.py`, `python/tests/acceptance/n2_arms_cut38.py` (the re-export shim, byte-for-byte cut 37's with `37` → `38`), `python/tests/acceptance/test_n2_cut38.py`, `python/tools/cut38_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit and body digest; Task 5's test names.
- Produces: `CUT38_ARMS` (14), `DECLARATION_UNITS` (12), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS`, `PHASE_MODULES`, `TOOLS`, `ACCEPTANCE`, `PYTHON_ROOT`, `declared_accounting`.

- [ ] **Step 1: The declaration** — `python/tests/n2_arms_cut38.py` on cut 37's shape (`sed -n 1,60p tests/n2_arms_cut37.py`). `DECLARATION_UNITS = ("T2-e", "T2-f", "T2-g", "T2-h", "T2-i", "T2-j", "T5-d", "T6-d", "T6-e", "BI-1", "BI-2", "BI-3")`; `_MODULE = "acceptance/test_act_report_remainder_acceptance.py"`; `UNIT_CHECKS` maps each unit to its Task 5 test node (the function name; parametrized units cite the function, not a case id); `unit_of` strips a trailing `1`–`3` from `T2-g1`, `T2-g2`, `T2-g3`. Every `before` is copied **from the tree** after Task 4 (`grep -n` the site, copy the exact lines) and checked with `source.count(before) == 1`. The fourteen arms:

| arm | module | before (the site) | after |
|---|---|---|---|
| T2-e | `audit_operation.py` | `        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n        # 4. Act: the read after the intent, so the chain position names the state judged.\n        writer._reconstruct()\n        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)` | the same four lines with the `_reconstruct` and `findings =` lines moved above the `intent_digest =` line |
| T2-f | `holdings/recheck.py` | `    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n    # 3. Acts, in request order, nothing held across them.` | `    intent_digest = None  # appended after the first act\n    # 3. Acts, in request order, nothing held across them.` plus, inside the loop before `results.append(result)`: `        if intent_digest is None:\n            intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)` — spell `before`/`after` over the loop's first two lines so both edits are one arm |
| T2-g1 | `holdings/recheck.py` | `    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():\n        raise RecheckRefused("the writer's root is not the act context's observer root; a re-check publishes in one root")` | `    pass  # the one-root check dropped: the intent lands in the writer's root while the acts publish in the observer's` — under T2-g's `wrong-root` arm the operation intent goes to the other root and the re-check act then runs in the observer root (a holdings intent, a read, an observation), which is exactly the act-before-refusal the unit forbids |
| T2-g2 | `audit_operation.py` | `        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)` | `        try:\n            intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)\n        except Exception:\n            intent_digest = "0" * 64  # the append failure swallowed; the acts proceed` |
| T2-g3 | `holdings/recheck.py` | `    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))\n    for location in locations:\n        if location.store_id != store_id:\n            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")\n    # 2. Open.` | `    # 2. Open.` followed by the four removed lines placed **after** the `intent_digest =` line (the store-genesis check moved after the intent) |
| T2-h | `audit_operation.py` | `        writer._publish_operation_report(report, intent_digest, port=port)\n    return AuditOutcome(` | `        writer._publish_operation_report(report, intent_digest, port=port)\n        try:\n            writer._publish_operation_report(report, intent_digest, port=port)\n        except Exception:\n            pass  # a second close, its refusal swallowed\n    return AuditOutcome(` |
| T2-i | `corpus.py` | `        if Path(port.root).resolve() != Path(self.root).resolve():\n            raise PortMismatch(` | `        if False:\n            raise PortMismatch(` |
| T2-j | `holdings/recheck.py` | `    _require_identity_text(ctx.observer, "observer")\n    _require_identity_text(ctx.instrument, "instrument")` together with the `heads` validation loop | the observer/instrument lines and the `for key, predecessors in heads.items():` block moved after the `intent_digest =` line — spell one `before` from `    heads: dict[str, …` through `            raise RecheckRefused(f"{key}: standing holds only HoldingsObservation values at that canonical location")` and its `after` as the `heads = …` line alone, with the validation re-inserted after the append |
| T5-d | `holdings/recheck.py` | `            entries.append(LocatorEntry(canonical, outcome))\n            continue` | `            continue  # the inconclusive location dropped from the entries` |
| T6-d | `audit_operation.py` | `        entries = tuple(_entry(finding) for finding in findings)` | `        entries = tuple(_entry(finding) for finding in reversed(findings))` |
| T6-e | `audit_operation.py` | `    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail}).decode("utf-8")` | `    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail, "message": finding.message}).decode("utf-8")` |
| BI-1 | `audit.py` | `    findings = list(corpus_check(view, profile))\n    if any(f.code == "profile-mismatch" and f.detail in ("base", "malformed") for f in findings):` | `    findings = list(corpus_check(view, profile))\n    view.executor.execute(())  # a write primitive reached from the evaluator\n    if any(f.code == "profile-mismatch" and f.detail in ("base", "malformed") for f in findings):` (statically a primitive attribute call; BI-1's check is static and never runs it) |
| BI-2 | `audit_operation.py` | `    outer = nullcontext() if hold is None else hold()\n    with outer, writer._operation:\n        # 3. Open.` | `    outer = nullcontext() if hold is None else hold()\n    with outer, writer._operation:\n        pass  # the lock released before the evaluator call\n    if True:\n        # 3. Open.` |
| BI-3 | `session/writer.py` | `            port=self.operation_port(), hold=self._closing_hold,\n        )\n\n    def recheck(` | `            port=self._writer._operation_port, hold=self._closing_hold,\n        )\n\n    def recheck(` (the audit route bypassing the ledgered port) |

Where a `before` above is described rather than spelled (T2-f, T2-g3, T2-j), spell it at declaration time from the tree so that `source.count(before) == 1`, and make the `after` a syntactically valid replacement — run `python -c "import ast; ast.parse(open(p).read())"` over each sabotaged text through `n2_arms.py`'s own sabotage helper before pinning. Homing: `T2-g1`–`T2-g3` → `T2-g`; every other arm → its own unit. The guard's `homed` assertion is `{unit: {"T2-g": 3}.get(unit, 1) for unit in DECLARATION_UNITS}`.

- [ ] **Step 2: The guard** — `python/tests/acceptance/test_n2_cut38.py`: copy `test_n2_cut37.py`, then: import `CUT37_ARMS` and add it to `PRIOR_ARMS`; add `"python/tests/n2_arms_cut37.py": "2223f95"` to `FROZEN_PRIOR_CUT_FILES` (verify with `git log -1 --format=%h -- python/tests/n2_arms_cut37.py`); `FROZEN_CUT = … "2026-09-22-conformance-cut-38.md"`; `CUT38_FREEZE_COMMIT` and `CUT38_FROZEN_SHA256` from Task 0 Step 6; `FROZEN_DECLARATION = "python/tests/n2_arms_cut38.py"` and `CUT38_DECLARATION_SHA256 = sha256sum` of it once final; the inventory test asserts the twelve units and `len(CUT38_ARMS) == 14`; `test_every_acceptance_test_the_arms_name_exists` parses `test_act_report_remainder_acceptance.py` with `ast`, collects every `def test_*` name, and asserts that the set of function names `UNIT_CHECKS` cites (`check.rsplit("::", 1)[1]` per value) is a subset of it and has exactly `len(DECLARATION_UNITS)` members — never a prefix filter, since the plain `test_the_two_reports_…` also begins with `test_t`; the freeze test asserts `"**12 declaration units**" in current` and `'("cut37_acceptance.py",)' in current`.

- [ ] **Step 3: The runner** — `python/tools/cut38_acceptance.py`: cut 37's with `cut=38`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut38"`, `PREFIX_RUNNERS = ("cut37_acceptance.py",)`, `PHASE_MODULES = ("test_act_report_remainder_acceptance.py", "test_n2_cut38.py")`, `declared_accounting` asserting `rows == {"T2", "T5", "T6"}`, and on success:

```python
        print("guarantee rows exercised: 3 (1 newly closed: T2; T5 and T6 re-read for the new kinds; T7 partial under cross-root-publication)", flush=True)
```

- [ ] **Step 4: The recent-cut row** — `python/tests/test_recent_cut_acceptance.py`: `import cut38_acceptance as cut38`; add `(cut38, 38, (14, 12, 3))` and id `"cut38"` to the parametrization; add

```python
    if cut == 38:
        assert "guarantee rows exercised: 3 (1 newly closed: T2; T5 and T6 re-read for the new kinds; T7 partial under cross-root-publication)" in output
```

- [ ] **Step 5: Guard green, then the cut on the certified volume**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
cd python && SCIENCE_CUT4_ROOT=~/d/beliefs/.work/acceptance/cut38-dev uv run --frozen pytest tests/acceptance/test_n2_cut38.py -q -p no:cacheprovider -k "not fails_under_its_own_sabotage"
```
Expected: green. Then the full N2 audit and the chained runner, detached (memory `long-gates-need-setsid-nohup`; the chain cut 37 → 17 is long):

```bash
cd ~/d/beliefs/.worktrees/act-report-remainder/python
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 38); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut38-runner.log uv run --frozen python tools/cut38_acceptance.py > /dev/null 2>&1 &
sleep 2; echo "runner process group $(cat ~/d/beliefs/.work/acceptance/cut38-runner.log.pid)"
```
If the turn ends before the wrapper does, report that process-group id and `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut38-runner.log.pid)"` as the stop. Read the log when it exits; expected tail: three `[cut38 phase n/3]` lines, `declared arms: 14 (= 12 declaration units; 3 guarantee rows)`, the rows-exercised line, exit 0. Every arm `sound`; every check `resolved`. A `stale` verdict means a `before` no longer matches — fix the declaration (Step 1), never the source.

- [ ] **Step 6: Commit**

```bash
tasks check && git add python/tests/n2_arms_cut38.py python/tests/acceptance/n2_arms_cut38.py python/tests/acceptance/test_n2_cut38.py python/tools/cut38_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut38): N2 declarations, guard, runner and the recent-cut row — T2"
```

---

### Task 7: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §17)

- [ ] **Step 1: Run** — set the root by its canonical path (§16 records that the symlinked spelling refuses the preflight): `export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30` and confirm `test -f "$SCIENCE_MM30_ROOT/state.json"`. Read `rederived_belief` and `rederived_equal` from `state.json` before running and keep a copy of the file in the scratchpad directory. Then from `python/`: `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight` (it must say `ok`; on a host-load refusal, `tasks park beliefs-26d2da "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`), then `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`. `MM30_PREDECESSOR` may need the explicit canonical value §16 records. Nothing is recreated or moved aside: no contract succeeded; `grep -n 'audit_operation\|recheck_locations\|ScopedWriter.audit\|scoped.recheck' python/tools/reproduction/*.py` is empty — step 9 calls the bare `audit_corpus` by its own contract ("Writes nothing") and the driver re-checks no holdings.

- [ ] **Step 2: Append §17** on §16's shape — `## 17. Addendum — the act-report remainder, 2026-09-22`: read in place at the worktree's head; §17.1 what changed (the two operations, the bound port; none reached by the driver — quote the empty grep and the step-9 docstring); §17.2 what the re-run reached — the same `NoBelief` payload as §16.2 (quote both), `rederived_equal: true`, `state.json` byte-identical (`diff` against the copy, both SHA-256s); the two operations are exercised only by `python/tests/acceptance/test_act_report_remainder_acceptance.py`; §17.3 what this addendum does not claim (that mm30 audited through the wrapper or re-checked a holding; decision 12's reason).

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under the act-report remainder; nothing moves"
```

---

### Task 8: The results record, the re-rank, and the amendments

**Files:**
- Create: `docs/plans/2026-09-22-conformance-cut-38-results.md`
- Modify: `docs/designs/2026-09-22-conformance-cut-38.md` (`**Status:**` only), the spec (`**Status:**`), `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `python/tools/roadmap_status.py`, `docs/designs/2026-08-11-act-report-design.md`, `docs/guide/open-questions.md`, `docs/guide/contracts-and-adoption.md`, `README.md`, tasks

- [ ] **Step 1: The results record** on cut 37's shape (`docs/plans/2026-09-21-conformance-cut-37-results.md`): §1 what ran (both summary lines verbatim from the runner log; the per-unit table, 14 arms over 12 units); §2 accounting (T2 closed; the T table partial on T7 alone under `cross-root-publication`; **188 of 216**); §3 evidence — corrections carried by the cut document: the task record's and ledger row's "lands on `audit.py`, `world/audit.py`, `holdings/boundary.py`" corrected to "consumes" (spec decision 1), and the ledger row's "unblocks: the T table in full" corrected to "in full but for T7's cross-root case"; deviations from the plan; every "read at freeze" choice; the inventories checked in both directions (`WRITE_ENTRY_POINTS` and `CASES` unchanged; the wrappers call no primitive; the two evaluator modules define no entry point — BI-1); limitations found at review; §4 the reproduction (§17); §5 `## Remaining boundary` — must name T7's cross-root case (the ledger guard reads its labels) and L1 under `persistence-cut`; §6 main integration (filled at merge); §7 execution rulings (each refusal wording the acceptance asserted, the ledger-act counts BI-3 observed, anything the implementer decided).

- [ ] **Step 2: `roadmap_status.py`** — add `38: ("conformance-cut-38-results §2", "T2", ""),` after the cut-37 entry. Regenerate Appendix A: `cd python && uv run --frozen python tools/roadmap_status.py`; expected `Closed 188 of 216; open 28.`

- [ ] **Step 3: Ledger and roadmap** — the ledger's `Current state`: a new built bullet for the two operations and the bound port; `act-report-remainder` leaves the table; the T2 row's text gains "closed 2026-09-22 at cut 38 (`../plans/2026-09-22-conformance-cut-38-results.md`): the `audit` and `re-check` operations open through the boundary"; the summary names cut 38; 188 of 216. The roadmap, rewritten whole: `**Ranked at:** cut 38, against the ledger's Current state (2026-09-22)`; a `**Cut 38 (2026-09-22) discharges the act-report remainder and closes the boundary**` paragraph after cut 37's (the audit operation over the writer's own corpus under the root lock, one entry per finding; the re-check operation over independent store re-checks; every supplied port bound to its writer; T2 closes in full; the T table partial on T7 alone; the **seventh** off-path lane under rule 6; re-ranks nothing on the path — the first belief audits nothing it must report and re-checks no holding; `act-report-remainder` leaves the table and the index; off-path row 1 discharged and later rows renumber; **`publish` moves from tier 2 to tier 1 off the path**, since its `world-read` prerequisite is discharged and the criterion needs no publish, and becomes the `world-read` lane's head); the boundary index: `act-report-remainder` removed, `publish`'s tier becomes `1, off the path`; tier 1 off-path rows renumbered (`publish` 1 with its rows and placement — "W17's publication-binding intent-position arm; governed publication act and records", unblocks "immutable selected-view publication and governed binding revisions", placement "the user and autonomy layer design §§4.1 and 6; its publication-binding revision and act-report amendments land before `contract-cut` freezes"; `contract-cut` 2); the lane table's `world-read` row: boundaries "`publish`", status "off the path at its head; `act-report-remainder` discharged at cut 38"; tier 2 loses `publish`; the "current accounting" paragraph: 188 of 216, 28 open, and one more sentence in the reproduction list ("cut 38 read it in place again and re-derived the same answer with `state.json` byte-identical — the driver audits through the bare evaluator and re-checks no holding"); Appendix A pasted from the tool; Appendix B: the T2 row removed. Then:

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```
Expected: green — `test_the_roadmap_and_ledger_name_the_same_boundaries`, `test_the_ledger_summary_names_the_newest_remaining_boundary` and `test_the_newest_cut_document_says_it_is_discharged` now read cut 38.

- [ ] **Step 4: Guide, README, the design amendments** — `docs/guide/contracts-and-adoption.md`: the cut-38 line as discharged, "Thirty-four conformance cuts" (`ls docs/plans | grep -c "conformance-cut-.*-results"`), the totals, the results-record link; `docs/guide/open-questions.md`: the act-report paragraph's sentence "What remains unbuilt of the enum is not a question but work: the `audit` and `re-check` wrappers, `act-report-remainder`'s remainder on the roadmap." becomes "Cut 38 (2026-09-22) built the `audit` and `re-check` operations; every kind but `corpus-write`, reportless by design, now opens through a boundary and closes through a report. One question the slice files: a world-scope audit operation — one report per touched root under one token (§2.2's composite shape), or one report whose entries name their corpus — either an act-report design amendment (`../superpowers/specs/2026-09-22-act-report-remainder-design.md` §13)."; `README.md`: "through **cut 38**", the table row's wording ("the discharged act-report-remainder cut…; the boundary closes"), "The latest discharged boundary is cut 38" with both links. The act-report design, beneath §3.1's cut-35 amendment note:

```markdown
> **Amended 2026-09-22 (the act-report remainder, conformance cut 38 —
> `../superpowers/specs/2026-09-22-act-report-remainder-design.md`):** the
> `audit` and `re-check` operations are built on exactly these four steps.
> The audit (`audit_operation.py`, `audit`; the session route
> `ScopedWriter.audit`) fixes the observer root as the writer's own, checks
> port, authority and metadata before anything, appends one `audit` intent,
> runs `audit_corpus` over the writer's own view, and closes through one
> report carrying one subject-evaluation entry per finding in the
> evaluator's order — the whole operation under the caller's hold and the
> root lock, so the state judged is the state at the intent's chain
> position; a clean audit's report has no entries. The re-check
> (`holdings/recheck.py`, `recheck_locations`; `ScopedWriter.recheck`)
> validates every location, the store genesis, the observer, the instrument
> and every standing set before the intent, appends one `re-check` intent,
> runs the per-location `recheck` act as built with nothing held across the
> acts, and closes through one report carrying one locator entry per
> location — `published-observation`, or `byte-locator-untested` /
> `retrieval-failed` with the attempt's reason — with no cooperative stop,
> since the close mints nothing. A supplied operation port is bound to its
> writer's root, authority and profile or refused before any intent
> (`PortMismatch`). With it, every kind but `corpus-write` opens through a
> boundary and closes through a report; T2 closes.
```

- [ ] **Step 5: Status lines and tasks**

The cut document's Status: `discharged 2026-09-22 on the certified volume; results: ../plans/2026-09-22-conformance-cut-38-results.md`. The spec's Status: `discharged at conformance cut 38 on 2026-09-22; results: ../../plans/2026-09-22-conformance-cut-38-results.md`.

```bash
tasks done beliefs-d1bfbd "results record, re-rank at cut 38, amendments"
tasks add "A world-scope audit operation: one report per touched root, or entries naming their corpus" --status idea -b "Filed by cut 38 (act-report-remainder design §13): the audit operation is corpus-scoped because a subject-evaluation entry has no corpus member; a world audit at an epoch needs either §2.2's composite root-local shape or a corpus-qualified entry — an act-report design amendment either way." --tag conformance --tag act-report
tasks add "A reproduction driver step that audits through the audit operation" --status idea -b "Filed by cut 38 (decision 12): step 9 audits through the bare evaluator by its own contract; routing it through the wrapper mints a report into the measured corpus, a change to the artifact the reproduction lane does not make from a kernel lane." --tag reproduction --tag act-report
tasks check
```

- [ ] **Step 6: Commit**

```bash
git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut38): results record, re-rank at cut 38, T2 closed"
```

---

### Task 9: Final review, gate, merge

- [ ] **Step 1: Whole-branch review** — `superpowers:requesting-code-review` over `git diff main...HEAD`, against the spec's decisions (Global Constraints, the "Decisions the code must honour" bullet) and the cut document's §5 table. Land fixes as their own commits; record each in the results record §3.2 ("Final review, following cut 37's pattern").

- [ ] **Step 2: The gate**, detached:

```bash
cd ~/d/beliefs/.worktrees/act-report-remainder
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 38); do export SCIENCE_CUT${n}_ROOT=~/d/beliefs/.work/acceptance/cut$n; done
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut38-gate.log just gate > /dev/null 2>&1 &
sleep 2; echo "gate process group $(cat ~/d/beliefs/.work/acceptance/cut38-gate.log.pid)"
```
If the turn ends before the wrapper does, report that process-group id and `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut38-gate.log.pid)"` as the stop. Read the log at exit; expected the pytest summary line with zero failures (memory `pytest-count-claims-need-the-summary-line`) and the TypeScript suite green.

- [ ] **Step 3: Close and merge**

```bash
tasks done beliefs-b4a631 "final review, gate green, merged"
tasks done beliefs-86b150 "cut 38 discharged: T2 in full — the audit and re-check operations open through the boundary; every supplied port bound to its writer"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-86b150 — cut 38 discharged"
cd ~/d/beliefs && git merge --no-ff design/act-report-remainder -m "merge: act-report remainder — conformance cut 38"
```
Then fill the results record's §6 (main integration: the merge commit, `just check` on merged `main`) in a `docs(cut38): record merged-main verification` commit. Before removing the worktree, check that no host pointer resolves into it (`readlink -f ~/bin/* ~/.local/bin/* 2>/dev/null | grep act-report-remainder` empty), then `git worktree unlock .worktrees/act-report-remainder && git worktree remove .worktrees/act-report-remainder`.

---

## Self-review

**Spec coverage.** §2 decisions 1–3 → Task 2; 4 → Task 2 (the hold) and Task 5 BI-2; 5–6 → Task 3; 7 → Tasks 2–3 (checks first, no catch) and Task 5 T2-g; 8 → Task 4; 9 → Tasks 2–3 (the helpers); 10 → Tasks 1–3 (the errors); 11 → Global Constraints and each task's inventory step, BI-1; 12 → Task 7; 13 → Task 1 and T2-i; 14 → Task 3 and T2-j. §3 → Task 2; §4 → Task 3; §5 → Task 4; §6 → Tasks 1–3; §7 → asserted by the unchanged tests each task runs; §8 → the file map and Task 1's fake edits; §9.1 → Tasks 1–4; §9.2 → Task 5 (twelve units, two plain tests); §9.3–9.5 → Task 6; §10 → Task 8; §11 → Task 0 Step 5 and Task 8 Step 5; §12–13 → Task 8 Steps 1 and 5.

**Placeholders.** Every code step carries its body. The three arms whose `before` is described (T2-f, T2-g3, T2-j) are spelled at declaration from the tree by instruction, as cut 37's plan did for its moved lines; the count check makes a mis-spelling loud. The acceptance module's fixture facts to confirm are each named with the grep that settles them and the adjustment to make. The raw-write-then-govern shape `stale_dataset` relies on was probed on the certified volume on 2026-09-22 before this plan was written (`semantic-hash-stale` returned; a governed report published after it; the report closed).

**Type consistency.** `audit(writer, *, observer: str, instrument: str, evidence: DerivationEvidence, port: OperationPort | None = None, hold: Callable[[], AbstractContextManager[object]] | None = None) -> AuditOutcome`; `AuditOutcome(report: ActReport, report_ref: str, findings: tuple[Finding, ...], entries: tuple[SubjectEvaluationEntry, ...])`; `_finding_payload(finding: Finding) -> str`; `recheck_locations(ctx: ActContext, writer: CorpusWriter, locations: tuple[StoreLocator, ...], *, standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None, port=None, hold=None) -> RecheckOutcome`; `RecheckOutcome(report, report_ref, entries: tuple[LocatorEntry, ...], results: tuple[ActResult, ...])`; `CorpusWriter._require_bound_port(port: OperationPort | None) -> OperationPort`; `OperationPort.root -> Path`; `LedgeredPort.root -> Path`; `boundary._mint_audit_report(intent, *, observer, instrument, opened_at, closed_at, entries) -> ActReport`; `boundary._mint_recheck_report(...)` the same shape; `ScopedWriter.audit(*, instrument, evidence) -> AuditOutcome`; `ScopedWriter.recheck(locations, *, instrument, standing=None) -> RecheckOutcome`; `PortMismatch`, `AuditRefused`, `RecheckRefused` all `WriteRefused`.

## Plan review log

- 2026-09-22 — drafted.
- 2026-09-22 — first review, six findings, all taken: Tasks 1–3's unit tests
  are portable over `test_operation_writes.py`'s `RecordingPort` and a
  scripted store seam (spec §9.1), certified storage kept for Task 5;
  both recording ports log a call's completion after the inner port
  returns; T2-e compares intent digests over one captured chain read;
  T2-g1 drops the one-root check, so the wrong-root arm really runs an
  act before the refusal; the T4 plain test fixes the observation set
  before its baseline and compares reducer outputs and audit findings
  across report addition and removal; the guard selects `UNIT_CHECKS`'
  exact function names.
