"""A shipped history is checked in full before either current resource is returned."""

import json

import pytest
import yaml
from shipped_domain_fixtures import history_resources, read_resource

import beliefs.profile as profile_module
from beliefs.contract.shipped import load_domain_history
from beliefs.errors import ProfileError
from beliefs.profile import shipped_base_contract
from beliefs.register import register_identity


def load(resources, namespace="general"):
    return load_domain_history(namespace, base=shipped_base_contract(), read_text=lambda p: read_resource(resources, p))


@pytest.mark.parametrize("count", [1, 2, 3])
def test_one_and_two_successors_load_with_exact_register_links(count):
    resources, contracts, registers = history_resources(count)
    loaded = load(resources)
    assert [r.contract.content_identity for r in loaded] == [c.content_identity for c in contracts]
    assert [register_identity(r.register) for r in loaded] == [register_identity(r) for r in registers]
    assert loaded[-1].directory == ""
    assert [r.directory for r in loaded[:-1]] == [f"history/{c.content_identity}" for c in contracts[:-1]]


@pytest.mark.parametrize(
    "defect",
    [
        "missing-domain",
        "missing-register",
        "wrong-identity",
        "namespace",
        "invalid-ancestor",
        "duplicate-key",
        "describes",
        "missing-entry",
        "extra-entry",
        "missing-previous",
        "wrong-previous",
        "genesis-previous",
        "register-only",
    ],
)
def test_broken_history_refuses_with_the_offending_resource(defect):
    resources, contracts, registers = history_resources()
    ancestor = f"history/{contracts[0].content_identity}/DOMAIN.yaml"
    regpath = "REGISTER.json"
    domain = yaml.safe_load(resources[ancestor])
    register = json.loads(resources[regpath])
    if defect == "missing-domain":
        del resources[ancestor]
    elif defect == "missing-register":
        regpath = f"history/{contracts[0].content_identity}/REGISTER.json"
        del resources[regpath]
    elif defect == "wrong-identity":
        domain["version"] += 1
    elif defect == "namespace":
        domain["contract"] = "other"
    elif defect == "invalid-ancestor":
        domain["sorts"] = []
    elif defect == "duplicate-key":
        resources[regpath] = '{"describes":"duplicate",' + resources[regpath][1:]
    elif defect == "describes":
        register["describes"] = "general:" + "0" * 64
    elif defect == "missing-entry":
        register["entries"].pop(next(iter(register["entries"])))
    elif defect == "extra-entry":
        register["entries"]["design:general/extra"] = next(iter(register["entries"].values()))
    elif defect == "missing-previous":
        del register["previous"]
    elif defect == "wrong-previous":
        register["previous"] = "assumptions-register:" + "0" * 64
    elif defect == "register-only":
        register["previous"] = register_identity(registers[-1])
    elif defect == "genesis-previous":
        regpath = f"history/{contracts[0].content_identity}/REGISTER.json"
        register = json.loads(resources[regpath])
        register["previous"] = register_identity(registers[0])
    if defect in {"wrong-identity", "namespace", "invalid-ancestor"}:
        resources[ancestor] = yaml.safe_dump(domain)
    if defect not in {
        "missing-domain",
        "missing-register",
        "wrong-identity",
        "namespace",
        "invalid-ancestor",
        "duplicate-key",
    }:
        resources[regpath] = json.dumps(register)
    with pytest.raises(
        ProfileError,
        match="DOMAIN.yaml"
        if defect in {"missing-domain", "wrong-identity", "namespace", "invalid-ancestor"}
        else "REGISTER.json",
    ):
        load(resources)


@pytest.mark.parametrize("identity", ["../outside", "a/b", "A" * 64, "abc", "", None])
def test_malformed_lineage_never_becomes_a_resource_path(identity):
    resources, _, _ = history_resources()
    document = yaml.safe_load(resources["DOMAIN.yaml"])
    document["lineage"] = {"successor": identity}
    resources["DOMAIN.yaml"] = yaml.safe_dump(document)
    reads = []

    def reader(path):
        reads.append(path)
        return read_resource(resources, path)

    with pytest.raises(ProfileError, match="DOMAIN.yaml"):
        load_domain_history("general", base=shipped_base_contract(), read_text=reader)
    assert reads == ["DOMAIN.yaml"]


@pytest.mark.parametrize("length", [1, 1100])
def test_cycles_are_diagnosed_without_recursion_exhaustion(length):
    identities = [f"{n:064x}" for n in range(length)]
    resources = {"DOMAIN.yaml": json.dumps({"lineage": {"successor": identities[0]}})}
    for index, identity in enumerate(identities):
        resources[f"history/{identity}/DOMAIN.yaml"] = json.dumps(
            {"lineage": {"successor": identities[(index + 1) % length]}}
        )
    with pytest.raises(ProfileError, match="cycle"):
        load(resources)


def test_package_apis_return_checked_current_pair_without_activating_it(tmp_path, monkeypatch):
    resources, contracts, registers = history_resources(namespace="sample")
    for relative, text in resources.items():
        path = tmp_path / "domains/sample" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    # Resolve the existing shipped base before replacing only the domain resource seam.
    shipped_base_contract()
    monkeypatch.setattr(profile_module.resources, "files", lambda _: tmp_path)
    profile_module._shipped_domain_history.cache_clear()
    profile_module.shipped_domain_contract.cache_clear()
    profile_module.shipped_assumptions_register.cache_clear()
    try:
        assert profile_module.shipped_domain_contract("sample").content_identity == contracts[-1].content_identity
        assert register_identity(profile_module.shipped_assumptions_register("sample")) == register_identity(
            registers[-1]
        )
        assert profile_module.shipped_domain_contract("sample") is profile_module.shipped_domain_contract("sample")
        assert not profile_module.shipped_base().activated_contracts
    finally:
        profile_module._shipped_domain_history.cache_clear()
        profile_module.shipped_domain_contract.cache_clear()
        profile_module.shipped_assumptions_register.cache_clear()
