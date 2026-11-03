"""The one acceptance runner: every `tests/acceptance` module, each in its own process."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from checkout import MAIN_CHECKOUT

PROBE_REFUSED = 2
OLD_ROOT_REFUSED = 3

DEFAULT_ACCEPTANCE_ROOT = MAIN_CHECKOUT / ".work" / "acceptance"

_OLD_ROOT = re.compile(r"SCIENCE_CUT(\d+)_ROOT")
_REPLACEMENTS = {
    "4": "BELIEFS_ACCEPTANCE_ROOT",
    "10": "BELIEFS_TEST_ROOT",
    "12": "BELIEFS_TEST_ROOT",
    "13": "BELIEFS_TEST_ROOT",
}


def refuse_old_roots(environ: Mapping[str, str]) -> str | None:
    """The refusal message when any `SCIENCE_CUT<n>_ROOT` is present (even empty), else None."""
    found = sorted((match.group(1), key) for key in environ if (match := _OLD_ROOT.fullmatch(key)))
    if not found:
        return None
    lines = ["the cut-named work-root variables were renamed and are no longer read:"]
    for number, key in found:
        replacement = _REPLACEMENTS.get(number, "BELIEFS_ACCEPTANCE_ROOT or BELIEFS_TEST_ROOT")
        lines.append(f"  {key} is set: use {replacement} instead")
    lines.append("Unset the old variable(s); this is an error, not a fallback.")
    return "\n".join(lines)


def _probe(run: Path, actor: str) -> str | None:
    from beliefs.permit import Authority, WritePermit
    from beliefs.root import init_corpus_root, metadata_root_for

    corpus_root = run / "probe-corpus"
    try:
        init_corpus_root(corpus_root, authority=Authority(WritePermit.full(), actor))
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(corpus_root), ignore_errors=True)


def run_acceptance(*, python_root: Path, work: Path, argv: list[str]) -> int:
    acceptance = python_root / "tests" / "acceptance"
    modules = sorted(acceptance.glob("test_*.py"))
    work.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = _probe(run, "acceptance-probe")
        if refusal is not None:
            print(
                "acceptance cannot run here: its durable corpus prerequisite refused.\n"
                f"  {refusal}\n"
                "  Set BELIEFS_ACCEPTANCE_ROOT to a certified volume or recertify the tuple. "
                "This is an error, not a skip.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        environment = {
            **os.environ,
            "XDG_CACHE_HOME": str(run / ".cache"),
            "BELIEFS_ACCEPTANCE_ROOT": str(run),
        }
        for index, module in enumerate(modules, start=1):
            print(f"[acceptance {index}/{len(modules)}] {module.name}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(module),
                    *(argv if index == len(modules) else []),
                ],
                cwd=python_root,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                return completed.returncode
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


def main(argv: list[str]) -> int:
    refusal = refuse_old_roots(os.environ)
    if refusal is not None:
        print(refusal, file=sys.stderr)
        return OLD_ROOT_REFUSED
    configured = os.environ.get("BELIEFS_ACCEPTANCE_ROOT")
    work = Path(configured) if configured else DEFAULT_ACCEPTANCE_ROOT
    return run_acceptance(python_root=Path(__file__).resolve().parents[1], work=work, argv=argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
