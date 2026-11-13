"""Held synthetic buffers and explicit records, with no ambient storage."""

from hashlib import sha256
from typing import Any, cast

from beliefs import stored
from beliefs.identity import v1

STORE = "a" * 32


def raw_object(data: bytes) -> dict[str, Any]:
    """Mutable JSON for deliberate fixture corruption; production decoding stays typed."""
    return cast(dict[str, Any], v1.decode(data))


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


def time_document():
    from time_roles_fixture import time_document as load_time

    return load_time()


def channel_coordinates():
    return {
        "quantity_kind": "testing/count",
        "unit": "testing/item",
        "value_type": "level",
        "transformation": "testing/identity",
    }


class SeriesCase:
    def __init__(self):
        self.records = Records()
        self.buffers = {}
        self.locations = {}

    def hold(self, value) -> dict[str, Any]:
        from beliefs.holdings.records import StoreLocator
        from beliefs.series.codec import series_ref_projection
        from beliefs.series.types import SeriesRef

        data = v1.encode(value)
        ref = SeriesRef(self.records.dataset(digest(data)), digest(data))
        path = digest(data).split(":")[1]
        self.buffers[path] = data
        self.locations[ref] = StoreLocator(STORE, path)
        return cast(dict[str, Any], series_ref_projection(ref))

    def evidence(self):
        from beliefs.series.evidence import SeriesEvidence

        return SeriesEvidence({STORE: lambda path, limit: self.buffers[path]}, self.locations)

    def origin(self):
        return {
            "source": self.hold({"format": "science.series-origins.v1", "origins": {"zero": {"label": "Sample zero"}}}),
            "key": "zero",
        }

    def procedure(self, **changes):
        from test_procedure import procedure

        from beliefs.procedure import Implementation

        node = stored.procedure_node(
            procedure(yields=(), implementation=Implementation("synthetic", "sha256:" + "c" * 64), **changes)
        )
        self.records.nodes[node.id] = node
        return node.id

    def table(self, coordinates, *, axis=None, support=None, values=None, channels=None):
        if axis is None:
            axis = {
                "kind": "elapsed",
                "unit": "si-brochure/second",
                "origin": self.origin(),
                "basis": "synthetic",
                "grid": {"kind": "regular", "spacing": "0.01", "rate": "100"},
            }
        table = {
            "format": "science.series-table.v1",
            "axis": axis,
            "coordinates": coordinates,
            "channels": channels
            or {"signal": {"coordinates": channel_coordinates(), "values": values or ["1"] * len(coordinates)}},
        }
        if support is not None:
            table["support"] = support
        return self.hold(table)

    def view(self, table, selection, **extra):
        return self.hold(
            {"format": "science.series-view.v1", "table": table, "channel": "signal", "selection": selection, **extra}
        )

    def read(self, ref, profile, roles):
        from beliefs.series.codec import series_ref_from_projection
        from beliefs.series.reader import _read_series_roots

        return _read_series_roots(
            (series_ref_from_projection(ref),),
            profile=profile,
            records=self.records,
            evidence=self.evidence(),
            time_roles=roles,
        )[0]

    def rewrite(self, ref, change):
        data = self.buffers[ref["resource"].split(":")[1]]
        value = raw_object(data)
        change(value)
        return self.hold(value)

    def hold_tree(self, values):
        from beliefs.holdings.records import StoreTreeLocator
        from beliefs.series.codec import series_ref_projection
        from beliefs.series.types import SeriesRef
        from beliefs.tree import TreeMember, make_tree, object_path, tree_digest, tree_file_bytes

        buffers = {path: v1.encode(value) for path, value in values.items()}
        tree = make_tree(TreeMember(path, digest(data), len(data)) for path, data in buffers.items())
        tree_ref = tree_digest(tree)
        dataset = self.records.dataset(tree_ref)
        self.buffers[object_path(tree_ref)] = tree_file_bytes(tree)
        result = {}
        for path, data in buffers.items():
            ref = SeriesRef(dataset, tree_ref, path)
            self.buffers[object_path(digest(data))] = data
            self.locations[ref] = StoreTreeLocator(STORE, tree_ref.split(":")[1])
            result[path] = series_ref_projection(ref)
        return result
