"""Gantry PreToolUse gate for file writes and edits."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (approved_for_branch, spec_slugs, approved, current_branch, deny_unless_overridden,  # noqa: E402
                     existed_at_branch_point, gantry_root, git_out, is_source,
                     is_test_file, lane_of, read_config, read_input, run_hook, runs_on)
from _secrets import scan  # noqa: E402


def new_text(tool: str, inp: dict) -> str:
    if tool == "Write":
        return inp.get("content", "")
    if tool == "Edit":
        return inp.get("new_string", "")
    return ""


def is_protected(path: Path, root: Path) -> bool:
    """Harness files the agent must not change."""
    plugin = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin and Path(plugin).resolve() in [path, *path.parents]:
        return True
    protected = {"secrets-allow.txt", "evidence.jsonl", "unproven.log", "approvals.jsonl",
                 "overrides.log", "override-token.json", "accepted-findings.log",
                 "conformance.jsonl"}
    if path.name in protected and path.parent.name == ".gantry":
        return True
    rel = path.relative_to(root).as_posix() if root in path.parents else ""
    # The architecture is a set of human decisions; agents and settings change
    # what Gantry and Claude Code do in future sessions.
    return (rel.startswith(".gantry/architecture/") or rel.startswith(".claude/agents/")
            or (rel.startswith(".claude/settings") and rel.endswith(".json")))


def changes_status_line(path: Path, tool: str, inp: dict) -> bool:
    """Only Gantry's approval recorder may write a spec's Status line."""
    if path.parent.name != "specs" or path.parent.parent.name != ".gantry":
        return False
    if tool == "Edit":
        return "Status:" in inp.get("old_string", "") or "Status:" in inp.get("new_string", "")
    if tool == "Write" and path.exists():
        old = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("Status:")]
        new = [l for l in inp.get("content", "").splitlines() if l.startswith("Status:")]
        return old != new
    return any(l.startswith("Status:") and l != "Status: draft"
               for l in inp.get("content", "").splitlines())


def check_lane_gates(root: Path, path: Path, config: dict) -> None:
    """Chapters 12 and 13: what each lane needs before source can change."""
    source = is_source(path, root, config)
    branch = current_branch(root)
    lane = lane_of(branch)
    if lane == "refactor" and is_test_file(path, root) and path.exists() \
            and existed_at_branch_point(root, path):
        deny_unless_overridden(root, "G-REFACTOR", "Gantry: refactor lane. Existing tests are frozen here, because "
             "passing them unchanged is the proof that behavior didn't change. "
             "If a test must change, this is a fix or a feature.")
    if not source:
        return                                  # tests, docs, config: not gated
    if lane is None:
        deny_unless_overridden(root, "G-LANE", f"Gantry: branch {branch} has no lane. Rename it with "
             "`git branch -m <lane>/<name>` (feat, fix, chore, refactor, or spike), "
             "or ask the user which kind of work this is.")
    if lane == "feat":
        slug = spec_slugs(branch)[-1]
        if not approved_for_branch(root, branch):
            deny_unless_overridden(root, "G-SPEC", f"Gantry: no approved spec for {slug}. Feature code can't be "
                 f"written until .gantry/specs/{slug}.md is approved. Run the "
                 "gantry:brainstorming skill, then ask the user to type "
                 f"`approve spec {slug}`.")
    if lane == "fix" and not any(not r["passed"] for r in runs_on(root, branch)):
        deny_unless_overridden(root, "G-FIX", "Gantry: fix lane. Write a test that reproduces the bug and run it "
             "so it fails, before changing source. The failing run is the proof "
             "the bug exists; the later passing run is the proof the fix works.")
    if lane == "chore":
        deny_unless_overridden(root, "G-CHORE", "Gantry: chore lane. Chores don't change source code. This change "
             "touches source, so it's a fix or a feature. Tell the user, and "
             "suggest /gantry:fix or /gantry:feature.")
    if lane == "refactor" and not any(r["passed"] and r["scope"] == "full"
                                      for r in runs_on(root, branch)):
        deny_unless_overridden(root, "G-REFACTOR", "Gantry: refactor lane. Run the full suite first so there's a "
             "green baseline to compare against.")


def check_migration_gate(root: Path, path: Path, config: dict) -> None:
    mig_dir = (root / config.get("migrations_dir", "migrations")).resolve()
    if mig_dir not in path.parents:
        return
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    if git_out(root, "cat-file", "-e", f"HEAD:{rel}")[0] == 0:
        deny_unless_overridden(root, "G-MIGRATION",
            f"Gantry: {path.name} is already committed. Databases that ran it won't "
            "run it again. Write a new numbered migration instead.")


def load_allowlist(root: Path) -> set[str]:
    f = root / ".gantry" / "secrets-allow.txt"
    if not f.exists():
        return set()
    return {line.strip() for line in f.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def main() -> None:
    data = read_input()
    tool = data.get("tool_name")
    if tool not in ("Write", "Edit"):
        return
    root = gantry_root(data)
    if root is None:
        return
    inp = data.get("tool_input") or {}
    path = (root / inp.get("file_path", "")).resolve()

    if path.name == "sprint-log.md" and path.parent.name == ".gantry" and path.exists():
        old = path.read_text(encoding="utf-8")
        new = inp.get("content") if tool == "Write" else None
        if new is None or old not in new:
            deny_unless_overridden(root, "G-HARNESS", "Gantry: the sprint log is append-only. "
                 "Write the whole file with every earlier entry unchanged, adding new "
                 "entries (or the summary at the top); don't edit what's there.")

    if is_protected(path, root):
        deny_unless_overridden(root, "G-HARNESS", f"Gantry: {path.name} is part of the harness and can't be "
             "changed by the agent. Tell the user what you wanted to change.")

    if changes_status_line(path, tool, inp):
        deny_unless_overridden(root, "G-HARNESS", "Gantry: a spec's Status line is written only when the user types "
             "the approval phrase. Leave it as it is.")

    config = read_config(root)
    check_migration_gate(root, path, config)
    check_lane_gates(root, path, config)

    allowed = load_allowlist(root)
    findings = [f for f in scan(new_text(tool, inp)) if f.preview not in allowed]
    if findings:
        lines = "; ".join(f"line {f.line}: {f.kind} ({f.preview})" for f in findings)
        deny_unless_overridden(root, "G-SECRET", f"Gantry: possible secret in {path.name}: {lines}. Read the "
             "value from an environment variable instead, and put a "
             "placeholder in any example file. In tests, generate the value "
             "at runtime. If this is a false positive, stop and tell the "
             "user; only the user can allowlist it.")


if __name__ == "__main__":
    run_hook("pre-write gate", main)
