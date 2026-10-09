"""Audit log and per-session state for the framework hooks. Standard library only.

The log records what was decided and why, never what was in a file and never a secret: commands are redacted
and truncated, and file contents are not logged at all. Logging problems never change a decision.
"""
import json
import os
import pathlib
import re
import time

MAX_LOG_BYTES = 5_000_000
COMMAND_LIMIT = 200
KEYWORDS = (r"(?:token|secret|passw(?:or)?d|passwd|pwd|api[_-]?key|apikey|authorization|auth[_-]?(?:token|key)|"
            r"bearer|credential|conn(?:ection)?[_-]?string|sas[_-]?token|signature|private[_-]?key|access[_-]?key|[_-]key)")
REDACTIONS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.S), "***"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 ***"),
    (re.compile(r"(?i)(\b[\w.-]*" + KEYWORDS + r"[\w.-]*\s*[=:]\s*)(?:\"[^\"]*\"|'[^']*'|\S+)"), r"\1***"),
    (re.compile(r"(?i)(--?[\w-]*" + KEYWORDS + r"[\w-]*[ =])(?:\"[^\"]*\"|'[^']*'|[^\s-]\S*)"), r"\1***"),
    (re.compile(r"(\s-p[ =]?)(?:\"[^\"]*\"|'[^']*'|\S+)"), r"\1***"),
    (re.compile(r"(://[^/\s:@]+:)[^@\s]+(@)"), r"\1***\2"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "***"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "***"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*"), "***"),
    (re.compile(r"\b(?=[A-Za-z0-9+/_=-]*\d)(?=[A-Za-z0-9+/_=-]*[A-Za-z])[A-Za-z0-9+/_=-]{32,}\b"), "***"),
]


def redact(text, limit=COMMAND_LIMIT):
    """Hide anything that looks like a credential, then cut the text to a short length."""
    text = str(text)
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def data_dir(environ=None):
    environ = os.environ if environ is None else environ
    configured = environ.get("CLAUDE_PLUGIN_DATA")
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(environ.get("HOME") or os.path.expanduser("~")) / ".claude" / "data" / "data-engineering-ai"


def make_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def log(record, environ=None):
    """Append one JSON line to the audit log. Returns True when written; never raises."""
    try:
        directory = make_dir(data_dir(environ) / "audit")
        target = directory / "decisions.jsonl"
        if target.exists() and target.stat().st_size > MAX_LOG_BYTES:
            target.replace(directory / "decisions.jsonl.1")
        record = dict(record, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def decision_record(event, verdict):
    """What to log about a PreToolUse decision: ids and short redacted text, never file content."""
    args = event.get("tool_input") or {}
    record = {"event": "PreToolUse", "session": event.get("session_id"), "tool": event.get("tool_name"),
              "agent": event.get("agent_type"), "role": verdict.role, "environment": verdict.environment,
              "decision": verdict.decision, "rules": verdict.rule_ids}
    if event.get("tool_name") == "Bash":
        record["command"] = redact(args.get("command", ""))
    else:
        for field in ("file_path", "notebook_path", "path"):
            if isinstance(args.get(field), str):
                record["path"] = redact(args[field], 300)
                break
        if str(event.get("tool_name", "")).startswith("mcp__"):
            record["arguments"] = sorted(args)[:12]
    return record


# --- per-session state ------------------------------------------------------------------------------------


class SessionState:
    """What happened in this session that the Stop hook needs: edits and verification runs, in order."""

    def __init__(self, session_id, environ=None):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id or "unknown"))[:80]
        self.path = data_dir(environ) / "sessions" / f"{safe}.json"
        self.data = {"seq": 0, "edits": [], "last_edit_seq": 0, "passed_seq": 0, "failed_seq": 0,
                     "last_verification": ""}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except (OSError, ValueError):
            pass

    def tick(self):
        self.data["seq"] += 1
        return self.data["seq"]

    def record_edit(self, path):
        self.data["last_edit_seq"] = self.tick()
        edits = [p for p in self.data["edits"] if p != path] + [path]
        self.data["edits"] = edits[-50:]

    def record_verification(self, passed, summary):
        seq = self.tick()
        self.data["passed_seq" if passed else "failed_seq"] = seq
        self.data["last_verification"] = redact(summary, 80)

    @property
    def outstanding(self):
        """True when source files changed after the last passing test or lint run."""
        return bool(self.data["edits"]) and self.data["passed_seq"] < self.data["last_edit_seq"]

    @property
    def last_run_failed(self):
        return self.data["failed_seq"] > self.data["passed_seq"]

    def save(self):
        try:
            make_dir(self.path.parent)
            self.path.write_text(json.dumps(self.data), encoding="utf-8")
            return True
        except Exception:
            return False

    def reset(self):
        self.data.update({"seq": 0, "edits": [], "last_edit_seq": 0, "passed_seq": 0, "failed_seq": 0,
                          "last_verification": ""})
