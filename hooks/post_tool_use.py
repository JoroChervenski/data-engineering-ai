#!/usr/bin/env python3
"""PostToolUse and PostToolUseFailure hook.

After an edit it checks the file still parses (JSON, Python), tells the Stop hook that source changed, and notes
edits to policy-protected files. After a shell command it records whether a test or lint run passed or failed.
It writes non-sensitive audit metadata only. It never blocks: the tool has already run.
"""
import ast
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit  # noqa: E402
import content_policy  # noqa: E402
import engine  # noqa: E402
import policy_store  # noqa: E402

WRITE_FIELDS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
MAX_CHECK_BYTES = 1_000_000


def syntax_problem(path):
    """A short description if the file at path no longer parses, else None."""
    try:
        file = pathlib.Path(path)
        if not file.is_file() or file.stat().st_size > MAX_CHECK_BYTES:
            return None
        if file.suffix == ".json":
            json.loads(file.read_text(encoding="utf-8"))
        elif file.suffix == ".py":
            ast.parse(file.read_text(encoding="utf-8"), str(file))
    except json.JSONDecodeError as exc:
        return f"JSON syntax error at line {exc.lineno}: {exc.msg}"
    except SyntaxError as exc:
        return f"Python syntax error at line {exc.lineno}: {exc.msg}"
    except (OSError, ValueError):
        return None
    return None


def project_relative(path, cwd):
    """The path relative to the project when it is inside it, else the absolute path."""
    normal = str(path).replace("\\", "/")
    try:
        relative = os.path.relpath(normal, cwd or ".")
    except ValueError:
        return normal
    return normal if relative.startswith("..") else relative.replace(os.sep, "/")


def needs_verification(path, fw, scratch, cwd=None):
    def globs(items):
        return [content_policy.glob_to_regex(g.replace("${scratchpad_dir}", scratch or "")) for g in items
                if scratch or "${scratchpad_dir}" not in g]
    normal = project_relative(path, cwd)
    ver = fw.verification
    return (any(rx.match(normal) for rx in globs(ver["required_after_edits_to"]))
            and not any(rx.match(normal) for rx in globs(ver["exempt"])))


def main(stdin=None, stdout=None, stderr=None):
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        event = json.load(stdin)
    except ValueError:
        print("post_tool_use: input is not JSON", file=stderr)
        return 0
    try:
        fw = policy_store.load_framework()
    except policy_store.PolicyError as exc:
        print(f"post_tool_use: policies could not be loaded: {exc}", file=stderr)
        return 0
    name, tool = event.get("hook_event_name"), event.get("tool_name", "")
    failed = name == "PostToolUseFailure"
    state = audit.SessionState(event.get("session_id"))
    record = {"event": name, "session": event.get("session_id"), "tool": tool, "agent": event.get("agent_type"),
              "ok": not failed}
    notes = []
    if tool == "Bash":
        classes = engine.classify_summary(event)
        record["classes"] = sorted(set(classes or []))
        if classes and set(classes) <= {"read", "test", "lint"} and set(classes) & {"test", "lint"}:
            command = (event.get("tool_input") or {}).get("command", "")
            state.record_verification(not failed, command)
            record["verification"] = "failed" if failed else "passed"
        if failed:
            first = str(event.get("error", "")).splitlines()[:1]
            record["error"] = audit.redact(first[0] if first else "", 60)
    elif tool in WRITE_FIELDS and not failed:
        path = (event.get("tool_input") or {}).get(WRITE_FIELDS[tool])
        if isinstance(path, str) and path:
            record["path"] = audit.redact(path, 300)
            if needs_verification(path, fw, event.get("scratchpad_dir"), event.get("cwd")):
                state.record_edit(path)
                record["needs_verification"] = True
            problem = syntax_problem(path)
            if problem:
                record["syntax_problem"] = True
                notes.append(f"{path} was just changed and no longer parses: {problem}. Fix it before going on.")
            normal = path.replace("\\", "/")
            if any(content_policy.glob_to_regex(g).match(normal) for g in fw.capability["self_protection_paths"]):
                notes.append(f"{path} is policy or guardrail configuration; mention this change to the user.")
    state.save()
    audit.log(record)
    if notes:
        json.dump({"hookSpecificOutput": {"hookEventName": name, "additionalContext": " ".join(notes)}}, stdout)
        stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
