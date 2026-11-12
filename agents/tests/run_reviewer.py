"""Run a Gantry reviewer against its planted-bug test set."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AGENT, RUNS = sys.argv[1], int(os.environ.get("RUNS", "3"))
HERE = Path(__file__).parent / AGENT
PLUGIN = Path(__file__).parents[2]
# Architect reviewers read the project's .gantry/architecture/, so they run in a
# small fixture project instead of the current folder.
PROJECT = Path(__file__).parent / "architect-project" if AGENT.startswith("architect-reviewer") else None


def review(diff: str) -> str:
    prompt = (f"Use the gantry:{AGENT} agent to review this change. "
              f"Return its output exactly.\n\n```diff\n{diff}\n```")
    out = subprocess.run(
        ["claude", "-p", prompt, "--plugin-dir", str(PLUGIN),
         "--add-dir", str(PLUGIN),          # so the agent can read standards/
         "--output-format", "json"],
        capture_output=True, text=True, timeout=600, cwd=PROJECT)
    return json.loads(out.stdout)["result"]


def rules_found(report: str) -> set[str]:
    if PROJECT:   # architect reviewers: rules cited in FAIL rows of a NON-CONFORMANT checklist
        if not re.search(r"verdict\s*\n+\s*NON-CONFORMANT", report):
            return set()
        fails = [row for row in report.splitlines() if re.search(r"\|\s*FAIL\s*\|", row)]
        return {r for row in fails for r in re.findall(r"\b([A-E]-\d+)\b", row)}
    return set(re.findall(r"\|\s*(?:CRITICAL|HIGH|MEDIUM|LOW)\s*\|\s*([A-Z]+-\d+)", report))


def expected_rule(case: Path) -> str:
    """ts3-floating-promise.diff -> TS-3; mig2-edit-old.diff -> MIG-2."""
    prefix = case.stem.split("-")[0]
    return re.sub(r"^([a-z]+)(\d+)$", r"\1-\2", prefix).upper()


def main() -> None:
    misses, false_alarms = [], []
    for case in sorted((HERE / "planted").glob("*.diff")):
        want = expected_rule(case)
        for n in range(RUNS):
            if want not in rules_found(review(case.read_text())):
                misses.append(f"{case.name} run {n + 1}")
    for case in sorted((HERE / "clean").glob("*.diff")):
        for n in range(RUNS):
            if found := rules_found(review(case.read_text())):
                false_alarms.append(f"{case.name} run {n + 1}: {sorted(found)}")
    print(f"misses: {len(misses)}", *misses, sep="\n  ")
    print(f"false alarms: {len(false_alarms)}", *false_alarms, sep="\n  ")
    sys.exit(1 if misses or false_alarms else 0)


if __name__ == "__main__":
    main()
