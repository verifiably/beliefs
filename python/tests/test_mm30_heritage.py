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
    records.mkdir(parents=True, exist_ok=True)
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


def _invocation(tmp_path, monkeypatch):
    import shutil
    from pathlib import Path

    # Modules in this test process may share the default path bindings; only the
    # certified subprocess relies on paths binding to the fresh child on import.
    from reproduction import analysis_inputs, phf19

    assert callable(analysis_inputs.resolve_phf19)
    fixture = Path(__file__).resolve().parents[2] / "fixtures/phf19"
    predecessor = tmp_path / "predecessor"
    shutil.copytree(fixture / "predecessor", predecessor)
    heritage, source, narrative = _survival(predecessor, monkeypatch)
    work = tmp_path / "missing" / "also-missing" / "fresh"
    monkeypatch.setenv("WORK_ROOT", str(tmp_path))
    monkeypatch.setenv("SCIENCE_MM30_ROOT", "uninitialized")
    monkeypatch.setenv("MM30_PREDECESSOR", "uninitialized")
    monkeypatch.setattr(heritage, "_DECLARATION", fixture / "declaration.json", raising=False)
    argv = [str(work), str(predecessor), str(fixture / "hgnc.tsv"), str(fixture / "ensembl.gtf.gz")]
    return heritage, phf19, work, argv, source, narrative


@pytest.mark.parametrize("slot", [2, 3])
def test_archive_in_either_release_slot_refuses_before_work(tmp_path, monkeypatch, capsys, slot):
    heritage, _, work, argv, _, _ = _invocation(tmp_path, monkeypatch)
    argv[slot] = str(tmp_path)
    assert heritage.main(argv) != 0
    assert "cut archives are no longer accepted" in capsys.readouterr().err
    assert not work.parent.exists()


@pytest.mark.parametrize("change", ["release", "survival", "marker"])
def test_invalid_inputs_refuse_before_claim(tmp_path, monkeypatch, capsys, change):
    from pathlib import Path

    heritage, _, work, argv, source, _ = _invocation(tmp_path, monkeypatch)
    if change == "release":
        wrong = tmp_path / "wrong.tsv"
        wrong.write_text("not the pinned TSV")
        argv[2] = str(wrong)
        diagnostic = "hgnc digest"
    elif change == "survival":
        source.write_bytes(b"wrong")
        diagnostic = "digest differs"
    else:
        (Path(argv[1]) / "science.yaml").unlink()
        diagnostic = "science.yaml"
    assert heritage.main(argv) != 0
    assert diagnostic in capsys.readouterr().err
    assert not work.parent.exists()


def test_failed_phf19_child_keeps_diagnosis_and_cannot_be_reused(tmp_path, monkeypatch, capsys):
    import os

    heritage, phf19, work, argv, _, _ = _invocation(tmp_path, monkeypatch)
    calls = []

    def fail(args):
        calls.append(args)
        child = work / "phf19"
        assert work.is_dir()
        assert not child.exists()
        assert os.environ["SCIENCE_MM30_ROOT"] == str(child)
        assert os.environ["MM30_PREDECESSOR"] == argv[1]
        assert args == [str(child), *argv[1:], "--declaration", str(heritage._DECLARATION)]
        child.mkdir()
        (child / "phf19-report.json").write_text('{"verification_verdict": "passed", "fresh_process_equal": true}')
        return 17

    monkeypatch.setattr(phf19, "main", fail)
    assert heritage.main(argv) == 17
    assert len(calls) == 1
    assert not (work / "heritage-report.json").exists()
    assert (work / "phf19/phf19-report.json").exists()
    assert not (work / "evidence").exists()
    assert heritage.main(argv) != 0
    assert "already exists" in capsys.readouterr().err
    assert len(calls) == 1


def test_losing_a_competing_claim_preserves_the_winners_directory(tmp_path, monkeypatch):
    from pathlib import Path

    heritage, phf19, work, argv, _, _ = _invocation(tmp_path, monkeypatch)
    work.parent.mkdir(parents=True)
    mkdir = Path.mkdir

    def competing_mkdir(self, *args, **kwargs):
        if self == work:
            mkdir(self)
            (self / "winner").write_text("kept")
        mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", competing_mkdir)
    monkeypatch.setattr(phf19, "main", lambda _: pytest.fail("the loser started PHF19"))
    assert heritage.main(argv) != 0
    assert [p.name for p in work.iterdir()] == ["winner"]
    assert (work / "winner").read_text() == "kept"


def test_second_evidence_sync_failure_leaves_no_terminal_report(tmp_path, monkeypatch, capsys):
    import os
    import stat

    heritage, phf19, work, argv, source, _ = _invocation(tmp_path, monkeypatch)
    fsync = os.fsync
    retained = work / "evidence"

    def fail_second_file_sync(fd):
        if stat.S_ISREG(os.fstat(fd).st_mode) and (retained / source.name).exists():
            raise OSError("second evidence file sync failed")
        fsync(fd)

    monkeypatch.setattr(phf19, "main", lambda _: 0)
    monkeypatch.setattr(os, "fsync", fail_second_file_sync)
    assert heritage.main(argv) != 0
    assert "second evidence file sync failed" in capsys.readouterr().err
    assert [(p.name, p.read_bytes()) for p in retained.iterdir()] == [(source.name, SOURCE_TEXT)]
    assert not (work / "heritage-report.json").exists()


def test_final_directory_sync_failure_leaves_no_terminal_report(tmp_path, monkeypatch, capsys):
    import os
    import stat

    heritage, phf19, work, argv, _, _ = _invocation(tmp_path, monkeypatch)
    fsync = os.fsync
    terminal = work / "heritage-report.json"

    def fail_terminal_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode) and terminal.exists():
            raise OSError("terminal directory sync failed")
        fsync(fd)

    monkeypatch.setattr(phf19, "main", lambda _: 0)
    monkeypatch.setattr(heritage, "_report", lambda *_: {"verdict": "refused"}, raising=False)
    monkeypatch.setattr(os, "fsync", fail_terminal_sync)
    assert heritage.main(argv) != 0
    assert "terminal directory sync failed" in capsys.readouterr().err
    assert not terminal.exists()
