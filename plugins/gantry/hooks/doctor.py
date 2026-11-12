"""Gantry doctor: check the install from top to bottom (read only).

    python doctor.py [--root DIR] --new-token     print a probe token
    python doctor.py [--root DIR] --check TOKEN   full report, including the live fire

Run it with the same command the hooks use (`python`, else `python3`), so the
Python it reports is the one the hooks get.
"""
import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import SECTION_FILES, chain_verify, read_config  # noqa: E402

MINIMUM = (3, 10)


def python_check() -> tuple[str, str]:
    v = sys.version_info
    where = sys.executable
    if sys.platform == "win32" and "WindowsApps" in where:
        return "FAIL", f"{where} is the Microsoft Store alias, not a real Python"
    if (v.major, v.minor) < MINIMUM:
        return "FAIL", f"hooks run with Python {v.major}.{v.minor}; Gantry needs 3.10+"
    return "ok", f"Python {v.major}.{v.minor}.{v.micro} ({where})"


def git_check(root: Path) -> tuple[str, str]:
    if not shutil.which("git"):
        return "FAIL", "git isn't on the PATH"
    version = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.split()[-1]
    email = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True).stdout.strip()
    if not email:
        return "warn", f"{version}, but user.email isn't set (logs will say 'unknown')"
    return "ok", f"{version}, user.email set"


def optin_check(root: Path) -> tuple[str, str]:
    ctx = root / ".gantry" / "context.md"
    if not ctx.exists():
        return "FAIL", "no .gantry/context.md here: run /gantry:init"
    config = read_config(root)
    if not config.get("test_command"):
        return "warn", ".gantry/context.md has no test_command, so the evidence gate can't run"
    return "ok", f".gantry/context.md, test_command: {config['test_command']}"


def chains_check(root: Path) -> tuple[str, str]:
    parts, bad = [], []
    for name in ("overrides.log", "approvals.jsonl", "accepted-findings.log"):
        f = root / ".gantry" / name
        if not f.exists():
            continue
        n = len([x for x in f.read_text(encoding="utf-8").splitlines() if x.strip()])
        line = chain_verify(f)
        parts.append(f"{name} ({n})")
        if line is not None:
            bad.append(f"{name} broken at line {line}")
    if bad:
        return "FAIL", "; ".join(bad)
    return "ok", ", ".join(parts) or "no chained logs yet"


def architecture_check(root: Path) -> tuple[str, str]:
    arch = root / ".gantry" / "architecture"
    if not arch.is_dir():
        return "skip", "no .gantry/architecture/"
    present = [s for s, f in SECTION_FILES.items() if (arch / f).exists()]
    return "ok", f"sections {', '.join(present) or 'none'}"


def live_fire(root: Path, token: str) -> tuple[str, str]:
    f = root / ".gantry" / "probe.jsonl"
    hits = []
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("token") == token:
                hits.append(rec)
    if not hits:
        return "FAIL", "probe token not recorded: the Bash hook is not running"
    if len(hits) > 1:
        roots = sorted({h.get("plugin_root", "?") for h in hits})
        return "FAIL", f"probe recorded {len(hits)} times: Gantry is loaded more than once ({'; '.join(roots)})"
    return "ok", "the Bash hook saw the probe"


def report(root: Path, token: str) -> int:
    checks = [("python", python_check()), ("git", git_check(root)), ("opt-in", optin_check(root)),
              ("chains", chains_check(root)), ("architecture", architecture_check(root)),
              ("live fire", live_fire(root, token))]
    print("Gantry doctor")
    for name, (status, detail) in checks:
        print(f"  {name:<12} {status:<5} {detail}")
    failed = [n for n, (s, _) in checks if s == "FAIL"]
    print()
    if failed:
        print("Gantry is NOT enforcing in this repository. Fix the items marked FAIL, "
              "then start a new session and run /gantry:doctor again.")
        return 1
    print("Gantry is installed and enforcing in this repository.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--new-token", action="store_true")
    group.add_argument("--check")
    a = ap.parse_args()
    if a.new_token:
        print(secrets.token_hex(8))
        return 0
    return report(Path(a.root).resolve(), a.check)


if __name__ == "__main__":
    sys.exit(main())
