---
name: intent-routing
description: Use when a Gantry routing note says a message matches a
  lane, or when a plain-English request asks for work. Decides the
  lane and starts it. Routes only; never does the work itself.
user-invocable: false
---

## Phase 1: Qualify
Is this a request for work (a change to the repository), or a
question, or conversation?
**Exit when:** decided.
**If not work:** answer or reply normally and end this skill. If the
question describes a bug, answer it first, then offer the fix lane.

## Phase 2: Classify
Pick one lane: feature, fix, chore, refactor, or spike, using the
routing note as a starting point, not a verdict.
- New behavior, or a change users would notice: feature.
- Existing behavior that is wrong: fix.
- No change to source behavior: chore.
- A change to the structure of source, with behavior unchanged: refactor.
- An open question about whether an approach works: spike.
**Exit when:** exactly one lane fits.
**If not:** go to Phase 4.

## Phase 3: Route
Tell the user in one sentence which lane and why. Then start that
lane exactly as its command would: gantry:feature, gantry:fix,
gantry:chore, gantry:refactor, or gantry:spike, passing a short name
derived from the request.
If the current branch already belongs to a different piece of work,
ask whether to continue there or start a new branch. Do not decide.

## Phase 4: Ambiguity
Ask ONE question that separates the candidate lanes, with the
options listed. Then return to Phase 2.

## Hard rules
- MUST NOT write or change any file in this skill.
- MUST NOT pick a lighter lane to save time.
- If a request contains two pieces of work, MUST say so and ask
  which to do first. One run per piece of work.
