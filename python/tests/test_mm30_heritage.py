"""Bind the historical survival decision to the exact predecessor bytes."""

from hashlib import sha256

import pytest

SOURCE = "protein-phf19-associates-with-concept-patient-survival"
NARRATIVE = "0002-h1-phf19-prognostic-independence"
SOURCE_TEXT = b"""---
id: proposition:protein-phf19-associates-with-concept-patient-survival
subject: protein:PHF19
predicate: associates_with
object: concept:patient-survival
identification_strength: observational
claim_layer: causal_effect
---
"""
# Deliberately contains none of the words in the authored interpretation.
NARRATIVE_TEXT = b"""---
id: proposition:0002-h1-phf19-prognostic-independence
---
A different synthetic body.
"""


def _survival(tmp_path, monkeypatch):
    from reproduction import heritage

    records = tmp_path / "entities/propositions"
    records.mkdir(parents=True)
    source = records / f"{SOURCE}.md"
    narrative = records / f"{NARRATIVE}.md"
    source.write_bytes(SOURCE_TEXT)
    narrative.write_bytes(NARRATIVE_TEXT)
    monkeypatch.setattr(heritage, "_SURVIVAL_SHA256", sha256(SOURCE_TEXT).hexdigest())
    monkeypatch.setattr(heritage, "_NARRATIVE_SHA256", sha256(NARRATIVE_TEXT).hexdigest())
    return heritage, source, narrative


def test_survival_keeps_the_checked_bytes_after_source_changes(tmp_path, monkeypatch):
    heritage, source, narrative = _survival(tmp_path, monkeypatch)
    evidence = heritage.read_survival(tmp_path)
    source.write_bytes(b"changed after verification")
    narrative.unlink()
    assert evidence.proposition.content == SOURCE_TEXT
    assert evidence.narrative.content == NARRATIVE_TEXT
    assert evidence.proposition.id == f"proposition:{SOURCE}"
    assert evidence.narrative.id == f"proposition:{NARRATIVE}"
    assert evidence.proposition.sha256 == sha256(SOURCE_TEXT).hexdigest()
    assert evidence.narrative.sha256 == sha256(NARRATIVE_TEXT).hexdigest()
    assert (evidence.subject, evidence.predicate, evidence.object) == (
        "protein:PHF19",
        "associates_with",
        "concept:patient-survival",
    )
    assert evidence.identification_strength == "observational"
    assert evidence.claim_layer == "causal_effect"
    assert "prognostic information" in evidence.narrative_interpretation
    assert "directly identified" in evidence.narrative_interpretation


@pytest.mark.parametrize("change", ["missing", "escaped", "changed", "swapped", "new-narrative"])
def test_missing_or_different_bytes_refuse(tmp_path, monkeypatch, change):
    heritage, source, narrative = _survival(tmp_path, monkeypatch)
    if change == "missing":
        source.unlink()
    elif change == "escaped":
        source.unlink()
        outside = tmp_path / "outside.md"
        outside.write_bytes(SOURCE_TEXT)
        source.symlink_to(outside)
        root = tmp_path / "predecessor"
        root.mkdir()
        (tmp_path / "entities").rename(root / "entities")
        with pytest.raises(ValueError, match="outside"):
            heritage.read_survival(root)
        return
    elif change == "changed":
        source.write_bytes(SOURCE_TEXT + b"changed")
    elif change == "swapped":
        narrative.write_bytes(SOURCE_TEXT)
        source.write_bytes(NARRATIVE_TEXT)
    else:
        narrative.write_bytes(NARRATIVE_TEXT + b"Prognostic information does not identify a direct effect.")
    with pytest.raises((FileNotFoundError, ValueError), match="digest|No such file"):
        heritage.read_survival(tmp_path)


@pytest.mark.parametrize(
    ("content", "diagnostic"),
    [
        (b"id: no-front-matter", "front matter"),
        (b"---\nid: no-closing-delimiter\n", "front matter"),
        (b"---\n--- inline is not a delimiter\n", "front matter"),
        (b"---\n\xff\n---\n", "UTF-8"),
        (b"---\nid: [\n---\n", "YAML"),
        (b"---\n---\n", "mapping"),
        (b"---\n- a sequence\n---\n", "mapping"),
        (SOURCE_TEXT.replace(SOURCE.encode(), b"wrong-id"), "id"),
        (SOURCE_TEXT.replace(b"associates_with", b"affects"), "predicate"),
        (SOURCE_TEXT.replace(b"object: concept:patient-survival", b"object: concept:overall-survival"), "object"),
        (SOURCE_TEXT.replace(b"observational", b"experimental"), "identification_strength"),
        (SOURCE_TEXT.replace(b"protein:PHF19", b"protein:EZH2"), "subject"),
    ],
)
def test_pinned_source_still_requires_valid_front_matter(tmp_path, monkeypatch, content, diagnostic):
    heritage, source, _ = _survival(tmp_path, monkeypatch)
    source.write_bytes(content)
    monkeypatch.setattr(heritage, "_SURVIVAL_SHA256", sha256(content).hexdigest())
    with pytest.raises((TypeError, ValueError), match=diagnostic):
        heritage.read_survival(tmp_path)
