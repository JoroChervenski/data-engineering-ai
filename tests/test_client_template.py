"""Tests for the client template and scripts/new-client.sh.

Run: python3 -m unittest discover -s tests
"""
import copy
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import devcontainer_rules  # noqa: E402
import new_client  # noqa: E402
import validate_framework  # noqa: E402
import vault_sync  # noqa: E402

SNAPSHOT = ROOT / "tests" / "fixtures" / "standard"

EXPECTED_FILES = {
    ".ai/guardrails.json", ".ai/manifest.yaml", ".ai/vault-sync.json", ".claude/settings.json",
    ".devcontainer/Dockerfile", ".devcontainer/devcontainer.json", ".devcontainer/initialize.sh",
    ".env.example", ".gitignore", "AGENTS.md", "CLAUDE.md", "README.md",
    "docs/requirements/.gitkeep", "tests/.gitkeep",
}


def files_under(root):
    root = pathlib.Path(root)
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def tree(root):
    return {str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None)
            for p in sorted(pathlib.Path(root).rglob("*"))}


class TemplateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.vault = self.tmp / "vault"
        (self.vault / "Projects").mkdir(parents=True)
        shutil.copytree(SNAPSHOT / "Project Standard", self.vault / "Knowledge" / "Project Standard")
        self.targets = self.tmp / "clients"
        self.targets.mkdir()
        self.lines = []

    def create(self, project, name, **kw):
        target = self.targets / name
        new_client.run(project, target, vault=str(self.vault), out=self.lines.append, **kw)
        return target

    def devcontainer(self, target):
        return json.loads((target / ".devcontainer/devcontainer.json").read_text())

    # --- completeness and validity -----------------------------------------------------------

    def test_a_new_repo_has_every_expected_file(self):
        target = self.create("Demo", "demo-repo")
        self.assertEqual(files_under(target), EXPECTED_FILES)

    def test_a_new_repo_satisfies_the_standards_structure(self):
        std = json.loads((SNAPSHOT / "Project Standard" / "standard.json").read_text())
        target = self.create("Demo", "demo-repo")
        for rel in std["repo"]["structure_files"]:
            self.assertTrue((target / rel).is_file(), f"standard requires {rel}")
        for rel in std["repo"]["required_dirs"]:
            self.assertTrue((target / rel).is_dir(), f"standard requires {rel}/")
        for rel in ("docs/adr", "docs/runbooks", "docs/architecture"):
            self.assertFalse((target / rel).exists(), f"PS-STRUCT-04 forbids {rel}")
        self.assertEqual((target / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        cfg = json.loads((target / ".ai/vault-sync.json").read_text())
        self.assertEqual(sorted(cfg), sorted(std["repo"]["sync_config"]["keys"]))
        self.assertEqual(std["repo"]["sync_config"]["file"], ".ai/vault-sync.json")

    def test_a_new_repo_carries_the_no_ai_signature_rule(self):
        target = self.create("Demo", "demo-repo")
        settings = json.loads((target / ".claude/settings.json").read_text())
        self.assertEqual(settings["attribution"], {"commit": "", "pr": "", "sessionUrl": False})
        self.assertIn("No AI signature", (target / "AGENTS.md").read_text())

    def test_a_new_repo_explains_and_supports_the_policies(self):
        target = self.create("Demo", "demo-repo")
        self.assertIn("AI_ENVIRONMENT=", (target / ".env.example").read_text().splitlines())
        readme = (target / "README.md").read_text()
        for part in ("## Policies", "AI_ENVIRONMENT", "secrets.allow_paths", "audit/decisions.jsonl"):
            self.assertIn(part, readme)
        manifest = (target / ".ai/manifest.yaml").read_text()
        self.assertIn("environments:", manifest)
        self.assertIn("write_access", manifest)

    def test_no_placeholder_is_left(self):
        target = self.create("Demo", "demo-repo")
        for rel in files_under(target):
            text = (target / rel).read_text(encoding="utf-8")
            for placeholder in ("__PROJECT__", "__REPO__", "<project-name>"):
                self.assertNotIn(placeholder, text, f"{rel} still has {placeholder}")

    def test_json_files_are_valid(self):
        target = self.create("Demo", "demo-repo")
        for rel in (".ai/guardrails.json", ".ai/vault-sync.json", ".claude/settings.json",
                    ".devcontainer/devcontainer.json"):
            json.loads((target / rel).read_text(encoding="utf-8"))

    def test_project_metadata_and_sync_config(self):
        target = self.create("Demo", "demo-repo")
        cfg = json.loads((target / ".ai/vault-sync.json").read_text())
        self.assertEqual(cfg, {"project": "Demo", "repo": "demo-repo", "vault_dir": "/vault/Demo"})
        manifest = (target / ".ai/manifest.yaml").read_text()
        self.assertIn('name: "Demo"', manifest)
        version = (ROOT / "VERSION").read_text().strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(manifest, rf'framework:\n  version: "{re.escape(version)}"')
        standard_version = json.loads((SNAPSHOT / "Project Standard" / "standard.json").read_text())["version"]
        self.assertRegex(manifest, rf'standard:\n  version: "{re.escape(standard_version)}"')
        self.assertIn("allow_force_push: false", manifest)

    def test_the_vault_layout_is_built_at_creation(self):
        self.create("Demo", "demo-repo")
        project_dir = self.vault / "Projects" / "Demo"
        self.assertTrue((project_dir / "Demo.md").is_file())
        self.assertTrue((project_dir / "_Conventions.md").is_file())
        self.assertTrue((project_dir / "04 Decisions").is_dir())

    def test_no_sync_leaves_the_vault_folder_empty(self):
        self.create("Demo", "demo-repo", run_sync=False)
        self.assertEqual(list((self.vault / "Projects" / "Demo").iterdir()), [])

    def test_claude_settings_protect_secrets_and_register_the_plugin(self):
        target = self.create("Demo", "demo-repo")
        settings = json.loads((target / ".claude/settings.json").read_text())
        deny, ask = settings["permissions"]["deny"], settings["permissions"]["ask"]
        for rule in ("Read(./.env)", "Read(~/.ssh/**)", "Read(~/.azure/**)", "Read(~/.config/gh/**)",
                     "Bash(git push --force *)", "Bash(git reset --hard *)"):
            self.assertIn(rule, deny)
        self.assertIn("Bash(git push *)", ask)
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(list(settings["enabledPlugins"]), [f"{plugin['name']}@{marketplace['name']}"])
        repo = settings["extraKnownMarketplaces"][marketplace["name"]]["source"]["repo"]
        self.assertTrue(plugin["repository"].endswith("/" + repo))

    def test_guardrails_hold_project_additions_in_the_policy_vocabulary(self):
        target = self.create("Demo", "demo-repo")
        guardrails = json.loads((target / ".ai/guardrails.json").read_text())
        self.assertEqual(set(guardrails["commands"]), {"deny", "approval_required"})
        self.assertEqual(guardrails["default_role"], "developer")
        self.assertFalse(guardrails["production"]["shell_write_operations"])
        self.assertTrue(guardrails["production"]["deployment_requires_explicit_approval"])
        self.assertEqual(guardrails["secrets"], {"allow_paths": []})

    # --- isolation and secrets ---------------------------------------------------------------

    def test_the_dev_container_mounts_only_what_the_standard_allows(self):
        target = self.create("Demo", "demo-repo")
        self.assertEqual(devcontainer_rules.check_mounts(self.devcontainer(target), "project", "Demo"), [])

    def test_azure_cli_is_optional(self):
        plain = self.create("Demo", "demo-repo")
        azure = self.create("Other", "other-repo", with_azure=True)
        self.assertNotIn(new_client.AZURE_FEATURE, self.devcontainer(plain)["features"])
        self.assertIn(new_client.AZURE_FEATURE, self.devcontainer(azure)["features"])
        self.assertEqual(devcontainer_rules.check_mounts(self.devcontainer(azure), "project", "Other"), [])

    def test_no_secret_is_generated(self):
        target = self.create("Demo", "demo-repo")
        self.assertFalse((target / ".env").exists())
        for rel in files_under(target):
            text = (target / rel).read_text(encoding="utf-8")
            for label, pattern in validate_framework.SECRET_PATTERNS.items():
                self.assertIsNone(pattern.search(text), f"{rel}: possible {label}")
        for line in (target / ".env.example").read_text().splitlines():
            if line and not line.startswith("#"):
                self.assertTrue(line.endswith("="), f"value in .env.example: {line}")
        self.assertIn(".env", (target / ".gitignore").read_text().splitlines())

    def test_dockerfile_bakes_in_nothing_and_runs_unprivileged(self):
        target = self.create("Demo", "demo-repo")
        text = (target / ".devcontainer/Dockerfile").read_text()
        code = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        self.assertRegex(code[0], r"^FROM \S+:\S+$")
        self.assertNotIn(":latest", code[0])
        self.assertEqual(code[-1], "USER vscode")
        joined = "\n".join(code)
        self.assertNotRegex(joined, r"(?m)^\s*(COPY|ADD)\b")
        self.assertNotRegex(joined, r"\|\s*(ba)?sh\b")
        self.assertNotRegex(joined, r"(?i)\b(ENV|ARG)\s+\w*(KEY|TOKEN|SECRET|PASSWORD)")

    def test_each_client_has_its_own_claude_state_volume(self):
        target = self.create("Demo", "demo-repo")
        config = self.devcontainer(target)
        volumes = [m for m in config["mounts"] if "type=volume" in m]
        self.assertEqual(len(volumes), 1)
        self.assertIn("${devcontainerId}", volumes[0])
        self.assertEqual(config["containerEnv"]["CLAUDE_CONFIG_DIR"], "/home/vscode/.claude")

    # --- the mount rules themselves ----------------------------------------------------------

    def valid_config(self):
        self._configs = getattr(self, "_configs", 0) + 1
        return self.devcontainer(self.create("Demo", f"config-repo-{self._configs}"))

    def test_rules_reject_unsafe_mounts(self):
        base = self.valid_config()
        v = devcontainer_rules.VAULT
        cases = {
            "whole vault": f"source={v},target=/vault,type=bind",
            "other project": f"source={v}/Projects/Other,target=/vault/Other,type=bind",
            "home folder": "source=${localEnv:HOME},target=/home/vscode/host,type=bind",
            "Home.md": f"source={v}/Home.md,target=/vault/Home.md,type=bind",
            "ssh keys": "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind",
            "docker socket": "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind",
            "parent folder": "source=${localWorkspaceFolder}/..,target=/clients,type=bind",
            "volume with a path": "source=/etc,target=/x,type=volume",
        }
        for name, mount in cases.items():
            config = copy.deepcopy(base)
            config["mounts"].append(mount)
            self.assertTrue(devcontainer_rules.check_mounts(config, "project", "Demo"), name)

    def test_rules_reject_a_writable_knowledge_mount(self):
        config = self.valid_config()
        config["mounts"] = [m.replace(",readonly", "") for m in config["mounts"]]
        problems = devcontainer_rules.check_mounts(config, "project", "Demo")
        self.assertTrue(any("read-only" in p for p in problems), problems)

    def test_rules_reject_object_form_vault_mounts(self):
        config = self.valid_config()
        config["mounts"] = [m for m in config["mounts"] if "Knowledge" not in m]
        config["mounts"].append({"source": f"{devcontainer_rules.VAULT}/Knowledge", "target": "/vault/Knowledge",
                                 "type": "bind"})
        self.assertTrue(devcontainer_rules.check_mounts(config, "project", "Demo"))

    def test_rules_reject_missing_mounts_and_wrong_targets(self):
        config = self.valid_config()
        config["mounts"] = [m for m in config["mounts"] if "Knowledge" not in m]
        self.assertTrue(any("missing" in p for p in devcontainer_rules.check_mounts(config, "project", "Demo")))
        config = self.valid_config()
        config["mounts"] = [m.replace("target=/vault/Demo", "target=/data") for m in config["mounts"]]
        self.assertTrue(any("must be mounted at" in p for p in devcontainer_rules.check_mounts(config, "project", "Demo")))

    def test_rules_reject_mounts_added_through_run_args_or_workspace_mount(self):
        for patch in ({"runArgs": ["-v", "/:/host"]}, {"runArgs": ["--mount=type=bind,src=/,dst=/h"]},
                      {"runArgs": ["--privileged"]}, {"workspaceMount": "source=/,target=/w,type=bind"}):
            config = self.valid_config()
            config.update(patch)
            self.assertTrue(devcontainer_rules.check_mounts(config, "project", "Demo"), patch)

    def test_framework_role_allows_only_knowledge_and_templates(self):
        v = devcontainer_rules.VAULT
        good = {"mounts": [f"source={v}/Knowledge,target=/vault/Knowledge,type=bind,readonly",
                           f"source={v}/Templates,target=/vault/Templates,type=bind,readonly"]}
        self.assertEqual(devcontainer_rules.check_mounts(good, "framework"), [])
        with_project = copy.deepcopy(good)
        with_project["mounts"].append(f"source={v}/Projects/Demo,target=/vault/Demo,type=bind")
        self.assertTrue(devcontainer_rules.check_mounts(with_project, "framework"))
        writable = {"mounts": [m.replace(",readonly", "") for m in good["mounts"]]}
        self.assertTrue(devcontainer_rules.check_mounts(writable, "framework"))
        self.assertTrue(devcontainer_rules.check_mounts({"mounts": good["mounts"][:1]}, "framework"))

    # --- safe handling of the destination ----------------------------------------------------

    def test_an_existing_file_is_never_overwritten_and_nothing_is_written(self):
        target = self.targets / "demo-repo"
        target.mkdir()
        (target / "README.md").write_text("mine", encoding="utf-8")
        before, vault_before = tree(self.targets), tree(self.vault)
        with self.assertRaises(new_client.NewClientError) as ctx:
            new_client.run("Demo", target, vault=str(self.vault), out=self.lines.append)
        self.assertIn("README.md", str(ctx.exception))
        self.assertEqual(tree(self.targets), before)
        self.assertEqual(tree(self.vault), vault_before)
        self.assertFalse((self.vault / "Projects" / "Demo").exists())

    def test_unrelated_existing_content_is_left_alone(self):
        target = self.targets / "demo-repo"
        (target / "src").mkdir(parents=True)
        (target / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
        (target / ".git").mkdir()
        (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        new_client.run("Demo", target, vault=str(self.vault), out=self.lines.append)
        self.assertEqual((target / "src" / "app.py").read_text(), "print('hi')\n")
        self.assertEqual((target / ".git" / "HEAD").read_text(), "ref: refs/heads/main\n")
        self.assertTrue(EXPECTED_FILES <= files_under(target))

    def test_a_failure_part_way_removes_what_it_created(self):
        target = self.targets / "demo-repo"
        original = vault_sync.sync

        def boom(*args, **kwargs):
            raise vault_sync.SyncError("boom")

        vault_sync.sync = boom
        try:
            with self.assertRaises(vault_sync.SyncError):
                new_client.run("Demo", target, vault=str(self.vault), out=self.lines.append)
        finally:
            vault_sync.sync = original
        self.assertFalse(target.exists())
        self.assertFalse((self.vault / "Projects" / "Demo").exists())

    def test_bad_names_write_nothing(self):
        before = tree(self.tmp)
        for project in ("my project", "Knowledge", "Templates", "Home", "a - b", "-x", ""):
            with self.assertRaises(new_client.NewClientError, msg=project):
                new_client.run(project, self.targets / "r", vault=str(self.vault), out=self.lines.append)
        with self.assertRaises(new_client.NewClientError):
            new_client.run("Demo", self.targets / "r", repo="bad repo", vault=str(self.vault), out=self.lines.append)
        self.assertEqual(tree(self.tmp), before)

    def test_missing_or_wrong_vault_is_refused(self):
        saved = os.environ.pop("AI_VAULT", None)
        try:
            with self.assertRaises(new_client.NewClientError):
                new_client.run("Demo", self.targets / "r", out=self.lines.append)
        finally:
            if saved is not None:
                os.environ["AI_VAULT"] = saved
        with self.assertRaises(new_client.NewClientError):
            new_client.run("Demo", self.targets / "r", vault=str(self.tmp), out=self.lines.append)
        shutil.rmtree(self.vault / "Knowledge" / "Project Standard")
        with self.assertRaises(new_client.NewClientError):
            new_client.run("Demo", self.targets / "r", vault=str(self.vault), out=self.lines.append)
        self.assertFalse((self.targets / "r").exists())

    # --- two clients -------------------------------------------------------------------------

    def test_two_clients_are_independent(self):
        a = self.create("Alpha", "alpha-repo")
        b = self.create("Beta", "beta-repo")
        for target, own, other in ((a, "Alpha", "Beta"), (b, "Beta", "Alpha")):
            for rel in files_under(target):
                text = (target / rel).read_text(encoding="utf-8")
                self.assertNotIn(other, text, f"{rel} mentions the other client")
            self.assertIn(f"Projects/{own},", " ".join(self.devcontainer(target)["mounts"]) + ",")
        alpha_vault, beta_vault = self.vault / "Projects" / "Alpha", self.vault / "Projects" / "Beta"
        self.assertTrue(alpha_vault.is_dir() and beta_vault.is_dir())
        before = tree(beta_vault)
        vault_sync.sync(a, self.vault / "Knowledge", vault_dir=alpha_vault)
        self.assertEqual(tree(beta_vault), before)

    def test_a_second_repo_reuses_the_project_folder_without_touching_its_notes(self):
        self.create("Demo", "first-repo")
        hub = self.vault / "Projects" / "Demo" / "Demo.md"
        hub.write_text(hub.read_text() + "\nMy own line.\n", encoding="utf-8")
        second = self.create("Demo", "second-repo")
        self.assertIn("My own line.", hub.read_text())
        self.assertEqual(json.loads((second / ".ai/vault-sync.json").read_text())["repo"], "second-repo")

    # --- initialize.sh and the wrapper -------------------------------------------------------

    def run_initialize(self, target, project, **env):
        full = {k: v for k, v in os.environ.items() if k != "AI_VAULT"}
        full.update(env)
        return subprocess.run(["sh", ".devcontainer/initialize.sh", project], cwd=target, env=full,
                              capture_output=True, text=True)

    def test_initialize_checks_the_vault_and_prepares_env(self):
        target = self.create("Demo", "demo-repo")
        no_var = self.run_initialize(target, "Demo")
        self.assertEqual(no_var.returncode, 1)
        self.assertIn("AI_VAULT", no_var.stderr)
        missing = self.run_initialize(target, "Nope", AI_VAULT=str(self.vault))
        self.assertEqual(missing.returncode, 1)
        self.assertIn("Missing vault folder", missing.stderr)
        self.assertFalse((self.vault / "Projects" / "Nope").exists())
        self.assertFalse((target / ".env").exists())
        ok = self.run_initialize(target, "Demo", AI_VAULT=str(self.vault))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertTrue((target / ".env").is_file())
        self.assertEqual((target / ".env").read_text(), "")
        self.assertTrue(os.access(target / ".devcontainer/initialize.sh", os.X_OK))

    def test_the_shell_wrapper_works_and_fails_safely(self):
        script = ROOT / "scripts" / "new-client.sh"
        self.assertTrue(os.access(script, os.X_OK))
        target = self.targets / "wrapped"
        ok = subprocess.run([str(script), "Demo", str(target), "--vault", str(self.vault)],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(files_under(target), EXPECTED_FILES)
        again = subprocess.run([str(script), "Demo", str(target), "--vault", str(self.vault)],
                               capture_output=True, text=True)
        self.assertEqual(again.returncode, 2)
        self.assertIn("would overwrite", again.stderr)

    def test_set_yaml_scalar(self):
        text = 'framework:\n  version: "unknown" # note\nother:\n  version: "x"\n'
        out = new_client.set_yaml_scalar(text, ("framework", "version"), "1.2.3")
        self.assertEqual(out, 'framework:\n  version: "1.2.3" # note\nother:\n  version: "x"\n')
        with self.assertRaises(new_client.NewClientError):
            new_client.set_yaml_scalar(text, ("framework", "missing"), "1")


if __name__ == "__main__":
    unittest.main()
