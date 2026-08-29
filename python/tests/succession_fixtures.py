"""Fabricated roots for the successor-admission tests: real engine, real seam.

Every blocker is genuine durable state — records through the port's
non-fulfilling `execute`, intents through `append_intent`, reports through
`execute_fulfilling` (cut 12 §6). Nothing here hands the act a set.
"""

from __future__ import annotations

from pathlib import Path

from fixtures_cut3 import spec_draft, spec_rules
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp
from test_operation_port import durable_port

from science import root as science_root
from science import stored
from science.identity import v1
from science.root import init_corpus_root
from science.spec import FrozenSpec, SuccessorAdmitted, SuccessorRefused, freeze, revise
from science.succession import admit_spec_successor

RUN = "run:r1"
PROPOSITION = "proposition:p1"
RULE = "rule:threshold"


def corpus(work: Path, name: str):
    root = work / name
    init_corpus_root(root)
    return root, durable_port(root)


def specs() -> tuple[FrozenSpec, FrozenSpec, FrozenSpec]:
    """`(original, unreferenced, referencing)` — the second supersedes nothing,
    the third supersedes the first by construction."""
    original = freeze(spec_draft(), held_rules=spec_rules())
    unreferenced = freeze(spec_draft(estimand="revised"), held_rules=spec_rules())
    referencing = revise(
        original, edits={"estimand": "revised"}, held_rules=spec_rules(), recorded_failures=frozenset()
    )
    return original, unreferenced, referencing


def assessment(spec_identity: str, slug: str = "a1") -> Node:
    return stored.assessment_node(
        slug,
        title=slug,
        spec=spec_identity,
        run=RUN,
        proposition=PROPOSITION,
        outcome="refuted",
        interpretation_rule=RULE,
    )


def identity_of(assessment_node: Node) -> str:
    return stored.assessment_value(assessment_node).identity()


def verification(slug: str, target: Node, verdict: str, *, supersedes: str | None = None) -> Node:
    return stored.verification_node(
        slug,
        title=slug,
        assessment=identity_of(target),
        assessment_ref=target.id,
        scope="clean-environment",
        verdict=verdict,
        supersedes=supersedes,
    )


def path_of(node: Node) -> str:
    kind, _, slug = node.id.partition(":")
    return f"{kind}/{slug}.md"


def plan(*nodes: Node) -> tuple[CreateOp, ...]:
    return tuple(CreateOp(path_of(node), node_to_markdown(node).encode("utf-8")) for node in nodes)


def publish(port, *nodes: Node) -> None:
    port.execute(plan(*nodes))


def append_assessment_intent(port, spec_identity: str, token: str = "tok") -> str:
    return port.append_intent(v1.encode({"spec_identity": spec_identity, "event_token": token, "actor": "a"}))


def seam():
    return science_root._log_seam()


def admit(root: Path, candidate: FrozenSpec, superseded: FrozenSpec) -> SuccessorAdmitted | SuccessorRefused:
    return admit_spec_successor(candidate, superseded, seam=seam(), root=root)
