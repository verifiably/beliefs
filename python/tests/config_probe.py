"""Observe the values Snakemake delivers for rendered config."""

import json
import os
import subprocess
import sys

PROBE = """\
import json, pathlib

rule probe:
    output: "out.json"
    run:
        rows = {k: [type(v).__name__, v] for k, v in config.items()}
        pathlib.Path(output[0]).write_text(json.dumps(rows, sort_keys=True))
"""


def run_config_probe(tmp_path, config):
    """Return each config value's engine-observed type name and value."""
    work = tmp_path / "probe"
    work.mkdir()
    (work / "Snakefile").write_text(PROBE)
    argv = [
        sys.executable,
        "-m",
        "snakemake",
        "--snakefile",
        str(work / "Snakefile"),
        "--cores",
        "1",
        "--directory",
        str(work),
        "--nolock",
        "--config",
        *(f"{key}={value}" for key, value in config.items()),
        "--",
        "out.json",
    ]
    result = subprocess.run(
        argv,
        cwd=work,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return json.loads((work / "out.json").read_text())
