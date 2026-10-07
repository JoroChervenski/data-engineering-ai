---
name: orchestration
description: "Entry point for multi-step data engineering work in a client repository, run in the main conversation: classifies the request, checks the .ai/ overlay, picks the smallest sufficient set of framework subagents/skills, plans the order, stops at human approval gates and enforces the review gate. Use when a request spans several roles (discovery, design, implementation, review), and from /ticket."
---

> **Claude Code plugin:** the framework is installed at `${CLAUDE_PLUGIN_ROOT}`. Relative links in this file resolve from `${CLAUDE_PLUGIN_ROOT}/skills/orchestration/`; read linked agents, skills, standards and templates from there. The repository being worked on is the current working directory, never the framework folder.

# Orchestration

## Purpose

Turn a request into the smallest sufficient sequence of framework skills
and subagents, with human approval gates and an independent review before
work is called done. The Orchestrator does not do specialist work itself.

This used to be an Orchestrator subagent. It runs in the main conversation
instead, because only the main conversation can stop for the user's
approval, ask a clarifying question and show intermediate results. A
subagent runs to completion and reports once, so an orchestrating subagent
either skips its own approval gates or stops after planning.

## When to Use

- From [`/ticket`](../../commands/ticket.md), for every ticket.
- A request that spans discovery, design, implementation and review.
- Not for a pure question or a single-skill task (a review only, a plan
  only): call that skill or command directly.

## Inputs

- The user's request (chat message, ticket text, command arguments).
- The working tree of the current repository.
- The repository's overlay: `AGENTS.md`, `.ai/manifest.yaml` and the
  `.ai/` documents they link to.

## Preconditions

- The current working directory is the client repository being worked
  on, and the overlay read is that repository's own.

## Procedure

1. **Classify** the request: question, investigation, planning,
   implementation, review or PR preparation. State it in one line.
2. **Load context.** Read `AGENTS.md` and `.ai/manifest.yaml`, then only
   the deeper `.ai/` documents the request touches. If there is no
   overlay and the work is non-trivial, offer
   [`/bootstrap-project`](../../commands/bootstrap-project.md) first.
3. **Pick the smallest sufficient set of roles.** A small Python bug does
   not need every specialist.

   | Need | Use | Runs as |
   |---|---|---|
   | Unfamiliar repository or area | [`repository-discovery`](../repository-discovery/SKILL.md) via [Repository Analyst](../../agents/repository-analyst.agent.md) | Subagent (read-only; keeps the main context small) |
   | A real architectural trade-off | [`architecture-assessment`](../architecture-assessment/SKILL.md) via [Architect](../../agents/architect.agent.md) | Subagent (read-only) |
   | A change to behaviour, data or architecture | [`implementation-plan`](../implementation-plan/SKILL.md) | Main conversation |
   | Implementation | [Data Engineer](../../agents/data-engineer.agent.md) rules and standards | Main conversation by default; the Data Engineer subagent only for a bounded, approved part of the plan |
   | Implementation finished | [`code-review`](../code-review/SKILL.md), plus [`kimball-review`](../kimball-review/SKILL.md) and [`testing`](../testing/SKILL.md) as needed, via [Reviewer](../../agents/reviewer.agent.md) | Subagent (an independent context is the point) |
   | PR text | [`pull-request`](../pull-request/SKILL.md) | Main conversation |

   Invoking this skill, directly or through `/ticket`, counts as the
   user asking for the framework subagents in this table. Do not spawn
   others.
4. **State the execution plan** before starting: steps, roles, and where
   the approval gates fall.
5. **Stop at approval gates** and wait for an explicit yes:
   - before the first edit of a non-trivial change (show the plan);
   - before anything the overlay names as a separate human approval
     gate;
   - before a commit, push, PR creation or any remote or cloud
     operation, and only within the permissions the user has configured;
   - when two specialists disagree, or a recommendation conflicts with
     the overlay.

   A trivial change (one obvious, low-risk edit) gets a one-line plan and
   still needs the user's go-ahead, unless they already gave it in the
   request. Approval of a plan is not approval to commit or push.
6. **Brief subagents completely.** They start without this conversation:
   pass the objective, the relevant paths, the overlay constraints that
   apply and the approved plan. A Reviewer also gets the diff range and
   what the change is meant to do.
7. **Treat subagent output as input, not as conclusions.** Check its key
   claims against the repository before acting on them, and state
   disagreements between specialists explicitly instead of silently
   picking one side.
8. **Enforce the review gate.** After implementation, run the Reviewer
   before declaring the work done or preparing a PR. Critical and High
   findings are fixed, or stay open with the user's decision recorded.
9. **Aggregate** into one coherent result, not a set of disconnected
   specialist outputs.
10. **Record learning candidates as they happen**: a correction from the
    user, an overlay fact that proved wrong or missing, a review finding
    that should not recur. With an active ticket they go into its note
    (see [`templates/TICKET.md`](../../templates/TICKET.md)); otherwise
    list them in the final answer. They are processed later by
    [`capture-learnings`](../capture-learnings/SKILL.md).

## Decision Criteria

- **Unfamiliar repository or area →** discovery before any architectural
  or implementation decision.
- **Request changes behaviour, data or architecture →** a plan, approved
  before editing.
- **Pure question or analysis →** no edits; route to the relevant skill
  read-only.
- **Several plausible approaches with real trade-offs →** the Architect
  before implementation starts.
- **Work is done →** the Reviewer before completion or a PR.

## Evidence Required

The classification, and for every role used, why it was needed. No
specialist is invoked "just in case".

## Output Format

```text
## Classification
## Execution Plan (steps, roles, gates)
## Result
## Conflicts / Open Risks
## Learning Candidates
```

## Quality Checks

- Every approval gate that applied was actually stopped at.
- The Reviewer ran after implementation, before completion or a PR.
- Nothing was taken from another client repository or an earlier
  engagement.

## Common Failure Modes

- Invoking every specialist for a small fix.
- Briefing a subagent in one line, then trusting its summary unchecked.
- Treating approval of a plan as approval to commit, push or deploy.
- Implementing inside a subagent, so the user first sees the diff after
  the fact.

## Escalation / Specialist Handoff

If the request cannot be classified with reasonable confidence, or spans
several unrelated repositories or clients, stop and ask rather than
guess, especially where guessing risks mixing client context.
