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
import sys
from pathlib import Path

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

ENGINE_COMMANDS = (
    "inspect_chain",
    "inspect_chain_detached",
    "capture_states",
    "state_from_json",
    "read_chain",
    "register_root",
    "run_transaction",
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
    """Every bare name and attribute tail the module mentions."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
    return found


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
