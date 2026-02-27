# API Provider 切换系统

在 DuckCoding、Quotio 本地隧道、Antigravity-tools 三个 provider 之间一键切换所有 AI 工具的 API 后端。

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

- **duck** — DuckCoding 中转 `https://jp.duckcoding.com`，支持 Claude Opus / Gemini 3 / GPT 等
- **quotio** — Quotio 本地隧道 `https://api.ancientechoes.ai`，支持 Claude Opus / Gemini 3 等
  - 依赖本地电脑运行 Quotio (port 8317) + Cloudflare Tunnel
- **antigravity** — Antigravity-tools `https://tools.ancientechoes.ai`，支持 Claude / Gemini 全系列
  - 依赖本地电脑运行 antigravity-tools (port 8045) + Cloudflare Tunnel
  - 同时支持 OpenAI / Anthropic / Gemini 三种协议

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

## 工具说明

- **cc** — Claude Code，配置文件 `~/.claude/settings.json`
- **openclaw** — OpenClaw Telegram Bot，配置文件 `~/.openclaw/openclaw.json`
- **codex** — OpenAI Codex，配置文件 `~/.codex/config.toml`
- **droid** — Gemini CLI (Droid)，通过 `~/.bashrc` 中的环境变量控制
- **all** — 以上全部

---

## 命令行用法

脚本位置：`~/bin/switch-api`（Python 脚本，v1.1.0）

### 语法

```bash
switch-api <参数1> [参数2] [参数3]
```

**方式一：双参数（指定工具 + Provider）**
```bash
switch-api <tool> <provider>
```
- `<tool>` = `cc` | `openclaw` | `codex` | `droid` | `all`
- `<provider>` = `duck` | `quotio` | `antigravity`

**方式二：单参数（快捷全切）**
```bash
switch-api <provider>
```

**方式三：三参数（OpenClaw + Profile）**
```bash
switch-api openclaw quotio <profile>
switch-api openclaw antigravity <profile>
```
- `<profile>` = `default` | `opus` | `sonnet` | `gemini` | `gemini3`

**方式四：查看状态**
```bash
switch-api status
```

### 完整命令列表

```bash
# ─── 查看状态 ───────────────────────────────────
switch-api status

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

# ─── 只切 OpenClaw ─────────────────────────────
switch-api openclaw duck
switch-api openclaw quotio                  # 默认 Opus 4.6 Thinking
switch-api openclaw quotio gemini3          # Quotio Gemini 3
switch-api openclaw antigravity             # 默认 Opus 4.6 Thinking
switch-api openclaw antigravity gemini3     # Antigravity Gemini 3

# ─── 只切 Codex ────────────────────────────────
switch-api codex duck
switch-api codex quotio
switch-api codex antigravity

# ─── 只切 Droid ────────────────────────────────
switch-api droid duck
switch-api droid quotio
switch-api droid antigravity
```

---

## Telegram 用法（通过 OpenClaw Bot）

### 全部切换

```
/switch duck                      → 全部切到 DuckCoding
/switch quotio                    → 全部切到 Quotio
/switch antigravity               → 全部切到 Antigravity-tools
```

### 只切某个工具

```
/switch cc duck
/switch cc antigravity
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

## 模型映射策略

### Claude Code 映射（Quotio / Antigravity 通用）
- 允许：`claude-opus-4-6-thinking`、`claude-sonnet-4-6`
- 自动回退：
  - `claude-opus-4-5*` → `claude-opus-4-6-thinking`
  - `claude-haiku-4-5*` → `claude-sonnet-4-6`
- 若当前模型不在白名单 → `claude-opus-4-6-thinking`

### OpenClaw 映射
- 默认主模型：`<provider>/claude-opus-4-6-thinking`
- 支持 profile 切换（`gemini3` → `<provider>-gemini/gemini-3.1-pro-high`）
- 同时注册两个 sub-provider：
  - `<provider>`（Claude 4.6 系列，OpenAI 协议）
  - `<provider>-gemini`（Gemini 3/3.1 系列，Google Generative AI 协议）

### Codex 映射
- 检测到 `claude-haiku-4-5*` / `claude-opus-4-5*` 会自动映射到 4.6 系列

### Droid 映射
- duck → `GEMINI_MODEL=gemini-3.1-pro-preview`
- quotio → `GEMINI_MODEL=gemini-3.1-pro-high`
- antigravity → `GEMINI_MODEL=gemini-3.1-pro-high`

---

## 状态输出说明

```
═══ API Provider Status ═══
  cc         🚀  antigravity
  openclaw   🚀  antigravity
  codex      🚀  antigravity
  droid      🚀  antigravity
═══════════════════════════
  🦆 = DuckCoding (jp.duckcoding.com)
  🔗 = Quotio Tunnel (api.ancientechoes.ai)
  🚀 = Antigravity-tools (tools.ancientechoes.ai)
```

---

## 安全检查

- 切换到 `quotio` 时检查 `QUOTIO_API_KEY`
- 切换到 `antigravity` 时检查 `ANTIGRAVITY_API_KEY`
- 密钥快照保存到 `~/.config/switch-api/credentials.json`（权限 600）
- Key 配置在 `~/.bashrc` 中，脚本自动读取 `export` 行

---

## 文件清单

```
~/bin/switch-api                              主切换脚本 (v1.1.0)
~/.bashrc                                     环境变量 (API Keys) + 快捷别名
~/.claude/settings.json                       Claude Code 配置
~/.openclaw/openclaw.json                     OpenClaw 主配置
~/.openclaw/agents/main/agent/models.json     OpenClaw 模型配置
~/.openclaw/agents/main/agent/auth.json       OpenClaw 认证
~/.openclaw/agents/main/agent/auth-profiles.json  OpenClaw 认证 Profile
~/.openclaw/workspace/TOOLS.md                OpenClaw /switch 指令说明
~/.codex/config.toml                          Codex 配置
~/.config/switch-api/credentials.json         Provider 密钥快照
~/.config/switch-api/provider-models.json     Provider 模型目录
~/logs/openclaw.log                           OpenClaw 启动日志
```
