# IDE plugins

Each IDE has its own marketplace manifest at the repo root. Plugin directories live here, grouped by target IDE.

## Layout

```text
plugins/
├── cursor/          # Cursor plugins (.cursor-plugin/plugin.json per plugin)
│   └── (see cursor-plugin/ at repo root for now)
└── claude/          # Claude Code plugins (.claude-plugin/plugin.json per plugin)
    └── (add plugins here)
```

## Conventions

- **Cursor plugins** use `.cursor-plugin/plugin.json` and are listed in [`.cursor-plugin/marketplace.json`](../.cursor-plugin/marketplace.json).
- **Claude Code plugins** use `.claude-plugin/plugin.json` and are listed in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json).
- Marketplace entry `name` must match the plugin manifest `name`.
- Marketplace entry `source` is the relative path from the repo root to the plugin directory.
- A plugin directory may include manifests for multiple IDEs when components overlap; list it in each IDE marketplace that supports it.

## Adding a Cursor plugin

1. Add a directory (for example `plugins/cursor/my-plugin/` or a top-level sibling like `cursor-plugin/`).
2. Add `.cursor-plugin/plugin.json` inside that directory.
3. Register in `.cursor-plugin/marketplace.json`.

## Adding a Claude Code plugin

1. Add a directory under `plugins/claude/my-plugin/`.
2. Add `.claude-plugin/plugin.json` inside that directory.
3. Register in `.claude-plugin/marketplace.json` (remove the empty `plugins` array once the first entry is added).
