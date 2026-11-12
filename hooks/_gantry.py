"""Shared helpers for Gantry hooks. Standard library only."""
import json
import os
import subprocess
import sys
from pathlib import Path


def read_input() -> dict:
    """Read the hook's JSON input from stdin."""
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    return data


def gantry_root(data: dict) -> Path | None:
    """Return the nearest folder containing .gantry/, or None (dormant)."""
    start = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    here = Path(start).resolve()
    for folder in [here, *here.parents]:
        if (folder / ".gantry").is_dir():
            return folder
    return None


def current_branch(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            cwd=root, capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git rev-parse failed")
    return result.stdout.strip()


def emit(payload: dict) -> None:
    """Print a JSON response and exit successfully."""
    print(json.dumps(payload))
    sys.exit(0)


def deny(reason: str) -> None:
    emit({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }})


def warn_and_allow(check: str, exc: BaseException) -> None:
    """Principle 3: a check that can't run warns in one line and allows."""
    emit({"systemMessage":
          f"gantry: {check} couldn't run ({type(exc).__name__}: {exc}); "
          f"allowed without checking."})


def run_hook(check: str, main) -> None:
    """Run a hook's main(), turning any unexpected error into a warning."""
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - fail open on purpose
        warn_and_allow(check, exc)
    sys.exit(0)


def read_config(root: Path) -> dict:
    """Parse the flat key: value lines between the --- markers of .gantry/context.md."""
    f = root / ".gantry" / "context.md"
    if not f.exists():
        return {}
    lines = f.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    config = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            config[key.strip()] = value.strip()
    return config


def tree_fingerprint(root: Path) -> str:
    """A hash of HEAD plus every uncommitted change outside .gantry/, staged or not."""
    import hashlib

    def git(*args: str) -> bytes:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=15)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode(errors="replace").strip())
        return r.stdout

    outside_gantry = ["--", ".", ":(exclude).gantry"]
    h = hashlib.sha256()
    h.update(git("rev-parse", "HEAD"))
    h.update(git("diff", "HEAD", "--binary", *outside_gantry))
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", *outside_gantry)
    for name in sorted(filter(None, untracked.split(b"\0"))):
        h.update(name)
        h.update(git("hash-object", "--", name.decode()))
    return h.hexdigest()[:16]


def ledger_records(root: Path) -> list[dict]:
    ledger = root / ".gantry" / "evidence.jsonl"
    if not ledger.exists():
        return []
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def latest_run(root: Path) -> dict | None:
    records = ledger_records(root)
    return records[-1] if records else None


def has_uncommitted_changes(root: Path) -> bool:
    r = subprocess.run(["git", "status", "--porcelain", "--", ".", ":(exclude).gantry"],
                       cwd=root, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return bool(r.stdout.strip())


def approved(root: Path, slug: str) -> bool:
    f = root / ".gantry" / "approvals.jsonl"
    if not f.exists():
        return False
    return any(json.loads(line).get("spec") == slug
               for line in f.read_text(encoding="utf-8").splitlines() if line.strip())
