---
id: beliefs-8bcec6
title: cut21_acceptance.py has never been executed
status: todo
priority: 2
size: xs
created: 2026-09-07T09:29:49Z
updated: 2026-09-07T09:29:49Z
depends: []
tags: [conformance]
---

tools/cut21_acceptance.py sets PREFIX_RUNNERS = ("cut20_acceptance.py",) and no such file exists, so main() returns 1 before probe(), cut_environment(), run_prefix() or declared_accounting() are ever reached. Its control flow is entirely unexercised code.

Cut 21's arm-soundness result (7 passed, 25 arms sound) was obtained by running tests/acceptance/test_n2_cut21.py directly, not through the runner. So the first real invocation — during cut 21's discharge — is also the runner's first execution, and it should be expected to need fixes rather than assumed to work. declared_accounting() was at least called directly and returns (25, 8, 8).

Recorded in the plan at docs/superpowers/plans/2026-09-06-verification-publication.md (Task 10 step 4) and in docs/plans/2026-09-06-verification-publication-execution.md.
