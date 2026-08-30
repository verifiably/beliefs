"""Producer derivation — the producers map and its coverage.

The subject projection is specification §7.6's producer snapshot: sorted
`{"dataset": …, "runs": […]}` members and the sorted declared coverage. Every
`produces` edge in every captured record contributes its run under its dataset,
wherever that record was captured — a snapshot that stopped at the first corpus
would publish a dataset with fewer producers than the world holds. The same
edge contributed twice contributes once: an enumeration counts what exists, not
how many times it was seen.

Coverage is the declared stable `corpus_id` values, never captured states. That
is what makes this identity semantic: an entity that moves between two covered
corpora changes every captured state and leaves this projection alone.
"""


def derive_producer_snapshot(capture):
    producers = {}
    for record in capture["records"]:
        for dataset in record["produces"]:
            producers.setdefault(dataset, set()).add(record["address"])
    return {
        "producers": [
            {"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(producers.items())
        ],
        "coverage": sorted(capture["coverage"]),
    }
