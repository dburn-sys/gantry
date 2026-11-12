"""Chapter 22: status line, metrics and stats, and maintainer dev mode."""
import json
import subprocess
import sys

from helpers import HOOKS, decision, git, run_hook
from test_evidence import record_run, setup_repo


def status(repo):
    r = subprocess.run([sys.executable, str(HOOKS / "statusline.py")],
                       input=json.dumps({"workspace": {"current_dir": str(repo)}}), capture_output=True, text=True)
    return r.stdout.strip()


def test_status_line_tracks_the_evidence(tmp_path):
    repo = setup_repo(tmp_path)
    assert "tests: none" in status(repo)
    record_run(repo)
    assert status(repo).startswith("gantry  feat/x  tests: green (current)")
    (repo / "app.txt").write_text("v2\n")
    assert "tests: STALE (" in status(repo)


def test_status_line_is_silent_outside_gantry(tmp_path):
    r = subprocess.run([sys.executable, str(HOOKS / "statusline.py")], input="{}", capture_output=True,
                       text=True, cwd=tmp_path)
    assert r.stdout.strip() == ""


def test_statusline_installer_backs_up_and_only_removes_its_own(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"model": "x"}))
    run = lambda *a: subprocess.run([sys.executable, str(HOOKS / "statusline_install.py"), *a,  # noqa: E731
                                     "--settings", str(settings)], capture_output=True, text=True)
    assert run("install").returncode == 0
    assert "gantry-statusline" in json.loads(settings.read_text())["statusLine"]["command"]
    assert (tmp_path / "settings.json.gantry-backup").exists()
    assert run("remove").returncode == 0
    assert json.loads(settings.read_text()) == {"model": "x"}
    settings.write_text(json.dumps({"statusLine": {"type": "command", "command": "mine.sh"}}))
    assert run("install").returncode == 1
    assert json.loads(settings.read_text())["statusLine"]["command"] == "mine.sh"


def test_denials_and_overrides_are_counted(tmp_path):
    repo = setup_repo(tmp_path)
    git(repo, "config", "user.email", "dev@example.com")
    commit = {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": "git commit -m x"}}
    run_hook("pre_bash.py", commit, repo)
    run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s",
             "prompt": "override G-EVIDENCE because the session expiry test is flaky again"}, repo)
    run_hook("pre_bash.py", commit, repo)
    lines = [json.loads(x) for x in (repo / ".gantry" / "metrics.jsonl").read_text().splitlines()]
    assert [(m["gate"], m["decision"]) for m in lines] == [("G-EVIDENCE", "deny"), ("G-EVIDENCE", "override")]
    out = subprocess.run([sys.executable, str(HOOKS / "stats.py"), "--root", str(repo)],
                         capture_output=True, text=True).stdout
    assert "Denials by gate:   G-EVIDENCE 1" in out and "Overrides used:    G-EVIDENCE 1" in out


def write_plugin_file(repo, plugin, session="s1", env=None):
    target = plugin / "hooks" / "x.py"
    return run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo), "session_id": session,
                    "tool_input": {"file_path": str(target), "content": "x"}}, repo,
                    {"CLAUDE_PLUGIN_ROOT": str(plugin), **(env or {})})


def test_dev_mode_needs_both_keys(tmp_path):
    repo = setup_repo(tmp_path / "repo") if False else setup_repo(tmp_path)
    git(repo, "config", "user.email", "dev@example.com")
    plugin = repo / "plugins" / "gantry"
    (plugin / "hooks").mkdir(parents=True)
    say = lambda text, env=None: run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s1",  # noqa: E731
                                          "prompt": text}, repo, env)
    reason = "gantry dev on because fixing the launcher on windows paths"
    assert decision(write_plugin_file(repo, plugin)) == "deny"                         # neither key
    assert say(reason).get("decision") == "block"                                      # phrase, no env
    assert decision(write_plugin_file(repo, plugin, env={"GANTRY_DEV": "1"})) == "deny"  # env, no phrase
    say(reason, {"GANTRY_DEV": "1"})
    assert decision(write_plugin_file(repo, plugin, env={"GANTRY_DEV": "1"})) == "allow"
    assert decision(write_plugin_file(repo, plugin, session="other", env={"GANTRY_DEV": "1"})) == "deny"
    assert "G-HARNESS (dev mode)" in (repo / ".gantry" / "overrides.log").read_text()
    say("gantry dev off", {"GANTRY_DEV": "1"})
    assert decision(write_plugin_file(repo, plugin, env={"GANTRY_DEV": "1"})) == "deny"


def test_dev_mode_never_relaxes_other_gates(tmp_path):
    repo = setup_repo(tmp_path)
    git(repo, "config", "user.email", "dev@example.com")
    run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s1",
             "prompt": "gantry dev on because fixing the launcher on windows paths"}, repo, {"GANTRY_DEV": "1"})
    out = run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo), "session_id": "s1",
                   "tool_input": {"command": "git commit -m x"}}, repo, {"GANTRY_DEV": "1"})
    assert decision(out) == "deny" and "G-EVIDENCE" in json.dumps(out)
