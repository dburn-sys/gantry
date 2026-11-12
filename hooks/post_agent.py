"""Gantry: record architecture conformance verdicts from architect reviewers."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import gantry_root, read_input, run_hook, tree_fingerprint  # noqa: E402

AGENT = re.compile(r"^gantry:architect-reviewer-([a-e])$", re.I)
VERDICT = re.compile(r"##\s*Section ([A-E]) verdict\s*\n+\s*(NON-CONFORMANT|CONFORMANT)\b")


def result_text(data: dict) -> str:
    """The subagent's final report. Its shape varies by Claude Code version."""
    resp = data.get("tool_response")
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        content = resp.get("content")
        if isinstance(content, list):          # [{"type": "text", "text": "..."}]
            return "\n".join(c.get("text", "") for c in content if isinstance(c, dict))
        if isinstance(content, str):
            return content
    return json.dumps(resp or "")


def main() -> None:
    data = read_input()
    if data.get("tool_name") not in ("Agent", "Task"):
        return
    root = gantry_root(data)
    if root is None:
        return
    kind = str((data.get("tool_input") or {}).get("subagent_type", ""))
    m = AGENT.search(kind)
    if not m:
        return                              # only Gantry's own reviewers count
    found = VERDICT.findall(result_text(data))
    if len(found) != 1 or found[0][0].lower() != m.group(1).lower():
        return                              # no single parseable verdict: record nothing
    section, verdict = found[0]
    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "section": section.upper(), "verdict": verdict,
              "tree": tree_fingerprint(root)}
    with (root / ".gantry" / "conformance.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    run_hook("conformance recorder", main)
