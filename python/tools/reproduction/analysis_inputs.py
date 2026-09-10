"""Step 2a: fix the analysis inputs into target.yaml.

Five keys the analysis needs and the selection cannot supply: `held_file`,
`value_row`, `value_row_symbol`, `group_separator`, `positive_level`. Each
is derived, never typed in: the symbol from the proposition's protein term,
the row from the crosswalk the dataset record names, the levels from the
held file's header, and the ordering and separator from the driver's own
declaration (`analysis-inputs.yaml`), which the header must agree with.
Any disagreement is an `InputsRefused` and the step exits 2.
"""

from __future__ import annotations

import csv
import gzip
import sys
from collections.abc import Iterable
from pathlib import Path

import yaml

from reproduction import paths
from reproduction.select_target import front

DECLARATION = Path(__file__).with_name("analysis-inputs.yaml")
KEYS = ("held_file", "value_row", "value_row_symbol", "group_separator", "positive_level")


class InputsRefused(Exception):
    pass


def measured_and_group(target: dict) -> tuple[str, str]:
    """The protein term is the measured row; the concept term is the grouping."""
    kinds = {term.partition(":")[0]: term for term in (target["subject"], target["object"])}
    if set(kinds) != {"concept", "protein"}:
        raise InputsRefused(
            f"the analysis compares one protein between the levels of one concept; "
            f"{target['subject']} {target['predicate']} {target['object']} is not that shape"
        )
    return kinds["protein"], kinds["concept"]


def positive_level_for(polarity: str, level_order: list[str]) -> str:
    if polarity == "positive":
        return level_order[-1]
    if polarity == "negative":
        return level_order[0]
    raise InputsRefused(f"polarity {polarity!r} predicts no level; a two-group comparison needs a signed proposition")


def levels_in(header: list[str], separator: str) -> list[str]:
    levels: set[str] = set()
    for sample in header[1:]:
        if separator not in sample:
            raise InputsRefused(f"sample {sample!r} carries no group token after {separator!r}")
        levels.add(sample.rsplit(separator, 1)[-1])
    return sorted(levels)


def row_for_symbol(rows: Iterable[dict], symbol: str, *, key: str, symbol_column: str) -> str:
    hits = [row[key] for row in rows if row[symbol_column] == symbol]
    if len(hits) != 1:
        found = f"{len(hits)} rows" if hits else "no row"
        raise InputsRefused(f"the crosswalk carries {found} for symbol {symbol!r}; exactly one is required")
    return hits[0]


def analysis_inputs(target: dict, declaration: dict, dataset_front: dict, header: list[str], crosswalk: Iterable[dict]) -> dict:
    protein, concept = measured_and_group(target)
    symbol = protein.partition(":")[2]
    gene = ((dataset_front.get("identity_context") or {}).get("molecular_ids") or {}).get("gene")
    if not gene or "registry" not in gene:
        raise InputsRefused(f"{dataset_front.get('id')} declares no identity_context.molecular_ids.gene.registry")
    walk = (declaration.get("crosswalks") or {}).get(gene["registry"])
    if walk is None:
        raise InputsRefused(f"registry {gene['registry']} is not declared under crosswalks in {DECLARATION.name}")
    group = (declaration.get("groups") or {}).get(concept)
    if group is None:
        raise InputsRefused(f"{concept} is not declared under groups in {DECLARATION.name}")
    levels = levels_in(header, group["separator"])
    if levels != sorted(group["level_order"]):
        raise InputsRefused(f"the header carries levels {levels}; {concept} declares {group['level_order']}")
    return {
        "held_file": Path(target["dataset_path"]).name,
        "value_row": row_for_symbol(crosswalk, symbol, key=walk["key"], symbol_column=walk["symbol"]),
        "value_row_symbol": symbol,
        "group_separator": group["separator"],
        "positive_level": positive_level_for(target["polarity"], group["level_order"]),
    }


def _open(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", newline="") if path.name.endswith(".gz") else path.open(encoding="utf-8", newline="")


def matrix_header(path: Path) -> list[str]:
    with _open(path) as handle:
        return handle.readline().rstrip("\r\n").split("\t")


def row_hits(path: Path, value_row: str) -> int:
    with _open(path) as handle:
        handle.readline()
        return sum(1 for line in handle if line.split("\t", 1)[0] == value_row)


def dataset_record(root: Path, dataset_id: str) -> dict:
    for path in (root / "entities" / "datasets").glob("*.md"):
        if (f := front(path)).get("id") == dataset_id:
            return f
    raise InputsRefused(f"no dataset record under {root / 'entities' / 'datasets'} carries id {dataset_id}")


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    declaration = yaml.safe_load(DECLARATION.read_text())
    held = Path(target["dataset_path"])
    if not held.is_file():
        print(f"REFUSED: dataset_path {held} is not a regular file; the analysis reads one held file")
        return 2
    try:
        record = dataset_record(paths.PREDECESSOR, target["dataset_id"])
        registry = record["identity_context"]["molecular_ids"]["gene"]["registry"]
        walk = declaration["crosswalks"][registry]
        with _open(paths.PREDECESSOR / walk["path"]) as handle:
            crosswalk = list(csv.DictReader(handle, delimiter="\t"))
        inputs = analysis_inputs(target, declaration, record, matrix_header(held), crosswalk)
        if (hits := row_hits(held, inputs["value_row"])) != 1:
            raise InputsRefused(f"row {inputs['value_row']} ({inputs['value_row_symbol']}) appears {hits} times in {held.name}")
    except (InputsRefused, KeyError) as refused:
        print(f"REFUSED: {type(refused).__name__}: {refused}")
        return 2
    target.update(inputs)
    paths.TARGET.write_text(yaml.safe_dump(target, sort_keys=False))
    print("; ".join(f"{key}={inputs[key]}" for key in KEYS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
