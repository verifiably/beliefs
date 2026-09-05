"""Task 2: enumerate candidates under the design's §3 four criteria and write target.yaml."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import yaml

from reproduction import paths, state

EMPIRICAL_LAYERS = ("causal_effect", "empirical_regularity")


def front(path: Path) -> dict:
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def rank(candidates: list[dict]) -> list[dict]:
    """Empirical layer first, then a dataset under the predecessor's own
    `data/` before one resolved elsewhere on the host (§3 "locally held"),
    then the smallest held dataset, then the most empirical evidence lines;
    the id breaks ties so the order is total."""
    return sorted(
        candidates,
        key=lambda c: (
            0 if c["claim_layer"] in EMPIRICAL_LAYERS else 1,
            0 if c.get("under_data", True) else 1,
            c["dataset_bytes"],
            -c["empirical_lines"],
            c["proposition_id"],
        ),
    )


def dataset_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) if root.is_dir() else root.stat().st_size


def main() -> int:
    root = paths.PREDECESSOR
    propositions = {
        f["id"]: f
        for p in (root / "entities" / "propositions").glob("*.md")
        if (f := front(p)).get("predicate") and f.get("subject") and f.get("object")
    }
    lines: dict[str, list[dict]] = defaultdict(list)
    for p in (root / "entities" / "evidence-lines").glob("*.md"):
        f = front(p)
        if f.get("evidence_type") == "empirical_data" and f.get("belief_eligible") is True:
            lines[f.get("target")].append(f)
    datasets: dict[str, Path] = {}
    for p in (root / "entities" / "datasets").glob("*.md"):
        f = front(p)
        local = f.get("local_path") or (str(Path(f["datapackage"]).parent) if f.get("datapackage") else "")
        # `local_path` is absolute for datasets held outside the predecessor
        # (`/data/proj/mm30/...`, `/data/raw/...`); `root / absolute` is the absolute path.
        if local and (root / local).exists():
            datasets[f["id"]] = (root / local).resolve()
    candidates = []
    for pid, prop in propositions.items():
        if pid not in lines:
            continue
        named = set(prop.get("datasets") or []) | {
            r for r in (prop.get("related") or []) if str(r).startswith("dataset:")
        }
        for line in lines[pid]:
            named |= {r for r in (line.get("related") or []) if str(r).startswith("dataset:")}
            # The predecessor's evidence lines name the datasets they analyzed in
            # `dataset_usage` (role `analyzed`), not in `related`; that is the join.
            named |= {
                str(u.get("ref"))
                for u in (line.get("dataset_usage") or [])
                if isinstance(u, dict) and u.get("role") == "analyzed" and str(u.get("ref", "")).startswith("dataset:")
            }
        for did in sorted(named):
            if did in datasets:
                candidates.append(
                    {
                        "proposition_id": pid,
                        "subject": prop["subject"],
                        "predicate": prop["predicate"],
                        "object": prop["object"],
                        "claim_layer": prop.get("claim_layer"),
                        "polarity": prop.get("polarity"),
                        "identification_strength": prop.get("identification_strength"),
                        "dataset_id": did,
                        "dataset_path": str(datasets[did]),
                        "dataset_bytes": dataset_bytes(datasets[did]),
                        "under_data": datasets[did].is_relative_to((root / "data").resolve()),
                        "empirical_lines": len(lines[pid]),
                        "evidence_line_ids": [line["id"] for line in lines[pid]],
                    }
                )
    ordered = rank(candidates)
    if not ordered:
        print("no proposition joins to a held dataset through its own fields; relax per spec §3 and record which")
        return 2
    chosen = dict(ordered[0])
    chosen["alternatives"] = ordered[1:5]
    paths.TARGET.write_text(yaml.safe_dump(chosen, sort_keys=False))
    state.save(target=chosen["proposition_id"], dataset=chosen["dataset_id"])
    print(
        f"candidates: {len(candidates)}; chosen: {chosen['proposition_id']} over {chosen['dataset_id']} "
        f"({chosen['dataset_bytes']} bytes)"
    )
    for c in ordered[:5]:
        print(f"  {c['proposition_id']}  layer={c['claim_layer']}  dataset={c['dataset_id']}  bytes={c['dataset_bytes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
