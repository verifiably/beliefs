"""Replay eligibility, execution, conformance, equivalence, and scope.

Seed conformance validates recorded claims against the global SeedPlan. Family
coverage is deferred: RunClosure retains the workflow-definition identity, not
its family-to-stream mapping, so missing family/job/stream claims cannot be
derived from this value alone.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import final

from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run, execute_production_run
from beliefs.errors import MalformedRecord
from beliefs.recipe import REQUIRED_FOR_CLEAN_ENVIRONMENT, BoundaryReceipt, ResultManifest, RunClosure
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.spec import (
    SEED_DERIVATION_V1,
    Deterministic,
    FrozenSpec,
    RuleFixture,
    Seeded,
    StochasticUnseeded,
    derive_seed,
)

AVAILABLE = "available"
NOT_AVAILABLE = "not-available"
CONFORMING = "conforming"


@sealed
@final
@dataclass(frozen=True)
class EquivalenceImplementation:
    identity: str
    evaluate: Callable[[ResultManifest, ResultManifest], str]
    fixtures: tuple[RuleFixture, ...]

    def __post_init__(self) -> None:
        if type(self.identity) is not str or not self.identity:
            raise MalformedRecord("an equivalence implementation carries a nonempty string identity")
        if type(self.fixtures) is not tuple or any(type(fixture) is not RuleFixture for fixture in self.fixtures):
            raise MalformedRecord("equivalence fixtures must be a tuple of RuleFixture values")
        try:
            parameters = tuple(inspect.signature(self.evaluate).parameters.values())
        except (TypeError, ValueError) as error:
            raise MalformedRecord("an equivalence evaluator must expose its two-result signature") from error
        positional = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        if len(parameters) != 2 or any(
            parameter.kind not in positional or parameter.default is not inspect.Parameter.empty
            for parameter in parameters
        ):
            raise MalformedRecord("an equivalence evaluator takes exactly the original and replay results")


def _manifest_equality(original: ResultManifest, replayed: ResultManifest) -> str:
    return "passed" if original == replayed else "failed"


CONTENT_EQUALITY = EquivalenceImplementation("impl-eq-1", _manifest_equality, ())
DATASET_CONTENT_EQUALITY = EquivalenceImplementation("impl-dataset-eq-1", _manifest_equality, ())


@sealed
@final
@dataclass(frozen=True)
class CodeLineageCertification:
    rationale: str
    attribution: str

    def __post_init__(self) -> None:
        if any(type(value) is not str or not value for value in (self.rationale, self.attribution)):
            raise MalformedRecord("a code-lineage certification carries a rationale and attribution")


def replay_eligibility(
    run: RunClosure,
    *,
    resolvable_here: frozenset[str],
    attributions: Mapping[str, str],
) -> str:
    recipe = run.recipe
    required = {
        recipe.code_identity,
        recipe.environment.identity(),
        recipe.workflow_definition_identity,
        *(entry.content for entry in recipe.inputs),
    }
    return AVAILABLE if required <= resolvable_here and run.address() in attributions else NOT_AVAILABLE


def replay(
    original: RunMinted,
    *,
    port: OperationPort,
    spec: FrozenSpec | None,
    definition: WorkflowDefinition,
    code_roots: tuple[Path, ...],
    held_inputs: Mapping[str, Path],
    entrypoint: str,
    targets: tuple[str, ...],
    declared_outputs: tuple[str, ...],
    actor: str,
    observer: str,
    started_at: str,
    host_realization: str,
    scratch_base: Path,
    cores: int = 1,
) -> RunMinted | RunRefused:
    common = {
        "definition": definition,
        "code_roots": code_roots,
        "held_inputs": held_inputs,
        "entrypoint": entrypoint,
        "targets": targets,
        "declared_outputs": declared_outputs,
        "actor": actor,
        "observer": observer,
        "started_at": started_at,
        "host_realization": host_realization,
        "scratch_base": scratch_base,
        "cores": cores,
        "port": port,
        "boundary_policy": original.run.recipe.boundary_policy,
    }
    recipe = original.run.recipe
    common["expected_recipe_identity"] = recipe.identity()
    if recipe.shape == "assessment":
        outcome = execute_assessment_run(spec=spec, **common)
    else:
        outcome = execute_production_run(
            inputs=recipe.inputs,
            parameters=recipe.parameters,
            nondeterminism=recipe.nondeterminism,
            **common,
        )
    return outcome


def byte_tolerance_rule(store: Mapping[str, bytes]) -> EquivalenceImplementation:
    tolerance = Decimal("0.000001")

    def evaluate(original: ResultManifest, replayed: ResultManifest) -> str:
        left = dict(original.outputs)
        right = dict(replayed.outputs)
        if left.keys() != right.keys():
            return "failed"
        try:
            for name in left:
                a = Decimal(store[left[name]].decode("utf-8"))
                b = Decimal(store[right[name]].decode("utf-8"))
                if not a.is_finite() or not b.is_finite():
                    return "inconclusive"
                if abs(a - b) > tolerance:
                    return "failed"
        except Exception:  # noqa: BLE001 — any artifact-reader or payload failure is inconclusive
            return "inconclusive"
        return "passed"

    return EquivalenceImplementation(
        identity="impl-tolerance-1e-6",
        evaluate=evaluate,
        fixtures=(),
    )


def conformance(run: RunClosure) -> str:
    """Validate every recorded seed claim; do not infer unrecorded family coverage."""
    contract = run.recipe.nondeterminism
    realized = run.occurrence.realized_seeds.seeds
    if type(contract) is StochasticUnseeded:
        return CONFORMING
    if type(contract) is Deterministic:
        if realized:
            return f"non-conforming: deterministic recipe reported seeds for {min(realized)!r}"
        return CONFORMING

    if type(contract) is not Seeded:
        return "non-conforming: unknown nondeterminism contract"
    plan = contract.plan
    if plan.derivation_rule != SEED_DERIVATION_V1:
        return f"non-conforming: unsupported seed derivation rule {plan.derivation_rule!r}"

    streams = set(plan.streams)
    for job, claims in sorted(realized.items()):
        for stream, actual in sorted(claims.items()):
            if stream not in streams:
                return f"non-conforming: job {job!r} names undeclared stream {stream!r}"
            expected = derive_seed(plan.roots[plan.stream_roots[stream]], job, stream)
            if actual != expected:
                return f"non-conforming: job {job!r} stream {stream!r} realized {actual}, expected {expected}"
    return CONFORMING


def qualifies(receipt: BoundaryReceipt, environment_identity: str) -> bool:
    """§7.3a over the closed vocabulary — containment, never an ordering — plus
    the fresh-instance conjunct, bound to the replayed recipe's environment
    (design §7.1). Reads the receipt only; a policy's identity string is
    nothing here."""
    if type(receipt) is not BoundaryReceipt:
        raise MalformedRecord("qualification reads a BoundaryReceipt")
    if receipt.instance is None:
        return False
    if not set(REQUIRED_FOR_CLEAN_ENVIRONMENT) <= set(receipt.capabilities):
        return False
    return receipt.instance.environment_identity == environment_identity


def derive_scope(
    original: RunClosure,
    replayed: RunClosure,
    *,
    certification: CodeLineageCertification | None,
) -> str:
    """Walk every row of §7.3."""
    if conformance(original) != CONFORMING or conformance(replayed) != CONFORMING:
        return "not-certified"
    if original.recipe.identity() == replayed.recipe.identity():
        if qualifies(replayed.occurrence.receipt, replayed.recipe.environment.identity()):
            return "clean-environment"
        return "same-environment"
    left = original.recipe
    right = replayed.recipe
    left_observes = {entry.content for entry in left.inputs if entry.role == "observes"}
    right_observes = {entry.content for entry in right.inputs if entry.role == "observes"}
    if (
        left.spec_identity is not None
        and left.spec_identity == right.spec_identity
        and left_observes == right_observes
        and left.code_identity != right.code_identity
        and type(certification) is CodeLineageCertification
    ):
        return "independent-implementation"
    return "not-certified"


derive_scope.__doc__ = """Derive verification scope from two conforming closures — every row of
§7.3. The `clean-environment` row is reached only through the replay's
receipt qualifying under §7.3a (conformance cut 13); the original's receipt is
not read, because the requirement is that the replay ran through the boundary.
"""
