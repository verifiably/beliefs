"""Steps 5-7: confined run, assessment, replay, verification.

Two identities for one assessment: `build_assessment` returns a value whose
`run` is the bare closure address; the stored record spells it as the typed
`run:<address>`, so `stored.assessment_value(node).identity()` differs from
`assessment.identity()`. Both are written to `state.json`; neither is
substituted for the other.
"""

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
    return DurableOperationPort(
        paths.CORPUS_ROOT,
        backend=select_backend(),
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(paths.CORPUS_ROOT),
        authority=AUTHORITY,
    )


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_scope(scope: str, *, conforming: tuple[bool, bool], recipes_agree: bool) -> str:
    """Design §2 rule 4. `same-environment` with agreeing recipes is the
    host's; `not-certified` is a non-conforming closure (defect) or
    disagreeing recipes (authoring, i.e. corpus work). Never the host by
    default."""
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
    common = dict(
        port=port(),
        definition=spec.definition(),
        code_roots=(spec.CODE_ROOT,),
        held_inputs=held,
        entrypoint=spec.ENTRYPOINT,
        targets=spec.TARGETS,
        declared_outputs=spec.TARGETS,
        observer=OBSERVER,
        host_realization=socket.gethostname(),
        cores=1,
    )
    # Step 5
    original = execute_assessment_run(
        spec=frozen, boundary_policy=CONFINED_POLICY, started_at=now(), scratch_base=paths.SCRATCH / "original", **common
    )
    if isinstance(original, RunRefused):
        malformed = original.reason == "execution-failed" and "malformed input" in (original.detail or "")
        cls = "corpus-work" if malformed else "design-gap"
        findings.record(5, cls, f"run refused: {original.reason}: {original.detail}")
        print(f"REFUSED at run: {original.reason}: {original.detail}")
        return 2
    original_ref = run_ref(original.run.address())
    # Step 6
    derived = build_assessment(
        original.run,
        specs={frozen.identity: frozen},
        implementations={spec.interpretation().identity: spec.interpretation()},
    )
    if isinstance(derived, AssessmentFinding):
        findings.record(6, "defect", f"AssessmentFinding: {derived.reason}")
        print(f"ASSESSMENT FINDING: {derived.reason}")
        return 2
    optional = {
        k: v
        for k, v in (
            ("estimate", derived.estimate),
            ("uncertainty", derived.uncertainty),
            ("estimand", derived.estimand),
            ("applicability", derived.applicability),
        )
        if v is not None
    }
    writer = world.open_writer()
    minted = writer.add(
        stored.assessment_node(
            derived.identity()[:16],
            title=f"assessment of {st['proposition_ref']}",
            spec=frozen.identity,
            run=original_ref,
            proposition=st["proposition_ref"],
            outcome=derived.outcome,
            interpretation_rule=derived.interpretation_rule,
            **optional,
        )
    )
    stored_identity = stored.assessment_value(writer.read_view.get(minted.id)).identity()
    if stored_identity != derived.identity():
        findings.record(
            6,
            "design-gap",
            "the derived AssessmentValue spells `run` as a bare address and the stored record as run:<address>; "
            "the two identities differ, and no single one satisfies both admission over the corpus and the "
            "audit's recomputation (which digests the bare address)",
            filed="assessment/run-record design (one spelling for the run member)",
        )
    # Step 7
    replayed = replay(original, spec=frozen, started_at=now(), scratch_base=paths.SCRATCH / "replayed", **common)
    if isinstance(replayed, RunRefused):
        findings.record(7, "design-gap", f"replay refused: {replayed.reason}: {replayed.detail}")
        print(f"REFUSED at replay: {replayed.reason}: {replayed.detail}")
        return 2
    scope = derive_scope(original.run, replayed.run, certification=None)
    cls = classify_scope(
        scope,
        conforming=(conformance(original.run) == CONFORMING, conformance(replayed.run) == CONFORMING),
        recipes_agree=original.run.recipe.identity() == replayed.run.recipe.identity(),
    )
    if cls != "none":
        receipt = replayed.run.occurrence.receipt.execution
        findings.record(
            7,
            cls,
            f"scope {scope}: replay capabilities={receipt.capabilities} "
            f"instance={'present' if receipt.instance else 'absent'}",
        )
    verification = build_verification(
        original.run,
        replayed.run,
        specs={frozen.identity: frozen},
        held_rules={spec.equivalence().identity: spec.equivalence()},
        contract_identity=writer.manifest_pins().science_contract,
        epoch="none-published",
    )
    assert isinstance(verification, AssessmentVerification), verification
    state.save(
        original_run_ref=original_ref,
        replayed_run_ref=run_ref(replayed.run.address()),
        assessment_ref=minted.id,
        assessment_identity_stored=stored_identity,
        assessment_identity_derived=derived.identity(),
        assessment_outcome=derived.outcome,
        verification_scope=verification.scope,
        verification_verdict=verification.verdict,
        scope_class=cls,
    )
    print(
        f"run {original_ref}; assessment {derived.outcome}; scope {verification.scope} ({cls}); "
        f"verdict {verification.verdict}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
