"""Recipe, occurrence, result, and run-closure values."""

from __future__ import annotations

import posixpath
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import cast, final

from beliefs.errors import (
    BoundaryPolicyUnsupported,
    CanonicalTextRefused,
    MalformedClosure,
    MalformedRecord,
    UnsafeInvocation,
)
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.spec import (
    Deterministic,
    ExclusionCertification,
    FrozenSpec,
    RealizedSeeds,
    Seeded,
    SeedPlan,
    StochasticUnseeded,
)

__all__ = [
    "ARTIFACT_KINDS",
    "ASSESSMENT_ROLES",
    "BOUNDARY_RECEIPT_DOMAIN",
    "CAPABILITIES",
    "CONFINED_POLICY",
    "CONFINED_RECEIPT_DOMAIN",
    "CONFINED_RUN_DOMAIN",
    "ENVIRONMENT_DOMAIN",
    "MINIMAL_POLICY",
    "MOUNT_PLAN_DOMAIN",
    "NAMESPACES",
    "PRODUCTION_ROLES",
    "RECIPE_DOMAIN",
    "REQUIRED_FOR_CLEAN_ENVIRONMENT",
    "RUN_DOMAIN",
    "SHAPES",
    "SUPPORTED_POLICIES",
    "WORKFLOW_DEFINITION_DOMAIN",
    "BoundaryPolicy",
    "BoundaryReceipt",
    "EnvironmentManifest",
    "EnvironmentReference",
    "ExclusionCertification",
    "InstanceAttestation",
    "Invocation",
    "LaunchAttestation",
    "Occurrence",
    "PlannedJob",
    "Recipe",
    "RecipeInput",
    "ResultManifest",
    "RunClosure",
    "TraceJob",
    "WorkflowDefinitionSnapshot",
    "job_key",
    "mount_plan_identity",
    "project_recipe",
    "run_domain_for",
    "run_domain_for_projection",
    "supported_policy",
]

RECIPE_DOMAIN = "science.recipe.v2"
RUN_DOMAIN = "science.run.v1"
CONFINED_RUN_DOMAIN = "science.run.v2"
ENVIRONMENT_DOMAIN = "science.environment.v2"
BOUNDARY_RECEIPT_DOMAIN = "science.boundary-receipt.v3"
CONFINED_RECEIPT_DOMAIN = "science.boundary-receipt.v4"
MOUNT_PLAN_DOMAIN = "science.mount-plan.v1"
WORKFLOW_DEFINITION_DOMAIN = "science.workflow-definition.v2"

#: §7.3a's three capabilities — the closed vocabulary a policy may name.
CAPABILITIES = ("from-bundle", "closure-confined-filesystem", "network-denied")
#: What `clean-environment` requires — spelled separately, never derived from
#: CAPABILITIES, so a capability added later does not become a requirement.
REQUIRED_FOR_CLEAN_ENVIRONMENT = tuple(["from-bundle", "closure-confined-filesystem", "network-denied"])  # noqa: C409
ARTIFACT_KINDS = ("file", "symlink")
RENDERED_KINDS = ("file", "symlink", "value")
NAMESPACES = ("cgroup", "ipc", "mnt", "net", "pid", "user", "uts")
MOUNT_ACCESS = ("ro", "rw")

SHAPES = ("assessment", "dataset-production")
ASSESSMENT_ROLES = ("observes", "reads")
PRODUCTION_ROLES = ("transforms", "reads")


def _require_str(value: object, where: str) -> None:
    if type(value) is not str:
        raise MalformedClosure(f"{where} must be a string")


def _require_component(value: object, where: str) -> None:
    _require_str(value, where)
    if value in ("", "unknown", "attested"):
        raise MalformedClosure(f"{where} must carry a held component identity, not {value!r}")


def _freeze_parameter_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_parameter_value(member) for key, member in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_parameter_value(member) for member in value)
    return value


def _project_parameter_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _project_parameter_value(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_project_parameter_value(member) for member in value]
    return value


def _require_tuple(value: object, where: str) -> None:
    if type(value) is not tuple:
        raise MalformedClosure(f"{where} must be a tuple")


def _require_strings(value: object, where: str) -> None:
    _require_tuple(value, where)
    if not all(type(member) is str for member in cast(tuple[object, ...], value)):
        raise MalformedClosure(f"{where} must contain strings only")


def _require_pairs(value: object, where: str) -> None:
    _require_tuple(value, where)
    if not all(
        type(row) is tuple and len(row) == 2 and all(type(member) is str for member in row)
        for row in cast(tuple[object, ...], value)
    ):
        raise MalformedClosure(f"{where} must contain (string, string) pairs only")


def _require_triples(value: object, where: str) -> None:
    _require_tuple(value, where)
    if not all(
        type(row) is tuple and len(row) == 3 and all(type(member) is str for member in row)
        for row in cast(tuple[object, ...], value)
    ):
        raise MalformedClosure(f"{where} must contain (string, string, string) triples only")


def _triples(rows: tuple[tuple[str, str, str], ...]) -> list[list[str]]:
    return [list(row) for row in sorted(rows)]


def _require_nondeterminism(value: object) -> None:
    if type(value) is Deterministic:
        return
    if type(value) is StochasticUnseeded:
        _require_str(value.rationale, "stochastic-unseeded rationale")
        return
    if type(value) is not Seeded or type(value.plan) is not SeedPlan:
        raise MalformedClosure("recipe nondeterminism must be a frozen spec variant")
    plan = value.plan
    _require_str(plan.derivation_rule, "seed derivation rule")
    _require_strings(plan.streams, "seed streams")
    if not isinstance(plan.roots, Mapping) or not all(
        type(name) is str and type(seed) is int for name, seed in plan.roots.items()
    ):
        raise MalformedClosure("seed roots must map strings to integers")
    if not isinstance(plan.stream_roots, Mapping) or not all(
        type(stream) is str and type(root) is str for stream, root in plan.stream_roots.items()
    ):
        raise MalformedClosure("seed stream roots must map strings to strings")


def _pairs(rows: tuple[tuple[str, str], ...]) -> list[list[str]]:
    return [list(row) for row in sorted(rows)]


@sealed
@final
@dataclass(frozen=True)
class RecipeInput:
    role: str
    dataset: str
    content: str
    exclusion: ExclusionCertification | None = None

    def __post_init__(self) -> None:
        _require_str(self.role, "input role")
        _require_str(self.dataset, "input dataset")
        _require_component(self.content, "input content")
        if self.exclusion is not None:
            if type(self.exclusion) is not ExclusionCertification:
                raise MalformedClosure("input exclusion must be an ExclusionCertification")
            _require_str(self.exclusion.rationale, "exclusion rationale")
            _require_str(self.exclusion.attribution, "exclusion attribution")
        if self.exclusion is not None and self.role != "reads":
            raise MalformedClosure("an exclusion certification is carried by a `reads` input only")


@sealed
@final
@dataclass(frozen=True)
class Invocation:
    entrypoint: str
    targets: tuple[str, ...]
    bindings: tuple[str, ...]
    declared_outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_str(self.entrypoint, "invocation entrypoint")
        for name, values in (
            ("targets", self.targets),
            ("bindings", self.bindings),
            ("declared_outputs", self.declared_outputs),
        ):
            _require_strings(values, f"invocation {name}")
        if any(target.startswith("-") for target in self.targets):
            raise UnsafeInvocation("an option-like target is not a workflow target")
        for output in self.declared_outputs:
            depth = 0
            if PurePosixPath(output).is_absolute():
                raise UnsafeInvocation(f"declared output {output!r} is absolute")
            for segment in output.split("/"):
                if segment == "..":
                    depth -= 1
                elif segment not in ("", "."):
                    depth += 1
                if depth < 0:
                    raise UnsafeInvocation(f"declared output {output!r} escapes the run root")
        if len(set(self.declared_outputs)) != len(self.declared_outputs):
            raise MalformedClosure("duplicate logical names in declared outputs")


@sealed
@final
@dataclass(frozen=True)
class EnvironmentManifest:
    """The runtime artifact closure, one row per file: (sandbox path, kind,
    digest or link target). Host paths never enter it (design §4.1). Every
    path is normalized — absolute, no `.`, `..` or empty components — so a
    join under a snapshot root can never leave it."""

    artifacts: tuple[tuple[str, str, str], ...]

    def __post_init__(self) -> None:
        _require_triples(self.artifacts, "environment artifacts")
        paths = [path for path, _, _ in self.artifacts]
        if len(set(paths)) != len(paths):
            raise MalformedClosure("environment artifacts name each sandbox path once")
        for path, kind, content in self.artifacts:
            if not path.startswith("/") or path.startswith("//") or posixpath.normpath(path) != path:
                raise MalformedClosure(f"environment artifact {path!r} is not a normalized absolute sandbox path")
            if kind not in ARTIFACT_KINDS:
                raise MalformedClosure(f"environment artifact {path!r} has kind {kind!r}, outside {ARTIFACT_KINDS}")
            if not content:
                raise MalformedClosure(f"environment artifact {path!r} carries no content")

    def identity(self) -> str:
        return v1.digest(ENVIRONMENT_DOMAIN, {"artifacts": _triples(self.artifacts)})


@sealed
@final
@dataclass(frozen=True)
class EnvironmentReference:
    """The identity-only environment evidence available in a decoded recipe."""

    identity_value: str

    def __post_init__(self) -> None:
        _require_component(self.identity_value, "environment identity")

    def identity(self) -> str:
        return self.identity_value


@sealed
@final
@dataclass(frozen=True)
class BoundaryPolicy:
    identity: str
    scope_rule: str
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_str(self.identity, "boundary policy identity")
        _require_str(self.scope_rule, "boundary policy scope rule")
        _require_strings(self.capabilities, "boundary policy capabilities")
        if any(capability not in CAPABILITIES for capability in self.capabilities):
            raise MalformedClosure(f"boundary policy capabilities are outside the closed vocabulary {CAPABILITIES}")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise MalformedClosure("boundary policy capabilities name each capability once")


MINIMAL_POLICY = BoundaryPolicy(identity="boundary-policy/minimal-v1", scope_rule="scope-derivation/v1")
CONFINED_POLICY = BoundaryPolicy(
    identity="boundary-policy/confined-v1",
    scope_rule="scope-derivation/v1",
    capabilities=CAPABILITIES,
)
SUPPORTED_POLICIES = (MINIMAL_POLICY, CONFINED_POLICY)


def supported_policy(policy: object) -> BoundaryPolicy:
    """The entire definition — identity, scope rule and capability *set* —
    must equal one of the two the boundary knows; the canonical known value is
    returned, so a reordered spelling of a known set carries on as the
    definition it names (design §3)."""
    if type(policy) is not BoundaryPolicy:
        raise BoundaryPolicyUnsupported("the boundary policy must be a BoundaryPolicy value")
    for known in SUPPORTED_POLICIES:
        if (policy.identity, policy.scope_rule, frozenset(policy.capabilities)) == (known.identity, known.scope_rule, frozenset(known.capabilities)):
            return known
    raise BoundaryPolicyUnsupported(
        f"{policy.identity!r} with scope rule {policy.scope_rule!r} and capabilities "
        f"{policy.capabilities} matches no known definition"
    )


@sealed
@final
@dataclass(frozen=True)
class Recipe:
    shape: str
    spec_identity: str | None
    code_identity: str
    environment: EnvironmentManifest | EnvironmentReference
    workflow_definition: WorkflowDefinitionSnapshot
    invocation: Invocation
    inputs: tuple[RecipeInput, ...]
    parameters: Mapping[str, object]
    nondeterminism: Deterministic | Seeded | StochasticUnseeded
    boundary_policy: BoundaryPolicy
    rule_bindings: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_str(self.shape, "recipe shape")
        if self.shape not in SHAPES:
            raise MalformedClosure(f"recipe shape {self.shape!r} is outside {SHAPES}")
        if self.spec_identity is not None:
            _require_str(self.spec_identity, "spec identity")
        if self.shape == "assessment" and self.spec_identity is None:
            raise MalformedClosure("an assessment recipe carries its frozen spec identity")
        if self.shape == "dataset-production" and self.spec_identity is not None:
            raise MalformedClosure("a dataset-production recipe has no assessment spec identity")
        if type(self.environment) is not EnvironmentManifest:  # noqa: SIM102 - frozen cut-3 mutation seam
            if type(self.environment) is not EnvironmentReference:
                raise MalformedClosure("environment must be an EnvironmentManifest or decoded EnvironmentReference")
        if type(self.invocation) is not Invocation:
            raise MalformedClosure("invocation must be an Invocation")
        if type(self.boundary_policy) is not BoundaryPolicy:
            raise MalformedClosure("boundary_policy must be a BoundaryPolicy")
        _require_tuple(self.inputs, "recipe inputs")
        _require_pairs(self.rule_bindings, "recipe rule bindings")
        rules = [rule for rule, _ in self.rule_bindings]
        if len(rules) != len(set(rules)):
            raise MalformedClosure("recipe rule bindings must name each logical rule once")
        if not all(type(entry) is RecipeInput for entry in self.inputs):
            raise MalformedClosure("recipe inputs hold RecipeInput values only")
        roles = ASSESSMENT_ROLES if self.shape == "assessment" else PRODUCTION_ROLES
        if any(entry.role not in roles for entry in self.inputs):
            raise MalformedClosure(f"an input role is outside the {self.shape} partition {roles}")
        if not isinstance(self.parameters, Mapping):
            raise MalformedClosure("recipe parameters must be a mapping")
        _require_nondeterminism(self.nondeterminism)
        _require_component(self.code_identity, "code identity")
        if type(self.workflow_definition) is not WorkflowDefinitionSnapshot:
            raise MalformedClosure("workflow definition must be a WorkflowDefinitionSnapshot")
        parameters = MappingProxyType({key: _freeze_parameter_value(value) for key, value in self.parameters.items()})
        v1.encode(_project_parameter_value(parameters))
        object.__setattr__(
            self,
            "parameters",
            parameters,
        )

    def _projection(self) -> dict[str, object]:
        inputs = []
        for entry in sorted(
            self.inputs,
            key=lambda value: (
                value.role,
                value.dataset,
                value.content,
                value.exclusion.rationale if value.exclusion else "",
                value.exclusion.attribution if value.exclusion else "",
            ),
        ):
            row: dict[str, object] = {
                "role": entry.role,
                "dataset": entry.dataset,
                "content": entry.content,
            }
            if entry.exclusion is not None:
                row["exclusion"] = {
                    "rationale": entry.exclusion.rationale,
                    "attribution": entry.exclusion.attribution,
                }
            inputs.append(row)
        projection: dict[str, object] = {
            "shape": self.shape,
            "code_identity": self.code_identity,
            "environment": self.environment.identity(),
            "workflow_definition": self.workflow_definition.projection(),
            "invocation": {
                "entrypoint": self.invocation.entrypoint,
                "targets": list(self.invocation.targets),
                "bindings": list(self.invocation.bindings),
                "declared_outputs": list(self.invocation.declared_outputs),
            },
            "inputs": inputs,
            "parameters": _project_parameter_value(self.parameters),
            "nondeterminism": self.nondeterminism.projection(),
            "boundary_policy": {
                "identity": self.boundary_policy.identity,
                "scope_rule": self.boundary_policy.scope_rule,
                "capabilities": sorted(self.boundary_policy.capabilities),
            },
            "rule_bindings": _pairs(self.rule_bindings),
        }
        if self.spec_identity is not None:
            projection["spec_identity"] = self.spec_identity
        # Scheduling options have no recipe member: they cannot become a second
        # parameter channel or alter the recorded closure.
        return projection

    def identity(self) -> str:
        return v1.digest(RECIPE_DOMAIN, self._projection())


def project_recipe(
    spec: FrozenSpec,
    *,
    held: Mapping[str, str],
    code_identity: str,
    environment: EnvironmentManifest,
    workflow_definition: WorkflowDefinitionSnapshot,
    invocation: Invocation,
    boundary_policy: BoundaryPolicy,
) -> Recipe:
    if type(spec) is not FrozenSpec:
        raise MalformedClosure("project_recipe requires a FrozenSpec")
    try:
        inputs = tuple(
            RecipeInput(
                role=entry.role,
                dataset=entry.dataset,
                content=held[entry.dataset],
                exclusion=entry.exclusion,
            )
            for entry in spec.input_roles
        )
    except KeyError as error:
        raise MalformedClosure(f"declared input {error.args[0]!r} is not held") from error
    return Recipe(
        shape="assessment",
        spec_identity=spec.identity,
        code_identity=code_identity,
        environment=environment,
        workflow_definition=workflow_definition,
        invocation=invocation,
        inputs=inputs,
        parameters=spec.parameters,
        nondeterminism=spec.nondeterminism,
        boundary_policy=boundary_policy,
        rule_bindings=spec.rule_bindings,
    )


@sealed
@final
@dataclass(frozen=True)
class ResultManifest:
    outputs: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _require_pairs(self.outputs, "result outputs")
        names = [name for name, _ in self.outputs]
        if len(set(names)) != len(names):
            raise MalformedClosure("duplicate logical names in result manifest")


@sealed
@final
@dataclass(frozen=True)
class WorkflowDefinitionSnapshot:
    snakefile_digest: str
    family_streams: Mapping[str, tuple[str, ...]]
    checkpoint_expanded_families: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.snakefile_digest) is not str or not self.snakefile_digest.startswith("sha256:"):
            raise MalformedClosure("a workflow definition snapshot carries a sha256 snakefile digest")
        if not isinstance(self.family_streams, Mapping) or not all(
            type(family) is str and type(streams) is tuple and all(type(stream) is str for stream in streams)
            for family, streams in self.family_streams.items()
        ):
            raise MalformedClosure("workflow family streams must map strings to tuples of strings")
        if type(self.checkpoint_expanded_families) is not tuple or any(
            type(family) is not str for family in self.checkpoint_expanded_families
        ):
            raise MalformedClosure("checkpoint-expanded families are a tuple of strings")
        object.__setattr__(self, "family_streams", MappingProxyType(dict(self.family_streams)))

    def projection(self) -> dict[str, object]:
        return {
            "snakefile": self.snakefile_digest,
            "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},
            "checkpoint_expanded_families": sorted(self.checkpoint_expanded_families),
        }

    def identity(self) -> str:
        return v1.digest(WORKFLOW_DEFINITION_DOMAIN, self.projection())


def job_key(rule: str, wildcards: tuple[tuple[str, str], ...]) -> str:
    """Return canonical text over a rule name and its wildcard binding."""
    _require_str(rule, "job key rule")
    _require_pairs(wildcards, "job key wildcards")
    names = [name for name, _ in wildcards]
    if len(names) != len(set(names)):
        raise MalformedClosure("job key wildcards name each binding once")
    return v1.encode({"rule": rule, "wildcards": {name: value for name, value in wildcards}}).decode("utf-8")


@sealed
@final
@dataclass(frozen=True)
class TraceJob:
    job_id: str
    rule: str
    wildcards: tuple[tuple[str, str], ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_str(self.job_id, "trace job id")
        _require_str(self.rule, "trace rule")
        _require_pairs(self.wildcards, "trace job wildcards")
        job_key(self.rule, self.wildcards)
        _require_strings(self.inputs, "trace job inputs")
        _require_strings(self.outputs, "trace job outputs")

    def job_key(self) -> str:
        return job_key(self.rule, self.wildcards)


@sealed
@final
@dataclass(frozen=True)
class PlannedJob:
    job_key: str
    family: str
    outputs: tuple[str, ...]
    is_checkpoint: bool

    def __post_init__(self) -> None:
        _require_str(self.job_key, "planned job key")
        _require_str(self.family, "planned job family")
        _require_strings(self.outputs, "planned job outputs")
        if type(self.is_checkpoint) is not bool:
            raise MalformedClosure("planned job checkpoint flag must be a boolean")
        try:
            parsed = v1.decode(self.job_key.encode("utf-8"))
        except (CanonicalTextRefused, UnicodeError) as error:
            raise MalformedClosure("planned job key is not canonical job-key text") from error
        if not isinstance(parsed, Mapping) or set(parsed) != {"rule", "wildcards"}:
            raise MalformedClosure("planned job key is not canonical job-key text")
        wildcards = parsed["wildcards"]
        if (
            type(parsed["rule"]) is not str
            or not isinstance(wildcards, Mapping)
            or any(type(name) is not str or type(value) is not str for name, value in wildcards.items())
            or job_key(self.family, tuple(wildcards.items())) != self.job_key
        ):
            raise MalformedClosure("planned job key disagrees with its family")

    def projection(self) -> dict[str, object]:
        return {
            "job_key": self.job_key,
            "family": self.family,
            "outputs": list(self.outputs),
            "is_checkpoint": self.is_checkpoint,
        }


def mount_plan_identity(mounts: tuple[tuple[str, str, str], ...]) -> str:
    """Digest of a canonical mount table: rows of (mountpoint, role, access)."""
    _require_triples(mounts, "mount plan rows")
    return v1.digest(MOUNT_PLAN_DOMAIN, {"mounts": _triples(mounts)})


@sealed
@final
@dataclass(frozen=True)
class InstanceAttestation:
    """What the boundary observed of the fresh instance from its own /proc:
    every namespace distinct from the parent's, the canonical mount table, its
    identity, and the verified snapshot's environment identity (design §6.3)."""

    namespaces: tuple[str, ...]
    mounts: tuple[tuple[str, str, str], ...]
    mount_plan_identity: str
    environment_identity: str

    def __post_init__(self) -> None:
        _require_strings(self.namespaces, "instance namespaces")
        if tuple(sorted(self.namespaces)) != NAMESPACES:
            raise MalformedClosure(f"an instance attests every namespace in {NAMESPACES} as distinct, and no other")
        _require_triples(self.mounts, "instance mounts")
        points = [point for point, _, _ in self.mounts]
        if len(set(points)) != len(points):
            raise MalformedClosure("instance mounts name each mountpoint once")
        if any(access not in MOUNT_ACCESS for _, _, access in self.mounts):
            raise MalformedClosure(f"instance mount access is one of {MOUNT_ACCESS}")
        _require_str(self.mount_plan_identity, "instance mount plan identity")
        if self.mount_plan_identity != mount_plan_identity(self.mounts):
            raise MalformedClosure("an instance's mount plan identity is the digest of its own canonical mounts")
        _require_component(self.environment_identity, "instance environment identity")


@sealed
@final
@dataclass(frozen=True)
class LaunchAttestation:
    scratch_mapping: str
    argv: tuple[str, ...]
    rendered_config: tuple[tuple[str, str], ...]
    capabilities: tuple[str, ...] = ()
    instance: InstanceAttestation | None = None
    rendered_environment: tuple[tuple[str, str, str], ...] | None = None
    mounts: tuple[tuple[str, str], ...] | None = None

    def __post_init__(self) -> None:
        _require_str(self.scratch_mapping, "launch scratch mapping")
        _require_strings(self.argv, "launch argv")
        _require_pairs(self.rendered_config, "launch rendered config")
        _require_strings(self.capabilities, "launch capabilities")
        if any(capability not in CAPABILITIES for capability in self.capabilities):
            raise MalformedClosure(f"launch capabilities are outside the closed vocabulary {CAPABILITIES}")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise MalformedClosure("launch capabilities name each capability once")
        present = sum(member is not None for member in (self.instance, self.rendered_environment, self.mounts))
        if present not in (0, 3):
            raise MalformedClosure(
                "a confined launch carries instance, rendered_environment and mounts together; a minimal launch carries none"
            )
        if self.instance is None:
            return
        if type(self.instance) is not InstanceAttestation:
            raise MalformedClosure("a confined launch's instance is an InstanceAttestation")
        _require_triples(self.rendered_environment, "launch rendered environment")
        if any(kind not in RENDERED_KINDS for _, kind, _ in cast(tuple[tuple[str, str, str], ...], self.rendered_environment)):
            raise MalformedClosure(f"a rendered environment row's kind is one of {RENDERED_KINDS}")
        _require_pairs(self.mounts, "launch mounts")

    @property
    def confined(self) -> bool:
        return self.instance is not None


@sealed
@final
@dataclass(frozen=True)
class BoundaryReceipt:
    planning: LaunchAttestation
    execution: LaunchAttestation

    def __post_init__(self) -> None:
        if type(self.planning) is not LaunchAttestation or type(self.execution) is not LaunchAttestation:
            raise MalformedClosure("a boundary receipt carries planning and execution launch attestations")
        if self.planning.confined != self.execution.confined:
            raise MalformedClosure("planning and execution launches must agree about confinement")

    @property
    def confined(self) -> bool:
        return self.execution.confined

    def identity(self) -> str:
        domain = CONFINED_RECEIPT_DOMAIN if self.confined else BOUNDARY_RECEIPT_DOMAIN
        return v1.digest(domain, _receipt_projection(self))


@sealed
@final
@dataclass(frozen=True)
class Occurrence:
    event_token: str
    started_at: str
    actor: str
    host_realization: str
    trace: tuple[TraceJob, ...]
    planned: tuple[PlannedJob, ...]
    target_keys: tuple[str, ...]
    realized_seeds: RealizedSeeds
    receipt: BoundaryReceipt

    def __post_init__(self) -> None:
        _require_str(self.event_token, "occurrence event token")
        _require_str(self.started_at, "occurrence start time")
        _require_str(self.actor, "occurrence actor")
        _require_str(self.host_realization, "occurrence host realization")
        _require_tuple(self.trace, "occurrence trace")
        if not all(type(job) is TraceJob for job in self.trace):
            raise MalformedClosure("occurrence trace holds TraceJob values only")
        _require_tuple(self.planned, "occurrence planned jobs")
        if not all(type(job) is PlannedJob for job in self.planned):
            raise MalformedClosure("occurrence planned jobs hold PlannedJob values only")
        keys = [job.job_key for job in self.planned]
        if len(keys) != len(set(keys)):
            raise MalformedClosure("occurrence planned jobs name each job key once")
        _require_strings(self.target_keys, "occurrence target keys")
        if type(self.realized_seeds) is not RealizedSeeds:
            raise MalformedClosure("occurrence realized_seeds must be RealizedSeeds")
        if not all(
            type(job) is str
            and isinstance(per_stream, Mapping)
            and all(type(stream) is str and type(seed) is int for stream, seed in per_stream.items())
            for job, per_stream in self.realized_seeds.seeds.items()
        ):
            raise MalformedClosure("realized seeds must map job and stream strings to integers")
        if type(self.receipt) is not BoundaryReceipt:
            raise MalformedClosure("occurrence receipt must be a BoundaryReceipt")


def _trace_projection(job: TraceJob) -> dict[str, object]:
    return {
        "job_id": job.job_id,
        "rule": job.rule,
        "wildcards": _pairs(job.wildcards),
        "inputs": list(job.inputs),
        "outputs": list(job.outputs),
    }


def _launch_projection(receipt: LaunchAttestation) -> dict[str, object]:
    projection: dict[str, object] = {
        "scratch_mapping": receipt.scratch_mapping,
        "argv": list(receipt.argv),
        "rendered_config": _pairs(receipt.rendered_config),
        "capabilities": sorted(receipt.capabilities),
    }
    if not receipt.confined:
        return projection
    instance = cast(InstanceAttestation, receipt.instance)
    projection["instance"] = {
        "namespaces": sorted(instance.namespaces),
        "mounts": _triples(instance.mounts),
        "mount_plan_identity": instance.mount_plan_identity,
        "environment_identity": instance.environment_identity,
    }
    projection["rendered_environment"] = _triples(cast(tuple[tuple[str, str, str], ...], receipt.rendered_environment))
    projection["mounts"] = _pairs(cast(tuple[tuple[str, str], ...], receipt.mounts))
    return projection


def _receipt_projection(receipt: BoundaryReceipt) -> dict[str, object]:
    return {"planning": _launch_projection(receipt.planning), "execution": _launch_projection(receipt.execution)}


def _occurrence_projection(occurrence: Occurrence) -> dict[str, object]:
    return {
        "event_token": occurrence.event_token,
        "started_at": occurrence.started_at,
        "actor": occurrence.actor,
        "host_realization": occurrence.host_realization,
        "trace": [_trace_projection(job) for job in occurrence.trace],
        "planned": [job.projection() for job in sorted(occurrence.planned, key=lambda job: job.job_key)],
        "target_keys": list(occurrence.target_keys),
        "realized_seeds": occurrence.realized_seeds.projection(),
        "receipt": _receipt_projection(occurrence.receipt),
    }


RUN_DOMAINS = {
    (False, False): "science.run.v1",
    (False, True): "science.run.v2",
    (True, False): "science.run.v3",
    (True, True): "science.run.v4",
}


def _v1_run_domain(confined: bool) -> str:
    return CONFINED_RUN_DOMAIN if confined else RUN_DOMAIN


def run_domain_for(*, recipe_v2: bool, confined: bool) -> str:
    is_confined = _v1_run_domain(confined) == CONFINED_RUN_DOMAIN
    return RUN_DOMAINS[(recipe_v2, is_confined)]


def run_domain_for_projection(parsed: Mapping[str, object]) -> str:
    recipe = cast(Mapping[str, object], parsed["recipe"])
    receipt = cast(Mapping[str, object], cast(Mapping[str, object], parsed["occurrence"])["receipt"])
    composed = set(receipt) == {"planning", "execution"}
    recipe_v2 = "workflow_definition" in recipe
    if recipe_v2 == ("workflow_definition_identity" in recipe):
        raise MalformedRecord("a recipe projection carries exactly one workflow member")
    if recipe_v2 != composed:
        raise MalformedRecord(f"recipe shape v{2 if recipe_v2 else 1} does not pair with this receipt shape (§3.5)")
    launch = cast(Mapping[str, object], receipt["execution"]) if composed else receipt
    return run_domain_for(recipe_v2=recipe_v2, confined="instance" in launch)


@sealed
@final
@dataclass(frozen=True)
class RunClosure:
    recipe: Recipe
    result: ResultManifest
    occurrence: Occurrence

    def __post_init__(self) -> None:
        if type(self.recipe) is not Recipe:
            raise MalformedClosure("run recipe must be a Recipe")
        if type(self.result) is not ResultManifest:
            raise MalformedClosure("run result must be a ResultManifest")
        if type(self.occurrence) is not Occurrence:
            raise MalformedClosure("run occurrence must be an Occurrence")
        declared = set(self.recipe.invocation.declared_outputs)
        supplied = {name for name, _ in self.result.outputs}
        if declared - supplied:
            raise MalformedClosure(f"missing declared output: {sorted(declared - supplied)}")
        if supplied - declared:
            raise MalformedClosure(f"undeclared entry: {sorted(supplied - declared)}")

    def address(self) -> str:
        return v1.digest(
            run_domain_for(recipe_v2=True, confined=self.occurrence.receipt.confined),
            {
                "recipe": self.recipe._projection(),
                "result": _pairs(self.result.outputs),
                "occurrence": _occurrence_projection(self.occurrence),
            },
        )
