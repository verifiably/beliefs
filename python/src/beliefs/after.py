"""A chain's entries after a tip, read detached.

`read_after` serves a caller that holds a tip it saw earlier (a seal's
`ChainTip`) and wants what the chain recorded since. The read goes through the
seam's detached inspection: no lock, no recovery, no append, so a staged
registration nothing has settled is reported in `pending`, never settled. A
refusal is a value (`AfterUnavailable`), never an exception, so the caller can
turn each reason into its own answer. Placement reuses `world.events.place`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from beliefs.root import log_seam
from beliefs.world.events import place
from beliefs.world.logmodel import AbsentView, EntryView, MalformedView, WellFormedView

__all__ = ["AfterEntries", "AfterRead", "AfterReason", "AfterUnavailable", "read_after"]

AfterReason = Literal[
    "chain-absent",
    "chain-malformed",
    "genesis-mismatch",
    "tip-not-on-chain",
    "through-not-on-chain",
    "through-before-after",
]


@dataclass(frozen=True)
class AfterEntries:
    """The entries strictly after the named tip, through `tip` inclusive.

    `tip` is the digest the slice runs to: the `through` digest when one was
    given, else the chain's tip. It is `after` itself when `entries` is empty.
    `pending` is the chain's unsettled `(txid, registration digest)` pairs, as
    the detached read saw them."""

    entries: tuple[EntryView, ...]
    tip: str
    pending: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class AfterUnavailable:
    reason: AfterReason
    detail: str


AfterRead = AfterEntries | AfterUnavailable


def read_after(root: Path, *, genesis: str, after: str, through: str | None = None) -> AfterRead:
    """`root`'s entries strictly after `after`, through `through` inclusive or
    the chain's tip, or the reason they cannot be named.

    `genesis` is the digest of the chain the caller saw `after` on; a chain
    with another genesis was replaced. `after` and `through` must be entries of
    the chain, `through` not before `after`."""
    root = Path(root)
    if not root.is_dir():
        # The seam does not return `AbsentView` for a root that is not there;
        # the engine's root open raises. A missing directory is an absent chain.
        return AfterUnavailable("chain-absent", f"{root}: no such root")
    view = log_seam().inspect_detached(root)
    if type(view) is AbsentView:
        return AfterUnavailable("chain-absent", f"{root}: no chain")
    if type(view) is MalformedView:
        return AfterUnavailable("chain-malformed", f"{root}: {view.defect.detail}")
    if type(view) is not WellFormedView:
        raise TypeError(f"unexpected chain view {type(view).__name__}")
    if genesis != view.genesis.digest:
        return AfterUnavailable(
            "genesis-mismatch", f"{root}: the chain's genesis is {view.genesis.digest}, not {genesis}"
        )
    start = place(view, genesis_digest=genesis, head_digest=after)
    if start is None:
        return AfterUnavailable("tip-not-on-chain", f"{root}: {after} is no entry of the chain")
    if through is None:
        end = len(view.entries) - 1
        end_digest = view.tip
    else:
        stop = place(view, genesis_digest=genesis, head_digest=through)
        if stop is None:
            return AfterUnavailable("through-not-on-chain", f"{root}: {through} is no entry of the chain")
        if stop.head < start.head:
            return AfterUnavailable("through-before-after", f"{root}: {through} precedes {after}")
        end = stop.head
        end_digest = through
    return AfterEntries(view.entries[start.head + 1 : end + 1], end_digest, view.pending)
