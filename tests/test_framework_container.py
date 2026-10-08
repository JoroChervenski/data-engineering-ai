"""Tests for this repository's own Dev Container (.devcontainer/).

It may see the vault's Knowledge/ and Templates/ folders, read-only, and nothing else
(AGENTS.md rule 11; Project Standard, Isolation).

Run: python3 -m unittest discover -s tests
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import devcontainer_rules  # noqa: E402

DEVCONTAINER = ROOT / ".devcontainer"


def tree(root):
    return {str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None)
            for p in sorted(pathlib.Path(root).rglob("*"))}


class FrameworkContainerTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8"))

    def test_it_mounts_only_knowledge_and_templates_read_only(self):
        self.assertEqual(devcontainer_rules.check_mounts(self.config, "framework"), [])

    def test_it_never_names_projects_home_or_client_repos(self):
        text = (DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8")
        for forbidden in ("Projects", "Home.md", "clients", "${localEnv:HOME}", "/mnt/c"):
            self.assertNotIn(forbidden, text, forbidden)

    def test_it_holds_no_client_credentials(self):
        self.assertNotIn("runArgs", self.config)
        self.assertFalse(any("env-file" in str(v) for v in self.config.values()))

    def test_it_reuses_the_template_dockerfile_so_the_base_image_is_pinned_once(self):
        dockerfile = (DEVCONTAINER / self.config["build"]["dockerfile"]).resolve()
        context = (DEVCONTAINER / self.config["build"]["context"]).resolve()
        self.assertEqual(dockerfile, ROOT / "templates" / "client-project" / ".devcontainer" / "Dockerfile")
        self.assertTrue(dockerfile.is_file() and context.is_dir())
        self.assertEqual(self.config["remoteUser"], "vscode")

    def test_claude_state_is_one_volume_per_container(self):
        volumes = [m for m in self.config["mounts"] if "type=volume" in m]
        self.assertEqual(len(volumes), 1)
        self.assertIn("${devcontainerId}", volumes[0])
        self.assertEqual(self.config["containerEnv"]["CLAUDE_CONFIG_DIR"], "/home/vscode/.claude")

    def test_the_tests_find_the_real_standard_inside_the_container(self):
        env = self.config["containerEnv"]
        self.assertEqual(env["KNOWLEDGE_DIR"], "/vault/Knowledge")
        self.assertEqual(env["VAULT_KNOWLEDGE_DIR"], "/vault/Knowledge")
        self.assertEqual(env["DATA_ENGINEERING_AI_SRC"], "${containerWorkspaceFolder}")

    def run_initialize(self, **env):
        full = {k: v for k, v in os.environ.items() if k != "AI_VAULT"}
        full.update(env)
        return subprocess.run(["sh", ".devcontainer/initialize.sh"], cwd=ROOT, env=full,
                              capture_output=True, text=True)

    def test_initialize_checks_the_vault_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            self.assertEqual(self.run_initialize().returncode, 1)
            self.assertIn("AI_VAULT", self.run_initialize().stderr)
            (vault / "Knowledge").mkdir()
            missing = self.run_initialize(AI_VAULT=str(vault))
            self.assertEqual(missing.returncode, 1)
            self.assertIn("Templates", missing.stderr)
            (vault / "Templates").mkdir()
            before, repo_before = tree(vault), {p for p in ROOT.iterdir()}
            ok = self.run_initialize(AI_VAULT=str(vault))
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(tree(vault), before)
            self.assertEqual({p for p in ROOT.iterdir()}, repo_before)
            self.assertFalse((vault / "Projects").exists())

    def test_initialize_is_executable(self):
        self.assertTrue(os.access(DEVCONTAINER / "initialize.sh", os.X_OK))


if __name__ == "__main__":
    unittest.main()
