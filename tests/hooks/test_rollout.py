"""Chapter 24: warn-only mode, and the version note that leads to /gantry:repair."""
import json

from helpers import HOOKS, decision, make_repo, run_hook
from test_evidence import setup_repo

COMMIT = lambda repo: {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": "git commit -m x"}}  # noqa: E731


def test_warn_mode_allows_and_says_what_it_would_have_refused(tmp_path):
    repo = setup_repo(tmp_path)
    out = run_hook("pre_bash.py", COMMIT(repo), repo, {"GANTRY_GATES_WARN": "G-EVIDENCE"})
    assert decision(out) == "warn" and "would have refused" in out["systemMessage"]
    assert "[G-EVIDENCE]" in out["systemMessage"]
    events = [json.loads(x) for x in (repo / ".gantry" / "metrics.jsonl").read_text().splitlines()]
    assert events[-1]["decision"] == "would_deny" and events[-1]["gate"] == "G-EVIDENCE"


def test_only_listed_gates_are_relaxed(tmp_path):
    repo = setup_repo(tmp_path)
    out = run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                   "tool_input": {"command": "git push --force"}}, repo, {"GANTRY_GATES_WARN": "G-EVIDENCE"})
    assert decision(out) == "deny" and "[G-FORCE]" in json.dumps(out)


def test_star_puts_every_gate_in_warn_mode(tmp_path):
    repo = setup_repo(tmp_path)
    out = run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(repo),
                   "tool_input": {"command": "git push --force"}}, repo, {"GANTRY_GATES_WARN": "*"})
    assert decision(out) == "warn" and "[G-FORCE]" in out["systemMessage"]


def test_without_warn_mode_gates_block(tmp_path):
    repo = setup_repo(tmp_path)
    assert decision(run_hook("pre_bash.py", COMMIT(repo), repo)) == "deny"


def context(repo, plugin_version="1.2.0", recorded=None):
    ctx = "---\ngantry: enabled\n" + (f"gantry_version: {recorded}\n" if recorded else "") + "---\n"
    (repo / ".gantry" / "context.md").write_text(ctx)
    out = run_hook("session_start.py", {"cwd": str(repo)}, repo, {"CLAUDE_PLUGIN_ROOT": str(HOOKS.parent)})
    return out["hookSpecificOutput"]["additionalContext"]


def test_older_repo_is_pointed_at_repair(tmp_path):
    text = context(make_repo(tmp_path), recorded="1.0.0")
    assert "set up with Gantry 1.0.0" in text and "/gantry:repair" in text


def test_unrecorded_version_is_pointed_at_repair(tmp_path):
    assert "doesn't record which Gantry version" in context(make_repo(tmp_path))


def test_current_repo_gets_no_note(tmp_path):
    installed = json.loads((HOOKS.parent / ".claude-plugin" / "plugin.json").read_text())["version"]
    assert "Gantry upgrade" not in context(make_repo(tmp_path), recorded=installed)


def test_template_has_the_gantry_section():
    text = (HOOKS.parent / "templates" / "CLAUDE.md").read_text()
    for heading in ("## What this is", "## Commands", "## Layout", "## Hard rules", "## Gantry"):
        assert heading in text
