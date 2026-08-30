"""``π_claim`` and ``I_claim`` — the canonical projection and claim identity.

```text
π_claim(c)  =  ⟨ operator, args by slot, qualifiers by dimension, polarity, layer ⟩
I_claim(c)  =  H( tag_claim ‖ encode(π_claim(c)) )        under science.identity.v1
```

**Every position is an identifier** (§6.5). A symbol is what a term is *called*;
an identifier is what it *is*. No prose reaches here — `statement` left identity
for the reason kernel §4.1 gave for `title`, *"a field cannot be both
hand-editable prose and an identity input"* — and neither does anything a
contract declares.

**The projection takes a `Claim` and nothing else.** That signature is the whole
of M8: claim identity is independent of contract release and of compilation. A
`ProfileSpec` parameter here would make it possible to fold a contract release
into `π_claim`, at which point an ontology release forks every claim in the
corpus; and `ProfileSpec`'s own identity would be an identity authority, which is
`KIND_DESCRIPTORS`' defect one level up (§7.5). What moves when a contract behind
one of these identifiers is reinterpreted is `belief_input_digest`, on the other
channel entirely.

So the profile is where a claim is *typed*, and it is deliberately absent from
where a claim is *named*.
"""

from __future__ import annotations

from beliefs.claim import Claim
from beliefs.identity import v1

__all__ = ["CLAIM_DOMAIN", "claim_identity", "project_claim"]

CLAIM_DOMAIN = "science.claim.v1"
"""§6.5's `tag_claim`, domain-separated under `science.identity.v1`.

The version is the **projection's**, not the corpus's or the grammar's. A change
to π_claim's *shape* takes a new domain, so a v2 projection can never collide
with a v1 one. A later qualifier grammar that adds scope order (§6.4 rule 4) is
exactly such a change — and until one arrives, the flat fragment's claims keep
the identities they were written with, which is what rule 4 promises.
"""


def project_claim(claim: Claim) -> dict[str, object]:
    """Project a claim into its canonical form.

    Three choices here are load-bearing, and each is a place where the obvious
    alternative would be wrong:

    **Arguments emit `term`, never `sort`.** §6.5's table admits *"the referent
    identifier, in the sort's vocabulary"* — the sort is the context that
    admitted the term, not part of what the claim says. It is also
    contract-declared, so carrying it would put a declaration inside claim
    identity and let a re-declaration re-project stored claims, which is M8's
    prohibition arriving through the argument position.

    **Slots stay ordered; dimensions do not get ordered here.** `args` is a
    sequence because `ArgSort(op)` is positional and *"X affects Y"* is not *"Y
    affects X"*. The qualifier map is a map because `Dims(op)` is a set — and
    §6.5's *"sorted by dimension identifier"* is delivered by
    `science.identity.v1`, which sorts object keys at encode time. Sorting them
    again here would be a second, silent canonicalization that could drift from
    the encoder's.

    **The polarity position is always present** (§7.5), carrying the base
    contract's `sign_inapt_tag` for the unit inhabitant. The claim already holds
    the tag, so no contract field is consulted to decide the shape: `π_claim`'s
    arity is a function of the claim's own content — one entry per slot, one per
    present dimension, and one polarity, always.
    """
    return {
        "operator": claim.operator,
        "args": [referent.term for referent in claim.args],
        "qualifiers": {
            dimension: {"quantifier": qualifier.quantifier, "restriction": qualifier.restriction.term}
            for dimension, qualifier in claim.qualifiers.items()
        },
        "polarity": claim.polarity,
        "layer": claim.layer,
    }


def claim_identity(claim: Claim) -> str:
    """``I_claim`` — the identity a claim keeps across every ontology release."""
    return v1.digest(CLAIM_DOMAIN, project_claim(claim))
