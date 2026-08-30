"""What counts as an identifier, and where canonical form is required.

Several boundaries admit free-form identifier text — a `Referent`'s sort and
term, a `VocabularyBinding`'s fields, a `ResolutionSnapshot`'s members, a wire
value's tags — and values admitted at one are compared against values admitted at
another. The predicates live here, once, so that agreement is structural rather
than remembered.

**`science.identity.v1` normalizes strings to NFC at encode time**, so `"é"` and
`"é"` are one identifier to every digest in this system and two distinct
strings to Python. That split is the whole subject of this module: string
equality and encoded equality are different relations, and each boundary has to
say which one it means.

**The claim layer preserves what the author wrote.** A `Referent` is *not*
required to be canonical, and requiring it would be a defect rather than a
tightening: normalizing at parse time — or refusing what only encode-time
normalization would fold — is precisely the second-implementation divergence the
`affects-decomposed-referent` parity row was built to catch, and this
implementation would then be the one it catches. So `not_an_identifier` is
non-emptiness and stringness, and nothing about form.

**The contract layer requires canonical form, because there is nothing to
preserve and a collision to prevent.** A `VocabularyBinding`'s fields are not a
π_claim position; they are the input to a projection two identities are taken
over. Two bindings differing only in normalization are two dictionary keys and
one encoded binding, which is the same collision D §5's sum already had to be
closed against, arriving through the text instead of the shape. Refusing is also
the contract layer's own discipline — D5's *"refused at load, never ignored"* —
rather than a rule imported from elsewhere.

**Comparison normalizes, because it must agree with `I_claim`.** A snapshot
stores canonical members and `canonical()` is applied to whatever it is asked
about, so membership is decided under the same equivalence the identity uses.
Storing canonically and comparing canonically are both needed: without the first
a vocabulary can hold two members that encode alike, and without the second a
legitimately decomposed claim term reports `not-member` against a vocabulary that
holds it.
"""

from __future__ import annotations

import unicodedata

__all__ = ["canonical", "not_a_canonical_identifier", "not_an_identifier"]


def canonical(value: str) -> str:
    """The form `science.identity.v1` compares under. Every comparison of
    identifier text against stored identifier text goes through this."""
    return unicodedata.normalize("NFC", value)


def not_an_identifier(value: object) -> str | None:
    """Say why ``value`` is not an identifier, or ``None`` if it is one.

    Says nothing about normalization — see the module docstring for why the claim
    layer must not care.
    """
    if not isinstance(value, str):
        return f"{value!r} is a {type(value).__name__}, not a string"
    if not value:
        return "the empty string is not an identifier"
    return None


def not_a_canonical_identifier(value: object) -> str | None:
    """Say why ``value`` is not a canonical identifier, or ``None`` if it is one."""
    problem = not_an_identifier(value)
    if problem is not None:
        return problem
    assert isinstance(value, str)
    if canonical(value) != value:
        return (
            f"{value!r} is not in NFC. The encoding normalizes before digesting, so this string and its "
            "canonical form are one identifier to every digest here and two distinct keys to Python. Where "
            "the two disagree, a projection maps two values onto one encoding. Normalize it where it enters"
        )
    return None
