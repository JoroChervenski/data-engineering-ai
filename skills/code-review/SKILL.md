---
name: code-review
description: "Senior/principal-level review of a diff, branch or PR focused on production risk, using the framework severity model (Critical/High/Medium/Low/Suggestion). Use after implementation, before work is considered complete or a PR is prepared."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/code-review/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Code Review

## Purpose

Independently review implementation output (a diff, branch, or PR) as a
senior/principal engineer would, focused on production risk rather than
whether the implementer's stated intent was met.

## Severity Model

Every review skill in this framework (code review, Kimball review,
architecture review, PR review) reports findings using this same model.
This is its canonical definition:

| Severity | Meaning |
|---|---|
| **Critical** | Causes data loss, a security exposure, or a production outage. Always includes any committed secret. |
| **High** | Likely to cause incorrect results or a significant operational problem; not immediately catastrophic. |
| **Medium** | A real defect or risk with limited blast radius, or a Critical/High-class issue with low likelihood. |
| **Low** | A minor correctness or maintainability issue. |
| **Suggestion** | A style or best-practice improvement with no correctness/production risk. |

Each finding states exactly these fields, in this order:

```text
Severity
Location
Evidence
Impact
Recommended fix
Confidence
```

Production risk always outranks cosmetic style when prioritizing findings.

## When to Use

- Invoked via [`/review-pr`](../../commands/review-pr.md).
- After any implementation step, before it is considered complete, per
  the [`orchestration`](../orchestration/SKILL.md) skill's review gate.

## Inputs

- The diff/branch/PR to review.
- The original request/ticket and, if one exists, the
  [implementation plan](../implementation-plan/SKILL.md) it was built
  against.
- Relevant standards: [`python.md`](../../standards/python.md),
  [`pyspark.md`](../../standards/pyspark.md),
  [`sql.md`](../../standards/sql.md),
  [`security.md`](../../standards/security.md),
  [`testing.md`](../../standards/testing.md).

## Preconditions

- The change to review actually exists (a real diff, not a description of
  intended work).

## Procedure

1. Read the diff in full; do not review only the parts that look
   unfamiliar.
2. Check correctness against the stated requirement and grain.
3. Check for data loss or duplicate-record creation risk.
4. Check incremental-loading logic specifically for idempotency and
   correct watermark/CDC handling.
5. Check joins for cardinality, correct keys, and null-handling
   semantics.
6. Check for grain violations if a dimensional model is touched — hand
   off to [`kimball-review`](../kimball-review/SKILL.md) if so.
7. Check for secrets, least-privilege violations, or PII handling issues
   — see [`standards/security.md`](../../standards/security.md). Any
   committed secret is automatically Critical.
8. Check performance implications appropriate to the change's size and
   scope.
9. Check maintainability: naming, structure, duplication.
10. Check test coverage and whether tests actually exercise the risk
    areas identified above, not just the happy path.
11. Check logging/observability: can a production failure of this change
    be diagnosed from what it logs?

## Decision Criteria

- Severity is assigned using the [Severity Model](#severity-model) above.
- Production risk outranks cosmetic style every time.
- A finding with low confidence is still reported, but its Confidence
  field says so — it is not suppressed.

## Evidence Required

Every finding cites a specific file/line/construct. No finding of the
form "this might have issues" without pointing at the actual location.

## Output Format

Findings list, most severe first:

```text
Severity
Location
Evidence
Impact
Recommended fix
Confidence
```

Followed by an overall recommendation: ready to proceed / needs changes /
blocked.

## Quality Checks

- Every Critical/High finding has concrete evidence, not speculation.
- The review does not merely confirm the implementer's stated intent; it
  independently checks what the code does.
- No committed secret goes unflagged.

## Common Failure Modes

- Rubber-stamping a change because the PR description sounds confident.
- Treating style preferences as Critical/High findings.
- Reviewing only the files that changed the most lines and skipping a
  small-but-risky change elsewhere in the diff.

## Escalation / Specialist Handoff

Dimensional-model findings → [`kimball-review`](../kimball-review/SKILL.md).
Test-adequacy findings → [`testing`](../testing/SKILL.md). Findings are
aggregated by the [Reviewer agent](../../agents/reviewer.agent.md) before
being handed to [`/prepare-pr`](../../commands/prepare-pr.md).
