"""Write permits (design `docs/designs/2026-09-04-write-permits-design.md` §3).

The closed act families, the kind-to-route map, the permit value, and the
authority every write entry point requires of before its first effect. This
module imports nothing that writes: `errors` and the identity encoding only,
so every seam can import it without a cycle.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from beliefs.errors import PermitExceeded, PermitFact, PermitSummary
from beliefs.identity import v1

__all__ = [
    "ACT_FAMILIES",
    "COMMAND_REACHABLE_FAMILIES",
    "KIND_ACTS",
    "ActFamily",
    "Authority",
    "RequiredCapabilities",
    "WritePermit",
    "permit_covers",
    "require_actor",
    "scoped_authority",
]

ActFamily = Literal["corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"]

ACT_FAMILIES: frozenset[str] = frozenset(
    {"corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"}
)
"""The closed enumeration. `publish` arrives by sub-project 5's amendment."""

COMMAND_REACHABLE_FAMILIES: frozenset[str] = frozenset({"corpus-write", "run", "holdings"})
"""Command-framework §4.4 as data: the families a write class may map to."""

_CORPUS_WRITE = frozenset({"corpus-write"})
_COORDINATION_KINDS = ("project", "question", "hypothesis", "topic", "theme", "task", "decision", "note")

KIND_ACTS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "proposition": _CORPUS_WRITE,
        "source-assertion": _CORPUS_WRITE,
        "assessment": _CORPUS_WRITE,
        "analysis-spec": _CORPUS_WRITE,
        "run": frozenset({"run", "corpus-write"}),
        "verification": _CORPUS_WRITE,
        "dataset": _CORPUS_WRITE,
        "source": _CORPUS_WRITE,
        "holdings-observation": frozenset({"holdings"}),
        "retraction": _CORPUS_WRITE,
        "instrument-certification": _CORPUS_WRITE,
        "coreference-attestation": _CORPUS_WRITE,
        "act-report": frozenset({"corpus-write", "run"}),
        **{kind: _CORPUS_WRITE for kind in _COORDINATION_KINDS},
    }
)
"""Every mintable kind to the families admissible as its minting route —
validation data, never a requirement derivation (§3.2). `test_permit.py`
holds the key set equal to `stored.WORLD_KINDS ∪ coordination.COORDINATION_KINDS`."""


def require_actor(actor: object) -> str:
    """The one actor rule: an exact, non-empty, `v1`-encodable string."""
    if type(actor) is not str:
        raise TypeError("actor must be an exact string")
    if not actor:
        raise ValueError("actor must be a non-empty string")
    try:
        v1.encode(actor)
    except Exception as caught:
        raise ValueError(f"actor is not encodable: {caught}") from caught
    return actor


def _require_closed(values: object, universe: frozenset[str], dimension: str) -> frozenset[str]:
    if type(values) is not frozenset or any(type(value) is not str for value in values):
        raise TypeError(f"{dimension}s must be an exact frozenset of strings")
    unknown = sorted(values - universe)
    if unknown:
        raise ValueError(f"unknown {dimension}{'s' if len(unknown) > 1 else ''}: {unknown}")
    return values


@dataclass(frozen=True)
class WritePermit:
    """Two closed dimensions (§3.3) and the ungoverned flag (§13.7). `full()`
    is the only convenience."""

    kinds: frozenset[str]
    act_families: frozenset[str]
    ungoverned: bool = False

    def __post_init__(self) -> None:
        _require_closed(self.kinds, frozenset(KIND_ACTS), "kind")
        _require_closed(self.act_families, ACT_FAMILIES, "act family")
        if type(self.ungoverned) is not bool:
            raise TypeError("ungoverned must be an exact bool")

    @classmethod
    def full(cls) -> WritePermit:
        return cls(frozenset(KIND_ACTS), ACT_FAMILIES, True)

    def summary(self) -> PermitSummary:
        return PermitSummary(tuple(sorted(self.kinds)), tuple(sorted(self.act_families)), self.ungoverned)


@dataclass(frozen=True)
class Authority:
    """A permit and an actor, bound once at a construction seam (§3.4)."""

    permit: WritePermit
    actor: str

    def __post_init__(self) -> None:
        if type(self.permit) is not WritePermit:
            raise TypeError("permit must be a WritePermit")
        require_actor(self.actor)

    def require(self, family: str, kinds: Iterable[str] = ()) -> None:
        """Refuse before any effect, naming the family or the first missing
        kind in the caller's order. No other outcome."""
        if family not in ACT_FAMILIES:
            raise ValueError(f"{family!r} is not an act family")
        if family not in self.permit.act_families:
            raise PermitExceeded(PermitFact("family", family), self.permit.summary())
        for kind in kinds:
            if kind in KIND_ACTS:
                permitted = kind in self.permit.kinds
            else:
                permitted = self.permit.ungoverned and family == "corpus-write"
            if not permitted:
                raise PermitExceeded(PermitFact("kind", kind), self.permit.summary())



# The read door's authority (§16): the empty permit, so every act on a `World`
# opened through `root.open_world_read` refuses on its family before any effect,
# and an actor no record can ever carry, because no act under it runs.
READ_ONLY = Authority(WritePermit(frozenset(), frozenset()), "read-only")


@dataclass(frozen=True)
class RequiredCapabilities:
    """What a declaration needs (§3.5). Compiled to a permit whose families
    are exactly the selected routes; never a union over `KIND_ACTS`."""

    permit: WritePermit

    def __post_init__(self) -> None:
        if type(self.permit) is not WritePermit:
            raise TypeError("a requirement carries a WritePermit")
        if not self.permit.act_families <= COMMAND_REACHABLE_FAMILIES:
            raise ValueError("a requirement names only command-reachable families")
        if self.permit.ungoverned:
            raise ValueError("a requirement never claims ungoverned kinds; a declaration names governed ones")

    @classmethod
    def none(cls) -> RequiredCapabilities:
        return cls(WritePermit(frozenset(), frozenset()))

    @classmethod
    def coordination(cls) -> RequiredCapabilities:
        return cls(WritePermit(frozenset(_COORDINATION_KINDS), _CORPUS_WRITE))

    @classmethod
    def for_kinds(cls, kinds: Iterable[str], routes: Mapping[str, str]) -> RequiredCapabilities:
        declared = frozenset(kinds)
        unknown = sorted(declared - frozenset(KIND_ACTS))
        if unknown:
            raise ValueError(f"unknown kinds: {unknown}")
        stray = sorted(frozenset(routes) - declared)
        if stray:
            raise ValueError(f"routes name undeclared kinds: {stray}")
        families: set[str] = set()
        for kind in sorted(declared):
            admissible = KIND_ACTS[kind]
            if kind in routes:
                route = routes[kind]
                if route not in admissible:
                    raise ValueError(f"KIND_ACTS does not admit route {route!r} for {kind!r}")
            elif len(admissible) == 1:
                (route,) = admissible
            else:
                raise ValueError(f"{kind!r} admits more than one route; the declaration must select one")
            families.add(route)
        return cls(WritePermit(declared, frozenset(families)))

    @classmethod
    def publishes(cls) -> RequiredCapabilities:
        raise ValueError("publish is not an act family")


def scoped_authority(required: RequiredCapabilities, actor: str) -> Authority:
    """A requirement's exact permit, bound to an actor its caller derived.

    E6's static test admits an `Authority(...)` construction in this module and
    nowhere else (§16), and the writer session narrows an authority per
    invocation from a `RequiredCapabilities` it holds no `Authority` for
    (writer-session design §5). The permit is exactly `required.permit` — never
    widened, never defaulted — so this is the construction seam §3.4 already
    names, reached by the one caller with no authority of its own to pass on.
    """
    if type(required) is not RequiredCapabilities:
        raise TypeError("scoped_authority binds a RequiredCapabilities")
    return Authority(required.permit, actor)


def permit_covers(ceiling: WritePermit, required: RequiredCapabilities) -> bool:
    """Subset inclusion on both dimensions and nothing else (E5)."""
    if type(ceiling) is not WritePermit or type(required) is not RequiredCapabilities:
        raise TypeError("permit_covers judges a WritePermit against a RequiredCapabilities")
    return (
        required.permit.kinds <= ceiling.kinds
        and required.permit.act_families <= ceiling.act_families
        and (not required.permit.ungoverned or ceiling.ungoverned)
    )
