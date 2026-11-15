"""The series reader reads only caller-selected, bounded, verified buffers."""

import pytest

from beliefs.holdings.records import StoreLocator, StoreTreeLocator, url_locator
from beliefs.identity import v1
from beliefs.tree import TreeMember, make_tree, object_path, tree_digest, tree_file_bytes

from .fixtures import STORE, Records, digest, held_file, objects


def test_missing_location_refuses():
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRefused

    ref, records, _, _ = held_file()
    with pytest.raises(SeriesRefused) as caught:
        load_series_object(ref, records=records, evidence=SeriesEvidence({}, {}), budget=ReadBudget())
    assert caught.value.code == "evidence-unavailable"


def test_explicit_location_and_same_buffer():
    from beliefs.series.codec import decode_series_object
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRefused

    ref, records, evidence, calls = held_file()
    captured = load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())
    assert decode_series_object(captured).format == "science.series-origins.v2"
    assert [path for path, _ in calls] == ["held.json"]
    with pytest.raises(SeriesRefused) as caught:
        load_series_object(ref, records=records, evidence=SeriesEvidence({}, evidence.locations), budget=ReadBudget())
    assert caught.value.code == "evidence-unavailable"
    with pytest.raises(SeriesRefused):
        SeriesEvidence({}, {ref: url_locator("https://example.org/data")})  # pyright: ignore[reportArgumentType]
    with pytest.raises(SeriesRefused) as caught:
        load_series_object(
            ref,
            records=records,
            evidence=SeriesEvidence({STORE: lambda p, n: b"changed"}, evidence.locations),
            budget=ReadBudget(),
        )
    assert caught.value.code == "invalid-series"
    records.nodes.clear()
    from beliefs.errors import DependencyNotHeld

    with pytest.raises(DependencyNotHeld):
        load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())


def test_tree_member_manifest_size_digest_and_location():
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRef, SeriesRefused

    data = v1.encode(objects()[2])
    tree = make_tree([TreeMember("nested/origins.json", digest(data), len(data))])
    manifest = tree_file_bytes(tree)
    records = Records()
    ref = SeriesRef(records.dataset(tree_digest(tree)), tree_digest(tree), "nested/origins.json")
    location = StoreTreeLocator(STORE, tree_digest(tree).split(":")[1])
    buffers = {object_path(tree_digest(tree)): manifest, object_path(digest(data)): data}
    evidence = SeriesEvidence({STORE: lambda p, n: buffers[p]}, {ref: location})
    assert load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget()) == data
    for changed in (b"bad manifest", b"x" * (16 * 1024 * 1024 + 1)):
        buffers[object_path(tree_digest(tree))] = changed
        with pytest.raises(SeriesRefused) as caught:
            load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())
        assert caught.value.code == "invalid-series"
    buffers[object_path(tree_digest(tree))] = manifest
    buffers[object_path(digest(data))] = b"wrong"
    with pytest.raises(SeriesRefused):
        load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())
    buffers.pop(object_path(tree_digest(tree)))
    with pytest.raises(SeriesRefused) as caught:
        load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())
    assert caught.value.code == "evidence-unavailable"
    with pytest.raises(SeriesRefused):
        load_series_object(
            ref,
            records=records,
            evidence=SeriesEvidence(evidence.stores, {ref: StoreLocator(STORE, "file")}),
            budget=ReadBudget(),
        )


def test_tree_member_declared_size_is_checked():
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRef, SeriesRefused

    data = b"bytes"
    tree = make_tree([TreeMember("file", digest(data), 99)])
    records = Records()
    ref = SeriesRef(records.dataset(tree_digest(tree)), tree_digest(tree), "file")
    buffers = {object_path(tree_digest(tree)): tree_file_bytes(tree), object_path(digest(data)): data}
    evidence = SeriesEvidence(
        {STORE: lambda p, n: buffers[p]}, {ref: StoreTreeLocator(STORE, tree_digest(tree).split(":")[1])}
    )
    with pytest.raises(SeriesRefused):
        load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())


def test_resource_limits_are_cumulative():
    from beliefs.series.evidence import ReadBudget, load_series_object
    from beliefs.series.types import SeriesRefused

    # Repeated reads count actual bytes, although they locate only one object.
    ref, records, evidence, _ = held_file(b"x" * (16 * 1024 * 1024))
    budget = ReadBudget()
    for _ in range(4):
        assert len(load_series_object(ref, records=records, evidence=evidence, budget=budget)) == 16 * 1024 * 1024
    with pytest.raises(SeriesRefused):
        load_series_object(ref, records=records, evidence=evidence, budget=budget)
    ref, records, evidence, _ = held_file(b"x" * (16 * 1024 * 1024 + 1))
    with pytest.raises(SeriesRefused):
        load_series_object(ref, records=records, evidence=evidence, budget=ReadBudget())


def test_located_object_limit_includes_manifests():
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRef, SeriesRefused

    records = Records()
    refs = []
    buffers = {}
    locations = {}
    for i in range(257):
        data = str(i).encode()
        ref = SeriesRef(records.dataset(digest(data)), digest(data))
        refs.append(ref)
        buffers[str(i)] = data
        locations[ref] = StoreLocator(STORE, str(i))
    evidence = SeriesEvidence({STORE: lambda p, n: buffers[p]}, locations)
    budget = ReadBudget()
    for ref in refs[:256]:
        load_series_object(ref, records=records, evidence=evidence, budget=budget)
    with pytest.raises(SeriesRefused):
        load_series_object(refs[256], records=records, evidence=evidence, budget=budget)


def test_registered_store_read_pins_and_rejects_symlinks(certified_work):
    from authority import FULL

    from beliefs.root import holdings_seam, init_store_root, open_series_store
    from beliefs.series.types import SeriesRefused

    root = certified_work / "series-store"
    store_id = init_store_root(root, authority=FULL)
    holdings_seam().store_write(root, "nested/value", b"original", "f" * 64)
    with open_series_store(root, store_id=store_id) as read:
        captured = read("nested/value", 100)
        assert captured == b"original"
        (root / "nested/value").write_bytes(b"replacement")
        assert captured == b"original"
        (root / "escape").symlink_to(root / "nested", target_is_directory=True)
        with pytest.raises(SeriesRefused):
            read("escape/value", 100)
        with pytest.raises(SeriesRefused):
            read("nested/value", 2)
    with pytest.raises(SeriesRefused):
        read("nested/value", 100)
    with pytest.raises(SeriesRefused), open_series_store(root, store_id="b" * 32):
        pytest.fail("foreign store opened")


def test_graph_depth_and_cycles_share_one_budget():
    from contextlib import ExitStack

    from beliefs.series.evidence import ReadBudget
    from beliefs.series.types import SeriesRef, SeriesRefused

    refs = [SeriesRef("dataset:sha256:" + f"{i:064x}", "sha256:" + f"{i:064x}") for i in range(33)]
    budget = ReadBudget()
    with ExitStack() as stack:
        for ref in refs[:32]:
            stack.enter_context(budget.enter(ref))
        with pytest.raises(SeriesRefused, match="depth"):
            stack.enter_context(budget.enter(refs[32]))
    with budget.enter(refs[0]), pytest.raises(SeriesRefused, match="cycle"), budget.enter(refs[0]):
        pytest.fail("cycle entered")


def test_manifest_bytes_and_objects_share_the_budget():
    from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
    from beliefs.series.types import SeriesRef, SeriesRefused

    records = Records()
    buffers = {digest(str(i).encode()): str(i).encode() for i in range(256)}
    tree = make_tree([TreeMember(f"f{i:03}", digest(str(i).encode()), len(str(i))) for i in range(256)])
    tree_ref = tree_digest(tree)
    data_id = records.dataset(tree_ref)
    buffers[tree_ref] = tree_file_bytes(tree)
    by_path = {object_path(key): value for key, value in buffers.items()}
    refs = [SeriesRef(data_id, tree_ref, row.path) for row in tree.members]
    evidence = SeriesEvidence(
        {STORE: lambda p, n: by_path[p]}, {ref: StoreTreeLocator(STORE, tree_ref.split(":")[1]) for ref in refs}
    )
    budget = ReadBudget()
    for ref in refs[:255]:
        load_series_object(ref, records=records, evidence=evidence, budget=budget)
    with pytest.raises(SeriesRefused, match="256"):
        load_series_object(refs[255], records=records, evidence=evidence, budget=budget)
    data = b"x" * (16 * 1024 * 1024)
    tree = make_tree([TreeMember("file", digest(data), len(data))])
    ref = SeriesRef(records.dataset(tree_digest(tree)), tree_digest(tree), "file")
    by_path = {object_path(tree_digest(tree)): tree_file_bytes(tree), object_path(digest(data)): data}
    evidence = SeriesEvidence(
        {STORE: lambda p, n: by_path[p]}, {ref: StoreTreeLocator(STORE, tree_digest(tree).split(":")[1])}
    )
    budget = ReadBudget()
    for _ in range(3):
        load_series_object(ref, records=records, evidence=evidence, budget=budget)
    with pytest.raises(SeriesRefused):
        load_series_object(ref, records=records, evidence=evidence, budget=budget)
