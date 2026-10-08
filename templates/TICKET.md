---
type: ticket
project: <project-tag>
ticket: <TICKET-ID>
status: open # open | in-progress | review | done
branch:
pr:
created: <YYYY-MM-DD>
tags: [ticket]
---

<!--
  Ticket note template, filled per client repository by /ticket. Where the
  overlay's AGENTS.md defines its own note conventions (frontmatter values,
  status names, link style), those win over this template.
-->

# <TICKET-ID>: <title>

## Context

<The ticket text or request as given, then what discovery found about the
affected area. Label claims O (observed), I (inferred) or U (unknown).>

## Acceptance Criteria

<From the ticket. Missing or ambiguous criteria go under Open Questions,
not here as assumptions.>

## Plan

<The approved implementation plan (implementation-plan output), and the
date and person that approved it.>

## Review

<Verdict and findings of the independent review (/review-pr, or /ticket
step 7), most severe first, with the date and the commit reviewed.>

## Decisions

- <YYYY-MM-DD> <decision>: <why> (<who decided>)

## Open Questions

- [ ] <question>

## Learning Candidates

<!-- One line each, written when it happens: a correction from the user,
     an overlay fact that proved wrong or missing, a review finding that
     should not recur, a convention discovered. capture-learnings ticks
     each one and records where it went. -->

- [ ] <YYYY-MM-DD> <what happened> → <suggested target, e.g. .ai/STANDARDS.md, or framework>

## Log

- <YYYY-MM-DD> Created.
