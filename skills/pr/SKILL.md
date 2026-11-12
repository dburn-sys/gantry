---
name: pr
description: Open a pull request for the current branch through Gantry's PR gate.
disable-model-invocation: true
---

1. Check: the branch is not main, not spike/*, and has commits ahead of main.
   Every finding in this run's report has a disposition. If not, stop and say which.
2. Push the branch (never main; never force).
3. Build the description from the run report and spec. Sections: Summary (from
   the spec), Issue (Closes #<n> only if every AC is met; otherwise Refs #<n>),
   Acceptance criteria (each with the test that proves it), Evidence (the last
   full test run from the ledger), Review (the merged findings table with
   dispositions), Overrides (from overrides.log for this branch, or "None"),
   Architecture (conformance verdicts per touched section).
   Save it as `.gantry/runs/<run>/pr.md`.
4. Show the description to the user. Open the PR (`gh pr create --body-file`,
   or the GitHub MCP server's create tool) only after they approve it.
5. Never merge, approve, or enable auto-merge. Gantry refuses it (G-MERGE).
