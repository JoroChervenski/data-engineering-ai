---
description: "Produce an implementation plan for a ticket/request without changing any files"
argument-hint: "<ticket text or ID>"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/plan-ticket`

## Purpose

Produce a concise implementation plan for a ticket/request without
changing any files.

## Expected Inputs

- The ticket/request text.
- The target repository, open and accessible.

## Skills / Roles Invoked

- [Repository Analyst agent](../agents/repository-analyst.agent.md) via
  [`repository-discovery`](../skills/repository-discovery/SKILL.md), for
  the affected area if not already understood.
- [Data Engineer agent](../agents/data-engineer.agent.md) via
  [`implementation-plan`](../skills/implementation-plan/SKILL.md).
- [Architect agent](../agents/architect.agent.md), only if the plan
  surfaces a real architectural trade-off.

## Ordered Execution Steps

1. Restate the objective/requirement from the ticket.
2. Run (or reuse) repository discovery for the affected area.
3. Run the [`implementation-plan`](../skills/implementation-plan/SKILL.md)
   procedure.
4. If a real architectural trade-off is surfaced, route to the
   [Architect agent](../agents/architect.agent.md) before finalizing the
   plan.
5. Return the plan. Do not implement it as part of this command.
6. If the request names a ticket and the overlay keeps ticket notes
   (see [`/ticket`](ticket.md), step 0), write the plan into that
   ticket's note under Plan, marked not approved, with a dated Log line.
   Create the note from [`templates/TICKET.md`](../templates/TICKET.md)
   if it is missing.

## Expected Output

The implementation-plan skill's output format: Objective, Affected
Files/Components, Architecture Impact, Data-Model Impact, Security
Impact, Performance Impact, Backward Compatibility, Testing Strategy,
Deployment Considerations, Open Questions.

## Safety Constraints

- No file in the client repository is changed — this command only
  produces a plan. The ticket note (step 6) is the only file it writes.
- Affected files/components listed must have actually been located in
  the repository, not guessed.

## Request

$ARGUMENTS
