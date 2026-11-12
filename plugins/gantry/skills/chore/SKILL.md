---
name: chore
description: Start a chore: docs, dependencies, config, CI, or a revert. No source changes.
disable-model-invocation: true
argument-hint: <short name>
---

1. Make a slug from "$ARGUMENTS" (lowercase, hyphens). If empty, ask
   for a short name.
2. Run `git switch -c chore/<slug>` from an up-to-date main.
3. Make the change. Chores don't touch source code; if the work needs
   to, stop and suggest /gantry:fix or /gantry:feature.
4. End with gantry:commit-gate.
