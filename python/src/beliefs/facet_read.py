"""Derivation-side reads of domain facets (biology pack design §5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.dataset import dataset_address
from beliefs.errors import FacetUndeclared, MalformedRecord
from beliefs.facets import validate_payload
from beliefs.identity import v1
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed

__all__ = ["FACET_READ_DOMAIN", "FacetRead", "read_observed_facets"]

FACET_READ_DOMAIN = "science.facet-read.v1"

_MINT = object()


@sealed
@final
@dataclass(frozen=True, init=False)
class FacetRead:
    address: str
    key: str
    payload_digest: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MalformedRecord(
            "FacetRead is minted by the reader — use read_observed_facets(profile, view, target). A field-wise "
            "constructor would let a caller author the read ledger the consulted walk digests (F §5.6)."
        )

    @classmethod
    def _minted(cls, mint: object, *, address: str, key: str, payload_digest: str) -> FacetRead:
        if mint is not _MINT:
            raise MalformedRecord("FacetRead._minted is the reader's, not a public constructor")
        row = object.__new__(cls)
        object.__setattr__(row, "address", address)
        object.__setattr__(row, "key", key)
        object.__setattr__(row, "payload_digest", payload_digest)
        return row

    def projection(self) -> list[str]:
        return [self.address, self.key, self.payload_digest]


def read_observed_facets(profile: ProfileSpec, view: ReadView, target: str) -> tuple[FacetRead, ...]:
    """Fetch and validate the namespaced facets on one observed dataset."""
    if not isinstance(view, ReadView):
        raise MalformedRecord(
            f"the domain-facet reader reads through a corpus ReadView, not a {type(view).__name__}; a row is a "
            "receipt for a read against a corpus, and nothing else can mint one (B3)"
        )
    if not view.holds(target):
        raise MalformedRecord(f"{target} is not held by this corpus; the reader is called over held observed inputs only")
    node = view.get(target)
    if node.kind != "dataset":
        raise MalformedRecord(f"{node.id}: the domain-facet reader reads observed datasets, not {node.kind!r}")
    address = dataset_address(stored.dataset_declaration(node))
    if address is None:
        raise MalformedRecord(f"{node.id}: an observed dataset with no content address has nothing to ledger against")
    rows: list[FacetRead] = []
    for key in sorted(node.facets):
        _, separator, _ = key.partition("/")
        if not separator:
            continue
        facet = profile.facets.get(key)
        if facet is None or "dataset" not in facet.attaches_to:
            raise FacetUndeclared(
                f"facet-undeclared: {key!r} on {node.id} is not a dataset facet the profile in force declares; the "
                "profile is stale against the corpus, and a read under it would digest a meaning nobody declared"
            )
        payload = node.facets[key]
        validate_payload(facet, payload, where=node.id)
        rows.append(
            FacetRead._minted(_MINT, address=address, key=key, payload_digest=v1.digest(FACET_READ_DOMAIN, payload))
        )
    return tuple(rows)
