"""Confinement values shared by `conftest.py` and `confinement_fixtures.py`.

Split out so both a plain `tests/`-scoped test and an acceptance-scoped one
(`tests/acceptance/...`) can import these by an unambiguous name: `conftest`
is not one, since pytest's ancestor-conftest chain also loads
`tests/acceptance/conftest.py` under the same bare name for any
acceptance-scoped collection, and whichever conftest loads last wins the
`sys.modules['conftest']` slot.
"""

ENVIRONMENT = "sha256:" + "ab" * 32
CONFINED_MOUNTS = (
    ("/", "root", "ro"),
    ("/lib64/ld-linux-x86-64.so.2", "loader", "ro"),
    ("/science/env", "env", "ro"),
    ("/science/bundle", "bundle", "ro"),
    ("/science/out", "output", "rw"),
    ("/science/out/inputs", "inputs", "ro"),
    ("/dev/null", "device", "rw"),
    ("/dev/urandom", "device", "rw"),
)
RENDERED_ENVIRONMENT = (("env:PATH", "value", "/science/env/venv/bin"), ("hostname", "value", "science"))
SANDBOX_MOUNTS = (("/science/bundle", "/host/scratch/run-1/bundle"), ("/science/out", "/host/scratch/run-1/out"))
