"""Generate the cross-language claim-identity parity fixture (`science.claim.v2`). **Run by hand, never by tests.**

    uv run python tools/generate_claim_identity_fixture.py

The output is a **conformance oracle**, not a source of truth. `science.identity.v1`
and the base contract remain the normative sources; this file is what two
implementations compare against so that a divergence is caught as a divergence
rather than each side confirming its own arithmetic. Python bootstraps the bytes
because something has to; the artifact is then **reviewed and frozen**, and the
test suite only ever reads it. A fixture regenerated during a test run asserts
that the implementation agrees with itself.

Two decisions the reader should not have to reverse-engineer.

**The vector carries components, not just an expected projection.** Each row
holds the claim's parts, and both implementations must **build and project from
the parts**. A fixture whose only input were the projection would test
`science.identity.v1` parity while bypassing `π_claim` entirely — the shared
encoding would be covered and the shared *projection* would not, which is most of
what this fixture is for.

**The file is written pure-ASCII** (`ensure_ascii=True`). The vector deliberately
contains non-ASCII and combining-character referents, and an editor, a merge tool
or a copy-paste that normalized them would silently change what the fixture
asserts — which is exactly the class of bug it exists to catch. Escaped, the
bytes on disk cannot drift, and both languages' JSON parsers decode them
identically.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from beliefs.claim import Member, Qualifier, Referent, build_claim
from beliefs.contract import load_base_contract, load_domain_contract
from beliefs.contract.base import TAG_ENCODING
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_CONTRACT = REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"
DOMAIN_CONTRACT = REPO_ROOT / "fixtures" / "contracts" / "testing.yaml"
OUTPUT = REPO_ROOT / "fixtures" / "claim-identity-v2.json"

# One referent per binding kind the testing contract declares, so every binding
# kind reaches the vector: `entity` and `outcome` (release), `method` (scheme),
# `cohort` (dataset), `event` (selection), `product` (run-output) and
# `procedure-spec` (world-kind, through `within-model`).
GENE = Referent(sort="testing/entity", term="EX:gene-x")
OTHER_GENE = Referent(sort="testing/entity", term="EX:gene-z")
PRODUCT_GENE = Referent(sort="testing/entity", term="EX:gene-w")
CATALYST = Referent(sort="testing/entity", term="EX:catalyst-k")
OUTCOME = Referent(sort="testing/outcome", term="EX:outcome-y")
METHOD = Referent(sort="testing/method", term="EX:assay-q")
ADULTS = Referent(sort="testing/cohort", term="EX:adults")
HUMANS = Referent(sort="testing/cohort", term="EX:humans")
PRODUCT = Referent(sort="testing/product", term="EX:product-p")
MODEL = Referent(sort="testing/procedure-spec", term="procedure:" + "6" * 64)

# Written as escapes so this source file is pure ASCII too — the same reason the
# output is. `BETA` is a composed non-ASCII identifier; `CAFE_NFD` is `café` with
# a combining acute, which `science.identity.v1` normalizes to NFC **at encode
# time**. The projection therefore carries the decomposed form and the canonical
# bytes carry the composed one, which is precisely the divergence a second
# implementation is likely to get wrong by normalizing at parse time or not at
# all. Both need the wide identifier class `EX:.+`, so `BETA` is an `event` and
# `CAFE_NFD` a `cohort`.
BETA = Referent(sort="testing/event", term="EX:\u03b2-catenin")
CAFE_NFD = Referent(sort="testing/cohort", term="EX:cafe\u0301-cohort")

# Case 2a's ordering pair: a BMP member above the surrogate range (U+FF21,
# fullwidth A) and a supplementary-plane member (U+1F600). By code point the BMP
# member sorts first; by UTF-16 code unit the astral one does (its high surrogate
# is 0xD83D < 0xFF21). The canonical member key orders by code point, so an
# implementation comparing UTF-16 strings with `<` projects them reversed.
BMP_EVENT = Referent(sort="testing/event", term="EX:\uff21")
ASTRAL_EVENT = Referent(sort="testing/event", term="EX:\U0001f600")

Role = Referent | Sequence[Member]


@dataclass(frozen=True)
class Row:
    """One vector entry: what to build, and what it is for.

    `roles` is in the order the author wrote, members included: the fixture
    records that order in `claim`, and the projection records the canonical one.
    """

    name: str
    covers: str
    operator: str
    roles: Mapping[str, Role]
    layer: str
    form: str = "polar"
    polarity: str | None = None
    qualifiers: dict[str, Qualifier] = field(default_factory=dict)


CAUSE_EFFECT: Mapping[str, Role] = {"cause": GENE, "effect": OUTCOME}

VECTOR: list[Row] = [
    Row(
        name="affects-positive-causal",
        covers="form polar; polarity positive; layer causal; two one-roles; release-bound sorts; no qualifiers",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-negative-causal",
        covers="polarity negative",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        polarity="negative",
        layer="causal",
    ),
    Row(
        name="affects-unsigned-causal",
        covers="polarity unsigned: the operator has a sign and this claim asserts none",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        polarity="unsigned",
        layer="causal",
    ),
    Row(
        name="affects-null-statistical",
        covers='form "null"; polarity inapt on a sign-apt template; layer statistical',
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        form="null",
        polarity=None,
        layer="statistical",
    ),
    Row(
        name="affects-within-model",
        covers="the reserved within-model role; a world-kind-bound sort; distinct from affects-positive-causal",
        operator="testing/affects",
        roles={**CAUSE_EFFECT, "within-model": MODEL},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-generic-population",
        covers="quantifier generic; a claim-side qualifier; a dataset-bound restriction sort",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        qualifiers={"testing/population": Qualifier("generic", ADULTS)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-universal-population",
        covers="quantifier universal: kernel section 4.1's founding pair, second half",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        qualifiers={"testing/population": Qualifier("universal", HUMANS)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-existential-two-dimensions",
        covers="quantifier existential; two qualifier dimensions, so map-key order is observable",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        qualifiers={
            "testing/setting": Qualifier("existential", OTHER_GENE),
            "testing/population": Qualifier("universal", ADULTS),
        },
        polarity="negative",
        layer="causal",
    ),
    Row(
        name="affects-decomposed-restriction",
        covers="a restriction in NFD: the projection holds it decomposed, the canonical bytes hold it composed",
        operator="testing/affects",
        roles=CAUSE_EFFECT,
        qualifiers={"testing/population": Qualifier("generic", CAFE_NFD)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="promotes-bridge",
        covers="a bridging relation as the operator, over its template's roles; distinct from the template's claim",
        operator="testing/promotes",
        roles=CAUSE_EFFECT,
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="correlates-with-written-forward",
        covers="a size-2 many role without coefficients (parties), written in one member order",
        operator="testing/correlates-with",
        roles={"parties": (Member(GENE), Member(OUTCOME))},
        qualifiers={"testing/population": Qualifier("generic", ADULTS)},
        polarity="positive",
        layer="statistical",
    ),
    Row(
        name="correlates-with-written-reversed",
        covers="the same claim with its parties written in the other order: one identity",
        operator="testing/correlates-with",
        roles={"parties": (Member(OUTCOME), Member(GENE))},
        qualifiers={"testing/population": Qualifier("generic", ADULTS)},
        polarity="positive",
        layer="statistical",
    ),
    Row(
        name="correlates-event-product-non-ascii",
        covers="a non-ASCII referent (BETA); a selection-bound and a run-output-bound sort",
        operator="testing/correlates-with",
        roles={"parties": (Member(PRODUCT), Member(BETA))},
        polarity="negative",
        layer="statistical",
    ),
    Row(
        name="correlates-event-product-astral-bmp",
        covers="case 2a: a supplementary-plane and a BMP member project in code-point, not UTF-16, order",
        operator="testing/correlates-with",
        roles={"parties": (Member(ASTRAL_EVENT), Member(BMP_EVENT))},
        polarity="positive",
        layer="statistical",
    ),
    Row(
        name="transforms-structural",
        covers="polarity inapt on a sign-inapt template; layer structural; many roles with coefficients; "
        "an empty min-0 role (facilitators)",
        operator="testing/transforms",
        roles={
            "inputs": (Member(OTHER_GENE, 1), Member(GENE, 2)),
            "outputs": (Member(PRODUCT_GENE, 1),),
            "facilitators": (),
        },
        polarity=None,
        layer="structural",
    ),
    Row(
        name="transforms-facilitated-causal",
        covers="a non-empty coefficient-free member of a role on a coefficient template; a second layer",
        operator="testing/transforms",
        roles={
            "inputs": (Member(GENE, 1),),
            "outputs": (Member(PRODUCT_GENE, 3),),
            "facilitators": (Member(CATALYST),),
        },
        polarity=None,
        layer="causal",
    ),
    Row(
        name="measured-by-methodological",
        covers="layer methodological; a scheme-bound sort; a second sign-inapt template",
        operator="testing/measured-by",
        roles={"subject": GENE, "instrument": METHOD},
        polarity=None,
        layer="methodological",
    ),
]


def _referent(referent: Referent) -> dict[str, str]:
    return {"sort": referent.sort, "term": referent.term}


def _role(value: Role) -> object:
    """A role as written: a referent for a `one` role, a member list otherwise."""
    if isinstance(value, Referent):
        return _referent(value)
    return [{**_referent(member.referent), "coefficient": member.coefficient} for member in value]


def main() -> None:
    base = load_base_contract(BASE_CONTRACT)
    domain = load_domain_contract(DOMAIN_CONTRACT, base=base, predecessor=None)
    profile = compile_profile(base, [domain])

    rows = []
    for entry in VECTOR:
        claim = build_claim(
            profile,
            operator=entry.operator,
            roles=entry.roles,
            qualifiers=entry.qualifiers,
            form=entry.form,
            polarity=entry.polarity,
            layer=entry.layer,
        )
        projection = project_claim(claim)
        rows.append(
            {
                "name": entry.name,
                "covers": entry.covers,
                "claim": {
                    "operator": entry.operator,
                    "roles": {name: _role(value) for name, value in entry.roles.items()},
                    "qualifiers": {
                        dimension: {
                            "quantifier": qualifier.quantifier,
                            "restriction": _referent(qualifier.restriction),
                        }
                        for dimension, qualifier in entry.qualifiers.items()
                    },
                    "form": entry.form,
                    "polarity": entry.polarity,
                    "layer": entry.layer,
                },
                "projection": projection,
                "canonical_bytes": v1.encode(projection).decode("utf-8"),
                "digest": claim_identity(claim),
            }
        )

    document = {
        "fixture": "claim-identity",
        "note": (
            "A conformance oracle, frozen. Regenerate deliberately with "
            "tools/generate_claim_identity_fixture.py and review the diff; never regenerate during a test run. "
            "Each row carries the claim's components in the order the author wrote them, and an implementation "
            "must build and project from them; comparing against `projection` alone would bypass the projection "
            "this fixture exists to pin. A role is a referent object (arity one) or a member list (arity many); "
            "a null polarity is the authoring route's 'no sign to assert'."
        ),
        "claim_domain": CLAIM_DOMAIN,
        "identity_contract": TAG_ENCODING,
        "base_contract": "contracts/science/CONTRACT.yaml",
        "domain_contracts": ["fixtures/contracts/testing.yaml"],
        "profile_compiled_identity": profile.compiled_identity,
        "vector": rows,
    }
    OUTPUT.write_text(json.dumps(document, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} rows to {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
