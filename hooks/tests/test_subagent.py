"""Chapter 18: only the main session commits."""
import json

import pytest

from helpers import decision, run_hook
from test_evidence import record_run, setup_repo


def git_from(repo, command, agent=True):
    event = {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": command}}
    if agent:
        event |= {"agent_id": "a-123", "agent_type": "gantry:backend-author"}
    return run_hook("pre_bash.py", event, repo)


@pytest.mark.parametrize("command", ["git commit -m x", "git push origin feat/x",
                                     "git merge feat/y", "git rebase main",
                                     "npm test && git commit -am done"])
def test_subagent_cannot_commit_push_merge_or_rebase(tmp_path, command):
    repo = setup_repo(tmp_path)
    record_run(repo)
    out = git_from(repo, command)
    assert decision(out) == "deny" and "[G-SUBAGENT]" in json.dumps(out)


def test_subagent_can_use_read_only_git(tmp_path):
    repo = setup_repo(tmp_path)
    assert decision(git_from(repo, "git status --short")) == "allow"
    assert decision(git_from(repo, "git diff")) == "allow"


def test_main_session_still_commits(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo)
    assert decision(git_from(repo, "git commit -m x", agent=False)) == "allow"
