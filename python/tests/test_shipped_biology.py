"""B6 (biology pack design §3.2, §6.1): the first packaged domain contract."""

from importlib import resources

import pytest

from beliefs.errors import ProfileError
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract


def test_the_packaged_copy_is_byte_identical_to_the_normative_file(fixtures_dir):
    normative = fixtures_dir.parent / "domains" / "biology" / "DOMAIN.yaml"
    packaged = resources.files("beliefs").joinpath("domains/biology/DOMAIN.yaml").read_bytes()
    assert packaged == normative.read_bytes()


def test_the_shipped_pack_declares_the_floor():
    pack = shipped_domain_contract("biology")
    assert pack.namespace == "biology"
    assert set(pack.sorts) == {"molecular-entity"}
    binding = pack.sorts["molecular-entity"].vocabulary
    assert (binding.namespace, binding.release) == ("HGNC", "2026-07-01")
    assert set(pack.operators) == {
        "affects-molecular-entity-molecular-entity",
        "associates-with-molecular-entity-molecular-entity",
        "regulates-molecular-entity-molecular-entity",
    }
    assert set(pack.facets) == {"biology/gene-axis"}
    assert set(pack.facets["biology/gene-axis"].fields) == {"axis", "namespace"}


def test_the_shipped_pack_compiles_with_the_shipped_base():
    profile = compile_profile(shipped_base_contract(), [shipped_domain_contract("biology")])
    operator = profile.operator("biology/affects-molecular-entity-molecular-entity")
    assert operator.arg_sorts == ("biology/molecular-entity", "biology/molecular-entity")
    assert "dataset" in profile.facets["biology/gene-axis"].attaches_to


def test_the_pack_is_parsed_once():
    assert shipped_domain_contract("biology") is shipped_domain_contract("biology")


def test_an_unshipped_namespace_is_refused():
    with pytest.raises(ProfileError, match="ships no domain contract"):
        shipped_domain_contract("chemistry")


@pytest.mark.parametrize("namespace", ["biology/../biology", "biology.bad"])
def test_an_invalid_namespace_is_refused(namespace):
    with pytest.raises(ProfileError, match="ships no domain contract"):
        shipped_domain_contract(namespace)
