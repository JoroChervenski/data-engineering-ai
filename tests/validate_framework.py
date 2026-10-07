"""Static checks for the framework repository.

Run from anywhere: python3 tests/validate_framework.py

Checks:
- every relative Markdown link resolves (templates/ are excluded: their
  links are meant to resolve inside a client repository);
- agents, skills and commands carry the frontmatter Claude Code needs;
- no secret-like strings or GUIDs;
- no client terms, read from the untracked file `.client-terms` (one term
  per line, `#` comments allowed) so the list itself never enters Git.

Exits non-zero if any check fails.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^(```|~~~)")
SECRET_PATTERNS = {
    "GUID": re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I
    ),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "connection secret": re.compile(
        r"(AccountKey|SharedAccessKey|Password|pwd)\s*=\s*[^;\s<>{}]{6,}", re.I
    ),
}


def tracked_files() -> list[Path]:
    """Tracked plus new, not-ignored files: what a commit would contain."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields


def check_links(path: Path, text: str) -> list[str]:
    errors = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(line):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_part = target.split("#", 1)[0]
            if not (path.parent / file_part).exists():
                errors.append(f"{rel(path)}:{number}: broken link -> {target}")
    return errors


def check_frontmatter(path: Path, text: str) -> list[str]:
    parts = path.relative_to(ROOT).parts
    fields = frontmatter(text)
    required: tuple[str, ...] = ()
    if parts[0] == "agents" and path.name.endswith(".agent.md"):
        required = ("name", "description")
    elif parts[0] == "skills" and path.name == "SKILL.md":
        required = ("name", "description")
        if fields.get("name") and fields["name"] != parts[1]:
            return [f"{rel(path)}: skill name '{fields['name']}' != folder '{parts[1]}'"]
    elif parts[0] == "commands" and path.suffix == ".md":
        required = ("description",)
    return [f"{rel(path)}: missing frontmatter '{key}'" for key in required if not fields.get(key)]


def load_client_terms() -> list[str]:
    terms_file = ROOT / ".client-terms"
    if not terms_file.exists():
        return []
    terms = []
    for line in terms_file.read_text(encoding="utf-8").splitlines():
        term = line.split("#", 1)[0].strip()
        if term:
            terms.append(term)
    return terms


def check_content(path: Path, text: str, client_terms: list[str]) -> list[str]:
    errors = []
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                errors.append(f"{rel(path)}:{number}: possible {label}")
        lowered = line.lower()
        for term in client_terms:
            if re.search(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])", lowered):
                errors.append(f"{rel(path)}:{number}: client term '{term}'")
    return errors


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    client_terms = load_client_terms()
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        if path.name == ".client-terms" or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            if path.relative_to(ROOT).parts[0] != "templates":
                errors += check_links(path, text)
            errors += check_frontmatter(path, text)
        if path != Path(__file__).resolve():
            errors += check_content(path, text, client_terms)

    for error in errors:
        print(error)
    note = "" if client_terms else " (no .client-terms file: client-term check skipped)"
    print(f"{len(files)} files checked, {len(errors)} problem(s){note}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
