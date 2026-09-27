"""Compile a mounted corpus's profile from its manifest's pins."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from beliefs.contract.coordination import CoordinationContract
from beliefs.contract.domain import DomainContract
from beliefs.errors import MountPinUnresolved, ProfileError, UnparsedContract
from beliefs.profile import (
    ProfileSpec,
    compile_profile,
    shipped_base_contract,
    shipped_coordination,
    shipped_domain_contract,
)
from beliefs.world import load_manifest

__all__ = ["compile_mount_profile"]


def compile_mount_profile(root: Path, *, available: Iterable[DomainContract] = ()) -> ProfileSpec:
    """Compile exactly the contracts pinned by ``root``'s manifest."""
    if not isinstance(root, Path):
        raise TypeError("compile_mount_profile takes the corpus root as a Path")
    documents = tuple(available)
    for document in documents:
        if not isinstance(document, DomainContract):
            raise UnparsedContract(f"an available contract is a {type(document).__name__}, not a parsed DomainContract")
    pins = load_manifest(root).profile
    base = shipped_base_contract()
    if pins.science_contract != f"science:{base.content_identity}":
        raise MountPinUnresolved(root, "science", pins.science_contract)
    domains: list[DomainContract] = []
    coordination: CoordinationContract | None = None
    for namespace, pin in sorted(pins.domains.items()):
        prefix = f"{namespace}:"
        identity = pin[len(prefix):] if pin.startswith(prefix) else None
        if namespace == "coordination":
            coordination = next((c for c in (shipped_coordination(1), shipped_coordination(2)) if c.content_identity == identity), None)
            if coordination is None:
                raise MountPinUnresolved(root, namespace, pin)
            continue
        candidates = (*_shipped(namespace), *(d for d in documents if d.namespace == namespace))
        match = next((c for c in candidates if c.content_identity == identity), None)
        if match is None:
            raise MountPinUnresolved(root, namespace, pin)
        domains.append(match)
    return compile_profile(base, domains, coordination=coordination)


def _shipped(namespace: str) -> tuple[DomainContract, ...]:
    try:
        return (shipped_domain_contract(namespace),)
    except ProfileError:
        return ()
