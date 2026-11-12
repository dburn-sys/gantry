"""Chapter 19: G-ARCH refuses commits without a CONFORMANT review of the current code."""
import json

from helpers import decision, git, make_repo, run_hook
from test_evidence import record_run
from test_post_agent import REPORT, agent_returns

SECTIONS = """| Section | Touched when the change includes |
| --- | --- |
| A | src/contracts/**, src/routes/** |
| E | infra/**, Dockerfile*, .github/** |
"""


def gated(tmp_path, with_files=("A-services.md", "E-cloud.md")):
    r = make_repo(tmp_path)
    (r / ".gantry" / "context.md").write_text("---\ngantry: enabled\ntest_command: sh test.sh\n---\n")
    (r / "test.sh").write_text("exit 0\n")
    arch = r / ".gantry" / "architecture"
    arch.mkdir()
    (arch / "sections.md").write_text(SECTIONS)
    for f in with_files:
        (arch / f).write_text(f"# {f}\n## Conformance checklist\nX-C1: ok?\n")
    git(r, "add", "-A")
    git(r, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
    git(r, "switch", "-q", "-c", "feat/m6")
    return r


def commit(r):
    return run_hook("pre_bash.py", {"tool_name": "Bash", "cwd": str(r),
                                    "tool_input": {"command": "git commit -m x"}}, r)


def change_dockerfile(r, text="FROM node:22\n"):
    (r / "Dockerfile").write_text(text)
    record_run(r)


def test_untouched_sections_need_nothing(tmp_path):
    r = gated(tmp_path)
    (r / "README.md").write_text("docs\n")
    record_run(r)
    assert decision(commit(r)) == "allow"


def test_touched_section_without_review_is_refused(tmp_path):
    r = gated(tmp_path)
    change_dockerfile(r)
    out = commit(r)
    assert decision(out) == "deny" and "[G-ARCH]" in json.dumps(out) and "Section E" in json.dumps(out)


def test_conformant_review_of_this_tree_allows(tmp_path):
    r = gated(tmp_path)
    change_dockerfile(r)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="CONFORMANT"))
    assert decision(commit(r)) == "allow"


def test_non_conformant_is_refused(tmp_path):
    r = gated(tmp_path)
    change_dockerfile(r)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="NON-CONFORMANT"))
    out = commit(r)
    assert decision(out) == "deny" and "NON-CONFORMANT" in json.dumps(out)


def test_edit_after_review_is_refused(tmp_path):
    r = gated(tmp_path)
    change_dockerfile(r)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="CONFORMANT"))
    change_dockerfile(r, "FROM node:22\nUSER root\n")
    assert decision(commit(r)) == "deny"


def test_every_touched_section_needs_its_own_review(tmp_path):
    r = gated(tmp_path)
    (r / "src" / "routes").mkdir(parents=True)
    (r / "src" / "routes" / "x.ts").write_text("export {}\n")
    change_dockerfile(r)
    agent_returns(r, "gantry:architect-reviewer-e", REPORT.format(s="E", v="CONFORMANT"))
    out = commit(r)
    assert decision(out) == "deny" and "Section A" in json.dumps(out)


def test_missing_section_file_is_not_gated(tmp_path):
    r = gated(tmp_path, with_files=("A-services.md",))
    change_dockerfile(r)
    assert decision(commit(r)) == "allow"


def test_no_architecture_folder_is_not_gated(tmp_path):
    r = gated(tmp_path)
    git(r, "rm", "-rq", ".gantry/architecture")
    git(r, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "drop arch")
    change_dockerfile(r)
    assert decision(commit(r)) == "allow"


def test_agent_cannot_write_architecture_agents_or_settings(tmp_path):
    r = gated(tmp_path)
    for rel in (".gantry/architecture/E-cloud.md", ".claude/agents/architect-reviewer-e.md",
                ".claude/settings.json", ".claude/settings.local.json", ".gantry/conformance.jsonl"):
        out = run_hook("pre_write.py", {"tool_name": "Write", "cwd": str(r),
                       "tool_input": {"file_path": str(r / rel), "content": "x"}}, r)
        assert decision(out) == "deny", rel
