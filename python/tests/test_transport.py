"""The transport seam (publish-act-remote design §3.1), portable: the naming of
an export root's files, the local listing and its identity, and the
directory-backed fake the acceptance module drives."""

from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

import pytest
from transport_fake import DirectoryTransport, TransportFault

from beliefs.errors import MalformedRecord
from beliefs.intents.publish import Destination
from beliefs.transport import TransportAbandoned, listing_identity, local_listing, transport_files

CORPUS = "1" * 32
REMOTE = Destination.remote("https://remote.test/pub")


def _container(tmp_path: Path) -> Path:
    """An export container: a root with a record, a nested record and a hidden chain file, and its sibling."""
    container = tmp_path / "export"
    root = container / CORPUS
    (root / "run").mkdir(parents=True)
    (root / ".#~chain").mkdir()
    (root / "corpus.yaml").write_bytes(b"manifest")
    (root / "run" / "a.md").write_bytes(b"a")
    (root / ".#~chain" / "0001").write_bytes(b"entry")
    (container / f"{CORPUS}.head-artifact.v1").write_bytes(b"artifact")
    return container


def test_every_regular_file_and_the_sibling_are_named(tmp_path):
    container = _container(tmp_path)
    assert sorted(transport_files(container, CORPUS)) == [
        f"{CORPUS}.head-artifact.v1",
        f"{CORPUS}/.#~chain/0001",
        f"{CORPUS}/corpus.yaml",
        f"{CORPUS}/run/a.md",
    ]


def test_the_metadata_sibling_is_never_named(tmp_path):
    container = _container(tmp_path)
    (container / f"{CORPUS}.metadata").mkdir()
    (container / f"{CORPUS}.metadata" / "store").write_bytes(b"engine")
    assert not any("metadata" in name for name in transport_files(container, CORPUS))


@pytest.mark.parametrize("where", ["file", "directory", "sibling"])
def test_a_symlink_refuses(tmp_path, where):
    container = _container(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    if where == "file":
        os.symlink(container / CORPUS / "run" / "a.md", container / CORPUS / "run" / "b.md")
    elif where == "directory":
        os.symlink(target, container / CORPUS / "linked")
    else:
        sibling = container / f"{CORPUS}.head-artifact.v1"
        sibling.rename(target / "artifact")
        os.symlink(target / "artifact", sibling)
    with pytest.raises(MalformedRecord):
        transport_files(container, CORPUS)


def test_a_missing_root_or_sibling_refuses(tmp_path):
    container = _container(tmp_path)
    with pytest.raises(MalformedRecord):
        transport_files(container, "2" * 32)
    (container / f"{CORPUS}.head-artifact.v1").unlink()
    with pytest.raises(MalformedRecord):
        transport_files(container, CORPUS)


def test_the_local_listing_digests_the_bytes(tmp_path):
    files = transport_files(_container(tmp_path), CORPUS)
    assert local_listing(files) == {name: sha256(path.read_bytes()).hexdigest() for name, path in files.items()}


def test_the_listing_identity_is_a_function_of_the_listing_alone():
    one = {"b": "1" * 64, "a": "2" * 64}
    assert listing_identity(one) == listing_identity(dict(sorted(one.items())))
    assert len(listing_identity(one)) == 64 and listing_identity(one) != listing_identity({"a": "2" * 64})


def test_equivalent_remote_spellings_are_one_destination():
    """Review Focus 1: one URL, spelled two ways, is one destination."""
    assert Destination.remote("HTTPS://Remote.Test/pub") == REMOTE
    assert REMOTE.locator == "https://remote.test/pub"


def test_the_fake_round_trips_and_lists_the_whole_namespace(tmp_path):
    container = _container(tmp_path)
    fake = DirectoryTransport(tmp_path / "remote")
    files = transport_files(container, CORPUS)
    assert fake.push(REMOTE, files) is None
    assert fake.listing(REMOTE, CORPUS) == local_listing(files)
    (fake.remote_dir(REMOTE) / CORPUS / "extra").write_bytes(b"x")
    (fake.remote_dir(REMOTE) / ("2" * 32)).mkdir()
    (fake.remote_dir(REMOTE) / ("2" * 32) / "other").write_bytes(b"y")
    listed = fake.listing(REMOTE, CORPUS)
    assert f"{CORPUS}/extra" in listed and not any(name.startswith("2" * 32) for name in listed)


def test_the_fakes_faults(tmp_path):
    container = _container(tmp_path)
    files = transport_files(container, CORPUS)
    fake = DirectoryTransport(tmp_path / "remote", fail_after_files=1)
    with pytest.raises(TransportFault):
        fake.push(REMOTE, files)
    assert len(fake.listing(REMOTE, CORPUS)) == 1
    fake.fail_after_files = None
    assert fake.push(REMOTE, files) is None
    root, sibling = fake.materialize(REMOTE, CORPUS, tmp_path / "copy")
    assert sibling == b"artifact" and (root / "run" / "a.md").read_bytes() == b"a"
    assert not (tmp_path / "copy" / f"{CORPUS}.metadata").exists()
    fake.abandon = True
    assert type(fake.push(REMOTE, files)) is TransportAbandoned
