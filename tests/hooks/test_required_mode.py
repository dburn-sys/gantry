"""Chapter 23 (ADR-0010): with GANTRY_REQUIRED=1, a repo without .gantry/ is uninitialized."""
import json

from helpers import decision, git, make_repo, run_hook

REQUIRED = {"GANTRY_REQUIRED": "1"}


def bare_repo(tmp_path):
    repo = make_repo(tmp_path, opted_in=False)
    git(repo, "config", "user.email", "dev@example.com")
    return repo


def write(repo, rel, env=REQUIRED):
    return run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
                    "tool_input": {"file_path": str(repo / rel), "content": "x"}}, repo, env)


def bash(repo, command, env=REQUIRED):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                    "tool_input": {"command": command}}, repo, env)


def test_source_writes_and_commits_are_refused(tmp_path):
    repo = bare_repo(tmp_path)
    out = write(repo, "src/app.ts")
    assert decision(out) == "deny" and "[G-INIT]" in json.dumps(out) and "/gantry:init" in json.dumps(out)
    assert decision(bash(repo, "git commit -m x")) == "deny"
    assert decision(bash(repo, "git push origin feat/x")) == "deny"


def test_setting_up_gantry_and_reading_are_allowed(tmp_path):
    repo = bare_repo(tmp_path)
    assert decision(write(repo, ".gantry/context.md")) == "allow"
    assert decision(bash(repo, "git status")) == "allow"
    assert decision(bash(repo, "grep -r TODO src")) == "allow"


def test_without_the_variable_principle_7_still_holds(tmp_path):
    repo = bare_repo(tmp_path)
    assert decision(write(repo, "src/app.ts", env={})) == "allow"
    assert decision(bash(repo, "git commit -m x", env={})) == "allow"


def test_outside_a_git_repository_nothing_changes(tmp_path):
    assert decision(write(tmp_path, "notes.md")) == "allow"


def test_g_init_is_overridable_and_logged_privately(tmp_path):
    repo = bare_repo(tmp_path)
    run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s",
             "prompt": "override G-INIT because hotfix for the outage, setting up Gantry tomorrow"}, repo, REQUIRED)
    assert decision(write(repo, "src/fix.ts")) == "allow"          # one use
    assert decision(write(repo, "src/fix.ts")) == "deny"
    log = (repo / ".git" / "gantry" / "overrides.log").read_text()
    assert "G-INIT" in log and "hotfix for the outage" in log
    assert not (repo / ".gantry").exists()                         # the override doesn't initialize


def test_other_override_phrases_do_nothing_before_init(tmp_path):
    repo = bare_repo(tmp_path)
    run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s",
             "prompt": "override G-EVIDENCE because the tests are slow today, honestly"}, repo, REQUIRED)
    assert not (repo / ".git" / "gantry" / "override-token.json").exists()


def test_session_start_explains(tmp_path):
    repo = bare_repo(tmp_path)
    out = run_hook("session_start.py", {"cwd": str(repo)}, repo, REQUIRED)
    assert "[G-INIT]" in out["hookSpecificOutput"]["additionalContext"]
