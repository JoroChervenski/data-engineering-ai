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
11. **Read-only is not enforced.** The three read-only agents have `Bash`, which can write. Resolved in W2: the
    hook denies file edits and mutating commands for the architect, reviewer and verifier roles.

## 4. Unknowns

Checked against the Claude Code documentation on 2026-10-08:

- **Marketplace privacy and pinning (W4): answered.** A marketplace repository can be private, if the
  user's git has credentials for it. A plugin entry can be pinned with `ref` (branch or tag) and `sha`,
  and a marketplace can be added at a ref with `#<ref>`. Users get new plugin files only when the
  computed `version` changes; without a `version` they track commits.
- **Registering the plugin per repository: answered.** `extraKnownMarketplaces` and `enabledPlugins` in a
  repo's `.claude/settings.json` work after the developer trusts the folder. The client template uses them.
- **Permission rules: answered.** `Read(~/...)` and `Read(!pattern)` work in deny rules; Bash rules match
  command text only, so they are not a security boundary. Deny is checked before ask, ask before allow.

Hooks, checked against the Claude Code documentation on 2026-10-09:

- **Role enforcement (W2): answered.** A `PreToolUse` hook receives `agent_id` and `agent_type` when the call
  comes from a subagent, so "reviewer cannot edit source" is enforceable. Calls from the main conversation
  carry no agent type and get the session's default role. Not confirmed: whether a plugin agent's
  `agent_type` is `reviewer` or `data-engineering-ai:reviewer`; the hook should accept both.
- **Plugin-shipped hooks (W2): answered.** A plugin can ship `hooks/hooks.json`, with scripts at
  `${CLAUDE_PLUGIN_ROOT}`. A subagent's own frontmatter can also carry hooks that run only while it runs.
- **Decisions and blocking:** exit code 2 blocks; a JSON `permissionDecision` of allow, deny or ask is
  preferred. A blocking hook beats an allow rule, and deny and ask rules still apply when a hook allows.

## 5. Decisions

| # | Decision | Outcome |
|---|---|---|
| D1 | Name the new work as workstreams, not phases; update AGENTS.md rule 7 | Done |
| D2 | Add `.ai/project.yaml`, or extend `.ai/manifest.yaml` | Extended `manifest.yaml` with `framework`, `standard`, `security` and per-environment `write_access` |
| D3 | ADR and runbook location | `.ai/adr` and `.ai/runbooks`, mirrored read-only into the vault per repo; no `docs/adr`, `docs/runbooks` or `docs/architecture` |
| D4 | How to parse policy without a new dependency | `.ai/guardrails.json` (JSON), with the keys `deny` and `approval_required` (not `blocked`) |
| D5 | First framework version and its source | `VERSION` file at `0.1.0`. The git tag and a `plugin.json` `version` are W4 |

## 6. Sequence and status

1. Close-out of Phase 1: done.
2. **W1, client template: implemented.** `templates/client-project/`, `scripts/new-client.sh`,
   `scripts/vault_sync.py`, the `/vault-sync` command, and tests. The requirements it implements are in the
   Project Standard in the vault's `Knowledge/` folder, not here.
3. Minimal CI: `validate.yml` running the validator and the unit tests. Not started.
4. **W2, policies and hooks: implemented.** `policies/` (command, capability, environment, production, secret,
   content, verification), `hooks/` (PreToolUse, PostToolUse and its failure event, SessionStart, Stop), role
   enforcement from `agent_type`, a shell parser, project guardrails that can only tighten, a redacted audit log,
   and the project requirements in the Project Standard (`PS-POL`). Not done: JSON schemas for the policy files
   (W4, needs a validator decision), a verifier agent (W3), and enforcement of the policies for tools other
   than Bash, file tools and MCP.
5. W3, verifier and evals. Not started.
6. W4, `VERSION` tag, `CHANGELOG`, `evals.yml`, `release.yml`, rollback docs. Not started.
7. README update at the end.

Also not done: a Dev Container for this framework repository itself, mounting only `Knowledge/` and
`Templates/` read-only. The mount rules it must satisfy are already tested in
`tests/devcontainer_rules.py` (role `framework`).

## 7. What W1 added or changed

W2 added `policies/`, `hooks/` (engine, shell parser, four hook scripts), `tests/test_w2_engine.py`,
`tests/test_w2_hooks.py`, `tests/test_content_policy.py` and the `PS-POL` requirements in the Project Standard.

W1 added `templates/client-project/`, `scripts/new-client.sh`, `scripts/new_client.py`,
`scripts/vault_sync.py`, `commands/vault-sync.md`, `VERSION`, `tests/test_vault_sync.py`,
`tests/test_client_template.py`, `tests/devcontainer_rules.py`, `tests/fixtures/standard/`.

Changed: `templates/manifest.yaml`, `commands/bootstrap-project.md`, `tests/validate_framework.py` (JSON
check), `AGENTS.md` (rules 7, 8 and 11), `README.md`.
