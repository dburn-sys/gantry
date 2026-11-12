---
name: brainstorming
description: Use before any new feature or significant behavior change. Turns an idea into an approved spec through a one-question-at-a-time interview. No feature code until the spec is approved.
---

# Brainstorming

## Phase 1: Frame
Restate the idea in two sentences. Ask the user to confirm or correct it.
**Exit when:** the user confirms.

## Phase 2: Refine
Ask ONE question per message. Cover users, the main flow, edge cases, failure
cases, permissions, data, and what's out of scope. If an answer is vague, offer
two or three concrete options. Raise edge cases you notice as questions; never
decide them. After each answer, state in one line what you recorded.
**Exit when:** every spec section could be written without guessing.
**If not:** keep asking, one question at a time.

## Phase 3: Write
Write `.gantry/specs/<slug>.md` using `reference/spec-template.md`. Acceptance
criteria as `AC-n: Given ..., when ..., then ...`. Anything unresolved becomes
`[CONFIRM-NN]` under Open questions. Leave `Status: draft`.
**Exit when:** the file exists and every section is filled.

## Phase 4: Approve
Show the spec. If any `[CONFIRM-NN]` is unresolved, ask about it and update the
spec, marking the line `(resolved: <answer>)`. When none remain, tell the user:
"To approve, type: approve spec <slug>".
**Exit when:** the user has typed it and Gantry confirms the approval was recorded.

## Hard rules
- MUST NOT write or change code in this skill.
- MUST NOT change the Status line. Gantry records approval when the user types
  the approval phrase.
- MUST NOT add acceptance criteria the user didn't agree to.
