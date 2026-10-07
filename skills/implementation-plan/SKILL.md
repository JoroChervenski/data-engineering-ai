# Implementation Plan

## Purpose

Produce a concise implementation plan for a non-trivial change before any
code is written, so scope, impact and testing strategy are agreed before
implementation starts.

## When to Use

- Any change that is not trivially obvious and low-risk.
- Invoked via [`/plan-ticket`](../../commands/plan-ticket.md), which
  produces the plan without changing any files.
- Before the [Data Engineer agent](../../agents/data-engineer.agent.md)
  starts implementation on a non-trivial request.

## Inputs

- The business objective and/or technical requirement (ticket, request).
- The output of [`repository-discovery`](../repository-discovery/SKILL.md)
  for the affected area, if not already available in context.
- Any constraints or acceptance criteria already known.

## Preconditions

- The affected area of the repository has been inspected (discovery has
  run, or the area is already well understood in the current session).

## Procedure

1. Restate the business objective and the technical requirement in your
   own words; confirm they match what was asked.
2. Identify affected files/components based on actual inspection, not
   assumption.
3. Assess architecture impact: does this change any boundary, contract,
   or data flow?
4. Assess data-model impact: does this change grain, keys, or
   relationships in a dimensional model?
5. Assess security impact: does this touch secrets, access control, PII,
   or RLS/OLS?
6. Assess performance impact: does this touch a hot path, a large join, a
   semantic-model refresh?
7. State backward-compatibility impact explicitly: compatible, or
   intentionally breaking (and why).
8. Define the testing strategy: which test types apply (unit,
   integration, data quality, reconciliation, schema, regression).
9. Note deployment considerations, if any are observable (e.g., an
   environment-specific config that must be set).
10. List open questions or missing acceptance criteria instead of
    guessing.

## Decision Criteria

- If any of architecture, data-model, or security impact is non-trivial,
  the plan must be reviewed before implementation starts, even if the
  requester did not ask for review.
- If acceptance criteria are missing or ambiguous, state that as a
  blocking open question rather than picking an interpretation silently.

## Evidence Required

Affected files/components are named because they were found during
inspection, not guessed from a similar past change.

## Output Format

```text
## Objective
## Affected Files / Components
## Architecture Impact
## Data-Model Impact
## Security Impact
## Performance Impact
## Backward Compatibility
## Testing Strategy
## Deployment Considerations
## Open Questions
```

## Quality Checks

- Every affected file/component was actually located in the repository.
- Testing strategy names concrete test types for this change, not a
  generic boilerplate list.
- Open questions are listed, not silently resolved by assumption.

## Common Failure Modes

- Writing a plan from the ticket text alone, without inspecting the
  repository.
- Skipping the backward-compatibility and security-impact sections
  because the change "looks small."

## Escalation / Specialist Handoff

If the plan reveals a real architectural trade-off, hand off to the
[Architect agent](../../agents/architect.agent.md) via
[`architecture-review`](../architecture-review/SKILL.md) before
implementation proceeds.
