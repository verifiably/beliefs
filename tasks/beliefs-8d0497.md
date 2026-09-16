---
id: beliefs-8d0497
title: Guard the project root against new scratch directories
status: done
priority: 3
size: s
complexity: low
process: direct
owner: chore/docs-guards
created: 2026-09-07T09:49:14Z
updated: 2026-09-16T10:22:47Z
started: 2026-09-16T10:18:56Z
completed: 2026-09-16T10:22:47Z
depends: []
tags: [testing]
model: "claude-opus-5[1m]"
---

Thirteen work-root directories accumulated at the project root one variant at a time, each added to .gitignore as it appeared, until they outnumbered the genuine hidden dirs five to one. Nothing objected, because nothing was watching.

Add a test that pins the project root's entry set against an explicit allowlist and fails when an unlisted directory appears. It should name the offender and point at the convention (see beliefs-5aad8c: work roots belong under .work/). Cheap to write, and it converts a silent drift into a red test the first time it happens rather than the thirteenth.

Two nuances worth handling:
- It must tolerate a developer's own untracked scratch without becoming noise. Gating on directories that are git-ignored-but-unlisted is the useful signal; a stray file someone made by hand is not.
- .gitignore globs hide the problem from git status but not from the filesystem, so the test should read the directory, not git's view of it. The .cut*-acceptance/ glob added in e9768a6 already means a new cut root appears with no .gitignore edit at all — convenient, and exactly why the count grew unnoticed.

Related incident: during the verification-publication slice a stray 'git add -A' in the main checkout swept an unignored .mm30-reproduction-cut21/ into a commit on main. It was caught and reverted, but a root-hygiene test would have made the underlying condition visible much earlier.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity low: The task specifies the filesystem entry allowlist, ignored-directory filter, diagnostic and .work convention; existing .gitignore supplies the policy. One focused guard with positive/negative cases has a clear check.
- 2026-09-16T10:18:45Z (main): Process direct: the body fixes the signal (an unlisted directory at the root, read from the filesystem, ignoring hand-made files), the diagnostic and the convention; the allowlist is read off the tree.
- 2026-09-16T10:22:47Z (chore/docs-guards): python/tests/test_project_root.py pins the root's directory set against an explicit allowlist plus the five legacy work roots named individually (no globs); reads the filesystem, ignores files, names the offender and points at .work/ (beliefs-5aad8c); red on a stray .cut32-acceptance, green on the worktree and the main checkout.
