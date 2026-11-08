"""Tree values: a dataset directory as a sorted list of file members.

A tree is identified by `sha256-tree:<hex>`, the `science.identity.v1` digest
of its member list under `TREE_DOMAIN`. The stored tree file is the domain line
followed by the canonical bytes of `{"members": [...]}`, so the digest is also
the sha256 of the file's bytes.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise
from typing import final

from beliefs.errors import CanonicalTextRefused, MalformedRecord
from beliefs.holdings.records import require_canonical_digest, require_store_relative_path
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "TREE_ALGORITHM",
    "TREE_DOMAIN",
    "Tree",
    "TreeMember",
    "make_tree",
    "object_path",
    "parse_tree_file",
    "tree_digest",
    "tree_file_bytes",
]

TREE_DOMAIN = "science.dataset-tree.v1"
TREE_ALGORITHM = "sha256-tree"

_FILE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_OBJECT_DIGEST = re.compile(r"^(?:sha256|sha256-tree):(?P<hex>[0-9a-f]{64})$")


@sealed
@final
@dataclass(frozen=True)
class TreeMember:
    path: str
    digest: str
    size: int

    def __post_init__(self) -> None:
        require_store_relative_path(self.path)
        if unicodedata.normalize("NFC", self.path) != self.path:
            raise MalformedRecord(f"tree member path {self.path!r} is not NFC-normalised")
        if type(self.digest) is not str or _FILE_DIGEST.fullmatch(self.digest) is None:
            raise MalformedRecord(f"tree member digest {self.digest!r} is not `sha256:` and 64 lowercase hex digits")
        require_canonical_digest(self.digest, "a tree member's digest")
        if type(self.size) is not int or self.size < 0:
            raise MalformedRecord(f"tree member size {self.size!r} is not a non-negative integer")


@sealed
@final
@dataclass(frozen=True)
class Tree:
    members: tuple[TreeMember, ...]

    def __post_init__(self) -> None:
        if type(self.members) is not tuple or not self.members:
            raise MalformedRecord("a tree holds a non-empty tuple of members")
        for member in self.members:
            if type(member) is not TreeMember:
                raise MalformedRecord(f"tree member {member!r} is not a TreeMember")
        paths = [member.path for member in self.members]
        for before, after in pairwise(paths):
            if before == after:
                raise MalformedRecord(f"tree path {after!r} appears twice")
            if before > after:
                raise MalformedRecord(f"tree members are not sorted by path: {before!r} precedes {after!r}")
        directories = frozenset("/".join(path.split("/")[:i]) for path in paths for i in range(1, path.count("/") + 1))
        for path in paths:
            if path in directories:
                raise MalformedRecord(f"tree path {path!r} is both a file and a directory")


def make_tree(members: Iterable[TreeMember]) -> Tree:
    return Tree(tuple(sorted(members, key=lambda member: member.path)))


def _value(tree: Tree) -> dict[str, object]:
    return {"members": [{"digest": m.digest, "path": m.path, "size": m.size} for m in tree.members]}


def tree_file_bytes(tree: Tree) -> bytes:
    return TREE_DOMAIN.encode("utf-8") + b"\n" + v1.encode(_value(tree))


def tree_digest(tree: Tree) -> str:
    return f"{TREE_ALGORITHM}:{v1.digest(TREE_DOMAIN, _value(tree))}"


def parse_tree_file(data: bytes) -> Tree:
    head, newline, rest = data.partition(b"\n")
    if not newline or head != TREE_DOMAIN.encode("utf-8"):
        raise MalformedRecord(f"a tree file starts with the line {TREE_DOMAIN!r}")
    try:
        parsed = v1.decode(rest)
    except CanonicalTextRefused as caught:
        raise MalformedRecord(f"a tree file's body is not canonical text: {caught}") from caught
    if type(parsed) is not dict or set(parsed) != {"members"} or type(parsed["members"]) is not list:  # pyright: ignore[reportUnknownArgumentType]
        raise MalformedRecord("a tree file's body is exactly {'members': [...]}")
    members: list[TreeMember] = []
    for raw in parsed["members"]:  # pyright: ignore[reportUnknownVariableType]
        if type(raw) is not dict or set(raw) != {"digest", "path", "size"}:  # pyright: ignore[reportUnknownArgumentType]
            raise MalformedRecord(f"tree member {raw!r} is not exactly digest, path and size")
        members.append(TreeMember(path=raw["path"], digest=raw["digest"], size=raw["size"]))  # pyright: ignore[reportUnknownArgumentType]
    tree = Tree(tuple(members))
    if tree_file_bytes(tree) != data:
        raise MalformedRecord("a tree file is not the canonical encoding of its members")
    return tree


def object_path(digest: str) -> str:
    match = _OBJECT_DIGEST.fullmatch(digest) if isinstance(digest, str) else None
    if match is None:
        raise MalformedRecord(f"{digest!r} is not a `sha256:` or `sha256-tree:` digest")
    hex_ = match.group("hex")
    return f"objects/sha256/{hex_[:2]}/{hex_}"
