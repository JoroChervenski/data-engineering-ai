# AGENTS.md — <project-name>

<!--
  Client repository overlay template. Fill every section from actual
  repository evidence (see repository-discovery). Mark anything unknown
  as "Unknown" rather than guessing. Remove this comment block once filled.
-->

## 1. What is this project?

<One or two sentences: what this repository is and does.>

## 2. Critical architecture constraints

<Hard constraints that must not be violated, e.g. "Gold layer is Kimball
dimensional," "semantic model is Direct Lake," "no PII in Bronze." Mark
unknown constraints as Unknown rather than omitting them silently.>

## 3. Important files and directories

<Key entry points, pipelines, notebooks, semantic model location —
from `.ai/ARCHITECTURE.md` and repository-discovery output.>

## 4. Allowed technologies

<Technologies/platform services this project actually uses and should
keep using.>

## 5. Disallowed or discouraged technologies

<Anything explicitly ruled out for this project, and why, if known.>

## 6. Required testing

<What test types are required before a change here is considered done.
See the framework's `standards/testing.md`.>

## 7. Security rules

<Project-specific security rules beyond the framework's
`standards/security.md` — e.g. specific RLS requirements, specific
data-classification rules.>

## 8. Deployment

<How this project is deployed — environments, promotion process, who can
trigger it. Mark Unknown if not observable.>

## 9. Directories that must not be modified without explicit reason

<e.g. generated artifacts, vendor code, anything with a known reason to
leave alone.>

## 10. Deeper documentation

- [.ai/PROJECT.md](.ai/PROJECT.md)
- [.ai/ARCHITECTURE.md](.ai/ARCHITECTURE.md)
- [.ai/DATA-MODEL.md](.ai/DATA-MODEL.md)
- [.ai/GLOSSARY.md](.ai/GLOSSARY.md)
- [.ai/STANDARDS.md](.ai/STANDARDS.md)
- [.ai/TECH-DEBT.md](.ai/TECH-DEBT.md)
- [.ai/manifest.yaml](.ai/manifest.yaml)

## 11. Working notes and workflow

<Where ticket notes, ADRs and runbooks live (default: `.ai/tickets/`,
`.ai/adr/`, `.ai/runbooks/`), any frontmatter or link conventions they
must follow, and how the overlay itself is versioned (committed here, or
its own repository). Tickets run through `/ticket <TICKET-ID>`; lessons
are recorded at close with the `capture-learnings` skill.>

## 12. Rules that always apply

These come from the framework's policies and are not project facts. Do not remove them.

- **No AI signature.** No commit, pull request, issue, ticket note, task, ADR or runbook says that an AI
  wrote, edited, reviewed or published it: no `Co-Authored-By` line naming an AI, no "Generated with ..."
  footer, no robot emoji, no "signed, edited or published by AI". Human co-authors are fine. The framework
  blocks this with a hook, and `.claude/settings.json` turns off Claude Code's own attribution.
