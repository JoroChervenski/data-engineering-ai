#!/usr/bin/env python3
"""PreToolUse hook: applies the framework's policies before a tool runs.

Claude Code passes the call as JSON on stdin. The hook prints a decision as JSON (deny or ask), or nothing when
no policy objects. Every deny or ask is written to the audit log, redacted. A crash asks a person rather than
letting the call through unchecked.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit  # noqa: E402
import content_policy  # noqa: E402
import engine  # noqa: E402


def main(stdin=None, stdout=None, stderr=None):
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        event = json.load(stdin)
    except ValueError:
        print("pre_tool_use: input is not JSON; no policy applied", file=stderr)
        return 0
    try:
        verdict = engine.evaluate(event)
        if verdict.decision:
            audit.log(audit.decision_record(event, verdict))
        result = engine.hook_output(verdict)
    except Exception as exc:  # a broken hook must be visible, not silently skipped
        result = content_policy.decision(
            "ask", f"The policy hook failed ({type(exc).__name__}). Ask the owner before continuing.")
        audit.log({"event": "PreToolUse", "tool": event.get("tool_name") if isinstance(event, dict) else None,
                   "decision": "ask", "rules": ["HOOK-ERROR"], "error": type(exc).__name__})
    if result:
        json.dump(result, stdout)
        stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
