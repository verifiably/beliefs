"""Shared closure and report builders for the intent-boundary tests."""

from decimal import Decimal
from pathlib import PurePosixPath  # noqa: F401 — builders below

from beliefs.recipe import (
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentManifest,
    Invocation,
    LaunchAttestation,
    Occurrence,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    WorkflowDefinitionSnapshot,
)
from beliefs.report import ActReport, Entry, RunAttemptEntry, RunRefusal, _mint_report
from beliefs.spec import Deterministic, RealizedSeeds


def make_closure(
    *, shape: str = "assessment", parameters=None, spec: str | None = "s" * 64, token: str = "tok"
) -> RunClosure:
    """Build a closure with two outputs and both eligible input roles."""
    eligible = "observes" if shape == "assessment" else "transforms"
    inputs = (
        RecipeInput(
            role=eligible,
            dataset="dataset:" + "1" * 64,
            content="sha256:" + "2" * 64,
        ),
        RecipeInput(
            role="reads",
            dataset="dataset:" + "3" * 64,
            content="sha256:" + "4" * 64,
        ),
    )
    recipe = Recipe(
        shape=shape,
        spec_identity=spec if shape == "assessment" else None,
        code_identity="sha256:" + "5" * 64,
        environment=EnvironmentManifest(
            artifacts=(("/science/env/python/bin/python3", "file", "sha256:" + "6" * 64),)
        ),
        workflow_definition=WorkflowDefinitionSnapshot(
            snakefile_digest="sha256:" + "7" * 64,
            family_streams={},
            checkpoint_expanded_families=(),
        ),
        invocation=Invocation(
            entrypoint="code/workflow/Snakefile",
            targets=("out-a", "out-b"),
            bindings=("inputs",),
            declared_outputs=("out-a", "out-b"),
        ),
        inputs=inputs,
        parameters=(
            parameters if parameters is not None else {"threshold": Decimal("0.5")}
        ),
        nondeterminism=Deterministic(),
        boundary_policy=BoundaryPolicy(
            identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1"
        ),
        rule_bindings=(("rule:eq", "impl-1"),),
    )
    result = ResultManifest(
        outputs=(
            ("out-a", "sha256:" + "8" * 64),
            ("out-b", "sha256:" + "9" * 64),
        )
    )
    occurrence = Occurrence(
        event_token=token,
        started_at="2026-08-27T00:00:00Z",
        actor="tester",
        host_realization="host-a",
        trace=(),
        planned=(),
        realized_seeds=RealizedSeeds({}),
        receipt=BoundaryReceipt(
            planning=LaunchAttestation(
                scratch_mapping="/scratch", argv=("snakemake",), rendered_config=(("threshold", "0.5"),)
            ),
            execution=LaunchAttestation(
                scratch_mapping="/scratch", argv=("snakemake",), rendered_config=(("threshold", "0.5"),)
            ),
        ),
    )
    return RunClosure(recipe=recipe, result=result, occurrence=occurrence)


def sample_report(*, operation: str = "run-attempt", token: str = "tok") -> ActReport:
    entries: tuple[Entry, ...] = (
        RunAttemptEntry("subject", RunRefusal("execution-failed")),
    )
    return _mint_report(
        operation=operation,
        event_token=token,
        actor="tester",
        observer="observer-1",
        instrument="beliefs.boundary/v1",
        opened_at="2026-08-27T00:00:00Z",
        closed_at="2026-08-27T00:00:00Z",
        entries=entries,
    )
