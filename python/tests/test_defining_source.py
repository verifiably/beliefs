"""Shared source grammar and local succession; admission is a separate boundary."""

import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from beliefs import errors
from beliefs.contract.domain import parse_domain_contract
from beliefs.profile import compile_profile
from beliefs.register import register_entry_keys

ROOT = Path(__file__).resolve().parents[2]
VECTOR = json.loads((ROOT / "fixtures/defining-source.json").read_text())
CASES = {c["name"]: c for c in VECTOR["cases"]}


def parse(case, base):
    prior = parse(CASES[case["previous"]], base) if case["previous"] else None
    return parse_domain_contract(case["document"], source=case["name"], base=base, predecessor=prior)


@pytest.mark.parametrize("case", VECTOR["cases"], ids=lambda c: c["name"])
def test_source_vector(case, base_contract):
    if case["outcome"] == "refuse":
        with pytest.raises(getattr(errors, case["error"])) as caught:
            parse(case, base_contract)
        assert case["diagnostic"] in str(caught.value)
    else:
        contract = parse(case, base_contract)
        assert contract.content_identity == case["content_identity"]
        expected = case["document"].get("defining_source")
        assert (contract.defining_source.id if contract.defining_source else None) == (
            expected["id"] if expected else None
        )


def test_source_is_immutable_and_outside_projections(base_contract):
    absent, present = (parse(CASES[n], base_contract) for n in ("absent", "urn"))
    assert absent.content_identity != present.content_identity
    assert absent.claim_vocabulary() == present.claim_vocabulary()
    assert register_entry_keys(absent) == register_entry_keys(present)
    assert (
        compile_profile(base_contract, [absent]).compiled_identity
        == compile_profile(base_contract, [present]).compiled_identity
    )
    assert present.defining_source is not None
    with pytest.raises(FrozenInstanceError):
        present.defining_source.id = "urn:changed:id"  # pyright: ignore[reportAttributeAccessIssue]
    other = copy.deepcopy(CASES["urn"]["document"])
    other["contract"] = "other-source-test"
    duplicate = parse_domain_contract(other, source="other", base=base_contract, predecessor=None)
    compile_profile(base_contract, [present, duplicate])


def test_unchanged_production_profiles(base_contract):
    parsed = {}
    for row in sorted(
        VECTOR["production"],
        key=lambda r: r["contract_identity"] != "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f",
    ):
        doc = yaml.safe_load((ROOT / row["contract_path"]).read_text())
        prior = parsed.get(row["namespace"])
        c = parse_domain_contract(doc, source=row["contract_path"], base=base_contract, predecessor=prior)
        assert c.content_identity == row["contract_identity"]
        parsed[c.namespace] = c
    for names, identity in VECTOR["profiles"].items():
        assert compile_profile(base_contract, [parsed[n] for n in names.split("+")]).compiled_identity == identity
