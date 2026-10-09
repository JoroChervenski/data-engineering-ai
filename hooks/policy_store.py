"""Loads the framework policies, the project's guardrails and the project's environment.

Framework policies live in policies/*.json and are validated strictly: anything missing or of the wrong type
raises PolicyError, and the caller must then fail closed. The project's .ai/guardrails.json can only make
things stricter. If it is malformed it is ignored as a whole and the environment becomes unknown, which is
the restrictive choice. Standard library only.
"""
import json
import os
import pathlib
import re

POLICY_DIR = pathlib.Path(__file__).resolve().parent.parent / "policies"
ROLES_FOR_PROJECT_DEFAULT = ("architect", "reviewer", "verifier", "developer")
CLASS_NAMES = ("read", "test", "lint", "dev", "install", "network", "remote_write", "deploy", "privileged",
               "sql_write", "destructive", "secret", "unknown")


class PolicyError(Exception):
    """A framework policy file is missing or invalid."""


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PolicyError(f"{path}: {type(exc).__name__}: {exc}")


def need(data, dotted, kind, where):
    value = data
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            raise PolicyError(f"{where}: missing '{dotted}'")
        value = value[key]
    if not isinstance(value, kind):
        raise PolicyError(f"{where}: '{dotted}' must be {getattr(kind, '__name__', kind)}")
    return value


class Framework:
    """The framework policies, validated. Attributes are the parsed JSON documents."""

    def __init__(self, directory):
        self.directory = pathlib.Path(directory)
        self.command = read_json(self.directory / "command-policy.json")
        self.capability = read_json(self.directory / "capability-policy.json")
        self.environment = read_json(self.directory / "environment-policy.json")
        self.production = read_json(self.directory / "production-policy.json")
        self.secret = read_json(self.directory / "secret-policy.json")
        self.verification = read_json(self.directory / "verification-policy.json")
        self.validate()

    def validate(self):
        cap, env, prod, sec, ver = (self.capability, self.environment, self.production, self.secret,
                                    self.verification)
        need(self.command, "rules", list, "command-policy")
        need(self.command, "wrappers", dict, "command-policy")
        need(cap, "default_role", str, "capability-policy")
        need(cap, "agent_roles", dict, "capability-policy")
        roles = need(cap, "roles", dict, "capability-policy")
        modes = need(cap, "shell_modes", dict, "capability-policy")
        for name, role in roles.items():
            need(role, "shell.mode", str, f"capability-policy role {name}")
            need(role, "write", bool, f"capability-policy role {name}")
            if role["shell"]["mode"] not in modes:
                raise PolicyError(f"capability-policy: role {name} uses unknown shell mode")
        for name, table in modes.items():
            for cls in CLASS_NAMES:
                if table.get(cls) not in ("allow", "ask", "deny", "none"):
                    raise PolicyError(f"capability-policy: shell mode {name} has no valid entry for {cls}")
        if cap["default_role"] not in roles or cap.get("unknown_agent_role") not in roles:
            raise PolicyError("capability-policy: default roles must be defined roles")
        for role in cap["agent_roles"].values():
            if role not in roles:
                raise PolicyError(f"capability-policy: agent maps to unknown role {role}")
        need(cap, "approval_paths", list, "capability-policy")
        need(cap, "self_protection_paths", list, "capability-policy")
        need(env, "environment_variable", str, "environment-policy")
        need(env, "manifest_file", str, "environment-policy")
        need(env, "project_policy_file", str, "environment-policy")
        need(env, "unknown_environment.deploy", str, "environment-policy")
        need(prod, "production_tokens_regex", str, "production-policy")
        need(prod, "shell_write_operations", bool, "production-policy")
        need(sec, "protected_paths", list, "secret-policy")
        need(ver, "required_after_edits_to", list, "verification-policy")
        try:
            re.compile(prod["production_tokens_regex"])
            re.compile(cap["restricted_mcp_tools"])
            re.compile(sec["glob_hint_regex"], re.IGNORECASE)
        except (re.error, KeyError) as exc:
            raise PolicyError(f"invalid regular expression in the policies: {exc}")


def load_framework(directory=POLICY_DIR):
    return Framework(directory)


# --- the project ------------------------------------------------------------------------------------------


class Project:
    """The project's guardrails (if any) and anything wrong with them."""

    def __init__(self, root, path, data, errors, notes):
        self.root, self.path, self.data, self.errors, self.notes = root, path, data, errors, notes

    @property
    def valid(self):
        return not self.errors


def find_up(start, relative, depth):
    current = pathlib.Path(start or ".").resolve()
    for _ in range(max(1, depth)):
        candidate = current / relative
        if candidate.is_file():
            return current, candidate
        if current.parent == current:
            break
        current = current.parent
    return None, None


def string_list(value, label, errors):
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{label} must be a list of non-empty strings")
        return []
    return value


def load_project(cwd, fw):
    relative = fw.environment["project_policy_file"]
    root, path = find_up(cwd, relative, fw.environment.get("search_depth", 8))
    if path is None:
        return Project(None, None, {}, [], [])
    errors, notes = [], []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return Project(root, path, {}, [f"cannot read {relative}: {type(exc).__name__}"], [])
    if not isinstance(raw, dict):
        return Project(root, path, {}, [f"{relative} must be a JSON object"], [])
    data = {}
    commands = raw.get("commands", {})
    if not isinstance(commands, dict):
        errors.append("commands must be an object")
        commands = {}
    data["deny"] = string_list(commands.get("deny"), "commands.deny", errors)
    data["approval_required"] = string_list(commands.get("approval_required"), "commands.approval_required", errors)
    production = raw.get("production", {})
    if not isinstance(production, dict) or not all(isinstance(v, bool) for v in production.values()):
        errors.append("production must be an object of true/false values")
        production = {}
    if production.get("shell_write_operations") is True:
        notes.append("production.shell_write_operations: true is ignored; a project cannot loosen production")
    secrets = raw.get("secrets", {})
    if not isinstance(secrets, dict):
        errors.append("secrets must be an object")
        secrets = {}
    data["allow_paths"] = string_list(secrets.get("allow_paths"), "secrets.allow_paths", errors)
    data["protected_paths"] = string_list(secrets.get("protected_paths"), "secrets.protected_paths", errors)
    default_role = raw.get("default_role")
    if default_role is not None:
        if default_role in ROLES_FOR_PROJECT_DEFAULT and default_role in fw.capability["roles"]:
            data["default_role"] = default_role
        else:
            errors.append(f"default_role must be one of {', '.join(ROLES_FOR_PROJECT_DEFAULT)}")
    verification = raw.get("verification", {})
    if not isinstance(verification, dict):
        errors.append("verification must be an object")
        verification = {}
    data["verification_commands"] = string_list(verification.get("commands"), "verification.commands", errors)
    data["expected_tools"] = string_list(raw.get("expected_tools"), "expected_tools", errors)
    if errors:
        return Project(root, path, {}, errors, notes)
    return Project(root, path, data, [], notes)


# --- the manifest and the environment ---------------------------------------------------------------------


def manifest_text(cwd, fw):
    root, path = find_up(cwd, fw.environment["manifest_file"], fw.environment.get("search_depth", 8))
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def manifest_scalar(text, parent, key):
    """A quoted or bare scalar two levels deep, e.g. ('framework', 'version'). None when absent."""
    if not text:
        return None
    in_block = False
    for line in text.splitlines():
        if re.match(rf"^{re.escape(parent)}:\s*(#.*)?$", line):
            in_block = True
            continue
        if in_block and re.match(r"^\S", line):
            break
        match = re.match(rf"^\s+{re.escape(key)}:\s*(?:\"([^\"]*)\"|([^\s#]+))", line) if in_block else None
        if match:
            return match.group(1) if match.group(1) is not None else match.group(2)
    return None


def manifest_environments(text):
    """The environments block: a list of {name, write_access}. Raises PolicyError when it is malformed."""
    if text is None:
        return None
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"^environments:\s*(?:\[\])?\s*(#.*)?$", line)), None)
    if start is None:
        return None
    environments, current = [], None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            break
        item = re.match(r"^\s*-\s*name:\s*\"?([\w.-]+)\"?\s*(#.*)?$", line)
        access = re.match(r"^\s+write_access:\s*(true|false)\s*(#.*)?$", line)
        if item:
            current = {"name": item.group(1), "write_access": None}
            environments.append(current)
        elif access and current is not None:
            current["write_access"] = access.group(1) == "true"
        else:
            raise PolicyError(f"environments: cannot read this line: {stripped[:60]}")
    for env in environments:
        if env["write_access"] is None:
            raise PolicyError(f"environments: {env['name']} has no write_access true/false")
    return environments


class Environment:
    def __init__(self, name, known, write_access, reason):
        self.name, self.known, self.write_access, self.reason = name, known, write_access, reason

    @property
    def label(self):
        return self.name if self.known else "unknown"

    @property
    def production_like(self):
        return self.known and self.write_access is False


def resolve_environment(cwd, fw, project, environ=None):
    environ = os.environ if environ is None else environ
    name = environ.get(fw.environment["environment_variable"], "").strip()
    variable = fw.environment["environment_variable"]
    if not project.valid:
        return Environment(name or None, False, None, "the project's guardrails are invalid, so no environment is trusted")
    if not name:
        return Environment(None, False, None, f"{variable} is not set")
    try:
        environments = manifest_environments(manifest_text(cwd, fw))
    except PolicyError as exc:
        return Environment(name, False, None, str(exc))
    if not environments:
        return Environment(name, False, None, "the manifest defines no environments")
    for env in environments:
        if env["name"] == name:
            return Environment(name, True, env["write_access"], "")
    return Environment(name, False, None, f"{name} is not an environment in the manifest")
