# switch-api
Unified API provider switcher across:
- Claude Code (`cc`, alias: `claude`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)
- Gemini CLI (`gemini`)
- Hermes (`hermes`)
- Grok (`grok`)

## Supported Providers

| Provider | Icon | Tools | Description |
|----------|------|-------|-------------|
| `duck` | 🦆 | all | DuckCoding (api.duckcoding.ai) |
| `quotio` | 🔗 | all | Quotio Tunnel (api.ancientechoes.ai) |
| `antigravity` | 🚀 | all | Antigravity-tools (tools.ancientechoes.ai) |
| `xingyun` | ☁️ | openclaw, codex, droid | Xingyun GPT (ai.xingyungept.cn) |
| `molifang` | 🧩 | openclaw, codex, droid, hermes | Molifang API (molifangapi.xyz) — OpenAI GPT-5.5 only |
| `flames` | 🔥 | cc, openclaw, codex, gemini, hermes, grok | Flames NewAPI (www.flamescn.vip) |
| `xai` | ⚡ | grok | xAI Official / Grok 官方直连 |
| `deepseek` | 🧠 | cc, codex | DeepSeek Official Anthropic + Responses API (api.deepseek.com) |
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
switch-api list [provider] --online  # 在线刷新 custom provider 模型后再列出
switch-api provider sync-models [provider]  # 同步 custom provider 的 /models
switch-api probe <custom-provider>   # 探测 custom provider 的 /models + 请求链路
switch-api doctor <custom-provider>  # 先刷新模型缓存，再做完整探测
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

### Keys & Custom Providers
```bash
switch-api key set MY_RELAY_API_KEY sk-xxx
switch-api key set MY_RELAY_CC_API_KEY sk-ant-xxx
switch-api key list

switch-api provider add-openai myrelay https://relay.example.com/v1 MY_RELAY_API_KEY gpt-5.4
switch-api provider add-openai myrelay https://relay.example.com/v1 MY_RELAY_API_KEY gpt-5.4 --disable-image-generation
switch-api provider add-anthropic myrelay https://relay.example.com/anthropic MY_RELAY_CC_API_KEY claude-sonnet-4-6
switch-api provider add-anthropic myrelay https://relay.example.com/anthropic MY_RELAY_CC_API_KEY claude-sonnet-4-6 --env CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
switch-api provider add-anthropic anyrouter https://anyrouter.top ANYROUTER_API_KEY claude-opus-4-8 --env ANTHROPIC_BETAS=context-1m-2025-08-07
switch-api provider sync-models anyrouter
switch-api model list
switch-api model add flames deepseek-v4-flash-vision-exp --tools cc,codex --vision
switch-api probe anyrouter
switch-api doctor anyrouter
switch-api list anyrouter --online
switch-api provider export myrelay ./myrelay.provider.json
switch-api provider export-all ./providers.bundle.json
switch-api provider export-all ./providers.bundle.json --with-secrets
switch-api provider import ./providers.bundle.json
switch-api provider list
switch-api provider rm myrelay

switch-api cc myrelay
switch-api codex myrelay
switch-api openclaw myrelay
switch-api droid myrelay
switch-api hermes myrelay
switch-api grok myrelay
switch-api myrelay                   # 切换该 custom provider 启用的全部工具
```

当前自定义 provider 分两层：
- `provider add-openai` 面向 **OpenAI-compatible** 网关，支持工具：
  - `codex`
  - `openclaw`
  - `droid`
  - `hermes`
  - `grok`
- `provider add-anthropic` 面向 **Anthropic-compatible** 网关，支持工具：
  - `cc`
- custom provider 现在支持自动探测 `/v1/models` 并缓存到：
  - `~/.config/switch-api/custom-providers.json`
  - `~/.config/switch-api/provider-models.json`

内置 `flames` / `deepseek` 的新模型可用 `switch-api model add` 持久登记，无需升级脚本；Codex DeepSeek catalog 会按登记信息动态生成。

同一个 provider 名称可以同时挂这两套配置；例如先执行：
- `switch-api provider add-openai myrelay ...`
- `switch-api provider add-anthropic myrelay ...`

之后：
- `switch-api cc myrelay` 只切 Claude Code
- `switch-api myrelay` 会切换该 provider 已启用的全部工具

`switch-api key set ...` 会同时写入：
- `~/.config/switch-api/credentials.json`
- `~/.env`

并自动确保：
- `~/.zshrc`
- `~/.bashrc`

里有 `source ~/.env` 的加载逻辑。

provider bundle 导入/导出：
- 默认导出 **不包含** secret
- `--with-secrets` 才会把相关 env value 一起写进 bundle
- `provider import` 默认 merge
- `provider import ... --replace` 用导入内容替换当前 provider 注册表

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
switch-api molifang                  # openclaw+codex+droid+hermes → Molifang / gpt-5.5
switch-api flames                    # cc+openclaw+codex+gemini+hermes+grok → Flames NewAPI
switch-api xai                       # grok → xAI 官方直连
switch-api deepseek                  # cc + codex → DeepSeek Official
switch-api aiwave                    # openclaw+codex+droid+gemini+hermes → AI Wave
switch-api icodeeasy                 # cc+openclaw+codex+gemini → iCodeEasy
switch-api openrouter                # openclaw+codex+droid → OpenRouter (free)
```

### Single Tool Switch
```bash
switch-api cc duck
switch-api claude deepseek              # `claude` 是 `cc` 的别名
switch-api cc icodeeasy
switch-api cc deepseek [model]
switch-api cc deepseek deepseek-v4-pro
switch-api cc deepseek deepseek-v4-flash-vision-exp  # Claude Code → DeepSeek V4 Flash Vision
switch-api codex deepseek                 # Codex → DeepSeek V4 Flash
switch-api codex deepseek deepseek-v4-flash
switch-api codex deepseek deepseek-v4-flash-vision-exp  # Codex → DeepSeek V4 Flash Vision
switch-api codex deepseek deepseek-v4-pro      # Codex → DeepSeek V4 Pro (direct Responses)
switch-api cc flames [model]
switch-api cc flames claude-opus-4-8
switch-api cc flames moonshotai/kimi-k3       # K3 主模型及 helper/subagent 均走 Flames
switch-api cc flames deepseek-v4-pro          # Claude Code → Flames NewAPI / DeepSeek V4 Pro
switch-api cc flames deepseek-v4-flash-vision-exp  # Claude Code → Flames NewAPI / DeepSeek V4 Flash Vision
switch-api codex flames deepseek-v4-flash     # Codex → Flames NewAPI / DeepSeek V4 Flash
switch-api codex flames deepseek-v4-flash-vision-exp  # Codex → Flames NewAPI / DeepSeek V4 Flash Vision
switch-api codex flames deepseek-v4-pro       # Codex → Flames NewAPI / DeepSeek V4 Pro
switch-api openclaw quotio [profile]
switch-api openclaw icodeeasy [model]
switch-api codex icodeeasy [model]
switch-api openclaw xingyun gpt-5.4
switch-api codex molifang            # Codex → Molifang / gpt-5.5
switch-api openclaw molifang         # OpenClaw → molifang/gpt-5.5
switch-api droid molifang            # Droid custom model → Molifang gpt-5.5
switch-api hermes molifang           # Hermes → Molifang / gpt-5.5
switch-api openclaw duck codex             # duckcoding-codex/gpt-5.4-xhigh-openai-compact
switch-api openclaw flames [model]
switch-api openclaw flames --agent lingxi  # 仅切换指定 OpenClaw agent
switch-api openclaw flames --all-agents    # 同步切换所有 OpenClaw agent
switch-api codex openai                    # OpenAI 官方 OAuth
switch-api codex openai_V420               # flames_newapi + OPENAI_V420_API_KEY
switch-api codex flames                    # Flames / gpt-5.6 + FLAMES_API_KEY
switch-api codex flames moonshotai/kimi-k3 # 同一 FLAMES_API_KEY，显式切到 K3
switch-api grok flames                     # Grok → Flames；暂存官方登录态，优先当前 key 可用的 grok-*
switch-api grok xai                        # Grok → xAI 官方直连 / grok-build；恢复官方登录态
switch-api openclaw aiwave [model]
switch-api droid quotio [profile]
switch-api hermes flames
switch-api hermes aiwave [model]
switch-api --profile video-maker hermes aiwave
switch-api --all-profiles hermes flames
switch-api gemini duck
switch-api gemini icodeeasy
```

切到 Codex K3 时会生成受管的 `model_catalog_json`，补齐 1M context、推理档位和工具能力元数据；该目录在 Codex 启动时加载，因此切换后请新开 Codex 会话。

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
- Shared shell env file: `~/.env`
- `switch-api key set ...` 会：
  - 写入 `credentials.json`
  - 写入 `~/.env`
  - 检查 `~/.zshrc` / `~/.bashrc` 是否已加载 `~/.env`；若没有则自动补一条
- Supported environment variables:
  - `DUCK_ANTHROPIC_API_KEY`, `DUCK_GEMINI_API_KEY`, `DUCKCODING_API_KEY`
  - `QUOTIO_API_KEY`
  - `ANTIGRAVITY_API_KEY`
  - `XINGYUN_API_KEY`
  - `MOLIFANG_API_KEY`
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
- 对需要 shell env 的链路，`switch-api` 现在优先把共享变量渲染到 `~/.env`
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
VERSION                             # current CLI version
docs/usage/switch-api.md             # usage guide
docs/plans/                          # design notes
examples/credentials.example.json   # redacted example
skills/                              # repo-local Codex skills
skills/api-provider-switch/          # 切换 skill
skills/api-provider-admin/           # key/provider 注册与维护 skill
```
