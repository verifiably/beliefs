from collections.abc import Callable
from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import Any, ClassVar

from authority import FULL
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor, WritePlanExecutor
from profiles import pins_for

from beliefs import stored
from beliefs.contract.coordination import parse_coordination_contract
from beliefs.contract.document import parse_document
from beliefs.corpus import CorpusWriter
from beliefs.profile import compile_profile, shipped_base_contract

AT = "2026-09-02T12:00:00Z"
EMPTY_QUERY = {"version": "science.view-query.v1", "clauses": []}

_SHIPPED_V1 = parse_document(
    resources.files("beliefs").joinpath("contracts/coordination/v1/CONTRACT.yaml").read_text(encoding="utf-8"),
    source="beliefs/contracts/coordination/v1/CONTRACT.yaml",
)
assert isinstance(_SHIPPED_V1, dict), "the shipped v1 coordination contract is a mapping"
COORDINATION_DOCUMENT: dict[str, Any] = _SHIPPED_V1


def coordination_contract(document=None, predecessor=None):
    return parse_coordination_contract(
        deepcopy(COORDINATION_DOCUMENT if document is None else document),
        source="<coordination-test>",
        predecessor=predecessor,
    )


def coordination_profile(base_contract, *, document=None, version=1):
    if version == 2:
        assert document is None, "a v2 profile is the shipped contract"
        from beliefs.profile import shipped_coordination

        return compile_profile(shipped_base_contract(), [], coordination=shipped_coordination(2))
    return compile_profile(shipped_base_contract(), [], coordination=coordination_contract(document))


def content_for(kind, *, name=None, **changes) -> dict[str, object]:
    content: dict[str, object] = {"name": name or kind, "body": "", "author": "actor", "at": AT}
    if kind in {"project", "question", "hypothesis", "topic", "theme"}:
        content["query"] = EMPTY_QUERY
    elif kind == "task":
        content.update(status="open", depends=[])
    content.update(changes)
    return content


def raw_coordination_node(kind, project, revision, *, local=None, supersedes=(), **facet):
    node_id = f"{kind}:{project}.{revision}" if local is None else f"{kind}:{project}.{local}.{revision}"
    if kind in {"project", "question", "hypothesis", "topic", "theme"}:
        facet.setdefault("query", {"version": "science.view-query.v1", "clauses": []})
    elif kind == "task":
        facet.setdefault("status", "open")
        facet.setdefault("depends", [])
    return Node(
        id=node_id,
        uid=revision,
        kind=kind,
        title=facet.pop("name", kind),
        body=facet.pop("body", ""),
        facets={
            stored.COORDINATION_FACET: {
                "project": project,
                **({} if local is None else {"local": local}),
                "author": facet.pop("author", "actor"),
                "at": facet.pop("at", AT),
                **facet,
            }
        },
        relations=[
            Relation(source=node_id, predicate=stored.SUPERSEDES, target=target) for target in supersedes
        ],
    )


class Recorder:
    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


def mounted_root(
    root, profile, executor_factory: Callable[[Path], WritePlanExecutor] = DefaultExecutor
):
    CorpusWriter(root, executor_factory, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
    return root


def raw_add(root, *nodes):
    corpus = Corpus(root)
    for node in nodes:
        corpus.add(node)
