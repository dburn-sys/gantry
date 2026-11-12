"""Gantry PreToolUse gate for file writes and edits."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import deny, gantry_root, read_input, run_hook  # noqa: E402
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
    return path.name == "secrets-allow.txt" and path.parent.name == ".gantry"


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
