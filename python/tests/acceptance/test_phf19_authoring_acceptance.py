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
