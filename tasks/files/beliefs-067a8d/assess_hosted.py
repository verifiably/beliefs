"""Assess a downloaded hosted run against the adoption spec's Hosted acceptance criteria.

Usage: python3 -I assess_hosted.py <artifacts-dir> <baseline-skip-reason>...

<artifacts-dir> holds one subdirectory per matrix job, as `gh run download` writes them
(python-3.11-coverage/, python-3.13-coverage/, typescript-20-coverage/, ...). Each
baseline reason is a non-capability skip reason from the local baseline. Prints a
per-job report and exits 0 only when every criterion holds for every job.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

CAPABILITY = "certified tuple unavailable on this host:"


def cases(path: Path) -> list[ET.Element]:
    return ET.parse(path).findall(".//testcase")


def outcome(case: ET.Element) -> str:
    for kind in ("failure", "error", "skipped"):
        if case.find(kind) is not None:
            return kind
    return "passed"


def module_of(case: ET.Element, python: bool) -> str:
    classname = case.attrib.get("classname", "")
    if not python:
        name = classname if classname.startswith("tests/") else f"tests/{classname}"
        return name
    parts = classname.split(".")
    # tests.test_x or tests.test_x.TestClass -> tests/test_x.py
    for end in range(len(parts), 0, -1):
        if parts[end - 1].startswith("test_") or parts[end - 1].endswith("_test"):
            return "/".join(parts[:end]) + ".py"
    return classname


def assess(job_dir: Path, baseline: set[str]) -> tuple[bool, list[str]]:
    python = job_dir.name.startswith("python")
    lines = (job_dir / "module-inventory.txt").read_text().splitlines()
    revisions = [line for line in lines if line.split(" ")[0] in ("beliefs", "atoms", "nodes") and len(line.split()) == 2]
    modules = [line for line in lines if line.startswith("tests/")]
    phases = {"pytest.xml": "non-N2", "pytest-n2.xml": "N2"} if python else {"vitest.xml": "Vitest"}
    report = [f"## {job_dir.name}", "revisions: " + "; ".join(revisions)]
    ok = True
    seen: dict[str, list[str]] = {}
    capability: list[str] = []
    other: Counter[str] = Counter()
    for xml, phase in phases.items():
        path = job_dir / xml
        if not path.is_file():
            report.append(f"FAIL {phase}: {xml} missing")
            ok = False
            continue
        found = cases(path)
        counts = Counter(outcome(case) for case in found)
        executed = len(found) - counts["skipped"]
        report.append(
            f"{phase}: {len(found)} cases, executed {executed}, passed {counts['passed']}, "
            f"skipped {counts['skipped']}, failed {counts['failure']}, errors {counts['error']}"
        )
        if executed == 0:
            report.append(f"FAIL {phase}: no executed test")
            ok = False
        if counts["failure"] or counts["error"]:
            report.append(f"FAIL {phase}: failed or errored tests")
            ok = False
        for case in found:
            module = module_of(case, python)
            seen.setdefault(module, []).append(outcome(case))
            if (skipped := case.find("skipped")) is not None:
                message = skipped.attrib.get("message", "")
                test_id = f"{case.attrib.get('classname')}::{case.attrib.get('name')}"
                if message.startswith(CAPABILITY):
                    capability.append(test_id)
                else:
                    other[message] += 1
        expected_here = [m for m in modules if (m.endswith("test_n2.py")) == (xml == "pytest-n2.xml")] if python else modules
        absent = [m for m in expected_here if m not in seen]
        report.append(f"{phase}: eligible modules expected {len(expected_here)}, absent {len(absent)}")
        for module in absent:
            report.append(f"FAIL absent module: {module}")
            ok = False
    report.append(f"capability omissions: {len(capability)}")
    report.extend(f"  {test_id}" for test_id in sorted(capability))
    report.append(f"other skips: {sum(other.values())} in {len(other)} reasons")
    for message, count in sorted(other.items()):
        known = any(reason in message or message in reason for reason in baseline) and message != ""
        report.append(f"  {count} x {'baseline' if known else 'NEW'}: {message or '(no message)'}")
        if not known:
            ok = False
    whole = sorted(m for m, outcomes in seen.items() if outcomes and all(o == "skipped" for o in outcomes))
    report.append(f"wholly skipped modules: {len(whole)}")
    report.extend(f"  {module}" for module in whole)
    report.append("verdict: " + ("accept" if ok else "BLOCKED"))
    return ok, report


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    baseline = set(argv[2:])
    jobs = sorted(path for path in root.iterdir() if path.is_dir())
    if not jobs:
        print("no job artifacts found")
        return 1
    all_ok = True
    for job in jobs:
        ok, report = assess(job, baseline)
        all_ok &= ok
        print("\n".join(report), end="\n\n")
    print("overall: " + ("accept" if all_ok else "BLOCKED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
