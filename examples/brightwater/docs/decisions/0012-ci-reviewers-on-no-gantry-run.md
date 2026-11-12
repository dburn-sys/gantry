---
status: accepted
date: 2026-07-06
title: Run the security and auth-crypto reviewers in CI, only on PRs without a Gantry run
decided-by: Brightwater platform team
supersedes: none
---

## Context
Human-written changes are welcome and don't go through Gantry's local reviewers.
Running the whole fleet in CI on every PR would duplicate local review and cost
money on every push.

## Decision
gantry-check labels a PR with no run report `no-gantry-run`. On those PRs only, CI
runs the security-reviewer and auth-crypto-reviewer, and posts their findings.
CI never requires a Gantry run.

## Alternatives considered
- Require a run report on every PR: rejected. It would forbid writing code by hand.
- The full fleet on every PR: rejected on cost. Our estimate was about twelve times
  the cost of this decision, for review that mostly repeats local review.

## Consequences
- Extra scrutiny lands exactly where the local process didn't run.
- The `no-gantry-run` count is a metric the platform team watches.

## Risks
- Reviewer results in CI are advisory unless a person acts on them; the required
  human approval still applies.
