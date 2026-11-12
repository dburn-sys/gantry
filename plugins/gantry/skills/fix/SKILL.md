---
name: fix
description: Start a bug fix: a failing regression test first, then the fix.
disable-model-invocation: true
argument-hint: <short bug name>
---

1. Make a slug from "$ARGUMENTS" (lowercase, hyphens). If empty, ask
   for a short name.
2. Run `git switch -c fix/<slug>` from an up-to-date main.
3. Ask for the bug description if it wasn't given.
4. Invoke gantry:tdd. Phase 1's first obligation is the regression:
   a test that fails because of the bug.
5. End with gantry:commit-gate.
