---
name: pull-request
description: "Build a PR description from the actual diff, test results and review findings rather than from the original request. Use near the end of a task, after implementation and review are complete."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/pull-request/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Pull Request Preparation

## Purpose

Build a PR description from the actual diff, tests and review findings —
not from the original request alone — so the PR accurately reflects what
changed and what was checked.

## When to Use

- Invoked via [`/prepare-pr`](../../commands/prepare-pr.md), near the end
  of a task, after implementation and review are complete.

## Inputs

- The actual diff/branch.
- The original ticket/request and, if one exists, the
  [implementation plan](../implementation-plan/SKILL.md).
- Test results.
- Review findings from [`code-review`](../code-review/SKILL.md) and, if
  applicable, [`kimball-review`](../kimball-review/SKILL.md).

## Preconditions

- Implementation and review have both actually happened. This skill does
  not produce a PR description for work that has not been reviewed.

## Procedure

1. Derive the summary and business reason from the original
   ticket/request — do not invent a justification that was not actually
   given.
2. Derive "technical changes" from the real diff, not from the plan (the
   plan is the intent; the diff is the truth).
3. State architecture impact and data impact only if the diff actually
   has any; say "none" explicitly if so.
4. Summarize testing: what was run, what passed, what is intentionally
   not covered.
5. State deployment considerations, if any (config changes, migration
   steps, ordering constraints).
6. State a rollback approach appropriate to the change.
7. List risks, drawn from the actual review findings, not a generic
   boilerplate list.
8. Include a reviewer checklist tailored to what this specific change
   touches (e.g., "confirm the incremental load was tested for
   idempotency" only if that's actually relevant here).

## Decision Criteria

- Nothing in the PR description may contradict the actual diff.
- Any unresolved Critical/High review finding is listed as an open risk,
  not omitted because it is embarrassing or inconvenient.
- This skill never approves or merges anything — it only prepares the
  description for human review.

## Evidence Required

Every claim in "technical changes," "data impact," and "testing" traces
to the actual diff/test run/review output.

## Output Format

```text
## Branch Name
## PR Title
## Summary
## Business Reason
## Technical Changes
## Architecture Impact
## Data Impact
## Testing
## Deployment
## Rollback
## Risks
## Reviewer Checklist
```

## Quality Checks

- Technical changes match the real diff, file for file.
- Any open Critical/High finding from review appears under Risks.
- The description does not claim tests ran if they did not.

## Common Failure Modes

- Writing the PR description from the ticket instead of from the diff,
  so it describes intended work rather than actual work.
- Omitting a known risk because the change otherwise looks finished.
- Auto-approving or recommending merge — this skill's output is input to
  human review, not a merge decision.

## Escalation / Specialist Handoff

None — this is the last step before human review in the standard
workflow. See
[`commands/prepare-pr.md`](../../commands/prepare-pr.md) and
[`templates/PR.md`](../../templates/PR.md).
