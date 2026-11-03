"""The document link check: files and heading anchors, GitHub slug rules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from conftest import REPO_ROOT

_SPEC = importlib.util.spec_from_file_location(
    "check_doc_links", Path(__file__).parents[1] / "tools" / "check_doc_links.py"
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = checker
_SPEC.loader.exec_module(checker)


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_good_file_and_anchor_links_pass(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "README.md": "# Top\n[a](docs/a.md) [b](docs/a.md#the-part-two) [self](#top)\n",
            "docs/a.md": "# A\n## The part two\n",
        },
    )
    assert checker.check(root) == []


def test_missing_file_is_reported_with_file_and_line(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"README.md": "# Top\n\n[gone](docs/gone.md)\n"})
    assert checker.check(root) == ["README.md:3: missing link target: docs/gone.md"]


def test_broken_anchor_is_reported(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"README.md": "[x](docs/a.md#nope)\n", "docs/a.md": "# A\n"})
    errors = checker.check(root)
    assert len(errors) == 1 and errors[0].startswith("README.md:1:") and "docs/a.md#nope" in errors[0]


def test_duplicate_heading_suffix_resolves(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "README.md": "[one](docs/a.md#same) [two](docs/a.md#same-1) [three](docs/a.md#same-2)\n",
            "docs/a.md": "# A\n## Same\n## Same\n",
        },
    )
    errors = checker.check(root)
    assert len(errors) == 1 and "#same-2" in errors[0]


def test_explicit_anchor_and_punctuated_heading_resolve(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "README.md": "[x](docs/a.md#custom) [y](docs/a.md#6-m----the-calculus)\n",
            "docs/a.md": '# A\n<a id="custom"></a>\n## 6. M -- the `calculus`\n',
        },
    )
    assert checker.check(root) == []


def test_external_urls_fences_and_inline_code_are_ignored(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {"README.md": "[w](https://example.test/x#y) `[c](gone.md)`\n```\n[f](gone.md)\n# not-a-heading\n```\n"},
    )
    assert checker.check(root) == []


def test_main_exits_non_zero_on_a_failure(tmp_path: Path, capsys) -> None:
    root = _tree(tmp_path, {"README.md": "[gone](gone.md)\n"})
    assert checker.main([str(root)]) == 1
    assert "README.md:1" in capsys.readouterr().err


def test_the_real_documents_pass() -> None:
    assert checker.check(REPO_ROOT) == []
