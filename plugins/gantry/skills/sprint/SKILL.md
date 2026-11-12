---
name: sprint
description: Run a whole milestone autonomously after one interactive spec gate. Every unscripted decision is scored and logged; hard stops wait for the user.
disable-model-invocation: true
argument-hint: <slug> [issue-number]
---

Sprint mode removes the human pauses between gates. It never relaxes a gate.

## Phase 0: Resume or start
If `.gantry/sprint-log.md` exists for this slug with `Status: running` or
`Status: stopped`, this is a resume: read the plan, the sprint log, and the run
report, and continue at the first task that isn't ACCEPTED (after the user
answers any open stop). Otherwise create the branch `feat/<slug>` (or
`feat/<n>-<slug>` with an issue) and the log:

    # Sprint: <slug>
    Status: running
    Plan: .gantry/plans/<slug>.md
    Started: <time>

## Phase 1: Spec (interactive, the only one)
If there's an issue, run gantry:ticket-intake first. Run gantry:brainstorming,
and in Refine also ask the questions in
${CLAUDE_PLUGIN_ROOT}/includes/sprint-defaults-questions.md. The user approves
the spec with the usual phrase.
**Exit when:** the spec is approved. From here on, don't ask the user anything
except at a hard stop.

## Phase 2: Plan
Run gantry:writing-plans. Add `- State: PENDING` to every task.

## Phase 3: Execute
Run gantry:subagent-driven-development over the whole plan, with no batch
checkpoints. Update each task's State line in the plan as it moves
(IN-PROGRESS, VERIFIED, ACCEPTED). Append one line per state change, finding,
and escalation to the sprint log.

## Phase 4: Decide
For every decision nothing written down answers, use
${CLAUDE_PLUGIN_ROOT}/includes/decision-scorecard.md and append the scorecard to
the sprint log. Check ${CLAUDE_PLUGIN_ROOT}/includes/hard-stops.md before acting
on any decision; if one applies, stop as it describes.

## Phase 5: Finish
Commit through gantry:commit-gate. Prepend a summary to the sprint log:

    ## Sprint summary: <slug>
    Tasks: <n> accepted, <n> open.
    Decisions: <n> (confidence: 5xn, 4xn, ...).
      Review first: <every decision with confidence 3 or less, lowest first>
    Findings: <n> raised, <n> fixed, <n> accepted, <n> deferred.
    Stops: <n> (<ids and how each was resolved>)
    Overrides: <from overrides.log, or none>
    PR: <number> (<state>). Merge is yours.

Set Status to `finished`. Open the PR with gantry:pr; its Decisions section
lists every scorecard, lowest confidence first.

## Hard rules
- MUST NOT type, suggest, or simulate an override or acceptance phrase.
- MUST NOT merge, approve, or push to the default branch.
- MUST NOT edit earlier entries in the sprint log. Gantry refuses it anyway.
- MUST stop at every hard stop and stop limit, even mid-task.
