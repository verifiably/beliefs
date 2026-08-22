"""The log seam: the engine capability every verification act is handed.

`LogSeam` is the whole of what an act of slice 3 may do with the engine —
inspect a chain in either mode, state a set of paths, read a validated head,
and take the two locks that make those answers true. Every act core takes one
as a parameter, and `science.root` is the only constructor of a production
seam: a test builds a stand-in, an act never reaches for one.

**What crosses and what does not.** Every callable is typed in Science's own
vocabulary (`science.world.logmodel`), so nothing here names an engine class.
The one exception is deliberate and typed as `object`: a path-state
fingerprint is the engine's own value, carried opaquely and compared only by
equality. `absent_state` is the engine's absent singleton, which replay needs
as the default of its union comparison and which Science must not mint for
itself.

**The adapters' one translation.** Three engine states escape the inspecting
commands' never-raises envelope, and the seam's adapters translate exactly
those three into `LogEvidenceRefused` (design §6.4) — a refusal to judge, not
a judgment. Everything else, `ProtocolError` and setup errors included, keeps
its own contract.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from science.corpus import OperationLock
from science.world.logmodel import ChainHead, ChainView

__all__ = [
    "LogSeam",
    "PresentedIdentity",
    "PresentedManifest",
    "PresentedWorldIds",
]


@dataclass(frozen=True)
class LogSeam:
    """One root's worth of engine capability, as callables over `Path`.

    `inspect_registered` serves a live root: it takes the project lock, runs
    recovery and answers about chain state. `inspect_detached` serves an
    arriving root: a read-only scan, no metadata root, no recovery, pending
    honestly unresolved. `capture` states exactly the named paths, in the
    caller's order, under one coherent observation. `read_head` is the
    validated head read. `world_lock` yields holding a world root's lock —
    resolved through a lock-only lookup, so an audit locks a world it never
    opened and an opened `World` shares the identical lock object — and
    `corpus_lock` returns a corpus root's operation lock, the very one its
    writers take.
    """

    inspect_registered: Callable[[Path], ChainView]
    inspect_detached: Callable[[Path], ChainView]
    capture: Callable[[Path, tuple[str, ...]], tuple[tuple[str, object], ...]]
    read_head: Callable[[Path], ChainHead]
    absent_state: object
    world_lock: Callable[[Path], AbstractContextManager[None]]
    corpus_lock: Callable[[Path], OperationLock]


@dataclass(frozen=True)
class PresentedManifest:
    """What a corpus root's manifest claims its identity is."""

    corpus_id: str


@dataclass(frozen=True)
class PresentedWorldIds:
    """What a world root claims its identity is, from both places it is written.

    `mirrored` is `None` where the root carries no `world.yaml` at all, which
    is a different fact from a mirror that disagrees with the configuration.
    """

    configured: str
    mirrored: str | None


PresentedIdentity: TypeAlias = PresentedManifest | PresentedWorldIds
"""The typed identity input the evaluator's subject-mismatch findings compare
against.

State fingerprints alone cannot say what a root *claims* to be: a chain proves
what happened to a surface, not which corpus or world the operator believes
they are holding. The claim is therefore an explicit input rather than
something the evaluator goes looking for.
"""
