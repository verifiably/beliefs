"""Conformance cut 43 — the multi-corpus session (session-mounts design §8.2):
J12, J14 and J15-a over real roots on the certified volume. Corpus A (the
write root) pins base, the fixture `biology` and coordination v2; B pins base,
the shipped `biology` and coordination v2; C pins the fixture `biology` alone,
the mm30 shape; D shares A's profile as a read mount. Every mount is compiled
from its own manifest, and each case's directory is removed at teardown."""

from __future__ import annotations

import json
import secrets
import shutil
from collections.abc import Mapping
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace
from typing import Literal

import pytest
from authority import FULL
from coordination_fixtures import content_for, pins_for
from nodes.core.node import Node
from nodes.core.paths import path_for_node_id
from profiles import WITH_BIOLOGY, biology
from test_durable_families import proposition
from test_session_acceptance import PROPOSITIONS, fresh

from beliefs.coordination import CoordinationRefused, coordination_revision
from beliefs.corpus import CoordinationResolver
from beliefs.errors import ContractMismatch, CoordinationUnavailable, SessionRefused
from beliefs.mount import compile_mount_profile
from beliefs.permit import RequiredCapabilities
from beliefs.profile import (
    ProfileSpec,
    compile_profile,
    shipped_base_contract,
    shipped_coordination,
    shipped_domain_contract,
)
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.session import open_attended_session, open_ledger_reader, reconcile_sessions
from beliefs.session.ledger import ledger_path
from beliefs.world import WorldConfig

V2_LOCAL = compile_profile(shipped_base_contract(), [biology("fixture")], coordination=shipped_coordination(2))
V2_SHIPPED = compile_profile(shipped_base_contract(), [shipped_domain_contract("biology")], coordination=shipped_coordination(2))
AVAILABLE = (biology("fixture"),)


def _adopt(base: Path, name: str, profile) -> Path:
    root = base / name
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins_for(profile))
    return root.resolve()


@pytest.fixture()
def corpora(work_directory):
    """Every case owns one directory under the certified work directory: its
    roots, their `.metadata` siblings, its worlds, links and operations roots.
    Teardown removes it whole (plan review, round 2)."""
    base = Path(mkdtemp(prefix="cut43-", dir=work_directory)).resolve()
    try:
        yield SimpleNamespace(
            base=base,
            a=_adopt(base, "a", V2_LOCAL),
            b=_adopt(base, "b", V2_SHIPPED),
            c=_adopt(base, "c", WITH_BIOLOGY),
            d=_adopt(base, "d", V2_LOCAL),  # a read mount with A's profile: J15-a's sabotage target
        )
    finally:
        shutil.rmtree(base, ignore_errors=True)


def mounts_for(roots):
    return {root: compile_mount_profile(root, available=AVAILABLE) for root in roots}


def open_over(
    s, roots, write_root, *,
    mounts: Mapping[Path, ProfileSpec] | Literal["compiled"] | None = "compiled",
    profile: ProfileSpec | None = None, **kwargs,
):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    ops = s.base / f"ops-{secrets.token_hex(4)}"
    compiled = mounts_for(roots) if isinstance(mounts, str) else mounts
    writer_profile = profile or (compiled[write_root] if compiled else compile_mount_profile(write_root, available=AVAILABLE))
    session = open_attended_session(config, ops, write_root=write_root, profile=writer_profile, mounts=compiled, **kwargs)
    return session, config, ops


def refused_without_directory(s, roots, write_root, error: type[Exception] = SessionRefused, **kwargs):
    config = WorldConfig(s.base / f"world-{secrets.token_hex(4)}", secrets.token_hex(16), tuple(roots))
    ops = s.base / f"ops-{secrets.token_hex(4)}"
    with pytest.raises(error):
        open_attended_session(config, ops, write_root=write_root, **kwargs)
    assert not (ops / "sessions").exists()


def library_on(root: Path, profile):
    return open_corpus(root, authority=FULL, profile=profile, coordination_resolver=CoordinationResolver({root: profile}))


def state(root: Path):
    """A root's bytes and its metadata sibling's: the chain lives under the root."""
    def tree(path: Path):
        return sorted((str(p.relative_to(path)), p.read_bytes() if p.is_file() else None) for p in path.rglob("*")) if path.exists() else []
    return tree(root), tree(metadata_root_for(root))


# --- J12 ------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["outside", "zero-roots"])
def test_j12_a_a_write_root_outside_the_configured_roots_refuses_durably(corpora, case):
    """J12-a: the membership check, which also refuses a configuration naming no root."""
    s = corpora
    if case == "outside":
        refused_without_directory(s, (s.a, s.b), s.c, profile=WITH_BIOLOGY)
    else:
        refused_without_directory(s, (), s.a, profile=V2_LOCAL)


@pytest.mark.parametrize("case", ["missing", "extra", "repeated", "unadopted", "profile"])
def test_j12_b_a_mount_set_other_than_the_configured_roots_refuses_durably(corpora, case):
    """J12-b: the mount set is exactly the configured roots, each once; a read mount's
    manifest loads; the writer's profile is its own mount's."""
    s = corpora
    compiled = mounts_for((s.a, s.b))
    if case == "missing":
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={s.a: compiled[s.a]})
    elif case == "extra":
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={**compiled, **mounts_for((s.c,))})
    elif case == "repeated":
        link = s.base / f"link-{secrets.token_hex(4)}"
        link.symlink_to(s.a)
        refused_without_directory(s, (s.a, s.b), s.a, profile=V2_LOCAL, mounts={**compiled, link: compiled[s.a]})
    elif case == "unadopted":
        bare = s.base / f"bare-{secrets.token_hex(4)}"
        init_corpus_root(bare, authority=FULL)
        refused_without_directory(s, (s.a, bare), s.a, profile=V2_LOCAL, mounts={s.a: compiled[s.a], bare: V2_SHIPPED})
    else:
        refused_without_directory(s, (s.a, s.b), s.a, ContractMismatch, profile=V2_SHIPPED, mounts=compiled)


@pytest.mark.parametrize("case", ["a", "b", "one-root"])
def test_j12_c_the_session_writes_the_named_root_and_only_it_durably(corpora, case):
    """J12-c: each configured root as the write root in turn; the negative, a
    one-root world, opens as J9's sessions do."""
    s = corpora
    if case == "one-root":
        session, config, ops = open_over(s, (s.a,), s.a)
        reader = open_ledger_reader(ops, session.session_id)
        assert reader.world_id == config.world_id and reader.actor == session.actor
        opened = json.loads(ledger_path(ops, session.session_id).read_bytes().splitlines()[0])
        ceiling = FULL.permit.summary()
        assert opened["permit"] == {
            "kinds": list(ceiling.kinds),
            "act_families": list(ceiling.act_families),
            "ungoverned": ceiling.ungoverned,
        }
        session.close()
        return
    write, other = (s.a, s.b) if case == "a" else (s.b, s.a)
    session, _, _ = open_over(s, (s.a, s.b), write)
    assert session.corpus_root == write
    before = state(other)
    w = fresh(session, "A", RequiredCapabilities.coordination())
    project = w.mint_coordination("project", content=content_for("project", name=f"in-{case}"))
    assert (write / path_for_node_id(project.id)).is_file()
    assert state(other) == before
    session.close()


# --- J14 ------------------------------------------------------------------------


def test_j14_a_coordination_resolves_over_every_mount_durably(corpora):
    """J14-a: a project minted in B is the initial selection of a session writing
    A; its revision lands in A and resolves; a second tip in B makes it divergent;
    without mounts, coordination is unavailable."""
    s = corpora
    library = library_on(s.b, V2_SHIPPED)
    project = library.mint_coordination("project", content=content_for("project", name="in-b"))
    address = coordination_revision(project).address.unpinned()
    session, _, ops = open_over(s, (s.a, s.b), s.a, project=address)
    assert open_ledger_reader(ops, session.session_id).initial_project == address.pinned(project.uid)
    w = fresh(session, "A", RequiredCapabilities.coordination())
    revised = w.revise_coordination("project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-a"))
    assert (s.a / path_for_node_id(revised.id)).is_file() and not (s.b / path_for_node_id(revised.id)).exists()
    resolver = session._coordination_resolver
    assert resolver is not None
    resolved = resolver.resolve(address)
    assert isinstance(resolved, Node) and resolved.uid == revised.uid
    assert set(resolver.standing("project")) == {address}
    sibling = library_on(s.b, V2_SHIPPED).revise_coordination(
        "project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-b")
    )
    divergent = resolver.resolve(address)
    assert type(divergent) is CoordinationRefused and divergent.reason == "divergent-view"
    assert set(divergent.tips) == {revised.uid, sibling.uid}
    session.close()
    bare, _, _ = open_over(s, (s.a, s.b), s.a, mounts=None, profile=V2_LOCAL)
    with pytest.raises(CoordinationUnavailable):
        fresh(bare, "B", RequiredCapabilities.coordination()).revise_coordination(
            "project", address, predecessors=[project.uid], content=content_for("project", name="without-mounts")
        )
    bare.close()


# --- J15 ------------------------------------------------------------------------


def test_j15_a_a_session_never_writes_a_read_mount_durably(corpora):
    """J15-a: an ordinary write, a coordination mint and a revision of a read-mount
    predecessor leave every read mount byte-identical, and reconciliation finds nothing."""
    s = corpora
    project = library_on(s.b, V2_SHIPPED).mint_coordination("project", content=content_for("project", name="in-b"))
    address = coordination_revision(project).address.unpinned()
    before = {root: state(root) for root in (s.b, s.c, s.d)}
    session, config, ops = open_over(s, (s.a, s.b, s.c, s.d), s.a)
    w = fresh(session, "A", PROPOSITIONS)
    w.add(proposition("q1"))
    session.close_invocation("A", {"done": []})
    c = fresh(session, "B", RequiredCapabilities.coordination())
    c.mint_coordination("project", content=content_for("project", name="in-a"))
    c.revise_coordination("project", address, predecessors=[project.uid], content=content_for("project", name="revised-in-a"))
    session.close_invocation("B", {"done": []})
    session.close()
    findings = reconcile_sessions(config, ops)
    assert {root: state(root) for root in (s.b, s.c, s.d)} == before
    assert findings == ()


def test_the_mm30_shape_mounts_beside_a_working_corpus_durably(corpora):
    """Decision 3: a corpus pinning no coordination contract is mounted, and contributes nothing to resolution."""
    s = corpora
    session, _, _ = open_over(s, (s.a, s.c), s.a)
    resolver = session._coordination_resolver
    assert resolver is not None and set(resolver.mounted()) == {s.a, s.c}
    assert dict(resolver.standing("project")) == {}
    session.close()
