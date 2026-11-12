"""The gap found while building the companion repo: a command run from outside a
Gantry repo, but aimed at one, must meet that repo's gates."""
import json

from helpers import decision, make_repo, run_hook


def repo_on_main(tmp_path):
    repo = make_repo(tmp_path / "tally")
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\nnot_source: .gantry/, *.md\n---\n")
    return repo


def bash_from(outside, command):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(outside),
                                    "tool_input": {"command": command}}, outside)


def outside_dir(tmp_path):
    d = tmp_path / "home"
    d.mkdir()
    return d


def test_cd_into_a_gantry_repo_then_commit_is_gated(tmp_path):
    (tmp_path / "tally").mkdir()
    repo, home = repo_on_main(tmp_path), outside_dir(tmp_path)
    out = bash_from(home, f"cd {repo} && git commit -m x")
    assert decision(out) == "deny" and "[G-MAIN]" in json.dumps(out)


def test_relative_cd_is_followed(tmp_path):
    (tmp_path / "tally").mkdir()
    repo_on_main(tmp_path)
    out = bash_from(tmp_path, "cd tally && git commit -m x")
    assert decision(out) == "deny"


def test_git_dash_c_is_gated(tmp_path):
    (tmp_path / "tally").mkdir()
    repo, home = repo_on_main(tmp_path), outside_dir(tmp_path)
    out = bash_from(home, f"git -C {repo} commit -m x")
    assert decision(out) == "deny" and "[G-MAIN]" in json.dumps(out)


def test_harmless_commands_elsewhere_are_untouched(tmp_path):
    (tmp_path / "tally").mkdir()
    repo, home = repo_on_main(tmp_path), outside_dir(tmp_path)
    assert decision(bash_from(home, f"cd {repo} && git status")) == "allow"
    assert decision(bash_from(home, "cd /tmp && ls")) == "allow"


def test_absolute_write_into_a_gantry_repo_is_gated(tmp_path):
    (tmp_path / "tally").mkdir()
    repo, home = repo_on_main(tmp_path), outside_dir(tmp_path)
    out = run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(home),
                   "tool_input": {"file_path": str(repo / "src" / "app.ts"), "content": "x"}}, home)
    assert decision(out) == "deny" and "[G-LANE]" in json.dumps(out)
