"""Chapter 18: hooks follow a subagent into its git worktree."""
from helpers import decision, git, run_hook
from test_evidence import setup_repo


def make(tmp_path):
    main_dir = tmp_path / "main"
    main_dir.mkdir()
    repo = setup_repo(main_dir)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
    wt = tmp_path / "main-wt-retries"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "feat/x-retries-wt")
    return repo, wt


def run_in(wt, project, command, hook="post_bash.py", passed=True):
    """The session started in `project`; the command ran in the worktree."""
    event = {"tool_name": "Bash", "cwd": str(wt), "session_id": "s1",
             "hook_event_name": "PostToolUse" if passed else "PostToolUseFailure",
             "tool_input": {"command": command}}
    return run_hook(hook, event, project)


def test_test_run_in_a_worktree_is_recorded_there(tmp_path):
    repo, wt = make(tmp_path)
    run_in(wt, repo, "sh test.sh")
    assert (wt / ".gantry" / "evidence.jsonl").exists()
    assert not (repo / ".gantry" / "evidence.jsonl").exists()


def test_commit_in_a_worktree_uses_the_worktrees_evidence(tmp_path):
    repo, wt = make(tmp_path)
    run_in(wt, repo, "sh test.sh")
    assert decision(run_in(wt, repo, "git commit -m x", hook="pre_bash.py")) == "allow"
    (wt / "app.txt").write_text("changed in the worktree\n")
    out = run_in(wt, repo, "git commit -m x", hook="pre_bash.py")
    assert decision(out) == "deny" and "files changed after" in str(out)


def test_same_checkout_still_uses_project_dir(tmp_path):
    repo, _ = make(tmp_path)
    sub = repo / "src"
    sub.mkdir()
    run_in(sub, repo, "sh test.sh")
    assert (repo / ".gantry" / "evidence.jsonl").exists()
