"""Mint a produced dataset from one production run's manifest (R23).

The stamped basis attests one derivation route when an address is first minted;
a later producing run adds its own edge and preserves that basis unchanged
(computation §5.2). Divergence, deletion, conflict, and all store/audit
behaviour are deliberately deferred to the store and audit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import MalformedClosure
from beliefs.recipe import RunClosure
from beliefs.sealed import sealed

__all__ = ["MintedDataset", "ProducesEdge", "StampedBasis", "mint_dataset"]


def _require_str(value: object, where: str) -> None:
    if type(value) is not str:
        raise MalformedClosure(f"{where} must be a string")


@sealed
@final
@dataclass(frozen=True)
class ProducesEdge:
    run: str
    dataset: str

    def __post_init__(self) -> None:
        _require_str(self.run, "produces edge run")
        _require_str(self.dataset, "produces edge dataset")


@sealed
@final
@dataclass(frozen=True)
class StampedBasis:
    run: str
    transforms: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_str(self.run, "stamped basis run")
        if type(self.transforms) is not tuple or not all(type(value) is str for value in self.transforms):
            raise MalformedClosure("stamped basis transforms must be a tuple of strings")


@sealed
@final
@dataclass(frozen=True)
class MintedDataset:
    address: str
    edge: ProducesEdge
    basis: StampedBasis
    stamped: bool

    def __post_init__(self) -> None:
        _require_str(self.address, "minted dataset address")
        if type(self.edge) is not ProducesEdge:
            raise MalformedClosure("a minted dataset holds a ProducesEdge")
        if type(self.basis) is not StampedBasis:
            raise MalformedClosure("a minted dataset holds a StampedBasis")
        if type(self.stamped) is not bool:
            raise MalformedClosure("a minted dataset stamped flag must be a bool")


def mint_dataset(run: RunClosure, *, existing_bases: Mapping[str, StampedBasis]) -> MintedDataset:
    """Project the manifest's content identities and stamp its first basis."""
    if type(run) is not RunClosure:
        raise MalformedClosure("mint_dataset requires a RunClosure")
    if run.recipe.shape != "dataset-production":
        raise MalformedClosure("mint_dataset requires a dataset-production run")
    if not isinstance(existing_bases, Mapping) or not all(
        type(address) is str and type(basis) is StampedBasis for address, basis in existing_bases.items()
    ):
        raise MalformedClosure("existing bases must map strings to StampedBasis values")

    address = dataset_address(
        DatasetDeclaration(
            resources=tuple(ResourceDeclaration(name=name, digest=digest) for name, digest in run.result.outputs)
        )
    )
    if address is None:
        raise MalformedClosure("a production manifest must have a dataset content identity")
    run_address = run.address()
    prior = existing_bases.get(address)
    basis = prior or StampedBasis(
        run=run_address,
        transforms=tuple(sorted(value.content for value in run.recipe.inputs if value.role == "transforms")),
    )
    return MintedDataset(
        address=address,
        edge=ProducesEdge(run=run_address, dataset=address),
        basis=basis,
        stamped=prior is None,
    )
