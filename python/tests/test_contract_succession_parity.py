"""Shared normative documents and succession outcomes, independent of TypeScript."""

import copy
import json
from pathlib import Path

import pytest

from beliefs import errors
from beliefs.contract.domain import DECLARATION_FAMILIES, parse_domain_contract
from beliefs.identity import v1

VECTOR = json.loads((Path(__file__).resolve().parents[2] / "fixtures/contract-succession.json").read_text())


def test_the_shared_vector_covers_every_family(base_contract):
    assert VECTOR["families"] == [name for name, _ in DECLARATION_FAMILIES]
    assert {c["name"][5:] for c in VECTOR["cases"] if c["name"].startswith("drop-")} == set(VECTOR["families"])
    genesis = parse_domain_contract(VECTOR["genesis"], source="genesis", base=base_contract, predecessor=None)
    assert genesis.content_identity == VECTOR["genesis_identity"]
    assert genesis.claim_vocabulary() == VECTOR["genesis_schema"]


@pytest.mark.parametrize("case", VECTOR["cases"], ids=lambda c: c["name"])
def test_shared_succession_outcome(base_contract, case):
    genesis = parse_domain_contract(VECTOR["genesis"], source="genesis", base=base_contract, predecessor=None)
    added = parse_domain_contract(VECTOR["added"], source="added", base=base_contract, predecessor=genesis)
    assert added.content_identity == VECTOR["added_identity"]
    document = copy.deepcopy(VECTOR[case["previous"] or "genesis"])
    document["version"] += 1
    document["lineage"] = case["lineage"]
    for change in case["changes"]:
        target = document
        for key in change["path"][:-1]:
            target = target[key]
        if change.get("delete"):
            del target[change["path"][-1]]
        else:
            target[change["path"][-1]] = change["value"]
    assert v1.digest("science.contract.v1", document) == case["identity"]
    predecessor = {"genesis": genesis, "added": added, None: None}[case["previous"]]
    if case["outcome"] == "accept":
        assert (
            parse_domain_contract(
                document, source=case["name"], base=base_contract, predecessor=predecessor
            ).content_identity
            == case["identity"]
        )
    else:
        with pytest.raises(getattr(errors, case["outcome"])):
            parse_domain_contract(document, source=case["name"], base=base_contract, predecessor=predecessor)
