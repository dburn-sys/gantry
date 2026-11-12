"""Chapter 19: conformance verdicts are recorded by the hook, from the reviewer's own output."""
import json

import pytest

from helpers import git, make_repo, run_hook

REPORT = "## Section {s} checklist\n| Item | Result | Evidence |\n| E-C1 | PASS | Dockerfile:1 |\n\n## Section {s} verdict\n{v}\n"


def repo(tmp_path):
    r = make_repo(tmp_path)
    (r / ".gantry" / "context.md").write_text("---\ngantry: enabled\n---\n")
    git(r, "add", "-A")
    git(r, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
    return r


def agent_returns(r, subagent, text, tool="Agent", shape="string"):
    response = text if shape == "string" else {"content": [{"type": "text", "text": text}]}
    run_hook("post_agent.py", {"tool_name": tool, "cwd": str(r),
                               "tool_input": {"subagent_type": subagent, "prompt": "review"},
                               "tool_response": response}, r)


def records(r):
    f = r / ".gantry" / "conformance.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


@pytest.mark.parametrize("tool,shape", [("Agent", "string"), ("Task", "string"), ("Agent", "content")])
def test_records_gantry_reviewer_verdict(tmp_path, tool, shape):
    r = repo(tmp_path)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="CONFORMANT"), tool, shape)
    [rec] = records(r)
    assert rec["section"] == "E" and rec["verdict"] == "CONFORMANT" and len(rec["tree"]) == 16


def test_non_conformant_is_recorded_as_such(tmp_path):
    r = repo(tmp_path)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="NON-CONFORMANT"))
    assert records(r)[0]["verdict"] == "NON-CONFORMANT"


@pytest.mark.parametrize("subagent", ["architect-reviewer-e", "myproject:architect-reviewer-e",
                                      "gantry:code-reviewer", "general-purpose"])
def test_other_agents_are_ignored(tmp_path, subagent):
    r = repo(tmp_path)
    agent_returns(r, subagent, REPORT.format(s="E", v="CONFORMANT"))
    assert records(r) == []


def test_section_must_match_the_reviewer(tmp_path):
    r = repo(tmp_path)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="A", v="CONFORMANT"))
    assert records(r) == []


def test_unparseable_or_doubled_verdicts_record_nothing(tmp_path):
    r = repo(tmp_path)
    agent_returns(r, "gantry:architect-reviewer-e", "Looks fine to me. CONFORMANT")
    both = REPORT.format(s="E", v="NON-CONFORMANT") + REPORT.format(s="E", v="CONFORMANT")
    agent_returns(r, "gantry:architect-reviewer-e", both)
    assert records(r) == []


def test_dormant_without_gantry(tmp_path):
    r = make_repo(tmp_path, opted_in=False)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="CONFORMANT"))
    assert not (r / ".gantry").exists()
