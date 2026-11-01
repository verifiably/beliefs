# Corrective round 1 re-review — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only subagent). Scope: commit c929e95 (test_ci_suites_are_the_local_suites), fix for final review Important 1.
Verdict: accept. Critical 0, Important 0, Minor 1. Ran just test-one tests/test_ci_workflow.py: 18 passed.

Minor 1 (python/tests/test_ci_workflow.py:237-250): the test compares the per-package variables, not test_cmd (justfile:45, py_test_cmd + " && " + ts_test_cmd); a phase added directly to test_cmd would leave CI behind with the test green — the same silent coverage loss one level up. Fix: assert evaluate("test_cmd") == evaluate("py_test_cmd") + " && " + evaluate("ts_test_cmd").

Checked and fine: local edits to py_fast_cmd, the N2 phase or ts_test_cmd fail it; CI-side additions beyond reporting flags (--deselect, -k, --ignore, -p, vitest flags before or after the reporters) fail it; the JUnit regex cannot cross the closing quote, so it cannot swallow a selection change (only deliberate $(...) sabotage escapes); dropping a JUnit flag changes no selection and the artifact tests still guard evidence; quoting via just --evaluate is consistent on both sides; ci.yml env sets no selection (no PYTEST_ADDOPTS or vitest filter); test uses the fixture Checkout, only just --evaluate, key-by-key env, checks return codes. No new Critical or Important issue; no production code changed.
