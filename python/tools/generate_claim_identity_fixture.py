"""Generate M10's cross-language parity fixture. **Run by hand, never by tests.**

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
what M10 is for.

**The file is written pure-ASCII** (`ensure_ascii=True`). The vector deliberately
contains non-ASCII and combining-character referents, and an editor, a merge tool
or a copy-paste that normalized them would silently change what the fixture
asserts — which is exactly the class of bug it exists to catch. Escaped, the
bytes on disk cannot drift, and both languages' JSON parsers decode them
identically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import load_base_contract, load_domain_contract
from beliefs.contract.base import TAG_ENCODING
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_CONTRACT = REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"
DOMAIN_CONTRACT = REPO_ROOT / "fixtures" / "contracts" / "testing.yaml"
OUTPUT = REPO_ROOT / "fixtures" / "claim-identity-v1.json"

GENE = Referent(sort="testing/entity", term="EX:gene-x")
OTHER_GENE = Referent(sort="testing/entity", term="EX:gene-z")
OUTCOME = Referent(sort="testing/outcome", term="EX:outcome-y")
METHOD = Referent(sort="testing/method", term="EX:assay-q")
ADULTS = Referent(sort="testing/cohort", term="EX:adults")
HUMANS = Referent(sort="testing/cohort", term="EX:humans")

# Written as escapes so this source file is pure ASCII too — the same reason the
# output is. `BETA` is a composed non-ASCII identifier; `CAFE_NFD` is `café` with
# a combining acute, which `science.identity.v1` normalizes to NFC **at encode
# time**. The projection therefore carries the decomposed form and the canonical
# bytes carry the composed one, which is precisely the divergence a second
# implementation is likely to get wrong by normalizing at parse time or not at
# all.
BETA = Referent(sort="testing/entity", term="EX:\u03b2-catenin")
CAFE_NFD = Referent(sort="testing/cohort", term="EX:cafe\u0301-cohort")


@dataclass(frozen=True)
class Row:
    """One vector entry: what to build, and what it is for."""

    name: str
    covers: str
    operator: str
    args: tuple[Referent, ...]
    layer: str
    polarity: str | None = None
    qualifiers: dict[str, Qualifier] = field(default_factory=dict)


VECTOR: list[Row] = [
    Row(
        name="affects-positive-causal",
        covers="polarity positive; layer causal; no qualifiers",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-negative-causal",
        covers="polarity negative",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        polarity="negative",
        layer="causal",
    ),
    Row(
        name="affects-unsigned-causal",
        covers="polarity unsigned — the operator has a sign and this claim asserts none",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        polarity="unsigned",
        layer="causal",
    ),
    Row(
        name="subtype-of-inapt-structural",
        covers="polarity inapt; layer structural; the unit inhabitant is supplied by the constructor",
        operator="testing/subtype-of",
        args=(GENE, OTHER_GENE),
        polarity=None,
        layer="structural",
    ),
    Row(
        name="affects-generic-population",
        covers="quantifier generic",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        qualifiers={"testing/population": Qualifier("generic", ADULTS)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-universal-population",
        covers="quantifier universal — kernel §4.1's founding pair, second half",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        qualifiers={"testing/population": Qualifier("universal", HUMANS)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="affects-existential-population",
        covers="quantifier existential",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        qualifiers={"testing/population": Qualifier("existential", ADULTS)},
        polarity="positive",
        layer="causal",
    ),
    Row(
        name="correlates-with-statistical",
        covers="layer statistical",
        operator="testing/correlates-with",
        args=(GENE, OUTCOME),
        qualifiers={"testing/population": Qualifier("generic", ADULTS)},
        polarity="positive",
        layer="statistical",
    ),
    Row(
        name="measured-by-methodological",
        covers="layer methodological; a second sign-inapt operator; a third argument sort",
        operator="testing/measured-by",
        args=(OUTCOME, METHOD),
        qualifiers={"testing/setting": Qualifier("generic", GENE)},
        polarity=None,
        layer="methodological",
    ),
    Row(
        name="affects-two-dimensions-non-ascii",
        covers="two qualifier dimensions, so map-key order is observable; a non-ASCII referent identifier",
        operator="testing/affects",
        args=(BETA, OUTCOME),
        qualifiers={
            "testing/setting": Qualifier("existential", BETA),
            "testing/population": Qualifier("universal", ADULTS),
        },
        polarity="negative",
        layer="causal",
    ),
    Row(
        name="affects-decomposed-referent",
        covers="a referent in NFD — the projection holds it decomposed, the canonical bytes hold it composed",
        operator="testing/affects",
        args=(GENE, OUTCOME),
        qualifiers={"testing/population": Qualifier("generic", CAFE_NFD)},
        polarity="positive",
        layer="causal",
    ),
]


def _referent(referent: Referent) -> dict[str, str]:
    return {"sort": referent.sort, "term": referent.term}


def main() -> None:
    base = load_base_contract(BASE_CONTRACT)
    domain = load_domain_contract(DOMAIN_CONTRACT, base=base, predecessor=None)
    profile = compile_profile(base, [domain])

    rows = []
    for entry in VECTOR:
        claim = build_claim(
            profile,
            operator=entry.operator,
            args=entry.args,
            qualifiers=entry.qualifiers,
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
                    "args": [_referent(referent) for referent in entry.args],
                    "qualifiers": {
                        dimension: {
                            "quantifier": qualifier.quantifier,
                            "restriction": _referent(qualifier.restriction),
                        }
                        for dimension, qualifier in entry.qualifiers.items()
                    },
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
            "Each row carries the claim's components, and an implementation must build and project from them "
            "— comparing against `projection` alone would bypass the projection this fixture exists to pin."
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
