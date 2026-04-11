import importlib.machinery
import importlib.util
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


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

    def test_config_uses_default_openclaw_agent_paths(self):
        self.write_json(
            self.home / ".openclaw/openclaw.json",
            {
                "agents": {
                    "list": [
                        {"id": "dev", "default": True},
                        {"id": "lingxi"},
                    ]
                }
            },
        )

        cfg = self.mod.Config(self.home)

        self.assertEqual(cfg.oc_agent_id, "dev")
        self.assertEqual(cfg.oc_models, self.home / ".openclaw/agents/dev/agent/models.json")
        self.assertEqual(cfg.oc_auth, self.home / ".openclaw/agents/dev/agent/auth.json")
        self.assertEqual(cfg.oc_auth_profiles, self.home / ".openclaw/agents/dev/agent/auth-profiles.json")

    def test_parse_global_flags_supports_openclaw_agent_options(self):
        positional, force, agent_id, all_agents = self.mod.parse_global_flags(
            ["openclaw", "flames", "--agent", "lingxi"]
        )
        self.assertEqual(positional, ["openclaw", "flames"])
        self.assertFalse(force)
        self.assertEqual(agent_id, "lingxi")
        self.assertFalse(all_agents)

        positional, force, agent_id, all_agents = self.mod.parse_global_flags(
            ["--force", "flames", "--all-agents"]
        )
        self.assertEqual(positional, ["flames"])
        self.assertTrue(force)
        self.assertEqual(agent_id, "")
        self.assertTrue(all_agents)

    def test_switch_openclaw_flames_updates_all_agents_by_default(self):
        self.write_json(
            self.home / ".openclaw/openclaw.json",
            {
                "agents": {
                    "defaults": {
                        "model": {
                            "primary": "quotio/claude-sonnet-4-6",
                        }
                    },
                    "list": [
                        {"id": "dev", "default": True},
                        {"id": "lingxi"},
                    ],
                },
                "models": {"providers": {}},
            },
        )
        for agent_id in ("dev", "lingxi"):
            agent_dir = self.home / f".openclaw/agents/{agent_id}/agent"
            self.write_json(agent_dir / "models.json", {"providers": {}})
            self.write_json(agent_dir / "auth.json", {})
            self.write_json(agent_dir / "auth-profiles.json", {})

        cfg = self.mod.Config(self.home)
        self.mod.switch_openclaw("flames", cfg, {"flames": "dummy"}, profile="", model="")

        oc = json.loads((self.home / ".openclaw/openclaw.json").read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "flames/gpt-5.4")

        for agent_id in ("dev", "lingxi"):
            agent_dir = self.home / f".openclaw/agents/{agent_id}/agent"
            models = json.loads((agent_dir / "models.json").read_text(encoding="utf-8"))
            self.assertEqual(models["providers"]["flames"]["api"], "openai-responses")
            self.assertTrue(models["providers"]["flames"]["authHeader"])
            self.assertEqual(models["providers"]["flames"]["apiKey"], "dummy")

            auth = json.loads((agent_dir / "auth.json").read_text(encoding="utf-8"))
            self.assertEqual(auth["flames"]["key"], "dummy")

            auth_profiles = json.loads((agent_dir / "auth-profiles.json").read_text(encoding="utf-8"))
            self.assertEqual(auth_profiles["lastGood"]["flames"], "flames:manual")

    def test_switch_openclaw_flames_with_explicit_agent_uses_agent_model_override(self):
        self.write_json(
            self.home / ".openclaw/openclaw.json",
            {
                "agents": {
                    "defaults": {
                        "model": {
                            "primary": "quotio/claude-sonnet-4-6",
                        }
                    },
                    "list": [
                        {"id": "dev", "default": True},
                        {"id": "lingxi"},
                    ],
                },
                "models": {"providers": {}},
            },
        )
        for agent_id in ("dev", "lingxi"):
            agent_dir = self.home / f".openclaw/agents/{agent_id}/agent"
            self.write_json(agent_dir / "models.json", {"providers": {}})
            self.write_json(agent_dir / "auth.json", {})
            self.write_json(agent_dir / "auth-profiles.json", {})

        cfg = self.mod.Config(self.home)
        self.mod.switch_openclaw(
            "flames",
            cfg,
            {"flames": "dummy"},
            profile="",
            model="",
            agent_id="lingxi",
        )

        oc = json.loads((self.home / ".openclaw/openclaw.json").read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "quotio/claude-sonnet-4-6")

        agent_entries = {entry["id"]: entry for entry in oc["agents"]["list"]}
        self.assertNotIn("model", agent_entries["dev"])
        self.assertEqual(agent_entries["lingxi"]["model"], "flames/gpt-5.4")

        dev_cfg = self.mod.Config(self.home)
        self.assertEqual(self.mod.detect_provider("openclaw", dev_cfg), "quotio")

        lingxi_cfg = self.mod.Config(self.home)
        self.mod.configure_openclaw_agent_paths(lingxi_cfg, "lingxi")
        self.assertEqual(self.mod.detect_provider("openclaw", lingxi_cfg), "flames")

        lingxi_models = json.loads(
            (self.home / ".openclaw/agents/lingxi/agent/models.json").read_text(encoding="utf-8")
        )
        self.assertEqual(lingxi_models["providers"]["flames"]["api"], "openai-responses")

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

    def test_switch_codex_icodeeasy_writes_provider_block_and_detects_icodeeasy(self):
        self.mod.switch_codex("icodeeasy", self.cfg, {"icodeeasy": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"icodeeasy"\s*$', text, re.M))
        self.assertIn('model = "gpt-5.4"', text)
        self.assertIn("[model_providers.icodeeasy]", text)
        self.assertIn('base_url = "https://api.icodeeasy.cc/v1"', text)
        self.assertIn('env_key = "ICODEEASY_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "icodeeasy")

    def test_switch_openclaw_flames_writes_provider_and_auth_store(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw("flames", self.cfg, {"flames": "dummy"}, profile="", model="")

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "flames/gpt-5.4")

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["flames"]["baseUrl"], "https://www.flamescn.vip/v1")
        self.assertEqual(models["providers"]["flames"]["api"], "openai-responses")
        self.assertTrue(models["providers"]["flames"]["authHeader"])
        self.assertEqual(models["providers"]["flames"]["apiKey"], "dummy")
        self.assertEqual(models["providers"]["flames"]["models"][0]["api"], "openai-responses")

        auth = json.loads(self.cfg.oc_auth.read_text(encoding="utf-8"))
        self.assertEqual(auth["flames"]["key"], "dummy")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["flames"], "flames:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "flames")

    def test_switch_openclaw_duck_codex_profile_writes_codex_provider(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw(
            "duck",
            self.cfg,
            {"duck_anthropic": "anth", "duck_gemini": "gem", "duck_codex": "codex"},
            profile="codex",
            model="",
        )

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(
            oc["agents"]["defaults"]["model"]["primary"],
            "duckcoding-codex/gpt-5.4-xhigh-openai-compact",
        )

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["duckcoding-codex"]["apiKey"], "codex")
        self.assertEqual(
            models["providers"]["duckcoding-codex"]["models"][0]["id"],
            "gpt-5.4-xhigh-openai-compact",
        )

        auth = json.loads(self.cfg.oc_auth.read_text(encoding="utf-8"))
        self.assertEqual(auth["duckcoding-codex"]["key"], "codex")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["duckcoding-codex"], "duckcoding-codex:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "duck")

    def test_switch_gemini_cli_icodeeasy_updates_env_and_detects_icodeeasy(self):
        self.mod.switch_gemini_cli("icodeeasy", self.cfg, {"icodeeasy": "dummy"}, model="")

        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=https://api.icodeeasy.cc", gemini_env)
        self.assertIn("GEMINI_API_KEY=dummy", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-2.5-flash", gemini_env)
        self.assertEqual(self.mod.detect_provider("gemini", self.cfg), "icodeeasy")

        bashrc = self.cfg.bashrc.read_text(encoding="utf-8")
        self.assertIn('export GEMINI_API_KEY="dummy"', bashrc)

    def test_switch_gemini_cli_aiwave_uses_gemini_key_slot(self):
        self.mod.switch_gemini_cli(
            "aiwave",
            self.cfg,
            {"aiwave_gemini": "gem-slot", "aiwave_codex": "codex-slot"},
            model="",
        )

        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=https://api.ai-wave.org/gemini", gemini_env)
        self.assertIn("GEMINI_API_KEY=gem-slot", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-3.1-pro-preview", gemini_env)

        bashrc = self.cfg.bashrc.read_text(encoding="utf-8")
        self.assertIn('export GEMINI_API_KEY="gem-slot"', bashrc)

    def test_switch_openclaw_aiwave_writes_gemini_provider(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw("aiwave", self.cfg, {"aiwave_gemini": "dummy"}, profile="", model="")

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "aiwave/gemini-3.1-pro-preview")

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["aiwave"]["baseUrl"], "https://api.ai-wave.org/gemini")
        self.assertEqual(models["providers"]["aiwave"]["api"], "google-generative-ai")
        self.assertEqual(models["providers"]["aiwave"]["apiKey"], "dummy")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["aiwave"], "aiwave:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "aiwave")

    def test_switch_droid_aiwave_uses_codex_key_slot(self):
        self.mod.switch_droid(
            "aiwave",
            self.cfg,
            {"aiwave_gemini": "gem-slot", "aiwave_codex": "codex-slot"},
            profile="",
            model="",
        )

        settings = json.loads(self.cfg.factory_settings.read_text(encoding="utf-8"))
        self.assertEqual(settings["customModels"][0]["apiKey"], "codex-slot")
        self.assertEqual(settings["customModels"][0]["baseUrl"], "https://api.ai-wave.org/v1")

    def test_get_keys_prefers_split_aiwave_slots(self):
        with patch.dict(
            os.environ,
            {
                "AIWAVE_CODEX_API_KEY": "codex-slot",
                "AIWAVE_GEMINI_GCP_API_KEY": "gem-gcp-slot",
                "AIWAVE_GEMINI_API_KEY": "gem-slot",
                "AIWAVE_API_KEY": "legacy-slot",
            },
            clear=False,
        ):
            keys = self.mod.get_keys({})

        self.assertEqual(keys["aiwave_codex"], "codex-slot")
        self.assertEqual(keys["aiwave_gemini"], "gem-gcp-slot")
        self.assertEqual(keys["aiwave"], "legacy-slot")

    def test_switch_hermes_aiwave_updates_root_and_profiles(self):
        root_cfg = self.home / ".hermes/config.yaml"
        profile_cfg = self.home / ".hermes/profiles/dev/config.yaml"
        for path in (root_cfg, profile_cfg):
            self.write(
                path,
                yaml.safe_dump(
                    {
                        "model": {
                            "default": "gpt-5.4",
                            "provider": "custom:flames",
                            "base_url": "https://www.flamescn.vip/v1",
                            "api_key": "old",
                            "api_mode": "codex_responses",
                        },
                        "custom_providers": [
                            {
                                "name": "flames",
                                "base_url": "https://www.flamescn.vip/v1",
                                "api_key": "",
                                "api_mode": "codex_responses",
                                "model": "gpt-5.4",
                            }
                        ],
                    },
                    sort_keys=False,
                ),
            )

        self.mod.switch_hermes("aiwave", self.cfg, {"aiwave_gemini": "gem-key"}, model="")

        for path in (root_cfg, profile_cfg):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(data["model"]["provider"], "custom:aiwave")
            self.assertEqual(data["model"]["default"], "gemini-3.1-pro-preview")
            self.assertEqual(data["model"]["base_url"], "https://api.ai-wave.org/v1")
            self.assertEqual(data["model"]["api_key"], "gem-key")
            self.assertEqual(data["model"]["api_mode"], "chat_completions")

            entries = {entry["name"]: entry for entry in data["custom_providers"]}
            self.assertEqual(entries["aiwave"]["base_url"], "https://api.ai-wave.org/v1")
            self.assertEqual(entries["aiwave"]["api_key"], "gem-key")
            self.assertEqual(entries["aiwave"]["api_mode"], "chat_completions")
            self.assertEqual(entries["aiwave"]["model"], "gemini-3.1-pro-preview")

        self.assertEqual(self.mod.detect_provider("hermes", self.cfg), "aiwave")

    def test_model_validation_rejects_openclaw_icodeeasy_gpt_model(self):
        with self.assertRaises(self.mod.SwitchError):
            self.mod.validate_model_for_tool("openclaw", "gpt-5.4", "icodeeasy")

    def test_model_in_provider_accepts_icodeeasy_gpt_and_gemini(self):
        self.assertTrue(self.mod.model_in_provider("gpt-5.4", "icodeeasy"))
        self.assertTrue(self.mod.model_in_provider("gemini-2.5-flash", "icodeeasy"))

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
