"""Test-local inventory. None of these nine rows is a spectral admission proposal.

joint-payload/joint-law: declared parameters over-certify response transformations;
procedure-spec/model-specification: type the within-model route, not a real model;
calibration-transfer: names a synthetic proxy, grants no calibrated validity;
calibration-agreement/agreement-on-series/agreement-correlation: construct only the
synthetic supported/empirical typing basis required by qualify_calibration;
monotone-increasing: deliberately tests over-certification on this same profile.
"""

from dataclasses import replace
from decimal import Decimal
from typing import Literal

from candidate_contracts import fragment

from beliefs import stored
from beliefs.assumptions import AssumptionInstance
from beliefs.claim import Claim, Referent, build_claim
from beliefs.contract.base import BaseContract
from beliefs.contract.domain import DomainContract, parse_domain_contract
from beliefs.estimand import Control, Estimand, MeasuredBinding, OutputSpec, ValueReference, build_estimand
from beliefs.procedure import ModelInputs, SameAs, procedure_from_stored
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.proxy_model import Calibration, ProxyModel, ProxySource, ProxyTarget
from beliefs.resolution import build_snapshot
from beliefs.spec import Deterministic, FrozenSpec, SpecDraft, freeze
from beliefs.target import AssessedTarget

from .fixtures import Records
from .spectral_case import OBSERVABLE, SpectralCase, build_quantity, fixture_rules, spectral_case
from .test_authoring import input_roles

SOURCE = "urn:beliefs:definitions:synthetic-spectral-diagnostics"


def diagnostic_contract(base: BaseContract) -> DomainContract:
    properties = dict(fragment("general-spectral")["rows"]["functionals"]["peak-power-fraction"])
    properties.update(
        output="declared",
        response_transformation="by-parameters",
        domain="not-applicable",
        definition="Diagnostic payload shape only; dimensionless parameters over-certify spectral invariance.",
        parameters={
            "rho": {"typing": "dimensionless", "domain": "unit-interval"},
            "exponent": {"typing": "dimensionless", "domain": "real"},
        },
    )
    agreement = {
        "form": "association",
        "arity": "two",
        "response_transformation": "fixed",
        "response_reversal": "not-applicable",
        "reversal": "not-applicable",
        "exchange": "symmetric",
        "ties": "midrank",
        "output": "dimensionless",
        "domain": "signed-unit-interval",
        "null": "zero",
        "increment": "not-applicable",
        "uncertainty": "none",
        "parameters": "not-applicable",
    }
    return parse_domain_contract(
        {
            "contract": "spectral-checks",
            "version": 1,
            "lineage": "genesis",
            "defining_source": {"id": SOURCE},
            "sorts": {"procedure-spec": {"binding": {"kind": "world-kind", "world_kind": "procedure"}}},
            "dimensions": {},
            "functionals": {
                "joint-payload": properties,
                "joint-law": {**properties, "form": "law-parameters", "arity": "not-applicable"},
                "agreement-correlation": agreement,
            },
            "procedure_kinds": {"model-specification": {"fills_within_model": True}},
            "assumption_kinds": {
                "calibration-transfer": {
                    "collapses": "Synthetic typing agreement is carried through a named proxy; no real calibration is claimed.",
                    "particulars": ["proxy"],
                }
            },
            "templates": {
                "calibration-agreement": {
                    "roles": {"series": {"arity": "one"}},
                    "sign_apt": False,
                    "layers": ["statistical"],
                    "forms": ["polar"],
                }
            },
            "instantiations": {
                "agreement-on-series": {
                    "template": "calibration-agreement",
                    "roles": {"series": ["general/series-view"]},
                }
            },
            "estimands": {"instantiation:agreement-on-series": {"forms": ["association"], "conditioning_sorts": []}},
            "transformations": {
                "monotone-increasing": {
                    "kind": "monotone",
                    "direction": "increasing",
                    "fixed": True,
                    "domain": "real",
                    "invertible": True,
                }
            },
        },
        source="<synthetic spectral diagnostics, never shipped>",
        base=base,
        predecessor=None,
    )


def diagnostic_estimand(case: SpectralCase, *, form: Literal["quantity", "law-parameters"]) -> Estimand:
    bindings = {"response": MeasuredBinding("series", None, case.measure, None, None, case.series)}
    if form == "law-parameters":
        bindings["independent"] = ()
    return build_estimand(
        case.profile,
        case.claim,
        form=form,
        functional="spectral-checks/joint-payload" if form == "quantity" else "spectral-checks/joint-law",
        bindings=bindings,
        outputs={"rho": OutputSpec("dimensionless", "unit-interval"), "exponent": OutputSpec("dimensionless", "real")},
        reference={"rho": ValueReference(Decimal(0)), "exponent": ValueReference(Decimal(0))},
        control=Control("general/observational", (), "general/single-record-summary", "general/explicit-series-view"),
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=case.applicability,
        snapshot=build_snapshot(),
        records=case.case.records,
        series_evidence=case.case.evidence(),
    )[0]


def model_case(profile: ProfileSpec, *, calibrated: bool = False) -> tuple[FrozenSpec, Claim, Records, str | None]:
    """Synthetic model/basis labels exercise typing and current eligibility callbacks only."""
    s = spectral_case(profile)
    records = s.case.records
    assay = procedure_from_stored(records.nodes[s.measuring])
    model = stored.procedure_node(
        replace(
            assay,
            kind="spectral-checks/model-specification",
            name="Synthetic model",
            scale=SameAs(s.measuring),
            inputs=ModelInputs((), ()),
        )
    )
    records.nodes[model.id] = model
    model_measure = replace(s.measure, procedure=model.id)
    claim = (
        s.claim
        if calibrated
        else build_claim(
            profile,
            operator=s.claim.operator,
            roles={**s.claim.roles, "within-model": Referent("spectral-checks/procedure-spec", model.id)},
            form="polar",
            layer="statistical",
        )
    )
    basis_id = None
    if calibrated:
        agreement = build_claim(
            profile,
            operator="spectral-checks/calibration-agreement",
            roles=s.claim.roles,
            form="polar",
            layer="statistical",
        )
        basis_e, _ = build_estimand(
            profile,
            agreement,
            form="association",
            functional="spectral-checks/agreement-correlation",
            bindings={
                "variables": (
                    ("model", MeasuredBinding("series", None, model_measure, None, None)),
                    ("observed", MeasuredBinding("series", None, s.measure, None, None)),
                )
            },
            outputs={"estimate": OutputSpec("dimensionless", "signed-unit-interval")},
            reference=ValueReference(Decimal(0)),
            control=Control(
                "general/observational", (), "general/single-record-summary", "general/explicit-series-view"
            ),
            uncertainty="interval",
            assumptions=(),
            calibration=None,
            applicability=s.applicability,
            snapshot=build_snapshot(),
            records=records,
        )
        basis_args = {
            "title": "Synthetic typing-only agreement, never published evidence",
            "spec": "synthetic-basis",
            "run": "run:" + "b" * 64,
            "proposition": "proposition:" + claim_identity(agreement),
            "outcome": "supported",
            "interpretation_rule": "spectral-typing-agreement/v1",
            "target": AssessedTarget(basis_e, s.applicability, basis_e.dependencies, None, "empirical"),
        }
        initial = stored.assessment_node("c" * 64, **basis_args)
        basis_id = stored.assessment_value(initial, profile=profile).identity()
        basis = stored.assessment_node(basis_id, **basis_args)
        records.nodes[basis.id] = basis
        basis_id = basis.id
        proxy = stored.proxy_model_node(
            ProxyModel(
                ProxySource(OBSERVABLE, model.id),
                ProxyTarget(OBSERVABLE, None),
                {},
                Calibration(OBSERVABLE, (basis.id,), ("spectral-typing-agreement/v1",), None),
                None,
            )
        )
        records.nodes[proxy.id] = proxy
        callback = lambda id: stored.frozen_assessment_dependency(id, records=records, profile=profile)
        e, _ = build_estimand(
            profile,
            claim,
            form="quantity",
            functional="general/peak-power-fraction",
            bindings={"response": MeasuredBinding("series", None, model_measure, None, None, s.series)},
            outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
            reference=ValueReference(Decimal(0)),
            control=Control(
                "general/observational", (), "general/single-record-summary", "general/explicit-series-view"
            ),
            uncertainty="interval",
            assumptions=(AssumptionInstance("spectral-checks/calibration-transfer", {"proxy": proxy.id}),),
            calibration=proxy.id,
            applicability=s.applicability,
            snapshot=build_snapshot(),
            records=records,
            assessment_dependency=callback,
            series_evidence=s.case.evidence(),
        )
    else:
        e = build_quantity(
            replace(s, claim=claim, measure=model_measure),
            functional="general/peak-power-fraction",
            reference=ValueReference(Decimal(0)),
        )
        callback = None
    draft = SpecDraft(
        target="proposition:" + claim_identity(claim),
        estimand=e,
        method="Synthetic standing-route apparatus",
        assumptions="No scientific calibration or empirical admission.",
        falsification="Typing only",
        input_roles=input_roles(e),
        applicability=s.applicability,
        interpretation_rule="spectral-fixture-inconclusive/v1",
        equivalence_rule="content-identity-equality/v1",
        parameters={},
        nondeterminism=Deterministic(),
        registers=(),
        standing="calibrated-model" if calibrated else "model",
        model=model.id,
    )
    spec = freeze(
        draft,
        held_rules=fixture_rules(),
        rule_procedures={draft.interpretation_rule: s.estimator},
        profile=profile,
        claim=claim,
        records=records,
        assessment_dependency=callback,
        series_evidence=s.case.evidence(),
    )
    return spec, claim, records, basis_id
