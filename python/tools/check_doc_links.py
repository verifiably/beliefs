"""Check every relative Markdown link, and its #anchor, in the repository's documents.

A link to a file that is gone, or to a heading that was renamed, still renders as a link;
only this check tells. External (scheme-qualified) links are not followed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_GLOBS = ("README.md", "AGENTS.md", "docs/*.md", "python/README.md", "ts/README.md")

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^ {0,3}(```|~~~)")
EXPLICIT_ANCHOR = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
INLINE_CODE = re.compile(r"`[^`]*`")


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every line outside a fenced code block."""
    lines = []
    fence = None
    for number, line in enumerate(text.splitlines(), start=1):
        marker = FENCE.match(line)
        if marker:
            fence = None if fence == marker.group(1) else (fence or marker.group(1))
            continue
        if fence is None:
            lines.append((number, line))
    return lines


def anchors(text: str) -> set[str]:
    """The anchors GitHub mints for a document: heading slugs and explicit ids.

    A slug is the heading text lowercased, minus everything that is not a word
    character, space or hyphen, with each space turned into a hyphen. A repeated
    slug gets `-1`, `-2`, ... appended in document order.
    """
    found: set[str] = set()
    seen: dict[str, int] = {}
    for _, line in _prose_lines(text):
        found.update(EXPLICIT_ANCHOR.findall(line))
        heading = HEADING.match(line)
        if not heading:
            continue
        title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading.group(1))
        title = re.sub(r"<[^>]+>", "", title)
        slug = re.sub(r"[^\w\s-]", "", title.replace("`", "").lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def check_file(path: Path, root: Path) -> list[str]:
    errors = []
    text = path.read_text(encoding="utf-8")
    shown = path.relative_to(root)
    for number, line in _prose_lines(text):
        for target in LINK.findall(INLINE_CODE.sub("", line)):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            resolved = path if not parsed.path else (path.parent / unquote(parsed.path))
            if not resolved.exists():
                errors.append(f"{shown}:{number}: missing link target: {target}")
            elif (
                parsed.fragment
                and resolved.suffix == ".md"
                and unquote(parsed.fragment) not in anchors(resolved.read_text(encoding="utf-8"))
            ):
                errors.append(f"{shown}:{number}: the file exists but the anchor does not: {target}")
    return errors


def documents(root: Path) -> list[Path]:
    return sorted({path for pattern in DOCUMENT_GLOBS for path in root.glob(pattern) if path.is_file()})


def check(root: Path) -> list[str]:
    return [error for path in documents(root) for error in check_file(path, root)]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]).resolve() if args else REPO_ROOT
    errors = check(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
