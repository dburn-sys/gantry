"""Gantry SessionStart hook: inject the persona and project state."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import emit, gantry_root, read_input, run_hook  # noqa: E402

LIMIT = 9500  # Claude Code caps additionalContext at 10,000 characters


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    plugin = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).parents[1])
    persona = (plugin / "ORCHESTRATOR.md").read_text(encoding="utf-8")
    state_file = root / ".gantry" / "context.md"
    state = state_file.read_text(encoding="utf-8") if state_file.exists() else ""

    text = (f"Gantry is active in this repository ({root.name}).\n\n"
            f"{persona}\n\n## Current project state\n\n{state}")
    emit({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text[:LIMIT],
    }})


if __name__ == "__main__":
    run_hook("session-start", main)
