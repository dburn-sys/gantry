---
name: doctor
description: Check that Gantry is installed and actually enforcing in this repository, ending with a live-fire probe through the hooks. Read only.
disable-model-invocation: true
---

1. Get a probe token. Use the same interpreter the hooks use: run
   `python "${CLAUDE_PLUGIN_ROOT}/hooks/doctor.py" --new-token`, and if `python`
   isn't found, the same with `python3`.
2. Run exactly `echo GANTRY_PROBE_<token>`, as its own Bash command, with
   nothing before or after it.
3. Run `python "${CLAUDE_PLUGIN_ROOT}/hooks/doctor.py" --check <token>` (or
   `python3`), and show its output to the user unchanged.
4. If any line says FAIL, explain each one in a sentence and what the user
   should do. Don't try to fix anything yourself.

Don't change any file. The probe line is written by Gantry's hook, not by you.
