"""Caller-selected local reads with graph-wide bounds and buffer integrity."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias

from beliefs.dataset import dataset_address, declaration_from_facet
from beliefs.errors import DependencyNotHeld, ScienceError
from beliefs.holdings.records import StoreLocator, StoreTreeLocator
from beliefs.series.types import SeriesGraph, SeriesRef, SeriesRefused
from beliefs.tree import object_path, parse_tree_file

if TYPE_CHECKING:
    from beliefs.dependencies import HeldRecords

__all__ = [
    "ReadBudget",
    "SeriesEvidence",
    "SeriesStoreRead",
    "check_series_input_content",
    "load_series_object",
    "staged_evidence",
]

SeriesStoreRead: TypeAlias = Callable[[str, int], bytes]
_FILE_BYTES = 16 * 1024 * 1024
_GRAPH_BYTES = 64 * 1024 * 1024
_OBJECTS = 256
_DEPTH = 32


@dataclass(frozen=True)
class SeriesEvidence:
    stores: Mapping[str, SeriesStoreRead]
    locations: Mapping[SeriesRef, StoreLocator | StoreTreeLocator]

    def __post_init__(self) -> None:
        if any(
            not isinstance(key, SeriesRef) or type(value) not in (StoreLocator, StoreTreeLocator)
            for key, value in self.locations.items()
        ):
            raise SeriesRefused("invalid-series", "series evidence requires exact local store locations")
        if any(not isinstance(key, str) or not callable(value) for key, value in self.stores.items()):
            raise SeriesRefused("invalid-series", "series stores map ids to explicit read callables")
        object.__setattr__(self, "stores", MappingProxyType(dict(self.stores)))
        object.__setattr__(self, "locations", MappingProxyType(dict(self.locations)))


class ReadBudget:
    """One call's accounting, including repeated buffers and tree manifests."""

    def __init__(self) -> None:
        self._bytes = 0
        self._located: set[tuple[str, str]] = set()
        self._stack: list[SeriesRef] = []

    @contextmanager
    def enter(self, ref: SeriesRef) -> Iterator[None]:
        if len(self._stack) >= _DEPTH:
            raise SeriesRefused("invalid-series", "series graph exceeds depth 32")
        if ref in self._stack:
            raise SeriesRefused("invalid-series", "series graph contains a cycle")
        self._stack.append(ref)
        try:
            yield
        finally:
            self._stack.pop()

    def _read(self, store: str, path: str, read: SeriesStoreRead) -> bytes:
        identity = (store, path)
        if identity not in self._located and len(self._located) >= _OBJECTS:
            raise SeriesRefused("invalid-series", "series graph exceeds 256 located objects")
        self._located.add(identity)
        remaining = min(_FILE_BYTES, _GRAPH_BYTES - self._bytes)
        try:
            data = read(path, remaining)
        except SeriesRefused:
            raise
        except (OSError, KeyError) as exc:
            raise SeriesRefused("evidence-unavailable", "explicit local series source is unreadable") from exc
        if type(data) is not bytes or len(data) > remaining:
            raise SeriesRefused("invalid-series", "series buffer exceeds per-file or cumulative byte limit")
        self._bytes += len(data)
        return data


def _hash(data: bytes, digest: str, size: int | None = None) -> None:
    if sha256(data).hexdigest() != digest.split(":", 1)[1] or (size is not None and len(data) != size):
        raise SeriesRefused("invalid-series", "series buffer digest or size disagrees with its reference")


def load_series_object(ref: SeriesRef, *, records: HeldRecords, evidence: SeriesEvidence, budget: ReadBudget) -> bytes:
    """Return the very buffer verified here, never a path to reopen."""
    if type(ref) is not SeriesRef:
        raise SeriesRefused("invalid-series", "expected a SeriesRef")
    if not records.holds(ref.dataset):
        raise DependencyNotHeld(f"series dataset {ref.dataset} is not recorded")
    node = records.read(ref.dataset)
    try:
        facet = node.facets.get("dataset")
        if node.kind != "dataset" or node.id != ref.dataset or not isinstance(facet, Mapping):
            raise SeriesRefused("invalid-series", "series dataset record or facet disagrees")
        declaration = declaration_from_facet(facet)
        if dataset_address(declaration) != ref.dataset or ref.resource not in {r.digest for r in declaration.resources}:
            raise SeriesRefused("invalid-series", "series resource is not in the addressed dataset")
    except SeriesRefused:
        raise
    except ScienceError as exc:
        raise SeriesRefused("invalid-series", str(exc)) from exc
    location = evidence.locations.get(ref)
    if location is None or location.store_id not in evidence.stores:
        raise SeriesRefused("evidence-unavailable", "no explicit series location or authorized store reader")
    read = evidence.stores[location.store_id]
    if isinstance(location, StoreLocator):
        if ref.member is not None:
            raise SeriesRefused("invalid-series", "tree member requires a store-tree location")
        data = budget._read(location.store_id, location.relative_path, read)
        _hash(data, ref.resource)
        return data
    if ref.member is None or location.digest() != ref.resource:
        raise SeriesRefused("invalid-series", "store-tree location disagrees with series resource")
    manifest = budget._read(location.store_id, object_path(ref.resource), read)
    _hash(manifest, ref.resource)
    try:
        tree = parse_tree_file(manifest)
    except ScienceError as exc:
        raise SeriesRefused("invalid-series", f"invalid series tree manifest: {exc}") from exc
    member = next((row for row in tree.members if row.path == ref.member), None)
    if member is None:
        raise SeriesRefused("invalid-series", "series member is not in the referenced tree")
    data = budget._read(location.store_id, object_path(member.digest), read)
    _hash(data, member.digest, member.size)
    return data


def staged_evidence(
    graph: SeriesGraph,
    *,
    evidence: SeriesEvidence,
    inputs_root: Path,
    staged: Mapping[str, str | Mapping[str, str]],
    single_names: Mapping[str, str],
) -> SeriesEvidence:
    """Bind the selected locations to immutable buffers from this staged copy.

    Tree manifests remain explicitly supplied evidence. Their verified member
    paths are read in the staged tree; no locator or store authority is invented.
    """
    buffers: dict[tuple[str, str], bytes] = {}
    budget = ReadBudget()

    def capture(store, path, read):
        data = budget._read(store, path, read)
        key = (store, path)
        if key in buffers and buffers[key] != data:
            raise SeriesRefused("invalid-series", "staged copies disagree at one selected location")
        buffers[key] = data
        return data

    def local(path):
        def read(_name, limit):
            if path.is_symlink() or not path.is_file():
                raise SeriesRefused("evidence-unavailable", "staged series resource is not a regular file")
            with path.open("rb") as stream:
                return stream.read(limit + 1)

        return read

    for row in graph:
        ref = row.ref
        location = evidence.locations.get(ref)
        if location is None or location.store_id not in evidence.stores:
            raise SeriesRefused("evidence-unavailable", "series staged binding lacks its explicit location")
        entry = staged.get(ref.dataset)
        if isinstance(entry, str):
            names = [single_names[ref.dataset]] if entry == ref.resource else []
        elif isinstance(entry, Mapping):
            names = [name for name, digest in entry.items() if digest == ref.resource]
        else:
            names = []
        if not names:
            raise SeriesRefused("invalid-series", "series resource is not in the staged input digest map")
        if isinstance(location, StoreTreeLocator):
            manifest_path = object_path(ref.resource)
            manifest = capture(location.store_id, manifest_path, evidence.stores[location.store_id])
            _hash(manifest, ref.resource)
            tree = parse_tree_file(manifest)
            member = next((m for m in tree.members if m.path == ref.member), None)
            if member is None:
                raise SeriesRefused("invalid-series", "series member is absent from the explicit manifest")
            for name in names:
                capture(location.store_id, object_path(member.digest), local(inputs_root / name / member.path))
        else:
            for name in names:
                capture(location.store_id, location.relative_path, local(inputs_root / name))

    def store_reader(store):
        return lambda path, limit: buffers[(store, path)]

    return SeriesEvidence({store: store_reader(store) for store in evidence.stores}, evidence.locations)


def check_series_input_content(graph: SeriesGraph, records: HeldRecords, contents: Mapping[str, str]) -> None:
    """Match full content sets under the existing file and resource-map folds.

    Dataset identity ignores resource names and repetition. A singleton set
    can be staged as a file (raw digest) or a resource map (dataset fold).
    """
    for dataset in sorted({row.ref.dataset for row in graph}):
        if not records.holds(dataset):
            raise DependencyNotHeld(f"series dataset {dataset} is not recorded")
        declaration = declaration_from_facet(records.read(dataset).facets["dataset"])
        address = dataset_address(declaration)
        if address is None or address != dataset:
            raise SeriesRefused("invalid-series", "series input declaration/address disagrees")
        digests = {resource.digest for resource in declaration.resources}
        allowed = {address.removeprefix("dataset:")}
        if len(digests) == 1:
            digest = next(iter(digests))
            assert digest is not None  # a content address above requires every digest
            allowed.add(digest)
        if contents.get(dataset) not in allowed:
            raise SeriesRefused("invalid-series", "series input content differs from its dataset declaration")
