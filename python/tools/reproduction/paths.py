"""The work directory, the predecessor root and the fixed sub-paths.

Throwaway by declaration (mm30 reproduction design §8 item 3): the exercise's
instrument, not a surface.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# "Beside the checkout" means beside the main checkout: a lane worktree under
# `.worktrees/` is removed when the lane closes, and the corpus must outlive it.
CHECKOUT = REPO.parents[1] if REPO.parent.name == ".worktrees" else REPO
WORK = Path(os.environ.get("SCIENCE_MM30_ROOT", CHECKOUT / ".mm30-reproduction"))
PREDECESSOR = Path(
    os.environ.get("MM30_PREDECESSOR", Path.home() / "d" / "cancer" / "cancer-types" / "multiple-myeloma")
)
WORLD_ROOT, CORPUS_ROOT, STORE_ROOT, SCRATCH = WORK / "world", WORK / "corpus", WORK / "store", WORK / "scratch"
STATE, FINDINGS, TARGET = WORK / "state.json", WORK / "findings.jsonl", WORK / "target.yaml"
