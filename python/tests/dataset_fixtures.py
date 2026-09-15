"""Seed-based dataset fixtures (slice 5 design §8.2).

A dataset's id is derived from its declared content identity, so a test
can no longer name a dataset by handle and build it later. These helpers
give every seed one deterministic pinned declaration and the address that
declaration derives, so a closure recipe, a relation target or a lineage
route can name `dataset_ref("raw")` before `dataset("raw")` is built, and
the two always agree.
"""

from __future__ import annotations

from hashlib import sha256

from nodes.core.node import Node

from beliefs import stored
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address

__all__ = ["dataset", "dataset_ref", "digest_for", "pinned", "pinned_for"]

_MINTED: dict[str, str] = {}


def digest_for(seed: str) -> str:
    """One deterministic sha256 digest per seed, distinct across seeds."""
    return "sha256:" + sha256(f"dataset-fixture:{seed}".encode()).hexdigest()


def pinned(seed: str) -> list[dict[str, str]]:
    """The one-resource pinned declaration for `seed`."""
    return [{"name": "matrix", "digest": digest_for(seed)}]


def dataset_ref(seed: str) -> str:
    """The address `pinned(seed)` derives — usable before the record is built."""
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="matrix", digest=digest_for(seed)),)))
    assert address is not None
    _MINTED[address] = seed
    return address


def pinned_for(ref: str) -> list[dict[str, str]]:
    """The declaration behind a ref `dataset_ref` minted; `KeyError` for any other."""
    return pinned(_MINTED[ref])


def dataset(seed: str, *, title: str | None = None, **facets) -> Node:
    """A dataset record at `dataset_ref(seed)`: `title` defaults to the seed;
    `facets` are the builder's keyword facets (`empirical_observation`,
    `basis`, `domain_facets`)."""
    dataset_ref(seed)
    return stored.dataset_node(seed, title=seed if title is None else title, resources=pinned(seed), **facets)
