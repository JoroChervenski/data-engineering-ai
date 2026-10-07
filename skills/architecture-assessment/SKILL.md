---
name: architecture-assessment
description: "Qualitative, evidence-grounded assessment of a repository's current architecture, risks and credible target/alternative architectures with trade-offs. Use before significant architectural changes or when comparing current vs. target designs; requires repository-discovery output."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/architecture-assessment/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Architecture Review

## Purpose

Produce a qualitative, evidence-grounded assessment of a repository's
current architecture, its risks, and credible target/alternative
architectures with trade-offs — without inventing facts or mechanically
prescribing a fashionable pattern.

## When to Use

- Invoked by [`/architecture-review`](../../commands/architecture-review.md).
- Before any significant architectural change.
- When comparing current vs. target vs. alternative architectures.

## Inputs

- The output of [`repository-discovery`](../repository-discovery/SKILL.md)
  (required — this skill does not run against an un-inspected repository).
- Any existing `.ai/ARCHITECTURE.md` or ADRs in the client repository.
- The business/technical objective driving the review, if one was given.

## Preconditions

- Repository discovery has already produced an evidence-based inventory.

## Procedure

1. Build a current-state architecture description strictly from the
   discovery inventory (ingestion, storage, transformation, orchestration,
   serving, semantic models, reporting, APIs, monitoring, CI/CD, security,
   governance).
2. Identify risks and technical debt, each tied to specific observed
   evidence.
3. Propose a target architecture appropriate to the observed scale,
   constraints, and (where known) team/budget.
4. Propose credible alternatives, not just the one preferred option.
5. Compare current/target/alternatives on: scalability, availability,
   disaster recovery, cost, operational complexity, security, governance.
6. Recommend a target with explicit reasoning.
7. Flag candidate ADRs for decisions that matter.
8. Sketch a migration roadmap only if a change is actually being
   recommended.

## Decision Criteria

- Use qualitative classifications: Strong / Acceptable / Needs improvement
  / High risk / Critical. Never invent numerical scores without a
  documented scoring model.
- Prefer Fabric-native capabilities when they meet the requirement without
  unnecessary operational complexity.
- Apply [Kimball](../../standards/kimball.md) to analytical Gold/serving
  layers and semantic models by default — not to Bronze/Silver/staging.
- Do not mechanically recommend Medallion, Data Vault, Lakehouse or
  microservices patterns; justify against the observed context every
  time.
- Label every recommendation as **Required fix**, **Best practice**,
  **Good practice**, or **Project-specific recommendation**.

## Evidence Required

Every risk and recommendation traces back to specific discovery findings.
No claim about the current state may exceed what discovery actually
found.

## Output Format

Follows [Architecture Comparison Output](../../standards/architecture.md#architecture-comparison-output):
Current state → Problems → Root causes → Risks → Technical debt →
Recommended target → Alternatives → Advantages/disadvantages → Migration
complexity → Cost/performance/security/operational implications →
Migration roadmap → ADR candidates.

## Quality Checks

- Every current-state claim is traceable to discovery evidence.
- At least one real alternative is presented, not only the preferred
  option.
- Trade-offs are stated for every option, including the recommended one.
- Recommendation labels (Required fix / Best practice / Good practice /
  Project-specific) are used consistently.

## Common Failure Modes

- Recommending a target architecture the client cannot realistically
  operate given observed team size/maturity.
- Treating "best practice" and "required" as interchangeable.
- Comparing architectures using invented numerical scores.

## Escalation / Specialist Handoff

For dimensional-model-specific concerns, hand off to
[`kimball-review`](../kimball-review/SKILL.md). ADR candidates become
repository artifacts using [`templates/ADR.md`](../../templates/ADR.md).
