---
id: beliefs-97938d
title: Harden TypeScript dependency installation
status: done
priority: 2
size: xs
owner: fix/ts-dependencies
created: 2026-09-02T21:54:09Z
updated: 2026-09-02T22:15:47Z
depends: []
tags: [security]
---

Upgrade the vulnerable Vitest dependency tree, pin npm's install-policy behavior, and approve only reviewed version-pinned lifecycle scripts. Acceptance: npm audit reports zero findings; strict npm ci emits no unreviewed-script warning; TypeScript gates and tasks check pass.

## Notes

- 2026-09-02T21:54:13Z (fix/ts-dependencies): All six audit findings trace to vitest@2.1.9 and its Vite stack; current pending scripts are @biomejs/biome@1.9.4 and esbuild@0.21.5, both registry-signed and reviewed before approval.
- 2026-09-02T21:57:17Z (fix/ts-dependencies): Vitest 4.1.11 resolves to Vite 8.2.2, removes esbuild, updates nanoid to 3.3.18, and yields zero audit findings. Strict npm 11.17 installs also require the signed macOS-only fsevents@2.3.3 approval hidden from Linux's pending list; approvals are exact-version pinned.
- 2026-09-02T22:15:47Z (fix/ts-dependencies): Verification: strict npm ci found 0 vulnerabilities with no pending-script warning; 101 TypeScript tests, typecheck, Biome, registry signatures/attestations, 3074 Python tests, Ruff, and Pyright all pass.
- 2026-09-02T22:15:47Z (fix/ts-dependencies): Upgraded Vitest to 4.1.11 and enforced exact-version install-script approvals; npm audit is clean
