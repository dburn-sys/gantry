"""Shared helpers for Gantry hooks. Standard library only."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def read_input() -> dict:
    """Read the hook's JSON input from stdin."""
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    return data


def _toplevel(path: str) -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path,
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return str(Path(r.stdout.strip()).resolve()) if r.returncode == 0 else None


def in_other_worktree(cwd: str) -> bool:
    """True when cwd is inside a different git checkout than CLAUDE_PROJECT_DIR.

    CLAUDE_PROJECT_DIR is set once, when the session starts. A subagent working
    in a git worktree runs its commands somewhere else, and Gantry must look at
    that checkout: its tests, its tree, its branch.
    """
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project or not Path(cwd).is_dir():
        return False
    mine = _toplevel(cwd)
    return mine is not None and mine != _toplevel(project)


def gantry_root(data: dict) -> Path | None:
    """Return the nearest folder containing .gantry/, or None (dormant)."""
    cwd = data.get("cwd")
    start = cwd if cwd and in_other_worktree(cwd) else (
        os.environ.get("CLAUDE_PROJECT_DIR") or cwd or ".")
    here = Path(start).resolve()
    for folder in [here, *here.parents]:
        if (folder / ".gantry").is_dir():
            return folder
    return None


def uninitialized_repo(data: dict) -> Path | None:
    """Chapter 23 (ADR-0010): with GANTRY_REQUIRED=1 from managed settings, a git
    repository with no .gantry/ is uninitialized, not dormant. Returns its top
    folder, or None (not required, not a git repo, or already initialized)."""
    if os.environ.get("GANTRY_REQUIRED") != "1" or gantry_root(data) is not None:
        return None
    cwd = data.get("cwd")
    start = cwd if cwd and in_other_worktree(cwd) else (
        os.environ.get("CLAUDE_PROJECT_DIR") or cwd or ".")
    top = _toplevel(str(start)) if Path(str(start)).is_dir() else None
    return Path(top) if top else None


def state_dir(root: Path) -> Path:
    """Where override tokens, override logs, and metrics live: .gantry/ once a repo
    is initialized; before that (G-INIT), a private folder inside .git/."""
    g = root / ".gantry"
    if g.is_dir():
        return g
    d = root / ".git" / "gantry"
    d.mkdir(parents=True, exist_ok=True)
    return d


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


def spec_slugs(branch: str) -> list[str]:
    """feat/12-csv-export -> ["12-csv-export", "csv-export"]: an issue number rides along."""
    slug = branch.split("/", 1)[-1]
    bare = re.sub(r"^\d+-", "", slug)
    return [slug] if bare == slug else [slug, bare]


def approved_for_branch(root: Path, branch: str) -> str | None:
    """The approved spec slug for this branch, or None."""
    return next((s for s in spec_slugs(branch) if approved(root, s)), None)


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
         "G-CHORE", "G-LANE", "G-SPIKE", "G-REFACTOR", "G-MIGRATION", "G-FINDINGS",
         "G-SUBAGENT", "G-ARCH", "G-PR", "G-MERGE", "G-INIT"}

INIT_REASON = ("Gantry is required in this organization, and this repository isn't set "
               "up yet. Run /gantry:init (it takes a minute), or ask the user to.")
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
    token = state_dir(root) / "override-token.json"
    if token.exists():
        t = json.loads(token.read_text(encoding="utf-8"))
        fresh = datetime.fromisoformat(t["expires"]) > datetime.now(timezone.utc)
        if t.get("gate") == gate and fresh:
            token.unlink()                                   # one use only
            chain_append(state_dir(root) / "overrides.log",
                         [now_iso(), t.get("by", "unknown"), gate, current_branch(root), "used"])
            record_metric(root, {"gate": gate, "decision": "override"})
            return
    record_metric(root, {"gate": gate, "decision": "deny"})
    deny(f"[{gate}] {reason}")


def record_metric(root: Path, event: dict) -> None:
    """Chapter 22: one local line per gate decision, for /gantry:stats. Never fails a hook."""
    try:
        with (state_dir(root) / "metrics.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now_iso(), **event}) + "\n")
    except OSError:
        pass


def dev_mode(root: Path, data: dict) -> bool:
    """Chapter 22: maintainer dev mode needs both keys: GANTRY_DEV=1 from the human's
    shell, and `gantry dev on because ...` typed in this session."""
    if os.environ.get("GANTRY_DEV") != "1":
        return False
    f = root / ".gantry" / "dev-mode.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("session") == data.get("session_id")
    except (OSError, ValueError):
        return False


# --- Chapter 19: architecture conformance -------------------------------------

SECTION_FILES = {"A": "A-services.md", "B": "B-data.md", "C": "C-security.md",
                 "D": "D-ai.md", "E": "E-cloud.md"}


def changed_paths(root: Path) -> list[str]:
    """Every path that differs from HEAD, staged or not, plus untracked files."""
    _, diff = git_out(root, "diff", "HEAD", "--name-only")
    _, untracked = git_out(root, "ls-files", "--others", "--exclude-standard")
    return sorted({p for p in (diff + "\n" + untracked).splitlines() if p.strip()})


def section_map(root: Path) -> dict[str, list[str]]:
    """Parse .gantry/architecture/sections.md: section letter -> path patterns."""
    f = root / ".gantry" / "architecture" / "sections.md"
    out: dict[str, list[str]] = {}
    if not f.exists():
        return out
    for line in f.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and len(cells[0]) == 1 and cells[0].isalpha():
            pats = [p.split(" (")[0].strip() for p in cells[1].split(",")]
            out[cells[0].upper()] = [p for p in pats if p and not p.startswith("any ")] + \
                [p[4:].strip() for p in pats if p.startswith("any ")]
    return out


def sections_touched(root: Path, paths: list[str] | None = None) -> set[str]:
    paths = changed_paths(root) if paths is None else paths
    touched = set()
    for section, patterns in section_map(root).items():
        if any(_matches(p, pat) for p in paths for pat in patterns):
            touched.add(section)
    return touched


def latest_verdicts(root: Path) -> dict[str, dict]:
    f = root / ".gantry" / "conformance.jsonl"
    out: dict[str, dict] = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            out[r.get("section", "?")] = r
    return out
