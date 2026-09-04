"""What a derivation recomputation is handed, and what it answers with.

These three values sit in their own module because both sides of the audit
seam will need them: `beliefs.audit` recomputes with them now, and
`beliefs.corpus` names them at the import boundary from the explicit-import
work on. A module that imported `beliefs.corpus` to name `Finding` would close
that loop, so the reference is a type-checking one and nothing here imports the
corpus at run time.

Evidence is **supplied**, never ambient (M11's doctrine): a recomputation that
reached for a registry of held specs would decide by process state, and two
holders of the same bytes would reach different verdicts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from beliefs.replay import EquivalenceImplementation
from beliefs.sealed import sealed
from beliefs.spec import FrozenSpec, RuleImplementation

if TYPE_CHECKING:
    from beliefs.corpus import Finding

__all__ = ["NO_EVIDENCE", "DerivationEvidence", "DerivationOutcome"]


@sealed
@final
@dataclass(frozen=True)
class DerivationEvidence:
    """What the caller holds: frozen specs, equivalence-rule implementations
    keyed by identity, and interpretation-rule implementations keyed by
    identity. Supplied explicitly, never ambient (M11's doctrine)."""

    specs: Mapping[str, FrozenSpec]
    held_rules: Mapping[str, EquivalenceImplementation]
    implementations: Mapping[str, RuleImplementation]


NO_EVIDENCE = DerivationEvidence(specs={}, held_rules={}, implementations={})
"""Every mapping empty — an explicit *nothing held*, so a caller that holds no
evidence says so rather than defaulting into one."""


@sealed
@final
@dataclass(frozen=True)
class DerivationOutcome:
    """Checked and agreeing, checked and contradicted, or not checked at all.

    `reason` is why a recomputation could not run, and it is never a verdict:
    an unchecked derivation is neither validated nor contradicted.
    """

    checked: bool
    reason: str
    contradiction: Finding | None
