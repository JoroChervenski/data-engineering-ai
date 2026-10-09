"""Classifies shell commands with policies/command-policy.json.

Each simple command is normalised (wrappers such as sudo and timeout are peeled off, `python -m x` becomes `x`,
`bash -c '...'` and `eval` are looked into) and matched against the rules. The result is a Finding: a decision
(allow, approval_required, deny or None for an unknown command) and a class (read, test, dev, deploy, ...). What a
role may do with each class is decided in engine.py. Standard library only.
"""
import os
import re

import shell_parser

MAX_NORMALIZE_DEPTH = 5
STANDARD_BIN_DIRS = {"/bin", "/usr/bin", "/usr/local/bin", "/sbin", "/usr/sbin", "/opt/homebrew/bin"}
OUTPUT_REDIRECTS = {">", ">>", "&>", "&>>", ">|", ">&"}
STRENGTH = {"allow": 1, "approval_required": 2, "deny": 3}
FLAG_SHORT = re.compile(r"^-[A-Za-z]{2,}$")


class Finding:
    def __init__(self, decision, cls, rule_id, reason, command):
        self.decision, self.cls, self.rule_id, self.reason, self.command = decision, cls, rule_id, reason, command


def as_list(value):
    if value is None:
        return None
    return value if isinstance(value, list) else [value]


class Rule:
    def __init__(self, data):
        self.id, self.cls, self.decision = data["id"], data["class"], data["decision"]
        self.reason = data.get("reason", "")
        self.fallback = bool(data.get("fallback"))
        programs = as_list(data.get("program"))
        self.programs = set(programs) if programs is not None else None
        self.program_regex = re.compile(data["program_regex"], re.I) if "program_regex" in data else None
        self.raw_regex = re.compile(data["raw_regex"], re.I) if "raw_regex" in data else None
        self.positionals = data.get("positionals")
        self.positionals_any = data.get("positionals_any")
        self.positional_any_of = set(data["positional_any_of"]) if "positional_any_of" in data else None
        self.positionals_none = set(data.get("positionals_none", []))
        self.extra_min, self.extra_max = data.get("extra_min"), data.get("extra_max")
        self.flags_any, self.flags_all = set(data.get("flags_any", [])), set(data.get("flags_all", []))
        self.flags_none = set(data.get("flags_none", []))
        self.args_regex = re.compile(data["args_regex"], re.I) if "args_regex" in data else None
        self.args_regex_none = re.compile(data["args_regex_none"], re.I) if "args_regex_none" in data else None
        self.targets_regex = re.compile(data["targets_regex"]) if "targets_regex" in data else None
        if self.programs is None and self.program_regex is None and self.raw_regex is None:
            raise ValueError(f"rule {self.id} has no program, program_regex or raw_regex")
        if self.decision not in STRENGTH:
            raise ValueError(f"rule {self.id} has an unknown decision {self.decision!r}")

    def matches(self, cmd):
        if self.programs is not None and cmd.program not in self.programs:
            return False
        if self.program_regex is not None and not self.program_regex.search(cmd.program):
            return False
        if self.raw_regex is not None and not self.raw_regex.search(cmd.raw):
            return False
        pos, consumed = cmd.positionals, 0
        if self.positionals is not None:
            consumed = find_run(pos, self.positionals)
            if consumed is None:
                return False
        elif self.positionals_any is not None:
            runs = (find_run(pos, words) for words in self.positionals_any)
            consumed = next((c for c in runs if c is not None), None)
            if consumed is None:
                return False
        elif self.positional_any_of is not None:
            index = next((i for i, p in enumerate(pos[:6]) if p in self.positional_any_of), None)
            if index is None:
                return False
            consumed = index + 1
        if self.positionals_none and any(p in self.positionals_none for p in pos[:4]):
            return False
        extra = len(pos) - consumed
        if self.extra_max is not None and extra > self.extra_max:
            return False
        if self.extra_min is not None and extra < self.extra_min:
            return False
        if self.flags_any and not (self.flags_any & cmd.flags):
            return False
        if self.flags_all and not self.flags_all <= cmd.flags:
            return False
        if self.flags_none and (self.flags_none & cmd.flags):
            return False
        if self.args_regex is not None and not self.args_regex.search(cmd.args_text):
            return False
        if self.args_regex_none is not None and self.args_regex_none.search(cmd.args_text):
            return False
        if self.targets_regex is not None and not any(self.targets_regex.search(p) for p in pos):
            return False
        return True


def find_run(positionals, words):
    """Index just past the first place where words appear next to each other among the first positionals."""
    window = positionals[:6]
    for i in range(len(window) - len(words) + 1):
        if window[i:i + len(words)] == words:
            return i + len(words)
    return None


class CommandPolicy:
    def __init__(self, data):
        self.data = data
        self.rules = [Rule(r) for r in data["rules"]]
        self.primary = [r for r in self.rules if not r.fallback]
        self.fallbacks = [r for r in self.rules if r.fallback]
        self.wrappers = data["wrappers"]
        self.value_flags = {k: set(v) for k, v in data.get("value_flags", {}).items()}
        self.combined_short = set(data.get("combined_short_programs", []))
        self.sql_clients = set(data.get("sql_clients", []))
        self.interpreters = set(data.get("interpreters", []))
        self.runner_wrappers = set(data.get("runner_wrappers", []))
        self.privileged_rule = data.get("privileged_rule")
        self.privileged_programs = set(data.get("privileged_programs", []))
        self.pipeline_rules = data.get("pipeline_rules", [])
        self.raw_rules = [dict(r, regex=re.compile(r["regex"], re.I)) for r in data.get("raw_rules", [])]
        self.destructive_fallback = [re.compile(r, re.I) for r in data.get("destructive_fallback_regex", [])]


class Cmd:
    """One normalised command with the pieces the rules look at."""

    def __init__(self, policy, program, args, simple, privileged=False):
        self.program, self.args, self.simple, self.privileged = program, args, simple, privileged
        self.positionals, self.flags = split_args(policy, program, args)
        self.heredoc = simple.heredoc or ""
        here_strings = [target for op, target in simple.redirects if op == "<<<"]
        self.args_text = " ".join(args + here_strings) + ((" " + self.heredoc) if self.heredoc else "")
        self.raw = " ".join([program] + args)

    @property
    def redirects(self):
        return self.simple.redirects


def split_args(policy, program, args):
    value_flags = policy.value_flags.get(program, set())
    expand = program in policy.combined_short
    positionals, flags, i = [], set(), 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            positionals.extend(args[i + 1:])
            break
        if arg.startswith("--"):
            base = arg.split("=", 1)[0]
            flags.add(base)
            if "=" not in arg and base in value_flags:
                i += 1
        elif arg.startswith("-") and len(arg) > 1:
            flags.add(arg)
            if expand and FLAG_SHORT.match(arg):
                flags.update("-" + ch for ch in arg[1:])
            if arg in value_flags:
                i += 1
        else:
            positionals.append(arg)
        i += 1
    return positionals, flags


def program_name(word):
    if "/" in word and os.path.dirname(word) in STANDARD_BIN_DIRS:
        return os.path.basename(word)
    return word


def strip_wrappers(words, policy):
    """Peel off sudo, env, timeout and similar; return (remaining words, privileged)."""
    privileged = False
    while words:
        name = program_name(words[0])
        spec = policy.wrappers.get(name)
        if spec is None:
            break
        privileged = privileged or bool(spec.get("privileged"))
        rest, i = words[1:], 0
        flag_values = spec.get("flag_values", [])
        while i < len(rest):
            word = rest[i]
            if word.startswith("-") and word != "-":
                i += 2 if word in flag_values else 1
            elif spec.get("assignments") and shell_parser.ASSIGNMENT.match(word):
                i += 1
            else:
                break
        i += spec.get("positional_skip", 0)
        words = rest[i:]
        if not words and name == "env":
            return ["env"], privileged
    return words, privileged


def shell_script(args):
    """The script text after -c (also in -lc, -ec, ...), or None."""
    for i, arg in enumerate(args):
        if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:] and i + 1 < len(args):
            return args[i + 1]
    return None


def expand(words, privileged, simple, policy, depth):
    if depth > MAX_NORMALIZE_DEPTH:
        raise shell_parser.ParseError("commands are nested too deeply")
    if not words:
        return [Cmd(policy, ":", [], simple, privileged)]
    program, args = program_name(words[0]), words[1:]
    if re.fullmatch(r"python[\d.]*", program) and len(args) >= 2 and args[0] == "-m":
        program, args = args[1], args[2:]
    if program in policy.runner_wrappers and args and args[0] == "run":
        inner = [a for a in args[1:]]
        while inner and inner[0].startswith("-"):
            inner = inner[1:]
        inner, inner_priv = strip_wrappers(inner, policy)
        return expand(inner, privileged or inner_priv, simple, policy, depth + 1)
    if program in policy.interpreters:
        script = shell_script(args)
        if script is None and simple.heredoc and not [a for a in args if not a.startswith("-")]:
            script = simple.heredoc
        if script is not None:
            return normalize(shell_parser.parse(script, depth + 1), policy, depth + 1, privileged)
    if program == "eval":
        return normalize(shell_parser.parse(" ".join(args), depth + 1), policy, depth + 1, privileged)
    cmd = Cmd(policy, program, args, simple, privileged)
    return [cmd]


def normalize(simples, policy, depth=0, privileged_outer=False):
    commands = []
    for simple in simples:
        words, privileged = strip_wrappers(list(simple.words), policy)
        commands.extend(expand(words, privileged or privileged_outer, simple, policy, depth))
    return commands


def attach_piped_input(commands, policy):
    """What is piped into a SQL client is its input, so it counts as part of that client's arguments."""
    by_pipeline = {}
    for cmd in commands:
        by_pipeline.setdefault(cmd.simple.pipeline, []).append(cmd)
    for members in by_pipeline.values():
        for index, cmd in enumerate(members):
            if cmd.program in policy.sql_clients and index:
                cmd.args_text += " " + " ".join(m.args_text for m in members[:index])


def classify(cmd, policy):
    """The strongest matching rule as a Finding (cls 'unknown' and decision None when nothing matches)."""
    matched = [r for r in policy.primary if r.matches(cmd)] or [r for r in policy.fallbacks if r.matches(cmd)]
    if not matched:
        return Finding(None, "unknown", None, "this command is not in the command policy", cmd.raw)
    best = max(matched, key=lambda r: STRENGTH[r.decision])
    return Finding(best.decision, best.cls, best.id, best.reason, cmd.raw)


def extra_findings(cmd, policy):
    """Findings that come from how a command is run rather than from what it is."""
    findings = []
    spec = policy.privileged_rule
    if spec and (cmd.privileged or cmd.program in policy.privileged_programs):
        findings.append(Finding(spec["decision"], spec["class"], spec["id"], spec["reason"], cmd.raw))
    for op, target in cmd.redirects:
        if op in OUTPUT_REDIRECTS and target != "/dev/null" and not (op == ">&" and re.fullmatch(r"\d+|-", target)):
            findings.append(Finding("allow", "dev", "CMD-V90", "writes a file through a redirection", cmd.raw))
            break
    return findings


def pipeline_findings(commands, policy):
    findings = []
    by_pipeline = {}
    for cmd in commands:
        by_pipeline.setdefault(cmd.simple.pipeline, []).append(cmd)
    for members in by_pipeline.values():
        for rule in policy.pipeline_rules:
            sources = [i for i, c in enumerate(members) if c.program in rule["from_programs"]]
            sinks = [i for i, c in enumerate(members) if c.program in rule["to_programs"]]
            if any(s < k for s in sources for k in sinks):
                findings.append(Finding(rule["decision"], rule["class"], rule["id"], rule["reason"],
                                        " | ".join(c.raw for c in members)))
    return findings


def raw_findings(text, policy):
    return [Finding(r["decision"], r["class"], r["id"], r["reason"], text[:80])
            for r in policy.raw_rules if r["regex"].search(text)]


def phrase_matches(cmd, phrase):
    """Does a project's phrase such as 'git push --force' describe this command? Order matters, gaps are fine."""
    tokens = phrase.split()
    if not tokens or tokens[0] != cmd.program:
        return False
    rest = [cmd.program] + cmd.args
    position = 1
    for token in tokens[1:]:
        try:
            position = rest.index(token, position) + 1
        except ValueError:
            return False
    return True
