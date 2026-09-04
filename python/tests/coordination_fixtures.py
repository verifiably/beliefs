from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import ClassVar

from authority import FULL
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor, WritePlanExecutor

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.contract.coordination import parse_coordination_contract
from beliefs.corpus import CorpusWriter
from beliefs.profile import compile_profile

AT = "2026-09-02T12:00:00Z"
EMPTY_QUERY = {"version": "science.view-query.v1", "clauses": []}

COORDINATION_DOCUMENT = {
    "contract": "coordination",
    "version": 1,
    "lineage": "genesis",
    "description": "Project coordination records",
    "address_root": "project",
    "query_vocabulary": {
        "kinds": [
            "proposition",
            "source-assertion",
            "assessment",
            "analysis-spec",
            "run",
            "verification",
            "dataset",
            "source",
            "holdings-observation",
            "retraction",
            "instrument-certification",
            "coreference-attestation",
            "act-report",
        ],
        "relations": [
            "assesses",
            "observes",
            "reads",
            "transforms",
            "produces",
            "produced_by",
            "executes",
            "targets",
            "verifies",
            "member_of",
            "grounded-in",
        ],
    },
    "kinds": {
        **{
            kind: {
                "fields": ["name", "body", "author", "at", "query"],
                "query_versions": ["science.view-query.v1"],
            }
            for kind in ("project", "question", "hypothesis", "topic", "theme")
        },
        "task": {
            "fields": ["name", "body", "author", "at", "status", "depends"],
            "query_versions": [],
        },
        "decision": {
            "fields": ["name", "body", "author", "at"],
            "query_versions": [],
        },
        "note": {
            "fields": ["name", "body", "author", "at", "about"],
            "query_versions": [],
        },
    },
}


def coordination_contract(document=None, predecessor=None):
    return parse_coordination_contract(
        deepcopy(COORDINATION_DOCUMENT if document is None else document),
        source="<coordination-test>",
        predecessor=predecessor,
    )


def coordination_profile(base_contract, *, document=None):
    return compile_profile(base_contract, [], coordination=coordination_contract(document))


def content_for(kind, *, name=None, **changes) -> dict[str, object]:
    content: dict[str, object] = {"name": name or kind, "body": "", "author": "actor", "at": AT}
    if kind in {"project", "question", "hypothesis", "topic", "theme"}:
        content["query"] = EMPTY_QUERY
    elif kind == "task":
        content.update(status="open", depends=[])
    content.update(changes)
    return content


def pins_for(profile):
    return CorpusPins(
        "science:" + profile.base_contract_identity,
        {namespace: f"{namespace}:{identity}" for namespace, identity in profile.activated_contracts.items()},
    )


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
    CorpusWriter(root, executor_factory, authority=FULL).adopt_manifest(profile=pins_for(profile))
    return root


def raw_add(root, *nodes):
    corpus = Corpus(root)
    for node in nodes:
        corpus.add(node)
