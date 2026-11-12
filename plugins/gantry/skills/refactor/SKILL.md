---
name: refactor
description: Start a refactor: restructure code with no behavior change, proven by unchanged tests.
disable-model-invocation: true
argument-hint: <short name>
---

1. Make a slug from "$ARGUMENTS" (lowercase, hyphens). If empty, ask
   for a short name.
2. Run `git switch -c refactor/<slug>` from an up-to-date main.
3. Run the test command from CLAUDE.md first, so there's a green baseline.
4. Restructure. Do not change existing tests. Add new tests only for
   seams the refactor needs.
5. End with gantry:commit-gate.
