---
id: beliefs-2ce409
title: Keep setup-installed dependencies out of Dropbox
status: done
priority: 2
size: xs
complexity: low
owner: main
created: 2026-09-12T18:44:30Z
updated: 2026-09-12T18:46:28Z
started: 2026-09-12T18:44:42Z
completed: 2026-09-12T18:46:28Z
depends: []
tags: [testing]
---

ops-54ee7b found that just setup recreates ts/node_modules with npm ci but does not restore com.dropbox.ignored=1. Append the native attr command after a successful install; verify just setup succeeds and the directory attribute is 1. This is the existing-setup piece of the cross-project Dropbox churn audit.

## Notes

- 2026-09-12T18:44:42Z (main): Claimed by Codex for the setup attribute line; the existing audit task is parked for its baseline week.
- 2026-09-12T18:46:28Z (main): just setup now restores com.dropbox.ignored=1 after npm ci recreates ts/node_modules. Verified the full setup recipe and attribute readback; tasks check has no errors or warnings.
