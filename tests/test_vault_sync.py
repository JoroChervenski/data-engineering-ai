"""Tests for scripts/vault_sync.py.

Run: python3 -m unittest discover -s tests

Set KNOWLEDGE_DIR to the vault's Knowledge folder to also check that the pinned standard snapshot in
tests/fixtures/standard still matches the real standard.
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import vault_sync  # noqa: E402

SNAPSHOT = ROOT / "tests" / "fixtures" / "standard"
TODAY = "2026-01-02"
PROJECT, REPO = "Demo", "demo-repo"
STANDARD_VERSION = json.loads((SNAPSHOT / "Project Standard" / "standard.json").read_text())["version"]


def tree(root):
    return {str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None)
            for p in sorted(pathlib.Path(root).rglob("*"))}


class Env:
    """A temporary Knowledge folder, vault project folder and repo."""

    def __init__(self, tmp):
        self.tmp = pathlib.Path(tmp)
        self.knowledge = self.tmp / "Knowledge"
        shutil.copytree(SNAPSHOT / "Project Standard", self.knowledge / "Project Standard")
        self.vault = self.tmp / "vault"
        self.project_dir = self.vault / "Projects" / PROJECT
        self.project_dir.mkdir(parents=True)
        self.repo = self.tmp / REPO
        self.write_repo(".ai/vault-sync.json", json.dumps(
            {"project": PROJECT, "repo": REPO, "vault_dir": str(self.project_dir)}))

    def write_repo(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def populate(self):
        self.write_repo(".ai/PROJECT.md", "# Project\n<!-- comment -->\nSee [architecture](ARCHITECTURE.md).\n")
        self.write_repo(".ai/ARCHITECTURE.md", "# Architecture\nUnknown.\n")
        self.write_repo(".ai/tickets/T-1.md", "---\nticket: T-1\nstatus: open\nbranch: b\n---\n# First ticket\nBody\n")
        self.write_repo(".ai/adr/ADR-0001-x.md", "# ADR-0001: x\nSee [two](ADR-0002-y.md).\n")
        self.write_repo(".ai/adr/ADR-0002-y.md", "# ADR-0002: y\n")
        self.write_repo(".ai/runbooks/rerun-load.md", "# Rerun the load\n1. Do it.\n")

    def sync(self, **kw):
        return vault_sync.sync(self.repo, self.knowledge, today=TODAY, **kw)

    def note(self, rel):
        return (self.project_dir / rel).read_text(encoding="utf-8")


class VaultSyncTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.env = Env(self._tmp.name)

    # --- what gets written -------------------------------------------------------------------

    def test_first_run_builds_the_standard_layout(self):
        self.env.populate()
        result = self.env.sync()
        std = json.loads((SNAPSHOT / "Project Standard" / "standard.json").read_text())
        for folder in std["vault"]["folders"]:
            self.assertTrue((self.env.project_dir / folder["name"]).is_dir(), folder["name"])
        self.assertTrue((self.env.project_dir / "_Conventions.md").is_file())
        self.assertTrue((self.env.project_dir / f"{PROJECT}.md").is_file())
        # conventions, hub, two overview mirrors, one ticket, two ADRs, one runbook
        self.assertEqual((result.counts["created"], result.counts["updated"]), (8, 0))

    def test_mirror_names_folders_and_frontmatter(self):
        self.env.populate()
        self.env.sync()
        base = f"{PROJECT} - {REPO} - "
        expected = {
            f"02 Repos/{REPO}/{base}Project.md": "overview",
            f"02 Repos/{REPO}/{base}Architecture.md": "overview",
            "03 Tickets/T-1.md": "ticket",
            f"04 Decisions/{REPO}/{base}ADR-0001-x.md": "decision",
            f"04 Decisions/{REPO}/{base}ADR-0002-y.md": "decision",
            f"05 Runbooks/{REPO}/{base}rerun-load.md": "runbook",
        }
        for rel, kind in expected.items():
            text = self.env.note(rel)
            meta, _ = vault_sync.split_frontmatter(text)
            self.assertEqual(meta["type"], kind, rel)
            self.assertEqual(meta["authority"], "mirror", rel)
            self.assertEqual(meta["project"], PROJECT, rel)
            self.assertEqual(meta["captured"], TODAY, rel)
            self.assertIn("mirror", meta["tags"], rel)
        self.assertEqual(vault_sync.split_frontmatter(self.env.note("03 Tickets/T-1.md"))[0]["status"], "open")

    def test_links_become_wiki_links_and_comments_are_removed(self):
        self.env.populate()
        self.env.sync()
        project_note = self.env.note(f"02 Repos/{REPO}/{PROJECT} - {REPO} - Project.md")
        self.assertIn(f"[[{PROJECT} - {REPO} - Architecture]]", project_note)
        self.assertNotIn("comment", project_note)
        adr = self.env.note(f"04 Decisions/{REPO}/{PROJECT} - {REPO} - ADR-0001-x.md")
        self.assertIn(f"[[{PROJECT} - {REPO} - ADR-0002-y]]", adr)

    def test_hub_and_conventions_carry_the_standard_version(self):
        self.env.sync()
        for rel in (f"{PROJECT}.md", "_Conventions.md"):
            meta, _ = vault_sync.split_frontmatter(self.env.note(rel))
            self.assertEqual(meta["standard_version"], STANDARD_VERSION, rel)
            self.assertIn("standard_commit", meta, rel)
        self.assertIn(f"[[Projects/{PROJECT}/_Conventions|_Conventions]]", self.env.note(f"{PROJECT}.md"))

    def test_hub_block_lists_tickets_decisions_and_runbooks(self):
        self.env.populate()
        self.env.sync()
        hub = self.env.note(f"{PROJECT}.md")
        self.assertIn("| [[T-1]] | open | First ticket |", hub)
        self.assertIn(f"[[{PROJECT} - {REPO} - ADR-0001-x|ADR-0001-x]]", hub)
        self.assertIn(f"[[{PROJECT} - {REPO} - rerun-load|rerun-load]]", hub)
        self.assertIn(f"[[{PROJECT} - {REPO} - Project|Project]]", hub)

    # --- repeatability and dry run -----------------------------------------------------------

    def test_second_run_changes_nothing(self):
        self.env.populate()
        self.env.sync()
        before = tree(self.env.project_dir)
        result = self.env.sync()
        self.assertEqual((result.counts["created"], result.counts["updated"]), (0, 0))
        self.assertEqual(tree(self.env.project_dir), before)

    def test_dry_run_writes_nothing_but_reports(self):
        self.env.populate()
        before = tree(self.env.tmp)
        result = self.env.sync(dry_run=True)
        self.assertEqual(tree(self.env.tmp), before)
        self.assertEqual(result.counts["created"], 8)

    def test_dry_run_matches_the_real_run(self):
        self.env.populate()
        planned = self.env.sync(dry_run=True).counts
        actual = self.env.sync().counts
        self.assertEqual(planned, actual)

    # --- what is never touched ---------------------------------------------------------------

    def test_hand_written_notes_and_top_levels_are_left_alone(self):
        self.env.populate()
        own = {"01 Overview/Demo - Open Questions.md": "mine 1", "04 Decisions/Demo - Choice.md": "mine 2",
               "05 Runbooks/Demo - Deploy.md": "mine 3", "06 Analysis/x.md": "mine 4"}
        for rel, text in own.items():
            path = self.env.project_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.env.sync()
        for rel, text in own.items():
            self.assertEqual(self.env.note(rel), text, rel)
        top_level = [p.name for p in (self.env.project_dir / "04 Decisions").glob("*.md")]
        self.assertEqual(top_level, ["Demo - Choice.md"])

    def test_hub_text_outside_the_block_survives(self):
        self.env.sync()
        hub_path = self.env.project_dir / f"{PROJECT}.md"
        hub_path.write_text(hub_path.read_text().replace("<One paragraph: the client and the engagement. Hand-written.>",
                                                         "My own summary."), encoding="utf-8")
        self.env.populate()
        self.env.sync()
        hub = self.env.note(f"{PROJECT}.md")
        self.assertIn("My own summary.", hub)
        self.assertIn("| [[T-1]] |", hub)

    def test_conventions_are_not_overwritten_unless_asked(self):
        self.env.sync()
        conv = self.env.project_dir / "_Conventions.md"
        conv.write_text("edited", encoding="utf-8")
        self.env.sync()
        self.assertEqual(conv.read_text(), "edited")
        self.env.sync(refresh_conventions=True)
        self.assertNotEqual(conv.read_text(), "edited")

    def test_edits_to_a_mirror_are_overwritten(self):
        self.env.populate()
        self.env.sync()
        rel = f"04 Decisions/{REPO}/{PROJECT} - {REPO} - ADR-0002-y.md"
        original = self.env.note(rel)
        (self.env.project_dir / rel).write_text("tampered", encoding="utf-8")
        self.env.sync()
        self.assertEqual(self.env.note(rel), original)

    def test_orphans_are_reported_and_never_deleted(self):
        self.env.populate()
        self.env.sync()
        (self.env.repo / ".ai/adr/ADR-0002-y.md").unlink()
        (self.env.repo / ".ai/runbooks/rerun-load.md").unlink()
        result = self.env.sync()
        names = sorted(p.name for p in result.orphans)
        self.assertEqual(names, [f"{PROJECT} - {REPO} - ADR-0002-y.md", f"{PROJECT} - {REPO} - rerun-load.md"])
        for p in result.orphans:
            self.assertTrue(p.exists())

    def test_another_projects_folder_is_never_touched(self):
        other = self.env.vault / "Projects" / "Other"
        other.mkdir()
        (other / "Other.md").write_text("not yours", encoding="utf-8")
        before = tree(other)
        self.env.populate()
        self.env.sync()
        self.assertEqual(tree(other), before)

    def test_two_repos_in_one_project_do_not_clash(self):
        self.env.populate()
        self.env.sync()
        second = Env(self._tmp.name + "/second")
        second.project_dir = self.env.project_dir
        second.knowledge = self.env.knowledge
        second.write_repo(".ai/vault-sync.json", json.dumps(
            {"project": PROJECT, "repo": "other-repo", "vault_dir": str(self.env.project_dir)}))
        second.write_repo(".ai/adr/ADR-0001-x.md", "# ADR-0001: x\n")
        result = second.sync()
        self.assertEqual(result.orphans, [])
        self.assertTrue((self.env.project_dir / "04 Decisions" / "other-repo").is_dir())
        self.assertTrue((self.env.project_dir / "04 Decisions" / REPO / f"{PROJECT} - {REPO} - ADR-0001-x.md").exists())

    # --- fails closed ------------------------------------------------------------------------

    def assert_fails_without_writing(self, message_part):
        before = tree(self.env.tmp)
        with self.assertRaises(vault_sync.SyncError) as ctx:
            self.env.sync()
        self.assertIn(message_part, str(ctx.exception))
        self.assertEqual(tree(self.env.tmp), before)

    def test_missing_standard_stops_the_run(self):
        shutil.rmtree(self.env.knowledge / "Project Standard")
        self.assert_fails_without_writing("standard not found")

    def test_invalid_standard_stops_the_run(self):
        (self.env.knowledge / "Project Standard" / "standard.json").write_text("{not json", encoding="utf-8")
        self.assert_fails_without_writing("unreadable")

    def test_standard_missing_a_key_stops_the_run(self):
        path = self.env.knowledge / "Project Standard" / "standard.json"
        std = json.loads(path.read_text())
        del std["mirrors"]["adr"]
        path.write_text(json.dumps(std), encoding="utf-8")
        self.assert_fails_without_writing("mirrors.adr")

    def test_standard_with_an_escaping_target_stops_the_run(self):
        path = self.env.knowledge / "Project Standard" / "standard.json"
        std = json.loads(path.read_text())
        std["mirrors"]["adr"]["target"] = "../../elsewhere/{repo}"
        path.write_text(json.dumps(std), encoding="utf-8")
        self.assert_fails_without_writing("relative path")

    def test_template_that_breaks_the_standard_stops_the_run(self):
        hub = self.env.knowledge / "Project Standard" / "_templates" / "Project Hub.md"
        hub.write_text(hub.read_text().replace("authority: working\n", ""), encoding="utf-8")
        self.assert_fails_without_writing("authority")

    def test_template_with_an_unknown_token_stops_the_run(self):
        conv = self.env.knowledge / "Project Standard" / "_templates" / "Project Conventions.md"
        conv.write_text(conv.read_text() + "\n{{surprise}}\n", encoding="utf-8")
        self.assert_fails_without_writing("surprise")

    def test_missing_vault_folder_stops_the_run(self):
        shutil.rmtree(self.env.project_dir)
        with self.assertRaises(vault_sync.SyncError) as ctx:
            self.env.sync()
        self.assertIn("not found", str(ctx.exception))

    def test_vault_folder_of_another_project_is_refused(self):
        other = self.env.vault / "Projects" / "Other"
        other.mkdir()
        with self.assertRaises(vault_sync.SyncError) as ctx:
            self.env.sync(vault_dir=other)
        self.assertIn("not the folder of project", str(ctx.exception))
        self.assertEqual(list(other.iterdir()), [])

    def test_bad_and_reserved_names_are_refused(self):
        for project in ("my project", "Knowledge", "Templates", "Home", "a - b", "-x"):
            cfg = {"project": project, "repo": REPO, "vault_dir": str(self.env.project_dir)}
            self.env.write_repo(".ai/vault-sync.json", json.dumps(cfg))
            with self.assertRaises(vault_sync.SyncError, msg=project):
                self.env.sync()
        cfg = {"project": PROJECT, "repo": "bad repo", "vault_dir": str(self.env.project_dir)}
        self.env.write_repo(".ai/vault-sync.json", json.dumps(cfg))
        with self.assertRaises(vault_sync.SyncError):
            self.env.sync()

    def test_a_symlink_out_of_the_project_folder_is_refused(self):
        outside = self.env.tmp / "outside"
        outside.mkdir()
        (self.env.project_dir / "04 Decisions").mkdir()
        (self.env.project_dir / "04 Decisions" / REPO).symlink_to(outside, target_is_directory=True)
        self.env.populate()
        with self.assertRaises(vault_sync.SyncError) as ctx:
            self.env.sync()
        self.assertIn("outside the project folder", str(ctx.exception))
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_sources_are_skipped(self):
        self.env.populate()
        secret = self.env.tmp / "secret.md"
        secret.write_text("# do not copy\n", encoding="utf-8")
        (self.env.repo / ".ai/adr/ADR-0009-link.md").symlink_to(secret)
        self.env.sync()
        self.assertFalse(any("ADR-0009" in p.name for p in (self.env.project_dir / "04 Decisions").rglob("*.md")))

    # --- command line ------------------------------------------------------------------------

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = vault_sync.main(["--repo-root", str(self.env.repo), "--knowledge-dir",
                                    str(self.env.knowledge), *args])
        return code, out.getvalue(), err.getvalue()

    def test_cli_reports_success(self):
        self.env.populate()
        code, out, err = self.run_main()
        self.assertEqual(code, 0, err)
        self.assertIn(f"standard {STANDARD_VERSION}", out)

    def test_cli_exits_2_with_a_message_on_error(self):
        shutil.rmtree(self.env.knowledge / "Project Standard")
        code, out, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("vault_sync:", err)


class StandardContractTest(unittest.TestCase):
    """The pinned snapshot must match the real standard, when the real one is available."""

    def test_snapshot_matches_the_real_standard(self):
        real = os.environ.get("KNOWLEDGE_DIR")
        if not real or not (pathlib.Path(real) / "Project Standard").is_dir():
            self.skipTest("KNOWLEDGE_DIR not set; snapshot not compared with the real standard")
        for rel in ("standard.json", "_templates/Project Hub.md", "_templates/Project Conventions.md"):
            self.assertEqual((SNAPSHOT / "Project Standard" / rel).read_text(encoding="utf-8"),
                             (pathlib.Path(real) / "Project Standard" / rel).read_text(encoding="utf-8"), rel)


if __name__ == "__main__":
    unittest.main()
