"""Gantry: record approvals typed by the user."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (state_dir, uninitialized_repo, GATES, TOKEN_MINUTES, _sha8, chain_append, current_branch,  # noqa: E402
                     emit, gantry_root, git_email, now_iso, read_input, run_hook)

APPROVE = re.compile(r"^\s*approve spec ([a-z0-9][a-z0-9-]*)\s*$", re.I)
CONFIRM = re.compile(r"\[CONFIRM-\d+\](?!.*resolved:)")
OVERRIDE = re.compile(r"^\s*override (G-[A-Z]+) because (.+?)\s*$", re.I | re.S)
DEV = re.compile(r"^\s*gantry dev (on because (.+?)|off)\s*$", re.I | re.S)


def handle_dev(root: Path, data: dict, on: bool, reason: str) -> None:
    """Maintainer dev mode (Chapter 22). The env key comes from the human's shell."""
    import os
    f = root / ".gantry" / "dev-mode.json"
    if not on:
        f.unlink(missing_ok=True)
        emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
              "additionalContext": "Gantry dev mode is off."}})
    if os.environ.get("GANTRY_DEV") != "1":
        emit({"decision": "block", "reason": "Gantry: dev mode needs GANTRY_DEV=1 in the shell "
              "that started Claude Code, as well as this phrase."})
    if len(reason.split()) < 5:
        emit({"decision": "block", "reason": "Gantry: dev mode needs a reason of at least five words."})
    who = git_email(root)
    chain_append(root / ".gantry" / "overrides.log",
                 [now_iso(), who, "G-HARNESS (dev mode)", current_branch(root), " ".join(reason.split())])
    f.write_text(json.dumps({"session": data.get("session_id"), "by": who, "at": now_iso()}), encoding="utf-8")
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
          "additionalContext": f"Gantry dev mode is on for this session ({who}): the plugin's own "
                               "files can be edited. Every other gate still applies."}})


ACCEPT = re.compile(r"^\s*accept finding (\d+) because (.+?)\s*$", re.I | re.S)


def handle_accept(root: Path, number: str, reason: str) -> None:
    """A person accepts a blocking finding in this branch's latest run report."""
    if len(reason.split()) < 5:
        emit({"decision": "block",
              "reason": "Gantry: accepting a finding needs a real reason of at least five words."})
    branch = current_branch(root)
    runs = sorted((root / ".gantry" / "runs").glob(f"*{branch.replace('/', '-')}*/report.md"))
    if not runs:
        emit({"decision": "block", "reason": f"Gantry: no run report for {branch}, so no finding {number}."})
    run = runs[-1].parent.name
    who = git_email(root)
    chain_append(root / ".gantry" / "accepted-findings.log",
                 [now_iso(), who, branch, run, number, " ".join(reason.split())])
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
          "additionalContext": f"Gantry recorded that {who} accepted finding {number} in "
                               f"{run}. Set its disposition to \"accepted: <reason>\" in the run report."}})


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
    chain_append(state_dir(root) / "overrides.log",
                 [now_iso(), who, gate, current_branch(root), reason_one_line])
    expires = (datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)).isoformat()
    (state_dir(root) / "override-token.json").write_text(
        json.dumps({"gate": gate, "by": who, "expires": expires}), encoding="utf-8")
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
          "additionalContext": f"Gantry recorded an override of {gate} by {who}. "
                               f"The next action blocked by {gate} in the next "
                               f"{TOKEN_MINUTES} minutes is allowed once."}})


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        bare = uninitialized_repo(data)       # required mode: only a G-INIT override applies
        o = OVERRIDE.match(data.get("prompt", ""))
        if bare is not None and o and o.group(1).upper() == "G-INIT":
            handle_override(bare, o.group(1), o.group(2))
        return
    o = OVERRIDE.match(data.get("prompt", ""))
    if o:
        handle_override(root, o.group(1), o.group(2))
    d = DEV.match(data.get("prompt", ""))
    if d:
        handle_dev(root, data, d.group(1).lower().startswith("on"), d.group(2) or "")
    a = ACCEPT.match(data.get("prompt", ""))
    if a:
        handle_accept(root, a.group(1), a.group(2))
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
