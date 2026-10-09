"""Decides what to do with one tool call: nothing to say (None), ask a person, or deny.

It combines, for the calling role and the current environment:
  - the command policy (what a shell command is),
  - the capability policy (what each role may do with each kind of command, and with files),
  - the environment and production policies (where deployment is allowed),
  - the secret policy (paths no tool may touch),
  - the content policy (no AI signature),
  - the project's guardrails, which can only add restrictions.
Every decision is made by data and code, never by asking a model. Standard library only.
"""
import os
import posixpath
import re
import shutil
import subprocess

import command_policy
import content_policy
import policy_store
import shell_parser
from policy_store import PolicyError

STRENGTH = {"none": 0, "allow": 1, "ask": 2, "deny": 3}
BASE_TO_LEVEL = {"allow": "allow", "approval_required": "ask", "deny": "deny", None: "none"}
READ_TOOLS = {"Read": ("file_path",), "Grep": ("path",), "Glob": ("path",)}
WRITE_TOOLS = {"Write": ("file_path",), "Edit": ("file_path",), "MultiEdit": ("file_path",),
               "NotebookEdit": ("notebook_path",)}
GLOB_FIELDS = {"Grep": ("glob",), "Glob": ("pattern",)}
FALLBACK_ASK = re.compile(r"\bgit\s+push\b|\bterraform\s+(?:apply|destroy)\b|\baz\s+deployment\b|\bkubectl\s+apply\b")
FALLBACK_DENY = [re.compile(r, re.I) for r in (
    r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(?:--\s+)?(?:/|~|\$HOME)(?=[\s/\"']|$)", r"\bgit\s+push\b[^\n]*(?:--force|\s-f\b|\s\+)",
    r"\bgit\s+reset\s+--hard\b", r"\bDROP\s+(?:DATABASE|SCHEMA)\b", r"\bcurl\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b")]
FALLBACK_PATHS = re.compile(r"\.ssh/|\.azure/|\.config/gh/|(?:^|/)\.env(?:\.|$)|credentials|secrets", re.I)


class Verdict:
    def __init__(self):
        self.decision = None
        self.items = []           # (level, rule_id, reason)
        self.notes = []
        self.role = None
        self.environment = None
        self.classes = []

    def add(self, level, rule_id, reason):
        if STRENGTH[level] >= STRENGTH["ask"]:
            self.items.append((level, rule_id, reason))
            if STRENGTH[level] > STRENGTH[self.decision or "none"]:
                self.decision = level

    @property
    def rule_ids(self):
        return [rule_id for _, rule_id, _ in self.items]

    def reason(self):
        ranked = sorted(self.items, key=lambda item: -STRENGTH[item[0]])
        text = " ".join(f"{reason} [{rule_id}]" for _, rule_id, reason in ranked[:3])
        if len(ranked) > 3:
            text += f" (and {len(ranked) - 3} more)"
        return f"{text} (role: {self.role}; environment: {self.environment})"


# --- context ----------------------------------------------------------------------------------------------


class SecretRule:
    def __init__(self, glob, never_allow, exempt):
        self.glob, self.never_allow = glob, never_allow
        self.regex = content_policy.glob_to_regex(glob)
        self.exempt = [content_policy.glob_to_regex(g) for g in exempt]


class Context:
    def __init__(self, event, fw, project, environment, role, role_source, environ):
        self.event, self.fw, self.project, self.environment = event, fw, project, environment
        self.role, self.role_source = role, role_source
        self.role_spec = fw.capability["roles"][role]
        self.mode = self.role_spec["shell"]["mode"]
        self.table = fw.capability["shell_modes"][self.mode]
        self.cwd = event.get("cwd") or os.getcwd()
        self.home = environ.get("HOME") or os.path.expanduser("~")
        self.scratch = event.get("scratchpad_dir")
        self.production_tokens = re.compile(fw.production["production_tokens_regex"], re.I)
        self.policy = command_policy.CommandPolicy(fw.command)
        self.secret_rules = [SecretRule(e["glob"], bool(e.get("never_allow")), e.get("exempt", []))
                             for e in fw.secret["protected_paths"]]
        self.secret_rules += [SecretRule(g, True, []) for g in project.data.get("protected_paths", [])]
        self.allow_paths = [content_policy.glob_to_regex(g) for g in project.data.get("allow_paths", [])]
        self.approval = [content_policy.glob_to_regex(g) for g in fw.capability["approval_paths"]]
        self.self_protect = [content_policy.glob_to_regex(g) for g in fw.capability["self_protection_paths"]]
        scratch_globs = [g for g in fw.capability["write_allowed_for_read_only_roles"] if "${scratchpad_dir}" in g]
        other_globs = [g for g in fw.capability["write_allowed_for_read_only_roles"] if "${scratchpad_dir}" not in g]
        self.write_allowed_scratch = ([content_policy.glob_to_regex(g.replace("${scratchpad_dir}", self.scratch))
                                       for g in scratch_globs] if self.scratch else [])
        self.write_allowed_elsewhere = [content_policy.glob_to_regex(g) for g in other_globs]


def resolve_role(event, fw, project):
    cap = fw.capability
    agent = event.get("agent_type")
    if agent:
        name = agent
        for prefix in cap.get("agent_prefixes", []):
            if name.startswith(prefix):
                name = name[len(prefix):]
        return cap["agent_roles"].get(name, cap["unknown_agent_role"]), f"subagent {agent}"
    return project.data.get("default_role", cap["default_role"]), "main conversation"


def build_context(event, fw, environ):
    cwd = event.get("cwd") or os.getcwd()
    project = policy_store.load_project(cwd, fw)
    environment = policy_store.resolve_environment(cwd, fw, project, environ)
    role, source = resolve_role(event, fw, project)
    return Context(event, fw, project, environment, role, source, environ)


# --- paths and secrets ------------------------------------------------------------------------------------


def normalise_path(raw, ctx):
    path = str(raw).strip().strip("'\"").replace("\\", "/")
    for variable in ("${HOME}", "$HOME"):
        if path.startswith(variable):
            path = ctx.home + path[len(variable):]
    if path == "~" or path.startswith("~/"):
        path = ctx.home + path[1:]
    if "$" not in path:
        path = posixpath.normpath(path) if path else path
    return path


def secret_match(raw, ctx):
    """The protected glob this path falls under, or None."""
    path = normalise_path(raw, ctx)
    for rule in ctx.secret_rules:
        if not rule.regex.match(path) or any(x.match(path) for x in rule.exempt):
            continue
        if not rule.never_allow and any(a.match(path) for a in ctx.allow_paths):
            continue
        return rule.glob
    return None


def inside_project(path, ctx):
    try:
        return not os.path.relpath(path, ctx.cwd).startswith("..")
    except ValueError:
        return False


def write_allowed(path, ctx):
    """Read-only roles may write only to the session's scratch space, and to /tmp outside the project."""
    if any(rx.match(path) for rx in ctx.write_allowed_scratch):
        return True
    return not inside_project(path, ctx) and any(rx.match(path) for rx in ctx.write_allowed_elsewhere)


def matches_any(path, regexes):
    return any(rx.match(path) for rx in regexes)


def path_like(value, key_names):
    return ("/" in value or value.startswith((".", "~", "$")) or value in key_names
            or re.search(r"\.[A-Za-z0-9]{1,8}$", value) is not None)


def bash_path_candidates(cmd, ctx):
    sec = ctx.fw.secret
    key_names = set(sec.get("key_file_names", []))
    skip_pattern = cmd.program in sec.get("search_programs", [])
    args = [] if cmd.program in sec.get("output_only_programs", []) else cmd.args
    values = []
    for arg in args:
        if arg.startswith("-"):
            if "=" not in arg:
                continue
            arg = arg.split("=", 1)[1]
        elif "=" in arg and not path_like(arg.split("=", 1)[0], key_names):
            arg = arg.split("=", 1)[1]
        elif skip_pattern:
            skip_pattern = False
            continue
        if "://" in arg or not arg or not path_like(arg, key_names):
            continue
        values.append(arg)
    for op, target in cmd.redirects:
        if not (op in (">&", "<&") and re.fullmatch(r"\d+|-", target)) and op not in ("<<", "<<-", "<<<"):
            values.append(target)
    return values


# --- the decision for one classified command ---------------------------------------------------------------


def stronger(a, b):
    return a if STRENGTH[a] >= STRENGTH[b] else b


def deploy_level(ctx, text):
    """(level, reason) for a deploy-class command, from the role, the environment and the target."""
    capability = ctx.role_spec.get("deploy")
    env = ctx.environment
    if capability in (False, None):
        return "deny", f"the {ctx.role} role may not deploy"
    if not env.known and ctx.fw.environment["unknown_environment"]["deploy"] == "deny":
        return "deny", (f"the environment is unknown ({env.reason}); set "
                        f"{ctx.fw.environment['environment_variable']} to an environment in the manifest")
    targets_production = env.production_like or bool(ctx.production_tokens.search(text))
    if capability == "approval_required_non_production":
        if targets_production:
            return "deny", "production deployment needs the deployer role and a person's approval"
        return "ask", "deployment needs a person's approval"
    if capability == "approval_required":
        return "ask", "deployment needs a person's approval" + (" (production)" if targets_production else "")
    return "deny", "deployment is not allowed"


def apply_finding(verdict, ctx, program, finding):
    """Turn one classified command into a decision for the calling role and environment."""
    cls = finding.cls
    base = BASE_TO_LEVEL[finding.decision]
    role_level = ctx.table.get(cls, "none")
    level = stronger(base, role_level)
    reason = finding.reason
    if STRENGTH[role_level] > STRENGTH[base] and role_level in ("ask", "deny"):
        if cls == "unknown":
            reason = f"'{program}' is not an approved command for the {ctx.role} role"
        else:
            need = "needs a person's approval" if role_level == "ask" else "is not allowed"
            reason = f"a {cls} command {need} for the {ctx.role} role"
    if cls == "deploy":
        dlevel, dreason = deploy_level(ctx, finding.command)
        if STRENGTH[dlevel] >= STRENGTH[level]:
            level, reason = dlevel, f"{finding.reason} {dreason}."
    if (cls in ("dev", "install") and ctx.environment.known and ctx.environment.write_access is False
            and not ctx.fw.production["shell_write_operations"]):
        level, reason = "deny", f"environment {ctx.environment.name} is read-only, so shell writes are not allowed"
    verdict.add(level, finding.rule_id or f"ROLE-{cls}", f"{reason or 'not allowed'}: {finding.command[:80]}")


def check_dev_paths(verdict, ctx, cmd, finding):
    """File changes made through the shell to infrastructure or policy files need approval too."""
    if finding.cls != "dev":
        return
    for path in bash_path_candidates(cmd, ctx):
        normal = normalise_path(path, ctx)
        if matches_any(normal, ctx.self_protect):
            verdict.add("ask", "PROT-01", f"this changes policy or guardrail configuration ({path})")
        elif matches_any(normal, ctx.approval):
            verdict.add("ask", "PROT-02", f"this changes infrastructure or schema files ({path})")


def findings_for(cmd, ctx):
    """Everything the policies say about one normalised command."""
    policy = ctx.policy
    base = command_policy.classify(cmd, policy)
    if base.cls == "unknown" and ctx.mode == "verification" and any(
            command_policy.phrase_matches(cmd, p) for p in ctx.project.data.get("verification_commands", [])):
        base = command_policy.Finding("allow", "test", "PRJ-V", "approved verification command", cmd.raw)
    findings = [base] + command_policy.extra_findings(cmd, policy)
    for index, phrase in enumerate(ctx.project.data.get("deny", [])):
        if command_policy.phrase_matches(cmd, phrase):
            findings.append(command_policy.Finding("deny", "destructive", f"PRJ-D{index + 1}",
                                                   "the project forbids this command", cmd.raw))
    for index, phrase in enumerate(ctx.project.data.get("approval_required", [])):
        if command_policy.phrase_matches(cmd, phrase):
            findings.append(command_policy.Finding("approval_required", "remote_write", f"PRJ-A{index + 1}",
                                                   "the project requires approval for this command", cmd.raw))
    if base.cls == "unknown" and len(findings) > 1:
        findings = findings[1:]                       # the other findings already classify this command
    return findings


def evaluate_bash(verdict, ctx):
    command = (ctx.event.get("tool_input") or {}).get("command") or ""
    policy = ctx.policy
    try:
        commands = command_policy.normalize(shell_parser.parse(command), policy)
    except shell_parser.ParseError as exc:
        if any(rx.search(command) for rx in policy.destructive_fallback):
            verdict.add("deny", "CMD-D90", f"this command looks destructive and could not be parsed ({exc})")
        else:
            verdict.add("ask", "CMD-X01", f"this command could not be parsed ({exc}); a person should look at it")
        return
    command_policy.attach_piped_input(commands, policy)
    for cmd in commands:
        for finding in findings_for(cmd, ctx):
            verdict.classes.append(finding.cls)
            apply_finding(verdict, ctx, cmd.program, finding)
            check_dev_paths(verdict, ctx, cmd, finding)
        for value in bash_path_candidates(cmd, ctx):
            glob = secret_match(value, ctx)
            if glob:
                verdict.add("deny", "SEC-01", f"{value} is protected by the secret policy ({glob}); "
                                              "credentials are never read or printed")
    for finding in (command_policy.pipeline_findings(commands, policy)
                    + command_policy.raw_findings(command, policy)):
        verdict.classes.append(finding.cls)
        apply_finding(verdict, ctx, "", finding)


def evaluate_file(verdict, ctx):
    tool, args = ctx.event.get("tool_name", ""), ctx.event.get("tool_input") or {}
    fields = READ_TOOLS.get(tool) or WRITE_TOOLS.get(tool) or ()
    paths = [args[f] for f in fields if isinstance(args.get(f), str) and args[f]]
    for path in paths:
        glob = secret_match(path, ctx)
        if glob:
            verdict.add("deny", "SEC-01", f"{path} is protected by the secret policy ({glob}); "
                                          "credentials are never read or printed")
    hint = re.compile(ctx.fw.secret["glob_hint_regex"], re.I)
    for field in GLOB_FIELDS.get(tool, ()):
        value = args.get(field)
        if isinstance(value, str) and hint.search(value):
            verdict.add("deny", "SEC-02", f"the search pattern {value!r} points at secret files")
    if tool in WRITE_TOOLS:
        for path in paths:
            normal = normalise_path(path, ctx)
            if not ctx.role_spec["write"] and not write_allowed(normal, ctx):
                verdict.add("deny", "ROLE-W", f"the {ctx.role} role cannot modify files ({path})")
            elif matches_any(normal, ctx.self_protect):
                verdict.add("ask", "PROT-01", f"this changes policy or guardrail configuration ({path})")
            elif matches_any(normal, ctx.approval):
                verdict.add("ask", "PROT-02", f"this changes infrastructure or schema files ({path})")


def evaluate_mcp(verdict, ctx):
    tool = ctx.event.get("tool_name", "")
    if re.search(ctx.fw.capability["restricted_mcp_tools"], tool) and ctx.mode in ("read_only", "verification"):
        verdict.add("deny", "ROLE-M", f"the {ctx.role} role cannot call {tool}, which changes something")


def apply_content_policy(verdict, ctx, policy_dir):
    out = content_policy.decide(ctx.event, os.path.join(str(policy_dir), "content-policy.json"))
    if out:
        data = out["hookSpecificOutput"]
        rule = "CP-01" if data["permissionDecision"] == "deny" else "CP-00"
        verdict.add(data["permissionDecision"], rule, data["permissionDecisionReason"])


def fallback_verdict(event, verdict, error):
    """The framework policies cannot be loaded: a small built-in baseline, failing closed."""
    verdict.role, verdict.environment = "unknown", "unknown"
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    verdict.notes.append(f"policies could not be loaded: {error}")
    command = args.get("command") or ""
    path = args.get("file_path") or args.get("path") or ""
    if tool == "Bash":
        if any(rx.search(command) for rx in FALLBACK_DENY):
            verdict.add("deny", "FALLBACK-D", "the policies could not be loaded and this command looks destructive")
        elif FALLBACK_ASK.search(command) or FALLBACK_PATHS.search(command):
            verdict.add("ask", "FALLBACK-A", "the policies could not be loaded; a person must approve this command")
    elif path and FALLBACK_PATHS.search(str(path)):
        verdict.add("deny", "FALLBACK-S", f"the policies could not be loaded and {path} may hold secrets")
    return verdict


def evaluate(event, environ=None, policy_dir=policy_store.POLICY_DIR):
    environ = os.environ if environ is None else environ
    verdict = Verdict()
    try:
        fw = policy_store.load_framework(policy_dir)
    except PolicyError as exc:
        return fallback_verdict(event, verdict, exc)
    ctx = build_context(event, fw, environ)
    verdict.role, verdict.environment = ctx.role, ctx.environment.label
    verdict.notes += [f"project guardrails ignored: {e}" for e in ctx.project.errors] + ctx.project.notes
    tool = event.get("tool_name", "")
    if tool == "Bash":
        evaluate_bash(verdict, ctx)
    elif tool in READ_TOOLS or tool in WRITE_TOOLS:
        evaluate_file(verdict, ctx)
    elif tool.startswith("mcp__"):
        evaluate_mcp(verdict, ctx)
    apply_content_policy(verdict, ctx, policy_dir)
    return verdict


def classify_summary(event, policy_dir=policy_store.POLICY_DIR):
    """The classes of a Bash command (used by PostToolUse to recognise a test or lint run), or None."""
    try:
        fw = policy_store.load_framework(policy_dir)
        policy = command_policy.CommandPolicy(fw.command)
        project = policy_store.load_project(event.get("cwd") or os.getcwd(), fw)
        commands = command_policy.normalize(
            shell_parser.parse((event.get("tool_input") or {}).get("command") or ""), policy)
        classes = []
        for cmd in commands:
            if cmd.program == ":":
                continue
            cls = command_policy.classify(cmd, policy).cls
            if cls == "unknown" and any(command_policy.phrase_matches(cmd, p)
                                        for p in project.data.get("verification_commands", [])):
                cls = "test"
            classes.append(cls)
        return classes
    except (PolicyError, shell_parser.ParseError):
        return None


def hook_output(verdict):
    if not verdict.decision:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": verdict.decision,
                                   "permissionDecisionReason": verdict.reason()}}


def tools_missing(names):
    return [name for name in names if shutil.which(name) is None]


def git_summary(cwd):
    """(branch, modified, untracked) for the repository at cwd, or None."""
    try:
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
        try:
            branch = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "HEAD"], capture_output=True,
                                    text=True, check=True, env=env).stdout.strip()
        except subprocess.CalledProcessError:       # detached HEAD
            branch = "detached " + subprocess.run(["git", "-C", cwd, "rev-parse", "--short", "HEAD"],
                                                  capture_output=True, text=True, check=True, env=env).stdout.strip()
        status = subprocess.run(["git", "-C", cwd, "status", "--porcelain"], capture_output=True, text=True,
                                check=True, env=env).stdout.splitlines()
    except Exception:
        return None
    untracked = sum(1 for line in status if line.startswith("??"))
    return branch, len(status) - untracked, untracked
