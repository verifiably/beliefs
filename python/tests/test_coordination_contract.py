import copy

import pytest
from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract

from beliefs.contract.coordination import (
    CoordinationContract,
    load_coordination_contract,
)
from beliefs.errors import MalformedContract, SuccessionViolation


def successor(predecessor, **changes):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document.update(changes)
    document["version"] = predecessor.version + 1
    document["lineage"] = {"successor": predecessor.content_identity}
    return document


def test_v1_parses_to_the_exact_schema_projection():
    contract = coordination_contract()
    assert isinstance(contract, CoordinationContract)
    assert contract.namespace == "coordination"
    assert contract.schema_projection()["address_root"] == "project"
    assert tuple(contract.kinds) == tuple(sorted(COORDINATION_DOCUMENT["kinds"]))


@pytest.mark.parametrize(
    "field",
    ["contract", "version", "lineage", "address_root", "query_vocabulary", "kinds"],
)
def test_every_required_root_member_is_required(field):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    del document[field]
    with pytest.raises(MalformedContract):
        coordination_contract(document)


def test_kind_members_are_closed():
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    document["kinds"]["project"]["extra"] = True
    with pytest.raises(MalformedContract, match="exactly"):
        coordination_contract(document)


@pytest.mark.parametrize(
    "path",
    [
        ("kinds", "project", "fields"),
        ("kinds", "project", "query_versions"),
        ("query_vocabulary", "kinds"),
        ("query_vocabulary", "relations"),
    ],
)
def test_declared_sets_refuse_duplicates(path):
    document = copy.deepcopy(COORDINATION_DOCUMENT)
    value: object = document
    for part in path:
        assert isinstance(value, dict)
        value = value[part]
    assert isinstance(value, list)
    value.append(value[0])
    with pytest.raises(MalformedContract, match="duplicate"):
        coordination_contract(document)


def test_editorial_successor_preserves_schema_projection_and_moves_content_identity():
    genesis = coordination_contract()
    edited = successor(genesis, description="Reworded")
    current = coordination_contract(edited, genesis)
    assert current.content_identity != genesis.content_identity
    assert current.schema_projection() == genesis.schema_projection()


def test_a_successor_may_add_a_kind_and_query_vocabulary():
    genesis = coordination_contract()
    document = successor(genesis)
    document["kinds"]["publication"] = {
        "fields": ["name", "body", "author", "at"],
        "query_versions": [],
    }
    document["query_vocabulary"]["kinds"].append("future-world-kind")
    document["query_vocabulary"]["relations"].append("future-relation")
    current = coordination_contract(document, genesis)
    assert "publication" in current.kinds
    assert "future-world-kind" in current.query_kinds
    assert "future-relation" in current.query_relations


def test_yaml_duplicate_keys_refuse_at_load(tmp_path):
    path = tmp_path / "coordination.yaml"
    path.write_text("contract: coordination\ncontract: coordination\n", encoding="utf-8")
    with pytest.raises(MalformedContract, match="duplicate"):
        load_coordination_contract(path, predecessor=None)


@pytest.mark.parametrize(
    "change",
    [
        "address_root",
        "drop_kind",
        "change_fields",
        "drop_query_version",
        "drop_query_kind",
        "drop_query_relation",
    ],
)
def test_succession_refuses_every_redefinition(change):
    genesis = coordination_contract()
    document = successor(genesis)
    if change == "address_root":
        document["address_root"] = "question"
    elif change == "drop_kind":
        del document["kinds"]["note"]
    elif change == "change_fields":
        document["kinds"]["note"]["fields"].remove("about")
    elif change == "drop_query_version":
        document["kinds"]["project"]["query_versions"] = []
    elif change == "drop_query_kind":
        document["query_vocabulary"]["kinds"].pop()
    else:
        document["query_vocabulary"]["relations"].pop()
    with pytest.raises(SuccessionViolation):
        coordination_contract(document, genesis)
