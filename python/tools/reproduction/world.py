"""Step 1: register a world root and adopt one fresh corpus on the certified volume."""

from __future__ import annotations

import secrets
import sys

from beliefs.corpus import CorpusWriter
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus
from beliefs.root import open_world as _open_world
from beliefs.world import Fresh, World, WorldConfig
from reproduction import paths, state
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import pins


def config() -> WorldConfig:
    return WorldConfig(paths.WORLD_ROOT, state.load()["world_id"], (paths.CORPUS_ROOT,))


def open_writer() -> CorpusWriter:
    return open_corpus(paths.CORPUS_ROOT, authority=AUTHORITY)


def open_world() -> World:
    return _open_world(config(), authority=AUTHORITY)


def main() -> int:
    if paths.WORLD_ROOT.exists():
        print(f"REFUSED: {paths.WORLD_ROOT} exists; the exercise runs once per work directory")
        return 2
    state.save(world_id=secrets.token_hex(16))
    init_world_root(config(), authority=AUTHORITY)
    init_corpus_root(paths.CORPUS_ROOT, authority=AUTHORITY)
    store_id = init_store_root(paths.STORE_ROOT, authority=AUTHORITY)
    manifest = open_writer().adopt_manifest(profile=pins())
    open_world().admit(paths.CORPUS_ROOT, provenance=Fresh())
    state.save(corpus_id=manifest.corpus_id, store_id=store_id)
    print(f"corpus {manifest.corpus_id} status {open_world().status(manifest.corpus_id)}; store {store_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
