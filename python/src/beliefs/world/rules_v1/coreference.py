"""Coreference reduction — sorted endpoint pair to balance and distinct count.

The subject projection is specification §7.6's coreference map. The reduction
is the world-address ruling §5.2's: a unit is a distinct
`(endpoints, stance, actor, grounds)`, the event token is deliberately outside
that key, and every unit carries weight ±1 regardless of who submitted it. So
exact duplicates — a retry, a re-import, a second submission of the same stance
on the same grounds — do not add weight, while one attester's genuinely
different grounds do.

Endpoints are sorted here rather than trusted as captured, so `{A, B}` is one
pair however either attestation was authored.

Every key member is compared in NFC, the form `science.identity.v1` digests
under, so the reduction and every identity here agree about which strings are
one string; the boundary refuses non-NFC text and this is the rule's own half
of the same agreement (slice 2 design §2 item 2).

The reduction stores no coverage and no edge state. Whether an edge is active
is a function of the world a query spans and of whether the receipt resolves
now, neither of which an immutable epoch can know.
"""

import unicodedata


def _nfc(value):
    return unicodedata.normalize("NFC", value)


def reduce_coreference(capture):
    units = {}
    for record in capture["records"]:
        attestation = record["coreference"]
        if attestation is None:
            continue
        endpoints = tuple(sorted(_nfc(endpoint) for endpoint in attestation["endpoints"]))
        if len(endpoints) != 2 or endpoints[0] == endpoints[1]:
            raise ValueError("a coreference attestation names two distinct endpoints")
        stance = attestation["stance"]
        if type(stance) is not int or stance not in (1, -1):
            raise ValueError("a coreference stance is +1 or -1")
        units.setdefault(endpoints, set()).add((stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"])))
    return {
        "pairs": [
            {
                "endpoints": [left, right],
                "balance": sum(stance for stance, _actor, _grounds in distinct),
                "distinct_key_count": len(distinct),
            }
            for (left, right), distinct in sorted(units.items())
        ]
    }
