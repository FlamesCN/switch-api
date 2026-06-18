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

    def init_cc_settings(self, model: str = "claude-sonnet-4-6", env: dict | None = None) -> None:
        self.write_json(
            self.cfg.cc_settings,
            {
                "env": env or {},
                "model": model,
            },
        )

    def init_gemini_balance_env(self, extra: str = "") -> None:
        self.write(
            self.cfg.gemini_balance_env,
            (
                "BASE_URL=https://generativelanguage.googleapis.com/v1beta\n"
                "API_KEYS=[\"old-key\"]\n"
                "TEST_MODEL=gemini-2.5-flash-lite\n"
                + extra
            ),
        )

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
        positional, force, agent_id, all_agents, hermes_profile, all_profiles = self.mod.parse_global_flags(
            ["openclaw", "flames", "--agent", "lingxi"]
        )
        self.assertEqual(positional, ["openclaw", "flames"])
        self.assertFalse(force)
        self.assertEqual(agent_id, "lingxi")
        self.assertFalse(all_agents)
        self.assertEqual(hermes_profile, "")
        self.assertFalse(all_profiles)

        positional, force, agent_id, all_agents, hermes_profile, all_profiles = self.mod.parse_global_flags(
            ["--force", "flames", "--all-agents"]
        )
        self.assertEqual(positional, ["flames"])
        self.assertTrue(force)
        self.assertEqual(agent_id, "")
        self.assertTrue(all_agents)
        self.assertEqual(hermes_profile, "")
        self.assertFalse(all_profiles)

    def test_parse_global_flags_supports_hermes_profile_options(self):
        positional, force, agent_id, all_agents, hermes_profile, all_profiles = self.mod.parse_global_flags(
            ["hermes", "aiwave", "--profile", "video-maker"]
        )
        self.assertEqual(positional, ["hermes", "aiwave"])
        self.assertFalse(force)
        self.assertEqual(agent_id, "")
        self.assertFalse(all_agents)
        self.assertEqual(hermes_profile, "video-maker")
        self.assertFalse(all_profiles)

        positional, force, agent_id, all_agents, hermes_profile, all_profiles = self.mod.parse_global_flags(
            ["--all-profiles", "all", "flames"]
        )
        self.assertEqual(positional, ["all", "flames"])
        self.assertEqual(hermes_profile, "")
        self.assertTrue(all_profiles)

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

    def test_switch_cc_flames_writes_custom_model_env_and_detects_flames(self):
        self.init_cc_settings(
            model="claude-sonnet-4-6",
            env={
                "ANTHROPIC_CUSTOM_MODEL_OPTION": "stale",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_NAME": "stale",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION": "stale",
            },
        )

        self.mod.switch_cc("flames", self.cfg, {"flames": "dummy"}, model="deepseek-v4-pro")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://www.flamescn.vip")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "dummy")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"], "DeepSeek V4 Pro")
        self.assertEqual(
            env["ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION"],
            "Flames NewAPI custom model relay",
        )
        self.assertEqual(env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"], "1")
        self.assertEqual(env["CLAUDE_CODE_ATTRIBUTION_HEADER"], "0")
        self.assertEqual(self.mod.detect_provider("cc", self.cfg), "flames")

    def test_switch_cc_quotio_clears_stale_custom_model_env(self):
        self.init_cc_settings(
            model="gpt-5.4",
            env={
                "ANTHROPIC_CUSTOM_MODEL_OPTION": "deepseek-v4-pro",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_NAME": "DeepSeek V4 Pro",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION": "Flames NewAPI custom model relay",
            },
        )

        self.mod.switch_cc("quotio", self.cfg, {"quotio": "dummy"}, model="")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "claude-opus-4-6-thinking")
        self.assertNotIn("ANTHROPIC_CUSTOM_MODEL_OPTION", env)
        self.assertNotIn("ANTHROPIC_CUSTOM_MODEL_OPTION_NAME", env)
        self.assertNotIn("ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION", env)

    def test_switch_cc_deepseek_writes_direct_provider_config(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc("deepseek", self.cfg, {"deepseek": "dummy"}, model="deepseek-v4-pro")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://api.deepseek.com/anthropic")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "dummy")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"], "DeepSeek V4 Pro")
        self.assertEqual(
            env["ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION"],
            "DeepSeek official Anthropic-compatible API",
        )
        self.assertEqual(self.mod.detect_provider("cc", self.cfg), "deepseek")

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
            {
                "aiwave_gemini_gcp": "gem-gcp-slot",
                "aiwave_gemini": "gem-slot",
                "aiwave_codex": "codex-slot",
            },
            model="",
        )

        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=https://api.ai-wave.org/gemini", gemini_env)
        self.assertIn("GEMINI_API_KEY=gem-gcp-slot", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-3.1-pro-preview", gemini_env)

        bashrc = self.cfg.bashrc.read_text(encoding="utf-8")
        self.assertIn('export GEMINI_API_KEY="gem-gcp-slot"', bashrc)

    def test_switch_gemini_cli_flames_updates_env_and_detects_flames(self):
        self.mod.switch_gemini_cli("flames", self.cfg, {"flames": "dummy"}, model="")

        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=https://www.flamescn.vip", gemini_env)
        self.assertIn("GEMINI_API_KEY=dummy", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-2.5-flash", gemini_env)
        self.assertEqual(self.mod.detect_provider("gemini", self.cfg), "flames")

        bashrc = self.cfg.bashrc.read_text(encoding="utf-8")
        self.assertIn('export GEMINI_API_KEY="dummy"', bashrc)

    def test_switch_gemini_provider_gemini_balance_updates_balance_env(self):
        self.init_gemini_balance_env()

        self.mod.switch_gemini_cli(
            "gemini-balance",
            self.cfg,
            {
                "gemini_balance_token": "sk-123456",
            },
            model="",
        )

        env_text = self.cfg.gemini_balance_env.read_text(encoding="utf-8")
        self.assertIn("BASE_URL=https://generativelanguage.googleapis.com/v1beta", env_text)
        self.assertIn('API_KEYS=["old-key"]', env_text)
        self.assertIn("TEST_MODEL=gemini-2.5-flash-lite", env_text)
        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=http://localhost:8000/gemini", gemini_env)
        self.assertIn("GEMINI_API_KEY=sk-123456", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-2.5-flash-lite", gemini_env)

    def test_switch_openclaw_aiwave_writes_gemini_provider(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw(
            "aiwave",
            self.cfg,
            {"aiwave_gemini_gcp": "gcp-dummy", "aiwave_gemini": "legacy-dummy"},
            profile="",
            model="",
        )

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "aiwave/gemini-3.1-pro-preview")

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["aiwave"]["baseUrl"], "https://api.ai-wave.org/gemini")
        self.assertEqual(models["providers"]["aiwave"]["api"], "google-generative-ai")
        self.assertEqual(models["providers"]["aiwave"]["apiKey"], "gcp-dummy")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["aiwave"], "aiwave:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "aiwave")

    def test_switch_droid_aiwave_uses_codex_key_slot(self):
        self.mod.switch_droid(
            "aiwave",
            self.cfg,
            {"aiwave_gemini_gcp": "gem-gcp-slot", "aiwave_gemini": "gem-slot", "aiwave_codex": "codex-slot"},
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
        self.assertEqual(keys["aiwave_gemini_gcp"], "gem-gcp-slot")
        self.assertEqual(keys["aiwave_gemini"], "gem-gcp-slot")
        self.assertEqual(keys["aiwave"], "legacy-slot")

    def test_switch_hermes_aiwave_updates_root_only_by_default(self):
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

        self.mod.switch_hermes(
            "aiwave",
            self.cfg,
            {"aiwave_gemini_gcp": "gem-gcp-key", "aiwave_gemini": "gem-key"},
            model="",
        )

        root_data = yaml.safe_load(root_cfg.read_text(encoding="utf-8"))
        self.assertEqual(root_data["model"]["provider"], "custom:aiwave")
        self.assertEqual(root_data["model"]["default"], "gemini-3.1-pro-preview")
        self.assertEqual(root_data["model"]["base_url"], "https://api.ai-wave.org/v1")
        self.assertEqual(root_data["model"]["api_key"], "gem-gcp-key")
        self.assertEqual(root_data["model"]["api_mode"], "chat_completions")
        root_entries = {entry["name"]: entry for entry in root_data["custom_providers"]}
        self.assertEqual(root_entries["aiwave"]["model"], "gemini-3.1-pro-preview")

        profile_data = yaml.safe_load(profile_cfg.read_text(encoding="utf-8"))
        self.assertEqual(profile_data["model"]["provider"], "custom:flames")
        self.assertNotIn("aiwave", {entry["name"] for entry in profile_data["custom_providers"]})

        self.assertEqual(self.mod.detect_provider("hermes", self.cfg), "aiwave")

    def test_switch_hermes_aiwave_updates_selected_profile_only(self):
        root_cfg = self.home / ".hermes/config.yaml"
        dev_cfg = self.home / ".hermes/profiles/dev/config.yaml"
        video_cfg = self.home / ".hermes/profiles/video-maker/config.yaml"
        for path in (root_cfg, dev_cfg, video_cfg):
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
                        "custom_providers": [],
                    },
                    sort_keys=False,
                ),
            )

        self.mod.switch_hermes(
            "aiwave",
            self.cfg,
            {"aiwave_gemini_gcp": "gem-gcp-key", "aiwave_gemini": "gem-key"},
            model="gemini-3.1-flash-lite-preview",
            profile_name="video-maker",
        )

        root_data = yaml.safe_load(root_cfg.read_text(encoding="utf-8"))
        dev_data = yaml.safe_load(dev_cfg.read_text(encoding="utf-8"))
        video_data = yaml.safe_load(video_cfg.read_text(encoding="utf-8"))

        self.assertEqual(root_data["model"]["provider"], "custom:flames")
        self.assertEqual(dev_data["model"]["provider"], "custom:flames")
        self.assertEqual(video_data["model"]["provider"], "custom:aiwave")
        self.assertEqual(video_data["model"]["default"], "gemini-3.1-flash-lite-preview")

    def test_switch_hermes_all_profiles_updates_all_profiles_not_root(self):
        root_cfg = self.home / ".hermes/config.yaml"
        dev_cfg = self.home / ".hermes/profiles/dev/config.yaml"
        video_cfg = self.home / ".hermes/profiles/video-maker/config.yaml"
        for path in (root_cfg, dev_cfg, video_cfg):
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
                        "custom_providers": [],
                    },
                    sort_keys=False,
                ),
            )

        self.mod.switch_hermes(
            "flames",
            self.cfg,
            {"flames": "flames-key"},
            model="gpt-5.4",
            all_profiles=True,
        )

        root_data = yaml.safe_load(root_cfg.read_text(encoding="utf-8"))
        dev_data = yaml.safe_load(dev_cfg.read_text(encoding="utf-8"))
        video_data = yaml.safe_load(video_cfg.read_text(encoding="utf-8"))

        self.assertEqual(root_data["model"]["api_key"], "old")
        self.assertEqual(dev_data["model"]["provider"], "custom:flames")
        self.assertEqual(video_data["model"]["provider"], "custom:flames")
        self.assertEqual(dev_data["model"]["api_key"], "flames-key")
        self.assertEqual(video_data["model"]["api_key"], "flames-key")

    def test_resolve_aiwave_gemini_key_prefers_gcp_slot(self):
        keys = {
            "aiwave_gemini_gcp": "gcp-slot",
            "aiwave_gemini": "legacy-slot",
            "aiwave": "fallback-slot",
        }
        self.assertEqual(self.mod.resolve_aiwave_gemini_key(keys), "gcp-slot")

        keys = {
            "aiwave_gemini_gcp": "",
            "aiwave_gemini": "legacy-slot",
            "aiwave": "fallback-slot",
        }
        self.assertEqual(self.mod.resolve_aiwave_gemini_key(keys), "legacy-slot")

    def test_model_validation_rejects_openclaw_icodeeasy_gpt_model(self):
        with self.assertRaises(self.mod.SwitchError):
            self.mod.validate_model_for_tool("openclaw", "gpt-5.4", "icodeeasy")

    def test_model_validation_allows_cc_flames_custom_models(self):
        self.mod.validate_model_for_tool("cc", "gpt-5.4", "flames")
        self.mod.validate_model_for_tool("cc", "deepseek-v4-pro", "flames")

    def test_model_validation_allows_cc_deepseek_models(self):
        self.mod.validate_model_for_tool("cc", "deepseek-v4-pro", "deepseek")

    def test_model_in_provider_accepts_icodeeasy_gpt_and_gemini(self):
        self.assertTrue(self.mod.model_in_provider("gpt-5.4", "icodeeasy"))
        self.assertTrue(self.mod.model_in_provider("gemini-2.5-flash", "icodeeasy"))

    def test_model_in_provider_accepts_flames_deepseek(self):
        self.assertTrue(self.mod.model_in_provider("deepseek-v4-pro", "flames"))

    def test_model_in_provider_accepts_deepseek_provider_models(self):
        self.assertTrue(self.mod.model_in_provider("deepseek-v4-pro", "deepseek"))

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
