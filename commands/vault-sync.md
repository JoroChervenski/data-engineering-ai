---
description: "Mirror this repo's .ai/ overlay, tickets, ADRs and runbooks read-only into its Obsidian project folder, following the Project Standard"
argument-hint: "[--dry-run] [--refresh-conventions]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/vault-sync`

## Purpose

Copy the repo's project facts into the project's own folder in the Obsidian vault, in the layout the
Project Standard defines. The repo stays the source of truth; the vault holds read-only copies next to the
notes you write by hand.

## Expected Inputs

- A repo created from the client template: `.ai/vault-sync.json` names the project, the repo and the vault
  folder.
- The Project Standard mounted at `/vault/Knowledge` (read-only) and the project's vault folder mounted
  at `/vault/<Project>`.
- Optionally `--dry-run` or `--refresh-conventions` in the arguments.

## Skills / Roles Invoked

None. This command runs one script, [`scripts/vault_sync.py`](../scripts/vault_sync.py), which reads the
layout from the standard.

## Ordered Execution Steps

1. Check that `.ai/vault-sync.json` exists. If not, stop: this repo was not created from the template.
2. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vault_sync.py" --repo-root . --dry-run` when the arguments ask
   for a dry run or when the project's hub note does not exist yet. Show the counts and any orphaned
   mirrors, and ask before the real run.
3. Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/vault_sync.py" --repo-root .` with the arguments.
4. Report the standard version and commit it used, the counts of created, updated and unchanged notes, and
   every orphaned mirror.

## Expected Output

One summary line from the script, plus a list of orphaned mirrors (notes whose source file no longer
exists). Orphans are reported, never deleted: the user decides.

## Safety Constraints

- The script writes only inside the project's own vault folder and stops without writing if the standard is
  missing or invalid, or if the vault folder is not the project's.
- Never edit a mirror in the vault to "fix" it; change the repo file and run the sync again.
- Never mount or read another project's vault folder.
- If the script fails, report its message as it is. Do not work around it by writing vault files by hand.

## Request

$ARGUMENTS
