---
description: "Review a diff/branch/PR as a senior/principal engineer, focused on production risk"
argument-hint: "[branch, PR or diff range]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/review-pr`

## Purpose

Review a diff/branch/PR as a senior/principal engineer would, focused on
production risk.

## Expected Inputs

- The diff/branch/PR to review.
- The original request/ticket and implementation plan, if available.

## Skills / Roles Invoked

- [Reviewer agent](../agents/reviewer.agent.md) via
  [`code-review`](../skills/code-review/SKILL.md).
- [`kimball-review`](../skills/kimball-review/SKILL.md), if a dimensional
  model is touched.
- [`testing`](../skills/testing/SKILL.md), to assess test adequacy.

## Ordered Execution Steps

1. Read the full diff.
2. Run the [`code-review`](../skills/code-review/SKILL.md) procedure.
3. If a dimensional model or semantic model is touched, also run
   [`kimball-review`](../skills/kimball-review/SKILL.md).
4. Assess test adequacy via [`testing`](../skills/testing/SKILL.md).
5. Aggregate findings, most severe first, with an overall recommendation.
6. If the change belongs to a ticket that has a note in the overlay
   (see [`/ticket`](ticket.md), step 0), write the verdict and the
   findings into the note's Review section, with the date, the commit
   reviewed and a dated Log line.

## Expected Output

Findings list (Severity, Location, Evidence, Impact, Recommended fix,
Confidence per finding — see the
[severity model](../skills/code-review/SKILL.md#severity-model)) plus an
overall recommendation: ready to proceed / needs changes / blocked.

## Safety Constraints

- Read-only for the code under review: it never modifies the
  diff/branch, approves, or merges anything. The ticket note (step 6) is
  the only file it writes.
- Any committed secret is reported as Critical without exception.

## Request

$ARGUMENTS
