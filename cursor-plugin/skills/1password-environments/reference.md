# 1Password Environments — reference

## Skill-read gate (plugin hook)

`scripts/require-1password-skill-read` runs on `beforeMCPExecution`. It **blocks**
1Password MCP until the agent has Read `skills/1password-environments/SKILL.md` in
the current conversation. `scripts/mark-1password-skill-read` records that read on
`beforeReadFile` / `preToolUse` Read. Partial reads (`limit`, `offset`, or line
ranges) do not satisfy the gate — the agent must read the entire skill file.

If MCP is denied with a skill-read message, Read the skill file end-to-end, then
retry the MCP call. Do not substitute MCP docs or `mcps/**/tools/*.json`.

## Read gate (plugin hook)

`scripts/deny-1password-docs-read` runs on `beforeReadFile` / `preToolUse` and denies
Read on 1Password MCP descriptors and docs under `mcps/**/*1password*/**`, plus
`FetchMcpResource` for `1password://docs/*`, redirecting to `SKILL.md`. Call the MCP
tools directly per this skill. It fails open (`failClosed: false`) so a hook error
never blocks a legitimate read.

## Import completion nudges (plugin hook)

The plugin runs `scripts/nudge-1password-import` after relevant 1Password MCP calls and on agent stop. If you appended variables during an import but have not called `create_local_env_file`, the hook injects the next required steps. Treat that as mandatory — do not reply to the user until the mount is verified.

## Mount conflict (shell validation hook)

The `beforeShellExecution` hook (`scripts/validate-mounted-env-files`) blocks **all**
shell commands when 1Password expects a mount at a path that is missing, disabled, or
not a FIFO (for example a plain `.env` still on disk at the mount path). Reading the
`.env` with the Read tool is unaffected — only shell commands are gated.

Validation scope depends on `.1password/environments.toml`:

- No TOML file (or no `mount_paths` field) — default mode: all 1Password mount destinations for this workspace are validated.
- `mount_paths = [".env", ...]` — only listed paths are validated.
- `mount_paths = []` — validation disabled for this repo; all shell commands allowed.

If shell commands are blocked with a message about missing, invalid, or disabled environment files:

1. Check whether 1Password already has a destination for the same path (`list_local_env_files`, or the 1Password app Destinations tab).
2. Resolve it by one of:
   - Temporarily set `mount_paths = []` in `.1password/environments.toml` to disable mount validation for this repo.
   - Fix the mount in 1Password (enable the destination, or remove it until migration finishes).

The import itself does not need shell — Read the `.env` directly to get its keys and values.

## Setup and troubleshooting

**Requirements**

- macOS or Linux with the 1Password desktop app installed (local `.env` mounts are macOS/Linux only; on Windows the validation hook is a no-op).
- **1Password Cursor plugin installed** (marketplace or local symlink) so this skill, hooks, and MCP config load together.
- 1Password Labs **MCP Server** experiment enabled in the desktop app (`onepassword://settings/labs`).
- Access to a 1Password account with Developer Environments enabled.

The MCP server binary on macOS:

```text
/Applications/1Password.app/Contents/MacOS/1password-mcp
```

On Linux, see the [1Password MCP server documentation](https://www.1password.dev/environments/mcp-server) for the binary path on your platform.

**When things fail**

- Authentication or environment access fails — the 1Password desktop app may need approval, unlocking, or account access.
- MCP server unavailable — enable the **1Password Labs MCP Server** experiment via `onepassword://settings/labs`. If the Labs setting is missing, the account may not have the required `ai-local-mcp-server` feature flag.
- `create_local_env_file` fails — confirm the user is on macOS or Linux.
- Shell commands denied while 1Password expects a mount that is missing or disabled — see **Mount conflict** above.
