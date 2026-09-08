"""The guard modules that are cited, not run, and what the tree has done to them since.

A conformance guard leaves the live chain by a **ruling**, never by quietly falling out
of an inventory, and from that moment its bytes are evidence rather than machinery: the
module is what produced the discharge later cuts cite, so it is pinned as it stood and
never edited. This registry is where that ruling becomes machine-checked — the doctrine
is `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`, and
`tests/test_frozen_guards.py` holds the tree to it.

`falsified_pins` is the honest half. A cited-not-run guard's own pin table goes on
claiming things about a tree that has moved on, and those claims are not repaired: the
mismatch is recorded here, with the commit that caused it, so that the next reader meets
a stated consequence of the freeze instead of what looks like a regression.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CitedNotRun:
    """One guard module's standing."""

    cut: int
    ruled_by: str
    """The document that took the module out of the live chain."""
    standing_record: str
    """The discharge that still stands, and that later cuts cite in its place."""
    successor: str
    """What carries the coverage now — a citation is not a hole."""
    reason: str
    falsified_pins: dict[str, str] = field(default_factory=dict)
    """Pin target -> what moved it. Recorded, never repaired."""


MOVED_BY_VERIFICATION_PUBLICATION = (
    "moved at 1e92471, when the verification-publication slice rewrote the cut-3 and cut-5 "
    "arm declarations against the landed source under the fix-the-arm-never-the-source rule"
)

CITED_NOT_RUN: dict[str, CitedNotRun] = {
    "test_n2_cut4.py": CitedNotRun(
        cut=4,
        ruled_by="docs/plans/2026-09-02-conformance-cut-14-results.md",
        standing_record="docs/plans/2026-08-18-conformance-cut-4-results.md",
        successor="cut 14's twelve-module inventory, which begins at cut 6",
        reason=(
            "Cut 14 re-rooted the chain onto twelve frozen phase modules beginning at cut 6 "
            "(its results record §2) and cut 4's guard is not among them. No document names "
            "the drop: unlike cuts 5, 8 and 10 this one was implicit, which is the case this "
            "registry exists to make impossible. The inventory is the ruling of record."
        ),
    ),
    "test_n2_cut5.py": CitedNotRun(
        cut=5,
        ruled_by="docs/plans/2026-09-02-conformance-cut-14-results.md",
        standing_record="docs/plans/2026-08-19-conformance-cut-5-results.md",
        successor="cut 14's own arms, which cite cut 5's record rather than re-running it",
        reason=(
            "\"Cut 14 cites cut 5 ... it does not invoke cut 5 or an aggregate runner\" (cut 14 "
            "results §3), which pins the whole cut-5 surface by SHA-256 in FROZEN_CUT5_SHA256; "
            "`pyproject.toml` excludes the module from pyright for the same reason. The slice "
            "that moved the cut-5 arms edited this module once (205e5f7) and re-minted cut 14's "
            "content pin; both were reverted on 2026-09-07 — see the doctrine's §5."
        ),
    ),
    "test_n2_cut8.py": CitedNotRun(
        cut=8,
        ruled_by="docs/plans/2026-08-23-root-lifecycle-ledger.md",
        standing_record="docs/plans/2026-08-22-conformance-cut-8-results.md",
        successor="cut 9's store units, the successor certification named by R15",
        reason=(
            "Ruling R15: the root-lifecycle plan's Task 4 deleted the shape-only store refusal "
            "that cut 8's label 6 and store-refusal arms certify, so those declarations fail on "
            "the tree by design. Cut 9's runner and guard both state it in their docstrings."
        ),
        falsified_pins={
            "python/tests/n2_arms_cut5.py": MOVED_BY_VERIFICATION_PUBLICATION,
            "python/tests/acceptance/test_n2_cut6.py": (
                "moved after the 5a02ca2 package rename; cuts 7 and 9 re-pinned their own "
                "entries for it while they were live, and cut 8, already cited, did not"
            ),
        },
    ),
    "test_n2_cut10.py": CitedNotRun(
        cut=10,
        ruled_by="docs/designs/2026-09-04-write-permits-design.md",
        standing_record="docs/plans/2026-08-24-conformance-cut-10-results.md",
        successor="cut 16's E1 and E7 holdings arms, plus its labeled unit K1",
        reason=(
            "Write-permits design §13.1, 'Cut 10 is cited, not run': E6 requires `_publish` to "
            "begin with its `require` statement, so the H4u1 and J8 `before` blocks match "
            "nothing from cut 16's tree onward. The whole cut-10 surface — design, declarations, "
            "guard and runner — is left byte-identical and pinned so by cut 17's "
            "FROZEN_CUT10_SHA256, which is why its own table cannot be repaired."
        ),
        falsified_pins={"python/tests/n2_arms_cut5.py": MOVED_BY_VERIFICATION_PUBLICATION},
    ),
}
