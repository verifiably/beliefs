"""The analysis spec is the pre-registration (computation §3), frozen as a value.

Carries R20's discriminated union — incoherent contract/plan combinations are
unspellable by type, not caught by a validator — R7's no-target refusal, R8's
successor mint, and G4's successor admissibility over the slice's value state
(cut 3 §4.1: activeness and reference are over the recorded-failure set the
boundary holds, and a discarded failure is undetectable — kernel G4's bound).

Rule identities bind to behaviour through held, fixture-carrying
implementations supplied to the freeze (computation §3.1b). The registry/
resolver route — and R22's unresolvable-rule refusal clause — is the rules
store's, excluded exactly as cut 2's P1 cell ruled (cut 3 §4.2, R22 row).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from hashlib import sha256
from types import MappingProxyType
from typing import Protocol, cast, final

from beliefs.errors import CanonicalTextRefused, MalformedRecord, MalformedSpec, RuleUnbound, UnfreezableSpec
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "BITWISE_EQUIVALENCE_RULES",
    "DATASET_EQUIVALENCE_RULE",
    "SEED_DERIVATION_V1",
    "SPEC_DOMAIN",
    "Deterministic",
    "ExclusionCertification",
    "FrozenSpec",
    "HeldImplementation",
    "NondeterminismContract",
    "RealizedSeeds",
    "RuleFixture",
    "RuleImplementation",
    "SeedPlan",
    "Seeded",
    "SpecDraft",
    "SpecInput",
    "StochasticUnseeded",
    "SuccessorAdmitted",
    "SuccessorRefused",
    "admit_successor",
    "bind_rules",
    "derive_seed",
    "freeze",
    "frozen_projection",
    "implementation_conforms",
    "restore",
    "revise",
]

SPEC_DOMAIN = "science.spec.v1"
SEED_DERIVATION_V1 = "seed-derivation/v1"
BITWISE_EQUIVALENCE_RULES = frozenset({"content-identity-equality/v1", "beliefs/content-identity-equality/v1"})
DATASET_EQUIVALENCE_RULE = "dataset-content-equality/v1"
SPEC_INPUT_ROLES = ("observes", "reads")


def derive_seed(stream_root: int, semantic_job_key: str, stream_key: str) -> int:
    """`seed = f(stream_root, semantic_job_key, stream_key)` (computation §6.2),
    the v1 derivation rule: deterministic, keyed by job AND stream."""
    material = f"{stream_root}\n{semantic_job_key}\n{stream_key}".encode()
    return int.from_bytes(sha256(material).digest()[:8], "big")


@sealed
@final
@dataclass(frozen=True)
class SeedPlan:
    derivation_rule: str
    streams: tuple[str, ...]
    """Logical stream identities — analytical roles (`model-initialization`),
    never library or workflow-rule names. No field for families exists here:
    the per-family declaration is the workflow-definition snapshot's (§3.1a),
    which is what keeps `independent-implementation` reachable (R20 neg. (d))."""
    roots: Mapping[str, int]
    stream_roots: Mapping[str, str]

    def __post_init__(self) -> None:
        unmapped = set(self.streams) - set(self.stream_roots)
        if unmapped:
            raise MalformedSpec(f"streams with no root: {sorted(unmapped)} — the mapping must be total")
        undeclared = set(self.stream_roots.values()) - set(self.roots)
        if undeclared:
            raise MalformedSpec(f"mapped roots nobody declared: {sorted(undeclared)}")
        if set(self.stream_roots) - set(self.streams):
            raise MalformedSpec("a mapping entry for an undeclared stream")
        object.__setattr__(self, "roots", MappingProxyType(dict(self.roots)))
        object.__setattr__(self, "stream_roots", MappingProxyType(dict(self.stream_roots)))

    def projection(self) -> dict[str, object]:
        return {
            "derivation_rule": self.derivation_rule,
            "streams": sorted(self.streams),
            "roots": {k: v for k, v in self.roots.items()},
            "stream_roots": {k: v for k, v in self.stream_roots.items()},
        }


@sealed
@final
@dataclass(frozen=True)
class Deterministic:
    """Carries nothing: the run claims no RNG dependence at all."""

    def projection(self) -> dict[str, object]:
        return {"variant": "deterministic"}


@sealed
@final
@dataclass(frozen=True)
class Seeded:
    plan: SeedPlan

    def projection(self) -> dict[str, object]:
        return {"variant": "seeded", "plan": self.plan.projection()}


@sealed
@final
@dataclass(frozen=True)
class StochasticUnseeded:
    rationale: str

    def __post_init__(self) -> None:
        if not self.rationale:
            raise MalformedSpec("stochastic-unseeded carries a rationale — an empty one declares nothing")

    def projection(self) -> dict[str, object]:
        return {"variant": "stochastic-unseeded", "rationale": self.rationale}


NondeterminismContract = Deterministic | Seeded | StochasticUnseeded


@sealed
@final
@dataclass(frozen=True)
class RealizedSeeds:
    """Occurrence member: `[semantic job key][stream key] -> seed` (§6.2).
    Nested by construction — a flat, job-keyed record has one slot for two
    streams and cannot represent a two-stream plan (R20 negative (b))."""

    seeds: Mapping[str, Mapping[str, int]]

    def __post_init__(self) -> None:
        for job_key, per_stream in self.seeds.items():
            if not isinstance(per_stream, Mapping):
                raise MalformedRecord(
                    f"realized seeds are keyed [job][stream]; {job_key!r} carries a bare value — "
                    "one slot cannot hold two streams (computation §6.2)"
                )
        object.__setattr__(
            self, "seeds", MappingProxyType({k: MappingProxyType(dict(v)) for k, v in self.seeds.items()})
        )

    def projection(self) -> dict[str, object]:
        return {job: dict(per_stream) for job, per_stream in self.seeds.items()}


@sealed
@final
@dataclass(frozen=True)
class ExclusionCertification:
    rationale: str
    attribution: str

    def __post_init__(self) -> None:
        if not self.rationale or not self.attribution:
            raise MalformedSpec("an exclusion certification carries a rationale and an attribution (§5.2)")


@sealed
@final
@dataclass(frozen=True)
class SpecInput:
    role: str
    dataset: str
    exclusion: ExclusionCertification | None = None

    def __post_init__(self) -> None:
        if self.role not in SPEC_INPUT_ROLES:
            raise MalformedSpec(f"input role {self.role!r} is outside the closed set {SPEC_INPUT_ROLES}")
        if self.exclusion is not None and self.role != "reads":
            raise MalformedSpec("an exclusion certification is inline on a `reads` entry only (§5.2)")


@sealed
@final
@dataclass(frozen=True)
class RuleFixture:
    arguments: tuple[object, ...]
    expected: object


@sealed
@final
@dataclass(frozen=True)
class RuleImplementation:
    identity: str
    evaluate: Callable[..., object]
    fixtures: tuple[RuleFixture, ...]

    def __post_init__(self) -> None:
        if not self.identity:
            raise MalformedSpec("an implementation carries its content identity")


class HeldImplementation(Protocol):
    """The fixture-carrying implementation shape bound by ``freeze``."""

    @property
    def identity(self) -> str: ...

    @property
    def evaluate(self) -> Callable[..., object]: ...

    @property
    def fixtures(self) -> tuple[RuleFixture, ...]: ...


def implementation_conforms(impl: HeldImplementation) -> bool:
    """An evaluator that raises does not conform; comparison is exact (==)."""
    for fixture in impl.fixtures:
        try:
            if impl.evaluate(*fixture.arguments) != fixture.expected:
                return False
        except Exception:  # noqa: BLE001 — any raise from an arbitrary implementation is non-conformance
            return False
    return True


def bind_rules(named: tuple[str, ...], held: Mapping[str, HeldImplementation]) -> tuple[tuple[str, str], ...]:
    bound: dict[str, str] = {}
    for rule in named:
        if rule not in held:
            raise RuleUnbound(f"{rule!r} names no held implementation — the registry route is the rules store's")
        if not implementation_conforms(held[rule]):
            raise RuleUnbound(f"{rule!r}: the held implementation fails its fixtures and is not that rule (§3.1b)")
        bound[rule] = held[rule].identity
    return tuple(sorted(bound.items()))


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


@sealed
@final
@dataclass(frozen=True)
class SpecDraft:
    target: str
    estimand: str
    method: str
    assumptions: str
    falsification: str
    input_roles: tuple[SpecInput, ...]
    applicability: str
    interpretation_rule: str
    equivalence_rule: str
    parameters: Mapping[str, object]
    nondeterminism: Deterministic | Seeded | StochasticUnseeded

    def __post_init__(self) -> None:
        if not isinstance(self.input_roles, tuple) or not all(
            isinstance(entry, SpecInput) for entry in self.input_roles
        ):
            raise MalformedSpec("input_roles holds SpecInput values only")
        object.__setattr__(
            self,
            "parameters",
            MappingProxyType({key: _freeze_parameter_value(value) for key, value in self.parameters.items()}),
        )


@sealed
@final
@dataclass(frozen=True, init=False)
class FrozenSpec:
    target: str
    estimand: str
    method: str
    assumptions: str
    falsification: str
    input_roles: tuple[SpecInput, ...]
    applicability: str
    interpretation_rule: str
    equivalence_rule: str
    parameters: Mapping[str, object]
    nondeterminism: Deterministic | Seeded | StochasticUnseeded
    rule_bindings: tuple[tuple[str, str], ...]
    supersedes: str | None
    identity: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("FrozenSpec values are minted by freeze, revise or restore")

    def __post_init__(self) -> None:
        if not isinstance(self.input_roles, tuple) or not all(
            isinstance(entry, SpecInput) for entry in self.input_roles
        ):
            raise MalformedSpec("input_roles holds SpecInput values only")
        object.__setattr__(
            self,
            "parameters",
            MappingProxyType({key: _freeze_parameter_value(value) for key, value in self.parameters.items()}),
        )


def _mint_frozen_spec(**members: object) -> FrozenSpec:
    spec = object.__new__(FrozenSpec)
    for field in fields(FrozenSpec):
        object.__setattr__(spec, field.name, members[field.name])
    spec.__post_init__()
    return spec


@sealed
@final
@dataclass(frozen=True)
class SuccessorAdmitted:
    candidate: str


@sealed
@final
@dataclass(frozen=True)
class SuccessorRefused:
    candidate: str
    reason: str


def admit_successor(
    candidate: FrozenSpec,
    superseded: FrozenSpec,
    recorded_failures: frozenset[str],
    unfinished_attempts: frozenset[str],
) -> SuccessorAdmitted | SuccessorRefused:
    """G4 over the slice's value state — the two blocker classes the boundary
    derives (successor-admission design §3). The first check is byte-identical
    to cut 3's line, so a spec in both classes refuses with the recorded-failure
    reason by statement order, never by set iteration. A failure absent from
    both sets never happened: undetectable."""
    if superseded.identity in recorded_failures and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to a recorded failed replay")
    if superseded.identity in unfinished_attempts and candidate.supersedes != superseded.identity:
        return SuccessorRefused(candidate.identity, "an unreferenced successor to an unfinished recorded attempt")
    return SuccessorAdmitted(candidate.identity)


def _facet_projection(draft: SpecDraft | FrozenSpec, rule_bindings, supersedes) -> dict[str, object]:
    facet: dict[str, object] = {
        "target": draft.target,
        "estimand": draft.estimand,
        "method": draft.method,
        "assumptions": draft.assumptions,
        "falsification": draft.falsification,
        "input_roles": [
            {"role": entry.role, "dataset": entry.dataset}
            | (
                {"exclusion": {"rationale": entry.exclusion.rationale, "attribution": entry.exclusion.attribution}}
                if entry.exclusion is not None
                else {}
            )
            for entry in draft.input_roles
        ],
        "applicability": draft.applicability,
        "interpretation_rule": draft.interpretation_rule,
        "equivalence_rule": draft.equivalence_rule,
        "parameters": _project_parameter_value(draft.parameters),
        "nondeterminism": draft.nondeterminism.projection(),
        "rule_bindings": [list(pair) for pair in rule_bindings],
    }
    if supersedes is not None:
        facet["supersedes"] = supersedes
    return facet


def freeze(
    draft: SpecDraft, *, held_rules: Mapping[str, HeldImplementation], supersedes: str | None = None
) -> FrozenSpec:
    if not draft.target:
        raise MalformedSpec("an assessment spec targets a proposition; an empty target is not a spec (R7)")
    if isinstance(draft.nondeterminism, StochasticUnseeded) and draft.equivalence_rule in BITWISE_EQUIVALENCE_RULES:
        raise UnfreezableSpec(
            "stochastic-unseeded cannot support a bitwise equivalence rule — the §1.2 contradiction, "
            "caught at freeze because both halves are now in one frozen record (computation §3.1a)"
        )
    rule_bindings = bind_rules((draft.interpretation_rule, draft.equivalence_rule), held_rules)
    identity = v1.digest(SPEC_DOMAIN, _facet_projection(draft, rule_bindings, supersedes))
    members = {f.name: getattr(draft, f.name) for f in fields(SpecDraft)}
    return _mint_frozen_spec(**members, rule_bindings=rule_bindings, supersedes=supersedes, identity=identity)


def frozen_projection(spec: FrozenSpec) -> dict[str, object]:
    """The mapping `SPEC_DOMAIN` digests for a frozen spec — what a stored
    `analysis-spec` record carries as canonical text (design §7)."""
    if type(spec) is not FrozenSpec:
        raise MalformedRecord("frozen_projection requires a FrozenSpec")
    return _facet_projection(spec, spec.rule_bindings, spec.supersedes)


_FROZEN_MEMBERS = frozenset(
    {
        "target", "estimand", "method", "assumptions", "falsification", "input_roles", "applicability",
        "interpretation_rule", "equivalence_rule", "parameters", "nondeterminism", "rule_bindings",
    }
)
_TEXT_MEMBERS = ("target", "estimand", "method", "assumptions", "falsification", "applicability", "interpretation_rule", "equivalence_rule")


def _text(mapping: Mapping[str, object], name: str, where: str) -> str:
    value = mapping[name]
    if type(value) is not str:
        raise MalformedRecord(f"{where}: {name} is a string")
    return value


def _restore_input(entry: object, where: str) -> SpecInput:
    if not isinstance(entry, dict) or not {"role", "dataset"} <= set(entry) <= {"role", "dataset", "exclusion"}:
        raise MalformedRecord(f"{where}: a spec input names role and dataset, with an optional exclusion")
    exclusion = None
    if "exclusion" in entry:
        claim = entry["exclusion"]
        if not isinstance(claim, dict) or set(claim) != {"rationale", "attribution"}:
            raise MalformedRecord(f"{where}: an exclusion names exactly rationale and attribution")
        exclusion = ExclusionCertification(rationale=_text(claim, "rationale", where), attribution=_text(claim, "attribution", where))
    return SpecInput(role=_text(entry, "role", where), dataset=_text(entry, "dataset", where), exclusion=exclusion)


def _restore_nondeterminism(value: object, where: str) -> NondeterminismContract:
    if not isinstance(value, dict) or type(value.get("variant")) is not str:
        raise MalformedRecord(f"{where}: a nondeterminism member names its variant")
    variant = value["variant"]
    if variant == "deterministic" and set(value) == {"variant"}:
        return Deterministic()
    if variant == "stochastic-unseeded" and set(value) == {"variant", "rationale"}:
        return StochasticUnseeded(rationale=_text(value, "rationale", where))
    if variant == "seeded" and set(value) == {"variant", "plan"}:
        plan = value["plan"]
        if not isinstance(plan, dict) or set(plan) != {"derivation_rule", "streams", "roots", "stream_roots"}:
            raise MalformedRecord(f"{where}: a seed plan names derivation_rule, streams, roots and stream_roots")
        streams, roots, stream_roots = plan["streams"], plan["roots"], plan["stream_roots"]
        if not isinstance(streams, list) or any(type(s) is not str for s in streams):
            raise MalformedRecord(f"{where}: seed plan streams are strings")
        if not isinstance(roots, dict) or any(type(k) is not str or type(v) is not int for k, v in roots.items()):
            raise MalformedRecord(f"{where}: seed plan roots map stream keys to integers")
        if not isinstance(stream_roots, dict) or any(type(k) is not str or type(v) is not str for k, v in stream_roots.items()):
            raise MalformedRecord(f"{where}: seed plan stream roots map strings to strings")
        return Seeded(plan=SeedPlan(derivation_rule=_text(plan, "derivation_rule", where), streams=tuple(streams), roots=dict(roots), stream_roots=dict(stream_roots)))
    raise MalformedRecord(f"{where}: nondeterminism variant {variant!r} is not one of the three")


def restore(identity: str, projection: bytes) -> FrozenSpec:
    """The third mint: a frozen spec from its stored canonical projection
    (design §7). Refuses text that is not canonical, a mapping that is not
    exactly the frozen members, a digest that is not `identity`, any member of
    the wrong type — nothing is coerced — and the pair `freeze` refuses, so a
    stored spec is exactly one `freeze` produced."""
    where = f"analysis-spec {identity[:12]}"
    try:
        mapping = v1.decode(projection)
    except CanonicalTextRefused as refused:
        raise MalformedRecord(f"{where}: the projection is not canonical text: {refused}") from refused
    if not isinstance(mapping, dict) or not _FROZEN_MEMBERS <= set(mapping) <= _FROZEN_MEMBERS | {"supersedes"}:
        raise MalformedRecord(f"{where}: the projection carries exactly the frozen members")
    if v1.digest(SPEC_DOMAIN, mapping) != identity:
        raise MalformedRecord(f"{where}: the projection does not digest to the identity")
    text = {name: _text(mapping, name, where) for name in _TEXT_MEMBERS}
    if not text["target"]:
        raise MalformedRecord(f"{where}: an assessment spec targets a proposition; an empty target is not a spec (R7)")
    if not isinstance(mapping["input_roles"], list):
        raise MalformedRecord(f"{where}: input_roles is a list")
    if not isinstance(mapping["parameters"], dict) or any(type(k) is not str for k in mapping["parameters"]):
        raise MalformedRecord(f"{where}: parameters is a mapping with string keys")
    bindings = mapping["rule_bindings"]
    if not isinstance(bindings, list) or any(
        not isinstance(pair, list) or len(pair) != 2 or any(type(half) is not str for half in pair) for pair in bindings
    ):
        raise MalformedRecord(f"{where}: rule bindings are string pairs")
    nondeterminism = _restore_nondeterminism(mapping["nondeterminism"], where)
    if isinstance(nondeterminism, StochasticUnseeded) and text["equivalence_rule"] in BITWISE_EQUIVALENCE_RULES:
        raise UnfreezableSpec("stochastic-unseeded cannot support a bitwise equivalence rule (computation §3.1a)")
    supersedes = mapping.get("supersedes")
    if supersedes is not None and type(supersedes) is not str:
        raise MalformedRecord(f"{where}: supersedes is a string")
    spec = _mint_frozen_spec(
        **text,
        input_roles=tuple(_restore_input(entry, where) for entry in mapping["input_roles"]),
        parameters=mapping["parameters"],
        nondeterminism=nondeterminism,
        rule_bindings=tuple((pair[0], pair[1]) for pair in bindings),
        supersedes=supersedes,
        identity=identity,
    )
    if v1.encode(frozen_projection(spec)) != projection:
        # A member the value canonicalizes (a seed plan sorts its streams) can be
        # spelled otherwise in canonical text and still digest to `identity`; the
        # restored spec would then project to other bytes and another digest.
        raise MalformedRecord(f"{where}: the projection is not the restored spec's own projection")
    return spec


def revise(
    original: FrozenSpec,
    *,
    edits: Mapping[str, object],
    held_rules: Mapping[str, HeldImplementation],
    recorded_failures: frozenset[str],
) -> FrozenSpec:
    """The only edit path. Always mints with `supersedes=original.identity`,
    so the successor to a recorded failed replay carries its reference by
    construction; `admit_successor` is the value-state check the boundary
    applies to specs it did not mint (G4)."""
    draft = SpecDraft(
        target=cast(str, edits.get("target", original.target)),
        estimand=cast(str, edits.get("estimand", original.estimand)),
        method=cast(str, edits.get("method", original.method)),
        assumptions=cast(str, edits.get("assumptions", original.assumptions)),
        falsification=cast(str, edits.get("falsification", original.falsification)),
        input_roles=cast(tuple[SpecInput, ...], edits.get("input_roles", original.input_roles)),
        applicability=cast(str, edits.get("applicability", original.applicability)),
        interpretation_rule=cast(str, edits.get("interpretation_rule", original.interpretation_rule)),
        equivalence_rule=cast(str, edits.get("equivalence_rule", original.equivalence_rule)),
        parameters=cast(Mapping[str, object], edits.get("parameters", original.parameters)),
        nondeterminism=cast(NondeterminismContract, edits.get("nondeterminism", original.nondeterminism)),
    )
    return freeze(draft, held_rules=held_rules, supersedes=original.identity)
