"""gantry-check: verify a repository's Gantry paper trail in CI.

Runs on a server, with no Claude Code involved, so it also covers commits made
outside Gantry. Usage (from the repository root):

    python <gantry>/ci/gantry_check.py [--branch <name>]

Exits 1 and lists every problem found. Checks:
  1. The hash chains in overrides.log, approvals.jsonl, and accepted-findings.log.
  2. A feat/ branch has an approved spec.
  3. Every finding in a committed run report has a disposition, and every CRITICAL
     or HIGH finding is fixed or accepted by a person (accepted-findings.log).

With --base <ref> (the PR's base branch), it also reports whether the PR went
through Gantry at all: a PR that adds or changes no .gantry/runs/*/report.md is
"no-gantry-run". That isn't a failure (people may write code by hand); it is
written to $GITHUB_OUTPUT as no_gantry_run=true so the workflow can label the
PR and send it to the CI reviewers (Chapter 23, ADR-0012).
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins" / "gantry" / "hooks"))
from _gantry import approved_for_branch, chain_verify, spec_slugs  # noqa: E402

CHAINED = ("overrides.log", "approvals.jsonl", "accepted-findings.log")


def accepted(root: Path) -> set[tuple[str, str]]:
    log = root / ".gantry" / "accepted-findings.log"
    out = set()
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            f = [x.strip() for x in line.split(" | ")]
            if len(f) >= 5:
                out.add((f[3], f[4]))
    return out


def report_problems(root: Path) -> list[str]:
    problems = []
    ok = accepted(root)
    for report in sorted((root / ".gantry" / "runs").glob("*/report.md")):
        run = report.parent.name
        text = report.read_text(encoding="utf-8")
        if "## Review findings" not in text:
            continue
        section = text.split("## Review findings", 1)[1].split("\n## ", 1)[0]
        rows = [r for r in section.splitlines() if r.startswith("|") and not set(r) <= set("|- ")]
        if not rows:
            continue
        cols = [c.strip().lower() for c in rows[0].strip("|").split("|")]
        if "disposition" not in cols:
            continue
        i, sev = cols.index("disposition"), cols.index("severity") if "severity" in cols else None
        num = cols.index("#") if "#" in cols else 0
        for r in rows[1:]:
            cells = [c.strip() for c in r.strip("|").split("|")]
            if len(cells) <= i:
                continue
            n, disposition = cells[num], cells[i].lower()
            if not disposition:
                problems.append(f"{run}: finding {n} has no disposition")
            elif sev is not None and cells[sev].upper() in ("CRITICAL", "HIGH") \
                    and not disposition.startswith("fixed") \
                    and not (disposition.startswith("accepted") and (run, n) in ok):
                problems.append(f"{run}: {cells[sev].upper()} finding {n} is neither fixed "
                                "nor accepted by a person")
    return problems


def went_through_gantry(root: Path, base: str) -> bool:
    import subprocess
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"can't diff against {base}")
    return any(re.match(r"^\.gantry/runs/[^/]+/report\.md$", p) for p in r.stdout.splitlines())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--base", help="PR base ref, e.g. origin/main, to detect a PR with no Gantry run")
    ap.add_argument("--branch", default=os.environ.get("GITHUB_HEAD_REF")
                    or os.environ.get("GITHUB_REF_NAME") or "")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if not (root / ".gantry").is_dir():
        print("gantry-check: no .gantry/ folder; nothing to check.")
        return 0
    problems = []
    for name in CHAINED:
        line = chain_verify(root / ".gantry" / name)
        if line is not None:
            problems.append(f"{name}: hash chain broken at line {line}")
    if a.branch.startswith("feat/") and not approved_for_branch(root, a.branch):
        problems.append(f"{a.branch}: no approved spec ({' or '.join(spec_slugs(a.branch))})")
    problems += report_problems(root)
    if a.base:
        gantry_run = went_through_gantry(root, a.base)
        print(f"gantry-check: {'run report found' if gantry_run else 'no-gantry-run: no run report in this PR'}")
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a", encoding="utf-8") as f:
                f.write(f"no_gantry_run={'false' if gantry_run else 'true'}\n")
    for p in problems:
        print(f"gantry-check: {p}")
    print(f"gantry-check: {'FAILED' if problems else 'ok'} ({len(problems)} problem(s))")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
