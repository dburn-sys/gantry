"""Chapter 20: an issue number in the branch name rides along; the lane still decides."""
from helpers import decision, git, run_hook
from test_gantry_check import approve, repo_with_spec


def write_source(repo):
    return run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
                    "tool_input": {"file_path": str(repo / "src" / "export.ts"), "content": "export {}\n"}}, repo)


def test_numbered_feature_branch_finds_its_spec(tmp_path):
    repo = repo_with_spec(tmp_path)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "spec")
    git(repo, "switch", "-q", "-c", "feat/12-csv-export")
    assert decision(write_source(repo)) == "deny"
    approve(repo)
    assert decision(write_source(repo)) == "allow"
