---
name: subagent-driven-development
description: Use to build an approved plan task by task, with a fresh author agent per task and review before the next task builds on it. Run by the main session only.
user-invocable: false
---

Read `.gantry/plans/<slug>.md` and the spec it implements. Track each task's
state in the run report: PENDING -> IN-PROGRESS -> VERIFIED -> ACCEPTED.
A task can start once every task it depends on is VERIFIED.

For each ready task:

## Phase 1: Dispatch
Start a fresh author agent: `gantry:<Author line>-author`, with the tier from
the task's Tier line. Pass the tier's model with the Agent tool's `model`
parameter (helper: the smallest allowed; senior-engineer: the most capable).
The brief contains ONLY: the task block, the acceptance criteria it covers
(copied from the spec), the standards that apply, the paths of files to read,
the tier name, and the worktree folder if there is one.
Never paste the whole plan or earlier tasks' conversations.

## Phase 2: Collect
Read the completion report.
**If it escalated:** re-dispatch at the higher tier, or, if it says human, ask
the user and stop until they answer.

## Phase 3: Verify evidence
Check `.gantry/evidence.jsonl` (in the task's worktree, if it has one) for a
passing full run recorded after the author's last edit, on the current tree.
**Exit when:** there is one. Mark the task VERIFIED.
**If not:** the report is not accepted. Re-dispatch the author with that fact.

## Phase 4: Review
Compute the reviewer set: every row of
${CLAUDE_PLUGIN_ROOT}/includes/review-matrix.md (and the project's
.gantry/review-matrix.md) that matches the task's diff, UNION every reviewer
in the author's "Reviewers required". Neither list can remove a reviewer the
other added. Dispatch all of them IN ONE MESSAGE so they run in parallel. Each
gets the task's diff and the acceptance criteria, nothing else.

## Phase 5: Triage
Dispatch gantry:finding-triage with every reviewer report pasted in full.
Copy its merged table into the run report's "## Review findings".

## Phase 6: Decide
**If any merged finding has Blocks: yes:** re-dispatch the author with those
findings, then repeat from Phase 3.
**Otherwise:** fill each finding's Disposition, mark the task ACCEPTED, and
continue with the next ready task.

## Hard rules
- MUST NOT write source code in the main session. Authors write; you route.
- MUST NOT accept a task on the author's word. Evidence comes from the ledger.
- MUST NOT accept a CRITICAL or HIGH finding. Only a person can, by typing
  `accept finding <n> because <reason>`.
- Commits happen only through gantry:commit-gate, from the main session.
