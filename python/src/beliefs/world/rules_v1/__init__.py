"""Package content for the four v1 enumeration rules.

Each module here is **content**, not an import target. The rules store reads
its bytes, digests them, and executes the digested bytes; nothing in `beliefs`
imports these modules, and nothing in them may import `beliefs` — an
implementation whose behaviour depended on the installation around it could
pass its fixtures here and mean something else in another world.

The fixtures beside them are the normative half. A fixture is a closed document
carrying exactly `input` and `expected`, and the rule's entry point maps the
one onto the other exactly.
"""
