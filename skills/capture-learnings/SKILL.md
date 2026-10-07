---
name: capture-learnings
description: "Turn what was learned during a ticket or session into approved updates: project-specific facts go into the client's .ai/ overlay, generic lessons go (anonymised) into the framework's inbox for later promotion. Use when a ticket closes, after a session that corrected the overlay or the framework, or when the user asks to capture learnings."
argument-hint: "[TICKET-ID]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/capture-learnings/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Capture Learnings

## Purpose

Keep the client overlay and the framework improving from real work,
without breaking client isolation or letting unreviewed AI notes become
project truth. Every change is proposed with its evidence and applied
only after the user approves it.

## When to Use

- At step 9 of [`/ticket`](../../commands/ticket.md).
- After a session in which the user corrected the agent, or the overlay
  proved wrong, missing or stale.
- When the user asks to capture learnings.

## Inputs

- The ticket note's Learning Candidates, Decisions and Log, if a ticket
  is given.
- The branch diff against the default branch and its commit messages.
- Review findings for the change.
- Corrections and decisions from the current conversation.
- The overlay (`AGENTS.md`, `.ai/`).

## Preconditions

- The current working directory is the client repository whose overlay
  is being updated.
- The framework inbox is the owner's **working clone** of the framework,
  named by the environment variable `DATA_ENGINEERING_AI_SRC`
  (`$DATA_ENGINEERING_AI_SRC/inbox/`). Never write to
  `${CLAUDE_PLUGIN_ROOT}`: it is a managed install that is replaced on
  every update. If the variable is unset or the folder is missing, show
  the inbox items to the user instead of writing them.

## Procedure

1. **Gather** the inputs above. List each candidate lesson in one line
   with its evidence (file and line, commit, review finding, or the
   user's correction).
2. **Classify** each candidate:

   | Class | Test | Goes to |
   |---|---|---|
   | Project | True only for this client or repository | The `.ai/` document that owns it (table below) |
   | Framework | Would hold, unchanged, in an unrelated client's repository | `$DATA_ENGINEERING_AI_SRC/inbox/`, anonymised |
   | Drop | One-off, already recorded, or not supported by evidence | Nowhere; say why |

   One event can yield both: a project fact and a generic lesson.
3. **Project updates.** Map each to its owner document:

   | Lesson | Document |
   |---|---|
   | Hard constraint, protected path, approval gate | `AGENTS.md` |
   | Convention, project-specific rule | `.ai/STANDARDS.md` |
   | Debt found or resolved | `.ai/TECH-DEBT.md` (add, or change Status) |
   | Business term | `.ai/GLOSSARY.md` |
   | Table, grain, key, relationship | `.ai/DATA-MODEL.md` |
   | Component, flow, integration | `.ai/ARCHITECTURE.md` |
   | Decision worth keeping | `.ai/adr/` from [`templates/ADR.md`](../../templates/ADR.md) |
   | Repeatable operational procedure | `.ai/runbooks/` |

   Write the smallest edit that records the fact, labelled O/I/U and
   citing its evidence. Correct a wrong statement in place rather than
   appending a contradiction. Never delete content silently: mark it
   superseded or resolved.
4. **Framework items.** Rewrite each one without client names, people,
   IDs, URLs, table, column or item names, business rules or data. The
   lesson must read as generic engineering guidance. Check it against
   the project's own terms (project name, ticket prefix, glossary terms)
   and remove any that remain. Then look in the inbox for an item on the
   same lesson: if one exists, increment its `seen`, update `last_seen`
   and add an anonymised evidence line; otherwise create one per
   [`inbox/README.md`](../../inbox/README.md).
5. **Present everything before writing**: the proposed overlay diffs, the
   inbox items as they will be written, and the dropped candidates with
   reasons. **Wait for the user's approval**; apply only what they
   approve.
6. **Version the overlay.** Find out how the overlay is versioned before
   writing: committed in the client repository (`.ai/` changes show in
   its `git status`), its own repository (`git -C .ai rev-parse
   --show-toplevel` is not the client repository root), or not versioned
   (warn the user). In its own repository, commit the approved changes
   there with a message naming the ticket. In the client repository,
   leave them uncommitted for the user's normal change process.
7. **Close the loop.** Tick each processed Learning Candidate in the
   ticket note and record where it went (`→ .ai/STANDARDS.md`,
   `→ inbox/<file>`, `→ dropped: <reason>`). Set `overlay.last_learning_capture`
   in `.ai/manifest.yaml` to today's date, the current client commit and
   the ticket ID.

## Decision Criteria

- A lesson that is only plausible, not evidenced, is dropped or recorded
  as an open question, never written as a fact.
- When in doubt between Project and Framework, choose Project. Generic
  value can be extracted later; client data cannot be un-leaked.
- A repeated lesson raises the existing inbox item's `seen` count; it
  does not create a duplicate.

## Evidence Required

Every proposed change cites where the lesson came from. Framework items
cite anonymised evidence only.

## Output Format

```text
## Project Updates (proposed diffs, with evidence)
## Framework Inbox Items (as they will be written)
## Dropped (with reasons)
## Applied (after approval: files changed, overlay commit if any)
```

## Quality Checks

- No framework item contains a client name, ticket prefix, person, ID,
  URL, table, column or item name.
- No secret, token or tenant, workspace or connection ID was written
  anywhere.
- Every processed Learning Candidate is ticked with its destination.
- Nothing was written before the user approved it.

## Common Failure Modes

- Writing the user's offhand remark into the overlay as a standing rule.
  Confirm that a correction is meant to apply beyond this task.
- Anonymising only the obvious names and leaving a table name, a ticket
  prefix or a business rule in a framework item.
- Recording lessons in the conversation only, where the next session
  will not see them.
- Appending a new statement that contradicts an existing one instead of
  correcting the original.

## Escalation / Specialist Handoff

A lesson that changes architecture or the data model goes through the
[Architect](../../agents/architect.agent.md) or
[`kimball-review`](../kimball-review/SKILL.md) before it is recorded as
the new truth. Promoting inbox items into framework files happens in the
framework repository, per its `AGENTS.md`.
