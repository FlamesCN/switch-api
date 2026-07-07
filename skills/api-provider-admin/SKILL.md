---
name: api-provider-admin
description: '维护 switch-api 的 key 与自定义 provider 时使用：写 key、注册/删除 custom provider、导入/导出 provider bundle、排查 ~/.env 与 shell source 关系。'
metadata: { "openclaw": { "emoji": "🧰", "requires": { "anyBins": ["switch-api"] }, "os": ["linux"] } }
---

# API Provider Admin Skill

## 目标

当用户要做以下事情时，使用本 skill：
- 保存 / 更新 API key
- 注册自定义 provider
- 删除自定义 provider
- 导入 / 导出 provider bundle
- 检查 `~/.env`、`~/.bashrc`、`~/.zshrc` 是否正确联动

## Key 写入

```bash
switch-api key set <ENV_KEY> <VALUE>
switch-api key list
```

行为：
- 写入 `~/.config/switch-api/credentials.json`
- 写入 `~/.env`
- 自动补齐 shell 对 `~/.env` 的加载：
  - `~/.zshrc`
  - `~/.bashrc`

## 自定义 OpenAI-compatible provider

```bash
switch-api provider add-openai <name> <base_url> <env_key> <default_model>
switch-api provider add-openai myrelay https://relay.example.com/v1 MY_RELAY_API_KEY gpt-5.4 --disable-image-generation
```

适用工具：
- `codex`
- `openclaw`
- `droid`
- `hermes`

## 自定义 Anthropic-compatible provider

```bash
switch-api provider add-anthropic <name> <base_url> <env_key> <default_model>
switch-api provider add-anthropic myrelay https://relay.example.com/anthropic MY_RELAY_CC_API_KEY claude-sonnet-4-6 --env CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

适用工具：
- `cc`

可重复追加：

```bash
switch-api provider add-openai myrelay ...
switch-api provider add-anthropic myrelay ...
```

这样同一个 `myrelay` 名称会同时服务：
- `cc`
- `codex`
- `openclaw`
- `droid`
- `hermes`

## 检查 / 删除

```bash
switch-api provider list
switch-api provider rm <name>
```

## 导出 / 导入

```bash
switch-api provider export <name> [path|-]
switch-api provider export-all [path|-]
switch-api provider export-all ./providers.bundle.json --with-secrets

switch-api provider import ./providers.bundle.json
switch-api provider import ./providers.bundle.json --replace
```

规则：
- 默认导出不带 secret
- `--with-secrets` 才会导出 `env_values`
- 导入时若 bundle 带 `env_values`，会同时写入：
  - `~/.config/switch-api/credentials.json`
  - `~/.env`
  - 并自动确保 shell 加载 `~/.env`
- 默认导入是 merge
- `--replace` 只替换 provider 注册表，不主动清理旧 credentials

## 注册后切换

```bash
switch-api cc myrelay
switch-api codex myrelay
switch-api myrelay
```
