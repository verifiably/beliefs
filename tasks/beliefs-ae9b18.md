---
id: beliefs-ae9b18
title: One spelling for the assessment's run member
status: todo
priority: 1
size: m
created: 2026-09-05T20:00:55Z
updated: 2026-09-05T20:00:55Z
depends: []
parent: beliefs-754995
tags: [write-path, assessment, reproduction-finding]
---

Finding from the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §6, steps 6 and 8). build_assessment returns an AssessmentValue whose run is the bare closure address; stored.assessment_node stores run:<address> (eligibility_refusal requires the typed ref), so the stored record's identity differs from the derived one. Admission over the corpus (gather -> admit) matches verifications against the stored identity; the audit's check_verification recomputes the derived one. A verification naming the derived identity passed the audit and was refused at admission (not-admitted-verification-state) on a clean-environment pass, giving NoBelief(no-eligible-assessment) for that reason alone. Failing test to write first: a verification derived from an original and replayed run over a stored assessment is both Admitted over the corpus and checked without contradiction by audit_corpus. Amend the computation design or the assessment record's stored mapping so one spelling enters the identity.
