"""The base, biology, and mm30 contracts used by the reproduction.

**The contract layer is retired with the v1 grammar** (beliefs-d64969, ruling P11).
`mm30.yaml` and its predecessors are v1 documents (`operators`, `edges`,
slot-keyed `estimands`) and no biology pack ships, so nothing here that compiles a
contract can run under base v2: `contract`, `plan` and `binding_for` raise
`MalformedContract` (base v2 refuses a v1 document), `biology`, `profile` and
`pins` raise `ProfileError`, `snapshot` reaches one of the two, and
`checked_lines` / `snapshot_over` still read the v1 binding's `dataset_identity`.
The contract-layer imports live inside
the functions that compile, so the driver's other steps (`hold`, `spec`, `run`)
still import. The documents stay in place as the v1 heritage the mm30 recreate
reads; beliefs-709bd9 restores this module against the biology v2 genesis and the
mm30 corpus-local v2 contract.
"""

from __future__ import annotations

from functools import cache
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from beliefs.dataset import DatasetDeclaration, dataset_address
from reproduction import paths, state

if TYPE_CHECKING:
    from beliefs.consulted import CorpusPins
    from beliefs.contract.domain import DomainContract, SortBinding
    from beliefs.profile import ProfileSpec
    from beliefs.resolution import ResolutionSnapshot

DOCUMENT = Path(__file__).with_name("mm30.yaml")
# The earliest document, byte-for-byte, so `check_succession` runs against the
# real predecessor rather than against a contract written to pass.
CUT22_DOCUMENT = Path(__file__).with_name("mm30-cut22.yaml")
# The estimand-era document, byte-for-byte: the estimand contract, which this
# lane's `edges:` table succeeds. The chain is walked, not summarized.
CUT31_DOCUMENT = Path(__file__).with_name("mm30-cut31.yaml")
MODAL_SORTED = paths.REPO / "python" / "tools" / "reproduction" / "mm30-modal-sorted.yaml"
# Each sort binds the dataset address of a list held before anything adopts
# (`lists.py`, `concepts.py`): the contract cannot compile without them.
VOCABULARY_TOKENS = {
    "{{CONCEPTS}}": "concepts_address",
    "{{LEVELS}}": "levels_address",
    "{{MEASURES}}": "measures_address",
    "{{IDENTIFICATIONS}}": "identifications_address",
}


@cache
def _document(path: Path = DOCUMENT) -> dict:
    text = path.read_text()
    st = state.load()
    for token, key in VOCABULARY_TOKENS.items():
        if token not in text:
            continue
        if key not in st:
            raise RuntimeError(
                f"{path.name} binds a sort to the held list {key}; run lists.py (step 1c) and concepts.py (step 1b) "
                "before anything compiles the contract"
            )
        text = text.replace(token, st[key].removeprefix("dataset:"))
    return yaml.safe_load(text)


@cache
def base():
    from beliefs.profile import shipped_base_contract

    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    from beliefs.profile import shipped_domain_contract

    return shipped_domain_contract("biology")


PREDECESSORS = {DOCUMENT: CUT31_DOCUMENT, CUT31_DOCUMENT: CUT22_DOCUMENT}
"""Each document and the one it succeeds: earliest → estimand-era → current. The
chain is parsed document by document, never summarized by identity."""


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    """The successor mm30 contract, checked against the document it succeeds —
    the estimand-era document, which itself succeeds the earliest one. Each predecessor
    is parsed here rather than trusted by shape: `check_succession` certifies
    nothing against an authored stand-in."""
    from beliefs.contract.domain import parse_domain_contract

    ancestor = PREDECESSORS.get(path)
    predecessor = contract(ancestor) if ancestor is not None else None
    return parse_domain_contract(
        _document(path)["contract"], source=f"{path}: contract", base=base(), predecessor=predecessor
    )


@cache
def profile(path: Path = DOCUMENT) -> ProfileSpec:
    from beliefs.profile import compile_profile

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
    raise KeyError(
        f"no plan row for {predicate} {subject_kind}→{object_kind}; a shape with no row is refused, never nearest-typed"
    )


def pins() -> CorpusPins:
    from beliefs.consulted import CorpusPins

    p = profile()
    return CorpusPins(
        science_contract=f"science:{p.base_contract_identity}",
        domains={ns: f"{ns}:{identity}" for ns, identity in p.activated_contracts.items()},
    )


def binding_for(sort: str) -> SortBinding:
    return contract().sorts[sort].vocabulary


def concept_binding() -> SortBinding:
    return binding_for("concept")


# Every held list, by the `state.json` prefix its step saved and the sort the
# contract binds it to. One snapshot covers all four.
HELD_SORTS = {
    "concepts": "concept",
    "levels": "stage-level",
    "measures": "measure",
    "identifications": "identification",
}


def checked_lines(declared: DatasetDeclaration, content: bytes, binding: SortBinding) -> list[str]:
    address = dataset_address(declared)
    if binding.dataset_identity is None or address != f"dataset:{binding.dataset_identity}":
        raise RuntimeError(
            f"the fetched vocabulary dataset is {address}, but the sort binds "
            f"dataset:{binding.dataset_identity}; membership is measured against the dataset the contract names"
        )
    (resource,) = declared.resources
    if "sha256:" + sha256(content).hexdigest() != resource.digest:
        raise RuntimeError(
            f"the held copy does not hash to the held vocabulary's declared digest {resource.digest}; "
            "membership is measured against the dataset the contract binds, never against an edited copy"
        )
    return content.decode("utf-8").splitlines()


def snapshot_over(declared: DatasetDeclaration, content: bytes, binding: SortBinding) -> ResolutionSnapshot:
    from beliefs.resolution import build_snapshot

    return build_snapshot(readable={binding: checked_lines(declared, content, binding)})


def snapshot() -> ResolutionSnapshot:
    from beliefs import stored
    from beliefs.resolution import build_snapshot
    from reproduction import world

    st = state.load()
    view = world.open_writer().read_view
    readable = {}
    for prefix, sort in HELD_SORTS.items():
        binding = binding_for(sort)
        content = Path(st[f"{prefix}_file"]).read_bytes()
        declared = stored.dataset_declaration(view.get(st[f"{prefix}_ref"]))
        readable[binding] = checked_lines(declared, content, binding)
    return build_snapshot(readable=readable)
