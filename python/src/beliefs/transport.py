"""The transport seam (publish-act-remote design §3.1, decision 1): the caller's
adapter moves bytes and reads the remote back, and the act — never the seam —
decides "verified complete" by comparing the remote's enumeration with its own
listing. Plain standard library over the export root; nothing of `atoms`."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination

__all__ = ["LISTING_DOMAIN", "Transport", "TransportAbandoned", "listing_identity", "local_listing", "transport_files"]

LISTING_DOMAIN = "science.publish-transport-listing.v1"


@dataclass(frozen=True)
class TransportAbandoned:
    """This attempt's upload will never complete (decision 4): a terminal answer,
    unlike an exception, which means "try again"."""

    detail: str


class Transport(Protocol):
    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None:
        """Upload every named file, idempotently: a retry converges on the same remote content."""
        ...

    def listing(self, destination: Destination, corpus_id: str) -> Mapping[str, str]:
        """Every remote file named `<corpus_id>.head-artifact.v1` or under `<corpus_id>/`,
        mapped to the SHA-256 hex of its remote bytes: what the remote holds, not what was asked."""
        ...


def transport_files(container: Path, corpus_id: str) -> dict[str, Path]:
    """Every regular file under `<container>/<corpus_id>`, named
    `<corpus_id>/<posix path relative to the root>`, and the sibling, named
    `<corpus_id>.head-artifact.v1`. The `.metadata` sibling is the engine's and is
    never named. A symlink or any other non-regular entry refuses."""
    root = Path(container) / corpus_id
    if root.is_symlink() or not root.is_dir():
        raise MalformedRecord(f"{root}: a transported root is a directory")
    files: dict[str, Path] = {}
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(dirnames)
        here = Path(directory)
        for name in (*dirnames, *filenames):
            if (here / name).is_symlink():
                raise MalformedRecord(f"{here / name}: a transported root holds no symlink")
        for name in sorted(filenames):
            path = here / name
            if not path.is_file():
                raise MalformedRecord(f"{path}: a transported root holds only regular files")
            files[f"{corpus_id}/{path.relative_to(root).as_posix()}"] = path
    sibling = Path(container) / f"{corpus_id}.head-artifact.v1"
    if sibling.is_symlink() or not sibling.is_file():
        raise MalformedRecord(f"{sibling}: the sibling is a regular file")
    files[sibling.name] = sibling
    return files


def local_listing(files: Mapping[str, Path]) -> dict[str, str]:
    """Each name mapped to the SHA-256 hex of its local bytes."""
    return {name: sha256(Path(path).read_bytes()).hexdigest() for name, path in sorted(files.items())}


def listing_identity(listing: Mapping[str, str]) -> str:
    """The `transported` outcome's `listing`: a digest of the verified listing alone."""
    return v1.digest(LISTING_DOMAIN, dict(sorted(listing.items())))
