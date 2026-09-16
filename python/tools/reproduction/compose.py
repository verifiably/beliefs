"""Step 11: mint the h1-prognosis spine and compose the fragment (composite-claims design §9)."""

from __future__ import annotations

import sys

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeError, CompositeNode, build_composite
from beliefs.projection import project_claim
from reproduction import findings, state, vocabulary, world

SPINE_SLUG = "protein-phf19-affects-concept-overall-survival"
COMPOSITE_SLUG = "h1-prognosis-fragment"


def main() -> int:
    st = state.load()
    profile = vocabulary.profile()
    writer = world.open_writer()
    spine_claim = build_claim(
        profile,
        operator="mm30/affects-molecular-entity-concept",
        args=(Referent("biology/molecular-entity", "protein:PHF19"), Referent("mm30/concept", "concept:overall-survival")),
        layer="causal",
        polarity="negative",
    )
    spine = writer.add(
        stored.proposition_node(
            SPINE_SLUG,
            title="PHF19 expression affects overall survival (negatively)",
            claim=project_claim(spine_claim),
            display_statement="Higher PHF19 expression predicts shorter overall survival — inquiry 0001-prognosis's spine, minted here with no evidence.",
        )
    )
    nodes = [
        CompositeNode("mm30/concept", "concept:disease-stage"),
        CompositeNode("biology/molecular-entity", "protein:PHF19"),
        CompositeNode("mm30/concept", "concept:overall-survival"),
    ]
    try:
        value, receipt = build_composite(
            profile, writer.read_view, shape="dag", nodes=nodes, members=[st["proposition_ref"], spine.id],
            snapshot=vocabulary.snapshot(), slug=COMPOSITE_SLUG,
        )
    except CompositeError as refused:
        findings.record(11, "design-gap" if refused.code == "composite-node-not-member" else "defect", f"build_composite refused: {refused}", filed="composite-claims design §9")
        state.save(spine_ref=spine.id, composite_refusal=f"{refused.code}: {refused}")
        print(f"REFUSED: {refused}")
        return 2
    minted = writer.add(stored.composite_node(value, title="h1-prognosis fragment: disease stage → PHF19 ⊣ overall survival"))
    state.save(
        spine_ref=spine.id,
        composite_ref=minted.id,
        composite_identity=value.identity,
        composite_receipt={label: outcome.value for label, outcome in receipt.outcomes.items()},
    )
    outcomes = state.load()["composite_receipt"]
    # The reproduction's snapshot consults concepts, levels, measures and identifications and leaves
    # `biology/molecular-entity` unconsulted, so PHF19 — node:0, since "biology" sorts before "mm30" —
    # resolves `not-consulted`, and the two concepts `member` (design §4.1: a check not performed is not a finding).
    expected = {"node:0": "not-consulted", "node:1": "member", "node:2": "member"}
    findings.record(11, "closed" if outcomes == expected else "defect", f"composed {minted.id} ({value.identity[:16]}…) over {len(value.edges)} edges; node outcomes {outcomes} (expected {expected})")
    print(f"composed {minted.id}; edges {[(e.cause.term, e.effect.term, e.sign) for e in value.edges]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
