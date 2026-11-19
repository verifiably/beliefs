"""Read checked PHF19 pairs from standalone head and archive paths."""

import json
import re

import pytest
from fixtures.phf19_history import phf19_history

from beliefs.errors import ProfileError
from beliefs.profile import shipped_base_contract
from beliefs.register import register_identity


@pytest.mark.parametrize("successors", [0, 1, 2])
def test_standalone_pair_history(tmp_path, successors):
    from reproduction.contract_history import load_phf19_history

    pairs = phf19_history(tmp_path / "copied", successors=successors)
    loaded = load_phf19_history(pairs[-1].contract_path, base=shipped_base_contract())
    assert [r.contract.content_identity for r in loaded] == [pair.contract.content_identity for pair in pairs]
    assert [register_identity(r.register) for r in loaded] == [register_identity(pair.register) for pair in pairs]


@pytest.mark.parametrize("index", [0, -1], ids=["archive", "head"])
@pytest.mark.parametrize("root_relative", [False, True])
def test_malformed_register_names_physical_file(tmp_path, index, root_relative):
    from reproduction.contract_history import load_phf19_history

    pairs = phf19_history(tmp_path / "arbitrary/copy")
    damaged = pairs[index].register_path
    damaged.write_text("{")
    root = tmp_path if root_relative else None
    label = damaged.relative_to(root) if root is not None else damaged
    with pytest.raises(ProfileError, match=f"^{re.escape(label.as_posix())}:"):
        load_phf19_history(pairs[-1].contract_path, base=shipped_base_contract(), root=root)


def test_third_pair_requires_immediate_register_predecessor(tmp_path):
    from reproduction.contract_history import load_phf19_history

    genesis, _, head = phf19_history(tmp_path, successors=2)
    payload = json.loads(head.register_path.read_bytes())
    payload["previous"] = register_identity(genesis.register)
    head.register_path.write_text(json.dumps(payload))
    with pytest.raises(ProfileError, match=r"mm30-phf19-register\.json: previous .*immediate"):
        load_phf19_history(head.contract_path, base=shipped_base_contract())


def test_successor_advances_the_documentary_version(tmp_path):
    from dataclasses import replace

    import yaml
    from reproduction.contract_history import load_phf19_history

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.register import register_projection

    predecessor, head = phf19_history(tmp_path)
    document = yaml.safe_load(head.contract_path.read_bytes())
    document["version"] = predecessor.contract.version
    base = shipped_base_contract()
    contract = parse_domain_contract(document, source="fixture", base=base, predecessor=predecessor.contract)
    register = replace(head.register, describes=f"mm30:{contract.content_identity}")
    head.contract_path.write_text(yaml.safe_dump(document))
    head.register_path.write_text(json.dumps(register_projection(register)))

    with pytest.raises(ProfileError, match=r"mm30-phf19\.yaml: .*version"):
        load_phf19_history(head.contract_path, base=base)


def test_fixture_seeds_from_the_adopted_pair_after_the_source_advances(tmp_path):
    source_root = tmp_path / "source"
    genesis, head = phf19_history(source_root / "python/tools/reproduction")
    inventory = source_root / "contracts/source-ownership/INVENTORY.json"
    inventory.parent.mkdir(parents=True)
    rows = [
        {
            "contract_path": pair.contract_path.relative_to(source_root).as_posix(),
            "register_path": pair.register_path.relative_to(source_root).as_posix(),
        }
        for pair in (genesis, head)
    ]
    inventory.write_text(json.dumps({"lineages": {"mm30": {"revisions": rows}}}))

    (seed,) = phf19_history(tmp_path / "seeded", source_root=source_root, successors=0)
    assert seed.contract_path.read_bytes() == genesis.contract_path.read_bytes()
    assert seed.register_path.read_bytes() == genesis.register_path.read_bytes()
    assert seed.contract.content_identity == genesis.contract.content_identity
    assert seed.contract.content_identity != head.contract.content_identity
