---
name: commit
description: Commit staged work through Gantry's commit checklist.
disable-model-invocation: true
argument-hint: [optional summary]
---

# Commit

Follow these steps in order. Do not skip or reorder them.

## 1. Branch
Run `git branch --show-current`.
**Exit when:** the branch is not `main` or `master`.
**If not:** stop. Offer to create a branch named from the change,
for example `feat/month-total`, and wait for the user.

## 2. Tests
Run the test command listed in CLAUDE.md.
**Exit when:** the full suite passes.
**If not:** stop and show the failing tests. If the command can't
run (tool missing, database down, timeout), stop and report the
error in one line. Do not change code or tests to get past this step.

## 3. Changes
Run `git status --short`. List every changed and untracked file.
**Exit when:** the user has said which files to stage.
**If not:** ask. Do not guess.

## 4. Stage
Stage exactly the files the user named, by path.
**Exit when:** `git diff --cached --stat` shows only those files.
**If not:** unstage the extras and check again.

## 5. Message
Draft a commit message in this format. If arguments were given
("$ARGUMENTS"), use them as the starting point for the summary.

    feat(expenses): add monthTotal to list response

    Sums amounts spent in the current calendar month.

- First line: type(scope): summary, under 72 characters.
  Types: feat, fix, test, docs, refactor, chore.
- Blank line, then one to three lines on what and why.

**Exit when:** the user approves the message.

## 6. Commit
Run `git commit` with the approved message. Show the commit hash.

## Hard rules
- MUST NOT commit on `main` or `master`.
- MUST NOT stage files the user didn't name. MUST NOT use
  `git add -A` or `git add .`.
- MUST NOT commit if step 2 did not pass in this run.
