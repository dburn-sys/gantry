---
name: executing-plans
description: Use to run an approved plan in batches, with a human checkpoint between batches. Groups independent tasks to run in parallel worktrees.
---

## Phase 1: Batch
Read the plan. Group tasks into batches: a batch holds tasks whose dependencies
are all in earlier batches. Within a batch, tasks that touch disjoint files can
run in parallel; mark them. Show the batches to the user.
**Exit when:** the user says go.

## Phase 2: Isolate
For a batch with parallel tasks, run the gantry:using-git-worktrees skill to
create one worktree per task.

## Phase 3: Run the batch
Run gantry:subagent-driven-development for the batch's tasks. Dispatch the
authors of parallel tasks in one message.
**Exit when:** every task in the batch is ACCEPTED.

## Phase 4: Integrate
If the batch used worktrees, merge each worktree branch back into the feature
branch (main session, `git merge --no-ff`), run the full test command on the
merged result, and remove the worktrees.
**Exit when:** the merged suite passes.

## Phase 5: Checkpoint
Report: tasks accepted so far out of the total, findings fixed and accepted in
this batch, and anything escalated. Ask "Continue to batch N?"
**Exit when:** the user says continue (go to Phase 2 with the next batch) or
stop.

## Hard rules
- MUST stop at every checkpoint, even if the user said "keep going" earlier,
  unless they are running gantry:sprint.
