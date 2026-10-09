---
id: beliefs-7be4f1
title: detached.sh should persist its wrapped command's exit code
status: idea
priority: 2
created: 2026-09-22T15:13:32Z
updated: 2026-10-09T14:03:50Z
depends: []
tags: [conformance]
---

Filed by cut 38: the cut runner is launched through .work/acceptance/detached.sh, which does not record $? anywhere, so the results record had to establish exit 0 from the log's contents (no FAILED/ERROR/Traceback, all phases complete, the rows-exercised line printed only inside 'if result == 0'). Echoing 'exit=$?' into the log would make it an observation instead of an inference.

## Notes

- 2026-10-09T14:03:50Z (main): scope: drop; no task changes; proposal: premise gone — be18e7b (plan review, 2026-09-27) replaced detached.sh with harness-tracked run_in_background + tee, whose completion reports the exit status; every plan since forbids detached.sh (2026-10-01-mount-citations.md:76). .work/acceptance/detached.sh is an untracked local file
