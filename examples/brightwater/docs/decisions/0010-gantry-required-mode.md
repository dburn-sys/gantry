---
status: accepted
date: 2026-07-06
title: When GANTRY_REQUIRED is set, a repo without .gantry/ is uninitialized, not dormant
decided-by: Brightwater platform team
supersedes: none (amends principle 7 for managed installs)
---

## Context
Managed settings put Gantry on every machine, but principle 7 makes it do nothing
in a repository without `.gantry/`. Installed everywhere, active nowhere.

## Decision
When the environment variable GANTRY_REQUIRED=1 is present (delivered only through
managed settings), Gantry treats a git repository with no .gantry/ folder as
uninitialized. In an uninitialized repo, source writes and commits are refused with
[G-INIT] until /gantry:init runs. Questions, reading code, and work outside git
repositories are unaffected.

## Alternatives considered
- Create `.gantry/` automatically on first use: rejected. It would commit a
  configuration nobody chose, with a guessed test command.
- Leave principle 7 as it is: rejected. Then the policy enforces nothing.

## Consequences
- Principle 7 still holds for personal installs: no env var, no behavior without .gantry/.
- G-INIT is overridable like every gate, so a developer is never trapped. Before
  init, override records live in `.git/gantry/`, so an override doesn't create a
  half-initialized `.gantry/`.

## Risks
- `/gantry:init` becomes everyone's first experience of Gantry. It has to be good.
