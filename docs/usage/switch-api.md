# API Provider 切换系统

在 DuckCoding 中转和 Quotio 本地隧道之间一键切换所有 AI 工具的 API 后端。

## 架构

```
┌─────────────┐     ┌──────────────────────────┐
│  DuckCoding  │     │  Quotio Tunnel           │
│  (🦆 duck)   │     │  (🔗 quotio)              │
│              │     │                          │
│  jp.duck     │     │  api.ancientechoes.ai    │
│  coding.com  │     │    ↓ Cloudflare Tunnel   │
│              │     │  localhost:8317 (Quotio)  │
└──────┬───────┘     └────────────┬─────────────┘
       │                         │
       └──────────┬──────────────┘
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

## 工具说明

- **cc** — Claude Code，配置文件 `~/.claude/settings.json`
- **openclaw** — OpenClaw Telegram Bot，配置文件 `~/.openclaw/openclaw.json`
- **codex** — OpenAI Codex，配置文件 `~/.codex/config.toml`
- **droid** — Gemini CLI (Droid)，通过 `~/.bashrc` 中的环境变量控制
- **all** — 以上全部

---

## 命令行用法

脚本位置：`~/bin/switch-api`（Python 脚本）

### 语法

```bash
switch-api <参数1> [参数2]
```

支持两种调用方式：

**方式一：双参数（指定工具 + Provider）**
```bash
switch-api <tool> <provider>
```
- `<tool>` = `cc` | `openclaw` | `codex` | `droid` | `all`
- `<provider>` = `duck` | `quotio`

**方式二：单参数（快捷全切）**
```bash
switch-api <provider>
```
- 等价于 `switch-api all <provider>`，一次切换所有工具

**方式三：查看状态**
```bash
switch-api status
```

### 完整命令列表

```bash
# ─── 查看状态 ───────────────────────────────────
switch-api status              # 显示所有工具当前连接的 provider

# ─── 全部切换（两种写法等价）─────────────────────
switch-api duck                # 全部 → DuckCoding（单参数简写）
switch-api quotio              # 全部 → Quotio（单参数简写）
switch-api all duck            # 全部 → DuckCoding（完整写法）
switch-api all quotio          # 全部 → Quotio（完整写法）

# ─── 只切 Claude Code ──────────────────────────
switch-api cc duck             # Claude Code → DuckCoding
switch-api cc quotio           # Claude Code → Quotio

# ─── 只切 OpenClaw ─────────────────────────────
switch-api openclaw duck       # OpenClaw → DuckCoding
switch-api openclaw quotio     # OpenClaw → Quotio（默认主模型 Opus 4.6 Thinking）
switch-api openclaw quotio gemini3  # OpenClaw → Quotio Gemini 3 (3.1-pro-high)

# ─── 只切 Codex ────────────────────────────────
switch-api codex duck          # Codex → DuckCoding
switch-api codex quotio        # Codex → Quotio

# ─── 只切 Droid ────────────────────────────────
switch-api droid duck          # Droid → DuckCoding
switch-api droid quotio        # Droid → Quotio
```

### Bash 快捷别名

在终端直接输入（已配置在 `~/.bashrc`）：

```bash
api-status       # = switch-api status
api-duck         # = switch-api all duck
api-quotio       # = switch-api all quotio
cc-duck          # = switch-api cc duck
cc-quotio        # = switch-api cc quotio
oc-duck          # = switch-api openclaw duck
oc-quotio        # = switch-api openclaw quotio
cx-duck          # = switch-api codex duck
cx-quotio        # = switch-api codex quotio
```

临时使用某个 provider（不修改配置文件）：

```bash
cxo              # Codex 临时用 OpenAI 官方
cxq              # Codex 临时用 Quotio
```

---

## Telegram 用法（通过 OpenClaw Bot）

在 Telegram 私聊 OpenClaw Bot 发送消息：

### 全部切换

```
/switch duck                   → 全部切到 DuckCoding
/switch quotio                 → 全部切到 Quotio
/switch all duck               → 全部切到 DuckCoding（显式写法）
/switch all quotio             → 全部切到 Quotio（显式写法）
```

### 只切某个工具

```
/switch cc duck                → 只切 Claude Code → DuckCoding
/switch cc quotio              → 只切 Claude Code → Quotio
/switch openclaw duck          → 只切 OpenClaw → DuckCoding
/switch openclaw quotio        → 只切 OpenClaw → Quotio（默认 Opus 4.6 Thinking）
/switch openclaw quotio gemini3 → 只切 OpenClaw → Quotio Gemini 3
/switch codex duck             → 只切 Codex → DuckCoding
/switch codex quotio           → 只切 Codex → Quotio
/switch droid duck             → 只切 Droid → DuckCoding
/switch droid quotio           → 只切 Droid → Quotio
```

### 查看状态

```
/switch status                 → 显示所有工具当前 provider
/api                           → 同上
```

### 工作原理

OpenClaw 的 `TOOLS.md` 里注册了 `/switch` 指令。Bot 收到消息后在服务器执行
`~/bin/switch-api` 脚本，修改对应工具的配置文件并返回结果。

---


## Quotio 模型白名单（已记录）

`switch-api` 每次运行会写入：`~/.config/switch-api/provider-models.json`

当前记录的 Quotio 可用模型：
- `claude-opus-4-6-thinking`
- `claude-sonnet-4-6`
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-3-flash`
- `gemini-3-pro-high`
- `gemini-3.1-flash-image`
- `gemini-3.1-pro-high`
- `gemini-3.1-pro-low`
- `gpt-oss-120b-medium`
- `tab_flash_lite_preview`
- `tab_jump_flash_lite_preview`

### Claude Code 映射策略（Quotio）
### OpenClaw 映射策略（Quotio）
- 切换到 `quotio` 时，默认主模型设为：`quotio/claude-sonnet-4-6`
- 同时保留两个 provider：
  - `quotio`（Claude 4.6 系列）
  - `quotio-gemini`（Gemini 3/3.1 系列）
- 自动回退：
  - `quotio-gemini/*` → `quotio/claude-sonnet-4-6`
  - `quotio/claude-haiku-4-5*` → `quotio/claude-sonnet-4-6`
  - `quotio/claude-opus-4-5*` → `quotio/claude-opus-4-6-thinking`

### Droid 映射策略（Quotio）
### Codex 映射策略（Quotio）
- `switch-api codex/all quotio` 默认保留你当前 `model`。
- 若检测到 `claude-haiku-4-5*` 或 `claude-opus-4-5*`，会自动映射到 4.6 系列避免 502。

- `switch-api droid quotio` 或 `switch-api all quotio` 会同步写入：
  - `GEMINI_MODEL=gemini-3.1-pro-high`
- 切回 duck 时写入：
  - `GEMINI_MODEL=gemini-3.1-pro-preview`

- 允许：`claude-opus-4-6-thinking`、`claude-sonnet-4-6`
- 自动回退：
  - `claude-opus-4-5*` → `claude-opus-4-6-thinking`
  - `claude-haiku-4-5*` → `claude-sonnet-4-6`
- 若当前模型不在白名单：回退到 `claude-opus-4-6-thinking`

## 状态输出说明

运行 `switch-api status` 或 `/switch status` 后看到的输出：

```
═══ API Provider Status ═══
  cc         🦆  duck        ← Claude Code 连接 DuckCoding
  openclaw   🦆  duck        ← OpenClaw 连接 DuckCoding
  codex      🦆  duck        ← Codex 连接 DuckCoding
  droid      🦆  duck        ← Droid 连接 DuckCoding
═══════════════════════════
  🦆 = DuckCoding (jp.duckcoding.com)
  🔗 = Quotio Tunnel (api.ancientechoes.ai)
```

图标含义：
- 🦆 = 当前连接 DuckCoding
- 🔗 = 当前连接 Quotio 隧道
- ❓ = 未知 / 未配置

---

## 切换时发生了什么

### Claude Code (cc)
修改 `~/.claude/settings.json` 中的：
- `env.ANTHROPIC_BASE_URL` → 对应 provider 的地址
- `env.ANTHROPIC_AUTH_TOKEN` → 对应 provider 的 API Key

### OpenClaw
修改三个文件：
- `~/.openclaw/openclaw.json` → `models.providers` 和 `agents.defaults.model.primary`
- `~/.openclaw/agents/main/agent/models.json` → provider 定义
- `~/.openclaw/agents/main/agent/auth.json` + `auth-profiles.json` → API Key 认证

**并自动重启 gateway**（kill 旧进程 → 从 `/opt/openclaw` 启动新进程）

### Codex
修改 `~/.codex/config.toml` 中的 `model_provider` 字段值

### Droid
修改 `~/.bashrc` 中的 `GEMINI_BASE_URL` 和 `GEMINI_API_KEY`
（切换后需要新开终端或 `source ~/.bashrc` 才对当前终端生效）

---

## 备份

每次切换自动生成带时间戳的备份：

```
原文件.bak.switch-YYYYMMDD-HHMMSS
```

例如：
```
~/.claude/settings.json.bak.switch-20260226-153000
~/.openclaw/openclaw.json.bak.switch-20260226-153000
```

---

## 安全检查

- 切换到 `quotio` 时，脚本会检查 `QUOTIO_API_KEY` 环境变量是否已设置
- `switch-api` 会把 duck/quotio 的密钥快照保存到 `~/.config/switch-api/credentials.json`（权限 600），用于环境变量冲突或切换失败时恢复
- 切换 `openclaw/droid` 到 `duck` 时，优先使用 `DUCK_GEMINI_API_KEY`，若未设置再回退到 `GEMINI_API_KEY`
- 推荐在 `~/.bashrc` 固定配置 `DUCK_GEMINI_API_KEY`，避免 `GEMINI_API_KEY` 被 Quotio 覆盖后导致 Duck 401
- 如果为空，拒绝切换并提示错误
- Key 配置在 `~/.bashrc` 中：`export QUOTIO_API_KEY="..."`
- 脚本会自动从 `~/.bashrc` 读取 `export` 行，无需手动 source

---

## 故障排除

### Quotio 隧道不通（Cloudflare 1033 错误）
本地电脑关机或 Quotio 停止时会出现。解决：
```bash
api-duck           # 切回 DuckCoding
```

### OpenClaw 切换后不响应
查看日志：
```bash
tail -20 ~/logs/openclaw.log
```
手动重启：
```bash
pkill -f openclaw-gateway
cd /opt/openclaw && nohup npx openclaw gateway --port 18789 run > ~/logs/openclaw.log 2>&1 &
```

### QUOTIO_API_KEY 报错
```bash
grep QUOTIO_API_KEY ~/.bashrc    # 检查 key 是否配置
```

---

## 文件清单

```
~/bin/switch-api                              主切换脚本
~/.bashrc                                     环境变量 (API Keys) + 快捷别名
~/.claude/settings.json                       Claude Code 配置
~/.openclaw/openclaw.json                     OpenClaw 主配置
~/.openclaw/agents/main/agent/models.json     OpenClaw 模型配置
~/.openclaw/agents/main/agent/auth.json       OpenClaw 认证 (API Key)
~/.openclaw/agents/main/agent/auth-profiles.json  OpenClaw 认证 Profile
~/.openclaw/workspace/TOOLS.md                OpenClaw /switch 指令说明
~/.codex/config.toml                          Codex 配置
~/docs/usage/switch-api.md                    本文档
~/docs/plans/WP-1.0-api-provider-switch.md    规划文档
~/.config/switch-api/credentials.json          Provider 密钥快照（duck + quotio）
~/logs/openclaw.log                           OpenClaw 启动日志
```
