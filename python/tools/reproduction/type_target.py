"""Step 2: build_claim over the target and mint the proposition record.

Before the mint, one pure measurement: `build_claim` under the modal-sorted
vocabulary, which excludes the target's concept→protein pair by its stated
rule. Its refusal is recorded as the answer to "what `build_claim` refused
and why" (design §6, the fourth question); nothing is minted from it.
"""

from __future__ import annotations

import sys
import time

import yaml

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.errors import ClaimError
from beliefs.projection import claim_identity, project_claim
from reproduction import findings, paths, state, vocabulary, world


def referent(term: str, plan: dict) -> Referent:
    kind, colon, tail = term.partition(":")
    if not colon or not kind or not tail:
        raise ClaimError(f"term {term!r} carries no `<kind>:` prefix")
    if kind not in plan["sorts"]:
        raise ClaimError(f"term {term!r}: kind prefix {kind!r} maps to no sort in the plan")
    return Referent(sort=plan["sorts"][kind], term=term)


def typed(target: dict, profile, plan: dict):
    return build_claim(
        profile,
        operator=plan["operators"][target["predicate"]],
        args=(referent(target["subject"], plan), referent(target["object"], plan)),
        layer=plan["layers"][target["claim_layer"]],
        polarity=plan["polarities"][target["polarity"]],
    )


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    # The measurement: the modal-sorted vocabulary, no mint.
    try:
        typed(target, vocabulary.profile(vocabulary.MODAL_SORTED), vocabulary.plan(vocabulary.MODAL_SORTED))
        modal = "typed (unexpected: the modal rule assigns `affects` [concept, concept])"
    except (ClaimError, KeyError) as refused:
        modal = f"{type(refused).__name__}: {refused}"
    findings.record(
        2,
        "corpus-work",
        f"under mm30-modal-sorted, build_claim on the target: {modal}",
        filed="record §2 / §5 (the fourth question); the exercise types under the unsorted vocabulary",
    )
    print(f"modal-sorted measurement: {modal}")
    # The mint, under the exercise's vocabulary.
    plan = vocabulary.plan()
    started = time.monotonic()
    try:
        claim = typed(target, vocabulary.profile(), plan)
    except (ClaimError, KeyError) as refused:
        findings.record(2, "corpus-work", f"build_claim refused the target: {type(refused).__name__}: {refused}")
        print(f"REFUSED at build_claim: {refused}")
        return 2
    slug = target["proposition_id"].split(":", 1)[1]
    minted = world.open_writer().add(
        stored.proposition_node(
            slug,
            title=target["proposition_id"],
            claim=project_claim(claim),
            display_statement=f"{target['subject']} {target['predicate']} {target['object']}",
        )
    )
    state.save(
        proposition_ref=minted.id,
        claim_identity=claim_identity(claim),
        typing_seconds=round(time.monotonic() - started, 1),
    )
    print(f"minted {minted.id}; claim identity {claim_identity(claim)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
