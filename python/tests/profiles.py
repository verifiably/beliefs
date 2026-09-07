# python/tests/profiles.py
"""Compiled profiles the tests write under, from real contracts (facet-contracts §5.1).

Every manifest pins the shipped base; a writer refuses a profile whose base
identity is not the shipped one. The `biology` fixture exists twice so the
relocation tests can pin two disagreeing identities for one namespace.
"""

from __future__ import annotations

from pathlib import Path

from beliefs.consulted import CorpusPins
from beliefs.contract import parse_domain_contract
from beliefs.contract.document import load_document
from beliefs.profile import ProfileSpec, compile_profile, shipped_base, shipped_base_contract

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "biology-fixture.yaml"


def biology(description: str):
    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    document["description"] = description
    return parse_domain_contract(document, source=f"{FIXTURE}#{description}", base=shipped_base_contract(), predecessor=None)


BASE: ProfileSpec = shipped_base()
WITH_BIOLOGY: ProfileSpec = compile_profile(shipped_base_contract(), [biology("fixture")])
WITH_BIOLOGY_OTHER: ProfileSpec = compile_profile(shipped_base_contract(), [biology("fixture, second variant")])


def pins_for(profile: ProfileSpec) -> CorpusPins:
    return CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
