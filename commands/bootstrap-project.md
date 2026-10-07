# `/bootstrap-project`

## Purpose

Create a client repository's AI overlay (`AGENTS.md` + `.ai/`) from this
framework's templates, grounded in the repository's actual state.

## Expected Inputs

- The target client repository, open and accessible.
- Optionally, a stated business objective/context the bootstrap should
  record under "Known Facts" — not required to proceed.

## Skills / Roles Invoked

- [Repository Analyst agent](../agents/repository-analyst.agent.md) via
  [`repository-discovery`](../skills/repository-discovery/SKILL.md)
  (required first step).
- [Orchestrator agent](../agents/orchestrator.agent.md) to sequence the
  rest.

## Ordered Execution Steps

1. Run repository discovery. Do not proceed to filling any template
   before this step has produced an evidence-based inventory.
2. Check whether an `.ai/` overlay already exists. If it does, treat its
   content as a hypothesis to verify against current discovery output,
   not as already-correct — update rather than blindly overwrite.
3. Propose `AGENTS.md` at the repository root from
   [`templates/AGENTS.md`](../templates/AGENTS.md), filled only with what
   discovery actually found. Mark anything else Unknown.
4. Propose `.ai/PROJECT.md`, `.ai/ARCHITECTURE.md`, `.ai/DATA-MODEL.md`,
   `.ai/GLOSSARY.md`, `.ai/TECH-DEBT.md` from their respective templates,
   same rule.
5. Propose `.ai/STANDARDS.md` — a short pointer file naming which of this
   framework's `standards/*.md` apply to this project, plus any
   project-specific additions.
6. Propose `.ai/manifest.yaml` from
   [`templates/manifest.yaml`](../templates/manifest.yaml), filled only
   with observed values; leave the rest as the template's defaults/
   unknown markers. Never add credentials, tokens, tenant/subscription
   IDs beyond what the template itself allows.
7. Create empty `.ai/adr/` and `.ai/runbooks/` directories only if the
   repository is expected to actually use them soon; otherwise note them
   as "to be created when first needed" rather than adding empty
   placeholder directories.
8. Present the proposed overlay to the user for review before committing
   it — this command proposes; a human (or an explicit follow-up
   instruction) commits.

## Expected Output

A proposed `.ai/` overlay and root `AGENTS.md`, each clearly marking
Observed vs. Inferred vs. Unknown content, plus a short list of open
questions the bootstrap could not resolve from the repository alone.

## Safety Constraints

- Never invent architecture, data, or business facts to fill a template
  section. Unknown stays Unknown.
- Never copy content from another client repository's overlay.
- Never include secrets, tenant/subscription IDs, or real client data
  beyond what is already appropriately present in the repository being
  bootstrapped.
- Does not commit on its own; the proposed files are presented for
  review first.
