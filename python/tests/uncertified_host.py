"""The declaration that a host cannot supply the certified kernel and volume tuple.

Its own module rather than a conftest local so the gate can be imported and
tested directly; conftest is not importable by name.
"""

import os

UNCERTIFIED_HOST_VAR = "BELIEFS_UNCERTIFIED_HOST"


def uncertified_host(environ: "os._Environ[str] | dict[str, str]") -> bool:
    """Whether this host has declared it cannot supply the certified tuple.

    Opt-in, and set in one place: the CI workflow. Anywhere it is unset — a
    developer machine, the pre-push gate, the certified host — the suite runs
    closed and `CapabilityUnavailable` is a failure, which is what AGENTS.md
    requires. Only an explicit "1" counts, so an empty or stray value cannot
    quietly disarm the gate.
    """
    return environ.get(UNCERTIFIED_HOST_VAR, "") == "1"
