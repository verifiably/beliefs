import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "fixtures/phf19"


def invoke(tmp_path, *arguments, work_root=None):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "PYTHONPATH": str(REPO_ROOT / "python/tools"),
        "WORK_ROOT": str(work_root or tmp_path),
    }
    return subprocess.run(
        [sys.executable, "-m", "reproduction.phf19", *map(str, arguments)],
        cwd=REPO_ROOT / "python",
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_no_declaration_refuses_without_creating_work(tmp_path):
    work = tmp_path / "fresh"
    result = invoke(tmp_path, work, FIXTURE / "predecessor", FIXTURE / "hgnc.tsv", FIXTURE / "ensembl.gtf.gz")
    assert result.returncode != 0
    assert "declaration" in result.stderr
    assert not work.exists()


def test_terminal_verdict_refuses_missing_fields_and_zero_exit_defect():
    driver = importlib.import_module("reproduction.phf19")
    assert driver.verdict({}, [])
    state = {
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
    state["effect"] = 0.5
    assert driver.verdict(state, []) == []
    for key in state:
        missing = dict(state)
        del missing[key]
        assert driver.verdict(missing, []), key
    assert driver.verdict(state, [{"class": "defect", "reason": "step exited zero but failed its obligation"}])
    assert driver.verdict(state, [{"class": "unrecognized", "reason": "malformed finding"}])


@pytest.mark.parametrize("case", ["existing", "synced", "malformed"])
def test_bad_destination_or_declaration_is_refused_before_corpus_write(tmp_path, case):
    work = tmp_path / "fresh"
    declaration = FIXTURE / "declaration.json"
    if case == "existing":
        work.mkdir()
        (work / "keep").write_text("keep")
    if case == "synced":
        work = REPO_ROOT / "should-never-be-created"
    if case == "malformed":
        declaration = tmp_path / "bad.json"
        declaration.write_text("{}")
    result = invoke(
        tmp_path,
        work,
        FIXTURE / "predecessor",
        FIXTURE / "hgnc.tsv",
        FIXTURE / "ensembl.gtf.gz",
        "--declaration",
        declaration,
    )
    assert result.returncode != 0
    assert not (work / "corpus").exists()
    if case == "existing":
        assert (work / "keep").read_text() == "keep"


def test_legacy_recipe_refuses_without_modifying_destination(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    work = tmp_path / "legacy"
    result = subprocess.run(
        ["just", "mm30-recreate", str(work), str(FIXTURE / "predecessor")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert "beliefs-6f039b" in result.stderr
    assert not work.exists()


def test_analysis_loads_the_bundled_parser_with_safe_python_paths(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {"PATH": os.environ["PATH"], "HOME": str(home)}
    assoc = REPO_ROOT / "python/tools/reproduction/analysis/assoc.py"
    matrix = FIXTURE / "predecessor/data/supp/orig/misund2022/GSE179929_gene_tpm.txt.gz"
    result = subprocess.run(
        [
            sys.executable,
            "-P",
            str(assoc),
            str(matrix),
            str(tmp_path / "stats.tsv"),
            str(tmp_path / "outcome.txt"),
            "ENSG00000119403",
            "_",
            "PD",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "stats.tsv").read_text().splitlines()[0] == "effect\tz\tp\tn"
