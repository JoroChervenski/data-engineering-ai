---
name: testing
description: "Choose and apply the right test types (unit, data quality, reconciliation, regression, integration) for a data engineering change so correctness is verified, not assumed. Use with any implementation step and when checking whether tests cover risks found in review."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/testing/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Testing

## Purpose

Choose and apply the right test types for a change, so that correctness,
data quality and regressions are actually verified rather than assumed.

## When to Use

- Any implementation step produced by the
  [Data Engineer agent](../../agents/data-engineer.agent.md).
- As part of [`code-review`](../code-review/SKILL.md), to check whether
  existing/added tests actually cover the risk areas identified in
  review.

## Inputs

- The change being tested (diff, or the implementation plan describing
  intended behavior).
- The repository's existing test setup, if any (frameworks, fixtures,
  CI wiring) — identified via
  [`repository-discovery`](../repository-discovery/SKILL.md) if not
  already known.

## Preconditions

- The behavior under test is understood well enough to state an expected
  outcome, not just an input.

## Procedure

1. Identify which test types actually apply to this change:
   - **Unit** — isolated logic, pure functions, transformation rules.
   - **Integration** — a pipeline/job against realistic inputs end to end.
   - **Data quality** — nulls, uniqueness, referential integrity, valid
     ranges, schema conformance.
   - **Reconciliation** — totals/counts match between source and target,
     or between old and new logic during a migration.
   - **Regression** — a previously fixed defect stays fixed.
   - **Business-rule validation** — a specific business rule produces the
     documented outcome.
2. For data pipelines, make sure at least one test exercises the
   incremental/CDC path, not only a full-reload happy path.
3. Prefer deterministic tests. If a test result can depend on wall-clock
   time, parallelism, or external state, make that dependency explicit and
   control for it.
4. Make sure tests are safe to run repeatedly without side effects that
   accumulate (idempotent test fixtures/teardown).
5. Record what is intentionally left untested and why, rather than
   silently omitting coverage.

## Decision Criteria

- A change to transformation logic needs at least a unit test.
- A change to an incremental/CDC load needs an integration test that
  proves idempotency (running it twice produces the same result).
- A change to a Gold-layer fact/dimension needs a data-quality check on
  grain, uniqueness and referential integrity.
- A migration/backfill needs a reconciliation test against the prior
  logic or source counts.

## Evidence Required

Each test type chosen is justified by what the change actually does, not
applied as boilerplate. Tests not added are explicitly called out with a
reason.

## Output Format

```text
## Test Types Applied (and why)
## Test Types Intentionally Not Applied (and why)
## Coverage of Identified Risk Areas
```

## Quality Checks

- At least one test proves idempotency for any incremental/CDC change.
- Data-quality checks exist for any new/changed Gold-layer table.
- No test silently depends on execution order or shared mutable state.

## Common Failure Modes

- Testing only the happy path for an incremental load, never the
  re-run/duplicate-processing case.
- Treating "it ran once without an error" as equivalent to "it is
  correct."
- Skipping data-quality checks because unit tests already exist.

## Escalation / Specialist Handoff

Findings about missing or inadequate tests feed back into
[`code-review`](../code-review/SKILL.md) and, for dimensional models,
[`kimball-review`](../kimball-review/SKILL.md).
