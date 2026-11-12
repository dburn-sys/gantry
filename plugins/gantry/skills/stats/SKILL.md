---
name: stats
description: Summarize what Gantry's gates did in this repository: denials, overrides and their reasons, unproven commits, and review findings.
disable-model-invocation: true
argument-hint: [days]
---

Run `python "${CLAUDE_PLUGIN_ROOT}/hooks/stats.py" --days ${ARGUMENTS:-30}` (or
`python3`) and show the output. Then add at most three observations, read like a
product manager would: a gate overridden often for the same reason points at a
fix somewhere else (name it); a gate overridden often for different reasons may
be too strict; a gate that never fires may be unneeded or broken. Suggest an ADR
for any gate change. Don't change anything.
