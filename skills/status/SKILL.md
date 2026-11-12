---
name: status
description: Show Gantry's current state for this repository.
disable-model-invocation: true
---

Read only. Do not change any file. Report, in this order:
1. Current branch and its lane (or "no lane").
2. The open run for this branch, if any, and its last completed phase.
3. Spec and plan status for this branch (draft, approved, none).
4. The latest evidence ledger entry: time, scope, pass or fail, and
   whether the tree has changed since.
5. Unresolved [CONFIRM-NN] count, with the first three listed.
6. Overrides since this branch left main.
Keep it under 20 lines.
