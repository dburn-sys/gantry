---
name: using-git-worktrees
description: Use before dispatching tasks that run in parallel. Creates one git worktree per task, branched from the current feature branch.
user-invocable: false
---

Claude Code's built-in agent isolation branches from the default branch. Gantry
work happens on a feature branch, so create worktrees from it yourself.

1. Note the current branch, e.g. `feat/m5`.
2. For each parallel task, from the main session:

       git worktree add ../<repo>-wt-<task-slug> -b <branch>-<task-slug>-wt <branch>

3. Put the worktree's absolute path in that task's brief, with: "Work only in
   this folder."
4. After integration, remove each worktree: `git worktree remove <path>` and
   `git branch -d <branch>-<task-slug>-wt`.

## Hard rules
- MUST create worktrees from the current feature branch, never from main.
- MUST NOT let two tasks share a worktree.
- MUST remove worktrees after their branches are merged.
