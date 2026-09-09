# World resolution slice 1 — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the kernel's walks, snapshot builders, evaluator and verification check a world read view — a per-corpus coherent capture bound to one published epoch — so a read that today stops at the corpus edge continues through the epoch's address map and reports `not-present` where a covered corpus is absent.

**Architecture:** One new module, `beliefs/world/view.py`, holds a sealed `WorldReadView` with the corpus `ReadView`'s method shape plus `locate`, `corpus_of`, `corpus_view`, `published_producers`, `absent` and `drift`. It is opened at an explicit `Epoch`, captures every present covered corpus under that corpus's `OperationLock.capture()`, serves detached copies of mapped records only, and answers inbound queries from an index it builds over mapped records with targets resolved through the world map. The existing adjacencies, `lineage_snapshot`, `gather`, `evaluate_over`, `run_value` and `check_verification` widen their annotations to the union `ReadView | WorldReadView`; `LineageSnapshot`, `Producer`, `Certification`, `divergence_state` and the resolution snapshot gain identity-encodable absence members. The work freezes as conformance cut 23 before any code lands and discharges through its own runner.

**Tech Stack:** Python 3.11+ (`uv run --frozen`), pytest with `pytest-xdist`, pydantic v2 `Node` models from `nodes`, the `atoms` durable engine for the acceptance arms, ruff and pyright as the gate.

**Spec:** `docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md` (revised through `a92fe8d`). The plan argues from it; read both.

## Global Constraints

- Work on branch `design/world-resolution` in `.worktrees/world-resolution`; commit with conventional messages; no AI-attribution trailers.
- Run every Python command from `python/` with `uv run --frozen …`; the pre-commit hook runs ruff, pyright, the ts checks and `tasks check`, so `ts/node_modules` must exist (`cd ts && npm ci` once).
- `ReadView` stays sealed, final and constructed only over `nodes.core.corpus.Corpus` (B3); `read_observed_facets` keeps its exact-type check. Nothing here changes either.
- Every new projection member is identity-encodable: no `None`, no tuple; use `[] | [value]` lists and lists of objects, the `_ref_projection` idiom.
- Only a `NotPresent` answer enters `not_present`, `absent` or the resolution snapshot's third state; every refusal propagates.
- The world lock (`registry._locked_barrier`) is held for the registry scan only and released before any corpus capture; captures are serial in sorted `corpus_id` order under `OperationLock.capture()`, which never waits.
- Shared surfaces this lane rewrites, per roadmap concurrency rule 3: `corpus.py`, `lineage.py`, `resolution.py`, `evaluation.py`, `belief.py`, `consulted.py`, `audit.py`, `errors.py`, plus `python/tests/test_designs_corpus.py`, the ledger, the roadmap and the guide index at discharge.
- The cut is frozen before implementation (Task 1) and its §§2–7 are byte-exact from the freeze commit onward; §1 stays editable. The cut number is 23 unless a sibling worktree has already claimed it — check every worktree's `docs/designs/` at freeze.
- Fast loop: `uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py`. Gate before each commit: `uv run --frozen ruff check . && uv run --frozen pyright`.

---

## File structure

| path | responsibility |
|---|---|
| `docs/designs/2026-09-09-conformance-cut-23.md` | the frozen cut: boundary, selection, accounting, obligations |
| `python/src/beliefs/errors.py` | `RecordNotPresent` |
| `python/src/beliefs/corpus.py` | `validated_node` factored out of `ReadView._validated`; widened adjacencies, `superseded_by`, `_producer_ids`, `lineage_snapshot`, `_producers_of`, `run_value` |
| `python/src/beliefs/world/view.py` | **new** — `DriftReport`, `WorldReadView`, `open_world_view` |
| `python/src/beliefs/world/__init__.py` | re-export of the three names |
| `python/src/beliefs/lineage.py` | `Absence`, `Producer.absent`, `LineageSnapshot.not_present`, `Certification.absent`, `divergence_state` → `"incomplete"`, projections |
| `python/src/beliefs/resolution.py` | `_BoundVocabulary.state/absent`, `build_snapshot(not_present=)`, `NOT_PRESENT` reachable |
| `python/src/beliefs/consulted.py`, `belief.py` | `node_corpus: Mapping[str, tuple[str, ...]]`; `NoBelief.detail` |
| `python/src/beliefs/evaluation.py` | widened `gather`/`evaluate_over`; attribution at the read; facet-set comparison; `unavailable-corpus-absent`; `EvaluationInputs.absent` |
| `python/src/beliefs/audit.py` | `check_verification` widened |
| `python/tests/test_world_view.py` | **new** unit tests for the view |
| `python/tests/test_lineage.py`, `test_resolution_snapshot.py` (**new**), `test_evaluation.py`, `test_audit.py`, `test_corpus_traversal.py` | unit arms |
| `python/tests/acceptance/test_world_view_acceptance.py` | **new** durable arms on the certified volume |
| `python/tests/acceptance/n2_arms_cut23.py`, `test_n2_cut23.py` | declarations and guard |
| `python/tools/cut23_acceptance.py` | the runner |
| `docs/plans/2026-09-XX-conformance-cut-23-results.md`, ledger, roadmap, `docs/designs/README.md` | discharge |

---

### Task 1: Freeze conformance cut 23

**Files:**
- Create: `docs/designs/2026-09-09-conformance-cut-23.md`
- Modify: `docs/designs/README.md` (the design list and its count), `python/tests/test_designs_corpus.py` only if `_COUNT_WORDS` needs the next number word

**Interfaces:**
- Produces: the nine declaration units named below, cited verbatim by Task 12's `DECLARATION_UNITS`, and the literal `PREFIX_RUNNERS = ("cut22_acceptance.py",)` cited by Task 13.

- [ ] **Step 1: Confirm the number is free**

```bash
git -C /mnt/ssd/Dropbox/beliefs worktree list
for wt in $(git -C /mnt/ssd/Dropbox/beliefs worktree list --porcelain | awk '/^worktree /{print $2}'); do ls "$wt/docs/designs" | grep -c "conformance-cut-23" ; done
```
Expected: every count is `0`. If not, the number is taken; use the next free one everywhere below.

- [ ] **Step 2: Write the cut document**

Follow `docs/designs/2026-09-08-conformance-cut-22.md` section for section. Header:

```markdown
# Conformance cut 23 — the world read view and cross-corpus traversal

**Status:** frozen 2026-09-09 before implementation.
**Frozen:** 2026-09-09, before implementation, on `design/world-resolution`
**Design:** `../superpowers/specs/2026-09-09-world-resolution-slice-1-design.md`, reviewed 2026-09-09
**Numbered after** cut 22 (roadmap concurrency rule 1) and **serialized after** its discharge, which landed on `main` at `197f517` (rule 5).
```

`## 1. What this cut is` — two paragraphs from spec §1, plus the selection rule sentence cut 22 uses ("a clause is selected only when its source mutation and every named check run inside §2").

`## 2. The boundary` — `In scope:` bullets naming, at file-and-symbol granularity, every item in this plan's file-structure table; `Out of scope:` bullets naming slice 2 (the `coreference-attestation` kind, X12, W15, W8a's coreference arms, M3's coreference arm, W4, W1, W2, W5a), slice 3 (the import, audit and diagnostic callers; R23's snapshot, divergence and explicit-import clauses; X5, W13), slice 4 (W7), and `ReadView` itself.

`## 3. Selection` — one subsection per row, each ending with `Selected:` and `**Deferred:**`:

```markdown
### D3 — closes
`not-present` produced over the world index; the five-way non-collapse with every member reachable; every pair of overlapping availability inputs refused. Selected: unit `D3`. **Deferred:** nothing.

### S1 — closes
The relation chain crossing corpora returns its full closure through the world inbound index; the dangling-target case stays distinguishable. Selected: unit `S1`. **Deferred:** nothing.

### S1a — closes
The lineage chain crossing corpora, walked as a facet, returns its full closure. Selected: unit `S1a`. **Deferred:** nothing.

### S5 — closes
Cross-corpus reach: an absent ancestor or producing run in a covered corpus is `lineage-incomplete` naming the corpus, `not-certified`, and moves the belief input digest through the lineage projection. Selected: unit `S5`. **Deferred:** nothing.

### W6 — closes, read over slice 2's code
Three states, never collapsed; removing a corpus does not convert its ids to `unknown`. Selected: unit `W6`. **Deferred:** nothing.

### W8b — closes, read over slice 2's code
Duplicate-location and corruption distinguished at build; no repair offered. Selected: unit `W8b`. **Deferred:** nothing.

### W10 — closes
Cross-corpus edges are ordinary at the world layer and dangling at the corpus layer. Selected: unit `W10`. **Deferred:** nothing.

### R19 — closes
Cross-corpus recomputation: `check_verification` over the world view reports a well-formed forgery whose runs sit in the other corpus as `verification-derivation-contradicted`, and a malformed record raises. Selected: unit `R19`. **Deferred:** nothing.

### R23 — part, coverage clause
Absence within coverage reads `not-present` and digests differently from absence outside it. Selected: unit `R23`. **Deferred:** the snapshot, cross-corpus-divergence and explicit-import clauses (slice 3) and the rules-store clauses (`contract-cut`).

### Boundary invariants
The view captures, never rereads; every object served is detached; the world lock is released before any capture; only `NotPresent` enters an absence structure; every projection member is identity-encodable.
```

`## 4. Accounting` — exactly these two sentences, which the guard greps:

```markdown
Nine guarantee rows are read, **8 full/closed** (D3, S1, S1a, S5, W6, W8b, W10, R19), 1 partial (R23), and **9 declaration units** carry them: `D3`, `S1`, `S1a`, `S5`, `W6`, `W8b`, `W10`, `R19`, `R23`.
```

`## 5. N2 and acceptance obligations` — numbered as cut 22's: (1) the inventory is exactly the nine units, single-homed; (2) every durable arm runs on the certified volume, refusal is an error and never a skip; (3) the runner, quoting `PREFIX_RUNNERS = ("cut22_acceptance.py",)` and `PHASE_MODULES = ("test_world_view_acceptance.py", "test_n2_cut23.py")`; (4) every sabotage site, listed from spec §8's N2 paragraph plus the two measured-row sabotages: in `world/view.py` (map-first resolution replaced by a carrier scan; the absent set read as unknown; `get` served from the live carrier; drift sources filed in the inbound index; targets resolved through the local index; the retained node returned), in `corpus.py` (the published-producers union dropped; `not_present` filtered by the inspected set), in `lineage.py` (the divergence comparison made over an absent producer; `not_present` omitted from the projection), in `resolution.py` (one overlap pair unrefused), in `evaluation.py` (attribution after the fact through `corpus_of`; the world view passed to `read_observed_facets`; the facet comparison made on identities), in `world/read.py` (`not status.present` answered `Unknown`), in `world/registry.py` (the `duplicate-carrier` finding dropped); (5) `test_n2_cut23.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree; (6) prior declarations frozen, no check reclaimed; (7) the freeze pin.

`## 6. Second reader` and `## 7. Limitations` — the second reader records the three review passes on the spec (§11 there); limitations: per-corpus coherent capture is not one world state; the absent set reaches the digest through the lineage member only (spec §9).

- [ ] **Step 3: Add the document to the README list and count**

Open `docs/designs/README.md`, add the cut in date order in the same format as cut 22's entry, and bump the stated count by one (the phrase the test `test_the_readme_states_how_many_designs_there_are` greps; run it to see the exact wording expected).

- [ ] **Step 4: Run the design-corpus guards**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider`
Expected: PASS. If `test_the_readme_states_how_many_designs_there_are` fails on the number word, extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` by the next word and rerun.

- [ ] **Step 5: Commit the freeze**

```bash
git add docs/designs/2026-09-09-conformance-cut-23.md docs/designs/README.md python/tests/test_designs_corpus.py
git commit -m "docs(cut23): freeze conformance cut 23, the world read view"
git rev-parse --short HEAD   # this is CUT23_FREEZE_COMMIT for Task 12
```

Record the sha and `sha256sum docs/designs/2026-09-09-conformance-cut-23.md` in a task note: `tasks note beliefs-d248ba "cut 23 frozen at <sha>, sha256 <digest>"`.

---

### Task 2: `RecordNotPresent` and `validated_node`

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `ResolutionRefused`, around line 388)
- Modify: `python/src/beliefs/corpus.py:299-314` (`ReadView._validated`)
- Test: `python/tests/test_corpus_write.py` (append)

**Interfaces:**
- Produces: `errors.RecordNotPresent(ScienceError)`; `corpus.validated_node(node: Node) -> Node` raising `SemanticHashMissing` / `SemanticHashStale`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_corpus_write.py`:

```python
def test_validated_node_is_the_facade_rule_factored_out():
    from beliefs.corpus import ReadView, validated_node
    from beliefs import stored
    from beliefs.errors import SemanticHashMissing

    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    with pytest.raises(SemanticHashMissing):
        validated_node(node)
    stamped = stored.stamp_semantic_identity(node)
    assert validated_node(stamped) is stamped
    assert ReadView._validated(stamped) is stamped


def test_record_not_present_is_its_own_refusal():
    from beliefs.errors import RecordNotPresent, ResolutionRefused, ScienceError

    assert issubclass(RecordNotPresent, ScienceError)
    assert not issubclass(RecordNotPresent, ResolutionRefused)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_corpus_write.py -k "validated_node or record_not_present" -q -p no:cacheprovider`
Expected: FAIL, `ImportError` on `validated_node` / `RecordNotPresent`.

- [ ] **Step 3: Implement**

In `errors.py`, after `ResolutionRefused`:

```python
class RecordNotPresent(ScienceError):
    """A world read reached a record the epoch maps to a covered corpus that
    has no carrier here. The answer `NotPresent` exists for a caller who asks;
    a caller who fetches gets this refusal rather than a record nobody holds.
    It is never raised for an address the epoch did not record — that is the
    corpus's own `RefError` — and never for corruption, which is
    `ResolutionRefused`."""
```

In `corpus.py`, replace the body of `ReadView._validated` with a call and add the module-level function directly above the class:

```python
def validated_node(node: Node) -> Node:
    """The facade's fetch rule, in one place: a governed record is stamped and
    its stamp agrees with the fields it covers. `ReadView.get` and the world
    read view's `get` both serve through this and nothing else does."""
    if stored.semantic_hash_missing(node):
        raise SemanticHashMissing(
            f"{node.id}: a {node.kind!r} carries no semantic-identity stamp "
            "(semantic-hash-missing); the boundary mints every governed record stamped, "
            "so an unstamped one is a raw write that skipped even self-stamping"
        )
    if stored.semantic_hash_disagrees(node):
        raise SemanticHashStale(
            f"{node.id}: the stored semantic hash disagrees with the fields it covers "
            "(semantic-hash-stale); the node is an untrusted import, not a guaranteed mutation"
        )
    return node
```

and

```python
    @staticmethod
    def _validated(node: Node) -> Node:
        return validated_node(node)
```

- [ ] **Step 4: Run the tests and the fast loop**

Run: `uv run --frozen pytest tests/test_corpus_write.py -q -p no:cacheprovider && uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py -q -p no:cacheprovider`
Expected: PASS; the N2 arm staleness test (`tests/test_arm_staleness.py`) stays green because no arm's `before` names `_validated`'s body — confirm by its passing.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/errors.py python/src/beliefs/corpus.py python/tests/test_corpus_write.py
git commit -m "feat(corpus): factor the facade's fetch rule into validated_node and add RecordNotPresent"
```

---

### Task 3: `WorldReadView` — opening, resolution, enumeration, drift, isolation

**Files:**
- Create: `python/src/beliefs/world/view.py`
- Modify: `python/src/beliefs/world/__init__.py` (re-export `DriftReport`, `WorldReadView`, `open_world_view`)
- Test: `python/tests/test_world_view.py` (new)

**Interfaces:**
- Consumes: `read._address_map`, `read._stamp`, `read.Resolved/NotPresent/Unknown/Location/BoundStamp`; `registry._locked_barrier`, `_scan_registry`, `_reduce_status`, `_carrier_roots`, `corpus_state_identity`; `corpus._root_state_for`, `validated_node`, `ReadView`; `epoch.Epoch.documents["address-map.yaml"]["addresses"]` and `["producers-map.yaml"]["producers"]`.
- Produces: `open_world_view(world, published) -> WorldReadView`; on the view: `stamp`, `resolve`, `holds`, `get`, `iter_stored`, `live_id`, `locate`, `corpus_of`, `corpus_view`, `absent()`, `drift()`, and (Task 4) `inbound`, `producers`, `published_producers`. `DriftReport(corpus_id, published_state, captured_state, unmapped)`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_world_view.py`:

```python
"""The world read view: a per-corpus coherent capture bound to one epoch.

Two covered corpora throughout, because one corpus going absent has to be a
statement about that corpus and not about the epoch (`test_world_read`'s
argument).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import FULL
from nodes.core.errors import RefError
from profiles import WITH_BIOLOGY
from test_world_build import ALPHA, BETA, sample_nodes, slug_for
from test_world_receipts import corpora, hold_shipped, publish, world_over

from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView, _root_state_for
from beliefs.errors import BuildContended, RecordNotPresent, ResolutionRefused
from beliefs.world import read, registry
from beliefs.world.view import DriftReport, WorldReadView, open_world_view
from nodes.core.write_plan import DefaultExecutor


def two_corpus_world(tmp_path: Path):
    coverage = (ALPHA, BETA)
    roots = corpora(
        tmp_path,
        {ALPHA: sample_nodes(slug_for(ALPHA, coverage)), BETA: sample_nodes(slug_for(BETA, coverage))},
    )
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    return world, roots, publish(world, coverage, bindings)


def address_in(published, corpus_id: str, kind: str = "dataset") -> str:
    for entry in published.documents["address-map.yaml"]["addresses"]:
        if entry["corpus_id"] == corpus_id and entry["address"].startswith(f"{kind}:"):
            return entry["address"]
    raise AssertionError(f"no {kind} in {corpus_id}")


def make_absent(roots: dict[str, Path], corpus_id: str) -> None:
    (roots[corpus_id] / "corpus.yaml").unlink()


class TestOpening:
    def test_the_stamp_is_the_epochs(self, tmp_path):
        world, _roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        assert view.stamp == read.BoundStamp(published.packaging_identity, published.coverage)
        assert view.absent() == ()
        assert view.drift() == ()

    def test_a_present_corpus_captures_and_an_absent_one_is_named(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert view.absent() == (BETA,)
        alpha = address_in(published, ALPHA)
        beta = address_in(published, BETA)
        assert type(view.locate(alpha)) is read.Resolved
        assert type(view.locate(beta)) is read.NotPresent
        assert type(view.locate("dataset:never-observed")) is read.Unknown
        assert view.corpus_of(beta) == BETA
        assert view.corpus_of("dataset:never-observed") is None
        assert view.resolve(beta) is None and not view.holds(beta)
        with pytest.raises(RecordNotPresent):
            view.get(beta)
        with pytest.raises(RefError):
            view.get("dataset:never-observed")

    def test_a_writer_holding_the_lock_refuses_the_open_at_once(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        state = _root_state_for(roots[ALPHA], DefaultExecutor)
        with state.lock:
            with pytest.raises(BuildContended):
                open_world_view(world, published)

    def test_a_carrier_disagreeing_with_the_map_is_corruption(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        alpha = address_in(published, ALPHA)
        uid = next(e["uid"] for e in published.documents["address-map.yaml"]["addresses"] if e["address"] == alpha)
        path = roots[ALPHA] / "dataset" / f"{alpha.partition(':')[2]}.md"
        path.write_text(path.read_text().replace(uid, "0" * 32))  # the map names a uid the carrier no longer holds
        with pytest.raises(ResolutionRefused):
            open_world_view(world, published)


class TestBoundReads:
    def test_reads_are_from_the_capture_and_drift_is_reported_on_the_next_open(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        first = open_world_view(world, published)
        alpha = address_in(published, ALPHA)
        before = first.get(alpha)
        writer = CorpusWriter(roots[ALPHA], DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY)
        writer.add(stored.dataset_node("late", title="late"))
        assert first.get(alpha) == before
        assert "dataset:late" not in {n.id for n in first.iter_stored()}
        assert first.drift() == ()  # it reports what it captured, not what came after
        assert type(first.locate("dataset:late")) is read.Unknown
        second = open_world_view(world, published)
        (report,) = second.drift()
        assert report.corpus_id == ALPHA
        assert report.published_state != report.captured_state
        assert report.unmapped == (writer.read_view.get("dataset:late").uid,)
        assert "dataset:late" not in {n.id for n in second.iter_stored()}

    def test_enumeration_is_mapped_records_in_corpus_order(self, tmp_path):
        world, _roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        ids = [n.id for n in view.iter_stored()]
        recorded = {e["address"] for e in published.documents["address-map.yaml"]["addresses"]}
        assert set(ids) <= recorded and len(ids) == len(set(ids))
        corpora_seen = [view.corpus_of(i) for i in ids]
        assert corpora_seen == sorted(corpora_seen)

    def test_get_validates_like_the_facade(self, tmp_path):
        """Edit a covered facet behind the boundary without restamping: the
        capture holds the edited bytes, and `get` refuses them as the facade would."""
        from nodes.core.corpus import Corpus
        from nodes.core.frontmatter import node_to_markdown

        from beliefs.errors import SemanticHashStale

        world, roots, published = two_corpus_world(tmp_path)
        alpha = address_in(published, ALPHA)
        node = Corpus(roots[ALPHA]).get(alpha)
        node.facets["dataset"]["resources"] = [{"digest": "f" * 64}]
        (roots[ALPHA] / "dataset" / f"{alpha.partition(':')[2]}.md").write_text(node_to_markdown(node))
        view = open_world_view(world, published)
        with pytest.raises(SemanticHashStale):
            view.get(alpha)

    def test_corpus_view_is_the_holding_corpus_and_refuses_absence(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert type(view.corpus_view(address_in(published, ALPHA))) is ReadView
        with pytest.raises(RecordNotPresent):
            view.corpus_view(address_in(published, BETA))
        with pytest.raises(RefError):
            view.corpus_view("dataset:never-observed")


class TestIsolation:
    def test_a_returned_object_is_detached(self, tmp_path):
        world, _roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        alpha = address_in(published, ALPHA)
        node = view.get(alpha)
        node.title = "mutated"
        node.facets["dataset"]["resources"].append({"digest": "x"})
        assert view.get(alpha).title != "mutated"
        assert view.get(alpha).facets["dataset"]["resources"] == []
        yielded = next(n for n in view.iter_stored() if n.id == alpha)
        yielded.deprecated_ids.append("dataset:fake")
        assert "dataset:fake" not in next(n for n in view.iter_stored() if n.id == alpha).deprecated_ids
        assert view.get(alpha) is not view.get(alpha)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_world_view.py -q -p no:cacheprovider`
Expected: FAIL at import, `No module named 'beliefs.world.view'`.

- [ ] **Step 3: Write the module**

Create `python/src/beliefs/world/view.py`:

```python
"""The world read view: a per-corpus coherent capture, bound to one epoch.

`world/read.py` answers one question at a time from a publication. This
module answers the questions the kernel's walks ask — fetch, enumerate,
inbound — across every corpus the publication covers, and it answers them
from a capture rather than from live carriers, so that a walk sees each
corpus in one coherent state (design §3.2).

**What is bound.** Addressing goes through the epoch's address map only. An
address the map records resolves to its captured record or reads
`not-present`; an address it never observed is `unknown` whatever a carrier
holds now; a carrier record the map does not know is drift, reported and
never served (§2 decision 2).

**What is coherent.** Each present covered corpus is captured under its own
`OperationLock.capture()`, which never waits: state identity, every record,
state identity again, and `CaptureDrift` if they differ — `epoch._capture`'s
discipline. The captures are serial, so the view is a sequence of coherent
corpus states, not one world state; the stamp names the publication and no
moment.

**What leaves.** Detached copies only. `Node` and its parts are mutable, and
a caller that could reach a retained record could rewrite the capture behind
the inbound index built over it.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast, final

from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge

from beliefs.corpus import ReadView, _producer_ids, _root_state_for, validated_node
from beliefs.errors import CaptureDrift, ManifestMalformed, RecordNotPresent, ResolutionRefused
from beliefs.sealed import sealed
from beliefs.world import epoch, registry
from beliefs.world.read import BoundStamp, Location, NotPresent, Resolved, Unknown, _address_map, _stamp

__all__ = ["DriftReport", "WorldReadView", "open_world_view"]

_MINT = object()


@final
@dataclass(frozen=True)
class DriftReport:
    """One present corpus whose bytes are not the bytes the epoch captured.

    `unmapped` is every uid the capture holds that the map does not record
    for this corpus; the two states disagree whenever anything changed, uids
    or not. A corpus that agrees on both appears in no report.
    """

    corpus_id: str
    published_state: str
    captured_state: str
    unmapped: tuple[str, ...]


@sealed
@final
class WorldReadView:
    """Built by `open_world_view` only; see the module docstring."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionRefused("WorldReadView is opened, never constructed — use open_world_view(world, published)")

    @classmethod
    def _opened(
        cls,
        mint: object,
        *,
        stamp: BoundStamp,
        recorded: Mapping[str, tuple[str, str]],
        held: Mapping[str, Mapping[str, Node]],
        absent: tuple[str, ...],
        drift: tuple[DriftReport, ...],
        inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]],
        producers: Mapping[tuple[str, str], tuple[str, ...]],
        live: Mapping[str, ReadView],
    ) -> WorldReadView:
        if mint is not _MINT:
            raise ResolutionRefused("WorldReadView._opened is open_world_view's own route")
        view = object.__new__(cls)
        view._stamp = stamp
        view._recorded = recorded
        view._held = held
        view._absent = absent
        view._drift = drift
        view._inbound = inbound
        view._producers = producers
        view._live = live
        return view

    # --- world-only --------------------------------------------------------

    @property
    def stamp(self) -> BoundStamp:
        return self._stamp

    def absent(self) -> tuple[str, ...]:
        return self._absent

    def drift(self) -> tuple[DriftReport, ...]:
        return self._drift

    def locate(self, ref: str) -> Resolved | NotPresent | Unknown:
        entry = self._recorded.get(ref)
        if entry is None:
            return Unknown(self._stamp)
        corpus_id, uid = entry
        if corpus_id in self._absent:
            return NotPresent(self._stamp)
        return Resolved(Location(corpus_id, uid), self._stamp)

    def corpus_of(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else entry[0]

    def corpus_view(self, ref: str) -> ReadView:
        located = self._located(ref)
        return self._live[located.location.corpus_id]

    def published_producers(self, dataset: str) -> tuple[str, ...]:
        entry = self._recorded.get(dataset)
        return () if entry is None else self._producers.get(entry, ())

    # --- the corpus read shape --------------------------------------------

    def resolve(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        if entry is None or entry[0] in self._absent:
            return None
        corpus_id, uid = entry
        return self._held[corpus_id][uid].id

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    def get(self, ref: str) -> Node:
        located = self._located(ref)
        node = self._held[located.location.corpus_id][located.location.uid]
        return validated_node(node).model_copy(deep=True)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        entry = self._recorded.get(ref)
        if entry is None:
            return []
        return [
            ResolvedEdge(relation=copy.deepcopy(edge.relation), source_uid=edge.source_uid, target_uid=edge.target_uid)
            for edge in self._inbound.get(entry, ())
        ]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return _producer_ids(self, dataset, aliases=aliases)

    def iter_stored(self) -> Iterator[Node]:
        for corpus_id in sorted(self._held):
            records = self._held[corpus_id]
            for uid in sorted(records):
                yield records[uid].model_copy(deep=True)

    def live_id(self, uid: str) -> str:
        for records in self._held.values():
            node = records.get(uid)
            if node is not None:
                return node.id
        raise KeyError(uid)

    # --- internals ---------------------------------------------------------

    def _located(self, ref: str) -> Resolved:
        located = self.locate(ref)
        if type(located) is Unknown:
            raise RefError(f"no node resolves ref {ref!r}")
        if type(located) is NotPresent:
            raise RecordNotPresent(
                f"{ref}: recorded in {self._recorded[ref][0]}, a covered corpus with no carrier here "
                f"(publication {self._stamp.packaging_identity[:12]}…); the record is elsewhere, not gone"
            )
        return cast(Resolved, located)


def open_world_view(world: registry.World, published: epoch.Epoch) -> WorldReadView:
    """§3.2: the registry under the world lock, then one capture per corpus."""
    stamp = _stamp(published)
    recorded = _address_map(published)
    covered = tuple(corpus_id for corpus_id, _ in published.coverage)
    published_states = dict(published.coverage)

    carriers: dict[str, Path] = {}
    with registry._locked_barrier(world) as world_root:
        world._state.registry = registry._scan_registry(world_root)
        for corpus_id in covered:
            try:
                status = registry._reduce_status(world.config, world._state.registry, corpus_id)
            except ManifestMalformed as caught:
                raise ResolutionRefused(
                    f"{corpus_id}: a configured root claims a manifest this world cannot read, so it can say "
                    f"neither that the corpus is here nor that it is absent: {caught}"
                ) from caught
            if any(finding.code == "duplicate-carrier" for finding in status.findings):
                raise ResolutionRefused(
                    f"{corpus_id}: more than one configured carrier claims this corpus, so which bytes "
                    "answer is a configuration question rather than a resolution"
                )
            if status.present:
                carriers[corpus_id] = registry._carrier_roots(world.config, corpus_id)[0]
    absent = tuple(corpus_id for corpus_id in covered if corpus_id not in carriers)

    captured: dict[str, dict[str, Node]] = {}
    states: dict[str, str] = {}
    live: dict[str, ReadView] = {}
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        state = _root_state_for(carrier, world._corpus_executor_factory)
        with state.lock.capture():
            before = registry.corpus_state_identity(carrier)
            view = ReadView.opened_at(carrier)
            view._require_base_pin()
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole open is discarded and nothing is served"
                )
        captured[corpus_id] = {node.uid: node for node in records}
        states[corpus_id] = before
        live[corpus_id] = view

    mapped: dict[str, set[str]] = {}
    for address, (corpus_id, uid) in recorded.items():
        mapped.setdefault(corpus_id, set()).add(uid)
        if corpus_id not in captured:
            continue
        node = captured[corpus_id].get(uid)
        if node is None or (address != node.id and address not in node.deprecated_ids):
            raise ResolutionRefused(
                f"{address}: {corpus_id}: {carriers[corpus_id]}: the present carrier does not hold uid {uid!r} "
                "under this address as the epoch mapped it; a carrier that disagrees with the publication is "
                "corruption and not an absence"
            )

    drift: list[DriftReport] = []
    held: dict[str, dict[str, Node]] = {}
    for corpus_id in sorted(captured):
        known = mapped.get(corpus_id, set())
        unmapped = tuple(sorted(uid for uid in captured[corpus_id] if uid not in known))
        if unmapped or states[corpus_id] != published_states[corpus_id]:
            drift.append(DriftReport(corpus_id, published_states[corpus_id], states[corpus_id], unmapped))
        held[corpus_id] = {uid: node for uid, node in captured[corpus_id].items() if uid in known}

    inbound: dict[tuple[str, str], list[ResolvedEdge]] = {}
    for corpus_id in sorted(held):
        for uid in sorted(held[corpus_id]):
            node = held[corpus_id][uid]
            for relation in node.relations:
                target = recorded.get(relation.target)
                if target is None:
                    continue  # dangling at the world layer: nothing the epoch recorded
                inbound.setdefault(target, []).append(ResolvedEdge(relation=relation, source_uid=uid, target_uid=target[1]))

    producers: dict[tuple[str, str], tuple[str, ...]] = {}
    entries = cast(tuple[Mapping[str, object], ...], published.documents["producers-map.yaml"]["producers"])
    for entry in entries:
        located = recorded.get(cast(str, entry["dataset"]))
        if located is not None:
            producers[located] = tuple(cast(list[str], entry["runs"]))

    return WorldReadView._opened(
        _MINT,
        stamp=stamp,
        recorded=recorded,
        held=held,
        absent=absent,
        drift=tuple(drift),
        inbound={key: tuple(edges) for key, edges in inbound.items()},
        producers=producers,
        live=live,
    )
```

Then in `python/src/beliefs/world/__init__.py` add, beside the existing `read` re-exports: `from beliefs.world.view import DriftReport, WorldReadView, open_world_view` and the three names to `__all__`. In `corpus.py`, widen `_producer_ids`'s annotation to `"ReadView | _ImportView | _CheckView | WorldReadView"` with `if TYPE_CHECKING: from beliefs.world.view import WorldReadView` (the string form avoids the import cycle: `view.py` imports `corpus`).

- [ ] **Step 4: Run the tests**

Run: `uv run --frozen pytest tests/test_world_view.py -q -p no:cacheprovider`
Expected: PASS, 9 tests.

- [ ] **Step 5: Lint and commit**

```bash
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/world/view.py python/src/beliefs/world/__init__.py python/src/beliefs/corpus.py python/tests/test_world_view.py
git commit -m "feat(world): open a world read view as a per-corpus coherent capture bound to one epoch"
```

---

### Task 4: The world inbound index and published producers

**Files:**
- Modify: `python/src/beliefs/world/view.py` (already built in Task 3; this task tests and hardens it)
- Test: `python/tests/test_world_view.py` (append)

**Interfaces:**
- Produces: `inbound(ref)` answering for `Resolved` and `NotPresent` refs from mapped sources only; `published_producers(dataset)` from the epoch's producers map.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_world_view.py`:

```python
def chain_nodes():
    """D0 -> R1 -> D1 -> R2 -> D2, R1 and D1 placed in BETA by the caller."""
    d0 = stored.dataset_node("d0", title="d0")
    r1 = stored.run_node("r1", title="r1", spec="s", transforms=[d0.id], produces=["dataset:d1"])
    d1 = stored.dataset_node(
        "d1", title="d1",
        basis={"tag": "single", "routes": [{"identity": "route:d1", "run": r1.id, "ancestor": d0.id, "transforms": [d0.id]}]},
    )
    r2 = stored.run_node("r2", title="r2", spec="s", transforms=[d1.id], produces=["dataset:d2"])
    d2 = stored.dataset_node(
        "d2", title="d2",
        basis={"tag": "single", "routes": [{"identity": "route:d2", "run": r2.id, "ancestor": d1.id, "transforms": [d1.id]}]},
    )
    return d0, r1, d1, r2, d2


def chain_world(tmp_path: Path):
    d0, r1, d1, r2, d2 = chain_nodes()
    coverage = (ALPHA, BETA)
    roots = corpora(tmp_path, {ALPHA: (d0, r2, d2), BETA: (r1, d1)})
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    return world, roots, publish(world, coverage, bindings)


class TestCrossCorpusEdges:
    def test_inbound_crosses_the_corpus_edge_and_is_dangling_locally(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        view = open_world_view(world, published)
        producers_of_d1 = {e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "produces"}
        assert producers_of_d1 == {"run:r1"}
        producers_of_d2 = {e.relation.source for e in view.inbound("dataset:d2") if e.relation.predicate == "produces"}
        assert producers_of_d2 == {"run:r2"}
        # r2 transforms d1, which BETA holds: found at the world layer, dangling in ALPHA alone.
        assert {e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "transforms"} == {"run:r2"}
        assert ReadView.opened_at(roots[ALPHA]).inbound("dataset:d1") == []

    def test_inbound_to_an_absent_record_still_finds_present_sources(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert type(view.locate("dataset:d1")) is read.NotPresent
        assert {e.relation.source for e in view.inbound("dataset:d1")} == {"run:r2"}
        assert view.inbound("dataset:never-observed") == []

    def test_a_drift_source_files_no_edge_and_producers_excludes_it(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        writer = CorpusWriter(roots[ALPHA], DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY)
        writer.add(stored.run_node("late", title="late", spec="s", produces=["dataset:d2"]))
        view = open_world_view(world, published)
        assert "run:late" not in {e.relation.source for e in view.inbound("dataset:d2")}
        assert view.producers("dataset:d2") == ("run:r2",)

    def test_a_drift_copy_of_a_foreign_target_does_not_hide_the_edge(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        writer = CorpusWriter(roots[ALPHA], DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY)
        writer.add(stored.dataset_node("d1", title="a drift copy of BETA's d1"))
        view = open_world_view(world, published)
        assert view.corpus_of("dataset:d1") == BETA
        assert {e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "transforms"} == {"run:r2"}

    def test_published_producers_survive_an_absent_carrier(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert view.published_producers("dataset:d1") == ("run:r1",)
        assert view.published_producers("dataset:d2") == ("run:r2",)
        assert view.published_producers("dataset:never-observed") == ()
```

- [ ] **Step 2: Run to verify which fail**

Run: `uv run --frozen pytest tests/test_world_view.py -k CrossCorpusEdges -q -p no:cacheprovider`
Expected: most PASS against Task 3's index; `test_a_drift_copy_of_a_foreign_target_does_not_hide_the_edge` fails at the corruption check if the drift copy's uid collides — it will not, `dataset_node` mints a fresh uid. Any failure here is a defect in Task 3's index; fix there, not by weakening the test.

- [ ] **Step 3: Harden**

`corpus_at` pins every fixture corpus to `pins_for(WITH_BIOLOGY)`, which is why the writers above are built with `profile=WITH_BIOLOGY`: `require_pins_agree` refuses any other profile at the write. Keep the index logic as written; a failure here is a defect in Task 3's index.

- [ ] **Step 4: Run and commit**

```bash
uv run --frozen pytest tests/test_world_view.py -q -p no:cacheprovider
git add python/tests/test_world_view.py python/src/beliefs/world/view.py
git commit -m "test(world): the world inbound index crosses corpora and excludes drift on both ends"
```

---

### Task 5: Widen the adjacencies and the `supersedes` closure (W10)

**Files:**
- Modify: `python/src/beliefs/corpus.py:724-845` (`RelationAdjacency.__init__`, `LineageAdjacency.__init__`, `_DerivedFromAdjacency`, `derived_from`, `superseded_by`) — annotations only
- Test: `python/tests/test_world_view.py` (append)

**Interfaces:**
- Consumes: `WorldReadView.get/resolve/inbound/live_id`.
- Produces: `closure(root, LineageAdjacency(world_view))` and `RelationAdjacency(world_view, "produces", "inbound")` crossing corpora.

- [ ] **Step 1: Write the failing test**

```python
class TestW10:
    def test_the_world_closure_is_complete_and_the_local_one_truncates(self, tmp_path):
        from beliefs.corpus import LineageAdjacency, RelationAdjacency
        from beliefs.traversal import closure

        world, roots, published = chain_world(tmp_path)
        view = open_world_view(world, published)
        world_reach = closure("dataset:d2", LineageAdjacency(view))
        assert set(world_reach.reached) == {"dataset:d1", "dataset:d0"}
        assert world_reach.unresolved == ()
        local_reach = closure("dataset:d2", LineageAdjacency(ReadView.opened_at(roots[ALPHA])))
        assert set(local_reach.reached) == set()
        assert local_reach.unresolved != ()
        produced = closure("dataset:d1", RelationAdjacency(view, "produces", "inbound"))
        assert set(produced.reached) == {"run:r1"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --frozen pytest tests/test_world_view.py -k W10 -q -p no:cacheprovider`
Expected: pyright would already flag the type; at runtime it may PASS by duck typing. If it passes, that is the point of this task being annotations: proceed to Step 3 and confirm pyright is green after.

- [ ] **Step 3: Widen the annotations**

In `corpus.py`, add under the existing `TYPE_CHECKING` block `from beliefs.world.view import WorldReadView`, define once near the top `AnyReadView = "ReadView | WorldReadView"` is not valid — instead annotate each site with the string `"ReadView | WorldReadView"`: `RelationAdjacency.__init__(self, view: "ReadView | WorldReadView", …)`, `LineageAdjacency.__init__(self, view: "ReadView | WorldReadView")`, `_DerivedFromAdjacency.__init__`, `derived_from(view: "ReadView | WorldReadView", dataset)`, `superseded_by(view: "ReadView | WorldReadView", ref)`. Leave `standing_in_local_view` on `ReadView`.

- [ ] **Step 4: Run, lint, commit**

```bash
uv run --frozen pytest tests/test_world_view.py tests/test_corpus_traversal.py -q -p no:cacheprovider
uv run --frozen pyright
git add python/src/beliefs/corpus.py python/tests/test_world_view.py
git commit -m "feat(corpus): the adjacencies and the supersedes closure accept the world read view (W10)"
```

---

### Task 6: Absence in the lineage snapshot

**Files:**
- Modify: `python/src/beliefs/lineage.py` (`Producer`, `LineageSnapshot`, `Certification`, `DIVERGENCE_STATES`, `divergence_state`, `_closure`, `certify`, `_producer_projection`, `snapshot_projection`, `__all__`)
- Test: `python/tests/test_lineage.py` (append)

**Interfaces:**
- Produces: `Absence(ref, corpus_id)`; `Producer(stored_run, resolved_run, transforms, absent=())`; `LineageSnapshot(roots, bases, producers, not_present={})`; `Certification(state, findings, absent=())`; `divergence_state(...) -> "divergent" | "undiverged" | "incomplete"`; projections with `"absent"` and `"not_present"` members.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_lineage.py`:

```python
from beliefs.lineage import Absence  # noqa: E402


class TestAbsenceGatesDivergence:
    def test_an_absent_producer_is_incomplete_never_divergent(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "a", transforms=("a",)),))},
            producers={"d": (Producer(stored_run="run:gone", resolved_run=None, transforms=(), absent=("beta",)),)},
            not_present={"run:gone": "beta"},
        )
        assert divergence_state(snapshot, "d") == "incomplete"
        result = certify(snapshot, ("d",), ())
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings and "lineage-divergent" not in result.findings
        assert result.absent == (Absence("run:gone", "beta"),)
        assert snapshot_projection(snapshot)["divergence"] == {"d": "incomplete"}

    def test_a_present_producer_still_compares(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "a", transforms=("a",)),))},
            producers={"d": (Producer(stored_run="run-d", resolved_run="run-d", transforms=("other",)),)},
        )
        assert divergence_state(snapshot, "d") == "divergent"


class TestAbsenceIsCollectedFromReferences:
    def test_a_missing_ancestor_and_run_are_named_though_never_reached(self):
        snapshot = LineageSnapshot(
            roots=("d",),
            bases={"d": Basis(tag="single", routes=(route("d", "dataset:anc", resolved=False),))},
            producers={},
            not_present={"run-d": "beta", "dataset:anc": "beta"},
        )
        result = certify(snapshot, ("d",), ())
        assert set(result.absent) == {Absence("run-d", "beta"), Absence("dataset:anc", "beta")}

    def test_an_absent_root_is_named(self):
        snapshot = LineageSnapshot(roots=("dataset:gone",), bases={}, producers={}, not_present={"dataset:gone": "beta"})
        result = certify(snapshot, ("dataset:gone",), ())
        assert result.state == "not-certified"
        assert "lineage-incomplete" in result.findings
        assert result.absent == (Absence("dataset:gone", "beta"),)

    def test_findings_stay_the_closed_code_set(self):
        with pytest.raises(MalformedSnapshot):
            Certification(state="not-certified", findings=("lineage-incomplete: beta",))


class TestAbsenceIsProjected:
    def test_not_present_moves_the_projection_and_is_encodable(self):
        from beliefs.identity import v1

        with_absence = LineageSnapshot(
            roots=("d",), bases={"d": Basis(tag="single", routes=(route("d", "x", resolved=False),))}, producers={},
            not_present={"x": "beta"},
        )
        unknown = LineageSnapshot(
            roots=("d",), bases={"d": Basis(tag="single", routes=(route("d", "x", resolved=False),))}, producers={},
        )
        a, b = snapshot_projection(with_absence), snapshot_projection(unknown)
        assert a["not_present"] == [{"ref": "x", "corpus_id": "beta"}] and b["not_present"] == []
        assert v1.encode(a) != v1.encode(b)
        producer = Producer(stored_run="r", resolved_run=None, transforms=(), absent=("beta",))
        assert v1.encode({"p": snapshot_projection(LineageSnapshot(roots=(), bases={}, producers={"d": (producer,)}))})
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_lineage.py -q -p no:cacheprovider`
Expected: FAIL, `ImportError: Absence`, then `TypeError` on the new keyword arguments.

- [ ] **Step 3: Implement**

In `lineage.py`:

```python
DIVERGENCE_STATES = ("divergent", "incomplete", "undiverged")


@sealed
@final
@dataclass(frozen=True)
class Absence:
    """One reference the world records in a covered corpus that has no carrier."""

    ref: str
    corpus_id: str
```

`Producer` gains `absent: tuple[str, ...] = ()` with a `__post_init__` refusing anything but `()` or a one-tuple. `LineageSnapshot` gains `not_present: Mapping[str, str] = MappingProxyType({})` after `producers`, wrapped in `MappingProxyType(dict(...))` in `__post_init__`. `Certification` gains `absent: tuple[Absence, ...] = ()` after `findings`, and its `__post_init__` also checks every member is an `Absence`.

`divergence_state`, after the `BasisTagMismatch` guard:

```python
    route = basis.routes[0]
    producers = snapshot.producers.get(dataset, ())
    if (
        route.stored_run in snapshot.not_present
        or route.stored_ancestor in snapshot.not_present
        or any(p.absent for p in producers)
    ):
        return "incomplete"  # an absent input is unknown, not empty: no comparison is made over it
    for producer in producers:
        if producer.transforms != route.transforms:
            return "divergent"
    return "undiverged"
```

In `_closure`, replace the final `if divergence_state(...) == "divergent"` with:

```python
        state = divergence_state(snapshot, dataset)
        if state == "divergent":
            findings.append("lineage-divergent")
        elif state == "incomplete":
            findings.append("lineage-incomplete")
```

and, at the top of the loop body after `inspected.add(dataset)`, add `if dataset in snapshot.not_present: findings.append("lineage-incomplete")` so an absent root reports.

Add the collector and use it in `certify`:

```python
def _absent_references(snapshot: LineageSnapshot, inspected: frozenset[str], roots: tuple[str, ...]) -> tuple[Absence, ...]:
    """§5.1's rule: absence is collected from the references the inspected
    datasets make — never from the inspected set, which a missing run or
    ancestor is by definition never in — plus the absent roots."""
    named: dict[str, str] = {}
    for root in roots:
        if root in snapshot.not_present:
            named[root] = snapshot.not_present[root]
    for dataset in inspected:
        basis = snapshot.bases.get(dataset)
        if basis is not None:
            for r in basis.routes:
                for ref in (r.stored_run, r.stored_ancestor):
                    if ref in snapshot.not_present:
                        named[ref] = snapshot.not_present[ref]
        for producer in snapshot.producers.get(dataset, ()):
            if producer.absent:
                named[producer.stored_run] = producer.absent[0]
    return tuple(Absence(ref, corpus_id) for ref, corpus_id in sorted(named.items()))
```

`certify` becomes:

```python
    closure_a, findings_a = _walk_all(snapshot, roots_a)
    closure_b, findings_b = _walk_all(snapshot, roots_b)
    findings = tuple(dict.fromkeys(findings_a + findings_b))
    absent = _absent_references(snapshot, closure_a | closure_b, roots_a + roots_b)
    if findings:
        return Certification(state="not-certified", findings=findings, absent=absent)
    if closure_a & closure_b:
        return Certification(state="shared-source", findings=(), absent=absent)
    return Certification(state="independent", findings=(), absent=absent)
```

Projections: `_producer_projection` adds `"absent": list(producer.absent)`; `snapshot_projection` adds `"not_present": [{"ref": ref, "corpus_id": cid} for ref, cid in sorted(snapshot.not_present.items())]` and its docstring drops the "Deferred" sentence in favour of "the absent corpus per not-present reference (world-resolution slice 1 §5.1)". Add `Absence` to `__all__`.

- [ ] **Step 4: Run the lineage tests and the fast loop**

Run: `uv run --frozen pytest tests/test_lineage.py -q -p no:cacheprovider && uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py -q -p no:cacheprovider`
Expected: PASS. Every existing snapshot digest is unchanged because an empty `not_present` projects as `[]` and `"absent": []` — if any digest-pinning test moves, the projection gained a member for the existing case; the R23 coverage clause wants a *different* digest only when absence is present, so keep the empty case's digest by construction: confirm the failure is a pinned literal in a test, then re-pin it with a dated comment naming this slice, and only if the pinned value is a fixture literal rather than a frozen record.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/lineage.py python/tests/test_lineage.py
git commit -m "feat(lineage): absence is a named corpus that gates divergence and survives into certification"
```

---

### Task 7: `lineage_snapshot`, `_producers_of` and `run_value` over the world view

**Files:**
- Modify: `python/src/beliefs/corpus.py:986-1062` (`run_value`, `lineage_snapshot`, `_producers_of`)
- Test: `python/tests/test_world_view.py` (append)

**Interfaces:**
- Consumes: `WorldReadView.locate`, `corpus_of`, `published_producers`; `lineage.Producer.absent`, `LineageSnapshot.not_present`.
- Produces: `lineage_snapshot(view: ReadView | WorldReadView, roots)` filling `not_present`; `_producers_of(view, dataset)` unioning published producers; `run_value(view: ReadView | WorldReadView, ref)`.

- [ ] **Step 1: Write the failing tests**

```python
class TestLineageSnapshotOverTheWorld:
    def test_absence_is_entered_with_its_corpus_and_only_from_not_present(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import certify

        world, roots, published = chain_world(tmp_path)
        complete = lineage_snapshot(open_world_view(world, published), ["dataset:d2"])
        assert complete.not_present == {}
        assert certify(complete, ("dataset:d2",), ()).state == "independent"

        make_absent(roots, BETA)
        partial = lineage_snapshot(open_world_view(world, published), ["dataset:d2"])
        assert partial.not_present == {"dataset:d1": BETA}
        (route,) = partial.bases["dataset:d2"].routes
        assert route.resolved_run == "run:r2" and route.resolved_ancestor is None
        result = certify(partial, ("dataset:d2",), ())
        assert result.state == "not-certified" and "lineage-incomplete" in result.findings
        assert result.absent == (Absence("dataset:d1", BETA),)
        assert snapshot_projection(partial) != snapshot_projection(complete)

    def test_a_refusal_is_not_absence(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.errors import SemanticHashStale

        from nodes.core.corpus import Corpus
        from nodes.core.frontmatter import node_to_markdown

        world, roots, published = chain_world(tmp_path)
        node = Corpus(roots[ALPHA]).get("dataset:d2")
        node.facets["dataset"]["resources"] = [{"digest": "f" * 64}]
        (roots[ALPHA] / "dataset" / "d2.md").write_text(node_to_markdown(node))
        view = open_world_view(world, published)
        with pytest.raises(SemanticHashStale):
            lineage_snapshot(view, ["dataset:d2"])

    def test_a_published_producer_survives_its_absent_carrier(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import divergence_state

        d3 = stored.dataset_node(
            "d3", title="d3",
            basis={"tag": "single", "routes": [{"identity": "route:d3", "run": "run:r3", "ancestor": "dataset:d0", "transforms": ["dataset:d0"]}]},
        )
        d0 = stored.dataset_node("d0", title="d0")
        r3 = stored.run_node("r3", title="r3", spec="s", transforms=[d0.id], produces=[d3.id])
        roots = corpora(tmp_path, {ALPHA: (d0, d3), BETA: (r3,)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        present = lineage_snapshot(open_world_view(world, published), ["dataset:d3"])
        assert [p.absent for p in present.producers["dataset:d3"]] == [()]
        assert divergence_state(present, "dataset:d3") == "undiverged"

        make_absent(roots, BETA)
        gone = lineage_snapshot(open_world_view(world, published), ["dataset:d3"])
        (producer,) = gone.producers["dataset:d3"]
        assert producer.stored_run == "run:r3" and producer.resolved_run is None and producer.absent == (BETA,)
        assert gone.not_present == {"run:r3": BETA}
        assert divergence_state(gone, "dataset:d3") == "incomplete"
        assert snapshot_projection(gone)["divergence"] == {"dataset:d3": "incomplete"}
```

Add `from beliefs.lineage import Absence, snapshot_projection` to the test module's imports.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_world_view.py -k LineageSnapshotOverTheWorld -q -p no:cacheprovider`
Expected: FAIL — `not_present` empty; the absent producer missing.

- [ ] **Step 3: Implement**

In `corpus.py`, add a helper below `run_value`:

```python
def _absence_of(view: "ReadView | WorldReadView", ref: str) -> str | None:
    """The corpus a world view records `ref` in when that corpus has no
    carrier, else `None`. Over a corpus view there is no world to ask. Only a
    `NotPresent` answer counts; a refusal from the view propagates."""
    from beliefs.world.read import NotPresent
    from beliefs.world.view import WorldReadView

    if not isinstance(view, WorldReadView):
        return None
    return view.corpus_of(ref) if type(view.locate(ref)) is NotPresent else None
```

`lineage_snapshot`:

```python
def lineage_snapshot(view: "ReadView | WorldReadView", roots: Sequence[str]) -> LineageSnapshot:
    adjacency = LineageAdjacency(view)
    inspected: list[str] = []
    not_present: dict[str, str] = {}
    for root in roots:
        for dataset in (root, *closure(root, adjacency).reached):
            if dataset not in inspected:
                inspected.append(dataset)

    bases: dict[str, Basis] = {}
    producers: dict[str, tuple[Producer, ...]] = {}
    for dataset in inspected:
        if not view.holds(dataset):
            corpus_id = _absence_of(view, dataset)
            if corpus_id is not None:
                not_present[dataset] = corpus_id
            continue
        node = view.get(dataset)
        routes = []
        for route in stored.basis_routes(node):
            run, ancestor = str(route.get("run", "")), str(route.get("ancestor", ""))
            for ref in (run, ancestor):
                corpus_id = _absence_of(view, ref)
                if corpus_id is not None:
                    not_present[ref] = corpus_id
            routes.append(Route(
                dataset=dataset, stored_run=run, resolved_run=view.resolve(run),
                stored_ancestor=ancestor, resolved_ancestor=view.resolve(ancestor),
                transforms=tuple(str(entry) for entry in route.get("transforms", []) or ()),
            ))
        facet = stored.lineage_basis(node)
        if facet is not None and routes:
            bases[dataset] = Basis(tag=str(facet.get("tag", "single")), routes=tuple(routes))
        found = _producers_of(view, dataset)
        for producer in found:
            if producer.absent:
                not_present[producer.stored_run] = producer.absent[0]
        producers[dataset] = tuple(found)
    return LineageSnapshot(roots=tuple(roots), bases=bases, producers=producers, not_present=not_present)
```

`_producers_of`:

```python
def _producers_of(view: "ReadView | WorldReadView", dataset: str) -> list[Producer]:
    producers: list[Producer] = []
    for edge in view.inbound(dataset):
        if edge.relation.predicate != stored.PRODUCES:
            continue
        run_ref = edge.relation.source
        resolved = view.resolve(run_ref)
        transforms = () if resolved is None else stored.inputs_of(view.get(resolved), stored.TRANSFORMS)
        producers.append(Producer(stored_run=run_ref, resolved_run=resolved, transforms=transforms))
    from beliefs.world.view import WorldReadView

    if isinstance(view, WorldReadView):
        seen = {p.stored_run for p in producers}
        for run in view.published_producers(dataset):
            if run in seen:
                continue
            resolved = view.resolve(run)
            if resolved is not None:
                producers.append(Producer(stored_run=run, resolved_run=resolved, transforms=stored.inputs_of(view.get(resolved), stored.TRANSFORMS)))
                continue
            corpus_id = _absence_of(view, run)
            if corpus_id is not None:
                producers.append(Producer(stored_run=run, resolved_run=None, transforms=(), absent=(corpus_id,)))
    return producers
```

`run_value`'s annotation widens to `"ReadView | WorldReadView"`; its body is unchanged, and its docstring's last sentence becomes: "Over a world view the filter is the same and the absence is reported by `gather`, which collects every input whose `locate` is `NotPresent`."

- [ ] **Step 4: Run, lint, commit**

```bash
uv run --frozen pytest tests/test_world_view.py tests/test_lineage.py tests/test_corpus_traversal.py -q -p no:cacheprovider
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/corpus.py python/tests/test_world_view.py
git commit -m "feat(corpus): the lineage snapshot names absent corpora and keeps published producers (S5, R23 coverage)"
```

---

### Task 8: The resolution snapshot's third state (D3)

**Files:**
- Modify: `python/src/beliefs/resolution.py` (`_BoundVocabulary`, `build_snapshot`, `ResolutionSnapshot.resolve`, module docstring lines 26-34)
- Test: `python/tests/test_resolution_snapshot.py` (new)

**Interfaces:**
- Produces: `build_snapshot(*, readable=None, unreadable=(), not_present={})` with `not_present: Mapping[VocabularyBinding, str]`; `_BoundVocabulary(state, terms, absent)`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_resolution_snapshot.py`:

```python
"""D3's remaining arm: `not-present` produced, the five outcomes distinct, and
every availability state digested apart."""

import pytest
from test_evaluation import EX, GENE  # the bindings the evaluation tests already declare

from beliefs.errors import ResolutionError
from beliefs.resolution import TermOutcome, build_snapshot


def test_not_present_is_produced_and_carries_its_corpus():
    snapshot = build_snapshot(not_present={EX: "beta"})
    assert snapshot.resolve(EX, GENE) is TermOutcome.NOT_PRESENT
    assert snapshot.projection()["bindings"][0]["state"] == "not-present"
    assert snapshot.projection()["bindings"][0]["absent"] == ["beta"]


def test_the_five_outcomes_are_pairwise_distinct():
    readable = build_snapshot(readable={EX: [GENE]})
    outcomes = {
        readable.resolve(EX, GENE),
        readable.resolve(EX, "EX:other"),
        build_snapshot().resolve(EX, GENE),
        build_snapshot(unreadable=[EX]).resolve(EX, GENE),
        build_snapshot(not_present={EX: "beta"}).resolve(EX, GENE),
    }
    assert outcomes == set(TermOutcome)


def test_the_identity_moves_across_the_three_availability_states():
    identities = {
        build_snapshot(readable={EX: []}).identity,
        build_snapshot(unreadable=[EX]).identity,
        build_snapshot(not_present={EX: "beta"}).identity,
        build_snapshot(not_present={EX: "gamma"}).identity,
    }
    assert len(identities) == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"readable": {EX: []}, "unreadable": [EX]},
        {"readable": {EX: []}, "not_present": {EX: "beta"}},
        {"unreadable": [EX], "not_present": {EX: "beta"}},
    ],
)
def test_overlapping_inputs_refuse(kwargs):
    with pytest.raises(ResolutionError):
        build_snapshot(**kwargs)
```

If `test_evaluation` does not export `EX`/`GENE` at module level, import them from wherever that module defines them (grep `^EX =`); do not redefine them.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_resolution_snapshot.py -q -p no:cacheprovider`
Expected: FAIL, `TypeError: unexpected keyword argument 'not_present'`.

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True)
class _BoundVocabulary:
    """What the snapshot holds for one binding: its terms, or which of the two
    ways it could not be read — bytes not held here, or the corpus that holds
    them absent from this world."""

    state: str
    """`readable` | `not-available` | `not-present`."""
    terms: frozenset[str]
    absent: tuple[str, ...]
    """`()`, or the one absent corpus id — `not-present` only."""

    @property
    def readable(self) -> bool:
        return self.state == "readable"

    def projection(self) -> dict[str, object]:
        if self.state == "readable":
            return {"state": "readable", "terms": sorted(self.terms), "absent": []}
        return {"state": self.state, "terms": [], "absent": list(self.absent)}
```

`resolve`, after the `NOT_CONSULTED` return:

```python
        if state.state == "not-present":
            # The world records the binding's dataset in a covered corpus that has no
            # carrier here — D3's world-level arm, produced by the world read view.
            return TermOutcome.NOT_PRESENT
        if state.state == "not-available":
            return TermOutcome.NOT_AVAILABLE
        return TermOutcome.MEMBER if canonical(term) in state.terms else TermOutcome.NOT_MEMBER
```

`build_snapshot`:

```python
def build_snapshot(
    *,
    readable: Mapping[VocabularyBinding, Iterable[str]] | None = None,
    unreadable: Iterable[VocabularyBinding] = (),
    not_present: Mapping[VocabularyBinding, str] | None = None,
) -> ResolutionSnapshot:
    table: dict[VocabularyBinding, _BoundVocabulary] = {}

    def _place(binding: VocabularyBinding, entry: _BoundVocabulary) -> None:
        _require_binding(binding)
        if binding in table:
            raise ResolutionError(
                f"binding {binding.projection()} is given in more than one availability state "
                f"({table[binding].state} and {entry.state}). One binding has one state; a snapshot that "
                "carried two would let a caller pick."
            )
        table[binding] = entry

    for binding, terms in (readable or {}).items():
        _place(binding, _BoundVocabulary(
            state="readable",
            terms=frozenset(_require_term(term, binding) for term in _require_terms(terms, binding)),
            absent=(),
        ))
    for binding in unreadable:
        _place(binding, _BoundVocabulary(state="not-available", terms=frozenset(), absent=()))
    for binding, corpus_id in (not_present or {}).items():
        if type(corpus_id) is not str or not corpus_id:
            raise ResolutionError(f"{binding.projection()}: a not-present binding names the absent corpus")
        _place(binding, _BoundVocabulary(state="not-present", terms=frozenset(), absent=(corpus_id,)))

    snapshot = ResolutionSnapshot._built(_MINT, bindings=MappingProxyType(dict(table)), identity="")
    object.__setattr__(snapshot, "identity", v1.digest(SNAPSHOT_DOMAIN, snapshot.projection()))
    return snapshot
```

Rewrite the module docstring's paragraph at lines 26–34 to say `not-present` is produced by `build_snapshot(not_present=…)` from the world read view's `locate`, and update the inline comment near `NOT_AVAILABLE`.

- [ ] **Step 4: Run the new tests and the fast loop**

Run: `uv run --frozen pytest tests/test_resolution_snapshot.py -q -p no:cacheprovider && uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py -q -p no:cacheprovider`
Expected: PASS. Existing readable/unreadable snapshot identities move because the projection gained `state` and `absent`; any test pinning a literal snapshot identity must be re-pinned with a comment citing this task. `tests/test_arm_staleness.py` must stay green — if an N2 arm's `before` named `{"readable": False}`, re-target it in the guard's `_LIVE_SABOTAGES` per the frozen-guard doctrine §7, never in the declaration file.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/resolution.py python/tests/test_resolution_snapshot.py
git commit -m "feat(resolution): not-present is a digested third availability state (D3)"
```

---

### Task 9: Attribution and `node_corpus` as a tuple-valued mapping

**Files:**
- Modify: `python/src/beliefs/consulted.py:45-54`, `python/src/beliefs/belief.py` (`SuppliedContext.node_corpus`, `NoBelief`)
- Modify: every fixture that builds `node_corpus`: `python/tests/verification_fixtures.py:189`, `python/tests/test_evaluation.py`, `python/tests/test_belief.py:162`, `python/tests/domain_facet_fixtures.py:155`, `python/tests/acceptance/test_deletion_acceptance.py:457`, `python/tests/test_world_derive.py:303` (run `grep -rn "node_corpus=" python/tests` for the complete list)
- Test: `python/tests/test_consulted.py` (append; create if absent)

**Interfaces:**
- Produces: `consulted_contracts(node_corpus: Mapping[str, tuple[str, ...]], …)`; `SuppliedContext.node_corpus: Mapping[str, tuple[str, ...]]`; `NoBelief(reason, detail="")`.

- [ ] **Step 1: Write the failing test**

```python
def test_one_identity_held_in_two_corpora_consults_both_and_refuses_disagreement():
    from dataclasses import replace

    from beliefs.consulted import consulted_contracts
    from beliefs.errors import ContractDisagreement
    from profiles import PROFILE, pins_for  # the same objects test_evaluation uses

    same = pins_for(PROFILE)
    other = replace(same, science_contract="science:" + "0" * 64)
    node_corpus = {"a" * 64: ("c1", "c2")}
    consulted = consulted_contracts(claims={}, profile=PROFILE, node_corpus=node_corpus, pins={"c1": same, "c2": same}, closure_nodes=("a" * 64,))
    assert consulted[0][0] == "science"
    with pytest.raises(ContractDisagreement):
        consulted_contracts(claims={}, profile=PROFILE, node_corpus=node_corpus, pins={"c1": same, "c2": other}, closure_nodes=("a" * 64,))
```

Adjust the import of `PROFILE`/`pins_for` to wherever `test_evaluation.py` gets them.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --frozen pytest tests/test_consulted.py -q -p no:cacheprovider`
Expected: FAIL, `TypeError: unhashable type` or a `sorted` over tuples error at `consulted.py:54`.

- [ ] **Step 3: Implement**

`consulted.py`:

```python
    node_corpus: Mapping[str, tuple[str, ...]],
    ...
    corpora = sorted({corpus for node in closure_nodes if node in node_corpus for corpus in node_corpus[node]}) or sorted(pins)
```

`belief.py`: `node_corpus: Mapping[str, tuple[str, ...]]`, and in `__post_init__` refuse an entry that is not a non-empty tuple of strings with `MalformedRecord("node_corpus attributes each node to a non-empty tuple of corpus ids")`. `NoBelief` gains `detail: str = ""` after `reason`. Update every fixture: `{identity: ("c1",) for identity in identities}` and the like.

- [ ] **Step 4: Run the fast loop and commit**

```bash
uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py -q -p no:cacheprovider
uv run --frozen ruff check . && uv run --frozen pyright
git add -A python/src/beliefs/consulted.py python/src/beliefs/belief.py python/tests
git commit -m "feat(consulted): a node may be attributed to more than one corpus, and every one is consulted"
```

---

### Task 10: The evaluation seam over the world view

**Files:**
- Modify: `python/src/beliefs/evaluation.py` (`EvaluationInputs`, `gather`, `evaluate_over`, imports)
- Modify: `python/src/beliefs/belief.py` docstring at lines 88–91 (`unavailable-corpus-absent` is now reachable)
- Test: `python/tests/test_world_view.py` (append)

**Interfaces:**
- Consumes: `WorldReadView.corpus_of/locate/corpus_view/get`; `corpus._absence_of` (Task 7); `facet_read.read_observed_facets`, `facet_read.FACET_READ_DOMAIN`; `identity.v1`.
- Produces: `gather(view: ReadView | WorldReadView, …)` returning `EvaluationInputs` with a new member `absent: tuple[tuple[str, str], ...]` of `(ref, corpus_id)`; `evaluate_over(view: ReadView | WorldReadView, …)` returning `NoBelief("unavailable-corpus-absent", detail=…)`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_world_view.py`. The scenario is `domain_facet_fixtures.seed` — a proposition, two observed datasets (`dataset:d-a` carrying the namespaced `biology/gene-axis` facet), two runs, two assessments and two verifications — authored into a scratch directory, then placed across two corpora with `dataset:d-a` in `BETA` and everything else in `ALPHA`, so the run in `ALPHA` observes a dataset the other corpus holds.

```python
from dataclasses import replace  # noqa: E402

from domain_facet_fixtures import kwargs_for, profile_with, seed  # noqa: E402
from fixtures_cut4 import reopen  # noqa: E402
from nodes.core.frontmatter import node_to_markdown  # noqa: E402

from beliefs.corpus import lineage_snapshot  # noqa: E402


def split_evaluation_world(tmp_path: Path):
    """`seed`'s corpus split across two carriers: `dataset:d-a` in BETA, the rest in ALPHA."""
    scratch = tmp_path / "scratch"
    seeded = seed(scratch, axis="rows")
    nodes = list(seeded.iter_stored())
    d_a = [n for n in nodes if n.id == "dataset:d-a"]
    rest = [n for n in nodes if n.id != "dataset:d-a"]
    roots = corpora(tmp_path, {ALPHA: tuple(rest), BETA: tuple(d_a)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    return world, roots, published


def world_kwargs(view, profile):
    """`kwargs_for` over the world view: attribution derived, both corpora pinned alike."""
    kwargs = kwargs_for(view, profile)
    context = replace(
        kwargs["context"],
        snapshot=lineage_snapshot(view, ("dataset:d-a", "dataset:d-b")),
        retractions=replace(kwargs["context"].retractions, coverage=(ALPHA, BETA)),
        node_corpus={},
        pins={ALPHA: kwargs["context"].pins["c1"], BETA: kwargs["context"].pins["c1"]},
    )
    return {**kwargs, "context": context}


class TestEvaluationOverTheWorld:
    def test_a_belief_over_two_corpora_attributes_at_the_read(self, tmp_path):
        from beliefs.belief import Belief
        from beliefs.evaluation import evaluate_over, gather

        world, _roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.absent == ()
        assert ("biology", kwargs["context"].pins[ALPHA].domains["biology"]) in inputs.consulted
        assert len(inputs.observed_facets) == 1  # d-a's gene-axis row, read through BETA's own ReadView
        result = evaluate_over(view, "proposition:p", **kwargs)
        assert isinstance(result, Belief)

    def test_an_absent_input_corpus_is_the_banked_reason(self, tmp_path):
        from beliefs.belief import NoBelief
        from beliefs.evaluation import evaluate_over

        world, roots, published = split_evaluation_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        result = evaluate_over(view, "proposition:p", **world_kwargs(view, profile_with()))
        assert isinstance(result, NoBelief)
        assert result.reason == "unavailable-corpus-absent" and BETA in result.detail

    def test_a_supplied_attribution_over_a_world_view_refuses(self, tmp_path):
        from beliefs.errors import MalformedRecord
        from beliefs.evaluation import gather

        world, _roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        supplied = replace(kwargs["context"], node_corpus={"anything": (ALPHA,)})
        with pytest.raises(MalformedRecord):
            gather(view, "proposition:p", context=supplied, profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])

    def test_a_facet_read_is_held_to_the_capture(self, tmp_path):
        """A namespaced facet is not under the semantic hash: editing it after the
        capture leaves `get` content-valid and the address unchanged, and only the
        row-set comparison sees it. A whitespace-only rewrite keeps the row set and
        must not refuse."""
        from beliefs.errors import CaptureDrift
        from beliefs.evaluation import gather

        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        path = roots[BETA] / "dataset" / "d-a.md"
        path.write_text(path.read_text() + "\n")
        gather(view, "proposition:p", context=kwargs["context"], profile=profile,
               resolution=kwargs["resolution"], binding=kwargs["binding"])
        node = reopen(roots[BETA]).get("dataset:d-a")
        node.facets["biology/gene-axis"]["axis"] = "columns"
        path.write_text(node_to_markdown(node))
        assert view.get("dataset:d-a").facets["biology/gene-axis"]["axis"] == "rows"  # the capture stands
        with pytest.raises(CaptureDrift):
            gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_world_view.py -k EvaluationOverTheWorld -q -p no:cacheprovider`
Expected: FAIL — `read_observed_facets` refuses the world view's type, and `inputs.absent` does not exist.

- [ ] **Step 3: Implement**

In `evaluation.py`, add imports `from nodes.core.node import Node` (if absent), `from beliefs.corpus import _absence_of` (beside the existing `run_value` import), `from beliefs.errors import CaptureDrift, MalformedRecord`, `from beliefs.facet_read import FACET_READ_DOMAIN, read_observed_facets`, `from beliefs.identity import v1`, and under `TYPE_CHECKING` `from beliefs.world.view import WorldReadView`. `EvaluationInputs` gains, after `read_trace`:

```python
    absent: tuple[tuple[str, str], ...] = ()
    """`(ref, corpus_id)` for every input the world records in a covered corpus
    with no carrier. Not a closure member and not a declared read: it is the
    reason no closure was built."""
```

Two helpers above `gather`:

```python
def _expected_facet_rows(node: Node, address: str) -> frozenset[tuple[str, str, str]]:
    """The rows `read_observed_facets` mints over exactly this record, computed
    from the captured node so a live read can be held to the capture."""
    return frozenset(
        (address, key, v1.digest(FACET_READ_DOMAIN, node.facets[key])) for key in node.facets if "/" in key
    )


def _facets_held_to_capture(profile: ProfileSpec, view: "WorldReadView", target: str) -> tuple[FacetRead, ...]:
    """§5.3: the facet read goes through the holding corpus's own `ReadView`
    (B3) and is compared, after it returns, to the rows the captured record
    would mint — additions and removals included. Comparing identities before
    the read would neither bind the payload nor check the read itself."""
    captured = view.get(target)
    address = dataset_address(stored.dataset_declaration(captured))
    rows = read_observed_facets(profile, view.corpus_view(target), target)
    returned = frozenset((row.address, row.key, row.payload_digest) for row in rows)
    expected = _expected_facet_rows(captured, address or "")
    if returned != expected:
        raise CaptureDrift(
            f"{target}: the facet read returned rows {sorted(returned - expected)} the capture lacks and lacked "
            f"rows {sorted(expected - returned)} the capture holds; a write landed after the capture"
        )
    return rows
```

In `gather`: widen the annotation to `"ReadView | WorldReadView"`; add `from beliefs.world.view import WorldReadView` at the top of the body (a runtime import, because `world.view` imports `corpus`); add `world = isinstance(view, WorldReadView)`, `attribution: dict[str, set[str]] = {}`, `absent: list[tuple[str, str]] = []`. Then:

- in the assessment loop, after `matched.append(value)`: `if world: attribution.setdefault(value.identity(), set()).add(view.corpus_of(node.id) or "")`;
- in the run loop, replace `if not view.holds(target): continue` with:

```python
            if not view.holds(target):
                corpus_id = _absence_of(view, target)
                if corpus_id is not None:
                    absent.append((target, corpus_id))
                continue
```

  and after `address` is known: `if world: attribution.setdefault(address, set()).add(view.corpus_of(target) or "")`;
- replace `read_observed_facets(profile, view, target)` with `(_facets_held_to_capture(profile, view, target) if world else read_observed_facets(profile, view, target))`;
- before `consulted_contracts`:

```python
    if world:
        if context.node_corpus:
            raise MalformedRecord(
                "node_corpus is derived from a world read and must be supplied empty; a caller may not relocate a record"
            )
        node_corpus = {node: tuple(sorted(c for c in corpora if c)) for node, corpora in attribution.items()}
    else:
        node_corpus = context.node_corpus
```

  and pass `node_corpus=node_corpus`;
- return `absent=tuple(sorted(set(absent)))`.

In `evaluate_over`: widen the annotation; after the `try` block succeeds:

```python
    if inputs.absent:
        corpora = ", ".join(sorted({corpus_id for _, corpus_id in inputs.absent}))
        return NoBelief("unavailable-corpus-absent", detail=f"inputs recorded in absent corpora: {corpora}")
```

Update `belief.py`'s `NO_BELIEF_REASONS` docstring (lines 88–91): "`unavailable-corpus-absent` is returned by `evaluate_over` over a world read view whose run inputs reach a record the epoch maps to a covered corpus with no carrier (world-resolution slice 1 §5.3)."

- [ ] **Step 4: Run, lint, commit**

```bash
uv run --frozen pytest tests/test_world_view.py tests/test_evaluation.py tests/test_belief.py tests/test_domain_facets.py -q -p no:cacheprovider
uv run --frozen ruff check . && uv run --frozen pyright
git add python/src/beliefs/evaluation.py python/src/beliefs/belief.py python/tests/test_world_view.py
git commit -m "feat(evaluation): evaluate over the world read view, attributing at the read and reporting absent corpora"
```

---

### Task 11: `check_verification` across corpora (R19)

**Files:**
- Modify: `python/src/beliefs/audit.py:101` (`_closure` annotation) and `:116-118` (`check_verification` annotation)
- Test: `python/tests/test_world_view.py` (append)

- [ ] **Step 1: Write the failing test**

```python
from profiles import BASE, pins_for  # noqa: E402
from verification_fixtures import publish_corpus, self_consistent_forgery  # noqa: E402


class TestR19AcrossCorpora:
    def test_a_well_formed_forgery_is_a_finding_and_a_malformed_record_raises(self, tmp_path):
        from beliefs.audit import check_verification
        from beliefs.errors import MalformedRecord

        scratch = tmp_path / "scratch"
        writer = CorpusWriter(scratch, DefaultExecutor, authority=FULL, profile=BASE)
        writer.adopt_manifest(profile=pins_for(BASE))  # the manifest a fresh root needs, as test_relocation._writer does
        published = publish_corpus(writer, publish=True)
        forged = self_consistent_forgery(writer, published.node, mutate=lambda facet: facet.__setitem__("verdict", "failed"))
        nodes = list(reopen(scratch).iter_stored())
        runs = tuple(n for n in nodes if n.kind == "run")
        rest = tuple(n for n in nodes if n.kind != "run")
        roots = corpora(tmp_path, {ALPHA: rest, BETA: runs})
        world = world_over(tmp_path, roots)
        view = open_world_view(world, publish(world, (ALPHA, BETA), hold_shipped(world)))
        assert view.corpus_of(published.node.id) == ALPHA and view.corpus_of(runs[0].id) == BETA

        genuine = check_verification(view, view.get(published.node.id), evidence=published.evidence)
        assert genuine.checked and genuine.contradiction is None

        outcome = check_verification(view, view.get(forged.id), evidence=published.evidence)
        assert outcome.checked and outcome.contradiction is not None
        assert outcome.contradiction.code == "verification-derivation-contradicted"

        malformed = view.get(published.node.id)
        malformed.facets["verification"]["report"] = {"forged": True}
        with pytest.raises(MalformedRecord):
            check_verification(view, malformed, evidence=published.evidence)
```

The nodes `publish_corpus` mints in `scratch` are stamped and carry `BASE`'s pins, so `corpora` can place them under `corpus_at`'s manifest unchanged; the world reads pins from manifests only at admission and capture, and the verification check reads none.

- [ ] **Step 2: Run to verify it fails or passes by duck typing**

Run: `uv run --frozen pytest tests/test_world_view.py -k R19 -q -p no:cacheprovider`
Expected: PASS at runtime is possible — `_closure` only uses `holds`/`get`; pyright is what fails until Step 3. Either way continue.

- [ ] **Step 3: Widen the annotations**

`check_verification(view: "ReadView | _ImportView | WorldReadView", …)` and `_closure(view: "ReadView | _ImportView | WorldReadView", …)`, with `from beliefs.world.view import WorldReadView` under `TYPE_CHECKING`.

- [ ] **Step 4: Run, lint, commit**

```bash
uv run --frozen pytest tests/test_world_view.py tests/test_audit.py -q -p no:cacheprovider && uv run --frozen pyright
git add python/src/beliefs/audit.py python/tests/test_world_view.py
git commit -m "feat(audit): check_verification recomputes across corpora through the world read view (R19)"
```

---

### Task 12: Durable acceptance arms and the cut 23 declarations

**Files:**
- Create: `python/tests/acceptance/test_world_view_acceptance.py`
- Create: `python/tests/acceptance/n2_arms_cut23.py`
- Create: `python/tests/acceptance/test_n2_cut23.py`

**Interfaces:**
- Consumes: Task 1's nine units and freeze sha; every unit test named above as an N2 check.
- Produces: `CUT23_ARMS`, `DECLARATION_UNITS`, `unit_of`, `CO_CITED = ()`.

- [ ] **Step 1: Write the durable acceptance module**

`test_world_view_acceptance.py` re-runs the chain and split-producer scenarios of `test_world_view.py` over corpus roots initialised with `init_corpus_root` under `work_directory` (the `durable_root` pattern in `tests/acceptance/conftest.py`), the world under `root.init_world_root`, records written through `CorpusWriter` with the durable executor, and the epoch built by `root.open_world(config, authority=FULL)`. One test per arm in spec §8, named:

```
test_the_world_closure_is_complete_and_the_local_one_truncates_durably      (W10)
test_the_relation_and_lineage_chains_cross_the_edge_durably                 (S1, S1a)
test_an_absent_corpus_is_lineage_incomplete_naming_it_durably              (S5, R23)
test_a_published_producer_survives_its_absent_carrier_durably              (S5)
test_an_absent_dataset_is_incomplete_without_a_comparison_durably          (S5)
test_absence_names_what_each_root_can_discover_durably                     (S5)
test_a_refusal_is_not_absence_durably                                      (boundary)
test_the_capture_is_coherent_and_drift_is_the_next_opens_durably           (capture)
test_a_returned_object_is_detached_durably                                 (isolation)
test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably (evaluation)
test_check_verification_reports_a_cross_corpus_forgery_durably             (R19)
test_the_three_states_never_collapse_and_removal_is_not_unknown            (W6, over read.resolve_address)
test_duplicate_location_and_corruption_are_distinguished_at_build          (W8b, over epoch.build_epoch)
test_the_five_outcomes_are_produced_and_kept_apart_durably                 (D3)
test_a_facet_read_is_held_to_the_capture_durably                            (evaluation)
```

Each is the unit test's body with the durable fixtures substituted; absence is produced by unlinking the carrier's `corpus.yaml`.

- [ ] **Step 2: Run it on the certified volume**

Run: `SCIENCE_CUT4_ROOT=$(pwd)/../.cut23-acceptance uv run --frozen pytest tests/acceptance/test_world_view_acceptance.py -q -p no:cacheprovider`
Expected: PASS. A refusal from the engine is an error, never a skip.

- [ ] **Step 3: Declare the arms**

`n2_arms_cut23.py`. Every `before` below is a verbatim substring of the code this plan lands (Tasks 3–10); after those tasks, confirm each occurs exactly once with the check in Step 5. Where a landed line differs from the plan's text, the arm follows the landed line — the arm, never the source.

```python
"""Cut 23's nine frozen declaration units and their source sabotages — one arm
per sabotage site the cut document §5 item 4 names."""

from n2_arms import Arm, Sabotage

_VIEW = "world/view.py"
_CORPUS = "corpus.py"
_LINEAGE = "lineage.py"
_RESOLUTION = "resolution.py"
_EVALUATION = "evaluation.py"
_READ = "world/read.py"
_REGISTRY = "world/registry.py"
_A = "acceptance/test_world_view_acceptance.py"

DECLARATION_UNITS: tuple[str, ...] = ("D3", "S1", "S1a", "S5", "W6", "W8b", "W10", "R19", "R23")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    """The unit a lettered row belongs to. `W8b` and `S1a` are units whose names
    end in a letter, so stripping letters would misfile them; the longest unit
    the row spells, exactly or plus one lowercase letter, is the answer."""
    matches = [
        unit for unit in DECLARATION_UNITS
        if row == unit or (row.startswith(unit) and len(row) == len(unit) + 1 and row[-1].islower())
    ]
    return max(matches, key=len)


CUT23_ARMS = (
    Arm(
        row="W10b",
        asserts="map-first resolution: an address the epoch never observed is unknown whatever a carrier holds",
        sabotage=Sabotage(
            module=_VIEW,
            before="        entry = self._recorded.get(ref)\n        if entry is None:\n            return Unknown(self._stamp)\n",
            after=(
                "        entry = self._recorded.get(ref)\n        if entry is None:\n"
                "            for corpus_id, records in self._held.items():\n"
                "                for uid, node in records.items():\n"
                "                    if node.id == ref:\n"
                "                        return Resolved(Location(corpus_id, uid), self._stamp)\n"
                "            return Unknown(self._stamp)\n"
            ),
        ),
        checks=(f"{_A}::test_the_capture_is_coherent_and_drift_is_the_next_opens_durably",),
    ),
    Arm(
        row="W6b",
        asserts="an absent covered corpus is not-present, never unknown",
        sabotage=Sabotage(
            module=_VIEW,
            before="        if corpus_id in self._absent:\n            return NotPresent(self._stamp)\n",
            after="        if corpus_id in self._absent:\n            return Unknown(self._stamp)\n",
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="W10c",
        asserts="get serves the capture, never the live carrier",
        sabotage=Sabotage(
            module=_VIEW,
            before="        node = self._held[located.location.corpus_id][located.location.uid]\n        return validated_node(node).model_copy(deep=True)\n",
            after="        return self._live[located.location.corpus_id].get(ref)\n",
        ),
        checks=(f"{_A}::test_the_capture_is_coherent_and_drift_is_the_next_opens_durably",),
    ),
    Arm(
        row="W10d",
        asserts="the inbound index files mapped sources only",
        sabotage=Sabotage(
            module=_VIEW,
            before="    for corpus_id in sorted(held):\n        for uid in sorted(held[corpus_id]):\n            node = held[corpus_id][uid]\n            for relation in node.relations:\n",
            after="    for corpus_id in sorted(captured):\n        for uid in sorted(captured[corpus_id]):\n            node = captured[corpus_id][uid]\n            for relation in node.relations:\n",
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="W10e",
        asserts="the inbound index resolves targets through the world map, not the local index",
        sabotage=Sabotage(
            module=_VIEW,
            before="                target = recorded.get(relation.target)\n                if target is None:\n                    continue  # dangling at the world layer: nothing the epoch recorded\n",
            after=(
                "                target = recorded.get(relation.target)\n"
                "                if target is None or relation.target in {n.id for n in held[corpus_id].values()} and target[0] != corpus_id:\n"
                "                    continue\n"
            ),
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="W10f",
        asserts="an object that leaves the view is detached",
        sabotage=Sabotage(
            module=_VIEW,
            before="        return validated_node(node).model_copy(deep=True)\n",
            after="        return validated_node(node)\n",
        ),
        checks=(f"{_A}::test_a_returned_object_is_detached_durably",),
    ),
    Arm(
        row="W10",
        asserts="cross-corpus edges are ordinary at the world layer and dangling at the corpus layer",
        sabotage=Sabotage(
            module=_VIEW,
            before="            for edge in self._inbound.get(entry, ())\n",
            after="            for edge in self._inbound.get(entry, ())\n            if edge.source_uid in self._held.get(entry[0], {})\n",
        ),
        checks=(f"{_A}::test_the_world_closure_is_complete_and_the_local_one_truncates_durably",),
    ),
    Arm(
        row="S1",
        asserts="the relation chain crossing corpora returns its full closure",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        for edge in self._view.inbound(ref):\n            if edge.relation.predicate != self._predicate or edge.source_uid is None:\n",
            after="        for edge in self._view.inbound(ref):\n            if edge.relation.predicate != self._predicate or edge.source_uid is None or edge.target_uid is None:\n                continue\n            if type(self._view).__name__ == \"WorldReadView\":\n",
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="S1a",
        asserts="the lineage chain crossing corpora, walked as a facet, returns its full closure",
        sabotage=Sabotage(
            module=_CORPUS,
            before="                        resolved=self._view.resolve(ancestor),\n                        entry=LineageEntry(dataset=node.id, route=index, position=\"ancestor\", target=ancestor),\n",
            after="                        resolved=self._view.resolve(ancestor) if type(self._view).__name__ != \"WorldReadView\" else None,\n                        entry=LineageEntry(dataset=node.id, route=index, position=\"ancestor\", target=ancestor),\n",
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="S5b",
        asserts="absence is entered with its corpus, from a not-present answer only",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            corpus_id = _absence_of(view, dataset)\n            if corpus_id is not None:\n                not_present[dataset] = corpus_id\n            continue\n",
            after="            continue\n",
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="S5c",
        asserts="a published producer survives its absent carrier",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        for run in view.published_producers(dataset):\n",
            after="        for run in ():\n",
        ),
        checks=(f"{_A}::test_a_published_producer_survives_its_absent_carrier_durably",),
    ),
    Arm(
        row="S5d",
        asserts="absence gates divergence: no comparison is made over an absent producer",
        sabotage=Sabotage(
            module=_LINEAGE,
            before="        return \"incomplete\"  # an absent input is unknown, not empty: no comparison is made over it\n",
            after="        pass\n",
        ),
        checks=(f"{_A}::test_a_published_producer_survives_its_absent_carrier_durably",),
    ),
    Arm(
        row="S5e",
        asserts="absence is collected from the inspected datasets' references, not the inspected set",
        sabotage=Sabotage(
            module=_LINEAGE,
            before="    for dataset in inspected:\n        basis = snapshot.bases.get(dataset)\n        if basis is not None:\n            for r in basis.routes:\n                for ref in (r.stored_run, r.stored_ancestor):\n                    if ref in snapshot.not_present:\n",
            after="    for dataset in inspected:\n        basis = snapshot.bases.get(dataset)\n        if basis is not None:\n            for r in basis.routes:\n                for ref in (r.stored_run, r.stored_ancestor):\n                    if ref in snapshot.not_present and ref in inspected:\n",
        ),
        checks=(f"{_A}::test_absence_names_what_each_root_can_discover_durably",),
    ),
    Arm(
        row="S5f",
        asserts="a refusal is not absence",
        sabotage=Sabotage(
            module=_CORPUS,
            before="    if not isinstance(view, WorldReadView):\n        return None\n    return view.corpus_of(ref) if type(view.locate(ref)) is NotPresent else None\n",
            after="    if not isinstance(view, WorldReadView):\n        return None\n    try:\n        view.get(ref)\n    except Exception:\n        return view.corpus_of(ref)\n    return None\n",
        ),
        checks=(f"{_A}::test_a_refusal_is_not_absence_durably",),
    ),
    Arm(
        row="R23b",
        asserts="not-present enters the lineage projection, so absence within coverage digests differently",
        sabotage=Sabotage(
            module=_LINEAGE,
            before="        \"not_present\": [{\"ref\": ref, \"corpus_id\": cid} for ref, cid in sorted(snapshot.not_present.items())],\n",
            after="        \"not_present\": [],\n",
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="D3b",
        asserts="a binding named in two availability states is refused",
        sabotage=Sabotage(
            module=_RESOLUTION,
            before="        if binding in table:\n            raise ResolutionError(\n",
            after="        if binding in table and entry.state != \"not-present\":\n            raise ResolutionError(\n",
        ),
        checks=(f"{_A}::test_the_five_outcomes_are_produced_and_kept_apart_durably",),
    ),
    Arm(
        row="D3c",
        asserts="not-present is produced, distinct from not-available",
        sabotage=Sabotage(
            module=_RESOLUTION,
            before="        if state.state == \"not-present\":\n",
            after="        if state.state == \"never\":\n",
        ),
        checks=(f"{_A}::test_the_five_outcomes_are_produced_and_kept_apart_durably",),
    ),
    Arm(
        row="R19b",
        asserts="attribution happens at the read, never after the fact",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="        if world: attribution.setdefault(value.identity(), set()).add(view.corpus_of(node.id) or \"\")\n",
            after="        if world: attribution.setdefault(value.identity(), set()).add(view.corpus_of(value.identity()) or \"\")\n",
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="R19c",
        asserts="a facet read goes through the holding corpus's own ReadView",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="    rows = read_observed_facets(profile, view.corpus_view(target), target)\n",
            after="    rows = read_observed_facets(profile, view, target)\n",
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="R19d",
        asserts="the facet read is held to the capture on its returned row set",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="    if returned != expected:\n",
            after="    if captured.uid != view.get(target).uid:\n",
        ),
        checks=(f"{_A}::test_a_facet_read_is_held_to_the_capture_durably",),
    ),
    Arm(
        row="R19",
        asserts="check_verification recomputes across corpora and reports a well-formed forgery",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="        return NoBelief(\"unavailable-corpus-absent\", detail=f\"inputs recorded in absent corpora: {corpora}\")\n",
            after="        return NoBelief(\"unavailable-input-unheld\", detail=f\"inputs recorded in absent corpora: {corpora}\")\n",
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="W6",
        asserts="the three states never collapse; removing a corpus does not convert its ids to unknown",
        sabotage=Sabotage(
            module=_READ,
            before="        if not status.present:\n            return NotPresent(stamp)\n",
            after="        if not status.present:\n            return Unknown(stamp)\n",
        ),
        checks=(f"{_A}::test_the_three_states_never_collapse_and_removal_is_not_unknown",),
    ),
    Arm(
        row="W8b",
        asserts="duplicate location and corruption are distinguished at build and no repair is offered",
        sabotage=Sabotage(
            module=_REGISTRY,
            before="    if len(carriers) > 1:\n",
            after="    if len(carriers) > 2:\n",
        ),
        checks=(f"{_A}::test_duplicate_location_and_corruption_are_distinguished_at_build",),
    ),
)
```

The R19 rows: `R19b`–`R19d` sabotage the evaluation seam the cross-corpus recomputation shares, and `R19` proper is checked by the verification arm; if the guard's uniqueness test wants one check per arm, split `test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably` into the three checks its name implies. Add `test_the_five_outcomes_are_produced_and_kept_apart_durably` and `test_a_facet_read_is_held_to_the_capture_durably` to the acceptance module (Step 1) — the unit tests of Tasks 8 and 10 over the durable roots. `W6` and `W8b` sabotage slice 2's code and their checks run `read.resolve_address` and `epoch.build_epoch` over the durable world: that is what "measured, not built" means at N2.

- [ ] **Step 4: Write the guard**

`test_n2_cut23.py`, modelled on `test_n2_cut22.py` line for line: `CUT23_FREEZE_COMMIT` and `CUT23_FROZEN_SHA256` from Task 1's note; `FROZEN_CUT = ROOT / "docs/designs/2026-09-09-conformance-cut-23.md"`; `FROZEN_PRIOR_CUT_FILES` = cut 22's table plus `"python/tests/acceptance/n2_arms_cut22.py": "<the commit that last touched it, from git log -1 --format=%h -- that path>"`; `PRIOR_ARMS` extended with `CUT22_ARMS`; the inventory test asserting `DECLARATION_UNITS == ("D3", "S1", "S1a", "S5", "W6", "W8b", "W10", "R19", "R23")`, `{unit_of(arm.row) for arm in CUT23_ARMS}` equal to it, and `len(CUT23_ARMS) == 23`; the pinned-sections test greping `**9 declaration units**`, the accounting sentence and `("cut22_acceptance.py",)`.

- [ ] **Step 5: Audit the arms**

Run: `SCIENCE_CUT4_ROOT=$(pwd)/../.cut23-acceptance uv run --frozen pytest tests/acceptance/test_n2_cut23.py -q -p no:cacheprovider`
Expected: every arm `sound`, the baseline `resolved`, the pins hold. A `vacuous` arm means the check does not reach the sabotaged line — fix the check or the sabotage, never the source. Then `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py -q -p no:cacheprovider` — the new guard is not yet live (no runner), so it must be neither live nor declared: this fails until Task 13 lands the runner; run it again there.

- [ ] **Step 6: Commit**

```bash
git add python/tests/acceptance/test_world_view_acceptance.py python/tests/acceptance/n2_arms_cut23.py python/tests/acceptance/test_n2_cut23.py
git commit -m "test(cut23): durable arms, N2 declarations and the guard for the world read view"
```

---

### Task 13: The runner, and the design-corpus and guard sweeps

**Files:**
- Create: `python/tools/cut23_acceptance.py`
- Modify: `python/src/beliefs/corpus.py` module docstring (the "Traversal is corpus-local throughout" paragraph), `python/src/beliefs/world/read.py` nothing, `docs/guide/` pages that state traversal is corpus-local (grep `corpus-local` under `docs/guide`)

- [ ] **Step 1: Write the runner**

Copy `python/tools/cut22_acceptance.py` to `cut23_acceptance.py` and change: `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut23-acceptance"`, `PREFIX_RUNNERS = ("cut22_acceptance.py",)`, `PHASE_MODULES = ("test_world_view_acceptance.py", "test_n2_cut23.py")`, the env var `SCIENCE_CUT23_ROOT`, `cut_environment`'s range to `range(4, 24)`, the banner prefix `[cut23 …]`, and `declared_accounting` importing `CUT23_ARMS, DECLARATION_UNITS, unit_of` from `n2_arms_cut23`.

- [ ] **Step 2: Run the guard sweeps**

Run: `uv run --frozen pytest tests/test_frozen_guards.py tests/test_arm_staleness.py tests/test_designs_corpus.py -q -p no:cacheprovider`
Expected: PASS — `test_n2_cut23.py` is now live through the new runner; every pin in every live guard holds; every arm applies once.

- [ ] **Step 3: Correct the docstrings and guide**

`corpus.py`'s docstring paragraph "Traversal is corpus-local throughout" becomes: "Traversal is corpus-local over a `ReadView` and world-wide over a `WorldReadView` (`world/view.py`): the same adjacencies, one truncating at the corpus edge and the other continuing through the epoch's address map." Grep `docs/guide` for the corpus-local claim and correct each hit to name the world read view; run `uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider` again.

- [ ] **Step 4: Run the whole runner**

Run: `uv run --frozen python tools/cut23_acceptance.py 2>&1 | tee ../.cut23-acceptance/run.log | tail -30`
Expected: exit 0; the prefix chain through cut 22 green; both phases green; the final line `declared arms: N (= 9 declaration units; 9 guarantee rows)`.

- [ ] **Step 5: Commit**

```bash
git add python/tools/cut23_acceptance.py python/src/beliefs/corpus.py docs/guide
git commit -m "test(cut23): the acceptance runner, and the corpus-local claims corrected"
```

---

### Task 14: Discharge

**Files:**
- Create: `docs/plans/<discharge date>-conformance-cut-23-results.md` and `docs/plans/<discharge date>-conformance-cut-23-run/{certified.log,check.log,test.log}` — the date is the day the gate runs, in `YYYY-MM-DD`; every `2026-09-XX` below is that date
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Updated`, `Implemented through conformance cut 23`, the `Current state` table: `world-resolution` row rewritten to its remaining rows), `docs/plans/2026-08-29-implementation-roadmap.md` (whole rewrite per its own rule: `**Ranked at:** cut 23`, Appendix A regenerated by `python/tools/roadmap_status.py`, Appendix B rows for D3, S1, S1a, S5, W6, W8b, W10, R19 removed and R23 narrowed), `docs/superpowers/specs/2026-09-09-world-resolution-slice-1-design.md` (`Status:` line → discharged at cut 23, dated)
- Task tree: `tasks add "Freeze cut 23" --parent beliefs-d248ba` and `tasks add "Discharge cut 23" --parent beliefs-d248ba` were the two ceremony tasks; close both; file slices 2–4 as siblings.

- [ ] **Step 1: Run the serial gate and retain the transcripts**

```bash
mkdir -p ../docs/plans/2026-09-XX-conformance-cut-23-run
uv run --frozen python tools/cut23_acceptance.py > ../docs/plans/2026-09-XX-conformance-cut-23-run/certified.log 2>&1; echo "exit $?"
(uv run --frozen ruff check . && uv run --frozen pyright) > ../docs/plans/2026-09-XX-conformance-cut-23-run/check.log 2>&1; echo "exit $?"
uv run --frozen pytest -p no:cacheprovider > ../docs/plans/2026-09-XX-conformance-cut-23-run/test.log 2>&1; echo "exit $?"
tail -1 ../docs/plans/2026-09-XX-conformance-cut-23-run/test.log
```
Expected: three `exit 0`; the summary line names the count. Claim the count only from that line.

- [ ] **Step 2: Write the results record**

Sections as cut 22's: `## 1. What ran` (the exact commands, exit codes, the prefix chain, per-phase counts, the `declared arms:` line, the transcript links), `## 2. Accounting and disposition` (D3, S1, S1a, S5, W6, W8b, W10, R19 full/closed; R23 part with its remainder), `## 3. Corrections and deviations from the frozen cut` (dated bullets, empty if none), `## 4. Reproduction measurement`, `## 5. Remaining boundary` (naming every open label: `world-resolution` retains W1, W2, W4, W5a, W7, W8, W13's clauses, W8a's coreference arms, X12 and M3's coreference arms, R23's snapshot, divergence and explicit-import clauses; `packaging-remainder` unchanged).

- [ ] **Step 3: Regenerate the roadmap's Appendix A and rewrite the ledger's Current state**

Run: `uv run --frozen python tools/roadmap_status.py` and paste its table; rewrite the roadmap whole per its header rule; update the ledger's `world-resolution` row and summary; run `uv run --frozen pytest tests/test_designs_corpus.py -q -p no:cacheprovider` until green — `test_the_roadmap_and_ledger_name_the_same_boundaries` and `test_the_ledger_summary_names_the_newest_remaining_boundary` are the two that bind these documents to the record.

- [ ] **Step 4: Close the tasks and commit**

```bash
tasks done <discharge-task-id> "cut 23 discharged; results record docs/plans/2026-09-XX-conformance-cut-23-results.md"
tasks note beliefs-d248ba "slice 1 discharged at cut 23; slices 2-4 filed as <ids>"
git add -A docs python/tests tasks
git commit -m "docs(cut23): discharge conformance cut 23 and re-rank the roadmap"
```

Then merge `design/world-resolution` into `main` with `--no-ff`, run the serial gate on `main`, and remove the worktree per the roadmap's lane rules.
