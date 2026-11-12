"""Run a hook script the way Claude Code does: JSON in on stdin, JSON out."""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "plugins" / "gantry" / "hooks"


def run_hook(script: str, event: dict, cwd: Path, extra_env: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    env.update({"CLAUDE_PROJECT_DIR": str(cwd), **(extra_env or {})})
    r = subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(event),
                       capture_output=True, text=True, cwd=cwd, env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else {}


def decision(out: dict) -> str:
    if not out:
        return "allow"
    if "systemMessage" in out and "hookSpecificOutput" not in out:
        return "warn"
    return out["hookSpecificOutput"].get("permissionDecision", "allow")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def make_repo(tmp: Path, opted_in: bool = True) -> Path:
    git(tmp, "init", "-q", "-b", "main")
    git(tmp, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
    if opted_in:
        (tmp / ".gantry").mkdir()
    return tmp
