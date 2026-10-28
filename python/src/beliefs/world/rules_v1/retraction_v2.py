"""Retraction enumeration v2 — every found retraction with its world resolution.

The subject projection is specification §7.6's retraction enumeration, exactly
as v1 emits it: each found retraction address attached to one resolution, the
pairs sorted, the declared coverage beside them. What changes is where the
resolution comes from (overlapping-publications design §4.5, cut 48). v1 copies
each captured record's per-corpus resolution, so one retraction held in two
corpora whose correction graphs differ is enumerated twice. This rule folds
standing once over the whole capture: a retraction's resolution is the standing
of one record in the one graph every covered corpus contributes to.

It reads the `science.rule-input.v2` input, which carries each retraction's
target arm. A counter edge exists only for a node-arm target that resolves over
the capture's live and deprecated addresses — exactly `corpus.retraction_standing`'s
edge rule, reimplemented here because rule content may share no code. Route-arm
and snapshot-arm retractions are vertices. The per-corpus resolution in the input
is not read.

Two inputs are not worlds and raise: one live or deprecated address claimed by
records of distinct uids, and a counter cycle. Both are refused earlier by the
kernel (the address map, and the capture's own cycle check), so a raise here is
defensive; the kernel wraps it as a nonconformant run.
"""


def enumerate_retractions_v2(capture):
    records = capture["records"]
    uid_of = {}
    for record in records:
        for key in (record["address"], *record["deprecated_ids"]):
            held = uid_of.setdefault(key, record["uid"])
            if held != record["uid"]:
                raise ValueError(f"{key!r} is claimed by records of distinct uids; this capture is not a world")
    live_of = {}
    for record in records:
        live_of[record["uid"]] = record["address"]
    targets = {}
    for record in records:
        retraction = record["retraction"]
        if retraction is None:
            continue
        target = retraction["target"] if retraction["arm"] == "node" else None
        targets[record["address"]] = target
    graph = {}
    for address, target in targets.items():
        if target is None:
            continue
        uid = uid_of.get(target)
        if uid is not None:
            graph.setdefault(live_of[uid], set()).add(address)
    standing = {}

    def standing_of(address, path):
        if address in standing:
            return standing[address]
        if address in path:
            raise ValueError(f"retraction cycle through {address!r}")
        value = not any(standing_of(retraction, path | {address}) for retraction in sorted(graph.get(address, ())))
        standing[address] = value
        return value

    found = set()
    for address in targets:
        found.add((address, "upheld" if standing_of(address, frozenset()) else "overturned"))
    return {
        "found": [[ref, resolution] for ref, resolution in sorted(found)],
        "coverage": sorted(capture["coverage"]),
    }
