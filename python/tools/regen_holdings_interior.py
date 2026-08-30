"""Regenerate beliefs/holdings/qualify.py from the shared holdings shape."""

from pathlib import Path

HEADER = (
    b"# GENERATED from beliefs/intents/holdings.py by tools/regen_holdings_interior.py.\n"
    b"# Edit the source and regenerate; hand edits here are discarded.\n"
)


def main() -> None:
    src = Path(__file__).resolve().parents[1] / "src" / "beliefs"
    shared = (src / "intents" / "holdings.py").read_bytes()
    (src / "holdings" / "qualify.py").write_bytes(HEADER + shared)


if __name__ == "__main__":
    main()
