# Verification Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `verification-publication` slice: one spelling for the assessment's run member, a stored verification carrying its whole basis with the comparison report embedded, publication as an ordinary `add`, forgery refused before the intent, scope recomputed by the audit and the import, and the stored `analysis-spec` builder and reader — discharging V1–V8 at conformance cut 21.

**Architecture:** `stored.typed_ref`/`local_id` become the one place a kind prefix is added or removed, and `AssessmentValue.run` is the bare run address on both the derived and the stored side. `verify.publication_node` projects a derived verification to a stamped node under `verification:<identity>` whose facet carries `rule`, `scope_rule`, `report` (the `ComparisonReport` projection) and the typed `derivation`/`supersedes`; `verify.decode_verification` restores a `StoredVerification` and refuses an id that does not recompute. `CorpusWriter._refuse` decodes every verification and restores every analysis-spec it prepares, then checks the `verifies` target's identity, before the intent. `audit.check_verification` recomputes through the constructor's own `_derive` helper and compares scope, rule, scope rule and report identity when a report is stored. `spec.restore` rebuilds a `FrozenSpec` from canonical projection text.

**Tech Stack:** Python 3.11+ (`uv run --frozen`), `pydantic` v2 `nodes` documents, `pytest`; the `atoms` certified engine for the durable suite; `science.identity.v1` canonical encoding.

**Spec:** `docs/designs/2026-09-06-verification-publication-design.md` (every task cites its sections) and the frozen cut `docs/designs/2026-09-06-conformance-cut-21.md` (frozen at `41c9920`, digest `eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5`). Read both before any task. The design's §2 decisions 1–18 are the rulings; §8's V rows are the acceptance criteria and their cells are quoted byte-exact in the cut's §3.

## Global Constraints

- From `python/`: `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen pyright` must pass at every commit. Run the Python suite with the project venv, never system python. `addopts` already sets `-q` and ignores `tests/acceptance`; run acceptance modules by path.
- The worktree is `.worktrees/verification-publication` on `feat/verification-publication`; run everything from it. `python/` is the working directory for every `uv run` below unless stated.
- Never edit `tasks/*.md` directly; use the `tasks` CLI. `tasks start <id>` before a task that carries an id, `tasks done <id> "<result>"` in the commit that lands it. Ids: `beliefs-ae9b18` (one spelling, Task 1), `beliefs-f860f1` (the stored report, Task 3), `beliefs-91aac6` (the analysis-spec builder and reader, Task 6), `beliefs-754995` (the boundary, Task 12).
- Conventional commits, no AI-attribution trailer or footer of any kind.
- Fail early, no silent fallbacks: every refusal is raised or reported, never skipped. A malformed member is refused, never repaired (M11).
- Every new check must be able to fail (N2): each test asserts a refusal or a finding a sabotage in Task 10 turns green.
- The constructor's argument list stays closed (R19): `build_verification` gains no parameter. `admission_record` is untouched. Reading never validates: `decode_verification` is self-consistency, and derivation validation happens at import and under audit only (design §5.3, §6).
- Sealed value types (`AssessmentVerification`, `DatasetProductionVerification`, `ComparisonReport`, `FrozenSpec`, `StoredVerification`) get no public constructor; restoration goes through the module's private mint.
- The `domain` lane's cut 20 is undischarged on its branch. `tools/cut21_acceptance.py` names `cut20_acceptance.py` as prefix and cannot run end to end until that lane merges (Task 12). Every portable test and the durable module run now.
- No `/home/keith` or `/mnt/ssd/Dropbox` paths in code or docs.
- Sections §2–§7 of the cut document are frozen; any deviation from them is dated in the results record (Task 12), never edited in.

---

## File structure

**Created**

| path | responsibility |
|---|---|
| `python/tests/test_verification_identity.py` | exists (fails at its first assertion on the freeze tree); Task 1 makes it pass, Task 7 widens it |
| `python/tests/acceptance/test_verification_acceptance.py` | V1, V2, V3, V5 through an attended session on the certified volume; the fresh-process arms |
| `python/tests/acceptance/n2_arms_cut21.py`, `python/tests/acceptance/test_n2_cut21.py`, `python/tools/cut21_acceptance.py` | the cut-21 discharge surface |
| `docs/plans/2026-09-06-conformance-cut-21-results.md` | the results record (Task 12, after cut 20 merges) |

**Modified**

| path | change |
|---|---|
| `python/src/beliefs/stored.py` | `typed_ref`, `local_id`, `governed_node`, `ANALYSIS_SPEC_FACET`, `analysis_spec_node`, `analysis_spec_value`; `assessment_value` strict on `run` (§3, §7) |
| `python/src/beliefs/record.py` | `AssessmentValue.run` docstring: bare on both sides (§3.2) |
| `python/src/beliefs/admission.py` | `admit` resolves through `typed_ref` (§3.2) |
| `python/src/beliefs/evaluation.py` | `gather` resolves through `typed_ref` (§3.2) |
| `python/src/beliefs/verify.py` | `ComparisonReport.projection()`, `_Derived`/`_derive`, `StoredVerification`, `_restore_report`, `decode_verification`, `publication_node` (§4, §5.1, §6) |
| `python/src/beliefs/audit.py` | `check_assessment`'s lookup, `_assessment_disagreements`, `check_verification` widened, `check_analysis_spec`, `stored_specs`, the `analysis-spec` branch (§3.2, §6) |
| `python/src/beliefs/corpus.py` | `_refuse_verification`, `_refuse_r20_contradiction` through `analysis_spec_value`, both called from `_refuse` (§5.3, §7) |
| `python/src/beliefs/errors.py` | `VerificationTargetMismatch(WriteRefused)` (§5.3) |
| `python/src/beliefs/spec.py` | `frozen_projection`, `restore` and its three inverse helpers (§7) |
| `python/tests/test_stored.py`, `test_admission.py`, `test_verify.py`, `test_audit.py`, `test_import_derivation.py`, `test_operation_writes.py`, `test_corpus_write.py`, `test_evaluation.py`, `test_spec.py` | the portable arms, one module per cut §3 cell |
| `python/tools/reproduction/spec.py`, `belief.py`, `rederive.py`, `close.py` | steps 4, 8, 10b and the evidence (§11) |
| `docs/designs/2026-09-06-verification-publication-design.md`, the guide, the ledger, the roadmap, `README.md`, `docs/designs/2026-08-02-computation-reproducibility-design.md`, `2026-08-30-run-confinement-design.md`, `docs/plans/2026-09-04-conformance-cut-18-results.md` | banking and discharge (Tasks 11–12) |

---

### Task 1: One spelling for the run member (V2) — `beliefs-ae9b18`

**Files:**
- Modify: `python/src/beliefs/stored.py` (after `WORLD_RELATIONS`, and `assessment_value` at lines 381–399; `__all__`)
- Modify: `python/src/beliefs/record.py:78-98` (docstring only)
- Modify: `python/src/beliefs/admission.py:54-56`
- Modify: `python/src/beliefs/evaluation.py:174-179`
- Modify: `python/src/beliefs/audit.py:169`, `:191-209`
- Modify: `python/tests/test_verification_identity.py` (the spec target)
- Test: `python/tests/test_stored.py`, `python/tests/test_admission.py`, `python/tests/test_verification_identity.py`

**Interfaces:**
- Produces: `stored.typed_ref(kind: str, local: str) -> str`, `stored.local_id(kind: str, ref: str) -> str`; `AssessmentValue.run` is the bare address from `stored.assessment_value`.

- [ ] **Step 1: `tasks start beliefs-ae9b18`** (from the worktree root).

- [ ] **Step 2: Correct the identity test's spec target**

The stored assessment's `proposition` is the proposition record's ref and the derived one is the spec's `target` (design §9, decision 1's limitation). The reproduction met them by setting the target to the ref; the test does the same. In `tests/test_verification_identity.py` replace

```python
    frozen = freeze(spec_draft(), held_rules=spec_rules())
```

with

```python
    frozen = freeze(spec_draft(target="proposition:p1"), held_rules=spec_rules())
```

Run: `uv run --frozen pytest tests/test_verification_identity.py -p no:cacheprovider`
Expected: still FAIL at the first assertion, the two identities differing on `run` only.

- [ ] **Step 3: Write the failing helper-pair tests** — append to `tests/test_stored.py`:

```python
# --- V2: the one place a kind prefix is added or removed (design §3.1) --------
import pytest

from beliefs.errors import MalformedRecord
from beliefs.runrecord import run_ref
from beliefs.stored import local_id, typed_ref


def test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref():
    address = "a" * 64
    assert typed_ref("run", address) == run_ref(address) == f"run:{address}"
    assert local_id("run", f"run:{address}") == address
    assert typed_ref("assessment", "a1") == "assessment:a1"
    assert local_id("verification", "verification:v-1") == "v-1"


@pytest.mark.parametrize(
    "call",
    [
        lambda: typed_ref("run", "run:abc"),
        lambda: typed_ref("run", ""),
        lambda: typed_ref("not-a-kind", "abc"),
        lambda: local_id("run", "abc"),
        lambda: local_id("run", "run:"),
        lambda: local_id("run", "assessment:abc"),
        lambda: local_id("run", None),
    ],
)
def test_v2_the_helper_pair_refuses_the_wrong_shape(call):
    with pytest.raises(MalformedRecord):
        call()


def test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one():
    from beliefs import stored

    node = stored.assessment_node(
        "a1", title="a1", spec="s", run="run:r1", proposition="proposition:p", outcome="supported",
        interpretation_rule="rule-1",
    )
    assert stored.assessment_value(node).run == "r1"
    node.facets[stored.ASSESSMENT_FACET]["run"] = "r1"
    with pytest.raises(MalformedRecord):
        stored.assessment_value(node)
    del node.facets[stored.ASSESSMENT_FACET]["run"]
    with pytest.raises(MalformedRecord):
        stored.assessment_value(node)
```

And append to `tests/test_admission.py`:

```python
# --- V2: admit resolves the bare run through the typed ref (design §3.2) ------
def test_v2_admit_matches_a_typed_run_ref_to_the_bare_member():
    from beliefs.admission import AdmissionRefused, admit
    from beliefs.record import AssessmentValue, RunValue

    assessment = AssessmentValue(spec="s", run="r1", proposition="p", outcome="supported", interpretation_rule="rule-1")
    other = RunValue(ref="run:r2", spec="s", inputs=())
    refused = admit(assessment, other, {}, ())
    assert isinstance(refused, AdmissionRefused) and refused.reason.startswith("run-mismatch")
    same = RunValue(ref="run:r1", spec="s", inputs=())
    assert admit(assessment, same, {}, ()).reason.startswith("no-observes-input")
```

- [ ] **Step 4: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_stored.py tests/test_admission.py -k v2 -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'local_id'`, and the admission test's first assertion (`admit` compares the typed ref to the bare member and reports `run-mismatch` for `run:r1` too).

- [ ] **Step 5: Add the helper pair to `stored.py`** after `WORLD_RELATIONS`:

```python
def typed_ref(kind: str, local: str) -> str:
    """`kind:local` — the one place a kind prefix is added (design §3.1). A
    stored facet spells a reference typed; a derived value spells an identity
    bare; this and `local_id` are the whole bridge."""
    if kind not in WORLD_KINDS:
        raise MalformedRecord(f"{kind!r} is not a world kind")
    if type(local) is not str or not local or local.startswith(f"{kind}:"):
        raise MalformedRecord(f"{local!r} is not a bare {kind} id")
    return f"{kind}:{local}"


def local_id(kind: str, ref: str) -> str:
    """The inverse of `typed_ref`: exactly the kind prefix removed, refusing a
    reference that does not carry it."""
    if kind not in WORLD_KINDS:
        raise MalformedRecord(f"{kind!r} is not a world kind")
    prefix = f"{kind}:"
    if type(ref) is not str or not ref.startswith(prefix) or len(ref) == len(prefix):
        raise MalformedRecord(f"{ref!r} is not a typed {kind} reference")
    return ref[len(prefix):]
```

Add `"local_id"` and `"typed_ref"` to `__all__` (alphabetical). In `assessment_value` replace `run=str(facet.get("run", "")),` with `run=local_id("run", facet.get("run")),` and extend its docstring: "`run` is handed back bare — the run's address, the world identity the derivation digests — and a facet whose `run` is absent or untyped is malformed (design §3.2)."

- [ ] **Step 6: Resolve through the typed ref at the three resolvers and drop the audit's normalization**

`admission.py`: add `from beliefs.stored import typed_ref` and replace

```python
    if run.ref != assessment.run:
        return AdmissionRefused(uid, f"run-mismatch: assessment names {assessment.run!r}, given {run.ref!r}")
```

with

```python
    if run.ref != typed_ref("run", assessment.run):
        return AdmissionRefused(uid, f"run-mismatch: assessment names {assessment.run!r}, given {run.ref!r}")
```

`evaluation.py`, in `gather`, replace the run loop's head:

```python
    for a in matched:
        ref = stored.typed_ref("run", a.run)
        if a.run in runs or not view.holds(ref):
            continue
        runs[a.run] = run_value(view, ref)
        trace.append(("run", a.run))
```

(`runs` stays keyed by the value's bare `a.run`, and the trace row and `declared_refs` both spell it that way.)

`audit.py`: in `check_assessment` replace `closure, why = _closure(view, stored_value.run)` with `closure, why = _closure(view, stored.typed_ref("run", stored_value.run))`; in `_assessment_disagreements` replace `if stored_value.run != run_ref(derived.run):` with `if stored_value.run != derived.run:`, delete the docstring sentence beginning "`run` is normalized first" and the module docstring's clause "after `run` is normalized from a bare closure address to its typed stored reference" (replace with "both spelled bare"), and drop `run_ref` from the `runrecord` import if it is now unused.

`record.py`: replace `AssessmentValue.run`'s implicit position with a docstring line under `run: str`: `"""The run's bare closure address — its world identity — on the derived and the stored side alike (verification-publication design §3)."""`

- [ ] **Step 7: Fix the fixtures that spelled a stored run bare**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -30` and fix every failure that is a `MalformedRecord` from `assessment_value` or a `run-mismatch`: a fixture assessment whose `run=` is not `run:`-prefixed gets the prefix; a test asserting `assessment_value(node).run == "run:…"` asserts the bare form; a test building `RunValue(ref=…)` keeps the typed ref. Do not weaken any assertion; every edit is a spelling.

- [ ] **Step 8: Run the suite and the identity test**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3` → all pass.
Run: `uv run --frozen pytest tests/test_verification_identity.py -p no:cacheprovider` → PASS (all three assertions).
Run: `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 9: Commit**

```bash
tasks done beliefs-ae9b18 "typed_ref/local_id in stored; AssessmentValue.run bare on both sides; admit, gather and check_assessment resolve through the typed ref; test_verification_identity passes"
git add -A python tasks
git commit -m "feat(stored): one spelling for the assessment's run member (V2)"
```

---

### Task 2: The stored verification's reader (V1's round trip, V6's malformed report)

**Files:**
- Modify: `python/src/beliefs/verify.py` (`ComparisonReport`, new `StoredVerification`, `_restore_report`, `decode_verification`, `__all__`)
- Test: `python/tests/test_verify.py`

**Interfaces:**
- Produces: `ComparisonReport.projection() -> dict[str, object]`; `class StoredVerification` with members `original, replayed, assessment, rule, report, scope_rule, scope, verdict, supersedes`, `basis()`, `identity()`; `decode_verification(node: Node) -> StoredVerification | None`.
- Consumes: `stored.local_id`, `stored.verification_derivation`, `stored.VERIFICATION_FACET`, `stored.VERIFIES` (Task 1 and existing).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_verify.py`:

```python
# --- V1 / V6: the stored verification's reader (design §4.2) -----------------
from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.errors import MalformedRecord
from beliefs.verify import StoredVerification, decode_verification


def _facet_for(verification: AssessmentVerification) -> dict:
    return {
        "assessment": verification.assessment,
        "scope": verification.scope,
        "verdict": verification.verdict,
        "derivation": {
            "original": stored.typed_ref("run", verification.original),
            "replayed": stored.typed_ref("run", verification.replayed),
        },
        "rule": verification.rule,
        "scope_rule": verification.scope_rule,
        "report": verification.report.projection(),
    }


def _node_for(verification: AssessmentVerification, *, facet: dict | None = None, identity: str | None = None) -> Node:
    identity = verification.identity() if identity is None else identity
    node_id = f"verification:{identity}"
    return stored.stamp_semantic_identity(
        Node(
            id=node_id,
            kind="verification",
            title="v",
            facets={stored.VERIFICATION_FACET: _facet_for(verification) if facet is None else facet},
            relations=[Relation(source=node_id, predicate=stored.VERIFIES, target="assessment:a")],
        )
    )


def test_v1_projection_is_what_identity_digests(pair):
    report = verification_of(pair).report
    assert report.identity() == v1.digest(COMPARISON_REPORT_DOMAIN, report.projection())
    assert set(report.projection()) == {"original_conformance", "replay_conformance", "receipts", "rule_bindings", "diagnostics"}


def test_v1_decode_restores_the_basis_and_the_report_by_identity(pair):
    verification = verification_of(pair)
    decoded = decode_verification(_node_for(verification))
    assert isinstance(decoded, StoredVerification)
    assert decoded.basis() == verification.basis()
    assert decoded.identity() == verification.identity()
    assert decoded.report.identity() == verification.report.identity()
    assert decoded.assessment == verification.assessment and decoded.supersedes is None


def test_v1_a_report_less_verification_decodes_as_absent(pair):
    verification = verification_of(pair)
    facet = _facet_for(verification)
    del facet["report"]
    assert decode_verification(_node_for(verification, facet=facet)) is None
    assert decode_verification(stored.verification_node("v", title="v", assessment="x", assessment_ref="assessment:a", scope="same-environment", verdict="passed")) is None


def test_v5_a_record_id_that_does_not_recompute_is_malformed(pair):
    verification = verification_of(pair)
    with pytest.raises(MalformedRecord, match="recomputed identity"):
        decode_verification(_node_for(verification, identity="f" * 64))
    facet = _facet_for(verification)
    facet["scope"] = "clean-environment" if facet["scope"] != "clean-environment" else "same-environment"
    with pytest.raises(MalformedRecord, match="recomputed identity"):
        decode_verification(_node_for(verification, facet=facet))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda f: f["report"].pop("receipts"),
        lambda f: f["report"].__setitem__("receipts", [f["report"]["receipts"][0]]),
        lambda f: f["report"].__setitem__("diagnostics", [1]),
        lambda f: f["report"].__setitem__("certification", {"rationale": "r"}),
        lambda f: f["report"].__setitem__("extra", 1),
        lambda f: f.pop("rule"),
        lambda f: f.__setitem__("supersedes", "v-1"),
        lambda f: f.__setitem__("assessment", None),
    ],
)
def test_v6_a_present_but_malformed_report_or_member_is_refused(pair, mutate):
    verification = verification_of(pair)
    facet = _facet_for(verification)
    mutate(facet)
    with pytest.raises(MalformedRecord):
        decode_verification(_node_for(verification, facet=facet))


def test_v7_the_assessment_member_and_the_verifies_edge_travel_together(pair):
    verification = verification_of(pair)
    node = _node_for(verification)
    node.relations = []
    with pytest.raises(MalformedRecord, match="present together"):
        decode_verification(node)
    node = _node_for(verification)
    node.relations.append(Relation(source=node.id, predicate=stored.VERIFIES, target="assessment:b"))
    with pytest.raises(MalformedRecord, match="at most one"):
        decode_verification(node)
```

(`pair`, `verification_of`, `v1`, `COMPARISON_REPORT_DOMAIN`, `pytest` and `AssessmentVerification` are already imported or defined in `test_verify.py`; add any that are not.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_verify.py -k "v1 or v5 or v6 or v7" -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'StoredVerification'`.

- [ ] **Step 3: Make the projection public and add the reader** in `verify.py`

Replace `ComparisonReport.identity` with:

```python
    def projection(self) -> dict[str, object]:
        """The canonical mapping `identity()` digests — and what a published
        verification stores under `report` (design §4.1)."""
        projection: dict[str, object] = {
            "original_conformance": self.original_conformance,
            "replay_conformance": self.replay_conformance,
            "receipts": list(self.receipts),
            "rule_bindings": [list(pair) for pair in self.rule_bindings],
            "diagnostics": list(self.diagnostics),
        }
        if self.certification is not None:
            projection["certification"] = _certification_projection(self.certification)
        if self.citation is not None:
            projection["citation"] = _citation_projection(self.citation)
        return projection

    def identity(self) -> str:
        return v1.digest(COMPARISON_REPORT_DOMAIN, self.projection())
```

Update `ComparisonReport.__init__`'s message to "minted only by build_verification and restored by decode_verification". After `RunVerification: TypeAlias = ...` add:

```python
@sealed
@final
@dataclass(frozen=True)
class StoredVerification:
    """A published verification read back: the same basis as the derived
    value, minted only by `decode_verification` after the record's id
    recomputes from its members (design §4.2). Distinct from the derived
    types on purpose — R19 admits no constructor that accepts a report."""

    original: str
    replayed: str
    assessment: str | None
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None

    def basis(self) -> dict[str, object]:
        members: dict[str, object] = {
            "original": self.original,
            "replayed": self.replayed,
            "rule": self.rule,
            "report": self.report,
            "scope_rule": self.scope_rule,
            "scope": self.scope,
            "verdict": self.verdict,
            "supersedes": self.supersedes,
        }
        if self.assessment is not None:
            members["assessment"] = self.assessment
        return _basis(members)

    def identity(self) -> str:
        return v1.digest(RUN_VERIFICATION_DOMAIN, self.basis())


_REPORT_REQUIRED = frozenset({"original_conformance", "replay_conformance", "receipts", "rule_bindings", "diagnostics"})
_REPORT_OPTIONAL = frozenset({"certification", "citation"})
_PUBLISHED_REQUIRED = frozenset({"scope", "verdict", "derivation", "rule", "scope_rule", "report"})
_PUBLISHED_OPTIONAL = frozenset({"assessment", "supersedes"})


def _string_list(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(type(member) is not str for member in value):
        raise MalformedRecord(f"{where} must be a list of strings")
    return tuple(value)


def _restore_report(node_id: str, member: object) -> ComparisonReport:
    if not isinstance(member, Mapping) or not _REPORT_REQUIRED <= set(member) <= _REPORT_REQUIRED | _REPORT_OPTIONAL:
        raise MalformedRecord(f"{node_id}: a report member carries exactly the comparison report's projection")
    bindings = member["rule_bindings"]
    if not isinstance(bindings, list) or any(
        not isinstance(pair, list) or len(pair) != 2 or any(type(half) is not str for half in pair) for pair in bindings
    ):
        raise MalformedRecord(f"{node_id}: report rule bindings must be a list of string pairs")
    certification = None
    if "certification" in member:
        claim = member["certification"]
        if not isinstance(claim, Mapping) or set(claim) != {"rationale", "attribution"}:
            raise MalformedRecord(f"{node_id}: a report certification names exactly rationale and attribution")
        certification = CodeLineageCertification(rationale=claim["rationale"], attribution=claim["attribution"])
    citation = None
    if "citation" in member:
        cited = member["citation"]
        if not isinstance(cited, Mapping) or set(cited) != {"report_ref", "index", "content"}:
            raise MalformedRecord(f"{node_id}: a report citation names exactly report_ref, index and content")
        citation = EmbeddedCitation(report_ref=cited["report_ref"], index=cited["index"], content=cited["content"])
    return _mint_comparison_report(
        original_conformance=member["original_conformance"],
        replay_conformance=member["replay_conformance"],
        receipts=_string_list(member["receipts"], f"{node_id}: report receipts"),
        rule_bindings=tuple((pair[0], pair[1]) for pair in bindings),
        certification=certification,
        citation=citation,
        diagnostics=_string_list(member["diagnostics"], f"{node_id}: report diagnostics"),
    )


def decode_verification(node: Node) -> StoredVerification | None:
    """A published verification read back, or `None` for one that carries no
    report (cut 18 ruling R2: not malformed, only unchecked for scope). A
    present member that is malformed, or an id that does not recompute from
    the members, is refused — never repaired (M11). Pure over the node."""
    if node.kind != "verification":
        raise MalformedRecord(f"{node.id}: not a verification record")
    facet = node.facets.get(stored.VERIFICATION_FACET)
    if not isinstance(facet, dict):
        raise MalformedRecord(f"{node.id}: a verification carries a {stored.VERIFICATION_FACET!r} facet")
    if "report" not in facet:
        return None
    keys = set(facet)
    if not _PUBLISHED_REQUIRED <= keys or not keys <= _PUBLISHED_REQUIRED | _PUBLISHED_OPTIONAL:
        raise MalformedRecord(f"{node.id}: a published verification carries exactly its basis members")
    derivation = stored.verification_derivation(node)
    assert derivation is not None  # `derivation` is required above; `verification_derivation` validated it
    edges = [relation for relation in node.relations if relation.predicate == stored.VERIFIES]
    if len(edges) > 1:
        raise MalformedRecord(f"{node.id}: a verification carries at most one verifies edge")
    if ("assessment" in facet) != bool(edges):
        raise MalformedRecord(f"{node.id}: the assessment member and the verifies edge are present together or not at all")
    for name in ("rule", "scope_rule", "scope", "verdict"):
        if type(facet[name]) is not str:
            raise MalformedRecord(f"{node.id}: verification {name} must be a string")
    assessment = facet.get("assessment")
    if "assessment" in facet and type(assessment) is not str:
        raise MalformedRecord(f"{node.id}: verification assessment must be a string")
    supersedes = facet.get("supersedes")
    if supersedes is not None:
        supersedes = stored.local_id("verification", supersedes)
    members: dict[str, Any] = {
        "original": stored.local_id("run", derivation[0]),
        "replayed": stored.local_id("run", derivation[1]),
        "rule": facet["rule"],
        "report": _restore_report(node.id, facet["report"]),
        "scope_rule": facet["scope_rule"],
        "scope": facet["scope"],
        "verdict": facet["verdict"],
        "supersedes": supersedes,
    }
    checked: dict[str, object] = dict(members)
    if assessment is not None:
        checked["assessment"] = assessment
    _validate_verification(checked)
    decoded = StoredVerification(assessment=assessment, **members)
    if decoded.identity() != stored.local_id("verification", node.id):
        raise MalformedRecord(f"{node.id}: the recomputed identity is not the record id")
    return decoded
```

Imports to add at the top of `verify.py`: `from typing import Any` (beside `TypeAlias, cast, final`), `from nodes.core.node import Node`, `from beliefs import stored`. Add `"StoredVerification"` and `"decode_verification"` to `__all__`.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run --frozen pytest tests/test_verify.py -p no:cacheprovider` → PASS (the R18/R19 tests included: `identity()`'s bytes are unchanged).
Run: `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "feat(verify): StoredVerification and decode_verification restore a published verification by identity (V1, V6)"
```

---

### Task 3: The publication projection (V1, V7) — `beliefs-f860f1`

**Files:**
- Modify: `python/src/beliefs/stored.py` (`governed_node` beside `_node` at line 670; `__all__`)
- Modify: `python/src/beliefs/verify.py` (`publication_node`; `__all__`)
- Test: `python/tests/test_verify.py`

**Interfaces:**
- Produces: `stored.governed_node(kind: str, local: str, title: str, facets: Mapping[str, Any], relations: Sequence[Relation]) -> Node`; `verify.publication_node(derived: RunVerification, *, assessment_ref: str | None = None) -> Node`.
- Consumes: Task 2's `decode_verification`.

- [ ] **Step 1: `tasks start beliefs-f860f1`**

- [ ] **Step 2: Write the failing tests** — append to `tests/test_verify.py`:

```python
# --- V1 / V7: the publication projection (design §5.1) ------------------------
from beliefs.verify import DatasetProductionVerification, publication_node


def _production_verification(production_pair) -> DatasetProductionVerification:
    first, second = production_pair
    verification = build_verification(
        first.run, second.run, specs={}, held_rules={"impl-dataset-eq-1": DATASET_CONTENT_EQUALITY},
        contract_identity="contract-1", epoch="epoch-1",
    )
    assert isinstance(verification, DatasetProductionVerification)
    return verification


def test_v1_publication_node_round_trips_through_the_reader(pair):
    verification = verification_of(pair)
    node = publication_node(verification, assessment_ref="assessment:a")
    assert node.id == f"verification:{verification.identity()}"
    assert [(r.predicate, r.target) for r in node.relations] == [(stored.VERIFIES, "assessment:a")]
    facet = node.facets[stored.VERIFICATION_FACET]
    assert facet["derivation"] == {"original": f"run:{verification.original}", "replayed": f"run:{verification.replayed}"}
    assert facet["report"] == verification.report.projection() and "supersedes" not in facet
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)
    decoded = decode_verification(node)
    assert decoded is not None and decoded.basis() == verification.basis()


def test_v7_the_production_shape_publishes_edge_less_and_admits_nothing(production_pair):
    verification = _production_verification(production_pair)
    node = publication_node(verification)
    assert node.relations == [] and "assessment" not in node.facets[stored.VERIFICATION_FACET]
    decoded = decode_verification(node)
    assert decoded is not None and decoded.assessment is None and decoded.identity() == verification.identity()
    with pytest.raises(NotAnAssessmentVerification):
        admission_record(verification)


def test_v7_publication_node_refuses_the_cross(pair, production_pair):
    with pytest.raises(MalformedRecord, match="corpus ref"):
        publication_node(verification_of(pair))
    with pytest.raises(MalformedRecord):
        publication_node(verification_of(pair), assessment_ref="proposition:p")
    with pytest.raises(MalformedRecord, match="no assessment"):
        publication_node(_production_verification(production_pair), assessment_ref="assessment:a")
    with pytest.raises(MalformedRecord):
        publication_node("not a verification")  # type: ignore[arg-type]
```

(`DATASET_CONTENT_EQUALITY`, `NotAnAssessmentVerification` and `admission_record` are already used in `test_verify.py`; import any that are not.)

- [ ] **Step 3: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_verify.py -k "publication or v7" -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'publication_node'`.

- [ ] **Step 4: Add `governed_node` and `publication_node`**

`stored.py`, after `_node`:

```python
def governed_node(kind: str, local: str, title: str, facets: Mapping[str, Any], relations: Sequence[Relation]) -> Node:
    """`_node`'s public twin for builders outside this module (verification
    publication, design §5.1): a stamped record of a governed kind. The stamp's
    one construction authority is unchanged."""
    if kind not in SEMANTIC_DOMAINS:
        raise MalformedRecord(f"kind {kind!r} has no semantic-identity domain")
    return _node(kind, local, title, facets, relations)
```

Add `"governed_node"` to `__all__`. `verify.py`, after `decode_verification`:

```python
def publication_node(derived: RunVerification, *, assessment_ref: str | None = None) -> Node:
    """The stored record of a derived verification, total over both shapes
    (design §5.1). Pure: reads no view, holds no lock; `decode_verification`
    over the result restores the same basis."""
    if type(derived) is AssessmentVerification:
        if assessment_ref is None:
            raise MalformedRecord("an assessment verification publishes against its assessment's corpus ref")
        stored.local_id("assessment", assessment_ref)
        title = f"verification of {assessment_ref}"
    elif type(derived) is DatasetProductionVerification:
        if assessment_ref is not None:
            raise MalformedRecord("a dataset-production verification has no assessment to verify")
        title = "dataset-production verification"
    else:
        raise MalformedRecord("publication_node requires a derived RunVerification")
    facet: dict[str, object] = {
        "scope": derived.scope,
        "verdict": derived.verdict,
        "derivation": {
            "original": stored.typed_ref("run", derived.original),
            "replayed": stored.typed_ref("run", derived.replayed),
        },
        "rule": derived.rule,
        "scope_rule": derived.scope_rule,
        "report": derived.report.projection(),
    }
    if type(derived) is AssessmentVerification:
        facet["assessment"] = derived.assessment
    if derived.supersedes is not None:
        facet["supersedes"] = stored.typed_ref("verification", derived.supersedes)
    identity = derived.identity()
    relations: list[Relation] = []
    if assessment_ref is not None:
        relations.append(Relation(source=f"verification:{identity}", predicate=stored.VERIFIES, target=assessment_ref))
    return stored.governed_node("verification", identity, title, {stored.VERIFICATION_FACET: facet}, relations)
```

Import `from nodes.core.relations import Relation` in `verify.py`; add `"publication_node"` to `__all__`.

- [ ] **Step 5: Run to verify they pass, then the suite**

Run: `uv run --frozen pytest tests/test_verify.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 6: Commit**

```bash
tasks done beliefs-f860f1 "publication_node stores the comparison report's projection, rule, scope_rule and typed derivation under verification:<identity>; decode_verification restores it by identity"
git add -A python tasks
git commit -m "feat(verify): publication_node projects a derived verification to its stored record (V1, V7)"
```

---

### Task 4: The audit recomputes scope through the constructor's own derivation (V4, V6)

**Files:**
- Modify: `python/src/beliefs/verify.py` (`_Derived`, `_derive`, `build_verification`)
- Modify: `python/src/beliefs/audit.py:113-162` (`check_verification`)
- Test: `python/tests/test_audit.py`

**Interfaces:**
- Produces: `verify._derive(original, replayed, *, specs, held_rules, certification, citation) -> _Derived` with members `rule, implementation_identity, report, scope, verdict, assessment`.
- Consumes: Task 2's `decode_verification`, Task 3's `publication_node`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_audit.py`:

```python
# --- V4 / V6: scope, rule, scope rule and report are recomputed (design §6) ---
from beliefs.verify import decode_verification, publication_node


def _published(writer, *, agreeing: bool = True):
    """A published verification over two persisted runs and the stored
    assessment it verifies; returns (evidence, derived, stored node)."""
    evidence, derived = _replayed_pair(writer, agreeing=agreeing)
    original = writer.read_view.get(stored.typed_ref("run", derived.original))
    assessment = writer.add(
        stored.assessment_node(
            "a1", title="a1", spec=runrecord.decode_run_closure(original).recipe.spec_identity,
            run=original.id, proposition="proposition:p", outcome="supported", interpretation_rule="median-difference/v1",
        )
    )
    node = writer.add(publication_node(derived, assessment_ref=assessment.id))
    return evidence, derived, node


def _self_consistent_forgery(writer, node, *, mutate):
    """V4's fixture (design decision 16): alter a member, then recompute the
    id, the relation source and the stamp so the record decodes and only the
    derivation recomputation can catch it."""
    facet = dict(node.facets[stored.VERIFICATION_FACET])
    facet["report"] = dict(facet["report"])
    mutate(facet)
    # The id is recomputed from the altered members through the reader's own basis.
    from beliefs.verify import StoredVerification, _restore_report

    members = {
        "original": stored.local_id("run", facet["derivation"]["original"]),
        "replayed": stored.local_id("run", facet["derivation"]["replayed"]),
        "assessment": facet["assessment"],
        "rule": facet["rule"],
        "report": _restore_report(node.id, facet["report"]),
        "scope_rule": facet["scope_rule"],
        "scope": facet["scope"],
        "verdict": facet["verdict"],
        "supersedes": None,
    }
    identity = StoredVerification(**members).identity()
    forged_id = f"verification:{identity}"
    forged = stored.stamp_semantic_identity(
        Node(
            id=forged_id, kind="verification", title=node.title, facets={stored.VERIFICATION_FACET: facet},
            relations=[Relation(source=forged_id, predicate=r.predicate, target=r.target) for r in node.relations],
        )
    )
    assert decode_verification(forged) is not None, "V4's fixture must decode; a malformed one tests nothing"
    raw_write(writer.root, forged)  # behind the boundary on purpose: the audit is what catches it
    return forged


def test_v2_a_contradicted_assessment_still_contradicts(writer, tmp_path):
    """Decision 13: the assessment audit resolves the bare run through the typed ref, so a raw-altered outcome (stamp recomputed) contradicts at audit and refuses at import."""
    evidence, derived, node = _published(writer)
    assessment = writer.read_view.get("assessment:a1")
    altered = assessment.model_copy(deep=True)
    altered.facets[stored.ASSESSMENT_FACET]["outcome"] = "refuted"
    stored.stamp_semantic_identity(altered)
    raw_write(writer.root, altered)
    view = reopen(writer.root)
    codes = {f.code for f in audit_corpus(view, evidence=evidence)}
    assert "assessment-derivation-contradicted" in codes and "semantic-hash-stale" not in codes
    from test_relocation import _writer

    from beliefs.errors import ImportRefused

    target = _writer(tmp_path / "target")
    members = tuple(n for n in view.iter_stored() if n.kind in {"dataset", "run"}) + (altered,)
    with pytest.raises(ImportRefused):
        target.import_bundle(members, evidence=evidence, observer="o", instrument="i", opened_at="2026-09-06T00:00:00Z", closed_at="2026-09-06T00:00:01Z")


def _contradictions(writer, evidence):
    view = reopen(writer.root)
    return [f for f in audit_corpus(view, evidence=evidence) if f.code == "verification-derivation-contradicted"]


def test_v4_a_published_verification_audits_checked_with_no_contradiction(writer):
    evidence, derived, node = _published(writer)
    outcome = check_verification(writer.read_view, writer.read_view.get(node.id), evidence=evidence)
    assert outcome.checked and outcome.contradiction is None
    assert not _contradictions(writer, evidence)


@pytest.mark.parametrize(
    "member, mutate",
    [
        ("scope", lambda f: f.__setitem__("scope", "clean-environment")),
        ("verdict", lambda f: f.__setitem__("verdict", "failed")),
        ("report", lambda f: f["report"].__setitem__("receipts", ["sha256:" + "0" * 64, f["report"]["receipts"][1]])),
        ("report", lambda f: f["report"].__setitem__("original_conformance", "non-conforming: forged")),
        ("rule", lambda f: f.__setitem__("rule", "some-other-rule/v1")),
        ("scope_rule", lambda f: f.__setitem__("scope_rule", "scope-derivation/v9")),
    ],
)
def test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member(writer, member, mutate):
    evidence, derived, node = _published(writer)
    forged = _self_consistent_forgery(writer, node, mutate=mutate)
    (finding,) = _contradictions(writer, evidence)
    assert finding.ref == forged.id and member in finding.detail


def test_v6_a_report_less_verification_is_checked_for_verdict_and_identity_only(writer):
    evidence, derived, node = _published(writer)
    facet = dict(node.facets[stored.VERIFICATION_FACET])
    del facet["report"], facet["rule"], facet["scope_rule"]
    facet["scope"] = "clean-environment"  # a raised scope a report-less record cannot be caught on (cut 18 §7)
    legacy = stored.stamp_semantic_identity(
        Node(id="verification:legacy", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, legacy)
    outcome = check_verification(reopen(writer.root), reopen(writer.root).get(legacy.id), evidence=evidence)
    assert outcome.checked and outcome.contradiction is None
    facet["verdict"] = "failed"
    flipped = stored.stamp_semantic_identity(
        Node(id="verification:legacy-flipped", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, flipped)
    outcome = check_verification(reopen(writer.root), reopen(writer.root).get(flipped.id), evidence=evidence)
    assert outcome.contradiction is not None and "verdict" in outcome.contradiction.detail
```

Imports needed at the top of `test_audit.py` if absent: `from nodes.core.relations import Relation`, `from fixtures_cut4 import reopen`, `from beliefs.audit import audit_corpus, check_verification`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_audit.py -k "v4 or v6" -p no:cacheprovider`
Expected: the `scope`, `report`, `rule` and `scope_rule` cases FAIL with no contradiction found (`ValueError: not enough values to unpack`); the `verdict` case and V6 pass already — cut 18's path.

- [ ] **Step 3: Extract `_derive` in `verify.py`** — before `build_verification`:

```python
@dataclass(frozen=True)
class _Derived:
    rule: str
    implementation_identity: str
    report: ComparisonReport
    scope: str
    verdict: str
    assessment: str | None


def _derive(
    original: RunClosure,
    replayed: RunClosure,
    *,
    specs: Mapping[str, FrozenSpec],
    held_rules: Mapping[str, EquivalenceImplementation],
    certification: CodeLineageCertification | None,
    citation: EmbeddedCitation | None,
) -> _Derived:
    """The one derivation, for the constructor and for the audit (design
    decision 8). Every scope-bearing fact is read from the runs; the
    certification and citation are the authored claims the caller embeds."""
    rule, implementation_identity, implementation, spec = _resolve_rule(original, specs=specs, held_rules=held_rules)
    verdict = implementation.evaluate(original.result, replayed.result)
    if verdict not in VERDICTS:
        raise MalformedRecord(f"equivalence evaluator returned {verdict!r}, outside {VERDICTS}")
    report = _mint_comparison_report(
        original_conformance=conformance(original),
        replay_conformance=conformance(replayed),
        receipts=(original.occurrence.receipt.identity(), replayed.occurrence.receipt.identity()),
        rule_bindings=((rule, implementation_identity),),
        certification=certification,
        citation=citation,
        diagnostics=_job_diagnostics(original, replayed),
    )
    assessment = None
    if spec is not None:
        assessment = v1.digest(
            record.ASSESSMENT_DOMAIN,
            {"spec": spec.identity, "run": original.address(), "proposition": spec.target},
        )
    return _Derived(rule, implementation_identity, report, derive_scope(original, replayed, certification=certification), verdict, assessment)
```

Then rewrite the body of `build_verification` after its three refusals and the two `_require_str` calls:

```python
    embedded_citation = None
    if citation is not None:
        published, index = citation
        entry = cite(published, index)
        embedded_citation = EmbeddedCitation(report_ref=published.identity(), index=index, content=_entry_facet(entry))
    derived = _derive(original, replayed, specs=specs, held_rules=held_rules, certification=certification, citation=embedded_citation)
    common = {
        "original": original.address(),
        "replayed": replayed.address(),
        "rule": derived.rule,
        "report": derived.report,
        "scope_rule": original.recipe.boundary_policy.scope_rule,
        "scope": derived.scope,
        "verdict": derived.verdict,
    }
    return _mint_verification(assessment=derived.assessment, supersedes=None, **common)
```

- [ ] **Step 4: Widen `check_verification` in `audit.py`**

Replace its body from `derivation = ...` to the `disagreements` construction with:

```python
    derivation = stored.verification_derivation(node)  # MalformedRecord propagates: refuse, never repair
    if derivation is None:
        return _unchecked("no derivation member")
    decoded = decode_verification(node)  # a present, malformed report is refused the same way
    original, why = _closure(view, derivation[0])
    if original is None:
        return _unchecked(why)
    replayed, why = _closure(view, derivation[1])
    if replayed is None:
        return _unchecked(why)
    if original.recipe.shape != replayed.recipe.shape:
        return _unchecked("mixed shapes")
    certification = None if decoded is None else decoded.report.certification
    citation = None if decoded is None else decoded.report.citation
    try:
        derived = _derive(
            original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
            certification=certification, citation=citation,
        )
    except RuleUnbound as unbound:
        return _unchecked(str(unbound))
    stored_value = stored.verification_value(node)
    disagreements: list[str] = []
    if derived.verdict != stored_value.verdict:
        disagreements.append(f"verdict stored={stored_value.verdict!r} recomputed={derived.verdict!r}")
    if derived.assessment is not None and derived.assessment != stored_value.assessment:
        disagreements.append("assessment identity differs from the original run's derivation")
    if decoded is not None:
        if decoded.rule != derived.rule:
            disagreements.append(f"rule stored={decoded.rule!r} recomputed={derived.rule!r}")
        scope_rule = original.recipe.boundary_policy.scope_rule
        if decoded.scope_rule != scope_rule:
            disagreements.append(f"scope_rule stored={decoded.scope_rule!r} recomputed={scope_rule!r}")
        if decoded.scope != derived.scope:
            disagreements.append(f"scope stored={decoded.scope!r} recomputed={derived.scope!r}")
        if decoded.report.identity() != derived.report.identity():
            disagreements.append("report identity differs from the recomputed report")
```

Keep the existing `if not disagreements: … return DerivationOutcome(... Finding(code="verification-derivation-contradicted" ...))` tail. Replace `from beliefs.verify import _resolve_rule` with `from beliefs.verify import _derive, decode_verification`; drop the now-unused `ASSESSMENT_DOMAIN`, `v1` and `VERDICTS` imports if nothing else uses them. Update the docstring: "Recompute a stored verification's derivation from the two runs it names — verdict and assessment identity always; rule, scope rule, scope and report identity when the record carries its report (design §6)."

- [ ] **Step 5: Run to verify they pass, then the suite**

Run: `uv run --frozen pytest tests/test_audit.py tests/test_verify.py tests/test_import_derivation.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 6: Commit**

```bash
git add -A python
git commit -m "feat(audit): recompute scope, rule, scope rule and report over a stored verification through the constructor's derivation (V4, V6)"
```

---

### Task 5: Forgery refused before the intent (V5, V6's import arms, V4's import half)

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `ValidationRefused`, line 1087)
- Modify: `python/src/beliefs/corpus.py:2265-2281` (`_refuse`), new `_refuse_verification`
- Test: `python/tests/test_operation_writes.py`, `python/tests/test_import_derivation.py`, `python/tests/test_corpus_write.py`

**Interfaces:**
- Produces: `errors.VerificationTargetMismatch(WriteRefused)`; `CorpusWriter._refuse_verification(node, *, view)`.
- Consumes: Task 2's `decode_verification`, Task 3's `publication_node`, Task 1's `assessment_value`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_operation_writes.py`:

```python
# --- V5: forgery is refused before the intent (design §5.3) ------------------
from fixtures_cut3 import spec_draft, spec_rules
from test_audit import _verification_evidence, add_observed_datasets, assessment_closure, run_publication

from nodes.core.relations import Relation

from beliefs.errors import MalformedRecord, VerificationTargetMismatch
from beliefs.runrecord import run_ref
from beliefs.spec import freeze
from beliefs.verify import build_verification, publication_node


def _publishable(writer):
    """Two persisted runs, the stored assessment and the derived verification."""
    frozen = freeze(spec_draft(target="proposition:p"), held_rules=spec_rules())
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(frozen, token="tok-replayed")
    add_observed_datasets(writer, original)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    assessment = writer.add(
        stored.assessment_node(
            "a1", title="a1", spec=frozen.identity, run=run_ref(original.address()), proposition="proposition:p",
            outcome="supported", interpretation_rule=frozen.interpretation_rule,
        )
    )
    evidence = _verification_evidence(frozen)
    derived = build_verification(
        original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
        contract_identity="science:" + "c" * 64, epoch="epoch:" + "e" * 64,
    )
    return assessment, derived


def _forgeries(writer, assessment, derived):
    good = publication_node(derived, assessment_ref=assessment.id)
    stale_id = good.model_copy(update={"id": "verification:" + "f" * 64})
    stale_id.relations = [Relation(source=stale_id.id, predicate=r.predicate, target=r.target) for r in good.relations]
    stored.stamp_semantic_identity(stale_id)
    bad_report = good.model_copy(deep=True)
    bad_report.facets[stored.VERIFICATION_FACET]["report"]["diagnostics"] = ["forged"]
    stored.stamp_semantic_identity(bad_report)
    no_edge = good.model_copy(deep=True, update={"relations": []})
    stored.stamp_semantic_identity(no_edge)
    twin_a1 = writer.add(stored.proposition_node("p9", title="p9", claim={"operator": "affects"}))
    wrong_target = publication_node(derived, assessment_ref="assessment:absent")
    other = writer.add(
        stored.assessment_node(
            "other", title="other", spec="s-other", run=stored.typed_ref("run", derived.original), proposition=twin_a1.id,
            outcome="supported", interpretation_rule="rule-1",
        )
    )
    other_identity = publication_node(derived, assessment_ref=other.id)
    return [
        (stale_id, MalformedRecord),
        (bad_report, MalformedRecord),
        (no_edge, MalformedRecord),
        (wrong_target, VerificationTargetMismatch),
        (other_identity, VerificationTargetMismatch),
    ]


def test_v5_each_forgery_is_refused_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    assessment, derived = _publishable(writer)
    port.calls.clear()
    for node, refusal in _forgeries(writer, assessment, derived):
        with pytest.raises(refusal):
            writer.operations.add(node)
        assert not [c for c in port.calls if c[0] == "append_intent"], node.id
        assert writer.read_view.resolve(node.id) is None
    commit = writer.operations.add(publication_node(derived, assessment_ref=assessment.id))
    assert commit.record is not None and primitive_calls(port)[-3:] == ["preflight", "append_intent", "execute_fulfilling"]
```

Append to `tests/test_import_derivation.py`:

```python
# --- V4 / V5 / V6 at the import boundary (design §5.4) ------------------------
from test_audit import _published, _self_consistent_forgery

from beliefs.errors import VerificationTargetMismatch
from beliefs.verify import publication_node


def test_v5_a_forged_published_verification_refuses_the_bundle_before_any_write(tmp_path):
    source = _writer(tmp_path / "source")
    evidence, derived, node = _published(source)
    forged = _self_consistent_forgery(source, node, mutate=lambda f: f.__setitem__("scope", "clean-environment"))
    target = _writer(tmp_path / "target")
    runs = [source.read_view.get(stored.typed_ref("run", derived.original)), source.read_view.get(stored.typed_ref("run", derived.replayed))]
    datasets = [n for n in source.read_view.iter_stored() if n.kind == "dataset"]
    assessment = source.read_view.get("assessment:a1")
    with pytest.raises(ImportRefused):
        target.import_bundle((*datasets, *runs, assessment, forged), evidence=evidence, **IMPORT_FIELDS)
    assert not path_for(target.root, forged.id).exists() and not path_for(target.root, assessment.id).exists()
    wrong_target = publication_node(derived, assessment_ref="assessment:absent")
    with pytest.raises(ImportRefused, match="VerificationTargetMismatch|resolves to no record"):
        target.import_bundle((*datasets, *runs, assessment, wrong_target), evidence=evidence, **IMPORT_FIELDS)
    report = target.import_bundle((*datasets, *runs, assessment, source.read_view.get(node.id)), evidence=evidence, **IMPORT_FIELDS)
    assert "derivation-unchecked" not in " ".join(_report_findings(report))


def test_v6_a_report_less_verification_imports_on_cut_18s_terms(tmp_path):
    pair = _two_runs(tmp_path / "source", mount=True, agreeing=True)
    target = _writer(tmp_path / "target")
    legacy = _stored_from(pair.verification, slug="legacy")
    contradicting = _stored_from(pair.verification, slug="flipped", verdict=_flip(pair.verification.verdict))
    derivation_less = stored.verification_node(
        "bare", title="bare", assessment=pair.verification.assessment, assessment_ref=ASSESSMENT_REF,
        scope=pair.verification.scope, verdict=pair.verification.verdict,
    )
    report = target.import_bundle((derivation_less,), evidence=pair.evidence, **IMPORT_FIELDS)
    assert any(f.startswith("derivation-unchecked: verification:bare") for f in _report_findings(report))
    report = target.import_bundle((legacy,), evidence=pair.evidence, **IMPORT_FIELDS)
    assert any(f.startswith("derivation-unchecked: verification:legacy") for f in _report_findings(report))  # its runs are not in the bundle
    with pytest.raises(ImportRefused):
        target.import_bundle((*pair.datasets, pair.original_node, pair.replayed_node, contradicting), evidence=pair.evidence, **IMPORT_FIELDS)
```

Confirm `_two_runs`' returned namespace carries `verification`, `evidence`, `original_node`, `replayed_node` and the datasets (read `tests/test_import_derivation.py:150-200`); if the datasets are not on it, mint them with `add_observed_datasets` into the target before the last import and drop `*pair.datasets`.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_operation_writes.py tests/test_import_derivation.py -k "v5 or v6" -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'VerificationTargetMismatch'`.

- [ ] **Step 3: Add the refusal class** — `errors.py`, after `ValidationRefused`:

```python
class VerificationTargetMismatch(WriteRefused):
    """A published verification's `verifies` edge does not resolve to an
    assessment carrying the identity the verification names — before the
    intent, at `add` and at import (verification-publication design §5.3).
    Equality of identity is the whole requirement: a second assessment record
    with the same identity is an equally valid target (decision 17)."""
```

- [ ] **Step 4: Add the preflight step** — `corpus.py`, in `_refuse`, between `self._refuse_invalid(node)`'s block and `self._refuse_governed_stamp(node)`:

```python
        if node.kind == "verification":
            self._refuse_verification(node, view=self._view if view is None else view)
```

and, after `_refuse_governed_stamp`:

```python
    def _refuse_verification(self, node: Node, *, view: ReadView | _ImportView) -> None:
        """Self-consistency of a published verification, before the intent
        (design §5.3): the record decodes — id, report identity, edge
        cardinality — and its `verifies` target is an assessment carrying the
        named identity. A report-less verification is admitted on cut 18's
        terms. No run is read: derivation validation is the import's and the
        audit's alone."""
        from beliefs.verify import decode_verification  # local: `audit` imports this module

        decoded = decode_verification(node)  # MalformedRecord propagates: refuse, never repair
        if decoded is None or decoded.assessment is None:
            return
        (edge,) = [relation for relation in node.relations if relation.predicate == stored.VERIFIES]
        if not view.holds(edge.target):
            raise VerificationTargetMismatch(f"{node.id}: the verifies target {edge.target!r} resolves to no record here")
        target = view.get(edge.target)
        if target.kind != "assessment":
            raise VerificationTargetMismatch(f"{node.id}: the verifies target {edge.target!r} is a {target.kind}, not an assessment")
        identity = stored.assessment_value(target).identity()
        if identity != decoded.assessment:
            raise VerificationTargetMismatch(
                f"{node.id}: the verifies target carries assessment identity {identity}, not the verification's {decoded.assessment}"
            )
```

Import `VerificationTargetMismatch` from `beliefs.errors` in `corpus.py`. Confirm `self._view` is the writer's read view attribute (it is what `_validated_import_bundle` wraps); if `_refuse` is also reached with `view=None` from a path where the view is not yet built, use `self.read_view`.

- [ ] **Step 5: Run to verify they pass, then the suite**

Run: `uv run --frozen pytest tests/test_operation_writes.py tests/test_import_derivation.py tests/test_corpus_write.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 6: Commit**

```bash
git add -A python
git commit -m "feat(corpus): refuse a forged or mistargeted published verification before the intent (V5)"
```

---

### Task 6: The analysis-spec record (V8) — `beliefs-91aac6`

**Files:**
- Modify: `python/src/beliefs/spec.py` (`frozen_projection`, `restore`, the three inverse helpers; `__all__`)
- Modify: `python/src/beliefs/stored.py` (`ANALYSIS_SPEC_FACET`, `analysis_spec_node`, `analysis_spec_value`; `__all__`)
- Modify: `python/src/beliefs/corpus.py:2099-2112` (`_refuse_r20_contradiction`) and `_refuse`
- Modify: `python/src/beliefs/audit.py` (`check_analysis_spec`, `stored_specs`, the dispatch)
- Test: `python/tests/test_spec.py`, `python/tests/test_stored.py`, `python/tests/test_audit.py`, `python/tests/test_import_derivation.py`

**Interfaces:**
- Produces: `spec.frozen_projection(spec: FrozenSpec) -> dict[str, object]`; `spec.restore(identity: str, projection: bytes) -> FrozenSpec`; `stored.ANALYSIS_SPEC_FACET = "analysis-spec"`; `stored.analysis_spec_node(spec: FrozenSpec) -> Node`; `stored.analysis_spec_value(node: Node) -> FrozenSpec`; `audit.check_analysis_spec(node: Node) -> DerivationOutcome`; `audit.stored_specs(view) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]`.

- [ ] **Step 1: `tasks start beliefs-91aac6`**

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_spec.py`:

```python
# --- V8: restore from canonical projection text (design §7) -------------------
from decimal import Decimal

import pytest
from fixtures_cut3 import spec_draft, spec_rules

from beliefs.errors import MalformedRecord, UnfreezableSpec
from beliefs.identity import v1
from beliefs.spec import (
    ExclusionCertification,
    Seeded,
    SpecInput,
    StochasticUnseeded,
    freeze,
    frozen_projection,
    restore,
)


def _rich_spec():
    draft = spec_draft(
        input_roles=(
            SpecInput(role="observes", dataset="dataset:" + "1" * 64),
            SpecInput(role="reads", dataset="dataset:" + "2" * 64, exclusion=ExclusionCertification(rationale="r", attribution="a")),
        ),
        parameters={"alpha": Decimal("0.05"), "iterations": 10, "labels": ["a", "b"], "nested": {"k": Decimal("1.5")}},
    )
    return freeze(draft, held_rules=spec_rules())


def test_v8_restore_round_trips_every_member_and_the_decimal_by_type():
    spec = _rich_spec()
    text = v1.encode(frozen_projection(spec))
    restored = restore(spec.identity, text)
    assert restored == spec and restored.identity == spec.identity
    assert type(restored.parameters["alpha"]) is Decimal and restored.parameters["alpha"] == Decimal("0.05")
    assert type(restored.parameters["iterations"]) is int
    assert isinstance(restored.nondeterminism, Seeded) and restored.input_roles[1].exclusion is not None
    assert v1.encode(frozen_projection(restored)) == text


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda m: m.__setitem__("method", "another method"),
        lambda m: m.__setitem__("extra", 1),
        lambda m: m.pop("estimand"),
        lambda m: m["parameters"].__setitem__("alpha", Decimal("0.5")),
    ],
)
def test_v8_restore_refuses_a_projection_that_does_not_digest_to_the_identity(corrupt):
    spec = _rich_spec()
    mapping = frozen_projection(spec)
    corrupt(mapping)
    with pytest.raises(MalformedRecord):
        restore(spec.identity, v1.encode(mapping))


def test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair():
    spec = _rich_spec()
    text = v1.encode(frozen_projection(spec))
    with pytest.raises(MalformedRecord):
        restore(spec.identity, text + b"\n")
    with pytest.raises(MalformedRecord):
        restore(spec.identity, b"{}")
    draft = spec_draft(nondeterminism=StochasticUnseeded(rationale="urandom"), equivalence_rule="content-identity-equality/v1")
    mapping = {**frozen_projection(freeze(spec_draft(), held_rules=spec_rules())), "nondeterminism": draft.nondeterminism.projection()}
    from beliefs.spec import SPEC_DOMAIN

    identity = v1.digest(SPEC_DOMAIN, mapping)
    with pytest.raises(UnfreezableSpec):
        restore(identity, v1.encode(mapping))
```

Append to `tests/test_stored.py`:

```python
# --- V8: the analysis-spec record (design §7) --------------------------------
from decimal import Decimal

from fixtures_cut3 import spec_draft, spec_rules
from test_relocation import _writer

from beliefs import stored
from beliefs.spec import freeze


def test_v8_analysis_spec_node_round_trips_through_the_writer_and_the_reader(tmp_path):
    spec = freeze(spec_draft(parameters={"alpha": Decimal("0.05")}), held_rules=spec_rules())
    writer = _writer(tmp_path / "corpus")
    node = writer.add(stored.analysis_spec_node(spec))
    assert node.id == f"analysis-spec:{spec.identity}"
    assert set(node.facets[stored.ANALYSIS_SPEC_FACET]) == {"identity", "projection"}
    restored = stored.analysis_spec_value(writer.read_view.get(node.id))
    assert restored == spec and type(restored.parameters["alpha"]) is Decimal


def test_v8_a_renamed_or_falsely_identified_record_is_malformed(tmp_path):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    node = stored.analysis_spec_node(spec)
    renamed = node.model_copy(update={"id": "analysis-spec:elsewhere"})
    with pytest.raises(MalformedRecord, match="not the spec identity"):
        stored.analysis_spec_value(renamed)
    node.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = node.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    stored.stamp_semantic_identity(node)  # the stamp passes; restoration is what detects the mismatch
    with pytest.raises(MalformedRecord):
        stored.analysis_spec_value(node)
    with pytest.raises(MalformedRecord):
        stored.analysis_spec_value(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
```

Append to `tests/test_audit.py`:

```python
# --- V8: no spec disappears silently (design decision 15) --------------------
from beliefs.audit import check_analysis_spec, stored_specs
from beliefs.spec import freeze


def test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it(writer):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    good = writer.add(stored.analysis_spec_node(spec))
    forged = stored.analysis_spec_node(spec).model_copy(update={"id": "analysis-spec:forged"})
    forged.facets[stored.ANALYSIS_SPEC_FACET]["identity"] = "forged"
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    stored.stamp_semantic_identity(forged)
    raw_write(writer.root, forged)
    view = reopen(writer.root)
    assert check_analysis_spec(view.get(good.id)).checked
    with pytest.raises(MalformedRecord):
        check_analysis_spec(view.get(forged.id))
    specs, findings = stored_specs(view)
    assert set(specs) == {spec.identity} and [f.ref for f in findings] == [forged.id] and findings[0].code == "derivation-malformed"
    assert [f.ref for f in audit_corpus(view, evidence=NO_EVIDENCE) if f.code == "derivation-malformed"] == [forged.id]


def test_v4_the_audit_reaches_the_same_verdict_with_specs_restored_from_the_corpus(writer):
    evidence, derived, node = _published(writer)
    frozen = next(iter(evidence.specs.values()))
    writer.add(stored.analysis_spec_node(frozen))
    specs, findings = stored_specs(writer.read_view)
    assert not findings and set(specs) == {frozen.identity}
    from dataclasses import replace

    from_corpus = replace(evidence, specs=specs)
    outcome = check_verification(writer.read_view, writer.read_view.get(node.id), evidence=from_corpus)
    assert outcome.checked and outcome.contradiction is None
```

Append to `tests/test_import_derivation.py`:

```python
def test_v8_a_spec_record_whose_identity_is_false_refuses_the_bundle(tmp_path):
    from beliefs.spec import freeze

    spec = freeze(spec_draft(), held_rules=spec_rules())
    forged = stored.analysis_spec_node(spec)
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    stored.stamp_semantic_identity(forged)
    target = _writer(tmp_path / "target")
    with pytest.raises(ImportRefused):
        target.import_bundle((forged,), evidence=NO_EVIDENCE, **IMPORT_FIELDS)
    assert not path_for(target.root, forged.id).exists()
```

(`NO_EVIDENCE` from `beliefs.evidence`; `MalformedRecord` and `pytest` as needed.)

- [ ] **Step 3: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_spec.py tests/test_stored.py tests/test_audit.py tests/test_import_derivation.py -k v8 -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'frozen_projection'`.

- [ ] **Step 4: Add `frozen_projection` and `restore` to `spec.py`** after `freeze`:

```python
def frozen_projection(spec: FrozenSpec) -> dict[str, object]:
    """The mapping `SPEC_DOMAIN` digests for a frozen spec — what a stored
    `analysis-spec` record carries as canonical text (design §7)."""
    if type(spec) is not FrozenSpec:
        raise MalformedRecord("frozen_projection requires a FrozenSpec")
    return _facet_projection(spec, spec.rule_bindings, spec.supersedes)


_FROZEN_MEMBERS = frozenset(
    {
        "target", "estimand", "method", "assumptions", "falsification", "input_roles", "applicability",
        "interpretation_rule", "equivalence_rule", "parameters", "nondeterminism", "rule_bindings",
    }
)


def _restore_input(entry: object) -> SpecInput:
    if not isinstance(entry, dict) or not {"role", "dataset"} <= set(entry) <= {"role", "dataset", "exclusion"}:
        raise MalformedRecord("a spec input names role and dataset, with an optional exclusion")
    exclusion = None
    if "exclusion" in entry:
        claim = entry["exclusion"]
        if not isinstance(claim, dict) or set(claim) != {"rationale", "attribution"}:
            raise MalformedRecord("an exclusion names exactly rationale and attribution")
        exclusion = ExclusionCertification(rationale=str(claim["rationale"]), attribution=str(claim["attribution"]))
    return SpecInput(role=str(entry["role"]), dataset=str(entry["dataset"]), exclusion=exclusion)


def _restore_nondeterminism(value: object) -> NondeterminismContract:
    if not isinstance(value, dict) or type(value.get("variant")) is not str:
        raise MalformedRecord("a nondeterminism member names its variant")
    variant = value["variant"]
    if variant == "deterministic" and set(value) == {"variant"}:
        return Deterministic()
    if variant == "stochastic-unseeded" and set(value) == {"variant", "rationale"}:
        return StochasticUnseeded(rationale=str(value["rationale"]))
    if variant == "seeded" and set(value) == {"variant", "plan"}:
        plan = value["plan"]
        if not isinstance(plan, dict) or set(plan) != {"derivation_rule", "streams", "roots", "stream_roots"}:
            raise MalformedRecord("a seed plan names derivation_rule, streams, roots and stream_roots")
        return Seeded(
            plan=SeedPlan(
                derivation_rule=str(plan["derivation_rule"]),
                streams=tuple(str(s) for s in plan["streams"]),
                roots={str(k): int(v) for k, v in plan["roots"].items()},
                stream_roots={str(k): str(v) for k, v in plan["stream_roots"].items()},
            )
        )
    raise MalformedRecord(f"nondeterminism variant {variant!r} is not one of the three")


def restore(identity: str, projection: bytes) -> FrozenSpec:
    """The third mint: a frozen spec from its stored canonical projection
    (design §7). Refuses text that is not canonical, a mapping that is not
    exactly the frozen members, a digest that is not `identity`, and the
    pair `freeze` refuses — so a stored spec is exactly one `freeze` produced."""
    try:
        mapping = v1.decode(projection)
    except CanonicalTextRefused as refused:
        raise MalformedRecord(f"analysis-spec {identity[:12]}: the projection is not canonical text: {refused}") from refused
    if not isinstance(mapping, dict) or not _FROZEN_MEMBERS <= set(mapping) <= _FROZEN_MEMBERS | {"supersedes"}:
        raise MalformedRecord(f"analysis-spec {identity[:12]}: the projection carries exactly the frozen members")
    if v1.digest(SPEC_DOMAIN, mapping) != identity:
        raise MalformedRecord(f"analysis-spec {identity[:12]}: the projection does not digest to the identity")
    if not isinstance(mapping["input_roles"], list) or not isinstance(mapping["rule_bindings"], list):
        raise MalformedRecord(f"analysis-spec {identity[:12]}: input_roles and rule_bindings are lists")
    bindings = mapping["rule_bindings"]
    if any(not isinstance(pair, list) or len(pair) != 2 or any(type(half) is not str for half in pair) for pair in bindings):
        raise MalformedRecord(f"analysis-spec {identity[:12]}: rule bindings are string pairs")
    nondeterminism = _restore_nondeterminism(mapping["nondeterminism"])
    equivalence_rule = str(mapping["equivalence_rule"])
    if isinstance(nondeterminism, StochasticUnseeded) and equivalence_rule in BITWISE_EQUIVALENCE_RULES:
        raise UnfreezableSpec("stochastic-unseeded cannot support a bitwise equivalence rule (computation §3.1a)")
    supersedes = mapping.get("supersedes")
    if supersedes is not None and type(supersedes) is not str:
        raise MalformedRecord(f"analysis-spec {identity[:12]}: supersedes is a string")
    return _mint_frozen_spec(
        target=str(mapping["target"]),
        estimand=str(mapping["estimand"]),
        method=str(mapping["method"]),
        assumptions=str(mapping["assumptions"]),
        falsification=str(mapping["falsification"]),
        input_roles=tuple(_restore_input(entry) for entry in mapping["input_roles"]),
        applicability=str(mapping["applicability"]),
        interpretation_rule=str(mapping["interpretation_rule"]),
        equivalence_rule=equivalence_rule,
        parameters=_freeze_parameter_value(mapping["parameters"]),
        nondeterminism=nondeterminism,
        rule_bindings=tuple((pair[0], pair[1]) for pair in bindings),
        supersedes=supersedes,
        identity=identity,
    )
```

Import `CanonicalTextRefused` from `beliefs.errors`. Add `"frozen_projection"` and `"restore"` to `__all__`. Widen `FrozenSpec.__init__`'s message to "FrozenSpec values are minted by freeze, revise or restore". If `_mint_frozen_spec` does not accept the `parameters` value as frozen (check `FrozenSpec.__post_init__`), pass the decoded mapping through the same freezing `SpecDraft.__post_init__` applies.

- [ ] **Step 5: Add the builder and reader to `stored.py`**

Add `ANALYSIS_SPEC_FACET = "analysis-spec"` beside the other facet names and use it in `SEMANTIC_DOMAINS`/`COVERED_FACETS` for `"analysis-spec"`. Add `from beliefs.spec import FrozenSpec, frozen_projection, restore` and, after `verification_node`:

```python
def analysis_spec_node(spec: FrozenSpec) -> Node:
    """A frozen spec as a stored record: its identity and its canonical
    projection text — the run record's pattern, so a `Decimal` parameter
    round-trips and the identity is the text's digest by construction
    (design §7)."""
    if type(spec) is not FrozenSpec:
        raise MalformedRecord("analysis_spec_node requires a FrozenSpec")
    projection = v1.encode(frozen_projection(spec)).decode("utf-8")
    facet = {"identity": spec.identity, "projection": projection}
    return _node("analysis-spec", spec.identity, f"spec {spec.identity[:12]}", {ANALYSIS_SPEC_FACET: facet}, ())


def analysis_spec_value(node: Node) -> FrozenSpec:
    """The frozen spec a stored record carries, restored and refused on any
    disagreement between its text, its identity and its id (M11)."""
    if node.kind != "analysis-spec":
        raise MalformedRecord(f"{node.id}: not an analysis-spec record")
    facet = _facet(node, ANALYSIS_SPEC_FACET)
    if facet is None or set(facet) != {"identity", "projection"} or type(facet["identity"]) is not str or type(facet["projection"]) is not str:
        raise MalformedRecord(f"{node.id}: an analysis-spec facet is exactly {{identity, projection}}")
    spec = restore(facet["identity"], facet["projection"].encode("utf-8"))
    if node.id != typed_ref("analysis-spec", spec.identity):
        raise MalformedRecord(f"{node.id}: the record id is not the spec identity")
    return spec
```

Add both to `__all__`. Confirm the module graph stays acyclic: `spec.py` imports `errors`, `identity`, `sealed` only.

- [ ] **Step 6: Route the preflight and the r20 check through the reader** — `corpus.py`:

Replace `_refuse_r20_contradiction`'s body with:

```python
    @staticmethod
    def _refuse_r20_contradiction(record: Node) -> None:
        """A stored spec restores, or the record is refused: the r20 pair is
        `restore`'s `UnfreezableSpec`, surfaced as document validation."""
        if record.kind != "analysis-spec":
            return
        try:
            stored.analysis_spec_value(record)
        except UnfreezableSpec as caught:
            raise ValidationRefused(f"{record.id}: {caught}") from caught
```

and in `_refuse`, beside the verification step:

```python
        if node.kind == "analysis-spec":
            self._refuse_r20_contradiction(node)
```

Import `UnfreezableSpec` from `beliefs.errors`. Then find every test fixture that hand-builds an `analysis-spec` record (`grep -rn '"analysis-spec"' tests/ | grep -v analysis_spec_node`) and rebuild each through `stored.analysis_spec_node(freeze(...))`; a fixture that existed to exercise the r20 refusal builds a `StochasticUnseeded` draft under `content-identity-equality/v1` and asserts `ValidationRefused` from the writer (its `freeze` would refuse, so build its node from the projection mapping by hand exactly as `test_spec.py`'s unfreezable case does, stamped through `stamp_semantic_identity`).

- [ ] **Step 7: Add the audit branch and `stored_specs`** — `audit.py`:

```python
def check_analysis_spec(node: Node) -> DerivationOutcome:
    """A stored spec restores or is malformed; `audit_corpus` reports the
    latter as `derivation-malformed` under the catch R11 already has."""
    stored.analysis_spec_value(node)
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def stored_specs(view: ReadView | _ImportView) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]:
    """Every restorable stored spec keyed by identity, and one
    `derivation-malformed` finding per record that does not restore — the
    two halves travel together so a false spec never vanishes into an
    unchecked derivation (design decision 15)."""
    specs: dict[str, FrozenSpec] = {}
    findings: list[Finding] = []
    for node in view.iter_stored():
        if node.kind != "analysis-spec":
            continue
        try:
            spec = stored.analysis_spec_value(node)
        except RecordError as refused:
            findings.append(
                Finding(
                    severity="error",
                    code="derivation-malformed",
                    ref=node.id,
                    detail=str(refused),
                    message=f"{node.id}: the members a derivation recomputation reads are malformed",
                )
            )
            continue
        specs[spec.identity] = spec
    return MappingProxyType(specs), tuple(findings)
```

In `audit_corpus`'s dispatch add `elif node.kind == "analysis-spec": outcome = check_analysis_spec(node)` after the `dataset` branch. Imports: `from collections.abc import Mapping`, `from types import MappingProxyType`, `from beliefs.spec import FrozenSpec`. Add both names to `__all__`.

- [ ] **Step 8: Run to verify they pass, then the suite**

Run: `uv run --frozen pytest tests/test_spec.py tests/test_stored.py tests/test_audit.py tests/test_import_derivation.py tests/test_corpus_write.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 9: Commit**

```bash
tasks done beliefs-91aac6 "stored.analysis_spec_node / analysis_spec_value over canonical projection text; spec.restore recomputes the identity; the preflight, the r20 check and audit_corpus restore every spec; stored_specs returns specs and findings"
git add -A python tasks
git commit -m "feat(spec): a stored analysis-spec builder and reader over canonical projection text (V8)"
```

---

### Task 7: Admission over records read back (V3, V7's gather arm; V2 widened)

**Files:**
- Test: `python/tests/test_evaluation.py`, `python/tests/test_verification_identity.py`

**Interfaces:**
- Consumes: Tasks 1–6.

- [ ] **Step 1: Widen the identity test to the full path** — replace the tail of `tests/test_verification_identity.py` from `stored_node = writer.add(` onward with:

```python
    from beliefs.verify import publication_node

    stored_node = writer.add(publication_node(verification, assessment_ref=assessment.id))
    view = writer.read_view

    stored_identity = stored.assessment_value(view.get(assessment.id)).identity()
    assert stored_identity == derived.identity() == record.assessment, (
        "one spelling for the run member: the stored assessment reads back the identity its run derives"
    )
    verifications = (stored.verification_value(view.get(stored_node.id)),)
    assert lifecycle_state(tuple(v for v in verifications if v.assessment == stored_identity)) == ADMITTED
    outcome = check_verification(view, view.get(stored_node.id), evidence=evidence)
    assert outcome.checked and outcome.contradiction is None

    # V2 in full: gather -> admit over the corpus, the gate's every clause.
    from test_verification_publication import admission_over

    verdict, belief = admission_over(writer, proposition.id, original)
    assert isinstance(verdict, Admitted), verdict
    assert isinstance(belief, Belief), belief
```

with `from beliefs.admission import Admitted` and `from beliefs.belief import Belief` at the top.

- [ ] **Step 2: Write the V3/V7 module** — create `tests/test_verification_publication.py`:

```python
"""V3 and V7's gather arm (design §8): admission is evaluated over records
read back, and the belief moves with the verification record."""

from __future__ import annotations

from fixtures_cut3 import spec_draft, spec_rules
from test_audit import add_observed_datasets, assessment_closure, run_publication, writer  # noqa: F401
from test_belief import PROFILE
from test_evaluation import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO

from beliefs import stored
from beliefs.admission import admit
from beliefs.belief import Availability, Belief, NoBelief, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.corpus import lineage_snapshot
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.evaluation import evaluate_over, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.resolution import build_snapshot
from beliefs.runrecord import run_ref
from beliefs.spec import freeze
from beliefs.verify import AssessmentVerification, build_verification, publication_node
from test_audit import _verification_evidence

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


def _observations(view):
    """One observation per held dataset, at its declared digest, so `admit`
    reads every input as Held."""
    observations = {}
    for node in view.iter_stored():
        if node.kind != "dataset":
            continue
        declaration = stored.dataset_declaration(node)
        address = dataset_address(declaration)
        if address is not None:
            observations[address] = tuple(
                ByteObservation(digest=resource.digest, location="repo://data") for resource in declaration.resources if resource.digest
            )
    return observations


def _kwargs(view, proposition_ref: str, identities: dict[str, str]):
    addresses = list(_observations(view))
    return {
        "availability": Availability(observations=_observations(view), implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES}),
        "context": SuppliedContext(
            snapshot=lineage_snapshot(view, addresses),
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={identity: "c1" for identity in identities},
            pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
        ),
        "profile": PROFILE,
        "resolution": build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        "binding": BINDING,
    }


def admission_over(writer, proposition_ref: str, original):
    """`gather` -> `admit` -> `evaluate_over` over the corpus as it stands."""
    view = writer.read_view
    identities = {stored.assessment_value(n).identity(): n.id for n in view.iter_stored() if n.kind == "assessment"}
    kwargs = _kwargs(view, proposition_ref, identities)
    gathered = {k: v for k, v in kwargs.items() if k != "availability"}
    inputs = gather(view, proposition_ref, **gathered)
    (a,) = [a for a in inputs.assessments if a.run == original.address()]
    verdict = admit(a, inputs.runs[a.run], kwargs["availability"].observations, inputs.verifications)
    return verdict, evaluate_over(view, proposition_ref, **kwargs)


def _corpus(writer):
    """A typed proposition, two persisted runs, the stored assessment and the
    derived verification — everything V3 publishes and then moves."""
    proposition = writer.add(stored.proposition_node("p", title="p", claim=CLAIM_FACET))
    frozen = freeze(spec_draft(target=proposition.id), held_rules=spec_rules())
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(frozen, token="tok-replayed")
    add_observed_datasets(writer, original)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    assessment = writer.add(
        stored.assessment_node(
            "a1", title="a1", spec=frozen.identity, run=run_ref(original.address()), proposition=proposition.id,
            outcome="supported", interpretation_rule=frozen.interpretation_rule,
        )
    )
    evidence = _verification_evidence(frozen)
    derived = build_verification(
        original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
        contract_identity="science:" + "c" * 64, epoch="epoch:" + "e" * 64,
    )
    assert isinstance(derived, AssessmentVerification)
    return proposition, original, replayed, assessment, derived


def test_v3_the_belief_moves_with_the_verification_record(writer):
    proposition, original, replayed, assessment, derived = _corpus(writer)
    _, before = admission_over(writer, proposition.id, original)
    assert isinstance(before, NoBelief) and before.reason == "no-eligible-assessment"
    published = writer.add(publication_node(derived, assessment_ref=assessment.id))
    _, belief = admission_over(writer, proposition.id, original)
    assert isinstance(belief, Belief)
    writer.delete(published.id)
    _, after = admission_over(writer, proposition.id, original)
    assert isinstance(after, NoBelief) and after.reason == "no-eligible-assessment"


def test_v3_a_superseding_failed_verification_invalidates(writer):
    proposition, original, replayed, assessment, derived = _corpus(writer)
    first = writer.add(publication_node(derived, assessment_ref=assessment.id))
    from beliefs.verify import _mint_verification  # the private mint: `build_verification` never sets `supersedes`

    failed = _mint_verification(
        original=derived.original, replayed=derived.replayed, assessment=derived.assessment, rule=derived.rule,
        report=derived.report, scope_rule=derived.scope_rule, scope=derived.scope, verdict="failed",
        supersedes=derived.identity(),
    )
    writer.add(publication_node(failed, assessment_ref=assessment.id))
    inputs = gather(writer.read_view, proposition.id, **{k: v for k, v in _kwargs(writer.read_view, proposition.id, {}).items() if k != "availability"})
    from beliefs.verification import INVALIDATED, lifecycle_state

    assert lifecycle_state(inputs.verifications) == INVALIDATED
    assert stored.verification_value(writer.read_view.get(first.id)).ref == first.id


def test_v3_negatives_another_proposition_is_never_gathered_and_a_twin_target_admits(writer):
    proposition, original, replayed, assessment, derived = _corpus(writer)
    twin = writer.add(
        stored.assessment_node(
            "a1-twin", title="twin", spec=stored.assessment_value(assessment).spec, run=run_ref(original.address()),
            proposition=proposition.id, outcome="supported", interpretation_rule=stored.assessment_value(assessment).interpretation_rule,
        )
    )
    assert stored.assessment_value(twin).identity() == stored.assessment_value(assessment).identity()
    writer.add(publication_node(derived, assessment_ref=twin.id))  # decision 17: the twin is a valid target
    verdict, belief = admission_over(writer, proposition.id, original)
    assert isinstance(belief, Belief)
    other = writer.add(stored.proposition_node("q", title="q", claim={**CLAIM_FACET, "args": [OTHER_GENE, PHENO]}))
    inputs = gather(writer.read_view, other.id, **{k: v for k, v in _kwargs(writer.read_view, other.id, {}).items() if k != "availability"})
    assert inputs.verifications == () and inputs.assessments == ()
```

`test_verification_publication.py` sits beside the other portable modules; V3's cut cell names `test_evaluation.py` for the negatives, so add to `test_evaluation.py` one line that imports and re-exports them:

```python
from test_verification_publication import (  # noqa: F401 - V3's negatives live beside their fixture
    test_v3_negatives_another_proposition_is_never_gathered_and_a_twin_target_admits,
)
```

and for V7's gather arm append to `test_evaluation.py` (`production_pair` is module-scoped in `test_verify.py`, so it is resolved through `request`):

```python
def test_v7_gather_never_selects_a_production_verification(request, tmp_path):
    from test_verify import _production_verification
    from test_relocation import _writer

    production = _production_verification(request.getfixturevalue("production_pair"))
    writer = _writer(tmp_path / "corpus")
    node = writer.add(publication_node(production))
    fixture = _fixture(writer, PROPOSITION_REF)
    inputs = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs)
    assert node.id not in {v.ref for v in inputs.verifications}
```

with `from test_verify import production_pair  # noqa: F401` at module level so the fixture resolves, and `from beliefs.verify import publication_node`.

- [ ] **Step 3: Run**

Run: `uv run --frozen pytest tests/test_verification_publication.py tests/test_verification_identity.py tests/test_evaluation.py -p no:cacheprovider`
Expected: PASS. If `evaluate_over` answers `Refused(consulted-contracts-disagree…)`, the pins in `_kwargs` disagree with `PROFILE`'s compiled identity — copy the exact `CorpusPins` values `test_evaluation._fixture` uses at that point in the tree.

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 4: Commit**

```bash
git add -A python
git commit -m "test(evaluation): admission over records read back — the belief moves with the verification record (V3, V7)"
```

---

### Task 8: The durable suite and the module graph (V1, V2, V3, V5 on the certified volume)

**Files:**
- Create: `python/tests/acceptance/test_verification_acceptance.py`
- Test: `python/tests/test_verify.py` (the acyclic-imports assertion)

**Interfaces:**
- Consumes: `test_session_acceptance.py`'s rig (`adopted`, `attended`, `chain`, `intents`, `fresh`, `DIGEST`, `work_directory`), Tasks 1–7.

- [ ] **Step 1: Read the rig you mirror**

Run: `sed -n 40,80p tests/acceptance/conftest.py && grep -n "^DIGEST\|^PROPOSITIONS\|^def adopted\|^def attended\|^def chain" tests/acceptance/test_session_acceptance.py` and note the `work_directory` fixture, `adopted`, `attended`, `chain` and `DIGEST`.

- [ ] **Step 2: Write the module** — `tests/acceptance/test_verification_acceptance.py`:

```python
"""Cut 21's durable arms: verification publication through an attended session
on the certified engine and volume (`docs/designs/2026-09-06-conformance-cut-21.md`
§3, V1, V2, V3 and V5). Every body mirrors its portable twin and additionally
reopens the corpus — a fresh process for V1 and V3 — so each assertion is
about bytes the engine committed."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fixtures_cut3 import spec_draft, spec_rules
from test_audit import _verification_evidence, assessment_closure, run_publication
from test_belief import PROFILE  # noqa: F401 - re-exported for the fresh-process script
from test_evaluation import CLAIM_FACET
from test_session_acceptance import DIGEST, adopted, attended, chain, intents  # noqa: F401 - `work_directory` is the acceptance conftest's session fixture
from test_verification_publication import admission_over

from beliefs import stored
from beliefs.admission import Admitted
from beliefs.belief import Belief, NoBelief
from beliefs.corpus import open_corpus
from beliefs.errors import MalformedRecord, VerificationTargetMismatch
from beliefs.permit import RequiredCapabilities
from beliefs.root import metadata_root_for
from beliefs.runrecord import run_ref
from beliefs.spec import freeze
from beliefs.verify import AssessmentVerification, build_verification, decode_verification, publication_node
from authority import FULL

PINNED = [{"name": "raw", "digest": "sha256:" + "7" * 64}]
KINDS = RequiredCapabilities.for_kinds({"proposition", "dataset", "run", "assessment", "verification", "analysis-spec"}, {})


def _publish_pair(writer):
    proposition = writer.add(stored.proposition_node("p", title="p", claim=CLAIM_FACET))
    frozen = freeze(spec_draft(target=proposition.id), held_rules=spec_rules())
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(frozen, token="tok-replayed")
    for entry in original.recipe.inputs:
        if not writer.read_view.holds(entry.dataset):
            writer.add(stored.dataset_node(entry.dataset.removeprefix("dataset:"), title="raw", resources=PINNED, empirical_observation={"boundary": "instrument"}))
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    assessment = writer.add(
        stored.assessment_node(
            "a1", title="a1", spec=frozen.identity, run=run_ref(original.address()), proposition=proposition.id,
            outcome="supported", interpretation_rule=frozen.interpretation_rule,
        )
    )
    evidence = _verification_evidence(frozen)
    derived = build_verification(
        original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
        contract_identity="science:" + "c" * 64, epoch="epoch:" + "e" * 64,
    )
    assert isinstance(derived, AssessmentVerification)
    return proposition, original, assessment, derived, evidence


def _fresh_process(root: Path, script: str) -> dict:
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)])}
    completed = subprocess.run([sys.executable, "-c", script.replace("ROOT", repr(str(root)))], check=True, capture_output=True, text=True, env=env)
    return json.loads(completed.stdout.strip().splitlines()[-1])


def test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone(work_directory):
    root = adopted(work_directory, "corpus")
    session, _ = attended(work_directory, root)
    try:
        writer = session.scoped(KINDS, "A")
        session.claim_invocation("A", "mint", DIGEST)
        proposition, original, assessment, derived, evidence = _publish_pair(open_corpus(root, authority=FULL))
        node = writer.add(publication_node(derived, assessment_ref=assessment.id))
        writer.delete(stored.typed_ref("run", derived.original))
        writer.delete(stored.typed_ref("run", derived.replayed))
    finally:
        session.close()
    report = _fresh_process(
        root,
        "import json; from authority import FULL; from beliefs.corpus import open_corpus; from beliefs.verify import decode_verification\n"
        f"view = open_corpus(ROOT, authority=FULL).read_view; d = decode_verification(view.get({node.id!r}))\n"
        "print(json.dumps({'identity': d.identity(), 'report': d.report.identity(), 'scope': d.scope, 'verdict': d.verdict, 'basis': json.dumps(d.basis(), default=lambda r: r.identity(), sort_keys=True)}))",
    )
    assert report["identity"] == derived.identity() and report["report"] == derived.report.identity()
    assert (report["scope"], report["verdict"]) == (derived.scope, derived.verdict)
    assert report["basis"] == json.dumps(derived.basis(), default=lambda r: r.identity(), sort_keys=True)


def test_v2_and_v3_admission_over_the_corpus_and_the_belief_moves_with_the_record(work_directory):
    root = adopted(work_directory, "corpus")
    session, _ = attended(work_directory, root)
    library = open_corpus(root, authority=FULL)
    try:
        writer = session.scoped(KINDS, "A")
        session.claim_invocation("A", "mint", DIGEST)
        proposition, original, assessment, derived, evidence = _publish_pair(library)
        library = open_corpus(root, authority=FULL)
        _, before = admission_over(library, proposition.id, original)
        assert isinstance(before, NoBelief)
        published = writer.add(publication_node(derived, assessment_ref=assessment.id))
        library = open_corpus(root, authority=FULL)
        verdict, belief = admission_over(library, proposition.id, original)
        assert isinstance(verdict, Admitted) and isinstance(belief, Belief)
        digest_here = belief.belief_input_digest
        writer.delete(published.id)
        library = open_corpus(root, authority=FULL)
        _, after = admission_over(library, proposition.id, original)
        assert isinstance(after, NoBelief)
        writer.add(publication_node(derived, assessment_ref=assessment.id))
    finally:
        session.close()
    report = _fresh_process(
        root,
        "import json; from authority import FULL; from beliefs.corpus import open_corpus; from test_verification_publication import admission_over\n"
        "from beliefs.runrecord import decode_run_closure; from beliefs import stored\n"
        f"w = open_corpus(ROOT, authority=FULL); original = decode_run_closure(w.read_view.get({stored.typed_ref('run', derived.original)!r}))\n"
        f"verdict, belief = admission_over(w, {proposition.id!r}, original); print(json.dumps({{'digest': belief.belief_input_digest}}))",
    )
    assert report["digest"] == digest_here


def test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent(work_directory):
    from test_operation_writes import _forgeries

    root = adopted(work_directory, "corpus")
    session, ops = attended(work_directory, root)
    try:
        writer = session.scoped(KINDS, "A")
        session.claim_invocation("A", "mint", DIGEST)
        library = open_corpus(root, authority=FULL)
        proposition, original, assessment, derived, evidence = _publish_pair(library)
        head_before = chain(root).tip
        acts_before = len(session.invocation_acts("A"))
        for node, refusal in _forgeries(open_corpus(root, authority=FULL), assessment, derived):
            with pytest.raises(refusal):
                writer.add(node)
            assert chain(root).tip == head_before, node.id
            assert len(session.invocation_acts("A")) == acts_before
            assert not (root / "verification" / f"{node.id.split(':', 1)[1]}.md").exists()
        writer.add(publication_node(derived, assessment_ref=assessment.id))
        assert len(intents(root)) == len(intents(root)) and len(session.invocation_acts("A")) == acts_before + 1
    finally:
        session.close()
```

`work_directory` comes from `tests/acceptance/conftest.py` (session-scoped, `SCIENCE_CUT4_ROOT` or `.cut4-acceptance` beside the checkout; the runner points every `SCIENCE_CUT*_ROOT` at one run directory). `_forgeries` in Task 5 mints helper records through the writer it is given; here that is the library writer over the same root, which the session's next `add` sees after settlement. The head is `chain(root).tip`, the probe J1 uses.

- [ ] **Step 3: Add the acyclic-imports assertion** — append to `tests/test_verify.py`:

```python
def test_the_publication_modules_form_no_import_cycle():
    """Design §4.3: verify -> stored -> (record, verification, report, spec); audit -> verify; corpus -> verify only locally."""
    import importlib
    import sys

    for name in ("beliefs.verify", "beliefs.stored", "beliefs.spec", "beliefs.audit", "beliefs.corpus", "beliefs.evaluation", "beliefs.admission"):
        sys.modules.pop(name, None)
    importlib.import_module("beliefs.verify")
    importlib.import_module("beliefs.corpus")
    source = (Path(science_root.__file__).resolve().parent / "corpus.py").read_text(encoding="utf-8")
    assert "\nfrom beliefs.verify import" not in source and "\nimport beliefs.verify" not in source
```

(`Path` and `science_root` as in the acceptance modules: `import beliefs.root as science_root`.)

- [ ] **Step 4: Run the durable module**

Run: `SCIENCE_CUT4_ROOT=$(git rev-parse --show-toplevel)/.cut21-acceptance uv run --frozen pytest tests/acceptance/test_verification_acceptance.py -p no:cacheprovider`
Expected: PASS (4 tests). A capability refusal is an error: do not skip.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "test(acceptance): verification publication through an attended session on the certified volume (V1, V2, V3, V5)"
```

---

### Task 9: The reproduction driver reads the report (V1's and V8's 10b arms)

**Files:**
- Modify: `python/tools/reproduction/spec.py` (`spec_record`), `belief.py` (step 8), `rederive.py` (10b), `close.py` (`evidence`)

**Interfaces:**
- Consumes: `stored.analysis_spec_node`, `verify.publication_node`, `verify.decode_verification`, `audit.stored_specs`.

- [ ] **Step 1: Replace the hand-built spec record** — in `tools/reproduction/spec.py` delete `spec_record`'s body and make it:

```python
def spec_record(spec: FrozenSpec) -> Node:
    """The kernel's own builder (verification-publication design §7); the
    Task-11 finding that nothing restored a FrozenSpec is closed by it."""
    return stored.analysis_spec_node(spec)
```

and delete the step-4 `findings.record(4, "design-gap", "analysis-spec is a stored kind ... no kernel builder"...)` call if `main` still emits it (keep the interpretation-rule finding).

- [ ] **Step 2: Publish through the projection** — in `belief.py` replace the `writer.add(stored.verification_node(...))` block with:

```python
    minted = writer.add(publication_node(verification, assessment_ref=st["assessment_ref"]))
```

importing `publication_node` from `beliefs.verify`.

- [ ] **Step 3: Read the report in 10b** — in `rederive.py`, replace `"comparison_report_stored": "comparison" in facet,` with `"comparison_report_stored": "report" in facet,`, and after `derivation = stored.verification_derivation(node)` insert:

```python
    decoded = decode_verification(node)
    if decoded is not None:
        report["inputs"]["corpus"] = ["verification record (basis, comparison report, scope, verdict read)", "two run publications", "analysis-spec record"]
        report["inputs"]["in_process"] = ["interpretation and equivalence RuleImplementations"]
        report["scope_read"], report["verdict_read"] = decoded.scope, decoded.verdict
        report["report_identity_read"] = decoded.report.identity()
```

importing `decode_verification`. Keep the recomputation block that follows (it now asserts equality against the *read* values as well: add `report["scope_equal"] = scope == decoded.scope` when `decoded` is present).

- [ ] **Step 4: Compose the evidence from the corpus** — in `close.py`:

```python
def evidence() -> DerivationEvidence:
    specs, findings = stored_specs(world.open_writer().read_view)
    if findings:
        raise RuntimeError(f"stored specs that do not restore: {[f.ref for f in findings]}")
    return DerivationEvidence(
        specs=specs,
        held_rules={spec.equivalence().identity: spec.equivalence()},
        implementations={spec.interpretation().identity: spec.interpretation()},
    )
```

importing `stored_specs` from `beliefs.audit` and `world` from `reproduction`.

- [ ] **Step 5: Re-run the driver into a fresh directory** (design decision 12). From `python/`, with the predecessor corpus available as the record's §1 states:

```bash
export SCIENCE_MM30_ROOT=$(git -C "$(git rev-parse --show-toplevel)/.." rev-parse --show-toplevel 2>/dev/null || echo "$(git rev-parse --show-toplevel)/..")/.mm30-reproduction-cut21
for step in preflight select_target type_target hold world spec run belief close rederive; do
  PYTHONPATH=tools uv run --frozen python -m reproduction.$step || { echo "step $step failed"; break; }
done
```

(`SCIENCE_MM30_ROOT` must be on the certified volume beside the **main** checkout, as `paths.py` computes for `.mm30-reproduction`; set it to that checkout's sibling directory.) Expected at `rederive`: the printed 10b JSON has `"comparison_report_stored": true`, `"scope_equal": true`, `"verdict_equal": true`, and `"in_process": ["interpretation and equivalence RuleImplementations"]`; step 8 prints `admission Admitted` and a `Belief` answer. Save the 10b JSON to `docs/plans/` beside the results record later (Task 12 cites it).

- [ ] **Step 6: Run the driver's tests and the suite**

Run: `uv run --frozen pytest tests/test_reproduction_driver.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 7: Commit**

```bash
git add -A python
git commit -m "feat(reproduction): publish the verification with its report, build the spec record, read 10b from the corpus"
```

---

### Task 10: N2 arms, the cut-21 audit and the runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut21.py`, `python/tests/acceptance/test_n2_cut21.py`, `python/tools/cut21_acceptance.py`

**Interfaces:**
- Produces: `CUT21_ARMS`, `DECLARATION_UNITS = ("V1", …, "V8")`, `CO_CITED`, `unit_of`.

- [ ] **Step 1: Declare the arms** — `tests/acceptance/n2_arms_cut21.py`. One grouped unit per V row; every `before` is the exact landed line (re-read the source when writing each). The checks name Tasks 1–8's tests:

```python
"""Cut 21's eight frozen declaration units and their source sabotages
(docs/designs/2026-09-06-conformance-cut-21.md §3, §5 item 4)."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

_VERIFY, _STORED, _AUDIT, _CORPUS, _SPEC, _ADMISSION, _EVALUATION = (
    "verify.py", "stored.py", "audit.py", "corpus.py", "spec.py", "admission.py", "evaluation.py",
)
_TV, _TS, _TA, _TI, _TO, _TSP, _TE, _TID, _ACC = (
    "test_verify.py", "test_stored.py", "test_audit.py", "test_import_derivation.py", "test_operation_writes.py",
    "test_spec.py", "test_evaluation.py", "test_verification_identity.py", "acceptance/test_verification_acceptance.py",
)

DECLARATION_UNITS = tuple(f"V{n}" for n in range(1, 9))
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


CUT21_ARMS = (
    Arm("V1a", "the projection is what identity digests and what the record stores",
        Sabotage(_VERIFY, '        "report": derived.report.projection(),\n', '        "report": {},\n'),
        (f"{_TV}::test_v1_publication_node_round_trips_through_the_reader", f"{_ACC}::test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone")),
    Arm("V1b", "a record whose id does not recompute is refused by the reader",
        Sabotage(_VERIFY, "    if decoded.identity() != stored.local_id(\"verification\", node.id):\n", "    if False:\n"),
        (f"{_TV}::test_v5_a_record_id_that_does_not_recompute_is_malformed",)),
    Arm("V2a", "the stored assessment hands back the bare run",
        Sabotage(_STORED, '        run=local_id("run", facet.get("run")),\n', '        run=str(facet.get("run", "")),\n'),
        (f"{_TS}::test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one", f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean")),
    Arm("V2b", "admit resolves the bare member through the typed ref",
        Sabotage(_ADMISSION, '    if run.ref != typed_ref("run", assessment.run):\n', "    if run.ref != assessment.run:\n"),
        ("test_admission.py::test_v2_admit_matches_a_typed_run_ref_to_the_bare_member",)),
    Arm("V2c", "gather resolves the run through the typed ref",
        Sabotage(_EVALUATION, '        ref = stored.typed_ref("run", a.run)\n', "        ref = a.run\n"),
        (f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean",)),
    Arm("V2d", "the assessment audit resolves the run through the typed ref",
        Sabotage(_AUDIT, '    closure, why = _closure(view, stored.typed_ref("run", stored_value.run))\n', "    closure, why = _closure(view, stored_value.run)\n"),
        (f"{_TA}::test_v2_a_contradicted_assessment_still_contradicts",)),
    Arm("V3a", "a superseding verification is read from the record",
        Sabotage(_VERIFY, '        facet["supersedes"] = stored.typed_ref("verification", derived.supersedes)\n', "        pass\n"),
        ("test_verification_publication.py::test_v3_a_superseding_failed_verification_invalidates",)),
    Arm("V4a", "scope is recomputed over a stored verification",
        Sabotage(_AUDIT, "        if decoded.scope != derived.scope:\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[scope-mutate0]",)),
    Arm("V4b", "the report is recomputed by identity",
        Sabotage(_AUDIT, "        if decoded.report.identity() != derived.report.identity():\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[report-mutate2]",)),
    Arm("V4c", "the stored certification enters the recomputation",
        Sabotage(_AUDIT, "    certification = None if decoded is None else decoded.report.certification\n", "    certification = None\n"),
        (f"{_TA}::test_v4_a_published_verification_audits_checked_with_no_contradiction",)),
    Arm("V5a", "the verification step precedes the intent",
        Sabotage(_CORPUS, '        if node.kind == "verification":\n            self._refuse_verification(node, view=self._view if view is None else view)\n', "        pass\n"),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent", f"{_ACC}::test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent")),
    Arm("V5b", "the target's identity must equal the member",
        Sabotage(_CORPUS, "        if identity != decoded.assessment:\n", "        if False:\n"),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent",)),
    Arm("V6a", "a present, malformed report is refused, never repaired",
        Sabotage(_VERIFY, "    if not isinstance(member, Mapping) or not _REPORT_REQUIRED <= set(member) <= _REPORT_REQUIRED | _REPORT_OPTIONAL:\n", "    if False:\n"),
        (f"{_TV}::test_v6_a_present_but_malformed_report_or_member_is_refused[mutate0]",)),
    Arm("V7a", "the production shape carries no assessment member",
        Sabotage(_VERIFY, '    if type(derived) is AssessmentVerification:\n        facet["assessment"] = derived.assessment\n', '    facet["assessment"] = getattr(derived, "assessment", "")\n'),
        (f"{_TV}::test_v7_the_production_shape_publishes_edge_less_and_admits_nothing",)),
    Arm("V8a", "restore recomputes the identity",
        Sabotage(_SPEC, "    if v1.digest(SPEC_DOMAIN, mapping) != identity:\n", "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_a_projection_that_does_not_digest_to_the_identity[corrupt0]", f"{_TS}::test_v8_a_renamed_or_falsely_identified_record_is_malformed")),
    Arm("V8b", "restore refuses the unfreezable pair",
        Sabotage(_SPEC, "    if isinstance(nondeterminism, StochasticUnseeded) and equivalence_rule in BITWISE_EQUIVALENCE_RULES:\n", "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair",)),
    Arm("V8c", "stored_specs reports what it cannot restore",
        Sabotage(_AUDIT, "            findings.append(\n                Finding(\n                    severity=\"error\",\n                    code=\"derivation-malformed\",\n                    ref=node.id,\n                    detail=str(refused),\n                    message=f\"{node.id}: the members a derivation recomputation reads are malformed\",\n                )\n            )\n            continue\n        specs[spec.identity] = spec\n", "            continue\n        specs[spec.identity] = spec\n"),
        (f"{_TA}::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it",)),
)
```

V2d's check is Task 4's `test_v2_a_contradicted_assessment_still_contradicts`. Parametrized ids (`[scope-mutate0]`) must match pytest's generated ids — run `uv run --frozen pytest tests/test_audit.py --collect-only -q | grep v4` and copy them. Every `before` must occur exactly once in its module; the V8c `before` is multi-line and must match the landed indentation byte for byte.

- [ ] **Step 2: Write the audit module** — `tests/acceptance/test_n2_cut21.py`, by the cut-19 pattern (copy `test_n2_cut19.py` and adjust): `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-06-conformance-cut-21.md"`, `CUT21_FREEZE_COMMIT = "41c9920"`, `CUT21_FROZEN_SHA256 = "eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5"`, `FROZEN_PRIOR_CUT_FILES` = cut 19's table plus `"python/tests/acceptance/n2_arms_cut19.py": "8723fac"` (and, after Task 12's merge, cut 20's arms file at its last commit), `PRIOR_ARMS` gaining `CUT19_ARMS`, the inventory test asserting `DECLARATION_UNITS == tuple(f"V{n}" for n in range(1, 9))`, and the freeze test asserting `"**8 declaration units**"`, `"Eight guarantee rows are read, **8 full/closed** (V1–V8), 0 partial, 0"` and `'("cut20_acceptance.py",)'` in the current text, with `_frozen_body` spanning `## 2. The boundary` to the first `\n## 8.` (none exists yet: the whole tail).

- [ ] **Step 3: Write the runner** — `tools/cut21_acceptance.py`: copy `cut19_acceptance.py`, with `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut21-acceptance"`, `PREFIX_RUNNERS = ("cut20_acceptance.py",)`, `PHASE_MODULES = ("test_verification_acceptance.py", "test_n2_cut21.py")`, `SCIENCE_CUT21_ROOT`, `range(4, 22)` in `cut_environment`, `SCIENCE_CUT20_ROOT` in `run_prefix`'s environment, the import `from n2_arms_cut21 import CUT21_ARMS, DECLARATION_UNITS`, and the final line `f"declared arms: {arms} (= {units} declaration units; 8 guarantee rows)"`.

- [ ] **Step 4: Run the audit module directly** (the runner refuses until cut 20 merges):

Run: `SCIENCE_CUT4_ROOT=$(git rev-parse --show-toplevel)/.cut21-acceptance uv run --frozen pytest tests/acceptance/test_n2_cut21.py -p no:cacheprovider`
Expected: PASS — every arm sound, every check resolved, the freeze pinned. A `stale` finding means a `before` no longer matches the source: fix the arm, never the source.
Run: `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "test(cut21): declare the N2 arms, the cut-21 audit and the acceptance runner"
```

---

### Task 11: Bank the implementation

**Files:**
- Modify: `docs/designs/2026-09-06-verification-publication-design.md` (Status), `docs/designs/2026-08-02-computation-reproducibility-design.md` (§7.3b–§7.3c dated note), `docs/designs/2026-08-30-run-confinement-design.md` (§10), `docs/plans/2026-09-04-conformance-cut-18-results.md` (§3 R3, §4), `docs/guide/computation-and-reproducibility.md`, `docs/guide/glossary.md`

- [ ] **Step 1: The design's status** — replace the `**Status:**` paragraph's last sentence with: `**implemented through <sha of Task 10's commit>** on 2026-09-06; cut 21 undischarged, awaiting the domain lane's cut 20 (roadmap rule 5).`

- [ ] **Step 2: Dated notes.** Computation design, at the end of §7.3c: `> **Note (2026-09-06).** The stored verification carries the report's projection and its rule and scope-rule identities (verification-publication design §4.1), and scope is recomputed under audit and at import from the stored certification (§6 there).` Run-confinement design §10, after the finding sentence: `Closed 2026-09-06 by the verification-publication design.` Cut 18 results §3 R3 and §4's "Scope is not recomputed": append `— lifted 2026-09-06 by the verification-publication slice (V4); cut 21's results record carries the reading.`

- [ ] **Step 3: Guide.** `computation-and-reproducibility.md` "Current state": replace the durable-publication clause with "verification publication is implemented (verification-publication design; cut 21 undischarged until cut 20 merges)"; `updated: 2026-09-06`. `glossary.md`: add `**Published verification** — A verification record carrying its whole basis with the comparison report embedded under an id that is its identity; the audit and the import recompute its scope, and a record without a report is checked for verdict and identity only.`

- [ ] **Step 4: Tests and commit**

Run: `uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider` → PASS.

```bash
git add -A docs
git commit -m "docs(verification): bank the implementation; dated notes in the computation, run-confinement and cut 18 records"
```

---

### Task 12: Discharge after cut 20 merges — `beliefs-754995`

**Files:**
- Modify: `contracts/science/CONTRACT.yaml` and its packaged copy (the reader line, if the merged tree declares reader-shaped facets), `python/tests/acceptance/test_n2_cut21.py` (`FROZEN_PRIOR_CUT_FILES` gains cut 20's arms), the ledger, the roadmap, `README.md`, `docs/plans/2026-09-06-conformance-cut-21-results.md`

- [ ] **Step 1: Merge `main`** once the domain lane's cut 20 is discharged: `git merge --no-ff main` in the worktree; resolve every shared file toward `main` (roadmap rule 3): `_refuse`'s step order is document validation → `_refuse_facets` → `_refuse_verification`/`_refuse_r20_contradiction` → stamp; `audit_corpus` and `check_verification` keep their profile arguments from `main` and this lane's bodies; `stored.py`'s tables become views as `main` has them, with `analysis_spec_node`/`analysis_spec_value`/`governed_node`/`typed_ref`/`local_id` added.

- [ ] **Step 2: Declare the readers.** In the merged base contract's `facets:` section, name `verify.decode_verification` beside `verification`'s readers and `stored.analysis_spec_value` as `analysis-spec`'s reader, in the shape that design's §3.2 fixes; keep the packaged copy byte-identical (its test holds them). Run the full suite and the facet tests.

- [ ] **Step 3: Pin cut 20's arms.** Add `"python/tests/acceptance/n2_arms_cut20.py": "<git log -1 --format=%h -- that path>"` (or `python/tests/n2_arms_cut20.py`, wherever it landed) to `FROZEN_PRIOR_CUT_FILES` and `CUT20_ARMS` to `PRIOR_ARMS` in `test_n2_cut21.py`.

- [ ] **Step 4: Re-run the reproduction driver** into a fresh directory (Task 9 step 5) on the merged tree and keep the 10b JSON.

- [ ] **Step 5: Run the runner on the certified volume**

Run: `uv run --frozen python tools/cut21_acceptance.py` from `python/` → every phase green through the cut 20, 19, 18 and 17 prefixes, ending `declared arms: 17 (= 8 declaration units; 8 guarantee rows)`.

- [ ] **Step 6: The results record** — `docs/plans/2026-09-06-conformance-cut-21-results.md`, by cut 19's record's sections: header (subject, measured against the frozen cut at `41c9920`, digest `eaf2147…`); §1 accounting (8 units, 17 arms, all sound); §2 what ran (the runner's command, its work root, the host tuple, every phase, the driver's 10b JSON quoted); §3 disposition (V1–V8 close; R19's stored-verification limitation closes and its cross-corpus arm stays with `world-resolution`; the `Remaining boundary` section naming `world-resolution`'s rows); §4 what this run does not claim (design §9's limitations); §5 every substitution from the frozen §3 file list, dated.

- [ ] **Step 7: Re-rank.** Run `uv run --frozen python tools/roadmap_status.py` and rewrite the roadmap whole (its rule): `**Ranked at:** cut 21`; tier 1 row 1 leaves; `write-path`'s row reads "no open boundary"; the boundary index drops `verification-publication`; Appendix A gains the `V` row (8 closed) and updates the totals; Appendix C drops R19's row. The ledger's `Current state` heading date and table drop the boundary and restate R19's remainder; its summary names cut 21. README: the design's row reads "V1–V8, closed at cut 21", the cut's row "discharged 2026-09-06", and the results record is listed where cut 19's is.

- [ ] **Step 8: Tests, task, commit, merge**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

```bash
tasks done beliefs-754995 "cut 21 discharged: V1–V8 closed, R19's stored-verification limitation lifted; results record and re-rank landed"
git add -A
git commit -m "docs(verification): discharge conformance cut 21 and re-rank the roadmap"
```

Then the finishing-a-development-branch skill: merge `--no-ff` into `main`, remove the worktree, and confirm the execution ledger (this plan's checkbox state and every ruling made during execution) is committed to a tracked path before the worktree goes.
