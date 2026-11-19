"""Evidence for the refusal of the historical mm30 prognosis composite."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import yaml

__all__ = ["SurvivalEvidence", "main", "read_survival"]

_DECLARATION = Path(__file__).with_name("phf19-inputs.json")
_SURVIVAL = "protein-phf19-associates-with-concept-patient-survival"
_NARRATIVE = "0002-h1-phf19-prognostic-independence"
_SURVIVAL_SHA256 = "4a12955ca187c8ab66896b8997ca59eaf675a05bccfa86a7add71f10d82ea4ea"
_NARRATIVE_SHA256 = "6ec9b713bddbf8306124400acc9f7ca0422fe23ac29300b8e2d94f8d73d2496c"


@dataclass(frozen=True)
class _Source:
    id: str
    sha256: str
    content: bytes


@dataclass(frozen=True)
class SurvivalEvidence:
    proposition: _Source
    narrative: _Source
    subject: str
    predicate: str
    object: str
    identification_strength: str
    claim_layer: str
    narrative_interpretation: str


def _pinned_source(directory: Path, root: Path, slug: str, digest: str) -> tuple[_Source, dict]:
    path = (directory / f"{slug}.md").resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{slug}: source resolves outside {root}")
    content = path.read_bytes()
    if sha256(content).hexdigest() != digest:
        raise ValueError(f"{slug}: digest differs from the pinned source")
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError(f"{slug}: invalid UTF-8") from error
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError(f"{slug}: missing or unterminated front matter")
    try:
        fields = yaml.safe_load("\n".join(lines[1 : lines.index("---", 1)]))
    except yaml.YAMLError as error:
        raise ValueError(f"{slug}: invalid front matter YAML: {error}") from error
    if not isinstance(fields, dict):
        raise TypeError(f"{slug}: front matter must be a mapping")
    expected_id = f"proposition:{slug}"
    if fields.get("id") != expected_id:
        raise ValueError(f"{slug}: source id differs from {expected_id}")
    return _Source(expected_id, digest, content), fields


def _survival(directory: Path, root: Path) -> SurvivalEvidence:
    proposition, fields = _pinned_source(directory, root, _SURVIVAL, _SURVIVAL_SHA256)
    narrative, _ = _pinned_source(directory, root, _NARRATIVE, _NARRATIVE_SHA256)
    expected = {
        "subject": "protein:PHF19",
        "predicate": "associates_with",
        "object": "concept:patient-survival",
        "identification_strength": "observational",
    }
    for field, value in expected.items():
        if fields.get(field) != value:
            raise ValueError(f"{proposition.id}: {field} differs from {value}")
    claim_layer = fields.get("claim_layer")
    if not isinstance(claim_layer, str) or not claim_layer:
        raise ValueError(f"{proposition.id}: missing claim_layer")
    return SurvivalEvidence(
        proposition=proposition,
        narrative=narrative,
        subject=expected["subject"],
        predicate=expected["predicate"],
        object=expected["object"],
        identification_strength=expected["identification_strength"],
        claim_layer=claim_layer,
        narrative_interpretation=(
            "The narrative describes prognostic information. It does not establish a directly identified survival effect."
        ),
    )


def read_survival(predecessor: Path) -> SurvivalEvidence:
    root = predecessor.resolve()
    return _survival(root / "entities/propositions", root)


def _sync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish(path: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        try:
            _sync_directory(path.parent)
        except OSError:
            path.unlink()
            raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _report(work: Path, evidence: SurvivalEvidence) -> dict[str, object]:
    from beliefs.estimand import MeasuredBinding, RuleClassLevels
    from reproduction import paths, phf19, type_target

    child = work / "phf19"
    if paths.WORK != child:
        raise RuntimeError("PHF19 readback is bound to a different work directory")
    positive = json.loads((child / "phf19-report.json").read_text())
    findings = [json.loads(line) for line in paths.FINDINGS.read_text().splitlines()]
    recovered, target = phf19._readback()
    if (
        not isinstance(positive, dict)
        or positive != {**recovered, "fresh_process_equal": True}
        or phf19.verdict(positive, findings)
    ):
        raise RuntimeError("PHF19 verification or stored readback differs from the successful child verdict")

    inputs = target.inputs
    response = target.estimand.bindings["response"]
    grouping = target.estimand.bindings["grouping"]
    # PHF19 readback compares the full stored estimand with its checked reconstruction.
    if not isinstance(response, MeasuredBinding) or not isinstance(grouping, RuleClassLevels):
        raise TypeError("PHF19 stored target lacks the measured RNA stage contrast")
    observable = response.measure.observable
    if observable != type_target.OBSERVABLE or observable.aspect is None:
        raise RuntimeError("PHF19 stored measurement differs from the gene-level RNA observable")

    return {
        "verdict": "refused",
        "corpus_id": target.corpus_id,
        "phf19": positive,
        "stage_to_protein": {
            "reason": "The stored statistical PD vs NDMM contrast measures gene-level RNA. It cannot identify a disease-stage effect on PHF19 protein.",
            "proposed_edge": {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19"},
            "source": {"id": inputs.source_proposition, "sha256": inputs.digests["proposition"]},
            "replacement": {
                "proposition_id": target.proposition_id,
                "claim_identity": recovered["claim_identity"],
                "operator": target.claim.operator,
                "layer": target.claim.layer,
                "factor": inputs.factor,
                "gene": inputs.gene,
                "feature": inputs.feature,
                "rna_aspect": observable.aspect.term,
                "levels": [level.term for level in grouping.classes],
            },
        },
        "protein_to_survival": {
            "reason": "The source is an observational association with patient survival. It cannot identify a causal effect on overall survival.",
            "proposed_edge": {"subject": "protein:PHF19", "predicate": "affects", "object": "concept:overall-survival"},
            "source": {
                "id": evidence.proposition.id,
                "sha256": evidence.proposition.sha256,
                "subject": evidence.subject,
                "predicate": evidence.predicate,
                "object": evidence.object,
                "claim_layer": evidence.claim_layer,
                "identification_strength": evidence.identification_strength,
            },
            "narrative": {
                "id": evidence.narrative.id,
                "sha256": evidence.narrative.sha256,
                "interpretation": evidence.narrative_interpretation,
            },
        },
    }


def main(argv: list[str]) -> int:
    from reproduction import phf19

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work")
    for name in ("predecessor", "hgnc", "ensembl"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args(argv)
    try:
        hgnc, ensembl = args.hgnc.resolve(), args.ensembl.resolve()
        if hgnc.is_dir() or ensembl.is_dir():
            raise ValueError(
                "the last two arguments are HGNC/Ensembl release files; cut archives are no longer accepted"
            )
        if not hgnc.is_file() or not ensembl.is_file():
            raise ValueError("the last two arguments must be regular HGNC/Ensembl release files")
        work = phf19._work(args.work, existing=False)
        child = work / "phf19"
        predecessor = args.predecessor.resolve()
        if not (predecessor / "science.yaml").is_file():
            raise ValueError("PREDECESSOR must contain science.yaml")
        os.environ["SCIENCE_MM30_ROOT"] = str(child)
        os.environ["MM30_PREDECESSOR"] = str(predecessor)
        from reproduction import analysis_inputs

        declaration = json.loads(_DECLARATION.read_text())
        if not isinstance(declaration, dict):
            raise TypeError("PHF19 declaration must be a mapping")
        analysis_inputs.resolve_phf19(declaration, predecessor=predecessor, hgnc=hgnc, ensembl=ensembl)
        evidence = read_survival(predecessor)
        work.mkdir(parents=True, exist_ok=False)
        status = phf19.main([str(child), str(predecessor), str(hgnc), str(ensembl), "--declaration", str(_DECLARATION)])
        if status != 0:
            return status

        retained = work / "evidence"
        retained.mkdir()
        _sync_directory(work)
        _publish(retained / f"{_SURVIVAL}.md", evidence.proposition.content)
        _publish(retained / f"{_NARRATIVE}.md", evidence.narrative.content)
        report = _report(work, _survival(retained, work))
        content = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
        _publish(work / "heritage-report.json", content)
        print("mm30 recreation verified; historical causal composite refused")
        return 0
    except Exception as error:  # noqa: BLE001 -- CLI boundary reports the concrete refusal and exits.
        print(f"mm30 recreation refused: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
