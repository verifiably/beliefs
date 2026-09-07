---
id: beliefs-e7b186
title: Add GitHub Actions CI running just gate
status: done
priority: 2
size: m
owner: main
created: 2026-09-07T11:57:19Z
updated: 2026-09-07T13:07:05Z
depends: [beliefs-97eb6d, beliefs-0e0c9c]
tags: [testing]
---

Decision 2026-09-07: beliefs gets remote CI, at no cost. verifiably/beliefs is public, and GitHub's billing docs state that standard GitHub-hosted runners are free in public repositories regardless of plan. Public-repo runs do not draw on the private-repo allowance (2,000 min/month on Free; $0.006/min for a Linux 2-core runner beyond it), which is what was exhausted. Larger runners, GPU runners and macOS are billed even on public repos, so this stays on standard Linux.

Pattern to follow is nodes: a workflow whose jobs run the justfile recipes, so the local gate and the remote gate cannot drift (audit design §4.6). nodes keeps a two-job matrix with ci-python and ci-typescript recipes; those recipes leave `tasks check` out because the tasks binary is not on a runner. Per §4.1, projects that do want it install tasks with `cargo install --git https://github.com/khughitt/tasks --locked` behind the cargo cache action.

Expect a standard 2-core runner to be materially slower than the 16-core/32-thread host where the serial suite measured 1096.5s for 3840 tests, since that run is single-core anyway; consider `-n 2` for the CI job and keep the serial run as the conformance gate. Cache uv and npm.

Gated on the gate being green: CI added now would fail on every run.

## Notes

- 2026-09-07T13:07:05Z (main): CI added: .github/workflows/ci.yml runs just ci-python (3.11, 3.13) and just ci-typescript (20, 24) on pushes to main and pull requests, reusing the action pins nodes already vetted. Recipes rather than just gate, because the tasks binary is not on a runner; serial pytest, because python/README.md makes the serial run the required CI gate. Free: the repo is public.
