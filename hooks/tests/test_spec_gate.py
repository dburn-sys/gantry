"""Chapter 12: approvals recorded from the human side, and the spec gate."""
import json
from helpers import decision, git, make_repo, run_hook

SPEC = "# Spec: Approval workflow\nStatus: draft\n\n## Open questions\n"


def setup(tmp_path, spec_extra=""):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\nsource_dirs: src\n---\n")
    (repo / ".gantry" / "specs").mkdir()
    (repo / ".gantry" / "specs" / "approval-workflow.md").write_text(SPEC + spec_extra)
    git(repo, "switch", "-q", "-c", "feat/approval-workflow")
    return repo


def prompt(repo, text):
    return run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s1", "prompt": text}, repo)


def write(repo, rel, content="x = 1\n"):
    return decision(run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(repo),
        "tool_input": {"file_path": str(repo / rel), "content": content}}, repo))


def test_source_refused_before_approval(tmp_path):
    assert write(setup(tmp_path), "src/approvals/states.ts") == "deny"


def test_tests_are_not_gated(tmp_path):
    assert write(setup(tmp_path), "test/approvals.test.ts") == "allow"


def test_approval_phrase_records_and_unlocks(tmp_path):
    repo = setup(tmp_path)
    out = prompt(repo, "approve spec approval-workflow")
    assert "recorded approval" in json.dumps(out)
    assert json.loads((repo / ".gantry" / "approvals.jsonl").read_text())["spec"] == "approval-workflow"
    assert "Status: approved" in (repo / ".gantry" / "specs" / "approval-workflow.md").read_text()
    assert write(repo, "src/approvals/states.ts") == "allow"


def test_unresolved_confirm_blocks_approval(tmp_path):
    repo = setup(tmp_path, "[CONFIRM-01] What happens when the submitter leaves?\n")
    out = prompt(repo, "approve spec approval-workflow")
    assert out.get("decision") == "block"
    assert not (repo / ".gantry" / "approvals.jsonl").exists()


def test_resolved_confirm_allows_approval(tmp_path):
    repo = setup(tmp_path, "[CONFIRM-01] Submitter leaves? (resolved: it stays submitted)\n")
    assert prompt(repo, "approve spec approval-workflow").get("decision") is None


def test_unknown_spec_blocks(tmp_path):
    assert prompt(setup(tmp_path), "approve spec nope").get("decision") == "block"


def test_ordinary_prompts_pass_through(tmp_path):
    assert prompt(setup(tmp_path), "please add a filter") == {}


def test_agent_cannot_write_status_or_approvals(tmp_path):
    repo = setup(tmp_path)
    approved_spec = SPEC.replace("Status: draft", "Status: approved 2026-01-01")
    assert write(repo, ".gantry/specs/approval-workflow.md", approved_spec) == "deny"
    assert write(repo, ".gantry/approvals.jsonl", '{"spec": "approval-workflow"}') == "deny"


def test_agent_can_edit_spec_body(tmp_path):
    repo = setup(tmp_path)
    assert write(repo, ".gantry/specs/approval-workflow.md", SPEC + "AC-1: Given x, when y, then z.\n") == "allow"
