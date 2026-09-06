"""Stdlib-only values and callables for the holdings store boundary."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

WritePlan: TypeAlias = Sequence[object]


@dataclass(frozen=True)
class FileStateView:
    content_hash: str


@dataclass(frozen=True)
class AbsentStateView:
    pass


@dataclass(frozen=True)
class NonRegularStateView:
    kind: str


PathStateView = FileStateView | AbsentStateView | NonRegularStateView


@dataclass(frozen=True)
class PathObservedView:
    state: PathStateView


@dataclass(frozen=True)
class ReadNotAttemptedView:
    reason: str
    lifecycle_state: str | None
    detail: str


@dataclass(frozen=True)
class ReadUnestablishedView:
    reason: str
    detail: str


PathReadView = PathObservedView | ReadNotAttemptedView | ReadUnestablishedView


@dataclass(frozen=True)
class StoreOutcomeView:
    txid: str
    final_states: tuple[tuple[str, PathStateView], ...]


@dataclass(frozen=True)
class StoreActSeam:
    corpus_lock: Callable[[Path], AbstractContextManager[None]]
    append_intent: Callable[[Path, bytes], str]
    publish_fulfilling: Callable[[Path, WritePlan, str], None]
    read_path: Callable[[Path, str], PathReadView]
    store_write: Callable[[Path, str, bytes], StoreOutcomeView]
    store_delete: Callable[[Path, str], StoreOutcomeView]
    store_move: Callable[[Path, str, str], StoreOutcomeView]
    store_genesis: Callable[[Path], bytes]
