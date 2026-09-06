# Verification Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `verification-publication` slice: one spelling for the assessment's run member, a stored verification carrying its whole basis with the comparison report embedded, publication as an ordinary `add`, forgery refused before the intent, scope recomputed by the audit and the import, and the stored `analysis-spec` builder and reader — discharging V1–V8 at conformance cut 21.

**Architecture:** `stored.typed_ref`/`local_id` become the one place a kind prefix is added or removed, and `AssessmentValue.run` is the bare run address on both the derived and the stored side. `verify.publication_node` projects a derived verification to a stamped node under `verification:<identity>` whose facet carries `rule`, `scope_rule`, `report` (the `ComparisonReport` projection) and the typed `derivation`/`supersedes`; `verify.decode_verification` restores a `StoredVerification` through a private mint and refuses an id that does not recompute. `CorpusWriter._refuse` decodes every verification and restores every analysis-spec it prepares, then checks the `verifies` target's identity, before the intent. `audit.check_verification` recomputes through the constructor's own `_derive` helper and compares scope, rule, scope rule and report identity when a report is stored. `spec.restore` rebuilds a `FrozenSpec` from canonical projection text without coercing a member.

**Tech Stack:** Python 3.11+ (`uv run --frozen`), `pydantic` v2 `nodes` documents, `pytest`; the `atoms` certified engine for the durable suite; `science.identity.v1` canonical encoding.

**Spec:** `docs/designs/2026-09-06-verification-publication-design.md` (every task cites its sections) and the frozen cut `docs/designs/2026-09-06-conformance-cut-21.md` (frozen at `41c9920`, digest `eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5`). Read both before any task. The design's §2 decisions 1–18 are the rulings; §8's V rows are the acceptance criteria and their cells are quoted byte-exact in the cut's §3. This plan was reviewed once (2026-09-06, eleven findings); the resolutions are marked **[R1]**–**[R11]** where they land.

## Global Constraints

- From `python/`: `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen pyright` must pass at every commit. Run the Python suite with the project venv, never system python. `addopts` already sets `-q` and ignores `tests/acceptance`; run acceptance modules by path.
- The worktree is `.worktrees/verification-publication` on `feat/verification-publication`; run everything from it. `python/` is the working directory for every `uv run` below unless stated.
- Never edit `tasks/*.md` directly; use the `tasks` CLI. `tasks start <id>` before a task that carries an id, `tasks done <id> "<result>"` in the commit that lands it. Ids: `beliefs-ae9b18` (one spelling, Task 1), `beliefs-f860f1` (the stored report, Task 3), `beliefs-91aac6` (the analysis-spec builder and reader, Task 6), `beliefs-754995` (the boundary, Task 12).
- Conventional commits, no AI-attribution trailer or footer of any kind.
- Fail early, no silent fallbacks: every refusal is raised or reported, never skipped. A malformed member is refused, never repaired or coerced (M11).
- Every new check must be able to fail (N2): each test asserts a refusal or a finding a sabotage in Task 10 turns green. Task 10's arm list is the cut's §5 item 4, sabotage for sabotage.
- The constructor's argument list stays closed (R19): `build_verification` gains no parameter. `admission_record` is untouched. Reading never validates: `decode_verification` is self-consistency, and derivation validation happens at import and under audit only (design §5.3, §6).
- Sealed value types (`AssessmentVerification`, `DatasetProductionVerification`, `ComparisonReport`, `FrozenSpec`, `StoredVerification`) get no public constructor; restoration goes through the module's private mint. **[R3]**
- A raw-write fixture the audit must *recompute* recomputes its semantic stamp first; an unstamped edit is `semantic-hash-stale`, which the audit skips as malformed and exercises nothing.
- The `domain` lane's cut 20 is undischarged on its branch. `tools/cut21_acceptance.py` names `cut20_acceptance.py` as prefix and cannot run end to end until that lane merges (Task 12). Every portable test and the durable module run now.
- No `/home/keith` or `/mnt/ssd/Dropbox` paths in code or docs.
- Sections §2–§7 of the cut document are frozen; a deviation from them is dated in the results record (Task 12 step 6), never edited in. Two are known at plan time and listed there.

---

## File structure

**Created**

| path | responsibility |
|---|---|
| `python/tests/verification_fixtures.py` | the shared builders every V arm uses: a conforming assessment run pair whose replay carries a qualifying confined receipt (`clean-environment` with no engine), the stored records around it, the derived verification, admission over a corpus, the forgeries and the self-consistent forgery **[R4]** |
| `python/tests/test_verification_identity.py` | exists (fails at its first assertion on the freeze tree); Task 1 makes it pass over the shared pair, Task 7 widens it |
| `python/tests/test_verification_publication.py` | V3's arms; imports nothing from `test_evaluation` that imports it back **[R6]** |
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
| `python/src/beliefs/verify.py` | `ComparisonReport.projection()`, `_Derived`/`_derive`, `StoredVerification` and its private mint, `_restore_report`, `decode_verification`, `publication_node` (§4, §5.1, §6) |
| `python/src/beliefs/audit.py` | `check_assessment`'s lookup, `_assessment_disagreements`, `check_verification` widened, `check_analysis_spec`, `stored_specs`, the `analysis-spec` branch (§3.2, §6) |
| `python/src/beliefs/corpus.py` | `_refuse_verification`, `_refuse_r20_contradiction` through `analysis_spec_value`, both called from `_refuse`; the import's separate r20 call removed (§5.3, §7) |
| `python/src/beliefs/errors.py` | `VerificationTargetMismatch(WriteRefused)` (§5.3) |
| `python/src/beliefs/spec.py` | `frozen_projection`, `restore` and its inverse helpers, type-checked without coercion (§7) **[R1]** |
| `python/tests/test_stored.py`, `test_admission.py`, `test_verify.py`, `test_audit.py`, `test_import_derivation.py`, `test_operation_writes.py`, `test_corpus_write.py`, `test_spec.py`, `test_evaluation.py`, `test_reproduction_driver.py` | the portable arms |
| `python/tools/reproduction/spec.py`, `belief.py`, `rederive.py`, `close.py` | steps 4, 8, 10b and the evidence, with 10b a pure function over a view and its evidence **[R9]** |
| `docs/designs/2026-09-06-verification-publication-design.md`, the guide, the ledger, the roadmap, `README.md`, `docs/designs/2026-08-02-computation-reproducibility-design.md`, `2026-08-30-run-confinement-design.md`, `docs/plans/2026-09-04-conformance-cut-18-results.md` | banking and discharge (Tasks 11–12) |

---

### Task 0: The shared fixture module

**Files:**
- Create: `python/tests/verification_fixtures.py`

**Interfaces:**
- Produces: `frozen_for(target) -> FrozenSpec`; `conforming_closure(frozen, *, token, confined=False, outputs=None) -> RunClosure`; `clean_pair(frozen, *, agreeing=True, qualifying=True) -> tuple[RunClosure, RunClosure]`; `evidence_for(frozen) -> DerivationEvidence`; `run_record(closure) -> Node`; `mint_datasets(writer, closure)`; `Published` (dataclass: `frozen, original, replayed, proposition, assessment, derived_value, derived, evidence, node`); `publish_corpus(writer, *, slug="p", claim=None, certification=None, agreeing=True, qualifying=True, publish=False) -> Published`; `observations_for(view)`; `evaluation_kwargs(view) -> dict`; `admission_over(writer, proposition_ref, original)`; `self_consistent_forgery(writer, node, *, mutate) -> Node`; `forgeries(writer, published) -> list[tuple[Node, type[Exception], str]]`. `publish=True`, `self_consistent_forgery` and `forgeries` import Task 2's, 3's and 5's names lazily, so the module loads from Task 0 on.
- Consumes: `fixtures_cut3.closure_with/planned/traced/spec_draft/spec_rules`, `confinement_fixtures.confined_receipt/instance`, `test_evaluation.CLAIM_FACET/EX/GENE/PHENO/OTHER_GENE`, `test_belief.PROFILE`, `fixtures_cut4.raw_write`.

- [ ] **Step 1: Write the module**

```python
"""Shared builders for cut 21's arms (verification-publication design §8).

The run pair is synthetic and conforming — `fixtures_cut3.closure_with` with a
one-job plan — and the replay carries a qualifying confined receipt bound to
the recipe's environment identity, so `derive_scope` reaches
`clean-environment` with no engine (`test_replay.py`'s R4 arms do the same
over real runs). Every V arm that needs admission builds on it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from authority import ACTOR
from confinement_fixtures import confined_receipt, instance
from fixtures_cut3 import closure_with, planned, spec_draft, spec_rules, traced
from fixtures_cut4 import raw_write
from nodes.core.node import Node
from nodes.core.relations import Relation
from test_belief import PROFILE
from test_evaluation import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO

from beliefs import runrecord, stored
from beliefs.admission import admit
from beliefs.assess import build_assessment
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.corpus import lineage_snapshot
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.evaluation import evaluate_over, gather
from beliefs.evidence import DerivationEvidence
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.recipe import RunClosure, job_key
from beliefs.record import AssessmentValue
from beliefs.replay import CONTENT_EQUALITY, CodeLineageCertification
from beliefs.resolution import build_snapshot
from beliefs.runrecord import run_ref
from beliefs.spec import FrozenSpec, freeze
from beliefs.verify import AssessmentVerification, build_verification

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]
CONTRACT = "science:" + "c" * 64
EPOCH = "epoch:" + "e" * 64
BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)
DISAGREEING = (("out.txt", "sha256:" + "d" * 64),)
_PARTS = {
    "trace": (traced("fit", {"n": "a"}),),
    "planned": (planned("fit", ("outputs/a.done",), wildcards=(("n", "a"),)),),
    "target_keys": (job_key("fit", (("n", "a"),)),),
    "targets": ("outputs/a.done",),
}
__all__ = ["CLAIM_FACET", "PROFILE", "EX", "GENE", "OTHER_GENE", "PHENO"]  # re-exported for the acceptance module


def frozen_for(target: str) -> FrozenSpec:
    """The spec's target is the proposition's corpus ref, as the reproduction
    set it: the stored assessment's `proposition` and the derived one then
    spell the same string (design §9 names the two namespaces)."""
    return freeze(spec_draft(target=target), held_rules=spec_rules())


def conforming_closure(frozen: FrozenSpec, *, token: str, confined: bool = False, outputs=None) -> RunClosure:
    base = closure_with(**_PARTS) if outputs is None else closure_with(**_PARTS, outputs=outputs)
    recipe = replace(base.recipe, spec_identity=frozen.identity, rule_bindings=frozen.rule_bindings)
    occurrence = replace(base.occurrence, event_token=token, actor=ACTOR)
    if confined:
        receipt = confined_receipt(instance=instance(environment_identity=recipe.environment.identity()))
        occurrence = replace(occurrence, receipt=receipt)
    return RunClosure(recipe=recipe, result=base.result, occurrence=occurrence)


def clean_pair(frozen: FrozenSpec, *, agreeing: bool = True, qualifying: bool = True) -> tuple[RunClosure, RunClosure]:
    """`qualifying=False` leaves the replay's receipt unconfined: the pair
    then derives `same-environment`, which is what a forged
    `clean-environment` over it must be caught against (V4)."""
    original = conforming_closure(frozen, token="tok-original")
    replayed = conforming_closure(frozen, token="tok-replayed", confined=qualifying, outputs=None if agreeing else DISAGREEING)
    return original, replayed


def evidence_for(frozen: FrozenSpec) -> DerivationEvidence:
    rules = spec_rules()
    interpretation = rules[frozen.interpretation_rule]
    return DerivationEvidence(
        specs={frozen.identity: frozen},
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        implementations={interpretation.identity: interpretation},
    )


def run_record(closure: RunClosure) -> Node:
    return stored.run_publication_node(
        closure.address(),
        title="assessment run",
        projection=runrecord.projection_text(closure).decode("utf-8"),
        spec=closure.recipe.spec_identity,
        observes=tuple(e.dataset for e in closure.recipe.inputs if e.role == "observes"),
        reads=tuple(e.dataset for e in closure.recipe.inputs if e.role == "reads"),
    )


def mint_datasets(writer, closure: RunClosure) -> None:
    for entry in closure.recipe.inputs:
        if not writer.read_view.holds(entry.dataset):
            writer.add(
                stored.dataset_node(
                    entry.dataset.removeprefix("dataset:"), title="raw", resources=PINNED,
                    empirical_observation={"boundary": "instrument"},
                )
            )


@dataclass(frozen=True)
class Published:
    frozen: FrozenSpec
    original: RunClosure
    replayed: RunClosure
    proposition: Node
    assessment: Node
    derived_value: AssessmentValue
    derived: AssessmentVerification
    evidence: DerivationEvidence
    node: Node | None


def publish_corpus(
    writer, *, slug: str = "p", claim=None, certification: CodeLineageCertification | None = None,
    agreeing: bool = True, qualifying: bool = True, publish: bool = False,
) -> Published:
    """A proposition, the two runs and their datasets, the stored assessment
    over the original, the verification derived from the pair, and — with
    `publish` — its record through `writer.add`."""
    proposition = writer.add(stored.proposition_node(slug, title=slug, claim=claim or {"operator": "affects"}))
    frozen = frozen_for(proposition.id)
    original, replayed = clean_pair(frozen, agreeing=agreeing, qualifying=qualifying)
    mint_datasets(writer, original)
    writer.add(run_record(original))
    writer.add(run_record(replayed))
    evidence = evidence_for(frozen)
    derived_value = build_assessment(original, specs=evidence.specs, implementations=evidence.implementations)
    assert isinstance(derived_value, AssessmentValue), derived_value
    optional = {n: getattr(derived_value, n) for n in ("estimate", "uncertainty", "estimand", "applicability") if getattr(derived_value, n) is not None}
    assessment = writer.add(
        stored.assessment_node(
            f"a-{slug}", title=f"a-{slug}", spec=frozen.identity, run=run_ref(original.address()), proposition=proposition.id,
            outcome=derived_value.outcome, interpretation_rule=derived_value.interpretation_rule, **optional,
        )
    )
    derived = build_verification(
        original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
        contract_identity=CONTRACT, epoch=EPOCH, certification=certification,
    )
    assert isinstance(derived, AssessmentVerification)
    node = None
    if publish:
        from beliefs.verify import publication_node

        node = writer.add(publication_node(derived, assessment_ref=assessment.id))
    return Published(frozen, original, replayed, proposition, assessment, derived_value, derived, evidence, node)


def observations_for(view) -> dict[str, tuple[ByteObservation, ...]]:
    """One observation per held dataset at its declared digest, so `admit`
    reads every input as Held."""
    observations: dict[str, tuple[ByteObservation, ...]] = {}
    for node in view.iter_stored():
        if node.kind != "dataset":
            continue
        declaration = stored.dataset_declaration(node)
        address = dataset_address(declaration)
        if address is not None:
            observations[address] = tuple(
                ByteObservation(digest=r.digest, location="repo://data") for r in declaration.resources if r.digest
            )
    return observations


def evaluation_kwargs(view) -> dict:
    identities = {stored.assessment_value(n).identity() for n in view.iter_stored() if n.kind == "assessment"}
    observations = observations_for(view)
    return {
        "availability": Availability(observations=observations, implementations={BELIEF_V1.identity: BELIEF_V1}, fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES}),
        "context": SuppliedContext(
            snapshot=lineage_snapshot(view, [n.id for n in view.iter_stored() if n.kind == "dataset"]),  # corpus refs, not content addresses [R2, second round]
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={identity: "c1" for identity in identities},
            pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
        ),
        "profile": PROFILE,
        "resolution": build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        "binding": BINDING,
    }


def admission_over(writer, proposition_ref: str, original: RunClosure):
    """`gather` -> `admit` -> `evaluate_over` over the corpus as it stands. The
    assessment admitted is *an* assessment over `original`: two records may
    carry one identity (design decision 17) and the gate is over the identity. [R5]"""
    view = writer.read_view
    kwargs = evaluation_kwargs(view)
    gathered = {k: v for k, v in kwargs.items() if k != "availability"}
    inputs = gather(view, proposition_ref, **gathered)
    a = next(a for a in inputs.assessments if a.run == original.address())
    verdict = admit(a, inputs.runs[a.run], kwargs["availability"].observations, inputs.verifications)
    return verdict, evaluate_over(view, proposition_ref, **kwargs)


def self_consistent_forgery(writer, node: Node, *, mutate) -> Node:
    """V4's fixture (design decision 16): alter a member, then recompute the
    id, the relation source and the stamp from the altered members, so the
    record decodes and only the derivation recomputation can catch it. Written
    behind the boundary on purpose. The identity is computed through the
    reader's own basis helper — no constructor is opened for it."""
    from beliefs.verify import RUN_VERIFICATION_DOMAIN, _basis, _restore_report

    facet = {k: (dict(v) if isinstance(v, dict) else v) for k, v in node.facets[stored.VERIFICATION_FACET].items()}
    mutate(facet)
    members: dict[str, object] = {
        "original": stored.local_id("run", facet["derivation"]["original"]),
        "replayed": stored.local_id("run", facet["derivation"]["replayed"]),
        "rule": facet["rule"],
        "report": _restore_report(node.id, facet["report"]),
        "scope_rule": facet["scope_rule"],
        "scope": facet["scope"],
        "verdict": facet["verdict"],
        "supersedes": None if "supersedes" not in facet else stored.local_id("verification", facet["supersedes"]),
    }
    if "assessment" in facet:
        members["assessment"] = facet["assessment"]
    forged_id = f"verification:{v1.digest(RUN_VERIFICATION_DOMAIN, _basis(members))}"
    forged = stored.stamp_semantic_identity(
        Node(
            id=forged_id, kind="verification", title=node.title, facets={stored.VERIFICATION_FACET: facet},
            relations=[Relation(source=forged_id, predicate=r.predicate, target=r.target) for r in node.relations],
        )
    )
    raw_write(writer.root, forged)
    return forged


def forgeries(writer, published: Published) -> list[tuple[Node, type[Exception], str]]:
    """V5's five: a stale id, a forged report, a missing edge, a target that
    resolves nowhere, and a target carrying another identity — each with the
    refusal type and the substring its message carries. The helper records
    they need are minted through `writer` first, so a caller takes its
    baseline after this returns. [R8]"""
    from beliefs.errors import MalformedRecord, VerificationTargetMismatch
    from beliefs.verify import publication_node

    derived, assessment = published.derived, published.assessment
    good = publication_node(derived, assessment_ref=assessment.id)
    stale_id = good.model_copy(update={"id": "verification:" + "f" * 64})
    stale_id.relations = [Relation(source=stale_id.id, predicate=r.predicate, target=r.target) for r in good.relations]
    stored.stamp_semantic_identity(stale_id)
    bad_report = good.model_copy(deep=True)
    bad_report.facets[stored.VERIFICATION_FACET]["report"]["diagnostics"] = ["forged"]
    stored.stamp_semantic_identity(bad_report)
    no_edge = good.model_copy(deep=True, update={"relations": []})
    stored.stamp_semantic_identity(no_edge)
    wrong_target = publication_node(derived, assessment_ref="assessment:absent")
    other_proposition = writer.add(stored.proposition_node("p-other", title="p-other", claim={"operator": "affects"}))
    # Spelled from the same derived value as the real assessment, optionals included,
    # so it audits clean and imports; only its proposition differs, which the audit's
    # comparison excludes (cut 18 ruling R12). Its identity differs by that member.
    value = published.derived_value
    optional = {n: getattr(value, n) for n in ("estimate", "uncertainty", "estimand", "applicability") if getattr(value, n) is not None}
    other = writer.add(
        stored.assessment_node(
            "a-other", title="a-other", spec=published.frozen.identity, run=run_ref(published.original.address()),
            proposition=other_proposition.id, outcome=value.outcome, interpretation_rule=value.interpretation_rule, **optional,
        )
    )
    other_identity = publication_node(derived, assessment_ref=other.id)
    return [
        (stale_id, MalformedRecord, "recomputed identity"),
        (bad_report, MalformedRecord, "recomputed identity"),
        (no_edge, MalformedRecord, "present together"),
        (wrong_target, VerificationTargetMismatch, "resolves to no record"),
        (other_identity, VerificationTargetMismatch, "carries assessment identity"),
    ]
```

- [ ] **Step 2: Probe it**

Run: `PYTHONPATH=tests uv run --frozen python -c "from verification_fixtures import frozen_for, clean_pair; from beliefs.replay import derive_scope, conformance; f = frozen_for('proposition:p'); a, b = clean_pair(f); print(conformance(a), conformance(b), derive_scope(a, b, certification=None))"`
Expected: `conforming conforming clean-environment`.

- [ ] **Step 3: Commit**

```bash
git add python/tests/verification_fixtures.py
git commit -m "test: shared verification fixtures — a conforming pair whose replay qualifies for clean-environment"
```

---

### Task 1: One spelling for the run member (V2) — `beliefs-ae9b18`

**Files:**
- Modify: `python/src/beliefs/stored.py` (after `WORLD_RELATIONS`; `assessment_value` at lines 381–399; `__all__`)
- Modify: `python/src/beliefs/record.py:78-98` (docstring only)
- Modify: `python/src/beliefs/admission.py:54-56`
- Modify: `python/src/beliefs/evaluation.py:174-179`
- Modify: `python/src/beliefs/audit.py:169`, `:191-209`
- Modify: `python/tests/test_verification_identity.py` (the fixture pair) **[R4]**
- Test: `python/tests/test_stored.py`, `python/tests/test_admission.py`, `python/tests/test_verification_identity.py`

**Interfaces:**
- Produces: `stored.typed_ref(kind: str, local: str) -> str`, `stored.local_id(kind: str, ref: str) -> str`; `AssessmentValue.run` is the bare address from `stored.assessment_value`.

- [ ] **Step 1: `tasks start beliefs-ae9b18`** (from the worktree root).

- [ ] **Step 2: Rebuild the identity test over the shared pair** — the assertions stay (cut §5 item 8); the construction moves to Task 0's builders, whose replay qualifies for `clean-environment`. Replace everything from `def test_v2_…(writer):` down to (not including) `stored_node = writer.add(` with:

```python
def test_v2_one_identity_admits_over_the_corpus_and_audits_clean(writer):
    published = publish_corpus(writer, claim=CLAIM_FACET)
    original, replayed, assessment = published.original, published.replayed, published.assessment
    derived, verification, evidence = published.derived_value, published.derived, published.evidence
    record = admission_record(verification)
```

(`replayed` stays bound: the retained publication block spells `run_ref(replayed.address())`.) With `from test_evaluation import CLAIM_FACET` and `from verification_fixtures import publish_corpus` at the top and the now-unused imports (`test_audit`'s helpers, `freeze`, `spec_draft`, `spec_rules`, `build_assessment`, `AssessmentValue`, `build_verification`) removed. The `stored.verification_node(...)` publication and every assertion stay as they are.

Run: `uv run --frozen pytest tests/test_verification_identity.py -p no:cacheprovider`
Expected: still FAIL at the first assertion, the two identities differing on `run` only (the proposition member now agrees, since `frozen_for` targets the ref).

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
Expected: FAIL — `ImportError: cannot import name 'local_id'`, and the admission test's second assertion (`admit` compares the typed ref to the bare member and reports `run-mismatch` for `run:r1` too).

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

`admission.py`: add `from beliefs.stored import typed_ref` and replace `    if run.ref != assessment.run:` with `    if run.ref != typed_ref("run", assessment.run):`.

`evaluation.py`, in `gather`, replace the run loop's head:

```python
    for a in matched:
        ref = stored.typed_ref("run", a.run)
        if a.run in runs or not view.holds(ref):
            continue
        runs[a.run] = run_value(view, ref)
        trace.append(("run", a.run))
```

(`runs` stays keyed by the value's bare `a.run`; the trace row and `declared_refs` both spell it that way.)

`audit.py`: in `check_assessment` replace `closure, why = _closure(view, stored_value.run)` with `closure, why = _closure(view, stored.typed_ref("run", stored_value.run))`; in `_assessment_disagreements` replace `if stored_value.run != run_ref(derived.run):` with `if stored_value.run != derived.run:`, delete the docstring sentence beginning "`run` is normalized first" and the module docstring's clause "after `run` is normalized from a bare closure address to its typed stored reference" (replace with "both spelled bare"), and drop `run_ref` from the `runrecord` import if it is now unused.

`record.py`: under `run: str` add `"""The run's bare closure address — its world identity — on the derived and the stored side alike (verification-publication design §3)."""`.

- [ ] **Step 7: Fix the fixtures that spelled a stored run bare**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -30` and fix every failure that is a `MalformedRecord` from `assessment_value` or a `run-mismatch`: a fixture assessment whose `run=` is not `run:`-prefixed gets the prefix; a test asserting `assessment_value(node).run == "run:…"` asserts the bare form; a test building `RunValue(ref=…)` keeps the typed ref. Do not weaken any assertion; every edit is a spelling.

- [ ] **Step 8: Run the suite and the identity test**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3` → all pass.
Run: `uv run --frozen pytest tests/test_verification_identity.py -p no:cacheprovider` → PASS, the `ADMITTED` assertion included (the shared pair's scope is `clean-environment`).
Run: `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 9: Commit**

```bash
tasks done beliefs-ae9b18 "typed_ref/local_id in stored; AssessmentValue.run bare on both sides; admit, gather and check_assessment resolve through the typed ref; test_verification_identity passes over a clean-environment pair"
git add -A python tasks
git commit -m "feat(stored): one spelling for the assessment's run member (V2)"
```

---

### Task 2: The stored verification's reader (V1's round trip, V6's malformed report)

**Files:**
- Modify: `python/src/beliefs/verify.py` (`ComparisonReport`, `StoredVerification` and its mint, `_restore_report`, `decode_verification`, `__all__`)
- Test: `python/tests/test_verify.py`

**Interfaces:**
- Produces: `ComparisonReport.projection() -> dict[str, object]`; `class StoredVerification` (closed constructor) with members `original, replayed, assessment, rule, report, scope_rule, scope, verdict, supersedes`, `basis()`, `identity()`; `verify._mint_stored_verification(*, assessment, **members)`; `verify._restore_report(node_id, member) -> ComparisonReport`; `decode_verification(node: Node) -> StoredVerification | None`.
- Consumes: `stored.local_id`, `stored.verification_derivation`, `stored.VERIFICATION_FACET`, `stored.VERIFIES`.

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


def test_v3_stored_verification_has_no_public_constructor():
    with pytest.raises(TypeError):
        StoredVerification(original="a", replayed="b", assessment=None, rule="r", report=None, scope_rule="s", scope="bogus", verdict="bogus", supersedes=None)  # type: ignore[call-arg]


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
        lambda f: f.__setitem__("derivation", None),
        lambda f: f.pop("derivation"),
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

(`pair`, `verification_of`, `v1`, `COMPARISON_REPORT_DOMAIN`, `pytest`, `AssessmentVerification` are already imported or defined in `test_verify.py`; add any that are not.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_verify.py -k "v1 or v3 or v5 or v6 or v7" -p no:cacheprovider`
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
@dataclass(frozen=True, init=False)
class StoredVerification:
    """A published verification read back: the same basis as the derived
    value, minted only by `decode_verification` after the record's id
    recomputes from its members (design §4.2). Distinct from the derived
    types on purpose — R19 admits no constructor that accepts a report — and
    closed the same way they are."""

    original: str
    replayed: str
    assessment: str | None
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("StoredVerification values are minted only by decode_verification")

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


def _mint_stored_verification(*, assessment: str | None, **members: object) -> StoredVerification:
    """The reader's private mint: `_validate_verification` over the same
    member set the derived mint validates, then the sealed value."""
    checked: dict[str, object] = dict(members)
    if assessment is not None:
        checked["assessment"] = assessment
    _validate_verification(checked)
    value = object.__new__(StoredVerification)
    for name, member in (*members.items(), ("assessment", assessment)):
        object.__setattr__(value, name, member)
    return value


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
    present member that is malformed — a null derivation included — or an id
    that does not recompute from the members is refused, never repaired
    (M11). Pure over the node."""
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
    if facet["derivation"] is None:
        raise MalformedRecord(f"{node.id}: a published verification names its derivation")
    derivation = stored.verification_derivation(node)
    if derivation is None:
        raise MalformedRecord(f"{node.id}: a published verification names its derivation")
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
    decoded = _mint_stored_verification(
        assessment=assessment,
        original=stored.local_id("run", derivation[0]),
        replayed=stored.local_id("run", derivation[1]),
        rule=facet["rule"],
        report=_restore_report(node.id, facet["report"]),
        scope_rule=facet["scope_rule"],
        scope=facet["scope"],
        verdict=facet["verdict"],
        supersedes=supersedes,
    )
    if decoded.identity() != stored.local_id("verification", node.id):
        raise MalformedRecord(f"{node.id}: the recomputed identity is not the record id")
    return decoded
```

Imports to add at the top of `verify.py`: `from nodes.core.node import Node`, `from beliefs import stored`. Add `"StoredVerification"` and `"decode_verification"` to `__all__`. **[R2]** the null-derivation branch; **[R3]** the closed constructor.

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
- Produces: `stored.governed_node(kind, local, title, facets, relations) -> Node`; `verify.publication_node(derived: RunVerification, *, assessment_ref: str | None = None) -> Node`; `publish_corpus(..., publish=True)` now works.

- [ ] **Step 1: `tasks start beliefs-f860f1`**

- [ ] **Step 2: Write the failing tests** — append to `tests/test_verify.py`:

```python
# --- V1 / V3 / V7: the publication projection (design §5.1) --------------------
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


def test_v3_a_superseding_verification_publishes_its_typed_predecessor(pair):
    verification = verification_of(pair)
    successor = _mint_verification(
        original=verification.original, replayed=verification.replayed, assessment=verification.assessment,
        rule=verification.rule, report=verification.report, scope_rule=verification.scope_rule,
        scope=verification.scope, verdict="failed", supersedes=verification.identity(),
    )
    node = publication_node(successor, assessment_ref="assessment:a")
    assert node.facets[stored.VERIFICATION_FACET]["supersedes"] == f"verification:{verification.identity()}"
    decoded = decode_verification(node)
    assert decoded is not None and decoded.supersedes == verification.identity()


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

- [ ] **Step 3: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_verify.py -k "publication or v7 or superseding" -p no:cacheprovider`
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

### Task 4: The audit recomputes scope through the constructor's own derivation (V4, V6, V2's contradicted assessment)

**Files:**
- Modify: `python/src/beliefs/verify.py` (`_Derived`, `_derive`, `build_verification`)
- Modify: `python/src/beliefs/audit.py:113-162` (`check_verification`)
- Test: `python/tests/test_audit.py`

**Interfaces:**
- Produces: `verify._derive(original, replayed, *, specs, held_rules, certification, citation) -> _Derived` with members `rule, implementation_identity, report, scope, verdict, assessment`; `test_audit.V4_FORGERIES`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_audit.py`:

```python
# --- V4 / V6 / V2: scope, rule, scope rule and report are recomputed (design §6) ---
from fixtures_cut4 import reopen
from nodes.core.node import Node
from verification_fixtures import publish_corpus, self_consistent_forgery

from beliefs.audit import audit_corpus, check_verification
from beliefs.replay import CodeLineageCertification

CERTIFIED = CodeLineageCertification(rationale="independent reimplementation", attribution="second team")
DERIVATION_CODES = {"verification-derivation-contradicted", "assessment-derivation-contradicted", "derivation-malformed"}


def _findings(writer, evidence, code="verification-derivation-contradicted"):
    return [f for f in audit_corpus(reopen(writer.root), evidence=evidence) if f.code == code]


def test_v4_a_published_verification_audits_checked_with_no_contradiction(writer):
    published = publish_corpus(writer, publish=True)
    outcome = check_verification(writer.read_view, writer.read_view.get(published.node.id), evidence=published.evidence)
    assert outcome.checked and outcome.contradiction is None
    assert not {f.code for f in audit_corpus(reopen(writer.root), evidence=published.evidence)} & DERIVATION_CODES


def test_v4_a_certified_verification_audits_clean_through_its_stored_certification(writer):
    """The recomputation takes the certification from the stored report (decision 7): drop it and the report identity moves. [R10]"""
    published = publish_corpus(writer, publish=True, certification=CERTIFIED)
    assert published.derived.report.certification == CERTIFIED
    assert not _findings(writer, published.evidence)


# (member named in the finding, the mutation, the corpus it is forged over). The
# scope case is the frozen cell's escalation: `clean-environment` asserted over a
# replay that does not qualify, so the honest derivation is `same-environment`.
V4_FORGERIES = [
    ("scope", lambda f: f.__setitem__("scope", "clean-environment"), {"qualifying": False}),
    ("verdict", lambda f: f.__setitem__("verdict", "failed"), {}),
    ("report", lambda f: f["report"].__setitem__("receipts", ["sha256:" + "0" * 64, f["report"]["receipts"][1]]), {}),
    ("report", lambda f: f["report"].__setitem__("original_conformance", "non-conforming: forged"), {}),
    ("rule", lambda f: f.__setitem__("rule", "some-other-rule/v1"), {}),
    ("scope_rule", lambda f: f.__setitem__("scope_rule", "scope-derivation/v9"), {}),
]
V4_IDS = ["scope", "verdict", "report-receipt", "report-conformance", "rule", "scope_rule"]


@pytest.mark.parametrize("member, mutate, corpus", V4_FORGERIES, ids=V4_IDS)
def test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member(writer, member, mutate, corpus):
    published = publish_corpus(writer, publish=True, **corpus)
    if member == "scope":
        assert published.derived.scope == "same-environment"  # the honest reading the forgery escalates
    forged = self_consistent_forgery(writer, published.node, mutate=mutate)
    findings = _findings(writer, published.evidence)
    assert [f.ref for f in findings] == [forged.id] and member in findings[0].detail
    assert not _findings(writer, published.evidence, code="derivation-malformed")


def test_v6_a_report_less_verification_is_checked_for_verdict_and_identity_only(writer):
    published = publish_corpus(writer, publish=True)
    facet = dict(published.node.facets[stored.VERIFICATION_FACET])
    del facet["report"], facet["rule"], facet["scope_rule"]
    facet["scope"] = "same-environment"  # a lowered scope a report-less record cannot be caught on (cut 18 §7)
    legacy = stored.stamp_semantic_identity(
        Node(id="verification:legacy", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, legacy)
    view = reopen(writer.root)
    outcome = check_verification(view, view.get(legacy.id), evidence=published.evidence)
    assert outcome.checked and outcome.contradiction is None
    facet["verdict"] = "failed"
    flipped = stored.stamp_semantic_identity(
        Node(id="verification:legacy-flipped", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, flipped)
    view = reopen(writer.root)
    outcome = check_verification(view, view.get(flipped.id), evidence=published.evidence)
    assert outcome.contradiction is not None and "verdict" in outcome.contradiction.detail


def test_v2_a_contradicted_assessment_still_contradicts(writer, tmp_path):
    """Decision 13: the assessment audit resolves the bare run through the typed ref."""
    published = publish_corpus(writer, publish=True)
    altered = published.assessment.model_copy(deep=True)
    altered.facets[stored.ASSESSMENT_FACET]["outcome"] = "refuted"
    stored.stamp_semantic_identity(altered)
    raw_write(writer.root, altered)
    codes = {f.code for f in audit_corpus(reopen(writer.root), evidence=published.evidence)}
    assert "assessment-derivation-contradicted" in codes and "semantic-hash-stale" not in codes
    from test_relocation import _writer

    from beliefs.errors import ImportRefused

    target = _writer(tmp_path / "target")
    members = tuple(n for n in reopen(writer.root).iter_stored() if n.kind in {"dataset", "run", "proposition"}) + (altered,)
    with pytest.raises(ImportRefused):
        target.import_bundle(members, evidence=published.evidence, observer="o", instrument="i", opened_at="2026-09-06T00:00:00Z", closed_at="2026-09-06T00:00:01Z")
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_audit.py -k "v4 or v6 or contradicted_assessment" -p no:cacheprovider`
Expected: the `scope` (an escalation to `clean-environment` over a non-qualifying replay), `report-*`, `rule` and `scope_rule` cases FAIL (no contradiction found); the `verdict` case, V6, the certified case and the contradicted-assessment case pass already.

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
    scope = derive_scope(original, replayed, certification=certification)
    return _Derived(rule, implementation_identity, report, scope, verdict, assessment)
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

- [ ] **Step 4: Widen `check_verification` in `audit.py`** — replace its body from `derivation = ...` to the `disagreements` construction with:

```python
    decoded = decode_verification(node)  # MalformedRecord propagates: a present, malformed report is refused, never repaired
    derivation = stored.verification_derivation(node)
    if derivation is None:
        return _unchecked("no derivation member")
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

**[R2]** the decode precedes the unchecked return. Keep the existing tail. Replace `from beliefs.verify import _resolve_rule` with `from beliefs.verify import _derive, decode_verification`; drop now-unused imports (`ASSESSMENT_DOMAIN`, `v1`, `VERDICTS`) if nothing else uses them. Docstring: "Recompute a stored verification's derivation from the two runs it names — verdict and assessment identity always; rule, scope rule, scope and report identity when the record carries its report (design §6)."

- [ ] **Step 5: Run to verify they pass, then the suite**

Run: `uv run --frozen pytest tests/test_audit.py tests/test_verify.py tests/test_import_derivation.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 6: Commit**

```bash
git add -A python
git commit -m "feat(audit): recompute scope, rule, scope rule and report over a stored verification through the constructor's derivation (V4, V6)"
```

---

### Task 5: Forgery refused before the intent (V5; V6's and V4's import arms)

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `ValidationRefused`, line 1087)
- Modify: `python/src/beliefs/corpus.py:2265-2281` (`_refuse`), new `_refuse_verification`
- Test: `python/tests/test_operation_writes.py`, `python/tests/test_import_derivation.py`

**Interfaces:**
- Produces: `errors.VerificationTargetMismatch(WriteRefused)`; `CorpusWriter._refuse_verification(node, *, view)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_operation_writes.py`:

```python
# --- V5: forgery is refused before the intent (design §5.3) ------------------
from verification_fixtures import forgeries, publish_corpus

from beliefs.verify import publication_node


def test_v5_each_forgery_is_refused_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    published = publish_corpus(writer)
    cases = forgeries(writer, published)
    port.calls.clear()
    for node, refusal, reason in cases:
        with pytest.raises(refusal, match=reason):
            writer.operations.add(node)
        assert not [c for c in port.calls if c[0] == "append_intent"], node.id
        assert writer.read_view.resolve(node.id) is None
    commit = writer.operations.add(publication_node(published.derived, assessment_ref=published.assessment.id))
    assert commit.record is not None and primitive_calls(port)[-3:] == ["preflight", "append_intent", "execute_fulfilling"]
```

Append to `tests/test_import_derivation.py`:

```python
# --- V4 / V5 / V6 at the import boundary (design §5.4) ------------------------
from test_audit import V4_FORGERIES, V4_IDS
from verification_fixtures import forgeries, publish_corpus, self_consistent_forgery


def _bundle_around(source, published, *extra):
    """Every dataset, proposition, assessment and the two runs the source holds,
    plus `extra` — so a target that carries another identity *resolves* in the
    destination's union view and is refused for the identity, not for absence."""
    view = source.read_view
    runs = [view.get(stored.typed_ref("run", published.derived.original)), view.get(stored.typed_ref("run", published.derived.replayed))]
    others = [n for n in view.iter_stored() if n.kind in {"dataset", "proposition", "assessment"}]
    return (*others, *runs, *extra)


@pytest.mark.parametrize("member, mutate, corpus", V4_FORGERIES, ids=V4_IDS)
def test_v4_every_self_consistent_forgery_refuses_the_bundle_before_any_write(tmp_path, member, mutate, corpus):
    source = _writer(tmp_path / "source")
    published = publish_corpus(source, publish=True, **corpus)
    forged = self_consistent_forgery(source, published.node, mutate=mutate)
    target = _writer(tmp_path / "target")
    with pytest.raises(ImportRefused, match=member):
        target.import_bundle(_bundle_around(source, published, forged), evidence=published.evidence, **IMPORT_FIELDS)
    assert not path_for(target.root, forged.id).exists() and not path_for(target.root, published.assessment.id).exists()


def test_v5_every_forgery_refuses_the_bundle_and_the_well_formed_record_imports(tmp_path):
    source = _writer(tmp_path / "source")
    published = publish_corpus(source, publish=True)
    for index, (node, _refusal, reason) in enumerate(forgeries(source, published)):
        target = _writer(tmp_path / f"target-{index}")
        with pytest.raises(ImportRefused, match=reason):
            target.import_bundle(_bundle_around(source, published, node), evidence=published.evidence, **IMPORT_FIELDS)
        assert not path_for(target.root, node.id).exists()
    target = _writer(tmp_path / "target-good")
    # The target assessment is in the bundle and not in the corpus: the union view resolves it (the import-union arm).
    report = target.import_bundle(_bundle_around(source, published, source.read_view.get(published.node.id)), evidence=published.evidence, **IMPORT_FIELDS)
    assert not [f for f in _report_findings(report) if f.startswith("derivation-unchecked")]
    assert path_for(target.root, published.node.id).exists()


def test_v6_a_report_less_verification_imports_on_cut_18s_terms(tmp_path):
    source = _writer(tmp_path / "source")
    published = publish_corpus(source)
    legacy = _stored_from(published.derived, slug="legacy")
    contradicting = _stored_from(published.derived, slug="flipped", verdict=_flip(published.derived.verdict))
    derivation_less = stored.verification_node(
        "bare", title="bare", assessment=published.derived.assessment, assessment_ref=ASSESSMENT_REF,
        scope=published.derived.scope, verdict=published.derived.verdict,
    )
    target = _writer(tmp_path / "target")
    report = target.import_bundle((derivation_less,), evidence=published.evidence, **IMPORT_FIELDS)
    assert any(f.startswith("derivation-unchecked: verification:bare") for f in _report_findings(report))
    report = target.import_bundle((legacy,), evidence=published.evidence, **IMPORT_FIELDS)
    assert any(f.startswith("derivation-unchecked: verification:legacy") for f in _report_findings(report))  # its runs are not in the bundle
    with pytest.raises(ImportRefused):
        target.import_bundle(_bundle_around(source, published, contradicting), evidence=published.evidence, **IMPORT_FIELDS)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_operation_writes.py tests/test_import_derivation.py -k "v4 or v5 or v6" -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'VerificationTargetMismatch'` (raised from `verification_fixtures.forgeries`).

- [ ] **Step 3: Add the refusal class** — `errors.py`, after `ValidationRefused`:

```python
class VerificationTargetMismatch(WriteRefused):
    """A published verification's `verifies` edge does not resolve to an
    assessment carrying the identity the verification names — before the
    intent, at `add` and at import (verification-publication design §5.3).
    Equality of identity is the whole requirement: a second assessment record
    with the same identity is an equally valid target (decision 17)."""
```

- [ ] **Step 4: Add the preflight step** — `corpus.py`, in `_refuse`, between the `_refuse_invalid` block and `self._refuse_governed_stamp(node)`:

```python
        if node.kind == "verification":
            self._refuse_verification(node, view=self._view if view is None else view)
```

and after `_refuse_governed_stamp`:

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

Import `VerificationTargetMismatch` from `beliefs.errors` in `corpus.py`. `self._view` is the writer's read view, the one `_validated_import_bundle` wraps in `_ImportView`.

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
- Modify: `python/src/beliefs/spec.py` (`frozen_projection`, `restore`, the inverse helpers; `__all__`)
- Modify: `python/src/beliefs/stored.py` (`ANALYSIS_SPEC_FACET`, `analysis_spec_node`, `analysis_spec_value`; `__all__`)
- Modify: `python/src/beliefs/corpus.py` (`_refuse_r20_contradiction` at 2099–2112, `_refuse`, `_validated_import_bundle`)
- Modify: `python/src/beliefs/audit.py` (`check_analysis_spec`, `stored_specs`, the dispatch)
- Test: `python/tests/test_spec.py`, `python/tests/test_stored.py`, `python/tests/test_audit.py`, `python/tests/test_import_derivation.py`, `python/tests/test_corpus_write.py`

**Interfaces:**
- Produces: `spec.frozen_projection(spec) -> dict[str, object]`; `spec.restore(identity: str, projection: bytes) -> FrozenSpec`; `stored.ANALYSIS_SPEC_FACET`; `stored.analysis_spec_node(spec) -> Node`; `stored.analysis_spec_value(node) -> FrozenSpec`; `audit.check_analysis_spec(node) -> DerivationOutcome`; `audit.stored_specs(view) -> tuple[Mapping[str, FrozenSpec], tuple[Finding, ...]]`; `test_audit._false_spec_record(spec) -> Node`.

- [ ] **Step 1: `tasks start beliefs-91aac6`**

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_spec.py`:

```python
# --- V8: restore from canonical projection text, no coercion (design §7) -----
from decimal import Decimal

import pytest
from fixtures_cut3 import spec_draft, spec_rules

from beliefs.errors import MalformedRecord, UnfreezableSpec
from beliefs.identity import v1
from beliefs.spec import (
    SPEC_DOMAIN,
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


def _identified(mapping) -> tuple[str, bytes]:
    return v1.digest(SPEC_DOMAIN, mapping), v1.encode(mapping)


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


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda m: m.__setitem__("target", 7),
        lambda m: m.__setitem__("target", ""),
        lambda m: m.__setitem__("parameters", ["not", "a", "mapping"]),
        lambda m: m["nondeterminism"]["plan"]["roots"].__setitem__("model-initialization", Decimal("7.5")),
        lambda m: m["nondeterminism"]["plan"]["roots"].__setitem__("model-initialization", True),
        lambda m: m["input_roles"][0].__setitem__("role", 1),
        lambda m: m.__setitem__("rule_bindings", [["only-one"]]),
        lambda m: m.__setitem__("supersedes", 5),
    ],
)
def test_v8_restore_refuses_a_member_of_the_wrong_type_even_under_its_own_identity(corrupt):
    """[R1] The digest agrees with the text by construction; the members are
    still typed and never coerced, and `freeze`'s invariants hold."""
    mapping = frozen_projection(_rich_spec())
    corrupt(mapping)
    identity, text = _identified(mapping)
    with pytest.raises(MalformedRecord):
        restore(identity, text)


def test_v8_restore_refuses_a_projection_the_restored_spec_would_not_reproduce():
    """[R1, second round] `SeedPlan.projection()` sorts its streams; a text
    with them unsorted is canonical, digests to its own identity, and would
    restore to a spec whose projection digests to another."""
    mapping = frozen_projection(_rich_spec())
    plan = mapping["nondeterminism"]["plan"]
    plan["streams"] = ["b-stream", "a-stream"]
    plan["stream_roots"] = {"a-stream": "r", "b-stream": "r"}
    plan["roots"] = {"r": 7}
    identity, text = _identified(mapping)
    with pytest.raises(MalformedRecord, match="own projection"):
        restore(identity, text)


def test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair():
    spec = _rich_spec()
    text = v1.encode(frozen_projection(spec))
    with pytest.raises(MalformedRecord):
        restore(spec.identity, text + b"\n")
    with pytest.raises(MalformedRecord):
        restore(spec.identity, b"{}")
    mapping = {**frozen_projection(freeze(spec_draft(), held_rules=spec_rules())), "nondeterminism": StochasticUnseeded(rationale="urandom").projection()}
    identity, text = _identified(mapping)
    with pytest.raises(UnfreezableSpec):
        restore(identity, text)
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
from beliefs.evidence import NO_EVIDENCE
from beliefs.spec import freeze


def _false_spec_record(spec):
    forged = stored.analysis_spec_node(spec).model_copy(update={"id": "analysis-spec:forged"})
    forged.facets[stored.ANALYSIS_SPEC_FACET]["identity"] = "forged"
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    return stored.stamp_semantic_identity(forged)


def test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it(writer):
    spec = freeze(spec_draft(), held_rules=spec_rules())
    good = writer.add(stored.analysis_spec_node(spec))
    forged = _false_spec_record(spec)
    raw_write(writer.root, forged)
    view = reopen(writer.root)
    assert check_analysis_spec(view.get(good.id)).checked
    with pytest.raises(MalformedRecord):
        check_analysis_spec(view.get(forged.id))
    specs, findings = stored_specs(view)
    assert set(specs) == {spec.identity} and [f.ref for f in findings] == [forged.id] and findings[0].code == "derivation-malformed"
    assert [f.ref for f in audit_corpus(view, evidence=NO_EVIDENCE) if f.code == "derivation-malformed"] == [forged.id]


def test_v4_the_audit_reaches_the_same_verdict_with_specs_restored_from_the_corpus(writer):
    published = publish_corpus(writer, publish=True)
    writer.add(stored.analysis_spec_node(published.frozen))
    specs, findings = stored_specs(writer.read_view)
    assert not findings and set(specs) == {published.frozen.identity}
    from dataclasses import replace

    from_corpus = replace(published.evidence, specs=specs)
    outcome = check_verification(writer.read_view, writer.read_view.get(published.node.id), evidence=from_corpus)
    assert outcome.checked and outcome.contradiction is None
```

Append to `tests/test_import_derivation.py` and `tests/test_corpus_write.py` respectively:

```python
def test_v8_a_spec_record_whose_identity_is_false_refuses_the_bundle(tmp_path):
    from test_audit import _false_spec_record

    from beliefs.evidence import NO_EVIDENCE
    from beliefs.spec import freeze

    forged = _false_spec_record(freeze(spec_draft(), held_rules=spec_rules()))
    target = _writer(tmp_path / "target")
    with pytest.raises(ImportRefused):
        target.import_bundle((forged,), evidence=NO_EVIDENCE, **IMPORT_FIELDS)
    assert not path_for(target.root, forged.id).exists()
```

```python
def test_v8_a_spec_record_whose_identity_is_false_is_refused_at_add(tmp_path):
    from fixtures_cut3 import spec_draft, spec_rules
    from test_audit import _false_spec_record
    from test_relocation import _writer

    from beliefs.errors import MalformedRecord
    from beliefs.spec import freeze

    writer = _writer(tmp_path / "corpus")
    with pytest.raises(MalformedRecord):
        writer.add(_false_spec_record(freeze(spec_draft(), held_rules=spec_rules())))
    assert writer.read_view.resolve("analysis-spec:forged") is None
```

- [ ] **Step 3: Run to verify they fail**

Run: `uv run --frozen pytest tests/test_spec.py tests/test_stored.py tests/test_audit.py tests/test_import_derivation.py tests/test_corpus_write.py -k v8 -p no:cacheprovider`
Expected: FAIL — `ImportError: cannot import name 'frozen_projection'`.

- [ ] **Step 4: Add `frozen_projection` and `restore` to `spec.py`** after `freeze` **[R1]**:

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
_TEXT_MEMBERS = ("target", "estimand", "method", "assumptions", "falsification", "applicability", "interpretation_rule", "equivalence_rule")


def _text(mapping: Mapping[str, object], name: str, where: str) -> str:
    value = mapping[name]
    if type(value) is not str:
        raise MalformedRecord(f"{where}: {name} is a string")
    return value


def _restore_input(entry: object, where: str) -> SpecInput:
    if not isinstance(entry, dict) or not {"role", "dataset"} <= set(entry) <= {"role", "dataset", "exclusion"}:
        raise MalformedRecord(f"{where}: a spec input names role and dataset, with an optional exclusion")
    exclusion = None
    if "exclusion" in entry:
        claim = entry["exclusion"]
        if not isinstance(claim, dict) or set(claim) != {"rationale", "attribution"}:
            raise MalformedRecord(f"{where}: an exclusion names exactly rationale and attribution")
        exclusion = ExclusionCertification(rationale=_text(claim, "rationale", where), attribution=_text(claim, "attribution", where))
    return SpecInput(role=_text(entry, "role", where), dataset=_text(entry, "dataset", where), exclusion=exclusion)


def _restore_nondeterminism(value: object, where: str) -> NondeterminismContract:
    if not isinstance(value, dict) or type(value.get("variant")) is not str:
        raise MalformedRecord(f"{where}: a nondeterminism member names its variant")
    variant = value["variant"]
    if variant == "deterministic" and set(value) == {"variant"}:
        return Deterministic()
    if variant == "stochastic-unseeded" and set(value) == {"variant", "rationale"}:
        return StochasticUnseeded(rationale=_text(value, "rationale", where))
    if variant == "seeded" and set(value) == {"variant", "plan"}:
        plan = value["plan"]
        if not isinstance(plan, dict) or set(plan) != {"derivation_rule", "streams", "roots", "stream_roots"}:
            raise MalformedRecord(f"{where}: a seed plan names derivation_rule, streams, roots and stream_roots")
        streams, roots, stream_roots = plan["streams"], plan["roots"], plan["stream_roots"]
        if not isinstance(streams, list) or any(type(s) is not str for s in streams):
            raise MalformedRecord(f"{where}: seed plan streams are strings")
        if not isinstance(roots, dict) or any(type(k) is not str or type(v) is not int for k, v in roots.items()):
            raise MalformedRecord(f"{where}: seed plan roots map stream keys to integers")
        if not isinstance(stream_roots, dict) or any(type(k) is not str or type(v) is not str for k, v in stream_roots.items()):
            raise MalformedRecord(f"{where}: seed plan stream roots map strings to strings")
        return Seeded(plan=SeedPlan(derivation_rule=_text(plan, "derivation_rule", where), streams=tuple(streams), roots=dict(roots), stream_roots=dict(stream_roots)))
    raise MalformedRecord(f"{where}: nondeterminism variant {variant!r} is not one of the three")


def restore(identity: str, projection: bytes) -> FrozenSpec:
    """The third mint: a frozen spec from its stored canonical projection
    (design §7). Refuses text that is not canonical, a mapping that is not
    exactly the frozen members, a digest that is not `identity`, any member of
    the wrong type — nothing is coerced — and the pair `freeze` refuses, so a
    stored spec is exactly one `freeze` produced."""
    where = f"analysis-spec {identity[:12]}"
    try:
        mapping = v1.decode(projection)
    except CanonicalTextRefused as refused:
        raise MalformedRecord(f"{where}: the projection is not canonical text: {refused}") from refused
    if not isinstance(mapping, dict) or not _FROZEN_MEMBERS <= set(mapping) <= _FROZEN_MEMBERS | {"supersedes"}:
        raise MalformedRecord(f"{where}: the projection carries exactly the frozen members")
    if v1.digest(SPEC_DOMAIN, mapping) != identity:
        raise MalformedRecord(f"{where}: the projection does not digest to the identity")
    text = {name: _text(mapping, name, where) for name in _TEXT_MEMBERS}
    if not text["target"]:
        raise MalformedRecord(f"{where}: an assessment spec targets a proposition; an empty target is not a spec (R7)")
    if not isinstance(mapping["input_roles"], list):
        raise MalformedRecord(f"{where}: input_roles is a list")
    if not isinstance(mapping["parameters"], dict) or any(type(k) is not str for k in mapping["parameters"]):
        raise MalformedRecord(f"{where}: parameters is a mapping with string keys")
    bindings = mapping["rule_bindings"]
    if not isinstance(bindings, list) or any(
        not isinstance(pair, list) or len(pair) != 2 or any(type(half) is not str for half in pair) for pair in bindings
    ):
        raise MalformedRecord(f"{where}: rule bindings are string pairs")
    nondeterminism = _restore_nondeterminism(mapping["nondeterminism"], where)
    if isinstance(nondeterminism, StochasticUnseeded) and text["equivalence_rule"] in BITWISE_EQUIVALENCE_RULES:
        raise UnfreezableSpec("stochastic-unseeded cannot support a bitwise equivalence rule (computation §3.1a)")
    supersedes = mapping.get("supersedes")
    if supersedes is not None and type(supersedes) is not str:
        raise MalformedRecord(f"{where}: supersedes is a string")
    spec = _mint_frozen_spec(
        **text,
        input_roles=tuple(_restore_input(entry, where) for entry in mapping["input_roles"]),
        parameters=_freeze_parameter_value(mapping["parameters"]),
        nondeterminism=nondeterminism,
        rule_bindings=tuple((pair[0], pair[1]) for pair in bindings),
        supersedes=supersedes,
        identity=identity,
    )
    if v1.encode(frozen_projection(spec)) != projection:
        # A member the value canonicalizes (a seed plan sorts its streams) can be
        # spelled otherwise in canonical text and still digest to `identity`; the
        # restored spec would then project to other bytes and another digest.
        raise MalformedRecord(f"{where}: the projection is not the restored spec's own projection")
    return spec
```

Import `CanonicalTextRefused` from `beliefs.errors` and `Mapping` from `collections.abc`. Add `"frozen_projection"` and `"restore"` to `__all__`. Widen `FrozenSpec.__init__`'s message to "FrozenSpec values are minted by freeze, revise or restore". Read `FrozenSpec.__post_init__` (spec.py ~300): if it re-freezes `parameters` itself, pass the decoded mapping as is.

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

Add both to `__all__`. `spec.py` imports `errors`, `identity`, `sealed` only, so the graph stays acyclic.

- [ ] **Step 6: Route the preflight and the r20 check through the reader** — `corpus.py`:

Replace `_refuse_r20_contradiction`'s body with:

```python
    @staticmethod
    def _refuse_r20_contradiction(record: Node) -> None:
        """A stored spec restores, or the record is refused: the r20 pair is
        `restore`'s `UnfreezableSpec`, surfaced as document validation; every
        other malformedness propagates as `restore` raised it."""
        if record.kind != "analysis-spec":
            return
        try:
            stored.analysis_spec_value(record)
        except UnfreezableSpec as caught:
            raise ValidationRefused(f"{record.id}: {caught}") from caught
```

In `_refuse`, beside the verification step:

```python
        if node.kind == "analysis-spec":
            self._refuse_r20_contradiction(node)
```

and in `_validated_import_bundle` delete the separate `self._refuse_r20_contradiction(record)` line — `_refuse(record, view=union)` now performs it, so the one call site is the one Task 10's arm sabotages. Import `UnfreezableSpec` from `beliefs.errors`. Then find every test fixture that hand-builds an `analysis-spec` record (`grep -rn '"analysis-spec"' tests/ | grep -v analysis_spec_node`) and rebuild each through `stored.analysis_spec_node(freeze(...))`; a fixture that existed to exercise the r20 refusal builds its node from the unfreezable mapping exactly as `test_spec.py`'s `_identified` case does, stamped through `stamp_semantic_identity`, and asserts `ValidationRefused`.

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
tasks done beliefs-91aac6 "stored.analysis_spec_node / analysis_spec_value over canonical projection text; spec.restore recomputes the identity and coerces nothing; the preflight, the r20 check and audit_corpus restore every spec; stored_specs returns specs and findings"
git add -A python tasks
git commit -m "feat(spec): a stored analysis-spec builder and reader over canonical projection text (V8)"
```

---

### Task 7: Admission over records read back (V3, V7's gather arm; V2 widened)

**Files:**
- Create: `python/tests/test_verification_publication.py` **[R6]**
- Modify: `python/tests/test_verification_identity.py`, `python/tests/test_evaluation.py` (V7's gather arm only)

- [ ] **Step 1: Widen the identity test to the full path** — replace its tail from `stored_node = writer.add(` onward with:

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
    from verification_fixtures import admission_over

    verdict, belief = admission_over(writer, published.proposition.id, original)
    assert isinstance(verdict, Admitted), verdict
    assert isinstance(belief, Belief), belief
```

with `from beliefs.admission import Admitted` and `from beliefs.belief import Belief` at the top.

- [ ] **Step 2: Write the V3 module** — `tests/test_verification_publication.py`:

```python
"""V3 (design §8): admission is evaluated over records read back, and the
belief moves with the verification record. V7's gather arm sits in
`test_evaluation.py` beside the gather fixture; nothing here is imported
back into `test_evaluation`."""

from __future__ import annotations

from test_audit import writer  # noqa: F401 - the fixture
from test_evaluation import CLAIM_FACET, OTHER_GENE, PHENO
from verification_fixtures import admission_over, evaluation_kwargs, publish_corpus

from beliefs import stored
from beliefs.belief import Belief, NoBelief
from beliefs.evaluation import gather
from beliefs.runrecord import run_ref
from beliefs.verification import INVALIDATED, active, lifecycle_state
from beliefs.verify import _mint_verification, publication_node


def _gathered(writer, proposition_ref):
    view = writer.read_view
    return gather(view, proposition_ref, **{k: v for k, v in evaluation_kwargs(view).items() if k != "availability"})


def test_v3_the_belief_moves_with_the_verification_record(writer):
    published = publish_corpus(writer, claim=CLAIM_FACET)
    _, before = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(before, NoBelief) and before.reason == "no-eligible-assessment"
    node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
    _, belief = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(belief, Belief)
    writer.delete(node.id)
    _, after = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(after, NoBelief) and after.reason == "no-eligible-assessment"


def test_v3_a_superseding_failed_verification_invalidates_and_retires_its_predecessor(writer):
    published = publish_corpus(writer, claim=CLAIM_FACET, publish=True)
    derived = published.derived
    failed = _mint_verification(  # the private mint: `build_verification` never sets `supersedes`
        original=derived.original, replayed=derived.replayed, assessment=derived.assessment, rule=derived.rule,
        report=derived.report, scope_rule=derived.scope_rule, scope=derived.scope, verdict="failed",
        supersedes=derived.identity(),
    )
    successor = writer.add(publication_node(failed, assessment_ref=published.assessment.id))
    inputs = _gathered(writer, published.proposition.id)
    assert lifecycle_state(inputs.verifications) == INVALIDATED
    assert {v.ref for v in active(inputs.verifications)} == {successor.id}  # [R10] the predecessor leaves the active set
    _, belief = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(belief, NoBelief)


def test_v3_negatives_another_proposition_is_never_gathered_and_a_twin_target_admits(writer):
    published = publish_corpus(writer, claim=CLAIM_FACET)
    value = stored.assessment_value(published.assessment)
    twin = writer.add(
        stored.assessment_node(
            "a-p-twin", title="twin", spec=value.spec, run=run_ref(published.original.address()),
            proposition=published.proposition.id, outcome=value.outcome, interpretation_rule=value.interpretation_rule,
        )
    )
    assert stored.assessment_value(twin).identity() == value.identity()
    writer.add(publication_node(published.derived, assessment_ref=twin.id))  # decision 17: the twin is a valid target
    _, belief = admission_over(writer, published.proposition.id, published.original)  # [R5] admission is over the identity
    assert isinstance(belief, Belief)
    other = writer.add(stored.proposition_node("q", title="q", claim={**CLAIM_FACET, "args": [OTHER_GENE, PHENO]}))
    inputs = _gathered(writer, other.id)
    assert inputs.verifications == () and inputs.assessments == ()
```

- [ ] **Step 3: V7's gather arm** — append to `tests/test_evaluation.py` (no import of the new module **[R6]**):

```python
from test_verify import production_pair  # noqa: F401 - the module-scoped fixture V7's arm resolves


def test_v7_gather_never_selects_a_production_verification(request, tmp_path):
    from test_relocation import _writer
    from test_verify import _production_verification

    from beliefs.verify import publication_node

    production = _production_verification(request.getfixturevalue("production_pair"))
    writer = _writer(tmp_path / "corpus")
    node = writer.add(publication_node(production))
    fixture = _fixture(writer, PROPOSITION_REF)
    inputs = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs)
    assert node.id not in {v.ref for v in inputs.verifications}
```

- [ ] **Step 4: Run**

Run: `uv run --frozen pytest tests/test_verification_publication.py tests/test_verification_identity.py tests/test_evaluation.py -p no:cacheprovider` → PASS. If `evaluate_over` answers `Refused(consulted-contracts-disagree…)`, copy the `CorpusPins` values `test_evaluation._fixture` uses into `evaluation_kwargs`.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "test(evaluation): admission over records read back — the belief moves with the verification record (V3, V7)"
```

---

### Task 8: The durable suite and the module graph (V1, V2, V3, V5 on the certified volume)

**Files:**
- Create: `python/tests/acceptance/test_verification_acceptance.py`
- Test: `python/tests/test_verify.py` (the acyclic-imports probe, in a subprocess **[R7]**)

- [ ] **Step 1: Read the rig you mirror**

Run: `sed -n 40,80p tests/acceptance/conftest.py && grep -n "^DIGEST\|^PROPOSITIONS\|^def adopted\|^def attended\|^def chain\|^def intents\|^def registrations" tests/acceptance/test_session_acceptance.py`. `work_directory` is the conftest's session fixture (`SCIENCE_CUT4_ROOT`, default `.cut4-acceptance` beside the checkout; the runner points every `SCIENCE_CUT*_ROOT` at one run directory). The head probe is `chain(root).tip`.

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
from authority import FULL
from test_evaluation import CLAIM_FACET
from test_session_acceptance import DIGEST, adopted, attended, chain, intents, registrations
from verification_fixtures import admission_over, forgeries, publish_corpus

from beliefs import stored
from beliefs.admission import Admitted
from beliefs.belief import Belief, NoBelief
from beliefs.corpus import open_corpus
from beliefs.permit import RequiredCapabilities
from beliefs.verification import INVALIDATED, active, lifecycle_state
from beliefs.verify import _mint_verification, publication_node

KINDS = RequiredCapabilities.for_kinds({"verification"}, {})  # [R8] runs, datasets and the assessment go through the library writer
TESTS = Path(__file__).resolve().parents[1]


def _fresh_process(root: Path, script: str) -> dict:
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(TESTS), str(TESTS / "acceptance")])}
    completed = subprocess.run([sys.executable, "-c", script.replace("ROOT", repr(str(root)))], check=True, capture_output=True, text=True, env=env)
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _session_over(work_directory):
    root = adopted(work_directory, "corpus")
    session, _ = attended(work_directory, root)
    writer = session.scoped(KINDS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    return root, session, writer


def test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL), claim=CLAIM_FACET)
        node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        library = open_corpus(root, authority=FULL)
        library.delete(stored.typed_ref("run", published.derived.original))
        library.delete(stored.typed_ref("run", published.derived.replayed))
    finally:
        session.close()
    report = _fresh_process(
        root,
        "import json; from authority import FULL; from beliefs.corpus import open_corpus; from beliefs.verify import decode_verification\n"
        f"view = open_corpus(ROOT, authority=FULL).read_view; d = decode_verification(view.get({node.id!r}))\n"
        "assert not view.holds(f'run:{d.original}') and not view.holds(f'run:{d.replayed}')\n"
        "print(json.dumps({'identity': d.identity(), 'report': d.report.identity(), 'scope': d.scope, 'verdict': d.verdict, 'basis': json.dumps(d.basis(), default=lambda r: r.identity(), sort_keys=True)}))",
    )
    derived = published.derived
    assert report["identity"] == derived.identity() and report["report"] == derived.report.identity()
    assert (report["scope"], report["verdict"]) == (derived.scope, derived.verdict)
    assert report["basis"] == json.dumps(derived.basis(), default=lambda r: r.identity(), sort_keys=True)


def test_v2_and_v3_admission_over_the_corpus_and_the_belief_moves_with_the_record(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL), claim=CLAIM_FACET)
        _, before = admission_over(open_corpus(root, authority=FULL), published.proposition.id, published.original)
        assert isinstance(before, NoBelief)
        node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        verdict, belief = admission_over(open_corpus(root, authority=FULL), published.proposition.id, published.original)
        assert isinstance(verdict, Admitted) and isinstance(belief, Belief)
        digest_here = belief.belief_input_digest
        writer.delete(node.id)
        _, after = admission_over(open_corpus(root, authority=FULL), published.proposition.id, published.original)
        assert isinstance(after, NoBelief)
        writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
    finally:
        session.close()
    report = _fresh_process(
        root,
        "import json; from authority import FULL; from beliefs.corpus import open_corpus; from verification_fixtures import admission_over\n"
        "from beliefs.runrecord import decode_run_closure\n"
        f"w = open_corpus(ROOT, authority=FULL); original = decode_run_closure(w.read_view.get({stored.typed_ref('run', published.derived.original)!r}))\n"
        f"verdict, belief = admission_over(w, {published.proposition.id!r}, original); print(json.dumps({{'digest': belief.belief_input_digest}}))",
    )
    assert report["digest"] == digest_here


def test_v3_a_superseding_failed_verification_invalidates_through_the_session(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        published = publish_corpus(open_corpus(root, authority=FULL), claim=CLAIM_FACET)
        derived = published.derived
        writer.add(publication_node(derived, assessment_ref=published.assessment.id))
        failed = _mint_verification(
            original=derived.original, replayed=derived.replayed, assessment=derived.assessment, rule=derived.rule,
            report=derived.report, scope_rule=derived.scope_rule, scope=derived.scope, verdict="failed",
            supersedes=derived.identity(),
        )
        successor = writer.add(publication_node(failed, assessment_ref=published.assessment.id))
    finally:
        session.close()
    view = open_corpus(root, authority=FULL).read_view
    values = tuple(stored.verification_value(n) for n in view.iter_stored() if n.kind == "verification")
    assert lifecycle_state(values) == INVALIDATED and {v.ref for v in active(values)} == {successor.id}


def test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent(work_directory):
    root, session, writer = _session_over(work_directory)
    try:
        library = open_corpus(root, authority=FULL)
        published = publish_corpus(library, claim=CLAIM_FACET)
        cases = forgeries(library, published)  # [R8] helper records first, then the baseline
        open_corpus(root, authority=FULL).read_view  # a settled, non-writing probe
        head_before = chain(root).tip
        intents_before, registrations_before = len(intents(root)), len(registrations(root))
        acts_before = len(session.invocation_acts("A"))
        for node, refusal, reason in cases:
            with pytest.raises(refusal, match=reason):
                writer.add(node)
            assert chain(root).tip == head_before, node.id
            assert len(session.invocation_acts("A")) == acts_before
            assert not (root / "verification" / f"{node.id.split(':', 1)[1]}.md").exists()
        writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
        assert len(intents(root)) == intents_before + 1 and len(registrations(root)) == registrations_before + 1
        assert len(session.invocation_acts("A")) == acts_before + 1
    finally:
        session.close()
```

- [ ] **Step 3: Add the acyclic-imports probe, in a subprocess** — append to `tests/test_verify.py`:

```python
def test_the_publication_modules_form_no_import_cycle():
    """Design §4.3, probed in a fresh interpreter so no loaded class identity is disturbed. [R7]"""
    import subprocess
    import sys

    script = (
        "import importlib\n"
        "for name in ('beliefs.verify', 'beliefs.stored', 'beliefs.spec', 'beliefs.audit', 'beliefs.corpus', 'beliefs.evaluation', 'beliefs.admission'):\n"
        "    importlib.import_module(name)\n"
        "import beliefs.corpus, pathlib\n"
        "source = pathlib.Path(beliefs.corpus.__file__).read_text(encoding='utf-8')\n"
        "assert '\\nfrom beliefs.verify import' not in source and '\\nimport beliefs.verify' not in source\n"
        "print('acyclic')\n"
    )
    completed = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)
    assert completed.stdout.strip() == "acyclic"
```

- [ ] **Step 4: Run the durable module**

Run: `SCIENCE_CUT4_ROOT=$(git rev-parse --show-toplevel)/.cut21-acceptance uv run --frozen pytest tests/acceptance/test_verification_acceptance.py -p no:cacheprovider`
Expected: PASS (4 tests). A capability refusal is an error: do not skip. If `library.delete` of a run is refused with `DeletionKindExcluded`, the design's V1 arm cannot delete runs; date it in the results record and assert instead that the fresh process decodes with `view.holds` monkeypatched to raise.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "test(acceptance): verification publication through an attended session on the certified volume (V1, V2, V3, V5)"
```

---

### Task 9: The reproduction driver reads the report (V1's and V8's 10b arms) **[R9]**

**Files:**
- Modify: `python/tools/reproduction/spec.py` (`spec_record`), `belief.py` (step 8), `close.py` (`evidence_for`), `rederive.py` (`reconstruct` as a pure function)
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `close.evidence_for(view) -> DerivationEvidence` (specs from the corpus, rules from code); `rederive.reconstruct(view, st: dict, evidence) -> dict` (10b's report; no `spec.frozen()` anywhere in it).

- [ ] **Step 1: Write the failing driver test** — append to `tests/test_reproduction_driver.py`:

```python
def test_10b_reads_the_report_from_the_corpus_with_no_in_process_spec(tmp_path, monkeypatch):
    """V1 and V8's 10b arms: the report, scope and verdict are read; the only
    in-process input is the rule implementations; `spec.frozen()` is not
    reachable. The negative: a report-less record reports false."""
    from fixtures_cut3 import spec_rules
    from test_relocation import _writer
    from verification_fixtures import publish_corpus

    from beliefs import stored
    from beliefs.replay import CONTENT_EQUALITY
    from beliefs.verify import publication_node
    from reproduction import close, rederive, spec

    writer = _writer(tmp_path / "corpus")
    published = publish_corpus(writer)
    spec_node = writer.add(stored.analysis_spec_node(published.frozen))
    node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))

    def unavailable():
        raise RuntimeError("the in-process spec is unavailable")

    monkeypatch.setattr(spec, "frozen", unavailable)
    interpretation = spec_rules()[published.frozen.interpretation_rule]
    monkeypatch.setattr(spec, "equivalence", lambda: CONTENT_EQUALITY)
    monkeypatch.setattr(spec, "interpretation", lambda: interpretation)
    st = {"verification_ref": node.id, "spec_ref": spec_node.id}
    view = writer.read_view
    report = rederive.reconstruct(view, st, close.evidence_for(view))
    assert report["comparison_report_stored"] is True
    assert report["scope_equal"] is True and report["verdict_equal"] is True and report["report_identity_equal"] is True
    assert report["inputs"]["in_process"] == ["interpretation and equivalence RuleImplementations"]
    assert report["spec_restored_identity_matches_run"] is True
    assert report["audit_check"] == {"checked": True, "reason": "", "contradiction": None}
    legacy = writer.add(
        stored.verification_node(
            "legacy", title="legacy", assessment=published.derived.assessment, assessment_ref=published.assessment.id,
            scope=published.derived.scope, verdict=published.derived.verdict,
            derivation=(stored.typed_ref("run", published.derived.original), stored.typed_ref("run", published.derived.replayed)),
        )
    )
    negative = rederive.reconstruct(writer.read_view, {**st, "verification_ref": legacy.id}, close.evidence_for(writer.read_view))
    assert negative["comparison_report_stored"] is False and "scope_read" not in negative


def test_10b_names_no_in_process_spec():
    from pathlib import Path

    from reproduction import rederive

    source = Path(rederive.__file__).read_text(encoding="utf-8")
    assert "spec.frozen" not in source and "from reproduction import" in source
```

Run: `uv run --frozen pytest tests/test_reproduction_driver.py -k 10b -p no:cacheprovider` → FAIL (`AttributeError: module 'reproduction.rederive' has no attribute 'reconstruct'`).

- [ ] **Step 2: Replace the hand-built spec record** — in `tools/reproduction/spec.py`:

```python
def spec_record(spec: FrozenSpec) -> Node:
    """The kernel's own builder (verification-publication design §7)."""
    return stored.analysis_spec_node(spec)
```

and delete the step-4 finding about the missing builder if `main` still records it (keep the interpretation-rule finding).

- [ ] **Step 3: Publish through the projection** — in `belief.py` replace the `writer.add(stored.verification_node(...))` block with `minted = writer.add(publication_node(verification, assessment_ref=st["assessment_ref"]))`, importing `publication_node`.

- [ ] **Step 4: Evidence from the corpus** — in `close.py`:

```python
def evidence_for(view) -> DerivationEvidence:
    """Specs from the corpus, rules from code — 10b's only in-process input."""
    specs, findings = stored_specs(view)
    if findings:
        raise RuntimeError(f"stored specs that do not restore: {[f.ref for f in findings]}")
    return DerivationEvidence(
        specs=specs,
        held_rules={spec.equivalence().identity: spec.equivalence()},
        implementations={spec.interpretation().identity: spec.interpretation()},
    )


def evidence() -> DerivationEvidence:
    return evidence_for(world.open_writer().read_view)
```

importing `stored_specs` from `beliefs.audit`.

- [ ] **Step 5: 10b as a pure function** — in `rederive.py` replace the evidence-reconstruction block of `main` with a call to:

```python
def reconstruct(view, st: dict, evidence: DerivationEvidence) -> dict:
    """10b, field by field, each labelled. Reads the verification record, the
    two run publications and the spec record; recomputes only through
    `evidence`, which names no in-process spec."""
    node = view.get(st["verification_ref"])
    stored_value = stored.verification_value(node)
    decoded = decode_verification(node)
    report: dict = {
        "inputs": {
            "corpus": ["verification record (basis, comparison report, scope, verdict read)", "two run publications", "analysis-spec record"],
            "in_process": ["interpretation and equivalence RuleImplementations"],
        },
        "comparison_report_stored": decoded is not None,
        "derivation_named": False,
        "closures_decoded": False,
        "scope_recomputed": None,
        "scope_equal": None,
        "verdict_recomputed": None,
        "verdict_equal": None,
        "report_identity_equal": None,
        "spec_restored_identity_matches_run": None,
        "audit_check": None,
    }
    if decoded is not None:
        report["scope_read"], report["verdict_read"], report["report_identity_read"] = decoded.scope, decoded.verdict, decoded.report.identity()
    derivation = stored.verification_derivation(node)
    if derivation is not None:
        report["derivation_named"] = True
        original, replayed = (decode_run_closure(view.get(ref)) for ref in derivation)
        report["closures_decoded"] = True
        certification = None if decoded is None else decoded.report.certification
        scope = derive_scope(original, replayed, certification=certification)
        report["scope_recomputed"], report["scope_equal"] = scope, scope == stored_value.scope
        rebuilt = build_verification(
            original, replayed, specs=evidence.specs, held_rules=evidence.held_rules,
            contract_identity="none-consulted", epoch="none-published", certification=certification,
        )
        if isinstance(rebuilt, AssessmentVerification):
            report["verdict_recomputed"], report["verdict_equal"] = rebuilt.verdict, rebuilt.verdict == stored_value.verdict
            if decoded is not None:
                report["report_identity_equal"] = rebuilt.report.identity() == decoded.report.identity()
        if view.holds(st["spec_ref"]):
            restored = stored.analysis_spec_value(view.get(st["spec_ref"]))
            report["spec_restored_identity_matches_run"] = restored.identity == original.recipe.spec_identity
    outcome = check_verification(view, node, evidence=evidence)
    report["audit_check"] = {
        "checked": outcome.checked,
        "reason": outcome.reason,
        "contradiction": None if outcome.contradiction is None else {"code": outcome.contradiction.code, "detail": outcome.contradiction.detail},
    }
    return report
```

`main` calls `reconstruct(view, st, close.evidence())`, records the 10b design-gap finding only when `comparison_report_stored` is false, and keeps 10a. The module imports `decode_verification` and `DerivationEvidence`, and drops `spec` from its `from reproduction import …` line.

- [ ] **Step 6: Run the driver's tests and the suite**

Run: `uv run --frozen pytest tests/test_reproduction_driver.py -p no:cacheprovider` → PASS.
Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 7: Re-run the driver into a fresh directory** (design decision 12), from `python/`, with the predecessor corpus available as the record's §1 states and `SCIENCE_MM30_ROOT` set to a fresh directory on the certified volume beside the **main** checkout (e.g. `<main checkout>/.mm30-reproduction-cut21`):

```bash
for step in preflight select_target type_target hold world spec run belief close rederive; do
  PYTHONPATH=tools uv run --frozen python -m reproduction.$step || { echo "step $step failed"; break; }
done
```

Expected at `rederive`: the printed 10b JSON has `"comparison_report_stored": true`, `"scope_equal": true`, `"verdict_equal": true`, `"report_identity_equal": true` and `"in_process": ["interpretation and equivalence RuleImplementations"]`; step 8 prints `admission Admitted` and a `Belief` answer. Keep the 10b JSON for Task 12.

- [ ] **Step 8: Commit**

```bash
git add -A python
git commit -m "feat(reproduction): publish the verification with its report, build the spec record, read 10b from the corpus alone"
```

---

### Task 10: N2 arms, the cut-21 audit and the runner **[R10] [R11]**

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut21.py`, `python/tests/acceptance/test_n2_cut21.py`, `python/tools/cut21_acceptance.py`

- [ ] **Step 1: Declare the arms, one per frozen sabotage** — `tests/acceptance/n2_arms_cut21.py`. The cut's §5 item 4 lists twenty-three sabotages; every one is an arm below (plus V3's own), and every `before` is copied from the landed source when the arm is written — re-read each site. Parametrized check ids are those `V4_IDS`/the `mutate<N>` defaults produce; confirm with `uv run --frozen pytest tests/test_audit.py tests/test_verify.py tests/test_spec.py --collect-only -q | grep -E "v4|v6|v8"`.

```python
"""Cut 21's eight frozen declaration units and their source sabotages
(docs/designs/2026-09-06-conformance-cut-21.md §3, §5 item 4), one arm per
frozen sabotage. `V5a` keeps the refusal and appends an intent before it,
inside `_refuse_verification` — the after-intent ordering as one replacement."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

_VERIFY, _STORED, _AUDIT, _CORPUS, _SPEC, _ADMISSION, _EVALUATION = (
    "verify.py", "stored.py", "audit.py", "corpus.py", "spec.py", "admission.py", "evaluation.py",
)
_TV, _TS, _TAD, _TA, _TI, _TO, _TSP, _TID, _TVP, _TCW, _ACC = (
    "test_verify.py", "test_stored.py", "test_admission.py", "test_audit.py", "test_import_derivation.py",
    "test_operation_writes.py", "test_spec.py", "test_verification_identity.py",
    "test_verification_publication.py", "test_corpus_write.py", "acceptance/test_verification_acceptance.py",
)

DECLARATION_UNITS = tuple(f"V{n}" for n in range(1, 9))
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


CUT21_ARMS = (
    # --- verify.py -----------------------------------------------------------
    Arm("V1a", "drop report from the projection",
        Sabotage(_VERIFY, '        "report": derived.report.projection(),\n', '        "report": {},\n'),
        (f"{_TV}::test_v1_publication_node_round_trips_through_the_reader", f"{_ACC}::test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone")),
    Arm("V1b", "skip the identity recomputation in decode_verification",
        Sabotage(_VERIFY, '    if decoded.identity() != stored.local_id("verification", node.id):\n', "    if False:\n"),
        (f"{_TV}::test_v5_a_record_id_that_does_not_recompute_is_malformed",)),
    Arm("V6a", "accept a projection with a missing key",
        Sabotage(_VERIFY, "    if not isinstance(member, Mapping) or not _REPORT_REQUIRED <= set(member) <= _REPORT_REQUIRED | _REPORT_OPTIONAL:\n", "    if not isinstance(member, Mapping):\n"),
        (f"{_TV}::test_v6_a_present_but_malformed_report_or_member_is_refused[mutate0]",)),
    Arm("V7a", "write assessment for the production shape",
        Sabotage(_VERIFY, '    if type(derived) is AssessmentVerification:\n        facet["assessment"] = derived.assessment\n', '    facet["assessment"] = getattr(derived, "assessment", "")\n'),
        (f"{_TV}::test_v7_the_production_shape_publishes_edge_less_and_admits_nothing",)),
    Arm("V2e", "compute the assessment digest over the typed ref",
        Sabotage(_VERIFY, '            {"spec": spec.identity, "run": original.address(), "proposition": spec.target},\n', '            {"spec": spec.identity, "run": stored.typed_ref("run", original.address()), "proposition": spec.target},\n'),
        (f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean",)),
    Arm("V3a", "publish a superseding verification without its predecessor",
        Sabotage(_VERIFY, '        facet["supersedes"] = stored.typed_ref("verification", derived.supersedes)\n', "        pass\n"),
        (f"{_TV}::test_v3_a_superseding_verification_publishes_its_typed_predecessor", f"{_TVP}::test_v3_a_superseding_failed_verification_invalidates_and_retires_its_predecessor")),
    # --- stored.py -----------------------------------------------------------
    Arm("V2a", "return the typed ref from assessment_value",
        Sabotage(_STORED, '        run=local_id("run", facet.get("run")),\n', '        run=str(facet.get("run", "")),\n'),
        (f"{_TS}::test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one", f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean")),
    Arm("V2f", "strip nothing in local_id",
        Sabotage(_STORED, "    return ref[len(prefix):]\n", "    return ref\n"),
        (f"{_TS}::test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref",)),
    Arm("V8d", "skip the identity check in analysis_spec_value",
        Sabotage(_STORED, '    if node.id != typed_ref("analysis-spec", spec.identity):\n', "    if False:\n"),
        (f"{_TS}::test_v8_a_renamed_or_falsely_identified_record_is_malformed",)),
    # --- admission.py / evaluation.py ----------------------------------------
    Arm("V2b", "compare run.ref to the bare address",
        Sabotage(_ADMISSION, '    if run.ref != typed_ref("run", assessment.run):\n', "    if run.ref != assessment.run:\n"),
        (f"{_TAD}::test_v2_admit_matches_a_typed_run_ref_to_the_bare_member",)),
    Arm("V2c", "resolve a.run untyped",
        Sabotage(_EVALUATION, '        ref = stored.typed_ref("run", a.run)\n', "        ref = a.run\n"),
        (f"{_TID}::test_v2_one_identity_admits_over_the_corpus_and_audits_clean",)),
    # --- audit.py ------------------------------------------------------------
    Arm("V4a", "skip the scope comparison",
        Sabotage(_AUDIT, "        if decoded.scope != derived.scope:\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[scope]",)),
    Arm("V4b", "skip the report comparison",
        Sabotage(_AUDIT, "        if decoded.report.identity() != derived.report.identity():\n", "        if False:\n"),
        (f"{_TA}::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[report-receipt]",)),
    Arm("V4c", "take certification=None for a decoded report",
        Sabotage(_AUDIT, "    certification = None if decoded is None else decoded.report.certification\n", "    certification = None\n"),
        (f"{_TA}::test_v4_a_certified_verification_audits_clean_through_its_stored_certification",)),
    Arm("V2g", "compare stored_value.run through run_ref again",
        Sabotage(_AUDIT, "    if stored_value.run != derived.run:\n", '    if stored_value.run != "run:" + derived.run:\n'),
        (f"{_TA}::test_v4_a_published_verification_audits_checked_with_no_contradiction",)),
    Arm("V2d", "resolve the assessment's run bare",
        Sabotage(_AUDIT, '    closure, why = _closure(view, stored.typed_ref("run", stored_value.run))\n', "    closure, why = _closure(view, stored_value.run)\n"),
        (f"{_TA}::test_v2_a_contradicted_assessment_still_contradicts",)),
    Arm("V8e", "drop the analysis-spec branch",
        Sabotage(_AUDIT, '            elif node.kind == "analysis-spec":\n                outcome = check_analysis_spec(node)\n', "            elif False:\n                continue\n"),
        (f"{_TA}::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it",)),
    Arm("V8c", "let stored_specs return the mapping alone",
        Sabotage(_AUDIT, "            spec = stored.analysis_spec_value(node)\n        except RecordError as refused:\n", "            spec = stored.analysis_spec_value(node)\n        except RecordError:\n            continue\n"),
        (f"{_TA}::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it",)),
    # --- corpus.py -----------------------------------------------------------
    Arm("V5a", "the verification refusal lands after an intent is appended",
        # The refusal is preserved; an intent is appended through the port first, which is
        # exactly the ordering the guarantee forbids. `_encode_operation_intent` is corpus.py's own.
        Sabotage(_CORPUS, "        decoded = decode_verification(node)  # MalformedRecord propagates: refuse, never repair\n",
                 '        port = self._operation_port\n        assert port is not None\n        port.append_intent(_encode_operation_intent("corpus-write", "sabotage", self.authority.actor))\n        decoded = decode_verification(node)  # MalformedRecord propagates: refuse, never repair\n'),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent", f"{_ACC}::test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent")),
    Arm("V5b", "return before the target check",
        Sabotage(_CORPUS, "        if identity != decoded.assessment:\n", "        if False:\n"),
        (f"{_TO}::test_v5_each_forgery_is_refused_before_the_intent",)),
    Arm("V5c", "resolve the target in self._view instead of the union for import",
        Sabotage(_CORPUS, "            self._refuse_verification(node, view=self._view if view is None else view)\n", "            self._refuse_verification(node, view=self._view)\n"),
        (f"{_TI}::test_v5_every_forgery_refuses_the_bundle_and_the_well_formed_record_imports",)),
    Arm("V8f", "skip _refuse's spec restoration",
        Sabotage(_CORPUS, '        if node.kind == "analysis-spec":\n            self._refuse_r20_contradiction(node)\n', "        pass\n"),
        (f"{_TCW}::test_v8_a_spec_record_whose_identity_is_false_is_refused_at_add", f"{_TI}::test_v8_a_spec_record_whose_identity_is_false_refuses_the_bundle")),
    # --- spec.py -------------------------------------------------------------
    Arm("V8a", "skip restore's identity check",
        Sabotage(_SPEC, "    if v1.digest(SPEC_DOMAIN, mapping) != identity:\n", "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_a_projection_that_does_not_digest_to_the_identity[corrupt0]", f"{_TS}::test_v8_a_renamed_or_falsely_identified_record_is_malformed")),
    Arm("V8b", "skip the unfreezable check in restore",
        Sabotage(_SPEC, '    if isinstance(nondeterminism, StochasticUnseeded) and text["equivalence_rule"] in BITWISE_EQUIVALENCE_RULES:\n', "    if False:\n"),
        (f"{_TSP}::test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair",)),
    Arm("V8g", "decode with a float parser",
        Sabotage(_SPEC, "        mapping = v1.decode(projection)\n", '        mapping = __import__("json").loads(projection)\n'),
        (f"{_TSP}::test_v8_restore_round_trips_every_member_and_the_decimal_by_type",)),
)
```

Every `before` must occur exactly once in its module. V8c's `before` starts one line above the `except` because `audit_corpus` carries the same `except RecordError as refused:` line; its `after` skips the finding, so the mapping returns alone. If a parametrized id differs from the collected one, copy the collected id.

- [ ] **Step 2: Write the audit module** — `tests/acceptance/test_n2_cut21.py`, by the cut-19 pattern (copy `test_n2_cut19.py` and adjust): `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-06-conformance-cut-21.md"`, `CUT21_FREEZE_COMMIT = "41c9920"`, `CUT21_FROZEN_SHA256 = "eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5"`, `FROZEN_PRIOR_CUT_FILES` = cut 19's table plus `"python/tests/acceptance/n2_arms_cut19.py": "8723fac"`, `PRIOR_ARMS` gaining `CUT19_ARMS`, the inventory test asserting `DECLARATION_UNITS == tuple(f"V{n}" for n in range(1, 9))` and `len(CUT21_ARMS) == 25`, and the freeze test asserting `"**8 declaration units**"`, `"Eight guarantee rows are read, **8 full/closed** (V1–V8), 0 partial, 0"` and `'("cut20_acceptance.py",)'` in the current text, with `_frozen_body` spanning `## 2. The boundary` to the first `\n## 8.` (none yet: the whole tail).

- [ ] **Step 3: Write the runner** — `tools/cut21_acceptance.py`: copy `cut19_acceptance.py`, with `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut21-acceptance"`, `PREFIX_RUNNERS = ("cut20_acceptance.py",)`, `PHASE_MODULES = ("test_verification_acceptance.py", "test_n2_cut21.py")`, `SCIENCE_CUT21_ROOT`, `range(4, 22)` in `cut_environment`, `SCIENCE_CUT20_ROOT` in `run_prefix`'s environment, the import `from n2_arms_cut21 import CUT21_ARMS, DECLARATION_UNITS`, and the final line `f"declared arms: {arms} (= {units} declaration units; 8 guarantee rows)"`.

- [ ] **Step 4: Run the audit module directly** (the runner refuses until cut 20 merges):

Run: `SCIENCE_CUT4_ROOT=$(git rev-parse --show-toplevel)/.cut21-acceptance uv run --frozen pytest tests/acceptance/test_n2_cut21.py -p no:cacheprovider`
Expected: PASS — every arm sound, every check resolved, the freeze pinned. A `stale` finding means a `before` no longer matches the source: fix the arm, never the source. A `mixed` finding means a check passes under its sabotage: strengthen the check, never the arm.
Run: `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 5: Commit**

```bash
git add -A python
git commit -m "test(cut21): declare the N2 arms, the cut-21 audit and the acceptance runner"
```

---

### Task 11: Bank the implementation

**Files:**
- Modify: `docs/designs/2026-09-06-verification-publication-design.md` (Status), `docs/designs/2026-08-02-computation-reproducibility-design.md` (§7.3c dated note), `docs/designs/2026-08-30-run-confinement-design.md` (§10), `docs/plans/2026-09-04-conformance-cut-18-results.md` (§3 R3, §4), `docs/guide/computation-and-reproducibility.md`, `docs/guide/glossary.md`

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
- Modify: `contracts/science/CONTRACT.yaml` and its packaged copy (the reader lines), `python/tests/acceptance/test_n2_cut21.py` (`FROZEN_PRIOR_CUT_FILES` gains cut 20's arms), the ledger, the roadmap, `README.md`, `docs/plans/2026-09-06-conformance-cut-21-results.md`

- [ ] **Step 1: Merge `main`** once the domain lane's cut 20 is discharged: `git merge --no-ff main` in the worktree; resolve every shared file toward `main` (roadmap rule 3): `_refuse`'s step order is document validation → `_refuse_facets` → `_refuse_verification`/`_refuse_r20_contradiction` → stamp; `audit_corpus` and `check_verification` keep their profile arguments from `main` and this lane's bodies; `stored.py`'s tables become views as `main` has them, with this lane's builders, readers and helper pair added.

- [ ] **Step 2: Declare the readers.** In the merged base contract's `facets:` section, name `verify.decode_verification` beside `verification`'s readers and `stored.analysis_spec_value` as `analysis-spec`'s reader, in the shape that design's §3.2 fixes; keep the packaged copy byte-identical (its test holds them). Run the full suite and the facet tests.

- [ ] **Step 3: Pin cut 20's arms.** Add cut 20's arms file at its last commit (`git log -1 --format=%h -- <path>`) to `FROZEN_PRIOR_CUT_FILES` and `CUT20_ARMS` to `PRIOR_ARMS` in `test_n2_cut21.py`.

- [ ] **Step 4: Re-run the reproduction driver** into a fresh directory (Task 9 step 7) on the merged tree and keep the 10b JSON.

- [ ] **Step 5: Run the runner on the certified volume**

Run: `uv run --frozen python tools/cut21_acceptance.py` from `python/` → every phase green through the cut 20, 19, 18 and 17 prefixes, ending `declared arms: 25 (= 8 declaration units; 8 guarantee rows)`.

- [ ] **Step 6: The results record** — `docs/plans/2026-09-06-conformance-cut-21-results.md`, by cut 19's record's sections: header (subject, measured against the frozen cut at `41c9920`, digest `eaf2147…`); §1 accounting (8 units, 25 arms, all sound); §2 what ran (the runner's command, its work root, the host tuple, every phase, the driver's 10b JSON quoted); §3 disposition (V1–V8 close; R19's stored-verification limitation closes and its cross-corpus arm stays with `world-resolution`; the `Remaining boundary` section naming `world-resolution`'s rows); §4 what this run does not claim (design §9's limitations); §5 every substitution from the frozen §3 and §5, dated — at least these two: V3's negatives live in `test_verification_publication.py` rather than `test_evaluation.py` (a circular test import), and V5's "after `append_intent`" sabotage is declared inside `_refuse_verification` (an intent appended through the port before the check) rather than by moving the call in `_commit`; plus the V1 run-deletion substitution if Task 8 step 4 met it.

- [ ] **Step 7: Re-rank.** Run `uv run --frozen python tools/roadmap_status.py` and rewrite the roadmap whole: `**Ranked at:** cut 21`; tier 1 row 1 leaves; `write-path`'s row reads "no open boundary"; the boundary index drops `verification-publication`; Appendix A gains the `V` row (8 closed) and updates the totals; Appendix C drops R19's row. The ledger's `Current state` heading date and table drop the boundary and restate R19's remainder; its summary names cut 21. README: the design's row reads "V1–V8, closed at cut 21", the cut's row "discharged 2026-09-06", and the results record is listed where cut 19's is.

- [ ] **Step 8: Tests, task, commit, merge**

Run: `uv run --frozen pytest -p no:cacheprovider 2>&1 | tail -3 && uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider && uv run --frozen ruff check . && uv run --frozen pyright` → clean.

```bash
tasks done beliefs-754995 "cut 21 discharged: V1–V8 closed, R19's stored-verification limitation lifted; results record and re-rank landed"
git add -A
git commit -m "docs(verification): discharge conformance cut 21 and re-rank the roadmap"
```

Then the finishing-a-development-branch skill: merge `--no-ff` into `main`, remove the worktree, and confirm the execution ledger (this plan's checkbox state and every ruling made during execution) is committed to a tracked path before the worktree goes.
