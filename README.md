# switch-api
Unified API provider switcher across:
- Claude Code (`cc`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)
- Gemini CLI (`gemini`)
- Hermes (`hermes`)

## Supported Providers

| Provider | Icon | Tools | Description |
|----------|------|-------|-------------|
| `duck` | 🦆 | all | DuckCoding (api.duckcoding.ai) |
| `quotio` | 🔗 | all | Quotio Tunnel (api.ancientechoes.ai) |
| `antigravity` | 🚀 | all | Antigravity-tools (tools.ancientechoes.ai) |
| `xingyun` | ☁️ | openclaw, codex, droid | Xingyun GPT (ai.xingyungept.cn) |
| `flames` | 🔥 | cc, openclaw, codex, hermes | Flames NewAPI (www.flamescn.vip) |
| `deepseek` | 🧠 | cc | DeepSeek Official Anthropic API (api.deepseek.com/anthropic) |
| `quotio_local` | 🔗 | codex, droid | Quotio Local (本地 app, 127.0.0.1:8317) |
| `openrouter` | 🌐 | openclaw, codex, droid | OpenRouter (openrouter.ai) — free models |
| `openai` | 🔑 | openclaw, codex, droid | OpenAI 官方 (api.openai.com via proxy) |
| `aiwave` | 🌊 | openclaw, codex, droid, gemini, hermes | AI Wave (api.ai-wave.org) |
| `icodeeasy` | 🧊 | cc, openclaw, codex, gemini | iCodeEasy (api.icodeeasy.cc) — 统一网关（Anthropic + OpenAI + Gemini） |
| `duck_codex2cc` | 🦆 | cc | Duck CodeX→CC 映射 key（Claude 名称映射到 gpt-5.3-codex） |

## Version
See `VERSION`.

## Commands

### Status & Info
```bash
switch-api status                    # 查看各工具当前提供商
switch-api check [--online]          # 检查当前模型状态
switch-api list [provider]           # 列出可用模型
switch-api codex-account status      # 查看当前 Codex 官方 auth / 目录状态
switch-api codex-account list        # 列出 accounts/auth.json_* 与已注册的官方账号目录
```

### Codex Official Accounts
```bash
switch-api codex openai                    # 切到 OpenAI 官方模式（注释 model_provider，使用 auth.json）
switch-api codex-account list              # 列出 ~/.codex/accounts/auth.json_* 与已注册目录
switch-api codex-account use cool1982405@gmail.com
switch-api codex-account add main @current   # 把当前生效中的 CODEX_HOME 注册为 main
switch-api codex-account add alt             # 创建 ~/.codex-profiles/alt 并注册
switch-api codex-account use alt             # 持久化切换到 alt（写入 CODEX_HOME）
```

`codex-account` 与 provider 是两套机制：
- `provider` 切换的是 API endpoint / API key
- `codex openai` 切换的是 Codex 官方 OAuth 模式（`auth.json`）
- `codex-account` 优先切换当前 `CODEX_HOME/accounts/` 下的 `auth.json_*` 账号快照；若名称匹配已注册目录，则切换整套 `CODEX_HOME`
- Codex 被 `switch-api` 改写前的 `config.toml` / `auth.json` 会统一备份到 `CODEX_HOME/backups/`

注册新账号后，如果目录还没登录：
```bash
CODEX_HOME="$HOME/.codex-profiles/alt" codex login --device-auth
```

### Full Switch (all tools)
```bash
switch-api duck                      # 全部 → DuckCoding
switch-api quotio                    # 全部 → Quotio
switch-api antigravity               # 全部 → Antigravity
switch-api xingyun                   # openclaw+codex+droid → Xingyun GPT
switch-api flames                    # cc+openclaw+codex+hermes → Flames NewAPI
switch-api deepseek                  # cc → DeepSeek Official
switch-api aiwave                    # openclaw+codex+droid+gemini+hermes → AI Wave
switch-api icodeeasy                 # cc+openclaw+codex+gemini → iCodeEasy
switch-api openrouter                # openclaw+codex+droid → OpenRouter (free)
```

### Single Tool Switch
```bash
switch-api cc duck
switch-api cc icodeeasy
switch-api cc deepseek [model]
switch-api cc deepseek deepseek-v4-pro
switch-api cc flames [model]
switch-api openclaw quotio [profile]
switch-api openclaw icodeeasy [model]
switch-api codex icodeeasy [model]
switch-api openclaw xingyun gpt-5.4
switch-api openclaw duck codex             # duckcoding-codex/gpt-5.4-xhigh-openai-compact
switch-api openclaw flames [model]
switch-api openclaw flames --agent lingxi  # 仅切换指定 OpenClaw agent
switch-api openclaw flames --all-agents    # 同步切换所有 OpenClaw agent
switch-api codex openai                    # OpenAI 官方 OAuth
switch-api codex openai_V420               # flames_newapi + OPENAI_V420_API_KEY
switch-api codex flames                    # flames_newapi + FLAMES_API_KEY
switch-api openclaw aiwave [model]
switch-api droid quotio [profile]
switch-api hermes flames
switch-api hermes aiwave [model]
switch-api --profile video-maker hermes aiwave
switch-api --all-profiles hermes flames
switch-api gemini duck
switch-api gemini icodeeasy
```

Hermes profile rules:
- `switch-api hermes <provider>` 只改根 `~/.hermes/config.yaml`
- `switch-api --profile <name> hermes <provider>` 只改该 profile
- `switch-api --all-profiles hermes <provider>` 批量改所有 `~/.hermes/profiles/*/config.yaml`

### OpenRouter (Free Models)
```bash
switch-api openrouter                         # 默认 stepfun/step-3.5-flash:free
switch-api codex openrouter                   # codex → OpenRouter
switch-api openclaw openrouter                # openclaw → step-3.5-flash
switch-api openclaw openrouter llama          # openclaw → llama-3.3-70b
switch-api openclaw openrouter qwen           # openclaw → qwen3-coder
switch-api openclaw openrouter gpt-oss        # openclaw → gpt-oss-120b
switch-api droid openrouter                   # droid → OpenRouter (customModels)
switch-api list openrouter                    # 列出 26 个免费模型
```

**OpenRouter OpenClaw Profiles:**
- `default` / `step` → stepfun/step-3.5-flash:free
- `llama` → meta-llama/llama-3.3-70b-instruct:free
- `qwen` → qwen/qwen3-coder:free
- `gemma` → google/gemma-3-27b-it:free
- `hermes` → nousresearch/hermes-3-llama-3.1-405b:free
- `gpt-oss` → openai/gpt-oss-120b:free

> Note: OpenRouter uses OpenAI-compatible API. `cc` (Claude Code) and `gemini` (Gemini CLI) are skipped because they require Anthropic / Google native API formats.

### Quotio Local (本地 Quotio app)
```bash
switch-api quotio_local                        # codex+droid → Quotio Local
switch-api droid quotio_local                  # Droid → Quotio Local
switch-api codex quotio_local                  # Codex → Quotio Local
switch-api droid quotio_local gpt-5.3-codex-high  # 指定模型+思考等级
```

### Model-level Switch
```bash
switch-api <tool> <provider> <model>          # 指定具体模型
switch-api codex duck gpt-5.3-codex
switch-api codex xingyun gpt-5.4
switch-api droid quotio_local gpt-5.3-codex-high  # 高思考等级
```

### Thinking Level (思考等级)
GPT 系列模型后缀控制思考等级：`-low` / `-medium` / `-high` / `-xhigh`

```bash
switch-api droid duck gpt-5.3-codex-high       # 高思考
switch-api droid quotio_local gpt-5.3-codex-xhigh  # 超高思考
```
> `-max` 是 5.1 系列独有模型变体，不是思考等级。

## Credential Management
- Credential store: `~/.config/switch-api/credentials.json` (mode 600)
- Supported environment variables:
  - `DUCK_ANTHROPIC_API_KEY`, `DUCK_GEMINI_API_KEY`, `DUCKCODING_API_KEY`
  - `QUOTIO_API_KEY`
  - `ANTIGRAVITY_API_KEY`
  - `XINGYUN_API_KEY`
  - `OPENAI_API_KEY`, `OPENAI_GQ80_API_KEY`, `OPENAI_V420_API_KEY`
  - `FLAMES_API_KEY`
  - `DEEPSEEK_API_KEY`
  - `OPENROUTER_API_KEY`
  - `AIWAVE_CODEX_API_KEY`, `AIWAVE_GEMINI_GCP_API_KEY`, `AIWAVE_GEMINI_API_KEY`
  - `AIWAVE_CLAUDE_ANTI_API_KEY`, `AIWAVE_CLAUDE_OMG_API_KEY`
  - `AIWAVE_API_KEY` (legacy fallback)
  - `ICODEEASY_API_KEY`
  - `DUCK_CODEX2CC_API_KEY`
- Keys are loaded from env → credential store (auto-merged on each run)
- `aiwave` 当前分槽规则：
  - `codex` / `droid` 使用 `AIWAVE_CODEX_API_KEY`
  - `gemini-gcp` 与 `gemini` 现在是两套独立槽位
  - `gemini` / `openclaw` / `hermes` 优先使用 `AIWAVE_GEMINI_GCP_API_KEY`，兼容回退到 `AIWAVE_GEMINI_API_KEY`
  - `AIWAVE_API_KEY` 只作为旧配置兼容兜底

## Security
- Real keys must NOT be committed.
- `examples/credentials.example.json` is a redacted placeholder only.

## Project Layout
```
bin/switch-api                       # executable Python CLI
docs/usage/switch-api.md             # usage guide
docs/plans/                          # design notes
examples/credentials.example.json   # redacted example
skills/                              # OpenClaw skill
```
