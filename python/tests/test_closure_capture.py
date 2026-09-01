"""The runtime artifact closure (design §4.2): discovered from the executing
interpreter, one row per file, host paths ephemeral; K7's three refusals."""

import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest

import beliefs.adapter as adapter_module
from beliefs.adapter import (
    SANDBOX_ENV,
    SANDBOX_LIB,
    SANDBOX_PATH,
    SANDBOX_PYTHON,
    SANDBOX_SITE,
    SANDBOX_VENV,
    CapturedEnvironment,
    _Closure,
    _elf_architecture,
    _elf_library_path,
    _parse_listing,
    build_argv,
    capture_closure,
    capture_environment,
    elf_interpreter,
    loader_listing,
    require_executing_environment,
)
from beliefs.errors import ClosureUnsupported, MalformedClosure, UnsafeInvocation
from beliefs.identity import v1
from beliefs.recipe import ENVIRONMENT_DOMAIN, EnvironmentManifest

# The K7 fixtures below build synthetic .so files that must be treated as
# loadable ELVES of *this* host's own architecture (ruling R4) — derived from
# the interpreter actually running the suite, never a hardcoded literal, so
# the same fixtures hold on whatever host runs these tests.
_NATIVE_CLASS, _NATIVE_DATA, _NATIVE_MACHINE = _elf_architecture(Path(os.path.realpath(sys.executable)))
_NATIVE_ENDIAN = "<" if _NATIVE_DATA == 1 else ">"
_FOREIGN_CLASS = 1 if _NATIVE_CLASS == 2 else 2
_FOREIGN_MACHINE = 183 if _NATIVE_MACHINE != 183 else 62  # EM_AARCH64 vs EM_X86_64


def _synthetic_elf(*, e_class: int = _NATIVE_CLASS, e_machine: int = _NATIVE_MACHINE) -> bytes:
    """A minimal, structurally-valid (never-executed) ET_DYN header: magic,
    class/data/version, padding to e_ident[16], then e_type and e_machine —
    exactly the 20 bytes `_is_loadable_elf`/`_elf_architecture` read."""
    return (
        b"\x7fELF"
        + bytes([e_class, _NATIVE_DATA, 1])
        + bytes(9)
        + struct.pack(f"{_NATIVE_ENDIAN}H", 3)  # ET_DYN
        + struct.pack(f"{_NATIVE_ENDIAN}H", e_machine)
    )


LOADABLE_ELF = _synthetic_elf()  # this host's own architecture — always loadable and listable


def _terminal(rows: dict[str, tuple[str, str]], path: str) -> str:
    while rows[path][0] == "symlink":
        target = rows[path][1]
        path = target if target.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(path), target))
    return path


# --- science.environment.v2 (moved here with the capture that produces it) ----
def test_the_manifest_is_per_file_under_the_v2_domain():
    manifest = EnvironmentManifest(
        artifacts=(
            ("/science/env/python/bin/python3.13", "file", "sha256:" + "dd" * 32),
            ("/science/env/python/lib/libpython3.13.so", "symlink", "libpython3.13.so.1.0"),
        )
    )
    assert ENVIRONMENT_DOMAIN == "science.environment.v2"
    assert manifest.identity() == v1.digest(
        ENVIRONMENT_DOMAIN,
        {
            "artifacts": [
                ["/science/env/python/bin/python3.13", "file", "sha256:" + "dd" * 32],
                ["/science/env/python/lib/libpython3.13.so", "symlink", "libpython3.13.so.1.0"],
            ]
        },
    )


@pytest.mark.parametrize(
    "rows",
    [
        (("python", "sha256:" + "dd" * 32),),  # the v1 pair shape
        (("science/env/x", "file", "sha256:" + "dd" * 32),),  # not absolute
        (("/science/env/../../outside", "file", "sha256:" + "dd" * 32),),  # not normalized: escapes a snapshot join
        (("/science/env//x", "file", "sha256:" + "dd" * 32),),  # empty component
        (("/science/env/./x", "file", "sha256:" + "dd" * 32),),  # dot component
        (("/science/env/x/", "file", "sha256:" + "dd" * 32),),  # trailing slash
        (("//science/env/x", "file", "sha256:" + "dd" * 32),),  # POSIX double root
        (("/science/env/x", "directory", "sha256:" + "dd" * 32),),  # kind outside the closed set
        (("/science/env/x", "file", "sha256:" + "dd" * 32), ("/science/env/x", "file", "sha256:" + "ee" * 32)),
        (("/science/env/x", "file", ""),),
    ],
)
def test_a_malformed_manifest_row_is_unspellable(rows):
    with pytest.raises(MalformedClosure):
        EnvironmentManifest(artifacts=rows)


@pytest.fixture(scope="module")
def captured() -> CapturedEnvironment:
    return capture_closure()


def test_every_row_is_a_sandbox_path_and_the_plan_covers_exactly_the_rows(captured):
    paths = {path for path, _, _ in captured.manifest.artifacts}
    assert paths == set(captured.plan)
    assert all(path.startswith("/science/env/") or path == captured.loader for path in paths)
    assert not any(str(Path.home()) in path for path in paths)


def test_the_interpreter_its_libraries_and_the_loader_are_rows(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    assert captured.interpreter.startswith(f"{SANDBOX_PYTHON}/bin/")
    assert rows[captured.interpreter][0] == "file"
    assert rows[captured.loader][0] == "file"
    assert captured.loader.startswith("/")
    assert any(path.startswith(f"{SANDBOX_LIB}/libc.so") for path in rows)
    assert any(path.startswith(f"{SANDBOX_SITE}/snakemake/") for path in rows)
    assert any(path.startswith(f"{SANDBOX_PATH}/") and path.endswith("/beliefs/adapter.py") for path in rows)


def test_the_loader_map_covers_every_loadable_elf_and_names_rows_only(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    listed = {elf for elf, _, _ in captured.loader_map}
    assert captured.interpreter in listed
    assert all(elf.startswith(f"{SANDBOX_ENV}/") and rows[elf][0] == "file" for elf in listed)
    assert all(resolved in rows for _, _, resolved in captured.loader_map)
    assert all(rows[_terminal(rows, resolved)][0] == "file" for _, _, resolved in captured.loader_map)
    assert any(soname.startswith("libc.so") for _, soname, _ in captured.loader_map)
    # ruling R6: every mapped ELF is a loader elf too, but a loader elf need
    # not be mapped — a zero-dependency ELF stays a key with an empty map,
    # never silently omitted from loader_elves.
    assert listed <= set(captured.loader_elves)
    assert all(elf.startswith(f"{SANDBOX_ENV}/") and rows[elf][0] == "file" for elf in captured.loader_elves)


def test_the_interpreter_symlink_chain_is_captured_link_by_link(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    rendered = {path for path, _, _ in captured.rendered}
    venv_python = f"{SANDBOX_VENV}/bin/python"
    if Path(sys.executable).is_symlink() and sys.prefix != sys.base_prefix:
        assert rows[venv_python][0] == "symlink" and venv_python not in rendered
        assert _terminal(rows, venv_python) == captured.interpreter
    else:
        assert venv_python in rendered and venv_python not in rows
    assert rows[captured.interpreter][0] == "file"


def test_every_symlink_row_resolves_to_a_closure_row(captured):
    rows = {path: (kind, content) for path, kind, content in captured.manifest.artifacts}
    for path, (kind, content) in rows.items():
        if kind != "symlink":
            continue
        resolved = content if content.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(path), content))
        assert resolved in rows or any(row.startswith(resolved + "/") for row in rows), (path, content)


def test_the_rendered_venv_and_pth_files_are_functions_of_the_layout(captured):
    rendered = {path: (kind, content) for path, kind, content in captured.rendered}
    assert rendered[f"{SANDBOX_VENV}/pyvenv.cfg"] == ("file", f"home = {SANDBOX_PYTHON}/bin\ninclude-system-site-packages = false\n")
    version_dir = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    assert rendered[f"{SANDBOX_VENV}/lib/{version_dir}/site-packages"] == ("symlink", SANDBOX_SITE)
    editable_pths = [
        path
        for path, (kind, content) in rendered.items()
        if path.endswith(".pth")
        and kind == "file"
        and all(line.startswith(f"{SANDBOX_PATH}/") for line in content.splitlines() if line)
    ]
    assert editable_pths
    assert not set(rendered) & {path for path, _, _ in captured.manifest.artifacts}


def test_the_manifest_is_the_executing_environment_under_v2(captured):
    assert ENVIRONMENT_DOMAIN == "science.environment.v2"
    assert capture_environment() == captured.manifest
    require_executing_environment(captured.manifest)


def test_elf_interpreter_reads_the_program_interpreter_from_the_header():
    loader = elf_interpreter(Path(os.path.realpath(sys.executable)))
    assert loader.startswith("/") and Path(loader).exists()
    with pytest.raises(ClosureUnsupported):
        elf_interpreter(Path(__file__))


def test_parse_listing_keeps_sonames_and_drops_the_vdso_and_the_loader():
    text = (
        "\tlinux-vdso.so.1 (0x00007f00)\n"
        "\tlibm.so.6 => /usr/lib/libm.so.6 (0x00007f01)\n"
        "\t/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f02)\n"
    )
    assert _parse_listing(text) == {"libm.so.6": Path("/usr/lib/libm.so.6")}
    with pytest.raises(ClosureUnsupported):
        _parse_listing("\tlibmissing.so.1 => not found\n")


def test_loader_listing_runs_the_loader_under_an_empty_environment(monkeypatch):
    seen: dict = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout="\tlibm.so.6 => /usr/lib/libm.so.6 (0x1)\n", stderr="")

    monkeypatch.setattr(adapter_module.subprocess, "run", fake_run)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/ambient")
    monkeypatch.setenv("LD_PRELOAD", "/ambient/libx.so")
    assert loader_listing("/lib64/ld.so", Path("/x")) == {"libm.so.6": Path("/usr/lib/libm.so.6")}
    assert seen["env"] == {}
    assert "--library-path" not in seen["argv"]
    assert loader_listing("/lib64/ld.so", Path("/x"), library_path=("/a", "/b")) == {
        "libm.so.6": Path("/usr/lib/libm.so.6")
    }
    assert seen["env"] == {}  # the explicit --library-path never widens into an ambient env
    assert seen["argv"] == ["/lib64/ld.so", "--library-path", "/a:/b", "--list", "/x"]


def test_elf_library_path_expands_origin_against_the_binarys_own_directory(tmp_path):
    """A synthetic ELF64 whose DT_RPATH names `$ORIGIN/../lib`: the walker
    reads it from the dynamic section directly, no loader invocation
    involved, and expands `$ORIGIN` against the file's real location."""
    elf = tmp_path / "synthetic.so"
    phoff, phentsize, phnum = 64, 56, 2
    dyn_offset = phoff + phentsize * phnum
    dyn_size = 16 * 3
    strtab_offset = dyn_offset + dyn_size
    strtab = b"\x00$ORIGIN/../lib\x00"

    header = bytearray(64)
    header[0:4] = b"\x7fELF"
    header[4], header[5], header[6] = 2, 1, 1  # ELFCLASS64, little-endian, EV_CURRENT
    struct.pack_into("<Q", header, 0x20, phoff)
    struct.pack_into("<HH", header, 0x36, phentsize, phnum)

    load_phdr = bytearray(phentsize)
    struct.pack_into("<I", load_phdr, 0, 1)  # PT_LOAD
    struct.pack_into("<Q", load_phdr, 8, 0)  # p_offset
    struct.pack_into("<Q", load_phdr, 16, 0)  # p_vaddr — identity-mapped to file offset
    struct.pack_into("<Q", load_phdr, 32, strtab_offset + len(strtab))  # p_filesz — the whole file

    dynamic_phdr = bytearray(phentsize)
    struct.pack_into("<I", dynamic_phdr, 0, 2)  # PT_DYNAMIC
    struct.pack_into("<Q", dynamic_phdr, 8, dyn_offset)
    struct.pack_into("<Q", dynamic_phdr, 16, dyn_offset)  # vaddr == offset under the identity mapping above
    struct.pack_into("<Q", dynamic_phdr, 32, dyn_size)

    dynamic = bytearray(dyn_size)
    struct.pack_into("<qQ", dynamic, 0, 5, strtab_offset)  # DT_STRTAB
    struct.pack_into("<qQ", dynamic, 16, 15, 1)  # DT_RPATH -> "$ORIGIN/../lib" (past the leading NUL)
    struct.pack_into("<qQ", dynamic, 32, 0, 0)  # DT_NULL

    elf.write_bytes(bytes(header) + bytes(load_phdr) + bytes(dynamic_phdr) + bytes(dynamic) + strtab)
    origin = str(Path(os.path.realpath(elf)).parent)
    assert _elf_library_path(elf) == (f"{origin}/../lib",)


def test_a_nonzero_loader_exit_is_closure_unsupported(monkeypatch):
    def failing_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 127, stdout="", stderr="cannot list")

    monkeypatch.setattr(adapter_module.subprocess, "run", failing_run)
    with pytest.raises(ClosureUnsupported, match="cannot list"):
        loader_listing("/lib64/ld.so", Path("/x"))


def test_a_loader_that_cannot_be_invoked_is_closure_unsupported_not_oserror(tmp_path):
    with pytest.raises(ClosureUnsupported, match="could not be invoked"):
        loader_listing(str(tmp_path / "no-such-loader"), Path("/x"))


def test_a_failing_host_read_during_the_walk_is_closure_unsupported(monkeypatch):
    def unreadable() -> CapturedEnvironment:
        raise PermissionError("synthetic: a closure file is unreadable")

    monkeypatch.setattr(adapter_module, "_walk_closure", unreadable)
    with pytest.raises(ClosureUnsupported, match="unreadable"):
        capture_closure()


# --- K7: the three refusals, over synthetic closures --------------------------
def _site(tmp_path: Path) -> tuple[_Closure, Path]:
    purelib = tmp_path / "site"
    purelib.mkdir()
    walker = _Closure()
    walker.register(purelib, SANDBOX_SITE)
    return walker, purelib


def test_k7_a_mixed_pth_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    tree = tmp_path / "tree"
    tree.mkdir()
    (purelib / "mixed.pth").write_text(f"import os\n{tree}\n")
    with pytest.raises(ClosureUnsupported, match="mixes"):
        walker.add_pth(purelib)


def test_a_pth_path_line_is_followed_under_a_canonical_ordinal_key(tmp_path):
    walker, purelib = _site(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "mod.py").write_text("X = 1\n")
    (second / "other.py").write_text("Y = 2\n")
    (purelib / "_editable.pth").write_text(f"{first}\n{second}\n")
    walker.add_pth(purelib)
    assert f"{SANDBOX_PATH}/_editable.pth/0/mod.py" in walker.rows
    assert f"{SANDBOX_PATH}/_editable.pth/1/other.py" in walker.rows
    assert walker.rendered[f"{SANDBOX_SITE}/_editable.pth"] == (
        "file",
        f"{SANDBOX_PATH}/_editable.pth/0\n{SANDBOX_PATH}/_editable.pth/1\n",
    )


def test_a_pth_path_line_that_is_not_a_directory_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "bad.pth").write_text("relative/dir\n")
    with pytest.raises(ClosureUnsupported):
        walker.add_pth(purelib)


def test_an_import_only_pth_names_a_module_that_must_be_a_closure_member(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "_shim.pth").write_text("import _shim; _shim.install()\n")
    with pytest.raises(ClosureUnsupported, match="not a closure member"):
        walker.add_pth(purelib)
    (purelib / "_shim.py").write_text("def install(): pass\n")
    walker.add_pth(purelib)
    assert walker.rows[f"{SANDBOX_SITE}/_shim.pth"][0] == "file"
    assert walker.rows[f"{SANDBOX_SITE}/_shim.py"][0] == "file"


def test_k7_a_symlink_escaping_the_closure_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "escape").symlink_to("../../outside")
    with pytest.raises(ClosureUnsupported, match="escapes"):
        walker.add(purelib / "escape")
    (purelib / "absolute").symlink_to("/etc/hostname")
    with pytest.raises(ClosureUnsupported, match="escapes"):
        walker.add(purelib / "absolute")


def test_a_symlink_row_captures_its_target_and_a_dangling_link_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "real.so.1").write_bytes(b"x")
    (purelib / "real.so").symlink_to("real.so.1")
    walker.add(purelib / "real.so")
    assert walker.rows[f"{SANDBOX_SITE}/real.so"] == ("symlink", "real.so.1")
    assert walker.rows[f"{SANDBOX_SITE}/real.so.1"][0] == "file"
    walker.check_links()
    (purelib / "dangling").symlink_to("missing")
    with pytest.raises(ClosureUnsupported, match="names nothing"):
        walker.add(purelib / "dangling")


def test_check_links_refuses_a_symlink_row_whose_target_is_no_row(tmp_path):
    walker, _ = _site(tmp_path)
    walker.rows[f"{SANDBOX_SITE}/orphan"] = ("symlink", "../elsewhere")
    with pytest.raises(ClosureUnsupported, match="not a closure row"):
        walker.check_links()


def test_a_relative_link_into_another_root_is_rewritten_to_its_sandbox_path(tmp_path):
    walker, purelib = _site(tmp_path)
    base = tmp_path / "base"
    (base / "lib").mkdir(parents=True)
    (base / "lib" / "libq.so.1").write_bytes(b"q")
    walker.register(base, SANDBOX_PYTHON)
    (purelib / "libq.so").symlink_to("../base/lib/libq.so.1")
    walker.add(purelib / "libq.so")
    assert walker.rows[f"{SANDBOX_SITE}/libq.so"] == ("symlink", f"{SANDBOX_PYTHON}/lib/libq.so.1")
    assert walker.rows[f"{SANDBOX_PYTHON}/lib/libq.so.1"][0] == "file"
    walker.check_links()


def test_a_link_to_a_directory_inside_the_closure_is_a_symlink_row(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "pkg").mkdir()
    (purelib / "pkg" / "__init__.py").write_text("")
    (purelib / "alias").symlink_to("pkg")
    walker.add(purelib / "pkg" / "__init__.py")
    walker.add(purelib / "alias")
    assert walker.rows[f"{SANDBOX_SITE}/alias"] == ("symlink", "pkg")
    walker.check_links()


def test_add_chain_captures_every_link_and_returns_the_terminal(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "python3.13").write_bytes(b"bin")
    (purelib / "python3").symlink_to("python3.13")
    (purelib / "python").symlink_to("python3")
    assert walker.add_chain(purelib / "python") == f"{SANDBOX_SITE}/python3.13"
    assert walker.rows[f"{SANDBOX_SITE}/python"] == ("symlink", "python3")
    assert walker.rows[f"{SANDBOX_SITE}/python3"] == ("symlink", "python3.13")
    assert walker.rows[f"{SANDBOX_SITE}/python3.13"][0] == "file"


def test_k7_a_soname_collision_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "libz.so.1").write_bytes(b"a")
    (b / "libz.so.1").write_bytes(b"b")
    (purelib / "one.so").write_bytes(LOADABLE_ELF)
    (purelib / "two.so").write_bytes(LOADABLE_ELF)
    listings = {"one.so": {"libz.so.1": a / "libz.so.1"}, "two.so": {"libz.so.1": b / "libz.so.1"}}
    walker.add(purelib / "one.so")
    walker.add(purelib / "two.so")
    with pytest.raises(ClosureUnsupported, match="SONAME"):
        walker.add_native(listing=lambda elf: listings[elf.name])
    single = _Closure()
    single.register(purelib, SANDBOX_SITE)
    single.add(purelib / "one.so")
    single.add_native(listing=lambda elf: listings[elf.name])
    assert single.rows[f"{SANDBOX_LIB}/libz.so.1"][0] == "file"
    assert single.loader_map == [(f"{SANDBOX_SITE}/one.so", "libz.so.1", f"{SANDBOX_LIB}/libz.so.1")]


def test_k7_a_soname_collision_between_two_registered_roots_is_refused(tmp_path):
    walker, purelib = _site(tmp_path)
    base = tmp_path / "base"
    (base / "lib").mkdir(parents=True)
    walker.register(base, SANDBOX_PYTHON)
    (base / "lib" / "libz.so.1").write_bytes(b"base")
    (purelib / "libz.so.1").write_bytes(b"site")
    (purelib / "one.so").write_bytes(LOADABLE_ELF)
    (purelib / "two.so").write_bytes(LOADABLE_ELF)
    listings = {"one.so": {"libz.so.1": base / "lib" / "libz.so.1"}, "two.so": {"libz.so.1": purelib / "libz.so.1"}}
    walker.add(purelib / "one.so")
    walker.add(purelib / "two.so")
    with pytest.raises(ClosureUnsupported, match="SONAME"):
        walker.add_native(listing=lambda elf: listings[elf.name])


def test_two_names_for_one_artifact_are_not_a_soname_collision(tmp_path):
    walker, purelib = _site(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "libz.so.1.3").write_bytes(b"z")
    (outside / "libz.so.1").symlink_to("libz.so.1.3")
    (purelib / "one.so").write_bytes(LOADABLE_ELF)
    (purelib / "two.so").write_bytes(LOADABLE_ELF)
    listings = {"one.so": {"libz.so.1": outside / "libz.so.1"}, "two.so": {"libz.so.1": outside / "libz.so.1.3"}}
    walker.add(purelib / "one.so")
    walker.add(purelib / "two.so")
    walker.add_native(listing=lambda elf: listings[elf.name])
    assert walker.rows[f"{SANDBOX_LIB}/libz.so.1"][0] == "file"


def test_add_native_closes_over_the_libraries_it_adds_and_maps_in_root_targets_to_their_rows(tmp_path):
    walker, purelib = _site(tmp_path)
    (purelib / "ext.so").write_bytes(LOADABLE_ELF)
    (purelib / "libinner.so.1").write_bytes(LOADABLE_ELF)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "libouter.so.1").write_bytes(LOADABLE_ELF)
    listings = {
        "ext.so": {"libinner.so.1": purelib / "libinner.so.1"},
        "libinner.so.1": {"libouter.so.1": outside / "libouter.so.1"},
        "libouter.so.1": {},
    }
    walker.add(purelib / "ext.so")
    walker.add_native(listing=lambda elf: listings[elf.name])
    assert sorted(walker.loader_map) == [
        (f"{SANDBOX_SITE}/ext.so", "libinner.so.1", f"{SANDBOX_SITE}/libinner.so.1"),
        (f"{SANDBOX_SITE}/libinner.so.1", "libouter.so.1", f"{SANDBOX_LIB}/libouter.so.1"),
    ]
    assert walker.rows[f"{SANDBOX_LIB}/libouter.so.1"][0] == "file"
    # ruling R6: libouter.so.1 resolves zero dependencies of its own but is
    # still a loadable ELF under the environment root — a key in
    # loader_elves, even though it never gains a loader_map row.
    assert walker.loader_elves == sorted([f"{SANDBOX_SITE}/ext.so", f"{SANDBOX_SITE}/libinner.so.1", f"{SANDBOX_LIB}/libouter.so.1"])


def test_r4_a_foreign_class_or_machine_elf_is_a_row_but_never_listed_or_mapped(tmp_path):
    """Ruling R4: an ELF joins the loader listing and map only when its
    class, data encoding and machine equal the capturing interpreter's own —
    a foreign-architecture file stays an ordinary digest-verified row."""
    walker, purelib = _site(tmp_path)
    (purelib / "wrong-class.so").write_bytes(_synthetic_elf(e_class=_FOREIGN_CLASS))
    (purelib / "wrong-machine.so").write_bytes(_synthetic_elf(e_machine=_FOREIGN_MACHINE))
    walker.add(purelib / "wrong-class.so")
    walker.add(purelib / "wrong-machine.so")

    def never(elf: Path) -> dict[str, Path]:
        raise AssertionError(f"{elf} is off-architecture and must never be listed")

    walker.add_native(listing=never)
    assert walker.rows[f"{SANDBOX_SITE}/wrong-class.so"][0] == "file"
    assert walker.rows[f"{SANDBOX_SITE}/wrong-machine.so"][0] == "file"
    assert walker.loader_map == []
    assert walker.loader_elves == []


# --- the policy-neutral argv --------------------------------------------------
def test_build_argv_is_policy_neutral_and_the_minimal_spelling_is_unchanged():
    minimal = build_argv(
        interpreter="/host/python",
        snakefile="/host/scratch/bundle/code/workflow/Snakefile",
        directory="/host/scratch",
        targets=("outputs/result.txt",),
        config={"alpha": "0.05"},
        log_handler="/host/trace/handler.py",
        cores=1,
        in_process_jobs=False,
    )
    assert minimal == (
        "/host/python", "-m", "snakemake",
        "--snakefile", "/host/scratch/bundle/code/workflow/Snakefile",
        "--cores", "1", "--directory", "/host/scratch", "--nolock",
        "--log-handler-script", "/host/trace/handler.py",
        "--config", "alpha=0.05", "--", "outputs/result.txt",
    )
    confined = build_argv(
        interpreter="/science/env/venv/bin/python",
        snakefile="/science/bundle/code/workflow/Snakefile",
        directory="/science/out",
        targets=("outputs/result.txt",),
        config={},
        log_handler="/science/out/.trace/handler.py",
        cores=2,
        in_process_jobs=True,
    )
    assert confined[:3] == ("/science/env/venv/bin/python", "-m", "snakemake")
    assert "--force-use-threads" in confined and confined.index("--force-use-threads") == confined.index("--nolock") + 1
    assert not any(part.startswith("/host") for part in confined)
    with pytest.raises(UnsafeInvocation):
        build_argv(interpreter="/p", snakefile="/s", directory="/d", targets=("--all",), config={}, log_handler="/h", cores=1, in_process_jobs=False)
