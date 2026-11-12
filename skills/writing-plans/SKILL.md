---
name: writing-plans
description: Use after a spec is approved. Breaks it into small tasks, each with files, a one-sentence change, a verification, the acceptance criteria it covers, and dependencies. Writes .gantry/plans/<slug>.md.
---

# Writing plans

## Phase 1: Read the spec
Read `.gantry/specs/<slug>.md`.
**Exit when:** its Status line says approved.
**If not:** stop. Plans are only written for approved specs.

## Phase 2: Decompose
Write tasks in this format:

    ### T-3: Reject self-approval
    - Files: src/approvals/service.ts, test/approvals.test.ts
    - Change: approve() refuses when approver id equals submitter id
    - Verify: test "AC-4: approver cannot approve own expense" passes
    - Covers: AC-4
    - Depends on: T-2

A task needing two sentences of Change is two tasks. Mark the tasks that form
the minimum viable slice with `(MVP)` after the title.
**Exit when:** every task has all five parts.

## Phase 3: Cover
Add a coverage table mapping every AC to its tasks.
**Exit when:** every AC has at least one task and every task covers at least one AC.
**If not:** add the missing task, or remove the task that covers nothing.

## Phase 4: Present
Write `.gantry/plans/<slug>.md` and show it to the user.

## Hard rules
- MUST give every task exact file paths.
- MUST NOT add tasks that cover no acceptance criterion.
