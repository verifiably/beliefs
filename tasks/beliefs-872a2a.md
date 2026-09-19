---
id: beliefs-872a2a
title: "ts inner loop has no recipe: 25 npm test/vitest bypasses in the audit's after-week"
status: idea
priority: 2
created: 2026-09-19T12:08:11Z
updated: 2026-09-19T12:08:11Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5
---

beliefs-f253a1's after-week (09-12..09-17) recorded 25 tt bypasses, all TypeScript: 19 'npm test' and 6 'npx vitest run tests/declarations.test.ts', all claude. The python side had zero: test-fast and test carry it. AGENTS.md lists npm test as the standalone command and test-fast runs both packages, so an agent iterating on ts/ alone has no wrapped target and runs npm directly. Option: a 'just test-ts' (and test-py) recipe through tools/tt, listed in AGENTS.md beside test-fast; or accept the ts loop is 1s and not worth wrapping, and say so.
