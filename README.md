# switch-api
Unified API provider switcher for `duck` and `quotio` across:
- Claude Code (`cc`)
- OpenClaw (`openclaw`)
- Codex (`codex`)
- Droid (`droid`)

## Version
See `VERSION`.

## Commands
- `switch-api status`
- `switch-api duck`
- `switch-api quotio`
- `switch-api all duck|quotio`
- `switch-api cc|openclaw|codex|droid duck|quotio`

## Security
- Real keys must not be committed.
- Use local credential snapshot at: `~/.config/switch-api/credentials.json` (600).
- `examples/credentials.example.json` is redacted placeholder only.

## Project layout
- `bin/switch-api` - executable Python CLI
- `docs/usage/switch-api.md` - usage guide
- `docs/plans/WP-1.0-api-provider-switch.md` - plan/design notes
- `examples/credentials.example.json` - redacted example
