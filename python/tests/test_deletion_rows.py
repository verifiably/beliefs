"""Frozen cut-18 row evidence over the ordinary-write `delete`.

One section per frozen row of `docs/designs/2026-09-04-conformance-cut-18.md`
§3, portable over `test_relocation._writer`. Task 8 re-runs the same arms
durably; what runs here is the corpus-read half of every selection, and only
that half — the log-verification arms G8 and C6 also name are the durable
module's, and §7's two narrowings are honoured here:

- **S5's "indistinguishable"** is compared over the epistemic readings only —
  stored ids, the lineage snapshot projection, certification, the belief
  digest and admission. Chain and log state are never compared, because a
  managed deletion is perfectly visible there and the row does not claim
  otherwise.
- **R23's "the audit reports nothing"** is asserted as the absence of the
  `lineage-basis-contradicted` code, never as an empty finding list.

M3's audit arm (a raw-written cyclic pair classified malformed before any
standing or belief evaluation) already runs in
`test_audit.py::TestOmegaValidComesFirst`; this module adds M3's admission-order
negative and does not duplicate it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pytest
from authority import ACTOR
from fixtures_cut4 import path_for
from nodes.core.node import Node
from profiles import pins_for
from test_audit import forged_single_over_two_producers
from test_belief import PROFILE
from test_decode import ADULTS, COHORT_DATASET
from test_deletion import retraction_for
from test_evaluation import (
    CLAIM_FACET,
    EX,
    GENE,
    OTHER_CLAIM_FACET,
    OTHER_GENE,
    PHENO,
    PROPOSITION_REF,
    _address,
    _observations,
    _resources,
)
from test_relocation import CONSOLIDATE_FIELDS, _writer, _writer_for
from test_relocation_rows import _basis_route, _duplicate_datasets

from beliefs import relocation, stored
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.belief import Availability, Belief, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.contract import load_domain_contract
from beliefs.corpus import CorpusWriter, ReadView, corpus_check, lineage_snapshot, standing_in_local_view
from beliefs.decode import claim_from_stored
from beliefs.evaluation import evaluate_over
from beliefs.lineage import Certification, LineageSnapshot, certify, snapshot_projection
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity
from beliefs.record import AssessmentValue
from beliefs.resolution import build_snapshot
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED, lifecycle_state

# --- the shared corpus: one full belief scenario, minted through the writer ---

OBSERVED = ("a", "b")
"""The two observed datasets, one per assessment run — `test_evaluation._seed`'s
shape, re-homed onto `CorpusWriter.add` so these tests can `delete` from it."""

DATASET_ROOTS = tuple(_address(letter) for letter in OBSERVED)
"""Each observed dataset is minted **at its own content address**: the slug is
`_address(letter)`'s `sha256:<hex>` half, so the node ref and the address are
one string — what `production.mint_dataset` mints.

This is load-bearing, not cosmetic. `belief.evaluate` step 7 keys `certify` by
`_observes_roots`, which is `dataset_address(...)`, while `lineage_snapshot`
keys its bases by node **ref**. On a corpus where those differ, every lineage
finding is invisible to the belief value and S5's *belief may rise* cannot be
run at all. Here they coincide, so a certification decision moves belief."""

DERIVED, SIBLING = DATASET_ROOTS
"""The first observed dataset carries the stamped basis the lineage rows delete
from; the second is the independent side `certify` is asked about."""

ACQUISITION_WITNESS = _address("e")

ASSESSMENTS = ("assessment:a-1", "assessment:a-2")


@dataclass(frozen=True)
class Scenario:
    """A writer-backed corpus that yields a `Belief` through `evaluate_over`.

    Every reading is recomputed from the live view on each call: a snapshot or
    an admission state cached across a `delete` would be the very residue S5's
    row denies, so nothing here is memoized.
    """

    writer: CorpusWriter
    values: dict[str, AssessmentValue]
    roots: tuple[str, ...]

    @property
    def view(self) -> ReadView:
        return self.writer.read_view

    def snapshot(self) -> LineageSnapshot:
        return lineage_snapshot(self.view, self.roots)

    def context(self) -> SuppliedContext:
        return SuppliedContext(
            snapshot=self.snapshot(),
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={value.identity(): ("c1",) for value in self.values.values()},
            pins={"c1": pins_for(PROFILE)},
        )

    def belief(self) -> Belief:
        """Admission and the digest through the instrumented resolver (M1's
        seam), so these rows read the same path belief actually runs on."""
        answer = evaluate_over(
            self.view,
            PROPOSITION_REF,
            availability=Availability(
                observations=_observations(*(OBSERVED + (("e",) if ACQUISITION_WITNESS in self.roots else ()))),
                implementations={BELIEF_V1.identity: BELIEF_V1},
                fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
            ),
            context=self.context(),
            profile=PROFILE,
            resolution=build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
            binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
        )
        assert isinstance(answer, Belief), answer
        return answer

    def lifecycle(self, assessment: str) -> str:
        """Kernel §3.3's state for one assessment, over the stored verification
        records, `active` read under the amendment: a verification a standing
        retraction targets is not active. `gather` enumerates no retractions —
        they reach a closure as supplied `context.retractions` — so the
        amendment is applied here, over `standing_in_local_view`."""
        identity = self.values[assessment].identity()
        live = tuple(
            stored.verification_value(node)
            for node in self.view.iter_stored()
            if node.kind == "verification"
            if stored.verification_value(node).assessment == identity
            if standing_in_local_view(self.view, node.id)
        )
        return lifecycle_state(live)


def _records(
    *,
    basis: dict[str, Any] | None = None,
    extra: tuple[Node, ...] = (),
    retraction_chain: bool = False,
) -> dict[str, tuple[str, Node]]:
    """The one record set every section runs over, each entry tagged with the
    write it arrives through: `add` for the ordinary kinds and `retract` for a
    retraction, which C10 refuses unless its target already resolves.

    Two assessments on one proposition, each over its own run observing its own
    pinned dataset, each carrying one `clean-environment, passed` verification
    — `belief().value == 2` before anything is touched. With a lineage basis,
    the first run also observes a separate acquisition witness; its derived
    dataset supplies lineage, not acquisition standing.

    One builder, two consumers: `_scenario` admits it in its own order and M3's
    negative admits it in two, so the corpus the digest comparison runs over
    and the corpus every other row runs over cannot drift apart.
    """
    records: dict[str, tuple[str, Node]] = {
        "p": ("add", stored.proposition_node("p", title="p", claim=CLAIM_FACET)),
        "q": ("add", stored.proposition_node("q", title="q", claim=OTHER_CLAIM_FACET)),
    }
    if basis is not None:
        records["acquisition-witness"] = (
            "add",
            stored.dataset_node(
                ACQUISITION_WITNESS.split(":", 1)[1], title="acquisition witness",
                resources=_resources("e"),
                empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
            ),
        )
    verifications: dict[str, Node] = {}
    for index, letter in enumerate(OBSERVED, start=1):
        address = _address(letter)
        records[f"d-{letter}"] = (
            "add",
            stored.dataset_node(
                address.split(":", 1)[1],  # the address is the ref: see DATASET_ROOTS
                title=f"d-{letter}",
                resources=_resources(letter),
                empirical_observation=None if basis is not None and address == DERIVED else {"locator": "instrument:fixture", "attested_by": ACTOR},
                basis=basis if address == DERIVED else None,
            ),
        )
        records[f"run-{letter}"] = (
            "add",
            stored.run_node(
                f"run-{letter}", title=f"run-{letter}", spec=f"spec-{letter}",
                observes=[address, ACQUISITION_WITNESS] if basis is not None and address == DERIVED else [address],
            ),
        )
        assessment = stored.assessment_node(
            f"a-{index}",
            title=f"a-{index}",
            spec=f"spec-{letter}",
            run=f"run:run-{letter}",
            proposition=PROPOSITION_REF,
            outcome="supported",
            interpretation_rule="rule-1",
        )
        records[f"a-{index}"] = ("add", assessment)
        verification = stored.verification_node(
            f"v-{index}",
            title=f"v-{index}",
            assessment=stored.assessment_value(assessment).identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        )
        verifications[f"v-{index}"] = verification
        records[f"v-{index}"] = ("add", verification)
    for node in extra:
        records[node.id] = ("add", node)
    if retraction_chain:
        retraction = retraction_for(verifications["v-2"], "verification:grounds")
        records["retraction"] = ("retract", retraction)
        records["counter"] = ("retract", retraction_for(retraction, "verification:counter-grounds"))
    return records


def _admit(
    corpus,
    records: dict[str, tuple[str, Node]],
    order: tuple[str, ...],
    *,
    roots: tuple[str, ...] = DATASET_ROOTS,
) -> Scenario:
    """Admit `records` into a fresh corpus in `order`, through the boundary.

    `corpus` is a path here and an open durable writer in Task 8's acceptance
    module (`_writer_for`), so both suites admit the same record set through
    the same builder."""
    assert set(order) == set(records), "the order admits exactly the record set"
    writer = _writer_for(corpus)
    values: dict[str, AssessmentValue] = {}
    for name in order:
        mode, node = records[name]
        written = writer.add(node) if mode == "add" else writer.retract(node)
        if written.kind == "assessment":
            values[written.id] = stored.assessment_value(written)
    return Scenario(writer=writer, values=values, roots=roots)


def _scenario(corpus, *, basis: dict[str, Any] | None = None, extra: tuple[Node, ...] = ()) -> Scenario:
    """`_records` admitted in its own order."""
    records = _records(basis=basis, extra=extra)
    roots = DATASET_ROOTS + ((ACQUISITION_WITNESS,) if basis is not None else ())
    return _admit(corpus, records, tuple(records), roots=roots)


def _verification(scenario: Scenario, slug: str, *, scope: str, verdict: str, supersedes: str | None = None) -> Node:
    """One more verification of `assessment:a-1`, minted as a stored record."""
    target = ASSESSMENTS[0]
    return scenario.writer.add(
        stored.verification_node(
            slug,
            title=slug,
            assessment=scenario.values[target].identity(),
            assessment_ref=target,
            scope=scope,
            verdict=verdict,
            supersedes=supersedes,
        )
    )


# --- G2c: the §3.3 lifecycle-table walk, plus the raw-deletion negative -------


@dataclass(frozen=True)
class LifecycleRow:
    """One row of kernel §3.3's table, or one of the two `active` amendments."""

    label: str
    keep_seeded_pass: bool
    """Whether `verification:v-1` — the seeded `clean-environment, passed`
    record — survives. Where it does not, a real `delete` removes it."""

    mint: tuple[tuple[str, str, str, str | None], ...]
    """`(slug, scope, verdict, supersedes)` per verification the row adds."""

    retract: tuple[str, ...]
    """Slugs of the minted verifications a standing retraction then targets."""

    state: str
    belief: int | None
    """The belief `evaluate_over` computes, or `None` for the rows a standing
    retraction decides: the resolver enumerates no retractions, so the amended
    `active` is not visible on that path and asserting a value there would be
    asserting the resolver's bound rather than the row."""


LIFECYCLE_ROWS = (
    LifecycleRow("no-verification-admits-nothing", False, (), (), NOT_ADMITTED, 1),
    LifecycleRow(
        "an-active-failure-invalidates-past-its-passing-sibling",
        True,
        (("v-1-fail", "clean-environment", "failed", None),),
        (),
        INVALIDATED,
        1,
    ),
    LifecycleRow("a-clean-environment-pass-admits", True, (), (), ADMITTED, 2),
    LifecycleRow(
        "a-pass-outside-clean-environment-admits-nothing",
        False,
        (("v-1-same", "same-environment", "passed", None),),
        (),
        NOT_ADMITTED,
        1,
    ),
    LifecycleRow(
        "a-superseded-clean-environment-pass-admits-nothing",
        False,
        (
            ("v-1-old", "clean-environment", "passed", None),
            ("v-1-new", "same-environment", "passed", "verification:v-1-old"),
        ),
        (),
        NOT_ADMITTED,
        1,
    ),
    LifecycleRow(
        "a-standing-retraction-clears-the-failure",
        True,
        (("v-1-fail", "clean-environment", "failed", None),),
        ("v-1-fail",),
        ADMITTED,
        None,
    ),
)
"""The four table rows and the two `active` amendments — a superseded pass
admits nothing, and a standing retraction of the failure restores admission."""


@pytest.mark.parametrize("row", LIFECYCLE_ROWS, ids=lambda row: row.label)
def test_g2c_every_lifecycle_row_over_stored_records(tmp_path, row):
    # Keyed by the row label, not a fixed name: pytest hands consecutive
    # parametrizations of a long test name the *same* `tmp_path`, and two
    # corpora at one root would collide on the first record.
    scenario = _scenario(tmp_path / row.label)
    if not row.keep_seeded_pass:
        scenario.writer.delete("verification:v-1")
    minted = {
        slug: _verification(scenario, slug, scope=scope, verdict=verdict, supersedes=supersedes)
        for slug, scope, verdict, supersedes in row.mint
    }
    for slug in row.retract:
        scenario.writer.retract(retraction_for(minted[slug], "verification:grounds"))

    assert scenario.lifecycle(ASSESSMENTS[0]) == row.state
    assert scenario.lifecycle(ASSESSMENTS[1]) == ADMITTED, "the untouched sibling assessment is unaffected"
    if row.belief is not None:
        assert scenario.belief().value == row.belief


def test_g2c_g8_c6_raw_deletion_restores_admission_undetected_on_read(tmp_path):
    """The negative all three rows share: a raw `unlink` of a failing
    verification returns the assessment to admitted, and nothing on the corpus
    read says so. §3.2's undetectable-history limit, not a tamper-evidence
    claim — the log audit's refutation is the durable module's arm."""
    scenario = _scenario(tmp_path / "corpus")
    failing = _verification(scenario, "v-1-fail", scope="clean-environment", verdict="failed")
    assert scenario.lifecycle(ASSESSMENTS[0]) == INVALIDATED
    invalidated = scenario.belief()
    assert invalidated.value == 1

    os.unlink(path_for(scenario.writer.root, failing.id))
    scenario.writer._reconstruct()

    assert scenario.lifecycle(ASSESSMENTS[0]) == ADMITTED
    restored = scenario.belief()
    assert restored.value == 2
    assert restored.belief_input_digest != invalidated.belief_input_digest
    assert corpus_check(scenario.view, scenario.writer.profile) == (), "the removal is invisible to the read-side check"
    assert audit_corpus(scenario.view, evidence=NO_EVIDENCE, profile=scenario.writer.profile) == (), "and to the corpus-local audit"


# --- G8 and C6: the managed half reads the same; the log half is Task 8's -----


def test_g8_c6_managed_delete_reads_identically_to_raw_on_the_corpus(tmp_path):
    """Two corpora holding the same records, one raw-unlinking the failing
    verification and one calling `delete`: the corpus read, admission and the
    belief digest cannot tell them apart. The log audit can — it reads the
    managed removal as `validated` with `record-removed` and the raw one as
    `refuted` — and that half runs durably (§5 obligation 4)."""
    raw = _scenario(tmp_path / "raw")
    managed = _scenario(tmp_path / "managed")
    failing = {
        label: _verification(scenario, "v-1-fail", scope="clean-environment", verdict="failed")
        for label, scenario in (("raw", raw), ("managed", managed))
    }
    assert raw.lifecycle(ASSESSMENTS[0]) == managed.lifecycle(ASSESSMENTS[0]) == INVALIDATED

    os.unlink(path_for(raw.writer.root, failing["raw"].id))
    raw.writer._reconstruct()
    managed.writer.delete(failing["managed"].id)

    assert sorted(node.id for node in raw.view.iter_stored()) == sorted(
        node.id for node in managed.view.iter_stored()
    )
    assert raw.lifecycle(ASSESSMENTS[0]) == managed.lifecycle(ASSESSMENTS[0]) == ADMITTED
    assert raw.belief().value == managed.belief().value == 2
    assert raw.belief().belief_input_digest == managed.belief().belief_input_digest
    assert corpus_check(raw.view, raw.writer.profile) == corpus_check(managed.view, managed.writer.profile) == ()


# --- S5's deletion half -------------------------------------------------------

ANCESTOR = "dataset:origin"
PRODUCER = "run:origin"
"""`_basis_route("origin")` spells the producing run `run:origin` and the
transformed ancestor `dataset:origin` from one name, so the fixture is named to
match cut 16's helper rather than copying a route literal."""

OTHER_ANCESTOR = "dataset:other"
SECOND_PRODUCER = "run:other"
"""The divergent producer: it reaches the same content address by transforming
something the stamped route does not name."""


def _lineage_corpus(corpus, *, second_producer: bool) -> Scenario:
    """The belief corpus with a stamped derivation on the dataset
    `assessment:a-1`'s run observes: `run:origin` produced `DERIVED` from
    `dataset:origin`, and — optionally — `run:other` produced the same address
    from `dataset:other` by another route, which is R23 negative (e)'s
    divergence and S5's *divergent producer*.

    The derived dataset is the **observed** one, so it is the address
    `belief.evaluate` certifies over: the certification decision reaches the
    belief value, and S5's *belief may rise* is a runnable arm. A separate
    unproduced acquisition witness supplies the first run's eligibility;
    DERIVED carries only its lineage basis, never an acquisition declaration."""
    extra: list[Node] = [
        stored.dataset_node("origin", title="origin", resources=_resources("c")),
        stored.dataset_node("other", title="other", resources=_resources("d")),
        stored.run_node(
            "origin", title="origin", spec="spec-origin", transforms=[ANCESTOR], produces=[DERIVED]
        ),
    ]
    if second_producer:
        extra.append(
            stored.run_node(
                "other", title="other", spec="spec-other", transforms=[OTHER_ANCESTOR], produces=[DERIVED]
            )
        )
    return _scenario(corpus, basis={"tag": "single", "routes": [_basis_route("origin")]}, extra=tuple(extra))


def _projected(snapshot: LineageSnapshot, *path: Any) -> Any:
    """One member of the kernel §5.1 projection, reached by `path`.
    `snapshot_projection` is typed `dict[str, object]`, so a nested read takes
    one deliberate widening here rather than an `object` index at every step."""
    value: Any = snapshot_projection(snapshot)
    for key in path:
        value = value[key]
    return value


def _certification(scenario: Scenario) -> Certification:
    """Exactly the call `belief.evaluate` step 7 makes between the two
    assessments: `certify` over each run's `observes` addresses. Their closures
    are disjoint, so the only thing that can decide it is a finding — and the
    decision is the edge that moves the aggregated belief value."""
    return certify(
        scenario.snapshot(),
        stored.inputs_of(scenario.view.get("run:run-a"), stored.OBSERVES),
        stored.inputs_of(scenario.view.get("run:run-b"), stored.OBSERVES),
    )


def _epistemic_readings(scenario: Scenario) -> dict[str, Any]:
    """§7's scoping made concrete: the readings S5's *indistinguishable* covers
    — the corpus read, the lineage traversal, admission and belief. Log
    verification is deliberately **not** here: a managed deletion is perfectly
    visible in the chain, and the row never claimed otherwise."""
    return {
        "stored_ids": sorted(node.id for node in scenario.view.iter_stored()),
        "lineage": snapshot_projection(scenario.snapshot()),
        "certification": _certification(scenario),
        "belief_input_digest": scenario.belief().belief_input_digest,
        "belief_value": scenario.belief().value,
        "admission": {ref: scenario.lifecycle(ref) for ref in ASSESSMENTS},
    }


def test_s5_deleting_a_basis_ancestor_yields_incomplete_and_moves_the_digest(tmp_path):
    """The deletion half's first arm: an ancestor a stamped basis names is
    deleted, the basis entry goes unresolved, independence over the dataset
    stops certifying, and kernel §5.1's digest moves without belief rising."""
    scenario = _lineage_corpus(tmp_path / "corpus", second_producer=False)
    before = scenario.belief()
    # The certify path is reached, not merely present: an `independent`
    # certification is what lets both supports count, so `value == 2`.
    assert _certification(scenario) == Certification(state="independent", findings=())
    assert before.value == 2

    scenario.writer.delete(ANCESTOR)

    snapshot = scenario.snapshot()
    route = snapshot.bases[DERIVED].routes[0]
    assert route.stored_ancestor == ANCESTOR and route.resolved_ancestor is None
    certification = _certification(scenario)
    assert certification.state == "not-certified"
    assert "lineage-incomplete" in certification.findings
    after = scenario.belief()
    assert after.belief_input_digest != before.belief_input_digest, "kernel §5.1's digest moves"
    assert after.value < before.value, "deleting an ancestor never raises belief; here it lowers it"


def test_s5_deleting_a_divergent_producer_restores_the_certificate_indistinguishably(tmp_path):
    """Corpus X mints `R2` and then deletes it; corpus Y never mints one. Every
    epistemic reading agrees afterwards — and disagrees before, so the
    comparison is not vacuous."""
    diverged = _lineage_corpus(tmp_path / "x", second_producer=True)
    never = _lineage_corpus(tmp_path / "y", second_producer=False)
    assert _certification(diverged) == Certification(state="not-certified", findings=("lineage-divergent",))
    divergent_belief = diverged.belief()
    assert _epistemic_readings(diverged) != _epistemic_readings(never)

    diverged.writer.delete(SECOND_PRODUCER)

    restored = diverged.belief()
    assert restored.value > divergent_belief.value, "the certificate restored, belief rises"
    assert _certification(diverged) == Certification(state="independent", findings=())
    assert _epistemic_readings(diverged) == _epistemic_readings(never)


# --- R23's deletion and audit clauses ----------------------------------------


def test_r23_stored_ref_and_null_resolution_are_recorded_separately(tmp_path):
    """Recording the stored ref alone, or the resolution alone, loses the
    deletion; the projection carries both, for the producing run and for the
    ancestor, and the digest moves for each."""
    for label, doomed, member, stored_ref in (
        ("run", PRODUCER, "producing_run", PRODUCER),
        ("ancestor", ANCESTOR, "ancestor", ANCESTOR),
    ):
        scenario = _lineage_corpus(tmp_path / label, second_producer=False)
        before = scenario.belief()

        scenario.writer.delete(doomed)

        snapshot = scenario.snapshot()
        assert DERIVED in snapshot.bases, "the dataset still carries a basis: it does not read as a root"
        route = snapshot.bases[DERIVED].routes[0]
        assert (route.stored_run, route.stored_ancestor) == (PRODUCER, ANCESTOR)
        assert (route.resolved_run is None) == (doomed == PRODUCER)
        assert (route.resolved_ancestor is None) == (doomed == ANCESTOR)
        projected = _projected(snapshot, "bases", DERIVED, "routes", 0)
        assert projected[member] == {"stored": stored_ref, "resolved": []}
        certification = _certification(scenario)
        assert certification.state == "not-certified"
        assert "lineage-incomplete" in certification.findings
        assert scenario.belief().belief_input_digest != before.belief_input_digest


def test_r23_a_second_surviving_run_does_not_repair_the_first_basis(tmp_path):
    """The basis is one stamped route, not a query over the producer set: a
    second run producing the same address by another route survives the
    deletion and leaves the first basis exactly as unresolved as it was."""
    scenario = _lineage_corpus(tmp_path / "corpus", second_producer=True)

    scenario.writer.delete(PRODUCER)

    snapshot = scenario.snapshot()
    route = snapshot.bases[DERIVED].routes[0]
    assert route.stored_run == PRODUCER and route.resolved_run is None
    surviving = {producer.resolved_run for producer in snapshot.producers[DERIVED]}
    assert surviving == {SECOND_PRODUCER}, "the second run still produces the address"
    certification = _certification(scenario)
    assert certification.state == "not-certified"
    assert "lineage-incomplete" in certification.findings, "the surviving producer repairs nothing"


def test_r23_the_residue_after_deleting_r2(tmp_path):
    """§11.14, worded as R23 words it: certification is restored, no prior
    digest is retained anywhere — belief is a computed view — and no test
    distinguishes the corpus from one in which `R2` never existed."""
    residue = _lineage_corpus(tmp_path / "residue", second_producer=True)
    never = _lineage_corpus(tmp_path / "never", second_producer=False)
    diverged_digest = residue.belief().belief_input_digest

    residue.writer.delete(SECOND_PRODUCER)

    assert _certification(residue).state == "independent"
    assert _epistemic_readings(residue) == _epistemic_readings(never)
    assert residue.belief().belief_input_digest != diverged_digest
    on_disk = [path.read_bytes() for path in residue.writer.root.rglob("*") if path.is_file()]
    assert on_disk, "the scan actually read the corpus"
    assert not any(diverged_digest.encode() in payload for payload in on_disk), "no retained prior digest"


def test_r23_the_audit_detects_a_forged_single_while_b_stands_then_reports_no_contradiction(tmp_path):
    """`single(A)` forged by a raw write while `B`'s run stands is contradicted
    by recomputation; once `B`'s run is deleted, nothing contradicts it. §7:
    the assertion is the **absence of the semantic contradiction code**, never
    the absence of all findings — the log audit still reports the committed
    removal."""
    writer = _writer(tmp_path / "corpus")
    run_b = forged_single_over_two_producers(writer)
    assert "lineage-basis-contradicted" in {
        finding.code for finding in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
    }

    writer.delete(run_b.id)

    assert "lineage-basis-contradicted" not in {
        finding.code for finding in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
    }


# --- W16's remaining arm ------------------------------------------------------

CONFLICT_ROUTES = ("a", "z")
"""The two routes `_duplicate_datasets`' inputs carry; consolidation unions them
into the survivor's `conflict` basis, sorted."""


@pytest.mark.parametrize("doomed", CONFLICT_ROUTES)
def test_w16_the_conflict_survives_deleting_either_producing_run(tmp_path, doomed):
    """Deleting a producing run resolves nothing: unlike the single-basis case,
    where the deletion is what makes the lineage incomplete, a `conflict` is
    decided on its tag and no API removes a route."""
    keep_writer, other_writer, keep, other = _duplicate_datasets(tmp_path / doomed)
    survivor, _, _ = relocation.consolidate(
        (keep_writer, keep.id), (other_writer, other.id), **CONSOLIDATE_FIELDS
    )
    assert stored.lineage_basis(survivor) == {
        "tag": "conflict",
        "routes": [_basis_route("a"), _basis_route("z")],
    }
    for name in CONFLICT_ROUTES:
        keep_writer.add(
            stored.run_node(
                name, title=name, spec=f"spec-{name}", transforms=[f"dataset:{name}"], produces=[survivor.id]
            )
        )
    sibling = keep_writer.add(stored.dataset_node("sibling", title="sibling", resources=_resources("f")))
    roots = (survivor.id, sibling.id)
    divergent = Certification(state="not-certified", findings=("lineage-divergent",))
    assert certify(lineage_snapshot(keep_writer.read_view, roots), (survivor.id,), (sibling.id,)) == divergent

    keep_writer.delete(f"run:{doomed}")

    assert keep_writer.read_view.resolve(f"run:{doomed}") is None, "the producing run really is gone"
    node = keep_writer.read_view.get(survivor.id)
    basis = stored.lineage_basis(node)
    assert basis is not None and basis["tag"] == "conflict"
    assert [route["run"] for route in stored.basis_routes(node)] == [f"run:{name}" for name in CONFLICT_ROUTES]
    snapshot = lineage_snapshot(keep_writer.read_view, roots)
    assert _projected(snapshot, "divergence", survivor.id) == "divergent"
    assert certify(snapshot, (survivor.id,), (sibling.id,)) == divergent


# --- M3's admission-order negative -------------------------------------------

RANKING_MEMBERS = frozenset(
    {"rank", "order", "position", "sequence", "topological_rank", "topological_order", "admission_order"}
)
"""What a stored topological rank would have to be called. M3's negative is
that none of them exists: `standing` terminates because the retraction graph
is a DAG, not because an ordering was recorded when the records arrived."""


def _facet_members(value: Any) -> set[str]:
    """Every mapping key reachable inside a facet payload, at any depth."""
    if isinstance(value, dict):
        return set(value) | {key for member in value.values() for key in _facet_members(member)}
    if isinstance(value, (list, tuple)):
        return {key for member in value for key in _facet_members(member)}
    return set()


ORDER_A = (
    "p", "q",
    "d-a", "run-a", "a-1", "v-1",
    "d-b", "run-b", "a-2", "v-2",
    "retraction", "counter",
)
ORDER_B = (
    "q", "d-b", "run-b", "a-2", "v-2",
    "retraction", "p",
    "d-a", "run-a", "a-1", "v-1",
    "counter",
)
"""Two admission orders over `_records(retraction_chain=True)`. Both respect the
only orderings the write boundary itself demands — an assessment's run resolves
first (S7), and a retraction's target resolves first (C10) — and agree on
nothing else. The retraction chain is what makes this M3's negative rather than
a generic ordering test."""


def test_m3_admission_order_leaves_every_identity_and_the_digest_unchanged(tmp_path):
    """M3's negative: no topological rank is stored anywhere, so the same
    records admitted in two orders leave every stored identity and the belief
    digest exactly where they were."""
    records = _records(retraction_chain=True)
    assert set(ORDER_A) == set(records), "the declared orders cover the builder's record set"
    first = _admit(tmp_path / "first", records, ORDER_A)
    second = _admit(tmp_path / "second", records, ORDER_B)

    identities = [
        {node.id: stored.stored_semantic_hash(node) for node in scenario.view.iter_stored()}
        for scenario in (first, second)
    ]
    assert sorted(identities[0]) == sorted(identities[1]) == sorted(node.id for _, node in records.values())
    assert identities[0] == identities[1]
    assert first.belief().belief_input_digest == second.belief().belief_input_digest
    for scenario in (first, second):
        for node in scenario.view.iter_stored():
            assert _facet_members(node.facets) & RANKING_MEMBERS == set(), f"{node.id} carries a stored rank"


# --- M5, portable half (the durable re-run is Task 8) -------------------------

CHILDREN = "EX:children"
"""A second cohort term, so a restriction can differ with everything else
held fixed."""

SETTING = OTHER_GENE
"""The `testing/setting` dimension's restriction sort is `entity`, so its term
comes from the same vocabulary the arguments do."""

QUALIFIED = {
    **CLAIM_FACET,
    "qualifiers": {"testing/population": {"quantifier": "generic", "restriction": ADULTS}},
}
M5_VARIANTS = {
    "qualified": QUALIFIED,
    "restriction": {**QUALIFIED, "qualifiers": {"testing/population": {"quantifier": "generic", "restriction": CHILDREN}}},
    "quantifier": {**QUALIFIED, "qualifiers": {"testing/population": {"quantifier": "universal", "restriction": ADULTS}}},
    "unqualified": {**QUALIFIED, "qualifiers": {}},
}
"""One qualification difference each, against a claim otherwise byte-identical:
restriction only, quantifier tag only, and one omitting the dimension the other
carries."""


@pytest.fixture()
def claim_profile(base_contract, testing_contract_path):
    """The compiled profile the restore seam types a claim against. Built here
    rather than imported from `test_decode`: importing a pytest fixture
    function by name and taking it as a same-named parameter reads to ruff as a
    redefinition (F811), which `test_claim_restore.py` records at length. That
    argument is about the fixture name only — its two callees are ordinary
    module-level imports."""
    testing = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim_snapshot():
    return build_snapshot(readable={EX: [GENE, PHENO, SETTING], COHORT_DATASET: [ADULTS, CHILDREN]})


def test_m5_qualification_participates_in_stored_identity(tmp_path, claim_profile, claim_snapshot):
    """Restriction only, quantifier tag only, and one omitting the dimension
    the others carry: each moves the record's stored semantic identity and each
    moves `I_claim` through the restore seam."""
    writer = _writer(tmp_path / "corpus")
    minted = {
        name: writer.add(stored.proposition_node(f"p-{name}", title=name, claim=facet))
        for name, facet in M5_VARIANTS.items()
    }
    stamps = {name: stored.stored_semantic_hash(node) for name, node in minted.items()}
    identities = {
        name: claim_identity(claim_from_stored(node, profile=claim_profile, snapshot=claim_snapshot)[0])
        for name, node in minted.items()
    }

    assert None not in stamps.values()
    assert len(set(stamps.values())) == len(M5_VARIANTS), "each qualification difference moves the stored identity"
    assert len(set(identities.values())) == len(M5_VARIANTS), "and moves I_claim"


def test_m5_qualifier_key_order_leaves_the_identity_unchanged(tmp_path, claim_profile, claim_snapshot):
    """The negative: the same qualification, re-serialized with its keys in a
    different order, is the same claim. `science.identity.v1` sorts object keys
    at encode time, so neither the stored stamp nor `I_claim` moves."""
    population = {"quantifier": "generic", "restriction": ADULTS}
    setting = {"quantifier": "generic", "restriction": SETTING}
    forward = {**CLAIM_FACET, "qualifiers": {"testing/population": population, "testing/setting": setting}}
    reversed_keys = {
        **CLAIM_FACET,
        "qualifiers": {
            "testing/setting": {"restriction": SETTING, "quantifier": "generic"},
            "testing/population": {"restriction": ADULTS, "quantifier": "generic"},
        },
    }
    writer = _writer(tmp_path / "corpus")
    nodes = [
        writer.add(stored.proposition_node(f"p-{name}", title=name, claim=facet))
        for name, facet in (("forward", forward), ("reversed", reversed_keys))
    ]

    forward_identity, reversed_identity = (
        claim_identity(claim_from_stored(node, profile=claim_profile, snapshot=claim_snapshot)[0]) for node in nodes
    )
    assert stored.stored_semantic_hash(nodes[0]) == stored.stored_semantic_hash(nodes[1])
    assert forward_identity == reversed_identity
