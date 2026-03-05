# switch-api
Unified API provider switcher across:
- Claude Code (`cc`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)
- Gemini CLI (`gemini`)

## Supported Providers

| Provider | Icon | Tools | Description |
|----------|------|-------|-------------|
| `duck` | 🦆 | all | DuckCoding (api.duckcoding.ai) |
| `quotio` | 🔗 | all | Quotio Tunnel (api.ancientechoes.ai) |
| `antigravity` | 🚀 | all | Antigravity-tools (tools.ancientechoes.ai) |
| `openai` | 🔑 | codex | OpenAI 官方 (api.openai.com via proxy) |
| `quotio_local` | 🔗 | codex, droid | Quotio Local (本地 app, 127.0.0.1:8317) |
| `openrouter` | 🌐 | openclaw, codex, droid | OpenRouter (openrouter.ai) — free models |
| `openai` | 🔑 | codex, droid | OpenAI 官方 (api.openai.com via proxy) |
| `aiwave` | 🌊 | codex, droid, gemini | AI Wave (api.ai-wave.org) |
| `icodeeasy` | 🧊 | cc | iCodeEasy (api.icodeeasy.cc) — Anthropic 原生 API |
| `duck_codex2cc` | 🦆 | cc | Duck CodeX→CC 映射 key（Claude 名称映射到 gpt-5.3-codex） |

## Version
See `VERSION`.

## Commands

### Status & Info
```bash
switch-api status                    # 查看各工具当前提供商
switch-api check [--online]          # 检查当前模型状态
switch-api list [provider]           # 列出可用模型
```

### Full Switch (all tools)
```bash
switch-api duck                      # 全部 → DuckCoding
switch-api quotio                    # 全部 → Quotio
switch-api antigravity               # 全部 → Antigravity
switch-api openrouter                # openclaw+codex+droid → OpenRouter (free)
```

### Single Tool Switch
```bash
switch-api cc duck
switch-api openclaw quotio [profile]
switch-api codex openai
switch-api droid quotio [profile]
switch-api gemini duck
```

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
  - `OPENAI_API_KEY`
  - `OPENROUTER_API_KEY`
  - `ICODEEASY_API_KEY`
  - `DUCK_CODEX2CC_API_KEY`
- Keys are loaded from env → credential store (auto-merged on each run)

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
