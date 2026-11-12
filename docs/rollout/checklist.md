# Rollout checklist (Chapter 24)

## Before the pilot
1. Fork Gantry into a company marketplace repo. Add your company's standards and review-matrix rows.
2. Write your answers to the security and legal questions (security-review.md).
3. Pick one pilot team with a real codebase and a willing lead. Agree on what success looks like after four to six weeks, in numbers.

## Pilot
4. Install Gantry for the pilot team through managed settings, from the early-access marketplace.
5. Wave 1 gates blocking; everything else in warn mode (`GANTRY_GATES_WARN`).
6. Run `/gantry:init` with the team, in their repos. Watch where it confuses people and fix that.
7. Read the override log and warn-mode data weekly. Fix blocking false positives within two working days.
8. Advance through waves 2 and 3 with the pilot team as the data supports it.

## Company rollout
9. Promote the release to the stable marketplace. Managed settings for everyone: marketplace, enabled plugin, allowlist, sideload flags off, managed hooks only, required mode.
10. Wave 1 blocking for everyone; everything else in warn mode. Announce what's blocking and how overrides work.
11. Branch protection on main everywhere: PRs, required CI checks, human approval, code owners for `.gantry/` governance files.
12. Advance waves company-wide on a published schedule, driven by warn-mode data.
13. Teams adopt wave 4 (specs and architecture) one at a time, when ready.

## Ongoing
14. A named owner, a channel, an issue tracker, and a two-day turnaround on blocking false positives.
15. Weekly override-log reading. Monthly metrics pack. Monthly review of admin bypasses.
16. Every gate change through an ADR. Every release through early-access first.

## The waves, as GANTRY_GATES_WARN values
Everything not yet blocking is listed, so it keeps collecting would-deny data.

| Wave | GANTRY_GATES_WARN |
| --- | --- |
| 1 | `G-EVIDENCE,G-SUBAGENT,G-MERGE,G-PR,G-LANE,G-CHORE,G-FIX,G-REFACTOR,G-FINDINGS,G-SPEC,G-ARCH,G-INIT,G-SPIKE,G-MIGRATION` |
| 2 | `G-LANE,G-CHORE,G-FIX,G-REFACTOR,G-FINDINGS,G-SPEC,G-ARCH,G-INIT,G-SPIKE,G-MIGRATION` |
| 3 | `G-SPEC,G-ARCH,G-INIT` |
| 4 | (empty, per team) |
