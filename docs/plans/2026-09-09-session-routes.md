# Session Routes, Store Identity and Reference Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the invocation-scoped writer the `run` and `holdings` routes under its own authority with every commit ledgered, expose the store identity reader publicly, and ship the two reference rules keyed by kernel-scoped rule identity.

**Architecture:** `beliefs.root.store_identity` is the public name of the private genesis read. The writer session optionally binds a store root; `ScopedWriter` gains `actor`, `store_id`, `operation_port()` and `holdings_context()`. A new module `beliefs/session/routes.py` wraps the durable operation port and the holdings store seam so each fulfilling commit is recorded as an `act` line with the records parsed from the plan, with the session lock always taken before the corpus lock. Reconciliation learns the run and holdings intent shapes. `beliefs/rules.py` holds `REFERENCE_RULES`; the reproduction driver maps its identities onto the kernel implementations.

**Tech Stack:** Python 3.13, `uv`, pytest (`just test-fast` for the parallel run, `just test` for the serial gate, `just check` for ruff + pyright + biome + tsc + `tasks check`), the `tasks` tracker.

**Spec:** `docs/designs/2026-09-09-session-routes-design.md`

## Global Constraints

- Every command runs from the worktree root `.worktrees/kernel-seams` (or `python/` where stated). Never `cd` to the main checkout.
- Run tests as `just test-fast` (whole suite, parallel) or, for one file, `(cd python && uv run --frozen pytest tests/<file> -q)`. Before every commit run `just check`; the pre-commit hook runs it again and refuses on failure.
- Conventional commits, no attribution trailers, no `/home/<user>` or absolute Dropbox paths in code or docs.
- `Authority(...)` is constructed in `beliefs/permit.py` and in tests only (write permits §16); no task constructs one in `src`.
- Rule identities are permanent: `beliefs/outcome-file/v1` and `beliefs/content-identity-equality/v1` exactly (design §5.1).
- Lock order is session lock, then corpus operation lock, everywhere (design §4.2).
- Tracker: `tasks start <id>` before a task's first step, `tasks note <id> "<what landed>"` and `tasks done <id>` at its last, `tasks check` before every commit. Never edit `tasks/*.md` directly.
- Task ids: Task 1 → `beliefs-2d9a55`; Tasks 2–8 and 11 → children of `beliefs-5fe2e3` (Task 2 `beliefs-8dca16`, Task 3 `beliefs-89e551`, Task 4 `beliefs-b9edfe`, Task 5 `beliefs-c90220`, Task 6 `beliefs-440c98`, Task 7 `beliefs-7fd23b`, Task 8 `beliefs-469af0`, Task 11 `beliefs-6a9931`); Tasks 9–10 → children of `beliefs-e5ab34` (Task 9 `beliefs-77caa9`, Task 10 `beliefs-dff3e9`). Each step below names its id.

## Task order

Task 1 first (science's read context depends on it alone). Tasks 2–8 in order. Tasks 9–10 are independent of 2–8 and may run any time after Task 1. Task 11 last.

---

### Task 1: The public store identity reader

**Files:**
- Modify: `python/src/beliefs/root.py:392-407` (rename `_read_existing_store_genesis` → `store_identity`), `:426`, `:661` (callers), `__all__` near `:230`
- Test: `python/tests/test_store_root.py`

**Interfaces:**
- Produces: `beliefs.root.store_identity(store_root: Path) -> str | None`; raises `CorpusRootRefused` for a genesis that is not a store genesis.

- [x] **Step 1: `tasks start beliefs-2d9a55`**

- [x] **Step 2: Write the failing tests**

Append to `python/tests/test_store_root.py` (imports `init_corpus_root` and `store_identity` are added at the top of the file, beside the existing `from beliefs.root import LifecycleState, init_store_root`):

```python
from beliefs.root import LifecycleState, init_corpus_root, init_store_root, store_identity


class TestStoreIdentity:
    def test_a_fresh_store_round_trips_its_id(self, certified_work):
        root = certified_work / "store"
        minted = init_store_root(root, authority=FULL)
        assert store_identity(root) == minted

    def test_an_empty_directory_and_a_missing_root_read_none(self, tmp_path):
        (tmp_path / "empty").mkdir()
        assert store_identity(tmp_path / "empty") is None
        assert store_identity(tmp_path / "absent") is None

    def test_a_corpus_root_is_refused_not_none(self, certified_work):
        root = certified_work / "corpus"
        init_corpus_root(root, authority=FULL)
        with pytest.raises(CorpusRootRefused, match="store genesis payload is malformed"):
            store_identity(root)

    def test_a_malformed_store_genesis_is_refused(self, tmp_path):
        root = tmp_path / "store"
        _fabricate_genesis(root, b'{"domain":"science.store-root.v1"}')
        with pytest.raises(CorpusRootRefused):
            store_identity(root)

    def test_the_private_name_is_gone(self):
        assert not hasattr(science_root, "_read_existing_store_genesis")
```

- [x] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_store_root.py -q -k TestStoreIdentity)`
Expected: FAIL — `ImportError: cannot import name 'store_identity'`.

- [x] **Step 4: Rename and document the reader**

In `python/src/beliefs/root.py` replace the function at `:392` with:

```python
def store_identity(store_root: Path) -> str | None:
    """The id a durable store genesis claims for this tree, or None when no
    chain, no well-formed chain, or no genesis entry is there to claim one.

    Detached inspection, deliberately: an arriving or interrupted store has
    no serviceable carrier to read coherently, so this read takes no lock,
    runs no recovery and writes nothing. A genesis that is not a store
    genesis — a corpus root's, or a malformed payload — raises
    `CorpusRootRefused`: that root is misnamed, not merely empty.
    """
    inspected = inspect_chain_detached(_PRODUCTION_BACKEND, str(store_root))
    if type(inspected) is not WellFormedChain or not inspected.entries:
        return None
    _digest, genesis = inspected.entries[0]
    if type(genesis) is not GenesisEntry:
        return None
    store_id, _forked_from = _decode_store_genesis(genesis.payload)
    return store_id
```

Replace the two callers (`existing = _read_existing_store_genesis(store_root)` at `:426`, `resumed = _read_existing_store_genesis(dest)` at `:661`) with `store_identity(...)`. Add `"store_identity",` to `__all__` in alphabetical position (after `"restore_root"`). Update the module docstring of `python/tests/test_store_root.py` line 6–7 to name `store_identity` instead of `_read_existing_store_genesis`.

- [x] **Step 5: Run the file and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_store_root.py -q)` then `just check`
Expected: all pass; ruff and pyright clean.

- [x] **Step 6: Commit and close**

```bash
git add python/src/beliefs/root.py python/tests/test_store_root.py
tasks note beliefs-2d9a55 "store_identity is the public detached genesis read; a corpus root refuses, an empty root reads None"
tasks done beliefs-2d9a55
git add tasks
git commit -m "feat(root): expose the store identity reader"
```

---

### Task 2: The holdings seam's publish returns the entry digest

**Files:**
- Modify: `python/src/beliefs/holdings/seam.py:63`, `python/src/beliefs/root.py:1274-1285` (`_store_publish_fulfilling`)
- Modify: `python/tests/test_profile_agreement.py:227-229` (the fake `publish` returns a digest)
- Test: `python/tests/test_holdings_seam.py`

**Interfaces:**
- Produces: `StoreActSeam.publish_fulfilling: Callable[[Path, WritePlan, str], str]` returning the digest of the registration that fulfilled the intent.

- [x] **Step 1: `tasks start beliefs-8dca16`**

- [x] **Step 2: Write the failing test**

Append to `python/tests/test_holdings_seam.py`:

```python
def test_publish_fulfilling_returns_the_registration_digest(certified_work):
    from nodes.core.write_plan import CreateOp

    from beliefs.holdings.boundary import intent_payload
    from beliefs.holdings.records import StoreLocator
    from beliefs.root import init_corpus_root

    observer = certified_work / "observer"
    init_corpus_root(observer, authority=FULL)
    seam = holdings_seam()
    payload = intent_payload(
        location=StoreLocator("1" * 32, "p.bin"), act_kind="write", event_token="tok", actor="observer"
    )
    with seam.corpus_lock(observer):
        intent = seam.append_intent(observer, payload)
        entry = seam.publish_fulfilling(observer, (CreateOp("notes/p.md", b"---\nid: x\n---\n"),), intent)

    view = science_root.log_seam().inspect_detached(observer)
    registered = {digest: e for digest, e in _entries(view) if getattr(e, "fulfills", None) == intent}
    assert list(registered) == [entry]


def _entries(view):
    return [(entry.digest, entry) for entry in view.entries]
```

(`WellFormedView.entries` carries `RegisteredEntryView(digest, txid, initial, final, fulfills)` rows, so `getattr(e, "fulfills", None)` selects exactly the registration.)

- [x] **Step 3: Run it to see it fail**

Run: `(cd python && uv run --frozen pytest tests/test_holdings_seam.py -q -k publish_fulfilling_returns)`
Expected: FAIL — `assert [...] == [None]`.

- [x] **Step 4: Return the digest**

`python/src/beliefs/holdings/seam.py:63`:

```python
    publish_fulfilling: Callable[[Path, WritePlan, str], str]
```

`python/src/beliefs/root.py:1274`:

```python
def _store_publish_fulfilling(root: Path, plan: SeamWritePlan, fulfills: str) -> str:
    """Publish the observation plan fulfilling `fulfills` and answer with the
    registration's digest, read back from the chain the way the operation
    port reads its own (design §4.4)."""
    _refuse_over_ceiling(cast(WritePlan, plan))
    metadata_root = metadata_root_for(root)
    DurableExecutor(
        root,
        backend=_PRODUCTION_BACKEND,
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root,
        consumer_tag=CONSUMER_TAG,
        intent_domain=INTENT_DOMAIN,
        fulfills=fulfills,
    ).execute(cast(WritePlan, plan))
    return _registration_for(root, _PRODUCTION_BACKEND, PRODUCTION_STORAGE, metadata_root, fulfills)
```

In `python/tests/test_profile_agreement.py:227` make the fake return a digest:

```python
    def publish(_root, plan, intent):
        assert held
        published.append((plan, intent))
        return "cd" * 32
```

- [x] **Step 5: Run the holdings files and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_holdings_seam.py tests/test_holdings_boundary.py tests/test_profile_agreement.py -q)` then `just check`
Expected: pass.

- [x] **Step 6: Commit and close**

```bash
git add python/src/beliefs/holdings/seam.py python/src/beliefs/root.py python/tests/test_holdings_seam.py python/tests/test_profile_agreement.py
tasks note beliefs-8dca16 "publish_fulfilling returns the registration digest"
tasks done beliefs-8dca16
git add tasks
git commit -m "feat(holdings): return the registration digest from the seam's publish"
```

---

### Task 3: The session binds a store and the facade holds its authority

**Files:**
- Modify: `python/src/beliefs/session/writer.py:100-135` (`WriterSession.__init__`), `:150-167` (`scoped`), `:275-290` (`ScopedWriter`)
- Modify: `python/src/beliefs/session/__init__.py:73-131` (`open_attended_session`)
- Test: `python/tests/test_session_writer.py`, `python/tests/acceptance/test_session_acceptance.py`

**Interfaces:**
- Produces: `WriterSession(…, profile: ProfileSpec | None = None, store_root: Path | None = None, store_id: str | None = None, holdings_seam: StoreActSeam | None = None)`; `WriterSession.scoped` passes the authority to `ScopedWriter(session, writer, invocation_id, authority)`; `ScopedWriter.actor -> str`; `ScopedWriter.store_id -> str` (raises `SessionProtocolError` without a store); `open_attended_session(…, store_root: Path | None = None)` refusing `SessionRefused` when `store_identity` is `None`.

- [x] **Step 1: `tasks start beliefs-89e551`**

- [x] **Step 2: Write the failing portable tests**

Append to `python/tests/test_session_writer.py`:

```python
# --- the session's store and the facade's authority (session-routes design §3) ---
def test_the_facade_exposes_the_session_actor(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    assert writer.actor == session.actor == f"session:{SESSION}"


def test_store_id_without_a_store_is_a_protocol_error(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    with pytest.raises(SessionProtocolError, match="no store"):
        writer.store_id


def test_a_session_built_with_a_store_exposes_its_id(tmp_path):
    session, _ = make_session(tmp_path, store_root=tmp_path / "store", store_id="e" * 32)
    session.claim_invocation("A", "mint", DIGEST)
    assert session.scoped(PROPOSITIONS, "A").store_id == "e" * 32
```

Extend `make_session` to accept and forward the store:

```python
def make_session(
    tmp_path: Path,
    ceiling: WritePermit | None = None,
    *,
    store_root: Path | None = None,
    store_id: str | None = None,
    holdings_seam: Any = None,
) -> tuple[WriterSession, list[RecordingPort]]:
    ...
    session = WriterSession(
        session_id=SESSION, world_id=WORLD, corpus_root=corpus_root, corpus_id=CORPUS,
        operations_root=operations_root, ledger=ledger, writer_factory=writer_factory,
        ceiling=WritePermit.full() if ceiling is None else ceiling,
        profile=BASE, store_root=store_root, store_id=store_id, holdings_seam=holdings_seam,
    )
    return session, ports
```

Append to `python/tests/acceptance/test_session_acceptance.py` (add `init_store_root` and `store_identity` to the existing `from beliefs.root import (...)` block, and `SessionRefused` to the errors block if absent):

```python
# --- the session's store (session-routes design §3.1) --------------------------
def test_a_session_opened_with_a_store_exposes_its_identity(work_directory):
    root = adopted(work_directory, "store-session")
    store = _track(work_directory / f"store-{secrets.token_hex(4)}")
    minted = init_store_root(store, authority=FULL)
    session, _ops = attended(work_directory, root, store_root=store)
    try:
        session.claim_invocation("A", "mint", "d" * 64)
        writer = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "A")
        assert writer.store_id == minted == store_identity(store)
    finally:
        session.close()


def test_a_store_root_without_a_genesis_refuses_before_any_ledger(work_directory):
    root = adopted(work_directory, "no-store")
    store = _track(work_directory / f"store-{secrets.token_hex(4)}")
    store.mkdir()
    ops = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    with pytest.raises(SessionRefused, match="store root"):
        session_module.open_attended_session(config_for(work_directory, root), ops, profile=WITH_BIOLOGY, store_root=store)
    assert not (ops / "sessions").exists()
```

- [x] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_session_writer.py tests/acceptance/test_session_acceptance.py -q -k "facade_exposes or store_id or with_a_store or without_a_genesis")`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'store_root'` and `AttributeError: 'ScopedWriter' object has no attribute 'actor'`.

- [x] **Step 4: Carry the store on the session and the authority on the facade**

`python/src/beliefs/session/writer.py`. Imports: add `from beliefs.holdings.seam import StoreActSeam` and `from beliefs.profile import ProfileSpec`. In `WriterSession.__init__` add after `ceiling`:

```python
        profile: ProfileSpec | None = None,
        store_root: Path | None = None,
        store_id: str | None = None,
        holdings_seam: StoreActSeam | None = None,
```

and after `self._ceiling = ...`:

```python
        if (store_root is None) != (store_id is None):
            raise TypeError("a session binds a store root and its id together, or neither")
        self.profile = profile
        self.store_root = None if store_root is None else Path(store_root)
        self.store_id = store_id
        self._holdings_seam = holdings_seam
```

`scoped` (`:166-167`) becomes:

```python
        authority = scoped_authority(required, self.actor)
        return ScopedWriter(self, self._writer_factory(authority), invocation, authority)
```

`ScopedWriter`:

```python
class ScopedWriter:
    """The facade a handler holds (design §5): seven corpus-write methods, the
    two routes of the session-routes design §3.3, one invocation."""

    __slots__ = ("_authority", "_invocation", "_session", "_writer")

    def __init__(self, session: WriterSession, writer: CorpusWriter, invocation_id: str, authority: Authority) -> None:
        self._session = session
        self._writer = writer
        self._invocation = invocation_id
        self._authority = authority

    @property
    def invocation_id(self) -> str:
        return self._invocation

    @property
    def actor(self) -> str:
        """The session actor — also the scoped authority's, so the observer a
        command passes and the actor a boundary stamps agree."""
        return self._session.actor

    @property
    def store_id(self) -> str:
        store_id = self._session.store_id
        if store_id is None:
            raise SessionProtocolError("this session was opened with no store root; the holdings route has no store")
        return store_id
```

`python/src/beliefs/session/__init__.py`. Import `holdings_seam, store_identity` from `beliefs.root` beside `durable_executor_factory, durable_operation_port, log_seam`. Signature and body of `open_attended_session`:

```python
def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    profile: ProfileSpec,
    coordination: ProfileSpec | None = None,
    store_root: Path | None = None,
) -> WriterSession:
```

After the existing detached-view check (the `WellFormedView` refusal) and before `resolver = ...`, add:

```python
    store_id: str | None = None
    if store_root is not None:
        if not isinstance(store_root, Path):
            raise TypeError("store_root must be a Path")
        store_id = store_identity(store_root)
        if store_id is None:
            raise SessionRefused(f"store root {store_root} carries no store genesis")
```

and pass to the constructor:

```python
        profile=profile,
        store_root=store_root,
        store_id=store_id,
        holdings_seam=holdings_seam() if store_root is not None else None,
```

- [x] **Step 5: Extend the facade-surface test**

`python/tests/test_session_writer.py:278-280` asserts the facade's public names exactly. Add the two properties:

```python
def test_the_scoped_writer_exposes_the_seven_methods_the_routes_and_its_invocation(tmp_path):
    public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
    assert public == {
        "add", "retract", "supersede", "revise", "delete", "mint_coordination", "revise_coordination",
        "invocation_id", "actor", "store_id",
    }
```

(Tasks 4 and 5 each add one more name to this set.)

- [x] **Step 6: Run the two files and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_session_writer.py tests/acceptance/test_session_acceptance.py -q)` then `just check`
Expected: pass.

- [x] **Step 7: Commit and close**

```bash
git add python/src/beliefs/session python/tests/test_session_writer.py python/tests/acceptance/test_session_acceptance.py
tasks note beliefs-89e551 "open_attended_session(store_root=) refuses a genesis-less store; ScopedWriter carries its authority, actor, store_id"
tasks done beliefs-89e551
git add tasks
git commit -m "feat(session): bind an optional store root and expose actor and store id"
```

---

### Task 4: The ledgered operation port

**Files:**
- Create: `python/src/beliefs/session/routes.py`
- Modify: `python/src/beliefs/session/writer.py` (`_record_act` split; `ScopedWriter.operation_port`)
- Test: `python/tests/test_session_routes.py` (new)

**Interfaces:**
- Consumes: `ScopedWriter._authority`, `WriterSession._lock`, `WriterSession._require_current(invocation)`, `CorpusWriter._operation_port` (the durable port the writer factory built).
- Produces: `beliefs.session.routes.plan_records(plan) -> tuple[tuple[str, str], ...]`; `beliefs.session.routes.LedgeredPort(session, invocation, inner)`; `WriterSession._record_committed(invocation, *, intent: str, entry: str, records: tuple[tuple[str, str], ...]) -> None`; `ScopedWriter.operation_port() -> OperationPort`.

- [x] **Step 1: `tasks start beliefs-b9edfe`**

- [x] **Step 2: Write the failing tests**

Create `python/tests/test_session_routes.py`:

```python
"""The invocation-scoped run and holdings routes (session-routes design §4),
portably: a session from parts, the recording port, a fake store seam."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import narrowed
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp, DeleteOp
from test_operation_writes import proposition
from test_session_writer import DIGEST, make_session

from beliefs.errors import PermitExceeded, SessionProtocolError
from beliefs.permit import RequiredCapabilities
from beliefs.session import open_ledger_reader
from beliefs.session.routes import plan_records

RUNS = RequiredCapabilities.for_kinds({"run", "act-report"}, {"run": "run", "act-report": "run"})
INTENT = "1" * 64


def _plan(*nodes) -> tuple[CreateOp, ...]:
    return tuple(CreateOp(f"{n.kind}/{n.id.split(':', 1)[1]}.md", node_to_markdown(n).encode("utf-8")) for n in nodes)


def test_plan_records_reads_uid_and_id_from_each_create(tmp_path):
    a, b = proposition("one"), proposition("two")
    assert plan_records(_plan(a, b)) == ((a.uid, a.id), (b.uid, b.id))


def test_plan_records_refuses_any_other_op():
    with pytest.raises(SessionProtocolError, match="creates only"):
        plan_records((DeleteOp("x.md", expected_digest="a" * 64),))


def _run_port(tmp_path: Path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "run", DIGEST)
    writer = session.scoped(RUNS, "A")
    return session, writer, writer.operation_port(), ports[-1]


def test_execute_fulfilling_ledgers_an_act_with_the_plan_records(tmp_path):
    session, writer, port, inner = _run_port(tmp_path)
    node = proposition("p")
    fulfills = port.append_intent(b"intent")
    entry = port.execute_fulfilling(_plan(node), fulfills)
    session.close_invocation("A", {"done": [[node.uid, node.id]]})
    session.close()

    (act,) = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert (act.intent, act.entry, act.record_ids) == (fulfills, entry, ((node.uid, node.id),))
    assert [kind for kind, _ in inner.calls] == ["append_intent", "execute_fulfilling"]


def test_execute_and_the_guarded_form_are_refused_before_the_inner_port(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="fulfilling"):
        port.execute(_plan(proposition("p")))
    with pytest.raises(SessionProtocolError, match="guarded"):
        port.execute_fulfilling_guarded(_plan(proposition("p")), INTENT, guard=lambda _v: None, fallback=lambda r: ())
    assert inner.calls == []


def test_a_non_create_plan_is_refused_before_the_inner_port(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="creates only"):
        port.execute_fulfilling((DeleteOp("x.md", expected_digest="a" * 64),), INTENT)
    assert inner.calls == []


def test_a_closed_invocation_refuses_both_port_steps(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        port.append_intent(b"intent")
    with pytest.raises(SessionProtocolError):
        port.execute_fulfilling(_plan(proposition("p")), INTENT)
    assert inner.calls == []


def test_the_port_carries_the_scoped_authority_and_profile(tmp_path):
    _session, writer, port, inner = _run_port(tmp_path)
    assert port.authority is inner.authority
    assert port.authority.actor == writer.actor
    assert port.profile is inner.profile


def test_a_permit_below_run_is_refused_by_the_boundary_before_any_intent(tmp_path):
    from beliefs.boundary import execute_assessment_run

    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "run", DIGEST)
    port = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "A").operation_port()
    with pytest.raises(PermitExceeded):
        port.authority.require("run", ("run", "act-report"))
    assert ports[-1].calls == []
```

Round-1 review adds one deterministic concurrency regression for design §8
item 6. Move the `TracingLock` helper originally shown in Task 5 into this
file now; use it with a blocking recording-port `append_intent` to prove a
concurrent `close_invocation` reports `held-by-another`, stays blocked until
the append is released, and completes after the append. Temporarily release
the session lock between `_require_current` and the inner append and verify
this test fails before restoring the implementation.

(The last test states the boundary's own guard; `execute_assessment_run` opens with exactly that `require`, so the refusal precedes its `append_intent`.)

- [x] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_session_routes.py -q)`
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.session.routes'`.

- [x] **Step 4: Split `_record_act` and add the port**

`python/src/beliefs/session/writer.py`. Replace `_record_act` (`:228-262`) with the general entry and a commit-shaped wrapper:

```python
    def _record_committed(
        self, invocation: str, *, intent: str, entry: str, records: tuple[tuple[str, str], ...]
    ) -> None:
        """Ledger one committed write by its digests and record pairs. Reached
        only from `ScopedWriter._act` and the session routes, each of which
        already holds this lock and checked currency under it, so the
        re-check below is an invariant, not a refusal: an operation whose
        registration is durable can no longer be refused, and only a crash or
        a ledger I/O failure — both terminal — may leave it unledgered (§5,
        §13 item 18)."""
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise ScienceError(
                    f"the current invocation moved from {invocation} to {self._current} while an act "
                    "held the session lock"
                )
            self._ledger.append(
                {
                    "line": "act",
                    "invocation": invocation,
                    "corpus": self.corpus_id,
                    "entry": entry,
                    "intent": intent,
                    "records": [list(pair) for pair in records],
                }
            )
            self._index[invocation].acts.append(ActLine(invocation, self.corpus_id, entry, intent, records))

    def _record_act(self, invocation: str, commit: OperationCommit) -> None:
        records = () if commit.record is None else ((commit.record.uid, commit.record.id),)
        self._record_committed(invocation, intent=commit.intent_digest, entry=commit.entry_digest, records=records)
```

Add to `ScopedWriter` after `store_id`:

```python
    def operation_port(self) -> OperationPort:
        """The `run` route (session-routes design §4.1): this invocation's
        durable port, bound to its scoped authority, whose fulfilling commits
        are ledgered as `act` lines."""
        from beliefs.session.routes import LedgeredPort

        return LedgeredPort(self._session, self._invocation, self._writer._operation_port)
```

with `from beliefs.runrecord import OperationPort` among the imports (a `TYPE_CHECKING` import is fine; the module already uses `from __future__ import annotations`).

Create `python/src/beliefs/session/routes.py`:

```python
"""The invocation-scoped `run` and `holdings` routes (session-routes design
§4): two thin wrappers that let the session hear what the kernel boundaries
commit, and one helper that names the records a plan writes.

Lock order is session, then corpus operation lock — the order
`ScopedWriter._act` takes — and it is taken here in exactly one place per
route: `LedgeredPort.execute_fulfilling` and the seam's `corpus_lock`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nodes.core.frontmatter import node_from_markdown
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs.errors import SessionProtocolError
from beliefs.holdings.seam import StoreActSeam
from beliefs.permit import Authority
from beliefs.profile import ProfileSpec
from beliefs.runrecord import OperationPort

if TYPE_CHECKING:
    from beliefs.session.writer import WriterSession

__all__ = ["LedgeredPort", "plan_records"]


def plan_records(plan: Sequence[object]) -> tuple[tuple[str, str], ...]:
    """The `[uid, id]` pairs a plan writes, read from the plan's own bytes
    through the reader the corpus uses (design §4.3). A plan carrying anything
    but creates is refused: the run publication, act-report and holdings
    observation plans are creates only, and a route guesses nothing."""
    records: list[tuple[str, str]] = []
    for op in plan:
        if type(op) is not CreateOp:
            raise SessionProtocolError(
                f"a session route commits creates only; the plan carries {type(op).__name__}"
            )
        node = node_from_markdown(op.content.decode("utf-8"))
        records.append((node.uid, node.id))
    return tuple(records)


class LedgeredPort:
    """An `OperationPort` over the invocation's durable port (design §4.1)."""

    __slots__ = ("_inner", "_invocation", "_session")

    def __init__(self, session: WriterSession, invocation: str, inner: OperationPort) -> None:
        self._session = session
        self._invocation = invocation
        self._inner = inner

    @property
    def profile(self) -> ProfileSpec:
        return self._inner.profile

    @property
    def authority(self) -> Authority:
        return self._inner.authority

    def preflight(self, plan: WritePlan) -> None:
        self._inner.preflight(plan)

    def append_intent(self, payload: bytes) -> str:
        # The check and the durable append are one step under the lock: a
        # close on another thread cannot land between them.
        with self._session._lock:
            self._session._require_current(self._invocation)
            return self._inner.append_intent(payload)

    def execute(self, plan: WritePlan) -> None:
        raise SessionProtocolError("a session route commits only fulfilling writes")

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        with self._session._lock:
            self._session._require_current(self._invocation)
            records = plan_records(plan)
            entry = self._inner.execute_fulfilling(plan, fulfills)
            self._session._record_committed(self._invocation, intent=fulfills, entry=entry, records=records)
            return entry

    def execute_fulfilling_guarded(
        self,
        plan: WritePlan,
        fulfills: str,
        *,
        guard: Callable[[Any], str | None],
        fallback: Callable[[str], WritePlan],
    ) -> str | None:
        raise SessionProtocolError(
            "the guarded execution path is outside the session routes (session-routes design §4.1)"
        )
```

(`ledgered_seam` and its `__all__` entry are added together in Task 5.)

- [x] **Step 5: Run the routes file, the session files, and the checks**

Add `"operation_port"` to the expected set in `test_the_scoped_writer_exposes_the_seven_methods_the_routes_and_its_invocation` (`python/tests/test_session_writer.py`). Then:

Run: `(cd python && uv run --frozen pytest tests/test_session_routes.py tests/test_session_writer.py tests/test_session_ledger.py -q)` then `just check`
Expected: pass. `CorpusWriter._operation_port` (`corpus.py:1475`) is read directly: the session module already reaches the writer's private operation lock the same way, and pyright's private-usage report is not enabled in this repository.

- [x] **Step 6: Commit and close**

```bash
git add python/src/beliefs/session python/tests/test_session_routes.py
tasks note beliefs-b9edfe "LedgeredPort: currency atomic with append, act line from the plan's records, execute and guarded refused"
tasks done beliefs-b9edfe
git add tasks
git commit -m "feat(session): ledger the run route through the scoped writer's operation port"
```

---

### Task 5: The ledgered holdings seam and `holdings_context`

**Files:**
- Modify: `python/src/beliefs/session/routes.py` (add `ledgered_seam`), `python/src/beliefs/session/writer.py` (`ScopedWriter.holdings_context`)
- Test: `python/tests/test_session_routes.py`

**Interfaces:**
- Consumes: `WriterSession.store_root`, `.store_id`, `.profile`, `._holdings_seam`, `.corpus_root`; `ScopedWriter._authority`.
- Produces: `beliefs.session.routes.ledgered_seam(session, invocation, inner: StoreActSeam) -> StoreActSeam`; `ScopedWriter.holdings_context(*, instrument: str) -> ActContext`.

- [ ] **Step 1: `tasks start beliefs-c90220`**

- [ ] **Step 2: Write the failing tests**

Append to `python/tests/test_session_routes.py`:

```python
# --- the holdings route (design §4.2) ---------------------------------------------
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field

from beliefs.corpus import _operation_lock_for
from beliefs.holdings.boundary import ActContext, recheck, write
from beliefs.holdings.records import StoreLocator
from beliefs.holdings.seam import FileStateView, PathObservedView, StoreActSeam, StoreOutcomeView
from beliefs.holdings.records import holdings_observation, Found
from beliefs import stored

HOLDINGS = RequiredCapabilities.for_kinds({"holdings-observation"}, {})
STORE_ID = "1" * 32
GENESIS = b'{"domain":"science.store-root.v1","store_id":"' + STORE_ID.encode() + b'"}'
STATE = FileStateView("sha256:" + "a" * 64)


@dataclass
class FakeSeam:
    """The inner seam a ledgered seam wraps: records every member reached, and
    asserts the session lock is held on entry when `lock` is given."""

    root: Path
    lock: TracingLock | None = None
    on_corpus_lock: Any = None
    reached: list[str] = field(default_factory=list)
    published: list[tuple[object, ...]] = field(default_factory=list)
    entered: int = 0

    def _touch(self, name: str) -> None:
        if self.lock is not None:
            assert self.lock.held_by_me(), f"{name} entered without the session lock"
        self.reached.append(name)

    def build(self) -> StoreActSeam:
        @contextmanager
        def corpus_lock(root):
            self._touch("corpus_lock")
            with _operation_lock_for(root):
                self.entered += 1
                if self.on_corpus_lock is not None:
                    self.on_corpus_lock(self.entered)
                yield

        def append_intent(_root, _payload):
            self._touch("append_intent")
            return INTENT

        def publish_fulfilling(_root, plan, _intent):
            self._touch("publish_fulfilling")
            self.published.append(tuple(plan))
            return "2" * 64

        def read_path(_root, _path):
            self._touch("read_path")
            return PathObservedView(STATE)

        def store_write(_root, path, _bytes):
            self._touch("store_write")
            return StoreOutcomeView("tx", ((path, STATE),))

        def store_genesis(_root):
            self._touch("store_genesis")
            return GENESIS

        def unused(*_):
            raise AssertionError("not reached")

        return StoreActSeam(
            corpus_lock=corpus_lock, append_intent=append_intent, publish_fulfilling=publish_fulfilling,
            read_path=read_path, store_write=store_write, store_delete=unused, store_move=unused,
            store_genesis=store_genesis,
        )


BOTH = RequiredCapabilities.for_kinds({"holdings-observation", "proposition"}, {})


def _holdings(tmp_path: Path, seam: FakeSeam, scope: RequiredCapabilities = HOLDINGS):
    session, ports = make_session(tmp_path, store_root=tmp_path / "store", store_id=STORE_ID, holdings_seam=seam.build())
    session.claim_invocation("A", "hold", DIGEST)
    writer = session.scoped(scope, "A")
    return session, writer, writer.holdings_context(instrument="test"), ports[-1]


def _published_pair(seam: FakeSeam) -> tuple[str, str]:
    """The `[uid, id]` of the one node the fake seam was asked to publish,
    read from the plan's bytes: `stored.holdings_observation_node` mints a
    fresh uid per call, so the ledgered pair can only be read back, not rebuilt."""
    from nodes.core.frontmatter import node_from_markdown

    ((op,),) = seam.published
    node = node_from_markdown(op.content.decode("utf-8"))  # type: ignore[attr-defined]
    return node.uid, node.id


def test_holdings_context_without_a_store_is_a_protocol_error(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "hold", DIGEST)
    with pytest.raises(SessionProtocolError, match="no store"):
        session.scoped(HOLDINGS, "A").holdings_context(instrument="test")


def test_holdings_context_binds_the_session_and_the_scoped_authority(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, writer, ctx, _ = _holdings(tmp_path, seam)
    assert type(ctx) is ActContext
    assert (ctx.observer_root, ctx.store_root) == (session.corpus_root, tmp_path / "store")
    assert (ctx.observer, ctx.instrument, ctx.actor) == (session.actor, "test", writer.actor)
    assert ctx.authority is writer._authority and ctx.profile is session.profile


def test_a_holdings_write_ledgers_an_act_naming_the_observation(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, writer, ctx, _ = _holdings(tmp_path, seam)
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    pair = _published_pair(seam)
    session.close_invocation("A", {"done": [list(pair)]})
    session.close()

    (act,) = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert (act.intent, act.entry, act.record_ids) == (INTENT, "2" * 64, (pair,))
    assert seam.reached == ["corpus_lock", "append_intent", "store_genesis", "store_write", "corpus_lock", "publish_fulfilling"]


def test_a_context_kept_past_its_invocation_reaches_no_member(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    with pytest.raises(SessionProtocolError):
        recheck(ctx, StoreLocator(STORE_ID, "p.bin"))
    assert seam.reached == []
```

`TracingLock` is already present above this Task 5 append block because Task
4's round-1 concurrency regression moved the shared helper earlier. Reuse it;
do not define another lock wrapper.

The close-during-the-act test drives the close from inside the fake seam's own `append_intent` (the session lock is held there and is re-entrant):

```python
def test_a_close_inside_the_intent_append_is_refused_at_the_genesis_read(tmp_path):
    holder: dict[str, Any] = {}
    seam = FakeSeam(tmp_path / "corpus")
    original = seam.build

    def build():
        built = original()
        inner_append = built.append_intent

        def closing_append(root, payload):
            digest = inner_append(root, payload)
            holder["session"].close_invocation("A", {"done": []})  # re-entrant: the session lock is held
            return digest

        from dataclasses import replace
        return replace(built, append_intent=closing_append)

    seam.build = build  # type: ignore[method-assign]
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    holder["session"] = session
    with pytest.raises(SessionProtocolError):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    assert seam.reached == ["corpus_lock", "append_intent"]


def test_lock_order_is_session_then_corpus_everywhere(tmp_path):
    lock = TracingLock()
    seam = FakeSeam(tmp_path / "corpus", lock=lock)
    session, writer, ctx, _ = _holdings(tmp_path, seam, BOTH)  # the add needs the proposition kind too
    session._lock = lock  # type: ignore[assignment]
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    writer.add(proposition("p"))
    assert {outcome for _, outcome in lock.attempts} == {"owned"}
    assert "publish_fulfilling" in seam.reached


def test_a_holdings_write_and_a_corpus_add_on_two_threads_both_complete(tmp_path):
    b_signalled = threading.Event()
    a_in_publication = threading.Event()

    def on_attempt(thread_name: str, outcome: str) -> None:
        if thread_name == "B":
            b_signalled.set()

    lock = TracingLock(on_attempt=on_attempt)

    def on_corpus_lock(entered: int) -> None:
        if entered == 2:  # the publication's corpus lock
            a_in_publication.set()
            assert b_signalled.wait(5), "B never attempted the session lock"

    seam = FakeSeam(tmp_path / "corpus", on_corpus_lock=on_corpus_lock)
    session, writer, ctx, _ = _holdings(tmp_path, seam, BOTH)
    session._lock = lock  # type: ignore[assignment]
    failures: list[BaseException] = []

    def run(fn):
        try:
            fn()
        except BaseException as caught:  # noqa: BLE001 — surfaced by the assertion below
            failures.append(caught)

    a = threading.Thread(name="A", target=run, args=(lambda: write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes"),), daemon=True)
    b = threading.Thread(name="B", target=run, args=(lambda: writer.add(proposition("p")),), daemon=True)
    a.start()
    assert a_in_publication.wait(5)
    b.start()
    a.join(5)
    b.join(5)
    assert not a.is_alive() and not b.is_alive(), "deadlock: the lock order is not session then corpus"
    assert failures == []
    assert ("B", "held-by-another") in lock.attempts
```

- [ ] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_session_routes.py -q)`
Expected: the new tests FAIL — `AttributeError: 'ScopedWriter' object has no attribute 'holdings_context'`.

- [ ] **Step 4: Add the seam wrapper and the facade method**

Add `"ledgered_seam"` to `__all__` and append to `python/src/beliefs/session/routes.py`:

```python
def ledgered_seam(session: WriterSession, invocation: str, inner: StoreActSeam) -> StoreActSeam:
    """A `StoreActSeam` over the production seam (design §4.2). Every member
    requires the invocation to be current under the session lock, atomically
    with its delegate — the two that look like reads run recovery on a
    writable root, so none is inert. `corpus_lock` is where the session lock
    is taken (session, then corpus; the boundary holds the corpus lock when
    it appends and publishes), and `publish_fulfilling` records the act."""

    def guarded(member: Callable[..., Any]) -> Callable[..., Any]:
        def call(*args: Any) -> Any:
            with session._lock:
                session._require_current(invocation)
                return member(*args)

        return call

    @contextmanager
    def corpus_lock(root: Path) -> Iterator[None]:
        with session._lock:
            session._require_current(invocation)
            with inner.corpus_lock(root):
                yield

    def publish_fulfilling(root: Path, plan: Sequence[object], intent: str) -> str:
        with session._lock:
            session._require_current(invocation)
            records = plan_records(plan)
            entry = inner.publish_fulfilling(root, plan, intent)
            session._record_committed(invocation, intent=intent, entry=entry, records=records)
            return entry

    return StoreActSeam(
        corpus_lock=corpus_lock,
        append_intent=guarded(inner.append_intent),
        publish_fulfilling=publish_fulfilling,
        read_path=guarded(inner.read_path),
        store_write=guarded(inner.store_write),
        store_delete=guarded(inner.store_delete),
        store_move=guarded(inner.store_move),
        store_genesis=guarded(inner.store_genesis),
    )
```

Add to `ScopedWriter` in `python/src/beliefs/session/writer.py` after `operation_port`:

```python
    def holdings_context(self, *, instrument: str) -> ActContext:
        """The `holdings` route (session-routes design §4.2): an act context
        over the session's store, observed by the session actor under this
        invocation's scoped authority, whose published observations are
        ledgered as `act` lines."""
        from beliefs.holdings.boundary import ActContext
        from beliefs.session.routes import ledgered_seam

        session = self._session
        if session.store_root is None or session._holdings_seam is None or session.profile is None:
            raise SessionProtocolError("this session was opened with no store root; the holdings route has no store")
        return ActContext(
            observer_root=session.corpus_root,
            store_root=session.store_root,
            observer=session.actor,
            instrument=instrument,
            authority=self._authority,
            seam=ledgered_seam(session, self._invocation, session._holdings_seam),
            profile=session.profile,
        )
```

(`ActContext` is imported under `TYPE_CHECKING` for the annotation; the in-function import avoids a cycle through `beliefs.holdings.boundary` → `beliefs.corpus`.)

- [ ] **Step 5: Run the file, the holdings files, and the checks**

Add `"holdings_context"` to the expected set in `test_the_scoped_writer_exposes_the_seven_methods_the_routes_and_its_invocation` (`python/tests/test_session_writer.py`); the set is now complete. Then:

Run: `(cd python && uv run --frozen pytest tests/test_session_routes.py tests/test_session_writer.py tests/test_holdings_boundary.py -q)` then `just check`
Expected: pass.

- [ ] **Step 6: Prove the two lock-order tests bite**

Temporarily reverse the order in `ledgered_seam.corpus_lock` (enter `inner.corpus_lock(root)` first, then `session._lock`) and in `publish_fulfilling` (take `session._lock` only inside, after the boundary already holds the corpus lock — that is the code as reversed above). Run:

`(cd python && uv run --frozen pytest tests/test_session_routes.py -q -k "lock_order or two_threads")`

Expected: `test_lock_order_is_session_then_corpus_everywhere` fails on the `held_by_me` assertion inside `corpus_lock`; `test_a_holdings_write_and_a_corpus_add_on_two_threads_both_complete` fails on `is_alive`. Restore the designed order, rerun, expect pass. Record the observation in the task note.

- [ ] **Step 7: Commit and close**

```bash
git add python/src/beliefs/session python/tests/test_session_routes.py
tasks note beliefs-c90220 "ledgered_seam guards every member under the session lock, taken in corpus_lock; holdings_context binds the session store; both lock-order tests fail under the reversed order (verified)"
tasks done beliefs-c90220
git add tasks
git commit -m "feat(session): ledger the holdings route through the scoped writer's act context"
```

---

### Task 6: The durable routes on the acceptance rig

**Files:**
- Test: `python/tests/acceptance/test_session_acceptance.py`

**Interfaces:**
- Consumes: Tasks 3–5; `beliefs.runrecord.publication_plan(closure)`; `test_audit.assessment_closure`, `fixtures_cut3.spec_draft/spec_rules`; `beliefs.holdings.boundary.write`; `beliefs.holdings.records.StoreLocator`; `beliefs.session.reconcile_sessions`.

- [ ] **Step 1: `tasks start beliefs-440c98`**

- [ ] **Step 2: Write the tests**

Append to `python/tests/acceptance/test_session_acceptance.py` (add the imports named in the body to the file's import blocks):

```python
# --- the routes, durably (session-routes design §8 items 10–12) -------------------
# (`from nodes.core.frontmatter import node_from_markdown` joins the file's imports.)
def _registration_fulfilling(root: Path, intent: str) -> str:
    matches = [e.digest for e in chain(root).entries if getattr(e, "fulfills", None) == intent]
    assert len(matches) == 1, matches
    return matches[0]


def test_a_holdings_write_through_the_scoped_writer_is_ledgered_against_the_chain(work_directory):
    from beliefs.holdings.boundary import write
    from beliefs.holdings.records import StoreLocator

    root = adopted(work_directory, "holdings-route")
    store = _track(work_directory / f"store-{secrets.token_hex(4)}")
    init_store_root(store, authority=FULL)
    session, ops = attended(work_directory, root, store_root=store)
    session.claim_invocation("A", "dataset", "d" * 64)
    writer = session.scoped(RequiredCapabilities.for_kinds({"holdings-observation"}, {}), "A")
    published = write(writer.holdings_context(instrument="acceptance"), StoreLocator(writer.store_id, "held.bin"), b"held")
    (act,) = session.invocation_acts("A")
    session.close_invocation("A", {"done": [list(pair) for pair in act.record_ids]})
    session.close()

    # The persisted node is the only holder of the uid the boundary minted.
    persisted = node_from_markdown((root / "holdings-observation" / f"{published.record.identity()}.md").read_text())
    assert act.record_ids == ((persisted.uid, persisted.id),)
    assert act.entry == _registration_fulfilling(root, act.intent)
    assert reconcile_sessions(config_for(work_directory, root), ops) == ()


def test_a_run_publication_through_the_operation_port_is_ledgered_against_the_chain(work_directory):
    from fixtures_cut3 import spec_draft, spec_rules
    from test_audit import assessment_closure

    from beliefs.identity import v1
    from beliefs.runrecord import publication_plan
    from beliefs.spec import freeze

    root = adopted(work_directory, "run-route")
    session, ops = attended(work_directory, root)
    session.claim_invocation("A", "run", "d" * 64)
    writer = session.scoped(RequiredCapabilities.for_kinds({"run", "act-report"}, {"run": "run", "act-report": "run"}), "A")
    port = writer.operation_port()
    closure = assessment_closure(freeze(spec_draft(), held_rules=spec_rules()))
    intent = port.append_intent(v1.encode({"spec_identity": closure.recipe.spec_identity, "event_token": "tok", "actor": writer.actor}))
    _address, _produces, plan = publication_plan(closure)
    entry = port.execute_fulfilling(plan, intent)
    (act,) = session.invocation_acts("A")
    session.close_invocation("A", {"done": [list(pair) for pair in act.record_ids]})
    session.close()

    assert act.entry == entry == _registration_fulfilling(root, intent)
    (pair,) = act.record_ids
    assert pair[1] == f"run:{closure.address()}"
    assert reconcile_sessions(config_for(work_directory, root), ops) == ()
```

- [ ] **Step 3: Run them**

Run: `(cd python && uv run --frozen pytest tests/acceptance/test_session_acceptance.py -q -k "holdings_route or run_route or through_the")`
Expected: PASS (`stored.run_publication_node(slug, …)` assigns `id = f"run:{slug}"`, and `publication_plan` passes the closure address as the slug).

- [ ] **Step 4: Run `just check` and commit**

```bash
git add python/tests/acceptance/test_session_acceptance.py
tasks note beliefs-440c98 "durable: holdings write and run publication through the routes are ledgered with the chain's registration digest"
tasks done beliefs-440c98
git add tasks
git commit -m "test(session): prove the routes durably against the chain"
```

---

### Task 7: Reconciliation hears the run and holdings intent shapes

**Files:**
- Modify: `python/src/beliefs/intents/holdings.py` (`decode_holdings_intent` returns `actor`; this is the source), `python/src/beliefs/holdings/qualify.py` (GENERATED from it by `python/tools/regen_holdings_interior.py`; never hand-edited), `python/src/beliefs/session/reconcile.py:181-190`
- Test: `python/tests/test_session_reconcile.py` (`test_intent_evidence.py` exercises the decoder and asserts only its `location`, so the added key breaks nothing)

**Interfaces:**
- Produces: `decode_holdings_intent(row)` mapping gains `"actor": str`; `reconcile` classifies intents of all three decoded shapes by their session actor.

- [ ] **Step 1: `tasks start beliefs-7fd23b`**

- [ ] **Step 2: Write the failing tests**

Append to `python/tests/test_session_reconcile.py`:

```python
# --- the run and holdings shapes (session-routes design §4.4) ----------------------
from beliefs.holdings.boundary import intent_payload
from beliefs.holdings.qualify import decode_holdings_intent
from beliefs.holdings.records import StoreLocator


def run_intent(digest: str, session: str = S1) -> IntentEntryView:
    return IntentEntryView(digest=digest, payload=v1.encode({"spec_identity": "5" * 64, "event_token": "tok", "actor": f"session:{session}"}))


def holdings_intent(digest: str, session: str = S1) -> IntentEntryView:
    payload = intent_payload(location=StoreLocator("1" * 32, "p.bin"), act_kind="write", event_token="tok", actor=f"session:{session}")
    return IntentEntryView(digest=digest, payload=payload)


def test_the_decoded_holdings_intent_carries_its_actor():
    entry = holdings_intent(I)
    decoded = decode_holdings_intent({"digest": I, "entry": {"payload": entry.payload.hex()}})
    assert decoded is not None and decoded["actor"] == f"session:{S1}"


@pytest.mark.parametrize("shape", [run_intent, holdings_intent])
def test_a_session_intent_of_either_shape_with_no_ledger_is_unknown(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-unknown", "error", I) in codes(reconcile([], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent])
def test_an_uncovered_registration_of_either_shape_is_foreign_when_closed(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-entry-foreign", "error", R) in codes(reconcile([ledger(opens=("A",), closes=("A",))], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent])
def test_an_uncovered_registration_of_either_shape_is_outcome_unknown_when_open(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-outcome-unknown", "warning", R) in codes(reconcile([ledger(opens=("A",), closed=False)], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent])
def test_a_covered_registration_of_either_shape_yields_nothing(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains) == ()


def test_an_interrupted_holdings_act_is_an_unclaimed_intent():
    chains = {CORPUS: view(holdings_intent(I))}
    assert ("session-intent-unclaimed", "error", I) in codes(reconcile([ledger(opens=("A",), closes=("A",))], chains))
```

- [ ] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_session_reconcile.py -q -k "either_shape or carries_its_actor or interrupted_holdings")`
Expected: FAIL — the actor `KeyError` and empty finding lists.

- [ ] **Step 4: Decode the actor and classify every shape**

In `python/src/beliefs/intents/holdings.py`, the `return` of `decode_holdings_intent` (the source `shapes.decode_intent` calls):

```python
    return {
        "digest": row["digest"],
        "actor": value["actor"],
        "event_token": value["event_token"],
        "kind": value["kind"],
        "location": _location(value["location"]),
    }
```

Then regenerate the rule-side copy and confirm the two agree:

```bash
(cd python && uv run --frozen python tools/regen_holdings_interior.py && uv run --frozen pytest tests/test_intents_holdings.py -q)
```

`python/src/beliefs/session/reconcile.py`. Add `from beliefs.report import AssessmentRunIntent, OperationIntent` and, above `reconcile`:

```python
def _session_of(decoded: shapes.DecodedIntent | shapes.Unrecognized) -> str | None:
    """The session id an intent names as its actor, for any of the three
    decoded shapes (session-routes design §4.4); None for an unrecognized
    intent or a non-session actor."""
    if type(decoded) is not shapes.DecodedIntent:
        return None
    value = decoded.value
    if isinstance(value, (OperationIntent, AssessmentRunIntent)):
        actor: object = value.actor
    else:
        actor = value.get("actor")
    if type(actor) is not str:
        return None
    match = _SESSION_ACTOR.fullmatch(actor)
    return None if match is None else match.group(1)
```

Replace lines `183-190` (`decoded = ...` through `sid = match.group(1)`) with:

```python
            decoded = shapes.decode_intent(entry.digest, entry.payload)
            sid = _session_of(decoded)
            if sid is None:
                continue
            actor = f"session:{sid}"
```

and in the `session-unknown` finding use `f"actor={actor}"` for the detail. Check `shapes.Unrecognized` is the decoder's other return type (it is, `decode_intent -> DecodedIntent | Unrecognized`).

- [ ] **Step 5: Run the reconcile, holdings and acceptance files and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_session_reconcile.py tests/test_intent_evidence.py tests/test_intents_holdings.py tests/test_holdings_receipt.py tests/acceptance/test_session_acceptance.py -q)` then `just check`
Expected: pass.

- [ ] **Step 6: Commit and close**

```bash
git add python/src/beliefs/intents/holdings.py python/src/beliefs/holdings/qualify.py python/src/beliefs/session/reconcile.py python/tests/test_session_reconcile.py
tasks note beliefs-7fd23b "reconcile classifies run and holdings intents by session actor; the decoded holdings intent carries its actor"
tasks done beliefs-7fd23b
git add tasks
git commit -m "feat(session): reconcile the run and holdings intent shapes"
```

---

### Task 8: `replay` over a closure

**Files:**
- Modify: `python/src/beliefs/replay.py:111-150`
- Test: `python/tests/test_replay.py`

**Interfaces:**
- Produces: `replay(original: RunMinted | RunClosure, …)`.

- [ ] **Step 1: `tasks start beliefs-469af0`**

- [ ] **Step 2: Write the failing test**

Append to `python/tests/test_replay.py`:

```python
def test_replay_over_a_closure_is_replay_over_the_minted_result(monkeypatch, tmp_path):
    from fixtures_cut3 import spec_draft, spec_rules
    from test_audit import assessment_closure

    from beliefs import replay as replay_module
    from beliefs.boundary import RunMinted
    from beliefs.report import AssessmentRunIntent, Registration
    from beliefs.spec import freeze

    frozen = freeze(spec_draft(), held_rules=spec_rules())
    closure = assessment_closure(frozen)
    minted = RunMinted(run=closure, intent=AssessmentRunIntent(frozen.identity, "tok", "test-actor"), registration=Registration("tok", "p" * 64))
    seen: list[dict] = []

    def capture(**kwargs):
        seen.append(kwargs)
        return "sentinel"

    monkeypatch.setattr(replay_module, "execute_assessment_run", capture)
    common = dict(port=object(), spec=frozen, definition=closure.recipe.workflow_definition, code_roots=(), held_inputs={},
                  entrypoint="e", targets=("t",), declared_outputs=tuple(n for n, _ in closure.result.outputs),
                  observer="o", started_at="2026-09-09T00:00:00Z", host_realization="h", scratch_base=tmp_path)
    assert replay_module.replay(minted, **common) == "sentinel"
    assert replay_module.replay(closure, **common) == "sentinel"
    assert seen[0] == seen[1]
```

(`RunMinted`'s exact constructor fields are `run`, `intent`, `registration` — `boundary.py:137`; if `Registration` needs different strings, mirror `test_boundary.py`'s minted fixture.)

- [ ] **Step 3: Run it to see it fail**

Run: `(cd python && uv run --frozen pytest tests/test_replay.py -q -k over_a_closure)`
Expected: FAIL — `AttributeError: 'RunClosure' object has no attribute 'run'`.

- [ ] **Step 4: Accept the closure**

`python/src/beliefs/replay.py`: import `RunClosure` from `beliefs.recipe` (extend the existing `from beliefs.recipe import (...)` block) and change the signature and the two reads:

```python
def replay(
    original: RunMinted | RunClosure,
    *,
    ...
) -> RunMinted | RunRefused:
    """Replay a run from its closure. A minted result is accepted for the
    boundary's callers; a stored run record's closure is what the surface
    holds, and only the closure is read (session-routes design §6)."""
    closure = original.run if type(original) is RunMinted else original
    common = {
        ...
        "boundary_policy": closure.recipe.boundary_policy,
    }
    recipe = closure.recipe
```

- [ ] **Step 5: Run the file and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_replay.py -q)` then `just check`
Expected: pass.

- [ ] **Step 6: Commit and close**

```bash
git add python/src/beliefs/replay.py python/tests/test_replay.py
tasks note beliefs-469af0 "replay reads only the closure and accepts one directly"
tasks done beliefs-469af0
git add tasks
git commit -m "feat(replay): accept a run closure"
```

---

### Task 9: Reference rules keyed by kernel-scoped identity

**Files:**
- Create: `python/src/beliefs/rules.py`
- Modify: `python/src/beliefs/replay.py:66` (`CONTENT_EQUALITY` fixtures), `python/src/beliefs/spec.py:58` (`BITWISE_EQUIVALENCE_RULES`), `python/src/beliefs/spec.py:196-235` (a `HeldImplementation` protocol so `freeze` accepts either implementation type)
- Test: `python/tests/test_rules.py` (new), `python/tests/test_spec.py`

**Interfaces:**
- Produces: `beliefs.rules.OUTCOME_FILE`, `OUTCOME_FILE_RULE`, `CONTENT_IDENTITY_RULE`, `OUTCOME_FILE_V1`, `REFERENCE_RULES`, `outcome_digest(outcome) -> str`, `interpret_outcome_file(manifest) -> dict[str, str]`; `beliefs.spec.HeldImplementation` protocol; `freeze(..., held_rules: Mapping[str, HeldImplementation])`.

- [ ] **Step 1: `tasks start beliefs-77caa9`**

- [ ] **Step 2: Write the failing tests**

Create `python/tests/test_rules.py`:

```python
"""The reference rules the kernel ships, keyed by rule identity (session-routes design §5)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fixtures_cut3 import spec_draft

from beliefs.errors import UnfreezableSpec
from beliefs.identity import v1
from beliefs.recipe import ResultManifest
from beliefs.replay import CONTENT_EQUALITY
from beliefs.rules import (
    CONTENT_IDENTITY_RULE,
    OUTCOME_FILE,
    OUTCOME_FILE_RULE,
    OUTCOME_FILE_V1,
    REFERENCE_RULES,
    interpret_outcome_file,
    outcome_digest,
)
from beliefs.spec import (
    BITWISE_EQUIVALENCE_RULES,
    SPEC_DOMAIN,
    StochasticUnseeded,
    freeze,
    frozen_projection,
    implementation_conforms,
    restore,
)


def test_every_reference_rule_conforms_and_carries_a_kernel_identity():
    assert set(REFERENCE_RULES) == {OUTCOME_FILE_RULE, CONTENT_IDENTITY_RULE}
    for identity, impl in REFERENCE_RULES.items():
        assert identity.startswith("beliefs/") and identity.endswith("/v1")
        assert impl.fixtures, identity
        assert implementation_conforms(impl), identity


def test_the_outcome_rule_maps_each_canonical_line_and_refuses_the_rest():
    for outcome in ("supported", "refuted", "inconclusive"):
        assert interpret_outcome_file(ResultManifest(outputs=((OUTCOME_FILE, outcome_digest(outcome)),))) == {"outcome": outcome}
    with pytest.raises(ValueError, match="canonical"):
        interpret_outcome_file(ResultManifest(outputs=((OUTCOME_FILE, "sha256:" + "0" * 64),)))
    with pytest.raises(ValueError, match=OUTCOME_FILE):
        interpret_outcome_file(ResultManifest(outputs=(("outputs/stats.tsv", "sha256:" + "0" * 64),)))
    assert OUTCOME_FILE_V1.identity == "impl-outcome-file-1"


def test_content_equality_keeps_its_identity_and_is_no_longer_vacuous():
    assert REFERENCE_RULES[CONTENT_IDENTITY_RULE] is CONTENT_EQUALITY
    assert CONTENT_EQUALITY.identity == "impl-eq-1"
    assert len(CONTENT_EQUALITY.fixtures) == 2
    assert implementation_conforms(CONTENT_EQUALITY)


def _kernel_draft(**overrides):
    return spec_draft(interpretation_rule=OUTCOME_FILE_RULE, equivalence_rule=CONTENT_IDENTITY_RULE, **overrides)


def test_freeze_binds_the_reference_rules():
    frozen = freeze(_kernel_draft(), held_rules=REFERENCE_RULES)
    assert frozen.rule_bindings == ((CONTENT_IDENTITY_RULE, "impl-eq-1"), (OUTCOME_FILE_RULE, "impl-outcome-file-1"))


def test_the_kernel_equality_identity_is_bitwise_at_freeze():
    assert CONTENT_IDENTITY_RULE in BITWISE_EQUIVALENCE_RULES
    with pytest.raises(UnfreezableSpec):
        freeze(_kernel_draft(nondeterminism=StochasticUnseeded(rationale="honest")), held_rules=REFERENCE_RULES)


def test_the_kernel_equality_identity_is_bitwise_at_restore():
    mapping = frozen_projection(freeze(_kernel_draft(), held_rules=REFERENCE_RULES))
    mapping["nondeterminism"] = StochasticUnseeded(rationale="honest").projection()
    identity = v1.digest(SPEC_DOMAIN, mapping)
    with pytest.raises(UnfreezableSpec):
        restore(identity, v1.encode(mapping))
```

- [ ] **Step 3: Run them to see them fail**

Run: `(cd python && uv run --frozen pytest tests/test_rules.py -q)`
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.rules'`.

- [ ] **Step 4: Ship the rules**

Create `python/src/beliefs/rules.py`:

```python
"""Reference rule implementations keyed by rule identity (session-routes
design §5).

A rule identity is `<scope>/<rule>/v<N>`: the scope names the author, the
version is the contract's. The kernel's scope is `beliefs`. The identity is
digested into every spec that binds it and is permanent; a new digest scheme
is a new version, a faster implementation of the same contract is a new
`impl-…` identity under the same rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from types import MappingProxyType

from beliefs.recipe import ResultManifest
from beliefs.replay import CONTENT_EQUALITY, EquivalenceImplementation
from beliefs.spec import RuleFixture, RuleImplementation

__all__ = [
    "CONTENT_IDENTITY_RULE",
    "OUTCOME_FILE",
    "OUTCOME_FILE_RULE",
    "OUTCOME_FILE_V1",
    "OUTCOMES",
    "REFERENCE_RULES",
    "interpret_outcome_file",
    "outcome_digest",
]

OUTCOME_FILE = "outputs/outcome.txt"
OUTCOME_FILE_RULE = "beliefs/outcome-file/v1"
CONTENT_IDENTITY_RULE = "beliefs/content-identity-equality/v1"
OUTCOMES = ("supported", "refuted", "inconclusive")


def outcome_digest(outcome: str) -> str:
    """The digest of the canonical outcome line: the word and one newline."""
    return "sha256:" + sha256((outcome + "\n").encode("utf-8")).hexdigest()


_OUTCOME_BY_DIGEST: Mapping[str, str] = MappingProxyType({outcome_digest(o): o for o in OUTCOMES})


def interpret_outcome_file(manifest: ResultManifest) -> dict[str, str]:
    """`beliefs/outcome-file/v1`: the manifest's digest for the outcome file
    names one of the three canonical lines. The rule sees digests, not
    bytes; a manifest without the file or with another digest raises, which
    `implementation_conforms` reads as non-conformance."""
    outputs = dict(manifest.outputs)
    if OUTCOME_FILE not in outputs:
        raise ValueError(f"the result manifest carries no {OUTCOME_FILE}")
    digest = outputs[OUTCOME_FILE]
    if digest not in _OUTCOME_BY_DIGEST:
        raise ValueError(f"{OUTCOME_FILE} digest {digest} is none of the canonical outcome lines")
    return {"outcome": _OUTCOME_BY_DIGEST[digest]}


def _manifest(outcome: str) -> ResultManifest:
    return ResultManifest(outputs=((OUTCOME_FILE, outcome_digest(outcome)),))


OUTCOME_FILE_V1 = RuleImplementation(
    identity="impl-outcome-file-1",
    evaluate=interpret_outcome_file,
    fixtures=tuple(RuleFixture(arguments=(_manifest(o),), expected={"outcome": o}) for o in OUTCOMES),
)

REFERENCE_RULES: Mapping[str, RuleImplementation | EquivalenceImplementation] = MappingProxyType(
    {OUTCOME_FILE_RULE: OUTCOME_FILE_V1, CONTENT_IDENTITY_RULE: CONTENT_EQUALITY}
)
```

`python/src/beliefs/replay.py:66`, with `ResultManifest` already imported from `beliefs.recipe`:

```python
_EQUAL_A = ResultManifest(outputs=(("outputs/result.txt", "sha256:" + "a" * 64),))
_EQUAL_B = ResultManifest(outputs=(("outputs/result.txt", "sha256:" + "b" * 64),))
CONTENT_EQUALITY = EquivalenceImplementation(
    "impl-eq-1",
    _manifest_equality,
    (
        RuleFixture(arguments=(_EQUAL_A, _EQUAL_A), expected="passed"),
        RuleFixture(arguments=(_EQUAL_A, _EQUAL_B), expected="failed"),
    ),
)
```

`python/src/beliefs/spec.py:58`:

```python
BITWISE_EQUIVALENCE_RULES = frozenset({"content-identity-equality/v1", "beliefs/content-identity-equality/v1"})
```

`python/src/beliefs/spec.py`, after `RuleImplementation`: a protocol both implementation types satisfy (frozen dataclass fields read as properties), and type `implementation_conforms`, `bind_rules`, `freeze` and the `held_rules` parameter at `:512` with it:

```python
class HeldImplementation(Protocol):
    """What `freeze` binds: an identity, an evaluator and fixtures — the
    interpretation and equivalence implementations both."""

    @property
    def identity(self) -> str: ...
    @property
    def evaluate(self) -> Callable[..., object]: ...
    @property
    def fixtures(self) -> tuple[RuleFixture, ...]: ...
```

(`from typing import Protocol` beside the existing typing imports; add `"HeldImplementation"` to `__all__`.)

- [ ] **Step 5: Run the rules, spec and replay files and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_rules.py tests/test_spec.py tests/test_replay.py tests/test_reproduction_driver.py -q)` then `just check`
Expected: pass; pyright accepts `REFERENCE_RULES` where `held_rules` is expected.

- [ ] **Step 6: Commit and close**

```bash
git add python/src/beliefs/rules.py python/src/beliefs/replay.py python/src/beliefs/spec.py python/tests/test_rules.py
tasks note beliefs-77caa9 "beliefs.rules ships outcome-file/v1 and content-identity-equality/v1 under the beliefs scope; the kernel equality identity is bitwise"
tasks done beliefs-77caa9
git add tasks
git commit -m "feat(rules): ship the reference rules keyed by kernel-scoped identity"
```

---

### Task 10: The reproduction driver maps onto the kernel rules

**Files:**
- Modify: `python/tools/reproduction/spec.py:34-84`; the callers of the removed accessors: `python/tools/reproduction/run.py:96,159`, `python/tools/reproduction/belief.py:117`, `python/tools/reproduction/close.py:33-34`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `beliefs.rules.OUTCOME_FILE_V1`, `beliefs.replay.CONTENT_EQUALITY`.
- Produces: `reproduction.spec.held_rules()` mapping the driver's two identities to the kernel objects; `reproduction.spec.INTERPRETATION` (= `OUTCOME_FILE_V1`) and `reproduction.spec.EQUIVALENCE` (= `CONTENT_EQUALITY`) replacing the `interpretation()` / `equivalence()` accessors; `OUTCOME_FILE`, `INTERPRETATION_RULE`, `EQUIVALENCE_RULE`, `OUTCOME_DIGESTS` unchanged in value.

- [ ] **Step 1: `tasks start beliefs-dff3e9`, then pin the pre-change identity**

Before touching the driver, compute the identity the current code freezes for the fixed draft the driver's existing test uses:

```bash
(cd python && uv run --frozen python - <<'EOF'
from decimal import Decimal
from reproduction import spec as m
from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
draft = SpecDraft(
    target="proposition:p", estimand="e", method="m", assumptions="a", falsification="f",
    input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),), applicability="x",
    interpretation_rule=m.INTERPRETATION_RULE, equivalence_rule=m.EQUIVALENCE_RULE,
    parameters={"alpha": Decimal("0.05")}, nondeterminism=Deterministic(),
)
print(freeze(draft, held_rules=m.held_rules()).identity)
EOF
)
```

Copy the printed 64-character identity into `PINNED_IDENTITY` in Step 2.

- [ ] **Step 2: Write the failing test**

Append to `python/tests/test_reproduction_driver.py`:

```python
PINNED_IDENTITY = "<paste the identity printed in Step 1>"


def test_the_driver_binds_the_kernel_rules_under_its_own_identities():
    from decimal import Decimal

    from reproduction import spec as spec_module

    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.rules import OUTCOME_FILE_V1
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze

    held = spec_module.held_rules()
    assert held[spec_module.INTERPRETATION_RULE] is OUTCOME_FILE_V1
    assert held[spec_module.EQUIVALENCE_RULE] is CONTENT_EQUALITY
    draft = SpecDraft(
        target="proposition:p", estimand="e", method="m", assumptions="a", falsification="f",
        input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),), applicability="x",
        interpretation_rule=spec_module.INTERPRETATION_RULE, equivalence_rule=spec_module.EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")}, nondeterminism=Deterministic(),
    )
    frozen = freeze(draft, held_rules=held)
    # The pairs the 2026-09-05 record digests, unchanged: identity-neutral by construction.
    assert frozen.rule_bindings == (
        ("content-identity-equality/v1", "impl-eq-1"),
        ("mm30-reproduction/outcome-file/v1", "impl-outcome-file-1"),
    )
    assert frozen.identity == PINNED_IDENTITY
```

- [ ] **Step 3: Run it to see it fail**

Run: `(cd python && uv run --frozen pytest tests/test_reproduction_driver.py -q -k binds_the_kernel_rules)`
Expected: FAIL on the `is OUTCOME_FILE_V1` assertion (the identity assertion would pass already, which is the point).

- [ ] **Step 4: Re-point the driver**

In `python/tools/reproduction/spec.py` delete `_interpret`, `interpretation()` and `equivalence()` and the now-unused imports (`cache` stays if still used by `frozen()`; `sha256`, `RuleFixture`, `RuleImplementation`, `EquivalenceImplementation`, `ResultManifest` go if unused). Replace the constants and `held_rules`:

```python
from beliefs.replay import CONTENT_EQUALITY
from beliefs.rules import OUTCOME_FILE, OUTCOME_FILE_V1, outcome_digest

...
INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"
EQUIVALENCE_RULE = "content-identity-equality/v1"
OUTCOME_DIGESTS = {outcome_digest(o): o for o in ("supported", "refuted", "inconclusive")}
INTERPRETATION = OUTCOME_FILE_V1
EQUIVALENCE = CONTENT_EQUALITY


def held_rules() -> dict:
    """The driver's identities, bound to the kernel's implementations
    (session-routes design §5.2). The record's spec identity is unchanged:
    `freeze` digests (rule identity, implementation identity) pairs, and both
    pairs are the ones the 2026-09-05 record carries."""
    return {INTERPRETATION_RULE: INTERPRETATION, EQUIVALENCE_RULE: EQUIVALENCE}
```

The three other driver modules call the removed accessors; change each call site to the constants, keeping the mapping shape it builds:

- `python/tools/reproduction/run.py:96`: `implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION},`
- `python/tools/reproduction/run.py:159`: `held_rules={spec.EQUIVALENCE.identity: spec.EQUIVALENCE},`
- `python/tools/reproduction/belief.py:117`: `held_rules={spec.EQUIVALENCE.identity: spec.EQUIVALENCE},`
- `python/tools/reproduction/close.py:33-34`: `held_rules={spec.EQUIVALENCE.identity: spec.EQUIVALENCE},` and `implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION},`

Then `grep -rn "interpretation()\|equivalence()" python/tools python/tests` must print nothing.

Keep `OUTCOME_FILE` importable from the module (`from beliefs.rules import OUTCOME_FILE` re-exports it) — `grep -rn "spec.OUTCOME_FILE\|OUTCOME_DIGESTS" python/tools python/tests` and keep every name still referenced.

- [ ] **Step 5: Run the driver tests and the checks**

Run: `(cd python && uv run --frozen pytest tests/test_reproduction_driver.py -q)` then `just check`
Expected: pass, including `test_spec_record_carries_a_fresh_semantic_stamp`.

- [ ] **Step 6: Commit and close**

```bash
git add python/tools/reproduction python/tests/test_reproduction_driver.py
tasks note beliefs-dff3e9 "driver held_rules maps its identities onto the kernel implementations; frozen identity pinned and unchanged"
tasks done beliefs-dff3e9
git add tasks
git commit -m "refactor(reproduction): bind the driver's rule identities to the kernel implementations"
```

---

### Task 11: Status, ledger row, and the science handoff

**Files:**
- Modify: `docs/designs/2026-09-09-session-routes-design.md` (Status), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (a row for the session routes beside the writer-session row, `:125` region), `docs/guide/` (only if a guide page lists `ScopedWriter`'s methods or `open_attended_session`'s signature: `grep -rn "ScopedWriter\|open_attended_session" docs/guide`)

- [ ] **Step 1: `tasks start beliefs-6a9931`, then run the whole gate**

Run: `just gate`
Expected: pass. The serial `just test` is the conformance gate; do not skip it.

- [ ] **Step 2: Correct the design's status and the ledger**

In the design's `**Status:**` replace `Not yet implemented.` with `Implemented on branch kernel-seams, <date>: Tasks 1–10 of ../plans/2026-09-09-session-routes.md; landed at <merge commit> (fill on merge).` In the adoption ledger add, after the writer-session bullet, one bullet: `- **The session routes** — the scoped writer's run and holdings routes, ledgered; the public store identity reader; the reference rules under the beliefs scope (docs/designs/2026-09-09-session-routes-design.md). Built.` Update any guide page found by the grep to the new signatures.

- [ ] **Step 3: Close the three tasks and tell science what landed**

```bash
tasks note beliefs-6a9931 "status corrected, ledger row added, science notified"
tasks done beliefs-6a9931
tasks note beliefs-5fe2e3 "landed: open_attended_session(store_root=), ScopedWriter.actor/store_id/operation_port()/holdings_context(), replay over a RunClosure; reconciliation covers run and holdings intents"
tasks done beliefs-5fe2e3
tasks note beliefs-e5ab34 "landed: beliefs.rules.REFERENCE_RULES keyed beliefs/outcome-file/v1 and beliefs/content-identity-equality/v1; beliefs.rules.OUTCOME_FILE; the driver binds the same objects"
tasks done beliefs-e5ab34
tasks note sci-66b26d "kernel seams landed on beliefs branch kernel-seams. Names differ from the plan's assumptions in one place: rule identities are beliefs/outcome-file/v1 and beliefs/content-identity-equality/v1 (constants beliefs.rules.OUTCOME_FILE_RULE, CONTENT_IDENTITY_RULE); adjust the spec command's resolution and the fixture contract at the call sites."
tasks check
git add docs tasks
git commit -m "docs(session): record the session routes as built"
```

- [ ] **Step 4: Hand back**

Report the branch head and the three closed task ids. Merging `kernel-seams` into `main` is the operator's; the science plan's Task 3 becomes ready once `beliefs-2d9a55` is closed (it already is after Task 1), and Tasks 4, 6–9, 11 once the other two close.
