"""Rules every Dev Container configuration must satisfy, from the Project Standard's Isolation note.

check_mounts(config, role, project) returns a list of violations (empty means compliant).

role "project":   Knowledge read-only, Projects/<project> read/write, optionally Templates read-only.
role "framework": Knowledge and Templates read-only, nothing else from the vault.
Named volumes are allowed. Any other bind mount is a violation, and so is any attempt to add mounts
through runArgs or workspaceMount.
"""
import re

VAULT = "${localEnv:AI_VAULT}"
FORBIDDEN_HINTS = ("Home.md", "${localEnv:HOME}", "~", "/home/", "/mnt/c/Users", "docker.sock", "..")


def parse_mount(mount):
    if isinstance(mount, dict):
        return {k: str(v) for k, v in mount.items()}
    parsed = {}
    for part in str(mount).split(","):
        key, sep, value = part.partition("=")
        parsed[key.strip()] = value.strip() if sep else "true"
    return parsed


def is_readonly(parsed):
    """Docker's --mount accepts the bare flags `readonly` and `ro`, or readonly=true. Object-form mounts cannot be read-only."""
    return any(parsed.get(key) in ("true", "1") for key in ("readonly", "ro"))


def check_mounts(config, role, project=None):
    problems = []
    allowed = {f"{VAULT}/Knowledge": True}                   # path -> must be read-only
    if role == "framework":
        allowed[f"{VAULT}/Templates"] = True
    elif role == "project":
        allowed[f"{VAULT}/Projects/{project}"] = False
        allowed[f"{VAULT}/Templates"] = True
    else:
        raise ValueError(role)

    seen = set()
    for raw in config.get("mounts", []):
        mount = parse_mount(raw)
        kind = mount.get("type", "volume")
        source = mount.get("source", mount.get("src", ""))
        if kind == "volume":
            if "/" in source or source.startswith(("~", ".")):
                problems.append(f"volume source looks like a path: {source}")
            continue
        if kind != "bind":
            problems.append(f"unsupported mount type {kind!r}: {raw}")
            continue
        for hint in FORBIDDEN_HINTS:
            if hint in source:
                problems.append(f"forbidden mount source ({hint}): {source}")
        if source not in allowed:
            problems.append(f"bind mount not allowed for role {role}: {source}")
            continue
        seen.add(source)
        if allowed[source] and not is_readonly(mount):
            problems.append(f"must be read-only: {source}")
        expected_target = f"/vault/{project}" if source == f"{VAULT}/Projects/{project}" \
            else "/vault/" + source.rsplit("/", 1)[-1]
        if mount.get("target") != expected_target:
            problems.append(f"{source} must be mounted at {expected_target}, not {mount.get('target')}")

    required = [f"{VAULT}/Knowledge"] + ([f"{VAULT}/Projects/{project}"] if role == "project" else [f"{VAULT}/Templates"])
    for source in required:
        if source not in seen:
            problems.append(f"missing required mount: {source}")

    if "workspaceMount" in config:
        problems.append("workspaceMount is not allowed: it can expose a parent folder")
    for arg in (str(a) for a in config.get("runArgs", [])):
        if re.match(r"^(-v|--volume|--mount|--privileged|--pid=host|--net=host|--network=host)(=|$)", arg) \
                or re.match(r"^-v.+", arg):
            problems.append(f"runArgs must not add mounts or privileges: {arg}")
    return problems
