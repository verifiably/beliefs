"""``π_claim`` and ``I_claim`` — the canonical projection and claim identity.

```text
π_claim(c)  =  ⟨ operator, roles by name, qualifiers by dimension, form, polarity, layer ⟩
I_claim(c)  =  H( tag_claim ‖ encode(π_claim(c)) )        under science.identity.v1
```

**Every leaf is an identifier, a tag or a member coefficient**. A symbol is what
a term is *called*; an identifier is what it *is*. No prose reaches here —
`statement` left identity for the reason `title` did, *"a field cannot be both
hand-editable prose and an identity input"* — and neither does anything a
contract declares: a referent carries its sort's *identifier*, never the sort's
binding, so re-declaring a binding re-projects nothing.

**The projection takes a `Claim` and nothing else.** That signature is the whole
guarantee: claim identity is independent of contract release and of compilation. A
`ProfileSpec` parameter here would make it possible to fold a contract release
into `π_claim`, at which point an ontology release forks every claim in the
corpus; and `ProfileSpec`'s own identity would be an identity authority, which is
`KIND_DESCRIPTORS`' defect one level up. What moves when a contract behind
one of these identifiers is reinterpreted is `belief_input_digest`, on the other
channel entirely.

So the profile is where a claim is *typed*, and it is deliberately absent from
where a claim is *named*.
"""

from __future__ import annotations

from beliefs.claim import Claim, Member, Referent
from beliefs.identity import v1

__all__ = ["CLAIM_DOMAIN", "claim_identity", "project_claim"]

CLAIM_DOMAIN = "science.claim.v2"
"""The `tag_claim` domain, separated under `science.identity.v1`.

The version is the **projection's**, not the corpus's or the grammar's. A change
to π_claim's *shape* takes a new domain, so a v2 projection can never collide
with a v1 one: v2 replaced positional `args` (terms only) with roles by name,
every referent carrying its sort, and added the form position. There is no
v1-to-v2 mapping; corpora are recreated.
"""


def project_claim(claim: Claim) -> dict[str, object]:
    """Project a claim into its canonical form.

    Four choices here are load-bearing, and each is a place where the obvious
    alternative would be wrong:

    **Every referent emits `sort` and `term`.** Under templates the operator and
    the terms no longer fix the sorts: one term over a gene and over a protein
    would otherwise collide. The sort enters as its *identifier*; its binding is
    the contract's and never enters.

    **Roles are a map by name, never a sequence.** Role names are the
    template's, and `science.identity.v1` sorts object keys at encode time, so
    declaration order cannot reach the identity. A `one` role projects as a
    referent object; a `many` role as its members in canonical member-key order
    (the claim already holds them so), each carrying `coefficient` even when it
    is 1, and an empty role as `[]`.

    **Dimensions do not get ordered here.** The qualifier map is a map, and the
    projection's *"sorted by dimension identifier"* is delivered by the
    encoder. Sorting them again here would be a second, silent canonicalization
    that could drift from the encoder's.

    **The form and polarity positions are always present**, the polarity
    carrying the base contract's `sign_inapt_tag` where there is no sign. The
    claim already holds the tag, so no contract field is consulted to decide the
    shape.
    """
    return {
        "operator": claim.operator,
        "roles": {name: _project_role(value) for name, value in claim.roles.items()},
        "qualifiers": {
            dimension: {"quantifier": qualifier.quantifier, "restriction": _project_referent(qualifier.restriction)}
            for dimension, qualifier in claim.qualifiers.items()
        },
        "form": claim.form,
        "polarity": claim.polarity,
        "layer": claim.layer,
    }


def claim_identity(claim: Claim) -> str:
    """``I_claim`` — the identity a claim keeps across every ontology release."""
    return v1.digest(CLAIM_DOMAIN, project_claim(claim))


def _project_referent(referent: Referent) -> dict[str, object]:
    return {"sort": referent.sort, "term": referent.term}


def _project_member(member: Member) -> dict[str, object]:
    return {**_project_referent(member.referent), "coefficient": member.coefficient}


def _project_role(value: Referent | tuple[Member, ...]) -> object:
    if isinstance(value, Referent):
        return _project_referent(value)
    return [_project_member(member) for member in value]
