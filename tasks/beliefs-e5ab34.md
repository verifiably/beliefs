---
id: beliefs-e5ab34
title: Ship reference rule implementations keyed by rule identity
status: todo
priority: 1
size: s
created: 2026-09-09T12:43:20Z
updated: 2026-09-09T12:43:20Z
depends: []
tags: [command-framework, dogfood]
---

Belief-path design (science docs/specs/2026-09-09-belief-path-commands-design.md §6.1): the kernel ships, keyed by rule identity and importable without constructing anything, the outcome-file interpretation rule the mm30 reproduction driver defined (mapping a ResultManifest's digest for a canonical outcome file to supported/refuted/inconclusive, under a kernel identity in place of mm30-reproduction/outcome-file/v1) and content-identity-equality/v1, each with its fixtures, beside science.belief.v1/reference. The surface resolves a spec's rule identities through this table and defines no rule; an unknown identity refuses; the audit recomputes against the same implementations freeze bound.
