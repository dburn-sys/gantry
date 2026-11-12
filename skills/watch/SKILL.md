---
name: watch
description: Follow a pull request's CI to a result.
disable-model-invocation: true
argument-hint: [pr-number]
---

1. Find the PR (argument, or the current branch's PR).
2. Check its CI status every 60 seconds until every required check has finished
   (`gh pr checks <n>`). Don't print anything while waiting except one line per
   status change.
3. If a check fails: fetch its log (`gh run view <id> --log-failed`), find the
   first real error, and say which check failed and why in three lines or fewer.
   Offer to fix it through the fix lane on this branch. Do not start until the
   user agrees.
4. If everything passes: say so, link the PR, and remind the user that merging
   is theirs.
5. Never merge, re-run checks repeatedly hoping for a pass, or push to make a
   check go green without a fix.
