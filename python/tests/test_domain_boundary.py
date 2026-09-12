"""D1 — `nodes` assigns no domain semantics, read as an invariance.

For every bijective renaming ρ of namespace tokens (the part of a facet name before
`/`), every public `nodes` operation commutes with ρ. Built-in facet names carry no
`/`, so ρ never touches them; consumer invariants are the consumer's domain semantics
and are outside the property, so the registry here holds only the kernel's shape
invariants. Diagnostics compare after renaming and re-sorting, since `Registry.check`
sorts by name and a renamed token legitimately moves.

Design: docs/superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md §3.
The subject is the installed `nodes`; N2 runs this same test against a sabotaged copy
(n2_arms_cut26.py), where it must fail.
"""

from __future__ import annotations

import re

import pytest
from nodes.core.corpus import Corpus
from nodes.core.errors import FacetError
from nodes.core.frontmatter import node_from_bytes, node_from_markdown, node_to_markdown
from nodes.core.node import Node
from nodes.core.paths import path_for_node_id
from nodes.core.projection import to_canonical
from nodes.core.registry import KindSpec, Registry, Violation
from nodes.core.shapes import register_builtin_shapes
from nodes.core.write_plan import CreateOp

NAMESPACED = re.compile(r"^([^/]+)/([^/]+)$")

RENAMINGS = {
    "sorts-first": {"biology": "aaa"},  # the renamed token sorts before every other key
    "sorts-last": {"biology": "zzz"},  # and after
}

# `nodes`' own `fixtures/gene-axis.md`, inlined: a sabotaged copy of the package has no
# fixtures directory beside it, and the check must read the same bytes either way.
GENE_AXIS = """---
id: dataset:gene-expression-matrix
uid: 4f1a9c2e8b7d4f1a9c2e8b7d4f1a9c2e
kind: dataset
title: Gene expression matrix
facets:
  biology:
    organism: Homo sapiens
  biology/gene-axis:
    axis: rows
---
Rows are genes; columns are samples.
"""


def _rename_name(name: str, rho: dict[str, str]) -> str:
    match = NAMESPACED.match(name)
    if match is None:
        return name
    return f"{rho.get(match[1], match[1])}/{match[2]}"


def _rename_node(node: Node, rho: dict[str, str]) -> Node:
    return node.model_copy(update={"facets": {_rename_name(k, rho): v for k, v in node.facets.items()}})


def _rename_spec(spec: KindSpec, rho: dict[str, str]) -> KindSpec:
    return spec.model_copy(
        update={
            "required_facets": {_rename_name(n, rho) for n in spec.required_facets},
            "optional_facets": {_rename_name(n, rho) for n in spec.optional_facets},
        }
    )


def _rename_canonical(canonical: dict[str, object], rho: dict[str, str]) -> dict[str, object]:
    facets = canonical["facets"]
    assert isinstance(facets, dict)
    return {**canonical, "facets": {_rename_name(k, rho): v for k, v in facets.items()}}


def _rename_violations(violations: list[Violation], rho: dict[str, str]) -> list[Violation]:
    renamed = [
        Violation(
            code=v.code,
            detail=_rename_name(v.detail, rho),
            message=v.message.replace(repr(v.detail), repr(_rename_name(v.detail, rho))),
        )
        for v in violations
    ]
    return sorted(renamed, key=lambda v: (v.code, v.detail))


def _sorted(violations: list[Violation]) -> list[Violation]:
    return sorted(violations, key=lambda v: (v.code, v.detail))


SPECS = (
    KindSpec(name="dataset", required_facets={"biology/gene-axis"}, optional_facets={"biology", "chemistry/assay"}),
    KindSpec(name="genes", shape="set", optional_facets={"biology/gene-axis"}),
)


def _registry(rho: dict[str, str]) -> Registry:
    """Kernel invariants only: the built-in shapes and nothing supplied by a consumer."""
    registry = Registry()
    register_builtin_shapes(registry)
    for spec in SPECS:
        registry.register(_rename_spec(spec, rho))
    return registry


def _nodes() -> dict[str, Node]:
    # Constructed, not parsed: a node the parser never touched, so that a parser that
    # drops a facet is caught at clause 1 rather than hidden by having dropped it here.
    gene_axis = Node(
        id="dataset:gene-expression-matrix",
        uid="4f1a9c2e8b7d4f1a9c2e8b7d4f1a9c2e",
        kind="dataset",
        title="Gene expression matrix",
        body="Rows are genes; columns are samples.",
        facets={"biology": {"organism": "Homo sapiens"}, "biology/gene-axis": {"axis": "rows"}},
    )
    return {
        "valid": gene_axis,
        # A non-empty membership naming the dataset, so clause 4 has a structural reference
        # to read back through `members` and `containers` and not only a node to fetch.
        "built-in-beside-namespaced": Node(
            id="genes:all",
            uid="0" * 32,
            kind="genes",
            title="all genes",
            facets={
                "membership": {"members": ["dataset:gene-expression-matrix"]},
                "biology/gene-axis": {"axis": "rows"},
            },
        ),
        "missing-required": gene_axis.model_copy(update={"facets": {"biology": {"organism": "Homo sapiens"}}}),
        "unexpected": gene_axis.model_copy(
            update={"facets": {**gene_axis.facets, "biology/extra": {}, "physics/extra": {}}}
        ),
    }


def _validate_outcome(registry: Registry, node: Node) -> type[BaseException] | None:
    try:
        registry.validate(node)
    except FacetError as error:
        return type(error)
    return None


@pytest.mark.parametrize("rho", list(RENAMINGS.values()), ids=list(RENAMINGS))
def test_d1_installed_nodes_is_invariant_under_namespace_renaming(rho, tmp_path):
    identity: dict[str, str] = {}
    registry, renamed_registry = _registry(identity), _registry(rho)
    # the fixture nodes ships parses to the facets the constructed node carries
    assert node_from_markdown(GENE_AXIS).facets == _nodes()["valid"].facets
    for label, node in _nodes().items():
        renamed = _rename_node(node, rho)
        # 1. the boundary parser and serializer commute with ρ
        assert node_from_markdown(node_to_markdown(renamed)) == _rename_node(
            node_from_markdown(node_to_markdown(node)), rho
        ), label
        assert node_from_bytes(node_to_markdown(renamed).encode("utf-8")) == _rename_node(
            node_from_bytes(node_to_markdown(node).encode("utf-8")), rho
        ), label
        # 2. the canonical projection commutes with ρ, as structures
        assert to_canonical(renamed) == _rename_canonical(to_canonical(node), rho), label
        # 3. validation verdicts and re-sorted diagnostics commute with ρ
        assert _validate_outcome(renamed_registry, renamed) == _validate_outcome(registry, node), label
        assert _sorted(renamed_registry.check(renamed)) == _rename_violations(registry.check(node), rho), label
    # non-empty by construction, so clause 3 compared something
    nodes = _nodes()
    assert _validate_outcome(registry, nodes["missing-required"]) is FacetError
    assert [v.code for v in registry.check(nodes["unexpected"])] == ["facet-unexpected", "facet-unexpected"]
    # 4. a corpus written with ρ(n) reads back as ρ of what n reads back as — the nodes
    #    themselves and the structural index over them
    dataset, container = nodes["valid"], nodes["built-in-beside-namespaced"]
    read: dict[str, tuple[list[Node], list[Node], list[str], list[str]]] = {}
    for label, mapping in (("plain", identity), ("renamed", rho)):
        root = tmp_path / label
        root.mkdir()
        corpus = Corpus(root, registry=_registry(mapping))
        plan = [
            CreateOp(path_for_node_id(n.id), node_to_markdown(_rename_node(n, mapping)).encode("utf-8"))
            for n in (dataset, container)
        ]
        corpus.executor.execute(plan)
        reopened = Corpus(root, registry=_registry(mapping))
        read[label] = (
            [reopened.get(n.id) for n in (dataset, container)],
            reopened.all(),
            reopened.members(container.id),
            reopened.containers(dataset.id),
        )
        assert [n.id for n in read[label][1]] == [dataset.id, container.id]
    plain_nodes, plain_all, plain_members, plain_containers = read["plain"]
    assert plain_members == [dataset.id] and plain_containers == [container.id]  # non-empty by construction
    assert read["renamed"] == (
        [_rename_node(n, rho) for n in plain_nodes],
        [_rename_node(n, rho) for n in plain_all],
        plain_members,
        plain_containers,
    )
