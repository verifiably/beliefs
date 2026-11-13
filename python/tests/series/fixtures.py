"""Held synthetic buffers and explicit records, with no ambient storage."""

from hashlib import sha256

from beliefs import stored
from beliefs.identity import v1

STORE = "a" * 32


def digest(data):
    return "sha256:" + sha256(data).hexdigest()


def ref_value(data):
    node = stored.dataset_node(title="Synthetic series", resources=({"name": "data", "digest": digest(data)},))
    return {"dataset": node.id, "resource": digest(data)}


def objects():
    ref = ref_value(b"table")
    coordinates = {
        "quantity_kind": "testing/abundance",
        "unit": "testing/count",
        "value_type": "level",
        "transformation": "testing/identity",
    }
    return (
        {"format": "science.series-view.v1", "table": ref, "channel": "signal", "selection": [0, 1]},
        {
            "format": "science.series-table.v1",
            "axis": {"kind": "index"},
            "coordinates": [0, 1],
            "channels": {"signal": {"coordinates": coordinates, "values": ["1", "2"]}},
        },
        {"format": "science.series-origins.v1", "origins": {"zero": {"label": "Sample zero"}}},
        {
            "format": "science.series-anchors.v1",
            "axis": {
                "kind": "elapsed",
                "unit": "testing/second",
                "origin": {"source": ref, "key": "zero"},
                "basis": "synthetic",
            },
            "rule": "classification-rule:" + "b" * 64,
            "rows": [{"key": "first", "class": {"sort": "testing/event", "term": "onset"}, "coordinate": "0"}],
        },
    )


class Records:
    def __init__(self):
        self.nodes = {}

    def holds(self, id):
        return id in self.nodes

    def read(self, id):
        return self.nodes[id]

    def retraction_in_force(self, id):
        return False

    def observation_held(self, digest):
        return True

    def crosswalks(self, a, b):
        return ()

    def dataset(self, *digests):
        node = stored.dataset_node(
            title="Synthetic", resources=tuple({"name": str(i), "digest": d} for i, d in enumerate(digests))
        )
        self.nodes[node.id] = node
        return node.id


def held_file(data=None):
    from beliefs.holdings.records import StoreLocator
    from beliefs.series.evidence import SeriesEvidence
    from beliefs.series.types import SeriesRef

    if data is None:
        data = v1.encode(objects()[2])
    records = Records()
    ref = SeriesRef(records.dataset(digest(data)), digest(data))
    calls = []

    def read(path, limit):
        calls.append((path, limit))
        return data

    return ref, records, SeriesEvidence({STORE: read}, {ref: StoreLocator(STORE, "held.json")}), calls
