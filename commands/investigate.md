# `/investigate`

## Purpose

Run evidence-driven root-cause analysis for a reported incident, without
jumping from a symptom straight to a claimed cause.

## Expected Inputs

- The reported symptom: what was observed, when, and how it was
  detected.
- Access to logs, job run history, and the relevant pipeline/code.

## Skills / Roles Invoked

- [`incident-analysis`](../skills/incident-analysis/SKILL.md).
- [Repository Analyst agent](../agents/repository-analyst.agent.md) via
  [`repository-discovery`](../skills/repository-discovery/SKILL.md), if
  the relevant pipeline/code is not already understood.

## Ordered Execution Steps

1. Record the symptom precisely (what/when/scope).
2. Gather evidence: logs, errors, row counts, recent changes.
3. Run the [`incident-analysis`](../skills/incident-analysis/SKILL.md)
   procedure: hypotheses, falsification attempts, validated root cause.
4. Propose a fix tied to the validated root cause, a validation plan, and
   a prevention measure.
5. Hand the fix to [`/plan-ticket`](plan-ticket.md) before it is
   implemented, unless it is trivially obvious and low-risk.

## Expected Output

Symptom → Known Facts → Hypotheses (with falsification attempts) →
Missing Evidence → Validated Root Cause → Fix → Validation Plan →
Prevention, per the incident-analysis skill's output format.

## Safety Constraints

- Investigation itself is read-only.
- No hypothesis is reported as "root cause" without an attempted
  falsification test.
- A fix is not implemented as part of this command; it is handed off.
