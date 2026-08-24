"""Corpus-level guards over `docs/designs/`.

Three drift classes were found by hand on 2026-08-08, and each one is a fact that
lives in many documents while being owned by none of them:

* **`atoms` adoption state.** Plan A through A8 and Plan B items 1–2 are
  implemented; this file names every live document that still gates on a
  completed Plan A stage.
* **The guarantee-row inventory.** Thirteen frozen tables carry the acceptance
  criteria. Their counts are quoted in the README and in the review-disposition
  record, and nothing recomputed them when the belief policy added a table.
* **Cross-references.** Designs cite each other by filename. A rename or a typo is
  invisible to a reader who does not follow the link.

These are guards over *documents*, not over behaviour, and they hold only the
mechanical half. Whether a limitation is still true is review work; whether the
document it defers to exists is not.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
DESIGNS = ROOT / "docs" / "designs"
GUIDE = ROOT / "docs" / "guide"
README = ROOT / "README.md"

#: A digest as §6.2's projection folds it: the algorithm, then lowercase hex.
_ALGORITHM_QUALIFIED = re.compile(r"\A[a-z0-9][a-z0-9_-]*:[0-9a-f]+\Z")

#: The thirteen frozen guarantee tables and the rows each holds. Extending a table
#: means adding its id here; the corpus's own rule is that ids are never renumbered.
GUARANTEE_TABLES: dict[str, tuple[str, ...]] = {
    "G": ("G1", "G2a", "G2b", "G2c", "G3", "G4", "G5", "G6", "G7", "G8", "G9"),
    "S": ("S1", "S1a", "S2", "S3", "S4", "S5", "S6", "S7", "S8"),
    "W": tuple(f"W{n}" for n in range(1, 17)) + ("W5a", "W8a", "W8b"),
    "R": tuple(f"R{n}" for n in range(1, 24)),
    "C": tuple(f"C{n}" for n in range(1, 11)),
    "X": tuple(f"X{n}" for n in range(1, 13)),
    "N": tuple(f"N{n}" for n in range(1, 11)),
    "L": tuple(f"L{n}" for n in range(1, 14)),
    "D": tuple(f"D{n}" for n in range(1, 11)),
    "M": tuple(f"M{n}" for n in range(1, 14)),
    "P": tuple(f"P{n}" for n in range(1, 10)),
    "H": ("H1", "H2", "H3", "H4"),
    "T": ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"),
}

#: Which design owns each table. The formal model reproduces every other table in
#: its coverage map, so ownership cannot be inferred from mentions.
TABLE_OWNERS = {
    "G": "2026-08-02-epistemic-kernel-design.md",
    "S": "2026-08-02-substrate-consolidation-design.md",
    "W": "2026-08-02-world-addressing-design.md",
    "R": "2026-08-02-computation-reproducibility-design.md",
    "C": "2026-08-03-correction-lifecycle-design.md",
    "X": "2026-08-03-world-index-packaging-design.md",
    "N": "2026-08-03-normative-contract-design.md",
    "L": "2026-08-03-tamper-evident-log-design.md",
    "D": "2026-08-04-domain-extension-boundary-design.md",
    "M": "2026-08-04-formal-model-and-claim-calculus-design.md",
    "P": "2026-08-05-belief-policy-design.md",
    "H": "2026-08-10-verified-holdings-record-design.md",
    "T": "2026-08-11-act-report-design.md",
}

#: Science's Linux adoption vocabulary ends at A8. A9 is `atoms`' macOS arm and
#: deliberately stays outside this guard because it is not a Science durability gate.
#: `A6` is also the formal model's refinement-row prefix (`ρA6`), so a bare stage
#: token must not be preceded by `ρ`. `A5b` and `A4a` carry a letter suffix.
_STAGE = r"A[1-8][ab]?"
_ASCII_RANGE = re.compile(rf"(?<![ρ\w])({_STAGE})-({_STAGE})(?![\w])")
_PENDING = r"(?:await(?:s|ing)?|block(?:ed|s|ing)?|gat(?:e|ed|es|ing)|remain(?:s|ing)?|still|until|wait(?:s|ing)?)"
_PENDING_ATOMS_STAGE = re.compile(
    rf"(?:{_PENDING})[^.\n]{{0,160}}(?<![ρ\w]){_STAGE}(?![\w])"
    rf"|(?<![ρ\w]){_STAGE}(?![\w])[^.\n]{{0,160}}(?:{_PENDING})",
    re.IGNORECASE,
)

#: Row ids run to `G2c` and `W8b`, so the suffix is a letter and not just `a`/`b`.
_ROW = re.compile(r"^\|\s*\*{0,2}([GSWRCXNLDMPHT][0-9]+[a-z]?)\*{0,2}\s*\|", re.MULTILINE)
_LINK = re.compile(r"\]\(([^)#\s]+\.md)[^)]*\)")
_BACKTICKED_DOC = re.compile(r"`(20\d\d-\d\d-\d\d-[a-z0-9-]+\.md)`")
#: The same name unquoted. The guide cites designs in links and `sources` lists,
#: never in backticks, so the backticked form finds nothing there.
_DESIGN_FILENAME = re.compile(r"(20\d\d-\d\d-\d\d-[a-z0-9-]+\.md)")

#: Documents this corpus cites that another repository owns. Declared rather than
#: pattern-matched, so a typo in a science filename cannot hide behind "external",
#: and so adding a cross-repo dependency is a visible act.
EXTERNAL_DOCUMENTS = {
    # `nodes`, branch `system-redesign` — cited by ledger artifact 3 and packaging
    # §6 for the reserved-path contract. Not on `nodes` main as of 2026-08-08.
    "2026-08-03-nodes-under-the-system-redesign-design.md",
    "2026-08-17-nodes-write-plan-executor-seam-design.md",
}


#: A label naming a span of one table's rows, as `W1–W13` or `M1–M13`. Both
#: endpoints must be rows that exist: the disposition record once labelled the
#: world group `W1–W16`, and there has never been a `W14`.
_ROW_RANGE = re.compile(r"\b([GSWRCXNLDMPHT])([0-9]+[a-z]?)–\1?([0-9]+[a-z]?)\b")


def design_documents() -> list[Path]:
    docs = sorted(DESIGNS.glob("*.md"))
    assert docs, f"no design documents under {DESIGNS}"
    return docs


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_no_live_document_gates_on_an_atoms_plan_a_stage() -> None:
    """Plan A is complete; live claims do not gate on a completed Plan A stage."""
    stale: list[str] = []
    paths = [README, *design_documents(), *sorted(GUIDE.glob("*.md"))]
    for path in paths:
        for line_no, line in enumerate(_text(path).splitlines(), start=1):
            clauses = re.split(r"[.;|]", line)
            if not line.lstrip().startswith(">") and any(_PENDING_ATOMS_STAGE.search(clause) for clause in clauses):
                stale.append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()}")
    assert not stale, (
        "`atoms` Plan A through A8 is implemented. These live claims still gate on a Plan A stage:\n  "
        + "\n  ".join(stale)
    )


def test_no_design_spells_a_stage_range_with_an_ascii_hyphen() -> None:
    """The guard above reads en-dash ranges, so a hyphenated one would slip past it."""
    found: list[str] = []
    for path in design_documents():
        for line_no, line in enumerate(_text(path).splitlines(), start=1):
            for start, end in _ASCII_RANGE.findall(line):
                found.append(f"{path.name}:{line_no}: {start}-{end}")
    assert not found, "stage ranges use an en-dash:\n  " + "\n  ".join(found)


def test_the_ledger_records_the_completed_atoms_adoption_gate() -> None:
    """The ledger records completed Plan A and Plan B adoption."""
    ledger = _text(DESIGNS / "2026-08-03-redesign-adoption-ledger.md")
    atoms_rows = [line for line in ledger.splitlines() if "**`atoms` " in line and "—" in line]
    assert atoms_rows, "the ledger no longer carries an `atoms` artifact row"
    state = atoms_rows[0].split("|")[-2]
    assert "A8 landed 2026-08-17" in state
    assert "Plan B item 2 landed 2026-08-19" in state
    assert "composition-root-adoption half is complete" in state


def test_every_design_declares_a_status() -> None:
    missing = [p.name for p in design_documents() if "**Status" not in _text(p)[:1200]]
    assert not missing, "no status declared in: " + ", ".join(missing)


def test_every_guarantee_table_is_complete_in_the_document_that_owns_it() -> None:
    """A table's owner must carry every row the inventory claims, and no others.

    The inventory is quoted as a count in the README and in the disposition record;
    without this, a table can grow a row that no count ever hears about.
    """
    for prefix, expected in GUARANTEE_TABLES.items():
        owner = DESIGNS / TABLE_OWNERS[prefix]
        found = {row for row in _ROW.findall(_text(owner)) if row.startswith(prefix)}
        # The owner may cite a neighbouring table's row; only its own prefix is checked.
        found = {row for row in found if re.fullmatch(rf"{prefix}[0-9]+[a-z]?", row)}
        assert found == set(expected), (
            f"{owner.name}'s {prefix} table disagrees with the inventory: "
            f"missing {sorted(set(expected) - found)}, unexpected {sorted(found - set(expected))}"
        )


def test_the_readme_states_the_corpus_row_total() -> None:
    """126 was the total on 2026-08-05 and is now the frozen denominator of cut 1.

    The corpus total moved when the belief policy added P1–P9, and the README is
    where a reader learns it. Both numbers must appear, doing their own jobs.
    """
    total = sum(len(rows) for rows in GUARANTEE_TABLES.values())
    tables = len(GUARANTEE_TABLES)
    # The README hard-wraps its prose, so a phrase can straddle a line break.
    readme = re.sub(r"\s+", " ", _text(README))
    assert f"{total} rows" in readme, f"the README does not state the corpus total of {total} rows"
    table_words = {11: "eleven", 12: "twelve", 13: "thirteen"}
    assert f"{table_words[tables]} frozen tables" in readme, (
        f"the README does not state that the rows sit in {tables} tables"
    )


def test_the_readme_lists_every_design_document() -> None:
    readme = _text(README)
    listed = set(_BACKTICKED_DOC.findall(readme))
    present = {p.name for p in design_documents()}
    assert listed == present, (
        f"README design table out of step: missing {sorted(present - listed)}, stale {sorted(listed - present)}"
    )


#: How the README spells its design count. Written out, as the prose does.
_COUNT_WORDS = {
    16: "Sixteen",
    17: "Seventeen",
    18: "Eighteen",
    19: "Nineteen",
    20: "Twenty",
    21: "Twenty-one",
    22: "Twenty-two",
    23: "Twenty-three",
    24: "Twenty-four",
    25: "Twenty-five",
    26: "Twenty-six",
    27: "Twenty-seven",
    28: "Twenty-eight",
    29: "Twenty-nine",
    30: "Thirty",
    31: "Thirty-one",
    32: "Thirty-two",
    33: "Thirty-three",
    34: "Thirty-four",
}


def test_the_readme_states_how_many_designs_there_are() -> None:
    """The sentence above the table counts the table, and drifts silently.

    It read "Sixteen documents ... through 2026-08-08" while the table listed
    eighteen through 2026-08-09 — the test above passes on a complete table with a
    wrong count, because it never reads the sentence. The newest document's date
    is checked too: the range's far end rots the same way and for the same reason.
    """
    present = design_documents()
    count = len(present)
    word = _COUNT_WORDS.get(count)
    assert word is not None, f"extend _COUNT_WORDS: {count} designs and no spelling for it"
    readme = re.sub(r"\s+", " ", _text(README))
    assert f"{word} documents" in readme, (
        f"the README says something other than '{word} documents' for its {count} designs"
    )
    newest = max(p.name[:10] for p in present)
    assert f"through {newest}" in readme, f"the README's date range does not end at the newest design, {newest}"


def test_every_guarantee_range_names_rows_that_exist() -> None:
    """A range label is read as a count, so an endpoint that is not a row misleads.

    Checked across the designs *and* the guide, because the guide's whole job is
    to quote these labels at a reader who will not open the table.
    """
    bad: list[str] = []
    for path in design_documents() + sorted(GUIDE.glob("*.md")):
        for line_no, line in enumerate(_text(path).splitlines(), start=1):
            for prefix, start, end in _ROW_RANGE.findall(line):
                rows = GUARANTEE_TABLES[prefix]
                label = f"{prefix}{start}–{prefix}{end}"
                for endpoint in (f"{prefix}{start}", f"{prefix}{end}"):
                    if endpoint not in rows:
                        bad.append(f"{path.name}:{line_no}: {label} — no {endpoint}")
    assert not bad, "guarantee ranges naming rows that do not exist:\n  " + "\n  ".join(bad)


def test_the_guide_cites_every_design() -> None:
    """The contributor guide's §6 rule: no design goes unmentioned.

    Banking a design is the moment this can rot, and the rot is silent — the new
    document is simply absent from the one place a newcomer looks.
    """
    cited: set[str] = set()
    for page in sorted(GUIDE.glob("*.md")):
        cited |= set(_DESIGN_FILENAME.findall(_text(page)))
    missing = sorted({p.name for p in design_documents()} - cited)
    assert not missing, "no guide page cites: " + ", ".join(missing)


def test_every_cross_reference_resolves() -> None:
    """A design citing a document by filename must cite one that exists.

    A name owned by another repository resolves against `EXTERNAL_DOCUMENTS`, which
    is a list and not a pattern: a mistyped science filename cannot pass as foreign.
    """
    present = {p.name for p in design_documents()}
    broken: list[str] = []
    for path in design_documents():
        text = _text(path)
        for name in set(_BACKTICKED_DOC.findall(text)):
            if name not in present and name not in EXTERNAL_DOCUMENTS:
                broken.append(f"{path.name} → `{name}`")
        for target in set(_LINK.findall(text)):
            if not (path.parent / target).resolve().exists():
                broken.append(f"{path.name} → {target}")
    assert not broken, "unresolvable references:\n  " + "\n  ".join(sorted(broken))


def test_the_frozen_survey_artifact_keeps_every_digest_algorithm_qualified() -> None:
    """The admission ramp's frozen measurement must yield §6.2's dataset basis
    projection on its own.

    That projection folds `<algorithm>:<hex>` strings. The first freeze stored bare
    hex, so the address could only be derived by trusting a sentence in the design
    or by re-reading source roots the freeze exists to replace — and a 64-character
    digest is producible by more than one algorithm. This guard is over the frozen
    file rather than the instrument: a future re-freeze by a changed instrument is
    exactly the way the fact would be lost again.
    """
    artifact = json.loads(_text(DESIGNS / "2026-08-09-admission-ramp-survey.json"))
    bare = [
        f"{r['dataset']}/{r['path']}: {field}={r[field]}"
        for r in artifact["resources"]
        for field in ("recorded_hash", "observed_hash")
        if r[field] is not None and not _ALGORITHM_QUALIFIED.match(r[field])
    ]
    assert not bare, "digests recorded without their algorithm:\n  " + "\n  ".join(bare)
