import pytest
from helpers import decision, git, make_repo, run_hook


def bash(cmd, repo):
    return decision(run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                                             "tool_input": {"command": cmd}}, repo))


@pytest.mark.parametrize("cmd", [
    "git push origin +main",
    "git -c push.default=current push --force",
    "npm test && git push --force-with-lease",
    "git push origin HEAD",
    "git push",
    "git push origin feat/x:main",
    "git push -uf origin feat/x",
    'git commit -m "fix a; b"',
    "FOO=1 git commit -m x",
])
def test_refused_on_main(cmd, tmp_path):
    assert bash(cmd, make_repo(tmp_path)) == "deny"


@pytest.mark.parametrize("cmd", ["git status", "git log --oneline", "npm test"])
def test_ordinary_commands_allowed(cmd, tmp_path):
    assert bash(cmd, make_repo(tmp_path)) == "allow"


def test_commit_and_push_allowed_on_a_branch(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "switch", "-q", "-c", "feat/x")
    assert bash("git commit -m ok", repo) == "allow"
    assert bash("git push origin feat/x", repo) == "allow"


def test_dormant_without_gantry_folder(tmp_path):
    assert bash("git push --force", make_repo(tmp_path, opted_in=False)) == "allow"


@pytest.mark.parametrize("cmd", ["rm -rf .gantry", "mv .gantry /tmp/x", "git rm -r .gantry"])
def test_harness_folder_protected(cmd, tmp_path):
    assert bash(cmd, make_repo(tmp_path)) == "deny"


def test_secret_in_command_refused(tmp_path):
    token = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
    assert bash(f"echo GITHUB_TOKEN={token} >> .env", make_repo(tmp_path)) == "deny"


def test_bad_input_fails_open(tmp_path):
    import subprocess, sys
    from helpers import HOOKS
    r = subprocess.run([sys.executable, str(HOOKS / "pre_bash.py")], input="not json",
                       capture_output=True, text=True)
    assert r.returncode == 0 and "couldn't run" in r.stdout
