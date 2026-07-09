---
name: 1password-environments
description: >-
  MANDATORY — read this ENTIRE file before any 1Password MCP call. Canonical
  workflow for 1Password Developer Environments in Cursor. Use when creating,
  importing, migrating, or mounting .env files; managing repo secrets; listing
  Environment variable names; or calling any 1password MCP tool. Import-from-.env
  ALWAYS includes create_local_env_file at the source path unless the user
  explicitly says not to mount. MCP calls are blocked by plugin hooks until this
  file has been read.
---

# 1Password Environments

## Read this first

If you have not read **every section** of this file in the current conversation,
stop. A plugin hook blocks 1Password MCP tools until you read this skill with
the Read tool. Do not substitute MCP docs, tool descriptor JSON under `mcps/`,
or memory from other sessions.

## Not done until

**Import / create from `.env`** (including "using values from the project `.env`"):

- [ ] Environment created or resolved
- [ ] Variables appended via `append_variables`
- [ ] `create_local_env_file` at the **source** `.env` absolute path — **always**
- [ ] Mount verified with `list_local_env_files`

Mounting at the source `.env` path is mandatory, not optional follow-up. The
**only** exception is the user explicitly opting out ("without mounting", "do not
mount", "skip the mount"). Never ask "want me to mount?" — just mount.

Stopping after `create_environment` + `append_variables` is **incomplete and wrong**.
`list_variables` is not mount verification. Do not report success until the mount
checklist is done.

**Mount only:** mount exists at the requested path (`list_local_env_files`).

## Do not

- Read files under `mcps/**/tools/*.json` — call MCP tools directly
- Fetch `1password://docs/getting-started` or `environments-guide` — they omit import-and-mount; this skill is the workflow
- Skip `create_local_env_file` on import unless the user explicitly opted out
- Report success before the import checklist (including mount) is complete
- Offer mounting as optional follow-up — it is mandatory on import

## MCP tools

Request params are **camelCase**; responses may use snake_case. Get `accountId`
from `authenticate`; get `environmentId` from `create_environment` /
`list_environments`. Pass **every** required param — omitting one fails with
`missing field '<param>'`.

| Tool | Required params | Returns / notes |
|------|-----------------|-----------------|
| `authenticate` | *(none)* | `accountId`. First call each turn. |
| `list_environments` | `accountId` | Environments to resolve by name. |
| `create_environment` | `accountId`, `environmentName` | `environmentId`. Import continues below. |
| `rename_environment` | `accountId`, `environmentId`, `environmentName` | `environmentName` is the **new** name. |
| `list_variables` | `accountId`, `environmentId` | Names only — never values. |
| `append_variables` | `accountId`, `environmentId`, `variables: [{ name, value, concealed }]` | `variables` is an **array**; secrets `concealed: true`. |
| `list_local_env_files` | `accountId`, `environmentId` | Existing mounts. |
| `create_local_env_file` | `accountId`, `environmentId`, `environmentName`, `mountPath` | `mountPath` = absolute source `.env` path (macOS/Linux). |

## Import from a `.env` file

Default path: `{workspace_root}/.env` unless the user names another path.

1. **Read** the `.env` file with the Read tool to get its keys and values. Strip optional surrounding quotes from values. Pass values to MCP only — never paste secret values into chat.
2. **`authenticate`** → `accountId`
3. **`create_environment`** (new name) or **`list_environments`** (existing)
4. **`append_variables`** with all variables (secrets `concealed: true`)
5. **Mount** — **always** (skip only if the user explicitly said not to mount):
   - `list_local_env_files` — skip `create_local_env_file` only if a mount already exists at the source path
   - `create_local_env_file` with `accountId`, `environmentId`, `environmentName`, `mountPath` (absolute path of the original `.env`)
   - `list_local_env_files` again to verify

If shell is blocked because 1Password already expects a mount at the path, see [reference.md](reference.md) (mount conflict).

## Other flows

**Mount existing Environment:** authenticate → resolve Environment → step 5 above.

**Inspect names:** authenticate → resolve → `list_variables` → summarize names only.

**Rename:** authenticate → resolve → confirm name → `rename_environment`.

**Add/update variables:** authenticate → resolve → `list_variables` → `append_variables`.

## Safety

- Never reveal secret values in chat
- Store secrets with `concealed: true`
- Ask before changing variables unless the request is explicit
- A plain source `.env` is fine to Read. But once an environment is mounted, that path becomes a live FIFO (named pipe) — do not Read a mounted FIFO path (reading it can consume/hang the pipe); use `list_variables` to inspect a mounted environment instead

## Plugin enforcement

This plugin enforces the workflow with hooks:

| Hook | Effect |
|------|--------|
| `beforeMCPExecution` | Blocks 1Password MCP until this skill is Read in full |
| `postToolUse` / `stop` | Nudges mount steps after `append_variables` |
| `beforeReadFile` / `preToolUse` | Blocks Read on 1Password MCP descriptors under `mcps/` and `FetchMcpResource` for `1password://docs/*` — read this skill instead |

Treat hook `additional_context`, `agent_message`, and `followup_message` output as mandatory — not suggestions.

## Troubleshooting

Mount conflict, validation modes, setup: [reference.md](reference.md)
