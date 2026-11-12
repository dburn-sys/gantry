"""Install or remove Gantry's status line in ~/.claude/settings.json.

    python statusline_install.py install|remove [--settings PATH]

Backs the file up before changing it, and only ever removes an entry it added.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

MARK = "gantry-statusline"


def command() -> str:
    script = (Path(__file__).resolve().parent / "statusline.py").as_posix()
    python = "python" if sys.platform == "win32" else "python3"
    return f'{python} "{script}" # {MARK}'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["install", "remove"])
    ap.add_argument("--settings", default=str(Path.home() / ".claude" / "settings.json"))
    a = ap.parse_args()
    path = Path(a.settings)
    settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current = settings.get("statusLine") or {}
    ours = MARK in str(current.get("command", ""))
    if a.action == "install":
        if current and not ours:
            print(f"A status line is already configured in {path} and isn't Gantry's. "
                  "Not changing it. Remove it yourself first if you want Gantry's.")
            return 1
        settings["statusLine"] = {"type": "command", "command": command()}
    else:
        if not ours:
            print("Gantry's status line isn't installed. Nothing to remove.")
            return 0
        del settings["statusLine"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.gantry-backup"))
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"{'Installed' if a.action == 'install' else 'Removed'} Gantry's status line in {path}"
          + (f" (backup: {path.with_suffix('.json.gantry-backup').name})" if path.exists() else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
