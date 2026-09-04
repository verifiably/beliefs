"""The one full authority every migrated test binds (design §9.2)."""
from __future__ import annotations

from collections.abc import Iterable

from beliefs.permit import ACT_FAMILIES, KIND_ACTS, Authority, WritePermit

ACTOR = "test-actor"
FULL = Authority(WritePermit.full(), ACTOR)


def narrowed(*, kinds: Iterable[str] = (), families: Iterable[str] = (), actor: str = ACTOR) -> Authority:
    """A governed-only permit holding exactly these kinds and families (no ungoverned kinds)."""
    return Authority(WritePermit(frozenset(kinds), frozenset(families)), actor)


def lacking(*, kinds: Iterable[str] = (), families: Iterable[str] = (), actor: str = ACTOR) -> Authority:
    """The full permit minus exactly these kinds and families; ungoverned kinds stay permitted."""
    return Authority(
        WritePermit(frozenset(KIND_ACTS) - frozenset(kinds), ACT_FAMILIES - frozenset(families), True), actor
    )
