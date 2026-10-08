#!/usr/bin/env python3
"""Mirror a repo's .ai/ overlay into its Obsidian project folder, following the Project Standard.

The layout, names, topics and note templates come from the standard in the vault's Knowledge folder
(Project Standard/standard.json). Nothing about them is hard-coded here. If the standard is missing or
invalid the run stops before writing anything.

    python3 vault_sync.py [--repo-root DIR] [--vault-dir DIR] [--knowledge-dir DIR]
                          [--dry-run] [--refresh-conventions]

Reads <repo-root>/.ai/vault-sync.json (project, repo, vault_dir). Writes only inside the project's own
vault folder, and never deletes. Standard library only.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

DEFAULT_KNOWLEDGE_DIR = "/vault/Knowledge"
STANDARD_DIR = "Project Standard"
STANDARD_FILE = "standard.json"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
TOKEN = re.compile(r"\{\{(\w+)\}\}")


class SyncError(Exception):
    """A problem that stops the run before anything is written."""


# --- standard ---------------------------------------------------------------------------------

REQUIRED = [
    ("standard", str), ("version", str),
    ("vault.folders", list), ("vault.hub.file", str), ("vault.hub.template", str),
    ("vault.hub.sync_block.start", str), ("vault.hub.sync_block.end", str),
    ("vault.conventions.file", str), ("vault.conventions.template", str),
    ("vault.names.repo_note", str), ("vault.names.mirror_note", str),
    ("vault.names.project_pattern", str), ("vault.names.repo_pattern", str),
    ("vault.names.reserved_project_names", list),
    ("vault.frontmatter.required", list), ("vault.frontmatter.repo_note", list),
    ("vault.frontmatter.mirror", list), ("vault.frontmatter.repo_file_mirror", list),
    ("vault.frontmatter.ticket_mirror", list), ("vault.frontmatter.hub_and_conventions", list),
    ("mirrors.repo_overlay.source_dir", str), ("mirrors.repo_overlay.target", str),
    ("mirrors.repo_overlay.topics", dict),
    ("mirrors.tickets.source_dir", str), ("mirrors.tickets.target", str),
    ("mirrors.adr.source_dir", str), ("mirrors.adr.target", str),
    ("mirrors.runbooks.source_dir", str), ("mirrors.runbooks.target", str),
    ("repo.sync_config.file", str),
]


def dig(obj, dotted):
    for key in dotted.split("."):
        if not isinstance(obj, dict) or key not in obj:
            raise KeyError(dotted)
        obj = obj[key]
    return obj


def safe_relative(value, label):
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or not value:
        raise SyncError(f"standard.json: {label} must be a relative path without '..': {value!r}")


def load_standard(knowledge_dir):
    path = knowledge_dir / STANDARD_DIR / STANDARD_FILE
    try:
        std = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SyncError(f"standard not found: {path} (is Knowledge mounted?)")
    except (OSError, ValueError) as exc:
        raise SyncError(f"standard unreadable: {path}: {exc}")
    for dotted, kind in REQUIRED:
        try:
            value = dig(std, dotted)
        except KeyError:
            raise SyncError(f"standard.json: missing '{dotted}'")
        if not isinstance(value, kind):
            raise SyncError(f"standard.json: '{dotted}' must be {kind.__name__}")
    if std["standard"] != "project-standard":
        raise SyncError(f"standard.json: unexpected standard {std['standard']!r}")
    for folder in std["vault"]["folders"]:
        if not isinstance(folder, dict) or not isinstance(folder.get("name"), str):
            raise SyncError("standard.json: every folder needs a 'name'")
        safe_relative(folder["name"], "folder name")
    for key, spec in std["mirrors"].items():
        safe_relative(spec["target"], f"mirrors.{key}.target")
        safe_relative(spec["source_dir"], f"mirrors.{key}.source_dir")
    safe_relative(std["vault"]["hub"]["template"], "hub template")
    safe_relative(std["vault"]["conventions"]["template"], "conventions template")
    return std


def check_names(std, project, repo):
    names = std["vault"]["names"]
    if not re.fullmatch(names["project_pattern"], project):
        raise SyncError(f"project name {project!r} does not match {names['project_pattern']}")
    if project in names["reserved_project_names"]:
        raise SyncError(f"project name {project!r} is reserved")
    if not re.fullmatch(names["repo_pattern"], repo):
        raise SyncError(f"repo name {repo!r} does not match {names['repo_pattern']}")


def load_config(repo_root, std):
    path = repo_root / std["repo"]["sync_config"]["file"]
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncError(f"cannot read {path}: {exc}")
    for key in std["repo"]["sync_config"].get("keys", ["project", "repo", "vault_dir"]):
        if not isinstance(cfg.get(key), str) or not cfg[key]:
            raise SyncError(f"{path}: '{key}' must be a non-empty string")
    return cfg


# --- text helpers -----------------------------------------------------------------------------

def fill(template, **values):
    def repl(match):
        if match.group(1) not in values:
            raise SyncError(f"unknown placeholder {{{match.group(1)}}} in {template!r}")
        return values[match.group(1)]
    return PLACEHOLDER.sub(repl, template)


def render(text, values, where):
    def repl(match):
        if match.group(1) not in values:
            raise SyncError(f"{where}: unknown template token {{{{{match.group(1)}}}}}")
        return values[match.group(1)]
    return TOKEN.sub(repl, text)


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            meta[key.strip()] = re.sub(r"\s+#.*$", "", value).strip()
    return meta, text[end + 5:]


def dump_frontmatter(meta):
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            value = "[" + ", ".join(value) + "]"
        lines.append(f"{key}: {value}".rstrip())
    lines.append("---")
    return "\n".join(lines) + "\n"


def strip_comments(text):
    return re.sub(r"<!--.*?-->\n*", "", text, flags=re.S)


def check_meta(meta, keys, where):
    missing = [k for k in keys if k not in meta]
    if missing:
        raise SyncError(f"{where}: frontmatter lacks {missing}; the standard requires them")


def git_stamp(path, dirty_check=False):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        head = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=True, env=env).stdout.strip()
    except Exception:
        return "unknown"
    if not head:
        return "unknown"
    if dirty_check:
        try:
            out = subprocess.run(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"],
                                 capture_output=True, text=True, check=True, env=env).stdout.strip()
        except Exception:
            out = ""
        if out:
            head += "+dirty"
    return head


# --- staged writes ----------------------------------------------------------------------------

class Vault:
    """Collects every write in memory; flush() applies them. Nothing leaves the project folder."""

    def __init__(self, root, dry_run):
        self.root = root.resolve()
        self.dry_run = dry_run
        self.pending = {}
        self.folders = set()

    def _inside(self, path):
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise SyncError(f"refusing to touch a path outside the project folder: {path}")
        return resolved

    def ensure_folder(self, path):
        self.folders.add(self._inside(path))

    def exists(self, path):
        resolved = self._inside(path)
        return resolved in self.pending or resolved.exists()

    def read(self, path):
        resolved = self._inside(path)
        if resolved in self.pending:
            return self.pending[resolved]
        return resolved.read_text(encoding="utf-8")

    def write(self, path, content):
        self.pending[self._inside(path)] = content

    def list_md(self, directory):
        d = self._inside(directory)
        found = {p for p in d.glob("*.md")} if d.is_dir() else set()
        found |= {p for p in self.pending if p.parent == d and p.suffix == ".md"}
        return sorted(found, key=lambda p: p.name)

    def subdirs(self, directory):
        d = self._inside(directory)
        found = {p for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()
        found |= {p.parent for p in self.pending if p.parent.parent == d}
        return sorted(found, key=lambda p: p.name)

    def counts(self):
        out = {"created": 0, "updated": 0, "unchanged": 0}
        for path, content in self.pending.items():
            if not path.exists():
                out["created"] += 1
            elif path.read_text(encoding="utf-8") == content:
                out["unchanged"] += 1
            else:
                out["updated"] += 1
        return out

    def flush(self):
        for folder in sorted(self.folders):
            folder.mkdir(parents=True, exist_ok=True)
        for path, content in self.pending.items():
            if path.exists() and path.read_text(encoding="utf-8") == content:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


# --- mirrors ----------------------------------------------------------------------------------

class Context:
    def __init__(self, std, project, repo, repo_root, knowledge_dir, vault_dir, today, repo_commit):
        self.std, self.project, self.repo = std, project, repo
        self.repo_root, self.knowledge_dir, self.vault_dir = repo_root, knowledge_dir, vault_dir
        self.today, self.repo_commit = today, repo_commit
        self.ptag = project.lower()

    def target_dir(self, mirror):
        return self.vault_dir / fill(self.std["mirrors"][mirror]["target"], repo=self.repo)


def rewrite_links(body, name_map):
    for source_name, stem in name_map.items():
        body = re.sub(r"\[[^\]]*\]\((?:\./)?" + re.escape(source_name) + r"\)", f"[[{stem}]]", body)
    return body


def sources(directory):
    """Markdown files directly inside directory; symlinks are skipped."""
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.glob("*.md")) if not p.is_symlink() and p.is_file()]


def read_source(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SyncError(f"cannot read {path}: {exc}")


def mirror_group(ctx, vault, key, pairs):
    """pairs: list of (source Path, note stem). Writes the mirrors and returns the produced paths."""
    spec = ctx.std["mirrors"][key]
    fm = ctx.std["vault"]["frontmatter"]
    note_type = spec.get("type", "overview")
    target_dir = ctx.target_dir(key)
    name_map = {src.name: stem for src, stem in pairs}
    produced = set()
    for src, stem in pairs:
        text = read_source(src)
        source_rel = f"{ctx.repo}/{spec['source_dir']}/{src.name}"
        if key == "tickets":
            tmeta, body = split_frontmatter(strip_comments(text))
            body = rewrite_links(body.lstrip("\n"), name_map)
            meta = {"project": ctx.project, "repo": ctx.repo, "type": note_type,
                    "ticket": tmeta.get("ticket", src.stem), "status": tmeta.get("status", "open"),
                    "branch": tmeta.get("branch", ""), "pr": tmeta.get("pr", ""),
                    "created": tmeta.get("created", ""), "authority": "mirror", "source": source_rel,
                    "captured": ctx.today, "tags": [ctx.ptag, ctx.repo, note_type, "mirror"]}
            keys = fm["required"] + fm["repo_note"] + fm["mirror"] + fm["ticket_mirror"]
            banner = (f"> [!info] Mirror of `{source_rel}`. The ticket note in the repo overlay is the source "
                      f"of truth; re-run the sync after changing it.\n> Back to [[{ctx.project}]]\n\n")
        else:
            body = rewrite_links(strip_comments(text), name_map)
            meta = {"project": ctx.project, "repo": ctx.repo, "type": note_type, "status": "active",
                    "authority": "mirror", "source": source_rel, "source_commit": ctx.repo_commit,
                    "captured": ctx.today, "tags": [ctx.ptag, ctx.repo, note_type, "mirror"]}
            keys = fm["required"] + fm["repo_note"] + fm["mirror"] + fm["repo_file_mirror"]
            legend = (" Tags: **[O]** Observed · **[I]** Inferred · **[U]** Unknown." if key == "repo_overlay"
                      else "")
            banner = (f"> [!info] Mirror of `{source_rel}` (client commit `{ctx.repo_commit}`). Edit the repo "
                      f"file and re-run the sync; changes made here are overwritten.{legend}\n"
                      f"> Back to [[{ctx.project}]]\n\n")
        check_meta(meta, keys, f"{key} mirror of {src.name}")
        target = target_dir / f"{stem}.md"
        produced.add(target.resolve())
        vault.write(target, dump_frontmatter(meta) + "\n" + banner + body)
    return produced


def plan_mirrors(ctx, vault):
    std = ctx.std
    names = std["vault"]["names"]
    produced = set()

    topics = std["mirrors"]["repo_overlay"]["topics"]
    overlay_dir = ctx.repo_root / std["mirrors"]["repo_overlay"]["source_dir"]
    overlay_pairs = [(overlay_dir / fname, fill(names["repo_note"], project=ctx.project, repo=ctx.repo, topic=topic))
                     for fname, topic in topics.items()
                     if (overlay_dir / fname).is_file() and not (overlay_dir / fname).is_symlink()]
    produced |= mirror_group(ctx, vault, "repo_overlay", overlay_pairs)

    ticket_dir = ctx.repo_root / std["mirrors"]["tickets"]["source_dir"]
    produced |= mirror_group(ctx, vault, "tickets", [(p, p.stem) for p in sources(ticket_dir)])

    for key in ("adr", "runbooks"):
        src_dir = ctx.repo_root / std["mirrors"][key]["source_dir"]
        pairs = [(p, fill(names["mirror_note"], project=ctx.project, repo=ctx.repo, stem=p.stem))
                 for p in sources(src_dir)]
        produced |= mirror_group(ctx, vault, key, pairs)
    return produced


def find_orphans(ctx, vault, produced):
    orphans = []
    for key in ("repo_overlay", "tickets", "adr", "runbooks"):
        for path in vault.list_md(ctx.target_dir(key)):
            if path.resolve() in produced:
                continue
            meta, _ = split_frontmatter(vault.read(path))
            if meta.get("authority") == "mirror" and meta.get("repo", ctx.repo) == ctx.repo:
                orphans.append(path)
    return orphans


# --- hub --------------------------------------------------------------------------------------

def hub_block(ctx, vault):
    vd, std = ctx.vault_dir, ctx.std
    start = std["vault"]["hub"]["sync_block"]["start"]
    end = std["vault"]["hub"]["sync_block"]["end"]
    topic_order = list(std["mirrors"]["repo_overlay"]["topics"].values())

    def topic_of(path):
        return path.stem.split(" - ")[-1]

    def container(key):
        return vd / std["mirrors"][key]["target"].replace("/{repo}", "")

    overview = next((f["name"] for f in std["vault"]["folders"] if f.get("role") == "overview"), None)
    lines = [start, "## Overview notes (auto)"]
    lines += [f"- [[{p.stem}]]" for p in vault.list_md(vd / overview)] if overview else []
    if lines[-1] == "## Overview notes (auto)":
        lines.append("- none yet")

    lines += ["", "## Repositories (auto)"]
    repo_dirs = vault.subdirs(container("repo_overlay"))
    for rd in repo_dirs:
        notes = sorted(vault.list_md(rd), key=lambda p: topic_order.index(topic_of(p))
                       if topic_of(p) in topic_order else len(topic_order))
        lines.append(f"- **{rd.name}**: " + " · ".join(f"[[{p.stem}|{topic_of(p)}]]" for p in notes))
    if not repo_dirs:
        lines.append("- none yet")

    lines += ["", "## Tickets (auto)", "| Ticket | Status | Title |", "|---|---|---|"]
    rows = []
    for p in vault.list_md(container("tickets")):
        meta, body = split_frontmatter(vault.read(p))
        title = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), p.stem)
        rows.append(f"| [[{p.stem}]] | {meta.get('status', '')} | {title.replace('|', '/')} |")
    lines += rows or ["| none yet | | |"]

    for heading, key in (("Decisions (auto)", "adr"), ("Runbooks (auto)", "runbooks")):
        lines += ["", f"## {heading}"]
        found = False
        for rd in vault.subdirs(container(key)):
            notes = vault.list_md(rd)
            if not notes:
                continue
            found = True
            prefix = f"{ctx.project} - {rd.name} - "
            lines.append(f"- **{rd.name}**: " + " · ".join(
                f"[[{p.stem}|{p.stem[len(prefix):] if p.stem.startswith(prefix) else p.stem}]]" for p in notes))
        if not found:
            lines.append("- none yet")
    lines.append(end)
    return "\n".join(lines), start, end


def plan_hub(ctx, vault, template_values):
    std = ctx.std
    hub_path = ctx.vault_dir / fill(std["vault"]["hub"]["file"], project=ctx.project)
    block, start, end = hub_block(ctx, vault)
    if vault.exists(hub_path):
        text = vault.read(hub_path)
    else:
        text = render(read_template(ctx, std["vault"]["hub"]["template"]), template_values, "hub template")
        check_meta(split_frontmatter(text)[0], std["vault"]["frontmatter"]["required"]
                   + std["vault"]["frontmatter"]["hub_and_conventions"], "hub template")
    if start in text and end in text:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: block, text, flags=re.S)
    elif "\n## Log" in text:
        text = text.replace("\n## Log", "\n" + block + "\n\n## Log", 1)
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    vault.write(hub_path, text)


def read_template(ctx, relative):
    path = ctx.knowledge_dir / STANDARD_DIR / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SyncError(f"cannot read template {path}: {exc}")


# --- run --------------------------------------------------------------------------------------

class Result:
    def __init__(self, counts, orphans, standard_version, standard_commit):
        self.counts, self.orphans = counts, orphans
        self.standard_version, self.standard_commit = standard_version, standard_commit


def sync(repo_root, knowledge_dir, vault_dir=None, dry_run=False, refresh_conventions=False, today=None):
    repo_root, knowledge_dir = pathlib.Path(repo_root).resolve(), pathlib.Path(knowledge_dir)
    std = load_standard(knowledge_dir)
    cfg = load_config(repo_root, std)
    project, repo = cfg["project"], cfg["repo"]
    check_names(std, project, repo)
    vault_dir = pathlib.Path(vault_dir or cfg["vault_dir"])
    if not vault_dir.is_dir():
        raise SyncError(f"vault folder not found: {vault_dir} (is it mounted?)")
    if vault_dir.name != project:
        raise SyncError(f"vault folder {vault_dir} is not the folder of project {project!r}")

    today = today or datetime.date.today().isoformat()
    ctx = Context(std, project, repo, repo_root, knowledge_dir, vault_dir.resolve(), today, git_stamp(repo_root))
    standard_commit = git_stamp(knowledge_dir, dirty_check=True)
    values = {"project": project, "ptag": ctx.ptag, "date": today, "standard_version": std["version"],
              "standard_commit": standard_commit,
              "sync_start": std["vault"]["hub"]["sync_block"]["start"],
              "sync_end": std["vault"]["hub"]["sync_block"]["end"]}

    vault = Vault(ctx.vault_dir, dry_run)
    for folder in std["vault"]["folders"]:
        vault.ensure_folder(ctx.vault_dir / folder["name"])

    conv_path = ctx.vault_dir / std["vault"]["conventions"]["file"]
    if refresh_conventions or not vault.exists(conv_path):
        text = render(read_template(ctx, std["vault"]["conventions"]["template"]), values, "conventions template")
        check_meta(split_frontmatter(text)[0], std["vault"]["frontmatter"]["required"]
                   + std["vault"]["frontmatter"]["hub_and_conventions"], "conventions template")
        vault.write(conv_path, text)

    produced = plan_mirrors(ctx, vault)
    orphans = find_orphans(ctx, vault, produced)
    plan_hub(ctx, vault, values)

    counts = vault.counts()
    if not dry_run:
        vault.flush()
    return Result(counts, orphans, std["version"], standard_commit)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--vault-dir", help="override vault_dir from vault-sync.json (for runs on the host)")
    parser.add_argument("--knowledge-dir", default=os.environ.get("VAULT_KNOWLEDGE_DIR", DEFAULT_KNOWLEDGE_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-conventions", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = sync(args.repo_root, args.knowledge_dir, args.vault_dir, args.dry_run, args.refresh_conventions)
    except SyncError as exc:
        print(f"vault_sync: {exc}", file=sys.stderr)
        return 2
    c = result.counts
    print(f"{'[dry run] ' if args.dry_run else ''}standard {result.standard_version} "
          f"({result.standard_commit}): {c['created']} created, {c['updated']} updated, {c['unchanged']} unchanged")
    for path in result.orphans:
        print(f"  orphaned mirror (not deleted): {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
