---
description: "Repository discovery plus qualitative architecture review: current state, risks, target, alternatives, trade-offs"
argument-hint: "[concern or objective]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/architecture-review`

## Purpose

Run repository discovery plus a qualitative architecture review:
current-state reconstruction, risks, target architecture, alternatives,
and trade-offs.

## Expected Inputs

- The target repository, open and accessible.
- Optionally, a specific concern or objective driving the review (e.g.
  "can this scale to 10x volume," "should we move off X").

## Skills / Roles Invoked

- [Repository Analyst agent](../agents/repository-analyst.agent.md) via
  [`repository-discovery`](../skills/repository-discovery/SKILL.md)
  (always runs first).
- [Architect agent](../agents/architect.agent.md) via
  [`architecture-assessment`](../skills/architecture-assessment/SKILL.md).
- [`kimball-review`](../skills/kimball-review/SKILL.md), if a dimensional
  model or semantic model is in scope.

## Ordered Execution Steps

1. Run repository discovery if it has not already run in this session for
   the relevant area.
2. Run the [architecture-assessment skill](../skills/architecture-assessment/SKILL.md)
   procedure against the discovery output.
3. If the review surfaces a dimensional-modelling concern, run
   [`kimball-review`](../skills/kimball-review/SKILL.md) on the relevant
   model.
4. Flag ADR candidates for decisions with lasting consequences.

## Expected Output

Current state → Problems → Root causes → Risks → Technical debt →
Recommended target → Alternatives → Advantages/disadvantages → Migration/
cost/performance/security/operational implications → Migration roadmap →
ADR candidates. Every current-state claim traces to discovery evidence.

## Safety Constraints

- Read-only. No files are modified; ADR candidates are proposals, not
  committed decisions.
- No numerical scoring unless a formal scoring model has been explicitly
  established for this engagement.
- No mechanical recommendation of a specific pattern (Medallion, Data
  Vault, Lakehouse, microservices) without justification against this
  repository's actual observed constraints.

## Request

$ARGUMENTS
