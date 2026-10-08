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
7. **Work incrementally, driven by real tasks.** Do not attempt to build
   the full target structure (see the implementation spec, section 7) in
   one pass. Improving existing agents, skills, standards, templates and
   commands is allowed whenever the owner asks for it, typically by
   promoting an [`inbox/`](inbox/README.md) item. New specialist agents
   (Phase 3), external tool/MCP integrations (Phase 4) and write or
   deploy automation (Phase 5 and later) still need explicit instruction.
   The four hardening workstreams (W1 client template, W2 hooks and
   policies, W3 verifier and evals, W4 versioning and release) are tracked
   in [`docs/workstream-gap-analysis.md`](docs/workstream-gap-analysis.md)
   and are started one at a time, on explicit instruction.
8. **Tests/validation must accompany meaningful changes.** When adding or
   changing an agent, skill, standard, template, script or command, run
   `python3 tests/validate_framework.py` and
   `python3 -m unittest discover -s tests`. The validator checks that every
   Markdown link resolves, that every JSON file parses, that agents, skills
   and commands carry the frontmatter Claude Code needs, and that no
   secret-like strings or client terms (from the untracked `.client-terms`
   file) were introduced. The unit tests cover the client template,
   `scripts/new_client.py` and `scripts/vault_sync.py`; set `KNOWLEDGE_DIR`
   to the vault's `Knowledge` folder to also compare the pinned standard
   snapshot in `tests/fixtures/standard` with the real one. Also re-check by
   hand that terminology (severities, Kimball terms, security terms) stays
   consistent across files.
9. **Do not duplicate instructions unnecessarily.** If the same guidance
   is about to be written in two places, link to the single canonical
   location instead.
10. **Prefer evidence over invention.** Any skill or command that produces
    a repository-facing artifact (overlay docs, manifests, reviews) must
    clearly separate observed facts from inference, and must never invent
    architecture, data or configuration that was not actually observed.
11. **The vault is read-only, and only two folders of it.** What every
    project MUST have is the Project Standard in the Obsidian vault's
    `Knowledge/` folder. This repository implements it (the client
    template, `scripts/new-client.sh`, `scripts/vault_sync.py`, the tests)
    and does not copy its text: link to it or test against it. You may read
    `Knowledge/` and `Templates/`. Never read, write, mount or ask for the
    vault's `Projects/` folder or `Home.md`; project facts live in the
    client repository and its own vault folder. Do not run
    `scripts/new-client.sh` yourself: the person creating a project runs it
    on the host.

## Current phase

**Phase 1 — Foundation, with task-driven Phase 2 improvements** (see rule
7), plus hardening workstream W1, the client template. Scope, rationale and the full phase roadmap are defined in
`AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md`. Do not add
specialist agents, external tool/MCP integrations or write automation
without an explicit instruction to do so.

## Inbox

[`inbox/`](inbox/README.md) holds anonymised lessons that the
[`capture-learnings`](skills/capture-learnings/SKILL.md) skill files from
client work. When asked to process it: promote the items that meet the
promotion rule in `inbox/README.md` by editing their target files, mark
each item promoted or rejected, run the validator, and stop before
committing so the owner can review the diff.
