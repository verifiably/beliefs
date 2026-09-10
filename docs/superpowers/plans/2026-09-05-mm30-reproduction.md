# The mm30 reproduction — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Push one real mm30 proposition through the `beliefs` kernel as a library, from a registered world to the belief evaluator's answer, and record every refusal, prediction and finding in a dated measurement record.

**Architecture:** A throwaway driver package under `python/tools/reproduction/` composes the kernel's public seams in the order the design's §4 fixes — world and corpus, typing, holding, spec, confined run, assessment, replay and verification, admission and belief, corpus close, and a fresh-process re-derivation split into belief equality and evidence reconstruction. Every governed record is minted through `open_corpus`'s `CorpusWriter` under one full `Authority`. Every identity a later step needs is read back from the corpus, never carried across from a Python object, so that the bridges between the kernel's value spellings (bare run addresses, typed run refs, content-address dataset ids) are crossed explicitly and once. No kernel module is edited from this lane. The record under `docs/designs/` is the deliverable, and its commit re-ranks the roadmap.

**Tech Stack:** Python 3.13 via `uv` in `python/`; the `beliefs` package and its `atoms`/`nodes` substrates; Snakemake through the kernel's confined boundary (bubblewrap); pytest for the driver's own unit tests.

**Spec:** `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` — read §2 (the four rules), §4 (the path), §5 (predictions P1–P7), §6 (the three questions) and §7 (the findings classes) before any task.

## Global Constraints

- **Reproduce, never migrate** (spec §2 rule 1): no file under the predecessor's `entities/`, `knowledge/` or `results/` is copied into the corpus. Its records are read to decide what to reproduce; its data files are re-held by content identity.
- **A refusal is a finding** (spec §2 rule 2): a `Refused`, `RunRefused`, `WriteRefused`, `PermitExceeded` or `AssessmentFinding` is recorded and classified under spec §7 (design gap / corpus work / defect / host). It is never retried with altered inputs, never suppressed, never worked around by a second write path.
- **The target, spec and interpretation rule are fixed at Task 7** (spec §2 rule 4) and are not changed afterwards to obtain a belief. `NoBelief` with an attributable reason is a terminal, complete outcome, classified as Task 8 step 3 says.
- **The driver's own mistakes are not findings.** Every bridge between kernel spellings is crossed by reading the stored record back (Tasks 6, 8, 9); every instrument failure in the analysis exits non-zero and becomes `RunRefused(execution-failed)`, never an outcome (Task 7). A failure traced to the driver is fixed in the driver and noted in the record's §8, not filed under §7.
- **One invocation convention.** Every driver module runs as `cd python && PYTHONPATH=tools uv run python -m reproduction.<module>`. `python/tools/` has no `__init__.py`; `reproduction/` is the package and `tools/` its parent on `PYTHONPATH`. Tests insert `tools/` on `sys.path` the same way.
- **The corpus lives on the certified volume beside the checkout**, never under `/tmp`, `/dev/shm` or the scratch volume. The work directory is `<repo>/.mm30-reproduction/` or `$SCIENCE_MM30_ROOT`.
- **No code under `python/src/beliefs/`** changes from this lane. Findings for kernel surfaces are filed as dated design amendments or `open-questions.md` entries through the owning lane (roadmap concurrency rule 6). A defect becomes a failing test in the owning lane, not a patch here.
- **The analysis is standard-library Python only**, and it refuses malformed input loudly (Task 7). If the chosen analysis genuinely needs a package, that is a finding, not a reason to relax confinement.
- **Ontology membership is never manufactured.** The resolution snapshot declares nothing readable; every binding is `not-consulted` unless a held ontology release supplies membership (Task 3). Question 1 is answered *unmeasured* in that case.
- **Sidecars are for references, not evidence.** `state.json` carries corpus refs and identities; `target.yaml` carries the selection. Neither supplies evidence to steps 9 or 10. Anything step 10 needs that the corpus does not hold is reported by name and labelled *sidecar* or *in-process*, never folded into "from the corpus alone" (Task 11).
- **Predictions are answered, never edited.** Spec §5's P1–P7 are copied verbatim into the record at Task 1 and each is marked at Task 12.
- **Every script is throwaway by declaration** (spec §8 item 3).
- Use the project venv: `cd python && uv run ...`. Commit messages use conventional commits with no AI attribution trailer.

---

## File structure

| path | responsibility |
|---|---|
| `.worktrees/mm30/` | the lane's worktree on branch `measure/mm30-reproduction`, from `main` after the course-correction branch merges |
| `python/tools/reproduction/__init__.py` | empty |
| `python/tools/reproduction/paths.py` | the work directory, the predecessor root, the fixed sub-paths |
| `python/tools/reproduction/authority.py` | the one `Authority` every act binds |
| `python/tools/reproduction/state.py` | `state.json`: refs and identities only (see the key table below) |
| `python/tools/reproduction/findings.py` | `findings.jsonl` writer with the four closed classes |
| `python/tools/reproduction/answers.py` | `payload(answer)`: the one serialization of a `Belief`/`NoBelief`/`Refused` both step 8 and step 10a use |
| `python/tools/reproduction/preflight.py` | step 0 |
| `python/tools/reproduction/select_target.py` | Task 2 |
| `python/tools/reproduction/vocabulary.py`, `mm30-reproduction.yaml` | Task 3: contract, profile, namespaced plan, snapshot |
| `python/tools/reproduction/world.py` | Task 4: world, corpus, store |
| `python/tools/reproduction/type_target.py` | Task 5 |
| `python/tools/reproduction/hold.py` | Task 6 |
| `python/tools/reproduction/analysis/workflow/Snakefile.template`, `analysis/assoc.py` | Task 7: the held code root (bundle name `analysis`) |
| `python/tools/reproduction/spec.py` | Task 7: rendered Snakefile, frozen spec, rule implementations, the `analysis-spec` record |
| `python/tools/reproduction/run.py` | Task 8: confined run, assessment, replay, verification |
| `python/tools/reproduction/belief.py` | Task 9: verification record, admission, `evaluate_over` |
| `python/tools/reproduction/close.py` | Task 10 |
| `python/tools/reproduction/rederive.py` | Task 11 |
| `python/tests/test_reproduction_driver.py` | unit tests: ranking, outcome digests, analysis validation, answer payload, scope classification, id bridges |
| `docs/designs/2026-09-DD-mm30-reproduction.md` | the record |

**`state.json` keys**, each written by exactly one task and read by later ones. Values are corpus refs, identities, or paths; no digests of evidence except `held_digest`, which Task 6 writes for the *record* and which Tasks 9 and 11 do **not** read (they read the stored holdings observation instead).

| key | written by | value |
|---|---|---|
| `target`, `dataset` | 2 | predecessor ids |
| `world_id`, `corpus_id`, `store_id` | 4 | |
| `proposition_ref`, `claim_identity`, `typing_seconds` | 5 | `proposition:<slug>` |
| `dataset_ref`, `dataset_address`, `held_file`, `held_digest`, `store_relative_path`, `holdings_observation_ref` | 6 | `dataset_ref == dataset_address` by construction |
| `spec_identity`, `spec_ref`, `held_name` | 7 | `analysis-spec:<identity>` |
| `original_run_ref`, `replayed_run_ref`, `assessment_ref`, `assessment_identity_stored`, `assessment_identity_derived`, `assessment_outcome`, `verification_scope`, `verification_verdict`, `scope_class` | 8 | typed `run:<hash>` refs; two identities, see Task 8 |
| `verification_ref`, `admission`, `belief_answer` | 9 | `belief_answer` is `answers.payload(...)` |
| `corpus_check_findings`, `audit_findings`, `log_verdict` | 10 | |
| `rederived_belief`, `rederived_equal`, `evidence_reconstruction` | 11 | |

---

### Task 1: Lane setup, preflight, shared modules, the record skeleton

**Files:**
- Create: `python/tools/reproduction/__init__.py`, `paths.py`, `authority.py`, `state.py`, `findings.py`, `answers.py`, `preflight.py`
- Create: `docs/designs/2026-09-DD-mm30-reproduction.md`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `paths.WORK, PREDECESSOR, WORLD_ROOT, CORPUS_ROOT, STORE_ROOT, SCRATCH, STATE, FINDINGS, TARGET: Path`; `authority.AUTHORITY: Authority`; `state.load() -> dict`, `state.save(**fields)`; `findings.record(step: int, cls: str, reason: str, filed: str = "unfiled")`; `answers.payload(answer) -> dict`; `preflight.main() -> int`.

- [ ] **Step 1: Create the worktree**

```bash
cd <repo> && git worktree add -b measure/mm30-reproduction .worktrees/mm30 main
cd .worktrees/mm30/python && uv sync --quiet
```

- [ ] **Step 2: Write the shared modules**

```python
# python/tools/reproduction/paths.py
from __future__ import annotations
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORK = Path(os.environ.get("SCIENCE_MM30_ROOT", REPO / ".mm30-reproduction"))
PREDECESSOR = Path(os.environ.get("MM30_PREDECESSOR", Path.home() / "d" / "cancer" / "cancer-types" / "multiple-myeloma"))
WORLD_ROOT, CORPUS_ROOT, STORE_ROOT, SCRATCH = WORK / "world", WORK / "corpus", WORK / "store", WORK / "scratch"
STATE, FINDINGS, TARGET = WORK / "state.json", WORK / "findings.jsonl", WORK / "target.yaml"
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
        out.write(json.dumps({"at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "step": step,
                              "class": cls, "reason": reason, "filed": filed}, sort_keys=True) + "\n")
```

```python
# python/tools/reproduction/answers.py
"""One serialization of the evaluator's answer, used by step 8 and step 10a alike.
A Belief is its value, its input digest and its policy binding; dropping any
of the three would let Belief(1) compare equal to Belief(99)."""
from __future__ import annotations
from beliefs.belief import Belief, NoBelief, Refused

def payload(answer: Belief | NoBelief | Refused) -> dict:
    if isinstance(answer, Belief):
        return {"kind": "Belief", "value": answer.value, "belief_input_digest": answer.belief_input_digest,
                "policy_binding": [answer.policy_binding.rule, answer.policy_binding.implementation]}
    if isinstance(answer, NoBelief):
        return {"kind": "NoBelief", "reason": answer.reason, "detail": answer.detail}
    if isinstance(answer, Refused):
        return {"kind": "Refused", "reason": answer.reason}
    raise TypeError(f"not an evaluator answer: {type(answer).__name__}")
```

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
    if (reason := host_prerequisites()) is not None:
        print(f"REFUSED: confinement unavailable on this host: {reason}")
        return 2
    if not (paths.PREDECESSOR / "science.yaml").exists():
        print(f"REFUSED: predecessor corpus not found at {paths.PREDECESSOR}")
        return 2
    print(f"ok: certified volume at {paths.WORK}; confinement available; predecessor at {paths.PREDECESSOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Write the failing tests for `findings` and `answers`**

```python
# python/tests/test_reproduction_driver.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from reproduction import answers, findings  # noqa: E402
from beliefs.belief import Belief, NoBelief  # noqa: E402
from beliefs.policy import PolicyBinding  # noqa: E402


def test_a_finding_class_outside_the_four_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(findings.paths, "FINDINGS", tmp_path / "f.jsonl")
    with pytest.raises(ValueError):
        findings.record(1, "oops", "reason")


def test_answer_payload_distinguishes_beliefs_by_value_and_digest():
    binding = PolicyBinding(rule="science.belief.v1", implementation="impl-1")
    one = answers.payload(Belief(1, "sha256:" + "a" * 64, binding))
    other = answers.payload(Belief(99, "sha256:" + "b" * 64, binding))
    assert one != other and one["value"] == 1 and other["belief_input_digest"].endswith("b" * 64)
    assert answers.payload(NoBelief("no-eligible-assessment")) == {"kind": "NoBelief", "reason": "no-eligible-assessment", "detail": ""}
```

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q` → FAIL (`ModuleNotFoundError: reproduction`) before Step 2's files exist, PASS after. If `Belief`'s constructor order differs from `(value, belief_input_digest, policy_binding)`, use keywords.

- [ ] **Step 4: Run preflight**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.preflight`
Expected: `ok: ...`, exit 0. A `REFUSED` line is the record's first entry and the exercise stops.

- [ ] **Step 5: Write the record skeleton** at `docs/designs/2026-09-DD-mm30-reproduction.md`: `# The mm30 reproduction — record`; `**Status:** in progress`; `## 1. Preflight`; `## 2. Target`; `## 3. The path` (table rows 1–10b: *step / outcome / left on disk*, all `pending`); `## 4. Predictions` (P1–P7 verbatim from spec §5, each `**Outcome:** pending`); `## 5. Questions` (spec §6's three); `## 6. Findings` (table: step / class / reason / filed); `## 7. Authoring cost`; `## 8. Driver corrections` (mistakes fixed in the driver during the run, kept apart from §6).

- [ ] **Step 6: Commit**

```bash
git add python/tools/reproduction python/tests/test_reproduction_driver.py docs/designs/2026-09-DD-mm30-reproduction.md
git commit -m "chore(reproduction): lane setup, preflight, shared modules and the record skeleton"
```

---

### Task 2: Select the target

**Files:**
- Create: `python/tools/reproduction/select_target.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `target.yaml` with `proposition_id, subject, predicate, object, claim_layer, polarity, identification_strength, dataset_id, dataset_path, dataset_bytes, evidence_line_ids, alternatives`; after step 4, also `held_file` (basename under `dataset_path`), `value_column`, `group_column`, `positive_level`; `select_target.rank(candidates) -> list[dict]` (pure).

Measured 2026-09-05 in the predecessor: 307 structured propositions; 225 empirical, eligible evidence lines each naming `target: proposition:<slug>`; 42 dataset records whose `local_path` or `datapackage` resolves on disk; no proposition carries `evidence_refs`.

- [ ] **Step 1: Write the failing test for `rank`**

```python
def test_rank_prefers_empirical_locally_held_small_targets():
    from reproduction.select_target import rank
    a = {"proposition_id": "p:a", "claim_layer": "causal_effect", "dataset_bytes": 2_000_000, "empirical_lines": 3}
    b = {"proposition_id": "p:b", "claim_layer": "structural_claim", "dataset_bytes": 1_000, "empirical_lines": 5}
    c = {"proposition_id": "p:c", "claim_layer": "empirical_regularity", "dataset_bytes": 50_000, "empirical_lines": 1}
    ordered = [r["proposition_id"] for r in rank([a, b, c])]
    assert ordered == ["p:c", "p:a", "p:b"]
```

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
    """Empirical layer first, then the smallest held dataset, then the most
    empirical evidence lines; the id breaks ties so the order is total."""
    return sorted(candidates, key=lambda c: (0 if c["claim_layer"] in EMPIRICAL_LAYERS else 1,
                                             c["dataset_bytes"], -c["empirical_lines"], c["proposition_id"]))


def dataset_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) if root.is_dir() else root.stat().st_size


def main() -> int:
    root = paths.PREDECESSOR
    propositions = {f["id"]: f for p in (root / "entities" / "propositions").glob("*.md")
                    if (f := front(p)).get("predicate") and f.get("subject") and f.get("object")}
    lines: dict[str, list[dict]] = defaultdict(list)
    for p in (root / "entities" / "evidence-lines").glob("*.md"):
        f = front(p)
        if f.get("evidence_type") == "empirical_data" and f.get("belief_eligible") is True:
            lines[f.get("target")].append(f)
    datasets: dict[str, Path] = {}
    for p in (root / "entities" / "datasets").glob("*.md"):
        f = front(p)
        local = f.get("local_path") or (str(Path(f["datapackage"]).parent) if f.get("datapackage") else "")
        if local and (root / local).exists():
            datasets[f["id"]] = (root / local).resolve()
    candidates = []
    for pid, prop in propositions.items():
        if pid not in lines:
            continue
        named = set(prop.get("datasets") or []) | {r for r in (prop.get("related") or []) if str(r).startswith("dataset:")}
        for line in lines[pid]:
            named |= {r for r in (line.get("related") or []) if str(r).startswith("dataset:")}
        for did in sorted(named):
            if did in datasets:
                candidates.append({
                    "proposition_id": pid, "subject": prop["subject"], "predicate": prop["predicate"], "object": prop["object"],
                    "claim_layer": prop.get("claim_layer"), "polarity": prop.get("polarity"),
                    "identification_strength": prop.get("identification_strength"),
                    "dataset_id": did, "dataset_path": str(datasets[did]), "dataset_bytes": dataset_bytes(datasets[did]),
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
Run: `PYTHONPATH=tools uv run python -m reproduction.select_target`.
If exit 2: widen the join to the evidence lines' `source` records (an `interpretation:` under `entities/interpretations/` or a task id under `tasks/`) and their `datasets` fields, relaxing *small* first and *locally held* last. Record which relaxation was needed in the record's §2.

- [ ] **Step 4: Fix the analysis inputs into `target.yaml`.** Read the chosen evidence lines and their sources. Write into the record's §2 what the predecessor computed and which file under `dataset_path` carries it. Then append to `target.yaml` by hand: `held_file` (the one regular file the analysis reads, its basename), `value_column`, `group_column`, `positive_level` (the level of `group_column` in which the proposition predicts the higher `value_column`), all as they appear in that file's header. If the computation is not expressible in standard-library Python over one file, take the next alternative and say why.

  *Superseded 2026-09-10 (`beliefs-efc32d`): the by-hand append is replaced by step 2a, `analysis_inputs.py`, which derives the keys from the selection, the dataset record, the held file's header and the checked-in `analysis-inputs.yaml`.*

- [ ] **Step 5: Commit**

```bash
git add python/tools/reproduction/select_target.py python/tests/test_reproduction_driver.py docs/designs/2026-09-DD-mm30-reproduction.md
git commit -m "feat(reproduction): select the target proposition under the four criteria"
```

---

### Task 3: The domain contract, the compiled profile, the namespaced plan, the snapshot

**Files:**
- Create: `python/tools/reproduction/vocabulary.py`, `python/tools/reproduction/mm30-reproduction.yaml`

**Interfaces:**
- Consumes: `python/tools/vocabularies/mm30-modal-sorted.yaml` (read only); `contracts/science/CONTRACT.yaml`.
- Produces: `vocabulary.base() -> BaseContract`, `contract() -> DomainContract`, `profile() -> ProfileSpec`, `plan() -> dict` (**namespaced**: `operators` and `sorts` values are `contract().term(local)`, as `type_corpus_claims.run` resolves them), `pins() -> CorpusPins`, `snapshot() -> ResolutionSnapshot`.

**Question 1 is answered here as unmeasured unless real membership data exists.** Both typing vocabularies bind only the placeholder `mm30-entities` namespace at release `2026-08-07`. A `ResolutionSnapshot` that declared the target's terms readable and present in a real ontology namespace would be an invented membership fact. The snapshot therefore declares **nothing readable** — every binding is `not-consulted`, which D3 admits for minting and decode (only `not-member` refuses) — and the record says so. The only path to a measured answer is a held ontology release the exercise reads membership from, and that is the domain lane's work, not this exercise's.

- [ ] **Step 1: Write `mm30-reproduction.yaml`**: copy the `contract:` and `plan:` blocks from `python/tools/vocabularies/mm30-modal-sorted.yaml` verbatim; set `contract.contract: mm30-reproduction`; leave every `vocabulary:` binding as the placeholder. Add a header comment stating that the binding is the placeholder and question 1 is unmeasured.

- [ ] **Step 2: Write `vocabulary.py`**

```python
# python/tools/reproduction/vocabulary.py
from __future__ import annotations
from functools import cache
from pathlib import Path

import yaml

from beliefs.consulted import CorpusPins
from beliefs.contract import load_base_contract
from beliefs.contract.domain import DomainContract, parse_domain_contract
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
    """The typing tool's resolution, repeated exactly: local names are
    namespaced once, here, through the contract's own `term`."""
    raw = _document()["plan"]
    return {
        "operators": {k: contract().term(v) for k, v in (raw.get("operators") or {}).items()},
        "sorts": {k: contract().term(v) for k, v in (raw.get("sorts") or {}).items()},
        "layers": dict(raw.get("layers") or {}),
        "polarities": dict(raw.get("polarities") or {}),
    }


def pins() -> CorpusPins:
    return CorpusPins(
        science_contract=f"science:{base().content_identity}",
        domains={contract().namespace: f"{contract().namespace}:{contract().content_identity}"},
    )


def snapshot() -> ResolutionSnapshot:
    """Nothing readable: every binding is `not-consulted`. No membership is
    asserted for any term, in any namespace (question 1: unmeasured)."""
    return build_snapshot()
```

- [ ] **Step 3: Check compilation and the namespacing**

Run: `cd python && PYTHONPATH=tools uv run python -c "from reproduction import vocabulary as v; p=v.plan(); print(p['operators']['affects'], p['sorts']); print(v.profile().operator(p['operators']['affects'])); print(v.pins())"`
Expected: `mm30-reproduction/affects {...'concept': 'mm30-reproduction/concept'...}`, a `CompiledOperator`, a `CorpusPins`. If `pins()` is refused later by `adopt_manifest`'s identity check, read `world/registry._identity` for the expected shape and adjust the two f-strings; that is a driver correction (record §8), not a finding.

- [ ] **Step 4: Commit**

```bash
git add python/tools/reproduction/vocabulary.py python/tools/reproduction/mm30-reproduction.yaml
git commit -m "feat(reproduction): the domain contract, compiled profile and namespaced plan"
```

---

### Task 4: World, corpus, store (path step 1)

**Files:**
- Create: `python/tools/reproduction/world.py`

**Interfaces:**
- Consumes: `vocabulary.pins()`, `authority.AUTHORITY`.
- Produces: `state.world_id, corpus_id, store_id`; `world.open_writer() -> CorpusWriter`; `world.open_world() -> World`.

- [ ] **Step 1: Write `world.py`**

```python
# python/tools/reproduction/world.py
"""Step 1: register a world root and adopt one fresh corpus on the certified volume."""
from __future__ import annotations
import secrets
import sys

from beliefs.corpus import CorpusWriter
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus
from beliefs.root import open_world as _open_world
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
    state.save(world_id=secrets.token_hex(16))
    init_world_root(config(), authority=AUTHORITY)
    init_corpus_root(paths.CORPUS_ROOT, authority=AUTHORITY)
    store_id = init_store_root(paths.STORE_ROOT, authority=AUTHORITY)
    manifest = open_writer().adopt_manifest(profile=pins())
    open_world().admit(paths.CORPUS_ROOT, provenance=Fresh())
    state.save(corpus_id=manifest.corpus_id, store_id=store_id)
    print(f"corpus {manifest.corpus_id} status {open_world().status(manifest.corpus_id)}; store {store_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.world` → one line; record §3 row 1.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/world.py
git commit -m "feat(reproduction): register the world, corpus and store roots"
```

---

### Task 5: Type and mint the proposition (path step 2)

**Files:**
- Create: `python/tools/reproduction/type_target.py`

**Interfaces:**
- Consumes: `target.yaml`; `vocabulary.profile(), plan()`; `world.open_writer()`.
- Produces: `state.proposition_ref, claim_identity, typing_seconds`.

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
    kind, colon, tail = term.partition(":")
    if not colon or not kind or not tail:
        raise ClaimError(f"term {term!r} carries no `<kind>:` prefix")
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
    minted = world.open_writer().add(stored.proposition_node(
        slug, title=target["proposition_id"], claim=project_claim(claim),
        display_statement=f"{target['subject']} {target['predicate']} {target['object']}"))
    state.save(proposition_ref=minted.id, claim_identity=claim_identity(claim), typing_seconds=round(time.monotonic() - started, 1))
    print(f"minted {minted.id}; claim identity {claim_identity(claim)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it; record the authoring cost**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.type_target`. Record §3 row 2 and §7 (wall time from opening the predecessor record through Task 3's edits to the mint). A `build_claim` refusal on sort is the typing exercise's known class; take the next alternative only then, and say so in §2.

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
- Consumes: `target.yaml` (`dataset_path`, `held_file`); `state.store_id`; `world.open_writer()`.
- Produces: `state.dataset_ref` (**equal to** `dataset_address`), `dataset_address, held_file, held_digest, store_relative_path, holdings_observation_ref`.

**The dataset record's id is its content address.** The run publication names observed inputs by the spec's `dataset:sha256:<hex>` address (`publication_plan`), and `eligibility_refusal` resolves that string against the corpus before an assessment may be added. So the dataset record's slug is `dataset_address(...).removeprefix("dataset:")`, exactly as `test_audit.py:93` and the cut-15 lineage acceptance mint them. The bridge is crossed here, once, and checked by a unit test before the run.

- [ ] **Step 1: Write the failing test for the id bridge**

```python
def test_dataset_record_id_equals_its_content_address():
    from reproduction.hold import dataset_record
    node, address = dataset_record(name="expr.tsv", digest="sha256:" + "c" * 64, title="t", facet={"boundary": "acquisition"})
    assert node.id == address == "dataset:sha256:" + __import__("hashlib").sha256(("sha256:" + "c" * 64 + "\n").encode()).hexdigest()
```

- [ ] **Step 2: Write `hold.py`**

```python
# python/tools/reproduction/hold.py
"""Step 3: hold the dataset's bytes in the store; mint the dataset record under its content address."""
from __future__ import annotations
import sys
from hashlib import sha256
from pathlib import Path

import yaml
from nodes.core.node import Node

from beliefs import stored
from beliefs.dataset import ByteObservation, DatasetDeclaration, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/hold.v1"


def dataset_record(*, name: str, digest: str, title: str, facet: dict) -> tuple[Node, str]:
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=name, digest=digest),)))
    assert address is not None
    node = stored.dataset_node(address.removeprefix("dataset:"), title=title,
                               resources=[{"name": name, "digest": digest}], empirical_observation=facet)
    return node, address


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    held = Path(target["dataset_path"]) / target["held_file"] if Path(target["dataset_path"]).is_dir() else Path(target["dataset_path"])
    if not held.is_file():
        print(f"REFUSED: held_file {held} is not a regular file; fix target.yaml (driver correction, record §8)")
        return 2
    content = held.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    st = state.load()
    relative = f"{target['dataset_id'].split(':', 1)[1]}/{held.name}"
    ctx = ActContext(paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam())
    published = write(ctx, StoreLocator(st["store_id"], relative), content, expected=digest)
    # P2: the facet payload is authored, not checked. Say what we claim and file the gap.
    node, address = dataset_record(name=held.name, digest=digest, title=target["dataset_id"],
                                   facet={"boundary": "acquisition", "source": target["dataset_id"], "asserted_by": AUTHORITY.actor})
    minted = world.open_writer().add(node)
    verdict = admission_state(stored.dataset_declaration(minted),
                              (ByteObservation(digest=digest, location=published.record.location.canonical()),))
    if not isinstance(verdict, Held):
        findings.record(3, "defect", f"held bytes with a matching digest did not read as Held: {verdict!r}")
        return 2
    findings.record(3, "design-gap",
                    "empirical-observation facet is presence-only: is_empirical_observation read our authored payload unchecked",
                    filed="domain lane (facet payload contract, kernel §11)")
    state.save(dataset_ref=minted.id, dataset_address=address, held_file=str(held), held_digest=digest,
               store_relative_path=relative, holdings_observation_ref=f"holdings-observation:{published.record.identity()}")
    print(f"held {held.name} ({len(content)} bytes) as {digest}; dataset {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the test, then the step**

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k content_address` → PASS.
Run: `PYTHONPATH=tools uv run python -m reproduction.hold`. Record §3 row 3, P2 and P3. Confirm `holdings_observation_ref` resolves: `view.holds(ref)` in a one-liner; if the stored id is spelled otherwise, read `stored.holdings_observation_node` and correct the ref (driver correction).

- [ ] **Step 4: Commit**

```bash
git add python/tools/reproduction/hold.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): hold the dataset and mint its record under the content address"
```

---

### Task 7: The analysis, the rendered workflow, the frozen spec, the spec record (path step 4)

**Files:**
- Create: `python/tools/reproduction/analysis/workflow/Snakefile.template`, `python/tools/reproduction/analysis/assoc.py`, `python/tools/reproduction/spec.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `target.yaml` (`held_file, value_column, group_column, positive_level`); `state.proposition_ref, dataset_address, held_file`.
- Produces: `spec.CODE_ROOT: Path` (the `analysis/` directory; bundle paths are `analysis/...` because `capture_bundle` keeps the root's name); `spec.ENTRYPOINT = "analysis/workflow/Snakefile"`; `spec.TARGETS`; `spec.OUTCOME_DIGESTS`; `spec.interpretation(), equivalence(), held_rules(), definition(), frozen()`; `spec.spec_record(frozen) -> Node` (semantically stamped); `state.spec_identity, spec_ref, held_name`.

Three facts fix this task's shape:

1. **The interpretation rule reads a result manifest, not bytes.** `build_assessment` calls `implementation.evaluate(run.result)` with `ResultManifest(outputs=((name, digest), ...))`. The verdict is routed through a canonical outcome file whose digest the rule maps. Filed as a design-gap finding (unpredicted by spec §5; recorded as such).
2. **The staged input keeps the held file's basename.** `boundary._stage_inputs` copies each held input to `inputs/<source.name>`, so the Snakefile's `input:` is `inputs/<held basename>`. The Snakefile is rendered from a template with that name, and the rendered bytes are what the definition snapshot digests.
3. **The bundle keeps the code root's directory name.** `capture_bundle` writes `(Path(root.name) / relative)`, so with root `analysis/` the entrypoint is `analysis/workflow/Snakefile` and the script is `analysis/assoc.py`.

- [ ] **Step 1: Write the failing tests for the outcome digests and the analysis's refusals**

```python
def test_outcome_digests_cover_exactly_the_three_outcomes():
    from hashlib import sha256
    from reproduction.spec import OUTCOME_DIGESTS
    assert set(OUTCOME_DIGESTS.values()) == {"supported", "refuted", "inconclusive"}
    assert OUTCOME_DIGESTS["sha256:" + sha256(b"supported\n").hexdigest()] == "supported"


def _assoc():
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "tools" / "reproduction" / "analysis" / "assoc.py"
    spec = importlib.util.spec_from_file_location("assoc", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tsv(tmp_path, header, rows):
    p = tmp_path / "data.tsv"
    p.write_text("\t".join(header) + "\n" + "".join("\t".join(r) + "\n" for r in rows))
    return p


def test_assoc_refuses_missing_columns(tmp_path):
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="column"):
        assoc.load(_tsv(tmp_path, ["a", "b"], [["1", "x"]]), value_column="expr", group_column="grp")


def test_assoc_refuses_non_finite_values(tmp_path):
    assoc = _assoc()
    with pytest.raises(assoc.MalformedInput, match="finite"):
        assoc.load(_tsv(tmp_path, ["expr", "grp"], [["nan", "a"], ["2", "b"], ["3", "a"], ["4", "b"], ["5", "a"], ["6", "b"]]),
                   value_column="expr", group_column="grp")


def test_assoc_refuses_a_group_below_the_floor(tmp_path):
    assoc = _assoc()
    rows = [["1", "a"], ["2", "a"], ["3", "a"], ["4", "b"]]
    with pytest.raises(assoc.MalformedInput, match="at least"):
        assoc.decide(assoc.load(_tsv(tmp_path, ["expr", "grp"], rows), value_column="expr", group_column="grp"), positive_level="a")


def test_assoc_refuses_a_positive_level_that_is_absent(tmp_path):
    assoc = _assoc()
    rows = [[str(i), "a" if i % 2 else "b"] for i in range(1, 11)]
    with pytest.raises(assoc.MalformedInput, match="positive level"):
        assoc.decide(assoc.load(_tsv(tmp_path, ["expr", "grp"], rows), value_column="expr", group_column="grp"), positive_level="zzz")


def test_spec_record_carries_a_fresh_semantic_stamp():
    from decimal import Decimal
    from beliefs import stored
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
    from reproduction import spec as spec_module
    draft = SpecDraft(target="proposition:p", estimand="e", method="m", assumptions="a", falsification="f",
                      input_roles=(SpecInput(role="observes", dataset="dataset:sha256:" + "a" * 64),), applicability="x",
                      interpretation_rule=spec_module.INTERPRETATION_RULE, equivalence_rule=spec_module.EQUIVALENCE_RULE,
                      parameters={"alpha": Decimal("0.05")}, nondeterminism=Deterministic())
    node = spec_module.spec_record(freeze(draft, held_rules=spec_module.held_rules()))
    assert node.kind == "analysis-spec"
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)


def test_assoc_supported_when_positive_level_is_higher(tmp_path):
    assoc = _assoc()
    rows = [[str(10 + i), "hi"] for i in range(8)] + [[str(i), "lo"] for i in range(8)]
    outcome, z, p, n = assoc.decide(assoc.load(_tsv(tmp_path, ["expr", "grp"], rows), value_column="expr", group_column="grp"), positive_level="hi")
    assert outcome == "supported" and z > 0 and p < 0.05 and n == 16
```

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k "outcome_digests or assoc or semantic_stamp"` → FAIL.

- [ ] **Step 2: Write the analysis**

```python
# python/tools/reproduction/analysis/assoc.py
"""One within-dataset association, standard library only, refusing malformed input.

Reads a tab-separated file with a header row, compares `value_column` between
the two levels of `group_column`, and writes stats.tsv and outcome.txt — the
latter exactly one of supported/refuted/inconclusive. Any malformation exits
non-zero, so the boundary reports execution-failed and no outcome exists.
"""
from __future__ import annotations
import csv
import math
import pathlib
import sys

ALPHA = 0.05
MIN_PER_GROUP = 3


class MalformedInput(Exception):
    pass


def load(path, *, value_column: str, group_column: str) -> dict[str, list[float]]:
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = reader.fieldnames or []
        for column in (value_column, group_column):
            if column not in header:
                raise MalformedInput(f"column {column!r} is absent from the header {header}")
        groups: dict[str, list[float]] = {}
        for number, row in enumerate(reader, start=2):
            raw = row.get(value_column)
            group = row.get(group_column)
            if raw is None or group is None or group == "":
                raise MalformedInput(f"line {number}: empty value or group")
            try:
                value = float(raw)
            except ValueError as error:
                raise MalformedInput(f"line {number}: {raw!r} is not a number") from error
            if not math.isfinite(value):
                raise MalformedInput(f"line {number}: {raw!r} is not finite")
            groups.setdefault(group, []).append(value)
    if not groups:
        raise MalformedInput("no data rows")
    return groups


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float]:
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b], key=lambda t: t[0])
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
    if sigma == 0:
        raise MalformedInput("degenerate groups: zero variance in the rank statistic")
    z = (u_a - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p


def decide(groups: dict[str, list[float]], *, positive_level: str) -> tuple[str, float, float, int]:
    levels = sorted(groups)
    if len(levels) != 2:
        raise MalformedInput(f"expected exactly two levels, found {levels}")
    if positive_level not in groups:
        raise MalformedInput(f"positive level {positive_level!r} is not among {levels}")
    for level, values in groups.items():
        if len(values) < MIN_PER_GROUP:
            raise MalformedInput(f"group {level!r} has {len(values)} values; at least {MIN_PER_GROUP} are required")
    other = next(l for l in levels if l != positive_level)
    z, p = mann_whitney(groups[positive_level], groups[other])
    outcome = "inconclusive" if p >= ALPHA else ("supported" if z > 0 else "refuted")
    return outcome, z, p, sum(len(v) for v in groups.values())


def main(inp: str, stats_out: str, outcome_out: str, value_column: str, group_column: str, positive_level: str) -> int:
    try:
        outcome, z, p, n = decide(load(inp, value_column=value_column, group_column=group_column), positive_level=positive_level)
    except MalformedInput as error:
        print(f"malformed input: {error}", file=sys.stderr)
        return 3
    pathlib.Path(stats_out).write_text(f"z\tp\tn\n{z}\t{p}\t{n}\n")
    pathlib.Path(outcome_out).write_text(outcome + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:7]))
```

```
# python/tools/reproduction/analysis/workflow/Snakefile.template
import subprocess, sys

rule assoc:
    input: "inputs/{HELD_NAME}"
    output: "outputs/stats.tsv", "outputs/outcome.txt"
    run:
        subprocess.run([sys.executable, "analysis/assoc.py", input[0], output[0], output[1],
                        "{VALUE_COLUMN}", "{GROUP_COLUMN}", "{POSITIVE_LEVEL}"], check=True)
```

If the held file is gzipped, add a first rule that decompresses with `gzip` from the standard library into a scratch-relative intermediate and point `assoc` at it; keep the input name rule.

- [ ] **Step 3: Write `spec.py`**

```python
# python/tools/reproduction/spec.py
"""Step 4: render the workflow, freeze the analysis spec, and mint its record."""
from __future__ import annotations
import sys
from decimal import Decimal
from functools import cache
from hashlib import sha256
from pathlib import Path

import yaml
from nodes.core.node import Node

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.recipe import ResultManifest
from beliefs.replay import EquivalenceImplementation
from beliefs.spec import Deterministic, FrozenSpec, RuleFixture, RuleImplementation, SpecDraft, SpecInput, freeze
from reproduction import findings, paths, state, world

CODE_ROOT = Path(__file__).with_name("analysis")          # bundle name: analysis/
TEMPLATE = CODE_ROOT / "workflow" / "Snakefile.template"
SNAKEFILE = CODE_ROOT / "workflow" / "Snakefile"
ENTRYPOINT = "analysis/workflow/Snakefile"
TARGETS = ("outputs/stats.tsv", "outputs/outcome.txt")
OUTCOME_FILE = "outputs/outcome.txt"
INTERPRETATION_RULE = "mm30-reproduction/outcome-file/v1"
EQUIVALENCE_RULE = "content-identity-equality/v1"
OUTCOME_DIGESTS = {"sha256:" + sha256((o + "\n").encode()).hexdigest(): o for o in ("supported", "refuted", "inconclusive")}


def render_snakefile() -> bytes:
    target = yaml.safe_load(paths.TARGET.read_text())
    text = TEMPLATE.read_text()
    for key in ("HELD_NAME", "VALUE_COLUMN", "GROUP_COLUMN", "POSITIVE_LEVEL"):
        value = Path(state.load()["held_file"]).name if key == "HELD_NAME" else target[key.lower()]
        text = text.replace("{" + key + "}", str(value))
    SNAKEFILE.write_bytes(text.encode())
    return SNAKEFILE.read_bytes()


def _interpret(manifest: ResultManifest) -> dict:
    return {"outcome": OUTCOME_DIGESTS[dict(manifest.outputs)[OUTCOME_FILE]]}


@cache
def interpretation() -> RuleImplementation:
    supported = next(d for d, o in OUTCOME_DIGESTS.items() if o == "supported")
    return RuleImplementation(identity="impl-outcome-file-1", evaluate=_interpret,
                              fixtures=(RuleFixture(arguments=(ResultManifest(outputs=((OUTCOME_FILE, supported),)),), expected={"outcome": "supported"}),))


@cache
def equivalence() -> EquivalenceImplementation:
    return EquivalenceImplementation(identity="impl-eq-1", evaluate=lambda a, b: "passed" if a == b else "failed",
                                     fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),))


def held_rules() -> dict:
    return {INTERPRETATION_RULE: interpretation(), EQUIVALENCE_RULE: equivalence()}


def definition() -> WorkflowDefinition:
    return WorkflowDefinition(snakefile=SNAKEFILE.read_bytes(), family_streams={})


def draft() -> SpecDraft:
    st = state.load()
    target = yaml.safe_load(paths.TARGET.read_text())
    return SpecDraft(
        target=st["proposition_ref"],
        estimand=f"difference in {target['value_column']} between levels of {target['group_column']} in {target['dataset_id']}",
        method="two-group rank comparison (Mann-Whitney U, normal approximation), standard library",
        assumptions="independent samples; the covariate is a two-level factor recorded per sample",
        falsification="no difference at alpha 0.05, or a difference opposite the proposition's polarity",
        input_roles=(SpecInput(role="observes", dataset=st["dataset_address"]),),
        applicability=f"samples of {target['dataset_id']} with both columns present and finite",
        interpretation_rule=INTERPRETATION_RULE, equivalence_rule=EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")}, nondeterminism=Deterministic(),
    )


@cache
def frozen() -> FrozenSpec:
    return freeze(draft(), held_rules=held_rules())


def spec_record(spec: FrozenSpec) -> Node:
    """`analysis-spec` is a stored kind (stored.py's kinds table; the import
    path validates its facet) but the kernel exports no builder or reader for
    it. This node carries the frozen members and the identity so the record
    is on disk; that no kernel function restores a FrozenSpec from it is a
    finding (Task 11)."""
    facet = {
        "identity": spec.identity, "target": spec.target, "estimand": spec.estimand, "method": spec.method,
        "assumptions": spec.assumptions, "falsification": spec.falsification,
        "input_roles": [{"role": e.role, "dataset": e.dataset} for e in spec.input_roles],
        "applicability": spec.applicability, "interpretation_rule": spec.interpretation_rule,
        "equivalence_rule": spec.equivalence_rule, "parameters": {k: str(v) for k, v in spec.parameters.items()},
        "nondeterminism": spec.nondeterminism.projection(), "rule_bindings": [list(p) for p in spec.rule_bindings],
    }
    # A governed kind: the writer refuses an unstamped record
    # (`ValidationRefused: ... semantic-identity stamp is missing or stale`).
    # `stamp_semantic_identity` is the one construction authority for the stamp.
    return stored.stamp_semantic_identity(Node(id=f"analysis-spec:{spec.identity}", kind="analysis-spec",
                                               title=f"spec {spec.identity[:12]}", facets={"analysis-spec": facet}, relations=[]))


def main() -> int:
    render_snakefile()
    spec = frozen()
    minted = world.open_writer().add(spec_record(spec))
    state.save(spec_identity=spec.identity, spec_ref=minted.id, held_name=Path(state.load()["held_file"]).name)
    findings.record(4, "design-gap",
                    "build_assessment hands the interpretation rule a ResultManifest of digests, not output bytes; "
                    "the verdict is routed through a canonical outcome file whose digest the rule maps",
                    filed="computation design (where an interpretation rule reads content)")
    findings.record(4, "design-gap",
                    "analysis-spec is a stored kind with no kernel builder or reader; the spec record was hand-built",
                    filed="computation design / stored.py (spec record builder and restore)")
    print(f"frozen spec {spec.identity} targeting {spec.target}; record {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`spec.target` is the proposition's **corpus ref**: `evaluation.gather` matches stored assessments on `value.proposition == proposition`, and the stored facet's `proposition` is the ref. `audit.py` remarks that the derived value's `proposition` is "the spec's claim target" in another namespace; whether those two are meant to coincide is answered at step 10a and filed if they diverge.

- [ ] **Step 4: Run the tests and freeze**

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k "outcome_digests or assoc or semantic_stamp"` → PASS.
Run: `PYTHONPATH=tools uv run python -m reproduction.spec` → `frozen spec ... record analysis-spec:...`. If `CorpusWriter.add` refuses the hand-built node (`ValidationRefused: malformed analysis-spec contract fields`), read `corpus._refuse_r20_contradiction` and correct the facet (driver correction). Record §3 row 4. **From here the target, spec and rule are fixed.**

- [ ] **Step 5: Commit**

```bash
git add python/tools/reproduction/analysis python/tools/reproduction/spec.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): the validating stdlib analysis, the rendered workflow and the frozen spec"
```

---

### Task 8: Run, assess, replay, verify (path steps 5–7)

**Files:**
- Create: `python/tools/reproduction/run.py`
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `spec.*`; `state.held_file, dataset_address, proposition_ref`.
- Produces: `state.original_run_ref, replayed_run_ref` (typed), `assessment_ref, assessment_identity_stored, assessment_identity_derived, assessment_outcome, verification_scope, verification_verdict, scope_class`; `run.port()`; `run.classify_scope(scope, original, replayed) -> str` (pure given closures).

**Two identities for one assessment, and neither can be substituted for the other.** `build_assessment` returns a value whose `run` is the **bare** closure address; the stored record's facet spells it as the **typed** `run:<address>` (`stored.assessment_node(run=run_ref(...))`, which `eligibility_refusal` requires so the run resolves), so `stored.assessment_value(node).identity()` differs from `assessment.identity()`. Admission over the corpus (`gather` → `admit`) matches verifications against the **stored** identity; the audit (`check_verification`) recomputes the identity from the spec identity, the original run's **bare** address and the spec target, and reports `verification-derivation-contradicted` against anything else. The verification therefore keeps the **derived** identity `admission_record` gives it (Task 9), the admission refusal that follows is recorded as the finding, and both identities are written to `state.json`. This is a kernel gap for the assessment/run-record owner, not a bridge the driver crosses.

- [ ] **Step 1: Write the failing test for `classify_scope`**

```python
def test_classify_scope_attributes_only_same_environment_to_the_host():
    from reproduction.run import classify_scope
    assert classify_scope("clean-environment", conforming=(True, True), recipes_agree=True) == "none"
    assert classify_scope("same-environment", conforming=(True, True), recipes_agree=True) == "host"
    assert classify_scope("not-certified", conforming=(True, False), recipes_agree=True) == "defect"
    assert classify_scope("not-certified", conforming=(True, True), recipes_agree=False) == "corpus-work"
```

- [ ] **Step 2: Write `run.py`**

```python
# python/tools/reproduction/run.py
"""Steps 5-7: confined run, assessment, replay, verification."""
from __future__ import annotations
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path

from atoms.fs.platform import select_backend

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.boundary import RunRefused, execute_assessment_run
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


def classify_scope(scope: str, *, conforming: tuple[bool, bool], recipes_agree: bool) -> str:
    """Spec §2 rule 4. `same-environment` with agreeing recipes is the host's;
    `not-certified` is a non-conforming closure (defect) or disagreeing
    recipes (authoring, i.e. corpus work). Never the host by default."""
    if scope == "clean-environment":
        return "none"
    if scope == "same-environment" and recipes_agree:
        return "host"
    if not all(conforming):
        return "defect"
    if not recipes_agree:
        return "corpus-work"
    return "defect"


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
        cls = "corpus-work" if original.reason == "execution-failed" and "malformed input" in (original.detail or "") else "design-gap"
        findings.record(5, cls, f"run refused: {original.reason}: {original.detail}")
        print(f"REFUSED at run: {original.reason}: {original.detail}")
        return 2
    original_ref = run_ref(original.run.address())
    # Step 6
    derived = build_assessment(original.run, specs={frozen.identity: frozen}, implementations={spec.interpretation().identity: spec.interpretation()})
    if isinstance(derived, AssessmentFinding):
        findings.record(6, "defect", f"AssessmentFinding: {derived.reason}")
        print(f"ASSESSMENT FINDING: {derived.reason}")
        return 2
    optional = {k: v for k, v in (("estimate", derived.estimate), ("uncertainty", derived.uncertainty),
                                  ("estimand", derived.estimand), ("applicability", derived.applicability)) if v is not None}
    writer = world.open_writer()
    minted = writer.add(stored.assessment_node(
        derived.identity()[:16], title=f"assessment of {st['proposition_ref']}", spec=frozen.identity, run=original_ref,
        proposition=st["proposition_ref"], outcome=derived.outcome, interpretation_rule=derived.interpretation_rule, **optional))
    stored_identity = stored.assessment_value(writer.read_view.get(minted.id)).identity()
    if stored_identity != derived.identity():
        findings.record(6, "design-gap",
                        "the derived AssessmentValue spells `run` as a bare address and the stored record as run:<address>; "
                        "the two identities differ, and no single one satisfies both admission over the corpus and the "
                        "audit's recomputation (which digests the bare address)",
                        filed="assessment/run-record design (one spelling for the run member)")
    # Step 7
    replayed = replay(original, spec=frozen, started_at=now(), scratch_base=paths.SCRATCH / "replayed", **common)
    if isinstance(replayed, RunRefused):
        findings.record(7, "design-gap", f"replay refused: {replayed.reason}: {replayed.detail}")
        print(f"REFUSED at replay: {replayed.reason}")
        return 2
    scope = derive_scope(original.run, replayed.run, certification=None)
    cls = classify_scope(scope, conforming=(conformance(original.run) == CONFORMING, conformance(replayed.run) == CONFORMING),
                         recipes_agree=original.run.recipe.identity() == replayed.run.recipe.identity())
    if cls != "none":
        receipt = replayed.run.occurrence.receipt.execution
        findings.record(7, cls, f"scope {scope}: replay capabilities={receipt.capabilities} instance={'present' if receipt.instance else 'absent'}")
    verification = build_verification(original.run, replayed.run, specs={frozen.identity: frozen},
                                      held_rules={spec.equivalence().identity: spec.equivalence()},
                                      contract_identity=writer.manifest_pins().science_contract, epoch="none-published")
    assert isinstance(verification, AssessmentVerification), verification
    state.save(original_run_ref=original_ref, replayed_run_ref=run_ref(replayed.run.address()), assessment_ref=minted.id,
               assessment_identity_stored=stored_identity, assessment_identity_derived=derived.identity(),
               assessment_outcome=derived.outcome, verification_scope=verification.scope,
               verification_verdict=verification.verdict, scope_class=cls)
    print(f"run {original_ref}; assessment {derived.outcome}; scope {verification.scope} ({cls}); verdict {verification.verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the test, then the step**

Run: `cd python && uv run pytest tests/test_reproduction_driver.py -q -k classify_scope` → PASS.
Run: `PYTHONPATH=tools uv run python -m reproduction.run`. Record §3 rows 5–7, P4 and P7. An `execution-failed` whose detail carries `malformed input` is the analysis refusing the data: fix `target.yaml`'s columns (record §8), re-render, and note that the definition snapshot and therefore the recipe changed **before** any run was minted; if a run was already minted, the exercise stops and records it, since the spec is fixed.

- [ ] **Step 4: Commit**

```bash
git add python/tools/reproduction/run.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): confined run, assessment, replay and verification"
```

---

### Task 9: Store the verification, admit, evaluate over the corpus (path step 8)

**Files:**
- Create: `python/tools/reproduction/belief.py`

**Interfaces:**
- Consumes: `state.*` refs; `spec.frozen()`; `vocabulary.profile(), snapshot()`.
- Produces: `state.verification_ref, admission, belief_answer` (`answers.payload`); `belief.context() -> SuppliedContext`, `belief.availability(view) -> Availability`, `belief.evaluate_here(view) -> Belief|NoBelief|Refused` — the **same** corpus-backed call step 10a repeats.

**Same path, both times.** Step 8 evaluates through `evaluation.evaluate_over(view, proposition, ...)`, which gathers the stored assessment, run, dataset, verification and claim through the instrumented resolver; step 10a calls the same function in a fresh process. A value-level `evaluate` with `claims={}` would consult a different contract set than the corpus-backed path and make 10a incomparable. Holdings evidence comes from the stored `holdings-observation` record, not from `state.json`.

**The verification names the derived assessment identity, unaltered.** `admission_record(verification).assessment` is what `build_verification` derived from the original run, and it is what the audit will recompute. Substituting the stored identity would satisfy admission and contradict the audit; keeping the derived one satisfies the audit and is refused by admission (`not-admitted-verification-state`, because the gathered assessment carries the typed-run identity). The exercise keeps the evidence honest and records the refusal: under spec §2 rule 4 the expected answer is then `NoBelief("no-eligible-assessment")` with class **design-gap**, and that answer is a complete run of the path. If admission instead reports `Admitted`, the two identities agreed on this kernel and Task 8's finding is withdrawn in the record.

- [ ] **Step 1: Write `belief.py`**

```python
# python/tools/reproduction/belief.py
"""Step 8: store the verification, admit, and evaluate over the corpus."""
from __future__ import annotations
import sys

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.dataset import ByteObservation
from beliefs.evaluation import evaluate_over, gather
from beliefs.holdings.records import Found
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, admission_record, build_verification
from reproduction import answers, findings, spec, state, vocabulary, world

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


def observations_from_corpus(view: ReadView) -> dict[str, tuple[ByteObservation, ...]]:
    """Every stored holdings observation with a Found outcome, keyed by the
    dataset address it satisfies. Corpus evidence, not a sidecar. The holdings
    reduction rule (supersession, coverage) is not applied: one observation,
    no history — stated in the record."""
    st = state.load()
    found = []
    for node in view.iter_stored():
        if node.kind == "holdings-observation":
            value = stored.holdings_observation_value(node)
            if isinstance(value.outcome, Found):
                found.append(ByteObservation(digest=value.outcome.digest, location=value.location.canonical()))
    return {st["dataset_address"]: tuple(found)}


def context(view: ReadView) -> SuppliedContext:
    st = state.load()
    return SuppliedContext(
        snapshot=lineage_snapshot(view, [st["dataset_address"]]),
        producer_snapshot_identity="no-epoch-published",          # supplied: this exercise builds no epoch (record §3)
        retractions=RetractionEnumeration(found=(), coverage=(st["corpus_id"],)),
        node_corpus={st["assessment_identity_stored"]: st["corpus_id"]},
        pins={st["corpus_id"]: world.open_writer().manifest_pins()},
    )


def availability(view: ReadView) -> Availability:
    return Availability(observations=observations_from_corpus(view),
                        implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES})


def evaluate_here(view: ReadView):
    return evaluate_over(view, state.load()["proposition_ref"], availability=availability(view), context=context(view),
                         profile=vocabulary.profile(), resolution=vocabulary.snapshot(), binding=BINDING)


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    original = decode_run_closure(view.get(st["original_run_ref"]))
    replayed = decode_run_closure(view.get(st["replayed_run_ref"]))
    frozen = spec.frozen()
    verification = build_verification(original, replayed, specs={frozen.identity: frozen},
                                      held_rules={spec.equivalence().identity: spec.equivalence()},
                                      contract_identity=writer.manifest_pins().science_contract, epoch="none-published")
    assert isinstance(verification, AssessmentVerification)
    record = admission_record(verification)
    if record.assessment != st["assessment_identity_derived"]:
        findings.record(8, "defect", f"admission_record names {record.assessment}, not the derived identity {st['assessment_identity_derived']}")
    minted = writer.add(stored.verification_node(
        record.ref[:16], title=f"verification of {st['assessment_ref']}", assessment=record.assessment,  # derived, unaltered
        assessment_ref=st["assessment_ref"], scope=record.scope, verdict=record.verdict,
        derivation=(st["original_run_ref"], st["replayed_run_ref"])))
    view = world.open_writer().read_view
    inputs = gather(view, st["proposition_ref"], context=context(view), profile=vocabulary.profile(),
                    resolution=vocabulary.snapshot(), binding=BINDING)
    if len(inputs.assessments) != 1 or inputs.assessments[0].run not in inputs.runs:
        findings.record(8, "design-gap", f"gather matched {len(inputs.assessments)} assessments for {st['proposition_ref']} "
                        f"with runs {sorted(inputs.runs)}; the spec target / stored proposition ref do not meet")
        state.save(verification_ref=minted.id, admission="not-evaluated: gather mismatch", belief_answer={"kind": "not-evaluated"})
        return 2
    a = inputs.assessments[0]
    verdict = admit(a, inputs.runs[a.run], observations_from_corpus(view), inputs.verifications)
    admission = "Admitted" if isinstance(verdict, Admitted) else f"AdmissionRefused: {verdict.reason}"
    if (not isinstance(verdict, Admitted) and verdict.reason.startswith("not-admitted-verification-state")
            and record.assessment != a.identity() and record.scope == "clean-environment" and record.verdict == "passed"):
        findings.record(8, "design-gap",
                        f"a clean-environment pass was refused at admission: the verification names the derived identity "
                        f"{record.assessment} and the gathered assessment carries {a.identity()}; the audit accepts only the former",
                        filed="assessment/run-record design (one spelling for the run member)")
    answer = answers.payload(evaluate_here(view))
    if answer["kind"] == "Refused":
        findings.record(8, "design-gap", f"evaluate refused: {answer['reason']}")
    state.save(verification_ref=minted.id, admission=admission, belief_answer=answer)
    print(f"admission {admission}; answer {answer}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it and apply spec §2 rule 4**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.belief`. Record §3 row 8 with the payload verbatim. Then:
- `Belief` → terminal.
- `NoBelief("no-directional-outcome")` → terminal; a scientific result.
- `NoBelief("no-eligible-assessment")` → terminal only with `state.admission` and `state.scope_class` quoted beside it. If `admission` is `not-admitted-verification-state` while the scope is `clean-environment` and the verdict `passed`, the class is **design-gap** (the identity bridge above), not host. Otherwise the class is `scope_class` (`host` / `defect` / `corpus-work`). The reason alone is never the classification.
- `Refused` or gather mismatch → filed; the path stops here and Tasks 10–12 run over what exists.

Record the two supplied members (`producer_snapshot_identity`, the retraction enumeration) and the bypassed holdings reduction as step 8's stated limitations.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/belief.py
git commit -m "feat(reproduction): store the verification, admit, and evaluate over the corpus"
```

---

### Task 10: Close the corpus (path step 9)

**Files:**
- Create: `python/tools/reproduction/close.py`

**Interfaces:**
- Produces: `state.corpus_check_findings, audit_findings, log_verdict`.

The contradiction codes are exactly `verification-derivation-contradicted`, `assessment-derivation-contradicted` and `lineage-basis-contradicted` (audit.py); those are defects. The malformedness codes (`semantic-hash-missing`, `semantic-hash-stale`, `coordination-facet-malformed`, `derivation-malformed`) are defects too. Anything else the audit emits is reported as design-gap with its code.

- [ ] **Step 1: Write `close.py`**

```python
# python/tools/reproduction/close.py
"""Step 9: corpus_check, the semantic audit, log verification. Writes nothing."""
from __future__ import annotations
import sys

from beliefs.audit import MALFORMEDNESS_CODES, DerivationEvidence, audit_corpus
from beliefs.corpus import corpus_check
from reproduction import findings, spec, state, world

CONTRADICTIONS = frozenset({"verification-derivation-contradicted", "assessment-derivation-contradicted", "lineage-basis-contradicted"})


def evidence() -> DerivationEvidence:
    return DerivationEvidence(specs={spec.frozen().identity: spec.frozen()},
                              held_rules={spec.equivalence().identity: spec.equivalence()},
                              implementations={spec.interpretation().identity: spec.interpretation()})


def main() -> int:
    view = world.open_writer().read_view
    checks = corpus_check(view)
    for f in checks:
        findings.record(9, "defect", f"corpus_check: {f.code}: {f.detail}")
    audits = audit_corpus(view, evidence=evidence())
    for f in audits:
        cls = "defect" if f.code in CONTRADICTIONS or f.code in MALFORMEDNESS_CODES else "design-gap"
        findings.record(9, cls, f"audit_corpus: {f.code}: {f.detail}")
    state.save(corpus_check_findings=len(checks), audit_findings=len(audits))
    print(f"corpus_check: {len(checks)}; audit_corpus: {len(audits)}")
    for f in (*checks, *audits):
        print(f"  {f.code}: {f.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Then add the log audit: `beliefs.root.audit_log(config, subject, target_root, observers, actor=)` with `CorpusSubject` from `beliefs.world.anchors`; read `beliefs.world.verify` for `ObserverSet`'s constructor and the one-observer case before writing the call, store the `LogReport`'s verdict as `log_verdict`, and record the observer shape used.

- [ ] **Step 2: Run it**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.close`. Record §3 row 9 with every code. Zero findings is the expected outcome and is stated as such.

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
- Consumes: the corpus on disk; `state.json` **refs only** (`proposition_ref, verification_ref, spec_ref, belief_answer` as the comparison target); in-process: `spec.frozen()`, `spec.held_rules()`, `vocabulary.profile()`.
- Produces: `state.rederived_belief, rederived_equal, evidence_reconstruction`.

**Labels are part of the result.** 10a's inputs are: the corpus (assessment, run, dataset, verification, claim, holdings observation), plus *supplied* context (producer snapshot identity, retraction enumeration), plus *in-process* profile and binding. 10b's are: the corpus (two run publications, the verification record, the spec record's identity), plus *in-process* spec and rule implementations, because no kernel reader restores a `FrozenSpec` or a rule from a record. Each field of the report names which. The stored spec's identity is compared to the in-process one so the sidecar is at least shown to agree with the record.

- [ ] **Step 1: Write `rederive.py`**

```python
# python/tools/reproduction/rederive.py
"""Steps 10a/10b, in a fresh process. Every input is labelled corpus / supplied / in-process."""
from __future__ import annotations
import json
import sys

from beliefs import stored
from beliefs.audit import check_verification
from beliefs.replay import derive_scope
from beliefs.runrecord import decode_run_closure
from beliefs.verify import AssessmentVerification, build_verification
from reproduction import answers, belief, close, findings, spec, state, world


def main() -> int:
    st = state.load()
    writer = world.open_writer()
    view = writer.read_view
    # 10a — the same call as step 8, in a new process.
    rederived = answers.payload(belief.evaluate_here(view))
    equal = rederived == st["belief_answer"]
    state.save(rederived_belief=rederived, rederived_equal=equal)
    # 10b — evidence reconstruction, field by field, each labelled.
    node = view.get(st["verification_ref"])
    stored_value = stored.verification_value(node)
    facet = node.facets.get(stored.VERIFICATION_FACET, {})
    spec_facet = view.get(st["spec_ref"]).facets.get("analysis-spec", {}) if view.holds(st["spec_ref"]) else {}
    report: dict = {
        "inputs": {"corpus": ["verification record", "two run publications", "analysis-spec record (identity only)"],
                   "in_process": ["FrozenSpec (no kernel reader for the record)", "interpretation and equivalence RuleImplementations"]},
        "comparison_report_stored": "comparison" in facet,
        "derivation_named": False, "closures_decoded": False,
        "scope_recomputed": None, "scope_equal": None, "verdict_recomputed": None, "verdict_equal": None,
        "spec_record_present": bool(spec_facet), "spec_identity_matches_in_process": spec_facet.get("identity") == spec.frozen().identity,
        "audit_check": None,
    }
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        scope = derive_scope(original, replayed, certification=None)
        report["scope_recomputed"], report["scope_equal"] = scope, scope == stored_value.scope
        rebuilt = build_verification(original, replayed, specs={spec.frozen().identity: spec.frozen()},
                                     held_rules={spec.equivalence().identity: spec.equivalence()},
                                     contract_identity=writer.manifest_pins().science_contract, epoch="none-published")
        if isinstance(rebuilt, AssessmentVerification):
            report["verdict_recomputed"], report["verdict_equal"] = rebuilt.verdict, rebuilt.verdict == stored_value.verdict
        else:
            report["verdict_recomputed"] = type(rebuilt).__name__
    outcome = check_verification(view, node, evidence=close.evidence())
    report["audit_check"] = {"checked": outcome.checked, "reason": outcome.reason,
                             "contradiction": None if outcome.contradiction is None else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail}}
    if outcome.contradiction is not None:
        findings.record(10, "defect", f"check_verification: {outcome.contradiction.code}: {outcome.contradiction.detail}")
    state.save(evidence_reconstruction=report)
    if not report["comparison_report_stored"]:
        findings.record(10, "design-gap",
                        "no stored record carries the comparison report; scope and verdict recover only by recomputation over both "
                        "stored closures with the in-process spec and rule implementations",
                        filed="verification-publication (write-path lane)")
    print(json.dumps({"10a": rederived, "equal": equal, "10b": report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Confirm `check_verification`'s keyword is `evidence=` (audit.py:113) and `Finding` exposes `.code` and `.detail` before running; correct the call, not the reading. With the verification naming the derived identity (Task 9), the expected `audit_check` is `checked: true` with no contradiction; a contradiction here is a defect.

- [ ] **Step 2: Run it in a fresh interpreter**

Run: `cd python && PYTHONPATH=tools uv run python -m reproduction.rederive`. Record §3 rows 10a and 10b separately, with the `inputs` labels copied into the record. Answer question 3 from 10b's `comparison_report_stored`, `scope_equal` and `verdict_equal` together, never from 10a. Answer question 2: no task called a resolver beyond the registry and the corpus, so the single-corpus first belief needed no world resolution; say whether `next` over one corpus would either. If 10a's gather matched nothing, that is the `target` namespace finding; file it and answer 10a as not re-derivable for that reason.

- [ ] **Step 3: Commit**

```bash
git add python/tools/reproduction/rederive.py
git commit -m "feat(reproduction): fresh-process re-derivation with labelled inputs"
```

---

### Task 12: The record, the findings, and the re-rank

**Files:**
- Modify: `docs/designs/2026-09-DD-mm30-reproduction.md` (rename to the completion date)
- Modify: `docs/plans/2026-08-29-implementation-roadmap.md` (re-rank under the method's second trigger)
- Modify: `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` (status line)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` only if a boundary changes tier; `docs/guide/open-questions.md` for any finding that is a question; `tasks/` for each finding's owning lane

- [ ] **Step 1: Complete the record.** §3 every row with outcome and what is on disk. §4 every prediction `confirmed`, `confirmed for another reason: …`, or `refuted`, citing `state.json` or `findings.jsonl`. §5 the three questions, question 1 `unmeasured`. §6 every finding line with where it was filed. §7 the authoring cost. §8 every driver correction made during the run, so a reader can tell instrument from kernel. Add `## 9. What this run does not claim`: no cut, no row, one proposition, one host, the supplied producer snapshot identity and retraction enumeration, the bypassed holdings reduction, in-process spec and rule implementations, and question 1 unmeasured.

- [ ] **Step 2: File each finding through its owning lane** as a task record under `tasks/` addressed to that lane (write-path, domain, computation/assessment owner); a question becomes an `open-questions.md` bullet in this commit; a defect becomes a task naming the failing test to write.

- [ ] **Step 3: Re-rank.** Rewrite the roadmap whole: `verification-publication` stays on the path unless 10b reports `comparison_report_stored` true **and** scope and verdict equal; `domain-boundary`'s placement carries question 1's answer; `world-resolution`'s carries question 2's. `Ranked at` stays at the newest results record; the `Method` line names this record.

- [ ] **Step 4: Gates**

```bash
cd python && uv run pytest tests/test_designs_corpus.py tests/test_check_guide.py tests/test_reproduction_driver.py -q
uv run python tools/check_guide.py
cd .. && git diff --check
```

- [ ] **Step 5: Commit and hand off**

```bash
git add docs python/tools/reproduction tasks
git commit -m "docs(reproduction): record the mm30 reproduction and re-rank the roadmap"
```

The `--no-ff` merge into `main` is the human partner's. The corpus under `.mm30-reproduction/` stays; it is the deliverable's second half.

---

## Self-review against the spec and the 2026-09-05 review

- **Identity bridges** (review 1, revised after the second review): the dataset record's id is its content address (Task 6, unit-tested); the verification keeps the **derived** assessment identity `admission_record` gives it, so the audit's recomputation agrees, and the admission refusal that follows is recorded as the design-gap finding rather than hidden by substitution (Tasks 8–9); admission uses the gathered run value, so both run refs are typed.
- **The spec record is stamped** (second review): `spec_record` returns `stored.stamp_semantic_identity(...)`, unit-tested with `semantic_hash_missing` and `semantic_hash_disagrees` both false.
- **Complete answer comparison, same path** (review 2): `answers.payload` serializes value, digest and binding (unit-tested); step 8 and step 10a both call `belief.evaluate_here`, i.e. `evaluate_over` on the corpus.
- **Contradictions preserved, equality explicit** (review 3): `scope_equal`, `verdict_equal`, `comparison_report_stored`, and the audit's `contradiction` are all reported; Task 10 classifies on the real codes.
- **Malformed input refused** (review 4): `assoc.py` raises `MalformedInput` on missing columns, non-finite values, wrong level count, absent positive level and a group below the floor, exits 3, and is unit-tested for each.
- **Namespaced plan** (review 5): `vocabulary.plan()` resolves through `contract().term`, checked at Task 3 step 3.
- **Invocation** (review 6): one convention, `PYTHONPATH=tools uv run python -m reproduction.<module>`, everywhere.
- **Bundle paths** (review 7): `analysis/workflow/Snakefile`, `analysis/assoc.py`, rendered `inputs/<held basename>`.
- **No manufactured membership** (review 8): `build_snapshot()` with nothing readable; question 1 unmeasured.
- **Measurement boundary** (review, last paragraph): holdings evidence from stored observations; the spec stored as a record and its identity compared; 10a/10b inputs labelled corpus / supplied / in-process in the report itself.
- **Spec coverage:** §2 rules 1–4; §3 criteria (Task 2); §4 rows 1–10b (Tasks 4, 3–5, 6, 7, 8, 9, 10, 11); §5 P1–P7 (Tasks 5, 6, 6, 8, 11, 12, 8) plus three unpredicted findings recorded as such (result-manifest interpretation, the spec record gap, the two assessment identities); §6 questions (Tasks 3, 11, 11); §7 classes; §8 deliverables; §10 lane discipline.
- **Type consistency:** `state.json` keys are declared once in the key table; `spec.frozen()`, `spec.held_rules()`, `spec.equivalence()`, `spec.interpretation()`, `belief.evaluate_here()`, `close.evidence()`, `answers.payload()` are defined before use and named identically throughout.
