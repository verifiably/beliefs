"""Explicit base/general/biology/mm30 PHF19 profile and held-list resolution."""

from __future__ import annotations

import re
from functools import cache
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.contract.base import BaseContract
from beliefs.contract.domain import DatasetBinding, DomainContract
from beliefs.contract.shipped import ShippedDomainRevision
from beliefs.dataset import DatasetDeclaration, dataset_address
from beliefs.errors import ProfileError
from beliefs.profile import CompiledSort, ProfileSpec, compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths, state
from reproduction.contract_history import load_phf19_history

__all__ = [
    "DOCUMENT",
    "HELD_SORTS",
    "base",
    "binding_for",
    "biology",
    "check_members",
    "checked_lines",
    "contract",
    "pins",
    "profile",
    "revision",
    "snapshot",
    "snapshot_over",
]

DOCUMENT = Path(__file__).with_name("mm30-phf19.yaml")
HELD_SORTS = {"clinical-factors": "clinical-factor", "stage-levels": "stage-level", "cohorts": "cohort"}


@cache
def base():
    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    return shipped_domain_contract("biology")


@cache
def _default_history() -> tuple[ShippedDomainRevision, ...]:
    return load_phf19_history(DOCUMENT, base=base())


def revision(
    path: Path = DOCUMENT, *, content_identity: str | None = None, base: BaseContract | None = None
) -> ShippedDomainRevision:
    """Select the head or an exact pair from a fully checked PHF19 history."""
    if content_identity is not None and (
        not isinstance(content_identity, str) or re.fullmatch(r"[0-9a-f]{64}", content_identity) is None
    ):
        raise ProfileError(f"{path}: content identity must be 64 lowercase hexadecimal characters")
    history = (
        _default_history()
        if path == DOCUMENT and base is None
        else load_phf19_history(path, base=shipped_base_contract() if base is None else base)
    )
    if content_identity is None:
        return history[-1]
    for selected in history:
        if selected.contract.content_identity == content_identity:
            return selected
    raise ProfileError(f"{path}: no PHF19 revision with content identity {content_identity!r}")


def contract(path: Path = DOCUMENT) -> DomainContract:
    return revision(path).contract


def _compile(contract: DomainContract) -> ProfileSpec:
    return compile_profile(base(), [shipped_domain_contract("general"), biology(), contract])


@cache
def _default_profile() -> ProfileSpec:
    return _compile(contract())


def profile(path: Path = DOCUMENT) -> ProfileSpec:
    return _default_profile() if path == DOCUMENT else _compile(contract(path))


def pins(path: Path = DOCUMENT) -> CorpusPins:
    p = profile(path)
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
