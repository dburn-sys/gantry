---
name: feature
description: Start a feature: brainstorm a spec, get it approved, plan it, build it test-first.
disable-model-invocation: true
argument-hint: <short feature name>
---

1. Make a slug from "$ARGUMENTS" (lowercase, hyphens). If empty, ask
   for a short name.
2. Run `git switch -c feat/<slug>` from an up-to-date main.
3. Invoke gantry:brainstorming, then gantry:writing-plans, then
   gantry:tdd for each task in plan order.
4. End with gantry:commit-gate.
