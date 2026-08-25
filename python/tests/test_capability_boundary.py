"""S8's static claim, and the `atoms`-import rule beside it.

**Two boundaries, two checks, neither standing in for the other.** S8 is about
who holds a **mutable corpus handle**: the write API is its only holder, every
other module receives a `ReadView`, and constructing or receiving a `Corpus`
outside `science.corpus` is a static violation. The `atoms`-import confinement
is about engine capability and is architecture, not an S8 arm — it is asserted
here because it belongs beside S8, not inside it.

**Why a static check and not a scan of writers.** "Discover the writers and
check them" is a roster wearing a predicate's clothes: a new writer reaching the
filesystem through an unrecognized primitive is simply not discovered, and the
scan reports clean. What is checkable is who holds the handle. What it does
**not** cover — a module writing bytes to a corpus path with a raw filesystem
call — is stated in §4.2.1 and pinned by the acceptance negative, not by this.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from typing import get_args

import pytest

import science

PACKAGE = Path(science.__file__).resolve().parent
"""The package as **imported**, not as checked out.

The sabotage harness runs a check against a copy of the package on
`PYTHONPATH`; a static check that read the working tree instead would inspect
the unmutated source and score every sabotage as survived — which is vacuity
wearing the costume of a static assertion.
"""
WRITE_API = "corpus.py"
COMPOSITION_ROOT = "root.py"
WORLD_PACKAGE = "world"
"""The world layer, which now reaches the engine's chain and must not do so
directly. `World` receives one `(genesis_digest, tip)` callback and the log
seam receives Science-owned view types; `root.py` implements both with the
engine's own commands, and no engine type crosses the package boundary."""

VIEW_MODULE = "world/logmodel.py"
"""The Science-typed chain views. Stdlib imports only, by rule: it is the
vocabulary the seam speaks *instead of* the engine's, so a dependency of its
own would be a second place engine shape could enter."""

SEAM_MODULE = "world/verify.py"
HOLDINGS_SEAM_MODULE = "holdings/seam.py"

ENGINE_COMMANDS = (
    "inspect_chain",
    "inspect_chain_detached",
    "capture_states",
    "state_from_json",
    "read_chain",
    "read_path_state",
    "register_root",
    "run_transaction",
    "replicate_root",
    "fork_root",
    "read_pending_fork_operation",
    "resume_fork_root",
    "grant_read_serviceability",
    "read_lifecycle_state",
    "migrate_root_to_lifecycle_v3",
)
"""The engine entry points Science calls by name, the log seam's four included.

`append_intent` is deliberately absent: `science.corpus` declares a port method
of that name, so the bare name is not evidence of an engine call. Every name
here is one only `root.py` may write — the confinement asserted over imports
above, restated over *use* so a module reaching one through an alias or a
re-export is caught too."""


def modules() -> list[Path]:
    return sorted(path for path in PACKAGE.rglob("*.py"))


def world_modules() -> list[Path]:
    return sorted(path for path in (PACKAGE / WORLD_PACKAGE).rglob("*.py"))


def relative(path: Path) -> str:
    return path.relative_to(PACKAGE).as_posix()


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def names_of(tree: ast.Module) -> set[str]:
    """Every bare name, attribute tail, and imported source name.

    Import sources count deliberately, on both sides of the confinement: an
    aliased import IS a naming — `from atoms... import replicate_root as _x`
    reaches the command exactly as a bare use does — so the composition
    root's roster is satisfied by its aliased callback imports, and a module
    elsewhere cannot smuggle a command in behind an alias.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            found.update(alias.name for alias in node.names)
    return found


def defined_names(tree: ast.Module) -> set[str]:
    """Every name this module *binds* as a class or a function.

    `names_of` reads uses, and a second summary model is a definition before it
    is ever used. A ban that read uses alone would pass over the class itself.
    """
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    }


def imported_modules(tree: ast.Module) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.add(node.module)
    return found


def composition_root_imports(tree: ast.Module) -> list[str]:
    """Every statement that binds `science.root`, in all four spellings.

    `imported_modules` records an `ImportFrom`'s *module*, so `from science
    import root` shows up there as plain `"science"` — a module-name predicate
    reading that set would miss the shortest evasion there is. The submodule
    can be bound four ways and each one is checked here: `import
    science.root`, `from science.root import …`, `from science import root`,
    and the package-relative `from .. import root` a module inside the package
    can write. The last two are recognized by the *alias* rather than the
    module, which is exactly what a set of module names cannot express.
    """
    offending: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offending.extend(
                alias.name
                for alias in node.names
                if alias.name == "science.root" or alias.name.startswith("science.root.")
            )
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        statement = f"from {'.' * node.level}{module}"
        # Inside the package the leading dots stand in for `science`, so a
        # relative import's module part is measured against `root` and an
        # absolute one's against `science.root`; `package` is what each
        # spelling calls the package whose `root` submodule an alias may name.
        submodule = "root" if node.level else "science.root"
        package = "" if node.level else "science"
        if module == submodule or module.startswith(submodule + "."):
            offending.append(statement)
        elif module == package:
            offending.extend(
                f"{statement} import {alias.name}" for alias in node.names if alias.name == "root"
            )
    return offending


class TestS8TheMutableCorpusHandleHasOneHolder:
    @pytest.mark.parametrize("module", [path for path in modules() if relative(path) != WRITE_API], ids=relative)
    def test_no_module_outside_the_write_api_names_the_mutable_corpus(self, module):
        tree = parsed(module)
        assert not any(
            imported == "nodes.core.corpus" for imported in imported_modules(tree)
        ), f"{relative(module)} imports the mutable corpus"
        assert "Corpus" not in names_of(tree), f"{relative(module)} names Corpus"

    def test_the_write_api_is_the_one_module_that_does(self):
        tree = parsed(PACKAGE / WRITE_API)
        assert "nodes.core.corpus" in imported_modules(tree)
        assert "Corpus" in names_of(tree)

    def test_the_check_would_see_a_second_holder(self, tmp_path):
        # Otherwise the arm asserts that the tree happens to be quiet rather
        # than that the check can speak: a module that constructs one is what it
        # has to catch.
        offender = tmp_path / "writer.py"
        offender.write_text(
            "from nodes.core.corpus import Corpus\n\n\ndef build(root):\n    return Corpus(root)\n",
            encoding="utf-8",
        )
        tree = parsed(offender)
        assert "nodes.core.corpus" in imported_modules(tree)
        assert "Corpus" in names_of(tree)

    def test_a_read_view_is_what_every_other_module_receives(self):
        # The positive half: the facade is exported, and the handle is not.
        from science.corpus import ReadView

        assert not hasattr(ReadView, "add")
        assert not any(name.startswith(("add", "delete")) for name in vars(ReadView))


class TestTheCompositionRootIsTheOneAtomsImporter:
    @pytest.mark.parametrize(
        "module", [path for path in modules() if relative(path) != COMPOSITION_ROOT], ids=relative
    )
    def test_no_module_outside_the_composition_root_imports_atoms(self, module):
        offending = [
            imported
            for imported in imported_modules(parsed(module))
            if imported == "atoms" or imported.startswith("atoms.")
        ]
        assert offending == [], f"{relative(module)} imports {offending}"

    def test_the_composition_root_does_import_atoms(self):
        imported = imported_modules(parsed(PACKAGE / COMPOSITION_ROOT))
        assert any(name == "atoms" or name.startswith("atoms.") for name in imported)

    @pytest.mark.parametrize(
        "module", [path for path in modules() if relative(path) != COMPOSITION_ROOT], ids=relative
    )
    def test_no_module_outside_the_composition_root_names_an_engine_command(self, module):
        named = names_of(parsed(module)) & set(ENGINE_COMMANDS)
        assert named == set(), f"{relative(module)} names {sorted(named)}"

    def test_the_composition_root_names_every_engine_command(self):
        # The roster is checked in both directions: a command that quietly left
        # `root.py` would otherwise leave a dead ban behind, and the log seam's
        # four new names are the ones this arm exists to keep honest.
        named = names_of(parsed(PACKAGE / COMPOSITION_ROOT))
        missing = [command for command in ENGINE_COMMANDS if command not in named]
        assert missing == []


class TestTheWorldPackageHoldsNoEngineCapability:
    """The same rule, stated over the package that most nearly needs to break it.

    The world layer is where recovery-completing chain reads enter Science: a
    build's anchors are chain digests, preflight completes recovery before it
    inspects a single world file, and the log seam hands verification a whole
    chain. It gets there through injected callables and never through `atoms`
    — the chain arrives already re-typed into `science.world.logmodel`'s own
    unions, and the only engine-derived *values* above the composition root
    are chain digests and path-state fingerprints the layer holds opaquely and
    compares only by equality. Asserting it here, over `science/world/` by
    name, means a future module in that package cannot pass by being one of
    many.
    """

    def test_the_world_package_is_not_empty(self):
        # Otherwise a rename to a package this test cannot find would score as
        # a clean sweep of nothing.
        assert len(world_modules()) >= 4

    @pytest.mark.parametrize("module", world_modules(), ids=relative)
    def test_no_world_module_imports_atoms(self, module):
        offending = [
            imported
            for imported in imported_modules(parsed(module))
            if imported == "atoms" or imported.startswith("atoms.")
        ]
        assert offending == [], f"{relative(module)} imports {offending}"

    @pytest.mark.parametrize("module", world_modules(), ids=relative)
    def test_no_world_module_imports_the_composition_root(self, module):
        """The second half of the same confinement.

        Banning `atoms` alone would leave the world layer one hop away from
        every engine type: `science.root` holds them all, so importing it is
        importing the engine with extra steps. The seam types the world layer
        does hold are handed to it as values, never fetched from the module
        that builds them.

        Checked over statements rather than over module names, because `from
        science import root` binds the module while naming only the package.
        """
        offending = composition_root_imports(parsed(module))
        assert offending == [], f"{relative(module)} imports {offending}"

    @pytest.mark.parametrize("module", world_modules(), ids=relative)
    def test_no_world_module_names_the_engines_chain_reader(self, module):
        assert "read_chain" not in names_of(parsed(module)), f"{relative(module)} names read_chain"

    def test_the_chain_view_the_world_package_names_is_sciences_own(self):
        """`ChainView` is now a name in both vocabularies, so the bare name is
        no longer the check — the object is.

        `science.world.logmodel` mints its own closed union under that name
        because the seam speaks Science's vocabulary; the engine's `ChainView`
        is a different class, reachable only through an `atoms` import the arms
        above forbid.
        """
        from atoms.coordinator.commands import ChainView as EngineChainView

        from science.world.logmodel import ChainView as ScienceChainView

        assert ScienceChainView is not EngineChainView

    def test_the_view_module_imports_only_the_standard_library(self):
        imported = imported_modules(parsed(PACKAGE / VIEW_MODULE))
        foreign = sorted(name for name in imported if name.split(".")[0] not in sys.stdlib_module_names)
        assert foreign == [], f"{VIEW_MODULE} imports {foreign}"

    def test_the_seam_module_imports_neither_the_engine_nor_the_composition_root(self):
        imported = imported_modules(parsed(PACKAGE / SEAM_MODULE))
        assert not any(name == "atoms" or name.startswith("atoms.") for name in imported)
        assert composition_root_imports(parsed(PACKAGE / SEAM_MODULE)) == []

    def test_the_holdings_seam_module_imports_only_the_standard_library(self):
        imported = imported_modules(parsed(PACKAGE / HOLDINGS_SEAM_MODULE))
        foreign = sorted(name for name in imported if name.split(".")[0] not in sys.stdlib_module_names)
        assert foreign == [], f"{HOLDINGS_SEAM_MODULE} imports {foreign}"

    def test_the_check_would_see_a_world_module_reading_the_chain(self, tmp_path):
        offender = tmp_path / "epoch.py"
        offender.write_text(
            "from atoms.coordinator.commands import read_chain\n"
            "from science.root import _log_seam\n\n\n"
            "def head(root, backend, storage):\n"
            "    return read_chain(backend, str(root), str(root), storage)\n",
            encoding="utf-8",
        )
        tree = parsed(offender)
        assert any(name.startswith("atoms") for name in imported_modules(tree))
        assert composition_root_imports(tree) == ["from science.root"]
        assert "read_chain" in names_of(tree)

    @pytest.mark.parametrize(
        "statement",
        [
            "import science.root",
            "import science.root as science_root",
            "from science.root import _log_seam",
            # The evasion the module-name predicate this replaced could not
            # see: `imported_modules` records only `science` for this form.
            "from science import root",
            "from science import root as science_root",
            "from .. import root",
            "from ..root import _log_seam",
        ],
    )
    def test_the_check_would_see_every_spelling_of_the_composition_root_import(self, tmp_path, statement):
        offender = tmp_path / "epoch.py"
        offender.write_text(f"{statement}\n", encoding="utf-8")

        assert composition_root_imports(parsed(offender)) != []

    @pytest.mark.parametrize(
        "statement",
        [
            "import science",
            "from science import stored",
            "from science.world.anchors import LogHeadRecord",
            "from science.corpus import ReadView",
            "from .anchors import LogHeadRecord",
            "from .. import corpus",
            "from ..corpus import ReadView",
        ],
    )
    def test_the_check_does_not_see_the_imports_the_world_layer_may_write(self, tmp_path, statement):
        # The other half: a ban that also caught `from science import stored`
        # would be an assertion nobody could satisfy, and would be deleted
        # rather than obeyed.
        offender = tmp_path / "epoch.py"
        offender.write_text(f"{statement}\n", encoding="utf-8")

        assert composition_root_imports(parsed(offender)) == []

    def test_the_check_would_see_a_view_module_reaching_past_the_standard_library(self, tmp_path):
        offender = tmp_path / "logmodel.py"
        offender.write_text("from atoms.core.fingerprint import PathState\n", encoding="utf-8")
        imported = imported_modules(parsed(offender))
        assert [name for name in imported if name.split(".")[0] not in sys.stdlib_module_names] == [
            "atoms.core.fingerprint"
        ]


# --- cut 8's declarations over the composition surface ----------------------

MUTATING_ENGINE_COMMANDS = ("register_root", "append_intent", "run_transaction")
"""The three engine entry points that change a root. Everything else in
`ENGINE_COMMANDS` reads."""

ENGINE_CALL_SITES = {
    "run_transaction": ["_mapped_submit.submit"],
    "register_root": [
        "init_corpus_root",
        "init_world_root",
        "init_store_root",
        "init_store_root",
    ],
    "append_intent": ["DurableOperationPort.append_intent"],
}
"""Where each mutating command is called, by enclosing definition.

One `run_transaction` site, the shared mapped submission used by the durable
executor and store commands — so **every registered-surface mutation flows
through it**. `register_root` runs
only in the two initializers and `append_intent` only in the operation port:
genesis registration and intent append are protocol entries, not application
mutations, which is why they are named separately rather than counted as a
second mutation path. `init_store_root` carries two register sites by
design: the interrupted-initialization retry and the fresh mint are the
same recorded operation approached from its two durable states.
"""

PORT_METHOD_NAMES = frozenset({"append_intent"})
"""`science.corpus` declares an `OperationPort` method of this name, so the bare
name is not evidence of an engine call and the name ban above cannot cover it —
exactly the carve-out `ENGINE_COMMANDS` already records. The *call sites* are
still counted: a port method is an `Attribute`, and the composition root's own
call is the only bare `Name`.
"""

BYTE_MUTATION_PRIMITIVES = (
    "write_bytes",
    "write_text",
    "unlink",
    "rmdir",
    "rmtree",
    "rename",
    "symlink_to",
    "chmod",
    "touch",
    "makedirs",
    "remove",
    "copy",
    "copy2",
    "copytree",
    "move",
)
"""Every way a Python module reaches a byte of a file without the engine.

`mkdir` is deliberately absent: creating the directory a root will occupy is
what `init_corpus_root` and `init_world_root` do *before* registering it, and
banning it would ban initialization rather than unregistered mutation.
`replace` is absent because the name is `str.replace` and
`dataclasses.replace` far more often than it is `Path.replace`, and a ban
nobody can satisfy is a ban that gets deleted.
"""

RAW_WRITE_ALLOWLIST = {
    # The export bundle: a directory this module mints for a consumer, outside
    # every corpus and world root and registered by nothing.
    "adapter.py": {"copy2"},
    # The execution sandbox: an inputs tree and the log-handler script, minted
    # per run under a scratch directory the substrate owns.
    "boundary.py": {"copy2", "write_text"},
}
"""The two surfaces Science writes with its own hands, both stated. Neither is
a registered surface; a third entry appearing here would be a claim to weigh,
which is why the allowlist is compared for equality and never for containment.
"""

STATE_VOCABULARY = (
    "PathState",
    "PathStateJSON",
    "FileState",
    "AbsentState",
    "DirectoryState",
    "SymlinkState",
    "state_from_json",
    "state_to_json",
    "capture_states",
    "read_path_state",
)
"""L12's one state vocabulary. Every member is the engine's; Science names them
in the composition root and nowhere else, and mints none of its own."""


def call_sites(tree: ast.Module, command: str) -> list[str]:
    """Every call to `command`, named by the definition that encloses it."""
    found: list[str] = []

    def walk(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                walk(child, (*scope, child.name))
                continue
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == command
            ):
                found.append(".".join(scope))
            walk(child, scope)

    walk(tree, ())
    return found


def test_no_cooperative_mutation_path_skips_registration():
    """L1u1. The unspellability arm, over the composition surface.

    Three facts, and no cooperative mutation path survives all three. First,
    `science.root` is the only `atoms` importer, so no other module holds
    engine capability at all. Second, the three mutating engine commands are
    named only there, and each is called from exactly the definitions the
    composition allows: **one** `run_transaction` site, the shared mapped
    submission, so every registered-surface mutation flows through it; the two
    initializers' `register_root` and the operation port's `append_intent` are
    protocol entries rather than application mutations. Third, no module in
    Science reaches a byte of a file itself outside the two stated non-registered
    surfaces — so there is no path that mutates a registered root *without* the
    engine, and no engine mutation that is not a registration.

    What this does not cover is stated rather than implied: a *new* module
    reaching the filesystem through a primitive absent from
    `BYTE_MUTATION_PRIMITIVES`. The kill-at-stage arms of L1 are deferred to
    atoms's own certification (cut 8 §3.1, §8.1).
    """
    for module in modules():
        offending = [
            imported
            for imported in imported_modules(parsed(module))
            if (imported == "atoms" or imported.startswith("atoms.")) and relative(module) != COMPOSITION_ROOT
        ]
        assert offending == [], f"{relative(module)} imports {offending}"

    composition_root = parsed(PACKAGE / COMPOSITION_ROOT)
    for command in MUTATING_ENGINE_COMMANDS:
        if command not in PORT_METHOD_NAMES:
            elsewhere = [
                relative(module)
                for module in modules()
                if relative(module) != COMPOSITION_ROOT and command in names_of(parsed(module))
            ]
            assert elsewhere == [], f"{command} is named outside the composition root by {elsewhere}"
        assert sorted(call_sites(composition_root, command)) == sorted(ENGINE_CALL_SITES[command]), command

    for module in modules():
        named = names_of(parsed(module)) & set(BYTE_MUTATION_PRIMITIVES)
        assert named == RAW_WRITE_ALLOWLIST.get(relative(module), set()), (
            f"{relative(module)} writes bytes itself: {sorted(named)}"
        )
    assert set(RAW_WRITE_ALLOWLIST) == {"adapter.py", "boundary.py"}


def test_science_fingerprints_only_through_the_engine_read_commands():
    """L12u2. No second summary model: Science fingerprints exclusively through
    the engine's capture and single-path read commands, asserted over the package surface.

    The state vocabulary is the engine's own union, named in the composition
    root and nowhere else; the two commands that read disk state each have
    exactly one call site; and the one place Science *constructs* a
    state builds the engine's `FileState` over **caller-supplied bytes**, never
    over a path, so it is a projection of a planned write and not a second way
    to observe a root.
    """
    composition_root = parsed(PACKAGE / COMPOSITION_ROOT)
    for name in STATE_VOCABULARY:
        elsewhere = [
            relative(module)
            for module in modules()
            if relative(module) != COMPOSITION_ROOT
            and name in names_of(parsed(module)) | defined_names(parsed(module))
        ]
        assert elsewhere == [], f"{name} is named or defined outside the composition root by {elsewhere}"
    # The composition root does name the members it uses — the ban above would
    # otherwise pass over a vocabulary nobody speaks. The one encoder call
    # mechanically carries validated chain facts for the holdings projection.
    named = set(STATE_VOCABULARY) & names_of(composition_root)
    assert named == {
        "AbsentState",
        "DirectoryState",
        "FileState",
        "PathState",
        "PathStateJSON",
        "SymlinkState",
        "capture_states",
        "read_path_state",
        "state_from_json",
        "state_to_json",
    }
    assert call_sites(composition_root, "capture_states") == ["_capture"]
    assert call_sites(composition_root, "read_path_state") == ["_store_read_path"]
    assert call_sites(composition_root, "state_to_json") == ["_state_facts"]

    # Science mints no state class of its own: the vocabulary is exactly the
    # engine's union, and every member Science names is that class.
    from atoms.core.fingerprint import AbsentState, DirectoryState, FileState, PathState, SymlinkState

    import science.root as composition

    assert set(get_args(PathState)) == {AbsentState, DirectoryState, FileState, SymlinkState}
    assert composition.FileState is FileState

    # ...and the one construction is over bytes, never over a path.
    signature = inspect.signature(composition._file_state)
    assert [(name, parameter.annotation) for name, parameter in signature.parameters.items()] == [
        ("content", "bytes")
    ]
    assert signature.return_annotation == "FileState"
