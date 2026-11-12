"""Gantry PreToolUse gate for shell commands."""
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import current_branch, deny, gantry_root, read_input, run_hook  # noqa: E402

PROTECTED = {"main", "master"}
GIT_OPTS_WITH_VALUE = {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}


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

    for words in simple_commands(command):
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

        if sub == "commit" and current_branch(root) in PROTECTED:
            deny("Gantry: commits on main or master are refused. Create a "
                 "branch with `git switch -c <type>/<short-name>`, then "
                 "commit through the gantry:commit-gate skill.")


if __name__ == "__main__":
    run_hook("pre-bash gate", main)
