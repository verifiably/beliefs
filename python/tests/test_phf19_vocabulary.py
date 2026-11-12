from hashlib import sha256

import pytest
from conftest import REPO_ROOT
from reproduction import vocabulary

from beliefs import stored
from beliefs.errors import ScienceError
from beliefs.resolution import TermOutcome


def test_literal_dataset_bindings_are_minted_from_exact_list_bytes():
    profile = vocabulary.profile()
    assert set(profile.activated_contracts) == {"general", "biology", "mm30"}
    for name, sort in {
        "clinical-factors": "clinical-factor",
        "stage-levels": "stage-level",
        "cohorts": "cohort",
    }.items():
        content = (REPO_ROOT / f"python/tools/reproduction/phf19-vocabulary/{name}.txt").read_bytes()
        node = stored.dataset_node(
            title=name, resources=[{"name": name + ".txt", "digest": "sha256:" + sha256(content).hexdigest()}]
        )
        compiled = vocabulary.binding_for(sort)
        assert compiled.binding.dataset == node.id
        snap = vocabulary.snapshot_over(stored.dataset_declaration(node), content, compiled)
        assert snap.resolve(compiled, content.decode().splitlines()[0]) == TermOutcome.MEMBER
        with pytest.raises(RuntimeError, match="digest"):
            vocabulary.snapshot_over(stored.dataset_declaration(node), content + b"bad\n", compiled)
        wrong = stored.dataset_node(title="wrong", resources=[{"name": name + ".txt", "digest": "sha256:" + "f" * 64}])
        with pytest.raises(RuntimeError, match="binds"):
            vocabulary.snapshot_over(stored.dataset_declaration(wrong), content, compiled)


def test_legacy_contract_path_fails_explicitly():
    with pytest.raises(ScienceError, match="beliefs-6f039b"):
        vocabulary.contract(REPO_ROOT / "python/tools/reproduction/mm30.yaml")


def test_source_custody_requires_dataset_record_holdings_record_and_bytes(certified_work, monkeypatch):
    from phf19_fixtures import initialize
    from reproduction import hold, paths

    initialize(monkeypatch, certified_work / "phf19")
    assert hasattr(hold, "source"), "per-run source holdings are missing"
    saved = hold.source("hgnc.tsv", b"hgnc_id\nHGNC:5\n")
    from beliefs.corpus import ReadView

    view = ReadView.opened_at(paths.CORPUS_ROOT)
    assert hold.restore(saved, view) == b"hgnc_id\nHGNC:5\n"
    (paths.STORE_ROOT / "phf19-sources/hgnc.tsv").write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="digest"):
        hold.restore(saved, view)


def test_complete_hgnc_membership_does_not_manufacture_absence():
    from phf19_fixtures import FIXTURE
    from reproduction.analysis_inputs import hgnc_members

    from beliefs.resolution import build_snapshot

    compiled = vocabulary.profile().sorts["biology/gene"]
    snap = build_snapshot(
        readable={compiled.binding: hgnc_members((FIXTURE / "hgnc.tsv").read_bytes()).decode().splitlines()}
    )
    assert snap.resolve(compiled, "hgnc:5") == TermOutcome.MEMBER
    assert snap.resolve(compiled, "hgnc:9999999") == TermOutcome.NOT_MEMBER
    assert (
        snap.resolve(vocabulary.profile().sorts["biology/ensembl-gene"], "ensembl:ENSG00000119403")
        == TermOutcome.NOT_CONSULTED
    )


def test_mm30_register_covers_its_six_declarations():
    import json

    from beliefs.register import register_entry_keys, register_from_projection

    value = register_from_projection(
        json.loads((REPO_ROOT / "python/tools/reproduction/mm30-phf19-register.json").read_text()),
        source="mm30-register",
    )
    assert set(value.entries) == register_entry_keys(vocabulary.contract())
    assert len(value.entries) == 6
