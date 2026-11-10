"""The chain claim: one session per written chain per host.

A session claims each chain it writes (its write root, and its store root when
it has one) with an exclusive `flock` on the root directory itself. Nothing is
created inside the root or beside it, and the engine locks only its metadata
sibling's lock file, so the claim never contends with an operation lock.
`flock` binds to the open file description, so a second claim conflicts in the
same process as in another; process death releases it. The descriptor is
close-on-exec, so no child a session launches inherits the claim.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path

from beliefs.errors import ChainClaimed, ChainRole

__all__ = ["ChainClaim", "claim_chain"]


class ChainClaim:
    """One held claim: an open descriptor on the root with an exclusive
    `flock`. `release` closes it, which drops the lock; it is idempotent."""

    def __init__(self, root: Path, role: ChainRole, fd: int) -> None:
        self.root = root
        self.role: ChainRole = role
        self._fd: int | None = fd

    def release(self) -> None:
        fd, self._fd = self._fd, None
        if fd is not None:
            os.close(fd)


def claim_chain(root: Path, role: ChainRole) -> ChainClaim:
    """Claim `root` for one session, or raise `ChainClaimed` when another
    session holds it. A refused or failed claim closes its descriptor."""
    if role not in ("write root", "store root"):
        raise ValueError(f"a chain claim's role is the write root or the store root, not {role!r}")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as caught:
        os.close(fd)
        raise ChainClaimed(root, role) from caught
    except BaseException:
        os.close(fd)
        raise
    return ChainClaim(root, role, fd)
