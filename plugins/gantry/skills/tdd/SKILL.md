---
name: tdd
description: Use before writing or changing any code that alters behavior. Drives the change test-first in five gated phases (obligations, red, green, verify, tidy). No implementation code until Phase 2 (red) passes.
---

# Test-first development

Work through the phases in order. After each phase print exactly one line:
`TDD Phase <n> (<name>): PASS - <one-line evidence>` or
`TDD Phase <n> (<name>): STOP - <reason>`.

## Phase 1: Obligations
From the request (and the spec, if one exists), list each required behavior as
one line: `OB-n: <given/when> -> <then>`. Include at least one failure-case
obligation for every new input. If unsure how to write them, read
`reference/obligations.md`.
**Exit when:** the user approves the list.
**If not:** an obligation that depends on something unknown is marked
`[CONFIRM-NN]` and asked about. Do not guess.

## Phase 2: Red
Write exactly one test per obligation, with the OB id in the test name, for
example `it("OB-3: rejects an empty category with 400")`. Run the test command
from CLAUDE.md.
**Exit when:** every new test runs and fails on an assertion: it reached its
`expect` and the value was wrong.
**If not:**
- A test passes already: the behavior exists or the test is wrong. Say which,
  and fix the test if it's wrong.
- A test fails on a syntax error, import error, or missing file: fix the test
  setup. That isn't red; it's broken.
- Do not write or change implementation code in this phase.

## Phase 3: Green
Write the minimum implementation that makes the new tests pass. Run the FULL
suite.
**Exit when:** the full suite passes.
**If not:** fix the implementation. Never change a test's expected value here.

## Phase 4: Verify
Print a table mapping every OB id to its test name and result.
**Exit when:** every row shows a passing test.
**If not:** return to Phase 2 for the missing obligation.

## Phase 5: Tidy
Run the lint command if CLAUDE.md lists one and fix what it reports. Run the full
suite again.
**Exit when:** both pass after the last edit.

## Hard rules
- MUST NOT write implementation code before Phase 2 prints PASS.
- MUST NOT skip Phase 1 for small changes. Size is not an exception.
- MUST NOT change an existing test's expected value to make it pass.
- If the test command can't run, MUST print STOP with the error and wait.
