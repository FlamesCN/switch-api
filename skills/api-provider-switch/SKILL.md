---
name: api-provider-switch
description: '切换 AI 工具的 API 后端（Provider / 模型）。当用户要求：(1) 切换 API provider, (2) 查看/列出可用模型, (3) 检查当前模型状态, (4) 切换到指定模型时，使用此 skill。触发词：/switch, /切换, /api, 切换到, 换成, 用XX模型, 模型列表'
metadata: { "openclaw": { "emoji": "🔀", "requires": { "anyBins": ["switch-api"] }, "os": ["linux"] } }
---

# API Provider 切换 Skill

## 工具

`~/bin/switch-api`（v2.0.2）— 一键切换所有 AI 工具的 API 后端和模型。

## Providers

| 代号 | 名称 | 地址 | 图标 |
|------|------|------|------|
| duck | DuckCoding | api.duckcoding.ai | 🦆 |
| quotio | Quotio 隧道 | api.ancientechoes.ai | 🔗 |
| quotio_local | Quotio Local | 127.0.0.1:8317 (本地 app) | 🔗 |
| antigravity | Antigravity-tools | tools.ancientechoes.ai | 🚀 |
| openai | OpenAI 官方 | api.openai.com (via xray proxy) | 🔑 |
| openrouter | OpenRouter | openrouter.ai (free models) | 🌐 |
| flames | Flames NewAPI | www.flamescn.vip | 🔥 |
| deepseek | DeepSeek 官方 Anthropic API | api.deepseek.com/anthropic | 🧠 |
| icodeeasy | iCodeEasy | api.icodeeasy.cc | 🧊 |

## 工具 × 模型兼容矩阵

**必须遵守，违反会报错：**

- **cc** (Claude Code): 默认 `claude-*`；当 provider 为 `flames` 时，也支持 `gpt-*` 和 `deepseek-v4-*`
- **openclaw**: `claude-*` + `gemini-*`
- **codex**: 仅 `gpt-*` — Claude/Gemini 切换时 **跳过 codex**
- **droid**: `gemini-*` + `gpt-*`
- **gemini**: 仅 `gemini-*`

### DeepSeek 速查

```bash
switch-api cc deepseek
switch-api claude deepseek
switch-api cc deepseek deepseek-v4-pro
switch-api cc deepseek deepseek-v4-flash
```

## 命令速查

### 查询类（只读，随时可用）

```bash
# 查看当前 provider
switch-api status

# 查看各工具当前模型 + 目录匹配
switch-api check

# 在线验证模型是否真正可用（走 provider API 路径）
switch-api check --online

# 列出所有 provider 可用模型
switch-api list

# 列出指定 provider 可用模型
switch-api list quotio
switch-api list duck
switch-api list antigravity
```

### 全量切换（切所有工具到同一 provider）

```bash
switch-api duck
switch-api quotio
switch-api antigravity
```

### 单工具切换（只切指定工具）

```bash
switch-api cc <provider>
switch-api openclaw <provider>
switch-api codex <provider>
switch-api droid <provider>
switch-api gemini <provider>
```

### Profile 切换（预定义模型组合）

```bash
switch-api openclaw quotio gemini3     # Quotio + Gemini 模型
switch-api openclaw duck sonnet        # Duck + Sonnet 模型
switch-api openclaw icodeeasy          # iCodeEasy + Claude Sonnet 4.6
switch-api droid quotio codex          # Droid + GPT-5.3 Codex
```

### Quotio Local

```bash
switch-api quotio_local                        # codex+droid → Quotio Local
switch-api droid quotio_local                  # Droid → Quotio Local
switch-api droid quotio_local gpt-5.3-codex-high  # 指定模型+思考等级
```

### 模型级切换（指定具体模型）

```bash
switch-api <tool> <provider> <model>

# 示例
switch-api codex quotio gpt-5.3-codex
switch-api droid quotio gpt-5.3-codex         # Quotio 互联网直连
switch-api droid quotio_local gpt-5.3-codex-high  # 本地代理 + 高思考
switch-api openclaw quotio claude-sonnet-4-6
switch-api openclaw icodeeasy claude-sonnet-4-6
switch-api cc duck claude-opus-4-6
switch-api gemini quotio gemini-3.1-pro-high
```

### 思考等级（Thinking Level）

GPT 模型后缀控制思考等级：
- (无后缀) = 默认/auto
- `-low` = 低思考
- `-medium` = 中等思考
- `-high` = 高思考
- `-xhigh` = 超高思考

> 注意：`-max` 是 5.1 系列独有模型变体，不是思考等级。

### Droid 非交互模式

切换后 Droid 会自动设置 `sessionDefaultSettings.model`，交互模式直接生效。

非交互模式使用 `-m` 指定 custom model ID：

```bash
# 格式: custom:{displayName 空格替换为 -}-0
droid exec -m "custom:Quotio-gpt-5.3-codex-0" "你的 prompt"

# 其他 provider 同理
droid exec -m "custom:Quotio-Local-gpt-5.3-codex-0" "prompt"
droid exec -m "custom:OpenRouter-stepfun/step-3.5-flash:free-0" "prompt"
```

> 切换 provider 时脚本自动更新 `~/.factory/settings.json` 的 `sessionDefaultSettings.model`，
> 切回 Gemini provider 时自动清除 custom 默认值。

## 决策流程

当用户要求切换时，按以下流程处理：

### 1. 用户说 "切到 quotio" / "用 duck"
→ 全量切换：`switch-api <provider>`

### 2. 用户说 "codex 切到 quotio" / "只切 openclaw"
→ 单工具切换：`switch-api <tool> <provider>`

### 3. 用户说 "用 gpt-5.3-codex" / "切到某个具体模型"
→ 判断模型 family，选择兼容的工具：
- `gpt-*` → `switch-api codex <provider> <model>` 和/或 `switch-api droid <provider> <model>`
- `claude-*` → `switch-api cc <provider> <model>` 和/或 `switch-api openclaw <provider> <model>`
- `gemini-*` → `switch-api openclaw <provider> <model>` 和/或 `switch-api droid <provider> <model>`

**重要**：每个工具要单独执行命令，不能省略 tool 参数。

### 4. 用户说 "有什么模型" / "看看可用模型"
→ `switch-api list` 或 `switch-api list <provider>`

### 5. 用户说 "检查下" / "模型状态"
→ `switch-api check` 或 `switch-api check --online`

### 6. 不确定用户要切哪个 provider
→ 先问用户要用哪个 provider，或者运行 `switch-api list` 让用户选

## 错误处理

- 模型不在 provider 目录 → 提示 `switch-api list <provider>` 查看可用模型
- 不兼容的 tool+model → 告知用户该工具不支持此模型 family
- Provider 不可达 → 建议用 `--force` 跳过 pre-flight 检查，或换 provider
- 切换后 OpenClaw 会自动重启 gateway（如果切了 openclaw 或 all）

## 切换后

- **始终**运行 `switch-api status` 或 `switch-api check` 展示结果
- 如果用户在 Droid/Gemini CLI 中，提醒执行 `source ~/.bashrc` 生效
- 如果切到 openai provider，提醒需要 xray proxy 在线

## Quotio 可用模型速查

**Claude**: claude-opus-4-6-thinking, claude-sonnet-4-6
**Gemini**: gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3-flash, gemini-3-pro-high, gemini-3.1-flash-image, gemini-3.1-pro-high, gemini-3.1-pro-low
**OpenAI**: gpt-5, gpt-5-codex, gpt-5-codex-mini, gpt-5.1, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini, gpt-5.2, gpt-5.2-codex, gpt-5.3-codex, gpt-5.3-codex-spark
**其他**: gpt-oss-120b-medium, tab_flash_lite_preview, tab_jump_flash_lite_preview
