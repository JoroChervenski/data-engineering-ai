---
description: "Create this client repository's AI overlay (AGENTS.md + .ai/) from the framework templates, grounded in discovery"
argument-hint: "[business objective or context]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

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
- [`orchestration`](../skills/orchestration/SKILL.md) skill to sequence the
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
   unknown markers. Record the date and client commit under
   `overlay.bootstrapped`. Keep `framework` and `standard` as the creation
   script stamped them, or fill them from the framework `VERSION` and the
   mounted Project Standard if they are still `unknown`. Never add credentials, tokens,
   tenant/subscription IDs beyond what the template itself allows.
7. Create empty `.ai/adr/`, `.ai/runbooks/` and `.ai/tickets/`
   directories only if the repository is expected to actually use them
   soon (`.ai/tickets/` when [`/ticket`](ticket.md) will be used);
   otherwise note them as "to be created when first needed" rather than
   adding empty placeholder directories.
8. Agree with the user how the overlay is versioned: committed in the
   client repository (the default), or kept out of it (for example in a
   personal notes folder). An overlay kept out of the client repository
   should have its own Git repository, unless the user chooses to keep it
   unversioned, so that later edits by
   [`capture-learnings`](../skills/capture-learnings/SKILL.md) have a
   history and can be undone. Agree also whether overlay updates are
   proposed for approval first (`propose`, the default) or written
   straight away (`direct`), and record it as `overlay.write_mode` in the
   manifest.
9. A first bootstrap is always presented to the user for review before
   it is written or committed. Later runs on an existing overlay follow
   its `overlay.write_mode`: `propose` presents the changes first;
   `direct` writes them, lists what changed, and runs the independent
   check from [`capture-learnings`](../skills/capture-learnings/SKILL.md)
   step 8. Committing follows the versioning agreed in step 8.

## Expected Output

The `.ai/` overlay and root `AGENTS.md` (proposed, or written in direct
mode), each clearly marking
Observed vs. Inferred vs. Unknown content, plus a short list of open
questions the bootstrap could not resolve from the repository alone.

## Safety Constraints

- Never invent architecture, data, or business facts to fill a template
  section. Unknown stays Unknown.
- Never copy content from another client repository's overlay.
- Never include secrets, tenant/subscription IDs, or real client data
  beyond what is already appropriately present in the repository being
  bootstrapped.
- Does not commit on its own. Files are presented for review first,
  except updates to an existing overlay in `direct` mode, which are
  written and then checked by the reviewer.

## Request

$ARGUMENTS
