---
name: kimball-review
description: "Review a dimensional model or Power BI semantic model against Kimball principles: business process, grain, fact types, conformed/role-playing/junk dimensions, SCD handling, late-arriving data and modelling anti-patterns. Use when designing or reviewing Gold-layer facts/dimensions or semantic-model relationships."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/kimball-review/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Kimball Review

## Purpose

Review a dimensional model (or semantic model built on one) against
Kimball dimensional modelling principles, and flag anti-patterns that
hurt correctness, maintainability or semantic-model performance.

## When to Use

- Reviewing or designing a Gold-layer fact/dimension schema.
- Reviewing a Power BI semantic model's relationships and grain.
- Invoked via [`/review-data-model`](../../commands/review-data-model.md)
  or by the [Architect](../../agents/architect.agent.md)/
  [Reviewer](../../agents/reviewer.agent.md) agents.

## Inputs

- The schema/model definition (table DDL, TMDL, or notebook/SQL that
  builds the Gold layer).
- The business process the fact table(s) represent, if stated. If not
  stated, it must be inferred from evidence or flagged as unknown — never
  assumed.

## Preconditions

- The business process and, ideally, the stated grain are known or can be
  reasonably inferred from evidence. If the grain cannot be determined,
  say so before reviewing further — do not review against a guessed
  grain.

## Procedure

1. Identify the business process each fact table represents.
2. Determine the fact table's grain. If it is not explicitly declared
   anywhere, state that as a finding on its own — declaring grain first
   is a precondition for good fact design, not optional.
3. Classify each fact table: transaction fact, periodic snapshot,
   accumulating snapshot, or factless fact.
4. Review dimension design: surrogate keys, natural/business keys,
   conformed dimensions, role-playing dimensions, junk dimensions,
   degenerate dimensions, bridge tables where applicable.
5. Review Slowly Changing Dimension (SCD) handling: is the type (0/1/2)
   appropriate for how the attribute is actually used, and implemented
   correctly?
6. Review handling of late-arriving facts/dimensions, inferred members
   and unknown members.
7. Review date/time dimension design and its semantic-model compatibility.
8. Check for the anti-patterns listed below.

## Decision Criteria — Anti-Patterns to Flag

- Mixed grain within a single fact table.
- Snowflaking without a stated justification.
- Unnecessary many-to-many relationships.
- Fact-to-fact relationships.
- Bidirectional filtering used to patch a modelling gap.
- Incorrect SCD handling (e.g., overwriting history that the business
  needs, or Type 2 churn on attributes nobody needs history for).
- Duplicated dimensions that should be conformed.
- Weak/ambiguous naming.
- Poor or missing surrogate keys.
- Excessive calculated columns that should be measures or ETL logic.
- High-cardinality attributes causing semantic-model performance
  problems.

## Evidence Required

Every finding cites the specific table/column/relationship it concerns.
No general "Kimball says..." finding without a concrete locator in the
model under review.

## Output Format

Findings list using the standard severity model (Critical / High / Medium
/ Low / Suggestion), each with Severity, Location, Evidence, Impact,
Recommended fix, Confidence. Precede findings with the identified grain(s)
per fact table — stated explicitly, even if the finding is "grain is not
declared anywhere."

## Quality Checks

- Grain is explicitly stated (or its absence is explicitly flagged) for
  every fact table reviewed.
- Every anti-pattern finding names the specific object it applies to.
- SCD recommendations match how the attribute is actually used
  downstream, not a default assumption.

## Common Failure Modes

- Reviewing a semantic model without ever stating the grain of its
  underlying fact tables.
- Flagging snowflaking or bidirectional filtering as wrong without
  checking whether it was a deliberate, justified choice.
- Applying Kimball rules to a Bronze/Silver/staging table that was never
  meant to be a dimensional model.

## Escalation / Specialist Handoff

Architecture-level consequences (e.g., a target-architecture change) go to
the [Architect agent](../../agents/architect.agent.md) via
[`architecture-assessment`](../architecture-assessment/SKILL.md).
