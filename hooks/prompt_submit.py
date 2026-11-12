"""Gantry: record approvals typed by the user."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import emit, gantry_root, read_input, run_hook  # noqa: E402

APPROVE = re.compile(r"^\s*approve spec ([a-z0-9][a-z0-9-]*)\s*$", re.I)
CONFIRM = re.compile(r"\[CONFIRM-\d+\](?!.*resolved:)")


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    m = APPROVE.match(data.get("prompt", ""))
    if not m:
        return
    slug = m.group(1).lower()
    spec = root / ".gantry" / "specs" / f"{slug}.md"
    if not spec.exists():
        emit({"decision": "block",
              "reason": f"Gantry: no spec named {slug} in .gantry/specs/."})
    open_items = [line for line in spec.read_text(encoding="utf-8").splitlines()
                  if CONFIRM.search(line)]
    if open_items:
        emit({"decision": "block",
              "reason": f"Gantry: {slug} has {len(open_items)} unresolved "
                        "[CONFIRM] question(s). Resolve them before approving."})

    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "spec": slug, "session": data.get("session_id")}
    with (root / ".gantry" / "approvals.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    text = spec.read_text(encoding="utf-8")
    spec.write_text(re.sub(r"(?m)^Status: .*$", f"Status: approved {record['at']}",
                           text, count=1), encoding="utf-8")
    emit({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"Gantry recorded approval of spec {slug} at {record['at']}."}})


if __name__ == "__main__":
    run_hook("approval recorder", main)
