"""Validation of the declared standing route against explicit held evidence."""

from collections.abc import Callable

from beliefs.claim import Claim, Referent
from beliefs.dependencies import HeldRecords, read_record
from beliefs.errors import StandingRefused
from beliefs.estimand import MeasuredBinding
from beliefs.procedure import Procedure
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import Calibration, ProxyModel, qualify_calibration
from beliefs.restriction import co_scope
from beliefs.spec import FrozenSpec, SpecInput


def _refuse(reason: str) -> None:
    raise StandingRefused(f"standing-route-mismatch: {reason}")


def model_procedure(id: str, *, profile: ProfileSpec, records: HeldRecords) -> Procedure:
    value = read_record(records, id)
    if (
        not isinstance(value, Procedure)
        or value.kind not in profile.procedure_kinds
        or not profile.procedure_kinds[value.kind].fills_within_model
    ):
        _refuse("within-model requires a model-specification procedure kind")
    assert isinstance(value, Procedure)
    return value


def check_within_model(claim: Claim, *, profile: ProfileSpec, records: HeldRecords) -> None:
    reference = claim.roles.get("within-model")
    if reference is not None:
        assert isinstance(reference, Referent)
        model_procedure(reference.term, profile=profile, records=records)


def check_standing(
    spec: FrozenSpec,
    claim: Claim,
    *,
    profile: ProfileSpec,
    records: HeldRecords,
    empirical: Callable[[SpecInput], bool],
    assessments: Callable[[str], bool],
) -> None:
    """Check only the declared route; successful observation never changes it."""
    from beliefs.projection import claim_identity

    if spec.estimand.claim != claim_identity(claim):
        _refuse("frozen target names another claim")
    reference = claim.roles.get("within-model")
    if spec.standing == "empirical":
        if reference is not None or spec.model is not None or spec.estimand.calibration is not None:
            _refuse("empirical requires a nonmodel claim and no model or calibration")
        if not any(i.role == "observes" and i.mode == "observation" and empirical(i) for i in spec.input_roles):
            _refuse("empirical needs an observes input of mode observation with empirical standing")
        return
    if spec.model is None:
        _refuse("model route requires a model procedure")
    assert spec.model is not None
    model_procedure(spec.model, profile=profile, records=records)
    if spec.standing == "model":
        if not isinstance(reference, Referent) or reference.term != spec.model or spec.estimand.calibration is not None:
            _refuse("model must equal the within-model referent and have no calibration")
        return
    if spec.standing != "calibrated-model" or reference is not None or spec.estimand.calibration is None:
        _refuse("calibrated model requires a nonmodel claim and calibration")
    assert spec.estimand.calibration is not None
    proxy = read_record(records, spec.estimand.calibration)
    response = spec.estimand.bindings.get("response")
    if (
        not isinstance(proxy, ProxyModel)
        or not isinstance(proxy.basis, Calibration)
        or not isinstance(response, MeasuredBinding)
    ):
        _refuse("calibrated model requires a calibration proxy and measured response")
    assert (
        isinstance(proxy, ProxyModel) and isinstance(proxy.basis, Calibration) and isinstance(response, MeasuredBinding)
    )
    from beliefs import stored
    from beliefs.aptness import check_aptness

    reference = response.member if response.member is not None else claim.roles[response.role]
    assert isinstance(reference, Referent)
    target = check_aptness(
        profile,
        reference.sort,
        response.measure,
        response.mapping,
        response.proxy,
        spec.applicability.restrictions(),
        records,
        assessment_dependency=lambda id: stored.frozen_assessment_dependency(id, records=records, profile=profile),
    ).target_observable
    if proxy.source.procedure != spec.model or proxy.target.observable != target:
        _refuse("calibration source model or target observable disagrees")
    qualify_calibration(proxy, records.read, profile)
    if co_scope(spec.applicability.restrictions(), proxy.validity, profile) not in {"equal", "narrower"}:
        raise StandingRefused("calibration-scope-uncovered: prediction exceeds proxy validity")
    if proxy.basis.transfer is not None and proxy.basis.transfer not in spec.estimand.assumptions:
        _refuse("calibration transfer assumption is absent from estimand")
    if not any(
        a.kind.endswith("/calibration-transfer") and a.particulars.get("proxy") == spec.estimand.calibration
        for a in spec.estimand.assumptions
    ):
        _refuse("calibration-transfer must name the proxy")
    if not all(assessments(id) for id in proxy.basis.assessments):
        _refuse("calibration assessment is not admitted and eligible")
