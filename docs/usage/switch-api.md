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
  - 三个独立 API Key：`duck_anthropic`（Claude）、`duck_gemini`（Gemini）、`duck_codex`（Codex）
- **quotio** — Quotio 本地隧道 `https://api.ancientechoes.ai`，支持 Claude Opus / Gemini 3 / OpenAI GPT-5 系列
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

## 工具说明

- **cc** — Claude Code，配置文件 `~/.claude/settings.json`
- **openclaw** — OpenClaw Telegram Bot，配置文件 `~/.openclaw/openclaw.json`
- **codex** — OpenAI Codex，配置文件 `~/.codex/config.toml`
- **droid** — Factory Droid CLI，默认通过 `~/.bashrc` Gemini 环境变量控制，codex profile 通过 `~/.factory/settings.json` customModels
- **all** — 以上全部

---

## 命令行用法

脚本位置：`~/bin/switch-api`（Python 脚本，v1.5.0）

### 语法

```bash
switch-api [--force] <参数1> [参数2] [参数3]
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

**方式三：三参数（OpenClaw / Droid + Profile）**
```bash
switch-api openclaw duck <profile>
switch-api openclaw quotio <profile>
switch-api openclaw antigravity <profile>
switch-api droid quotio <profile>
```
- OpenClaw `<profile>` = `default` | `opus` | `sonnet` | `gemini` | `gemini3`
- Droid `<profile>` = `default` | `gemini` | `codex`

**方式四：查看状态**
```bash
switch-api status
```

**选项：**
- `--force` — 跳过 pre-flight 连接检查（隧道检测）

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
switch-api openclaw duck                    # 默认 Claude Opus 4.6
switch-api openclaw duck gemini3            # Duck Gemini 3 ⚠️
switch-api openclaw duck sonnet             # Duck Sonnet 4.6
switch-api openclaw quotio                  # 默认 Opus 4.6 Thinking
switch-api openclaw quotio gemini3          # Quotio Gemini 3 ⚠️
switch-api openclaw antigravity             # 默认 Opus 4.6 Thinking
switch-api openclaw antigravity gemini3     # Antigravity Gemini 3 ⚠️

# ─── 只切 Codex ────────────────────────────────
switch-api codex duck
switch-api codex quotio
switch-api codex antigravity

# ─── 只切 Droid ────────────────────────────────
switch-api droid duck                       # Duck Gemini
switch-api droid quotio                     # Quotio Gemini (默认)
switch-api droid quotio codex               # Quotio GPT-5.3 Codex ⭐
switch-api droid antigravity                # Antigravity Gemini
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
- quotio → `GEMINI_MODEL=gemini-3.1-pro-high`（env vars，默认）
- quotio codex → `gpt-5.3-codex`（写入 `~/.factory/settings.json` customModels，OpenAI provider）
- antigravity → `GEMINI_MODEL=gemini-3.1-pro-high`（env vars）

> **Droid codex profile** 说明：Codex 模型使用 OpenAI 协议，无法通过 GEMINI_* 环境变量配置。
> 切换到 codex profile 时，脚本写入 `~/.factory/settings.json` 的 `customModels` 字段。
> 在 Droid 中通过 `/model` 选择 "Quotio gpt-5.3-codex"（Custom Models 分类下）。
> 切换回其他 profile（如 `switch-api droid quotio`）时自动清除 customModels。

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

- 切换前 pre-flight 探测目标 provider 连接性
- 切换到 `quotio` 时检查 `QUOTIO_API_KEY`
- 切换到 `antigravity` 时检查 `ANTIGRAVITY_API_KEY`
- 密钥快照保存到 `~/.config/switch-api/credentials.json`（权限 600）
- Key 配置在 `~/.bashrc` 中，脚本自动读取 `export` 行

---

## 文件清单

```
~/bin/switch-api                              主切换脚本 (v1.5.0)
~/.bashrc                                     环境变量 (API Keys) + 快捷别名
~/.claude/settings.json                       Claude Code 配置
~/.openclaw/openclaw.json                     OpenClaw 主配置
~/.openclaw/agents/main/agent/models.json     OpenClaw 模型配置
~/.openclaw/agents/main/agent/auth.json       OpenClaw 认证
~/.openclaw/agents/main/agent/auth-profiles.json  OpenClaw 认证 Profile
~/.openclaw/workspace/TOOLS.md                OpenClaw /switch 指令说明
~/.codex/config.toml                          Codex 配置
~/.factory/settings.json                      Droid customModels（codex profile）
~/.config/switch-api/credentials.json         Provider 密钥快照
~/.config/switch-api/provider-models.json     Provider 模型目录
~/logs/openclaw.log                           OpenClaw 启动日志
```
