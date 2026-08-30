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

    def assert_shell_rc_sources_env(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn('source "$HOME/.env"', text)

    def mock_codex_bundled_catalog(self, run) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps(
            {
                "models": [
                    {
                        "slug": slug,
                        "base_instructions": "You are Codex.",
                    }
                    for slug in (
                        "gpt-5.6-sol",
                        "gpt-5.6-terra",
                        "gpt-5.6-luna",
                        "gpt-5.4",
                    )
                ]
            }
        )
        run.return_value.stderr = ""

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

    def init_grok_config(self, text: str = "") -> None:
        self.write(
            self.cfg.grok_config,
            text
            or (
                "[ui]\n"
                'fork_secondary_model = "grok-build"\n'
            ),
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

    def test_parse_args_normalizes_claude_alias_to_cc(self):
        self.assertEqual(
            self.mod.parse_args(["claude", "deepseek"]),
            ("cc", "deepseek", ""),
        )
        self.assertEqual(
            self.mod.parse_args(["claude", "deepseek", "deepseek-v4-pro"]),
            ("cc", "deepseek", "@model:deepseek-v4-pro"),
        )

    def test_parse_args_supports_key_and_custom_provider_commands(self):
        self.assertEqual(
            self.mod.parse_args(["key", "set", "MY_RELAY_API_KEY", "secret"]),
            ("key-set", "MY_RELAY_API_KEY", "secret"),
        )

        action, provider, spec = self.mod.parse_args(
            [
                "provider",
                "add-openai",
                "myrelay",
                "https://relay.example.com/v1",
                "MY_RELAY_API_KEY",
                "gpt-5.4",
                "--disable-image-generation",
            ]
        )
        self.assertEqual(action, "provider-add-openai")
        self.assertEqual(provider, "myrelay")
        self.assertEqual(spec["env_key"], "MY_RELAY_API_KEY")
        self.assertFalse(spec["codex_features"]["image_generation"])

        action, provider, spec = self.mod.parse_args(
            [
                "provider",
                "add-anthropic",
                "myrelay",
                "https://relay.example.com/anthropic",
                "MY_RELAY_CC_API_KEY",
                "claude-sonnet-4-6",
                "--env",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            ]
        )
        self.assertEqual(action, "provider-add-anthropic")
        self.assertEqual(provider, "myrelay")
        self.assertEqual(spec["anthropic"]["env_key"], "MY_RELAY_CC_API_KEY")
        self.assertEqual(spec["anthropic"]["extra_env"]["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"], "1")

        action, provider, payload = self.mod.parse_args(
            ["provider", "export", "myrelay", "./myrelay.provider.json", "--with-secrets"]
        )
        self.assertEqual(action, "provider-export")
        self.assertEqual(provider, "myrelay")
        self.assertEqual(payload["path"], "./myrelay.provider.json")
        self.assertTrue(payload["with_secrets"])

        action, provider, payload = self.mod.parse_args(
            ["provider", "export-all", "./providers.bundle.json", "--with-secrets"]
        )
        self.assertEqual(action, "provider-export-all")
        self.assertEqual(provider, "")
        self.assertEqual(payload["path"], "./providers.bundle.json")
        self.assertTrue(payload["all"])

        action, provider, payload = self.mod.parse_args(
            ["provider", "import", "./providers.bundle.json", "--replace"]
        )
        self.assertEqual(action, "provider-import")
        self.assertEqual(provider, "./providers.bundle.json")
        self.assertTrue(payload["replace"])

        self.assertEqual(
            self.mod.parse_args(["list", "myrelay", "--online"], known_providers=["myrelay"]),
            ("list-online", "myrelay", ""),
        )
        self.assertEqual(
            self.mod.parse_args(["probe", "myrelay"], known_providers=["myrelay"]),
            ("probe-provider", "myrelay", ""),
        )
        self.assertEqual(
            self.mod.parse_args(["doctor", "myrelay"], known_providers=["myrelay"]),
            ("doctor-provider", "myrelay", ""),
        )

    def test_parse_provider_add_supports_model_discovery_options(self):
        action, provider, spec = self.mod.parse_args(
            [
                "provider",
                "add-openai",
                "anyrouter",
                "https://anyrouter.top/v1",
                "ANYROUTER_API_KEY",
                "gpt-5.5",
                "--models-url",
                "https://anyrouter.top/v1/models",
                "--models-auth",
                "bearer,anthropic",
            ]
        )
        self.assertEqual(action, "provider-add-openai")
        self.assertEqual(provider, "anyrouter")
        self.assertEqual(spec["openai"]["model_discovery"]["models_url"], "https://anyrouter.top/v1/models")
        self.assertEqual(spec["openai"]["model_discovery"]["auth_modes"], ["bearer", "anthropic"])
        self.assertIn("grok", spec["openai"]["tools"])

        action, provider, spec = self.mod.parse_args(
            [
                "provider",
                "add-anthropic",
                "anyrouter",
                "https://anyrouter.top",
                "ANYROUTER_API_KEY",
                "claude-opus-4-8",
                "--env",
                "ANTHROPIC_BETAS=context-1m-2025-08-07",
                "--models-auth",
                "bearer,anthropic,none",
            ]
        )
        self.assertEqual(action, "provider-add-anthropic")
        self.assertEqual(provider, "anyrouter")
        self.assertEqual(
            spec["anthropic"]["model_discovery"]["models_url"],
            "https://anyrouter.top/v1/models",
        )
        self.assertEqual(
            spec["anthropic"]["model_discovery"]["auth_modes"],
            ["bearer", "anthropic", "none"],
        )

    def test_sync_custom_provider_model_cache_discovers_models_and_updates_catalog(self):
        openai_spec = self.mod.normalize_custom_openai_provider_spec(
            "anyrouter",
            {
                "name": "anyrouter",
                "base_url": "https://anyrouter.top/v1",
                "env_key": "ANYROUTER_API_KEY",
                "default_model": "gpt-5.5",
                "tools": ["codex", "openclaw", "droid", "hermes"],
            },
        )
        anthropic_spec = self.mod.parse_provider_add_anthropic_args(
            [
                "anyrouter",
                "https://anyrouter.top",
                "ANYROUTER_API_KEY",
                "claude-opus-4-8",
                "--env",
                "ANTHROPIC_BETAS=context-1m-2025-08-07",
            ]
        )
        merged = self.mod.merge_custom_provider_record(openai_spec, anthropic_spec)

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {"data": [{"id": "claude-opus-4-8"}, {"id": "gpt-5.5"}, {"id": "gpt-5-codex"}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)) as mocked:
            synced, notes = self.mod.sync_custom_provider_model_cache(
                merged,
                {"ANYROUTER_API_KEY": "dummy"},
            )

        self.assertTrue(notes)
        self.assertEqual(
            synced["openai"]["available_models"],
            ["claude-opus-4-8", "gpt-5.5", "gpt-5-codex"],
        )
        self.assertEqual(
            synced["anthropic"]["available_models"],
            ["claude-opus-4-8", "gpt-5.5", "gpt-5-codex"],
        )
        self.assertEqual(synced["openai"]["model_discovery"]["last_sync_status"], "ok")
        self.assertEqual(synced["openai"]["model_discovery"]["last_sync_auth_mode"], "bearer")
        self.assertEqual(synced["anthropic"]["model_discovery"]["last_sync_auth_mode"], "bearer")
        self.assertEqual(mocked.call_count, 2)

        self.mod.save_custom_provider_store(self.cfg.custom_providers_file, {"providers": {"anyrouter": synced}})
        saved = self.mod.load_custom_provider_store(self.cfg.custom_providers_file)
        catalog = self.mod.provider_model_catalog(saved)
        self.assertIn("gpt-5-codex", catalog["providers"]["anyrouter"]["available_models"])
        self.assertIn(
            "claude-opus-4-8",
            catalog["providers"]["anyrouter"]["claude_code"]["available_models"],
        )

    def test_probe_custom_provider_uses_synced_configs(self):
        openai_spec = self.mod.normalize_custom_openai_provider_spec(
            "myrelay",
            {
                "name": "myrelay",
                "base_url": "https://relay.example.com/v1",
                "env_key": "MY_RELAY_API_KEY",
                "default_model": "gpt-5.4",
                "tools": ["codex"],
            },
        )
        anthropic_spec = self.mod.parse_provider_add_anthropic_args(
            [
                "myrelay",
                "https://relay.example.com",
                "MY_RELAY_API_KEY",
                "claude-sonnet-4-6",
                "--env",
                "ANTHROPIC_BETAS=context-1m-2025-08-07",
            ]
        )
        merged = self.mod.merge_custom_provider_record(openai_spec, anthropic_spec)
        self.mod.save_custom_provider_store(self.cfg.custom_providers_file, {"providers": {"myrelay": merged}})

        with patch.object(
            self.mod,
            "fetch_remote_model_catalog",
            return_value=(["gpt-5.4", "claude-sonnet-4-6"], "bearer", ""),
        ), patch.object(
            self.mod,
            "perform_json_http_request",
            return_value=(True, 200, '{"ok":true}'),
        ):
            self.mod.cmd_probe_provider(
                self.cfg,
                {"MY_RELAY_API_KEY": "dummy"},
                "myrelay",
                doctor=True,
            )

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

    def test_cmd_key_set_writes_credentials_env_and_shell_bootstrap(self):
        store = {}

        self.mod.cmd_key_set(self.cfg, store, "MY_RELAY_API_KEY", "sk-test-1234")

        saved = json.loads(self.cfg.cred_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["MY_RELAY_API_KEY"], "sk-test-1234")
        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export MY_RELAY_API_KEY="sk-test-1234"\n')
        self.assert_shell_rc_sources_env(self.cfg.bashrc)
        self.assert_shell_rc_sources_env(self.cfg.zshrc)

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
        self.assertIn('model = "gpt-5.6"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "flames")

    @patch("subprocess.run")
    def test_switch_codex_flames_accepts_deepseek_v4_flash(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="deepseek-v4-flash",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"flames_newapi"\s*$', text, re.M))
        self.assertIn('model = "deepseek-v4-flash"', text)
        self.assertIn('wire_api = "responses"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_flames_catalog}"',
            text,
        )
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "flames")

        catalog = json.loads(self.cfg.codex_flames_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model for model in catalog["models"] if model["slug"] == "deepseek-v4-flash"
        )
        self.assertEqual(deepseek["context_window"], 1_048_576)
        self.assertEqual(deepseek["max_context_window"], 1_048_576)

    @patch("subprocess.run")
    def test_switch_codex_flames_accepts_deepseek_v4_pro(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="deepseek-v4-pro",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"flames_newapi"\s*$', text, re.M))
        self.assertIn('model = "deepseek-v4-pro"', text)
        self.assertIn('wire_api = "responses"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_flames_catalog}"',
            text,
        )
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "flames")

        catalog = json.loads(self.cfg.codex_flames_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model for model in catalog["models"] if model["slug"] == "deepseek-v4-pro"
        )
        self.assertEqual(deepseek["context_window"], 1_048_576)
        self.assertEqual(deepseek["max_context_window"], 1_048_576)

    @patch("subprocess.run")
    def test_switch_codex_flames_accepts_deepseek_v4_flash_vision(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="deepseek-v4-flash-vision-exp",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "deepseek-v4-flash-vision-exp"', text)
        self.assertIn('wire_api = "responses"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_flames_catalog}"',
            text,
        )

        catalog = json.loads(self.cfg.codex_flames_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model
            for model in catalog["models"]
            if model["slug"] == "deepseek-v4-flash-vision-exp"
        )
        self.assertEqual(deepseek["input_modalities"], ["text", "image"])

    @patch("subprocess.run")
    def test_switch_codex_flames_glm_uses_grouped_catalog(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.cmd_model_override_add(
            self.cfg,
            "flames",
            "glm-5.3-flash",
            ["codex"],
            False,
        )

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="glm-5.3-flash",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "glm-5.3-flash"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_flames_catalog}"',
            text,
        )
        catalog = json.loads(self.cfg.codex_flames_catalog.read_text(encoding="utf-8"))
        slugs = [model["slug"] for model in catalog["models"]]
        self.assertEqual(
            slugs[:7],
            [
                "gpt-5.6-sol",
                "gpt-5.6-terra",
                "gpt-5.6-luna",
                "deepseek-v4-flash",
                "deepseek-v4-flash-vision-exp",
                "deepseek-v4-pro",
                "glm-5.3-flash",
            ],
        )


    @patch("subprocess.run")
    def test_switch_codex_flames_accepts_kimi_k3_with_existing_key_slot(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="moonshotai/kimi-k3",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model_provider = "flames_newapi"', text)
        self.assertIn('model = "moonshotai/kimi-k3"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_kimi_catalog}"',
            text,
        )

        catalog = json.loads(self.cfg.codex_kimi_catalog.read_text(encoding="utf-8"))
        kimi = next(
            model
            for model in catalog["models"]
            if model["slug"] == "moonshotai/kimi-k3"
        )
        self.assertEqual(kimi["context_window"], 1_048_576)
        self.assertEqual(kimi["max_context_window"], 1_048_576)
        self.assertEqual(kimi["input_modalities"], ["text", "image"])
        self.assertTrue(kimi["supports_parallel_tool_calls"])

    @patch("subprocess.run")
    def test_switch_codex_flames_default_restores_catalog_after_kimi(self, run):
        self.mock_codex_bundled_catalog(run)
        original_catalog = "/tmp/custom-codex-models.json"
        original_text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.cfg.cx_config.write_text(
            f'model_catalog_json = "{original_catalog}"\n' + original_text,
            encoding="utf-8",
        )

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="moonshotai/kimi-k3",
        )
        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6"', text)
        self.assertIn(f'model_catalog_json = "{original_catalog}"', text)
        self.assertNotIn(str(self.cfg.codex_kimi_catalog), text)

    @patch("subprocess.run")
    def test_switch_codex_flames_default_restores_catalog_after_deepseek(self, run):
        self.mock_codex_bundled_catalog(run)
        original_catalog = "/tmp/custom-codex-models.json"
        original_text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.cfg.cx_config.write_text(
            f'model_catalog_json = "{original_catalog}"\n' + original_text,
            encoding="utf-8",
        )

        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="deepseek-v4-flash",
        )
        self.mod.switch_codex(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6"', text)
        self.assertIn(f'model_catalog_json = "{original_catalog}"', text)
        self.assertNotIn(str(self.cfg.codex_deepseek_catalog), text)

    @patch("subprocess.run")
    def test_switch_codex_deepseek_writes_responses_provider_and_catalog(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex("deepseek", self.cfg, {"deepseek": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model_provider = "deepseek"', text)
        self.assertIn('model = "deepseek-v4-flash"', text)
        self.assertIn('[model_providers.deepseek]', text)
        self.assertIn('base_url = "https://api.deepseek.com"', text)
        self.assertIn('wire_api = "responses"', text)
        self.assertIn('env_key = "DEEPSEEK_API_KEY"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_deepseek_catalog}"',
            text,
        )
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "deepseek")
        self.assertEqual(
            (self.home / ".env").read_text(encoding="utf-8"),
            'export DEEPSEEK_API_KEY="dummy"\n',
        )

        catalog = json.loads(self.cfg.codex_deepseek_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model for model in catalog["models"] if model["slug"] == "deepseek-v4-flash"
        )
        self.assertEqual(deepseek["context_window"], 1_048_576)
        self.assertEqual(deepseek["input_modalities"], ["text"])
        self.assertEqual(deepseek["supported_reasoning_levels"][-1]["effort"], "max")
        self.assertEqual(deepseek["base_instructions"], "You are Codex.")

    @patch("subprocess.run")
    def test_switch_codex_deepseek_writes_v4_pro(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex("deepseek", self.cfg, {"deepseek": "dummy"}, model="deepseek-v4-pro")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model_provider = "deepseek"', text)
        self.assertIn('model = "deepseek-v4-pro"', text)
        self.assertIn('[model_providers.deepseek]', text)
        self.assertIn('base_url = "https://api.deepseek.com"', text)
        self.assertIn('wire_api = "responses"', text)
        self.assertIn('env_key = "DEEPSEEK_API_KEY"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_deepseek_catalog}"',
            text,
        )

        catalog = json.loads(self.cfg.codex_deepseek_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model for model in catalog["models"] if model["slug"] == "deepseek-v4-pro"
        )
        self.assertEqual(deepseek["context_window"], 1_048_576)
        self.assertEqual(deepseek["input_modalities"], ["text"])
        self.assertEqual(deepseek["base_instructions"], "You are Codex.")

    @patch("subprocess.run")
    def test_switch_codex_deepseek_writes_v4_flash_vision_catalog(self, run):
        self.mock_codex_bundled_catalog(run)

        self.mod.switch_codex(
            "deepseek",
            self.cfg,
            {"deepseek": "dummy"},
            model="deepseek-v4-flash-vision-exp",
        )

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "deepseek-v4-flash-vision-exp"', text)
        self.assertIn('model_provider = "deepseek"', text)

        catalog = json.loads(self.cfg.codex_deepseek_catalog.read_text(encoding="utf-8"))
        deepseek = next(
            model
            for model in catalog["models"]
            if model["slug"] == "deepseek-v4-flash-vision-exp"
        )
        self.assertEqual(deepseek["input_modalities"], ["text", "image"])

    @patch("subprocess.run")
    def test_registered_deepseek_model_can_be_used_without_code_change(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.cmd_model_override_add(
            self.cfg,
            "deepseek",
            "deepseek-v4-flash-next",
            ["codex"],
            True,
        )

        self.mod.switch_codex(
            "deepseek",
            self.cfg,
            {"deepseek": "dummy"},
            model="deepseek-v4-flash-next",
        )

        catalog = json.loads(self.cfg.codex_deepseek_catalog.read_text(encoding="utf-8"))
        model = next(item for item in catalog["models"] if item["slug"] == "deepseek-v4-flash-next")
        self.assertEqual(model["input_modalities"], ["text", "image"])

    def test_model_override_supports_other_builtin_provider_and_tool_scope(self):
        self.mod.cmd_model_override_add(
            self.cfg,
            "xingyun",
            "gpt-next",
            ["codex", "openclaw"],
            False,
        )

        self.mod.validate_model_for_tool(
            "codex",
            "gpt-next",
            "xingyun",
            cfg=self.cfg,
        )
        with self.assertRaises(self.mod.SwitchError):
            self.mod.validate_model_for_tool(
                "cc",
                "gpt-next",
                "xingyun",
                cfg=self.cfg,
            )

        listed = self.mod.get_provider_models("xingyun", cfg=self.cfg)
        self.assertIn("gpt-next", listed["gpt"])

    def test_model_override_all_expands_to_provider_tools(self):
        self.mod.cmd_model_override_add(
            self.cfg,
            "flames",
            "universal-next",
            ["all"],
            False,
        )

        entry = self.mod.model_override_spec(self.cfg, "flames", "universal-next")
        self.assertEqual(
            entry["tools"],
            list(self.mod.BUILTIN_PROVIDER_TOOLS["flames"]),
        )

    def test_model_override_rejects_tool_not_supported_by_provider(self):
        with self.assertRaisesRegex(
            self.mod.SwitchError,
            "does not support model overrides for: grok",
        ):
            self.mod.cmd_model_override_add(
                self.cfg,
                "deepseek",
                "deepseek-v4-next",
                ["grok"],
                False,
            )

    def test_registered_model_is_listed_for_provider_without_builtin_catalog(self):
        self.mod.cmd_model_override_add(
            self.cfg,
            "openai",
            "gpt-next",
            ["codex"],
            False,
        )

        listed = self.mod.get_provider_models("openai", cfg=self.cfg)
        self.assertIn("gpt-next", listed["gpt"])

    @patch("subprocess.run")
    def test_registered_openrouter_model_switches_codex(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.cmd_model_override_add(
            self.cfg,
            "openrouter",
            "vendor/model-next",
            ["codex"],
            False,
        )

        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="vendor/model-next",
        )
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "vendor/model-next"', text)
        self.assertIn('model_provider = "openrouter"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_openrouter_catalog}"',
            text,
        )
        catalog = json.loads(self.cfg.codex_openrouter_catalog.read_text(encoding="utf-8"))
        slugs = [model["slug"] for model in catalog["models"]]
        self.assertIn("vendor/model-next", slugs)
        self.assertIn("nvidia/nemotron-3.5-lightning:free", slugs)
        self.assertIn("deepseek/deepseek-v4-flash", slugs)

    def test_registered_openrouter_model_switches_droid(self):
        self.mod.cmd_model_override_add(
            self.cfg,
            "openrouter",
            "vendor/model-next",
            ["droid"],
            False,
        )

        self.mod.switch_droid(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="vendor/model-next",
        )
        settings = json.loads(self.cfg.factory_settings.read_text(encoding="utf-8"))
        self.assertEqual(settings["customModels"][0]["model"], "vendor/model-next")

    def test_registered_openrouter_model_switches_openclaw(self):
        self.init_openclaw_files()
        self.mod.cmd_model_override_add(
            self.cfg,
            "openrouter",
            "vendor/model-next",
            ["openclaw"],
            True,
        )

        self.mod.switch_openclaw(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="vendor/model-next",
        )
        config = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(
            config["agents"]["defaults"]["model"]["primary"],
            "openrouter/vendor/model-next",
        )
        registered = next(
            item
            for item in config["models"]["providers"]["openrouter"]["models"]
            if item["id"] == "vendor/model-next"
        )
        self.assertEqual(registered["input"], ["text", "image"])

    @patch("subprocess.run")
    def test_openrouter_alias_ds_switches_codex(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="ds",
        )
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "deepseek/deepseek-v4-flash"', text)
        self.assertIn('model_provider = "openrouter"', text)

    @patch("subprocess.run")
    def test_openrouter_alias_gpt_switches_codex(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="gpt",
        )
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "openai/gpt-5.4"', text)

    @patch("subprocess.run")
    def test_openrouter_allows_claude_on_codex(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.validate_model_for_tool(
            "codex",
            "anthropic/claude-sonnet-5",
            "openrouter",
        )
        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="claude",
        )
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "anthropic/claude-sonnet-5"', text)

    @patch("subprocess.run")
    def test_switch_codex_openrouter_writes_multi_model_catalog(self, run):
        self.mock_codex_bundled_catalog(run)
        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="nemotron",
        )
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "nvidia/nemotron-3.5-lightning:free"', text)
        self.assertIn(
            f'model_catalog_json = "{self.cfg.codex_openrouter_catalog}"',
            text,
        )
        catalog = json.loads(self.cfg.codex_openrouter_catalog.read_text(encoding="utf-8"))
        slugs = [model["slug"] for model in catalog["models"]]
        for expected in (
            "nvidia/nemotron-3.5-lightning:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "z-ai/glm-5.2:free",
            "deepseek/deepseek-v4-flash",
            "openai/gpt-5.4",
            "anthropic/claude-sonnet-5",
        ):
            self.assertIn(expected, slugs)
        self.assertGreaterEqual(len(slugs), 10)
        self.assertNotIn("google/lyria-3-pro-preview", slugs)

    @patch("subprocess.run")
    def test_switch_codex_flames_restores_catalog_after_openrouter(self, run):
        self.mock_codex_bundled_catalog(run)
        original_catalog = "/tmp/custom-codex-models.json"
        original_text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.cfg.cx_config.write_text(
            f'model_catalog_json = "{original_catalog}"\n' + original_text,
            encoding="utf-8",
        )

        self.mod.switch_codex(
            "openrouter",
            self.cfg,
            {"openrouter": "dummy"},
            model="nemotron",
        )
        self.mod.switch_codex("flames", self.cfg, {"flames": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn(f'model_catalog_json = "{original_catalog}"', text)
        self.assertNotIn(str(self.cfg.codex_openrouter_catalog), text)

    def test_openrouter_alias_resolution(self):
        self.assertEqual(
            self.mod.resolve_openrouter_model("ds"),
            "deepseek/deepseek-v4-flash",
        )
        self.assertEqual(
            self.mod.resolve_openrouter_model("free"),
            "openrouter/free",
        )
        self.assertTrue(self.mod.is_openrouter_free_model("nvidia/nemotron-3.5-lightning:free"))
        self.assertFalse(self.mod.is_openrouter_free_model("deepseek/deepseek-v4-flash"))

    def test_openrouter_codex_third_arg_is_model_not_profile(self):
        tool, provider, profile = self.mod.parse_args(
            ["codex", "openrouter", "ds"],
            known_providers=[],
        )
        self.assertEqual((tool, provider, profile), ("codex", "openrouter", "@model:ds"))

    def test_registered_xingyun_model_switches_codex(self):
        self.mod.cmd_model_override_add(
            self.cfg,
            "xingyun",
            "gpt-next",
            ["codex"],
            False,
        )
        self.mod.switch_codex("xingyun", self.cfg, {"xingyun": "dummy"}, model="gpt-next")
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn('model = "gpt-next"', text)
        self.assertIn('model_provider = "xingyun"', text)

    @patch("subprocess.run")
    def test_switch_codex_restores_previous_catalog_after_deepseek(self, run):
        self.mock_codex_bundled_catalog(run)
        original_catalog = "/tmp/custom-codex-models.json"
        original_text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.cfg.cx_config.write_text(
            f'model_catalog_json = "{original_catalog}"\n' + original_text,
            encoding="utf-8",
        )

        self.mod.switch_codex("deepseek", self.cfg, {"deepseek": "dummy"}, model="")
        self.mod.switch_codex("flames", self.cfg, {"flames": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIn(f'model_catalog_json = "{original_catalog}"', text)
        self.assertNotIn(str(self.cfg.codex_deepseek_catalog), text)

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

    def test_switch_cc_flames_accepts_claude_sonnet_5(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc("flames", self.cfg, {"flames": "dummy"}, model="claude-sonnet-5")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "claude-sonnet-5")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION"], "claude-sonnet-5")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"], "Claude Sonnet 5")

    def test_switch_cc_flames_accepts_deepseek_v4_flash_vision(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="deepseek-v4-flash-vision-exp",
        )

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "deepseek-v4-flash-vision-exp")
        self.assertEqual(
            env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"],
            "DeepSeek V4 Flash Vision (Experimental)",
        )

    def test_switch_cc_flames_kimi_k3_pins_main_helper_and_subagent_models(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc(
            "flames",
            self.cfg,
            {"flames": "dummy"},
            model="moonshotai/kimi-k3",
        )

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "moonshotai/kimi-k3")
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://www.flamescn.vip")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "dummy")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"], "Kimi K3")
        for alias_key in self.mod.CC_MODEL_ALIAS_ENV_KEYS:
            self.assertEqual(env[alias_key], "moonshotai/kimi-k3")

    def test_switch_cc_flames_defaults_to_claude_opus_48(self):
        self.init_cc_settings(
            model="claude-haiku-4-5-20251001",
            env={
                "ANTHROPIC_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
                "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
            },
        )

        self.mod.switch_cc("flames", self.cfg, {"flames": "dummy"}, model="")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "claude-opus-4-8")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION"], "claude-opus-4-8")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"], "Claude Opus 4.8")
        self.assertNotIn("ANTHROPIC_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_OPUS_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_SONNET_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_HAIKU_MODEL", env)
        self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", env)

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
        self.assertEqual(env["ANTHROPIC_MODEL"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_DEFAULT_OPUS_MODEL"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_DEFAULT_SONNET_MODEL"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_DEFAULT_HAIKU_MODEL"], "deepseek-v4-flash")
        self.assertEqual(env["CLAUDE_CODE_SUBAGENT_MODEL"], "deepseek-v4-flash")
        self.assertEqual(self.mod.detect_provider("cc", self.cfg), "deepseek")

    def test_switch_cc_deepseek_defaults_to_v4_pro(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc("deepseek", self.cfg, {"deepseek": "dummy"}, model="")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_CUSTOM_MODEL_OPTION"], "deepseek-v4-pro")
        self.assertEqual(env["ANTHROPIC_DEFAULT_HAIKU_MODEL"], "deepseek-v4-flash")

    def test_switch_cc_deepseek_accepts_v4_flash_vision(self):
        self.init_cc_settings(model="claude-sonnet-4-6")

        self.mod.switch_cc(
            "deepseek",
            self.cfg,
            {"deepseek": "dummy"},
            model="deepseek-v4-flash-vision-exp",
        )

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertEqual(data["model"], "deepseek-v4-flash-vision-exp")
        self.assertEqual(
            env["ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"],
            "DeepSeek V4 Flash Vision (Experimental)",
        )

    def test_switch_cc_non_deepseek_clears_stale_model_alias_env(self):
        self.init_cc_settings(
            model="deepseek-v4-pro",
            env={
                "ANTHROPIC_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
                "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
                "ANTHROPIC_CUSTOM_MODEL_OPTION": "deepseek-v4-pro",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_NAME": "DeepSeek V4 Pro",
                "ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION": "DeepSeek official Anthropic-compatible API",
            },
        )

        self.mod.switch_cc("quotio", self.cfg, {"quotio": "dummy"}, model="")

        data = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        env = data["env"]
        self.assertNotIn("ANTHROPIC_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_OPUS_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_SONNET_MODEL", env)
        self.assertNotIn("ANTHROPIC_DEFAULT_HAIKU_MODEL", env)
        self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", env)
        self.assertNotIn("ANTHROPIC_CUSTOM_MODEL_OPTION", env)

    def test_switch_codex_icodeeasy_writes_provider_block_and_detects_icodeeasy(self):
        self.mod.switch_codex("icodeeasy", self.cfg, {"icodeeasy": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"icodeeasy"\s*$', text, re.M))
        self.assertIn('model = "gpt-5.4"', text)
        self.assertIn("[model_providers.icodeeasy]", text)
        self.assertIn('base_url = "https://api.icodeeasy.cc/v1"', text)
        self.assertIn('env_key = "ICODEEASY_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "icodeeasy")

    def test_switch_codex_molifang_writes_gpt55_provider_block_and_detects(self):
        self.mod.switch_codex("molifang", self.cfg, {"molifang": "dummy"}, model="")

        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"molifang"\s*$', text, re.M))
        self.assertIn('model = "gpt-5.5"', text)
        self.assertRegex(text, r"(?ms)^\[features\]\n(?:.*\n)*image_generation = false$")
        self.assertIn("[model_providers.molifang]", text)
        self.assertIn('base_url = "https://molifangapi.xyz/v1"', text)
        self.assertIn('env_key = "MOLIFANG_API_KEY"', text)
        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export MOLIFANG_API_KEY="dummy"\n')
        self.assert_shell_rc_sources_env(self.cfg.zshrc)
        self.assert_shell_rc_sources_env(self.cfg.bashrc)
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "molifang")

    def test_switch_openclaw_molifang_writes_provider_and_auth_store(self):
        self.init_openclaw_files()

        self.mod.switch_openclaw("molifang", self.cfg, {"molifang": "dummy"}, profile="", model="")

        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "molifang/gpt-5.5")

        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["molifang"]["baseUrl"], "https://molifangapi.xyz/v1")
        self.assertEqual(models["providers"]["molifang"]["api"], "openai-completions")
        self.assertEqual(models["providers"]["molifang"]["apiKey"], "dummy")
        self.assertEqual(models["providers"]["molifang"]["models"][0]["id"], "gpt-5.5")

        auth = json.loads(self.cfg.oc_auth.read_text(encoding="utf-8"))
        self.assertEqual(auth["molifang"]["key"], "dummy")

        auth_profiles = json.loads(self.cfg.oc_auth_profiles.read_text(encoding="utf-8"))
        self.assertEqual(auth_profiles["lastGood"]["molifang"], "molifang:manual")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "molifang")

    def test_switch_droid_molifang_writes_custom_model(self):
        self.mod.switch_droid("molifang", self.cfg, {"molifang": "dummy"}, profile="", model="")

        data = json.loads(self.cfg.factory_settings.read_text(encoding="utf-8"))
        custom = data["customModels"][0]
        self.assertEqual(custom["model"], "gpt-5.5")
        self.assertEqual(custom["displayName"], "Molifang gpt-5.5")
        self.assertEqual(custom["baseUrl"], "https://molifangapi.xyz/v1")
        self.assertEqual(custom["apiKey"], "dummy")
        self.assertEqual(data["sessionDefaultSettings"]["model"], "custom:Molifang-gpt-5.5-0")
        self.assertEqual(self.mod.detect_provider("droid", self.cfg), "molifang")

    def test_cmd_provider_add_openai_and_switch_custom_provider_surfaces(self):
        spec = self.mod.normalize_custom_openai_provider_spec(
            "myrelay",
            {
                "name": "myrelay",
                "base_url": "https://relay.example.com/v1",
                "env_key": "MY_RELAY_API_KEY",
                "default_model": "gpt-5.4",
                "tools": ["codex", "openclaw", "droid", "hermes", "grok"],
                "openclaw_api": "openai-completions",
                "hermes_api_mode": "codex_responses",
                "codex_features": {"image_generation": False},
            },
        )
        self.mod.cmd_provider_add_openai(self.cfg, spec)
        anthropic_spec = self.mod.parse_provider_add_anthropic_args(
            [
                "myrelay",
                "https://relay.example.com/anthropic",
                "MY_RELAY_CC_API_KEY",
                "claude-sonnet-4-6",
                "--env",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            ]
        )
        self.mod.cmd_provider_add_anthropic(self.cfg, anthropic_spec)

        saved = self.mod.load_custom_provider_store(self.cfg.custom_providers_file)
        self.assertEqual(saved["providers"]["myrelay"]["env_key"], "MY_RELAY_API_KEY")
        self.assertEqual(saved["providers"]["myrelay"]["anthropic"]["env_key"], "MY_RELAY_CC_API_KEY")
        self.assertIn("cc", saved["providers"]["myrelay"]["tools"])

        self.mod.cmd_key_set(self.cfg, {}, "MY_RELAY_API_KEY", "dummy")
        self.mod.cmd_key_set(self.cfg, {}, "MY_RELAY_CC_API_KEY", "dummy-cc")

        self.init_cc_settings(model="claude-opus-4-6")
        self.mod.switch_custom_cc_provider(saved["providers"]["myrelay"], self.cfg, {"MY_RELAY_CC_API_KEY": "dummy-cc"}, model="")
        cc = json.loads(self.cfg.cc_settings.read_text(encoding="utf-8"))
        self.assertEqual(cc["model"], "claude-sonnet-4-6")
        self.assertEqual(cc["env"]["ANTHROPIC_BASE_URL"], "https://relay.example.com/anthropic")
        self.assertEqual(cc["env"]["ANTHROPIC_AUTH_TOKEN"], "dummy-cc")
        self.assertEqual(cc["env"]["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"], "1")
        self.assertEqual(self.mod.detect_provider("cc", self.cfg), "myrelay")

        self.mod.switch_custom_codex_provider(spec, self.cfg, {"MY_RELAY_API_KEY": "dummy"}, model="")
        text = self.cfg.cx_config.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r'^\s*model_provider\s*=\s*"myrelay"\s*$', text, re.M))
        self.assertIn('base_url = "https://relay.example.com/v1"', text)
        self.assertIn('env_key = "MY_RELAY_API_KEY"', text)
        self.assertRegex(text, r"(?ms)^\[features\]\n(?:.*\n)*image_generation = false$")
        self.assertEqual(self.mod.detect_provider("codex", self.cfg), "myrelay")

        self.init_openclaw_files()
        self.mod.switch_custom_openclaw_provider(spec, self.cfg, {"MY_RELAY_API_KEY": "dummy"}, model="")
        oc = json.loads(self.cfg.oc_config.read_text(encoding="utf-8"))
        self.assertEqual(oc["agents"]["defaults"]["model"]["primary"], "myrelay/gpt-5.4")
        models = json.loads(self.cfg.oc_models.read_text(encoding="utf-8"))
        self.assertEqual(models["providers"]["myrelay"]["baseUrl"], "https://relay.example.com/v1")
        self.assertEqual(models["providers"]["myrelay"]["api"], "openai-completions")
        self.assertEqual(models["providers"]["myrelay"]["apiKey"], "dummy")
        self.assertEqual(self.mod.detect_provider("openclaw", self.cfg), "myrelay")

        self.mod.switch_custom_droid_provider(spec, self.cfg, {"MY_RELAY_API_KEY": "dummy"}, model="")
        droid = json.loads(self.cfg.factory_settings.read_text(encoding="utf-8"))
        self.assertEqual(droid["customModels"][0]["baseUrl"], "https://relay.example.com/v1")
        self.assertEqual(droid["customModels"][0]["apiKey"], "dummy")
        self.assertEqual(self.mod.detect_provider("droid", self.cfg), "myrelay")

        self.write(
            self.cfg.hermes_config,
            yaml.safe_dump(
                {
                    "model": {
                        "default": "gpt-5.4",
                        "provider": "custom:flames",
                        "base_url": "https://www.flamescn.vip/v1",
                        "api_key": "old",
                        "api_mode": "codex_responses",
                    }
                },
                sort_keys=False,
            ),
        )
        self.mod.switch_custom_hermes_provider(spec, self.cfg, {"MY_RELAY_API_KEY": "dummy"}, model="")
        hermes = yaml.safe_load(self.cfg.hermes_config.read_text(encoding="utf-8"))
        self.assertEqual(hermes["model"]["provider"], "custom:myrelay")
        self.assertEqual(hermes["model"]["base_url"], "https://relay.example.com/v1")
        self.assertEqual(hermes["model"]["api_key"], "dummy")
        self.assertEqual(self.mod.detect_provider("hermes", self.cfg), "myrelay")

        self.init_grok_config()
        self.mod.switch_custom_grok_provider(spec, self.cfg, {"MY_RELAY_API_KEY": "dummy"}, model="gpt-5.4")
        grok_text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertIn('default = "gpt-5.4"', grok_text)
        self.assertIn('[model."gpt-5.4"]', grok_text)
        self.assertIn('model = "gpt-5.4"', grok_text)
        self.assertIn('base_url = "https://relay.example.com/v1"', grok_text)
        self.assertIn('env_key = "MY_RELAY_API_KEY"', grok_text)
        self.assertEqual(self.mod.detect_provider("grok", self.cfg), "myrelay")
        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "gpt-5.4")

        catalog = self.mod.provider_model_catalog(saved)
        self.assertEqual(catalog["providers"]["myrelay"]["claude_code"]["default_model"], "claude-sonnet-4-6")

    def test_cmd_provider_export_import_roundtrip_with_secrets(self):
        openai_spec = self.mod.normalize_custom_openai_provider_spec(
            "myrelay",
            {
                "name": "myrelay",
                "base_url": "https://relay.example.com/v1",
                "env_key": "MY_RELAY_API_KEY",
                "default_model": "gpt-5.4",
                "tools": ["codex", "openclaw", "droid", "hermes"],
                "openclaw_api": "openai-completions",
                "hermes_api_mode": "codex_responses",
            },
        )
        anthropic_spec = self.mod.parse_provider_add_anthropic_args(
            [
                "myrelay",
                "https://relay.example.com/anthropic",
                "MY_RELAY_CC_API_KEY",
                "claude-sonnet-4-6",
                "--env",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            ]
        )
        self.mod.cmd_provider_add_openai(self.cfg, openai_spec)
        self.mod.cmd_provider_add_anthropic(self.cfg, anthropic_spec)

        store = {}
        self.mod.cmd_key_set(self.cfg, store, "MY_RELAY_API_KEY", "dummy")
        self.mod.cmd_key_set(self.cfg, store, "MY_RELAY_CC_API_KEY", "dummy-cc")

        export_path = self.home / "providers.bundle.json"
        self.mod.cmd_provider_export(
            self.cfg,
            store,
            out_path=str(export_path),
            include_secrets=True,
            export_all=True,
        )

        exported = json.loads(export_path.read_text(encoding="utf-8"))
        self.assertEqual(exported["format"], "switch-api/provider-bundle")
        self.assertIn("myrelay", exported["providers"])
        self.assertEqual(exported["env_values"]["MY_RELAY_API_KEY"], "dummy")
        self.assertEqual(exported["env_values"]["MY_RELAY_CC_API_KEY"], "dummy-cc")

        with tempfile.TemporaryDirectory() as tempdir2:
            home2 = Path(tempdir2)
            cfg2 = self.mod.Config(home2)
            store2 = {}
            self.mod.cmd_provider_import(cfg2, store2, str(export_path), replace=False)

            saved2 = self.mod.load_custom_provider_store(cfg2.custom_providers_file)
            self.assertIn("myrelay", saved2["providers"])
            self.assertIn("cc", saved2["providers"]["myrelay"]["tools"])

            creds2 = json.loads(cfg2.cred_file.read_text(encoding="utf-8"))
            self.assertEqual(creds2["MY_RELAY_API_KEY"], "dummy")
            self.assertEqual(creds2["MY_RELAY_CC_API_KEY"], "dummy-cc")
            self.assertEqual(store2["MY_RELAY_API_KEY"], "dummy")
            self.assertEqual(store2["MY_RELAY_CC_API_KEY"], "dummy-cc")

            env_text = (home2 / ".env").read_text(encoding="utf-8")
            self.assertIn('export MY_RELAY_API_KEY="dummy"', env_text)
            self.assertIn('export MY_RELAY_CC_API_KEY="dummy-cc"', env_text)
            self.assert_shell_rc_sources_env(cfg2.bashrc)
            self.assert_shell_rc_sources_env(cfg2.zshrc)

    def test_cmd_provider_import_replace_overwrites_provider_store(self):
        bundle_path = self.home / "providers.bundle.json"
        bundle_path.write_text(
            json.dumps(
                {
                    "format": "switch-api/provider-bundle",
                    "schema_version": 1,
                    "providers": {
                        "myrelay": {
                            "name": "myrelay",
                            "openai": {
                                "base_url": "https://relay.example.com/v1",
                                "env_key": "MY_RELAY_API_KEY",
                                "default_model": "gpt-5.4",
                                "tools": ["codex"],
                                "openclaw_api": "openai-completions",
                                "hermes_api_mode": "codex_responses",
                                "codex_wire_api": "responses",
                                "codex_features": {},
                            }
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        self.mod.cmd_provider_add_openai(
            self.cfg,
            self.mod.normalize_custom_openai_provider_spec(
                "oldrelay",
                {
                    "name": "oldrelay",
                    "base_url": "https://old.example.com/v1",
                    "env_key": "OLD_RELAY_API_KEY",
                    "default_model": "gpt-5.4",
                    "tools": ["codex"],
                    "openclaw_api": "openai-completions",
                    "hermes_api_mode": "codex_responses",
                },
            ),
        )

        self.mod.cmd_provider_import(self.cfg, {}, str(bundle_path), replace=True)
        saved = self.mod.load_custom_provider_store(self.cfg.custom_providers_file)
        self.assertEqual(set(saved["providers"]), {"myrelay"})

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

        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export GEMINI_API_KEY="dummy"\n')
        self.assert_shell_rc_sources_env(self.cfg.bashrc)

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

        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export GEMINI_API_KEY="gem-gcp-slot"\n')
        self.assert_shell_rc_sources_env(self.cfg.bashrc)

    def test_switch_gemini_cli_flames_updates_env_and_detects_flames(self):
        self.mod.switch_gemini_cli("flames", self.cfg, {"flames": "dummy"}, model="")

        gemini_env = self.cfg.gemini_env.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_GEMINI_BASE_URL=https://www.flamescn.vip", gemini_env)
        self.assertIn("GEMINI_API_KEY=dummy", gemini_env)
        self.assertIn("GEMINI_MODEL=gemini-3.5-flash", gemini_env)
        self.assertEqual(self.mod.detect_provider("gemini", self.cfg), "flames")

        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export GEMINI_API_KEY="dummy"\n')
        self.assert_shell_rc_sources_env(self.cfg.bashrc)
        self.assert_shell_rc_sources_env(self.cfg.zshrc)

        settings = json.loads((self.home / ".gemini/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["security"]["auth"]["selectedType"], "gemini-api-key")
        self.assertEqual(settings["model"]["name"], "gemini-3.5-flash")
        self.assertTrue(settings["experimental"]["dynamicModelConfiguration"])
        self.assertIn("gemini-3.5-flash", settings["modelConfigs"]["modelDefinitions"])

    def test_switch_grok_flames_writes_managed_model_and_detects_flames(self):
        self.init_grok_config()

        self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"}, model="grok-4.5")

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertIn('default = "grok-4.5"', text)
        self.assertIn('[model."grok-4.5"]', text)
        self.assertIn('model = "grok-4.5"', text)
        self.assertIn('base_url = "https://www.flamescn.vip/v1"', text)
        self.assertIn('api_backend = "responses"', text)
        self.assertIn('env_key = "FLAMES_API_KEY"', text)
        self.assertEqual(self.mod.detect_provider("grok", self.cfg), "flames")
        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "grok-4.5")
        self.assertEqual((self.home / ".env").read_text(encoding="utf-8"), 'export FLAMES_API_KEY="dummy"\n')
        self.assert_shell_rc_sources_env(self.cfg.bashrc)
        self.assert_shell_rc_sources_env(self.cfg.zshrc)

    def test_switch_grok_flames_without_explicit_model_prefers_discovered_grok(self):
        self.init_grok_config()

        with patch.object(
            self.mod,
            "fetch_remote_model_catalog",
            return_value=(["gpt-5.4", "grok-4.5"], "bearer", ""),
        ):
            self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"})

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertIn('model = "grok-4.5"', text)
        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "grok-4.5")

    def test_switch_grok_flames_stashes_cached_xai_login(self):
        self.init_grok_config()
        self.write_json(self.cfg.grok_auth, {"auth_mode": "session", "access_token": "secret"})

        self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"}, model="grok-4.5")

        self.assertFalse(self.cfg.grok_auth.exists())
        self.assertTrue(self.cfg.grok_auth_relay_backup.exists())
        self.assertEqual(
            json.loads(self.cfg.grok_auth_relay_backup.read_text(encoding="utf-8"))["access_token"],
            "secret",
        )

    def test_switch_grok_flames_stashes_login_even_when_route_is_already_active(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "grok-4.5"\n\n'
                '[model."grok-4.5"]\n'
                'model = "grok-4.5"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'description = "Managed by switch-api (Flames NewAPI)"\n'
                'env_key = "FLAMES_API_KEY"\n'
                'api_backend = "responses"\n'
            )
        )
        self.write_json(self.cfg.grok_auth, {"auth_mode": "session", "access_token": "secret"})

        self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"}, model="grok-4.5")

        self.assertFalse(self.cfg.grok_auth.exists())
        self.assertTrue(self.cfg.grok_auth_relay_backup.exists())

    def test_switch_grok_flames_refreshes_legacy_model_when_provider_already_matches(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "switch-api-provider"\n\n'
                "[model.switch-api-provider]\n"
                'model = "grok-build-0.1"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'env_key = "FLAMES_API_KEY"\n'
                'api_backend = "responses"\n'
            )
        )

        with patch.object(
            self.mod,
            "fetch_remote_model_catalog",
            return_value=(["grok-4.5"], "bearer", ""),
        ):
            self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"})

        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "grok-4.5")

    def test_switch_grok_flames_is_idempotent_and_keeps_valid_toml(self):
        import tomllib

        self.init_grok_config()
        keys = {"flames": "dummy"}

        self.mod.switch_grok("flames", self.cfg, keys, model="grok-4.5")
        first = self.cfg.grok_config.read_text(encoding="utf-8")
        self.mod.switch_grok("flames", self.cfg, keys, model="grok-4.5")
        second = self.cfg.grok_config.read_text(encoding="utf-8")

        self.assertEqual(second, first)
        self.assertEqual(second.count('[model."grok-4.5"]'), 1)
        parsed = tomllib.loads(second)
        self.assertEqual(parsed["models"]["default"], "grok-4.5")
        self.assertEqual(parsed["model"]["grok-4.5"]["model"], "grok-4.5")

    def test_switch_grok_flames_repairs_legacy_duplicate_managed_table(self):
        import tomllib

        self.init_grok_config(
            (
                "[models]\n"
                'default = "switch-api-provider"[model.switch-api-provider]\n'
                'model = "grok-build-0.1"\n'
                'base_url = "https://www.flamescn.vip/v1"\n\n'
                'default = "switch-api-provider"\n'
                "[model.switch-api-provider]\n"
                'model = "grok-build-0.1"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
            )
        )

        with patch.object(
            self.mod,
            "fetch_remote_model_catalog",
            return_value=(["gpt-5.4", "grok-4.5"], "bearer", ""),
        ):
            self.mod.switch_grok("flames", self.cfg, {"flames": "dummy"})

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertNotIn("[model.switch-api-provider]", text)
        self.assertEqual(text.count('[model."grok-4.5"]'), 1)
        self.assertEqual(tomllib.loads(text)["models"]["default"], "grok-4.5")

    def test_build_model_discovery_headers_use_browser_user_agent(self):
        headers = self.mod.build_model_discovery_headers("secret", "bearer")

        self.assertEqual(headers["User-Agent"], self.mod.HTTP_USER_AGENT)
        self.assertEqual(headers["Authorization"], "Bearer secret")

    def test_skip_redundant_switch_checks_provider_and_explicit_model(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "switch-api-provider"\n\n'
                "[model.switch-api-provider]\n"
                'model = "grok-4.5"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
            )
        )

        self.assertTrue(self.mod.skip_redundant_switch("grok", "flames", self.cfg))
        self.assertTrue(self.mod.skip_redundant_switch("grok", "flames", self.cfg, "grok-4.5"))
        self.assertFalse(self.mod.skip_redundant_switch("grok", "flames", self.cfg, "grok-build-0.1"))
        self.assertFalse(self.mod.skip_redundant_switch("grok", "xai", self.cfg))

    def test_switch_grok_xai_restores_builtin_direct_mode(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "switch-api-provider"\n'
                "\n"
                "[model.switch-api-provider]\n"
                'model = "grok-4.5"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'env_key = "FLAMES_API_KEY"\n'
                'api_backend = "responses"\n'
            )
        )
        self.write_json(self.cfg.grok_auth, {"auth_mode": "session"})

        self.mod.switch_grok("xai", self.cfg, {}, model="")

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertIn('default = "grok-build"', text)
        self.assertEqual(self.mod.detect_provider("grok", self.cfg), "xai")
        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "grok-build")

    def test_switch_grok_xai_removes_actual_model_relay_override(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "grok-4.5"\n\n'
                '[model."grok-4.5"]\n'
                'model = "grok-4.5"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'description = "Managed by switch-api (Flames NewAPI)"\n'
                'env_key = "FLAMES_API_KEY"\n'
                'api_backend = "responses"\n'
            )
        )
        self.write_json(self.cfg.grok_auth, {"auth_mode": "session"})

        self.mod.switch_grok("xai", self.cfg, {}, model="")

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertNotIn('[model."grok-4.5"]', text)
        self.assertIn('default = "grok-build"', text)
        self.assertEqual(self.mod.detect_provider("grok", self.cfg), "xai")

    def test_switch_grok_xai_restores_stashed_login(self):
        self.init_grok_config(
            (
                "[models]\n"
                'default = "grok-4.5"\n\n'
                '[model."grok-4.5"]\n'
                'model = "grok-4.5"\n'
                'base_url = "https://www.flamescn.vip/v1"\n'
                'description = "Managed by switch-api (Flames NewAPI)"\n'
            )
        )
        self.write_json(self.cfg.grok_auth_relay_backup, {"auth_mode": "session", "access_token": "secret"})

        self.mod.switch_grok("xai", self.cfg, {}, model="")

        self.assertTrue(self.cfg.grok_auth.exists())
        self.assertFalse(self.cfg.grok_auth_relay_backup.exists())
        self.assertEqual(json.loads(self.cfg.grok_auth.read_text(encoding="utf-8"))["access_token"], "secret")

    def test_switch_grok_xai_accepts_explicit_builtin_model(self):
        self.init_grok_config()
        self.write_json(self.cfg.grok_auth, {"auth_mode": "session"})

        self.mod.switch_grok("xai", self.cfg, {}, model="grok-4.5")

        text = self.cfg.grok_config.read_text(encoding="utf-8")
        self.assertIn('default = "grok-4.5"', text)
        self.assertEqual(self.mod.detect_provider("grok", self.cfg), "xai")
        self.assertEqual(self.mod.detect_current_model("grok", self.cfg), "grok-4.5")

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
        self.mod.validate_model_for_tool("cc", "claude-fable-5", "flames")
        self.mod.validate_model_for_tool("cc", "claude-haiku-4-5-20251001", "flames")
        self.mod.validate_model_for_tool("cc", "claude-sonnet-5", "flames")
        self.mod.validate_model_for_tool("cc", "claude-sonnet-4-6", "flames")
        self.mod.validate_model_for_tool("cc", "claude-opus-4-8", "flames")
        self.mod.validate_model_for_tool("cc", "moonshotai/kimi-k3", "flames")
        self.mod.validate_model_for_tool("cc", "gpt-5.4", "flames")
        self.mod.validate_model_for_tool("cc", "deepseek-v4-pro", "flames")

    def test_model_validation_allows_grok_and_gpt_for_grok_tool(self):
        self.mod.validate_model_for_tool("grok", "grok-4.5", "flames")
        self.mod.validate_model_for_tool("grok", "gpt-5.4", "flames")
        with self.assertRaises(self.mod.SwitchError):
            self.mod.validate_model_for_tool("grok", "gemini-2.5-flash", "flames")

    def test_model_validation_allows_cc_deepseek_models(self):
        self.mod.validate_model_for_tool("cc", "deepseek-v4-pro", "deepseek")

    def test_model_validation_allows_codex_deepseek_models(self):
        self.mod.validate_model_for_tool("codex", "deepseek-v4-flash", "deepseek")
        self.mod.validate_model_for_tool("codex", "deepseek-v4-pro", "deepseek")

    def test_model_validation_allows_codex_flames_kimi_k3(self):
        self.mod.validate_model_for_tool("codex", "moonshotai/kimi-k3", "flames")

    def test_model_validation_allows_codex_flames_deepseek_models(self):
        self.mod.validate_model_for_tool("codex", "deepseek-v4-flash", "flames")
        self.mod.validate_model_for_tool("codex", "deepseek-v4-pro", "flames")

    def test_model_in_provider_accepts_icodeeasy_gpt_and_gemini(self):
        self.assertTrue(self.mod.model_in_provider("gpt-5.4", "icodeeasy"))
        self.assertTrue(self.mod.model_in_provider("gemini-2.5-flash", "icodeeasy"))

    def test_model_in_provider_accepts_molifang_only_gpt55(self):
        self.assertTrue(self.mod.model_in_provider("gpt-5.5", "molifang"))
        self.assertFalse(self.mod.model_in_provider("gpt-5.4", "molifang"))

    def test_model_in_provider_accepts_flames_deepseek(self):
        self.assertTrue(self.mod.model_in_provider("claude-fable-5", "flames"))
        self.assertTrue(self.mod.model_in_provider("claude-haiku-4-5-20251001", "flames"))
        self.assertTrue(self.mod.model_in_provider("claude-sonnet-5", "flames"))
        self.assertTrue(self.mod.model_in_provider("claude-sonnet-4-6", "flames"))
        self.assertTrue(self.mod.model_in_provider("claude-opus-4-8", "flames"))
        self.assertTrue(self.mod.model_in_provider("moonshotai/kimi-k3", "flames"))
        self.assertTrue(self.mod.model_in_provider("deepseek-v4-pro", "flames"))

    @patch("subprocess.run")
    def test_probe_model_curl_preserves_flames_namespaced_model(self, run):
        run.return_value.stdout = '{"choices": []}\n200'

        ok, reason = self.mod.probe_model_curl(
            "flames",
            "moonshotai/kimi-k3",
            {"flames": "dummy"},
        )

        self.assertTrue(ok, reason)
        command = run.call_args.args[0]
        payload = json.loads(command[command.index("-d") + 1])
        self.assertEqual(payload["model"], "moonshotai/kimi-k3")

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
