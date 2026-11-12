"""Certified synthetic construction, never a scientific recreation or validation."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
from phf19_fixtures import FIXTURE, initialize
from reproduction import hold, spec, state, type_target, vocabulary

from beliefs import stored
from beliefs.corpus import ReadView


@pytest.fixture()
def authoring_work(work_directory):
    with tempfile.TemporaryDirectory(prefix="phf19-", dir=work_directory) as directory:
        yield Path(directory)


def authored(monkeypatch, root):
    initialize(monkeypatch, root)
    declaration = json.loads((FIXTURE / "declaration.json").read_text())
    assert hasattr(hold, "prepare_phf19"), "PHF19 source-chain preparation is missing"
    hold.prepare_phf19(
        declaration, predecessor=FIXTURE / "predecessor", hgnc=FIXTURE / "hgnc.tsv", ensembl=FIXTURE / "ensembl.gtf.gz"
    )
    assert type_target.main() == 0
    assert spec.main() == 0
    return state.load()


def test_authoring_freezes_and_recovers_through_public_builders(monkeypatch, authoring_work, tmp_path):
    root = authoring_work / "phf19-authoring"
    st = authored(monkeypatch, root)
    view = ReadView.opened_at(root / "corpus")
    frozen = stored.analysis_spec_value(view.get(st["spec_ref"]), profile=vocabulary.profile())
    assert frozen.identity == st["spec_identity"]
    from beliefs.estimand import estimand_from_stored
    from beliefs.identity import v1

    declaration = v1.decode((root / "target.yaml").read_bytes())
    assert isinstance(declaration, dict)
    assert estimand_from_stored(declaration["estimand"], profile=vocabulary.profile()) == frozen.estimand

    dependencies = {d.id for d in frozen.estimand.dependencies}
    assert {st["assay_ref"], st["mapping_ref"], st["grouping_rule_ref"]} <= dependencies
    assert len(frozen.registers) == 3
    assert frozen.estimand.assumptions[0].particulars["co_scope"] == "unknown"
    home = tmp_path / "home"
    home.mkdir()
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "PYTHONPATH": str(REPO_ROOT / "python/tools"),
        "SCIENCE_MM30_ROOT": str(root),
        "MM30_PREDECESSOR": str(FIXTURE / "predecessor"),
    }
    script = """
import json
from reproduction import spec,state,world,hold
from beliefs import stored
st=state.load()
value=stored.analysis_spec_value(world.open_writer().read_view.get(st['spec_ref']),profile=spec._context()[2])
rebuilt=spec.frozen()
print(json.dumps({'stored':value.identity,'rebuilt':rebuilt.identity,'source_closure':hold.verify_sources()}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        cwd=REPO_ROOT / "python",
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    recovered = json.loads(result.stdout)
    assert recovered == {"stored": frozen.identity, "rebuilt": frozen.identity, "source_closure": True}


def test_corrupt_mapping_bytes_refuse_before_target_mint(monkeypatch, authoring_work):
    from reproduction import paths

    root = authoring_work / "phf19-corrupt-map"
    initialize(monkeypatch, root)
    hold.prepare_phf19(
        json.loads((FIXTURE / "declaration.json").read_text()),
        predecessor=FIXTURE / "predecessor",
        hgnc=FIXTURE / "hgnc.tsv",
        ensembl=FIXTURE / "ensembl.gtf.gz",
    )
    st = state.load()
    (paths.STORE_ROOT / st["sources"]["mapping-members"]["relative"]).write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="digest"):
        type_target.main()
    assert not any(n.kind == "proposition" for n in ReadView.opened_at(paths.CORPUS_ROOT).iter_stored())


def test_wrong_held_list_dataset_refuses_before_target_mint(monkeypatch, authoring_work):
    from reproduction import paths

    initialize(monkeypatch, authoring_work / "wrong-list")
    hold.prepare_phf19(
        json.loads((FIXTURE / "declaration.json").read_text()),
        predecessor=FIXTURE / "predecessor",
        hgnc=FIXTURE / "hgnc.tsv",
        ensembl=FIXTURE / "ensembl.gtf.gz",
    )
    st = state.load()
    st["sources"]["clinical-factors"]["dataset"] = st["sources"]["cohorts"]["dataset"]
    state.save(sources=st["sources"])
    with pytest.raises(RuntimeError, match="mismatch"):
        type_target.main()
    assert not any(n.kind == "proposition" for n in ReadView.opened_at(paths.CORPUS_ROOT).iter_stored())


def test_smallest_full_path_reaches_terminal_verdict_and_fresh_readback():
    import tempfile

    from checkout import MAIN_CHECKOUT

    # Small synthetic per-run copies; place outside the checkout on its certified volume.
    with tempfile.TemporaryDirectory(prefix=".phf19-cli-", dir=MAIN_CHECKOUT.parent) as directory:
        parent = Path(directory)
        home = parent / "home"
        home.mkdir()
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "PYTHONPATH": str(REPO_ROOT / "python/tools"),
            "WORK_ROOT": str(parent),
        }
        tracked = REPO_ROOT / "python/tools/reproduction/analysis/workflow/Snakefile"
        before = tracked.read_bytes()
        first = None
        for name in ("first", "second"):
            work = parent / name
            args = [
                str(work),
                str(FIXTURE / "predecessor"),
                str(FIXTURE / "hgnc.tsv"),
                str(FIXTURE / "ensembl.gtf.gz"),
                "--declaration",
                str(FIXTURE / "declaration.json"),
            ]
            result = subprocess.run(
                [sys.executable, "-m", "reproduction.phf19", *args],
                env=env,
                cwd=REPO_ROOT / "python",
                capture_output=True,
                text=True,
                check=False,
                timeout=240,
            )
            assert result.returncode == 0, result.stdout + "\n" + result.stderr
            report = json.loads((work / "phf19-report.json").read_text())
            assert report["effect"] == 1.0 and report["fresh_process_equal"] is True
            assert report["authored_identities"] and report["dependency_closure"]
            st = json.loads((work / "state.json").read_text())
            assert not st["phf19_failures"]
            assert all((work / "store" / item["relative"]).exists() for item in st["sources"].values())
            if first is None:
                first = (parent / "first/state.json").read_bytes()
            else:
                assert (parent / "first/state.json").read_bytes() == first
        assert tracked.read_bytes() == before
        from beliefs.identity import v1

        # A stale selection sidecar cannot reinterpret the frozen computation.
        target = parent / "first/target.yaml"
        original_target = target.read_bytes()
        altered = v1.decode(original_target)
        assert isinstance(altered, dict)
        altered["value_row"] = "another-feature"
        target.write_bytes(v1.encode(altered))
        result = subprocess.run(
            [sys.executable, "-m", "reproduction.phf19", "--readback", str(parent / "first")],
            env=env,
            cwd=REPO_ROOT / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert result.returncode != 0 and "authored_identities" in result.stderr
        target.write_bytes(original_target)
        # Omitting a required stored procedure fails independently of sidecars.
        from fixtures_cut4 import path_for

        first_state = json.loads((parent / "first/state.json").read_text())
        procedure = path_for(parent / "first/corpus", first_state["assay_ref"])
        original_procedure = procedure.read_bytes()
        procedure.unlink()
        result = subprocess.run(
            [sys.executable, "-m", "reproduction.phf19", "--readback", str(parent / "first")],
            env=env,
            cwd=REPO_ROOT / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert result.returncode != 0
        procedure.write_bytes(original_procedure)
        # A bundle edit is detected from actual bytes by a separate read process.
        bundle = parent / "second/bundle/analysis/labels.py"
        bundle.write_bytes(bundle.read_bytes() + b"\n# changed\n")
        result = subprocess.run(
            [sys.executable, "-m", "reproduction.phf19", "--readback", str(parent / "second")],
            env=env,
            cwd=REPO_ROOT / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert result.returncode != 0 and "parser/estimator" in result.stderr
        # Missing held closure is also a terminal refusal, independently of its sidecar.
        first_state = json.loads((parent / "first/state.json").read_text())
        (parent / "first/store" / first_state["sources"]["hgnc"]["relative"]).unlink()
        result = subprocess.run(
            [sys.executable, "-m", "reproduction.phf19", "--readback", str(parent / "first")],
            env=env,
            cwd=REPO_ROOT / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert result.returncode != 0


def test_zero_exit_step_defect_fails_the_actual_terminal_command():
    from checkout import MAIN_CHECKOUT

    with tempfile.TemporaryDirectory(prefix=".phf19-defect-", dir=MAIN_CHECKOUT.parent) as directory:
        parent = Path(directory)
        home = parent / "home"
        home.mkdir()
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "PYTHONPATH": str(REPO_ROOT / "python/tools"),
            "WORK_ROOT": str(parent),
        }
        script = """
import sys
from reproduction import phf19
run=phf19.subprocess.run
def with_defect(command,**kwargs):
    result=run(command,**kwargs)
    if len(command)>2 and command[2]=='reproduction.close' and result.returncode==0:
        from reproduction import findings
        findings.record(9,'defect','injected zero-exit step defect')
    return result
phf19.subprocess.run=with_defect
raise SystemExit(phf19.main(sys.argv[1:]))
"""
        work = parent / "run"
        args = [
            str(work),
            str(FIXTURE / "predecessor"),
            str(FIXTURE / "hgnc.tsv"),
            str(FIXTURE / "ensembl.gtf.gz"),
            "--declaration",
            str(FIXTURE / "declaration.json"),
        ]
        result = subprocess.run(
            [sys.executable, "-c", script, *args],
            env=env,
            cwd=REPO_ROOT / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=240,
        )
        assert result.returncode == 1, result.stdout + "\n" + result.stderr
        assert "injected zero-exit step defect" in result.stderr
        assert "injected zero-exit step defect" in json.loads((work / "state.json").read_text())["phf19_failures"]
