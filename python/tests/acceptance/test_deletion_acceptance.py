"""Cut 18's durable arms: managed deletion on the certified engine and volume.

Every selected behaviour of `docs/designs/2026-09-04-conformance-cut-18.md` §3
runs twice — portably, in `tests/test_deletion*.py` and the row modules it
names, and again here through `open_corpus` on a **registered** root. Only this
module supports a discharge claim (§5 obligation 2), and it never skips: the
`durable_root` fixture errors when the configuration tuple is uncertified.

One test per declaration unit, named for its row. Each body mirrors its
portable twin and additionally **reloads the view** — `open_corpus` for a
writer-backed reading, `reopen` for a bare one — before asserting, so every
assertion is about bytes the engine committed rather than about an index a
live facade happens to hold.

Two obligations are this module's alone:

- **G8's asymmetry** (§5 obligation 4) runs through `root.audit_log` over a
  real chain: a raw `unlink` reads **refuted**, and a managed `delete` of the
  same record reads **validated** with `record-removed` and, given the held
  copy, `failing-verification-removed` at error severity.
- **`delete`'s chain shape**: one registered transaction whose final states the
  removed path as `absent`, with **no** intent entry appended for it — the
  ordinary-write claim §3.1 makes, asserted where the entries actually are.

§7's two narrowings are honoured exactly as the portable module honours them:
S5's *indistinguishable* is compared over the epistemic readings only, never
over log verification, and R23's *the audit reports nothing* is the absence of
the semantic contradiction code, never of all findings.
"""

from __future__ import annotations

import inspect
import os
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from itertools import count
from pathlib import Path

import pytest
from atoms.chain.inspect import WellFormedChain
from atoms.chain.model import IntentEntry, RegisteredEntry, SettledEntry
from atoms.coordinator.commands import inspect_chain_detached
from atoms.fs.linux import LinuxBackend
from authority import FULL
from fixtures_cut4 import path_for, raw_write, reopen
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from profiles import BASE, WITH_BIOLOGY
from test_audit import forged_single_over_two_producers, raw_cyclic_retraction_pair
from test_belief import CLAIM, PROFILE, PROPOSITION
from test_claim_restore import stored_proposition
from test_decode import ADULTS, COHORT_DATASET, OUTCOME, affects
from test_deletion import _stored_act_report, retraction_for
from test_deletion_rows import ANCESTOR as BASIS_ANCESTOR
from test_deletion_rows import (
    ASSESSMENTS,
    CHILDREN,
    CONFLICT_ROUTES,
    DERIVED,
    LIFECYCLE_ROWS,
    M5_VARIANTS,
    ORDER_A,
    ORDER_B,
    PRODUCER,
    RANKING_MEMBERS,
    SECOND_PRODUCER,
    SETTING,
    Scenario,
    _admit,
    _certification,
    _epistemic_readings,
    _facet_members,
    _lineage_corpus,
    _projected,
    _records,
    _scenario,
    _verification,
)
from test_durable_families import chain_entries
from test_evaluation import (
    CLAIM_FACET,
    EX,
    GENE,
    OTHER_GENE,
    PHENO,
    PROPOSITION_REF,
    _fixture,
    _resources,
)
from test_import_derivation import (
    ASSESSMENT_REF,
    CONTRACT,
    EPOCH,
    IMPORT_FIELDS,
    _admission,
    _assessment_node_from,
    _flip,
    _report_findings,
    _stored_from,
    _two_runs,
)
from test_relocation import CONSOLIDATE_FIELDS, SCIENCE
from test_relocation_rows import _basis_route, _duplicate_datasets
from test_retract import mint_eligible_assessment

from beliefs import belief as belief_module
from beliefs import corpus as corpus_module
from beliefs import decode, evaluation, relocation, stored
from beliefs import root as science_root
from beliefs.admission import AdmissionRefused, admit
from beliefs.assess import build_assessment
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.belief import Availability, Belief, NoBelief, Records, SuppliedContext, evaluate
from beliefs.claim import Claim
from beliefs.closure import RetractionEnumeration
from beliefs.consulted import CorpusPins
from beliefs.corpus import CorpusWriter, ReadView, corpus_check, lineage_snapshot
from beliefs.dataset import DatasetDeclaration, Declared, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.decode import claim_from_stored, decode_claim
from beliefs.errors import (
    DeletionKindExcluded,
    ImportRefused,
    MalformedWireClaim,
    RelocationTargetMissing,
)
from beliefs.evaluation import gather
from beliefs.holdings.adapter import DatasetAnswer, dataset_observations
from beliefs.holdings.boundary import ActContext
from beliefs.holdings.boundary import delete as holdings_delete
from beliefs.holdings.boundary import write as holdings_write
from beliefs.holdings.receipt import derive_holdings
from beliefs.holdings.records import Absent, Found, StoreLocator
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.lineage import Certification, LineageSnapshot, certify
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.projection import claim_identity, project_claim
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.resolution import BindingCheckReceipt, build_snapshot
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.runrecord import run_ref
from beliefs.verification import ADMITTED, INVALIDATED, Verification
from beliefs.verify import AssessmentVerification, build_verification
from beliefs.world import anchors, registry, rules, verify

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_CONTRACT = REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"
TESTING_CONTRACT = REPO_ROOT / "fixtures" / "contracts" / "testing.yaml"

DEFAULT_PINS = CorpusPins(SCIENCE, {})
"""What `test_relocation._writer` adopts, so a durable corpus and its portable
twin are pinned to one contract set and an import across them is comparable."""

_COUNTER = count()


# --- the durable roots --------------------------------------------------------


def _adopted(writer: CorpusWriter, pins: CorpusPins = DEFAULT_PINS) -> CorpusWriter:
    """The manifest the portable writer adopts, adopted here too.

    `durable_root` registers a root and stops; the pins are a separate act, and
    every row that imports, consolidates or is audited needs them."""
    writer.adopt_manifest(profile=pins)
    return writer


@contextmanager
def _durable_corpora(
    work: Path, *labels: str, pins: CorpusPins = DEFAULT_PINS
) -> Iterator[tuple[CorpusWriter, ...]]:
    """Registered corpus roots beside `work`, removed with their metadata peers.

    Several rows need more than one corpus — a walk of six lifecycle rows, a
    consolidation, an indistinguishability comparison — and the acceptance
    fixtures hand out one. Registration failure is **not** caught: an
    uncertified tuple must reach the runner as the engine's own refusal.
    """
    roots: list[Path] = []
    try:
        writers: list[CorpusWriter] = []
        for label in labels:
            root = work / f"cut18-{os.getpid()}-{next(_COUNTER)}-{label}"
            init_corpus_root(root, authority=FULL)
            roots.append(root)
            writers.append(_adopted(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY if pins == PINS else BASE), pins))
        yield tuple(writers)
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _reloaded(scenario: Scenario) -> Scenario:
    """The same scenario over a corpus opened afresh from disk.

    Every durable assertion below reads through one of these: a live facade
    indexes at construction, so an assertion made on it is an assertion about
    the process's memory. This one is about the committed bytes.
    """
    return Scenario(writer=open_corpus(scenario.writer.root, authority=FULL, profile=scenario.writer.profile), values=scenario.values, roots=scenario.roots)


def _assert_delete_chain(root: Path, before: int, path: str) -> None:
    """`delete`'s committed shape (§3.1): **one** registered transaction whose
    final states `path` as `absent`, its settlement, and **no intent** — the
    ordinary-write claim, read off the chain rather than off a recorder."""
    added = chain_entries(root)[before:]
    assert [type(entry).__name__ for _, entry in added] == ["RegisteredEntry", "SettledEntry"]
    registration, settlement = added[0][1], added[1][1]
    assert isinstance(registration, RegisteredEntry) and isinstance(settlement, SettledEntry)
    assert not any(isinstance(entry, IntentEntry) for _, entry in added), "delete appends no intent"
    assert registration.fulfills is None, "delete fulfils no intent"
    assert registration.final == ((path, (("kind", "absent"),)),)
    assert settlement.registration == added[0][0]


def _log_observer(root: Path, corpus_id: str) -> verify.RegistryCarrier:
    """A registry log-head record anchoring the root's present chain tip — the
    `named-local` carrier `test_lifecycle_wrappers.py` builds for the same act."""
    inspected = inspect_chain_detached(LinuxBackend(), str(root))
    assert type(inspected) is WellFormedChain, inspected
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.CorpusSubject(corpus_id),
            inspected.entries[0][0],
            inspected.tip,
            anchors.AnchorActOrigin("alice"),
        )
    )


def _audit_log(writer: CorpusWriter, *, history: dict[str, bytes] | None = None) -> verify.LogReport:
    """The log audit over one registered root, anchored at its own tip."""
    corpus_id = writer.corpus_id
    return science_root.audit_log(
        science_root.WorldConfig(writer.root.parent / f"{writer.root.name}-world", "f" * 32, (writer.root,)),
        anchors.CorpusSubject(corpus_id),
        writer.root,
        verify.ObserverSet((_log_observer(writer.root, corpus_id),)),
        actor="alice",
        history=history,
    )


def _rendered(view: ReadView, ref: str) -> bytes:
    """A stored record's bytes as `history` carries them (`world/verify.py`'s
    `_held_records` decodes exactly this form)."""
    return node_to_markdown(view.get(ref)).encode("utf-8")


def _files(root: Path) -> list[Path]:
    """Every file under a root, the chain included — what "mints nothing"
    means when the claim is that no act ran at all."""
    return sorted(path for path in root.rglob("*") if path.is_file())


def _record_files(root: Path) -> list[Path]:
    """The stored records only. A refused import still appends chain entries
    and still mints the import family's own refusal report; what the row
    claims is that no **bundle member** landed."""
    return sorted(root.rglob("*.md"))


def _view_writer(writer: CorpusWriter):
    """`test_import_derivation._admission` reads `w.read_view`; hand it a
    corpus opened afresh so the admission it computes is over committed bytes."""
    return open_corpus(writer.root, authority=FULL, profile=writer.profile)


# --- G2c ----------------------------------------------------------------------


def test_g2c_lifecycle_walk_over_durable_records(durable_writer):
    """Kernel §3.3's lifecycle table, every row walked over durable records,
    with `active` read under the standing-retraction amendment; `delete`'s
    committed chain shape where a row removes the seeded pass; and the
    raw-deletion negative G2c, G8 and C6 share — admission restored, and the
    corpus read says nothing about it."""
    work = durable_writer.root.parent
    labels = [row.label for row in LIFECYCLE_ROWS[1:]]
    with _durable_corpora(work, *labels, "raw-negative") as extra:
        for row, writer in zip(LIFECYCLE_ROWS, (_adopted(durable_writer), *extra[:-1]), strict=True):
            scenario = _scenario(writer)
            if not row.keep_seeded_pass:
                before = len(chain_entries(writer.root))
                scenario.writer.delete("verification:v-1")
                _assert_delete_chain(writer.root, before, "verification/v-1.md")
            minted = {
                slug: _verification(scenario, slug, scope=scope, verdict=verdict, supersedes=supersedes)
                for slug, scope, verdict, supersedes in row.mint
            }
            for slug in row.retract:
                scenario.writer.retract(retraction_for(minted[slug], "verification:grounds"))

            reloaded = _reloaded(scenario)
            assert reloaded.lifecycle(ASSESSMENTS[0]) == row.state, row.label
            assert reloaded.lifecycle(ASSESSMENTS[1]) == ADMITTED, "the untouched sibling assessment is unaffected"
            if row.belief is not None:
                assert reloaded.belief().value == row.belief, row.label

        raw = _scenario(extra[-1])
        failing = _verification(raw, "v-1-fail", scope="clean-environment", verdict="failed")
        invalidated = _reloaded(raw)
        assert invalidated.lifecycle(ASSESSMENTS[0]) == INVALIDATED
        before_belief = invalidated.belief()
        assert before_belief.value == 1

        os.unlink(path_for(raw.writer.root, failing.id))

        restored = _reloaded(raw)
        assert restored.lifecycle(ASSESSMENTS[0]) == ADMITTED
        after_belief = restored.belief()
        assert after_belief.value == 2
        assert after_belief.belief_input_digest != before_belief.belief_input_digest
        assert corpus_check(restored.view, restored.writer.profile) == (), "the removal is invisible to the read-side check"
        assert audit_corpus(restored.view, evidence=NO_EVIDENCE, profile=restored.writer.profile) == (), "and to the corpus-local audit"


# --- G8 and C6: the log half (§5 obligation 4) --------------------------------


def test_g8_c6_raw_removal_refutes_and_managed_delete_validates(work_directory, durable_root):
    """The asymmetry §3.1 tables, read where it is actually visible. Two
    registered corpora hold the same records; one raw-`unlink`s the failing
    verification and one calls `delete`. The **corpus** read cannot tell them
    apart — same stored ids, same admission, same belief digest — and the
    **log** audit can: the raw removal is `refuted`, the managed one is
    `validated` carrying `record-removed` and, resolved against the caller's
    held copy, `failing-verification-removed` at error severity."""
    raw_writer = _adopted(open_corpus(durable_root, authority=FULL, profile=BASE))
    with _durable_corpora(work_directory, "g8-managed") as (managed_writer,):
        raw = _scenario(raw_writer)
        managed = _scenario(managed_writer)
        failing = {
            label: _verification(scenario, "v-1-fail", scope="clean-environment", verdict="failed")
            for label, scenario in (("raw", raw), ("managed", managed))
        }
        # §5.3's held copy: each arm's own record, as it reads back off disk,
        # filed under the digest of those exact bytes. The classification then
        # resolves it by the corpus path the record's identity claims.
        history = {}
        for label, scenario in (("raw", raw), ("managed", managed)):
            payload = _rendered(_reloaded(scenario).view, failing[label].id)
            history[label] = {f"sha256:{sha256(payload).hexdigest()}": payload}
        assert _reloaded(raw).lifecycle(ASSESSMENTS[0]) == INVALIDATED
        assert _reloaded(managed).lifecycle(ASSESSMENTS[0]) == INVALIDATED

        os.unlink(path_for(raw_writer.root, failing["raw"].id))
        managed_writer.delete(failing["managed"].id)

        raw_view, managed_view = _reloaded(raw), _reloaded(managed)
        assert sorted(node.id for node in raw_view.view.iter_stored()) == sorted(
            node.id for node in managed_view.view.iter_stored()
        )
        assert raw_view.lifecycle(ASSESSMENTS[0]) == managed_view.lifecycle(ASSESSMENTS[0]) == ADMITTED
        assert raw_view.belief().value == managed_view.belief().value == 2
        assert raw_view.belief().belief_input_digest == managed_view.belief().belief_input_digest
        assert corpus_check(raw_view.view, raw_view.writer.profile) == corpus_check(managed_view.view, managed_view.writer.profile) == ()

        raw_report = _audit_log(raw_writer, history=history["raw"])
        managed_report = _audit_log(managed_writer, history=history["managed"])

        assert raw_report.outcome == "refuted"
        assert managed_report.outcome == "validated"
        assert [finding.code for finding in managed_report.findings] == [
            "record-removed",
            "failing-verification-removed",
        ]
        assert [finding.severity for finding in managed_report.findings] == ["warning", "error"]
        assert all(finding.ref == "verification/v-1-fail.md" for finding in managed_report.findings)


# --- R5: the managed holdings deletion as the last-held-copy transition -------


R5_CONTENT = b"the observed bytes cut 18 unholds"
R5_DECLARATION = DatasetDeclaration(
    (ResourceDeclaration("data", f"sha256:{sha256(R5_CONTENT).hexdigest()}"),)
)
"""The observed dataset, declared at the digest the store act will establish, so
the reduction's head and the declaration join and the input reads **held**."""


def _r5_records() -> Records:
    """One supporting assessment over one run observing `R5_DECLARATION`, with
    its admitting verification: the smallest corpus in which unholding the
    input is unholding the **last** directional one (P9)."""
    assessment = AssessmentValue(
        spec="spec-a", run="run-a", proposition=PROPOSITION, outcome="supported", interpretation_rule="rule-1"
    )
    run = RunValue(ref="run-a", spec="spec-a", inputs=(RunInput(role="observes", dataset=R5_DECLARATION),))
    verification = Verification(
        ref="v-a", assessment=assessment.identity(), scope="clean-environment", verdict="passed"
    )
    return Records(
        claims={PROPOSITION: CLAIM},
        assessments=(assessment,),
        runs={"run-a": run},
        source_assertions=(),
        verifications=(verification,),
    )


def test_r5_the_managed_holdings_delete_ends_heldness_and_changes_admission(certified_work):
    """R5 negative (a): the last held copy of an `observes` input is destroyed
    by the **managed** act — `holdings.boundary.delete`, which publishes an
    `absent` observation superseding the write's — and the whole reduction is
    re-run over the committed records. The dataset is no longer held, the
    input's eligibility fails, and admission changes: `NoBelief`, never a
    silently unchanged value."""
    corpus_root, store_root = certified_work / "observer", certified_work / "store"
    init_corpus_root(corpus_root, authority=FULL)
    manifest = open_corpus(corpus_root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
    store_id = science_root.init_store_root(store_root, authority=FULL)
    context = ActContext(
        corpus_root, store_root, "observer", "instrument", FULL, science_root.holdings_seam(), profile=WITH_BIOLOGY
    )
    location = StoreLocator(store_id, "data.bin")

    published = holdings_write(context, location, R5_CONTENT)
    assert published.record.outcome == Found(f"sha256:{sha256(R5_CONTENT).hexdigest()}")

    config = registry.WorldConfig(certified_work / "world", "f" * 32, (corpus_root,))
    science_root.init_world_root(config, authority=FULL)
    world = science_root.open_world(config, authority=FULL)
    world.admit(corpus_root, provenance=registry.Fresh())
    binding = rules.install_rule_binding(world, holdings_rule_bundle())
    seam = science_root._log_seam()

    def observations() -> DatasetAnswer:
        """The reduction, run again over whatever the corpus now holds: chain
        heads and stored observation records in, one dataset answer out."""
        active, blocked, _receipt = derive_holdings(
            world,
            frozenset({manifest.corpus_id}),
            binding,
            chain_view=seam.inspect_registered,
            state_facts=seam.state_facts,
        )
        answer = dataset_observations(R5_DECLARATION, active, blocked)
        assert isinstance(answer, DatasetAnswer), answer
        return answer

    records = _r5_records()
    address = dataset_address(R5_DECLARATION)
    assert address is not None
    context_for_belief = SuppliedContext(
        snapshot=LineageSnapshot(roots=(address,), bases={}, producers={}),
        producer_snapshot_identity="producer-snapshot-1",
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        node_corpus={records.assessments[0].identity(): "c1"},
        pins={"c1": CorpusPins(science_contract="sci-1", domains={"testing": "testing-1"})},
    )

    def answer_for(held: DatasetAnswer):
        return evaluate(
            proposition=PROPOSITION,
            records=records,
            availability=Availability(
                observations={address: held.observations},
                implementations={BELIEF_V1.identity: BELIEF_V1},
                fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
            ),
            context=context_for_belief,
            binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
            profile=PROFILE,
        )

    while_held = observations()
    assert isinstance(admission_state(R5_DECLARATION, while_held.observations), Held)
    belief = answer_for(while_held)
    assert isinstance(belief, Belief) and belief.value == 1

    removed = holdings_delete(context, location, standing=(published.record,))

    assert removed.record.outcome == Absent(), "the managed act published the absent observation"
    assert stored.holdings_observation_value(
        reopen(corpus_root).get(f"holdings-observation:{removed.record.identity()}")
    ).outcome == Absent(), "and it is that published record the reduction reads"
    after = observations()
    assert after == DatasetAnswer(()), "the dataset is no longer held"
    state = admission_state(R5_DECLARATION, after.observations)
    assert isinstance(state, Declared)
    assert [finding.outcome for finding in state.findings] == ["no-matching-observation-in-coverage"]
    eligibility = admit(
        records.assessments[0], records.runs["run-a"], {address: after.observations}, records.verifications
    )
    assert isinstance(eligibility, AdmissionRefused) and eligibility.reason.startswith("input-not-held")
    assert answer_for(after) == NoBelief("unavailable-input-unheld"), "admission changed; belief is not recomputed"


# --- S5's deletion half -------------------------------------------------------


def test_s5_deletion_half_durably(durable_writer):
    """Delete an ancestor a stamped basis names → `lineage-incomplete`,
    `not-certified`, the belief digest moved and no belief rise. Then delete a
    **divergent producer** → the certificate restored, belief rises, and every
    epistemic reading agrees with a corpus in which that run never existed.
    §7's scoping: the log is not one of those readings and is never compared."""
    work = durable_writer.root.parent
    with _durable_corpora(work, "s5-diverged", "s5-never") as (diverged_root, never_root):
        ancestor = _lineage_corpus(_adopted(durable_writer), second_producer=False)
        before = _reloaded(ancestor)
        assert _certification(before) == Certification(state="independent", findings=())
        before_belief = before.belief()
        assert before_belief.value == 2

        ancestor.writer.delete(BASIS_ANCESTOR)

        after = _reloaded(ancestor)
        route = after.snapshot().bases[DERIVED].routes[0]
        assert route.stored_ancestor == BASIS_ANCESTOR and route.resolved_ancestor is None
        certification = _certification(after)
        assert certification.state == "not-certified"
        assert "lineage-incomplete" in certification.findings
        after_belief = after.belief()
        assert after_belief.belief_input_digest != before_belief.belief_input_digest, "kernel §5.1's digest moves"
        assert after_belief.value < before_belief.value, "deleting an ancestor never raises belief"

        diverged = _lineage_corpus(diverged_root, second_producer=True)
        never = _lineage_corpus(never_root, second_producer=False)
        assert _certification(_reloaded(diverged)) == Certification(
            state="not-certified", findings=("lineage-divergent",)
        )
        divergent_belief = _reloaded(diverged).belief()
        assert _epistemic_readings(_reloaded(diverged)) != _epistemic_readings(_reloaded(never))

        diverged.writer.delete(SECOND_PRODUCER)

        restored = _reloaded(diverged)
        assert restored.belief().value > divergent_belief.value, "the certificate restored, belief rises"
        assert _certification(restored) == Certification(state="independent", findings=())
        assert _epistemic_readings(restored) == _epistemic_readings(_reloaded(never))


# --- R23's deletion and audit clauses -----------------------------------------


def test_r23_deletion_and_audit_clauses_durably(durable_writer):
    """The stored ref and its `null` resolution recorded **separately**, for a
    deleted producing run and for a deleted ancestor; a second surviving run
    repairing nothing; §11.14's residue after deleting `R2`; and the audit's
    contradiction of a forged `single(A)` disappearing once `B`'s run is gone —
    §7, the absence of the semantic code, never of all findings."""
    work = durable_writer.root.parent
    labels = ("r23-ancestor", "r23-second", "r23-residue", "r23-never", "r23-forged")
    with _durable_corpora(work, *labels) as (ancestor, second, residue, never_writer, forged):
        separated = (
            (PRODUCER, "producing_run", _adopted(durable_writer)),
            (BASIS_ANCESTOR, "ancestor", ancestor),
        )
        for doomed, member, writer in separated:
            scenario = _lineage_corpus(writer, second_producer=False)
            before = _reloaded(scenario).belief()

            scenario.writer.delete(doomed)

            reloaded = _reloaded(scenario)
            snapshot = reloaded.snapshot()
            assert DERIVED in snapshot.bases, "the dataset still carries a basis: it does not read as a root"
            route = snapshot.bases[DERIVED].routes[0]
            assert (route.stored_run, route.stored_ancestor) == (PRODUCER, BASIS_ANCESTOR)
            assert (route.resolved_run is None) == (doomed == PRODUCER)
            assert (route.resolved_ancestor is None) == (doomed == BASIS_ANCESTOR)
            assert _projected(snapshot, "bases", DERIVED, "routes", 0)[member] == {
                "stored": doomed,
                "resolved": [],
            }, "the stored ref and its null resolution are recorded separately"
            certification = _certification(reloaded)
            assert certification.state == "not-certified"
            assert "lineage-incomplete" in certification.findings
            assert reloaded.belief().belief_input_digest != before.belief_input_digest

        surviving = _lineage_corpus(second, second_producer=True)
        surviving.writer.delete(PRODUCER)
        reloaded = _reloaded(surviving)
        snapshot = reloaded.snapshot()
        route = snapshot.bases[DERIVED].routes[0]
        assert route.stored_run == PRODUCER and route.resolved_run is None
        assert {producer.resolved_run for producer in snapshot.producers[DERIVED]} == {SECOND_PRODUCER}
        certification = _certification(reloaded)
        assert certification.state == "not-certified"
        assert "lineage-incomplete" in certification.findings, "the surviving producer repairs nothing"

        residue_scenario = _lineage_corpus(residue, second_producer=True)
        never_scenario = _lineage_corpus(never_writer, second_producer=False)
        diverged_digest = _reloaded(residue_scenario).belief().belief_input_digest

        residue_scenario.writer.delete(SECOND_PRODUCER)

        reloaded = _reloaded(residue_scenario)
        assert _certification(reloaded).state == "independent"
        assert _epistemic_readings(reloaded) == _epistemic_readings(_reloaded(never_scenario))
        assert reloaded.belief().belief_input_digest != diverged_digest
        on_disk = [path.read_bytes() for path in _files(residue_scenario.writer.root)]
        assert on_disk, "the scan actually read the corpus"
        assert not any(diverged_digest.encode() in payload for payload in on_disk), "no retained prior digest"

        run_b = forged_single_over_two_producers(forged)
        assert "lineage-basis-contradicted" in {
            finding.code for finding in audit_corpus(reopen(forged.root), evidence=NO_EVIDENCE, profile=forged.profile)
        }

        forged.delete(run_b.id)

        # §7: the **semantic** contradiction is gone. This arm reads the
        # semantic audit only; that the log still reports the removal the
        # transaction committed is the G8/C6 arm's property, established there
        # over `root.audit_log`.
        assert "lineage-basis-contradicted" not in {
            finding.code for finding in audit_corpus(reopen(forged.root), evidence=NO_EVIDENCE, profile=forged.profile)
        }


# --- W16's remaining arm ------------------------------------------------------


def test_w16_conflict_survives_deleting_either_producer_durably(work_directory):
    """A consolidated `conflict` basis is decided on its **tag**, and no API
    removes a route: deleting either producing run leaves both routes stored,
    the dataset `lineage-divergent`, and independence over it `not-certified`.
    Unlike the single-basis case, the deletion resolves nothing."""
    for doomed in CONFLICT_ROUTES:
        with _durable_corpora(
            work_directory, f"w16-{doomed}-keep", f"w16-{doomed}-other", pins=PINS
        ) as writers:
            # The record construction is `test_relocation_rows`' own; only the
            # two corpora are this module's, so it needs no scratch path.
            keep_writer, other_writer, keep, other = _duplicate_datasets(None, writers=writers)
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
                        name,
                        title=name,
                        spec=f"spec-{name}",
                        transforms=[f"dataset:{name}"],
                        produces=[survivor.id],
                    )
                )
            sibling = keep_writer.add(
                stored.dataset_node("sibling", title="sibling", resources=_resources("f"))
            )
            roots = (survivor.id, sibling.id)
            divergent = Certification(state="not-certified", findings=("lineage-divergent",))
            assert certify(lineage_snapshot(reopen(keep_writer.root), roots), (survivor.id,), (sibling.id,)) == (
                divergent
            )

            keep_writer.delete(f"run:{doomed}")

            view = reopen(keep_writer.root)
            assert view.resolve(f"run:{doomed}") is None, "the producing run really is gone"
            node = view.get(survivor.id)
            basis = stored.lineage_basis(node)
            assert basis is not None and basis["tag"] == "conflict"
            assert [route["run"] for route in stored.basis_routes(node)] == [
                f"run:{name}" for name in CONFLICT_ROUTES
            ]
            snapshot = lineage_snapshot(view, roots)
            assert _projected(snapshot, "divergence", survivor.id) == "divergent"
            assert certify(snapshot, (survivor.id,), (sibling.id,)) == divergent


# --- C1, re-read under §2.2's narrowing ---------------------------------------


def test_c1_retraction_never_removes_its_target_durably(durable_writer):
    """Retraction is additive while a deletion API exists: the operation never
    reaches the delete seam, the target's bytes and address are unchanged, and
    it still resolves — read back from disk after the engine committed."""
    writer = _adopted(durable_writer)
    target = mint_eligible_assessment(writer)
    before = path_for(writer.root, target.id).read_bytes()
    calls: list[str] = []
    original = CorpusWriter._delete_locked

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            CorpusWriter,
            "_delete_locked",
            lambda self, ref: calls.append(ref) or original(self, ref),
        )
        writer.retract(retraction_for(target, "grounds"))

    assert calls == [], "the retraction operation never reaches the delete seam"
    assert path_for(writer.root, target.id).read_bytes() == before
    view = reopen(writer.root)
    assert view.resolve(target.id) == target.id
    assert view.get(target.id) == target


# --- T8, re-read against `delete` ---------------------------------------------


def test_t8_delete_refuses_an_act_report_durably(durable_writer):
    """No ordinary API deletes a report: `delete` refuses an act-report subject
    on the excluded-kind rule, the report survives the refusal, and the refused
    call mints no report of its own."""
    writer = _adopted(durable_writer)
    report = _stored_act_report(writer)
    before = sum(1 for node in reopen(writer.root).iter_stored() if node.kind == "act-report")
    assert before == 2, "import_bundle stored the foreign report and minted its own"

    with pytest.raises(DeletionKindExcluded):
        writer.delete(report.id)

    view = reopen(writer.root)
    assert view.get(report.id) == report
    assert sum(1 for node in view.iter_stored() if node.kind == "act-report") == before


# --- M13 and M11 against `claim_from_stored` ----------------------------------


M13_SNAPSHOT = build_snapshot(readable={EX: [GENE, OTHER_GENE, OUTCOME], COHORT_DATASET: [ADULTS]})
"""Both vocabularies read, holding every term the restore seam binds here."""


def test_m13_claim_from_stored_is_opaque_over_a_durable_record(durable_writer):
    """§2.5's opacity arms against a record the certified engine committed: no
    wire type in or out of the signature, delegation to `decode_claim` with the
    seam's own typing path, and the brand chain intact through the new route —
    `π_claim` accepts the restored claim and it projects back to the stored
    facet."""
    writer = _adopted(durable_writer)
    minted = writer.add(stored_proposition(affects()))
    node = reopen(writer.root).get(minted.id)

    signature = inspect.signature(claim_from_stored)
    assert "WireClaim" not in str(signature)
    assert signature.return_annotation != "WireClaim"
    assert claim_from_stored.__module__ == "beliefs.decode"

    seen: list[object] = []
    real = decode.decode_claim
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(decode, "decode_claim", lambda wire, **kw: seen.append(wire) or real(wire, **kw))
        claim, receipt = claim_from_stored(node, profile=PROFILE, snapshot=M13_SNAPSHOT)

    assert len(seen) == 1 and isinstance(seen[0], decode.WireClaim)
    assert isinstance(claim, Claim) and isinstance(receipt, BindingCheckReceipt)
    direct, _ = decode_claim(affects(), profile=PROFILE, snapshot=M13_SNAPSHOT)
    assert project_claim(claim) == project_claim(direct)
    assert claim_identity(claim) == claim_identity(direct)


def test_m11_claim_from_stored_is_a_function_of_its_arguments_over_a_durable_record(durable_writer):
    """§2.5's decode arms: the same durable record decoded in **another
    process** from the same bytes yields an identical claim identity and
    receipt; availability stays a parameter; and a wrong kind, a missing, an
    extra and a malformed facet field each refuse **before** delegation with
    nothing minted."""
    writer = _adopted(durable_writer)
    minted = writer.add(stored_proposition(affects()))
    node = reopen(writer.root).get(minted.id)
    claim, receipt = claim_from_stored(node, profile=PROFILE, snapshot=M13_SNAPSHOT)

    script = textwrap.dedent(f"""
        from pathlib import Path
        from beliefs.contract import load_base_contract, load_domain_contract
        from beliefs.contract.domain import VocabularyBinding
        from beliefs.corpus import ReadView
        from beliefs.decode import claim_from_stored
        from beliefs.profile import compile_profile
        from beliefs.projection import claim_identity
        from beliefs.resolution import build_snapshot

        base = load_base_contract(Path({str(BASE_CONTRACT)!r}))
        testing = load_domain_contract(Path({str(TESTING_CONTRACT)!r}), base=base, predecessor=None)
        profile = compile_profile(base, [testing])
        EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
        COHORT = VocabularyBinding(namespace=None, release=None, dataset_identity={"0" * 64!r})
        snapshot = build_snapshot(readable={{EX: [{GENE!r}, {OTHER_GENE!r}, {OUTCOME!r}], COHORT: [{ADULTS!r}]}})
        node = ReadView.opened_at(Path({str(writer.root)!r})).get({node.id!r})
        decoded, emitted = claim_from_stored(node, profile=profile, snapshot=snapshot)
        print(claim_identity(decoded))
        print(emitted.identity())
    """)
    out = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, cwd=str(REPO_ROOT)
    ).stdout.split()
    assert out == [claim_identity(claim), receipt.identity()]

    with pytest.raises(MalformedWireClaim):
        claim_from_stored(node, profile=PROFILE, snapshot=None)  # type: ignore[arg-type]

    facet = node.facets[stored.PROPOSITION_FACET]
    mutations = (
        {key: value for key, value in facet.items() if key != "polarity"},
        {**facet, "extra": "x"},
        {**facet, "args": "not-a-list"},
        {**facet, "qualifiers": {"dim": {"quantifier": "all"}}},
    )
    before = _files(writer.root)
    for mutated in mutations:
        bad = node.model_copy(update={"facets": {stored.PROPOSITION_FACET: mutated}})
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated on malformed input"))
            with pytest.raises(MalformedWireClaim):
                claim_from_stored(bad, profile=PROFILE, snapshot=M13_SNAPSHOT)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated on a wrong kind"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(
                stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}),
                profile=PROFILE,
                snapshot=M13_SNAPSHOT,
            )
    assert _files(writer.root) == before, "a refusal mints nothing"


# --- R19 ----------------------------------------------------------------------


def test_r19_import_validation_and_transition_b_durably(durable_writer):
    """Explicit-import derivation validation over complete closure evidence —
    a contradicted verification refused **before any payload write** — then
    transition (b) end to end: a forged verification whose runs do not resolve
    imports unvalidated and admits; mounting the runs is not an epistemic
    event; the audit emits the contradiction and mints nothing; a separate
    constructor act mints the superseding verification and admission changes
    **because of that node**. Then negatives (d) and (e): the same forgery
    written raw is not refused and not seen on read, and the **log** audit
    refutes the root that carries it."""
    work = durable_writer.root.parent
    with _durable_corpora(work, "r19-unmounted") as (unmounted_writer,):
        derived = _two_runs(_adopted(durable_writer), mount=True, agreeing=True)
        assert derived.verification.verdict == "passed"
        writer = derived.writer

        forged = stored.verification_node(
            "forged-resolvable",
            title="forged-resolvable",
            assessment=derived.verification.assessment,
            assessment_ref=ASSESSMENT_REF,
            scope=derived.verification.scope,
            verdict=_flip(derived.verification.verdict),
            derivation=(
                run_ref(derived.verification.original),
                run_ref(derived.verification.replayed),
            ),
        )
        before = _record_files(writer.root)
        with pytest.raises(ImportRefused) as refused:
            writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
        assert refused.value.member == forged.id
        assert not path_for(writer.root, forged.id).exists()
        assert [
            path for path in _record_files(writer.root) if path not in before and "act-report" not in str(path)
        ] == [], "no bundle member landed"

        genuine = _stored_from(derived.verification, slug="genuine")
        writer.import_bundle([genuine], evidence=derived.evidence, **IMPORT_FIELDS)
        reloaded = reopen(writer.root).get(genuine.id)
        assert reloaded.kind == "verification"
        assert "validated" not in reloaded.facets[stored.VERIFICATION_FACET], "the record gains no validation state"

        unmounted = _two_runs(unmounted_writer, mount=False, agreeing=False)
        assert unmounted.verification.verdict == "failed"
        w = unmounted.writer
        identity = unmounted.assessment_identity
        transition_forgery = stored.verification_node(
            "forged",
            title="forged",
            assessment=identity,
            assessment_ref=ASSESSMENT_REF,
            scope="clean-environment",
            verdict="passed",
            derivation=(
                run_ref(unmounted.verification.original),
                run_ref(unmounted.verification.replayed),
            ),
        )
        report = w.import_bundle([transition_forgery], evidence=unmounted.evidence, **IMPORT_FIELDS)
        assert any(
            finding.startswith(f"derivation-unchecked: {transition_forgery.id}")
            for finding in _report_findings(report)
        )
        assert _admission(_view_writer(w), identity) == ADMITTED
        assert audit_corpus(reopen(w.root), evidence=unmounted.evidence, profile=w.profile) == ()

        w.import_bundle([unmounted.original_node, unmounted.replayed_node], **IMPORT_FIELDS)  # the mount

        assert _admission(_view_writer(w), identity) == ADMITTED, "mounting is not an epistemic event"
        assert "validated" not in reopen(w.root).get(transition_forgery.id).facets[stored.VERIFICATION_FACET]

        files = _files(w.root)
        findings = audit_corpus(reopen(w.root), evidence=unmounted.evidence, profile=w.profile)
        assert [finding.code for finding in findings] == ["verification-derivation-contradicted"]
        assert [finding.ref for finding in findings] == [transition_forgery.id]
        assert _files(w.root) == files, "the audit mints nothing"
        assert _admission(_view_writer(w), identity) == ADMITTED, "the audit alone changes nothing"

        superseding = build_verification(
            unmounted.original,
            unmounted.replayed,
            specs=unmounted.evidence.specs,
            held_rules=unmounted.evidence.held_rules,
            contract_identity=CONTRACT,
            epoch=EPOCH,
        )
        assert isinstance(superseding, AssessmentVerification)
        node = _stored_from(superseding, slug="superseding", supersedes=transition_forgery.id)
        w.import_bundle([node], evidence=unmounted.evidence, **IMPORT_FIELDS)

        assert _admission(_view_writer(w), identity) != ADMITTED
        assert [
            finding.ref for finding in audit_corpus(reopen(w.root), evidence=unmounted.evidence, profile=w.profile)
        ] == [transition_forgery.id]

        raw_forgery = _stored_from(
            derived.verification, slug="raw-forged", verdict=_flip(derived.verification.verdict)
        )
        raw_write(writer.root, raw_forgery)

        view = reopen(writer.root)
        assert view.get(raw_forgery.id).kind == "verification", "not refused, not detected on read"
        assert corpus_check(view, writer.profile) == (), "the corpus check says nothing"
        assert ("verification-derivation-contradicted", raw_forgery.id) in {
            (finding.code, finding.ref) for finding in audit_corpus(view, evidence=derived.evidence, profile=writer.profile)
        }
        assert _audit_log(writer).outcome == "refuted", "the log sees the write the read path cannot"


# --- R22 ----------------------------------------------------------------------


def test_r22_import_recomputation_and_audit_durably(durable_writer):
    """Negative (c)'s two halves over the certified engine: **explicit import**
    recomputes the assessment facet from the run and refuses a mismatch before
    any write, and the same forgery written straight into the corpus directory
    is not refused, not detected on read, and caught **only** under audit."""
    writer = _adopted(durable_writer)
    derived = _two_runs(writer, mount=True, agreeing=True)
    genuine = build_assessment(
        derived.original, specs=derived.evidence.specs, implementations=derived.evidence.implementations
    )
    assert isinstance(genuine, AssessmentValue)
    proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    flipped = "refuted" if genuine.outcome == "supported" else "supported"

    honest = _assessment_node_from(genuine, slug="a1", proposition=proposition.id, outcome=genuine.outcome)
    writer.import_bundle([honest], evidence=derived.evidence, **IMPORT_FIELDS)
    assert reopen(writer.root).get(honest.id).kind == "assessment"

    forged = _assessment_node_from(genuine, slug="forged", proposition=proposition.id, outcome=flipped)
    with pytest.raises(ImportRefused) as refused:
        writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
    assert refused.value.member == forged.id
    assert not path_for(writer.root, forged.id).exists()

    raw_write(writer.root, forged)

    view = reopen(writer.root)
    assert view.get(forged.id).kind == "assessment", "the raw write is not refused"
    assert corpus_check(view, writer.profile) == (), "and not detected on read"
    assert ("assessment-derivation-contradicted", forged.id) in {
        (finding.code, finding.ref) for finding in audit_corpus(view, evidence=derived.evidence, profile=writer.profile)
    }


# --- M1 -----------------------------------------------------------------------


def test_m1_containment_over_a_durable_corpus(durable_writer):
    """The recorded read-set is contained in the declared closure, over a
    durable corpus exercising **every** corpus-read kind the resolver has; and
    the sabotage — one extra verification of a different proposition read
    through `gather`, nothing else changed — leaves the digest exactly where it
    was and breaks containment. Appendix C's resolver bound is untouched: a
    read that never crosses `gather` is still invisible here."""
    fixture = _fixture(_adopted(durable_writer), PROPOSITION_REF)

    honest = gather(fixture.view, fixture.proposition, **fixture.gather_kwargs)
    assert set(honest.read_trace) <= honest.declared_refs()
    assert {kind for kind, _ in honest.read_trace} == set(evaluation.READ_KINDS) - {
        "retraction",
        "contract",
        "producer-snapshot",
    }, "every corpus-read kind is exercised"
    answer = evaluate(
        proposition=fixture.proposition,
        records=honest.records(),
        availability=fixture.availability,
        context=fixture.context,
        binding=fixture.binding,
        profile=PROFILE,
    )
    assert isinstance(answer, Belief)
    assert honest.closure().digest() == answer.belief_input_digest

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(evaluation, "_verification_selected", lambda value, ids: True)
        leaky = gather(fixture.view, fixture.proposition, **fixture.gather_kwargs)

    assert {v.ref for v in leaky.verifications} > {v.ref for v in honest.verifications}
    assert leaky.closure().digest() == honest.closure().digest()
    assert not set(leaky.read_trace) <= leaky.declared_refs()


# --- M3 -----------------------------------------------------------------------


def test_m3_audit_classification_and_admission_order_durably(work_directory):
    """Ω_valid first: a raw-written cyclic retraction configuration is
    classified **malformed** before any standing or belief evaluation — both
    are made to raise, so a reading that happened would fail the test — and
    then the negative: no topological rank is stored anywhere, so the same
    records admitted in two orders leave every stored identity and the belief
    digest unchanged."""
    with _durable_corpora(work_directory, "m3-cyclic", "m3-first", "m3-second") as (cyclic, first, second):
        raw_cyclic_retraction_pair(cyclic)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(
                corpus_module,
                "standing_in_local_view",
                lambda *a, **k: pytest.fail("standing was evaluated"),
            )
            patch.setattr(belief_module, "evaluate", lambda *a, **k: pytest.fail("belief was evaluated"))
            findings = audit_corpus(reopen(cyclic.root), evidence=NO_EVIDENCE, profile=cyclic.profile)

        assert findings and all(finding.severity == "error" for finding in findings)
        assert {finding.code for finding in findings} <= {
            "semantic-hash-stale",
            "semantic-hash-missing",
            "retraction-target-invalid",
            "retraction-cycle",
        }

        records = _records(retraction_chain=True)
        assert set(ORDER_A) == set(ORDER_B) == set(records)
        ordered = (_admit(first, records, ORDER_A), _admit(second, records, ORDER_B))
        reloaded = tuple(_reloaded(scenario) for scenario in ordered)

        identities = [
            {node.id: stored.stored_semantic_hash(node) for node in scenario.view.iter_stored()}
            for scenario in reloaded
        ]
        assert sorted(identities[0]) == sorted(identities[1]) == sorted(node.id for _, node in records.values())
        assert identities[0] == identities[1]
        assert reloaded[0].belief().belief_input_digest == reloaded[1].belief().belief_input_digest
        for scenario in reloaded:
            for node in scenario.view.iter_stored():
                assert _facet_members(node.facets) & RANKING_MEMBERS == set(), f"{node.id} carries a stored rank"


# --- M5 -----------------------------------------------------------------------


M5_SNAPSHOT = build_snapshot(readable={EX: [GENE, PHENO, SETTING], COHORT_DATASET: [ADULTS, CHILDREN]})


def test_m5_qualification_identity_durably(durable_writer):
    """Restriction only, quantifier tag only, and one omitting the dimension
    the others carry: each moves the stored semantic identity of a record the
    engine committed and each moves `I_claim` through the restore seam. The
    negative: the same qualification re-serialized with its keys in another
    order moves neither."""
    writer = _adopted(durable_writer)
    minted = {
        name: writer.add(stored.proposition_node(f"p-{name}", title=name, claim=facet))
        for name, facet in M5_VARIANTS.items()
    }
    view = reopen(writer.root)
    reloaded = {name: view.get(node.id) for name, node in minted.items()}
    stamps = {name: stored.stored_semantic_hash(node) for name, node in reloaded.items()}
    identities = {
        name: claim_identity(claim_from_stored(node, profile=PROFILE, snapshot=M5_SNAPSHOT)[0])
        for name, node in reloaded.items()
    }

    assert None not in stamps.values()
    assert len(set(stamps.values())) == len(M5_VARIANTS), "each qualification difference moves the stored identity"
    assert len(set(identities.values())) == len(M5_VARIANTS), "and moves I_claim"

    population = {"quantifier": "generic", "restriction": ADULTS}
    setting = {"quantifier": "generic", "restriction": SETTING}
    order_variants = {
        "forward": {
            **CLAIM_FACET,
            "qualifiers": {"testing/population": population, "testing/setting": setting},
        },
        "reversed": {
            **CLAIM_FACET,
            "qualifiers": {
                "testing/setting": {"restriction": SETTING, "quantifier": "generic"},
                "testing/population": {"restriction": ADULTS, "quantifier": "generic"},
            },
        },
    }
    ordered = [
        writer.add(stored.proposition_node(f"p-order-{name}", title=name, claim=facet))
        for name, facet in order_variants.items()
    ]
    view = reopen(writer.root)
    forward_node, reversed_node = (view.get(node.id) for node in ordered)
    forward_identity, reversed_identity = (
        claim_identity(claim_from_stored(node, profile=PROFILE, snapshot=M5_SNAPSHOT)[0])
        for node in (forward_node, reversed_node)
    )
    assert stored.stored_semantic_hash(forward_node) == stored.stored_semantic_hash(reversed_node)
    assert forward_identity == reversed_identity


# --- the boundary invariant ---------------------------------------------------


def test_boundary_reresolution_after_a_durable_delete(durable_writer):
    """§3.6: both entry points re-resolve under the lock immediately before
    plan construction and refuse `RelocationTargetMissing` when a real `delete`
    removed the target under them. The absence is produced by `delete` and
    never by a filesystem call."""
    writer = _adopted(durable_writer)
    target = mint_eligible_assessment(writer)
    record = retraction_for(target, "grounds")
    original_refuse = CorpusWriter._refuse

    def delete_target_then_refuse(self, node, **kwargs):
        if node.kind == "retraction":
            self._delete_locked(target.id)
        return original_refuse(self, node, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(CorpusWriter, "_refuse", delete_target_then_refuse)
        with pytest.raises(RelocationTargetMissing):
            writer.retract(record)

    view = reopen(writer.root)
    assert view.resolve(record.id) is None, "the retraction was never written"
    assert view.resolve(target.id) is None, "and the delete that raced it did happen"

    predecessor = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    successor = stored.proposition_node("q", title="q", claim={"operator": "causes"})

    def delete_predecessor_then_refuse(self, node, **kwargs):
        if node.kind == "proposition" and node.id == successor.id:
            self._delete_locked(predecessor.id)
        return original_refuse(self, node, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(CorpusWriter, "_refuse", delete_predecessor_then_refuse)
        with pytest.raises(RelocationTargetMissing):
            writer.supersede(successor, of=predecessor.id)

    view = reopen(writer.root)
    assert view.resolve(successor.id) is None, "the successor was never written"
    assert view.resolve(predecessor.id) is None
