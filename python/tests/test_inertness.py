"""T1 and T4: reports are boundary-minted and inert to belief."""

import dataclasses
import inspect
from pathlib import Path

from fixtures_cut3 import D_IN, closure_kwargs, report

import beliefs
from beliefs.admission import admit
from beliefs.closure import build_closure
from beliefs.dataset import ByteObservation, DatasetDeclaration, ResourceDeclaration, admission_state, dataset_address
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.report import ActReport
from beliefs.verification import Verification


def admitted_scenario():
    d = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D_IN),))
    run = RunValue(ref="run-1", spec="spec-1", inputs=(RunInput(role="observes", dataset=d),))
    assessment = AssessmentValue(
        spec="spec-1",
        run="run-1",
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="rule-1",
    )
    address = dataset_address(d)
    assert address is not None
    observations = {address: (ByteObservation(digest=D_IN, location="repo://data"),)}
    admitting = (Verification(ref="v1", assessment=assessment.identity(), scope="clean-environment", verdict="passed"),)
    return d, run, assessment, observations, admitting


def test_t4_adding_and_removing_reports_leaves_belief_admission_and_eligibility_byte_unchanged():
    d, run, assessment, observations, admitting = admitted_scenario()
    address = dataset_address(d)
    assert address is not None
    kwargs = closure_kwargs((assessment,), {"run-1": run})
    before_digest = build_closure(**kwargs).digest()
    before_admission = admit(assessment, run, observations, admitting)
    before_state = admission_state(d, observations[address])
    reports = {r.identity(): r for r in (report(), report(event_token="tok-2"))}
    assert reports  # The reports exist and reference nothing that protects them.
    after_digest = build_closure(**kwargs).digest()
    after_admission = admit(assessment, run, observations, admitting)
    after_state = admission_state(d, observations[address])
    assert after_digest == before_digest  # Byte-unchanged, not merely equal-valued.
    assert after_admission == before_admission
    assert type(after_state) is type(before_state)
    reports.clear()  # Removal is as inert as addition.
    assert build_closure(**kwargs).digest() == before_digest


def test_t4_no_belief_bearing_signature_names_a_report():
    for fn in (build_closure, admit, admission_state):
        assert not {"report", "reports", "act_report"} & set(inspect.signature(fn).parameters)
    from beliefs.belief import Records

    assert "reports" not in {field.name for field in dataclasses.fields(Records)}


def test_t4_the_belief_modules_never_import_the_report_layer():
    # Inert BY TYPE: the reference conveys neither protection nor force, and
    # the derivations cannot even see the layer (act-report §2.3).
    import beliefs.admission
    import beliefs.belief
    import beliefs.closure
    import beliefs.dataset

    for module in (beliefs.admission, beliefs.belief, beliefs.closure, beliefs.dataset):
        source = inspect.getsource(module)
        assert "beliefs.report" not in source and "beliefs.boundary" not in source


def test_t1_no_construction_path_authors_an_act_report():
    import beliefs.boundary as boundary_module
    import beliefs.report as report_module

    assert "_mint_report" not in report_module.__all__
    report_fields = {field.name for field in dataclasses.fields(ActReport)}
    distinctive = report_fields - {"actor", "observer"}
    for module in (report_module, boundary_module):
        for name in module.__all__:
            value = getattr(module, name)
            if callable(value) and not isinstance(value, type) and name != "cite":
                params = set(inspect.signature(value).parameters)
                # Approved correction: boundary metadata may name the actor and
                # observer, but no public API may accept distinctive report fields.
                assert not distinctive & params, (module.__name__, name)


def test_t1_the_constructor_is_reachable_only_from_the_boundary():
    # The one src caller of the private constructor is the boundary — the
    # in-slice form of "minted only by the boundary" (cut 3 §9 item 2).
    src = Path(beliefs.__file__).parent
    callers = [path.name for path in src.rglob("*.py") if "_mint_report" in path.read_text(encoding="utf-8")]
    assert sorted(callers) == ["boundary.py", "report.py"]
