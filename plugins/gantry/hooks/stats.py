"""Gantry stats: what the gates did here, for /gantry:stats.

    python stats.py [--root DIR] [--days 30]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def since(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def when(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def jsonl(f: Path):
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                yield json.loads(line)
            except ValueError:
                continue


def summarize(root: Path, days: int) -> str:
    start = since(days)
    g = root / ".gantry"
    denials, overrides_used = Counter(), Counter()
    for m in jsonl(g / "metrics.jsonl"):
        t = when(m.get("at", ""))
        if t and t >= start:
            (denials if m.get("decision") == "deny" else overrides_used)[m.get("gate", "?")] += 1
    reasons = Counter()
    if (g / "overrides.log").exists():
        for line in (g / "overrides.log").read_text(encoding="utf-8").splitlines():
            f = [x.strip() for x in line.split(" | ")]
            if len(f) >= 5 and f[4] != "used" and (when(f[0]) or start) >= start:
                reasons[(f[2], f[4])] += 1
    unproven = sum(1 for x in (g / "unproven.log").read_text(encoding="utf-8").splitlines() if x.strip()) \
        if (g / "unproven.log").exists() else 0
    findings, dispositions = Counter(), Counter()
    for report in (g / "runs").glob("*/report.md"):
        text = report.read_text(encoding="utf-8")
        if "## Review findings" not in text:
            continue
        for row in text.split("## Review findings", 1)[1].split("\n## ", 1)[0].splitlines():
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[1].upper() in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                rule = re.search(r"\b([A-Z]{1,4}-C?\d+)\b", cells[2]) or re.match(r"([a-z][a-z-]+)\b", cells[2])
                findings[rule.group(1) if rule else "unlabeled"] += 1
                dispositions[cells[-1].split(":")[0].split(" ")[0].lower() or "none"] += 1

    def top(c: Counter, n: int = 6) -> str:
        return ", ".join(f"{k} {v}" for k, v in c.most_common(n)) or "none"

    repeated = [f"{gate} x{n} \"{reason[:60]}\"" for (gate, reason), n in reasons.most_common() if n > 1]
    return "\n".join([
        f"Gantry stats, last {days} days ({root.name})",
        f"  Denials by gate:   {top(denials)}",
        f"  Overrides used:    {top(overrides_used)}",
        f"  Repeated reasons:  {'; '.join(repeated) or 'none'}",
        f"  Unproven commits:  {unproven}",
        f"  Findings by rule:  {top(findings, 8)}",
        f"  Dispositions:      {top(dispositions)}",
        "",
        "A gate overridden often for the same reason is pointing at a fix somewhere else.",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    print(summarize(Path(a.root).resolve(), a.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
