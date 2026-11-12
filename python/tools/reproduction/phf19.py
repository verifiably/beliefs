"""One PHF19 engineering demonstration; initialize paths before helper imports."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path

REQUIRED = {
    "source_closure": True,
    "authored_identities": True,
    "dependency_closure": True,
    "conforming": True,
    "verification_scope": "clean-environment",
    "verification_verdict": "passed",
    "admission": "Admitted",
    "corpus_check_findings": 0,
    "audit_findings": 0,
    "assessment_recovered": True,
    "belief_recovered": True,
    "comparison_recovered": True,
    "fresh_process_equal": True,
}


def verdict(state: Mapping[str, object], findings: Sequence[Mapping[str, object]]) -> list[str]:
    failures = [
        key
        for key, value in REQUIRED.items()
        if key not in state or type(state[key]) is not type(value) or state[key] != value
    ]
    effect = state.get("effect")
    if type(effect) not in (int, float) or not math.isfinite(effect) or not 0 <= effect <= 1:
        failures.append("effect")
    failures.extend(
        str(f.get("reason", "unexplained step failure"))
        for f in findings
        if f.get("class") not in {"closed", "corpus-work"}
    )
    return failures


def _work(value: str, *, existing: bool) -> Path:
    from checkout import MAIN_CHECKOUT

    work = Path(value)
    declared = os.environ.get("WORK_ROOT")
    if not declared:
        raise ValueError("WORK_ROOT must name explicit host-local storage")
    root = Path(declared)
    if not root.is_absolute() or root != root.resolve() or not work.is_absolute() or work != work.resolve():
        raise ValueError("work and WORK_ROOT must be absolute canonical paths")
    if work == root or not work.is_relative_to(root) or work.is_relative_to(MAIN_CHECKOUT.resolve()):
        raise ValueError("work must be below WORK_ROOT and outside the synced checkout")
    if existing:
        if not work.is_dir():
            raise ValueError("readback work directory is absent")
    elif work.exists():
        raise ValueError("work directory already exists; select a fresh destination")
    return work


def readback() -> dict[str, object]:
    """Read stored recovery and recompute its estimand; never call spec.frozen()."""
    import csv

    from beliefs import stored
    from beliefs.admission import Admitted, admit
    from beliefs.applicability import applicability_projection
    from beliefs.assess import AssessmentFinding, build_assessment
    from beliefs.audit import audit_corpus
    from beliefs.confinement import bundle_identity
    from beliefs.corpus import ReadView, corpus_check
    from beliefs.decode import claim_from_stored
    from beliefs.estimand import estimand_projection
    from beliefs.evaluation import gather
    from beliefs.identity import v1
    from beliefs.procedure import procedure_identity
    from beliefs.projection import claim_identity
    from beliefs.replay import CONFORMING, conformance
    from beliefs.runrecord import decode_run_closure
    from reproduction import answers, belief, close, hold, paths, rederive, spec, state, type_target, vocabulary, world

    st = state.load()
    profile = vocabulary.profile()
    view = ReadView.opened_at(paths.CORPUS_ROOT)
    inputs = hold.recover_inputs()
    snapshot = vocabulary.snapshot()
    frozen = stored.analysis_spec_value(view.get(st["spec_ref"]), profile=profile)
    claim, _ = claim_from_stored(view.get(st["proposition_ref"]), profile=profile, snapshot=snapshot)
    parser, estimator = type_target.implementation_digests(spec.code_root())
    if (parser, estimator) != type_target.implementation_digests():
        raise RuntimeError("bundle parser/estimator differs from reviewed code")
    rebuilt, app = type_target.estimand(
        inputs,
        profile=profile,
        claim=claim,
        records=spec._HeldRecords(view),
        snapshot=snapshot,
        assay_id=st["assay_ref"],
        grouping_rule_id=st["grouping_rule_ref"],
        parser_digest=parser,
        estimator_digest=estimator,
    )
    declarations = v1.decode(paths.TARGET.read_bytes())
    authored = (
        frozen.identity == st["spec_identity"]
        and frozen.target == st["proposition_ref"] == "proposition:phf19-rna-pd-vs-ndmm"
        and claim_identity(claim) == st["claim_identity"]
        and v1.encode(estimand_projection(rebuilt)) == v1.encode(estimand_projection(frozen.estimand))
        and v1.encode(declarations["estimand"]) == v1.encode(estimand_projection(rebuilt))
        and v1.encode(applicability_projection(app)) == v1.encode(applicability_projection(frozen.applicability))
        and world.open_writer().manifest_pins() == vocabulary.pins()
    )
    expected = {st["assay_ref"], st["estimator_ref"], st["grouping_rule_ref"], st["mapping_ref"], *st["registers"]}
    closure = expected <= {d.id for d in frozen.assessed_target.dependencies} and all(
        view.holds(ref) for ref in expected
    )
    original = decode_run_closure(view.get(st["original_run_ref"]))
    replayed = decode_run_closure(view.get(st["replayed_run_ref"]))
    value = stored.assessment_value(view.get(st["assessment_ref"]), profile=profile)
    assessment = build_assessment(
        original, specs={frozen.identity: frozen}, implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION}
    )
    recovered = (
        not isinstance(assessment, AssessmentFinding)
        and assessment.identity()
        == value.identity()
        == st["assessment_identity_derived"]
        == st["assessment_identity_stored"]
    )
    gathered = gather(
        view,
        st["proposition_ref"],
        key=value.key(),
        observations=belief.observations_from_corpus(view),
        context=belief.context(view),
        profile=profile,
        resolution=snapshot,
        binding=belief.BINDING,
    )
    admitted = admit(
        value,
        gathered.runs[value.run],
        belief.observations_from_corpus(view),
        gathered.verifications,
        gathered.dependencies,
    )
    admission = "Admitted" if isinstance(admitted, Admitted) else "AdmissionRefused: " + admitted.reason
    answer = answers.payload(belief.evaluate_here(view))
    evidence = close.evidence_for(view, profile)
    comparison = rederive.reconstruct(view, st, evidence)
    compared = all(
        comparison.get(k) is True
        for k in (
            "comparison_report_stored",
            "derivation_named",
            "closures_decoded",
            "scope_equal",
            "verdict_equal",
            "report_identity_equal",
            "spec_restored_identity_matches_run",
        )
    )
    compared = (
        compared and comparison["audit_check"]["checked"] is True and comparison["audit_check"]["contradiction"] is None
    )
    # An estimate is read from covered output bytes, never manufactured from a digest.
    artifact = Path(original.occurrence.receipt.execution.scratch_mapping) / "out/outputs/stats.tsv"
    if not artifact.resolve().is_relative_to(paths.WORK.resolve()):
        raise RuntimeError("run output is outside this work directory")
    content = artifact.read_bytes()
    if "sha256:" + sha256(content).hexdigest() != dict(original.result.outputs)["outputs/stats.tsv"]:
        raise RuntimeError("stats output differs from its run manifest digest")
    rows = list(csv.DictReader(content.decode().splitlines(), delimiter="\t"))
    if len(rows) != 1 or set(rows[0]) != {"effect", "z", "p", "n"}:
        raise RuntimeError("stats output has an unexpected shape")
    _, expected_estimator, _ = type_target.procedures(inputs, parser_digest=parser, estimator_digest=estimator)
    estimator_ref = procedure_identity(expected_estimator)
    code_identity = bundle_identity(spec.code_root().parent)
    authored = authored and (
        st["estimator_ref"] == estimator_ref
        and any(b.rule == spec.INTERPRETATION_RULE and b.procedure == estimator_ref for b in frozen.rule_bindings)
        and declarations.get("estimator_procedure") == estimator_ref
        and declarations.get("value_row") == inputs.feature
        and declarations.get("group_separator") == inputs.separator
        and declarations.get("positive_level") == "PD"
        and original.recipe.spec_identity == replayed.recipe.spec_identity == frozen.identity
        and original.recipe.code_identity == replayed.recipe.code_identity == code_identity
        and (spec.code_root() / "workflow/Snakefile").read_bytes()
        == spec.snakefile_bytes(Path(st["held_file"]).name, inputs.feature, inputs.separator)
    )
    verification = stored.verification_value(view.get(st["verification_ref"]))
    return {
        "source_closure": True,
        "authored_identities": authored,
        "dependency_closure": closure,
        "conforming": conformance(original) == CONFORMING and conformance(replayed) == CONFORMING,
        "verification_scope": verification.scope,
        "verification_verdict": verification.verdict,
        "admission": admission if admission == st["admission"] else "stale admission sidecar",
        "corpus_check_findings": len(corpus_check(view, profile)),
        "audit_findings": len(audit_corpus(view, evidence=evidence, profile=profile)),
        "assessment_recovered": recovered,
        "belief_recovered": answer == st["belief_answer"],
        "comparison_recovered": compared,
        "effect": float(rows[0]["effect"]),
        "spec_identity": frozen.identity,
        "claim_identity": claim_identity(claim),
        "answer": answer,
        "limitation": "Engineering demonstration; source pairing is unmodeled, independence and assay validity are unestablished.",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    if argv[:1] == ["--readback"]:
        parser.add_argument("--readback", required=True)
        arguments = parser.parse_args(argv)
        try:
            work = _work(arguments.readback, existing=True)
            os.environ["SCIENCE_MM30_ROOT"] = str(work)
            # No acquisition/predecessor directory is needed for stored recovery.
            os.environ["MM30_PREDECESSOR"] = str(work / "unused-predecessor")
            report = readback()
            from reproduction import paths

            rows = [json.loads(line) for line in paths.FINDINGS.read_text().splitlines()]
            failures = [f for f in verdict(report, rows) if f != "fresh_process_equal"]
            print(json.dumps(report, sort_keys=True))
            if failures:
                print("PHF19 readback failed: " + ", ".join(failures), file=sys.stderr)
                return 1
            return 0
        except Exception as error:  # noqa: BLE001 -- CLI boundary reports the concrete refusal and exits.
            print(f"PHF19 readback refused: {type(error).__name__}: {error}", file=sys.stderr)
            return 2
    for name in ("work", "predecessor", "hgnc", "ensembl"):
        parser.add_argument(name)
    parser.add_argument("--declaration", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        work = _work(arguments.work, existing=False)
        os.environ["SCIENCE_MM30_ROOT"] = str(work)
        os.environ["MM30_PREDECESSOR"] = str(Path(arguments.predecessor).resolve())
        from reproduction import (
            analysis_inputs,
            hold,
            lists,
            paths,
            preflight,
            spec,
            state,
            type_target,
            world,
        )

        declaration = json.loads(arguments.declaration.read_text())
        if not isinstance(declaration, dict):
            raise TypeError("declaration must be a mapping")
        predecessor = Path(arguments.predecessor).resolve()
        hgnc = Path(arguments.hgnc).resolve()
        ensembl = Path(arguments.ensembl).resolve()
        analysis_inputs.resolve_phf19(declaration, predecessor=predecessor, hgnc=hgnc, ensembl=ensembl)
        if preflight.main() != 0 or world.main() != 0:
            return 2
        lists.prepare()
        world.adopt()
        hold.prepare_phf19(declaration, predecessor=predecessor, hgnc=hgnc, ensembl=ensembl)
        for step in (type_target.main, spec.main):
            if step() != 0:
                return 2
        home = work / "readback-home"
        home.mkdir()
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
            "WORK_ROOT": os.environ["WORK_ROOT"],
            "SCIENCE_MM30_ROOT": str(work),
            "MM30_PREDECESSOR": str(predecessor),
        }
        # Low-level run publication is observed through a fresh process's index.
        for module in ("run", "belief", "close"):
            completed = subprocess.run(
                [sys.executable, "-m", "reproduction." + module],
                env=environment,
                cwd=Path(__file__).resolve().parents[2],
                check=False,
                timeout=600,
            )
            if completed.returncode != 0:
                return 2
        local = readback()
        child = subprocess.run(
            [sys.executable, "-m", "reproduction.phf19", "--readback", str(work)],
            env=environment,
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if child.returncode not in (0, 1):
            raise RuntimeError(child.stderr)
        recovered = json.loads(child.stdout)
        report = {**local, "fresh_process_equal": local == recovered}
        rows = [json.loads(line) for line in paths.FINDINGS.read_text().splitlines()]
        failures = verdict(report, rows)
        state.save(phf19_report=report, phf19_failures=failures)
        (work / "phf19-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        if failures:
            print("PHF19 failed: " + ", ".join(failures), file=sys.stderr)
            return 1
        print("PHF19 engineering demonstration verified; effect=" + str(report["effect"]))
        return 0
    except Exception as error:  # noqa: BLE001 -- CLI boundary reports the concrete refusal and exits.
        print(f"PHF19 refused: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
