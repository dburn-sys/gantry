"""Gantry SessionStart hook: inject the persona and project state."""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import emit, gantry_root, git_email, read_input, run_hook  # noqa: E402

LIMIT = 9500  # Claude Code caps additionalContext at 10,000 characters


def sprint_state(root: Path) -> str:
    """One line about a sprint in progress, so a compacted or new session can resume it."""
    log = root / ".gantry" / "sprint-log.md"
    if not log.exists():
        return ""
    head = log.read_text(encoding="utf-8")
    name = re.search(r"^# Sprint: (\S+)", head, re.M)
    status = re.search(r"^Status: (\w+)", head, re.M)
    plan = re.search(r"^Plan: (\S+)", head, re.M)
    if not (name and status) or status.group(1) == "finished":
        return ""
    tasks = []
    if plan and (root / plan.group(1)).exists():
        text = (root / plan.group(1)).read_text(encoding="utf-8")
        for block in re.split(r"(?m)^### ", text)[1:]:
            tid = block.split(":", 1)[0].strip()
            st = re.search(r"^- State: (\S+)", block, re.M)
            tasks.append((tid, st.group(1) if st else "PENDING"))
    done = sum(1 for _, s in tasks if s == "ACCEPTED")
    nxt = next((t for t, s in tasks if s != "ACCEPTED"), None)
    stops = re.findall(r"^### (S-\d+):.*$", head, re.M)
    line = (f"Sprint {name.group(1)} is {status.group(1)}: {done} of {len(tasks)} tasks accepted"
            + (f"; next {nxt}" if nxt else "") + ".")
    if status.group(1) == "stopped" and stops:
        line += f" Waiting on the user for {stops[-1]} (see .gantry/sprint-log.md)."
    return line + " Resume with the gantry:sprint skill.\n\n"


def health_note(root: Path) -> str:
    """Chapter 22: say so when nobody has proved the hooks fire here recently."""
    import json
    from datetime import datetime, timedelta, timezone
    f = root / ".gantry" / "probe.jsonl"
    last = None
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                last = datetime.fromisoformat(json.loads(line)["at"])
            except (ValueError, KeyError):
                continue
    if last is None:
        return ("Gantry health: /gantry:doctor has never run in this repository, so nothing "
                "has proved the hooks fire here. Mention this to the user.\n\n")
    if datetime.now(timezone.utc) - last > timedelta(days=7):
        return (f"Gantry health: the last live-fire probe was {last.date()}. Suggest the user "
                "runs /gantry:doctor.\n\n")
    return ""


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    plugin = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).parents[1])
    persona = (plugin / "ORCHESTRATOR.md").read_text(encoding="utf-8")
    state_file = root / ".gantry" / "context.md"
    state = state_file.read_text(encoding="utf-8") if state_file.exists() else ""

    note = ("\n\nNote: git has no user.email set here, so overrides will be "
            "recorded as 'unknown'. Ask the user to set it.") if git_email(root) == "unknown" else ""
    text = (f"Gantry is active in this repository ({root.name}).{note}\n\n{health_note(root)}{sprint_state(root)}"
            f"{persona}\n\n## Current project state\n\n{state}")
    emit({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text[:LIMIT],
    }})


if __name__ == "__main__":
    run_hook("session-start", main)
