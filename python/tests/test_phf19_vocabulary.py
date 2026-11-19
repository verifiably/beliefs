from hashlib import sha256

import pytest
from conftest import REPO_ROOT
from reproduction import vocabulary

from beliefs import stored
from beliefs.contract.domain import DatasetBinding
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
        assert isinstance(compiled.binding, DatasetBinding)
        assert compiled.binding.dataset == node.id
        snap = vocabulary.snapshot_over(stored.dataset_declaration(node), content, compiled)
        assert snap.resolve(compiled, content.decode().splitlines()[0]) == TermOutcome.MEMBER
        with pytest.raises(RuntimeError, match="digest"):
            vocabulary.snapshot_over(stored.dataset_declaration(node), content + b"bad\n", compiled)
        wrong = stored.dataset_node(title="wrong", resources=[{"name": name + ".txt", "digest": "sha256:" + "f" * 64}])
        with pytest.raises(RuntimeError, match="binds"):
            vocabulary.snapshot_over(stored.dataset_declaration(wrong), content, compiled)


def test_legacy_contract_path_fails_explicitly():
    with pytest.raises(ScienceError, match=r"use mm30-phf19\.yaml"):
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


def test_source_adoption_preserves_the_phf19_genesis_and_current_pin():
    import json

    from beliefs.profile import compile_profile, shipped_domain_contract
    from beliefs.register import register_entry_keys, register_identity

    rows = json.loads((REPO_ROOT / "contracts/source-ownership/INVENTORY.json").read_bytes())["lineages"]["mm30"][
        "revisions"
    ]
    genesis, head = rows[0], rows[-1]
    identity = "5d3f0b25bc6173e9321de2f3d020ff0e110fa00b1eebf2d5c5a3b2666a734c2d"
    selected = vocabulary.revision(content_identity=identity)
    assert genesis["contract_identity"] == selected.contract.content_identity == identity
    assert sha256((REPO_ROOT / genesis["contract_path"]).read_bytes()).hexdigest() == genesis["contract_sha256"]
    assert sha256((REPO_ROOT / genesis["register_path"]).read_bytes()).hexdigest() == genesis["register_sha256"]
    assert register_identity(selected.register) == genesis["register_identity"]
    assert selected.contract.defining_source is None
    assert set(selected.register.entries) == register_entry_keys(selected.contract)
    assert len(selected.register.entries) == 6
    peers = [shipped_domain_contract(ns) for ns in ("general", "biology")]
    original = compile_profile(vocabulary.base(), [*peers, selected.contract])
    assert original.compiled_identity == "080fd67b17a99384bf0e0ad5638aaa09b4902d71d885e9ec22ed5e9d47c2eb8b"

    current = vocabulary.revision()
    assert current.contract.content_identity == head["contract_identity"]
    assert register_identity(current.register) == head["register_identity"]
    assert current.register.describes == vocabulary.pins().domains["mm30"]


def test_successor_head_and_historical_mount(tmp_path):
    from fixtures.phf19_history import phf19_history

    from beliefs.mount import compile_mount_profile
    from beliefs.profile import compile_profile, shipped_domain_contract
    from beliefs.register import register_identity
    from beliefs.world import CorpusManifest, manifest_bytes

    (original,) = phf19_history(tmp_path / "original", successors=0)
    genesis_profile = vocabulary.profile(original.contract_path)
    manifest = CorpusManifest(2, "a" * 32, vocabulary.pins(original.contract_path))
    (tmp_path / "corpus.yaml").write_bytes(manifest_bytes(manifest))

    genesis, head = phf19_history(tmp_path / "updated")
    selected = vocabulary.revision(head.contract_path)
    assert vocabulary.contract(head.contract_path).content_identity == head.contract.content_identity
    assert selected.register.describes == vocabulary.pins(head.contract_path).domains["mm30"]
    assert register_identity(selected.register) == register_identity(head.register)

    old = vocabulary.revision(head.contract_path, content_identity=genesis.contract.content_identity)
    peers = [shipped_domain_contract(ns) for ns in ("general", "biology")]
    recovered = compile_profile(vocabulary.base(), [*peers, old.contract])
    assert recovered.compiled_identity == genesis_profile.compiled_identity
    assert register_identity(old.register) == register_identity(original.register)
    assert compile_mount_profile(tmp_path, available=(old.contract,)).compiled_identity == recovered.compiled_identity


@pytest.mark.parametrize("selector", ["f" * 64, "../outside", "A" * 64, ""])
def test_exact_selection_refuses_a_missing_or_malformed_identity(tmp_path, selector):
    from fixtures.phf19_history import phf19_history

    from beliefs.errors import ProfileError

    _, head = phf19_history(tmp_path)
    with pytest.raises(ProfileError, match=r"mm30-phf19\.yaml: .*identity"):
        vocabulary.revision(head.contract_path, content_identity=selector)


def test_old_selection_checks_head_under_the_requested_base(tmp_path):
    import yaml
    from fixtures.phf19_history import phf19_history

    from beliefs.contract.base import parse_base_contract
    from beliefs.errors import ProfileError

    document = yaml.safe_load((REPO_ROOT / "contracts/science/CONTRACT.yaml").read_bytes())
    document["claim_grammar"]["layers"].remove("methodological")
    base = parse_base_contract(document, source="restricted fixture base")
    (original,) = phf19_history(tmp_path / "original", successors=0)
    old = vocabulary.revision(original.contract_path, content_identity=original.contract.content_identity, base=base)
    assert old.contract.base_identity == base.content_identity

    _, head = phf19_history(tmp_path / "updated", template_layer="methodological")
    assert vocabulary.revision(head.contract_path).contract.content_identity == head.contract.content_identity
    with pytest.raises(ProfileError, match=r"mm30-phf19\.yaml: .*fixture-template.*methodological"):
        vocabulary.revision(head.contract_path, content_identity=old.contract.content_identity, base=base)


def test_hold_stores_the_selected_register(certified_work, monkeypatch):
    import json
    from dataclasses import replace

    from phf19_fixtures import FIXTURE, initialize
    from reproduction import hold, paths, state

    from beliefs.register import register_from_stored, register_identity
    from beliefs.world import load_manifest

    writer = initialize(monkeypatch, certified_work / "phf19-checked-register")
    current = vocabulary.revision()
    entries = dict(current.register.entries)
    key = "sort:mm30/cohort"
    entries[key] = replace(entries[key], licenses=entries[key].licenses + " Fixture change.")
    selected = replace(current.register, entries=entries)
    choice = replace(current, register=selected)
    monkeypatch.setattr(vocabulary, "revision", lambda: choice, raising=False)
    hold.prepare_phf19(
        json.loads((FIXTURE / "declaration.json").read_bytes()),
        predecessor=FIXTURE / "predecessor",
        hgnc=FIXTURE / "hgnc.tsv",
        ensembl=FIXTURE / "ensembl.gtf.gz",
    )
    stored_id = state.load()["registers"][-1]
    assert stored_id == register_identity(selected)
    assert (
        register_from_stored(writer.read_view.get(stored_id)).describes
        == (load_manifest(paths.CORPUS_ROOT).profile.domains["mm30"])
    )
