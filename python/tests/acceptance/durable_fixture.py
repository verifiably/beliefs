"""The records cut 4's durable arms are asserted over, minted through the add
path into one registered corpus root.

Everything here goes through `CorpusWriter.add` — no raw write, no edit, no
deletion. Where an arm needs a state the add path does not produce, the arm
itself constructs it with the raw-write act; where it needs a state a deletion
*would* produce, it is **minted** instead, which is what §3's add-only reading
makes selectable: a basis entry naming an address no record carries is a state,
not a transition.
"""

from __future__ import annotations

from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import CorpusWriter

SPEC = "analysis-spec:s1"
RULE = "rule:threshold"

RAW = "dataset:raw"
DERIVED = "dataset:derived"
RUN = "run:r1"
PROPOSITION = "proposition:p1"
ASSESSMENT = "assessment:a1"

CHAIN = ("note:chain-a", "note:chain-b", "note:chain-c")
DIAMOND_TOP = "note:diamond-top"
DIAMOND_BOTTOM = "note:diamond-bottom"
CYCLE = ("note:cycle-a", "note:cycle-b")
UNDIRECTED = ("note:undirected-source", "note:undirected-target")
DANGLING_SOURCE = "note:dangling"
RENAMED = "note:renamed"
RENAMED_OLD = "note:renamed-old"
UNRELATED = "note:unrelated"

LINEAGE_ROOT = "dataset:lineage-root"
LINEAGE_MIDDLE = "dataset:lineage-middle"
LINEAGE_LEAF = "dataset:lineage-leaf"
LINEAGE_LEFT = "dataset:lineage-left"
LINEAGE_RIGHT = "dataset:lineage-right"
LINEAGE_CONFLICT = "dataset:lineage-conflict"
LINEAGE_ABSENT_ANCESTOR = "dataset:lineage-absent-ancestor"
LINEAGE_ABSENT_RUN = "dataset:lineage-absent-run"
LINEAGE_CYCLE = ("dataset:lineage-cycle-a", "dataset:lineage-cycle-b")

CITES = "cites"

_digests = iter(f"sha256:{index:064x}" for index in range(1, 1000))


def pinned() -> list[dict[str, str]]:
    """One distinct pinned resource, so every dataset has its own content
    identity and no two collide by accident."""
    return [{"name": "matrix", "digest": next(_digests)}]


def slug(ref: str) -> str:
    return ref.split(":", 1)[1]


def note(ref: str, *, relations=(), deprecated=()) -> Node:
    node = Node(id=ref, kind="note", title=slug(ref), relations=list(relations))
    node.deprecated_ids = list(deprecated)
    return node


def cites(source: str, target: str, *, predicate: str = CITES, directed: bool = True) -> Relation:
    return Relation(source=source, predicate=predicate, target=target, directed=directed)


def basis(*routes, tag: str = "single") -> dict[str, object]:
    return {"tag": tag, "routes": [dict(route) for route in routes]}


def route(run: str, ancestor: str, transforms=()) -> dict[str, object]:
    return {"run": run, "ancestor": ancestor, "transforms": list(transforms)}


def observed_dataset(ref: str = RAW):
    return stored.dataset_node(
        slug(ref), title=slug(ref), resources=pinned(), empirical_observation={"boundary": "instrument"}
    )


def mint_records(writer: CorpusWriter) -> None:
    """The kernel records: an observed dataset, the run that reads it, the
    proposition, the assessment that assesses it, and the dataset that run
    produces with its stamped basis."""
    writer.add(observed_dataset())
    writer.add(
        stored.run_node(
            slug(RUN),
            title="r1",
            spec=SPEC,
            observes=[RAW],
            transforms=[RAW],
            produces=[DERIVED],
        )
    )
    writer.add(
        stored.dataset_node(
            slug(DERIVED),
            title="derived",
            resources=pinned(),
            basis=basis(route(RUN, RAW, [RAW])),
        )
    )
    writer.add(stored.proposition_node(slug(PROPOSITION), title="p1", claim={"operator": "affects"}))
    writer.add(
        stored.assessment_node(
            slug(ASSESSMENT),
            title="a1",
            spec=SPEC,
            run=RUN,
            proposition=PROPOSITION,
            outcome="supported",
            interpretation_rule=RULE,
        )
    )


def mint_relation_fixture(writer: CorpusWriter) -> None:
    """S1's fixture: chain, diamond, cycle, unrelated predicate, deprecated
    ref, dangling target, and the undirected relation."""
    first, second, third = CHAIN
    writer.add(note(first, relations=[cites(first, second), cites(first, UNRELATED, predicate="mentions")]))
    writer.add(note(second, relations=[cites(second, third)]))
    writer.add(note(third, relations=[cites(third, RENAMED_OLD)]))
    writer.add(note(UNRELATED))
    writer.add(note(RENAMED, deprecated=[RENAMED_OLD]))

    left, right = "note:diamond-left", "note:diamond-right"
    writer.add(note(DIAMOND_TOP, relations=[cites(DIAMOND_TOP, left), cites(DIAMOND_TOP, right)]))
    writer.add(note(left, relations=[cites(left, DIAMOND_BOTTOM)]))
    writer.add(note(right, relations=[cites(right, DIAMOND_BOTTOM)]))
    writer.add(note(DIAMOND_BOTTOM))

    cycle_a, cycle_b = CYCLE
    writer.add(note(cycle_a, relations=[cites(cycle_a, cycle_b)]))
    writer.add(note(cycle_b, relations=[cites(cycle_b, cycle_a)]))

    source, target = UNDIRECTED
    writer.add(note(source, relations=[cites(source, target, directed=False)]))
    writer.add(note(target))

    writer.add(
        note(
            DANGLING_SOURCE,
            relations=[cites(DANGLING_SOURCE, UNRELATED), cites(DANGLING_SOURCE, "note:gone")],
        )
    )


def mint_lineage_fixture(writer: CorpusWriter) -> None:
    """S1a's fixture, walked as a facet: chain, diamond, cycle, a `single`
    basis, a `conflict` basis, and the two unresolvable cases — both **minted**,
    never produced by removing anything."""

    def dataset(ref: str, stamped=None):
        return stored.dataset_node(slug(ref), title=slug(ref), resources=pinned(), basis=stamped)

    writer.add(dataset(LINEAGE_ROOT))
    writer.add(dataset(LINEAGE_MIDDLE, basis(route(RUN, LINEAGE_ROOT))))
    writer.add(dataset(LINEAGE_LEAF, basis(route(RUN, LINEAGE_MIDDLE))))

    writer.add(dataset(LINEAGE_LEFT, basis(route(RUN, LINEAGE_ROOT))))
    writer.add(dataset(LINEAGE_RIGHT, basis(route(RUN, LINEAGE_ROOT))))
    # The diamond's apex needs two routes out of one dataset, which `single`
    # cannot spell — so the diamond and the conflict tag are one fixture.
    writer.add(
        dataset(
            LINEAGE_CONFLICT,
            basis(route(RUN, LINEAGE_LEFT), route(RUN, LINEAGE_RIGHT), tag="conflict"),
        )
    )

    writer.add(dataset(LINEAGE_ABSENT_ANCESTOR, basis(route(RUN, "dataset:absent"))))
    writer.add(dataset(LINEAGE_ABSENT_RUN, basis(route("run:absent", LINEAGE_ROOT))))

    cycle_a, cycle_b = LINEAGE_CYCLE
    writer.add(dataset(cycle_a, basis(route(RUN, cycle_b))))
    writer.add(dataset(cycle_b, basis(route(RUN, cycle_a))))


def mint_cut4_corpus(writer: CorpusWriter) -> None:
    mint_records(writer)
    mint_relation_fixture(writer)
    mint_lineage_fixture(writer)
