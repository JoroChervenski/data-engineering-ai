#!/usr/bin/env python3
"""SessionStart hook: tells Claude, at the start of a session, the facts the policies depend on.

Project, framework and standard versions, the Git branch, the role and environment, whether production writes
are allowed, whether the project's guardrails loaded, and which expected tools are missing.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit  # noqa: E402
import engine  # noqa: E402
import policy_store  # noqa: E402


def describe(event, environ=None):
    environ = os.environ if environ is None else environ
    cwd = event.get("cwd") or os.getcwd()
    try:
        fw = policy_store.load_framework()
    except policy_store.PolicyError as exc:
        return ("Framework policy context (data-engineering-ai): the policies could not be loaded "
                f"({exc}). A small built-in baseline is in force: destructive commands are denied, and pushes, "
                "deployments and secret paths need a person's approval.")
    project = policy_store.load_project(cwd, fw)
    env = policy_store.resolve_environment(cwd, fw, project, environ)
    manifest = policy_store.manifest_text(cwd, fw)
    name = policy_store.manifest_scalar(manifest, "project", "name")
    version = policy_store.manifest_scalar(manifest, "framework", "version") or "unknown"
    standard = policy_store.manifest_scalar(manifest, "standard", "version") or "unknown"
    commit = policy_store.manifest_scalar(manifest, "standard", "commit") or "unknown"
    git = engine.git_summary(cwd)
    role = project.data.get("default_role", fw.capability["default_role"])
    variable = fw.environment["environment_variable"]
    expected = list(fw.environment.get("expected_tools", [])) + project.data.get("expected_tools", [])
    missing = engine.tools_missing(sorted(set(expected)))

    lines = ["Framework policy context (data-engineering-ai, policy hooks active):",
             f"- Project: {name or 'not defined in the manifest'}; framework {version}; standard {standard} ({commit})."]
    lines.append(f"- Git: branch {git[0]}, {git[1]} modified, {git[2]} untracked." if git else "- Git: not a repository.")
    lines.append(f"- Role: this conversation acts as {role}; subagents follow their own roles "
                 "(architect, reviewer and verifier cannot modify files).")
    if env.known:
        access = "writes allowed" if env.write_access else "READ-ONLY"
        lines.append(f"- Environment: {env.name} ({access}).")
    else:
        lines.append(f"- Environment: unknown ({env.reason}). Deployment is denied until {variable} names an "
                     "environment defined in .ai/manifest.yaml.")
    prod = fw.production
    lines.append("- Production write operations: NOT allowed. "
                 + ("Shell writes are blocked in a read-only environment. " if not prod["shell_write_operations"] else "")
                 + "Any deployment needs a person's explicit approval, and is denied for this role in production.")
    if project.path is None:
        lines.append("- Project guardrails: none found; the framework baseline applies.")
    elif project.valid:
        lines.append(f"- Project guardrails: loaded from {project.path.relative_to(project.root)}"
                     + (f" ({'; '.join(project.notes)})" if project.notes else "") + ".")
    else:
        lines.append("- Project guardrails: INVALID and ignored (" + "; ".join(project.errors)
                     + "). The framework baseline applies and the environment is treated as unknown.")
    lines.append("- Tools: " + (f"MISSING {', '.join(missing)}." if missing else "all expected tools are present."))
    lines.append("- Always: no AI signature in commits, pull requests, tickets or tasks. Secret paths (.env, ~/.ssh, "
                 "~/.azure, credentials*, secrets*) are never read or printed. Do not claim work is complete "
                 "while tests or lint have not passed after your last edit.")
    return "\n".join(lines)


def main(stdin=None, stdout=None, stderr=None):
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        event = json.load(stdin)
    except ValueError:
        event = {}
    try:
        text = describe(event)
        if event.get("source") in ("startup", "clear"):
            state = audit.SessionState(event.get("session_id"))
            state.reset()
            state.save()
    except Exception as exc:
        print(f"session_start: {type(exc).__name__}: {exc}", file=stderr)
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, stdout)
    stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
