# D1 Cross-Repository Negative Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close D1 by adding a namespace-renaming invariance check over the installed `nodes`, an N2 that can sabotage a copy of `nodes`, and cut 26 that reads D1 in full.

**Architecture:** One portable test (`test_domain_boundary.py`) states the property; `Sabotage` gains a `package` field and N2 copies whichever package the arm names; cut 26's declaration file feeds both N2 directions through one `PORTABLE_ARMS` tuple and an acceptance guard pins the freeze. `nodes` gains one STANDARD sentence and one seam row, no code.

**Tech Stack:** Python 3.11+, pytest, `nodes.core` (editable sibling checkout at `../../nodes/python`), the N2 harness in `python/tests/test_n2.py`, `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md`

**Implementation status:** complete 2026-09-12; cut 26 discharged and D1 closed.

## Global Constraints

- Work in the worktree `.worktrees/d1-cross-repo-negative` (branch `design/d1-cross-repo-negative`); every path below is relative to the Beliefs repository root, and paths shown to the user are prefixed with the worktree directory.
- Every Python command runs from `python/` as `uv run --frozen …`. `pytest` is bare (addopts already has `-q`). `--ignore=tests/acceptance` is in `addopts`: an acceptance module runs only when named on the command line.
- The `nodes` tree is read, never written, by any Beliefs code; the only `nodes` edits are Task 1's two prose edits, made in the `nodes` repository.
- No domain-aware path lands in `nodes`, production or test. Sabotages exist only inside N2's scratch copies.
- Frozen declarations and cut bodies through cut 25 stay byte-exact. `n2_arms.py` (cut 1) is not pinned and gains a defaulted field only.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs the gate.
- `nodes` head at plan time: `5ff3c78`. Sabotage `before` blocks are verified against that tree; the results record the commit the discharge resolves.

---

## File map

| File | Responsibility |
| --- | --- |
| `../nodes/docs/STANDARD.md` §2.3 (nodes repo) | the opacity sentence |
| `../nodes/docs/designs/2026-08-17-nodes-write-plan-executor-seam-design.md` §8 (nodes repo) | the amendment row |
| `docs/designs/2026-09-12-conformance-cut-26.md` | the cut: boundary, selection, N2 obligations, second reader, limitations |
| `python/tests/test_domain_boundary.py` | the positive check (portable) |
| `python/tests/n2_arms.py` | `Sabotage.package`; `installed_nodes_root()` |
| `python/tests/test_n2.py` | package-aware copy and subprocess; `PORTABLE_ARMS`; self-tests |
| `python/tests/arm_staleness.py` | package-aware `working_tree`; `historical_tree` stays Beliefs-only |
| `python/tests/test_arm_staleness.py` | consumes `PORTABLE_ARMS` |
| `python/tests/n2_arms_cut26.py` | cut 26's declaration: units, checks, two arms |
| `python/tests/acceptance/n2_arms_cut26.py` | acceptance re-export shim |
| `python/tests/acceptance/test_n2_cut26.py` | the guard: accounting, freeze pins, prior pins, audit |
| `python/tools/cut26_acceptance.py` | the runner, chained after cut 25 |
| `docs/plans/2026-09-12-conformance-cut-26-results.md` | discharge record |
| ledger, roadmap, domain-boundary design status | `domain-boundary` → closed |

---

### Task 1: The `nodes`-local gate — STANDARD §2.3 and the seam row

**Files:**
- Modify: `/mnt/ssd/Dropbox/nodes/docs/STANDARD.md` (§2.3 Facets, after the sentence ending "New facet schemas SHOULD reject unknown keys.")
- Modify: `/mnt/ssd/Dropbox/nodes/docs/designs/2026-08-17-nodes-write-plan-executor-seam-design.md` (§8 Amendments log, append a row)

**Interfaces:**
- Produces: the `nodes` commit sha `NODES_GATE_COMMIT`, recorded in Task 5's declaration file and Task 6's results.

- [ ] **Step 1: File the `nodes` task and claim it**

Run from the `nodes` checkout:

```bash
cd /mnt/ssd/Dropbox/nodes
tasks add "Facet-name opacity: STANDARD 2.3 sentence and the seam row for Science's D1 negative" -p 2 --size xs --tag standard --source beliefs-928881 -b "Science's D1 negative (beliefs docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md section 4.4) asks nodes for two prose edits and no code: STANDARD 2.3 states that facet names outside the built-in set are opaque to the kernel while caller-supplied invariants may read any facet by name; the write-plan seam's section 8 records that Beliefs' N2 harness mutates a scratch copy of the installed package and the nodes tree gains nothing."
tasks start <nodes-id>
```

Record `<nodes-id>`. Then, back in the Beliefs worktree: `tasks dep beliefs-928881 --on <nodes-id>`.

- [ ] **Step 2: Add the STANDARD sentence**

Append this paragraph to §2.3, after "New facet schemas SHOULD reject unknown keys.":

```markdown
Facet names outside the built-in set (§5) are opaque to the kernel: no kernel
behaviour depends on a name's content beyond equality and ordering, and in
particular no namespace token (the part before a `/`) selects a kernel code
path. Caller-supplied invariants (§6) MAY read any facet by name — that is the
consumer's domain validation, not the kernel's. Consumers check this property
from outside; Science's D1 negative mutates a scratch copy of the installed
package and never this tree.
```

- [ ] **Step 3: Add the seam row**

Append to the Amendments log table in §8:

```markdown
| 2026-09-12 | §8 process | Science's D1 negative (Beliefs cut 26) audits a scratch copy of the installed `nodes` package under Beliefs' N2 harness, applying a domain-aware mutation to the copy and proving Beliefs' namespace-renaming check refuses it. The `nodes` tree gains no code, production or test; STANDARD §2.3's opacity sentence (this date) is the property checked. | `nodes`-side review | n/a — no exercised part changed; Science is the author |
```

- [ ] **Step 4: Verify the tree and commit in `nodes`**

```bash
cd /mnt/ssd/Dropbox/nodes
grep -n "opaque to the kernel" docs/STANDARD.md
tasks done <nodes-id> "STANDARD 2.3 opacity sentence and seam section 8 row; no code"
tasks check
git add docs/STANDARD.md docs/designs/2026-08-17-nodes-write-plan-executor-seam-design.md tasks/<nodes-id>.md
git commit -m "docs(standard): facet names outside the built-in set are opaque to the kernel

Science's D1 negative (beliefs-928881) checks this from outside over a scratch
copy of the installed package; the seam record says so. No code."
git rev-parse --short HEAD
```

Expected: `grep` prints one line; `tasks check` reports zero errors. Record the printed sha as `NODES_GATE_COMMIT`.

---

### Task 2: Cut 26's design document

**Files:**
- Create: `docs/designs/2026-09-12-conformance-cut-26.md`

**Interfaces:**
- Produces: the frozen body (§§2–7) Task 5's guard pins; the freeze commit sha `CUT26_FREEZE_COMMIT` and the document's sha256 at that commit `CUT26_FROZEN_SHA256`, both recorded in Task 5.

- [ ] **Step 1: Fetch the D1 row byte-exact from its source**

```bash
grep -n "^| D1 |" docs/designs/2026-08-04-domain-extension-boundary-design.md
```

Expected: one line (line 722). Copy it verbatim into the fenced block in Step 2 — the guard compares the fenced row against the source table.

- [ ] **Step 2: Write the document**

```markdown
# Conformance cut 26 — D1's cross-repository negative

**Status:** drafted 2026-09-12; freezes at the commit this line names once it does.
**Design:** `../superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md`, reviewed in two passes 2026-09-12.
**Numbered after and serialized after** cut 25, whose discharge is in the branch ancestry.
**`nodes` gate:** `nodes` commit `<NODES_GATE_COMMIT>` (STANDARD §2.3 opacity sentence; seam §8 row).

## 1. What this cut is

D1 says `nodes` assigns no domain semantics. Cut 20 read its inspection arm and
deferred the negative; cut 22 deferred it again. Both deferrals named the same
obstacle — the negative runs in another repository's tree — and neither named
the prior one: no check would refuse a `nodes` path that branches on `biology/`,
because signature inspection cannot see a branch on a string and a grep for
domain names fails a conforming tree.

This cut reads D1 in full. The design states opacity as an invariance: every
public `nodes` operation commutes with a bijective renaming of namespace tokens
that leaves the built-in facet names alone, over registries whose invariants are
the kernel's own. A portable Beliefs test asserts it over the installed package.
N2 gains a sabotage that names its package, copies `nodes`, applies a
domain-aware mutation to the copy, and proves the check fails there.

The selection rule is cut 5's: a clause is selected only when its source mutation
and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `python/tests/test_domain_boundary.py`: the invariance check,
  `test_d1_installed_nodes_is_invariant_under_namespace_renaming`, over
  `nodes.core.frontmatter`, `projection`, `registry`, `corpus` and `write_plan`,
  with a registry holding only the built-in shapes' invariants, two renamings
  (`biology` → `aaa`, `biology` → `zzz`), and fixtures that make the
  missing-facet, unexpected-facet and raising cases non-empty.
- `python/tests/n2_arms.py`, `test_n2.py`, `arm_staleness.py`: `Sabotage.package`
  (`"beliefs"` default, `"nodes"`); the package root resolved from the
  interpreter; the copy, the mutation and the subprocess `PYTHONPATH` per package;
  `working_tree` reading a `nodes` arm from the resolved tree; one
  `PORTABLE_ARMS` tuple feeding the sabotage audit, the unsabotaged baseline and
  the staleness gate.
- `python/tests/n2_arms_cut26.py`: one declaration unit, D1, two arms — the
  parser sabotage and the validation sabotage — each naming the one check above;
  cut 20's inspection check co-cited.
- `python/tests/acceptance/test_n2_cut26.py` and `python/tools/cut26_acceptance.py`.
- The `nodes` repository: STANDARD §2.3's opacity sentence and the seam §8 row,
  at `<NODES_GATE_COMMIT>`. No `nodes` code.

Out of scope: any domain-aware path in the `nodes` tree; `nodes`' own suite;
extending N2's commit-pinned (`historical_tree`) staleness reading to `nodes`;
every D row other than D1. Frozen declarations and cut bodies through cut 25
remain byte-exact.

## 3. Selection

### D1 — closes

```markdown
<the D1 row from Step 1, byte-exact>
```

**Selected:** the inspection arm cut 20 selected, re-cited
(`acceptance/test_facet_acceptance.py::test_d1_installed_nodes_takes_no_domain_argument`,
unchanged); the opacity clause, as the invariance check; the negative, as two N2
arms whose sabotage lands in a copy of `nodes`:

- **D1-a** — `core/frontmatter.py`, `node_from_markdown`'s facets read, drops
  every facet whose name starts with `biology/`. Unrenamed, the gene-axis facet
  disappears at parse; renamed, it survives. Clause 1 fails.
- **D1-b** — `core/registry.py`, `validate`'s present set excludes `biology/`
  names. A required `biology/gene-axis` reads as missing unrenamed and present
  renamed. Clause 3 fails.

**Deferred:** nothing. The grep clause is honoured by its own terms: the check
never reads a name's content, so `nodes`' fixtures carrying `biology/gene-axis`
pass it.

### Boundary invariants

No verdict changes for any Beliefs record. No claim identity changes. The
installed `nodes` tree is byte-identical before and after every N2 run.

## 4. Accounting

One guarantee row is read, **1 full/closed** (D1). The frozen inventory is
**1 declaration unit** expanding to 2 one-mutation sabotage arms. The global
corpus moves to **148 of 195 rows closed, 47 open**. `domain-boundary` closes.

## 5. N2 and acceptance obligations

Every arm's `before` block occurs exactly once in the resolved `nodes` tree at
`<NODES_GATE_COMMIT>`; `test_n2.py` audits both arms at every serial run, and
`test_n2_cut26.py` audits them at the discharge. Both directions: the check
passes against the real package (`baseline`) and fails under each sabotage
(`audit`). The harness self-tests prove a `nodes` sabotage that does not apply
scores `stale`, the copy is mutated and the source is not, and the copy shadows
the installed package in the subprocess.

## 6. Second reader

Verify the fenced row byte-exact against its source table at the freeze commit;
audit every selected clause against §2; force any unrun clause to remain
deferred and its row partial. Challenge especially:

- the registry the check builds carries no consumer invariant, so a legitimate
  domain semantic cannot be mistaken for a kernel one;
- violation lists compare after renaming and re-sorting, over non-empty cases;
- each sabotage applies exactly once and the check fails under each on its own;
- the `nodes` tree is unchanged after the audit;
- STANDARD §2.3's sentence is in the `nodes` tree at the cited commit.

## 7. Limitations

- The invariance is read over `nodes.core`'s public surface named in §2; a
  domain-aware path in a surface the check does not exercise (search, similarity)
  would not be refused. Those surfaces read titles and bodies, not facet names,
  today; the limitation is stated rather than closed.
- `historical_tree` does not read `nodes`, so a commit-pinned guard cannot audit
  a `nodes` arm against a historical `nodes` tree. Cut 26 audits the working tree.
```

- [ ] **Step 3: Commit the draft**

```bash
tasks check
git add docs/designs/2026-09-12-conformance-cut-26.md
git commit -m "docs(cut26): draft the cut reading D1 in full"
```

Freezing (status line, `CUT26_FREEZE_COMMIT`) happens in Task 5 Step 6, after the harness exists and the sabotages are verified.

---

### Task 3: The positive check — `python/tests/test_domain_boundary.py`

**Files:**
- Create: `python/tests/test_domain_boundary.py`

**Interfaces:**
- Produces: `test_d1_installed_nodes_is_invariant_under_namespace_renaming[sorts-first]` and `[sorts-last]` — the check Task 5's arms name as `test_domain_boundary.py::test_d1_installed_nodes_is_invariant_under_namespace_renaming`.

- [ ] **Step 1: Write the test module**

```python
"""D1 — `nodes` assigns no domain semantics, read as an invariance.

For every bijective renaming ρ of namespace tokens (the part of a facet name before
`/`), every public `nodes` operation commutes with ρ. Built-in facet names carry no
`/`, so ρ never touches them; consumer invariants are the consumer's domain semantics
and are outside the property, so the registry here holds only the kernel's shape
invariants. Diagnostics compare after renaming and re-sorting, since `Registry.check`
sorts by name and a renamed token legitimately moves.

Design: docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md §3.
The subject is the installed `nodes`; N2 runs this same test against a sabotaged copy
(n2_arms_cut26.py), where it must fail.
"""

from __future__ import annotations

import re

import pytest
from nodes.core.corpus import Corpus
from nodes.core.errors import FacetError
from nodes.core.frontmatter import node_from_bytes, node_from_markdown, node_to_markdown
from nodes.core.node import Node
from nodes.core.paths import path_for_node_id
from nodes.core.projection import to_canonical
from nodes.core.registry import KindSpec, Registry, Violation
from nodes.core.shapes import register_builtin_shapes
from nodes.core.write_plan import CreateOp

NAMESPACED = re.compile(r"^([^/]+)/([^/]+)$")

RENAMINGS = {
    "sorts-first": {"biology": "aaa"},  # the renamed token sorts before every other key
    "sorts-last": {"biology": "zzz"},  # and after
}

# `nodes`' own `fixtures/gene-axis.md`, inlined: a sabotaged copy of the package has no
# fixtures directory beside it, and the check must read the same bytes either way.
GENE_AXIS = """---
id: dataset:gene-expression-matrix
uid: 4f1a9c2e8b7d4f1a9c2e8b7d4f1a9c2e
kind: dataset
title: Gene expression matrix
facets:
  biology:
    organism: Homo sapiens
  biology/gene-axis:
    axis: rows
---
Rows are genes; columns are samples.
"""


def _rename_name(name: str, rho: dict[str, str]) -> str:
    match = NAMESPACED.match(name)
    if match is None:
        return name
    return f"{rho.get(match[1], match[1])}/{match[2]}"


def _rename_node(node: Node, rho: dict[str, str]) -> Node:
    return node.model_copy(update={"facets": {_rename_name(k, rho): v for k, v in node.facets.items()}})


def _rename_spec(spec: KindSpec, rho: dict[str, str]) -> KindSpec:
    return spec.model_copy(
        update={
            "required_facets": {_rename_name(n, rho) for n in spec.required_facets},
            "optional_facets": {_rename_name(n, rho) for n in spec.optional_facets},
        }
    )


def _rename_canonical(canonical: dict[str, object], rho: dict[str, str]) -> dict[str, object]:
    facets = canonical["facets"]
    assert isinstance(facets, dict)
    return {**canonical, "facets": {_rename_name(k, rho): v for k, v in facets.items()}}


def _rename_violations(violations: list[Violation], rho: dict[str, str]) -> list[Violation]:
    renamed = [
        Violation(
            code=v.code,
            detail=_rename_name(v.detail, rho),
            message=v.message.replace(repr(v.detail), repr(_rename_name(v.detail, rho))),
        )
        for v in violations
    ]
    return sorted(renamed, key=lambda v: (v.code, v.detail))


def _sorted(violations: list[Violation]) -> list[Violation]:
    return sorted(violations, key=lambda v: (v.code, v.detail))


SPECS = (
    KindSpec(name="dataset", required_facets={"biology/gene-axis"}, optional_facets={"biology", "chemistry/assay"}),
    KindSpec(name="genes", shape="set", optional_facets={"biology/gene-axis"}),
)


def _registry(rho: dict[str, str]) -> Registry:
    """Kernel invariants only: the built-in shapes and nothing supplied by a consumer."""
    registry = Registry()
    register_builtin_shapes(registry)
    for spec in SPECS:
        registry.register(_rename_spec(spec, rho))
    return registry


def _nodes() -> dict[str, Node]:
    # Constructed, not parsed: a node the parser never touched, so that a parser that
    # drops a facet is caught at clause 1 rather than hidden by having dropped it here.
    gene_axis = Node(
        id="dataset:gene-expression-matrix",
        uid="4f1a9c2e8b7d4f1a9c2e8b7d4f1a9c2e",
        kind="dataset",
        title="Gene expression matrix",
        body="Rows are genes; columns are samples.",
        facets={"biology": {"organism": "Homo sapiens"}, "biology/gene-axis": {"axis": "rows"}},
    )
    return {
        "valid": gene_axis,
        # A non-empty membership naming the dataset, so clause 4 has a structural reference
        # to read back through `members` and `containers` and not only a node to fetch.
        "built-in-beside-namespaced": Node(
            id="genes:all",
            uid="0" * 32,
            kind="genes",
            title="all genes",
            facets={
                "membership": {"members": ["dataset:gene-expression-matrix"]},
                "biology/gene-axis": {"axis": "rows"},
            },
        ),
        "missing-required": gene_axis.model_copy(update={"facets": {"biology": {"organism": "Homo sapiens"}}}),
        "unexpected": gene_axis.model_copy(
            update={"facets": {**gene_axis.facets, "biology/extra": {}, "physics/extra": {}}}
        ),
    }


def _validate_outcome(registry: Registry, node: Node) -> type[BaseException] | None:
    try:
        registry.validate(node)
    except FacetError as error:
        return type(error)
    return None


@pytest.mark.parametrize("rho", list(RENAMINGS.values()), ids=list(RENAMINGS))
def test_d1_installed_nodes_is_invariant_under_namespace_renaming(rho, tmp_path):
    identity: dict[str, str] = {}
    registry, renamed_registry = _registry(identity), _registry(rho)
    # the fixture nodes ships parses to the facets the constructed node carries
    assert node_from_markdown(GENE_AXIS).facets == _nodes()["valid"].facets
    for label, node in _nodes().items():
        renamed = _rename_node(node, rho)
        # 1. the boundary parser and serializer commute with ρ
        assert node_from_markdown(node_to_markdown(renamed)) == _rename_node(
            node_from_markdown(node_to_markdown(node)), rho
        ), label
        assert node_from_bytes(node_to_markdown(renamed).encode("utf-8")) == _rename_node(
            node_from_bytes(node_to_markdown(node).encode("utf-8")), rho
        ), label
        # 2. the canonical projection commutes with ρ, as structures
        assert to_canonical(renamed) == _rename_canonical(to_canonical(node), rho), label
        # 3. validation verdicts and re-sorted diagnostics commute with ρ
        assert _validate_outcome(renamed_registry, renamed) == _validate_outcome(registry, node), label
        assert _sorted(renamed_registry.check(renamed)) == _rename_violations(registry.check(node), rho), label
    # non-empty by construction, so clause 3 compared something
    nodes = _nodes()
    assert _validate_outcome(registry, nodes["missing-required"]) is FacetError
    assert [v.code for v in registry.check(nodes["unexpected"])] == ["facet-unexpected", "facet-unexpected"]
    # 4. a corpus written with ρ(n) reads back as ρ of what n reads back as — the nodes
    #    themselves and the structural index over them
    dataset, container = nodes["valid"], nodes["built-in-beside-namespaced"]
    read: dict[str, tuple[list[Node], list[str], list[str]]] = {}
    for label, mapping in (("plain", identity), ("renamed", rho)):
        root = tmp_path / label
        root.mkdir()
        corpus = Corpus(root, registry=_registry(mapping))
        plan = [
            CreateOp(path_for_node_id(n.id), node_to_markdown(_rename_node(n, mapping)).encode("utf-8"))
            for n in (dataset, container)
        ]
        corpus.executor.execute(plan)
        reopened = Corpus(root, registry=_registry(mapping))
        read[label] = (
            [reopened.get(n.id) for n in (dataset, container)],
            reopened.members(container.id),
            reopened.containers(dataset.id),
        )
        assert {n.id for n in reopened.all()} == {dataset.id, container.id}
    plain_nodes, plain_members, plain_containers = read["plain"]
    assert plain_members == [dataset.id] and plain_containers == [container.id]  # non-empty by construction
    assert read["renamed"] == ([_rename_node(n, rho) for n in plain_nodes], plain_members, plain_containers)
```

- [ ] **Step 2: Run it against the real `nodes`**

```bash
cd python && uv run --frozen pytest tests/test_domain_boundary.py -v
```

Expected: both parametrized cases PASS. If `_registry` fails on `registry._specs.pop("set")`, read `register_builtin_shapes` again — it registers kinds named after each shape; the pop removes the bare `set` kind so the test's own `set` spec with an optional namespaced facet can register. If `Corpus(root, registry=...)` refuses the gene-axis node on rebuild, the bare `biology` facet is the cause: it is optional in the `dataset` spec above, so check the spec was registered before the corpus was opened.

- [ ] **Step 3: Prove it fails against a sabotaged copy (the red half, by hand)**

```bash
cd python
SCRATCH=$(mktemp -d)
cp -r "$(uv run --frozen python -c 'import importlib.util,pathlib;print(pathlib.Path(importlib.util.find_spec("nodes.core").submodule_search_locations[0]).parent)')" "$SCRATCH/nodes"
python3 - "$SCRATCH/nodes/core/frontmatter.py" <<'EOF'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
before = '    facets = fm["facets"] if "facets" in fm else {}  # absence defaults; null does not\n'
assert s.count(before) == 1
p.write_text(s.replace(before, before + '    facets = {k: v for k, v in facets.items() if not k.startswith("biology/")}\n'))
EOF
PYTHONPATH="$SCRATCH" uv run --frozen pytest tests/test_domain_boundary.py -p no:cacheprovider; echo "exit $?"
rm -rf "$SCRATCH"
```

Expected: both cases FAIL at the fixture-parity assertion (the sabotaged parser dropped `biology/gene-axis`), exit 1. Then the same with the validation sabotage:

```bash
SCRATCH=$(mktemp -d)
cp -r "$(uv run --frozen python -c 'import importlib.util,pathlib;print(pathlib.Path(importlib.util.find_spec("nodes.core").submodule_search_locations[0]).parent)')" "$SCRATCH/nodes"
python3 - "$SCRATCH/nodes/core/registry.py" <<'EOF'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
before = "        present = set(node.facets)\n        missing = required - present\n"
assert s.count(before) == 1
p.write_text(s.replace(before, '        present = {name for name in node.facets if not name.startswith("biology/")}\n        missing = required - present\n'))
EOF
PYTHONPATH="$SCRATCH" uv run --frozen pytest tests/test_domain_boundary.py -p no:cacheprovider; echo "exit $?"
rm -rf "$SCRATCH"
```

Expected: both cases FAIL on clause 3 (`_validate_outcome` differs for `valid`), exit 1.

- [ ] **Step 4: Lint, typecheck, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks check
git add python/tests/test_domain_boundary.py
git commit -m "test(d1): the installed nodes is invariant under namespace renaming

The check D1's negative is refused by. Kernel invariants only; diagnostics
compare renamed and re-sorted; missing, unexpected and raising cases are
non-empty. Fails by hand against a copy of nodes that drops or discounts
biology/ facets."
```

---

### Task 4: N2 sabotages a copy of `nodes`

**Files:**
- Modify: `python/tests/n2_arms.py:51-66` (`Sabotage`), plus a new function after it
- Modify: `python/tests/test_n2.py:67` (`PACKAGE`), `:181-189` (`_sabotage`), and new self-tests after `test_an_explicit_cache_root_reaches_n2_children`
- Modify: `python/tests/arm_staleness.py:129-152` (`working_tree`, `historical_tree`), `:154-166` (`stale_arms`)
- Modify: `python/tests/test_arm_staleness.py:59-61` (the reader call)

**Interfaces:**
- Produces: `Sabotage(module, before, after, package="beliefs")`; `n2_arms.installed_nodes_root() -> Path` (the resolved `src/nodes`); `test_n2.PACKAGES: dict[str, Path]`; `arm_staleness.TreeReader`, a `Protocol` whose `__call__(self, module: str, package: str = "beliefs") -> str | None` every reader (`working_tree`, `historical_tree`, `audited_tree`) returns and `stale_arms` takes — the default keeps every existing one-argument call site valid under pyright.
- Consumes: Task 3's test as the check the self-tests name.

- [ ] **Step 1: Write the failing self-tests in `test_n2.py`**

Add after `test_an_explicit_cache_root_reaches_n2_children`:

```python
NODES_CHECK = "test_domain_boundary.py::test_d1_installed_nodes_is_invariant_under_namespace_renaming"


def test_a_nodes_sabotage_that_does_not_apply_is_stale(tmp_path):
    arm = Arm(
        row="D1",
        asserts="a sabotage written against code nodes no longer has",
        sabotage=Sabotage(package="nodes", module="core/registry.py", before="this text is not in nodes\n", after=""),
        checks=(NODES_CHECK,),
    )
    assert audit(arm, tmp_path).verdict == "stale"


def test_a_nodes_sabotage_mutates_the_copy_and_never_the_source(tmp_path):
    from n2_arms import installed_nodes_root

    source = installed_nodes_root()
    before_bytes = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.py")}
    arm = Arm(
        row="D1",
        asserts="the copy carries the mutation",
        sabotage=Sabotage(
            package="nodes",
            module="core/registry.py",
            before="        present = set(node.facets)\n        missing = required - present\n",
            after="        present = set()\n        missing = required - present\n",
        ),
        checks=(NODES_CHECK,),
    )
    package = _sabotage(arm, tmp_path)
    assert package == tmp_path / "nodes"
    assert "present = set()" in (package / "core" / "registry.py").read_text(encoding="utf-8")
    assert {p.relative_to(source): p.read_bytes() for p in source.rglob("*.py")} == before_bytes


def test_a_nodes_copy_shadows_the_installed_package_in_the_subprocess(tmp_path):
    import subprocess
    import sys

    arm = Arm(
        row="D1",
        asserts="the subprocess imports the copy",
        sabotage=Sabotage(
            package="nodes",
            module="core/registry.py",
            before="        present = set(node.facets)\n        missing = required - present\n",
            after="        present = set()\n        missing = required - present\n",
        ),
        checks=(NODES_CHECK,),
    )
    package = _sabotage(arm, tmp_path)
    assert package is not None
    completed = subprocess.run(
        [sys.executable, "-c", "import nodes.core.registry as r; print(r.__file__)"],
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(package.parent)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == str(package / "core" / "registry.py")
```

- [ ] **Step 2: Run them to see them fail**

```bash
cd python && uv run --frozen pytest tests/test_n2.py -k "nodes_sabotage or nodes_copy" -v
```

Expected: all three FAIL — `Sabotage.__init__() got an unexpected keyword argument 'package'`.

- [ ] **Step 3: Extend `Sabotage` and add `installed_nodes_root`**

In `n2_arms.py`, replace the `Sabotage` class body's field block with:

```python
    module: str
    """Path under the package root — `src/beliefs` by default, `src/nodes` for a
    `nodes` sabotage — e.g. `resolution.py`, `contract/domain.py`, `core/registry.py`."""

    before: str
    after: str

    package: str = "beliefs"
    """Which package the mutation lands in: `beliefs`, or `nodes` for D1's
    cross-repository negative, where the copy N2 mutates is of the installed
    `nodes` and the real tree is never written."""
```

Add after the class:

```python
def installed_nodes_root() -> Path:
    """The `src/nodes` directory of the `nodes` the interpreter installed — the
    sibling editable checkout locally, the default-branch checkout in CI. `nodes`
    is a namespace package, so it is found through `nodes.core`."""
    spec = importlib.util.find_spec("nodes.core")
    assert spec is not None and spec.submodule_search_locations, "nodes.core is not installed"
    return Path(next(iter(spec.submodule_search_locations))).resolve().parent
```

with `import importlib.util` and `from pathlib import Path` at the top of the module (keep `from __future__ import annotations` first), and add `"installed_nodes_root"` to `__all__`.

- [ ] **Step 4: Make `test_n2` package-aware**

Replace `PACKAGE = ...` (line 67) with:

```python
PACKAGE = Path(__file__).resolve().parent.parent / "src" / "beliefs"
PACKAGES = {"beliefs": PACKAGE, "nodes": installed_nodes_root()}
"""Where each package's source is read from. A sabotage names one of these; the copy
under the arm's workspace carries the package's own directory name, so `PYTHONPATH`
set to the copy's parent shadows the installed package by that name."""
```

and import `installed_nodes_root` from `n2_arms`. Replace `_sabotage`:

```python
def _sabotage(arm: Arm, into: Path) -> Path | None:
    """Copy the arm's package into `into` and apply the mutation. `None` if it does not apply."""
    source_root = PACKAGES[arm.sabotage.package]
    package = into / source_root.name
    shutil.copytree(source_root, package)
    target = package / arm.sabotage.module
    if not target.is_file():
        return None
    source = target.read_text(encoding="utf-8")
    if source.count(arm.sabotage.before) != 1:
        return None
    target.write_text(source.replace(arm.sabotage.before, arm.sabotage.after), encoding="utf-8")
    return package
```

`_run_check` needs no change: `env["PYTHONPATH"] = str(package.parent)` already puts the copy's parent first.

- [ ] **Step 5: Run the self-tests**

```bash
cd python && uv run --frozen pytest tests/test_n2.py -k "nodes_sabotage or nodes_copy" -v
```

Expected: all three PASS.

- [ ] **Step 6: Make the staleness reader package-aware**

In `arm_staleness.py`, add `Protocol` to the `typing` imports (add the import if the module has none) and define the reader contract once, after `StaleArm`:

```python
class TreeReader(Protocol):
    """A module's source in one package's tree, or `None` when the tree has no such module.

    `package` defaults so that every reader can be called with a module alone, as the
    Beliefs-only callers always have; a `nodes` arm passes its own package.
    """

    def __call__(self, module: str, package: str = "beliefs") -> str | None: ...
```

Replace `working_tree`:

```python
def working_tree(repo_root: Path) -> TreeReader:
    roots = {"beliefs": repo_root / "python" / "src" / "beliefs", "nodes": installed_nodes_root()}

    def read(module: str, package: str = "beliefs") -> str | None:
        path = roots[package] / module
        return path.read_text(encoding="utf-8") if path.is_file() else None

    return read
```

Change `historical_tree`'s return annotation to `-> TreeReader`, its inner signature to `def read(module: str, package: str = "beliefs") -> str | None:`, and add as its first line:

```python
        if package != "beliefs":
            return None  # a nodes arm has no Beliefs commit to read from; it reads as stale here
```

Change `audited_tree`'s return annotation to `-> TreeReader`, `stale_arms`'s parameter to `read: TreeReader`, and inside it `source = read(arm.sabotage.module)` to `source = read(arm.sabotage.module, arm.sabotage.package)`. Import `installed_nodes_root` from `n2_arms`. The three `Callable[[str], str | None]` annotations in the module are now all `TreeReader`; grep for `Callable[[str]` afterwards and expect no match.

- [ ] **Step 7: Add the reader test and run the staleness suite**

In `test_arm_staleness.py`, extend `test_a_module_the_tree_no_longer_has_is_stale_not_an_error` with two lines after the existing asserts:

```python
    assert read("core/registry.py", "nodes") is not None
    assert read("core/registry.py") is None  # a nodes module is not a beliefs module
```

```bash
cd python && uv run --frozen pyright && uv run --frozen pytest tests/test_arm_staleness.py "tests/test_n2.py::test_a_nodes_sabotage_that_does_not_apply_is_stale" "tests/test_n2.py::test_a_nodes_sabotage_mutates_the_copy_and_never_the_source" "tests/test_n2.py::test_a_nodes_copy_shadows_the_installed_package_in_the_subprocess" "tests/test_n2.py::test_an_explicit_cache_root_reaches_n2_children" -v
```

Expected: pyright 0 errors; every selected test PASS. The session audit (`TestEveryArmAssertsSomething`, the `findings` fixture) is not selected — it is named by node id nowhere above, and `-k` would not exclude it since it matches names, not fixtures. Task 5 Step 4 runs it in full.

- [ ] **Step 8: Lint, typecheck, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks check
git add python/tests/n2_arms.py python/tests/test_n2.py python/tests/arm_staleness.py python/tests/test_arm_staleness.py
git commit -m "test(n2): a sabotage names its package, and nodes can be the package

Sabotage.package defaults to beliefs; nodes resolves from the interpreter,
is copied whole, mutated in the copy and shadowed on PYTHONPATH as the
namespace package it is. Staleness reads a nodes arm from the same tree.
Self-tests: a non-applying nodes sabotage is stale, the source is never
written, the subprocess imports the copy."
```

---

### Task 5: Cut 26's declaration, the shared inventory, the guard and the runner

**Files:**
- Create: `python/tests/n2_arms_cut26.py`
- Create: `python/tests/acceptance/n2_arms_cut26.py`
- Create: `python/tests/acceptance/test_n2_cut26.py`
- Create: `python/tools/cut26_acceptance.py`
- Modify: `python/tests/test_n2.py:259` and `:301` (the two tuples → `PORTABLE_ARMS`)
- Modify: `python/tests/test_arm_staleness.py:65-71`
- Modify: `docs/designs/2026-09-12-conformance-cut-26.md` (freeze status line)

**Interfaces:**
- Consumes: Task 3's check id; Task 4's `Sabotage.package`; Task 1's `NODES_GATE_COMMIT`; Task 2's document.
- Produces: `CUT26_ARMS`, `DECLARATION_UNITS`, `UNIT_CHECKS`, `CO_CITED`, `unit_of`, `NODES_SOURCE_COMMIT`; `test_n2.PORTABLE_ARMS`.

- [ ] **Step 1: Write the declaration file**

`python/tests/n2_arms_cut26.py`:

```python
"""Cut 26 canonical declaration: D1 in full, two sabotages that land in a copy of `nodes`."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("D1",)

NODES_SOURCE_COMMIT = "<NODES_GATE_COMMIT>"
"""The `nodes` commit the `before` blocks below were written against. Human-read: the
harness audits whatever `nodes` the interpreter resolves, and the cut's results record
what that was at the discharge."""

UNIT_CHECKS = {
    "D1": "test_domain_boundary.py::test_d1_installed_nodes_is_invariant_under_namespace_renaming",
}

CO_CITED = ("acceptance/test_facet_acceptance.py::test_d1_installed_nodes_takes_no_domain_argument",)
"""Cut 20's inspection arm, re-cited unchanged; not an arm of this cut."""


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-26 row")
    return unit


CUT26_ARMS = (
    Arm(
        row="D1-a",
        asserts="the boundary parser keeps a namespaced facet whatever its namespace says",
        sabotage=Sabotage(
            package="nodes",
            module="core/frontmatter.py",
            before='    facets = fm["facets"] if "facets" in fm else {}  # absence defaults; null does not\n',
            after=(
                '    facets = fm["facets"] if "facets" in fm else {}  # absence defaults; null does not\n'
                '    facets = {k: v for k, v in facets.items() if not k.startswith("biology/")}\n'
            ),
        ),
        checks=(UNIT_CHECKS["D1"],),
    ),
    Arm(
        row="D1-b",
        asserts="registry validation counts a namespaced facet as present whatever its namespace says",
        sabotage=Sabotage(
            package="nodes",
            module="core/registry.py",
            before="        present = set(node.facets)\n        missing = required - present\n",
            after=(
                '        present = {name for name in node.facets if not name.startswith("biology/")}\n'
                "        missing = required - present\n"
            ),
        ),
        checks=(UNIT_CHECKS["D1"],),
    ),
)
```

Replace `<NODES_GATE_COMMIT>` with Task 1's sha.

- [ ] **Step 2: Write the acceptance shim**

`python/tests/acceptance/n2_arms_cut26.py`:

```python
"""Acceptance re-export of the one canonical cut-26 arm table."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_cut26_canonical", Path(__file__).resolve().parents[1] / "n2_arms_cut26.py")
assert _spec is not None and _spec.loader is not None
_table = module_from_spec(_spec)
_spec.loader.exec_module(_table)
CUT26_ARMS = _table.CUT26_ARMS
DECLARATION_UNITS = _table.DECLARATION_UNITS
UNIT_CHECKS = _table.UNIT_CHECKS
CO_CITED = _table.CO_CITED
NODES_SOURCE_COMMIT = _table.NODES_SOURCE_COMMIT
unit_of = _table.unit_of
```

- [ ] **Step 3: One inventory for both N2 directions and the staleness gate**

In `test_n2.py`, add `from n2_arms_cut26 import CUT26_ARMS` beside the cut 2 and 3 imports, and after `HARNESS = ...`:

```python
PORTABLE_ARMS = (*ARMS, *CUT2_ARMS, *CUT3_ARMS, *CUT26_ARMS)
"""Every arm the portable suite audits. One tuple, consumed by the session audit under
sabotage and by the unsabotaged baseline below, so the two directions cannot drift —
a cut added to one and not the other would be audited without ever being shown to
pass in this harness's environment. Cut 26's arms are here, not only in an acceptance
guard, because their sabotage lands in `nodes` and a `nodes` that moves under it has to
be seen at every serial run, not at the next discharge."""
```

Replace line 259's `all_arms = (*ARMS, *CUT2_ARMS, *CUT3_ARMS)` with `all_arms = PORTABLE_ARMS`, and line 301's `for arm in (*ARMS, *CUT2_ARMS, *CUT3_ARMS)` with `for arm in PORTABLE_ARMS`. Update the fixture docstring's "cuts 1–3" to "cuts 1–3 and 26".

In `test_arm_staleness.py`, add `from test_n2 import PORTABLE_ARMS` and replace `test_the_portable_harness_arms_apply_exactly_once` with:

```python
def test_the_portable_harness_arms_apply_exactly_once() -> None:
    """Cuts 1–3 and 26, which `test_n2.py` audits and the fast loop ignores. Cut 26's arms
    are read from the installed `nodes` tree."""
    stale = arm_staleness.stale_arms("test_n2.py", PORTABLE_ARMS, arm_staleness.working_tree(REPO_ROOT))

    assert stale == ()
```

- [ ] **Step 4: Run the portable audit in full**

```bash
cd python && uv run --frozen pytest tests/test_n2.py tests/test_arm_staleness.py
```

Expected: PASS, including `test_no_arm_survives_its_own_sabotage` (both D1 arms `sound`) and `test_every_check_resolves_and_passes_without_the_sabotage`. Takes a few minutes.

- [ ] **Step 5: Write the guard**

`python/tests/acceptance/test_n2_cut26.py` — copy `test_n2_cut25.py` and change what follows; the shape is identical, so only the differences are listed, every one of them:

```python
"""Cut 26 declaration accounting, freeze pin, and N2 audit."""
```

Imports: keep every `from n2_arms_cutN import CUTN_ARMS` for cuts 3–24, add `from n2_arms_cut25 import CUT25_ARMS as FROZEN_CUT25_ARMS` and `from test_n2_cut25 import CUT25_ARMS` (the live tuple with its supplement), replace the cut 25 declaration imports with `from n2_arms_cut26 import CO_CITED, CUT26_ARMS, DECLARATION_UNITS, NODES_SOURCE_COMMIT, unit_of`, and add `from n2_arms import installed_nodes_root`. No live supplement: `CUT26_ARMS` is the frozen tuple.

Constants:

```python
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-12-conformance-cut-26.md"
CUT26_FREEZE_COMMIT = "<filled at Step 6>"
CUT26_FROZEN_SHA256 = "<filled at Step 6>"
```

`FROZEN_PRIOR_CUT_FILES`: cut 25's table plus `"python/tests/acceptance/n2_arms_cut25.py": "515fc8b"`. `PRIOR_ARMS`: cut 25's tuple plus `*CUT25_ARMS`.

The cut's **own** declaration is pinned too — cut 25's guard pins the document and the prior declarations but not its own table, so an edit to a sabotage's text or an arm's check after the freeze would pass it. Add:

```python
FROZEN_DECLARATION = "python/tests/n2_arms_cut26.py"
CUT26_DECLARATION_SHA256 = "<filled at Step 6>"


def test_the_declaration_is_byte_exact_against_the_freeze() -> None:
    """The arms the guard audits are the arms that were frozen: the canonical table's
    bytes at HEAD equal its bytes at the freeze commit, and that digest is pinned here
    so a rewrite of both the file and the commit reference cannot pass silently."""
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT26_DECLARATION_SHA256
    assert current.decode("utf-8") == _show(CUT26_FREEZE_COMMIT, FROZEN_DECLARATION)
```

Tests, each replacing its cut 25 counterpart:

```python
def test_the_inventory_is_exactly_the_one_declared_unit() -> None:
    assert DECLARATION_UNITS == ("D1",)
    assert {unit_of(arm.row) for arm in CUT26_ARMS} == {"D1"}
    assert [arm.row for arm in CUT26_ARMS] == ["D1-a", "D1-b"]
    assert all(arm.sabotage.package == "nodes" for arm in CUT26_ARMS)


def test_each_sabotage_names_one_real_source_site() -> None:
    package = installed_nodes_root()
    for arm in CUT26_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row


def test_the_nodes_gate_is_in_the_installed_tree() -> None:
    """STANDARD §2.3's sentence is what the arms check; the installed nodes must carry it.
    The commit itself is human-read (results §1): CI's nodes checkout has no history."""
    standard = installed_nodes_root().parents[2] / "docs" / "STANDARD.md"
    assert standard.is_file(), standard
    assert "opaque to the kernel" in standard.read_text(encoding="utf-8")
    assert len(NODES_SOURCE_COMMIT) >= 7
```

Keep `test_each_lettered_arm_is_unique_and_carries_an_exact_check`, `test_every_live_check_resolves_and_passes_without_sabotage`, `test_every_arm_fails_under_its_own_sabotage`, `test_prior_declarations_are_frozen_and_no_check_is_reclaimed` and `test_row_parser_accepts_only_declared_units_and_one_letter_suffix` with `CUT26`/`cut-26` substituted, and the parser's refused rows as `("", "D2", "D1-", "D1a", "D1-A", "D1-1", "D1-aa", "D1-a-b")`. In `test_the_freeze_commit_and_sections_two_through_seven_are_pinned`, the three content assertions become:

```python
    assert "**1 declaration unit**" in current
    assert "One guarantee row is read, **1 full/closed** (D1)" in current
    assert '("cut25_acceptance.py",)' in current
```

and `_frozen_body` slices from `## 2. The boundary` to `\n## 8.` as cut 25's does (cut 26 has no §8 at the freeze, so the slice runs to the end).

`python/tools/cut26_acceptance.py`: copy `cut25_acceptance.py`, with `cut=26`, `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut26-acceptance"`, `PREFIX_RUNNERS = ("cut25_acceptance.py",)`, `PHASE_MODULES = ("test_n2_cut26.py",)`, and `declared_accounting` importing from `n2_arms_cut26`. Add `('("cut25_acceptance.py",)')` to the cut document's §5 as the runner-chain sentence: "The runner `python/tools/cut26_acceptance.py` chains `PREFIX_RUNNERS = ("cut25_acceptance.py",)` and runs `test_n2_cut26.py`."

- [ ] **Step 6: Freeze**

Set the cut document's status line to `**Status:** frozen 2026-09-12 at the commit named by test_n2_cut26.py; discharge pending.` Commit the document, declaration, shim, guard (with the two placeholders still in place), runner and the `test_n2`/`test_arm_staleness` edits:

```bash
tasks check
git add docs/designs/2026-09-12-conformance-cut-26.md python/tests/n2_arms_cut26.py python/tests/acceptance/n2_arms_cut26.py python/tests/acceptance/test_n2_cut26.py python/tools/cut26_acceptance.py python/tests/test_n2.py python/tests/test_arm_staleness.py
git commit -m "test(cut26): freeze D1's declaration; the negative joins the portable inventory"
git rev-parse HEAD
git show HEAD:docs/designs/2026-09-12-conformance-cut-26.md | sha256sum
```

Also `sha256sum python/tests/n2_arms_cut26.py` for the declaration's digest. Fill `CUT26_FREEZE_COMMIT` with the full sha, `CUT26_FROZEN_SHA256` with the document digest and `CUT26_DECLARATION_SHA256` with the declaration digest, then:

```bash
git add python/tests/acceptance/test_n2_cut26.py
git commit -m "test(cut26): pin the freeze commit, the body digest and the declaration digest"
```

- [ ] **Step 7: Run the guard and the frozen-guard gates**

```bash
cd python && uv run --frozen pytest tests/acceptance/test_n2_cut26.py tests/test_frozen_guards.py tests/test_arm_staleness.py -v
```

Expected: PASS. `test_frozen_guards` sees the new guard as live through the runner chain and checks every pin it carries.

---

### Task 6: Discharge, results, ledger and roadmap

**Files:**
- Create: `docs/plans/2026-09-12-conformance-cut-26-results.md`
- Modify: `docs/designs/2026-09-12-conformance-cut-26.md` (status line)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md:52-53`, `:139`, `:153`, `:172`, `:188`, `:232`
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md:51-55`, `:71`, `:134`, `:190`, `:244`, `:279`
- Modify: `docs/designs/2026-08-04-domain-extension-boundary-design.md:857-861` (status note)

- [ ] **Step 1: Run the serial gate on the certified tuple, then the runner**

```bash
just test 2>&1 | tail -3
cd python && uv run --frozen python tools/cut26_acceptance.py 2>&1 | tail -20
```

Expected: `just test` green (the serial suite includes `test_n2.py`, hence both D1 arms); the runner prints cut 26's accounting (2 arms, 1 unit, 1 row) and exit 0. Record the `nodes` commit the run resolved: `git -C "$(dirname "$(dirname "$(dirname "$(uv run --frozen python -c 'from n2_arms import installed_nodes_root;print(installed_nodes_root())' 2>/dev/null || echo /mnt/ssd/Dropbox/nodes/python/src/nodes)')")")" rev-parse --short HEAD` — or simply `git -C /mnt/ssd/Dropbox/nodes rev-parse --short HEAD` locally.

- [ ] **Step 2: Write the results**

`docs/plans/2026-09-12-conformance-cut-26-results.md`, in cut 24's shape:

```markdown
# Conformance cut 26 — results

Frozen at `<CUT26_FREEZE_COMMIT>`; discharged 2026-09-12 against `nodes` `<sha>`.

## 1. What ran

`just test` on the certified tuple: `<N> passed in <T>s`, including `test_n2.py`'s
portable audit of `PORTABLE_ARMS` (cuts 1–3 and 26). `python/tools/cut26_acceptance.py`
after cut 25's chain: `test_n2_cut26.py` <n> passed; D1-a and D1-b both `sound`; the
baseline `resolved`. The installed `nodes` tree was byte-identical before and after.

## 2. Accounting and disposition

Cut 26 reads one guarantee row: **1 full/closed** (D1). One declaration unit, two arms.
The global corpus has **148 of 195 rows closed, 47 open**. `domain-boundary` closes.

- **D1 closes.** Cut 20's inspection arm re-cited; the invariance check selected; the
  negative discharged as two `nodes`-package sabotages the check refuses.

## 3. Corrections and deviations from the frozen cut

None. (Or list each, with the reason and the commit.)

## 4. Remaining boundary

`domain-boundary` has no open row. The next on-path boundary is `world-resolution`
slice 3.
```

- [ ] **Step 3: Move the status lines**

- Cut document status: `**Status:** frozen and discharged 2026-09-12. D1 is closed.`
- Ledger line 52–53: "Implemented through conformance cut 26." and add "cut 26 records discharge in `../plans/2026-09-12-conformance-cut-26-results.md`".
- Ledger 139: replace "cut 22 closes D6 while D1 stays partial" with "cut 22 closes D6; cut 26 closes D1's cross-repository negative".
- Ledger 153: "D1 remains partial" → "D1 closes at cut 26".
- Ledger 172: "147 of 195" → "148 of 195".
- Ledger 188: the `domain-boundary` row → `| \`domain-boundary\` | closed at cut 26 (D1's cross-repository negative; slices 1 and 2 at cuts 20 and 22) | \`2026-08-04-domain-extension-boundary-design.md\` | — |`.
- Ledger 232: "only D1's cross-repository negative remains" → "D1's cross-repository negative closed at cut 26".
- Roadmap 51: "147 of 195 rows closed, with 48 open" → "148 of 195 rows closed, with 47 open"; 54–55: delete "`domain-boundary` retains D1's cross-repository negative."; 71: delete the `domain-boundary` row; 134: the `domain` lane row → "closed 2026-09-12 at cut 26"; 190: delete the row; 244: "Closed 148 of 195; open 47."; 279: delete the D1 row.
- Domain-boundary design status note (line 857–861): append "Cut 26 (2026-09-12) discharges D1's cross-repository negative; D1 is in full."

- [ ] **Step 4: Grep for drift, check, commit, close**

```bash
grep -rn "D1 remains partial\|D1 stays partial\|147 of 195" docs README.md AGENTS.md | grep -v "cut-2[0-5]"
tasks done beliefs-928881 "cut 26 frozen and discharged: D1 in full through the namespace-renaming invariance and two nodes-package sabotages under N2; domain-boundary closed"
tasks check
git add -A docs tasks
git commit -m "docs(cut26): discharge D1's cross-repository negative; domain-boundary closes"
```

Expected: the grep prints only lines inside frozen cut documents (cuts 20–25), which stay as written. Then `superpowers:finishing-a-development-branch` for the merge to `main`.

---

## Self-review

- **Spec coverage.** §2 decisions → Tasks 3 (invariance), 4 (package-aware N2), 5 (portable inventory), 1 (nodes gate, read-only checkout). §3 property clauses 1–4 → Task 3's four assertion groups; kernel-only invariants → `_registry`; sorted diagnostics → `_rename_violations`/`_sorted`; non-empty fixtures → `missing-required`, `unexpected`, and the two explicit non-emptiness asserts. §4.1 → Task 3. §4.2 → Task 4 (field, roots, copy, PYTHONPATH, staleness, three self-tests). §4.3 → Task 5 (declaration, shim, `PORTABLE_ARMS` in both consumers and the staleness gate, guard). §4.4 → Task 1. §4.5 → Tasks 2, 5 Step 6, 6. §5 → Task 3 Step 3 (red by hand), Task 4 self-tests, Task 6 Step 1. §6 sequence → task order. §7 → Task 2's out-of-scope paragraph.
- **Placeholders.** `<NODES_GATE_COMMIT>`, `<CUT26_FREEZE_COMMIT>`, `<CUT26_FROZEN_SHA256>`, `<sha>`, `<N>`, `<T>`, `<n>` are values produced by earlier steps and named there; each step that fills one says which command prints it.
- **Type consistency.** `Sabotage(package=, module=, before=, after=)` everywhere; `installed_nodes_root()` from `n2_arms` in Tasks 4 and 5; `TreeReader` is the one reader type in `arm_staleness` (`working_tree`, `historical_tree`, `audited_tree`, `stale_arms`) and its default `package` keeps the one-argument calls in `test_arm_staleness` valid; `PORTABLE_ARMS` in `test_n2` and imported by `test_arm_staleness`; the check id string is identical in Tasks 3, 4 (`NODES_CHECK`) and 5 (`UNIT_CHECKS["D1"]`).
