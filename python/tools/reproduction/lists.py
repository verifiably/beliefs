"""Step 1c: hold mm30's three corpus-local sort vocabularies as datasets.

Two entry points, because `world.adopt()` compiles the contract and the
contract binds every list's dataset address: `prepare` writes each list and
computes its address **before** anything adopts, `mint` holds its bytes
through the holdings boundary and mints its dataset record afterwards. The
line format is the tool's, the same one `concepts.py` writes (design §6.3):
one canonical identifier per line, sorted, newline-terminated.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path

from nodes.core.node import Node

from beliefs import stored
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.identifiers import not_a_canonical_identifier
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import profile

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/lists.v1"

# `identification` carries the predecessor's two-axis values; `none` is
# deliberately absent, because an estimand with no identification does not
# freeze (estimand-typing design §9).
LISTS: dict[str, tuple[str, list[str]]] = {
    "levels": ("mm30-stage-levels.txt", ["level:ndmm", "level:pd"]),
    "measures": ("mm30-measures.txt", ["measure:rna-seq-tpm"]),
    "identifications": (
        "mm30-identifications.txt",
        ["identification:interventional", "identification:longitudinal", "identification:observational", "identification:structural"],
    ),
}
TITLES = {
    "levels": "mm30 stage-level vocabulary",
    "measures": "mm30 measure vocabulary",
    "identifications": "mm30 identification vocabulary",
}


def list_lines(terms: Iterable[str]) -> bytes:
    """One canonical identifier per line, sorted, newline-terminated."""
    ordered = sorted(terms)
    for term in ordered:
        problem = not_a_canonical_identifier(term)
        if problem is not None:
            raise ValueError(f"{term!r} is not a canonical identifier: {problem}")
    return "".join(term + "\n" for term in ordered).encode()


def list_node(name: str, digest: str) -> Node:
    return stored.dataset_node(title=TITLES[name], resources=[{"name": LISTS[name][0], "digest": digest}])


def hold_list(name: str, terms: Iterable[str]) -> tuple[str, Path]:
    """Write one list to the work directory and return its dataset address and
    the file written. The address is what the contract's sort binds, so it is
    computed here — before adoption — and minted unchanged by `mint`."""
    content = list_lines(terms)
    path = paths.WORK / LISTS[name][0]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return list_node(name, "sha256:" + sha256(content).hexdigest()).id, path


def prepare() -> int:
    saved: dict[str, object] = {}
    for name, (_resource, terms) in LISTS.items():
        address, path = hold_list(name, terms)
        saved[f"{name}_address"], saved[f"{name}_file"], saved[f"{name}_count"] = address, str(path), len(terms)
        print(f"{name}: {len(terms)} terms as {address}")
    state.save(**saved)
    return 0


def mint() -> int:
    st = state.load()
    ctx = ActContext(
        paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=profile()
    )
    writer = world.open_writer()
    for name, (resource, terms) in LISTS.items():
        content = Path(st[f"{name}_file"]).read_bytes()
        digest = "sha256:" + sha256(content).hexdigest()
        write(ctx, StoreLocator(st["store_id"], f"mm30-lists/{resource}"), content, expected=digest)
        minted = writer.add(list_node(name, digest))
        state.save(**{f"{name}_ref": minted.id})
        findings.record(
            1,
            "closed",
            f"held {len(terms)} {name} as {digest}; dataset {minted.id}; the line format is the tool's (design §6.3)",
        )
        print(f"held {len(terms)} {name} as {digest}; dataset {minted.id}")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["prepare"]:
        return prepare()
    if argv == ["mint"]:
        return mint()
    print("usage: python -m reproduction.lists prepare|mint")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
