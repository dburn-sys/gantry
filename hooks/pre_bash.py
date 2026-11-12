"""Gantry PreToolUse gate for shell commands."""
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (current_branch, deny, gantry_root, lane_of, latest_run,  # noqa: E402
                     read_config, read_input, run_hook, tree_fingerprint)
from _secrets import scan  # noqa: E402

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


def check_evidence(root: Path, test_command: str) -> None:
    run = latest_run(root)
    how = (f"Run `{test_command}` exactly (no extra file or test arguments, "
           "no pipes or redirects, not in the background), then commit again.")
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


def main() -> None:
    data = read_input()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return
    root = gantry_root(data)
    if root is None:
        return                      # principle 7: dormant until invited
    command = (data.get("tool_input") or {}).get("command", "")

    findings = scan(command)
    if findings:
        deny("Gantry: this command contains what looks like a secret "
             f"({findings[0].kind}, {findings[0].preview}). Don't put "
             "secret values in commands; they're saved in the session log.")

    if writes_into_harness(command):
        deny("Gantry: commands can't write into .gantry/. Those files are "
             "records Gantry keeps itself.")

    for words in simple_commands(command):
        if touches_harness(words):
            deny("Gantry: .gantry/ holds this repo's harness state and can't "
                 "be removed or moved by the agent. If the user wants to opt "
                 "out of Gantry, they can delete it themselves.")
        args = git_args(words)
        if not args:
            continue
        sub = args[0]

        if sub == "push" and is_force(args):
            deny("Gantry: force pushes are refused in this repository. "
                 "If history needs rewriting, stop and ask the user; a "
                 "human can do it from their own terminal.")

        if sub == "push":
            targets = push_targets(args) or ["HEAD"]
            targets = [current_branch(root) if t == "HEAD" else t for t in targets]
            hit = PROTECTED.intersection(targets)
            if hit:
                deny(f"Gantry: pushing to {', '.join(sorted(hit))} is "
                     "refused. Push your branch and open a pull request.")

        if sub in ("merge", "rebase", "cherry-pick") and \
                any(a.startswith("spike/") for a in args[1:]):
            deny("Gantry: spike branches can't be merged. Write up what you "
                 "learned in .gantry/spikes/<slug>.md, then start the real work "
                 "with /gantry:feature.")

        if sub == "branch" and any(a in ("-m", "-M", "--move") for a in args[1:]):
            names = [a for a in args[1:] if not a.startswith("-")]
            old, new = (names if len(names) == 2 else [current_branch(root), *names[-1:]])[:2]
            if lane_of(old) != lane_of(new):
                deny("Gantry: renaming a branch into a different lane changes "
                     "which gates apply. Ask the user; they can rename it.")

        if sub == "commit":
            if current_branch(root) in PROTECTED:
                deny("Gantry: commits on main or master are refused. Create a "
                     "branch with `git switch -c <type>/<short-name>`, then "
                     "commit through the gantry:commit-gate skill.")
            test_command = read_config(root).get("test_command")
            if test_command and lane_of(current_branch(root)) != "spike":
                check_evidence(root, test_command)


if __name__ == "__main__":
    run_hook("pre-bash gate", main)
