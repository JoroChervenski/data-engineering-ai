---
description: "Run a ticket end to end (intake, discovery, approved plan, implementation, tests, independent review, PR text, learnings) with its state kept in a ticket note, so it can be resumed"
argument-hint: "<TICKET-ID> [ticket text]"
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/commands/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# `/ticket`

## Purpose

Run one ticket through the full workflow, in the main conversation, with
its state kept in a ticket note in the overlay. Running `/ticket` again
with the same ID resumes from where the note says the work stopped.

## Expected Inputs

- The ticket ID, and the ticket text the first time (there is no ticket
  tracker integration yet, so ask for the text if only an ID is given and
  no note exists).
- The client repository, open, with its overlay (`AGENTS.md` +
  `.ai/`). Without an overlay, offer
  [`/bootstrap-project`](bootstrap-project.md) first.

## Skills / Roles Invoked

- [`orchestration`](../skills/orchestration/SKILL.md) throughout: it
  decides which of the roles below each ticket actually needs.
- [`repository-discovery`](../skills/repository-discovery/SKILL.md) via the
  [Repository Analyst](../agents/repository-analyst.agent.md), for an
  unfamiliar area.
- [`implementation-plan`](../skills/implementation-plan/SKILL.md), and the
  [Architect](../agents/architect.agent.md) only for a real trade-off.
- [Data Engineer](../agents/data-engineer.agent.md) rules for
  implementation; [`testing`](../skills/testing/SKILL.md).
- [Reviewer](../agents/reviewer.agent.md) via
  [`code-review`](../skills/code-review/SKILL.md), plus
  [`kimball-review`](../skills/kimball-review/SKILL.md) if a dimensional
  or semantic model is touched.
- [`pull-request`](../skills/pull-request/SKILL.md);
  [`capture-learnings`](../skills/capture-learnings/SKILL.md) at close.

## Ordered Execution Steps

0. **Locate the note.** Read the overlay's note conventions (`AGENTS.md`,
   `.ai/manifest.yaml` `notes.tickets`; default `.ai/tickets/`). The note
   is `<TICKET-ID>.md`. If it exists, read it, report its status and last
   log entry, and resume at the matching step below. If it has
   uncommitted changes from an interrupted session, commit them first
   (see "Committing the note" below) as `<TICKET-ID>: changes from an
   interrupted session`. Statuses are those of
   [`templates/TICKET.md`](../templates/TICKET.md) unless the overlay
   defines its own.
1. **Intake** (new ticket). Create the note from
   [`templates/TICKET.md`](../templates/TICKET.md), following the
   overlay's frontmatter conventions. Record the ticket text, the
   acceptance criteria and the open questions. Status `open`.
2. **Context.** Run [`orchestration`](../skills/orchestration/SKILL.md)
   steps 1–4: classify the ticket, run discovery for the affected area if
   it is unfamiliar, and record what was found under Context, labelled
   O/I/U.
3. **Plan and approval gate.** Produce the plan with
   [`implementation-plan`](../skills/implementation-plan/SKILL.md), write
   it into the note, and **stop until the user approves it**. Record the
   approval in the note. Unresolved blocking questions keep the ticket at
   this step.
4. **Branch.** Create or switch to a branch that follows the overlay's
   naming convention. Never work on the default, shared or production
   branch. Record the branch in the frontmatter. Status `in-progress`.
5. **Implement** in the main conversation, within the approved plan and
   the overlay's constraints and protected directories. Log each decision
   in the note as it is made. Anything outside the plan goes back to the
   user first.
6. **Test** with [`testing`](../skills/testing/SKILL.md) and the test
   commands the overlay requires. Log the exact commands and their real
   results; never record a test as passed that did not run.
7. **Review.** Run the Reviewer as a subagent with the diff range, the
   plan and the ticket's acceptance criteria. Fix Critical/High findings,
   or keep them open with the user's decision recorded. Status `review`.
8. **PR text.** Build the description with
   [`pull-request`](../skills/pull-request/SKILL.md). Commit, push or open
   the PR only when the user asks, within their configured permissions.
   Record the PR link in the frontmatter once it exists.
9. **Close** (when the user says the ticket is merged or done). Run
   [`capture-learnings`](../skills/capture-learnings/SKILL.md) for this
   ticket, then set status `done`.

Throughout: add a dated line under Log at every step, and add a line
under Learning Candidates as soon as the user corrects something, or an
overlay fact proves wrong or missing. The conversation may be gone by
step 9; the note will not.

**Committing the note.** At the end of every step that changed the note,
commit it, when the overlay has its own Git repository (how to tell:
[`capture-learnings`](../skills/capture-learnings/SKILL.md), step 6).
Commit the note's path only, with a message naming the ticket and the
step, for example `ABC-123: plan approved`:

```bash
git -C <overlay> add -- <note>
git -C <overlay> commit -m "<TICKET-ID>: <step>" -- <note>
```

These commits need no separate approval: they are local, touch only the
note, and give it a history. If the overlay is committed in the client
repository instead, leave the note uncommitted for the user's normal
change process. If the overlay is not versioned at all, say so once.

## Expected Output

Per step: what was done, what the note now says, and the next gate or
step. At the end, the PR description and the capture-learnings summary.

## Safety Constraints

- No file in the client repository is edited before the plan is approved
  (step 3). The ticket note itself is the only exception.
- Approval of the plan is not approval to commit, push, open a PR,
  deploy, or run anything against a cloud environment.
- The only commits this command makes without asking are the ticket-note
  commits above, in an overlay that has its own repository. Nothing is
  committed in the client repository unless the user asks.
- The overlay's critical constraints and approval gates apply at every
  step, and win over this command where they are stricter.
- No secrets, tokens or tenant, workspace or connection IDs in the note.

## Request

$ARGUMENTS
