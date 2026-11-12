"""Gantry: the PR and merge gates for GitHub's MCP server tools.

Tool names differ between versions of the GitHub MCP server, so this matches
on words in the name rather than an exact list. Check yours with /mcp.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import gantry_root, read_input, run_hook  # noqa: E402
from pre_bash import check_pr_create, refuse_merge  # noqa: E402


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    name = str(data.get("tool_name", "")).lower()
    if not name.startswith("mcp__github"):
        return
    tool = name.split("__")[-1]
    payload = json.dumps(data.get("tool_input") or {}).upper()
    if "merge" in tool and "pull" in tool or "auto_merge" in tool or "automerge" in tool:
        refuse_merge(root, "merge pull requests or enable auto-merge")
    elif "review" in tool and "APPROVE" in payload:
        refuse_merge(root, "approve pull requests")
    elif tool.startswith("create_pull_request") and "review" not in tool:
        check_pr_create(root)


if __name__ == "__main__":
    run_hook("github gate", main)
