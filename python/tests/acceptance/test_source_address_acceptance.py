"""Cut 25 — source addresses derived from the normalized identifier (W1, W2, W5a)."""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import ACTOR, FULL
from nodes.core.errors import ExecutionError
from profiles import BASE, WITH_BIOLOGY, pins_for
from session_faults import PUBLISH_CALLS_BEFORE_RECORD
from test_identifier_correction import _ImportFields, raw_edit_history
from test_retract import content_identity, mint_eligible_assessment
from test_session_acceptance import (
    _swept,  # noqa: F401 — cleanup for the imported durable session helpers
    adopted,
    chain,
    config_for,
    fresh,
    halting_session,
    pending_registrations,
    state_of,
    tree_hash,
    triple,
)
from test_world_receipts import hold_shipped, publish

from beliefs import source, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    AddressMapConflict,
    BasisMissing,
    CollisionRefused,
    ContractMismatch,
    CorrectionRefused,
    HistoryDisagreement,
    IdentifierMalformed,
    PermitExceeded,
    RecordAlreadyMinted,
    ReviseOutsideAllowlist,
    SourceAddressDisagreement,
    ValidationRefused,
)
from beliefs.permit import RequiredCapabilities
from beliefs.relocation import consolidate, move
from beliefs.root import init_corpus_root, init_world_root, metadata_root_for, open_corpus, open_world
from beliefs.session import reconcile_sessions
from beliefs.world import Fresh, WorldConfig
from beliefs.world.read import Unknown
from beliefs.world.view import open_world_view

REPORT: _ImportFields = {
    "observer": "o",
    "instrument": "i",
    "opened_at": "2026-09-10T00:00:00Z",
    "closed_at": "2026-09-10T00:00:01Z",
}
SOURCES = RequiredCapabilities.for_kinds(
    {"source", "dataset", "run", "proposition", "assessment", "retraction"}, {"run": "corpus-write"}
)
PAIRS = (
    ("Chen2023", "10.1234/chen.a", "10.5678/chen.b"),
    ("Liu2020", "10.1234/liu.a", "10.5678/liu.b"),
    ("Shi2025", "10.1234/shi.a", "10.5678/shi.b"),
)


@pytest.fixture()
def world(work_directory):
    """Two durable corpora and a world root; the caller populates and publishes."""
    roots = []

    def corpus():
        path = Path(mkdtemp(prefix="cut25-corpus-", dir=work_directory))
        roots.append(path)
        init_corpus_root(path, authority=FULL)
        writer = open_corpus(path, authority=FULL, profile=BASE)
        manifest = writer.adopt_manifest(profile=pins_for(BASE))
        return manifest.corpus_id, path, writer

    a, alpha, left = corpus()
    b, beta, right = corpus()
    path = Path(mkdtemp(prefix="cut25-world-", dir=work_directory))
    roots.append(path)
    config = WorldConfig(path, "e" * 32, (alpha, beta))
    init_world_root(config, authority=FULL)
    registry = open_world(config, authority=FULL)
    registry.admit(alpha, provenance=Fresh())
    registry.admit(beta, provenance=Fresh())
    try:
        yield registry, (a, left), (b, right)
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def test_w1_distinct_bases_never_become_one_node(world):
    registry, (a, left), (b, right) = world
    for citekey, first, second in PAIRS:
        left.add(stored.source_node(title=citekey, identifiers={"doi": first}))
        right.add(stored.source_node(title=citekey, identifiers={"doi": second}))
    addresses = {n.id for w in (left, right) for n in w.read_view.iter_stored() if n.kind == "source"}
    assert len(addresses) == 6
    assert left.read_view.resolve("source:Chen2023") is None
    published = publish(registry, (a, b), hold_shipped(registry))
    view = open_world_view(registry, published)
    assert isinstance(view.locate("source:Chen2023"), Unknown) and view.resolve("source:Chen2023") is None
    assert all(view.resolve(address) == address for address in addresses)


def test_w2_a_shared_basis_is_one_address(world):
    registry, (a, left), (b, right) = world
    one = left.add(stored.source_node(title="x", identifiers={"doi": "10.1234/ABC"}))
    two = stored.source_node(title="y", identifiers={"doi": "https://doi.org/10.1234/abc"})
    assert one.id == two.id
    with pytest.raises(CollisionRefused):
        left.add(two)  # fresh uid, held address
    with pytest.raises(RecordAlreadyMinted):
        left.add(one)  # same (uid, id)
    right.add(two)
    bindings = hold_shipped(registry)
    epochs = registry.config.world_root / "epochs"
    before = tree_hash(epochs)
    with pytest.raises(AddressMapConflict) as caught:
        publish(registry, (a, b), bindings)
    assert tree_hash(epochs) == before
    assert caught.value.finding.code == "duplicate-location"
    consolidate((left, one.id), (right, two.id), rationale="one paper", **REPORT)
    published = publish(registry, (a, b), hold_shipped(registry))
    assert open_world_view(registry, published).corpus_of(one.id) == a
    # Negative: a shared secondary identifier infers nothing.
    p = left.add(stored.source_node(title="p", identifiers={"pmid": "77"}))
    dp = right.add(stored.source_node(title="dp", identifiers={"doi": "10.1234/dp", "pmid": "77"}))
    assert p.id != dp.id
    publish(registry, (a, b), hold_shipped(registry))


def test_w5a_dataset_arm_a_rehold_is_a_new_entity(world):
    _, (_, left), _ = world
    assessment = mint_eligible_assessment(left)  # observes dataset:raw through run:r1
    d = left.read_view.get("dataset:raw")
    changed = d.model_copy(deep=True)
    changed.facets[stored.DATASET_FACET]["resources"] = [{"name": "d", "digest": "sha256:" + "9" * 64}]
    stored.stamp_semantic_identity(changed)
    with pytest.raises(ReviseOutsideAllowlist):
        left.revise(changed)
    with pytest.raises(CollisionRefused):
        left.add(stored.dataset_node("raw", title="raw", resources=[{"name": "d", "digest": "sha256:" + "9" * 64}]))
    reheld = left.add(
        stored.dataset_node("raw-reheld", title="raw", resources=[{"name": "d", "digest": "sha256:" + "9" * 64}])
    )
    assert reheld.id != d.id and stored.dataset_declaration(reheld) != stored.dataset_declaration(d)
    assert content_identity(reheld) != content_identity(d)
    run = left.read_view.get(
        "run:r1"
    )  # mint_eligible_assessment's run; AssessmentValue.run is the closure address, not the id
    assert [
        e.relation.target for e in left.read_view.outbound(assessment.id) if e.relation.predicate == stored.PRODUCED_BY
    ] == [run.id]
    observed = [r.target for r in run.relations if r.predicate == stored.OBSERVES]
    assert observed == [d.id] and reheld.id not in observed
    assert left.read_view.get(d.id).facets[stored.DATASET_FACET] == d.facets[stored.DATASET_FACET]


def test_w5a_source_arm_rename_preserves_uid_and_redirects(world):
    registry, (a, left), (b, _right) = world
    paper = left.add(stored.source_node(title="p", identifiers={"doi": "10.1234/wrong"}))
    # The referrer: a retraction grounded in the source (a source is not a retraction NodeTarget).
    assessment = mint_eligible_assessment(left)
    retraction = stored.retraction_node(  # grounds supplied at build: the id is content-derived over them
        title="retraction",
        target=stored.NodeTarget(assessment.id, assessment.id, content_identity(assessment)),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=(paper.id,),
        actor=ACTOR,
        event_token="event-1",
    )
    minted = left.retract(retraction)
    referrer_bytes = (left.root / "retraction" / f"{minted.id.partition(':')[2]}.md").read_bytes()

    corrected = left.correct_identifier(paper.id, {"doi": "10.1234/right"}, grounds="the PDF's DOI")
    assert corrected.uid == paper.uid and corrected.deprecated_ids == [paper.id]
    (correction,) = stored.identifier_corrections(corrected)
    assert correction.actor == ACTOR and correction.grounds == "the PDF's DOI"
    assert left.read_view.resolve(paper.id) == corrected.id
    assert (left.root / "retraction" / f"{minted.id.partition(':')[2]}.md").read_bytes() == referrer_bytes
    (ground,) = [e for e in left.read_view.outbound(minted.id) if e.relation.predicate == stored.GROUNDED_IN]
    assert ground.relation.target == paper.id and ground.target_uid == corrected.uid
    published = publish(registry, (a, b), hold_shipped(registry))
    view = open_world_view(registry, published)
    assert view.resolve(paper.id) == corrected.id

    # Negative — three arms, three calls, no chooser.
    assert "case" not in inspect.signature(left.correct_identifier).parameters
    other = left.add(stored.source_node(title="p2", identifiers={"doi": "10.1234/another"}))  # arm 2: a new work
    assert other.uid != corrected.uid
    attestation = stored.coreference_attestation_node(  # arm 3: two identifiers legitimately exist
        title="same paper",
        endpoints=(corrected.id, other.id),
        stance=1,
        actor=ACTOR,
        grounds="the same PDF",
        event_token="e1",
    )
    left.attest_coreference(attestation)
    assert left.read_view.get(corrected.id).id == corrected.id and left.read_view.get(other.id).id == other.id
    assert left.read_view.get(other.id).deprecated_ids == [] and left.read_view.get(corrected.id).deprecated_ids == [
        paper.id
    ]


@pytest.mark.parametrize(
    "case,exception,reason",
    [
        ("permit", PermitExceeded, None),
        ("pins", ContractMismatch, None),
        ("missing", CorrectionRefused, "target-missing"),
        ("not-source", CorrectionRefused, "not-a-source"),
        ("raw-current", SourceAddressDisagreement, None),
        ("malformed", IdentifierMalformed, "malformed"),
        ("noncanonical", IdentifierMalformed, "non-canonical"),
        ("empty-basis", BasisMissing, None),
        ("empty-grounds", CorrectionRefused, "grounds-empty"),
        ("surrogate-grounds", CorrectionRefused, "grounds-empty"),
        ("unchanged", CorrectionRefused, "unchanged"),
        ("successor-facets", ValidationRefused, None),
        ("collision", CollisionRefused, None),
        ("retired-collision", CollisionRefused, None),
    ],
)
def test_refusals_leave_no_intent_or_file_effect(work_directory, case, exception, reason):
    """Each refusing stage of §6.1 runs before intent append or file publication."""
    root = adopted(work_directory, f"cut25-refuse-{case}")
    session, _backend, ops = halting_session(work_directory, root)
    try:
        w = fresh(session, "setup", SOURCES)
        paper = w.add(stored.source_node(title="p", identifiers={"pmid": "1"}))
        ref, target, grounds = paper.id, {"doi": "10.1234/one"}, "g"
        required = SOURCES
        if case == "permit":
            required = RequiredCapabilities.for_kinds({"dataset"}, {})
        elif case == "pins":
            manifest = root / "corpus.yaml"
            manifest.write_bytes(
                manifest.read_bytes().replace(
                    pins_for(WITH_BIOLOGY).science_contract.encode(), ("science:" + "f" * 64).encode()
                )
            )
        elif case == "missing":
            ref = "source:missing"
        elif case == "not-source":
            ref = w.add(
                stored.dataset_node("d", title="d", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}])
            ).id
        elif case in ("raw-current", "successor-facets"):

            def corrupt(node):
                if case == "raw-current":
                    node.facets[stored.SOURCE_FACET]["identifiers"] = {"pmid": "2"}
                else:
                    node.facets["unregistered-facet"] = {}
                stored.stamp_semantic_identity(node)

            raw_edit_history(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY), paper.id, corrupt)
        elif case == "malformed":
            target = {"pmid": "not-digits"}
        elif case == "noncanonical":
            target = {"doi": "10.1234/ABC"}
        elif case == "empty-basis":
            target = {}
        elif case == "empty-grounds":
            grounds = ""
        elif case == "surrogate-grounds":
            grounds = "\udcff"
        elif case == "unchanged":
            target = {"pmid": "1"}
        elif case in ("collision", "retired-collision"):
            other = w.add(stored.source_node(title="other", identifiers=target))
            if case == "retired-collision":
                w.correct_identifier(other.id, {"doi": "10.1234/two"}, grounds="g")

        w = fresh(session, "refused", required)
        before_chain = chain(root)
        before_files = tree_hash(root, metadata_root_for(root), ops)
        with pytest.raises(exception) as caught:
            w.correct_identifier(ref, target, grounds=grounds)
        assert type(caught.value) is exception
        if reason is not None:
            assert caught.value.reason == reason
        assert chain(root) == before_chain
        assert tree_hash(root, metadata_root_for(root), ops) == before_files
        assert (root / "source" / f"{paper.id.partition(':')[2]}.md").is_file()
    finally:
        session.close()


def _halt_at(session, backend, root, skip, subject, target):
    """Arm the halting backend at publish `skip`, run one correction of `subject`
    to `target`, and return the file state observed at the halt as
    `(old_exists, new_exists)`; then disarm and settle through an unrelated add."""
    old_path = root / "source" / f"{subject.id.partition(':')[2]}.md"
    target_address = source.source_address(target)
    assert target_address is not None
    new_path = root / "source" / f"{target_address.partition(':')[2]}.md"
    backend.skip = skip
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        fresh(session, f"halt-{skip}", SOURCES).correct_identifier(subject.id, target, grounds="g")
    assert backend.halted and state_of(root).unresolved is True
    observed = (old_path.exists(), new_path.exists())
    backend.disarm()
    fresh(session, f"settle-{skip}", SOURCES).add(
        stored.source_node(title="settle", identifiers={"pmid": str(1000 + skip)})
    )
    assert state_of(root).unresolved is False
    return observed


@pytest.fixture()
def correction_halt_positions(work_directory) -> tuple[int, int]:
    """Derive the injection positions for the requesting test: sweep
    the halt over the two-op transaction's publish sequence and read the file
    state at each halt. The positions are derived from what was observed, never
    from the single-record count, and the sweep must show the create completing
    before the delete begins."""
    root = adopted(work_directory, "cut25-sweep")
    session, backend, _ops = halting_session(work_directory, root)
    w = fresh(session, "warm", SOURCES)
    w.add(stored.source_node(title="warm", identifiers={"pmid": "99"}))  # the kind directory exists
    observed: list[tuple[int, tuple[bool, bool]]] = []
    for skip in range(PUBLISH_CALLS_BEFORE_RECORD, PUBLISH_CALLS_BEFORE_RECORD + 4):
        subject = fresh(session, f"subject-{skip}", SOURCES).add(
            stored.source_node(title="s", identifiers={"pmid": str(10 + skip)})
        )
        target = {"doi": f"10.1234/s{skip}", "pmid": str(10 + skip)}
        observed.append((skip, _halt_at(session, backend, root, skip, subject, target)))
    states = [state for _, state in observed]
    assert (True, False) in states and (True, True) in states, observed
    assert states.index((True, False)) < states.index((True, True)), observed
    assert (False, False) not in states, observed  # the delete never lands before the create
    halt_before_create = observed[states.index((True, False))][0]
    halt_between = observed[states.index((True, True))][0]
    session.close()
    return halt_before_create, halt_between


def test_failure_boundary_refusals_and_applied_prefixes(work_directory, monkeypatch, correction_halt_positions):
    """Spec §10.3: a refusal has no effect; a halt after submission leaves a stated
    prefix and the root unresolved; a post-commit readback fault leaves the record
    durable; settlement leaves exactly one record with the subject's uid."""
    halt_before_create, halt_between = correction_halt_positions
    root = adopted(work_directory, "cut25-halt")
    session, backend, ops = halting_session(work_directory, root)
    w = fresh(session, "A", SOURCES)
    w.add(stored.source_node(title="warm", identifiers={"pmid": "99"}))  # the kind directory exists
    paper = w.add(stored.source_node(title="p", identifiers={"pmid": "1"}))
    target = {"doi": "10.1234/one", "pmid": "1"}
    old_path = root / "source" / f"{paper.id.partition(':')[2]}.md"
    target_address = source.source_address(target)
    assert target_address is not None
    new_path = root / "source" / f"{target_address.partition(':')[2]}.md"

    # 1. Refusal: no intent, no effect.
    before = len(chain(root).entries)
    with pytest.raises(CorrectionRefused):
        w.correct_identifier(paper.id, {"pmid": "1"}, grounds="g")
    assert len(chain(root).entries) == before and old_path.exists() and not new_path.exists()

    # 2. Halt before the create's publish (position derived by the requested sweep fixture):
    #    nothing published, the intent stands, reconciliation classifies it.
    backend.skip = halt_before_create
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        w.correct_identifier(paper.id, target, grounds="g")
    assert backend.halted and pending_registrations(root) and state_of(root).unresolved is True
    assert (old_path.exists(), new_path.exists()) == (True, False), "create halted: nothing published"
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert any(f.code in ("session-outcome-unknown", "session-entry-pending") for f in findings)
    backend.disarm()
    fresh(session, "B", SOURCES).add(stored.source_node(title="q", identifiers={"pmid": "2"}))  # settles first
    assert not pending_registrations(root) and state_of(root).unresolved is False
    assert (old_path.exists(), new_path.exists()) == (True, False), "rolled back: the subject stands at its old address"

    # 3. Halt between the create and the delete (the sweep's (True, True) position): the create
    #    completed and the delete did not; settlement resolves the pair to exactly one record.
    before = len(chain(root).entries)
    backend.skip = halt_between
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        fresh(session, "C", SOURCES).correct_identifier(paper.id, target, grounds="g")
    assert backend.halted and state_of(root).unresolved is True
    assert (old_path.exists(), new_path.exists()) == (True, True), "create completed, delete pending"
    pending = {e.digest for e in chain(root).entries[before:]}
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert any(f.code in ("session-outcome-unknown", "session-entry-pending") and f.ref in pending for f in findings)
    backend.disarm()
    fresh(session, "D", SOURCES).add(stored.source_node(title="r", identifiers={"pmid": "3"}))
    assert state_of(root).unresolved is False
    assert old_path.exists() != new_path.exists(), "settlement leaves one file, never both"
    reader = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    holders = [n for n in reader.read_view.iter_stored() if n.uid == paper.uid]
    assert len(holders) == 1
    stored.validate_source_history(holders[0])

    # 4. Post-commit readback fault: the plan committed, the registration stands, the view is not rebuilt.
    subject = holders[0]
    next_target = {"doi": "10.1234/postcommit", "pmid": "1"}
    old_path = root / "source" / f"{subject.id.partition(':')[2]}.md"
    target_address = source.source_address(next_target)
    assert target_address is not None and target_address != subject.id
    new_path = root / "source" / f"{target_address.partition(':')[2]}.md"
    w = fresh(session, "E", SOURCES)
    before = len(chain(root).entries)
    monkeypatch.setattr(
        CorpusWriter,
        "_reconstruct",
        lambda self: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.correct_identifier(subject.id, next_target, grounds="g")
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    assert (old_path.exists(), new_path.exists()) == (False, True)
    entries = chain(root).entries[before:]
    assert len(entries) == 3
    intent, registration, settlement = triple(entries, 0)
    assert registration.fulfills == intent.digest
    assert settlement.registration == registration.digest and settlement.committed
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert any(f.code == "session-outcome-unknown" and f.ref == registration.digest for f in findings)
    fresh(session, "F", SOURCES).add(stored.source_node(title="s", identifiers={"pmid": "4"}))
    reader = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    holders = [n for n in reader.read_view.iter_stored() if n.uid == paper.uid]
    assert len(holders) == 1 and holders[0].facets[stored.SOURCE_FACET]["identifiers"] == next_target
    stored.validate_source_history(holders[0])
    session.close()


def test_lifecycle_move_consolidate_delete(world):
    _registry, (_a, left), (_b, right) = world
    paper = left.add(stored.source_node(title="p", identifiers={"pmid": "5"}))
    corrected = left.correct_identifier(paper.id, {"doi": "10.1234/five", "pmid": "5"}, grounds="g")
    moved, *_ = move(left, right, corrected.id, **REPORT)
    assert moved.uid == corrected.uid
    assert stored.identifier_corrections(moved) == stored.identifier_corrections(corrected)
    assert right.read_view.get(moved.id).deprecated_ids == [paper.id]
    assert right.read_view.resolve(paper.id) == moved.id
    left.import_bundle([right.read_view.get(moved.id)], **REPORT)  # a byte-identical replica
    survivor, *_ = consolidate((left, moved.id), (right, moved.id), rationale="r", **REPORT)
    assert survivor.uid == corrected.uid and survivor.deprecated_ids == [paper.id]
    assert stored.identifier_corrections(survivor) == stored.identifier_corrections(corrected)
    assert left.read_view.resolve(paper.id) == survivor.id
    assert right.read_view.resolve(survivor.id) is None
    other = right.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    right.correct_identifier(other.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g1")
    twin = left.add(stored.source_node(title="o", identifiers={"pmid": "6"}))
    left.correct_identifier(twin.id, {"doi": "10.1234/six", "pmid": "6"}, grounds="g2")  # another token: divergent
    divergent = source.source_address({"doi": "10.1234/six"})
    assert divergent is not None
    with pytest.raises(HistoryDisagreement):
        consolidate(
            (left, divergent),
            (right, divergent),
            rationale="r",
            **REPORT,
        )
    left.delete(survivor.id)
    assert left.read_view.resolve(paper.id) is None
