# Restore Sub-90-Second `test-fast` Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a repeatable 16-worker `TT_FORCE=1 just test-fast` wall-time median of at most 90 seconds (targeting 62–72 seconds) without weakening any test, static boundary invariant, skip partition, or live environment-observation guarantee, then verify and locally integrate `beliefs-0f5112`.

**Architecture:** Part 1 eliminates redundant test-machinery work across three hotspots: a byte-keyed bounded AST cache plus outer-loop hoisting in `test_capability_boundary.py`, a module-scoped exported publication in `test_session_sharing_doors.py` backed by a `try / finally` certified-volume context manager, and a byte-verified module-scoped read-only source world for the 8 non-mutating items in `test_session_publish_door.py`. Part 2 cuts single-walk Python object and syscall churn inside `beliefs.adapter._Closure` (string-prefix root matching, string-keyed parent `realpath` plus single `os.lstat`, directory-pruned `os.scandir`, parent-resolved low-allocation `RECORD` scanning, and in-walk 20-byte ELF header retention) with zero cross-call caching, proven end to end by three alternating clean-tree 16-worker baseline/candidate pairs (`B1, C1, B2, C2, B3, C3`) and one certified `just test-full` run (`<= 300 s`).

**Tech Stack:** Python 3.11+ standard library (`ast`, `contextlib`, `errno`, `functools`, `os`, `stat`, `struct`), `pytest` / `pytest-xdist` (`--dist=loadgroup`), `just`, `tools/tt`, `host-budget`, and Vitest.

**Spec:** `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md` (accepted in spec round 2 at `fb26beb`, approved by user in spec round 3).

## Global Constraints

- **Policy-off test execution (`.tt.toml` has `automatic_broad = false`):** Run fresh focused tests via `just test-one <args>` (paths relative to `python/`) and mandatory `just check-hygiene` during implementation and any corrective review round. Never call `pytest` or `vitest` directly, never treat a policy skip as green evidence, and do not run unforced broad suites per commit; deliberate broad runs (`TT_FORCE=1 just check-code`, `TT_FORCE=1 just test-fast`, `just test-full`) execute where explicitly specified below.
- **Physical worktree `cwd` for `atoms` durability:** Run every `just test-one`, `TT_FORCE=1 just test-fast`, and `just test-full` command from the worktree's resolved physical directory (`cd "$(pwd -P)"` from `.worktrees/0f5112-test-latency`, using its literal resolved path in shell commands), never through the `.worktrees/` symlink, which causes `atoms`'s `open_root` to fail with `ELOOP`. Show paths to the user relative to the main checkout (`.worktrees/0f5112-test-latency/...`).
- **No machine-layout strings in tracked files:** Never write a literal hostname, home directory, expanded `WORK_ROOT`, or checkout path into any tracked source, test, spec, plan, or results document (`tools/ops-check` fails on machine layout). Use `$WORK_ROOT/beliefs/beliefs-0f5112` in prose and shell snippets.
- **Zero cross-call environment caching:** Never memoize or cache `capture_closure()`, `capture_environment()`, `require_executing_environment()`, `_file_digest()`, or `os.path.realpath()` across walks. Every `_Closure` state structure is initialized fresh in `_Closure.__init__`.
- **No copying of `.metadata`-bearing writable roots:** Copy only metadata-less export directories (`shutil.copytree(exported.export_root, work / "copy", symlinks=True)`) per test; shared registered roots (`exported_publication`, `readonly_source`) are strictly read-only.
- **No `sys.modules["conftest"]` import coupling:** Because collecting `tests/acceptance/...` loads `tests/acceptance/conftest.py` into `sys.modules["conftest"]`, neither `test_session_sharing_doors.py` nor `test_session_publish_door.py` may write `from conftest import ...` (both consume `certified_work_dir()` through `conftest.py` pytest fixtures `certified_module_work` and `certified_work_factory`), and `tests/test_fixture_grouping.py` (which executes `from conftest import pytest_collection_modifyitems`) must never run in the same `just test-one` invocation as `tests/acceptance/...`.
- **Exact `RAW_WRITE_ALLOWLIST` preservation in `adapter.py`:** `RAW_WRITE_ALLOWLIST["adapter.py"]` is `{"copy2"}`. Because `test_capability_boundary.names_of()` collects every bare `ast.Name`, `ast.Attribute` tail, and `ImportFrom` alias, **no new identifier in `BYTE_MUTATION_PRIMITIVES`** (`write_bytes`, `write_text`, `unlink`, `rmdir`, `rmtree`, `rename`, `symlink_to`, `chmod`, `touch`, `makedirs`, `remove`, `copy`, `copy2`, `copytree`, `move`) may appear anywhere in `python/src/beliefs/adapter.py` (not even `dict.copy()` or `set.remove()`).
- **Exact N2 `Sabotage.before` anchors in `python/src/beliefs/adapter.py`:** All five live/portable sabotage targets must remain unique with exact indentation and surrounding variable bindings:
  - `K7a` (`_Closure.add_native`, 20 spaces): `                    if known != canonical:`
  - `K7b` (`_Closure.add`, 12 spaces): `            if target_root is None:\n                raise ClosureUnsupported(f"symlink {located} -> {target!r} escapes the closure")` (with `target_root`, `located`, `target`, and `root` bound in scope so `after="            if target_root is None:\n                target_root = root"` executes cleanly)
  - `K7c` (`_Closure.add_pth`, 12 spaces): `            if imports and paths:`
  - `R13` (`capture_bundle`, 12 spaces): `            rows.append((name, _file_digest(target)))`
  - `R17` (`build_argv`, 8 spaces): `        if target.startswith("-"):`
- **Cross-module imported symbols and guarded nodeids:**
  - Preserve `modules`, `relative`, `parsed`, `names_of`, and `imported_modules` in `python/tests/test_capability_boundary.py` (imported by `tests/acceptance/test_durable_corpus.py`).
  - Preserve `_written` and `publishing_session` signatures and top-level `def test_y17_w_scoped_ownership` in `python/tests/test_session_publish_door.py` (consumed by `tests/acceptance/test_owned_replica_publication_acceptance.py` and `tests/n2_arms_cut47.py` / `tests/acceptance/test_n2_cut47.py`).
- **Non-cut status:** `AGENTS.md`'s two conformance-cut obligations (`root.py` `atoms`-importer additions and `test_recent_cut_acceptance.py` rows) do not add new entries because no conformance cut is discharged; `root.py` remains the sole `atoms` importer.
- **Subprocess and git hygiene:** Any test that spawns a subprocess builds its environment key by key (never `os.environ.copy()`). Use conventional commits with no AI attribution, trailers, or footers.

## Review Focus

1. **In-place byte mutation on disk between two `parsed(path)` calls in one worker (sabotage on `PYTHONPATH` or `tmp_path` reuse under `tmp_path_retention_policy=failed`):** `parsed(path)` must read current file bytes from disk on every call and recompute the AST whenever bytes or `str(path)` differ, while bounding retained entries at `maxsize=256` (Task 1: `test_parsed_recomputes_when_file_bytes_change_and_bounds_cache`).
2. **A setup-time exception inside a `certified_work_dir()` consumer (such as `CapabilityUnavailable` on an uncertified host):** `certified_work_dir()` must still evict `corpus` and `world_registry` entries under `work` and delete the directory, while `VERIFIABLY_UNCERTIFIED_HOST=1` still executes every portable test and skips only the 60 capability-dependent items (`38` in `test_session_sharing_doors.py` and `22` in `test_session_publish_door.py`) across both session-door modules with zero leaked directories (Task 2: `test_certified_work_dir_cleans_up_and_forgets_registries_on_exception` and Step 5 `VERIFIABLY_UNCERTIFIED_HOST=1` verification).
3. **Writes to `s.ops` or `s.dest` inside one of the 8 `readonly_source` items in `test_session_publish_door.py`:** `scoped_source(readonly_source, tmp_path)` must rebind `ops`, `dest`, and `destination` into per-test `tmp_path`, and `readonly_source` teardown must assert `_files(s.base) == before` byte for byte before cleanup (Task 2: `test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged` and `readonly_source` teardown assertion).
4. **Wheel `RECORD` entries traversing a symlinked distribution ancestor or `../` relative path, `.pth` suffixes vs a literal `".pth"` dotfile, and missing, directory, or `ELOOP` `RECORD` paths:** `_Closure.add_records()` must normalize `os.path.normpath(os.path.join(dist_base, raw_entry))` lexically before resolving parent symlinks via `_located` (matching `Path(os.path.normpath(str(dist.locate_file(entry))))`), skip `*.pth` suffixes while retaining `".pth"`, and raise `MalformedClosure` formatting `PurePosixPath(raw_entry)` on missing, `ELOOP`, or non-regular/non-symlink entries (Task 3: `test_add_records_resolves_symlinked_parents_relative_entries_pth_edges_and_refusals`).
5. **Symlinked directories, `.pyc`-named directories, unreadable subdirectories, and non-monotone custom `excluded` predicates in `_Closure.add_tree()`, plus ELF files hashed via `add()`, `add_records()`, or `add_native()`'s `SANDBOX_LIB` branch (including `18–19`-byte truncated ELF prefixes, foreign-endianness headers, and unhashed synthetic rows):** `add_tree()` must keep symlinked directories as symlink rows without recursing, prune directory recursion only on monotone directory names (`"site-packages"`/`"__pycache__"` for `_stdlib_excluded` and `".git"`/`"__pycache__"` for `_path_tree_excluded`, never `.pyc`-named directories), and fail closed by propagating `OSError` on unreadable subdirectories, while `elves()` must classify hashed files from retained headers (keyed by `_is_loadable_elf`'s 18-byte predicate so `18–19`-byte truncated ELFs still raise `struct.error` matching `probe.py`) without reopening them on disk and fall back to disk only for unhashed direct `rows`/`plan` insertions (Task 3: `test_add_tree_keeps_symlinked_dirs_as_links_prunes_known_exclusions_and_preserves_custom_predicates` and `test_elves_reuses_hashed_headers_across_add_records_and_native_libs_without_reopening`).

---

### Task 1: Execution setup, focused baseline, and byte-keyed AST caching

**Files:**
- Modify: `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:5`
- Modify: `python/tests/test_capability_boundary.py:18-28,90-96,541-637`
- Test: `python/tests/test_capability_boundary.py`

**Interfaces:**
- Preserves in `python/tests/test_capability_boundary.py`: `modules() -> list[Path]`, `relative(path: Path) -> str`, `parsed(path: Path) -> ast.Module`, `names_of(tree: ast.Module, *, exclude_stdlib_copy: bool = False) -> set[str]`, `defined_names(tree: ast.Module) -> set[str]`, `imported_modules(tree: ast.Module) -> set[str]`.
- Produces in `python/tests/test_capability_boundary.py`: `@functools.lru_cache(maxsize=256) def _parsed_bytes(raw: bytes, filename: str) -> ast.Module` (retains ~`63 MiB` of `ast.Module` trees across the package's `116` modules in the `xdist` worker running `test_capability_boundary.py`, and `0 MiB` in workers that do not collect/execute it).

- [ ] **Step 1: Verify worktree state, scratch manifest, and focused policy-off baseline**

From the physical worktree directory (`cd "$(pwd -P)"` inside `.worktrees/0f5112-test-latency`), confirm `git status --porcelain` is empty, verify `$WORK_ROOT/beliefs/beliefs-0f5112` matches the latest pinned scratch manifest on `beliefs-0f5112` (`tasks/files/beliefs-0f5112/scratch-manifest-v2.json` or newer), start the Task 1 step record, and run the focused baseline across all target test modules:

Run: `just test-one tests/test_capability_boundary.py tests/test_session_sharing_doors.py tests/test_session_publish_door.py tests/test_closure_capture.py tests/test_adapter.py tests/test_confinement.py tests/test_arm_staleness.py`
Expected: PASS (0 failures). Record a task note on `beliefs-0f5112` naming the command, passed count, recorded `tt` seconds, and the deliberate omission of the broad baseline under `.tt.toml` (`automatic_broad = false`).

- [ ] **Step 2: Write the failing AST cache regression test (Review Focus 1)**

Add `test_parsed_recomputes_when_file_bytes_change_and_bounds_cache(tmp_path: Path)` to `python/tests/test_capability_boundary.py`:

```python
def test_parsed_recomputes_when_file_bytes_change_and_bounds_cache(tmp_path: Path):
    _parsed_bytes.cache_clear()
    try:
        first = tmp_path / "first.py"
        second = tmp_path / "second.py"
        first.write_text("VALUE = 1\n", encoding="utf-8")
        second.write_text("VALUE = 1\n", encoding="utf-8")

        tree_a = parsed(first)
        info_after_first = _parsed_bytes.cache_info()
        assert parsed(first) is tree_a
        assert _parsed_bytes.cache_info().hits == info_after_first.hits + 1

        tree_b = parsed(second)
        assert tree_b is not tree_a
        assert _parsed_bytes.cache_info().misses == info_after_first.misses + 1

        first.write_text("VALUE = 2\n", encoding="utf-8")
        updated = parsed(first)
        assert updated is not tree_a
        assign = updated.body[0]
        assert isinstance(assign, ast.Assign) and isinstance(assign.value, ast.Constant)
        assert assign.value.value == 2

        for index in range(260):
            extra = tmp_path / f"m_{index}.py"
            extra.write_text(f"X = {index}\n", encoding="utf-8")
            parsed(extra)
        bounded = _parsed_bytes.cache_info()
        assert (bounded.currsize, bounded.maxsize) == (256, 256)
        parsed(second)
        assert _parsed_bytes.cache_info().misses == bounded.misses + 1
    finally:
        _parsed_bytes.cache_clear()
```

- [ ] **Step 3: Run the new test to verify RED**

Run: `just test-one tests/test_capability_boundary.py::test_parsed_recomputes_when_file_bytes_change_and_bounds_cache`
Expected: FAIL with `NameError: name '_parsed_bytes' is not defined`.

- [ ] **Step 4: Implement `_parsed_bytes`, hoist per-module name sets, and update spec status**

In `python/tests/test_capability_boundary.py`:
- Import `functools` and define `@functools.lru_cache(maxsize=256) def _parsed_bytes(raw: bytes, filename: str) -> ast.Module: return ast.parse(raw.decode("utf-8"), filename=filename)`.
- Update `parsed(path: Path) -> ast.Module` to `return _parsed_bytes(path.read_bytes(), str(path))`.
- In `test_no_cooperative_mutation_path_skips_registration`, precompute `non_root_names = [(relative(module), names_of(parsed(module))) for module in modules() if relative(module) != COMPOSITION_ROOT]` once before the `for command in MUTATING_ENGINE_COMMANDS:` loop and build `elsewhere = [rel for rel, used in non_root_names if command in used]`.
- In `test_science_fingerprints_only_through_the_engine_read_commands`, precompute `non_root_vocab = [(relative(module), names_of(tree) | defined_names(tree)) for module in modules() if relative(module) != COMPOSITION_ROOT for tree in (parsed(module),)]` once before `for name in STATE_VOCABULARY:` and build `elsewhere = [rel for rel, vocab in non_root_vocab if name in vocab]`.
- Update line 5 of `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md` to `**Status:** approved design (revised after spec round 1 b033606; round 2 accepted fb26beb; approved by user in round 3)`.

- [ ] **Step 5: Run focused tests and hygiene to verify GREEN and tail-pole removal**

Run: `just test-one tests/test_capability_boundary.py tests/acceptance/test_durable_corpus.py && just check-hygiene`
Expected: All tests PASS, `test_capability_boundary.py` completes in under 3 seconds (down from `30.78 s` worker time / `21.81 s` single-test pole), and `just check-hygiene` exits 0.

- [ ] **Step 6: Commit Task 1 and close its step record**

```bash
git add docs/superpowers/specs/2026-11-01-test-fast-latency-design.md python/tests/test_capability_boundary.py
git commit -m "perf(tests): cache capability-boundary ASTs by raw bytes and hoist scans"
```

---

### Task 2: Certified directory helper and module-scoped session-door fixtures

**Files:**
- Modify: `python/tests/conftest.py:10-20,151-175`
- Modify: `python/tests/test_session_sharing_doors.py:14-35,73-91,134-653`
- Modify: `python/tests/test_session_publish_door.py:94-153,394-420,504-540`
- Test: `python/tests/test_session_sharing_doors.py`, `python/tests/test_session_publish_door.py`

**Interfaces:**
- Produces in `python/tests/conftest.py`:
  - `@contextmanager def certified_work_dir() -> Iterator[Path]` (wraps `yield work` in `try: ... finally:` calling `corpus._forget_roots_under(work)`, `world_registry._forget_worlds_under(work)`, and `shutil.rmtree(work, ignore_errors=True)`).
  - `@pytest.fixture() def certified_work() -> Iterator[Path]` (`with certified_work_dir() as work: yield work`).
  - `@pytest.fixture(scope="module") def certified_module_work() -> Iterator[Path]` (`with certified_work_dir() as work: yield work`).
  - `@pytest.fixture() def certified_work_factory() -> Callable[[], AbstractContextManager[Path]]` (`return certified_work_dir`).
- Produces in `python/tests/test_session_sharing_doors.py`:
  - `@pytest.fixture(scope="module") def exported_publication(certified_module_work: Path) -> SimpleNamespace` yielding `SimpleNamespace(export_root=..., cid=..., sibling=..., other_sibling=..., evidence=..., observers=...)` (omitting `s`).
  - `def shared(work: Path, exported: SimpleNamespace, *, required: RequiredCapabilities = SHARING) -> SimpleNamespace` and `def adopted(work: Path, exported: SimpleNamespace) -> SimpleNamespace`.
- Produces in `python/tests/test_session_publish_door.py`:
  - `@pytest.fixture(scope="module") def readonly_source(certified_module_work: Path) -> Iterator[SimpleNamespace]` (snapshots `before = _files(s.base)`, yields `s`, asserts `_files(s.base) == before` at teardown).
  - `def scoped_source(source: SimpleNamespace, tmp_path: Path) -> SimpleNamespace` (creates `ops = tmp_path / "ops"` and `dest = tmp_path / "dest"` with `ops.mkdir(parents=True, exist_ok=True)` and `dest.mkdir(parents=True, exist_ok=True)`, and returns a shallow `SimpleNamespace` copy with `ops`, `dest`, and `destination = Destination.local(str(dest))` rebound).
  - Preserves exact signatures of `publishing_session` and `_written` and top-level `def test_y17_w_scoped_ownership`.

- [ ] **Step 1: Start Task 2 step record and write the failing portable tests (Review Focus 2 & 3)**

Add `test_certified_work_dir_cleans_up_and_forgets_registries_on_exception` to `python/tests/test_session_sharing_doors.py` (taking `(certified_work_factory, tmp_path, monkeypatch)` and neither `certified_work` nor `exported_publication`):

```python
def test_certified_work_dir_cleans_up_and_forgets_registries_on_exception(
    certified_work_factory, tmp_path, monkeypatch
):
    import beliefs.world.registry as world_registry
    from beliefs import corpus

    vol = tmp_path / "vol"
    monkeypatch.setenv("SCIENCE_CUT10_ROOT", str(vol))
    forgotten_corpora: list[Path] = []
    forgotten_worlds: list[Path] = []
    real_forget_corpora = corpus._forget_roots_under
    real_forget_worlds = world_registry._forget_worlds_under
    monkeypatch.setattr(
        corpus, "_forget_roots_under", lambda p: (forgotten_corpora.append(p), real_forget_corpora(p))[1]
    )
    monkeypatch.setattr(
        world_registry, "_forget_worlds_under", lambda p: (forgotten_worlds.append(p), real_forget_worlds(p))[1]
    )
    created: Path | None = None
    with pytest.raises(RuntimeError, match="setup-boom"):
        with certified_work_factory() as work:
            created = work
            (work / "sentinel").write_bytes(b"x")
            raise RuntimeError("setup-boom")
    assert created is not None and not created.exists()
    assert forgotten_corpora == [created]
    assert forgotten_worlds == [created]
```

Add `test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged(tmp_path: Path)` to `python/tests/test_session_publish_door.py`:

```python
def test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged(tmp_path: Path):
    base = tmp_path / "readonly"
    (base / "alpha").mkdir(parents=True)
    (base / "ops").mkdir()
    (base / "dest").mkdir()
    (base / "alpha" / "record.md").write_bytes(b"immutable")
    source = SimpleNamespace(
        base=base,
        alpha_id="a" * 32,
        ops=base / "ops",
        dest=base / "dest",
        destination=Destination.local(str(base / "dest")),
    )
    before = _files(base)
    scoped = scoped_source(source, tmp_path / "per-test")
    assert scoped.alpha_id == source.alpha_id and scoped.base == base
    assert scoped.ops != source.ops and scoped.ops.is_dir()
    assert scoped.dest != source.dest and scoped.dest.is_dir()
    assert scoped.destination == Destination.local(str(scoped.dest))
    (scoped.ops / "publish").mkdir()
    (scoped.dest / "artifact").write_bytes(b"scratch")
    assert _files(base) == before
```

- [ ] **Step 2: Run the two new portable tests to verify RED**

Run: `just test-one tests/test_session_sharing_doors.py::test_certified_work_dir_cleans_up_and_forgets_registries_on_exception tests/test_session_publish_door.py::test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged`
Expected: FAIL (`fixture 'certified_work_factory' not found` and `NameError: name 'scoped_source' is not defined`).

- [ ] **Step 3: Implement `certified_work_dir()`, `exported_publication`, and `readonly_source` + `scoped_source`**

1. In `python/tests/conftest.py`, implement `certified_work_dir()`, `certified_work`, `certified_module_work`, and `certified_work_factory` per the Interfaces block above.
2. In `python/tests/test_session_sharing_doors.py`:
   - Add `shutil` import (removing unused `metadata_less_copy` import if no longer called).
   - Define `@pytest.fixture(scope="module") def exported_publication(certified_module_work: Path) -> SimpleNamespace` that builds `s = published_source(certified_module_work)`, `published = publish_locally(s)`, `export_root = s.dest / published.corpus_id`, `sibling = (s.dest / f"{published.corpus_id}.head-artifact.v1").read_bytes()`, `other_dest = s.base / "dest-other"` (`other_dest.mkdir()`, `other = publish_locally(s, destination=Destination.local(str(other_dest)))`, `assert other.corpus_id != published.corpus_id`, `other_sibling = (other_dest / f"{other.corpus_id}.head-artifact.v1").read_bytes()`), and returns `SimpleNamespace(export_root=export_root, cid=published.corpus_id, sibling=sibling, other_sibling=other_sibling, evidence=evidence_for(published, sibling, s), observers=ObserverSet((ArtifactCarrier.from_bytes(sibling),)))`.
   - Update `shared(work: Path, exported: SimpleNamespace, *, required: RequiredCapabilities = SHARING) -> SimpleNamespace` to copy `shutil.copytree(exported.export_root, work / "copy", symlinks=True)`, resolve `copy = (work / "copy").resolve()`, open `session, writer = recipient_session(work, required=required)`, and return `SimpleNamespace(cid=exported.cid, copy=copy, sibling=exported.sibling, other_sibling=exported.other_sibling, evidence=exported.evidence, observers=exported.observers, session=session, writer=writer)`.
   - Update `adopted(work: Path, exported: SimpleNamespace) -> SimpleNamespace` and pass `exported_publication` in all 25 capability-dependent test functions (38 pytest items, using `x.other_sibling` directly in `test_the_artifact_binding_searches_every_carrier`), keeping the 3 portable tests (`test_sharing_evidence_disagrees_is_a_write_refusal_naming_its_field`, `test_a_session_without_a_world_configuration_refuses_admit_publication_and_retire`, `test_certified_work_dir_cleans_up_and_forgets_registries_on_exception`) free of `certified_work` and `exported_publication`.
3. In `python/tests/test_session_publish_door.py`:
   - Define `@pytest.fixture(scope="module") def readonly_source(certified_module_work: Path) -> Iterator[SimpleNamespace]` (`s = published_source(certified_module_work); before = _files(s.base); yield s; assert _files(s.base) == before`) and `def scoped_source(source: SimpleNamespace, tmp_path: Path) -> SimpleNamespace` creating `ops = tmp_path / "ops"` and `dest = tmp_path / "dest"` (`ops.mkdir(parents=True, exist_ok=True)`, `dest.mkdir(parents=True, exist_ok=True)`).
   - Route ONLY the 8 strictly non-mutating items through `s = scoped_source(readonly_source, tmp_path)` (closing opened sessions in `try / finally` so session handles do not outlive the test):
     - `test_the_preview_needs_no_authority(readonly_source, tmp_path)`
     - `test_a_coordination_scoped_writer_refuses_the_permit_before_the_world_is_opened(readonly_source, tmp_path, monkeypatch)`
     - `test_a_session_without_a_resolver_refuses_coordination_unavailable(readonly_source, tmp_path)`
     - `test_y17_w_scoped_ownership(readonly_source, tmp_path, monkeypatch, scenario)` (remaining a top-level `def`)
   - Keep all 14 mutating `certified_work` items (across 11 test functions) on per-test `certified_work`.

- [ ] **Step 4: Run focused certified tests and acceptance/N2 callers to verify GREEN**

Run: `just test-one tests/test_session_sharing_doors.py tests/test_session_publish_door.py tests/test_fixture_grouping.py && just test-one tests/acceptance/test_owned_replica_publication_acceptance.py tests/acceptance/test_n2_cut47.py`
Expected: All tests PASS, `readonly_source` teardown byte-invariance holds, and `test_session_sharing_doors.py` completes in under 25 seconds (down from `175.41 s` worker time).

- [ ] **Step 5: Verify `VERIFIABLY_UNCERTIFIED_HOST=1` skip partition and zero leaked directories (Review Focus 2)**

Run: `uncer_tmp=$(mktemp -d /tmp/uncer-XXXXXX) && VERIFIABLY_UNCERTIFIED_HOST=1 SCIENCE_CUT10_ROOT="$uncer_tmp" just test-one -rs tests/test_session_sharing_doors.py tests/test_session_publish_door.py && rmdir "$uncer_tmp" && just check-hygiene`
Expected: `6 passed, 60 skipped` (3 portable passed + 38 skipped in `test_session_sharing_doors.py`; 3 portable passed + 22 skipped [8 `readonly_source` + 14 mutating `certified_work`] in `test_session_publish_door.py`), every skip reason starts with `certified tuple unavailable on this host:`, `rmdir "$uncer_tmp"` exits 0 (confirming zero leaked `t-*` directories after setup `CapabilityUnavailable`), and `just check-hygiene` exits 0.

- [ ] **Step 6: Commit Task 2 and close its step record**

```bash
git add python/tests/conftest.py python/tests/test_session_sharing_doors.py python/tests/test_session_publish_door.py
git commit -m "perf(tests): share read-only session-door source worlds at module scope"
```

---

### Task 3: Zero-cache single-walk closure cleanup in adapter.py

**Files:**
- Modify: `python/src/beliefs/adapter.py:5-25,245-503`
- Modify: `python/tests/test_closure_capture.py`
- Test: `python/tests/test_closure_capture.py`

**Interfaces:**
- Preserves in `python/src/beliefs/adapter.py`: `_Closure` (`rows`, `plan`, `rendered`, `loader_map`, `loader_elves`, `native_arch`, `register`, `root_of`, `sandbox_of`, `add`, `add_chain`, `check_links`, `add_tree`, `add_records`, `add_pth`, `add_native`, `elves`), `_is_loadable_elf(path: Path) -> bool`, `_elf_architecture(path: Path) -> tuple[int, int, int]`, `capture_closure() -> CapturedEnvironment`, `capture_environment() -> EnvironmentManifest`, `require_executing_environment(manifest: EnvironmentManifest | EnvironmentReference) -> None`.
- Preserves `RAW_WRITE_ALLOWLIST["adapter.py"] == {"copy2"}` and all five exact `Sabotage.before` anchors (`K7a`, `K7b`, `K7c`, `R13`, `R17`).

- [ ] **Step 1: Start Task 3 step record, snapshot baseline `capture_closure()`, and write the failing and pinning `_Closure` regression tests (Review Focus 4 & 5)**

First, before modifying `python/src/beliefs/adapter.py` (confirming `git diff 240a989 -- python/src/` is empty), dump a canonical JSON snapshot of `capture_closure()` in the worktree's `.venv` to `$WORK_ROOT/beliefs/beliefs-0f5112/closure-baseline-240a989.json` recording `manifest.artifacts`, `rendered`, `loader`, `interpreter`, `loader_map`, `loader_elves`, and `sorted((k, str(v)) for k, v in plan.items())`, and print its SHA-256 digest so Step 4 proves zero-row, zero-field drift against `240a989`.

Then add four tests to `python/tests/test_closure_capture.py`:
1. `test_elves_reuses_hashed_headers_across_add_records_and_native_libs_without_reopening(tmp_path, monkeypatch)`:
   - Register `site = tmp_path / "site"` at `SANDBOX_SITE` and set `walker.native_arch = (_NATIVE_CLASS, _NATIVE_DATA, _NATIVE_MACHINE)`.
   - Add `(site / "mod.py")` (`b"X = 1\n"`) and `(site / "direct.so")` (`LOADABLE_ELF`) via `walker.add(...)`.
   - Create a synthetic distribution double returning `RECORD` lines for `rec_native.so` (`LOADABLE_ELF`), `rec_foreign_endian.so` (20-byte ELF header with `EI_DATA` flipped to `2 if _NATIVE_DATA == 1 else 1`, `<H` `3` at offset 16 so it enters `_loadable_elf_headers`, and flipped-endian `e_machine` at offset 18 so `elves()` rejects it), and `short17.bin` (17-byte truncated `LOADABLE_ELF[:17]` so `<18`-byte files do not match `_is_loadable_elf` in either baseline or candidate and Step 2 RED reaches `elves()` without premature `struct.error`), monkeypatch `importlib.metadata.distributions` to `lambda: (dist,)`, and call `walker.add_records()`.
   - Create `outside = tmp_path / "outside"` with `(outside / "libext.so.1")` (`LOADABLE_ELF`) and call `walker.add_native(listing=lambda elf: {"libext.so.1": outside / "libext.so.1"} if elf.name == "direct.so" else {})`.
   - Monkeypatch `adapter_module._is_loadable_elf` and `adapter_module._elf_architecture` to raise `AssertionError("reopened already-hashed file")` and assert `walker.elves()` returns `[("/science/env/lib/libext.so.1", ...), ("/science/env/site/direct.so", ...), ("/science/env/site/rec_native.so", ...)]`.
   - Undo the monkeypatch, insert a direct unhashed synthetic row `walker.rows[f"{SANDBOX_SITE}/manual.so"] = ("file", "sha256:" + "00" * 32)` with `walker.plan[f"{SANDBOX_SITE}/manual.so"] = manual_path` (`LOADABLE_ELF`), and assert `f"{SANDBOX_SITE}/manual.so"` is included via the disk-read fallback.
   - On a separate `_Closure` registered at `tmp_path / "short19_site"`, add a 19-byte truncated loadable-ELF prefix (`short19.bin = LOADABLE_ELF[:19]`, which passes `_is_loadable_elf`'s 18-byte check) and assert `with pytest.raises(struct.error): walker19.elves()`, preserving exact parity with `adapter._is_loadable_elf` + `_elf_architecture` and `probe.py:84-99`.
2. `test_add_tree_keeps_symlinked_dirs_as_links_prunes_known_exclusions_and_preserves_custom_predicates(tmp_path, monkeypatch)`:
   - Create `site / "real_dir" / "inside.py"`, `site / "dir_link"` (symlink to `"real_dir"`), `site / "top.pyc"` (`b"compiled"`), `site / "dir.pyc" / "inner.py"` (`b"X = 1\n"`), `site / "site-packages" / "pkg" / "skip.py"`, and `site / "__pycache__" / "skip.cpython-313.pyc"`.
   - Wrap `os.scandir` to record every scanned directory path (normalized via `os.path.realpath`), run `walker.add_tree(site, excluded=adapter_module._stdlib_excluded)`, and assert positive control `{os.path.realpath(site), os.path.realpath(site / "real_dir"), os.path.realpath(site / "dir.pyc")} <= scanned` (so Step 2 RED fails deterministically on Python 3.13 where `Path.rglob` calls `0` module-level `os.scandir`), `os.path.realpath(site / "site-packages") not in scanned`, `os.path.realpath(site / "__pycache__") not in scanned`, `f"{SANDBOX_SITE}/top.pyc"` is NOT in `walker.rows`, `f"{SANDBOX_SITE}/dir.pyc/inner.py"` IS in `walker.rows` (proving `.pyc`-named directories are never falsely pruned), `walker.rows[f"{SANDBOX_SITE}/dir_link"] == ("symlink", "real_dir")`, and `f"{SANDBOX_SITE}/dir_link/inside.py"` is NOT in `walker.rows` while `f"{SANDBOX_SITE}/real_dir/inside.py"` IS in `walker.rows`.
   - On a fresh `_Closure`, create `site2 / "pkg" / "sub" / "keep.py"` and run `walker2.add_tree(site2, excluded=lambda parts: parts == ("pkg",))`; assert `f"{SANDBOX_SITE}/pkg/sub/keep.py"` IS in `walker2.rows` (proving non-monotone custom predicates are not falsely pruned).
   - Also verify deliberate fail-closed unreadable-directory propagation: monkeypatch `os.scandir` to raise `PermissionError("locked subdir")` on `site2 / "pkg"` and assert `walker3.add_tree(site2, excluded=adapter_module._stdlib_excluded)` raises `PermissionError` (which `capture_closure()` wraps as `ClosureUnsupported`, rather than silently skipping unreadable subdirectories as `Path.rglob` did).
3. `test_add_records_resolves_symlinked_parents_relative_entries_pth_edges_and_refusals(tmp_path, monkeypatch)`:
   - Register `real_venv = tmp_path / "real_venv"` (`SANDBOX_VENV`) with `(real_venv / "bin" / "tool")` and `real_site = real_venv / "lib" / "site-packages"` (`SANDBOX_SITE`), plus both a leaf symlink `alias_site = tmp_path / "alias_site" -> real_site` and an ancestor venv symlink `alias_venv = tmp_path / "alias_venv" -> real_venv`.
   - Build two distribution doubles: `dist_leaf` whose `locate_file("")` returns `alias_site` (with `RECORD` listing `pkg/mod.py,sha256:...,1`, `pkg/link.py,sha256:...,1` [symlink to `mod.py`], `.pth,sha256:...,1` [literal dotfile], `ignored.pth,sha256:...,1` [skipped `.pth` suffix], and `pkg/__pycache__/mod.cpython-313.pyc,,` [skipped cache]), and `dist_rel` whose `locate_file("")` returns `alias_venv / "lib" / "site-packages"` (with `RECORD` listing `../../bin/tool,sha256:...,1`, whose lexical `os.path.normpath` resolves to `alias_venv / "bin" / "tool"` and whose `_located` parent resolves `alias_venv / "bin"` -> `real_venv / "bin"` in `SANDBOX_VENV`). Assert `add_records()` captures `pkg/mod.py`, `pkg/link.py`, `.pth`, and `/science/env/venv/bin/tool`, and skips `ignored.pth` and `.pyc`.
   - Also pin lexical-`normpath` parity when `../` crosses a leaf symlink: a distribution at `alias_site` listing `../../bin/tool,sha256:...,1` normalizes lexically to `tmp_path.parent / "bin" / "tool"` before `_located` (matching `Path(os.path.normpath(str(dist.locate_file(entry))))`) and raises `MalformedClosure`.
   - Verify `add_records()` raises `MalformedClosure` matching `r"RECORD lists a/missing\.py and no such file exists"` across three sub-cases that each list `"a/missing.py"` in `RECORD`: (a) absent `a/missing.py`, (b) directory `(site / "a" / "missing.py").mkdir(parents=True)`, and (c) parent-directory symlink loop `(site / "a").symlink_to("a")` (so `os.lstat(".../a/missing.py")` raises `OSError(errno.ELOOP)` and `_lstat_mode` returns `None`).
4. `test_root_matching_handles_double_slashes_and_walks_observe_live_mutations(tmp_path)`:
   - Verify `walker.root_of(Path(f"//{purelib.as_posix().lstrip('/')}/mod.py")) == (Path(os.path.realpath(purelib)), SANDBOX_SITE)` and `sandbox_of` returns `f"{SANDBOX_SITE}/mod.py"`.
   - Mutate a tracked file in a two-walk `_Closure` sequence over the same path and assert the two walks record distinct `"sha256:..."` digests with zero cross-walk caching.

- [ ] **Step 2: Run the new tests to verify RED**

Run: `just test-one tests/test_closure_capture.py -k "reuses_hashed_headers or prunes_known_exclusions"`
Expected: FAIL (`AssertionError: reopened already-hashed file` in `elves()`, and the positive-control `scanned` assertion failing against `set()` in `test_add_tree_...` because Python 3.13's `Path.rglob` calls `0` module-level `os.scandir`).

- [ ] **Step 3: Implement the five zero-cache per-walk optimizations in `python/src/beliefs/adapter.py`**

Import `errno` and `stat`, and update `_Closure` in `python/src/beliefs/adapter.py` (using zero identifiers from `BYTE_MUTATION_PRIMITIVES` and keeping all five `Sabotage.before` anchors exact and unique):
1. **Root table & string-prefix matching:** Store `self._roots: list[tuple[str, str, Path, str]] = []` (`(real_str, prefix_str, Path(real_str), sandbox_root)` with `prefix_str = "/" if real_str == "/" else f"{real_str}{os.sep}"`, sorted descending by `len(real_str)`). Add `_normalize_path_str(raw: str) -> str` calling `os.path.normpath(raw)` and collapsing POSIX leading `"//"` (`if norm.startswith("//") and not norm.startswith("///"): norm = norm[1:]`). Use string-prefix matching (`located_str == real_str or located_str.startswith(prefix_str)`) in `root_of` and `sandbox_of`, computing `relative = "." if located_str == real_str else located_str[len(prefix_str):].replace(os.sep, "/")` so `f"{sandbox_root}/{relative}"` matches `os.path.relpath(located, host_root)` at both the root itself and descendants.
2. **String-keyed parent `realpath` & single `os.lstat`:** Replace `_parent_locations` with `dict[str, str]` in `_located_str(self, host_str: str) -> str` (`parent_str, tail = os.path.split(host_str)` -> cache `os.path.realpath(parent_str or ".")` -> `os.path.join(real_parent, tail)` when `tail` is non-empty, else `real_parent`), with `_located(self, host: Path) -> Path` returning `Path(self._located_str(os.fspath(host)))`. Add `_lstat_mode(path_str: str) -> int | None` returning `os.lstat(path_str).st_mode` and returning `None` only on `errno.ENOENT`, `errno.ENOTDIR`, `errno.EBADF`, `errno.ELOOP` (propagating `EACCES`/`EIO`). Keep `K7b`'s exact 12-space block and `target_root`, `located`, `target`, `root` bindings in `_Closure.add`.
3. **Directory-pruned `os.scandir` in `add_tree`:** Recursively scan directories using `with os.scandir(current_dir) as scan: entries = sorted(scan, key=lambda e: e.name)` so directory file descriptors close immediately even on error, deliberately letting `os.scandir` propagate `OSError` (`PermissionError`, `EIO`) rather than swallowing it (so `capture_closure()` fails closed with `ClosureUnsupported` on unreadable subdirectories). Check `entry.is_symlink()` and `entry.is_file(follow_symlinks=False)` before `entry.is_dir(follow_symlinks=False)`: pass symlinks and regular files to `self.add(Path(entry.path))` whenever `not excluded(rel_parts)`, and when recursing into non-symlink directories (`entry.is_dir(follow_symlinks=False)`), prune directory recursion **only on monotone directory names** (`entry.name in ("site-packages", "__pycache__")` when `excluded is _stdlib_excluded`; `entry.name in (".git", "__pycache__")` when `excluded is _path_tree_excluded`; never prune `.pyc`-named directories or custom `excluded` predicates).
4. **Low-allocation parent-resolved `add_records`:** Compute `dist_base = os.fspath(dist.locate_file(""))` once per distribution; filter `raw_entry` strings directly (`stripped = raw_entry.rstrip("/")`, `basename = stripped.rsplit("/", 1)[-1]`, skipping `("__pycache__" in stripped and "__pycache__" in stripped.split("/"))` or `basename.endswith(".pyc")` or `(basename.endswith(".pth") and basename != ".pth")`); resolve `located_str = self._located_str(os.path.normpath(os.path.join(dist_base, raw_entry)))`; call `mode = _lstat_mode(located_str)`; raise `MalformedClosure(f"distribution {name!r}: RECORD lists {PurePosixPath(raw_entry)} and no such file exists")` when `mode is None` or neither `stat.S_ISREG(mode)` nor `stat.S_ISLNK(mode)` (importing `PurePosixPath` from `pathlib`); record regular files directly via `_record_regular_file` when `stat.S_ISREG(mode)` (skipping if `sandbox in self.rows`) and delegate symlinks (`stat.S_ISLNK(mode)`) to `self.add(Path(located_str))`.
5. **Shared regular-file hashing & ELF header retention:** Add per-walk `self._hashed_files: set[str] = set()` and `self._loadable_elf_headers: dict[str, bytes] = {}` plus `_record_regular_file(self, sandbox: str, located_path: Path) -> None` reading `data = located_path.read_bytes()` once, storing `self.rows[sandbox] = ("file", "sha256:" + sha256(data).hexdigest())`, `self.plan[sandbox] = located_path`, adding `sandbox` to `self._hashed_files`, and storing `self._loadable_elf_headers[sandbox] = data[:20]` whenever `len(data) >= 18 and data[:4] == _ELF_MAGIC and struct.unpack_from("<H", data, 16)[0] in (2, 3)` (matching `_is_loadable_elf` and `probe.py:84-88`, so `18–19`-byte truncated loadable-ELF prefixes still raise `struct.error` when `elves()` unpacks offset 18). Use `_record_regular_file` in `add()`, `add_records()`, and `add_native()`'s `else:` branch (`resolved = f"{SANDBOX_LIB}/{soname}"`, guarded by `if resolved not in self.rows:`, keeping `K7a` at exact 20-space indent above it). In `elves()`, classify any `path in self._hashed_files` from `self._loadable_elf_headers.get(path)` using `EI_DATA` endianness (`"<"` if `header[5] == 1 else ">"`) at offset 18, falling back to `_is_loadable_elf(self.plan[path])` and `_elf_architecture(self.plan[path])` only when `path not in self._hashed_files`.

- [ ] **Step 4: Run focused closure, confinement, boundary, N2-cut13, Python 3.11, live-closure parity, and code checks to verify GREEN**

1. Run: `just test-one tests/test_closure_capture.py tests/test_adapter.py tests/test_confinement.py tests/test_arm_staleness.py tests/test_capability_boundary.py && just test-one tests/acceptance/test_n2_cut13.py && just check-hygiene && TT_FORCE=1 just check-code`
   Expected: All tests PASS (including live `K7a`/`K7b`/`K7c` sabotage kills in `test_n2_cut13.py`, uniqueness checks in `test_arm_staleness.py`, and `RAW_WRITE_ALLOWLIST` in `test_capability_boundary.py`), and both `check-hygiene` and `check-code` exit 0.
2. Dump the candidate `capture_closure()` snapshot in the same `.venv` to `$WORK_ROOT/beliefs/beliefs-0f5112/closure-candidate.json`, assert **exact byte-for-byte / SHA-256 equality** against `$WORK_ROOT/beliefs/beliefs-0f5112/closure-baseline-240a989.json` across `manifest.artifacts`, `rendered`, `loader`, `interpreter`, `loader_map`, `loader_elves`, and `plan`, and confirm unprofiled single-walk latency drops well below `0.60 s` (vs `1.507 s` baseline).
3. Verify Python 3.11 compatibility locally through `just test-one` in an isolated temporary `UV_PROJECT_ENVIRONMENT` (leaving `python/.venv` on Python 3.13 untouched):
   `py311_env=$(mktemp -d /tmp/0f5112-py311-XXXXXX) && UV_PYTHON=3.11 UV_PROJECT_ENVIRONMENT="$py311_env" just test-one tests/test_closure_capture.py tests/test_adapter.py tests/test_confinement.py tests/test_capability_boundary.py tests/test_session_sharing_doors.py tests/test_session_publish_door.py; rc=$?; rm -rf "$py311_env"; test $rc -eq 0`

- [ ] **Step 5: Commit Task 3 and close its step record**

```bash
git add python/src/beliefs/adapter.py python/tests/test_closure_capture.py
git commit -m "perf(adapter): cut single-walk closure stat, path, tree, and ELF churn"
```

---

### Task 4: Paired 16-worker benchmark, certified full suite, and results record

**Files:**
- Create: `docs/plans/2026-11-01-test-fast-latency-results.md`
- Modify: `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:5`
- Test: `python/tests/test_check_guide.py`, `python/tests/test_front_door.py`, `python/tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: committed Tasks 1–3 candidate on `perf/0f5112-test-latency`, baseline commit `240a989` (`git merge-base main perf/0f5112-test-latency`), baseline diagnostic `$WORK_ROOT/beliefs/beliefs-0f5112/diag-attribution.json` (`1,381.43 s` worker time, `96.428 s` `tt`), and Task 3 closure parity snapshots `$WORK_ROOT/beliefs/beliefs-0f5112/closure-baseline-240a989.json` and `$WORK_ROOT/beliefs/beliefs-0f5112/closure-candidate.json`.
- Produces: benchmark logs `bench-pilot.log`, `bench-B{1,2,3}.log`, `bench-C{1,2,3}.log`, `cand-durations.log`, `cand-attribution.json`, and `test-full.log` in `$WORK_ROOT/beliefs/beliefs-0f5112/`, plus committed results record `docs/plans/2026-11-01-test-fast-latency-results.md`.

- [ ] **Step 1: Start Task 4 step record and run the 16-worker candidate pilot**

From the physical worktree directory (`cd "$(pwd -P)"` on clean `perf/0f5112-test-latency`), inspect `host-budget show` and `host-load --section load`, then run one unprofiled 16-worker pilot:

Run: `TT_FORCE=1 just test-fast 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-0f5112/bench-pilot.log"`
Expected: `6,410 passed, 1 skipped` (6,403 baseline + 7 new regression tests across Tasks 1–3), affected TypeScript green, observed 16-worker grant, `dirty: false` in the recorded `tt` row, and `tt` `seconds <= 90.0`. If host load refuses a 16-worker grant (or before any conditional park in Task 4), record the refusal note, attach a fresh immutable scratch manifest covering any new or modified files in `$WORK_ROOT/beliefs/beliefs-0f5112/` with updated `retained:` and `retention checkpoint:` notes (`--stamp`, recording `observer session attribution unknown` when no `harness_session` stamp is emitted) whenever scratch contents changed since the last checkpoint, and park `--reason quiet --waiting-on user --minutes 25`.

- [ ] **Step 2: Execute the six-run alternating clean-tree benchmark (`B1, C1, B2, C2, B3, C3`)**

Run all three consecutive alternating pairs (`i = 1, 2, 3`, ~10 min total) inside **one single tracked shell script invocation** in the physical worktree directory with a timeout of at least 15–20 minutes (`run_in_background` with `timeout >= 1200000` in Claude Code, or one single tracked script invocation in harnesses with reactive task wakeup — never separate shell calls that lose the `trap` and can leave the worktree detached, and never detached `&`/`nohup`), guarded by `set -euo pipefail` and `trap 'git checkout perf/0f5112-test-latency' EXIT INT TERM`:
- Baseline `B_i`: `git checkout --detach 240a989`, confirm `git status --porcelain` is empty, sample `host-load --section load`, run `TT_FORCE=1 just test-fast 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-0f5112/bench-B${i}.log"`, sample `host-load --section load`, and read the latest `tt` `test-fast` row (`rev` starting `240a989`, `dirty == false`, `6,403` passed / `1` skipped, 16 workers). Do not run `tasks` writes while detached.
- Candidate `C_i`: `git checkout perf/0f5112-test-latency`, confirm `git status --porcelain` is empty, sample `host-load --section load`, run `TT_FORCE=1 just test-fast 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-0f5112/bench-C${i}.log"`, sample `host-load --section load`, and read the latest `tt` `test-fast` row (`dirty == false`, `6,410` passed / `1` skipped, 16 workers).
- If host load shifts materially within a pair or `OPS_WORKERS` drops below 16, invalidate and repeat that entire pair (retaining the invalidated logs and noting why before reading the replacement pair). Never drop a valid slow run.

- [ ] **Step 3: Evaluate the four keep-or-revert gates and run `--durations=0` candidate attribution**

1. Verify all four retention criteria on recorded `tt` wall seconds:
   - Full correctness (`6,403` passed / `1` skipped on every `B_i`; `6,410` passed / `1` skipped on every `C_i`; affected TypeScript exit 0).
   - `median(C1, C2, C3) <= 90.0`.
   - `D_i = B_i - C_i > 0` for `i = 1, 2, 3`.
   - `median(D1, D2, D3) > max(max(B1, B2, B3) - min(B1, B2, B3), max(C1, C2, C3) - min(C1, C2, C3))`.
2. Run one candidate attribution pass outside the six-run decision:
   `TT_FORCE=1 PYTEST_ADDOPTS="--durations=0" just test-fast 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-0f5112/cand-durations.log"`
   Aggregate per-module setup+call+teardown worker seconds into `$WORK_ROOT/beliefs/beliefs-0f5112/cand-attribution.json` and confirm each of Part 1A (`test_session_sharing_doors.py`), Part 1B (`test_session_publish_door.py`), Part 1C (`test_capability_boundary.py`), and Part 2 (workflow/closure modules) achieved real worker-time reductions vs `diag-attribution.json` (`1,381.43 s`).
   - If an individual part shows zero worker-time gain while the remaining parts still plausibly meet `<= 90.0 s`, revert only that unproven commit on `perf/0f5112-test-latency` (`git revert --no-edit <part-sha>`), re-verify focused tests + `just check-hygiene` + `TT_FORCE=1 just check-code`, and **rerun the full six-run alternating `B1..C3` benchmark and `--durations=0` attribution** on the trimmed branch before proceeding to Step 4.
   - If any keep gate still fails (`median(C1..C3) > 90.0`, non-positive `D_i`, or `median(D) <= noise`), ensure `perf/0f5112-test-latency` is checked out, record the measured numbers and residual bottleneck on `beliefs-0f5112`, attach a fresh immutable scratch manifest + updated `retained:` (`next_owner: "task:beliefs-0f5112"`) + `retention checkpoint:` (`--stamp`) notes, and run `tasks park beliefs-0f5112 "User decides whether to widen optimization scope (e.g., fixture-scoped Snakemake closure reuse) or retire beliefs-0f5112 under .tt.toml policy-off given measured B1..C3 results" --waiting-on user --reason decision`.

- [ ] **Step 4: Run the complete certified `just test-full` suite (`<= 300 s`)**

Run: `just test-full 2>&1 | tee "$WORK_ROOT/beliefs/beliefs-0f5112/test-full.log"`
Expected: Exit 0 across all three phases (non-N2 Python `6,410` passed / `1` skipped, standalone portable N2 `46` passed, full TypeScript `155` passed), recorded `tt` `test` row with `execution == "ran"`, `execution_reason == "forced"`, and `seconds <= 300.0`.

- [ ] **Step 5: Write `docs/plans/2026-11-01-test-fast-latency-results.md` and update spec status**

Create `docs/plans/2026-11-01-test-fast-latency-results.md` (containing zero machine-layout strings: refer to `the incident host`, `.worktrees/0f5112-test-latency`, and `$WORK_ROOT/beliefs/beliefs-0f5112`) documenting:
- Summary of Part 1 and Part 2 changes (including the ~`63 MiB` single-worker AST cache footprint across `116` modules and `add_tree()`'s deliberate fail-closed `OSError` propagation on unreadable subdirectories), RED/GREEN regression tests, `6 passed, 60 skipped` uncertified-host skip-partition check, local Python 3.11 focused verification, exact `capture_closure()` before/after snapshot SHA-256 parity digest and row counts, and single-walk `capture_closure()` timing.
- Six-run alternating `B1..C3` table (`tt` seconds, paired deltas `B_i - C_i`, medians, baseline/candidate ranges, noise-gate threshold, and **keep** verdict).
- Baseline (`240a989`, `1,381.43 s`) vs candidate `--durations=0` worker-time attribution table across the top modules.
- Complete certified `just test-full` result (`<= 300 s`, counts per phase).
- Policy-off and hosted-CI closeout record citing `.tt.toml` activation at `01eb638191bd44fe9bd2a715fcc7d6853b07cc6e` (`beliefs-067a8d`), why `tt-latency verify` reports disabled `test-fast` as `not applicable`, and that local merge to `main` without pushing leaves hosted GitHub Actions CI (`Python 3.11/3.13`, `Node 20/24`) pending the next user-approved push.
Update line 5 of `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md` to `**Status:** implemented and benchmark-verified; awaiting whole-branch review and local integration`.

- [ ] **Step 6: Run hygiene, code checks, and doc-sensitive focused tests, then commit Task 4**

Run: `just check-hygiene && TT_FORCE=1 just check-code && just test-one tests/test_check_guide.py tests/test_front_door.py tests/test_ci_workflow.py`
Expected: All checks and tests exit 0 (`ops-check` confirms zero machine-layout or broken-reference findings in the new results record).

```bash
git add docs/plans/2026-11-01-test-fast-latency-results.md docs/superpowers/specs/2026-11-01-test-fast-latency-design.md
git commit -m "docs(plans): record test-fast latency benchmark and full-suite results"
```

---

### Task 5: Whole-branch review, local integration, and policy-off closeout

**Files:**
- Modify: `docs/plans/2026-11-01-test-fast-latency-results.md`
- Modify: `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:5`

**Interfaces:**
- Consumes: committed Tasks 1–4 branch `perf/0f5112-test-latency` and benchmark/full-suite logs in `$WORK_ROOT/beliefs/beliefs-0f5112/`.
- Produces: accepted whole-branch review record, local merge of `perf/0f5112-test-latency` into `main` (no push), `tt-report` timing harvest, complete retained-item release/checkpoint accounting, and closed task records.

- [ ] **Step 1: Start Task 5 step record and run fresh read-only whole-branch review**

Dispatch a fresh read-only reviewer subagent over `main..perf/0f5112-test-latency` against the approved spec and plan (carrying the policy-off test rules and pointing to the committed results record). Before acting on the returned review:
- Record `review: impl round <n> — verdict: <revise|accept>; findings: <counts|none>; reviewer: <identity>` on `beliefs-0f5112`.
- Save the full review text to `$WORK_ROOT/beliefs/beliefs-0f5112/impl-round-<n>-report.md`.
If any Critical or Important finding is raised, fix it `RED -> GREEN` via `just test-one` + `just check-hygiene` + `TT_FORCE=1 just check-code` and run a fresh scoped re-review (up to five rounds); record any `Ruling:` or `minor (deferred)` entries in task notes and `docs/plans/2026-11-01-test-fast-latency-results.md`.

- [ ] **Step 2: Record review disposition, verify gates, and close Task 5 step record**

Update `docs/plans/2026-11-01-test-fast-latency-results.md` and line 5 of `docs/superpowers/specs/2026-11-01-test-fast-latency-design.md` (`implemented, benchmark-verified, and branch-reviewed`) with the whole-branch review outcome, run `just check-hygiene && TT_FORCE=1 just check-code`, commit `docs(plans): record whole-branch review acceptance for test-fast latency` if updated, and close the Task 5 step child (`tasks done <task5-id> "..."`). Confirm all five step children of `beliefs-0f5112` are `done`.

- [ ] **Step 3: Harvest timings, complete pre-close retention accounting, and close `beliefs-0f5112` on the branch**

Following `~/.agents/skills/references/retained-item-records.md`:
1. Run `tt-report --project beliefs` and `host-load --section session`.
2. Inventory the complete final contents of `$WORK_ROOT/beliefs/beliefs-0f5112/` into a final immutable scratch manifest attachment (`tasks attach beliefs-0f5112 /tmp/scratch-manifest-final.json --name scratch-manifest-final.json --caption "Final SHA-256 manifest of task scratch contents before closeout disposition"`, then remove `/tmp/scratch-manifest-final.json`) accounting for every prior manifest member (from `scratch-manifest-v1.json` onward) plus all Task 3–5 closure-parity (`closure-baseline-240a989.json`, `closure-candidate.json`), benchmark, attribution, full-suite, and review files. Attach the portable immutable artifacts needed on `beliefs-0f5112` (`cand-attribution.json` and review reports; `tools/ops-check` v16 admits verified ledger-backed `tasks attach` files, and if any needed file ever triggers a layout refusal, apply the raw-plus-portable fallback by preserving its exact raw bytes in `$WORK_ROOT/beliefs/beliefs-0f5112` under an explicit `kind: "evidence"`, `state: "kept"` record transferred to an open follow-up task and keeping the enclosing directory — because attaching a derivative never releases raw bytes). Verify `tasks show beliefs-0f5112` lists every attachment and SHA-256 digests match. Only when no file required the raw-plus-portable fallback and every member of `scratch-manifest-final.json` has a verified disposition (attached on `beliefs-0f5112`, or discarded as regenerable benchmark/profile/closure-snapshot logs summarized in committed `docs/plans/2026-11-01-test-fast-latency-results.md`), remove `$WORK_ROOT/beliefs/beliefs-0f5112` and write its `retained:` `state: "released"` JSON note (`verification: "verified"`, `next_owner: "none"`, `cleanup_trigger: "none"`, naming `scratch-manifest-final.json` and which members were attached vs discarded).
3. Because `tasks` skill §6 and `retained-item-records.md` §Who acts after done require committing `tasks done` on the feature branch *before* `git merge` brings the closed record into `main` (and `--stamp` emits no `harness_session` identity in this harness), do not invent a `session:` owner for `.worktrees/0f5112-test-latency`: file a small sibling cleanup task (`tasks add "Remove 0f5112 worktree after local main merge" --origin agent -p 2 --size xs --complexity low --process direct`), link `beliefs-0f5112` and `<cleanup-id>` bidirectionally with `tasks note` on both records (`retained-item-records.md` §Who acts after done), update `.worktrees/0f5112-test-latency`'s `retained:` JSON note to `next_owner: "task:<cleanup-id>"` with `cleanup_trigger: "Immediately after perf/0f5112-test-latency merges locally into main"`, verify the committed basis (`git log <basis>..HEAD -- tasks/beliefs-0f5112.md`), append `tasks note beliefs-0f5112 "retention checkpoint: ..." --stamp` (`kept verified 1, kept unknown 0, released 1` when scratch is released, or reflecting any retained raw-fallback evidence item) and inspect the stamp output (recording `observer session attribution unknown` explicitly when no `harness_session` stamp is emitted), and run `tasks done beliefs-0f5112 "..."` recording focused scope (including local Python 3.11 focused verification and `capture_closure()` parity SHA-256), mandatory checks, `TT_FORCE=1` paired `test-fast` medians and `just test-full` verdict, retired `tt-latency` obligation under `01eb638191bd44fe9bd2a715fcc7d6853b07cc6e`, observer attribution status, and pre-merge branch state (`perf/0f5112-test-latency` unmerged at Step 3 branch close, handed to `<cleanup-id>` for immediate Step 4 local merge into `main`; post-merge integration commit recorded via Step 4 lifecycle note on `main`).

- [ ] **Step 4: Locally merge into `main`, dispose of `.worktrees/0f5112-test-latency`, and record post-merge integration state**

1. From the main checkout, verify `git status --porcelain` is empty on both `main` and `.worktrees/0f5112-test-latency`, then merge locally (`git merge --no-edit perf/0f5112-test-latency`; do NOT push unless the user explicitly approves a push).
2. In `main`, claim `<cleanup-id>` (`tasks start <cleanup-id>`), verify every `retention checkpoint:` basis commit on `beliefs-0f5112` is reachable from `main` (`git merge-base --is-ancestor <basis-commit> main`), inspect `git -C .worktrees/0f5112-test-latency status --ignored --porcelain` (confirming only regenerable caches/venv/`node_modules` remain), check that no host pointer resolves into `.worktrees/0f5112-test-latency` (`readlink -f` across `~/bin/*`, `~/.local/bin/*`, `~/.config/systemd/user/*`), run `tt-report --project beliefs`, unlock and remove the worktree (`git worktree unlock .worktrees/0f5112-test-latency && git worktree remove .worktrees/0f5112-test-latency`), delete the merged local branch (`git branch -d perf/0f5112-test-latency`), and re-verify `git merge-base --is-ancestor <basis-commit> main` on `main`.
3. Record the verified `retained:` `state: "released"` note for `.worktrees/0f5112-test-latency` on `beliefs-0f5112` (and `<cleanup-id>`), append a post-merge lifecycle `tasks note beliefs-0f5112` (`retained-item-records.md`: closed records may receive lifecycle notes without reopening implementation) recording the exact `main` integration commit SHA, worktree removal and local branch `perf/0f5112-test-latency` deletion, verified basis ancestry on `main`, and unpushed `main` / hosted-CI (`Python 3.11/3.13`, `Node 20/24`) pending-push disclosure, verify zero kept items remain on any host (no empty checkpoint note per `retained-item-records.md`), run `just check-hygiene` and `host-load --section session` in `main`, and close `<cleanup-id>` (`tasks done <cleanup-id> "..."`).
