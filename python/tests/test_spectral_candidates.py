"""Unshipped spectral definitions: source, additive history and claim parity."""

import json
from pathlib import Path

import pytest
from candidate_contracts import (
    GENERAL_SOURCE_ID,
    candidate_history,
    fragment,
    general_successor_history,
    oracle,
    spectral_profile,
)

from beliefs import errors
from beliefs.claim import Member, Qualifier, Referent, build_claim
from beliefs.identity import v1
from beliefs.projection import claim_identity, project_claim
from beliefs.register import register_entry_keys, register_identity

ROOT = Path(__file__).resolve().parents[2]
SPECTRAL_KEYS = {
    "sort:general/series-view",
    "functional:general/peak-power-fraction",
    "functional:general/signed-aperiodic-exponent",
    "design:general/single-record-summary",
    "selection-mechanism:general/explicit-series-view",
}
EXAMPLE_KEYS = {
    "template:spectral-example/has-spectral-summary",
    "quantity-kind:spectral-example/synthetic-amplitude",
    "measurement:general/series-view",
    "instantiation:spectral-example/selected-series-summary",
    "estimand:instantiation:spectral-example/selected-series-summary",
}


def spectral_oracle():
    return json.loads((ROOT / "fixtures/spectral-candidates.json").read_text())


def components(row):
    c = row["components"]
    return {
        **c,
        "roles": {
            k: tuple(Member(Referent(v["sort"], v["term"]), v["coefficient"]) for v in r)
            if isinstance(r, list)
            else Referent(r["sort"], r["term"])
            for k, r in c["roles"].items()
        },
        "qualifiers": {k: Qualifier(v["quantifier"], Referent(**v["restriction"])) for k, v in c["qualifiers"].items()},
    }


def summary(profile, term="dataset:sha256:" + "a" * 64):
    return build_claim(
        profile,
        operator="spectral-example/has-spectral-summary",
        roles={"series": Referent("general/series-view", term)},
        form="polar",
        layer="statistical",
    )


def test_spectral_inventory_and_register(base_contract):
    data = spectral_oracle()
    *_, previous, current = general_successor_history(base_contract, fragments=("general-spectral",))
    assert register_entry_keys(current.contract) - register_entry_keys(previous.contract) == SPECTRAL_KEYS
    assert set(current.register.entries) == set(previous.register.entries) | SPECTRAL_KEYS
    assert current.register.previous == register_identity(previous.register)
    assert all(current.register.entries[k] == v for k, v in previous.register.entries.items())
    assert all(current.register.entries[k].status == "provisional" for k in SPECTRAL_KEYS)
    assert current.contract.defining_source is not None
    assert current.contract.defining_source.id == GENERAL_SOURCE_ID
    pair = candidate_history("spectral-example", base_contract)
    assert register_entry_keys(pair.contract) == set(pair.register.entries) == EXAMPLE_KEYS
    assert {e.status for e in pair.register.entries.values()} == {"provisional"}
    assert pair.contract.defining_source is not None
    assert pair.contract.defining_source.id == "urn:beliefs:definitions:synthetic-spectral-example"
    assert pair.contract.content_identity == data["synthetic_pair"]["contract_identity"]
    assert register_identity(pair.register) == data["synthetic_pair"]["register_identity"]
    assert base_contract.content_identity == data["base_identity"]
    for name in ("spectral", "joint"):
        joint = name == "joint"
        profile = spectral_profile(base_contract, joint=joint)
        fragments = ("general-event-locked", "general-spectral") if joint else ("general-spectral",)
        current = general_successor_history(base_contract, fragments=fragments)[-1]
        assert current.contract.content_identity == data["profiles"][name]["general_contract_identity"]
        assert register_identity(current.register) == data["profiles"][name]["general_register_identity"]
        assert profile.compiled_identity == data["profiles"][name]["compiled_identity_python"]


def test_joint_successor_preserves_both_fragments(base_contract):
    *_, previous, current = general_successor_history(
        base_contract, fragments=("general-event-locked", "general-spectral")
    )
    assert register_entry_keys(current.contract) == register_entry_keys(previous.contract) | SPECTRAL_KEYS | set(
        fragment("general-event-locked")["register_entries"]
    )
    assert current.register.previous == register_identity(previous.register)
    profile = spectral_profile(base_contract, joint=True)
    assert set(profile.activated_contracts) == {
        "general",
        "si-brochure",
        "spectral-example",
        "plasma-populations",
        "catalogue-anchors",
    }


def test_existing_event_oracle_unchanged(base_contract):
    assert (
        general_successor_history(base_contract)[-1].contract.content_identity
        == oracle()["general_successor"]["contract_identity"]
        == "cb56b47ba248ae64ac66d727d7f97090da1d5c4aedf52652606e9c437e539ed2"
    )


@pytest.mark.parametrize(
    "joint,omitted",
    [(j, o) for j in (False, True) for o in ("general-spectral", "spectral-example")]
    + [(True, o) for o in ("general-event-locked", "speed", "plasma-populations", "catalogue-anchors", "si-brochure")],
)
def test_declaration_omissions_refuse_at_their_boundary(base_contract, joint, omitted):
    if omitted in ("spectral-example", "catalogue-anchors"):
        profile = spectral_profile(base_contract, joint=joint, omit=(omitted,))
        with pytest.raises(errors.ClaimError if omitted == "catalogue-anchors" else errors.ProfileError):
            if omitted == "spectral-example":
                summary(profile)
            else:
                build_claim(
                    profile,
                    operator="general/event-locked-change",
                    roles={
                        "anchor": Referent("catalogue-anchors/cdaw-halo-cme", "catalogue-class:cdaw-halo-cme"),
                        "response": Referent(
                            "plasma-populations/near-earth-solar-wind", "plasma-population:near-earth-solar-wind"
                        ),
                    },
                    form="polar",
                    polarity="positive",
                    layer="statistical",
                )
    else:
        with pytest.raises((errors.ProfileError, errors.MalformedContract)):
            spectral_profile(base_contract, joint=joint, omit=(omitted,))


def test_standalone_time_omission_compiles_and_types(base_contract):
    profile = spectral_profile(base_contract, omit=("si-brochure",))
    assert "si-brochure" not in profile.activated_contracts
    assert summary(profile).operator == "spectral-example/has-spectral-summary"


def test_collision_refuses(base_contract):
    with pytest.raises(ValueError, match="already declares"):
        general_successor_history(base_contract, fragments=("general-spectral", "general-spectral"))


def test_claim_vectors_rebuild(base_contract):
    data = spectral_oracle()
    assert len({c["components"]["roles"]["series"]["term"] for c in data["claims"]}) == 2
    for row in data["claims"]:
        claim = build_claim(spectral_profile(base_contract, joint=row["profile"] == "joint"), **components(row))
        assert project_claim(claim) == row["projection"]
        assert v1.encode(project_claim(claim)).decode() == row["canonical_bytes"]
        assert claim_identity(claim) == row["digest"]
