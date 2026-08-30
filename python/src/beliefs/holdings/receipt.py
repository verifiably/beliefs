"""Derive and re-run the receipt for one holdings reduction."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import cast, final

from beliefs.errors import (
    BuildContended,
    CaptureDrift,
    CorpusStateMalformed,
    CoverageNotLive,
    CoverageUnknown,
    CoverageUnresolvable,
    LogEvidenceRefused,
    RuleNotHeld,
)
from beliefs.holdings.project import StateFacts, capture_coverage
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.world import registry, rules
from beliefs.world.logmodel import ChainView

__all__ = [
    "HOLDINGS_RECEIPT_DOMAIN",
    "HoldingsReceipt",
    "HoldingsReceiptOutcome",
    "derive_holdings",
    "output_digest",
    "validate_holdings_receipt",
]

HOLDINGS_RECEIPT_DOMAIN = "science.holdings-receipt.v1"
_KIND = "holdings-reduction"
_OUTCOMES = ("validated", "refuted", "unresolvable", "malformed")
_FIELDS = {
    "kind",
    "coverage",
    "rule_identity",
    "implementation_identity",
    "active_set_digest",
    "blocked_set_digest",
}

ChainReader = Callable[[Path], ChainView]
Output = list[dict[str, object]]


def _digest(value: object, width: int, name: str) -> str:
    if type(value) is not str or not re.fullmatch(rf"[0-9a-f]{{{width}}}", value):
        raise ValueError(f"{name} must be {width} lowercase hexadecimal characters")
    return value


@sealed
@final
@dataclass(frozen=True)
class HoldingsReceipt:
    kind: str
    coverage: tuple[tuple[str, str, str], ...]
    rule_identity: str
    implementation_identity: str
    active_set_digest: str
    blocked_set_digest: str

    def __post_init__(self) -> None:
        if self.kind != _KIND:
            raise ValueError(f"kind must be {_KIND!r}")
        if type(self.coverage) is not tuple:
            raise TypeError("coverage must be an exact tuple")
        corpus_ids: list[str] = []
        for member in self.coverage:
            if type(member) is not tuple or len(member) != 3:
                raise TypeError("each coverage member must be an exact (corpus_id, corpus_state, chain_head) triple")
            corpus_id, corpus_state, chain_head = member
            corpus_ids.append(_digest(corpus_id, 32, "corpus_id"))
            _digest(corpus_state, 64, "corpus_state")
            _digest(chain_head, 64, "chain_head")
        if corpus_ids != sorted(corpus_ids) or len(corpus_ids) != len(set(corpus_ids)):
            raise ValueError("coverage must be sorted and deduplicated by corpus_id")
        _digest(self.rule_identity, 64, "rule_identity")
        _digest(self.implementation_identity, 64, "implementation_identity")
        _digest(self.active_set_digest, 64, "active_set_digest")
        _digest(self.blocked_set_digest, 64, "blocked_set_digest")

    def identity(self) -> str:
        return v1.digest(
            HOLDINGS_RECEIPT_DOMAIN,
            [
                self.kind,
                [[corpus_id, state, head] for corpus_id, state, head in self.coverage],
                self.rule_identity,
                self.implementation_identity,
                self.active_set_digest,
                self.blocked_set_digest,
            ],
        )


@dataclass(frozen=True)
class HoldingsReceiptOutcome:
    outcome: str
    detail: str

    def __post_init__(self) -> None:
        if self.outcome not in _OUTCOMES:
            raise ValueError(f"outcome must be one of {list(_OUTCOMES)}")
        if type(self.detail) is not str or not self.detail:
            raise ValueError("detail must be a non-empty exact string")


def output_digest(value: object) -> str:
    return sha256(v1.encode(value)).hexdigest()


def _outputs(value: object) -> tuple[Output, Output]:
    if type(value) is not dict or set(value) != {"active", "blocked"}:
        raise ValueError("the holdings reducer must return exactly active and blocked")
    active = value["active"]
    blocked = value["blocked"]
    if type(active) is not list or type(blocked) is not list:
        raise ValueError("the holdings reducer's active and blocked values must be lists")
    if not all(type(member) is dict for member in (*active, *blocked)):
        raise ValueError("the holdings reducer's members must be objects")
    return active, blocked


def _coverage(capture: Mapping[str, object]) -> tuple[tuple[str, str, str], ...]:
    corpora = capture["corpora"]
    if type(corpora) is not list:
        raise TypeError("captured corpora must be a list")
    covered: list[tuple[str, str, str]] = []
    for corpus in corpora:
        if type(corpus) is not dict:
            raise TypeError("each captured corpus must be an object")
        covered.append(
            (
                cast(str, corpus["corpus_id"]),
                cast(str, corpus["corpus_state"]),
                cast(str, corpus["chain_head"]),
            )
        )
    return tuple(covered)


def _held(world: registry.World, binding: rules.RuleBinding) -> rules._HeldRule:
    with registry._locked_barrier(world) as world_root:
        return rules._locked_resolve_rule_binding(world_root, binding)


def derive_holdings(
    world: registry.World,
    coverage: frozenset[str],
    binding: rules.RuleBinding,
    *,
    chain_view: ChainReader,
    state_facts: StateFacts,
) -> tuple[Output, Output, HoldingsReceipt]:
    captured = capture_coverage(world, coverage, chain_view=chain_view, state_facts=state_facts)
    active, blocked = _outputs(_held(world, binding).invoke(captured))
    receipt = HoldingsReceipt(
        kind=_KIND,
        coverage=_coverage(captured),
        rule_identity=binding.rule_identity,
        implementation_identity=binding.implementation_identity,
        active_set_digest=output_digest(active),
        blocked_set_digest=output_digest(blocked),
    )
    return active, blocked, receipt


def _from_mapping(value: Mapping[object, object]) -> HoldingsReceipt:
    if set(value) != _FIELDS:
        raise ValueError(f"a holdings receipt must have exactly {sorted(_FIELDS)}")
    raw_coverage = value["coverage"]
    if type(raw_coverage) not in (list, tuple):
        raise TypeError("coverage must be a sequence")
    coverage: list[tuple[str, str, str]] = []
    for row in cast(list[object] | tuple[object, ...], raw_coverage):
        if type(row) not in (list, tuple):
            raise TypeError("each coverage row must have three members")
        members = cast(list[object] | tuple[object, ...], row)
        if len(members) != 3:
            raise TypeError("each coverage row must have three members")
        coverage.append((cast(str, members[0]), cast(str, members[1]), cast(str, members[2])))
    return HoldingsReceipt(
        kind=cast(str, value["kind"]),
        coverage=tuple(coverage),
        rule_identity=cast(str, value["rule_identity"]),
        implementation_identity=cast(str, value["implementation_identity"]),
        active_set_digest=cast(str, value["active_set_digest"]),
        blocked_set_digest=cast(str, value["blocked_set_digest"]),
    )


def _named_capture(
    current: dict[str, object],
    named: tuple[tuple[str, str, str], ...],
) -> dict[str, object] | None:
    corpora = current["corpora"]
    if type(corpora) is not list or len(corpora) != len(named):
        return None
    selected: list[dict[str, object]] = []
    for corpus, (corpus_id, corpus_state, chain_head) in zip(corpora, named, strict=True):
        if type(corpus) is not dict:
            return None
        if corpus.get("corpus_id") != corpus_id or corpus.get("corpus_state") != corpus_state:
            return None
        chain = corpus.get("chain")
        if type(chain) is not list:
            return None
        try:
            end = next(index for index, row in enumerate(chain) if type(row) is dict and row.get("digest") == chain_head)
        except StopIteration:
            return None
        prefix = dict(corpus)
        prefix["chain_head"] = chain_head
        prefix["chain"] = chain[: end + 1]
        selected.append(prefix)
    return {"corpora": selected}


def validate_holdings_receipt(
    world: registry.World,
    receipt: HoldingsReceipt,
    *,
    chain_view: ChainReader,
    state_facts: StateFacts,
) -> HoldingsReceiptOutcome:
    if type(receipt) is not HoldingsReceipt:
        try:
            if not isinstance(receipt, Mapping):
                raise TypeError("a receipt must be a HoldingsReceipt or mapping")
            _from_mapping(receipt)
        except (KeyError, TypeError, ValueError) as caught:
            return HoldingsReceiptOutcome("malformed", f"the receipt contract is malformed: {caught}")
        return HoldingsReceiptOutcome("malformed", "a mapping is not a constructed HoldingsReceipt")
    checked = receipt

    binding = rules.RuleBinding(checked.rule_identity, checked.implementation_identity)
    try:
        held = _held(world, binding)
    except RuleNotHeld as caught:
        return HoldingsReceiptOutcome("unresolvable", f"the exact binding is not held here: {caught}")

    try:
        current = capture_coverage(
            world,
            frozenset(corpus_id for corpus_id, _state, _head in checked.coverage),
            chain_view=chain_view,
            state_facts=state_facts,
        )
    except (
        BuildContended,
        CaptureDrift,
        CorpusStateMalformed,
        CoverageNotLive,
        CoverageUnknown,
        CoverageUnresolvable,
        LogEvidenceRefused,
    ) as caught:
        return HoldingsReceiptOutcome("unresolvable", f"the named coverage cannot be produced here: {caught}")
    selected = _named_capture(current, checked.coverage)
    if selected is None:
        return HoldingsReceiptOutcome(
            "unresolvable",
            "a named corpus state or chain head cannot be produced from the current validated chains",
        )
    try:
        active, blocked = _outputs(held.invoke(selected))
        active_digest = output_digest(active)
        blocked_digest = output_digest(blocked)
    except Exception as caught:  # noqa: BLE001 — any ordinary rule/output/digest failure refutes
        return HoldingsReceiptOutcome("refuted", f"the named implementation did not reproduce the outputs: {caught}")
    if active_digest != checked.active_set_digest or blocked_digest != checked.blocked_set_digest:
        return HoldingsReceiptOutcome("refuted", "the named reduction did not reproduce both output digests")
    return HoldingsReceiptOutcome("validated", "the named reduction reproduced both output digests")
