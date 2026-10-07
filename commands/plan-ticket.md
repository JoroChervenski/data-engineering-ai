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

## Expected Output

The implementation-plan skill's output format: Objective, Affected
Files/Components, Architecture Impact, Data-Model Impact, Security
Impact, Performance Impact, Backward Compatibility, Testing Strategy,
Deployment Considerations, Open Questions.

## Safety Constraints

- No files are changed by this command under any circumstance — it only
  produces a plan.
- Affected files/components listed must have actually been located in
  the repository, not guessed.
