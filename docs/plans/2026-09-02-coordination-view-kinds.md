# Coordination and View Kinds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the coordination revision family, closed view-query grammar, contract/profile authorization, multi-corpus resolution, world exclusion, and conformance cut 14.

**Architecture:** Three focused value/parser modules own coordination addresses and stored-shape validation, the coordination contract, and view queries. `corpus.py` remains the sole mutable-corpus owner and adds the path-backed resolver plus two family methods; `ProfileSpec` carries the compiled authorization, while epoch capture excludes everything outside the explicit world-kind allowlist.

**Tech Stack:** Python 3.12, frozen `uv` environment, `nodes` corpus substrate, PyYAML, pytest, Ruff, Pyright, repository `tasks` CLI.

**Spec:** `docs/superpowers/specs/2026-08-31-coordination-and-view-kinds-design.md` at design commit `09b0b58` (frozen cut body §9 at `c07bf72`, approved implementation amendment §11).

## Global Constraints

- Preserve frozen §9 and the cut-5 surface byte-for-byte; cut 14 cites cut 5 and does not run its aggregate runner.
- Build no intent-position helper. W17 remains partial on that clause until `publish` supplies adequate evidence.
- Add exactly two public family methods: `mint_coordination(kind, *, project=None, content)` and `revise_coordination(kind, address, *, predecessors, content)`.
- A coordination writer has no implicit local-only resolver; a missing destination mount refuses before planning.
- Reopen every mounted corpus on every resolver operation. Mount order, names, handles, timestamps, and author identity never choose a tip.
- Keep coordination outside `SEMANTIC_DOMAINS`, every world map, and `belief_input_digest`; store its pin only at `CorpusPins.domains["coordination"]`.
- The v1 query and contract grammars are closed. Fail on unknown members, duplicates, wrong tiers, and unsupported vocabulary; never resolve query addresses during mint.
- Use the existing per-root operation lock and submit one create per coordination revision. Add no generic family framework or new dependency.
- During implementation run only the targeted command named by each task. Run the full Python suite once, in Task 12, on the certified tuple.
- Use the `tasks` CLI for task state. Close each child with its one-line result in the same commit as its code.

## File Structure

- `python/src/beliefs/coordination.py` — coordination address value, stored-facet decoding, pure standing-tip computation, and sealed resolver refusal value.
- `python/src/beliefs/view_query.py` — parsed `science.view-query.v1` values and its closed parser.
- `python/src/beliefs/contract/coordination.py` — parsed coordination contract, content/schema projections, YAML load, and succession validation.
- `python/src/beliefs/profile.py` — compile the optional coordination contract into immutable runtime authorization.
- `python/src/beliefs/corpus.py` — live path-backed resolver, audit integration, and the only two mutation methods.
- `python/src/beliefs/stored.py` — exact world kind/relation inventories and the coordination facet key.
- `python/src/beliefs/world/epoch.py` — retain all bytes in corpus-state capture but build `CapturedRecord` only for world kinds.
- `python/src/beliefs/root.py` — allow the composition root to receive an explicit resolver.
- `python/tests/coordination_fixtures.py` — one canonical v1 contract document plus minimal valid content/profile helpers shared by portable and acceptance tests.
- `python/tests/test_coordination.py`, `test_view_query.py`, `test_coordination_contract.py`, `test_coordination_write.py` — portable value, parser, compiler, resolver, and write-boundary checks.
- `python/tests/acceptance/test_coordination_acceptance.py` — durable W11/W12/W13/W17/W18 checks on the certified volume.
- `python/tests/acceptance/n2_arms_cut14.py`, `test_n2_cut14.py` — cut-14 declarations and sabotage audit.
- `python/tools/cut14_acceptance.py` — exact frozen phase inventory, cut-5 citation pins, durable probe, and cut-14 phases.
- `docs/plans/2026-09-02-conformance-cut-14-results.md` and current-facing design/ledger/roadmap docs — discharge evidence and status correction.

---

### Task 1: Coordination Address, Refusal, and Kernel Inventories

**Files:**
- Create: `python/src/beliefs/coordination.py`
- Modify: `python/src/beliefs/stored.py`
- Modify: `python/src/beliefs/errors.py`
- Test: `python/tests/test_coordination.py`

**Interfaces:**
- Consumes: `beliefs.sealed.sealed`; `nodes.core.node.Node`; existing `WriteRefused`.
- Produces: `COORDINATION_KINDS`, `VIEW_KINDS`, `CoordinationAddress.parse(value: str) -> CoordinationAddress`, `str(CoordinationAddress) -> str`, `CoordinationRefused(reason: Literal["divergent-view", "predecessor-not-standing"], tips: tuple[str, ...])`, `stored.WORLD_KINDS`, `stored.WORLD_RELATIONS`, `stored.COORDINATION_FACET`, and the coordination write-refusal classes used by Tasks 5–8.

- [ ] **Step 1: Write the address, inventory, and closed-refusal tests**

```python
# python/tests/test_coordination.py
from dataclasses import FrozenInstanceError

import pytest

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused

HEX_A = "a" * 32
HEX_B = "b" * 32
HEX_C = "c" * 32


@pytest.mark.parametrize(
    ("wire", "value"),
    [
        (f"coord:{HEX_A}", CoordinationAddress(HEX_A)),
        (f"coord:{HEX_A}@{HEX_C}", CoordinationAddress(HEX_A, revision=HEX_C)),
        (f"coord:{HEX_A}/{HEX_B}", CoordinationAddress(HEX_A, HEX_B)),
        (f"coord:{HEX_A}/{HEX_B}@{HEX_C}", CoordinationAddress(HEX_A, HEX_B, HEX_C)),
    ],
)
def test_coordination_addresses_round_trip_exactly(wire, value):
    assert CoordinationAddress.parse(wire) == value
    assert str(value) == wire


@pytest.mark.parametrize(
    "wire",
    ["coord:a", f"coord:{HEX_A.upper()}", f"coord:{HEX_A}/", f"coord:{HEX_A}//{HEX_B}", f"project:{HEX_A}"],
)
def test_coordination_addresses_refuse_noncanonical_text(wire):
    with pytest.raises(ValueError, match="coordination address"):
        CoordinationAddress.parse(wire)


def test_coordination_addresses_are_frozen():
    address = CoordinationAddress(HEX_A)
    with pytest.raises(FrozenInstanceError):
        address.project = HEX_B


def test_the_resolver_refusal_vocabulary_is_closed_and_tips_are_canonical():
    assert CoordinationRefused("divergent-view", (HEX_B, HEX_A, HEX_A)).tips == (HEX_A, HEX_B)
    with pytest.raises(ValueError, match="reason"):
        CoordinationRefused("new-reason", ())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="tip"):
        CoordinationRefused("divergent-view", ("bad",))


def test_the_world_inventory_is_exactly_the_thirteen_banked_kinds():
    assert stored.WORLD_KINDS == (
        "proposition", "source-assertion", "assessment", "analysis-spec", "run", "verification",
        "dataset", "source", "holdings-observation", "retraction", "instrument-certification",
        "coreference-attestation", "act-report",
    )
    assert not set(stored.WORLD_KINDS) & {"project", "question", "hypothesis", "topic", "theme", "task", "decision", "note"}
```

- [ ] **Step 2: Verify the new module is absent**

Run: `cd python && uv run --frozen pytest tests/test_coordination.py`

Expected: collection fails with `ModuleNotFoundError: No module named 'beliefs.coordination'`.

- [ ] **Step 3: Add the minimal values, inventories, and refusal classes**

```python
# python/src/beliefs/coordination.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, final

from beliefs.sealed import sealed

__all__ = ["COORDINATION_KINDS", "VIEW_KINDS", "CoordinationAddress", "CoordinationRefused"]

VIEW_KINDS = ("project", "question", "hypothesis", "topic", "theme")
COORDINATION_KINDS = (*VIEW_KINDS, "task", "decision", "note")
_ADDRESS = re.compile(r"coord:([0-9a-f]{32})(?:/([0-9a-f]{32}))?(?:@([0-9a-f]{32}))?")
_HEX = re.compile(r"[0-9a-f]{32}")


@sealed
@final
@dataclass(frozen=True)
class CoordinationAddress:
    project: str
    local: str | None = None
    revision: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("project", self.project), ("local", self.local), ("revision", self.revision)):
            if value is not None and _HEX.fullmatch(value) is None:
                raise ValueError(f"coordination address {name} must be 32 lowercase hexadecimal characters")

    @classmethod
    def parse(cls, value: str) -> CoordinationAddress:
        match = _ADDRESS.fullmatch(value) if type(value) is str else None
        if match is None:
            raise ValueError(f"{value!r} is not a canonical coordination address")
        return cls(*match.groups())

    def unpinned(self) -> CoordinationAddress:
        return CoordinationAddress(self.project, self.local)

    def pinned(self, revision: str) -> CoordinationAddress:
        return CoordinationAddress(self.project, self.local, revision)

    def __str__(self) -> str:
        value = f"coord:{self.project}"
        if self.local is not None:
            value += f"/{self.local}"
        return value if self.revision is None else f"{value}@{self.revision}"


CoordinationRefusalReason = Literal["divergent-view", "predecessor-not-standing"]


@sealed
@final
@dataclass(frozen=True)
class CoordinationRefused:
    reason: CoordinationRefusalReason
    tips: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.reason not in ("divergent-view", "predecessor-not-standing"):
            raise ValueError(f"unknown coordination refusal reason {self.reason!r}")
        if any(_HEX.fullmatch(tip) is None for tip in self.tips):
            raise ValueError("coordination refusal tips are 32 lowercase hexadecimal revision ids")
        object.__setattr__(self, "tips", tuple(sorted(set(self.tips))))
```

Add to `stored.py`:

```python
COORDINATION_FACET = "coordination"
WORLD_KINDS = (
    "proposition", "source-assertion", "assessment", "analysis-spec", "run", "verification",
    "dataset", "source", "holdings-observation", "retraction", "instrument-certification",
    "coreference-attestation", "act-report",
)
WORLD_RELATIONS = (
    ASSESSES, OBSERVES, READS, TRANSFORMS, PRODUCES, PRODUCED_BY,
    EXECUTES, TARGETS, VERIFIES, MEMBER_OF, GROUNDED_IN,
)
```

Add distinct `WriteRefused` subclasses to `errors.py`; only `ProjectNotResolvable` carries data:

```python
class CoordinationKindUnsupported(WriteRefused):
    """A world kind used at the coordination door, or a coordination kind used at another family door."""


class CoordinationUnavailable(WriteRefused):
    """The writer's destination is absent from its explicit coordination resolver."""


class PredecessorMismatch(WriteRefused):
    """A predecessor stands but belongs to another kind or coordination address."""


class PredecessorNotStanding(WriteRefused):
    """A supplied predecessor is absent or superseded at the at-commit check."""


class ProjectNotResolvable(WriteRefused):
    def __init__(self, message: str, *, tips: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.tips = tuple(sorted(set(tips)))
```

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination.py && uv run --frozen ruff check src/beliefs/coordination.py src/beliefs/stored.py src/beliefs/errors.py tests/test_coordination.py && uv run --frozen pyright src/beliefs/coordination.py tests/test_coordination.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-f5bb04 "Added canonical coordination addresses, sealed refusals, and exact world inventories."
git add python/src/beliefs/coordination.py python/src/beliefs/stored.py python/src/beliefs/errors.py python/tests/test_coordination.py tasks
git commit -m "feat(coordination): add address and refusal values"
```

### Task 2: Closed View-Query v1 Parser

**Files:**
- Create: `python/src/beliefs/view_query.py`
- Test: `python/tests/test_view_query.py`

**Interfaces:**
- Consumes: `stored.WORLD_KINDS`; `beliefs.identifiers.not_an_identifier`; `CoordinationAddress.parse` only to reject the wrong tier, never to resolve it.
- Produces: immutable predicate values, `ViewQuery.projection() -> dict[str, object]`, `ViewQuery.world_kinds() -> frozenset[str]`, `ViewQuery.relations() -> frozenset[str]`, `ViewQuery.addresses() -> tuple[str, ...]`, and `parse_view_query(value: object) -> ViewQuery`.

- [ ] **Step 1: Write the complete grammar tests**

```python
# python/tests/test_view_query.py
import pytest

from beliefs.view_query import parse_view_query


def test_empty_outer_clauses_are_valid_and_canonical():
    query = parse_view_query({"version": "science.view-query.v1", "clauses": []})
    assert query.projection() == {"version": "science.view-query.v1", "clauses": []}


def test_every_v1_predicate_parses_without_resolving_addresses():
    value = {
        "version": "science.view-query.v1",
        "clauses": [{"all": [
            {"kinds": ["dataset", "proposition"]},
            {"references-term": "biology/gene-1"},
            {"closure": {"anchor": "dataset:not-yet-held", "predicates": ["reads"], "direction": "both"}},
            {"addresses": ["proposition:not-yet-held"]},
        ]}],
    }
    query = parse_view_query(value)
    assert query.world_kinds() == frozenset({"dataset", "proposition"})
    assert query.relations() == frozenset({"reads"})
    assert query.addresses() == ("dataset:not-yet-held", "proposition:not-yet-held")


def test_reordering_set_like_members_does_not_move_the_canonical_projection():
    first = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset", "proposition"]}, {"addresses": ["dataset:b", "dataset:a"]}]}]}
    second = {"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": ["dataset:a", "dataset:b"]}, {"kinds": ["proposition", "dataset"]}]}]}
    assert parse_view_query(first).projection() == parse_view_query(second).projection()


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"version": "science.view-query.v2", "clauses": []},
        {"version": "science.view-query.v1", "clauses": [], "extra": True},
        {"version": "science.view-query.v1", "clauses": [{"all": []}]},
        {"version": "science.view-query.v1", "clauses": [{"any": [{"kinds": ["dataset"]}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"unknown": "x"}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": []}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"closure": {"anchor": "dataset:x", "predicates": [], "direction": "out"}}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"closure": {"anchor": "dataset:x", "predicates": ["reads"], "direction": "sideways"}}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": ["coord:" + "a" * 32]}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": ["note:x"]}]}]},
    ],
)
def test_the_v1_grammar_is_closed(value):
    with pytest.raises(ValueError, match="view query"):
        parse_view_query(value)
```

- [ ] **Step 2: Verify the parser is absent**

Run: `cd python && uv run --frozen pytest tests/test_view_query.py`

Expected: collection fails on `beliefs.view_query`.

- [ ] **Step 3: Implement the parser as four value types, not an evaluator**

Use frozen dataclasses `Kinds`, `ReferencesTerm`, `Closure`, `Addresses`, `Clause`, and `ViewQuery`. The parser must use exact-key checks and the following central helpers; it must not accept a resolver parameter:

```python
VIEW_QUERY_VERSION = "science.view-query.v1"


def _world_address(value: object, where: str) -> str:
    if type(value) is not str:
        raise ValueError(f"view query {where} must be a world address string")
    kind, separator, local = value.partition(":")
    if separator != ":" or kind not in stored.WORLD_KINDS or not local or value.startswith("coord:"):
        raise ValueError(f"view query {where} must be a world-tier address")
    return value


def _distinct_strings(value: object, where: str) -> tuple[str, ...]:
    if type(value) is not list or not value or any(type(member) is not str or not member for member in value):
        raise ValueError(f"view query {where} must be a non-empty string list")
    members = tuple(value)
    if len(set(members)) != len(members):
        raise ValueError(f"view query {where} must not repeat a member")
    return tuple(sorted(members))
```

`parse_view_query` must require exactly `{"version", "clauses"}`, exact version v1, a list of clauses, exactly `{"all"}` per clause, non-empty predicate lists, exactly one recognized predicate key, and exact closure keys `{"anchor", "predicates", "direction"}`. `ViewQuery.projection()` emits lists and mappings in canonical sorted order; order predicates by `v1.encode(predicate.projection())`. Its introspection methods union only literal values and never inspect a corpus.

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_view_query.py && uv run --frozen ruff check src/beliefs/view_query.py tests/test_view_query.py && uv run --frozen pyright src/beliefs/view_query.py tests/test_view_query.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-07a924 "Added the closed, canonical science.view-query.v1 parser without evaluation."
git add python/src/beliefs/view_query.py python/tests/test_view_query.py tasks
git commit -m "feat(coordination): parse view query v1"
```

### Task 3: Coordination Contract and Succession

**Files:**
- Create: `python/src/beliefs/contract/coordination.py`
- Modify: `python/src/beliefs/contract/__init__.py`
- Create: `python/tests/coordination_fixtures.py`
- Test: `python/tests/test_coordination_contract.py`

**Interfaces:**
- Consumes: `identity.v1`, `MalformedContract`, `SuccessionViolation`, `UnparsedContract`, PyYAML.
- Produces: `CoordinationKindDecl(fields: tuple[str, ...], query_versions: tuple[str, ...])`, parsed-only `CoordinationContract`, `parse_coordination_contract(document: object, *, source: str, predecessor: CoordinationContract | None) -> CoordinationContract`, `load_coordination_contract(path: Path, *, predecessor: CoordinationContract | None) -> CoordinationContract`, and `check_coordination_succession`.

- [ ] **Step 1: Add the one shared v1 document and parser tests**

```python
# python/tests/coordination_fixtures.py
from copy import deepcopy

from beliefs.contract.coordination import parse_coordination_contract

COORDINATION_DOCUMENT = {
    "contract": "coordination",
    "version": 1,
    "lineage": "genesis",
    "description": "Project coordination records",
    "address_root": "project",
    "query_vocabulary": {
        "kinds": ["proposition", "source-assertion", "assessment", "analysis-spec", "run", "verification", "dataset", "source", "holdings-observation", "retraction", "instrument-certification", "coreference-attestation", "act-report"],
        "relations": ["assesses", "observes", "reads", "transforms", "produces", "produced_by", "executes", "targets", "verifies", "member_of", "grounded-in"],
    },
    "kinds": {
        **{kind: {"fields": ["name", "body", "author", "at", "query"], "query_versions": ["science.view-query.v1"]} for kind in ("project", "question", "hypothesis", "topic", "theme")},
        "task": {"fields": ["name", "body", "author", "at", "status", "depends"], "query_versions": []},
        "decision": {"fields": ["name", "body", "author", "at"], "query_versions": []},
        "note": {"fields": ["name", "body", "author", "at", "about"], "query_versions": []},
    },
}


def coordination_contract(document=None, predecessor=None):
    return parse_coordination_contract(
        deepcopy(COORDINATION_DOCUMENT if document is None else document),
        source="<coordination-test>",
        predecessor=predecessor,
    )
```

```python
# python/tests/test_coordination_contract.py
import copy

import pytest

from beliefs.contract.coordination import CoordinationContract, load_coordination_contract, parse_coordination_contract
from beliefs.errors import MalformedContract, SuccessionViolation
from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract


def successor(predecessor, **changes):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document.update(changes)
    document["version"] = predecessor.version + 1
    document["lineage"] = {"successor": predecessor.content_identity}
    return document


def test_v1_parses_to_the_exact_schema_projection():
    contract = coordination_contract()
    assert isinstance(contract, CoordinationContract)
    assert contract.namespace == "coordination"
    assert contract.schema_projection()["address_root"] == "project"
    assert tuple(contract.kinds) == tuple(sorted(COORDINATION_DOCUMENT["kinds"]))


@pytest.mark.parametrize("field", ["contract", "version", "lineage", "address_root", "query_vocabulary", "kinds"])
def test_every_required_root_member_is_required(field):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    del document[field]
    with pytest.raises(MalformedContract):
        coordination_contract(document)


def test_kind_members_are_closed():
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["kinds"]["project"]["extra"] = True
    with pytest.raises(MalformedContract, match="exactly"):
        coordination_contract(document)


@pytest.mark.parametrize("path", [("kinds", "project", "fields"), ("kinds", "project", "query_versions"), ("query_vocabulary", "kinds"), ("query_vocabulary", "relations")])
def test_declared_sets_refuse_duplicates(path):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    value = document
    for part in path:
        value = value[part]
    value.append(value[0])
    with pytest.raises(MalformedContract, match="duplicate"):
        coordination_contract(document)


def test_editorial_successor_preserves_schema_projection_and_moves_content_identity():
    genesis = coordination_contract()
    edited = successor(genesis, description="Reworded")
    current = coordination_contract(edited, genesis)
    assert current.content_identity != genesis.content_identity
    assert current.schema_projection() == genesis.schema_projection()


def test_a_successor_may_add_a_kind_and_query_vocabulary():
    genesis = coordination_contract()
    document = successor(genesis)
    document["kinds"]["publication"] = {"fields": ["name", "body", "author", "at"], "query_versions": []}
    document["query_vocabulary"]["kinds"].append("future-world-kind")
    document["query_vocabulary"]["relations"].append("future-relation")
    current = coordination_contract(document, genesis)
    assert "publication" in current.kinds
    assert "future-world-kind" in current.query_kinds
    assert "future-relation" in current.query_relations


def test_yaml_duplicate_keys_refuse_at_load(tmp_path):
    path = tmp_path / "coordination.yaml"
    path.write_text("contract: coordination\ncontract: coordination\n", encoding="utf-8")
    with pytest.raises(MalformedContract, match="duplicate"):
        load_coordination_contract(path, predecessor=None)


@pytest.mark.parametrize("change", ["address_root", "drop_kind", "change_fields", "drop_query_version", "drop_query_kind", "drop_query_relation"])
def test_succession_refuses_every_redefinition(change):
    genesis = coordination_contract()
    document = successor(genesis)
    if change == "address_root": document["address_root"] = "question"
    elif change == "drop_kind": del document["kinds"]["note"]
    elif change == "change_fields": document["kinds"]["note"]["fields"].remove("about")
    elif change == "drop_query_version": document["kinds"]["project"]["query_versions"] = []
    elif change == "drop_query_kind": document["query_vocabulary"]["kinds"].pop()
    else: document["query_vocabulary"]["relations"].pop()
    with pytest.raises(SuccessionViolation):
        coordination_contract(document, genesis)
```

- [ ] **Step 2: Verify the contract module is absent**

Run: `cd python && uv run --frozen pytest tests/test_coordination_contract.py`

Expected: collection fails on `beliefs.contract.coordination`.

- [ ] **Step 3: Implement the parsed-only contract**

Use one local duplicate-detecting `SafeLoader`; neither existing contract loader detects duplicate YAML keys, and the world-registry loader has unrelated scalar coercion. Pin the complete loader rather than relying on `safe_load`'s last-writer-wins behavior:

```python
class _CoordinationLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _CoordinationLoader, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_CoordinationLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)
```

`load_coordination_contract` uses `yaml.load(..., Loader=_CoordinationLoader)` and wraps YAML/shape failures as `MalformedContract`, preserving the duplicate-key text. The exact schema projection is:

```python
def schema_projection(self) -> dict[str, object]:
    return {
        "address_root": self.address_root,
        "kinds": {name: self.kinds[name].projection() for name in sorted(self.kinds)},
        "query_vocabulary": {
            "kinds": sorted(self.query_kinds),
            "relations": sorted(self.query_relations),
        },
    }
```

The content identity is `v1.digest("science.coordination-contract.v1", root)`. Parse `lineage` as either literal `"genesis"` or exact `{"successor": <coordination identity>}`. Store all list-shaped sets as sorted tuples behind `MappingProxyType`. `check_coordination_succession` must run from both parse and load and apply, in order: genesis/predecessor agreement, exact predecessor identity, coordination namespace, stable `address_root`, no dropped kind, identical existing field sets, monotone per-kind query versions, monotone query-kind vocabulary, monotone query-relation vocabulary. Adding a kind or adding vocabulary is allowed.

Re-export only the concrete coordination names from `contract/__init__.py`; keep domain's existing `check_succession` export unchanged and export the new check as `check_coordination_succession`.

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination_contract.py && uv run --frozen ruff check src/beliefs/contract/coordination.py src/beliefs/contract/__init__.py tests/coordination_fixtures.py tests/test_coordination_contract.py && uv run --frozen pyright src/beliefs/contract/coordination.py tests/test_coordination_contract.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-05575d "Added the closed coordination contract parser and monotone succession check."
git add python/src/beliefs/contract python/tests/coordination_fixtures.py python/tests/test_coordination_contract.py tasks
git commit -m "feat(coordination): parse coordination contracts"
```

### Task 4: Compile Coordination Authorization into Profiles

**Files:**
- Modify: `python/src/beliefs/profile.py`
- Modify: `python/src/beliefs/contract/domain.py`
- Modify: `python/tests/coordination_fixtures.py`
- Modify: `python/tests/test_profile.py`
- Modify: `python/tests/test_domain_contract.py`

**Interfaces:**
- Consumes: `CoordinationContract.schema_projection()`, `stored.WORLD_KINDS`, `stored.WORLD_RELATIONS`.
- Produces: `CompiledCoordinationKind`, `ProfileSpec.coordination_kinds`, `.coordination_address_root`, `.coordination_query_kinds`, `.coordination_query_relations`, and `compile_profile(base, domains, *, coordination: CoordinationContract | None = None) -> ProfileSpec`.

- [ ] **Step 1: Add compiler and reserved-namespace tests**

```python
# append to python/tests/test_profile.py; reuse its existing copy, pytest, and ProfileError imports
from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract


def test_coordination_compiles_into_immutable_authorization(base_contract):
    contract = coordination_contract()
    compiled = compile_profile(base_contract, [], coordination=contract)
    assert set(compiled.coordination_kinds) == set(contract.kinds)
    assert compiled.coordination_address_root == "project"
    assert compiled.coordination_query_kinds == frozenset(contract.query_kinds)
    assert compiled.coordination_query_relations == frozenset(contract.query_relations)
    assert compiled.activated_contracts["coordination"] == contract.content_identity


def test_no_coordination_contract_preserves_the_pre_cut_compiled_identity(base_contract):
    before = compile_profile(base_contract, [])
    assert before.compiled_identity == "343e9aecf49a0042962a92921da3d3a9e5416a42638e20e7a906658b806af411"
    assert compile_profile(base_contract, [], coordination=None).compiled_identity == before.compiled_identity
    assert before.coordination_kinds == {}


def test_coordination_editorial_edits_do_not_recompile(base_contract):
    genesis = coordination_contract()
    editorial_document = copy.deepcopy(COORDINATION_DOCUMENT)
    editorial_document.update(version=2, lineage={"successor": genesis.content_identity}, description="new words")
    editorial = coordination_contract(editorial_document, genesis)
    assert editorial.content_identity != genesis.content_identity
    assert compile_profile(base_contract, [], coordination=editorial).compiled_identity == compile_profile(base_contract, [], coordination=genesis).compiled_identity


def test_coordination_schema_edits_recompile(base_contract):
    genesis = coordination_contract()
    schema_document = copy.deepcopy(COORDINATION_DOCUMENT)
    schema_document["version"] = 2
    schema_document["kinds"]["publication"] = {
        "fields": ["name", "body", "author", "at"],
        "query_versions": [],
    }
    schema = coordination_contract(schema_document)
    assert compile_profile(base_contract, [], coordination=schema).compiled_identity != compile_profile(base_contract, [], coordination=genesis).compiled_identity


def test_coordination_compile_refuses_unknown_query_kind(base_contract):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["kinds"].append("not-world")
    with pytest.raises(ProfileError, match="query vocabulary"):
        compile_profile(base_contract, [], coordination=coordination_contract(document))


def test_coordination_compile_refuses_unknown_query_relation(base_contract):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["relations"].append("not-a-relation")
    with pytest.raises(ProfileError, match="query vocabulary"):
        compile_profile(base_contract, [], coordination=coordination_contract(document))
```

```python
# append to python/tests/test_domain_contract.py
def test_a_domain_contract_cannot_claim_the_coordination_namespace(base_contract, testing_document):
    testing_document["contract"] = "coordination"
    with pytest.raises(MalformedContract, match="reserved"):
        domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
```

- [ ] **Step 2: Verify the focused tests fail for missing profile members**

Run: `cd python && uv run --frozen pytest tests/test_profile.py tests/test_domain_contract.py`

Expected: FAIL because `compile_profile` has no `coordination` parameter and the reserved namespace is accepted.

- [ ] **Step 3: Extend the compiler without moving legacy no-coordination identities**

Add:

```python
@dataclass(frozen=True)
class CompiledCoordinationKind:
    fields: frozenset[str]
    query_versions: frozenset[str]

    def projection(self) -> dict[str, object]:
        return {"fields": sorted(self.fields), "query_versions": sorted(self.query_versions)}
```

Extend `_projection` with an optional `coordination` mapping and add the `"coordination"` member only when the argument is not `None`. That omission is required: existing profiles compiled without coordination keep their exact identity. `compile_profile` validates `CoordinationContract` provenance, validates both literal vocabularies against the exact stored inventories, adds `activated_contracts["coordination"]`, freezes every new field, and passes the schema projection rather than the contract identity into `_projection`.

Pin the compiler anchors used by W18's identity and inventory sabotages:

```python
def _coordination_projection(contract: CoordinationContract) -> dict[str, object]:
    return contract.schema_projection()


    unknown_kinds = set(coordination.query_kinds) - set(stored.WORLD_KINDS)
    unknown_relations = set(coordination.query_relations) - set(stored.WORLD_RELATIONS)
    if unknown_kinds or unknown_relations:
        raise ProfileError("coordination query vocabulary is outside the kernel inventory")
```

In `parse_domain_contract`, immediately after parsing `namespace`, pin this exact implementation line for W18's N2 arm:

```python
    if namespace == "coordination":
        raise MalformedContract(f"{source}: 'coordination' is reserved for the coordination contract")
```

Extend `coordination_fixtures.py` with:

```python
def coordination_profile(base_contract, *, document=None):
    return compile_profile(base_contract, [], coordination=coordination_contract(document))
```

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_profile.py tests/test_domain_contract.py && uv run --frozen ruff check src/beliefs/profile.py src/beliefs/contract/domain.py tests/coordination_fixtures.py tests/test_profile.py tests/test_domain_contract.py && uv run --frozen pyright src/beliefs/profile.py src/beliefs/contract/domain.py tests/test_profile.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-30cfd7 "Compiled optional coordination authorization into ProfileSpec and reserved its namespace."
git add python/src/beliefs/profile.py python/src/beliefs/contract/domain.py python/tests/coordination_fixtures.py python/tests/test_profile.py python/tests/test_domain_contract.py tasks
git commit -m "feat(coordination): compile coordination profiles"
```

### Task 5: Stored Revision Validation, Live Resolver, and Audit

**Files:**
- Modify: `python/src/beliefs/coordination.py`
- Modify: `python/src/beliefs/corpus.py`
- Modify: `python/tests/coordination_fixtures.py`
- Modify: `python/tests/test_coordination.py`
- Create: `python/tests/test_coordination_write.py`

**Interfaces:**
- Consumes: `ProfileSpec`, `CorpusPins`, `load_manifest`, `ReadView.opened_at`, `stored.COORDINATION_FACET`, `stored.SUPERSEDES`.
- Produces: `CoordinationRevision`, `coordination_revision(node: Node) -> CoordinationRevision`, `coordination_facet_malformed(node: Node) -> bool`, `standing_tips(revisions: Sequence[CoordinationRevision]) -> tuple[CoordinationRevision, ...]`, `CoordinationResolver(mounts: Mapping[Path, ProfileSpec])`, `.profile(root: Path) -> ProfileSpec | None`, `.revision(uid: str)`, `.tips(address: CoordinationAddress)`, `.resolve(address: CoordinationAddress)`, plus audit codes `coordination-facet-malformed` and `coordination-supersession-cycle`.

- [ ] **Step 1: Add raw stored-node helpers and focused resolver tests**

Extend `coordination_fixtures.py` with real corpus construction helpers:

```python
from typing import ClassVar

from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.corpus import CorpusWriter

AT = "2026-09-02T12:00:00Z"


def pins_for(profile):
    return CorpusPins(
        "science:" + profile.base_contract_identity,
        {namespace: f"{namespace}:{identity}" for namespace, identity in profile.activated_contracts.items()},
    )


def raw_coordination_node(kind, project, revision, *, local=None, supersedes=(), **facet):
    node_id = f"project:{project}.{revision}" if kind == "project" else f"{kind}:{project}.{local}.{revision}"
    if kind in {"project", "question", "hypothesis", "topic", "theme"}:
        facet.setdefault("query", {"version": "science.view-query.v1", "clauses": []})
    elif kind == "task":
        facet.setdefault("status", "open")
        facet.setdefault("depends", [])
    return Node(
        id=node_id,
        uid=revision,
        kind=kind,
        title=facet.pop("name", kind),
        body=facet.pop("body", ""),
        facets={stored.COORDINATION_FACET: {"project": project, **({} if local is None else {"local": local}), "author": facet.pop("author", "actor"), "at": facet.pop("at", AT), **facet}},
        relations=[Relation(source=node_id, predicate=stored.SUPERSEDES, target=target) for target in supersedes],
    )


class Recorder:
    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


def mounted_root(root, profile, executor_factory=DefaultExecutor):
    CorpusWriter(root, executor_factory).adopt_manifest(profile=pins_for(profile))
    return root


def raw_add(root, *nodes):
    corpus = Corpus(root)
    for node in nodes:
        corpus.add(node)
```

Write these tests in `test_coordination_write.py`:

```python
import pytest
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver, CorpusWriter, corpus_check
from coordination_fixtures import Recorder, coordination_profile, mounted_root, raw_add, raw_coordination_node

A, B, C, D = (character * 32 for character in "abcd")


def test_resolver_reopens_every_mount_and_is_order_inert(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    forward = CoordinationResolver({left: profile, right: profile})
    assert forward.resolve(CoordinationAddress(A)) == first
    raw_add(right, second)  # committed after resolver construction
    assert forward.resolve(CoordinationAddress(A)) == CoordinationRefused("divergent-view", (C, D))
    assert CoordinationResolver({right: profile, left: profile}).resolve(CoordinationAddress(A)) == CoordinationRefused("divergent-view", (C, D))


def test_a_pinned_address_reads_an_immutable_superseded_revision(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    old = raw_coordination_node("project", A, C)
    new = raw_coordination_node("project", A, D, supersedes=(old.id,))
    raw_add(root, old, new)
    resolver = CoordinationResolver({root: profile})
    assert resolver.resolve(CoordinationAddress(A)) == new
    assert resolver.resolve(CoordinationAddress(A, revision=C)) == old


def test_malformed_facets_are_reported_and_excluded_from_tips(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    valid = raw_coordination_node("project", A, C)
    malformed = raw_coordination_node("project", A, D)
    malformed.facets[stored.COORDINATION_FACET]["project"] = "bad"
    raw_add(root, valid, malformed)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress(A)) == valid
    assert [(finding.code, finding.ref) for finding in corpus_check(CorpusWriter(root, DefaultExecutor).read_view) if finding.code.startswith("coordination-")] == [("coordination-facet-malformed", malformed.id)]


def test_a_raw_local_cycle_has_no_tip_and_has_an_audit_finding(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    first.relations = [Relation(source=first.id, predicate=stored.SUPERSEDES, target=second.id)]
    second.relations = [Relation(source=second.id, predicate=stored.SUPERSEDES, target=first.id)]
    raw_add(root, first, second)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress(A)) is None
    assert any(finding.code == "coordination-supersession-cycle" for finding in corpus_check(CorpusWriter(root, DefaultExecutor).read_view))
```

Also test that resolver construction raises `ContractMismatch` when the supplied profile's base or activated-contract table differs from the mounted manifest.

- [ ] **Step 2: Verify the resolver tests fail**

Run: `cd python && uv run --frozen pytest tests/test_coordination.py tests/test_coordination_write.py`

Expected: FAIL because the stored decoder and resolver do not exist.

- [ ] **Step 3: Add one strict stored decoder and the pure tip function**

`CoordinationRevision` carries `node`, `address`, and predecessor node ids. `coordination_revision` validates the contract-independent stored envelope only: a coordination mapping and no other top-level facet; exact address halves and node-id formula; a 32-lower-hex revision uid; non-empty author; RFC3339 `at`; and only distinct, directed, correct-source `supersedes` relations with syntactically valid targets. It deliberately does not reproduce per-kind field sets or query/status/reference rules: the mounted contract and Task 6's writer validator are their single source. An unknown future kind is structurally decodable but gains no authorization from that fact; the mounted profile decides whether it participates.

Pin its name-independent address construction:

```python
    address = CoordinationAddress(project=facet["project"], local=facet.get("local"))
```

Pin the pure algorithm in `coordination.py`:

```python
def standing_tips(revisions: Sequence[CoordinationRevision]) -> tuple[CoordinationRevision, ...]:
    by_id = {revision.node.id: revision for revision in revisions}
    superseded = {
        predecessor
        for revision in revisions
        for predecessor in revision.predecessors
        if predecessor in by_id
    }
    return tuple(sorted((revision for revision in revisions if revision.node.id not in superseded), key=lambda revision: revision.node.uid))
```

The public boolean is one implementation of the decoder:

```python
def coordination_facet_malformed(node: Node) -> bool:
    try:
        coordination_revision(node)
    except MalformedRecord:
        return True
    return False
```

- [ ] **Step 4: Add the live resolver in `corpus.py`**

Construction resolves each `Path`, rejects duplicate resolved roots, requires every value to be `ProfileSpec`, loads each manifest, and compares it with the namespaced wire pins from `pins_for`: `science:<base content identity>` and `<namespace>:<contract content identity>`. Store an immutable path-to-profile mapping. Production code must build that expected `CorpusPins` itself; test helpers are not importable from the package.

Every `revision`, `tips`, and `resolve` call invokes a private `_revisions()` that opens `ReadView.opened_at(root)` afresh, decodes only nodes carrying the coordination facet whose kind that root's mounted profile declares, excludes `MalformedRecord`, and deduplicates byte-equal replica copies by `uid`. Thus a raw undeclared future kind claims no address. A repeated uid carrying unequal nodes raises `MalformedRecord`; it never picks one. `tips` groups on the unpinned address. `resolve` returns the exact pinned revision when `address.revision` is set, otherwise `None`, one node, or `CoordinationRefused("divergent-view", ...)`.

The grouping line is name-blind:

```python
        revisions = tuple(revision for revision in self._revisions() if revision.address == address.unpinned())
```

Pin the exclusion and divergence anchors:

```python
                if coordination_facet_malformed(node):
                    continue
```

```python
        if len(tips) > 1:
            return CoordinationRefused("divergent-view", tuple(revision.node.uid for revision in tips))
        return tips[0].node
```

Pin this tolerant destination lookup. Coordination writes turn absence into `CoordinationUnavailable`; ordinary writes use the same lookup without requiring a mount:

```python
    def profile(self, root: Path) -> ProfileSpec | None:
        return self._mounts.get(Path(root).resolve())
```

- [ ] **Step 5: Integrate the two audit findings**

In `corpus_check`, collect malformed coordination nodes before other per-node checks. Exclude coordination `supersedes` edges from the existing corpus-local missing-target finding because lawful revisions may target a predecessor held in another mounted root. Group locally valid revisions by address, call `standing_tips`, and when a non-empty group has zero tips add:

```python
Finding(
    severity="error",
    code="coordination-supersession-cycle",
    ref=str(address),
    detail=",".join(sorted(revision.node.uid for revision in revisions)),
    message=f"{address}: coordination supersession graph has no standing tip",
)
```

The guard above the finding is exactly:

```python
        if revisions and not standing_tips(revisions):
```

- [ ] **Step 6: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination.py tests/test_coordination_write.py && uv run --frozen ruff check src/beliefs/coordination.py src/beliefs/corpus.py tests/coordination_fixtures.py tests/test_coordination_write.py && uv run --frozen pyright src/beliefs/coordination.py src/beliefs/corpus.py tests/test_coordination_write.py`

Expected: PASS.

- [ ] **Step 7: Close the task and commit**

```bash
tasks done beliefs-4b9383 "Added strict coordination facet decoding, fresh multi-root resolution, tips, and audit findings."
git add python/src/beliefs/coordination.py python/src/beliefs/corpus.py python/tests/coordination_fixtures.py python/tests/test_coordination.py python/tests/test_coordination_write.py tasks
git commit -m "feat(coordination): resolve live revision tips"
```

### Task 6: Coordination Genesis Door

**Files:**
- Modify: `python/src/beliefs/corpus.py`
- Modify: `python/src/beliefs/root.py`
- Modify: `python/tests/coordination_fixtures.py`
- Modify: `python/tests/test_coordination_write.py`

**Interfaces:**
- Consumes: `CoordinationResolver.profile/resolve`, compiled kind specs, `parse_view_query`, existing `_refuse_already_minted`, `_refuse_rendering`, per-root lock, and one-create `Corpus.add` path.
- Produces: `CorpusWriter(..., coordination_resolver: CoordinationResolver | None = None)`, `open_corpus(corpus_root: Path, *, coordination_resolver: CoordinationResolver | None = None)`, and `CorpusWriter.mint_coordination(kind: str, *, project: CoordinationAddress | None = None, content: Mapping[str, object]) -> Node`.

- [ ] **Step 1: Add valid content helpers and genesis tests**

```python
# append to python/tests/coordination_fixtures.py
EMPTY_QUERY = {"version": "science.view-query.v1", "clauses": []}


def content_for(kind, *, name=None, **changes):
    content = {"name": name or kind, "body": "", "author": "actor", "at": AT}
    if kind in {"project", "question", "hypothesis", "topic", "theme"}:
        content["query"] = EMPTY_QUERY
    elif kind == "task":
        content.update(status="open", depends=[])
    content.update(changes)
    return content
```

Add tests:

```python
from copy import deepcopy

from beliefs.errors import CoordinationUnavailable, ProjectNotResolvable, ValidationRefused
from beliefs.profile import compile_profile
from coordination_fixtures import COORDINATION_DOCUMENT, Recorder, content_for, coordination_contract


def writer_with_resolver(root, profile):
    mounted_root(root, profile)
    resolver = CoordinationResolver({root: profile})
    return CorpusWriter(root, DefaultExecutor, coordination_resolver=resolver), resolver


def test_project_and_subordinate_genesis_have_adapter_owned_shape(tmp_path, base_contract, monkeypatch):
    profile = coordination_profile(base_contract)
    writer, resolver = writer_with_resolver(tmp_path, profile)
    values = iter((A, B, C, D))
    monkeypatch.setattr("beliefs.corpus.secrets.token_hex", lambda _: next(values))
    project = writer.mint_coordination("project", content=content_for("project", name="Old name"))
    question = writer.mint_coordination("question", project=CoordinationAddress(A), content=content_for("question"))
    assert (project.id, project.uid, project.relations) == (f"project:{A}.{B}", B, [])
    assert (question.id, question.uid, question.relations) == (f"question:{A}.{C}.{D}", D, [])
    assert set(project.facets) == {stored.COORDINATION_FACET}
    assert resolver.resolve(CoordinationAddress(A)) == project
    assert resolver.resolve(CoordinationAddress(A, C)) == question


def test_a_coordination_call_without_a_destination_mount_plans_nothing(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    mounted_root(tmp_path, profile, Recorder)
    Recorder.plans = []
    writer = CorpusWriter(tmp_path, Recorder, coordination_resolver=CoordinationResolver({}))
    with pytest.raises(CoordinationUnavailable):
        writer.mint_coordination("project", content=content_for("project"))
    assert Recorder.plans == []


def test_a_mounted_profile_without_a_coordination_contract_authorizes_nothing(tmp_path, base_contract):
    profile = compile_profile(base_contract, [])
    mounted_root(tmp_path, profile)
    writer = CorpusWriter(tmp_path, DefaultExecutor, coordination_resolver=CoordinationResolver({tmp_path: profile}))
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination("project", content=content_for("project"))


def test_a_subordinate_requires_one_resolvable_project(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=CoordinationAddress(A), content=content_for("task"))
    assert caught.value.tips == ()


@pytest.mark.parametrize("mutation", ["missing", "extra", "bad-at", "bad-status", "world-depends", "coord-about"])
def test_content_is_closed_and_tier_checked(tmp_path, base_contract, mutation):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project"))
    project_address = coordination_revision(project).address
    kind = "task" if mutation in {"bad-status", "world-depends"} else "note"
    content = content_for(kind)
    if mutation == "missing": del content["author"]
    elif mutation == "extra": content["extra"] = True
    elif mutation == "bad-at": content["at"] = "today"
    elif mutation == "bad-status": content["status"] = "later"
    elif mutation == "world-depends": content["depends"] = ["dataset:x"]
    else: content["about"] = [str(project_address)]
    with pytest.raises(ValidationRefused):
        writer.mint_coordination(kind, project=project_address, content=content)
```

Add focused tests for malformed query syntax and a well-formed unresolved world anchor. For literal contract authorization, use valid narrowed genesis contracts so the parser accepts the world vocabulary and only the mounted contract can decide:

```python
def writer_with_document(root, base_contract, document):
    profile = coordination_profile(base_contract, document=document)
    return writer_with_resolver(root, profile)[0]


def test_w18c_a_query_kind_outside_the_contract_refuses(tmp_path, base_contract):
    document = deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["kinds"].remove("dataset")
    writer = writer_with_document(tmp_path, base_contract, document)
    with pytest.raises(ValidationRefused, match="world kind"):
        writer.mint_coordination("project", content=content_for("project", query={"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset"]}]}]}))


def test_w18d_a_query_relation_outside_the_contract_refuses(tmp_path, base_contract):
    document = deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["relations"].remove("reads")
    writer = writer_with_document(tmp_path, base_contract, document)
    with pytest.raises(ValidationRefused, match="relation"):
        writer.mint_coordination("project", content=content_for("project", query={"version": "science.view-query.v1", "clauses": [{"all": [{"closure": {"anchor": "dataset:not-held", "predicates": ["reads"], "direction": "out"}}]}]}))


def test_an_earlier_contract_version_authorizes_nothing_added_later(tmp_path, base_contract):
    genesis = coordination_contract()
    document = deepcopy(COORDINATION_DOCUMENT)
    document.update(version=2, lineage={"successor": genesis.content_identity})
    document["kinds"]["publication"] = {"fields": ["name", "body", "author", "at"], "query_versions": []}
    amended = coordination_contract(document, genesis)
    old_profile = compile_profile(base_contract, [], coordination=genesis)
    assert "publication" in compile_profile(base_contract, [], coordination=amended).coordination_kinds
    mounted_root(tmp_path, old_profile)
    writer = CorpusWriter(tmp_path, DefaultExecutor, coordination_resolver=CoordinationResolver({tmp_path: old_profile}))
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination("publication", project=coordination_revision(project).address, content=content_for("decision"))
```

Wrap `parse_view_query`'s `ValueError` as `ValidationRefused` at this boundary, preserving it as `__cause__`.

- [ ] **Step 2: Verify the public door is absent**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py`

Expected: FAIL because `CorpusWriter` has no `mint_coordination`.

- [ ] **Step 3: Add the optional resolver and exact content validator**

Store the resolver unchanged on the writer. The validator must:

1. reject a world kind with `CoordinationKindUnsupported`, before profile lookup;
2. get the destination profile with `resolver.profile(root)` and raise `CoordinationUnavailable` when it returns `None`, before generating identities;
3. use `profile.coordination_kinds.get(kind)` and raise `ValidationRefused` if absent;
4. require exactly the declared fields, except `note.about` may be omitted;
5. require non-empty string `name` and `author`, string `body`, and an `at` matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})` whose calendar/timezone value parses through `datetime.fromisoformat(at.replace("Z", "+00:00"))`;
6. require task status in `{"open", "done", "dropped"}` and distinct coordination addresses in `depends`;
7. require world-tier addresses in optional `about`;
8. parse query syntax, require its version in the compiled kind's permission, and enforce its literal kind/relation subsets without resolving any address.

The wrong-family guard is exactly:

```python
        if kind in stored.WORLD_KINDS:
            raise CoordinationKindUnsupported(f"{kind!r} is a world kind, not a coordination kind")
```

Pin these W18 implementation lines for N2:

```python
        kind_spec = profile.coordination_kinds.get(kind)
        if kind_spec is None:
            raise ValidationRefused(f"{kind!r} is not declared by the mounted coordination contract")
```

```python
        query = parse_view_query(content["query"])
        if query.world_kinds() - profile.coordination_query_kinds:
            raise ValidationRefused("view query names a world kind outside the coordination contract vocabulary")
        if query.relations() - profile.coordination_query_relations:
            raise ValidationRefused("view query names a relation outside the coordination contract vocabulary")
        return query
```

The coordination-reference helper is the one check used for every authored `depends` value:

```python
def _coordination_reference(value: object) -> str:
    if type(value) is not str:
        raise ValidationRefused("a coordination reference is a string")
    try:
        CoordinationAddress.parse(value)
    except ValueError as caught:
        raise ValidationRefused(str(caught)) from caught
    return value
```

Import and reuse `view_query._world_address` for every authored `about` value, translating its `ValueError` to `ValidationRefused`; do not restate its tier predicate. Store `depends` and `about` sorted after validation. Replace authored `query` with `query.projection()` in the validated content passed to `_coordination_node`, so the parser is the one implementation of both accepted form and stored canonical spelling.

- [ ] **Step 4: Implement genesis under the existing operation lock**

The method validates `project=None` only for kind `project`; for other kinds it requires an unpinned project-root address (`local is None`, `revision is None`) and resolves it to one project node. Missing and divergent project resolution raise `ProjectNotResolvable`, copying refusal tips in the latter case.

Generate project/local/revision ids only after all refusal-only inputs are validated. Build `Node.title/body`, the sole coordination facet, and no relations. Pin the identity generation lines for W13 and W17 N2:

```python
            project_identity = secrets.token_hex(16) if kind == "project" else project.project
            local_identity = None if kind == "project" else secrets.token_hex(16)
            revision_identity = secrets.token_hex(16)
```

Project resolution has two separate, falsifiable guards:

```python
            if resolved_project is None:
                raise ProjectNotResolvable(f"{project}: project does not resolve")
            if isinstance(resolved_project, CoordinationRefused):
                raise ProjectNotResolvable(f"{project}: project is divergent", tips=resolved_project.tips)
```

Call the shared candidate builder with the exact genesis arity and retain the already-minted guard as separate anchors:

```python
            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())
            self._refuse_already_minted(candidate)
```

Call `coordination_revision(candidate)` as the shared shape validation, then `_refuse_already_minted`, `_refuse_rendering`, and `_corpus.add`. Do not call `_refuse`, because coordination is deliberately unstamped and has family-owned validation.

Extend `open_corpus` only by the optional keyword and pass it to `CorpusWriter`; do not construct a resolver there.

- [ ] **Step 5: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py && uv run --frozen ruff check src/beliefs/corpus.py src/beliefs/root.py tests/coordination_fixtures.py tests/test_coordination_write.py && uv run --frozen pyright src/beliefs/corpus.py src/beliefs/root.py tests/test_coordination_write.py`

Expected: PASS.

- [ ] **Step 6: Close the task and commit**

```bash
tasks done beliefs-b84a76 "Added profile-authorized project and subordinate genesis through one locked create."
git add python/src/beliefs/corpus.py python/src/beliefs/root.py python/tests/coordination_fixtures.py python/tests/test_coordination_write.py tasks
git commit -m "feat(coordination): mint coordination genesis"
```

### Task 7: Coordination Revision, Divergence, and Repair

**Files:**
- Modify: `python/src/beliefs/corpus.py`
- Modify: `python/tests/test_coordination_write.py`

**Interfaces:**
- Consumes: `CoordinationResolver.revision/tips`, `coordination_revision`, Task 6's complete content validator and candidate builder.
- Produces: `CorpusWriter.revise_coordination(kind: str, address: CoordinationAddress, *, predecessors: Sequence[str], content: Mapping[str, object]) -> Node` with continuity-before-standing, partial-supersession divergence, and all-tip repair.

- [ ] **Step 1: Write revision, continuity, divergence, and repair tests**

```python
def test_revision_is_a_new_whole_record_and_the_old_revision_remains_pinnable(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, resolver = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project", name="Old"))
    address = coordination_revision(project).address
    revised = writer.revise_coordination("project", address, predecessors=(project.uid,), content=content_for("project", name="New"))
    assert revised.uid != project.uid
    assert revised.relations[0].target == project.id
    assert resolver.resolve(address) == revised
    assert resolver.resolve(address.pinned(project.uid)) == project


def test_continuity_is_checked_before_standing(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project"))
    project_address = coordination_revision(project).address
    task = writer.mint_coordination("task", project=project_address, content=content_for("task"))
    with pytest.raises(PredecessorMismatch):
        writer.revise_coordination("project", project_address, predecessors=(task.uid,), content=content_for("project"))


def test_a_superseded_predecessor_refuses_at_commit(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    writer.revise_coordination("project", address, predecessors=(first.uid,), content=content_for("project", name="second"))
    with pytest.raises(PredecessorNotStanding):
        writer.revise_coordination("project", address, predecessors=(first.uid,), content=content_for("project", name="stale"))


def test_revision_requires_an_unpinned_address_and_distinct_nonempty_predecessors(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    for candidate, predecessors in ((address.pinned(first.uid), (first.uid,)), (address, ()), (address, (first.uid, first.uid))):
        with pytest.raises(ValidationRefused):
            writer.revise_coordination("project", candidate, predecessors=predecessors, content=content_for("project"))


def test_two_roots_diverge_and_one_all_tip_revision_repairs_without_deleting_siblings(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    left_writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=CoordinationResolver({left: profile}))
    project = left_writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(project).address
    raw_add(right, project.model_copy(deep=True))
    left_tip = left_writer.revise_coordination("project", address, predecessors=(project.uid,), content=content_for("project", name="left"))
    right_writer = CorpusWriter(right, DefaultExecutor, coordination_resolver=CoordinationResolver({right: profile}))
    right_tip = right_writer.revise_coordination("project", address, predecessors=(project.uid,), content=content_for("project", name="right"))
    resolver = CoordinationResolver({left: profile, right: profile})
    refused = resolver.resolve(address)
    assert refused == CoordinationRefused("divergent-view", (left_tip.uid, right_tip.uid))
    repair_writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    repair = repair_writer.revise_coordination("project", address, predecessors=(right_tip.uid, left_tip.uid), content=content_for("project", name="repaired"))
    assert resolver.resolve(address) == repair
    assert resolver.resolve(address.pinned(left_tip.uid)) == left_tip
    assert resolver.resolve(address.pinned(right_tip.uid)) == right_tip
    assert [relation.target for relation in repair.relations] == sorted((left_tip.id, right_tip.id))
    assert not any(finding.code == "supersession-target-missing" for finding in corpus_check(CorpusWriter(left, DefaultExecutor).read_view))
```

Add the lawful partial supersession check:

```python
def test_superseding_only_one_standing_sibling_is_lawful_and_remains_divergent(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    raw_add(right, second)
    resolver = CoordinationResolver({left: profile, right: profile})
    writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    successor = writer.revise_coordination("project", CoordinationAddress(A), predecessors=(first.uid,), content=content_for("project", name="partial"))
    assert resolver.resolve(CoordinationAddress(A)) == CoordinationRefused("divergent-view", (second.uid, successor.uid))
```

Add the divergent-project check using the same raw sibling construction:

```python
def test_a_subordinate_revision_refuses_while_its_project_is_divergent(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    raw_add(right, second)
    resolver = CoordinationResolver({left: profile, right: profile})
    writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=CoordinationAddress(A), content=content_for("task"))
    assert caught.value.tips == (C, D)
```

- [ ] **Step 2: Verify the revision method is absent**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py`

Expected: FAIL on missing `revise_coordination`.

- [ ] **Step 3: Implement continuity before standing**

Require an unpinned address, a non-empty duplicate-free sequence of 32-lower-hex revision ids, and validate content before looking up predecessors. For every supplied uid call `resolver.revision(uid)` independent of the candidate address; absence raises `PredecessorNotStanding`. Decode each found node, then pin this continuity guard:

```python
            if predecessor.node.kind != kind or predecessor.address != address:
                raise PredecessorMismatch(f"revision {predecessor.node.uid} belongs to {predecessor.node.kind} {predecessor.address}, not {kind} {address}")
```

Only after every predecessor passes continuity, recompute `standing = resolver.tips(address)` under the destination lock and pin the at-commit guard:

```python
            if predecessor_ids - {revision.node.uid for revision in standing}:
                raise PredecessorNotStanding("every supplied predecessor must be a standing tip at commit")
```

Resolve the owning project for subordinate records; project revisions skip that lookup so divergent project tips can be repaired. Generate one fresh revision uid, build one new node at the same project/local address, sort predecessor nodes by `Node.id`, and store one `supersedes` relation per predecessor. Validate through the shared decoder, already-minted guard, rendering, and one create. Pin the fresh-revision line for W17's whole-revision unit:

```python
            new_revision_identity = secrets.token_hex(16)
```

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py && uv run --frozen ruff check src/beliefs/corpus.py tests/test_coordination_write.py && uv run --frozen pyright src/beliefs/corpus.py tests/test_coordination_write.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-fb5c38 "Added continuity-first coordination revision, sibling divergence, and all-tip repair."
git add python/src/beliefs/corpus.py python/tests/test_coordination_write.py tasks
git commit -m "feat(coordination): revise and repair tips"
```

### Task 8: Close Wrong Family Doors and Retire Unscoped Note Fixtures

**Files:**
- Modify: `python/src/beliefs/corpus.py`
- Modify: `python/tests/test_coordination_write.py`
- Modify: `python/tests/acceptance/durable_fixture.py`
- Modify: `python/tests/acceptance/test_durable_traversal.py`
- Modify: `python/tests/test_arrival_modes.py`
- Modify: `python/tests/test_corpus_write.py`
- Modify: `python/tests/test_fork_acts.py`
- Modify: `python/tests/test_import_bundle.py`
- Modify: `python/tests/test_local_standing.py`
- Modify: `python/tests/test_read_side.py`
- Modify: `python/tests/test_survey_instrument.py`

**Interfaces:**
- Consumes: `COORDINATION_KINDS`, the destination profile's coordination kinds, existing family methods, and `ImportRefused(member=...)`.
- Produces: wrong-door `CoordinationKindUnsupported` across `add`, `revise`, `supersede`, `retract`, and the coordination door; import member refusal; no ordinary unscoped `note` outside the byte-frozen cut-5 surface.

- [ ] **Step 1: Write the wrong-door and import tests**

```python
@pytest.mark.parametrize("door", ["add", "revise", "supersede", "retract"])
def test_every_ordinary_family_door_refuses_coordination_kinds(tmp_path, door):
    writer = CorpusWriter(tmp_path, DefaultExecutor)
    node = Node(id="note:old", kind="note", title="old")
    with pytest.raises(CoordinationKindUnsupported):
        if door == "add": writer.add(node)
        elif door == "revise": writer.revise(node)
        elif door == "supersede": writer.supersede(node, of="note:old")
        else: writer.retract(node)


# append to python/tests/test_import_bundle.py, where writer_with_port is defined
def test_import_refuses_a_coordination_member_by_name(writer_with_port):
    member = Node(id="note:old", kind="note", title="old")
    with pytest.raises(ImportRefused) as caught:
        writer_with_port.import_bundle([member], actor="a", observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert caught.value.member == member.id


@pytest.mark.parametrize("kind", stored.WORLD_KINDS)
def test_the_coordination_door_refuses_every_world_kind(tmp_path, base_contract, kind):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    with pytest.raises(CoordinationKindUnsupported):
        writer.mint_coordination(kind, content=content_for("project"))
```

Add the pre-plan guard with the portable recorder:

```python
def test_w17e_an_already_minted_revision_pair_refuses_before_plan(tmp_path, base_contract, monkeypatch):
    profile = coordination_profile(base_contract)
    mounted_root(tmp_path, profile, Recorder)
    resolver = CoordinationResolver({tmp_path: profile})
    Recorder.plans = []
    writer = CorpusWriter(tmp_path, Recorder, coordination_resolver=resolver)
    values = iter(("a" * 32, "b" * 32, "a" * 32, "b" * 32))
    monkeypatch.setattr("beliefs.corpus.secrets.token_hex", lambda _: next(values))
    writer.mint_coordination("project", content=content_for("project"))
    assert len(Recorder.plans) == 1
    with pytest.raises(RecordAlreadyMinted):
        writer.mint_coordination("project", content=content_for("project"))
    assert len(Recorder.plans) == 1
```

- [ ] **Step 2: Verify the tests fail on the still-open doors**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py tests/test_import_bundle.py tests/test_read_side.py`

Expected: FAIL because ordinary `note` and coordination import are still admitted.

- [ ] **Step 3: Close the existing doors at their shared boundaries**

Extend `_refuse_family_kinds` to reject the fixed eight coordination kinds everywhere, even when no resolver is configured. When a resolver is configured, use its tolerant `profile(root)` lookup and reject additionally declared kinds only when that destination is mounted; an ordinary write never requires coordination configuration. Call the guard first from `revise`, `supersede`, and `retract`, so their narrower errors cannot mask the family error. At the coordination methods, reject `kind in stored.WORLD_KINDS` before profile lookup.

Pin the shared ordinary-door guard:

```python
        if node.kind in COORDINATION_KINDS:
            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")
        profile = self._coordination_resolver.profile(self._corpus.store.root) if self._coordination_resolver is not None else None
        if profile is not None and node.kind in profile.coordination_kinds:
            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")
```

At the top of `_validate_import_bundle`'s member loop, pin:

```python
            if record.kind in COORDINATION_KINDS:
                raise ImportRefused(f"{record.id}: coordination records are replicated with their corpus, never imported", member=record.id)
```

Do not special-case `act-report`; its existing import behavior remains.

- [ ] **Step 4: Move only non-frozen generic fixtures from `note` to `memo`**

Apply a mechanical record-kind/id rename `note` → `memo` in the files listed above. Do not change YAML keys such as `note: extra` that test closed document shapes. Do not edit either frozen cut-5 file:

```text
python/tests/n2_arms_cut5.py
python/tests/acceptance/test_n2_cut5.py
```

After the rename, assert the remaining stored `note` uses are only the frozen cut-5 evidence plus new coordination tests:

Run: `rg -n 'kind="note"|kind='"'"'note'"'"'|note:' python/tests | sort`

Expected: matches in the two frozen cut-5 files, coordination fixtures/tests, and YAML unknown-key strings only.

- [ ] **Step 5: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_coordination_write.py tests/test_import_bundle.py tests/test_read_side.py tests/test_arrival_modes.py tests/test_fork_acts.py tests/test_local_standing.py tests/test_corpus_write.py tests/acceptance/test_durable_traversal.py && uv run --frozen ruff check src/beliefs/corpus.py tests && uv run --frozen pyright src/beliefs/corpus.py tests/test_coordination_write.py tests/test_import_bundle.py`

Expected: PASS. Do not run cut 5 on the new tree; Task 11 pins and cites its unchanged files.

- [ ] **Step 6: Close the task and commit**

```bash
tasks done beliefs-17bc0e "Closed every wrong family door, named coordination imports, and retired non-frozen unscoped-note fixtures."
git add python/src/beliefs/corpus.py python/tests tasks
git commit -m "feat(coordination): close coordination family doors"
```

### Task 9: Exclude Coordination from World and Belief Inputs

**Files:**
- Modify: `python/src/beliefs/world/epoch.py`
- Modify: `python/tests/test_world_epoch.py`
- Modify: `python/tests/test_consulted.py`
- Modify: `python/tests/test_belief.py`

**Interfaces:**
- Consumes: `stored.WORLD_KINDS`, existing complete corpus-state enumeration, `consulted_contracts`' operator-driven walk.
- Produces: `_captured_records` that retains coordination bytes in corpus-state identity but creates `CapturedRecord` only for world kinds; regression proof that an activated coordination pin is never consulted.

- [ ] **Step 1: Write the capture-boundary and consulted-set tests**

```python
# append to python/tests/test_world_epoch.py
from nodes.core.corpus import Corpus
from beliefs.corpus import CoordinationResolver, CorpusWriter
from coordination_fixtures import content_for, coordination_profile, mounted_root


def test_coordination_bytes_move_corpus_state_but_never_become_captured_world_records(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    writer = CorpusWriter(root, DefaultExecutor, coordination_resolver=CoordinationResolver({root: profile}))
    before = registry.corpus_state_identity(root)
    project = writer.mint_coordination("project", content=content_for("project"))
    after = registry.corpus_state_identity(root)
    assert after != before
    assert project.id not in {record.address for record in epoch._captured_records(root)}


def test_world_records_are_still_captured_beside_coordination_records(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    Corpus(root).add(stored.dataset_node("world", title="world", resources=[{"name": "x", "digest": "sha256:" + "a" * 64}]))
    writer = CorpusWriter(root, DefaultExecutor, coordination_resolver=CoordinationResolver({root: profile}))
    writer.mint_coordination("project", content=content_for("project"))
    assert {record.address for record in epoch._captured_records(root)} == {"dataset:world"}
```

```python
# append to python/tests/test_consulted.py
def test_an_activated_coordination_contract_is_never_a_belief_input(profile):
    ordinary = pins()
    with_coordination = CorpusPins(
        science_contract=ordinary.science_contract,
        domains={**ordinary.domains, "coordination": "coordination:" + "c" * 64},
    )
    without = consulted_contracts(claims={}, profile=profile, node_corpus={}, pins={"c1": ordinary}, closure_nodes=())
    with_pin = consulted_contracts(claims={}, profile=profile, node_corpus={}, pins={"c1": with_coordination}, closure_nodes=())
    assert with_pin == without
    assert "coordination" not in dict(with_pin)
```

Use the existing `profile` fixture and `pins` helper; add no second scenario builder.

Add the value-level consequence in `test_belief.py` using its existing `scenario()` helper:

```python
def test_w18j_a_coordination_pin_never_enters_the_belief_input_digest():
    ordinary = scenario()
    first = evaluate(**ordinary)
    pin = ordinary["context"].pins["c1"]
    with_coordination = {
        "c1": CorpusPins(
            science_contract=pin.science_contract,
            domains={**pin.domains, "coordination": "coordination:" + "c" * 64},
        )
    }
    second = evaluate(**scenario(context=replace(ordinary["context"], pins=with_coordination)))
    assert isinstance(first, Belief) and isinstance(second, Belief)
    assert second.belief_input_digest == first.belief_input_digest
```

- [ ] **Step 2: Verify coordination is currently captured**

Run: `cd python && uv run --frozen pytest tests/test_world_epoch.py::test_coordination_bytes_move_corpus_state_but_never_become_captured_world_records tests/test_world_epoch.py::test_world_records_are_still_captured_beside_coordination_records tests/test_consulted.py::test_an_activated_coordination_contract_is_never_a_belief_input tests/test_belief.py::test_w18j_a_coordination_pin_never_enters_the_belief_input_digest`

Expected: the first two tests FAIL because `_captured_records` includes every node; the consulted-set test already passes and becomes the regression pin.

- [ ] **Step 3: Filter only the constructed world values**

Keep the initial `nodes = tuple(view.iter_stored())`, governance pass, retraction-facet pass, and standing computation unchanged. Change only the final comprehension in `_captured_records`:

```python
        for node in nodes
        if node.kind in stored.WORLD_KINDS
```

This placement is essential: the corpus state and governance checks still see every stored node. Do not add coordination to `SEMANTIC_DOMAINS`, `ENUMERATED_SOURCE_KINDS`, or any derive module.

- [ ] **Step 4: Run the focused checks**

Run: `cd python && uv run --frozen pytest tests/test_world_epoch.py::test_coordination_bytes_move_corpus_state_but_never_become_captured_world_records tests/test_world_epoch.py::test_world_records_are_still_captured_beside_coordination_records tests/test_consulted.py tests/test_belief.py::test_w18j_a_coordination_pin_never_enters_the_belief_input_digest && uv run --frozen ruff check src/beliefs/world/epoch.py tests/test_world_epoch.py tests/test_consulted.py tests/test_belief.py && uv run --frozen pyright src/beliefs/world/epoch.py tests/test_world_epoch.py tests/test_consulted.py tests/test_belief.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-42a702 "Kept coordination in corpus identity while excluding it from world capture and consulted contracts."
git add python/src/beliefs/world/epoch.py python/tests/test_world_epoch.py python/tests/test_consulted.py python/tests/test_belief.py tasks
git commit -m "feat(coordination): exclude coordination from world inputs"
```

### Task 10: Durable Cut-14 Acceptance Surface

**Files:**
- Create: `python/tests/acceptance/test_coordination_acceptance.py`
- Modify: `python/tests/acceptance/conftest.py`

**Interfaces:**
- Consumes: the complete Tasks 1–9 public surface, certified `work_directory`, root lifecycle functions, shipped world derivation bindings, and `belief.evaluate` fixtures.
- Produces: the exact durable check nodes referenced by Task 11 for every executable W11, W12, W13, W17, and W18 unit; W18's earlier-version authorization check remains portable beside the writer.

- [ ] **Step 1: Add a two-root certified coordination fixture**

Append to `acceptance/conftest.py`:

```python
@pytest.fixture()
def durable_coordination_roots(work_directory, base_contract):
    from coordination_fixtures import coordination_profile, pins_for

    profile = coordination_profile(base_contract)
    roots = tuple(work_directory / f"coordination-{os.getpid()}-{next(_counter)}-{side}" for side in ("left", "right"))
    try:
        for root in roots:
            init_corpus_root(root)
            open_corpus(root).adopt_manifest(profile=pins_for(profile))
        yield roots, profile
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


@pytest.fixture()
def durable_coordination_world(work_directory, durable_coordination_roots):
    (corpus_root, _), profile = durable_coordination_roots
    world_root = work_directory / f"coordination-world-{os.getpid()}-{next(_counter)}"
    config = WorldConfig(world_root, "e" * 32, (corpus_root,))
    try:
        init_world_root(config)
        world = open_world(config)
        world.admit(corpus_root, provenance=Fresh(), actor="cut14")
        yield world, corpus_root, profile
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(world_root), ignore_errors=True)
```

This uses the existing certified-volume gate; it does not add another probe.

- [ ] **Step 2: Write W11, W12, W13, and the family-door checks**

Create `test_coordination_acceptance.py` with imports from `coordination_fixtures` and these exact tests:

```python
from dataclasses import replace

import pytest
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation

from coordination_fixtures import AT, content_for, raw_add, raw_coordination_node
from test_belief import scenario as belief_scenario
from test_n2_cut7 import shipped_bindings
from beliefs import stored
from beliefs.belief import Belief, evaluate
from beliefs.consulted import CorpusPins
from beliefs.coordination import CoordinationAddress, CoordinationRefused, coordination_revision
from beliefs.corpus import CoordinationResolver, ReadView, corpus_check
from beliefs.errors import CoordinationKindUnsupported, ImportRefused, PredecessorMismatch, PredecessorNotStanding, ProjectNotResolvable, RecordAlreadyMinted, ValidationRefused
from beliefs.root import open_corpus
from beliefs.view_query import parse_view_query
from beliefs.world import derive, epoch, load_manifest
```

Then add:

```python
def writers(case):
    roots, profile = case
    resolver = CoordinationResolver(dict.fromkeys(roots, profile))
    return roots, resolver, tuple(open_corpus(root, coordination_resolver=resolver) for root in roots)


def test_w11a_view_queries_reject_coordination_addresses():
    with pytest.raises(ValueError, match="world-tier"):
        parse_view_query({"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": ["coord:" + "a" * 32]}]}]})


def test_w11b_coordination_fields_reject_world_addresses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused):
        writer.mint_coordination("task", project=coordination_revision(project).address, content=content_for("task", depends=["dataset:x"]))


def test_w12_renaming_a_project_preserves_every_subordinate_address(durable_coordination_roots, monkeypatch):
    _roots, resolver, (writer, _other) = writers(durable_coordination_roots)
    values = iter(("a" * 32, "b" * 32, "c" * 32, "d" * 32, "e" * 32))
    monkeypatch.setattr("beliefs.corpus.secrets.token_hex", lambda _: next(values))
    project = writer.mint_coordination("project", content=content_for("project", name="a" * 32))
    project_address = coordination_revision(project).address
    task = writer.mint_coordination("task", project=project_address, content=content_for("task"))
    renamed = writer.revise_coordination("project", project_address, predecessors=(project.uid,), content=content_for("project", name="different"))
    assert resolver.resolve(project_address) == renamed
    assert resolver.resolve(coordination_revision(task).address) == task
    assert coordination_revision(task).address.project == project_address.project


def test_w13_project_identity_is_independent_of_corpus_identity_and_mount(durable_coordination_roots):
    (left, right), profile = durable_coordination_roots
    left_resolver = CoordinationResolver({left: profile})
    writer = open_corpus(left, coordination_resolver=left_resolver)
    first = writer.mint_coordination("project", content=content_for("project", name="one"))
    second = writer.mint_coordination("project", content=content_for("project", name="two"))
    left_manifest = load_manifest(left)
    right_manifest = load_manifest(right)
    assert coordination_revision(first).address.project != coordination_revision(second).address.project
    assert left_manifest.corpus_id == load_manifest(left).corpus_id
    Corpus(right).add(first.model_copy(deep=True))
    assert CoordinationResolver({right: profile}).resolve(coordination_revision(first).address) == first
    assert load_manifest(left).corpus_id == left_manifest.corpus_id
    assert load_manifest(right).corpus_id == right_manifest.corpus_id


def test_w17a_genesis_names_zero_predecessors(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    assert coordination_revision(project).predecessors == ()


def test_w17n_every_edit_is_a_new_whole_revision(durable_coordination_roots):
    _roots, resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project", name="old"))
    address = coordination_revision(project).address
    revised = writer.revise_coordination("project", address, predecessors=(project.uid,), content=content_for("project", name="new"))
    assert revised.uid != project.uid
    assert revised.relations[0].target == project.id
    assert resolver.resolve(address) == revised
    assert resolver.resolve(address.pinned(project.uid)) == project


def test_w17b_every_ordinary_door_refuses_coordination(durable_coordination_roots):
    (root, _), _profile = durable_coordination_roots
    writer = open_corpus(root)
    node = Node(id="note:old", kind="note", title="old")
    for call in (lambda: writer.add(node), lambda: writer.revise(node), lambda: writer.supersede(node, of=node.id), lambda: writer.retract(node)):
        with pytest.raises(CoordinationKindUnsupported):
            call()


def test_w17c_import_refuses_and_names_the_coordination_member(durable_coordination_roots):
    (root, _), _profile = durable_coordination_roots
    writer = open_corpus(root)
    member = Node(id="note:old", kind="note", title="old")
    with pytest.raises(ImportRefused) as caught:
        writer.import_bundle([member], actor="a", observer="o", instrument="i", opened_at=AT, closed_at=AT)
    assert caught.value.member == member.id


def test_w17d_coordination_door_refuses_world_kinds(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    for kind in stored.WORLD_KINDS:
        with pytest.raises(CoordinationKindUnsupported):
            writer.mint_coordination(kind, content=content_for("project"))
```

- [ ] **Step 3: Write the remaining W17 state-machine checks**

Use the two roots and the exact operations from Task 7. The tests and terminal assertions are:

```python
def test_w17e_reusing_an_existing_revision_pair_refuses_before_a_plan(durable_coordination_roots, monkeypatch):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    values = iter(("a" * 32, "b" * 32, "a" * 32, "b" * 32))
    monkeypatch.setattr("beliefs.corpus.secrets.token_hex", lambda _: next(values))
    writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(RecordAlreadyMinted):
        writer.mint_coordination("project", content=content_for("project"))


def test_w17f_a_superseded_predecessor_refuses_at_commit(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    writer.revise_coordination("project", address, predecessors=(first.uid,), content=content_for("project", name="next"))
    with pytest.raises(PredecessorNotStanding):
        writer.revise_coordination("project", address, predecessors=(first.uid,), content=content_for("project", name="stale"))


def test_w17g_continuity_refuses_a_standing_predecessor_of_another_address_or_kind(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    other = writer.mint_coordination("project", content=content_for("project", name="other"))
    task = writer.mint_coordination("task", project=coordination_revision(project).address, content=content_for("task"))
    for predecessor in (other.uid, task.uid):
        with pytest.raises(PredecessorMismatch):
            writer.revise_coordination("project", coordination_revision(project).address, predecessors=(predecessor,), content=content_for("project"))


def divergent(case):
    (left, right), profile = case
    left_writer = open_corpus(left, coordination_resolver=CoordinationResolver({left: profile}))
    genesis = left_writer.mint_coordination("project", content=content_for("project"))
    Corpus(right).add(genesis.model_copy(deep=True))
    address = coordination_revision(genesis).address
    left_tip = left_writer.revise_coordination("project", address, predecessors=(genesis.uid,), content=content_for("project", name="left"))
    right_writer = open_corpus(right, coordination_resolver=CoordinationResolver({right: profile}))
    right_tip = right_writer.revise_coordination("project", address, predecessors=(genesis.uid,), content=content_for("project", name="right"))
    resolver = CoordinationResolver({left: profile, right: profile})
    repair_writer = open_corpus(left, coordination_resolver=resolver)
    return address, resolver, repair_writer, left_tip, right_tip


def test_w17h_siblings_refuse_with_sorted_tips_independent_of_mount_order(durable_coordination_roots):
    address, resolver, _writer, left_tip, right_tip = divergent(durable_coordination_roots)
    expected = CoordinationRefused("divergent-view", (left_tip.uid, right_tip.uid))
    assert resolver.resolve(address) == expected
    roots, profile = durable_coordination_roots
    assert CoordinationResolver({roots[1]: profile, roots[0]: profile}).resolve(address) == expected


def test_w17i_all_tip_repair_restores_resolution_and_retains_siblings(durable_coordination_roots):
    address, resolver, writer, left_tip, right_tip = divergent(durable_coordination_roots)
    repair = writer.revise_coordination("project", address, predecessors=(right_tip.uid, left_tip.uid), content=content_for("project", name="repair"))
    assert resolver.resolve(address) == repair
    assert resolver.resolve(address.pinned(left_tip.uid)) == left_tip
    assert resolver.resolve(address.pinned(right_tip.uid)) == right_tip


def test_w17j_a_raw_cycle_has_no_tip_and_an_audit_finding(durable_coordination_roots):
    # Construct the two-node cycle with raw_coordination_node/raw_add exactly as Task 5.
    root, profile = durable_coordination_roots[0][0], durable_coordination_roots[1]
    first = raw_coordination_node("project", "a" * 32, "b" * 32)
    second = raw_coordination_node("project", "a" * 32, "c" * 32)
    first.relations = [Relation(source=first.id, predicate=stored.SUPERSEDES, target=second.id)]
    second.relations = [Relation(source=second.id, predicate=stored.SUPERSEDES, target=first.id)]
    raw_add(root, first, second)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress("a" * 32)) is None
    assert any(finding.code == "coordination-supersession-cycle" for finding in corpus_check(open_corpus(root).read_view))


def test_w17k_a_malformed_facet_is_reported_and_excluded(durable_coordination_roots):
    root, profile = durable_coordination_roots[0][0], durable_coordination_roots[1]
    valid = raw_coordination_node("project", "a" * 32, "b" * 32)
    malformed = raw_coordination_node("project", "a" * 32, "c" * 32)
    malformed.facets[stored.COORDINATION_FACET]["project"] = "bad"
    raw_add(root, valid, malformed)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress("a" * 32)) == valid
    assert any(finding.code == "coordination-facet-malformed" and finding.ref == malformed.id for finding in corpus_check(open_corpus(root).read_view))


def test_w17l_a_subordinate_under_a_missing_project_refuses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=CoordinationAddress("a" * 32), content=content_for("task"))
    assert caught.value.tips == ()


def test_w17m_a_subordinate_under_a_divergent_project_names_the_project_tips(durable_coordination_roots):
    address, _resolver, writer, left_tip, right_tip = divergent(durable_coordination_roots)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=address, content=content_for("task"))
    assert caught.value.tips == tuple(sorted((left_tip.uid, right_tip.uid)))
```

The comments in the cycle test are descriptive, not omitted code: the complete five construction lines are shown directly below them.

- [ ] **Step 4: Write W18 authorization, query, and world-exclusion checks**

```python
def test_w18a_an_undeclared_kind_mints_nothing(durable_coordination_roots):
    _roots, resolver, (writer, _other) = writers(durable_coordination_roots)
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination("publication", project=coordination_revision(project).address, content=content_for("decision"))
    assert all(node.kind != "publication" for root in durable_coordination_roots[0] for node in ReadView.opened_at(root).iter_stored())


def test_w18b_malformed_query_refuses(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    with pytest.raises(ValidationRefused):
        writer.mint_coordination("project", content=content_for("project", query={"version": "science.view-query.v1", "clauses": [{"all": []}]}))


def test_w18e_an_unresolved_anchor_is_accepted(durable_coordination_roots):
    _roots, _resolver, (writer, _other) = writers(durable_coordination_roots)
    accepted = writer.mint_coordination("project", content=content_for("project", query={"version": "science.view-query.v1", "clauses": [{"all": [{"addresses": ["dataset:not-held"]}]}]}))
    assert accepted.kind == "project"


def test_w18i_coordination_moves_epoch_identity_not_world_maps_or_belief_input(durable_coordination_world):
    world, corpus_root, profile = durable_coordination_world
    bindings = shipped_bindings(world)
    corpus_id = load_manifest(corpus_root).corpus_id
    before = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
    resolver = CoordinationResolver({corpus_root: profile})
    open_corpus(corpus_root, coordination_resolver=resolver).mint_coordination("project", content=content_for("project"))
    after = epoch.build_epoch(world, coverage=frozenset({corpus_id}), bindings=bindings)
    assert before.packaging_identity != after.packaging_identity
    for member in ("address-map.yaml", "producers-map.yaml", "retraction-discovery-map.yaml", "coreference-map.yaml", "producer-snapshot.yaml"):
        assert before.members[member] == after.members[member]
    assert before.documents["certification-receipt.yaml"]["inventory"] == after.documents["certification-receipt.yaml"]["inventory"]
    before_snapshot = derive.producer_snapshot(before.documents["producer-snapshot.yaml"]).identity()
    after_snapshot = derive.producer_snapshot(after.documents["producer-snapshot.yaml"]).identity()
    assert before_snapshot == after_snapshot
    ordinary = belief_scenario()
    pin = ordinary["context"].pins["c1"]
    pinned = {"c1": CorpusPins(pin.science_contract, {**pin.domains, "coordination": "coordination:" + profile.activated_contracts["coordination"]})}
    first = evaluate(**{**ordinary, "context": replace(ordinary["context"], producer_snapshot_identity=before_snapshot, pins=pinned)})
    second = evaluate(**{**ordinary, "context": replace(ordinary["context"], producer_snapshot_identity=after_snapshot, pins=pinned)})
    assert isinstance(first, Belief) and isinstance(second, Belief)
    assert first.belief_input_digest == second.belief_input_digest
```

The W18 contract/compiler checks remain portable and are the exact Task 4 test nodes: undeclared kernel vocabulary, editorial identity stability, schema identity movement, and reserved domain namespace.

- [ ] **Step 5: Run the new durable module once**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_coordination_acceptance.py`

Expected: PASS on the certified volume, never skip. If the engine refuses the tuple, report that exact refusal and do not mark this task done.

- [ ] **Step 6: Run focused static checks**

Run: `cd python && uv run --frozen ruff check tests/acceptance/test_coordination_acceptance.py tests/acceptance/conftest.py && uv run --frozen pyright tests/acceptance/test_coordination_acceptance.py tests/acceptance/conftest.py`

Expected: PASS.

- [ ] **Step 7: Close the task and commit**

```bash
tasks done beliefs-bdacf1 "Added certified durable coverage for every executable cut-14 guarantee unit."
git add python/tests/acceptance/conftest.py python/tests/acceptance/test_coordination_acceptance.py tasks
git commit -m "test(coordination): add cut 14 durable acceptance"
```

### Task 11: Declare and Audit Cut-14 N2 Arms

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut14.py`
- Create: `python/tests/acceptance/test_n2_cut14.py`

**Interfaces:**
- Consumes: the exact implementation anchors pinned in Tasks 2 and 4–9; `Arm`, `Sabotage`, `audit`, and `baseline`; all prior cut arm tables through cut 13.
- Produces: 29 selected units and 29 one-mutation lettered arms: W11 2, W12 1, W13 1, W17 14, W18 11. `LABELED_UNITS` is empty and `CO_CITED` is empty. There is no intent-position unit; W17n carries the frozen row's distinct whole-revision clause.

- [ ] **Step 1: Write the complete declaration module**

```python
# python/tests/acceptance/n2_arms_cut14.py
"""Cut 14: 29 selected units, 29 lettered arms; no labeled or intent-position unit."""

from n2_arms import Arm, Sabotage

_COORDINATION = "coordination.py"
_QUERY = "view_query.py"
_CORPUS = "corpus.py"
_PROFILE = "profile.py"
_DOMAIN = "contract/domain.py"
_EPOCH = "world/epoch.py"
_ACCEPT = "acceptance/test_coordination_acceptance.py"

_UNIT_OF_LETTERED = {
    "W11a": "W11u1", "W11b": "W11u2", "W12a": "W12u1", "W13a": "W13u1",
    **{f"W17{letter}": f"W17u{number}" for number, letter in enumerate("abcdefghijklmn", 1)},
    **{f"W18{letter}": f"W18u{number}" for number, letter in enumerate("abcdefghijk", 1)},
}


def unit_of(row: str) -> str:
    return _UNIT_OF_LETTERED[row]


ROW_UNITS = {"W11": 2, "W12": 1, "W13": 1, "W17": 14, "W18": 11}
LABELED_UNITS: tuple[str, ...] = ()
CO_CITED: dict[str, tuple[str, ...]] = {}

CUT14_ARMS = (
    Arm("W11a", "view queries reject coordination addresses by tier before lookup",
        Sabotage(_QUERY,
            before='    if separator != ":" or kind not in stored.WORLD_KINDS or not local or value.startswith("coord:"):\n        raise ValueError(f"view query {where} must be a world-tier address")',
            after='    if False:\n        raise ValueError(f"view query {where} must be a world-tier address")'),
        (f"{_ACCEPT}::test_w11a_view_queries_reject_coordination_addresses",)),
    Arm("W11b", "coordination reference fields reject world addresses before lookup",
        Sabotage(_CORPUS, before='        CoordinationAddress.parse(value)', after='        pass'),
        (f"{_ACCEPT}::test_w11b_coordination_fields_reject_world_addresses",)),
    Arm("W12a", "project rename leaves project identity and subordinate resolution unchanged",
        Sabotage(_CORPUS,
            before='        revisions = tuple(revision for revision in self._revisions() if revision.address == address.unpinned())',
            after='        revisions = tuple(revision for revision in self._revisions() if revision.address == address.unpinned() and revision.node.title == address.project)'),
        (f"{_ACCEPT}::test_w12_renaming_a_project_preserves_every_subordinate_address",)),
    Arm("W13a", "project identity is independent of corpus identity and mount",
        Sabotage(_CORPUS,
            before='            project_identity = secrets.token_hex(16) if kind == "project" else project.project',
            after='            project_identity = __import__("beliefs.world", fromlist=["load_manifest"]).load_manifest(self._corpus.store.root).corpus_id if kind == "project" else project.project'),
        (f"{_ACCEPT}::test_w13_project_identity_is_independent_of_corpus_identity_and_mount",)),
    Arm("W17a", "genesis names zero predecessors",
        Sabotage(_CORPUS,
            before='            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())',
            after='            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=("project:" + "0" * 32 + "." + "0" * 32,))'),
        (f"{_ACCEPT}::test_w17a_genesis_names_zero_predecessors",)),
    Arm("W17b", "ordinary family doors refuse coordination kinds including note",
        Sabotage(_CORPUS,
            before='        if node.kind in COORDINATION_KINDS:\n            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")',
            after='        if False:\n            raise CoordinationKindUnsupported(f"{node.kind!r} enters through the coordination family door")'),
        (f"{_ACCEPT}::test_w17b_every_ordinary_door_refuses_coordination",)),
    Arm("W17c", "import refuses a coordination member and names it",
        Sabotage(_CORPUS,
            before='            if record.kind in COORDINATION_KINDS:\n                raise ImportRefused(f"{record.id}: coordination records are replicated with their corpus, never imported", member=record.id)',
            after='            if False:\n                raise ImportRefused(f"{record.id}: coordination records are replicated with their corpus, never imported", member=record.id)'),
        (f"{_ACCEPT}::test_w17c_import_refuses_and_names_the_coordination_member",)),
    Arm("W17d", "the coordination door refuses every world kind",
        Sabotage(_CORPUS,
            before='        if kind in stored.WORLD_KINDS:\n            raise CoordinationKindUnsupported(f"{kind!r} is a world kind, not a coordination kind")',
            after='        if False:\n            raise CoordinationKindUnsupported(f"{kind!r} is a world kind, not a coordination kind")'),
        (f"{_ACCEPT}::test_w17d_coordination_door_refuses_world_kinds",)),
    Arm("W17e", "an already-minted revision pair refuses before planning",
        Sabotage(_CORPUS,
            before='            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())\n            self._refuse_already_minted(candidate)',
            after='            candidate = self._coordination_node(kind, address, revision_identity, validated, predecessors=())'),
        ("test_coordination_write.py::test_w17e_an_already_minted_revision_pair_refuses_before_plan",)),
    Arm("W17f", "every supplied predecessor stands at commit",
        Sabotage(_CORPUS,
            before='            if predecessor_ids - {revision.node.uid for revision in standing}:\n                raise PredecessorNotStanding("every supplied predecessor must be a standing tip at commit")',
            after='            if False:\n                raise PredecessorNotStanding("every supplied predecessor must be a standing tip at commit")'),
        (f"{_ACCEPT}::test_w17f_a_superseded_predecessor_refuses_at_commit",)),
    Arm("W17g", "kind and address continuity are checked before standing",
        Sabotage(_CORPUS,
            before='            if predecessor.node.kind != kind or predecessor.address != address:\n                raise PredecessorMismatch(f"revision {predecessor.node.uid} belongs to {predecessor.node.kind} {predecessor.address}, not {kind} {address}")',
            after='            if False:\n                raise PredecessorMismatch(f"revision {predecessor.node.uid} belongs to {predecessor.node.kind} {predecessor.address}, not {kind} {address}")'),
        (f"{_ACCEPT}::test_w17g_continuity_refuses_a_standing_predecessor_of_another_address_or_kind",)),
    Arm("W17h", "siblings refuse with sorted tips independent of mount order",
        Sabotage(_CORPUS,
            before='        if len(tips) > 1:\n            return CoordinationRefused("divergent-view", tuple(revision.node.uid for revision in tips))',
            after='        if False:\n            return CoordinationRefused("divergent-view", tuple(revision.node.uid for revision in tips))'),
        (f"{_ACCEPT}::test_w17h_siblings_refuse_with_sorted_tips_independent_of_mount_order",)),
    Arm("W17i", "one revision over every tip repairs divergence and retains siblings",
        Sabotage(_COORDINATION,
            before='        for predecessor in revision.predecessors',
            after='        for predecessor in revision.predecessors[:1]'),
        (f"{_ACCEPT}::test_w17i_all_tip_repair_restores_resolution_and_retains_siblings",)),
    Arm("W17j", "a raw supersession cycle has zero tips and an audit finding",
        Sabotage(_CORPUS,
            before='        if revisions and not standing_tips(revisions):',
            after='        if False:'),
        (f"{_ACCEPT}::test_w17j_a_raw_cycle_has_no_tip_and_an_audit_finding",)),
    Arm("W17k", "a malformed coordination facet is reported and excluded from tips",
        Sabotage(_CORPUS,
            before='                if coordination_facet_malformed(node):\n                    continue',
            after='                if False:\n                    continue'),
        (f"{_ACCEPT}::test_w17k_a_malformed_facet_is_reported_and_excluded",)),
    Arm("W17l", "a subordinate under a missing project refuses",
        Sabotage(_CORPUS,
            before='            if resolved_project is None:\n                raise ProjectNotResolvable(f"{project}: project does not resolve")',
            after='            if False:\n                raise ProjectNotResolvable(f"{project}: project does not resolve")'),
        (f"{_ACCEPT}::test_w17l_a_subordinate_under_a_missing_project_refuses",)),
    Arm("W17m", "a subordinate under a divergent project names every project tip",
        Sabotage(_CORPUS,
            before='            if isinstance(resolved_project, CoordinationRefused):\n                raise ProjectNotResolvable(f"{project}: project is divergent", tips=resolved_project.tips)',
            after='            if False:\n                raise ProjectNotResolvable(f"{project}: project is divergent", tips=resolved_project.tips)'),
        (f"{_ACCEPT}::test_w17m_a_subordinate_under_a_divergent_project_names_the_project_tips",)),
    Arm("W17n", "every edit is a new whole revision and retains the predecessor",
        Sabotage(_CORPUS,
            before='            new_revision_identity = secrets.token_hex(16)',
            after='            new_revision_identity = next(iter(predecessor_ids))'),
        (f"{_ACCEPT}::test_w17n_every_edit_is_a_new_whole_revision",)),
    Arm("W18a", "an undeclared coordination kind authorizes no mint",
        Sabotage(_CORPUS,
            before='        kind_spec = profile.coordination_kinds.get(kind)\n        if kind_spec is None:\n            raise ValidationRefused(f"{kind!r} is not declared by the mounted coordination contract")',
            after='        kind_spec = profile.coordination_kinds.get(kind) or next(iter(profile.coordination_kinds.values()))'),
        (f"{_ACCEPT}::test_w18a_an_undeclared_kind_mints_nothing", "test_coordination_write.py::test_an_earlier_contract_version_authorizes_nothing_added_later")),
    Arm("W18b", "an ill-formed query refuses at mint",
        Sabotage(_CORPUS,
            before='        query = parse_view_query(content["query"])',
            after='        query = parse_view_query({"version": "science.view-query.v1", "clauses": []})'),
        (f"{_ACCEPT}::test_w18b_malformed_query_refuses",)),
    Arm("W18c", "a query kind outside the pinned literal vocabulary refuses",
        Sabotage(_CORPUS,
            before='        if query.world_kinds() - profile.coordination_query_kinds:\n            raise ValidationRefused("view query names a world kind outside the coordination contract vocabulary")',
            after='        if False:\n            raise ValidationRefused("view query names a world kind outside the coordination contract vocabulary")'),
        ("test_coordination_write.py::test_w18c_a_query_kind_outside_the_contract_refuses",)),
    Arm("W18d", "a query relation outside the pinned literal vocabulary refuses",
        Sabotage(_CORPUS,
            before='        if query.relations() - profile.coordination_query_relations:\n            raise ValidationRefused("view query names a relation outside the coordination contract vocabulary")',
            after='        if False:\n            raise ValidationRefused("view query names a relation outside the coordination contract vocabulary")'),
        ("test_coordination_write.py::test_w18d_a_query_relation_outside_the_contract_refuses",)),
    Arm("W18e", "a syntactically valid unresolved query anchor is accepted",
        Sabotage(_CORPUS,
            before='        return query',
            after='        if query.addresses():\n            raise ValidationRefused("view query address does not resolve")\n        return query'),
        (f"{_ACCEPT}::test_w18e_an_unresolved_anchor_is_accepted",)),
    Arm("W18f", "the compiler refuses query vocabulary outside kernel inventories",
        Sabotage(_PROFILE,
            before='    if unknown_kinds or unknown_relations:\n        raise ProfileError("coordination query vocabulary is outside the kernel inventory")',
            after='    if False:\n        raise ProfileError("coordination query vocabulary is outside the kernel inventory")'),
        ("test_profile.py::test_coordination_compile_refuses_unknown_query_kind", "test_profile.py::test_coordination_compile_refuses_unknown_query_relation")),
    Arm("W18g", "editorial and lineage edits move contract identity but not compiled identity",
        Sabotage(_PROFILE,
            before='    return contract.schema_projection()',
            after='    return {**contract.schema_projection(), "contract": contract.content_identity}'),
        ("test_profile.py::test_coordination_editorial_edits_do_not_recompile",)),
    Arm("W18h", "coordination schema edits move compiled identity",
        Sabotage(_PROFILE,
            before='    return contract.schema_projection()',
            after='    return {}'),
        ("test_profile.py::test_coordination_schema_edits_recompile",)),
    Arm("W18i", "coordination moves packaging identity but enters no world map",
        Sabotage(_EPOCH,
            before='        if node.kind in stored.WORLD_KINDS',
            after='        if True'),
        (f"{_ACCEPT}::test_w18i_coordination_moves_epoch_identity_not_world_maps_or_belief_input",)),
    Arm("W18j", "an activated coordination pin never enters a belief input digest",
        Sabotage("consulted.py",
            before='    consulted: dict[str, str] = {BASE_NAMESPACE: base_identities.pop()}',
            after='    consulted: dict[str, str] = {BASE_NAMESPACE: base_identities.pop()}\n    if "coordination" in pins[corpora[0]].domains:\n        consulted["coordination"] = pins[corpora[0]].domains["coordination"]'),
        ("test_belief.py::test_w18j_a_coordination_pin_never_enters_the_belief_input_digest",)),
    Arm("W18k", "a domain contract cannot claim the coordination namespace",
        Sabotage(_DOMAIN,
            before='    if namespace == "coordination":\n        raise MalformedContract(f"{source}: \'coordination\' is reserved for the coordination contract")',
            after='    if False:\n        raise MalformedContract(f"{source}: \'coordination\' is reserved for the coordination contract")'),
        ("test_domain_contract.py::test_a_domain_contract_cannot_claim_the_coordination_namespace",)),
)
```

- [ ] **Step 2: Write the declaration audit**

`test_n2_cut14.py` uses the cut-13 audit mechanism with these complete imports, cut-14 constants, and assertions:

```python
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import subprocess

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
from n2_arms_cut14 import CO_CITED, CUT14_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
CUT14_FREEZE_COMMIT = "c07bf72"
IMPLEMENTATION_AMENDMENT_COMMIT = "09b0b58"
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
}
FROZEN_CUT5_SHA256 = {
    "python/tests/n2_arms_cut5.py": "29a778a617627a697787ea62b578034e2407d45c2d9adb4e85816598af3f0f19",
    "python/tests/acceptance/test_n2_cut5.py": "df589285dd377709c322a2a3958196f3e8a8c65032af8d79863b548584e41798",
    "docs/designs/2026-08-19-conformance-cut-5.md": "683dc249b1898179beaac9c9a550bca5b43f5fe3af9a107f0fc7ee47d58cbdd0",
    "docs/plans/2026-08-19-conformance-cut-5-results.md": "3a24efe3678b99d977a6ddd4f464e600479fb689dedd6df3f5647cb58f6f32de",
}


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    root = tmp_path_factory.mktemp("n2-cut14")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT14_ARMS)))


def test_no_cut14_arm_is_vacuous_mixed_uncollected_or_stale(findings):
    for verdict in ("vacuous", "mixed", "uncollected", "stale"):
        offending = [finding for finding in findings if finding.verdict == verdict]
        assert not offending, "\n".join(f"{finding.arm.label}: {finding.detail}" for finding in offending)


def test_every_declared_check_passes_without_sabotage():
    every = Arm("N2", "all cut-14 checks pass", CUT14_ARMS[0].sabotage, tuple(dict.fromkeys(check for arm in CUT14_ARMS for check in arm.checks)))
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_the_29_arms_are_unique_and_account_for_every_selected_unit():
    rows = tuple(arm.row for arm in CUT14_ARMS)
    assert len(rows) == len(set(rows)) == 29
    assert ROW_UNITS == {"W11": 2, "W12": 1, "W13": 1, "W17": 14, "W18": 11}
    assert sum(ROW_UNITS.values()) == 29
    assert {unit_of(row) for row in rows} == {f"W11u{n}" for n in range(1, 3)} | {"W12u1", "W13u1"} | {f"W17u{n}" for n in range(1, 15)} | {f"W18u{n}" for n in range(1, 12)}
    assert LABELED_UNITS == () and CO_CITED == {}


def test_the_design_freeze_and_approved_amendment_are_ancestors():
    for commit in (CUT14_FREEZE_COMMIT, IMPLEMENTATION_AMENDMENT_COMMIT):
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"], check=False).returncode == 0


def test_prior_declarations_and_the_whole_cited_cut5_surface_are_unchanged():
    for path, commit in FROZEN_PRIOR_CUT_FILES.items():
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--quiet", commit, "HEAD", "--", path], check=False).returncode == 0
    for path, expected in FROZEN_CUT5_SHA256.items():
        assert sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected
```

Import all prior arm tables and form:

```python
PRIOR_ARMS = (*CUT3_ARMS, *CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS, *CUT10_ARMS, *CUT11_ARMS, *CUT12_ARMS, *CUT13_ARMS)


def test_every_arm_has_one_source_mutation_and_exact_check_nodes():
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT14_ARMS:
        assert arm.checks and len(arm.checks) == len(set(arm.checks)), arm.row
        assert arm.sabotage.before != arm.sabotage.after and arm.asserts.strip(), arm.row
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_no_cut14_arm_rehomes_a_prior_cuts_check():
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT14_ARMS:
        assert not (set(arm.checks) & prior), arm.row
```

No co-citation exception exists.

- [ ] **Step 3: Run the N2 audit**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut14.py`

Expected: PASS; every sabotage makes all and only its declared checks fail.

- [ ] **Step 4: Run focused static checks**

Run: `cd python && uv run --frozen ruff check tests/acceptance/n2_arms_cut14.py tests/acceptance/test_n2_cut14.py && uv run --frozen pyright tests/acceptance/n2_arms_cut14.py tests/acceptance/test_n2_cut14.py`

Expected: PASS.

- [ ] **Step 5: Close the task and commit**

```bash
tasks done beliefs-48c8b6 "Declared and audited all 29 executable cut-14 units with no intent-position arm."
git add python/tests/acceptance/n2_arms_cut14.py python/tests/acceptance/test_n2_cut14.py tasks
git commit -m "test(coordination): declare cut 14 arms"
```

### Task 12: Run Cut 14, Bank the Design, and Close the Boundary

**Files:**
- Create: `python/tools/cut14_acceptance.py`
- Create: `python/tests/test_cut14_acceptance.py`
- Create: `docs/plans/2026-09-02-conformance-cut-14-results.md`
- Modify: `.gitignore`
- Modify: `docs/plans/2026-09-02-coordination-view-kinds.md`
- Move: `docs/superpowers/specs/2026-08-31-coordination-and-view-kinds-design.md` → `docs/designs/2026-08-31-coordination-and-view-kinds-design.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md`
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md`
- Modify if its current claim is stale: `docs/designs/2026-08-02-world-addressing-design.md`
- Modify if its current claim is stale: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`
- Modify if its current claim is stale: `docs/guide/README.md`
- Modify if its current claim is stale: `docs/guide/foundations.md`
- Modify if its current claim is stale: `README.md`

**Interfaces:**
- Consumes: all eleven completed implementation tasks, the frozen §9 phase inventory, the certified tuple and confinement gate, cut-5 byte pins, and the tasks dependency chain.
- Produces: `cut14_acceptance.py`, a results record, a banked implemented design, corrected current-facing status, a re-ranked roadmap, all child tasks closed, and parent `beliefs-1f7400` closed in the same commit.

- [ ] **Step 1: Write the runner with no aggregate prefix**

Write the cut-14 launcher with the following complete work-directory, probe, cleanup, subprocess, and declared-arm-count mechanics:

```python
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut14-acceptance"
PREFIX_RUNNERS: tuple[str, ...] = ()
PHASE_MODULES = (
    "test_n2_cut6.py",
    "test_n2_cut7.py",
    "test_n2_cut9.py",
    "test_n2_cut10.py",
    "test_intent_boundary_acceptance.py",
    "test_n2_cut11.py",
    "test_successor_admission_acceptance.py",
    "test_n2_cut12.py",
    "test_confinement_acceptance.py",
    "test_n2_cut13.py",
    "test_coordination_acceptance.py",
    "test_n2_cut14.py",
)
PROBE_REFUSED = 2


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT14_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def cut_environment(run: Path) -> dict[str, str]:
    return {**os.environ, **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 15)}}


def declared_arm_count() -> int:
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut14 import CUT14_ARMS  # pyright: ignore[reportMissingImports]
    return len(CUT14_ARMS)


def probe(run: Path) -> str | None:
    from beliefs.confinement import host_prerequisites
    from beliefs.root import init_corpus_root, init_store_root, init_world_root, metadata_root_for
    from beliefs.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        init_store_root(store_root)
        reason = host_prerequisites()
        return None if reason is None else f"ConfinementUnavailable: {reason}"
    except Exception as refused:  # noqa: BLE001 - expose the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def main(argv: list[str]) -> int:
    for module in PHASE_MODULES:
        if not (ACCEPTANCE / module).is_file():
            print(f"cut-14 required acceptance module is missing: {ACCEPTANCE / module}", file=sys.stderr)
            return 1
    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(f"cut-14 acceptance cannot run here; this is an error, not a skip: {refusal}", file=sys.stderr)
            return PROBE_REFUSED
        for phase, module in enumerate(PHASE_MODULES, 1):
            print(f"[cut14 phase {phase}/{len(PHASE_MODULES)}] {module}", flush=True)
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", str(ACCEPTANCE / module), *(argv if phase == len(PHASE_MODULES) else ())],
                cwd=PYTHON_ROOT,
                check=False,
                env=cut_environment(run),
            )
            if completed.returncode != 0:
                return completed.returncode
        try:
            arms = declared_arm_count()
        except Exception as failure:  # noqa: BLE001 - report, do not mask a green run
            print(f"cut-14 acceptance: could not compute declared-arm count: {failure}", file=sys.stderr)
        else:
            print(f"declared arms: {arms} (= 29 selected units)", flush=True)
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)
```

No function invokes `cut5_acceptance.py` or any aggregate runner.

Add `.cut14-acceptance/` to the repository `.gitignore`; the default work root must never appear as an untracked discharge artifact.

- [ ] **Step 2: Write the portable runner-shape check**

```python
# python/tests/test_cut14_acceptance.py
import importlib.util
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("cut14_acceptance", Path(__file__).parents[1] / "tools" / "cut14_acceptance.py")
assert _SPEC is not None and _SPEC.loader is not None
cut14 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cut14)

EXPECTED = (
    "test_n2_cut6.py", "test_n2_cut7.py", "test_n2_cut9.py", "test_n2_cut10.py",
    "test_intent_boundary_acceptance.py", "test_n2_cut11.py",
    "test_successor_admission_acceptance.py", "test_n2_cut12.py",
    "test_confinement_acceptance.py", "test_n2_cut13.py",
    "test_coordination_acceptance.py", "test_n2_cut14.py",
)


def test_cut14_has_no_aggregate_prefix_and_the_exact_frozen_phase_order():
    assert cut14.PREFIX_RUNNERS == ()
    assert cut14.PHASE_MODULES == EXPECTED


def test_every_phase_receives_one_probed_environment_and_only_n2_receives_arguments(tmp_path, monkeypatch):
    acceptance = tmp_path / "acceptance"
    acceptance.mkdir()
    for module in EXPECTED:
        (acceptance / module).write_text("", encoding="utf-8")
    monkeypatch.setattr(cut14, "ACCEPTANCE", acceptance)
    monkeypatch.setattr(cut14, "work_directory", lambda: tmp_path)
    monkeypatch.setattr(cut14, "probe", lambda _run: None)
    calls = []
    monkeypatch.setattr(cut14.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs)) or subprocess.CompletedProcess(command, 0))
    monkeypatch.setattr(cut14, "declared_arm_count", lambda: 29)
    assert cut14.main(["-k", "one"]) == 0
    assert [Path(call[0][3]).name for call in calls] == list(EXPECTED)
    assert calls[-1][0][-2:] == ["-k", "one"]
    assert all(call[1]["env"]["SCIENCE_CUT14_ROOT"] for call in calls)


def test_declared_arm_count_imports_both_test_roots():
    assert cut14.declared_arm_count() == 29
```

- [ ] **Step 3: Run the portable runner check**

Run: `cd python && uv run --frozen pytest tests/test_cut14_acceptance.py`

Expected: PASS.

- [ ] **Step 4: Run the certified cut command once**

Run: `cd python && uv run --frozen python tools/cut14_acceptance.py`

Expected: all 12 phases PASS and the runner prints `declared arms: 29 (= 29 selected units)`. Any tuple or confinement refusal is an error, not a waiver.

- [ ] **Step 5: Run the final repository gates, with one full suite**

Run from `python/`, in this order:

```bash
uv run --frozen ruff check .
uv run --frozen pyright
uv run --frozen pytest
```

Expected: all PASS. This is the only full-suite invocation in the plan.

Run from the repository root:

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py
cd ..
git diff --check
tasks check
```

Expected: documentation checks PASS, `git diff --check` is silent, and `tasks check` reports zero errors and zero warnings.

- [ ] **Step 6: Bank the design and write the exact results record**

Move the approved design with `git mv`. Preserve frozen §9 byte-for-byte; compare it to `c07bf72` before and after the move. Update its status to implemented at the last implementation commit, with W17 explicitly partial only on intent-position.

The results record must state the exact observed command outcomes from Steps 4–5 and these fixed facts:

- frozen cut §9: `c07bf72`; approved implementation amendment: `09b0b58`;
- 29 selected units: W11 2, W12 1, W13 1, W17 14, W18 11; zero labeled units; no intent-position arm; W17's whole-revision clause is its own unit, while missing and divergent projects remain separate units;
- all 12 direct phase modules in their executed order and no aggregate prefix;
- cut 5 cited from `docs/plans/2026-08-19-conformance-cut-5-results.md`, with all four Task 11 SHA-256 pins unchanged;
- W11, W12, and W18 closed; W17 closed for the ordinary family and partial on intent-position; W13 still partial beyond the two-project negative;
- the certified volume/kernel/confinement facts printed by the runner; and
- the implementation commit range; identify the results record as committed with the discharge change rather than attempting to embed its own commit id.

Do not invent pass counts before the commands run; copy the actual totals and environment evidence into the record.

- [ ] **Step 7: Correct every current-facing status and re-rank the roadmap**

Mark `coordination-addressing` built in the adoption ledger and close only the selected row clauses. In the roadmap, record cut-14 discharge and re-rank the mutation lane from its then-current state; do not rewrite frozen selections or move the deferred intent-position clause away from `publish`. Grep all user-facing docs for `coordination-addressing`, `W17`, `W18`, `not implemented`, and the old design path; correct every claim made stale by banking. Keep historical plan/results prose unchanged.

Update this plan's `Spec:` path to `docs/designs/2026-08-31-coordination-and-view-kinds-design.md` in the banking change. If `test_n2_cut14.py` names the design path, update that path in the same change while keeping both commit ancestry checks.

- [ ] **Step 8: Close tasks in dependency order and commit**

First close this child, then close the parent, then verify the task graph:

```bash
tasks done beliefs-a03506 "Discharged cut 14, banked the coordination design, and recorded certified results."
tasks done beliefs-1f7400 "Delivered coordination and view kinds; cut 14 discharged with W17 intent-position deferred to publish."
tasks check
git add .gitignore python/tools/cut14_acceptance.py python/tests/test_cut14_acceptance.py python/tests/acceptance docs tasks README.md
git commit -m "docs(coordination): discharge conformance cut 14"
```

The staged docs must include every path changed in Steps 6–7. Do not use `tasks done --force`; every dependency is closed first.
