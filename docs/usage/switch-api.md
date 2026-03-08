# API Provider 切换系统

在 DuckCoding、Quotio 本地隧道、Antigravity-tools、OpenAI 官方等 provider 之间一键切换所有 AI 工具的 API 后端。

## 架构

```
┌─────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│  DuckCoding  │  │  Quotio Tunnel           │  │  Antigravity-tools       │
│  (🦆 duck)   │  │  (🔗 quotio)              │  │  (🚀 antigravity)        │
│              │  │                          │  │                          │
│  jp.duck     │  │  api.ancientechoes.ai    │  │  tools.ancientechoes.ai  │
│  coding.com  │  │    ↓ Cloudflare Tunnel   │  │    ↓ Cloudflare Tunnel   │
│              │  │  localhost:8317 (Quotio)  │  │  localhost:8045 (local)  │
└──────┬───────┘  └────────────┬─────────────┘  └────────────┬─────────────┘
       │                       │                             │
       └───────────┬───────────┴─────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ▼             ▼             ▼
  Claude Code   OpenClaw     Codex/Droid
```

## Provider 说明

- **duck** — DuckCoding 中转 `https://api.duckcoding.ai`，支持 Claude Opus / Gemini 3 / GPT 等
  - 三个独立 API Key：`duck_anthropic`（Claude）、`duck_gemini`（Gemini）、`duck_codex`（Codex）
- **quotio** — Quotio 本地隧道 `https://api.ancientechoes.ai`，支持 Claude Opus / Gemini 3 / OpenAI GPT-5 系列
  - 依赖本地电脑运行 Quotio (port 8317) + Cloudflare Tunnel
- **antigravity** — Antigravity-tools `https://tools.ancientechoes.ai`，支持 Claude / Gemini 全系列
  - 依赖本地电脑运行 antigravity-tools (port 8045) + Cloudflare Tunnel
  - 同时支持 OpenAI / Anthropic / Gemini 三种协议
- **icodeeasy** — iCodeEasy `https://api.icodeeasy.cc`，**CC-only**（仅 Claude Code）
  - **仅支持 Anthropic 原生 API**（`/v1/messages` + `x-api-key`），不支持 OpenAI `/v1/chat/completions`
  - 支持所有 Claude 模型（3.5 haiku → opus 4.6）
  - 不能用于 openclaw / codex / droid / gemini（这些工具需要 OpenAI 兼容格式）
- **duck_codex2cc** — Duck CodeX→CC 映射 key，**CC-only**
  - 在 CC 中用 Claude 模型名，duck 后端自动映射到 GPT codex 模型
  - `claude-opus-4-6` → `gpt-5.3-codex-xhigh`
  - `claude-sonnet-4-6` → `gpt-5.3-codex-high`
  - `claude-haiku-4-5-20251001` → `gpt-5.3-codex-medium`
- **openai** — OpenAI 官方 `https://api.openai.com/v1`
  - `codex` / `droid` 使用静态 API key
  - `openclaw` 支持两种模式：
    - `key` → `openai-direct/...`
    - `oauth` → `openai-codex/...`
  - `openclaw oauth` 切换前需先执行：`openclaw onboard --auth-choice openai-codex`
  - 或使用：`~/.npm-global/bin/openclaw models auth login --provider openai-codex`

## Antigravity-tools 可用模型

**Claude 系列（OpenAI 协议 `/v1`）：**
- `claude-opus-4-6-thinking`
- `claude-sonnet-4-6`
- `claude-sonnet-4-6-thinking`

**Gemini 系列（Gemini 协议 `/v1beta`）：**
- `gemini-3.1-pro-high`
- `gemini-3.1-pro-low`
- `gemini-3.1-flash-image`（图片生成）
- `gemini-3-pro-image`（图片生成）
- `gemini-3-pro-high`
- `gemini-3-pro-low`
- `gemini-3-flash`

**其他：**
- `gpt-oss-120b-medium`
- 更多模型详见 `/v1/models` 接口

## Quotio 可用模型（2026-02-28 更新）

**Claude 系列：**
- `claude-opus-4-6-thinking`
- `claude-sonnet-4-6`

**Gemini 系列：**
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-3-flash`
- `gemini-3-pro-high`
- `gemini-3.1-flash-image`
- `gemini-3.1-pro-high`
- `gemini-3.1-pro-low`

**OpenAI 系列（新增）：**
- `gpt-5`
- `gpt-5-codex` / `gpt-5-codex-mini`
- `gpt-5.1` / `gpt-5.1-codex` / `gpt-5.1-codex-max` / `gpt-5.1-codex-mini`
- `gpt-5.2` / `gpt-5.2-codex`
- `gpt-5.3-codex` / `gpt-5.3-codex-spark`

**其他：**
- `gpt-oss-120b-medium`
- `tab_flash_lite_preview` / `tab_jump_flash_lite_preview`

## iCodeEasy 可用模型（CC-only, 2026-03-06 更新）

> ⚠️ **API 兼容性限制**：iCodeEasy 仅支持 Anthropic 原生 API（`/v1/messages`），
> 不支持 OpenAI 格式（`/v1/chat/completions`）。因此**只能用于 Claude Code (cc)**，
> 不能用于 openclaw / codex / droid / gemini。

**Claude 系列：**
- `claude-opus-4-6`
- `claude-sonnet-4-6`
- `claude-sonnet-4-5-20250929`
- `claude-sonnet-4-20250514`（→ 实际返回 sonnet-4-5-20250929）
- `claude-opus-4-5-20251101`
- `claude-opus-4-1-20250805`（→ 实际返回 opus-4-5-20251101）
- `claude-haiku-4-5-20251001`
- `claude-3-5-haiku-20241022`（→ 实际返回 haiku-4-5-20251001）
- `claude-3-7-sonnet-20250219`

## 工具说明

- **cc** — Claude Code，配置文件 `~/.claude/settings.json`
- **openclaw** — OpenClaw Telegram Bot，配置文件 `~/.openclaw/openclaw.json`
- **codex** — OpenAI Codex，配置文件默认 `~/.codex/config.toml`，若设置 `CODEX_HOME` 则跟随该目录
- **droid** — Factory Droid CLI，默认通过 `~/.bashrc` Gemini 环境变量控制，codex profile 通过 `~/.factory/settings.json` customModels
- **gemini** — Gemini CLI，配置文件 `~/.gemini/.env`
- **all** — 以上全部

---

## 命令行用法

脚本位置：`~/bin/switch-api`（Python 脚本，v2.0.1）

### 语法

```bash
switch-api [--force] <参数1> [参数2] [参数3]
```

**方式一：双参数（指定工具 + Provider）**
```bash
switch-api <tool> <provider>
```
- `<tool>` = `cc` | `openclaw` | `codex` | `droid` | `all`
- `<provider>` = `duck` | `quotio` | `antigravity` | `openai`

**方式二：单参数（快捷全切）**
```bash
switch-api <provider>
```

**方式三：三参数（OpenClaw / Droid + Profile）**
```bash
switch-api openclaw duck <profile>
switch-api openclaw quotio <profile>
switch-api openclaw antigravity <profile>
switch-api openclaw openai <mode>
switch-api droid quotio <profile>
```
- OpenClaw `duck/quotio/antigravity <profile>` = `default` | `opus` | `sonnet` | `gemini` | `gemini3`
- OpenClaw `openai <mode>` = `key` | `oauth`
- Droid `<profile>` = `default` | `gemini` | `codex`

**方式四：查看状态**
```bash
switch-api status
switch-api codex-account status
```

**方式五：Codex 官方账号切换**
```bash
switch-api codex-account list
switch-api codex-account add <name> [path|@current]
switch-api codex-account use <name>
```

**选项：**
- `--force` — 跳过 pre-flight 连接检查（隧道检测）

### 完整命令列表

```bash
# ─── 查看状态 ───────────────────────────────────
switch-api status                            # 查看当前 provider
switch-api check                             # 查看当前各工具模型状态
switch-api check --online                    # 在线验证模型可用性
switch-api list                              # 列出所有 provider 可用模型
switch-api list quotio                       # 列出指定 provider 可用模型
switch-api codex-account status              # 查看当前 Codex 官方账号目录
switch-api codex-account list                # 列出已注册的官方账号

# ─── Codex 官方账号切换（ChatGPT OAuth）─────────
switch-api codex-account add main @current   # 注册当前生效中的目录
switch-api codex-account add alt             # 创建并注册 ~/.codex-profiles/alt
switch-api codex-account use alt             # 切换到 alt（写入 CODEX_HOME）
CODEX_HOME="$HOME/.codex-profiles/alt" codex login --device-auth

# ─── 全部切换 ───────────────────────────────────
switch-api duck                # 全部 → DuckCoding
switch-api quotio              # 全部 → Quotio
switch-api antigravity         # 全部 → Antigravity-tools
switch-api all duck            # 同上（完整写法）
switch-api all quotio
switch-api all antigravity

# ─── 只切 Claude Code ──────────────────────────
switch-api cc duck
switch-api cc quotio
switch-api cc antigravity
switch-api cc icodeeasy              # iCodeEasy (CC-only)
switch-api cc duck_codex2cc          # Duck CodeX→CC (GPT codex via CC)

# ─── 只切 OpenClaw ─────────────────────────────
switch-api openclaw duck                    # 默认 Claude Opus 4.6
switch-api openclaw duck gemini3            # Duck Gemini 3 ⚠️
switch-api openclaw duck sonnet             # Duck Sonnet 4.6
switch-api openclaw quotio                  # 默认 Opus 4.6 Thinking
switch-api openclaw quotio gemini3          # Quotio Gemini 3 ⚠️
switch-api openclaw antigravity             # 默认 Opus 4.6 Thinking
switch-api openclaw antigravity gemini3     # Antigravity Gemini 3 ⚠️
switch-api openclaw openai key              # OpenClaw → OpenAI API Key (openai-direct)
switch-api openclaw openai oauth            # OpenClaw → OpenAI OAuth (openai-codex)

# ─── 只切 Codex ────────────────────────────────
switch-api codex duck
switch-api codex quotio
switch-api codex antigravity

# ─── 只切 Droid ────────────────────────────────
switch-api droid duck                       # Duck Gemini
switch-api droid quotio                     # Quotio Gemini (默认)
switch-api droid quotio codex               # Quotio GPT-5.3 Codex (profile)
switch-api droid quotio gpt-5.3-codex       # Quotio GPT-5.3 Codex (直接指定) ⭐
switch-api droid antigravity                # Antigravity Gemini

# ─── Quotio Local (本地 Quotio app, 127.0.0.1:8317) ───
switch-api quotio_local                      # codex+droid → Quotio Local
switch-api droid quotio_local                # Droid → Quotio Local (gpt-5.3-codex)
switch-api codex quotio_local                # Codex → Quotio Local
switch-api droid quotio_local gpt-5.3-codex-high  # 指定模型+思考等级

# ─── OpenRouter (免费模型) ─────────────────────
switch-api openrouter                        # openclaw+codex+droid → OpenRouter
switch-api openclaw openrouter llama         # OpenClaw → Llama
switch-api droid openrouter                  # Droid → OpenRouter

# ─── OpenAI 多账号（API key provider）─────────
switch-api openai_Gq80                       # codex+droid → OpenAI[Gq80]
switch-api droid openai_V420                 # Droid → OpenAI[V420]
```

> `openai_Gq80` / `openai_V420` 仍然是 API key provider 切换。
> 如果要切换两个 ChatGPT 官方账号，请使用 `codex-account`，不要混用 provider 语义。

---

## 模型思考等级（Thinking Level）

OpenAI GPT 系列模型通过模型名后缀控制思考等级：

| 后缀 | 等级 | 示例 |
|------|------|------|
| (无后缀) | 默认/auto | `gpt-5.3-codex` |
| `-low` | 低 | `gpt-5.3-codex-low` |
| `-medium` | 中 | `gpt-5.3-codex-medium` |
| `-high` | 高 | `gpt-5.3-codex-high` |
| `-xhigh` | 超高 | `gpt-5.3-codex-xhigh` |

**注意**：`-max` 是 5.1 系列独有的模型变体（如 `gpt-5.1-codex-max`），不是思考等级后缀。

使用示例：
```bash
# Droid 使用 gpt-5.3-codex 高思考
switch-api droid quotio_local gpt-5.3-codex-high
switch-api droid duck gpt-5.3-codex-high

# Codex 使用 gpt-5.3-codex 高思考
switch-api codex duck gpt-5.3-codex-high
```

**Provider × 思考等级可用性**：
- **duck** — 支持所有思考等级（`-low/-medium/-high/-xhigh`）
- **quotio** — 仅基础模型（`gpt-5.3-codex`、`gpt-5.3-codex-spark`）
- **quotio_local** — 取决于本地 Quotio app 配置（跳过目录检查）

---

## Telegram 用法（通过 OpenClaw Bot）

### 全部切换

```
/switch duck                      → 全部切到 DuckCoding
/switch quotio                    → 全部切到 Quotio
/switch antigravity               → 全部切到 Antigravity-tools
```

### 查看模型

```
/switch list                      → 列出所有 provider 可用模型
/switch list quotio               → 列出 Quotio 可用模型
/switch check                     → 查看当前各工具模型状态
/switch check online              → 在线验证模型可用性
```

### 模型级切换

```
/switch codex quotio gpt-5.3-codex
/switch droid quotio gpt-5.3-codex
/switch openclaw quotio claude-sonnet-4-6
/switch openclaw openai key
/switch openclaw openai oauth
```

### 只切某个工具

```
/switch cc duck
/switch cc antigravity
/switch openclaw duck
/switch openclaw duck gemini3
/switch openclaw antigravity
/switch openclaw antigravity gemini3
/switch openclaw quotio gemini3
/switch codex antigravity
/switch droid antigravity
```

### 查看状态

```
/switch status
/api
```

---

## Pre-flight 连接检查 & 自动回滚

### Pre-flight（切换前）
- 对目标 provider 的 `/v1/models` 发 HTTP 请求（8 秒超时）
- 检测 Cloudflare 隧道错误（error code 1010/1033 等），即使 HTTP 状态码看似正常（403/200）
- 不可达 → 拒绝切换，所有配置文件保持不变
- `--force` 可跳过此检查

### Post-restart 回滚（OpenClaw 重启后）
- 切换前将 4 个配置文件快照保存到内存
- Gateway 重启后再探测一次（5 秒超时）
- 如果 provider 在重启期间挂了 → 自动恢复快照、重新启动 gateway

---

## OpenClaw 模型兼容性

OpenClaw 工具 schema 使用 `patternProperties`，Gemini API 不支持此特性（返回 HTTP 400）。

### 默认行为
- 所有 provider 的 OpenClaw 默认主模型均为 **Claude**（安全）
- `duck` → `duckcoding-claude/claude-opus-4-6`
- `quotio` → `quotio/claude-opus-4-6-thinking`
- `antigravity` → `antigravity/claude-opus-4-6-thinking`

### Gemini profile
- `gemini3` 等 profile 会切换到 Gemini 模型，并显示兼容性警告
- 如果遇到 HTTP 400 错误，切回默认（Claude）profile

### OpenClaw provider 结构
每个 provider 在 OpenClaw 中注册两个 sub-provider：

| Provider | Claude sub-provider | Gemini sub-provider |
|----------|-------------------|-------------------|
| duck | `duckcoding-claude` | `duckcoding` |
| quotio | `quotio` | `quotio-gemini` |
| antigravity | `antigravity` | `antigravity-gemini` |

---

## OpenClaw × OpenAI 双认证模式

`switch-api` 对 OpenClaw 的 OpenAI 路径支持两条独立链路：

| 模式 | 主模型前缀 | 认证来源 | 说明 |
|------|------------|----------|------|
| `key` | `openai-direct/...` | `OPENAI_API_KEY` / manual auth store | 静态 API key 模式 |
| `oauth` | `openai-codex/...` | `~/.openclaw/agents/main/agent/auth-profiles.json` | OpenClaw 官方 OAuth 模式 |

### 常用命令

```bash
switch-api openclaw openai key
switch-api openclaw openai oauth
switch-api status
switch-api check
```

### 关键说明

- `oauth` 模式检查的是 `~/.openclaw/agents/main/agent/auth-profiles.json`
- `~/.openclaw/openclaw.json` 中的 `auth.profiles` 只保存 metadata 和默认顺序，不保存真实 OAuth token
- `status` / `check` 会区分显示 `openai (key)` 和 `openai (oauth)`
- 如果本机还没有 `openai-codex` OAuth 凭据，先运行：

```bash
openclaw onboard --auth-choice openai-codex
# 或
~/.npm-global/bin/openclaw models auth login --provider openai-codex
```

---

## 模型映射策略

### Claude Code 映射（Quotio / Antigravity 通用）
- 允许：`claude-opus-4-6-thinking`、`claude-sonnet-4-6`
- 自动回退：
  - `claude-opus-4-5*` → `claude-opus-4-6-thinking`
  - `claude-haiku-4-5*` → `claude-sonnet-4-6`
- 若当前模型不在白名单 → `claude-opus-4-6-thinking`

### Codex 映射
- 检测到 `claude-haiku-4-5*` / `claude-opus-4-5*` 会自动映射到 4.6 系列

### Droid 映射
- duck → `GEMINI_MODEL=gemini-3.1-pro-preview`（env vars）
- quotio → `GEMINI_MODEL=gemini-3.1-pro-high`（env vars，无模型参数时默认 Gemini）
- quotio + 模型 → 如 `gpt-5.3-codex`（写入 customModels + 自动设置默认，同 quotio_local 逻辑）
- quotio codex → `gpt-5.3-codex`（profile 写法，同上）
- quotio_local → `gpt-5.3-codex`（写入 `~/.factory/settings.json` customModels，本地 127.0.0.1:8317）
- antigravity → `GEMINI_MODEL=gemini-3.1-pro-high`（env vars）
- openrouter → `stepfun/step-3.5-flash:free`（写入 `~/.factory/settings.json` customModels）
- openai / openai_Gq80 / openai_V420 → `gpt-5.3-codex`（写入 customModels，需代理）

> **Droid codex/quotio/quotio_local/openrouter/openai** 模型使用 OpenAI 协议，无法通过 GEMINI_* 环境变量配置。
> 切换时脚本写入 `~/.factory/settings.json` 的 `customModels` 字段，并自动更新 `sessionDefaultSettings.model`。
> 交互模式无需手动选模型，打开 Droid 即自动使用。
> 切换回 Gemini profile（如 `switch-api droid quotio`，不带模型参数）时自动清除 customModels 和 custom 默认值。

---

## Droid 非交互模式

切换 provider 后，Droid 交互模式自动使用新模型（`sessionDefaultSettings.model` 已更新）。

非交互模式通过 `-m` 参数指定 custom model ID：

```bash
# 格式: custom:{displayName 中空格替换为 -}-0
droid exec -m "custom:Quotio-gpt-5.3-codex-0" "分析当前目录的代码结构"
droid exec -m "custom:Quotio-Local-gpt-5.3-codex-0" "重构 main.py"
droid exec -m "custom:OpenRouter-stepfun/step-3.5-flash:free-0" "解释这段代码"
```

**常用 custom model ID**：

| Provider | 模型 | Custom ID |
|----------|------|-----------|
| quotio | gpt-5.3-codex | `custom:Quotio-gpt-5.3-codex-0` |
| quotio_local | gpt-5.3-codex | `custom:Quotio-Local-gpt-5.3-codex-0` |
| openrouter | step-3.5-flash:free | `custom:OpenRouter-stepfun/step-3.5-flash:free-0` |
| openai_Gq80 | gpt-5.3-codex | `custom:OpenAI[Gq80]-gpt-5.3-codex-0` |

> ID 生成规则：`custom:{displayName.replace(" ", "-")}-{index}`，其中 index 是 customModels 数组下标（通常为 0）。

---

## 状态输出说明

```
═══ API Provider Status ═══
  cc         🚀  antigravity
  openclaw   🔑  openai (oauth)
  codex      🚀  antigravity
  droid      🚀  antigravity
═══════════════════════════
  🦆 = DuckCoding (api.duckcoding.ai)
  🔗 = Quotio Tunnel (api.ancientechoes.ai)
  🚀 = Antigravity-tools (tools.ancientechoes.ai)
  🧊 = iCodeEasy (api.icodeeasy.cc)
  🔑 = OpenAI 官方 (api.openai.com via proxy)
```

OpenClaw 走 OpenAI 时会额外显示认证模式后缀，避免把 OAuth 和 API key 两条链路混在一起。

---

## Provider × API 协议兼容矩阵

不同工具需要不同的 API 协议，不是所有 provider 都支持所有工具：

| Provider | API 协议 | cc | openclaw | codex | droid | gemini |
|----------|----------|:--:|:--------:|:-----:|:-----:|:------:|
| duck | OpenAI + Anthropic | ✅ | ✅ | ✅ | ✅ | ✅ |
| quotio | OpenAI + Anthropic + Gemini | ✅ | ✅ | ✅ | ✅ | ✅ |
| antigravity | OpenAI + Anthropic + Gemini | ✅ | ✅ | ✅ | ✅ | ✅ |
| **icodeeasy** | **Anthropic 原生 only** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **duck_codex2cc** | **Anthropic 原生 (映射)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| openai | OpenAI | ❌ | ✅* | ✅ | ✅ | ❌ |
| openrouter | OpenAI | ❌ | ✅ | ✅ | ✅ | ❌ |
| aiwave | OpenAI + Gemini | ❌ | ❌ | ✅ | ✅ | ✅ |
| duck_cc1 | Anthropic 原生 only | ✅ | ❌ | ❌ | ❌ | ❌ |

> **关键限制**：`icodeeasy`、`duck_cc1` 和 `duck_codex2cc` 仅支持 Anthropic 原生 API（`/v1/messages`），
> OpenClaw / Codex / Droid 需要 OpenAI 格式（`/v1/chat/completions`），因此这些 provider
> 只能用于 Claude Code。`duck_codex2cc` 特殊之处在于后端将 Claude 模型名映射到 GPT codex 模型。
>
> `openai` 对 OpenClaw 支持两种模式：
> `switch-api openclaw openai key` 与 `switch-api openclaw openai oauth`。
> `oauth` 依赖 agent-local `auth-profiles.json` 中真实存在的 `type: "oauth"` 凭据。

---

## 排错：`No API key found for provider "openai-codex"`

### 现象

OpenClaw 切到 `openai oauth` 后启动失败，日志类似：

```text
No API key found for provider "openai-codex"
```

### 根因

- `openai-codex` 是 OpenClaw 官方 OAuth provider，不应该被当成普通 static-key provider 处理
- `~/.openclaw/openclaw.json` 中看到 `auth.profiles["openai-codex:*"]`，只说明 metadata 存在
- 真正的 OAuth access token / refresh token 必须在 `~/.openclaw/agents/main/agent/auth-profiles.json`
- 如果 agent-local auth store 里没有真实 OAuth 凭据，运行时就会退回到“找 API key”的错误路径

### 修复步骤

```bash
openclaw onboard --auth-choice openai-codex
# 或
~/.npm-global/bin/openclaw models auth login --provider openai-codex
switch-api openclaw openai oauth
switch-api status
switch-api check
```

### 临时回退

如果当前只想先恢复可用性，不等 OAuth 登录，可以先切回 API key 模式：

```bash
switch-api openclaw openai key
```

---

## 工具 × 模型兼容矩阵

模型级切换时，必须指定工具。不兼容的组合会报错。

- **cc** (Claude Code): 仅 `claude-*` 模型 — 切 GPT/Gemini 时 cc 保持不动
- **openclaw**: `claude-*` + `gemini-*`
- **codex**: 仅 `gpt-*` 模型 — 切 Claude/Gemini 时 codex 保持不动
- **droid**: `gemini-*`（默认）+ `gpt-*`（codex profile）
- **gemini**: 仅 `gemini-*`

### 模型级切换验证流程

1. 检查模型是否在 provider 目录中（`switch-api list <provider>` 查看）
2. 不在目录 → 报错（用 `--force` 跳过）
3. 检查工具是否兼容该模型 family → 不兼容则报错
4. 执行切换

---

## 安全检查

- 切换前 pre-flight 探测目标 provider 连接性
- 切换到 `quotio` 时检查 `QUOTIO_API_KEY`
- 切换到 `antigravity` 时检查 `ANTIGRAVITY_API_KEY`
- 切换到 `icodeeasy` 时检查 `ICODEEASY_API_KEY`
- 切换到 `duck_codex2cc` 时检查 `DUCK_CODEX2CC_API_KEY`
- 切换到 `openai` 时：
  - `codex` / `droid` / `openclaw key` 检查 `OPENAI_API_KEY`
  - `openclaw oauth` 检查 `~/.openclaw/agents/main/agent/auth-profiles.json` 中的真实 OAuth 凭据
- 密钥快照保存到 `~/.config/switch-api/credentials.json`（权限 600）
- Key 配置在 `~/.bashrc` 中，脚本自动读取 `export` 行

---

## 文件清单

```
~/bin/switch-api                              部署脚本 (v2.0.1)
~/code/switch-api/bin/switch-api             源码仓库脚本 (v2.0.1)
~/.bashrc                                     环境变量 (API Keys) + 快捷别名
~/.claude/settings.json                       Claude Code 配置
~/.openclaw/openclaw.json                     OpenClaw 主配置 + auth metadata / 默认路由
~/.openclaw/agents/main/agent/models.json     OpenClaw 模型配置
~/.openclaw/agents/main/agent/auth.json       OpenClaw 认证
~/.openclaw/agents/main/agent/auth-profiles.json  OpenClaw 真实认证 Profile（含 OAuth token）
~/.openclaw/workspace/TOOLS.md                OpenClaw /switch 指令说明
~/.codex/config.toml                          Codex 配置
~/.factory/settings.json                      Droid customModels（codex profile）
~/.config/switch-api/credentials.json         Provider 密钥快照
~/.config/switch-api/provider-models.json     Provider 模型目录
~/logs/openclaw.log                           OpenClaw 启动日志
```
