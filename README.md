# mcp-plugin-test-marketplace

Internal multi-IDE plugin marketplace for in-development 1Password plugins that require marketplace installs.

Each supported IDE reads its own marketplace manifest at the repo root. Plugin directories are siblings (or under `plugins/`) and contain per-IDE manifests inside `.cursor-plugin/` or `.claude-plugin/`.

## Supported IDEs

| IDE | Marketplace manifest | Plugin manifest |
|-----|---------------------|-----------------|
| [Cursor](https://cursor.com/docs/plugins) | [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json) | `<plugin>/.cursor-plugin/plugin.json` |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/plugins) | [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | `<plugin>/.claude-plugin/plugin.json` |

Register each manifest URL separately in the target IDE's team or org settings.

## Repository structure

```text
mcp-plugin-test-marketplace/
├── .cursor-plugin/
│   └── marketplace.json          # Cursor plugin index
├── .claude-plugin/
│   └── marketplace.json          # Claude Code plugin index (empty until first plugin)
├── cursor-plugin/                # 1Password for Cursor (in-dev)
│   ├── .cursor-plugin/plugin.json
│   ├── hooks/
│   ├── skills/
│   ├── rules/
│   └── mcp.json
├── plugins/
│   └── README.md                 # Conventions for adding IDE plugins
├── schemas/
├── scripts/validate-marketplace.mjs
└── README.md
```

## Registered plugins

### Cursor

| Plugin | Source | Description |
|--------|--------|-------------|
| `1password` | [`cursor-plugin/`](cursor-plugin/) | Hooks, skill, rules, and MCP for 1Password Developer Environments (v1.2.0, in-dev) |

Install in Cursor:

```
/add-plugin 1password
```

See [`cursor-plugin/README.md`](cursor-plugin/README.md) for plugin-specific setup.

### Claude Code

No plugins registered yet. Add directories under `plugins/claude/` and list them in `.claude-plugin/marketplace.json`. See [`plugins/README.md`](plugins/README.md).

## Register as a team marketplace

### Cursor

1. Push this repo to GitHub.
2. Cursor Dashboard → **Settings → Plugins** → import the repository URL.
3. Cursor reads `.cursor-plugin/marketplace.json` and exposes listed plugins.

### Claude Code

1. Push this repo to GitHub.
2. Add the marketplace URL to team settings, for example in `.claude/settings.json`:

   ```json
   {
     "extraKnownMarketplaces": [
       "https://github.com/agilebits-inc/mcp-plugin-test-marketplace/blob/main/.claude-plugin/marketplace.json"
     ]
   }
   ```

3. Enable plugins from the marketplace once entries are added.

## Adding a plugin

1. Create a plugin directory with the appropriate `.cursor-plugin/plugin.json` and/or `.claude-plugin/plugin.json`.
2. Add an entry to each IDE marketplace manifest that should distribute the plugin. Entry `name` must match the plugin manifest `name`; `source` is the relative path from repo root.
3. Run validation locally before opening a PR.

Details: [`plugins/README.md`](plugins/README.md)

## Local development (Cursor)

Symlink the plugin directory for local testing:

```bash
ln -s "$(pwd)/cursor-plugin" ~/.cursor/plugins/local/1password
```

Reload Cursor and verify hooks, skills, and MCP under Settings.

## Validation

```bash
npm install --no-save ajv ajv-formats
npm run validate
```

CI runs the same check on pull requests and pushes to `main`.

## Cleanup note

If `cursor-plugin/` was copied from a git clone, remove the nested repository metadata before committing:

```bash
rm -rf cursor-plugin/.git
```

That path is gitignored, but removing it locally avoids confusion.

## References

- [Cursor Plugins reference](https://cursor.com/docs/reference/plugins)
- [Claude Code plugins](https://docs.anthropic.com/en/docs/claude-code/plugins)
