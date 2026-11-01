# Restore sub-90-second `test-fast` latency across session-door fixtures, static boundary scans, and single-walk closure capture

**Date:** 2026-11-01  
**Task:** `beliefs-0f5112` (`test-latency`, `testing`)  
**Status:** proposed design (awaiting spec review)  
**Workspace:** `.worktrees/0f5112-test-latency` (`perf/0f5112-test-latency`)

## Intent and scope

Restore a repeatable `TT_FORCE=1 just test-fast` wall-time median of at most 90
seconds on the incident host while preserving every existing test, assertion,
skip rule, frozen-pin check, static boundary invariant, and runtime closure
guarantee. This slice introduces no product feature or schema change and
discharges no conformance-cut guarantee row.

### Recorded origin and designer's scope call

`beliefs-0f5112` was filed automatically by `tt-latency` (`2026-11-01T10:00:05Z`)
when `test-fast`'s trailing seven-day median reached **91.312 seconds** over 11
successful, uncontended, unwidened runs across three days against a 90-second
limit. The task record is authoritative for the incident host's identity.

While `beliefs-0f5112` was parked on a three-way scope question, concurrent
adoption task `beliefs-067a8d` activated `.tt.toml` (`automatic_broad = false`,
with `test-fast` in `broad_targets`) on `main` at merge
`01eb638191bd44fe9bd2a715fcc7d6853b07cc6e` (`2026-11-01T11:25:32Z`), noted that
the incident's `tt-latency` obligation for `test-fast` is retired from that
revision, and removed only the task's `halt` tag. The user opened this work with
`"Let's take beliefs-0f5112"` and then reported `"beliefs-067a8d is now done."`
without overriding the recommended Option A.

- **Designer's call — proceed on Option A (runtime reduction under policy-off):**
  Keep `beliefs-0f5112` to design and prove a real sub-90-second reduction on
  `TT_FORCE=1 just test-fast`. Even with automatic local broad runs disabled by
  `.tt.toml`, `AGENTS.md` designates `TT_FORCE=1 just test-fast` as the
  approximately 90-second local certified-tuple capability sweep whenever a
  change's capability reach is unclear, `just hook-pre-push-fast` (`test-push`)
  runs the same non-N2 Python suite before non-CI-covered pushes or fast hook
  checks, and hosted `just ci-python` runs the portable subset on every branch
  push. If the user instead prefers Option B (closing `beliefs-0f5112` as
  `policy-retired` with no code change), declining this spec at the spec gate
  selects that path before any product or test code is edited.
- **Closeout mechanics under policy-off:** Because `test-fast` is a disabled
  broad target in `.tt.toml`, `tt-latency verify beliefs-0f5112` reports the
  obligation as `not applicable` and never exits zero. Under the policy-off test
  rules, disabled `tt-latency` obligations remain not applicable rather than
  `tt-latency`-verified; Option A proves its runtime reduction through three
  alternating warm baseline/candidate pairs (`B1, C1, B2, C2, B3, C3`) of
  `TT_FORCE=1 just test-fast` at a 16-worker grant plus a complete certified
  `just test-full` run, recorded in
  `docs/plans/2026-11-01-test-fast-latency-results.md` and the task record.

## Evidence

Since `beliefs-ce9d05` closed on `2026-10-18` with a `68.671 s` post-merge
median across **6,119** non-N2 Python tests, **284** non-N2 tests landed
(**6,403** passed, **1** skipped at `240a989`). In the incident window's 11
eligible runs (`78.333 s` to `820.807 s`, median `91.312 s`), recent uncontended
runs over 6,385–6,403 tests took `99.46–103.73 s`.

One instrumented 16-worker diagnostic run on the unchanged task worktree at
`240a989` (`TT_FORCE=1 PYTEST_ADDOPTS="--durations=0" just test-fast`, host load
`15.56` before and `20.93` after, affected TypeScript selecting zero changed test
files) recorded:

| Measurement | `ce9d05` diagnostic (`77ce692`) | Current diagnostic (`240a989`) | Delta |
| --- | ---: | ---: | ---: |
| Non-N2 Python tests passed / skipped | 6,119 / 1 | 6,403 / 1 | +284 / 0 |
| Recorded `tt` wall time | 84.743 s | 96.428 s | +11.685 s |
| Pytest wall time | 82.54 s | 94.22 s | +11.68 s |
| Total setup + call + teardown across 16 workers | 993.25 s | 1,381.43 s | +388.18 s |

Top worker-time modules in the `240a989` diagnostic (`diag-attribution.json` in
persistent task storage `$WORK_ROOT/beliefs/beliefs-0f5112/`):

| Module | Worker time | `loadgroup` serial group | Notes |
| --- | ---: | ---: | --- |
| `tests/test_boundary.py` | 181.76 s | 8.90 s | Live workflow boundary and `capture_closure()` |
| `tests/test_session_sharing_doors.py` | 175.41 s | none | New since `ce9d05`; 37 `certified_work` items |
| `tests/test_replay.py` | 122.54 s | 24.78 s | Live workflow replay and `capture_closure()` |
| `tests/test_cut15_workflows.py` | 105.84 s | none | Multi-job workflow runs and `capture_closure()` |
| `tests/test_session_publish_door.py` | 80.77 s | none | New since `ce9d05`; 21 `certified_work` items |
| `tests/test_verify.py` | 70.36 s | 28.68 s | Workflow verification and `capture_closure()` |
| `tests/test_assess.py` | 65.49 s | 21.60 s | Workflow assessment and `capture_closure()` |
| `tests/test_run_persistence.py` | 44.62 s | none | Durable run persistence and `capture_closure()` |
| `tests/test_world_audit.py` | 39.50 s | none | Durable world audit |
| `tests/test_acceptance.py` | 31.30 s | none | Portable acceptance checks and `capture_closure()` |
| `tests/test_capability_boundary.py` | 30.78 s | none | `21.81 s` in one AST scan test; `4.63 s` in another |

Focused profiling isolated three concrete, independent sources of waste:

1. **Repeated durable source-world and export construction in the two new
   session-door modules (`256.18 s` combined worker time):**
   - Under `cProfile` (`sharing.prof`), one `test_session_sharing_doors.py` test
     (`test_restore_root_grants_read_serviceability_and_ledgers_fetched_validated`,
     `5.325 s` profiled) spends **`5.291 s` (`99.4%`)** inside
     `shared(certified_work)`: `published_source` takes `3.511 s` (`hold_shipped`
     `1.475 s`, `build_epoch` `1.140 s`, `_corpus` `0.590 s`, executing 29
     durable `atoms` transactions and 786 `fsync` calls), `publish_locally` takes
     `1.544 s`, and `metadata_less_copy` plus `recipient_session` take `0.236 s`.
     The `restore_root` door under test takes **`0.034 s`**. All 37
     `certified_work` items rebuild that identical source world and local
     publication from scratch solely to act on a fresh metadata-less copy and a
     fresh recipient session.
   - In `test_session_publish_door.py` (`80.77 s` across 21 `certified_work`
     items), 8 items inspect `publication_preview` or preflight session refusals
     without writing a byte to the source corpora or source world, yet each
     rebuilds `published_source` (`~3.5 s` per item).
2. **Repeated full-package AST parsing and traversal in
   `test_capability_boundary.py` (`30.78 s` worker time, `21.81 s` single-test
   pole):**
   - `test_science_fingerprints_only_through_the_engine_read_commands` loops over
     10 `STATE_VOCABULARY` names and, for every non-`root.py` module in
     `beliefs`, evaluates `names_of(parsed(module)) | defined_names(parsed(module))`
     — re-reading and `ast.parse`-ing the entire package from disk ~20 times
     (~2,000 `ast.parse` calls) in a single test, creating a `21.81 s` tail pole.
     `test_no_cooperative_mutation_path_skips_registration` (`4.63 s`) and the
     module's parametrized classes parse the same unchanged module bytes hundreds
     of additional times per worker.
3. **Single-walk Python object and syscall overhead in
   `beliefs.adapter._Closure` (`666.66 s` worker time across workflow and
   closure modules):**
   - Under `cProfile` (`boundary.prof`, two `test_boundary.py` tests executing 4
     `_walk_closure()` calls in `15.884 s`), `_walk_closure()` took **`11.509 s`
     (`72.5%`, `2.877 s` per profiled walk)**; an unprofiled single-core
     `capture_closure()` call takes **`1.507 s`** over `8,476` manifest rows,
     `27` loadable ELFs, and `75` loader-map entries.
   - Actual SHA-256 content hashing (`_file_digest`, `1.284 s` / 4 walks) and
     `ld.so --list` subprocesses (`loader_listing`, `0.121 s` / 4 walks) account
     for only **`12.2%`** of `_walk_closure()`. The remaining **`87.8%`** is
     per-walk mechanical churn:
     - `add_records()` outside `add()` (`2.95 s` / 4 walks): constructs
       `importlib.metadata.PackagePath` plus intermediate `Path` objects, calls
       `dist.locate_file(entry)`, and runs `is_file()`/`is_symlink()` across
       `7,526` wheel `RECORD` rows before `add()` repeats the same path and stat
       work (`dist.locate_file("")` joined with `row[0]` matches
       `dist.locate_file(PackagePath(row[0]))` with **0 mismatches** across all
       `7,526` rows);
     - `sandbox_of()` and `root_of()` (`1.847 s` / 4 walks): call
       `os.path.commonpath` and `os.path.relpath` ~17,000 times per walk on roots
       already resolved via `os.path.realpath`;
     - `elves()` (`1.491 s` / 4 walks): re-opens every `"file"` row on disk
       (`open` + `read(18)` + `close`, plus `read(20)` for ELFs) across multiple
       `while pending:` fixpoint iterations, including ~8,400 `.py` and metadata
       files whose full bytes `_file_digest` just read;
     - `_located()`, `add()`, and `add_tree()` (`1.47+ s` / 4 walks): allocate
       `host.parent` `Path` keys per file, issue separate `is_symlink()` and
       `is_file()` syscalls where one `os.lstat` suffices, and enumerate `8,848`
       `rglob("*")` entries under `platstdlib` (`.venv/lib/python3.13`), `98%`
       of which lie inside the excluded `site-packages/` directory.

## Goals, non-goals, and anti-goals

### Goals

- Bring `TT_FORCE=1 just test-fast` to a repeatable 16-worker `tt` wall-time
  median of **at most 90 seconds** on the incident host, targeting **62–72
  seconds** (`~450–520` worker-seconds removed) so normal host load variance
  cannot push routine sweeps back over 90 seconds.
- Eliminate the `21.81 s` single-test AST tail pole in
  `test_capability_boundary.py`.
- Preserve 100% of test coverage, failure diagnostics, and certified vs
  uncertified-host execution semantics.

### Non-goals

- Discharging any conformance cut or modifying any product domain contract,
  manifest format (`science.environment.v2`), or public API signature.
- Changing `.tt.toml`, `latency.toml` thresholds, `pytest-xdist` `--dist
  loadgroup` scheduling, or `host-budget` worker allocation.
- Editing any frozen-pinned conformance module or frozen cut document.

### Anti-goals

- **No cross-call environment observation cache:** Never memoize or cache
  `capture_closure()`, `capture_environment()`, `require_executing_environment()`,
  `_file_digest()`, or `os.path.realpath()` across walks. Every closure capture
  must observe live filesystem mutations made earlier in the same process
  (`beliefs-ce9d05` design §Scope and alternatives).
- **No copying of `.metadata`-bearing writable roots:** `atoms` binds registered
  roots' `.metadata` SQLite siblings to exact host paths and inodes; cloning a
  registered root with `.metadata` triggers `RESTORED_BACKUP` / lifecycle
  refusals. Only metadata-less export directories may be copied per test, and
  shared registered roots may only be read without mutation.
- **No path-only AST cache:** Caching `ast.Module` by `Path` without reading
  current file bytes from disk would mask N2 sabotage mutations on `PYTHONPATH`
  and `tmp_path` reuse under `tmp_path_retention_policy=failed`.
- **No shifted CI skip partition:** Portable tests in
  `test_session_sharing_doors.py` and `test_session_publish_door.py` must remain
  independent of certified-volume fixtures so `VERIFIABLY_UNCERTIFIED_HOST=1`
  continues to execute portable tests and convert only capability-dependent tests
  into `certified tuple unavailable on this host:` skips.

## Constraints

- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`), and **`RAW_WRITE_ALLOWLIST` is
  checked for exact set equality** (`test_no_cooperative_mutation_path_skips_registration`).
  `RAW_WRITE_ALLOWLIST["adapter.py"]` is `{"copy2"}`. Because `names_of()` scans
  every bare `ast.Name`, `ast.Attribute` tail, and `ImportFrom` alias in a
  module, **no new identifier in `BYTE_MUTATION_PRIMITIVES`** (`write_bytes`,
  `write_text`, `unlink`, `rmdir`, `rmtree`, `rename`, `symlink_to`, `chmod`,
  `touch`, `makedirs`, `remove`, `copy`, `copy2`, `copytree`, `move`) may appear
  anywhere in `python/src/beliefs/adapter.py` — not even as a `dict.copy()` or
  `set.remove()` method call or local variable name (apart from the existing
  `shutil.copy2` and stdlib `import copy` carve-out).
- **N2 and acceptance imports from `test_capability_boundary.py`:**
  `tests/acceptance/test_durable_corpus.py` imports `imported_modules`,
  `modules`, `names_of`, `parsed`, and `relative` from
  `test_capability_boundary`, and N2 cut-4 and cut-8 sabotage arms invoke
  `test_capability_boundary.py` tests against mutated package copies on
  `PYTHONPATH`. All five helper signatures and behaviors must remain intact.
- **Synthetic `_Closure` unit tests in `test_closure_capture.py`:** Tests
  construct `_Closure()` directly and call `register`, `add`, `add_chain`,
  `add_tree` (including custom `excluded=lambda parts: ...` callables),
  `add_pth`, `add_native(listing=...)`, and `check_links`, inspecting `rows`,
  `plan`, `rendered`, `loader_map`, and `loader_elves`. All existing methods,
  attributes, traversal orders, and `ClosureUnsupported` / `MalformedClosure`
  refusals must remain intact.
- **Test runner front door:** Every verification command runs through `just`
  (`just test-one`, `TT_FORCE=1 just test-fast`, `just test-full`,
  `just check-hygiene`, `TT_FORCE=1 just check-code`), never by calling `pytest`
  or `vitest` directly.

## Approaches considered

1. **Approach 1 — Test-machinery deduplication only** (`conftest.py`,
   `test_session_sharing_doors.py`, `test_session_publish_door.py`,
   `test_capability_boundary.py`):
   - *Pros:* Touches zero files under `python/src/beliefs/`; removes `~210`
     worker-seconds (`~158 s` in `test_session_sharing_doors.py`, `~25 s` in
     `test_session_publish_door.py`, `~28 s` in `test_capability_boundary.py`).
   - *Cons:* Reduces total worker time from `1,381 s` to `~1,170 s` (`~82–87 s`
     wall time at 16 workers). That leaves only `3–8 s` of margin below `90 s` —
     narrower than normal 3-run host variance (`5–10 s` in `ce9d05`), risking
     failure of the paired-range noise gate and immediate regression as new tests
     land.
2. **Approach 2 — Single-walk `beliefs.adapter._Closure` cleanup only**
   (`adapter.py` + `test_closure_capture.py`):
   - *Pros:* Cuts per-walk `_walk_closure()` overhead across every workflow test
     (`~260–310` worker-seconds saved across `test-fast`, plus `test-full` and
     CI).
   - *Cons:* Leaves `256 s` of redundant durable root setup in the two session
     door modules and leaves the `21.81 s` single-test AST tail pole in
     `test_capability_boundary.py`.
3. **Approach 3 (Selected — designer's call) — Combined two-part remedy (Part 1:
   test-machinery deduplication + Part 2: zero-cache single-walk `_Closure`
   cleanup):**
   - *Pros:* Removes both the new fixture/AST waste (`~210` worker-seconds) and
     the dominant single-walk Python/syscall churn (`~260–310` worker-seconds)
     without caching any environment observation across walks. Projected total
     savings of **`~470–520` worker-seconds** (`1,381 s -> ~860–910 s`, targeting
     **`62–72 s`** `tt` wall time) provide `18–28 s` of headroom below `90 s`
     and comfortably clear host noise.
   - *Cons:* Touches `python/src/beliefs/adapter.py` alongside three test
     modules, requiring direct single-walk equivalence tests and a full certified
     `just test-full` run (including N2 and TypeScript) in addition to the paired
     `test-fast` benchmark.

## Design

### Part 1 — Test-machinery deduplication

#### 1A. Certified directory helper and module-scoped exported publication in `test_session_sharing_doors.py`

1. In `python/tests/conftest.py`, factor a context-manager helper
   `certified_work_dir() -> Iterator[Path]` out of `certified_work` using the
   existing certified-volume base selection (`SCIENCE_CUT10_ROOT`,
   `SCIENCE_CUT12_ROOT`, `SCIENCE_CUT13_ROOT`, or
   `MAIN_CHECKOUT / ".lifecycle-wrappers-test"`). On exit, call
   `corpus._forget_roots_under(work)`,
   `world_registry._forget_worlds_under(work)`, and
   `shutil.rmtree(work, ignore_errors=True)` so long-lived worker processes do
   not retain evicted root paths in in-process registries. Keep the per-test
   `certified_work` fixture delegating directly to `certified_work_dir()`.
2. In `python/tests/test_session_sharing_doors.py`, add a `scope="module"`
   fixture `exported_publication` backed by `certified_work_dir()`:
   - Build `s = published_source(source_work)` and `published = publish_locally(s)`
     once per module.
   - Compute `sibling` bytes, `evidence = evidence_for(published, sibling, s)`,
     and `observers = ObserverSet((ArtifactCarrier.from_bytes(sibling),))`.
   - Export one secondary publication into `other_dest = s.base / "dest-other"`
     (`other = publish_locally(s, destination=Destination.local(str(other_dest)))`,
     asserting `other.corpus_id != published.corpus_id`) and capture
     `other_sibling` bytes once for
     `test_the_artifact_binding_searches_every_carrier`.
   - Yield a read-only namespace containing only `export_root = s.dest /
     published.corpus_id`, `cid = published.corpus_id`, `sibling`,
     `other_sibling`, `evidence`, and `observers` (omitting `s` so no test can
     mutate the shared source world).
3. Update `shared(work, exported, *, required=SHARING)` and `adopted(work,
   exported)` so each of the 37 `certified_work` items copies only the
   metadata-less export tree (`shutil.copytree(exported.export_root, work /
   "copy", symlinks=True)`) into its own fresh per-test `certified_work`
   directory and opens its own fresh `recipient_session(work,
   required=required)`.
4. Keep the two portable tests
   (`test_sharing_evidence_disagrees_is_a_write_refusal_naming_its_field` and
   `test_a_session_without_a_world_configuration_refuses_admit_publication_and_retire`)
   independent of `exported_publication`. Under `conftest.py`'s
   `pytest_collection_modifyitems` hook, the 37 `certified_work` items join
   `xdist_group("tests/test_session_sharing_doors.py")` on one worker (`~6.5 s`
   one-time export setup + `37 x ~0.30 s` recipient acts = `~17.6 s` group wall
   time, shorter than the existing `test_verify.py` `28.68 s`, `test_replay.py`
   `24.78 s`, and `test_assess.py` `21.60 s` groups), while on
   `VERIFIABLY_UNCERTIFIED_HOST=1` the two portable tests still pass and the 37
   capability-dependent items still skip via `pytest_runtest_setup`.

#### 1B. Module-scoped read-only source world for non-mutating items in `test_session_publish_door.py`

1. In `python/tests/test_session_publish_door.py`, add a `scope="module"`
   fixture `readonly_source` backed by `certified_work_dir()` that builds
   `s = published_source(work)` once, snapshots `before = _files(s.base)`, yields
   `s`, and asserts `_files(s.base) == before` before cleanup at teardown.
2. Route only the 8 strictly non-mutating test items through `readonly_source`,
   using a per-test `tmp_path` directory for `operations_root` (so
   `open_attended_session` writes its session ledger under `tmp_path / "ops" /
   "sessions-root"`, never under `readonly_source.base`, and closes the session
   in `try / finally`):
   - `test_the_preview_needs_no_authority`
   - `test_a_coordination_scoped_writer_refuses_the_permit_before_the_world_is_opened`
   - `test_a_session_without_a_resolver_refuses_coordination_unavailable`
   - `test_y17_w_scoped_ownership` (5 scenarios: `forward`, `closed`, `stale`,
     `permit`, `resolver`)
3. Keep all 13 mutating `certified_work` items (including
   `test_the_preview_refuses_as_publish_does`, whose `empty-selection` arm mints
   a coordination record, and
   `test_an_operations_root_inside_a_mount_is_unusable_from_the_act`, which
   creates `s.alpha / "ops"`) on per-test `certified_work` so they continue
   scheduling in parallel across all 16 workers outside the module's ~4-second
   `xdist_group`.

#### 1C. Byte-keyed bounded AST cache and outer-loop hoisting in `test_capability_boundary.py`

1. Keep `parsed(path: Path) -> ast.Module` reading `raw = path.read_bytes()`
   fresh from disk on every call and delegating to
   `@functools.lru_cache(maxsize=256) def _parsed_bytes(raw: bytes, filename:
   str) -> ast.Module: return ast.parse(raw.decode("utf-8"), filename=filename)`.
   - `maxsize=256` exceeds the package's ~100 Python files per worker while
     bounding memory.
   - Any byte edit on disk (N2 sabotage on `PYTHONPATH` or `tmp_path` reuse)
     produces different `raw` bytes and misses the cache.
   - `UnicodeDecodeError` and `SyntaxError` propagate identically to
     `path.read_text(encoding="utf-8")` + `ast.parse`.
   - Callers remain strictly read-only over returned `ast.Module` trees.
2. In `test_no_cooperative_mutation_path_skips_registration` and
   `test_science_fingerprints_only_through_the_engine_read_commands`, precompute
   per-module `names_of(tree)` and `names_of(tree) | defined_names(tree)` once
   per test call outside the `MUTATING_ENGINE_COMMANDS` and `STATE_VOCABULARY`
   loops, preserving identical `elsewhere` lists and assertion failure text.

### Part 2 — Zero-cache single-walk cleanup in `beliefs.adapter._Closure`

All state in `_Closure` remains strictly per-walk (`__init__` initializes fresh
instances on every `_walk_closure()` call; nothing is cached across calls).

1. **String-prefix root matching in `register`, `root_of`, and `sandbox_of`:**
   - Store `(real_str, prefix_str, Path(real_str), sandbox_root)` per registered
     root, where `real_str = os.path.realpath(host_root)` and `prefix_str` is
     `"/"` when `real_str == "/"` and `f"{real_str}{os.sep}"` otherwise, sorted
     descending by `len(real_str)`.
   - Match normalized path strings with `located_str == real_str or
     located_str.startswith(prefix_str)` and compute relative sandbox paths by
     string slicing (`"."` when `located_str == real_str`, else
     `located_str[len(prefix_str):]`, normalizing `os.sep` to `"/"` if needed)
     instead of calling `os.path.commonpath` and `os.path.relpath` per file. Keep
     `root_of(located: Path)` and `sandbox_of(located: Path)` accepting `Path`
     and normalizing `os.path.normpath(os.fspath(located))` so direct callers see
     identical behavior.
2. **String-keyed parent realpath lookup and single `os.lstat` per added entry:**
   - Replace `_parent_locations: dict[Path, Path]` with a per-walk string cache
     `dict[str, str]` keyed by `os.path.split(os.fspath(host))[0]`, resolving
     each parent directory via `os.path.realpath` once per walk without
     constructing intermediate `host.parent` `Path` objects on every file.
   - Inspect candidate paths with a single `os.lstat` (`stat.S_ISLNK` /
     `stat.S_ISREG`), avoiding separate `is_symlink()` and `is_file()` syscalls.
     Preserve exact refusal exceptions: `FileNotFoundError` / `NotADirectoryError`
     in `add()` raises `ClosureUnsupported(f"{located} is neither a regular file
     nor a symlink")`, while permission or I/O errors propagate as `OSError` for
     `capture_closure()` to wrap as `ClosureUnsupported`.
3. **Directory-pruned `os.scandir` traversal in `add_tree`:**
   - Traverse directories recursively with `os.scandir`, sorting entries by name
     at each level so rows enter `self.rows` in deterministic order.
   - When `excluded` is `_stdlib_excluded` or `_path_tree_excluded` (whose
     directory exclusions `"site-packages"`, `"__pycache__"`, and `".git"` are
     monotone over path prefixes), skip descending into excluded directories
     immediately rather than enumerating the `8,800+` files under
     `.venv/lib/python3.13/site-packages`. For any other caller-supplied
     `excluded` callable, test `excluded(rel_parts)` on every entry without
     pruning non-monotone predicates so custom predicates behave identically to
     `sorted(root.rglob("*"))`.
4. **Low-allocation `RECORD` scanning in `add_records`:**
   - Resolve `dist_base = os.fspath(dist.locate_file(""))` once per distribution
     instead of instantiating `importlib.metadata.PackagePath` and calling
     `dist.locate_file(entry)` across all `7,526` `RECORD` rows.
   - Apply `_distribution_cache` and `.pth` filtering directly on the `RECORD`
     path string (`stripped = raw_entry.rstrip("/")`, `basename =
     stripped.rsplit("/", 1)[-1]`, skipping when
     `("__pycache__" in stripped and "__pycache__" in stripped.split("/"))` or
     `basename.endswith(".pyc")` or
     `(basename.endswith(".pth") and basename != ".pth")`, matching
     `PurePosixPath.parts` and `PurePosixPath.suffix` edge cases including a
     literal `".pth"` dotfile).
   - Check `os.lstat(located_str)` once (`S_ISREG` or `S_ISLNK`), raising the
     exact `MalformedClosure(f"distribution {name!r}: RECORD lists {raw_entry}
     and no such file exists")` when absent or a directory, and pass the
     pre-stat'd file directly into `_Closure`'s row addition so `os.lstat` is not
     repeated.
5. **In-walk ELF header retention for `elves()`:**
   - When hashing a regular `"file"` row (`data = located.read_bytes()`), record
     its 20-byte prefix `data[:20]` in `self._elf_headers[sandbox]` whenever
     `data[:4] == _ELF_MAGIC`, and record `sandbox` in `self._hashed_files`.
   - In `elves()`, evaluate loadable ELF type (`ET_EXEC` / `ET_DYN`) and
     `(EI_CLASS, EI_DATA, e_machine)` architecture directly from
     `self._elf_headers` with zero extra `open`/`read`/`close` syscalls across
     fixpoint passes; if a `"file"` row in `self.rows` is not in
     `self._hashed_files` (for example, synthetic direct dict insertion in a
     test), fall back to `_is_loadable_elf(self.plan[path])` and
     `_elf_architecture(self.plan[path])`.

## What is left to the builder

- Exact internal helper names and private tuple/method signatures inside
  `python/src/beliefs/adapter.py`, `python/tests/conftest.py`,
  `python/tests/test_session_sharing_doors.py`,
  `python/tests/test_session_publish_door.py`, and
  `python/tests/test_capability_boundary.py`, subject to the identifier ban on
  `BYTE_MUTATION_PRIMITIVES` in `adapter.py` and the preserved public helper
  signatures in `test_capability_boundary.py` and `_Closure`.
- Task ordering across implementation commits (Part 1C, Part 1A/1B, Part 2, then
  paired benchmark and results record), provided every code change follows
  focused `RED -> GREEN` through `just test-one` and each part's focused speedup
  is verified before moving to the full paired sweep.

## Verification and keep-or-revert rule

1. **Focused `RED -> GREEN` regression tests (`just test-one`):**
   - `test_capability_boundary.py`: prove repeated `parsed(path)` calls on
     unchanged bytes hit `_parsed_bytes`, mutating the file's bytes on disk
     recomputes the AST, distinct paths do not collide, and `maxsize=256` bounds
     retained entries (`RED` before `_parsed_bytes`, `GREEN` after). Run the full
     `just test-one tests/test_capability_boundary.py`.
   - `test_session_sharing_doors.py` and `test_session_publish_door.py`: verify
     all existing tests pass with `exported_publication` and `readonly_source`,
     `readonly_source` detects zero file/byte mutations across all 8 read-only
     items, and `VERIFIABLY_UNCERTIFIED_HOST=1` still executes the portable tests
     while converting `CapabilityUnavailable` on capability-dependent items into
     `certified tuple unavailable on this host:` skips.
   - `test_closure_capture.py`, `test_adapter.py`, `test_confinement.py`, and
     `test_capability_boundary.py`: prove (a) file content or symlink changes
     between two `capture_closure()` calls in one process produce distinct
     manifests (no cross-call caching), (b) `elves()` does not re-open files
     hashed through `add()` (`RED` before Part 2E, `GREEN` after), (c) `.pth`
     suffix vs `".pth"` dotfile and missing/directory `RECORD` entries preserve
     exact `MalformedClosure` semantics, (d) `add_tree` pruning matches
     unpruned traversal and preserves custom non-monotone `excluded` callables,
     and (e) `adapter.py` still satisfies `RAW_WRITE_ALLOWLIST["adapter.py"] ==
     {"copy2"}`.
2. **Pilot before sweep:** Run one unprofiled 16-worker `TT_FORCE=1 just
   test-fast` pilot on the candidate to verify full non-N2 selection, zero
   regressions, and expected wall-time range before starting the six-run paired
   benchmark.
3. **Six-run alternating paired benchmark (`B1, C1, B2, C2, B3, C3`):**
   - Execute three consecutive alternating baseline (`240a989`) and candidate
     pairs of warm, unprofiled `TT_FORCE=1 just test-fast` runs on the incident
     host, each at an observed 16-worker grant (`OPS_WORKERS=16`).
   - Record `host-load` before and after every run, worker grant, selected /
     passed / skipped test counts, and `tt` `seconds`. If host load or background
     activity shifts materially within a pair or `OPS_WORKERS` drops below 16,
     discard and repeat that entire pair.
   - Run one `--durations=0` attribution pass on the candidate (`TT_FORCE=1
     PYTEST_ADDOPTS="--durations=0" just test-fast`) to compare total worker
     seconds and per-module timings against the `1,381.43 s` baseline diagnostic.
4. **Keep-or-revert gate (all four required to retain):**
   - Full correctness holds (`6,403 + N_new` passed, `1` skipped, affected
     TypeScript green).
   - `median(C1, C2, C3) <= 90.0 s`.
   - Every candidate beats its paired baseline: `B_i - C_i > 0` for `i = 1, 2, 3`.
   - Conservative noise gate:
     `median(B1 - C1, B2 - C2, B3 - C3) > max(max(B) - min(B), max(C) - min(C))`.
   - Also check each part's focused measurement so no zero-gain complexity is
     retained; if the keep-or-revert gate fails, revert the unproven change and
     record the measured residual.
5. **Hygiene, code checks, and certified full suite:**
   - Run `just check-hygiene` and `TT_FORCE=1 just check-code`.
   - Run one complete certified `just test-full` (non-N2 Python, standalone N2
     including cut-4 and cut-8 sabotage arms over `test_capability_boundary.py`,
     and full TypeScript suite) and verify it passes within the 300-second suite
     limit.
   - Commit the measured benchmark table, attribution comparison, and policy-off
     closeout evidence in `docs/plans/2026-11-01-test-fast-latency-results.md`.
