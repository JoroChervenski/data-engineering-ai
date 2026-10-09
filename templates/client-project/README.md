# __REPO__

Repository `__REPO__` of project `__PROJECT__`. This file describes the working environment; describe the
project itself in `.ai/PROJECT.md` once `/bootstrap-project` has run.

## One-time setup on your machine

1. Install Docker and the VS Code Dev Containers extension.
2. In your WSL shell, export the path of your Obsidian vault, then start VS Code from that shell:

   ```bash
   export AI_VAULT=/path/to/your/vault   # the folder that contains Knowledge/ and Projects/
   code .
   ```

3. The vault folder `Projects/__PROJECT__/` must exist. `scripts/new-client.sh` in the framework creates it.

Open the folder in VS Code and choose **Reopen in Container**. A check runs on the host first and stops with
a clear message if `AI_VAULT` or a vault folder is missing.

## What the container can see

| Path in the container | Comes from | Access |
|---|---|---|
| the workspace | this repo folder | read/write |
| `/vault/__PROJECT__` | `Projects/__PROJECT__/` in the vault | read/write |
| `/vault/Knowledge` | `Knowledge/` in the vault (the Project Standard) | read-only |
| `~/.claude` | a Docker volume named for this container | read/write, one per project |

Nothing else is mounted: not the vault root, not another project, not your home folder, `~/.ssh` or
`~/.azure`. Do not add such mounts.

## Credentials

Credentials are never in the image or in Git.

- **Client values:** copy `.env.example` to `.env` (git-ignored) and fill in this client's values only. The
  container receives `.env` as environment variables. Never copy another client's values.
- **Claude Code:** run `claude` in the container and sign in. The login lives in the per-project volume and
  survives rebuilds.
- **Azure CLI (optional):** add `"ghcr.io/devcontainers/features/azure-cli:1": {}` under `features` in
  `.devcontainer/devcontainer.json`, rebuild, then `az login --use-device-code` in the container.
- **Git:** prefer a repository-scoped or short-lived token in `.env` over host credentials. VS Code can also
  forward your host's Git credential helper and SSH agent into a container; check what is forwarded before
  you work for a client whose access must stay separate.

## Rebuilding

Your files are in the bind-mounted workspace, so rebuilding the container does not delete them. `.env`, the
vault folder and the Claude login also survive.

## Getting started

1. Run `/data-engineering-ai:bootstrap-project` to create the overlay (`AGENTS.md` and `.ai/`) from what is
   in the repo. Until then `AGENTS.md` is an empty skeleton.
2. Commit the overlay.
3. After changing `.ai/*.md`, a ticket note, an ADR or a runbook, run `/data-engineering-ai:vault-sync`. It
   mirrors them read-only into `Projects/__PROJECT__/` in the vault, following the Project Standard.
   Use `--dry-run` to preview.

## Policies

The framework plugin applies its policies through hooks, in every session of this repo:

- **Roles.** This conversation acts as the developer. Subagents act as their own role: the architect, reviewer
  and verifier cannot modify files; only the deployer may deploy, and only with your approval.
- **Commands.** Destructive commands (force-push, `git reset --hard`, `rm -rf /`, `DROP DATABASE`, piping a
  download into a shell) are denied. Pushes, package installs, SQL changes and deployments ask you first.
- **Environment.** Set `AI_ENVIRONMENT` in `.env` to an environment listed under `environments` in
  `.ai/manifest.yaml`. While it is empty or unknown, deployment is denied. An environment with
  `write_access: false` is read-only for shell writes.
- **Secrets.** `.env`, `~/.ssh`, `~/.azure`, `~/.config/gh`, `credentials*` and `secrets*` are never read or
  printed. `.env.example` is fine. To allow one narrow, safe file, list it under `secrets.allow_paths` in
  `.ai/guardrails.json`; credential stores cannot be allowed.
- **Verification.** After you change source files, the session cannot finish until a test or lint run passes.
- **No AI signature** in commits, pull requests, tickets or tasks.

Every denial and approval request is logged, with credentials hidden and file contents left out, in the plugin's
data folder (`audit/decisions.jsonl`).

## Guardrails

- `.claude/settings.json` denies reading secret files, force-push and hard reset, and asks before a push.
  These are permission rules, not a security boundary: the container's mounts are.
- `.ai/guardrails.json` holds this project's additions to the framework policies: more denied or approval-required
  commands, a more restricted default role, approved verification commands, and narrow secret exceptions. It can only
  add restrictions. If it is invalid it is ignored as a whole and the environment is treated as unknown.

## Versions

`.ai/manifest.yaml` records the framework version and the Project Standard version and commit this project was
created from. Upgrade deliberately, not automatically. The base image is pinned to Python 3.12 on Debian 12.
The Claude Code feature installs the latest release; to pin it, see "Enforce organization policy" in the
Claude Code dev container documentation.
