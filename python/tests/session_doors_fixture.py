"""Real roots for the session's sharing and publish doors (sharing design §6).

`published_source` mirrors cut 40's `source` fixture inside a caller-owned
directory on the certified volume: a source world over one BASE corpus of topic
records and a written root under coordination v2 that holds the view, so an
attended session can open with the written root as its write root and every
configured root mounted. `publish_locally` runs the local publish act as the
cut-40 `run` does, and the remaining helpers turn its export into what a
recipient holds: a metadata-less copy, the head-artifact sibling's bytes, the
evidence a sharing door binds, and a recipient session over its own world.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

from authority import ACTOR, FULL
from coordination_fixtures import content_for, coordination_profile
from profiles import BASE, pins_for
from test_world_receipts import hold_shipped
from test_world_selection import topic_nodes

from beliefs import stored
from beliefs.coordination import coordination_revision
from beliefs.corpus import CoordinationResolver, ReadView
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publication import MARKER_KIND
from beliefs.publish import Published, publish
from beliefs.root import init_corpus_root, init_world_root, moment_seam, open_corpus, open_world
from beliefs.session import ScopedWriter, SharingEvidence, WriterSession, open_attended_session
from beliefs.world import Fresh, WorldConfig, epoch

__all__ = [
    "KINDS",
    "SOURCE",
    "SOURCE_WORLD",
    "V2",
    "evidence_for",
    "metadata_less_copy",
    "publish_locally",
    "published_source",
    "recipient_session",
    "successor_session",
]

V2 = coordination_profile(None, version=2)
KINDS = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset", "run"]}]}]}
SOURCE_WORLD = "e" * 32
RECIPIENT_WORLD = "f" * 32
SOURCE = "provider:https://remote.test/a"
LOCATION = "https://remote.test/a"
DIGEST = "d" * 64
PUBLISHES = scoped_authority(RequiredCapabilities.publishes(), ACTOR)
"""Exactly the publication permit, as cut 40's publishing writer binds it."""


class Clock:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-23T00:00:{self.n:02d}Z"


def _corpus(path: Path, profile, nodes=()) -> str:
    init_corpus_root(path, authority=FULL)
    writer = open_corpus(path, authority=FULL, profile=profile)
    manifest = writer.adopt_manifest(profile=pins_for(profile))
    for node in nodes:
        writer.add(node.model_copy(deep=True))
    return manifest.corpus_id


def published_source(work: Path) -> SimpleNamespace:
    """The cut-40 source shape inside `work`: `alpha` (BASE, every topic record), `written`
    (coordination v2, holding a project whose query selects datasets and runs), a
    world over both with an epoch built, an operations root and a local destination."""
    base = Path(work).resolve()
    alpha, written = base / "alpha", base / "written"
    # Both halves of the topic records in one corpus: alpha's runs and datasets
    # name beta's, and the publication's closure must hold inside the world.
    alpha_nodes, beta_nodes = topic_nodes()
    a = _corpus(alpha, BASE, tuple(node for node in (*alpha_nodes, *beta_nodes) if node.kind != "project"))
    w = _corpus(written, V2)
    config = WorldConfig(base / "world", SOURCE_WORLD, (alpha, written))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(alpha, provenance=Fresh())
    world.admit(written, provenance=Fresh())
    epoch.build_epoch(world, coverage=frozenset({a}), bindings=hold_shipped(world))
    mounts = {config.corpus_roots[0]: BASE, config.corpus_roots[1]: V2}
    resolver = CoordinationResolver(mounts)
    project = open_corpus(written, authority=FULL, profile=V2, coordination_resolver=resolver).mint_coordination(
        "project", content=content_for("project", query=KINDS)
    )
    ops, dest = base / "ops", base / "dest"
    ops.mkdir()
    dest.mkdir()
    return SimpleNamespace(
        base=base,
        config=config,
        alpha=config.corpus_roots[0],
        written=config.corpus_roots[1],
        alpha_id=a,
        written_id=w,
        profile=V2,
        mounts=mounts,
        resolver=resolver,
        view=coordination_revision(project).address,
        ops=ops,
        dest=dest,
        destination=Destination.local(str(dest)),
    )


def publish_locally(s: SimpleNamespace, *, destination: Destination | None = None) -> Published:
    """The local publish act under exactly the publication permit, as cut 40's `run`."""
    writer = open_corpus(s.written, authority=PUBLISHES, profile=V2, coordination_resolver=s.resolver)
    outcome = publish(
        writer,
        s.resolver,
        open_world(s.config, authority=PUBLISHES),
        view=s.view,
        destination=s.destination if destination is None else destination,
        operations_root=s.ops,
        staging_profile=V2,
        clock=Clock(),
        seam=moment_seam(),
    )
    assert type(outcome) is Published, outcome
    return outcome


def _export_dir(s: SimpleNamespace, destination: Destination | None) -> Path:
    return s.dest if destination is None else Path(destination.locator)


def metadata_less_copy(
    s: SimpleNamespace, published: Published, into: Path, *, destination: Destination | None = None
) -> tuple[Path, bytes]:
    """The export copied without its metadata sibling, and the head-artifact sibling's bytes."""
    export = _export_dir(s, destination)
    shutil.copytree(export / published.corpus_id, into, symlinks=True)
    return Path(into).resolve(), (export / f"{published.corpus_id}.head-artifact.v1").read_bytes()


def evidence_for(published: Published, sibling: bytes, s: SimpleNamespace) -> SharingEvidence:
    """The seven pin facts a recipient knows before any act, read from the export's marker."""
    export = s.dest / published.corpus_id
    (marker,) = (node for node in ReadView.opened_at(export).iter_stored() if node.kind == MARKER_KIND)
    source = marker.facets[stored.COORDINATION_FACET]["published_from"]
    assert source["world_id"] == SOURCE_WORLD
    return SharingEvidence(
        corpus=published.corpus_id,
        marker=marker.uid,
        artifact=hashlib.sha256(sibling).hexdigest(),
        world=source["world_id"],
        view=source["view"],
        source=SOURCE,
        location=LOCATION,
    )


def recipient_session(work: Path, *, required: RequiredCapabilities) -> tuple[WriterSession, ScopedWriter]:
    """An attended session over a recipient world of one fresh BASE corpus,
    invocation `A` claimed and scoped to `required`."""
    base = Path(work).resolve()
    root = base / "recipient"
    _corpus(root, BASE)
    config = WorldConfig(base / "rworld", RECIPIENT_WORLD, (root,))
    init_world_root(config, authority=FULL)
    open_world(config, authority=FULL).admit(root, provenance=Fresh())
    session = open_attended_session(config, base / "rops", write_root=root, profile=BASE, mounts={root: BASE})
    session.claim_invocation("A", "share", DIGEST)
    return session, session.scoped(required, "A")


def successor_session(session: WriterSession, *, required: RequiredCapabilities) -> tuple[WriterSession, ScopedWriter]:
    """A second attended session over `session`'s recipient world, write root
    and operations root, with its own session actor, invocation `A` claimed and
    scoped to `required`: the next session that reconciles after `session`."""
    config = session.world_config
    assert config is not None
    root = session.corpus_root
    successor = open_attended_session(
        config, session.operations_root, write_root=root, profile=BASE, mounts={root: BASE}
    )
    successor.claim_invocation("A", "share", DIGEST)
    return successor, successor.scoped(required, "A")
