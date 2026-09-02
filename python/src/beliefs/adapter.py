"""Minimal Snakemake execution adapter and held-content capture."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import os
import posixpath
import re
import shutil
import struct
import subprocess
import sys
import sysconfig
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import cast, final

from beliefs.errors import ClosureUnsupported, MalformedClosure, UnsafeInvocation
from beliefs.identity import v1
from beliefs.recipe import EnvironmentManifest, TraceJob
from beliefs.sealed import sealed
from beliefs.spec import RealizedSeeds

WORKFLOW_DEFINITION_DOMAIN = "science.workflow-definition.v1"
_CONFIG_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PEP_503_RUN = re.compile(r"[-_.]+")
SANDBOX_ENV = "/science/env"
SANDBOX_PYTHON = "/science/env/python"
SANDBOX_SITE = "/science/env/site"
SANDBOX_PATH = "/science/env/path"
SANDBOX_LIB = "/science/env/lib"
SANDBOX_VENV = "/science/env/venv"
_ELF_MAGIC = b"\x7fELF"
_PT_INTERP = 3
_PT_LOAD = 1
_PT_DYNAMIC = 2
_DT_NULL = 0
_DT_STRTAB = 5
_DT_RPATH = 15
_DT_RUNPATH = 29

LOG_HANDLER_SCRIPT = """\
import json
import os

_EVENTS = os.environ["SCIENCE_TRACE_FILE"]


def log_handler(msg):
    if msg.get("level") == "job_info":
        with open(_EVENTS, "a", encoding="utf-8") as events:
            events.write(json.dumps(msg, default=str) + "\\n")
"""


@sealed
@final
@dataclass(frozen=True)
class WorkflowDefinition:
    snakefile: bytes
    family_streams: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if type(self.snakefile) is not bytes:
            raise MalformedClosure("workflow definition snakefile must be bytes")
        if not isinstance(self.family_streams, Mapping) or not all(
            type(family) is str and type(streams) is tuple and all(type(stream) is str for stream in streams)
            for family, streams in self.family_streams.items()
        ):
            raise MalformedClosure("workflow family streams must map strings to tuples of strings")
        object.__setattr__(self, "family_streams", MappingProxyType(dict(self.family_streams)))

    def identity(self) -> str:
        return v1.digest(
            WORKFLOW_DEFINITION_DOMAIN,
            {
                "snakefile": "sha256:" + sha256(self.snakefile).hexdigest(),
                "family_streams": {family: sorted(streams) for family, streams in self.family_streams.items()},
            },
        )


def _file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _fold(rows: list[tuple[str, str]]) -> str:
    folded = "".join(f"{name}\n{digest}\n" for name, digest in sorted(rows)).encode()
    return "sha256:" + sha256(folded).hexdigest()


def create_scratch_root(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=base))


def capture_bundle(code_roots: tuple[Path, ...], bundle_dir: Path) -> str:
    rows: list[tuple[str, str]] = []
    names: set[str] = set()
    bundle_dir.mkdir(parents=True)
    for root in code_roots:
        for source in sorted(root.rglob("*")):
            relative = source.relative_to(root)
            if ".git" in relative.parts or not source.is_file():
                continue
            name = (Path(root.name) / relative).as_posix()
            if name in names:
                raise MalformedClosure(f"code roots map more than one file to bundle path {name!r}")
            names.add(name)
            target = bundle_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            rows.append((name, _file_digest(target)))
    return _fold(rows)


def _distribution_cache(parts: tuple[str, ...]) -> bool:
    return "__pycache__" in parts or bool(parts and parts[-1].endswith(".pyc"))


def _stdlib_excluded(parts: tuple[str, ...]) -> bool:
    return "site-packages" in parts or _distribution_cache(parts)


def tree_digest(root: Path, *, label: str) -> str:
    """Fold a file tree under location-independent logical names."""
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if _stdlib_excluded(relative.parts) or not path.is_file():
            continue
        rows.append((f"{label}/{relative.as_posix()}", _file_digest(path)))
    return _fold(rows)


def distribution_digest(dist: importlib.metadata.Distribution) -> str:
    """Fold all non-derived files enumerated by a distribution RECORD."""
    name = dist.metadata["Name"]
    record = dist.read_text("RECORD")
    if not record:
        raise MalformedClosure(f"distribution {name!r} has no readable RECORD — its inventory cannot be enumerated")
    rows = []
    for row in csv.reader(record.splitlines()):
        if not row or not row[0]:
            raise MalformedClosure(f"distribution {name!r} has a malformed RECORD entry")
        entry = importlib.metadata.PackagePath(row[0])
        if _distribution_cache(entry.parts):
            continue
        located = Path(str(dist.locate_file(entry)))
        if not located.is_file():
            raise MalformedClosure(f"distribution {name!r}: RECORD lists {entry} and no such file exists")
        rows.append((entry.as_posix(), _file_digest(located)))
    return _fold(rows)


def _stdlib_digest() -> str:
    labelled = {
        ("stdlib", Path(sysconfig.get_path("stdlib")).resolve()),
        ("platstdlib", Path(sysconfig.get_path("platstdlib")).resolve()),
    }
    return _fold([(label, tree_digest(root, label=label)) for label, root in sorted(labelled)])


def _canonical_distribution_name(name: str) -> str:
    return _PEP_503_RUN.sub("-", name).lower()


@sealed
@final
@dataclass(frozen=True)
class CapturedEnvironment:
    """The closure as captured: the manifest, the ephemeral host plan for
    materializing it, the rendered rows, the loader path, the interpreter's
    sandbox path, the loader map — (ELF, SONAME, resolved sandbox path) for
    every dependency a loadable ELF under the environment root has — and
    `loader_elves`, every architecture-matched loadable ELF under the
    environment root, whether or not it has a dependency of its own. The
    probe's in-layout listing must reproduce both exactly: a zero-dependency
    ELF is a key with an empty map, not an omission (design §4.1–§4.2,
    §5.2–§5.3, ruling R6)."""

    manifest: EnvironmentManifest
    plan: Mapping[str, Path]
    rendered: tuple[tuple[str, str, str], ...]
    loader: str
    interpreter: str
    loader_map: tuple[tuple[str, str, str], ...]
    loader_elves: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.manifest) is not EnvironmentManifest:
            raise MalformedClosure("a captured environment carries an EnvironmentManifest")
        paths = {path for path, _, _ in self.manifest.artifacts}
        if set(self.plan) != paths:
            raise MalformedClosure("the capture plan covers exactly the manifest's rows")
        if not self.loader.startswith("/") or self.loader not in paths:
            raise MalformedClosure("the loader is an absolute path and a manifest row")
        for path in paths:
            if not (path.startswith(f"{SANDBOX_ENV}/") or path == self.loader):
                raise MalformedClosure(f"manifest row {path!r} lies outside {SANDBOX_ENV} and is not the loader")
        if self.interpreter not in paths:
            raise MalformedClosure("the interpreter is a manifest row")
        if {rendered for rendered, _, _ in self.rendered} & paths:
            raise MalformedClosure("a rendered row may not shadow a manifest row")
        for elf, _, resolved in self.loader_map:
            if elf not in paths or resolved not in paths:
                raise MalformedClosure("the loader map names manifest rows only")
        if not all(elf in paths for elf in self.loader_elves):
            raise MalformedClosure("the loader elves are manifest rows")
        if not {elf for elf, _, _ in self.loader_map} <= set(self.loader_elves):
            raise MalformedClosure("every loader map ELF is a loader elf")
        object.__setattr__(self, "plan", MappingProxyType(dict(self.plan)))


def _located(host: Path) -> Path:
    """The path's own location: its parent resolved, its name kept — so a
    symlink is captured as the link, not as its target."""
    return Path(os.path.realpath(host.parent)) / host.name


def _path_tree_excluded(parts: tuple[str, ...]) -> bool:
    return ".git" in parts or _distribution_cache(parts)


def _import_names(line: str) -> list[str]:
    body = line[len("import"):].split(";", 1)[0]
    return [part.strip().split(" as ")[0].strip().split(".")[0] for part in body.split(",") if part.strip()]


class _Closure:
    """The walker. `rows` and `plan` are keyed by sandbox path; `rendered`
    holds the rows the boundary renders from the layout."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, str]] = {}
        self.plan: dict[str, Path] = {}
        self.rendered: dict[str, tuple[str, str]] = {}
        self.loader_map: list[tuple[str, str, str]] = []
        self.loader_elves: list[str] = []
        self.native_arch: tuple[int, int, int] | None = None
        self._sonames: dict[str, Path] = {}
        self._roots: list[tuple[Path, str]] = []

    def register(self, host_root: Path, sandbox_root: str) -> None:
        self._roots.append((Path(os.path.realpath(host_root)), sandbox_root))
        self._roots.sort(key=lambda pair: len(str(pair[0])), reverse=True)

    def root_of(self, located: Path) -> tuple[Path, str] | None:
        for host_root, sandbox_root in self._roots:
            try:
                common = os.path.commonpath((host_root, located))
            except ValueError:
                continue
            if common == os.fspath(host_root):
                return host_root, sandbox_root
        return None

    def sandbox_of(self, located: Path) -> str:
        root = self.root_of(located)
        if root is None:
            raise ClosureUnsupported(f"{located} lies outside every closure root")
        host_root, sandbox_root = root
        relative = os.path.relpath(located, host_root).replace(os.sep, "/")
        return f"{sandbox_root}/{relative}"

    def add(self, host: Path) -> str:
        """One row. A symlink's target is captured with it: a relative target
        staying under the link's own root keeps its relative text, any other
        in-closure target is rewritten to its sandbox path, a target outside
        every root escapes, and a target that names nothing is dangling."""
        located = _located(host)
        sandbox = self.sandbox_of(located)
        if sandbox in self.rows:
            return sandbox
        if located.is_symlink():
            target = os.readlink(located)
            target_host = _located(Path(os.path.normpath(target if os.path.isabs(target) else located.parent / target)))
            root = self.root_of(located)
            target_root = self.root_of(target_host)
            if target_root is None:
                raise ClosureUnsupported(f"symlink {located} -> {target!r} escapes the closure")
            same_root = not os.path.isabs(target) and root == target_root
            self.rows[sandbox] = ("symlink", target if same_root else self.sandbox_of(target_host))
            self.plan[sandbox] = located
            if target_host.is_symlink() or target_host.is_file():
                self.add(target_host)
            elif not target_host.is_dir():
                raise ClosureUnsupported(f"symlink {located} -> {target!r} names nothing")
            return sandbox
        if located.is_file():
            self.rows[sandbox] = ("file", _file_digest(located))
            self.plan[sandbox] = located
            return sandbox
        raise ClosureUnsupported(f"{located} is neither a regular file nor a symlink")

    def add_chain(self, host: Path) -> str:
        """Every link of a symlink chain as a symlink row and its terminal file
        as a file row; returns the terminal's sandbox path (design §4.2)."""
        located = _located(host)
        seen: set[Path] = set()
        while located.is_symlink():
            if located in seen:
                raise ClosureUnsupported(f"{host} is a symlink cycle")
            seen.add(located)
            self.add(located)
            target = os.readlink(located)
            located = _located(Path(os.path.normpath(target if os.path.isabs(target) else located.parent / target)))
        return self.add(located)

    def check_links(self) -> None:
        """Every symlink row resolves, within the sandbox layout, to a row or
        to a directory some row lies under — never to nothing."""
        for sandbox, (kind, content) in sorted(self.rows.items()):
            if kind != "symlink":
                continue
            resolved = content if content.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(sandbox), content))
            if resolved in self.rows or any(row.startswith(resolved + "/") for row in self.rows):
                continue
            raise ClosureUnsupported(f"symlink {sandbox} -> {content!r} resolves to {resolved}, which is not a closure row")

    def add_tree(self, root: Path, *, excluded: Callable[[tuple[str, ...]], bool]) -> None:
        for path in sorted(root.rglob("*")):
            if excluded(path.relative_to(root).parts):
                continue
            if path.is_symlink() or path.is_file():
                self.add(path)

    def add_records(self) -> None:
        for dist in importlib.metadata.distributions():
            name = dist.metadata["Name"]
            record = dist.read_text("RECORD")
            if not record:
                raise MalformedClosure(f"distribution {name!r} has no readable RECORD — its inventory cannot be enumerated")
            for row in csv.reader(record.splitlines()):
                if not row or not row[0]:
                    raise MalformedClosure(f"distribution {name!r} has a malformed RECORD entry")
                entry = importlib.metadata.PackagePath(row[0])
                if _distribution_cache(entry.parts) or entry.suffix == ".pth":
                    continue
                located = Path(os.path.normpath(str(dist.locate_file(entry))))
                if not located.is_file() and not located.is_symlink():
                    raise MalformedClosure(f"distribution {name!r}: RECORD lists {entry} and no such file exists")
                self.add(located)

    def add_pth(self, purelib: Path) -> None:
        for pth in sorted(purelib.glob("*.pth")):
            lines = [line for line in pth.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
            imports = [line for line in lines if line.startswith(("import ", "import\t"))]
            paths = [line for line in lines if line not in imports]
            if imports and paths:
                raise ClosureUnsupported(f"{pth.name} mixes import lines and path lines")
            if paths:
                targets = []
                for ordinal, line in enumerate(paths):
                    tree = Path(line.strip())
                    if not tree.is_absolute() or not tree.is_dir():
                        raise ClosureUnsupported(f"{pth.name} line {ordinal} names {line!r}, not an absolute directory")
                    sandbox_root = f"{SANDBOX_PATH}/{pth.name}/{ordinal}"
                    self.register(tree, sandbox_root)
                    self.add_tree(tree, excluded=_path_tree_excluded)
                    targets.append(sandbox_root)
                self.rendered[f"{SANDBOX_SITE}/{pth.name}"] = ("file", "".join(f"{target}\n" for target in targets))
                continue
            self.add(pth)
            for line in imports:
                for module in _import_names(line):
                    if f"{SANDBOX_SITE}/{module}.py" in self.rows or f"{SANDBOX_SITE}/{module}/__init__.py" in self.rows:
                        continue
                    candidate = purelib / f"{module}.py"
                    if candidate.is_file():
                        self.add(candidate)
                        continue
                    raise ClosureUnsupported(f"{pth.name} imports {module!r}, which is not a closure member")

    def add_native(self, *, listing: Callable[[Path], Mapping[str, Path]]) -> None:
        """The loader's own resolution for every loadable ELF under the
        environment root, closed to a fixpoint over the libraries it adds, and
        the expected map row for each — what the probe must reproduce. An ELF
        that resolves zero dependencies of its own still ends up in
        `loader_elves` — every ELF the walk ever listed — so it stays a key
        with an empty map rather than vanishing (design §5.3, ruling R6)."""
        listed: set[str] = set()
        while pending := [(sandbox, host) for sandbox, host in self.elves() if sandbox not in listed]:
            for elf_sandbox, elf in pending:
                listed.add(elf_sandbox)
                for soname, host in sorted(listing(elf).items()):
                    located = _located(host)
                    canonical = Path(os.path.realpath(located))
                    known = self._sonames.setdefault(soname, canonical)
                    if known != canonical:
                        raise ClosureUnsupported(f"SONAME {soname!r} resolves to both {known} and {canonical}")
                    if self.root_of(located) is not None:
                        resolved = self.add(located)
                    else:
                        resolved = f"{SANDBOX_LIB}/{soname}"
                        self.rows[resolved] = ("file", _file_digest(located))
                        self.plan[resolved] = located
                    self.loader_map.append((elf_sandbox, soname, resolved))
        self.loader_elves = sorted(listed)

    def elves(self) -> list[tuple[str, Path]]:
        """Every loadable ELF file row under the environment root, of the
        closure's own architecture, by sandbox path — the same set the probe
        enumerates in-layout (design §5.3, ruling R4). A foreign-class,
        foreign-encoding or foreign-machine file stays an ordinary row: it
        cannot execute in the sandbox regardless, its program interpreter
        being outside the closure."""
        reference = self.native_arch if self.native_arch is not None else _elf_architecture(Path(os.path.realpath(sys.executable)))
        return [
            (path, self.plan[path])
            for path, (kind, _) in sorted(self.rows.items())
            if kind == "file"
            and path.startswith(f"{SANDBOX_ENV}/")
            and _is_loadable_elf(self.plan[path])
            and _elf_architecture(self.plan[path]) == reference
        ]


def _is_loadable_elf(path: Path) -> bool:
    """ELF of type ET_EXEC or ET_DYN — what `ld.so --list` can list; a
    relocatable object is not."""
    with path.open("rb") as handle:
        header = handle.read(18)
    return len(header) == 18 and header[:4] == _ELF_MAGIC and struct.unpack_from("<H", header, 16)[0] in (2, 3)


def _elf_architecture(path: Path) -> tuple[int, int, int]:
    """(EI_CLASS, EI_DATA, e_machine) — the identity triple a loadable ELF
    must share with the capturing interpreter's own before the host loader
    is asked to list it (design §5.3, ruling R4): a foreign-architecture
    file is neither listable by this host's native loader nor executable in
    the sandbox, whose closure holds no matching program interpreter for it."""
    with path.open("rb") as handle:
        header = handle.read(20)
    endian = "<" if header[5] == 1 else ">"
    (e_machine,) = struct.unpack_from(f"{endian}H", header, 18)
    return (header[4], header[5], e_machine)


def elf_interpreter(path: Path) -> str:
    """PT_INTERP, read from the ELF program headers; nothing is hardcoded."""
    with path.open("rb") as handle:
        header = handle.read(64)
        if header[:4] != _ELF_MAGIC:
            raise ClosureUnsupported(f"{path} is not an ELF file")
        if header[5] != 1:
            raise ClosureUnsupported(f"{path} is not little-endian")
        if header[4] == 2:
            (phoff,) = struct.unpack_from("<Q", header, 0x20)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x36)
        elif header[4] == 1:
            (phoff,) = struct.unpack_from("<I", header, 0x1C)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x2A)
        else:
            raise ClosureUnsupported(f"{path} has an unknown ELF class")
        for index in range(phnum):
            handle.seek(phoff + index * phentsize)
            phdr = handle.read(phentsize)
            if struct.unpack_from("<I", phdr, 0)[0] != _PT_INTERP:
                continue
            if header[4] == 2:
                (offset,) = struct.unpack_from("<Q", phdr, 8)
                (size,) = struct.unpack_from("<Q", phdr, 32)
            else:
                (offset,) = struct.unpack_from("<I", phdr, 4)
                (size,) = struct.unpack_from("<I", phdr, 16)
            handle.seek(offset)
            return handle.read(size).rstrip(b"\0").decode("ascii")
    raise ClosureUnsupported(f"{path} names no program interpreter")


def _elf_library_path(path: Path) -> tuple[str, ...]:
    """DT_RUNPATH if present, else DT_RPATH, read from the ELF dynamic
    section and $ORIGIN-expanded against the binary's own real location,
    deduplicated in order — the one resolution context a process inherits
    process-wide from its own main executable at runtime, supplied to the
    host listing explicitly rather than left to the ambient environment
    (design §5.3)."""
    with path.open("rb") as handle:
        header = handle.read(64)
        if header[:4] != _ELF_MAGIC:
            raise ClosureUnsupported(f"{path} is not an ELF file")
        if header[5] != 1:
            raise ClosureUnsupported(f"{path} is not little-endian")
        is64 = header[4] == 2
        if is64:
            (phoff,) = struct.unpack_from("<Q", header, 0x20)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x36)
        elif header[4] == 1:
            (phoff,) = struct.unpack_from("<I", header, 0x1C)
            phentsize, phnum = struct.unpack_from("<HH", header, 0x2A)
        else:
            raise ClosureUnsupported(f"{path} has an unknown ELF class")
        loads: list[tuple[int, int, int]] = []
        dynamic: tuple[int, int] | None = None
        for index in range(phnum):
            handle.seek(phoff + index * phentsize)
            phdr = handle.read(phentsize)
            p_type = struct.unpack_from("<I", phdr, 0)[0]
            if is64:
                if p_type == _PT_LOAD:
                    p_offset, p_vaddr = struct.unpack_from("<QQ", phdr, 8)
                    (p_filesz,) = struct.unpack_from("<Q", phdr, 32)
                    loads.append((p_vaddr, p_offset, p_filesz))
                elif p_type == _PT_DYNAMIC:
                    (p_offset,) = struct.unpack_from("<Q", phdr, 8)
                    (p_filesz,) = struct.unpack_from("<Q", phdr, 32)
                    dynamic = (p_offset, p_filesz)
            else:
                if p_type == _PT_LOAD:
                    (p_offset,) = struct.unpack_from("<I", phdr, 4)
                    (p_vaddr,) = struct.unpack_from("<I", phdr, 8)
                    (p_filesz,) = struct.unpack_from("<I", phdr, 16)
                    loads.append((p_vaddr, p_offset, p_filesz))
                elif p_type == _PT_DYNAMIC:
                    (p_offset,) = struct.unpack_from("<I", phdr, 4)
                    (p_filesz,) = struct.unpack_from("<I", phdr, 16)
                    dynamic = (p_offset, p_filesz)
        if dynamic is None:
            return ()
        dyn_offset, dyn_size = dynamic

        def to_file_offset(vaddr: int) -> int:
            for seg_vaddr, seg_offset, seg_filesz in loads:
                if seg_vaddr <= vaddr < seg_vaddr + seg_filesz:
                    return seg_offset + (vaddr - seg_vaddr)
            raise ClosureUnsupported(f"{path} names a dynamic-section address outside its load segments")

        entry_size = 16 if is64 else 8
        strtab_vaddr: int | None = None
        rpath_val: int | None = None
        runpath_val: int | None = None
        handle.seek(dyn_offset)
        for _ in range(dyn_size // entry_size):
            entry = handle.read(entry_size)
            if is64:
                tag, val = struct.unpack_from("<qQ", entry, 0)
            else:
                tag, val = struct.unpack_from("<iI", entry, 0)
            if tag == _DT_NULL:
                break
            if tag == _DT_STRTAB:
                strtab_vaddr = val
            elif tag == _DT_RPATH:
                rpath_val = val
            elif tag == _DT_RUNPATH:
                runpath_val = val
        selected = runpath_val if runpath_val is not None else rpath_val
        if selected is None:
            return ()
        if strtab_vaddr is None:
            raise ClosureUnsupported(f"{path} has an RPATH or RUNPATH entry but no DT_STRTAB")
        strtab_offset = to_file_offset(strtab_vaddr)
        handle.seek(strtab_offset + selected)
        text = b""
        while True:
            block = handle.read(256)
            if not block:
                break
            text += block
            if b"\0" in block:
                break
        raw = text.split(b"\0", 1)[0].decode("ascii")
    origin = str(Path(os.path.realpath(path)).parent)
    directories: list[str] = []
    seen: set[str] = set()
    for part in raw.split(":"):
        if not part:
            continue
        expanded = part.replace("$ORIGIN", origin).replace("${ORIGIN}", origin)
        if expanded not in seen:
            seen.add(expanded)
            directories.append(expanded)
    return tuple(directories)


def _parse_listing(text: str) -> dict[str, Path]:
    listing: dict[str, Path] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith(("linux-vdso", "linux-gate")) or parts[0].startswith("/"):
            continue
        if len(parts) < 3 or parts[1] != "=>":
            raise ClosureUnsupported(f"unparseable loader line {line!r}")
        if parts[2] == "not":
            raise ClosureUnsupported(f"{parts[0]} does not resolve on this host")
        listing[parts[0]] = Path(parts[2])
    return listing


def loader_listing(loader: str, path: Path, library_path: tuple[str, ...] = ()) -> dict[str, Path]:
    """What `execve` will map for `path`, as the loader itself reports it —
    under an empty environment, so no ambient LD_LIBRARY_PATH or LD_PRELOAD
    shapes the capture. `library_path`, when supplied, is passed as the
    loader's own `--library-path` argument — the one resolution context
    supplied explicitly rather than ambiently (design §5.3)."""
    argv = [loader]
    if library_path:
        argv.extend(["--library-path", ":".join(library_path)])
    argv.extend(["--list", str(path)])
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, check=False, env={})
    except OSError as error:
        raise ClosureUnsupported(f"the loader {loader} could not be invoked: {error}") from error
    if completed.returncode != 0:
        raise ClosureUnsupported(f"the loader cannot list {path}: {completed.stderr.strip()}")
    return _parse_listing(completed.stdout)


def capture_closure() -> CapturedEnvironment:
    """The closure walk; a host read that fails mid-walk is ClosureUnsupported,
    never a raw OSError reaching the run boundary (design §8)."""
    try:
        return _walk_closure()
    except OSError as error:
        raise ClosureUnsupported(f"the runtime closure could not be read: {error}") from error


def _walk_closure() -> CapturedEnvironment:
    walker = _Closure()
    base = Path(os.path.realpath(sys.base_prefix))
    prefix = Path(os.path.realpath(sys.prefix))
    purelib = Path(os.path.realpath(sysconfig.get_path("purelib")))
    walker.register(base, SANDBOX_PYTHON)
    if prefix != base:
        walker.register(prefix, SANDBOX_VENV)
    walker.register(purelib, SANDBOX_SITE)
    interpreter = walker.add_chain(Path(sys.executable))
    interpreter_host = walker.plan[interpreter]
    if not interpreter_host.is_relative_to(base):
        raise ClosureUnsupported(f"the interpreter {interpreter_host} is outside its base prefix {base}")
    for name in ("stdlib", "platstdlib"):
        walker.add_tree(Path(os.path.realpath(sysconfig.get_path(name))), excluded=_stdlib_excluded)
    walker.add_records()
    walker.add_pth(purelib)
    loader = elf_interpreter(interpreter_host)
    library_path = _elf_library_path(interpreter_host)
    walker.native_arch = _elf_architecture(interpreter_host)
    walker.add_native(listing=lambda elf: loader_listing(loader, elf, library_path=library_path))
    walker.rows[loader] = ("file", _file_digest(Path(loader)))
    walker.plan[loader] = Path(loader)
    walker.check_links()
    version_dir = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    walker.rendered[f"{SANDBOX_VENV}/pyvenv.cfg"] = ("file", f"home = {SANDBOX_PYTHON}/bin\ninclude-system-site-packages = false\n")
    if f"{SANDBOX_VENV}/bin/python" not in walker.rows:
        walker.rendered[f"{SANDBOX_VENV}/bin/python"] = ("symlink", interpreter)
    walker.rendered[f"{SANDBOX_VENV}/lib/{version_dir}/site-packages"] = ("symlink", SANDBOX_SITE)
    return CapturedEnvironment(
        manifest=EnvironmentManifest(artifacts=tuple(sorted((path, kind, content) for path, (kind, content) in walker.rows.items()))),
        plan=walker.plan,
        rendered=tuple(sorted((path, kind, content) for path, (kind, content) in walker.rendered.items())),
        loader=loader,
        interpreter=interpreter,
        loader_map=tuple(sorted(walker.loader_map)),
        loader_elves=tuple(walker.loader_elves),
    )


def capture_environment() -> EnvironmentManifest:
    return capture_closure().manifest


def require_executing_environment(manifest: EnvironmentManifest) -> None:
    if manifest != capture_environment():
        raise MalformedClosure(
            "the recorded environment is not the executing environment — a recipe claiming "
            "environment A cannot run in environment B through this boundary (§4.5)"
        )


def validate_entrypoint(bundle_dir: Path, entrypoint: str) -> Path:
    bundle = bundle_dir.resolve()
    candidate = (bundle / entrypoint).resolve()
    if not candidate.is_relative_to(bundle) or not candidate.is_file():
        raise UnsafeInvocation(f"entrypoint {entrypoint!r} must resolve to a regular file inside the captured bundle")
    return candidate


def build_argv(
    *,
    interpreter: str,
    snakefile: str,
    directory: str,
    targets: tuple[str, ...],
    config: Mapping[str, str],
    log_handler: str,
    cores: int,
    in_process_jobs: bool,
) -> tuple[str, ...]:
    """Policy-neutral: the minimal policy supplies host paths, the confined
    policy sandbox paths. `in_process_jobs` adds `--force-use-threads`, under
    which Snakemake executes `run:` rules in-process instead of re-spawning
    itself through `/bin/sh` (design §5.5)."""
    for target in targets:
        if target.startswith("-"):
            raise UnsafeInvocation(
                f"target {target!r} is option-like; shell=False prevents shell injection, "
                "not option injection — targets are separated from options (cut 3 §3)"
            )
    for key in config:
        if not _CONFIG_KEY.fullmatch(key):
            raise UnsafeInvocation(f"config key {key!r} is not an identifier and could parse as an option")
    argv = [
        interpreter,
        "-m",
        "snakemake",
        "--snakefile",
        snakefile,
        "--cores",
        str(cores),
        "--directory",
        directory,
        "--nolock",
    ]
    if in_process_jobs:
        argv.append("--force-use-threads")
    argv.extend(["--log-handler-script", log_handler])
    if config:
        argv.append("--config")
        argv.extend(f"{key}={value}" for key, value in sorted(config.items()))
    argv.append("--")
    argv.extend(targets)
    return tuple(argv)


def run_engine(argv: tuple[str, ...], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
    completed = subprocess.run(
        list(argv), shell=False, capture_output=True, text=True, cwd=cwd, env=dict(env), check=False
    )
    return completed.returncode, completed.stdout + completed.stderr


def read_trace(events_file: Path) -> tuple[TraceJob, ...]:
    try:
        lines = events_file.read_text().splitlines()
    except (OSError, UnicodeError) as error:
        raise MalformedClosure("the engine trace is missing or unreadable") from error
    if not lines:
        raise MalformedClosure("the engine trace is empty")

    trace = []
    jobs_by_id: dict[str, TraceJob] = {}
    for line in lines:
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, UnicodeError) as error:
            raise MalformedClosure("the engine trace contains an unparseable record") from error
        if not isinstance(record, dict) or record.get("level") != "job_info":
            raise MalformedClosure("the engine trace contains a non-job_info record")
        required = ("jobid", "name", "input", "output", "wildcards")
        if any(name not in record for name in required):
            raise MalformedClosure("the engine trace record is missing a required member")
        job_id, rule = record["jobid"], record["name"]
        inputs, outputs, wildcards = record["input"], record["output"], record["wildcards"]
        if (
            type(job_id) not in (int, str)
            or str(job_id) == ""
            or type(rule) is not str
            or not rule
            or type(inputs) is not list
            or not all(type(value) is str for value in inputs)
            or type(outputs) is not list
            or not all(type(value) is str for value in outputs)
            or not isinstance(wildcards, dict)
            or not all(type(key) is str and type(value) is str for key, value in wildcards.items())
        ):
            raise MalformedClosure("the engine trace record has a malformed required member")
        job = TraceJob(
            job_id=str(job_id),
            rule=rule,
            wildcards=tuple(sorted(cast(dict[str, str], wildcards).items())),
            inputs=tuple(inputs),
            outputs=tuple(outputs),
        )
        previous = jobs_by_id.get(job.job_id)
        if previous is not None and previous != job:
            raise MalformedClosure(f"engine job ID {job.job_id!r} has conflicting required trace fields")
        if previous is None:
            jobs_by_id[job.job_id] = job
            trace.append(job)
    return tuple(trace)


def read_realized_seeds(scratch: Path) -> RealizedSeeds:
    reports = scratch / ".seeds"
    if reports.is_symlink():
        raise MalformedClosure("the seed-report path is a symlink, not a boundary-owned directory")
    if not reports.exists():
        return RealizedSeeds(seeds={})
    if not reports.is_dir():
        raise MalformedClosure("the seed-report path exists but is not a directory")

    merged: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, str]] = set()
    for report in sorted(reports.glob("*.json")):
        try:
            record = json.loads(report.read_text(), object_pairs_hook=_object_without_duplicate_keys)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise MalformedClosure(f"seed report {report.name!r} is unreadable") from error
        if not isinstance(record, dict):
            raise MalformedClosure(f"seed report {report.name!r} is not nested by job and stream")
        for job, per_stream in record.items():
            if type(job) is not str or not isinstance(per_stream, dict):
                raise MalformedClosure(f"seed report {report.name!r} is not nested by job and stream")
            for stream, seed in per_stream.items():
                if type(stream) is not str or type(seed) is not int:
                    raise MalformedClosure(f"seed report {report.name!r} has a malformed claim")
                key = (job, stream)
                if key in seen:
                    raise MalformedClosure(f"seed report repeats claim {job!r}/{stream!r}")
                seen.add(key)
                merged.setdefault(job, {})[stream] = seed
    return RealizedSeeds(seeds=merged)


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, member in pairs:
        if key in value:
            raise MalformedClosure(f"seed report repeats JSON object key {key!r}")
        value[key] = member
    return value
