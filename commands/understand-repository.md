# `/understand-repository`

## Purpose

Run repository discovery and return a structured project model of the
current repository, without making any architecture recommendation or
code change.

## Expected Inputs

- The target repository, open and accessible.
- Optionally, a specific area of interest to focus discovery on.

## Skills / Roles Invoked

- [Repository Analyst agent](../agents/repository-analyst.agent.md) via
  [`repository-discovery`](../skills/repository-discovery/SKILL.md).

## Ordered Execution Steps

1. Run the full [`repository-discovery`](../skills/repository-discovery/SKILL.md)
   procedure.
2. Cross-check against any existing `.ai/` overlay if present; note any
   drift between the overlay and what was actually observed, without
   silently trusting the overlay over current observation.
3. Return the structured inventory in the skill's defined output format.

## Expected Output

The repository-discovery output format: Technologies, Key
Directories/Files, Entry Points, Configuration, Data Sources/Targets,
Orchestration/Pipelines, Testing, Deployment, Semantic Model/Fabric
Artifacts, Dependencies & Data Flows, Possible Dead/Obsolete Code,
Documentation Gaps, Open Questions — each item marked Observed, Inferred,
or Unknown.

## Safety Constraints

- Read-only. No files are modified.
- No architecture recommendation is made here — that belongs to
  [`/architecture-review`](architecture-review.md).
