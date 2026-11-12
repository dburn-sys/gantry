"""Gantry: record approvals typed by the user."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (GATES, TOKEN_MINUTES, _sha8, chain_append, current_branch,  # noqa: E402
                     emit, gantry_root, git_email, now_iso, read_input, run_hook)

APPROVE = re.compile(r"^\s*approve spec ([a-z0-9][a-z0-9-]*)\s*$", re.I)
CONFIRM = re.compile(r"\[CONFIRM-\d+\](?!.*resolved:)")
OVERRIDE = re.compile(r"^\s*override (G-[A-Z]+) because (.+?)\s*$", re.I | re.S)


def handle_override(root: Path, gate: str, reason: str) -> None:
    from datetime import datetime, timedelta, timezone
    gate = gate.upper()
    if gate not in GATES:
        emit({"decision": "block", "reason": f"Gantry: {gate} isn't a Gantry gate. See docs/gates.md."})
    if len(reason.split()) < 5:
        emit({"decision": "block",
              "reason": "Gantry: an override needs a real reason of at least five words."})
    who = git_email(root)
    reason_one_line = " ".join(reason.split())
    chain_append(root / ".gantry" / "overrides.log",
                 [now_iso(), who, gate, current_branch(root), reason_one_line])
    expires = (datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)).isoformat()
    (root / ".gantry" / "override-token.json").write_text(
        json.dumps({"gate": gate, "by": who, "expires": expires}), encoding="utf-8")
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
          "additionalContext": f"Gantry recorded an override of {gate} by {who}. "
                               f"The next action blocked by {gate} in the next "
                               f"{TOKEN_MINUTES} minutes is allowed once."}})


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    o = OVERRIDE.match(data.get("prompt", ""))
    if o:
        handle_override(root, o.group(1), o.group(2))
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

    log = root / ".gantry" / "approvals.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "spec": slug, "session": data.get("session_id"),
              "prev": _sha8(lines[-1]) if lines else "00000000"}
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    text = spec.read_text(encoding="utf-8")
    spec.write_text(re.sub(r"(?m)^Status: .*$", f"Status: approved {record['at']}",
                           text, count=1), encoding="utf-8")
    emit({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"Gantry recorded approval of spec {slug} at {record['at']}."}})


if __name__ == "__main__":
    run_hook("approval recorder", main)
