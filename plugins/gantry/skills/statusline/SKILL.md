---
name: statusline
description: Install or remove Gantry's status line in your user settings.
disable-model-invocation: true
argument-hint: install|remove
---

Run `python "${CLAUDE_PLUGIN_ROOT}/hooks/statusline_install.py" $ARGUMENTS`
(or `python3` if `python` isn't found) and show its output. It backs up
`~/.claude/settings.json` before changing it and never touches a status line it
didn't add. The status line appears from the next session.
