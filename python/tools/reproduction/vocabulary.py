"""The base, biology, and mm30 contracts used by the reproduction."""

from __future__ import annotations

from functools import cache
from hashlib import sha256
from pathlib import Path

import yaml

from beliefs.consulted import CorpusPins
from beliefs.contract.domain import DomainContract, VocabularyBinding, parse_domain_contract
from beliefs.dataset import DatasetDeclaration, dataset_address
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths, state

DOCUMENT = Path(__file__).with_name("mm30.yaml")
MODAL_SORTED = paths.REPO / "python" / "tools" / "vocabularies" / "mm30-modal-sorted.yaml"
CONCEPTS_TOKEN = "{{CONCEPTS}}"


@cache
def _document(path: Path = DOCUMENT) -> dict:
    text = path.read_text()
    if CONCEPTS_TOKEN in text:
        st = state.load()
        if "concepts_address" not in st:
            raise RuntimeError("mm30.yaml binds `concept` to the held concept list; run concepts.py (step 1b) first")
        text = text.replace(CONCEPTS_TOKEN, st["concepts_address"].removeprefix("dataset:"))
    return yaml.safe_load(text)


@cache
def base():
    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    return shipped_domain_contract("biology")


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    return parse_domain_contract(_document(path)["contract"], source=f"{path}: contract", base=base(), predecessor=None)


@cache
def profile(path: Path = DOCUMENT) -> ProfileSpec:
    if path == DOCUMENT:
        return compile_profile(base(), [biology(), contract(path)])
    return compile_profile(base(), [contract(path)])


def _term(domain: DomainContract, name: str) -> str:
    return name if "/" in name else domain.term(name)


def plan(path: Path = DOCUMENT) -> dict:
    raw = _document(path)["plan"]
    domain = contract(path)
    operators = raw.get("operators") or {}
    if isinstance(operators, dict):
        rows = {(predicate, None, None): _term(domain, name) for predicate, name in operators.items()}
    else:
        rows = {(row["predicate"], row["subject"], row["object"]): _term(domain, row["operator"]) for row in operators}
    return {
        "operators": rows,
        "sorts": {k: _term(domain, v) for k, v in (raw.get("sorts") or {}).items()},
        "layers": dict(raw.get("layers") or {}),
        "polarities": dict(raw.get("polarities") or {}),
    }


def operator_for(plan_: dict, predicate: str, subject_kind: str, object_kind: str) -> str:
    rows = plan_["operators"]
    if (predicate, subject_kind, object_kind) in rows:
        return rows[(predicate, subject_kind, object_kind)]
    if (predicate, None, None) in rows:
        return rows[(predicate, None, None)]
    raise KeyError(f"no plan row for {predicate} {subject_kind}→{object_kind}; a shape with no row is refused, never nearest-typed")


def pins() -> CorpusPins:
    p = profile()
    return CorpusPins(
        science_contract=f"science:{p.base_contract_identity}",
        domains={ns: f"{ns}:{identity}" for ns, identity in p.activated_contracts.items()},
    )


def concept_binding() -> VocabularyBinding:
    return contract().sorts["concept"].vocabulary


def snapshot_over(declared: DatasetDeclaration, content: bytes, binding: VocabularyBinding) -> ResolutionSnapshot:
    address = dataset_address(declared)
    if binding.dataset_identity is None or address != f"dataset:{binding.dataset_identity}":
        raise RuntimeError(
            f"the fetched vocabulary dataset is {address}, but the `concept` sort binds "
            f"dataset:{binding.dataset_identity}; membership is measured against the dataset the contract names"
        )
    (resource,) = declared.resources
    if "sha256:" + sha256(content).hexdigest() != resource.digest:
        raise RuntimeError(
            f"the concept copy does not hash to the held vocabulary's declared digest {resource.digest}; "
            "membership is measured against the dataset the contract binds, never against an edited copy"
        )
    return build_snapshot(readable={binding: content.decode("utf-8").splitlines()})


def snapshot() -> ResolutionSnapshot:
    from beliefs import stored
    from reproduction import world

    st = state.load()
    content = Path(st["concepts_file"]).read_bytes()
    declared = stored.dataset_declaration(world.open_writer().read_view.get(st["concepts_ref"]))
    return snapshot_over(declared, content, concept_binding())
