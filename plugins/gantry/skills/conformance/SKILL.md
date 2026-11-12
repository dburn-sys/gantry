---
name: conformance
description: Use before committing in a repository with .gantry/architecture/. Checks the current change against each architecture section it touches, using Gantry's architect reviewers.
---

## Phase 1: Sections
If `.gantry/architecture/` doesn't exist, say "Not architecture-gated" and stop.
Read `.gantry/architecture/sections.md`. Compare its patterns with the changed
files (`git diff HEAD --name-only` plus untracked files). List the touched
sections. For a touched section with no section file, say it is skipped.
**Exit when:** you have the list of touched sections that have section files.

## Phase 2: Review
Dispatch `gantry:architect-reviewer-<letter>` for every touched section, all IN
ONE MESSAGE. Each brief: the diff, the list of changed files, and the section
letter. Nothing about how good the change is.

## Phase 3: Report
Show each reviewer's checklist and verdict, unchanged.

## Hard rules
- MUST NOT write `.gantry/conformance.jsonl` or any record of a verdict. Gantry's
  hook records verdicts as the reviewers return them.
- MUST NOT dispatch any agent other than gantry:architect-reviewer-* for this.
- MUST NOT change the architecture files. A change that needs the architecture
  to change needs an ADR and a human edit.
