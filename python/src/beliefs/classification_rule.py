"""Content-addressed classification definitions and their input observables."""

from dataclasses import dataclass

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.errors import MalformedRecord
from beliefs.measurement import Observable, observable_projection
from beliefs.procedure import (
    External,
    Implementation,
    _external_from,
    _external_projection,
    _implementation_from,
    _implementation_projection,
)

__all__ = [
    "RULE_DOMAIN",
    "RULE_FACET",
    "RULE_KIND",
    "ClassificationRule",
    "rule_from_stored",
    "rule_identity",
    "rule_projection",
]

RULE_DOMAIN = "science.classification-rule.v1"
RULE_KIND = RULE_FACET = "classification-rule"


@dataclass(frozen=True)
class ClassificationRule:
    classes: str
    reads: tuple[Observable, ...]
    definition: str
    external: External | None
    implementation: Implementation | None
    annotator: str | None

    def __post_init__(self) -> None:
        record.term(self.classes, "classes sort")
        object.__setattr__(self, "reads", record.observables(self.reads))
        record.text(self.definition, "definition")
        if self.annotator is not None:
            record.text(self.annotator, "annotator")
        if self.external is not None and not isinstance(self.external, External):
            raise MalformedRecord("external must be an External")
        if self.implementation is not None and not isinstance(self.implementation, Implementation):
            raise MalformedRecord("implementation must be an Implementation")


def rule_projection(value: ClassificationRule) -> dict[str, object]:
    result: dict[str, object] = {
        "classes": value.classes,
        "reads": [observable_projection(row) for row in value.reads],
        "definition": value.definition,
    }
    if value.external is not None:
        result["external"] = _external_projection(value.external)
    if value.implementation is not None:
        result["implementation"] = _implementation_projection(value.implementation)
    if value.annotator is not None:
        result["annotator"] = value.annotator
    return result


def rule_identity(value: ClassificationRule) -> str:
    return record.identity(RULE_KIND, RULE_DOMAIN, rule_projection(value))


def _rule_from(value: object) -> ClassificationRule:
    fields = record.shape(value, {"classes", "reads", "definition"}, {"external", "implementation", "annotator"})
    return ClassificationRule(
        record.term(fields["classes"], "classes"),
        record.sequence(fields["reads"], record.observable),
        record.text(fields["definition"], "definition"),
        _external_from(fields["external"]) if "external" in fields else None,
        _implementation_from(fields["implementation"]) if "implementation" in fields else None,
        record.text(fields["annotator"], "annotator") if "annotator" in fields else None,
    )


def rule_from_stored(node: Node) -> ClassificationRule:
    return record.from_stored(node, RULE_KIND, _rule_from, rule_projection, rule_identity)
