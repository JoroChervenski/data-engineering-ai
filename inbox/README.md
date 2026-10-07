# Inbox: lessons from client work

Generic lessons captured by the
[`capture-learnings`](../skills/capture-learnings/SKILL.md) skill while
working in client repositories. Items here are candidates, not framework
rules: they become rules only when promoted into an agent, skill,
standard, template or command.

Everything in this folder is anonymised. No client names, people, IDs,
URLs, table, column or item names, business rules or data, the same as
the rest of this repository (see [`AGENTS.md`](../AGENTS.md), rule 1).

## Item format

One file per lesson: `inbox/<YYYY-MM-DD>-<short-slug>.md`, dated by when
the lesson was first seen.

```markdown
---
type: framework-learning
kind: skill # agent | skill | standard | template | command
target: skills/code-review/SKILL.md # best guess at where it belongs
status: new # new | promoted | rejected
seen: 1
first_seen: YYYY-MM-DD
last_seen: YYYY-MM-DD
---

# <The lesson, as one sentence>

## Why it matters

<The failure it prevents, in generic terms.>

## Evidence (anonymised)

- YYYY-MM-DD: <what happened, without client specifics>

## Proposed change

<The concrete edit to the target file.>
```

## Promotion

Promote an item when one of these holds:

- it has been seen in three separate tasks (`seen: 3`);
- it prevents a Critical or High class failure (see the
  [severity model](../skills/code-review/SKILL.md#severity-model)), after
  one occurrence;
- the framework owner asks for it.

To promote: make the edit in the target file, set `status: promoted` and
name the commit in the item, then run `python3 tests/validate_framework.py`.
A rejected item gets `status: rejected` and one line saying why; it stays
in the folder so the same lesson is not proposed again.
