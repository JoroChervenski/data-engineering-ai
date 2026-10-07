# AI-Assisted Data Engineering Consulting Platform

## What this is

A reusable framework of agent definitions, skills, standards, templates and
commands that helps an AI coding agent act like a disciplined virtual
Principal Data Engineering team inside a client repository — grounded in
that repository's actual state, proficient in the Microsoft data platform
(Microsoft Fabric, Azure, Power BI, SQL, Python, PySpark), and built around
Kimball dimensional modelling as the default analytical standard.

It is designed to be bootstrapped into any number of separate client
repositories without ever mixing client context between them.

## What this is not

- Not a client repository. It must never contain client-specific business
  facts, architecture, credentials, tenant/subscription identifiers or data.
- Not a single giant system prompt. Responsibilities are split across
  agents (roles), skills (procedures) and standards (engineering principles).
- Not a fully automated deployment system. Production-changing operations
  stay human-controlled until that is explicitly changed in a later phase.
- Not a finished platform. This repository currently implements **Phase 1 —
  Foundation** only (see [Implementation status](#implementation-status)).

## Architecture

Five logical layers, from the user-facing surface down to concrete tools:

```mermaid
flowchart TD
    A[Experience Layer\nVS Code + Chat + Commands + Git Diff] --> B
    B[Orchestration Layer\nOrchestrator + Context Builder + Router + Review Gate] --> C
    C[Agent Layer\nRoles: Architect, Repository Analyst, Data Engineer, Reviewer, ...] --> D
    D[Skill Layer\nReusable procedures: discovery, Kimball review, testing, PR, ...] --> E
    E[Tool Layer\nGit, GitHub/Azure DevOps, Fabric, Azure, SQL, Power BI, CI/CD]
```

Each client repository that uses this framework forms its own separate
context and security boundary. The framework is invoked *against* a client
repository; it never stores that repository's facts itself.

## Agents vs. skills

- An **agent** (`agents/*.agent.md`) is a role or responsibility — *who* is
  reasoning and what it is accountable for.
- A **skill** (`skills/*/SKILL.md`) is a reusable, repeatable procedure —
  *how* a task gets done, including inputs, evidence requirements, and
  quality checks.
- A skill may be used by more than one agent. Procedures are not duplicated
  across agent prompts; agents reference skills instead.

## Client isolation

This framework repository holds **generic, reusable engineering knowledge
only**. It must never contain:

```text
data-engineering-ai/
└── projects/
    ├── client-a/
    ├── client-b/
    └── client-c/
```

Instead, each client gets its own physically separate repository with a
thin AI overlay (`AGENTS.md` + `.ai/`) created from this framework's
`templates/`. A typical working layout looks like:

```text
work/
├── data-engineering-ai/      <- this repository
├── client-a/
│   └── repo-1/
├── client-b/
│   └── repo-1/
└── client-c/
    └── repo-1/
```

Client-specific facts, rules, glossary, technical debt and decisions live
inside the corresponding client repository's `.ai/` directory — never here,
and never copied from one client repository into another.

## How to bootstrap a client repository

1. Open the target client repository in VS Code alongside this framework.
2. Run the [`/bootstrap-project`](commands/bootstrap-project.md) command.
3. The agent inspects the client repository first (it must not invent
   facts), then proposes a client `AGENTS.md` and a `.ai/` overlay
   (`PROJECT.md`, `ARCHITECTURE.md`, `DATA-MODEL.md`, `GLOSSARY.md`,
   `STANDARDS.md`, `TECH-DEBT.md`, `manifest.yaml`, `adr/`, `runbooks/`)
   from this framework's `templates/`.
4. Anything that cannot be determined from the repository is marked as
   unknown, not guessed.
5. The client repository owner reviews and commits the overlay like any
   other change.

## How to use commands

Commands (`commands/*.md`) are reusable workflows that chain skills and
agents together. Phase 1 ships:

| Command | Purpose |
|---|---|
| [`/bootstrap-project`](commands/bootstrap-project.md) | Create a client repository's AI overlay from templates |
| [`/understand-repository`](commands/understand-repository.md) | Run repository discovery and produce a structured project model |
| [`/architecture-review`](commands/architecture-review.md) | Run discovery plus a qualitative architecture review |
| [`/plan-ticket`](commands/plan-ticket.md) | Produce an implementation plan without changing files |
| [`/review-pr`](commands/review-pr.md) | Review a diff/branch as a senior/principal engineer |
| [`/review-data-model`](commands/review-data-model.md) | Review a dimensional/semantic model against Kimball standards |
| [`/investigate`](commands/investigate.md) | Run evidence-driven incident / root-cause analysis |
| [`/prepare-pr`](commands/prepare-pr.md) | Build a PR description from the actual diff/tests/reviews |

A small Python bug does not need every specialist invoked. The
[Orchestrator](agents/orchestrator.agent.md) classifies the task first and
invokes only the agents/skills the task actually requires.

## Implementation status

**Phase 1 — Foundation (current).** Minimal, coherent framework: 5 core
agents, 8 Phase 1 skills, 8 engineering standards, 9 client-overlay
templates, 8 commands. Enough to reliably bootstrap one real client
repository and run the core workflows above.

Not yet implemented (by design — see the roadmap below):

- Deep/expanded behavior for every agent and skill (Phase 2).
- Specialist agents beyond the Phase 1 five, e.g. Fabric Architect, SQL
  Specialist, Spark Specialist, Semantic Model Specialist, Security
  Reviewer, Production Reliability Reviewer, DevOps Agent, PR Agent
  (Phase 3).
- External tool/MCP integrations: GitHub, Azure DevOps, Microsoft Fabric,
  Azure, Power BI, SQL (Phase 4).
- Controlled write automation: branches, commits, pushes, PRs, pipeline
  triggers (Phase 5).
- Advanced automation: automated PR review, drift detection, semantic-model
  linting, CI enforcement (Phase 6).

## Roadmap

See `AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md` for the full
phased plan (Phases 2–6). Each phase is only implemented after the
previous one has been reviewed; later phases are not started implicitly.

## Safety model

- **Repository truth over AI memory.** Architectural and implementation
  decisions are based on the current state of the repository being worked
  on, not on previously observed state.
- **Strict client isolation.** Generic framework vs. client-specific
  overlay, enforced by directory structure and by the agent/skill
  instructions themselves.
- **Git is the system of record.** Decisions that matter become reviewable
  repository artifacts (code, tests, docs, ADRs, PR descriptions) rather
  than an undocumented AI-only knowledge layer.
- **Least privilege.** Tools are conceptually leveled L0 (read) through L3
  (deploy). Phase 1 only requires L0/L1 (observe, modify local working
  tree). Remote writes and cloud deployment stay human-controlled.
- **No secrets, ever.** Never in `AGENTS.md`, manifests, documentation,
  prompts, skill or agent definitions. See
  [`standards/security.md`](standards/security.md).
- **Human review stays in the loop.** Agents prepare plans, diffs and PR
  descriptions; they do not auto-approve or auto-merge.
