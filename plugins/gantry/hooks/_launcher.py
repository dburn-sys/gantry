# -*- coding: utf-8 -*-
"""Gantry hook launcher.

Every hook in hooks.json runs through this file: `_launcher.py <hook-name>`.
It is written in old Python syntax on purpose (no annotations, no f-strings,
no walrus), so that a Python older than Gantry needs can still run it far
enough to say so, instead of failing silently while the real hook loads.
"""
import json
import os
import re
import sys

MINIMUM = (3, 10)


def interpreter_version():
    fake = os.environ.get("GANTRY_TEST_PY_VERSION")       # tests only
    if fake:
        return tuple(int(part) for part in fake.split(".")[:2])
    return tuple(sys.version_info[:2])


def too_old_message(version):
    return ("Gantry can't run: its hooks need Python %d.%d or later, and they are "
            "running on %d.%d (%s). Gantry is NOT enforcing anything in this "
            "session. Install a newer Python, make sure `python` or `python3` "
            "finds it, and start a new session. Then run /gantry:doctor."
            % (MINIMUM[0], MINIMUM[1], version[0], version[1], sys.executable))


def main():
    if len(sys.argv) < 2 or not re.match(r"^[a-z_]+$", sys.argv[1]):
        return 0
    version = interpreter_version()
    if version < MINIMUM:
        try:
            sys.stdin.read()
        except Exception:
            pass
        sys.stdout.write(json.dumps({"systemMessage": too_old_message(version)}))
        return 0
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, sys.argv[1] + ".py")
    if not os.path.isfile(target):
        return 0
    sys.argv = [target] + sys.argv[2:]
    sys.path.insert(0, here)
    import runpy
    runpy.run_path(target, run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
