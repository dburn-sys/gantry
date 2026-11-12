"""Chapter 22: the launcher runs hooks, and says so loudly on a Python that's too old."""
import json
import os
import subprocess
import sys

import pytest

from helpers import HOOKS, make_repo


def launch(name, event, cwd, version=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)}
    if version:
        env["GANTRY_TEST_PY_VERSION"] = version
    r = subprocess.run([sys.executable, str(HOOKS / "_launcher.py"), name], input=json.dumps(event),
                       capture_output=True, text=True, cwd=cwd, env=env, timeout=30)
    return r.returncode, r.stdout


def test_runs_the_named_hook(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\n---\n")
    code, out = launch("pre_bash", {"tool_name": "Bash", "cwd": str(repo),
                                    "tool_input": {"command": "git push --force"}}, repo)
    assert code == 0 and "[G-FORCE]" in out


@pytest.mark.parametrize("version", ["3.9", "3.6", "2.7"])
def test_old_python_warns_instead_of_failing_silently(tmp_path, version):
    code, out = launch("pre_bash", {"tool_name": "Bash", "tool_input": {"command": "ls"}}, tmp_path, version)
    msg = json.loads(out)["systemMessage"]
    assert code == 0 and f"running on {version}" in msg and "NOT enforcing" in msg


def test_unknown_or_unsafe_names_do_nothing(tmp_path):
    for name in ("nope", "../evil", "pre-bash"):
        assert launch(name, {}, tmp_path) == (0, "")


def test_launcher_uses_only_old_syntax():
    source = (HOOKS / "_launcher.py").read_text()
    assert 'f"' not in source and "f'" not in source and ":=" not in source and "->" not in source


def test_every_hook_in_hooks_json_goes_through_the_launcher():
    config = json.loads((HOOKS / "hooks.json").read_text())
    commands = [h["command"] for groups in config["hooks"].values() for g in groups for h in g["hooks"]]
    assert commands and all("_launcher.py" in c for c in commands)
    for c in commands:
        assert (HOOKS / f"{c.split()[-1]}.py").exists(), c
