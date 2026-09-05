# The mm30 reproduction — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Push one real mm30 proposition through the `beliefs` kernel as a library, from a registered world to the belief evaluator's answer, and record every refusal, prediction and finding in a dated measurement record.

**Architecture:** A throwaway driver package under `python/tools/reproduction/` composes the kernel's public seams in the order the design's §4 fixes — world and corpus, typing, holding, spec, confined run, assessment, verification, admission and belief, corpus close, and a fresh-process re-derivation split into belief equality and evidence reconstruction. Every governed record is minted through `open_corpus`'s `CorpusWriter` under one full `Authority`; no kernel module is edited from this lane. The record under `docs/designs/` is the deliverable, and its commit re-ranks the roadmap.

**Tech Stack:** Python 3.13 via `uv` in `python/`; the `beliefs` package and its `atoms`/`nodes` substrates; Snakemake through the kernel's confined boundary (bubblewrap); pytest for the driver's own unit tests.

**Spec:** `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` — read §2 (the four rules), §4 (the path), §5 (predictions P1–P7), §6 (the three questions) and §7 (the findings classes) before any task.

## Global Constraints

- **Reproduce, never migrate** (spec §2 rule 1): no file under the predecessor's `entities/`, `knowledge/` or `results/` is copied into the corpus. Its records are read to decide what to reproduce; its data files are re-held by content identity.
- **A refusal is a finding** (spec §2 rule 2): a `Refused`, `RunRefused`, `WriteRefused`, `PermitExceeded` or `AssessmentFinding` is recorded and classified under spec §7 (design gap / corpus work / defect). It is never retried with altered inputs, never suppressed, never worked around by a second write path.
- **The target, spec and interpretation rule are fixed at Task 6** (spec §2 rule 4) and are not changed afterwards to obtain a belief. `NoBelief` with an attributable reason is a terminal, complete outcome.
- **The corpus lives on the certified volume beside the checkout**, never under `/tmp`, `/dev/shm` or the scratch volume. The work directory is `<repo>/.mm30-reproduction/` or `$SCIENCE_MM30_ROOT`, mirroring the acceptance runners' `DEFAULT_WORK` convention.
- **No code under `python/src/beliefs/`** changes from this lane. Findings for kernel surfaces are filed as dated design amendments or `open-questions.md` entries through the owning lane (roadmap concurrency rule 6). A defect becomes a failing test in the owning lane, not a patch here.
- **The analysis is standard-library Python only.** The confined runtime closure is materialized per file from the interpreter; whether third-party packages are reachable inside it is unmeasured, and a dependency would confound the run with an environment question. If the chosen analysis genuinely needs one, that is a finding, not a reason to relax confinement.
- **Predictions are answered, never edited.** Spec §5's P1–P7 are copied verbatim into the record at Task 1 and each is marked confirmed, confirmed-for-another-reason, or refuted at Task 12.
- **Every script is throwaway by declaration** (spec §8 item 3): it lives under `python/tools/reproduction/`, ships in no distribution, and is not promoted into `science`.
- Use the project venv: `cd python && uv run ...`. Never the system interpreter.
- Commit messages use conventional commits with no AI attribution trailer.

---

## File structure

| path | responsibility |
|---|---|
| `.worktrees/mm30/` | the lane's worktree on branch `measure/mm30-reproduction`, from `main` after the course-correction branch merges |
| `python/tools/reproduction/__init__.py` | empty; makes the driver importable in tests as `reproduction` (tests add `tools/` to `sys.path` as `roadmap_status.py`'s test does) |
| `python/tools/reproduction/paths.py` | the work directory on the certified volume, the predecessor corpus root, the record path; nothing else |
| `python/tools/reproduction/preflight.py` | step 0: certified-volume probe and `host_prerequisites()`; refuses loudly, never skips |
| `python/tools/reproduction/select_target.py` | Task 2: enumerates candidates under the four criteria and writes `target.yaml` |
| `python/tools/reproduction/authority.py` | the one `Authority` every act binds: `Authority(WritePermit.full(), "mm30-reproduction")` |
| `python/tools/reproduction/world.py` | step 1: world root, corpus root, store root, manifest adoption, admission |
| `python/tools/reproduction/vocabulary.py` | step 2: the domain contract document, `compile_profile`, the resolution snapshot |
| `python/tools/reproduction/type_target.py` | step 2: `build_claim` over `target.yaml`, the proposition record |
| `python/tools/reproduction/hold.py` | step 3: the holdings write, the dataset record, `admission_state` |
| `python/tools/reproduction/analysis/` | the held code root: `workflow/Snakefile` and `assoc.py`, the stdlib-only association |
| `python/tools/reproduction/spec.py` | step 4: the frozen spec, the interpretation and equivalence rule implementations |
| `python/tools/reproduction/run.py` | steps 5–7: confined run, assessment, replay, verification |
| `python/tools/reproduction/belief.py` | step 8: admission, verification record, `evaluate` |
| `python/tools/reproduction/close.py` | step 9: `corpus_check`, `audit_corpus`, `audit_log` |
| `python/tools/reproduction/rederive.py` | step 10a/10b: a fresh-process script over the on-disk corpus alone |
| `python/tools/reproduction/state.py` | `state.json` under the work directory: every identity a later step needs (corpus id, store id, proposition ref, spec identity, run refs, assessment identity, verification ref, the step-8 answer) |
| `python/tools/reproduction/findings.py` | `findings.jsonl` writer: one line per finding with class, step, reason, and where it was filed |
| `python/tests/test_reproduction_driver.py` | unit tests for the pure pieces: candidate ranking, outcome-file digest mapping, findings classification of a `derive_scope` result |
| `docs/designs/2026-09-DD-mm30-reproduction.md` | the record (spec §8 item 1); `DD` is the day the run completes |

Every driver module exposes one `main()` and writes what later steps need into `state.json` through `state.py`; no step reads another step's Python objects across processes. That is what makes step 10 a genuine fresh-process re-derivation.

---

### Task 1: Lane setup, preflight, and the record skeleton

**Files:**
- Create: `python/tools/reproduction/__init__.py`, `paths.py`, `authority.py`, `state.py`, `findings.py`, `preflight.py`
- Create: `docs/designs/2026-09-DD-mm30-reproduction.md` (skeleton)
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `paths.WORK: Path`, `paths.PREDECESSOR: Path`, `paths.RECORD: Path`; `authority.ACTOR: str`, `authority.AUTHORITY: Authority`; `state.load() -> dict`, `state.save(**fields) -> None` (merge-write); `findings.record(step: int, cls: str, reason: str, filed: str) -> None` with `cls in {"design-gap", "corpus-work", "defect", "host"}`; `preflight.main() -> int`.

- [ ] **Step 1: Create the worktree and branch**

```bash
cd <repo>
git worktree add -b measure/mm30-reproduction .worktrees/mm30 main
cd .worktrees/mm30/python && uv sync --quiet
```

- [ ] **Step 2: Write `paths.py`, `authority.py`, `state.py`, `findings.py`**

```python
# python/tools/reproduction/paths.py
from __future__ import annotations
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORK = Path(os.environ.get("SCIENCE_MM30_ROOT", REPO / ".mm30-reproduction"))
# The predecessor's mm30 project: cancer-types/multiple-myeloma under the cancer collection.
PREDECESSOR = Path(os.environ["MM30_PREDECESSOR"]) if "MM30_PREDECESSOR" in os.environ else (
    Path.home() / "d" / "cancer" / "cancer-types" / "multiple-myeloma"
)
RECORD = REPO / "docs" / "designs"  # the dated record file is named at Task 12
WORLD_ROOT = WORK / "world"
CORPUS_ROOT = WORK / "corpus"
STORE_ROOT = WORK / "store"
SCRATCH = WORK / "scratch"
STATE = WORK / "state.json"
FINDINGS = WORK / "findings.jsonl"
TARGET = WORK / "target.yaml"
```

```python
# python/tools/reproduction/authority.py
from beliefs.permit import Authority, WritePermit

ACTOR = "mm30-reproduction"
AUTHORITY = Authority(WritePermit.full(), ACTOR)
```

```python
# python/tools/reproduction/state.py
from __future__ import annotations
import json
from reproduction import paths

def load() -> dict:
    return json.loads(paths.STATE.read_text()) if paths.STATE.exists() else {}

def save(**fields: object) -> None:
    current = load()
    current.update(fields)
    paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    paths.STATE.write_text(json.dumps(current, indent=2, sort_keys=True))
```

```python
# python/tools/reproduction/findings.py
from __future__ import annotations
import json
from datetime import UTC, datetime
from reproduction import paths

CLASSES = frozenset({"design-gap", "corpus-work", "defect", "host"})

def record(step: int, cls: str, reason: str, filed: str = "unfiled") -> None:
    if cls not in CLASSES:
        raise ValueError(f"finding class {cls!r} is not one of {sorted(CLASSES)}")
    paths.FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    with paths.FINDINGS.open("a") as out:
        out.write(json.dumps({
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "step": step, "class": cls, "reason": reason, "filed": filed,
        }, sort_keys=True) + "\n")
```

- [ ] **Step 3: Write `preflight.py`** — the cut-13 runner's probe, reused rather than re-derived

```python
# python/tools/reproduction/preflight.py
"""Step 0. Refuses loudly; never skips. Exit 2 on refusal."""
from __future__ import annotations
import shutil
import sys

from beliefs.confinement import host_prerequisites
from beliefs.root import init_corpus_root, init_store_root, init_world_root, metadata_root_for
from beliefs.world import WorldConfig
from reproduction import paths
from reproduction.authority import AUTHORITY


def main() -> int:
    paths.WORK.mkdir(parents=True, exist_ok=True)
    probe = paths.WORK / "probe"
    world, corpus, store = probe / "world", probe / "corpus", probe / "store"
    try:
        init_world_root(WorldConfig(world, "0" * 32, ()), authority=AUTHORITY)
        init_corpus_root(corpus, authority=AUTHORITY)
        init_store_root(store, authority=AUTHORITY)
    except Exception as refused:  # noqa: BLE001 — report the engine's own words
        print(f"REFUSED: the volume under {paths.WORK} is not certified: {type(refused).__name__}: {refused}")
        return 2
    finally:
        for root in (world, corpus, store):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)
        shutil.rmtree(probe, ignore_errors=True)
    reason = host_prerequisites()
    if reason is not None:
        print(f"REFUSED: confinement unavailable on this host: {reason}")
        return 2
    if not paths.PREDECESSOR.joinpath("science.yaml").exists():
        print(f"REFUSED: predecessor corpus not found at {paths.PREDECESSOR}")
        return 2
    print(f"ok: certified volume at {paths.WORK}; confinement available; predecessor at {paths.PREDECESSOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run preflight**

Run: `cd python && uv run python tools/reproduction/preflight.py`
Expected: `ok: certified volume at ...` and exit 0. If it prints `REFUSED`, stop: the volume or host is the finding and the record's first entry.

- [ ] **Step 5: Write the failing unit test for findings classification**

```python
# python/tests/test_reproduction_driver.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from reproduction import findings  # noqa: E402


def test_a_finding_class_outside_the_four_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(findings.paths, "FINDINGS", tmp_path / "f.jsonl")
    with pytest.raises(ValueError):
        findings.record(1, "oops", "reason")


def test_a_finding_is_appended_as_one_json_line(tmp_path, monkeypatch):
    monkeypatch.setattr(findings.paths, "FINDINGS", tmp_path / "f.jsonl")
    findings.record(3, "design-gap", "facet is presence-only", filed="domain lane")
    lines = (tmp_path / "f.jsonl").read_text().splitlines()
    assert len(lines) == 1 and '"class": "design-gap"' in lines[0]
```

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q`
Expected: 2 passed.

- [ ] **Step 6: Write the record skeleton** at `docs/designs/2026-09-DD-mm30-reproduction.md` with these headings and nothing invented: `# The mm30 reproduction — record`; `**Status:** in progress`; `## 1. Preflight` (paste preflight's output line); `## 2. Target` (empty until Task 2); `## 3. The path` (a table with rows 1–10b, columns *step / outcome / left on disk*, all cells `pending`); `## 4. Predictions` (P1–P7 copied verbatim from the spec §5, each followed by `**Outcome:** pending`); `## 5. Questions` (spec §6's three, each `pending`); `## 6. Findings` (empty table: step / class / reason / filed); `## 7. Authoring cost` (empty).

- [ ] **Step 7: Commit**

```bash
git add python/tools/reproduction python/tests/test_reproduction_driver.py docs/designs/2026-09-DD-mm30-reproduction.md
git commit -m "chore(reproduction): lane setup, preflight and the record skeleton"
```

---

### Task 2: Select the target

**Files:**
- Create: `python/tools/reproduction/select_target.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `target.yaml` with keys `proposition_id`, `subject`, `predicate`, `object`, `claim_layer`, `polarity`, `identification_strength`, `dataset_id`, `dataset_path` (absolute), `dataset_bytes`, `evidence_line_ids` (list), `alternatives` (list of the next four candidates with their scores); `select_target.rank(candidates: list[dict]) -> list[dict]` (pure).

The predecessor's shape, measured 2026-09-05: 307 structured propositions (`subject`/`predicate`/`object` in front matter; `claim_layer` in `causal_effect` 228, `structural_claim` 63, `empirical_regularity` 16); 396 evidence lines, 266 `empirical_data`, 225 of those `belief_eligible: true`, each with `target: proposition:<slug>` and `source:` naming a task id, an interpretation, or a DOI; 259 dataset records of which 42 carry a `local_path` or `datapackage` that resolves on disk. No proposition carries `evidence_refs`; the join is evidence line → proposition.

- [ ] **Step 1: Write the failing test for `rank`**

```python
def test_rank_prefers_empirical_locally_held_small_targets():
    from reproduction.select_target import rank
    a = {"proposition_id": "p:a", "claim_layer": "causal_effect", "dataset_bytes": 2_000_000, "empirical_lines": 3}
    b = {"proposition_id": "p:b", "claim_layer": "structural_claim", "dataset_bytes": 1_000, "empirical_lines": 5}
    c = {"proposition_id": "p:c", "claim_layer": "empirical_regularity", "dataset_bytes": 50_000, "empirical_lines": 1}
    ordered = [r["proposition_id"] for r in rank([a, b, c])]
    assert ordered[0] == "p:c"          # empirical layer and smallest empirical dataset
    assert ordered[-1] == "p:b"         # structural layer is excluded from first place
```

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k rank`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 2: Write `select_target.py`**

```python
# python/tools/reproduction/select_target.py
"""Task 2: enumerate candidates under spec §3's four criteria and write target.yaml."""
from __future__ import annotations
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from reproduction import paths, state

EMPIRICAL_LAYERS = ("causal_effect", "empirical_regularity")


def front(path: Path) -> dict:
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def rank(candidates: list[dict]) -> list[dict]:
    """Structured is a precondition of being here; empirical layer first, then
    the smallest held dataset, then the most empirical evidence lines."""
    def key(c: dict) -> tuple:
        return (
            0 if c["claim_layer"] in EMPIRICAL_LAYERS else 1,
            c["dataset_bytes"],
            -c["empirical_lines"],
            c["proposition_id"],
        )
    return sorted(candidates, key=key)


def dataset_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) if root.is_dir() else root.stat().st_size


def main() -> int:
    root = paths.PREDECESSOR
    propositions = {}
    for path in (root / "entities" / "propositions").glob("*.md"):
        f = front(path)
        if f.get("predicate") and f.get("subject") and f.get("object"):
            propositions[f["id"]] = f
    lines = defaultdict(list)
    for path in (root / "entities" / "evidence-lines").glob("*.md"):
        f = front(path)
        if f.get("evidence_type") == "empirical_data" and f.get("belief_eligible") is True:
            lines[f.get("target")].append(f)
    datasets = {}
    for path in (root / "entities" / "datasets").glob("*.md"):
        f = front(path)
        local = f.get("local_path") or (str(Path(f["datapackage"]).parent) if f.get("datapackage") else "")
        if local and (root / local).exists():
            datasets[f["id"]] = (root / local).resolve()
    candidates = []
    for pid, prop in propositions.items():
        if pid not in lines:
            continue
        # A candidate needs a held dataset it can be assessed over. The predecessor
        # names datasets on evidence-line sources indirectly, so the join here is
        # the proposition's own `datasets`/`related` fields plus every dataset the
        # evidence lines' sources name; the executor confirms the analysis reads it.
        named = set(prop.get("datasets") or []) | {r for r in (prop.get("related") or []) if str(r).startswith("dataset:")}
        for line in lines[pid]:
            named |= {r for r in (line.get("related") or []) if str(r).startswith("dataset:")}
        held = [(d, datasets[d]) for d in sorted(named) if d in datasets]
        for did, dpath in held:
            candidates.append({
                "proposition_id": pid, "subject": prop["subject"], "predicate": prop["predicate"],
                "object": prop["object"], "claim_layer": prop.get("claim_layer"),
                "polarity": prop.get("polarity"), "identification_strength": prop.get("identification_strength"),
                "dataset_id": did, "dataset_path": str(dpath), "dataset_bytes": dataset_bytes(dpath),
                "empirical_lines": len(lines[pid]), "evidence_line_ids": [l["id"] for l in lines[pid]],
            })
    ordered = rank(candidates)
    if not ordered:
        print("no proposition joins to a held dataset through its own fields; relax per spec §3 and record which")
        return 2
    chosen = dict(ordered[0])
    chosen["alternatives"] = ordered[1:5]
    paths.TARGET.write_text(yaml.safe_dump(chosen, sort_keys=False))
    state.save(target=chosen["proposition_id"], dataset=chosen["dataset_id"])
    print(f"candidates: {len(candidates)}; chosen: {chosen['proposition_id']} over {chosen['dataset_id']} ({chosen['dataset_bytes']} bytes)")
    for c in ordered[:5]:
        print(f"  {c['proposition_id']}  layer={c['claim_layer']}  dataset={c['dataset_id']}  bytes={c['dataset_bytes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the test, then the selection**

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k rank` → PASS.
Run: `uv run python tools/reproduction/select_target.py` → a chosen target, or exit 2.

If exit 2: the join through the proposition's own fields found no held dataset. Relax *small* first, then *locally held* last (spec §3), by widening the join to the evidence lines' `source` records (an `interpretation:` or task id under `tasks/`) and reading their `datasets` fields. Record in the record's §2 which relaxation was needed — that is itself an authoring-cost measurement for P1.

- [ ] **Step 4: Confirm the analysis is reproducible from the dataset alone**

Open the chosen evidence lines and their `source` records in the predecessor. Write into the record's §2, in one paragraph each: what the predecessor computed (the statistic, the covariate, the direction), which file under `dataset_path` carries the columns it needs, and whether that computation is expressible in standard-library Python. If it is not (needs a fitted model, a package, or an intermediate the predecessor no longer holds), take the next alternative and say why.

- [ ] **Step 5: Commit**

```bash
git add python/tools/reproduction/select_target.py python/tests/test_reproduction_driver.py docs/designs/2026-09-DD-mm30-reproduction.md
git commit -m "feat(reproduction): select the target proposition under the four criteria"
```

---

### Task 3: World, corpus, store (path step 1)

**Files:**
- Create: `python/tools/reproduction/world.py`

**Interfaces:**
- Consumes: `authority.AUTHORITY`, `paths.*`.
- Produces: `state.json` gains `world_id`, `corpus_id`, `store_id`; `world.open_writer() -> CorpusWriter` and `world.open_world() -> World` for later tasks.

The kernel's shape: `init_world_root(WorldConfig(world_root, world_id, (corpus_root,)), authority=A)`; `init_corpus_root(corpus_root, authority=A)`; `init_store_root(store_root, authority=A) -> store_id`; `open_corpus(corpus_root, authority=A).adopt_manifest(profile=CorpusPins(...))` mints the manifest; `open_world(config, authority=A).admit(corpus_root, provenance=Fresh())` registers it. The manifest's pins are `"<namespace>:<content identity>"` strings; the base contract's is `f"science:{base.content_identity}"` and the domain's is `f"{contract.namespace}:{contract.content_identity}"`, both from Task 4's parsed contracts, so this task **imports `vocabulary.pins()`** and Task 4 is written before this task runs.

- [ ] **Step 1: Write `world.py`**

```python
# python/tools/reproduction/world.py
"""Step 1: register a world root and adopt one fresh corpus on the certified volume."""
from __future__ import annotations
import secrets
import sys

from beliefs.corpus import CorpusWriter
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world as _open_world
from beliefs.world import Fresh, World, WorldConfig
from reproduction import paths, state
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import pins


def config() -> WorldConfig:
    return WorldConfig(paths.WORLD_ROOT, state.load()["world_id"], (paths.CORPUS_ROOT,))


def open_writer() -> CorpusWriter:
    return open_corpus(paths.CORPUS_ROOT, authority=AUTHORITY)


def open_world() -> World:
    return _open_world(config(), authority=AUTHORITY)


def main() -> int:
    if paths.WORLD_ROOT.exists():
        print(f"REFUSED: {paths.WORLD_ROOT} exists; the exercise runs once per work directory")
        return 2
    world_id = secrets.token_hex(16)
    state.save(world_id=world_id)
    init_world_root(config(), authority=AUTHORITY)
    init_corpus_root(paths.CORPUS_ROOT, authority=AUTHORITY)
    store_id = init_store_root(paths.STORE_ROOT, authority=AUTHORITY)
    manifest = open_writer().adopt_manifest(profile=pins())
    admission = open_world().admit(paths.CORPUS_ROOT, provenance=Fresh())
    state.save(corpus_id=manifest.corpus_id, store_id=store_id, admission=admission.corpus_id)
    status = open_world().status(manifest.corpus_id)
    print(f"world {world_id}; corpus {manifest.corpus_id} status {status}; store {store_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it (after Task 4 exists)**

Run: `cd python && uv run python tools/reproduction/world.py`
Expected: one line naming world, corpus and store ids; `state.json` carries all three. Record in §3 row 1: outcome and what is on disk (`ls .mm30-reproduction/`).

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/world.py
git commit -m "feat(reproduction): register the world, corpus and store roots"
```

---

### Task 4: Vocabulary and the compiled profile (path step 2, first half)

**Files:**
- Create: `python/tools/reproduction/vocabulary.py`, `python/tools/reproduction/mm30-reproduction.yaml`

**Interfaces:**
- Consumes: `python/tools/vocabularies/mm30-modal-sorted.yaml` (read, not edited); `contracts/science/CONTRACT.yaml`; `target.yaml`.
- Produces: `vocabulary.profile() -> ProfileSpec`, `vocabulary.contract() -> DomainContract`, `vocabulary.pins() -> CorpusPins`, `vocabulary.snapshot() -> ResolutionSnapshot`, `vocabulary.plan() -> dict` (the operator/layer/polarity/sort maps).

Spec §6 question 1 binds this task: both typing vocabularies bind only the placeholder `mm30-entities` namespace at release `2026-08-07`. The reproduction's contract document is a copy of `mm30-modal-sorted.yaml`'s `contract:` block **with the target's two terms bound under a named ontology release if one can be named honestly** (the term is a GO, HP, EFO or MONDO identifier the predecessor records in `ontology_terms` or `xrefs`), and otherwise under the placeholder, in which case question 1 is answered *unmeasured* and the record says so.

- [ ] **Step 1: Write the contract document** `python/tools/reproduction/mm30-reproduction.yaml`: copy the `contract:` and `plan:` blocks from `mm30-modal-sorted.yaml` verbatim, then set `contract.contract: mm30-reproduction`. If the target's terms carry ontology identifiers, add one sort per ontology under `sorts:` with `vocabulary: { namespace: <GO|HP|EFO|MONDO>, release: "<release the predecessor pins>" }` and set the target operator's `arg_sorts` accordingly. Note at the top of the file which of the two cases holds and why.

- [ ] **Step 2: Write `vocabulary.py`**

```python
# python/tools/reproduction/vocabulary.py
from __future__ import annotations
from functools import cache
from pathlib import Path

import yaml

from beliefs.consulted import CorpusPins
from beliefs.contract import load_base_contract
from beliefs.contract.domain import DomainContract, VocabularyBinding, parse_domain_contract
from beliefs.profile import ProfileSpec, compile_profile
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths

DOCUMENT = Path(__file__).with_name("mm30-reproduction.yaml")
BASE = paths.REPO / "contracts" / "science" / "CONTRACT.yaml"


@cache
def _document() -> dict:
    return yaml.safe_load(DOCUMENT.read_text())


@cache
def base():
    return load_base_contract(BASE)


@cache
def contract() -> DomainContract:
    return parse_domain_contract(_document()["contract"], source=f"{DOCUMENT}: contract", base=base(), predecessor=None)


@cache
def profile() -> ProfileSpec:
    return compile_profile(base(), [contract()])


def plan() -> dict:
    return _document()["plan"]


def pins() -> CorpusPins:
    return CorpusPins(
        science_contract=f"science:{base().content_identity}",
        domains={contract().namespace: f"{contract().namespace}:{contract().content_identity}"},
    )


def snapshot(terms: tuple[str, ...]) -> ResolutionSnapshot:
    """Every declared binding readable over exactly the target's terms. A term
    is `member` because we say so — the placeholder namespace has no
    authority behind it, which is the unmeasured half of question 1."""
    readable = {}
    for sort in _document()["contract"]["sorts"].values():
        binding = VocabularyBinding(namespace=sort["vocabulary"]["namespace"], release=str(sort["vocabulary"]["release"]), dataset_identity=None)
        readable[binding] = terms
    return build_snapshot(readable=readable)
```

- [ ] **Step 3: Check it compiles**

Run: `cd python && uv run python -c "import sys; sys.path.insert(0,'tools'); from reproduction import vocabulary as v; print(v.profile().operator('affects')); print(v.pins())"`
Expected: a `CompiledOperator` and a `CorpusPins`. A parse refusal here is a **corpus-work** finding on the contract document (the typing exercise's own document parsed, so a refusal means this task's edits).

- [ ] **Step 4: Commit**

```bash
git add python/tools/reproduction/vocabulary.py python/tools/reproduction/mm30-reproduction.yaml
git commit -m "feat(reproduction): the reproduction's domain contract and compiled profile"
```

---

### Task 5: Type and mint the proposition (path step 2, second half)

**Files:**
- Create: `python/tools/reproduction/type_target.py`

**Interfaces:**
- Consumes: `target.yaml`; `vocabulary.profile()`, `vocabulary.plan()`; `world.open_writer()`.
- Produces: `state.json` gains `proposition_ref` (`proposition:<slug>`) and `claim_identity`; the proposition record on disk.

The typing tool's mapping is the precedent (`python/tools/type_corpus_claims.py`, `type_record`): predicate → operator via `plan.operators`; `claim_layer` → layer via `plan.layers`; `polarity` → via `plan.polarities` (`not_applicable` → `None`); a term's sort from its `<kind>:` prefix via `plan.sorts`. `build_claim(profile, operator=, args=(Referent(sort=, term=), ...), layer=, polarity=)`; the stored facet is `project_claim(claim)`; the record is `stored.proposition_node(slug, title=, claim=facet, display_statement=)`.

- [ ] **Step 1: Write `type_target.py`**

```python
# python/tools/reproduction/type_target.py
"""Step 2: build_claim over the target and mint the proposition record."""
from __future__ import annotations
import sys
import time

import yaml

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.errors import ClaimError
from beliefs.projection import claim_identity, project_claim
from reproduction import findings, paths, state, vocabulary, world


def referent(term: str, plan: dict) -> Referent:
    kind = term.split(":", 1)[0]
    if kind not in plan["sorts"]:
        raise ClaimError(f"term {term!r}: kind prefix {kind!r} maps to no sort in the plan")
    return Referent(sort=plan["sorts"][kind], term=term)


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    plan = vocabulary.plan()
    started = time.monotonic()
    try:
        claim = build_claim(
            vocabulary.profile(),
            operator=plan["operators"][target["predicate"]],
            args=(referent(target["subject"], plan), referent(target["object"], plan)),
            layer=plan["layers"][target["claim_layer"]],
            polarity=plan["polarities"][target["polarity"]],
        )
    except (ClaimError, KeyError) as refused:
        findings.record(2, "corpus-work", f"build_claim refused the target: {type(refused).__name__}: {refused}")
        print(f"REFUSED at build_claim: {refused}")
        return 2
    slug = target["proposition_id"].split(":", 1)[1]
    node = stored.proposition_node(
        slug, title=target["proposition_id"], claim=project_claim(claim),
        display_statement=f"{target['subject']} {target['predicate']} {target['object']}",
    )
    minted = world.open_writer().add(node)
    state.save(proposition_ref=minted.id, claim_identity=claim_identity(claim),
               typing_seconds=round(time.monotonic() - started, 1))
    print(f"minted {minted.id}; claim identity {claim_identity(claim)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it; record the authoring cost**

Run: `cd python && uv run python tools/reproduction/type_target.py`
Expected: `minted proposition:<slug>`. Record §3 row 2 and §7: wall time from opening the predecessor record to the mint, in minutes, including the vocabulary edits of Task 4. That is P1's measurement.

If `build_claim` refuses: the finding is already recorded; **do not edit the target's fields**. The typing exercise measured 25 sort refusals under the modal-sorted plan; a refusal here is the same class and the record says so. Take the next alternative from `target.yaml` only if the refusal is on sort, and say so in §2.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/type_target.py
git commit -m "feat(reproduction): type the target and mint the proposition record"
```

---

### Task 6: Hold the dataset (path step 3)

**Files:**
- Create: `python/tools/reproduction/hold.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `target.yaml`'s `dataset_path`; `state.store_id`; `world.open_writer()`.
- Produces: `state.json` gains `dataset_ref`, `dataset_address`, `held_file` (the single file the analysis reads), `held_digest`, `store_relative_path`, `holdings_observation_id`; the holdings observation and dataset records on disk.

The local arm (cut 10): `ActContext(observer_root, store_root, observer, instrument, authority, holdings_seam())`; `holdings.boundary.write(ctx, StoreLocator(store_id, relative_path), content)` writes the bytes into the store and publishes a `holdings-observation` into the observer corpus under an intent. The dataset record is `stored.dataset_node(slug, title=, resources=[{"name":, "digest": "sha256:..."}], empirical_observation={...})`; its address is `dataset_address(stored.dataset_declaration(node))`.

**P2 is measured here.** `is_empirical_observation` reads presence only; the facet payload written below is what the author says, and nothing checks it. The finding is filed to the `domain` lane as a design gap whatever payload is chosen.

- [ ] **Step 1: Write the failing test for the single-file rule**

```python
def test_held_file_is_one_regular_file_the_analysis_reads():
    from reproduction.hold import choose_held_file
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "a.tsv").write_text("x\ty\n1\t2\n")
        (root / "notes.md").write_text("ignore")
        assert choose_held_file(root, preferred=("a.tsv",)) == root / "a.tsv"
        assert choose_held_file(root / "a.tsv", preferred=()) == root / "a.tsv"
```

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k held_file` → FAIL (ImportError).

- [ ] **Step 2: Write `hold.py`**

```python
# python/tools/reproduction/hold.py
"""Step 3: hold the dataset's bytes in the store; mint the dataset record."""
from __future__ import annotations
import sys
from hashlib import sha256
from pathlib import Path

import yaml

from beliefs import stored
from beliefs.dataset import ByteObservation, Held, admission_state, dataset_address
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/hold.v1"


def choose_held_file(path: Path, *, preferred: tuple[str, ...]) -> Path:
    """One regular file: the path itself, or the first preferred name under it,
    else the largest tabular file. The analysis of Task 7 reads exactly this."""
    if path.is_file():
        return path
    for name in preferred:
        if (path / name).is_file():
            return path / name
    tabular = sorted((p for p in path.rglob("*") if p.is_file() and p.suffix in {".tsv", ".csv", ".txt", ".gz"}),
                     key=lambda p: p.stat().st_size, reverse=True)
    if not tabular:
        raise FileNotFoundError(f"{path}: no tabular file to hold")
    return tabular[0]


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    held = choose_held_file(Path(target["dataset_path"]), preferred=tuple(target.get("preferred_files", ())))
    content = held.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    st = state.load()
    relative = f"{target['dataset_id'].split(':', 1)[1]}/{held.name}"
    ctx = ActContext(paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam())
    published = write(ctx, StoreLocator(st["store_id"], relative), content, expected=digest)
    observation = published.record
    # P2: the facet payload is authored, not checked. Say what we claim and file the gap.
    facet = {"boundary": "acquisition", "source": target["dataset_id"], "asserted_by": AUTHORITY.actor}
    node = stored.dataset_node(
        target["dataset_id"].split(":", 1)[1], title=target["dataset_id"],
        resources=[{"name": held.name, "digest": digest}], empirical_observation=facet,
    )
    minted = world.open_writer().add(node)
    declaration = stored.dataset_declaration(minted)
    verdict = admission_state(declaration, (ByteObservation(digest=digest, location=observation.location.canonical()),))
    if not isinstance(verdict, Held):
        findings.record(3, "defect", f"held bytes with matching digest did not read as Held: {verdict!r}")
        print(f"NOT HELD: {verdict!r}")
        return 2
    findings.record(3, "design-gap",
                    "empirical-observation facet is presence-only: is_empirical_observation read our authored payload unchecked",
                    filed="domain lane (facet payload contract, kernel §11)")
    state.save(dataset_ref=minted.id, dataset_address=dataset_address(declaration), held_file=str(held),
               held_digest=digest, store_relative_path=relative, holdings_observation_id=observation.identity())
    print(f"held {held.name} ({len(content)} bytes) as {digest}; dataset {minted.id}; address {dataset_address(declaration)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the test, then the step**

Run: `uv run pytest tests/test_reproduction_driver.py -q -k held_file` → PASS.
Run: `uv run python tools/reproduction/hold.py` → `held ... address dataset:sha256:...`. Record §3 row 3 and P2/P3 outcomes.

- [ ] **Step 4: Commit**

```bash
git add python/tools/reproduction/hold.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): hold the dataset through the store and mint its record"
```

---

### Task 7: The analysis code root and the frozen spec (path step 4)

**Files:**
- Create: `python/tools/reproduction/analysis/workflow/Snakefile`, `python/tools/reproduction/analysis/assoc.py`, `python/tools/reproduction/spec.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `state.proposition_ref`, `state.dataset_address`; `target.yaml`'s statistic description (Task 2 step 4).
- Produces: `spec.frozen() -> FrozenSpec` (deterministic: same inputs, same identity); `spec.interpretation() -> RuleImplementation`; `spec.equivalence() -> EquivalenceImplementation`; `spec.definition() -> WorkflowDefinition`; `spec.CODE_ROOT: Path`; `spec.OUTCOME_DIGESTS: dict[str, str]`; `state.json` gains `spec_identity`.

**The interpretation rule reads a result manifest, not bytes.** `build_assessment` calls `implementation.evaluate(run.result)` where `run.result` is `ResultManifest(outputs=((name, digest), ...))`. The rule therefore cannot open the analysis output. The exercise routes the verdict through a **canonical outcome file**: the workflow's last rule writes `outputs/outcome.txt` containing exactly one of `supported\n`, `refuted\n`, `inconclusive\n`, and the interpretation rule maps that file's digest to the outcome. This is spellable and honest, and it is a **design-gap finding** (where does interpretation read content?) filed at this task. Spec §5 predicted no such thing; it is recorded as an unpredicted finding.

- [ ] **Step 1: Write the failing test for the outcome-digest map**

```python
def test_outcome_digests_cover_exactly_the_three_outcomes():
    from hashlib import sha256
    from reproduction.spec import OUTCOME_DIGESTS
    assert set(OUTCOME_DIGESTS.values()) == {"supported", "refuted", "inconclusive"}
    assert OUTCOME_DIGESTS["sha256:" + sha256(b"supported\n").hexdigest()] == "supported"
```

Run: `uv run pytest tests/test_reproduction_driver.py -q -k outcome_digests` → FAIL.

- [ ] **Step 2: Write the analysis** — stdlib only. The statistic is the one Task 2 step 4 wrote into the record; the skeleton below is a two-group rank comparison (Mann–Whitney U with a normal approximation), which covers "expression of gene X differs by covariate Y". Replace the column names and the direction rule with the target's; do not add a dependency.

```python
# python/tools/reproduction/analysis/assoc.py
"""One within-dataset association, standard library only.

Reads inputs/data.tsv (tab-separated, header row), compares `VALUE_COLUMN`
between the two levels of `GROUP_COLUMN`, and writes outputs/stats.tsv and
outputs/outcome.txt — the latter exactly one of supported/refuted/inconclusive.
"""
from __future__ import annotations
import csv
import math
import pathlib
import sys

VALUE_COLUMN = "REPLACE_ME_value"      # set at Task 7 from target.yaml
GROUP_COLUMN = "REPLACE_ME_group"      # set at Task 7 from target.yaml
POSITIVE_LEVEL = "REPLACE_ME_level"    # the level in which the proposition predicts the higher value
ALPHA = 0.05


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float]:
    pooled = sorted((v, 0) for v in a) + sorted((v, 1) for v in b)
    pooled.sort(key=lambda t: t[0])
    ranks: dict[int, float] = {}
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    r_a = sum(ranks[k] for k, (_, g) in enumerate(pooled) if g == 0)
    n_a, n_b = len(a), len(b)
    u_a = r_a - n_a * (n_a + 1) / 2
    mu = n_a * n_b / 2
    sigma = math.sqrt(n_a * n_b * (n_a + n_b + 1) / 12)
    z = (u_a - mu) / sigma if sigma else 0.0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p


def main(inp: str, stats_out: str, outcome_out: str) -> None:
    groups: dict[str, list[float]] = {}
    with open(inp, newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            try:
                groups.setdefault(row[GROUP_COLUMN], []).append(float(row[VALUE_COLUMN]))
            except (KeyError, ValueError):
                continue
    levels = sorted(groups)
    if len(levels) != 2 or POSITIVE_LEVEL not in levels:
        outcome = "inconclusive"
        z = p = float("nan")
    else:
        other = [l for l in levels if l != POSITIVE_LEVEL][0]
        z, p = mann_whitney(groups[POSITIVE_LEVEL], groups[other])
        if p >= ALPHA:
            outcome = "inconclusive"
        else:
            outcome = "supported" if z > 0 else "refuted"
    pathlib.Path(stats_out).write_text(f"z\tp\tn\n{z}\t{p}\t{sum(len(v) for v in groups.values())}\n")
    pathlib.Path(outcome_out).write_text(outcome + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
```

```python
# python/tools/reproduction/analysis/workflow/Snakefile
import pathlib, subprocess, sys

rule assoc:
    input: "inputs/data.tsv"
    output: "outputs/stats.tsv", "outputs/outcome.txt"
    run:
        subprocess.run([sys.executable, "code/assoc.py", input[0], output[0], output[1]], check=True)
```

If the held file is gzipped or not TSV, add a first rule that decompresses or reshapes it inside the run with the standard library, and keep `assoc` reading `inputs/data.tsv` as staged by the boundary. The staged input name is the held input's logical name (`_stage_inputs` in `boundary.py`), and the fixtures stage the observed input as `inputs/data.txt`; confirm the staged name by reading `boundary._stage_inputs` before setting `input:`.

- [ ] **Step 3: Write `spec.py`**

```python
# python/tools/reproduction/spec.py
"""Step 4: freeze the analysis spec. Everything identity-bearing is fixed here."""
from __future__ import annotations
import sys
from decimal import Decimal
from functools import cache
from hashlib import sha256
from pathlib import Path

import yaml

from beliefs.adapter import WorkflowDefinition
from beliefs.recipe import ResultManifest
from beliefs.replay import EquivalenceImplementation
from beliefs.spec import Deterministic, FrozenSpec, RuleFixture, RuleImplementation, SpecDraft, SpecInput, freeze
from reproduction import findings, paths, state

CODE_ROOT = Path(__file__).with_name("analysis")
ENTRYPOINT = "code/workflow/Snakefile"
TARGETS = ("outputs/stats.tsv", "outputs/outcome.txt")
OUTCOME_FILE = "outputs/outcome.txt"
INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"
EQUIVALENCE_RULE = "content-identity-equality/v1"

OUTCOME_DIGESTS = {"sha256:" + sha256((o + "\n").encode()).hexdigest(): o for o in ("supported", "refuted", "inconclusive")}


def _interpret(manifest: ResultManifest) -> dict:
    digest = dict(manifest.outputs)[OUTCOME_FILE]
    return {"outcome": OUTCOME_DIGESTS[digest]}


@cache
def interpretation() -> RuleImplementation:
    fixture_manifest = ResultManifest(outputs=((OUTCOME_FILE, next(d for d, o in OUTCOME_DIGESTS.items() if o == "supported")),))
    return RuleImplementation(identity="impl-outcome-file-1", evaluate=_interpret,
                              fixtures=(RuleFixture(arguments=(fixture_manifest,), expected={"outcome": "supported"}),))


@cache
def equivalence() -> EquivalenceImplementation:
    return EquivalenceImplementation(identity="impl-eq-1", evaluate=lambda a, b: "passed" if a == b else "failed",
                                     fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),))


def held_rules() -> dict:
    return {INTERPRETATION_RULE: interpretation(), EQUIVALENCE_RULE: equivalence()}


def definition() -> WorkflowDefinition:
    return WorkflowDefinition(snakefile=(CODE_ROOT / "workflow" / "Snakefile").read_bytes(), family_streams={})


def draft() -> SpecDraft:
    st = state.load()
    target = yaml.safe_load(paths.TARGET.read_text())
    return SpecDraft(
        target=st["proposition_ref"],
        estimand=f"difference in {target['subject']} between levels of {target['object']} in {target['dataset_id']}",
        method="two-group rank comparison (Mann-Whitney U, normal approximation), standard library",
        assumptions="independent samples; the covariate is a two-level factor recorded per sample",
        falsification="no difference at alpha 0.05, or a difference in the direction opposite the proposition's polarity",
        input_roles=(SpecInput(role="observes", dataset=st["dataset_address"]),),
        applicability=f"samples of {target['dataset_id']} with both columns present",
        interpretation_rule=INTERPRETATION_RULE,
        equivalence_rule=EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
    )


@cache
def frozen() -> FrozenSpec:
    return freeze(draft(), held_rules=held_rules())


def main() -> int:
    spec = frozen()
    state.save(spec_identity=spec.identity)
    findings.record(4, "design-gap",
                    "build_assessment hands the interpretation rule a ResultManifest of digests, not output bytes; "
                    "the verdict is routed through a canonical outcome file whose digest the rule maps",
                    filed="computation design (where an interpretation rule reads content)")
    print(f"frozen spec {spec.identity} targeting {spec.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`spec.target` is set to the **proposition's corpus ref** because `evaluation.gather` matches stored assessments on `value.proposition == proposition` and the assessment record's `proposition` member is the corpus ref. `audit.py` notes the derived value carries "the spec's claim target" in a different namespace from the stored ref. Whether `target` is meant to be a claim identity or a corpus ref is a question the run answers at step 10a; if the two disagree, that is a design-gap finding, filed to the kernel's spec/assessment owner.

- [ ] **Step 4: Run the test and freeze**

Run: `uv run pytest tests/test_reproduction_driver.py -q -k outcome_digests` → PASS.
Run: `uv run python tools/reproduction/spec.py` → `frozen spec <64 hex> targeting proposition:<slug>`. Record §3 row 4. **From here on the target, spec and rule are fixed** (spec §2 rule 4).

- [ ] **Step 5: Commit**

```bash
git add python/tools/reproduction/analysis python/tools/reproduction/spec.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): the stdlib analysis and the frozen spec"
```

---

### Task 8: Run, assess, replay, verify (path steps 5–7)

**Files:**
- Create: `python/tools/reproduction/run.py`

**Interfaces:**
- Consumes: `spec.*`; `state.held_file`, `state.dataset_address`; `paths.SCRATCH`.
- Produces: `state.json` gains `original_run_address`, `replayed_run_address`, `assessment_identity`, `assessment_ref`, `verification_scope`, `verification_verdict`, `assessment_outcome`; the run publications, act-reports and assessment record on disk; `run.port() -> DurableOperationPort`.

The boundary: `execute_assessment_run(spec=, port=, boundary_policy=CONFINED_POLICY, definition=, code_roots=(CODE_ROOT,), held_inputs={dataset_address: Path}, entrypoint=, targets=, declared_outputs=, observer=, started_at=, host_realization=, scratch_base=, cores=1) -> RunMinted | RunRefused`. The port over the real root is `DurableOperationPort(root, backend=select_backend(), storage=PRODUCTION_STORAGE, metadata_root=metadata_root_for(root), authority=AUTHORITY)` (`test_operation_port.durable_port`'s shape, with `select_backend` from `atoms.fs.platform` and `PRODUCTION_STORAGE`, `metadata_root_for` from `beliefs.root`). The replay is `beliefs.replay.replay(original, port=, spec=, definition=, code_roots=, held_inputs=, entrypoint=, targets=, declared_outputs=, observer=, started_at=, host_realization=, scratch_base=, cores=)`. Scope is `derive_scope(original.run, replayed.run, certification=None)`; the verification is `build_verification(original.run, replayed.run, specs={id: spec}, held_rules={"impl-eq-1": equivalence()}, contract_identity=, epoch=)`.

- [ ] **Step 1: Write `run.py`**

```python
# python/tools/reproduction/run.py
"""Steps 5-7: confined run, assessment, replay, verification."""
from __future__ import annotations
import sys
from datetime import UTC, datetime
from pathlib import Path
import socket

from atoms.fs.platform import select_backend

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run
from beliefs.recipe import CONFINED_POLICY
from beliefs.replay import CONFORMING, conformance, derive_scope, replay
from beliefs.root import PRODUCTION_STORAGE, DurableOperationPort, metadata_root_for
from beliefs.runrecord import run_ref
from beliefs.verify import AssessmentVerification, build_verification
from reproduction import findings, paths, spec, state, world
from reproduction.authority import AUTHORITY

OBSERVER = "mm30-reproduction-observer"


def port() -> DurableOperationPort:
    return DurableOperationPort(paths.CORPUS_ROOT, backend=select_backend(), storage=PRODUCTION_STORAGE,
                                metadata_root=metadata_root_for(paths.CORPUS_ROOT), authority=AUTHORITY)


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_scope(scope: str, original, replayed) -> None:
    """Spec §2 rule 4: same-environment is the host's; not-certified is authoring or defect."""
    if scope == "clean-environment":
        return
    if scope == "same-environment":
        receipt = replayed.run.occurrence.receipt.execution
        findings.record(7, "host", f"scope same-environment: replay receipt capabilities={receipt.capabilities} instance={'present' if receipt.instance else 'absent'}")
        return
    if conformance(original.run) != CONFORMING or conformance(replayed.run) != CONFORMING:
        findings.record(7, "defect", f"scope {scope}: a closure is non-conforming (original={conformance(original.run)}, replayed={conformance(replayed.run)})")
    else:
        findings.record(7, "corpus-work", f"scope {scope}: recipes disagree; the replay's authored inputs differ from the original's")


def main() -> int:
    st = state.load()
    frozen = spec.frozen()
    held = {st["dataset_address"]: Path(st["held_file"])}
    common = dict(port=port(), definition=spec.definition(), code_roots=(spec.CODE_ROOT,), held_inputs=held,
                  entrypoint=spec.ENTRYPOINT, targets=spec.TARGETS, declared_outputs=spec.TARGETS,
                  observer=OBSERVER, host_realization=socket.gethostname(), cores=1)
    # Step 5
    original = execute_assessment_run(spec=frozen, boundary_policy=CONFINED_POLICY, started_at=now(),
                                      scratch_base=paths.SCRATCH / "original", **common)
    if isinstance(original, RunRefused):
        findings.record(5, "corpus-work" if original.reason in {"held-input-missing", "no-frozen-spec"} else "design-gap",
                        f"run refused: {original.reason}: {original.detail}")
        print(f"REFUSED at run: {original.reason}: {original.detail}")
        return 2
    state.save(original_run_address=original.run.address())
    # Step 6
    assessment = build_assessment(original.run, specs={frozen.identity: frozen}, implementations={spec.interpretation().identity: spec.interpretation()})
    if isinstance(assessment, AssessmentFinding):
        findings.record(6, "defect", f"AssessmentFinding: {assessment.reason}")
        print(f"ASSESSMENT FINDING: {assessment.reason}")
        return 2
    node = stored.assessment_node(
        assessment.identity()[:16], title=f"assessment of {st['proposition_ref']}", spec=frozen.identity,
        run=run_ref(original.run.address()), proposition=st["proposition_ref"], outcome=assessment.outcome,
        interpretation_rule=assessment.interpretation_rule,
        **{k: v for k, v in (("estimate", assessment.estimate), ("uncertainty", assessment.uncertainty),
                             ("estimand", assessment.estimand), ("applicability", assessment.applicability)) if v is not None},
    )
    minted = world.open_writer().add(node)
    state.save(assessment_identity=assessment.identity(), assessment_ref=minted.id, assessment_outcome=assessment.outcome)
    # Step 7
    replayed = replay(original, spec=frozen, started_at=now(), scratch_base=paths.SCRATCH / "replayed", **common)
    if isinstance(replayed, RunRefused):
        findings.record(7, "design-gap", f"replay refused: {replayed.reason}: {replayed.detail}")
        print(f"REFUSED at replay: {replayed.reason}")
        return 2
    scope = derive_scope(original.run, replayed.run, certification=None)
    classify_scope(scope, original, replayed)
    verification = build_verification(original.run, replayed.run, specs={frozen.identity: frozen},
                                      held_rules={spec.equivalence().identity: spec.equivalence()},
                                      contract_identity=world.open_writer().manifest_pins().science_contract,
                                      epoch="none-published")
    assert isinstance(verification, AssessmentVerification), verification
    state.save(replayed_run_address=replayed.run.address(), verification_scope=verification.scope, verification_verdict=verification.verdict)
    print(f"run {original.run.address()[:16]}; assessment {assessment.outcome}; replay scope {verification.scope}; verdict {verification.verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

Run: `cd python && uv run python tools/reproduction/run.py`
Expected: one summary line. Record §3 rows 5, 6, 7 with what is on disk (`ls .mm30-reproduction/corpus/run .mm30-reproduction/corpus/act-report .mm30-reproduction/corpus/assessment`). Record P4 and P7 outcomes. If `RunRefused` with `execution-failed`, the detail names the analysis error: fix **the analysis code** (it is the exercise's own instrument) and rerun; that is not a change to the target, spec identity notwithstanding — note that a code change moves `code_identity` and therefore the run's recipe, and say so in the record.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/run.py
git commit -m "feat(reproduction): confined run, assessment, replay and verification"
```

---

### Task 9: Admit and compute belief (path step 8)

**Files:**
- Create: `python/tools/reproduction/belief.py`

**Interfaces:**
- Consumes: everything in `state.json`; `spec.*`; `vocabulary.profile()`; `run.port()` is not needed.
- Produces: `state.json` gains `verification_ref`, `admission`, `belief_answer` (a JSON-able dict: kind and value or reason); the verification record on disk.

Shape from the cut-13 acceptance test: `admission_record(verification) -> Verification`; the stored record is `stored.verification_node(slug, title=, assessment=<assessment identity>, assessment_ref=<corpus ref>, scope=, verdict=, derivation=(original run ref, replayed run ref))`; `admit(assessment, run_record(run), observations, (record,))`; `evaluate(proposition=, records=Records(...), availability=Availability(...), context=SuppliedContext(...), binding=PolicyBinding(BELIEF_V1_RULE, BELIEF_V1.identity), profile=)`.

- [ ] **Step 1: Write `belief.py`**

```python
# python/tools/reproduction/belief.py
"""Step 8: admit the verification and ask the evaluator."""
from __future__ import annotations
import sys
from dataclasses import asdict

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.assess import run_record
from beliefs.belief import Availability, Belief, NoBelief, Records, Refused, SuppliedContext, evaluate
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import lineage_snapshot
from beliefs.dataset import ByteObservation
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.runrecord import decode_run_closure, run_ref
from beliefs.verify import AssessmentVerification, admission_record, build_verification
from reproduction import findings, spec, state, vocabulary, world


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    original = decode_run_closure(view.get(run_ref(st["original_run_address"])))
    replayed = decode_run_closure(view.get(run_ref(st["replayed_run_address"])))
    frozen = spec.frozen()
    verification = build_verification(original, replayed, specs={frozen.identity: frozen},
                                      held_rules={spec.equivalence().identity: spec.equivalence()},
                                      contract_identity=writer.manifest_pins().science_contract, epoch="none-published")
    assert isinstance(verification, AssessmentVerification)
    record = admission_record(verification)
    node = stored.verification_node(
        record.ref[:16], title=f"verification of {st['assessment_ref']}", assessment=st["assessment_identity"],
        assessment_ref=st["assessment_ref"], scope=record.scope, verdict=record.verdict,
        derivation=(run_ref(st["original_run_address"]), run_ref(st["replayed_run_address"])),
    )
    minted = writer.add(node)
    assessment = stored.assessment_value(view.get(st["assessment_ref"]))
    run_value = run_record(original)
    observations = {st["dataset_address"]: (ByteObservation(digest=st["held_digest"], location=f"store:{st['store_id']}:{st['store_relative_path']}"),)}
    verdict = admit(assessment, run_value, observations, (record,))
    state.save(verification_ref=minted.id, admission=type(verdict).__name__ + (": " + verdict.reason if not isinstance(verdict, Admitted) else ""))
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, [st["dataset_address"]]),
        producer_snapshot_identity="no-epoch-published",  # supplied, not derived: no epoch is built by this exercise (recorded)
        retractions=RetractionEnumeration(found=(), coverage=(st["corpus_id"],)),
        node_corpus={assessment.identity(): st["corpus_id"]},
        pins={st["corpus_id"]: writer.manifest_pins()},
    )
    answer = evaluate(
        proposition=st["proposition_ref"],
        records=Records(claims={}, assessments=(assessment,), runs={run_value.ref: run_value}, source_assertions=(), verifications=(record,)),
        availability=Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES}),
        context=context,
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        profile=vocabulary.profile(),
    )
    if isinstance(answer, Belief):
        payload = {"kind": "Belief", **asdict(answer)}
    elif isinstance(answer, NoBelief):
        payload = {"kind": "NoBelief", "reason": answer.reason}
    else:
        payload = {"kind": "Refused", "reason": answer.reason}
        findings.record(8, "design-gap", f"evaluate refused: {answer.reason}")
    state.save(belief_answer=payload)
    print(f"admission {state.load()['admission']}; answer {payload}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

If `Belief`'s dataclass fields are not `asdict`-able, replace the `asdict` line with the explicit fields `belief.py:95–105` declares; read them before running.

- [ ] **Step 2: Run it and apply spec §2 rule 4**

Run: `cd python && uv run python tools/reproduction/belief.py`
Record §3 row 8 with the answer verbatim. Then classify:
- `Belief` → terminal.
- `NoBelief("no-directional-outcome")` → terminal; the analysis read `inconclusive`; record as a scientific result.
- `NoBelief("no-eligible-assessment")` → terminal **only after** Task 8's scope classification is read: the record cites the `derive_scope` result and the finding class (`host` for `same-environment`, `defect`/`corpus-work` for `not-certified`) beside the reason.
- `Refused(...)` → a finding, already recorded; stop the path here and continue with Tasks 10–12 over what exists.

The `producer_snapshot_identity` is **supplied**; no epoch is built by this exercise. Record that as a limitation of step 8 in the record's §3: the belief closure digests a member this run did not derive.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/belief.py
git commit -m "feat(reproduction): admit the verification and compute belief"
```

---

### Task 10: Close the corpus (path step 9)

**Files:**
- Create: `python/tools/reproduction/close.py`

**Interfaces:**
- Consumes: `state.json`; `spec.*`.
- Produces: `state.json` gains `corpus_check_findings` (count), `audit_findings` (count), `log_verdict`; each finding classified in `findings.jsonl`.

`corpus_check(view) -> tuple[Finding, ...]`; `audit_corpus(view, evidence=DerivationEvidence(specs=, held_rules=, implementations=))`; `audit_log(config, subject, target_root, observers, actor=)` from `beliefs.root` with `CorpusSubject` from `beliefs.world.anchors` and an `ObserverSet` — read `beliefs.world.verify` for `ObserverSet`'s constructor and the one-observer case (the world root itself) before writing the call; if a one-observer set is not constructible without an exported head artifact, call the audit over the world's own registry carrier and record the shape used.

- [ ] **Step 1: Write `close.py`**

```python
# python/tools/reproduction/close.py
"""Step 9: corpus_check, the semantic audit, log verification. Writes nothing."""
from __future__ import annotations
import sys

from beliefs.audit import DerivationEvidence, audit_corpus
from beliefs.corpus import corpus_check
from reproduction import findings, spec, state, world


def main() -> int:
    view = world.open_writer().read_view
    checks = corpus_check(view)
    for f in checks:
        findings.record(9, "defect", f"corpus_check: {f.code}: {f.detail}")
    evidence = DerivationEvidence(specs={spec.frozen().identity: spec.frozen()},
                                  held_rules={spec.equivalence().identity: spec.equivalence()},
                                  implementations={spec.interpretation().identity: spec.interpretation()})
    audits = audit_corpus(view, evidence=evidence)
    for f in audits:
        cls = "defect" if f.code in {"derivation-contradicted"} else "design-gap"
        findings.record(9, cls, f"audit_corpus: {f.code}: {f.detail}")
    state.save(corpus_check_findings=len(checks), audit_findings=len(audits))
    print(f"corpus_check: {len(checks)} findings; audit_corpus: {len(audits)} findings")
    for f in (*checks, *audits):
        print(f"  {f.code}: {f.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Then add the log audit call per the note above, storing `log_verdict` from the returned `LogReport`.

- [ ] **Step 2: Run it**

Run: `cd python && uv run python tools/reproduction/close.py`. Record §3 row 9: counts and every finding by code. Zero findings is the expected outcome and is stated as such; a `derivation-unchecked` on the verification record is expected if the audit cannot read the stored closures, and is recorded as design-gap feeding 10b.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/close.py
git commit -m "feat(reproduction): close the corpus under check, audit and log verification"
```

---

### Task 11: Re-derive in a fresh process (path steps 10a and 10b)

**Files:**
- Create: `python/tools/reproduction/rederive.py`

**Interfaces:**
- Consumes: **only** the corpus on disk, `state.json`'s refs, `vocabulary.profile()`, `spec.held_rules()` (the rule implementations are in-process code; they are not stored, and that is itself reported).
- Produces: `state.json` gains `rederived_belief` and `rederived_equal` (10a), `evidence_reconstruction` (10b: which of `comparison report`, `scope`, `verdict` were recoverable, and from what).

Run this in a **new interpreter** after Tasks 8–10, never in the same process. 10a uses `evaluate_over(view, proposition, availability=, context=, profile=, resolution=, binding=)`, which gathers the stored assessment, run, dataset, verification and claim through the instrumented resolver. 10b attempts three reconstructions, each reported separately: (i) `stored.verification_derivation(node)` names two run refs; (ii) `decode_run_closure` on both stored run publications yields two `RunClosure`s; (iii) `build_verification` over them with the held rules recovers a verification whose `scope` and `verdict` are compared to the stored ones, and whose comparison report exists only in this recomputation — the stored record has none. `audit.check_verification` is run beside it and its `DerivationOutcome` recorded.

- [ ] **Step 1: Write `rederive.py`**

```python
# python/tools/reproduction/rederive.py
"""Steps 10a/10b, in a fresh process, from the corpus on disk alone."""
from __future__ import annotations
import json
import sys

from beliefs import stored
from beliefs.audit import DerivationEvidence, check_verification
from beliefs.belief import Availability, Belief, NoBelief, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import lineage_snapshot
from beliefs.dataset import ByteObservation
from beliefs.evaluation import evaluate_over
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification
from reproduction import findings, spec, state, vocabulary, world


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    proposition = view.get(st["proposition_ref"])
    terms = tuple(proposition.facets[stored.PROPOSITION_FACET]["args"])
    observations = {st["dataset_address"]: (ByteObservation(digest=st["held_digest"], location=f"store:{st['store_id']}:{st['store_relative_path']}"),)}
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, [st["dataset_address"]]),
        producer_snapshot_identity="no-epoch-published",
        retractions=RetractionEnumeration(found=(), coverage=(st["corpus_id"],)),
        node_corpus={st["assessment_identity"]: st["corpus_id"]},
        pins={st["corpus_id"]: writer.manifest_pins()},
    )
    # 10a
    answer = evaluate_over(view, st["proposition_ref"], availability=Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES}),
                           context=context, profile=vocabulary.profile(), resolution=vocabulary.snapshot(terms),
                           binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity))
    rederived = {"kind": type(answer).__name__, **({"reason": answer.reason} if not isinstance(answer, Belief) else {})}
    equal = rederived["kind"] == st["belief_answer"]["kind"] and rederived.get("reason") == st["belief_answer"].get("reason")
    state.save(rederived_belief=rederived, rederived_equal=equal)
    # 10b
    node = view.get(st["verification_ref"])
    report: dict = {"derivation_named": False, "closures_decoded": False, "scope_recomputed": None, "verdict_recomputed": None, "comparison_report_stored": False}
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        report["scope_recomputed"] = derive_scope(original, replayed, certification=None)
        rebuilt = build_verification(original, replayed, specs={spec.frozen().identity: spec.frozen()}, held_rules={spec.equivalence().identity: spec.equivalence()},
                                     contract_identity=writer.manifest_pins().science_contract, epoch="none-published")
        report["verdict_recomputed"] = rebuilt.verdict if isinstance(rebuilt, AssessmentVerification) else type(rebuilt).__name__
        report["comparison_report_stored"] = "comparison" in node.facets.get(stored.VERIFICATION_FACET, {})
    outcome = check_verification(view, node, evidence=DerivationEvidence(specs={spec.frozen().identity: spec.frozen()}, held_rules={spec.equivalence().identity: spec.equivalence()}, implementations={spec.interpretation().identity: spec.interpretation()}))
    report["audit_check"] = {"checked": outcome.checked, "reason": outcome.reason}
    state.save(evidence_reconstruction=report)
    if not report["comparison_report_stored"]:
        findings.record(10, "design-gap", "no stored record carries the comparison report; scope and verdict recover only by recomputation over both stored closures with in-process rule implementations", filed="verification-publication (write-path lane)")
    print(json.dumps({"10a": rederived, "equal": equal, "10b": report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Confirm `check_verification`'s parameter names against `audit.py:113` before running; adjust the call, not the reading.

- [ ] **Step 2: Run it in a fresh interpreter**

Run: `cd python && uv run python tools/reproduction/rederive.py`
Record §3 rows 10a and 10b separately, and answer spec §6 question 3 from 10b only. Record P5's outcome in both halves. If 10a's `gather` finds no assessment (the `spec.target` namespace question from Task 7), that is the design-gap finding on what `target` names; file it and answer 10a as *not re-derivable for that reason*.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/rederive.py
git commit -m "feat(reproduction): fresh-process re-derivation of belief and verification evidence"
```

---

### Task 12: The record, the findings, and the re-rank

**Files:**
- Modify: `docs/designs/2026-09-DD-mm30-reproduction.md` (rename to the completion date)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md` (re-rank under the method's second trigger)
- Modify: `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` (status line only)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` only if a boundary changes tier; `docs/guide/open-questions.md` for any finding that is a question

- [ ] **Step 1: Complete the record.** For every row of §3, the outcome and what is on disk. For every prediction P1–P7, `confirmed`, `confirmed for another reason: <reason>`, or `refuted`, with the evidence line from `state.json` or `findings.jsonl`. §5: the three questions, question 1 marked *unmeasured* if Task 4 typed under the placeholder. §6: every line of `findings.jsonl` with where it was filed. §7: the authoring cost from Task 5 in minutes and the number of propositions typed. Add `## 8. What this run does not claim` in the results-record convention: no cut, no row, one proposition, one host, the supplied producer snapshot identity, in-process rule implementations.

- [ ] **Step 2: File each finding through its owning lane.** A design gap becomes a dated amendment proposal in a task record under `tasks/` addressed to the owning lane (write-path, domain, or the computation design's owner), not an edit from this worktree. A question becomes an `open-questions.md` bullet in this commit. A defect becomes a task naming the failing test to write.

- [ ] **Step 3: Re-rank.** Rewrite the roadmap whole per its method: `verification-publication` stays on the path if 10b failed and leaves it if 10b passed; `domain-boundary`'s placement carries question 1's answer; `world-resolution`'s carries question 2's. `Ranked at` stays at the newest results record; the `Method` line names this record as the second-trigger amendment.

- [ ] **Step 4: Gates**

```bash
cd python && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py tests/test_reproduction_driver.py -q
uv run python tools/check_guide.py
cd .. && git diff --check
```

Expected: all pass. The roadmap/ledger guard fails if a boundary left one document and not the other.

- [ ] **Step 5: Commit and hand off**

```bash
git add docs python/tools/reproduction tasks
git commit -m "docs(reproduction): record the mm30 reproduction and re-rank the roadmap"
```

The `--no-ff` merge into `main` is the human partner's. The corpus under `.mm30-reproduction/` is left in place; it is the deliverable's second half and the seed of the dogfood world.

---

## Self-review against the spec

- **§2 rules 1–4:** rule 1 in Global Constraints and Task 2 step 4; rule 2 in every task's refusal branch and `findings.py`'s closed classes; rule 3 in Task 9 step 2; rule 4 in Task 7 step 4 and Task 8's `classify_scope`.
- **§3 target criteria:** Task 2's `rank` and step 3's relaxation order.
- **§4 rows 1–10b:** Tasks 3, 4–5, 6, 7, 8 (rows 5–7), 9, 10, 11.
- **§5 P1–P7:** P1 at Task 5 step 2; P2, P3 at Task 6; P4, P7 at Task 8; P5 at Task 11; P6 at Task 12. One unpredicted finding, the result-manifest interpretation seam, is recorded at Task 7 as such.
- **§6 questions 1–3:** Task 4 (question 1, with the unmeasured branch), Task 11 (questions 2 and 3; question 2 is answered by whether any step needed a resolver beyond the registry, which none of Tasks 3–11 calls).
- **§7 classes:** `findings.py` admits exactly `design-gap`, `corpus-work`, `defect`, plus `host` for rule 4's `same-environment` case.
- **§8 deliverables:** record (Task 12), corpus (left on the volume), scripts under `python/tools/reproduction/`, amendments (Task 12 step 2), re-rank (Task 12 step 3).
- **§10 lane discipline:** worktree `.worktrees/mm30`; no file under `python/src/beliefs/` in any task's Files list.
- **Type consistency:** `state.json` keys are named once in the File structure note and used identically across Tasks 3–11; `spec.frozen()`, `spec.interpretation()`, `spec.equivalence()`, `spec.definition()` are the only cross-task callables and are defined in Task 7 before Tasks 8–11 use them.
