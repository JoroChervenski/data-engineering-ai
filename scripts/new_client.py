#!/usr/bin/env python3
"""Create a new client repo from the framework's client template.

    ./scripts/new-client.sh <project> <target-path> [--repo NAME] [--vault DIR] [--with-azure-cli] [--no-sync]

Run it yourself in a host terminal, not inside a container: it creates the empty vault folder
Projects/<project>/ and writes the new repo, neither of which the framework container may reach.

It reads the Project Standard from <vault>/Knowledge for the name rules. It checks everything first and
writes nothing if a file would be overwritten. It generates no secrets and no credentials.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
FRAMEWORK = HERE.parent
sys.path.insert(0, str(HERE))
import vault_sync  # noqa: E402

TEMPLATE = FRAMEWORK / "templates" / "client-project"
AGENTS_TEMPLATE = FRAMEWORK / "templates" / "AGENTS.md"
MANIFEST_TEMPLATE = FRAMEWORK / "templates" / "manifest.yaml"
AZURE_FEATURE = "ghcr.io/devcontainers/features/azure-cli:1"


class NewClientError(Exception):
    pass


def framework_version():
    try:
        return (FRAMEWORK / "VERSION").read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def set_yaml_scalar(text, path, value):
    """Set a scalar two levels deep, e.g. ("framework", "version"), keeping the line's trailing comment."""
    parent, key = path
    lines = text.split("\n")
    in_block = False
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(parent)}:\s*(#.*)?$", line):
            in_block = True
            continue
        if in_block and re.match(r"^\S", line):
            break
        match = re.match(rf"^(\s+){re.escape(key)}:\s*\"[^\"]*\"(\s*#.*)?$", line) if in_block else None
        if match:
            lines[i] = f'{match.group(1)}{key}: "{value}"{match.group(2) or ""}'
            return "\n".join(lines)
    raise NewClientError(f"manifest template has no {parent}.{key}")


def build_files(project, repo, with_azure, standard_version, standard_commit):
    """Return {relative path: text} for the new repo. Nothing is written here."""
    files = {}
    for path in sorted(TEMPLATE.rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            text = text.replace("__PROJECT__", project).replace("__REPO__", repo)
            files[path.relative_to(TEMPLATE).as_posix()] = text

    if with_azure:
        key = ".devcontainer/devcontainer.json"
        config = json.loads(files[key])
        config["features"][AZURE_FEATURE] = {}
        files[key] = json.dumps(config, indent=2) + "\n"

    files["AGENTS.md"] = AGENTS_TEMPLATE.read_text(encoding="utf-8").replace("<project-name>", project)

    manifest = MANIFEST_TEMPLATE.read_text(encoding="utf-8").replace("<project-name>", project)
    manifest = set_yaml_scalar(manifest, ("framework", "version"), framework_version())
    manifest = set_yaml_scalar(manifest, ("standard", "version"), standard_version)
    manifest = set_yaml_scalar(manifest, ("standard", "commit"), standard_commit)
    files[".ai/manifest.yaml"] = manifest
    return files


def run(project, target, repo=None, vault=None, with_azure=False, run_sync=True, out=print):
    vault_arg = vault or os.environ.get("AI_VAULT")
    if not vault_arg:
        raise NewClientError("the vault path is not set: pass --vault or export AI_VAULT")
    vault_root = pathlib.Path(vault_arg)
    knowledge = vault_root / "Knowledge"
    projects = vault_root / "Projects"
    if not projects.is_dir():
        raise NewClientError(f"{projects} not found; is {vault_root} the vault folder?")

    try:
        std = vault_sync.load_standard(knowledge)
        target = pathlib.Path(target).expanduser().resolve()
        repo = repo or target.name
        vault_sync.check_names(std, project, repo)
    except vault_sync.SyncError as exc:
        raise NewClientError(str(exc))

    standard_commit = vault_sync.git_stamp(knowledge, dirty_check=True)
    files = build_files(project, repo, with_azure, std["version"], standard_commit)

    conflicts = sorted(rel for rel in files if (target / rel).exists() or (target / rel).is_symlink())
    if conflicts:
        raise NewClientError(f"would overwrite existing files in {target}:\n  " + "\n  ".join(conflicts))
    if target.exists() and not target.is_dir():
        raise NewClientError(f"{target} exists and is not a folder")

    project_dir = projects / project
    created_files, created_dirs = [], []
    try:
        for folder in (project_dir,):
            if not folder.exists():
                folder.mkdir()
                created_dirs.append(folder)
        for rel, text in files.items():
            path = target / rel
            for parent in reversed(path.parents):
                if parent == target.parent:
                    continue
                if not parent.exists() and parent not in created_dirs:
                    parent.mkdir()
                    created_dirs.append(parent)
            path.write_text(text, encoding="utf-8")
            created_files.append(path)
        (target / ".devcontainer" / "initialize.sh").chmod(0o755)
        if run_sync:
            vault_sync.sync(target, knowledge, vault_dir=project_dir)
    except Exception:
        for path in created_files:
            path.unlink(missing_ok=True)
        for folder in sorted(created_dirs, key=lambda p: len(p.parts), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass
        raise

    out(f"Created {repo} for project {project} in {target}")
    out(f"  vault folder: {project_dir}" + ("" if run_sync else " (empty; run the sync to build the layout)"))
    out("Next:")
    out(f"  1. cd {target} && git init   (if it is not a repository yet)")
    out(f"  2. export AI_VAULT={vault_root}   then   code .   and Reopen in Container")
    out("  3. In the container: /data-engineering-ai:bootstrap-project, then commit the overlay")
    out("  4. Copy .env.example to .env and fill in this client's values (never commit it)")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project")
    parser.add_argument("target")
    parser.add_argument("--repo", help="repo name (default: the target folder's name)")
    parser.add_argument("--vault", help="vault folder (default: $AI_VAULT)")
    parser.add_argument("--with-azure-cli", action="store_true", help="add the Azure CLI Dev Container feature")
    parser.add_argument("--no-sync", action="store_true", help="do not build the vault layout yet")
    args = parser.parse_args(argv)
    try:
        run(args.project, args.target, args.repo, args.vault, args.with_azure_cli, not args.no_sync)
    except (NewClientError, vault_sync.SyncError) as exc:
        print(f"new-client: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
