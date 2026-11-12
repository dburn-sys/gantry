"""Chapter 20: gantry-check verifies the paper trail in CI."""
import subprocess
import sys
from pathlib import Path

from helpers import make_repo, run_hook

CHECK = Path(__file__).resolve().parents[2] / "ci" / "gantry_check.py"


def check(repo, branch="main"):
    r = subprocess.run([sys.executable, str(CHECK), "--root", str(repo), "--branch", branch],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def repo_with_spec(tmp_path, slug="csv-export"):
    repo = make_repo(tmp_path)
    (repo / ".gantry" / "context.md").write_text("---\ngantry: enabled\n---\n")
    (repo / ".gantry" / "specs").mkdir()
    (repo / ".gantry" / "specs" / f"{slug}.md").write_text("# Spec\nStatus: draft\n")
    return repo


def approve(repo, slug="csv-export"):
    run_hook("prompt_submit.py", {"cwd": str(repo), "session_id": "s", "prompt": f"approve spec {slug}"}, repo)


def test_clean_repo_passes(tmp_path):
    repo = repo_with_spec(tmp_path)
    approve(repo)
    assert check(repo, "feat/12-csv-export")[0] == 0


def test_feature_branch_without_approved_spec_fails(tmp_path):
    code, out = check(repo_with_spec(tmp_path), "feat/12-csv-export")
    assert code == 1 and "no approved spec" in out


def test_edited_approval_log_fails(tmp_path):
    repo = repo_with_spec(tmp_path)
    approve(repo)
    (repo / ".gantry" / "specs" / "other.md").write_text("# Spec\nStatus: draft\n")
    approve(repo, "other")
    log = repo / ".gantry" / "approvals.jsonl"
    lines = log.read_text().splitlines()
    log.write_text("\n".join([lines[0].replace("csv-export", "csv-exports"), lines[1]]) + "\n")
    code, out = check(repo)
    assert code == 1 and "approvals.jsonl: hash chain broken at line 2" in out


def test_findings_need_dispositions_and_blocking_ones_a_person(tmp_path):
    repo = repo_with_spec(tmp_path)
    run = repo / ".gantry" / "runs" / "2026-05-02-feat-12-csv-export"
    run.mkdir(parents=True)
    (run / "report.md").write_text(
        "## Review findings\n| # | Severity | Finding | Disposition |\n| --- | --- | --- | --- |\n"
        "| 1 | HIGH | CSV injection | accepted: low risk |\n| 2 | LOW | naming |  |\n")
    code, out = check(repo)
    assert code == 1 and "finding 2 has no disposition" in out and "HIGH finding 1" in out


def test_repo_without_gantry_is_skipped(tmp_path):
    repo = make_repo(tmp_path, opted_in=False)
    assert check(repo)[0] == 0


def test_pr_without_a_run_report_is_labeled_not_failed(tmp_path):
    from helpers import git
    repo = repo_with_spec(tmp_path)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
    git(repo, "switch", "-q", "-c", "fix/typo")
    (repo / "README.md").write_text("hand-written fix\n")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "by hand")
    out_file = tmp_path / "gh_output"
    r = subprocess.run([sys.executable, str(CHECK), "--root", str(repo), "--branch", "fix/typo", "--base", "main"],
                       capture_output=True, text=True, env={**__import__("os").environ, "GITHUB_OUTPUT": str(out_file)})
    assert r.returncode == 0 and "no-gantry-run" in r.stdout
    assert out_file.read_text().strip() == "no_gantry_run=true"
    run = repo / ".gantry" / "runs" / "2026-07-02-fix-typo"
    run.mkdir(parents=True)
    (run / "report.md").write_text("# Run\n")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "through gantry")
    out_file.unlink()
    r = subprocess.run([sys.executable, str(CHECK), "--root", str(repo), "--branch", "fix/typo", "--base", "main"],
                       capture_output=True, text=True, env={**__import__("os").environ, "GITHUB_OUTPUT": str(out_file)})
    assert r.returncode == 0 and out_file.read_text().strip() == "no_gantry_run=false"
