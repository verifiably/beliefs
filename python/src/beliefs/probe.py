"""The held probe that gates the confined engine (design §6.1–§6.2).

It runs inside the sandbox as the engine's own process: performs its checks,
writes the report and READY on the report descriptor, waits for GO on the go
descriptor, closes both, and ``execve``s the engine. It decides nothing — the
boundary judges the report from outside. Its one write check touches and
removes a file with inventoried operations (``Path.touch``, ``unlink``), so
``test_capability_boundary.py`` weighs this module as the fourth raw-write
surface rather than a raw ``os.open`` escaping the inventory.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import pathlib
import socket
import struct
import subprocess
import sys

_ELF_MAGIC = b"\x7fELF"
_ENV_ROOT = "/science/env"
_READ_PROBES = ("/etc/passwd", "/tmp")
_WRITE_PROBES = ("/", "/science/bundle", "/science/env", "/science/out/inputs", "/science/out")
_IPV4 = ("192.0.2.1", 9)
_IPV6 = ("2001:db8::1", 9)


def _errno_name(error: OSError) -> str:
    if error.errno is None:
        return type(error).__name__
    return errno.errorcode.get(error.errno, f"errno{error.errno}")


def _read_probe(path: str) -> str:
    try:
        with open(path, "rb"):
            return "READ"
    except OSError as error:
        return _errno_name(error)


def _write_probe(directory: str) -> str:
    probe = pathlib.Path(directory) / ".probe"
    try:
        probe.touch(mode=0o600, exist_ok=False)
    except OSError as error:
        return _errno_name(error)
    probe.unlink()
    return "OK"


def _connect(family: int, address: tuple[str, int]) -> str:
    try:
        sock = socket.socket(family, socket.SOCK_STREAM)
    except OSError as error:
        return _errno_name(error)
    try:
        sock.settimeout(2.0)
        sock.connect(address)
        return "CONNECTED"
    except OSError as error:
        return _errno_name(error)
    finally:
        sock.close()


def _digest(path: str) -> str:
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def _is_loadable_elf(path: str) -> bool:
    """The same predicate as adapter._is_loadable_elf: ELF of type ET_EXEC or ET_DYN."""
    with open(path, "rb") as handle:
        header = handle.read(18)
    return len(header) == 18 and header[:4] == _ELF_MAGIC and struct.unpack_from("<H", header, 16)[0] in (2, 3)


def _elf_architecture(path: str) -> tuple[int, int, int]:
    """(EI_CLASS, EI_DATA, e_machine) — the same identity triple adapter.py's
    ``_elf_architecture`` computes on the host, mirrored here so the probe
    lists exactly the architecture-matched set the capture's loader map
    covers (design §5.3, ruling R4)."""
    with open(path, "rb") as handle:
        header = handle.read(20)
    endian = "<" if header[5] == 1 else ">"
    (e_machine,) = struct.unpack_from(f"{endian}H", header, 18)
    return (header[4], header[5], e_machine)


def _elves() -> list[str]:
    """Every loadable ELF regular file under the environment root whose
    architecture matches the running interpreter's own — the same
    architecture-matched set the boundary's loader map covers (design §5.3,
    ruling R4); symlinked directories are not followed. A foreign-architecture
    file (a vendored solver for another platform, say) stays outside the
    probe's listing exactly as it stayed outside the captured map."""
    reference = _elf_architecture(os.path.realpath(sys.executable))
    found: list[str] = []
    for directory, _, names in os.walk(_ENV_ROOT):
        for name in names:
            path = os.path.join(directory, name)
            if (
                os.path.isfile(path)
                and not os.path.islink(path)
                and _is_loadable_elf(path)
                and _elf_architecture(path) == reference
            ):
                found.append(path)
    return sorted(found)


def _listing(loader: str, path: str) -> dict[str, object]:
    """The loader's own in-layout resolution, reported whole: exit status, every
    resolved SONAME with the path as listed and its digest, every line that did
    not resolve. The boundary requires equality with its captured map."""
    completed = subprocess.run([loader, "--list", path], capture_output=True, text=True, check=False)
    resolved: dict[str, list[str]] = {}
    unresolved: list[str] = []
    for line in completed.stdout.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith(("linux-vdso", "linux-gate")) or parts[0].startswith("/"):
            continue
        if len(parts) >= 3 and parts[1] == "=>" and parts[2] != "not":
            resolved[parts[0]] = [parts[2], _digest(parts[2])]
        else:
            unresolved.append(line.strip())
    return {"returncode": completed.returncode, "resolved": resolved, "unresolved": unresolved}


def report(loader: str) -> dict[str, object]:
    return {
        "environ": dict(os.environ),
        "hostname": os.uname().nodename,
        "cwd": os.getcwd(),
        "filesystem": {
            **{f"read:{path}": _read_probe(path) for path in _READ_PROBES},
            **{f"write:{path}": _write_probe(path) for path in _WRITE_PROBES},
        },
        "network": {"ipv4": _connect(socket.AF_INET, _IPV4), "ipv6": _connect(socket.AF_INET6, _IPV6)},
        "loader": {elf: _listing(loader, elf) for elf in _elves()},
    }


def main(argv: list[str]) -> int:
    separator = argv.index("--")
    options = dict(zip(argv[:separator:2], argv[1:separator:2]))
    engine = argv[separator + 1 :]
    report_fd = int(options["--report-fd"])
    go_fd = int(options["--go-fd"])
    payload = report(options["--loader"])
    with os.fdopen(report_fd, "w", encoding="utf-8") as out:
        out.write(json.dumps(payload, sort_keys=True) + "\nREADY\n")
    with os.fdopen(go_fd, "r", encoding="utf-8") as go:
        line = go.readline()
    if line.rstrip("\n") != "GO":
        return 3
    os.execv(engine[0], engine)
    return 4  # pragma: no cover - execv does not return


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
