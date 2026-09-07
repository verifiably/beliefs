"""Step 9: corpus_check, the semantic audit, log verification. Writes nothing.

The contradiction codes are exactly `verification-derivation-contradicted`,
`assessment-derivation-contradicted` and `lineage-basis-contradicted`; those
and the malformedness codes are defects. Anything else the audit emits is a
design-gap with its code.
"""

from __future__ import annotations

import sys

from beliefs import root as science_root
from beliefs.audit import MALFORMEDNESS_CODES, DerivationEvidence, audit_corpus, stored_specs
from beliefs.corpus import corpus_check
from beliefs.world import anchors, verify
from reproduction import findings, paths, spec, state, world
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import profile

CONTRADICTIONS = frozenset(
    {"verification-derivation-contradicted", "assessment-derivation-contradicted", "lineage-basis-contradicted"}
)


def evidence_for(view) -> DerivationEvidence:
    """Specs from the corpus, rules from code — 10b's only in-process input."""
    specs, unrestorable = stored_specs(view)
    if unrestorable:
        raise RuntimeError(f"stored specs that do not restore: {[f.ref for f in unrestorable]}")
    return DerivationEvidence(
        specs=specs,
        held_rules={spec.equivalence().identity: spec.equivalence()},
        implementations={spec.interpretation().identity: spec.interpretation()},
    )


def evidence() -> DerivationEvidence:
    return evidence_for(world.open_writer().read_view)


def log_audits() -> dict[str, dict]:
    """Two observer shapes, both measured, neither written. The exercise
    anchored nothing, so the corpus's own observer set is empty; the second
    shape is one registry carrier built from the chain head as read now — the
    record an anchor act would have left — so the chain verification itself
    (replay, removal policy) runs over the real chain."""
    st = state.load()
    subject = anchors.CorpusSubject(st["corpus_id"])
    genesis, head = science_root.chain_head_reader()(paths.CORPUS_ROOT)
    carrier = verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(subject, genesis, head, anchors.AnchorActOrigin(AUTHORITY.actor))
    )
    reports = {}
    for shape, observers in (("no-observer", verify.ObserverSet(())), ("head-carrier", verify.ObserverSet((carrier,)))):
        report = science_root.audit_log(world.config(), subject, paths.CORPUS_ROOT, observers, actor=AUTHORITY.actor)
        reports[shape] = {
            "outcome": report.outcome,
            "anchored_through": report.anchored_through,
            "unanchored_tail": len(report.unanchored_tail),
            "pending": len(report.pending),
            "intents": len(report.qualification),
            "observer_bound": list(report.observer_bound),
            "findings": [f"{f.code}: {f.ref}" for f in report.findings],
        }
    return reports


def main() -> int:
    view = world.open_writer().read_view
    checks = corpus_check(view, profile())
    for f in checks:
        findings.record(9, "defect", f"corpus_check: {f.code}: {f.ref}: {f.message}")
    audits = audit_corpus(view, evidence=evidence(), profile=profile())
    for f in audits:
        cls = "defect" if f.code in CONTRADICTIONS or f.code in MALFORMEDNESS_CODES else "design-gap"
        findings.record(9, cls, f"audit_corpus: {f.code}: {f.ref}: {f.message}")
    logs = log_audits()
    for shape, report in logs.items():
        for line in report["findings"]:
            # An `unanchored` chain under the empty observer set is the exercise's
            # own omission (it performed no anchor act), not a kernel finding.
            own = shape == "no-observer" and line.startswith("unanchored:")
            findings.record(
                9,
                "corpus-work" if own else "design-gap",
                f"audit_log[{shape}]: {line}",
                filed="the exercise performed no anchor act; measured under the head carrier instead" if own else "unfiled",
            )
    state.save(corpus_check_findings=len(checks), audit_findings=len(audits), log_verdict=logs)
    print(f"corpus_check: {len(checks)}; audit_corpus: {len(audits)}")
    for f in (*checks, *audits):
        print(f"  {f.code}: {f.ref}: {f.message}")
    for shape, report in logs.items():
        print(f"audit_log[{shape}]: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
