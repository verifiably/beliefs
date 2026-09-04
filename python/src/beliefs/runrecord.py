"""The closure-to-stored run publication codec (spec §2.6 items 4–5).

Identity is the closure's address: `run:<RunClosure.address()>`. The
`run-closure` facet carries the `{recipe, result, occurrence}` projection
as v1-canonical text. Decode validates the typed projection view, recomputes
the address, and checks the reader-facing `run` facet.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from typing import NoReturn, Protocol, cast, final

from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs import stored
from beliefs.errors import MalformedClosure, MalformedRecord, RecipeVersionUnsupported
from beliefs.identity import v1
from beliefs.permit import Authority
from beliefs.production import mint_dataset
from beliefs.recipe import (
    ASSESSMENT_ROLES,
    CAPABILITIES,
    MOUNT_ACCESS,
    NAMESPACES,
    PRODUCTION_ROLES,
    RENDERED_KINDS,
    SHAPES,
    BoundaryPolicy,
    BoundaryReceipt,
    EnvironmentReference,
    InstanceAttestation,
    Invocation,
    LaunchAttestation,
    Occurrence,
    PlannedJob,
    Recipe,
    RecipeInput,
    ResultManifest,
    RunClosure,
    TraceJob,
    WorkflowDefinitionSnapshot,
    _occurrence_projection,
    _pairs,
    mount_plan_identity,
    run_domain_for_projection,
)
from beliefs.recipe import run_domain_for as _run_domain_for
from beliefs.sealed import sealed
from beliefs.spec import Deterministic, ExclusionCertification, RealizedSeeds, Seeded, SeedPlan, StochasticUnseeded

__all__ = [
    "OperationPort",
    "RunPublication",
    "bare_address",
    "decode_projection",
    "decode_run_closure",
    "decode_run_record",
    "projection_text",
    "publication_plan",
    "run_ref",
]


_CLOSURE_ADDRESS = re.compile(r"[0-9a-f]{64}")


def run_ref(address: str) -> str:
    """Convert a bare closure address to its typed stored reference."""
    if type(address) is not str or not _CLOSURE_ADDRESS.fullmatch(address):
        raise MalformedRecord(f"{address!r} is not a bare closure address")
    return f"run:{address}"


def bare_address(ref: str) -> str:
    """Return the bare address from exactly the image of `run_ref`."""
    if type(ref) is not str or not ref.startswith("run:"):
        raise MalformedRecord(f"{ref!r} is not a typed run reference")
    address = ref.removeprefix("run:")
    if not _CLOSURE_ADDRESS.fullmatch(address):
        raise MalformedRecord(f"{ref!r} does not name a closure address")
    return address


class OperationPort(Protocol):
    @property
    def authority(self) -> Authority: ...

    def append_intent(self, payload: bytes) -> str: ...

    def execute(self, plan: WritePlan) -> None: ...

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None: ...


@sealed
@final
@dataclass(frozen=True)
class RunPublication:
    address: str
    shape: str
    spec_identity: str | None
    event_token: str


def projection_text(closure: RunClosure) -> bytes:
    if type(closure) is not RunClosure:
        raise MalformedClosure("projection_text requires a RunClosure")
    return v1.encode(
        {
            "recipe": closure.recipe._projection(),
            "result": _pairs(closure.result.outputs),
            "occurrence": _occurrence_projection(closure.occurrence),
        }
    )


def _refuse(path: str, why: str) -> NoReturn:
    raise MalformedRecord(f"run projection at {path}: {why}")


def _mapping(value: object, keys: set[str], path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _refuse(path, "not an object")
    if set(value) != keys:
        _refuse(path, f"keys {sorted(value)} != {sorted(keys)}")
    return value


def _str_at(value: object, path: str) -> str:
    if type(value) is not str:
        _refuse(path, "not a string")
    return value


def _component_at(value: object, path: str) -> str:
    component = _str_at(value, path)
    if component in ("", "unknown", "attested"):
        _refuse(path, f"{component!r} is not a held component identity")
    return component


def _str_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or any(
        type(member) is not str for member in value
    ):
        _refuse(path, "not a list of strings")
    return value


def _pair_list(value: object, path: str) -> list[list[str]]:
    if not isinstance(value, list) or any(
        not isinstance(row, list)
        or len(row) != 2
        or any(type(member) is not str for member in row)
        for row in value
    ):
        _refuse(path, "not a list of [string, string] pairs")
    return value


def _triple_list(value: object, path: str) -> list[list[str]]:
    if not isinstance(value, list) or any(
        not isinstance(row, list)
        or len(row) != 3
        or any(type(member) is not str for member in row)
        for row in value
    ):
        _refuse(path, "not a list of [string, string, string] triples")
    return value


_RECEIPT_KEYS = {"scratch_mapping", "argv", "rendered_config", "capabilities"}
_CONFINED_RECEIPT_KEYS = _RECEIPT_KEYS | {"instance", "rendered_environment", "mounts"}


def _is_confined_receipt(receipt: object) -> bool:
    if isinstance(receipt, dict) and set(receipt) == {"planning", "execution"}:
        receipt = receipt["execution"]
    return isinstance(receipt, dict) and "instance" in receipt


_RECIPE_KEYS = {
    "shape",
    "code_identity",
    "environment",
    "invocation",
    "inputs",
    "parameters",
    "nondeterminism",
    "boundary_policy",
    "rule_bindings",
}


def _validate_recipe(recipe: object) -> str:
    if not isinstance(recipe, dict):
        _refuse("$.recipe", "not an object")
    shape = _str_at(recipe.get("shape"), "$.recipe.shape")
    if shape not in SHAPES:
        _refuse("$.recipe.shape", f"{shape!r} is outside {SHAPES}")
    recipe_v2 = "workflow_definition" in recipe
    if recipe_v2 == ("workflow_definition_identity" in recipe):
        _refuse("$.recipe", "carries exactly one workflow member")
    workflow_member = "workflow_definition" if recipe_v2 else "workflow_definition_identity"
    expected = _RECIPE_KEYS | {workflow_member} | ({"spec_identity"} if shape == "assessment" else set())
    _mapping(recipe, expected, "$.recipe")
    if shape == "assessment":
        _str_at(recipe["spec_identity"], "$.recipe.spec_identity")
    _component_at(recipe["code_identity"], "$.recipe.code_identity")
    _component_at(recipe["environment"], "$.recipe.environment")
    if recipe_v2:
        definition = _mapping(
            recipe["workflow_definition"],
            {"snakefile", "family_streams", "checkpoint_expanded_families"},
            "$.recipe.workflow_definition",
        )
        _component_at(definition["snakefile"], "$.recipe.workflow_definition.snakefile")
        family_streams = definition["family_streams"]
        if not isinstance(family_streams, dict) or any(
            type(family) is not str
            or not isinstance(streams, list)
            or any(type(stream) is not str for stream in streams)
            for family, streams in family_streams.items()
        ):
            _refuse("$.recipe.workflow_definition.family_streams", "not a string to string-list object")
        _str_list(
            definition["checkpoint_expanded_families"],
            "$.recipe.workflow_definition.checkpoint_expanded_families",
        )
    else:
        _component_at(recipe["workflow_definition_identity"], "$.recipe.workflow_definition_identity")
    invocation = _mapping(
        recipe["invocation"],
        {"entrypoint", "targets", "bindings", "declared_outputs"},
        "$.recipe.invocation",
    )
    _str_at(invocation["entrypoint"], "$.recipe.invocation.entrypoint")
    lists = {
        field: _str_list(invocation[field], f"$.recipe.invocation.{field}")
        for field in ("targets", "bindings", "declared_outputs")
    }
    if any(target.startswith("-") for target in lists["targets"]):
        _refuse(
            "$.recipe.invocation.targets",
            "an option-like target is not a workflow target",
        )
    declared = lists["declared_outputs"]
    for output in declared:
        depth = 0
        if output.startswith("/"):
            _refuse(
                "$.recipe.invocation.declared_outputs", f"{output!r} is absolute"
            )
        for segment in output.split("/"):
            if segment == "..":
                depth -= 1
            elif segment not in ("", "."):
                depth += 1
            if depth < 0:
                _refuse(
                    "$.recipe.invocation.declared_outputs",
                    f"{output!r} escapes the run root",
                )
    if len(set(declared)) != len(declared):
        _refuse("$.recipe.invocation.declared_outputs", "duplicate logical names")
    roles = ASSESSMENT_ROLES if shape == "assessment" else PRODUCTION_ROLES
    inputs = recipe["inputs"]
    if not isinstance(inputs, list):
        _refuse("$.recipe.inputs", "not a list")
    for index, row in enumerate(inputs):
        path = f"$.recipe.inputs[{index}]"
        if not isinstance(row, dict):
            _refuse(path, "not an object")
        keys = {"role", "dataset", "content"} | (
            {"exclusion"} if "exclusion" in row else set()
        )
        _mapping(row, keys, path)
        role = _str_at(row["role"], f"{path}.role")
        if role not in roles:
            _refuse(
                f"{path}.role", f"{role!r} is outside the {shape} partition {roles}"
            )
        _str_at(row["dataset"], f"{path}.dataset")
        _component_at(row["content"], f"{path}.content")
        if "exclusion" in row:
            if role != "reads":
                _refuse(
                    f"{path}.exclusion",
                    "an exclusion certification is carried by a `reads` input only",
                )
            exclusion = _mapping(
                row["exclusion"], {"rationale", "attribution"}, f"{path}.exclusion"
            )
            for member in ("rationale", "attribution"):
                if not _str_at(exclusion[member], f"{path}.exclusion.{member}"):
                    _refuse(
                        f"{path}.exclusion.{member}",
                        "an exclusion member is never empty",
                    )
    if not isinstance(recipe["parameters"], dict):
        _refuse("$.recipe.parameters", "not an object")
    _validate_nondeterminism(recipe["nondeterminism"])
    policy = _mapping(
        recipe["boundary_policy"],
        {"identity", "scope_rule", "capabilities"},
        "$.recipe.boundary_policy",
    )
    _str_at(policy["identity"], "$.recipe.boundary_policy.identity")
    _str_at(policy["scope_rule"], "$.recipe.boundary_policy.scope_rule")
    _str_list(policy["capabilities"], "$.recipe.boundary_policy.capabilities")
    bindings = _pair_list(recipe["rule_bindings"], "$.recipe.rule_bindings")
    rules = [rule for rule, _ in bindings]
    if len(rules) != len(set(rules)):
        _refuse("$.recipe.rule_bindings", "each logical rule is named once")
    return shape


def _validate_nondeterminism(value: object) -> None:
    if not isinstance(value, dict) or "variant" not in value:
        _refuse("$.recipe.nondeterminism", "not a variant object")
    variant = value["variant"]
    if variant == "deterministic":
        _mapping(value, {"variant"}, "$.recipe.nondeterminism")
    elif variant == "stochastic-unseeded":
        _mapping(value, {"variant", "rationale"}, "$.recipe.nondeterminism")
        _str_at(value["rationale"], "$.recipe.nondeterminism.rationale")
        if not value["rationale"]:
            _refuse(
                "$.recipe.nondeterminism.rationale",
                "an empty rationale declares nothing",
            )
    elif variant == "seeded":
        _mapping(value, {"variant", "plan"}, "$.recipe.nondeterminism")
        plan = _mapping(
            value["plan"],
            {"derivation_rule", "streams", "roots", "stream_roots"},
            "$.recipe.nondeterminism.plan",
        )
        _str_at(
            plan["derivation_rule"], "$.recipe.nondeterminism.plan.derivation_rule"
        )
        streams = _str_list(
            plan["streams"], "$.recipe.nondeterminism.plan.streams"
        )
        roots = plan["roots"]
        if not isinstance(roots, dict) or any(
            type(key) is not str or type(member) is not int
            for key, member in roots.items()
        ):
            _refuse(
                "$.recipe.nondeterminism.plan.roots", "not a string-to-int object"
            )
        stream_roots = plan["stream_roots"]
        if not isinstance(stream_roots, dict) or any(
            type(key) is not str or type(member) is not str
            for key, member in stream_roots.items()
        ):
            _refuse(
                "$.recipe.nondeterminism.plan.stream_roots",
                "not a string-to-string object",
            )
        if set(streams) - set(stream_roots):
            _refuse("$.recipe.nondeterminism.plan", "streams with no root")
        if set(stream_roots) - set(streams):
            _refuse(
                "$.recipe.nondeterminism.plan",
                "a mapping entry for an undeclared stream",
            )
        if set(stream_roots.values()) - set(roots):
            _refuse(
                "$.recipe.nondeterminism.plan", "mapped roots nobody declared"
            )
    else:
        _refuse(
            "$.recipe.nondeterminism.variant", f"unknown variant {variant!r}"
        )


def _validate_launch(value: object, path: str) -> bool:
    confined = _is_confined_receipt(value)
    launch = _mapping(value, _CONFINED_RECEIPT_KEYS if confined else _RECEIPT_KEYS, path)
    _str_at(launch["scratch_mapping"], f"{path}.scratch_mapping")
    _str_list(launch["argv"], f"{path}.argv")
    _pair_list(launch["rendered_config"], f"{path}.rendered_config")
    capabilities = _str_list(launch["capabilities"], f"{path}.capabilities")
    if any(capability not in CAPABILITIES for capability in capabilities):
        _refuse(f"{path}.capabilities", f"outside the closed vocabulary {CAPABILITIES}")
    if len(set(capabilities)) != len(capabilities):
        _refuse(f"{path}.capabilities", "names a capability more than once")
    if not confined:
        return False
    instance = _mapping(
        launch["instance"],
        {"namespaces", "mounts", "mount_plan_identity", "environment_identity"},
        f"{path}.instance",
    )
    namespaces = _str_list(instance["namespaces"], f"{path}.instance.namespaces")
    if sorted(namespaces) != list(NAMESPACES):
        _refuse(f"{path}.instance.namespaces", f"not exactly {NAMESPACES}")
    mounts = _triple_list(instance["mounts"], f"{path}.instance.mounts")
    points = [point for point, _, _ in mounts]
    if len(set(points)) != len(points):
        _refuse(f"{path}.instance.mounts", "names a mountpoint more than once")
    if any(access not in MOUNT_ACCESS for _, _, access in mounts):
        _refuse(f"{path}.instance.mounts", f"access is not one of {MOUNT_ACCESS}")
    recomputed = mount_plan_identity(tuple((point, role, access) for point, role, access in mounts))
    if _str_at(instance["mount_plan_identity"], f"{path}.instance.mount_plan_identity") != recomputed:
        if path == "$.occurrence.receipt":
            _refuse("$.occurrence.receipt.instance.mount_plan_identity", "is not the digest of its own mounts")
        else:
            _refuse(f"{path}.instance.mount_plan_identity", "is not the digest of its own mounts")
    _component_at(instance["environment_identity"], f"{path}.instance.environment_identity")
    rendered = _triple_list(launch["rendered_environment"], f"{path}.rendered_environment")
    if any(kind not in RENDERED_KINDS for _, kind, _ in rendered):
        _refuse(f"{path}.rendered_environment", f"kind is not one of {RENDERED_KINDS}")
    _pair_list(launch["mounts"], f"{path}.mounts")
    return True


def _validate_occurrence(value: object, *, recipe_v2: bool) -> str:
    members = {
        "event_token",
        "started_at",
        "actor",
        "host_realization",
        "trace",
        "realized_seeds",
        "receipt",
    }
    if recipe_v2:
        members.update(("planned", "target_keys"))
    occurrence = _mapping(
        value,
        members,
        "$.occurrence",
    )
    for field in ("event_token", "started_at", "actor", "host_realization"):
        _str_at(occurrence[field], f"$.occurrence.{field}")
    trace = occurrence["trace"]
    if not isinstance(trace, list):
        _refuse("$.occurrence.trace", "not a list")
    for index, job in enumerate(trace):
        path = f"$.occurrence.trace[{index}]"
        row = _mapping(
            job, {"job_id", "rule", "wildcards", "inputs", "outputs"}, path
        )
        job_id = _str_at(row["job_id"], f"{path}.job_id")
        rule = _str_at(row["rule"], f"{path}.rule")
        _pair_list(row["wildcards"], f"{path}.wildcards")
        inputs = _str_list(row["inputs"], f"{path}.inputs")
        outputs = _str_list(row["outputs"], f"{path}.outputs")
        try:
            TraceJob(job_id, rule, _decoded_pairs(row["wildcards"]), tuple(inputs), tuple(outputs))
        except MalformedClosure as error:
            _refuse(path, str(error))
    if recipe_v2:
        planned = occurrence["planned"]
        if not isinstance(planned, list):
            _refuse("$.occurrence.planned", "not a list")
        planned_keys = []
        for index, job in enumerate(planned):
            path = f"$.occurrence.planned[{index}]"
            row = _mapping(job, {"job_key", "family", "outputs", "is_checkpoint"}, path)
            key = _str_at(row["job_key"], f"{path}.job_key")
            family = _str_at(row["family"], f"{path}.family")
            outputs = _str_list(row["outputs"], f"{path}.outputs")
            if type(row["is_checkpoint"]) is not bool:
                _refuse(f"{path}.is_checkpoint", "not a boolean")
            try:
                PlannedJob(key, family, tuple(outputs), row["is_checkpoint"])
            except MalformedClosure as error:
                _refuse(path, str(error))
            planned_keys.append(key)
        if len(planned_keys) != len(set(planned_keys)):
            _refuse("$.occurrence.planned", "repeats a job key")
        _str_list(occurrence["target_keys"], "$.occurrence.target_keys")
    seeds = occurrence["realized_seeds"]
    if not isinstance(seeds, dict) or any(
        type(job) is not str
        or not isinstance(per_stream, dict)
        or any(
            type(stream) is not str or type(seed) is not int
            for stream, seed in per_stream.items()
        )
        for job, per_stream in seeds.items()
    ):
        _refuse(
            "$.occurrence.realized_seeds", "not a [job][stream] -> int object"
        )
    raw_receipt = occurrence["receipt"]
    if isinstance(raw_receipt, dict) and set(raw_receipt) == {"planning", "execution"}:
        receipt = _mapping(raw_receipt, {"planning", "execution"}, "$.occurrence.receipt")
        planning_confined = _validate_launch(receipt["planning"], "$.occurrence.receipt.planning")
        execution_confined = _validate_launch(receipt["execution"], "$.occurrence.receipt.execution")
        if planning_confined != execution_confined:
            _refuse("$.occurrence.receipt", "planning and execution disagree about confinement")
    else:
        _validate_launch(raw_receipt, "$.occurrence.receipt")
    return cast(str, occurrence["event_token"])


def _input_sort_key(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    exclusion = row.get("exclusion")
    rationale = (
        cast(str, exclusion["rationale"]) if isinstance(exclusion, dict) else ""
    )
    attribution = (
        cast(str, exclusion["attribution"]) if isinstance(exclusion, dict) else ""
    )
    return (
        cast(str, row["role"]),
        cast(str, row["dataset"]),
        cast(str, row["content"]),
        rationale,
        attribution,
    )


def _reproject_launch(launch: dict[str, object]) -> None:
    launch["rendered_config"] = sorted(cast("list[list[str]]", launch["rendered_config"]))
    launch["capabilities"] = sorted(cast("list[str]", launch["capabilities"]))
    if _is_confined_receipt(launch):
        instance = cast(dict[str, object], launch["instance"])
        instance["namespaces"] = sorted(cast("list[str]", instance["namespaces"]))
        instance["mounts"] = sorted(cast("list[list[str]]", instance["mounts"]))
        launch["rendered_environment"] = sorted(cast("list[list[str]]", launch["rendered_environment"]))
        launch["mounts"] = sorted(cast("list[list[str]]", launch["mounts"]))


def _reproject(parsed: dict[str, object]) -> dict[str, object]:
    rebuilt = cast(dict[str, object], deepcopy(parsed))
    recipe = cast(dict[str, object], rebuilt["recipe"])
    recipe["inputs"] = sorted(
        cast("list[dict[str, object]]", recipe["inputs"]), key=_input_sort_key
    )
    recipe["rule_bindings"] = sorted(
        cast("list[list[str]]", recipe["rule_bindings"])
    )
    policy = cast(dict[str, object], recipe["boundary_policy"])
    policy["capabilities"] = sorted(
        cast("list[str]", policy["capabilities"])
    )
    if "workflow_definition" in recipe:
        definition = cast(dict[str, object], recipe["workflow_definition"])
        family_streams = cast(dict[str, list[str]], definition["family_streams"])
        for family, streams in family_streams.items():
            family_streams[family] = sorted(streams)
        definition["checkpoint_expanded_families"] = sorted(
            cast("list[str]", definition["checkpoint_expanded_families"])
        )
    nondeterminism = cast(dict[str, object], recipe["nondeterminism"])
    if nondeterminism.get("variant") == "seeded":
        plan = cast(dict[str, object], nondeterminism["plan"])
        plan["streams"] = sorted(cast("list[str]", plan["streams"]))
    rebuilt["result"] = sorted(cast("list[list[str]]", rebuilt["result"]))
    occurrence = cast(dict[str, object], rebuilt["occurrence"])
    for job in cast("list[dict[str, object]]", occurrence["trace"]):
        job["wildcards"] = sorted(cast("list[list[str]]", job["wildcards"]))
    if "planned" in occurrence:
        occurrence["planned"] = sorted(
            cast("list[dict[str, object]]", occurrence["planned"]),
            key=lambda job: cast(str, job["job_key"]),
        )
    receipt = cast(dict[str, object], occurrence["receipt"])
    if set(receipt) == {"planning", "execution"}:
        _reproject_launch(cast(dict[str, object], receipt["planning"]))
        _reproject_launch(cast(dict[str, object], receipt["execution"]))
    else:
        _reproject_launch(receipt)
    return rebuilt


def decode_projection(data: bytes) -> dict[str, object]:
    parsed = v1.decode(data)
    if not isinstance(parsed, dict):
        _refuse("$", "not an object")
    _mapping(parsed, {"recipe", "result", "occurrence"}, "$")
    _validate_recipe(parsed["recipe"])
    result = _pair_list(parsed["result"], "$.result")
    names = [name for name, _ in result]
    if len(set(names)) != len(names):
        _refuse("$.result", "duplicate logical names")
    recipe = cast(dict[str, object], parsed["recipe"])
    invocation = cast(dict[str, object], recipe["invocation"])
    if set(names) != set(cast("list[str]", invocation["declared_outputs"])):
        _refuse("$.result", "result names disagree with the declared outputs")
    _validate_occurrence(parsed["occurrence"], recipe_v2="workflow_definition" in recipe)
    if _reproject(parsed) != parsed:
        _refuse("$", "an array the projection sorts is out of its canonical order")
    return parsed


def decode_run_record(node: Node) -> RunPublication | None:
    if node.kind != "run":
        raise MalformedRecord(f"{node.id}: not a run record")
    facet = node.facets.get(stored.RUN_CLOSURE_FACET)
    if facet is None:
        return None
    if (
        not isinstance(facet, dict)
        or set(facet) != {"projection"}
        or type(facet["projection"]) is not str
    ):
        raise MalformedRecord(
            f"{node.id}: the run-closure facet is exactly {{'projection': <text>}}"
        )
    data = facet["projection"].encode("utf-8")
    parsed = decode_projection(data)
    run_domain_for_projection(parsed)
    recipe_view = cast(dict[str, object], parsed["recipe"])

    def run_domain_for(confined: bool) -> str:
        return _run_domain_for(recipe_v2="workflow_definition" in recipe_view, confined=confined)

    occurrence_view = cast(dict[str, object], parsed["occurrence"])
    address = v1.digest(run_domain_for(_is_confined_receipt(occurrence_view["receipt"])), parsed)
    if node.id != run_ref(address):
        raise MalformedRecord(
            f"{node.id}: the recomputed address {address} is not the record id"
        )
    recipe = cast(dict[str, object], parsed["recipe"])
    shape = cast(str, recipe["shape"])
    spec_identity = cast("str | None", recipe.get("spec_identity"))
    run_facet = node.facets.get(stored.RUN_FACET)
    if not isinstance(run_facet, dict):
        raise MalformedRecord(
            f"{node.id}: a boundary-published run carries the run facet"
        )
    if shape == "assessment":
        if run_facet != {"spec": spec_identity}:
            raise MalformedRecord(
                f"{node.id}: the run facet is exactly "
                "{'spec': <the closure's spec>}"
            )
    elif run_facet != {}:
        raise MalformedRecord(f"{node.id}: a production run facet is exactly {{}}")
    occurrence = cast(dict[str, object], parsed["occurrence"])
    return RunPublication(
        address=address,
        shape=shape,
        spec_identity=spec_identity,
        event_token=cast(str, occurrence["event_token"]),
    )


def _decoded_pairs(value: object) -> tuple[tuple[str, str], ...]:
    return tuple((cast(str, row[0]), cast(str, row[1])) for row in cast("list[list[object]]", value))


def _decoded_triples(value: object) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (cast(str, row[0]), cast(str, row[1]), cast(str, row[2]))
        for row in cast("list[list[object]]", value)
    )


def _decode_launch(value: object) -> LaunchAttestation:
    launch = cast(dict[str, object], value)
    instance = None
    rendered_environment = None
    mounts = None
    if "instance" in launch:
        raw_instance = cast(dict[str, object], launch["instance"])
        instance = InstanceAttestation(
            namespaces=tuple(cast("list[str]", raw_instance["namespaces"])),
            mounts=_decoded_triples(raw_instance["mounts"]),
            mount_plan_identity=cast(str, raw_instance["mount_plan_identity"]),
            environment_identity=cast(str, raw_instance["environment_identity"]),
        )
        rendered_environment = _decoded_triples(launch["rendered_environment"])
        mounts = _decoded_pairs(launch["mounts"])
    return LaunchAttestation(
        scratch_mapping=cast(str, launch["scratch_mapping"]),
        argv=tuple(cast("list[str]", launch["argv"])),
        rendered_config=_decoded_pairs(launch["rendered_config"]),
        capabilities=tuple(cast("list[str]", launch["capabilities"])),
        instance=instance,
        rendered_environment=rendered_environment,
        mounts=mounts,
    )


def _decode_nondeterminism(value: object) -> Deterministic | Seeded | StochasticUnseeded:
    nondeterminism = cast(dict[str, object], value)
    variant = nondeterminism["variant"]
    if variant == "deterministic":
        return Deterministic()
    if variant == "stochastic-unseeded":
        return StochasticUnseeded(cast(str, nondeterminism["rationale"]))
    raw_plan = cast(dict[str, object], nondeterminism["plan"])
    return Seeded(
        SeedPlan(
            derivation_rule=cast(str, raw_plan["derivation_rule"]),
            streams=tuple(cast("list[str]", raw_plan["streams"])),
            roots=cast("dict[str, int]", raw_plan["roots"]),
            stream_roots=cast("dict[str, str]", raw_plan["stream_roots"]),
        )
    )


def decode_run_closure(node: Node) -> RunClosure:
    """Rebuild a v2 typed closure from its validated stored projection."""
    if decode_run_record(node) is None:
        raise MalformedRecord(f"{node.id}: no run-closure projection to decode")
    facet = cast(dict[str, str], node.facets[stored.RUN_CLOSURE_FACET])
    parsed = decode_projection(facet["projection"].encode("utf-8"))
    recipe = cast(dict[str, object], parsed["recipe"])
    if "workflow_definition_identity" in recipe:
        raise RecipeVersionUnsupported(
            "a v1 recipe carries an identity where the snapshot's members belong"
        )

    raw_definition = cast(dict[str, object], recipe["workflow_definition"])
    raw_invocation = cast(dict[str, object], recipe["invocation"])
    raw_policy = cast(dict[str, object], recipe["boundary_policy"])
    inputs = []
    for raw_input in cast("list[dict[str, object]]", recipe["inputs"]):
        raw_exclusion = cast("dict[str, str] | None", raw_input.get("exclusion"))
        exclusion = (
            ExclusionCertification(raw_exclusion["rationale"], raw_exclusion["attribution"])
            if raw_exclusion is not None
            else None
        )
        inputs.append(
            RecipeInput(
                role=cast(str, raw_input["role"]),
                dataset=cast(str, raw_input["dataset"]),
                content=cast(str, raw_input["content"]),
                exclusion=exclusion,
            )
        )
    decoded_recipe = Recipe(
        shape=cast(str, recipe["shape"]),
        spec_identity=cast("str | None", recipe.get("spec_identity")),
        code_identity=cast(str, recipe["code_identity"]),
        environment=EnvironmentReference(cast(str, recipe["environment"])),
        workflow_definition=WorkflowDefinitionSnapshot(
            snakefile_digest=cast(str, raw_definition["snakefile"]),
            family_streams={
                family: tuple(streams)
                for family, streams in cast("dict[str, list[str]]", raw_definition["family_streams"]).items()
            },
            checkpoint_expanded_families=tuple(
                cast("list[str]", raw_definition["checkpoint_expanded_families"])
            ),
        ),
        invocation=Invocation(
            entrypoint=cast(str, raw_invocation["entrypoint"]),
            targets=tuple(cast("list[str]", raw_invocation["targets"])),
            bindings=tuple(cast("list[str]", raw_invocation["bindings"])),
            declared_outputs=tuple(cast("list[str]", raw_invocation["declared_outputs"])),
        ),
        inputs=tuple(inputs),
        parameters=cast("dict[str, object]", recipe["parameters"]),
        nondeterminism=_decode_nondeterminism(recipe["nondeterminism"]),
        boundary_policy=BoundaryPolicy(
            identity=cast(str, raw_policy["identity"]),
            scope_rule=cast(str, raw_policy["scope_rule"]),
            capabilities=tuple(cast("list[str]", raw_policy["capabilities"])),
        ),
        rule_bindings=_decoded_pairs(recipe["rule_bindings"]),
    )

    raw_occurrence = cast(dict[str, object], parsed["occurrence"])
    raw_receipt = cast(dict[str, object], raw_occurrence["receipt"])
    occurrence = Occurrence(
        event_token=cast(str, raw_occurrence["event_token"]),
        started_at=cast(str, raw_occurrence["started_at"]),
        actor=cast(str, raw_occurrence["actor"]),
        host_realization=cast(str, raw_occurrence["host_realization"]),
        trace=tuple(
            TraceJob(
                job_id=cast(str, job["job_id"]),
                rule=cast(str, job["rule"]),
                wildcards=_decoded_pairs(job["wildcards"]),
                inputs=tuple(cast("list[str]", job["inputs"])),
                outputs=tuple(cast("list[str]", job["outputs"])),
            )
            for job in cast("list[dict[str, object]]", raw_occurrence["trace"])
        ),
        planned=tuple(
            PlannedJob(
                job_key=cast(str, job["job_key"]),
                family=cast(str, job["family"]),
                outputs=tuple(cast("list[str]", job["outputs"])),
                is_checkpoint=cast(bool, job["is_checkpoint"]),
            )
            for job in cast("list[dict[str, object]]", raw_occurrence["planned"])
        ),
        target_keys=tuple(cast("list[str]", raw_occurrence["target_keys"])),
        realized_seeds=RealizedSeeds(
            cast("dict[str, dict[str, int]]", raw_occurrence["realized_seeds"])
        ),
        receipt=BoundaryReceipt(
            planning=_decode_launch(raw_receipt["planning"]),
            execution=_decode_launch(raw_receipt["execution"]),
        ),
    )
    return RunClosure(
        recipe=decoded_recipe,
        result=ResultManifest(_decoded_pairs(parsed["result"])),
        occurrence=occurrence,
    )


def publication_plan(closure: RunClosure) -> tuple[str, str, tuple[CreateOp, ...]]:
    shape = closure.recipe.shape
    produces = (
        mint_dataset(closure, existing_bases={}).address
        if shape == "dataset-production"
        else None
    )
    address = closure.address()
    inputs = closure.recipe.inputs
    node = stored.run_publication_node(
        address,
        title=f"{shape} run",
        projection=projection_text(closure).decode("utf-8"),
        spec=closure.recipe.spec_identity,
        observes=tuple(entry.dataset for entry in inputs if entry.role == "observes"),
        reads=tuple(entry.dataset for entry in inputs if entry.role == "reads"),
        transforms=tuple(
            entry.dataset for entry in inputs if entry.role == "transforms"
        ),
        produces=(produces,) if produces is not None else (),
    )
    path = f"run/{address}.md"
    record_id = run_ref(address)
    if node.id != record_id:
        raise MalformedRecord(
            f"the stored node id {node.id!r} disagrees with the bridge's {record_id!r}"
        )
    return record_id, path, (
        CreateOp(path, node_to_markdown(node).encode("utf-8")),
    )
