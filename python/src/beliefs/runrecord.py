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
from beliefs.errors import MalformedClosure, MalformedRecord
from beliefs.identity import v1
from beliefs.production import mint_dataset
from beliefs.recipe import (
    ASSESSMENT_ROLES,
    PRODUCTION_ROLES,
    RUN_DOMAIN,
    SHAPES,
    RunClosure,
    _occurrence_projection,
    _pairs,
)
from beliefs.sealed import sealed

__all__ = [
    "OperationPort",
    "RunPublication",
    "bare_address",
    "decode_projection",
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


_RECIPE_KEYS = {
    "shape",
    "code_identity",
    "environment",
    "workflow_definition_identity",
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
    expected = _RECIPE_KEYS | ({"spec_identity"} if shape == "assessment" else set())
    _mapping(recipe, expected, "$.recipe")
    if shape == "assessment":
        _str_at(recipe["spec_identity"], "$.recipe.spec_identity")
    _component_at(recipe["code_identity"], "$.recipe.code_identity")
    _str_at(recipe["environment"], "$.recipe.environment")
    _component_at(
        recipe["workflow_definition_identity"],
        "$.recipe.workflow_definition_identity",
    )
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


def _validate_occurrence(value: object) -> str:
    occurrence = _mapping(
        value,
        {
            "event_token",
            "started_at",
            "actor",
            "host_realization",
            "trace",
            "realized_seeds",
            "receipt",
        },
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
        _str_at(row["job_id"], f"{path}.job_id")
        _str_at(row["rule"], f"{path}.rule")
        _pair_list(row["wildcards"], f"{path}.wildcards")
        _str_list(row["inputs"], f"{path}.inputs")
        _str_list(row["outputs"], f"{path}.outputs")
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
    receipt = _mapping(
        occurrence["receipt"],
        {"scratch_mapping", "argv", "rendered_config", "capabilities"},
        "$.occurrence.receipt",
    )
    _str_at(receipt["scratch_mapping"], "$.occurrence.receipt.scratch_mapping")
    _str_list(receipt["argv"], "$.occurrence.receipt.argv")
    _pair_list(
        receipt["rendered_config"], "$.occurrence.receipt.rendered_config"
    )
    _str_list(receipt["capabilities"], "$.occurrence.receipt.capabilities")
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
    nondeterminism = cast(dict[str, object], recipe["nondeterminism"])
    if nondeterminism.get("variant") == "seeded":
        plan = cast(dict[str, object], nondeterminism["plan"])
        plan["streams"] = sorted(cast("list[str]", plan["streams"]))
    rebuilt["result"] = sorted(cast("list[list[str]]", rebuilt["result"]))
    occurrence = cast(dict[str, object], rebuilt["occurrence"])
    for job in cast("list[dict[str, object]]", occurrence["trace"]):
        job["wildcards"] = sorted(cast("list[list[str]]", job["wildcards"]))
    receipt = cast(dict[str, object], occurrence["receipt"])
    receipt["rendered_config"] = sorted(
        cast("list[list[str]]", receipt["rendered_config"])
    )
    receipt["capabilities"] = sorted(
        cast("list[str]", receipt["capabilities"])
    )
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
    _validate_occurrence(parsed["occurrence"])
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
    address = v1.digest(RUN_DOMAIN, parsed)
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
