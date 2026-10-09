#!/usr/bin/env python3
"""Stop hook: keeps Claude from declaring work complete while required verification is outstanding.

If source files changed in this session after the last passing test or lint run, it blocks the stop once, with
the reason and a summary of uncommitted changes. It never blocks twice in a row (stop_hook_active), so it
cannot loop. Claude Code also caps consecutive stop blocks.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit  # noqa: E402
import engine  # noqa: E402


def names(paths, limit=4):
    shown = [pathlib.PurePosixPath(p.replace("\\", "/")).name for p in paths[-limit:]]
    more = len(paths) - len(shown)
    return ", ".join(shown) + (f" and {more} more" if more > 0 else "")


def build_reason(state, git):
    edits = state.data["edits"]
    why = ("the last test or lint run failed" if state.last_run_failed
           else "no test or lint run has passed since")
    reason = (f"Verification is outstanding: {len(edits)} source file(s) changed ({names(edits)}) and {why}. "
              "Run the project's tests or linters and fix any failure, or tell the user plainly that "
              "verification has not been done. Do not say the work is complete.")
    if git:
        reason += f" Uncommitted: {git[1]} modified, {git[2]} untracked on branch {git[0]}."
    return reason


def main(stdin=None, stdout=None, stderr=None):
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        event = json.load(stdin)
    except ValueError:
        return 0
    try:
        state = audit.SessionState(event.get("session_id"))
        if not state.outstanding or event.get("stop_hook_active"):
            if state.outstanding:
                audit.log({"event": "Stop", "session": event.get("session_id"), "decision": "allow",
                           "rules": ["VER-01"], "note": "verification outstanding, already blocked once"})
            return 0
        reason = build_reason(state, engine.git_summary(event.get("cwd") or os.getcwd()))
        audit.log({"event": "Stop", "session": event.get("session_id"), "decision": "block", "rules": ["VER-01"],
                   "edits": len(state.data["edits"])})
        json.dump({"decision": "block", "reason": reason}, stdout)
        stdout.write("\n")
    except Exception as exc:
        print(f"stop: {type(exc).__name__}: {exc}", file=stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
