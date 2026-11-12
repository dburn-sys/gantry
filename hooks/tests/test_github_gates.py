"""Chapter 20: G-PR and G-MERGE, through gh and through the GitHub MCP server."""
import json

import pytest

from helpers import decision, git, run_hook
from test_evidence import record_run, setup_repo


def run(repo, command):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                                    "tool_input": {"command": command}}, repo)


def mcp(repo, tool, args=None):
    return run_hook("pre_mcp.py", {"tool_name": f"mcp__github__{tool}", "cwd": str(repo),
                                   "tool_input": args or {}}, repo)


def gate(out):
    return json.dumps(out)


@pytest.mark.parametrize("command", ["gh pr merge 12 --squash", "gh pr merge --auto --merge",
                                     "gh pr review 12 --approve", "gh pr review -a 12",
                                     "gh api -X PUT repos/o/r/pulls/12/merge",
                                     "GH_TOKEN=x gh pr merge 12"])
def test_agents_never_merge_or_approve(tmp_path, command):
    out = run(setup_repo(tmp_path), command)
    assert decision(out) == "deny" and "[G-MERGE]" in gate(out)


@pytest.mark.parametrize("tool,args", [("merge_pull_request", {"pullNumber": 12}),
                                       ("enable_pr_auto_merge", {"pullNumber": 12}),
                                       ("pull_request_review_write", {"method": "create", "event": "APPROVE"}),
                                       ("create_and_submit_pull_request_review", {"event": "APPROVE"})])
def test_mcp_merge_and_approve_are_refused(tmp_path, tool, args):
    out = mcp(setup_repo(tmp_path), tool, args)
    assert decision(out) == "deny" and "[G-MERGE]" in gate(out)


def test_mcp_review_comments_are_fine(tmp_path):
    repo = setup_repo(tmp_path)
    assert decision(mcp(repo, "pull_request_review_write", {"event": "COMMENT"})) == "allow"
    assert decision(mcp(repo, "get_pull_request", {"pullNumber": 12})) == "allow"


@pytest.mark.parametrize("via", ["gh", "mcp"])
def test_pr_needs_a_full_passing_run_of_this_code(tmp_path, via):
    repo = setup_repo(tmp_path)
    ask = (lambda: run(repo, "gh pr create --fill")) if via == "gh" else \
          (lambda: mcp(repo, "create_pull_request", {"title": "x"}))
    out = ask()
    assert decision(out) == "deny" and "[G-PR]" in gate(out)
    record_run(repo)
    assert decision(ask()) == "allow"
    (repo / "app.txt").write_text("changed after the run\n")
    assert decision(ask()) == "deny"


def test_pr_needs_dispositions(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo)
    run_dir = repo / ".gantry" / "runs" / "2026-05-02-feat-x"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text("## Review findings\n| # | Severity | Finding | Disposition |\n"
                                       "| --- | --- | --- | --- |\n| 1 | LOW | x |  |\n")
    out = run(repo, "gh pr create --fill")
    assert decision(out) == "deny" and "[G-PR]" in gate(out)


@pytest.mark.parametrize("branch", ["main", "spike/try-it"])
def test_no_pr_from_main_or_spikes(tmp_path, branch):
    repo = setup_repo(tmp_path)
    git(repo, "switch", "-q", "-C", branch)
    record_run(repo)
    assert decision(run(repo, "gh pr create --fill")) == "deny"


def test_read_only_gh_is_fine(tmp_path):
    repo = setup_repo(tmp_path)
    for command in ("gh issue view 12 --comments", "gh pr checks 12", "gh pr view 12", "gh run view 99 --log-failed"):
        assert decision(run(repo, command)) == "allow", command
