"""Content-addressed correspondence between two bearer sorts."""

from collections.abc import Mapping
from dataclasses import dataclass

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.contract.base import SUPPORTED_CARDINALITIES
from beliefs.errors import MalformedRecord

__all__ = [
    "MAPPING_DOMAIN",
    "MAPPING_FACET",
    "MAPPING_KIND",
    "ReferentMapping",
    "mapping_from_stored",
    "mapping_identity",
    "mapping_projection",
]

MAPPING_DOMAIN = "science.referent-mapping.v1"
MAPPING_KIND = MAPPING_FACET = "referent-mapping"


@dataclass(frozen=True)
class ReferentMapping:
    source_sort: str
    target_sort: str
    reference: Mapping[str, str]
    cardinality: str
    aggregation: str | None
    members: str | None

    def __post_init__(self) -> None:
        record.term(self.source_sort, "source sort")
        record.term(self.target_sort, "target sort")
        object.__setattr__(self, "reference", record.strings(self.reference))
        if record.text(self.cardinality, "cardinality") not in SUPPORTED_CARDINALITIES:
            raise MalformedRecord("unsupported mapping cardinality")
        if self.aggregation is not None:
            record.term(self.aggregation, "aggregation")
        if self.members is not None:
            record.address(self.members, "sha256")

    def joins(self, a: str, b: str) -> bool:
        return {self.source_sort, self.target_sort} == {a, b}


def mapping_projection(value: ReferentMapping) -> dict[str, object]:
    result: dict[str, object] = {
        "source_sort": value.source_sort,
        "target_sort": value.target_sort,
        "reference": dict(value.reference),
        "cardinality": value.cardinality,
    }
    if value.aggregation is not None:
        result["aggregation"] = value.aggregation
    if value.members is not None:
        result["members"] = value.members
    return result


def mapping_identity(value: ReferentMapping) -> str:
    return record.identity(MAPPING_KIND, MAPPING_DOMAIN, mapping_projection(value))


def _mapping_from(value: object) -> ReferentMapping:
    fields = record.shape(value, {"source_sort", "target_sort", "reference", "cardinality"}, {"aggregation", "members"})
    return ReferentMapping(
        record.term(fields["source_sort"], "source sort"),
        record.term(fields["target_sort"], "target sort"),
        record.strings(fields["reference"]),
        record.text(fields["cardinality"], "cardinality"),
        record.term(fields["aggregation"], "aggregation") if "aggregation" in fields else None,
        record.address(fields["members"], "sha256") if "members" in fields else None,
    )


def mapping_from_stored(node: Node) -> ReferentMapping:
    return record.from_stored(node, MAPPING_KIND, _mapping_from, mapping_projection, mapping_identity)
