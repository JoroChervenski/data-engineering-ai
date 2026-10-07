# AGENTS.md — data-engineering-ai (framework repository)

This file instructs any coding agent (human-supervised or autonomous)
working **inside this repository**. It does not describe how to work
inside a client repository — that is the client repository's own
`AGENTS.md`, generated from `templates/AGENTS.md`.

## What this repository is

A reusable, generic framework of agent roles, skills, engineering
standards, templates and commands for AI-assisted data engineering
consulting work, with a strong focus on Microsoft Fabric and Kimball
dimensional modelling. See [README.md](README.md) for the full picture.

## Rules for anyone editing this repository

1. **No client-specific confidential information, ever.** No client
   names, tenant/subscription IDs, environment URLs, real data, business
   rules specific to one engagement, or credentials of any kind. If a
   piece of knowledge only makes sense for one client, it belongs in that
   client repository's `.ai/` overlay, not here.
2. **Generic logic belongs in `skills/` and `standards/`.** Reusable
   procedures go in `skills/<name>/SKILL.md`; engineering principles and
   rules of thumb go in `standards/<name>.md`. Do not re-explain the same
   procedure or principle inside multiple files — link instead.
3. **Personas and responsibilities belong in `agents/`.** An agent file
   says *who is accountable for what*, and which skills/standards it
   relies on. It should not contain a full copy of a procedure that
   already lives in a skill.
4. **Commands orchestrate skills and agents.** A command in `commands/`
   describes a workflow: inputs, which skills/agents it invokes, ordered
   steps, outputs and safety constraints. It should not re-implement a
   skill's procedure inline.
5. **Templates must remain generic.** Files under `templates/` are filled
   in *per client repository*. They must never ship with example content
   that looks like a real client, a real tenant, or real data.
6. **Secrets are forbidden.** No secrets, tokens, passwords, keys,
   connection strings or tenant/subscription identifiers anywhere in this
   repository, including inside examples. See
   [`standards/security.md`](standards/security.md).
7. **Work incrementally.** Do not attempt to build the full target
   structure (see the implementation spec, section 7) in one pass. Follow
   the phase defined in the spec; do not start a later phase without
   explicit instruction.
8. **Tests/validation must accompany meaningful changes.** When adding or
   changing an agent, skill, standard, template or command, re-check: all
   required files for the current phase exist, every Markdown link
   resolves, terminology (severities, Kimball terms, security terms) stays
   consistent across files, and no client-specific data or secrets were
   introduced. A dedicated `tests/` directory is introduced once there is
   an automatable check worth running in CI — not before.
9. **Do not duplicate instructions unnecessarily.** If the same guidance
   is about to be written in two places, link to the single canonical
   location instead.
10. **Prefer evidence over invention.** Any skill or command that produces
    a repository-facing artifact (overlay docs, manifests, reviews) must
    clearly separate observed facts from inference, and must never invent
    architecture, data or configuration that was not actually observed.

## Current phase

**Phase 1 — Foundation.** Scope, rationale and the full phase roadmap are
defined in `AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md`. Do not
implement Phase 2 or later, and do not add external tool/MCP integrations,
without an explicit instruction to do so.
