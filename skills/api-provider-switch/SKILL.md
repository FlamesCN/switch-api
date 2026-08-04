---
name: api-provider-switch
description: '切换 AI 工具的 API provider / 模型，或查看当前 provider / 可用模型时使用。覆盖 cc、openclaw、codex、droid、gemini、hermes、grok，以及 repo 内自定义 provider。'
metadata: { "openclaw": { "emoji": "🔀", "requires": { "anyBins": ["switch-api"] }, "os": ["linux", "darwin"] } }
---

# API Provider 切换 Skill

## 工具

`switch-api`（v2.0.8）— 统一切换：
- Claude Code (`cc`, alias: `claude`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)
- Gemini CLI (`gemini`)
- Hermes (`hermes`)
- Grok (`grok`)

## 常用查询

```bash
switch-api status
switch-api check
switch-api check --online
switch-api list
switch-api list quotio
switch-api list myrelay
switch-api list myrelay --online
switch-api probe myrelay
switch-api doctor myrelay
```

## 常用切换

```bash
switch-api duck
switch-api quotio
switch-api flames

switch-api cc deepseek
switch-api openclaw quotio
switch-api codex flames
switch-api droid molifang
switch-api hermes aiwave
switch-api grok flames
switch-api grok xai
```

## 自定义 provider

支持两类自定义 provider：

1. **OpenAI-compatible**
   - 工具：`codex` / `openclaw` / `droid` / `hermes` / `grok`
2. **Anthropic-compatible**
   - 工具：`cc`

同一个 provider 名称可以同时注册这两套配置。

示例：

```bash
switch-api provider add-openai myrelay https://relay.example.com/v1 MY_RELAY_API_KEY gpt-5.4
switch-api provider add-anthropic myrelay https://relay.example.com/anthropic MY_RELAY_CC_API_KEY claude-sonnet-4-6
switch-api provider sync-models myrelay

switch-api cc myrelay
switch-api codex myrelay
switch-api myrelay
```

## Key 管理

```bash
switch-api key set MY_RELAY_API_KEY sk-xxx
switch-api key set MY_RELAY_CC_API_KEY sk-ant-xxx
switch-api key list
```

`key set` 会同时：
- 写入 `~/.config/switch-api/credentials.json`
- 写入 `~/.env`
- 自动确保 `~/.zshrc` / `~/.bashrc` 会加载 `~/.env`

如果要迁移 / 备份自定义 provider，也可以配合：

```bash
switch-api provider sync-models myrelay
switch-api provider export myrelay ./myrelay.provider.json
switch-api provider export-all ./providers.bundle.json --with-secrets
switch-api provider import ./providers.bundle.json
```

## anyrouter 示例

```bash
switch-api key set ANYROUTER_API_KEY sk-xxx
switch-api provider add-openai anyrouter https://anyrouter.top/v1 ANYROUTER_API_KEY gpt-5.5
switch-api provider add-anthropic anyrouter https://anyrouter.top ANYROUTER_API_KEY claude-opus-4-8 --env ANTHROPIC_BETAS=context-1m-2025-08-07
switch-api list anyrouter --online
switch-api doctor anyrouter
switch-api cc anyrouter
```

说明：
- custom provider 现在会自动探测 `/v1/models`
- 模型缓存会写入：
  - `~/.config/switch-api/custom-providers.json`
  - `~/.config/switch-api/provider-models.json`

## 模型兼容规则

- `cc`: 默认 `claude-*`；`flames` 下也可走 `gpt-*` / `deepseek-v4-*`
- `openclaw`: `claude-*` + `gemini-*` + 部分 `gpt-*`
- `codex`: `gpt-*`；DeepSeek 官方 provider 额外支持 `deepseek-v4-flash`
- `droid`: `gemini-*` + `gpt-*`
- `gemini`: `gemini-*`
- `hermes`: `gpt-*` / `gemini-*`（取决于 provider）
- `grok`: `grok-*`；在 Flames / 自定义 OpenAI-compatible relay 下也可用 `gpt-*`

模型级切换：

```bash
switch-api <tool> <provider> <model>
```

例如：

```bash
switch-api codex quotio gpt-5.3-codex
switch-api codex deepseek deepseek-v4-flash
switch-api cc deepseek deepseek-v4-pro
switch-api openclaw quotio claude-sonnet-4-6
```

## 执行后建议

切换后建议马上运行：

```bash
switch-api status
# 或
switch-api check
```
