"""Shared helpers for Gantry hooks. Standard library only."""
import json
import os
import subprocess
import sys
from pathlib import Path


def read_input() -> dict:
    """Read the hook's JSON input from stdin."""
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    return data


def gantry_root(data: dict) -> Path | None:
    """Return the nearest folder containing .gantry/, or None (dormant)."""
    start = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    here = Path(start).resolve()
    for folder in [here, *here.parents]:
        if (folder / ".gantry").is_dir():
            return folder
    return None


def current_branch(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            cwd=root, capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git rev-parse failed")
    return result.stdout.strip()


def current_branch_or_none(root: Path) -> str | None:
    """The current branch, or None outside git or before the first commit."""
    try:
        return current_branch(root)
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return None


def emit(payload: dict) -> None:
    """Print a JSON response and exit successfully."""
    print(json.dumps(payload))
    sys.exit(0)


def deny(reason: str) -> None:
    emit({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }})


def warn_and_allow(check: str, exc: BaseException) -> None:
    """Principle 3: a check that can't run warns in one line and allows."""
    emit({"systemMessage":
          f"gantry: {check} couldn't run ({type(exc).__name__}: {exc}); "
          f"allowed without checking."})


def run_hook(check: str, main) -> None:
    """Run a hook's main(), turning any unexpected error into a warning."""
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - fail open on purpose
        warn_and_allow(check, exc)
    sys.exit(0)


def read_config(root: Path) -> dict:
    """Parse the flat key: value lines between the --- markers of .gantry/context.md."""
    f = root / ".gantry" / "context.md"
    if not f.exists():
        return {}
    lines = f.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    config = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            config[key.strip()] = value.strip()
    return config


def tree_fingerprint(root: Path) -> str:
    """A hash of HEAD plus every uncommitted change outside .gantry/, staged or not."""
    import hashlib

    def git(*args: str) -> bytes:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=15)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode(errors="replace").strip())
        return r.stdout

    outside_gantry = ["--", ".", ":(exclude).gantry"]
    h = hashlib.sha256()
    h.update(git("rev-parse", "HEAD"))
    h.update(git("diff", "HEAD", "--binary", *outside_gantry))
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", *outside_gantry)
    for name in sorted(filter(None, untracked.split(b"\0"))):
        h.update(name)
        h.update(git("hash-object", "--", name.decode()))
    return h.hexdigest()[:16]


def ledger_records(root: Path) -> list[dict]:
    ledger = root / ".gantry" / "evidence.jsonl"
    if not ledger.exists():
        return []
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def latest_run(root: Path) -> dict | None:
    records = ledger_records(root)
    return records[-1] if records else None


def has_uncommitted_changes(root: Path) -> bool:
    r = subprocess.run(["git", "status", "--porcelain", "--", ".", ":(exclude).gantry"],
                       cwd=root, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return bool(r.stdout.strip())


def approved(root: Path, slug: str) -> bool:
    f = root / ".gantry" / "approvals.jsonl"
    if not f.exists():
        return False
    return any(json.loads(line).get("spec") == slug
               for line in f.read_text(encoding="utf-8").splitlines() if line.strip())


LANES = ("feat/", "fix/", "chore/", "spike/", "refactor/")


def lane_of(branch: str) -> str | None:
    return next((p.rstrip("/") for p in LANES if branch.startswith(p)), None)


def _matches(rel: str, pattern: str) -> bool:
    import fnmatch
    pattern = pattern.strip()
    if not pattern:
        return False
    if pattern.endswith("/"):
        return rel.startswith(pattern) or ("/" + pattern) in ("/" + rel)
    return fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern)


def is_source(path: Path, root: Path, config: dict) -> bool:
    """Deny by default: everything is source unless not_source says otherwise."""
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False                       # outside the repo
    if "not_source" in config:
        return not any(_matches(rel, p) for p in config["not_source"].split(","))
    dirs = [d.strip().rstrip("/") + "/" for d in config.get("source_dirs", "src").split(",")]
    return any(rel.startswith(d) for d in dirs)


def is_test_file(path: Path, root: Path) -> bool:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    name = Path(rel).name
    return (rel.startswith(("test/", "tests/")) or ".test." in name or ".spec." in name
            or name.startswith("test_") or name.endswith("_test.py"))


def git_out(root: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10)
    return r.returncode, r.stdout.strip()


def existed_at_branch_point(root: Path, path: Path) -> bool:
    code, base = git_out(root, "merge-base", "HEAD", "main")
    if code != 0:
        code, base = git_out(root, "merge-base", "HEAD", "master")
    if code != 0:
        raise RuntimeError("no merge-base with main or master")
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    return git_out(root, "cat-file", "-e", f"{base}:{rel}")[0] == 0


def runs_on(root: Path, branch: str) -> list[dict]:
    return [r for r in ledger_records(root) if r.get("branch") == branch]


# ---- Chapter 14: overrides and hash-chained logs ------------------------------

GATES = {"G-MAIN", "G-FORCE", "G-SECRET", "G-HARNESS", "G-EVIDENCE", "G-SPEC", "G-FIX",
         "G-CHORE", "G-LANE", "G-SPIKE", "G-REFACTOR", "G-MIGRATION", "G-FINDINGS"}
TOKEN_MINUTES = 10


def _sha8(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def chain_append(path: Path, fields: list[str]) -> str:
    """Append ' | '-joined fields plus prev=<hash of the previous line>."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    prev = _sha8(lines[-1]) if lines else "00000000"
    line = " | ".join([*fields, f"prev={prev}"])
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def chain_verify(path: Path) -> int | None:
    """Return the 1-based number of the first line whose prev doesn't match, or None."""
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        expected = _sha8(lines[i - 1]) if i else "00000000"
        if not line.endswith(f"prev={expected}") and f'"prev": "{expected}"' not in line:
            return i + 1
    return None


def git_email(root: Path) -> str:
    code, out = git_out(root, "config", "user.email")
    return out if code == 0 and out else "unknown"


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def deny_unless_overridden(root: Path, gate: str, reason: str) -> None:
    """Deny with the gate ID, unless a fresh one-use override token names this gate."""
    from datetime import datetime, timezone
    token = root / ".gantry" / "override-token.json"
    if token.exists():
        t = json.loads(token.read_text(encoding="utf-8"))
        fresh = datetime.fromisoformat(t["expires"]) > datetime.now(timezone.utc)
        if t.get("gate") == gate and fresh:
            token.unlink()                                   # one use only
            chain_append(root / ".gantry" / "overrides.log",
                         [now_iso(), t.get("by", "unknown"), gate, current_branch(root), "used"])
            return
    deny(f"[{gate}] {reason}")
