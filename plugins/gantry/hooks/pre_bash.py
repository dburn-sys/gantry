"""Gantry PreToolUse gate for shell commands."""
import os
import json
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (current_branch, deny_unless_overridden, gantry_root,  # noqa: E402
                     lane_of, latest_run, read_config, read_input, run_hook,
                     tree_fingerprint)
from _secrets import scan  # noqa: E402
from _gantry import INIT_REASON, now_iso, uninitialized_repo, SECTION_FILES, latest_verdicts, sections_touched  # noqa: E402

PROTECTED = {"main", "master"}
GIT_OPTS_WITH_VALUE = {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}
HARNESS_DIR = ".gantry"
LEDGER_FILES = ("evidence.jsonl", "unproven.log")


def writes_into_harness(command: str) -> bool:
    """Redirects, tee, or in-place edits aimed at .gantry/ files."""
    return bool(re.search(r"(>>?|\btee\b(\s+-a)?|\bsed\s+-i\S*)\s*\S*\.gantry/", command))


def warn_unproven(root: Path, reason: str) -> None:
    with (root / ".gantry" / "unproven.log").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "
                f"commit allowed unchecked: {reason}\n")


class _Allowed(Exception):
    """Raised after an override lets a check through, to skip its remaining steps."""


def check_findings(root: Path, branch: str, gate: str = "G-FINDINGS") -> None:
    """G-FINDINGS: every review finding in this branch's run report needs a disposition."""
    runs = sorted((root / ".gantry" / "runs").glob(f"*{branch.replace('/', '-')}*/report.md"))
    if not runs:
        return
    text = runs[-1].read_text(encoding="utf-8")
    if "## Review findings" not in text:
        return
    section = text.split("## Review findings", 1)[1].split("\n## ", 1)[0]
    rows = [r for r in section.splitlines() if r.startswith("|") and not set(r) <= set("|- ")]
    header, *body = rows or [""]
    cols = [c.strip().lower() for c in header.strip("|").split("|")]
    if "disposition" not in cols:
        return
    i = cols.index("disposition")
    sev = cols.index("severity") if "severity" in cols else None
    num = cols.index("#") if "#" in cols else None
    accepted = accepted_findings(root, runs[-1].parent.name)
    open_rows, unaccepted = [], []
    for r in body:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if len(cells) <= i:
            continue
        disposition = cells[i].lower()
        if not disposition:
            open_rows.append(r)
            continue
        blocking = sev is not None and cells[sev].upper() in ("CRITICAL", "HIGH")
        if blocking and not disposition.startswith("fixed"):
            n = cells[num] if num is not None else "?"
            if not (disposition.startswith("accepted") and n in accepted):
                unaccepted.append(n)
    if open_rows:
        deny_unless_overridden(root, gate,
            f"Gantry: {len(open_rows)} review finding(s) in {runs[-1].parent.name} have no "
            "disposition. Mark each one fixed (with the commit), accepted (with a "
            "reason), or deferred ([NEEDS-TRIAGE] and a ticket).")
    if unaccepted:
        deny_unless_overridden(root, gate,
            f"Gantry: blocking finding(s) {', '.join(unaccepted)} in {runs[-1].parent.name} "
            "aren't fixed. A CRITICAL or HIGH finding is either fixed, or accepted by a "
            "person typing: accept finding <n> because <reason>.")


def accepted_findings(root: Path, run: str) -> set[str]:
    """Finding numbers a person accepted for this run, from the chained log."""
    log = root / ".gantry" / "accepted-findings.log"
    if not log.exists():
        return set()
    out = set()
    for line in log.read_text(encoding="utf-8").splitlines():
        fields = [f.strip() for f in line.split(" | ")]
        if len(fields) >= 5 and fields[3] == run:
            out.add(fields[4])
    return out


def check_conformance(root: Path) -> None:
    """G-ARCH: every touched architecture section has a CONFORMANT review of this exact tree."""
    arch = root / ".gantry" / "architecture"
    if not arch.is_dir():
        return                                   # not architecture-gated
    present = {s for s in sections_touched(root)
               if s in SECTION_FILES and (arch / SECTION_FILES[s]).exists()}
    if not present:
        return
    tree = tree_fingerprint(root)
    latest = latest_verdicts(root)
    for s in sorted(present):
        r = latest.get(s)
        if r is None or r.get("tree") != tree:
            deny_unless_overridden(root, "G-ARCH",
                f"Gantry: Section {s} is touched and has no conformance review of "
                "the current code. Run the gantry:conformance skill, then commit again.")
            return
        if r.get("verdict") != "CONFORMANT":
            deny_unless_overridden(root, "G-ARCH",
                f"Gantry: Section {s} is NON-CONFORMANT. Fix the failing checklist "
                "items through gantry:tdd, re-run gantry:conformance, then commit.")
            return


def check_evidence(root: Path, test_command: str, gate: str = "G-EVIDENCE") -> None:
    run = latest_run(root)
    how = (f"Run `{test_command}` exactly (no extra file or test arguments, "
           "no pipes or redirects, not in the background), then try again.")
    def deny(reason: str) -> None:
        deny_unless_overridden(root, gate, reason)
        raise _Allowed

    if run is None:
        deny(f"Gantry: no test run recorded in this repository. {how}")
    if run["scope"] != "full":
        deny(f"Gantry: the last test run ({run['at']}) was partial: "
             f"`{run['command']}`. Commits need a full-suite run. {how}")
    if not run["passed"]:
        deny(f"Gantry: the last test run ({run['at']}) failed. Fix the "
             f"failures through the gantry:tdd skill. {how}")
    try:
        current = tree_fingerprint(root)
    except Exception as exc:  # noqa: BLE001 - principle 3, recorded as unproven
        warn_unproven(root, f"{type(exc).__name__}: {exc}")
        raise
    if run["tree"] != current:
        deny(f"Gantry: files changed after the last passing test run "
             f"({run['at']}). The tests haven't run against this code. {how}")


def gh_args(words: list[str]) -> list[str] | None:
    """If these words run the GitHub CLI, return its arguments."""
    i = 0
    while i < len(words) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[i]):
        i += 1
    if i >= len(words) or Path(words[i]).name.lower() not in ("gh", "gh.exe"):
        return None
    return words[i + 1:] or None


def refuse_merge(root: Path, what: str) -> None:
    deny_unless_overridden(root, "G-MERGE",
        f"Gantry: agents don't {what}. A person merges, in GitHub or their own "
        "terminal, after reading the PR. Tell the user the PR is ready.")


def check_pr_create(root: Path) -> None:
    """G-PR: a PR is opened only for finished, evidenced, fully dispositioned work."""
    branch = current_branch(root)
    if branch in PROTECTED or lane_of(branch) == "spike":
        deny_unless_overridden(root, "G-PR",
            f"Gantry: no pull requests from {branch}. Spikes never merge, and "
            "main isn't a feature branch.")
        return
    check_findings(root, branch, gate="G-PR")
    test_command = read_config(root).get("test_command")
    if test_command:
        try:
            check_evidence(root, test_command, gate="G-PR")
        except _Allowed:
            pass


def check_gh(root: Path, args: list[str]) -> None:
    joined = " ".join(args)
    if args[:2] == ["pr", "create"]:
        check_pr_create(root)
    elif args[:2] == ["pr", "merge"]:
        refuse_merge(root, "merge pull requests or enable auto-merge")
    elif args[:2] == ["pr", "review"] and any(a in ("--approve", "-a") for a in args):
        refuse_merge(root, "approve pull requests")
    elif args[:1] == ["api"] and re.search(r"pulls/\d+/(merge|reviews)\b|automerge|enablePullRequestAutoMerge|mergePullRequest", joined):
        refuse_merge(root, "merge or approve pull requests through the API")


def touches_harness(words: list[str]) -> bool:
    destructive = {"rm", "rmdir", "mv", "del", "Remove-Item", "rd"}
    if not words or Path(words[0]).name not in destructive and words[:2] != ["git", "rm"]:
        return False
    return any(HARNESS_DIR in w for w in words[1:])


def simple_commands(line: str):
    """Split a shell line into word lists on &&, ||, ;, | and newlines."""
    for part in re.split(r"&&|\|\||;|\||\n", line):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if words:
            yield words


def git_args(words: list[str]) -> list[str] | None:
    """If these words run git, return git's subcommand and arguments."""
    i = 0
    while i < len(words) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[i]):
        i += 1                      # skip FOO=bar environment prefixes
    if i >= len(words) or Path(words[i]).name.lower() not in ("git", "git.exe"):
        return None
    i += 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in GIT_OPTS_WITH_VALUE else 1
    return words[i:] or None


def is_force(args: list[str]) -> bool:
    for a in args[1:]:
        if a in ("-f", "--force") or a.startswith("--force-with-lease") \
                or a.startswith("--force-if-includes") \
                or (a.startswith("+") and len(a) > 1):
            return True
        if not a.startswith("--") and a.startswith("-") and "f" in a[1:]:
            return True             # combined short flags like -uf
    return False


def push_targets(args: list[str]) -> list[str]:
    """Branch names a push would update, from explicit refspecs."""
    positional = [a for a in args[1:] if not a.startswith("-")]
    refspecs = positional[1:]       # first positional is the remote
    return [r.lstrip("+").split(":")[-1].removeprefix("refs/heads/")
            for r in refspecs]


def effective_dirs(command: str, start: str) -> list[str]:
    """Every folder this command runs git in. `cd other-repo && git commit` from
    outside a Gantry repo must be judged by other-repo, not by where the session
    happens to be (a gap found while building the book's companion repo)."""
    here = Path(start).expanduser()
    dirs = [str(here)]
    for words in simple_commands(command):
        if words[0] in ("cd", "pushd", "Set-Location", "sl") and len(words) > 1:
            here = (here / os.path.expanduser(words[1])).resolve()
            dirs.append(str(here))
        i = 1 if words and Path(words[0]).name.lower() in ("git", "git.exe") else None
        while i is not None and i < len(words) - 1 and words[i].startswith("-"):
            if words[i] == "-C":
                dirs.append(str((here / os.path.expanduser(words[i + 1])).resolve()))
                i += 2
            else:
                i += 1
    seen, out = set(), []
    for d in dirs:
        if d not in seen and Path(d).is_dir():
            seen.add(d)
            out.append(d)
    return out


def main() -> None:
    data = read_input()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return
    command = (data.get("tool_input") or {}).get("command", "")
    start = data.get("cwd") or os.getcwd()
    dirs = effective_dirs(command, start)
    for d in dirs[1:]:
        check(dict(data, cwd=d), elsewhere=True)
    check(data)


def check(data: dict, elsewhere: bool = False) -> None:
    """All the Bash gates, for one folder the command runs in."""
    if elsewhere and gantry_root(data) is None and uninitialized_repo(data) is None:
        return
    root = gantry_root(data)
    if root is None:
        bare = uninitialized_repo(data)     # required mode (ADR-0010)
        if bare is not None:
            command = (data.get("tool_input") or {}).get("command", "")
            for words in simple_commands(command):
                args = git_args(words)
                if args and args[0] in ("commit", "push"):
                    deny_unless_overridden(bare, "G-INIT", INIT_REASON)
        return                      # principle 7: dormant until invited
    command = (data.get("tool_input") or {}).get("command", "")

    probe = re.fullmatch(r"\s*echo GANTRY_PROBE_([0-9a-f]{16})\s*", command)
    if probe:                       # /gantry:doctor's live fire: prove this hook runs
        with (root / ".gantry" / "probe.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"token": probe.group(1), "at": now_iso(), "hook": "pre_bash",
                                "plugin_root": os.environ.get("CLAUDE_PLUGIN_ROOT", "")}) + "\n")
        return

    findings = scan(command)
    if findings:
        deny_unless_overridden(root, "G-SECRET", "Gantry: this command contains what looks like a secret "
             f"({findings[0].kind}, {findings[0].preview}). Don't put "
             "secret values in commands; they're saved in the session log.")

    if writes_into_harness(command):
        deny_unless_overridden(root, "G-HARNESS", "Gantry: commands can't write into .gantry/. Those files are "
             "records Gantry keeps itself.")

    for words in simple_commands(command):
        if touches_harness(words):
            deny_unless_overridden(root, "G-HARNESS", "Gantry: .gantry/ holds this repo's harness state and can't "
                 "be removed or moved by the agent. If the user wants to opt "
                 "out of Gantry, they can delete it themselves.")
        gh = gh_args(words)
        if gh:
            check_gh(root, gh)
            continue
        args = git_args(words)
        if not args:
            continue
        sub = args[0]

        if sub in ("commit", "push", "merge", "rebase") and data.get("agent_id"):
            deny_unless_overridden(root, "G-SUBAGENT",
                f"Gantry: subagents don't {sub}. Finish the task and return "
                "your completion report; the main session reviews and "
                "commits through gantry:commit-gate.")

        if sub == "push" and is_force(args):
            deny_unless_overridden(root, "G-FORCE", "Gantry: force pushes are refused in this repository. "
                 "If history needs rewriting, stop and ask the user; a "
                 "human can do it from their own terminal.")

        if sub == "push":
            targets = push_targets(args) or ["HEAD"]
            targets = [current_branch(root) if t == "HEAD" else t for t in targets]
            hit = PROTECTED.intersection(targets)
            if hit:
                deny_unless_overridden(root, "G-MAIN", f"Gantry: pushing to {', '.join(sorted(hit))} is "
                     "refused. Push your branch and open a pull request.")

        if sub in ("merge", "rebase", "cherry-pick") and \
                any(a.startswith("spike/") for a in args[1:]):
            deny_unless_overridden(root, "G-SPIKE", "Gantry: spike branches can't be merged. Write up what you "
                 "learned in .gantry/spikes/<slug>.md, then start the real work "
                 "with /gantry:feature.")

        if sub == "branch" and any(a in ("-m", "-M", "--move") for a in args[1:]):
            names = [a for a in args[1:] if not a.startswith("-")]
            old, new = (names if len(names) == 2 else [current_branch(root), *names[-1:]])[:2]
            if lane_of(old) != lane_of(new):
                deny_unless_overridden(root, "G-LANE", "Gantry: renaming a branch into a different lane changes "
                     "which gates apply. Ask the user; they can rename it.")

        if sub == "commit":
            if current_branch(root) in PROTECTED:
                deny_unless_overridden(root, "G-MAIN", "Gantry: commits on main or master are refused. Create a "
                     "branch with `git switch -c <type>/<short-name>`, then "
                     "commit through the gantry:commit-gate skill.")
            test_command = read_config(root).get("test_command")
            branch = current_branch(root)
            if test_command and lane_of(branch) != "spike":
                try:
                    check_evidence(root, test_command)
                except _Allowed:
                    pass
            check_findings(root, branch)
            check_conformance(root)


if __name__ == "__main__":
    run_hook("pre-bash gate", main)
