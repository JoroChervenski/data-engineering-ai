"""Shared helpers for the policy and hook tests."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

import engine  # noqa: E402

HOME = "/home/user"
MANIFEST = """project:
  name: "Demo"

framework:
  version: "0.1.0"

standard:
  version: "0.1.0"
  commit: "abc1234"

environments:
  - name: dev
    write_access: true
  - name: prod
    write_access: false
"""


def make_project(tmp, manifest=MANIFEST, guardrails=None):
    """A project folder with an .ai/manifest.yaml and, optionally, .ai/guardrails.json (dict or raw text)."""
    root = pathlib.Path(tmp)
    (root / ".ai").mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        (root / ".ai" / "manifest.yaml").write_text(manifest, encoding="utf-8")
    if guardrails is not None:
        text = guardrails if isinstance(guardrails, str) else json.dumps(guardrails)
        (root / ".ai" / "guardrails.json").write_text(text, encoding="utf-8")
    return root


def event(tool, cwd, agent=None, **tool_input):
    ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd),
          "session_id": "s1"}
    if agent:
        ev["agent_type"] = agent
    return ev


def verdict(ev, environment=None, **extra_env):
    env = {"HOME": HOME}
    if environment:
        env["AI_ENVIRONMENT"] = environment
    env.update(extra_env)
    return engine.evaluate(ev, environ=env)


def level(command, cwd, agent=None, environment=None):
    """none, ask or deny for a shell command."""
    return verdict(event("Bash", cwd, agent, command=command), environment).decision or "none"


def file_level(tool, cwd, agent=None, environment=None, **tool_input):
    return verdict(event(tool, cwd, agent, **tool_input), environment).decision or "none"
