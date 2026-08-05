# switch-api Skills

This repository ships repo-local Codex/OpenClaw skills for `switch-api`.

## Available skills

- `api-provider-switch`
  - Use when the task is to inspect current provider state, list models, switch providers, or switch to a specific model.
- `api-provider-admin`
  - Use when the task is to register/update/remove custom providers, save API keys, or bootstrap `~/.env` / shell loading for `switch-api`.

## Layout

- `skills/api-provider-switch/SKILL.md`
- `skills/api-provider-admin/SKILL.md`

## Sync

仓库内的 `skills/` 是 source of truth。本机 Claude Code 安装副本位于：

- `~/.claude/skills/api-provider-switch`
- `~/.claude/skills/api-provider-admin`

更新仓库 skill 后，需要把对应 `SKILL.md` 同步到上述目录（当前是拷贝，不是 symlink）。
`switch-api` 没有独立 MCP server，只提供这两个 repo-local skills。
