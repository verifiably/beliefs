"""Science-typed chain views — the vocabulary the log seam speaks.

**Why these types exist.** `science.root` is the one module that may import
`atoms`, and the acts of slice 3 must discriminate over an inspection result:
well-formed against malformed against absent, and defect kind by defect kind.
Discriminating over the engine's own union would require naming the engine's
classes above the composition root. So the composition root converts every
`atoms` inspection result into the closed unions below **before** it crosses
the seam, and every act reads these.

**One vocabulary, not two.** The conversion is a re-typing of the *shape* and
never of the *facts*: a state fingerprint is carried as an atoms `PathState`
object, typed here as `object`, **opaque and compared only by equality**.
Science never constructs one, never interprets one and never re-encodes one,
which is what keeps the log design's one-summary-model rule a mechanism rather
than a promise. The chain's own entries carry the encoded form
(`PathStateJSON`) and the capture command returns `PathState`; the composition
root decodes the former with the engine's own `state_from_json` during this
conversion, so both sides of every replay comparison are `PathState` values and
the comparison is a comparison rather than a re-encoding.

Stdlib imports only, by rule — a dependency of its own would be a second place
engine shape could enter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, get_args

__all__ = [
    "DEFECT_KINDS",
    "AbsentView",
    "ChainHead",
    "ChainView",
    "DefectKind",
    "DefectView",
    "EntryView",
    "GenesisEntryView",
    "IntentEntryView",
    "MalformedView",
    "RegisteredEntryView",
    "SettledEntryView",
    "WellFormedView",
]


@dataclass(frozen=True, slots=True)
class GenesisEntryView:
    """The chain's one genesis: its registration payload and its baseline.

    `baseline` pairs a registered-surface path with the opaque state the
    engine captured for it at registration. Replay starts from exactly this.
    """

    digest: str
    payload: bytes
    baseline: tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class RegisteredEntryView:
    """One transaction's registration: the surface it declared, both ends.

    `intent_digest` and `consumer_tag` are deliberately absent: nothing this
    slice judges reads them, and a view member nothing consumes is a fact
    Science would be claiming to carry faithfully for no reason.
    """

    digest: str
    txid: str
    initial: tuple[tuple[str, object], ...]
    final: tuple[tuple[str, object], ...]
    fulfills: str | None


@dataclass(frozen=True, slots=True)
class SettledEntryView:
    """One transaction's settlement.

    The engine's two-member outcome enum arrives as `committed`: replay applies
    a committed registration's transition and treats a rolled-back one as no
    transition at all, so the boolean is the whole of what the outcome decides
    here.
    """

    digest: str
    txid: str
    registration: str
    committed: bool


@dataclass(frozen=True, slots=True)
class IntentEntryView:
    digest: str
    payload: bytes


EntryView: TypeAlias = GenesisEntryView | RegisteredEntryView | SettledEntryView | IntentEntryView

DefectKind = Literal[
    "foreign-leaf",
    "name-mismatch",
    "undecodable-entry",
    "genesis-count",
    "missing-predecessor",
    "sibling-branch",
    "cycle",
    "orphan-history",
    "settlement-unregistered",
    "settlement-txid-mismatch",
    "duplicate-settlement",
    "duplicate-registration",
    "fulfills-invalid",
    "duplicate-fulfillment",
]
"""One member per taxonomy entry of the design's §2.1 defect list.

The three `fulfills` reference variants (missing, non-ancestor, non-intent)
share `fulfills-invalid`, and zero and multiple genesis share `genesis-count`,
because the engine reports one defect per chain and those variants differ in
wording rather than in what the operator must do. The engine's own spellings
differ for three members; the composition root holds the closed mapping, which
is checked member-by-member against the engine's enum.
"""

DEFECT_KINDS: tuple[DefectKind, ...] = get_args(DefectKind)
"""The taxonomy as a value, so the mapping's closedness is assertable."""


@dataclass(frozen=True, slots=True)
class DefectView:
    """The one deterministic defect a malformed chain reports.

    `subject` names the offending chain-directory leaf for the three scan-time
    kinds, the offending entry digest for every linkage and entry-class kind,
    and is `None` for exactly one kind — `genesis-count`, where a chain with
    zero or several geneses has no single offending entry and naming one of
    several would invent a fact. `detail` is the engine's own wording,
    verbatim: there is exactly one place a defect's message is minted.
    """

    kind: DefectKind
    subject: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class WellFormedView:
    """The chain's linearization, plus the registrations nothing has settled.

    `entries` is the engine's linearized order — genesis first, one successor
    per entry, tip last — carried whole, and `genesis` is `entries[0]`, the
    same object. It is named separately because the evaluator validates the
    genesis *form* before it looks at anything else (§4.2 step 1) and would
    otherwise have to re-discriminate the first entry to reach it.

    `pending` pairs a transaction id with the registration digest no settlement
    settles. In detached mode a staged, non-durable registration may contribute
    a pair whose digest does **not** occur in `entries`: staged evidence errs
    toward refusal, so a detached pending digest is not an entry lookup key.
    """

    genesis: GenesisEntryView
    entries: tuple[EntryView, ...]
    tip: str
    pending: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class MalformedView:
    defect: DefectView


@dataclass(frozen=True, slots=True)
class AbsentView:
    """No durable chain claim: no chain directory, or an empty one."""


ChainView: TypeAlias = WellFormedView | MalformedView | AbsentView


@dataclass(frozen=True, slots=True)
class ChainHead:
    """One validated head read, with the genesis payload it was read from.

    The payload is a member because a world export must bind its subject to
    the `world_id` the genesis carries, and a head read that returned only the
    two digests would leave the exporter re-reading the chain to learn what it
    had just read.
    """

    genesis_digest: str
    genesis_payload: bytes
    tip: str
