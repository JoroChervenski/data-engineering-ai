---
name: repository-discovery
description: "Evidence-based inventory of a repository before any architecture or implementation decision. Use when the repository or the relevant area has not been inspected in this session, before architecture-assessment, implementation-plan or bootstrap-project, or when previously observed structure may be stale."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/repository-discovery/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Repository Discovery

## Purpose

Produce an evidence-based inventory of a repository before any
architectural or implementation decision is made, so decisions are based
on what is actually there rather than on assumption or memory of similar
projects.

## When to Use

- The repository (or the relevant area of it) has not been inspected in
  the current working session.
- Before [`architecture-assessment`](../architecture-assessment/SKILL.md),
  [`implementation-plan`](../implementation-plan/SKILL.md), or
  [`/bootstrap-project`](../../commands/bootstrap-project.md).
- Whenever there is reason to doubt that previously observed structure is
  still current.

## Inputs

- Read access to the repository working tree.
- The repository's `.ai/` overlay, if one already exists (treat it as a
  starting hypothesis to verify, not as ground truth).

## Preconditions

- None beyond read access. This skill never requires write access.

## Procedure

1. Inventory top-level structure: directories, root files, obvious
   project markers (package manifests, Fabric item folders, pipeline
   definitions, infra-as-code).
2. Detect technologies/languages/platform services actually present
   (import statements, config files, file extensions, Fabric item types,
   CI/CD definitions) — do not infer a technology from the client's
   industry or from a similar past project.
3. Identify likely entry points: jobs, notebooks, pipeline definitions,
   application entry files.
4. Identify configuration: where it lives, whether it is
   environment-specific, whether secrets appear to be handled correctly
   (flag, don't fix, unless asked).
5. Identify data sources/targets where inferable from code or config.
6. Identify orchestration/pipelines in use.
7. Identify testing: frameworks, coverage areas, what is conspicuously
   untested.
8. Identify deployment mechanism, if observable (CI/CD definitions,
   deployment pipelines, environment folders).
9. Identify semantic model / Microsoft Fabric artifacts if present
   (Lakehouse, Warehouse, semantic model, Direct Lake usage, Dataflows,
   Eventstream, etc.).
10. Reconstruct dependencies and data flows from what was actually
    observed; mark any gap explicitly rather than filling it.
11. Flag possible dead/obsolete code as a hypothesis, not a fact.
12. List documentation gaps and open questions a human should resolve.

## Decision Criteria

- A claim is **Observed** only if it was seen directly in a file, config,
  or command output.
- A claim is **Inferred** if it follows from observed evidence but was not
  seen directly (e.g., "likely append-only load, based on the absence of
  any delete/merge logic").
- Anything else is **Unknown** and must be stated as such, never guessed.

## Evidence Required

Every inventory item cites what was inspected (file path, directory,
config key) to produce it. No unsupported claims.

## Output Format

```text
## Technologies (Observed)
## Key Directories/Files
## Entry Points
## Configuration
## Data Sources / Targets (Observed / Inferred)
## Orchestration / Pipelines
## Testing
## Deployment
## Semantic Model / Fabric Artifacts
## Dependencies & Data Flows (Observed / Inferred)
## Possible Dead/Obsolete Code (flagged, unconfirmed)
## Documentation Gaps
## Open Questions
```

## Quality Checks

- Every section separates Observed from Inferred from Unknown.
- No claim traces back to "likely because similar projects do this."
- No client-specific terminology leaked in from a different repository.

## Common Failure Modes

- Treating a previous session's understanding as still valid without
  re-checking.
- Filling an unknown with a plausible-sounding guess instead of marking it
  unknown.
- Reporting framework conventions (e.g., a typical Medallion layout) as if
  they were observed when they were assumed.

## Escalation / Specialist Handoff

Hand the resulting inventory to the
[Architect agent](../../agents/architect.agent.md) for architecture
reasoning, or to the
[Data Engineer agent](../../agents/data-engineer.agent.md) via
[`implementation-plan`](../implementation-plan/SKILL.md) for
implementation planning. This skill itself produces no recommendations.
