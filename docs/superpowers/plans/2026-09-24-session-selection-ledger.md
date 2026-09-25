# Session Selection Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The session ledger records the current-project selection at `session-open` and at every change, as a project address pinned to the revision it resolved to, readable back by invocation id and as a per-act attribution.

**Architecture:** `session/ledger.py` gains the `select` line kind, an optional `project` key on `session-open`, reader currency tracking, `SelectLine`, `InvocationRecord.selection`, `LedgerReader.initial_project` and `LedgerReader.attributed_acts()`. `session/writer.py` gains `WriterSession.select_project` and `invocation_selection`, plus two helpers (`require_project_address`, `resolve_project`) that resolve an unpinned project address through the session's `CoordinationResolver`. `open_attended_session` takes an optional `project`, resolves it before any ledger effect, and hands the pinned result to `WriterSession`.

**Tech Stack:** Python 3.11+, pytest (xdist), `uv run --frozen`, `just`, the `tasks` CLI.

**Spec:** `docs/superpowers/specs/2026-09-24-session-selection-ledger-design.md` (approved 2026-09-24 after review, commit `da0eaee`). Read it beside this plan; section numbers below (§3, §4.2, …) are the spec's.

## Global Constraints

- A recorded selection is JSON `null` or the string `coord:<project>@<revision>`: a `CoordinationAddress` with `local` unset and `revision` set (spec decision 1). Nothing else is accepted, on either side.
- The writer always writes `project` on `session-open`; the reader also accepts the historical six-key `session-open` and reads its selection as `None` (decision 6). Every other line's key set stays exact.
- `select` is appended only for the current invocation, at most once per invocation, before that invocation's close (decisions 3, 5); the reader enforces the same currency (decision 7).
- The index learns a selection only after the ledger append returns; an append failure is terminal (`SessionLedgerFailed` from every later method, `invocation_selection` included) and leaves the index unchanged (§4.2).
- No conformance cut (decision 8, accepted in review). Ordinary tests only.
- These frozen cut-19 sabotage before-strings must stay textually intact and each still occur **exactly once** in its module (`tests/test_arm_staleness.py` must stay green). Do not write new code that repeats any of them:
  - `session/writer.py`: `"            if self._current != invocation:\n                raise SessionProtocolError(\n"` (in `_require_current` — the new currency check must be spelled `if invocation != self._current:` instead); `"            entry = self._index.get(invocation)\n            if entry is None:\n"` (in `claim_invocation` — new reads must not repeat it); `"            self._index[invocation].outcome = validated\n"`; the `invocation-close` append; `"        if not permit_covers(self._ceiling, required):\n"`; `"        writer = self._writer_factory(scoped_authority(required, self.actor))\n"`; `"            self._session._record_act(self._invocation, commit)\n"`; `"        with self._session._lock, _operation_lock_for(self._writer.root):\n"`; `"            if entry.command != command or entry.input_digest != digest:\n"`; `"            self._session._require_current(self._invocation)\n"`.
  - `session/ledger.py`: `"            os.fsync(self._file.fileno())\n"`; `"            self._failed = True\n"`; the `except OSError as caught:  # a directory in the file's place, …` line in `read_ledger_evidence`.
  - `session/__init__.py`: `"    if len(world_config.corpus_roots) != 1:\n"`; `"    if type(view) is not WellFormedView:\n"`; the two lines in `reconcile_sessions` (`chains[corpus_id] = log_seam().inspect_detached(root)`, `stack.enter_context(_operation_lock_for(root))`).
- `root.py` stays the one `atoms` importer: nothing here imports `atoms`. No new write primitive is added, so `WRITE_ENTRY_POINTS` does not change.
- A design document under `docs/designs/` cites a spec under `docs/superpowers/specs/` by a markdown link (`[…](../superpowers/specs/<file>.md)`), never by a backticked filename (`test_designs_corpus.py::test_every_cross_reference_resolves`).
- Tests: targeted runs are `cd python && uv run --frozen pytest -q -p no:cacheprovider <paths>`; the inner loop is `just test-fast` from the worktree root. This worktree lives on WORK_ROOT storage, which is not on the durability allowlist, so capability-dependent tests need the certified work root on the main checkout's volume (beliefs-ad68df). Export it once per shell, from the worktree root: `export SCIENCE_CUT13_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.lifecycle-wrappers-test"`. Every command below that needs it assumes it is exported. Never call `pytest` outside `uv run`/`just`.
- Task records change only through the `tasks` CLI. Each task: `tasks start <child-id>` before its first edit, `tasks done <child-id> "<what landed>"` in the same commit as its code.

## Review Focus

- **Re-selecting the project already selected** in a later invocation: a person runs `project-select health` twice; both invocations get their own `select` line and the second is not refused. Test added to Task 2.
- **An invocation that acts and then selects** (the kernel allows both in one invocation, decision 5): acts before the `select` line are attributed to the earlier selection, acts after it to the new one. Tests added to Task 1 (reader) and Task 2 (writer → reader).
- **A project-root address whose tip is not a `project` record** (a raw-written `question` at `coord:<p>` with no `local`): selecting it must refuse `ProjectNotResolvable`, not pin a question. Test added to Task 2.
- **A crash mid-append of a `select` line** (torn tail): the reader reports the torn tail and the invocation shows no selection; the previous selection still stands. Test added to Task 1.
- **An address with uppercase hex or extra segments in a ledger line**: refused as malformed, never normalized. Test added to Task 1 (parametrized malformed cases).

---

### Task 1: Ledger: the select line, session-open's project, and the reader

**Files:**
- Modify: `python/src/beliefs/session/ledger.py`
- Test: `python/tests/test_session_ledger.py`

**Interfaces:**
- Consumes: `beliefs.coordination.CoordinationAddress` (`parse`, `local`, `revision`, `__str__`).
- Produces:
  - `LINE_KINDS == ("session-open", "invocation-open", "act", "invocation-close", "session-close", "select")`
  - `require_selection(value: object, what: str) -> CoordinationAddress | None` (raises `ValueError`)
  - `SelectLine(invocation: str, project: CoordinationAddress | None)` — sealed, final, frozen dataclass
  - `InvocationRecord(invocation, command, input_digest, acts, outcome, selection: SelectLine | None)` — `selection` is a new last positional field
  - `LedgerReader.initial_project: CoordinationAddress | None`
  - `LedgerReader.attributed_acts() -> tuple[tuple[ActLine, CoordinationAddress | None], ...]`

- [ ] **Step 1: Start the task**

Run from the worktree root: `tasks start beliefs-f5b838`.

- [ ] **Step 2: Write the failing tests**

In `python/tests/test_session_ledger.py`, change the import block and helpers at the top to:

```python
from beliefs.coordination import CoordinationAddress
from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.session.ledger import (
    LINE_KINDS,
    ActLine,
    LedgerEmpty,
    LedgerMissing,
    LedgerUnreadable,
    LedgerWriter,
    SelectLine,
    encode_line,
    ledger_path,
    open_ledger_reader,
    read_ledger_evidence,
    validated_outcome,
)
from beliefs.session.reconcile import reconcile

SESSION = "a" * 32
ACTOR = f"session:{SESSION}"
WORLD = "b" * 32
DIGEST = "c" * 64
ENTRY = "d" * 64
INTENT = "e" * 64
AT = "2026-09-05T12:00:00Z"
P, Q, L, R1, R2 = ("1" * 32, "2" * 32, "3" * 32, "4" * 32, "5" * 32)
P_AT_R1 = f"coord:{P}@{R1}"
Q_AT_R2 = f"coord:{Q}@{R2}"


def open_line(**project):
    """The session-open line; `open_line(project=...)` adds the post-amendment key."""
    return {"line": "session-open", "session": SESSION, "actor": ACTOR, "world": WORLD,
            "permit": {"kinds": ["proposition"], "act_families": ["corpus-write"], "ungoverned": False}, "at": AT, **project}


def invocation_open(name):
    return {"line": "invocation-open", "invocation": name, "command": "mint", "input_digest": DIGEST, "at": AT}


def invocation_close(name):
    return {"line": "invocation-close", "invocation": name, "outcome": {"done": []}}


def act(name, entry=ENTRY):
    return {"line": "act", "invocation": name, "corpus": WORLD, "entry": entry, "intent": INTENT, "records": []}


def select(name, project):
    return {"line": "select", "invocation": name, "project": project}


def ledger_bytes(*lines):
    return b"".join(encode_line(line) for line in lines)


def selection_of(reader, invocation):
    record = reader.invocation(invocation)
    assert record is not None
    return record.selection
```

(Keep the existing `lines()` and `fsyncs` definitions below these unchanged; `open_line()` with no argument is exactly the old six-key line.)

Change the first assertion test's `LINE_KINDS` check to:

```python
    assert set(LINE_KINDS) == {"session-open", "invocation-open", "act", "invocation-close", "session-close", "select"}
```

Append these tests at the end of the file:

```python
# --- selection lines (selection design §3, §4.3) -------------------------------------
def test_the_reader_reads_the_initial_project_each_selection_and_the_attribution(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    a1, a2, b1 = "1" * 64, "2" * 64, "3" * 64
    for line in (
        open_line(project=P_AT_R1),
        invocation_open("A"),
        act("A", a1),
        select("A", Q_AT_R2),  # one invocation may act, select, then act again (decision 5)
        act("A", a2),
        invocation_close("A"),
        invocation_open("B"),
        select("B", None),
        act("B", b1),
        invocation_close("B"),
        invocation_open("C"),
        invocation_close("C"),
    ):
        writer.append(line)
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.initial_project == CoordinationAddress(P, revision=R1)
    record_a, record_b, record_c = reader.invocations()
    assert record_a.selection == SelectLine("A", CoordinationAddress(Q, revision=R2))
    assert record_b.selection == SelectLine("B", None)
    assert record_c.selection is None
    assert [(act_line.entry, project) for act_line, project in reader.attributed_acts()] == [
        (a1, CoordinationAddress(P, revision=R1)),
        (a2, CoordinationAddress(Q, revision=R2)),
        (b1, None),
    ]


def test_a_historical_session_open_without_project_reads_as_no_selection(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(*lines()))  # open_line() is the pre-amendment six-key shape
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.initial_project is None
    assert [project for _, project in reader.attributed_acts()] == [None]
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is not LedgerUnreadable
    assert "session-ledger-malformed" not in {finding.code for finding in reconcile((evidence,), {})}


def test_a_torn_select_leaves_the_previous_selection_standing(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(
        ledger_bytes(open_line(project=P_AT_R1), invocation_open("A"))
        + encode_line(select("A", Q_AT_R2))[:25]
    )
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True
    assert reader.initial_project == CoordinationAddress(P, revision=R1)
    assert selection_of(reader, "A") is None


@pytest.mark.parametrize(
    "line",
    [
        pytest.param(select("A", f"coord:{P}"), id="unpinned"),
        pytest.param(select("A", f"coord:{P}/{L}@{R1}"), id="subordinate"),
        pytest.param(select("A", "project-health"), id="not-an-address"),
        pytest.param(select("A", f"coord:{P.upper()}@{R1}"), id="uppercase-hex"),
        pytest.param(select("A", f"coord:{P}@{R1}@{R2}"), id="extra-segment"),
        pytest.param(select("A", 5), id="not-a-string"),
        pytest.param({**select("A", P_AT_R1), "at": AT}, id="extra-key"),
        pytest.param({"line": "select", "invocation": "A"}, id="missing-project"),
        pytest.param({"line": "select", "invocation": "bad id!", "project": None}, id="bad-invocation-id"),
    ],
)
def test_a_malformed_select_line_is_refused_naming_its_number(tmp_path, line):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(open_line(project=None), invocation_open("A"), line))
    with pytest.raises(LedgerMalformed, match="line 3"):
        open_ledger_reader(tmp_path, SESSION)


@pytest.mark.parametrize("project", [f"coord:{P}", f"coord:{P}/{L}@{R1}", 7])
def test_a_malformed_session_open_project_is_refused(tmp_path, project):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(open_line(project=project)))
    with pytest.raises(LedgerMalformed, match="line 1"):
        open_ledger_reader(tmp_path, SESSION)


@pytest.mark.parametrize(
    "raw, message",
    [
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_open("B"), select("A", P_AT_R1)),
            "line 4", id="select-names-an-abandoned-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_open("B"), invocation_close("B"), select("A", P_AT_R1)),
            "line 5", id="select-while-no-invocation-is-current",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_close("A"), select("A", P_AT_R1)),
            "line 4", id="select-after-its-invocation-closed",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), select("A", P_AT_R1)),
            "line 2", id="select-names-an-unopened-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), select("A", P_AT_R1), select("A", None)),
            "line 4", id="a-second-select-in-one-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), act("A"), invocation_open("B"), select("A", P_AT_R1), act("B")),
            "line 5", id="an-invalid-select-cannot-reattribute-a-later-act",
        ),
    ],
)
def test_a_select_the_writer_could_not_have_written_is_refused(tmp_path, raw, message):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    with pytest.raises(LedgerMalformed, match=message):
        open_ledger_reader(tmp_path, SESSION)
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is LedgerUnreadable and message in evidence.error
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_ledger.py`
Expected: collection error `ImportError: cannot import name 'SelectLine' from 'beliefs.session.ledger'`.

- [ ] **Step 4: Implement the ledger changes**

In `python/src/beliefs/session/ledger.py`:

Add the import after `from beliefs.errors import LedgerMalformed, SessionLedgerFailed`:

```python
from beliefs.coordination import CoordinationAddress
```

In `__all__`, add `"SelectLine"` after `"LedgerWriter"` and `"require_selection"` after `"require_invocation_id"`.

Replace `LINE_KINDS`:

```python
LINE_KINDS = ("session-open", "invocation-open", "act", "invocation-close", "session-close", "select")
```

Add after `require_hex`:

```python
def require_selection(value: object, what: str) -> CoordinationAddress | None:
    """A recorded selection: `null`, or a project address pinned to the revision it
    resolved to (selection design decision 1)."""
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{what} must be null or a pinned project address")
    address = CoordinationAddress.parse(value)
    if address.local is not None or address.revision is None:
        raise ValueError(f"{what} must be a project address pinned to a revision: {value!r}")
    return address
```

Add `SelectLine` after `ActLine`, and give `InvocationRecord` its new last field:

```python
@sealed
@final
@dataclass(frozen=True)
class SelectLine:
    """One `select` line: the invocation that changed the selection, and the new
    value — pinned, or None for a clear (selection design §4.3)."""

    invocation: str
    project: CoordinationAddress | None


@sealed
@final
@dataclass(frozen=True)
class InvocationRecord:
    invocation: str
    command: str
    input_digest: str
    acts: tuple[ActLine, ...]
    outcome: Mapping[str, object] | None
    selection: SelectLine | None
```

In `_validated_line`, replace the `expected = {...}[kind]` block and the key-set check with:

```python
        expected = {
            "session-open": {"line", "session", "actor", "world", "permit", "at"},
            "invocation-open": {"line", "invocation", "command", "input_digest", "at"},
            "act": {"line", "invocation", "corpus", "entry", "intent", "records"},
            "invocation-close": {"line", "invocation", "outcome"},
            "session-close": {"line", "at"},
            "select": {"line", "invocation", "project"},
        }[kind]
        if kind == "session-open" and "project" in line:
            expected = expected | {"project"}  # a pre-amendment session-open omits it (selection design decision 6)
        if set(line) != expected:
            raise ValueError(f"{kind} carries exactly {sorted(expected)}")
```

In the `if kind == "session-open":` branch, after `_require_str(line["at"], "at")`, add:

```python
            if "project" in line:
                require_selection(line["project"], "session-open project")
```

Insert this branch immediately before the final `else:` (the `session-close` branch):

```python
        elif kind == "select":
            require_invocation_id(line["invocation"])
            require_selection(line["project"], "select project")
```

Replace `LedgerReader.__init__` with:

```python
    def __init__(self, session_id: str, lines: list[dict[str, object]], torn_tail: bool) -> None:
        self.session_id = session_id
        self.torn_tail = torn_tail
        head = lines[0]
        self.actor = str(head["actor"])
        self.world_id = str(head["world"])
        self.initial_project = require_selection(head.get("project"), "session-open project")
        self.closed = any(line["line"] == "session-close" for line in lines)
        self._records: dict[str, InvocationRecord] = {}
        self._order: list[str] = []
        acts: dict[str, list[ActLine]] = {}
        selections: dict[str, SelectLine] = {}
        attributed: list[tuple[ActLine, CoordinationAddress | None]] = []
        standing = self.initial_project
        for line in lines[1:]:
            kind = line["line"]
            if kind == "invocation-open":
                invocation = str(line["invocation"])
                self._order.append(invocation)
                self._records[invocation] = InvocationRecord(invocation, str(line["command"]), str(line["input_digest"]), (), None, None)
                acts[invocation] = []
            elif kind == "act":
                invocation = str(line["invocation"])
                act = ActLine(invocation, str(line["corpus"]), str(line["entry"]), str(line["intent"]), _pairs(line["records"], "act records"))
                acts[invocation].append(act)
                attributed.append((act, standing))
            elif kind == "select":
                invocation = str(line["invocation"])
                standing = require_selection(line["project"], "select project")
                selections[invocation] = SelectLine(invocation, standing)
            elif kind == "invocation-close":
                invocation = str(line["invocation"])
                current = self._records[invocation]
                self._records[invocation] = InvocationRecord(invocation, current.command, current.input_digest, (), validated_outcome(line["outcome"]), None)
        for invocation, record in list(self._records.items()):
            self._records[invocation] = InvocationRecord(
                invocation, record.command, record.input_digest, tuple(acts.get(invocation, ())), record.outcome, selections.get(invocation)
            )
        self._attributed = tuple(attributed)
```

Add this method to `LedgerReader`, after `acts()`:

```python
    def attributed_acts(self) -> tuple[tuple[ActLine, CoordinationAddress | None], ...]:
        """Every act in ledger order, with the selection standing at its line: the
        latest `select` before it, else session-open's value (selection design
        decision 4)."""
        return self._attributed
```

Update the `LedgerReader` docstring's list of refused lines to add "a `select` naming anything but the current invocation, or a second `select` in one invocation".

In `_parse`, after `session_closed_at: int | None = None`, add:

```python
    current: str | None = None  # the writer's currency, replayed (selection design decision 7)
    selected: set[str] = set()
```

In `_parse`'s `invocation-open` branch, after `opened.add(invocation)`, add `current = invocation`. In its `invocation-close` branch, after `closed.add(invocation)`, add:

```python
                if invocation == current:
                    current = None
```

Insert before the `elif kind == "session-close":` branch:

```python
            elif kind == "select":
                invocation = str(validated["invocation"])
                if invocation not in opened:
                    raise LedgerMalformed(f"line {number}: select names invocation {invocation!r}, never opened")
                if invocation != current:
                    raise LedgerMalformed(
                        f"line {number}: select names invocation {invocation!r}, not the current invocation ({current!r})"
                    )
                if invocation in selected:
                    raise LedgerMalformed(f"line {number}: invocation {invocation!r} already holds a select")
                selected.add(invocation)
```

Update `_parse`'s docstring to name the three new `select` refusals beside the existing list.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_ledger.py tests/test_session_reconcile.py tests/test_session_writer.py`
Expected: all pass (the reconcile and writer suites prove the reader change broke nothing that reads ledgers).

- [ ] **Step 6: Lint, type-check, and check the frozen arms**

Run: `cd python && uv run --frozen ruff check src/beliefs/session/ledger.py tests/test_session_ledger.py && uv run --frozen pyright && uv run --frozen pytest -q -p no:cacheprovider tests/test_arm_staleness.py`
Expected: `All checks passed!`, `0 errors`, all staleness tests pass.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-f5b838 "ledger: select line, session-open project, reader currency, SelectLine, attributed_acts"
tasks check
git add python/src/beliefs/session/ledger.py python/tests/test_session_ledger.py tasks/
git commit -m "feat(session): the select ledger line and the reader's selection trajectory"
```

---

### Task 2: WriterSession: select_project, invocation_selection, and the pinned initial selection

**Files:**
- Modify: `python/src/beliefs/session/writer.py`
- Test: `python/tests/test_session_writer.py`

**Interfaces:**
- Consumes (Task 1): `SelectLine`, `require_selection`, `LINE_KINDS` including `"select"`, `LedgerReader.initial_project`, `InvocationRecord.selection`, `LedgerReader.attributed_acts()`; `beliefs.corpus.CoordinationResolver.resolve(address) -> Node | CoordinationRefused | None`.
- Produces:
  - `require_project_address(address: object) -> CoordinationAddress` (raises `ValueError`)
  - `resolve_project(resolver: CoordinationResolver | None, address: CoordinationAddress) -> CoordinationAddress` (pinned; raises `CoordinationUnavailable` or `ProjectNotResolvable`)
  - `WriterSession(..., coordination_resolver: CoordinationResolver | None = None, project: CoordinationAddress | None = None)` — `project` must already be pinned
  - `WriterSession.select_project(invocation_id: str, address: CoordinationAddress | None) -> CoordinationAddress | None`
  - `WriterSession.invocation_selection(invocation_id: str) -> SelectLine | None`

- [ ] **Step 1: Start the task**

Run: `tasks start beliefs-1e7ab0`.

- [ ] **Step 2: Write the failing tests**

In `python/tests/test_session_writer.py`, add to the imports:

```python
import json
import os

from coordination_fixtures import coordination_profile, mounted_root, raw_add, raw_coordination_node

from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CoordinationResolver
from beliefs.errors import CoordinationUnavailable, ProjectNotResolvable
from beliefs.session.ledger import SelectLine
```

(`from beliefs.corpus import CorpusWriter` already exists — extend it to `from beliefs.corpus import CoordinationResolver, CorpusWriter`; add the two error names to the existing `from beliefs.errors import (...)` block instead of a second import.)

Replace `make_session` with a version that forwards the two new arguments:

```python
def make_session(
    tmp_path: Path,
    ceiling: WritePermit | None = None,
    *,
    store_root: Path | None = None,
    store_id: str | None = None,
    holdings_seam: Any = None,
    coordination_resolver: CoordinationResolver | None = None,
    project: CoordinationAddress | None = None,
) -> tuple[WriterSession, list[RecordingPort]]:
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    operations_root = tmp_path / "ops"
    path = ledger_path(operations_root, SESSION)
    path.parent.mkdir(parents=True)
    ports: list[RecordingPort] = []

    def writer_factory(authority: Authority) -> CorpusWriter:
        port = RecordingPort(authority, corpus_root)
        ports.append(port)
        return CorpusWriter(corpus_root, DefaultExecutor, authority=authority, operation_port=port, profile=BASE)

    ledger = LedgerWriter(path)
    session = WriterSession(
        session_id=SESSION, world_id=WORLD, corpus_root=corpus_root, corpus_id=CORPUS,
        operations_root=operations_root, ledger=ledger, writer_factory=writer_factory,
        ceiling=WritePermit.full() if ceiling is None else ceiling,
        profile=BASE, store_root=store_root, store_id=store_id, holdings_seam=holdings_seam,
        coordination_resolver=coordination_resolver, project=project,
    )
    return session, ports
```

Append at the end of the file:

```python
# --- selection (selection design §4.2) ------------------------------------------------
P, Q, D, L = ("1" * 32, "2" * 32, "3" * 32, "4" * 32)
R1, R2, R3, R4, R5 = ("5" * 32, "6" * 32, "7" * 32, "8" * 32, "9" * 32)


def projects_resolver(tmp_path: Path, base_contract) -> tuple[CoordinationResolver, Path]:
    """A resolver over one mounted root holding projects P@R1 and Q@R2."""
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path / "coordination", profile)
    raw_add(root, raw_coordination_node("project", P, R1), raw_coordination_node("project", Q, R2))
    return CoordinationResolver({root: profile}), root


def ledger_file(session: WriterSession) -> Path:
    return ledger_path(session.operations_root, SESSION)


def recorded_selection(session: WriterSession, invocation: str) -> SelectLine | None:
    record = open_ledger_reader(session.operations_root, SESSION).invocation(invocation)
    assert record is not None
    return record.selection


def test_select_project_ledgers_the_pinned_tip_and_the_index_learns_it(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    pinned = session.select_project("A", CoordinationAddress(P))
    assert pinned == CoordinationAddress(P, revision=R1)
    assert session.invocation_selection("A") == SelectLine("A", pinned)
    assert session.current_invocation == "A"  # selecting does not close the invocation
    session.close_invocation("A", {"done": []})
    session.claim_invocation("B", "project-select", DIGEST)
    assert session.select_project("B", None) is None
    assert session.invocation_selection("B") == SelectLine("B", None)
    session.close_invocation("B", {"done": []})
    session.claim_invocation("C", "mint", DIGEST)
    assert session.invocation_selection("C") is None
    assert session.invocation_selection("Z") is None
    assert recorded_selection(session, "A") == SelectLine("A", CoordinationAddress(P, revision=R1))
    assert recorded_selection(session, "B") == SelectLine("B", None)


def test_reselecting_the_standing_project_records_a_second_line(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    for invocation in ("A", "B"):
        session.claim_invocation(invocation, "project-select", DIGEST)
        assert session.select_project(invocation, CoordinationAddress(P)) == CoordinationAddress(P, revision=R1)
        session.close_invocation(invocation, {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert [record.selection for record in reader.invocations()] == [
        SelectLine("A", CoordinationAddress(P, revision=R1)),
        SelectLine("B", CoordinationAddress(P, revision=R1)),
    ]


def test_session_open_always_writes_the_project_key(tmp_path):
    session, _ = make_session(tmp_path, project=CoordinationAddress(P, revision=R1))
    head = json.loads(ledger_file(session).read_bytes().splitlines()[0])
    assert head["project"] == f"coord:{P}@{R1}"
    assert open_ledger_reader(session.operations_root, SESSION).initial_project == CoordinationAddress(P, revision=R1)
    (tmp_path / "unselected").mkdir()
    other, _ = make_session(tmp_path / "unselected")
    assert json.loads(ledger_file(other).read_bytes().splitlines()[0])["project"] is None


@pytest.mark.parametrize("project", [CoordinationAddress(P), CoordinationAddress(P, L, R1), f"coord:{P}@{R1}"])
def test_a_session_refuses_an_initial_project_that_is_not_pinned_to_a_project_revision(tmp_path, project):
    with pytest.raises(ValueError):
        make_session(tmp_path, project=project)  # pyright: ignore[reportArgumentType]


def test_select_project_refusals_append_nothing_and_leave_the_invocation_current(tmp_path, base_contract):
    resolver, root = projects_resolver(tmp_path, base_contract)
    raw_add(
        root,
        raw_coordination_node("project", D, R3),
        raw_coordination_node("project", D, R4),  # two standing tips: divergent
        raw_coordination_node("question", L, R5),  # a project-root address whose tip is not a project
    )
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    before = ledger_file(session).read_bytes()
    for address, refusal in (
        (CoordinationAddress("0" * 32), ProjectNotResolvable),
        (CoordinationAddress(D), ProjectNotResolvable),
        (CoordinationAddress(L), ProjectNotResolvable),
        (CoordinationAddress(P, L), ValueError),
        (CoordinationAddress(P, revision=R1), ValueError),
        (f"coord:{P}", ValueError),
    ):
        with pytest.raises(refusal) as caught:
            session.select_project("A", address)  # pyright: ignore[reportArgumentType]
        if address == CoordinationAddress(D):
            assert caught.value.tips == (R3, R4)  # pyright: ignore[reportAttributeAccessIssue]
        assert ledger_file(session).read_bytes() == before
        assert session.current_invocation == "A"
        assert session.invocation_selection("A") is None


def test_a_clear_needs_no_resolver_but_an_address_does(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "project-select", DIGEST)
    with pytest.raises(CoordinationUnavailable):
        session.select_project("A", CoordinationAddress(P))
    assert session.select_project("A", None) is None


def test_a_later_revision_leaves_the_recorded_line_pinned(tmp_path, base_contract):
    resolver, root = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.select_project("A", CoordinationAddress(P))
    session.close_invocation("A", {"done": []})
    raw_add(root, raw_coordination_node("project", P, R5, supersedes=(f"project:{P}.{R1}",)))
    session.claim_invocation("B", "project-select", DIGEST)
    assert session.select_project("B", CoordinationAddress(P)) == CoordinationAddress(P, revision=R5)
    assert recorded_selection(session, "A") == SelectLine("A", CoordinationAddress(P, revision=R1))


def test_select_project_is_held_to_the_current_invocation_and_one_line(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.select_project("A", CoordinationAddress(P))
    before = ledger_file(session).read_bytes()
    with pytest.raises(SessionProtocolError):
        session.select_project("A", CoordinationAddress(Q))  # a second select in one invocation
    session.claim_invocation("B", "project-select", DIGEST)  # A is now abandoned
    with pytest.raises(SessionProtocolError):
        session.select_project("A", CoordinationAddress(Q))
    session.close_invocation("B", {"done": []})
    with pytest.raises(SessionProtocolError):
        session.select_project("B", CoordinationAddress(Q))  # no invocation is current
    after = ledger_file(session).read_bytes()
    assert after.startswith(before) and b'"line":"select"' not in after[len(before):]


def test_selection_calls_on_a_closed_session_are_session_closed(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.close()
    for call in (lambda: session.select_project("A", CoordinationAddress(P)), lambda: session.invocation_selection("A")):
        with pytest.raises(SessionClosed):
            call()


@pytest.mark.parametrize("fault", ["write", "flush", "fsync"])
def test_a_failed_select_append_leaves_the_index_unchanged_and_ends_the_session(tmp_path, base_contract, monkeypatch, fault):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    handle = session._ledger._file

    def failing(*_args):
        raise OSError(f"{fault} failed")

    if fault == "write":
        real_write = handle.write
        monkeypatch.setattr(handle, "write", lambda data: real_write(data[:17]))  # a short write
    elif fault == "flush":
        monkeypatch.setattr(handle, "flush", failing)
    else:
        monkeypatch.setattr(os, "fsync", failing)
    with pytest.raises(SessionLedgerFailed):
        session.select_project("A", CoordinationAddress(P))
    monkeypatch.undo()
    assert session._index["A"].selection is None  # the index never learned the selection
    frozen = ledger_file(session).read_bytes()
    for call in (
        lambda: session.select_project("A", None),
        lambda: session.invocation_selection("A"),
        lambda: session.invocation_acts("A"),
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.close_invocation("A", {"done": []}),
        lambda: session.scoped(PROPOSITIONS, "A"),
        session.close,
    ):
        with pytest.raises(SessionLedgerFailed):
            call()
    assert ledger_file(session).read_bytes() == frozen  # nothing after the fault reaches the file


def test_every_act_is_attributed_to_the_selection_standing_when_it_ran(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver, project=CoordinationAddress(P, revision=R1))

    def mint(invocation: str, name: str) -> str:
        writer = session.scoped(PROPOSITIONS, invocation)
        return writer.add(proposition(name)).id

    session.claim_invocation("A", "mint", DIGEST)
    mint("A", "p1")
    session.select_project("A", CoordinationAddress(Q))  # act, then select, in one invocation
    mint("A", "p2")
    session.close_invocation("A", {"done": []})
    session.claim_invocation("B", "project-select", DIGEST)
    session.select_project("B", None)
    session.close_invocation("B", {"done": []})
    session.claim_invocation("C", "mint", DIGEST)
    mint("C", "p3")
    session.close_invocation("C", {"done": []})
    session.claim_invocation("F", "project-select", DIGEST)
    session.select_project("F", CoordinationAddress(P))
    session.claim_invocation("G", "mint", DIGEST)  # F is abandoned; its selection still stands (decision 4)
    mint("G", "p4")
    session.close_invocation("G", {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert [(act.record_ids[0][1], project) for act, project in reader.attributed_acts()] == [
        ("proposition:p1", CoordinationAddress(P, revision=R1)),
        ("proposition:p2", CoordinationAddress(Q, revision=R2)),
        ("proposition:p3", None),
        ("proposition:p4", CoordinationAddress(P, revision=R1)),
    ]
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_writer.py`
Expected: FAIL — `TypeError: WriterSession.__init__() got an unexpected keyword argument 'coordination_resolver'`.

- [ ] **Step 4: Implement the writer changes**

In `python/src/beliefs/session/writer.py`, change the imports:

```python
from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver, CorpusWriter, Finding, OperationCommit, _operation_lock_for
from beliefs.errors import (
    CoordinationUnavailable,
    PermitExceeded,
    PermitFact,
    ProjectNotResolvable,
    ScienceError,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
)
```

and add `SelectLine,` to the `from beliefs.session.ledger import (...)` list.

Give `_Invocation` its selection slot:

```python
@dataclass
class _Invocation:
    command: str
    input_digest: str
    acts: list[ActLine]
    outcome: Mapping[str, object] | None
    selection: SelectLine | None = None
```

Add the two helpers after the `_Invocation` dataclass and before `class WriterSession`:

```python
def require_project_address(address: object) -> CoordinationAddress:
    """An unpinned project address: the only thing a caller may ask to select
    (selection design §4). The kernel pins it; a caller never supplies a revision."""
    if type(address) is not CoordinationAddress or address.local is not None or address.revision is not None:
        raise ValueError(f"a selection names an unpinned project address, not {address!r}")
    return address


def resolve_project(resolver: CoordinationResolver | None, address: CoordinationAddress) -> CoordinationAddress:
    """`address` resolved through `resolver` to its one standing `project` tip, and
    pinned to that revision (selection design decision 2)."""
    if resolver is None:
        raise CoordinationUnavailable(f"{address}: no coordination resolver is mounted to resolve a project")
    resolved = resolver.resolve(address)
    if resolved is None:
        raise ProjectNotResolvable(f"{address}: the selected project does not resolve")
    if isinstance(resolved, CoordinationRefused):
        raise ProjectNotResolvable(f"{address}: the selected project is divergent", tips=resolved.tips)
    if resolved.kind != "project":
        raise ProjectNotResolvable(f"{address}: resolves to a {resolved.kind}, not a project")
    return address.pinned(resolved.uid)
```

In `WriterSession.__init__`, add two keyword parameters after `holdings_seam: StoreActSeam | None = None,`:

```python
        coordination_resolver: CoordinationResolver | None = None,
        project: CoordinationAddress | None = None,
```

After `self._holdings_seam = holdings_seam`, add:

```python
        if project is not None and (
            type(project) is not CoordinationAddress or project.local is not None or project.revision is None
        ):
            raise ValueError(f"an initial selection is a project address pinned to its revision, not {project!r}")
        self._coordination_resolver = coordination_resolver
```

In the `session-open` append dict, add after `"at": utc_now(),`:

```python
                "project": None if project is None else str(project),
```

Add these two methods after `invocation_acts`:

```python
    # --- selection (selection design §4.2) -----------------------------------------------
    def select_project(self, invocation_id: str, address: CoordinationAddress | None) -> CoordinationAddress | None:
        """Ledger the current invocation's one selection change and return it
        pinned, or None for a clear. The index learns it only after the append
        returns; a failed append is terminal and leaves the index unchanged."""
        invocation = require_invocation_id(invocation_id)
        if address is not None:
            require_project_address(address)
        with self._lock:
            self._require_live()
            if invocation != self._current:
                raise SessionProtocolError(f"{invocation} cannot select; the current invocation is {self._current}")
            entry = self._index[invocation]
            if entry.selection is not None:
                raise SessionProtocolError(f"{invocation} already recorded its selection")
            pinned = None if address is None else resolve_project(self._coordination_resolver, address)
            self._ledger.append({"line": "select", "invocation": invocation, "project": None if pinned is None else str(pinned)})
            entry.selection = SelectLine(invocation, pinned)
            return pinned

    def invocation_selection(self, invocation_id: str) -> SelectLine | None:
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
            found = self._index.get(invocation)
            return None if found is None else found.selection
```

(`found`, not `entry`: the frozen before-string `entry = self._index.get(invocation)\n            if entry is None:\n` must keep occurring once. The currency check is spelled `if invocation != self._current:` for the same reason — `_require_current`'s `if self._current != invocation:\n                raise SessionProtocolError(\n` is pinned.)

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_writer.py tests/test_session_ledger.py tests/test_profile_agreement.py`
Expected: all pass.

- [ ] **Step 6: Lint, type-check, and check the frozen arms**

Run: `cd python && uv run --frozen ruff check src/beliefs/session tests/test_session_writer.py && uv run --frozen pyright && uv run --frozen pytest -q -p no:cacheprovider tests/test_arm_staleness.py`
Expected: `All checks passed!`, `0 errors`, all staleness tests pass.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-1e7ab0 "WriterSession.select_project and invocation_selection; session-open writes the pinned initial project"
tasks check
git add python/src/beliefs/session/writer.py python/tests/test_session_writer.py tasks/
git commit -m "feat(session): select_project ledgers a pinned selection under the current invocation"
```

---

### Task 3: open_attended_session resolves the initial project

**Files:**
- Modify: `python/src/beliefs/session/__init__.py`
- Test: `python/tests/test_session_writer.py`

**Interfaces:**
- Consumes (Task 2): `require_project_address`, `resolve_project`, `WriterSession(..., coordination_resolver=..., project=...)`.
- Produces: `open_attended_session(world_config, operations_root, *, profile, coordination=None, store_root=None, snapshot_resolver=None, project: CoordinationAddress | None = None) -> WriterSession`.

- [ ] **Step 1: Start the task**

Run: `tasks start beliefs-530198`.

- [ ] **Step 2: Write the failing tests**

In `python/tests/test_session_writer.py`, extract the durable-seam stubs out of `_attended` into a helper and make `_attended` call it. Replace the body of `_attended` from `genesis = GenesisEntryView(...)` through the three `monkeypatch.setattr(session_module, ...)` lines with a call `_stub_durable_seams(monkeypatch)`, and add the helper above `_attended`:

```python
def _stub_durable_seams(monkeypatch) -> None:
    """Swap the session's durable seams for in-memory doubles (see the note above)."""
    from beliefs.world.logmodel import GenesisEntryView, WellFormedView

    genesis = GenesisEntryView(digest="g" * 64, payload=b"", baseline=())

    class _StubLogSeam:
        def inspect_detached(self, _root):
            return WellFormedView(genesis=genesis, entries=(genesis,), tip=genesis.digest, pending=())

    def _stub_port(port_root, authority, *, profile):
        port = RecordingPort(authority, port_root)
        port.profile = profile
        return port

    monkeypatch.setattr(session_module, "log_seam", lambda: _StubLogSeam())
    monkeypatch.setattr(session_module, "durable_executor_factory", lambda: DefaultExecutor)
    monkeypatch.setattr(session_module, "durable_operation_port", _stub_port)
```

(Remove the now-unused `GenesisEntryView, WellFormedView` import from `_attended`'s local imports.)

Append at the end of the file:

```python
# --- the initial selection at open (selection design §4.1) -----------------------------
def _coordinated_open(tmp_path, monkeypatch, base_contract, *, coordination=True, **kwargs):
    """Open a real `open_attended_session` over a coordination-pinned root holding
    projects P@R1, D@R3 and D@R4 (divergent), with the durable seams stubbed."""
    from beliefs.session import open_attended_session
    from beliefs.world import WorldConfig

    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path / "corpus", profile)
    raw_add(
        root,
        raw_coordination_node("project", P, R1),
        raw_coordination_node("project", D, R3),
        raw_coordination_node("project", D, R4),
    )
    _stub_durable_seams(monkeypatch)
    ops = tmp_path / "ops"
    config = WorldConfig(tmp_path / "world", WORLD, (root,))
    session = open_attended_session(config, ops, profile=profile, coordination=profile if coordination else None, **kwargs)
    return session, ops


def test_an_attended_session_records_its_resolved_initial_project(tmp_path, monkeypatch, base_contract):
    session, ops = _coordinated_open(tmp_path, monkeypatch, base_contract, project=CoordinationAddress(P))
    assert open_ledger_reader(ops, session.session_id).initial_project == CoordinationAddress(P, revision=R1)
    session.claim_invocation("A", "project-select", DIGEST)
    assert session.select_project("A", CoordinationAddress(P)) == CoordinationAddress(P, revision=R1)


def test_an_attended_session_without_a_project_opens_unselected(tmp_path, monkeypatch, base_contract):
    session, ops = _coordinated_open(tmp_path, monkeypatch, base_contract)
    assert open_ledger_reader(ops, session.session_id).initial_project is None


@pytest.mark.parametrize(
    "project, coordination, refusal",
    [
        pytest.param(CoordinationAddress(P), False, SessionRefused, id="no-coordination-profile"),
        pytest.param(CoordinationAddress("0" * 32), True, ProjectNotResolvable, id="unknown"),
        pytest.param(CoordinationAddress(D), True, ProjectNotResolvable, id="divergent"),
        pytest.param(CoordinationAddress(P, revision=R1), True, ValueError, id="pinned"),
        pytest.param(CoordinationAddress(P, L), True, ValueError, id="subordinate"),
    ],
)
def test_an_unresolvable_initial_project_refuses_before_any_ledger_effect(
    tmp_path, monkeypatch, base_contract, project, coordination, refusal
):
    with pytest.raises(refusal) as caught:
        _coordinated_open(tmp_path, monkeypatch, base_contract, coordination=coordination, project=project)
    if project == CoordinationAddress(D):
        assert caught.value.tips == (R3, R4)  # pyright: ignore[reportAttributeAccessIssue]
    assert not (tmp_path / "ops" / "sessions").exists()
```

Add `SessionRefused` to the `from beliefs.errors import (...)` block.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_writer.py -k "attended"`
Expected: the new tests FAIL with `TypeError: open_attended_session() got an unexpected keyword argument 'project'`; the two existing snapshot-resolver tests still pass after the `_stub_durable_seams` extraction.

- [ ] **Step 4: Implement the open path**

In `python/src/beliefs/session/__init__.py`:

Add `from beliefs.coordination import CoordinationAddress` to the imports, and extend the `from beliefs.session.writer import (...)` list with `require_project_address,` and `resolve_project,` (keep the list sorted as ruff's isort expects).

Add the parameter to `open_attended_session`'s signature after `snapshot_resolver: SnapshotResolver | None = None,`:

```python
    project: CoordinationAddress | None = None,
```

Extend the docstring with: "`project`, an unpinned project address, is the initial selection: it resolves through the coordination resolver before the session directory exists, and the pinned result is written into `session-open` (selection design §4.1)."

After the `if coordination is not None and not isinstance(coordination, ProfileSpec):` check and before `if len(world_config.corpus_roots) != 1:`, add:

```python
    if project is not None:
        require_project_address(project)
        if coordination is None:
            raise SessionRefused(f"{project}: an initial project needs a coordination profile to resolve it")
```

After `resolver = CoordinationResolver({root: coordination}) if coordination is not None else None` and before `session_id = secrets.token_hex(16)`, add:

```python
    pinned = None if project is None else resolve_project(resolver, project)
```

In the `WriterSession(...)` call, add after `holdings_seam=holdings_seam() if store_root is not None else None,`:

```python
        coordination_resolver=resolver,
        project=pinned,
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_session_writer.py tests/test_profile_agreement.py`
Expected: all pass.

- [ ] **Step 6: Lint, type-check, and check the frozen arms**

Run: `cd python && uv run --frozen ruff check src/beliefs/session tests/test_session_writer.py && uv run --frozen pyright && uv run --frozen pytest -q -p no:cacheprovider tests/test_arm_staleness.py`
Expected: `All checks passed!`, `0 errors`, all staleness tests pass.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-530198 "open_attended_session resolves and ledgers the initial project before any ledger effect"
tasks check
git add python/src/beliefs/session/__init__.py python/tests/test_session_writer.py tasks/
git commit -m "feat(session): open_attended_session takes the initial project selection"
```

---

### Task 4: Documentation amendments and the gate

**Files:**
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (append a dated section at the end)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (one bullet after "The session routes")

**Interfaces:**
- Consumes: everything Tasks 1–3 produce, by name, for the amendment text.
- Produces: nothing new in code.

- [ ] **Step 1: Start the task**

Run: `tasks start beliefs-f9ff55`.

- [ ] **Step 2: Append the writer-session amendment**

Append to the end of `docs/designs/2026-09-05-writer-session-design.md`:

```markdown
## Selection amendment — 2026-09-24

The ledger records the session's current-project selection
([selection design](../superpowers/specs/2026-09-24-session-selection-ledger-design.md),
`beliefs-1148ad`; science's coordination command set design §8 S2). §3.2's
table gains one key and one row:

| `line` | fields |
|---|---|
| `session-open` | as before, plus `project`: `null` or a project address pinned to the revision it resolved to (`coord:<project>@<revision>`) |
| `select` | `invocation`; `project`: `null` or a pinned project address |

`open_attended_session` takes `project`, an unpinned project address, and
resolves it through the coordination resolver before the session directory
exists; no tip, a divergent tip, or a tip that is not a `project` refuses
`ProjectNotResolvable`, and a project without `coordination` refuses
`SessionRefused`. `WriterSession.select_project(invocation_id, address)`
resolves the same way, appends `select` for the current invocation only and at
most once per invocation, and returns the pinned address; the index learns it
after the append returns, and a failed append is §3.2's terminal
`LedgerFailed` state. `invocation_selection(invocation_id)` reads the index and,
like `invocation_acts`, requires a live session.

A selection takes effect at its line, whether or not its invocation later
closes. The reader replays the writer's currency (§3.3): a `select` naming
anything but the invocation current at its line, or a second `select` in one
invocation, is `LedgerMalformed`. §3.5's reader gains
`LedgerReader.initial_project`, `InvocationRecord.selection` and
`attributed_acts()`, which pairs every act with the selection standing at its
line. A `session-open` written before this amendment, without `project`, reads
as no selection; it is the only historical shape accepted.
```

- [ ] **Step 3: Add the adoption ledger bullet**

In `docs/designs/2026-08-03-redesign-adoption-ledger.md`, insert after the bullet that begins `- **The session routes** —` (and ends `Built.`):

```markdown
- **Session selection** — the ledger records the current-project selection as
  a project address pinned to its resolved revision: on `session-open`, and on
  a `select` line per change under the current invocation, replayed by the
  reader with the writer's currency and read back per invocation and as a
  per-act attribution
  ([selection design](../superpowers/specs/2026-09-24-session-selection-ledger-design.md)).
  Built; no conformance cut.
```

- [ ] **Step 4: Run the design-corpus guard**

Run: `cd python && uv run --frozen pytest -q -p no:cacheprovider tests/test_designs_corpus.py`
Expected: all pass (the two links resolve; no backticked spec filename in `docs/designs/`).

- [ ] **Step 5: Run the gate**

Run from the worktree root:

```bash
just check
just test-fast
```

Expected: `just check` clean; `just test-fast` exits 0 with no failures. If any failure is `CapabilityUnavailable` from a repo-relative acceptance root (beliefs-ad68df), record it in a task note and rerun that module from the main checkout after the merge instead of treating it as a code failure; any other failure is a code failure and blocks the task.

- [ ] **Step 6: Commit and close the goal**

```bash
tasks done beliefs-f9ff55 "writer-session selection amendment and adoption ledger bullet; gate green"
tasks done beliefs-1148ad "Session ledger records the selection: session-open project, select line under the writer's currency, select_project/invocation_selection, open_attended_session(project=), reader initial_project/selection/attributed_acts"
tasks check
git add docs/designs/2026-09-05-writer-session-design.md docs/designs/2026-08-03-redesign-adoption-ledger.md tasks/
git commit -m "docs(session): record the selection amendment; close beliefs-1148ad"
```
