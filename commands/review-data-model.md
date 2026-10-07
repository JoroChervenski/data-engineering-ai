---
description: "Review a dimensional/semantic model against Kimball and semantic-model standards"
argument-hint: "[model, tables or path]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/review-data-model`

## Purpose

Review a dimensional model and/or semantic model against Kimball and
semantic-model standards.

## Expected Inputs

- The schema/model definition (DDL, TMDL, or the notebook/SQL that builds
  it).
- The business process the model represents, if known (otherwise this
  command must first determine it from evidence or flag it as unknown).

## Skills / Roles Invoked

- [`kimball-review`](../skills/kimball-review/SKILL.md), run by the
  [Architect](../agents/architect.agent.md) or
  [Reviewer](../agents/reviewer.agent.md) agent depending on whether this
  is a design review or a post-implementation review.

## Ordered Execution Steps

1. Identify the business process and declared (or inferred) grain for
   each fact table in scope. If grain is not declared anywhere, state
   that as a finding before continuing.
2. Run the [`kimball-review`](../skills/kimball-review/SKILL.md)
   procedure.
3. If the model feeds a Power BI semantic model, also check Direct Lake/
   Import/DirectQuery mode and relationship/RLS/OLS design per
   [`standards/fabric.md`](../standards/fabric.md).
4. Return findings using the standard severity model.

## Expected Output

Grain statement per fact table, followed by a findings list (Severity,
Location, Evidence, Impact, Recommended fix, Confidence per the
[severity model](../skills/code-review/SKILL.md#severity-model)).

## Safety Constraints

- Read-only. No schema or model change is made by this command directly.
- Does not review against an assumed grain — an undeclared, unconfirmed
  grain is itself reported as a finding, not silently assumed.

## Request

$ARGUMENTS
