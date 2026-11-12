"""Gantry: record test runs to the evidence ledger."""
import json
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import current_branch, gantry_root, read_config, read_input, run_hook, tree_fingerprint  # noqa: E402

FILTER_FLAGS = {"-t", "--testNamePattern", "-k", "--grep", "--only"}


def classify(command: str, test_command: str) -> str | None:
    """Return 'full', 'partial', or None if this isn't the test command."""
    if re.search(r"[|;&<>]", command):
        return None                 # pipes and redirects can hide the exit code
    words = shlex.split(command)
    base = shlex.split(test_command)
    if words[:len(base)] != base:
        return None
    extra = [w for w in words[len(base):] if w != "--"]
    if any(w in FILTER_FLAGS or not w.startswith("-") for w in extra):
        return "partial"
    return "full"


def main() -> None:
    data = read_input()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return
    root = gantry_root(data)
    if root is None:
        return
    test_command = read_config(root).get("test_command")
    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not test_command or tool_input.get("run_in_background"):
        return                      # a background run hasn't finished; it proves nothing yet
    scope = classify(command.strip(), test_command)
    if scope is None:
        return

    record = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": data.get("session_id"),
        "branch": current_branch(root),
        "command": command,
        "scope": scope,
        "passed": data.get("hook_event_name") == "PostToolUse",
        "tree": tree_fingerprint(root),
    }
    with (root / ".gantry" / "evidence.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    run_hook("evidence recorder", main)
