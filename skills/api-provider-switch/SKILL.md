---
name: api-provider-switch
description: '切换 AI 工具的 API provider / 模型，或查看当前 provider / 可用模型时使用。覆盖 cc、openclaw、codex、droid、gemini、hermes，以及 repo 内自定义 provider。'
metadata: { "openclaw": { "emoji": "🔀", "requires": { "anyBins": ["switch-api"] }, "os": ["linux"] } }
---

# API Provider 切换 Skill

## 工具

`~/bin/switch-api`（v2.0.6）— 统一切换：
- Claude Code (`cc`, alias: `claude`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)
- Gemini CLI (`gemini`)
- Hermes (`hermes`)

## 常用查询

```bash
switch-api status
switch-api check
switch-api check --online
switch-api list
switch-api list quotio
switch-api list myrelay
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
```

## 自定义 provider

支持两类自定义 provider：

1. **OpenAI-compatible**
   - 工具：`codex` / `openclaw` / `droid` / `hermes`
2. **Anthropic-compatible**
   - 工具：`cc`

同一个 provider 名称可以同时注册这两套配置。

示例：

```bash
switch-api provider add-openai myrelay https://relay.example.com/v1 MY_RELAY_API_KEY gpt-5.4
switch-api provider add-anthropic myrelay https://relay.example.com/anthropic MY_RELAY_CC_API_KEY claude-sonnet-4-6

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

## 模型兼容规则

- `cc`: 默认 `claude-*`；`flames` 下也可走 `gpt-*` / `deepseek-v4-*`
- `openclaw`: `claude-*` + `gemini-*` + 部分 `gpt-*`
- `codex`: `gpt-*`
- `droid`: `gemini-*` + `gpt-*`
- `gemini`: `gemini-*`
- `hermes`: `gpt-*` / `gemini-*`（取决于 provider）

模型级切换：

```bash
switch-api <tool> <provider> <model>
```

例如：

```bash
switch-api codex quotio gpt-5.3-codex
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
