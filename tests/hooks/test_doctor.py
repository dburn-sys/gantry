"""Chapter 22: the doctor's live fire proves the Bash hook runs, once."""
import subprocess
import sys

from helpers import HOOKS, make_repo, run_hook


def doctor(repo, *args):
    r = subprocess.run([sys.executable, str(HOOKS / "doctor.py"), "--root", str(repo), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def probe(repo, token, plugin_root=None):
    extra = {"CLAUDE_PLUGIN_ROOT": plugin_root} if plugin_root else None
    run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                             "tool_input": {"command": f"echo GANTRY_PROBE_{token}"}}, repo, extra)


def setup(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\ntest_command: npm test\n---\n")
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo, check=True)
    return repo


def test_new_token_is_sixteen_hex(tmp_path):
    code, out = doctor(setup(tmp_path), "--new-token")
    assert code == 0 and len(out.strip()) == 16 and int(out.strip(), 16) >= 0


def test_probe_seen_once_means_enforcing(tmp_path):
    repo = setup(tmp_path)
    probe(repo, "0123456789abcdef")
    code, out = doctor(repo, "--check", "0123456789abcdef")
    assert code == 0 and "live fire    ok" in out and "installed and enforcing" in out


def test_probe_missing_means_not_enforcing(tmp_path):
    code, out = doctor(setup(tmp_path), "--check", "0123456789abcdef")
    assert code == 1 and "the Bash hook is not running" in out and "NOT enforcing" in out


def test_probe_seen_twice_means_gantry_is_loaded_twice(tmp_path):
    repo = setup(tmp_path)
    probe(repo, "0123456789abcdef", "/marketplace/gantry")
    probe(repo, "0123456789abcdef", "/home/me/gantry/plugins/gantry")
    code, out = doctor(repo, "--check", "0123456789abcdef")
    assert code == 1 and "loaded more than once" in out


def test_session_start_nags_until_the_doctor_has_run(tmp_path):
    repo = setup(tmp_path)
    ctx = run_hook("session_start.py", {"cwd": str(repo)}, repo)["hookSpecificOutput"]["additionalContext"]
    assert "never run in this repository" in ctx
    probe(repo, "0123456789abcdef")
    ctx = run_hook("session_start.py", {"cwd": str(repo)}, repo)["hookSpecificOutput"]["additionalContext"]
    assert "Gantry health" not in ctx


def test_probe_needs_the_exact_command(tmp_path):
    repo = setup(tmp_path)
    for cmd in ("echo GANTRY_PROBE_0123456789abcdef && rm -rf x", "echo GANTRY_PROBE_xyz"):
        run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": cmd}}, repo)
    assert not (repo / ".gantry" / "probe.jsonl").exists()
