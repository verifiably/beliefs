"""The recreation's terminal verdict, read-only over `state.json` and `findings.jsonl`.

Five steps (belief, rederive, close, compose's receipt check, `read --again`)
record a defect and still exit zero, so a recreation's exit codes alone cannot
say it reproduced. This step reads what they recorded and exits non-zero
naming every failed line of the verdict
(`docs/notes/2026-09-29-reproduction-audit-backlog-brief.md`, "The minimal
terminal verdict"). It writes nothing.

The expected values are run-invariant and copied from the fixture's
`state.json` (the 2026-09-16 recreation). Run, assessment, verification and
composite record identities move with every confined run, so they are
compared only with each other. `findings.jsonl` is append-only and each
`rederive` re-run adds two step-10 lines, so the verdict is defined over a
fresh work directory that ran the sequence once.

Throwaway by declaration (mm30 reproduction design §8 item 3).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from reproduction import paths

MISSING = object()

TARGET = "proposition:concept-disease-stage-affects-protein-phf19"
SPINE = "proposition:protein-phf19-affects-concept-overall-survival"
BASE_MISMATCH = ["profile-mismatch: base"]

# {group: {dotted state key: expected value}}.
EXPECTED: dict[str, dict[str, object]] = {
    "authored": {
        "target": TARGET,
        "dataset": "dataset:gse179929",
        "held_digest": "sha256:c74ea661e636ab670315f722cbad2d9c1154dbbc114012180d48c623850a31a5",
        "dataset_address": "dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448",
        "concepts_count": 285,
        "concepts_address": "dataset:sha256:be3bf183a830c31d4f8acf46a309e01bd0476580d2d6db4079af3e3c7bd738d8",
        "levels_address": "dataset:sha256:85b5e3477d98ec0191b0e54da86202ec8c0d4081c45e7ddac103a30f8feb12a8",
        "measures_address": "dataset:sha256:08027c2e5fdd6939d2392ebbb0b9002a5b0778a3f71c7a54cab994836ab88f0c",
        "identifications_address": "dataset:sha256:79e307100a52bc03c0799780d4caeaf040f5ece71f938f6c2ae9bbd4d61bff36",
        "claim_identity": "780ace5964c8ab8315607ee9ed084b4acf6bf0f3f20f82bbbd41c11408cddb1c",
        "spec_identity": "10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714",
    },
    "run": {
        "assessment_outcome": "inconclusive",
        "verification_scope": "clean-environment",
        "verification_verdict": "passed",
        "scope_class": "none",
        "admission": "Admitted",
    },
    "belief": {
        "belief_answer": {"detail": "", "kind": "NoBelief", "reason": "no-directional-outcome"},
        "rederived_equal": True,
    },
    "10b": {
        "evidence_reconstruction.comparison_report_stored": True,
        "evidence_reconstruction.scope_equal": True,
        "evidence_reconstruction.verdict_equal": True,
        "evidence_reconstruction.report_identity_equal": True,
        "evidence_reconstruction.spec_restored_identity_matches_run": True,
        "evidence_reconstruction.audit_check.checked": True,
        "evidence_reconstruction.audit_check.contradiction": None,
    },
    "10c": {
        "fresh_process_restoration.assessment_equal": True,
        "fresh_process_restoration.assessment_restored": True,
        "fresh_process_restoration.belief_equal": True,
        "fresh_process_restoration.prior_pre_grammar": True,
        "fresh_process_restoration.spec_restored": True,
        "prior_corpus_state.audit": BASE_MISMATCH,
    },
    "close": {
        "corpus_check_findings": 0,
        "audit_findings": 0,
        "log_verdict.no-observer.outcome": "unresolvable",
        "log_verdict.head-carrier.outcome": "validated",
    },
    "composite": {
        "composite_receipt": {"node:0": "not-consulted", "node:1": "member", "node:2": "member"},
        "reading_equal": True,
        "reading_rows": {
            TARGET: ["positive", "NoBelief", ["identification:observational"]],
            SPINE: ["negative", "NoBelief", []],
        },
    },
    "transition": {
        "cut31_corpus_state.audit": BASE_MISMATCH,
        "cut31_corpus_state.records_read": 0,
    },
}

# The lines outside `closed` that the fixture's first pass left, as
# (step, class): step 2's modal-sorted refusal, step 4's two, step 9's
# unanchored chain under the empty observer set, and step 10's Q10 spec half.
EXPECTED_OPEN = Counter(
    [(2, "corpus-work"), (4, "design-gap"), (4, "corpus-work"), (9, "corpus-work"), (10, "design-gap")]
)
FAILING_CLASSES = frozenset({"defect", "host"})


def _at(state: dict, key: str) -> object:
    node: object = state
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return MISSING
        node = node[part]
    return node


def _state_failures(state: dict) -> list[str]:
    failed: list[str] = []
    for group, expected in EXPECTED.items():
        for key, want in expected.items():
            got = _at(state, key)
            if got is MISSING:
                failed.append(f"{group}: {key} is missing")
            elif got != want:
                failed.append(f"{group}: {key} is {got!r}, expected {want!r}")
    stored, derived = _at(state, "assessment_identity_stored"), _at(state, "assessment_identity_derived")
    if stored is MISSING or derived is MISSING:
        failed.append("run: assessment_identity_stored or assessment_identity_derived is missing")
    elif stored != derived:
        failed.append(f"run: assessment_identity_stored {stored} differs from assessment_identity_derived {derived}")
    if "composite_refusal" in state:
        failed.append(f"composite: compose refused: {state['composite_refusal']}")
    return failed


def _findings_failures(lines: list[dict]) -> list[str]:
    failed = [
        f"findings: step {line['step']} recorded {line['class']}: {line['reason']}"
        for line in lines
        if line["class"] in FAILING_CLASSES
    ]
    open_lines = Counter(
        (line["step"], line["class"]) for line in lines if line["class"] not in FAILING_CLASSES | {"closed"}
    )
    for (step, cls), count in sorted((open_lines - EXPECTED_OPEN).items()):
        failed.append(f"findings: {count} unexpected step {step} {cls} line(s)")
    for (step, cls), count in sorted((EXPECTED_OPEN - open_lines).items()):
        failed.append(f"findings: {count} expected step {step} {cls} line(s) absent")
    return failed


def failures(state: dict, lines: list[dict]) -> list[str]:
    """Every failed verdict line; empty when the recreation reproduced."""
    return _state_failures(state) + _findings_failures(lines)


def _read(state_file: Path, findings_file: Path) -> tuple[dict, list[dict]]:
    for required in (state_file, findings_file):
        if not required.is_file():
            raise RuntimeError(f"the verdict reads {required}, which does not exist; run the recreation first")
    lines = [json.loads(line) for line in findings_file.read_text().splitlines() if line]
    return json.loads(state_file.read_text()), lines


def main() -> int:
    state, lines = _read(paths.STATE, paths.FINDINGS)
    failed = failures(state, lines)
    for line in failed:
        print(f"FAIL {line}")
    checked = sum(len(group) for group in EXPECTED.values())
    if failed:
        print(f"verdict: failed, {len(failed)} line(s), over {paths.WORK}")
        return 1
    print(f"verdict: passed; {checked} state keys, {len(lines)} findings lines, over {paths.WORK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
