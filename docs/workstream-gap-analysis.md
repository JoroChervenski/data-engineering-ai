# Gap analysis: the four workstreams

Compares [the workstation implementation spec](../ai_assisted_consulting_workstation_implementation.md)
(Dev Container template, hooks and policies, verifier and evals, versioning and release) with this
repository. This is the "Phase 1 — repository discovery" output that spec asks for.

- Repository state: commit `89be5f9` plus the close-out changes on `chore/phase1-closeout`.
- **Observed** = seen in a file or command output. **Unknown** = not verified; each one needs a
  check before the work that depends on it.

## Terminology

The workstation spec has its own Phases 1–7. The original
[implementation spec](../AI_DATA_ENGINEERING_PLATFORM_IMPLEMENTATION_SPEC.md) has Phases 1–6, and
[AGENTS.md](../AGENTS.md) rule 7 gates work by those numbers. To avoid a clash, the four
workstreams are called **W1 template, W2 hooks and policies, W3 verifier and evals, W4 versioning
and release**. "Phase" always means the original spec.

## 1. What exists that the workstreams can reuse

| Mechanism | Observed | Reuse in |
|---|---|---|
| Claude Code plugin packaging | [.claude-plugin/](../.claude-plugin/); frontmatter on every agent, skill and command | W2 hooks shipped with the plugin, W4 release artifact |
| Per-agent `tools` allow-list | Architect, repository-analyst, reviewer: `Read, Grep, Glob, Bash`. Data-engineer: none (inherits all) | W2 role enforcement (the spec says reuse sound mechanisms) |
| Static validator | [tests/validate_framework.py](../tests/validate_framework.py): links, frontmatter, secret patterns, client terms. Standard library only | W1 template tests, W4 `validate.yml` |
| Human approval gates | [orchestration](../skills/orchestration/SKILL.md) step 5. Instruction-level only | W2 turns these into enforced rules |
| Tool levels L0–L3 | [standards/security.md](../standards/security.md) | W2 capability policy vocabulary |
| Severity model | Critical/High/Medium/Low/Suggestion in [code-review](../skills/code-review/SKILL.md) | W3 verifier findings |
| Project manifest with `schema_version` and an overlay block | [templates/manifest.yaml](../templates/manifest.yaml) | W1 `project.yaml`, W4 framework version pin |
| `@AGENTS.md` pointer | [CLAUDE.md](../CLAUDE.md) | W1 template `CLAUDE.md` |
| Learning loop | [capture-learnings](../skills/capture-learnings/SKILL.md), [inbox/](../inbox/README.md) | W3 regression evals |
| Install and update flow | README "Use with Claude Code" and "Updating the framework" | W4 upgrade and rollback docs |
| Fixture | [tests/fixtures/example-retail](../tests/fixtures/example-retail) | W3 eval material |

## 2. Missing

None of these exist: `templates/client-project/`, `.devcontainer`, `scripts/`, `policies/`,
`hooks/`, `schemas/`, `evals/`, `.github/workflows/`, `VERSION`, `CHANGELOG.md`, and a verifier.

Local tooling: Docker and Python 3.12 are available. Node, `jq`, `yq` and `shellcheck` are not.
The default Python has no PyYAML, `jsonschema` or `pytest`.

## 3. Conflicts between the spec and the repository

1. **Layout.** The spec uses `agents/<role>/` folders; the repo uses `agents/<role>.agent.md`. A
   verifier would be `agents/verifier.agent.md`. Keep the repo convention.
2. **Roles.** The spec's `developer` is the repo's `data-engineer`. `repository-analyst` has no
   policy role (it behaves like `architect`). `orchestration` is a skill in the main conversation,
   so it has no role of its own. Do not build a `deployer` agent; keep it as a policy role only.
3. **Skills.** The spec lists `fabric`, `pyspark`, `sql` and `dimensional-modeling` skills. The repo
   keeps that knowledge in `standards/` (AGENTS.md rule 2) and has `kimball-review`. Do not
   duplicate it.
4. **Overlapping metadata.** `.ai/project.yaml` overlaps `.ai/manifest.yaml`. `docs/adr` and
   `docs/runbooks` overlap `.ai/adr` and `.ai/runbooks`.
5. **Policy vocabulary.** `guardrails.yaml` says `blocked`, `command-policy.yaml` says `deny`. `deploy`
   is `false` for some roles and `approval_required` for another. `environment-policy.yaml` and
   `production-policy.yaml` appear in the target tree but are never specified. Nothing defines
   precedence between framework policy, client `guardrails.yaml` and Claude's own `permissions`.
6. **Verifier vs reviewer.** Both may run tests in the spec. The verifier's lowercase `severity: high`
   does not match the repo's severity model.
7. **Versioning.** [plugin.json](../.claude-plugin/plugin.json) has no `version`, so every commit is a
   new version (stated in the README). W4 wants explicit client pins.
8. **Spec internal.** Its section 14 says to start the template right after discovery, while section 9
   makes that Phase 2. Its eval baseline (section 7.2) comes before the evals exist.
9. **Eval gate.** A CI gate on LLM-judged security evals can be flaky, and needs an API key that
   pull requests from forks will not have. The deterministic policy unit tests must be the real gate;
   Promptfoo is a second layer.
10. **Graphify and Obsidian.** The repo's doctrine is "Git is the system of record". Both must stay
    non-authoritative, and each is an external tool that [AGENTS.md](../AGENTS.md) rule 7 gates.
11. **Read-only is not enforced.** The three read-only agents have `Bash`, which can write. This is
    the main reason for W2.

## 4. Unknowns to verify before building

- How a `PreToolUse` hook learns which subagent or role is calling. W2 role enforcement depends on it.
- Whether a plugin can ship hooks, and where they are declared.
- Whether the plugin marketplace supports pinning a client to a version or tag, and rollback. W4 depends
  on it.
- Whether the current marketplace repository is private. The spec assumes a private marketplace.

Check each against the current Claude Code documentation first; do not design from memory.

## 5. Decisions needed before W1

| # | Decision | Recommendation |
|---|---|---|
| D1 | Name the new work as workstreams, not phases; update AGENTS.md rule 7 | Yes |
| D2 | Add `.ai/project.yaml`, or extend `.ai/manifest.yaml` | Extend `manifest.yaml`; fewer files, one schema |
| D3 | ADR and runbook location | Keep `.ai/adr` and `.ai/runbooks`; drop `docs/adr` and `docs/runbooks` |
| D4 | How to parse YAML policy without a new dependency | JSON policies and manifest checks first; add PyYAML only if W2 needs YAML |
| D5 | First framework version and its source | `VERSION` file at `0.1.0`, a matching git tag, and `plugin.json` `version` kept in sync by a check |

## 6. Recommended sequence

1. Close-out (this branch): README, marketplace and kimball fixes, the dry-run, this document.
2. **W1.** `templates/client-project/`, `scripts/new-client.sh`, template tests added to the validator.
3. **Minimal CI.** `validate.yml` running the existing validator. Cheap, and pulled forward from W4.
4. **W2.** Policy engine with unit tests first, then hooks, then role enforcement.
5. **W3.** Verifier agent and its output contract, then Promptfoo with a baseline.
6. **W4.** `VERSION`, `CHANGELOG`, `evals.yml`, `release.yml`, rollback docs.
7. README update.

## 7. Files W1 would add or change

Add: `templates/client-project/` (`.devcontainer/devcontainer.json`, `.devcontainer/Dockerfile`,
`.claude/settings.json`, `.ai/guardrails.yaml`, `docs/` folders, `tests/`, `.env.example`, `CLAUDE.md`,
`README.md`) and `scripts/new-client.sh`.

Change: [tests/validate_framework.py](../tests/validate_framework.py) (template checks),
[templates/manifest.yaml](../templates/manifest.yaml) (project and environment fields, per D2),
[AGENTS.md](../AGENTS.md) rule 7 (per D1), [README.md](../README.md).

Design notes for the template: a named volume per client for Claude Code's own configuration, so one
client's login and settings are never shared; no bind mount of the home directory; credentials injected
at runtime, never at image build.
