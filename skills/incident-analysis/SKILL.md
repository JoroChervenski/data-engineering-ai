---
name: incident-analysis
description: "Evidence-driven root-cause analysis for a production data incident (failed job, wrong numbers, missing records) without jumping from symptom to claimed cause. Use when a reported symptom needs a diagnosed cause before a fix is proposed."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/incident-analysis/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Incident Analysis

## Purpose

Perform evidence-driven root-cause analysis for a production incident,
without jumping from a symptom straight to a claimed root cause.

## When to Use

- Invoked via [`/investigate`](../../commands/investigate.md).
- Any time a reported symptom (a failed job, wrong numbers, a missing
  record) needs a diagnosed cause before a fix is proposed.

## Inputs

- The reported symptom (what was observed, when, and how it was
  detected).
- Logs, job run history, error messages, and any relevant monitoring
  output.
- The relevant pipeline/code, inspected via
  [`repository-discovery`](../repository-discovery/SKILL.md) if not
  already understood.

## Preconditions

- The symptom is described concretely (what, when, how detected) — a
  vague report ("something is wrong with the numbers") is itself the
  first thing to resolve before analysis can proceed.

## Procedure

```text
Symptom
  ↓
Evidence
  ↓
Potential causes
  ↓
Tests / falsification
  ↓
Root cause
  ↓
Fix
  ↓
Validation
  ↓
Prevention
```

1. Record the symptom precisely: what was observed, expected vs. actual,
   when it started, scope (one record, one run, all runs since a date).
2. Gather evidence: logs, error messages, affected row counts, recent
   changes (code, config, data, upstream source) around the relevant
   time window.
3. List potential causes as hypotheses — explicitly labeled as
   hypotheses, not conclusions.
4. For each plausible hypothesis, design a test or check that could
   falsify it. Run/perform it before accepting the hypothesis.
5. Only call something the root cause once a hypothesis survives an
   attempt to falsify it and the evidence actually explains the full
   symptom (not just part of it).
6. Propose a fix tied directly to the validated root cause.
7. Define how the fix will be validated (what result confirms the
   incident is actually resolved).
8. Propose a prevention measure (a test, an alert, a validation check)
   so the same class of incident is caught earlier next time.

## Decision Criteria

- Keep **known facts**, **hypotheses**, **missing evidence**, and
  **validated root cause** visibly separate at every step.
- Do not advance a hypothesis to "root cause" without an attempted
  falsification test.
- If evidence is insufficient to distinguish between two hypotheses, say
  so rather than picking the more convenient one.

## Evidence Required

Every hypothesis cites what evidence would confirm or rule it out, and
whether that test was actually performed.

## Output Format

```text
## Symptom
## Known Facts
## Hypotheses (and falsification attempts)
## Missing Evidence
## Validated Root Cause
## Fix
## Validation Plan
## Prevention
```

## Quality Checks

- The root cause section only exists if a hypothesis actually survived
  falsification.
- The fix addresses the validated root cause, not just the symptom.
- A prevention measure is proposed, not only a one-off fix.

## Common Failure Modes

- Jumping from an error message straight to "root cause" without testing
  alternative explanations.
- Fixing the first plausible cause found instead of the one the evidence
  actually supports.
- Omitting a prevention measure, so the same incident recurs.

## Escalation / Specialist Handoff

Once a fix is identified, hand off to
[`implementation-plan`](../implementation-plan/SKILL.md) before
implementing it, and to [`code-review`](../code-review/SKILL.md)
afterward.
