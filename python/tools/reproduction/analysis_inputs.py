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


def analysis_inputs(
    target: dict, declaration: dict, dataset_front: dict, header: list[str], crosswalk: Iterable[dict]
) -> dict:
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
    return (
        gzip.open(path, "rt", encoding="utf-8", newline="")
        if path.name.endswith(".gz")
        else path.open(encoding="utf-8", newline="")
    )


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
            raise InputsRefused(
                f"row {inputs['value_row']} ({inputs['value_row_symbol']}) appears {hits} times in {held.name}"
            )
    except (InputsRefused, KeyError) as refused:
        print(f"REFUSED: {type(refused).__name__}: {refused}")
        return 2
    target.update(inputs)
    paths.TARGET.write_text(yaml.safe_dump(target, sort_keys=False))
    print("; ".join(f"{key}={inputs[key]}" for key in KEYS))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# The explicit route preserves the heritage selectors above for read-only callers.
import re
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from types import MappingProxyType

from beliefs.referent_mapping import ReferentMapping
from reproduction.analysis.labels import stage_token


@dataclass(frozen=True)
class PHF19Inputs:
    source_proposition: str
    source_dataset: str
    feature: str
    gene: str
    factor: str
    baseline: str
    comparison: str
    separator: str
    digests: Mapping[str, str]
    mapping: ReferentMapping
    mapping_members: bytes


def hgnc_members(content: bytes) -> bytes:
    """Derive the entire ID set, including entries unrelated to the selected row."""
    try:
        rows = csv.DictReader(StringIO(content.decode("utf-8")), delimiter="\t")
        if rows.fieldnames is None or "hgnc_id" not in rows.fieldnames:
            raise InputsRefused("HGNC input has no hgnc_id column")
        members = set()
        for row in rows:
            raw = row["hgnc_id"]
            if not isinstance(raw, str) or re.fullmatch(r"HGNC:[1-9][0-9]*", raw) is None:
                raise InputsRefused("malformed HGNC member identifier")
            term = "hgnc:" + raw.partition(":")[2]
            if term in members:
                raise InputsRefused("duplicate HGNC member identifier")
            members.add(term)
        if not members:
            raise InputsRefused("empty HGNC release")
        return "".join(x + "\n" for x in sorted(members)).encode()
    except (UnicodeError, csv.Error) as error:
        raise InputsRefused("unreadable HGNC TSV") from error


def declared_paths(declaration: Mapping[str, object], predecessor: Path) -> dict[str, Path]:
    raw = declaration.get("paths")
    if not isinstance(raw, dict) or set(raw) != {"proposition", "dataset", "matrix", "crosswalk"}:
        raise InputsRefused("explicit proposition, dataset, matrix and crosswalk paths required")
    result = {}
    for name, value in raw.items():
        if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
            raise InputsRefused("source paths must be predecessor-relative")
        path = predecessor / value
        if not path.resolve().is_relative_to(predecessor.resolve()) or not path.is_file():
            raise InputsRefused(f"missing or escaping source file: {name}")
        result[name] = path
    return result


def resolve_phf19(declaration: Mapping[str, object], *, predecessor: Path, hgnc: Path, ensembl: Path) -> PHF19Inputs:
    """Check pinned sources and the selected correspondence, without ranking or analysis."""
    expected = {
        "source_proposition": "proposition:concept-disease-stage-affects-protein-phf19",
        "source_dataset": "dataset:gse179929",
        "feature": "ENSG00000119403",
        "gene": "hgnc:24566",
        "factor": "concept:disease-stage",
        "baseline": "level:ndmm",
        "comparison": "level:pd",
        "separator": "_",
        "hgnc_release": "2025-09-05",
        "ensembl_release": "115",
        "assembly": "GRCh38.p14",
    }
    if any(declaration.get(k) != v for k, v in expected.items()):
        raise InputsRefused("declaration changes the frozen PHF19 question or reference release")
    if set(declaration) != set(expected) | {"paths", "digests", "evidence"}:
        raise InputsRefused("missing or unknown PHF19 declaration fields")
    if declaration["evidence"] not in ("held-release", "synthetic"):
        raise InputsRefused("reference evidence must be labelled held-release or synthetic")
    digests = declaration["digests"]
    if not isinstance(digests, dict) or set(digests) != {
        "proposition",
        "dataset",
        "matrix",
        "crosswalk",
        "hgnc",
        "ensembl",
    }:
        raise InputsRefused("all six source digest pins required")
    if any(not isinstance(x, str) or re.fullmatch("[0-9a-f]{64}", x) is None for x in digests.values()):
        raise InputsRefused("source digest is not lowercase SHA256")
    if declaration["evidence"] == "held-release":
        import json

        approved = json.loads(Path(__file__).with_name("phf19-inputs.json").read_text())
        if digests != approved["digests"]:
            raise InputsRefused("held-release pins differ from the approved acquisition and predecessor")
    locations = {**declared_paths(declaration, predecessor), "hgnc": hgnc, "ensembl": ensembl}
    try:
        for key, path in locations.items():
            if sha256(path.read_bytes()).hexdigest() != digests[key]:
                raise InputsRefused(f"{key} digest differs from declared source")
        if front(locations["proposition"]).get("id") != expected["source_proposition"]:
            raise InputsRefused("source proposition id mismatch")
        if front(locations["dataset"]).get("id") != expected["source_dataset"]:
            raise InputsRefused("source dataset id mismatch")
        hgnc_content = hgnc.read_bytes()
        members = hgnc_members(hgnc_content)
        if b"hgnc:24566\n" not in members.splitlines(keepends=True):
            raise InputsRefused("selected HGNC entry is absent")
        rows = list(csv.DictReader(StringIO(hgnc_content.decode()), delimiter="\t"))
        hits = [
            r
            for r in rows
            if r.get("hgnc_id") == "HGNC:24566" or "ENSG00000119403" in r.get("ensembl_gene_id", "").split("|")
        ]
        if len(hits) != 1 or any(
            hits[0].get(k) != v
            for k, v in {
                "hgnc_id": "HGNC:24566",
                "symbol": "PHF19",
                "status": "Approved",
                "ensembl_gene_id": "ENSG00000119403",
            }.items()
        ):
            raise InputsRefused("HGNC correspondence is absent, unapproved or ambiguous")
        headers, genes = [], []
        with gzip.open(ensembl, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("#!"):
                    headers.append(line.rstrip())
                elif not line.startswith("#"):
                    fields = line.rstrip().split("\t")
                    if len(fields) == 9 and fields[2] == "gene":
                        attrs = dict(re.findall(r'(\w+) "([^"]*)"', fields[8]))
                        if attrs.get("gene_id") == "ENSG00000119403":
                            genes.append(attrs)
        if "#!genome-build GRCh38.p14" not in headers or "#!genome-build-accession GCA_000001405.29" not in headers:
            raise InputsRefused("Ensembl assembly mismatch")
        if len(genes) != 1 or genes[0].get("gene_name") != "PHF19" or genes[0].get("gene_version") != "16":
            raise InputsRefused("Ensembl gene annotation is absent, duplicate or inconsistent")
        with _open(locations["crosswalk"]) as handle:
            corroboration = [r for r in csv.DictReader(handle, delimiter="\t") if r.get("ensgene") == "ENSG00000119403"]
        if len(corroboration) != 1 or corroboration[0].get("symbol") != "PHF19":
            raise InputsRefused("original source crosswalk is absent or ambiguous")
        if (
            sorted({stage_token(s, "_") for s in matrix_header(locations["matrix"])[1:]}) != ["NDMM", "PD"]
            or row_hits(locations["matrix"], "ENSG00000119403") != 1
        ):
            raise InputsRefused("matrix feature or group-label inventory mismatch")
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        raise InputsRefused(f"unreadable PHF19 source: {error}") from error
    mapping_members = b"ensembl:ENSG00000119403\thgnc:24566\n"
    mapping = ReferentMapping(
        "biology/ensembl-gene",
        "biology/gene",
        {
            "hgnc_release": "2025-09-05",
            "ensembl_release": "115",
            "assembly": "GRCh38.p14",
            "evidence": str(declaration["evidence"]),
            "hgnc_sha256": digests["hgnc"],
            "ensembl_sha256": digests["ensembl"],
            "historical_matrix_annotation_release": "unknown",
        },
        "one-to-one",
        None,
        "sha256:" + sha256(mapping_members).hexdigest(),
    )
    return PHF19Inputs(
        *(
            expected[k]
            for k in (
                "source_proposition",
                "source_dataset",
                "feature",
                "gene",
                "factor",
                "baseline",
                "comparison",
                "separator",
            )
        ),
        MappingProxyType(dict(digests)),
        mapping,
        mapping_members,
    )
