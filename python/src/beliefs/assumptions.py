"""Vocabulary-named assumption instances and their declared particulars."""

from collections.abc import Mapping
from dataclasses import dataclass

from beliefs import _measurement_record as record
from beliefs.errors import MalformedRecord
from beliefs.profile import ProfileSpec

__all__ = ["AssumptionInstance", "check_instance", "instance_from_projection", "instance_projection"]


@dataclass(frozen=True)
class AssumptionInstance:
    kind: str
    particulars: Mapping[str, str]

    def __post_init__(self) -> None:
        record.term(self.kind, "assumption kind")
        object.__setattr__(self, "particulars", record.strings(self.particulars))


def instance_projection(instance: AssumptionInstance) -> dict[str, object]:
    return {"kind": instance.kind, "particulars": dict(instance.particulars)}


def instance_from_projection(value: object) -> AssumptionInstance:
    fields = record.shape(value, {"kind", "particulars"})
    return AssumptionInstance(record.term(fields["kind"], "assumption kind"), record.strings(fields["particulars"]))


def check_instance(profile: ProfileSpec, instance: AssumptionInstance) -> None:
    declaration = profile.assumption_kinds.get(instance.kind)
    if declaration is None:
        raise MalformedRecord(f"undeclared assumption kind {instance.kind!r}")
    if not set(declaration.particulars) <= instance.particulars.keys():
        raise MalformedRecord(f"{instance.kind}: missing required particulars")
