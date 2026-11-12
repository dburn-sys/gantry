---
name: spike
description: Start a spike: an experiment on a throwaway branch to answer one question.
disable-model-invocation: true
argument-hint: <short name>
---

1. Make a slug from "$ARGUMENTS" (lowercase, hyphens). If empty, ask
   for a short name.
2. Run `git switch -c spike/<slug>` from an up-to-date main.
3. Create .gantry/spikes/<slug>.md with the question filled in and the
   headings "Tried", "Learned", and "Recommendation" empty.
4. Work fast. The commit gate's evidence check is relaxed here.
5. When done, fill in the findings note. Spike branches never merge.
