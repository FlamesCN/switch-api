# WP-1.0 API Provider 切换系统

> **状态**: ✅ 已实现  
> **创建日期**: 2026-02-26  
> **涉及工具**: Claude Code · OpenClaw · Codex · Droid

---

## 1. 背景与目标

本地电脑运行 Quotio 代理 (port 8317)，通过 Cloudflare Tunnel 暴露为公网地址 `https://api.ancientechoes.ai`。
需要让服务器上的所有 AI 工具能在 **DuckCoding 中转** 和 **Quotio 隧道** 之间自由切换。

### 核心需求

1. **统一切换** — 一条命令切换所有工具，也支持单独切换
2. **Telegram 控制** — 通过 OpenClaw bot 的 `/switch` 命令远程切换
3. **状态可见** — 随时查看各工具当前连接的 provider
4. **安全备份** — 每次切换自动备份配置文件

## 2. Provider 定义

```
Provider    标识      地址                            用途
─────────────────────────────────────────────────────────────
DuckCoding  duck      https://jp.duckcoding.com       第三方中转，稳定
Quotio      quotio    https://api.ancientechoes.ai    本地隧道，Opus/Gemini3
```

### 隧道架构

```
本地电脑 Quotio (localhost:8317)
    ↓ Cloudflare Tunnel (ID: 270e9644-b793-4d55-8f69-b4e4bc3f7ccb)
    ↓
https://api.ancientechoes.ai
    ↓
新加坡服务器上的 CC / OpenClaw / Codex / Droid
```

## 3. 各工具切换方案

### 3.1 Claude Code (cc)

- **配置文件**: `~/.claude/settings.json`
- **切换字段**: `env.ANTHROPIC_BASE_URL` + `env.ANTHROPIC_AUTH_TOKEN`
- **duck 值**: `https://jp.duckcoding.com` + DuckCoding API Key
- **quotio 值**: `https://api.ancientechoes.ai` + Quotio API Key
- **模型**: `claude-opus-4-5-20251101-thinking` (不变)

### 3.2 OpenClaw

- **配置文件**: `~/.openclaw/openclaw.json` + `~/.openclaw/agents/main/agent/models.json`
- **切换字段**: `agents.defaults.model.primary` + `models.providers.*`
- **duck 值**: `duckcoding/gemini-3.1-pro-preview` → `jp.duckcoding.com/v1`
- **quotio 值**: `quotio/gemini-3-pro-preview` → `api.ancientechoes.ai/v1`
- **特殊处理**: 切换后需重启 gateway（kill 旧进程 → 从 `/opt/openclaw` 重新启动）

### 3.3 Codex

- **配置文件**: `~/.codex/config.toml`
- **切换字段**: `model_provider` (duckcoding / quotio)
- **已配置 provider**:
  - `[model_providers.duckcoding]` → `jp.duckcoding.com/v1`
  - `[model_providers.quotio]` → `api.ancientechoes.ai/v1`
  - `[model_providers.openai-official]` → `api.openai.com/v1`

### 3.4 Droid (Gemini CLI)

- **配置方式**: `~/.bashrc` 中的环境变量
- **切换字段**: `GEMINI_BASE_URL` + `GEMINI_API_KEY`
- **注意**: 切换后需 `source ~/.bashrc` 才生效

## 4. 实现方案

### 4.1 主切换脚本 `~/bin/switch-api`

```
用法: switch-api <tool> <provider>
  tool:     cc | openclaw | codex | droid | all | status
  provider: duck | quotio

核心逻辑:
  cc       → jq 修改 ~/.claude/settings.json
  openclaw → jq 修改 openclaw.json + models.json → kill + restart gateway
  codex    → sed 修改 ~/.codex/config.toml 的 model_provider
  droid    → sed 修改 ~/.bashrc 的 GEMINI_BASE_URL
  all      → 依次执行上述四个
  status   → 读取各配置文件，检测当前 provider
```

### 4.2 Bash 快捷别名 (在 ~/.bashrc)

```
api-status    → switch-api status        查看状态
api-duck      → switch-api all duck      全部切到 Duck
api-quotio    → switch-api all quotio    全部切到 Quotio
cc-duck       → switch-api cc duck       单切 CC
cc-quotio     → switch-api cc quotio
oc-duck       → switch-api openclaw duck 单切 OpenClaw
oc-quotio     → switch-api openclaw quotio
cx-duck       → switch-api codex duck    单切 Codex
cx-quotio     → switch-api codex quotio
cxq           → codex -c model_provider="quotio"  (临时，不改配置)
cxo           → codex -c model_provider="openai-official"
```

### 4.3 Telegram /switch 命令

通过 OpenClaw 的 `TOOLS.md` 注册指令映射：

```
/switch duck              → switch-api all duck
/switch quotio            → switch-api all quotio
/switch cc duck           → switch-api cc duck
/switch openclaw quotio   → switch-api openclaw quotio
/switch status            → switch-api status
/api                      → switch-api status
```

OpenClaw agent 收到消息后通过 shell exec 执行脚本，返回结果。

## 5. OpenClaw Gateway 重启流程

切换 OpenClaw provider 时的自动重启逻辑：

```
1. pkill -f "openclaw-gateway"
2. pkill -f "npm exec openclaw gateway"
3. sleep 2 (等待进程退出)
4. cd /opt/openclaw && npx openclaw gateway --port 18789 run (nohup 后台)
5. sleep 4 (等待启动)
6. pgrep "openclaw-gateway" 验证启动成功
7. 日志输出到 ~/logs/openclaw.log
```

## 6. 备份策略

每次切换自动生成时间戳备份：

```
~/.claude/settings.json.bak.switch-20260226-152900
~/.openclaw/openclaw.json.bak.switch-20260226-152900
~/.openclaw/agents/main/agent/models.json.bak.switch-20260226-152900
~/.codex/config.toml.bak.switch-20260226-152900
```

## 7. 环境变量

```bash
# ~/.bashrc 中需设置
export QUOTIO_API_KEY=""          # Quotio 代理的 API Key (待填入)
export DUCKCODING_API_KEY="..."   # DuckCoding Key (已配置)
export ANTHROPIC_API_KEY="..."    # Anthropic/Duck Key (已配置)
export GEMINI_API_KEY="..."       # Gemini/Duck Key (已配置)
```

## 8. 文件清单

```
~/bin/switch-api                              主切换脚本
~/.bashrc                                     环境变量 + aliases
~/.claude/settings.json                       CC 配置
~/.openclaw/openclaw.json                     OpenClaw 主配置
~/.openclaw/agents/main/agent/models.json     OpenClaw 模型配置
~/.openclaw/workspace/TOOLS.md                OpenClaw /switch 指令说明
~/.codex/config.toml                          Codex 配置
~/docs/usage/switch-api.md                    使用文档
~/docs/plans/WP-1.0-api-provider-switch.md    本规划文档
~/logs/openclaw.log                           OpenClaw 启动日志
```

## 9. 待办 / 后续

- [ ] 填入 `QUOTIO_API_KEY`（等本地 Quotio 隧道上线后确认）
- [ ] 验证 Quotio 隧道端到端连通性（目前返回 1033，隧道未上线）
- [ ] 考虑将 OpenClaw 注册为 systemd user service 以提高可靠性
- [ ] 可选：添加更多 provider（如直连 Anthropic 官方）
