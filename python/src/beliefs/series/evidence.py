"""Caller-selected local reads with graph-wide bounds and buffer integrity."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias

from beliefs.dataset import dataset_address, declaration_from_facet
from beliefs.errors import ScienceError
from beliefs.holdings.records import StoreLocator, StoreTreeLocator
from beliefs.series.types import SeriesRef, SeriesRefused
from beliefs.tree import object_path, parse_tree_file

if TYPE_CHECKING:
    from beliefs.dependencies import HeldRecords

__all__ = ["ReadBudget", "SeriesEvidence", "SeriesStoreRead", "load_series_object"]

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
        raise SeriesRefused("invalid-series", f"series dataset {ref.dataset} is not recorded")
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
