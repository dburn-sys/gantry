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
