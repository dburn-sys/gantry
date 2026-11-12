---
name: init
description: Opt this repository into Gantry by creating .gantry/.
disable-model-invocation: true
---

1. If `.gantry/context.md` already exists, say so and stop.
2. Create `.gantry/context.md` with exactly this content, replacing
   <project name> with the repository folder name:

       ---
       gantry: enabled
       project: <project name>
       ---
       # Project state

       No open questions. No tasks in flight.

3. Create `.gantry/.gitignore` with these lines, which are local
   records that never belong in git:

       evidence.jsonl
       unproven.log
       override-token.json
       intent-samples.jsonl
       conformance.jsonl
       metrics.jsonl
       probe.jsonl
       dev-mode.json

4. Tell the user to commit `.gantry/` and start a new session so the
   Gantry hooks pick it up.
