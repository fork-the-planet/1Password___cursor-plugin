"""Shared conversation state for 1Password Cursor plugin hooks."""

from __future__ import annotations

import json
import re
from pathlib import Path

STATE_DIR = Path("/tmp/1password-cursor-plugin")
IMPORT_STATE_DIR = STATE_DIR / "import-state"
SKILL_READ_DIR = STATE_DIR / "skill-read"

_SKILL_MARKERS = (
    "skills/1password-environments/skill.md",
    "1password-environments/skill.md",
)

_ONEPASSWORD_MCP_TOOLS = frozenset(
    {
        "authenticate",
        "list_environments",
        "create_environment",
        "rename_environment",
        "list_variables",
        "append_variables",
        "create_local_env_file",
        "list_local_env_files",
    }
)

_MCP_TOOL_WRAPPERS = frozenset({"callmcptool", "call_mcp_tool"})
_MCP_FETCH_WRAPPERS = frozenset({"fetchmcpresource", "fetch_mcp_resource"})

_ONEPASSWORD_SERVER = re.compile(r"1password", re.IGNORECASE)
_MCP_ONEPASSWORD_PATH = re.compile(r"/mcps/[^/]*1password[^/]*/", re.IGNORECASE)
_ONEPASSWORD_DOC_URI = re.compile(
    r"^1password://docs/(?:getting-started|environments-guide)",
    re.IGNORECASE,
)

_CONVERSATION_ID_KEYS = (
    "conversation_id",
    "session_id",
    "chat_id",
    "thread_id",
    "generation_id",
)


def parse_tool_input(data: dict) -> dict:
    raw = data.get("tool_input")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def conversation_id(data: dict) -> str:
    for key in _CONVERSATION_ID_KEYS:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def can_enforce_skill_gate(data: dict) -> bool:
    """Return False when no stable conversation key is available.

    Without one, deny would deadlock because mark-1password-skill-read cannot
    persist state. Fail open in that case.
    """
    return bool(conversation_id(data))


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value or "unknown")


def skill_read_marker_path(conv_id: str) -> Path:
    return SKILL_READ_DIR / f"{_safe_id(conv_id)}.json"


def is_skill_read(conv_id: str) -> bool:
    if not conv_id:
        return False
    path = skill_read_marker_path(conv_id)
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return bool(payload.get("skill_read"))
    except (OSError, json.JSONDecodeError):
        return False


def mark_skill_read(conv_id: str) -> None:
    if not conv_id:
        return
    SKILL_READ_DIR.mkdir(parents=True, exist_ok=True)
    skill_read_marker_path(conv_id).write_text(
        json.dumps({"skill_read": True}, indent=2),
        encoding="utf-8",
    )


def skill_paths_for_workspace(workspace_root: str) -> list[str]:
    paths: list[str] = []
    if workspace_root:
        workspace_skill = (
            Path(workspace_root) / "skills" / "1password-environments" / "SKILL.md"
        )
        if workspace_skill.is_file():
            paths.append(str(workspace_skill))
    home = Path.home()
    paths.extend(
        str(path)
        for path in (
            home / ".cursor" / "plugins" / "local" / "1password" / "skills" / "1password-environments" / "SKILL.md",
            home / ".cursor" / "plugins" / "cache" / "1password" / "skills" / "1password-environments" / "SKILL.md",
        )
        if path.is_file()
    )
    cache_root = home / ".cursor" / "plugins" / "cache"
    if cache_root.is_dir():
        for skill_path in cache_root.glob("**/skills/1password-environments/SKILL.md"):
            resolved = str(skill_path)
            if resolved not in paths:
                paths.append(resolved)
    return paths


def skill_path_hint(data: dict) -> str:
    """Absolute-path instruction for reading the bundled skill."""
    workspace_roots = data.get("workspace_roots")
    workspace_root = workspace_roots[0] if isinstance(workspace_roots, list) and workspace_roots else ""
    candidates = skill_paths_for_workspace(workspace_root)
    if candidates:
        paths = "\n".join(f"- `{path}`" for path in candidates)
        return f"Read the ENTIRE file at the first path that exists:\n{paths}"
    return (
        "Read the ENTIRE `1password-environments` plugin skill "
        "(`skills/1password-environments/SKILL.md` in the plugin root)."
    )


def skill_read_instruction(data: dict) -> str:
    path_hint = skill_path_hint(data)

    return (
        "1Password MCP calls are blocked until you read the bundled plugin skill. "
        f"{path_hint} "
        "Do not read MCP tool descriptors under `mcps/`. "
        "Do not fetch `1password://docs/getting-started` or `environments-guide`. "
        "After reading the skill, retry the MCP call and follow the import checklist "
        "(append_variables is not done until create_local_env_file is verified)."
    )


def is_skill_markdown_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(marker in normalized for marker in _SKILL_MARKERS)


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def is_full_skill_read(data: dict) -> bool:
    """Return True only when the Read appears to cover the entire skill file."""
    tool_input = parse_tool_input(data)

    if _coerce_int(tool_input.get("limit")) is not None:
        return False

    offset = _coerce_int(tool_input.get("offset"))
    if offset is not None and offset > 0:
        return False

    for key in ("startLine", "lineStart", "start_line"):
        start = _coerce_int(tool_input.get(key))
        if start is not None and start > 1:
            return False

    for key in ("endLine", "lineEnd", "end_line"):
        if _coerce_int(tool_input.get(key)) is not None:
            return False

    return True


def is_1password_server(server: str) -> bool:
    return bool(server and _ONEPASSWORD_SERVER.search(server))


def normalize_tool_name(name: str) -> str:
    lowered = name.strip().lower()
    if lowered.startswith("mcp:"):
        lowered = lowered[4:]
    if "1password" in lowered and "-" in lowered:
        return lowered.rsplit("-", 1)[-1]
    return lowered


def tool_name(data: dict) -> str:
    for key in ("tool_name", "toolName"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def mcp_tool_slug(data: dict) -> str:
    """Return the 1Password MCP tool slug when this payload is a 1Password MCP call."""
    name = tool_name(data)
    if not name:
        return ""

    lowered = name.strip().lower()
    tool_input = parse_tool_input(data)

    if lowered in _MCP_TOOL_WRAPPERS:
        server = str(
            tool_input.get("server")
            or tool_input.get("mcpServer")
            or tool_input.get("mcp_server")
            or ""
        )
        if not is_1password_server(server):
            return ""
        slug = str(
            tool_input.get("toolName")
            or tool_input.get("tool_name")
            or tool_input.get("name")
            or ""
        ).strip()
        return normalize_tool_name(slug) if slug else ""

    if "1password" in lowered or "user-1password" in lowered:
        slug = normalize_tool_name(name)
        return slug if slug in _ONEPASSWORD_MCP_TOOLS else ""

    slug = normalize_tool_name(name)
    return slug if slug in _ONEPASSWORD_MCP_TOOLS else ""


def mcp_tool_arguments(data: dict) -> dict:
    tool_input = parse_tool_input(data)
    name = tool_name(data).strip().lower()

    if name in _MCP_TOOL_WRAPPERS:
        args = (
            tool_input.get("arguments")
            or tool_input.get("args")
            or tool_input.get("parameters")
            or {}
        )
        if isinstance(args, str) and args.strip():
            try:
                parsed = json.loads(args)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return args if isinstance(args, dict) else {}

    return tool_input


def is_1password_mcp_call(data: dict) -> bool:
    slug = mcp_tool_slug(data)
    if not slug:
        return False
    return slug in _ONEPASSWORD_MCP_TOOLS


def is_onepassword_mcp_doc_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(_MCP_ONEPASSWORD_PATH.search(normalized))


def is_onepassword_mcp_doc_fetch(data: dict) -> bool:
    name = tool_name(data).strip().lower()
    if name not in _MCP_FETCH_WRAPPERS:
        return False

    tool_input = parse_tool_input(data)
    uri = str(tool_input.get("uri") or tool_input.get("url") or "").strip()
    if not uri:
        return False

    if _ONEPASSWORD_DOC_URI.match(uri):
        return True

    normalized = uri.replace("\\", "/")
    return bool(_MCP_ONEPASSWORD_PATH.search(normalized))
