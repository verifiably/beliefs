"""Check a measured binding against pack admissions and held normative records."""

from dataclasses import dataclass

from beliefs.assumptions import AssumptionInstance, check_instance, instance_projection
from beliefs.classification_rule import ClassificationRule
from beliefs.dependencies import DependencyEntry, HeldRecords, dependency_closure, read_record
from beliefs.errors import (
    MalformedRecord,
    MappingRequired,
    MeasurementNotAdmitted,
    ProcedureYieldMismatch,
    ProfileError,
    ProxyRequired,
)
from beliefs.identity import v1
from beliefs.measurement import Measure, Observable, check_measure, check_measure_procedure, check_observable
from beliefs.procedure import Procedure, SameAs
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import ProxyModel
from beliefs.referent_mapping import ReferentMapping
from beliefs.restriction import RestrictionMap, check_held_rule_scope, co_scope, co_scope_by_dimension

__all__ = ["Apt", "check_aptness"]


@dataclass(frozen=True)
class Apt:
    target_observable: Observable
    assumptions: tuple[AssumptionInstance, ...]
    dependencies: tuple[DependencyEntry, ...]


def _validity(
    profile: ProfileSpec, scope: RestrictionMap, validity: RestrictionMap, id: str, name: str
) -> AssumptionInstance | None:
    verdict = co_scope(scope, validity, profile)
    if verdict in {"equal", "narrower"}:
        return None
    kinds = [term for term in profile.assumption_kinds if term.partition("/")[2] == name]
    if len(kinds) != 1:
        raise ProfileError(f"aptness requires exactly one activated {name!r} assumption kind")
    instance = AssumptionInstance(
        kinds[0],
        {
            "record": id,
            "co_scope": verdict,
            "dimensions": ",".join(
                dimension
                for dimension, result in co_scope_by_dimension(scope, validity, profile).items()
                if result != "equal"
            ),
        },
    )
    check_instance(profile, instance)
    return instance


def check_aptness(
    profile: ProfileSpec,
    role_sort: str,
    measure: Measure,
    mapping: str | None,
    proxy: str | None,
    scope: RestrictionMap,
    records: HeldRecords,
) -> Apt:
    source = measure.observable
    if not profile.admits_measurement(source.bearer_sort, source.quantity_kind):
        raise MeasurementNotAdmitted("the source bearer and quantity kind are not admitted")
    model = None
    target = source
    if proxy is not None:
        model = read_record(records, proxy)
        if not isinstance(model, ProxyModel):
            raise MalformedRecord("the proxy reference must name a proxy model")
        if model.target.observable is not None:
            target = model.target.observable
            if not profile.admits_measurement(target.bearer_sort, target.quantity_kind):
                raise MeasurementNotAdmitted("the target bearer and quantity kind are not admitted")
            check_observable(profile, target)
    check_measure(profile, measure)
    procedure = read_record(records, measure.procedure)
    if not isinstance(procedure, Procedure):
        raise MalformedRecord("the measure's procedure reference must name a procedure")
    # Yield precedes authority reads, including a missing same_as authority.
    if source not in procedure.yields:
        raise ProcedureYieldMismatch("the procedure does not yield this complete observable")
    authority = None
    if measure.scale is not None:
        if procedure.is_authority:
            authority = procedure
        elif isinstance(procedure.scale, SameAs):
            authority = read_record(records, procedure.scale.authority)
            if not isinstance(authority, Procedure):
                raise MalformedRecord("the scale authority reference must name a procedure")
    check_measure_procedure(measure, procedure, authority)
    if model is None:
        if source.bearer_sort != role_sort:
            raise ProxyRequired("a bearer change requires a proxy model")
    else:
        allowed_procedures = {measure.procedure}
        if isinstance(procedure.scale, SameAs):
            allowed_procedures.add(procedure.scale.authority)
        if (
            model.source.observable != source
            or model.source.procedure not in allowed_procedures
            or model.target.observable is None
            or target.bearer_sort != role_sort
            or mapping is None
        ):
            raise MappingRequired("the proxy and mapping must bridge the measure to the role's bearer")
        correspondence = read_record(records, mapping)
        if not isinstance(correspondence, ReferentMapping) or not correspondence.joins(source.bearer_sort, role_sort):
            raise MappingRequired("the mapping must join the source and role bearer sorts")

    def held_rule_classes(id: str) -> str:
        rule = read_record(records, id)
        if not isinstance(rule, ClassificationRule):
            raise MalformedRecord("a scope rule reference must name a classification rule")
        return rule.classes

    check_held_rule_scope(profile, scope, classes_of=held_rule_classes)
    assumptions: list[AssumptionInstance] = []
    validity = _validity(profile, scope, procedure.validated_in, measure.procedure, "procedure-validity")
    if validity is not None:
        assumptions.append(validity)
    if model is not None:
        assert proxy is not None
        validity = _validity(profile, scope, model.validity, proxy, "proxy-validity")
        if validity is not None:
            assumptions.append(validity)
        if isinstance(model.basis, AssumptionInstance):
            check_instance(profile, model.basis)
            assumptions.append(model.basis)
    ids = [measure.procedure]
    if mapping is not None:
        ids.append(mapping)
    if proxy is not None:
        ids.append(proxy)
    unique = {v1.encode(instance_projection(instance)): instance for instance in assumptions}
    return Apt(target, tuple(unique[key] for key in sorted(unique)), dependency_closure(ids, records, profile))
