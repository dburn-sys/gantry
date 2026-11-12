"""Gantry PreToolUse gate for file writes and edits."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (approved, current_branch, deny, gantry_root, read_config,  # noqa: E402
                     read_input, run_hook)
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
    protected = {"secrets-allow.txt", "evidence.jsonl", "unproven.log", "approvals.jsonl"}
    return path.name in protected and path.parent.name == ".gantry"


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


def check_spec_gate(root: Path, path: Path, config: dict) -> None:
    source_dirs = [(root / d.strip()).resolve() for d in config.get("source_dirs", "src").split(",")]
    if not any(d in path.parents for d in source_dirs):
        return                                  # tests, docs, config: not gated
    branch = current_branch(root)
    if not branch.startswith("feat/"):
        return                                  # Chapter 13 handles other lanes
    slug = branch.removeprefix("feat/")
    if not approved(root, slug):
        deny(f"Gantry: no approved spec for {slug}. Feature code can't be "
             f"written until .gantry/specs/{slug}.md is approved. Run the "
             "gantry:brainstorming skill, then ask the user to type "
             f"`approve spec {slug}`.")


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

    if is_protected(path, root):
        deny(f"Gantry: {path.name} is part of the harness and can't be "
             "changed by the agent. Tell the user what you wanted to change.")

    if changes_status_line(path, tool, inp):
        deny("Gantry: a spec's Status line is written only when the user types "
             "the approval phrase. Leave it as it is.")

    check_spec_gate(root, path, read_config(root))

    allowed = load_allowlist(root)
    findings = [f for f in scan(new_text(tool, inp)) if f.preview not in allowed]
    if findings:
        lines = "; ".join(f"line {f.line}: {f.kind} ({f.preview})" for f in findings)
        deny(f"Gantry: possible secret in {path.name}: {lines}. Read the "
             "value from an environment variable instead, and put a "
             "placeholder in any example file. In tests, generate the value "
             "at runtime. If this is a false positive, stop and tell the "
             "user; only the user can allowlist it.")


if __name__ == "__main__":
    run_hook("pre-write gate", main)
