"""Chapter 22: every hook, given junk, warns and exits 0. Never a traceback, never a block."""
import json
import os
import subprocess
import sys

import pytest

from helpers import HOOKS, make_repo

HOOK_NAMES = sorted({h["command"].split()[-1]
                     for groups in json.loads((HOOKS / "hooks.json").read_text())["hooks"].values()
                     for g in groups for h in g["hooks"]})


def raw(name, stdin, cwd, path=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)}
    if path is not None:
        env["PATH"] = path
    r = subprocess.run([sys.executable, str(HOOKS / "_launcher.py"), name], input=stdin,
                       capture_output=True, text=True, cwd=cwd, env=env, timeout=30)
    return r


def opted_in(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\ntest_command: sh t.sh\n---\n")
    return repo


@pytest.mark.parametrize("hook", HOOK_NAMES)
@pytest.mark.parametrize("stdin", ["not json", "[1, 2]", "", "null"])
def test_junk_input_warns_and_exits_zero(tmp_path, hook, stdin):
    r = raw(hook, stdin, opted_in(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "Traceback" not in r.stderr
    if r.stdout.strip():
        out = json.loads(r.stdout)
        assert "systemMessage" in out and out.get("decision") != "block"
        assert out.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_empty_event_is_harmless(tmp_path, hook):
    r = raw(hook, "{}", opted_in(tmp_path))
    assert r.returncode == 0 and "Traceback" not in r.stderr


@pytest.mark.parametrize("hook", ["pre_bash", "pre_write", "post_bash", "session_start", "prompt_submit"])
def test_no_git_on_path_fails_open(tmp_path, hook):
    repo = opted_in(tmp_path)
    event = {"tool_name": "Bash", "cwd": str(repo), "session_id": "s", "prompt": "hello",
             "hook_event_name": "PostToolUse",
             "tool_input": {"command": "git commit -m x", "file_path": str(repo / "src" / "a.ts"), "content": "x"}}
    r = raw(hook, json.dumps(event), repo, path=str(tmp_path / "empty-path"))
    assert r.returncode == 0 and "Traceback" not in r.stderr
    if r.stdout.strip():
        out = json.loads(r.stdout)
        assert out.get("hookSpecificOutput", {}).get("permissionDecision") != "deny" or "couldn't run" in r.stdout
