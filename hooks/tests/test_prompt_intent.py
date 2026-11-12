"""Chapter 15: the intent hint. One row per real message, with the lane we want.

When you tune the keyword lists, add every miss here first, then change the
lists until the whole table passes.
"""
import json
import sys

import pytest

from helpers import HOOKS, git, make_repo, run_hook

sys.path.insert(0, str(HOOKS))
from prompt_intent import classify  # noqa: E402

TABLE = [
    # fix
    ("managers keep approving their own expenses through the integration API", ["fix"]),
    ("the total is wrong when an expense has cents", ["fix"]),
    ("login fails for emails with capital letters", ["fix"]),
    ("the approve endpoint crashes on a bad id", ["fix"]),
    ("POST /expenses returns 500 instead of 400, that's a bug", ["fix"]),
    ("history shouldn't show other people's changes", ["fix"]),
    ("the session expiry check doesn't work after midnight", ["fix"]),
    ("Don't add a new endpoint, just fix the existing one", ["fix"]),
    ("this is broken since yesterday's merge", ["fix"]),
    # feature
    ("can finance export approved expenses as a CSV", ["feature"]),
    ("add a receipt upload to expenses", ["feature"]),
    ("let managers set a monthly limit per employee", ["feature"]),
    ("support euros and pounds as currencies", ["feature"]),
    ("we need a new report of spend by category", ["feature"]),
    ("allow employees to withdraw a submitted expense", ["feature"]),
    # chore
    ("bump fastify to the latest minor", ["chore"]),
    ("fix the typo in the README", ["fix", "chore"]),
    ("update the docs for the approval API", ["chore"]),
    ("upgrade vitest", ["chore"]),
    ("revert yesterday's lint config change", ["chore"]),
    # refactor
    ("refactor the approval service into smaller functions", ["refactor"]),
    ("extract the money helpers into their own module", ["refactor"]),
    ("clean up app.ts without changing behaviour", ["refactor"]),
    # spike
    ("try a schema per company and see how migrations feel", ["spike"]),
    ("is it possible to stream the CSV instead of building it in memory", ["spike"]),
    ("prototype a receipt reader with the model", ["spike"]),
    # more than one
    ("add CSV export and fix the broken totals", ["fix", "feature"]),
    # questions and conversation: no hint
    ("where is the RLS policy defined", []),
    ("thanks, that looks good", []),
    ("explain how sessions are signed", []),
]


@pytest.mark.parametrize("text,lanes", TABLE)
def test_table(text, lanes):
    assert sorted(classify(text)) == sorted(lanes)


def hint(repo, prompt):
    out = run_hook("prompt_intent.py", {"cwd": str(repo), "session_id": "s", "prompt": prompt}, repo)
    return out["hookSpecificOutput"]["additionalContext"] if out else None


def repo_on(tmp_path, branch="main"):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\n---\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    if branch != "main":
        git(repo, "switch", "-q", "-c", branch)
    return repo


def test_note_names_the_lane_and_branch(tmp_path):
    repo = repo_on(tmp_path, "feat/approval-workflow")
    note = hint(repo, "the approve button is broken")
    assert "fix lane" in note and "feat/approval-workflow" in note


def test_ambiguous_message_asks(tmp_path):
    note = hint(repo_on(tmp_path), "add CSV export and fix the broken totals")
    assert "more than one lane" in note


def test_question_about_a_bug_says_both(tmp_path):
    note = hint(repo_on(tmp_path), "why does the total come out wrong?")
    assert "fix lane" in note and "question" in note


@pytest.mark.parametrize("prompt", ["/gantry:fix totals", "btw, where is the policy?",
                                    "override G-EVIDENCE because the flaky test again today",
                                    "approve spec csv-export"])
def test_commands_and_phrases_get_no_hint(tmp_path, prompt):
    assert hint(repo_on(tmp_path), prompt) is None


def test_dormant_without_gantry(tmp_path):
    repo = make_repo(tmp_path, opted_in=False)
    assert hint(repo, "the total is wrong") is None


def test_samples_are_recorded_locally(tmp_path):
    repo = repo_on(tmp_path)
    hint(repo, "the total is wrong")
    hint(repo, "thanks")
    lines = [json.loads(x) for x in (repo / ".gantry" / "intent-samples.jsonl").read_text().splitlines()]
    assert [x["hint"] for x in lines] == [["fix"], None]
