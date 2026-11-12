---
status: accepted
date: 2026-03-10
title: A check that cannot run warns and lets the work through
decided-by: Gantry author
supersedes: none
---

## Context
Gantry's hooks will run on every developer's machine. A missing tool, an unreadable file, or a
timeout can stop a check from running at all, which is different from a check that ran and
found a problem.

## Decision
Every Gantry gate separates two outcomes. When the check runs and the work fails it, the gate
refuses and names the reason. When the check cannot run, the gate prints one warning line,
allows the action, and marks any record it keeps as unproven.

## Alternatives considered
- Fail closed: rejected. One broken dependency would stop every developer from committing.
- Ask the user each time: rejected. It trains people to click through prompts.

## Consequences
- A record written on the let-through path is weaker proof and is marked unproven.

## Risks
- An agent could break a check's inputs to reach the let-through path. Watch for unproven
  records on ordinary work.
