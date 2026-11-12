"""Real resources; annotation examples prove grammar, never release membership."""

import json
from importlib import resources

import pytest
from conftest import REPO_ROOT

from beliefs.claim import Referent, build_claim
from beliefs.errors import ScienceError
from beliefs.identity import v1
from beliefs.profile import (
    compile_profile,
    shipped_assumptions_register,
    shipped_base,
    shipped_base_contract,
    shipped_domain_contract,
)
from beliefs.projection import claim_identity, project_claim
from beliefs.register import register_entry_keys, register_identity


def biology_profile():
    return compile_profile(
        shipped_base_contract(),
        [shipped_domain_contract("general"), shipped_domain_contract("biology")],
    )


def structural(profile, protein=False, **changes):
    values = {
        "operator": "biology/translated-from" if protein else "biology/transcribed-from",
        "roles": {
            "protein" if protein else "gene": Referent(
                "biology/protein" if protein else "biology/ensembl-gene",
                "ensembl:ENSP00000310372.6" if protein else "ensembl:ENSG00000119403",
            ),
            "transcript": Referent("biology/transcript", "ensembl:ENST00000312189.10"),
        },
        "qualifiers": {},
        "form": "polar",
        "polarity": None,
        "layer": "structural",
    }
    values.update(changes)
    return build_claim(profile, **values)


def test_biology_is_explicit_and_has_exact_canonical_coverage():
    contract = shipped_domain_contract("biology")
    register = shipped_assumptions_register("biology")
    assert contract.version == 1 and contract.predecessor is None
    assert register.previous is None
    assert register.describes == f"biology:{contract.content_identity}"
    assert set(register.entries) == register_entry_keys(contract)
    assert len(register.entries) == 12
    assert all(e.status == "provisional" for e in register.entries.values())
    assert set(contract.sorts) == {"gene", "ensembl-gene", "transcript", "protein", "molecular-aspect"}
    assert set(contract.templates) == {"transcribed-from", "translated-from"}
    assert set(contract.instantiations) == {"transcript-gene", "protein-transcript"}
    assert set(contract.bridges) == {"regulates"}
    assert not contract.estimands
    assert not shipped_base().activated_contracts
    with pytest.raises(ScienceError):
        compile_profile(shipped_base_contract(), [contract])
    profile = biology_profile()
    assert profile.admits_measurement("biology/gene", "general/relative-abundance")
    assert not profile.admits_measurement("biology/protein", "general/relative-abundance")
    assert not profile.admits_measurement("biology/ensembl-gene", "general/relative-abundance")
    for name in ("DOMAIN.yaml", "REGISTER.json"):
        assert (REPO_ROOT / "domains/biology" / name).read_bytes() == resources.files("beliefs").joinpath(
            f"domains/biology/{name}"
        ).read_bytes()
    vector = json.loads((REPO_ROOT / "fixtures/biology-claim-identity-v2.json").read_text())
    assert contract.content_identity == vector["biology_content_identity"]
    assert profile.compiled_identity == vector["profile_compiled_identity"]
    assert register_identity(register) == vector["register_identity"]


def test_structural_claims_and_regulates_have_the_declared_edges():
    profile = biology_profile()
    assert structural(profile).operator == "biology/transcribed-from"
    assert structural(profile, protein=True).operator == "biology/translated-from"
    assert profile.templates["biology/transcribed-from"].edge is None
    assert profile.templates["biology/translated-from"].edge is None
    claim = build_claim(
        profile,
        operator="biology/regulates",
        roles={"intervention": Referent("biology/gene", "hgnc:24566"), "response": Referent("biology/gene", "hgnc:5")},
        qualifiers={},
        form="polar",
        polarity="positive",
        layer="causal",
    )
    assert claim.layer == "causal"
    assert profile.templates["general/changes-under-intervention"].edge == ("intervention", "response")
    with pytest.raises(ScienceError):
        structural(
            profile,
            roles={
                "gene": Referent("biology/protein", "ensembl:ENSP00000310372.6"),
                "transcript": Referent("biology/transcript", "ensembl:ENST00000312189.10"),
            },
        )


@pytest.mark.parametrize(
    "term",
    [
        "PHF19",
        "ENST00000312189.10",
        "ensembl:ENST00000312189",
        "ensembl:ENST00000312189.0",
        "ensembl:ENST00000312189.x",
        "ensembl:ENSMUST000001.1",
        "ensembl:ENSG00000119403",
    ],
)
def test_transcript_identifier_refusals(term):
    with pytest.raises(ScienceError):
        structural(
            biology_profile(),
            roles={
                "gene": Referent("biology/ensembl-gene", "ensembl:ENSG00000119403"),
                "transcript": Referent("biology/transcript", term),
            },
        )


@pytest.mark.parametrize(
    "term",
    ["PHF19", "ensembl:ENSP00000310372", "ensembl:ENSP00000310372.0", "ensembl:ENSG00000119403", "uniprot:Q5T6S3"],
)
def test_protein_identifier_refusals(term):
    with pytest.raises(ScienceError):
        structural(
            biology_profile(),
            protein=True,
            roles={
                "protein": Referent("biology/protein", term),
                "transcript": Referent("biology/transcript", "ensembl:ENST00000312189.10"),
            },
        )


def test_python_reproduces_frozen_claim_vectors():
    profile = biology_profile()
    fixture = json.loads((REPO_ROOT / "fixtures/biology-claim-identity-v2.json").read_text())
    for row in fixture["vector"]:
        values = row["claim"]
        claim = build_claim(profile, **{**values, "roles": {k: Referent(**v) for k, v in values["roles"].items()}})
        assert project_claim(claim) == row["projection"]
        assert v1.encode(project_claim(claim)).decode() == row["canonical_bytes"]
        assert claim_identity(claim) == row["digest"]
