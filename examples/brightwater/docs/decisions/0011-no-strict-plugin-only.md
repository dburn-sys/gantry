---
status: accepted
date: 2026-07-06
title: Don't turn on strictPluginOnlyCustomization
decided-by: Brightwater platform team
supersedes: none
---

## Context
`strictPluginOnlyCustomization` blocks skills, agents, hooks, and MCP servers that
don't come from a plugin or from managed settings.

## Decision
Leave it off. `allowManagedHooksOnly` already stops user and project hooks from
undoing Gantry's work, and Gantry's gates don't depend on there being no other
skills or agents.

## Alternatives considered
- Turn it on: rejected for now. Developers writing their own skills is something
  we want to encourage, and a personal skill can't get past a Gantry hook.

## Consequences
- Developers keep personal skills and agents. A personal agent named like a Gantry
  reviewer can't fake a conformance record, because Gantry only records verdicts
  from `gantry:`-scoped agents (Chapter 19).

## Risks
- A project MCP server could expose tools Gantry doesn't gate. Revisit if one does.
