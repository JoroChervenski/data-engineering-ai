"""Content policy: no AI signature in commits, pull requests, issues, tickets or tasks.

The rule and its scope are data, in policies/content-policy.json. This module only applies them to one
PreToolUse event and says what to do: deny, ask, or nothing. Standard library only.

Only text that is being written is inspected: a shell command that publishes (git commit, gh pr, ...),
the new content of a ticket, ADR or runbook note, and the arguments of a create/update MCP tool. Text being
removed (old_string) and ordinary reads (grep, git log) are never inspected, so a signature can be taken out.
"""
import json
import pathlib
import re
import shlex

POLICY_PATH = pathlib.Path(__file__).resolve().parent.parent / "policies" / "content-policy.json"
MAX_FILE_BYTES = 200_000

# Where a command can start: beginning of text or line, after ; & | ( ` $( and optional VAR=value prefixes.
COMMAND_POSITION = r"(?:^|[;&|(`]|\$\()\s*(?:\w+=\S*\s+)*(?:sudo\s+|command\s+|exec\s+)?"
# Used only when the policy file cannot be read: a conservative stand-in for its scope.
FALLBACK_SCOPE = re.compile(r"\bgit\s+commit\b|\bgh\s+(?:pr|issue)\b|/\.ai/")
FILE_TOOLS = {"Write": ("content",), "Edit": ("new_string",), "NotebookEdit": ("new_source",)}


class PolicyError(Exception):
    """The policy file is missing or invalid."""


class Policy:
    def __init__(self, message, patterns, commands, files, mcp):
        self.message, self.patterns, self.commands, self.files, self.mcp = message, patterns, commands, files, mcp


def glob_to_regex(glob):
    """Translate a glob ('*' within a segment, '**' across segments) into an anchored regex."""
    folder_too = glob.endswith("/**")
    core = glob[:-3] if folder_too else glob
    out, i = "", 0
    while i < len(core):
        if core.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif core.startswith("**", i):
            out += ".*"
            i += 2
        elif core[i] == "*":
            out += "[^/]*"
            i += 1
        elif core[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(core[i])
            i += 1
    return re.compile(out + ("(?:/.*)?" if folder_too else "") + r"\Z")


def load_policy(path=POLICY_PATH):
    path = pathlib.Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rule = data["rules"]["no_ai_signature"]
        scope = data["scope"]
        patterns = [(p["name"], re.compile(p["regex"], re.IGNORECASE)) for p in rule["patterns"]]
        commands = [re.compile(COMMAND_POSITION + c, re.IGNORECASE | re.MULTILINE)
                    for c in scope["bash_publishing_commands"]]
        files = [glob_to_regex(g) for g in scope["files"]]
        mcp = re.compile(scope["mcp_tools"])
        message = rule["message"]
    except (OSError, ValueError, KeyError, TypeError, re.error) as exc:
        raise PolicyError(f"{path}: {type(exc).__name__}: {exc}")
    if not patterns or not isinstance(message, str):
        raise PolicyError(f"{path}: the rule needs a message and at least one pattern")
    return Policy(message, patterns, commands, files, mcp)


def find_signatures(text, policy):
    found = []
    for name, regex in policy.patterns:
        match = regex.search(text)
        if match:
            found.append((name, match.group(0).strip()))
    return found


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


def message_files(command, cwd):
    """Files whose content becomes the message: git commit -F file, gh ... --body-file file."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    paths = []
    for i, token in enumerate(tokens):
        if token in ("-F", "--file", "--body-file") and i + 1 < len(tokens):
            paths.append(tokens[i + 1])
        elif token.startswith(("--file=", "--body-file=")):
            paths.append(token.split("=", 1)[1])
    texts = []
    for raw in paths:
        if raw == "-":
            continue
        path = pathlib.Path(raw)
        if not path.is_absolute():
            path = pathlib.Path(cwd or ".") / path
        try:
            if path.is_file() and path.stat().st_size <= MAX_FILE_BYTES:
                texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return texts


def path_in_scope(file_path, policy):
    normalised = str(file_path or "").replace("\\", "/")
    return any(rx.match(normalised) for rx in policy.files)


def written_texts(event, policy):
    """(where, text) pairs this tool call would store."""
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    if tool == "Bash":
        command = args.get("command") or ""
        if not any(rx.search(command) for rx in policy.commands):
            return []
        texts = [("commit, pull request or issue command", command)]
        texts += [("commit or pull request message file", t) for t in message_files(command, event.get("cwd"))]
        return texts
    if tool in FILE_TOOLS or tool == "MultiEdit":
        if not path_in_scope(args.get("file_path") or args.get("notebook_path"), policy):
            return []
        if tool == "MultiEdit":
            return [("ticket, decision or runbook note", e.get("new_string") or "")
                    for e in args.get("edits") or [] if isinstance(e, dict)]
        return [("ticket, decision or runbook note", args.get(field) or "") for field in FILE_TOOLS[tool]]
    if policy.mcp.search(tool):
        return [("issue, pull request or task", s) for s in strings_in(args)]
    return []


def decision(kind, reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": kind,
                                   "permissionDecisionReason": reason}}


def decide(event, policy_path=POLICY_PATH):
    """Return a hook decision (dict) or None when the policy has nothing to say."""
    try:
        policy = load_policy(policy_path)
    except PolicyError as exc:
        # Cannot tell what is in scope, so ask a person for the calls that are most likely to be in it.
        tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
        probe = args.get("command") or args.get("file_path") or ""
        if tool.startswith("mcp__") or FALLBACK_SCOPE.search(str(probe)):
            return decision("ask", f"The content policy could not be read ({exc}). Ask the owner before "
                                   "writing a commit, pull request, issue or ticket note.")
        return None
    for where, text in written_texts(event, policy):
        found = find_signatures(text, policy)
        if found:
            name, matched = found[0]
            reason = policy.message.replace("{matched}", matched).replace("{where}", where)
            return decision("deny", f"{reason} [{name}]")
    return None
