"""Step 13: the cut-31 corpus state under the successor profile, in its own process.

Composite-claims decision 11's transition arm, measured rather than restated
(reproduction record §11.5). The corpus state moved aside at recreation pins
the estimand lane's base contract, which the successor does not ship, so
`audit_corpus`'s profile-disagreement rule answers before any record is
reached. The step passes on exactly that measurement — one finding,
`profile-mismatch: base`, and no record read — and fails on any other.

The archive is required input and is only read. It is named by `--archive`,
or found beside the work directory as `<work dir>.cut31`; when it is absent
the step raises, and nothing stands in for it. The successor profile compiles
from the work directory's held lists, so the step runs after the recreation
has written them, and saves its measurement in that directory's `state.json`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from nodes.core.node import Node

from beliefs.audit import audit_corpus
from beliefs.corpus import ReadView
from beliefs.evidence import DerivationEvidence
from beliefs.world import load_manifest
from reproduction import findings, paths, spec, state
from reproduction.vocabulary import profile

EXPECTED_AUDIT = ["profile-mismatch: base"]


@contextmanager
def counted_reads(view: ReadView) -> Iterator[list[str]]:
    """The ids `view` hands out through its two record routes, `get` and
    `iter_stored`, while the block runs. The facade is sealed, so the count is
    taken on the class for the block's length and answers for this view alone.
    Opening a corpus indexes it; that is not counted, and is not the audit's."""
    read: list[str] = []
    get, iter_stored = ReadView.get, ReadView.iter_stored

    def counted_get(self: ReadView, ref: str) -> Node:
        node = get(self, ref)
        if self is view:
            read.append(node.id)
        return node

    def counted_iter_stored(self: ReadView) -> Iterator[Node]:
        for node in iter_stored(self):
            if self is view:
                read.append(node.id)
            yield node

    with patch.object(ReadView, "get", counted_get), patch.object(ReadView, "iter_stored", counted_iter_stored):
        yield read


def cut31_state(root: Path) -> dict[str, object]:
    """What the archived corpus state at `root` answers, read-only, under the
    successor profile: the route `rederive.prior_state` takes over the cut-22
    state, with the audit's record reads counted."""
    for required in (root / "corpus" / "corpus.yaml", root / "state.json"):
        if not required.is_file():
            raise RuntimeError(
                f"the cut-31 corpus state is not at {root}: {required.name} is missing. It is moved aside, never "
                "deleted, when the corpus is recreated under the successor contracts (composite-claims decision 11); "
                "name it with --archive"
            )
    archived = json.loads((root / "state.json").read_text())
    manifest = load_manifest(root / "corpus")
    view = ReadView.opened_at(root / "corpus")
    evidence = DerivationEvidence(
        specs={},
        held_rules={spec.EQUIVALENCE.identity: spec.EQUIVALENCE},
        implementations={spec.INTERPRETATION.identity: spec.INTERPRETATION},
    )
    with counted_reads(view) as read:
        audit = [f"{f.code}: {f.detail}" for f in audit_corpus(view, evidence=evidence, profile=profile())]
    return {
        "assessment_ref": archived["assessment_ref"],
        "audit": audit,
        "base_pin": f"science_contract: {manifest.profile.science_contract}",
        "corpus_id": manifest.corpus_id,
        "records_read": len(read),
        "spec_ref": archived["spec_ref"],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="reproduction.transition", description=__doc__)
    parser.add_argument("--archive", type=Path, default=paths.CUT31, help="the archived cut-31 work directory")
    measured = cut31_state(parser.parse_args(argv).archive)
    state.save(cut31_corpus_state=measured)
    print(json.dumps(measured, indent=2, sort_keys=True))
    if measured["audit"] == EXPECTED_AUDIT and measured["records_read"] == 0:
        return 0
    findings.record(
        13,
        "defect",
        f"the cut-31 corpus state under the successor profile: expected audit_corpus {EXPECTED_AUDIT} and no record "
        f"read; measured {measured['audit']} with {measured['records_read']} read",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
