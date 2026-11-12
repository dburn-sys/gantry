"""Gantry Stop hook: don't end a turn implying untested code passes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import (emit, gantry_root, has_uncommitted_changes, latest_run,  # noqa: E402
                     read_config, read_input, run_hook, tree_fingerprint)


def main() -> None:
    data = read_input()
    root = gantry_root(data)
    if root is None or data.get("stop_hook_active"):
        return                      # never loop: one nudge per stop
    test_command = read_config(root).get("test_command")
    if not test_command or not has_uncommitted_changes(root):
        return
    run = latest_run(root)
    if run and run["passed"] and run["scope"] == "full" \
            and run["tree"] == tree_fingerprint(root):
        return
    emit({"decision": "block",
          "reason": f"Gantry: files changed after the last passing full "
                    f"test run. Run `{test_command}` now, or tell the user "
                    f"plainly that the tests have not been run on the "
                    f"current code."})


if __name__ == "__main__":
    run_hook("stop check", main)
