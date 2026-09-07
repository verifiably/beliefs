---
id: beliefs-22fbf9
title: Settle the beliefs package names before any release
status: done
priority: 2
size: s
owner: main
created: 2026-09-07T14:29:39Z
updated: 2026-09-07T15:39:33Z
depends: []
tags: [hygiene]
---

Two naming problems, both blocking publication.

PyPI: python/pyproject.toml declares name = 'beliefs', and that name is taken by an unrelated package — Dustin Smith, MIT Media Lab, github.com/EventTeam/beliefs, 'Partial-information datastructures used to represent belief states', last released at 0.1. PyPI's namespace is flat, so this is not a scope collision that can be worked around; the package needs a different name. verifiably-beliefs is free.

npm: ts/package.json is @verifiably/beliefs with private: true. That may be deliberate — the README says ts carries only the one shared encoding (M10 is the only cross-implementation row), which is a parity artifact rather than a library anyone installs. Decide whether it stays private or ships; if it ships, note that the scope actually in use across the stack is @nodes-dev, not @verifiably.

Renaming also touches the dependents: [tool.uv.sources] comments say publication replaces the editable path entries with released-version bounds, and science depends on beliefs.

Gated on ops-f1a933 for the naming scheme.

## Notes

- 2026-09-07T15:39:33Z (main): Python distribution renamed beliefs -> verifiably-beliefs, per the verifiably- prefix decision; the import package stays 'beliefs', matching science which imports as 'science' while shipping as verifiably-science. science's dependency and its [tool.uv.sources] key updated, both uv.lock files regenerated. Gates green in both, and science's 226 tests pass against the renamed editable dependency. The npm side is untouched and still open: @verifiably/beliefs remains private: true, and the scope actually in use across the stack is @nodes-dev.
