"""Chapter 13: lanes."""
import json
from helpers import decision, git, make_repo, run_hook

CONFIG = "---\ngantry: enabled\ntest_command: sh test.sh\nnot_source: test/, docs/, .gantry/, *.md, package.json\n---\n"


def setup(tmp_path, branch):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text(CONFIG)
    (repo / "test").mkdir()
    (repo / "test" / "app.test.ts").write_text("old test\n")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
    git(repo, "switch", "-q", "-c", branch)
    return repo


def write(repo, rel, content="x = 1\n"):
    return decision(run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
        "tool_input": {"file_path": str(repo / rel), "content": content}}, repo))


def record(repo, passed):
    run_hook("post_bash.py", {"tool_name": "Bash", "cwd": str(repo), "session_id": "s",
        "hook_event_name": "PostToolUse" if passed else "PostToolUseFailure",
        "tool_input": {"command": "sh test.sh"}}, repo)


def bash(repo, cmd):
    return decision(run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                                             "tool_input": {"command": cmd}}, repo))


def test_no_lane_blocks_source(tmp_path):
    assert write(setup(tmp_path, "approvals-v2"), "src/rules.ts") == "deny"


def test_new_top_level_folder_is_source(tmp_path):
    assert write(setup(tmp_path, "approvals-v2"), "lib/rules.ts") == "deny"


def test_chore_can_change_docs_and_manifests(tmp_path):
    repo = setup(tmp_path, "chore/readme")
    assert write(repo, "README.md", "fixed typo\n") == "allow"
    assert write(repo, "package.json", "{}\n") == "allow"


def test_chore_cannot_touch_source(tmp_path):
    assert write(setup(tmp_path, "chore/rename-state"), "src/states.ts") == "deny"


def test_fix_needs_a_failing_run_first(tmp_path):
    repo = setup(tmp_path, "fix/self-approval")
    assert write(repo, "src/approvals.ts") == "deny"
    record(repo, passed=False)
    assert write(repo, "src/approvals.ts") == "allow"


def test_refactor_needs_green_baseline(tmp_path):
    repo = setup(tmp_path, "refactor/split-service")
    assert write(repo, "src/service.ts") == "deny"
    record(repo, passed=True)
    assert write(repo, "src/service.ts") == "allow"


def test_refactor_freezes_existing_tests_but_allows_new_ones(tmp_path):
    repo = setup(tmp_path, "refactor/split-service")
    assert write(repo, "test/app.test.ts", "changed\n") == "deny"
    assert write(repo, "test/seam.test.ts", "new\n") == "allow"


def test_spike_writes_freely_and_commits_without_evidence(tmp_path):
    repo = setup(tmp_path, "spike/tenancy-rls")
    assert write(repo, "src/rls.ts") == "allow"
    assert bash(repo, "git commit -m wip") == "allow"


def test_spike_cannot_merge(tmp_path):
    repo = setup(tmp_path, "feat/x")
    assert bash(repo, "git merge spike/tenancy-rls") == "deny"
    assert bash(repo, "git cherry-pick spike/tenancy-rls") == "deny"


def test_renaming_into_another_lane_is_refused(tmp_path):
    repo = setup(tmp_path, "fix/slow")
    assert bash(repo, "git branch -m spike/slow") == "deny"
    assert bash(repo, "git branch -m fix/slow-totals") == "allow"
