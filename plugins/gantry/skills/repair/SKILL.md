---
name: repair
description: Bring a repository set up by an older Gantry up to date. Adds what's safe, asks about anything that changes what's gated.
disable-model-invocation: true
---

1. Read the installed version from ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json
   and `gantry_version` from `.gantry/context.md` (missing means "before 1.2.0").
2. Compare the repository with what this version expects, and sort every
   difference into two lists:
   - **Safe**: a missing `.gantry/.gitignore` line; a missing `gantry_version`;
     a missing `## Gantry` section in CLAUDE.md (from
     ${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md, filled from context.md).
   - **Needs a decision**: anything that changes what's gated or how: adding or
     changing `test_command` or `not_source`, a config key whose meaning changed,
     a new gate that would start refusing here.
3. Show both lists. Apply the safe ones. Ask about each decision ONE at a time.
4. Set `gantry_version` to the installed version.
5. Run gantry:doctor and show the result. Tell the user to commit the changes
   through gantry:commit-gate.

Never delete anything in `.gantry/` and never edit its logs.
