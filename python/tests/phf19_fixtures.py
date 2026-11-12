"""Synthetic PHF19 construction helpers; never real-release evidence."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
from reproduction import paths, world

FIXTURE = REPO_ROOT / "fixtures/phf19"


def initialize(monkeypatch, root):
    for name, relative in {
        "WORK": "",
        "WORLD_ROOT": "world",
        "CORPUS_ROOT": "corpus",
        "STORE_ROOT": "store",
        "SCRATCH": "scratch",
        "STATE": "state.json",
        "TARGET": "target.yaml",
        "FINDINGS": "findings.jsonl",
    }.items():
        monkeypatch.setattr(paths, name, root / relative)
    assert world.main() == 0
    world.adopt()
    return world.open_writer()


def selected():
    from reproduction.analysis_inputs import resolve_phf19

    return resolve_phf19(
        json.loads((FIXTURE / "declaration.json").read_text()),
        predecessor=FIXTURE / "predecessor",
        hgnc=FIXTURE / "hgnc.tsv",
        ensembl=FIXTURE / "ensembl.gtf.gz",
    )
