"""Explicit base/general/biology/mm30 PHF19 profile and held-list resolution."""

from __future__ import annotations

from functools import cache
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.contract import load_domain_contract
from beliefs.contract.domain import DatasetBinding, DomainContract
from beliefs.dataset import DatasetDeclaration, dataset_address
from beliefs.errors import ProfileError
from beliefs.profile import CompiledSort, ProfileSpec, compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths, state

DOCUMENT = Path(__file__).with_name("mm30-phf19.yaml")
HELD_SORTS = {"clinical-factors": "clinical-factor", "stage-levels": "stage-level", "cohorts": "cohort"}


@cache
def base():
    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    return shipped_domain_contract("biology")


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    if path.name != DOCUMENT.name:
        raise ProfileError("legacy reproduction contracts are unsupported; beliefs-6f039b owns restoration")
    return load_domain_contract(path, base=base(), predecessor=None)


@cache
def profile(path: Path = DOCUMENT) -> ProfileSpec:
    return compile_profile(base(), [shipped_domain_contract("general"), biology(), contract(path)])


def pins() -> CorpusPins:
    p = profile()
    return CorpusPins(
        science_contract=f"science:{p.base_contract_identity}",
        domains={ns: f"{ns}:{identity}" for ns, identity in p.activated_contracts.items()},
    )


def binding_for(sort: str) -> CompiledSort:
    return profile().sorts[sort if "/" in sort else "mm30/" + sort]


def checked_lines(declared: DatasetDeclaration, content: bytes, sort: CompiledSort) -> list[str]:
    binding = sort.binding
    if not isinstance(binding, DatasetBinding) or dataset_address(declared) != binding.dataset:
        raise RuntimeError("fetched vocabulary dataset differs from the dataset the sort binds")
    (resource,) = declared.resources
    if resource.digest != "sha256:" + sha256(content).hexdigest():
        raise RuntimeError("held vocabulary copy digest differs from its declared digest")
    return content.decode("utf-8").splitlines()


def snapshot_over(declared: DatasetDeclaration, content: bytes, sort: CompiledSort) -> ResolutionSnapshot:
    return build_snapshot(readable={sort.binding: checked_lines(declared, content, sort)})


def snapshot() -> ResolutionSnapshot:
    from reproduction import hold

    st = state.load()
    from beliefs.corpus import ReadView

    view = ReadView.opened_at(paths.CORPUS_ROOT)
    readable = {}
    for name, sort in HELD_SORTS.items():
        compiled = binding_for(sort)
        content = hold.restore(st["sources"][name], view)
        readable[compiled.binding] = checked_lines(
            stored.dataset_declaration(view.get(st["sources"][name]["dataset"])), content, compiled
        )
    original = hold.restore(st["sources"]["hgnc"], view)
    members = hold.restore(st["sources"]["hgnc-members"], view)
    manifest = hold.restore(st["sources"]["hgnc-derivation"], view)
    check_members(original, members, manifest)
    readable[profile().sorts["biology/gene"].binding] = members.decode().splitlines()
    # Ensembl is mapping evidence, not a complete consulted vocabulary.
    return build_snapshot(readable=readable)


def check_members(original: bytes, members: bytes, manifest: bytes) -> None:
    import json

    from reproduction import analysis_inputs
    from reproduction.analysis_inputs import hgnc_members

    expected = {
        "release": "2025-09-05",
        "source_sha256": sha256(original).hexdigest(),
        "parser_sha256": sha256(Path(analysis_inputs.__file__).read_bytes()).hexdigest(),
        "output_sha256": sha256(members).hexdigest(),
        "member_count": len(members.splitlines()),
    }
    if hgnc_members(original) != members or json.loads(manifest) != expected:
        raise RuntimeError("HGNC membership derivation is incomplete or inconsistent")
