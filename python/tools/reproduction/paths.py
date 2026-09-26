"""The work directory, the predecessor root and the fixed sub-paths.

Throwaway by declaration (mm30 reproduction design §8 item 3): the exercise's
instrument, not a surface.
"""

from __future__ import annotations

import os
from pathlib import Path

from checkout import MAIN_CHECKOUT

REPO = Path(__file__).resolve().parents[3]
# "Beside the checkout" means beside the main checkout: a lane worktree under
# `.worktrees/` is removed when the lane closes, and the corpus must outlive it.
WORK = Path(os.environ.get("SCIENCE_MM30_ROOT", MAIN_CHECKOUT / ".work" / "reproduction" / "mm30"))
PREDECESSOR = Path(
    os.environ.get("MM30_PREDECESSOR", Path.home() / "d" / "cancer" / "cancer-types" / "multiple-myeloma")
)
# The prior corpus state, moved aside when the corpus was recreated under the
# successor contracts (estimand-typing decision 10). Read-only: Q10's
# transition arm presents it to the successor readers.
PRIOR = WORK.with_name(WORK.name + ".cut22")
WORLD_ROOT, CORPUS_ROOT, STORE_ROOT, SCRATCH = WORK / "world", WORK / "corpus", WORK / "store", WORK / "scratch"
STATE, FINDINGS, TARGET = WORK / "state.json", WORK / "findings.jsonl", WORK / "target.yaml"
