"""Certification enumeration — the by-kind inventory.

The subject projection is specification §7.6's certification inventory: sorted
kinds, each carrying its sorted distinct refs, and the declared coverage. It is
location-free and resolution-free by construction — a captured certification
carries a kind and a ref, and the corpus it was found in is read from nowhere
here, so one ref certified in two covered corpora enters the inventory once and
without either corpus.
"""


def enumerate_certifications(capture):
    by_kind = {}
    for record in capture["records"]:
        certification = record["certification"]
        if certification is None:
            continue
        by_kind.setdefault(certification["kind"], set()).add(certification["ref"])
    return {
        "by_kind": [{"kind": kind, "refs": sorted(refs)} for kind, refs in sorted(by_kind.items())],
        "coverage": sorted(capture["coverage"]),
    }
