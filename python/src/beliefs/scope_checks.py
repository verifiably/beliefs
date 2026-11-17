"""Checked reads of a structural comparison's selected scope context.

Scope containment design §7.3. A structural ``compare_scopes`` result reads no
record and confers no authority. A ``ScopeReader`` computes the same result,
records it, and before returning it checks every selected rule root: the
operation's eligibility callback first (when one is supplied), then each rule's
held body, kind and classes sort against the selected relations, and its ordinary
references through the existing body walker. A failure anywhere in the selected
component refuses the use with ``ScopeDependencyIneligible``; there is no
smaller-graph or unknown fallback.

``require_eligible=None`` means an authoring check over held records, never
snapshot permission. Snapshot and captured-input adapters supply the callback.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from nodes.core.node import Node

from beliefs.classification_rule import ClassificationRule
from beliefs.contract.scope import RuleScopeEndpoint
from beliefs.dependencies import HeldRecords, Record, read_record, walk
from beliefs.errors import ScienceError, ScopeDependencyIneligible
from beliefs.profile import ProfileSpec
from beliefs.restriction import RestrictionMap, ScopeComparison, compare_scopes, scope_rule_ids

__all__ = ["ScopeReader", "author_scope_reader", "held_scope_reader"]


class ScopeReader:
    """One operation's checked scope comparisons and the reads they selected."""

    def __init__(
        self,
        profile: ProfileSpec,
        read: Callable[[str], Record],
        require_eligible: Callable[[tuple[str, ...]], None] | None,
    ) -> None:
        self.profile = profile
        self._read = read
        self._require = require_eligible
        self._comparisons: list[ScopeComparison] = []
        self._reads: dict[str, Record | None] = {}

    @property
    def comparisons(self) -> tuple[ScopeComparison, ...]:
        """Every comparison computed through this reader, in order, checked or not."""
        return tuple(self._comparisons)

    @property
    def reads(self) -> tuple[str, ...]:
        """Every selected ordinary record this reader attempted, in first-read order."""
        return tuple(self._reads)

    def held(self, id: str) -> Record:
        """A typed held body that is not scope context (a procedure or proxy the
        operation already depends on); not recorded as a selected read."""
        return self._read(id)

    def compare(self, a: RestrictionMap, b: RestrictionMap) -> ScopeComparison:
        comparison = compare_scopes(a, b, self.profile)
        self._comparisons.append(comparison)
        roots = scope_rule_ids(comparison, self.profile)
        if roots:
            if self._require is not None:
                self._require(roots)
            self._check(comparison, roots)
        return comparison

    def _follow(self, id: str, visiting: set[str]) -> Record:
        if id in self._reads and self._reads[id] is not None:
            return cast(Record, self._reads[id])
        self._reads.setdefault(id, None)
        value = self._read(id)
        self._reads[id] = value
        visiting.add(id)
        for reference in sorted(walk(value, self.profile).references):
            if reference not in visiting:
                self._follow(reference, visiting)
        return value

    def _check(self, comparison: ScopeComparison, roots: tuple[str, ...]) -> None:
        failed: dict[str, str] = {}
        rules: dict[str, ClassificationRule] = {}
        for root in roots:
            try:
                value = self._follow(root, set())
            except ScienceError as error:
                failed[root] = f"{type(error).__name__}: {error}"
                continue
            if not isinstance(value, ClassificationRule):
                failed[root] = f"names a {type(value).__name__}, not a classification rule"
                continue
            rules[root] = value
        for term in comparison.relations:
            relation = self.profile.scope_relations[term]
            restriction = self.profile.dimensions[relation.declaration.dimension].restriction
            leaf = restriction.of if restriction is not None and restriction.form == "union" else restriction
            for endpoint in (relation.declaration.left, relation.declaration.right):
                if not isinstance(endpoint, RuleScopeEndpoint) or endpoint.rule not in rules:
                    continue
                classes = rules[endpoint.rule].classes
                if leaf is None or classes != leaf.classes:
                    failed[endpoint.rule] = f"classes sort {classes!r} is not the dimension's"
                    continue
                identifier_class = self.profile.sorts[classes].identifier_class
                if identifier_class is not None and not identifier_class.matches(endpoint.classes[0]):
                    failed[endpoint.rule] = f"class {endpoint.classes[0]!r} is outside {classes!r}"
        if failed:
            detail = "; ".join(f"{id}: {reason}" for id, reason in sorted(failed.items()))
            raise ScopeDependencyIneligible(
                f"scope-dependency-ineligible: selected scope dependencies cannot be used ({detail})", tuple(failed)
            )


class _NodeRecords:
    def __init__(self, holds: Callable[[str], bool], read: Callable[[str], Node]) -> None:
        self.holds = holds
        self.read = read


def held_scope_reader(
    profile: ProfileSpec, *, holds: Callable[[str], bool], read: Callable[[str], Node]
) -> ScopeReader:
    """An authoring reader over any held-node lookup, decoding with ``read_record``."""
    records = cast(HeldRecords, _NodeRecords(holds, read))
    return ScopeReader(profile, lambda id: read_record(records, id), None)


def author_scope_reader(profile: ProfileSpec, records: HeldRecords) -> ScopeReader:
    """The authoring-time reader over held records: every selected rule must be held and valid."""
    return ScopeReader(profile, lambda id: read_record(records, id), None)
