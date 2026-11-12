"""Chapter 18: blocking findings are fixed, or accepted by a person."""
import json

from helpers import decision
from test_override import commit, prompt, setup

REPORT = """# Run: spike/payouts
## Review findings
| # | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| 1 | MEDIUM | Missing index | deferred: [NEEDS-TRIAGE] TALLY-12 |
| 2 | HIGH | Retry can double-pay after a timeout | {d} |
"""


def repo_with(tmp_path, disposition):
    repo = setup(tmp_path, branch="spike/payouts")
    run = repo / ".gantry" / "runs" / "2026-05-20-spike-payouts"
    run.mkdir(parents=True)
    (run / "report.md").write_text(REPORT.format(d=disposition))
    return repo


def test_fixed_blocking_finding_allows(tmp_path):
    assert decision(commit(repo_with(tmp_path, "fixed in 9f2c1ab"))) == "allow"


def test_blocking_finding_cant_be_deferred(tmp_path):
    out = commit(repo_with(tmp_path, "deferred: [NEEDS-TRIAGE] TALLY-13"))
    assert decision(out) == "deny" and "blocking finding(s) 2" in json.dumps(out)


def test_agent_written_acceptance_is_not_enough(tmp_path):
    out = commit(repo_with(tmp_path, "accepted: the provider dedupes by idempotency key"))
    assert decision(out) == "deny"


def test_person_accepts_with_a_reason(tmp_path):
    repo = repo_with(tmp_path, "accepted: the provider dedupes by idempotency key")
    prompt(repo, "accept finding 2 because the provider dedupes retries by idempotency key")
    log = (repo / ".gantry" / "accepted-findings.log").read_text()
    assert "2026-05-20-spike-payouts | 2 |" in log and "prev=00000000" in log
    assert decision(commit(repo)) == "allow"


def test_acceptance_needs_a_real_reason(tmp_path):
    repo = repo_with(tmp_path, "accepted: fine")
    out = prompt(repo, "accept finding 2 because fine")
    assert out.get("decision") == "block"
    assert not (repo / ".gantry" / "accepted-findings.log").exists()


def test_acceptance_is_per_run(tmp_path):
    repo = repo_with(tmp_path, "accepted: see log")
    prompt(repo, "accept finding 2 because the provider dedupes retries by idempotency key")
    newer = repo / ".gantry" / "runs" / "2026-05-21-spike-payouts"
    newer.mkdir()
    (newer / "report.md").write_text(REPORT.format(d="accepted: see log"))
    assert decision(commit(repo)) == "deny"
