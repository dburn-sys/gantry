---
name: commit-gate
description: Use whenever work is to be committed. The only path to a git commit in a Gantry repo. Checks the branch, runs the full suite, stages only user-named files, and writes a formatted message.
---

# Commit gate

## Phase 1: Branch
Run `git branch --show-current`.
**Exit when:** the branch is not `main` or `master`.
**If not:** stop. Offer a branch name such as `feat/month-total` and wait.

## Phase 2: Tests
Run the test command from CLAUDE.md, exactly as written.
**Exit when:** the full suite passes.
**If not:** stop and show the failures. If the command can't run, report the
error in one line. Do not change code or tests to get past this phase.

## Phase 3: Changes
Run `git status --short` and list every changed and untracked file.
**Exit when:** the user has said which files to stage.

## Phase 4: Stage
Stage exactly the files the user named, by path.
**Exit when:** `git diff --cached --stat` shows only those files.

## Phase 5: Message
Draft a message in this format, starting from any summary the user gave:

    feat(expenses): add monthTotal to list response

    Sums amounts spent in the current calendar month.

**Exit when:** the user approves it.

## Phase 6: Commit
Run `git commit` with the approved message and show the hash.

## Hard rules
- MUST NOT commit on `main` or `master`.
- MUST NOT use `git add -A` or `git add .`.
- MUST NOT commit if Phase 2 did not pass in this run.
