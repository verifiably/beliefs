"""Tree values and the `sha256-tree` digest."""

from __future__ import annotations

import pytest

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.tree import (
    TREE_DOMAIN,
    Tree,
    TreeMember,
    make_tree,
    object_path,
    parse_tree_file,
    tree_digest,
    tree_file_bytes,
)

_D = "sha256:" + "a" * 64


def m(path: str, digest: str = _D, size: int = 3) -> TreeMember:
    return TreeMember(path, digest, size)


def test_tree_digest_is_the_v1_digest_of_the_member_list():
    t = Tree((m("a/x.txt"),))
    expected = v1.digest(TREE_DOMAIN, {"members": [{"digest": _D, "path": "a/x.txt", "size": 3}]})
    assert tree_digest(t) == "sha256-tree:" + expected
    assert tree_file_bytes(t).startswith(b"science.dataset-tree.v1\n")


def test_make_tree_sorts_and_tree_refuses_unsorted():
    assert make_tree([m("b"), m("a")]).members[0].path == "a"
    with pytest.raises(MalformedRecord):
        Tree((m("b"), m("a")))


@pytest.mark.parametrize(
    "build",
    [
        lambda: Tree(()),
        lambda: Tree((m("a"), m("a"))),
        lambda: Tree((m("a/b"), m("a/b-x"), m("a/b/c"))),
        lambda: m("é"),
        lambda: m("../x"),
        lambda: m("/x"),
        lambda: m("a//b"),
        lambda: m("a/.#~tmp"),
        lambda: m("a", size=-1),
        lambda: m("a", size=True),
        lambda: m("a", digest="md5:" + "a" * 32),
        lambda: m("a", digest="sha256:" + "a" * 63),
        lambda: m("a", digest="sha256-tree:" + "a" * 64),
    ],
)
def test_tree_refuses(build):
    with pytest.raises(MalformedRecord):
        build()


def test_parse_tree_file_round_trips_and_refuses():
    t = make_tree([m("a/x.txt"), m("b", size=0)])
    data = tree_file_bytes(t)
    assert parse_tree_file(data) == t
    body = data.split(b"\n", 1)[1]
    bad = [
        b"science.dataset-tree.v2\n" + body,
        body,
        data + b"\n",
        data.replace(b'"members":', b'"members": '),
        b"science.dataset-tree.v1\n" + v1.encode({"members": [], "extra": 1}),
        b"science.dataset-tree.v1\n" + v1.encode({"members": [{"digest": _D, "path": "a", "size": 1, "x": 1}]}),
    ]
    for case in bad:
        with pytest.raises(MalformedRecord):
            parse_tree_file(case)


def test_object_path_fans_out_by_the_first_two_hex_digits():
    hex_ = "ab" + "0" * 62
    assert object_path("sha256:" + hex_) == "objects/sha256/ab/" + hex_
    assert object_path("sha256-tree:" + hex_) == "objects/sha256/ab/" + hex_
