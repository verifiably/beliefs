# Session Mounts — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an attended session write one corpus while mounting every configured corpus, each under the profile its own manifest pins. Coordination then resolves over all of them. Reconciliation matches acts to chains by corpus, and cut 43 discharges J12–J15.

**Architecture:**
- `beliefs/mount.py` holds `compile_mount_profile`, which resolves a manifest's pins by namespace and content identity against the shipped packs and the caller's available documents.
- `open_attended_session` takes a required `write_root` and a `mounts` mapping, which replaces `coordination`, and builds its `CoordinationResolver` over every configured root.
- `session/reconcile.py` matches `(corpus_id, registration digest)` in both directions.
- Nothing else in the kernel changes: the resolver, the writer, the ledger and the publish act already take several mounts.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `atoms` engine behind `root.py`, `nodes` records, the acceptance harness and the N2 audit.

**Spec:** `docs/superpowers/specs/2026-09-27-session-mounts-design.md`, approved 2026-09-27 after two user reviews (its §12). Read it first.

## Global Constraints

- **Baseline is `design/session-mounts` at `ebba6eb`**, branched from `main` at `026f208`. Work in `.worktrees/session-mounts`, which is locked "on WORK_ROOT storage". Paths shown to the user carry the `.worktrees/session-mounts/` prefix. Run pytest from the canonical path (`cd "$(pwd -P)"`; memory `run-pytest-from-the-canonical-worktree-path`).
- **The cut is 43**, numbered after cut 42 (`beliefs-3ce305`, frozen on `design/publish`) under roadmap rule 1. Rule 5 then applies:
  - cut 43's runner chains `cut42_acceptance.py`;
  - its discharge waits for cut 42's merge;
  - Tasks 0–4 run now, and Task 5 starts by merging `main` once cut 42 has landed.

  Task 0 (`beliefs-8e46e1`) runs only after publish's Task 0 (`beliefs-64bb0e`) has frozen cut 42. That task's record lives on `design/publish`, where this branch's tracker cannot resolve it, so Step 1's scan enforces the order, not `tasks dep`. If the scan finds no cut 42 frozen anywhere, stop and ask. The number and the chain both change, and that is the user's sequencing call.
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  - For this lane, `mount.py` imports nothing of `atoms`, and the lane adds no caller of a write primitive (spec §8.4). Task 2 runs both inventories and `test_capability_boundary.py` green.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. Here that is Task 5, with `(cut43, 43, (9, 9, 4))`.
- **The declared accounting is 9 arms, 9 declaration units and 4 rows (J12–J15).** The spec's §8.3 names nine sabotages. Each gets its own unit: J12-a, J12-b and J12-c; J13-a and J13-b; J14-a; J15-a, J15-b and J15-c.
- **Frozen pins stay byte-exact.** Cut 19's live arms pin these lines, and each must still occur exactly once after this lane's edits:
  - `session/__init__.py`: `            chains[corpus_id] = log_seam().inspect_detached(root)`, `            stack.enter_context(_operation_lock_for(root))` and `    if type(view) is not WellFormedView:`;
  - `session/reconcile.py`: `                    if r.digest in acts:\n                        continue`, `                    if unknown:`, `            unknown = reader is None or bool(open_invocations)` and `            if staged not in digests:`.

  Only J9a's pin (`    if len(world_config.corpus_roots) != 1:`) disappears. It is re-targeted in `test_n2_cut19.py`'s `_LIVE_SABOTAGES` (Task 2). Tasks 2 and 3 end with `tests/test_arm_staleness.py`, and zero stale arms is the exit condition. A second stale arm is a finding against the spec (its §8.3), not a routine re-target.
- **Long runs are harness-tracked.** Run the cut runner and the gate through the Bash tool with `run_in_background: true`, piping through `tee` into `~/d/beliefs/.work/acceptance/cut43-*.log`. Never `setsid nohup`, `&` or `detached.sh` (memory `long-runs-are-harness-tracked`). If the harness kills a run at its background cap, park `--reason environment` and tell the user.
- **Commits:** conventional, with no attribution trailers; `tasks check` before each commit; `just test-fast` while working; `uv run --frozen` from `python/`; no TypeScript changes.

## Review Focus

1. **A `mounts` key given as a relative path, or through a symlink, for a configured root.** A person expects it to match the configured root after resolution. Pinned by `test_mount_keys_resolve_before_matching` in Task 2.
2. **A read mount pinning a domain contract the launcher did not make available.** A person expects the refusal to name the mount and the pin, so that they know which document to supply. Pinned by `test_an_unresolved_pin_names_root_namespace_and_pin` in Task 1.
3. **One document passed twice in `available`, or a shipped pack passed as available too.** A person expects no error and the same profile. Pinned by `test_duplicate_available_documents_are_harmless` in Task 1.
4. **A session with `mounts=None` over two roots.** A person expects it to open and write the write root, with coordination unavailable, as a one-root session without coordination does today. Pinned by `test_two_roots_without_mounts_open_without_coordination` in Task 2.
5. **An act line whose corpus is not configured in this world** (a ledger written under another configuration). A person expects no finding, since no chain here is truth for it, as today. Pinned by `test_an_act_naming_an_unconfigured_corpus_is_not_unverified` in Task 3.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-09-05-writer-session-design.md` | J12–J15 banked; the session-mounts amendment section (Tasks 0, 7) |
| `docs/designs/<freeze date>-conformance-cut-43.md` (new), `README.md`, the guide, `python/tests/test_designs_corpus.py`, the ledger, the roadmap | freeze and totals (Task 0) |
| `python/src/beliefs/mount.py` (new), `python/src/beliefs/errors.py`, `python/tests/test_mount.py` (new) | `compile_mount_profile`, `MountPinUnresolved` (Task 1) |
| `python/src/beliefs/session/__init__.py`; `python/tests/test_session_writer.py`, `test_session_routes.py`, `test_profile_agreement.py`, `acceptance/test_session_acceptance.py`, `acceptance/test_n2_cut19.py` | the new open, its callers, J9's case and J9a's re-target (Task 2) |
| `python/src/beliefs/session/reconcile.py`, `python/tests/test_session_reconcile.py` | corpus-matched reconciliation (Task 3) |
| `python/tests/acceptance/test_session_mounts_acceptance.py` (new) | J12, J14, J15-a (Task 4) |
| `python/tests/n2_arms_cut43.py`, `python/tests/acceptance/n2_arms_cut43.py`, `python/tests/acceptance/test_n2_cut43.py`, `python/tools/cut43_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declarations, guard, runner, recent-cut row (Task 5) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | the next addendum (Task 6) |
| `docs/plans/<date>-conformance-cut-43-results.md` (new) and the amended documents | discharge (Task 7) |

---

### Task 0: Freeze cut 43, bank J12–J15

**Files:**
- Create: `docs/designs/<freeze date>-conformance-cut-43.md`
- Modify: `docs/designs/2026-09-05-writer-session-design.md` (§7 table), `python/tests/test_designs_corpus.py`, `README.md`, `docs/guide/contracts-and-adoption.md`, the ledger, the roadmap (through `python/tools/roadmap_status.py`), the spec (planning notes), tasks

- [ ] **Step 1: Confirm cut 42 is frozen and 43 unclaimed**

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only $b docs/designs | grep -o "conformance-cut-4[2-9]" | sort -u | sed "s|^|$b: |"; done; echo scan done
```
Expected: `design/publish: conformance-cut-42` and no `-43` anywhere. Anything else means stop and ask (Global Constraints).

- [ ] **Step 2: Bank J12–J15.**
  - Append the four rows to the writer-session design's §7 table, byte for byte from the spec's §7 (`grep -n '^| \*\*J1[2-5]\*\*' docs/superpowers/specs/2026-09-27-session-mounts-design.md`). Put a one-line note above them: "J12–J15 banked with conformance cut 43's freeze (`../superpowers/specs/2026-09-27-session-mounts-design.md` §7); J9's two-root clause is superseded by J12."
  - In `test_designs_corpus.py`, change `range(1, 12)` to `range(1, 16)`.
  - Totals are taken from this branch's own tree. `cd python && uv run --frozen python tools/roadmap_status.py` prints `Closed X of Y`, and the new total is Y + 4. On a branch without cut 42's rows that is 231 → 235, with 204 of 235 closed. Cut 42's rows join at the Task 5 merge, and Task 7's re-rank reconciles the two (roadmap rule 2).
  - Update README, the guide's totals, the ledger (J12–J15 open under the new boundary `multi-corpus-session`) and the roadmap's accounting and Appendix A.

- [ ] **Step 3: Write the cut document** on cut 41's shape:
  - **Header:** `**Status:** frozen <date>, before implementation; J12–J15 are open`, the design and plan paths, and "Numbered after cut 42 (`design/publish`) under roadmap rule 1; its discharge serializes after cut 42's under rule 5."
  - **§1:** spec §1 condensed.
  - **§2, the boundary:** the file map's Tasks 1–5.
  - **§3, selection:** J12–J15 and the unit table (Task 5's).
  - **§4, accounting:** "**9 arms, 9 declaration units**, four rows; recent-cut row `(9, 9, 4)`", and the acceptance count that Task 4 declares: 13 test cases.
  - **§5, N2 and acceptance obligations:** the sabotage table from Task 5 Step 1; J9a's re-target (spec §8.3); `PREFIX_RUNNERS = ("cut42_acceptance.py",)`; `PHASE_MODULES = ("test_session_mounts_acceptance.py", "test_n2_cut43.py")`.
  - **§6, second reader:** check that J9a's re-target is observable (J9's zero-root case passes an adopted, well-formed write root), and that J15-a hashes each read mount's metadata sibling.
  - **§7, limitations:** spec §10.

- [ ] **Step 4: Planning notes.** Append to the spec as §13:

```markdown
## 13. Planning notes

- 2026-09-27 — at planning (plan `../plans/2026-09-27-session-mounts.md`):
  - **The test-local contract is the `biology` fixture** (`tests/profiles.py`
    `biology("fixture")`): a `biology`-namespace document whose identity is
    not the shipped pack's. The acceptance corpora are:
    - A, the write root: base, the fixture `biology` and coordination v2.
      Ordinary proposition writes need the fixture's operators.
    - B: base, the shipped `biology` and coordination v2.
    - C: the fixture `biology` alone, the mm30 shape.
    - D: a read mount with A's profile. J15-a's sabotage needs a read target
      the writer can bind without a profile mismatch.

    §8.2's "biology and the test-local contract" cannot both pin the one
    namespace.
  - **J15a's sabotage rebinds the writer factory's root, and with it the
    operation port, to the first read mount whose profile equals the
    writer's (D).** The spec's §8.3 "binds the first read mount" would bind B,
    whose profile differs, and construction would refuse `ContractMismatch`
    before any write. The unchanged-tree assertion would then never be
    reached (plan review, round 2).
  - **A malformed pin is the manifest's refusal, not the mount's.** A pin not
    spelled `<namespace>:<identity>` fails `load_manifest` with
    `ManifestMalformed`, which propagates (§3.1). `MountPinUnresolved` is
    reserved for a well-formed pin nothing carries.
  - **J12c's sabotage binds the whole session to `corpus_roots[0]`** in place
    of the resolved write root. That is where the writer factory's root
    comes from, so it is the one-edit form of "the writer factory binds
    `corpus_roots[0]`".
  - **Nine units, one per arm.** J13's two units are portable tests in
    `test_mount.py`, and J15-b and J15-c are portable tests in
    `test_session_reconcile.py`, over stand-in views as the spec states.
  - **`mounts=None` is `None`, never an empty mapping.** An empty mapping
    omits every configured root and refuses under decision 3.
```

Update the spec's Status line to "approved 2026-09-27; frozen as cut 43 on <date>".

The plan's step children, each depending on its predecessor:
- Task 0 `beliefs-8e46e1`, Task 1 `beliefs-9ef1bf`, Task 2 `beliefs-98b0b5`;
- Task 3 `beliefs-423d6f`, Task 4 `beliefs-fe1a0a` (high), Task 5 `beliefs-0749cc`;
- Task 6 `beliefs-27ce5c`, Task 7 `beliefs-c70f30`, Task 8 `beliefs-654638`.

- [ ] **Step 5: Verify and commit**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
cd .. && tasks done <Task 0's id> "cut 43 frozen; J12–J15 banked"
tasks check && git add docs README.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut): freeze conformance cut 43, the multi-corpus session; bank J12–J15"
git rev-parse HEAD; sha256sum docs/designs/*-conformance-cut-43.md
```
Record `CUT43_FREEZE_COMMIT` and `CUT43_FROZEN_SHA256` for Task 5.

---

### Task 1: `compile_mount_profile`

**Files:**
- Create: `python/src/beliefs/mount.py`, `python/tests/test_mount.py`
- Modify: `python/src/beliefs/errors.py` (after `ProfileError`)

**Interfaces:**
- Produces: `compile_mount_profile(root: Path, *, available: Iterable[DomainContract] = ()) -> ProfileSpec`, and `MountPinUnresolved(root, namespace, pin)`, a `ProfileError`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_mount.py`:

```python
"""A mounted corpus's profile from its own manifest (session-mounts design §3.1,
decision 5; row J13), portable: manifests written into `tmp_path` roots."""

from __future__ import annotations

import pytest
from profiles import WITH_BIOLOGY, biology, pins_for

from beliefs.consulted import CorpusPins
from beliefs.corpus import CoordinationResolver
from beliefs.errors import ManifestMalformed, MountPinUnresolved, UnparsedContract
from beliefs.mount import compile_mount_profile
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world.registry import CorpusManifest, manifest_bytes

SHIPPED = compile_profile(shipped_base_contract(), [shipped_domain_contract("biology")], coordination=shipped_coordination(2))
LOCAL = compile_profile(shipped_base_contract(), [biology("fixture")], coordination=shipped_coordination(2))
COORD_ONLY = compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))


def _root(tmp_path, name, pins: CorpusPins, corpus_id: str = "c" * 32):
    root = tmp_path / name
    root.mkdir()
    (root / "corpus.yaml").write_bytes(manifest_bytes(CorpusManifest(2, corpus_id, pins)))
    return root


def test_shipped_pins_compile_with_nothing_available(tmp_path):
    root = _root(tmp_path, "a", pins_for(SHIPPED))
    assert compile_mount_profile(root).compiled_identity == SHIPPED.compiled_identity


def test_a_test_local_contract_resolves_when_available(tmp_path):
    """J13-a."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert compiled.compiled_identity == LOCAL.compiled_identity
    assert pins_for(compiled) == pins_for(LOCAL)


def test_the_mm30_shape_compiles_without_coordination(tmp_path):
    root = _root(tmp_path, "c", pins_for(WITH_BIOLOGY))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert compiled.compiled_identity == WITH_BIOLOGY.compiled_identity and not compiled.coordination_kinds


def test_an_unresolved_pin_names_root_namespace_and_pin(tmp_path):
    """J13-a, and Review Focus 2."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    with pytest.raises(MountPinUnresolved) as caught:
        compile_mount_profile(root)
    pin = pins_for(LOCAL).domains["biology"]
    assert (caught.value.root, caught.value.namespace, caught.value.pin) == (root, "biology", pin)
    assert str(root) in str(caught.value) and pin in str(caught.value)


def test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin(tmp_path):
    """J13-a's negative."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    with pytest.raises(MountPinUnresolved):
        compile_mount_profile(root, available=(biology("fixture, second variant"),))


def test_an_available_unpinned_document_is_never_activated(tmp_path):
    """J13-b."""
    root = _root(tmp_path, "coord", pins_for(COORD_ONLY))
    compiled = compile_mount_profile(root, available=(biology("fixture"),))
    assert set(compiled.activated_contracts) == {"coordination"}
    assert compiled.compiled_identity == COORD_ONLY.compiled_identity


def test_duplicate_available_documents_are_harmless(tmp_path):
    """Review Focus 3."""
    root = _root(tmp_path, "b", pins_for(LOCAL))
    twice = compile_mount_profile(root, available=(biology("fixture"), biology("fixture")))
    shipped_too = compile_mount_profile(_root(tmp_path, "a", pins_for(SHIPPED)), available=(shipped_domain_contract("biology"),))
    assert twice.compiled_identity == LOCAL.compiled_identity and shipped_too.compiled_identity == SHIPPED.compiled_identity


@pytest.mark.parametrize(
    "pins, namespace",
    [
        (CorpusPins("science:" + "0" * 64, {}), "science"),
        (CorpusPins(pins_for(COORD_ONLY).science_contract, {"coordination": "coordination:" + "0" * 64}), "coordination"),
    ],
    ids=["unshipped-base", "unshipped-coordination"],
)
def test_well_formed_pins_nothing_carries_refuse(tmp_path, pins, namespace):
    with pytest.raises(MountPinUnresolved) as caught:
        compile_mount_profile(_root(tmp_path, "x", pins), available=(biology("fixture"),))
    assert caught.value.namespace == namespace


def test_a_malformed_pin_is_the_manifests_refusal(tmp_path):
    """§3.1: `load_manifest`'s refusals propagate; `MountPinUnresolved` is for well-formed pins."""
    pins = CorpusPins(pins_for(COORD_ONLY).science_contract, {"biology": "not-the-namespace:" + "0" * 64})
    with pytest.raises(ManifestMalformed):
        compile_mount_profile(_root(tmp_path, "x", pins), available=(biology("fixture"),))


def test_each_compiled_profile_is_accepted_by_the_resolver(tmp_path):
    roots = {
        _root(tmp_path, "a", pins_for(SHIPPED), "a" * 32): (),
        _root(tmp_path, "b", pins_for(LOCAL), "b" * 32): (biology("fixture"),),
        _root(tmp_path, "c", pins_for(WITH_BIOLOGY), "d" * 32): (biology("fixture"),),
    }
    resolver = CoordinationResolver({root: compile_mount_profile(root, available=docs) for root, docs in roots.items()})
    assert set(resolver.mounted()) == {root.resolve() for root in roots}


def test_arguments_are_typed(tmp_path):
    root = _root(tmp_path, "a", pins_for(SHIPPED))
    with pytest.raises(TypeError):
        compile_mount_profile(str(root))  # type: ignore[arg-type]
    with pytest.raises(UnparsedContract):
        compile_mount_profile(root, available=(object(),))  # type: ignore[arg-type]
```

If `CorpusManifest`'s constructor or `manifest_bytes` takes other arguments than `test_publication_doors.mount` uses (`CorpusManifest(2, corpus_id, pins)`), follow that helper.

- [ ] **Step 2: Run to verify they fail.** `cd python && uv run --frozen pytest tests/test_mount.py -q` → `No module named 'beliefs.mount'`.

- [ ] **Step 3: Implement.** In `errors.py`, after `ProfileError`:

```python
class MountPinUnresolved(ProfileError):
    """A mounted corpus's manifest pins a contract that no shipped pack and no
    available document carries (session-mounts design decision 5)."""

    def __init__(self, root: Path, namespace: str, pin: str) -> None:
        super().__init__(f"{root}: the {namespace} pin {pin} resolves to no shipped or available contract")
        self.root = root
        self.namespace = namespace
        self.pin = pin
```

`python/src/beliefs/mount.py`:

```python
"""A mounted corpus's profile, compiled from its own manifest's pins
(session-mounts design §3.1, decision 5): each pin resolves by namespace and
content identity against the shipped packs and the caller's available
documents, and nothing the manifest does not pin is activated. The launcher
calls it once per configured root, for a session's mounts and for a
sessionless read alike."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from beliefs.contract.coordination import CoordinationContract
from beliefs.contract.domain import DomainContract
from beliefs.errors import MountPinUnresolved, ProfileError, UnparsedContract
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world import load_manifest

__all__ = ["compile_mount_profile"]

_COORDINATION = "coordination"


def compile_mount_profile(root: Path, *, available: Iterable[DomainContract] = ()) -> ProfileSpec:
    """The profile `root`'s manifest pins. Refuses `MountPinUnresolved`, naming the
    root, the namespace and the pin, for the first pin nothing carries."""
    if not isinstance(root, Path):
        raise TypeError("compile_mount_profile takes the corpus root as a Path")
    documents = tuple(available)
    for document in documents:
        if not isinstance(document, DomainContract):
            raise UnparsedContract(f"an available contract is a {type(document).__name__}, not a parsed DomainContract")
    pins = load_manifest(root).profile
    base = shipped_base_contract()
    if pins.science_contract != f"science:{base.content_identity}":
        raise MountPinUnresolved(root, "science", pins.science_contract)
    domains: list[DomainContract] = []
    coordination: CoordinationContract | None = None
    for namespace, pin in sorted(pins.domains.items()):
        prefix = f"{namespace}:"
        identity = pin[len(prefix):] if pin.startswith(prefix) else None
        if namespace == _COORDINATION:
            coordination = next((c for c in (shipped_coordination(1), shipped_coordination(2)) if c.content_identity == identity), None)
            if coordination is None:
                raise MountPinUnresolved(root, namespace, pin)
            continue
        candidates = (*_shipped(namespace), *(d for d in documents if d.namespace == namespace))
        match = next((c for c in candidates if c.content_identity == identity), None)
        if match is None:
            raise MountPinUnresolved(root, namespace, pin)
        domains.append(match)
    return compile_profile(base, domains, coordination=coordination)


def _shipped(namespace: str) -> tuple[DomainContract, ...]:
    try:
        return (shipped_domain_contract(namespace),)
    except ProfileError:
        return ()  # no shipped pack for this namespace
```

If importing `beliefs.world` at module level cycles (`corpus.py` imports it lazily for that reason), move the import into the function and note why.

- [ ] **Step 4: Run to verify they pass.** `uv run --frozen pytest tests/test_mount.py -q && uv run --frozen pyright src/beliefs/mount.py` → `12 passed` (11 test functions, one parametrized two ways).

- [ ] **Step 5: Commit**

```bash
tasks done <Task 1's id> "compile_mount_profile, MountPinUnresolved"
tasks check && git add python/src/beliefs/mount.py python/src/beliefs/errors.py python/tests/test_mount.py tasks
git commit -m "feat(session): compile a mounted corpus's profile from its manifest — cut 43"
```

---

### Task 2: The session over a write root and mounts

**Files:**
- Modify: `python/src/beliefs/session/__init__.py` (`open_attended_session`, `SessionRefused`'s docstring in `errors.py`)
- Modify, callers: `tests/test_session_writer.py` (lines 390, 444, 714 and `_coordinated_open`), `tests/test_session_routes.py` (426, 486), `tests/test_profile_agreement.py` (499), `tests/acceptance/test_session_acceptance.py` (`attended`, lines 170, 347, 483, 517–534, 539, the script string at 1032, and 1203)
- Modify: `tests/acceptance/test_n2_cut19.py` (`_LIVE_SABOTAGES`)
- Test: `tests/test_session_writer.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `open_attended_session(world_config, operations_root, *, write_root: Path, profile: ProfileSpec, mounts: Mapping[Path, ProfileSpec] | None = None, store_root=None, snapshot_resolver=None, project=None) -> WriterSession`.

- [ ] **Step 1: Write the failing tests**, appended to `tests/test_session_writer.py`:

```python
# --- session-mounts §3.2: the write root and the mounts (row J12) --------------

from beliefs.errors import ContractMismatch, SessionRefused
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination

V2M = compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))


def _two_roots(tmp_path, monkeypatch):
    from beliefs.world import WorldConfig

    a, b = mounted_root(tmp_path / "a", V2M), mounted_root(tmp_path / "b", V2M)
    _stub_durable_seams(monkeypatch)
    return a.resolve(), b.resolve(), WorldConfig(tmp_path / "world", WORLD, (a, b))


def _open(config, tmp_path, **kwargs):
    from beliefs.session import open_attended_session

    return open_attended_session(config, tmp_path / "ops", **kwargs)


@pytest.mark.parametrize("which", [0, 1], ids=["first", "second"])
def test_either_configured_root_can_be_the_write_root(tmp_path, monkeypatch, which):
    a, b, config = _two_roots(tmp_path, monkeypatch)
    write = (a, b)[which]
    session = _open(config, tmp_path, write_root=write, profile=V2M, mounts={a: V2M, b: V2M})
    assert session.corpus_root == write


@pytest.mark.parametrize(
    "case",
    ["outside", "zero-roots", "missing-mount", "extra-mount", "repeated-mount", "unadopted-read-mount"],
)
def test_the_configuration_refusals_create_no_session_directory(tmp_path, monkeypatch, case):
    import os

    from beliefs.world import WorldConfig

    a, b, config = _two_roots(tmp_path, monkeypatch)
    kwargs = {"write_root": a, "profile": V2M, "mounts": {a: V2M, b: V2M}}
    if case == "outside":
        kwargs["write_root"] = tmp_path / "elsewhere"
    elif case == "zero-roots":
        config = WorldConfig(tmp_path / "world", WORLD, ())
        kwargs["mounts"] = None
    elif case == "missing-mount":
        kwargs["mounts"] = {a: V2M}
    elif case == "extra-mount":
        kwargs["mounts"] = {a: V2M, b: V2M, mounted_root(tmp_path / "c", V2M): V2M}
    elif case == "repeated-mount":
        os.symlink(a, tmp_path / "link")
        kwargs["mounts"] = {a: V2M, tmp_path / "link": V2M, b: V2M}
    else:
        (tmp_path / "d").mkdir()
        config = WorldConfig(tmp_path / "world", WORLD, (a, tmp_path / "d"))
        kwargs["mounts"] = {a: V2M, tmp_path / "d": V2M}
    with pytest.raises(SessionRefused):
        _open(config, tmp_path, **kwargs)
    assert not (tmp_path / "ops" / "sessions").exists()


def test_the_writer_profile_must_be_the_write_mounts(tmp_path, monkeypatch):
    a, b, config = _two_roots(tmp_path, monkeypatch)
    other = compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(1))
    with pytest.raises(ContractMismatch):
        _open(config, tmp_path, write_root=a, profile=V2M, mounts={a: other, b: V2M})
    assert not (tmp_path / "ops" / "sessions").exists()


def test_mount_keys_resolve_before_matching(tmp_path, monkeypatch):
    """Review Focus 1."""
    import os

    a, b, config = _two_roots(tmp_path, monkeypatch)
    os.symlink(b, tmp_path / "b-link")
    session = _open(config, tmp_path, write_root=a, profile=V2M, mounts={a: V2M, tmp_path / "b-link": V2M})
    assert session._coordination_resolver is not None and set(session._coordination_resolver.mounted()) == {a, b}


def test_two_roots_without_mounts_open_without_coordination(tmp_path, monkeypatch):
    """Review Focus 4."""
    a, _, config = _two_roots(tmp_path, monkeypatch)
    session = _open(config, tmp_path, write_root=a, profile=V2M)
    assert session._coordination_resolver is None and session.corpus_root == a


def test_a_non_path_write_root_is_a_type_error(tmp_path, monkeypatch):
    a, b, config = _two_roots(tmp_path, monkeypatch)
    with pytest.raises(TypeError):
        _open(config, tmp_path, write_root=str(a), profile=V2M)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        _open(config, tmp_path, write_root=a, profile=V2M, mounts={str(a): V2M, b: V2M})  # type: ignore[dict-item]
```

`WriterSession.corpus_root` is public, and the resolver is `_coordination_resolver` (`session/writer.py`). The tests read the private name, as the selection tests do.

- [ ] **Step 2: Run to verify they fail.** `uv run --frozen pytest tests/test_session_writer.py -q -k "write_root or mounts or refusals or writer_profile"` → `unexpected keyword argument 'write_root'`.

- [ ] **Step 3: Implement.** In `session/__init__.py`, import `Mapping` from `collections.abc`, then replace `open_attended_session`'s signature and its checks up to and including the resolver:

```python
def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    write_root: Path,
    profile: ProfileSpec,
    mounts: Mapping[Path, ProfileSpec] | None = None,
    store_root: Path | None = None,
    snapshot_resolver: SnapshotResolver | None = None,
    project: CoordinationAddress | None = None,
) -> WriterSession:
    """The interactive constructor (design §3.1, as the session-mounts design
    amends it): full permit by construction. It writes `write_root`, one of the
    configured roots, and nothing else. When `mounts` is given, it covers every
    configured root, each under the profile its own manifest pins, and
    coordination resolves over all of them. `None` opens without coordination.

    A world-bound caller passes `RetainedSnapshots(world)`; without it a
    session cannot author a snapshot-arm retraction.

    `project`, an unpinned project address, is the initial selection: it
    resolves through the coordination resolver before the session directory
    exists, and the pinned result is written into `session-open` (selection
    design §4.1).
    """
    if type(world_config) is not WorldConfig:
        raise TypeError("open_attended_session takes an exact WorldConfig")
    if not isinstance(operations_root, Path):
        raise TypeError("operations_root must be a Path")
    if not isinstance(write_root, Path):
        raise TypeError("write_root must be a Path")
    if not isinstance(profile, ProfileSpec):
        raise TypeError("profile must be a compiled ProfileSpec")
    if mounts is not None and (
        not isinstance(mounts, Mapping)
        or any(not isinstance(key, Path) or not isinstance(value, ProfileSpec) for key, value in mounts.items())
    ):
        raise TypeError("mounts maps each configured root's Path to its compiled ProfileSpec")
    if project is not None:
        require_project_address(project)
        if mounts is None:
            raise SessionRefused(f"{project}: an initial project needs mounted corpora to resolve it")
    write_root = write_root.resolve()
    if write_root not in world_config.corpus_roots:
        raise SessionRefused(f"write root {write_root} is not one of the configured corpus roots")
    root = write_root
    mounted: dict[Path, ProfileSpec] | None = None
    if mounts is not None:
        resolved = [Path(key).resolve() for key in mounts]
        configured = set(world_config.corpus_roots)
        if len(set(resolved)) != len(resolved) or set(resolved) != configured:
            missing = sorted(str(path) for path in configured - set(resolved))
            extra = sorted(str(path) for path in set(resolved) - configured)
            raise SessionRefused(
                f"the mounts are exactly the configured corpus roots, each once; missing {missing}, extra {extra}"
            )
        mounted = {Path(key).resolve(): value for key, value in mounts.items()}
    require_profile_compatible(profile, mounted[root] if mounted is not None else None)
    try:
        corpus_id = load_manifest(root).corpus_id
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"{root}: the corpus is not adopted: {caught}") from caught
    require_pins_agree(root, profile)
    view = log_seam().inspect_detached(root)
    if type(view) is not WellFormedView:
        raise SessionRefused(
            f"{root}: the chain is {type(view).__name__}; a session opens over a registered, well-formed root"
        )
    store_id: str | None = None
    if store_root is not None:
        if not isinstance(store_root, Path):
            raise TypeError("store_root must be a Path")
        store_id = store_identity(store_root)
        if store_id is None:
            raise SessionRefused(f"store root {store_root} carries no store genesis")
    resolver = _mount_resolver(mounted)
    pinned = None if project is None else resolve_project(resolver, project)
```

From `session_id = …` on, the function is unchanged: it binds `root`. Add after it:

```python
def _mount_resolver(mounted: Mapping[Path, ProfileSpec] | None) -> CoordinationResolver | None:
    """Every mount in the resolver (decision 3). A read mount whose manifest does
    not load refuses as the write root's does; a pin mismatch is the resolver's own."""
    if mounted is None:
        return None
    try:
        return CoordinationResolver(mounted)
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"a mounted corpus is not adopted: {caught}") from caught
```

The `resolver = _mount_resolver(mounted)` line is J14a's pin, and `    if write_root not in world_config.corpus_roots:` is J12a's and J9a's. In `errors.py`, `SessionRefused`'s docstring becomes: "`open_attended_session` refused its configuration (writer-session design §3.1, session-mounts design §3.2): a write root outside the configured roots, a mount set other than the configured roots, a root with no manifest, or no well-formed chain."

- [ ] **Step 4: Migrate the callers.**
  - Every `open_attended_session(config, ops, …)` over a one-root config gains `write_root=<that root>`.
  - Every `coordination=<profile>` becomes `mounts={<that root>: <profile>}`.
  - `coordination=None` is dropped.
  - `_coordinated_open`'s `coordination=profile if coordination else None` becomes `mounts={root: profile} if coordination else None`.
  - `test_profile_agreement.py:499` becomes `mounts={<its root>: WITH_BIOLOGY} if mismatch == "mounted" else None`.
  - The script string at `test_session_acceptance.py:1032` gains `write_root=root`.
  - In `test_session_acceptance.py`, `attended()` passes `write_root=root`, and its `coordination=profile` caller at line 347 becomes `mounts={root: profile}`.

  **J9's case.** In `test_j9_lifecycle_and_the_refusing_configurations`:
  - delete `other = adopted(work_directory, "other")` and the `("two roots", (root, other))` row, since J12 covers that configuration now (spec §8.3);
  - give the loop's call `write_root=roots[0] if roots else root`. The zero-root case then passes the adopted, well-formed `root`, so the membership check is the only refusal on its path.

  **J9a.** Add to `test_n2_cut19.py`'s `_LIVE_SABOTAGES`:

```python
    "J9a": Sabotage(
        # session-mounts §8.3: the root-count guard is gone; the membership check
        # alone refuses a zero-root configuration, so J9's zero-root case sees it.
        "session/__init__.py",
        before="    if write_root not in world_config.corpus_roots:\n",
        after="    if False:\n",
    ),
```

- [ ] **Step 5: Run**

```bash
cd python && uv run --frozen pytest tests/test_session_writer.py tests/test_session_routes.py tests/test_profile_agreement.py tests/test_session_ledger.py tests/test_arm_staleness.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_capability_boundary.py -q
uv run --frozen pytest tests/acceptance/test_session_acceptance.py -q
uv run --frozen pytest tests/acceptance/test_n2_cut19.py -q -k "each_sabotage_names_one_real_source_site or inventory"
```
Expected: all pass; `test_arm_staleness.py` reports no stale arm. `test_session_acceptance.py` needs the certified volume, and J9 passes with six refusing configurations.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 2's id> "open_attended_session over a write root and mounts; callers; J9's case; J9a re-targeted"
tasks check && git add python/src/beliefs/session/__init__.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(session): one write root, every configured corpus mounted — cut 43"
```

---

### Task 3: Reconciliation matches by corpus

**Files:**
- Modify: `python/src/beliefs/session/reconcile.py`
- Test: `python/tests/test_session_reconcile.py`

- [ ] **Step 1: Write the failing tests.** Give the module's `ledger()` helper a `corpus: str = CORPUS` keyword and use it in the `act` line (`"corpus": corpus`). Then append:

```python
# --- session-mounts decision 8: matching by (corpus, digest) (J15-b, J15-c) -----

A_ID, B_ID = "a" * 32, "b" * 32


def _misattributed():
    """A ledger naming corpus A over a registration committed in B's chain."""
    chains = {A_ID: view(), B_ID: view(intent(I), registration(R, I), settled(R, True))}
    return codes(reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus=A_ID)], chains))


def test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there():
    """J15-b: the forward direction."""
    assert ("session-entry-foreign", "error", R) in _misattributed()


def test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified():
    """J15-c: the backward direction."""
    assert ("session-act-unverified", "error", R) in _misattributed()


def test_the_same_act_naming_the_corpus_that_holds_it_is_covered():
    chains = {A_ID: view(), B_ID: view(intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus=B_ID)], chains) == ()


def test_an_act_naming_an_unconfigured_corpus_is_not_unverified():
    """Review Focus 5: no chain here is truth for it."""
    chains = {A_ID: view()}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus="e" * 32)], chains) == ()
```

- [ ] **Step 2: Run to verify they fail.** `uv run --frozen pytest tests/test_session_reconcile.py -q -k "foreign_there or does_not_hold or holds_it"` fails: the two new findings are absent.

- [ ] **Step 3: Implement.** In `reconcile.py`:
  - `committed_everywhere: set[str] = set()` becomes `committed_pairs: set[tuple[str, str]] = set()`;
  - `committed_everywhere |= {digest for digest, committed in settlement.items() if committed}` becomes `committed_pairs |= {(corpus_id, digest) for digest, committed in settlement.items() if committed}`;
  - `acts: set[str] = {act.entry for act in reader.acts()} if reader is not None else set()` becomes `acts: set[str] = {act.entry for act in reader.acts() if act.corpus == corpus_id} if reader is not None else set()`;
  - `if act.corpus in well_formed and act.entry not in committed_everywhere:` becomes `if act.corpus in well_formed and (act.corpus, act.entry) not in committed_pairs:`.

  The pinned `if r.digest in acts:` line does not change. Update the comment above the backward loop to say claims are matched by corpus (session-mounts decision 8).

- [ ] **Step 4: Run.** `uv run --frozen pytest tests/test_session_reconcile.py tests/test_arm_staleness.py -q` passes, with every existing reconcile test unchanged and no stale arm.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 3's id> "reconciliation matches (corpus_id, digest) both ways"
tasks check && git add python/src/beliefs/session/reconcile.py python/tests/test_session_reconcile.py tasks
git commit -m "fix(session): reconcile acts to chains by corpus as well as digest — cut 43"
```

---
### Task 4: The acceptance module — `test_session_mounts_acceptance.py`

**Files:**
- Create: `python/tests/acceptance/test_session_mounts_acceptance.py`

**Interfaces:**
- Consumes: Tasks 1–3, and `adopted`, `fresh` and `PROPOSITIONS` from `test_session_acceptance`.
- Produces: the unit functions Task 5's `UNIT_CHECKS` names.

- [ ] **Step 1: Write the module**

```python
"""Conformance cut 43 — the multi-corpus session (session-mounts design §8.2):
J12, J14 and J15-a over real roots on the certified volume. Corpus A (the
write root) pins base, the fixture `biology` and coordination v2; B pins base,
the shipped `biology` and coordination v2; C pins the fixture `biology` alone,
the mm30 shape; D shares A's profile as a read mount. Every mount is compiled
from its own manifest, and each case's directory is removed at teardown."""

from __future__ import annotations

import secrets
import shutil
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace

import pytest
from authority import FULL
from coordination_fixtures import content_for, pins_for
from nodes.core.paths import path_for_node_id
from profiles import WITH_BIOLOGY, biology
from test_durable_families import proposition
from test_session_acceptance import PROPOSITIONS, fresh

from beliefs.coordination import CoordinationRefused, coordination_revision
from beliefs.corpus import CoordinationResolver
from beliefs.errors import ContractMismatch, CoordinationUnavailable, SessionRefused
from beliefs.mount import compile_mount_profile
from beliefs.permit import RequiredCapabilities
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.session import open_attended_session, open_ledger_reader, reconcile_sessions
from beliefs.world import WorldConfig

V2_LOCAL = compile_profile(shipped_base_contract(), [biology("fixture")], coordination=shipped_coordination(2))
V2_SHIPPED = compile_profile(shipped_base_contract(), [shipped_domain_contract("biology")], coordination=shipped_coordination(2))
AVAILABLE = (biology("fixture"),)


def _adopt(base: Path, name: str, profile) -> Path:
    root = base / name
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
    return root.resolve()


@pytest.fixture()
def corpora(work_directory):
    """Every case owns one directory under the certified work directory: its
    roots, their `.metadata` siblings, its worlds, links and operations roots.
    Teardown removes it whole (plan review, round 2)."""
    base = Path(mkdtemp(prefix="cut43-", dir=work_directory)).resolve()
    try:
        yield SimpleNamespace(
            base=base,
            a=_adopt(base, "a", V2_LOCAL),
            b=_adopt(base, "b", V2_SHIPPED),
            c=_adopt(base, "c", WITH_BIOLOGY),
            d=_adopt(base, "d", V2_LOCAL),  # a read mount with A's profile: J15-a's sabotage target
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)


def mounts_for(roots):
    return {root: compile_mount_profile(root, available=AVAILABLE) for root in roots}


def open_over(s, roots, write_root, *, mounts="compiled", profile=None, **kwargs):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    ops = s.base / f"ops-{secrets.token_hex(4)}"
    compiled = mounts_for(roots) if mounts == "compiled" else mounts
    writer_profile = profile or (compiled[write_root] if compiled else compile_mount_profile(write_root, available=AVAILABLE))
    session = open_attended_session(config, ops, write_root=write_root, profile=writer_profile, mounts=compiled, **kwargs)
    return session, config, ops


def refused_without_directory(s, roots, write_root, error=SessionRefused, **kwargs):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    ops = s.base / f"ops-{secrets.token_hex(4)}"
    with pytest.raises(error):
        open_attended_session(config, ops, write_root=write_root, **kwargs)
    assert not (ops / "sessions").exists()


def library_on(root: Path, profile):
    return open_corpus(root, authority=FULL, profile=profile, coordination_resolver=CoordinationResolver({root: profile}))


def state(root: Path):
    """A root's bytes and its metadata sibling's: the chain lives under the root."""
    def tree(path: Path):
        return sorted((str(p.relative_to(path)), p.read_bytes() if p.is_file() else None) for p in path.rglob("*")) if path.exists() else []
    return tree(root), tree(metadata_root_for(root))


# --- J12 ------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["outside", "zero-roots"])
def test_j12_a_a_write_root_outside_the_configured_roots_refuses_durably(corpora, case):
    """J12-a: the membership check, which also refuses a configuration naming no root."""
    s = corpora
    if case == "outside":
        refused_without_directory(s, (s.a, s.b), s.c, profile=WITH_BIOLOGY)
    else:
        refused_without_directory(s, (), s.a, profile=V2_LOCAL)


@pytest.mark.parametrize("case", ["missing", "extra", "repeated", "unadopted", "profile"])
def test_j12_b_a_mount_set_other_than_the_configured_roots_refuses_durably(corpora, case):
    """J12-b: the mount set is exactly the configured roots, each once; a read mount's
    manifest loads; the writer's profile is its own mount's."""
    s = corpora
    compiled = mounts_for((s.a, s.b))
    if case == "missing":
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={s.a: compiled[s.a]})
    elif case == "extra":
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={**compiled, **mounts_for((s.c,))})
    elif case == "repeated":
        link = s.base / f"link-{secrets.token_hex(4)}"
        link.symlink_to(s.a)
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={**compiled, link: compiled[s.a]})
    elif case == "unadopted":
        bare = s.base / f"bare-{secrets.token_hex(4)}"
        init_corpus_root(bare, authority=FULL)
        refused_without_directory(s, (s.a, bare), s.a, profile=V2_LOCAL, mounts={s.a: compiled[s.a], bare: V2_SHIPPED})
    else:
        refused_without_directory(s, (s.a, s.b), s.a, ContractMismatch, profile=V2_SHIPPED, mounts=compiled)


@pytest.mark.parametrize("case", ["a", "b", "one-root"])
def test_j12_c_the_session_writes_the_named_root_and_only_it_durably(corpora, case):
    """J12-c: each configured root as the write root in turn; the negative, a
    one-root world, opens as J9's sessions do."""
    s = corpora
    if case == "one-root":
        session, config, ops = open_over(s, (s.a,), s.a)
        reader = open_ledger_reader(ops, session.session_id)
        assert reader.world_id == config.world_id and reader.actor == session.actor
        session.close()
        return
    write, other = (s.a, s.b) if case == "a" else (s.b, s.a)
    session, _, _ = open_over(s, (s.a, s.b), write)
    assert session.corpus_root == write
    before = state(other)
    w = fresh(session, "A", RequiredCapabilities.coordination())
    project = w.mint_coordination("project", content=content_for("project", name=f"in-{case}"))
    assert (write / path_for_node_id(project.id)).is_file()
    assert state(other) == before
    session.close()


# --- J14 ------------------------------------------------------------------------


def test_j14_a_coordination_resolves_over_every_mount_durably(corpora):
    """J14-a: a project minted in B is the initial selection of a session writing
    A; its revision lands in A and resolves; a second tip in B makes it divergent;
    without mounts, coordination is unavailable."""
    s = corpora
    library = library_on(s.b, V2_SHIPPED)
    project = library.mint_coordination("project", content=content_for("project", name="in-b"))
    address = coordination_revision(project).address.unpinned()
    session, _, ops = open_over(s, (s.a, s.b), s.a, project=address)
    assert open_ledger_reader(ops, session.session_id).initial_project == address.pinned(project.uid)
    w = fresh(session, "A", RequiredCapabilities.coordination())
    revised = w.revise_coordination("project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-a"))
    assert (s.a / path_for_node_id(revised.id)).is_file() and not (s.b / path_for_node_id(revised.id)).exists()
    resolver = session._coordination_resolver
    assert resolver is not None and resolver.resolve(address).uid == revised.uid
    assert set(resolver.standing("project")) == {address}
    sibling = library_on(s.b, V2_SHIPPED).revise_coordination(
        "project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-b")
    )
    divergent = resolver.resolve(address)
    assert type(divergent) is CoordinationRefused and divergent.reason == "divergent-view"
    assert set(divergent.tips) == {revised.uid, sibling.uid}
    session.close()
    bare, _, _ = open_over(s, (s.a, s.b), s.a, mounts=None, profile=V2_LOCAL)
    with pytest.raises(CoordinationUnavailable):
        fresh(bare, "B", RequiredCapabilities.coordination()).mint_coordination("project", content=content_for("project"))
    bare.close()


# --- J15 ------------------------------------------------------------------------


def test_j15_a_a_session_never_writes_a_read_mount_durably(corpora):
    """J15-a: an ordinary write, a coordination mint and a revision of a read-mount
    predecessor leave every read mount byte-identical, and reconciliation finds nothing."""
    s = corpora
    project = library_on(s.b, V2_SHIPPED).mint_coordination("project", content=content_for("project", name="in-b"))
    address = coordination_revision(project).address.unpinned()
    before = {root: state(root) for root in (s.b, s.c, s.d)}
    session, config, ops = open_over(s, (s.a, s.b, s.c, s.d), s.a)
    w = fresh(session, "A", PROPOSITIONS)
    w.add(proposition("q1"))
    session.close_invocation("A", {"done": []})
    c = fresh(session, "B", RequiredCapabilities.coordination())
    c.mint_coordination("project", content=content_for("project", name="in-a"))
    c.revise_coordination("project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-a"))
    session.close_invocation("B", {"done": []})
    session.close()
    assert {root: state(root) for root in (s.b, s.c, s.d)} == before
    assert reconcile_sessions(config, ops) == ()


def test_the_mm30_shape_mounts_beside_a_working_corpus_durably(corpora):
    """Decision 3: a corpus pinning no coordination contract is mounted, and contributes nothing to resolution."""
    s = corpora
    session, _, _ = open_over(s, (s.a, s.c), s.a)
    resolver = session._coordination_resolver
    assert resolver is not None and set(resolver.mounted()) == {s.a, s.c}
    assert dict(resolver.standing("project")) == {}
    session.close()
```

If `proposition("q1")` needs a profile other than A's (the fixture `biology` with coordination), use the kind J1's test writes under `WITH_BIOLOGY`. A is that profile plus coordination.

- [ ] **Step 2: Run.** `cd "$(pwd -P)" && uv run --frozen pytest tests/acceptance/test_session_mounts_acceptance.py -q`, then `--collect-only -q | tail -1`. Expected: `13 passed`, 13 collected. A unit that cannot see its behaviour is rehomed here and recorded in the spec's §13, never dropped.

- [ ] **Step 3: Commit**

```bash
tasks done <Task 4's id> "acceptance module: J12, J14, J15-a; 13 cases"
tasks check && git add python/tests/acceptance/test_session_mounts_acceptance.py tasks
git commit -m "test(cut43): the multi-corpus session acceptance module — J12, J14, J15"
```

---

### Task 5: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut43.py`, `python/tests/acceptance/n2_arms_cut43.py` (cut 41's shim with `41` → `43`), `python/tests/acceptance/test_n2_cut43.py`, `python/tools/cut43_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

- [ ] **Step 0: Wait for cut 42, then merge `main`.** Cut 43 chains `cut42_acceptance.py` (rule 5), which reaches this branch only when `design/publish` has merged. Check with `git -C ~/d/beliefs log --oneline main -- python/tools/cut42_acceptance.py | head -1`.
  - If that prints nothing, run `tasks park <Task 5's id> "merge main after cut 42 (beliefs-3ce305) lands, then Task 5" --reason dependency`, then `tasks dep <Task 5's id> --on beliefs-3ce305`, and end the increment.
  - Once it prints a commit, run `git merge --no-ff main` in this worktree. Resolve toward `main` in the shared files (roadmap rule 3): the ledger, the roadmap, README, the guide and `test_designs_corpus.py`.
  - The `Y` rows come from `main` and the `J` rows from this branch. Rerun `tools/roadmap_status.py`, and expect `Closed 210 of 241; open 31`.
  - Then run `just test-fast` and `tests/test_arm_staleness.py`.

- [ ] **Step 1: The declaration**, on cut 42's shape (`_arm(row, module, assertion, before, after)`), with:
- `DECLARATION_UNITS = ("J12-a", "J12-b", "J12-c", "J13-a", "J13-b", "J14-a", "J15-a", "J15-b", "J15-c")`;
- `UNIT_CHECKS`:
  - `J12-a`, `J12-b`, `J12-c`, `J14-a` and `J15-a`: the Task 4 functions of those letters, in `acceptance/test_session_mounts_acceptance.py`;
  - `J13-a`: `test_mount.py::test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin`;
  - `J13-b`: `test_mount.py::test_an_available_unpinned_document_is_never_activated`;
  - `J15-b`: `test_session_reconcile.py::test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there`;
  - `J15-c`: `test_session_reconcile.py::test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified`.

The arms follow. Copy each `before` from the tree and check it with `source.count(before) == 1`. Each `after` must parse.

| arm | module | before | after |
|---|---|---|---|
| J12-a | `session/__init__.py` | `    if write_root not in world_config.corpus_roots:` | `    if False:` |
| J12-b | `session/__init__.py` | `        if len(set(resolved)) != len(resolved) or set(resolved) != configured:` | `        if False:` |
| J12-c | `session/__init__.py` | `    root = write_root` | `    root = world_config.corpus_roots[0]` |
| J13-a | `mount.py` | `        match = next((c for c in candidates if c.content_identity == identity), None)` | `        match = next(iter(candidates), None)` |
| J13-b | `mount.py` | `    return compile_profile(base, domains, coordination=coordination)` | `    return compile_profile(base, [*domains, *(d for d in documents if d.namespace not in {m.namespace for m in domains})], coordination=coordination)` |
| J14-a | `session/__init__.py` | `    resolver = _mount_resolver(mounted)` | `    resolver = _mount_resolver({root: mounted[root]} if mounted is not None else None)` |
| J15-a | `session/__init__.py` | `    def writer_factory(authority: Authority) -> CorpusWriter:\n        return CorpusWriter(` | `    def writer_factory(authority: Authority) -> CorpusWriter:\n        root = next(r for r, p in (mounted or {}).items() if r != write_root and p.compiled_identity == profile.compiled_identity)\n        return CorpusWriter(` |
| J15-b | `session/reconcile.py` | `            acts: set[str] = {act.entry for act in reader.acts() if act.corpus == corpus_id} if reader is not None else set()` | `            acts: set[str] = {act.entry for act in reader.acts()} if reader is not None else set()` |
| J15-c | `session/reconcile.py` | `            if act.corpus in well_formed and (act.corpus, act.entry) not in committed_pairs:` | `            if act.corpus in well_formed and act.entry not in {digest for _, digest in committed_pairs}:` |

J12-c's and J15-a's `after`s are spelled for the one-edit form (spec §13). J15-a's rebinds the factory's local `root`, so the writer and its operation port both move to D, a read mount with the writer's profile. The write then lands there, and J15-a's unchanged-tree assertion is what fails. `test_arm_staleness.py` expects `root = write_root` and the `writer_factory` signature line to occur once each in `session/__init__.py`.

- [ ] **Step 2: The guard.** Copy `test_n2_cut42.py` (from `main` after Step 0) to `test_n2_cut43.py`, then:
- import `CUT42_ARMS` into `PRIOR_ARMS`, and pin `n2_arms_cut42.py` in `FROZEN_PRIOR_CUT_FILES`;
- set `FROZEN_CUT`, `CUT43_FREEZE_COMMIT`, `CUT43_FROZEN_SHA256` and `FROZEN_DECLARATION`;
- assert 9 units and 9 arms, `"**9 arms, 9 declaration units**" in current`, and `'("cut42_acceptance.py",)' in current`.

The guard holds no `_LIVE_SABOTAGES` table. J9a's re-target is `test_n2_cut19.py`'s (Task 2).

- [ ] **Step 3: The runner.** `python/tools/cut43_acceptance.py`, as cut 42's with:
- `cut=43`;
- `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut43"`;
- `PREFIX_RUNNERS = ("cut42_acceptance.py",)`;
- `PHASE_MODULES = ("test_session_mounts_acceptance.py", "test_n2_cut43.py")`;
- `declared_accounting` asserting rows `{"J12", "J13", "J14", "J15"}` and `(9, 9)`;
- on success, `print("guarantee rows exercised: 4 (4 newly closed: J12, J13, J14, J15)", flush=True)`.

- [ ] **Step 4: The recent-cut row.** In `test_recent_cut_acceptance.py`:
- add `import cut43_acceptance as cut43`;
- add `(cut43, 43, (9, 9, 4))` with id `"cut43"`;
- add `if cut == 43: assert "guarantee rows exercised: 4 (4 newly closed: J12, J13, J14, J15)" in output`.

- [ ] **Step 5: Guard green, then the cut, harness-tracked.**

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
```

Then run with the Bash tool, `run_in_background: true`:

```bash
cd ~/d/beliefs/.worktrees/session-mounts/python && cd "$(pwd -P)" && export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30 && set -o pipefail && uv run --frozen python tools/cut43_acceptance.py 2>&1 | tee ~/d/beliefs/.work/acceptance/cut43-runner.log
```

Read the log when the harness wakes the session. The expected tail has:
- three `[cut43 phase n/3]` lines;
- `declared arms: 9 (= 9 declaration units; 4 guarantee rows)`;
- the rows-exercised line;
- exit 0, with every arm `sound`.

A `stale` verdict means fix the declaration. A `vacuous` arm means reshape it and record the change in the spec's §13. On a background-cap kill, park `--reason environment` and tell the user.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 5's id> "N2 declarations, guard, runner, recent-cut row; cut 43 ran green"
tasks check && git add python/tests/n2_arms_cut43.py python/tests/acceptance/n2_arms_cut43.py python/tests/acceptance/test_n2_cut43.py python/tools/cut43_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut43): N2 declarations, guard, runner and the recent-cut row — J12–J15"
```

---

### Task 6: The reproduction re-run

- [ ] **Step 1: Run** as cut 42's Task 9 does: preflight, then `reproduction.rederive`, and copy `state.json` first. Then `grep -n 'open_attended_session\|mount' python/tools/reproduction/*.py`, which shows whether the driver opens a session.
- [ ] **Step 2: Append the next addendum** (§22 if cut 42's §21 is on `main`) on §21's shape:
  - what changed: the session's open signature, per-mount profiles and corpus-matched reconciliation;
  - what the re-run reached: the same `NoBelief` answer, with `state.json` byte-identical;
  - what it does not claim: mm30 is still one corpus opened as a library. The second-project milestone, mm30 mounted beside a working corpus, is science's (`sci-0d00d2`), after `beliefs-c08725` relocates the corpus.

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
tasks done <Task 6's id> "reproduction re-run under cut 43; nothing moves"
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under the multi-corpus session; nothing moves"
```

---

### Task 7: The results record, the re-rank, and the amendments

- [ ] **Step 1: The results record** `docs/plans/<date>-conformance-cut-43-results.md`, on cut 42's shape:
  - **§1, what ran:** the runner's summary and the per-unit table.
  - **§2, accounting:** 9 / 9 / 4; J12–J15 closed; the totals as `roadmap_status.py` prints them.
  - **§3, evidence:** the spec's §13 notes; J9a's re-target, J9's zero-root case and the removed two-root case; the staleness probe clean with only J9a re-targeted; the inventories unchanged.
  - **§4, the reproduction.**
  - **§5, `## Remaining boundary`:** none for `multi-corpus-session`; limitations per spec §10.
  - **§6, main integration:** filled at merge.
  - **§7, execution rulings.**
- [ ] **Step 2: `roadmap_status.py`.** Add `43: ("conformance-cut-43-results §2", "J12, J13, J14, J15", ""),` and regenerate Appendix A.
- [ ] **Step 3: Ledger and roadmap.**
  - **Ledger:** `multi-corpus-session` built and closed.
  - **Roadmap:** `**Ranked at:** cut 43`. Add a `**Cut 43 (<date>) discharges the multi-corpus session and closes the boundary**` paragraph: tier 1 **on the path**, the second-project milestone's kernel prerequisite (spec §9). The `write-path` lane row is closed again with this boundary named, and the on-path section notes that science's `sci-923d3a` and `beliefs-c08725` are the milestone's remaining prerequisites.
- [ ] **Step 4: Amendments.** Append a dated `## Session-mounts amendment — <date>` section to the writer-session design, covering:
  - §3.1's signature and checks;
  - limitation 1's first sentence retired, its second (cross-corpus targeting) kept;
  - J9's two-root clause pointing at J12;
  - reconciliation matching by corpus;
  - `compile_mount_profile`.
- [ ] **Step 5: Status lines, README, guide, tasks**, then commit:

```bash
tasks done <Task 7's id> "results record, re-rank at cut 43, writer-session amendment"
tasks check && git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut43): results record, re-rank at cut 43, J12–J15 closed"
```

---

### Task 8: Final review, gate, merge

- [ ] **Step 1: Whole-branch review.** Run `superpowers:requesting-code-review` over `git diff main...HEAD`, against the spec's decisions, the Global Constraints' pins and the Review Focus. Land each fix as its own commit and record it in the results record §3.
- [ ] **Step 2: The gate, harness-tracked.** Launch with the Bash tool, `run_in_background: true`: `cd ~/d/beliefs/.worktrees/session-mounts && cd "$(pwd -P)" && set -o pipefail && just gate 2>&1 | tee ~/d/beliefs/.work/acceptance/cut43-gate.log`. Expected: the pytest summary line with zero failures, and the TypeScript suite green.
- [ ] **Step 3: Close and merge**

```bash
tasks done <Task 8's id> "final review, gate green, merged"
tasks done beliefs-fe7149 "cut 43 discharged: one write root, every configured corpus mounted under its own pins, coordination over all, corpus-matched reconciliation"
tasks check && git add tasks && git commit -m "chore(tasks): close beliefs-fe7149 — cut 43 discharged"
cd ~/d/beliefs && git merge --no-ff design/session-mounts -m "merge: the multi-corpus session — conformance cut 43"
```

Fill the results record's §6 on `main`. Then remove the worktree:
1. check that no host pointer resolves into it;
2. `git worktree unlock .worktrees/session-mounts`;
3. `git worktree remove .worktrees/session-mounts`.

Tell science's owner that `sci-923d3a` can start: the kernel now takes `write_root`, `mounts` and `compile_mount_profile`.

---

## Self-review

**Spec coverage.**

| Spec section | Where |
|---|---|
| §1, decisions 1–4 | Task 2 |
| decision 5 | Task 1 |
| decision 6 | Task 2 (`_mount_resolver`; no chain check on read mounts) |
| decision 7 | Task 2 (the writer factory binds `root`), J15-a |
| decision 8 | Task 3, J15-b, J15-c |
| decision 9 | Task 1 (no cache) |
| decision 10 | Tasks 0 and 5 |
| §3.1 | Task 1 |
| §3.2 | Task 2 |
| §4 | Task 4's J14-a |
| §5, §6 | the Global Constraints' pins; Task 5 Step 0 |
| §7 | Tasks 0 (bank), 4, 5, 7 (close) |
| §8.1 | Tasks 1–3 |
| §8.2 | Task 4 |
| §8.3 | Task 2 (J9a), Task 5 (arms) |
| §8.4 | Task 5 |
| §9 | Task 7 |
| §10 | the cut document §7 |
| §11 | Task 0 Step 4 (children) |

**Placeholders.** Two by instruction: the `CorpusManifest` constructor shape (with the helper to follow), and `proposition`'s profile fallback.

**Type consistency.**
- `compile_mount_profile(root, *, available=()) -> ProfileSpec`; `MountPinUnresolved(root, namespace, pin)`.
- `open_attended_session(config, ops, *, write_root, profile, mounts=None, store_root=None, snapshot_resolver=None, project=None)`; `_mount_resolver(mounted)`.
- `committed_pairs: set[tuple[str, str]]`.
- The units are J12-a through J15-c; the arm rows share their names.

**Review Focus.** Task 2 (1, 4), Task 1 (2, 3), Task 3 (5).

## Plan review log

- 2026-09-27 — drafted from the spec approved after two reviews. Found at planning and recorded in the spec's §13:
  - the `biology` fixture is the test-local contract, and the acceptance corpora's pins are adjusted because §8.2's B cannot pin the one namespace twice;
  - J12c's sabotage binds the whole session to `corpus_roots[0]`;
  - nine units, one per arm;
  - `mounts=None`, never an empty mapping.

  Sequencing: cut 43 chains cut 42, so Task 5 starts after `design/publish` merges. Tasks 0–4 do not wait.
- 2026-09-27 — user review of the plan, round 1, three P2 findings, each confirmed by the reviewer's probe, all taken:
  1. **J15-a's sabotage failed before the write.** Redirecting the writer to B kept A's profile, so construction refused `ContractMismatch`. The acceptance corpora gain D, a read mount with A's profile, and the sabotage rebinds the factory's root, and with it the operation port, to D. The write lands there, and the unchanged-tree assertion fails.
  2. **The malformed pin expected the wrong refusal.** It is `load_manifest`'s `ManifestMalformed`, which propagates (§3.1). It has its own test now, and `MountPinUnresolved` covers only well-formed pins nothing carries.
  3. **The acceptance fixture had no teardown.** `corpora` now owns a `mkdtemp` directory under the certified work directory, holding every root, metadata sibling, world, link and operations root. It removes that directory at teardown, and no longer imports `adopted`.

  Also: the planning note's A and B profiles were swapped and are corrected; Task 0 waits for publish's Task 0, enforced by Step 1's scan because the two task records live on different branches.
