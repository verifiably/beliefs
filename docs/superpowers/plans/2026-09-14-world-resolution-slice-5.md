# World Resolution Slice 5 Implementation Plan

**Status:** draft, awaiting review.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derive every `dataset` record's id from its declared content identity, hold every admitted dataset to that address at the write boundary and at both inputs of `consolidate`, and discharge the work as conformance cut 29.

**Architecture:** `dataset.dataset_address` (the ruled fold, unchanged) becomes the one source of a dataset's id: `stored.dataset_node` loses its slug and derives the id, `stored.dataset_address_of` reads the address back from a stored record, `_refuse_dataset_basis` gains a second clause raising `DatasetAddressDisagreement`, and `relocation.consolidate` validates both inputs before reconciling. No seam, history or redirect set — a re-held dataset is a new entity. The bulk of the work is the measured test migration, driven by one seed-based fixture helper so a fixture can name a dataset's address before building it.

**Tech Stack:** Python 3.13, `uv`, pytest, pyright, ruff; `nodes` (the record substrate) and `atoms` (the executor); the repo's N2 sabotage audit (`tests/n2_arms.py`, `tests/test_n2.py`) and cut runners (`tools/acceptance_runner.py`).

**Spec:** `docs/superpowers/specs/2026-09-14-world-resolution-slice-5-design.md` — every task cites its section. Read the spec first; the plan argues from it.

## Global Constraints

- Run everything from `python/` with the project venv: `uv run --frozen pytest ...` and `uv run --frozen pyright`; system python lacks `beliefs`.
- Pytest count claims need the summary line: do not pass `-q` (addopts already sets it); read the final `N passed` line. Do not pipe through `tail` without `pipefail`.
- The cut freezes **before** its code exists (roadmap concurrency rules; spec §8.5): Task 1 writes and commits the cut document first, and its §§2–7 are never edited afterwards.
- Frozen files — `n2_arms_cut*.py` of cuts ≤ 28, cut documents of cuts ≤ 28, `python/tests/cited_not_run.py`'s existing entries — are never edited. Live phase modules of earlier cuts receive only the documented fixture migration (Task 4). A displaced frozen line gets a **dated live adapter** in its guard's `_LIVE_SABOTAGES` (the cut 16 and cut 7 precedent), never an edit to the declaration.
- Decision 3 of the spec: the first clause of `_refuse_dataset_basis` — the line `if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:` — and the two call lines `self._refuse_dataset_basis(node)` stay byte-identical. Cut 4's W3 arms and cut 25's `before` strings match them.
- `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py` must pass after every task that touches `stored.py`, `corpus.py`, `relocation.py`, `world/epoch.py`'s guard or any `test_n2_cut*.py`: run it in Tasks 3, 4, 5, 7.
- The closeout gate is the root-level `just check` and `just test` (from the repository root), then the cut 29 runner on the certified volume. Per-task pytest invocations are feedback, not the gate.
- Conventional commits; no AI-attribution trailer (the pre-commit hook refuses one).
- N2 rows are `<unit>-<letter>` (`W2-a`, `W8-c`); cut 29's `unit_of` parses exactly that.
- Paths in this plan are relative to the repository root; the worktree is `.worktrees/world-resolution-slice-5/`. When reporting a path to the user, prefix it with the worktree directory.
- Never `git stash`; read the main checkout without changing it when a baseline is needed.
- `tasks start <id>` before each task, `tasks done <id> "<what landed>"` in the task's final commit; `tasks check` before every commit.

---

## File map

| file | responsibility |
|---|---|
| `python/tests/dataset_fixtures.py` (new) | `digest_for(seed)`, `pinned(seed)`, `dataset_ref(seed)`, `pinned_for(ref)`, `dataset(seed, ...)` — the migration's instrument (spec §8.2) |
| `python/src/beliefs/errors.py` | `DatasetAddressDisagreement(WriteRefused)` beside `SourceAddressDisagreement` (spec §7) |
| `python/src/beliefs/stored.py` | `dataset_node` (new signature, derives the id), `dataset_address_of` (spec §3, §4) |
| `python/src/beliefs/corpus.py` | `_refuse_dataset_basis` clause 2 (spec §5) |
| `python/src/beliefs/relocation.py` | `consolidate` validates both dataset inputs before `_reconcile` (spec §2 item 4, §5) |
| `python/tools/reproduction/hold.py`, `concepts.py` | drop the slug argument (spec §6) |
| `python/tests/acceptance/durable_fixture.py`, `verification_fixtures.py`, `fixtures_cut3.py` | fixture references derived through `dataset_ref` (spec §8.2) |
| the 50 test files calling `dataset_node(` | the §8.2 migration |
| `python/tests/acceptance/test_n2_cut7.py` | dated live adapter for the X9 interposed write (spec §8.6) |
| `python/tests/acceptance/test_dataset_address_acceptance.py` (new) | W2, W3, W8 dataset arms on the certified volume (spec §8.3) |
| `python/tests/acceptance/n2_arms_cut29.py`, `test_n2_cut29.py`, `python/tools/cut29_acceptance.py` (new) | declaration, guard, runner (spec §8.4, §8.5) |
| `docs/designs/2026-09-14-conformance-cut-29.md` (new) | the frozen cut |
| `docs/plans/2026-09-14-conformance-cut-29-results.md` (new) | the discharge record |
| `README.md`, `python/tests/test_designs_corpus.py`, the guide, the ledger, the roadmap, `python/tools/roadmap_status.py`, world design §4.2, slice 2b §12 | navigation, accounting, dated notes (spec §9) |

---

### Task 1: Freeze conformance cut 29

**Files:**
- Create: `docs/designs/2026-09-14-conformance-cut-29.md`
- Modify: `README.md:30-32` (the design count and date range), `README.md:98` (the design table), `python/tests/test_designs_corpus.py:252-300` (`_COUNT_WORDS`), `docs/guide/identity-world-and-change.md:24`, `docs/guide/contracts-and-adoption.md:43` (the design-link lists)

**Interfaces:**
- Produces: the freeze commit's full sha and the document's `sha256sum`, recorded in the task note; Task 7's guard pins both.

- [ ] **Step 1: Write the cut document**

`docs/designs/2026-09-14-conformance-cut-29.md`, on cut 28's section shape. Every sentence below is what the guard (Task 7) and the results record (Task 9) quote, so keep the quoted accounting strings exact.

```markdown
# Conformance cut 29 — dataset addresses derived from the content identity

**Status:** frozen 2026-09-14; not yet discharged.
**Frozen:** 2026-09-14, before implementation, on `design/world-resolution-slice-5`
**Design:** `../superpowers/specs/2026-09-14-world-resolution-slice-5-design.md`, approved 2026-09-14 after one review (§12 there)
**Numbered after** cut 28 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The baseline below describes `main` at `fb1dac1` before implementation.

A dataset's address is ruled (admission ramp §6.2) and computed
(`dataset.dataset_address`), and seven kernel modules read it from a stored
declaration — the belief-input closure, the observed-facet ledger, produced
dataset minting, run-input admission. What has never existed is the check:
`stored.dataset_node(slug, ...)` mints `dataset:<slug>` from an authored
handle, and the write boundary refuses a dataset with *no* content identity
(W3, cut 4) while never comparing the id it has with the address its
declaration derives. Slice 2b closed the same gap for `source` at cut 25 and
filed this half.

This cut removes the slug from the dataset builder, adds
`stored.dataset_address_of`, holds every admitted dataset to its derived
address at the write boundary (`DatasetAddressDisagreement`) and at both
inputs of `consolidate`, and migrates the test corpus to derived addresses.
The address form is unchanged: `dataset:sha256:<fold>` as ruled. No seam,
history or redirect set is built: a re-held dataset is a new entity (world
design §4.4).

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-14-conformance-cut-29.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/errors.py`: `DatasetAddressDisagreement`;
- `python/src/beliefs/stored.py`: `dataset_node` without its slug, `dataset_address_of`;
- `python/src/beliefs/corpus.py`: `_refuse_dataset_basis`'s second clause;
- `python/src/beliefs/relocation.py`: `consolidate`'s dataset input validation;
- `python/tools/reproduction/hold.py` and `concepts.py`: the slug argument removed;
- `python/tests/dataset_fixtures.py` and the test corpus's `dataset_node` sites, closure fixtures and `dataset:` literals: the §8.2 migration of the design;
- `python/tests/acceptance/test_n2_cut7.py`: the dated live adapter for the X9 interposed write;
- `python/tests/acceptance/test_dataset_address_acceptance.py`, `python/tests/acceptance/n2_arms_cut29.py` and `python/tests/acceptance/test_n2_cut29.py`: durable arms, declarations and guard;
- `python/tests/test_designs_corpus.py`: the design-count guard;
- `python/tools/cut29_acceptance.py` and `python/tools/roadmap_status.py`: runner and accounting;
- `docs/designs/2026-08-02-world-addressing-design.md`: a dated note on the §4.2 dataset row;
- `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md`: a dated §12 note;
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/glossary.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/foundations.md`, `README.md` and the cut 29 results record: discharge and navigation.

Out of scope:

- `dataset.py`: the fold is the ruling and is not touched;
- a `corpus_check` or world-audit finding for a handle-addressed dataset in a corpus written outside the boundary (design §11 item 1);
- `beliefs-24b42b`, divergent correction-history reconciliation: the lane's next boundary, not a prerequisite;
- the seven modules that already compute the address from a declaration (`closure.py`, `evaluation.py`, `facet_read.py`, `production.py`, `admission.py`, `belief.py`, `corpus.py`'s readers): read and not rewritten;
- the mm30 reproduction record: its records already sit at derived addresses; no new measurement.

## 3. Selection

### W2 — closed at cut 25, re-read on its dataset arm
Two writers in two corpora build a dataset from one declaration under different titles and observation attesters and mint one address; resource order, repetition and names give the same address and one changed digest gives a different one; the world's producers map and a run's `observes` closure name the derived address; a declaration under an unaccepted algorithm refuses `BasisMissing` at the builder and again at the boundary for a hand-built record; `dataset_address_of` reads the stored declaration and agrees with the fold. Selected: unit `W2`. **Deferred:** nothing.

### W3 — closed at cut 4, re-read on its builder arm
`dataset_node` with an empty or unpinned declaration refuses `BasisMissing` before any write; a declared-not-held dataset is minted (the narrowed arm, unchanged); the boundary's own refusal of a hand-built unpinned record still runs and still fails when its guard is removed. Selected: unit `W3`. **Deferred:** nothing.

### W8 — part, the address-conflict conflict on datasets
A hand-built dataset at a handle address refuses `DatasetAddressDisagreement` on `add`, on `import_bundle` naming the member, and on `move` into a governed destination; the same bytes at the derived address are admitted; `consolidate` of two records at one derived address gives one address and no redirect; `consolidate` of a valid survivor with a raw record at the same id carrying different digests refuses `DatasetAddressDisagreement` naming `other` before anything is written, the invalid record is still present in its corpus afterwards, and swapping `keep` names `keep`. Selected: unit `W8`. **Deferred:** the ambiguous-search-term conflict, which needs the pinned authority snapshot (ledger artifact 11) and is W9's arm restated (`authority-labels`) — unchanged from cut 28.

### Boundary invariants
The fold (`dataset.py`) is byte-unchanged; the first clause of `_refuse_dataset_basis` and its two call lines are byte-unchanged; no referrer is rewritten; no address is retired; `revise` still preserves the `dataset` facet; the mm30 corpus's recorded dataset addresses are what the builder now derives.

## 4. Accounting

Three guarantee rows are read, **0 full/closed** newly (W2 and W3 are re-read on dataset arms and keep their closed status; W8 stays partial on its ambiguous-search-term conflict), and **3 declaration units** carry them: `W2`, `W3`, `W8`. `world-resolution` then retains one filed follow-up, `beliefs-24b42b`.

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the three units `W2`, `W3` and `W8`, each single-homed to the test that exercises it.
2. Every durable arm runs on the certified volume. Capability refusal is an error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut28_acceptance.py",)` and `PHASE_MODULES = ("test_dataset_address_acceptance.py", "test_n2_cut29.py")`.
4. The 6 declared arms cover every sabotage site: in `stored.py` (the builder deriving the id from the title instead of the declaration; the builder minting through a `None` address; `dataset_address_of` answering `node.id` instead of the stored declaration), in `corpus.py` (the id/derived-address agreement dropped on `add`; the import loop skipping datasets), and in `relocation.py` (`consolidate` validating the survivor only).
5. `test_n2_cut29.py` audits them by the cut-28 pattern with the staleness probe's baseline taken from the tree; cut 7's guard carries a dated live adapter for the X9 interposed write and every other live matcher still applies exactly once.
6. Prior declarations remain frozen and no check is reclaimed.
7. This document and its declaration inventory are pinned by digest before discharge.

The sites in item 4 count three in `stored.py`, two in `corpus.py` and one in `relocation.py`: **6 arms**.

## 6. Second reader

The spec's one review pass on 2026-09-14 resolved two findings (§12 there): consolidation now validates both inputs, and the boundary's existing `BasisMissing` checks migrate to hand-built records so the builder's refusal cannot satisfy them. The user approved the spec and the freeze on 2026-09-14.

## 7. Limitations

1. Boundary-only: a corpus written outside the write boundary can hold a dataset at a handle address unreported (design §11 item 1).
2. One record per byte set: a second observer of the same bytes edits through `revise` (design §11 item 2).
3. The accepted-algorithm set is still `{"sha256"}` (design §11 item 3).
4. W8's search-term conflict is unrun and stays with `authority-labels`.
```

- [ ] **Step 2: The design-count guard and the navigation lists**

`README.md` line 30: `Sixty-three documents` → `Sixty-four documents`; line 32 keeps `through 2026-09-14` (the newest date is unchanged). After the cut 28 row in the README's design table (line 98) add:

```markdown
| `2026-09-14-conformance-cut-29.md` | the frozen slice 5 cut: dataset ids derived from the content identity, held at the write boundary and at both inputs of `consolidate`; W2, W3 and W8 re-read on dataset arms |
```

`python/tests/test_designs_corpus.py`: add `64: "Sixty-four",` after the `63` entry of `_COUNT_WORDS`.

`docs/guide/identity-world-and-change.md` line 24 and `docs/guide/contracts-and-adoption.md` line 43: after the `2026-09-14-conformance-cut-28.md` entry add `  - ../designs/2026-09-14-conformance-cut-29.md`.

- [ ] **Step 3: Verify the guard**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py`
Expected: the final line reads `N passed` with no failures (the count test now reads "Sixty-four documents" and the newest date `2026-09-14`).

- [ ] **Step 4: Freeze**

```bash
tasks check
git add docs/designs/2026-09-14-conformance-cut-29.md README.md python/tests/test_designs_corpus.py docs/guide/identity-world-and-change.md docs/guide/contracts-and-adoption.md
git commit -m "docs(cut29): freeze conformance cut 29"
git rev-parse HEAD
sha256sum docs/designs/2026-09-14-conformance-cut-29.md
tasks note beliefs-48214e "cut 29 frozen at <full sha>, document sha256 <hex>"
```

Record both values in the task note; Task 7 pins them.

---

### Task 2: The error, the reader and the fixture helper

**Files:**
- Modify: `python/src/beliefs/errors.py:1092-1096` (after `SourceAddressDisagreement`)
- Modify: `python/src/beliefs/stored.py:137` (`__all__`), `:376-381` (after `source_address_of`)
- Create: `python/tests/dataset_fixtures.py`
- Test: `python/tests/test_stored.py` (append), `python/tests/test_dataset_fixtures.py` (new)

**Interfaces:**
- Produces: `beliefs.errors.DatasetAddressDisagreement(WriteRefused)`; `stored.dataset_address_of(node: Node) -> str | None`; `dataset_fixtures.digest_for(seed: str) -> str`, `pinned(seed: str) -> list[dict[str, str]]`, `dataset_ref(seed: str) -> str`, `pinned_for(ref: str) -> list[dict[str, str]]`, `dataset(seed: str, *, title: str | None = None, **facets) -> Node` (the last one is completed in Task 3 once the builder's signature changes; in this task it calls the old builder with the seed as slug so the helper is testable now).

- [ ] **Step 1: Write the failing tests**

`python/tests/test_dataset_fixtures.py`:

```python
"""The seed-based dataset fixtures slice 5 migrates the corpus onto (design §8.2)."""

import pytest
from dataset_fixtures import dataset_ref, digest_for, pinned, pinned_for

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address


def test_a_seed_gives_one_deterministic_pinned_declaration():
    assert pinned("raw") == pinned("raw")
    assert pinned("raw") != pinned("derived")
    assert pinned("raw") == [{"name": "matrix", "digest": digest_for("raw")}]
    assert digest_for("raw").startswith("sha256:") and len(digest_for("raw")) == len("sha256:") + 64


def test_dataset_ref_is_the_fold_over_the_pinned_declaration():
    declaration = DatasetDeclaration(resources=(ResourceDeclaration(name="matrix", digest=digest_for("raw")),))
    assert dataset_ref("raw") == dataset_address(declaration)
    assert dataset_ref("raw").startswith("dataset:sha256:")


def test_pinned_for_answers_a_ref_minted_by_dataset_ref_and_refuses_a_stranger():
    ref = dataset_ref("lineage-left")
    assert pinned_for(ref) == pinned("lineage-left")
    with pytest.raises(KeyError):
        pinned_for("dataset:never-minted")
```

Append to `python/tests/test_stored.py`:

```python
def test_dataset_address_of_reads_the_stored_declaration_not_the_id():
    handle = stored.governed_node("dataset", "handle", "handle", {stored.DATASET_FACET: {"resources": PINNED}}, ())
    assert stored.dataset_address_of(handle) == dataset_address(stored.dataset_declaration(handle))
    assert stored.dataset_address_of(handle) != handle.id


def test_dataset_address_of_is_none_for_an_unpinned_record():
    unpinned = stored.governed_node("dataset", "u", "u", {stored.DATASET_FACET: {"resources": [{"name": "x"}]}}, ())
    assert stored.dataset_address_of(unpinned) is None
```

Add `from beliefs.dataset import dataset_address` to `test_stored.py`'s imports.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_dataset_fixtures.py tests/test_stored.py -k "dataset_address_of or seed or dataset_ref or pinned_for"`
Expected: FAIL — `ModuleNotFoundError: No module named 'dataset_fixtures'` and `AttributeError: module 'beliefs.stored' has no attribute 'dataset_address_of'`.

- [ ] **Step 3: The error class**

In `python/src/beliefs/errors.py`, directly after `SourceAddressDisagreement`'s docstring (line 1096):

```python
class DatasetAddressDisagreement(WriteRefused):
    """A dataset's stored id is not the address its declaration derives (slice 5
    §5). The declaration is present and pinned; the record simply lives at the
    wrong address, which is what a handle-addressed or hand-edited dataset is —
    the dataset half of `SourceAddressDisagreement`."""
```

- [ ] **Step 4: The reader**

In `python/src/beliefs/stored.py`, after `source_address_of` (line 381):

```python
def dataset_address_of(node: Node) -> str | None:
    """The address the stored declaration derives (slice 5 §3) — what the
    boundary compares `node.id` against. All-or-nothing, like the fold it
    calls: an unpinned resource gives `None`, never a partial address."""
    return dataset_address(dataset_declaration(node))
```

Add `dataset_address` to the `from beliefs.dataset import ...` line (line 61) and `"dataset_address_of",` to `__all__` beside `"dataset_declaration",`.

- [ ] **Step 5: The fixture helper**

`python/tests/dataset_fixtures.py`:

```python
"""Seed-based dataset fixtures (slice 5 design §8.2).

A dataset's id is derived from its declared content identity, so a test
can no longer name a dataset by handle and build it later. These helpers
give every seed one deterministic pinned declaration and the address that
declaration derives, so a closure recipe, a relation target or a lineage
route can name `dataset_ref("raw")` before `dataset("raw")` is built, and
the two always agree.
"""

from __future__ import annotations

from hashlib import sha256

from nodes.core.node import Node

from beliefs import stored
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

__all__ = ["dataset", "dataset_ref", "digest_for", "pinned", "pinned_for"]

_MINTED: dict[str, str] = {}


def digest_for(seed: str) -> str:
    """One deterministic sha256 digest per seed, distinct across seeds."""
    return "sha256:" + sha256(f"dataset-fixture:{seed}".encode()).hexdigest()


def pinned(seed: str) -> list[dict[str, str]]:
    """The one-resource pinned declaration for `seed`."""
    return [{"name": "matrix", "digest": digest_for(seed)}]


def dataset_ref(seed: str) -> str:
    """The address `pinned(seed)` derives — usable before the record is built."""
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="matrix", digest=digest_for(seed)),)))
    assert address is not None
    _MINTED[address] = seed
    return address


def pinned_for(ref: str) -> list[dict[str, str]]:
    """The declaration behind a ref `dataset_ref` minted; `KeyError` for any other."""
    return pinned(_MINTED[ref])


def dataset(seed: str, *, title: str | None = None, **facets) -> Node:
    """A dataset record at `dataset_ref(seed)`: `title` defaults to the seed;
    `facets` are the builder's keyword facets (`empirical_observation`,
    `basis`, `domain_facets`)."""
    dataset_ref(seed)
    return stored.dataset_node(seed, title=seed if title is None else title, resources=pinned(seed), **facets)
```

(The `seed` positional argument to `dataset_node` is the current builder's slug; Task 3 removes it. Until then `dataset(seed).id` is `dataset:<seed>`, which is fine for this task's tests, which do not build.)

- [ ] **Step 6: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_dataset_fixtures.py tests/test_stored.py`
Expected: the final line reads `N passed`.

- [ ] **Step 7: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
tasks check
git add python/src/beliefs/errors.py python/src/beliefs/stored.py python/tests/dataset_fixtures.py python/tests/test_dataset_fixtures.py python/tests/test_stored.py
git commit -m "feat(stored): read a dataset's derived address from its stored declaration"
```

---

### Task 3: The builder derives the id; migrate the unit-test corpus

**Files:**
- Modify: `python/src/beliefs/stored.py:880-901` (`dataset_node`)
- Modify: `python/tests/dataset_fixtures.py` (`dataset` drops the seed positional)
- Modify: `python/tests/fixtures_cut3.py:204` (`closure_with` dataset defaults), `python/tests/verification_fixtures.py:42,104-113`, `python/tests/test_corpus_write.py:302-305`, `python/tests/test_read_side.py:252`, `python/tests/test_audit.py:87-100`, `python/tests/test_stored.py:11-12`, `python/tests/domain_facet_fixtures.py`, and every other non-acceptance test file calling `dataset_node(` (the list in Step 4)
- Test: `python/tests/test_stored.py` (append), then `tests` without acceptance

**Interfaces:**
- Consumes: `dataset_fixtures.pinned`, `dataset_ref`, `pinned_for`, `dataset` (Task 2).
- Produces: `stored.dataset_node(*, title: str, resources: Sequence[Mapping[str, Any]], empirical_observation=None, basis=None, domain_facets=None) -> Node` — no `slug`, `resources` required, id `dataset:sha256:<fold>`; refuses `BasisMissing` when the declaration has no address.

- [ ] **Step 1: Write the failing builder tests**

Append to `python/tests/test_stored.py`:

```python
from dataset_fixtures import dataset_ref, pinned

from beliefs.errors import BasisMissing


class TestTheDatasetBuilder:
    def test_it_derives_the_id_from_the_declaration(self):
        node = stored.dataset_node(title="DepMap 24Q2", resources=pinned("depmap"))
        assert node.id == dataset_ref("depmap") == stored.dataset_address_of(node)
        assert node.facets[stored.DATASET_FACET] == {"resources": pinned("depmap")}

    def test_one_byte_set_is_one_id_whatever_the_title_order_repetition_or_names(self):
        a = pinned("a")[0]
        b = pinned("b")[0]
        one = stored.dataset_node(title="first", resources=[a, b])
        two = stored.dataset_node(title="second", resources=[b, a, {"name": "copy", "digest": a["digest"]}])
        assert one.id == two.id
        assert stored.dataset_node(title="x", resources=[a]).id != one.id

    def test_an_unpinned_or_empty_declaration_refuses_at_the_builder(self):
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="DepMap", resources=[])
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="DepMap", resources=[*pinned("p"), {"name": "unpinned"}])
        with pytest.raises(BasisMissing):
            stored.dataset_node(title="md5", resources=[{"name": "m", "digest": "md5:" + "0" * 32}])

    def test_the_slug_parameter_is_gone(self):
        with pytest.raises(TypeError):
            stored.dataset_node("slug", title="t", resources=pinned("s"))  # type: ignore[misc]
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_stored.py -k TheDatasetBuilder`
Expected: FAIL — `TypeError: dataset_node() missing 1 required positional argument: 'slug'` on the first three; the fourth fails because the old builder accepts the slug.

- [ ] **Step 3: Replace the builder**

In `python/src/beliefs/stored.py` replace `dataset_node` (lines 880–901) with:

```python
def dataset_node(
    *,
    title: str,
    resources: Sequence[Mapping[str, Any]],
    empirical_observation: Mapping[str, Any] | None = None,
    basis: Mapping[str, Any] | None = None,
    domain_facets: Mapping[str, Mapping[str, Any]] | None = None,
) -> Node:
    """A dataset at its content-derived address (slice 5 §4): the id is the
    ruled fold over the declared digests, never a handle. Refuses a
    declaration with no content identity itself, since no id exists without
    one; the boundary refuses it again for hand-built records."""
    facets: dict[str, Any] = {DATASET_FACET: {"resources": [dict(resource) for resource in resources]}}
    if empirical_observation is not None:
        facets[EMPIRICAL_OBSERVATION_FACET] = dict(empirical_observation)
    if basis is not None:
        facets[LINEAGE_BASIS_FACET] = dict(basis)
    for key, payload in (domain_facets or {}).items():
        if "/" not in key:
            raise MalformedRecord(
                f"{key!r} is not a namespaced facet key; a domain facet is `<namespace>/<name>` (F §3.3), and a base "
                "facet has its own parameter"
            )
        facets[key] = dict(payload)
    address = dataset_address(_declaration_of(facets[DATASET_FACET]))
    if address is None:
        raise BasisMissing(
            "a dataset carries a content identity — every declared resource pinned by an accepted digest; "
            "a curation note is its own explicit add, and supplying the basis later is a second, separate mint"
        )
    return _node("dataset", address.partition(":")[2], title, facets, ())
```

Factor the projection `dataset_declaration` already performs into a helper the reader and the builder share, so the builder derives from exactly what the reader will read back:

```python
def _declaration_of(facet: Mapping[str, Any]) -> DatasetDeclaration:
    resources = facet.get("resources")
    if not isinstance(resources, list):
        return DatasetDeclaration(resources=())
    declared: list[ResourceDeclaration] = []
    for entry in resources:
        if not isinstance(entry, dict):
            raise MalformedRecord("a declared resource is not an object")
        digest = entry.get("digest")
        declared.append(ResourceDeclaration(name=str(entry.get("name", "")), digest=digest if isinstance(digest, str) else None))
    return DatasetDeclaration(resources=tuple(declared))
```

and make `dataset_declaration(node)` call it: `return _declaration_of(_facet(node, DATASET_FACET) or {})`, keeping its docstring and its `MalformedRecord` message prefixed with `node.id` by catching and re-raising (`except MalformedRecord as caught: raise MalformedRecord(f"{node.id}: {caught}") from caught`).

In `python/tests/dataset_fixtures.py` the `dataset` helper becomes:

```python
def dataset(seed: str, *, title: str | None = None, **facets) -> Node:
    dataset_ref(seed)
    return stored.dataset_node(title=seed if title is None else title, resources=pinned(seed), **facets)
```

- [ ] **Step 4: Migrate the non-acceptance test files**

The files (from `grep -rl "dataset_node(" python/tests --include='*.py' | grep -v /acceptance/`): `test_read_side.py`, `test_world_view.py`, `test_coreference_attestation.py`, `test_audit.py`, `test_world_selection.py`, `test_relocation_rows.py`, `test_holdings_capture.py`, `test_deletion_rows.py`, `test_corpus_write.py`, `test_acquisition.py`, `test_world_read.py`, `test_world_build.py`, `test_retract.py`, `test_facet_read.py`, `test_facet_seams.py`, `test_dataset_revision.py`, `test_world_receipts.py`, `test_world_epoch.py`, `test_relocation.py`, `test_permit_entry_points.py`, `test_import_bundle.py`, `test_identifier_correction.py`, `test_guarded_publication.py`, `test_evaluation.py`, `domain_facet_fixtures.py`, `verification_fixtures.py`, `test_world_relabels.py`, `test_world_audit.py`, `test_stored.py`, `test_profile_agreement.py`, `test_local_standing.py`, `test_holdings_windows.py`, `test_holdings_receipt.py`, `n2_arms_cut7.py` (**frozen — do not edit**; its site is a declaration string, handled in Task 4).

Two mechanical passes from `python/`, title-only sites first so the general pass cannot swallow them:

```bash
FILES=$(grep -rl "dataset_node(" tests --include='*.py' | grep -v /acceptance/ | grep -v n2_arms_cut7.py)
# title-only sites: dataset_node("a", title="a") -> dataset_node(title="a", resources=pinned("a"))
sed -i -E 's/dataset_node\("([^"]*)",\s*title=("[^"]*")\)/dataset_node(title=\2, resources=pinned("\1"))/g' $FILES
# every remaining site: drop the slug
sed -i -E 's/dataset_node\("[^"]*",\s*title=/dataset_node(title=/g' $FILES
# multi-line calls keep the slug on its own line; this lists them for deletion by hand
grep -rn -A1 "dataset_node($" $FILES | grep -E '^\S+-\s+(f?"[^"]*"|[a-z_.()]+),$'
```

Add `from dataset_fixtures import dataset, dataset_ref, pinned, pinned_for` (only the names used) to each file the sed touched.

Then the manual pass, file by file:

1. **Every `"dataset:<handle>"` literal that named a built dataset** becomes the built node's `.id` or `dataset_ref("<handle>")`. Where a fixture names the dataset *before* building it (closure recipes, `run_node(observes=[...])`, lineage routes, relation targets), use `dataset_ref("<handle>")` and build the record with `pinned("<handle>")` or `dataset("<handle>")`. Where the record is built first, bind it and use `.id`. Literals naming a dataset that is deliberately *absent* (`dataset:absent`, `dataset:gone`, `dataset:elsewhere`) stay as they are — an unresolvable ref is what they assert.
2. **Sites that gave several records one shared constant** (`PINNED`, `"sha256:" + "1" * 64`, …) give each record its own seed unless the test is about one byte set in two places — W16's consolidation (`test_relocation_rows.py::_duplicate_datasets`, both records at `"d" * 64`), R23's negative (a), the revision tests (`test_dataset_revision.py`, one record revised) — where the shared constant is the point and stays.
3. **`fixtures_cut3.py::closure_with`**: every `"dataset:<x>"` default in its recipe inputs becomes `dataset_ref("<x>")`, so every closure built from it names derived addresses; the `content` component of each `RecipeInput` is unchanged.
4. **`verification_fixtures.py`**: `PINNED` is deleted; `mint_datasets` builds each input as `stored.dataset_node(title="raw", resources=pinned_for(entry.dataset), empirical_observation={...})`. **`test_audit.py::add_observed_datasets`** likewise. **`test_corpus_write.py::observed_dataset(slug="raw")`** and **`test_read_side.py::observed_dataset(slug="raw")`** become `observed_dataset(seed="raw")` returning `stored.dataset_node(title=seed, resources=pinned(seed), empirical_observation=...)`; callers that compared against `"dataset:raw"` compare against `dataset_ref("raw")`. **`test_stored.py::_dataset(slug, basis=None)`** becomes `_dataset(seed, basis=None)` over `pinned(seed)`, and `_route(identity)`'s `"ancestor": f"dataset:{identity}"` / `"transforms": [f"dataset:{identity}"]` become `dataset_ref(identity)`.
5. **`test_world_selection.py::topic_nodes`**: `d_a = dataset("d-a")`, `d_b = dataset("d-b")` (the acceptance module's empty-resources patch loop in `test_world_selection_acceptance.py` is removed in Task 4).
6. **The three boundary tests that reach `BasisMissing` through the builder are NOT de-slugged into passing** — `test_corpus_write.py::TestW3TheBasisRefusal::test_a_dataset_with_no_content_identity_refuses`, `::test_a_dataset_with_one_unpinned_resource_refuses`, and `::test_the_basis_check_refuses_before_eligibility` (lines 533–540 and 645–653) build the record by hand so the boundary is what refuses:

```python
    def test_a_dataset_with_no_content_identity_refuses(self, writer):
        # Hand-built: the builder refuses this itself (TestTheDatasetBuilder), and
        # the boundary must refuse it independently (design §8.2 review finding 2).
        unpinned = stored.governed_node("dataset", "d1", "DepMap", {stored.DATASET_FACET: {"resources": []}}, ())
        with pytest.raises(BasisMissing):
            writer.add(unpinned)

    def test_a_dataset_with_one_unpinned_resource_refuses(self, writer):
        half = stored.governed_node(
            "dataset", "d1", "DepMap", {stored.DATASET_FACET: {"resources": [*pinned("d1"), {"name": "unpinned"}]}}, ()
        )
        with pytest.raises(BasisMissing):
            writer.add(half)
```

and

```python
    def test_the_basis_check_refuses_before_eligibility(self, writer):
        node = stored.governed_node("dataset", "d1", "d1", {stored.DATASET_FACET: {"resources": []}}, ())
        node.relations.append(stored.Relation(source=node.id, predicate=stored.ASSESSES, target="proposition:p1"))
        with pytest.raises(BasisMissing):
            writer.add(node)
```

   `test_a_dataset_whose_bytes_are_held_nowhere_is_minted` keeps its builder call, de-slugged, with `resources=pinned("depmap")`. (`test_durable_corpus.py`'s site is Task 4's.)

7. **`test_dataset_revision.py`** keeps one shared `PINNED` for the record under revision; where a test builds a *second* dataset it gets its own seed.
8. **Holdings tests** (`test_holdings_capture.py`, `test_holdings_windows.py`, `test_holdings_receipt.py`, `test_acquisition.py`): de-slug; where the capture or receipt names `"dataset:<x>"`, use `dataset_ref("<x>")`.

- [ ] **Step 5: Run the portable suite**

Run: `cd python && uv run --frozen pytest tests`
Expected: the final line reads `N passed` with **no failures**. Work through failures file by file; every failure is one of the manual-pass categories above. Do not touch `tests/acceptance` in this task except `durable_fixture.py`'s imports if a portable test imports it (it does not; leave it for Task 4).

- [ ] **Step 6: Staleness and frozen guards**

Run: `cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: pass. `stored.py`'s builder is matched by no frozen arm; if a guard reports a newly stale arm, stop and record which line moved before continuing.

- [ ] **Step 7: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
tasks check
git add python/src/beliefs/stored.py python/tests
git commit -m "feat(stored)!: derive dataset ids from the content identity"
```

---

### Task 4: Migrate the acceptance corpus, the frozen-cut adapters and the tools

**Files:**
- Modify: `python/tests/acceptance/durable_fixture.py:24-48,52-58,83-86,105-113,164-183`, and every acceptance module calling `dataset_node(` (`test_durable_corpus.py`, `test_world_selection_acceptance.py`, `test_relocation_acceptance.py`, `test_world_view_acceptance.py`, `test_facet_acceptance.py`, `test_world_audit_acceptance.py`, `test_durable_traversal.py`, `test_source_address_acceptance.py`, `test_coreference_acceptance.py`, `test_n2_cut7.py`, `test_n2_cut5.py`, `test_cut15_lineage.py`, `test_session_acceptance.py`, `test_durable_records.py`, `test_deletion_acceptance.py`)
- Modify: `python/tests/acceptance/test_n2_cut7.py:95-135,1011-1050` (the X9 live adapter)
- Modify: `python/tools/reproduction/hold.py:38-48`, `python/tools/reproduction/concepts.py:43-55`
- Modify: `python/tests/test_domain_boundary.py:40,115,132` only if the fixture crosses the boundary (Step 5)

**Interfaces:**
- Consumes: `dataset_fixtures` (Task 2), the new builder (Task 3).
- Produces: `durable_fixture.RAW`, `DERIVED`, `LINEAGE_*` as derived addresses; `durable_fixture.pinned()` retained; `test_n2_cut7.LIVE_INTERPOSED_WRITE`.

- [ ] **Step 1: `durable_fixture.py`**

Replace the dataset constants (lines 24–25, 40–48) with seed-derived addresses:

```python
from dataset_fixtures import dataset_ref, pinned as pinned_for_seed

RAW = dataset_ref("raw")
DERIVED = dataset_ref("derived")
...
LINEAGE_ROOT = dataset_ref("lineage-root")
LINEAGE_MIDDLE = dataset_ref("lineage-middle")
LINEAGE_LEAF = dataset_ref("lineage-leaf")
LINEAGE_LEFT = dataset_ref("lineage-left")
LINEAGE_RIGHT = dataset_ref("lineage-right")
LINEAGE_CONFLICT = dataset_ref("lineage-conflict")
LINEAGE_ABSENT_ANCESTOR = dataset_ref("lineage-absent-ancestor")
LINEAGE_ABSENT_RUN = dataset_ref("lineage-absent-run")
LINEAGE_CYCLE = (dataset_ref("lineage-cycle-a"), dataset_ref("lineage-cycle-b"))
```

Keep the no-argument `pinned()` iterator: four acceptance modules import it for records whose address they never name in advance. `observed_dataset` and `mint_lineage_fixture`'s inner `dataset` become seed-based:

```python
def observed_dataset(seed: str = "raw"):
    return stored.dataset_node(
        title=seed, resources=pinned_for_seed(seed), empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}
    )
```

```python
    def dataset(seed: str, stamped=None):
        return stored.dataset_node(title=seed, resources=pinned_for_seed(seed), basis=stamped)

    writer.add(dataset("lineage-root"))
    writer.add(dataset("lineage-middle", basis(route(RUN, LINEAGE_ROOT))))
    ...
```

`mint_records`' `DERIVED` record: `stored.dataset_node(title="derived", resources=pinned_for_seed("derived"), basis=basis(route(RUN, RAW, [RAW])))`. Every route and relation keeps naming the constants, which are now the derived addresses. `slug(ref)` stays for the non-dataset kinds.

- [ ] **Step 2: The acceptance modules**

Run the same two `sed` passes as Task 3 Step 4 over `tests/acceptance` (excluding `n2_arms_cut*.py`, which are frozen), add the `dataset_fixtures` imports, then the manual pass with the same eight rules. Two module-specific items:

- `test_world_selection_acceptance.py` lines 66–69: delete the loop body that patches empty `resources` to `pinned()` and re-stamps — every dataset now arrives pinned from `topic_nodes`; keep the plain `writer.add(node)`.
- `test_durable_corpus.py::TestW3Durably::test_a_dataset_with_no_content_identity_is_refused_before_it_lands` (line 100) builds by hand, and asserts against the handle path it names:

```python
    def test_a_dataset_with_no_content_identity_is_refused_before_it_lands(self, durable_writer, durable_root):
        unpinned = stored.governed_node("dataset", "d1", "DepMap", {stored.DATASET_FACET: {"resources": []}}, ())
        with pytest.raises(BasisMissing):
            durable_writer.add(unpinned)
        assert not path_for(durable_root, "dataset:d1").exists()
```

- [ ] **Step 3: The cut 7 live adapter**

`test_n2_cut7.py` already re-targets two frozen arms by `(row, index)` (lines 99–133). The X9 relocated-head arm is index **15** in `CUT7_ARMS` (`world/epoch.py`); its frozen `after` interposes `stored.dataset_node(__import__("uuid").uuid4().hex, title="interposed")`, which the new builder refuses with `TypeError`, so the witness would fail for the wrong reason. Add, beside the existing `_LIVE_SABOTAGES` block:

```python
# Live interposed-write migration, 2026-09-14 (slice 5): `stored.dataset_node`
# derives its id and requires a pinned declaration; cut 7's declaration stays
# frozen at 8ca085e and the X9 arm interposes the same real corpus write.
LIVE_INTERPOSED_WRITE = (
    '        __import__("nodes.core.corpus", fromlist=["Corpus"]).Corpus(carrier).add(\n'
    '            stored.dataset_node(\n'
    '                title="interposed",\n'
    '                resources=[{"name": "interposed", "digest": "sha256:" + __import__("uuid").uuid4().hex * 2}],\n'
    '            )\n'
    "        )\n"
)
_X9_RELOCATED_HEAD_INDEX = 15
FROZEN_CUT7_ARMS = CUT7_ARMS
CUT7_ARMS = tuple(
    dataclasses.replace(
        arm,
        sabotage=Sabotage(
            arm.sabotage.module,
            before=arm.sabotage.before,
            after=arm.sabotage.after.replace(INTERPOSED_WRITE, LIVE_INTERPOSED_WRITE),
        ),
    )
    if index == _X9_RELOCATED_HEAD_INDEX
    else arm
    for index, arm in enumerate(CUT7_ARMS)
)
```

placed **after** the existing `CUT7_ARMS = tuple(...)` re-targeting so both adapters apply. Verify the index before pinning it: `uv run --frozen python -c "import sys; sys.path[:0]=['tests','tests/acceptance']; from n2_arms_cut7 import *; print([i for i,a in enumerate(CUT7_ARMS) if a.checks==(RELOCATED_HEAD_CHECK,)])"` prints `[15]`. Add an assertion in the module: `assert FROZEN_CUT7_ARMS[_X9_RELOCATED_HEAD_INDEX].checks == (RELOCATED_HEAD_CHECK,)`.

Then in `TestTheRelocatedHeadSabotageIsNotVacuous` (line 1011 on): `test_the_declared_mutation_carries_a_real_interposed_write` reads the **frozen** arm — change `_relocated_head_arm()` to take the tuple:

```python
def _relocated_head_arm(arms=None) -> Arm:
    (arm,) = [arm for arm in (CUT7_ARMS if arms is None else arms) if arm.checks == (RELOCATED_HEAD_CHECK,)]
    return arm
```

and in that one test call `_relocated_head_arm(FROZEN_CUT7_ARMS)`; the live tests (`test_relocation_alone_passes_the_witness_and_the_interposed_write_fails_it`) keep `_relocated_head_arm()` and replace `INTERPOSED_WRITE` with `LIVE_INTERPOSED_WRITE` in the `relocation_only` construction (`arm.sabotage.after.replace(LIVE_INTERPOSED_WRITE, "")`). Add one test:

```python
    def test_the_live_interposed_write_is_the_dated_adapter_of_the_frozen_one(self):
        frozen = _relocated_head_arm(FROZEN_CUT7_ARMS)
        live = _relocated_head_arm()
        assert frozen.sabotage.after.count(INTERPOSED_WRITE) == 1
        assert live.sabotage.after.count(LIVE_INTERPOSED_WRITE) == 1
        assert live.sabotage.after.replace(LIVE_INTERPOSED_WRITE, INTERPOSED_WRITE) == frozen.sabotage.after
        assert live.sabotage.before == frozen.sabotage.before
```

`test_n2_cut7.py`'s own `_extra_record(corpus_root, slug)` (line 644) becomes `_extra_record(corpus_root, seed)` adding `dataset(seed, title=f"dataset {seed}")`; the `"a-successor"` site at line 339 becomes `dataset("a-successor", title="dataset a successor")`.

- [ ] **Step 4: The reproduction tools**

`python/tools/reproduction/hold.py::dataset_record`:

```python
def dataset_record(*, name: str, digest: str, title: str, accession: str) -> tuple[Node, str]:
    node = stored.dataset_node(
        title=title,
        resources=[{"name": name, "digest": digest}],
        empirical_observation={"locator": f"accession:{accession}", "attested_by": AUTHORITY.actor},
        domain_facets={"biology/gene-axis": {"axis": "rows", "namespace": "HGNC"}},
    )
    return node, node.id
```

and drop the now-unused `DatasetDeclaration`, `ResourceDeclaration`, `dataset_address` imports if nothing else in the module uses them. `concepts.py` lines 43–55: delete the `address = dataset_address(...)` line, build `stored.dataset_node(title="mm30 concept vocabulary", resources=[{"name": RESOURCE, "digest": digest}])`, and use `node.id` where `address` was used.

Run: `cd python && uv run --frozen pytest tests/test_reproduction_driver.py`
Expected: the final line reads `N passed`.

- [ ] **Step 5: The on-disk domain-boundary fixture**

`python/tests/test_domain_boundary.py` line 40 writes a raw markdown record `id: dataset:gene-expression-matrix`. Read the test: if the record is only read back through `nodes` or a `ReadView`, leave it. If it is added through `CorpusWriter.add`, `import_bundle` or relocation, compute the derived id from its declared resources (`dataset_address(DatasetDeclaration(...))` over the digests the fixture text declares) and replace the three `dataset:gene-expression-matrix` literals with it. The copy in `docs/superpowers/plans/2026-09-12-d1-cross-repository-negative.md` is an execution record and is not edited.

- [ ] **Step 6: Run the acceptance modules and the guards**

Run each migrated module on the certified volume (the worktree's own `.cut29-acceptance/` directory is on it; `tests/acceptance/conftest.py` refuses otherwise):

```bash
cd python && uv run --frozen pytest tests/acceptance/test_durable_corpus.py tests/acceptance/test_world_selection_acceptance.py tests/acceptance/test_relocation_acceptance.py tests/acceptance/test_world_view_acceptance.py tests/acceptance/test_facet_acceptance.py tests/acceptance/test_world_audit_acceptance.py tests/acceptance/test_durable_traversal.py tests/acceptance/test_source_address_acceptance.py tests/acceptance/test_coreference_acceptance.py tests/acceptance/test_n2_cut5.py tests/acceptance/test_n2_cut7.py tests/acceptance/test_cut15_lineage.py tests/acceptance/test_session_acceptance.py tests/acceptance/test_durable_records.py tests/acceptance/test_deletion_acceptance.py
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py
```

Expected: every module's final line reads `N passed`; the guards pass, with cut 7's re-targeted rows reported by `re_targeted_rows` and nothing newly stale.

- [ ] **Step 7: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
tasks check
git add python/tests/acceptance python/tools/reproduction python/tests/test_domain_boundary.py
git commit -m "test: migrate the acceptance corpus and reproduction tools to derived dataset addresses"
```

---

### Task 5: The write boundary and `consolidate`

**Files:**
- Modify: `python/src/beliefs/corpus.py:117` (import), `:3104-3110` (`_refuse_dataset_basis`)
- Modify: `python/src/beliefs/relocation.py:24-34` (import), `:214-231` (`consolidate`, after the source clause)
- Test: `python/tests/test_corpus_write.py` (new class), `python/tests/test_relocation.py` (append)

**Interfaces:**
- Consumes: `DatasetAddressDisagreement`, `stored.dataset_address_of` (Task 2).
- Produces: `_refuse_dataset_basis` clause 2 on every `_refuse` path; `consolidate` refusing `DatasetAddressDisagreement` naming `keep` or `other`.

- [ ] **Step 1: Write the failing boundary tests**

Append to `python/tests/test_corpus_write.py`:

```python
class TestDatasetAddress:
    """Slice 5 §5: a dataset's stored id is its derived address, on every write path."""

    @staticmethod
    def handle(seed: str, node_id: str = "dataset:handle") -> Node:
        node = stored.governed_node("dataset", node_id.partition(":")[2], seed, {stored.DATASET_FACET: {"resources": pinned(seed)}}, ())
        return node

    def test_a_handle_addressed_dataset_refuses_on_add(self, writer):
        with pytest.raises(DatasetAddressDisagreement) as caught:
            writer.add(self.handle("h"))
        assert dataset_ref("h") in str(caught.value)
        assert not writer.read_view.holds("dataset:handle")

    def test_the_same_bytes_at_the_derived_address_are_admitted(self, writer):
        minted = writer.add(stored.dataset_node(title="h", resources=pinned("h")))
        assert minted.id == dataset_ref("h")

    def test_a_second_add_of_one_byte_set_collides(self, writer):
        writer.add(stored.dataset_node(title="first", resources=pinned("h")))
        with pytest.raises(CollisionRefused):
            writer.add(stored.dataset_node(title="second", resources=pinned("h")))

    def test_a_bundle_with_a_handle_addressed_dataset_refuses_naming_the_member(self, tmp_path):
        from test_relocation import _writer

        importer = _writer(tmp_path / "importer")
        bad = self.handle("h")
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle(
                [bad], observer="o", instrument="i", opened_at="2026-09-14T00:00:00Z", closed_at="2026-09-14T00:00:01Z"
            )
        assert caught.value.member == bad.id
        assert not importer.read_view.holds(bad.id)

    def test_the_basis_refusal_still_precedes_the_address_check(self, writer):
        # An unpinned hand-built record is BasisMissing, never a disagreement over an address it lacks.
        unpinned = stored.governed_node("dataset", "handle", "u", {stored.DATASET_FACET: {"resources": []}}, ())
        with pytest.raises(BasisMissing):
            writer.add(unpinned)
```

Add `DatasetAddressDisagreement`, `CollisionRefused`, `ImportRefused` to the `beliefs.errors` import and `from dataset_fixtures import dataset_ref, pinned` (merge with Task 3's import). `ImportRefused` carries `member` (errors.py line 1258).

Append to `python/tests/test_relocation.py`. The raw-write-then-`_reconstruct()` technique is cut 25's (`test_identifier_correction.py::test_consolidate_refuses_a_handle_addressed_replica_at_replace`): `writer.root` is the corpus path and `_reconstruct()` rebuilds the cached view.

```python
def _raw_dataset_at(writer, node_id: str, seed: str) -> Node:
    """A dataset written behind the boundary at `node_id` with `seed`'s bytes."""
    from fixtures_cut4 import raw_write

    node = stored.governed_node("dataset", node_id.partition(":")[2], seed, {stored.DATASET_FACET: {"resources": pinned(seed)}}, ())
    raw_write(writer.root, node)
    writer._reconstruct()
    return node


def _files(writer) -> list[str]:
    return sorted(str(p.relative_to(writer.root)) for p in writer.root.rglob("*.md"))


def test_move_refuses_a_handle_addressed_dataset_into_a_governed_destination(source_writer, destination_writer):
    node = _raw_dataset_at(source_writer, "dataset:handle", "h")
    with pytest.raises(DatasetAddressDisagreement):
        relocation.move(source_writer, destination_writer, node.id, **MOVE_FIELDS)
    assert not destination_writer.read_view.holds(node.id)
    assert source_writer.read_view.holds(node.id)


@pytest.mark.parametrize("invalid", ["other", "keep"])
def test_consolidate_validates_both_dataset_inputs_before_reconciling(source_writer, destination_writer, invalid):
    """Review finding 1: the loser's declaration is judged before it is discarded."""
    valid = source_writer.add(stored.dataset_node(title="kept", resources=pinned("shared")))
    # A raw record at the SAME id whose bytes are different: its declaration derives another address.
    other = _raw_dataset_at(destination_writer, valid.id, "different")
    keep, lose = (source_writer, valid.id), (destination_writer, other.id)
    if invalid == "keep":
        keep, lose = lose, keep
    before = (_files(source_writer), _files(destination_writer))
    with pytest.raises(DatasetAddressDisagreement) as caught:
        relocation.consolidate(keep, lose, **CONSOLIDATE_FIELDS)
    assert invalid in str(caught.value)
    assert destination_writer.read_view.holds(other.id)
    assert (_files(source_writer), _files(destination_writer)) == before
```

Add `DatasetAddressDisagreement` to the errors import and `from dataset_fixtures import pinned`.

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_corpus_write.py -k TestDatasetAddress tests/test_relocation.py -k "handle_addressed or validates_both"`
Expected: FAIL — the handle record is admitted (no `DatasetAddressDisagreement` raised); the consolidate test consolidates successfully (this is the reviewer's reproduction).

- [ ] **Step 3: The boundary clause**

In `python/src/beliefs/corpus.py`, `_refuse_dataset_basis` (line 3104) becomes — the first `if` line is **byte-identical** to today's:

```python
    def _refuse_dataset_basis(self, node: Node) -> None:
        """W3 as narrowed, the dataset half (clause 1); slice 5 §5's id/address
        agreement (clause 2). The first clause's line is matched by cut 4's
        W3 arms and cut 25's declarations and does not move."""
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:
            raise BasisMissing(
                f"{node.id}: a dataset carries a content identity — every declared resource pinned by an "
                "accepted digest. Supplying it later is a second, separate mint"
            )
        if node.kind == "dataset":
            address = stored.dataset_address_of(node)
            if node.id != address:
                raise DatasetAddressDisagreement(f"{node.id}: the declaration derives {address}")
```

Add `DatasetAddressDisagreement` to the `beliefs.errors` import block (beside `SourceAddressDisagreement`, line 117).

- [ ] **Step 4: The consolidate clause**

In `python/src/beliefs/relocation.py`, after the `if keep_node.kind == "source":` block (line 231) and before `_refuse_contract_disagreement`:

```python
        if keep_node.kind == "dataset":
            for position, node, writer in (("keep", keep_node, keep_writer), ("other", other_node, other_writer)):
                address = stored.dataset_address_of(node)
                if node.id != address:
                    raise DatasetAddressDisagreement(
                        f"{node.id}: the {position} replica in {writer.corpus_id} derives {address}; "
                        "consolidate judges both declarations before it discards one"
                    )
```

Add `DatasetAddressDisagreement` to the errors import (lines 24–34).

- [ ] **Step 5: Run to verify they pass**

Run: `cd python && uv run --frozen pytest tests/test_corpus_write.py tests/test_relocation.py tests/test_relocation_rows.py tests/test_import_bundle.py tests/test_dataset_revision.py`
Expected: the final line reads `N passed`. Then the whole portable suite: `uv run --frozen pytest tests` — `N passed`, no failures (every dataset in the corpus is now at its derived address, so nothing else should trip clause 2; a failure here is a site Task 3 missed — fix it in this task).

- [ ] **Step 6: Staleness and frozen guards**

Run: `cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: pass; cut 4's `W3[6]`/`W3[8]` and cut 25's matchers still find their lines exactly once.

- [ ] **Step 7: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
tasks check
git add python/src/beliefs/corpus.py python/src/beliefs/relocation.py python/tests/test_corpus_write.py python/tests/test_relocation.py
git commit -m "feat(corpus): hold every dataset to its derived address at the boundary and at both consolidate inputs"
```

---

### Task 6: Acceptance — W2, W3 and W8 on the certified volume

**Files:**
- Create: `python/tests/acceptance/test_dataset_address_acceptance.py`

**Interfaces:**
- Consumes: `durable_world` (from `test_world_view_acceptance`), `raw_write` (`fixtures_cut4`), `dataset_fixtures`, `relocation.move`/`consolidate`, `epoch.build_epoch`, `hold_shipped` (`test_world_receipts`).
- Produces: the test node ids the declaration (Task 7) names — keep the function names below exactly.

- [ ] **Step 1: Write the module**

On `test_world_selection_acceptance.py`'s header (imports, `scratch`, `MOVE_FIELDS`, `CONSOLIDATE_FIELDS`). Every function name ends in `_durably`.

```python
"""Cut 29: dataset ids derived from the content identity, over certified durable roots."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, digest_for, pinned
from fixtures_cut4 import raw_write
from profiles import BASE
from test_world_receipts import hold_shipped
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.
from beliefs import relocation, stored
from beliefs.errors import BasisMissing, CollisionRefused, DatasetAddressDisagreement, ImportRefused
from beliefs.root import init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig, epoch

MOVE_FIELDS = {"observer": "o", "instrument": "i", "opened_at": "2026-09-14T00:00:00Z", "closed_at": "2026-09-14T00:00:01Z"}
CONSOLIDATE_FIELDS = {**MOVE_FIELDS, "rationale": "keep holds the authored record"}
OBSERVED = {"locator": "instrument:fixture", "attested_by": ACTOR}


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut29-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def handle(seed: str, node_id: str = "dataset:handle"):
    return stored.governed_node("dataset", node_id.partition(":")[2], seed, {stored.DATASET_FACET: {"resources": pinned(seed)}}, ())


# --- W2, the dataset arm ---------------------------------------------------------

def test_w2_two_corpora_mint_one_address_from_one_declaration_durably(durable_world):
    _, _, left = durable_world.corpus(BASE)
    _, _, right = durable_world.corpus(BASE)
    a = left.add(stored.dataset_node(title="DepMap 24Q2", resources=pinned("depmap"), empirical_observation=OBSERVED))
    b = right.add(stored.dataset_node(title="depmap release", resources=pinned("depmap"), empirical_observation={**OBSERVED, "attested_by": "other"}))
    assert a.id == b.id == dataset_ref("depmap")
    assert stored.dataset_address_of(left.read_view.get(a.id)) == a.id


def test_w2_order_repetition_and_names_do_not_move_the_address_and_one_digest_does_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    x, y = pinned("x")[0], pinned("y")[0]
    one = stored.dataset_node(title="one", resources=[x, y])
    two = stored.dataset_node(title="two", resources=[y, {"name": "renamed", "digest": x["digest"]}, {"name": "copy", "digest": x["digest"]}])
    assert one.id == two.id
    assert stored.dataset_node(title="three", resources=[x, pinned("z")[0]]).id != one.id
    minted = writer.add(one)
    with pytest.raises(CollisionRefused):
        writer.add(two)
    assert writer.read_view.get(minted.id).title == "one"


def test_w2_the_producers_map_and_the_observes_closure_name_the_derived_address_durably(durable_world, scratch):
    a, alpha, left = durable_world.corpus(BASE)
    raw = left.add(stored.dataset_node(title="raw", resources=pinned("raw"), empirical_observation=OBSERVED))
    run = left.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[raw.id], transforms=[raw.id], produces=[dataset_ref("derived")]))
    left.add(stored.dataset_node(title="derived", resources=pinned("derived"), basis={"tag": "single", "routes": [{"run": run.id, "ancestor": raw.id, "transforms": [raw.id]}]}))
    config = WorldConfig(scratch / "world", "e" * 32, (alpha,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(alpha, provenance=Fresh())
    published = epoch.build_epoch(world, coverage=frozenset((a,)), bindings=hold_shipped(world))
    producers = {entry["dataset"]: list(entry["runs"]) for entry in published.documents["producers-map.yaml"]["producers"]}
    assert producers == {dataset_ref("derived"): [run.id]}
    assert stored.inputs_of(left.read_view.get(run.id), stored.OBSERVES) == (dataset_ref("raw"),)


def test_w2_an_unaccepted_algorithm_has_no_address_at_the_builder_or_the_boundary_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    md5 = [{"name": "m", "digest": "md5:" + "0" * 32}]
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="md5", resources=md5)
    with pytest.raises(BasisMissing):
        writer.add(stored.governed_node("dataset", "md5", "md5", {stored.DATASET_FACET: {"resources": md5}}, ()))


# --- W3, the builder arm ---------------------------------------------------------

def test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="empty", resources=[])
    with pytest.raises(BasisMissing):
        stored.dataset_node(title="half", resources=[*pinned("p"), {"name": "unpinned"}])
    minted = writer.add(stored.dataset_node(title="declared, held nowhere", resources=pinned("nowhere")))
    assert writer.read_view.holds(minted.id)


def test_w3_the_boundary_refuses_a_hand_built_unpinned_record_durably(durable_world):
    _, _, writer = durable_world.corpus(BASE)
    with pytest.raises(BasisMissing):
        writer.add(stored.governed_node("dataset", "d1", "d1", {stored.DATASET_FACET: {"resources": []}}, ()))
    assert not any(n.kind == "dataset" for n in writer.read_view.iter_stored())


# --- W8, the address conflict on datasets ---------------------------------------

def test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably(durable_world):
    _, alpha, left = durable_world.corpus(BASE)
    _, _, right = durable_world.corpus(BASE)
    bad = handle("h")
    with pytest.raises(DatasetAddressDisagreement):
        left.add(bad)
    with pytest.raises(ImportRefused) as caught:
        right.import_bundle([bad], **MOVE_FIELDS)
    assert caught.value.member == bad.id
    raw_write(alpha, bad)
    with pytest.raises(DatasetAddressDisagreement):
        relocation.move(left, right, bad.id, **MOVE_FIELDS)
    assert not right.read_view.holds(bad.id)
    good = right.add(stored.dataset_node(title="h", resources=pinned("h")))
    assert good.id == dataset_ref("h")


def test_w8_consolidate_at_one_derived_address_gives_one_address_and_no_redirect_durably(durable_world):
    _, _, left = durable_world.corpus(BASE)
    _, _, right = durable_world.corpus(BASE)
    keep = left.add(stored.dataset_node(title="kept", resources=pinned("shared")))
    other = right.add(stored.dataset_node(title="other", resources=pinned("shared")))
    merged, _, _ = relocation.consolidate((left, keep.id), (right, other.id), **CONSOLIDATE_FIELDS)
    assert merged.id == keep.id == dataset_ref("shared")
    assert merged.deprecated_ids == []
    assert not right.read_view.holds(other.id)


@pytest.mark.parametrize("invalid", ["other", "keep"])
def test_w8_consolidate_judges_both_declarations_before_it_discards_one_durably(durable_world, invalid):
    a, alpha, left = durable_world.corpus(BASE)
    b, beta, right = durable_world.corpus(BASE)
    valid = left.add(stored.dataset_node(title="kept", resources=pinned("shared")))
    raw = handle("different", node_id=valid.id)   # same id, different bytes: derives another address
    raw_write(beta, raw)
    right_reopened = open_corpus(beta, authority=FULL, profile=BASE)   # a fresh view sees the raw write
    keep, lose = (left, valid.id), (right_reopened, raw.id)
    if invalid == "keep":
        keep, lose = lose, keep
    snapshot = lambda root: sorted(str(p.relative_to(root)) for p in Path(root).rglob("*.md"))
    before = (snapshot(alpha), snapshot(beta))
    with pytest.raises(DatasetAddressDisagreement) as caught:
        relocation.consolidate(keep, lose, **CONSOLIDATE_FIELDS)
    assert invalid in str(caught.value)
    assert (snapshot(alpha), snapshot(beta)) == before
```

Notes for the implementer: `Epoch.documents` is keyed by member file name (`world/epoch.py` line 584 on; `producers-map.yaml` carries `producers` entries of `dataset` and `runs`). Re-opening `beta` with `open_corpus` after a raw write is what `test_world_selection_acceptance.py` lines 130–134 do.

- [ ] **Step 2: Run on the certified volume**

Run: `cd python && uv run --frozen pytest tests/acceptance/test_dataset_address_acceptance.py`
Expected: the final line reads `10 passed` (9 functions, one parametrized twice).

- [ ] **Step 3: Lint, type-check, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
tasks check
git add python/tests/acceptance/test_dataset_address_acceptance.py
git commit -m "test(cut29): durable W2, W3 and W8 dataset arms"
```

---

### Task 7: N2 declaration, guard and runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut29.py`, `python/tests/acceptance/test_n2_cut29.py`, `python/tools/cut29_acceptance.py`

**Interfaces:**
- Consumes: the freeze sha and document digest from Task 1's note; the test names of Tasks 3, 5 and 6.
- Produces: `CUT29_ARMS` (6 arms), `DECLARATION_UNITS = ("W2", "W3", "W8")`, `UNIT_CHECKS`, `unit_of`; the guard's pins; the runner.

- [ ] **Step 1: Declare the arms**

`n2_arms_cut29.py`, on cut 28's shape. Copy every `before` by `sed -n` from the file — never retype. The six mechanisms and their intended text:

```python
"""Cut 29 canonical declaration: W2, W3 and W8 dataset arms over the slice 5 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W2", "W3", "W8")
_A = "acceptance/test_dataset_address_acceptance.py"
UNIT_CHECKS = {
    "W2": f"{_A}::test_w2_two_corpora_mint_one_address_from_one_declaration_durably",
    "W3": f"{_A}::test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably",
    "W8": f"{_A}::test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-29 row")
    return unit


def _arm(row, assertion, module, before, after, *checks):
    return Arm(row=row, asserts=assertion, sabotage=Sabotage(module=module, before=before, after=after), checks=tuple(checks))


CUT29_ARMS = (
    _arm("W2-a", "The builder derives the id from the declaration, never the title.", "stored.py",
         '    return _node("dataset", address.partition(":")[2], title, facets, ())',
         '    return _node("dataset", title, title, facets, ())',
         f"{_A}::test_w2_two_corpora_mint_one_address_from_one_declaration_durably",
         "test_stored.py::TestTheDatasetBuilder::test_one_byte_set_is_one_id_whatever_the_title_order_repetition_or_names"),
    _arm("W2-b", "dataset_address_of reads the stored declaration.", "stored.py",
         "    return dataset_address(dataset_declaration(node))",
         "    return node.id",
         "test_stored.py::test_dataset_address_of_reads_the_stored_declaration_not_the_id",
         "test_corpus_write.py::TestDatasetAddress::test_a_handle_addressed_dataset_refuses_on_add"),
    _arm("W3-a", "The builder refuses a declaration with no address before minting.", "stored.py",
         "    address = dataset_address(_declaration_of(facets[DATASET_FACET]))\n    if address is None:",
         "    address = dataset_address(_declaration_of(facets[DATASET_FACET]))\n    if False:",
         f"{_A}::test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably",
         "test_stored.py::TestTheDatasetBuilder::test_an_unpinned_or_empty_declaration_refuses_at_the_builder"),
    _arm("W8-a", "A dataset's stored id must equal its derived address on every write path.", "corpus.py",
         "            if node.id != address:\n                raise DatasetAddressDisagreement(",
         "            if False:\n                raise DatasetAddressDisagreement(",
         f"{_A}::test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably",
         "test_corpus_write.py::TestDatasetAddress::test_a_handle_addressed_dataset_refuses_on_add",
         "test_relocation.py::test_move_refuses_a_handle_addressed_dataset_into_a_governed_destination"),
    _arm("W8-b", "consolidate validates both dataset inputs before reconciling.", "relocation.py",
         '            for position, node, writer in (("keep", keep_node, keep_writer), ("other", other_node, other_writer)):',
         '            for position, node, writer in (("keep", keep_node, keep_writer),):',
         f"{_A}::test_w8_consolidate_judges_both_declarations_before_it_discards_one_durably[other]",
         "test_relocation.py::test_consolidate_validates_both_dataset_inputs_before_reconciling[other]"),
    _arm("W8-c", "Import validates datasets like every other member.", "corpus.py",
         "                self._refuse(record, document_validated=True, view=union, provenance=True)",
         '                if record.kind != "dataset":\n                    self._refuse(record, document_validated=True, view=union, provenance=True)',
         "test_corpus_write.py::TestDatasetAddress::test_a_bundle_with_a_handle_addressed_dataset_refuses_naming_the_member"),
)
```

Under W3-a the sabotaged builder reaches `address.partition` on `None` and raises `AttributeError`, so `pytest.raises(BasisMissing)` fails — the check is not vacuous. Under W8-b the `keep` side is still validated, so only the `[other]` parametrization fails; name it exactly. Under W8-c the source arm of cut 25 (`W5a-h`) shares the `before` line; each arm is applied on its own and both stay unique in the module.

- [ ] **Step 2: The guard**

`test_n2_cut29.py`: copy `test_n2_cut28.py` wholesale, then: add `from n2_arms_cut28 import CUT28_ARMS` and append `*CUT28_ARMS` to `PRIOR_ARMS`; import `CO_CITED, CUT29_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of` from `n2_arms_cut29` (never cut 28's); add `"python/tests/acceptance/n2_arms_cut28.py": "d11baf9",` to `FROZEN_PRIOR_CUT_FILES`; rename every `28` reference to `29` while preserving prior imports and historical commit ids; `FROZEN_CUT` is the cut 29 document; `CUT29_FREEZE_COMMIT` and `CUT29_FROZEN_SHA256` are the values from Task 1's note (the freeze already exists, so no skip guard); `CUT29_DECLARATION_COMMIT` and `CUT29_DECLARATION_SHA256` are `""` with `pytest.skip("declaration not yet pinned")` in `test_the_declaration_is_byte_exact_against_its_own_commit` until Step 5 fills them; the inventory test asserts `DECLARATION_UNITS == ("W2", "W3", "W8")` and `len(CUT29_ARMS) == 6`; the pin test's three `assert ... in current` strings become `"**3 declaration units**"`, `"Three guarantee rows are read, **0 full/closed** newly"` and `'("cut28_acceptance.py",)'`; the row-parser test's invalid rows use `W2-`, `W2a`, `W2-A`, `W2-1`, `W2-aa`, `W2-a-b` and the match string `is not a cut-29 row`. Add at the module's end, as cut 25 does, the comment `# Export the live tuple so arm_staleness.audited_arms measures every audited arm.` — `CUT29_ARMS` is already the imported name, so nothing else is needed.

- [ ] **Step 3: The runner**

`python/tools/cut29_acceptance.py`: copy `cut28_acceptance.py`, replace `28` with `29`, `PREFIX_RUNNERS = ("cut28_acceptance.py",)`, `PHASE_MODULES = ("test_dataset_address_acceptance.py", "test_n2_cut29.py")`, `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut29-acceptance"`, and the `declared_accounting` import from `n2_arms_cut29`.

- [ ] **Step 4: Run the audit and the guards**

```bash
cd python && uv run --frozen pytest tests/acceptance/test_n2_cut29.py
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py
```

Expected: every arm `sound`; no `stale`, `vacuous`, `mixed` or `uncollected`; one planned skip (the declaration pin). A `vacuous` verdict means the named check survives the sabotage — sharpen the fixture in the named test, never the check.

- [ ] **Step 5: Pin the declaration**

```bash
tasks check
git add python/tests/acceptance/n2_arms_cut29.py python/tests/acceptance/test_n2_cut29.py python/tools/cut29_acceptance.py
git commit -m "test(cut29): N2 arms, audit and runner for derived dataset addresses"
git rev-parse HEAD; sha256sum python/tests/acceptance/n2_arms_cut29.py
```

Fill `CUT29_DECLARATION_COMMIT` (full sha) and `CUT29_DECLARATION_SHA256` in the guard, remove the skip, rerun `uv run --frozen pytest tests/acceptance/test_n2_cut29.py`, and commit `test(cut29): pin the declaration`.

---

### Task 8: Discharge on the certified volume

**Files:**
- Create: `docs/plans/2026-09-14-conformance-cut-29-results.md`, `docs/plans/2026-09-14-conformance-cut-29-run/` (`certified.log`, `check.log`, `test.log`)
- Modify: `docs/designs/2026-09-14-conformance-cut-29.md` (**status line only** — §§2–7 are frozen)

- [ ] **Step 1: The root gate, then the runner**

From the repository root of the worktree:

```bash
just check > docs/plans/2026-09-14-conformance-cut-29-run/check.log 2>&1; echo "check exit $?"
just test  > docs/plans/2026-09-14-conformance-cut-29-run/test.log 2>&1;  echo "test exit $?"
cd python && mkdir -p ../.cut29-acceptance
uv run --frozen python tools/cut29_acceptance.py > ../.cut29-acceptance/run.log 2>&1; echo "runner exit $?"
cp ../.cut29-acceptance/run.log ../docs/plans/2026-09-14-conformance-cut-29-run/certified.log
```

Expected: all three exit **0**. Read the final summary lines (`N passed`) of every phase in `run.log` and the Python/TypeScript totals in `test.log`; they go into the record verbatim. Redact only a machine-specific checkout path in the logs, replacing it with `.worktrees/world-resolution-slice-5/...`, and say so in the record.

- [ ] **Step 2: Write the results record**

`docs/plans/2026-09-14-conformance-cut-29-results.md`, on cut 28's six sections: **header** (cut, freeze sha and digest, declaration sha and digest, subject "dataset addresses derived from the content identity", discharged date, runner); **§1 What ran** (the command block above, exit code, transcript path and its `sha256sum`, the prefix chain cut 29 → … → cut 17, the per-phase summary table copied from `run.log`, the declared-arms inventory line `declared arms: 6 (= 3 declaration units; 3 guarantee rows)`, then `just check` and `just test` exits and totals with transcript links); **§2 Accounting and disposition** — "Cut 29 reads three guarantee rows on their dataset arms and closes none newly: W2 and W3 keep their closed status; W8 remains partial only on its ambiguous-search-term conflict. Three declaration units carry 6 arms. The closed count stays at **153 of 196**, with **43 open**. The generated accounting reports exactly `Closed 153 of 196; open 43.`" plus one bullet per unit; **§3 Corrections and deviations** (whatever Tasks 3–7 recorded in task notes; if none, say the frozen §§2–7 and the declaration did not change and no staleness re-target beyond cut 7's dated X9 adapter was required); **§4 Reproduction measurement** — no new mm30 run, the previous measurement stands (cut 22 results §4), and the mm30 record's dataset addresses are what the builder now derives; **§5 Remaining boundary** — `world-resolution` retains `beliefs-24b42b`; `authority-labels` and `contract-cut` unchanged from cut 28; **§6 Main integration** — left for the merge (filled by the controller after the `--no-ff` merge and `just gate` on main, as cut 28 did).

Set the cut document's status line to `**Status:** discharged 2026-09-14; results: `../plans/2026-09-14-conformance-cut-29-results.md`.` — that line is above §1 and outside the frozen body.

- [ ] **Step 3: Commit**

```bash
tasks check
git add docs/plans/2026-09-14-conformance-cut-29-results.md docs/plans/2026-09-14-conformance-cut-29-run docs/designs/2026-09-14-conformance-cut-29.md
git commit -m "docs(cut29): record the discharge on the certified volume"
```

---

### Task 9: Accounting, documentation, the re-rank and task closeout

**Files:**
- Modify: `python/tools/roadmap_status.py:59` (the cut table), `docs/plans/2026-08-29-implementation-roadmap.md` (header, §"Cut 28" paragraph, boundary index row, tier-1 row, lane row, Appendix A), `docs/designs/2026-08-03-redesign-adoption-ledger.md:41-55,197,211-217`, `docs/guide/identity-world-and-change.md:176-180`, `docs/guide/glossary.md:234-237`, `docs/guide/contracts-and-adoption.md:233`, `docs/guide/foundations.md:128`, `README.md:106-109,147-149`, `docs/designs/2026-08-02-world-addressing-design.md:327` (dated note), `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md:570-574` (dated note), the spec's status line, this plan's status line
- Tasks: `beliefs-48214e` and its plan children

- [ ] **Step 1: The accounting tool and the roadmap**

`python/tools/roadmap_status.py`: after the `28:` entry add

```python
    29: ("conformance-cut-29-results §2", "", "W8"),
```

Run `cd python && uv run --frozen python tools/roadmap_status.py` and paste its table and closing line into the roadmap's Appendix A, whose heading becomes `## Appendix A — live status of every guarantee row at cut 29` and whose lead paragraph says cut 29 closes nothing and re-reads W2, W3 and W8 on dataset arms; the W row's "part" cell now reads `W8 (cut 29), W17 (cut 14), W8a (cut 27)`. The closing line must still read `Closed 153 of 196; open 43.` — Appendix B's W8 row cites cut 29 results §2 for the same remainder.

Roadmap header: `**Ranked at:** cut 29, against the ledger's Current state (2026-09-14)`. Replace the "Cut 28 (2026-09-14) discharges…" paragraph and the one after it with:

```markdown
**Cut 29 (2026-09-14) discharges world-resolution slice 5 without changing
the ranking.** Every dataset record's id is now its derived content address,
held at the write boundary and at both inputs of `consolidate`; no guarantee
row moves. `world-resolution` stays first on the path for its one remaining
filed follow-up: divergent correction-history reconciliation
(`beliefs-24b42b`).

The current accounting is 153 of 196 rows closed, with 43 open. The prior
single-corpus mm30 measurement still ranks this boundary on the path when a
second corpus enters; cut 29 adds no new mm30 reproduction measurement.
Dataset addressing (`beliefs-48214e`) closed at cut 29.
```

Boundary index row, tier-1 row 1 and the `world-read` lane row: "the two filed follow-ups: dataset addressing and …" becomes "one filed follow-up: divergent correction-history reconciliation; no guarantee rows", the placement cell adds "slice 5 discharged at cut 29", and the lane's boundaries cell reads `` the `world-resolution` reconciliation follow-up → `event-level-l8` (+ `log-remainder`) → `publish` ``. The `test_the_roadmap_and_ledger_name_the_same_boundaries` guard holds ids, not prose, so the row keeps its id.

- [ ] **Step 2: The ledger**

`Current state`: `**Updated 2026-09-14** for cut 29's world-resolution slice 5 discharge.`; `**Implemented through conformance cut 29.**` with `cuts 26–29 record discharge in their dated results records, most recently ../plans/2026-09-14-conformance-cut-29-results.md`; the `world-resolution` row's boundary cell becomes `` one filed follow-up: divergent correction-history reconciliation (`beliefs-24b42b`); no guarantee row remains `` and its "what it blocks" cell `correction-history reconciliation`; the "newest results record" paragraph names the cut 29 record and says it discharges slice 5, holding every dataset to its derived address, with W8 unchanged and `beliefs-24b42b` retaining the open work.

- [ ] **Step 3: Guide, README, dated notes**

- `docs/guide/identity-world-and-change.md` lines 176–180: after the cut 28 sentence add `Cut 29 derives every dataset id from its declared content identity — the ruled fold, unchanged — and holds it at the write boundary and at both inputs of `consolidate`; divergent-history reconciliation remains filed.`
- `docs/guide/glossary.md`, after **Source address**: `- **Dataset address** — The `dataset:sha256:<hex>` lookup key: the ruled fold over a dataset's declared resource digests (deduplicated, sorted, newline-joined, sha256), which is the record's id from cut 29. ([identity](identity-world-and-change.md#identity-is-not-one-field))`
- `docs/guide/contracts-and-adoption.md` line 233: append a sentence naming cut 29 and its document, on the cut 28 sentence's shape.
- `docs/guide/foundations.md` line 128 is about the evaluator and does not change.
- `README.md` lines 106 and 147–149: `through **cut 29**`, and "The latest discharged boundary is cut 29" with the cut and results links.
- World design §4.2, `dataset` row (line 327): append `*— and from 2026-09-14 (cut 29) the stored id **is** that address: `stored.dataset_node` derives it and the write boundary refuses a dataset whose id disagrees with its declaration (`DatasetAddressDisagreement`), on add, import, move and both inputs of `consolidate`*`.
- Slice 2b §12 item 1: append `*Built at cut 29 (2026-09-14): the address stays `dataset:sha256:<fold>` as ruled; see `2026-09-14-world-resolution-slice-5-design.md`.*`
- The slice 5 spec's status line: `**Status:** discharged at conformance cut 29 on 2026-09-14; results: `../../plans/2026-09-14-conformance-cut-29-results.md``; this plan's status line: `**Status:** implementation discharged at conformance cut 29 on 2026-09-14.`

- [ ] **Step 4: Verify the guards and gate**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_arm_staleness.py tests/test_frozen_guards.py
cd .. && just check
```

Expected: pass, exit 0. (`just test` ran in Task 8 over the same source; if any source file changed since, run it again.)

- [ ] **Step 5: Close the tasks and commit**

```bash
tasks done <the Task 9 child id> "Accounting, docs and re-rank landed for cut 29"
tasks done beliefs-48214e "Slice 5 landed: dataset ids derived from the content identity, DatasetAddressDisagreement at the boundary and both consolidate inputs; cut 29 discharged, no row moves"
tasks check
git add -A docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut29): discharge conformance cut 29 and re-rank the roadmap"
```

Then hand the branch to the controller for the whole-branch review and the `--no-ff` merge; the results record's §6 is filled after `just gate` passes on merged `main`.

---

## Self-review

**Spec coverage.** §2 items 1–6: Task 3 (builder), Task 5 (boundary, consolidate), Task 1/9 (no audit finding; documented). §3 reader: Task 2. §4 builder: Task 3. §5 paths: Task 5 tests add, import, move, replacement (through consolidate), consolidate both inputs. §6: Task 4 Step 4, Task 8 §4. §7 refusals: Tasks 2, 3, 5. §8.1 unit: Tasks 2, 3, 5. §8.2 migration incl. the three boundary sites and `test_domain_boundary.py`: Tasks 3, 4. §8.3 acceptance: Task 6. §8.4 arms: Task 7 (six arms — the plan fixes the count the spec left open). §8.5 cut: Tasks 1, 7, 8. §8.6 frozen evidence, cut 7 adapter, live phase modules: Task 4. §9 shared files: Tasks 1, 9. §10 task linkage: plan attach. §11 limitations: Task 1 §7.

**Type consistency.** `dataset_node(*, title, resources, empirical_observation=None, basis=None, domain_facets=None)` is used identically in Tasks 3–6; `dataset_address_of(node) -> str | None` in Tasks 2, 5, 6, 7; `dataset_fixtures.pinned(seed)`, `dataset_ref(seed)`, `pinned_for(ref)`, `dataset(seed, *, title=None, **facets)` throughout; `DatasetAddressDisagreement` in Tasks 2, 5, 6, 7.

**Known unknowns named where the implementer meets them.** The domain-boundary fixture's write path (Task 4 Step 5); the exact multi-line builder sites the mechanical pass cannot reach (Task 3 Step 4).
