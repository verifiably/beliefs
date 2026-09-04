"""The two-root world-changing operations: move and consolidate.

Portable: `relocation` takes its writers as arguments, so these run against
`DefaultExecutor` behind the test recorder. What they cannot claim is cut-16
discharge — that runs on the certified engine, under the acceptance runner.
"""

from __future__ import annotations

from beliefs.errors import (
    AddressDisagreement,
    ContractPinDisagreement,
    DuplicateLocation,
    RelocationKindExcluded,
    RelocationRefused,
    RelocationTargetMissing,
    SameRootRefused,
    WriteRefused,
)


def test_every_relocation_refusal_is_a_write_refusal():
    for error in (
        RelocationRefused, SameRootRefused, AddressDisagreement, DuplicateLocation,
        ContractPinDisagreement, RelocationKindExcluded, RelocationTargetMissing,
    ):
        assert issubclass(error, WriteRefused)
