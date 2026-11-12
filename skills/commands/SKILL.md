---
name: commands
description: List Gantry's commands and what each one does.
disable-model-invocation: true
---

List the Gantry commands below, exactly as written. Do not add
commands that aren't listed.

| Command | What it does |
| --- | --- |
| `/gantry:commit [summary]` | Commit through the commit gate |
| `/gantry:tdd` | Drive a behavior change test-first (Claude also starts this on its own) |
| `/gantry:init` | Opt this repository into Gantry |
| `/gantry:feature <name>` | Start a feature: spec, plan, test-first build |
| `/gantry:fix <name>` | Start a bug fix: failing regression test first |
| `/gantry:chore <name>` | Start a chore: docs, dependencies, config; no source changes |
| `/gantry:refactor <name>` | Restructure with no behavior change |
| `/gantry:spike <name>` | Run an experiment that can never merge |
| `/gantry:adr <name>` | Record a decision as an ADR |
| `/gantry:audit [range]` | Summarize overrides, approvals, ADRs, and findings |
| `/gantry:commands` | Show this list |
