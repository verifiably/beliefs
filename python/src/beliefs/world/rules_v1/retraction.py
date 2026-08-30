"""Retraction enumeration — every found retraction with its resolution.

The subject projection is specification §7.6's retraction enumeration: each
found retraction address stays attached to its resolution, the pairs are
sorted, and the declared coverage travels with them.

The enumeration visits **every** retraction record rather than starting from
one target, which is how it generalizes the record reading `standing_in_local_view`
already does. It is therefore keyed by the retraction, never by the target:
several retractions may name one target, and keying by target would publish one
of them and silently drop the rest. Grouping by target is the
retraction-discovery map's job, and it is a different member.

A ref found twice with the same resolution is one finding; the same ref with
two resolutions is two, because dropping either would be an enumeration
deciding which resolution it preferred.
"""


def enumerate_retractions(capture):
    found = set()
    for record in capture["records"]:
        retraction = record["retraction"]
        if retraction is None:
            continue
        found.add((record["address"], retraction["resolution"]))
    return {
        "found": [[ref, resolution] for ref, resolution in sorted(found)],
        "coverage": sorted(capture["coverage"]),
    }
