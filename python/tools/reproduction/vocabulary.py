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
# The cut-22 document, byte-for-byte, so `check_succession` runs against the
# real predecessor rather than against a contract written to pass.
CUT22_DOCUMENT = Path(__file__).with_name("mm30-cut22.yaml")
# The cut-31 document, byte-for-byte: the estimand lane's contract, which this
# lane's `edges:` table succeeds. The chain is walked, not summarized.
CUT31_DOCUMENT = Path(__file__).with_name("mm30-cut31.yaml")
MODAL_SORTED = paths.REPO / "python" / "tools" / "vocabularies" / "mm30-modal-sorted.yaml"
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
    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    return shipped_domain_contract("biology")


PREDECESSORS = {DOCUMENT: CUT31_DOCUMENT, CUT31_DOCUMENT: CUT22_DOCUMENT}
"""Each document and the one it succeeds: cut 22 → cut 31 → current. The
chain is parsed document by document, never summarized by identity."""


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    """The successor mm30 contract, checked against the document it succeeds —
    the cut-31 document, which itself succeeds the cut-22 one. Each predecessor
    is parsed here rather than trusted by shape: `check_succession` certifies
    nothing against an authored stand-in."""
    ancestor = PREDECESSORS.get(path)
    predecessor = contract(ancestor) if ancestor is not None else None
    return parse_domain_contract(
        _document(path)["contract"], source=f"{path}: contract", base=base(), predecessor=predecessor
    )


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


def binding_for(sort: str) -> VocabularyBinding:
    return contract().sorts[sort].vocabulary


def concept_binding() -> VocabularyBinding:
    return binding_for("concept")


# Every held list, by the `state.json` prefix its step saved and the sort the
# contract binds it to. One snapshot covers all four (design §9).
HELD_SORTS = {"concepts": "concept", "levels": "stage-level", "measures": "measure", "identifications": "identification"}


def checked_lines(declared: DatasetDeclaration, content: bytes, binding: VocabularyBinding) -> list[str]:
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


def snapshot_over(declared: DatasetDeclaration, content: bytes, binding: VocabularyBinding) -> ResolutionSnapshot:
    return build_snapshot(readable={binding: checked_lines(declared, content, binding)})


def snapshot() -> ResolutionSnapshot:
    from beliefs import stored
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
