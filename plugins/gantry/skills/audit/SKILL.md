---
name: audit
description: Summarize the governance record for a branch or date range.
disable-model-invocation: true
argument-hint: [branch or since-date]
---

Read only. Do not change any file.

1. Verify the hash chains in `.gantry/overrides.log` and `.gantry/approvals.jsonl`
   by running `python "${CLAUDE_PLUGIN_ROOT}/hooks/verify_chains.py"`. Report the
   first broken line, if any.
2. List overrides in range: time, who, gate, reason.
3. List approvals in range.
4. List ADRs created or superseded in range.
5. List run reports in range, with any finding marked accepted or deferred.
6. List unresolved [CONFIRM-NN] items from `.gantry/open-questions.md`.

Output one Markdown report with a section per item.
