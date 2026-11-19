"""Evidence for the refusal of the historical mm30 prognosis composite."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import yaml

__all__ = ["SurvivalEvidence", "read_survival"]

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
