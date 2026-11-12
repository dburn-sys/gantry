"""Gantry: add a lane hint to plain-English work requests."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import current_branch_or_none, emit, gantry_root, now_iso, read_input, run_hook  # noqa: E402

LANES = {
    "fix": r"\b(fix|bug|broken|breaks|error|fails?|failing|crash\w*|wrong|"
           r"regression|keeps?|shouldn't|should not|doesn't work)\b",
    "feature": r"\b(add|new|support|allow|let (users|finance|managers)|"
               r"can (we|you|finance|users)|export|import|feature)\b",
    "chore": r"\b(bump|upgrade|update (the )?(deps|dependencies|readme|docs)|"
             r"typo|readme|docs?|documentation|ci|lint config|revert)\b",
    "refactor": r"\b(refactor\w*|restructure|clean up|tidy|extract|"
                r"split (up|out)|without changing (behaviou?r|what it does))\b",
    "spike": r"\b(try|experiment|prototype|would it work|compare|"
             r"is it possible|spike)\b",
}
QUESTION = re.compile(r"^\s*(what|why|how does|how do|where|which|explain)\b|\?\s*$", re.I)
SKIP = re.compile(r"^\s*(/|approve spec |override |accept finding |gantry dev |btw\b)", re.I)
NEGATED = re.compile(r"\b(don'?t|do not|just|only)\b", re.I)


def classify(text: str) -> list[str]:
    lanes = [lane for lane, pat in LANES.items() if re.search(pat, text, re.I)]
    # "Don't add a new endpoint, just fix the existing one": the fix wins
    # when a sentence negates or narrows the feature words.
    if "fix" in lanes and "feature" in lanes:
        for sentence in re.split(r"[.!?;]", text):
            if NEGATED.search(sentence) and re.search(LANES["fix"], sentence, re.I):
                lanes.remove("feature")
                break
    return lanes


def record_sample(root: Path, lanes: list[str], prompt: str) -> None:
    """Keep a local, gitignored sample for tuning the keyword lists."""
    path = root / ".gantry" / "intent-samples.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now_iso(), "hint": lanes or None,
                            "text": prompt[:80]}) + "\n")


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None:
        return
    prompt = data.get("prompt", "")
    if SKIP.match(prompt):
        return                       # commands and Gantry phrases route themselves
    lanes = classify(prompt)
    record_sample(root, lanes, prompt)
    if not lanes:
        return
    branch = current_branch_or_none(root) or "unknown"
    if len(lanes) == 1:
        note = (f"Gantry routing note: this message matches the {lanes[0]} "
                f"lane. Current branch: {branch}. Work in that lane starts "
                f"with the gantry:intent-routing skill.")
    else:
        note = (f"Gantry routing note: this message matches more than one "
                f"lane ({', '.join(lanes)}). Current branch: {branch}. The "
                f"gantry:intent-routing skill asks the user which one.")
    if QUESTION.search(prompt):
        note += " It may also be a question; if so, answer without starting a lane."
    emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                 "additionalContext": note}})


if __name__ == "__main__":
    run_hook("intent hint", main)
