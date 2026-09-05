"""Step 0. Refuses loudly; never skips. Exit 2 on refusal."""

from __future__ import annotations

import shutil
import sys

from beliefs.confinement import host_prerequisites
from beliefs.root import init_corpus_root, init_store_root, init_world_root, metadata_root_for
from beliefs.world import WorldConfig
from reproduction import paths
from reproduction.authority import AUTHORITY


def main() -> int:
    paths.WORK.mkdir(parents=True, exist_ok=True)
    probe = paths.WORK / "probe"
    world, corpus, store = probe / "world", probe / "corpus", probe / "store"
    try:
        init_world_root(WorldConfig(world, "0" * 32, ()), authority=AUTHORITY)
        init_corpus_root(corpus, authority=AUTHORITY)
        init_store_root(store, authority=AUTHORITY)
    except Exception as refused:  # noqa: BLE001 — report the engine's own words
        print(f"REFUSED: the volume under {paths.WORK} is not certified: {type(refused).__name__}: {refused}")
        return 2
    finally:
        for root in (world, corpus, store):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)
        shutil.rmtree(probe, ignore_errors=True)
    if (reason := host_prerequisites()) is not None:
        print(f"REFUSED: confinement unavailable on this host: {reason}")
        return 2
    if not (paths.PREDECESSOR / "science.yaml").exists():
        print(f"REFUSED: predecessor corpus not found at {paths.PREDECESSOR}")
        return 2
    print(f"ok: certified volume at {paths.WORK}; confinement available; predecessor at {paths.PREDECESSOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
