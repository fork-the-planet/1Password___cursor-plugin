#!/usr/bin/env python3
"""Lightweight regression checks for hook_state tool detection."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib.hook_state import (  # noqa: E402
    can_enforce_skill_gate,
    is_1password_mcp_call,
    is_full_skill_read,
    is_onepassword_mcp_doc_fetch,
    mcp_tool_slug,
)

SKILL = "/Users/x/.cursor/plugins/local/1password/skills/1password-environments/SKILL.md"


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"ok: {label}")


def run_require(payload: dict) -> str:
    script = ROOT / "require-1password-skill-read"
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["permission"]


def main() -> None:
    check("MCP:append_variables slug", mcp_tool_slug({"tool_name": "MCP:append_variables"}) == "append_variables")
    check(
        "CallMcpTool slug",
        mcp_tool_slug(
            {
                "tool_name": "CallMcpTool",
                "tool_input": {
                    "server": "user-1password",
                    "toolName": "append_variables",
                },
            }
        )
        == "append_variables",
    )
    check(
        "non-1password CallMcpTool",
        mcp_tool_slug(
            {
                "tool_name": "CallMcpTool",
                "tool_input": {"server": "github", "toolName": "search"},
            }
        )
        == "",
    )
    check(
        "fetch docs uri",
        is_onepassword_mcp_doc_fetch(
            {
                "tool_name": "FetchMcpResource",
                "tool_input": {"uri": "1password://docs/getting-started"},
            }
        ),
    )
    check(
        "partial read rejected",
        not is_full_skill_read({"tool_input": {"path": SKILL, "limit": 20}}),
    )
    check(
        "full read accepted",
        is_full_skill_read({"tool_input": {"path": SKILL}}),
    )
    check(
        "no conversation id cannot enforce",
        not can_enforce_skill_gate({"tool_name": "append_variables"}),
    )

    base = {
        "conversation_id": "hook-state-test",
        "workspace_roots": [str(ROOT.parent)],
    }
    check(
        "gate denies bare append_variables",
        run_require({**base, "tool_name": "append_variables"}) == "deny",
    )
    check(
        "gate denies MCP:append_variables",
        run_require({**base, "tool_name": "MCP:append_variables"}) == "deny",
    )
    check(
        "gate denies CallMcpTool append_variables",
        run_require(
            {
                **base,
                "tool_name": "CallMcpTool",
                "tool_input": {
                    "server": "user-1password",
                    "toolName": "append_variables",
                },
            }
        )
        == "deny",
    )
    check(
        "gate fails open without conversation id",
        run_require({"tool_name": "append_variables"}) == "allow",
    )

    print("all hook_state checks passed")


if __name__ == "__main__":
    main()
