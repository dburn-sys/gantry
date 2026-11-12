"""Chapter 21: sprint state survives compaction; the sprint log is append-only."""
from helpers import decision, make_repo, run_hook

LOG = """# Sprint: expense-policies
Status: {status}
Plan: .gantry/plans/expense-policies.md
Started: 2026-06-20T09:00:00Z

### D-1: Warning wording (task T-2)
Confidence: 4
{extra}"""

PLAN = """# Plan
### T-1: Policies table
- State: ACCEPTED
### T-2: Check on submit
- State: ACCEPTED
### T-3: Show warnings
- State: IN-PROGRESS
### T-4: Dashboard
- State: PENDING
"""


def sprint_repo(tmp_path, status="running", extra=""):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\n---\n")
    (repo / ".gantry" / "plans").mkdir()
    (repo / ".gantry" / "plans" / "expense-policies.md").write_text(PLAN)
    (repo / ".gantry" / "sprint-log.md").write_text(LOG.format(status=status, extra=extra))
    return repo


def context(repo):
    out = run_hook("session_start.py", {"cwd": str(repo), "source": "compact"}, repo)
    return out["hookSpecificOutput"]["additionalContext"]


def test_running_sprint_is_in_the_context(tmp_path):
    text = context(sprint_repo(tmp_path))
    assert "Sprint expense-policies is running: 2 of 4 tasks accepted; next T-3." in text


def test_stopped_sprint_names_the_stop(tmp_path):
    text = context(sprint_repo(tmp_path, "stopped", "### S-1: Hard stop (authorization)\nWaiting.\n"))
    assert "is stopped" in text and "Waiting on the user for S-1" in text


def test_finished_sprint_is_not_mentioned(tmp_path):
    assert "Sprint expense-policies" not in context(sprint_repo(tmp_path, "finished"))


def write(repo, content=None, tool="Write", **extra):
    inp = {"file_path": str(repo / ".gantry" / "sprint-log.md"), **extra}
    if content is not None:
        inp["content"] = content
    return run_hook("pre_write.py", {"tool_name": tool, "cwd": str(repo), "tool_input": inp}, repo)


def test_appending_and_prepending_a_summary_are_allowed(tmp_path):
    repo = sprint_repo(tmp_path)
    old = (repo / ".gantry" / "sprint-log.md").read_text()
    assert decision(write(repo, old + "### D-2: New decision\nConfidence: 3\n")) == "allow"
    assert decision(write(repo, "## Sprint summary: expense-policies\n\n" + old)) == "allow"


def test_rewriting_an_entry_is_refused(tmp_path):
    repo = sprint_repo(tmp_path)
    old = (repo / ".gantry" / "sprint-log.md").read_text()
    assert decision(write(repo, old.replace("Confidence: 4", "Confidence: 5"))) == "deny"
    assert decision(write(repo, tool="Edit", old_string="Confidence: 4", new_string="Confidence: 5")) == "deny"
