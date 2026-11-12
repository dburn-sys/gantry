"""Gantry status line: one line of harness state for Claude Code's statusLine setting.

Claude Code runs this with session JSON on stdin and shows the first line printed.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (changed_paths, current_branch_or_none, gantry_root,  # noqa: E402
                     latest_run, tree_fingerprint)


def open_findings(root: Path, branch: str) -> int:
    runs = sorted((root / ".gantry" / "runs").glob(f"*{branch.replace('/', '-')}*/report.md"))
    if not runs:
        return 0
    text = runs[-1].read_text(encoding="utf-8")
    if "## Review findings" not in text:
        return 0
    rows = [r for r in text.split("## Review findings", 1)[1].split("\n## ", 1)[0].splitlines()
            if r.startswith("|") and not set(r) <= set("|- ")]
    if not rows:
        return 0
    cols = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    if "disposition" not in cols:
        return 0
    i = cols.index("disposition")
    return sum(1 for r in rows[1:] if len(r.strip("|").split("|")) > i and not r.strip("|").split("|")[i].strip())


def count_lines(f: Path, needle: str = "") -> int:
    if not f.exists():
        return 0
    return sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip() and needle in line)


def line(data: dict) -> str:
    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or "."
    root = gantry_root({"cwd": cwd})
    if root is None:
        return ""
    branch = current_branch_or_none(root) or "?"
    run = latest_run(root)
    if run is None:
        tests = "tests: none"
    elif not run["passed"]:
        tests = "tests: RED"
    elif run["scope"] != "full":
        tests = "tests: partial"
    elif run["tree"] == tree_fingerprint(root):
        tests = "tests: green (current)"
    else:
        tests = f"tests: STALE ({len(changed_paths(root))} files changed)"
    overrides = count_lines(root / ".gantry" / "overrides.log", f"| {branch} |")
    unproven = count_lines(root / ".gantry" / "unproven.log")
    return (f"gantry  {branch}  {tests}  review: {open_findings(root, branch)} open  "
            f"overrides: {overrides}  unproven: {unproven}")


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        print(line(data if isinstance(data, dict) else {}))
    except Exception as exc:  # noqa: BLE001 - a status line must never crash the UI
        print(f"gantry  status unavailable ({type(exc).__name__})")


if __name__ == "__main__":
    main()
