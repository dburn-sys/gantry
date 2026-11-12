"""Chapter 11: the evidence ledger and the commit check."""
from helpers import decision, git, make_repo, run_hook


def setup_repo(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\ntest_command: sh test.sh\n---\n")
    (repo / "test.sh").write_text("exit 0\n")
    (repo / "app.txt").write_text("v1\n")
    git(repo, "switch", "-q", "-c", "feat/x")
    return repo


def record_run(repo, command="sh test.sh", passed=True, background=False):
    event = {"tool_name": "Bash", "cwd": str(repo), "session_id": "s1",
             "hook_event_name": "PostToolUse" if passed else "PostToolUseFailure",
             "tool_input": {"command": command, "run_in_background": background}}
    run_hook("post_bash.py", event, repo)


def commit(repo):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                                    "tool_input": {"command": "git commit -m x"}}, repo)


def ledger(repo):
    f = repo / ".gantry" / "evidence.jsonl"
    return f.read_text().splitlines() if f.exists() else []


def test_no_run_recorded_refuses(tmp_path):
    out = commit(setup_repo(tmp_path))
    assert decision(out) == "deny" and "no test run recorded" in str(out)


def test_full_passing_run_on_current_tree_allows(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo)
    assert decision(commit(repo)) == "allow"


def test_edit_after_run_refuses(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo)
    (repo / "app.txt").write_text("v2\n")
    out = commit(repo)
    assert decision(out) == "deny" and "files changed after" in str(out)


def test_failing_run_refuses(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo, passed=False)
    out = commit(repo)
    assert decision(out) == "deny" and "failed" in str(out)


def test_partial_run_refuses(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo, command="sh test.sh test/auth.test.ts")
    out = commit(repo)
    assert decision(out) == "deny" and "partial" in str(out)


def test_piped_run_is_not_recorded(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo, command="sh test.sh 2>&1 | tail -20")
    assert ledger(repo) == []


def test_background_run_is_not_recorded(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo, background=True)
    assert ledger(repo) == []


def test_gantry_files_written_after_run_do_not_make_it_stale(tmp_path):
    repo = setup_repo(tmp_path)
    record_run(repo)
    runs = repo / ".gantry" / "runs"
    runs.mkdir()
    (runs / "report.md").write_text("# Run report\n")
    (repo / ".gantry" / "overrides.log").write_text("entry\n")
    assert decision(commit(repo)) == "allow"


def test_ledger_is_protected_from_writes(tmp_path):
    repo = setup_repo(tmp_path)
    out = run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
        "tool_input": {"command": "echo '{}' >> .gantry/evidence.jsonl"}}, repo)
    assert decision(out) == "deny"
    out = run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
        "tool_input": {"file_path": str(repo / ".gantry" / "evidence.jsonl"), "content": "{}"}}, repo)
    assert decision(out) == "deny"


def stop(repo, active=False):
    return run_hook("stop_check.py", {"cwd": str(repo), "stop_hook_active": active}, repo)


def test_stop_nudges_when_untested_changes(tmp_path):
    repo = setup_repo(tmp_path)
    (repo / "app.txt").write_text("v2\n")
    assert stop(repo).get("decision") == "block"


def test_stop_never_loops(tmp_path):
    repo = setup_repo(tmp_path)
    (repo / "app.txt").write_text("v2\n")
    assert stop(repo, active=True) == {}


def test_stop_quiet_after_passing_run(tmp_path):
    repo = setup_repo(tmp_path)
    (repo / "app.txt").write_text("v2\n")
    record_run(repo)
    assert stop(repo) == {}
