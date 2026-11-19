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
