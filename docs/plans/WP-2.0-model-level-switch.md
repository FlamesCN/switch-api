# WP-2.0 模型级切换 + 列表/检查功能

> **状态**: ✅ 已实现  
> **创建日期**: 2026-02-28  
> **前置**: WP-1.0 API Provider 切换系统（已实现）

## 问题

当前 `/switch` 只支持 provider 级别切换（duck/quotio/antigravity），模型由 profile 预定义。用户需要：
1. 直接指定模型切换，如 `/switch openclaw quotio gpt-5.3-codex`
2. 查看某 provider 可用模型列表，如 `/switch list quotio`
3. 检查当前各工具的模型状态和可用性

## 当前架构

工具 × Provider × Profile 三层映射：`switch-api <tool> <provider> [profile]`

每个工具支持的模型 family 不同：
- **cc** (Claude Code): 仅 Claude（anthropic API）— **不支持 GPT/Gemini**
- **openclaw**: Claude + Gemini（通过 sub-provider），模型写入 `openclaw.json` 的 `primary`
- **codex**: Claude + OpenAI（通过 model_provider config）
- **droid**: Gemini（env vars）或 OpenAI（customModels）
- **gemini**: 仅 Gemini（env vars）

Provider 模型目录常量：
- `QUOTIO_AVAILABLE_MODELS` — 23 个（Claude 2 + Gemini 7 + OpenAI 11 + misc 3）
- `DUCK_ANTHROPIC_MODELS` — 18 个 Claude 模型
- `DUCK_GEMINI_MODELS` — 10 个 Gemini 模型
- `DUCK_CODEX_MODELS` — 91 个 GPT/Codex 模型

网络约束：
- Quotio (`api.ancientechoes.ai`) 的 Cloudflare 拦截 Python urllib，必须用 `curl`
- OpenAI 官方 (`api.openai.com`) 必须走本地 Xray 代理 `http://127.0.0.1:1081`，防止 IP 暴露

## 设计方案

### 1. `list` 子命令 — 查看可用模型

**语法：**
- `switch-api list` — 列出所有 provider 的模型
- `switch-api list quotio` — 只列 quotio 的模型
- `switch-api list duck` — 列 duck 3 个 key 的模型

**Telegram:** `/switch list`、`/switch list quotio`

**实现：**
- 新函数 `cmd_list_models(provider: str | None)`
- 纯本地，从常量读取，不发网络请求
- 按 family 分组显示（Claude / Gemini / OpenAI / 其他）
- 每个模型标注所属 provider key（duck 有 3 个 key 需区分）
- 同时标注该模型可用于哪些工具（cc/openclaw/codex/droid/gemini）

**输出示例：**
```
═══ Quotio 可用模型 (23) ═══
  Claude (cc, openclaw, codex):
    claude-opus-4-6-thinking
    claude-sonnet-4-6
  Gemini (openclaw, droid, gemini):
    gemini-2.5-flash, gemini-3.1-pro-high, ...
  OpenAI (codex, droid):
    gpt-5, gpt-5-codex, gpt-5.3-codex, ...
  其他:
    gpt-oss-120b-medium, tab_flash_lite_preview, ...
```

### 2. `check` 子命令 — 当前模型状态 + 在线验证

**语法：**
- `switch-api check` — 本地检查（默认）
- `switch-api check --online` — 在线验证每个工具当前模型是否可调用

**Telegram:** `/switch check`、`/switch check online`

**实现：**
- 新函数 `cmd_check(cfg, keys, online=False)`
- 读取每个工具的配置文件，提取当前 provider 和模型名
- 对照模型目录常量判断是否在列表内（✅ 在目录 / ⚠️ 不在目录）
- `--online` 模式：对每个工具当前的 provider+model 发实际 API 请求验证

**输出示例：**
```
═══ Model Status ═══
  cc         🔗 quotio    claude-opus-4-6-thinking   ✅
  openclaw   🔗 quotio    quotio/claude-opus-4-6..   ✅
  codex      🔗 quotio    claude-sonnet-4-6          ✅
  droid      🔗 quotio    gemini-3.1-pro-high        ✅
  gemini     🔗 quotio    gemini-3.1-pro-high        ✅
═══════════════════
```

**在线验证关键约束：**
- **必须走 provider 的 API 路径**，不能直接从服务器发请求
- Quotio → `curl https://api.ancientechoes.ai/v1/chat/completions`
- Duck → `curl https://api.duckcoding.ai/v1/chat/completions`
- Antigravity → `curl https://tools.ancientechoes.ai/v1/chat/completions`
- **OpenAI 官方 → `curl --proxy http://127.0.0.1:1081 https://api.openai.com/v1/chat/completions`**
- 统一用 `subprocess.run(["curl", ...])` 发请求（避免 urllib 被 Cloudflare 拦截）
- 发送 `max_tokens=1` 的最小请求，验证模型可调用
- 新函数 `probe_model(provider, model, keys) -> (ok, reason)`

### 3. 模型级切换（核心功能）

**语法（必须指定工具）：**
- `switch-api <tool> <provider> <model>`
- `switch-api openclaw quotio gpt-5.3-codex`
- `switch-api codex quotio gpt-5.3-codex`
- `switch-api droid quotio gpt-5.3-codex`

**Telegram:** `/switch openclaw quotio gpt-5.3-codex`

**不支持省略工具的自动路由**（避免误切）。用户必须明确指定切哪个工具。

**工具 × 模型 family 兼容矩阵：**
- **cc**: 仅 `claude-*` — 切 GPT/Gemini 时 cc 保持不动
- **openclaw**: `claude-*` + `gemini-*`（通过对应 sub-provider）
- **codex**: `claude-*` + `gpt-*`
- **droid**: `gemini-*`（默认）+ `gpt-*`（codex profile）
- **gemini**: 仅 `gemini-*`

**验证流程：**
1. 检查 model 是否在 provider 的模型目录常量中（`QUOTIO_AVAILABLE_MODELS` 等）
2. 不在目录 → 报错 + 提示 `switch-api list <provider>` 查看可用模型
3. 判断 model family（`claude-*` / `gemini-*` / `gpt-*`）
4. 检查 tool 是否兼容该 family → 不兼容则报错（如 `cc` + `gpt-*`）
5. 执行切换（复用现有 switch_* 函数，传入指定 model）
6. `--force` 跳过目录检查（用于目录未更新但模型实际可用的情况）

**对现有 switch_* 函数的改造：**
- 各 `switch_*` 函数新增可选参数 `model: str = ""`
- 当 `model` 非空时，使用指定模型而非默认/profile 映射的模型
- 当 `model` 为空时，行为不变（向后兼容）

### 4. parse_args 改造

当前返回 `(tool, provider, profile)`。扩展为：
- 1 arg: `status` | `check` | `list` | `<provider>`
- 2 args: `list <provider>` | `check --online` | `<tool> <provider>`
- 3 args: `<tool> <provider> <model_or_profile>`

新增 `is_model_name(s)` 辅助函数：
- 以 `claude-` / `gemini-` / `gpt-` 开头 → True
- 包含 `.`（如 `gpt-5.3-codex`）→ True
- 在已知 profile 名集合中 → False
- 其他 → True（宽松匹配，倾向当作模型名）

三参数模式 `<tool> <provider> <arg3>` 判断逻辑：
- 如果 arg3 是已知 profile → 走现有 profile 逻辑
- 否则 → 走模型级切换逻辑

### 5. TOOLS.md 更新

在 OpenClaw workspace `~/.openclaw/workspace/TOOLS.md` 中加入：
- `/switch list [provider]` 命令说明
- `/switch check [online]` 命令说明
- `/switch <tool> <provider> <model>` 模型级切换说明
- 工具 × 模型兼容矩阵

## 文件变更

- `~/bin/switch-api` — parse_args 扩展、新增 cmd_list_models / cmd_check / probe_model / is_model_name、switch_* 函数增加 model 参数
- `~/.openclaw/workspace/TOOLS.md` — 新命令文档
- `~/code/switch-api/docs/usage/switch-api.md` — 用户文档
- `~/code/switch-api/bin/switch-api` — 同步副本

## 实施阶段

- **Phase 1**: `list` 子命令（最简单，纯本地）
- **Phase 2**: `check` 子命令（本地 + 在线验证）
- **Phase 3**: 模型级切换（parse_args 改造 + switch_* 适配）
- **Phase 4**: TOOLS.md + 用户文档更新
