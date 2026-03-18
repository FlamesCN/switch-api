import importlib.machinery
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


def load_switch_api_module():
    script = Path(__file__).resolve().parents[1] / "bin" / "switch-api"
    loader = importlib.machinery.SourceFileLoader("switch_api_test", str(script))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class SwitchApiCodexOpenAITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_switch_api_module()

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name)
        self.cfg = self.mod.Config(self.home)
        self.cfg.codex_home.mkdir(parents=True, exist_ok=True)
        self.write(
            self.cfg.cx_config,
            (
                'model = "gpt-5.4"\n'
                'model_provider = "flames_newapi"\n'
                '\n'
                "[model_providers.flames_newapi]\n"
                'name = "Flames NewAPI"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'env_key = "OPENAI_API_KEY"\n'
                'wire_api = "responses"\n'
            ),
        )
        self.write_json(
            self.cfg.codex_home / "auth.json",
            {"auth_mode": "chatgpt", "tokens": {"account_id": "acct-current"}},
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_json(self, path: Path, data) -> None:
        self.write(path, json.dumps(data))

    def init_openclaw_files(self) -> None:
        self.write_json(
            self.cfg.oc_config,
            {
                "agents": {
                    "defaults": {
                        "model": {
                            "primary": "quotio/claude-sonnet-4-6",
                        }
                    }
                },
                "models": {"providers": {}},
            },
        )
        self.write_json(self.cfg.oc_models, {"providers": {}})
        self.write_json(self.cfg.oc_auth, {})
        self.write_json(self.cfg.oc_auth_profiles, {})

    def test_switch_codex_openai_comments_model_provider_for_official_mode(self):
        self.mod.switch_codex("openai", self.cfg, {}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r'^\s*model_provider\s*=\s*"', text, re.M))
        self.assertIn('# model_provider = "flames_newapi"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "openai")

    def test_switch_codex_backup_goes_to_codex_backups_dir(self):
        self.mod.switch_codex("openai", self.cfg, {}, model="")

        backups = list(self.cfg.codex_backup_dir.glob("config.toml.bak.switch-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(list(self.cfg.codex_home.glob("config.toml.bak.switch-*")), [])

    def test_switch_codex_named_openai_uses_flames_newapi_env_slot(self):
        self.mod.switch_codex("openai_V420", self.cfg, {"openai_V420": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"flames_newapi"\s*$', text, re.M))
        self.assertIn('env_key = "OPENAI_V420_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "openai_V420")

    def test_switch_codex_flames_uses_flames_api_key_and_detects_flames(self):
        self.mod.switch_codex("flames", self.cfg, {"flames": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"flames_newapi"\s*$', text, re.M))
        self.assertIn('model = "gpt-5.4"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "flames")

    def test_switch_openclaw_flames_writes_provider_and_auth_store(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw("flames", self.cfg, {"flames": "dummy"}, profile="", model="")

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "flames/gpt-5.4")

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["flames"]["baseUrl"], "https://www.flamescn.vip/v1")
        self.assertEqual(models["providers"]["flames"]["apiKey"], "dummy")

        auth = json.loads(self.cfg.oc_auth.read_text(encoding="utf-8"))
        self.assertEqual(auth["flames"]["key"], "dummy")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["flames"], "flames:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "flames")

    def test_codex_account_use_reads_auth_snapshot_from_accounts_dir(self):
        self.write_json(
            self.cfg.codex_accounts_dir / "auth.json_demo@example.com",
            {"auth_mode": "chatgpt", "tokens": {"account_id": "acct-demo"}},
        )

        self.mod.cmd_codex_account_use(self.cfg, "demo@example.com")

        auth = json.loads((self.cfg.codex_home / "auth.json").read_text(encoding="utf-8"))
        self.assertEqual(auth["tokens"]["account_id"], "acct-demo")

        backups = list(self.cfg.codex_backup_dir.glob("auth.json.bak.switch-*"))
        self.assertEqual(len(backups), 1)
        backup_auth = json.loads(backups[0].read_text(encoding="utf-8"))
        self.assertEqual(backup_auth["tokens"]["account_id"], "acct-current")

    def test_codex_account_use_accepts_auth_backup_email_names(self):
        self.write_json(
            self.cfg.codex_home / "auth.json_demo@example.com",
            {"auth_mode": "chatgpt", "tokens": {"account_id": "acct-demo"}},
        )

        self.mod.cmd_codex_account_use(self.cfg, "demo@example.com")

        auth = json.loads((self.cfg.codex_home / "auth.json").read_text(encoding="utf-8"))
        self.assertEqual(auth["tokens"]["account_id"], "acct-demo")


if __name__ == "__main__":
    unittest.main()
