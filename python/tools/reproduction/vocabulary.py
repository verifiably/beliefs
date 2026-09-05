"""Task 3: the domain contract, the compiled profile, the namespaced plan, the snapshot.

The reproduction's vocabulary is `mm30-reproduction.yaml` (from the typing
exercise's unsorted plan). The modal-sorted plan is exposed too, for one pure
measurement at step 2: what `build_claim` says when the target's kind pair
meets a sort discipline that excludes it.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from beliefs.consulted import CorpusPins
from beliefs.contract import load_base_contract
from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.profile import ProfileSpec, compile_profile
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths

DOCUMENT = Path(__file__).with_name("mm30-reproduction.yaml")
MODAL_SORTED = paths.REPO / "python" / "tools" / "vocabularies" / "mm30-modal-sorted.yaml"
BASE = paths.REPO / "contracts" / "science" / "CONTRACT.yaml"


@cache
def _document(path: Path = DOCUMENT) -> dict:
    return yaml.safe_load(path.read_text())


@cache
def base():
    return load_base_contract(BASE)


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    return parse_domain_contract(_document(path)["contract"], source=f"{path}: contract", base=base(), predecessor=None)


@cache
def profile(path: Path = DOCUMENT) -> ProfileSpec:
    return compile_profile(base(), [contract(path)])


def plan(path: Path = DOCUMENT) -> dict:
    """The typing tool's resolution, repeated exactly: local names are
    namespaced once, here, through the contract's own `term`."""
    raw = _document(path)["plan"]
    domain = contract(path)
    return {
        "operators": {k: domain.term(v) for k, v in (raw.get("operators") or {}).items()},
        "sorts": {k: domain.term(v) for k, v in (raw.get("sorts") or {}).items()},
        "layers": dict(raw.get("layers") or {}),
        "polarities": dict(raw.get("polarities") or {}),
    }


def pins() -> CorpusPins:
    return CorpusPins(
        science_contract=f"science:{base().content_identity}",
        domains={contract().namespace: f"{contract().namespace}:{contract().content_identity}"},
    )


def snapshot() -> ResolutionSnapshot:
    """Nothing readable: every binding is `not-consulted`. No membership is
    asserted for any term, in any namespace (question 1: unmeasured)."""
    return build_snapshot()
