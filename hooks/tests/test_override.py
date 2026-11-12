"""Chapter 14: overrides, hash chains, migrations, and finding dispositions."""
import json
import sys
from pathlib import Path

from helpers import HOOKS, decision, git, make_repo, run_hook

sys.path.insert(0, str(HOOKS))
from _gantry import chain_verify  # noqa: E402

CONFIG = "---\ngantry: enabled\ntest_command: sh test.sh\nnot_source: test/, .gantry/, *.md\n---\n"


def setup(tmp_path, branch="fix/flaky"):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text(CONFIG)
    git(repo, "config", "user.email", "dev@example.com")
    (repo / "test.sh").write_text("exit 0\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "switch", "-q", "-c", branch)
    return repo


def prompt(repo, text):
    return run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s", "prompt": text}, repo)


def commit(repo):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                                    "tool_input": {"command": "git commit -m x"}}, repo)


def test_deny_reason_names_the_gate(tmp_path):
    out = commit(setup(tmp_path))
    assert out["hookSpecificOutput"]["permissionDecisionReason"].startswith("[G-EVIDENCE]")


def test_override_allows_exactly_once(tmp_path):
    repo = setup(tmp_path)
    reason = "session expiry test is flaky (timing), tracked in TALLY-88"
    prompt(repo, f"override G-EVIDENCE because {reason}")
    assert decision(commit(repo)) == "allow"
    assert decision(commit(repo)) == "deny"
    log = (repo / ".gantry" / "overrides.log").read_text().splitlines()
    assert "dev@example.com | G-EVIDENCE | fix/flaky | " + reason in log[0]
    assert log[1].endswith(log[1].split(" | ")[-1]) and " | used | " in log[1]
    assert chain_verify(repo / ".gantry" / "overrides.log") is None


def test_override_only_applies_to_the_named_gate(tmp_path):
    repo = setup(tmp_path)
    prompt(repo, "override G-SECRET because this is a known false positive here")
    assert decision(commit(repo)) == "deny"


def test_short_or_unknown_override_is_rejected(tmp_path):
    repo = setup(tmp_path)
    assert prompt(repo, "override G-EVIDENCE because flaky").get("decision") == "block"
    assert prompt(repo, "override G-NOPE because this gate does not exist at all").get("decision") == "block"


def test_tampering_breaks_the_chain(tmp_path):
    repo = setup(tmp_path)
    prompt(repo, "override G-EVIDENCE because first reason with enough words here")
    prompt(repo, "override G-EVIDENCE because second reason with enough words here")
    log = repo / ".gantry" / "overrides.log"
    lines = log.read_text().splitlines()
    lines[0] = lines[0].replace("first", "edited")
    log.write_text("\n".join(lines) + "\n")
    assert chain_verify(log) == 2


def test_agent_cannot_touch_override_files(tmp_path):
    repo = setup(tmp_path)
    for name in ("overrides.log", "override-token.json"):
        out = run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
            "tool_input": {"file_path": str(repo / ".gantry" / name), "content": "{}"}}, repo)
        assert decision(out) == "deny"


def test_committed_migration_cannot_be_edited(tmp_path):
    repo = setup(tmp_path, branch="spike/x")
    (repo / "migrations").mkdir()
    (repo / "migrations" / "001_init.sql").write_text("CREATE TABLE t (id int);\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "migration")
    def write(name):
        return decision(run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
            "tool_input": {"file_path": str(repo / "migrations" / name), "content": "x"}}, repo))
    assert write("001_init.sql") == "deny"
    assert write("002_next.sql") == "allow"


REPORT = """# Run: fix/flaky
## Review findings
| # | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| 1 | MEDIUM | Clock skew not handled | fixed in a1b2c3d |
| 2 | LOW | Error reveals token age | {d} |
"""


def test_findings_need_dispositions(tmp_path):
    repo = setup(tmp_path, branch="spike/flaky")       # spike: no evidence check in the way
    run_dir = repo / ".gantry" / "runs" / "2026-04-21-spike-flaky"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text(REPORT.format(d=""))
    out = commit(repo)
    assert decision(out) == "deny" and "[G-FINDINGS]" in json.dumps(out)
    (run_dir / "report.md").write_text(REPORT.format(d="deferred: [NEEDS-TRIAGE] TALLY-91"))
    assert decision(commit(repo)) == "allow"
