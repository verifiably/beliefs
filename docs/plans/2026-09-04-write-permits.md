# Write Permits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every `beliefs` write entry point requires a permit bound with an actor at construction, before its first effect, and a static inventory holds that set of entry points closed — conformance cut 16, rows E1–E8.

**Architecture:** A new `beliefs/permit.py` owns the closed act families, the `KIND_ACTS` route map, `WritePermit`, `Authority(permit, actor)`, `RequiredCapabilities` and `permit_covers`; `errors.py` gains `PermitExceeded` and `ActorMismatch`. `Authority` enters at five construction seams (`open_corpus`/`CorpusWriter`, the `OperationPort`, `open_world`/`World`, the holdings `ActContext`, the root lifecycle acts) and every definition that calls a write primitive starts with one bare `authority.require(<family>, <kinds>)` statement. A static AST test in the S8 style holds the inventory closed in both directions; a durable acceptance suite, N2 arms and a runner discharge cut 16 on the certified volume.

**Tech Stack:** Python 3.11+ under `uv` (`python/`), pytest, ruff, pyright basic; the `atoms` engine on a certified volume for acceptance; git for freeze pins.

**Spec:** `docs/designs/2026-09-04-write-permits-design.md` (frozen at `c2f87b3`: §7 the E table, §9 cut 16). Task 1 adds §13, the implementation amendment, before any code.

## Global Constraints

- Work in the worktree `.worktrees/write-permits` on branch `design/write-permits`. Every command below runs from `python/` inside that worktree unless it says otherwise.
- Gates before every commit: `uv run --frozen pytest -q -p no:cacheprovider`, `uv run --frozen ruff check .`, `uv run --frozen pyright` — all clean.
- **Frozen text stays frozen.** Never edit §7 or §9 of the design. Amendments go in §13 (Task 1) and in §10.
- **The permit check is one bare statement.** In every inventoried definition the first statement after the docstring that has any effect is `<receiver>.require("<family>", (...))` as an expression statement at the top level of the body — never inside `with`, `if`, `try` (except the run boundary's exact shape, Task 7), `for`, a boolean expression or a comprehension. No `mkdir`, no byte mutation and no primitive call may precede it. Family names are string literals.
- **No `actor` parameter** on any inventoried definition or public function of `corpus.py`, `boundary.py`, `replay.py`, `root.py`, `holdings/boundary.py`, `world/registry.py`, `world/epoch.py`, `world/rules.py`, `world/anchors.py`, except `root.audit_log` and `holdings.boundary.intent_payload`. Where the removed parameter's *name* appears in a pinned prior-cut sabotage string (`boundary.py` — `actor` in `AssessmentRunIntent(...)`, `OperationIntent(...)`, `_refused(...)`; `holdings/boundary.py` — `ctx.actor`), keep the spelling alive as a local variable `actor = port.authority.actor` or the `ActContext.actor` property so those pinned blocks still match.
- **Pinned sabotage blocks must keep matching exactly once.** After every task that edits `src/beliefs`, run the staleness probe:

```bash
uv run --frozen python - <<'EOF'
import importlib, sys
from pathlib import Path
sys.path[:0] = ["tests", "tests/acceptance"]
import beliefs
package = Path(beliefs.__file__).resolve().parent
stale = []
for cut in (3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
    arms = getattr(importlib.import_module(f"n2_arms_cut{cut}"), f"CUT{cut}_ARMS")
    for arm in arms:
        n = (package / arm.sabotage.module).read_text(encoding="utf-8").count(arm.sabotage.before)
        if n != 1:
            stale.append((cut, arm.row, arm.sabotage.module, n))
print("stale:", stale)
assert stale == [(10, "H4u1", "holdings/boundary.py", 0), (10, "J8", "holdings/boundary.py", 0)] or stale == [], stale
EOF
```

  Before Task 8 the expected output is `stale: []`. From Task 8 on, exactly the two cut-10 `_publish` arms (`H4u1`, `J8`) are stale, by design (§13 cites cut 10). Anything else stale is a defect in the task that introduced it.
- Test helper for a full authority: `tests/authority.py` (Task 2) exports `FULL`, `ACTOR`, `narrowed(...)`. Every migrated test uses it; no test builds a `WritePermit` literal except the permit tests themselves.
- Task records: `tasks start <child id>` before each task, `tasks done <child id> "<what landed>"` in the task's final commit, `tasks check` before every commit. Never edit `tasks/*.md` by hand.
- Commit messages are conventional commits with no AI attribution trailer.

---

## File map

| file | responsibility |
|---|---|
| `python/src/beliefs/permit.py` (new) | `ACT_FAMILIES`, `COMMAND_REACHABLE_FAMILIES`, `KIND_ACTS`, `require_actor`, `WritePermit`, `Authority`, `RequiredCapabilities`, `permit_covers` |
| `python/src/beliefs/errors.py` | `PermitFact`, `PermitSummary`, `PermitExceeded(WriteRefused)`, `ActorMismatch(WriteRefused)` |
| `python/src/beliefs/runrecord.py` | `OperationPort.authority` on the protocol |
| `python/src/beliefs/corpus.py` | `CorpusWriter(authority=)`, the six corpus-write checks, `adopt_manifest`'s lifecycle check, `ActorMismatch` on `retract` and run-closure `add`, `import_bundle` member-by-member |
| `python/src/beliefs/root.py` | `DurableOperationPort(authority=)`, `open_corpus`, `open_world`, the lifecycle acts, `anchor_heads`/`admit_arrival` wrappers |
| `python/src/beliefs/boundary.py`, `replay.py` | run-family checks with the exact `try` shape; `actor` read from the port |
| `python/src/beliefs/holdings/boundary.py` | `ActContext.authority` (+ `actor` property), holdings checks in `recheck`, `write`, `delete`, `move`, `_append`, `_publish` |
| `python/src/beliefs/world/registry.py`, `epoch.py`, `rules.py`, `anchors.py`, `verify.py` | `World.authority`; registry and epoch checks; `_require_actor` single-homed |
| `python/tests/authority.py` (new) | the shared full authority |
| `python/tests/test_permit.py` (new) | E1 (value level), E4, E5 |
| `python/tests/test_permit_boundary.py` (new) | E6 — the static inventory, five arms, offender and satisfied modules |
| `python/tests/acceptance/test_permit_acceptance.py` (new) | E1, E2, E7, E8 over real roots |
| `python/tests/acceptance/n2_arms_cut16.py`, `test_n2_cut16.py`, `python/tools/cut16_acceptance.py` (new) | the cut |
| `docs/designs/2026-09-04-write-permits-design.md` §10, §13 | amendment and accounting |
| `docs/plans/2026-09-04-conformance-cut-16-results.md` (new, Task 14) | discharge |

---

### Task 1: The implementation amendment (§13) and the task record

**Files:**
- Modify: `docs/designs/2026-09-04-write-permits-design.md` (append §13 after §12; touch nothing in §7 or §9)
- Modify: `tasks/beliefs-96a24a.md` via the `tasks` CLI only

**Interfaces:**
- Consumes: the frozen design; cut 14 §11 as the amendment precedent; the pinned-arm survey below.
- Produces: the rulings every later task implements: (a) cut 10 is cited, not run, from cut 16's tree onward; (b) cut 16's runner names an explicit module inventory rather than chaining `cut15_acceptance.py`; (c) the `actor` local and `ActContext.actor` property; (d) E6's inventory-side mutations are inline unit arms, not N2 sabotages; (e) `_admit_arrival` reads `world.authority`, `_audit_log` keeps its label; (f) `dataset` not required by the run boundary is already §3.2's ruling. The commit hash of this task is `IMPLEMENTATION_AMENDMENT_COMMIT` in Task 13.

- [ ] **Step 1: Verify the survey the amendment rests on**

Run from `python/`:

```bash
grep -n "def _publish" tests/acceptance/n2_arms_cut10.py | head
grep -n "PREFIX_RUNNERS\|PHASE_MODULES" tools/cut14_acceptance.py tools/cut15_acceptance.py
```

Expected: two cut-10 arms (`H4u1` at about line 290 and `J8` at about line 515) carry `def _publish(...)`'s whole body as their `before`; cut 15 chains `cut14_acceptance.py`, which runs `test_n2_cut10.py` as a phase module.

- [ ] **Step 2: Append §13 to the design**

Append, verbatim, at the end of `docs/designs/2026-09-04-write-permits-design.md`:

```markdown
## 13. Implementation amendment — 2026-09-04

This section amends the implementation mechanics after checking the frozen
design against the current tree. It does not rewrite §7's or §9's frozen
bodies. Where it changes a cut disposition it is the current ruling, and the
cut-16 results record cites both the freeze (`c2f87b3`) and this amendment.

### 13.1 Cut 10 is cited, not run

Two frozen cut-10 arms, `H4u1` and `J8`, sabotage the **entire body** of
`holdings.boundary._publish`. E6 requires `_publish` to begin with its
`require` statement, so from this tree onward those two `before` blocks
match nothing and cut 10's audit would report them stale. On cut 9's and
cut 14's exact mechanism: the whole cut-10 surface — its design, its
declaration file, its acceptance module and its runner — is left
byte-identical and pinned so by cut 16's checks; cut 10 is **cited, not
run**, from cut 16's tree onward, its discharge standing as
`../plans/2026-08-24-conformance-cut-10-results.md`; and the successor
coverage for the two arms is carried by cut 16's own `E1` and `E7` holdings
arms plus one labeled unit, `K1`, that re-declares `H4u1`'s sabotage —
dropping the `publish_fulfilling` call — over the new `_publish` body, with
`H4u1`'s check co-cited. The eight other cut-10 arms keep matching, because
`ActContext.actor` survives as a read-only property (§13.3).

### 13.2 The runner names an inventory

§9.3's "names `cut15_acceptance.py` as its prefix runner" cannot hold
literally: that runner chains `cut14_acceptance.py`, which runs
`test_n2_cut10.py`, and both runners' probes call the lifecycle acts by
their pre-permit signatures. `tools/cut16_acceptance.py` therefore names
**no prefix runner** and defines the current-tree prefix as cut 14's module
inventory less `test_n2_cut10.py`, followed by cut 15's three phase modules,
then its own — the exact ordered list Task 13 of the implementation plan
fixes. The two older runners are left unchanged, the frozen commands of the
trees they discharged on. Cuts after 16 name `cut16_acceptance.py`.

### 13.3 Names that pinned sabotages spell

Pinned cut-3 and cut-11 arms sabotage `boundary.py` lines that spell the
name `actor` (`AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)`,
`_refused("no-frozen-spec", subject, actor, observer, started_at)`, …), and
pinned cut-10 arms spell `ctx.actor`. Removing the `actor` *parameter* is
§4.2's rule; the *name* survives as a local, `actor = port.authority.actor`,
bound immediately after the run boundary's `try` shape, and as a read-only
`ActContext.actor` property over `authority.actor`. Neither is a parameter
and neither is caller-supplied; the pinned blocks keep matching.

### 13.4 E6's inventory-side mutations are inline arms

§9.3 lists sabotages "in `test_permit_boundary.py`'s own inventory". The N2
harness copies `src/beliefs` alone, so a test file cannot be an N2 sabotage
target. Those mutations are carried instead as the static test's own
offender arms (§5 arm 5), run inline in the unit suite; the N2 arms for E6
sabotage the package (remove or displace a `require`) and are checked by the
static test.

### 13.5 Two seam details

`world.verify._admit_arrival` drops its `actor` keyword and reads
`world.authority`; `_audit_log` keeps `actor` as the label its report
carries (§4.2). `install_shipped_world_rules` needs no signature change: it
reaches `install_rule_binding`, which requires on `world.authority`.

### 13.6 `_fork_resume` is a primitive implementation

A pinned cut-9 arm spells `fork_corpus`'s retry block verbatim —
`pending = _fork_pending(dest)` … `_fork_resume(dest, pending)` … — so
`_fork_resume` can take no authority. It is the one body that invokes the
engine's `resume_fork_root` callback with the production tuple, exactly as
`_store_append_intent` is the one body that invokes `append_intent`: §4.3's
implementation list gains `root.py:_fork_resume`, compared by equality like
the rest, and §4.2's lifecycle row loses it. Its two callers, `fork_corpus`
and `fork_store`, are inventoried (each also calls `_fork_root_callback`
directly) and require `lifecycle` as their first statement, before the
pinned block. This narrows the second review finding's remedy without
reopening it: the caller is held, the implementation is named.
```

- [ ] **Step 3: Run the corpus tests and commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_designs_corpus.py
cd .. && tasks check && git add docs/designs/2026-09-04-write-permits-design.md && git commit -m "docs(designs): rule the cut 16 implementation amendment" && git rev-parse --short HEAD
```

Expected: 14 passed; record the printed short hash — it is `IMPLEMENTATION_AMENDMENT_COMMIT` in Task 13.

- [ ] **Step 4: Note the ruling on the task**

```bash
tasks note beliefs-96a24a "Implementation amendment §13 at <hash>: cut 10 cited, runner names an inventory, actor locals keep pinned arms matching"
git add tasks && git commit -m "chore(tasks): note the cut 16 implementation amendment"
```

---

### Task 2: `permit.py` values, `PermitExceeded`, `ActorMismatch`, and the test helper

**Files:**
- Create: `python/src/beliefs/permit.py`
- Modify: `python/src/beliefs/errors.py` (after `ImportRefused`)
- Create: `python/tests/authority.py`
- Test: `python/tests/test_permit.py`

**Interfaces:**
- Consumes: `beliefs.errors.WriteRefused`; `beliefs.identity.v1.encode`.
- Produces:
  - `beliefs.permit.ACT_FAMILIES: frozenset[str]`, `COMMAND_REACHABLE_FAMILIES: frozenset[str]`, `KIND_ACTS: Mapping[str, frozenset[str]]` (read-only), `ActFamily` (a `Literal`).
  - `beliefs.permit.require_actor(actor: object) -> str` — raises `TypeError` for a non-`str`, `ValueError` for an empty or non-encodable string.
  - `beliefs.permit.WritePermit(kinds: frozenset[str], act_families: frozenset[str])`, frozen; `WritePermit.full() -> WritePermit`; `WritePermit.summary() -> PermitSummary`.
  - `beliefs.permit.Authority(permit: WritePermit, actor: str)`, frozen; `Authority.require(family: str, kinds: Iterable[str] = ()) -> None`.
  - `beliefs.errors.PermitFact(dimension: str, name: str)`, `beliefs.errors.PermitSummary(kinds: tuple[str, ...], act_families: tuple[str, ...])`, both frozen dataclasses; `beliefs.errors.PermitExceeded(WriteRefused)` with `.requirement: PermitFact` and `.capability: PermitSummary`; `beliefs.errors.ActorMismatch(WriteRefused)`.
  - `tests/authority.py`: `ACTOR = "test-actor"`, `FULL = Authority(WritePermit.full(), ACTOR)`, `narrowed(*, kinds=(), families=(), actor=ACTOR) -> Authority`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_permit.py`:

```python
"""E1 at value level, E4 and E5 (design §3, §7)."""
from __future__ import annotations

import pytest

from beliefs.coordination import COORDINATION_KINDS
from beliefs.errors import ActorMismatch, PermitExceeded, PermitFact, PermitSummary, WriteRefused
from beliefs.permit import (
    ACT_FAMILIES,
    COMMAND_REACHABLE_FAMILIES,
    KIND_ACTS,
    Authority,
    WritePermit,
    require_actor,
)
from beliefs.stored import WORLD_KINDS


class TestE4KindActsIsClosedAndComplete:
    def test_the_key_set_is_exactly_the_world_and_coordination_kinds(self):
        assert set(KIND_ACTS) == set(WORLD_KINDS) | set(COORDINATION_KINDS)

    def test_every_route_is_an_act_family(self):
        for kind, routes in KIND_ACTS.items():
            assert routes and routes <= ACT_FAMILIES, kind

    def test_the_routes_are_the_banked_ones(self):
        assert KIND_ACTS["run"] == {"run", "corpus-write"}
        assert KIND_ACTS["dataset"] == {"corpus-write"}
        assert KIND_ACTS["act-report"] == {"corpus-write", "run"}
        assert KIND_ACTS["holdings-observation"] == {"holdings"}
        for kind in COORDINATION_KINDS:
            assert KIND_ACTS[kind] == {"corpus-write"}

    def test_the_mapping_is_read_only(self):
        with pytest.raises(TypeError):
            KIND_ACTS["proposition"] = frozenset()  # type: ignore[index]

    def test_the_families_are_the_six_and_three_are_command_reachable(self):
        assert ACT_FAMILIES == {"corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"}
        assert COMMAND_REACHABLE_FAMILIES == {"corpus-write", "run", "holdings"}


class TestWritePermitConstruction:
    def test_full_holds_every_kind_and_family(self):
        full = WritePermit.full()
        assert full.kinds == frozenset(KIND_ACTS)
        assert full.act_families == ACT_FAMILIES

    def test_an_unknown_kind_or_family_is_refused(self):
        with pytest.raises(ValueError, match="kind"):
            WritePermit(frozenset({"unicorn"}), frozenset())
        with pytest.raises(ValueError, match="family"):
            WritePermit(frozenset(), frozenset({"publish"}))

    def test_only_exact_frozensets_of_strings_construct(self):
        with pytest.raises(TypeError):
            WritePermit({"proposition"}, frozenset())  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            WritePermit(frozenset({1}), frozenset())  # type: ignore[arg-type]

    def test_summary_is_sorted_plain_data(self):
        permit = WritePermit(frozenset({"source", "proposition"}), frozenset({"run", "corpus-write"}))
        assert permit.summary() == PermitSummary(("proposition", "source"), ("corpus-write", "run"))


class TestRequireActor:
    def test_an_exact_encodable_string_passes(self):
        assert require_actor("alice") == "alice"

    def test_non_strings_and_empty_strings_refuse(self):
        with pytest.raises(TypeError):
            require_actor(b"alice")
        with pytest.raises(ValueError):
            require_actor("")


class TestE1AuthorityRequire:
    def test_a_missing_family_is_refused_on_the_family_before_any_kind(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        with pytest.raises(PermitExceeded) as caught:
            authority.require("run", ("proposition",))
        assert caught.value.requirement == PermitFact("family", "run")
        assert caught.value.capability == PermitSummary(("proposition",), ("corpus-write",))
        assert str(caught.value).startswith("permit exceeded: family run is not permitted")

    def test_the_first_missing_kind_in_the_callers_order_is_named(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        with pytest.raises(PermitExceeded) as caught:
            authority.require("corpus-write", ("proposition", "source", "dataset"))
        assert caught.value.requirement == PermitFact("kind", "source")

    def test_an_exact_requirement_passes_and_returns_nothing(self):
        authority = Authority(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), "a")
        assert authority.require("corpus-write", ("proposition",)) is None
        assert authority.require("corpus-write") is None

    def test_an_unknown_family_is_a_caller_error_not_a_refusal(self):
        with pytest.raises(ValueError):
            Authority(WritePermit.full(), "a").require("publish")

    def test_permit_exceeded_is_a_write_refusal_and_actor_mismatch_too(self):
        assert issubclass(PermitExceeded, WriteRefused)
        assert issubclass(ActorMismatch, WriteRefused)

    def test_authority_fixes_the_actor_by_the_one_rule(self):
        with pytest.raises(TypeError):
            Authority(WritePermit.full(), 7)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            Authority(WritePermit.full(), "")
        with pytest.raises(TypeError):
            Authority("full", "a")  # type: ignore[arg-type]
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_permit.py
```

Expected: collection error — `ModuleNotFoundError: No module named 'beliefs.permit'`.

- [ ] **Step 3: Add the error types**

In `python/src/beliefs/errors.py`, after the `ImportRefused` class, append:

```python
@dataclass(frozen=True)
class PermitFact:
    """One side of a permit refusal: the family or the kind an act needed."""

    dimension: str  # "family" | "kind"
    name: str


@dataclass(frozen=True)
class PermitSummary:
    """A permit as plain data: sorted kinds, sorted act families."""

    kinds: tuple[str, ...]
    act_families: tuple[str, ...]


class PermitExceeded(WriteRefused):
    """An act named a family or a kind the bound permit does not hold
    (write-permits design §3.6). Raised before any effect; `requirement` and
    `capability` are the structured fields the refusal envelope carries."""

    def __init__(self, requirement: PermitFact, capability: PermitSummary) -> None:
        super().__init__(f"permit exceeded: {requirement.dimension} {requirement.name} is not permitted")
        self.requirement = requirement
        self.capability = capability


class ActorMismatch(WriteRefused):
    """A record names an actor other than the bound one — a retraction's
    facet, or a run closure's occurrence through the add path (design §4.2).
    Not a permit refusal: the permit may well cover the kind."""
```

Add `from dataclasses import dataclass` to the imports at the top of `errors.py` if it is not already there (check with `grep -n "^from dataclasses" src/beliefs/errors.py`).

- [ ] **Step 4: Write `permit.py`**

`python/src/beliefs/permit.py`:

```python
"""Write permits (design `docs/designs/2026-09-04-write-permits-design.md` §3).

The closed act families, the kind-to-route map, the permit value, and the
authority every write entry point requires of before its first effect. This
module imports nothing that writes: `errors` and the identity encoding only,
so every seam can import it without a cycle.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from beliefs.errors import PermitExceeded, PermitFact, PermitSummary
from beliefs.identity import v1

__all__ = [
    "ACT_FAMILIES",
    "COMMAND_REACHABLE_FAMILIES",
    "KIND_ACTS",
    "ActFamily",
    "Authority",
    "RequiredCapabilities",
    "WritePermit",
    "permit_covers",
    "require_actor",
]

ActFamily = Literal["corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"]

ACT_FAMILIES: frozenset[str] = frozenset({"corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"})
"""The closed enumeration. `publish` arrives by sub-project 5's amendment."""

COMMAND_REACHABLE_FAMILIES: frozenset[str] = frozenset({"corpus-write", "run", "holdings"})
"""Command-framework §4.4 as data: the families a write class may map to."""

_CORPUS_WRITE = frozenset({"corpus-write"})
_COORDINATION_KINDS = ("project", "question", "hypothesis", "topic", "theme", "task", "decision", "note")

KIND_ACTS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "proposition": _CORPUS_WRITE,
        "source-assertion": _CORPUS_WRITE,
        "assessment": _CORPUS_WRITE,
        "analysis-spec": _CORPUS_WRITE,
        "run": frozenset({"run", "corpus-write"}),
        "verification": _CORPUS_WRITE,
        "dataset": _CORPUS_WRITE,
        "source": _CORPUS_WRITE,
        "holdings-observation": frozenset({"holdings"}),
        "retraction": _CORPUS_WRITE,
        "instrument-certification": _CORPUS_WRITE,
        "coreference-attestation": _CORPUS_WRITE,
        "act-report": frozenset({"corpus-write", "run"}),
        **{kind: _CORPUS_WRITE for kind in _COORDINATION_KINDS},
    }
)
"""Every mintable kind to the families admissible as its minting route —
validation data, never a requirement derivation (§3.2). `test_permit.py`
holds the key set equal to `stored.WORLD_KINDS ∪ coordination.COORDINATION_KINDS`."""


def require_actor(actor: object) -> str:
    """The one actor rule: an exact, non-empty, `v1`-encodable string."""
    if type(actor) is not str:
        raise TypeError("actor must be an exact string")
    if not actor:
        raise ValueError("actor must be a non-empty string")
    try:
        v1.encode(actor)
    except Exception as caught:
        raise ValueError(f"actor is not encodable: {caught}") from caught
    return actor


def _require_closed(values: object, universe: frozenset[str], dimension: str) -> frozenset[str]:
    if type(values) is not frozenset or any(type(value) is not str for value in values):
        raise TypeError(f"{dimension}s must be an exact frozenset of strings")
    unknown = sorted(values - universe)
    if unknown:
        raise ValueError(f"unknown {dimension}{'s' if len(unknown) > 1 else ''}: {unknown}")
    return values


@dataclass(frozen=True)
class WritePermit:
    """Two closed dimensions (§3.3). `full()` is the only convenience."""

    kinds: frozenset[str]
    act_families: frozenset[str]

    def __post_init__(self) -> None:
        _require_closed(self.kinds, frozenset(KIND_ACTS), "kind")
        _require_closed(self.act_families, ACT_FAMILIES, "act family")

    @classmethod
    def full(cls) -> WritePermit:
        return cls(frozenset(KIND_ACTS), ACT_FAMILIES)

    def summary(self) -> PermitSummary:
        return PermitSummary(tuple(sorted(self.kinds)), tuple(sorted(self.act_families)))


@dataclass(frozen=True)
class Authority:
    """A permit and an actor, bound once at a construction seam (§3.4)."""

    permit: WritePermit
    actor: str

    def __post_init__(self) -> None:
        if type(self.permit) is not WritePermit:
            raise TypeError("permit must be a WritePermit")
        require_actor(self.actor)

    def require(self, family: str, kinds: Iterable[str] = ()) -> None:
        """Refuse before any effect, naming the family or the first missing
        kind in the caller's order. No other outcome."""
        if family not in ACT_FAMILIES:
            raise ValueError(f"{family!r} is not an act family")
        if family not in self.permit.act_families:
            raise PermitExceeded(PermitFact("family", family), self.permit.summary())
        for kind in kinds:
            if kind not in self.permit.kinds:
                raise PermitExceeded(PermitFact("kind", kind), self.permit.summary())
```

(`RequiredCapabilities` and `permit_covers` are Task 3; leave them out of `__all__` until then — remove the two names from `__all__` for now and add them back in Task 3.)

- [ ] **Step 5: Write the test helper**

`python/tests/authority.py`:

```python
"""The one full authority every migrated test binds (design §9.2)."""
from __future__ import annotations

from collections.abc import Iterable

from beliefs.permit import ACT_FAMILIES, KIND_ACTS, Authority, WritePermit

ACTOR = "test-actor"
FULL = Authority(WritePermit.full(), ACTOR)


def narrowed(*, kinds: Iterable[str] = (), families: Iterable[str] = (), actor: str = ACTOR) -> Authority:
    """A permit holding exactly these kinds and families."""
    return Authority(WritePermit(frozenset(kinds), frozenset(families)), actor)


def lacking(*, kinds: Iterable[str] = (), families: Iterable[str] = (), actor: str = ACTOR) -> Authority:
    """The full permit minus exactly these kinds and families."""
    return Authority(
        WritePermit(frozenset(KIND_ACTS) - frozenset(kinds), ACT_FAMILIES - frozenset(families)), actor
    )
```

- [ ] **Step 6: Run the tests, gates, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_permit.py
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks check && git add python/src/beliefs/permit.py python/src/beliefs/errors.py python/tests/authority.py python/tests/test_permit.py && git commit -m "feat(permit): closed act families, KIND_ACTS, WritePermit and Authority"
```

Expected: `test_permit.py` all passing; the full suite unchanged.

---

### Task 3: `RequiredCapabilities` and `permit_covers`

**Files:**
- Modify: `python/src/beliefs/permit.py`
- Test: `python/tests/test_permit.py`

**Interfaces:**
- Consumes: Task 2's values.
- Produces: `RequiredCapabilities(permit: WritePermit)` frozen, with classmethods `none()`, `coordination()`, `for_kinds(kinds: Iterable[str], routes: Mapping[str, str])`, `publishes()` (raises `ValueError`); `permit_covers(ceiling: WritePermit, required: RequiredCapabilities) -> bool`. These are the names the `science` plan's Task 12 *Consumes* block pins.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_permit.py`:

```python
from beliefs.permit import RequiredCapabilities, permit_covers  # noqa: E402


class TestE4RequirementConstruction:
    def test_none_requires_nothing(self):
        assert RequiredCapabilities.none().permit == WritePermit(frozenset(), frozenset())

    def test_coordination_requires_the_coordination_kinds_over_corpus_write(self):
        required = RequiredCapabilities.coordination().permit
        assert required.kinds == frozenset(COORDINATION_KINDS)
        assert required.act_families == {"corpus-write"}

    def test_a_single_route_kind_derives_its_route(self):
        required = RequiredCapabilities.for_kinds(["proposition"], {}).permit
        assert required == WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"}))

    def test_an_ambiguous_kind_must_select_a_route(self):
        with pytest.raises(ValueError, match="route"):
            RequiredCapabilities.for_kinds(["run"], {})

    def test_a_selected_route_must_be_admissible(self):
        with pytest.raises(ValueError, match="admit"):
            RequiredCapabilities.for_kinds(["run"], {"run": "holdings"})

    def test_a_selected_route_is_the_requirement(self):
        required = RequiredCapabilities.for_kinds(["run", "proposition"], {"run": "run"}).permit
        assert required == WritePermit(frozenset({"run", "proposition"}), frozenset({"run", "corpus-write"}))

    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(ValueError, match="unknown"):
            RequiredCapabilities.for_kinds(["unicorn"], {})

    def test_a_route_key_outside_the_kinds_is_refused_even_when_admissible(self):
        with pytest.raises(ValueError, match="declared"):
            RequiredCapabilities.for_kinds(["proposition"], {"run": "run"})

    def test_publishes_is_refused_while_publish_is_not_a_family(self):
        with pytest.raises(ValueError, match="publish is not an act family"):
            RequiredCapabilities.publishes()

    def test_a_requirement_never_names_a_non_command_family(self):
        for required in (RequiredCapabilities.none(), RequiredCapabilities.coordination(),
                         RequiredCapabilities.for_kinds(["run"], {"run": "run"})):
            assert required.permit.act_families <= COMMAND_REACHABLE_FAMILIES


class TestE5Coverage:
    def test_full_covers_every_constructible_requirement(self):
        full = WritePermit.full()
        for required in (RequiredCapabilities.none(), RequiredCapabilities.coordination(),
                         RequiredCapabilities.for_kinds(list(KIND_ACTS), {"run": "run", "act-report": "run"})):
            assert permit_covers(full, required)

    def test_an_empty_requirement_is_covered_by_the_empty_permit(self):
        assert permit_covers(WritePermit(frozenset(), frozenset()), RequiredCapabilities.none())

    def test_coverage_is_subset_inclusion_on_both_dimensions(self):
        required = RequiredCapabilities.for_kinds(["proposition"], {})
        assert not permit_covers(WritePermit(frozenset(), frozenset({"corpus-write"})), required)
        assert not permit_covers(WritePermit(frozenset({"proposition"}), frozenset()), required)
        assert permit_covers(WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"})), required)

    def test_coverage_judges_the_selected_route_not_the_union(self):
        required = RequiredCapabilities.for_kinds(["run"], {"run": "corpus-write"})
        assert permit_covers(WritePermit(frozenset({"run"}), frozenset({"corpus-write"})), required)
        assert not permit_covers(WritePermit(frozenset({"run"}), frozenset({"run"})), required)
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_permit.py
```

Expected: `ImportError: cannot import name 'RequiredCapabilities'`.

- [ ] **Step 3: Implement**

Append to `python/src/beliefs/permit.py` (and restore the two names to `__all__`):

```python
@dataclass(frozen=True)
class RequiredCapabilities:
    """What a declaration needs (§3.5). Compiled to a permit whose families
    are exactly the selected routes; never a union over `KIND_ACTS`."""

    permit: WritePermit

    def __post_init__(self) -> None:
        if type(self.permit) is not WritePermit:
            raise TypeError("a requirement carries a WritePermit")
        if not self.permit.act_families <= COMMAND_REACHABLE_FAMILIES:
            raise ValueError("a requirement names only command-reachable families")

    @classmethod
    def none(cls) -> RequiredCapabilities:
        return cls(WritePermit(frozenset(), frozenset()))

    @classmethod
    def coordination(cls) -> RequiredCapabilities:
        return cls(WritePermit(frozenset(_COORDINATION_KINDS), _CORPUS_WRITE))

    @classmethod
    def for_kinds(cls, kinds: Iterable[str], routes: Mapping[str, str]) -> RequiredCapabilities:
        declared = frozenset(kinds)
        unknown = sorted(declared - frozenset(KIND_ACTS))
        if unknown:
            raise ValueError(f"unknown kinds: {unknown}")
        stray = sorted(frozenset(routes) - declared)
        if stray:
            raise ValueError(f"routes name kinds the class does not declare: {stray}")
        families: set[str] = set()
        for kind in sorted(declared):
            admissible = KIND_ACTS[kind]
            if kind in routes:
                route = routes[kind]
                if route not in admissible:
                    raise ValueError(f"KIND_ACTS does not admit route {route!r} for {kind!r}")
            elif len(admissible) == 1:
                (route,) = admissible
            else:
                raise ValueError(f"{kind!r} admits more than one route; the declaration must select one")
            families.add(route)
        return cls(WritePermit(declared, frozenset(families)))

    @classmethod
    def publishes(cls) -> RequiredCapabilities:
        raise ValueError("publish is not an act family")


def permit_covers(ceiling: WritePermit, required: RequiredCapabilities) -> bool:
    """Subset inclusion on both dimensions and nothing else (E5)."""
    if type(ceiling) is not WritePermit or type(required) is not RequiredCapabilities:
        raise TypeError("permit_covers judges a WritePermit against a RequiredCapabilities")
    return required.permit.kinds <= ceiling.kinds and required.permit.act_families <= ceiling.act_families
```

- [ ] **Step 4: Run, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_permit.py
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks check && git add python && git commit -m "feat(permit): RequiredCapabilities and permit_covers"
```

---

### Task 4: The corpus construction seam — port, writer, `open_corpus` (E2)

**Files:**
- Modify: `python/src/beliefs/runrecord.py:88-94` (the `OperationPort` protocol)
- Modify: `python/src/beliefs/root.py` (`DurableOperationPort.__init__` ~930; `open_corpus` ~1640)
- Modify: `python/src/beliefs/corpus.py` (`CorpusWriter.__init__` ~1099)
- Modify (fake ports and constructions): `python/tests/test_operation_port.py`, `test_import_bundle.py`, `fixtures_cut3.py`, `test_corpus_write.py`, `test_manifest.py`, `test_coordination_write.py`, `test_retract.py`, `test_supersede.py`, `test_revise.py`, `coordination_fixtures.py`, `test_world_build.py`, `test_world_epoch.py`, `test_stored_display.py`, `test_holdings_stored.py`, `test_root.py`, `test_holdings_windows.py`, `test_holdings_receipt.py`, `test_holdings_capture.py`, `succession_fixtures.py`, `test_run_persistence.py`, `tests/acceptance/conftest.py`, `tests/acceptance/test_intent_boundary_acceptance.py`, `tests/acceptance/test_cut15_lineage.py`, `tests/acceptance/test_n2_cut6.py`, `test_n2_cut7.py`, `test_durable_families.py`, `test_coordination_acceptance.py`, `test_world_arrival.py`
- Test: `python/tests/test_corpus_write.py` (new E2 tests)

**Interfaces:**
- Consumes: `beliefs.permit.Authority`; `tests/authority.FULL`.
- Produces: `OperationPort.authority` (read-only property on the protocol; every port implements it); `DurableOperationPort(root, *, backend, storage, metadata_root, authority)`; `CorpusWriter(root, executor_factory, *, authority, operation_port=None, coordination_resolver=None)` with `CorpusWriter.authority` property; `open_corpus(corpus_root, *, authority, coordination_resolver=None)`. Construction of a writer over a port whose authority differs raises `ValueError`.

- [ ] **Step 1: Write the failing E2 tests**

Append to `python/tests/test_corpus_write.py` (its `Recorder` executor and `writer` fixture already exist near the top):

```python
from authority import FULL, narrowed  # noqa: E402
from beliefs.permit import Authority  # noqa: E402


class TestE2AuthorityBindsOnceAtConstruction:
    def test_a_writer_requires_an_authority_keyword(self, tmp_path):
        with pytest.raises(TypeError):
            CorpusWriter(tmp_path, Recorder)  # type: ignore[call-arg]

    def test_the_bound_authority_is_readable_and_not_settable(self, tmp_path):
        writer = CorpusWriter(tmp_path, Recorder, authority=FULL)
        assert writer.authority is FULL
        with pytest.raises(AttributeError):
            writer.authority = FULL  # type: ignore[misc]

    def test_a_port_bound_to_another_authority_refuses_construction(self, tmp_path):
        class Port:
            authority = narrowed(kinds=("proposition",), families=("corpus-write",))

            def append_intent(self, payload):
                raise AssertionError("never reached")

            def execute(self, plan):
                raise AssertionError("never reached")

            def execute_fulfilling(self, plan, fulfills):
                raise AssertionError("never reached")

        with pytest.raises(ValueError, match="another authority"):
            CorpusWriter(tmp_path, Recorder, authority=FULL, operation_port=Port())

    def test_two_writers_over_one_port_with_its_own_authority_both_construct(self, tmp_path):
        class Port:
            authority = FULL

            def append_intent(self, payload):
                raise AssertionError("never reached")

            def execute(self, plan):
                raise AssertionError("never reached")

            def execute_fulfilling(self, plan, fulfills):
                raise AssertionError("never reached")

        port = Port()
        assert CorpusWriter(tmp_path, Recorder, authority=FULL, operation_port=port).authority is FULL
        assert CorpusWriter(tmp_path, Recorder, authority=FULL, operation_port=port).authority is FULL

    def test_an_authority_must_be_an_authority(self, tmp_path):
        with pytest.raises(TypeError):
            CorpusWriter(tmp_path, Recorder, authority="full")  # type: ignore[arg-type]
```

Add `import pytest` and `from beliefs.corpus import CorpusWriter` at the top if the module does not import them already.

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_corpus_write.py -k E2
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'authority'` on the second test and failures on the rest.

- [ ] **Step 3: Extend the protocol and the durable port**

`python/src/beliefs/runrecord.py` — the protocol becomes:

```python
class OperationPort(Protocol):
    @property
    def authority(self) -> Authority: ...

    def append_intent(self, payload: bytes) -> str: ...

    def execute(self, plan: WritePlan) -> None: ...

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None: ...
```

with `from beliefs.permit import Authority` among the imports.

`python/src/beliefs/root.py` — `DurableOperationPort`:

```python
class DurableOperationPort:
    def __init__(
        self, root: Path, *, backend: Backend, storage: StorageProfile, metadata_root: Path, authority: Authority
    ) -> None:
        if type(authority) is not Authority:
            raise TypeError("a port binds an Authority")
        self.root = Path(root)
        self._backend = backend
        self._storage = storage
        self._metadata_root = Path(metadata_root)
        self._authority = authority

    @property
    def authority(self) -> Authority:
        return self._authority
```

and `open_corpus`:

```python
def open_corpus(
    corpus_root: Path, *, authority: Authority, coordination_resolver: CoordinationResolver | None = None
) -> CorpusWriter:
    """... (keep the docstring) ..."""
    root = Path(corpus_root).resolve()
    return CorpusWriter(
        root,
        durable_executor_factory(),
        authority=authority,
        operation_port=DurableOperationPort(
            root,
            backend=_PRODUCTION_BACKEND,
            storage=PRODUCTION_STORAGE,
            metadata_root=metadata_root_for(root),
            authority=authority,
        ),
        coordination_resolver=coordination_resolver,
    )
```

Import `Authority` from `beliefs.permit` in `root.py`.

- [ ] **Step 4: Bind the writer**

`python/src/beliefs/corpus.py` — `CorpusWriter.__init__`:

```python
    def __init__(
        self,
        root: Path,
        executor_factory: Callable[[Path], WritePlanExecutor],
        *,
        authority: Authority,
        operation_port: OperationPort | None = None,
        coordination_resolver: CoordinationResolver | None = None,
    ) -> None:
        if type(authority) is not Authority:
            raise TypeError("a writer binds an Authority")
        if operation_port is not None and operation_port.authority != authority:
            raise ValueError("the operation port is bound to another authority than this writer")
        self._authority = authority
        self._state = _root_state_for(root, executor_factory)
        self._operation = self._state.lock
        self._operation_port = operation_port
        self._coordination_resolver = coordination_resolver

    @property
    def authority(self) -> Authority:
        return self._authority
```

Import `Authority` from `beliefs.permit` in `corpus.py`. (`OperationPort` is already imported from `runrecord`.)

- [ ] **Step 5: Migrate every construction in the tests**

Mechanical rules, applied file by file (open each and edit; do not regex blindly — some `World(` matches are unrelated):

1. Every `CorpusWriter(<root>, <factory>` call gains `, authority=FULL` (keyword, after the factory), and the file gains `from authority import FULL` (tests import sibling modules by bare name, as `from n2_arms import Arm` does).
2. Every `open_corpus(<root>` call gains `, authority=FULL` — including `tests/acceptance/conftest.py`'s `durable_writer` fixture and `durable_coordination_roots`.
3. Every `DurableOperationPort(` construction and `durable_port(...)` helper: `test_operation_port.py`'s `durable_port(tmp_path)` becomes `durable_port(tmp_path, authority=FULL)` with `authority=authority` passed through; update its five callers (`succession_fixtures.py`, `test_run_persistence.py`, `acceptance/test_intent_boundary_acceptance.py`, `acceptance/test_cut15_lineage.py`) to pass `authority=FULL`, or give the helper the default `authority: Authority = FULL` so callers stay unchanged — choose the default: it is a test helper, not a seam.
4. Every fake port class gains `authority = FULL` as a class attribute: `test_operation_port.FakePort`, `test_import_bundle.FakePort`, `fixtures_cut3.MemoryPort`, and any other class in `tests/` defining `append_intent` (find them with `grep -rn "def append_intent" tests`).
5. Do **not** touch `tests/acceptance/test_n2_cut5.py`, `n2_arms_cut5.py`, `n2_arms_cut10.py`, `test_n2_cut10.py` or any `n2_arms_cut*.py` — pinned.

- [ ] **Step 6: Run the suite, the staleness probe, gates, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider
uv run --frozen pyright && uv run --frozen ruff check .
```

Then the staleness probe from Global Constraints (expected `stale: []`), then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): bind Authority at the corpus writer, the port and open_corpus"
```

Expected: full suite green (pyright will point at every construction you missed; fix each by rule 1–4).

---

### Task 5: The corpus-write checks — `add`, `retract`, `supersede`, `revise`, coordination, `adopt_manifest` (E1, E3)

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`add` ~1125, `mint_coordination` ~1138, `revise_coordination` ~1171, `adopt_manifest` ~1348, `retract` ~1470, `supersede` ~1496, `revise` ~1529)
- Test: `python/tests/test_corpus_write.py`, `python/tests/test_retract.py`

**Interfaces:**
- Consumes: Task 4's bound writer.
- Produces: each method's first statement is its `require`; `retract` and run-closure `add` raise `ActorMismatch`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_corpus_write.py`:

```python
from beliefs.errors import ActorMismatch, PermitExceeded, PermitFact  # noqa: E402
from beliefs.runrecord import publication_plan  # noqa: E402
from nodes.core.frontmatter import node_from_markdown  # noqa: E402


class TestE1CorpusWriteRequiresBeforeAnyEffect:
    def test_add_under_a_permit_lacking_the_family_refuses_and_writes_nothing(self, tmp_path):
        Recorder.plans = []
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("proposition",), families=("run",)))
        with pytest.raises(PermitExceeded) as caught:
            writer.add(observed_dataset())
        assert caught.value.requirement == PermitFact("family", "corpus-write")
        assert Recorder.plans == []

    def test_add_under_a_permit_lacking_the_kind_names_the_kind(self, tmp_path):
        Recorder.plans = []
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("proposition",), families=("corpus-write",)))
        with pytest.raises(PermitExceeded) as caught:
            writer.add(observed_dataset())
        assert caught.value.requirement == PermitFact("kind", "dataset")
        assert Recorder.plans == []

    def test_add_under_the_exact_requirement_mints(self, tmp_path):
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("dataset",), families=("corpus-write",)))
        assert writer.add(observed_dataset()).kind == "dataset"

    def test_adopt_manifest_is_a_lifecycle_act(self, tmp_path):
        from beliefs.consulted import CorpusPins

        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(families=("corpus-write",)))
        with pytest.raises(PermitExceeded) as caught:
            writer.adopt_manifest(profile=CorpusPins(science_contract="sha256:" + "0" * 64, domains={}))
        assert caught.value.requirement == PermitFact("family", "lifecycle")
        assert not (tmp_path / "corpus.yaml").exists()


class TestE3TheActorIsBound:
    def test_a_run_closure_naming_another_actor_is_refused_through_add(self, tmp_path):
        from fixtures_cut3 import minted_closure  # a RunClosure whose occurrence.actor == "tester"

        _, _, (operation,) = publication_plan(minted_closure())
        node = node_from_markdown(operation.content.decode("utf-8"))
        Recorder.plans = []
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("run",), families=("corpus-write",), actor="someone-else"))
        with pytest.raises(ActorMismatch):
            writer.add(node)
        assert Recorder.plans == []

    def test_the_same_closure_under_its_own_actor_mints(self, tmp_path):
        from fixtures_cut3 import minted_closure

        _, _, (operation,) = publication_plan(minted_closure())
        node = node_from_markdown(operation.content.decode("utf-8"))
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("run",), families=("corpus-write",), actor="tester"))
        assert writer.add(node).kind == "run"

    def test_a_run_record_without_a_closure_carries_no_actor_and_mints(self, tmp_path):
        writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("run",), families=("corpus-write",), actor="someone-else"))
        node = stored.run_node("r1", title="run", spec="analysis-spec:s1")
        assert writer.add(node).kind == "run"
```

`fixtures_cut3.minted_closure` may not exist under that name: open `tests/fixtures_cut3.py`, find the helper that builds a `RunClosure` with `actor="tester"` (around lines 300–330, the one feeding `closure_fixtures`), and use its real name; if none returns a closure directly, use `closure_fixtures.make_closure()` (imported by `test_intent_boundary_acceptance.py`) — check its occurrence actor with `make_closure().occurrence.actor` and use that value in place of `"tester"`.

Append to `python/tests/test_retract.py` (it has a `retraction(...)` helper building `stored.retraction_node(..., actor="tester", ...)` near line 62, and a `writer` fixture):

```python
from authority import narrowed  # noqa: E402
from beliefs.errors import ActorMismatch  # noqa: E402


def test_e3_a_retraction_naming_another_actor_is_refused(tmp_path):
    writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("assessment", "retraction"), families=("corpus-write",), actor="not-tester"))
    target = writer.add(admissible_assessment())  # use this module's existing helper that mints a retractable target
    with pytest.raises(ActorMismatch):
        writer.retract(retraction(target, "invalid"))


def test_e3_a_retraction_under_its_own_actor_mints(tmp_path):
    writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("assessment", "retraction"), families=("corpus-write",), actor="tester"))
    target = writer.add(admissible_assessment())
    assert writer.retract(retraction(target, "invalid")).kind == "retraction"
```

Replace `admissible_assessment()` and `retraction(target, "invalid")` with the module's real helper names (read the file's first 120 lines).

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_corpus_write.py -k "E1 or E3" tests/test_retract.py -k e3
```

Expected: the refusal tests fail because no `PermitExceeded`/`ActorMismatch` is raised (the writes succeed).

- [ ] **Step 3: Add the checks**

In `python/src/beliefs/corpus.py`:

```python
    def add(self, node: Node) -> Node:
        """... keep docstring ..."""
        self._authority.require("corpus-write", (node.kind,))
        with self._operation:
            self._refuse_family_kinds(node)
            self._refuse(node)
            self._refuse_foreign_closure_actor(node)
            return self._corpus.add(node)
```

```python
    def mint_coordination(self, kind: str, *, project: CoordinationAddress | None = None, content: Mapping[str, object]) -> Node:
        self._authority.require("corpus-write", (kind,))
        with self._operation:
            ...unchanged...

    def revise_coordination(self, kind: str, address: CoordinationAddress, *, predecessors: Sequence[str], content: Mapping[str, object]) -> Node:
        self._authority.require("corpus-write", (kind,))
        with self._operation:
            ...unchanged...
```

```python
    def adopt_manifest(self, *, profile: CorpusPins) -> CorpusManifest:
        """Create this corpus's first closed manifest."""
        self._authority.require("lifecycle")
        from beliefs.world import CorpusManifest, _parse_manifest, manifest_bytes

        with self._operation:
            ...unchanged...
```

```python
    def retract(self, record: Node) -> Node:
        """Mint one locally resolvable retraction without touching its target."""
        self._authority.require("corpus-write", ("retraction",))
        with self._operation:
            self._refuse_family_kinds(record, admitted_kind="retraction")
            facet = record.facets.get(stored.RETRACTION_FACET)
            if isinstance(facet, dict) and facet.get("actor") != self._authority.actor:
                raise ActorMismatch(
                    f"{record.id}: the retraction names actor {facet.get('actor')!r}, not the bound {self._authority.actor!r}"
                )
            try:
                self._validated_retraction(record)
            ...unchanged...
```

```python
    def supersede(self, successor: Node, *, of: str) -> Node:
        """Mint a proposition successor without touching its predecessor."""
        self._authority.require("corpus-write", ("proposition",))
        with self._operation:
            ...unchanged...

    def revise(self, node: Node) -> Node:
        """Replace a proposition after changing display prose alone."""
        self._authority.require("corpus-write", ("proposition",))
        with self._operation:
            ...unchanged...
```

And the helper, beside `_refuse_family_kinds`:

```python
    def _refuse_foreign_closure_actor(self, node: Node) -> None:
        """A run closure through the add path names the bound actor or refuses (E3).
        Import members are provenance and never pass here."""
        if node.kind != "run" or stored.RUN_CLOSURE_FACET not in node.facets:
            return
        from beliefs.runrecord import decode_run_closure  # runrecord imports production, which reads corpora

        named = decode_run_closure(node).occurrence.actor
        if named != self._authority.actor:
            raise ActorMismatch(f"{node.id}: the run closure names actor {named!r}, not the bound {self._authority.actor!r}")
```

Add `ActorMismatch` (and `PermitExceeded` is not needed here) to the `from beliefs.errors import (...)` block. If `from beliefs.runrecord import decode_run_closure` can be a module-level import without a cycle (`uv run --frozen python -c "import beliefs.corpus"` succeeds with it at the top), prefer the module-level import.

Note the pinned cut-5 blocks around `return self._corpus.add(candidate)` / `return self._corpus.add(record)` and the cut-6 `adopt_manifest` blocks are untouched by these insertions.

- [ ] **Step 4: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider
uv run --frozen ruff check . && uv run --frozen pyright
```

Staleness probe: expected `stale: []`. Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): require the corpus-write and lifecycle permits on the writer's families"
```

---

### Task 6: `import_bundle` member by member (E8)

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`import_bundle` ~1372)
- Modify: `python/tests/test_import_bundle.py`, `tests/acceptance/test_coordination_acceptance.py`, `tests/acceptance/test_durable_families.py`, `tests/test_operation_port.py` (every `import_bundle(` caller drops `actor=`)
- Test: `python/tests/test_import_bundle.py`

**Interfaces:**
- Produces: `CorpusWriter.import_bundle(records, *, observer, instrument, opened_at, closed_at)` — no `actor`; the intent's actor is `self.authority.actor`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_import_bundle.py` (its `writer_with_port` fixture and `FakePort` exist; `member` there is a `source` or `proposition` node — read lines 55–80 for the exact helper):

```python
from authority import ACTOR, narrowed  # noqa: E402
from beliefs.errors import PermitExceeded, PermitFact  # noqa: E402
from beliefs.identity import v1  # noqa: E402


def _import(writer, members):
    return writer.import_bundle(members, observer="o", instrument="i", opened_at="T0", closed_at="T1")


def test_e8_one_unpermitted_member_refuses_the_bundle_before_the_intent(tmp_path):
    FakePort.intents, FakePort.executed, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(
        tmp_path, Recorder, authority=narrowed(kinds=("proposition", "act-report"), families=("corpus-write",)),
        operation_port=FakePort(tmp_path),
    )
    with pytest.raises(PermitExceeded) as caught:
        _import(writer, [proposition_member("p1"), stored.source_node("s1", title="s", identifiers={"doi": "10.1/x"})])
    assert caught.value.requirement == PermitFact("kind", "source")
    assert FakePort.intents == [] and FakePort.executed == [] and FakePort.fulfilling == []


def test_e8_a_permit_lacking_act_report_refuses_before_the_intent(tmp_path):
    FakePort.intents, FakePort.executed, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(
        tmp_path, Recorder, authority=narrowed(kinds=("proposition",), families=("corpus-write",)),
        operation_port=FakePort(tmp_path),
    )
    with pytest.raises(PermitExceeded) as caught:
        _import(writer, [proposition_member("p1")])
    assert caught.value.requirement == PermitFact("kind", "act-report")
    assert FakePort.intents == []


def test_e8_every_member_kind_plus_act_report_imports_with_one_fulfilling_report(tmp_path):
    FakePort.intents, FakePort.executed, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(
        tmp_path, Recorder, authority=narrowed(kinds=("proposition", "act-report"), families=("corpus-write",)),
        operation_port=FakePort(tmp_path),
    )
    report = _import(writer, [proposition_member("p1")])
    assert report.actor == ACTOR
    assert len(FakePort.intents) == 1 and len(FakePort.fulfilling) == 1


def test_e3_the_import_intent_carries_the_bound_actor(writer_with_port):
    FakePort.intents = []
    _import(writer_with_port, [proposition_member("p2")])
    assert v1.decode(FakePort.intents[0])["actor"] == ACTOR


def test_e3_an_imported_member_naming_a_foreign_actor_is_stored_verbatim(tmp_path):
    from fixtures_cut3 import minted_closure  # as in Task 5
    from nodes.core.frontmatter import node_from_markdown
    from beliefs.runrecord import decode_run_closure, publication_plan

    _, _, (operation,) = publication_plan(minted_closure())
    node = node_from_markdown(operation.content.decode("utf-8"))
    writer = CorpusWriter(tmp_path, Recorder, authority=narrowed(kinds=("run", "act-report"), families=("corpus-write",), actor="importer"), operation_port=FakePort(tmp_path))
    _import(writer, [node])
    stored_node = writer.read_view.get(node.id)  # use the ReadView's real lookup method (see corpus.ReadView)
    assert decode_run_closure(stored_node).occurrence.actor == "tester"
```

`proposition_member` is the module's existing member helper — use its real name. `v1.decode` exists in `beliefs.identity.v1`; if only `encode` is exported, decode with `json.loads` (the wire is canonical JSON). `ReadView.get` — read `corpus.ReadView` for the lookup by id; use its real method.

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_import_bundle.py -k "e8 or e3"
```

Expected: `TypeError: import_bundle() missing 1 required keyword-only argument: 'actor'`.

- [ ] **Step 3: Implement**

`import_bundle` becomes:

```python
    def import_bundle(
        self,
        records: Sequence[Node],
        *,
        observer: str,
        instrument: str,
        opened_at: str,
        closed_at: str,
    ) -> report_values.ActReport:
        """Admit one validated bundle in one payload transaction.

        Judged member by member before the intent (E8): one unpermitted kind
        refuses the bundle whole. Members are stored verbatim — an imported
        record naming another actor is provenance, attributed to the importer
        by the intent (design §4.2)."""
        try:
            bundle = tuple(records)
        except TypeError as caught:
            raise ImportRefused("an import bundle must be a sequence of records") from caught
        self._authority.require(
            "corpus-write", (*(record.kind for record in bundle if type(record) is Node), "act-report")
        )
        actor = self._authority.actor
        with self._operation:
            if not bundle:
                raise ImportRefused("an import bundle must not be empty")
            for name, value in (
                ("observer", observer),
                ("instrument", instrument),
                ("opened_at", opened_at),
                ("closed_at", closed_at),
            ):
                if type(value) is not str or not value:
                    raise ImportRefused(f"import {name} must be a non-empty string")
            ...everything from `try: v1.encode({...` onward unchanged; `actor` is now the local...
```

The `try: bundle = tuple(records)` block moves above `with`; the `("actor", actor)` entry leaves the field loop. Everything else in the body, including the pinned cut-5 `append_intent(` lines, stays byte-identical.

- [ ] **Step 4: Migrate the callers**

Remove `actor=...,` from every `import_bundle(` call in `tests/test_import_bundle.py`, `tests/test_operation_port.py`, `tests/acceptance/test_coordination_acceptance.py`, `tests/acceptance/test_durable_families.py`. Where a test asserted the report's `actor` equals the removed literal, assert `ACTOR` instead. (`tests/acceptance/test_n2_cut5.py` is pinned and cited; leave it.)

- [ ] **Step 5: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
```

Probe: `stale: []`. Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): judge import bundles member by member before the intent"
```

---

### Task 7: The run boundary and replay (E7)

**Files:**
- Modify: `python/src/beliefs/boundary.py` (`execute_assessment_run` ~790, `execute_production_run` ~859; the errors import block ~65)
- Modify: `python/src/beliefs/replay.py:110-160`
- Modify: `python/tests/fixtures_cut3.py` (the `memory_*` wrappers and every `actor="tester"` passed to a run entry point), `fixtures_cut15.py`, `test_boundary.py`, `test_world_log_evaluator.py`, `test_world_log_replay.py`, `n2_arms_cut3.py` is pinned — leave it
- Test: `python/tests/test_boundary.py`

**Interfaces:**
- Produces: `execute_assessment_run(*, spec, port, boundary_policy, expected_recipe_identity=None, definition, code_roots, held_inputs, entrypoint, targets, declared_outputs, observer, started_at, host_realization, scratch_base, cores=1)`; the same removal of `actor` on `execute_production_run` and `replay.replay`; a `PermitExceeded` becomes `RunRefused("permit-exceeded", None, None, None, detail)`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_boundary.py` (it imports `execute_assessment_run`, `RunRefused`, `stage`, `freeze`, `spec_draft`, `spec_rules`, `definition`, `MINIMAL_POLICY`, `DATA_ADDRESS`, `READS_ADDRESS` already — check the top of the file and add any missing):

```python
from authority import FULL, narrowed  # noqa: E402
from fixtures_cut3 import MemoryPort  # noqa: E402


class _NarrowPort(MemoryPort):
    def __init__(self, authority):
        self.authority = authority
        self.appended = []

    def append_intent(self, payload: bytes) -> str:
        self.appended.append(payload)
        return super().append_intent(payload)

    def execute(self, plan) -> None:
        raise AssertionError("a refused run must not write")

    def execute_fulfilling(self, plan, fulfills: str) -> None:
        raise AssertionError("a refused run must not write")


def _assessment(tmp_path, port, **overrides):
    code, held = stage(tmp_path)
    kwargs = dict(
        spec=freeze(spec_draft(), held_rules=spec_rules()),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(),
        code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=tmp_path / "scratch",
    )
    kwargs.update(overrides)
    return execute_assessment_run(**kwargs)


def test_e7_a_permit_lacking_run_refuses_with_no_intent_and_no_report(tmp_path):
    port = _NarrowPort(narrowed(kinds=("run", "act-report"), families=("corpus-write",)))
    outcome = _assessment(tmp_path, port)
    assert isinstance(outcome, RunRefused)
    assert outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None and outcome.registration is None
    assert "family run" in outcome.detail
    assert port.appended == []


def test_e7_a_permit_lacking_act_report_refuses_before_the_intent(tmp_path):
    port = _NarrowPort(narrowed(kinds=("run",), families=("run",)))
    outcome = _assessment(tmp_path, port)
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert "kind act-report" in outcome.detail
    assert port.appended == []


def test_e7_a_non_permit_refusal_after_the_check_still_mints_its_report(tmp_path):
    class Port(MemoryPort):
        authority = FULL
        executed = []

        def execute(self, plan) -> None:
            self.executed.append(plan)

    port = Port()
    outcome = _assessment(tmp_path, port, spec="not-a-frozen-spec")
    assert isinstance(outcome, RunRefused) and outcome.reason == "no-frozen-spec"
    assert outcome.report is not None and len(port.executed) == 1


def test_e3_the_run_intent_carries_the_ports_actor(tmp_path):
    class Port(MemoryPort):
        authority = narrowed(kinds=("run", "act-report"), families=("run",), actor="port-actor")
        appended = []

        def append_intent(self, payload: bytes) -> str:
            self.appended.append(payload)
            return super().append_intent(payload)

    port = Port()
    _assessment(tmp_path, port)
    assert b'"actor":"port-actor"' in port.appended[0] or b"port-actor" in port.appended[0]


def test_the_run_entry_points_take_no_actor(tmp_path):
    with pytest.raises(TypeError):
        _assessment(tmp_path, MemoryPort(), actor="tester")
```

`MemoryPort` in `fixtures_cut3.py` must have `authority = FULL` from Task 4; subclasses above override it.

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_boundary.py -k "e7 or e3 or no_actor"
```

Expected: `TypeError: execute_assessment_run() missing 1 required keyword-only argument: 'actor'`.

- [ ] **Step 3: Implement the exact `try` shape in both run entry points**

In `python/src/beliefs/boundary.py`, remove `actor: str,` from the signatures of `execute_assessment_run` and `execute_production_run`, and make each body begin:

```python
    try:
        port.authority.require("run", ("run", "act-report"))
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    actor = port.authority.actor
    if type(spec) is not FrozenSpec:
        ...unchanged...
```

(`execute_production_run`'s first original statement is `if type(inputs) is not tuple ...`; the three inserted statements go before it.) Every later use of `actor` in both bodies is the local, so the pinned cut-3 and cut-11 lines (`AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)`, `OperationIntent("run-attempt", secrets.token_hex(16), actor)`, every `_refused(...)` line) remain byte-identical. Add `PermitExceeded` to the `from beliefs.errors import (...)` block.

`replay.replay`: remove `actor: str,` from the signature and the `"actor": actor,` entry from `common`.

- [ ] **Step 4: Migrate the fixtures and tests**

- `tests/fixtures_cut3.py`: remove `actor="tester"` from every call that reaches `run_assessment`/`run_production`/`replay_of`/`execute_*` (lines ~509, ~574, ~629 — confirm each is a run call and not an `Occurrence`/report construction, which keep their `actor`).
- `tests/fixtures_cut15.py:243`, `tests/test_boundary.py` (every `actor="tester"` keyword on a run call), `tests/test_world_log_evaluator.py`, `tests/test_world_log_replay.py` (`replay(` calls): remove the keyword. Where a test asserts the minted `Occurrence.actor == "tester"`, it now equals the port's actor (`ACTOR`); update the assertion.
- `tests/n2_arms_cut3.py`, `tests/acceptance/n2_arms_cut11.py`: pinned — untouched.

- [ ] **Step 5: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
```

Probe: `stale: []` (the cut-3 and cut-11 blocks must still match — if any is stale, the `actor` local is missing or a line was reflowed). Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): run boundary requires the run permit and refuses without an intent"
```

---

### Task 8: Holdings — `ActContext.authority` and the six holdings checks

**Files:**
- Modify: `python/src/beliefs/holdings/boundary.py` (`ActContext` ~69, `_publish` ~76, `recheck` ~89, `_append` ~120, `write` ~127, `delete` ~147, `move` ~156)
- Modify: `python/tests/test_holdings_boundary.py`, `test_holdings_capture.py`, `test_holdings_windows.py` (every `ActContext(` construction)
- Test: `python/tests/test_holdings_boundary.py`

**Interfaces:**
- Produces: `ActContext(observer_root, store_root, observer, instrument, authority, seam)` with a read-only `actor` property returning `authority.actor`; each of `recheck`, `write`, `delete`, `move`, `_append`, `_publish` begins with `ctx.authority.require("holdings", ("holdings-observation",))`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_holdings_boundary.py` (its `context(certified_work)` helper builds the `ActContext` at line ~47 and returns `(ctx, store_id)`):

```python
from dataclasses import replace  # noqa: E402

from authority import ACTOR, FULL, narrowed  # noqa: E402
from beliefs.errors import PermitExceeded, PermitFact  # noqa: E402


def _chain_len(root):
    from beliefs import root as science_root
    from beliefs.world.logmodel import WellFormedView

    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return len(view.entries)


def test_e1_a_permit_lacking_holdings_refuses_recheck_before_the_intent(certified_work):
    ctx, store_id = context(certified_work)
    ctx = replace(ctx, authority=narrowed(kinds=("holdings-observation",), families=("corpus-write",)))
    before = _chain_len(ctx.observer_root)
    with pytest.raises(PermitExceeded) as caught:
        recheck(ctx, StoreLocator(store_id, "held.bin"))
    assert caught.value.requirement == PermitFact("family", "holdings")
    assert _chain_len(ctx.observer_root) == before


def test_e1_a_permit_lacking_the_observation_kind_refuses_write_before_any_store_effect(certified_work):
    ctx, store_id = context(certified_work)
    ctx = replace(ctx, authority=narrowed(families=("holdings",)))
    with pytest.raises(PermitExceeded) as caught:
        write(ctx, StoreLocator(store_id, "held.bin"), b"bytes")
    assert caught.value.requirement == PermitFact("kind", "holdings-observation")
    assert not (ctx.store_root / "held.bin").exists()


def test_e1_the_exact_holdings_requirement_publishes(certified_work):
    ctx, store_id = context(certified_work)
    ctx = replace(ctx, authority=narrowed(kinds=("holdings-observation",), families=("holdings",)))
    assert write(ctx, StoreLocator(store_id, "held.bin"), b"bytes").record.outcome is not None


def test_e3_the_holdings_intent_carries_the_bound_actor(certified_work):
    ctx, store_id = context(certified_work)
    assert ctx.actor == ACTOR
    ctx = replace(ctx, authority=narrowed(kinds=("holdings-observation",), families=("holdings",), actor="store-actor"))
    assert ctx.actor == "store-actor"
    write(ctx, StoreLocator(store_id, "held.bin"), b"bytes")
    from beliefs import root as science_root
    from beliefs.world.logmodel import IntentEntryView

    view = science_root._log_seam().inspect_registered(ctx.observer_root)
    intents = [entry for entry in view.entries if type(entry) is IntentEntryView]
    assert b"store-actor" in intents[-1].payload


def test_act_context_takes_no_actor_field():
    with pytest.raises(TypeError):
        ActContext(Path("a"), Path("b"), "observer", "instrument", "actor", holdings_seam())  # type: ignore[arg-type]
```

Read `beliefs.world.logmodel.IntentEntryView` for the payload attribute's real name and use it.

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_holdings_boundary.py -k "e1 or e3 or no_actor"
```

Expected: `TypeError` from `replace(ctx, authority=...)` (no such field) and the rest failing.

- [ ] **Step 3: Implement**

`python/src/beliefs/holdings/boundary.py`:

```python
@dataclass(frozen=True)
class ActContext:
    observer_root: Path
    store_root: Path
    observer: str
    instrument: str
    authority: Authority
    seam: StoreActSeam

    def __post_init__(self) -> None:
        if type(self.authority) is not Authority:
            raise TypeError("an act context binds an Authority")

    @property
    def actor(self) -> str:
        """The bound actor — a read, never a field (design §13.3)."""
        return self.authority.actor
```

Then, as the **first statement** of each of `_publish`, `recheck`, `_append`, `write`, `delete`, `move`:

```python
    ctx.authority.require("holdings", ("holdings-observation",))
```

Everything else in each body stays byte-identical (`_publish`'s existing lines included — its pinned cut-10 blocks go stale by design; every other pinned cut-10 block, which starts at a line after the inserted statement or inside `recheck`/`move`, keeps matching). Import `Authority` from `beliefs.permit`.

- [ ] **Step 4: Migrate the constructions**

In `tests/test_holdings_boundary.py`, `test_holdings_capture.py`, `test_holdings_windows.py`: every `ActContext(observer_root, store_root, "observer", "instrument", "actor", seam)` becomes `ActContext(observer_root, store_root, "observer", "instrument", FULL, seam)`; where a test asserted the intent's actor was `"actor"`, assert `ACTOR`.

- [ ] **Step 5: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
```

Probe: from here on the expected output is exactly `stale: [(10, 'H4u1', 'holdings/boundary.py', 0), (10, 'J8', 'holdings/boundary.py', 0)]`. Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): holdings acts require the holdings permit on the bound context"
```

---

### Task 9: The world seam — `open_world`, `World.authority`, registry and epoch checks

**Files:**
- Modify: `python/src/beliefs/world/registry.py` (`World.__init__` ~236, `admit` ~261, `retire`/`depart`/`_terminal` ~291–312, `_locked_admit` ~322)
- Modify: `python/src/beliefs/world/anchors.py` (`_anchor_heads` ~530; drop its `_require_actor`)
- Modify: `python/src/beliefs/world/epoch.py` (`build_epoch` ~1375, `delete_epoch` ~1686)
- Modify: `python/src/beliefs/world/rules.py` (`install_rule_binding` ~338, `remove_rule_binding` ~509)
- Modify: `python/src/beliefs/world/verify.py` (`_admit_arrival` ~1750: drop `actor`)
- Modify: `python/src/beliefs/root.py` (`open_world` ~1677, `anchor_heads` ~1542, `admit_arrival` ~1600)
- Modify: `python/src/beliefs/world/registry.py`, `anchors.py`, `holdings/boundary.py`, `stored.py`: their actor validators import `require_actor` from `beliefs.permit`
- Modify tests: every `World(` construction (`test_world_registry.py`, `test_world_log_codecs.py`, `test_world_anchor_act.py`, `test_world_rules.py`, `test_world_build.py`, `test_world_derive.py`, `test_holdings_receipt.py`, `test_world_receipts.py`, `test_world_epoch.py`, `test_holdings_windows.py`, `test_holdings_capture.py`, `test_world_log_audit.py`, `test_world_arrival.py`, `test_world_read.py`, `test_world_gc.py`, `test_store_subjects.py`, `test_arrival_modes.py`, `test_world_log_evaluator.py`), every `open_world(` (`test_root.py`, `test_world_build.py`, `test_world_rules.py`, `test_arrival_modes.py`, `test_world_log_audit.py`, `acceptance/conftest.py`, `acceptance/test_n2_cut6.py`, `acceptance/test_n2_cut7.py`), every `.admit(... actor=)`, `.retire(... actor=)`, `.depart(... actor=)`, `delete_epoch(... actor=)`, `anchor_heads(... actor=)`, `_anchor_heads(... actor=)`, `admit_arrival(... actor=)`, `_admit_arrival(... actor=)`
- Test: `python/tests/test_world_registry.py`, `python/tests/test_world_gc.py`

**Interfaces:**
- Produces: `World(config, executor_factory, *, chain_head, corpus_executor_factory, authority)` with `World.authority`; `open_world(config, *, authority)`; `World.admit(corpus_root, *, provenance)`, `World.retire(corpus_id)`, `World.depart(corpus_id)`; `epoch.delete_epoch(world, packaging_identity)`; `anchors._anchor_heads(world, corpus_ids, *, store_roots=(), seam)`; `root.anchor_heads(world, corpus_ids, *, store_roots=())`; `root.admit_arrival(world, corpus_root, provenance, observers, *, history=None)`; `verify._admit_arrival(world, corpus_root, provenance, observers, *, history=None, seam)`; `root.audit_log` unchanged.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_world_registry.py` (its `make_world(tmp_path, *corpus_roots)` helper at line ~48 builds a `World` over `DefaultExecutor`):

```python
from authority import ACTOR, FULL, narrowed  # noqa: E402
from beliefs.errors import PermitExceeded, PermitFact  # noqa: E402


def _registry_files(world_root):
    directory = world_root / "registry"
    return sorted(p.name for p in directory.glob("*.yaml")) if directory.exists() else []


def test_e1_admit_under_a_permit_lacking_registry_refuses_and_writes_nothing(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)  # this module's manifest helper
    world = world_module.World(
        world_module.WorldConfig(tmp_path / "world", "f" * 32, (corpus,)),
        DefaultExecutor, chain_head=unread_chain, corpus_executor_factory=DefaultExecutor,
        authority=narrowed(families=("epoch",)),
    )
    with pytest.raises(PermitExceeded) as caught:
        world.admit(corpus, provenance=world_module.Fresh())
    assert caught.value.requirement == PermitFact("family", "registry")
    assert _registry_files(tmp_path / "world") == []


def test_e3_an_admission_carries_the_bound_actor_and_takes_none(tmp_path):
    corpus = tmp_path / "corpus"
    write_manifest(corpus, "1" * 32)
    world = make_world(tmp_path, corpus)
    record = world.admit(corpus, provenance=world_module.Fresh())
    assert record.actor == ACTOR
    with pytest.raises(TypeError):
        world.retire(record.corpus_id, actor="alice")  # type: ignore[call-arg]
    assert world.retire(record.corpus_id).actor == ACTOR


def test_e2_open_world_and_world_require_an_authority(tmp_path):
    with pytest.raises(TypeError):
        world_module.World(
            world_module.WorldConfig(tmp_path / "world", "f" * 32, ()),
            DefaultExecutor, chain_head=unread_chain, corpus_executor_factory=DefaultExecutor,
        )  # type: ignore[call-arg]
```

`make_world` must pass `authority=FULL` after this task. Append to `python/tests/test_world_gc.py` (it builds a world with retained epochs; reuse its fixture that yields `world, first, ...` around line 150):

```python
from authority import narrowed  # noqa: E402
from dataclasses import replace  # noqa: E402
from beliefs.errors import PermitExceeded  # noqa: E402


def test_e1_delete_epoch_under_a_permit_lacking_epoch_refuses_and_keeps_the_members(<the module's retained-epochs fixture>):
    world, first = <unpack per the fixture>
    narrowed_world = world_module.World(
        world.config, world._executor_factory, chain_head=world._chain_head,
        corpus_executor_factory=world._corpus_executor_factory,
        authority=narrowed(families=("registry",)),
    )
    members_before = sorted(p.name for p in (world.config.world_root / "epochs" / first.packaging_identity).iterdir())
    with pytest.raises(PermitExceeded):
        epoch.delete_epoch(narrowed_world, first.packaging_identity)
    assert sorted(p.name for p in (world.config.world_root / "epochs" / first.packaging_identity).iterdir()) == members_before
```

Fill the fixture name and unpacking from the file (read its first 160 lines).

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_world_registry.py -k "e1 or e2 or e3" tests/test_world_gc.py -k e1
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'authority'`.

- [ ] **Step 3: Implement the world seam**

`world/registry.py`:

```python
    def __init__(
        self,
        config: WorldConfig,
        executor_factory: Callable[[Path], WritePlanExecutor],
        *,
        chain_head: Callable[[Path], tuple[str, str]],
        corpus_executor_factory: Callable[[Path], WritePlanExecutor],
        authority: Authority,
    ) -> None:
        if type(authority) is not Authority:
            raise TypeError("a world binds an Authority")
        self.config = config
        self.authority = authority
        ...unchanged...

    def admit(self, corpus_root: Path, *, provenance: AdmissionProvenance) -> AdmissionRecord:
        """... keep docstring ..."""
        if type(provenance) is ReplicaOf:
            raise ReplicaAdmissionRequiresVerification(...unchanged...)
        with self._state.lock:
            return _locked_admit(
                self._state, self.config.world_root, self._executor_factory,
                lambda: load_manifest(corpus_root), provenance, self.authority,
            )

    def retire(self, corpus_id: str) -> StatusRecord:
        return self._terminal(corpus_id, "retired")

    def depart(self, corpus_id: str) -> StatusRecord:
        return self._terminal(corpus_id, "departed")

    def _terminal(self, corpus_id: str, status: Literal["retired", "departed"]) -> StatusRecord:
        self.authority.require("registry")
        with self._state.lock:
            ...unchanged until...
            candidate = StatusRecord(corpus_id, status, self.authority.actor)
            ...unchanged (the pinned `self._executor_factory(self.config.world_root).execute(` block included)...
```

`_locked_admit(state, world_root, executor_factory, manifest_of, provenance, authority: Authority)`: first statement `authority.require("registry")`; `candidate = AdmissionRecord(manifest, provenance, authority.actor)`. Its `_require_actor` definition becomes `from beliefs.permit import require_actor as _require_actor` (the records keep validating their field).

`world/anchors.py` — `_anchor_heads(world, corpus_ids, *, store_roots=(), seam)`: replace the `_require_actor(actor)` line with `world.authority.require("registry")` as the first statement after the docstring, and `origin = AnchorActOrigin(world.authority.actor)`. Its `_require_actor` becomes the `permit` import likewise.

`world/epoch.py` — `build_epoch`: first statement after the docstring `world.authority.require("epoch")`. `delete_epoch(world, packaging_identity)`: first statement `world.authority.require("epoch")`; the line `actor = registry._require_actor(actor)` becomes `actor = world.authority.actor`.

`world/rules.py` — `install_rule_binding` and `remove_rule_binding`: first statement `world.authority.require("epoch")`.

`world/verify.py` — `_admit_arrival(world, corpus_root, provenance, observers, *, history=None, seam)`: drop the `registry._require_actor(actor)` line; pass `world.authority` where it passed `actor` into `_locked_admit`. `_audit_log` keeps `actor`.

`root.py` — `open_world(config, *, authority)` passes `authority=authority` to `World(...)`; `anchor_heads(world, corpus_ids, *, store_roots=())` and `admit_arrival(world, corpus_root, provenance, observers, *, history=None)` drop `actor`.

`holdings/boundary.py` `intent_payload` and `stored.retraction_node` keep their signatures (a serializer and a record constructor) but validate `actor` through `require_actor` from `beliefs.permit` where they validate it today.

- [ ] **Step 4: Migrate the tests**

Rules: every `World(` construction gains `authority=FULL` (keyword); every `open_world(<config>)` becomes `open_world(<config>, authority=FULL)`; remove `actor=` from every `.admit(`, `.retire(`, `.depart(`, `delete_epoch(`, `anchor_heads(`, `_anchor_heads(`, `admit_arrival(`, `_admit_arrival(` call; assertions on those records' `actor` compare to `ACTOR`. `audit_log(... actor=...)` calls stay. `tools/cut*_acceptance.py` and every `n2_arms_cut*.py` stay untouched.

- [ ] **Step 5: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
```

Probe: exactly the two cut-10 arms. Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): world binds an authority; registry and epoch acts require it"
```

---

### Task 10: The root lifecycle acts

**Files:**
- Modify: `python/src/beliefs/root.py` (`init_corpus_root` ~309, `init_world_root` ~341, `init_store_root` ~401, `replicate_root` ~468, `migrate_root_to_lifecycle_v3` ~500, `restore_root` ~516, `_fork_resume` ~567, `fork_corpus` ~576, `fork_store` ~630)
- Modify tests: every `init_corpus_root(`, `init_world_root(`, `init_store_root(`, `fork_corpus(`, `fork_store(`, `replicate_root(`, `restore_root(`, `migrate_root_to_lifecycle_v3(` caller under `tests/` (see the file list in the plan's survey: `test_root.py`, `test_lifecycle_wrappers.py`, `test_operation_port.py`, `test_fork_acts.py`, `test_arrival_modes.py`, `test_restore_root.py`, `test_store_root.py`, `test_holdings_seam.py`, `succession_fixtures.py`, `test_holdings_windows.py`, `test_holdings_capture.py`, `test_holdings_boundary.py`, `test_run_persistence.py`, `test_holdings_receipt.py`, `test_world_build.py`, `test_world_rules.py`, `acceptance/conftest.py`, `acceptance/test_intent_boundary_acceptance.py`, `acceptance/test_n2_cut6.py`, `acceptance/test_n2_cut7.py`, `acceptance/test_cut15_lineage.py`, `acceptance/test_coordination_acceptance.py`, and any other `grep -rln "init_corpus_root(\|init_store_root(\|init_world_root(" tests` hit). **Not** `tools/cut*_acceptance.py`.
- Test: `python/tests/test_lifecycle_wrappers.py`

**Interfaces:**
- Produces: `init_corpus_root(corpus_root, *, authority)`, `init_world_root(config, *, authority)`, `init_store_root(store_root, *, authority) -> str`, `replicate_root(source_root, dest_root, *, authority)`, `migrate_root_to_lifecycle_v3(root, *, authority)`, `restore_root(dest_root, subject, observers, *, authority)`, `fork_corpus(source_root, dest_root, *, authority)`, `fork_store(source_root, dest_root, *, authority)`, `_fork_resume(dest_root, operation_id)` (unchanged, §13.6).

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_lifecycle_wrappers.py` (it uses the `certified_work` fixture):

```python
from authority import FULL, narrowed  # noqa: E402
from beliefs.errors import PermitExceeded, PermitFact  # noqa: E402
from beliefs.root import init_corpus_root, init_world_root, metadata_root_for  # noqa: E402
from beliefs.world import WorldConfig  # noqa: E402


def test_e1_init_corpus_root_under_a_permit_lacking_lifecycle_creates_nothing(certified_work):
    root = certified_work / "never"
    with pytest.raises(PermitExceeded) as caught:
        init_corpus_root(root, authority=narrowed(families=("corpus-write",)))
    assert caught.value.requirement == PermitFact("family", "lifecycle")
    assert not root.exists() and not metadata_root_for(root).exists()


def test_e1_init_world_root_refuses_before_its_mkdir(certified_work):
    root = certified_work / "never-world"
    with pytest.raises(PermitExceeded):
        init_world_root(WorldConfig(root, "0" * 32, ()), authority=narrowed(families=("registry",)))
    assert not root.exists()


def test_e1_the_lifecycle_permit_initializes(certified_work):
    root = certified_work / "corpus"
    init_corpus_root(root, authority=narrowed(families=("lifecycle",)))
    assert metadata_root_for(root).exists()


def test_the_lifecycle_acts_take_no_default_authority(certified_work):
    with pytest.raises(TypeError):
        init_corpus_root(certified_work / "x")  # type: ignore[call-arg]
```

- [ ] **Step 2: Run to verify they fail**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_lifecycle_wrappers.py -k "e1 or no_default"
```

Expected: `TypeError: init_corpus_root() got an unexpected keyword argument 'authority'`.

- [ ] **Step 3: Implement**

Each act gains `*, authority: Authority` and the check as its first statement (after the docstring), before any `mkdir`, `Path(...)` binding or callback:

```python
def init_corpus_root(corpus_root: Path, *, authority: Authority) -> None:
    """... keep docstring ..."""
    authority.require("lifecycle")
    root = Path(corpus_root).resolve()
    ...unchanged...


def init_world_root(config: WorldConfig, *, authority: Authority) -> None:
    authority.require("lifecycle")
    root = config.world_root
    ...unchanged (the mkdir now follows the check)...


def init_store_root(store_root: Path, *, authority: Authority) -> str:
    """... keep docstring ..."""
    authority.require("lifecycle")
    ...unchanged; the pinned cut-9 block `store_root.mkdir(...)\n    existing = _read_existing_store_genesis(store_root)` stays adjacent...


def replicate_root(source_root: Path, dest_root: Path, *, authority: Authority) -> RootOperationId:
    """... keep docstring ..."""
    authority.require("lifecycle")
    ...unchanged...


def migrate_root_to_lifecycle_v3(root: Path, *, authority: Authority) -> None:
    """... keep docstring ..."""
    authority.require("lifecycle")
    target = Path(root)
    _migrate_root_to_lifecycle_v3_callback(...unchanged...)


def restore_root(dest_root, subject, observers, *, authority: Authority) -> LogReport:
    """... keep docstring ..."""
    if type(subject) not in {CorpusSubject, StoreSubject}:
        raise TypeError(...unchanged...)

    def grant(root: Path) -> None:
        authority.require("lifecycle")
        _grant_read_serviceability_callback(...unchanged...)

    return _restore_root(dest_root, subject, observers, seam=_log_seam(), grant=grant)


def _fork_resume(dest_root: Path, operation_id: RootOperationId) -> None:
    """The resume primitive's one body (design §13.6); its callers require."""
    _resume_fork_root_callback(...unchanged...)


def fork_corpus(source_root: Path, dest_root: Path, *, authority: Authority) -> _registry.CorpusManifest:
    """... keep docstring ..."""
    authority.require("lifecycle")
    ...unchanged, the pinned block `pending = _fork_pending(dest)` … `_fork_resume(dest, pending)` included...


def fork_store(source_root: Path, dest_root: Path, *, authority: Authority) -> str:
    """... keep docstring ..."""
    authority.require("lifecycle")
    ...unchanged...
```

Per §13.6, `_fork_resume` keeps its two-argument signature, takes **no**
authority and requires nothing: it is a primitive implementation, and Task 11
lists it in `PRIMITIVE_IMPLEMENTATIONS`. The pinned cut-9 block in
`fork_corpus` (`    pending = _fork_pending(dest)` … `return _registry.load_manifest(dest)`)
stays byte-identical because the check sits above it.

- [ ] **Step 4: Migrate the callers**

Every caller under `tests/` gains `authority=FULL` (or a narrowed one where the test is about permits). `tests/acceptance/conftest.py`'s `durable_root` fixture: `init_corpus_root(root, authority=FULL)`. Leave `tools/cut*_acceptance.py` untouched (§13.2).

- [ ] **Step 5: Run, probe, gate, commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
```

Probe: the by-design stale set as ruled in Step 3. Then:

```bash
cd .. && tasks check && git add python && git commit -m "feat(permit): root lifecycle acts require the lifecycle permit"
```

---

### Task 11: The static boundary — `test_permit_boundary.py` (E6)

**Files:**
- Create: `python/tests/test_permit_boundary.py`

**Interfaces:**
- Consumes: the seams of Tasks 4–10.
- Produces: `WRITE_ENTRY_POINTS`, `PRIMITIVE_ATTRIBUTES`, `PRIMITIVE_NAMES`, `PRIMITIVE_IMPLEMENTATIONS`, `READ_ONLY_ACTOR_EXCEPTIONS`, `ACTOR_BEARING_RECORDS`, the predicates `primitive_callers(tree, module)`, `requires_before_writing(node, family)`, `actor_parameters(tree)`, `authority_constructions(tree)`, and the five `test_*` arms (names below are the N2 checks of Task 13).

- [ ] **Step 1: Write the test module**

```python
"""E6: the write entry points are closed and held statically (design §5).

The S8 pattern over authority: every predicate reads the **imported** package,
is asserted in both directions, and is proved able to speak by a synthetic
offender and satisfiable by a synthetic satisfied module.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import beliefs

PACKAGE = Path(beliefs.__file__).resolve().parent

PRIMITIVE_ATTRIBUTES = frozenset(
    {"append_intent", "execute", "execute_fulfilling", "publish_fulfilling", "store_write", "store_delete", "store_move"}
)
"""A call `<receiver>.<attr>(...)` with one of these attrs is a write. `add` counts
only on a `_corpus` receiver (below)."""

PRIMITIVE_NAMES = frozenset(
    {
        "register_root",
        "_replicate_root_callback",
        "_fork_root_callback",
        "_resume_fork_root_callback",
        "_grant_read_serviceability_callback",
        "_migrate_root_to_lifecycle_v3_callback",
    }
)
"""Bare-name calls that are writes: the engine's registration and the root-copying callbacks."""

PRIMITIVE_IMPLEMENTATIONS = frozenset(
    {
        "root.py:DurableOperationPort.append_intent",
        "root.py:DurableOperationPort.execute",
        "root.py:DurableOperationPort._execute",
        "root.py:DurableOperationPort.execute_fulfilling",
        "root.py:DurableOperationPort._execute_fulfilling",
        "root.py:DurableExecutor.execute",
        "root.py:_mapped_submit.submit",
        "root.py:_store_append_intent",
        "root.py:_store_publish_fulfilling",
        "root.py:_store_write",
        "root.py:_store_delete",
        "root.py:_store_move",
        "root.py:_fork_resume",
    }
)
"""The bodies that *implement* a primitive, excluded by exact name (design §4.3,
§13.6). Every name must exist in the tree — compared for equality, never
containment. Correct the `_store_*` names to the tree's exact definitions in
`root.py` (they are the callables `holdings_seam()` binds)."""

WRITE_ENTRY_POINTS: dict[str, str] = {
    "corpus.py:CorpusWriter.add": "corpus-write",
    "corpus.py:CorpusWriter.retract": "corpus-write",
    "corpus.py:CorpusWriter.supersede": "corpus-write",
    "corpus.py:CorpusWriter.revise": "corpus-write",
    "corpus.py:CorpusWriter.mint_coordination": "corpus-write",
    "corpus.py:CorpusWriter.revise_coordination": "corpus-write",
    "corpus.py:CorpusWriter.import_bundle": "corpus-write",
    "corpus.py:CorpusWriter.adopt_manifest": "lifecycle",
    "boundary.py:execute_assessment_run": "run",
    "boundary.py:execute_production_run": "run",
    "holdings/boundary.py:_publish": "holdings",
    "holdings/boundary.py:recheck": "holdings",
    "holdings/boundary.py:_append": "holdings",
    "holdings/boundary.py:write": "holdings",
    "holdings/boundary.py:delete": "holdings",
    "holdings/boundary.py:move": "holdings",
    "world/registry.py:World._terminal": "registry",
    "world/registry.py:_locked_admit": "registry",
    "world/anchors.py:_anchor_heads": "registry",
    "world/epoch.py:build_epoch": "epoch",
    "world/epoch.py:delete_epoch": "epoch",
    "world/rules.py:install_rule_binding": "epoch",
    "world/rules.py:remove_rule_binding": "epoch",
    "root.py:init_corpus_root": "lifecycle",
    "root.py:init_world_root": "lifecycle",
    "root.py:init_store_root": "lifecycle",
    "root.py:replicate_root": "lifecycle",
    "root.py:migrate_root_to_lifecycle_v3": "lifecycle",
    "root.py:restore_root.grant": "lifecycle",
    "root.py:fork_corpus": "lifecycle",
    "root.py:fork_store": "lifecycle",
}
"""The inventory (design §4.2), edited by hand in the design that adds an act."""

SEAM_MODULES = (
    "corpus.py", "boundary.py", "replay.py", "root.py", "holdings/boundary.py",
    "world/registry.py", "world/epoch.py", "world/rules.py", "world/anchors.py",
)
READ_ONLY_ACTOR_EXCEPTIONS = frozenset({"root.py:audit_log", "holdings/boundary.py:intent_payload"})
ACTOR_BEARING_RECORDS = frozenset(
    {"AdmissionRecord", "StatusRecord", "AnchorActOrigin", "EpochDeletionReport", "Occurrence",
     "OperationIntent", "AssessmentRunIntent", "ActReport", "RunRefused"}
)
"""Values that record who acted. `permit.py` aside, these classes' fields are the
only `actor` spellings arm 3 permits in the seam modules."""

EFFECTS_BEFORE_CHECK = PRIMITIVE_ATTRIBUTES | PRIMITIVE_NAMES | {
    "mkdir", "write_bytes", "write_text", "unlink", "rmdir", "rmtree", "rename", "symlink_to", "chmod",
    "touch", "makedirs", "remove", "copy", "copy2", "copytree", "move",
}

RUN_FAMILY_TRY_SHAPE = frozenset({"boundary.py:execute_assessment_run", "boundary.py:execute_production_run"})


def modules() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def relative(path: Path) -> str:
    return path.relative_to(PACKAGE).as_posix()


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _is_primitive_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in PRIMITIVE_NAMES
    if isinstance(func, ast.Attribute):
        if func.attr in PRIMITIVE_ATTRIBUTES:
            return True
        return func.attr == "add" and isinstance(func.value, ast.Attribute) and func.value.attr == "_corpus"
    return False


def definitions(tree: ast.Module):
    """Every (qualified name, FunctionDef) in the module, nested ones included."""
    found = []

    def walk(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                found.append((".".join((*scope, child.name)), child))
                walk(child, (*scope, child.name))
            elif isinstance(child, ast.ClassDef):
                walk(child, (*scope, child.name))
            else:
                walk(child, scope)

    walk(tree, ())
    return found


def _own_statements(function: ast.AST):
    """Every node of `function` that is not inside a nested definition."""
    for child in ast.iter_child_nodes(function):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
            continue
        yield child
        yield from _own_statements(child)


def primitive_callers(tree: ast.Module, module: str) -> set[str]:
    return {
        f"{module}:{name}"
        for name, function in definitions(tree)
        if any(_is_primitive_call(node) for node in _own_statements(function))
    }


def _require_statement(statement: ast.stmt) -> ast.Call | None:
    """The bare `Expr(Call(<receiver>.require(...)))`, or None."""
    if (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and statement.value.func.attr == "require"
    ):
        return statement.value
    return None


def _family_literal(call: ast.Call) -> str | None:
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        return call.args[0].value
    return None


def _run_shape(statement: ast.stmt) -> ast.Call | None:
    """The one admitted `try` (design §5 arm 2): body is the bare require, one
    `except PermitExceeded as _:` handler whose body is one `return RunRefused(...)`."""
    if not isinstance(statement, ast.Try) or statement.orelse or statement.finalbody:
        return None
    if len(statement.body) != 1 or len(statement.handlers) != 1:
        return None
    call = _require_statement(statement.body[0])
    handler = statement.handlers[0]
    if call is None or not isinstance(handler.type, ast.Name) or handler.type.id != "PermitExceeded":
        return None
    if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Return):
        return None
    value = handler.body[0].value
    if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "RunRefused"):
        return None
    return call


def _has_effect(statement: ast.stmt) -> bool:
    for node in ast.walk(statement):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in EFFECTS_BEFORE_CHECK or _is_primitive_call(node):
                return True
    return False


def requires_before_writing(function: ast.AST, family: str, *, run_shape: bool) -> str | None:
    """None when the definition satisfies arm 2, else the reason it does not."""
    body = list(function.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]  # docstring
    for statement in body:
        call = _require_statement(statement)
        if call is None and run_shape:
            call = _run_shape(statement)
        if call is not None:
            literal = _family_literal(call)
            if literal is None:
                return "the family is not a string literal"
            if literal != family:
                return f"requires {literal!r}, inventoried as {family!r}"
            return None
        if _has_effect(statement):
            return f"an effect precedes the check: {ast.dump(statement)[:80]}"
        if any(_require_statement(s) is not None for s in ast.walk(statement) if isinstance(s, ast.stmt) and s is not statement):
            return "the check is nested, not a top-level statement"
    return "no require statement"


def actor_parameters(tree: ast.Module, module: str) -> set[str]:
    found = set()
    for name, function in definitions(tree):
        params = function.args
        every = [*params.posonlyargs, *params.args, *params.kwonlyargs]
        if any(param.arg == "actor" for param in every):
            found.add(f"{module}:{name}")
    return found


def authority_constructions(tree: ast.Module) -> int:
    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Authority"
    )


# --- the five arms ----------------------------------------------------------


def test_the_inventory_is_closed_in_both_directions():
    found: set[str] = set()
    defined: set[str] = set()
    for module in modules():
        tree, name = parsed(module), relative(module)
        found |= primitive_callers(tree, name)
        defined |= {f"{name}:{qualified}" for qualified, _ in definitions(tree)}
    present = {name for name in defined if name in PRIMITIVE_IMPLEMENTATIONS}
    assert present == PRIMITIVE_IMPLEMENTATIONS, (
        f"implementation exclusions name definitions the tree lacks: {sorted(PRIMITIVE_IMPLEMENTATIONS - defined)}"
    )
    callers = found - PRIMITIVE_IMPLEMENTATIONS
    assert callers == set(WRITE_ENTRY_POINTS), (
        f"uninventoried primitive callers: {sorted(callers - set(WRITE_ENTRY_POINTS))}; "
        f"inventoried definitions calling no primitive: {sorted(set(WRITE_ENTRY_POINTS) - callers)}"
    )


def test_every_entry_point_requires_before_it_writes():
    failures = []
    for module in modules():
        name = relative(module)
        for qualified, function in definitions(parsed(module)):
            key = f"{name}:{qualified}"
            if key not in WRITE_ENTRY_POINTS:
                continue
            reason = requires_before_writing(function, WRITE_ENTRY_POINTS[key], run_shape=key in RUN_FAMILY_TRY_SHAPE)
            if reason is not None:
                failures.append(f"{key}: {reason}")
    assert failures == []


def test_the_run_shape_is_admitted_only_for_the_run_family():
    for module in modules():
        name = relative(module)
        for qualified, function in definitions(parsed(module)):
            key = f"{name}:{qualified}"
            if key in WRITE_ENTRY_POINTS and key not in RUN_FAMILY_TRY_SHAPE:
                assert requires_before_writing(function, WRITE_ENTRY_POINTS[key], run_shape=False) is None, key
    assert {key for key in RUN_FAMILY_TRY_SHAPE} == {key for key, family in WRITE_ENTRY_POINTS.items() if family == "run"}


def test_no_entry_point_or_public_seam_function_takes_an_actor():
    offending: set[str] = set()
    for module in modules():
        name = relative(module)
        tree = parsed(module)
        found = actor_parameters(tree, name)
        offending |= {key for key in found if key in WRITE_ENTRY_POINTS}
        if name in SEAM_MODULES:
            public = {key for key in found if not key.split(":")[1].split(".")[-1].startswith("_")}
            records = {key for key in public if key.split(":")[1].split(".")[0] in ACTOR_BEARING_RECORDS}
            offending |= public - records - READ_ONLY_ACTOR_EXCEPTIONS
    assert offending == set(), sorted(offending)
    present = set()
    for module in modules():
        present |= {key for key in actor_parameters(parsed(module), relative(module)) if key in READ_ONLY_ACTOR_EXCEPTIONS}
    assert present == READ_ONLY_ACTOR_EXCEPTIONS, "the read-only exception set is compared by equality"


def test_authority_is_constructed_only_in_permit():
    for module in modules():
        count = authority_constructions(parsed(module))
        assert count == 0 or relative(module) == "permit.py", f"{relative(module)} constructs an Authority"


# --- offender and satisfied arms --------------------------------------------

SATISFIED = '''
def act(ctx, node):
    ctx.authority.require("corpus-write", (node.kind,))
    with ctx.lock:
        return ctx._corpus.add(node)
'''

SATISFIED_WITH_PARSING = '''
def act(ctx, records):
    bundle = tuple(records)
    kinds = tuple(record.kind for record in bundle)
    ctx.authority.require("corpus-write", kinds)
    ctx.port.append_intent(b"x")
'''

SATISFIED_RUN = '''
def execute(port):
    try:
        port.authority.require("run", ("run", "act-report"))
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    actor = port.authority.actor
    port.append_intent(b"x")
'''

OFFENDERS = {
    "no require": ("act", '''
def act(ctx, node):
    ctx.port.append_intent(b"x")
'''),
    "require after the append": ("act", '''
def act(ctx, node):
    ctx.port.append_intent(b"x")
    ctx.authority.require("corpus-write")
'''),
    "require under an if": ("act", '''
def act(ctx, node):
    if node is not None:
        ctx.authority.require("corpus-write")
    ctx.port.append_intent(b"x")
'''),
    "require behind flag and": ("act", '''
def act(ctx, node, flag):
    flag and ctx.authority.require("corpus-write")
    ctx.port.append_intent(b"x")
'''),
    "mkdir before the require": ("act", '''
def act(ctx, root):
    root.mkdir(parents=True, exist_ok=True)
    ctx.authority.require("lifecycle")
    register_root(root)
'''),
    "wrong family": ("act", '''
def act(ctx, node):
    ctx.authority.require("run")
    ctx.port.append_intent(b"x")
'''),
    "family not a literal": ("act", '''
def act(ctx, node, family):
    ctx.authority.require(family)
    ctx.port.append_intent(b"x")
'''),
    "try with a second statement": ("execute", '''
def execute(port):
    try:
        port.authority.require("run")
        port.append_intent(b"x")
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
'''),
    "handler does more than return": ("execute", '''
def execute(port):
    try:
        port.authority.require("run")
    except PermitExceeded as exceeded:
        port.append_intent(b"x")
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    port.append_intent(b"x")
'''),
}


def _only_definition(source: str, name: str):
    tree = ast.parse(source)
    return dict(definitions(tree))[name]


def test_the_satisfied_modules_pass():
    assert requires_before_writing(_only_definition(SATISFIED, "act"), "corpus-write", run_shape=False) is None
    assert requires_before_writing(_only_definition(SATISFIED_WITH_PARSING, "act"), "corpus-write", run_shape=False) is None
    assert requires_before_writing(_only_definition(SATISFIED_RUN, "execute"), "run", run_shape=True) is None
    assert primitive_callers(ast.parse(SATISFIED), "m.py") == {"m.py:act"}


@pytest.mark.parametrize("label", sorted(OFFENDERS))
def test_each_offender_is_caught(label):
    name, source = OFFENDERS[label]
    family = "run" if name == "execute" else ("lifecycle" if "mkdir" in label else "corpus-write")
    assert requires_before_writing(_only_definition(source, name), family, run_shape=name == "execute") is not None, label


def test_the_run_shape_under_a_non_run_family_is_caught():
    assert requires_before_writing(_only_definition(SATISFIED_RUN, "execute"), "run", run_shape=False) is not None


def test_an_actor_parameter_is_caught_and_a_read_only_exception_must_exist():
    tree = ast.parse("def act(ctx, *, actor):\n    ctx.port.append_intent(b'x')\n")
    assert actor_parameters(tree, "m.py") == {"m.py:act"}
    assert authority_constructions(ast.parse("a = Authority(p, 'x')")) == 1
```

- [ ] **Step 2: Run it against the tree**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_permit_boundary.py
```

Expected on first run: `test_the_inventory_is_closed_in_both_directions` and `test_every_entry_point_requires_before_it_writes` report every gap between the inventory above and the tree. Resolve each by its kind: a **§4.3 implementation body under another name** (a `_store_*` callable, a `DurableExecutor` method) — correct `PRIMITIVE_IMPLEMENTATIONS` to the tree's exact name; a **definition the AST finds calling a primitive that §4.2 did not list** (a helper in `corpus.py`, `world/`, or `root.py`) — it is a real entry point: give it a `require` with the family of the act it serves, add it to `WRITE_ENTRY_POINTS`, and record both in §10 of the design; an **inventoried entry point whose check is not its first effectful statement** — fix the entry point. Never widen an allowlist to make a finding go away. Iterate until all five arms and the offender arms pass.

- [ ] **Step 3: Gate and commit**

```bash
uv run --frozen pytest -q -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks check && git add python && git commit -m "test(permit): hold the write entry points closed statically (E6)"
```

---

### Task 12: The durable acceptance suite (E1, E2, E7, E8 over real roots)

**Files:**
- Create: `python/tests/acceptance/test_permit_acceptance.py`
- Modify: `python/tests/acceptance/conftest.py` (a `durable_world` fixture if none exists; `durable_root` already registers a corpus root)

**Interfaces:**
- Consumes: `open_corpus`, `open_world`, `init_world_root`, `holdings_seam`, `durable_port`, `science_root._log_seam().inspect_registered(root)`.
- Produces: the check ids Task 13's arms name.

- [ ] **Step 1: Write the suite**

```python
"""Cut 16's durable arms: E1, E2, E7 and E8 through the composition root on the
certified volume (design §9.2). Chains and world roots are byte-identical before
and after every refusal."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from authority import ACTOR, FULL, lacking, narrowed
from durable_fixture import memo
from fixtures_cut3 import stage, freeze, spec_draft, spec_rules, definition, MINIMAL_POLICY, DATA_ADDRESS, READS_ADDRESS
from test_operation_port import durable_port

from beliefs import root as science_root
from beliefs import stored
from beliefs.boundary import RunRefused, execute_assessment_run
from beliefs.corpus import CorpusWriter
from beliefs.errors import PermitExceeded, PermitFact
from beliefs.holdings.boundary import ActContext, StoreLocator, write as holdings_write
from beliefs.root import DurableOperationPort, holdings_seam, init_corpus_root, init_store_root, init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig
from beliefs.world.logmodel import WellFormedView


def _head(root: Path):
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return tuple(entry.digest for entry in view.entries)  # use the entry view's real digest attribute


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_e1_add_through_open_corpus_refuses_before_the_chain_moves(durable_root):
    writer = open_corpus(durable_root, authority=lacking(kinds=("proposition",)))
    before = _head(durable_root)
    with pytest.raises(PermitExceeded) as caught:
        writer.add(memo("proposition:p1"))  # `memo` mints a memo kind; use durable_fixture's proposition helper if memo is not a `proposition`
    assert caught.value.requirement == PermitFact("kind", memo("proposition:p1").kind)
    assert _head(durable_root) == before
    assert open_corpus(durable_root, authority=FULL).add(memo("proposition:p1")).id


def test_e2_the_composition_root_binds_one_authority_to_writer_and_port(durable_root):
    writer = open_corpus(durable_root, authority=FULL)
    assert writer.authority is FULL
    other = DurableOperationPort(
        durable_root, backend=science_root._PRODUCTION_BACKEND, storage=science_root.PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(durable_root), authority=narrowed(),
    )
    with pytest.raises(ValueError, match="another authority"):
        CorpusWriter(durable_root, science_root.durable_executor_factory(), authority=FULL, operation_port=other)


def test_e7_the_run_boundary_refuses_with_no_intent_through_a_real_port(durable_root, tmp_path):
    port = durable_port(durable_root, authority=lacking(families=("run",)))
    before = _head(durable_root)
    code, held = stage(tmp_path)
    outcome = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()), port=port, boundary_policy=MINIMAL_POLICY,
        definition=definition(), code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile", targets=("outputs/result.txt",), declared_outputs=("outputs/result.txt",),
        observer="observer-1", started_at="2026-09-04T00:00:00Z", host_realization="host-a", scratch_base=tmp_path / "scratch",
    )
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None
    assert _head(durable_root) == before


def test_e7_a_holdings_act_refuses_with_the_store_and_observer_chains_unchanged(work_directory):
    observer_root = work_directory / f"observer-{os.getpid()}-permit"
    store_root = work_directory / f"store-{os.getpid()}-permit"
    init_corpus_root(observer_root, authority=FULL)
    store_id = init_store_root(store_root, authority=FULL)
    ctx = ActContext(observer_root, store_root, "observer", "instrument", lacking(families=("holdings",)), holdings_seam())
    before = _head(observer_root), _tree_bytes(store_root)
    with pytest.raises(PermitExceeded):
        holdings_write(ctx, StoreLocator(store_id, "held.bin"), b"bytes")
    assert (_head(observer_root), _tree_bytes(store_root)) == before


def test_e7_world_admit_refuses_with_the_world_root_unchanged(durable_root, work_directory):
    world_root = work_directory / f"world-{os.getpid()}-permit"
    config = WorldConfig(world_root, "0" * 32, (durable_root,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=lacking(families=("registry",)))
    before = _tree_bytes(world_root)
    with pytest.raises(PermitExceeded):
        world.admit(durable_root, provenance=Fresh())
    assert _tree_bytes(world_root) == before
    assert open_world(config, authority=FULL).admit(durable_root, provenance=Fresh()).actor == ACTOR


def test_e8_an_unpermitted_member_refuses_the_bundle_with_the_chain_unchanged(durable_root):
    writer = open_corpus(durable_root, authority=lacking(kinds=("source",)))
    before = _head(durable_root)
    members = [memo("proposition:p2"), stored.source_node("s1", title="s", identifiers={"doi": "10.1/x"})]
    with pytest.raises(PermitExceeded) as caught:
        writer.import_bundle(members, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert caught.value.requirement == PermitFact("kind", "source")
    assert _head(durable_root) == before
    report = open_corpus(durable_root, authority=FULL).import_bundle(members, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert report.actor == ACTOR and len(_head(durable_root)) == len(before) + 3  # intent, payload, fulfilling report — adjust to the observed count
```

`durable_root` requires a corpus manifest for imports in some suites — read `tests/acceptance/test_durable_families.py`'s import test for the setup it performs (adopt a manifest with `writer.adopt_manifest(profile=...)` or the `pinned()` helper) and mirror it. Replace `_head`'s digest attribute and the chain-length delta with what the entry views actually expose.

- [ ] **Step 2: Run on the certified volume**

```bash
SCIENCE_CUT4_ROOT=<certified volume dir> uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_permit_acceptance.py
```

Expected: all passing. If the engine refuses the volume, the conftest raises `UncertifiedVolume` — report the exact mismatch rather than skipping (AGENTS.md).

- [ ] **Step 3: Commit**

```bash
cd .. && tasks check && git add python && git commit -m "test(permit): durable acceptance arms for E1, E2, E7 and E8"
```

---

### Task 13: N2 arms, the audit test, and the cut 16 runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut16.py`
- Create: `python/tests/acceptance/test_n2_cut16.py`
- Create: `python/tools/cut16_acceptance.py`

**Interfaces:**
- Consumes: every check id from Tasks 2–12; `IMPLEMENTATION_AMENDMENT_COMMIT` from Task 1; the pins below.
- Produces: `CUT16_ARMS`, `ROW_UNITS = {"E1": 1, ..., "E8": 1}`, `LABELED_UNITS = ("K1",)`, `CO_CITED = {"K1": ("test_holdings_boundary.py::test_write_publishes_found_and_fulfills_its_intent",)}` (use `H4u1`'s real check id from `n2_arms_cut10.py`), `unit_of`.

- [ ] **Step 1: Declare the arms**

`python/tests/acceptance/n2_arms_cut16.py` — one lettered arm per unit at least; every `before` must occur exactly once in the module it names:

```python
"""Cut 16: 8 selected + 1 labeled = 9 units, carried by the arms below."""

from n2_arms import Arm, Sabotage

_PERMIT, _CORPUS, _BOUNDARY = "permit.py", "corpus.py", "boundary.py"
_HOLDINGS, _REGISTRY, _ROOT = "holdings/boundary.py", "world/registry.py", "root.py"

_P = "test_permit.py"
_S = "test_permit_boundary.py"
_C = "test_corpus_write.py"
_I = "test_import_bundle.py"
_B = "test_boundary.py"
_H = "test_holdings_boundary.py"
_A = "acceptance/test_permit_acceptance.py"

CUT16_ARMS = (
    Arm(
        row="E1a",
        asserts="a missing family is refused on the family before any kind",
        sabotage=Sabotage(
            module=_PERMIT,
            before='        if family not in self.permit.act_families:\n            raise PermitExceeded(PermitFact("family", family), self.permit.summary())\n',
            after="",
        ),
        checks=(
            f"{_P}::TestE1AuthorityRequire::test_a_missing_family_is_refused_on_the_family_before_any_kind",
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_family_refuses_and_writes_nothing",
        ),
    ),
    Arm(
        row="E1b",
        asserts="the first missing kind, in the caller's order, is named",
        sabotage=Sabotage(
            module=_PERMIT,
            before="        for kind in kinds:\n            if kind not in self.permit.kinds:",
            after="        for kind in ():\n            if kind not in self.permit.kinds:",
        ),
        checks=(
            f"{_P}::TestE1AuthorityRequire::test_the_first_missing_kind_in_the_callers_order_is_named",
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_kind_names_the_kind",
        ),
    ),
    Arm(
        row="E1c",
        asserts="the corpus add path requires before it writes",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        self._authority.require("corpus-write", (node.kind,))\n        with self._operation:\n            self._refuse_family_kinds(node)\n            self._refuse(node)',
            after='        with self._operation:\n            self._refuse_family_kinds(node)\n            self._refuse(node)',
        ),
        checks=(
            f"{_C}::TestE1CorpusWriteRequiresBeforeAnyEffect::test_add_under_a_permit_lacking_the_family_refuses_and_writes_nothing",
            f"{_S}::test_every_entry_point_requires_before_it_writes",
        ),
    ),
    Arm(
        row="E2a",
        asserts="a writer over a port bound to another authority refuses construction",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        if operation_port is not None and operation_port.authority != authority:",
            after="        if False:",
        ),
        checks=(f"{_C}::TestE2AuthorityBindsOnceAtConstruction::test_a_port_bound_to_another_authority_refuses_construction",),
    ),
    Arm(
        row="E3a",
        asserts="a retraction naming another actor is refused",
        sabotage=Sabotage(
            module=_CORPUS,
            before='            if isinstance(facet, dict) and facet.get("actor") != self._authority.actor:',
            after="            if False:",
        ),
        checks=("test_retract.py::test_e3_a_retraction_naming_another_actor_is_refused",),
    ),
    Arm(
        row="E3b",
        asserts="a run closure naming another actor is refused through add",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        if named != self._authority.actor:",
            after="        if False:",
        ),
        checks=(f"{_C}::TestE3TheActorIsBound::test_a_run_closure_naming_another_actor_is_refused_through_add",),
    ),
    Arm(
        row="E3c",
        asserts="the run intent carries the port's actor",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before="    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
            after='    actor = "tester"\n    if type(spec) is not FrozenSpec:',
        ),
        checks=(f"{_B}::test_e3_the_run_intent_carries_the_ports_actor",),
    ),
    Arm(
        row="E4a",
        asserts="an ambiguous kind without a selected route is refused",
        sabotage=Sabotage(
            module=_PERMIT,
            before='                raise ValueError(f"{kind!r} admits more than one route; the declaration must select one")',
            after="                route = sorted(admissible)[0]",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_an_ambiguous_kind_must_select_a_route",),
    ),
    Arm(
        row="E4b",
        asserts="an inadmissible route is refused",
        sabotage=Sabotage(
            module=_PERMIT,
            before="                if route not in admissible:",
            after="                if False:",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_a_selected_route_must_be_admissible",),
    ),
    Arm(
        row="E4c",
        asserts="publishes() is refused while publish is not a family",
        sabotage=Sabotage(
            module=_PERMIT,
            before='        raise ValueError("publish is not an act family")',
            after="        return cls(WritePermit(frozenset(), frozenset()))",
        ),
        checks=(f"{_P}::TestE4RequirementConstruction::test_publishes_is_refused_while_publish_is_not_a_family",),
    ),
    Arm(
        row="E5a",
        asserts="coverage is subset inclusion on both dimensions",
        sabotage=Sabotage(
            module=_PERMIT,
            before="    return required.permit.kinds <= ceiling.kinds and required.permit.act_families <= ceiling.act_families",
            after="    return required.permit.act_families <= ceiling.act_families",
        ),
        checks=(f"{_P}::TestE5Coverage::test_coverage_is_subset_inclusion_on_both_dimensions",),
    ),
    Arm(
        row="E6a",
        asserts="a displaced check is caught statically",
        sabotage=Sabotage(
            module=_HOLDINGS,
            before='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    ctx.authority.require("holdings", ("holdings-observation",))\n    token = secrets.token_hex(16)',
            after='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    token = secrets.token_hex(16)\n    ctx.authority.require("holdings", ("holdings-observation",))',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6b",
        asserts="a removed check is caught statically",
        sabotage=Sabotage(
            module=_REGISTRY,
            before='    authority.require("registry")\n    state.registry = _scan_registry(world_root)',
            after="    state.registry = _scan_registry(world_root)",
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6c",
        asserts="a conditional check is caught statically",
        sabotage=Sabotage(
            module=_ROOT,
            before='    authority.require("lifecycle")\n    root = config.world_root',
            after='    if config is not None:\n        authority.require("lifecycle")\n    root = config.world_root',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6d",
        asserts="an effect before the check is caught statically",
        sabotage=Sabotage(
            module=_ROOT,
            before='    authority.require("lifecycle")\n    root = config.world_root\n    if root.exists() and not root.is_dir():\n        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a world root")\n    root.mkdir(parents=True, exist_ok=True)',
            after='    root = config.world_root\n    root.mkdir(parents=True, exist_ok=True)\n    authority.require("lifecycle")\n    if root.exists() and not root.is_dir():\n        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a world root")',
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E6e",
        asserts="a widened run handler is caught statically",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before="    except PermitExceeded as exceeded:\n        return RunRefused(\"permit-exceeded\", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
            after="    except WriteRefused as exceeded:\n        return RunRefused(\"permit-exceeded\", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:",
        ),
        checks=(f"{_S}::test_every_entry_point_requires_before_it_writes",),
    ),
    Arm(
        row="E7a",
        asserts="a permit violation on the run boundary appends no intent and mints no report",
        sabotage=Sabotage(
            module=_BOUNDARY,
            before='        return RunRefused("permit-exceeded", None, None, None, str(exceeded))\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:',
            after='        refused = _refused("permit-exceeded", "absent", port.authority.actor, observer, started_at, detail=str(exceeded))\n        port.execute(_report_plan(refused.report))\n        return refused\n    actor = port.authority.actor\n    if type(spec) is not FrozenSpec:',
        ),
        checks=(
            f"{_B}::test_e7_a_permit_lacking_run_refuses_with_no_intent_and_no_report",
            f"{_A}::test_e7_the_run_boundary_refuses_with_no_intent_through_a_real_port",
        ),
    ),
    Arm(
        row="E7b",
        asserts="a holdings act under a lacking permit leaves both chains unchanged",
        sabotage=Sabotage(
            module=_HOLDINGS,
            before='def write(ctx: ActContext, location: StoreLocator, content: bytes, *, expected: str | None = None,\n          standing: tuple[HoldingsObservation, ...] = ()) -> PublishedObservation:\n    ctx.authority.require("holdings", ("holdings-observation",))\n',
            after='def write(ctx: ActContext, location: StoreLocator, content: bytes, *, expected: str | None = None,\n          standing: tuple[HoldingsObservation, ...] = ()) -> PublishedObservation:\n',
        ),
        checks=(
            f"{_H}::test_e1_a_permit_lacking_the_observation_kind_refuses_write_before_any_store_effect",
            f"{_A}::test_e7_a_holdings_act_refuses_with_the_store_and_observer_chains_unchanged",
        ),
    ),
    Arm(
        row="E8a",
        asserts="one unpermitted member refuses the bundle whole before the intent",
        sabotage=Sabotage(
            module=_CORPUS,
            before='        self._authority.require(\n            "corpus-write", (*(record.kind for record in bundle if type(record) is Node), "act-report")\n        )',
            after='        self._authority.require("corpus-write", ("act-report",))',
        ),
        checks=(
            f"{_I}::test_e8_one_unpermitted_member_refuses_the_bundle_before_the_intent",
            f"{_A}::test_e8_an_unpermitted_member_refuses_the_bundle_with_the_chain_unchanged",
        ),
    ),
    Arm(
        row="K1",
        asserts="H4u1 succeeded: an established finding is published or the act fails loudly",
        sabotage=Sabotage(
            module=_HOLDINGS,
            before='    node = stored.holdings_observation_node(record)\n    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f"holdings-observation/{record.identity()}.md",\n                                                             node_to_markdown(node).encode("utf-8")),), intent)\n    return PublishedObservation(record)\n\n\ndef recheck(',
            after='    node = stored.holdings_observation_node(record)\n    return PublishedObservation(record)\n\n\ndef recheck(',
        ),
        checks=("<H4u1's check id, copied verbatim from n2_arms_cut10.py>",),
    ),
)

_UNIT_OF_LETTERED = {f"E{n}{letter}": f"E{n}" for n in range(1, 9) for letter in "abcde"}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED.get(row, row)


ROW_UNITS: dict[str, int] = {f"E{n}": 1 for n in range(1, 9)}
LABELED_UNITS: tuple[str, ...] = ("K1",)
CO_CITED: dict[str, tuple[str, ...]] = {"K1": ("<H4u1's check id, copied verbatim from n2_arms_cut10.py>",)}
```

Every `before` above is a **draft of the exact text**: after Tasks 5–11, open each named module and copy the real lines so each `before` occurs exactly once (the `test_every_arm_has_one_source_mutation_and_exact_check_nodes` arm below refuses anything else). Adjust the sabotage of `E6d` if `init_world_root`'s exact lines differ. Fill `K1`'s check id from `n2_arms_cut10.py`'s `H4u1` entry.

- [ ] **Step 2: Write the audit test**

`python/tests/acceptance/test_n2_cut16.py`, on the cut-14/15 pattern:

```python
"""Cut 16 declaration accounting and N2 audit."""
import subprocess
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm
from n2_arms_cut3 import CUT3_ARMS
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import CUT10_ARMS
from n2_arms_cut11 import CUT11_ARMS
from n2_arms_cut12 import CUT12_ARMS
from n2_arms_cut13 import CUT13_ARMS
from n2_arms_cut14 import CUT14_ARMS
from n2_arms_cut15 import CUT15_ARMS
from n2_arms_cut16 import CO_CITED, CUT16_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-04-write-permits-design.md"
CUT16_FREEZE_COMMIT = "c2f87b3"
IMPLEMENTATION_AMENDMENT_COMMIT = "<Task 1's hash>"
FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "7f5b28ec7da5f19db83fe0819c7477c8dbed7e93",
    "python/tests/n2_arms_cut6.py": "fdea7a7e2f8780f8ddfec3a6a700333a28e648cd",
    "python/tests/n2_arms_cut7.py": "8ca085e8cf860efc9b7504f0961523e5e2a0438f",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba5b32c72fc6b967cda85f9b1c4ef9f6198",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360a83c5e48c81824f04dd648adb972e790a",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d6906a8729f8e04097083396a50afc464f9b",
    "python/tests/acceptance/n2_arms_cut14.py": "f982778",
    "python/tests/acceptance/n2_arms_cut15.py": "8a4d43b",
}
FROZEN_CUT10_SHA256 = {
    "python/tests/acceptance/n2_arms_cut10.py": "e7e3cf02f8d033a9bf507b6eba0f4968bcf702c901ad3a753013f062c02e5ae8",
    "python/tests/acceptance/test_n2_cut10.py": "4058b86679b9a7b17bbfd5115ba3e7c21896e2316c384d700c4af052674dc650",
    "python/tools/cut10_acceptance.py": "39a1e333d8b99bacf0bcdc416e86ef6d68e97be797c6acc3c31c922bab838edf",
    "docs/designs/2026-08-24-conformance-cut-10.md": "<sha256sum of the file>",
    "docs/plans/2026-08-24-conformance-cut-10-results.md": "<sha256sum of the file>",
}
PRIOR_ARMS = (*CUT3_ARMS, *CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS, *CUT10_ARMS,
              *CUT11_ARMS, *CUT12_ARMS, *CUT13_ARMS, *CUT14_ARMS, *CUT15_ARMS)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    root = tmp_path_factory.mktemp("n2-cut16")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT16_ARMS)))


def test_the_inventory_is_eight_selected_and_one_labeled() -> None:
    assert ROW_UNITS == {f"E{n}": 1 for n in range(1, 9)}
    assert LABELED_UNITS == ("K1",)


def test_the_arm_rows_are_unique() -> None:
    rows = [arm.row for arm in CUT16_ARMS]
    assert len(rows) == len(set(rows))


def test_every_declared_unit_is_carried_by_at_least_one_arm() -> None:
    carried = {unit_of(arm.row) for arm in CUT16_ARMS}
    assert set(ROW_UNITS) | set(LABELED_UNITS) <= carried


def test_every_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(row="N2", asserts="every cut-16 check passes against the real package",
                sabotage=CUT16_ARMS[0].sabotage,
                checks=tuple(dict.fromkeys(check for arm in CUT16_ARMS for check in arm.checks)))
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{f.arm.label}: {f.verdict}: {f.detail}" for f in unsound)


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact() -> None:
    for commit in (CUT16_FREEZE_COMMIT, IMPLEMENTATION_AMENDMENT_COMMIT):
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"], check=False).returncode == 0
    frozen = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{CUT16_FREEZE_COMMIT}:{FROZEN_CUT.relative_to(REPO_ROOT)}"],
                            check=True, capture_output=True, text=True).stdout
    text = FROZEN_CUT.read_text(encoding="utf-8")
    for heading in ("## 7. Guarantees", "## 9. Conformance cut 16"):
        assert _section(text, heading) == _section(frozen, heading), heading


def test_every_arm_has_one_source_mutation_and_exact_check_nodes() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT16_ARMS:
        assert arm.checks and len(arm.checks) == len(set(arm.checks)), arm.row
        assert arm.sabotage.before != arm.sabotage.after and arm.asserts.strip(), arm.row
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_prior_declarations_and_the_whole_cited_cut10_surface_are_unchanged() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path], check=False).returncode == 0, path
    for path, expected in FROZEN_CUT10_SHA256.items():
        assert sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected, path
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT16_ARMS:
        assert set(arm.checks) & prior <= set(CO_CITED.get(arm.row, ())), arm.row
```

Fill the two `<sha256sum>` values with `sha256sum docs/designs/2026-08-24-conformance-cut-10.md docs/plans/2026-08-24-conformance-cut-10-results.md` from the repository root.

- [ ] **Step 3: Write the runner**

`python/tools/cut16_acceptance.py`, from `cut15_acceptance.py` with these differences: `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut16-acceptance"`, `SCIENCE_CUT16_ROOT`, `PREFIX_RUNNERS: tuple[str, ...] = ()`, and

```python
PHASE_MODULES = (
    "test_n2_cut6.py",
    "test_n2_cut7.py",
    "test_n2_cut9.py",
    "test_intent_boundary_acceptance.py",
    "test_n2_cut11.py",
    "test_successor_admission_acceptance.py",
    "test_n2_cut12.py",
    "test_confinement_acceptance.py",
    "test_n2_cut13.py",
    "test_coordination_acceptance.py",
    "test_n2_cut14.py",
    "test_cut15_lineage.py",
    "test_n2_cut15.py",
    "test_permit_acceptance.py",
    "test_permit_boundary.py",  # runs from tests/, not acceptance — see below
    "test_n2_cut16.py",
)
```

`test_permit_boundary.py` lives under `tests/`, so the runner resolves each module against `ACCEPTANCE` first and `PYTHON_ROOT / "tests"` second. `probe()` passes `authority=Authority(WritePermit.full(), "cut16-probe")` to the three `init_*` calls (import from `beliefs.permit`). `cut_environment` sets `SCIENCE_CUT{4..16}_ROOT`. `declared_arm_count()` imports `CUT16_ARMS`; the closing line prints `(= 8 selected + 1 labeled units)`. Drop `run_prefix` and the prefix loop.

- [ ] **Step 4: Run the portable parts, then the full runner on the certified volume**

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/acceptance/test_n2_cut16.py -k "inventory or unique or carried or one_source_mutation or unchanged or frozen"
uv run --frozen python tools/cut16_acceptance.py
```

Expected: the portable accounting tests pass; the runner runs every phase green and prints the declared arm count. If the volume or confinement gate refuses, the runner exits 2 with the exact refusal — report it, do not skip.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks check && git add python && git commit -m "test(cut16): declare the N2 arms, the audit, and the acceptance runner"
```

---

### Task 14: Discharge — results record, ledger, roadmap, guide, banked-design notes, task closure

**Files:**
- Create: `docs/plans/2026-09-04-conformance-cut-16-results.md`
- Modify: `docs/designs/2026-09-04-write-permits-design.md` (status line; §10 file list; nothing in §7/§9)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (Current state: drop the `write-permits` row, add a summary bullet, update the newest-record sentence)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md` (drop `write-permits` from the boundary index, tier 1 and the `authority` lane; re-rank note)
- Modify: `README.md` (design table row status wording; add the results record if the README lists plans)
- Modify: dated amendment notes in `2026-08-11-act-report-design.md` §3, `2026-08-19-family-adapters-design.md`, `2026-08-24-world-index-holdings-design.md`, `2026-08-02-computation-reproducibility-design.md`, `2026-08-30-run-confinement-design.md`, `2026-08-20-world-registry-design.md`, `2026-08-23-world-index-root-lifecycle-design.md` (a "**Amended 2026-09-04 (write permits):** …" note where each describes a caller-supplied actor or an unauthorized seam; frozen cut sections untouched)
- Modify: `docs/guide/foundations.md` or `identity-world-and-change.md` where the guide says a writer or world is opened without authority

- [ ] **Step 1: Write the results record**

Mirror `docs/plans/2026-09-01-conformance-cut-15-results.md`'s sections: header (subject, measured against frozen §7/§9 at `c2f87b3` and §13 at Task 1's hash); §1 accounting (8 selected + 1 labeled = 9 units, N arms); the citation of cut 10 with the pinned shas and the succession by `K1`; §2 what ran (the runner's command, its work root, the exact host tuple, every phase); §3 disposition (E1–E8 close); §4 the by-design stale cut-10 arms named.

- [ ] **Step 2: Move the design status and §10**

Status: `implemented and discharged 2026-09-<dd> at <hash>; conformance cut 16 froze before implementation at c2f87b3 and its 8 selected + 1 labeled units passed through <N> sabotage arms after the current-tree prefix of §13.2. Results: ../plans/2026-09-04-conformance-cut-16-results.md.` §10 gains the files the implementation rewrote beyond its list (at least `runrecord.py`, `world/verify.py`, `stored.py`, the acceptance conftest, and the corrections Task 11 Step 2 recorded).

- [ ] **Step 3: Ledger, roadmap, README, guide, amendment notes**

Apply the edits listed in Files. Then:

```bash
uv run --frozen pytest -q -p no:cacheprovider tests/test_designs_corpus.py
uv run --frozen python tools/check_guide.py
```

Expected: both clean (the corpus test holds the ledger's Current state to the newest results record and the roadmap's index to the ledger's rows).

- [ ] **Step 4: Close the task in the same commit**

```bash
cd .. && tasks done beliefs-96a24a "Write permits landed and cut 16 discharged: Authority bound at every seam, E1-E8 closed, cut 10 cited" && tasks check
git add -A && git commit -m "docs(permit): discharge conformance cut 16 and re-rank the roadmap"
```

Then, per `superpowers:finishing-a-development-branch`, merge `design/write-permits` into `main` with `--no-ff` (the repository's rule for a cut) and note on `beliefs-afbbff` and the science task `sci-c3f0bb` that the permit exports are live.
